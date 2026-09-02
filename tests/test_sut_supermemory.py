"""Supermemory adapter (fake client, no network): dedupe in shared mode,
per-principal container tags in silo mode, top_k, retrieval_prompt, settle
wait, and end-to-end through Runner with MockWorker."""

from types import SimpleNamespace

from membench.adapters import MockWorker, _render_event
from membench.rag import retrieval_prompt
from membench.runner import Runner
from membench.sut_supermemory import ORG_TAG, SupermemoryAdapter
from tests.test_runner import STREAM, _write_org


class FakeClient:
    def __init__(self, results=()):
        self.adds, self.searches, self.processing_polls = [], [], 0
        self._results = list(results)
        self.documents = SimpleNamespace(add=self._add, list_processing=self._processing)
        self.search = SimpleNamespace(memories=self._search)

    def _add(self, **kw):
        self.adds.append(kw)
        return SimpleNamespace(id=f"doc-{len(self.adds)}", status="queued")

    def _processing(self):
        self.processing_polls += 1
        return SimpleNamespace(documents=[], total_count=0)

    def _search(self, **kw):
        self.searches.append(kw)
        return SimpleNamespace(results=self._results, total=len(self._results), timing=1.0)


def _result(memory, sim_time=None, chunk=None):
    meta = {"sim_time": sim_time} if sim_time else {}
    return SimpleNamespace(memory=memory, chunk=chunk, metadata=meta, similarity=0.9)


def test_shared_mode_dedupes_by_event_id_and_uses_org_tag():
    fc = FakeClient()
    a = SupermemoryAdapter(MockWorker(), client=fc, shared=True)
    a.ingest("persona:alice", STREAM[0])
    a.ingest("persona:cara", STREAM[0])           # second witness: no second add
    a.ingest("persona:alice", STREAM[1])
    assert len(fc.adds) == 2 and a.counters["ingest_calls"] == 2
    assert {k["container_tag"] for k in fc.adds} == {ORG_TAG}
    assert fc.adds[0]["content"] == _render_event(STREAM[0])
    assert fc.adds[0]["metadata"] == {"event_id": "E-0001", "sim_time": STREAM[0]["sim_time"],
                                      "surface": "dm:alice-cara"}
    assert fc.adds[0]["document_date"] == STREAM[0]["sim_time"]
    assert fc.adds[0]["custom_id"] == "org:E-0001"


def test_silo_mode_ingests_under_each_witness_with_sanitized_tags():
    fc = FakeClient()
    a = SupermemoryAdapter(MockWorker(), client=fc, shared=False)
    a.ingest("persona:alice", STREAM[0])
    a.ingest("persona:cara", STREAM[0])
    a.ingest("persona:alice", STREAM[0])           # same witness twice: deduped
    assert [k["container_tag"] for k in fc.adds] == ["persona_alice", "persona_cara"]
    a.run_task("persona:cara", "Task: x")
    assert fc.searches[-1]["container_tag"] == "persona_cara"


def test_run_task_builds_retrieval_prompt_with_top_k():
    fc = FakeClient(results=[_result("deploy freeze Thursday", "2026-03-02T09:00:00Z"),
                             _result(None, chunk="raw chunk text"), _result(None)])
    w = MockWorker()
    a = SupermemoryAdapter(w, client=fc, top_k=3)
    a.ingest("persona:alice", STREAM[1])
    out = a.run_task("persona:alice", "Task: write the deploy note")
    assert out == "mock deliverable"
    assert fc.searches == [{"q": "Task: write the deploy note", "container_tag": ORG_TAG,
                            "limit": 3, "search_mode": "hybrid"}]
    items = ["[2026-03-02T09:00:00Z] deploy freeze Thursday", "raw chunk text"]
    assert w.calls[-1] == retrieval_prompt(items, "Task: write the deploy note")
    assert a.counters["retrieved"] == 2 and a.counters["search_calls"] == 1
    assert a.counters["last_context_chars"] == len("\n\n".join(items))


def test_settle_only_after_new_ingests(monkeypatch):
    import membench.sut_supermemory as m
    slept = []
    monkeypatch.setattr(m.time, "sleep", lambda s: slept.append(s))
    fc = FakeClient()
    a = SupermemoryAdapter(MockWorker(), client=fc, ingest_settle_seconds=3,
                           wait_for_processing=True)
    a.run_task("p", "t")                                   # nothing ingested: no wait
    assert slept == [] and a.counters["settle_waits"] == 0
    a.ingest("p", STREAM[0])
    a.run_task("p", "t")
    a.run_task("p", "t")                                   # no new ingest: no wait
    assert slept == [3] and fc.processing_polls == 1 and a.counters["settle_waits"] == 1


def test_end_to_end_runner_with_mock_worker(tmp_path):
    org_dir = _write_org(tmp_path)
    fc = FakeClient(results=[_result("standup-decision-kebab")])
    w = MockWorker()
    Runner(org_dir, SupermemoryAdapter(w, client=fc)).run()
    assert len(fc.adds) == 3                               # 3 events, once each
    assert len(fc.searches) == 1 and "standup-decision-kebab" in w.calls[0]


def test_namespace_prefixes_tags_in_both_modes():
    # hosted store persists across runs: tags must be disjoint per org side
    fc = FakeClient()
    a = SupermemoryAdapter(MockWorker(), client=fc, namespace="org-00001-twin")
    ev = {"event_id": "E-0001", "sim_time": "2026-03-01T09:00:00Z",
          "channel": "meeting", "surface": "team:eng/standup",
          "participants": ["persona:alice"], "content": "x"}
    a.ingest("persona:alice", ev)
    assert fc.adds[0]["container_tag"] == "org-00001-twin:org"
    assert fc.adds[0]["custom_id"].startswith("org-00001-twin:org:")
    silo = SupermemoryAdapter(MockWorker(), client=FakeClient(),
                              namespace="org-00001", shared=False)
    silo.ingest("persona:alice", ev)
    assert silo.client.adds[0]["container_tag"] == "org-00001:persona_alice"


def test_search_uses_vendor_recommended_hybrid_mode():
    fc = FakeClient(results=[_result("m1")])
    a = SupermemoryAdapter(MockWorker(), client=fc)
    a.run_task("persona:alice", "Task: q")
    assert fc.searches[0]["search_mode"] == "hybrid"


def test_null_sim_time_omits_date_and_metadata_nulls():
    # v1 streams: sim_time is null on every event (API 400s on null values)
    fc = FakeClient()
    a = SupermemoryAdapter(MockWorker(), client=fc)
    a.ingest("persona:alice", {"event_id": "E-0001", "sim_time": None,
                               "channel": "standup", "surface": "team:eng/standup",
                               "participants": ["persona:alice"], "content": "x"})
    add = fc.adds[0]
    assert "document_date" not in add
    assert "sim_time" not in add["metadata"] and add["metadata"]["event_id"] == "E-0001"
    assert not add["content"].startswith("[None]")


def test_render_event_omits_null_timestamp():
    # v1 frozen streams: sim_time is null on every event
    ev = {"event_id": "E-0001", "sim_time": None, "channel": "standup",
          "surface": "team:eng/standup", "participants": ["persona:a"], "content": "x"}
    out = _render_event(ev)
    assert out.startswith("team:eng/standup (")
    assert "None" not in out
