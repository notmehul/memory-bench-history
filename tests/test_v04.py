"""Probe-spec v0.4: commitment rule and cross-side detector generation."""

import importlib.util
import json
import sys
from pathlib import Path

from membench.probes import (
    anchors_pattern,
    build_side_patterns,
    is_hedged,
    side_value_anchors,
)

ROOT = Path(__file__).resolve().parents[1]


def _load_script(name):
    why = CONSTRUCTION if name == "add_cross_detectors" else "missing script"
    spec = importlib.util.spec_from_file_location(
        name, require(f"scripts/{name}.py", why))
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


BASE = "Deploy reviews happen on Monday with 2 approvals."
CF = "Deploy reviews happen on Friday with 6 approvals."


def test_anchors_no_bare_short_numerals():
    for own, other in ((BASE, CF), (CF, BASE)):
        for b in side_value_anchors(own, other):
            assert b not in {str(n) for n in range(100)}, b


def test_anchors_number_word_and_unit():
    cf_anchors = side_value_anchors(CF, BASE)
    pat = anchors_pattern(cf_anchors)
    assert pat is not None
    # must hit both numeral and word surface forms, unit-anchored
    assert is_hedged("needs 6 approvals now", pat, pat)
    assert is_hedged("needs six approvals now", pat, pat)
    # bare "6" without the unit must NOT fire
    assert not is_hedged("section 6 covers retros", pat, pat)


def test_is_hedged_requires_both_sides():
    b_pat = anchors_pattern(side_value_anchors(BASE, CF))
    c_pat = anchors_pattern(side_value_anchors(CF, BASE))
    committed = "Reviews run Monday with 2 approvals."
    hedging = "Reviews run Monday or Friday, whichever applies."
    assert not is_hedged(committed, b_pat, c_pat)
    assert is_hedged(hedging, b_pat, c_pat)
    assert not is_hedged(hedging, None, c_pat)  # uncoverable side -> never


def test_hedged_word_boundaries():
    base = "Paths use kebab-case names."
    cf = "Paths use camelCase names."
    b_pat = anchors_pattern(side_value_anchors(base, cf))
    c_pat = anchors_pattern(side_value_anchors(cf, base))
    assert is_hedged("use kebab-case or camelCase", b_pat, c_pat)
    # embedded in a longer word: guarded, must not fire
    assert not is_hedged("kebab-cased camelCased", b_pat, c_pat)


def test_build_side_patterns_prunes_foreign_and_reports_uncoverable():
    base_facts = {"F-1": BASE}
    twin_facts = {"F-1": CF}
    # foreign text containing the base value: branch pruned -> base side
    # uncoverable -> None with a note
    foreign = [("base:F-9", "The handbook already says Monday with 2 approvals.")]
    b_pat, c_pat, notes = build_side_patterns(
        base_facts, twin_facts, ["F-1"], foreign)
    assert b_pat is None
    assert any("co-valid" in n for n in notes)
    assert c_pat is not None


def test_scorer_hedged_fails_applied_keeps_absence():
    sp = _load_script("screen_probes")
    assertions = [
        {"id": "a1", "kind": "fact_applied", "checker": "semantic",
         "criterion": "states the cadence", "weight": 1.0},
        {"id": "a2", "kind": "fact_absent", "checker": "pattern",
         "criterion": r"(?<![\w-])camelcase(?![\w-])", "weight": 1.0},
    ]
    verdicts = {"a1": True}
    out = "kebab-case everywhere"
    assert sp._score("r", assertions, out, verdicts) == 1.0
    # hedged: applied fails even with a passing verdict; absence still scores
    assert sp._score("r", assertions, out, verdicts, hedged=True) == 0.5
    # hedged + absence violated -> 0
    assert sp._score("r", assertions, "camelCase too", verdicts,
                     hedged=True) == 0.0


def test_add_detectors_idempotent_and_valid():
    acd = _load_script("add_cross_detectors")
    probe = {
        "probe_id": "P-X-01", "targets": ["F-1"],
        "assertions": [
            {"id": "asrt-1", "kind": "fact_applied", "checker": "semantic",
             "criterion": "states the window", "weight": 1.0}],
        "counterfactual_probe": {
            "ledger_deltas": ["F-1"],
            "assertions": [
                {"id": "casrt-1", "kind": "fact_applied",
                 "checker": "semantic", "criterion": "states the window",
                 "weight": 1.0}]},
    }
    base_canon = {"F-1": BASE}
    twin_canon = {"F-1": CF}
    r1 = acd.add_detectors(probe, base_canon, twin_canon, [])
    snap1 = json.dumps(probe, sort_keys=True)
    r2 = acd.add_detectors(probe, base_canon, twin_canon, [])
    snap2 = json.dumps(probe, sort_keys=True)
    assert snap1 == snap2, "not idempotent"
    assert r1["added"] == r2["added"] == ["asrt-cs", "casrt-cs"]
    asrt_cs = [a for a in probe["assertions"] if a["id"] == "asrt-cs"][0]
    # base-side detector hunts CF values, not base values
    import re
    assert re.search(asrt_cs["criterion"], "moved to Friday",
                     re.IGNORECASE | re.DOTALL)
    assert not re.search(asrt_cs["criterion"], "Monday with 2 approvals",
                         re.IGNORECASE | re.DOTALL)


def test_manifest_prompts_unchanged_by_v04(tmp_path):
    """Hedge fields are additive: prompts must stay byte-identical to the
    committed seed-1 manifest."""
    require_ledger()
    sp = _load_script("screen_probes")
    from types import SimpleNamespace
    work = tmp_path / "wd"
    sp.cmd_manifest(SimpleNamespace(
        org_dir=ROOT / "datasets/dev/org-00001",
        twin_dir=ROOT / "datasets/dev/org-00001-twin",
        work_dir=work))
    new = {json.loads(x)["run_id"]: json.loads(x)
           for x in (work / "runs.jsonl").read_text().splitlines()}
    committed = {json.loads(x)["run_id"]: json.loads(x)
                 for x in (ROOT / "datasets/dev/screening/org-00001/runs.jsonl"
                           ).read_text().splitlines()}
    assert set(new) == set(committed)
    assert all(new[r]["prompt"] == committed[r]["prompt"] for r in new)
    # and every paired row carries the hedge fields
    assert all("hedge_base" in new[r] for r in new)
    # R3: historical probes carry no hedge patterns
    kinds = {}
    for line in (ROOT / "datasets/dev/org-00001/probes.jsonl"
                 ).read_text().splitlines():
        prb = json.loads(line)
        kinds[prb["probe_id"]] = prb.get("kind")
    for row in new.values():
        if kinds[row["probe_id"]] == "historical":
            assert row["hedge_base"] is None and row["hedge_cf"] is None


# ------------------------- v0.4 refinements R1-R5 (2026-08-07)

from conftest import CONSTRUCTION, require, require_ledger  # noqa: E402

from membench.probes import pattern_hits_unnegated  # noqa: E402


def test_r1_duration_anchors_banned():
    assert side_value_anchors(
        "escalate within 30 minutes", "escalate within 2 hours") == []
    assert side_value_anchors(
        "retire flags after 90 days", "retire flags after 26 weeks") == []
    # non-duration unit survives
    assert side_value_anchors(
        "needs 2 approvals", "needs 6 approvals") != []


def test_r2_lemma_inflection_guard():
    # twin's own canonical contains "Mondays"; base anchor "monday" must
    # be skipped for the detector guarding the twin side
    assert side_value_anchors(
        "Triage happens every Monday.", "Triage skips Mondays entirely.") == []


def test_r3_historical_probes_get_no_detectors():
    acd = _load_script("add_cross_detectors")
    probe = {
        "probe_id": "P-H-01", "kind": "historical", "targets": ["F-1"],
        "assertions": [
            {"id": "asrt-1", "kind": "fact_applied", "checker": "semantic",
             "criterion": "x", "weight": 1.0},
            {"id": "asrt-cs", "kind": "fact_absent", "checker": "pattern",
             "criterion": "stale", "weight": 1.0}],
        "counterfactual_probe": {
            "ledger_deltas": ["F-1"],
            "assertions": [
                {"id": "casrt-cs", "kind": "fact_absent",
                 "checker": "pattern", "criterion": "stale", "weight": 1.0}]},
    }
    # mirror of apply_org's R3 path
    probe["assertions"] = acd._strip_cs(probe["assertions"])
    probe["counterfactual_probe"]["assertions"] = acd._strip_cs(
        probe["counterfactual_probe"]["assertions"])
    ids = [a["id"] for a in probe["assertions"]]
    assert "asrt-cs" not in ids
    assert probe["counterfactual_probe"]["assertions"] == []


def test_r4_negation_window_guard():
    pat = r"(?<![\w-])(?:monday)(?![\w-])"
    assert not pattern_hits_unnegated(
        pat, "There is no Monday triage session.")
    assert not pattern_hits_unnegated(
        pat, "We skip Monday sessions this cycle.")
    assert pattern_hits_unnegated(pat, "Triage happens Monday.")
    # negator in a PREVIOUS sentence does not suppress
    assert pattern_hits_unnegated(
        pat, "No exceptions here. Triage happens Monday.")
    # negator further than 12 tokens away in the same clause: no suppress
    far = ("not once did anyone in any of the many long meetings on any "
           "topic decide against holding triage every Monday")
    assert pattern_hits_unnegated(pat, far)


def test_r4_negated_mention_cannot_pass_applied_side():
    sp = _load_script("screen_probes")
    assertions = [
        {"id": "a1", "kind": "fact_applied", "checker": "semantic",
         "criterion": "states the Monday schedule", "weight": 1.0},
        {"id": "asrt-cs", "kind": "fact_absent", "checker": "pattern",
         "criterion": r"(?<![\w-])(?:monday)(?![\w-])", "weight": 1.0},
    ]
    out = "There is no Monday session; we meet Friday."
    # suppression spares the absence detector...
    score = sp._score("r", assertions, out, {"a1": False})
    # ...but the affirmative criterion still fails: only absence credit
    assert score == 0.5


def test_r5_branch_validation_rejects_fragments():
    import pytest
    acd = _load_script("add_cross_detectors")

    def probe_with(crit):
        return {
            "probe_id": "P-V-01",
            "assertions": [
                {"id": "asrt-cs", "kind": "fact_absent",
                 "checker": "pattern", "criterion": crit, "weight": 1.0}],
            "counterfactual_probe": {"assertions": []},
        }
    bad_digit = r"(?<![\w-])(?:(?:000|two))(?![\w-])"
    with pytest.raises(SystemExit):
        acd._validate_branches(probe_with(bad_digit))
    bad_word = r"(?<![\w-])(?:two)(?![\w-])"
    with pytest.raises(SystemExit):
        acd._validate_branches(probe_with(bad_word))
    good = r"(?<![\w-])(?:(?:2|two)[\s-]+approval\w*|friday)(?![\w-])"
    acd._validate_branches(probe_with(good))  # no raise


# ------------------------------------------------------------ v0.4.3 items

def test_empty_output_scores_zero_on_every_assertion():
    """Empty-output rule: no deliverable, no credit — absence detectors
    included (an empty output would otherwise pass an absence-only side)."""
    sp = _load_script("screen_probes")
    assertions = [
        {"id": "a1", "kind": "fact_absent", "checker": "pattern",
         "criterion": r"never-there", "weight": 1.0},
        {"id": "a2", "kind": "fact_applied", "checker": "semantic",
         "criterion": "x", "weight": 1.0},
    ]
    assert sp._score("r", assertions, "", {"a2": True}) == 0.0
    assert sp._score("r", assertions, "  \n ", {"a2": True}) == 0.0
    assert sp._score("r", assertions, None, {"a2": True}) == 0.0
    assert sp._score("r", assertions, "real text", {"a2": True}) == 1.0


def test_check_assertion_exempts_cross_side_detectors():
    from membench.probes import _check_assertion
    facts = {"F-1": {"fact_id": "F-1", "canonical": "Standup at 9am.",
                     "counterfactual": "Standup at 4pm."}}
    cs = {"id": "asrt-cs", "kind": "fact_absent", "checker": "pattern",
          "criterion": r"(?<![\w-])4\s?pm(?![\w-])", "weight": 1.0}
    assert _check_assertion(cs, facts, "base", "F-1") == []
    bad = dict(cs, kind="fact_applied")
    assert any("cross-side detectors must be" in e
               for e in _check_assertion(bad, facts, "base", "F-1"))
    bad_re = dict(cs, criterion="(")
    assert any("bad regex" in e
               for e in _check_assertion(bad_re, facts, "base", "F-1"))


def test_semantic_detector_fallback_when_pattern_uncoverable():
    """The semantic fallback was measured and REJECTED (2026-08-15, 0/19
    true positives); default is pattern-only (skip). `semantic=True` is
    kept for reproduction; idempotent across both."""
    acd = _load_script("add_cross_detectors")
    base = "Standup lasts 15 minutes."
    cf = "Standup lasts 45 minutes."
    probe = {
        "probe_id": "P-Y-01", "targets": ["F-1"],
        "assertions": [
            {"id": "asrt-1", "kind": "fact_applied", "checker": "semantic",
             "criterion": "states the length", "weight": 1.0}],
        "counterfactual_probe": {
            "ledger_deltas": ["F-1"],
            "assertions": [
                {"id": "casrt-1", "kind": "fact_applied",
                 "checker": "semantic", "criterion": "states the length",
                 "weight": 1.0}]},
    }
    r = acd.add_detectors(probe, {"F-1": base}, {"F-1": cf}, [])
    assert r["added"] == [] and len(r["skipped"]) == 2
    r = acd.add_detectors(probe, {"F-1": base}, {"F-1": cf}, [], semantic=True)
    assert r["added"] == ["asrt-css", "casrt-css"]
    snap = json.dumps(probe, sort_keys=True)
    acd.add_detectors(probe, {"F-1": base}, {"F-1": cf}, [], semantic=True)
    assert json.dumps(probe, sort_keys=True) == snap
    a = [x for x in probe["assertions"] if x["id"] == "asrt-css"][0]
    assert a["kind"] == "fact_absent" and a["checker"] == "semantic"
    assert cf in a["criterion"] and base not in a["criterion"]
    assert "does not present" in a["criterion"]
    from membench.probes import _check_assertion
    assert _check_assertion(a, {}, "base", "F-1") == []


def test_r6_uncontested_attribute_classes_are_not_hunted():
    """R6: day-name/time, money and percent anchors only when the other
    side also carries that class (the attribute is contested)."""
    freeze = "Company policy freezes deploys from Thursday noon through Monday morning."
    no_freeze = "Company policy allows deploys through the weekend."
    assert side_value_anchors(freeze, no_freeze) == []
    assert side_value_anchors(freeze, "Company policy freezes deploys Friday 5pm to Tuesday.")
    assert side_value_anchors("Oncall engineers receive a $300 stipend per primary week.",
                              "Oncall engineers receive no stipend.") == []
    assert side_value_anchors("Oncall engineers receive a $300 stipend per primary week.",
                              "Oncall engineers receive a $500 stipend per primary week.")
    # unit-anchored counts are unaffected
    assert side_value_anchors("Reviews need 2 approvals.", "Reviews need no approvals.")
