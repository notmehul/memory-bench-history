# memory-bench: Vision

Status: positioning document, 2026-07-25 (style pass 2026-08-28, no content
change). This states what the benchmark is *for* and the claim structure it
serves. The frozen v1 design lives in `architecture.md`; nothing here modifies
a contract, a gate, or generated data.

## 1. Premise

Organizations are getting smaller while the number of agents working inside
them grows. Each person picks the harness built for their work: a developer's
coding agent, a designer's creative tool, a generalist assistant. And they pick
it *because* it is specialized, with its own system prompt, tools, and
defaults. This heterogeneity is a feature of the ecosystem, not a bug to
standardize away.

It has one structural consequence: **organizational coherence cannot live in
the models.** The weights are plural, vendor-owned, and chosen per person. The
only thing every harness can share is the memory layer. If continual
learning of organizational knowledge (decisions, preferences, working rules,
outcomes, commitments) happens anywhere, it happens in a harness, not in
weights. The memory system is not an accessory to an org's agents; it is the
org's connective tissue.

## 2. The mini-AGI claim, operationalized

Dorsey frames the endpoint as every company becoming a "mini AGI": a world
model of the company in the center, humans at the edge supplying judgment,
coordination through the model replacing hierarchical information relay
([Sequoia podcast, 2026](https://sequoiacap.com/podcast/jack-dorsey-every-company-can-now-be-a-mini-agi/)).
We take the frame seriously and sharpen it.

The naive implementation, pool every artifact and give everyone the same view,
is not a collective intelligence; it is a rumor mill with perfect recall.
Personal preferences are not org policy. A leadership decision outranks a loud
opinion. Superseded plans must stop driving behavior while remaining
retrievable. Need-to-know facts must not diffuse. The mini-AGI property comes
from the world model being **scoped, tiered, and temporally correct**: each
agent gets the context that is right for its principal and its task, at the
current epoch of truth.

This is testable, and the pilot baselines instantiate the competing
implementations directly. "Pool everything" is the long-context and naive-RAG
baselines; typed, scoped harnesses are the structured alternative. The
benchmark asks which design actually produces coherent organizational
behavior, and at what scale the pooled version stops working.

## 3. The capability ladder

"Mini AGI" is a vibe until decomposed into measurable capabilities. The
benchmark's metrics organize into four rungs; every scenario archetype
(`architecture.md` §5) feeds exactly one:

| Rung | Capability | Metrics | Archetypes | v1 |
|---|---|---|---|---|
| 0, retention | facts recallable on request | recall (table stakes; never headlined) | — | implicit in all probes |
| 1, alignment | each agent behaves as the org intends for its position: the right tier wins, current truth drives behavior, authority is respected | scope-resolution accuracy, staleness rate, decay correctness, authority-weighted accuracy | A4, A6, A7, A9 | A4, A7 |
| 2, coordination | knowledge moves across principals correctly and safely | propagation latency, rollback fidelity, leakage rate, conflict-surfacing | A1, A5, A8, A10 | A1 |
| 3, compounding | the org improves as a function of its own history, unprompted | proactive application, prospective recall, bootstrap latency, experience utilization | A2, A3, A11, A12 | A2 |

Rung 0 is where existing memory benchmarks live and where long context
saturates trivially. This benchmark's claim territory is rungs 1–3.

v1 is a deliberate **vertical slice**: at least one archetype on every rung
above retention, rather than exhaustive coverage of any single rung. v2
completes the rungs, A12 and A5 first, because outcome learning and conflict
surfacing are the most mini-AGI-critical capabilities. Results are always a
radar grouped by rung, never a single aggregate (`architecture.md` §6.5).

## 4. Fragmentation: the failure mode of the present

Today every agent product ships its own siloed memory; the org's knowledge
shatters per app and per person. A decision made in one room never reaches the
agent of someone who wasn't there. In ladder terms, silos cap rung 2 at zero:
propagation latency across a silo boundary is infinite.

The pilot measures this directly with a **silo ablation**: the same memory
system run once as per-principal isolated stores and once as a shared,
visibility-aware store. The delta is the measured value of sharing.
v1 captures only the propagation *benefit* of sharing; the governance *cost*,
leakage, arrives with A10 in v2. The two are adversarial by design, and are
always reported jointly once both exist.

## 5. Claims discipline

The framing above is positioning; claims stop at what is instantiated.

- v1 measures four archetypes at L1–L2 in a simulated two-team **software**
  organization. It does not measure "mini-AGI-ness," and its external-validity
  claim is scoped to that org type; industry breadth (consulting, regulated
  finance, …) enters in v2 as a *designed factor*, not by relabeling v1.
- At L1–L2 scale, long context may win everything. That is a real, publishable
  finding. The premise "every piece of work creates an artifact" guarantees
  the stream outgrows any context window; the scientific object is the
  crossover point (mapped at L3) and *which rungs fail first* as pooled
  context degrades.
- Every hypothesis about pilot outcomes is prespecified in `dataset-plan.md`
  (Phase 5), dated, before any pilot run. This is the same discipline as the
  Phase 3 screening amendments.
- The study is independent: no author-affiliated memory system is evaluated,
  market systems enter by published inclusion criteria (with every exclusion
  reported), and the structured-memory hypothesis is stated at the
  architecture-class level, tested via a generic open-source reference
  implementation. Author affiliations are disclosed in the paper.

## 6. Roadmap implications

- **v2 archetype priority** (reordered under this lens): A12, A5, then A10 +
  A8 (completing the adversarial sharing pair), then A3, A6, A9, A11.
- **Grid track = consumer portability.** The secondary model-grid track exists
  to test that memory-system rankings are consumer-invariant; a memory layer
  whose value evaporates outside one vendor's harness fails the premise in §1.
  Probe validity is task-model-relative (measured in Phase 3: ceiling-gate
  survival 17/54 for gpt-5.4-mini vs 37/54 for gpt-5.4 under the identical
  strict rule), so each added consumer model requires its own screening pass.
  And the harness is part of the consumer: identical gpt-5.4 weights behind
  two agent harnesses agreed on only 65% of twin-ceiling outcomes in a
  prespecified 60-run study (2026-07-25, evidence in
  `datasets/dev/screening/harness-study-2026-07-25/`).
- **v3, heterogeneous organization**: per-principal consumer profiles
  (synthetic profiles differing in system prompt, specialization, and context
  budget, not product clones, which date), agent-authored artifacts as an
  ingestion channel, and delegated authority (what weight an agent's
  assertion carries on behalf of its principal) as an A6 extension.
- **Exploratory metric, cross-principal coherence**: behavioral agreement
  across instances of one probe cluster issued via different principals;
  computable from existing per-instance scores at zero content cost,
  confounded with offset variation, reported as secondary only.
