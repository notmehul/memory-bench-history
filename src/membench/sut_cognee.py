"""Market system adapter: Cognee (OSS `cognee` package, embedded/local).

Every event is `cognee.add(_render_event(event), dataset_name=<scope>)`;
`cognee.cognify(datasets=[scope])` builds the graph + chunk index and is
run *lazily* — once per scope on the first `run_task` after new ingests
(dirty flag), so it runs at most once per probe injection, never per event
(`counters["cognify_calls"]`). Retrieval is `cognee.search(query_type=
SearchType.CHUNKS, top_k=...)`: the raw retrieved chunk texts (vector
similarity, no LLM answer generation), handed to `retrieval_prompt`.

Scope: shared=True keeps ONE org-wide dataset ("org"), each event added
once (dedupe by event_id; the runner ingests once per witness). This
configuration does NOT enforce per-principal visibility (v1 scores no
leakage; disclosed). shared=False keeps one dataset per principal
(silo ablation), each event added under every witness.

Internal LLM/embedder (vendor default: OpenAI gpt-5-mini +
text-embedding-3-large): configured to Gemini via env before the SDK is
first imported (`configure_gemini_env`; key from GEMINI_API_KEY). Storage:
cognee defaults — sqlite relational, lancedb vector, ladybug/kuzu graph —
all embedded, no docker. The SDK is imported lazily; the client is
injectable so tests run with a fake and no network.
"""

from __future__ import annotations

import asyncio
import os
import re
import threading
from dataclasses import dataclass, field
from pathlib import Path

from .adapters import WorkerModel, _render_event
from .rag import retrieval_prompt

DEPENDENCY = "cognee>=1.4"
GEMINI_LLM_MODEL = "gemini/gemini-2.5-flash"           # litellm route
GEMINI_EMBEDDING_MODEL = "gemini/gemini-embedding-001"
ORG_DATASET = "org"


def configure_gemini_env() -> None:
    """Point cognee's LLM + embedder at Gemini (only where unset)."""
    key = os.environ.get("GEMINI_API_KEY", "")
    for k, v in {"LLM_PROVIDER": "gemini", "LLM_MODEL": GEMINI_LLM_MODEL,
                 "LLM_API_KEY": key, "EMBEDDING_PROVIDER": "gemini",
                 "EMBEDDING_MODEL": GEMINI_EMBEDDING_MODEL,
                 "EMBEDDING_DIMENSIONS": "3072", "EMBEDDING_API_KEY": key}.items():
        os.environ.setdefault(k, v)


def _flatten_texts(result) -> list[str]:
    """CHUNKS results -> chunk texts. Handles both SDK shapes: access-control
    mode `[{"dataset_name":..., "search_result": [payload,...]}]` and plain
    `[payload,...]` (payload = dict with "text")."""
    if isinstance(result, str):
        return [result]
    if isinstance(result, dict):
        if "search_result" in result:
            return _flatten_texts(result["search_result"])
        return [str(result["text"])] if "text" in result else []
    if isinstance(result, (list, tuple)):
        return [t for r in result for t in _flatten_texts(r)]
    return []


class CogneeClient:
    """Sync bridge over the async SDK on a persistent background loop
    (cognee's engines bind to the loop they were created on). `root_dir`
    isolates the store; it is wiped on first use so every run starts empty."""

    def __init__(self, root_dir: Path | None = None):
        self.root_dir = Path(root_dir or Path.home() / ".membench" / "cognee")
        self._loop = None
        self._cognee = None

    def _run(self, coro):
        if self._loop is None:
            self._loop = asyncio.new_event_loop()
            threading.Thread(target=self._loop.run_forever, daemon=True).start()
        return asyncio.run_coroutine_threadsafe(coro, self._loop).result()

    def _sdk(self):
        if self._cognee is None:
            configure_gemini_env()
            import cognee  # optional dependency
            cognee.config.system_root_directory(str(self.root_dir / "system"))
            cognee.config.data_root_directory(str(self.root_dir / "data"))
            self._run(cognee.prune.prune_data())
            self._run(cognee.prune.prune_system(metadata=True))
            self._cognee = cognee
        return self._cognee

    def add(self, text: str, dataset: str) -> None:
        self._run(self._sdk().add(text, dataset_name=dataset))

    def cognify(self, datasets: list[str]) -> None:
        self._run(self._sdk().cognify(datasets=list(datasets)))

    def search(self, query: str, dataset: str, top_k: int) -> list[str]:
        c = self._sdk()
        res = self._run(c.search(query_text=query, query_type=c.SearchType.CHUNKS,
                                 datasets=[dataset], top_k=top_k))
        return _flatten_texts(res)


def _dataset_for(principal: str) -> str:
    return "silo_" + re.sub(r"[^A-Za-z0-9_]", "_", principal)


@dataclass
class CogneeAdapter:
    """See module docstring. `client` must expose add/cognify/search as
    `CogneeClient` does; built lazily when None."""

    worker: WorkerModel
    shared: bool = True
    top_k: int = 8
    client: object = None
    counters: dict = field(default_factory=lambda: {
        "calls": 0, "context_chars": 0, "last_context_chars": 0, "ingest_calls": 0,
        "search_calls": 0, "retrieved": 0, "cognify_calls": 0})
    _seen: set = field(default_factory=set)      # event_ids (shared mode)
    _dirty: set = field(default_factory=set)     # datasets with un-cognified adds

    def _client(self):
        if self.client is None:
            self.client = CogneeClient()
        return self.client

    def _scope(self, principal: str) -> str:
        return ORG_DATASET if self.shared else _dataset_for(principal)

    def ingest(self, principal: str, event: dict) -> None:
        if self.shared:
            if event["event_id"] in self._seen:
                return
            self._seen.add(event["event_id"])
        scope = self._scope(principal)
        self._client().add(_render_event(event), scope)
        self._dirty.add(scope)
        self.counters["ingest_calls"] += 1

    def run_task(self, principal: str, task: str) -> str:
        scope = self._scope(principal)
        if scope in self._dirty:
            self._client().cognify([scope])
            self._dirty.discard(scope)
            self.counters["cognify_calls"] += 1
        items = list(self._client().search(task, scope, self.top_k))
        prompt = retrieval_prompt(items, task)
        context = "\n\n".join(items)
        self.counters["calls"] += 1
        self.counters["search_calls"] += 1
        self.counters["retrieved"] += len(items)
        self.counters["last_context_chars"] = len(context)
        self.counters["context_chars"] += len(context)
        return self.worker.complete(prompt)


def smoke(org_dir: Path, n_events: int = 20) -> dict:
    """Ingest the first n events of an org (all witnesses -> shared org
    dataset), cognify once, run one CHUNKS search against the real
    embedded store (needs GEMINI_API_KEY). Not a test."""
    import json

    class _Echo:
        def complete(self, prompt, files=None):
            return prompt

    a = CogneeAdapter(_Echo())
    with open(Path(org_dir) / "events.jsonl") as f:
        events = [json.loads(line) for _, line in zip(range(n_events), f, strict=False)]
    for e in events:
        for p in e.get("participants", []):
            a.ingest(p, e)
    out = a.run_task(events[0]["participants"][0], "Summarize the recent decisions.")
    print(out[:2000])
    print(a.counters)
    return a.counters


if __name__ == "__main__":  # pragma: no cover
    import sys
    smoke(Path(sys.argv[1]), int(sys.argv[2]) if len(sys.argv) > 2 else 20)
