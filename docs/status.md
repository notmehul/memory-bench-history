# Status & Work Queue

Last updated: 2026-07-25 (session ending at commit `26343f6`). Update this
file whenever a queue item completes; keep entries dated.

## Where the project stands

- **G0–G1 PASSED**; **G2 machine-side complete** (human spot-check +
  read-throughs pending, packets ready in `datasets/dev/human-check/`).
- **Phase 3**: 810 probes (spec v0.3) across 5 orgs. Seed 1 fully screened
  under the final protocol with fully blinded judging: **45/54 clusters
  (cluster gate PASS at zero margin), 125 valid instances (instance gate
  explicit FAIL, structured twin-anchoring cause), strict 35**. Seeds 2–5
  probes final; screening blocked on codex quota.
- **Worker pinned**: (gpt-5.4, medium, codex-cli 0.144.5). Harness-sensitivity
  study committed (`datasets/dev/screening/harness-study-2026-07-25/`).
- **Consistency passes** done for all seeds; 2 filler defects found/fixed.
- **Phase 5 runner core** + NoMemory/FullTranscript(+silo) adapters built
  and tested; **Phase 4 calibration tooling** built (108-pair packet from
  seed 1; 150 needs seed 2+).
- **Independence protocol** adopted (no author-affiliated system; generic
  typed-memory reference impl; published inclusion criteria).
- **Standards audit** adopted 9 field learnings as dated amendments
  (`docs/standards-audit.md`); three BLOCKING items before headline numbers:
  judge decoy audit, statistics protocol (power analysis), scorer-exploit
  audit.

## Queue A — codex-quota-blocked (resets 2026-07-29; ~1.6 packs total)

| # | Item | Size | Notes |
|---|---|---|---|
| A1 | Seed-2 screening: fill 130 missing runs | 130 runs | 356/486 cached + prompt-verified in `datasets/dev/screening/org-00002/results.partial.jsonl`; manifest → seed work dir → `run` → blinded `judge-export` → sonnet judges → `judge-import` → `report` (commands in dataset-plan G3 note) |
| A2 | Seed-3 screening | 486 runs | full pipeline, blinded from the start |
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
| C1 | Scorer-exploit audit (BLOCKING) | degenerate outputs (empty / enumerate-all / topical waffle / base-side-only) through the scorer + blinded judge; publish results; expected pass via pair crediting — show it |
| C2 | Judge decoy set construction (BLOCKING) | deliberately wrong-but-topical outputs for G4 false-accept measurement; keep decoy authorship isolated from judging |
| C3 | Power-analysis script (BLOCKING) | from seed-1 screening variance; cluster-robust per Miller; sizes the pilot |
| C4 | Codex worker adapter for the runner | wraps the pinned worker behind `WorkerModel`; transport (file capture, timeout, retries) mirrors `screen_probes.py run` |
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
