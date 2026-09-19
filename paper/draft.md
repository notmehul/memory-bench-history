# memory-bench: A Screened Benchmark Dataset and Validity Study for Organizational Memory in Agent Harnesses

Mehul Srivastava, independent researcher. ORCID: 0009-0008-1031-304X

DOI: [10.5281/zenodo.22838321](https://doi.org/10.5281/zenodo.22838321). Companion methodology paper: [10.5281/zenodo.22838603](https://doi.org/10.5281/zenodo.22838603).

## Abstract

An organization's agents no longer run on one model: each person picks the
harness built for their work. The weights organizational knowledge must reach
are therefore plural and vendor-owned, so coherence cannot live in them. The
memory layer is the only place every harness can reach. Of the ten published
memory benchmarks we verified (§2), none measures whether a memory system holds
that knowledge with the right scope, authority, and freshness.

We release memory-bench as an instrument for that question, and this paper is
the evidence that the instrument measures what it claims. The dataset is three
simulated software organizations: multi-week event streams delivered
event-by-event to each principal who witnessed them; a hidden ledger from which
the expected belief state `B(p, t)` is computed rather than asserted; and
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
rung. Probe validity is *task-model-relative*: under identical strict rules,
37/54 probe clusters survived the ceiling gate for one worker and 17/54 for a
smaller sibling. Identical weights behind two agent harnesses agreed on only 65% of
twin-ceiling outcomes, failing a prespecified 90% bar. Judge-human agreement on
a blinded 150-pair packet reached 81.3% raw agreement at κ = 0.537, which fails
our prespecified gate of κ ≥ 0.75. Aggregate disagreement is symmetric, 14 items
each way, but the symmetry is a cancellation: every judge error on
absence-phrased criteria is an over-accept, and every error on scope criteria is
an under-accept. Mid-study the provider deprecated the pinned worker. We report
the event, release the partial rows as provenance, and specify the re-anchoring
procedure that lets the dataset outlive any single worker. No comparative system
result is claimed anywhere in this paper.

**Keywords:** agent memory; benchmark construction; construct validity;
LLM-as-judge; counterfactual evaluation; organizational knowledge;
reproducibility.

> **How to read this paper.** This is an instrument and a validity study, not a
> leaderboard. Three claims: the released set measures organizational memory
> behavior at rungs 1–3 under a stated worker pin; pair credit via
> counterfactual twins filters priors; screening anchors are properties of a
> worker and a harness, not of the items alone. Four prespecified bars failed:
> the instance gate on all three released seeds, the cluster gate on seed 3,
> harness equivalence, and judge-human κ. Against them, one clean positive
> result: a memoryless worker earns pair credit on 4 of 125 instances (§4.5).

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

### 1.3 What we claim, and what we do not

This paper claims an *instrument*, not a leaderboard.

We claim that the released dataset measures organizational memory behavior at
rungs 1–3 of the ladder, for a two-team simulated software organization at L1–
L2 scale, under a stated worker pin, and we report the measurements that
support that claim alongside the ones that qualify it. This paper publishes no
comparative system numbers. The instrument and the validity study are the same
object: a benchmark that cannot say what it measures is not a benchmark, so
the measurements that qualify the claim are the claim. We do not claim to
measure "mini-AGI-ness." No result is ever reduced to a single aggregate score. Results are grouped by
capability rung, always.

Three constraints were fixed before the evidence they govern was produced, and
each is corroborated by dated git history rather than by assertion: the gate
criteria and scoring rules (`docs/dataset-plan.md`), the worker and judge
pins, and the commitment to carry failed gates as failures rather than
repairing the probes that failed them. That commitment has a visible price.
Four prespecified bars failed, and the items behind them are retained and
marked rather than topped up (§4.1), because a gate that is relaxed once it
binds was never a gate.

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
   result existed. The measurement problems this pipeline raises in its own
   right are the subject of a companion methodology paper (Srivastava,
   *Constructing a Benchmark When Every Component Is a Language Model*, 2026,
   DOI 10.5281/zenodo.22838603, `paper/pipeline.tex`).

3. **A validity study** (§4): the measurements that test whether the instrument
   works: floor validation, the task-model-relativity of probe validity,
   harness sensitivity, judge false-accept rate, and judge–human agreement.

4. **A durability procedure** (§4.6): what it takes to keep an agentic
   benchmark valid when the worker it was screened under disappears. We did not
   choose this contribution; the provider deprecated our pinned worker
   mid-study and we documented what that costs and how to recover from it.

### 1.5 What this paper does not contain

It contains no system comparison. The pilot that would have produced one had
completed the memoryless floor and partial rows for four further baselines
when the pinned worker became unreachable (§4.6), and because probe validity
is worker-relative (§4.2) a successor's results cannot be attached to anchors
measured under the old one. The partial rows are released in §6 as provenance,
carrying no comparative claim. It also contains no treatment of how a benchmark
is validated when every component inside it is a language model; that is the
companion paper's subject (Srivastava, *Constructing a Benchmark When Every
Component Is a Language Model*, 2026), and the one result from it this paper
leans on is cited in §4.4.

## 2. Related work

> **Citation verification, 2026-09-14 and 2026-09-17.** These references were
> checked in two passes, because the section was first drafted from this
> project's own field audit (`docs/standards-audit.md`, compiled 2026-07-25)
> rather than from the papers. On 2026-09-14 ids and titles were resolved
> against their primary sources. All twenty arXiv ids resolve to a paper
> matching the name given, including the six that postdate the drafting model's
> knowledge, and a deliberate nonexistent id was checked to confirm that
> failures report as failures. Three descriptions were wrong and are corrected
> here: MEMTRACK is an organizational benchmark rather than a conversational
> one, LongMemEval V2 is a web-agent benchmark rather than a revision of the
> original, and the full-context-versus-Mem0 comparison comes from Mem0's own
> paper rather than from a third party. One claim was refuted by its own source
> and has been rewritten rather than re-cited: see the note on post-hoc tuning
> in §2.3. Author lists were not in that pass's scope. They were checked on
> 2026-09-17, which found seven entries carrying wrong given names and three
> titles that abbreviated what the source spells out; all ten are corrected in
> the submission bibliography (`paper/memory-bench.tex`). That pass also read this
> section's substantive claims about its sources against the sources themselves.
> MEMTRACK's best model at 60% correctness and the three LoCoMo scores quoted from
> Mem0's own Table 2 are as stated. One characterisation of BetterBench was not: it
> reports that most benchmarks give no statistical significance or uncertainty,
> which is weaker than calling that the criterion failed most often, and §2.4 now
> says the former.

### 2.1 What memory benchmarks currently measure

| benchmark | principals | what the system ingests | what is scored |
|---|---|---|---|
| LoCoMo (2402.17753) | one | conversation sessions | recall of a fact stated earlier |
| LongMemEval (2410.10813) | one | conversation sessions | recall, sometimes with a temporal qualifier |
| MemBench (2506.21605) | one | conversation sessions | recall, extending the same format |
| MemoryAgentBench (2507.05257) | one | memory written incrementally | agentic memory, measured on-policy |
| MemoryArena (2602.16313) | one | closed-loop agentic tasks | task outcome |
| StreamMemBench (2606.14571) | one | streaming egocentric lifelog | ingestion and feedback consolidation |
| HorizonBench (2604.17283) | one | preferences observed over time | preferences that change |
| LongMemEval V2 (2605.12493) | one | web-agent trajectories to 115M tokens | static and dynamic state, workflow knowledge, environment gotchas, premise awareness |
| MEMTRACK (2510.01353) | one | asynchronous Slack, Linear and Git events | acquisition, selection, conflict resolution |
| GateMem (2606.18829) | many | a shared memory store | utility, access control, deletion |
| **memory-bench** (this work) | many | a per-principal event stream, delivered event by event | scope, authority and freshness as behavior, credited per twin pair |

*The ten memory benchmarks the 2026-07-25 audit covered, on the two axes that
decide whether organizational memory is in range: how many principals hold
different views of the same history, and whether that history arrives as a
stream the system has to write down for itself. The first three are the rung-0
recall benchmarks. MEMTRACK is the nearest neighbour on setting and GateMem on
governance, and §2.5 says which part of the claim each one leaves standing.*

The table above places the ten benchmarks our audit covered. The established
ones evaluate a single agent's recall across a long conversation. That is rung 0
of the ladder this benchmark is organized around (§3.3): recall on request,
table stakes for a memory system, and saturated by long context. A second line
moves toward agentic settings, and MemoryAgentBench (2507.05257) makes the
argument that matters there, that pasting a conversation history into context
evaluates memory off-policy, since a deployed system writes its memory
incrementally rather than receiving the whole history at once. Every one of them
is single-principal.

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
inside the weights. This benchmark takes the harness position instead. The
knowledge an organization runs on changes faster than anyone retrains, and the
agents consuming it run on models the organization does not own (§1.1).

### 2.3 How memory evaluations have failed in practice

Most of this paper is validity evidence rather than results, and the reason is
that this field's published numbers have repeatedly failed on measurement
rather than on modeling.

**Ground truth that is wrong, and a judge that does not notice.** An
independent audit of LoCoMo (Penfield Labs, 2026-04-08) found 99
score-corrupting errors in 1,540 questions, a ceiling near 93.6% that vendors
were publishing above, and an LLM judge accepting topical but wrong answers at
62.81%. It is self-published, and its author discloses the same finding in a
public issue thread, so the figure has two routes rather than one.

**A corpus that does not need memory.** Mem0's own evaluation (2504.19413,
Table 2) reports a full-context baseline at 72.90% against Mem0's graph variant
at 68.44% and plain Mem0 at 66.88%, and Letta separately reported a plain
filesystem-and-grep agent at 74.0%. When the no-memory baseline wins on a
vendor's own table, the question is whether the corpus was measuring memory at
all. A grep agent is one of our registered baselines for that reason: a memory
product should have to beat a directory of files.

**Protocol loose enough to support a dispute.** One system was reported at 84%,
then 75.14%, then 58.44% in a public exchange between Mem0 and Zep, depending
on configuration and denominator, with neither party obviously acting in bad
faith. MemDelta (2606.29914) sharpens the point: an embedding-only swap moved
accuracy 6.2 points (p = 0.004) while the architectural comparison it ran,
verbatim RAG against full context, did not move (47.2 against 49.8, p = 0.34).
Our RAG-class baselines pin and report their embedding model
(`docs/vendor-configs.md`).

**Fitting the system to the test after seeing it.** A public teardown of
MemPalace documents three patches hand-coded against three specific questions
the system had failed, after which the result was reported as the first
perfect score on LongMemEval; the reporter's reading is that the fixes were
designed around the exact failure cases rather than found by analyzing general
ones. The documented failure is test-set inspection followed by targeted
repair, not benchmark content visible during ingestion, so what it argues for
is a withheld ledger, regenerable holdout seeds, and a freeze that makes
post-hoc repair visible in git history.

### 2.4 Benchmark validity and benchmark decay

The standards this paper is written against are BetterBench (2411.12990), whose
lifecycle assessment finds that most benchmarks report neither statistical
significance nor uncertainty, 14 of the 24 it assessed; the Agentic Benchmark Checklist (2507.02825), which requires
auditing a scorer against degenerate strategies; the construct-validity audit
of 445 benchmarks (2511.04703); Miller (2411.00640) and 2503.01747 on error
bars and small-sample intervals; 2306.05685 on measuring judge agreement rather
than assuming it; and BenchBench (2407.13696) on agreement testing between
benchmarks.

The decay literature treats the *data* as the perishable part. GSM1k
(2405.00332) regenerated a held-out equivalent of a saturated benchmark and
found accuracy drops up to 8% in some model families, and LiveBench
(2406.19314) answers rot with continuous refresh; both inform the withheld
generator and unscreened seeds of §8. What none of it covers is the failure
§4.6 reports. For an agentic benchmark the worker model used to establish which
items are answerable is equally perishable, and it perishes on the provider's
schedule rather than on the benchmark's. We measured how much validity depends
on that choice (§4.2) and then lived through the dependency.

### 2.5 Where this benchmark sits

No benchmark in the audit scores tiered scope, authority weighting, propagation
across principals, and supersession together as behavioral properties of an
organization. The claim is a conjunction, and
§2.1 says which neighbour breaks which part of it.

We state this as the result of a search rather than as a fact about the
literature. The audit was compiled 2026-07-25 and names what it covered
(`docs/standards-audit.md`), the citations were verified against primary
sources on 2026-09-14, and a reader who knows of prior work we missed should
read the claim as bounded by that date and that list.

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
that blocks release rather than a judgement call resolved per item, and the
two found this way were fixed before any screening.

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
event content is operational filler embedding no probed fact; every probed
fact carries at least two distractors, one of them a near-miss differing by a
single attribute; no fact's canonical text appears verbatim in more than one
event, which blocks string-match shortcuts; canary strings sit in the text at
low frequency for contamination detection; and timelines are sized so the
annotation-stripped transcript exceeds roughly 500k tokens, which keeps
full-transcript-in-context an honest but costly baseline rather than a free
win.

Salience parity is achieved by construction and then tested. Distractor type,
register, shape, length, and numeric form mirror the probed mix, and positions
are assigned mechanically to class-stratified band centers rather than by
re-rendering until a lint passes. A blinded discrimination check bounds it rather than
confirming it: raters told probed excerpts from distractor-only ones at 58/100,
58% with a Wilson 95% CI of [48.2%, 67.2%] (binomial p = 0.067; protocol,
per-seed splits and the human runs in `docs/validation-report.md`). G2 set the
bar at a reviewer who cannot beat 65% accuracy (`docs/dataset-plan.md`, Gate
G2), and the interval's upper bound reaches above that, so the check bounds
discrimination rather than demonstrating flatness: the data do not exclude a
discrimination rate at the level the gate itself calls failure. The comparison
is approximate, because G2's 65% is worded per 20-excerpt spot-check while
58/100 aggregates five of them. G2 was read off the point estimate, passed on
that basis, and is not re-litigated here. The check does detect discrimination
when it is large, which is how the one documented residual was found: seed 3
scored 14/20 on four independent samples, including after two targeted content
revisions that failed to remove it (42/60 across the first three, 70% with a
Wilson 95% CI of [57.5%, 80.1%], p ≈ 0.001), and it ships disclosed, with users
of salience-sensitive analyses pointed at the other seeds.

### 3.3 Probes are work, and every probe has a twin

A probe is not a question. It is a work task issued to a principal's agent at a
point in the timeline: write the announcement, draft the checklist, prepare the
review note. What is scored is whether the resulting artifact behaves as the
organization's knowledge requires. Probes are injected only at evaluation
time and never appear in the ingested stream, which is the countermeasure to
tuning a system on the questions.

Four archetypes instantiate the capability ladder (table below,
`docs/vision.md` §3). Rung 0, plain retention, is where existing memory
benchmarks live and where long context saturates; it is implicit in every probe
and never headlined. v1 is a deliberate vertical slice, at least one archetype
on every rung above retention, rather than exhaustive coverage of any one rung.

| rung | archetype | what the agent has to get right | valid instances |
|---|---|---|---|
| 1, alignment | A4, tier collision | personal, team and org facts conflict, and context decides the winner | 106 |
| 1, alignment | A7, supersession chain | a fact updated two or three times, probed at each epoch and once historically | 172 |
| 2, coordination | A1, decision ripple | a decision taken in a meeting the probed principal did not attend | 50 |
| 3, compounding | A2, silent rule | a working rule stated once, probed 30 or more events later with no reminder | 43 |

*The capability ladder as v1 instantiates it, and where the 371 valid paired
instances sit on it. Rung 0, plain retention, has no row because it is
implicit in every probe and never headlined. The archetype descriptions
restate the generator's templates rather than adding anything to them.*

Every probed fact has a counterfactual variant, and the generator produces a
**twin organization** from the same seed and the same timeline skeleton with the
delta facts re-rendered. The same probe runs against both. An instance is
credited **only when both sides pass**: correct behavior on the base
organization, and correctly *different* behavior on the twin. Passing one side
scores zero for the pair.

This is the most load-bearing design choice in the dataset. A fact invented by
a language model often coincides with that model's own prior, whether a naming convention, a
review threshold or a default cadence, and a memoryless system can guess the
base side at a rate that would flatter it badly. It cannot guess both sides,
because the twin's answer is the one its priors argue against, and §4.5
reports what that buys.

Assertions come in several kinds, among them `fact_applied`, `fact_absent`,
`scope_correct` and `conflict_flagged`. Each is checked by regex, by
structural parse, or by a blinded semantic judge. Which checker is allowed
where was settled by measurement rather than preference. Applied-content
assertions written as regexes failed 39–42% of ceiling runs, because a
deliverable paraphrases around any anchor; absence detectors failed 4% and
semantic criteria 9–17%. Spec v0.3 therefore requires the semantic checker for
applied content and reserves regex for absence detectors
(`docs/specs/probe-spec.md` §3). Assertion text was model-authored under a fixed
prompt and accepted only after mechanical validation, whose rules live with
the spec (`docs/specs/probe-spec.md` §3) rather than here. One authoring rule
came out of failure adjudication and changed scoring, so it belongs in the
paper: an assertion must never punish content drawn from a different co-valid
fact of the same cluster, because complementary facts are not competing
answers.

### 3.4 Screening: which items actually measure memory

Every probe instance runs in three conditions. `floor` gives the task alone with
no organizational context. `ceiling` gives the task plus exactly the relevant
facts from `B(principal, t)`, rendered canonically. `sut` gives whatever the
system under test provides. A system's score is normalized as
`(sut − floor) / (ceiling − floor)`.

The floor and ceiling conditions are the
screen. An instance is valid when its ceiling passes, its twin ceiling passes,
and its floor output fails at pair level. A ceiling that fails means the item
measures reasoning rather than memory. The facts were supplied and the worker
still could not produce the artifact. A floor that passes means the item is
answerable without memory at all. Both get dropped, and the per-side floor pass
rate survives as a reported `guessability` figure per cluster.

Two revisions to this rule were forced by measurement and dated before the
evidence they govern. The floor gate moved to pair level, because canonical
facts sometimes coincide with industry defaults and a per-side rule discarded
valid pairs for the exact reason the twin design exists. And screening moved
from clusters to instances: requiring all three instances of a cluster to be
valid demands per-run reliability near 98%, since 0.9⁶ ≈ 0.53 cluster survival
follows even at 9% instance noise. A cluster now survives with at least 2 of 3
valid instances and ships only those, and both counts are reported throughout.

Semantic verdicts are produced blind. `judge-export` writes each output with
its criteria under opaque ids, stripped of probe identity, condition, and
base-versus-twin side; fresh judge agents read only that batch file;
`judge-import` validates the ids and criterion keys before anything is
recorded. The judge model is never the worker model and never the family that
authored or repaired the criteria being judged, and the rubric is versioned
verbatim in the repository (`docs/specs/judge-rubric.md`). Blinding is
enforced in code rather than by instruction. It is worth reporting that
blinding changed little: an earlier unblinded pass over the same seed-1
material agreed with the blinded verdicts on 97.6% of criteria, 26 flips out
of 1,092, split 14 True→False against 12 False→True with no systematic
direction. Blinding is cheap insurance here rather than a large correction,
and we would rather publish that null than imply we caught a bias we did not
measure.

### 3.5 What the released dataset is

Seeds 1–3, probe-spec v0.4.3, judge rubric v2: **371 valid paired instances**
(A1 50, A2 43, A4 106, A7 172). Per seed the valid-instance counts are
125/131/115, from cluster survival of 46/54, 46/54, 40/54; the stricter
all-instances counts are 33, 39 and 35. Construction produced 54 clusters × 3
instances × 5 organizations, 810 instances in total, of which seeds 4 and 5
are withheld unscreened as holdouts.

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
is worth reading. **All three instance gates fail** against a prespecified 135,
and **seed 3's cluster gate also fails** at 40 surviving clusters against a
floor of 45.

| seed | clusters surviving | valid instances | instance gate (≥135) | cluster gate (≥45) |
|---|---|---|---|---|
| 1 | 46/54 | 125 | **FAIL** | pass |
| 2 | 46/54 | 131 | **FAIL** | pass |
| 3 | 40/54 | 115 | **FAIL** | **FAIL** |

The shortfall is structured rather than random. It is the residual tail of
counterfactual-anchoring failure on the twin side, the same defect family that
drives cluster drops, and the prespecified v2 response is to over-generate four
instances per cluster and require counterfactuals to invert the aspect the task
actually elicits.

Two further prespecified bars failed: the harness-equivalence study of §4.3, and
G4 in §4.4. Four failures against one clean positive result, the memoryless
floor of §4.5.

No probe that failed a gate was repaired to recover it, no criterion was
rewritten after seeing that it cost an instance, and no threshold moved once it
bound. Where repairs did happen they were made blind to direction and before the
evidence they touched: the cross-organization lineage sweep ran without
knowing whether it would move counts up or down, and it moved them both ways.

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

The disagreement is not uniform. It concentrates in the conditions that are
hardest to satisfy. Where the task is easy to fail (the memoryless floor, at
100%) or easy to pass (the ceiling with facts injected, at 95%) the harnesses
agree. The twin ceiling asks a worker to produce a deliverable consistent with
a counterfactual fact while an almost identical base fact is absent, and there
the same weights behind different scaffolds disagree on more than a third of
outcomes.

One consequence generalizes past this study. The harness is part of the
consumer, not a neutral pipe to the weights. A benchmark that pins a model
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
downgrade, §7 item 2) and scored against the committed judge verdicts
(`datasets/dev/calibration/judge-agreement.json`, raw submission
`rater-M-filled-2026-09-14.xlsx`).

| | n | raw agreement | κ | bootstrap 95% CI |
|---|---|---|---|---|
| **overall** | 150 | 0.813 | **0.537 (gate κ ≥ 0.75: FAIL)** | [0.370, 0.688] |
| `fact_applied` | 72 | 0.819 | 0.605 | [0.388, 0.782] |
| `scope_correct` | 34 | 0.794 | 0.561 | [0.298, 0.837] |
| `fact_absent` | 44 | 0.818 | **0.166** | [0.000, 0.493] |

The intervals are a percentile bootstrap over the 89 fact clusters the packet
draws on rather than over the 150 items, because the packet is stratified with a
per-cluster cap: 10,000 replicates, fixed seed, zero degenerate replicates
(`kappa_bootstrap` in `datasets/dev/calibration/judge-agreement.json`). They
were computed on 2026-09-17, after the gate was measured, so they are post-hoc
and were never prespecified. G4 was prespecified and decided on the point
estimate. The upper bound of the overall interval is 0.688, below the gate, so
the failure does not depend on the point estimate. BetterBench (2411.12990)
finds that most benchmarks report no uncertainty on their results at all, and putting an
interval on our own headline statistic is the standard we cited it for. The
per-kind intervals overlap heavily and establish nothing about whether κ differs
by criterion kind. The kind-wise claim below rests on the one-sided error
direction and on the corpus-scale positive rates, not on these intervals.

The headline number alone misleads in both directions.

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

**κ = 0.166 on `fact_absent` is a base-rate artifact, not evidence that
absence criteria are harder to agree on.** Raw agreement on that kind is
0.818, indistinguishable from `fact_applied` at 0.819 and `scope_correct` at
0.794; κ collapses only because the judge's 97.7% positive rate pushes chance
agreement to 0.782. We say so explicitly because the opposite reading is the
natural one and we made it ourselves in an earlier draft.

The gate was κ ≥ 0.75. It failed at 0.537, and that stands. One diagnostic is
worth a sentence, because the opposite reading is the tempting one: the collapse
on `fact_absent` is the kappa paradox, where a dominant label pushes chance
agreement up and κ then penalizes the residual disagreement out of proportion to
its size. Prevalence-adjusted statistics, computed post-hoc and never
prespecified, put the same data between 0.59 and 0.77
(`datasets/dev/calibration/judge-agreement.json`). We do not offer that as a
defence. We prespecified κ rather than raw agreement precisely so an unbalanced
task could not be dressed up as validity, and we do not get to discover the
objection to our own gate on the day it fails.

#### Where the leniency lands

**The over-accepts concentrate on the counterfactual side.** Of the judge's 14
over-accepts, 11 fall on twin-side criteria against 3 on base-side; its
under-accepts split evenly, 7 and 7. This follows from the design rather than
from chance. A twin asserts that the base fact is *not* presented, so
absence-phrased criteria live disproportionately on that side (26 of the 44
sampled absence items). Pair credit requires both sides to pass, so a judge
that waves twin sides through inflates instance credit directly. The error is
in the direction that flatters a system under test.

**The exposed fraction of the dataset is not small.** 218 of the 371 valid
instances (58.8%) carry at least one `fact_absent` criterion: 199 on the base
side, 207 on the twin side, 188 on both.

The mechanism is not mysterious. "The note
does not present the 48h SLA as current" is satisfied by a note that never
mentions the SLA at all, so silence passes. The class has a degenerate pass
mode, the judge sits at 97.7% positive because of it, and κ has almost no
variance to track. The human rater's stricter 79.5% reflects counting
paraphrase and implication as presenting, which is what the rubric intends and
what the judge did not do. This is therefore as much a criterion-design defect
as a judge defect. An absence criterion carries little discriminative
signal unless a positive criterion demanding the replacement value sits beside
it.

#### The mechanism at corpus scale, without human labels

The mechanism, a criterion class with a degenerate pass mode, can be measured
without human labels at all, on every verdict the project has committed.

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

This is a re-analysis of already-committed verdicts, prespecified and dated
before it was computed (`docs/decision-log.md` §2026-09-14): no output was
re-run, no criterion re-judged, and no valid set moved. It is a statement
about the mechanism, never about accuracy.

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
twin-side leniency were letting ignorance through, the floor would sit well
above 4 of 125 and the rung-1 upper bound would not stop at 10.6%. **The judge defect therefore does not explain away
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
defect removed is assumption-free, because it only requires flipping verdicts we
already have. **Repairing the defect we found, perfectly, still fails the
gate**: removing all 8 absence false-accepts takes agreement to 0.867 and κ to
0.688. The residual is symmetric noise on `fact_applied` plus 7 false-rejects
and zero false-accepts on `scope_correct`, where the judge is already too
strict, and rubric strictness is one dial, so turning it up to fix absence
criteria makes scope criteria worse. Fixing both biases in opposite directions
lands at 0.787, a hair over the line and assuming a precision no rubric edit
delivers. The G4 failure is therefore not attributable to the absence defect
alone, and we say that rather than letting the defect carry the blame for it.

There is a principle under the arithmetic. Even if the numbers worked, the
criteria were frozen before this evidence existed, and rewriting them now is
the practice §2.3 condemns. The freeze that forbids this repair is what makes
every other number here checkable against dated git history, and it cannot be
spent selectively on the gates that fail. The subtler trap is that iterating
rubric versions until κ clears 0.75 stops measuring judge quality and starts
measuring how many attempts were taken, and an unbiased re-measurement needs a
held-out calibration set we do not have.

**What it would cost.** All 5,398 criterion verdicts committed under rubric v2
would need re-judging, since a v3 verdict cannot be mixed with a v2 one. That is
mechanically possible without the deprecated worker, because worker outputs are
cached and re-judging is judge-side, but the 371-instance valid set is *defined*
by rubric-v2 verdicts, so a stricter judge moves the dataset itself. That is a
v2 project with a new rubric and a fresh held-out calibration packet, not a
patch.

The prespecified v2 fix: pair every absence criterion with a positive criterion
demanding the replacement value, so the class stops having a degenerate pass
mode.

One honest limit on the diagnosis. That the class has a **degenerate pass mode**
is demonstrated without human labels, on 1,463 verdicts, with the floor run as a
control. That the judge's permissiveness is **wrong on particular items** still
rests on one rater, and with one rater judge error and rater error cannot be
separated. A second independent rater would settle the second half and would not
change the first.

A judge panel is not that rater. The companion methodology paper (Srivastava,
*Constructing a Benchmark When Every Component Is a Language Model*, 2026) had
four further blinded judges re-judge this packet's semantic criteria
(`datasets/methods/judge-panel/report.json`). They agree with each other far
above the gate, κ 0.927 to 0.966 against the committed v1 judge across 478
criteria, and with the human rater far below it, κ 0.518 to 0.563 on the 150
sampled pairs. On the 44 sampled absence criteria all four returned identical
verdict vectors. Majority, unanimous-AND and unanimous-OR aggregation land at κ
0.537, 0.524 and 0.544, at or below the best single judge at 0.563. Those are
that paper's numbers, and the consequence for this one is that more judges do
not substitute for the second human rater of disclosure 2, because the judges'
failure on that criterion class is perfectly correlated.

**The methodological point, which generalizes past this benchmark.** Two
judge-validity checks, run on the same judge under the same rubric, returned
opposite verdicts. The cheap automated one passed and could not have failed,
because decoys are built by stating wrong values and therefore exercise only
criteria that demand content. The expensive human one failed and localized a
specific degenerate class. Anyone building a benchmark judged by a language model should
report judge agreement **per criterion type**: an aggregate false-accept rate,
and even an aggregate over/under-accept balance, can conceal opposite
directional failures that cancel.

### 4.5 Floor validation: pair credit filters priors

This is the paper's one clean positive result, and it tests the claim the whole
design rests on: that the instrument measures memory rather than competence.

The memoryless condition ran end to end through the full evaluation pipeline on
seed 1, not as a special case. A worker with no organizational context received
each of the 125 valid instances on both the base and twin sides, and the 250
resulting deliverables were judged blind through the same export and import path
as everything else.

Pair credit is small on every capability rung, and the counts are what carry it:
**rung 1 pair credit 0.022**, 2 successes of 92, 95% Wilson interval
[0.004, 0.106], n=92, for alignment; **rung 2 0.118**, 2 of 17, [0.022, 0.441],
n=17, for coordination; and **rung 3 0.000**, 0 of 16, [0.000, 0.194], n=16, for
compounding. Four instances out of 125 earned credit in total. Only rung 3, with
no successes at all, is consistent with exactly zero, and rung 2's interval
reaches 44.1% on 17 instances, which constrains almost nothing.

The interval method changed on 2026-09-17. Earlier drafts reported the Wald
normal approximation, which is invalid at these counts and degenerates to
[0, 0] at rung 3's zero successes, the failure 2503.01747 warns against and the
reason this paper cites it. These are Wilson score intervals on the
cluster-adjusted effective sample size n_eff = n / deff, with deff 1.80, 1.88 and
1.00 by rung (`ci95_wilson` in
`datasets/dev/pilot/nomemory/seed-1/score-k1/report.json`). This is a reporting
correction and nothing more. No valid set moved.

The mechanism is the twin (§3.3). A memoryless worker can guess a base side at a rate
well above zero, because a generated fact often matches the priors of a
competent model, and a benchmark crediting single sides would read that as
memory. Requiring the twin side as well removes it, because the twin's answer is
the one those same priors argue against. The design predicted this and the floor
measures it.

Two honest qualifications. Rung 2 rests on 17 instances and rung 3 on 16, so the
intervals are wide and the rung-level claim is weak even though the direction is
not. And this is one seed, because the deprecation stopped the other two before
they ran. What the result supports is a magnitude rather than a null test: a
memoryless worker earns pair credit on 4 of 125 instances, with 95% upper bounds
of 10.6%, 44.1% and 19.4% by rung. That is what the claim that the instrument
does not reward prior knowledge or generic competence on seed 1 rests on, and no
more.

### 4.6 Benchmark durability: the deprecation event and re-anchoring

The dataset was frozen on 2026-08-15. Pilot runs began 2026-09-02. On 2026-09-04
the runs stalled, and what the logs recorded was not an announcement but a wall
of identical worker failures. By the time it was diagnosed the provider had
removed gpt-5.4 from every billing path available to this project, returning a
hard error. The pinned worker had ceased to exist, roughly seven weeks after
being pinned.

§4.2 makes the consequence unavoidable. Screening anchors are properties of a
worker, so if the worker is gone the anchors cannot be reproduced, the partial
rows cannot be completed, and rows collected under a successor cannot be mixed
with rows collected under the dead one. The decay literature of §2.4 answers a
perishable dataset with regeneration and refresh; for an agentic benchmark the
data is the durable part and the worker is the perishable one. We would not
have written that up as a contribution if it had not happened to us.

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

**The adapter surface is three methods.** A system under test implements
three things: a counters dictionary, `ingest(principal, event)`, and
`run_task(principal, task) -> str`. Memory internals are never inspected. What
a system stores, how it indexes, when it consolidates: none of it is observed
or scored, only the behavior of the artifact its worker produces.

Witness routing lives in the runner rather than in any adapter, so
per-principal delivery is identical across systems and an unrecognized
visibility value raises rather than defaulting (§3.2). A worker failure is
recorded as a null deliverable carrying its error, never as a dropped run, so
a system cannot improve its score by failing.

**Eleven system configurations are registered; ten are runnable in v1.**
Four baselines (the memoryless floor, full-transcript long context, a
filesystem-and-grep agent, embedding RAG), a lexical BM25 ablation of the RAG
baseline, four market systems selected by published inclusion criteria, and a
per-principal silo ablation of one of them. The eleventh, a typed-memory reference
implementation, is registered but deferred by the v1 freeze and never run. The
grep baseline is there on principle (§2.3).

**Configurations were frozen before any live run and amended only mechanically.**
The per-system config file was committed 2026-08-27, before any system was
contacted, and states that the only permitted post-smoke changes are availability
fixes, meaning auth flags, timeouts and API-shape corrections, recorded as dated
amendments, never retrieval-quality tuning. Four amendments followed on
2026-09-02, all dated in git.

Two of the four are worth naming, because a reader could contest whether they
are purely mechanical: one vendor's search was pinned to the hybrid mode its
own documentation recommends after extracted-memories-only searches returned
empty, and another's models were pinned after the configured defaults
returned a 404. Both were forced by a failing result rather than chosen to
improve ranking,
and both are still configuration changes, so we say so. The other two namespace
container tags per organization side and handle null timestamps.

**One embedding model sits behind every RAG-class baseline**,
`gemini-embedding-001`, pinned in code with the pin asserted by tests, and a
retriever constructed without one identifies itself as `UNPINNED` in the
artifacts it writes, for the reason §2.3 measures. Market systems reuse
the same model for their internal embeddings where configurable, at each
system's own dimensionality.

**The scoring pipeline derives every number from artifacts.** Scoring joins
the screening anchors, the frozen valid set, and the SUT rows into one
manifest, hard-failing on a missing base or twin output rather than scoring a
partial pair. Pair credit
requires both sides to clear the ceiling-pass threshold. Aggregates carry
cluster-robust standard errors computed with a design effect from an estimated
intra-cluster correlation, because probe instances cluster within fact clusters
and a naive standard error would overstate precision. An empty deliverable scores
zero and stays in the denominator. The figure script adds no statistics at all.
It reads means and standard errors from the scored summary and renders them, and
the generated results file says so in its header.

No number in the pipeline is hand-typed, with two qualifications that keep
that honest: the radar's axis set and the archetype-to-rung map are literals in
code, prespecified structure rather than measured values; and the 95%
multiplier is 1.959964 in the scorer and 1.96 in the renderer, so a rendered
interval can differ from the scored one in the fourth decimal.

## 6. Partial pilot record (provenance, not results)

The prespecified pilot was roughly 5,900 system runs across three seeds. It
completed one condition. We release what exists, because an interrupted study
that quietly drops its partial rows is indistinguishable from one that dropped
the inconvenient ones.

Everything below is seed 1 only; no seed-2 or seed-3 system rows exist.

| system | base rows | base non-empty | twin rows | twin non-empty | judged |
|---|---|---|---|---|---|
| nomemory (floor) | 125 | 125 | 125 | 125 | **250 verdicts** |
| fulltranscript | 125 | 125 | 125 | 109 | no |
| grep | 125 | 125 | 125 | 46 | no |
| rag-lexical | 125 | 125 | 125 | 29 | no |
| rag | 125 | **0** | **113** | 34 | not manifested |

Only the memoryless floor is complete and judged, and it is the one result this
paper reports (§4.5). The other three were manifested but never judged, and the
RAG baseline never reached a manifest at all, because the scorer refuses to build
one with a missing twin rather than score a partial pair.

The empty deliverables are a single uniform failure, and it is not an adapter
failure. Deduplicated, the errors read `codex worker failed after 2 attempts:
no output.md produced`. The retrieval side was working while this happened: the
RAG baseline's base run embedded 179 times, retrieved 995 passages and assembled
721,655 characters of context, and the worker then produced nothing on all 125.
This is the deprecation of §4.6 arriving as a wall of null outputs rather than as
an announcement. Runs stalled 2026-09-04; the rows were committed 2026-09-14, so
that commit dates the release of the record rather than the runs.

**These rows carry no comparative claim.** They are released as provenance
for an interrupted prespecified pilot under a worker that no longer exists.
Because probe validity is worker-relative (§4.2), they cannot be completed by a
successor worker and they cannot be mixed with one. No ranking, no ordering, and
no per-system statement is derived from this table anywhere in this paper.

## 7. Limitations

Everything a reader would need to discount this work is in this
section, including the items that cost us the most. They are listed in rough
order of how much they should change your reading.

1. **G4 FAILED.** Judge-human agreement is κ = 0.537 against a prespecified
   gate of κ ≥ 0.75 (81.3% raw, n=150; §4.4), and every semantic verdict in
   this dataset inherits that error. A post-hoc cluster bootstrap added
   2026-09-17 puts the 95% interval at [0.370, 0.688], and its upper bound is
   below the gate, so the failure does not rest on the point estimate. It is not uniform. The judge over-accepts
   on absence-phrased criteria (8 of 8 errors, FALSE on only 1 of 44 items)
   and under-accepts on scope criteria (7 of 7), which cancel for this
   packet's mix of kinds and would not cancel for another. The over-accepts
   land 11-to-3 on the counterfactual side where pair credit compounds them,
   the lenient class is scored on 218 of 371 instances (58.8%), and our
   20-decoy audit passed this judge at 2/41 without catching it. Contained,
   not fatal: no side of any instance is scored on absence criteria alone, so
   the floor result is unaffected, but scores on absence-heavy archetypes (A4
   70.8%, A7 57.0%) should be read as upper bounds. Read the diagnosis in two
   halves. The degenerate pass mode is demonstrated on all 5,398 committed
   verdicts without human labels; whether the judge is *wrong* on specific
   items rests on one rater.

2. **One rater, and not an independent one.** G4 was rated by a single author,
   who has read seed content, a disclosed downgrade from the two-rater design
   originally specified. There is therefore no inter-rater κ, and judge error
   cannot be separated from rater error. A second independent rater is the
   first thing a v2 should buy, and a judge panel is not a substitute for one:
   the companion paper reports four further blinded judges agreeing with each
   other far above the gate and with this rater far below it, with identical
   verdict vectors on the sampled absence criteria (§4.4).

3. **All three released seeds fail the instance gate**, at 125, 131, and 115
   against a prespecified 135, and seed 3 also fails the cluster gate at 40/54
   against 45. Instances were retained and marked rather than topped up, and
   no failing probe was repaired. Four prespecified gates have failed in this
   project against one clean positive result, which is an asymmetry we report
   rather than manage.

4. **The evaluation this dataset was built for did not happen.** The pinned
   worker was withdrawn by its provider mid-pilot (§4.6), so there are no
   comparative system numbers here, and the partial rows in §6 are provenance
   rather than results. Worker billing and authentication changed during the
   study; the model and binary pin held until deprecation ended access
   entirely.

5. **Simulated organizations, not real logs.** Three screened seeds, one
   organization type (a two-team software company at L1–L2 scale), one worker
   model. The external-validity claim stops there.

6. **Nothing anchors probe difficulty to a human.** The ceiling condition is
   the pinned worker with the relevant facts injected, so a valid item is
   defined entirely relative to a model, and there is no human performance
   baseline anywhere on the probes. §4.2 reports that relativity as a finding.
   The separate point here is that construct validity against real
   organizational knowledge work is argued from the design and never measured.

7. **Event streams carry no timestamps.** `sim_time` is null throughout v1 and
   order is positional, so no result here separates knowing the order from
   reading a date. Screening anchors saw none either, so the condition is
   uniform.

8. **The judge and the human rater saw the same rules through different
   instruments.** The judge scored every criterion for one output together;
   the human scored one criterion per row, independently, under a
   no-backtracking rule. The rule text is materially identical in all three
   places it is maintained, which we checked, but no part of the κ gap has
   been attributed between judge quality and presentation. We found this while
   preparing the paper and did not measure it.

9. **Judge identity is procedural, not enforced.** The pipeline records the
   judging model as a free-text tag; nothing in code selects a model or
   verifies the tag against whatever actually produced the verdicts. The
   guarantee that the judge was never the worker model or the criterion-author
   family rests on protocol discipline and dated records, not on a mechanism.
   Anyone rebuilding on this harness should close that gap.

10. **Scoring-rule disclosures.** The scorer-exploit audit reads FAIL as
   literally prespecified and PASS when re-scoped to sides carrying at least
   one positive-content criterion; both lines are permanent in the report, and
   the re-scoping is post-hoc and labelled as such. The rank-direction
   robustness rule (≥2/3 seeds, a disclosed downgrade from ≥4/5) was
   prespecified for a pilot that did not run. **Twenty-eight criteria fall
   below the 0.7 raw-agreement threshold, and the prespecified rule to drop
   them was measured and then declined**: applying it moves the dataset from
   371 to 341 valid instances and fails all six gates instead of three, the
   whole 30-instance gap being sides the drop leaves with no criteria, and 25
   of the 28 rest on a single sampled judgment. We committed to the rule
   before running it, kept 371 after seeing the result, and publish both
   numbers with their dates (`datasets/dev/screening/sub07-sensitivity/`), so
   a reader who thinks that was the wrong call can prefer the other one.

11. **Released-harness configurations.** Market systems run their internal LLM
    on Gemini where configurable, with every deviation from vendor defaults
    listed (`docs/vendor-configs.md`). Shared-store configurations do not
    enforce per-principal visibility and v1 scores no leakage, so the silo
    ablation captures the benefit of sharing without its governance cost.
    These describe the released harness and support no claim in this paper.

12. **Vendor right-of-reply was not triggered**, because it attaches to
    published vendor numbers and this paper publishes none. The procedure
    stays specified for any re-anchored evaluation.

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
  seeds, recording which facts are probed and which are planted
  distractors), probe plans, realization maps, annotated scoring streams, the
  generator, the two unscreened holdout seeds, and every rater key.
- **Published on purpose**: the assertions. Scoring is impossible without
  them, and the cost of publishing them is that the set is open-book by
  construction, which the withheld generator, the holdout seeds and the canary
  strings are the answer to.
- `verify` fails the release on a leaked ledger, a missing canary, a tampered
  file, or any withheld filename. The redacted bundle still runs. It drives the real
  runner to the full frozen valid set (125 base + 125 twin rows on seed 1).

Hosting, decided 2026-09-14: HuggingFace, at
`huggingface.co/datasets/notmehul/memory-bench`, CC BY 4.0, and no dataset DOI. The two papers have Zenodo DOIs of their own, 10.5281/zenodo.22838321 for this
one and 10.5281/zenodo.22838603 for the methodology paper, and neither of them
identifies the dataset. The
repository is private until the all-in-one release; the bundle in it was built
and verified by `scripts/release.py` and round-trips through the host
byte-for-byte. Nothing ships with a BLOCKING row open in the G5 tracker
(`docs/standards-audit.md`).

## Acknowledgements

Harshit Agarwal reviewed an early draft of the gate criteria and the capability
ladder. His work at Boston Consulting Group on organizational structure and how
information moves through it informed the tier and authority model of §3.1. He
reviewed the measurement design only: he saw no seed content, no fact ledger and
no results, and he is not a rater in any measurement reported in this paper.

## Author contributions

M.S. designed the benchmark, built the generator, screening and scoring
pipelines, ran every measurement, and wrote the paper. The G4 calibration packet
was rated by M.S. alone, which is the limitation disclosure 2 records and the one
this work most needs repaired.

## Competing interests and funding

This is an independent study with no institutional affiliation and no funding
from any vendor whose system appears in the inclusion criteria. No
author-affiliated memory system is evaluated anywhere in this work, and no system
was given advance access to the dataset or the screening pipeline. Every
exclusion from the candidate set is reported with its reason.

## Ethics

The organizations, people and events in this dataset are synthetic; no real
personal data was collected or processed. The only human-subject component is the
author's own rating of the calibration packet.

## Data and code availability

The dataset is at `huggingface.co/datasets/notmehul/memory-bench` under CC BY
4.0, private until the all-in-one release; the harness is MIT. The bundle ships
the SUT-facing streams, the counterfactual twins, the probes with their scoring
assertions, the frozen valid sets, Croissant 1.0 and RAI metadata, and checksums.
The ground-truth ledger, probe plans, realization maps, annotated streams, the
generator and the two unscreened holdout seeds are withheld because they contain
the answers, and the withholding is enforced by `scripts/release.py verify`
rather than by care.

## Reproducibility

Every number in this paper derives from a committed artifact, and
`tests/test_paper_numbers.py` asserts the mapping. One limit is structural rather
than procedural: the pinned worker was withdrawn by its provider on 2026-09-04
(§4.6), so the screening anchors cannot be reproduced under the model that
produced them. The re-anchoring procedure is specified in §4.6 and ships with the
release.
