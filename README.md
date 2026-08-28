# memory-bench

A benchmark for memory systems in organizations of agents, where every person
has agents working under them and the memory layer must hold personal, team,
and org-level knowledge with the right scope, authority, and freshness.

## Thesis

Continual learning for LLM agents is largely a harness problem, not a weights
problem. Preferences, decisions, working rules, outcomes, and commitments can
be learned, updated, superseded, and rolled back by a memory system that lives
outside the weights. No existing benchmark measures whether a memory system
does this correctly across the tiers of a real organization. This one does.

Organizations are getting smaller while each person's agents live in different
specialized harnesses. The memory layer is the only place organizational
coherence can live, so the benchmark asks which memory system actually
produces coherent behavior from a company of agents. The full claim structure
is in `docs/vision.md`.

## What it measures

v1, frozen 2026-08-15, scores four probe archetypes. Results are grouped by
capability-ladder rung (`docs/vision.md` §3) and never reduced to a single
aggregate score:

| Rung | Archetype | Question it answers |
|---|---|---|
| 1, retention | A4 (working rules) | Does a rule stated once keep driving behavior later? |
| 1, retention | A7 (commitments/outcomes) | Are recorded commitments and outcomes applied in later tasks? |
| 2, supersession | A1 (staleness) | Do superseded facts stop driving behavior? |
| 3, cross-principal | A2 (scope/conflict) | When facts conflict across tiers, does the right one win? |

Every instance is scored as pair credit: the probe passes only if the base
task passes and its counterfactual-twin sibling passes. Knowledge the system
could have answered from priors earns nothing. The wider dimensional design
(leakage, propagation latency, rollback, conflict surfacing, experience
utilization) is specified in `docs/architecture.md` and deferred to v2
(`docs/deferred.md`). v1 claims none of it.

## How it works

1. A generator produces a synthetic organization from a seed: personas, teams,
   policies, and a multi-week event timeline of meetings, DMs, docs, and PRs.
2. Every fact in the timeline is tracked in a hidden ground-truth ledger with
   six coordinates: type, tier, visibility, authority, temporality,
   explicitness.
3. The system under test ingests the event stream per principal, however it
   wants: files, vectors, graphs, fine-tuning. The benchmark never inspects
   internals.
4. Behavioral probes, which are work tasks rather than quiz questions, are
   injected at intervals and scored against the ledger with machine-checkable
   assertions, counterfactual twins, and floor/ceiling normalization.

## Repository layout

- `docs/status.md`: current state and work queue (start here)
- `docs/vision.md`: positioning, the capability ladder, the heterogeneity
  thesis
- `docs/standards-audit.md`: field-failure audit and pre-release tracker
- `docs/architecture.md`: full benchmark design, dimensional model, scenario
  archetypes, methodology, positioning vs. prior work
- `docs/validation-report.md`: final v1 dataset validation numbers
- `docs/specs/ledger-schema.md`: ground-truth fact ledger (contract #1)
- `docs/specs/event-stream.md`: event stream format (contract #2)
- `docs/specs/probe-spec.md`: probe + assertion + counterfactual format
  (contract #3)
- `prompts/`: content-generation contracts (event rendering, canonical
  realization) used by whichever LLM renders prose
- `docs/dataset-plan.md`: phases + gates; the v1 pilot FREEZE section at the
  bottom governs. Dated history: `docs/decision-log.md`. Cut scope:
  `docs/deferred.md`
- `docs/vendor-survey.md` / `docs/vendor-configs.md`: market-system selection
  (top-4 by GitHub stars, 2026-08-15) and the per-system configs frozen before
  any run
- `paper/`: preprint skeleton + checklist
- `src/membench/sut_*.py`, `adapters.py`, `rag.py`: baseline + market-system
  adapters; `scripts/run_pilot.py` / `score_sut.py` / `figures.py`: the run,
  scoring, and results pipeline
- `scripts/` (rest): dataset construction + screening tooling
  (`screen_probes.py`, `author_probes.py`, `validation_sweep.py`, …), kept as
  the provenance of the frozen dataset
- `datasets/dev/org-0000N/`: released org. `org.json` (private ledger),
  `plan.json` (probe plans), `realization-map.json` (template-to-prose
  provenance), `events.jsonl` (SUT-facing stream), `events.annotated.jsonl`
  (scoring stream), `g1-report.txt`
- `datasets/dev/org-0000N-twin/`: counterfactual twin. `org.json`,
  `events.jsonl`, `events.annotated.jsonl`

## Status

v1 pilot, frozen 2026-08-15 (`docs/dataset-plan.md` FREEZE section). The
evaluation dataset is seeds 1–3: 371 valid paired instances (A1 50, A2 43,
A4 106, A7 172; per-seed 125/131/115; failed gates carried as explicit FAILs,
never repaired) under probe-spec v0.4.3 and judge rubric v2, screened with a
pinned worker (gpt-5.4, effort medium, codex-cli 0.144.5) and fully blinded
judging. Seeds 4–5 are unscreened holdouts. Systems under test: no-memory,
full-transcript, grep-agent, naive-RAG with and without a lexical ablation,
and the top-4 market systems by GitHub stars (Mem0, Cognee, Graphiti,
Supermemory), plus a Mem0 silo ablation. Adapters, the run/scoring/figures
pipeline, and the per-system config freeze are done; the pilot runs are next
(`docs/status.md` for the live queue).
