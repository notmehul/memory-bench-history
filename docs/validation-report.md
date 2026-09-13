# v1 Dataset Validation Report

> **Note 2026-08-28:** this report covers the construction of all 5 dev
> orgs. The v1 pilot evaluates seeds 1–3 only (v1 FREEZE, `docs/dataset-plan.md`);
> seeds 4–5 are unscreened holdouts.

Final validation of the five dev orgs and their counterfactual twins,
2026-07-18. Every check below runs from the committed artifacts via
`scripts/validation_sweep.py` and `scripts/blind_check.py`.

## Clean-room sweep

Per stream: structure equals deterministic regeneration (canonicals aside),
realization check, gate G1 (schema + oracle cross-checks + ambiguity scan +
interleaving), and the release-blocking stream lint (marker round-trip,
visibility, salience permutation tests, noise floor, canaries).

```
seed 1: struct=OK realization=OK G1=OK stream=OK (salience p: 0.85/0.502/1.0, noise 0.85)
  twin 1: stream=OK coords=OK (salience p: 0.136/0.303/1.0)
seed 2: struct=OK realization=OK G1=OK stream=OK (salience p: 0.124/0.344/1.0, noise 0.87)
  twin 2: stream=OK coords=OK (salience p: 0.414/0.977/1.0)
seed 3: struct=OK realization=OK G1=OK stream=OK (salience p: 0.254/0.746/1.0, noise 0.87)
  twin 3: stream=OK coords=OK (salience p: 0.459/0.438/1.0)
seed 4: struct=OK realization=OK G1=OK stream=OK (salience p: 0.165/0.533/1.0, noise 0.87)
  twin 4: stream=OK coords=OK (salience p: 0.301/0.06/1.0)
seed 5: struct=OK realization=OK G1=OK stream=OK (salience p: 0.054/0.78/1.0, noise 0.86)
  twin 5: stream=OK coords=OK (salience p: 0.134/0.084/1.0)

SWEEP: ALL GREEN   (unit tests: 95 passed; ruff: clean)
```

## Blinded rater protocol (machine)

Prespecified protocol: one adversarial rater per seed (GPT-5.4 via codex,
isolated working directory containing ONLY the 20-excerpt sample — earlier
runs that gave raters repository access were discarded after one rater
scored 20/20 by reading the ledger). Samples: 10 probed + 10 distractor
spans, no same-topic siblings. Aggregate binomial test against chance at
α = 0.05.

| Seed | Rater accuracy |
|---|---|
| 1 | 8/20 (40%) |
| 2 | 12/20 (60%) |
| 3 | 14/20 (70%) |
| 4 | 12/20 (60%) |
| 5 | 12/20 (60%) |

**Aggregate: 58/100 = 58%, binomial p = 0.067 → not significantly above
chance. Protocol PASSES.**

### Known limitation: seed 3

Seed 3 scored 14/20 on four independent samples (including after two
targeted content revisions), a repeatable single-seed signal
(42/60 across the first three, p ≈ 0.001). An explain-the-leak analysis
attributed it to subject-shape and topic-domain differences (probed facts
read as binding policies over governed classes; some distractors read as
artifact/process trivia). Two content passes (numeric parity, binding-policy
reshaping of all 59 distractor rules) did not remove it. Seed 3 ships
with this documented residual; users running salience-sensitive analyses
should prefer seeds 1/2/4/5 or regenerate seed 3 under a future generator
version. The realization rules that close the tells found so far are
codified in `prompts/canonical-realization.md`.

## Phase 3: probe construction + validity screening (2026-07-22)

**Construction (all 5 orgs): COMPLETE.** 54 clusters × 3 instances × 5 orgs
= 810 probe instances in `datasets/dev/org-0000N/probes.jsonl`. Every
instance is oracle-revalidated (targets ∈ B — or B_hist for historical —
must_not_use ∈ B_hist, A4 winners re-derived via `resolve_precedence`).
Task text and assertions were LLM-authored under
`prompts/probe-authoring.md` and accepted only after mechanical
validation: answer-token hygiene lint, 4-gram overlap lint, and pattern
cross-validation (each pattern must match every numeral/word surface
variant of its own side and no variant of the other side, and no sibling
fact). The authoring loop converged in ≤3 attempts per org.

**Screening (seed 1, final protocol, blinded re-judge 2026-07-25;
lineage repairs 2026-08-06): 486/486 gpt-5.4 task-model runs; 46/54
clusters survive, shipping 128 valid instances**
(`datasets/dev/org-00001/g3-report.json`, raw evidence in
`datasets/dev/screening/org-00001/`). The 2026-08-06 cross-org co-valid
lineage sweep found latent defective assertion pairs in two seed-1
survivors (P-0032, P-0023-family) and in the dropped P-0041; symmetric
removal under the precedented rule — applied blind to direction, with
the stated risk that floor-pair flips could move numbers DOWN —
re-scored from cached outputs and verdicts to 46/54 and 128 instances:
P-0041 recovered (its blinded-re-judge drop traced substantially to its
own defective criterion pair, refining the earlier "marginal probe"
adjudication), P-0032's pilot-time fairness risk eliminated. Gate G3:
cluster floor PASS (46 ≥ 45, margin one); instance floor **FAIL** (128 < 135, carried as an
explicit FAIL — the shortfall is structured, not noise: it is the
residual tail of twin-side counterfactual anchoring failure, the same
family that drives cluster drops; v2 over-generates 4 instances/cluster
and requires counterfactuals to invert the task-elicited aspect). Strict
all-instances rule for comparison: 35/54. Mean per-side floor
guessability 0.33; 7 surviving clusters have guessability 1.0 (their
discriminative power lives entirely on the counterfactual side — valid
under pair crediting, per-cluster values in the report; users scoring
sides independently must exclude them).

Judging is **blinded and single-provenance**: all 1,092 semantic verdicts
by claude-sonnet-5 through opaque-id export (the judge sees only output +
criterion — never probe ids, floor/ceiling/twin condition, or
base-vs-counterfactual side; harness-enforced in `screen_probes.py`).
An earlier unblinded pass (46/54 survivors, including 6 verdicts by a
fallback judge from the authoring model family) is retained in git
history for comparison: blinded agreement 97.6% (26/1,092 flips; 14
True→False vs 12 False→True, so no systematic direction). The two
clusters the blinded pass additionally dropped (P-0037, P-0041) had been
independently flagged as marginal by an item-level audit before the
blinded verdicts landed — convergent evidence that the drops are probe
defects, not judge noise. A post-screening adjudication (2026-07-25)
recovered P-0023 and repaired one P-0032 assertion pair under the
co-valid-sibling rule (identical defect class and treatment as the
precedented P-0031/40/41 repairs; task text byte-identical, so all
cached task-model outputs remain valid).

**Seed 2 (2026-08-06) and probe-spec v0.4.3 re-scoring of seeds 1–2
(2026-08-15).** Seed 2 screened fully blinded: 43/54 (cluster gate FAIL
carried), 123 valid instances, dominant defect class = unnatural-negation
criteria. The v0.4.3 semantic layer (natural-artifact rule in operational
form, tier rule for sibling guards, brittle-pattern replacements, empty-
output rule, S6 discrimination gate) and judge rubric v2 (commitment
clause, verbatim in `docs/specs/judge-rubric.md`) were then applied to
all five orgs; seeds 1–2 were re-scored from the identical cached worker
outputs (prompt equality verified) with every semantic verdict re-judged
blind under v2. **Canon as of 2026-08-15 (this paragraph): seed 1 = 46/54
PASS, 126 valid instances (strict 34); seed 2 = 46/54 PASS, 131 valid
instances (strict 39); both instance gates FAIL (<135).**

> **Superseded later the same day (noted 2026-09-14).** The R6
> contested-attribute rule re-scored seeds 1–3 mechanically and took seed 1
> from 126 to 125 valid instances (strict 34 → 33); seeds 2–3 gates unchanged
> (`docs/decision-log.md` §2026-08-15, R6). **Frozen canon: seed 1 46/54, 125
> (strict 33); seed 2 46/54, 131 (strict 39); seed 3 40/54, 115 (strict 35) —
> 371 total.** The committed `datasets/dev/org-0000N/g3-report.json` files are
> authoritative and carry these numbers; the paragraph above is kept as the
> dated record of the intermediate state. v1→v2 verdict agreement on
unchanged criteria 97.8% / 96.9%, symmetric. Two designs were tried and
rejected on evidence the same day: generated semantic cross-side
detectors (0/19 true positives) — see the spec changelog. The
scorer-exploit audit, rebuilt on the post canon under rubric v2, shows
zero pair-passes for every degenerate type and zero enumerate single-side
1.0s (from 27 pairs / 23 single sides at first audit); it reads FAIL as
literally prespecified (three waffle cf-side 1.0s, all absence-only
sides created by the natural-artifact rule) and PASS re-scoped to
positive-content sides — both lines are permanent in the report. Full
pre/post decomposition and every adjudicated flip: dataset-plan G3 note,
`datasets/dev/screening/org-0000N/pre-post-diff-v043-2026-08-15.json`,
`datasets/dev/screening/exploit-audit/css-flip-adjudication-2026-08-15.json`.

**Harness-sensitivity study (2026-07-25).** A prespecified 60-run
comparison (20 per condition, deterministic sample; evidence in
`datasets/dev/screening/harness-study-2026-07-25/`) ran the identical
prompts through the same gpt-5.4 weights behind a second agent harness
(cursor-agent) and scored them through the identical blinded pipeline.
Outcome agreement with the codex canon: ceiling-pass 95%, floor
pair-pass 100%, twin-ceiling-pass 65% — the second harness states
awkward counterfactuals the incumbent refuses. Equivalence was rejected
per the prespecified ≥90% bar; codex is retained and version-pinned
(codex-cli 0.144.5, open-source scaffold) as the reproducible
instrument. Consequence made explicit: probe validity is calibrated to
(model, effort, harness), and harness heterogeneity alone flips a third
of twin-side outcomes — the first measured motivation for the
consumer-portability track.

The screening iterations themselves produced the protocol (each revision
measured, made before any SUT evaluation, evidence in git history):
gpt-5.4-mini rejected as task model (ceiling-gate survival 17/54 vs
37/54 for gpt-5.4 under the identical strict rule); applied-content
regex assertions rejected (39–42% ceiling failure — deliverables
paraphrase around any anchor — vs 4% for absence-detector patterns and
9–17% for semantic criteria), hence probe-spec v0.3's checker policy;
the all-instances cluster gate replaced by instance-level validity
(0.9^6 ≈ 0.53 cluster survival at realistic noise made the strict rule
unsatisfiable at n=3); assertions must never punish co-valid sibling
facts (from failure adjudication); and judging fully blinded
(2026-07-25). Provenance discipline: "prespecified" is reserved for
commitments git can corroborate (the 2026-07-14 design anchors); the
2026-07-19-dated working decisions were first committed 2026-07-22 —
see the standing-decisions note in `dataset-plan.md`.

**Seeds 2–5: probes final under spec v0.3; screening blocked on codex
quota (resets 2026-07-29).** Seed 2 has 356/486 task-model runs cached
and prompt-verified against the final probes.

## Consistency and coherence

- LLM consistency pass (seed 1, full stream vs. full ledger): zero
  contradictions; filler inert.
- LLM consistency passes, seeds 2–5 (2026-07-25; checker = gpt-5.4-high
  via cursor-agent — QA tooling, distinct from both the renderer and the
  pinned worker; per-org evidence in
  `datasets/dev/org-0000N/consistency-report.json`): seeds 4/5 clean;
  seeds 2/3 each had ONE filler line asserting rule content that
  contradicted a probed fact (a growth release cadence vs F-0070; a
  deploy-freeze window vs F-0043). Both lines replaced with inert
  one-off logistics chatter (twins were unaffected — those events were
  delta-re-rendered); the full clean-room sweep is ALL GREEN after the
  fix. Screening artifacts are untouched by construction: floor/ceiling
  prompts derive from the ledger, never from the event stream.
- The spec's HUMAN blinded spot-check and per-org read-throughs remain
  open items for formal G2 closure; all machine-side checks are complete.
