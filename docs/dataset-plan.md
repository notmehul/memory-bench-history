# v1 Evaluation Dataset — Creation Plan

> **The "v1 pilot FREEZE" section at the bottom (2026-08-15) governs and
> supersedes anything above it that conflicts** (e.g. the 5-seed goal below:
> v1 evaluates seeds 1–3; seeds 4–5 are unscreened holdouts). The phase text
> is the original plan, kept for provenance.

Goal: a released v1 dataset + evaluation harness proving the benchmark concept:
**5 seeded orgs (L1–L2), archetypes A1/A2/A4/A7, full scientific methodology,
pilot results for 5–6 baseline memory systems.**

The plan is gated: each phase ends in a named gate (G0–G5) with objective pass
criteria. A gate failure loops within the phase; it never leaks downstream.

---

## Phase 0 — Freeze contracts *(this week)*

Contracts #1–#3 (`docs/specs/`) reviewed and frozen. Any later change bumps a spec
version and invalidates generated artifacts.

Deliverables: specs at v0.1 with changelog headers; reference implementation of the
belief-state function `B(principal, t)` as a pure function over (ledger, event index),
with unit tests covering every precedence rule and decay class in the ledger spec.

**Gate G0:** `B` reference implementation passes a hand-written test suite of ≥40
cases including every precedence rule (1–4), each decay class, ACL edge cases
(need_to_know, departure sealing), and supersession chains of length 3.

*History: G0 PASSED 2026-07-14 — see `docs/decision-log.md` §2026-07-14 (Gate G0).*

## Phase 1 — Org designer + fact planner *(week 1–2)*

Seeded generation of the org skeleton and the ledger — no prose yet.

1. **Org designer**: seed → personas (roles, authority levels, voice profiles), 2
   teams, 1 cross-team project, comms graph (who talks to whom on which surfaces),
   4-week calendar of recurring surfaces (standups, planning, 1:1s).
2. **Fact planner**: instantiates archetype templates (A1, A2, A4, A7) into concrete
   ledger facts with full six-axis coordinates, schedules their evidence events onto
   the calendar, generates counterfactual variants, and plans distractors (≥2:1 with
   ≥1 near-miss per probed fact).

Per-org content targets (L2): ~15 instances per archetype (60 probed fact clusters),
~150 distractor facts, ~800–1,200 events, stripped transcript ≥500k tokens.

**Gate G1:** For 5 seeds: ledger validates against schema; every non-distractor fact
has ≥1 planned probe and a counterfactual; `B` computes without ambiguity warnings at
every event index; archetype instances interleave (no contiguous blocks — measured by
a dispersion statistic over evidence-event indices).

*History: G1 PASSED 2026-07-14 — see `docs/decision-log.md` §2026-07-14 (Gate G1).*

## Phase 2 — Event realization *(week 2–4)*

LLM-rendered naturalistic events from the fact plan.

1. Renderer prompts per channel type, conditioned on author voice profiles;
   fact renderings assigned per plan (verbatim/paraphrase/implication/fragment).
2. Noise-floor filler generation (≥60% of content, zero probed facts).
3. **Linter suite** (release-blocking):
   - round-trip: an extractor re-derives `evidence_events` from annotations; mismatch fails
   - salience lint: probed-fact spans statistically indistinguishable from distractor
     spans on length / position-in-event / emphasis markers
   - no-verbatim-reuse: a fact's canonical text appears verbatim in ≤1 event
   - visibility consistency: fact visibility vs. surface visibility
   - canary insertion at fixed frequency
4. **Consistency pass**: a checker LLM (not the renderer) reads each event against the
   ledger and flags contradictions the plan didn't intend; flagged events re-render.

**Gate G2:** all linters green on 5 seeds + 1 twin org per seed; a blinded spot-check —
given 20 event excerpts (10 embedding probed facts, 10 distractor-only), a human
reviewer cannot beat 65% accuracy identifying which are probed (salience is truly
flat); one full org read-through by a human confirms narrative coherence.

*History: G2 machine-side complete 2026-07-18 — see `docs/decision-log.md` §2026-07-18 (Gate G2).*

## Phase 3 — Probe construction + validity screening *(week 4–5)*

1. Generate probe records per archetype instance (≥3 probe instances each: varied
   principals/offsets; latency series for A1/A2).
2. Author assertions; prefer `pattern`/`structural` checkers; write `semantic`
   criteria as binary statements.
3. **Validity screening** (no SUTs involved): run every probe in `floor` and
   `ceiling` conditions with the fixed task model.
   - drop/redesign probes failing the gates (ceiling ≥90% pass, floor ≥70% fail)
   - counterfactual screening: ceiling must pass both sides of every twin pair

Expected attrition: plan for 30% probe loss; over-generate accordingly.

**Gate G3:** ≥45 surviving probe clusters per org (≥135 probe instances); per-archetype
n ≥ 30 across the 5-seed suite; every surviving probe discriminative per the
floor/ceiling gates.

*History (all in `docs/decision-log.md`): gate-unit clarification §2026-07-25;
seed 1 screened + protocol history §2026-07-25; seed 2 screened §2026-08-06;
probe-spec v0.4.3 re-score, canon, exploit audit §2026-08-15; seed 3 screened + R6
§2026-08-15. Frozen canon (see FREEZE below): seed 1 46/54, 125 valid instances;
seed 2 46/54, 131; seed 3 40/54, 115 — instance gates carried as FAILs; seeds 4–5
unscreened holdouts.*

## Phase 4 — Human validation + judge calibration *(week 5–6)*

1. **Calibration subset**: 150 (output, criterion) pairs sampled across semantic
   assertions, labeled by 2 human raters; report inter-rater κ; adjudicate
   disagreements.
2. Judge model evaluated against adjudicated labels; per-criterion agreement < 0.7 κ →
   criterion rewritten (once) or probe dropped.
3. Probe-hygiene audit on a 20% sample: task/fact n-gram overlap lint + human check
   that tasks don't telegraph targets.

**Gate G4:** overall judge–human κ ≥ 0.75; no surviving criterion below 0.7; hygiene
audit clean.

*Amendment (standards audit B.1, decoy audit; result 2026-08-15: false-accept 2/41 as measured, 0/39 adjudicated) — see `docs/decision-log.md` §2026-07-25 (Gate G4).*

## Phase 5 — Pilot evaluation + release *(week 6–8)*

Baselines (fixed task model across all — the main-track rule):

1. no-memory (floor, already run)
2. full-transcript long-context (with token cost reported)
3. naive vector RAG over the raw stream (chunked, top-k)
4. summarize-then-RAG (rolling per-principal summaries)
5. market memory systems, selected by the published criteria below — not by
   convenience *(revised 2026-07-25; was "pick 1–2 by adapter effort")*
6. typed-memory reference implementation: a **generic** open-source baseline
   (typed nodes, tier/scope metadata, source-backed updates, explicit
   supersession) specified alongside the benchmark and implemented from that
   spec — testing the architecture *class*, affiliated with no product
   *(revised 2026-07-25; was "Marshmallow-style file-graph harness")*
7. silo ablation *(added 2026-07-25)*: the strongest shared-store baseline among
   3–6 re-run with per-principal isolated stores — identical system, sharing
   disabled. An adapter configuration, not new machinery. v1 measures only the
   propagation benefit of sharing; the governance cost (leakage) arrives with A10
   in v2, so the comparison is one-sided and must be reported as such.
8. filesystem+grep agent *(added 2026-07-25 per `docs/standards-audit.md` B.4)*:
   the worker with plain file read/search tools over its witnessed transcript —
   the trivial-tools floor any memory product must beat (motivated by Letta's
   74%-with-grep result on LoCoMo).

*Pilot protocol hardening 2026-07-25 (statistics, exploit audit, judge validation, confound pinning, cost columns, vendor fairness, agreement testing) — in force; text in `docs/decision-log.md` §2026-07-25 (Phase 5: pilot protocol hardening).*

*Independence & market-coverage protocol and prespecified hypotheses H1–H3 (2026-07-25) — in force; text in `docs/decision-log.md` §2026-07-25 (Phase 5: independence; H1–H3).*

Protocol: 5 seeds × all probes × 3 conditions × counterfactual twins. Report the
metric radar (application accuracy, scope resolution, propagation latency
distribution, staleness rate, proactive application) with 95% CIs, per difficulty
level, plus token cost per system.

**Item analysis** on pilot results: probes where all baselines pass or all
fail are flagged for review (non-discriminative among real systems); headline claims
checked for seed-robustness (direction of every system ranking stable across ≥4/5
seeds). An exploratory cross-principal coherence statistic (behavioral agreement
across instances of a cluster issued via different principals) is computed from
existing per-instance scores; it is confounded with offset variation and reported
as secondary only (`docs/vision.md` §6).

**Gate G5 (release):** pilot produces at least one seed-robust headline finding (the
expected one: systems without tier/type structure fail scope-resolution and
propagation disproportionately vs. recall-style metrics); frozen public release =
3 orgs public + 2 holdout, generator withheld pending v2 decision; results write-up.

*Amendment (standards audit B.9, release requirements) — see `docs/decision-log.md` §2026-07-25 (Gate G5).*

---

## Standing decisions

- **Fixed task model**: chosen once at Phase 3 start, used for validity screening and
  all pilot conditions. Must not be the judge model.
  *Current pin: gpt-5.4, effort medium, codex-cli 0.144.5 (enforced via
  `membench.codex_bin`); screening judge claude-sonnet-5, rubric v2. History —
  chosen §2026-07-19, amended §2026-07-22, harness study + enforcement note
  §2026-07-25, provenance note §2026-07-25 — all in `docs/decision-log.md`.*
- **Twin-org cost control**: twins re-render only delta-affected events (~5–10% of the
  stream); everything else is byte-identical to the base org.
- **What v1 explicitly does NOT claim**: leakage/governance coverage (GateMem's
  territory; ours lands in v2 with A10 jointly scored against propagation), people/
  customer/governance work modalities, L3–L4 difficulty, model-grid track.
- **v2 queue** (unblocked by v1 machinery, pure content): A12, A5, A10, A8, A3,
  A6, A9, A11 (reordered 2026-07-25 per `docs/vision.md` — outcome learning and
  conflict surfacing are the most mini-AGI-critical; A10+A8 complete the
  adversarial sharing pair); modalities 5–7; L3; leaderboard on regenerated
  holdouts. v3 adds heterogeneous consumer profiles, agent-authored artifacts,
  and delegated authority (`docs/vision.md` §6).
  **Industry matrix (added 2026-08-05, Mehul directive):** v2 introduces
  industry as a designed, seed-crossed factor (never confounded with seed):
  2–3 contrast industries selected for the memory dynamics software exercises
  weakly — consulting (engagement-based re-teaming → propagation/A11
  bootstrap; client confidentiality walls + external tier → A10) and a
  regulated-finance org (hard governance, retention/deletion, need-to-know,
  formal authority gradients → A6/A9/A10). Per-industry: new org-designer
  profiles (roles, surfaces, registers), per-register salience re-tuning and
  full lint re-pass, and ≥1 practitioner review of fact plans per industry
  (BetterBench domain-expert criterion). Fact *types* generalize unchanged;
  what varies is surfaces, personas, and registers.

## Risk register

| Risk | Mitigation |
|---|---|
| Rendered events feel synthetic / templated | voice profiles + noise floor + G2 blinded spot-check; if it fails, invest in renderer prompts, not more volume |
| Semantic judges unreliable | prefer pattern/structural; κ gates; binary criteria only |
| Long-context baseline wins everything at L1–L2 | acceptable and publishable (it's a real finding at that scale); L3 sizing exists precisely to map the crossover point |
| Probe attrition > 30% | over-generate; attrition rate itself is reported (silent-cap rule) |
| Generator LLM's own biases make facts guessable | counterfactual pairing structurally cancels this |

---

## v1 pilot FREEZE + reduced design (prespecified 2026-08-15, before any SUT run)

Decided by Mehul with the agent after a scope review; supersedes anything above
that conflicts. Rationale: one month of screening produced a usable dataset and
zero evaluated systems; the deliverable is pilot numbers.

**Frozen.** Dataset = seeds 1–3 exactly as in the repo at this commit (371
valid instances: A1 50, A2 43, A4 106, A7 172), probe-spec v0.4.3, judge
rubric v2. Seed 3's cluster-gate FAIL and all three instance-gate FAILs are
reported as FAILs. Seeds 4–5 are **unscreened holdouts** — no further
screening runs in v1. No further scoring-rule changes, criterion repairs,
adjudications, or re-judging; a probe that looks wrong during the pilot is
flagged in item analysis, never fixed. Worker (gpt-5.4, medium, codex-cli
0.144.5) and judge (claude-sonnet-5, rubric v2) unchanged. Worker billing moves
to an OpenAI API key behind the same pinned binary (disclosed).

**Systems run (fixed worker).** no-memory (floor; cached from screening) ·
full-transcript · grep-agent · naive-RAG
(embedding pin: Gemini `gemini-embedding-001`) · **four market systems by
rule**: from the vendor survey's INCLUDE list, the four dedicated
memory-system repositories with the most GitHub stars on 2026-08-15 →
**Mem0 (63.3k), Cognee (30.0k), Graphiti/Zep (29.9k), Supermemory (28.9k)**;
next: Letta 24.3k, Honcho 6.7k, Memobase 2.8k, LangMem 1.6k. Rulings:
LlamaIndex Memory not ranked (stars belong to the framework, not the memory
module); Zep Cloud represented by Graphiti (its OSS core). Everything else in
the candidate table: "not run in v1 (budget)". Market systems' internal LLM =
Gemini where configurable, vendor default listed alongside; ceiling condition
cached from screening. **Silo ablation (H2)** runs on Mem0 (per-principal stores vs one org-wide store), not on full-transcript — for a raw transcript the two configurations yield identical context text (`adapters.py`), so the ablation is only meaningful on a derived-memory system. Corrected 2026-08-15 before any run.

**Run budget.** 371 × 2 sides × 8 systems ≈ 5,900 SUT runs at K=1, plus one
variance subset (seed 1 × full-transcript + one market system × K=3, ≈500) for
the tie rule. Nothing else.

**Cut from v1 (deferred, no work).** Typed-memory reference implementation
(#6), summarize-RAG, full-transcript silo, K=3 elsewhere, G2 human read-through, industry matrix,
L3, grid track, further vendor-survey verification, seeds 4–5.

**Analysis.** As prespecified above (rung radar, cluster-robust SEs, paired
per-item, tie rule, cost columns, H1–H3) with two disclosed downgrades:
(1) rank-direction robustness threshold ≥2/3 seeds (was 4/5); (2) G4 =
single author-rater agreement on the existing 150-pair packet (rater is
Mehul, who has seen seeds 1–3 content — disclosed) + the 20-decoy audit;
criteria below 0.7 are dropped, never rewritten.

**Order.** Adapters + `run_pilot.py` + doc consolidation (no quota) → seed-1
smoke, all systems → item analysis → seeds 2–3 → blind judge → rater packet
+ stats → draft. Vendors receive raw results + harness with a 7-day
right-of-reply window before submission.

**Violations (any of these breaks the freeze):** a new gate, rule, spec
section, audit, or seed screening; a run outside the listed systems; any
harness other than pinned codex on a protocol path; any criterion edit.
