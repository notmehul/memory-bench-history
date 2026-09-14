"""Track B judge panel: score panel judges against the frozen human anchor.

Prespecified in `docs/decision-log.md` §2026-09-14 (Track B carve-out) before
any panel verdict existed. Read-only on v1 canon: the human anchor
(`ratings-M.json`), the committed v1 judge verdicts, and every g3-report are
inputs here and are never written.

Two populations are reported, deliberately:

  sampled (n=150)  the calibration pairs that have a human label. Agreement
                   and kappa against the human anchor are computable here and
                   only here.
  exported (n=478) every semantic criterion on the 146 runs the packet spans.
                   No human labels, so this reports positive RATE per criterion
                   kind -- the degenerate-pass mechanism, not accuracy -- plus
                   judge-vs-judge agreement.

Usage:
  python scripts/methods_judge_panel.py [--out <dir>]
"""
from __future__ import annotations

import argparse
import json
import sys
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from calibration import _cohens_kappa, _last_wins, _read_jsonl  # noqa: E402

REPO = Path(__file__).resolve().parent.parent
CALIB = REPO / "datasets/dev/calibration"
SCREEN = REPO / "datasets/dev/screening"
PANEL = REPO / "datasets/methods/judge-panel"
V1_TAG = "claude-sonnet-5-blinded-v2 (committed v1)"


def _pool(row: dict) -> list[dict]:
    """Every semantic assertion judge-export would send for a run -- including
    the S6 cross side, which `calibration._semantic_pool` omits because the
    150-pair packet was drawn only from the base and counterfactual sides."""
    pool = (row["assertions"] + (row.get("cf_assertions") or [])
            + (row.get("cross_assertions") or []))
    return [a for a in pool if a["checker"] == "semantic"]


# Keys are (org, run_id, assertion_id). The org is load-bearing: probe and run
# ids repeat across orgs, so a key without it silently collapses org-00002's
# verdicts onto org-00001's. `calibration._pair_id` hashes the org for the same
# reason.

def _kind_map(orgs: set[str]) -> dict[tuple[str, str, str], dict]:
    """(org, run_id, assertion_id) -> {kind, checker}, from the frozen runs.jsonl."""
    out: dict[tuple[str, str, str], dict] = {}
    for org in orgs:
        for row in _read_jsonl(SCREEN / org / "runs.jsonl"):
            for a in _pool(row):
                out[(org, row["run_id"], a["id"])] = {
                    "kind": a["kind"], "checker": a["checker"]}
    return out


def _v1_verdicts(orgs: set[str]) -> dict[tuple[str, str, str], bool]:
    out: dict[tuple[str, str, str], bool] = {}
    for org in orgs:
        judged = _last_wins(_read_jsonl(SCREEN / org / "judgements.jsonl"))
        for run_id, rec in judged.items():
            for aid, v in rec["verdicts"].items():
                out[(org, run_id, aid)] = bool(v)
    return out


def _panel_verdicts(tag_dir: Path) -> dict[tuple[str, str, str], bool]:
    """De-blind one panel judge's verdicts to (org, run_id, assertion_id)."""
    out: dict[tuple[str, str, str], bool] = {}
    for org_dir in sorted(p for p in tag_dir.iterdir() if p.is_dir()):
        org = org_dir.name
        vpath, mpath = org_dir / "verdicts.json", org_dir / "pending-judge.map.json"
        if not vpath.is_file():
            raise SystemExit(f"missing verdicts: {vpath}")
        verdicts = json.loads(vpath.read_text())
        mapping = json.loads(mpath.read_text())
        unknown = set(verdicts) - set(mapping)
        if unknown:
            raise SystemExit(f"{tag_dir.name}: unmapped row ids {sorted(unknown)[:5]}")
        for blind, crits in verdicts.items():
            m = mapping[blind]
            keys = set(m["criteria"])
            if set(crits) != keys:
                raise SystemExit(
                    f"{tag_dir.name}/{org_dir.name}: row {blind} has criterion keys "
                    f"{sorted(set(crits))}, expected {sorted(keys)}")
            for key, val in crits.items():
                if not isinstance(val, bool):
                    raise SystemExit(f"{tag_dir.name}: non-boolean verdict at {blind}.{key}")
                out[(org, m["run_id"], m["criteria"][key])] = val
    return out


def _rate_block(pairs, verdicts, kinds) -> dict:
    """Positive rate per criterion kind over `pairs` (no human labels needed)."""
    by: dict[str, list[bool]] = defaultdict(list)
    for p in pairs:
        if p in verdicts:
            by[kinds[p]["kind"]].append(verdicts[p])
    block = {}
    for kind, vals in sorted(by.items()):
        block[kind] = {"n": len(vals), "n_true": sum(vals),
                       "positive_rate": round(sum(vals) / len(vals), 4)}
    allv = [v for vals in by.values() for v in vals]
    block["overall"] = {"n": len(allv), "n_true": sum(allv),
                        "positive_rate": round(sum(allv) / len(allv), 4) if allv else None}
    return block


def _agree_block(pairs, a, b, kinds) -> dict:
    """Raw agreement + Cohen's kappa between two verdict sources, per kind."""
    by: dict[str, list[tuple[bool, bool]]] = defaultdict(list)
    for p in pairs:
        if p in a and p in b:
            by[kinds[p]["kind"]].append((a[p], b[p]))
    block = {}
    for kind, rows in sorted(by.items()):
        po, k, deg = _cohens_kappa([x for x, _ in rows], [y for _, y in rows])
        block[kind] = {"n": len(rows), "agreement": round(po, 4),
                       "kappa": round(k, 4), "degenerate_marginals": deg}
    allr = [r for rows in by.values() for r in rows]
    po, k, deg = _cohens_kappa([x for x, _ in allr], [y for _, y in allr])
    block["overall"] = {"n": len(allr), "agreement": round(po, 4),
                        "kappa": round(k, 4), "degenerate_marginals": deg}
    return block


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", type=Path, default=PANEL)
    args = ap.parse_args()

    key = json.loads((CALIB / "packet-key.json").read_text())
    human_raw = json.loads((CALIB / "ratings-M.json").read_text())
    orgs = {v["org"] for v in key.values()}

    sampled = {pid: (v["org"], v["run_id"], v["assertion_id"]) for pid, v in key.items()}
    missing = sorted(set(sampled) - set(human_raw))
    if missing:
        raise SystemExit(f"human anchor missing {len(missing)} packet ids: {missing[:5]}")
    human = {sampled[pid]: bool(human_raw[pid]) for pid in sampled}
    sampled_pairs = sorted(human)

    kinds = _kind_map(orgs)
    unmatched = [p for p in sampled_pairs if p not in kinds]
    if unmatched:
        raise SystemExit(
            f"{len(unmatched)} sampled pairs have no assertion kind: {unmatched[:5]}")

    sources: dict[str, dict[tuple[str, str], bool]] = {V1_TAG: _v1_verdicts(orgs)}
    for d in sorted(p for p in PANEL.iterdir() if p.is_dir() and not p.name.startswith("_")):
        sources[d.name] = _panel_verdicts(d)

    # CONTROL. Recomputing the v1 judge against the same anchor must reproduce
    # the committed G4 result exactly. If it does not, this script is measuring
    # something other than what `calibration.py judge-agreement` measured and
    # every panel number below is untrustworthy. (An earlier revision keyed
    # verdicts without the org and silently collapsed cross-org id collisions;
    # this control is what caught it.)
    g4 = json.loads((CALIB / "judge-agreement.json").read_text())
    ctl = _agree_block(sampled_pairs, human, sources[V1_TAG], kinds)["overall"]
    want = (g4["n"], round(g4["raw_agreement"], 4), round(g4["kappa"], 4))
    got = (ctl["n"], ctl["agreement"], ctl["kappa"])
    if got != want:
        raise SystemExit(
            f"CONTROL FAILED: v1 judge vs anchor recomputes as n={got[0]} "
            f"agreement={got[1]} kappa={got[2]}, but the committed G4 result is "
            f"n={want[0]} agreement={want[1]} kappa={want[2]}. Refusing to report.")

    # Exported population: every criterion every panel judge actually scored.
    panel_only = [t for t in sources if t != V1_TAG]
    if not panel_only:
        raise SystemExit("no panel judge directories found")
    exported_pairs = sorted(set.intersection(*(set(sources[t]) for t in panel_only)))
    exported_pairs = [p for p in exported_pairs if p in kinds]

    report = {
        "prespecification": "docs/decision-log.md §2026-09-14 (Track B carve-out)",
        "anchor": "datasets/dev/calibration/ratings-M.json (frozen, unmodified)",
        "populations": {"sampled": len(sampled_pairs), "exported": len(exported_pairs)},
        "human_anchor_rates": _rate_block(sampled_pairs, human, kinds),
        "positive_rates_sampled": {},
        "positive_rates_exported": {},
        "vs_human_sampled": {},
        "vs_v1_committed": {},
    }
    for tag, v in sources.items():
        report["positive_rates_sampled"][tag] = _rate_block(sampled_pairs, v, kinds)
        report["positive_rates_exported"][tag] = _rate_block(exported_pairs, v, kinds)
        report["vs_human_sampled"][tag] = _agree_block(sampled_pairs, human, v, kinds)
        if tag != V1_TAG:
            report["vs_v1_committed"][tag] = _agree_block(
                exported_pairs, sources[V1_TAG], v, kinds)

    args.out.mkdir(parents=True, exist_ok=True)
    (args.out / "report.json").write_text(json.dumps(report, indent=1))

    kinds_seen = ["fact_absent", "fact_applied", "scope_correct", "overall"]
    print(f"\npositive rate by criterion kind, exported population "
          f"(n={len(exported_pairs)} criteria)")
    print(f"{'judge':<34} " + " ".join(f"{k:>15}" for k in kinds_seen))
    for tag in [V1_TAG] + sorted(panel_only):
        row = report["positive_rates_exported"][tag]
        cells = []
        for k in kinds_seen:
            cells.append(f"{row[k]['positive_rate']:>15.3f}" if k in row else f"{'-':>15}")
        print(f"{tag:<34} " + " ".join(cells))

    print(f"\nagreement vs the human anchor, sampled population (n={len(sampled_pairs)})")
    print(f"{'judge':<34} " + " ".join(f"{k:>15}" for k in kinds_seen))
    for tag in [V1_TAG] + sorted(panel_only):
        row = report["vs_human_sampled"][tag]
        cells = []
        for k in kinds_seen:
            cells.append(f"{row[k]['agreement']:.3f}/{row[k]['kappa']:>+.3f}".rjust(15)
                         if k in row else f"{'-':>15}")
        print(f"{tag:<34} " + " ".join(cells))
    print("  (cells are raw agreement / Cohen's kappa)")

    print(f"\nvs the committed v1 judge, exported population (n={len(exported_pairs)})")
    print(f"{'judge':<34} " + " ".join(f"{k:>15}" for k in kinds_seen))
    for tag in sorted(panel_only):
        row = report["vs_v1_committed"][tag]
        cells = []
        for k in kinds_seen:
            cells.append(f"{row[k]['agreement']:.3f}/{row[k]['kappa']:>+.3f}".rjust(15)
                         if k in row else f"{'-':>15}")
        print(f"{tag:<34} " + " ".join(cells))

    print(f"\n-> {args.out / 'report.json'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
