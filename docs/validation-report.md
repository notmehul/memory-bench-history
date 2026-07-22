# v1 Dataset Validation Report

Final validation of the five dev orgs and their counterfactual twins,
2026-07-18. Every check below runs from the committed artifacts via
`scripts/validation_sweep.py` and `scripts/blind_check.py`.

## Clean-room sweep

Per stream: structure equals deterministic regeneration (canonicals aside),
realization check, gate G1 (schema + oracle cross-checks + ambiguity scan +
interleaving), and the release-blocking stream lint (marker round-trip,
visibility, salience permutation tests, noise floor, canaries).

```
seed 1: struct=OK realization=OK G1=OK stream=OK (salience p: 0.85/0.502/1.0, noise 0.85)
  twin 1: stream=OK coords=OK (salience p: 0.136/0.303/1.0)
seed 2: struct=OK realization=OK G1=OK stream=OK (salience p: 0.124/0.344/1.0, noise 0.87)
  twin 2: stream=OK coords=OK (salience p: 0.414/0.977/1.0)
seed 3: struct=OK realization=OK G1=OK stream=OK (salience p: 0.254/0.746/1.0, noise 0.87)
  twin 3: stream=OK coords=OK (salience p: 0.459/0.438/1.0)
seed 4: struct=OK realization=OK G1=OK stream=OK (salience p: 0.165/0.533/1.0, noise 0.87)
  twin 4: stream=OK coords=OK (salience p: 0.301/0.06/1.0)
seed 5: struct=OK realization=OK G1=OK stream=OK (salience p: 0.054/0.78/1.0, noise 0.86)
  twin 5: stream=OK coords=OK (salience p: 0.134/0.084/1.0)

SWEEP: ALL GREEN   (unit tests: 95 passed; ruff: clean)
```

## Blinded rater protocol (machine)

Prespecified protocol: one adversarial rater per seed (GPT-5.4 via codex,
isolated working directory containing ONLY the 20-excerpt sample — earlier
runs that gave raters repository access were discarded after one rater
scored 20/20 by reading the ledger). Samples: 10 probed + 10 distractor
spans, no same-topic siblings. Aggregate binomial test against chance at
α = 0.05.

| Seed | Rater accuracy |
|---|---|
| 1 | 8/20 (40%) |
| 2 | 12/20 (60%) |
| 3 | 14/20 (70%) |
| 4 | 12/20 (60%) |
| 5 | 12/20 (60%) |

**Aggregate: 58/100 = 58%, binomial p = 0.067 → not significantly above
chance. Protocol PASSES.**

### Known limitation: seed 3

Seed 3 scored 14/20 on four independent samples (including after two
targeted content revisions), a repeatable single-seed signal
(42/60 across the first three, p ≈ 0.001). An explain-the-leak analysis
attributed it to subject-shape and topic-domain differences (probed facts
read as binding policies over governed classes; some distractors read as
artifact/process trivia). Two content passes (numeric parity, binding-policy
reshaping of all 59 distractor rules) did not remove it. Seed 3 ships
with this documented residual; users running salience-sensitive analyses
should prefer seeds 1/2/4/5 or regenerate seed 3 under a future generator
version. The realization rules that close the tells found so far are
codified in `prompts/canonical-realization.md`.

## Phase 3: probe construction + validity screening (2026-07-22)

**Construction (all 5 orgs): COMPLETE.** 54 clusters × 3 instances × 5 orgs
= 810 probe instances in `datasets/dev/org-0000N/probes.jsonl`. Every
instance is oracle-revalidated (targets ∈ B — or B_hist for historical —
must_not_use ∈ B_hist, A4 winners re-derived via `resolve_precedence`).
Task text and assertions were LLM-authored under
`prompts/probe-authoring.md` and accepted only after mechanical
validation: answer-token hygiene lint, 4-gram overlap lint, and pattern
cross-validation (each pattern must match every numeral/word surface
variant of its own side and no variant of the other side, and no sibling
fact). The authoring loop converged in ≤3 attempts per org.

**Screening (seed 1): 486/486 task-model runs complete; 17/54 clusters
survive** the prespecified strict gates (3/3 ceiling ∧ 3/3 twin-ceiling ∧
pair-level floor; `datasets/dev/org-00001/g3-report.json`, raw evidence in
`datasets/dev/screening/org-00001/`). Survivors by kind: staleness 9/18,
application 4/12, scope_resolution 2/18, historical 2/6; mean per-side
floor guessability 0.23 (cancelled by pair crediting). Failure forensics:
ceiling failures dominate (25 clusters) and persist under a
primary-assertions-only gate (18/54), locating the problem in the fixed
task model — gpt-5.4-mini does not reliably restate compound facts even
when they are handed to it verbatim. Two protocol findings from the pilot
are now codified: pattern checkers are restricted to invariant surface
forms (numbers, identifiers, day names — everything else is judged
semantically), and the floor gate is evaluated at pair level (probe-spec
v0.2).

**G3 verdict: NOT PASSED at the original task-model choice; escalation to
gpt-5.4 prespecified** (dataset-plan standing decisions). Screening for
seeds 2–5 and the seed-1 re-screen are staged and blocked only on codex
quota (resets 2026-07-29). Judging provenance for seed 1: 339/399
semantic verdicts by gpt-5.4, 60 by a documented Claude fallback judge
after the quota cutoff (tagged in `judgements.jsonl`).

## Consistency and coherence

- LLM consistency pass (seed 1, full stream vs. full ledger): zero
  contradictions; filler inert. (Seeds 2–5 pending equivalent passes.)
- The spec's HUMAN blinded spot-check and per-org read-throughs remain
  open items for formal G2 closure; all machine-side checks are complete.
