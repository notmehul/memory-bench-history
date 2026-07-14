# Test Fixture Manifest — Gate G0

Six fixture JSON files exercising the belief-state function. Each file is a
self-contained mini-org: entities + events + facts in ONE json object.

## JSON format (exact)

```json
{
  "org_id": "fix-witnessing",
  "entities": {
    "personas": [
      {"id": "persona:alice", "role": "engineering_lead", "authority_level": 3,
       "teams": ["team:platform"], "joins_at": null, "leaves_at": null,
       "role_changes": []}
    ],
    "teams": [{"id": "team:platform", "members": ["persona:alice"]}],
    "projects": [{"id": "project:phoenix", "teams": ["team:platform"]}]
  },
  "events": [
    {"event_id": "E-001", "surface": "team:platform/standup",
     "visibility": "team_confidential", "team": "team:platform",
     "participants": ["persona:alice"]}
  ],
  "facts": [
    {"fact_id": "F-001",
     "canonical": "one-sentence realistic org fact",
     "type": "decision", "tier": "team", "scope_ref": "team:platform",
     "visibility": "team_confidential", "visibility_acl": null,
     "author": "persona:alice", "capacity": "formal_decision",
     "temporal": {"valid_from_event": "E-001", "valid_until_event": null,
                  "supersedes": null, "superseded_by": null,
                  "decay_class": "durable"},
     "explicitness": "stated", "evidence_events": ["E-001"],
     "distractor": false, "archetype": null, "archetype_instance": null}
  ]
}
```

Enums:
- type: preference|decision|working_rule|reference|outcome|procedure|commitment|relationship
- tier: personal|team|project|org|external ; visibility: private|need_to_know|team_confidential|org_public
- capacity: speculation|opinion|directive|formal_decision
- explicitness: stated|implied|distributed (distributed ⇒ ≥2 evidence_events)
- decay_class: durable|role_bound|time_bound (time_bound ⇒ valid_until_event set)
- event visibility: private|team_confidential|org_public (team_confidential ⇒ "team" set)
- Surfaces: "dm:<a>-<b>" (private), "team:<name>/<meeting>" or "chat:<team>-eng"
  (team_confidential), "org/all-hands" or "chat:general" (org_public).

Rules for ALL fixtures:
- supersedes/superseded_by must agree bidirectionally between the two facts.
- Every event id referenced by any fact/persona must exist in "events".
- Events are ordered; their array position is the time index.
- Canonical texts: realistic, varied, one sentence, business-plausible. No two alike.
- Persona names/roles: realistic and varied across fixtures.

## Fixture 1 — witnessing.json (org "fix-witnessing")

Personas: alice, bob (team:platform); carol, dan (team:growth); eve (team:platform).
Teams: platform {alice, bob, eve}, growth {carol, dan}. 12 events E-001..E-012:
- E-001 platform standup, participants alice+bob (NOT eve). team_confidential.
- E-002 dm:alice-carol, participants alice+carol. private.
- E-003 org/all-hands, participants alice+carol only. org_public.
- E-004 chat:growth-eng, participants carol+dan. team_confidential (growth).
- E-005..E-012: filler events, various surfaces, any participants.
Facts:
- F-101: team-tier, team_confidential, scope team:platform, evidence [E-001].
- F-102: personal-tier preference, private, scope persona:alice, author alice, evidence [E-002].
- F-103: org-tier decision, org_public, scope org, evidence [E-003].
- F-104: team-tier, team_confidential, scope team:growth, evidence [E-004].
- F-105: distributed org-tier reference, org_public, evidence [E-003, E-005] (make E-005 org_public).

## Fixture 2 — precedence.json (org "fix-precedence")

Personas: fiona (cto, authority 4, team:core), greg (lead, 3, core), hana (ic, 2, core),
ivan (intern, 1, core). Team core = all four. 10 events, all team_confidential
core surfaces or org_public, all four participants in every event (witnessing is
NOT under test here).
Facts (all visible to everyone — org_public — unless noted):
- F-201 org-tier formal_decision (fiona, E-001) and F-202 team-tier opinion (greg,
  E-002): SAME topic, conflicting → rule 1 case.
- F-203 org-tier directive (fiona, E-003) vs F-204 team-tier directive (greg, E-004)
  vs F-205 personal-tier directive scope persona:hana (hana, E-005): all conflicting,
  equal capacity → rule 2 cases (each frame picks its own tier).
- F-206 team-tier opinion (greg, E-006) vs F-207 team-tier opinion (greg, E-008),
  same scope team:core, conflicting, different valid_from → rule 3 case.
- F-208 team-tier directive (greg, E-007) vs F-209 team-tier directive (hana, E-007),
  same scope, same valid_from event, conflicting → rule 4 tie case.

## Fixture 3 — supersession.json (org "fix-supersession")

Personas: jules (ops lead, 3), kira (ic, 2), team:ops = both. 9 events, all
org_public, both participants everywhere.
Facts: a pricing-style chain F-301 → F-302 → F-303 (F-302 supersedes F-301 at
E-004; F-303 supersedes F-302 at E-007; all org-tier formal_decision, org_public;
valid_from E-001, E-004, E-007 respectively). Plus one unrelated stable fact F-304.

## Fixture 4 — lifecycle.json (org "fix-lifecycle")

Personas: liam (lead, 3, team:infra), mona (ic, 2, infra), noor (ic, 2, infra);
liam has role_changes [{at_event E-006, new_role "director"}]; mona leaves_at E-008.
Team infra = all three. 10 events, all team_confidential infra surfaces, all
current members participate.
Facts:
- F-401 time_bound (valid_from E-001, valid_until E-005), team-tier, author liam.
- F-402 role_bound opinion authored by liam (E-002) → decays at his E-006 role change.
- F-403 role_bound directive authored by mona (E-003) → decays when she leaves (E-008).
- F-404 durable team decision authored by mona (E-004) → survives her departure.

## Fixture 5 — acl.json (org "fix-acl")

Personas: omar (exec 4), pia (lead 3, team:sales), quinn (ic 2, team:sales),
ravi (lead 3, team:legal). Teams: sales {pia, quinn}, legal {ravi}.
Project project:renewal teams [team:sales, team:legal]. 8 events.
Facts:
- F-501 need_to_know, acl [persona:omar, persona:pia], evidence on org_public event.
- F-502 need_to_know, acl [team:legal], evidence on org_public event.
- F-503 team_confidential project-tier, scope project:renewal, evidence org_public event.
- F-504 private, author omar, scope persona:omar, evidence dm:omar-pia (participants omar+pia).

## Fixture 6 — sealing.json (org "fix-sealing")

Personas: sara (lead 3, team:data, leaves_at E-006), tom (ic 2, data), uma (ic 2, data).
Team data = all three. 9 events; E-001..E-005 include sara, E-006+ do not.
Facts:
- F-601 private personal-tier preference, scope persona:sara, author sara,
  evidence dm:sara-tom E-002 (participants sara+tom) → sealed for tom after E-006.
- F-602 team-tier formal_decision by sara (E-003), durable, team_confidential → persists.
- F-603 role_bound opinion by sara (E-004) → decays at her departure.
