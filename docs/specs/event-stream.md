# Contract #2 — Event Stream Format

The event stream is what the system under test actually sees — naturalistic
organizational communication with facts embedded in it. One JSONL file per org,
`events.jsonl`, ordered by `sim_time`. Fact annotations are stripped before the stream
reaches the SUT; the annotated version is private to the scoring pipeline.

## 1. Event record

```json
{
  "event_id": "E-0102",
  "sim_time": "2026-03-04T10:00:00Z",
  "channel": "meeting",
  "surface": "team:platform/standup",
  "participants": ["persona:alice", "persona:carol", "persona:dev1"],
  "content": "…naturalistic rendered text (transcript, message, doc body)…",
  "artifacts": [],
  "_annotations": {
    "embeds_facts": [
      { "fact_id": "F-0042", "span": [214, 388], "rendering": "paraphrase" }
    ],
    "canaries": []
  }
}
```

> **Spec change v0.2 (2026-07-14, G2 audit):** `embeds_facts` carries spans for
> ALL embedded facts — probed and distractor alike. The earlier draft's
> separate `embeds_distractors` id-list is removed: the salience lint needs
> distractor spans (it compares probed vs. distractor span statistics), and
> distractor status already lives in the ledger's `distractor` flag — a
> second copy in the stream invited drift.

`_annotations` is removed in the SUT-facing stream. `span` = character offsets of the
fact's expression (for salience linting and audit, not string-match scoring).
`rendering`: `verbatim` | `paraphrase` | `implication` | `fragment` (one piece of a
`distributed` fact).

## 2. Channels and surfaces

| `channel` | `surface` examples | Notes |
|---|---|---|
| `meeting` | `team:platform/standup`, `org/all-hands` | rendered as transcript or notes |
| `dm` | `dm:alice-bob` | exactly 2 participants |
| `channel_msg` | `chat:platform-eng`, `chat:general` | team or org chat |
| `email` | `email:thread-0041` | thread id groups replies |
| `doc` | `doc:pricing-v3` | long-form; revisions are separate events sharing surface |
| `ticket` | `tickets:PLAT-231` | planning work modality |
| `pr` | `repo:platform/pr-88` | engineering modality; review comments are events |
| `calendar` | `cal:alice` | commitments and deadlines live here |

Surfaces carry implicit visibility: `dm:*` is private to participants, `chat:<team>-*`
and `team:*/…` are team_confidential, `org/*` and `chat:general` are org_public.
A fact's ledger `visibility` must be consistent with every surface it appears on
(validator-enforced).

## 3. Delivery model — who sees what

The runner feeds each event to the agents of principals who **witnessed** it:

- `participants` always witness the event.
- Shared-surface events (org_public / team surfaces) are witnessed by all entitled
  principals, delivered at `sim_time` (people "read the channel").
- No global feed exists. This is the mechanism that makes propagation a real,
  measurable problem: a decision in `team:platform/standup` reaches `persona:bob`
  (growth team) only if some later event carries it across — or if the SUT's shared
  memory layer does.

Runner API (the SUT adapter's entire ingestion surface):

```
ingest(principal_id, event_sans_annotations)   # called once per witness per event
```

A SUT may maintain one shared store, per-principal stores, or anything else — but its
`run_task(principal, task)` outputs are scored against `B(principal, t)`, so visibility
violations (using facts the principal never witnessed and isn't entitled to) score as
leakage even if they'd be "helpful."

## 4. Realism requirements (generator obligations)

- **Noise floor**: ≥60% of event content is operational filler — standups, scheduling,
  small talk, routine updates — embedding no probed facts. Memory systems must find
  signal, not summarize everything.
- **Distractor ratio**: ≥2 distractor facts per probed fact, including ≥1 near-miss
  (single-attribute perturbation: wrong tier, expired, lower authority).
- **Salience linting**: automated check that probed-fact spans do not differ
  systematically from distractor spans in length, position (e.g., always the meeting's
  first agenda item), or emphasis markers. Lint failures block release.
- **Voice consistency**: events render in the author's `voice_profile`; facts are
  phrased the way that persona talks, not in ledger-canonical form.
- **Interleaving**: archetype instances overlap in time; the stream never presents one
  scenario as a contiguous block.

## 5. Sizing

Timelines are sized so the full annotated-stripped transcript at L2 exceeds ~500k
tokens — large enough that full-transcript-in-context is costly and degrading, keeping
long-context an honest but non-trivial baseline. Per-level sizing lives in the dataset
plan.
