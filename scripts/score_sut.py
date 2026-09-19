"""Score one system-under-test (SUT) run against the screened probe set
(probe-spec §3-§4, dataset-plan Phase 5 statistics protocol).

Inputs per org seed:
  - screening work dir  (runs.jsonl / results.jsonl / judgements.jsonl):
    the floor / ceiling / twin anchors and their blinded verdicts;
  - the org's g3-report.json: which instances are VALID (only those score);
  - two runner outputs from the SAME adapter: base org (`--sut-base`) and
    counterfactual twin org (`--sut-twin`), rows {run_id "<probe>:sut", output}.

Pipeline (same blinding discipline as screening):
  manifest  -> <work>/runs.jsonl rows "<probe>:sut_base" (scored against the
               base assertions) and "<probe>:sut_twin" (against the cf
               assertions), with the same hedge patterns as the anchors;
  judge-export / judge-import -> reuse screen_probes' opaque-id export and
               import verbatim (judge sees output + criteria only);
  report    -> per instance: sut_base, sut_twin, floor, ceiling, twin_ceiling
               scores; PAIR CREDIT = sut_base >= 1.0 AND sut_twin >= 1.0
               (spec §4: credited only if both sides pass); per-side
               normalized scores (sut - floor)/(ceiling - floor) clipped to
               [0,1] for the diagnostic tables; aggregation per metric and
               per rung as mean pair credit over valid instances with a
               cluster-robust SE (clusters = fact clusters; design-effect
               form, dataset-plan statistics protocol) and a 95% CI.

Empty-output rule (v0.4.3): a null/empty SUT deliverable scores 0.0 on
every assertion and stays in the denominator. Never a single aggregate.

Usage:
  python scripts/score_sut.py manifest <org_dir> <screening_dir> <work_dir> \
      --sut-base <results.jsonl> --sut-twin <results.jsonl> --system <name>
  python scripts/screen_probes.py judge-export <work_dir>       # then judge, then
  python scripts/screen_probes.py judge-import <work_dir> <verdicts.json> --judge <tag>
  python scripts/score_sut.py report <org_dir> <screening_dir> <work_dir> [--out report.json]
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import math
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from membench.g3 import valid_instances  # noqa: E402

_SPEC = importlib.util.spec_from_file_location(
    "screen_probes", ROOT / "scripts" / "screen_probes.py")
sp = importlib.util.module_from_spec(_SPEC)
sys.modules.setdefault("screen_probes", sp)
_SPEC.loader.exec_module(sp)

RUNG = {"A4": 1, "A6": 1, "A7": 1, "A9": 1,
        "A1": 2, "A5": 2, "A8": 2, "A10": 2,
        "A2": 3, "A3": 3, "A11": 3, "A12": 3}
Z95 = 1.959964


def _jsonl(path: Path) -> list[dict]:
    return [json.loads(x) for x in path.read_text().splitlines() if x.strip()]


def _last(rows: list[dict], key: str = "run_id") -> dict[str, dict]:
    out = {}
    for r in rows:
        out[r[key]] = r
    return out


def cmd_manifest(args) -> int:
    runs = _last(_jsonl(args.screening_dir / "runs.jsonl"))
    # valid instances of SURVIVING clusters only (the frozen 371 across seeds 1-3)
    valid = valid_instances(json.loads((args.org_dir / "g3-report.json").read_text()))
    base = _last(_jsonl(args.sut_base))
    twin = _last(_jsonl(args.sut_twin)) if args.sut_twin else {}
    rows, results = [], []
    for pid in sorted(valid):
        floor_row = runs[f"{pid}:floor"]
        b = base.get(f"{pid}:sut")
        if b is None:
            raise SystemExit(f"missing SUT base output for valid instance {pid}")
        rows.append({"run_id": f"{pid}:sut_base", "probe_id": pid,
                     "cluster_id": floor_row["cluster_id"], "condition": "sut_base",
                     "system": args.system, "prompt": "",
                     "assertions": floor_row["assertions"],
                     "hedge_base": floor_row.get("hedge_base"),
                     "hedge_cf": floor_row.get("hedge_cf")})
        results.append({"run_id": f"{pid}:sut_base", "output": b.get("output"),
                        "error": b.get("error")})
        if floor_row.get("cf_assertions"):
            t = twin.get(f"{pid}:sut")
            if t is None:
                raise SystemExit(f"missing SUT twin output for paired instance {pid}")
            rows.append({"run_id": f"{pid}:sut_twin", "probe_id": pid,
                         "cluster_id": floor_row["cluster_id"], "condition": "sut_twin",
                         "system": args.system, "prompt": "",
                         "assertions": floor_row["cf_assertions"],
                         "hedge_base": floor_row.get("hedge_base"),
                         "hedge_cf": floor_row.get("hedge_cf")})
            results.append({"run_id": f"{pid}:sut_twin", "output": t.get("output"),
                            "error": t.get("error")})
    args.work_dir.mkdir(parents=True, exist_ok=True)
    (args.work_dir / "runs.jsonl").write_text("".join(json.dumps(r) + "\n" for r in rows))
    (args.work_dir / "results.jsonl").write_text(
        "".join(json.dumps(r) + "\n" for r in results))
    (args.work_dir / "judgements.jsonl").touch()
    (args.work_dir / "manifest.json").write_text(json.dumps({
        "system": args.system, "org": args.org_dir.name, "valid_instances": len(valid),
        "sut_base": str(args.sut_base), "sut_twin": str(args.sut_twin)}, indent=1))
    n_empty = sum(1 for r in results if not (r.get("output") or "").strip())
    print(f"{len(rows)} SUT rows for {len(valid)} valid instances -> {args.work_dir} "
          f"({n_empty} empty/null deliverables score 0.0)")
    return 0


def _score_row(runs, results, judgements, rid) -> float:
    row = runs[rid]
    out = (results.get(rid) or {}).get("output") or ""
    verdicts = (judgements.get(rid) or {}).get("verdicts")
    if not out.strip():
        return 0.0
    hedged = sp.is_hedged(out, row.get("hedge_base"), row.get("hedge_cf"))
    return sp._score(rid, row["assertions"], out, verdicts, hedged=hedged)


def _norm(sut: float, floor: float, ceiling: float) -> float | None:
    if ceiling - floor <= 1e-9:
        return None
    return max(0.0, min(1.0, (sut - floor) / (ceiling - floor)))


def _cluster_robust(values: dict[str, list[float]]) -> tuple[float, float, int, int]:
    """(mean, se, n_instances, n_clusters): design-effect SE with rho
    estimated from the between/within decomposition (one-way ICC)."""
    xs = [v for vs in values.values() for v in vs]
    n = len(xs)
    if n == 0:
        return float("nan"), float("nan"), 0, 0
    mean = sum(xs) / n
    var = sum((x - mean) ** 2 for x in xs) / max(n - 1, 1)
    k = len(values)
    if k <= 1 or n <= 1:
        return mean, math.sqrt(var / n) if n else float("nan"), n, k
    m_bar = n / k
    means = {c: sum(vs) / len(vs) for c, vs in values.items()}
    msb = sum(len(vs) * (means[c] - mean) ** 2 for c, vs in values.items()) / (k - 1)
    msw = sum((x - means[c]) ** 2 for c, vs in values.items() for x in vs) / max(n - k, 1)
    denom = msb + (m_bar - 1) * msw
    rho = max(0.0, (msb - msw) / denom) if denom > 0 else 0.0
    de = 1 + (m_bar - 1) * rho
    se = math.sqrt(var / n * de)
    return mean, se, n, k


def _wilson_cluster(values: dict[str, list[float]], z: float = Z95) -> dict:
    """Wilson score interval on the cluster-adjusted effective sample size.

    Added 2026-09-17, post-hoc, because the Wald interval beside it is wrong at
    these counts and degenerate at zero: a rung with no successes gets [0, 0],
    which claims infinite precision from 16 observations. That is the failure
    arXiv:2503.01747 describes for evals below a few hundred datapoints. Wilson
    keeps the interval inside [0, 1] and stays finite at 0 successes.

    The clustering correction is preserved by deflating n rather than inflating
    the SE: n_eff = n / deff, with deff the same design effect `_cluster_robust`
    applies. Where the sample variance is zero the design effect is undefined
    and is taken as 1.
    """
    mean, se, n, k = _cluster_robust(values)
    if n == 0:
        return {"ci95_wilson": [float("nan"), float("nan")], "n_eff": 0.0, "deff": 1.0}
    xs = [v for vs in values.values() for v in vs]
    var = sum((x - mean) ** 2 for x in xs) / max(n - 1, 1)
    naive = math.sqrt(var / n)
    deff = (se / naive) ** 2 if naive > 0 else 1.0
    n_eff = n / deff
    z2 = z * z
    denom = 1 + z2 / n_eff
    centre = (mean + z2 / (2 * n_eff)) / denom
    half = (z / denom) * math.sqrt(mean * (1 - mean) / n_eff + z2 / (4 * n_eff * n_eff))
    return {"ci95_wilson": [round(max(0.0, centre - half), 4),
                            round(min(1.0, centre + half), 4)],
            "n_eff": round(n_eff, 2), "deff": round(deff, 4)}


def cmd_report(args) -> int:
    runs = _last(_jsonl(args.work_dir / "runs.jsonl"))
    results = _last(_jsonl(args.work_dir / "results.jsonl"))
    judgements = _last(_jsonl(args.work_dir / "judgements.jsonl"))
    s_runs = _last(_jsonl(args.screening_dir / "runs.jsonl"))
    s_results = _last(_jsonl(args.screening_dir / "results.jsonl"))
    s_j = _last(_jsonl(args.screening_dir / "judgements.jsonl"))
    probes = _last(_jsonl(args.org_dir / "probes.jsonl"), "probe_id")
    manifest = json.loads((args.work_dir / "manifest.json").read_text())

    per: dict[str, dict] = {}
    for rid, row in runs.items():
        pid = row["probe_id"]
        p = per.setdefault(pid, {"cluster_id": row["cluster_id"]})
        p[row["condition"]] = _score_row(runs, results, judgements, rid)
    for pid, p in per.items():
        p["floor"] = _score_row(s_runs, s_results, s_j, f"{pid}:floor")
        p["ceiling"] = _score_row(s_runs, s_results, s_j, f"{pid}:ceiling")
        if f"{pid}:twin_ceiling" in s_runs:
            p["twin_ceiling"] = _score_row(s_runs, s_results, s_j, f"{pid}:twin_ceiling")
        paired = "sut_twin" in p
        p["pair_credit"] = (p["sut_base"] >= sp.CEILING_PASS and
                            (not paired or p["sut_twin"] >= sp.CEILING_PASS))
        p["norm_base"] = _norm(p["sut_base"], p["floor"], p["ceiling"])
        if paired:
            p["norm_twin"] = _norm(p["sut_twin"], 0.0, p.get("twin_ceiling", 1.0))
        pr = probes[pid]
        p["archetype"] = pr["archetype"]
        p["metrics"] = pr.get("metrics") or []
        p["rung"] = RUNG.get(pr["archetype"])

    by_metric: dict[str, dict[str, list[float]]] = defaultdict(lambda: defaultdict(list))
    by_rung: dict[str, dict[str, list[float]]] = defaultdict(lambda: defaultdict(list))
    by_arch: dict[str, dict[str, list[float]]] = defaultdict(lambda: defaultdict(list))
    for p in per.values():
        v = 1.0 if p["pair_credit"] else 0.0
        for m in p["metrics"] or ["unlabelled"]:
            by_metric[m][p["cluster_id"]].append(v)
        by_rung[str(p["rung"])][p["cluster_id"]].append(v)
        by_arch[p["archetype"]][p["cluster_id"]].append(v)

    def agg(groups):
        out = {}
        for key, clusters in sorted(groups.items()):
            mean, se, n, k = _cluster_robust(clusters)
            out[key] = {"pair_credit_mean": round(mean, 4), "se_cluster_robust": round(se, 4),
                        "ci95": [round(mean - Z95 * se, 4), round(mean + Z95 * se, 4)],
                        "successes": int(round(mean * n)),
                        "n_instances": n, "n_clusters": k, **_wilson_cluster(clusters)}
        return out

    report = {"system": manifest["system"], "org": manifest["org"],
              "n_valid_instances": len(per),
              "n_empty_deliverables": sum(1 for rid, r in results.items()
                                          if not (r.get("output") or "").strip()),
              "by_rung": agg(by_rung), "by_metric": agg(by_metric),
              "by_archetype": agg(by_arch),
              "instances": {pid: per[pid] for pid in sorted(per)},
              "note": ("Radar by rung/metric; never a single aggregate. Pair credit per "
                       "probe-spec §4; SEs cluster-robust (design effect, clusters = fact "
                       "clusters); K resamples and the tie rule are applied at the "
                       "cross-system comparison stage, not here.")}
    text = json.dumps(report, indent=1)
    if args.out:
        args.out.write_text(text)
    print(f"{report['system']} on {report['org']}: {len(per)} valid instances, "
          f"{report['n_empty_deliverables']} empty deliverables")
    for r, v in report["by_rung"].items():
        print(f"  rung {r}: pair credit {v['pair_credit_mean']:.3f} "
              f"Wilson95 {v['ci95_wilson']} "
              f"(n={v['n_instances']}, k={v['n_clusters']})")
    for m, v in report["by_metric"].items():
        print(f"  {m}: {v['pair_credit_mean']:.3f} ± {Z95 * v['se_cluster_robust']:.3f}")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    m = sub.add_parser("manifest")
    m.add_argument("org_dir", type=Path)
    m.add_argument("screening_dir", type=Path)
    m.add_argument("work_dir", type=Path)
    m.add_argument("--sut-base", type=Path, required=True)
    m.add_argument("--sut-twin", type=Path, default=None)
    m.add_argument("--system", required=True)
    r = sub.add_parser("report")
    r.add_argument("org_dir", type=Path)
    r.add_argument("screening_dir", type=Path)
    r.add_argument("work_dir", type=Path)
    r.add_argument("--out", type=Path, default=None)
    args = ap.parse_args()
    return {"manifest": cmd_manifest, "report": cmd_report}[args.cmd](args)


if __name__ == "__main__":
    raise SystemExit(main())
