# memory-bench: A Screened Benchmark Dataset and Validity Study for Organizational Memory in Agent Harnesses

**Status, 2026-09-14.** All sections are drafted prose and §2's citations are verified against primary sources. Reframed from "pilot
numbers" to "dataset + construction methodology + validity study" after the
pinned worker (gpt-5.4) was deprecated provider-side mid-pilot
(`docs/decision-log.md` §2026-09-14). Every factual claim carries its source so
the prose can be checked line by line; `tests/test_paper_numbers.py` asserts the
headline numbers still match the artifacts they came from. **All measured
numbers are in: G4 came back 2026-09-14 as a FAIL (κ = 0.537 against the
prespecified κ ≥ 0.75), reported as such in the abstract, §4.4 and disclosure
1.** One item remains before submission: the voice pass has not run.

## Abstract

An organization's agents no longer run on one model: each person picks the
harness built for their work, and picks it *because* it is specialized. The
weights organizational knowledge must reach are therefore plural and
vendor-owned, so coherence cannot live in them. The memory layer is the only
place every harness can reach. Of the ten published memory benchmarks we
verified (§2), none measures whether a memory system holds that knowledge with
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
caught this. The mechanism does not depend on the human labels: across all
5,398 committed criterion verdicts the absence class passes at 96.4% against
39.0% and 36.9% for the other two kinds, and under a memoryless worker, where
the other two roughly halve, it holds at 96.2%, unmoved by removing the very
knowledge the instrument measures. The transferable lesson is to report judge
agreement per criterion type, because an aggregate false-accept rate can
conceal opposite directional failures that cancel. The defect is contained: no
side of any instance is scored on absence criteria alone, so silence cannot pass, and the memoryless
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
(§3.3), it is table stakes, and long context saturates it. Organizational
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

> **Citation verification, 2026-09-14.** Every reference in this section was
> resolved against its primary source before submission, because the section was
> first drafted from this project's own field audit
> (`docs/standards-audit.md`, compiled 2026-07-25) rather than from the papers.
> All twenty arXiv ids resolve to a paper matching the name given, including the
> six that postdate the drafting model's knowledge, and a deliberate nonexistent
> id was checked to confirm that failures report as failures. Three descriptions
> were wrong and are corrected here: MEMTRACK is an organizational benchmark
> rather than a conversational one, LongMemEval V2 is a web-agent benchmark
> rather than a revision of the original, and the full-context-versus-Mem0
> comparison comes from Mem0's own paper rather than from a third party. One
> claim was refuted by its own source and has been rewritten rather than
> re-cited: see the note on post-hoc tuning in §2.3.

### 2.1 What memory benchmarks currently measure

The established memory benchmarks evaluate one agent's recall across a long
conversation. LoCoMo (arXiv 2402.17753) and LongMemEval (2410.10813) ask whether
a system can retrieve a fact stated in an earlier session, sometimes with a
temporal qualifier, and MemBench (2506.21605) extends the format. These are
rung-0 tasks in the ladder of §3.3: recall on request, which is table stakes for
a memory system and which long context saturates.

A second line moves toward agentic settings. MemoryAgentBench (2507.05257)
argues that pasting a conversation history into context evaluates memory
off-policy, since a deployed system writes its memory incrementally rather than
receiving the whole history at once. MemoryArena (2602.16313) evaluates
closed-loop single-principal agentic tasks. StreamMemBench (2606.14571) covers
streaming ingestion of egocentric lifelog data and feedback consolidation, and
HorizonBench (2604.17283) covers personal preferences that change over time.
LongMemEval V2 (2605.12493), despite the name, is a different object from the
original: a web-agent benchmark over trajectories reaching 115M tokens, scoring
static state recall, dynamic state tracking, workflow knowledge, environment
gotchas, and premise awareness. Each of these remains single-principal.

Two works are close enough that the distinction has to be drawn precisely rather
than by category.

MEMTRACK (2510.01353) is the nearest neighbour on the organizational axis, and
it is not a conversational benchmark at all. It models realistic organizational
workflows by interleaving asynchronous events across Slack, Linear, and Git,
with noisy, conflicting, and cross-referring information, and it scores
acquisition, selection, and conflict resolution rather than retrieval alone. Its
best reported model reaches 60% correctness. Anyone reading our framing should
read MEMTRACK first. What separates it from this work is not ambition but
structure: MEMTRACK is single-agent, so it has no witness model and no notion of
a fact reaching one person and not another. It scores conflict resolution
without tiered authority deciding which side of a conflict is correct, and
without supersession as a distinct failure mode from retrieval.

GateMem (2606.18829) is the nearest neighbour on the multi-principal axis,
evaluating memory governance for shared-memory agents across utility, access
control, and deletion. It shares our premise that a memory system serving
several people is a different object from one serving a single user. It scores
access control on its own; we score governance jointly against propagation,
because the two pull in opposite directions and a system can win either by
sacrificing the other. That tension is the reason v1 defers leakage scoring
rather than reporting it alone.

### 2.2 Why organizational memory is a different object

Single-agent recall does not exercise three properties that decide whether an
organization's agents behave coherently.

**Events have witnesses.** In a conversation benchmark every turn is visible to
the one agent under test. In an organization a decision made in a meeting
reaches the people in the room, and whether it reaches anyone else is the
question being asked. Our streams are delivered per principal according to a
witness model, so a system that pools everything and a system that respects
visibility see different inputs by construction (§3.2).

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

An independent audit of LoCoMo (Penfield Labs, 2026-04-08) found 99
score-corrupting errors in 1,540 questions, roughly 6.4%, putting a ceiling of
about 93.6% on the benchmark while vendors published scores above it. The same
audit reported that an LLM judge accepted topical but wrong answers at 62.81%.
The audit is self-published rather than peer-reviewed, and its author
independently discloses the same finding in a public issue thread, so the figure
has two routes rather than one.

The comparison that should carry the most weight comes from a vendor's own
paper. Mem0's evaluation (2504.19413, Table 2) reports a full-context baseline
at 72.90% against Mem0's graph variant at 68.44% and plain Mem0 at 66.88%. The
system's own published table shows the no-memory-system baseline winning, which
raises the question of whether the corpus needed a memory system at all. Letta
separately reported that a plain filesystem-and-grep agent reached 74.0%. That
is why a grep agent is one of our registered baselines: a memory product should
have to beat a directory of files.

Protocol looseness produced a public scoring dispute between Mem0 and Zep, with
the same system reported at 84%, then 75.14%, then 58.44% depending on
configuration and denominator. Neither party was obviously acting in bad faith,
which is the point: without one prespecified scoring rule and one denominator,
two honest groups produce different numbers. MemDelta (2606.29914) found that an
embedding-only swap shifted accuracy by 6.2 points (p = 0.004) while the
architectural comparison it ran, verbatim RAG against full context, was not
significant (47.2 against 49.8, p = 0.34). That is why our RAG-class baselines
pin and report their embedding model (`docs/vendor-configs.md`).

A separate failure is fitting the system to the test after seeing it. A public
teardown of MemPalace documents three patches hand-coded against three specific
questions the system had failed, a quoted-phrase boost, a person-name boost, and
a pattern match for two particular phrasings, after which the result was reported
as the first perfect score on LongMemEval. The reporter's summary is that the
fixes were designed around the exact failure cases rather than discovered by
analyzing general failure patterns. The same teardown records retrieval
parameters set beyond the size of the corpus being searched and a metric
mismatch against other systems' end-to-end numbers.

We should be precise about what this does and does not motivate, because an
earlier draft of this paragraph overstated it. The documented failure is
test-set inspection followed by targeted repair, not benchmark content being
visible during ingestion. It is an argument for a withheld ledger, for holdout
seeds that can be regenerated, and for a freeze that makes post-hoc repair
visible in git history, all of which this paper's design carries. The separate
decision to inject probes only at evaluation time comes from our own threat
model rather than from this source.

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

On decay: GSM1k (2405.00332) regenerated a held-out equivalent of a saturated
benchmark and found accuracy drops of up to 8% in some model families, with
frontier models showing little overfitting, and LiveBench (2406.19314) answers
rot with continuous refresh. Both inform our release design, in which
the generator and two unscreened seeds are withheld so fresh organizations can
be minted if the public seeds are compromised (§8).

§4.6 adds a failure mode we have not seen addressed in this literature. The
decay work treats the *data* as the perishable component. For an agentic
benchmark, the worker model used to establish which items are answerable is
equally perishable, and it perishes on the provider's schedule rather than on
the benchmark's. We measured how much validity depends on that choice (§4.2)
and then lived through the dependency.

### 2.5 Where this benchmark sits

Of the ten published memory benchmarks in our audit, none scores tiered scope,
authority weighting, propagation across principals, and supersession together as
behavioral properties of an organization. The claim is a conjunction, and it is
worth saying which neighbour breaks which part of it. MEMTRACK already works in
an organizational setting with interleaved multi-platform events and conflicting
information, so the novelty is not the setting; what it does not have is a
witness model, tiered authority deciding conflicts, or supersession scored apart
from retrieval. GateMem already serves multiple principals with access control,
so the novelty is not multi-principal governance; what it does not do is score
governance against propagation, where the two trade off. The recall benchmarks
sit on a different rung entirely.

We state this as the result of a search rather than as a fact about the
literature. The audit was compiled 2026-07-25 and names what it covered
(`docs/standards-audit.md`), the citations were verified against primary sources
on 2026-09-14, and a reader who knows of prior work we missed should read the
claim as bounded by that date and that list.

What we believe is genuinely uncommon, and what §4 is spent defending, is the
combination of per-item floor and ceiling validity screening against a pinned
worker, counterfactual twins with pass-both-or-zero credit, a computable belief
oracle for ground truth, and a regenerable holdout.

## 3. The dataset and how it was built

### 3.1 Ground truth is computed, not asserted

The design decision everything else rests on is that this benchmark's answer
key is a function, not a list of question–answer pairs written by a model.

Each simulated organization has a private ledger of facts
(`docs/specs/ledger-schema.md`): decisions, working rules, preferences,
commitments, each with a tier (`personal`, `team`, `project`, `org`,
`external`), a capacity (`formal_decision` > `directive` > `opinion` >
`speculation`), a visibility, a validity window, and the events that evidence
it. From the ledger and the event index we compute the **expected belief
state** `B(principal, t)`: every fact that principal is entitled to hold at that
moment. A fact is in `B` when the principal witnessed it, when its visibility
permits them, when it is valid and unsuperseded at `t`, and when its decay class
still holds. Superseded facts move to a historical set `B_hist` rather than
vanishing, because a superseded plan must stop driving behavior while staying
retrievable.

Conflicts resolve by stated precedence: higher capacity first; at equal
capacity the tier matching the *artifact* being produced wins, so an org policy
governs an org-facing document and a personal preference governs a personal one;
then recency. A pair that remains tied is not a defect to be broken arbitrarily
but a genuine unresolved contradiction, where correct behavior is surfacing the
conflict rather than silently picking. Rule two is what makes precedence
contextual instead of a fixed hierarchy, and it is the mechanism the scope
archetypes probe.

`B` is a pure function over (ledger, event index) and is the single scoring
oracle. Two consequences matter for validity. Ambiguity in `B` is a spec bug
that blocks release rather than a judgement call resolved per item, and both
spec bugs found this way were fixed before any screening: distributed facts
originally required witnessing only one evidence event, which let principals
hold facts they could not have assembled, and departed principals needed an
explicit empty belief state. More importantly, no language model is anywhere in
the ground-truth path. The models render events and author scoring criteria;
they never decide what is true.

### 3.2 Streams, witnesses, and what the system under test sees

Each organization's history is a stream of naturalistic communication:
meetings, DMs, team and org chat, email threads, documents, tickets, pull
requests, calendar entries, with facts embedded in the prose as a person would
express them, in the author's voice, never in ledger-canonical form
(`docs/specs/event-stream.md`). Fact annotations are stripped before the stream
reaches a system under test; the annotated copy is private to scoring.

There is no global feed. The runner delivers each event only to the principals
who witnessed it: participants always, plus anyone entitled to the surface it
appeared on, since channel history is readable. A decision taken in a platform
standup reaches a growth-team principal only if some later event carries it
across, or if the memory layer under test does. That is what makes propagation
a measurable property rather than an assumption, and it is why a system pooling
everything and a system respecting visibility receive different inputs by
construction. The adapter's entire ingestion surface is one call,
`ingest(principal_id, event)`, invoked once per witness per event; what a system
does internally, whether one shared store or per-principal stores, is its
own business, and it is scored against `B(principal, t)`.

Realism is a set of generator obligations, not an aspiration. At least 60% of
event content is operational filler embedding no probed fact, so a memory system
has to find signal rather than summarize everything. Every probed fact is
accompanied by at least two distractor facts, including at least one near-miss
differing by a single attribute: wrong tier, expired, or lower authority. No
fact's canonical text may appear verbatim in more than one event, which forces
paraphrase and blocks string-match shortcuts. Canary strings sit in event text
at low frequency for post-hoc contamination detection. Timelines are sized so
the annotation-stripped transcript exceeds roughly 500k tokens, which keeps
full-transcript-in-context an honest but costly baseline rather than a free win.

Salience parity is achieved by construction and then tested. Distractor type,
register, shape, length, and numeric form mirror the probed mix, and positions
are assigned mechanically to class-stratified band centers rather than by
re-rendering until a lint passes. The test is a blinded discrimination check:
a rater sees 20 excerpts, half embedding probed facts and half distractor-only,
and must not beat 65%. Machine raters across five seeds scored 58/100 in
aggregate (binomial p = 0.067, not significantly above chance); human raters
scored 50% and 60% on the two seeds a rater could take uncontaminated
(`docs/validation-report.md`, `datasets/dev/human-check/`). One residual is
documented rather than resolved: seed 3 repeatedly scores above the others
(42/60 across three independent samples, p ≈ 0.001), two targeted content passes
failed to remove it, and it ships disclosed, with users of salience-sensitive
analyses pointed at the other seeds.

### 3.3 Probes are work, and every probe has a twin

A probe is not a question. It is a work task issued to a principal's agent at a
point in the timeline: write the announcement, draft the checklist, prepare the
review note. What is scored is whether the resulting artifact behaves as the
organization's knowledge requires. Probes are injected only at evaluation
time and never appear in the ingested stream, which is the countermeasure to
tuning a system on the questions.

Four archetypes instantiate the capability ladder (`docs/vision.md` §3): A4 and
A7 at rung 1, alignment, where the right tier must win and current truth must
drive behavior; A1 at rung 2, coordination, where knowledge must cross
principals; A2 at rung 3, compounding, where the organization should apply its
own history unprompted. v1 is a deliberate vertical slice, at least one
archetype on every rung above retention, rather than exhaustive coverage of any
one rung.

Every probed fact has a counterfactual variant, and the generator produces a
**twin organization** from the same seed and the same timeline skeleton with the
delta facts re-rendered. The same probe runs against both. An instance is
credited **only when both sides pass**: correct behavior on the base
organization, and correctly *different* behavior on the twin. Passing one side
scores zero for the pair.

This is the single most load-bearing design choice in the dataset, because it is
what makes a plausible guess worthless. A fact invented by a language model
often coincides with that model's own prior, whether a naming convention, a
review threshold or a default cadence, and a memoryless system can guess the base side
at a rate that would flatter it badly. It cannot guess both sides, because the
twin's answer is the one its priors argue against. §4.5 reports what this buys:
under a memoryless worker, 4 of 125 instances earn pair credit.

Assertions come in several kinds, among them `fact_applied`, `fact_absent`,
`scope_correct` and `conflict_flagged`. Each is checked by regex, by structural
parse, or by a blinded semantic judge. Which checker is allowed where was settled by
measurement rather than preference. Applied-content assertions written as
regexes failed 39–42% of ceiling runs, because a deliverable paraphrases around
any anchor; absence detectors failed 4% and semantic criteria 9–17%. Spec v0.3
therefore requires the semantic checker for applied content and reserves regex
for absence detectors (`docs/specs/probe-spec.md` §3). Assertion text was
LLM-authored under a fixed prompt and accepted only after mechanical validation:
answer-token hygiene, 4-gram overlap against the task text, and pattern
cross-validation requiring each pattern to match every surface variant of its
own side and no variant of the other side or of a sibling fact. One further
authoring rule came out of failure adjudication and matters more than it looks:
an assertion must never punish content drawn from a different co-valid fact of
the same cluster, because complementary facts are not competing answers.

### 3.4 Screening: which items actually measure memory

Every probe instance runs in three conditions. `floor` gives the task alone with
no organizational context. `ceiling` gives the task plus exactly the relevant
facts from `B(principal, t)`, rendered canonically. `sut` gives whatever the
system under test provides. A system's score is normalized as
`(sut − floor) / (ceiling − floor)`.

The floor and ceiling conditions are not only a normalization; they are the
screen. An instance is valid when its ceiling passes, its twin ceiling passes,
and its floor output fails at pair level. A ceiling that fails means the item
measures reasoning rather than memory: the facts were supplied and the worker
still could not produce the artifact. A floor that passes means the item is
answerable without memory at all. Both get dropped, and the per-side floor pass
rate survives as a reported `guessability` figure per cluster.

Two revisions to this rule were forced by measurement and are dated before the
evidence they govern. The floor gate moved to pair level once it was clear that
canonical facts sometimes coincide with industry defaults, so a per-side rule
discarded valid pairs for the exact reason the twin design exists. And screening
moved from clusters to instances: requiring all three instances of a cluster to
be valid demands per-run reliability near 98%, since 0.9⁶ ≈ 0.53 cluster
survival follows even at 9% instance noise, which no realistic worker–judge pair
delivers at n=3. A cluster now survives with at least 2 of 3 valid instances and
ships only those. Both the instance-level and the stricter all-instances counts
are reported throughout.

Semantic verdicts are produced blind. `judge-export` writes each output with its
criteria under opaque ids, stripped of probe identity, condition, and
base-versus-twin side; fresh judge agents read only that batch file; `judge-import`
validates the ids and criterion keys before anything is recorded. The judge model
is never the worker model and never the family that authored or repaired the
criteria being judged, and the rubric is versioned verbatim in the repository
(`docs/specs/judge-rubric.md`). Blinding is enforced in code rather than by
instruction. It is worth reporting that blinding changed little: an earlier
unblinded pass over the same seed-1 material agreed with the blinded verdicts on
97.6% of criteria, 26 flips out of 1,092, split 14 True→False against 12
False→True with no systematic direction. Blinding is cheap insurance here rather
than a large correction, and we would rather publish that null than imply we
caught a bias we did not measure.

### 3.5 What the released dataset is

Seeds 1–3, probe-spec v0.4.3, judge rubric v2: **371 valid paired instances**
(A1 50, A2 43, A4 106, A7 172). Per seed the valid-instance counts are 125/131/115,
from cluster survival of 46/54, 46/54, 40/54; the stricter all-instances counts
are 33, 39 and 35. Construction produced 54 clusters × 3 instances × 5
organizations, 810 instances in total, of which seeds 4 and 5 are withheld
unscreened as holdouts.

**All three instance gates fail.** The prespecified threshold was 135 valid
instances per seed, and the three seeds delivered 125, 131, and 115. **Seed 3's
cluster gate also fails**, at 40 surviving clusters against a floor of 45. No
probe that failed a gate was repaired, no criterion was rewritten to recover an
instance, and no gate was relaxed after it bound. The shortfall is structured
rather than random: it is the residual tail of counterfactual-anchoring failure
on the twin side, the same defect family that drives cluster drops, and the
prespecified v2 response is to over-generate four instances per cluster and
require counterfactuals to invert the aspect the task actually elicits.

The dataset was frozen on 2026-08-15 before any system was evaluated, and the
freeze is corroborated by dated commits rather than by assertion
(`docs/dataset-plan.md`, `docs/decision-log.md`).

### 3.6 Worker and harness pinning

All screening ran under a single pinned worker: gpt-5.4 at medium reasoning
effort behind codex-cli 0.144.5, with the binary pin enforced in code rather
than by convention, because the system `codex` upgrades silently. The pin is not
housekeeping. §4.2 shows that which items survive screening is a property of the
worker, §4.3 shows that the agent harness around identical weights changes
outcomes enough to fail a prespecified equivalence bar, and §4.6 reports what
happened when the provider withdrew the pinned model mid-study.

## 4. Validity study: the results core

Every number below was already measured; none of it needed the deprecated worker.

### 4.1 Gate results

Six gates run during construction, and their outcomes are reported as measured.
G0 and G1, the belief-oracle test suite and the schema, oracle cross-check,
ambiguity scan, and interleaving checks, passed on every seed. G2's machine side
passed: structural regeneration, realization checks, and the release-blocking
stream lint covering marker round-trip, visibility consistency, salience
permutation tests, a noise floor, and canaries all report green across five
organizations and their twins. Two of G2's human items remain open by the
freeze, and the salience residual on seed 3 is documented rather than repaired
(§3.2).

G3 is where the failures are, and they are the reason the rest of this section
is worth reading.

| seed | clusters surviving | valid instances | instance gate (≥135) | cluster gate (≥45) |
|---|---|---|---|---|
| 1 | 46/54 | 125 | **FAIL** | pass |
| 2 | 46/54 | 131 | **FAIL** | pass |
| 3 | 40/54 | 115 | **FAIL** | **FAIL** |

Two further prespecified bars failed: the harness-equivalence study of §4.3, and
G4 in §4.4. Four failures against one clean positive result, the memoryless
floor of §4.5.

No probe that failed a gate was repaired to recover it, no criterion was
rewritten after seeing that it cost an instance, and no threshold moved once it
bound. Where repairs did happen they were made blind to direction, before the
evidence they touched, and are recorded with the risk stated in advance: the
cross-organization lineage sweep was applied without knowing whether it would
move counts up or down, and it moved them both ways. The consistency pass found
exactly two defects across five seeds, single filler lines asserting rule content
that contradicted a probed fact, and both were replaced with inert material.

A gate that is relaxed once it binds was never a gate, so we would rather publish
a dataset that fails its own thresholds than one whose thresholds were chosen
after the fact. That is the whole argument for trusting the numbers that did
pass.

### 4.2 Probe validity is task-model-relative

Screening asks whether a worker given exactly the right facts can produce the
artifact the task requires. That question has a different answer for different
workers, and the size of the difference is the finding.

Under identical strict rules, **37 of 54** probe clusters survived the ceiling
gate for gpt-5.4 and **17 of 54** for gpt-5.4-mini, a smaller model from the
same family. Less than half. Nothing about the probes changed between those two
numbers; the items are the same items and the rule is the same rule.

The consequence is that a valid item is not a property of the item. It is a
property of the pair, item and worker, and a released valid set is defined
relative to the model that screened it. This is not a quirk of our design. Any
benchmark that decides which of its items are answerable by checking whether a
model can answer them inherits the same relativity, whether or not it says so.
Most do not say so, and many do not fix the worker at all, which makes their
item sets quietly unreproducible.

We handle it by pinning the worker, reporting the pin everywhere a number
appears, and publishing the per-worker re-screening procedure so a future user
can re-derive a valid set under whatever model they have. §4.6 is what happens
when that future arrives sooner than expected.

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

#### The mechanism at corpus scale, without human labels

Everything above rests on 44 absence-phrased items in one 150-pair packet, which
is a thin base for a claim about the instrument as a whole. The mechanism,
a criterion class with a degenerate pass mode, can be measured without human
labels at all, on every verdict the project has committed, and it was.

Joining all **5,398** committed rubric-v2 criterion verdicts to their assertion
kind gives the judge's positive rate per class (the join is deterministic and
lossless; `datasets/methods/corpus-kind-rates/report.json`):

| kind | n | positive rate |
|---|---|---|
| `fact_absent` | 1,463 | **96.4%** |
| `fact_applied` | 2,677 | 39.0% |
| `scope_correct` | 1,258 | 36.9% |

The 97.7% observed on 44 sampled items was not a sampling artifact. The rate
holds across all five sources of verdicts with no exception, from 93.2% to
98.9%.

The memoryless floor run supplies the control that makes this diagnostic rather
than merely descriptive. Under a worker with no organizational context, one
that demonstrably cannot know the facts, `fact_applied` collapses to 19.9% and
`scope_correct` to 18.6%, roughly half their screening-condition rates.
`fact_absent` holds at **96.2%**, statistically unmoved. A criterion class that
does not respond to removing the very knowledge the instrument is built to
measure is not discriminating; it is passing by construction, and the two
criterion kinds beside it in the same runs, judged by the same judge under the
same rubric, show what responding looks like.

This is a re-analysis of already-committed verdicts rather than a new
measurement: no output was re-run, no criterion re-judged, and no valid set
moved. It was prespecified and dated before it was computed
(`docs/decision-log.md` §2026-09-14), and it is reported here as a statement
about the mechanism, never about accuracy. With no human labels outside the
150, it cannot and does not claim to measure whether the judge is *right*.

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

One honest limit on the diagnosis, now narrower than it was. The two halves of
the claim rest on different evidence and should be read differently. That the
class has a **degenerate pass mode** is demonstrated without human labels, on
1,463 verdicts, with the floor run as a control: it does not respond to removing
the knowledge under test while the criterion kinds beside it halve. That the
judge's permissiveness is **wrong on particular items** still rests on one
rater, and with one rater we cannot separate judge error from rater error. So
the mechanism is measured and the misclassification rate is a strong reading of
thin evidence. A second independent rater remains the thing that would settle
the second half, and it would not change the first.

**The methodological point, which generalizes past this benchmark.** Two
judge-validity checks, run on the same judge under the same rubric, returned
opposite verdicts. The cheap automated one passed and could not have failed,
because decoys are built by stating wrong values and therefore exercise only
criteria that demand content. The expensive human one failed and localized a
specific degenerate class. Anyone building an LLM-judged benchmark should
report judge agreement **per criterion type**: an aggregate false-accept rate,
and even an aggregate over/under-accept balance, can conceal opposite
directional failures that cancel.

#### Per-criterion drops: a prespecified rule we measured and then declined

28 criteria fall below the 0.7 raw-agreement threshold. The prespecified rule is
to drop them and disclose the count, never to rewrite them. We report this at
length because the sequence matters more than the outcome.

We committed to applying the rule and recorded that commitment, with the
direction of the change stated as unknown, before any re-score ran. We then ran
it. Dropping the 28 takes the dataset from **371 to 341 valid instances** and
moves seeds 1 and 2 from a passing cluster gate to a failing one, 46/54 becoming
40/54 and 41/54. Before the drop, three of six gates failed. After it, all six
do. Seed 3 is unchanged, which is the control behaving: none of the 28 criteria
are in it.

Having seen that, we kept the frozen 371 and publish the drop as a sensitivity
(`datasets/dev/screening/sub07-sensitivity/`).

The substantive reason stands on its own and predates the result: 25 of the 28
rest on a single sampled judgment and 3 on two, so "below 0.7" means one rater
disagreed once, which the tooling itself flags as too weak a basis for dropping
an individual criterion. Dropping on that evidence discards real instances to
satisfy a threshold computed from one look.

The objection also stands, and a reader is entitled to weigh it: we are
declining a prespecified rule on the day it bound, after seeing that applying it
would have cost two gate passes. We record both the commitment and the reversal
with dates rather than presenting the decision as though the number had never
been computed.

One gap in the rule needed filling. For 30 instances, dropping removes every
criterion on a scored side, and a side with no criteria passes vacuously. We
mark those unscorable and therefore invalid, which is the strict reading and
accounts for the entire 30-instance difference; a permissive reading would leave
the total near 371. The prespecified rule does not cover the case, so this is our
judgement call and is reported as one.

### 4.5 Floor validation: pair credit filters priors

This is the paper's one clean positive result, and it tests the claim the whole
design rests on: that the instrument measures memory rather than competence.

The memoryless condition ran end to end through the full evaluation pipeline on
seed 1, not as a special case. A worker with no organizational context received
each of the 125 valid instances on both the base and twin sides, and the 250
resulting deliverables were judged blind through the same export and import path
as everything else.

Pair credit came out near zero on every capability rung: **rung 1 pair credit
0.022** (95% CI ±0.040, n=92) for alignment, **rung 2 0.118** (±0.217, n=17) for
coordination, and **rung 3 0.000** (n=16) for compounding. Four instances out of
125 earned credit in total, and every interval includes zero.

The mechanism is the twin. A memoryless worker can guess a base side at a rate
well above zero, because a generated fact often matches the priors of a
competent model, and a benchmark crediting single sides would read that as
memory. Requiring the twin side as well removes it, because the twin's answer is
the one those same priors argue against. The design predicted this and the floor
measures it.

Two honest qualifications. Rung 2 rests on 17 instances and rung 3 on 16, so the
intervals are wide and the rung-level claim is weak even though the direction is
not. And this is one seed, because the deprecation stopped the other two before
they ran. What the result supports is that the instrument does not reward prior
knowledge or generic competence on seed 1, which is the claim it is offered for
and no more.

### 4.6 Benchmark durability: the deprecation event and re-anchoring

The dataset was frozen on 2026-08-15. Pilot runs began 2026-09-02. On 2026-09-04
the runs stalled, and what the logs recorded was not an announcement but a wall
of identical worker failures. By the time it was diagnosed the provider had
removed gpt-5.4 from every billing path available to this project, returning a
hard error. The pinned worker had ceased to exist, roughly seven weeks after
being pinned.

§4.2 makes the consequence unavoidable. Screening anchors are properties of a
worker. If the worker is gone, the anchors cannot be reproduced, the partial
rows already collected cannot be completed, and rows collected under a successor
cannot be mixed with rows collected under the dead one. Attaching new results to
old anchors would break both the normalization and the pair-validity argument at
once. That is why §6 releases the partial rows as provenance and derives no
comparison from them.

The decay literature of §2.4 treats the data as the perishable component and
answers it with regeneration and refresh. For an agentic benchmark the data is
the durable part. The worker used to establish which items are answerable is the
perishable part, and it perishes on the provider's schedule rather than on the
benchmark's. We have not seen this addressed, and we would not have written it
up as a contribution if it had not happened to us.

The release therefore ships a maintenance contract rather than an assurance. If
a successor worker is pinned, the rule is the nearest same-provider successor at
the time of deprecation; anchors are re-screened for the released seeds under the
frozen gate rules with task text held byte-identical, which is what keeps the
comparison a re-anchoring rather than a new dataset; the result is a new valid
set under the new worker, reported as such; and only then can systems be
evaluated. Anchors and system rows from different workers are never mixed. The
procedure is specified whether or not we ever run it, because a dataset whose
validity cannot be re-established outlives nothing.

## 5. The instrument as released

The dataset ships with the harness that runs it, because a benchmark whose
evaluation code is a description rather than an artifact cannot be reproduced.

**The adapter surface is deliberately tiny.** A system under test implements
three things: a counters dictionary, `ingest(principal, event)`, and
`run_task(principal, task) -> str`. Memory internals are never inspected. What
a system stores, how it indexes, when it consolidates: none of it is observed
or scored, only the behavior of the artifact its worker produces.

Witness routing lives in the runner rather than in any adapter, which keeps
per-principal delivery identical across systems. Participants always witness an
event; org-public events reach every active principal, honouring join and leave
dates; team-confidential events reach team members as of that stream position;
private events reach participants only. Any other visibility value raises rather
than defaulting. The runner calls `ingest` once per witness per event, and
visibility metadata lives in the private org index, never in the SUT-facing
stream. A worker failure is recorded as a null deliverable carrying its error,
never as a dropped run, so a system cannot improve its score by failing.

**Eleven system configurations are registered; ten are runnable in v1.** Four
baselines, namely the memoryless floor, full-transcript long context, a
filesystem-and-grep agent and embedding RAG, plus a lexical BM25 ablation of
the RAG baseline, four market systems selected by published inclusion criteria,
and a per-principal silo ablation of Mem0. The eleventh, a typed-memory
reference implementation, is registered and constructible but deferred by the v1
freeze and never run. The grep baseline is there on principle: a memory product
should have to beat a directory of files and a search command.

**Configurations were frozen before any live run and amended only mechanically.**
The per-system config file was committed 2026-08-27, before any system was
contacted, and states that the only permitted post-smoke changes are availability
fixes, meaning auth flags, timeouts and API-shape corrections, recorded as dated
amendments, never retrieval-quality tuning. Four amendments followed on
2026-09-02, all dated in git.

Two of those four deserve to be named rather than folded into a summary, because
a reader could reasonably contest whether they are purely mechanical. Supermemory's
search was pinned to hybrid mode after extracted-memories-only searches returned
empty until the vendor's batched server-side extraction landed minutes after
ingestion; the mode is the one the vendor's own documentation recommends, and the
change was forced by an empty result set rather than chosen to improve ranking,
but it is a search-parameter change and we say so. Graphiti's models were pinned
to `gemini-2.5-flash` and `gemini-embedding-001` after the configured defaults
returned 404 for the available key, which supersedes a line in the frozen config.
The remaining two are unambiguously mechanical: namespacing Supermemory's
container tags per org side so a twin run cannot retrieve base-run documents,
and handling the dataset's null timestamps. The Graphiti work also included four
repairs to the frozen `graphiti-core` 0.29.3 embedded-Kuzu path, all availability
and none capability, at a measured ingestion cost of roughly 48 seconds per
episode, about 2.7 hours per organization side.

**One embedding model sits behind every RAG-class baseline**,
`gemini-embedding-001`, pinned in code with the pin asserted by tests, and a
retriever constructed without one identifies itself as `UNPINNED` in the
artifacts it writes. This follows directly from §2.3: if swapping an embedding
model moves results more than swapping the memory architecture, then an
unreported embedding model makes a comparison meaningless. Market systems reuse
the same model for their internal embeddings where configurable, at each
system's own dimensionality.

**The scoring pipeline derives every number from artifacts.** Runs are resumable
in two tiers: rows already carrying a non-empty output are skipped and empty or
errored rows are retried, while ingestion is never resumed and always replays
the full stream for a given side, system, and sample. Scoring joins the screening
anchors, the frozen valid set, and the SUT rows into one manifest, hard-failing
on a missing base or twin output rather than scoring a partial pair. Pair credit
requires both sides to clear the ceiling-pass threshold. Aggregates carry
cluster-robust standard errors computed with a design effect from an estimated
intra-cluster correlation, because probe instances cluster within fact clusters
and a naive standard error would overstate precision. An empty deliverable scores
zero and stays in the denominator. The figure script adds no statistics at all.
It reads means and standard errors from the scored summary and renders them, and
the generated results file says so in its header.

The claim that no number in the pipeline is hand-typed holds for the numbers, and
two qualifications keep it honest. The radar's axis set and the
archetype-to-rung map are literals in code, prespecified structure rather than
measured values, but literals nonetheless. And the 95% multiplier is written as
1.959964 in the scorer and 1.96 in the renderer, so a rendered interval can
differ from the scored one in the fourth decimal. Neither affects a result in
this paper, and both are the kind of thing that is cheaper to disclose than to
be asked about.

## 6. Partial pilot record (provenance, not results)

The prespecified pilot was roughly 5,900 system runs across three seeds. It
completed one condition. We release what exists, because an interrupted study
that quietly drops its partial rows is indistinguishable from one that dropped
the inconvenient ones.

Everything below is seed 1 only; no seed-2 or seed-3 system rows exist. Counts
are unique probe instances after last-wins deduplication, since the row files
are append logs that a resumed run adds to.

| system | base rows | base non-empty | twin rows | twin non-empty | judged |
|---|---|---|---|---|---|
| nomemory (floor) | 125 | 125 | 125 | 125 | **250 verdicts** |
| fulltranscript | 125 | 125 | 125 | 109 | no |
| grep | 125 | 125 | 125 | 46 | no |
| rag-lexical | 125 | 125 | 125 | 29 | no |
| rag | 125 | **0** | **113** | 34 | not manifested |

Only the memoryless floor is complete and judged, and it is the one result this
paper reports (§4.5). The other three were manifested but never judged; `rag`
never reached a manifest at all, because its twin side is missing twelve rows
outright, because the run was cut off mid-stream, and the scorer refuses to build a
manifest with a missing twin rather than scoring a partial pair. That refusal is
the design working: a half-present pair is exactly the kind of row that becomes
a misleading number later.

The empty deliverables are a single uniform failure, and it is not an adapter
failure. Deduplicated, the errors read `codex worker failed after 2 attempts: no
output.md produced`, with one timeout. The retrieval side was working while this
happened: the RAG baseline's base run embedded 179 times, retrieved 995 passages
and assembled 721,655 characters of context, and the worker then produced nothing
on all 125. This is the deprecation of §4.6 arriving as a wall of null outputs
rather than as an announcement.

One provenance note, because the dates differ and the difference is the kind of
thing that looks like a discrepancy later. Runs stalled 2026-09-04 when the
provider dropped the pinned worker for the billing path in use. The rows were
committed on 2026-09-14, so that commit dates the release of the record rather
than the runs themselves.

**These rows carry no comparative claim.** They are released as provenance for
an interrupted prespecified pilot under a worker that no longer exists. Because
probe validity is worker-relative (§4.2), they cannot be completed by a
successor worker and they cannot be mixed with one; the re-anchoring procedure
in §4.6 says what a successor would have to redo instead. No ranking, no
ordering, and no per-system statement is derived from this table anywhere in
this paper.

## 7. Limitations and disclosures

Everything a reader would need to discount this work is in this
section, including the items that cost us the most. They are listed in rough
order of how much they should change your reading.

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
   bounds. Read the two halves of the diagnosis differently: the degenerate
   pass mode is demonstrated on all 5,398 committed verdicts without human
   labels (96.4% positive on the absence class against 39.0% and 36.9%; 96.2%
   under a memoryless worker where the other two halve), while whether the
   judge is *wrong* on specific items rests on one rater, who cannot be
   separated from judge error. A second rater settles the second half and
   changes nothing about the first.
2. **One rater, and not an independent one.** G4 was rated by a single author,
   who has read seed content, a disclosed downgrade from the two-rater design
   originally specified. There is therefore no inter-rater κ, and judge error
   cannot be separated from rater error. Contamination was managed where it
   could be: the same author was cleared to run the blinded salience check only
   on seeds 4 and 5, because seeds 1–3 had been discussed in working sessions.
   A second independent rater is the first thing a v2 should buy.

3. **All three released seeds fail the instance gate**, at 125, 131, and 115
   against a prespecified 135, and seed 3 also fails the cluster gate
   at 40/54 against 45. Instances were retained and marked rather than topped
   up, and no failing probe was repaired. Four prespecified gates have failed
   in this project against one clean positive result, which is an asymmetry we
   report rather than manage.

4. **The evaluation this dataset was built for did not happen.** The pinned
   worker was withdrawn by its provider mid-pilot (§4.6), so there are no
   comparative system numbers here, and the partial rows in §6 are provenance
   rather than results. Worker billing and authentication changed during the
   study; the model and binary pin held until deprecation ended access
   entirely.

5. **Simulated organizations, not real logs.** Three screened seeds, one
   organization type (a two-team software company at L1–L2 scale), one worker
   model. The external-validity claim stops there. Industry breadth is a
   designed factor for a later version, not something to be obtained by
   relabeling this one.

6. **Event streams carry no timestamps.** `sim_time` is null throughout v1 and
   temporal order is positional, so no result here separates "knows the order"
   from "reads a date". Screening anchors never saw rendered timestamps either,
   so the condition is at least uniform.

7. **The judge and the human rater saw the same rules through different
   instruments.** The judge scored every criterion for one output together, in
   a single batch; the human scored one criterion per spreadsheet row,
   independently, under a no-backtracking rule, across an expected three to
   five hours. The rule text is materially identical in all three places it is
   maintained, which we checked, but joint and independent presentation are not
   the same instrument, and no part of the κ gap has been attributed between
   judge quality and presentation. We name this because we found it while
   preparing this paper and did not measure it.

8. **Judge identity is procedural, not enforced.** The pipeline records the
   judging model as a free-text tag; nothing in code selects a model or
   verifies the tag against whatever actually produced the verdicts. The
   guarantee that the judge was never the worker model or the criterion-author
   family rests on protocol discipline and dated records, not on a mechanism.
   Anyone rebuilding on this harness should close that gap.

9. **Scoring-rule disclosures.** The scorer-exploit audit reads FAIL as
   literally prespecified and PASS when re-scoped to sides carrying at least
   one positive-content criterion; both lines are permanent in the report,
   and the re-scoping is post-hoc and labelled as such. The rank-direction
   robustness rule (≥2/3 seeds, itself a disclosed downgrade from ≥4/5) was
   prespecified for a pilot that did not run and is unused here. **Twenty-eight
   criteria fall below the 0.7 raw-agreement threshold, and the prespecified
   rule to drop them was measured and then declined.** Applying it gives 341
   valid instances against the frozen 371 and fails all six gates instead of
   three. We committed to applying it before running it, kept 371 after seeing
   the result, and publish both numbers with their dates (§4.4). A reader who
   thinks that was the wrong call has what they need to prefer the other one.

10. **Released-harness configurations.** Market systems run their internal LLM
    on Gemini where configurable, with vendor defaults listed alongside every
    deviation (`docs/vendor-configs.md`). Shared-store configurations do not
    enforce per-principal visibility, and v1 scores no leakage, so the silo
    ablation captures the benefit of sharing without its governance cost. The
    two are adversarial by design and belong together once both exist. The
    ablation itself was moved to Mem0 before any run, because for a raw
    transcript the siloed and shared configurations produce identical context.
    Graphiti runs against embedded Kuzu, deprecated upstream, with adapter-side
    repairs documented. Supermemory's extraction is batched server-side. These
    describe the released harness and support no claim in this paper.

11. **Vendor right-of-reply was not triggered**, because it attaches to
    published vendor numbers and this paper publishes none. The procedure stays
    specified for any re-anchored evaluation.

## 8. Release

The release is built and checked by `scripts/release.py build|verify`, so the
bundle is reproducible rather than hand-assembled and the withholding policy is
enforced by code rather than by care. A policy that depends on nobody making a
mistake is not a policy.

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
