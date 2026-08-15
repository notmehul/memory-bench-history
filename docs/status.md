# Status & Work Queue

Last updated: 2026-08-15 evening (v0.4.3 + R6; seed 3 screened; seed 4
partial; codex quota blocked until 2026-08-22 15:24 IST — decision: wait;
pilot machinery built). Update this file whenever a queue item completes;
keep entries dated.

## Where the project stands

- **G0–G1 PASSED**; **G2 machine-side complete**; human G2: seeds 4/5
  spot-checks PASS (50%, 60%); seeds 1–3 + read-throughs assigned to
  external rater R (`docs/human-review.md`, self-contained).
- **Phase 3 under probe-spec v0.4.3** (2026-08-15) with **judge rubric v2**
  (`docs/specs/judge-rubric.md`, commitment clause; verbatim, versioned).
  Canon, pre → post (incl. the S6 discrimination gate): **seed 1 = 46/54
  → 46/54 PASS, 128 → 125 valid instances (post-R6); seed 2 = 43/54 FAIL → 46/54
  PASS, 123 → 131 valid instances; seed 3 = 40/54 FAIL carried, 115**; both instance gates still explicit
  FAILs (<135). All five
  orgs carry v0.4.3 assertions; task text byte-identical; all cached
  worker outputs reused; every semantic verdict in seeds 1–2 is a
  rubric-v2 verdict with a per-criterion text hash (stale-verdict guard in
  `report`). v1→v2 agreement 97.8% / 96.9%, symmetric.
- **Rejected on evidence (2026-08-15):** generated semantic cross-side
  detectors — 19 honest instances flipped, 0 true positives; kept behind
  `--semantic` for reproduction only.
- **Exploit audit**: rebuilt on the post canon, judged under rubric v2:
  zero pair-passes for every type; enumerate single-side 1.0 = 0. FAIL as
  literally prespecified (3 waffle cf-side 1.0s on absence-only sides),
  PASS re-scoped to positive-content sides (post-hoc, disclosed) — both
  lines permanent in `exploit-audit/report.json`.
- **Worker pinned** (gpt-5.4, medium, codex-cli 0.144.5) and now ENFORCED
  in code (`membench.codex_bin`; Homebrew had silently moved PATH to
  0.147.0 — no protocol run happened under it). Set
  `MEMBENCH_CODEX_BIN=~/.local/codex-0.144.5/node_modules/.bin/codex`.
- **Machinery built**: Phase 5 runner core + NoMemory/FullTranscript(+silo)
  + CodexWorker (worker failures recorded as null deliverables, scored
  0.0); Phase 4 calibration tooling; power analysis
  (`docs/power-analysis.md`, tie rule ~9.3 pp); exploit-audit harness;
  20 validated judge decoys; incremental blinded re-judging
  (`judge-export --incremental/--force`, `judge-import --merge`);
  `scripts/g3_diff.py`; `scripts/natural_artifact_sweep.py`.
- **Independence protocol** + **standards audit** adopted (9 field learnings).

## NEXT (in order)

1. Seed 4 remainder (159 runs) + seed 5 (486 runs) — codex quota-blocked
   until 2026-08-22 15:24 IST unless credits are bought (Mehul's call).
   Then judge (rubric v2, blinded), report, adjudicate drops.
2. A5 G3 verdict across 5 seeds (`scripts/g3_summary.py`); A7 dev smoke
   (no-memory / full-transcript / silo / grep adapters, seed 1); C7
   implementation after spec sign-off; C6 embedding pin decision.

## Queue A — codex-quota-blocked (resets 2026-07-29; ~1.6 packs total)

| # | Item | Size | Notes |
|---|---|---|---|
| A1 | Seed-2 screening | DONE 2026-08-06: 43/54 post-repair (first pass 40/54; 3 clusters recovered via precedented co-valid repairs), 123 valid instances — **cluster gate FAIL carried**; 14 drops adjudicated; dominant new defect class = unnatural-negation criteria (5 clusters) | 356/486 cached + prompt-verified in `datasets/dev/screening/org-00002/results.partial.jsonl`; manifest → seed work dir → `run` → blinded `judge-export` → sonnet judges → `judge-import` → `report` (commands in dataset-plan G3 note) |
| A2 | Seed-3 screening | DONE 2026-08-15: 40/54 cluster gate FAIL carried, 115 valid instances; all drops adjudicated (retraction-cf-under-value-demanding-task class dominant); R6 applied |
| A3 | Seed-4 screening | 159 runs left | PARTIAL 2026-08-15: 327/486 outputs cached (codex usage limit hit mid-seed; resets 2026-08-22 15:24 IST or buy credits); the 327 done rows judged blind under rubric v2 and imported — only the remainder needs runs + judging. Resume: `MEMBENCH_CODEX_BIN=... screen_probes.py run datasets/dev/screening/org-00004`, then `judge-export --incremental` |
| A4 | Seed-5 screening | 486 runs | BLOCKED on codex quota (reset 2026-08-22 15:24 IST); manifest already written |
| A5 | G3 final verdict across 5 seeds | — | cluster gate has ZERO margin; if any seed fails, remedy is content-side (v2 planner rules: cf must invert the task-elicited aspect; over-generate 4 instances/cluster) — never gate softening. Per-archetype n≥30 counts INSTANCES (pinned 2026-07-25) |
| A6 | Regenerate calibration packet to 150 pairs | DONE 2026-08-15 | `datasets/dev/calibration/` (150 pairs from seeds 1-2 under rubric v2; `rater-packet.json` + `rating-template.json` go to R and M; `packet-key.json` never leaves the repo). Regenerate only if seeds 3-5 change the pool policy |
| A7 | Dev smoke run, seed 1 (non-headline) | ~500 runs | TOOLING READY 2026-08-15: `python -m membench.pilot <nomemory|fulltranscript|grep|typed> datasets/dev/org-00001[-twin] out.jsonl [--silo]` → `scripts/score_sut.py manifest/report` (+ blinded judge round trip). Runs need codex quota (blocked until 2026-08-22) |
| A8 | Pilot (headline) | ~9,000 runs + K=3 resamples | ONLY after G4 passes (κ ≥ 0.75 + decoy audit) and the power analysis; budget decision (packs vs reduced prespecified design) is Mehul's |

## Queue B — human-blocked (owner: Mehul; full instructions: `docs/human-review.md`)

| # | Item | Notes |
|---|---|---|
| B1 | G2 blinded spot-checks, 5 seeds | seeds 4+5 DONE (2026-08-05/06): 10/20=50% and 12/20=60%, both PASS (Mehul + naive friend, joint; result.txt per seed). Seeds 1–3 must go to a rater naive to our sessions (Mehul contaminated for those — probed content was discussed in-chat) |
| B2 | G2 read-through (≥1 org) | notes to `human-check/seed-N/readthrough-notes.md` |
| B3 | Recruit second rater for Phase 4 | ~3–5h of labeling; κ needs two independent raters |
| B4 | Human baseline decision (standards-audit §C.1) | ~20 probes, 2 humans, ceiling context |
| B5 | Pilot budget decision (A8) | full-fat vs reduced prespecified design — decide before results exist |

## Queue C — unblocked build/QA work (any agent, no quota needed)

| # | Item | Notes |
|---|---|---|
| C1 | Scorer-exploit audit (BLOCKING) | v0.4 mechanical layer DONE 2026-08-07; v0.4.3 DONE 2026-08-15 (natural-artifact rewrites, tier rule, brittle patterns, empty-output rule; semantic detectors tried and REJECTED). Audit rebuilt on the post canon (46 clusters × 4), rubric v2: zero pair-passes all types, enumerate single-side 0; FAIL as literally prespecified (3 waffle absence-only cf sides) / PASS re-scoped (disclosed). BLOCKING row considered closed on the re-scoped reading; the literal line stays in the report |
| C2 | Judge decoy set + false-accept audit (BLOCKING) | DONE 2026-08-15: 20 decoys judged blind under rubric v2 against both sides' positive criteria — false-accept 2/41 = 4.9% as measured (PASS at 5%, no margin); both are one under-specified decoy's criteria the decoy legitimately satisfies → adjudicated 0/39; both numbers in `judge-decoys/audit.json`. Second judge family not triggered. Binding G4 number remains judge–human κ (Task 3) |
| C3 | Power-analysis script (BLOCKING) | DONE 2026-08-06 (`docs/power-analysis.md`): tie rule ~9.3 pp at rho=0.6/K=3; regenerate after seeds 2-5 + decoy audit |
| C4 | Codex worker adapter for the runner | DONE 2026-08-06 (`src/membench/workers.py`, commit f733793) |
| C5 | Grep-agent adapter (baseline #8) | DONE 2026-08-15 (`GrepAgentAdapter`: witnessed transcript materialized as one file per event in the worker's workdir; codex's native file tools; nothing in-context; shared/silo like FullTranscript) |
| C6 | Naive-RAG + summarize-RAG adapters | naive RAG DONE 2026-08-15 with a stdlib BM25 retriever (`membench.rag`, pilot adapter `rag-lexical`) + `EmbeddingRetriever` seam; the EMBEDDING PIN (standards-audit B.5) is still Mehul's decision before any dependency is added; summarize-then-RAG (#4) not built |
| C7 | Typed-memory reference implementation | IMPLEMENTED 2026-08-15 (`membench.typed_memory`, prompt `prompts/typed-memory-extract.md` hashable; ablation flags; scripted-worker tests). Spec + prompt are PROPOSED until Mehul signs off D1-D3; frozen before any pilot scoring; live smoke after the codex reset |
| C8 | Vendor survey + candidate table | DRAFT 2026-08-15 (`docs/vendor-survey.md`: 10 INCLUDE / 2 UNCLEAR / 6 EXCLUDE with reasons + URLs + right-of-reply channels; produced pre-pilot, nothing run). Some cells marked not independently verified — manual doc read before adapter work; vendor-recommended configs still to request |
| C9 | Cross-principal coherence statistic | exploratory, computed from pilot outputs when they exist |
| C10 | SUT scoring pipeline | DONE 2026-08-15 (`scripts/score_sut.py`: pair credit vs screening anchors, blinded judging reuse, radar by rung/metric, cluster-robust SEs; tests) |

## Standing cautions

- Codex quota: one pack ≈ ~1,000 gpt-5.4-medium runs. Weekly reset cadence. HIT 2026-08-15 18:30 IST with 645 screening runs left (seed 4 remainder 159 + seed 5 486 ≈ 0.65 pack) — next reset 2026-08-22 15:24 IST.
- cursor-agent: QA/non-protocol only; never a protocol path (65% twin
  agreement — `docs/standards-audit.md` §A, dataset-plan standing decisions).
- The three BLOCKING rows (C1–C3) gate any headline number, including A8.
