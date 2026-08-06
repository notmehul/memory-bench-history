# Human Review Handbook

Everything the human reviewers do for memory-bench, in order, with exact
materials and rules. Two roles:

- **Rater R** — the external rater (naive: has never seen this repo or any
  discussion of its contents; the joint rater from the seed-4/5 spot-checks
  qualifies for everything EXCEPT re-rating seeds 4/5).
- **M** — Mehul. Contaminated for seed-1/2/3 content (probed facts were
  discussed in working sessions); eligible for read-throughs, Phase 4
  labeling, and decisions.

## Isolation rules (apply to every task below)

1. Rater R never gets repo access. Materials are sent as individual files;
   the allowed set per task is listed below. NEVER send: any `org.json`,
   `KEY-do-not-open.json`, `probes.jsonl`, `judgements.jsonl`, `plan.json`,
   or any doc that describes facts (validation-report, dataset-plan).
2. One sitting per packet; no discussion of contents with M until the task's
   answers are locked and scored.
3. Answers are final on first submission — no revisions after any score or
   key is revealed.
4. Every completed task gets a dated result file committed to the repo with
   rater provenance.

## Task 1 — Blinded salience spot-checks, seeds 1–3 *(Rater R only, ~30 min)*

Status: seeds 4/5 DONE (50%, 60% — both PASS). Seeds 1–3 open.

- Materials to send R: `datasets/dev/human-check/seed-{1,2,3}/packet.json`
  (three files, nothing else).
- Instruction to R, verbatim: *"Each file lists 20 one-line excerpts from a
  fictional company's records. Exactly 10 are facts a hidden test probes;
  10 are planted noise. For each id, guess `probed` or `distractor`. Go
  with your gut, but genuinely try to find a pattern — you're the
  adversary. One sitting per file."*
- R returns three answer files: `{"1": "probed", ..., "20": "distractor"}`.
- Scoring (M or agent): `python scripts/blind_check.py score
  datasets/dev/human-check/seed-N/KEY-do-not-open.json <answers.json>`
- Gate: accuracy < 65% per protocol; write `result.txt` per seed (rater,
  date, score, any heuristic R reports having used).

## Task 2 — Narrative read-through *(R or M; ≥1 org required, ~45 min/org)*

Only AFTER that seed's spot-check is scored (a read-through primes topics).

- Materials: that org's `events.jsonl` only.
- Read start to finish; note anything incoherent: broken references,
  impossible timelines, personas acting out of character, tone breaks,
  content that feels machine-templated.
- Output: `datasets/dev/human-check/seed-N/readthrough-notes.md` — bullet
  list with event ids; "no issues found" is a valid result.
- M may do this for any seed (contamination doesn't affect coherence
  judgment). Recommended: M does seed 1; R does one of 2/3 after their
  spot-checks.

## Task 3 — Phase 4 judge-calibration labeling *(R and M, independently, ~3–5h each)*

Runs once the calibration packet reaches 150 pairs (needs seed-2 screening
merged; interim 108-pair packet exists). This is the load-bearing task:
the benchmark's semantic-judging policy stands or falls on gate G4
(judge–human κ ≥ 0.75).

- Materials per rater: `rater-packet.json` + `rating-template.json` from
  the calibration output dir (packet is blinded: only criterion text +
  deliverable text under opaque ids).
- Instruction, verbatim: *"For each item: read the criterion (a binary
  statement) and the deliverable. Mark true only if the deliverable
  clearly satisfies the criterion; when in doubt, false. Criteria phrased
  as absence statements ('does not mention X') are true only when X is
  genuinely absent — paraphrases of X count as present. Judge only what
  is on the page."*
- R and M fill their own copies of `rating-template.json` **independently
  — zero discussion until both are submitted.**
- Then: `python scripts/calibration.py kappa <out_dir> ratings-M.json
  ratings-R.json` → inter-rater κ + disagreement list.
- Adjudication: R and M discuss ONLY the disagreement items together,
  agree a final label for each, producing `adjudicated.json` (covers every
  packet id). Then `python scripts/calibration.py judge-agreement ...`
  computes judge-vs-human κ and the G4 verdict.

## Task 4 — Human performance baseline *(R + M, ~2h each; pending decision B4)*

If approved: each human completes the same ~20 work tasks the models do,
with the relevant facts provided (ceiling condition), producing the
deliverable in their own words. Outputs are scored by the standard blinded
pipeline and reported as a human reference band next to model ceilings.
Materials: task prompts only (the ceiling prompt text, which contains the
needed facts) — safe to send since ceiling prompts are self-contained.

## Task 5 — Decisions log *(M only — currently open)*

| ID | Decision | Options | Status |
|---|---|---|---|
| B3 | Confirm R as official second rater | yes / find another | OPEN |
| B4 | Human baseline (Task 4) | do it / skip + limitation note | OPEN |
| B5 | Pilot budget | full (~9 packs, all systems × 5 seeds × K=3) / reduced prespecified (all systems × 3 seeds + finalists × 5) | OPEN — must be decided before any pilot data exists |

Record each decision with a date in `docs/dataset-plan.md` (standing
decisions) when made.

## Sequence summary

1. R: spot-checks seeds 1–3 (Task 1) → scored.
2. R: read-through of seed 2 or 3; M: read-through of seed 1 (Task 2).
3. Both: Phase 4 labeling + adjudication (Task 3) — after seed-2 screening.
4. Both: human baseline (Task 4) if B4 = yes.
5. M: close B3/B4/B5 (Task 5) — B5 needed before the pilot, B3 before step 1.
