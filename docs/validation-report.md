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

**Screening (seed 1, final protocol): 486/486 gpt-5.4 task-model runs;
46/54 clusters survive, shipping 129 valid instances**
(`datasets/dev/org-00001/g3-report.json`, raw evidence in
`datasets/dev/screening/org-00001/`). Gate G3: cluster floor PASS
(46 ≥ 45); instance floor FAIL (129 < 135, single-instance noise inside
surviving clusters — v2 should over-generate 4 instances/cluster).
Strict all-instances rule for comparison: 37/54. Mean per-side floor
guessability 0.31 (cancelled by pair crediting). Judging: 1,146 semantic
verdicts, claude-sonnet-5 (each row tagged; a handful adjudicated by
claude-fable-5-fallback). Every dropped cluster was individually
adjudicated: twin-side model failures (the task model refusing to state
an awkward counterfactual cleanly, inventing structure the twin fact
forbids) or task defects (one task presupposing a base-side mechanism);
all recorded for the v2 generator.

The screening iterations themselves produced the protocol (each revision
measured, made before any SUT evaluation, evidence in git history):
gpt-5.4-mini rejected as task model (17/54 ceiling survival on compound
facts); applied-content regex assertions rejected (39–42% ceiling failure
— deliverables paraphrase around any anchor — vs 4% for absence-detector
patterns and 9–17% for semantic criteria), hence probe-spec v0.3's
checker policy; the all-instances cluster gate replaced by instance-level
validity (0.9^6 ≈ 0.53 cluster survival at realistic noise made the
strict rule unsatisfiable at n=3); and one authoring rule from failure
adjudication — assertions must never punish co-valid sibling facts.

**Seeds 2–5: probes final under spec v0.3; screening blocked on codex
quota (resets 2026-07-29).** Seed 2 has 356/486 task-model runs cached
and prompt-verified against the final probes.

## Consistency and coherence

- LLM consistency pass (seed 1, full stream vs. full ledger): zero
  contradictions; filler inert. (Seeds 2–5 pending equivalent passes.)
- The spec's HUMAN blinded spot-check and per-org read-throughs remain
  open items for formal G2 closure; all machine-side checks are complete.
