"""Mem0 market adapter: fake client (no network / no mem0ai import), shared
dedupe vs silo per-principal scopes, top_k, retrieval_prompt, Runner e2e."""

from membench.adapters import MockWorker
from membench.rag import retrieval_prompt
from membench.runner import Runner
from membench.sut_mem0 import ORG_SCOPE, Mem0Adapter
from tests.test_runner import _write_org


class FakeMem0:
    def __init__(self, hits=()):
        self.adds, self.searches, self.hits = [], [], list(hits)

    def add(self, messages, *, user_id, infer, metadata=None):
        self.adds.append((messages, user_id, infer, metadata))
        return {"results": [{"id": "m1", "memory": messages, "event": "ADD"}]}

    def search(self, query, *, filters, top_k):
        self.searches.append((query, filters, top_k))
        return {"results": self.hits}


def _ev(i, content):
    return {"event_id": f"E-{i:04d}", "sim_time": f"2026-03-{i:02d}T09:00:00Z",
            "channel": "meeting", "surface": "team:eng/standup",
            "participants": ["persona:alice"], "content": content}


def test_shared_dedupes_by_event_id_under_org_scope():
    fake = FakeMem0()
    a = Mem0Adapter(MockWorker(), client=fake, shared=True)
    a.ingest("persona:alice", _ev(1, "deploy freeze Thursday"))
    a.ingest("persona:bob", _ev(1, "deploy freeze Thursday"))    # second witness
    a.ingest("persona:bob", _ev(2, "snack budget"))
    assert [u for _, u, _, _ in fake.adds] == [ORG_SCOPE, ORG_SCOPE]
    assert all(infer is True for _, _, infer, _ in fake.adds)
    assert "deploy freeze Thursday" in fake.adds[0][0] and "[2026-03-01" in fake.adds[0][0]
    assert a.counters["ingest_calls"] == 2 and a.counters["memories_written"] == 2


def test_silo_ingests_under_each_witness():
    fake = FakeMem0()
    a = Mem0Adapter(MockWorker(), client=fake, shared=False)
    a.ingest("persona:alice", _ev(1, "x"))
    a.ingest("persona:bob", _ev(1, "x"))
    a.ingest("persona:alice", _ev(1, "x"))                        # same witness twice
    assert [u for _, u, _, _ in fake.adds] == ["persona:alice", "persona:bob"]
    a.run_task("persona:bob", "Task: t")
    assert fake.searches[-1][1] == {"user_id": "persona:bob"}


def test_run_task_passes_top_k_and_builds_retrieval_prompt():
    hits = [{"memory": "deploy freeze is Thursday", "created_at": "2026-08-15T10:00:00Z"},
            {"memory": "window Tuesday"}]
    fake = FakeMem0(hits)
    w = MockWorker()
    a = Mem0Adapter(w, client=fake, top_k=3)
    out = a.run_task("persona:alice", "Task: write the note")
    assert out == "mock deliverable"
    assert fake.searches == [("Task: write the note", {"user_id": ORG_SCOPE}, 3)]
    items = ["[2026-08-15T10:00:00Z] deploy freeze is Thursday", "window Tuesday"]
    assert w.calls[-1] == retrieval_prompt(items, "Task: write the note")
    assert a.counters["retrieved"] == 2 and a.counters["search_calls"] == 1
    assert a.counters["last_context_chars"] == len("\n\n".join(items))
    fake.hits = []
    a.run_task("persona:alice", "Task: bare")
    assert w.calls[-1] == "Task: bare" and a.counters["last_context_chars"] == 0


def test_end_to_end_through_runner(tmp_path):
    org_dir = _write_org(tmp_path)
    shared, silo = FakeMem0(), FakeMem0()
    Runner(org_dir, Mem0Adapter(MockWorker(), client=shared, shared=True)).run()
    Runner(org_dir, Mem0Adapter(MockWorker(), client=silo, shared=False)).run()
    assert len(shared.adds) == 3 and {u for _, u, _, _ in shared.adds} == {ORG_SCOPE}
    assert len(silo.adds) == 7                        # one add per delivery
    assert len(shared.searches) == 1 and shared.searches[0][1] == {"user_id": ORG_SCOPE}
    assert silo.searches[0][1] == {"user_id": "persona:bob"}
