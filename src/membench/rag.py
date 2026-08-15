"""Baseline #3 — naive RAG over the raw witnessed stream (chunk = event,
top-k by a retriever), and the retriever seam for the pinned embedding
model (standards-audit B.5: ONE pinned, reported embedding model for all
RAG-class baselines; one alternate as ablation — the pin is a PI decision
and adds a dependency, so it is not chosen here).

Ships with `LexicalRetriever` (BM25-style scoring, stdlib only) so the
RAG-class code path is testable and runnable today; `EmbeddingRetriever`
takes any `embed(texts) -> vectors` callable and is wired the moment the
pin lands. Storage follows FullTranscriptAdapter (shared store with access
lists, or per-principal silos).
"""

from __future__ import annotations

import math
import re
from collections import Counter
from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Protocol

from .adapters import FullTranscriptAdapter, WorkerModel, _render_event

_TOKEN = re.compile(r"[a-z0-9][a-z0-9$%'-]*")


def _toks(text: str) -> list[str]:
    return _TOKEN.findall(text.lower())


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
class EmbeddingRetriever:
    """Cosine ranking over `embed(texts)`; the callable is the pinned model."""

    embed: Callable[[list[str]], list[list[float]]]
    model_name: str = "UNPINNED"

    def rank(self, query: str, docs: list[str]) -> list[int]:
        if not docs:
            return []
        vecs = self.embed([query] + docs)
        q, ds = vecs[0], vecs[1:]

        def cos(a, b):
            na = math.sqrt(sum(x * x for x in a)) or 1.0
            nb = math.sqrt(sum(x * x for x in b)) or 1.0
            return sum(x * y for x, y in zip(a, b, strict=True)) / (na * nb)

        return [i for _, i in sorted(((-cos(q, d), i) for i, d in enumerate(ds)))]


@dataclass
class NaiveRAGAdapter:
    """Chunk = one witnessed event; top-k retrieved chunks are prepended to
    the task, oldest first, as 'Retrieved workspace history'."""

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
        context = "\n\n".join(docs[i] for i in picked)
        prompt = task
        if context:
            prompt = ("Retrieved workspace history (top matches, oldest first):\n\n"
                      f"{context}\n\n{task}")
        self.counters["calls"] += 1
        self.counters["retrieved"] += len(picked)
        self.counters["last_context_chars"] = len(context)
        self.counters["context_chars"] += len(context)
        return self.worker.complete(prompt)
