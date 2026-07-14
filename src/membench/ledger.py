"""Ground-truth ledger data model and validation.

Implements Contract #1 (docs/specs/ledger-schema.md). The ledger is the hidden
source of truth for a generated org; the belief-state function (belief.py) is a
pure function over (Ledger, EventIndex).

Time is discrete: t is the index of an event in the org's ordered event stream.
Facts reference events by id; the EventIndex maps ids to positions and carries
the witnessing metadata (surface, visibility, participants) that belief
computation needs. Event content is irrelevant here and deliberately absent.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path

FACT_TYPES = {
    "preference", "decision", "working_rule", "reference",
    "outcome", "procedure", "commitment", "relationship",
}
TIERS = {"personal", "team", "project", "org", "external"}
VISIBILITIES = {"private", "need_to_know", "team_confidential", "org_public"}
CAPACITIES = ("speculation", "opinion", "directive", "formal_decision")  # ascending rank
EXPLICITNESS = {"stated", "implied", "distributed"}
DECAY_CLASSES = {"durable", "role_bound", "time_bound"}
SURFACE_VISIBILITIES = {"private", "team_confidential", "org_public"}


class LedgerValidationError(Exception):
    """Raised when a ledger or event index violates Contract #1."""


@dataclass(frozen=True)
class Persona:
    id: str
    role: str
    authority_level: int
    teams: tuple[str, ...]
    joins_at: str | None = None   # event id; None = present from t=0
    leaves_at: str | None = None  # event id; None = never leaves
    role_changes: tuple[tuple[str, str], ...] = ()  # (event_id, new_role)


@dataclass(frozen=True)
class Team:
    id: str
    members: tuple[str, ...]


@dataclass(frozen=True)
class Project:
    id: str
    teams: tuple[str, ...]


@dataclass(frozen=True)
class Temporal:
    valid_from_event: str
    valid_until_event: str | None = None
    supersedes: str | None = None
    superseded_by: str | None = None
    decay_class: str = "durable"


@dataclass(frozen=True)
class Fact:
    fact_id: str
    canonical: str
    type: str
    tier: str
    scope_ref: str
    visibility: str
    author: str
    capacity: str
    temporal: Temporal
    explicitness: str
    evidence_events: tuple[str, ...]
    visibility_acl: tuple[str, ...] | None = None
    distractor: bool = False
    archetype: str | None = None
    archetype_instance: str | None = None


@dataclass(frozen=True)
class EventMeta:
    """Witnessing metadata for one event; content lives in the event stream."""
    event_id: str
    surface: str
    visibility: str                 # org_public | team_confidential | private
    participants: tuple[str, ...]
    team: str | None = None         # required iff visibility == team_confidential


@dataclass
class EventIndex:
    events: list[EventMeta]
    _pos: dict[str, int] = field(init=False, repr=False)

    def __post_init__(self) -> None:
        self._pos = {e.event_id: i for i, e in enumerate(self.events)}
        if len(self._pos) != len(self.events):
            raise LedgerValidationError("duplicate event ids in event index")

    def index_of(self, event_id: str) -> int:
        try:
            return self._pos[event_id]
        except KeyError:
            raise LedgerValidationError(f"unknown event id: {event_id}") from None

    def __contains__(self, event_id: str) -> bool:
        return event_id in self._pos


@dataclass
class Ledger:
    org_id: str
    personas: dict[str, Persona]
    teams: dict[str, Team]
    projects: dict[str, Project]
    facts: dict[str, Fact]


def _tuple(xs) -> tuple:
    return tuple(xs) if xs else ()


def load_event_index(data: dict) -> EventIndex:
    events = [
        EventMeta(
            event_id=e["event_id"],
            surface=e["surface"],
            visibility=e["visibility"],
            participants=_tuple(e.get("participants")),
            team=e.get("team"),
        )
        for e in data["events"]
    ]
    return EventIndex(events=events)


def load_ledger(data: dict) -> Ledger:
    entities = data.get("entities", {})
    personas = {
        p["id"]: Persona(
            id=p["id"],
            role=p["role"],
            authority_level=p["authority_level"],
            teams=_tuple(p.get("teams")),
            joins_at=p.get("joins_at"),
            leaves_at=p.get("leaves_at"),
            role_changes=tuple(
                (rc["at_event"], rc["new_role"]) for rc in p.get("role_changes", [])
            ),
        )
        for p in entities.get("personas", [])
    }
    teams = {
        t["id"]: Team(id=t["id"], members=_tuple(t.get("members")))
        for t in entities.get("teams", [])
    }
    projects = {
        pr["id"]: Project(id=pr["id"], teams=_tuple(pr.get("teams")))
        for pr in entities.get("projects", [])
    }
    facts = {}
    for f in data["facts"]:
        tmp = f["temporal"]
        facts[f["fact_id"]] = Fact(
            fact_id=f["fact_id"],
            canonical=f["canonical"],
            type=f["type"],
            tier=f["tier"],
            scope_ref=f["scope_ref"],
            visibility=f["visibility"],
            visibility_acl=_tuple(f.get("visibility_acl")) or None,
            author=f["author"],
            capacity=f["capacity"],
            temporal=Temporal(
                valid_from_event=tmp["valid_from_event"],
                valid_until_event=tmp.get("valid_until_event"),
                supersedes=tmp.get("supersedes"),
                superseded_by=tmp.get("superseded_by"),
                decay_class=tmp.get("decay_class", "durable"),
            ),
            explicitness=f["explicitness"],
            evidence_events=_tuple(f["evidence_events"]),
            distractor=f.get("distractor", False),
            archetype=f.get("archetype"),
            archetype_instance=f.get("archetype_instance"),
        )
    return Ledger(
        org_id=data.get("org_id", "org-unknown"),
        personas=personas,
        teams=teams,
        projects=projects,
        facts=facts,
    )


def load_fixture(path: str | Path) -> tuple[Ledger, EventIndex]:
    """Load a fixture file holding both the ledger and its event index."""
    data = json.loads(Path(path).read_text())
    ledger = load_ledger(data)
    index = load_event_index(data)
    validate(ledger, index)
    return ledger, index


def validate(ledger: Ledger, index: EventIndex) -> None:
    """Enforce Contract #1 invariants. Raises LedgerValidationError."""
    errors: list[str] = []

    for e in index.events:
        if e.visibility not in SURFACE_VISIBILITIES:
            errors.append(f"{e.event_id}: bad surface visibility {e.visibility!r}")
        if e.visibility == "team_confidential" and not e.team:
            errors.append(f"{e.event_id}: team_confidential surface requires team")
        if e.team is not None and e.team not in ledger.teams:
            errors.append(f"{e.event_id}: unknown team {e.team!r}")
        for p in e.participants:
            if p not in ledger.personas:
                errors.append(f"{e.event_id}: unknown participant {p!r}")

    for p in ledger.personas.values():
        for team in p.teams:
            if team not in ledger.teams:
                errors.append(f"{p.id}: unknown team {team!r}")
        for ev in (p.joins_at, p.leaves_at, *(rc[0] for rc in p.role_changes)):
            if ev is not None and ev not in index:
                errors.append(f"{p.id}: unknown lifecycle event {ev!r}")

    for t in ledger.teams.values():
        for m in t.members:
            if m not in ledger.personas:
                errors.append(f"{t.id}: unknown member {m!r}")

    for f in ledger.facts.values():
        fid = f.fact_id
        if f.type not in FACT_TYPES:
            errors.append(f"{fid}: bad type {f.type!r}")
        if f.tier not in TIERS:
            errors.append(f"{fid}: bad tier {f.tier!r}")
        if f.visibility not in VISIBILITIES:
            errors.append(f"{fid}: bad visibility {f.visibility!r}")
        if f.capacity not in CAPACITIES:
            errors.append(f"{fid}: bad capacity {f.capacity!r}")
        if f.explicitness not in EXPLICITNESS:
            errors.append(f"{fid}: bad explicitness {f.explicitness!r}")
        if f.temporal.decay_class not in DECAY_CLASSES:
            errors.append(f"{fid}: bad decay_class {f.temporal.decay_class!r}")
        if f.author not in ledger.personas:
            errors.append(f"{fid}: unknown author {f.author!r}")
        if f.visibility == "need_to_know" and not f.visibility_acl:
            errors.append(f"{fid}: need_to_know requires visibility_acl")
        if f.visibility_acl:
            for entry in f.visibility_acl:
                if entry not in ledger.personas and entry not in ledger.teams:
                    errors.append(f"{fid}: unknown ACL entry {entry!r}")
        if f.temporal.decay_class == "time_bound" and not f.temporal.valid_until_event:
            errors.append(f"{fid}: time_bound requires valid_until_event")
        if not f.evidence_events:
            errors.append(f"{fid}: evidence_events is empty")
        if f.explicitness == "distributed" and len(f.evidence_events) < 2:
            errors.append(f"{fid}: distributed fact needs >=2 evidence events")
        for ev in (f.temporal.valid_from_event, f.temporal.valid_until_event,
                   *f.evidence_events):
            if ev is not None and ev not in index:
                errors.append(f"{fid}: unknown event {ev!r}")
        for ref in (f.temporal.supersedes, f.temporal.superseded_by):
            if ref is not None and ref not in ledger.facts:
                errors.append(f"{fid}: unknown fact reference {ref!r}")

    # supersedes / superseded_by must agree in both directions
    for f in ledger.facts.values():
        if f.temporal.supersedes:
            old = ledger.facts.get(f.temporal.supersedes)
            if old and old.temporal.superseded_by != f.fact_id:
                errors.append(
                    f"{f.fact_id} supersedes {old.fact_id}, but "
                    f"{old.fact_id}.superseded_by is {old.temporal.superseded_by!r}"
                )
        if f.temporal.superseded_by:
            new = ledger.facts.get(f.temporal.superseded_by)
            if new and new.temporal.supersedes != f.fact_id:
                errors.append(
                    f"{f.fact_id} superseded_by {new.fact_id}, but "
                    f"{new.fact_id}.supersedes is {new.temporal.supersedes!r}"
                )

    # scope_ref must resolve AND agree with the fact's tier
    tier_scope_ok = {
        "personal": lambda r: r in ledger.personas,
        "team": lambda r: r in ledger.teams,
        "project": lambda r: r in ledger.projects,
        "org": lambda r: r == "org",
        "external": lambda r: r.startswith("external:"),
    }
    for f in ledger.facts.values():
        check = tier_scope_ok.get(f.tier)
        if check and not check(f.scope_ref):
            errors.append(
                f"{f.fact_id}: scope_ref {f.scope_ref!r} does not match "
                f"tier {f.tier!r}"
            )

    # supersession may only act at the superseded fact's tier or above
    # (spec §3: a decision supersedes conflicting facts at its tier and below)
    tier_rank = {"personal": 0, "external": 1, "team": 1, "project": 2, "org": 3}
    for f in ledger.facts.values():
        if f.temporal.supersedes:
            old = ledger.facts.get(f.temporal.supersedes)
            if old and tier_rank[f.tier] < tier_rank[old.tier]:
                errors.append(
                    f"{f.fact_id} ({f.tier}) cannot supersede "
                    f"{old.fact_id} ({old.tier}): lower tier"
                )

    if errors:
        raise LedgerValidationError(
            f"{len(errors)} validation error(s):\n" + "\n".join(f"  - {e}" for e in errors)
        )
