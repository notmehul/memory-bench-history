"""Pilot runner core: witness routing, probe injection, baseline adapters."""

import json

import pytest

from membench.adapters import FullTranscriptAdapter, MockWorker, NoMemoryAdapter
from membench.runner import Runner, RunnerError, task_prompt

ORG = {
    "org_id": "org-test",
    "entities": {
        "personas": [
            {"id": "persona:alice", "role": "engineer", "authority_level": 2,
             "teams": ["team:eng"]},
            {"id": "persona:bob", "role": "engineer", "authority_level": 2,
             "teams": ["team:eng"]},
            {"id": "persona:cara", "role": "marketer", "authority_level": 2,
             "teams": ["team:mkt"]},
        ],
        "teams": [
            {"id": "team:eng", "members": ["persona:alice", "persona:bob"]},
            {"id": "team:mkt", "members": ["persona:cara"]},
        ],
        "projects": [],
    },
    "events": [
        {"event_id": "E-0001", "surface": "dm:alice-cara", "visibility": "private",
         "participants": ["persona:alice", "persona:cara"]},
        {"event_id": "E-0002", "surface": "team:eng/standup",
         "visibility": "team_confidential", "team": "team:eng",
         "participants": ["persona:alice"]},
        {"event_id": "E-0003", "surface": "org/all-hands", "visibility": "org_public",
         "participants": ["persona:alice"]},
    ],
    "facts": [],
}

STREAM = [
    {"event_id": "E-0001", "sim_time": "2026-03-01T09:00:00Z", "channel": "dm",
     "surface": "dm:alice-cara", "participants": ["persona:alice", "persona:cara"],
     "content": "dm-secret-plan"},
    {"event_id": "E-0002", "sim_time": "2026-03-01T10:00:00Z", "channel": "meeting",
     "surface": "team:eng/standup", "participants": ["persona:alice"],
     "content": "standup-decision-kebab"},
    {"event_id": "E-0003", "sim_time": "2026-03-01T11:00:00Z", "channel": "meeting",
     "surface": "org/all-hands", "participants": ["persona:alice"],
     "content": "allhands-announcement"},
]

PROBE = {
    "probe_id": "P-0001-01", "cluster_id": "P-0001", "principal": "persona:bob",
    "inject_after_event": "E-0002", "task": "Write your triage note.",
    "context_frame": {"kind": "personal", "ref": None},
}


def _write_org(tmp_path, probes=(PROBE,), stream=STREAM):
    (tmp_path / "org.json").write_text(json.dumps(ORG))
    (tmp_path / "events.jsonl").write_text(
        "".join(json.dumps(e) + "\n" for e in stream))
    (tmp_path / "probes.jsonl").write_text(
        "".join(json.dumps(p) + "\n" for p in probes))
    return tmp_path


class RecordingAdapter:
    def __init__(self):
        self.counters = {}
        self.log = []

    def ingest(self, principal, event):
        self.log.append(("ingest", event["event_id"], principal))

    def run_task(self, principal, task):
        self.log.append(("task", principal, task))
        return "out"


def test_witness_routing(tmp_path):
    adapter = RecordingAdapter()
    Runner(_write_org(tmp_path), adapter).run()
    ingests = {}
    for _kind, eid, pid in (x for x in adapter.log if x[0] == "ingest"):
        ingests.setdefault(eid, set()).add(pid)
    assert ingests["E-0001"] == {"persona:alice", "persona:cara"}
    # bob is entitled to his team's surface without attending
    assert ingests["E-0002"] == {"persona:alice", "persona:bob"}
    assert ingests["E-0003"] == {"persona:alice", "persona:bob", "persona:cara"}


def test_probe_injection_position_and_prompt(tmp_path):
    adapter = RecordingAdapter()
    Runner(_write_org(tmp_path), adapter).run()
    kinds = [(x[0], x[1]) for x in adapter.log]
    task_at = kinds.index(("task", "persona:bob"))
    assert ("ingest", "E-0002") in kinds[:task_at]
    assert ("ingest", "E-0003") in kinds[task_at:]
    prompt = adapter.log[task_at][2]
    assert prompt.startswith("You are Bob, engineer (eng) at org-test.")
    assert "The artifact is for your own personal use." in prompt
    assert "Task: Write your triage note." in prompt
    assert "Authoritative context" not in prompt  # runner injects no facts


def test_no_memory_vs_full_transcript(tmp_path):
    org_dir = _write_org(tmp_path)
    floor_worker, lc_worker = MockWorker(), MockWorker()
    Runner(org_dir, NoMemoryAdapter(floor_worker)).run()
    Runner(org_dir, FullTranscriptAdapter(lc_worker, shared=True)).run()
    assert "workspace history" not in floor_worker.calls[0]
    lc_prompt = lc_worker.calls[0]
    assert "standup-decision-kebab" in lc_prompt      # witnessed via team surface
    assert "dm-secret-plan" not in lc_prompt          # bob never saw the dm


def test_silo_vs_shared_storage(tmp_path):
    org_dir = _write_org(tmp_path)
    shared = FullTranscriptAdapter(MockWorker(), shared=True)
    silo = FullTranscriptAdapter(MockWorker(), shared=False)
    Runner(org_dir, shared).run()
    Runner(org_dir, silo).run()
    assert shared.counters["stored_events"] == 3          # one copy per event
    assert silo.counters["stored_events"] == 7            # one copy per delivery
    # identical context text for the raw-transcript adapter (contrast becomes
    # material for derived-memory systems; storage shape is what differs here)
    assert shared.worker.calls == silo.worker.calls


def test_results_shape(tmp_path):
    org_dir = _write_org(tmp_path)
    out = tmp_path / "results.jsonl"
    rows = Runner(org_dir, NoMemoryAdapter(MockWorker())).run(out_path=out)
    assert [r["run_id"] for r in rows] == ["P-0001-01:sut"]
    parsed = [json.loads(line) for line in out.read_text().splitlines()]
    assert parsed == rows
    assert set(rows[0]) == {"run_id", "output", "context_chars"}
    assert rows[0]["output"] == "mock deliverable"
    assert rows[0]["context_chars"] == 0


def test_unknown_inject_event_raises(tmp_path):
    bad = dict(PROBE, inject_after_event="E-9999")
    org_dir = _write_org(tmp_path, probes=(bad,))
    with pytest.raises(RunnerError, match="E-9999"):
        Runner(org_dir, RecordingAdapter()).run()


def test_misaligned_stream_raises(tmp_path):
    org_dir = _write_org(tmp_path, stream=list(reversed(STREAM)))
    with pytest.raises(RunnerError, match="align"):
        Runner(org_dir, RecordingAdapter()).run()


def test_task_prompt_matches_screening_floor_structure():
    prompt = task_prompt(ORG, PROBE)
    parts = prompt.split("\n\n")
    assert parts[0] == "You are Bob, engineer (eng) at org-test."
    assert parts[1] == "The artifact is for your own personal use."
    assert parts[2] == "Task: Write your triage note."
    assert "state them concretely" in parts[3]
    assert "output.md" not in prompt  # transport belongs to the worker


def test_worker_failure_is_recorded_not_fatal(tmp_path):
    """Empty-output rule: a worker failure yields a null-output row that the
    scorer scores 0.0 — the probe stays in the denominator."""
    from membench.workers import WorkerError

    class FailingWorker:
        def complete(self, prompt):
            raise WorkerError("codex worker failed after 2 attempts: timeout")

    org_dir = _write_org(tmp_path)
    rows = Runner(org_dir, NoMemoryAdapter(FailingWorker())).run()
    assert rows[0]["output"] is None
    assert "timeout" in rows[0]["error"]


def test_grep_agent_adapter_materializes_history_files(tmp_path):
    """Baseline #8: nothing in-context; the witnessed transcript is handed
    to the worker as one file per event and the prompt points at it."""
    from membench.adapters import GrepAgentAdapter
    org_dir = _write_org(tmp_path)
    worker = MockWorker()
    adapter = GrepAgentAdapter(worker, shared=True)
    Runner(org_dir, adapter).run()
    prompt = worker.calls[0]
    assert "./history/" in prompt and "workspace history" in prompt
    assert "standup-decision-kebab" not in prompt          # nothing in-context
    files = worker.files_seen[0]
    assert "history/README.md" in files
    bodies = "\n".join(files.values())
    assert "standup-decision-kebab" in bodies              # witnessed event on disk
    assert "dm-secret-plan" not in bodies                  # unwitnessed stays out
    assert adapter.counters["last_context_chars"] == 0
    assert adapter.counters["last_files"] == len(files)


def test_pilot_cli_builds_every_adapter_and_writes_meta(tmp_path, monkeypatch):
    from membench import pilot
    from membench.adapters import GrepAgentAdapter
    from membench.typed_memory import TypedMemoryAdapter
    for name in pilot.ADAPTERS:
        a = pilot.build_adapter(name, MockWorker(), silo=True)
        assert hasattr(a, "ingest") and hasattr(a, "run_task")
    assert isinstance(pilot.build_adapter("grep", MockWorker()), GrepAgentAdapter)
    assert isinstance(pilot.build_adapter("typed", MockWorker()), TypedMemoryAdapter)
    org_dir = _write_org(tmp_path)
    monkeypatch.setattr(pilot, "CodexWorker", MockWorker)   # no live worker in tests
    out = tmp_path / "sut.jsonl"
    assert pilot.main(["nomemory", str(org_dir), str(out), "--no-only-valid"]) == 0
    rows = [json.loads(x) for x in out.read_text().splitlines()]
    assert rows[0]["run_id"] == "P-0001-01:sut"
    meta = json.loads((tmp_path / "sut.jsonl.meta.json").read_text())
    assert meta["worker"]["harness"] == "codex-cli 0.144.5" and meta["adapter"] == "nomemory"


def test_probes_override_and_on_row_callback(tmp_path):
    """Twin runs: the org dir has no probes.jsonl; probes come from the base
    org. on_row sees each row as soon as it exists (incremental writers)."""
    (tmp_path / "org.json").write_text(json.dumps(dict(ORG, org_id="org-twin")))
    (tmp_path / "events.jsonl").write_text(
        "".join(json.dumps(e) + "\n" for e in STREAM))
    seen = []
    worker = MockWorker()
    rows = Runner(tmp_path, NoMemoryAdapter(worker), probes=[PROBE],
                  on_row=seen.append).run()
    assert [r["run_id"] for r in rows] == ["P-0001-01:sut"] and seen == rows
    assert worker.calls[0].startswith("You are Bob, engineer (eng) at org-twin.")
