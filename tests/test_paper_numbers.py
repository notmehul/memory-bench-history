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


def test_g4_judge_human_agreement(draft: str):
    """G4 FAILED. The paper must say so, with the measured numbers."""
    r = json.loads(
        (ROOT / "datasets/dev/calibration/judge-agreement.json").read_text())
    assert r["n"] == 150
    assert round(r["raw_agreement"], 3) == 0.813
    assert round(r["kappa"], 3) == 0.537
    assert r["gate_g4_overall"] is False, "gate flipped: update the paper, not this test"
    assert len(r["criteria_below_threshold"]) == 28
    per = r["per_kind"]
    assert round(per["fact_absent"]["kappa"], 3) == 0.166
    for fragment in ("0.537", "0.813", "0.166", "κ ≥ 0.75"):
        assert fragment in draft, f"missing {fragment!r}"


def test_g4_failure_is_not_softened(draft: str):
    """A failed gate is reported as failed, in the abstract and the disclosures."""
    low = draft.lower()
    assert "fails** our prespecified gate" in low or "**fails**" in low
    assert "g4 failed" in low
    assert "28 criteria" in low


def test_g4_symmetry_is_reported_as_a_cancellation(draft: str):
    """The 14/14 split hides two opposite kind-specific biases. An earlier draft
    read it as unbiased noise; that claim would not survive a reviewer who
    computed the marginals, so the corrected reading is pinned here."""
    key = json.loads(
        (ROOT / "datasets/dev/calibration/packet-key.json").read_text())
    gold = json.loads(
        (ROOT / "datasets/dev/calibration/ratings-M.json").read_text())

    def jsonl(p):
        return [json.loads(x) for x in p.read_text().splitlines() if x.strip()]

    def last(rows):
        out = {}
        for r in rows:
            out[r["run_id"]] = r
        return out

    cache, cells = {}, Counter()
    for pid, ref in key.items():
        org = ref["org"]
        if org not in cache:
            d = ROOT / "datasets/dev/screening" / org
            cache[org] = (last(jsonl(d / "runs.jsonl")),
                          last(jsonl(d / "judgements.jsonl")))
        runs, judged = cache[org]
        run = runs[ref["run_id"]]
        a = next(x for x in run["assertions"] + (run.get("cf_assertions") or [])
                 if x["id"] == ref["assertion_id"])
        j = bool(judged[ref["run_id"]]["verdicts"][ref["assertion_id"]])
        cells[(a["kind"], gold[pid], j)] += 1

    # absence criteria: every judge error is an over-accept, none the other way
    assert cells[("fact_absent", False, True)] == 8
    assert cells[("fact_absent", True, False)] == 0
    # scope criteria: every judge error is an under-accept
    assert cells[("scope_correct", True, False)] == 7
    assert cells[("scope_correct", False, True)] == 0
    # and they cancel in aggregate
    over = sum(v for (k, h, j), v in cells.items() if not h and j)
    under = sum(v for (k, h, j), v in cells.items() if h and not j)
    assert over == under == 14

    low = draft.lower()
    assert "cancellation" in low, "the symmetry must not be reported as unbiased noise"
    assert "base-rate artifact" in low, "the fact_absent kappa needs its caveat"
    assert "1 of 44" in low


def test_g4_ratings_match_the_raw_submission(draft: str):
    """The committed labels are the ones the rater actually submitted."""
    packet = json.loads(
        (ROOT / "datasets/dev/calibration/rater-packet.json").read_text())
    ratings = json.loads(
        (ROOT / "datasets/dev/calibration/ratings-M.json").read_text())
    assert list(ratings) == [p["id"] for p in packet]
    assert all(isinstance(v, bool) for v in ratings.values())
    assert sum(ratings.values()) == 108
    assert (ROOT / "datasets/dev/calibration"
            / "rater-M-filled-2026-09-14.xlsx").is_file()


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
