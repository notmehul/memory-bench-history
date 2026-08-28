# Changelog

All notable changes to memory-bench will be documented in this file.
Format: [Keep a Changelog](https://keepachangelog.com/en/1.1.0/); versioning: SemVer.

## [Unreleased]

### Added
- Backtest/cleanup pass (2026-08-28): README, power-analysis, human-review,
  architecture, dataset-plan and validation-report re-pointed at the frozen v1
  scope with dated supersession notes; CI installs the figures extra.
- Results pipeline (2026-08-27): `scripts/figures.py` (radar by rung, per-rung/
  archetype tables, ≥2/3-seed direction rule, paired H2 diff, cost table;
  dry-run on mock data); per-system configs frozen before any live run
  (`docs/vendor-configs.md`); paper skeleton + preprint checklist (`paper/`).
- SUT adapters + pilot orchestrator (2026-08-22): Mem0, Cognee, Graphiti
  (embedded Kuzu), Supermemory (hosted, async-settle logic) behind fake-client
  tests; `scripts/run_pilot.py run/report` (resumable, only-valid instances,
  cost columns, cross-seed summary); Gemini embedding pin
  (`gemini-embedding-001`) behind the retriever seam.
- v1 pilot FREEZE (2026-08-15, prespecified before any SUT run): dataset =
  seeds 1–3 as-is (371 valid instances), 8 systems + Mem0 silo ablation
  (market systems by top-4 GitHub stars), single author-rater G4 (disclosed
  downgrade), ≥2/3-seed direction rule; seeds 4–5 unscreened holdouts. Dated
  history split to `docs/decision-log.md`; cut scope to `docs/deferred.md`.
- Benchmark design: dimensional model, 12 scenario archetypes, scientific
  methodology, difficulty ladder (`docs/architecture.md`).
- Contracts: ground-truth ledger schema, event-stream format, probe spec
  (`docs/specs/`).
- Phased dataset plan with gates G0–G5 (`docs/dataset-plan.md`).
- Belief-state oracle `B(principal, t)`, `B_hist`, and precedence resolution
  (`membench.belief`), with ledger loading/validation (`membench.ledger`).
- Gate G0 test suite: 70 hand-derived cases over six generated fixture orgs.

- Phase 1 generator: seeded org designer (personas, teams, calendar with
  first-class absences), fact planner instantiating archetypes A1/A2/A4/A7
  with distractors, near-misses, and counterfactual slots, gate G1 checker
  with planner↔oracle cross-validation, and a realization validator.
- `python -m membench.generate` CLI; dev dataset `datasets/dev/` (seeds 1–5),
  seed 1 fully prose-realized.
- Ledger schema: optional `distractor_kind` field (structural near-miss marker).
- Phase 2 machinery: event renderer with marker protocol (spans computed
  mechanically, never LLM-reported), release-blocking stream linter
  (round-trip, verbatim-reuse, visibility, salience permutation tests, noise
  floor, canaries), counterfactual twin builder with delta-only re-rendering,
  and `python -m membench.realize` assembly CLI.
- All five dev orgs + counterfactual twins fully realized and lint-green;
  blinded-rater protocol passes in aggregate (58/100, p=0.067; seed-3
  residual documented). Final numbers in docs/validation-report.md.
- prompts/ directory: event-render.md and canonical-realization.md codify
  the content-generation contracts learned from the salience arms race.
- Phase 3 machinery: probe constructor (`membench.probes`) expanding every
  plan cluster to >=3 oracle-revalidated instances with mechanical hygiene
  lint and pattern cross-validation of authored assertions
  (prompts/probe-authoring.md); floor/ceiling validity screening harness
  with prespecified small-n gates (`scripts/screen_probes.py`,
  `scripts/author_probes.py`).
- Probes for all 5 dev orgs: 810 oracle-validated instances
  (`datasets/dev/org-0000N/probes.jsonl`) under probe-spec v0.3. Seed-1
  validity screening complete under the final protocol: 486 gpt-5.4 runs,
  blinded claude-sonnet-5 judging, 45/54 clusters survive with 125 valid
  instances (cluster gate PASS at zero margin, instance gate an explicit
  FAIL at 125/135; evidence in `datasets/dev/screening/org-00001/`).
  Seed-2 partial run cache staged.
- Project orientation for agents (2026-07-25): repo-level `CLAUDE.md`
  (hard rules: pinned worker, blinded judging, prespecification and
  independence discipline) and `docs/status.md` (living work queue:
  codex-quota-blocked, human-blocked, and unblocked items, with the three
  BLOCKING pre-headline gates).
- Benchmark-standards audit (2026-07-25, `docs/standards-audit.md`):
  memory-bench compared against every verifiable published memory
  benchmark, the vendor eval controversies (Mem0/Zep, Letta, MemPalace,
  LoCoMo audit), and formal standards (BetterBench, ABC, NeurIPS E&D,
  Miller error-bar canon). Nine gaps adopted as dated Phase 4/5
  amendments: adversarial judge decoy audit, prespecified statistics
  protocol (cluster-robust SEs, paired comparisons, power analysis, tie
  rule), scorer-exploit audit, filesystem+grep baseline (#8), embedding
  pinning, mandatory cost columns, vendor fairness with right-of-reply,
  benchmark agreement testing, and release-compliance requirements on G5.
- Harness-sensitivity study (2026-07-25): 60 prespecified seed-1 runs
  through cursor-agent gpt-5.4-medium, blinded-judged and compared to the
  codex canon — twin-ceiling outcome agreement 65% (ceiling 95%, floor
  pair 100%). Worker harness rejected as interchangeable; the fixed
  worker is now pinned as (gpt-5.4, medium, codex-cli 0.144.5). Evidence
  in `datasets/dev/screening/harness-study-2026-07-25/`.
- Blinded judging in the screening harness (2026-07-25, from the
  meta-review audit): `judge-export` emits opaque row/criterion ids so
  the judge cannot infer condition or org side; `--ids` supports targeted
  blinded re-judging; round-trip tests in `tests/test_screening.py`. All
  1,092 seed-1 semantic verdicts re-judged blinded (97.6% agreement with
  the unblinded pass, retained in git history; fallback-judge conflict of
  interest eliminated — blinded verdicts confirmed all 6 affected rows).
- Probe spec v0.3: applied-content assertions must be semantic (measured:
  regex-on-paraphrase fails 39-42% of ceiling runs vs 9-17% semantic);
  pattern reserved for fact_absent detectors; validity gates evaluated per
  instance (cluster survives with >=2/3 valid instances); assertions may
  never punish co-valid sibling facts. Task model escalated to gpt-5.4
  after mini failed ceiling anchors (17/54); screening judge moved to the
  Claude family (cross-provider).
- Positioning document `docs/vision.md` (2026-07-25): the capability ladder
  (Retention → Alignment → Coordination → Compounding) operationalizing the
  collective-intelligence claim, and the heterogeneity / consumer-portability
  thesis.
- Probe-spec v0.4.3 semantic layer (2026-08-15): natural-artifact rule in operational form
  (pure-retraction criteria rewritten to observable absence, 40 criteria
  across five orgs, uniform codex classification + hand audit); tier rule
  for sibling guards (higher-tier nested rules may be restated); six
  brittle authored patterns replaced by semantic mirrors; empty-output
  scoring rule; incremental blinded re-judging with per-criterion text
  hashes (`judge-export --incremental`, `judge-import --merge`, stale-verdict
  guard in `report`); S6 discrimination gate (ceiling output must fail the
  cf assertion set and vice versa — cross rows judged in the same blinded
  pass); versioned verbatim judge rubric (`docs/specs/judge-rubric.md`,
  v2 = commitment clause) with a full clean re-judge of seeds 1–2; exploit
  audit reports both the literal and re-scoped bar; `scripts/g3_diff.py`;
  `scripts/natural_artifact_sweep.py`. Codex-cli 0.144.5 pin now enforced
  in code (`membench.codex_bin`) after Homebrew silently upgraded PATH.
  Generated semantic cross-side detectors were built, measured (0/19 true
  positives) and rejected; kept behind `--semantic` for reproduction.
- Pilot machinery (2026-08-15): grep-agent baseline adapter (#8) with a
  files seam on the worker; typed-memory reference implementation (#6,
  proposed spec + hashable extraction prompt, ablation flags);
  `membench.pilot` CLI; `scripts/score_sut.py` (pair credit against the
  screening anchors, blinded judging, radar by rung/metric with
  cluster-robust SEs); judge decoy false-accept audit tooling and result;
  150-pair calibration packet; cross-seed G3 summary; pre-pilot vendor
  survey; codex-cli pin enforced in code. Seed 3 screened (40/54 FAIL
  carried) with R6; seed 4 partial (quota).

### Changed
- Independence protocol (2026-07-25): the pilot evaluates no
  author-affiliated system. The "Marshmallow-style" baseline is replaced
  by a generic typed-memory reference implementation (architecture-class
  test, open-sourced with the benchmark); market systems enter by
  published inclusion criteria with every exclusion reported; author
  affiliation disclosed. See the Phase 5 protocol note in
  `docs/dataset-plan.md`.
- Probe spec v0.2 (Phase 3 pilot): the floor validity gate is evaluated at
  pair level for counterfactual-paired probes — a floor run only counts as
  "passable without memory" if one memoryless output satisfies BOTH sides
  of the twin pair. Per-side floor passes are reported as `guessability`.
  Rationale: canonical facts that coincide with plausible industry defaults
  are guessable per-side; twin pairing exists precisely to cancel this.
- Probe assertion patterns: `.*`/`.+` conjunctions banned (order-brittle);
  patterns must match digit and word number forms (enforced mechanically by
  generated surface variants) and enumerate paraphrase alternations for
  absence detectors.
- Fact planner mirrors distractor placement over probed event kinds; the
  first render pass failed the salience lint on position skew (p=0.002)
  because probed facts concentrated in meetings and distractors in chats.
- Deep-audit hardening (two independent code reviews + clean-room re-verify):
  validator enforces tier↔scope_ref pairing and supersession tier ordering;
  `B(departed) = ∅` documented as normative; rule-2 dead clause removed;
  G1 gains a full belief-state sweep, a same-topic co-valid ambiguity scan,
  and an honest interleaving statistic (adjacent-evidence mixing +
  no-contiguous-archetype-blocks) replacing the always-passing window check;
  expired near-misses must lapse before their topic's first real fact
  (the old placement created unresolvable precedence ties); `topic` is now
  an explicit ledger field; annotations carry `rendering`; `offsets_from`
  fails loudly on collapse; Contract #2 v0.2 drops `embeds_distractors`
  (salience lint needs distractor spans; ledger owns distractor status).
- Pre-pilot amendments (2026-07-25, before any pilot run): silo-ablation
  baseline added to the Phase 5 lineup; three pilot hypotheses prespecified
  in `docs/dataset-plan.md`; the model-grid track repurposed as consumer
  portability; v2 archetype queue reordered (A12/A5 first). README metrics
  regrouped by capability rung.

### Fixed
- Valid-instance counting included instances of dropped clusters (380 vs the
  frozen 371); `membench.g3.valid_instances` now intersects valid instances
  with surviving clusters (2026-08-22).
- Silo-ablation design: full-transcript shared vs silo yields byte-identical
  context, making the ablation vacuous there; moved to Mem0 before any run
  (2026-08-15, disclosed).
- Supermemory registry constructed the adapter with settle disabled; pilot
  registry now passes the frozen settle policy (2026-08-27).
- Seeds 2/3 stream contamination (2026-07-25, found by the seeds-2–5 LLM
  consistency passes): one filler line per seed asserted rule content
  contradicting a probed fact (release cadence vs F-0070 in seed 2;
  deploy-freeze window vs F-0043 in seed 3). Lines replaced with inert
  one-off chatter; twins unaffected; full validation sweep re-green.
  Checker reports committed per org (`consistency-report.json`).
- Meta-review remediations (2026-07-25, four-track audit of Phase 3): P-0023
  recovered and one P-0032 assertion pair repaired under the co-valid-sibling
  rule (inconsistently applied during screening; same treatment as the
  precedented P-0031/40/41 repairs); the G3 instance shortfall re-attributed
  from "single-instance noise" to structured twin-side counterfactual
  anchoring failure and the gate carried as an explicit FAIL; the
  "per-archetype n ≥ 30" gate unit pinned to instances; mini-vs-gpt-5.4
  comparison corrected to like-for-like (17/54 vs 37/54 ceiling-gate
  survival); verdict-count and task-defect-count corrections in the
  validation report; provenance note distinguishing commit-verifiable
  prespecifications from in-file-dated working decisions.
- Ledger spec §5: `distributed` facts now require all evidence events witnessed
  (found during G0 fixture review).
- Fact planner: probed supersession-chain links lacked counterfactuals; A4/A7
  counterfactual templates collided across facts (both caught by gates).
