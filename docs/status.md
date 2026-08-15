# Status & Work Queue

Last updated: 2026-08-15 (v1 freeze — `CLAUDE.md` + FREEZE section of
`docs/dataset-plan.md`). Update when a queue item completes; keep entries dated.
The pre-freeze A/B/C queue tables were removed 2026-08-15 — see git history
(`git show d0820af:docs/status.md`); dated evidence is in `docs/decision-log.md`.

## Where the project stands

- **Dataset (frozen):** seeds 1–3, probe-spec v0.4.3, judge rubric v2 —
  **371 valid instances: A1 50, A2 43, A4 106, A7 172** (seed 1 46/54, 125;
  seed 2 46/54, 131; seed 3 40/54, 115; instance gates carried as FAILs).
  Seeds 4–5 are **unscreened holdouts** (seed 4 has 327/486 cached outputs;
  no further screening in v1). No criterion edits, adjudications, or
  re-judging from here on — a probe that looks wrong is flagged in item
  analysis, never fixed.
- **Worker / judge:** gpt-5.4, effort medium, codex-cli 0.144.5 (enforced by
  `membench.codex_bin`; billing moves to an OpenAI key, disclosed) · judge
  claude-sonnet-5, rubric v2, always blinded.
- **Adapters that exist** (`src/membench/adapters.py`, `rag.py`,
  `typed_memory.py`; registered in `python -m membench.pilot`): no-memory,
  full-transcript, grep-agent, naive-RAG (BM25 lexical with an embedding
  seam; Gemini `gemini-embedding-001` embedder being added), typed-memory
  reference impl (registered, **unused — DEFERRED** by the freeze).
- **Pipeline that exists:** `python -m membench.pilot <adapter> <org> out.jsonl
  [--silo]` (one adapter, one org, pinned worker) → `scripts/score_sut.py` (pair
  credit, normalized, per-rung, cluster-robust SEs; blinded judge round trip).
- **Done audits:** scorer-exploit audit rebuilt on the frozen canon; 20-decoy
  judge false-accept audit **2/41 measured, 0/39 adjudicated**
  (`datasets/dev/screening/judge-decoys/audit.json`); power analysis; 150-pair
  calibration packet built (`datasets/dev/calibration/`). Vendor selection by
  the top-4-stars rule (`docs/vendor-survey.md`). Deferred scope: `docs/deferred.md`.

## Work queue (in order — the only queue)

1. **Adapters** (two-call SUT interface, per-principal isolation): naive-RAG
   with Gemini embeddings · Mem0 · Cognee · Graphiti (Kuzu backend) ·
   Supermemory (hosted; needs key). Internal LLM = Gemini where configurable;
   vendor-recommended config frozen in writing before any run.
2. **Pilot CLI + orchestrator:** extend `membench.pilot` (only-valid
   instances, resumable, cost columns) + `scripts/run_pilot.py` cross-seed
   orchestrator (in progress) + `scripts/score_pilot.py`.
3. **Keys from Mehul:** `OPENAI_API_KEY` (worker billing behind pinned codex
   0.144.5), `GEMINI_API_KEY`, `SUPERMEMORY_API_KEY`.
4. **Seed-1 smoke, all 8 systems** (+ Mem0 silo) → item analysis.
5. **Seeds 2–3** (K=1; variance subset: seed 1 × full-transcript + one market system × K=3).
6. **Blind judge** (rubric v2, opaque ids, fresh judge agents).
7. **150-pair rater packet to Mehul** — one file, one column
   (`datasets/dev/calibration/rater-packet.json`); criteria < 0.7 dropped, never rewritten.
8. **Stats + radar + reproducible tables** (cluster-robust SEs, paired per-item, tie rule, cost columns, H1–H3; ≥2/3-seed direction rule).
9. **Vendor right-of-reply** (raw results + harness, 7 days).
10. **Draft.**

## Standing cautions

- Worker pin: every protocol path runs with
  `MEMBENCH_CODEX_BIN=~/.local/codex-0.144.5/node_modules/.bin/codex`; PATH `codex` may be newer.
- cursor-agent: QA/non-protocol only (65% twin agreement — `docs/standards-audit.md` §A).
- Blinded judging always: `judge-export` → fresh judge agents that read only
  the batch file → `judge-import`; judge model ≠ worker model.
