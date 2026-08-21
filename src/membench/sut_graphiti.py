"""Market system: Graphiti (Zep's OSS temporal knowledge graph, `graphiti-core`).

Everything runs embedded: the graph is the in-process **Kuzu** driver
(`graphiti_core.driver.kuzu_driver.KuzuDriver`, local db path; present in
graphiti-core 0.29.3 but marked deprecated upstream — no docker, no Neo4j).
Internal LLM / embedder / reranker = Gemini (`GeminiClient`, `GeminiEmbedder`,
`GeminiRerankerClient`) via `GEMINI_API_KEY`; vendor defaults are OpenAI
(gpt-5.5 / text-embedding-3-small / OpenAI reranker). Model names are
graphiti's Gemini defaults (gemini-3-flash-preview + gemini-2.5-flash-lite,
text-embedding-001) unless overridden here.

Cost: Graphiti performs LLM entity/edge extraction, dedup and temporal
invalidation on EVERY `add_episode` (several Gemini calls per event) —
`counters["add_episode_calls"]` counts them.

Store semantics: shared=True = ONE org-wide graph (`group_id="org"`), each
event ingested once (dedupe by event_id; the runner calls ingest once per
witness). This configuration does NOT enforce per-principal visibility (v1
scores no leakage; disclosed). shared=False = one `group_id` per principal,
the event ingested under each witness — the silo ablation. Graphiti group
ids allow only `[A-Za-z0-9_-]`, so principal ids are sanitized ("persona:a"
-> "persona_a"). Retrieval = `graphiti.search(...)` edge facts (with
`valid_at` when set) fed to `retrieval_prompt`; the async SDK is bridged
with a persistent event loop.
"""

from __future__ import annotations

import asyncio
import os
import re
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path

from .adapters import WorkerModel, _render_event
from .rag import retrieval_prompt

DEPENDENCY = "graphiti-core[kuzu,google-genai]>=0.29"
ORG_GROUP = "org"


def _group(scope: str) -> str:
    return re.sub(r"[^A-Za-z0-9_-]", "_", scope)


def _build_client(db_path: str):
    os.environ.setdefault("GRAPHITI_TELEMETRY_ENABLED", "false")
    from graphiti_core import Graphiti
    from graphiti_core.cross_encoder.gemini_reranker_client import GeminiRerankerClient
    from graphiti_core.driver.kuzu_driver import KuzuDriver
    from graphiti_core.embedder.gemini import GeminiEmbedder, GeminiEmbedderConfig
    from graphiti_core.llm_client.config import LLMConfig
    from graphiti_core.llm_client.gemini_client import GeminiClient
    key = os.environ["GEMINI_API_KEY"]
    return Graphiti(
        graph_driver=KuzuDriver(db=db_path),
        llm_client=GeminiClient(config=LLMConfig(api_key=key)),
        embedder=GeminiEmbedder(config=GeminiEmbedderConfig(api_key=key)),
        cross_encoder=GeminiRerankerClient(config=LLMConfig(api_key=key)),
    )


@dataclass
class GraphitiAdapter:
    """See module docstring. `client` is any object with async
    `build_indices_and_constraints()`, `add_episode(...)`, `search(...)`."""

    worker: WorkerModel
    shared: bool = True
    top_k: int = 8
    db_path: str = ":memory:"
    client: object = None
    counters: dict = field(default_factory=lambda: {
        "calls": 0, "context_chars": 0, "last_context_chars": 0, "ingest_calls": 0,
        "search_calls": 0, "retrieved": 0, "add_episode_calls": 0})
    _seen: set = field(default_factory=set)         # event_id (shared) / (pid, event_id)
    _loop: object = None
    _ready: bool = False

    def _run(self, coro):
        if self._loop is None:
            self._loop = asyncio.new_event_loop()
        return self._loop.run_until_complete(coro)

    def _get_client(self):
        if self.client is None:
            self.client = _build_client(self.db_path)
        if not self._ready:
            self._run(self.client.build_indices_and_constraints())
            self._ready = True
        return self.client

    def _scope(self, principal: str) -> str:
        return ORG_GROUP if self.shared else _group(principal)

    def ingest(self, principal: str, event: dict) -> None:
        self.counters["ingest_calls"] += 1
        key = event["event_id"] if self.shared else (principal, event["event_id"])
        if key in self._seen:
            return
        self._seen.add(key)
        client = self._get_client()
        when = datetime.fromisoformat(event["sim_time"].replace("Z", "+00:00"))
        if when.tzinfo is None:
            when = when.replace(tzinfo=UTC)
        self._run(client.add_episode(
            name=event["event_id"], episode_body=_render_event(event),
            source_description=event["surface"], reference_time=when,
            group_id=self._scope(principal)))
        self.counters["add_episode_calls"] += 1

    def _items(self, principal: str, task: str) -> list[str]:
        edges = self._run(self._get_client().search(
            task, group_ids=[self._scope(principal)], num_results=self.top_k))
        self.counters["search_calls"] += 1
        out = []
        for e in edges:
            fact = getattr(e, "fact", None) or str(e)
            valid = getattr(e, "valid_at", None)
            out.append(f"[{valid.isoformat()}] {fact}" if valid else fact)
        return out

    def run_task(self, principal: str, task: str) -> str:
        items = self._items(principal, task)
        prompt = retrieval_prompt(items, task)
        context = "\n\n".join(items)
        self.counters["calls"] += 1
        self.counters["retrieved"] += len(items)
        self.counters["last_context_chars"] = len(context)
        self.counters["context_chars"] += len(context)
        return self.worker.complete(prompt)


def smoke(org_dir: Path, n_events: int = 20, db_path: str = ":memory:") -> dict:
    """Ingest the first n events of an org into a real Graphiti/Kuzu graph
    (Gemini extraction; needs GEMINI_API_KEY) and run one search. Not a test."""
    import json

    from .adapters import MockWorker
    a = GraphitiAdapter(MockWorker(), db_path=db_path)
    with (Path(org_dir) / "events.jsonl").open() as fh:
        for i, line in enumerate(fh):
            if i >= n_events:
                break
            e = json.loads(line)
            a.ingest(e["participants"][0] if e.get("participants") else "org", e)
    print(a.run_task("smoke", "Task: summarize what this team decided recently."))
    print(a.counters)
    return a.counters


if __name__ == "__main__":
    import sys
    smoke(Path(sys.argv[1]), int(sys.argv[2]) if len(sys.argv) > 2 else 20)
