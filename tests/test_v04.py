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
    spec = importlib.util.spec_from_file_location(
        name, ROOT / "scripts" / f"{name}.py")
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


BASE = "Retro action items must carry an owner within 48 hours."
CF = "Retro action items must carry an owner within 6 days."


def test_anchors_no_bare_short_numerals():
    for own, other in ((BASE, CF), (CF, BASE)):
        for b in side_value_anchors(own, other):
            assert b not in {str(n) for n in range(100)}, b


def test_anchors_number_word_and_unit():
    cf_anchors = side_value_anchors(CF, BASE)
    pat = anchors_pattern(cf_anchors)
    assert pat is not None
    # must hit both numeral and word surface forms, unit-anchored
    assert is_hedged("plan for 6 days out", pat, pat)
    assert is_hedged("plan for six days out", pat, pat)
    # bare "6" without the unit must NOT fire
    assert not is_hedged("section 6 covers retros", pat, pat)


def test_is_hedged_requires_both_sides():
    b_pat = anchors_pattern(side_value_anchors(BASE, CF))
    c_pat = anchors_pattern(side_value_anchors(CF, BASE))
    committed = "Owners assigned within 48 hours."
    hedging = "Assign owners within 48 hours (or 6 days, whichever applies)."
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
    foreign = [("base:F-9", "The SLA handbook already says 48 hours.")]
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
    assert re.search(asrt_cs["criterion"], "within six days",
                     re.IGNORECASE | re.DOTALL)
    assert not re.search(asrt_cs["criterion"], "within 48 hours",
                         re.IGNORECASE | re.DOTALL)


def test_manifest_prompts_unchanged_by_v04(tmp_path):
    """Hedge fields are additive: prompts must stay byte-identical to the
    committed seed-1 manifest."""
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
