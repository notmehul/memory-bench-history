# Changelog

All notable changes to memory-bench will be documented in this file.
Format: [Keep a Changelog](https://keepachangelog.com/en/1.1.0/); versioning: SemVer.

## [Unreleased]

### Added
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

### Changed
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

### Fixed
- Ledger spec §5: `distributed` facts now require all evidence events witnessed
  (found during G0 fixture review).
- Fact planner: probed supersession-chain links lacked counterfactuals; A4/A7
  counterfactual templates collided across facts (both caught by gates).
