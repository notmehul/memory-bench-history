# Baseline #6 — Typed-Memory Reference Implementation (spec, PROPOSED)

Status: **DEFERRED (v1 freeze 2026-08-15)** — not run in v1; see
`docs/deferred.md`. Prior status: **DRAFT 2026-08-15 — awaiting PI sign-off; frozen (spec + prompts)
before any pilot scoring.** Independence rule: this is a *generic*
architecture-class baseline specified from the benchmark's own contracts,
affiliated with no product, open-sourced with the benchmark. It tests the
class hypothesis "typed, tiered, source-backed, supersession-aware memory
outperforms pooled context" (dataset-plan Phase 5 #6; `docs/vision.md`).

## 1. What it is (one paragraph)

An adapter that ingests each witnessed event into a **typed store** of
memory nodes extracted by the pinned worker under a fixed extraction
prompt, keeps **tier/scope metadata** and **source provenance** per node,
resolves conflicts by **explicit supersession** (never silent overwrite),
and at task time renders the **entitled, current, on-topic** nodes into the
same "Authoritative context" block the screening ceiling uses. It contains
no retrieval model beyond lexical overlap on typed fields — deliberately
the simplest instance of the class.

## 2. Data model

```
Node {
  node_id, kind ∈ {rule, decision, preference, schedule, fact, commitment},
  statement (one canonical sentence, present tense),
  tier ∈ {org, team, personal, project}, scope_ref (team:x / persona:y / null),
  topic (short slug), valid_from (sim_time of source event),
  sources [event_id...], superseded_by (node_id|null), superseded_at,
  visibility {principals allowed}   # derived from event delivery, never inferred
}
```

Rules:
- A node's `visibility` is exactly the set of principals the runner
  delivered its source events to (shared store) — the adapter never widens
  it. `shared=False` (silo ablation) keeps a per-principal store instead.
- **Supersession** is the only mutation: when a new node conflicts with an
  existing one of the same `(kind, tier, scope_ref, topic)` (same attribute
  under the extraction prompt's `conflicts_with` output), the older node
  gets `superseded_by`; both stay. Historical probes read superseded nodes;
  current probes do not.
- No summaries, no embeddings, no cross-node inference.

## 3. Ingest (per witnessed event)

One worker call per event per *store* (shared: once per event; silo: once
per witnessing principal — this asymmetry is the silo cost and is
reported). Fixed prompt (`prompts/typed-memory-extract.md`, frozen):
input = rendered event + the store's current node statements on the
event's topics (≤ 20, lexical match); output = JSON list of new nodes with
`kind, statement, tier, scope_ref, topic, conflicts_with: [node_id]`.
Extraction is **conservative**: only statements the event asserts as
policy/decision/preference/schedule; chatter yields nothing. Malformed
output → retry once → skip event (counted).

## 4. Task-time rendering

For principal p at time t: nodes with p ∈ visibility, not superseded (or
superseded, for tasks whose prompt asks about the past — the adapter does
not know the probe kind; it always includes superseded nodes in a
separate "Previously:" list capped at 5, which is exactly what a real
system exposes), topic-matched to the task by lexical overlap (top 12 by
overlap, ties by recency), rendered as
"Authoritative context (typed memory):\n- [tier/scope] statement" —
mirroring the ceiling's canonical block so the *only* difference from the
ceiling is what memory retained. Counters: nodes stored, nodes rendered,
context chars, extraction calls, skipped events.

## 5. Ablations (planned, cheap: same code, flags)

- `supersession=False`: conflicts append without linking (stale + current
  both current) — isolates the supersession claim.
- `tiers=False`: all nodes rendered as `[org]` — isolates the scope claim.
- `shared=False`: silo (already the #7 configuration).

## 6. What it must not do

Read `org.json`, `probes.jsonl`, or any ledger; know probe timing; use any
model other than the pinned worker; change prompts after freeze.

## 7. Cost

Ingest = one worker call per event (shared) — ~500–700 calls per org, on
top of probe calls; reported in the cost columns (standards audit B.6).

## 8. Open decisions for the PI

- D1: pinned worker for extraction (keeps the "one model" main-track rule)
  vs a cheaper fixed extractor (breaks it) — recommendation: pinned worker.
- D2: include the "Previously:" superseded list by default (recommendation:
  yes — it is what a typed store naturally exposes and it is what makes
  historical probes answerable without probe-kind leakage).
- D3: lexical top-12 rendering cap (recommendation: fixed at 12; report
  sensitivity at 6/24 in an appendix, not headline).
