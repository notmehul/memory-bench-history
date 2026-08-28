# Pre-Pilot Power Analysis

> **Note 2026-08-28 (v1 freeze, dated 2026-08-15):** computed for the original
> 5-seed design. v1 runs seeds 1–3 only (N = 371 paired instances, not 625) and
> the direction rule is **≥ 2/3 seeds**, not ≥ 4/5 (`docs/dataset-plan.md`
> FREEZE; downgrade disclosed). Per-seed formulas below are unchanged; the
> cross-seed power is correspondingly lower and is reported as such.

Generated 2026-08-06 by `scripts/power_analysis.py` from committed
seed-1 evidence. **Prespecified before any pilot run** (standards
audit B.2 / dataset-plan Phase 5 hardening note). Regenerate after
seeds 2-5 screening if survival differs materially from seed 1.

## Inputs and assumptions

- A1. Seed-1 survivors: 45 clusters, 125 valid instances (mean cluster size 2.78); seeds 2-5 assumed to match -> N = 625 paired
  instances across 5 seeds.
- A2. Instance outcomes modeled Bernoulli(p), exchangeable
  intra-cluster correlation rho; cluster-robust variance via the
  design effect DE = 1 + (m_bar - 1) rho (Miller 2024). Clusters
  are independent across seeds; any org-level correlation beyond
  the cluster level would inflate these SEs further.
- A3. Paired comparison bound: Var(D_i) <= 2 p(1-p) — no credit
  taken for positive within-instance covariance, so real MDDs
  should be smaller than reported.
- A4. Judge noise: per-criterion flip rate 0.024 (26/1,092 blinded re-judge), ~2.25 criteria/run ->
  instance-level misclassification ~0.053. Folded into the
  transient variance share (A5), not modeled separately.
- A5. lam = 0.5 of per-instance variance is transient (worker
  run-to-run + judge) and averages down with K resamples;
  the persistent share (system x probe interaction) does not.
  This is a modeling assumption, not a measurement; at lam = 0.3
  the K=3 MDD improvement roughly halves.
- A6. Normal approximation (Bowyer caveat): N and the ~225 independent clusters support CLT at
  the cluster level, but 5 seeds are too few for seed-level
  Gaussian intervals — seed robustness is therefore reported as
  direction stability (>=4/5 seeds), never as a seed-level CI.

## Empirical anchor for rho

- One-way ICC of memoryless floor pass/fail within surviving
  seed-1 clusters: **rho ~= 0.54** (the only
  SUT-like outcome observable pre-pilot). The grid below brackets
  it.

## Single-system precision (p = 0.5, worst case)

| rho | SE of mean | 95% CI half-width |
|---|---|---|
| 0.2 | 0.0233 | ±4.6 pp |
| 0.4 | 0.0262 | ±5.1 pp |
| 0.6 | 0.0288 | ±5.6 pp |

## Minimum detectable difference, paired systems (alpha=.05, power=.80, p=0.5)

| rho \ K | K=1 | K=2 | K=3 |
|---|---|---|---|
| 0.2 | 9.2 pp | 8.0 pp | 7.5 pp |
| 0.4 | 10.4 pp | 9.0 pp | 8.5 pp |
| 0.6 | 11.4 pp | 9.9 pp | 9.3 pp |

Sensitivity at rho=0.4, K=3 across pass rates: p=0.3: 7.8 pp, p=0.5: 8.5 pp, p=0.8: 6.8 pp.

## Implications (prespecified)

1. **Tie rule threshold**: at rho = 0.6 (conservatively
   bracketing the empirical 0.54) and K=3,
   system deltas below ~9.3 pp overall are
   reported as ties. Per-rung metrics use fewer instances, so
   per-rung MDDs are larger — compute per-rung before claiming any
   rung-level separation.
2. **K=3 resamples are worth it** (~10-18% MDD reduction under
   A5) and are already budgeted in the pilot protocol.
3. **Halving the MDD needs ~4x the data (~2500 instances,
   ~20 seeds)** — or more efficiently, more *clusters* per seed:
   adding instances within existing clusters is dampened by the
   design effect, which is why v2 over-generates clusters, not
   just instances.
4. Headline claims must clear the paired MDD *and* direction
   stability across >=4/5 seeds.
