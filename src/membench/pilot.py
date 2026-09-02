"""Run one adapter over one org SIDE (base or twin) with the pinned worker
and write runner-shaped results (`<probe>:sut` rows) for
`scripts/score_sut.py`.

  python -m membench.pilot <adapter> <org_dir> <out.jsonl> [--silo]
      [--probes-from <base_org_dir>] [--no-only-valid]
      [--system <name>] [--side base|twin] [--k N]

Adapters (the SYSTEM registry — one line per system; market adapters
`mem0`, `mem0-silo`, `cognee`, `graphiti`, `supermemory` register here):
nomemory | fulltranscript | grep | rag | rag-lexical | typed. `rag` is the
pinned v1 baseline #3 (`EMBEDDING_MODEL` via `GeminiEmbedder`, needs
`GEMINI_API_KEY`; `rag-lexical` is its BM25 ablation). `typed` stays
registered but is DEFERRED by the v1 freeze of 2026-08-15 — never run in
v1. `--silo` selects the per-principal isolated store where the adapter
supports it.

Twin side: twin org dirs carry no probes.jsonl / g3-report.json, so a twin
run is driven with `--probes-from <base_org_dir>` (the base org's probes
against the twin's stream/org.json — as screening builds twin_ceiling).
Only-valid (default ON): only instances valid in the base org's
g3-report.json are injected; the count of skipped instances is recorded.
Resumable: run_ids already present in <out.jsonl> with an output are
skipped and new rows are appended. Ingestion is always a FULL stream pass
through a fresh adapter instance per (org side, system, k) — memory is
rebuilt from scratch, never resumed.

Every row carries cost columns (`context_chars`, worker `seconds`,
`wall_seconds`, `prompt_sha`); `<out>.meta.json` records system/side/k,
adapter + worker counters and the typed-memory prompt hash so cost columns
and freezes are auditable. Only `CodexWorker` (pinned gpt-5.4 medium,
codex-cli 0.144.5) is ever built here.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import time
from pathlib import Path

from .adapters import FullTranscriptAdapter, GrepAgentAdapter, NoMemoryAdapter
from .g3 import load_valid_instances
from .rag import EMBEDDING_MODEL, EmbeddingRetriever, GeminiEmbedder, NaiveRAGAdapter
from .runner import Runner
from .sut_cognee import CogneeAdapter
from .sut_graphiti import GraphitiAdapter
from .sut_mem0 import Mem0Adapter
from .sut_supermemory import SupermemoryAdapter
from .typed_memory import TypedMemoryAdapter, prompt_hash
from .workers import CodexWorker

ADAPTERS = {
    "nomemory": lambda w, silo: NoMemoryAdapter(w),
    "fulltranscript": lambda w, silo: FullTranscriptAdapter(w, shared=not silo),
    "grep": lambda w, silo: GrepAgentAdapter(w, shared=not silo),
    "typed": lambda w, silo: TypedMemoryAdapter(w, shared=not silo),   # DEFERRED (v1)
    # pinned embedding baseline (standards-audit B.5) + its lexical ablation
    "rag": lambda w, silo: NaiveRAGAdapter(
        w, retriever=EmbeddingRetriever(GeminiEmbedder().embed, model_name=EMBEDDING_MODEL),
        shared=not silo),
    "rag-lexical": lambda w, silo: NaiveRAGAdapter(w, shared=not silo),
    # market systems (v1 freeze: top-4 by stars, 2026-08-15); silo ablation on Mem0
    "mem0": lambda w, silo: Mem0Adapter(w, shared=not silo),
    "mem0-silo": lambda w, silo: Mem0Adapter(w, shared=False),
    "cognee": lambda w, silo: CogneeAdapter(w, shared=not silo),
    "graphiti": lambda w, silo: GraphitiAdapter(w, shared=not silo),
    # settle policy frozen in docs/vendor-configs.md (2026-08-27): ingestion is
    # async server-side; search only after the processing queue drains.
    "supermemory": lambda w, silo: SupermemoryAdapter(
        w, shared=not silo, ingest_settle_seconds=5, wait_for_processing=True,
        settle_timeout=600),
}


def build_adapter(name: str, worker, silo: bool = False, namespace: str = ""):
    if name not in ADAPTERS:
        raise SystemExit(f"unknown adapter {name!r}; choose from {sorted(ADAPTERS)}")
    adapter = ADAPTERS[name](worker, silo)
    if namespace and hasattr(adapter, "namespace"):
        adapter.namespace = namespace          # isolate persistent hosted stores
    return adapter


class _Instrumented:
    """Adapter proxy recording per-task wall time, worker seconds and the
    task prompt hash — cost columns the runner does not know about."""

    def __init__(self, adapter, worker):
        self._adapter, self._worker = adapter, worker
        self.last: dict = {}

    @property
    def counters(self):
        return self._adapter.counters

    def ingest(self, principal, event):
        return self._adapter.ingest(principal, event)

    def run_task(self, principal, task):
        before = float(getattr(self._worker, "counters", {}).get("seconds", 0.0))
        started = time.monotonic()
        try:
            return self._adapter.run_task(principal, task)
        finally:
            after = float(getattr(self._worker, "counters", {}).get("seconds", 0.0))
            self.last = {
                "seconds": round(after - before, 3),
                "wall_seconds": round(time.monotonic() - started, 3),
                "prompt_sha": hashlib.sha1(task.encode()).hexdigest()[:12],
            }


def read_rows(path: Path) -> dict[str, dict]:
    done = {}
    if path.exists():
        for line in path.read_text().splitlines():
            if line.strip():
                r = json.loads(line)
                done[r["run_id"]] = r
    return done


def run_side(adapter_name: str, org_dir: Path, out: Path, worker, *,
             silo: bool = False, probes_from: Path | None = None,
             only_valid: bool = True, system: str | None = None,
             side: str = "base", k: int = 1) -> dict:
    """One full pass of `org_dir`'s stream through a fresh adapter; probes
    (and the G3 valid set) come from `probes_from` (default: org_dir).
    Returns the meta dict also written to `<out>.meta.json`."""
    probes_dir = probes_from or org_dir
    probes = [json.loads(line) for line in
              (probes_dir / "probes.jsonl").read_text().splitlines()]
    n_all = len(probes)
    if only_valid:
        valid = load_valid_instances(probes_dir)
        probes = [p for p in probes if p["probe_id"] in valid]
    n_skipped_invalid = n_all - len(probes)
    done = {rid for rid, r in read_rows(out).items() if r.get("output")}
    todo = [p for p in probes if f"{p['probe_id']}:sut" not in done]

    adapter = build_adapter(adapter_name, worker, silo, namespace=org_dir.name)
    proxy = _Instrumented(adapter, worker)
    out.parent.mkdir(parents=True, exist_ok=True)
    started = time.monotonic()
    n_new = 0
    with out.open("a") as fh:
        def on_row(row: dict) -> None:
            nonlocal n_new
            row.update(proxy.last)
            fh.write(json.dumps(row) + "\n")
            fh.flush()
            n_new += 1
        Runner(org_dir, proxy, probes=todo, on_row=on_row).run()
    meta = {
        "adapter": adapter_name, "system": system or adapter_name, "side": side,
        "k": k, "silo": silo, "org": org_dir.name, "probes_from": probes_dir.name,
        "only_valid": only_valid, "n_probes_all": n_all,
        "n_skipped_invalid": n_skipped_invalid, "n_target": len(probes),
        "n_resumed": len(probes) - len(todo), "n_new_rows": n_new,
        "n_rows": len(read_rows(out)),
        "worker": {"model": "gpt-5.4", "effort": "medium",
                   "harness": "codex-cli 0.144.5"},
        "adapter_counters": adapter.counters,
        "worker_counters": getattr(worker, "counters", {}),
        "wall_seconds": round(time.monotonic() - started, 3),
    }
    if adapter_name == "typed":
        meta["typed_memory_prompt_hash"] = prompt_hash()
    Path(str(out) + ".meta.json").write_text(json.dumps(meta, indent=1))
    return meta


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("adapter", choices=sorted(ADAPTERS))
    ap.add_argument("org_dir", type=Path)
    ap.add_argument("out", type=Path)
    ap.add_argument("--silo", action="store_true")
    ap.add_argument("--probes-from", type=Path, default=None,
                    help="base org dir supplying probes.jsonl + g3-report.json (twin runs)")
    ap.add_argument("--no-only-valid", dest="only_valid", action="store_false")
    ap.add_argument("--system", default=None)
    ap.add_argument("--side", choices=("base", "twin"), default="base")
    ap.add_argument("--k", type=int, default=1)
    args = ap.parse_args(argv)
    meta = run_side(args.adapter, args.org_dir, args.out, CodexWorker(),
                    silo=args.silo, probes_from=args.probes_from,
                    only_valid=args.only_valid, system=args.system,
                    side=args.side, k=args.k)
    print(f"{meta['system']}{' (silo)' if args.silo else ''} {meta['side']} k={meta['k']} "
          f"on {args.org_dir.name}: {meta['n_new_rows']} new rows "
          f"({meta['n_resumed']} resumed, {meta['n_skipped_invalid']} invalid skipped) "
          f"-> {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
