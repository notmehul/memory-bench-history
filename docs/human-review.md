# Human Review Handbook

> **Note 2026-08-28:** the v1 freeze (2026-08-15, `docs/dataset-plan.md`)
> replaced the two-rater G4 design below with a **single author-rater**
> (Mehul) on the 150-pair packet — a disclosed downgrade; criteria < 0.7
> agreement are dropped, never rewritten. The Rater-R protocol is retained
> for provenance and for v2. Open item B3 (recruit rater R) is closed by
> that decision.

**Read this first — it is self-contained.** If you were handed this document
(or just its task sections) you have everything you need; you should not
need access to the project repository, and for most tasks you must not
have it.

## What this project is, in three sentences

memory-bench is a scientific benchmark that tests whether AI "memory
systems" correctly remember and apply an organization's knowledge —
policies, decisions, personal preferences — inside realistic work tasks.
The test data is a fictional software company: a stream of meetings, chat
messages, and documents, in which specific facts are secretly probed by
hidden test questions while other, equally plausible facts are planted as
decoys. Human reviewers do the checks a machine can't be trusted to do on
its own: verifying the hidden facts aren't visually obvious, verifying the
story reads naturally, and calibrating the automated grader against human
judgment.

## The two reviewer roles

- **Rater R** — an external reviewer who has never seen this project's
  files or discussed its contents with the team. Freshness is the point:
  several checks are only valid if the reviewer can't recognize the
  material.
- **M (Mehul)** — the project lead. M has discussed some test content in
  working sessions, so M is *disqualified* from the guessing tasks for
  seeds 1–3 (he'd be guessing from memory, not from the text), but fully
  qualified for coherence reading and grader calibration.

"Seeds" are the five independently generated fictional companies, named
seed 1 through seed 5.

## Ground rules (every task)

1. **R never opens the repository.** Materials arrive as individual files
   sent by M. If a file you weren't sent seems needed, it isn't — ask M.
2. **One sitting per packet.** Don't split a guessing task across days,
   don't discuss contents with anyone until your answers are submitted.
3. **First answers are final.** No revisions after any score is revealed.
4. **No external tools.** No web searches, no AI assistants, no asking a
   friend. Your unaided judgment is the measurement.
5. Every completed task is recorded with your name/date; results go into
   the project's public audit trail.

---

## Task 1 — "Probed or planted?" guessing game *(Rater R only; ~10 min per seed; seeds 1–3)*

**Why this exists:** if a human can spot which facts the benchmark
secretly tests, then the test facts are written more prominently than the
decoys, and a memory system could exploit that. The benchmark passes this
check only if a genuinely motivated human FAILS to beat 65% accuracy.
(Seeds 4 and 5 were already checked: the raters scored 50% and 60% —
coin-flip territory, which is the desired outcome.)

**You receive:** three files named `packet.json` (one per seed). Each
contains 20 numbered one-line statements from the fictional company's
records, like:

```
{ "id": 7, "text": "Company meeting notes must record decisions, owners, plus due dates" }
```

**Your job:** exactly 10 of the 20 are secretly tested ("probed"); 10 are
decoys ("distractor"). For each id, guess which. Gut feeling is fine —
but genuinely try to win: look for any pattern in wording, specificity,
formality, topic. You are the adversary; a half-hearted guess proves
nothing.

**You return:** one file per seed, any name (e.g. `seed1-answers.json`),
in exactly this shape — every id from 1 to 20, each labeled
`"probed"` or `"distractor"`:

```json
{"1": "probed", "2": "distractor", "3": "probed", ... , "20": "distractor"}
```

**Scoring (M runs this, after answers are locked):**

```
python scripts/blind_check.py score \
    datasets/dev/human-check/seed-N/KEY-do-not-open.json  answers.json
```

M then writes `datasets/dev/human-check/seed-N/result.txt`: rater, date,
score, and any pattern the rater says they used. Below 65% = PASS.

---

## Task 2 — Story read-through *(R or M; ≥1 seed required; ~45 min)*

**Why this exists:** the event stream must read like a real company's
communications. Incoherence (impossible dates, personality flips,
template-y repetition) would mark the data as synthetic junk.

**Rule:** only read a seed AFTER its Task-1 guessing is scored (reading
first would reveal which topics recur, spoiling the guess). M may read any
seed — coherence judgment isn't affected by his prior exposure.

**You receive:** one file, `events.jsonl` — the seed's full message/
meeting/document stream, one JSON event per line, in chronological order.
Read the `content` fields top to bottom like a story.

**You return:** a short notes file (`readthrough-notes.md`), bullet list.
Note anything that breaks the illusion, with the event's `event_id`:
broken references ("as discussed Tuesday" when nothing happened Tuesday),
impossible timelines, people acting against their established character,
tonal whiplash, machine-templated repetition. **"No issues found" is a
valid and useful result** — don't invent problems.

Suggested split: M reads seed 1; R reads seed 2 or 3 after their Task-1
answers are scored.

---

## Task 3 — Grader calibration *(M alone under the freeze; ~3–5h; THE critical task)*

> **Procedure as it actually runs (freeze 2026-08-15, single author-rater).**
> There is no second rater, so there is no inter-rater kappa and no
> adjudication meeting: M's 150 labels *are* the human gold, and the measured
> number is judge-vs-human agreement. Read the job and the rules below — they
> are unchanged — then use the single-rater commands at the end of this task,
> not the two-rater ones. The two-rater text is retained for v2.

**Why this exists:** thousands of test outputs are graded by an AI judge
against written criteria. The benchmark's credibility rests on proving the
AI judge agrees with careful humans (target: Cohen's κ ≥ 0.75). Your
labels are the gold standard the judge is measured against.

**You receive:** `rater-packet.json` — 150 items (M sends it from `datasets/dev/calibration/`; the packet is ready as of 2026-08-15). Each item has only two
things: a **criterion** (a single yes/no statement) and an **output** (a
work document some model wrote — a checklist, a note, an announcement).
You also receive `rating-template.json`, the same item ids with `null`
values to fill in.

**Your job, per item:** does the output satisfy the criterion?

- `true` ONLY if the output **clearly** satisfies the criterion.
- **When in doubt, `false`.** This is the protocol, not pessimism.
- Criteria phrased as absence ("does not mention X", "does not present X
  as current"): `true` only if X is genuinely not presented as
  current/applicable — paraphrases and synonyms of X count as present. If
  X appears only as past, replaced, hypothetical, or rejected ("we no
  longer do X"), that does NOT count as presenting it → `true`.
- Criteria demanding positive content ("states X", "sets X as the rule"):
  `true` only if the output actually commits to X. If it presents X AND a
  conflicting alternative as both current (hedging, listing both), it does
  not commit → `false`.
- Judge ONLY what is on the page. No outside knowledge, no guessing what
  the writer meant, no partial credit.
- These are exactly the rules the AI judge is given
  (`docs/specs/judge-rubric.md`, v2) — the comparison is only meaningful
  if you apply the same ones.

Example item:

```
criterion: "The note says PRs under 200 lines should be handled before lunch."
output:    "Triage order for tomorrow: small diffs (sub-200-line) first
            thing in the morning, big refactors after standup..."
→ true  (paraphrase clearly satisfies it: before lunch ≈ first thing in
   the morning is a judgment call — if that equivalence feels doubtful to
   you, answer false. Doubt = false is always safe.)
```

**Hard rules:** first answers are final; no revisions once any score is
revealed; no AI assistants and no looking anything up. Expect it to be tedious;
take breaks between blocks. Do not re-read earlier items to make them
consistent — drift is part of what the measurement captures.

### Single-rater run (the live procedure)

Rate in a spreadsheet, not in JSON. Export the packet as a sheet:

```
uv sync --extra sheet        # once
.venv/bin/python scripts/calibration_sheet.py export \
    datasets/dev/calibration ~/memory-bench-G4-calibration.xlsx
```

Two tabs: **How to rate** (the rules below, on one screen) and **Rate** (150
rows — `#`, `ANSWER`, `CRITERION`, `OUTPUT`, `id`). Put TRUE or FALSE in column
B; unanswered rows stay amber, and a counter in G1 shows how many are done. The
`#` and `ANSWER` columns are frozen, so the answer box stays on screen while a
long deliverable scrolls. Never sort, insert, or delete rows — that breaks the
mapping back to the packet, and the importer will refuse the file rather than
guess. A few outputs are longer than one row can show: click the cell and read
it in the formula bar, dragging its bottom edge taller.

The sheet stays blinded, like the JSON packet: criterion and deliverable only,
never the run id, condition, or side.

When it's filled:

```
.venv/bin/python scripts/calibration_sheet.py import ~/memory-bench-G4-calibration.xlsx
```

which validates every row and writes `datasets/dev/calibration/ratings-M.json`.
(Rating the JSON template by hand still works if you prefer: copy
`rating-template.json`, replace each `null` with `true` or `false`, save as
`ratings-M.json`.) Then:

```
.venv/bin/python scripts/calibration.py judge-agreement \
    datasets/dev/calibration \
    datasets/dev/calibration/ratings-M.json \
    datasets/dev/screening/org-00001 datasets/dev/screening/org-00002
```

This writes `datasets/dev/calibration/judge-agreement.json`: overall Cohen's
κ against the human gold (**gate G4 = κ ≥ 0.75**), per-assertion-kind κ, and
every criterion whose raw agreement falls below 0.7. Criteria below 0.7 are
**dropped and the count disclosed — never rewritten**. The result is reported
whichever way it lands; a FAIL is carried as a FAIL.

Verified 2026-09-14: the packet's 150 pairs draw on org-00001 and org-00002
(75 each) and every one has a committed judge verdict, so the command runs
against committed evidence with no further screening.

### Two-rater run (retained for v2, not used in v1)

With a second rater R, both work completely independently — zero discussion
until both files are submitted. Then `python scripts/calibration.py kappa <dir>
ratings-M.json ratings-R.json` prints inter-rater agreement and the
disagreement list; R and M meet, discuss only those items, and produce
`adjudicated.json`, which is passed to `judge-agreement` in place of a single
rater's file.

---

## Task 4 — Human performance baseline *(R + M, ~2h each; only if decision B4 = yes)*

**Why this exists:** reviewers of the paper will ask "how well would a
person do at these tasks?" Each human completes ~20 of the same work
tasks the models did, with the relevant company facts provided in the
prompt (so it's a writing task, not a memory test). Write the deliverable
in your own words, plain text, honest effort, no AI tools. Outputs are
graded by the standard pipeline and reported as the human reference band.

**You receive:** ~20 numbered task prompts (each self-contained).
**You return:** one text file per task, named by the task number.

---

## Task 5 — Open decisions *(M only)*

| ID | Decision | Options | Status |
|---|---|---|---|
| B3 | Confirm R as official second rater | yes / find another | CLOSED 2026-08-15 (single author-rater; see note at top) |
| B4 | Run Task 4 (human baseline)? | yes (recommended) / skip + limitation note | OPEN — needs no model runs, so the 2026-09-14 reframe leaves it available |
| B5 | Pilot compute budget | full / reduced prespecified design | CLOSED 2026-09-14 — superseded by the FREEZE amendment; comparative pilot runs are out of v1, so there is no budget left to set |

Record each decision with a date in `docs/dataset-plan.md` standing
decisions.

---

## Checklist and sequence

| Step | Who | Depends on | Time |
|---|---|---|---|
| 1. B3 decision (confirm R) | M | — | 1 min |
| 2. Task 1: seeds 1–3 guessing | R | step 1 | 3 × 10 min |
| 3. Score + record Task 1 | M | step 2 | 10 min |
| 4. Task 2: read-throughs (M: seed 1; R: seed 2 or 3) | both | step 3 (for R's seed) | 45 min each |
| 5. Task 3: grading (single rater under the freeze) | M | calibration packet ready | 3–5 h |
| 6. Task 3: adjudication meeting — NOT RUN in v1 (no second rater) | — | — | — |
| 7. Task 4 (if B4 = yes) | both | any time after step 1 | ~2 h each |
| 8. B5 decision — CLOSED 2026-09-14, superseded | — | — | — |

## FAQ

- **"I'm not sure about an item."** Task 1: guess anyway, that's the
  design. Task 3: unsure = `false`, that's the protocol.
- **"Can I look something up / ask an AI?"** No. Your unaided judgment is
  the instrument being used.
- **"I think I recognize a pattern in the packets."** Great — use it, and
  tell M what it was after scoring; the pattern itself is a finding.
- **"The output in Task 3 is well-written but doesn't address the
  criterion."** `false`. Quality is not the question; the criterion is.
- **"I accidentally saw a file I shouldn't have."** Tell M immediately —
  it may disqualify you from specific seeds only; honesty keeps the rest
  of your work usable.
- **"Why so strict?"** Every rule here maps to a documented failure in a
  published benchmark this project studied. The strictness is what makes
  the result publishable.
