"""Compare two g3-reports (pre/post a protocol revision) at cluster and
instance level, so every flip is listed for adjudication.

Usage:
  python scripts/g3_diff.py <pre.json> <post.json> [--out diff.json]
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path


def diff(pre: dict, post: dict) -> dict:
    def head(r):
        return {"survivors": r["n_survivors"], "valid_instances": r["n_valid_instances"],
                "strict": r["n_strict_survivors"]}
    out = {"pre": head(pre), "post": head(post), "cluster_flips": [], "instance_flips": []}
    for cid in sorted(set(pre["clusters"]) | set(post["clusters"])):
        a, b = pre["clusters"].get(cid), post["clusters"].get(cid)
        if a is None or b is None:
            out["cluster_flips"].append({"cluster": cid, "note": "present on one side only"})
            continue
        if a["survive"] != b["survive"]:
            out["cluster_flips"].append({
                "cluster": cid, "pre": a["survive"], "post": b["survive"],
                "direction": "RECOVERED" if b["survive"] else "DROPPED"})
        for pid in sorted(set(a["instances"]) | set(b["instances"])):
            ia, ib = a["instances"].get(pid), b["instances"].get(pid)
            if not ia or not ib:
                continue
            for cond in ("ceiling", "twin_ceiling", "floor", "valid"):
                if ia.get(cond) != ib.get(cond):
                    out["instance_flips"].append({"instance": pid, "field": cond,
                                                  "pre": ia.get(cond), "post": ib.get(cond)})
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("pre", type=Path)
    ap.add_argument("post", type=Path)
    ap.add_argument("--out", type=Path, default=None)
    args = ap.parse_args()
    d = diff(json.loads(args.pre.read_text()), json.loads(args.post.read_text()))
    print(f"pre  {d['pre']}\npost {d['post']}")
    for f in d["cluster_flips"]:
        print("  CLUSTER", f)
    drops = [f for f in d["instance_flips"] if f["field"] in ("ceiling", "twin_ceiling")
             and f["post"] is not None and f["pre"] is not None and f["post"] < f["pre"]]
    print(f"{len(d['instance_flips'])} instance-field flips; "
          f"{len(drops)} ceiling/twin DECREASES to adjudicate")
    for f in drops:
        print("  DOWN", f)
    if args.out:
        args.out.write_text(json.dumps(d, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
