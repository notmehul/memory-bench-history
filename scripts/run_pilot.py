"""Cross-seed pilot orchestrator (v1 freeze, dataset-plan "v1 pilot FREEZE").

Thin loop over seeds x sides on top of `membench.pilot` (one adapter over
one org side, pinned CodexWorker, resumable, only-valid instances) and
`scripts/score_sut.py` (manifest -> blinded judge round trip via
screen_probes -> per-seed report). Nothing here scores or judges on its own.

  python scripts/run_pilot.py run --system <name> --seeds 1,2,3 --work <dir> \
      [--k 1] [--silo] [--datasets datasets/dev]
  python scripts/screen_probes.py judge-export <work>/<system>/seed-N/score-k1   # per seed
      ... fresh judge agents read ONLY pending-judge.json ...
  python scripts/screen_probes.py judge-import <work>/<system>/seed-N/score-k1 \
      <verdicts.json> --judge <tag>
  python scripts/run_pilot.py report --system <name> --seeds 1,2,3 --work <dir> [--k 1]

Layout under <work>/<system>/seed-N/: base-k<K>.jsonl, twin-k<K>.jsonl
(+ .meta.json each), score-k<K>/ (score_sut work dir + report.json);
`report` writes <work>/<system>/pilot-summary.json: per-rung / per-archetype
/ per-metric mean pair credit over seeds (mean of per-seed means; SE =
sqrt(sum of per-seed cluster-robust SE^2) / n_seeds — seeds independent,
equal weight), instance and cluster counts, cost totals per side. Never a
single aggregate scalar across rungs.

`--k N` runs resamples 1..N (each a fresh adapter + full ingestion pass);
`report --k` selects one resample to summarize (run variance across
resamples is analysed at the tie-rule stage, not here). `--dry-run` swaps in
`MockWorker` for tests only — the protocol path is always the pinned codex.
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import math
import sys
from collections import defaultdict
from pathlib import Path
from types import SimpleNamespace

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from membench import pilot  # noqa: E402
from membench.adapters import MockWorker  # noqa: E402
from membench.workers import CodexWorker  # noqa: E402


def _load_script(name: str):
    if name in sys.modules:
        return sys.modules[name]
    spec = importlib.util.spec_from_file_location(name, ROOT / "scripts" / f"{name}.py")
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


score_sut = _load_script("score_sut")


def seed_dirs(datasets: Path, seed: int) -> tuple[Path, Path, Path]:
    org = datasets / f"org-{seed:05d}"
    return org, datasets / f"org-{seed:05d}-twin", datasets / "screening" / f"org-{seed:05d}"


def _paths(work: Path, system: str, seed: int, k: int) -> dict[str, Path]:
    d = work / system / f"seed-{seed}"
    return {"dir": d, "base": d / f"base-k{k}.jsonl", "twin": d / f"twin-k{k}.jsonl",
            "score": d / f"score-k{k}", "report": d / f"score-k{k}" / "report.json"}


def cmd_run(args) -> int:
    seeds = [int(s) for s in args.seeds.split(",")]
    for seed in seeds:
        org, twin, screening = seed_dirs(args.datasets, seed)
        for k in range(1, args.k + 1):
            p = _paths(args.work, args.system, seed, k)
            for side, org_dir in (("base", org), ("twin", twin)):
                worker = MockWorker() if args.dry_run else CodexWorker()
                meta = pilot.run_side(
                    args.system, org_dir, p[side], worker, silo=args.silo,
                    probes_from=org, only_valid=True, system=args.system,
                    side=side, k=k)
                print(f"seed {seed} {side} k={k}: {meta['n_new_rows']} new, "
                      f"{meta['n_resumed']} resumed, "
                      f"{meta['n_skipped_invalid']} invalid skipped", flush=True)
            score_sut.cmd_manifest(SimpleNamespace(
                org_dir=org, screening_dir=screening, work_dir=p["score"],
                sut_base=p["base"], sut_twin=p["twin"], system=args.system))
            print(f"next: python scripts/screen_probes.py judge-export {p['score']}")
    return 0


def _combine(seed_groups: list[dict]) -> dict:
    """Mean over seeds of per-seed group means; SE from independent seeds."""
    keys = sorted({k for g in seed_groups for k in g})
    out = {}
    for key in keys:
        present = [g[key] for g in seed_groups if key in g]
        means = [v["pair_credit_mean"] for v in present]
        ses = [v["se_cluster_robust"] for v in present]
        n = len(present)
        mean = sum(means) / n
        se = math.sqrt(sum(s * s for s in ses)) / n
        out[key] = {"pair_credit_mean": round(mean, 4), "se": round(se, 4),
                    "ci95": [round(mean - score_sut.Z95 * se, 4),
                             round(mean + score_sut.Z95 * se, 4)],
                    "per_seed_means": [round(m, 4) for m in means],
                    "n_seeds": n,
                    "n_instances": sum(v["n_instances"] for v in present),
                    "n_clusters": sum(v["n_clusters"] for v in present)}
    return out


def _cost(rows_path: Path) -> dict:
    rows = list(pilot.read_rows(rows_path).values())
    return {"n_rows": len(rows),
            "n_empty": sum(1 for r in rows if not (r.get("output") or "").strip()),
            "worker_seconds": round(sum(r.get("seconds", 0.0) for r in rows), 3),
            "wall_seconds": round(sum(r.get("wall_seconds", 0.0) for r in rows), 3),
            "context_chars": sum(r.get("context_chars", 0) for r in rows)}


def cmd_report(args) -> int:
    seeds = [int(s) for s in args.seeds.split(",")]
    per_seed, costs = {}, defaultdict(lambda: defaultdict(float))
    for seed in seeds:
        org, _twin, screening = seed_dirs(args.datasets, seed)
        p = _paths(args.work, args.system, seed, args.k)
        score_sut.cmd_report(SimpleNamespace(
            org_dir=org, screening_dir=screening, work_dir=p["score"], out=p["report"]))
        per_seed[seed] = json.loads(p["report"].read_text())
        for side in ("base", "twin"):
            for key, v in _cost(p[side]).items():
                costs[side][key] += v
    reports = list(per_seed.values())
    summary = {
        "system": args.system, "seeds": seeds, "k": args.k,
        "n_valid_instances": sum(r["n_valid_instances"] for r in reports),
        "n_empty_deliverables": sum(r["n_empty_deliverables"] for r in reports),
        "by_rung": _combine([r["by_rung"] for r in reports]),
        "by_archetype": _combine([r["by_archetype"] for r in reports]),
        "by_metric": _combine([r["by_metric"] for r in reports]),
        "cost": {side: dict(v) for side, v in costs.items()},
        "per_seed_reports": {str(s): str(_paths(args.work, args.system, s, args.k)["report"])
                             for s in seeds},
        "note": ("Radar by rung; never a single aggregate. Mean over seeds of per-seed "
                 "means; SE = sqrt(sum per-seed cluster-robust SE^2)/n_seeds."),
    }
    out = args.work / args.system / "pilot-summary.json"
    out.write_text(json.dumps(summary, indent=1))
    print(f"{args.system}: {summary['n_valid_instances']} valid instances over "
          f"seeds {seeds} -> {out}")
    for r, v in summary["by_rung"].items():
        print(f"  rung {r}: pair credit {v['pair_credit_mean']:.3f} ± "
              f"{score_sut.Z95 * v['se']:.3f} (n={v['n_instances']}, seeds={v['n_seeds']})")
    return 0


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    for name in ("run", "report"):
        sp = sub.add_parser(name)
        sp.add_argument("--system", required=True, choices=sorted(pilot.ADAPTERS))
        sp.add_argument("--seeds", default="1,2,3")
        sp.add_argument("--work", type=Path, required=True)
        sp.add_argument("--k", type=int, default=1)
        sp.add_argument("--datasets", type=Path, default=ROOT / "datasets" / "dev")
    sub.choices["run"].add_argument("--silo", action="store_true")
    sub.choices["run"].add_argument("--dry-run", action="store_true",
                                    help="MockWorker (tests only; never a protocol run)")
    args = ap.parse_args(argv)
    return {"run": cmd_run, "report": cmd_report}[args.cmd](args)


if __name__ == "__main__":
    raise SystemExit(main())
