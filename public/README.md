# memory-bench

A benchmark for organizational memory in agent harnesses. It asks whether a
memory system gives each person's agents the organization's knowledge with the
right scope, authority and freshness: a personal preference is not company
policy, a leadership decision outranks a loud opinion, and a superseded plan
stops driving behaviour while staying on record.

This repository holds the harness, the screening and scoring pipeline, the
evidence behind every number in the two papers, and the papers themselves. The
dataset lives on HuggingFace.

| | |
|---|---|
| Dataset and validity study | Srivastava (2026), [doi:10.5281/zenodo.22838320](https://doi.org/10.5281/zenodo.22838320) |
| Construction methodology | Srivastava (2026), [doi:10.5281/zenodo.22838602](https://doi.org/10.5281/zenodo.22838602) |
| Dataset | [huggingface.co/datasets/notmehul/memory-bench](https://huggingface.co/datasets/notmehul/memory-bench), CC BY 4.0 |
| Development record | [github.com/notmehul/memory-bench-history](https://github.com/notmehul/memory-bench-history) |

## What it measures

Three simulated software organizations, each a multi-week stream of meetings,
chat, email, documents and pull requests, delivered event by event to the
people who witnessed each event. A hidden ledger of facts decides what is true;
no language model does. The expected belief of any person at any moment is
computed from that ledger, and every scoring criterion derives from it.

Probes are work tasks, not quiz questions: write the announcement, draft the
checklist, prepare the review note. Every probe has a counterfactual twin whose
stream is identical except for the one fact under test, and an instance is
credited only when the system gets both sides right. A guess from a model's
priors passes one side and fails the other, so it earns nothing.

The released set is 371 paired instances across four archetypes, grouped by
the rung of the capability ladder each one tests. Results are always reported
per rung and never reduced to a single score.

| Rung | Archetype | Instances | What the agent has to get right |
|---|---|---:|---|
| 1, alignment | A4, tier collision | 106 | personal, team and org facts conflict, and context decides which wins |
| 1, alignment | A7, supersession chain | 172 | a fact updated two or three times, probed at each epoch |
| 2, coordination | A1, decision ripple | 50 | a decision taken in a meeting the probed person did not attend |
| 3, compounding | A2, silent rule | 43 | a working rule stated once, probed 30 or more events later |

## What v1 does not claim

It ranks no memory systems. The worker every item was screened against (gpt-5.4
at medium effort, behind codex-cli 0.144.5) was withdrawn by its provider on
2026-09-04, mid-pilot, before any system beyond the memoryless floor was
evaluated. Which items are valid depends on the worker, so results from a
different worker cannot be attached to these screening anchors. Running systems
needs a successor worker pinned and the anchors re-screened; `MAINTENANCE.md` in
the dataset gives the procedure.

Four prespecified gates failed and are reported as failures, including
judge-human agreement (Cohen's kappa 0.537 against a gate of 0.75). The
memoryless floor, the one clean positive result, credits 4 of 125 instances.
Both papers carry the full account.

## Check the papers' numbers

```
uv sync --extra figures --extra sheet
uv run pytest -q
```

The tests recompute the numbers in both papers from the evidence committed
under `datasets/` and fail on any mismatch, down to figure coordinates in the
LaTeX. A few checks need the rater key, which stays sealed until a second
independent rating of the calibration packet is done; those skip here and say
so.

## Get the dataset

```
uvx --from huggingface_hub hf download notmehul/memory-bench \
    --repo-type dataset --local-dir hf
cp -R hf/data/. datasets/dev/
```

That puts each organization's stream, probes and redacted `org.json` next to
the screening evidence already in `datasets/dev`, which is the layout the
harness reads by default. `.gitignore` keeps the copy out of commits.

## Run a memory system

A system under test implements three things (`src/membench/adapters.py`):

```python
counters: dict                                    # cost and call accounting
def ingest(self, principal: str, event: dict) -> None: ...
def run_task(self, principal: str, task: str) -> str: ...
```

The benchmark never inspects what a system stores or how. Register an adapter
in `src/membench/pilot.py` next to the eleven already there: four baselines, a
lexical ablation, four market systems, a per-principal silo ablation, and a
typed-memory reference that v1 registered but never ran. Then
see `scripts/run_pilot.py` for the run, blinded judging and report loop. The
worker caveat above applies.

## What is withheld, and why

The ground-truth ledger, probe plans, realization maps, annotated scoring
streams, the generator, the two unscreened holdout seeds and every rater key.
Each of them either contains the answers or rebuilds them: the generator is a
deterministic function of the seed and regenerates a holdout ledger's structure
exactly. The criteria a system is scored against are published on purpose,
because scoring is impossible without them; the withheld generator, the holdout
seeds and the canary strings in every stream are the answer to that.

`scripts/leak_audit.py` is how this tree was checked before it was published,
against every canonical fact string from all five seeds.

## Layout

- `paper/`: both papers, as LaTeX and as deposited PDFs
- `src/membench/`: runner, belief oracle, probes and scoring rules, adapters
- `scripts/`: screening, scoring, calibration, the judge-panel and
  criterion-kind analyses, the pilot loop, release tooling
- `datasets/dev/`: screening, calibration, pilot and harness-study evidence
- `datasets/methods/`: the construction paper's judge-panel and corpus analyses
- `docs/`: the capability ladder (`vision.md`), the design (`architecture.md`),
  the specs, the judge rubric, the rater protocol, and the market-system
  survey and configurations
- `tests/`: the number checks and the harness tests

## Independence

No memory system affiliated with the author is evaluated. Market systems enter
by published inclusion criteria and every exclusion is listed, in
`docs/vendor-survey.md`.

## Licence and citation

Code is MIT (`LICENSE`); the dataset is CC BY 4.0. `CITATION.cff` has both
papers. Author ORCID
[0009-0008-1031-304X](https://orcid.org/0009-0008-1031-304X).
