"""Run one adapter over one org (base or twin) with the pinned worker and
write runner-shaped results (`<probe>:sut` rows) for `scripts/score_sut.py`.

  python -m membench.pilot <adapter> <org_dir> <out.jsonl> [--silo]

Adapters: nomemory | fulltranscript | grep | typed | rag | rag-lexical (`rag` is the
pinned v1 baseline #3 — `EMBEDDING_MODEL` via `GeminiEmbedder`, needs `GEMINI_API_KEY`;
`rag-lexical` is its BM25 ablation). `--silo` selects the per-principal isolated store
where the adapter supports it (baseline #7).
Every run records the adapter counters and the typed-memory prompt hash
next to the results (`<out>.meta.json`) so cost columns and freezes are
auditable. Dev smoke runs (A7) are never headline numbers.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from .adapters import FullTranscriptAdapter, GrepAgentAdapter, NoMemoryAdapter
from .rag import EMBEDDING_MODEL, EmbeddingRetriever, GeminiEmbedder, NaiveRAGAdapter
from .runner import Runner
from .typed_memory import TypedMemoryAdapter, prompt_hash
from .workers import CodexWorker

ADAPTERS = {
    "nomemory": lambda w, silo: NoMemoryAdapter(w),
    "fulltranscript": lambda w, silo: FullTranscriptAdapter(w, shared=not silo),
    "grep": lambda w, silo: GrepAgentAdapter(w, shared=not silo),
    "typed": lambda w, silo: TypedMemoryAdapter(w, shared=not silo),
    # pinned embedding baseline (standards-audit B.5) + its lexical ablation
    "rag": lambda w, silo: NaiveRAGAdapter(
        w, retriever=EmbeddingRetriever(GeminiEmbedder().embed, model_name=EMBEDDING_MODEL),
        shared=not silo),
    "rag-lexical": lambda w, silo: NaiveRAGAdapter(w, shared=not silo),
}


def build_adapter(name: str, worker, silo: bool = False):
    if name not in ADAPTERS:
        raise SystemExit(f"unknown adapter {name!r}; choose from {sorted(ADAPTERS)}")
    return ADAPTERS[name](worker, silo)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("adapter", choices=sorted(ADAPTERS))
    ap.add_argument("org_dir", type=Path)
    ap.add_argument("out", type=Path)
    ap.add_argument("--silo", action="store_true")
    args = ap.parse_args(argv)
    worker = CodexWorker()
    adapter = build_adapter(args.adapter, worker, args.silo)
    rows = Runner(args.org_dir, adapter).run(out_path=args.out)
    meta = {"adapter": args.adapter, "silo": args.silo, "org": args.org_dir.name,
            "n_rows": len(rows), "worker": {"model": "gpt-5.4", "effort": "medium",
                                             "harness": "codex-cli 0.144.5"},
            "adapter_counters": adapter.counters,
            "worker_counters": getattr(worker, "counters", {})}
    if args.adapter == "typed":
        meta["typed_memory_prompt_hash"] = prompt_hash()
    Path(str(args.out) + ".meta.json").write_text(json.dumps(meta, indent=1))
    print(f"{args.adapter}{' (silo)' if args.silo else ''} on {args.org_dir.name}: "
          f"{len(rows)} probe outputs -> {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
