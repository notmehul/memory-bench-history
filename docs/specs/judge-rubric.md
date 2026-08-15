# Judge Rubric (versioned, verbatim)

The semantic checker (probe-spec §2) is an LLM judge that sees ONLY
`(output, criteria)` under opaque ids (`screen_probes.py judge-export`).
The judge's instructions are part of the instrument: every verdict in the
repository is produced under exactly one version of the text below, the
version is recorded per judgement batch, and the same text is handed to
human raters in Phase 4 (`docs/human-review.md`, Task 3) so judge–human κ
is measured against the same rule.

Judge model ≠ worker model, and never the family that authored or
repaired the criteria (CLAUDE.md hard rules).

## v2 — 2026-08-15 (current)

Change from v1: the **commitment clause** for positive-content criteria
(probe-spec v0.4.3 S1'): an output that presents the required value AND a
conflicting alternative as both current does not satisfy the criterion.
This is the semantic form of the v0.4.1 mechanical commitment rule and is
the closure for the scorer-exploit audit's enumerate-both-values residual;
the alternative closure (generated semantic cross-side detectors) was
measured and rejected the same day (0/19 true positives —
`datasets/dev/screening/exploit-audit/css-flip-adjudication-2026-08-15.json`).
Seeds 1–2 were fully re-judged under v2 so the canon is single-rubric;
v1→v2 verdict agreement is reported in the dataset-plan G3 note.

Verbatim text given to every judge (the file path varies per batch):

```
You are a blinded grader for a benchmark. Read ONLY this file (do not open
any other file, directory, or repository, and do not search anything):
<batch file>

It is a JSON array of rows. Each row has: "id" (opaque), "criteria" (a
dict of key -> one binary criterion sentence), and "output" (a work
document some model wrote). For EVERY row and EVERY criterion key, decide
true/false: does the output satisfy the criterion?

Rules:
- true ONLY if the output clearly satisfies the criterion. When in doubt,
  false.
- Judge only what is on the page: no outside knowledge, no guessing
  intent, no partial credit.
- Criteria phrased as absence ("does not present/list/state X as
  current/in effect", "does not require X"): true only if X is genuinely
  not presented as current/applicable — paraphrases and synonyms of X
  count as present. If X is mentioned only as past, replaced,
  hypothetical, or rejected, that does NOT count as presenting it (so the
  absence criterion is true).
- Criteria demanding positive content ("states X", "sets X as the rule"):
  true only if the output actually commits to X. If the output presents X
  AND a conflicting alternative as both current/applicable (hedging or
  enumerating both), it does not commit → false.
- Quality of the writing is irrelevant; only the criterion matters.

Write your verdicts as JSON to: <verdict file>
Format: {"<row id>": {"<criterion key>": true|false, ...}, ...} — every
row id from the input, every criterion key for that row, booleans only.
Before finishing, re-open your verdicts file and verify the row count
equals the input row count and each row has exactly the input's criterion
keys. Reply with just: "done, N rows, M criteria".
```

Judge tag written by `judge-import`: `claude-sonnet-5-blinded-v2`.

## v1 — 2026-07-25 … 2026-08-14 (superseded)

Same structure without the commitment clause: "true only if the
deliverable clearly satisfies the criterion; false when in doubt; absence
criteria — paraphrases count as present; judge only what is on the page."
Used for the seed-1 blinded re-judge (2026-07-25), seed 2 (2026-08-06),
the exploit audit's first pass, and the calibration packet's judge
column. All of these verdicts remain in git history; the current
`judgements.jsonl` files carry v2 verdicts with per-criterion text hashes.
