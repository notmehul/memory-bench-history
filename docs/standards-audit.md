# Benchmark-Standards Audit — 2026-07-25

Comparison of memory-bench against (a) every published memory benchmark we
could verify, (b) the public vendor-evaluation controversies in this market,
and (c) formal benchmark-quality standards (BetterBench, the Agentic
Benchmark Checklist, NeurIPS Evaluations & Datasets requirements, the
445-benchmark construct-validity audit, Miller's error-bar canon). Compiled
from three sourced research reports; key sources at the end. This document
is the living pre-release tracker: nothing ships while a BLOCKING row is
open.

## A. Field failure modes we already control (mechanism in place)

| Failure mode (who got burned) | Our control |
|---|---|
| Answers guessable from priors / generator bias (LoCoMo, most synthetic sets) | Counterfactual twin pairing with pass-both-or-zero crediting; per-side floor passes reported as guessability, 1.0-guessability clusters flagged per cluster |
| Corpus answerable without memory (LoCoMo full-context 73% > Mem0 68%) | Per-probe memoryless floor with the pinned worker; probes failing the floor gate are dropped — item-level, stronger than corpus-level arguments |
| Corrupted ground truth, impossible ceilings (LoCoMo 6.4% bad gold, vendors scoring above the 93.6% ceiling) | Ground truth is a computable oracle (`B(principal,t)`, 70 hand-verified tests, mutation-checked); every probe's ceiling is *measured* with facts injected; instances failing ceiling are dropped |
| Judge infers desired outcome (LoCoMo judge 63% false-accepts on topical waffle) | Blinded judging: opaque row/criterion ids, judge never sees condition, side, or ids; judge ≠ worker, cross-provider; full seed-1 blinded re-judge with agreement published (97.6%) |
| Probes visible at ingestion / teaching to the test (MemPalace) | Probes injected only at eval time; ledger private; canary strings in streams; salience linting + blinded-rater protocol so probed facts aren't typographically special |
| Single aggregate hides trade-offs (universal) | Radar by capability rung, never one score; propagation/leakage adversarial by design |
| Static public set rots, no holdout (LoCoMo; almost everyone) | Seeded generator mints fresh orgs; G5 release = 3 public + 2 holdout, generator withheld; regeneration is the contamination story |
| Unspecified protocol enables score wars (Zep 58/75/"84") | One scoring rule, one denominator, prespecified gates with dated amendments; screening evidence + report reproducible from committed artifacts |
| Off-policy paste-the-history evaluation (MemoryAgentBench critique) | Runner ingests per-principal, event-by-event, incremental — deployment-shaped |
| No prespecification (universal) | Hypotheses, gates, and protocol changes dated in-repo before evidence; provenance note distinguishes commit-verifiable prespecification |

## B. Gaps adopted 2026-07-25 (recorded as dated Phase 5/4 amendments)

| # | Gap (source) | Action adopted |
|---|---|---|
| 1 | Judge false-accept rate unmeasured — BLOCKING (Penfield audit; ABC O.c.1) | Phase 4 gains an adversarial decoy set: deliberately wrong-but-topical outputs; published false-accept rate; feeds the tie rule |
| 2 | Statistics underspecified — BLOCKING (BetterBench most-failed; Miller 2024) | Prespecified stats protocol: cluster-robust SEs (probes cluster within fact clusters/orgs), paired per-item system comparisons, K resamples per probe, pre-pilot power analysis, tie rule for deltas inside the noise band |
| 3 | Scorer never audited vs degenerate strategies — BLOCKING (ABC; τ-bench +38% empty-answer flaw) | Scorer-exploit audit before any SUT run: empty / enumerate-everything / topical-waffle / base-side-only outputs must score ≤ floor; results published |
| 4 | No trivial-tools baseline (Letta grep agent 74% on LoCoMo) | Baseline #8: filesystem+grep agent — memory products must beat it |
| 5 | Sub-memory confounds (MemDelta: embedding swap > architecture swap) | Embedding model pinned + reported for all RAG-class baselines; one alternate as ablation; no "memory" attribution without component ablation |
| 6 | Cost/latency omitted or gamed (Mem0/Zep latency fight; MemDelta 50× cost parity) | Mandatory columns: ingestion/write tokens, query tokens, $ and latency at disclosed concurrency, next to every accuracy number |
| 7 | Competitor misconfiguration wars (Mem0↔Zep role/timestamp errors) | Vendor fairness protocol: written vendor-recommended configs frozen pre-run; versions pinned; identical prompts/templates; raw per-question results + harness to vendors with a right-of-reply window, responses published verbatim |
| 8 | New benchmark unanchored to the field (BenchBench) | Benchmark agreement testing: rank-correlation of pilot rankings vs published LoCoMo/LongMemEval results where available; divergence on rungs 2–3 is the expected, prespecified finding |
| 9 | Release compliance (NeurIPS E&D: Croissant + RAI metadata, license, hosting, maintenance plan; GateMem's tiered leaderboard verification) | Added to the G5 release gate as hard requirements |

### Closure status (updated 2026-09-14; the table above is the dated adoption record, unedited)

| # | Status |
|---|---|
| 1 | CLOSED 2026-08-15 — 20-decoy audit, 2/41 measured and 0/39 adjudicated (`datasets/dev/screening/judge-decoys/audit.json`). No longer BLOCKING |
| 2 | CLOSED 2026-08-15 — stats protocol prespecified and implemented (`scripts/score_sut.py`, `docs/power-analysis.md`). No longer BLOCKING |
| 3 | CLOSED 2026-08-15 — scorer-exploit audit rebuilt on the frozen canon (`datasets/dev/screening/exploit-audit/`). No longer BLOCKING |
| 4 | BUILT, NOT RUN — grep-agent baseline is registered and frozen; the comparative run died with the worker (FREEZE amendment 2026-09-14) |
| 5 | BUILT, NOT RUN — embedding pinned and reported (`gemini-embedding-001`); the ablation needs runs |
| 6 | BUILT, NOT RUN — cost columns are implemented in the runner and carried on every row |
| 7 | NOT TRIGGERED 2026-09-14 — right-of-reply attaches to published vendor numbers and v1 publishes none; configs stay frozen and dated in `docs/vendor-configs.md` |
| 8 | DEFERRED 2026-09-14 — no rankings to correlate without comparative runs |
| 9 | CLOSED 2026-09-14 — `scripts/release.py build/verify` produces the bundle with Croissant 1.0 + RAI metadata, CC BY 4.0 data license, maintenance plan, checksums, and a verifier that fails on a leaked ledger, a missing canary, a tampered file, or any withheld filename. Hosting: HuggingFace `notmehul/memory-bench`, dataset card with metadata, no DOI (decided; the paper cites the URL). Uploaded private 2026-09-14, leak-audited before and round-tripped byte-for-byte after; anonymous access 401. No BLOCKING row remains open. |

## C. Open decisions (owner: Mehul)

1. **Human baseline on a probe subsample** (Bowman & Dahl; BetterBench): have 1–2 humans do ~20 probes with ceiling context to report a human reference band. Recommended; cost is a few hours of two people's time.
2. **Second judge family** for the pilot (judge-ensemble variance as part of the noise band) vs single calibrated judge + decoy audit. Recommended: decoy audit first; add second judge only if false-accept > ~5%.
3. **On-policy limitation wording**: our probes are behavioral work tasks (on-policy-shaped) but ingestion is a fixed stream (off-policy writes). AMemGym shows rankings can shift on-policy. Proposed: state as explicit limitation; closed-loop tasks go to v2.

## D. What the field lacks that we should not dilute

Per-item floor/ceiling validity screening with a pinned worker, counterfactual
twins with pair crediting, salience-linted rendering, a computable belief
oracle, and a regenerable holdout are each rare-to-absent in the surveyed
literature; together they are the paper's methodological contribution. No
adopted item above replaces them; they are the reason the adopted items can
be satisfied cheaply.

## Key sources

Mem0/Zep dispute: blog.getzep.com/lies-damn-lies-statistics…, github.com/getzep/zep-papers/issues/5 · Letta grep result: letta.com/blog/benchmarking-ai-agent-memory · LoCoMo audit: penfieldlabs.substack.com/p/we-audited-locomo… · MemPalace teardown: github.com/milla-jovovich/mempalace/issues/29 · Benchmarks: arXiv 2402.17753 (LoCoMo), 2410.10813 (LongMemEval), 2605.12493 (V2), 2506.21605 (MemBench), 2507.05257 (MemoryAgentBench), 2602.16313 (MemoryArena), 2606.18829 (GateMem), 2606.14571 (StreamMemBench), 2604.17283 (HorizonBench), 2510.01353 (MEMTRACK), 2606.29914 (MemDelta) · Standards: arXiv 2411.12990 (BetterBench), 2507.02825 (ABC), 2511.04703 (construct-validity audit), 2411.00640 (Miller, error bars), 2503.01747 (small-n CIs), 2407.13696 (BenchBench), 2306.05685 (LLM-as-judge), 2405.00332 (GSM1k holdout), 2406.19314 (LiveBench), neurips.cc/Conferences/2026/CallForEvaluationsDatasets.
