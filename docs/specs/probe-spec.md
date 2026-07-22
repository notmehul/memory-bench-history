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
