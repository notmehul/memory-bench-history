# memory-bench: A Screened Benchmark Dataset and Validity Study for Organizational Memory in Agent Harnesses

**Status, 2026-09-14.** Abstract and §1 are drafted prose; §2–§8 are still
sourced outlines. Reframed from "pilot numbers" to "dataset + construction
methodology + validity study" after the pinned worker (gpt-5.4) was deprecated
provider-side mid-pilot (`docs/decision-log.md` §2026-09-14). Every factual
claim carries its source so the prose can be checked line by line;
`tests/test_paper_numbers.py` asserts the headline numbers still match the
artifacts they came from. One value is outstanding: the G4 κ, marked
**[G4 pending]** below. Voice pass comes after the structure settles.

## Abstract

An organization's agents no longer run on one model: each person picks the
harness built for their work, and picks it *because* it is specialized. The
weights organizational knowledge must reach are therefore plural and
vendor-owned, so coherence cannot live in them — the memory layer is the only
substrate every harness shares. Of eleven published memory benchmarks we could
verify (§2), none measures whether a memory system holds that knowledge with
the right scope, authority, and freshness.

We release memory-bench, an instrument for that question, with the evidence
that it measures what it claims. The dataset is three simulated software
organizations: multi-week event streams delivered event-by-event to each
principal who witnessed them, a hidden ground-truth ledger, and behavioral
work tasks injected at evaluation time rather than quiz questions. Every probe
instance is paired with a counterfactual twin in which the probed fact differs
and the rest of the stream is byte-identical; an instance is credited only when
both sides pass, so an answer available from prior knowledge earns nothing.
Across three seeds, 371 instances survive a five-gate screening pipeline under
blinded judging; two further seeds are withheld unscreened as holdouts.

The validity study is this paper's result. A memoryless worker's pair credit
is statistically indistinguishable from zero on every capability rung, which
is direct evidence that the design does not reward priors. Probe validity is
*task-model-relative*: under identical strict rules, 37/54 probe clusters
survived the ceiling gate for one worker and 17/54 for a smaller sibling. The
harness is part of the consumer: identical weights behind two agent harnesses
agreed on only 65% of twin-ceiling outcomes. The blinded judge's false-accept
rate against an adversarial decoy set was 2/41 as measured and 0/39 after
adjudication, and judge–human agreement on a blinded 150-pair packet was
κ = **[G4 pending]**.

Mid-study, the provider deprecated the pinned worker, which ended comparative
evaluation and exposed a dependency every agentic benchmark carries and few
state: screening anchors are properties of a worker, not of the data. We report
the event, release the partial rows as provenance, and specify the re-anchoring
procedure that lets the dataset outlive any single worker. No comparative
system result is claimed anywhere in this paper.

## 1. Introduction

### 1.1 Organizational knowledge has no home in the weights

Organizations are getting smaller while the number of agents working inside
them grows, and the agents are not interchangeable. A developer's coding
agent, a designer's creative tool, and a generalist assistant differ in system
prompt, tools, and defaults, and each is chosen for those differences. This
heterogeneity is a property of the ecosystem rather than a transitional
untidiness to be standardized away (`docs/vision.md` §1).

One structural consequence follows. If the weights an organization runs on are
plural and vendor-owned, then organizational coherence cannot live in them.
The decisions, working rules, preferences, and commitments that make a company
act like one company have to be held somewhere every harness can reach, and
the memory layer is the only such place. On this view a memory system is not
an accessory to an organization's agents; it is the connective tissue.

The naive version of that idea does not work. Pooling every artifact and
giving every agent the same view produces a rumor mill with perfect recall,
not a collective intelligence. A personal preference is not org policy. A
leadership decision outranks a loud opinion. A superseded plan must stop
driving behavior while remaining retrievable. A need-to-know fact must not
diffuse. What makes an organizational world model useful is that it is
*scoped, tiered, and temporally correct*: each agent receives the context
appropriate to its principal and its task, at the current epoch of truth
(`docs/vision.md` §2).

### 1.2 What existing benchmarks measure instead

Published memory benchmarks overwhelmingly evaluate a single agent's recall
over a long conversation: can the system retrieve a fact it was told earlier.
That is rung 0 of the capability ladder this benchmark is organized around
(§3.1), it is table stakes, and long context saturates it. Organizational
memory differs along three axes that single-agent recall does not exercise:
events have multiple witnesses and per-principal visibility, facts carry tier
and authority so that conflicts have correct rather than arbitrary
resolutions, and facts are invalidated over time rather than merely
accumulated.

The gap is not only in coverage. §2 surveys the field's measurement failures —
answers guessable from priors, corpora answerable without memory at all,
corrupted ground truth producing impossible ceilings, judges that accept
topical waffle, protocols loose enough to support score disputes between
vendors. These are the reasons this paper spends most of its length on
validity rather than on results.

### 1.3 What we claim, and what we do not

This paper claims an *instrument*, not a leaderboard.

We claim that the released dataset measures organizational memory behavior at
rungs 1–3 of the ladder, for a two-team simulated software organization at L1–
L2 scale, under a stated worker pin; and we report the measurements that
support or qualify that claim, including the ones that qualify it. We do not
claim that any memory system is better than another — this paper publishes no
comparative system numbers. We do not claim to measure "mini-AGI-ness," and
the external-validity claim stops at the organization type instantiated;
industry breadth enters a later version as a designed factor rather than by
relabeling this one (`docs/vision.md` §5). No result is ever reduced to a
single aggregate score: results are grouped by capability rung, always.

Three constraints were fixed before the evidence they govern was produced, and
each is corroborated by dated git history rather than by assertion: the gate
criteria and scoring rules (`docs/dataset-plan.md`), the worker and judge pins,
and the commitment to carry failed gates as failures rather than repairing the
probes that failed them. That commitment has a visible price in this paper.
**All three released seeds fail the instance gate** (125, 131, and 115 valid
instances against a threshold of 135), and **seed 3's cluster gate also fails**
(40/54 surviving clusters). The instances are retained, marked,
and reported as failures rather than topped up, because a gate that is relaxed
once it binds was never a gate (`datasets/dev/org-0000N/g3-report.json`,
`docs/decision-log.md`).

### 1.4 Contributions

1. **A screened dataset** (§3): 371 valid paired probe instances across three
   simulated organizations, with counterfactual twins, hidden ground-truth
   ledgers, and two unscreened holdout seeds. Every gate result is dated and
   corroborated by commit history.

2. **A construction and screening methodology** (§3): pair credit via
   counterfactual twins; per-item floor and ceiling validity screening with a
   pinned worker; blinded judging with a versioned rubric where the judge model
   is never the worker model nor the family that authored the criteria; a
   five-gate pipeline; and a statistics protocol prespecified before any
   result existed.

3. **A validity study** (§4): the measurements that test whether the instrument
   works — floor validation, the task-model-relativity of probe validity,
   harness sensitivity, judge false-accept rate, and judge–human agreement.

4. **A durability procedure** (§4.6): what it takes to keep an agentic
   benchmark valid when the worker it was screened under disappears. We did not
   choose this contribution; the provider deprecated our pinned worker
   mid-study and we documented what that costs and how to recover from it.

### 1.5 What this paper does not contain

It contains no system comparison. The pilot that would have produced one had
completed the memoryless floor condition and partial rows for four further
baselines when the pinned worker became unreachable through every available
billing path (§4.6). Because probe validity is worker-relative (§4.2),
attaching a new worker's results to anchors measured under the old one would
break both the normalization and the pair-validity argument, so we did not do
it. The partial rows are released in §6 as provenance for an interrupted
prespecified pilot, carrying no comparative claim.

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
  40/54). **Gate outcomes carried as measured: all three instance gates FAIL
  (135 required); seed 3's cluster gate also FAILs.** No probe that failed a
  gate was repaired. Seeds 4–5 unscreened holdouts. Freeze prespecified
  2026-08-15, corroborated by git history (`docs/decision-log.md`).

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
3. All three released seeds fail the instance gate (125/131/115 against 135);
   seed 3 also fails the cluster gate (40/54). Instances retained and marked,
   never topped up or repaired.
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

Built and checked by `scripts/release.py build|verify`, so the bundle is
reproducible rather than hand-assembled and the withholding policy is
enforced by code.

- **Ships**: the SUT-facing streams, counterfactual twins, probes with their
  scoring assertions, the frozen valid sets, Croissant 1.0 + RAI metadata,
  `LICENSE-DATA` (CC BY 4.0; code stays MIT), `MAINTENANCE.md`, checksums, and
  a manifest naming what was withheld and why.
- **Withheld**: the ground-truth fact ledger (746 facts across the released
  seeds — it records which facts are probed and which are planted
  distractors), probe plans, realization maps, annotated scoring streams, the
  generator, the two unscreened holdout seeds, and every rater key.
- **Published on purpose**: the assertions. Scoring is impossible without
  them and a benchmark that hides its criteria cannot be audited; the cost is
  that the set is open-book by construction, which the withheld generator,
  the holdout seeds, and the embedded canary strings are the answer to.
- `verify` fails the release on a leaked ledger, a missing canary, a tampered
  file, or any withheld filename. Redaction is runnable-safe: the redacted
  bundle drives the real runner to the full frozen valid set (125 base + 125
  twin rows on seed 1).

(G5 tracker: `docs/standards-audit.md` — nothing ships with a BLOCKING row
open; rows 1–3 closed 2026-08-15, row 9 closed here bar hosting and the DOI.)

## Appendices (planned)

A. Probe spec + rubric verbatim. B. Screening gate results by seed.
C. Floor run detail + per-instance table. D. Re-anchoring procedure.
E. Reproduction commands.
