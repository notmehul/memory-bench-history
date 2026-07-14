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
- Seed-1 org fully realized: 204-event base + twin streams, lint green,
  machine-blinded salience check 40% (below 65% bar), LLM consistency pass
  clean. Human blinded check and seeds 2–5 rendering pending for G2.

### Changed
- Fact planner mirrors distractor placement over probed event kinds; the
  first render pass failed the salience lint on position skew (p=0.002)
  because probed facts concentrated in meetings and distractors in chats.

### Fixed
- Ledger spec §5: `distributed` facts now require all evidence events witnessed
  (found during G0 fixture review).
- Fact planner: probed supersession-chain links lacked counterfactuals; A4/A7
  counterfactual templates collided across facts (both caught by gates).
