"""Market system: Mem0 (OSS `mem0ai`, local mode — embedded Qdrant + sqlite
history under a scratch dir; no docker, no Mem0 platform).

Store semantics — `shared=True`: ONE org-wide Mem0 store (`user_id="org"`),
each event added once (dedupe by event_id; the runner calls ingest once per
witness). This configuration does NOT enforce per-principal visibility:
every principal searches the same store (v1 scores no leakage; disclosed).
`shared=False`: per-principal stores keyed by the principal id (`user_id=
principal`), the event added under each witness — the silo ablation (H2).

Ingest = `Memory.add(text, user_id=scope, infer=True, metadata={sim_time})`
with text = `_render_event(event)` (vendor-default LLM extraction/consolidation
ON). Search = `Memory.search(task, filters={"user_id": scope}, top_k=k)`;
each hit becomes `[created_at] memory` (mem0's own wall-clock created_at when
present) and goes into `retrieval_prompt`. mem0ai 2.0.x rejects top-level
`user_id=` on search — `filters=` is the required form.

Internal LLM/embedder = Gemini via `GEMINI_API_KEY` (v1 freeze). Vendor
defaults: LLM openai `gpt-5-mini`, embedder openai `text-embedding-3-small`,
vector store Qdrant at /tmp/qdrant, history db ~/.mem0/history.db. Set
`MEM0_TELEMETRY=false` in the environment to silence vendor telemetry.
"""

from __future__ import annotations

import os
import tempfile
from dataclasses import dataclass, field
from pathlib import Path

from .adapters import WorkerModel, _render_event
from .rag import retrieval_prompt

DEPENDENCY = "mem0ai>=2.0,<3"          # plus the existing `google-genai` extra
LLM_MODEL = "gemini-2.5-flash"         # mem0's gemini provider default: gemini-2.0-flash
EMBED_MODEL = "models/gemini-embedding-001"
EMBED_DIMS = 768                       # mem0 gemini embedder default output size
ORG_SCOPE = "org"


def mem0_config(store_dir: Path) -> dict:
    """`Memory.from_config` dict: Gemini LLM + embedder, embedded Qdrant."""
    key = os.environ["GEMINI_API_KEY"]
    return {
        "llm": {"provider": "gemini", "config": {"model": LLM_MODEL, "api_key": key}},
        "embedder": {"provider": "gemini",
                     "config": {"model": EMBED_MODEL, "embedding_dims": EMBED_DIMS,
                                "api_key": key}},
        "vector_store": {"provider": "qdrant",
                         "config": {"collection_name": "membench",
                                    "embedding_model_dims": EMBED_DIMS,
                                    "path": str(store_dir / "qdrant"), "on_disk": False}},
        "history_db_path": str(store_dir / "history.db"),
    }


def _item_text(item: dict) -> str:
    text = str(item.get("memory", ""))
    stamp = item.get("created_at")
    return f"[{stamp}] {text}" if stamp else text


@dataclass
class Mem0Adapter:
    """SUTAdapter over a local Mem0 `Memory` (see module docstring)."""

    worker: WorkerModel
    shared: bool = True
    top_k: int = 8
    client: object = None                # injectable; built lazily from mem0_config
    store_dir: Path | None = None
    counters: dict = field(default_factory=lambda: {
        "calls": 0, "context_chars": 0, "last_context_chars": 0,
        "ingest_calls": 0, "search_calls": 0, "retrieved": 0, "memories_written": 0})
    _seen: set = field(default_factory=set)   # event_id (shared) / (pid, event_id)

    def _client(self):
        if self.client is None:
            from mem0 import Memory  # optional dependency (DEPENDENCY)
            root = self.store_dir or Path(tempfile.mkdtemp(prefix="membench-mem0-"))
            self.client = Memory.from_config(mem0_config(root))
        return self.client

    def _scope(self, principal: str) -> str:
        return ORG_SCOPE if self.shared else principal

    def ingest(self, principal: str, event: dict) -> None:
        key = event["event_id"] if self.shared else (principal, event["event_id"])
        if key in self._seen:
            return
        self._seen.add(key)
        result = self._client().add(
            _render_event(event), user_id=self._scope(principal), infer=True,
            metadata={"sim_time": event.get("sim_time"), "event_id": event["event_id"]})
        self.counters["ingest_calls"] += 1
        self.counters["memories_written"] += len((result or {}).get("results", []))

    def run_task(self, principal: str, task: str) -> str:
        hits = self._client().search(
            task, filters={"user_id": self._scope(principal)}, top_k=self.top_k)
        items = [_item_text(h) for h in (hits or {}).get("results", [])][: self.top_k]
        prompt = retrieval_prompt(items, task)
        context = "\n\n".join(items)
        self.counters["calls"] += 1
        self.counters["search_calls"] += 1
        self.counters["retrieved"] += len(items)
        self.counters["last_context_chars"] = len(context)
        self.counters["context_chars"] += len(context)
        return self.worker.complete(prompt)


def smoke(org_dir: Path, n_events: int = 20) -> dict:
    """Not a test: ingest the first n events of an org into a real local Mem0
    (Gemini key required) and run one search; print and return counters."""
    import json

    from .adapters import MockWorker
    events = [json.loads(line) for line in
              (Path(org_dir) / "events.jsonl").read_text().splitlines()][:n_events]
    a = Mem0Adapter(MockWorker())
    for e in events:
        a.ingest(ORG_SCOPE, e)
    a.run_task(ORG_SCOPE, "Task: summarize the most recent decisions you know about.")
    print(a.worker.calls[-1])
    print(a.counters)
    return a.counters


if __name__ == "__main__":
    import sys
    smoke(Path(sys.argv[1]), int(sys.argv[2]) if len(sys.argv) > 2 else 20)
