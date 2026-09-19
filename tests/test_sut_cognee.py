"""Cognee market adapter with a fake client (no network): dedupe in shared
mode, per-principal datasets in silo mode, lazy cognify (once per scope per
dirty period), top_k, retrieval_prompt, end-to-end through the Runner."""

from test_runner import _write_org

from membench.adapters import MockWorker, _render_event
from membench.rag import retrieval_prompt
from membench.runner import Runner
from membench.sut_cognee import ORG_DATASET, CogneeAdapter, _dataset_for, _flatten_texts


class FakeCognee:
    def __init__(self):
        self.added = []          # (dataset, text)
        self.cognified = []      # list of dataset lists
        self.searches = []       # (query, dataset, top_k)

    def add(self, text, dataset):
        self.added.append((dataset, text))

    def cognify(self, datasets):
        self.cognified.append(list(datasets))

    def search(self, query, dataset, top_k):
        self.searches.append((query, dataset, top_k))
        return [t for d, t in self.added if d == dataset][:top_k]


def _ev(i, content):
    return {"event_id": f"E-{i:04d}", "sim_time": f"2026-03-{i:02d}T09:00:00Z",
            "channel": "meeting", "surface": "team:eng/standup",
            "participants": ["persona:alice"], "content": content}


def test_shared_mode_dedupes_and_uses_org_dataset():
    fake = FakeCognee()
    a = CogneeAdapter(MockWorker(), client=fake, shared=True)
    a.ingest("persona:alice", _ev(1, "deploy freeze Thursday"))
    a.ingest("persona:bob", _ev(1, "deploy freeze Thursday"))
    a.ingest("persona:bob", _ev(2, "snack budget"))
    assert [d for d, _ in fake.added] == [ORG_DATASET, ORG_DATASET]
    assert fake.added[0][1] == _render_event(_ev(1, "deploy freeze Thursday"))
    assert a.counters["ingest_calls"] == 2


def test_silo_mode_keys_by_principal_dataset():
    fake = FakeCognee()
    a = CogneeAdapter(MockWorker(), client=fake, shared=False)
    a.ingest("persona:alice", _ev(1, "x"))
    a.ingest("persona:bob", _ev(1, "x"))
    assert [d for d, _ in fake.added] == [_dataset_for("persona:alice"),
                                          _dataset_for("persona:bob")]
    a.run_task("persona:bob", "Task: q")
    assert fake.searches[-1][1] == _dataset_for("persona:bob")


def test_cognify_is_lazy_once_per_dirty_period_and_top_k_prompt():
    fake = FakeCognee()
    w = MockWorker()
    a = CogneeAdapter(w, client=fake, top_k=3)
    for i in range(1, 6):
        a.ingest("persona:alice", _ev(i, f"note {i}"))
    assert fake.cognified == []                       # nothing until a task
    a.run_task("persona:alice", "Task: write the note")
    a.run_task("persona:alice", "Task: again")        # no new ingests -> no cognify
    assert fake.cognified == [[ORG_DATASET]] and a.counters["cognify_calls"] == 1
    a.ingest("persona:alice", _ev(6, "note 6"))
    a.run_task("persona:alice", "Task: third")
    assert len(fake.cognified) == 2
    assert fake.searches[0] == ("Task: write the note", ORG_DATASET, 3)
    items = [_render_event(_ev(i, f"note {i}")) for i in range(1, 4)]
    assert w.calls[0] == retrieval_prompt(items, "Task: write the note")
    assert a.counters["retrieved"] >= 3 and a.counters["search_calls"] == 3


def test_flatten_texts_handles_both_sdk_shapes():
    plain = [{"text": "a"}, {"text": "b"}]
    acl = [{"dataset_name": "org", "search_result": [{"text": "c"}]}]
    assert _flatten_texts(plain) == ["a", "b"]
    assert _flatten_texts(acl) == ["c"]
    assert _flatten_texts("raw") == ["raw"]


def test_end_to_end_through_runner(tmp_path):
    org_dir = _write_org(tmp_path)
    fake = FakeCognee()
    w = MockWorker()
    a = CogneeAdapter(w, client=fake, shared=True)
    Runner(org_dir, a).run()
    assert len(fake.added) == 3                       # once per event
    assert a.counters["calls"] == 1 and "Retrieved workspace history" in w.calls[0]
    assert "standup-decision-kebab" in w.calls[0] and "allhands" not in w.calls[0]
