"""Author probe tasks/assertions for one org via the content LLM (codex).

Shards the constructor's authoring requests into batches, has gpt-5.4
(effort medium) author each batch against prompts/probe-authoring.md, and
loops `membench.probes apply` — which enforces the mechanical hygiene and
pattern validators — feeding validation errors back for up to two retries.
Only a fully-valid set of 54 clusters ever produces probes.jsonl.

Usage: python scripts/author_probes.py <org_dir> <work_dir> [--jobs 5]
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from membench.probes import build_requests, validate_authored_cluster  # noqa: E402

BATCH = 6
MODEL = ("gpt-5.4", "medium")
TIMEOUT = 600
CONTRACT = (ROOT / "prompts" / "probe-authoring.md").read_text()


def author_batch(
    reqs: list[dict], batch_dir: Path, feedback: dict[str, list[str]]
) -> list[dict]:
    batch_dir.mkdir(parents=True, exist_ok=True)
    prompt = CONTRACT + "\n\nRequests:\n" + json.dumps(reqs, indent=1)
    notes = {cid: fb for cid, fb in feedback.items()
             if cid in {r["cluster_id"] for r in reqs}}
    if notes:
        prompt += (
            "\n\nPrevious attempts for these clusters failed mechanical "
            "validation. Each entry gives the errors and the prior record. "
            "If no error mentions the task text, reuse the prior task "
            "VERBATIM and rewrite only the failing assertions:\n"
            + json.dumps(notes, indent=1)
        )
    prompt += (
        "\n\nWrite the JSON array (one object per request, same order) to a "
        "file named authored.json in the current directory. No other output."
    )
    try:
        subprocess.run(
            ["codex", "exec", "-C", str(batch_dir), "-s", "workspace-write",
             "--skip-git-repo-check",
             "-m", MODEL[0], "-c", f"model_reasoning_effort={MODEL[1]}", "-"],
            input=prompt, text=True, capture_output=True, timeout=TIMEOUT,
        )
    except subprocess.TimeoutExpired:
        return []
    out = batch_dir / "authored.json"
    if not out.exists():
        return []
    try:
        data = json.loads(out.read_text())
        return data if isinstance(data, list) else []
    except json.JSONDecodeError:
        return []


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("org_dir", type=Path)
    ap.add_argument("work_dir", type=Path)
    ap.add_argument("--jobs", type=int, default=5)
    args = ap.parse_args()

    org = json.loads((args.org_dir / "org.json").read_text())
    plan_doc = json.loads((args.org_dir / "plan.json").read_text())
    requests = build_requests(org, plan_doc)
    by_id = {r["cluster_id"]: r for r in requests}

    accepted: dict[str, dict] = {}
    feedback: dict[str, list[str]] = {}
    # Resume: keep previously authored clusters that still pass the current
    # validators (validator tightening only re-authors what it rejects).
    prior = args.work_dir / "authored.json"
    if prior.exists():
        for authored in json.loads(prior.read_text())["clusters"]:
            cid = authored.get("cluster_id")
            if cid not in by_id:
                continue
            errs = validate_authored_cluster(by_id[cid], authored)
            if errs:
                feedback[cid] = {"errors": errs, "prior": authored}
            else:
                accepted[cid] = authored
        print(f"resume: {len(accepted)} prior clusters still valid, "
              f"{len(feedback)} to repair", flush=True)
    for attempt in range(3):
        pending = [r for r in requests if r["cluster_id"] not in accepted]
        if not pending:
            break
        batches = [pending[i:i + BATCH] for i in range(0, len(pending), BATCH)]
        print(f"attempt {attempt + 1}: {len(pending)} clusters in "
              f"{len(batches)} batches", flush=True)
        with ThreadPoolExecutor(max_workers=args.jobs) as ex:
            futs = [
                ex.submit(author_batch, b, args.work_dir / f"a{attempt}-b{i}",
                          dict(feedback))
                for i, b in enumerate(batches)
            ]
            results = [f.result() for f in futs]
        feedback = {}
        for authored_list in results:
            for authored in authored_list:
                cid = authored.get("cluster_id")
                if cid not in by_id or cid in accepted:
                    continue
                errs = validate_authored_cluster(by_id[cid], authored)
                if errs:
                    feedback[cid] = {"errors": errs, "prior": authored}
                else:
                    accepted[cid] = authored
        print(f"  accepted {len(accepted)}/{len(requests)}; "
              f"{len(feedback)} rejected", flush=True)

    authored_path = args.work_dir / "authored.json"
    authored_path.write_text(json.dumps(
        {"clusters": [accepted[cid] for cid in sorted(accepted)]}, indent=1))
    if len(accepted) < len(requests):
        missing = sorted(set(by_id) - set(accepted))
        print(f"FAILED clusters after retries: {missing}", file=sys.stderr)
        return 3
    rc = subprocess.run(
        [sys.executable, "-m", "membench.probes", "apply", str(args.org_dir),
         "--authored", str(authored_path)],
        cwd=ROOT,
    ).returncode
    return rc


if __name__ == "__main__":
    raise SystemExit(main())
