"""Results figures + tables from `run_pilot.py report` outputs. No new
statistics: means/SEs are read from pilot-summary.json (cluster-robust,
combined across seeds there); this script only renders and applies the two
prespecified comparison rules (dataset-plan FREEZE):

  - rank-direction robustness: a cross-system ordering is called only when
    the per-seed means agree in >= 2/3 seeds (else "tie/unstable");
  - H2 (silo cost): paired per-instance diff mem0 vs mem0-silo, SE
    cluster-robust over fact clusters, combined across seeds as in run_pilot.

Usage:
  figures.py report --work W --systems nomemory,fulltranscript,...  \
      [--paired mem0,mem0-silo] [--out W/figures]

Writes: radar.svg (axes = archetypes ordered by rung; never a single
aggregate) and results.md (per-rung/per-archetype tables, cost, direction,
optional paired section).
"""

from __future__ import annotations

import argparse
import json
import math
from collections import defaultdict
from pathlib import Path

Z95 = 1.96
# archetype -> ladder rung (docs/vision.md §3); radar axis order = by rung
AXES = [("A4", 1), ("A7", 1), ("A1", 2), ("A2", 3)]


def _summary(work: Path, system: str) -> dict:
    return json.loads((work / system / "pilot-summary.json").read_text())


def radar(summaries: dict[str, dict], out: Path) -> None:
    import matplotlib
    matplotlib.use("svg")
    import matplotlib.pyplot as plt
    angles = [2 * math.pi * i / len(AXES) for i in range(len(AXES))]
    fig, ax = plt.subplots(subplot_kw={"polar": True}, figsize=(6, 6))
    for system, s in summaries.items():
        vals = [s["by_archetype"].get(a, {}).get("pair_credit_mean", 0.0)
                for a, _ in AXES]
        ax.plot(angles + angles[:1], vals + vals[:1], label=system, linewidth=1.4)
    ax.set_xticks(angles)
    ax.set_xticklabels([f"{a}\n(rung {r})" for a, r in AXES])
    ax.set_ylim(0, 1)
    ax.set_title("Pair credit by archetype (grouped by ladder rung)", pad=24)
    ax.legend(loc="upper right", bbox_to_anchor=(1.35, 1.1), fontsize=8)
    fig.savefig(out, bbox_inches="tight")
    plt.close(fig)


def _cell(v: dict | None) -> str:
    if not v:
        return "—"
    return (f"{v['pair_credit_mean']:.3f} ± {Z95 * v['se']:.3f} "
            f"(n={v['n_instances']})")


def group_table(summaries: dict[str, dict], group: str, keys: list[str]) -> list[str]:
    lines = ["| system | " + " | ".join(keys) + " |",
             "| :--- |" + " ---: |" * len(keys)]
    for system, s in summaries.items():
        cells = [_cell(s[group].get(k)) for k in keys]
        lines.append(f"| {system} | " + " | ".join(cells) + " |")
    return lines


def cost_table(summaries: dict[str, dict]) -> list[str]:
    cols = ["n_rows", "n_empty", "worker_seconds", "wall_seconds", "context_chars"]
    lines = ["| system | side | " + " | ".join(cols) + " |",
             "| :--- | :--- |" + " ---: |" * len(cols)]
    for system, s in summaries.items():
        for side in ("base", "twin"):
            v = s["cost"].get(side, {})
            lines.append(f"| {system} | {side} | " +
                         " | ".join(f"{v.get(c, 0):,.0f}" for c in cols) + " |")
    return lines


def direction(summaries: dict[str, dict], rung: str) -> list[str]:
    """Rank systems by combined mean; adjacent pairs get the >=2/3-seed rule."""
    per = {sys: s["by_rung"].get(rung) for sys, s in summaries.items()}
    per = {sys: v for sys, v in per.items() if v}
    ranked = sorted(per, key=lambda s: -per[s]["pair_credit_mean"])
    lines = []
    for hi, lo in zip(ranked, ranked[1:], strict=False):
        pairs = list(zip(per[hi]["per_seed_means"], per[lo]["per_seed_means"],
                         strict=True))
        wins = sum(1 for a, b in pairs if a > b)
        called = wins * 3 >= 2 * len(pairs)
        verdict = f"{hi} > {lo}" if called else f"{hi} ~ {lo} (tie/unstable)"
        lines.append(f"- rung {rung}: {verdict} — direction {wins}/{len(pairs)} seeds "
                     f"({per[hi]['pair_credit_mean']:.3f} vs "
                     f"{per[lo]['pair_credit_mean']:.3f})")
    return lines


def paired(work: Path, sys_a: str, sys_b: str) -> list[str]:
    """Per-instance paired diff (a - b) on pair credit; cluster-robust SE per
    seed over fact clusters; combined across seeds as in run_pilot._combine."""
    means, ses, n_pairs = [], [], 0
    sa, sb = _summary(work, sys_a), _summary(work, sys_b)
    for seed, path_a in sa["per_seed_reports"].items():
        ia = json.loads(Path(path_a).read_text())["instances"]
        ib = json.loads(Path(sb["per_seed_reports"][seed]).read_text())["instances"]
        clusters = defaultdict(list)
        for pid in sorted(set(ia) & set(ib)):
            d = float(ia[pid]["pair_credit"]) - float(ib[pid]["pair_credit"])
            clusters[ia[pid]["cluster_id"]].append(d)
        diffs = [d for ds in clusters.values() for d in ds]
        n, k = len(diffs), len(clusters)
        if not n or k < 2:
            continue
        mean = sum(diffs) / n
        cm = [sum(ds) / len(ds) for ds in clusters.values()]
        var_c = sum((m - sum(cm) / k) ** 2 for m in cm) / (k - 1)
        means.append(mean)
        ses.append(math.sqrt(var_c / k))
        n_pairs += n
    if not means:
        return [f"- paired {sys_a} vs {sys_b}: no overlapping instances"]
    mean = sum(means) / len(means)
    se = math.sqrt(sum(s * s for s in ses)) / len(means)
    return [f"- paired diff **{sys_a} − {sys_b}** (pair credit): "
            f"{mean:+.3f} ± {Z95 * se:.3f} (95% CI, cluster-robust; "
            f"n={n_pairs} paired instances, {len(means)} seeds; "
            f"per-seed {[f'{m:+.3f}' for m in means]})"]


def cmd_report(args) -> int:
    systems = args.systems.split(",")
    summaries = {s: _summary(args.work, s) for s in systems}
    out_dir = args.out or (args.work / "figures")
    out_dir.mkdir(parents=True, exist_ok=True)
    radar(summaries, out_dir / "radar.svg")
    rungs = sorted({r for s in summaries.values() for r in s["by_rung"]})
    md = ["# Pilot results (generated by scripts/figures.py — no hand edits)", "",
          "Never a single aggregate: read per rung. Pair credit mean ± 95% CI,",
          "cluster-robust SEs combined across seeds (see pilot-summary.json note).", "",
          "## By rung", ""]
    md += group_table(summaries, "by_rung", rungs)
    md += ["", "## By archetype", ""]
    md += group_table(summaries, "by_archetype", [a for a, _ in AXES])
    md += ["", "## Rank direction (called only at >= 2/3 seeds agreeing)", ""]
    for rung in rungs:
        md += direction(summaries, rung)
    if args.paired:
        a, b = args.paired.split(",")
        md += ["", "## Paired comparison (H2)", ""] + paired(args.work, a, b)
    md += ["", "## Cost", ""] + cost_table(summaries)
    (out_dir / "results.md").write_text("\n".join(md) + "\n")
    print(f"wrote {out_dir / 'radar.svg'} and {out_dir / 'results.md'}")
    return 0


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    sp = sub.add_parser("report")
    sp.add_argument("--work", type=Path, required=True)
    sp.add_argument("--systems", required=True)
    sp.add_argument("--paired", default=None, help="sysA,sysB e.g. mem0,mem0-silo")
    sp.add_argument("--out", type=Path, default=None)
    return cmd_report(ap.parse_args(argv))


if __name__ == "__main__":
    raise SystemExit(main())
