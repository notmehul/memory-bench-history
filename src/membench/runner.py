"""Pilot runner: per-principal event delivery + probe injection (§9).

Feeds the SUT-facing stream (`events.jsonl`) to an adapter, one `ingest`
call per witness per event, following the event-stream contract's delivery
model (§3): participants always witness; org_public events reach every
active principal; team_confidential events reach the team's members at that
time. Witness metadata (visibility, team) lives in `org.json`'s event
index — never in the SUT-facing stream.

Probes inject immediately after their `inject_after_event` event, to their
probe principal only. The task prompt mirrors the screening harness's floor
prompt (persona line, frame line, task, behavioural scaffold) WITHOUT any
fact context — the adapter supplies context — and without the screening
harness's file-transport instruction, which belongs to the worker transport,
not the task. Results rows are shaped like the screening scorer's
`results.jsonl` ({run_id, output, ...}) with run_id `<probe_id>:sut`.
"""

from __future__ import annotations

import json
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path

from .adapters import SUTAdapter
from .belief import is_member
from .ledger import EventIndex, Ledger, load_event_index, load_ledger
from .workers import WorkerError

# Mirrors scripts/screen_probes.py::_FRAME_LINE / _persona_line so SUT runs
# stay prompt-comparable with the screening floor/ceiling anchors.
_FRAME_LINE = {
    "org_facing": "The artifact you produce is org-facing (visible to the whole company).",
    "team_internal": "The artifact you produce is internal to your team ({ref}).",
    "personal": "The artifact is for your own personal use.",
    "project": "The artifact belongs to the cross-team project ({ref}).",
    "external": "The artifact is client-facing (external).",
}

_SCAFFOLD = (
    "Output only the deliverable itself — no meta-commentary and no notes "
    "about missing information; make reasonable choices and produce your "
    "best version. Apply only what fits this artifact's audience and scope "
    "— do not enumerate practices that belong to other scopes, teams, or "
    "individuals. Where the task calls for thresholds, cadences, or "
    "figures, state them concretely."
)


class RunnerError(Exception):
    pass


def _persona_line(org: dict, pid: str) -> str:
    p = next(x for x in org["entities"]["personas"] if x["id"] == pid)
    name = pid.split(":", 1)[1].capitalize()
    teams = ", ".join(t.split(":", 1)[1] for t in p["teams"]) or "exec staff"
    return f"You are {name}, {p['role']} ({teams}) at {org['org_id']}."


def task_prompt(org: dict, probe: dict) -> str:
    frame = probe["context_frame"]
    frame_line = _FRAME_LINE[frame["kind"]].format(ref=frame["ref"] or "")
    return "\n\n".join([
        _persona_line(org, probe["principal"]),
        frame_line,
        f"Task: {probe['task']}",
        _SCAFFOLD,
    ])


def _active(ledger: Ledger, index: EventIndex, pid: str, t: int) -> bool:
    p = ledger.personas[pid]
    if p.joins_at is not None and index.index_of(p.joins_at) > t:
        return False
    return not (p.leaves_at is not None and index.index_of(p.leaves_at) <= t)


def witnesses(ledger: Ledger, index: EventIndex, t: int) -> list[str]:
    """Principals whose agents receive event at stream position t (§3)."""
    meta = index.events[t]
    out = set(meta.participants)
    if meta.visibility == "org_public":
        out |= {pid for pid in ledger.personas
                if _active(ledger, index, pid, t)}
    elif meta.visibility == "team_confidential":
        if meta.team is None:
            raise RunnerError(
                f"{meta.event_id}: team_confidential event without team")
        out |= {pid for pid in ledger.personas
                if is_member(ledger, index, pid, meta.team, t)}
    elif meta.visibility != "private":
        raise RunnerError(
            f"{meta.event_id}: unknown visibility {meta.visibility!r}")
    return sorted(pid for pid in out if pid in ledger.personas)


@dataclass
class Runner:
    """Drives one org's stream through one adapter.

    The adapter owns its worker; the runner never calls the worker directly.

    `probes` overrides the org's own `probes.jsonl` — twin orgs carry no
    probes of their own, so a twin run is driven with the BASE org's probes
    against the twin's stream/org.json (exactly as the screening harness
    builds twin_ceiling runs). `on_row` is called with each result row as
    soon as it exists (incremental, resumable writers).
    """

    org_dir: Path
    adapter: SUTAdapter
    probes: list[dict] | None = None
    on_row: Callable[[dict], None] | None = None

    def run(self, out_path: Path | None = None) -> list[dict]:
        org = json.loads((self.org_dir / "org.json").read_text())
        ledger, index = load_ledger(org), load_event_index(org)
        stream = [json.loads(line) for line in
                  (self.org_dir / "events.jsonl").read_text().splitlines()]
        probes = self.probes
        if probes is None:
            probes = [json.loads(line) for line in
                      (self.org_dir / "probes.jsonl").read_text().splitlines()]

        if [e["event_id"] for e in stream] != [e.event_id for e in index.events]:
            raise RunnerError("events.jsonl does not align with org.json event index")
        by_event: dict[str, list[dict]] = {}
        for probe in probes:
            if probe["inject_after_event"] not in index:
                raise RunnerError(
                    f"{probe['probe_id']}: unknown inject_after_event "
                    f"{probe['inject_after_event']}")
            by_event.setdefault(probe["inject_after_event"], []).append(probe)

        rows = []
        for t, event in enumerate(stream):
            for pid in witnesses(ledger, index, t):
                self.adapter.ingest(pid, event)
            for probe in by_event.get(event["event_id"], ()):
                row = {"run_id": f"{probe['probe_id']}:sut"}
                try:
                    row["output"] = self.adapter.run_task(
                        probe["principal"], task_prompt(org, probe))
                except WorkerError as e:
                    # Empty-output rule (probe-spec v0.4.3): a worker failure
                    # is a recorded null deliverable that scores 0.0 on every
                    # assertion — never a dropped run.
                    row["output"] = None
                    row["error"] = str(e)
                row["context_chars"] = self.adapter.counters.get(
                    "last_context_chars", 0)
                rows.append(row)
                if self.on_row is not None:
                    self.on_row(row)
        if out_path is not None:
            out_path.write_text(
                "".join(json.dumps(r) + "\n" for r in rows))
        return rows
