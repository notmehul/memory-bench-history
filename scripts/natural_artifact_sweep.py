"""Probe-spec v0.4 rule 3 (natural-artifact rule) — uniform sweep.

Operational form (v0.4.3, 2026-08-15): an applied-content semantic
criterion (`fact_applied`, `scope_correct`, `constraint_followed`) is a
**pure retraction** iff its only demanded content is that the other side's
value / arrangement does not hold, no longer holds, or never held — adding
no independent value of its own ("states there is no Monday 2pm slot",
"says X never ran", "no longer priced at $49"). Every pure-retraction
criterion is rewritten to OBSERVABLE ABSENCE of the base-side value
("does not present Monday 2pm as an active slot"). The rewrite is
monotonic — an explicit denial already implies observable absence, so no
output that passed the original can fail the rewrite; it only stops
punishing the natural artifact, which omits a retracted value rather than
narrating its retraction. `kind=historical` probes are exempt (narrating
the past is the task).

Classification is done uniformly over EVERY non-historical applied
criterion in all orgs by the content model (codex, the authoring family —
never the judge family), then audited by hand before `apply`. Task text is
never touched, so cached worker outputs stay valid; only the affected
criteria are re-judged (blinded).

Usage:
  python scripts/natural_artifact_sweep.py export  <out_dir>            # items per org
  python scripts/natural_artifact_sweep.py classify <out_dir> [--jobs 4] # codex
  python scripts/natural_artifact_sweep.py review  <out_dir>            # print for audit
  python scripts/natural_artifact_sweep.py apply   <out_dir> [--dry-run] # patch probes.jsonl
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from membench.codex_bin import codex_bin  # noqa: E402

ORGS = [ROOT / "datasets" / "dev" / f"org-0000{i}" for i in range(1, 6)]
APPLIED = {"fact_applied", "scope_correct", "constraint_followed"}
MODEL = ("gpt-5.4", "medium")
TIMEOUT = 900
CHUNK = 20

RUBRIC = """You are auditing grading criteria for a benchmark of AI memory
systems. Each item is one criterion that a judge applies to a work
artifact (a note, blurb, checklist, ...) produced for the given task. The
criterion belongs to one SIDE of a paired probe: the BASE side (the org's
actual fact) or the COUNTERFACTUAL side (a twin org where that fact is
replaced by its counterfactual). Both facts are shown.

Classify each criterion into exactly one class:

  "positive"        — the criterion demands some positive content: a value,
                      arrangement, rule, threshold, owner, cadence, ordering,
                      framing, or scope. Contrast phrasing ("X rather than Y",
                      "X, not Y", "X; it does not say Y") is still positive
                      when X is an independent value. A negative-valued rule
                      that is itself the fact ("deploys are frozen Friday
                      3pm–Monday 9am", "no design doc needed under 50 lines
                      when that IS the stated policy") is positive.
  "pure_retraction" — the criterion's ONLY demanded content is that the
                      other side's value/arrangement does not hold, no
                      longer holds, never held, was removed, discontinued,
                      or is not current — with no independent replacement
                      value. Typical shapes: "states there is no X",
                      "says X never ran", "makes clear X is no longer
                      current", "says X does not require Y" where Y is the
                      base rule and nothing replaces it, "not capped" where
                      the base is a cap and nothing else is asserted.
                      Test: strip every negation of the other side's value
                      from the criterion — if nothing checkable is left, it
                      is a pure retraction.

For every "pure_retraction" item, also write a REWRITE: the observable-
absence form. Rules for the rewrite:
  - Same artifact noun and opening as the original ("The blurb ...").
  - Shape: "<The artifact> does not present/list/state/require <the other
    side's value or arrangement> as <current / active / the rule / the
    standard / part of the process>." Pick the natural verb.
  - Name the value being retracted concretely (day, time, price, cadence,
    threshold, approver) so a judge can check it.
  - Never require the artifact to SAY anything — no "states that", "makes
    clear", "explains", "notes that ... no longer", no reasons/history.
  - Do not introduce any value from the counterfactual side that is not
    already in the original criterion.
  - One sentence, plain English.

Return a JSON array, one object per item in the same order:
  {"item_id": "...", "class": "positive"|"pure_retraction",
   "reason": "<one short clause>", "rewrite": "<sentence>" | null}
"""


def _facts(org_dir: Path) -> dict[str, dict]:
    org = json.loads((org_dir / "org.json").read_text())
    return {f["fact_id"]: f for f in org["facts"]}


def _iter_items(org_dir: Path):
    facts = _facts(org_dir)
    seen: dict[tuple, dict] = {}
    for line in (org_dir / "probes.jsonl").read_text().splitlines():
        p = json.loads(line)
        if p.get("kind") == "historical":
            continue
        cf = p.get("counterfactual_probe") or {}
        for side, asrts in (("base", p["assertions"]),
                            ("counterfactual", cf.get("assertions", []))):
            for a in asrts:
                if a.get("checker") != "semantic" or a.get("kind") not in APPLIED:
                    continue
                key = (p["probe_id"][:6], side, a["criterion"])
                if key in seen:
                    seen[key]["instances"].append({"probe_id": p["probe_id"],
                                                   "assertion_id": a["id"]})
                    continue
                f = facts.get(a.get("fact_id"), {})
                seen[key] = {
                    "item_id": f"{org_dir.name}:{p['probe_id'][:6]}:{side}:{a['id']}",
                    "org": org_dir.name,
                    "cluster_id": p["probe_id"][:6],
                    "side": side,
                    "kind": a["kind"],
                    "criterion": a["criterion"],
                    "task": p["task"],
                    "probe_kind": p.get("kind"),
                    "fact_id": a.get("fact_id"),
                    "base_fact": f.get("canonical"),
                    "counterfactual_fact": (f.get("counterfactual") or {}).get("canonical"),
                    "instances": [{"probe_id": p["probe_id"], "assertion_id": a["id"]}],
                }
    return list(seen.values())


def cmd_export(args) -> int:
    args.out_dir.mkdir(parents=True, exist_ok=True)
    total = 0
    for org_dir in ORGS:
        items = _iter_items(org_dir)
        (args.out_dir / f"{org_dir.name}.items.json").write_text(
            json.dumps(items, indent=1))
        total += len(items)
        print(f"{org_dir.name}: {len(items)} applied criteria")
    print(f"total {total}")
    return 0


def _classify_chunk(chunk: list[dict], work: Path) -> list[dict]:
    work.mkdir(parents=True, exist_ok=True)
    slim = [{k: it[k] for k in ("item_id", "side", "kind", "criterion", "task",
                                "base_fact", "counterfactual_fact")}
            for it in chunk]
    prompt = (RUBRIC + "\n\nItems:\n" + json.dumps(slim, indent=1)
              + "\n\nWrite the JSON array to a file named classification.json "
                "in the current directory. No other output.")
    out = work / "classification.json"
    for _ in range(2):
        try:
            subprocess.run(
                [codex_bin(check=False), "exec", "-C", str(work), "-s",
                 "workspace-write", "--skip-git-repo-check", "-m", MODEL[0],
                 "-c", f"model_reasoning_effort={MODEL[1]}", "-"],
                input=prompt, text=True, capture_output=True, timeout=TIMEOUT)
        except subprocess.TimeoutExpired:
            continue
        if out.exists():
            try:
                data = json.loads(out.read_text())
            except json.JSONDecodeError:
                out.unlink()
                continue
            got = {d.get("item_id"): d for d in data if isinstance(d, dict)}
            if all(it["item_id"] in got for it in chunk):
                return [got[it["item_id"]] for it in chunk]
            out.unlink()
    return []


def cmd_classify(args) -> int:
    jobs = []
    for org_dir in ORGS:
        items = json.loads((args.out_dir / f"{org_dir.name}.items.json").read_text())
        done_path = args.out_dir / f"{org_dir.name}.classification.json"
        done = {}
        if done_path.exists():
            done = {d["item_id"]: d for d in json.loads(done_path.read_text())}
        todo = [it for it in items if it["item_id"] not in done]
        for i in range(0, len(todo), CHUNK):
            jobs.append((org_dir.name, todo[i:i + CHUNK], i // CHUNK))
    print(f"{len(jobs)} chunks to classify")
    results: dict[str, list[dict]] = {}
    with ThreadPoolExecutor(max_workers=args.jobs) as ex:
        futs = {ex.submit(_classify_chunk, chunk,
                          args.out_dir / "work" / f"{org}-{n}"): org
                for org, chunk, n in jobs}
        for fut in as_completed(futs):
            org = futs[fut]
            res = fut.result()
            if not res:
                print(f"  {org}: chunk FAILED (rerun classify to retry)")
            results.setdefault(org, []).extend(res)
    for org_dir in ORGS:
        done_path = args.out_dir / f"{org_dir.name}.classification.json"
        done = {}
        if done_path.exists():
            done = {d["item_id"]: d for d in json.loads(done_path.read_text())}
        for d in results.get(org_dir.name, []):
            done[d["item_id"]] = d
        done_path.write_text(json.dumps(list(done.values()), indent=1))
        n_ret = sum(1 for d in done.values() if d.get("class") == "pure_retraction")
        print(f"{org_dir.name}: {len(done)} classified, {n_ret} pure_retraction")
    return 0


def _load(out_dir: Path, org: str) -> tuple[list[dict], dict[str, dict]]:
    items = json.loads((out_dir / f"{org}.items.json").read_text())
    cls = {d["item_id"]: d
           for d in json.loads((out_dir / f"{org}.classification.json").read_text())}
    return items, cls


def cmd_review(args) -> int:
    for org_dir in ORGS:
        items, cls = _load(args.out_dir, org_dir.name)
        missing = [it["item_id"] for it in items if it["item_id"] not in cls]
        print(f"===== {org_dir.name}: {len(items)} items, {len(missing)} unclassified")
        for it in items:
            d = cls.get(it["item_id"])
            if not d or d.get("class") != "pure_retraction":
                continue
            print(f"- {it['item_id']} [{it['kind']}]")
            print(f"    task: {it['task'][:140]}")
            print(f"    fact(base): {it['base_fact']}")
            print(f"    fact(cf):   {it['counterfactual_fact']}")
            print(f"    WAS: {it['criterion']}")
            print(f"    NOW: {d.get('rewrite')}")
            print(f"    why: {d.get('reason')}")
    return 0


def cmd_apply(args) -> int:
    log = []
    for org_dir in ORGS:
        items, cls = _load(args.out_dir, org_dir.name)
        rewrites = {}
        for it in items:
            d = cls.get(it["item_id"])
            if not d or d.get("class") != "pure_retraction":
                continue
            rw = (d.get("rewrite") or "").strip()
            if not rw:
                print(f"  {it['item_id']}: pure_retraction without rewrite — SKIPPED")
                continue
            for inst in it["instances"]:
                rewrites[(inst["probe_id"], inst["assertion_id"])] = (
                    it["criterion"], rw, it["item_id"])
        path = org_dir / "probes.jsonl"
        lines = path.read_text().splitlines()
        out_lines = []
        n = 0
        for line in lines:
            p = json.loads(line)
            cf = p.get("counterfactual_probe") or {}
            for a in list(p["assertions"]) + list(cf.get("assertions", [])):
                key = (p["probe_id"], a["id"])
                if key in rewrites:
                    was, now, item_id = rewrites[key]
                    assert a["criterion"] == was, key
                    a["criterion"] = now
                    log.append({"org": org_dir.name, "probe_id": p["probe_id"],
                                "assertion_id": a["id"], "item_id": item_id,
                                "was": was, "now": now})
                    n += 1
            out_lines.append(json.dumps(p, ensure_ascii=False))
        print(f"{org_dir.name}: {n} assertions rewritten")
        if not args.dry_run:
            path.write_text("\n".join(out_lines) + "\n")
    (args.out_dir / "applied.json").write_text(json.dumps(log, indent=1))
    print(f"{len(log)} rewrites {'(dry run)' if args.dry_run else 'applied'} -> "
          f"{args.out_dir / 'applied.json'}")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    for name in ("export", "classify", "review", "apply"):
        s = sub.add_parser(name)
        s.add_argument("out_dir", type=Path)
        if name == "classify":
            s.add_argument("--jobs", type=int, default=4)
        if name == "apply":
            s.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()
    return {"export": cmd_export, "classify": cmd_classify,
            "review": cmd_review, "apply": cmd_apply}[args.cmd](args)


if __name__ == "__main__":
    raise SystemExit(main())
