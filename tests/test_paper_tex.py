"""The LaTeX paper's numbers must trace to committed artifacts, same as the draft.

`paper/memory-bench.tex` is the submission artifact and its figures carry numbers
as TikZ coordinates, where a typo is invisible: a wrong bar length still renders.
These tests recompute each figure's data from the evidence and assert the
coordinate is present in the source.
"""

import json
import re
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
TEX = ROOT / "paper" / "memory-bench.tex"
SEEDS = ("org-00001", "org-00002", "org-00003")


@pytest.fixture(scope="module")
def tex() -> str:
    return TEX.read_text()


@pytest.fixture(scope="module")
def flat(tex: str) -> str:
    """Whitespace collapsed: the prose is hard-wrapped, so a claim can straddle
    a newline."""
    return " ".join(tex.split())


@pytest.fixture(scope="module")
def g3() -> dict:
    return {o: json.loads((ROOT / "datasets/dev" / o / "g3-report.json").read_text())
            for o in SEEDS}


def test_tex_exists_and_is_complete(tex: str):
    assert tex.startswith("%")
    assert "\\begin{document}" in tex and "\\end{document}" in tex
    assert tex.count("\\begin{figure}") == 7, "seven figures expected"


def test_gate_figure_coordinates_match_the_reports(tex: str, g3: dict):
    """Figure 3 plots cluster survival and valid instances per seed."""
    surv = [g3[o]["n_survivors"] for o in SEEDS]          # seeds 1,2,3
    valid = [g3[o]["n_valid_instances"] for o in SEEDS]
    # plotted bottom-to-top as seed 3, 2, 1
    assert f"coordinates {{({surv[2]},1) ({surv[1]},2) ({surv[0]},3)}}" in tex
    assert f"coordinates {{({valid[2]},1) ({valid[1]},2) ({valid[0]},3)}}" in tex


def test_gate_thresholds_are_the_prespecified_ones(tex: str):
    assert "axis cs:45,0.4" in tex and "gate 45" in tex
    assert "axis cs:135,0.4" in tex and "gate 135" in tex


def test_slopegraph_endpoints_match_the_measured_rates(tex: str):
    data = json.loads(
        (ROOT / "datasets/methods/corpus-kind-rates/slopegraph.json").read_text())
    for kind in ("fact_absent", "fact_applied", "scope_correct"):
        a = data[kind]["screening"]["rate"]
        b = data[kind]["floor"]["rate"]
        assert f"(\\xa,\\yy{{{a}}}) -- (\\xb,\\yy{{{b}}})" in tex, \
            f"{kind}: slopegraph line should run {a} -> {b}"


def test_corpus_rates_in_prose_match_the_report(flat: str):
    rep = json.loads(
        (ROOT / "datasets/methods/corpus-kind-rates/report.json").read_text())
    by = rep["by_kind"] if "by_kind" in rep else rep["pooled"]["by_kind"]
    assert rep["n_verdicts_total"] == 5398
    assert "5{,}398" in flat
    pct = {k: round(100 * v["positive_rate"], 1) for k, v in by.items()}
    assert f"{pct['fact_absent']}\\%" in flat
    assert f"{pct['fact_applied']}\\%" in flat
    assert f"{pct['scope_correct']}\\%" in flat


def test_floor_figure_matches_the_scored_report(tex: str, flat: str):
    rep = json.loads((
        ROOT / "datasets/dev/pilot/nomemory/seed-1/score-k1/report.json").read_text())
    rungs = rep["by_rung"]
    assert [rungs[r]["n_instances"] for r in ("1", "2", "3")] == [92, 17, 16]
    assert round(rungs["1"]["pair_credit_mean"], 3) == 0.022
    assert round(rungs["2"]["pair_credit_mean"], 3) == 0.118
    assert rungs["3"]["pair_credit_mean"] == 0.0
    assert "(0.022,3) +- (0.040,0)" in tex
    assert "(0.118,2) +- (0.217,0)" in tex
    assert "rung 1 pair credit" in flat and "0.022" in flat


def test_sub07_sensitivity_numbers_match(flat: str):
    s = json.loads((
        ROOT / "datasets/dev/screening/sub07-sensitivity/summary.json").read_text())
    assert s["total_valid_instances"]["canon"] == 371
    assert s["total_valid_instances"]["after_drop"] == 341
    assert "371 to 341 valid instances" in flat
    assert "341 valid instances against the" in flat


def test_cancellation_figure_is_the_measured_confusion(tex: str):
    """Figure 5: over-accepts 8/6/0/14, under-accepts 0/7/7/14."""
    assert "coordinates {(8,4) (6,3) (0,2) (14,1)}" in tex
    assert "coordinates {(0,4) (-7,3) (-7,2) (-14,1)}" in tex


def test_harness_figure_matches_the_protocol(tex: str, flat: str):
    assert "coordinates {(75,1) (95,3) (100,4)}" in tex
    assert "coordinates {(65,2)}" in tex
    assert "axis cs:90,0.4" in tex, "the prespecified bar must be drawn at 90"
    assert "13/20" in tex and "19/20" in tex and "20/20" in tex


def test_headline_counts_present(flat: str, g3: dict):
    total = sum(g3[o]["n_valid_instances"] for o in SEEDS)
    assert total == 371
    assert "371 valid paired" in flat
    assert "125/131/115" in flat
    assert "46/54, 46/54, 40/54" in flat


def test_no_comparative_language_survives(flat: str):
    """The freeze forbids any comparative system claim in this paper."""
    banned = ("outperforms", "best-performing system", "beats every",
              "state of the art on memory-bench", "ranked first")
    hits = [b for b in banned if b.lower() in flat.lower()]
    assert not hits, f"comparative language in the LaTeX paper: {hits}"


def test_author_block_claims_no_affiliation(tex: str):
    assert "Mehul Srivastava" in tex
    assert "Independent" in tex
    assert re.search(r"no institutional affiliation", tex), \
        "the independence disclosure must be present"
