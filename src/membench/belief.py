"""The expected belief state B(principal, t) and precedence resolution.

Pure functions over (Ledger, EventIndex) — the single scoring oracle for
memory-bench (Contract #1 §5, docs/specs/ledger-schema.md).

Semantics fixed here (normative; the spec defers these details to this module):

- t is an event index; "at t" means events with index <= t have occurred.
- valid_until_event is exclusive: the fact stops being valid AT that event
  (invalid for t >= index(valid_until_event)).
- Shared-surface witnessing does not require presence at publish time: a
  principal entitled to a surface at t witnesses all prior events on it
  (channel history is readable). Direct witnessing requires participation.
- Departed principals have empty belief states: once a persona leaves, their
  agent is decommissioned and B(pid, t) = ∅ — the benchmark never probes
  them. Sealing (A9) governs everyone else: after the owner leaves, a
  private personal-tier fact is excluded from every OTHER principal's B and
  B_hist.
"""

from __future__ import annotations

from dataclasses import dataclass

from .ledger import CAPACITIES, EventIndex, Fact, Ledger

_CAP_RANK = {c: i for i, c in enumerate(CAPACITIES)}


# ---------------------------------------------------------------- membership

def _joined(ledger: Ledger, index: EventIndex, pid: str, t: int) -> bool:
    p = ledger.personas[pid]
    return p.joins_at is None or index.index_of(p.joins_at) <= t


def _left(ledger: Ledger, index: EventIndex, pid: str, t: int) -> bool:
    p = ledger.personas[pid]
    return p.leaves_at is not None and index.index_of(p.leaves_at) <= t


def is_member(ledger: Ledger, index: EventIndex, pid: str, team_id: str, t: int) -> bool:
    """Team membership at t: on the roster, joined, and not departed."""
    team = ledger.teams.get(team_id)
    if team is None or pid not in team.members:
        return False
    return _joined(ledger, index, pid, t) and not _left(ledger, index, pid, t)


def _role_changed(ledger: Ledger, index: EventIndex, pid: str, t: int) -> bool:
    return any(index.index_of(ev) <= t for ev, _ in ledger.personas[pid].role_changes)


# ---------------------------------------------------------------- witnessing

def _witnessed(ledger: Ledger, index: EventIndex, fact: Fact, pid: str, t: int) -> bool:
    """Condition 1 of B: direct participation or shared-surface entitlement.

    A `distributed` fact is only knowable by composing all its fragments, so
    it requires every evidence event witnessed; other facts require any one.
    """
    if not _joined(ledger, index, pid, t) or _left(ledger, index, pid, t):
        return False
    witnessed_events = 0
    for ev_id in fact.evidence_events:
        ev_idx = index.index_of(ev_id)
        if ev_idx > t:
            continue
        ev = index.events[ev_idx]
        if (
            pid in ev.participants
            or ev.visibility == "org_public"
            or (
                ev.visibility == "team_confidential"
                and ev.team
                and is_member(ledger, index, pid, ev.team, t)
            )
        ):
            witnessed_events += 1
    if fact.explicitness == "distributed":
        return witnessed_events == len(fact.evidence_events)
    return witnessed_events > 0


# ---------------------------------------------------------------- visibility

def _scope_teams(ledger: Ledger, fact: Fact) -> tuple[str, ...]:
    if fact.scope_ref in ledger.teams:
        return (fact.scope_ref,)
    if fact.scope_ref in ledger.projects:
        return ledger.projects[fact.scope_ref].teams
    return ()


def _visible(ledger: Ledger, index: EventIndex, fact: Fact, pid: str, t: int) -> bool:
    """Condition 2 of B: the fact's visibility class permits this principal."""
    if fact.visibility == "org_public":
        return True
    if fact.visibility == "team_confidential":
        teams = _scope_teams(ledger, fact)
        if teams:
            return any(is_member(ledger, index, pid, tm, t) for tm in teams)
        # org- or persona-scoped confidential fact: direct witnesses only
        return _witnessed_directly(index, fact, pid, t)
    if fact.visibility == "need_to_know":
        acl = fact.visibility_acl or ()
        if pid in acl:
            return True
        return any(
            entry in ledger.teams and is_member(ledger, index, pid, entry, t)
            for entry in acl
        )
    if fact.visibility == "private":
        if pid == fact.author or pid == fact.scope_ref:
            return True
        return _witnessed_directly(index, fact, pid, t)
    return False


def _witnessed_directly(index: EventIndex, fact: Fact, pid: str, t: int) -> bool:
    return any(
        pid in index.events[index.index_of(ev)].participants
        for ev in fact.evidence_events
        if index.index_of(ev) <= t
    )


# ---------------------------------------------------------------- lifecycle

def _started(index: EventIndex, fact: Fact, t: int) -> bool:
    return index.index_of(fact.temporal.valid_from_event) <= t


def _expired(index: EventIndex, fact: Fact, t: int) -> bool:
    until = fact.temporal.valid_until_event
    return until is not None and index.index_of(until) <= t


def _superseded(ledger: Ledger, index: EventIndex, fact: Fact, t: int) -> bool:
    succ_id = fact.temporal.superseded_by
    if succ_id is None:
        return False
    succ = ledger.facts[succ_id]
    return index.index_of(succ.temporal.valid_from_event) <= t


def _decayed(ledger: Ledger, index: EventIndex, fact: Fact, t: int) -> bool:
    if fact.temporal.decay_class != "role_bound":
        return False
    return _left(ledger, index, fact.author, t) or _role_changed(
        ledger, index, fact.author, t
    )


def _sealed(ledger: Ledger, index: EventIndex, fact: Fact, pid: str, t: int) -> bool:
    """Private personal-tier facts of a departed persona are sealed to others."""
    if fact.tier != "personal" or fact.visibility != "private":
        return False
    owner = fact.scope_ref if fact.scope_ref in ledger.personas else fact.author
    return pid != owner and _left(ledger, index, owner, t)


# ---------------------------------------------------------------- B and B_hist

def belief_state(ledger: Ledger, index: EventIndex, pid: str, t: int) -> set[str]:
    """B(principal, t): fact ids that should drive the principal's behavior."""
    if pid not in ledger.personas:
        raise KeyError(f"unknown principal: {pid}")
    result = set()
    for fact in ledger.facts.values():
        if not _started(index, fact, t):
            continue
        if _expired(index, fact, t) or _superseded(ledger, index, fact, t):
            continue
        if _decayed(ledger, index, fact, t):
            continue
        if _sealed(ledger, index, fact, pid, t):
            continue
        if not _witnessed(ledger, index, fact, pid, t):
            continue
        if not _visible(ledger, index, fact, pid, t):
            continue
        result.add(fact.fact_id)
    return result


def belief_hist(ledger: Ledger, index: EventIndex, pid: str, t: int) -> set[str]:
    """B_hist(principal, t): superseded/expired facts still correct historically.

    A fact lands here if the principal would have held it (witnessed, visible,
    not sealed) but it has been superseded or has expired by t. Decayed
    role_bound facts also become historical rather than vanishing: the claim
    lost standing, but "X used to say this" remains true.
    """
    if pid not in ledger.personas:
        raise KeyError(f"unknown principal: {pid}")
    result = set()
    for fact in ledger.facts.values():
        if not _started(index, fact, t):
            continue
        ended = (
            _expired(index, fact, t)
            or _superseded(ledger, index, fact, t)
            or _decayed(ledger, index, fact, t)
        )
        if not ended:
            continue
        if _sealed(ledger, index, fact, pid, t):
            continue
        if not _witnessed(ledger, index, fact, pid, t):
            continue
        if not _visible(ledger, index, fact, pid, t):
            continue
        result.add(fact.fact_id)
    return result


# ---------------------------------------------------------------- precedence

@dataclass(frozen=True)
class ContextFrame:
    """The scope an artifact belongs to (probe spec `context_frame`)."""
    kind: str            # org_facing | team_internal | personal | project | external
    ref: str | None = None  # team/persona/project/client id where applicable


_FRAME_TIER = {
    "org_facing": "org",
    "team_internal": "team",
    "personal": "personal",
    "project": "project",
    "external": "external",
}


@dataclass(frozen=True)
class Resolution:
    winner: str | None          # fact id, or None when conflict
    conflict: bool
    survivors: tuple[str, ...]  # facts alive at the stage that decided the outcome


def resolve_precedence(
    ledger: Ledger,
    index: EventIndex,
    fact_ids: set[str] | list[str],
    frame: ContextFrame,
) -> Resolution:
    """Apply normative precedence rules 1-4 to conflicting, applicable facts.

    Callers pass facts already known to be in B and mutually conflicting;
    this function only ranks them.
    """
    facts = [ledger.facts[fid] for fid in fact_ids]
    if not facts:
        raise ValueError("resolve_precedence needs at least one fact")

    # Rule 1: highest capacity wins
    top = max(_CAP_RANK[f.capacity] for f in facts)
    facts = [f for f in facts if _CAP_RANK[f.capacity] == top]

    # Rule 2: tier matching the artifact's scope wins (contextual precedence)
    if len(facts) > 1:
        want_tier = _FRAME_TIER[frame.kind]

        def matches(f: Fact) -> bool:
            if f.tier != want_tier:
                return False
            return frame.ref is None or f.scope_ref == frame.ref

        matching = [f for f in facts if matches(f)]
        if matching:
            facts = matching

    # Rule 3: most recent valid_from wins
    if len(facts) > 1:
        latest = max(index.index_of(f.temporal.valid_from_event) for f in facts)
        facts = [
            f for f in facts
            if index.index_of(f.temporal.valid_from_event) == latest
        ]

    # Rule 4: still tied -> unresolved contradiction (A5); flag, don't pick
    survivors = tuple(sorted(f.fact_id for f in facts))
    if len(facts) == 1:
        return Resolution(winner=facts[0].fact_id, conflict=False, survivors=survivors)
    return Resolution(winner=None, conflict=True, survivors=survivors)
