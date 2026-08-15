# Contract #3 — Probe Specification

Probes are behavioral work tasks injected into a principal's session at a scheduled
point in the timeline. They are scored against the ledger via machine-checkable
assertions, with counterfactual twins and floor/ceiling conditions. One JSONL file per
org, `probes.jsonl`.

## 1. Probe record

```json
{
  "probe_id": "P-0031",
  "archetype_instance": "A1-002",
  "principal": "persona:bob",
  "inject_after_event": "E-0300",
  "context_frame": "org_facing",
  "task": "Draft the proposal email to Acme for the Phoenix renewal. Keep it under 300 words.",
  "modality": "document",
  "targets": ["F-0042"],
  "must_not_use": ["F-0017"],
  "assertions": [
    {
      "id": "asrt-1",
      "kind": "fact_applied",
      "fact_id": "F-0042",
      "checker": "semantic",
      "criterion": "The proposal uses v3 pricing figures ($4,200/seat), not v2 ($3,800/seat).",
      "weight": 1.0
    },
    {
      "id": "asrt-2",
      "kind": "fact_absent",
      "fact_id": "F-0017",
      "checker": "pattern",
      "criterion": "\\$3,?800",
      "weight": 1.0
    }
  ],
  "counterfactual_probe": {
    "ledger_deltas": ["F-0042"],
    "assertions": [
      { "id": "casrt-1", "kind": "fact_applied", "fact_id": "F-0042", "checker": "semantic",
        "criterion": "The proposal uses v2 pricing figures ($3,800/seat).", "weight": 1.0 }
    ]
  },
  "judge_rubric": null,
  "metrics": ["application_accuracy", "staleness_rate"],
  "latency_series": null
}
```

## 2. Assertion kinds

| `kind` | Meaning | Typical checker |
|---|---|---|
| `fact_applied` | the fact's content shaped the output | `semantic` |
| `fact_absent` | superseded/private/wrong-tier fact does NOT appear | `pattern` or `semantic` |
| `constraint_followed` | a working_rule/procedure was obeyed (e.g., legal CC'd) | `structural` (parse output) |
| `conflict_flagged` | output surfaces an unresolved contradiction instead of silently picking | `semantic` |
| `scope_correct` | when tiers conflict, the `context_frame`-appropriate tier won | `semantic`, paired facts |
| `unprompted_surface` | commitment/deadline raised without the task asking | `semantic` |

Checkers:
- `pattern` — regex over output; used only for facts with unambiguous surface forms
  (numbers, names, identifiers). Deterministic.
- `structural` — programmatic parse (recipients list, section presence, ordering).
  Deterministic.
- `semantic` — LLM judge with a binary criterion. Constraints: judge model ≠ any model
  under test; judge sees only (output, criterion), never the ledger or probe metadata;
  every semantic criterion is validated against human labels on the calibration subset
  (report per-criterion agreement; κ < 0.7 → criterion rewritten or probe dropped).

## 3. Execution conditions

Every probe instance runs in three conditions:

| Condition | Context given to the task model |
|---|---|
| `sut` | whatever the SUT adapter provides |
| `floor` | task only, no memory of the org |
| `ceiling` | task + exactly the facts in `B(principal, t)` relevant to `targets` (rendered canonically) |

Scoring per assertion: pass/fail → probe score = weighted mean → **normalized score**
`(sut − floor) / (ceiling − floor)`, clipped to [0, 1].

Validity gates (computed during dataset construction, before any SUT is evaluated):
- `ceiling` must pass ≥ 90% of instances of a probe template, else the probe measures
  reasoning → dropped from memory metrics (kept in a diagnostic set).
- `floor` must fail ≥ 70% of instances, else the probe is passable without memory →
  redesigned or dropped.

> **Spec change v0.2 (2026-07-19, Phase 3 pilot):** for counterfactual-paired
> probes the floor gate is evaluated at pair level, matching §4's crediting
> unit: a floor run only counts as "passable without memory" if its output
> scores 1.0 against BOTH the base and counterfactual assertion sets (the
> floor prompt contains no org context, so one output serves both sides).
> Rationale: some canonical facts coincide with plausible industry defaults
> (e.g. a common naming convention), so a memoryless model can guess the
> base side; the twin pairing was designed precisely to cancel this
> (risk register: "generator LLM's own biases make facts guessable —
> counterfactual pairing structurally cancels this"). Dropping such probes
> per-side would throw away valid pairs. The per-side floor pass rate is
> still computed and reported as `guessability` per cluster.

> **Spec change v0.3 (2026-07-23, Phase 3 screening):** two measured
> revisions. (1) *Checker policy:* applied-content assertions
> (`fact_applied`, `scope_correct`, …) must use the `semantic` checker;
> `pattern` is reserved for `fact_absent` detectors. Seed-1 screening
> measured applied-content regexes failing 39–42% of ceiling runs — a
> deliverable paraphrases around any anchor — vs 4% for absence detectors
> and 9–17% for semantic criteria. (2) *Screening unit:* validity gates are
> evaluated per probe INSTANCE — an instance is valid iff its ceiling
> passes, its twin ceiling passes, and its floor output does not pass at
> pair level; a template (cluster) survives with ≥2/3 valid instances and
> ships only its valid instances. The earlier all-instances cluster rule
> demanded per-run reliability ≥98% (0.9^6 ≈ 0.53 cluster survival even at
> 9% instance noise), which no realistic task-model/judge pair delivers at
> n=3; both the strict and instance-level counts are reported. Additional
> authoring rule from failure adjudication: an assertion must never punish
> content from a different co-valid fact of the same cluster (complementary
> facts legitimately co-apply; only genuine precedence losers get
> `fact_absent` guards).

> **Spec change v0.4 (2026-08-07, approved by the PI; from the scorer-exploit
> audit and seed-2 adjudication — evidence in
> `datasets/dev/screening/exploit-audit/` and the dataset-plan G3 note):**
> 1. *Commitment rule (scoring):* an output that asserts the discriminative
>    values of BOTH sides of a paired probe (any surface variant) is
>    non-committal; all its applied-content criteria (`fact_applied`,
>    `scope_correct`, `constraint_followed`) score FAIL on both sides.
>    `fact_absent` detectors score normally. Rationale: pair crediting
>    cancels prior-based guessing but not deliberate hedging — the audit
>    measured enumerate-both-values passing 27/45 pairs.
> 2. *Cross-side absence detectors (structure):* every paired instance
>    carries a mechanically generated `fact_absent` pattern pair
>    (`asrt-cs` / `casrt-cs`) matching the OTHER side's discriminative
>    value variants. Generated, not authored: the pattern must match every
>    other-side surface variant, no own-side variant, and no co-valid
>    sibling canonical (detectors target the twin delta only — never
>    nested co-valid constraints).
> 3. *Natural-artifact rule (authoring):* absence criteria may demand only
>    OBSERVABLE absence; they may never require explicit denial, negation,
>    or historical narration the task did not ask for ("states there is no
>    X", "says X never ran", "because X was discontinued" are all invalid
>    criteria — seed-2 adjudication found this class caused 5/11 final
>    drops while the twin fact was correctly applied).
> 4. *Pattern quality:* alternations must not reduce to bare numerals or
>    common words under optional anchors (`(one|1)\s*(?:pm)?` matches "1";
>    banned). Surface-variant cross-validation runs against BOTH orgs'
>    variant sets.
> Re-scoring under v0.4 happens only after per-flip adjudication;
> pre-/post-v0.4 numbers are reported side by side wherever both exist.
>
> **v0.4 refinements R1–R5 (2026-08-07, from adjudication of the 11
> mechanical-layer flips — 0 of 11 were true positives):**
> R1 — duration-class anchors (number + minute/hour/day/week/month) are
> banned for cross-side detectors and the hedge rule: durations recur in
> unrelated semantic roles in honest artifacts (8/11 flips). Money, %,
> day-names/cadence words, unitless counts with object nouns, compounds,
> and identifiers remain valid.
> R2 — an anchor whose naive s/es-lemma appears in the other side's text
> is skipped (monday/mondays inflection degeneracy).
> R3 — `kind=historical` probes carry no cross-side detectors and are
> exempt from the hedge rule: multi-epoch narration is the task.
> R4 — a `-cs`/hedge match preceded by a negator within the same sentence
> (≤12 tokens) is suppressed: negated mention is commitment, not
> enumeration. Suppression spares only the absence detector; a negated
> mention still cannot satisfy the side's affirmative criteria.
> R5 — per-branch hard errors: no unit-less digit-only branches, no
> unit-less bare number-words.
> Consequence, measured and accepted: the mechanical layer alone cannot
> police enumeration for duration-valued probes (audit residual rises
> accordingly); full closure is assigned to the v0.4.3 semantic layer.
>
> **v0.4.3 semantic layer (2026-08-15, applied to all five orgs before
> seeds 3–5 have any screening evidence; seeds 1–2 re-scored from cached
> outputs with only the changed criteria re-judged blind — pre/post
> reported side by side in the G3 note):**
> S1 — *Semantic cross-side detectors.* Every paired non-historical side
> the pattern layer cannot cover (after R1–R5 that is the majority of
> sides) carries `asrt-css` / `casrt-css`: `fact_absent` + `semantic`,
> generated from ONE fixed template that hunts the other side's delta-fact
> canonicals verbatim — "The deliverable does not present the statement
> "…" as currently in effect. Mentioning it only as past, replaced,
> hypothetical, or rejected does not count as presenting it." (the
> past/replaced carve-out is the semantic form of R4). Never authored,
> never per-cluster; judged by the standard blinded pipeline.
> S2 — *Natural-artifact rule, operational form.* An applied-content
> criterion is a **pure retraction** iff its only demanded content is that
> the other side's value/arrangement does not / no longer / never holds,
> adding no independent value. Every pure-retraction criterion is
> rewritten to observable absence of the retracted value. The rewrite is
> monotonic (an explicit denial already implies observable absence), so
> it can only stop punishing natural omission. Classification ran
> uniformly over all 495 non-historical applied criteria by the content
> model under a fixed rubric, then was audited by hand (44 flagged, 40
> applied, 4 already-observable originals kept; log in
> `datasets/dev/screening/natural-artifact-sweep/`). Permission-style
> negatives ("may pay without finance review", "no cap") are positive
> content and were left alone — evidence: they pass twin-ceiling at
> 27/36 and 35/39 in seeds 1–2, at or above the overall rate.
> S3 — *Tier rule for sibling guards.* `fact_absent` guards on a sibling
> fact of a HIGHER tier than the artifact's frame are never used: nested
> rules (org→team/personal, team→personal) may legitimately be restated,
> and misapplying them is already caught by the winner's `scope_correct`
> criterion. Guards on LOWER-tier siblings remain (that is a real scope
> leak). Generalizes the 2026-08-06 lineage precedent to every org;
> symmetric pairs only. The two asymmetric lineage cases (org-1 P-0023,
> org-4 P-0040) resolve under the same rule now that S1 carries the
> cross-side role.
> S4 — *Authored pattern quality (rule 4 applied to authored patterns).*
> Six authored absence patterns whose branches reduce to bare numerals or
> common words under optional anchors (`(5\s*(pm)?|10\s*(am)?)`,
> `\b(thirty|30)\b`, `\b(half|…)`) were replaced by semantic mirrors of the
> same absence intent; kind and pairing unchanged.
> S5 — *Empty-output rule (scoring).* An empty / whitespace-only / missing
> deliverable (including a worker failure after retries) scores 0.0 on
> every assertion, absence detectors included, and stays in the
> denominator: no deliverable, no credit.
> Provenance: incremental blinded re-judging is harness-enforced —
> judgements now carry a per-criterion text hash and `report` refuses any
> verdict whose criterion text changed without a re-judge.
>
> **S1' — Commitment clause moves to the judge rubric (2026-08-15).** With
> S1 rejected, enumeration closure is the rubric v2 clause
> (`docs/specs/judge-rubric.md`): a positive-content criterion is not
> satisfied by an output that presents the required value together with a
> conflicting alternative as both current. Measured on the rebuilt exploit
> audit: enumerate-both-values pair-passes 18 → 1, base-side mean 0.74 →
> 0.15; the one remaining pair-pass is a non-inverting twin (below).
>
> **S6 — Discrimination gate (prespecified 2026-08-15, before any
> cross-verdict existed; computed on seeds 1–2 immediately after).** The
> exploit audit's `base_correct` row exposed a twin whose counterfactual
> criteria are satisfied by the honest BASE output (org-1 P-0032: "over
> 200 lines after lunch" complements "under 200 lines before lunch"). Such
> a pair does not discriminate — a stale SUT would be credited on the twin
> — and the ceiling/twin/floor gates cannot see it. Rule: an instance is
> valid only if, in addition to the v0.3 conditions, its ceiling output
> scores < 1.0 against the counterfactual assertion set AND its twin
> output scores < 1.0 against the base assertion set. Both cross-scores
> come from the same blinded judging pass (ceiling rows carry the cf
> criteria, twin rows the base criteria; the judge sees only criteria).
> Reported per instance as `ceiling_vs_cf` / `twin_vs_base`.
>
> **R6 — contested-attribute rule for pattern anchors (2026-08-15, from
> seed-3 adjudication).** A calendar/time-of-day, money or percent anchor
> is emitted only when the OTHER side of the same delta fact also carries
> a value of that class; when a class appears on one side only
> (retraction or attribute-less twin) the detector would punish incidental
> uses of that vocabulary (seed-3 P-0041: "cannot wait until Monday" in a
> no-freeze twin hit a base-side day-name detector). Unit-anchored counts
> unchanged. Applied to all five orgs; seeds 1–3 re-scored mechanically
> (no re-judging): seed 1 126→125 valid instances (an S6-unmasked
> non-inverting instance), seeds 2–3 gates unchanged. Detector coverage
> after R6: 51/54/33/81/54 pattern detectors per org.
>
> **Exploit-audit bar, re-scoped and disclosed (2026-08-15).** The
> prespecified bar demanded zero single-side 1.0 for waffle. The
> natural-artifact rule (approved v0.4 rule 3) makes some counterfactual
> sides absence-only by design (retraction counterfactuals: "no longer
> Mondays 2pm" has no replacement value), and a content-free output passes
> an absence-only side by construction while the pair still fails. The
> single-side clause is therefore re-scoped to sides carrying at least one
> positive-content criterion; the audit report prints BOTH the original
> and the re-scoped verdict, and the count of absence-only sides, forever.
> This is a post-hoc re-scoping made after seeing three such sides; it is
> labelled as such and is not called prespecified.

## 4. Counterfactual twins

`counterfactual_probe.ledger_deltas` names the facts whose `counterfactual.canonical`
variant is substituted; the generator produces a **twin org** (same seed, same
timeline skeleton, re-rendered events for delta facts) and the same probe runs against
it. A probe instance is **credited only if the SUT passes both sides** — correct
behavior on the base org AND correctly *different* behavior on the twin. Passing one
side only ⇒ score 0 for the pair (behavior wasn't memory-driven).

## 5. Latency-series probes (A1 decision ripple, A2 silent rule, A8 rollback)

For dynamics metrics, the same logical probe repeats at scheduled offsets:

```json
"latency_series": {
  "offsets_events": [5, 20, 60, 150],
  "metric": "propagation_latency"
}
```

Propagation latency = first offset at which the normalized score ≥ 0.8, reported as a
distribution over instances (never a mean alone — right-censored instances, where the
SUT never crosses 0.8, are reported as such, not imputed).

Rollback fidelity (A8) uses the inverse: after the correction event, score at each
offset measures how fast the *wrong* behavior disappears across every principal it had
spread to.

## 6. Probe hygiene rules

- The task text must never mention, hint at, or share vocabulary with `targets` beyond
  what the work task naturally requires (lint: n-gram overlap between task text and
  fact canonicals below threshold; audited on the human-validation sample).
- Probes are injected in-session and look like ordinary tasks; the SUT is never told
  it is being probed. Probe outputs are NOT fed back into the event stream (no
  self-contamination).
- Each archetype instance yields ≥3 probe instances (different principals or offsets)
  so per-archetype scores have usable sample sizes.
- `must_not_use` facts must be in `B_hist` or a non-entitled tier — i.e., genuinely
  known-but-wrong-to-use, not merely absent (otherwise `fact_absent` is trivially
  satisfied).
