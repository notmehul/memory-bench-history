"""Pre-pilot power analysis (standards-audit B.2; BLOCKING gate C3).

Sizes the pilot under the prespecified statistics protocol (dataset-plan
Phase 5 hardening note): cluster-robust variance with probe instances
clustered by fact cluster, paired per-item system comparisons, K worker
resamples per probe. Stdlib only; normal approximation throughout (see the
Bowyer small-n caveat in the generated report).

Model, stated fully in the generated report:
  - Per-instance SUT outcome ~ Bernoulli(p); exchangeable intra-cluster
    correlation rho; design effect DE = 1 + (m_bar - 1) * rho.
  - Paired difference D_i between two systems on the same instance, with
    the conservative no-pairing-covariance bound Var(D_i) <= 2 p(1-p).
  - A fraction lam of per-instance variance is transient (worker run +
    judge noise) and averages down with K resamples:
    v_K = v * ((1 - lam) + lam / K).
  - MDD = (z_.975 + z_.80) * SE(D_bar), two-sided alpha=.05, power=.80.

Empirical anchor: the intra-cluster correlation of memoryless floor
outcomes in the committed seed-1 report (the only SUT-like outcome
observed pre-pilot) is computed as a one-way ICC and reported next to the
rho grid.

Usage:
  python scripts/power_analysis.py [--report docs/power-analysis.md]
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from statistics import NormalDist

Z_SUM = NormalDist().inv_cdf(0.975) + NormalDist().inv_cdf(0.80)

# Pilot size assumption: seeds 2-5 survive screening like seed 1.
SEEDS = 5
JUDGE_FLIPS = (26, 1092)  # blinded re-judge disagreements / criteria

RHO_GRID = (0.2, 0.4, 0.6)
K_GRID = (1, 2, 3)
P_GRID = (0.3, 0.5, 0.8)
LAM = 0.5  # transient share of per-instance variance (assumption A5)


def design_effect(m_bar: float, rho: float) -> float:
    return 1.0 + (m_bar - 1.0) * rho


def se_single(p: float, n: int, m_bar: float, rho: float) -> float:
    """Cluster-robust SE of one system's mean pass rate over n instances."""
    return (p * (1 - p) * design_effect(m_bar, rho) / n) ** 0.5


def mdd_paired(
    p: float, n: int, m_bar: float, rho: float, k: int, lam: float = LAM,
) -> float:
    """Minimum detectable paired difference at alpha=.05, power=.80.

    Conservative bound: Var(D_i) <= 2 p(1-p) (no credit for positive
    within-instance covariance between systems; pairing on shared items
    can only shrink this).
    """
    var_d = 2.0 * p * (1 - p) * ((1 - lam) + lam / k)
    return Z_SUM * (var_d * design_effect(m_bar, rho) / n) ** 0.5


def icc_oneway(groups: list[list[float]]) -> float:
    """One-way ANOVA ICC(1); 0.0 when between/within variance degenerate."""
    groups = [g for g in groups if len(g) >= 2]
    k = len(groups)
    n = sum(len(g) for g in groups)
    if k < 2 or n <= k:
        return 0.0
    grand = sum(sum(g) for g in groups) / n
    msb = sum(len(g) * (sum(g) / len(g) - grand) ** 2 for g in groups) / (k - 1)
    msw = sum(sum((y - sum(g) / len(g)) ** 2 for y in g) for g in groups) / (n - k)
    m0 = (n - sum(len(g) ** 2 for g in groups) / n) / (k - 1)
    denom = msb + (m0 - 1) * msw
    if denom <= 0:
        return 0.0
    return max(0.0, (msb - msw) / denom)


def load_seed1(report_path: Path) -> dict:
    rep = json.loads(report_path.read_text())
    clusters = {c: r for c, r in rep["clusters"].items() if r["survive"]}
    floor_groups, n_valid = [], 0
    for r in clusters.values():
        g = []
        for inst in r["instances"].values():
            if inst["valid"]:
                n_valid += 1
                g.append(1.0 if inst["floor"] >= 0.999 else 0.0)
        if g:
            floor_groups.append(g)
    m_bar = n_valid / len(clusters)
    return {
        "n_clusters": len(clusters),
        "n_valid": n_valid,
        "m_bar": m_bar,
        "rho_floor": icc_oneway(floor_groups),
    }


def build_report(seed1: dict) -> str:
    n = seed1["n_valid"] * SEEDS
    m_bar = seed1["m_bar"]
    q_crit = JUDGE_FLIPS[0] / JUDGE_FLIPS[1]
    crit_per_run = 1092 / 486
    q_inst = 1 - (1 - q_crit) ** crit_per_run

    lines = [
        "# Pre-Pilot Power Analysis",
        "",
        "Generated 2026-08-06 by `scripts/power_analysis.py` from committed",
        "seed-1 evidence. **Prespecified before any pilot run** (standards",
        "audit B.2 / dataset-plan Phase 5 hardening note). Regenerate after",
        "seeds 2-5 screening if survival differs materially from seed 1.",
        "",
        "## Inputs and assumptions",
        "",
        f"- A1. Seed-1 survivors: {seed1['n_clusters']} clusters, "
        f"{seed1['n_valid']} valid instances (mean cluster size "
        f"{m_bar:.2f}); seeds 2-5 assumed to match -> N = {n} paired",
        "  instances across 5 seeds.",
        "- A2. Instance outcomes modeled Bernoulli(p), exchangeable",
        "  intra-cluster correlation rho; cluster-robust variance via the",
        "  design effect DE = 1 + (m_bar - 1) rho (Miller 2024). Clusters",
        "  are independent across seeds; any org-level correlation beyond",
        "  the cluster level would inflate these SEs further.",
        "- A3. Paired comparison bound: Var(D_i) <= 2 p(1-p) — no credit",
        "  taken for positive within-instance covariance, so real MDDs",
        "  should be smaller than reported.",
        f"- A4. Judge noise: per-criterion flip rate {q_crit:.3f} "
        f"(26/1,092 blinded re-judge), ~{crit_per_run:.2f} criteria/run ->",
        f"  instance-level misclassification ~{q_inst:.3f}. Folded into the",
        "  transient variance share (A5), not modeled separately.",
        f"- A5. lam = {LAM} of per-instance variance is transient (worker",
        "  run-to-run + judge) and averages down with K resamples;",
        "  the persistent share (system x probe interaction) does not.",
        "  This is a modeling assumption, not a measurement; at lam = 0.3",
        "  the K=3 MDD improvement roughly halves.",
        "- A6. Normal approximation (Bowyer caveat): N and the ~"
        f"{seed1['n_clusters'] * SEEDS} independent clusters support CLT at",
        "  the cluster level, but 5 seeds are too few for seed-level",
        "  Gaussian intervals — seed robustness is therefore reported as",
        "  direction stability (>=4/5 seeds), never as a seed-level CI.",
        "",
        "## Empirical anchor for rho",
        "",
        "- One-way ICC of memoryless floor pass/fail within surviving",
        f"  seed-1 clusters: **rho ~= {seed1['rho_floor']:.2f}** (the only",
        "  SUT-like outcome observable pre-pilot). The grid below brackets",
        "  it.",
        "",
        "## Single-system precision (p = 0.5, worst case)",
        "",
        "| rho | SE of mean | 95% CI half-width |",
        "|---|---|---|",
    ]
    for rho in RHO_GRID:
        se = se_single(0.5, n, m_bar, rho)
        lines.append(f"| {rho} | {se:.4f} | ±{1.96 * se * 100:.1f} pp |")
    lines += [
        "",
        "## Minimum detectable difference, paired systems "
        "(alpha=.05, power=.80, p=0.5)",
        "",
        "| rho \\ K | K=1 | K=2 | K=3 |",
        "|---|---|---|---|",
    ]
    for rho in RHO_GRID:
        cells = " | ".join(
            f"{mdd_paired(0.5, n, m_bar, rho, k) * 100:.1f} pp" for k in K_GRID
        )
        lines.append(f"| {rho} | {cells} |")
    p_sens = ", ".join(
        f"p={p}: {mdd_paired(p, n, m_bar, 0.4, 3) * 100:.1f} pp" for p in P_GRID
    )
    n_half = 4 * n
    lines += [
        "",
        f"Sensitivity at rho=0.4, K=3 across pass rates: {p_sens}.",
        "",
        "## Implications (prespecified)",
        "",
        "1. **Tie rule threshold**: at rho = 0.6 (conservatively",
        f"   bracketing the empirical {seed1['rho_floor']:.2f}) and K=3,",
        "   system deltas below"
        f" ~{mdd_paired(0.5, n, m_bar, 0.6, 3) * 100:.1f} pp overall are",
        "   reported as ties. Per-rung metrics use fewer instances, so",
        "   per-rung MDDs are larger — compute per-rung before claiming any",
        "   rung-level separation.",
        "2. **K=3 resamples are worth it** (~10-18% MDD reduction under",
        "   A5) and are already budgeted in the pilot protocol.",
        f"3. **Halving the MDD needs ~4x the data (~{n_half} instances,",
        "   ~20 seeds)** — or more efficiently, more *clusters* per seed:",
        "   adding instances within existing clusters is dampened by the",
        "   design effect, which is why v2 over-generates clusters, not",
        "   just instances.",
        "4. Headline claims must clear the paired MDD *and* direction",
        "   stability across >=4/5 seeds.",
        "",
    ]
    return "\n".join(lines)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--g3-report", type=Path,
                    default=Path("datasets/dev/org-00001/g3-report.json"))
    ap.add_argument("--report", type=Path,
                    default=Path("docs/power-analysis.md"))
    args = ap.parse_args()
    seed1 = load_seed1(args.g3_report)
    text = build_report(seed1)
    args.report.write_text(text)
    n = seed1["n_valid"] * SEEDS
    print(f"N={n} instances, m_bar={seed1['m_bar']:.2f}, "
          f"rho_floor={seed1['rho_floor']:.2f} -> {args.report}")
    print(f"MDD (p=.5, rho=.4): K=1 "
          f"{mdd_paired(0.5, n, seed1['m_bar'], 0.4, 1) * 100:.1f} pp, K=3 "
          f"{mdd_paired(0.5, n, seed1['m_bar'], 0.4, 3) * 100:.1f} pp")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
