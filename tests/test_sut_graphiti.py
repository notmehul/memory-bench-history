"""Graphiti market adapter with a fake async client (no network): dedupe in
shared mode, per-principal group ids in silo mode, top_k, retrieval_prompt,
end-to-end through the Runner."""

from types import SimpleNamespace

from test_runner import _write_org

from membench.adapters import MockWorker, _render_event
from membench.rag import retrieval_prompt
from membench.runner import Runner
from membench.sut_graphiti import ORG_GROUP, GraphitiAdapter, _group


class FakeGraphiti:
    def __init__(self):
        self.built = 0
        self.episodes = []
        self.searches = []

    async def build_indices_and_constraints(self):
        self.built += 1

    async def add_episode(self, **kw):
        self.episodes.append(kw)

    async def search(self, query, group_ids=None, num_results=10):
        self.searches.append((query, group_ids, num_results))
        hits = [e for e in self.episodes if e["group_id"] in (group_ids or [])]
        return [SimpleNamespace(fact=f"fact from {e['name']}: {e['episode_body']}",
                                valid_at=e["reference_time"]) for e in hits][:num_results]


def _ev(i, content):
    return {"event_id": f"E-{i:04d}", "sim_time": f"2026-03-{i:02d}T09:00:00Z",
            "channel": "meeting", "surface": "team:eng/standup",
            "participants": ["persona:alice"], "content": content}


def test_shared_mode_dedupes_by_event_id_and_uses_org_group():
    fake = FakeGraphiti()
    a = GraphitiAdapter(MockWorker(), client=fake, shared=True)
    a.ingest("persona:alice", _ev(1, "deploy freeze Thursday"))
    a.ingest("persona:bob", _ev(1, "deploy freeze Thursday"))
    a.ingest("persona:bob", _ev(2, "snack budget"))
    assert fake.built == 1
    assert [e["name"] for e in fake.episodes] == ["E-0001", "E-0002"]
    assert {e["group_id"] for e in fake.episodes} == {ORG_GROUP}
    assert fake.episodes[0]["episode_body"] == _render_event(_ev(1, "deploy freeze Thursday"))
    assert fake.episodes[0]["source_description"] == "team:eng/standup"
    assert fake.episodes[0]["reference_time"].year == 2026
    assert a.counters["ingest_calls"] == 3 and a.counters["add_episode_calls"] == 2


def test_silo_mode_keys_by_sanitized_principal():
    fake = FakeGraphiti()
    a = GraphitiAdapter(MockWorker(), client=fake, shared=False)
    a.ingest("persona:alice", _ev(1, "x"))
    a.ingest("persona:bob", _ev(1, "x"))
    assert [e["group_id"] for e in fake.episodes] == ["persona_alice", "persona_bob"]
    assert _group("persona:alice") == "persona_alice"
    a.run_task("persona:bob", "Task: q")
    assert fake.searches[-1][1] == ["persona_bob"]


def test_run_task_passes_top_k_and_builds_retrieval_prompt():
    fake = FakeGraphiti()
    w = MockWorker()
    a = GraphitiAdapter(w, client=fake, top_k=3)
    for i in range(1, 6):
        a.ingest("persona:alice", _ev(i, f"note {i}"))
    a.run_task("persona:alice", "Task: write the note")
    assert fake.searches == [("Task: write the note", [ORG_GROUP], 3)]
    items = [f"[2026-03-0{i}T09:00:00+00:00] fact from E-000{i}: "
             f"{_render_event(_ev(i, f'note {i}'))}" for i in range(1, 4)]
    assert w.calls[-1] == retrieval_prompt(items, "Task: write the note")
    assert a.counters["retrieved"] == 3 and a.counters["search_calls"] == 1
    assert a.counters["last_context_chars"] == len("\n\n".join(items))


def test_no_hits_gives_bare_task():
    fake = FakeGraphiti()
    w = MockWorker()
    a = GraphitiAdapter(w, client=fake)
    a.run_task("persona:alice", "Task: anything")
    assert w.calls[-1] == "Task: anything" and a.counters["last_context_chars"] == 0


def test_end_to_end_through_runner(tmp_path):
    org_dir = _write_org(tmp_path)
    fake = FakeGraphiti()
    w = MockWorker()
    a = GraphitiAdapter(w, client=fake, shared=True)
    Runner(org_dir, a).run()
    assert [e["name"] for e in fake.episodes] == ["E-0001", "E-0002", "E-0003"]  # once each
    assert a.counters["calls"] == 1 and "Retrieved workspace history" in w.calls[0]
    assert "standup-decision-kebab" in w.calls[0] and "allhands" not in w.calls[0]  # pre-probe


def test_pin_group_initializes_kuzu_driver_database():
    # graphiti-core 0.29.3: KuzuDriver never sets _database; adapter pins it
    from types import SimpleNamespace

    a = GraphitiAdapter(MockWorker(), client=FakeGraphiti())
    a.client.driver = SimpleNamespace()
    a._pin_group("org")
    assert a.client.driver._database == "org"
