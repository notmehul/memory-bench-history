# memory-bench — Claude Code

The project rules — the v1 freeze, read-first order, hard rules, conventions — live in
`AGENTS.md`, which Codex and cursor-agent read too. It is part of this file:

@./AGENTS.md

What follows is Claude-specific.

## Orchestration

You are usually the orchestrator here, not the worker. Protocol content generation goes
to pinned codex; cursor-agent is QA tooling only. Both now read `AGENTS.md`, so the pin
and the blinding rules reach them directly — but you own enforcing them, because a
subagent that violates one still produces output that looks fine.

Inspect what a worker actually wrote before accepting it: the file, the diff, the row
count. A summary is not evidence (`prove-it-works`).

## Reach for these

- **`show-me-your-work`** — any run that goes unattended or spans phases. Screening runs
  are exactly this: a decision trail beats reconstructing the night from scrollback.
- **`grilling`** — before a gate, spec section, or scoring rule changes. The freeze means
  the default answer is no; make the case explicit first.
- **`interrogate`** — for anything that will appear in the paper. Hostile review is the
  bar, so get the disagreement early and cheap.

## Memory

Cross-session facts that don't belong in the repo go in the auto-memory project file.
Convert relative dates to absolute ones.
