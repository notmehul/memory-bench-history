"""Baseline #3 — naive RAG over the raw witnessed stream (chunk = event,
top-k by a retriever), and the retriever seam for the pinned embedding
model (standards-audit B.5: ONE pinned, reported embedding model for all
RAG-class baselines; one alternate as ablation — the pin is a PI decision
and adds a dependency, so it is not chosen here).

Ships with `LexicalRetriever` (BM25-style scoring, stdlib only) so the
RAG-class code path is testable without a network, and `EmbeddingRetriever`,
which takes any `embed(texts) -> vectors` callable — the pinned one is
`GeminiEmbedder(EMBEDDING_MODEL).embed` — and embeds each chunk once
(cached by chunk text, i.e. once per event even in shared mode). Storage
follows FullTranscriptAdapter (shared store with access lists, or
per-principal silos); the prompt is `retrieval_prompt`, the one template
every retrieval-style adapter (this one, market systems) reuses.
"""

from __future__ import annotations

import math
import os
import re
from collections import Counter
from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Protocol

from .adapters import FullTranscriptAdapter, WorkerModel, _render_event

# v1 freeze pin (dataset-plan; standards-audit B.5): the ONE embedding model
# behind every RAG-class baseline.
EMBEDDING_MODEL = "gemini-embedding-001"

_TOKEN = re.compile(r"[a-z0-9][a-z0-9$%'-]*")
_STOP = frozenset([
    "a", "an", "and", "are", "as", "at", "be", "by", "for", "from", "has", "have", "in",
    "is", "it", "its", "of", "on", "or", "that", "the", "their", "there", "this", "to",
    "was", "were", "will", "with", "when", "what", "who", "how", "you", "your", "we",
    "our", "task", "write", "draft"])


def _toks(text: str) -> list[str]:
    return [t for t in _TOKEN.findall(text.lower()) if t not in _STOP]


class Retriever(Protocol):
    def rank(self, query: str, docs: list[str]) -> list[int]: ...


@dataclass
class LexicalRetriever:
    """BM25 (k1=1.5, b=0.75) computed per query over the candidate docs —
    small corpora (one org's events), so no persistent index is needed."""

    k1: float = 1.5
    b: float = 0.75

    def rank(self, query: str, docs: list[str]) -> list[int]:
        q = _toks(query)
        if not docs or not q:
            return list(range(len(docs)))
        tf = [Counter(_toks(d)) for d in docs]
        lens = [sum(c.values()) for c in tf]
        avg = sum(lens) / len(lens) if lens else 1.0
        n = len(docs)
        df = Counter()
        for c in tf:
            df.update(set(c))
        scores = []
        for i, c in enumerate(tf):
            s = 0.0
            for t in set(q):
                if t not in c:
                    continue
                idf = math.log(1 + (n - df[t] + 0.5) / (df[t] + 0.5))
                num = c[t] * (self.k1 + 1)
                den = c[t] + self.k1 * (1 - self.b + self.b * lens[i] / (avg or 1.0))
                s += idf * num / den
            scores.append((-s, i))
        scores.sort()
        return [i for _, i in scores]


@dataclass
class GeminiEmbedder:
    """The pinned embedder (`EMBEDDING_MODEL`) via the `google-genai` SDK
    (optional extra `adapters`); key from `GEMINI_API_KEY`. The SDK is
    imported lazily on first use so the module imports without it. Requests
    are batched at the API's per-call limit."""

    model: str = EMBEDDING_MODEL
    batch_size: int = 100
    counters: dict = field(default_factory=lambda: {"calls": 0, "texts": 0})
    _client: object = None

    def _get_client(self):
        if self._client is None:
            from google import genai  # optional dependency
            self._client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])
        return self._client

    def embed(self, texts: list[str]) -> list[list[float]]:
        client = self._get_client()
        out: list[list[float]] = []
        for i in range(0, len(texts), self.batch_size):
            batch = texts[i:i + self.batch_size]
            resp = client.models.embed_content(model=self.model, contents=batch)
            out.extend(list(e.values) for e in resp.embeddings)
            self.counters["calls"] += 1
            self.counters["texts"] += len(batch)
        return out


def retrieval_prompt(memories: list[str], task: str) -> str:
    """The ONE prompt template every retrieval-style adapter uses: header,
    the retrieved items in the order the adapter hands them over, then the
    task. No items -> the bare task."""
    if not memories:
        return task
    context = "\n\n".join(memories)
    return ("Retrieved workspace history (top matches for this task):\n\n"
            f"{context}\n\n{task}")


def _cosine(a: list[float], b: list[float]) -> float:
    na = math.sqrt(sum(x * x for x in a)) or 1.0
    nb = math.sqrt(sum(x * x for x in b)) or 1.0
    return sum(x * y for x, y in zip(a, b, strict=True)) / (na * nb)


@dataclass
class EmbeddingRetriever:
    """Cosine ranking over `embed(texts)`; the callable is the pinned model.
    Chunk vectors are cached by chunk text so each event is embedded once;
    the query is embedded per call. `embed_calls` counts embed round-trips."""

    embed: Callable[[list[str]], list[list[float]]]
    model_name: str = "UNPINNED"
    embed_calls: int = 0
    _cache: dict = field(default_factory=dict)      # chunk text -> vector

    def _vectors(self, docs: list[str]) -> list[list[float]]:
        missing = list(dict.fromkeys(d for d in docs if d not in self._cache))
        if missing:
            self._cache.update(zip(missing, self.embed(missing), strict=True))
            self.embed_calls += 1
        return [self._cache[d] for d in docs]

    def rank(self, query: str, docs: list[str]) -> list[int]:
        if not docs:
            return []
        ds = self._vectors(docs)
        q = self.embed([query])[0]
        self.embed_calls += 1
        return [i for _, i in sorted(((-_cosine(q, d), i) for i, d in enumerate(ds)))]


@dataclass
class NaiveRAGAdapter:
    """Chunk = one witnessed event; the top-k retrieved chunks are handed to
    `retrieval_prompt` in chronological order (oldest first)."""

    worker: WorkerModel
    retriever: Retriever = field(default_factory=LexicalRetriever)
    k: int = 8
    shared: bool = True
    counters: dict = field(default_factory=lambda: {"calls": 0, "context_chars": 0,
                                                    "last_context_chars": 0,
                                                    "stored_events": 0, "retrieved": 0})
    _shared_store: dict = field(default_factory=dict)
    _access: dict = field(default_factory=dict)
    _silo_store: dict = field(default_factory=dict)

    def ingest(self, principal: str, event: dict) -> None:
        FullTranscriptAdapter.ingest(self, principal, event)

    def _transcript(self, principal: str) -> list[dict]:
        return FullTranscriptAdapter._transcript(self, principal)

    def run_task(self, principal: str, task: str) -> str:
        events = self._transcript(principal)
        docs = [_render_event(e) for e in events]
        order = self.retriever.rank(task, docs)[: self.k]
        picked = sorted(order)                       # chronological presentation
        memories = [docs[i] for i in picked]
        context = "\n\n".join(memories)
        prompt = retrieval_prompt(memories, task)
        self.counters["calls"] += 1
        self.counters["retrieved"] += len(picked)
        self.counters["embed_calls"] = getattr(self.retriever, "embed_calls", 0)
        self.counters["last_context_chars"] = len(context)
        self.counters["context_chars"] += len(context)
        return self.worker.complete(prompt)
