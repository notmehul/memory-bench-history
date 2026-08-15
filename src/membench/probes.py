"""Contract #3 probe constructor (Phase 3, dataset-plan steps 1-2).

Expands the fact planner's probe plans into concrete probe instances and
assembles `probes.jsonl` per org. Every expanded instance is revalidated
against the belief oracle with the same rules gate G1 applies to the plan:
application/scope_resolution/staleness targets must be in B(principal, t),
historical targets in B_hist, must_not_use in B_hist, and A4 collisions
must resolve to the planner's expected winner under the declared frame.

Task text and assertions are authored by a content LLM against
prompts/probe-authoring.md; `apply_authored` merges them and enforces the
mechanical validators (probe-spec hygiene lint, pattern cross-validation
against canonical vs. counterfactual) so nothing the LLM writes is trusted
unchecked.

CLI:
  python -m membench.probes requests <org_dir> --out requests.json
  python -m membench.probes apply <org_dir> --authored authored.json
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass
from pathlib import Path

from .belief import ContextFrame, belief_hist, belief_state, resolve_precedence
from .ledger import EventIndex, Ledger, load_event_index, load_ledger

MIN_INSTANCES = 3
# Candidate offsets tried (in order) when a cluster needs more instances;
# spread out so staleness/historical instances sample distinct distances.
EXTRA_OFFSETS = (4, 9, 15, 22, 34, 50, 75, 110)
SERIES_METRICS = ("propagation_latency", "proactive_application")
ASSERTION_KINDS = (
    "fact_applied", "fact_absent", "constraint_followed",
    "conflict_flagged", "scope_correct", "unprompted_surface",
)
CHECKERS = ("pattern", "structural", "semantic")
TASK_WORDS = (15, 130)

_STOPWORDS = frozenset(
    ["a", "an", "and", "are", "as", "at", "be", "by", "for", "from", "has", "have",
     "in", "is", "it", "its", "of", "on", "or", "that", "the", "their", "there",
     "this", "to", "was", "were", "will", "with", "all", "any", "each", "every",
     "not", "no", "under", "over", "into", "out", "up", "down", "about", "after",
     "before", "during", "between", "within", "without"]
)


class ProbeConstructionError(Exception):
    pass


def _content_tokens(text: str) -> list[str]:
    toks = re.findall(r"[a-z0-9][a-z0-9$%./-]*", text.lower())
    return [t for t in toks if t not in _STOPWORDS]


def discriminative_tokens(canonical: str, counterfactual: str) -> set[str]:
    """Answer-bearing tokens: content words present in exactly one variant.

    Topic vocabulary (shared by both variants) stays usable in task text;
    only the tokens that distinguish base from twin are forbidden.
    """
    a, b = set(_content_tokens(canonical)), set(_content_tokens(counterfactual))
    return (a - b) | (b - a)


def _ngrams(tokens: list[str], n: int) -> set[tuple[str, ...]]:
    return {tuple(tokens[i:i + n]) for i in range(len(tokens) - n + 1)}


# ------------------------------------------------------------- expansion

@dataclass(frozen=True)
class ProbeInstance:
    probe_id: str
    principal: str
    offset: int
    inject_after_event: str


def _instance_ok(
    ledger: Ledger, index: EventIndex, plan: dict, principal: str, t: int
) -> bool:
    if t >= len(index.events):
        return False
    b = belief_state(ledger, index, principal, t)
    hist = belief_hist(ledger, index, principal, t)
    pool = hist if plan["kind"] == "historical" else b
    if any(fid not in pool for fid in plan["targets"]):
        return False
    if any(fid not in hist for fid in plan["must_not_use"]):
        return False
    if plan["expected_winner"]:
        frame = ContextFrame(plan["context_frame"]["kind"], plan["context_frame"]["ref"])
        res = resolve_precedence(ledger, index, list(plan["targets"]), frame)
        if res.winner != plan["expected_winner"]:
            return False
    return True


def expand_cluster(
    ledger: Ledger, index: EventIndex, plan: dict
) -> list[ProbeInstance]:
    """Deterministically grow a cluster to >=MIN_INSTANCES oracle-valid
    instances. Latency-series clusters vary offsets only (the series is
    per-principal by definition); scope_resolution prefers alternate
    principals (a genuinely different seat), staleness/historical prefer
    alternate offsets (distance is the metric's own dimension)."""
    anchor = index.index_of(plan["anchor_event"])
    principal = plan["principal"]
    series = plan["metric"] in SERIES_METRICS
    pairs: list[tuple[str, int]] = [(principal, off) for off in plan["offset_events"]]

    def try_offsets() -> None:
        for off in EXTRA_OFFSETS:
            if len(pairs) >= MIN_INSTANCES:
                return
            if any(p == principal and o == off for p, o in pairs):
                continue
            if _instance_ok(ledger, index, plan, principal, anchor + off):
                pairs.append((principal, off))

    def try_principals() -> None:
        for pid in sorted(ledger.personas):
            if len(pairs) >= MIN_INSTANCES:
                return
            if pid == principal:
                continue
            for off in plan["offset_events"]:
                if _instance_ok(ledger, index, plan, pid, anchor + off):
                    pairs.append((pid, off))
                    break

    if series or plan["kind"] in ("staleness", "historical"):
        try_offsets()
        if not series:
            try_principals()
    else:
        try_principals()
        try_offsets()

    if len(pairs) < MIN_INSTANCES:
        raise ProbeConstructionError(
            f"{plan['probe_plan_id']}: only {len(pairs)} valid instances found"
        )
    return [
        ProbeInstance(
            probe_id=f"{plan['probe_plan_id']}-{i + 1:02d}",
            principal=pid,
            offset=off,
            inject_after_event=index.events[anchor + off].event_id,
        )
        for i, (pid, off) in enumerate(pairs)
    ]


# ------------------------------------------------------ authoring requests

def _persona_view(org: dict, pid: str) -> dict:
    p = next(x for x in org["entities"]["personas"] if x["id"] == pid)
    return {
        "id": pid,
        "name": pid.split(":", 1)[1].capitalize(),
        "role": p["role"],
        "teams": p["teams"],
        "voice_profile": p["voice_profile"],
    }


def _fact_view(raw: dict) -> dict:
    cf = raw.get("counterfactual")
    return {
        "fact_id": raw["fact_id"],
        "canonical": raw["canonical"],
        "counterfactual": cf["canonical"] if cf else None,
        "type": raw["type"],
        "tier": raw["tier"],
        "scope_ref": raw["scope_ref"],
        "capacity": raw["capacity"],
        "topic": raw["topic"],
    }


def cluster_forbidden_tokens(facts: list[dict]) -> list[str]:
    """Hygiene blacklist for one cluster: the union of answer-bearing
    tokens across every target/must_not_use fact that has a twin variant."""
    banned: set[str] = set()
    for f in facts:
        if f["counterfactual"]:
            banned |= discriminative_tokens(f["canonical"], f["counterfactual"])
    return sorted(banned)


def build_requests(org: dict, plan_doc: dict) -> list[dict]:
    raw_facts = {f["fact_id"]: f for f in org["facts"]}
    out = []
    for plan in plan_doc["probe_plans"]:
        targets = [_fact_view(raw_facts[fid]) for fid in plan["targets"]]
        mnu = [_fact_view(raw_facts[fid]) for fid in plan["must_not_use"]]
        out.append({
            "cluster_id": plan["probe_plan_id"],
            "archetype": plan["archetype"],
            "kind": plan["kind"],
            "metric": plan["metric"],
            "principal": _persona_view(org, plan["principal"]),
            "context_frame": plan["context_frame"],
            "org_id": org["org_id"],
            "targets": targets,
            "must_not_use": mnu,
            "expected_winner": plan["expected_winner"],
            "forbidden_tokens": cluster_forbidden_tokens(targets + mnu),
        })
    return out


# ----------------------------------------------------- authored validation

def _pattern_hits(pattern: str, text: str) -> bool:
    return re.search(pattern, text, re.IGNORECASE | re.DOTALL) is not None


_NUM_WORDS = {
    "1": "one", "2": "two", "3": "three", "4": "four", "5": "five",
    "6": "six", "7": "seven", "8": "eight", "9": "nine", "10": "ten",
    "11": "eleven", "12": "twelve", "13": "thirteen", "14": "fourteen",
    "15": "fifteen", "16": "sixteen", "17": "seventeen", "18": "eighteen",
    "19": "nineteen", "20": "twenty", "24": "twenty-four", "30": "thirty",
    "36": "thirty-six", "45": "forty-five", "48": "forty-eight",
    "60": "sixty", "72": "seventy-two", "90": "ninety", "96": "ninety-six",
}
_WORD_NUMS = {w: d for d, w in _NUM_WORDS.items()}


def surface_variants(text: str) -> list[str]:
    """The fact text plus numeral<->word rewrites ('fifteen minutes' /
    '15 minutes'). A deliverable may use either form, so an assertion
    pattern must match every variant of its own side."""
    def swap(t: str, table: dict[str, str]) -> str:
        # Longest keys first so 'seventy-two' wins over 'two'; hyphen
        # lookarounds keep fragments of unknown compounds intact.
        keys = sorted(table, key=len, reverse=True)
        return re.sub(
            r"(?<![\w-])(" + "|".join(map(re.escape, keys)) + r")(?![\w-])",
            lambda m: table[m.group(1).lower()],
            t,
            flags=re.IGNORECASE,
        )
    variants = {text, swap(text, _NUM_WORDS), swap(text, _WORD_NUMS)}
    return sorted(variants)


# ------------------------------------- v0.4: commitment rule & cross-side

def _side_exclusive_tokens(own: str, other: str) -> list[str]:
    return sorted(set(_content_tokens(own)) - set(_content_tokens(other)))


def _num_pair(tok: str) -> tuple[str | None, str | None]:
    """(digit_form, word_form) when `tok` is a numeral or number-word."""
    if re.fullmatch(r"\d+", tok):
        return tok, _NUM_WORDS.get(tok)
    if tok in _WORD_NUMS:
        return _WORD_NUMS[tok], tok
    return None, None


def _unit_after(tok: str, text: str) -> str | None:
    m = re.search(
        rf"(?<![\w-]){re.escape(tok)}(?![\w-])[\s-]*([a-z]+)",
        text, re.IGNORECASE,
    )
    if not m:
        return None
    unit = m.group(1).lower()
    if unit in _STOPWORDS or len(unit) < 3:
        return None
    return unit


_VALUE_WORDS = frozenset(
    ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday",
     "sunday", "mondays", "tuesdays", "wednesdays", "thursdays", "fridays",
     "saturdays", "sundays", "daily", "weekly", "biweekly", "fortnightly",
     "monthly", "quarterly", "annually", "yearly", "hourly", "noon",
     "midnight"]
)


def _is_value_token(tok: str, own: str) -> bool:
    """A token qualifies as a VALUE anchor, never a phrasing word.

    Value classes (spec v0.4.4 — anchors must be invariant, never common
    words): contains a digit / $ / %; hyphenated compound ("kebab-case");
    calendar and cadence vocabulary; or a mixed-case identifier in the
    canonical's original casing ("camelCase", "LaunchDarkly")."""
    if re.search(r"[\d$%]", tok) or "-" in tok:
        return True
    if tok in _VALUE_WORDS or tok in _WORD_NUMS:
        return True
    m = re.search(rf"(?<![\w-])({re.escape(tok)})(?![\w-])", own, re.IGNORECASE)
    if m:
        span = m.group(1)
        if re.search(r"[a-z][A-Z]", span):  # internal case transition
            return True
    return False


_DURATION_UNITS = frozenset(["minute", "hour", "day", "week", "month"])


def _lemma(word: str) -> str:
    """Naive s/es-strip (v0.4 refinement R2)."""
    w = word.lower()
    if w.endswith("es") and len(w) > 4:
        return w[:-2]
    if w.endswith("s") and len(w) > 3:
        return w[:-1]
    return w


def _standalone_number(digit: str, text: str) -> bool:
    """R5: the digit form must appear as a standalone number in the
    canonical — never as a comma/period fragment of a larger figure
    (the `(?:000|two)` bug class)."""
    return re.search(
        rf"(?<![\w,.\-]){re.escape(digit)}(?![\w,.\-])", text
    ) is not None


_CAL_RE = re.compile(r"\b(\d{1,2}(?::\d{2})?\s?(?:am|pm)|noon|midnight)\b", re.I)


def _value_classes(text: str) -> set[str]:
    """Which contestable value classes a side's text carries (R6)."""
    toks = {t.lower() for t in re.findall(r"[A-Za-z0-9$%:.,'-]+", text)}
    classes = set()
    if toks & _VALUE_WORDS or _CAL_RE.search(text):
        classes.add("cal")
    if "$" in text:
        classes.add("money")
    if "%" in text or re.search(r"\bpercent\b", text, re.I):
        classes.add("pct")
    return classes


def _anchor_class(branch: str, tok: str) -> str | None:
    tl = tok.lower()
    if tl in _VALUE_WORDS or _CAL_RE.fullmatch(tok):
        return "cal"
    if branch.startswith("\\$"):
        return "money"
    if "%" in tok or "percent" in tl:
        return "pct"
    return None


def side_value_anchors(own: str, other: str) -> list[str]:
    """Regex branches identifying OWN side's distinctive VALUES.

    R6 (2026-08-15, contested-attribute rule; evidence: seed-3 P-0041 twin
    outputs "cannot wait until Monday" hit a base-side day-name detector
    on a no-freeze twin): a calendar/time-of-day, money or percent anchor
    is emitted only when the OTHER side's text also carries a value of
    that class — i.e. the attribute is contested between the sides. When
    a class appears on one side only (retraction or attribute-less twin),
    hunting it punishes any incidental use of that vocabulary.

    Spec v0.4 rules 2 and 4, refined 2026-08-07 (R1/R2/R5 from flip
    adjudication):
    - R1: duration-class branches (number + minute/hour/day/week/month)
      are banned — durations are generic ops vocabulary that honest
      artifacts reinvent constantly; valid anchors are money, %,
      day-names/cadence words, unitless counts WITH object nouns,
      hyphenated compounds, and mixed-case identifiers.
    - R2: a plain-word anchor whose naive lemma appears in the other
      side's text is skipped (monday vs mondays inflection degeneracy).
    - R5: no digit-only fragments of larger figures; no unit-less bare
      number-words. Bare 1-2 digit numerals still require a unit anchor.
    """
    other_lemmas = {_lemma(t) for t in _content_tokens(other)}
    branches: list[str] = []
    for tok in _side_exclusive_tokens(own, other):
        digit, word = _num_pair(tok)
        if digit is not None:
            unit = _unit_after(tok, own)
            if unit and unit.lower().rstrip("s") in _DURATION_UNITS:
                continue  # R1: duration anchors banned
            alt = f"(?:{digit}|{word})" if word else digit
            if len(digit) >= 3:
                if not _standalone_number(digit, own):
                    continue  # R5: no fragments of larger figures
                if re.search(rf"\$\s?{re.escape(digit)}", own):
                    branches.append(rf"\$\s?{digit}")  # money anchor
                elif unit:
                    stem = re.escape(unit.rstrip("s"))
                    branches.append(rf"{alt}[\s-]+{stem}\w*")
                # R5: a long digit with neither $ nor unit is dropped —
                # bare numerals are never branches, whatever their length
                continue
            if unit:
                stem = re.escape(unit.rstrip("s"))
                branches.append(rf"{alt}[\s-]+{stem}\w*")
            # R5: unit-less bare number-words are banned; a bare 1-2
            # digit numeral without a unit anchor is likewise dropped.
        elif not _is_value_token(tok, own):
            continue
        elif re.search(r"\d", tok):
            if len(tok) >= 3 and _standalone_number(tok, own):
                branches.append(re.escape(tok))  # fused: "5,000", "2pm"
        elif len(tok) >= 3:
            if _lemma(tok) in other_lemmas:
                continue  # R2: inflection-degenerate anchor
            branches.append(re.escape(tok))
    other_classes = _value_classes(other)
    kept = []
    for b in branches:
        tok = re.sub(r"\\(.)", r"\1", b).split("[")[0].strip("(?:)")
        cls = _anchor_class(b, tok)
        if cls is not None and cls not in other_classes:
            continue  # R6: uncontested attribute class
        kept.append(b)
    return sorted(set(kept))


def anchors_pattern(branches: list[str]) -> str | None:
    if not branches:
        return None
    return r"(?<![\w-])(?:" + "|".join(branches) + r")(?![\w-])"


def build_side_patterns(
    base_facts: dict[str, str],
    twin_facts: dict[str, str],
    delta_ids: list[str],
    foreign: list[tuple[str, str]],
) -> tuple[str | None, str | None, list[str]]:
    """(base_pattern, cf_pattern, notes) for one paired probe.

    base_pattern matches BASE-side distinctive values (used by `casrt-cs`
    and by the commitment rule); cf_pattern matches CF-side values (used
    by `asrt-cs`). Branches that hit any own-side surface variant or any
    `foreign` co-valid canonical are pruned (detectors target the twin
    delta only — never nested co-valid constraints). A side whose pruned
    pattern no longer covers every one of its full-text surface variants
    is returned as None with an explanatory note: no silent weakening.
    """
    notes: list[str] = []

    def one_side(own_key: str) -> str | None:
        own_map, other_map = (
            (base_facts, twin_facts) if own_key == "base"
            else (twin_facts, base_facts)
        )
        pairs = [(own_map[d], other_map[d]) for d in delta_ids
                 if d in own_map and d in other_map]
        if not pairs:
            notes.append(f"{own_key}: no delta fact pair available")
            return None
        branches: list[str] = []
        for own_text, other_text in pairs:
            branches += side_value_anchors(own_text, other_text)
        own_variants = [v for own_text, _ in pairs
                        for v in surface_variants(own_text)]
        other_variants = [v for _, other_text in pairs
                          for v in surface_variants(other_text)]
        kept = []
        for b in sorted(set(branches)):
            pat = anchors_pattern([b])
            if any(_pattern_hits(pat, v) for v in other_variants):
                notes.append(f"{own_key}: branch '{b}' hits other side; pruned")
                continue
            hit = next((n for n, t in foreign if _pattern_hits(pat, t)), None)
            if hit is not None:
                notes.append(f"{own_key}: branch '{b}' hits co-valid {hit}; pruned")
                continue
            kept.append(b)
        pattern = anchors_pattern(kept)
        if pattern is None:
            notes.append(f"{own_key}: no valid branches survive")
            return None
        missed = [v for v in own_variants if not _pattern_hits(pattern, v)]
        if missed:
            notes.append(
                f"{own_key}: pattern misses variant '{missed[0][:60]}'")
            return None
        return pattern

    return one_side("base"), one_side("cf"), notes


_NEGATORS = re.compile(
    r"\b(?:no|not|never|without|don'?t|doesn'?t|do\s+not|does\s+not|"
    r"stopped|skips?|skipped|omits?|omitted)\b"
    r"|\bno\s+longer\b|\brather\s+than\b|\binstead\s+of\b",
    re.IGNORECASE,
)
_SENTENCE_BOUNDARY = re.compile(r"[.!?;\n]")


def pattern_hits_unnegated(pattern: str, text: str) -> bool:
    """v0.4 refinement R4 (negation-window guard): a match is suppressed
    when a negator precedes it within the same sentence at <=12 tokens —
    mentioning the other side's value in order to NEGATE it ("there is no
    Monday session") is committed behavior, not hedging. Suppression only
    spares absence detectors; a negated mention still cannot satisfy the
    side's affirmative fact_applied criteria."""
    if not pattern or not text:
        return False
    norm = text.replace("’", "'")
    for m in re.finditer(pattern, norm, re.IGNORECASE | re.DOTALL):
        before = norm[: m.start()]
        cut = 0
        b = _SENTENCE_BOUNDARY.search(before)
        while b:
            cut = b.end()
            b = _SENTENCE_BOUNDARY.search(before, b.end())
        window = " ".join(before[cut:].split()[-12:])
        if not _NEGATORS.search(window):
            return True
    return False


def is_hedged(
    output: str, base_pattern: str | None, cf_pattern: str | None
) -> bool:
    """Commitment rule (spec v0.4.1, R4-guarded): an output asserting the
    distinctive values of BOTH sides of a paired probe is non-committal.
    Negated mentions do not count as assertions (R4); probes with
    kind=historical are exempt upstream — no patterns are embedded for
    them (R3)."""
    if not output or not base_pattern or not cf_pattern:
        return False
    return (pattern_hits_unnegated(base_pattern, output)
            and pattern_hits_unnegated(cf_pattern, output))


def _check_assertion(
    a: dict, facts: dict[str, dict], side: str, winner: str | None
) -> list[str]:
    """Validate one authored assertion. `side` is 'base' or 'twin': on the
    twin org every fact with a counterfactual reads as its twin variant, so
    patterns must discriminate against the *other* side's text."""
    errs = []
    aid = str(a.get("id", ""))
    if aid.endswith("-cs") or aid.endswith("-css"):
        # Mechanically generated cross-side detectors (spec v0.4 rule 2 /
        # v0.4.3 semantic fallback): they hunt the OTHER side's values and
        # carry no fact_id, so the fact-relative checks below do not apply
        # — the generator validated them against both orgs' variant sets.
        want = "pattern" if aid.endswith("-cs") else "semantic"
        if a.get("kind") != "fact_absent" or a.get("checker") != want:
            errs.append(f"{aid}: cross-side detectors must be fact_absent/{want}")
        if not isinstance(a.get("weight"), (int, float)) or a["weight"] <= 0:
            errs.append(f"{aid}: weight must be positive")
        if want == "pattern":
            try:
                re.compile(a.get("criterion") or "", re.IGNORECASE)
            except re.error as e:
                errs.append(f"{aid}: bad regex ({e})")
        elif "does not present" not in (a.get("criterion") or ""):
            errs.append(f"{aid}: semantic detector must use the fixed template")
        return errs
    for key in ("id", "kind", "fact_id", "checker", "criterion"):
        if not a.get(key):
            errs.append(f"assertion missing {key}")
            return errs
    if a["kind"] not in ASSERTION_KINDS:
        errs.append(f"{a['id']}: unknown kind {a['kind']}")
    if a["checker"] not in CHECKERS:
        errs.append(f"{a['id']}: unknown checker {a['checker']}")
    fact = facts.get(a["fact_id"])
    if fact is None:
        errs.append(f"{a['id']}: fact {a['fact_id']} not in cluster")
        return errs
    if not isinstance(a.get("weight"), (int, float)) or a["weight"] <= 0:
        errs.append(f"{a['id']}: weight must be positive")
    if a["kind"] == "fact_absent" and a["fact_id"] == winner:
        errs.append(f"{a['id']}: fact_absent may not target the expected winner")

    if a["checker"] != "pattern":
        # Semantic verdicts are never inverted by the scorer, so a
        # fact_absent criterion must itself be an absence statement.
        if a["kind"] == "fact_absent" and not re.search(
            r"\b(not|no|never|without|omit|absent)\b", a["criterion"], re.IGNORECASE
        ):
            errs.append(
                f"{a['id']}: semantic fact_absent criterion must be phrased "
                "as an absence statement ('does not …')"
            )
        return errs
    # Seed-1 screening measured applied-content patterns failing 39-42% of
    # ceiling runs (deliverables paraphrase around any anchor) vs 4% for
    # absence detectors: patterns are for fact_absent only.
    if a["kind"] != "fact_absent":
        errs.append(
            f"{a['id']}: pattern checkers are reserved for fact_absent "
            "detectors — applied-content assertions must be semantic"
        )
        return errs
    try:
        re.compile(a["criterion"], re.IGNORECASE)
    except re.error as e:
        errs.append(f"{a['id']}: bad regex ({e})")
        return errs
    if re.search(r"\.\s*[*+]", a["criterion"]):
        errs.append(
            f"{a['id']}: '.*'/'.+' conjunctions are banned (order/adjacency "
            "brittle) — use one surface form per assertion, alternations for "
            "synonyms, and multiple assertions for multiple required elements"
        )
    if a["criterion"].count("\\s") + a["criterion"].count(" ") > 4:
        errs.append(
            f"{a['id']}: pattern spans too many words — anchor on the "
            "minimal discriminating span (number+unit or key term), not the "
            "canonical's phrasing; paraphrased deliverables will not "
            "reproduce long word runs"
        )
    def text_of(f: dict, s: str) -> str:
        if s == "twin" and f["counterfactual"]:
            return f["counterfactual"]
        return f["canonical"]

    # Pattern checkers are reserved for invariant surface forms (probe-spec
    # section 2): a deliverable paraphrases everything else, so a pattern
    # must contain a number/symbol/day name, or hit an identifier-like
    # token (hyphenated, digit-bearing, mixed-case) of its own-side text.
    invariant = re.search(
        r"\d|\$|%|[A-Za-z]+-[A-Za-z?]+|"
        r"\b(one|two|three|four|five|six|seven|eight|nine|ten|eleven|twelve|"
        r"fifteen|twenty|thirty|sixty|ninety|monday|tuesday|wednesday|"
        r"thursday|friday|saturday|sunday)\b",
        a["criterion"], re.IGNORECASE,
    ) or any(
        _pattern_hits(a["criterion"], tok)
        and re.search(r"\d|-|[a-z][A-Z]", tok)
        for tok in re.findall(r"[A-Za-z0-9$%/.-]+", text_of(fact, side))
    )
    if not invariant:
        errs.append(
            f"{a['id']}: pattern has no invariant token (number, symbol, "
            "identifier, day name) — plain-word content gets paraphrased; "
            "use checker 'semantic' instead"
        )

    own = text_of(fact, side)
    other = fact["counterfactual"] if side == "base" else fact["canonical"]
    # A deliverable may render numbers as digits or words: the pattern must
    # hit every surface variant of its own side (forcing e.g. (fifteen|15))
    # and no variant of the other side.
    for v in surface_variants(own):
        if not _pattern_hits(a["criterion"], v):
            errs.append(
                f"{a['id']}: pattern misses the {side}-side variant {v!r}"
            )
    if fact["counterfactual"] and other:
        for v in surface_variants(other):
            if _pattern_hits(a["criterion"], v):
                errs.append(
                    f"{a['id']}: pattern also matches the "
                    f"{'twin' if side == 'base' else 'base'} variant {v!r} "
                    "— not discriminative"
                )
    # A pattern asserting one fact must not fire on a *different* cluster
    # fact's text (false positives corrupt fact_absent scoring).
    for fid, f in facts.items():
        if fid == a["fact_id"]:
            continue
        if _pattern_hits(a["criterion"], text_of(f, side) or ""):
            errs.append(f"{a['id']}: pattern also matches {fid} on the {side} side")
    return errs


def validate_authored_cluster(req: dict, authored: dict) -> list[str]:
    errs: list[str] = []
    task = authored.get("task") or ""
    words = task.split()
    if not (TASK_WORDS[0] <= len(words) <= TASK_WORDS[1]):
        errs.append(f"task length {len(words)} words outside {TASK_WORDS}")

    # Hygiene lint (probe-spec section 6): no answer-bearing token, no
    # 4-gram of content words shared with any fact variant.
    task_tokens = _content_tokens(task)
    banned = set(req["forbidden_tokens"])
    leaked = sorted(set(task_tokens) & banned)
    if leaked:
        errs.append(f"task leaks answer tokens: {leaked}")
    task_grams = _ngrams(task_tokens, 4)
    for f in req["targets"] + req["must_not_use"]:
        for variant in (f["canonical"], f["counterfactual"]):
            if variant and task_grams & _ngrams(_content_tokens(variant), 4):
                errs.append(f"task shares a 4-gram with {f['fact_id']}")

    facts = {f["fact_id"]: f for f in req["targets"] + req["must_not_use"]}
    winner = req["expected_winner"]
    assertions = authored.get("assertions") or []
    if not assertions:
        errs.append("no assertions")
    ids = [a.get("id") for a in assertions]
    if len(ids) != len(set(ids)):
        errs.append("duplicate assertion ids")
    for a in assertions:
        errs += _check_assertion(a, facts, "base", winner)

    # Twin side: required whenever any target carries a counterfactual.
    deltas = [f["fact_id"] for f in req["targets"] if f["counterfactual"]]
    cf_assertions = authored.get("counterfactual_assertions") or []
    if deltas and not cf_assertions:
        errs.append("counterfactual_assertions required (targets have twins)")
    for a in cf_assertions:
        errs += _check_assertion(a, facts, "twin", winner)
    return errs


# ------------------------------------------------------------- emission

def build_probes(
    org: dict, plan_doc: dict, authored_by_cluster: dict[str, dict]
) -> tuple[list[dict], dict[str, list[str]]]:
    """Returns (probe records, {cluster_id: errors}). Records are emitted
    only when every cluster validates — a partially-authored probe file is
    never written."""
    ledger = load_ledger(org)
    index = load_event_index(org)
    requests = {r["cluster_id"]: r for r in build_requests(org, plan_doc)}
    errors: dict[str, list[str]] = {}
    records: list[dict] = []

    for plan in plan_doc["probe_plans"]:
        cid = plan["probe_plan_id"]
        authored = authored_by_cluster.get(cid)
        if authored is None:
            errors[cid] = ["not authored"]
            continue
        errs = validate_authored_cluster(requests[cid], authored)
        if errs:
            errors[cid] = errs
            continue
        instances = expand_cluster(ledger, index, plan)
        series = plan["metric"] in SERIES_METRICS
        offsets = sorted({i.offset for i in instances})
        deltas = [
            f["fact_id"] for f in requests[cid]["targets"] if f["counterfactual"]
        ]
        for inst in instances:
            records.append({
                "probe_id": inst.probe_id,
                "cluster_id": cid,
                "archetype": plan["archetype"],
                "archetype_instance": plan["archetype_instance"],
                "kind": plan["kind"],
                "principal": inst.principal,
                "inject_after_event": inst.inject_after_event,
                "context_frame": plan["context_frame"],
                "task": authored["task"],
                "modality": authored.get("modality", "document"),
                "targets": plan["targets"],
                "must_not_use": plan["must_not_use"],
                "assertions": authored["assertions"],
                "counterfactual_probe": (
                    {
                        "ledger_deltas": deltas,
                        "assertions": authored["counterfactual_assertions"],
                    }
                    if deltas else None
                ),
                "judge_rubric": None,
                "metrics": [plan["metric"]],
                "latency_series": (
                    {"offsets_events": offsets, "metric": plan["metric"]}
                    if series else None
                ),
            })
    return records, errors


# ------------------------------------------------------------------ CLI

def _load(path: Path) -> dict:
    return json.loads(path.read_text())


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="membench.probes")
    sub = ap.add_subparsers(dest="cmd", required=True)
    p_req = sub.add_parser("requests")
    p_req.add_argument("org_dir", type=Path)
    p_req.add_argument("--out", type=Path, required=True)
    p_app = sub.add_parser("apply")
    p_app.add_argument("org_dir", type=Path)
    p_app.add_argument("--authored", type=Path, required=True)
    args = ap.parse_args(argv)

    org = _load(args.org_dir / "org.json")
    plan_doc = _load(args.org_dir / "plan.json")

    if args.cmd == "requests":
        reqs = build_requests(org, plan_doc)
        args.out.write_text(json.dumps(reqs, indent=1))
        print(f"{len(reqs)} authoring requests -> {args.out}")
        return 0

    authored_doc = _load(args.authored)
    by_cluster = {c["cluster_id"]: c for c in authored_doc["clusters"]}
    records, errors = build_probes(org, plan_doc, by_cluster)
    if errors:
        err_path = args.org_dir / "probe-authoring-errors.json"
        err_path.write_text(json.dumps(errors, indent=1))
        print(f"{len(errors)} clusters failed validation -> {err_path}", file=sys.stderr)
        return 3
    out = args.org_dir / "probes.jsonl"
    with out.open("w") as fh:
        for r in records:
            fh.write(json.dumps(r) + "\n")
    print(f"{len(records)} probe instances -> {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
