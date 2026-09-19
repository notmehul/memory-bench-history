"""Track B corpus re-analysis: the join over the committed verdicts is
lossless and its totals are the ones the prespecification names.

These assert against the real committed artifacts, not fixtures — a verdict
silently dropped or double-counted would move a number in the methods paper,
so the counts are pinned here.
"""

import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import methods_verdict_kinds as mvk  # noqa: E402
from conftest import HOLDOUT, require  # noqa: E402

PER_DIR_TOTALS = {
    "datasets/dev/screening/org-00001": 1512,
    "datasets/dev/screening/org-00002": 1341,
    "datasets/dev/screening/org-00003": 1278,
    "datasets/dev/screening/org-00004": 897,
    "datasets/dev/pilot/nomemory/seed-1/score-k1": 370,
}
POOLED_TOTAL = 5398
PER_KIND_TOTALS = {"fact_applied": 2677, "fact_absent": 1463, "scope_correct": 1258}


@pytest.fixture(scope="module")
def report() -> dict:
    require("datasets/dev/screening/org-00004", HOLDOUT)
    return mvk.analyze()


def test_join_is_lossless(report: dict):
    assert report["unmatched_total"] == 0
    assert all(d["unmatched"] == 0 for d in report["per_dir"])


def test_per_dir_totals(report: dict):
    assert {d["dir"]: d["n_verdicts"] for d in report["per_dir"]} == PER_DIR_TOTALS


def test_pooled_total(report: dict):
    assert report["n_verdicts_total"] == POOLED_TOTAL
    assert sum(PER_DIR_TOTALS.values()) == POOLED_TOTAL


def test_pooled_kind_totals(report: dict):
    by_kind = report["pooled"]["by_kind"]
    assert {k: v["n"] for k, v in by_kind.items()} == PER_KIND_TOTALS
    assert sum(v["n"] for v in by_kind.values()) == POOLED_TOTAL


def test_every_verdict_carries_the_rubric_v2_judge_tag(report: dict):
    assert report["judges"] == {"claude-sonnet-5-blinded-v2": POOLED_TOTAL}
    assert report["off_tag_verdicts"] == {}


def test_dedup_is_last_wins(tmp_path: Path):
    """Re-judged rows are appended, so the same run_id appears twice and the
    later line is the live one (screen_probes.py `_read_done`)."""
    p = tmp_path / "judgements.jsonl"
    p.write_text('{"run_id": "r1", "verdicts": {"a": true}}\n'
                 '{"run_id": "r1", "verdicts": {"a": false}}\n')
    done = mvk._read_done(p)
    assert len(done) == 1
    assert done["r1"]["verdicts"] == {"a": False}


def test_unmatched_verdict_fails_loudly(tmp_path: Path):
    (tmp_path / "runs.jsonl").write_text(json.dumps(
        {"run_id": "r1",
         "assertions": [{"id": "asrt-1", "kind": "fact_applied",
                         "checker": "semantic"}]}) + "\n")
    (tmp_path / "judgements.jsonl").write_text(json.dumps(
        {"run_id": "r1", "verdicts": {"asrt-1": True, "asrt-9": False},
         "judge": "claude-sonnet-5-blinded-v2"}) + "\n")
    with pytest.raises(SystemExit) as e:
        mvk.analyze_dir(tmp_path)
    assert "UNMATCHED JOIN" in str(e.value)
    assert "asrt-9" in str(e.value)
