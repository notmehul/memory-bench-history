"""Phase 4 judge calibration: blinded human-rater packet + kappa gates (dataset-plan Phase 4).

`sample` draws (output, criterion) pairs from committed screening evidence into a
BLINDED rater packet — the same opaque-id discipline as screen_probes.py judge-export:
raters see only the deliverable text and the criterion statement, never run ids,
conditions (floor/ceiling/twin), or base-vs-counterfactual side. Only semantic
assertions are sampled (pattern checkers are mechanical; there is nothing to
calibrate). Both human raters receive the identical packet.

`kappa` reports inter-rater Cohen's kappa, raw agreement, and the disagreement list
for adjudication. `judge-agreement` scores the committed judge verdicts against the
adjudicated human gold: overall and per-assertion-kind kappa, plus every criterion
whose raw agreement falls below the 0.7 rewrite-or-drop threshold (per-criterion n
is small — 1 or 2 sampled pairs — so that gate uses raw agreement, reported with
its n; the binding gate G4 is the overall kappa >= 0.75).

Sampling pools one or more screening dirs (run/cluster ids repeat across org seeds,
so every pair is keyed by org = the screening dir's basename). One screened seed
supports at most 2 x 54 = 108 pairs under the per-cluster cap; the 150-pair target
needs at least two screened seeds, and a smaller pool is reported loudly, never
silently.

Usage:
  python scripts/calibration.py sample <screening_dir>... <out_dir> [--n 150] [--seed S]
  python scripts/calibration.py kappa <out_dir> <ratings_a.json> <ratings_b.json>
  python scripts/calibration.py judge-agreement <out_dir> <adjudicated.json> <screening_dir>...
"""

from __future__ import annotations

import argparse
import hashlib
import json
import random
from collections import Counter, defaultdict
from pathlib import Path

REWRITE_THRESHOLD = 0.7
CLUSTER_CAP = 2

# Bootstrap settings for the kappa interval added 2026-09-17. Post-hoc: the G4
# gate was prespecified and measured on the point estimate, and the interval
# changes no verdict. Fixed seed so the interval is reproducible.
BOOTSTRAP_B = 10000
BOOTSTRAP_SEED = 20260917


# --------------------------------------------------------------- shared

def _read_jsonl(path: Path) -> list[dict]:
    return [json.loads(x) for x in path.read_text().splitlines() if x.strip()]


def _last_wins(rows: list[dict], key: str = "run_id") -> dict[str, dict]:
    out: dict[str, dict] = {}
    for r in rows:
        out[r[key]] = r
    return out


def _semantic_pool(row: dict) -> list[dict]:
    pool = row["assertions"] + (row.get("cf_assertions") or [])
    return [a for a in pool if a["checker"] == "semantic"]


def _pair_id(org: str, run_id: str, assertion_id: str) -> str:
    return "p" + hashlib.sha1(f"{org}|{run_id}|{assertion_id}".encode()).hexdigest()[:12]


def _load_ratings(path: Path, ids: set[str], label: str) -> dict[str, bool]:
    data = json.loads(Path(path).read_text())
    missing = sorted(ids - set(data))
    extra = sorted(set(data) - ids)
    if missing or extra:
        raise SystemExit(
            f"{label}: rating ids do not match the packet "
            f"(missing {missing[:5]}, extra {extra[:5]})")
    bad = sorted(k for k, v in data.items() if not isinstance(v, bool))
    if bad:
        raise SystemExit(f"{label}: non-boolean ratings for {bad[:5]} — use true/false")
    return data


def _cohens_kappa(xs: list[bool], ys: list[bool]) -> tuple[float, float, bool]:
    """Return (raw_agreement, kappa, degenerate) for two binary label lists."""
    n = len(xs)
    po = sum(1 for x, y in zip(xs, ys, strict=True) if x == y) / n
    pa = sum(xs) / n
    pb = sum(ys) / n
    pe = pa * pb + (1 - pa) * (1 - pb)
    if pe >= 1.0 - 1e-12:
        # Both raters used a single label class: chance agreement is 1 and the
        # standard formula is 0/0. Perfect agreement on one class reports 1.0.
        return po, (1.0 if po >= 1.0 - 1e-12 else 0.0), True
    return po, (po - pe) / (1 - pe), False


def _bootstrap_kappa_ci(rows: list[dict], b: int = BOOTSTRAP_B,
                        seed: int = BOOTSTRAP_SEED) -> dict:
    """Percentile CI for Cohen's kappa, resampling CLUSTERS rather than items.

    The packet is stratified with a per-cluster cap, so criteria inside one
    fact cluster are not independent and an item-level bootstrap would report
    an interval narrower than the data support. Each replicate draws as many
    clusters as the sample holds, with replacement, and pools their rows.

    A replicate in which both raters used a single label has chance agreement 1
    and no kappa; `_cohens_kappa` resolves it to 1.0 or 0.0 and those
    replicates are counted in the report rather than dropped silently.

    Added 2026-09-17, post-hoc. The point estimate and the gate verdict it was
    measured against are untouched.
    """
    by_cluster: dict[tuple, list[dict]] = defaultdict(list)
    for r in rows:
        by_cluster[r["cluster"]].append(r)
    clusters = sorted(by_cluster)
    rng = random.Random(seed)
    kappas: list[float] = []
    degenerate = 0
    for _ in range(b):
        sample = [r for _ in clusters
                  for r in by_cluster[clusters[rng.randrange(len(clusters))]]]
        _, k, deg = _cohens_kappa([r["human"] for r in sample],
                                  [r["judge"] for r in sample])
        kappas.append(k)
        degenerate += bool(deg)
    kappas.sort()
    return {"ci95": [round(kappas[int(0.025 * b)], 4),
                     round(kappas[int(0.975 * b) - 1], 4)],
            "replicates": b, "seed": seed, "n_clusters": len(clusters),
            "degenerate_replicates": degenerate}


# --------------------------------------------------------------- sample

def _candidates(screening_dirs: list[Path]) -> list[dict]:
    orgs = [d.resolve().name for d in screening_dirs]
    if len(set(orgs)) != len(orgs):
        raise SystemExit(f"screening dirs must have distinct basenames, got {orgs}")
    cands = []
    for d in sorted(screening_dirs, key=lambda p: p.resolve().name):
        org = d.resolve().name
        runs = _last_wins(_read_jsonl(d / "runs.jsonl"))
        results = _last_wins(_read_jsonl(d / "results.jsonl"))
        for rid in sorted(runs):
            res = results.get(rid)
            if not res or not res.get("output"):
                continue
            row = runs[rid]
            condition = rid.rsplit(":", 1)[1]
            for a in _semantic_pool(row):
                cands.append({
                    "org": org,
                    "run_id": rid,
                    "assertion_id": a["id"],
                    "criterion": a["criterion"],
                    "kind": a["kind"],
                    "cluster": (org, row["cluster_id"]),
                    "stratum": (condition, a["kind"]),
                    "output": res["output"],
                })
    return cands


def _allocate(strata_sizes: dict[tuple, int], n: int) -> dict[tuple, int]:
    """Largest-remainder proportional allocation of n over strata."""
    total = sum(strata_sizes.values())
    exact = {s: n * size / total for s, size in strata_sizes.items()}
    quota = {s: int(exact[s]) for s in strata_sizes}
    leftover = n - sum(quota.values())
    by_remainder = sorted(strata_sizes, key=lambda s: (-(exact[s] - quota[s]), s))
    for s in by_remainder[:leftover]:
        quota[s] += 1
    return quota


def cmd_sample(args) -> int:
    cands = _candidates(args.screening_dirs)
    if not cands:
        raise SystemExit(f"no semantic (output, criterion) pairs under {args.screening_dirs}")
    rng = random.Random(args.seed)
    by_stratum: dict[tuple, list[dict]] = defaultdict(list)
    for c in cands:
        by_stratum[c["stratum"]].append(c)
    quota = _allocate({s: len(v) for s, v in by_stratum.items()}, args.n)

    selected: list[dict] = []
    chosen: set[tuple[str, str]] = set()
    per_cluster: Counter = Counter()

    def take(pool: list[dict], want: int) -> None:
        for c in pool:
            if want <= 0:
                return
            key = (c["org"], c["run_id"], c["assertion_id"])
            if key in chosen or per_cluster[c["cluster"]] >= CLUSTER_CAP:
                continue
            chosen.add(key)
            per_cluster[c["cluster"]] += 1
            selected.append(c)
            want -= 1

    for stratum in sorted(by_stratum):
        pool = by_stratum[stratum]
        rng.shuffle(pool)
        take(pool, quota[stratum])
    if len(selected) < args.n:  # cluster cap starved some strata; refill globally
        rest = [c for c in cands
                if (c["org"], c["run_id"], c["assertion_id"]) not in chosen]
        rng.shuffle(rest)
        take(rest, args.n - len(selected))
    if len(selected) < args.n:
        print(f"WARNING: only {len(selected)}/{args.n} pairs available under the "
              f"{CLUSTER_CAP}-per-cluster cap — packet is smaller than requested")

    packet, key_map, template = [], {}, {}
    for c in selected:
        pid = _pair_id(c["org"], c["run_id"], c["assertion_id"])
        packet.append({"id": pid, "criterion": c["criterion"], "output": c["output"]})
        key_map[pid] = {"org": c["org"], "run_id": c["run_id"],
                        "assertion_id": c["assertion_id"]}
    packet.sort(key=lambda r: r["id"])  # opaque order, not manifest order
    template = {row["id"]: None for row in packet}

    args.out_dir.mkdir(parents=True, exist_ok=True)
    (args.out_dir / "rater-packet.json").write_text(json.dumps(packet, indent=1))
    (args.out_dir / "packet-key.json").write_text(json.dumps(key_map, indent=1))
    (args.out_dir / "rating-template.json").write_text(json.dumps(template, indent=1))
    strata = Counter(c["stratum"] for c in selected)
    print(f"{len(packet)} pairs -> {args.out_dir}/rater-packet.json "
          f"(strata: {dict((f'{c}/{k}', v) for (c, k), v in sorted(strata.items()))})")
    return 0


# --------------------------------------------------------------- kappa

def cmd_kappa(args) -> int:
    packet = json.loads((args.out_dir / "rater-packet.json").read_text())
    ids = [row["id"] for row in packet]
    criterion = {row["id"]: row["criterion"] for row in packet}
    a = _load_ratings(args.ratings_a, set(ids), "ratings_a")
    b = _load_ratings(args.ratings_b, set(ids), "ratings_b")
    po, kappa, degenerate = _cohens_kappa([a[i] for i in ids], [b[i] for i in ids])
    disagreements = [{"id": i, "criterion": criterion[i]} for i in ids if a[i] != b[i]]
    report = {
        "n": len(ids),
        "raw_agreement": round(po, 4),
        "kappa": round(kappa, 4),
        "degenerate_marginals": degenerate,
        "disagreements": disagreements,
    }
    (args.out_dir / "kappa-report.json").write_text(json.dumps(report, indent=1))
    print(f"inter-rater: n={len(ids)} agreement={po:.3f} kappa={kappa:.3f} "
          f"({len(disagreements)} disagreements to adjudicate) -> kappa-report.json")
    return 0


# --------------------------------------------------------------- judge-agreement

def cmd_judge_agreement(args) -> int:
    key_map = json.loads((args.out_dir / "packet-key.json").read_text())
    gold = _load_ratings(args.adjudicated, set(key_map), "adjudicated")
    by_org: dict[str, tuple[dict, dict]] = {}
    for d in args.screening_dirs:
        org = d.resolve().name
        by_org[org] = (_last_wins(_read_jsonl(d / "runs.jsonl")),
                       _last_wins(_read_jsonl(d / "judgements.jsonl")))
    needed = {ref["org"] for ref in key_map.values()}
    if not needed <= set(by_org):
        raise SystemExit(f"packet references orgs without a screening dir: "
                         f"{sorted(needed - set(by_org))}")

    rows = []
    for pid, ref in sorted(key_map.items()):
        org, rid, aid = ref["org"], ref["run_id"], ref["assertion_id"]
        runs, judgements = by_org[org]
        j = judgements.get(rid)
        if not j or aid not in j.get("verdicts", {}):
            raise SystemExit(f"no judge verdict for {org}/{rid}/{aid}")
        a = next(x for x in runs[rid]["assertions"] + (runs[rid].get("cf_assertions") or [])
                 if x["id"] == aid)
        rows.append({
            "human": gold[pid], "judge": bool(j["verdicts"][aid]), "kind": a["kind"],
            "cluster": (org, runs[rid]["cluster_id"]), "assertion_id": aid,
            "criterion": a["criterion"],
        })

    po, kappa, degenerate = _cohens_kappa(
        [r["human"] for r in rows], [r["judge"] for r in rows])
    per_kind = {}
    for kind in sorted({r["kind"] for r in rows}):
        sub = [r for r in rows if r["kind"] == kind]
        kpo, kk, kdeg = _cohens_kappa([r["human"] for r in sub], [r["judge"] for r in sub])
        per_kind[kind] = {"n": len(sub), "agreement": round(kpo, 4),
                          "kappa": round(kk, 4), "degenerate_marginals": kdeg,
                          "kappa_bootstrap": _bootstrap_kappa_ci(sub)}

    by_criterion: dict[tuple, list[dict]] = defaultdict(list)
    for r in rows:
        by_criterion[(r["cluster"], r["assertion_id"])].append(r)
    below = []
    for ((org, cluster), aid), sub in sorted(by_criterion.items()):
        agreement = sum(1 for r in sub if r["human"] == r["judge"]) / len(sub)
        if agreement < REWRITE_THRESHOLD:
            below.append({"org": org, "cluster_id": cluster, "assertion_id": aid,
                          "n": len(sub), "agreement": round(agreement, 4),
                          "criterion": sub[0]["criterion"]})

    report = {
        "n": len(rows),
        "raw_agreement": round(po, 4),
        "kappa": round(kappa, 4),
        "degenerate_marginals": degenerate,
        "kappa_bootstrap": _bootstrap_kappa_ci(rows),
        "gate_g4_overall": kappa >= 0.75,
        "per_kind": per_kind,
        "criteria_below_threshold": below,
    }
    (args.out_dir / "judge-agreement.json").write_text(json.dumps(report, indent=1))
    ci = report["kappa_bootstrap"]["ci95"]
    print(f"  kappa 95% CI (cluster bootstrap): [{ci[0]:.3f}, {ci[1]:.3f}]")
    print(f"judge vs human gold: n={len(rows)} agreement={po:.3f} kappa={kappa:.3f} "
          f"gate>=0.75: {'PASS' if report['gate_g4_overall'] else 'FAIL'}; "
          f"{len(below)} criteria below {REWRITE_THRESHOLD} -> judge-agreement.json")
    return 0


# --------------------------------------------------------------- cli

def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    sub = ap.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("sample")
    s.add_argument("screening_dirs", type=Path, nargs="+")
    s.add_argument("out_dir", type=Path)
    s.add_argument("--n", type=int, default=150)
    s.add_argument("--seed", type=int, default=20260725)
    k = sub.add_parser("kappa")
    k.add_argument("out_dir", type=Path)
    k.add_argument("ratings_a", type=Path)
    k.add_argument("ratings_b", type=Path)
    j = sub.add_parser("judge-agreement")
    j.add_argument("out_dir", type=Path)
    j.add_argument("adjudicated", type=Path)
    j.add_argument("screening_dirs", type=Path, nargs="+")
    args = ap.parse_args()
    return {"sample": cmd_sample, "kappa": cmd_kappa,
            "judge-agreement": cmd_judge_agreement}[args.cmd](args)


if __name__ == "__main__":
    raise SystemExit(main())
