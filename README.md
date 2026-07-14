# memory-bench

A benchmark for evaluating memory systems as the substrate for continual learning in
**organizations of agents** — where every person has agents working under them, and the
memory layer must hold personal, team, and org-level knowledge with the right scope,
authority, and freshness.

## Thesis

Continual learning for LLM agents is (largely) a harness problem, not a weights problem.
Declarative and episodic knowledge — preferences, decisions, working rules, outcomes,
commitments — can be learned, updated, superseded, and rolled back by a memory harness.
No existing benchmark measures whether a memory system does this correctly across the
tiers of a real organization. This one does.

## What it measures

Six-to-eight metric profile per system (never a single aggregate score):

| Metric | Question it answers |
|---|---|
| Scope-resolution accuracy | When personal/team/org facts conflict, does the contextually correct tier win? |
| Propagation latency | How many sessions until a decision made in one principal's context changes another's behavior? |
| Proactive application | Does a working rule stated once fire later, unprompted? |
| Staleness rate | Do superseded facts stop driving behavior (while remaining retrievable as history)? |
| Rollback fidelity | After a correction, does the wrong behavior disappear everywhere it spread? |
| Leakage rate | Do private/need-to-know facts stay inside their visibility boundary? |
| Conflict-surfacing | Are unresolved contradictions flagged rather than silently resolved? |
| Experience utilization | Do recorded outcomes change future recommendations? |

## How it works

1. A **generator** produces a synthetic organization from a seed: personas, teams,
   policies, and a multi-week event timeline (meetings, DMs, docs, PRs).
2. Every fact in the timeline is tracked in a hidden **ground-truth ledger** with six
   coordinates: type, tier, visibility, authority, temporality, explicitness.
3. The system under test ingests the event stream per-principal, however it wants
   (files, vectors, graphs, fine-tuning). The benchmark never inspects internals.
4. **Behavioral probes** (work tasks, not QA) are injected at intervals and scored
   against the ledger with machine-checkable assertions, counterfactual twins, and
   floor/ceiling normalization.

## Repository layout

- `docs/architecture.md` — full benchmark design: dimensional model, scenario
  archetypes, methodology, positioning vs. prior work
- `docs/specs/ledger-schema.md` — ground-truth fact ledger (contract #1)
- `docs/specs/event-stream.md` — event stream format (contract #2)
- `docs/specs/probe-spec.md` — probe + assertion + counterfactual format (contract #3)
- `docs/dataset-plan.md` — phased plan for building the v1 evaluation dataset

## Status

Design phase. Specs frozen → generator → v1 dataset (see `docs/dataset-plan.md`).
