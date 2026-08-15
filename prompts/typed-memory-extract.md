# Typed-memory reference implementation — extraction prompt (v0.1, PROPOSED)

Status: draft alongside `docs/specs/typed-memory-reference.md`; frozen
(text hash recorded in the run manifest) before any pilot scoring. Used
verbatim by `membench.typed_memory.TypedMemoryAdapter`; the worker is the
pinned task model. `{event}` and `{existing}` are the only substitutions.

---

You maintain a typed organizational memory. Read ONE workspace event and
extract only durable, memory-worthy statements it establishes: policies,
rules, decisions, schedules/cadences, thresholds, owners, and stated personal
preferences. Ignore chatter, questions, speculation, and one-off logistics
that do not set a standing rule.

For each extracted statement produce a node:
- "kind": one of rule | decision | preference | schedule | fact | commitment
- "statement": one canonical sentence, present tense, self-contained
  (name the subject: company / team X / person Y).
- "tier": org | team | personal | project — the scope the statement binds.
- "scope_ref": "team:<name>" for team tier, "persona:<name>" for personal,
  null for org.
- "topic": a short lowercase slug (2-4 words joined by hyphens).
- "conflicts_with": ids from EXISTING NODES below whose statement this new
  statement REPLACES (same subject and attribute, different value). Empty
  list if none. Complementary statements do not conflict.

Rules: be conservative — if the event does not clearly establish a standing
statement, return an empty list. Never merge two facts into one node. Never
infer scope wider than the event states. Never restate an existing node
unchanged (return nothing for it).

EVENT:
{event}

EXISTING NODES ON THESE TOPICS (id: statement):
{existing}

Return ONLY a JSON array of node objects (possibly empty), no prose.
