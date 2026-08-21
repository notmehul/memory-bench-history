# memory-bench — agent instructions

Publishable scientific benchmark for memory systems in organizations of
agents. High stakes: this ships as a research paper and must survive hostile
review. When in doubt, choose the option that is *measurable, dated, and
disclosed* over the convenient one.

## v1 freeze (2026-08-15) — read before anything else

The deliverable is **pilot numbers** (`docs/dataset-plan.md`, "v1 pilot
FREEZE"). No new gate, scoring rule, spec section, audit, spec doc, seed
screening, criterion edit, or system outside the frozen list without Mehul's
explicit ask in the current session. Prefer running the loop end-to-end over
hardening it. Outputs for Mehul (rater packets, decisions, summaries) are
pointed and short — one file, one ask; never sprawling report sets.

## Read first (in this order)

1. `docs/status.md` — current state and the work queue with blockers.
2. `docs/vision.md` — capability ladder, heterogeneity thesis, claims discipline.
3. `docs/dataset-plan.md` — short: phases, gates G0–G5, standing decisions,
   and the v1 FREEZE section at the bottom. The dated history (gate results,
   protocol amendments, harness study, screening notes) lives verbatim in
   `docs/decision-log.md` — read it only when a decision's provenance matters.
4. `docs/standards-audit.md` — field-failure audit; the pre-release tracker.
   Nothing ships while a BLOCKING row is open.
5. `docs/architecture.md`, `docs/validation-report.md`, `docs/specs/` as needed;
   `docs/deferred.md` (optional) — what v1 cut and where its material lives.

## Hard rules (violations invalidate published numbers)

- **Pinned worker**: the fixed task model is **(gpt-5.4, effort medium,
  codex-cli 0.144.5)**. Never substitute or mix harnesses in any protocol
  path — measured evidence: identical weights behind cursor-agent agree only
  65% on twin-ceiling outcomes (`datasets/dev/screening/harness-study-2026-07-25/`).
  cursor-agent is allowed ONLY for QA tooling and non-protocol work (wrap in
  `timeout`, retry ×2). The PATH `codex` may be newer (Homebrew upgrades
  silently); protocol paths enforce the pin via `membench.codex_bin` — run
  them with `MEMBENCH_CODEX_BIN=~/.local/codex-0.144.5/node_modules/.bin/codex`.
  If you are a codex or cursor-agent run: this pin is about *you*. Check which binary
  and model you are before touching a protocol path, and stop rather than proceed on
  the wrong one — a silent substitution invalidates the published numbers.
- **Blinded judging always**: semantic verdicts go through
  `screen_probes.py judge-export` (opaque ids) → fresh judge agents that read
  ONLY the batch file → `judge-import`. Judge model ≠ worker model, and never
  the model family that authored/repaired the assertions being judged.
- **Prespecify, then measure**: any gate/protocol change is written into
  `docs/dataset-plan.md` with a date BEFORE the evidence it applies to is
  produced. "Prespecified" is reserved for commitments corroborated by git
  history. Failed gates are carried as explicit FAILs, never narrated away.
- **Independence**: no author-affiliated memory system is ever evaluated;
  market systems enter by the published inclusion criteria; every exclusion
  reported. No product-level "expected to win" language anywhere.
- **Never a single aggregate score**; results are a radar grouped by
  capability-ladder rung (`docs/vision.md` §3).
- **Assertion repairs must keep task text byte-identical** (cached worker
  outputs stay valid; verify with the prompt-equality check before reusing
  results). Co-valid sibling facts must never be punished by assertions.
- Blinded raters/judges must be isolated from the repo (the ledger contains
  answers). Never run two screening pipelines against one work dir. Never
  edit a bash script while it is executing.

## Conventions

- Conventional Commits; every commit ends with the co-author trailer for whichever
  agent wrote it.
- Tests + `ruff check .` green before any commit (`.venv/bin/python -m pytest -q`).
- Scratch work goes in the session scratchpad, never the repo; committed
  evidence goes under `datasets/dev/screening/` or per-org dirs.
- Content generation for protocol paths runs through codex CLI
  (`codex exec -s workspace-write --skip-git-repo-check -m gpt-5.4 -c
  model_reasoning_effort=medium -`), output captured via a file the model
  writes, not stdout. Quota economics: one credit pack ≈ ~1,000 gpt-5.4
  medium runs; one seed's screening = 486 runs.
- Update `docs/status.md` when a queue item completes.
