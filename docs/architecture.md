# memory-bench: architecture and design

Status: design frozen (2026-07-14). Contracts live in `docs/specs/`.
**v1 measures a subset of this design**: archetypes A1/A2/A4/A7 with pair
credit only (v1 pilot FREEZE, 2026-08-15, `docs/dataset-plan.md`); everything
else here is specified-but-deferred (`docs/deferred.md`) and v1 claims none of it.

## 1. Problem statement

Agents working inside organizations need the right bits of information at the right
scope at the right time: the user's personal preferences, the team's conventions, the
org's decisions and policies. Existing memory benchmarks are single-principal and
recall-oriented; none measure whether a memory system correctly handles **tiered scope,
authority, propagation, supersession, and rollback**. Those are the dynamics that
constitute continual learning when it is implemented in a harness rather than in
weight updates.

memory-bench evaluates a memory system (the "SUT", or system under test) by embedding it
in a simulated organization and observing agent *behavior*, never memory internals.

> Addendum 2026-07-25: organizations are getting smaller while agents per person
> multiply, and each person picks a specialized harness (coding agent, creative
> tool, generalist assistant) precisely for its specialization. Organizational
> coherence therefore cannot live in the models, because the weights are plural
> and vendor-owned. It lives in the memory layer every harness shares. Full argument:
> `vision.md` §1.

## 2. Positioning vs. prior work (validated 2026-07-14)

| Benchmark | What it covers | What it lacks that we cover |
|---|---|---|
| LoCoMo / LongMemEval(+V2) | Multi-session recall, temporal QA | Behavioral probes, tiers, dynamics |
| MemoryArena (2602.16313) | Closed-loop single-principal agentic tasks | Multi-principal, org tiers, typed semantics |
| GateMem (2606.18829) | Multi-principal governance: utility, access control, deletion | Tier precedence, propagation, authority weighting, supersession, outcome learning, counterfactual methodology |
| StreamMemBench | Streaming lifelog, feedback consolidation | Single-principal, no org structure |
| HorizonBench | Evolving personal preferences | Single tier only |

Defensible claim: **first benchmark of tiered, typed, longitudinal memory dynamics in a
simulated organization**, with governance measured jointly against propagation (the two
are adversarial, and that tension is a design feature). Access-control-alone is
GateMem's territory; we cite it and go wider.

> Addendum 2026-07-25: the benchmark operationalizes the "company as mini AGI"
> frame (`vision.md` §2). Pooled-context implementations of the org world model
> are literally the long-context and naive-RAG baselines; the claim under test
> is that collective intelligence requires *scoped* memory, not pooled memory.

## 3. Dimensional model

Every ground-truth fact has coordinates on six axes (full schema:
`specs/ledger-schema.md`):

1. **Type**: preference, decision, working_rule, reference, outcome, procedure,
   commitment, relationship. Each type has distinct update semantics and distinct
   "correct use."
2. **Tier**: personal, team, project (cross-team), org, external (client/vendor).
3. **Visibility**: private, need_to_know, team_confidential, org_public.
4. **Authority**: author role × capacity (formal_decision, directive, opinion,
   speculation). An intern's musing ≠ a CTO's ruling.
5. **Temporality**: valid_from, valid_until, superseded_by, decay class.
6. **Explicitness**: stated, implied, distributed (across multiple events). Primary
   difficulty knob.

The ledger induces a computable **expected belief state** `B(principal, t)`: the set of
facts that are visible to, valid for, and applicable by that principal's agent at time
t. All scoring derives from `B`.

## 4. Work-type coverage

The generator and probes span seven organizational work modalities. v1 covers the
first four; the taxonomy exists from day one so coverage gaps are explicit:

1. Communication (email, chat, meetings): the primary ingestion channel *(v1)*
2. Document work (proposals, specs, reports) *(v1)*
3. Engineering (PR review, incidents, architecture decisions) *(v1)*
4. Planning (sprints, OKRs, roadmaps) *(v1)*
5. People work (onboarding, 1:1s, role changes) *(v2)*
6. Customer-facing (sales, support, contracts; external tier) *(v2)*
7. Governance (budget, compliance; hard precedence) *(v2)*

## 5. Scenario archetypes

Reusable templates the generator instantiates many times per org at varying
difficulty. Each defines an event pattern, the ledger truth it creates, its probe, and
the metric it feeds. Orthogonally to the groups below, each archetype feeds exactly
one rung of the capability ladder (`vision.md` §3; added 2026-07-25).

**Propagation & application**
- A1 **Decision ripple**: decision made in a meeting principal P didn't attend; probe
  P's agent N sessions later. → propagation latency, application accuracy. *(v1)*
- A2 **Silent rule**: working rule stated once; probe 30+ events later, no reminder.
  → proactive application. *(v1)*
- A3 **Commitment resurfacing**: promise with deadline; must surface at the right
  time unprompted. → prospective recall. *(v2)*

**Conflict & precedence**
- A4 **Tier collision**: personal vs team vs org facts conflict; context determines
  the winner. → scope-resolution accuracy. *(v1)*
- A5 **Unresolved contradiction**: equal-authority contradictory statements; correct
  behavior is flagging, not picking. → conflict-surfacing rate. *(v2)*
- A6 **Authority gradient**: same claim at different authority/capacity; formal
  decision must beat louder opinion. → authority-weighted accuracy. *(v2)*

**Time & change**
- A7 **Supersession chain**: fact updated 2–3 times; probes at each epoch plus a
  historical probe where the *old* fact is correct. → staleness + history retention.
  *(v1)*
- A8 **Correction & rollback**: wrong fact spreads to several principals, then one
  correction; probe everywhere it spread. → rollback fidelity. *(v2)*
- A9 **Departure / role change**: formal decisions persist, personal authority
  decays, private tier seals. → decay correctness. *(v2)*

**Boundaries & growth**
- A10 **Need-to-know leak trap**: adversarial and *innocent-adjacent* probes against
  confidential facts. → leakage rate. *(v2; overlaps GateMem, but our novelty is jointly
  scoring it against propagation)*
- A11 **Onboarding bootstrap**: new principal joins mid-timeline with an empty agent.
  → bootstrap latency. *(v2)*
- A12 **Outcome learning**: strategy tried, outcome recorded, similar situation
  recurs; recommendations must reflect the result. → experience utilization. *(v2)*

## 6. Scientific methodology (never cut from any version)

1. **Floor/ceiling normalization.** Every probe runs in three conditions: SUT,
   no-memory floor, ledger-oracle ceiling (correct facts injected into context). The
   memory score is the normalized position between floor and ceiling. Probes the
   oracle fails measure reasoning, not memory → flagged and excluded.
2. **Counterfactual paired probes.** Every probe has a twin generated from an
   alternate ledger (decision inverted, preference flipped). Credit only when behavior
   differs correctly across the pair. Kills parametric-knowledge contamination and
   generic-good-behavior passes.
3. **Programmatic scoring first.** Assertions derived from the ledger: fact_applied,
   fact_absent (leakage/staleness), constraint_followed, conflict_flagged. LLM judges
   only for graded qualities, rubric validated against human labels (report Cohen's κ),
   judge model ≠ any model under test.
4. **Contamination control by construction.** Seeded generation; public frozen orgs
   for comparability + held-out regenerated orgs for the leaderboard; unique canary
   strings embedded to detect future training-data leakage; salience linting so ledger
   facts are not phrased more prominently than distractors; near-miss distractors
   (wrong tier / expired / lower authority) at a fixed ratio.
5. **Variance as first-class.** Every number = mean over ≥5 org seeds with CIs.
   Output is a metric radar profile, never a single aggregate (propagation and leakage
   are adversarial; a scalar hides the tradeoff). The radar is presented grouped by
   capability-ladder rung (`vision.md` §3; 2026-07-25); the no-aggregate rule stands.
6. **Fixed-model main track.** The underlying LLM is held constant across SUTs so the
   memory harness is the only variable. A secondary grid track varies the consumer
   model to test portability: memory-system rankings should be invariant to the
   model/harness consuming the memory (repurposed 2026-07-25; previously framed as
   memory-compensating-for-model-quality). Probe validity is task-model-relative:
   Phase 3 measured ceiling-gate survival of 17/54 (gpt-5.4-mini) vs 37/54
   (gpt-5.4) under the identical strict rule, so each added consumer model
   requires its own ceiling/floor screening pass.
7. **Long-context as an honest baseline.** "Stuff the full transcript in context" is a
   real competitor. Timelines are sized so the full transcript is impractical or
   costly, and all results report token cost alongside accuracy.

## 7. Difficulty ladder

Four independent knobs: org scale, distractor density, explicitness
(stated → implied → distributed), hop count (single fact → cross-tier composition).

- **L1**: 1 team, 2 weeks, stated facts, 1-hop
- **L2**: 2 teams, 4 weeks, stated + implied, 1–2 hop
- **L3**: 2–3 teams, 8 weeks, implied + distributed, cross-tier composition
- **L4**: multi-team org, a quarter, distributed facts, adversarial probes

Published results always break out by level: *where* a system breaks is the finding.

## 8. v1 scope

One generated org shape (2 teams, 8 personas, 4-week timeline), archetypes A1, A2,
A4, A7, difficulty L1–L2, full methodology from §6, 5 seeds. Work modalities 1–4.
Every later archetype is content, not new machinery.

## 9. System components

```
generator/           seed → org config → fact plan (ledger) → event realization
  org-designer       personas, teams, roles, calendar, comms graph
  fact-planner       instantiates archetypes into ledger facts + schedule
  event-realizer     LLM-renders naturalistic events embedding facts + distractors
  linter             salience/tell checks, ledger-event consistency validation
probes/              probe construction + counterfactual twin generation
runner/              per-principal event feed → SUT adapter interface → probe injection
scoring/             assertion engine, judge harness, floor/ceiling normalization,
                     per-archetype metric aggregation, CI computation
adapters/            SUT interface implementations (no-memory, full-context, naive
                     RAG, market systems per the Phase 5 selection criteria,
                     typed-memory reference implementation)
datasets/            frozen released orgs (public) + holdout seeds (private)
```

The SUT adapter interface is deliberately minimal: `ingest(principal, event)` and
`run_task(principal, task) -> output`. Nothing else is observed.

> *Implementation map (2026-08-15):* `membench.runner` (feed + injection),
> `membench.adapters` (no-memory, full-transcript ± silo, grep-agent #8),
> `membench.typed_memory` (reference #6, spec `docs/specs/typed-memory-reference.md`),
> `membench.workers` (pinned codex worker), `membench.pilot` (CLI: adapter ×
> org → `<probe>:sut` rows), `scripts/score_sut.py` (blinded judging via
> `screen_probes`, pair credit against the screening anchors, radar by
> rung/metric with cluster-robust SEs). RAG adapters await the embedding pin.
