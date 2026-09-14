"""Track B: corpus-scale verdict re-analysis (decision-log 2026-09-14).

Joins every committed rubric-v2 criterion verdict to the `kind` of the
assertion it scored, and reports the judge's positive rate per kind, per
source dir and pooled. Descriptive only: there are no human labels outside
the 150-pair calibration packet, so this measures the judge's *mechanism*
(a degenerate pass mode on absence criteria), never its accuracy. It is not
an agreement measure, a validation, or a gate.

Read-only on datasets/dev/. Writes one file:
datasets/methods/corpus-kind-rates/report.json.

Usage:
  python scripts/methods_verdict_kinds.py [--out <path>]
"""

from __future__ import annotations

import argparse
import json
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

# The five committed (judgements.jsonl, runs.jsonl) pairs carrying rubric-v2
# verdicts: four screening seeds plus the pilot floor run.
SOURCES = [
    "datasets/dev/screening/org-00001",
    "datasets/dev/screening/org-00002",
    "datasets/dev/screening/org-00003",
    "datasets/dev/screening/org-00004",
    "datasets/dev/pilot/nomemory/seed-1/score-k1",
]

OUT = ROOT / "datasets" / "methods" / "corpus-kind-rates" / "report.json"


def _read_done(path: Path) -> dict[str, dict]:
    """Last-wins dedup by run_id — the convention in screen_probes.py:263,
    which is how judge-import's appended re-judgements are resolved."""
    done = {}
    if path.exists():
        for line in path.read_text().splitlines():
            r = json.loads(line)
            done[r["run_id"]] = r
    return done


def _all_assertions(row: dict) -> list[dict]:
    """Mirror of screen_probes.py:310 — a run's own assertions, the floor's
    cf side, and (S6) the cross side for ceiling/twin rows."""
    return (row["assertions"] + (row.get("cf_assertions") or [])
            + (row.get("cross_assertions") or []))


def _blank() -> dict:
    return {"n": 0, "n_true": 0}


def _rate(d: dict) -> dict:
    return {"n": d["n"], "n_true": d["n_true"],
            "positive_rate": round(d["n_true"] / d["n"], 6) if d["n"] else None}


def analyze_dir(work_dir: Path) -> dict:
    """Join one dir's verdicts to their assertion kinds. Raises on any
    verdict that has no matching assertion — the join must be lossless."""
    judgements = _read_done(work_dir / "judgements.jsonl")
    rows = {r["run_id"]: r for r in
            (json.loads(x) for x in
             (work_dir / "runs.jsonl").read_text().splitlines())}

    by_kind: dict[str, dict] = defaultdict(_blank)
    absent_by_checker: dict[str, dict] = defaultdict(_blank)
    judges: dict[str, int] = defaultdict(int)
    unmatched: list[dict] = []
    n_verdicts = 0

    for run_id, jrow in sorted(judgements.items()):
        row = rows.get(run_id)
        index = {a["id"]: a for a in _all_assertions(row)} if row else {}
        for assertion_id, verdict in (jrow.get("verdicts") or {}).items():
            n_verdicts += 1
            judges[jrow.get("judge")] += 1
            a = index.get(assertion_id)
            if a is None:
                unmatched.append({"run_id": run_id, "assertion_id": assertion_id,
                                  "reason": "no run row" if row is None
                                            else "no assertion with that id"})
                continue
            bucket = by_kind[a["kind"]]
            bucket["n"] += 1
            bucket["n_true"] += bool(verdict)
            if a["kind"] == "fact_absent":
                c = absent_by_checker[a["checker"]]
                c["n"] += 1
                c["n_true"] += bool(verdict)

    if unmatched:
        raise SystemExit(
            f"UNMATCHED JOIN in {work_dir}: {len(unmatched)} of {n_verdicts} "
            f"verdicts have no assertion. Examples: "
            f"{json.dumps(unmatched[:5])}")

    return {
        "dir": str(work_dir.relative_to(ROOT) if work_dir.is_relative_to(ROOT)
                   else work_dir),
        "n_verdicts": n_verdicts,
        "n_judged_runs": len(judgements),
        "judges": dict(sorted(judges.items())),
        "by_kind": {k: _rate(v) for k, v in sorted(by_kind.items())},
        "fact_absent_by_checker": {k: _rate(v) for k, v
                                   in sorted(absent_by_checker.items())},
        "unmatched": 0,
    }


def analyze(sources: list[str] | None = None) -> dict:
    per_dir = [analyze_dir(ROOT / s) for s in (sources or SOURCES)]

    pooled_kind: dict[str, dict] = defaultdict(_blank)
    pooled_checker: dict[str, dict] = defaultdict(_blank)
    pooled_judges: dict[str, int] = defaultdict(int)
    total = 0
    for d in per_dir:
        total += d["n_verdicts"]
        for judge, n in d["judges"].items():
            pooled_judges[judge] += n
        for kind, s in d["by_kind"].items():
            pooled_kind[kind]["n"] += s["n"]
            pooled_kind[kind]["n_true"] += s["n_true"]
        for checker, s in d["fact_absent_by_checker"].items():
            pooled_checker[checker]["n"] += s["n"]
            pooled_checker[checker]["n_true"] += s["n_true"]

    expected_judge = "claude-sonnet-5-blinded-v2"
    off_tag = {j: n for j, n in pooled_judges.items() if j != expected_judge}

    return {
        "generated_by": "scripts/methods_verdict_kinds.py",
        "prespecification": "docs/decision-log.md 2026-09-14 Track B carve-out",
        "note": ("Descriptive. Measures the judge's positive rate per criterion "
                 "kind, not agreement with any reference standard."),
        "n_verdicts_total": total,
        "unmatched_total": 0,
        "judges": dict(sorted(pooled_judges.items())),
        "off_tag_verdicts": off_tag,
        "per_dir": per_dir,
        "pooled": {
            "by_kind": {k: _rate(v) for k, v in sorted(pooled_kind.items())},
            "fact_absent_by_checker": {k: _rate(v) for k, v
                                       in sorted(pooled_checker.items())},
        },
    }


def render(report: dict) -> str:
    kinds = sorted(report["pooled"]["by_kind"])
    out = ["corpus-scale verdict re-analysis (descriptive; not an agreement measure)",
           "",
           f"{'source':<46} {'n':>6} " +
           " ".join(f"{k:>26}" for k in kinds),
           "-" * (54 + 27 * len(kinds))]
    for d in report["per_dir"] + [{"dir": "POOLED", "n_verdicts":
                                   report["n_verdicts_total"],
                                   "by_kind": report["pooled"]["by_kind"]}]:
        cells = []
        for k in kinds:
            s = d["by_kind"].get(k)
            cells.append(f"{'-':>26}" if not s else
                         f"{s['n_true']:>5}/{s['n']:<5} "
                         f"{s['positive_rate'] * 100:>6.1f}%      ")
        out.append(f"{d['dir']:<46} {d['n_verdicts']:>6} " + " ".join(cells))

    out += ["", "fact_absent by checker (pooled):"]
    for checker, s in report["pooled"]["fact_absent_by_checker"].items():
        out.append(f"  {checker:<12} {s['n_true']:>5}/{s['n']:<5} "
                   f"{s['positive_rate'] * 100:>6.1f}%")

    out += ["", f"judge tags: {report['judges']}"]
    if report["off_tag_verdicts"]:
        out.append(f"  WARNING off-tag verdicts: {report['off_tag_verdicts']}")
    out += [f"unmatched verdicts: {report['unmatched_total']}", ""]
    return "\n".join(out)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", type=Path, default=OUT)
    args = ap.parse_args(argv)
    report = analyze()
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, indent=1) + "\n")
    print(render(report))
    print(f"-> {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
