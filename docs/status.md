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

9. **§2 citations — BLOCKING.** Every reference is unverified. Six benchmark
   ids postdate the drafting agent's knowledge (LongMemEval V2 2605.12493,
   MemoryArena 2602.16313, GateMem 2606.18829, StreamMemBench 2606.14571,
   HorizonBench 2604.17283, MemDelta 2606.29914). Every number in §2.3 is
   secondary-sourced through our own audit notes. One recorded URL looks
   fabricated: `github.com/milla-jovovich/mempalace/issues/29`. Untraceable
   claims get cut, not softened. Detail in the §2 header note and
   `paper/checklist.md`.
10. **Remaining prose**: §3, §5, §6, §8; §7's 13 disclosures expanded into
    sentences. Then the voice pass with Mehul (`mehul-voice` last).
11. **Verification gate** (`paper/checklist.md`): regenerate the floor numbers
    from committed raw outputs, grep for surviving comparative language,
    confirm all 13 disclosures present, repro from a clean clone.
12. **Hosting + DOI**: pick the host (Zenodo gives a DOI, HuggingFace gives
    reach), then replace `DOI_PLACEHOLDER` in `scripts/release.py`.

### In flight, not blocking

13. **Second independent rater on the 150-pair packet.** Mehul is recruiting;
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

14. **Re-anchoring under a successor worker**, if one is ever affordable. Rule
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

**Honest sizing.** Small-n: 54 clusters for finding 1, 20 outcomes per
condition for finding 2, 150 pairs for finding 3 (the only one with real
statistical weight), and finding 4 is documentation rather than measurement.
That is a workshop or short paper as it stands. The second rater (Track A item
13) converts finding 3 into a decomposition of judge error by criterion type
with inter-rater agreement, which is what would make it a full paper.

**Open for the scoping chat:** framing and title, venue, how much of §4 the
dataset paper keeps versus cites, and whether to wait for the second rater.

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
