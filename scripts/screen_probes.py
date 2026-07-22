"""Phase 3 validity screening: floor/ceiling runs + gate G3 (probe-spec §3).

Every probe instance runs in `floor` (task only) and `ceiling` (task + the
relevant slice of B rendered canonically); instances with a counterfactual
side additionally run `twin_ceiling` against the twin org, scored with the
counterfactual assertions. No SUT is involved — this screens the probes
themselves.

Standing decisions (dataset-plan.md):
  fixed task model  = gpt-5.4-mini via codex, reasoning effort medium
  screening judge   = gpt-5.4 (semantic assertions only; != task model;
                      formal judge calibration happens in Phase 4)

Pass rules (n=3 instances/cluster; small-n adaptation of the spec's >=90%
ceiling / >=70% floor-fail gates; floor rule revised at the pilot stage,
before any full screening run — see probe-spec.md changelog v0.2):
  instance ceiling-pass  <=> weighted assertion score == 1.0
  instance floor-fail    <=> weighted assertion score <= 0.5
  pair-level floor       <=> a floor output scoring 1.0 against BOTH the
                             base and counterfactual assertion sets (the
                             floor prompt is org-independent, so one output
                             serves both sides)
  cluster survives G3    <=> all 3 ceiling pass, all twin_ceiling pass
                             (both sides of every twin pair), and no floor
                             run passes at pair level. Per-side floor
                             passes are reported as `guessability` — for
                             pair-credited probes they indicate a guessable
                             base side, which pair crediting cancels
                             structurally (risk register: generator bias).

Resumable: every completed run is appended to results.jsonl; re-running
`run`/`judge` skips completed work.

Usage:
  python scripts/screen_probes.py manifest <org_dir> <twin_dir> <work_dir>
  python scripts/screen_probes.py run <work_dir> [--jobs 8] [--limit N]
  python scripts/screen_probes.py judge <work_dir> [--jobs 6]
  python scripts/screen_probes.py report <work_dir> [--out <org_dir>/g3-report.json]
"""

from __future__ import annotations

import argparse
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
from membench.ledger import load_event_index, load_ledger  # noqa: E402

TASK_MODEL = ("gpt-5.4-mini", "medium")
JUDGE_MODEL = ("gpt-5.4", "low")
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

    rows = []
    for p in probes:
        base_asserts = p["assertions"]
        cf = p["counterfactual_probe"]
        rows.append({
            "run_id": f"{p['probe_id']}:floor",
            "probe_id": p["probe_id"], "cluster_id": p["cluster_id"],
            "condition": "floor",
            "prompt": _prompt(org, p, None),
            "assertions": base_asserts,
            # The floor prompt is identical on both orgs (no context), so the
            # same output is scored against both sides for pair-level floor.
            "cf_assertions": cf["assertions"] if cf else None,
        })
        rows.append({
            "run_id": f"{p['probe_id']}:ceiling",
            "probe_id": p["probe_id"], "cluster_id": p["cluster_id"],
            "condition": "ceiling",
            "prompt": _prompt(org, p, _context_facts(org, ledger, index, p)),
            "assertions": base_asserts,
        })
        if cf:
            rows.append({
                "run_id": f"{p['probe_id']}:twin_ceiling",
                "probe_id": p["probe_id"], "cluster_id": p["cluster_id"],
                "condition": "twin_ceiling",
                "prompt": _prompt(twin, p, _context_facts(twin, t_ledger, t_index, p)),
                "assertions": p["counterfactual_probe"]["assertions"],
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
        ["codex", "exec", "-C", str(cwd), "-s", "workspace-write",
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

def _do_judge(run_id: str, output: str, semantic: list[dict]) -> dict:
    crit = "\n".join(f"{i + 1}. {a['criterion']}" for i, a in enumerate(semantic))
    prompt = (
        "You are grading a work deliverable against binary criteria.\n\n"
        f"DELIVERABLE:\n---\n{output}\n---\n\n"
        f"CRITERIA:\n{crit}\n\n"
        "For each criterion, answer true only if the deliverable clearly "
        "satisfies it; when in doubt answer false. Write a file verdict.json "
        'in the current directory of the exact form {"1": true, "2": false, ...} '
        "with one entry per criterion. Write nothing else."
    )
    for _ in range(2):
        with tempfile.TemporaryDirectory(prefix="mbjudge-") as tmp:
            tmp_path = Path(tmp)
            try:
                _codex(prompt, *JUDGE_MODEL, cwd=tmp_path)
            except subprocess.TimeoutExpired:
                continue
            v = tmp_path / "verdict.json"
            if v.exists():
                try:
                    raw = json.loads(v.read_text())
                    verdicts = {
                        a["id"]: bool(raw[str(i + 1)])
                        for i, a in enumerate(semantic)
                    }
                    return {"run_id": run_id, "verdicts": verdicts}
                except (json.JSONDecodeError, KeyError):
                    continue
    return {"run_id": run_id, "verdicts": None, "error": "judge failed"}


def cmd_judge(args) -> int:
    rows = {r["run_id"]: r for r in
            (json.loads(x) for x in (args.work_dir / "runs.jsonl").read_text().splitlines())}
    results = _read_done(args.work_dir / "results.jsonl")
    j_path = args.work_dir / "judgements.jsonl"
    done = {rid for rid, r in _read_done(j_path).items() if r.get("verdicts")}
    todo = []
    for rid, res in results.items():
        if rid in done or not res.get("output"):
            continue
        row = rows[rid]
        pool = row["assertions"] + (row.get("cf_assertions") or [])
        semantic = [a for a in pool if a["checker"] == "semantic"]
        if semantic:
            todo.append((rid, res["output"], semantic))
    print(f"{len(done)} judged, {len(todo)} to judge", flush=True)
    lock = threading.Lock()
    n = 0
    with j_path.open("a") as fh, ThreadPoolExecutor(max_workers=args.jobs) as ex:
        futs = [ex.submit(_do_judge, *t) for t in todo]
        for fut in as_completed(futs):
            res = fut.result()
            with lock:
                fh.write(json.dumps(res) + "\n")
                fh.flush()
                n += 1
                if n % 20 == 0:
                    print(f"  {n}/{len(todo)}", flush=True)
    failed = sum(1 for r in _read_done(j_path).values() if not r.get("verdicts"))
    print(f"judge complete; {failed} failed (rerun `judge` to retry)")
    return 1 if failed else 0


# --------------------------------------------------------------- report

def _score(
    run_id: str, assertions: list[dict], output: str,
    verdicts: dict[str, bool] | None,
) -> float:
    total = passed = 0.0
    for a in assertions:
        total += a["weight"]
        if a["checker"] == "pattern":
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


def cmd_report(args) -> int:
    rows = {r["run_id"]: r for r in
            (json.loads(x) for x in (args.work_dir / "runs.jsonl").read_text().splitlines())}
    results = _read_done(args.work_dir / "results.jsonl")
    judgements = _read_done(args.work_dir / "judgements.jsonl")

    per_cluster: dict[str, dict[str, list]] = defaultdict(lambda: defaultdict(list))
    for rid, row in rows.items():
        res = results.get(rid)
        if not res or not res.get("output"):
            raise SystemExit(f"incomplete: no output for {rid} (run `run` again)")
        verdicts = (judgements.get(rid) or {}).get("verdicts")
        score = _score(rid, row["assertions"], res["output"], verdicts)
        if row["condition"] == "floor" and row.get("cf_assertions"):
            # Pair-level floor: the floor prompt is org-independent, so the
            # same output is scored against both sides. A memoryless model
            # can pass the pair only if the assertions fail to discriminate.
            cf_score = _score(rid, row["cf_assertions"], res["output"], verdicts)
            per_cluster[row["cluster_id"]]["floor_pair"].append(
                score >= CEILING_PASS and cf_score >= CEILING_PASS
            )
        per_cluster[row["cluster_id"]][row["condition"]].append(score)

    report, survivors = {}, []
    for cid, conds in sorted(per_cluster.items()):
        ceiling = conds["ceiling"]
        floor = conds["floor"]
        twin = conds.get("twin_ceiling", [])
        pair = conds.get("floor_pair", [])
        ceiling_ok = all(s >= CEILING_PASS for s in ceiling)
        twin_ok = all(s >= CEILING_PASS for s in twin)
        floor_fails = sum(1 for s in floor if s <= FLOOR_FAIL)
        # Counterfactual-paired probes (probe-spec section 4): the pair is
        # the scoring unit; per-side floor passes are reported as
        # guessability, not grounds for dropping.
        floor_ok = (not any(pair)) if pair else floor_fails >= 2
        guessability = sum(1 for s in floor if s >= CEILING_PASS) / len(floor)
        survive = ceiling_ok and twin_ok and floor_ok
        if survive:
            survivors.append(cid)
        report[cid] = {
            "ceiling": ceiling, "floor": floor, "twin_ceiling": twin,
            "ceiling_ok": ceiling_ok, "twin_ok": twin_ok,
            "floor_fails": floor_fails, "floor_ok": floor_ok,
            "guessability": round(guessability, 3),
            "survive": survive,
        }

    out = {
        "task_model": {"model": TASK_MODEL[0], "effort": TASK_MODEL[1]},
        "judge_model": {"model": JUDGE_MODEL[0], "effort": JUDGE_MODEL[1]},
        "clusters": report,
        "n_clusters": len(report),
        "n_survivors": len(survivors),
        "n_instances_surviving": 3 * len(survivors),
        "gate_g3_cluster_floor": len(survivors) >= 45,
    }
    text = json.dumps(out, indent=1)
    if args.out:
        Path(args.out).write_text(text)
        print(f"-> {args.out}")
    mean_guess = sum(r["guessability"] for r in report.values()) / len(report)
    print(
        f"clusters {len(report)}  survivors {len(survivors)}  "
        f"instances {3 * len(survivors)}  mean guessability {mean_guess:.2f}  "
        f"G3 cluster floor (>=45): "
        f"{'PASS' if out['gate_g3_cluster_floor'] else 'FAIL'}"
    )
    for cid, r in report.items():
        if not r["survive"]:
            why = []
            if not r["ceiling_ok"]:
                why.append(f"ceiling {r['ceiling']}")
            if not r["twin_ok"]:
                why.append(f"twin {r['twin_ceiling']}")
            if not r["floor_ok"]:
                why.append(f"floor fails {r['floor_fails']}/3")
            print(f"  DROP {cid}: {'; '.join(why)}")
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
    j = sub.add_parser("judge")
    j.add_argument("work_dir", type=Path)
    j.add_argument("--jobs", type=int, default=6)
    p = sub.add_parser("report")
    p.add_argument("work_dir", type=Path)
    p.add_argument("--out", type=Path, default=None)
    args = ap.parse_args()
    return {"manifest": cmd_manifest, "run": cmd_run,
            "judge": cmd_judge, "report": cmd_report}[args.cmd](args)


if __name__ == "__main__":
    raise SystemExit(main())
