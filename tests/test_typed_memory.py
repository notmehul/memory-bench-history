"""Typed-memory reference implementation (baseline #6): extraction seam,
visibility, supersession, rendering — with a scripted worker, no live calls."""

import json

from membench.adapters import MockWorker
from membench.typed_memory import (
    PROMPT_PATH,
    TypedMemoryAdapter,
    load_prompt,
    parse_nodes,
    prompt_hash,
)


class ScriptedWorker(MockWorker):
    """Extraction: returns JSON keyed by a substring of the event; task
    calls (prompt contains 'Task:') return the default deliverable."""

    def complete(self, prompt, files=None):
        self.calls.append(prompt)
        if "Task:" in prompt:
            return "deliverable"
        for key, response in self.responses.items():
            if key in prompt:
                return response
        return "[]"


def _ev(eid, content, t="2026-03-01T09:00:00Z"):
    return {"event_id": eid, "sim_time": t, "channel": "meeting", "surface": "team:eng/standup",
            "participants": ["persona:alice"], "content": content}


def test_prompt_is_loaded_and_hashable():
    assert PROMPT_PATH.exists()
    assert "{event}" in load_prompt() and "{existing}" in load_prompt()
    assert len(prompt_hash()) == 12


def test_parse_nodes_rejects_garbage_and_filters_kinds():
    assert parse_nodes("") is None and parse_nodes("no json here") is None
    assert parse_nodes('{"a": 1}') is None
    raw = ('Sure: [{"kind":"rule","statement":"Standup is 15 minutes.","tier":"team",'
           '"scope_ref":"team:eng","topic":"standup"},'
           '{"kind":"nonsense","statement":"x"},{"statement":""}]')
    nodes = parse_nodes(raw)
    assert len(nodes) == 1 and nodes[0]["topic"] == "standup"


def test_visibility_supersession_and_rendering():
    def node(stmt, **extra):
        return json.dumps([{"kind": "rule", "statement": stmt, "tier": "team",
                            "scope_ref": "team:eng", "topic": "standup-length", **extra}])
    w = ScriptedWorker(responses={
        "standup-15": node("Team eng standup lasts 15 minutes."),
        "standup-30": node("Team eng standup lasts 30 minutes.", conflicts_with=["n00001"]),
    })
    a = TypedMemoryAdapter(w, shared=True)
    a.ingest("persona:alice", _ev("E-1", "standup-15"))
    a.ingest("persona:bob", _ev("E-1", "standup-15"))          # widens visibility only
    a.ingest("persona:alice", _ev("E-2", "standup-30", "2026-03-02T09:00:00Z"))
    assert a.counters["extraction_calls"] == 2 and a.counters["nodes_stored"] == 2
    assert a.counters["superseded"] == 1
    # the second extraction prompt listed the existing node
    assert "n00001: Team eng standup lasts 15 minutes." in w.calls[1]
    # alice sees the current node + the superseded one under Previously
    a.run_task("persona:alice", "Task: Write the standup guide for eng; standup length.")
    prompt = w.calls[-1]
    assert "typed memory" in prompt and "30 minutes" in prompt
    assert "Previously (superseded" in prompt and "15 minutes" in prompt
    assert prompt.index("30 minutes") < prompt.index("Previously")
    # bob only witnessed E-1: sees the 15-minute node (as current for him? no —
    # supersession is store-wide; bob sees nothing current, and the old node
    # is superseded) -> only the Previously list
    a.run_task("persona:bob", "Task: standup length?")
    assert "30 minutes" not in w.calls[-1] and "15 minutes" in w.calls[-1]
    # cara witnessed nothing: no context at all
    a.run_task("persona:cara", "Task: standup length?")
    assert "typed memory" not in w.calls[-1]
    assert a.counters["last_context_chars"] == 0


def test_silo_stores_are_isolated_and_ablations_flag():
    w = ScriptedWorker(responses={
        "rule-a": json.dumps([{"kind": "rule", "tier": "org", "topic": "deploy-freeze",
                               "statement": "Company deploys freeze on Fridays."}])})
    silo = TypedMemoryAdapter(w, shared=False)
    silo.ingest("persona:alice", _ev("E-1", "rule-a"))
    silo.ingest("persona:bob", _ev("E-1", "rule-a"))
    assert silo.counters["extraction_calls"] == 2       # once per witnessing principal
    flat = TypedMemoryAdapter(ScriptedWorker(responses=w.responses),
                              tiers=False, supersession=False)
    flat.ingest("persona:alice", _ev("E-1", "rule-a"))
    flat.run_task("persona:alice", "Task: deploy freeze note")
    assert "[org scope: org-wide]" in flat.worker.calls[-1]


def test_malformed_extraction_is_skipped_not_fatal():
    w = ScriptedWorker(responses={"bad": "not json at all"})
    a = TypedMemoryAdapter(w)
    a.ingest("persona:alice", _ev("E-1", "bad"))
    assert a.counters["skipped_events"] == 1 and a.counters["nodes_stored"] == 0
