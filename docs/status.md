# Status & Work Queue

Last updated: 2026-09-14 (deliverable reframed to dataset + validity study — see queue; earlier same day: seed-1 runs stalled 2026-09-04: provider dropped
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

Reframed 2026-09-14 (decision-log): gpt-5.4 deprecated provider-side; the
deliverable is now **dataset + construction methodology + validity study**
(`paper/draft.md`). Comparative pilot numbers are out of scope until a
successor worker is pinned and anchors re-screened.

1. DONE 2026-09-14 — **Consolidation**: paper reframed with every measured
   number sourced (`paper/draft.md`, `paper/checklist.md`); deprecation
   event + reframe dated in `docs/decision-log.md`; partial pilot rows and
   the completed floor run committed as evidence (5959c26).
2. **G4 from Mehul** — the 150-pair rater packet (sent 2026-08-25) is now
   the paper's single missing measured number; criteria < 0.7 dropped,
   never rewritten.
3. **Prose pass with Mehul** on `paper/draft.md` (structure first, voice
   second), then the checklist gate.
4. **Release packaging** per `paper/checklist.md` + G5 tracker (canary,
   licenses, ledger withheld, repro from clean clone).
5. OPTIONAL, when a successor worker is affordable — **re-anchor**: pin
   successor (rule: nearest same-provider successor; gpt-5.5 available),
   re-run anchors seeds 1–3 under frozen gate rules, new valid set, then
   the pilot queue (the driver + judge pipeline are ready as-is).

## Standing cautions

- Worker pin: every protocol path runs with
  `MEMBENCH_CODEX_BIN=~/.local/codex-0.144.5/node_modules/.bin/codex`; PATH `codex` may be newer.
- cursor-agent: QA/non-protocol only (65% twin agreement — `docs/standards-audit.md` §A).
- Blinded judging always: `judge-export` → fresh judge agents that read only
  the batch file → `judge-import`; judge model ≠ worker model.
