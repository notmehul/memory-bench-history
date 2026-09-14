# Status & Work Queue

Last updated: 2026-09-14. **Two tracks run in parallel from here.** Track A is
the v1 dataset paper, which is close to done and has open decisions that are
Mehul's. Track B is a second paper on benchmark methodology, opened 2026-09-14
because the second rater (Track A item 13) takes real calendar time to recruit
and the project should not idle on it.

Earlier history is in `docs/decision-log.md`, dated and append-only. The
pre-freeze A/B/C queue tables were removed 2026-08-15 (`git show
d0820af:docs/status.md`). Update this file when a queue item completes; keep
entries dated.

---

## Where the project stands

- **Dataset (frozen):** seeds 1–3, probe-spec v0.4.3, judge rubric v2 —
  **371 valid instances: A1 50, A2 43, A4 106, A7 172** (seed 1 46/54, 125;
  seed 2 46/54, 131; seed 3 40/54, 115). **All three instance gates FAIL;
  seed 3's cluster gate also FAILs.** Carried as failures, never repaired.
  Seeds 4–5 are unscreened holdouts (seed 4 has 327/486 cached outputs).
  No criterion edits, adjudications, or re-judging from here on.
- **Worker / judge:** gpt-5.4, effort medium, codex-cli 0.144.5 —
  **deprecated provider-side 2026-09-04, unreachable through any available
  billing path.** Comparative evaluation is out of v1 (FREEZE amendment
  2026-09-14). Judge claude-sonnet-5, rubric v2, always blinded.
- **Four prespecified gates have failed and are reported as failures**: the
  three instance gates, seed 3's cluster gate, the harness-equivalence bar
  (§4.3), and G4 (§4.4). One positive result: the memoryless floor at 4 of 125
  instances credited. That asymmetry is deliberate and is the paper's
  credibility argument, not a wound.
- **Build is done.** Adapters for all 10 system configs registered in
  `membench.pilot`; `scripts/run_pilot.py` + `score_sut.py` + `figures.py`;
  `scripts/release.py build|verify`; `scripts/calibration_sheet.py
  export|import`. 282 tests, ruff clean.
- **Guards in place:** `tests/test_paper_numbers.py` recomputes every headline
  number from its artifact and asserts the string is in the draft;
  `tests/test_prose_style.py` holds the unslop pass on the public surfaces.

---

## Track A — v1 dataset paper

### Done (2026-09-14)

1. **Reframe merged** (`6e2ed86`) and the freeze reconciled with it
   (`ecab022`): dated FREEZE amendment, `AGENTS.md`, README, `deferred.md`.
2. **Release packaging** (`c12fb25`): ships streams, twins, probes, valid sets,
   Croissant 1.0 + RAI metadata, CC BY 4.0 `LICENSE-DATA`, `MAINTENANCE.md`,
   checksums, manifest. Withholds the ledger (746 facts), probe plans,
   realization maps, annotated streams, holdout seeds, rater keys. Proven
   runnable: the redacted bundle drives the real Runner to the full frozen
   valid set.
3. **G4 rater sheet** (`e099fbc`): blinded packet as .xlsx, validated back to
   JSON.
4. **G4 measured — FAIL** (`b3f89dd`, corrected `5510628`, extended `27b0f2a`,
   `171f694`, `49ad4cc`, `c2c8197`). κ = 0.537 vs prespecified ≥ 0.75, raw
   0.813, n=150. Full diagnosis in `paper/draft.md` §4.4 and
   `docs/decision-log.md`.
5. **Paper prose**: abstract, §1, §2, §4.3, §4.4 drafted. §3, §5, §6, §7, §8
   still sourced outlines.
6. **Unslop pass** on the public surfaces (`b5f1f23`), guarded by tests.

### Open — Mehul's decisions

7. **The 28 sub-0.7 criteria.** Prespecified rule: drop and disclose the count,
   never rewrite. 25 of the 28 rest on a single sampled judgment, which the
   tooling itself calls a weak basis. Applying the rule means re-scoring against
   frozen artifacts and can move the 371. Declining it means walking away from a
   prespecified rule on the day it bit. **Note added 2026-09-14:** we now know
   dropping them cannot rescue the gate either (§4.4 counterfactual: repairing
   the absence defect perfectly still gives κ = 0.688, FAIL), so this decision
   is about discipline, not about the number. Decide and date it BEFORE any
   re-scoring runs.
8. **B4 human performance baseline** (~20 probes, 2 people, ~2h each, no model
   access). Was deferred until the G4 κ was known. It is now known.

### Open — work, in rough order

9. **§2 citations — CLOSED 2026-09-14** (`4b10fd8`). All 20 arXiv ids verified
   against primary sources, including the six post-cutoff ones, with a
   nonexistent-id control. **Nothing was fabricated**, the suspect MemPalace URL
   is real, and all six §2.3 quantitative claims traced. Three descriptions were
   wrong and are fixed. Two matter: **MEMTRACK (2510.01353) is an organizational
   benchmark, not a conversational one** — Slack/Linear/Git interleaving,
   conflict resolution, 60% best correctness — so §2.5's "GateMem is nearest"
   was wrong on that axis. The conjunction survives (MEMTRACK is single-agent,
   no witness model, no tiered authority, no supersession) and §2.5 now names
   which neighbour breaks which conjunct. And **the MemPalace claim was refuted
   by its own source**: the teardown documents three patches hand-coded against
   three failed questions, not probe content visible at ingestion; the paragraph
   now reports what the source says and attributes evaluation-time injection to
   our own threat model.
10. **Remaining prose — DONE 2026-09-14** (`e916bab`). §3, §5, §6, §7, §8 are
    prose; §7's notes are disclosures, including two newly written down (the
    judge/human presentation asymmetry, and judge identity being an unverified
    free-text tag). §4.4 carries the corpus-scale rates. Still open: the voice
    pass with Mehul (`mehul-voice` last).
11. **Verification gate** (`paper/checklist.md`): regenerate the floor numbers
    from committed raw outputs, grep for surviving comparative language,
    confirm all 13 disclosures present, repro from a clean clone.
12. **Hosting — DECIDED 2026-09-14: HuggingFace** (Mehul). `DOI_PLACEHOLDER`
    in `scripts/release.py` still needs replacing with the dataset URL once the
    repo exists. No DOI; the paper cites the URL.

13. **LaTeX paper — DONE 2026-09-14** (`c3e9dac`). `paper/memory-bench.tex`,
    arXiv single-column, self-contained, ~11.4k body words, seven TikZ/pgfplots
    figures, compiled with tectonic and every figure inspected in the rendered
    PDF. Author block solo, no affiliation (Mehul's decision). Venue: arXiv
    preprint now, NeurIPS Datasets & Benchmarks planned. Guarded by
    `tests/test_paper_tex.py`, whose bite was verified by corrupting three
    figure coordinates.

14. **Sub-0.7 rule — MEASURED AND DECLINED 2026-09-14** (`ae3783a`, `535b94b`).
    Applying it gives 341 against the frozen 371 and fails all six gates instead
    of three. Canon unchanged; published as a sensitivity with both numbers and
    the full sequence disclosed (`docs/decision-log.md`).

### In flight, not blocking

15. **Second independent rater on the 150-pair packet.** Mehul is recruiting;
    it takes calendar time because it is 150 judgments a person has to actually
    make. Nothing in Track A waits on it. When it lands it gives an inter-rater
    κ, the only thing that separates judge error from rater error, and would
    upgrade "the judge is degenerate on absence criteria" from our best reading
    to a demonstrated fact. It changes §4.4 and disclosures 1–2, and it is what
    would turn Track B from a short paper into a full one.
    Procedure: `docs/human-review.md` Task 3, two-rater section. The packet and
    the export/import tooling already exist; the rater needs
    `scripts/calibration_sheet.py export` run against
    `datasets/dev/calibration` and nothing else.

### Parked

16. **Re-anchoring under a successor worker**, if one is ever affordable. Rule
    and procedure: FREEZE amendment in `docs/dataset-plan.md` and the released
    `MAINTENANCE.md`.

---

## Track B — methodology paper (opened 2026-09-14, Mehul's proposal)

Mehul's framing: a second study on the data pipeline and "the models working in
a loop and us not being able to get the exact outcomes". **Next step is a
scoping conversation in a fresh chat**; nothing is written yet.

**The subject that works.** Not "how we built the pipeline" — that is §3 of a
dataset paper and no venue takes it standalone. The publishable subject is
**the measurement failures that appear when both the worker and the judge in a
benchmark are language models.**

**The structural constraint, which decides whether a split is even possible.**
The dependency runs one way. The methods paper stands alone with memory-bench
as its case study. The dataset paper **cannot** ship without §4: strip the
validity evidence and it is a synthetic benchmark nobody has run, which was
already its largest attack surface. So this is one self-contained methods
paper plus a dataset paper that keeps a condensed §4 and cites it. Two papers
both claiming "we built memory-bench" would fail the salami-slicing test;
these have distinct primary claims and do not.

**The four findings, all measured, all evidence already committed.**

| # | Finding | Evidence |
|---|---|---|
| 1 | Probe validity is worker-relative. 37/54 clusters survive the ceiling gate under one model, 17/54 under a smaller sibling, identical rules. A "valid item" is not a property of the item. | `docs/decision-log.md` Phase 3 |
| 2 | The harness is part of the model. Identical weights behind two scaffolds failed a **prespecified ≥90% per-condition bar**: twin-ceiling 13/20 (65%), while ceiling-pass 19/20 (95%) and floor pair-pass 20/20 (100%). Disagreement concentrates in the hardest condition. | `datasets/dev/screening/harness-study-2026-07-25/` (`protocol.json` carries the prespecified bar) |
| 3 | **Judge validation is direction-blind in aggregate.** The decoy audit returned a clean 2/41 and could not have failed: 30 of its 41 criteria were `fact_applied`, 11 `scope_correct`, **zero `fact_absent`**. Human calibration then found the judge over-accepts on all 8 of its absence-criterion errors (FALSE on 1 of 44 items) and under-accepts on all 7 scope errors. These cancel to a 14/14 split and a bias index of exactly **0.000**. Exposure: 218 of 371 instances (58.8%), concentrated 11-to-3 on the counterfactual side where pair credit compounds it. | `datasets/dev/calibration/`, `datasets/dev/screening/judge-decoys/audit.json` |
| 4 | Screening anchors die on the provider's schedule. The pinned worker was deprecated mid-study; the re-anchoring procedure is a first-hand account, not speculation. | `docs/decision-log.md` §2026-09-14, released `MAINTENANCE.md` |

Finding 3 is the strongest and is the transferable claim: **report judge
agreement per criterion type, because an aggregate false-accept rate — and even
an aggregate over/under-accept balance — can conceal opposite directional
failures that cancel.** Finding 4 is the one nobody else can write, because it
requires having been caught by it.

### Measured 2026-09-14 — two prespecified Track B results (commits `4ae19ef` → `b772fbc`)

Prespecified in `docs/decision-log.md` §2026-09-14 (Track B carve-out) **before
any verdict existed**; git corroborates the ordering. v1 canon untouched.

**5. The absence defect holds at corpus scale, and the floor run proves the
mechanism without human labels.** All 5,398 committed rubric-v2 verdicts joined
to criterion kind (lossless, zero unmatched): `fact_absent` passes **96.4%**
(n=1,463) against `fact_applied` 39.0% (n=2,677) and `scope_correct` 36.9%
(n=1,258), holding in all five source dirs (93.2–98.9%). Under the memoryless
floor — where the worker demonstrably knows nothing — `fact_applied` collapses
to 19.9% and `scope_correct` to 18.6% while `fact_absent` holds at **96.2%**.
Absence criteria do not respond to the condition that halves the other two.
Finding 3 no longer rests on the 150 ratings or on the single-rater limitation.
`datasets/methods/corpus-kind-rates/report.json`.

**6. LLM judges are highly reliable and jointly invalid — the strongest result
in the project.** Four blinded judges (haiku-4.5, sonnet-5, opus-5, fable-5.1)
re-judged the 478 semantic criteria on the 146 runs the calibration packet
spans, byte-identical batches, verbatim rubric v2.

| | judge ↔ judge | judge ↔ human |
|---|---|---|
| overall κ | **0.927–0.966** (n=478) | **0.518–0.563** (n=150) |
| pairwise identical verdicts | 0.964–0.985 | — |

On the 44 sampled `fact_absent` criteria all four panel judges produced
**byte-identical verdict vectors** (42 TRUE / 2 FALSE, same positions); v1
sonnet gave 43/1; the human gave 35/9. Model diversity across three capability
tiers buys **nothing** on this criterion class — the failure is perfectly
correlated. Consensus among LLM judges is therefore not evidence of validity,
which is the transferable claim.

The sonnet-5 test-retest arm settles the remaining alternative explanation:
fresh sonnet vs the committed v1 sonnet agrees at **0.973 / κ 0.944** (n=478).
κ = 0.537 is not judge instability; it is a stable, reproducible judge–human
divergence. `datasets/methods/judge-panel/report.json`.

Scoped honestly: the panel is **within-family** (all Anthropic, differing by
tier) and cannot separate "LLM judges as a class" from "Claude models as a
family". Declared in the prespecification, not discovered after.

**Sizing, revised.** Findings 5 and 6 replace the small-n problem: n=5,398 and
n=478 with a reproducing control (the scorer refuses to report unless the v1
baseline recomputes to n=150 / 0.813 / κ 0.537). This is a full paper without
the second rater; the second rater now corroborates rather than carries it.

**Open for the scoping chat:** Q1 framing (absence-first vs coverage-first vs
pipeline-first — recommendation: coverage-first, lead with the case), Q2 whether
the construction pattern is a §3 contribution, Q4 venue/deadline, Q5 the
undisclosed judge/human presentation asymmetry, and how much of §4 the dataset
paper keeps versus cites. Q3 (freeze carve-out) is settled and dated.

---

## Standing cautions

- Worker pin: every protocol path runs with
  `MEMBENCH_CODEX_BIN=~/.local/codex-0.144.5/node_modules/.bin/codex`; PATH
  `codex` may be newer. The pinned model is gone, so protocol paths cannot run.
- cursor-agent: QA and non-protocol work only. That is the documented
  consequence of a failed prespecified gate (§4.3), not a preference.
- Blinded judging always: `judge-export` → fresh judge agents that read only the
  batch file → `judge-import`; judge model ≠ worker model.
- Failed gates are carried as failures. Four have failed. Reporting them is the
  reason the rest of the numbers are worth reading.
- A background fork analysed G4 across six passes on 2026-09-14. Its judgment
  was good and its three central claims verified; its arithmetic drifted (129 vs
  218 on exposure, 6,349 vs 5,398 on verdict count) and by the end it was
  reading a stale draft. Take the argument, recount the numbers.
