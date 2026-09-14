"""Phase 3 validity screening: floor/ceiling runs + gate G3 (probe-spec §3).

Every probe instance runs in `floor` (task only) and `ceiling` (task + the
relevant slice of B rendered canonically); instances with a counterfactual
side additionally run `twin_ceiling` against the twin org, scored with the
counterfactual assertions. No SUT is involved — this screens the probes
themselves.

Standing decisions (dataset-plan.md, amended 2026-07-22 after the seed-1
pilot rejected gpt-5.4-mini):
  fixed task model  = gpt-5.4 via codex, reasoning effort medium
  screening judge   = Claude family (semantic assertions only; != task
                      model, cross-provider; formal calibration in Phase 4).
                      Judging runs outside this script: `judge-export`
                      writes the pending (output, criteria) rows, the Claude
                      judge produces verdicts, `judge-import` validates and
                      merges them.

Pass rules (probe-spec v0.3, instance-level; floor rule v0.2 — both revised
on screening evidence before any SUT evaluation, see probe-spec.md changelog):
  instance ceiling-pass  <=> weighted assertion score == 1.0
  instance floor-fail    <=> weighted assertion score <= 0.5
  pair-level floor       <=> a floor output scoring 1.0 against BOTH the
                             base and counterfactual assertion sets (the
                             floor prompt is org-independent, so one output
                             serves both sides)
  instance valid         <=> ceiling pass AND twin_ceiling pass AND no
                             pair-level floor pass
  cluster survives G3    <=> >= 2/3 instances valid; only valid instances
                             ship. The strict all-instances rule is reported
                             alongside for comparison. Per-side floor passes
                             are reported as `guessability` (mean and
                             per-cluster) — pair crediting cancels them
                             structurally (risk register: generator bias).

Resumable: every completed run is appended to results.jsonl; re-running
`run` skips completed work.

Judge blinding: `judge-export` writes pending-judge.json under opaque row
and criterion ids — the judge sees only (output, criteria), never run ids,
conditions (floor/ceiling/twin), or base-vs-counterfactual side. The
translation table stays local in pending-judge.map.json and is applied by
`judge-import`. `--ids <file>` exports specific run_ids (one per line) for
blinded re-judging of already-judged rows. `--incremental` exports, per
row, only the criteria that lack a verdict, whose text changed since it
was judged (judgements carry `criteria_sha`), or that are listed in
`--force`; pair it with `judge-import --merge`. `report` refuses stale
verdicts (sha mismatch) so a criterion can never be re-authored without
being re-judged.

Usage:
  python scripts/screen_probes.py manifest <org_dir> <twin_dir> <work_dir>
  python scripts/screen_probes.py run <work_dir> [--jobs 8] [--limit N]
  python scripts/screen_probes.py judge-export <work_dir> [--ids <file>]
  python scripts/screen_probes.py judge-export <work_dir> --incremental [--force <file>]
  python scripts/screen_probes.py judge-import <work_dir> <verdicts.json> --judge <tag> \
      [--merge]
  python scripts/screen_probes.py report <work_dir> [--out <org_dir>/g3-report.json]
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
import sys
import tempfile
import threading
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from membench.belief import belief_hist, belief_state  # noqa: E402
from membench.codex_bin import pinned_codex  # noqa: E402
from membench.ledger import load_event_index, load_ledger  # noqa: E402
from membench.probes import (  # noqa: E402
    build_side_patterns,
    is_hedged,
    pattern_hits_unnegated,
)

TASK_MODEL = ("gpt-5.4", "medium")
JUDGE_MODEL = "claude"
RUN_TIMEOUT = 360
CEILING_PASS = 0.999
FLOOR_FAIL = 0.5

_FRAME_LINE = {
    "org_facing": "The artifact you produce is org-facing (visible to the whole company).",
    "team_internal": "The artifact you produce is internal to your team ({ref}).",
    "personal": "The artifact is for your own personal use.",
    "project": "The artifact belongs to the cross-team project ({ref}).",
    "external": "The artifact is client-facing (external).",
}


# ------------------------------------------------------------- manifest

def _fact_line(f: dict, historical: bool) -> str:
    scope = f["scope_ref"] or "org-wide"
    note = " (historical record — since superseded)" if historical else ""
    return f"- {f['canonical']} [{f['tier']} scope: {scope}; {f['capacity']}]{note}"


def _persona_line(org: dict, pid: str) -> str:
    p = next(x for x in org["entities"]["personas"] if x["id"] == pid)
    name = pid.split(":", 1)[1].capitalize()
    teams = ", ".join(t.split(":", 1)[1] for t in p["teams"]) or "exec staff"
    return f"You are {name}, {p['role']} ({teams}) at {org['org_id']}."


def _context_facts(org: dict, ledger, index, probe: dict) -> list[str]:
    """The ceiling slice: targets plus same-topic facts currently in B."""
    t = index.index_of(probe["inject_after_event"])
    pid = probe["principal"]
    b = belief_state(ledger, index, pid, t)
    hist = belief_hist(ledger, index, pid, t)
    by_id = {f["fact_id"]: f for f in org["facts"]}
    topics = {by_id[fid]["topic"] for fid in probe["targets"]}
    lines = {}
    for f in org["facts"]:
        if f["topic"] in topics and not f["distractor"] and f["fact_id"] in b:
            lines[f["fact_id"]] = _fact_line(f, historical=False)
    for fid in probe["targets"]:
        if fid not in lines:
            if fid not in hist:
                raise RuntimeError(f"{probe['probe_id']}: target {fid} in neither B nor B_hist")
            lines[fid] = _fact_line(by_id[fid], historical=True)
    return [lines[fid] for fid in sorted(lines)]


def _prompt(org: dict, probe: dict, context: list[str] | None) -> str:
    frame = probe["context_frame"]
    frame_line = _FRAME_LINE[frame["kind"]].format(ref=frame["ref"] or "")
    parts = [_persona_line(org, probe["principal"]), frame_line]
    if context:
        parts.append(
            "Authoritative context from the organization's records "
            "(current unless noted):\n" + "\n".join(context)
        )
    parts.append(f"Task: {probe['task']}")
    parts.append(
        "Write the deliverable to a file named output.md in the current "
        "directory. Output only the deliverable itself — no meta-commentary "
        "and no notes about missing information; make reasonable choices and "
        "produce your best version. Apply only what fits this artifact's "
        "audience and scope — do not enumerate practices that belong to "
        "other scopes, teams, or individuals. Where the task calls for "
        "thresholds, cadences, or figures, state them concretely."
    )
    return "\n\n".join(parts)


def cmd_manifest(args) -> int:
    org = json.loads((args.org_dir / "org.json").read_text())
    twin = json.loads((args.twin_dir / "org.json").read_text())
    probes = [
        json.loads(line)
        for line in (args.org_dir / "probes.jsonl").read_text().splitlines()
    ]
    ledger, index = load_ledger(org), load_event_index(org)
    t_ledger, t_index = load_ledger(twin), load_event_index(twin)

    base_canon = {f["fact_id"]: f["canonical"] for f in org["facts"]}
    twin_canon = {f["fact_id"]: f["canonical"] for f in twin["facts"]}

    rows = []
    for p in probes:
        base_asserts = p["assertions"]
        cf = p["counterfactual_probe"]
        # Commitment-rule patterns (spec v0.4.1): one per side, from the
        # probe's delta facts; co-valid canonicals of both orgs are the
        # foreign set so hedge detection never keys on nested constraints.
        # R3 (2026-08-07): historical probes are exempt — multi-epoch
        # narration is the task, so no hedge patterns are embedded.
        hedge_base = hedge_cf = None
        if cf and p.get("kind") != "historical":
            deltas = set(cf.get("ledger_deltas") or [])
            by_id = {f["fact_id"]: f for f in org["facts"]}
            topics = {by_id[t].get("topic") for t in p["targets"]
                      if t in by_id}
            foreign = [
                (f"{tag}:{f['fact_id']}", f["canonical"])
                for tag, o in (("base", org), ("twin", twin))
                for f in o["facts"]
                if (f["fact_id"] not in deltas and not f.get("distractor")
                    and f.get("topic") in topics)
            ]
            hedge_base, hedge_cf, _ = build_side_patterns(
                base_canon, twin_canon, sorted(deltas), foreign)
        rows.append({
            "run_id": f"{p['probe_id']}:floor",
            "probe_id": p["probe_id"], "cluster_id": p["cluster_id"],
            "condition": "floor",
            "prompt": _prompt(org, p, None),
            "assertions": base_asserts,
            # The floor prompt is identical on both orgs (no context), so the
            # same output is scored against both sides for pair-level floor.
            "cf_assertions": cf["assertions"] if cf else None,
            "hedge_base": hedge_base, "hedge_cf": hedge_cf,
        })
        rows.append({
            "run_id": f"{p['probe_id']}:ceiling",
            "probe_id": p["probe_id"], "cluster_id": p["cluster_id"],
            "condition": "ceiling",
            "prompt": _prompt(org, p, _context_facts(org, ledger, index, p)),
            "assertions": base_asserts,
            # S6 discrimination gate: the ceiling output is also scored
            # against the OTHER side's assertions (must fail there).
            "cross_assertions": cf["assertions"] if cf else None,
            "hedge_base": hedge_base, "hedge_cf": hedge_cf,
        })
        if cf:
            rows.append({
                "run_id": f"{p['probe_id']}:twin_ceiling",
                "probe_id": p["probe_id"], "cluster_id": p["cluster_id"],
                "condition": "twin_ceiling",
                "prompt": _prompt(twin, p, _context_facts(twin, t_ledger, t_index, p)),
                "assertions": p["counterfactual_probe"]["assertions"],
                "cross_assertions": base_asserts,
                "hedge_base": hedge_base, "hedge_cf": hedge_cf,
            })

    args.work_dir.mkdir(parents=True, exist_ok=True)
    with (args.work_dir / "runs.jsonl").open("w") as fh:
        for r in rows:
            fh.write(json.dumps(r) + "\n")
    print(f"{len(rows)} runs -> {args.work_dir / 'runs.jsonl'}")
    return 0


# ------------------------------------------------------------------ run

def _codex(prompt: str, model: str, effort: str, cwd: Path) -> None:
    subprocess.run(
        [pinned_codex(), "exec", "-C", str(cwd), "-s", "workspace-write",
         "--skip-git-repo-check",
         "-m", model, "-c", f"model_reasoning_effort={effort}", "-"],
        input=prompt, text=True, capture_output=True, timeout=RUN_TIMEOUT,
    )


def _do_run(row: dict) -> dict:
    last_err = "no output.md produced"
    for _ in range(2):
        with tempfile.TemporaryDirectory(prefix="mbrun-") as tmp:
            tmp_path = Path(tmp)
            try:
                _codex(row["prompt"], *TASK_MODEL, cwd=tmp_path)
            except subprocess.TimeoutExpired:
                last_err = "timeout"
                continue
            out = tmp_path / "output.md"
            if out.exists() and out.read_text().strip():
                return {"run_id": row["run_id"], "output": out.read_text().strip()}
    return {"run_id": row["run_id"], "output": None, "error": last_err}


def _read_done(path: Path) -> dict[str, dict]:
    done = {}
    if path.exists():
        for line in path.read_text().splitlines():
            r = json.loads(line)
            done[r["run_id"]] = r
    return done


def cmd_run(args) -> int:
    rows = [json.loads(x) for x in (args.work_dir / "runs.jsonl").read_text().splitlines()]
    res_path = args.work_dir / "results.jsonl"
    done = {rid for rid, r in _read_done(res_path).items() if r.get("output")}
    todo = [r for r in rows if r["run_id"] not in done]
    if args.limit:
        todo = todo[: args.limit]
    print(f"{len(done)} done, {len(todo)} to run", flush=True)
    lock = threading.Lock()
    n = 0
    with res_path.open("a") as fh, ThreadPoolExecutor(max_workers=args.jobs) as ex:
        futs = {ex.submit(_do_run, r): r for r in todo}
        for fut in as_completed(futs):
            res = fut.result()
            with lock:
                fh.write(json.dumps(res) + "\n")
                fh.flush()
                n += 1
                if n % 20 == 0:
                    print(f"  {n}/{len(todo)}", flush=True)
    failed = sum(1 for r in _read_done(res_path).values() if not r.get("output"))
    print(f"run complete; {failed} failed runs (rerun `run` to retry)")
    return 1 if failed else 0


# ---------------------------------------------------------------- judge
#
# The screening judge is a Claude-family model (cross-provider from the
# task model). This script only prepares and merges its work: judge-export
# writes every (output, criteria) row still lacking verdicts; the judge
# answers each criterion true/false (true only if the deliverable clearly
# satisfies it; false when in doubt) and returns
# {run_id: {assertion_id: bool}}; judge-import validates ids and appends.

def _crit_sha(text: str) -> str:
    return hashlib.sha1(text.encode()).hexdigest()[:10]


def _all_assertions(row: dict) -> list[dict]:
    """Every assertion a run's output is scored against: its own side, the
    floor's cf side, and (S6) the cross side for ceiling/twin rows."""
    return (row["assertions"] + (row.get("cf_assertions") or [])
            + (row.get("cross_assertions") or []))


def _load_force(path: Path | None) -> set[tuple[str, str]]:
    """Lines of `<probe_id|cluster_id> <assertion_id>`; a cluster id applies
    to every instance and every condition of that cluster."""
    out = set()
    if path is None:
        return out
    for line in Path(path).read_text().splitlines():
        parts = line.split()
        if len(parts) == 2:
            out.add((parts[0], parts[1]))
    return out


def _needs_verdict(rid: str, a: dict, judged: dict | None,
                   force: set[tuple[str, str]]) -> bool:
    probe_id = rid.split(":")[0]
    if (probe_id, a["id"]) in force or (probe_id[:6], a["id"]) in force:
        return True
    if not judged or a["id"] not in judged.get("verdicts", {}):
        return True
    sha = (judged.get("criteria_sha") or {}).get(a["id"])
    return sha is not None and sha != _crit_sha(a["criterion"])


def cmd_judge_export(args) -> int:
    rows = {r["run_id"]: r for r in
            (json.loads(x) for x in (args.work_dir / "runs.jsonl").read_text().splitlines())}
    results = _read_done(args.work_dir / "results.jsonl")
    judged = _read_done(args.work_dir / "judgements.jsonl")
    force = _load_force(getattr(args, 'force', None))
    incremental = getattr(args, 'incremental', False)
    if args.ids:
        wanted = [x.strip() for x in Path(args.ids).read_text().splitlines() if x.strip()]
        missing = [rid for rid in wanted if rid not in results]
        if missing:
            raise SystemExit(f"--ids run_ids without results: {missing[:5]}")
        selected = wanted
    elif incremental:
        selected = list(results)
    else:
        done = {rid for rid, r in judged.items() if r.get("verdicts")}
        selected = [rid for rid in results if rid not in done]
    # Blinding (probe-spec §3: the judge sees only output + criteria): rows
    # and criteria go out under opaque ids so neither the condition
    # (floor/ceiling/twin) nor the org side (asrt-/casrt-) is inferable.
    # --incremental exports, per row, only the semantic criteria that lack a
    # verdict, whose text changed since it was judged (criteria_sha), or
    # that are listed in --force; import them with --merge.
    todo, mapping = [], {}
    for rid in selected:
        res = results[rid]
        if not res.get("output"):
            continue
        row = rows[rid]
        pool = _all_assertions(row)
        semantic = [a for a in pool if a["checker"] == "semantic"]
        if incremental:
            semantic = [a for a in semantic
                        if _needs_verdict(rid, a, judged.get(rid), force)]
        if not semantic:
            continue
        blind = "r" + hashlib.sha1(rid.encode()).hexdigest()[:12]
        keys = {f"c{i + 1}": a for i, a in enumerate(semantic)}
        todo.append({
            "id": blind,
            "criteria": {k: a["criterion"] for k, a in keys.items()},
            "output": res["output"],
        })
        mapping[blind] = {"run_id": rid,
                          "criteria": {k: a["id"] for k, a in keys.items()},
                          "criteria_sha": {a["id"]: _crit_sha(a["criterion"])
                                           for a in keys.values()}}
    todo.sort(key=lambda t: t["id"])  # opaque order, not manifest order
    out = args.work_dir / "pending-judge.json"
    out.write_text(json.dumps(todo, indent=1))
    (args.work_dir / "pending-judge.map.json").write_text(json.dumps(mapping, indent=1))
    print(f"{len(todo)} rows ({sum(len(t['criteria']) for t in todo)} criteria) -> {out}")
    return 0


def cmd_judge_import(args) -> int:
    mapping = json.loads((args.work_dir / "pending-judge.map.json").read_text())
    verdicts = json.loads(Path(args.verdicts).read_text())
    unknown = set(verdicts) - set(mapping)
    if unknown:
        raise SystemExit(f"unknown row ids: {sorted(unknown)[:5]}")
    merge = getattr(args, "merge", False)
    existing = _read_done(args.work_dir / "judgements.jsonl") if merge else {}
    with (args.work_dir / "judgements.jsonl").open("a") as fh:
        for blind, v in verdicts.items():
            m = mapping[blind]
            want = set(m["criteria"])
            if set(v) != want:
                raise SystemExit(
                    f"{blind}: verdict ids {sorted(v)} != {sorted(want)}")
            new_v = {m["criteria"][k]: bool(x) for k, x in v.items()}
            new_sha = dict(m.get("criteria_sha") or {})
            judge = args.judge
            prev = existing.get(m["run_id"])
            if prev:
                # --merge: keep untouched verdicts, overwrite re-judged ones.
                merged_v = dict(prev.get("verdicts") or {})
                merged_v.update(new_v)
                merged_sha = dict(prev.get("criteria_sha") or {})
                merged_sha.update(new_sha)
                new_v, new_sha = merged_v, merged_sha
                if prev.get("judge") and prev["judge"] != judge:
                    judge = f"{prev['judge']}+{judge}"
            fh.write(json.dumps({
                "run_id": m["run_id"], "verdicts": new_v, "judge": judge,
                "criteria_sha": new_sha,
            }) + "\n")
    print(f"imported {len(verdicts)} judgements (judge={args.judge}"
          f"{', merged' if merge else ''})")
    return 0


# --------------------------------------------------------------- report

def _score(
    run_id: str, assertions: list[dict], output: str,
    verdicts: dict[str, bool] | None,
    hedged: bool = False,
) -> float:
    if not output or not output.strip():
        # Empty-output rule (probe-spec v0.4.3): no deliverable, no credit —
        # every assertion fails, absence detectors included, and the run
        # stays in the denominator. Applies to SUT worker failures too.
        return 0.0
    total = passed = 0.0
    for a in assertions:
        total += a["weight"]
        if hedged and a["kind"] != "fact_absent":
            # Commitment rule (probe-spec v0.4.1): a both-sides output is
            # non-committal — applied-content criteria fail on both sides.
            # Absence detectors still score normally.
            continue
        if a["checker"] == "pattern":
            if a["id"].endswith("-cs"):
                # Cross-side detectors use the negation-window guard
                # (v0.4 refinement R4): a negated mention of the other
                # side's value is commitment, not enumeration.
                hit = pattern_hits_unnegated(a["criterion"], output)
            else:
                hit = re.search(
                    a["criterion"], output, re.IGNORECASE | re.DOTALL
                ) is not None
            ok = (not hit) if a["kind"] == "fact_absent" else hit
        elif a["checker"] == "semantic":
            if verdicts is None or a["id"] not in verdicts:
                raise RuntimeError(f"{run_id}: missing verdict for {a['id']}")
            # Semantic criteria are binary statements already phrased in the
            # passing direction (fact_absent ones as absence statements, en-
            # forced by the authoring validator) — never invert the verdict.
            ok = verdicts[a["id"]]
        else:
            raise RuntimeError(f"unsupported checker {a['checker']}")
        if ok:
            passed += a["weight"]
    return passed / total


def _load_drops(path: Path | None, org: str) -> set[tuple[str, str]]:
    """(cluster_id, assertion_id) pairs to exclude from scoring, for this org.

    Prespecified G4 rule (v1 FREEZE 2026-08-15): criteria whose raw judge-human
    agreement falls below 0.7 are dropped, never rewritten. Input is the
    `criteria_below_threshold` block of a `judge-agreement.json`.
    """
    if path is None:
        return set()
    data = json.loads(Path(path).read_text())
    rows = data["criteria_below_threshold"] if isinstance(data, dict) else data
    return {(r["cluster_id"], r["assertion_id"]) for r in rows
            if r["org"] == org}


def _apply_drops(row: dict, drops: set[tuple[str, str]]) -> dict:
    """Remove dropped criteria from every assertion set on a run row.

    A base or counterfactual side left with no criteria cannot be scored: the
    denominator would be zero, and an output would satisfy it vacuously. The
    prespecified rule does not cover this case, so we take the conservative
    reading and mark the instance unscorable, which makes it invalid. An
    emptied cross-side set is different and is left alone: it reverts the run
    to having no S6 discrimination check, which is how every probe behaved
    before spec v0.4.3 added one.
    """
    if not drops:
        return row
    cid = row["cluster_id"]
    row = dict(row)
    emptied = []
    for field in ("assertions", "cf_assertions", "cross_assertions"):
        pool = row.get(field)
        if not pool:
            continue
        kept = [a for a in pool if (cid, a["id"]) not in drops]
        if not kept and field != "cross_assertions":
            emptied.append(field)
        row[field] = kept
    if emptied:
        row["_unscorable"] = emptied
    return row


def cmd_report(args) -> int:
    rows = {r["run_id"]: r for r in
            (json.loads(x) for x in (args.work_dir / "runs.jsonl").read_text().splitlines())}
    drops = _load_drops(getattr(args, "drop", None), args.work_dir.resolve().name)
    if drops:
        rows = {rid: _apply_drops(r, drops) for rid, r in rows.items()}
        print(f"dropped {len(drops)} sub-0.7 criteria for "
              f"{args.work_dir.resolve().name}")
    results = _read_done(args.work_dir / "results.jsonl")
    judgements = _read_done(args.work_dir / "judgements.jsonl")

    # Screening unit is the probe INSTANCE (probe-spec v0.3): an instance
    # is valid iff its ceiling passes, its twin ceiling passes (both sides
    # of the pair), and its floor output does not pass at pair level. A
    # cluster survives with >=2/3 valid instances; only valid instances
    # ship. The stricter all-instances cluster rule is reported alongside.
    per_probe: dict[str, dict] = defaultdict(dict)
    for rid, row in rows.items():
        res = results.get(rid)
        if not res or not res.get("output"):
            raise SystemExit(f"incomplete: no output for {rid} (run `run` again)")
        jrow = judgements.get(rid) or {}
        verdicts = jrow.get("verdicts")
        for a in _all_assertions(row):
            sha = (jrow.get("criteria_sha") or {}).get(a["id"])
            if sha is not None and sha != _crit_sha(a["criterion"]):
                raise SystemExit(
                    f"stale verdict: {rid} {a['id']} was judged under a "
                    "different criterion text — re-export with --incremental")
        hedged = is_hedged(
            res["output"], row.get("hedge_base"), row.get("hedge_cf"))
        p = per_probe[row["probe_id"]]
        p["cluster_id"] = row["cluster_id"]
        if row.get("_unscorable"):
            # Every criterion on a scored side was dropped by the sub-0.7 rule.
            # Nothing is left to demonstrate, so the instance cannot be valid.
            p["unscorable"] = sorted(set(p.get("unscorable", []))
                                     | set(row["_unscorable"]))
            p.setdefault(row["condition"], 0.0)
            continue
        score = _score(rid, row["assertions"], res["output"], verdicts,
                       hedged=hedged)
        p[row["condition"]] = score
        if hedged:
            p.setdefault("hedged_runs", []).append(row["condition"])
        if row.get("cross_assertions"):
            # S6 discrimination gate (probe-spec v0.4.3): the honest output
            # of one side must NOT satisfy the other side's assertion set,
            # else the twin does not discriminate and a stale SUT would be
            # credited on it.
            key = "ceiling_vs_cf" if row["condition"] == "ceiling" else "twin_vs_base"
            p[key] = _score(rid, row["cross_assertions"], res["output"], verdicts,
                            hedged=hedged)
        if row["condition"] == "floor" and row.get("cf_assertions"):
            # The floor prompt is org-independent, so the same output is
            # scored against both sides; a memoryless model passes the pair
            # only if the assertions fail to discriminate.
            cf_score = _score(rid, row["cf_assertions"], res["output"], verdicts,
                              hedged=hedged)
            p["floor_pair_pass"] = (
                score >= CEILING_PASS and cf_score >= CEILING_PASS
            )

    clusters: dict[str, dict] = defaultdict(lambda: {"instances": {}})
    n_unscorable = 0
    for pid, p in sorted(per_probe.items()):
        if p.get("unscorable"):
            n_unscorable += 1
            clusters[p["cluster_id"]]["instances"][pid] = {
                "ceiling": None, "twin_ceiling": None, "floor": None,
                "ceiling_vs_cf": None, "twin_vs_base": None,
                "unscorable": p["unscorable"], "valid": False,
            }
            continue
        ceiling_ok = p["ceiling"] >= CEILING_PASS
        twin_ok = p.get("twin_ceiling", 1.0) >= CEILING_PASS
        floor_ok = not p.get("floor_pair_pass", p["floor"] > FLOOR_FAIL)
        discriminates = (p.get("ceiling_vs_cf", 0.0) < CEILING_PASS
                         and p.get("twin_vs_base", 0.0) < CEILING_PASS)
        clusters[p["cluster_id"]]["instances"][pid] = {
            "ceiling": p["ceiling"], "twin_ceiling": p.get("twin_ceiling"),
            "floor": p["floor"],
            "ceiling_vs_cf": p.get("ceiling_vs_cf"),
            "twin_vs_base": p.get("twin_vs_base"),
            "valid": ceiling_ok and twin_ok and floor_ok and discriminates,
        }

    report, survivors, n_valid_instances, strict_survivors = {}, [], 0, []
    for cid, c in sorted(clusters.items()):
        insts = c["instances"]
        valid = [pid for pid, i in insts.items() if i["valid"]]
        floors = [i["floor"] for i in insts.values() if i["floor"] is not None]
        guessability = (sum(1 for s in floors if s >= CEILING_PASS) / len(floors)
                        if floors else None)
        survive = len(valid) >= 2
        strict = len(valid) == len(insts)
        if survive:
            survivors.append(cid)
            n_valid_instances += len(valid)
        if strict:
            strict_survivors.append(cid)
        report[cid] = {
            "instances": insts,
            "n_valid": len(valid),
            "guessability": None if guessability is None else round(guessability, 3),
            "survive": survive,
            "strict_survive": strict,
        }

    out = {
        "task_model": {"model": TASK_MODEL[0], "effort": TASK_MODEL[1]},
        "judge_model": JUDGE_MODEL,
        "clusters": report,
        "n_clusters": len(report),
        "n_survivors": len(survivors),
        "n_valid_instances": n_valid_instances,
        "n_strict_survivors": len(strict_survivors),
        "n_unscorable_instances": n_unscorable,
        "gate_g3_clusters": len(survivors) >= 45,
        "gate_g3_instances": n_valid_instances >= 135,
    }
    text = json.dumps(out, indent=1)
    if args.out:
        Path(args.out).write_text(text)
        print(f"-> {args.out}")
    scored_guess = [r["guessability"] for r in report.values()
                    if r["guessability"] is not None]
    mean_guess = sum(scored_guess) / len(scored_guess) if scored_guess else 0.0
    print(
        f"clusters {len(report)}  survivors {len(survivors)} "
        f"(strict {len(strict_survivors)})  valid instances {n_valid_instances}  "
        f"mean guessability {mean_guess:.2f}  "
        f"G3 clusters>=45: {'PASS' if out['gate_g3_clusters'] else 'FAIL'}  "
        f"instances>=135: {'PASS' if out['gate_g3_instances'] else 'FAIL'}"
    )
    for cid, r in report.items():
        if not r["survive"]:
            bad = {pid: i for pid, i in r["instances"].items() if not i["valid"]}
            detail = "; ".join(
                f"{pid}: unscorable ({','.join(i['unscorable'])})"
                if i.get("unscorable") else
                f"{pid}: ceil={i['ceiling']:.2f} twin="
                f"{'-' if i['twin_ceiling'] is None else format(i['twin_ceiling'], '.2f')}"
                for pid, i in bad.items()
            )
            print(f"  DROP {cid} ({r['n_valid']}/3 valid): {detail}")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    m = sub.add_parser("manifest")
    m.add_argument("org_dir", type=Path)
    m.add_argument("twin_dir", type=Path)
    m.add_argument("work_dir", type=Path)
    r = sub.add_parser("run")
    r.add_argument("work_dir", type=Path)
    r.add_argument("--jobs", type=int, default=8)
    r.add_argument("--limit", type=int, default=None)
    je = sub.add_parser("judge-export")
    je.add_argument("work_dir", type=Path)
    je.add_argument("--ids", type=Path, default=None)
    je.add_argument("--incremental", action="store_true",
                    help="export only unjudged / text-changed / --force criteria")
    je.add_argument("--force", type=Path, default=None,
                    help="file of '<probe_id|cluster_id> <assertion_id>' to re-judge")
    ji = sub.add_parser("judge-import")
    ji.add_argument("work_dir", type=Path)
    ji.add_argument("verdicts", type=Path)
    ji.add_argument("--judge", default="claude-sonnet-5")
    ji.add_argument("--merge", action="store_true",
                    help="merge into existing verdicts for the row (incremental waves)")
    p = sub.add_parser("report")
    p.add_argument("work_dir", type=Path)
    p.add_argument("--out", type=Path, default=None)
    p.add_argument("--drop", type=Path, default=None,
                   help="judge-agreement.json whose criteria_below_threshold "
                        "entries are excluded from scoring (prespecified G4 "
                        "sub-0.7 rule); omit for the frozen scoring")
    args = ap.parse_args()
    return {"manifest": cmd_manifest, "run": cmd_run,
            "judge-export": cmd_judge_export, "judge-import": cmd_judge_import,
            "report": cmd_report}[args.cmd](args)


if __name__ == "__main__":
    raise SystemExit(main())
