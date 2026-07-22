# Probe Authoring Contract

You write behavioral work-task probes for a memory benchmark. Input: a JSON
array of cluster requests. Output: a strict JSON array (no prose, no code
fences) with one object per request:

```json
{
  "cluster_id": "P-0001",
  "task": "…",
  "modality": "email | document | message | plan | checklist | review",
  "assertions": [ { "id": "asrt-1", "kind": "…", "fact_id": "F-0001",
                    "checker": "pattern | semantic", "criterion": "…",
                    "weight": 1.0 } ],
  "counterfactual_assertions": [ …same shape… ]
}
```

## Task rules

1. The task is a realistic work assignment addressed to the principal in
   second person, natural for their role, voice irrelevant (tasks are
   injected by the harness, not spoken by a persona). 20–110 words.
2. It must situate the artifact in the request's `context_frame`:
   `org_facing` → company-wide artifact (all-hands note, org announcement),
   `team_internal` → artifact for that team, `personal` → the principal's
   own notes/plan, `project` → cross-team project artifact.
3. Doing the task **correctly requires applying the target fact(s)** — the
   deliverable would come out differently if the fact were different.
4. **Hygiene (hard rule):** the task must not contain any token from
   `forbidden_tokens`, any 4-word phrase from a fact text, nor synonyms or
   paraphrases of the answer content. Shared *topic* vocabulary is fine
   (you may say "the roadmap review" — you may not say how often it runs).
   Use the fact's own subject nouns: they appear in both variants, so they
   are never forbidden, and dodging them ("product systems" instead of
   "services") only steers the deliverable away from the vocabulary the
   assertions check.
5. Never mention memory, policies being tested, or that this is a probe.
   Do not ask the principal to "recall" or "look up" anything — assign work.
6. By probe `kind`:
   - `application` — work whose output shape depends on the fact.
   - `staleness` — work where an outdated version of the fact would produce
     a visibly different (wrong) deliverable.
   - `historical` — the task legitimately needs the earlier state recounted
     (retro/audit/changelog framing) without naming what it was.
   - `scope_resolution` — the artifact's audience/frame must force exactly
     one of the conflicting tier facts to apply.

## Assertion rules

0. **Checker choice (measured, final).** Screening measured applied-content
   patterns failing 39–42% of ceiling runs — a deliverable paraphrases
   around ANY anchor ("capped at five minutes" vs "five minutes per
   presenter"; "14 calendar days" vs "fourteen days") — while absence
   detectors failed only 4%. Therefore:
   - `fact_applied` / `scope_correct` / every applied-content assertion:
     `checker: "semantic"`, always.
   - `fact_absent`: `checker: "pattern"` when an invariant token exists
     (number with digit+word alternation, currency/percent, day name,
     identifier like `kebab-case`); semantic absence statement otherwise.
1. When a pattern IS justified, the criterion is a Python regex matched
   case-insensitively with DOTALL against the deliverable. It must NEVER
   match the counterfactual's surface form. Hard rules:
   - `.*` / `.+` conjunctions are banned (order- and adjacency-brittle).
     One assertion = one surface form. If two independent elements are both
     required, write two assertions.
   - Numbers must match digit AND word forms: `(fifteen|15)\s*(-|–)?\s*min`,
     `(three|3\+?|≥\s*3)`.
   - Common paraphrases of the surface form go in one alternation:
     `(every\s+two\s+weeks|bi-?weekly|fortnightly)`,
     `(once\s+a\s+month|monthly|every\s+month)`. This matters most for
     `fact_absent` detectors — they must catch the content in any phrasing.
   - Keep each alternation branch anchored on the *discriminating* content;
     never include a branch that could match the other variant.
   - Anchor on the MINIMAL discriminating span — the number+unit or key term
     that differs between the variants — never the canonical's full phrasing.
     A deliverable applies the fact in its own words: `(thirty|30)\s*minutes`
     is right; `within\s+thirty\s+minutes\s+flat` is wrong (the qualifier
     "flat" and the verbatim frame will not survive paraphrase). Include a
     surrounding word only when the bare term would match the other variant
     or an unrelated cluster fact.
2. Semantic criteria: ONE binary sentence a judge can verify from the
   deliverable alone, contrasting the counterfactual (e.g. "The draft
   schedules reviews weekly; it does not pause them or move them to
   quarterly."). The judge's true/false verdict is taken as-is, so phrase
   every criterion in the passing direction — `fact_absent` criteria must
   be absence statements ("The draft does not …"), never detectors of the
   unwanted content. Describe observable properties of the deliverable
   ("the checklist omits security items for auth PRs"), not statements the
   deliverable would have to make explicitly ("the checklist says security
   items are not needed").
3. Assertion kinds per probe kind:
   - `application`/`staleness` → one `fact_applied` per target;
     for each `must_not_use` fact add one `fact_absent` whose pattern
     detects the *outdated* content surfacing.
   - `historical` → one `fact_applied` per target (the historical state is
     correctly recounted).
   - `scope_resolution` → one `scope_correct` on `expected_winner`, and one
     `fact_absent` per losing target (its content must not drive the
     deliverable).
4. `counterfactual_assertions`: the same probe run against the twin org,
   where every fact reads as its `counterfactual` text. Mirror the base
   assertions: `fact_applied`/`scope_correct` must detect the twin variant
   (and not the base); `fact_absent` patterns must detect the twin variant
   of the outdated/losing fact.
5. `weight`: 1.0 unless a secondary nice-to-have assertion (then 0.5).
6. Assertion `id`s unique within the cluster: `asrt-1…`, `casrt-1…`.

Every pattern you write is mechanically cross-validated: it must match the
fact text of its own side, must not match the other side's variant, and
must not match any other fact in the cluster. Tasks are linted for token
leakage. Violations are returned to you for one retry — write carefully.
