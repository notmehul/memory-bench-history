# Release copy, 2026-09-17

One source for the text that has to be identical in three places: the abstract
in the PDF, the Zenodo abstract field, and the HuggingFace dataset card. Three
different abstracts is how a scan goes wrong.

Nothing here is a claim the paper does not already make. If a number below stops
matching `paper/memory-bench.tex`, the paper is right and this file is stale.

## Abstract, canonical

Paste verbatim. Plain text, no markup, three paragraphs.

```
An organization's agents no longer run on one model: each person picks the
harness built for their work. The weights organizational knowledge must reach
are therefore plural and vendor-owned, so coherence cannot live in them. The
memory layer is the only place every harness can reach. Of the ten published
memory benchmarks we verified, none measures whether a memory system holds that
knowledge with the right scope, authority, and freshness.

We release memory-bench as an instrument for that question, and this paper is
the evidence that the instrument measures what it claims. The dataset is three
simulated software organizations: multi-week event streams delivered
event-by-event to each principal who witnessed them; a hidden ledger from which
the expected belief state B(p, t) is computed rather than asserted; and
behavioral work tasks injected at evaluation time rather than quiz questions.
Every probe instance is paired with a counterfactual twin in which the probed
fact differs and the rest of the stream is byte-identical. An instance is
credited only when both sides pass. Across three seeds, 371 instances survive a
five-gate screening pipeline under blinded judging; two further seeds are
withheld unscreened as holdouts. All three released seeds miss the prespecified
instance gate (125, 131, and 115 against 135). The misses are retained and
marked rather than repaired.

The validity study is the result. A memoryless worker earns pair credit on 4 of
125 instances, with 95% upper bounds of 10.6%, 44.1% and 19.4% by capability
rung. Probe validity is task-model-relative: under identical strict rules, 37/54
probe clusters survived the ceiling gate for one worker and 17/54 for a smaller
sibling. Identical weights behind two agent harnesses agreed on only 65% of
twin-ceiling outcomes, failing a prespecified 90% bar. Judge-human agreement on
a blinded 150-pair packet reached 81.3% raw agreement at kappa = 0.537, which
fails our prespecified gate of kappa >= 0.75. Aggregate disagreement is
symmetric, 14 items each way, but the symmetry is a cancellation: every judge
error on absence-phrased criteria is an over-accept, and every error on scope
criteria is an under-accept. Mid-study the provider deprecated the pinned
worker. We report the event, release the partial rows as provenance, and specify
the re-anchoring procedure that lets the dataset outlive any single worker. No
comparative system result is claimed anywhere in this paper.
```

The in-PDF version carries the section cross-reference and real Greek. This one
is ASCII because Zenodo and HuggingFace fields are not typeset.

## Zenodo record

| field | value |
|---|---|
| title | memory-bench: A Screened Benchmark Dataset and Validity Study for Organizational Memory in Agent Harnesses |
| authors | Mehul Srivastava, Independent researcher, ORCID 0009-0008-1031-304X |
| date | the date on the PDF first page, currently 19 September 2026 |
| abstract | the block above, verbatim |
| keywords | agent memory, benchmark construction, construct validity, LLM-as-judge, counterfactual evaluation, organizational knowledge, reproducibility |
| licence | data CC BY 4.0, code MIT |
| DOI | 10.5281/zenodo.22838321 (this record); 10.5281/zenodo.22838603 is the methodology paper |

Do not lead the record title with "LLM-as-a-Judge". The judge analysis is the
paper's most quotable section and the least accurate summary of what it is.

Upload the paper PDF, and separately the public bundle already specified in §8.
Never the ledger, the generator, the rater keys, or the holdout seeds. The
licence split on the record has to read the same as §8 does: data CC BY 4.0,
code MIT, ledger and generator withheld.

The paper carries its Zenodo DOI, 10.5281/zenodo.22838321, on page one, and
cites the methodology paper's, 10.5281/zenodo.22838603, in its bibliography.
It still carries no venue line: where it is hosted is the deposit page's
statement to make, not the PDF's. Both identifiers were reserved on the
deposit form and resolve only once the records are published. Publish both
before circulating either PDF, or the printed DOIs 404.

## Profile blurb

Goes next to the Zenodo link so a skimmer does not open a 25-page validity study
cold.

```
memory-bench is an evaluation instrument for organizational memory: scope,
authority, and freshness across principals who do not all see the same events.
Probes are work tasks, not quizzes. Every item has a counterfactual twin, so a
guess from model priors earns nothing. The paper is the validity study for that
instrument, including the gates that failed. No system ranking.
```

Then the Zenodo DOI (10.5281/zenodo.22838321) and the dataset URL.

## Still open: the HuggingFace card

The card is generated by `_readme()` in `scripts/release.py` and carries its own
three-line summary rather than this abstract. Making the three agree means
editing that template, rebuilding the bundle, and re-uploading to a repository
that has already been published. That is an outward-facing change and it has not
been made. It needs one explicit go-ahead, then
`scripts/release.py build` and `verify` on the rebuilt copy.
