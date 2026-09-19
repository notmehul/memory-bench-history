# memory-bench-history

The development record of memory-bench, from the first commit to publication.
The maintained repository, with the harness, the evidence and both papers, is
[github.com/notmehul/memory-bench](https://github.com/notmehul/memory-bench).

## Why this is public

Both papers claim that gates, thresholds and scoring rules were written down
before the evidence they govern existed, and that dated git history, not
assertion, is what shows it. This is that history, so the claim can be checked.
Start with `docs/decision-log.md` (dated, append-only), `docs/dataset-plan.md`
(the gates and the v1 freeze) and `docs/status.md` (the state at publication).

## What was removed from every commit

On 2026-09-19 the history was rewritten with `git filter-repo` to remove what the
release withholds, in every commit and not only the latest one:

- the ground-truth fact ledgers (`org.json`, and the copies `org.prev.json` and
  `org.partial.json`), probe plans, realization maps and annotated streams
- the generator (`src/membench/generator/`, `generate.py`, `pipeline.py`,
  `realize.py`) and its tests. It is a deterministic function of the seed and
  rebuilds a holdout ledger's structure exactly
- holdout seeds 4 and 5, everywhere they appeared, including their screening
  runs and human-check packets
- the G4 calibration ratings, agreement file and rater key, sealed until a
  second independent rater has rated the packet, and the human-check answer keys

Commit messages, authors and dates are as originally made. Hashes changed, so
`docs/commit-map.tsv` maps every original hash, as cited in the decision log and
elsewhere, to its rewritten one. `scripts/leak_audit.py` checked every blob in
every commit, and every message, against all 859 canonical fact strings from
the five seeds and their twins before this was published.

## What does not run here

With the generator and ledgers gone, the construction scripts and some tests no
longer run in this repository. Nothing here is maintained; use
[memory-bench](https://github.com/notmehul/memory-bench).

## Licence

Code MIT. Data CC BY 4.0, published at
[huggingface.co/datasets/notmehul/memory-bench](https://huggingface.co/datasets/notmehul/memory-bench).
