"""Market system: Supermemory (hosted API, official `supermemory` SDK).

Hosted only — there is no local mode; the internal LLM/embedder behind
memory extraction is vendor-managed and NOT configurable, so no Gemini
wiring applies (v1 freeze note: this system runs on the vendor default).

Ingest = `client.documents.add(content=_render_event(event), container_tag=
<scope>, custom_id=..., document_date=sim_time, metadata={event_id, sim_time,
surface})` (SDK 3.59: `documents.add`; `memories.add` no longer exists).
Search = `client.search.memories(q=task, container_tag=<scope>, limit=top_k)`
whose results carry `.memory` (extracted memory text; `.chunk` for hybrid/
document mode) → `retrieval_prompt`. Scope: `shared=True` uses ONE org-wide
container tag ("org") and ingests each event once (dedupe by event_id) — this
does NOT enforce per-principal visibility (v1 scores no leakage; disclosed);
`shared=False` is the silo ablation: one container tag per principal, each
event ingested under every witness.

Ingestion is asynchronous server-side (documents are queued → extracted →
indexed after `add` returns). The pilot run MUST set `ingest_settle_seconds`
(sleep before a search that follows new ingests) and/or `wait_for_processing`
(poll `client.documents.list_processing()` until empty, bounded by
`settle_timeout`) so probes see the data; `smoke` does both.
"""

from __future__ import annotations

import os
import re
import time
from dataclasses import dataclass, field
from pathlib import Path

from .adapters import WorkerModel, _render_event
from .rag import retrieval_prompt

DEPENDENCY = "supermemory>=3.59"
ORG_TAG = "org"
_TAG_OK = re.compile(r"[^A-Za-z0-9._-]")


def _tag(scope: str) -> str:
    """Container tags / custom ids allow only [A-Za-z0-9._-]."""
    return _TAG_OK.sub("_", scope)


@dataclass
class SupermemoryAdapter:
    worker: WorkerModel
    shared: bool = True
    top_k: int = 8
    ingest_settle_seconds: float = 0
    wait_for_processing: bool = False
    settle_timeout: float = 120
    client: object = None
    counters: dict = field(default_factory=lambda: {
        "calls": 0, "context_chars": 0, "last_context_chars": 0, "ingest_calls": 0,
        "search_calls": 0, "retrieved": 0, "settle_waits": 0, "settle_seconds": 0.0})
    _seen: set = field(default_factory=set)      # (scope, event_id) already ingested
    _dirty: bool = False                          # ingests since the last search

    def _get_client(self):
        if self.client is None:
            from supermemory import Supermemory  # optional dependency
            self.client = Supermemory(api_key=os.environ["SUPERMEMORY_API_KEY"])
        return self.client

    def _scope(self, principal: str) -> str:
        return ORG_TAG if self.shared else _tag(principal)

    def ingest(self, principal: str, event: dict) -> None:
        scope = self._scope(principal)
        key = (scope, event["event_id"])
        if key in self._seen:
            return
        self._seen.add(key)
        self._get_client().documents.add(
            content=_render_event(event), container_tag=scope,
            custom_id=_tag(f"{scope}.{event['event_id']}"), document_date=event["sim_time"],
            metadata={"event_id": event["event_id"], "sim_time": event["sim_time"],
                      "surface": event["surface"]})
        self.counters["ingest_calls"] += 1
        self._dirty = True

    def _settle(self) -> None:
        if not self._dirty:
            return
        self._dirty = False
        t0 = time.monotonic()
        if self.ingest_settle_seconds:               # let the queue register first
            time.sleep(self.ingest_settle_seconds)
        if self.wait_for_processing:
            while time.monotonic() - t0 < self.settle_timeout:
                if self._get_client().documents.list_processing().total_count == 0:
                    break
                time.sleep(2)
        self.counters["settle_waits"] += 1
        self.counters["settle_seconds"] += time.monotonic() - t0

    @staticmethod
    def _item_text(result) -> str:
        text = getattr(result, "memory", None) or getattr(result, "chunk", None) or ""
        meta = getattr(result, "metadata", None) or {}
        when = meta.get("sim_time")
        return f"[{when}] {text}" if when else text

    def run_task(self, principal: str, task: str) -> str:
        self._settle()
        resp = self._get_client().search.memories(
            q=task, container_tag=self._scope(principal), limit=self.top_k)
        memories = [t for t in (self._item_text(r) for r in resp.results) if t]
        context = "\n\n".join(memories)
        self.counters["calls"] += 1
        self.counters["search_calls"] += 1
        self.counters["retrieved"] += len(memories)
        self.counters["last_context_chars"] = len(context)
        self.counters["context_chars"] += len(context)
        return self.worker.complete(retrieval_prompt(memories, task))


def smoke(org_dir: Path, n_events: int = 20) -> dict:
    """Ingest the first `n_events` of an org into the real service (shared
    scope), wait for processing, run one search; print counters. Not a test."""
    import json

    from .adapters import MockWorker

    events = [json.loads(line) for line in
              (Path(org_dir) / "events.jsonl").read_text().splitlines()[:n_events]]
    a = SupermemoryAdapter(MockWorker(), ingest_settle_seconds=5, wait_for_processing=True)
    for e in events:
        a.ingest(e["participants"][0] if e.get("participants") else "smoke", e)
    a.run_task("smoke", f"Task: summarize what happened around {events[0]['surface']}.")
    print(a.worker.calls[-1][:2000])
    print(a.counters)
    return a.counters


if __name__ == "__main__":
    import sys

    smoke(Path(sys.argv[1]), int(sys.argv[2]) if len(sys.argv) > 2 else 20)
