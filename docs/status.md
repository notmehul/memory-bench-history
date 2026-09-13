# Status & Work Queue

Last updated: 2026-09-14 (seed-1 runs stalled 2026-09-04: provider dropped
gpt-5.4 for ChatGPT-account codex — pinned worker now needs OPENAI_API_KEY
(the prespecified billing switch, paper disclosure #4; model/binary unchanged).
Progress committed in `datasets/dev/pilot/`: nomemory done + judged (floor near
zero on all rungs), fulltranscript/grep/rag/rag-lexical partial and resumable.
Previously 2026-09-02: live smokes done, keys in; previously 2026-08-28 backtest/cleanup: README + stale docs re-pointed at the
frozen v1 scope with dated notes, CHANGELOG caught up, CI fixed for the figures extra;
vendor configs frozen pre-run — `docs/vendor-configs.md`;
rater packet sent to Mehul 2026-08-25; adapters + pilot CLI landed; v1 freeze — `CLAUDE.md` + FREEZE section of
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

1. DONE 2026-08-22 — **Adapters** for all 8 systems registered in `membench.pilot`
   (`nomemory fulltranscript grep rag mem0 mem0-silo cognee graphiti supermemory`;
   `uv sync --extra adapters --extra market`). Market systems' internal LLM =
   Gemini where configurable (Supermemory: vendor-managed, not configurable).
   Each `sut_<name>.py` has a `smoke(org_dir)` for a first live call once keys exist.
2. DONE 2026-08-22 — **Pilot CLI + orchestrator**: `scripts/run_pilot.py run/report`
   over `membench.pilot` (only-valid = the frozen 371, resumable, cost columns) and
   `scripts/score_sut.py` (blinded judge round trip, pair credit, per-rung SEs).
3. **Keys from Mehul** (shell env, never the repo): `OPENAI_API_KEY` (worker billing
   behind pinned codex 0.144.5 — switch codex auth from chatgpt to API key),
   `GEMINI_API_KEY`, `SUPERMEMORY_API_KEY`.
4. DONE 2026-09-02 — **Live smokes** ran against all four market adapters +
   the RAG embedder (keys: Supermemory + Gemini in `~/.membench/keys.env`,
   never the repo). Mechanical amendments dated in `docs/vendor-configs.md`:
   Supermemory tag charset/nulls/hybrid search; Graphiti 0.29.3 Kuzu fixes +
   Gemini model pins; dataset-wide finding — `sim_time` is null on every
   event (disclosures 11–12 in `paper/draft.md`). Graphiti ingests ≈ 48 s/
   episode → plan ≈ 2.7 h per org side.
5. **Seed-1 smoke, all 8 systems** (+ Mem0 silo) → blind judge → item analysis.
6. **Seeds 2–3** (K=1; variance subset: seed 1 × full-transcript + one market system × K=3).
7. **150-pair rater packet to Mehul** — one file, one column
   (`datasets/dev/calibration/rater-packet.json`); criteria < 0.7 dropped, never rewritten.
8. **Stats + radar + reproducible tables** — generator DONE 2026-08-27
   (`scripts/figures.py report --work W --systems ... --paired mem0,mem0-silo`:
   radar by rung, per-rung/archetype tables, ≥2/3-seed direction rule, paired H2
   diff, cost columns; dry-run on mock data). Rerun on real summaries when runs land.
9. **Vendor right-of-reply** (raw results + harness, 7 days).
10. **Draft** — skeleton DONE 2026-08-27 (`paper/draft.md`: sections sourced
    to docs, 10-item disclosure inventory; §5–6 wait on runs) + preprint
    checklist (`paper/checklist.md`). Remaining: prose pass with Mehul after
    real numbers.

## Standing cautions

- Worker pin: every protocol path runs with
  `MEMBENCH_CODEX_BIN=~/.local/codex-0.144.5/node_modules/.bin/codex`; PATH `codex` may be newer.
- cursor-agent: QA/non-protocol only (65% twin agreement — `docs/standards-audit.md` §A).
- Blinded judging always: `judge-export` → fresh judge agents that read only
  the batch file → `judge-import`; judge model ≠ worker model.
