"""Baseline #6 — typed-memory reference implementation (PROPOSED spec:
docs/specs/typed-memory-reference.md; extraction prompt:
prompts/typed-memory-extract.md).

A generic instance of the architecture class "typed, tiered, source-backed,
supersession-aware memory": each witnessed event is turned into typed
nodes by the pinned worker under a fixed prompt; nodes carry tier/scope,
provenance and visibility; conflicts are resolved by explicit supersession
(both nodes stay; the old one is linked); at task time the entitled,
current, on-topic nodes are rendered in the same shape as the screening
ceiling's context block so the only difference from the ceiling is what
memory retained. No embeddings, no summaries, no cross-node inference.

Affiliated with no product. Reads nothing but the two-call SUT interface.
"""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass, field
from pathlib import Path

from .adapters import WorkerModel, _render_event

PROMPT_PATH = Path(__file__).resolve().parents[2] / "prompts" / "typed-memory-extract.md"
KINDS = {"rule", "decision", "preference", "schedule", "fact", "commitment"}
TIERS = {"org", "team", "personal", "project"}
RENDER_CAP = 12          # spec D3
PREVIOUSLY_CAP = 5       # spec D2
EXISTING_CAP = 20
_STOP = frozenset([
    "a", "an", "and", "are", "as", "at", "be", "by", "for", "from", "has", "have", "in",
    "is", "it", "its", "of", "on", "or", "that", "the", "their", "there", "this", "to",
    "was", "were", "will", "with", "all", "any", "each", "every", "not", "no", "under",
    "over", "into", "out", "up", "down", "about", "after", "before", "during", "between",
    "within", "without", "you", "your", "write", "draft", "note", "task"])


def _tokens(text: str) -> set[str]:
    return {t for t in re.findall(r"[a-z0-9][a-z0-9-]*", text.lower())
            if t not in _STOP and len(t) > 2}


def load_prompt() -> str:
    text = PROMPT_PATH.read_text()
    return text.split("---", 1)[1].strip() if "---" in text else text


def prompt_hash() -> str:
    return hashlib.sha1(load_prompt().encode()).hexdigest()[:12]


@dataclass
class Node:
    node_id: str
    kind: str
    statement: str
    tier: str
    scope_ref: str | None
    topic: str
    valid_from: str
    sources: list[str]
    visibility: set[str]
    superseded_by: str | None = None
    superseded_at: str | None = None

    def render(self) -> str:
        scope = self.scope_ref or "org-wide"
        return f"- {self.statement} [{self.tier} scope: {scope}]"


def parse_nodes(text: str) -> list[dict] | None:
    """Parse the worker's JSON array; None on malformed output."""
    if not text:
        return None
    m = re.search(r"\[.*\]", text, re.S)
    if not m:
        return None
    try:
        data = json.loads(m.group(0))
    except json.JSONDecodeError:
        return None
    if not isinstance(data, list):
        return None
    out = []
    for d in data:
        if not isinstance(d, dict) or not d.get("statement"):
            continue
        kind = str(d.get("kind", "fact")).lower()
        tier = str(d.get("tier", "org")).lower()
        if kind not in KINDS or tier not in TIERS:
            continue
        out.append({
            "kind": kind, "statement": str(d["statement"]).strip(),
            "tier": tier, "scope_ref": d.get("scope_ref") or None,
            "topic": str(d.get("topic") or "general").lower(),
            "conflicts_with": [str(x) for x in (d.get("conflicts_with") or [])],
        })
    return out


@dataclass
class TypedMemoryAdapter:
    worker: WorkerModel
    shared: bool = True
    supersession: bool = True   # ablation flag (spec §5)
    tiers: bool = True          # ablation flag (spec §5)
    counters: dict = field(default_factory=lambda: {
        "calls": 0, "context_chars": 0, "last_context_chars": 0,
        "extraction_calls": 0, "nodes_stored": 0, "nodes_rendered": 0,
        "skipped_events": 0, "superseded": 0, "stored_events": 0})
    _prompt: str = field(default_factory=load_prompt)
    _nodes: dict = field(default_factory=dict)         # store_key -> {node_id: Node}
    _seen: dict = field(default_factory=dict)          # store_key -> {event_id}
    _seq: int = 0

    # ---------------------------------------------------------- storage keys
    def _store_key(self, principal: str) -> str:
        return "shared" if self.shared else principal

    def _store(self, principal: str) -> dict:
        return self._nodes.setdefault(self._store_key(principal), {})

    # ---------------------------------------------------------------- ingest
    def ingest(self, principal: str, event: dict) -> None:
        key = self._store_key(principal)
        seen = self._seen.setdefault(key, set())
        store = self._store(principal)
        if event["event_id"] in seen:
            # shared store: later witnesses only widen visibility
            for n in store.values():
                if event["event_id"] in n.sources:
                    n.visibility.add(principal)
            return
        seen.add(event["event_id"])
        self.counters["stored_events"] += 1
        rendered = _render_event(event)
        existing = self._existing_for(store, rendered)
        listing = "\n".join(f"{n.node_id}: {n.statement}" for n in existing) or "(none)"
        prompt = self._prompt.replace("{event}", rendered).replace("{existing}", listing)
        self.counters["extraction_calls"] += 1
        raw = self.worker.complete(prompt)
        parsed = parse_nodes(raw)
        if parsed is None:
            self.counters["skipped_events"] += 1
            return
        for d in parsed:
            self._seq += 1
            node = Node(node_id=f"n{self._seq:05d}", kind=d["kind"],
                        statement=d["statement"], tier=d["tier"],
                        scope_ref=d["scope_ref"], topic=d["topic"],
                        valid_from=str(event.get("sim_time") or ""),
                        sources=[event["event_id"]], visibility={principal})
            store[node.node_id] = node
            self.counters["nodes_stored"] += 1
            if self.supersession:
                for old_id in d["conflicts_with"]:
                    old = store.get(old_id)
                    if old is not None and old.superseded_by is None:
                        old.superseded_by = node.node_id
                        old.superseded_at = node.valid_from
                        self.counters["superseded"] += 1

    def _existing_for(self, store: dict, text: str) -> list[Node]:
        toks = _tokens(text)
        scored = []
        for n in store.values():
            if n.superseded_by is not None:
                continue
            ov = len(toks & (_tokens(n.statement) | _tokens(n.topic.replace("-", " "))))
            if ov:
                scored.append((ov, n.node_id, n))
        scored.sort(key=lambda x: (-x[0], x[1]))
        return [n for _, _, n in scored[:EXISTING_CAP]]

    # -------------------------------------------------------------- run_task
    def _select(self, principal: str, task: str) -> tuple[list[Node], list[Node]]:
        store = self._store(principal)
        toks = _tokens(task)
        current, past = [], []
        for n in store.values():
            if principal not in n.visibility:
                continue
            ov = len(toks & (_tokens(n.statement) | _tokens(n.topic.replace("-", " "))))
            if ov == 0:
                continue
            (past if n.superseded_by else current).append((ov, n.valid_from, n.node_id, n))
        current.sort(key=lambda x: (-x[0], x[1], x[2]))
        past.sort(key=lambda x: (-x[0], x[1], x[2]))
        return ([n for *_, n in current[:RENDER_CAP]],
                [n for *_, n in past[:PREVIOUSLY_CAP]])

    def run_task(self, principal: str, task: str) -> str:
        current, past = self._select(principal, task)
        lines = []
        for n in current:
            lines.append(n.render() if self.tiers else
                         f"- {n.statement} [org scope: org-wide]")
        context = ""
        if lines:
            context = ("Authoritative context from the organization's records "
                       "(typed memory; current unless noted):\n" + "\n".join(lines))
        if past:
            context += ("\n\nPreviously (superseded, historical record):\n"
                        + "\n".join(n.render() for n in past))
        prompt = f"{context}\n\n{task}" if context else task
        self.counters["calls"] += 1
        self.counters["nodes_rendered"] += len(current) + len(past)
        self.counters["last_context_chars"] = len(context)
        self.counters["context_chars"] += len(context)
        return self.worker.complete(prompt)
