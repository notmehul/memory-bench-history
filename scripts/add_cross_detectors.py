"""Generate cross-side absence detectors (probe-spec v0.4.2).

For every counterfactual-paired probe instance, append two mechanically
generated `fact_absent` pattern assertions:

  asrt-cs   (base side)  — fires when the CF side's distinctive values
                           appear in a base-side deliverable
  casrt-cs  (cf side)    — fires when the BASE side's distinctive values
                           appear in a cf-side deliverable

Generated, never authored: each pattern must match every full-text surface
variant of the side it hunts, no variant of the side it guards, and no
co-valid canonical of either org (spec v0.4.2); branches must carry
invariant anchors — bare 1-2 digit numerals are a hard error by
construction (spec v0.4.4, enforced in membench.probes.side_value_anchors).
Sides the pattern layer cannot cover (v0.4 R1 duration ban, R2, R5 —
the majority of sides) are SKIPPED and listed in the report — no silent
caps, no weakened detectors. A semantic fallback (`asrt-css`/`casrt-css`,
one fixed template hunting the other side's delta canonicals) was built
and measured on 2026-08-15 and REJECTED: 19 honest seed-1/2 instances
flipped, 0 true positives (`datasets/dev/screening/exploit-audit/
css-flip-adjudication-2026-08-15.json`). It stays available behind
`--semantic` for reproduction only; enumeration closure lives in the
judge rubric's commitment clause (probe-spec v0.4.3 S1').

Idempotent: existing *-cs assertions are stripped before regeneration.

Usage:
  python scripts/add_cross_detectors.py apply <org_dir> <twin_dir> [--report out.json]
  python scripts/add_cross_detectors.py apply-all [--report out.json]
  python scripts/add_cross_detectors.py apply-all --semantic   # rejected S1, reproduction only
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from membench.probes import build_side_patterns  # noqa: E402

DEV = Path(__file__).resolve().parents[1] / "datasets" / "dev"
ORGS = [f"org-0000{n}" for n in range(1, 6)]


def _strip_cs(assertions: list[dict]) -> list[dict]:
    return [a for a in assertions
            if not (a["id"].endswith("-cs") or a["id"].endswith("-css"))]


SEMANTIC_TEMPLATE = (
    "The deliverable does not present {what} as currently in effect. "
    "Mentioning it only as past, replaced, hypothetical, or rejected does "
    "not count as presenting it."
)


def semantic_detector(asrt_id: str, hunted: list[str], weight: float) -> dict:
    """v0.4.3 semantic cross-side detector: generated from a fixed template
    for a side the pattern layer could not cover. Hunts the OTHER side's
    delta-fact canonicals verbatim (never co-valid siblings); the
    past/replaced/rejected carve-out is the semantic form of R4."""
    if len(hunted) == 1:
        what = f'the statement "{hunted[0]}"'
    else:
        what = "any of the statements " + "; ".join(
            f'({i}) "{h}"' for i, h in enumerate(hunted, 1))
    return {"id": asrt_id, "kind": "fact_absent", "checker": "semantic",
            "criterion": SEMANTIC_TEMPLATE.format(what=what), "weight": weight}


def _absence_weight(assertions: list[dict]) -> float:
    for a in assertions:
        if a["kind"] == "fact_absent":
            return a["weight"]
    return 1.0


def cross_foreign(probe: dict, org: dict, twin: dict) -> list[tuple[str, str]]:
    """Co-valid texts a detector must never key on (spec v0.4.2): the
    same-topic NON-distractor facts of both orgs — the nested constraints
    an honest on-scope output may legitimately restate. Distractors and
    off-topic facts are excluded: restating those is exactly the
    enumeration behavior the detectors exist to punish."""
    deltas = set(probe["counterfactual_probe"].get("ledger_deltas") or [])
    by_id = {f["fact_id"]: f for f in org["facts"]}
    topics = {by_id[t].get("topic") for t in probe["targets"] if t in by_id}
    out = []
    for tag, o in (("base", org), ("twin", twin)):
        for f in o["facts"]:
            if (f["fact_id"] not in deltas and not f.get("distractor")
                    and f.get("topic") in topics):
                out.append((f"{tag}:{f['fact_id']}", f["canonical"]))
    return out


def add_detectors(probe: dict, base_canon: dict[str, str],
                  twin_canon: dict[str, str],
                  foreign: list[tuple[str, str]],
                  semantic: bool = False) -> dict:
    """Return {added: [...], skipped: [...], notes: [...]} and mutate probe."""
    out = {"added": [], "skipped": [], "notes": []}
    probe["assertions"] = _strip_cs(probe["assertions"])
    cf = probe["counterfactual_probe"]
    key = "cf_assertions" if "cf_assertions" in cf else "assertions"
    cf[key] = _strip_cs(cf[key])

    deltas = cf.get("ledger_deltas") or []
    base_pat, cf_pat, notes = build_side_patterns(
        base_canon, twin_canon, deltas, foreign)
    out["notes"] = notes

    hunted_cf = [twin_canon[d] for d in deltas if d in twin_canon]
    hunted_base = [base_canon[d] for d in deltas if d in base_canon]
    # asrt-cs guards the BASE side by hunting CF-side values.
    if cf_pat is not None:
        probe["assertions"].append({
            "id": "asrt-cs", "kind": "fact_absent", "checker": "pattern",
            "criterion": cf_pat,
            "weight": _absence_weight(probe["assertions"]),
        })
        out["added"].append("asrt-cs")
    elif semantic and hunted_cf:
        probe["assertions"].append(semantic_detector(
            "asrt-css", hunted_cf, _absence_weight(probe["assertions"])))
        out["added"].append("asrt-css")
    else:
        out["skipped"].append(
            {"side": "asrt-cs", "reason": "cf-side values not coverable"})
    # casrt-cs guards the CF side by hunting BASE-side values.
    if base_pat is not None:
        cf[key].append({
            "id": "casrt-cs", "kind": "fact_absent", "checker": "pattern",
            "criterion": base_pat,
            "weight": _absence_weight(cf[key]),
        })
        out["added"].append("casrt-cs")
    elif semantic and hunted_base:
        cf[key].append(semantic_detector(
            "casrt-css", hunted_base, _absence_weight(cf[key])))
        out["added"].append("casrt-css")
    else:
        out["skipped"].append(
            {"side": "casrt-cs", "reason": "base-side values not coverable"})
    return out


_WORD_NUM_SET = frozenset(
    ["one", "two", "three", "four", "five", "six", "seven", "eight",
     "nine", "ten", "eleven", "twelve", "thirteen", "fourteen", "fifteen",
     "sixteen", "seventeen", "eighteen", "nineteen", "twenty", "thirty",
     "sixty", "ninety"]
)


def _top_level_branches(inner: str) -> list[str]:
    out, depth, cur = [], 0, []
    for ch in inner:
        if ch == "(":
            depth += 1
        elif ch == ")":
            depth -= 1
        if ch == "|" and depth == 0:
            out.append("".join(cur))
            cur = []
        else:
            cur.append(ch)
    out.append("".join(cur))
    return out


def _validate_branches(probe: dict) -> None:
    """R5 hard errors (2026-08-07): a shipped -cs pattern may contain no
    unit-less digit-only branch (any length — the `(?:000|two)` fragment
    bug class) and no unit-less bare number-word branch. Branches with a
    unit tail (`[\\s-]+<stem>`) are exempt."""
    sides = [probe["assertions"]]
    cf = probe["counterfactual_probe"]
    sides.append(cf["cf_assertions" if "cf_assertions" in cf else "assertions"])
    for assertions in sides:
        for a in assertions:
            if not a["id"].endswith("-cs"):
                continue  # -css semantic detectors carry no regex
            m = re.fullmatch(
                r"\(\?<!\[[^]]*]\)\(\?:(.*)\)\(\?!\[[^]]*]\)", a["criterion"])
            inner = m.group(1) if m else a["criterion"]
            for branch in _top_level_branches(inner):
                if "[\\s-]" in branch:
                    continue  # unit-anchored compound: exempt
                alts = [x.strip("(?:)") for x in re.split(r"[|]", branch)]
                alts = [x for x in alts if x]
                if alts and all(re.fullmatch(r"\d+", x) for x in alts):
                    raise SystemExit(
                        f"{probe['probe_id']} {a['id']}: unit-less "
                        f"digit-only branch '{branch}' (R5)")
                if alts and all(x.lower() in _WORD_NUM_SET or
                                re.fullmatch(r"\d+", x) for x in alts) \
                        and any(x.lower() in _WORD_NUM_SET for x in alts):
                    raise SystemExit(
                        f"{probe['probe_id']} {a['id']}: unit-less bare "
                        f"number-word branch '{branch}' (R5)")


def apply_org(org_dir: Path, twin_dir: Path, semantic: bool = False) -> dict:
    org = json.loads((org_dir / "org.json").read_text())
    twin = json.loads((twin_dir / "org.json").read_text())
    base_canon = {f["fact_id"]: f["canonical"] for f in org["facts"]}
    twin_canon = {f["fact_id"]: f["canonical"] for f in twin["facts"]}

    path = org_dir / "probes.jsonl"
    rows, report = [], {"org": org_dir.name, "probes": 0, "added": 0,
                        "skips": [], "prune_notes": 0}
    for line in path.read_text().splitlines():
        p = json.loads(line)
        if p.get("counterfactual_probe"):
            if p.get("kind") == "historical":
                # R3 (2026-08-07): historical probes narrate multiple
                # epochs by design — no cross-side detectors. Strip any
                # previously generated ones (idempotency).
                p["assertions"] = _strip_cs(p["assertions"])
                cf = p["counterfactual_probe"]
                key = "cf_assertions" if "cf_assertions" in cf else "assertions"
                cf[key] = _strip_cs(cf[key])
                report["probes"] += 1
                report["skips"].append({
                    "probe_id": p["probe_id"], "side": "both",
                    "reason": "historical exemption (v0.4 R3)"})
            else:
                r = add_detectors(p, base_canon, twin_canon,
                                  cross_foreign(p, org, twin),
                                  semantic=semantic)
                _validate_branches(p)
                report["probes"] += 1
                report["added"] += len(r["added"])
                report["prune_notes"] += sum(
                    1 for n in r["notes"] if "pruned" in n)
                for s in r["skipped"]:
                    report["skips"].append({"probe_id": p["probe_id"], **s})
        rows.append(json.dumps(p))
    path.write_text("\n".join(rows) + "\n")
    return report


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    one = sub.add_parser("apply")
    one.add_argument("org_dir", type=Path)
    one.add_argument("twin_dir", type=Path)
    one.add_argument("--report", type=Path, default=None)
    alln = sub.add_parser("apply-all")
    alln.add_argument("--report", type=Path, default=None)
    for sp in (one, alln):
        sp.add_argument("--semantic", action="store_true",
                        help="add the REJECTED -css semantic fallback (reproduction only)")
    args = ap.parse_args(argv)

    sem = args.semantic
    if args.cmd == "apply":
        reports = [apply_org(args.org_dir, args.twin_dir, semantic=sem)]
    else:
        reports = [apply_org(DEV / o, DEV / f"{o}-twin", semantic=sem)
                   for o in ORGS]
    for r in reports:
        print(f"{r['org']}: {r['probes']} paired probes, {r['added']} "
              f"detectors added, {len(r['skips'])} side-skips, "
              f"{r['prune_notes']} branches pruned")
        for s in r["skips"]:
            print(f"  SKIP {s['probe_id']} {s['side']}: {s['reason']}")
    if args.report:
        args.report.write_text(json.dumps(reports, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())
