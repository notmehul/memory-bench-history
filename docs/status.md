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
  calibration packet built and RATED (`datasets/dev/calibration/`) — **G4 FAIL,
  κ = 0.537 vs ≥ 0.75; see queue item 2**. Vendor selection by
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
1b. DONE 2026-09-14 — **Freeze reconciled** with the reframe: dated FREEZE
   amendment (`docs/dataset-plan.md`), `AGENTS.md`, README, `docs/deferred.md`.
   Decisions recorded: arXiv preprint first, data license CC BY 4.0, B4 held
   until the G4 κ is known, B5 closed as superseded. Standards-audit B-table
   closure status filled in. The G4 procedure in `docs/human-review.md` was
   corrected — it still described a two-rater kappa + adjudication run that the
   2026-08-15 single-author-rater downgrade had already made impossible.

2. DONE 2026-09-14 — **G4 measured: FAIL.** κ = 0.537 (raw 0.813, n=150)
   against the prespecified κ ≥ 0.75. Per kind: fact_applied 0.605,
   scope_correct 0.561, **fact_absent 0.166**. The 14/14 aggregate symmetry is
   a CANCELLATION of two opposite kind-specific biases (judge over-accepts on
   all 8 absence-criterion errors, under-accepts on all 7 scope errors), not
   unbiased noise; the fact_absent κ is a base-rate artifact, since raw
   agreement there is 0.818, level with the other kinds. Corrected same-day in
   `docs/decision-log.md` after an initial misreading. Evidence:
   `datasets/dev/calibration/{rater-M-filled-2026-09-14.xlsx, ratings-M.json,
   judge-agreement.json}`; full entry in `docs/decision-log.md` §2026-09-14.
   Carried as a FAIL in the abstract, §4.4 and disclosure 1.

2b. **DECISION NEEDED from Mehul — what to do about the 28 sub-0.7 criteria.**
   The prespecified rule says drop them and disclose the count, never rewrite.
   25 of the 28 are "below 0.7" on a single sampled judgment, which the tooling
   itself calls a weak basis. Applying the rule means re-scoring the floor run
   with those criteria removed, which touches frozen artifacts and can move the
   371. Not doing it means declining a prespecified rule after seeing it bite.
   Both roads are defensible; only one of them is Mehul's to pick, and it is
   not the agent's. Nothing downstream proceeds until this is settled.

3. DONE 2026-09-14 — **Release packaging**: `scripts/release.py build|verify`
   (9 tests). Ships streams, twins, probes, valid sets, Croissant 1.0 + RAI
   metadata, CC BY 4.0 `LICENSE-DATA`, `MAINTENANCE.md` (re-anchoring as the
   maintenance contract), checksums, manifest. Withholds the ground-truth
   ledger (`org.json.facts`, 746 across the released seeds), probe plans,
   realization maps, annotated streams, holdout seeds, rater keys. `verify`
   fails on a leaked ledger, a missing canary, a tampered file, or any
   withheld filename. Proven runnable: the redacted bundle drives the real
   Runner to 125 base + 125 twin rows on seed 1, matching the frozen valid
   set. Remaining: hosting target + DOI (item 6).

4. **Remaining prose** on `paper/draft.md`: abstract, §1, §2 and §4.4 are
   drafted; §3, §5, §6, §7 and §8 are still sourced outlines. §7's 13
   disclosures need expanding into sentences. Then voice pass with Mehul
   (`unslop` is already applied to the public surfaces and guarded by
   `tests/test_prose_style.py`; `mehul-voice` comes last).

4b. **BLOCKING for §2** — verify every citation against its primary source.
   Six benchmark ids postdate the drafting agent's knowledge, the §2.3 numbers
   are secondary-sourced through our own audit notes, and one recorded URL
   (`github.com/milla-jovovich/mempalace/issues/29`) looks fabricated. The §2
   header note and `paper/checklist.md` carry the detail. Untraceable claims
   get cut, not softened.

5. **Verification gate** (`paper/checklist.md`): regenerate the floor numbers
   from committed raw outputs so nothing in the paper is hand-typed, grep the
   draft for surviving comparative language, confirm all 12 disclosures appear
   in prose, repro from a clean clone.

6. **Hosting + DOI** — pick the host (Zenodo gives a DOI; HuggingFace gives
   reach), then replace the `DOI_PLACEHOLDER` in `scripts/release.py`.

7. **B4 decision** (human performance baseline, ~20 probes × 2 people × 2h, no
   model access) — taken once the G4 κ is known.

8. OPTIONAL, when a successor worker is affordable — **re-anchor**: pin
   successor by the stated rule, re-run anchors seeds 1–3 under frozen gate
   rules, new valid set, then the pilot queue (the driver + judge pipeline are
   ready as-is). Procedure: FREEZE amendment + released `MAINTENANCE.md`.

## Standing cautions

- Worker pin: every protocol path runs with
  `MEMBENCH_CODEX_BIN=~/.local/codex-0.144.5/node_modules/.bin/codex`; PATH `codex` may be newer.
- cursor-agent: QA/non-protocol only (65% twin agreement — `docs/standards-audit.md` §A).
- Blinded judging always: `judge-export` → fresh judge agents that read only
  the batch file → `judge-import`; judge model ≠ worker model.
