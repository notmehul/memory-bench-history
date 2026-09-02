"""SUT adapter interface and reference baseline adapters (architecture §9).

The adapter surface is deliberately minimal and is the ONLY thing the
benchmark observes: `ingest(principal, event)` — called once per witness per
event by the runner — and `run_task(principal, task) -> output`. Memory
internals are never inspected.

This module ships the worker seam plus the two zero-dependency baselines:
no-memory (the floor) and full-transcript long-context, whose `shared` flag
is the pilot's silo-ablation configuration. Derived-memory baselines (RAG,
summaries, products, file-graph) plug into the same interface later.

Workers: only `MockWorker` lives here. The pilot's codex-backed worker is a
separate concern (it owns transport details such as file-based output
capture) and is added at Phase 5 run time.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Protocol


class WorkerModel(Protocol):
    """The fixed task model behind every adapter (dataset-plan standing
    decision: gpt-5.4, effort medium, codex-cli — pinned). Adapters must
    treat it as a pure prompt->text function."""

    def complete(self, prompt: str, files: dict[str, str] | None = None) -> str: ...


@dataclass
class MockWorker:
    """Deterministic worker for tests: returns the response whose key is a
    substring of the prompt, else `default`. Records every prompt (and the
    files a tools-baseline adapter handed it)."""

    responses: dict[str, str] = field(default_factory=dict)
    default: str = "mock deliverable"
    calls: list[str] = field(default_factory=list)
    files_seen: list[dict] = field(default_factory=list)

    def complete(self, prompt: str, files: dict[str, str] | None = None) -> str:
        self.calls.append(prompt)
        self.files_seen.append(dict(files or {}))
        for key, response in self.responses.items():
            if key in prompt:
                return response
        return self.default


class SUTAdapter(Protocol):
    counters: dict

    def ingest(self, principal: str, event: dict) -> None: ...

    def run_task(self, principal: str, task: str) -> str: ...


def _render_event(event: dict) -> str:
    who = ", ".join(event.get("participants", ()))
    when = event.get("sim_time")
    stamp = f"[{when}] " if when else ""      # v1 streams carry no timestamps
    return (
        f"{stamp}{event['surface']} ({event['channel']}; "
        f"participants: {who})\n{event['content']}"
    )


@dataclass
class NoMemoryAdapter:
    """Floor baseline: no ingestion, the task prompt goes to the worker bare."""

    worker: WorkerModel
    counters: dict = field(default_factory=lambda: {"calls": 0, "context_chars": 0,
                                                    "last_context_chars": 0})

    def ingest(self, principal: str, event: dict) -> None:
        return None

    def run_task(self, principal: str, task: str) -> str:
        self.counters["calls"] += 1
        self.counters["last_context_chars"] = 0
        return self.worker.complete(task)


@dataclass
class FullTranscriptAdapter:
    """Long-context baseline: prepend the principal's full witnessed
    transcript to every task.

    shared=True keeps one org-wide event store with per-principal access
    lists (each principal still only reads events the runner delivered to
    them, so visibility is respected); shared=False keeps fully isolated
    per-principal copies — the silo-ablation configuration. For a raw
    transcript the two produce identical *context text*; they differ in
    storage (counters["stored_events"]) and become behaviourally different
    for derived-memory adapters that share abstractions, which is what the
    silo ablation exists to measure.
    """

    worker: WorkerModel
    shared: bool = True
    counters: dict = field(default_factory=lambda: {"calls": 0, "context_chars": 0,
                                                    "last_context_chars": 0,
                                                    "stored_events": 0})
    _shared_store: dict = field(default_factory=dict)   # event_id -> event
    _access: dict = field(default_factory=dict)         # pid -> [event_id]
    _silo_store: dict = field(default_factory=dict)     # pid -> [event]

    def ingest(self, principal: str, event: dict) -> None:
        if self.shared:
            self._shared_store.setdefault(event["event_id"], event)
            self._access.setdefault(principal, []).append(event["event_id"])
            self.counters["stored_events"] = len(self._shared_store)
        else:
            self._silo_store.setdefault(principal, []).append(event)
            self.counters["stored_events"] = sum(
                len(v) for v in self._silo_store.values())

    def _transcript(self, principal: str) -> list[dict]:
        if self.shared:
            return [self._shared_store[eid]
                    for eid in self._access.get(principal, [])]
        return list(self._silo_store.get(principal, []))

    def run_task(self, principal: str, task: str) -> str:
        events = self._transcript(principal)
        context = "\n\n".join(_render_event(e) for e in events)
        prompt = task
        if context:
            prompt = (
                "Your accumulated workspace history, oldest first:\n\n"
                f"{context}\n\n{task}"
            )
        self.counters["calls"] += 1
        self.counters["last_context_chars"] = len(context)
        self.counters["context_chars"] += len(context)
        return self.worker.complete(prompt)


def _event_filename(i: int, event: dict) -> str:
    stamp = str(event.get("sim_time") or "").replace(":", "").replace(" ", "_")
    return f"history/{i:05d}_{stamp}_{event['surface']}.md"


@dataclass
class GrepAgentAdapter:
    """Baseline #8 (standards-audit B.4): the worker with plain file
    read/search tools over its witnessed transcript — the trivial-tools
    floor any memory product must beat. The transcript is materialized as
    one file per witnessed event (chronological, in `history/`) in the
    worker's working directory; nothing is retrieved or summarized for the
    worker, it must search itself. Storage follows FullTranscriptAdapter
    (shared store with access lists, or per-principal silos).
    """

    worker: WorkerModel
    shared: bool = True
    counters: dict = field(default_factory=lambda: {"calls": 0, "context_chars": 0,
                                                    "last_context_chars": 0,
                                                    "stored_events": 0,
                                                    "last_files": 0})
    _shared_store: dict = field(default_factory=dict)
    _access: dict = field(default_factory=dict)
    _silo_store: dict = field(default_factory=dict)

    def ingest(self, principal: str, event: dict) -> None:
        FullTranscriptAdapter.ingest(self, principal, event)  # same storage

    def _transcript(self, principal: str) -> list[dict]:
        return FullTranscriptAdapter._transcript(self, principal)

    def run_task(self, principal: str, task: str) -> str:
        events = self._transcript(principal)
        files = {_event_filename(i, e): _render_event(e) + "\n"
                 for i, e in enumerate(events)}
        if files:
            files["history/README.md"] = (
                "Your witnessed workspace history: one file per event, "
                "chronological by filename. Nothing here has been filtered "
                "or summarized for you.\n")
        prompt = task
        if files:
            prompt = (
                "Your witnessed workspace history is on disk in ./history/ "
                "(one file per event, chronological; see history/README.md). "
                "Search and read it with your file tools as needed before "
                "writing.\n\n" + task)
        total = sum(len(v) for v in files.values())
        self.counters["calls"] += 1
        self.counters["last_files"] = len(files)
        self.counters["last_context_chars"] = 0      # nothing is in-context
        self.counters["context_chars"] += 0
        self.counters["disk_chars"] = self.counters.get("disk_chars", 0) + total
        return self.worker.complete(prompt, files=files)
