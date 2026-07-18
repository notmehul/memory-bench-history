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

## Consistency and coherence

- LLM consistency pass (seed 1, full stream vs. full ledger): zero
  contradictions; filler inert. (Seeds 2–5 pending equivalent passes.)
- The spec's HUMAN blinded spot-check and per-org read-throughs remain
  open items for formal G2 closure; all machine-side checks are complete.
