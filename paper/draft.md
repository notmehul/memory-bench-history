# memory-bench: A Screened Benchmark Dataset and Validity Study for Organizational Memory in Agent Harnesses

**Status, 2026-09-14.** Abstract, §1 and §2 are drafted prose; §3–§8 are still
sourced outlines. Reframed from "pilot numbers" to "dataset + construction
methodology + validity study" after the pinned worker (gpt-5.4) was deprecated
provider-side mid-pilot (`docs/decision-log.md` §2026-09-14). Every factual
claim carries its source so the prose can be checked line by line;
`tests/test_paper_numbers.py` asserts the headline numbers still match the
artifacts they came from. **All measured numbers are now in: G4 came back
2026-09-14 as a FAIL (κ = 0.537 against the prespecified κ ≥ 0.75), reported as
such in the abstract, §4.4 and disclosure 1.** Voice pass comes after the
structure settles; §2's citations are unverified and gated separately.

## Abstract

An organization's agents no longer run on one model: each person picks the
harness built for their work, and picks it *because* it is specialized. The
weights organizational knowledge must reach are therefore plural and
vendor-owned, so coherence cannot live in them. The memory layer is the only
place every harness can reach. Of eleven published memory benchmarks we could
verify (§2), none measures whether a memory system holds that knowledge with
the right scope, authority, and freshness.

We release memory-bench, an instrument for that question, with the evidence
that it measures what it claims. The dataset is three simulated software
organizations: multi-week event streams delivered event-by-event to each
principal who witnessed them, a hidden ground-truth ledger, and behavioral
work tasks injected at evaluation time rather than quiz questions. Every probe
instance is paired with a counterfactual twin in which the probed fact differs
and the rest of the stream is byte-identical; an instance is credited only when
both sides pass, so an answer available from prior knowledge earns nothing.
Across three seeds, 371 instances survive a five-gate screening pipeline under
blinded judging; two further seeds are withheld unscreened as holdouts.

The validity study is this paper's result. A memoryless worker's pair credit
is statistically indistinguishable from zero on every capability rung, which
is direct evidence that the design does not reward priors. Probe validity is
*task-model-relative*: under identical strict rules, 37/54 probe clusters
survived the ceiling gate for one worker and 17/54 for a smaller sibling. The
harness is part of the consumer: identical weights behind two agent harnesses
agreed on only 65% of twin-ceiling outcomes. The blinded judge's false-accept
rate against an adversarial decoy set was 2/41 as measured and 0/39 after
adjudication. Judge-human agreement on a blinded 150-pair packet reached 81.3%
raw agreement at κ = 0.537, which **fails** our prespecified gate of κ ≥ 0.75.
Aggregate disagreement is symmetric, 14 items each way, but that symmetry is a
cancellation rather than a property of the judge: every one of its errors on
absence-phrased criteria is an over-accept (8 of 8; it returns FALSE on 1 of 44
such items), and every one of its errors on scope criteria is an under-accept
(7 of 7). The over-accepts concentrate on the counterfactual side, 11 against
3, which is where pair credit multiplies them, and 58.8% of instances carry a
criterion of the lenient class. Our cheaper automated check, a 20-decoy
false-accept audit, passed this same judge at 2/41; resolving those 41 criteria
by kind shows none of them were absence-phrased, so that audit could not have
caught this. The transferable lesson is to report judge agreement per criterion
type, because an aggregate false-accept rate can conceal opposite directional
failures that cancel. The defect is contained: no side of any instance is
scored on absence criteria alone, so silence cannot pass, and the memoryless
floor stays at 4 of 125 instances.

Mid-study, the provider deprecated the pinned worker, which ended comparative
evaluation and exposed a dependency every agentic benchmark carries and few
state: screening anchors are properties of a worker, not of the data. We report
the event, release the partial rows as provenance, and specify the re-anchoring
procedure that lets the dataset outlive any single worker. No comparative
system result is claimed anywhere in this paper.

## 1. Introduction

### 1.1 Organizational knowledge has no home in the weights

Organizations are getting smaller while the number of agents working inside
them grows, and the agents are not interchangeable. A developer's coding
agent, a designer's creative tool, and a generalist assistant differ in system
prompt, tools, and defaults, and each is chosen for those differences. This
heterogeneity is a property of the ecosystem rather than a transitional
untidiness to be standardized away (`docs/vision.md` §1).

One structural consequence follows. If the weights an organization runs on are
plural and vendor-owned, then organizational coherence cannot live in them.
The decisions, working rules, preferences, and commitments that make a company
act like one company have to be held somewhere every harness can reach, and
the memory layer is the only such place. On this view a memory system is not
an accessory to an organization's agents; it is the connective tissue.

The naive version of that idea does not work. Pooling every artifact and
giving every agent the same view produces a rumor mill with perfect recall,
not a collective intelligence. A personal preference is not org policy. A
leadership decision outranks a loud opinion. A superseded plan must stop
driving behavior while remaining retrievable. A need-to-know fact must not
diffuse. What makes an organizational world model useful is that it is
*scoped, tiered, and temporally correct*: each agent receives the context
appropriate to its principal and its task, at the current epoch of truth
(`docs/vision.md` §2).

### 1.2 What existing benchmarks measure instead

Published memory benchmarks overwhelmingly evaluate a single agent's recall
over a long conversation: can the system retrieve a fact it was told earlier.
That is rung 0 of the capability ladder this benchmark is organized around
(§3.1), it is table stakes, and long context saturates it. Organizational
memory differs along three axes that single-agent recall does not exercise:
events have multiple witnesses and per-principal visibility, facts carry tier
and authority so that conflicts have correct rather than arbitrary
resolutions, and facts are invalidated over time rather than merely
accumulated.

The gap is not only in coverage. §2 surveys the field's measurement failures:
answers guessable from priors, corpora answerable without memory at all,
corrupted ground truth producing impossible ceilings, judges that accept
topical waffle, protocols loose enough to support score disputes between
vendors. These are the reasons this paper spends most of its length on
validity rather than on results.

### 1.3 What we claim, and what we do not

This paper claims an *instrument*, not a leaderboard.

We claim that the released dataset measures organizational memory behavior at
rungs 1–3 of the ladder, for a two-team simulated software organization at L1–
L2 scale, under a stated worker pin; and we report the measurements that
support or qualify that claim, including the ones that qualify it. We do not
claim that any memory system is better than another. This paper publishes no
comparative system numbers. We do not claim to measure "mini-AGI-ness," and
the external-validity claim stops at the organization type instantiated;
industry breadth enters a later version as a designed factor rather than by
relabeling this one (`docs/vision.md` §5). No result is ever reduced to a
single aggregate score: results are grouped by capability rung, always.

Three constraints were fixed before the evidence they govern was produced, and
each is corroborated by dated git history rather than by assertion: the gate
criteria and scoring rules (`docs/dataset-plan.md`), the worker and judge pins,
and the commitment to carry failed gates as failures rather than repairing the
probes that failed them. That commitment has a visible price in this paper.
**All three released seeds fail the instance gate** (125, 131, and 115 valid
instances against a threshold of 135), and **seed 3's cluster gate also fails**
(40/54 surviving clusters). The instances are retained, marked,
and reported as failures rather than topped up, because a gate that is relaxed
once it binds was never a gate (`datasets/dev/org-0000N/g3-report.json`,
`docs/decision-log.md`).

### 1.4 Contributions

1. **A screened dataset** (§3): 371 valid paired probe instances across three
   simulated organizations, with counterfactual twins, hidden ground-truth
   ledgers, and two unscreened holdout seeds. Every gate result is dated and
   corroborated by commit history.

2. **A construction and screening methodology** (§3): pair credit via
   counterfactual twins; per-item floor and ceiling validity screening with a
   pinned worker; blinded judging with a versioned rubric where the judge model
   is never the worker model nor the family that authored the criteria; a
   five-gate pipeline; and a statistics protocol prespecified before any
   result existed.

3. **A validity study** (§4): the measurements that test whether the instrument
   works: floor validation, the task-model-relativity of probe validity,
   harness sensitivity, judge false-accept rate, and judge–human agreement.

4. **A durability procedure** (§4.6): what it takes to keep an agentic
   benchmark valid when the worker it was screened under disappears. We did not
   choose this contribution; the provider deprecated our pinned worker
   mid-study and we documented what that costs and how to recover from it.

### 1.5 What this paper does not contain

It contains no system comparison. The pilot that would have produced one had
completed the memoryless floor condition and partial rows for four further
baselines when the pinned worker became unreachable through every available
billing path (§4.6). Because probe validity is worker-relative (§4.2),
attaching a new worker's results to anchors measured under the old one would
break both the normalization and the pair-validity argument, so we did not do
it. The partial rows are released in §6 as provenance for an interrupted
prespecified pilot, carrying no comparative claim.

## 2. Related work

> **Citations are unverified as of 2026-09-14. This section does not ship as
> written.** Every reference below is taken from this project's own field audit
> (`docs/standards-audit.md`, compiled 2026-07-25 from three sourced research
> reports). The findings attributed to each work were read off that audit, not
> re-read from the papers while drafting. Three specific risks:
>
> 1. **Six of the eleven benchmark citations postdate the drafting agent's
>    knowledge** and could not be checked against the source at all: LongMemEval
>    V2 (2605.12493), MemoryArena (2602.16313), GateMem (2606.18829),
>    StreamMemBench (2606.14571), HorizonBench (2604.17283), MemDelta
>    (2606.29914). Both the arXiv ids and the described contributions need
>    confirming.
> 2. **The quantitative claims in §2.3 are secondary-sourced** (6.4% bad gold,
>    93.6% ceiling, 63% judge false-accepts, 73% vs 68%, 74% grep agent, the
>    58/75/84 dispute). They came from blog posts and a Substack audit by way of
>    our own notes. Each needs tracing to its primary source, and any that
>    cannot be traced gets cut rather than softened.
> 3. **One source looks wrong on its face.** The audit records the MemPalace
>    teardown as `github.com/milla-jovovich/mempalace/issues/29`. A GitHub
>    handle identical to a well-known actor's name is the signature of a
>    fabricated reference, so treat this one as suspect until someone opens the
>    URL. The claim it supports (probe content visible at ingestion) is load
>    bearing for §3.1, so if the source does not exist, the claim goes and the
>    design rationale is restated from our own threat model instead.

### 2.1 What memory benchmarks currently measure

The established memory benchmarks evaluate one agent's recall across a long
conversation. LoCoMo (arXiv 2402.17753) and LongMemEval (2410.10813), with its
V2 revision (2605.12493), ask whether a system can retrieve a fact stated in an
earlier session, sometimes with a temporal qualifier. MemBench (2506.21605) and
MEMTRACK (2510.01353) extend the format. These are rung-0 tasks in the ladder
of §3.1: recall on request, which is table stakes for a memory system and which
long context saturates.

A second line moves toward agentic settings. MemoryAgentBench (2507.05257)
argues that pasting a conversation history into context evaluates memory
off-policy, since a deployed system writes its memory incrementally rather than
receiving the whole history at once. MemoryArena (2602.16313) evaluates
closed-loop single-principal agentic tasks. StreamMemBench (2606.14571) covers
streaming lifelog ingestion and feedback consolidation, and HorizonBench
(2604.17283) covers personal preferences that change over time. Each remains
single-principal.

The closest prior work is GateMem (2606.18829), which evaluates multi-principal
governance: utility, access control, and deletion. GateMem shares our premise
that a memory system serving several people is a different object from one
serving a single user. It scores access control on its own. We score governance
jointly against propagation, because the two pull in opposite directions and a
system can win either one by sacrificing the other (§3.1). That tension is the
reason v1 defers leakage scoring rather than reporting it alone.

### 2.2 Why organizational memory is a different object

Single-agent recall does not exercise three properties that decide whether an
organization's agents behave coherently.

**Events have witnesses.** In a conversation benchmark every turn is visible to
the one agent under test. In an organization a decision made in a meeting
reaches the people in the room, and whether it reaches anyone else is the
question being asked. Our streams are delivered per principal according to a
witness model, so a system that pools everything and a system that respects
visibility see different inputs by construction (§3.1).

**Facts carry authority and tier.** When a personal preference contradicts a
team convention, or a loud opinion contradicts a leadership decision, there is
a correct answer rather than an arbitrary one. Recall benchmarks have no notion
of a fact outranking another fact, so they cannot score getting it wrong.

**Facts are invalidated, not only accumulated.** A superseded plan must stop
driving behavior while staying retrievable on request. A benchmark that scores
retrieval alone credits a system for surfacing a fact that should no longer
apply.

Continual-learning and knowledge-editing work addresses the third property
inside the weights. This benchmark takes the harness position instead: the
knowledge an organization runs on changes faster than anyone retrains, and the
agents consuming it run on models the organization does not own (§1.1).

### 2.3 How memory evaluations have failed in practice

Most of this paper is validity evidence rather than results, and the reason is
that this field's published numbers have repeatedly failed on measurement
rather than on modeling. The audit that shaped our design recorded the
following, each of which maps to a mechanism in §3.

An independent audit of LoCoMo (Penfield Labs) reported roughly 6.4% corrupted
ground truth, which put a ceiling of about 93.6% on the benchmark while vendors
published scores above it. The same audit reported that an LLM judge accepted
topical but wrong answers at around 63%. Separately, a full-context baseline
scored 73% against Mem0's 68% on LoCoMo, which raises the question of whether
the corpus needed a memory system at all. Letta reported that a plain
filesystem-and-grep agent reached 74%, which is why a grep agent is one of our
registered baselines: a memory product should have to beat one.

Protocol looseness produced a public scoring dispute between Mem0 and Zep, with
the same system reported at 58, 75, and 84 depending on configuration and
denominator. Neither party was obviously acting in bad faith, which is the
point: without one prespecified scoring rule and one denominator, two honest
groups produce different numbers. MemDelta (2606.29914) reported that swapping
the embedding model moved results more than swapping the memory architecture,
which is why our RAG-class baselines pin and report their embedding model
(`docs/vendor-configs.md`).

A separate failure is contamination of the test itself. A teardown of MemPalace
found probe content visible at ingestion time, which lets a system be tuned to
the questions. Our probes are injected only at evaluation time, the ledger
stays private, and canary strings are embedded in every released stream.

### 2.4 Benchmark validity and benchmark decay

Work on benchmark quality supplies the standards this paper is written
against. BetterBench (2411.12990) assesses benchmarks across their lifecycle
and finds statistical reporting the most commonly failed criterion; the Agentic
Benchmark Checklist (2507.02825) sets out validity requirements specific to
agentic evaluation, including auditing a scorer against degenerate strategies;
and a construct-validity audit of 445 benchmarks (2511.04703) documents how
often a benchmark's measured quantity differs from its claimed one. Miller
(2411.00640) makes the case for error bars as standard practice in language
model evaluation, with small-sample interval guidance in 2503.01747. Work on
LLM judges (2306.05685) motivates measuring judge agreement rather than
assuming it. BenchBench (2407.13696) formalizes agreement testing between
benchmarks.

On decay: GSM1k (2405.00332) demonstrated contamination by regenerating a
held-out equivalent of a saturated benchmark, and LiveBench (2406.19314)
answers rot with continuous refresh. Both inform our release design, in which
the generator and two unscreened seeds are withheld so fresh organizations can
be minted if the public seeds are compromised (§8).

§4.6 adds a failure mode we have not seen addressed in this literature. The
decay work treats the *data* as the perishable component. For an agentic
benchmark, the worker model used to establish which items are answerable is
equally perishable, and it perishes on the provider's schedule rather than on
the benchmark's. We measured how much validity depends on that choice (§4.2)
and then lived through the dependency.

### 2.5 Where this benchmark sits

Of the eleven published memory benchmarks in our audit, none scores tiered
scope, authority weighting, propagation across principals, and supersession as
behavioral properties of an organization. GateMem is nearest and covers
governance for multiple principals; the recall benchmarks are a different rung.
We state this as the result of a search rather than as a fact about the
literature: the audit was compiled 2026-07-25 and names what it covered
(`docs/standards-audit.md`), and a reader who knows of prior work we missed
should read the claim as bounded by that date and that list.

What we believe is genuinely uncommon, and what §4 is spent defending, is the
combination of per-item floor and ceiling validity screening against a pinned
worker, counterfactual twins with pass-both-or-zero credit, a computable belief
oracle for ground truth, and a regenerable holdout.

## 3. The dataset and how it was built

### 3.1 Event streams and probes
- Simulated org event streams (`docs/specs/event-stream.md`); witnessed
  per-principal delivery; counterfactual twin streams.
- Probe archetypes by capability-ladder rung: A4, A7 (rung 1), A1 (rung 2),
  A2 (rung 3) (`docs/specs/probe-spec.md` v0.4.3, `docs/vision.md` §3).
- Pair credit: an instance passes only if base AND twin sides pass
  (`docs/specs/probe-spec.md` §4). This is what stops a system answering
  from priors.
- Streams carry no timestamps (`sim_time` null throughout; §7 item 11):
  temporal order is positional.

### 3.2 Screening and gates
- G0–G5 pipeline (`docs/dataset-plan.md`); what each gate screens.
- Blinded judging: opaque-id export → fresh judges → import; judge model ≠
  worker model ≠ criterion-author family (`AGENTS.md` hard rules).
- **Released dataset: seeds 1–3, 371 valid paired instances** (A1 50, A2 43,
  A4 106, A7 172; per-seed 125/131/115; cluster survival 46/54, 46/54,
  40/54). **Gate outcomes carried as measured: all three instance gates FAIL
  (135 required); seed 3's cluster gate also FAILs.** No probe that failed a
  gate was repaired. Seeds 4–5 unscreened holdouts. Freeze prespecified
  2026-08-15, corroborated by git history (`docs/decision-log.md`).

### 3.3 Harness and worker pinning
- All screening ran under one pinned worker (gpt-5.4, effort medium,
  codex-cli 0.144.5); §4.2–4.3 give the measured reasons a pin is
  load-bearing, §4.6 what happens when the pinned worker dies.

## 4. Validity study: the results core

Every number below was already measured; none of it needed the deprecated worker.

### 4.1 Gate results
- Per-gate outcomes by seed, failures carried as FAILs never repaired
  (`docs/validation-report.md`, `docs/decision-log.md`).

### 4.2 Probe validity is task-model-relative
- Ceiling-gate survival under identical strict rules: **37/54** clusters for
  gpt-5.4 vs **17/54** for gpt-5.4-mini (`docs/decision-log.md`, Phase 3).
  A "valid instance" is valid *for a worker*; the released valid set is
  defined relative to the screening worker, and the release documents the
  per-worker re-screening procedure.

### 4.3 Harness sensitivity

Before admitting a second agent harness to any protocol path we ran a
prespecified equivalence study: 60 seed-1 runs, 20 per condition, RNG seed
fixed, scored through the identical blinded pipeline, with the acceptance rule
written down before any run (`harness-study-2026-07-25/protocol.json`).
The bar was **outcome agreement ≥ 90% per condition**. The two harnesses ran
identical gpt-5.4 weights at identical effort; only the agent scaffold differed.

| condition | agreement | vs the 90% bar |
|---|---|---|
| floor pair-pass | 20/20, 100% | pass |
| ceiling-pass | 19/20, 95% | pass |
| **twin-ceiling pass** | **13/20, 65%** | **FAIL** |
| floor base-pass (ungated) | 15/20, 75% | — |

The study therefore failed its own acceptance rule, and the second harness was
confined to QA and non-protocol work on that evidence. Two things are worth
drawing out.

The disagreement is not uniform: it concentrates in the conditions that are
hardest to satisfy. Where the task is easy to fail (the memoryless floor, at
100%) or easy to pass (the ceiling with facts injected, at 95%) the harnesses
agree. The twin ceiling asks a worker to produce a deliverable consistent with
a counterfactual fact while an almost identical base fact is absent, and there
the same weights behind different scaffolds disagree on more than a third of
outcomes.

The consequence for the field is the one worth carrying: the harness is part of
the consumer, not a neutral pipe to the weights. A benchmark that pins a model
and not its harness has not pinned its worker, and a result reported without a
harness version is unanchored. It also explains why re-anchoring (§4.6) has to
fix the harness version alongside the model.

### 4.4 Judge validation

We ran two checks on the judge: a cheap automated one and an expensive human
one. They disagree about whether the judge is sound, and the reason they
disagree is the most transferable result in this paper.

#### The 20-decoy false-accept audit: PASS, and blind to the defect

Deliberately wrong-but-topical outputs were judged blind against the real
criteria: **2/41 false accepts as measured, 0/39 after adjudicating two
criteria an under-specified decoy legitimately satisfied**
(`datasets/dev/screening/judge-decoys/audit.json`, rubric v2). Read on its own
this says the judge does not accept plausible-sounding wrong answers, which is
the LoCoMo failure mode of §2.3.

Resolving those 41 criteria back to their kinds shows why that reading was
premature: **30 were `fact_applied`, 11 were `scope_correct`, and none were
`fact_absent`.** A decoy is built by stating wrong values, so it exercises
criteria that demand content. A criterion phrased as absence is satisfied by an
output that never raises the topic, so a decoy cannot probe it without being
built differently. The audit was structurally incapable of detecting a failure
on absence criteria, and that is exactly where the failure turned out to be.

#### G4 judge-human agreement: measured 2026-09-14, **FAIL**

The blinded 150-pair packet was rated by the single author-rater (the disclosed
downgrade, §7 item 1) and scored against the committed judge verdicts
(`datasets/dev/calibration/judge-agreement.json`, raw submission
`rater-M-filled-2026-09-14.xlsx`).

| | n | raw agreement | κ |
|---|---|---|---|
| **overall** | 150 | 0.813 | **0.537 (gate κ ≥ 0.75: FAIL)** |
| `fact_applied` | 72 | 0.819 | 0.605 |
| `scope_correct` | 34 | 0.794 | 0.561 |
| `fact_absent` | 44 | 0.818 | **0.166** |

Three things about this failure are worth stating precisely, because the
headline number alone misleads in both directions.

**The symmetry is a cancellation, not a property.** Aggregate disagreement
splits 14 and 14, and both raters label 72.0% of items positive, which invites
the conclusion that the judge is unbiased noise. The per-kind confusion matrix
says otherwise:

| kind | n | hT/jT | hT/jF | hF/jT | hF/jF | direction |
|---|---|---|---|---|---|---|
| `fact_absent` | 44 | 35 | 0 | 8 | 1 | judge over-accepts, every error |
| `fact_applied` | 72 | 40 | 7 | 6 | 19 | mixed |
| `scope_correct` | 34 | 19 | 7 | 0 | 8 | judge under-accepts, every error |

The judge is one-sidedly permissive on absence-phrased criteria and one-sidedly
strict on scope criteria, and the two cancel to zero in aggregate because this
packet happens to contain 44 of the first and 34 of the second. A different mix
of criterion kinds would not cancel. Any system scored on this benchmark
inherits a bias whose sign depends on which archetypes its instances draw from,
which is a property of the judge that no single agreement number reveals.

**The judge barely discriminates on absence criteria.** It returns FALSE on 1
of 44 absence-phrased items; the human rater returns FALSE on 9. A criterion of
the form "does not present X as current" is, in this judge's hands, close to
automatically satisfied. This is the concrete defect behind the low κ on that
kind, and it is a rubric problem: the absence rule is stated in
`docs/specs/judge-rubric.md` v2 without pinning the edge cases, and the judge
resolves the ambiguity permissively every time.

**κ = 0.166 on `fact_absent` is a base-rate artifact and must not be read as
"absence criteria are harder to agree on".** Raw agreement on that kind is
0.818, statistically indistinguishable from `fact_applied` at 0.819 and
`scope_correct` at 0.794. κ collapses only because the judge's 97.7% positive
rate pushes chance agreement to 0.782, leaving almost no headroom. We state
this explicitly because the opposite reading is the natural one and we made it
ourselves in an earlier draft of this section.

**On the gate itself.** The gate was κ ≥ 0.75. It failed at 0.537. That stands,
and the diagnostics below explain the mechanism rather than soften the verdict.
They were computed after the result and are labelled post-hoc; none was
prespecified.

| | agreement | κ | prevalence idx | bias idx | PABAK | Gwet AC1 |
|---|---|---|---|---|---|---|
| `fact_absent` | 0.818 | 0.166 | **0.773** | 0.182 | 0.636 | 0.772 |
| `fact_applied` | 0.819 | 0.605 | 0.292 | 0.014 | 0.639 | 0.667 |
| `scope_correct` | 0.794 | 0.561 | 0.324 | 0.206 | 0.588 | 0.627 |
| **overall** | 0.813 | **0.537** | 0.440 | 0.000 | 0.627 | 0.687 |

This is the kappa paradox: when one label dominates, κ penalizes residual
disagreement disproportionately. `fact_absent` carries the highest prevalence
index of the three at 0.773, and it is the one whose κ collapses while its raw
agreement matches the others to within a point.

Two things follow, and only the first is a defence of the measurement rather
than of the result. Prevalence-adjusted statistics put the same data between
0.59 and 0.77, so the disagreement is not the near-chance concordance a bare
κ = 0.537 suggests. And we prespecified κ rather than raw agreement precisely so
an unbalanced task could not be dressed up as validity, which means we do not
now get to discover the objection to our own gate on the day it fails. Leading
with AC1 = 0.687 and putting κ in a footnote would be the spin version of this
paragraph, and a reader who knows the reliability literature would recognize the
move immediately, because these are exactly the statistics people reach for when
κ disappoints.

The bias index is worth reading alongside §4.4's earlier finding. Overall it is
**0.000**, a perfectly unbiased judge by that measure, while within kinds it is
0.182 and 0.206 pointing in opposite directions. The aggregate figure is not
evidence of an unbiased judge; it is the numerical signature of two biases
cancelling, and it is the single clearest demonstration that per-kind reporting
is not optional.

#### Where the leniency lands, and why it matters more than its size

Two facts decide how far this propagates.

**The over-accepts concentrate on the counterfactual side.** Of the judge's 14
over-accepts, 11 fall on twin-side criteria against 3 on base-side; its
under-accepts split evenly, 7 and 7. This follows from the design rather than
from chance: a twin asserts that the base fact is *not* presented, so
absence-phrased criteria live disproportionately on that side (26 of the 44
sampled absence items). Pair credit requires both sides to pass, so a judge
that waves twin sides through inflates instance credit directly. The error is
in the direction that flatters a system under test.

**The exposed fraction of the dataset is not small.** 218 of the 371 valid
instances (58.8%) carry at least one `fact_absent` criterion: 199 on the base
side, 207 on the twin side, 188 on both. The criterion class where the judge is
measurably lenient is scored on nearly three instances in five.

Why the class behaves this way is mechanical rather than mysterious. "The note
does not present the 48h SLA as current" is satisfied by a note that never
mentions the SLA at all, so silence passes. The class has a degenerate pass
mode, the judge sits at 97.7% positive because of it, and κ has almost no
variance to track. The human rater's stricter 79.5% reflects counting
paraphrase and implication as presenting, which is what the rubric intends and
what the judge did not do. This is therefore as much a criterion-design defect
as a judge defect: an absence criterion carries little discriminative signal
unless it is paired with a positive criterion demanding the replacement value.

#### What the defect does not reach

The leniency is contained by a structural property of the probe set, which we
checked rather than assumed: **no side of any instance is scored on absence
criteria alone.** Every base side and every twin side across all 371 valid
instances pairs its absence criteria with at least one criterion demanding
positive content. An output that stays silent, or that knows nothing, cannot
pass even one side on the judge's leniency, because the positive criterion on
that same side still has to be satisfied.

The floor run bears this out empirically. Under a memoryless worker, 4 of 125
instances earned pair credit, which is the result reported in §4.5. If
twin-side leniency were letting ignorance through, the floor would be visibly
above zero, and it is not. **The judge defect therefore does not explain away
this paper's one positive result.**

What it does affect is the size of any future number on absence-heavy
archetypes. Exposure is uneven: A4 70.8% of valid instances, A7 57.0%, A2
55.8%, A1 42.0%. Any score later computed on A4 in particular should be read as
an upper bound rather than an estimate, and we say so here rather than leaving
it to be discovered.

#### Why we did not fix it, and why fixing it would not have passed the gate

The obvious response to a judge lenient on one criterion class is to rewrite
that class and re-judge. Two independent reasons say no.

**The arithmetic.** Recomputing κ on the same 150 pairs with the identified
defect removed is assumption-free, because it only requires flipping verdicts
we already have:

| scenario | agreement | κ | gate |
|---|---|---|---|
| as measured | 0.813 | 0.537 | FAIL |
| every absence false-accept eliminated | 0.867 | 0.688 | FAIL |
| every false-accept of any kind eliminated | 0.907 | 0.790 | PASS |
| both directional biases eliminated | 0.913 | 0.787 | PASS |

**Repairing the defect we found, perfectly, still fails the gate.** After
removing all 8 absence false-accepts, the residual error is 6 false-accepts and
7 false-rejects on `fact_applied`, which is genuine symmetric noise, plus 7
false-rejects and zero false-accepts on `scope_correct`, where the judge is
already too strict. The two faults point in opposite directions, and rubric
strictness is one dial. Turning it up to fix absence criteria makes scope
criteria worse. Passing requires fixing both biases in opposite directions and
lands at 0.787, a hair over the line and assuming a precision no rubric edit
delivers. So the G4 failure is not attributable to the absence defect alone,
and we say that rather than letting the defect carry the blame for the gate.

**The principle.** Even if the arithmetic worked, the criteria were frozen
before this evidence existed, and rewriting them now is the practice §2.3
condemns: LoCoMo's ground truth and the Mem0/Zep dispute are both the measuring
instrument moving after the measurement. The freeze that forbids this repair is
what makes every other number here checkable against dated git history, and it
cannot be spent selectively on the gates that fail. There is a subtler trap
too: our 150 human labels are judge-independent, so a new rubric genuinely
could be re-scored against them, but iterating rubric versions until κ clears
0.75 stops measuring judge quality and starts measuring how many attempts were
taken. An unbiased re-measurement needs a held-out calibration set we do not
have.

**What it would cost, for the record.** 5,398 criterion verdicts are committed
under rubric v2 across the four screened seeds and the floor run. All would
need re-judging, since a v3 verdict cannot be mixed with a v2 verdict for the
same reason anchors from two workers cannot be mixed. That much is mechanically
possible without the deprecated worker, since the worker outputs are cached and
re-judging is judge-side. But the 371-instance valid set is *defined* by
rubric-v2 verdicts, so a stricter judge changes which instances pass and the
dataset itself moves. This is a v2 project with a new rubric, a fresh held-out
calibration packet, and a full re-judge. It is not a patch, and no version of
it rescues v1.

The prespecified v2 fix: pair every absence criterion with a positive criterion
demanding the replacement value, so the class stops having a degenerate pass
mode.

One honest limit on the diagnosis itself. With a single rater we cannot
separate judge error from rater error, so "the judge is degenerate on absence
criteria" is our best reading of the evidence rather than a demonstrated fact.
The 43-of-44 positive rate makes it a strong reading, but one rater is one
rater, and a second independent rater is the first thing that would settle it.

**The methodological point, which generalizes past this benchmark.** Two
judge-validity checks, run on the same judge under the same rubric, returned
opposite verdicts. The cheap automated one passed and could not have failed,
because decoys are built by stating wrong values and therefore exercise only
criteria that demand content. The expensive human one failed and localized a
specific degenerate class. Anyone building an LLM-judged benchmark should
report judge agreement **per criterion type**: an aggregate false-accept rate,
and even an aggregate over/under-accept balance, can conceal opposite
directional failures that cancel.

**Per-criterion drops.** 28 criteria fall below the 0.7 raw-agreement rewrite
threshold. 25 of those were sampled once and 3 twice, so "below 0.7" means the
single sampled judgment disagreed; this is a weak basis for dropping an
individual criterion and the tooling says so. The prespecified rule is to drop
them and disclose the count, never to rewrite them. What this costs the scored
dataset is recorded in `docs/decision-log.md` §2026-09-14.

### 4.5 Floor validation: pair credit filters priors
- The no-memory floor, run end-to-end through the full pilot pipeline on
  seed 1 (125 instances × base+twin, 250 blinded verdicts, judge
  `claude-sonnet-5-blinded-v2`): **rung 1 pair credit 0.022 (95% CI ±0.040,
  n=92), rung 2 0.118 (±0.217, n=17), rung 3 0.000 (n=16)**
  (`datasets/dev/pilot/nomemory/seed-1/score-k1/report.json`, commit
  5959c26). A memoryless worker scores ≈0: the instrument does not reward
  prior knowledge or generic competence.

### 4.6 Benchmark durability: the deprecation event and re-anchoring
- Timeline (all dated in decision-log/git): freeze 2026-08-15 → pilot runs
  began 2026-09-02 → provider deprecated gpt-5.4 for the available billing
  paths (observed as a hard 400 by 2026-09-14; runs stalled 2026-09-04).
- Consequence, derived from §4.2: screening anchors die with the worker;
  partial SUT rows under the dead worker cannot be mixed with a new one.
- The re-anchoring procedure (successor-model rule, re-run anchors under the
  frozen gate rules with byte-identical task text, new valid set, then
  evaluate): specified here as the release's maintenance contract.

## 5. The instrument as released

- Adapter interface + 10 registered system configs (4 baselines ± lexical
  ablation, top-4-by-stars market systems, Mem0 silo ablation), per-system
  configs frozen before any live run with dated mechanical amendments only
  (`docs/vendor-configs.md`).
- Run/score/figures pipeline (resumable runs, blinded judge round trip,
  cluster-robust SEs, ≥2/3-seed direction rule, cost columns; zero
  hand-typed numbers).
- Live-smoke findings (2026-09-02) as evidence the harness meets real
  vendor APIs: Supermemory tag/nulls/hybrid-search amendments, Graphiti
  0.29.3 embedded-Kuzu repairs. All availability-only, dated.

## 6. Partial pilot record (provenance, not results)

- What ran before the stall (commit 5959c26): nomemory complete + judged
  (→ §4.5); fulltranscript 125 base / 109 twin, grep 125/46, rag 0/34,
  rag-lexical 125/29 non-empty rows of 125.
- These rows are released as provenance under the dead worker pin; they are
  NOT comparative results and no system claim is made from them. Framed as
  an honest record of an interrupted prespecified pilot.

## 7. Limitations and disclosures (each becomes a sentence or two)

1. **G4 FAILED.** Judge-human agreement is κ = 0.537 against a prespecified
   gate of κ ≥ 0.75 (81.3% raw, n=150; §4.4). The benchmark ships with a judge
   whose agreement with a careful human is measurably short of the bar we set
   for it, and every semantic verdict in this dataset inherits that error. The
   error is not uniform: the judge over-accepts on absence-phrased criteria
   (8 of 8 errors, FALSE on only 1 of 44 items) and under-accepts on scope
   criteria (7 of 7), which cancel in aggregate for this packet's mix of kinds
   and would not cancel for another. A score computed over a different
   archetype mix therefore carries a bias of a different sign. 28 criteria fall
   below the prespecified 0.7 rewrite threshold, 25 of them on a single sampled
   judgment. The lenient class is scored on 218 of 371 instances (58.8%) and
   the over-accepts land 11-to-3 on the counterfactual side, where pair credit
   compounds them. Our 20-decoy false-accept audit passed this judge at 2/41
   and could not have caught the defect: none of those 41 criteria were
   absence-phrased. Contained, not fatal: no side of any instance is scored on
   absence criteria alone, so the floor result is unaffected; but scores on
   absence-heavy archetypes (A4 70.8%, A7 57.0%) should be read as upper
   bounds. With one rater we cannot separate judge error from rater error, so
   the diagnosis is our best reading rather than a demonstrated fact.
2. Single author-rater for G4, who has seen seed content: a disclosed downgrade
   from the original two-rater design, so there is no inter-rater κ to separate
   judge error from rater error. A second independent rater is the first thing
   a v2 should buy.
3. Rank-direction rule ≥2/3 seeds was prespecified for the pilot; unused in
   this paper (no comparative claims).
4. All three released seeds fail the instance gate (125/131/115 against 135);
   seed 3 also fails the cluster gate (40/54). Instances retained and marked,
   never topped up or repaired.
5. Worker billing/auth changes during the study; model/binary pin held
   until provider deprecation ended all access (§4.6).
6. Market-system configs set internal LLMs to Gemini where configurable;
   deviations from vendor defaults named in `docs/vendor-configs.md`.
7. Shared-store configs do not enforce per-principal visibility; no leakage
   scoring in v1.
8. Silo ablation moved to Mem0 pre-run (full-transcript silo vacuous);
   dated in `docs/decision-log.md`.
9. Graphiti runs embedded Kuzu (deprecated upstream); adapter-side repairs
   documented.
10. Simulated orgs, not real logs; 3 screened seeds; single worker model.
11. Vendor right-of-reply: not triggered. This paper publishes no vendor
    numbers; the procedure remains specified for any re-anchored evaluation.
12. Event streams carry no timestamps; temporal order is positional;
    screening anchors never saw rendered timestamps.
13. Supermemory "dreaming" extraction is batched server-side; hybrid search
    mode documented (relevant to the released harness, not to any claim).

## 8. Release

Built and checked by `scripts/release.py build|verify`, so the bundle is
reproducible rather than hand-assembled and the withholding policy is
enforced by code.

- **Ships**: the SUT-facing streams, counterfactual twins, probes with their
  scoring assertions, the frozen valid sets, Croissant 1.0 + RAI metadata,
  `LICENSE-DATA` (CC BY 4.0; code stays MIT), `MAINTENANCE.md`, checksums, and
  a manifest naming what was withheld and why.
- **Withheld**: the ground-truth fact ledger (746 facts across the released
  seeds. It records which facts are probed and which are planted
  distractors), probe plans, realization maps, annotated scoring streams, the
  generator, the two unscreened holdout seeds, and every rater key.
- **Published on purpose**: the assertions. Scoring is impossible without
  them and a benchmark that hides its criteria cannot be audited; the cost is
  that the set is open-book by construction, which the withheld generator,
  the holdout seeds, and the embedded canary strings are the answer to.
- `verify` fails the release on a leaked ledger, a missing canary, a tampered
  file, or any withheld filename. Redaction is runnable-safe: the redacted
  bundle drives the real runner to the full frozen valid set (125 base + 125
  twin rows on seed 1).

(G5 tracker: `docs/standards-audit.md`. Nothing ships with a BLOCKING row
open; rows 1–3 closed 2026-08-15, row 9 closed here bar hosting and the DOI.)

## Appendices (planned)

A. Probe spec + rubric verbatim. B. Screening gate results by seed.
C. Floor run detail + per-instance table. D. Re-anchoring procedure.
E. Reproduction commands.
