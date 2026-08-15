# Status & Work Queue

Last updated: 2026-08-07 (session ending at commit `ff1cb11`). Update this
file whenever a queue item completes; keep entries dated.

## Where the project stands

- **G0–G1 PASSED**; **G2 machine-side complete**; human G2: seeds 4/5
  spot-checks PASS (50%, 60%); seeds 1–3 + read-throughs assigned to
  external rater R (`docs/human-review.md`, self-contained).
- **Phase 3 under probe-spec v0.4** (PI-approved 2026-08-07): mechanical
  layer done — commitment rule + refined cross-side detectors (R1–R5, flip
  adjudication found 0/11 true positives). Canon: **seed 1 = 46/54 PASS
  (margin 1), 128 valid instances; seed 2 = 43/54 cluster gate FAIL
  carried, 123 valid instances**; both instance gates FAIL carried. Zero
  detector/hedge fires on any honest run; all reports reproduce from
  committed evidence. Cross-org co-valid lineage repairs applied to all
  orgs (orgs 3–5 pre-evidence).
- **Exploit audit**: empty/waffle/base_correct clean; enumerate_all
  residual 18 pair-passes (duration-valued / uncoverable sides) — assigned
  to the v0.4.3 semantic wave.
- **Worker pinned** (gpt-5.4, medium, codex-cli 0.144.5); harness study
  committed. **Consistency passes** all seeds (2 defects fixed).
- **Machinery built**: Phase 5 runner core + NoMemory/FullTranscript(+silo)
  + CodexWorker; Phase 4 calibration tooling; power analysis
  (`docs/power-analysis.md`, tie rule ~9.3 pp); exploit-audit harness;
  20 validated judge decoys.
- **Independence protocol** + **standards audit** adopted (9 field learnings).

## NEXT (in order)

1. **v0.4 item-3 semantic wave**: natural-artifact re-authoring of the
   negation-class criteria (all 5 orgs, codex authoring + fresh blinded
   judging; may flip seed-2 gate — report pre/post forever); per-cluster
   semantic anti-enumeration criteria for the 18 residual + 2 defective
   twin sides; asymmetric lineage cases (org-1 P-0023, org-4 P-0040) via
   authored replacements; org-2 latent sweep; `_check_assertion` `-cs`
   exemption; empty-SUT-output scoring rule.
2. Re-run exploit audit → bar must PASS. Re-report seeds 1–2 (post-item-3
   canon, side by side with pre).
3. Seeds 3–5 screening (blinded pipeline; ~1,460 codex runs).
4. Then Queue A6–A8 / Queue C4–C9 as listed.

## Queue A — codex-quota-blocked (resets 2026-07-29; ~1.6 packs total)

| # | Item | Size | Notes |
|---|---|---|---|
| A1 | Seed-2 screening | DONE 2026-08-06: 43/54 post-repair (first pass 40/54; 3 clusters recovered via precedented co-valid repairs), 123 valid instances — **cluster gate FAIL carried**; 14 drops adjudicated; dominant new defect class = unnatural-negation criteria (5 clusters) | 356/486 cached + prompt-verified in `datasets/dev/screening/org-00002/results.partial.jsonl`; manifest → seed work dir → `run` → blinded `judge-export` → sonnet judges → `judge-import` → `report` (commands in dataset-plan G3 note) |
| A2 | Seed-3 screening | 486 runs | v0.4 APPROVED 2026-08-07; fixes 1-2 implementing (mechanical); screening starts after flip adjudication + item-3 re-authoring |
| A3 | Seed-4 screening | 486 runs | " |
| A4 | Seed-5 screening | 486 runs | " |
| A5 | G3 final verdict across 5 seeds | — | cluster gate has ZERO margin; if any seed fails, remedy is content-side (v2 planner rules: cf must invert the task-elicited aspect; over-generate 4 instances/cluster) — never gate softening. Per-archetype n≥30 counts INSTANCES (pinned 2026-07-25) |
| A6 | Regenerate calibration packet to 150 pairs | — | pool `datasets/dev/screening/org-0000{1,2,...}` via `scripts/calibration.py sample` once ≥2 seeds screened |
| A7 | Dev smoke run, seed 1 (non-headline) | ~500 runs | long-context + grep + silo adapters through the runner; first real curves; labeled dev, never headline |
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
| C1 | Scorer-exploit audit (BLOCKING) | v0.4 mechanical layer DONE 2026-08-07 (commitment rule + refined cross-side detectors, R1-R5 adjudicated; canon unchanged 46/128, 43/123; zero honest fires). Residual: enumerate_all 18 pair-passes (duration-valued/uncoverable sides) + 2 known defective twin sides — ALL assigned to v0.4.3 semantic layer (item-3 wave, next). Empty-SUT scoring rule still pending before A7/A8 |
| C2 | Judge decoy set construction (BLOCKING) | DONE 2026-08-06: 20 validated decoys in `datasets/dev/screening/judge-decoys/` (third values, zero discriminative tokens either side); never judged — reserved for Phase 4 false-accept audit |
| C3 | Power-analysis script (BLOCKING) | DONE 2026-08-06 (`docs/power-analysis.md`): tie rule ~9.3 pp at rho=0.6/K=3; regenerate after seeds 2-5 + decoy audit |
| C4 | Codex worker adapter for the runner | DONE 2026-08-06 (`src/membench/workers.py`, commit f733793) |
| C5 | Grep-agent adapter (baseline #8) | worker + file read/search tools over witnessed transcript |
| C6 | Naive-RAG + summarize-RAG adapters | needs embedding-model pin decision (standards-audit B.5) — flag to Mehul before adding any dependency |
| C7 | Typed-memory reference implementation | generic (typed nodes, tier/scope metadata, source-backed updates, supersession); spec+prompts frozen before pilot scoring; ablation planned |
| C8 | Vendor survey + candidate table | Mem0/Zep/Letta/LangMem/Cognee/…; inclusion criteria in dataset-plan; written vendor-recommended configs; right-of-reply contacts |
| C9 | Cross-principal coherence statistic | exploratory, computed from pilot outputs when they exist |

## Standing cautions

- Codex quota: one pack ≈ ~1,000 gpt-5.4-medium runs. Weekly reset cadence.
- cursor-agent: QA/non-protocol only; never a protocol path (65% twin
  agreement — `docs/standards-audit.md` §A, dataset-plan standing decisions).
- The three BLOCKING rows (C1–C3) gate any headline number, including A8.
