"""Cross-seed G3 summary (A5): per-seed gates plus per-archetype valid
instance counts against the pinned n>=30 INSTANCES rule (dataset-plan,
2026-07-25 gate-unit pin).

Reads datasets/dev/org-0000N/g3-report.json (whichever exist) and the
matching probes.jsonl for archetype ids.

Usage:
  python scripts/g3_summary.py [--out docs/g3-summary.md]
"""

from __future__ import annotations

import argparse
import json
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DEV = ROOT / "datasets" / "dev"
CLUSTER_GATE = 45
INSTANCE_GATE = 135
ARCHETYPE_N = 30


def load() -> list[dict]:
    seeds = []
    for n in range(1, 6):
        org = DEV / f"org-0000{n}"
        rep = org / "g3-report.json"
        if not rep.exists():
            continue
        r = json.loads(rep.read_text())
        arche = {}
        for line in (org / "probes.jsonl").read_text().splitlines():
            p = json.loads(line)
            arche[p["probe_id"][:6]] = p["archetype_instance"].split("-")[0]
        seeds.append({"seed": n, "report": r, "archetype": arche})
    return seeds


def summarize(seeds: list[dict]) -> dict:
    per_seed, per_arch = [], defaultdict(lambda: defaultdict(int))
    for s in seeds:
        r = s["report"]
        row = {"seed": s["seed"], "survivors": r["n_survivors"],
               "valid_instances": r["n_valid_instances"],
               "strict": r["n_strict_survivors"],
               "cluster_gate": "PASS" if r["n_survivors"] >= CLUSTER_GATE else "FAIL",
               "instance_gate": "PASS" if r["n_valid_instances"] >= INSTANCE_GATE else "FAIL"}
        per_seed.append(row)
        for cid, c in r["clusters"].items():
            if not c["survive"]:
                continue
            a = s["archetype"].get(cid, "?")
            per_arch[a][s["seed"]] += sum(1 for i in c["instances"].values() if i["valid"])
    arch_rows = []
    for a in sorted(per_arch):
        total = sum(per_arch[a].values())
        arch_rows.append({"archetype": a, "per_seed": dict(per_arch[a]),
                          "total_valid_instances": total,
                          "n30": "PASS" if total >= ARCHETYPE_N else "FAIL"})
    return {"seeds": per_seed, "archetypes": arch_rows,
            "n_seeds_screened": len(seeds)}


def render(summary: dict) -> str:
    out = ["# G3 summary across screened seeds", "",
           f"Seeds screened: {summary['n_seeds_screened']} of 5.", "",
           "| seed | survivors | cluster gate (>=45) | valid instances | "
           "instance gate (>=135) | strict |",
           "|---|---|---|---|---|---|"]
    for r in summary["seeds"]:
        out.append(f"| {r['seed']} | {r['survivors']}/54 | {r['cluster_gate']} | "
                   f"{r['valid_instances']} | {r['instance_gate']} | {r['strict']} |")
    out += ["", "| archetype | valid instances (total) | per seed | n>=30 |",
            "|---|---|---|---|"]
    for a in summary["archetypes"]:
        per = ", ".join(f"s{k}:{v}" for k, v in sorted(a["per_seed"].items()))
        out.append(f"| {a['archetype']} | {a['total_valid_instances']} | {per} | {a['n30']} |")
    out.append("")
    return "\n".join(out)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", type=Path, default=None)
    args = ap.parse_args()
    summary = summarize(load())
    text = render(summary)
    print(text)
    if args.out:
        args.out.write_text(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
