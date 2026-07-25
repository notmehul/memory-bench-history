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

As organizations get smaller and each person's agents live in different specialized
harnesses, the memory layer is the only substrate organizational coherence can live in.
memory-bench measures which memory substrate turns a company of agents into a
collective intelligence — the "mini AGI" claim, operationalized in `docs/vision.md`.

## What it measures

Six-to-eight metric profile per system, grouped by capability rung
(`docs/vision.md`) — never a single aggregate score:

| Rung | Metric | Question it answers |
|---|---|---|
| Alignment | Scope-resolution accuracy | When personal/team/org facts conflict, does the contextually correct tier win? |
| Alignment | Staleness rate | Do superseded facts stop driving behavior (while remaining retrievable as history)? |
| Coordination | Propagation latency | How many sessions until a decision made in one principal's context changes another's behavior? |
| Coordination | Rollback fidelity | After a correction, does the wrong behavior disappear everywhere it spread? |
| Coordination | Leakage rate | Do private/need-to-know facts stay inside their visibility boundary? |
| Coordination | Conflict-surfacing | Are unresolved contradictions flagged rather than silently resolved? |
| Compounding | Proactive application | Does a working rule stated once fire later, unprompted? |
| Compounding | Experience utilization | Do recorded outcomes change future recommendations? |

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

- `docs/status.md` — current state and work queue (start here)
- `docs/vision.md` — positioning: the capability ladder and heterogeneity thesis
- `docs/standards-audit.md` — field-failure audit and pre-release tracker
- `docs/architecture.md` — full benchmark design: dimensional model, scenario
  archetypes, methodology, positioning vs. prior work
- `docs/validation-report.md` — final v1 dataset validation numbers
- `docs/specs/ledger-schema.md` — ground-truth fact ledger (contract #1)
- `docs/specs/event-stream.md` — event stream format (contract #2)
- `docs/specs/probe-spec.md` — probe + assertion + counterfactual format (contract #3)
- `docs/dataset-plan.md` — phased plan for building the v1 evaluation dataset
- `prompts/` — content-generation contracts (event rendering, canonical
  realization) used by whichever LLM renders prose
- `scripts/` — QA tooling: `validation_sweep.py`, `blind_check.py`,
  `length_pin.py`, `author_probes.py`, `screen_probes.py`
- `datasets/dev/org-0000N/` — released org: `org.json` (private ledger),
  `plan.json` (probe plans), `realization-map.json` (template→prose
  provenance), `events.jsonl` (SUT-facing stream), `events.annotated.jsonl`
  (scoring stream), `g1-report.txt`
- `datasets/dev/org-0000N-twin/` — counterfactual twin: `org.json`,
  `events.jsonl`, `events.annotated.jsonl`

## Status

v1 dev dataset complete: 5 seeded orgs + 5 counterfactual twins, all
machine validation green (`docs/validation-report.md`). Phase 3: 810
oracle-validated behavioral probes across the 5 orgs (`probes.jsonl`,
probe-spec v0.3); seed 1 fully screened under the final floor/ceiling
protocol with fully blinded judging — 45/54 clusters survive with 125
valid instances (cluster gate PASS, instance gate an explicit FAIL
carried with its cause; see the G3 note in `docs/dataset-plan.md` for
the measured protocol revisions the screening forced and the blinded
re-judge audit trail). Remaining: screening seeds 2–5 (staged, blocked
on task-model quota), then Phases 4–5 (judge calibration, pilot
baselines).
