# memory-bench: A Screened Benchmark Dataset and Validity Study for Organizational Memory in Agent Harnesses

**Status: consolidated skeleton, 2026-09-14.** Reframed from "pilot numbers"
to "dataset + construction methodology + validity study" after the pinned
worker (gpt-5.4) was deprecated provider-side mid-pilot (decision-log
2026-09-14; Mehul's explicit direction in-session). Every factual claim
carries its source so the prose pass can be checked line by line. Prose
style pass (with Mehul) comes after structure settles.

## Abstract (stub)

One paragraph: premise (org coherence can't live in plural vendor weights →
memory layer is the shared substrate); what we release (event-stream
benchmark: 3 screened simulated orgs, 371 valid paired probe instances,
counterfactual twins, hidden ground-truth ledgers, 2 unscreened holdout
seeds, full harness); the validity study (floor ≈ 0 under pair credit;
probe validity is task-model-relative; harness sensitivity 65%; judge
false-accept 2/41); and the durability finding (the pinned worker was
deprecated mid-study; we document the re-anchoring procedure that makes
the dataset outlive any single worker). Comparative system numbers are
explicitly out of scope for this paper.

## 1. Introduction

- Premise and mini-AGI operationalization: `docs/vision.md` §1–2.
- Claims discipline up front: this paper claims an *instrument*, not a
  leaderboard; no single aggregate anywhere (`docs/vision.md` §3, §5).
- Contributions:
  1. The dataset artifact (§3): screened, gated, twinned, with dated
     provenance corroborated by git history.
  2. The construction + screening methodology (§3): pair credit via
     counterfactual twins, blinded judging, G0–G5 gates, prespecified stats.
  3. The validity study (§4): floor validation, model-relativity, harness
     sensitivity, judge validation, human agreement (G4).
  4. The re-anchoring procedure (§4.6): what it takes to keep an agentic
     benchmark valid across worker deprecations — measured, not speculative.

## 2. Related work

- Memory benchmarks (LoCoMo, LongMemEval, letter-style long-context evals);
  why single-agent chat memory ≠ organizational memory (multi-witness
  events, per-principal visibility, temporal invalidation).
- Continual learning / knowledge editing; agent-org simulations.
- Benchmark-validity and benchmark-decay literature (ties §4.6 to prior art).

## 3. The dataset and how it was built

### 3.1 Event streams and probes
- Simulated org event streams (`docs/specs/event-stream.md`); witnessed
  per-principal delivery; counterfactual twin streams.
- Probe archetypes by capability-ladder rung: A4, A7 (rung 1), A1 (rung 2),
  A2 (rung 3) (`docs/specs/probe-spec.md` v0.4.3, `docs/vision.md` §3).
- Pair credit: an instance passes only if base AND twin sides pass
  (`docs/specs/probe-spec.md` §4) — guards against answering from priors.
- Streams carry no timestamps (`sim_time` null throughout; §7 item 11):
  temporal order is positional.

### 3.2 Screening and gates
- G0–G5 pipeline (`docs/dataset-plan.md`); what each gate screens.
- Blinded judging: opaque-id export → fresh judges → import; judge model ≠
  worker model ≠ criterion-author family (`AGENTS.md` hard rules).
- **Released dataset: seeds 1–3, 371 valid paired instances** (A1 50, A2 43,
  A4 106, A7 172; per-seed 125/131/115; cluster survival 46/54, 46/54,
  40/54; seed-3 instance gate carried as an explicit FAIL). Seeds 4–5
  unscreened holdouts. Freeze prespecified 2026-08-15, corroborated by git
  history (`docs/decision-log.md`).

### 3.3 Harness and worker pinning
- All screening ran under one pinned worker (gpt-5.4, effort medium,
  codex-cli 0.144.5); §4.2–4.3 give the measured reasons a pin is
  load-bearing, §4.6 what happens when the pinned worker dies.

## 4. Validity study — THE RESULTS CORE (all numbers already measured)

### 4.1 Gate results
- Per-gate outcomes by seed, failures carried as FAILs never repaired
  (`docs/validation-report.md`, `docs/decision-log.md`).

### 4.2 Probe validity is task-model-relative
- Ceiling-gate survival under identical strict rules: **37/54** clusters for
  gpt-5.4 vs **17/54** for gpt-5.4-mini (`docs/decision-log.md`, Phase 3).
  A "valid instance" is valid *for a worker*; the released valid set is
  defined relative to the screening worker, and the release documents the
  per-worker re-screening procedure.

### 4.3 Harness sensitivity
- Identical gpt-5.4 weights behind two agent harnesses agree on only
  **65%** of twin-ceiling outcomes (prespecified 60-run study, 2026-07-25;
  `datasets/dev/screening/harness-study-2026-07-25/`). The harness is part
  of the consumer; benchmark numbers without a harness pin are unanchored.

### 4.4 Judge validation
- 20-decoy false-accept audit: **2/41 measured, 0/39 adjudicated**
  (`datasets/dev/screening/judge-decoys/audit.json`), rubric v2.
- G4 human agreement: 150-pair author-rater packet — number lands when the
  packet returns; criteria < 0.7 dropped, never rewritten (single
  author-rater downgrade disclosed, §7 item 1).

### 4.5 Floor validation: pair credit filters priors
- The no-memory floor, run end-to-end through the full pilot pipeline on
  seed 1 (125 instances × base+twin, 250 blinded verdicts, judge
  `claude-sonnet-5-blinded-v2`): **rung 1 pair credit 0.022 (95% CI ±0.040,
  n=92), rung 2 0.118 (±0.217, n=17), rung 3 0.000 (n=16)**
  (`datasets/dev/pilot/nomemory/seed-1/score-k1/report.json`, commit
  5959c26). A memoryless worker scores ≈0: the instrument does not reward
  prior knowledge or generic competence.

### 4.6 Benchmark durability: the deprecation event and re-anchoring
- Timeline (all dated in decision-log/git): freeze 2026-08-15 → pilot runs
  began 2026-09-02 → provider deprecated gpt-5.4 for the available billing
  paths (observed as a hard 400 by 2026-09-14; runs stalled 2026-09-04).
- Consequence, derived from §4.2: screening anchors die with the worker;
  partial SUT rows under the dead worker cannot be mixed with a new one.
- The re-anchoring procedure (successor-model rule, re-run anchors under the
  frozen gate rules with byte-identical task text, new valid set, then
  evaluate): specified here as the release's maintenance contract.

## 5. The instrument as released

- Adapter interface + 10 registered system configs (4 baselines ± lexical
  ablation, top-4-by-stars market systems, Mem0 silo ablation), per-system
  configs frozen before any live run with dated mechanical amendments only
  (`docs/vendor-configs.md`).
- Run/score/figures pipeline (resumable runs, blinded judge round trip,
  cluster-robust SEs, ≥2/3-seed direction rule, cost columns; zero
  hand-typed numbers).
- Live-smoke findings (2026-09-02) as evidence the harness meets real
  vendor APIs: Supermemory tag/nulls/hybrid-search amendments, Graphiti
  0.29.3 embedded-Kuzu repairs — all availability-only, dated.

## 6. Partial pilot record (provenance, not results)

- What ran before the stall (commit 5959c26): nomemory complete + judged
  (→ §4.5); fulltranscript 125 base / 109 twin, grep 125/46, rag 0/34,
  rag-lexical 125/29 non-empty rows of 125.
- These rows are released as provenance under the dead worker pin; they are
  NOT comparative results and no system claim is made from them. Framed as
  an honest record of an interrupted prespecified pilot.

## 7. Limitations and disclosures (each becomes a sentence or two)

1. Single author-rater for G4 (has seen seed content); disclosed downgrade
   with the measured agreement number.
2. Rank-direction rule ≥2/3 seeds was prespecified for the pilot; unused in
   this paper (no comparative claims).
3. Seed-3 instance gate carried as FAIL; instances retained and marked.
4. Worker billing/auth changes during the study; model/binary pin held
   until provider deprecation ended all access (§4.6).
5. Market-system configs set internal LLMs to Gemini where configurable;
   deviations from vendor defaults named in `docs/vendor-configs.md`.
6. Shared-store configs do not enforce per-principal visibility; no leakage
   scoring in v1.
7. Silo ablation moved to Mem0 pre-run (full-transcript silo vacuous);
   dated in `docs/decision-log.md`.
8. Graphiti runs embedded Kuzu (deprecated upstream); adapter-side repairs
   documented.
9. Simulated orgs, not real logs; 3 screened seeds; single worker model.
10. Vendor right-of-reply: not triggered — this paper publishes no vendor
    numbers; the procedure remains specified for any re-anchored evaluation.
11. Event streams carry no timestamps; temporal order is positional;
    screening anchors never saw rendered timestamps.
12. Supermemory "dreaming" extraction is batched server-side; hybrid search
    mode documented (relevant to the released harness, not to any claim).

## 8. Release

Dataset (streams, twins, probes; ledger withheld per release policy),
harness, screening evidence, partial pilot rows, reproduction commands,
canary string, licenses. (G5 tracker: `docs/standards-audit.md` — nothing
ships with a BLOCKING row open.)

## Appendices (planned)

A. Probe spec + rubric verbatim. B. Screening gate results by seed.
C. Floor run detail + per-instance table. D. Re-anchoring procedure.
E. Reproduction commands.
