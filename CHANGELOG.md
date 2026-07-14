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

### Fixed
- Ledger spec §5: `distributed` facts now require all evidence events witnessed
  (found during G0 fixture review).
