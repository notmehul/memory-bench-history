"""Every headline number in the paper must trace to a committed artifact.

The preprint checklist requires zero hand-typed values in the results core.
These tests recompute each number from the evidence it cites and assert the
rendered string is present in `paper/draft.md`, so a number can no longer drift
away from the artifact it came from — in either direction. A number that
legitimately changes fails here until the artifact and the prose agree again.

Scope is deliberately the numbers the paper asserts, not everything measured.
"""

import json
import sys
from collections import Counter
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from membench.g3 import load_valid_instances  # noqa: E402

SEEDS = ("org-00001", "org-00002", "org-00003")


@pytest.fixture(scope="module")
def draft() -> str:
    """The draft with whitespace collapsed: the prose is hard-wrapped, so a
    claim can straddle a newline. We assert on content, not on layout."""
    return " ".join((ROOT / "paper" / "draft.md").read_text().split())


@pytest.fixture(scope="module")
def g3() -> dict[str, dict]:
    return {org: json.loads((ROOT / "datasets/dev" / org / "g3-report.json").read_text())
            for org in SEEDS}


def test_valid_instance_total(draft: str, g3: dict):
    total = sum(r["n_valid_instances"] for r in g3.values())
    assert total == 371
    assert f"{total} valid paired" in draft


def test_per_seed_counts(draft: str, g3: dict):
    per = [g3[o]["n_valid_instances"] for o in SEEDS]
    assert per == [125, 131, 115]
    assert "/".join(str(n) for n in per) in draft


def test_cluster_survival(draft: str, g3: dict):
    survival = [f'{g3[o]["n_survivors"]}/{g3[o]["n_clusters"]}' for o in SEEDS]
    assert survival == ["46/54", "46/54", "40/54"]
    assert ", ".join(survival) in draft


def test_archetype_breakdown(draft: str):
    counts: Counter = Counter()
    for org in SEEDS:
        d = ROOT / "datasets/dev" / org
        valid = load_valid_instances(d)
        arch = {json.loads(x)["probe_id"]: json.loads(x)["archetype"]
                for x in (d / "probes.jsonl").read_text().splitlines() if x.strip()}
        counts.update(arch[pid] for pid in valid)
    assert sum(counts.values()) == 371
    claim = " ".join(f"{a} {counts[a]}," for a in ("A1", "A2", "A4", "A7")).rstrip(",")
    assert claim in draft, f"expected {claim!r} in the draft"


def test_gate_failures_are_reported_not_repaired(draft: str, g3: dict):
    """All three instance gates FAIL; only seed 3's cluster gate FAILs."""
    assert [g3[o]["gate_g3_instances"] for o in SEEDS] == [False, False, False]
    assert [g3[o]["gate_g3_clusters"] for o in SEEDS] == [True, True, False]
    low = draft.lower()
    assert "all three instance gates fail" in low
    assert "seed 3's cluster gate also fails" in low


def test_floor_run_numbers(draft: str):
    report = json.loads(
        (ROOT / "datasets/dev/pilot/nomemory/seed-1/score-k1/report.json").read_text())
    rungs = report["by_rung"]
    assert round(rungs["1"]["pair_credit_mean"], 3) == 0.022
    assert round(rungs["2"]["pair_credit_mean"], 3) == 0.118
    assert rungs["3"]["pair_credit_mean"] == 0.0
    assert [rungs[r]["n_instances"] for r in ("1", "2", "3")] == [92, 17, 16]
    for fragment in ("rung 1 pair credit 0.022", "rung 2 0.118", "rung 3 0.000",
                     "n=92", "n=17", "n=16"):
        assert fragment in draft, f"missing {fragment!r}"


def test_floor_is_indistinguishable_from_zero_on_every_rung(draft: str):
    """The abstract's strongest claim — check it against the intervals."""
    report = json.loads(
        (ROOT / "datasets/dev/pilot/nomemory/seed-1/score-k1/report.json").read_text())
    for rung, stats in report["by_rung"].items():
        lo, hi = stats["ci95"]
        assert lo <= 0.0 <= hi, f"rung {rung} CI {lo, hi} excludes zero"
    assert "indistinguishable from zero on every capability rung" in draft


def test_judge_decoy_audit(draft: str):
    audit = json.loads(
        (ROOT / "datasets/dev/screening/judge-decoys/audit.json").read_text())
    assert audit["false_accepts"] == 2
    assert audit["n_positive_criteria"] == 41
    adj = audit["adjudication_2026_08_15"]
    assert adj["as_measured"].startswith("2/41")
    assert adj["adjudicated"].startswith("0/39")
    assert "2/41" in draft and "0/39" in draft


def test_harness_agreement(draft: str):
    comp = json.loads(
        (ROOT / "datasets/dev/screening/harness-study-2026-07-25"
                "/comparison.json").read_text())
    agree, disagree = comp["agree"]["twin_ceiling_pass"]
    pct = round(100 * agree / (agree + disagree))
    assert (agree, disagree, pct) == (13, 7, 65)
    assert f"{pct}%" in draft


def test_model_relativity(draft: str):
    """Sourced to the decision log; assert the paper and the log agree."""
    log = (ROOT / "docs" / "decision-log.md").read_text()
    assert "17/54" in log and "37/54" in log
    assert "37/54" in draft and "17/54" in draft


def test_no_comparative_system_claim(draft: str):
    """The reframe's central promise: no system is ranked against another."""
    low = draft.lower()
    for banned in ("expected to win", "outperforms", "beats the baseline",
                   "best-performing system", "state of the art"):
        assert banned not in low, f"comparative language survived: {banned!r}"


def test_no_single_aggregate_score(draft: str):
    low = draft.lower()
    assert "single aggregate" in low          # stated as a prohibition
    assert "overall score" not in low
