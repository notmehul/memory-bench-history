# Contract #1 — Ground-Truth Ledger Schema

The ledger is the hidden source of truth for a generated org. It is never shown to the
system under test. All scoring, probe construction, and belief-state computation derive
from it. Format: one JSON object per org, `ledger.json`.

## 1. Top-level structure

```json
{
  "org_id": "org-a3f9c2",
  "seed": 8817,
  "generator_version": "0.1.0",
  "difficulty": "L2",
  "entities": { "personas": [...], "teams": [...], "projects": [...] },
  "facts": [ ... ],
  "canaries": [ "mb-canary-7f3a-…" ]
}
```

## 2. Entities

```json
{
  "personas": [
    {
      "id": "persona:alice",
      "name": "Alice Iyer",
      "role": "engineering_lead",
      "authority_level": 3,
      "teams": ["team:platform"],
      "joins_at": null,
      "leaves_at": null,
      "voice_profile": "terse, direct, uses bullet points"
    }
  ],
  "teams": [
    { "id": "team:platform", "name": "Platform", "members": ["persona:alice", "..."] }
  ],
  "projects": [
    { "id": "project:phoenix", "teams": ["team:platform", "team:growth"] }
  ]
}
```

`authority_level`: 1 = intern/new hire, 2 = IC, 3 = lead, 4 = exec. Used with
`capacity` (below) to resolve authority-gradient conflicts.

## 3. Fact record

The core object. Every field is required unless marked optional.

```json
{
  "fact_id": "F-0042",
  "canonical": "All vendor-facing proposals must use the new pricing sheet (v3).",
  "type": "decision",
  "tier": "org",
  "scope_ref": "org",
  "visibility": "org_public",
  "visibility_acl": null,
  "author": "persona:carol",
  "capacity": "formal_decision",
  "temporal": {
    "valid_from_event": "E-0102",
    "valid_until_event": null,
    "supersedes": "F-0017",
    "superseded_by": null,
    "decay_class": "durable"
  },
  "explicitness": "stated",
  "evidence_events": ["E-0102"],
  "distractor": false,
  "archetype": "A7",
  "archetype_instance": "A7-003",
  "counterfactual": {
    "canonical": "All vendor-facing proposals must continue using pricing sheet v2 until Q4.",
    "notes": "inverts the supersession direction"
  }
}
```

### Field reference

| Field | Values / notes |
|---|---|
| `type` | `preference` \| `decision` \| `working_rule` \| `reference` \| `outcome` \| `procedure` \| `commitment` \| `relationship` |
| `tier` | `personal` \| `team` \| `project` \| `org` \| `external` |
| `scope_ref` | entity id the fact belongs to: `persona:alice`, `team:platform`, `project:phoenix`, `org`, `external:client-acme` |
| `visibility` | `private` \| `need_to_know` \| `team_confidential` \| `org_public` |
| `visibility_acl` | required iff `need_to_know`: explicit list of persona/team ids |
| `capacity` | `formal_decision` \| `directive` \| `opinion` \| `speculation` |
| `explicitness` | `stated` (verbatim in one event) \| `implied` (inferable from one event) \| `distributed` (requires composing ≥2 events, all listed in `evidence_events`) |
| `decay_class` | `durable` (survives author departure) \| `role_bound` (decays if author leaves/changes role) \| `time_bound` (has `valid_until_event`) |
| `distractor` | `true` for plausible facts that are never probed; fixed ratio per org (see dataset plan). Distractors still get full coordinates so near-miss distractors can be constructed by single-attribute perturbation |
| `distractor_kind` | optional, on distractors only: `plain` \| `near_miss_expired` \| `near_miss_other_scope` \| `near_miss_lower_capacity`. Structural marker so tooling never infers distractor identity from prose |
| `counterfactual` | present iff any probe targets this fact; the twin ledger substitutes `canonical` with this variant (see probe spec) |

### Type-specific update semantics (normative)

These define correct behavior; probes and assertions encode them:

- **decision** — supersedes conflicting facts at its tier and below from `valid_from`.
  Old decisions remain the correct answer for *historical* probes.
- **preference** — can drift; latest statement wins within the same scope_ref; never
  overrides a higher-tier `formal_decision` in that tier's context.
- **working_rule** — must be applied proactively (without retrieval-triggering
  queries) in all matching contexts within scope.
- **reference** — inert until relevant; staleness governed by `temporal`.
- **outcome** — must influence future recommendations in similar situations; never
  "expires" but can be outweighed by newer outcomes.
- **procedure** — like working_rule but multi-step; partial application scored.
- **commitment** — carries an implicit or explicit due time; must resurface at or
  before it, unprompted.
- **relationship** — context about people (reports-to, works-with, sensitive-topic);
  governs tone/routing, most often interacts with `visibility`.

## 4. Precedence rules (normative)

Given two applicable, valid, conflicting facts in a probe context:

1. Higher `capacity` wins (`formal_decision` > `directive` > `opinion` > `speculation`).
2. At equal capacity, the tier whose scope matches the *artifact* being produced wins
   (org policy for org-facing artifacts; personal preference for personal artifacts;
   team convention for team-internal artifacts).
3. At equal capacity and tier-match, more recent `valid_from` wins.
4. If still tied → the fact pair is an **A5 unresolved contradiction**; correct
   behavior is surfacing the conflict, and probes assert `conflict_flagged`.

Rule 2 is what makes precedence contextual rather than a fixed hierarchy; the probe
spec's `context_frame` field declares which scope an artifact belongs to.

## 5. Expected belief state

`B(principal, t)` = all facts `f` such that:

1. **witnessed**: principal participated in ≥1 of `f.evidence_events` at or before t,
   OR the event occurred on a shared surface the principal is entitled to at t
   (org_public, or team_confidential for their team — channel history is readable,
   so presence at publish time is not required). **Exception**: a `distributed`
   fact is only knowable by composing all its fragments, so witnessing requires
   *every* event in `evidence_events` to be witnessed, not ≥1. *(Spec bug found
   and fixed during G0: the original "≥1" rule let principals hold facts they
   could not possibly have assembled.)*;
2. **visible**: `f.visibility` permits the principal (ACL check for `need_to_know`);
3. **valid**: `valid_from ≤ t` and not superseded/expired at t (superseded facts stay
   in a `B_hist(principal, t)` set for historical probes);
4. **not decayed**: `decay_class` conditions hold at t.

The reference implementation of `B` is pure-functional over (ledger, event index) and
is the single scoring oracle. Any ambiguity discovered in `B` during dataset
construction is a spec bug and blocks release (see dataset plan, gate G2).

## 5b. Additional normative rules (added after G0/G1 audits)

- **Departed principals**: `B(p, t) = ∅` once `p.leaves_at ≤ t`. A departed
  persona's agent is decommissioned; the benchmark never probes them. Sealing
  and decay rules exist for the *remaining* principals' belief states.
- **Tier ↔ scope_ref pairing** (validator-enforced): `personal` → persona id,
  `team` → team id, `project` → project id, `org` → `"org"`, `external` →
  `external:*`. Mismatches are schema errors.
- **Supersession tier ordering** (validator-enforced): a fact may only
  supersede a fact at its own tier or below (`org > project > team =
  external > personal`); a team fact silently overriding an org decision is
  a schema error, per §3's "at its tier and below".

## 6. Design invariants

- Every non-distractor fact is targeted by ≥1 probe; every probed fact has a
  counterfactual variant.
- No fact's `canonical` text may appear verbatim in more than one event (forces
  paraphrase in event realization; prevents string-match shortcuts).
- Canary strings appear in event text (not in facts) at fixed low frequency, for
  post-hoc training-contamination detection.
- Ledger + event stream must round-trip: a validator recomputes every fact's
  `evidence_events` from annotations in the event stream and fails on mismatch.
