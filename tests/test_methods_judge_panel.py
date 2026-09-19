"""Guards for the Track B judge-panel scorer (`scripts/methods_judge_panel.py`).

The control test is the important one: recomputing the v1 judge against the
frozen human anchor must reproduce the committed G4 result exactly. An earlier
revision keyed verdicts by (run_id, assertion_id) and silently collapsed
cross-org id collisions, which moved kappa from 0.537 to 0.399 without erroring.
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "scripts"))

from conftest import SEALED, require  # noqa: E402
from methods_judge_panel import (  # noqa: E402, I001
    CALIB,
    PANEL,
    _agree_block,
    _kind_map,
    _panel_verdicts,
    _v1_verdicts,
)

pytestmark = pytest.mark.skipif(
    not (PANEL / "haiku-4.5").is_dir(), reason="judge-panel verdicts not present")


def _anchor():
    key = json.loads(require("datasets/dev/calibration/packet-key.json", SEALED).read_text())
    human_raw = json.loads((CALIB / "ratings-M.json").read_text())
    orgs = {v["org"] for v in key.values()}
    human = {(v["org"], v["run_id"], v["assertion_id"]): bool(human_raw[pid])
             for pid, v in key.items()}
    return orgs, human


def test_v1_baseline_reproduces_committed_g4():
    orgs, human = _anchor()
    got = _agree_block(sorted(human), human, _v1_verdicts(orgs), _kind_map(orgs))["overall"]
    g4 = json.loads((CALIB / "judge-agreement.json").read_text())
    assert got["n"] == g4["n"] == 150
    assert got["agreement"] == round(g4["raw_agreement"], 4)
    assert got["kappa"] == round(g4["kappa"], 4) == 0.537


def test_verdict_keys_carry_the_org():
    """Run ids repeat across orgs; a key without the org loses verdicts."""
    orgs, _ = _anchor()
    v1 = _v1_verdicts(orgs)
    assert len(orgs) > 1
    collisions = {(r, a) for (o, r, a) in v1} & {
        (r, a) for (o, r, a) in v1 if o == sorted(orgs)[1]}
    assert collisions, "expected run ids shared across orgs"
    assert len({(r, a) for (_, r, a) in v1}) < len(v1), \
        "dropping the org must lose keys, which is the bug this guards"


def test_panel_verdicts_cover_the_whole_batch():
    for tag in ("haiku-4.5", "sonnet-5", "opus-5", "fable-5.1"):
        v = _panel_verdicts(PANEL / tag)
        assert len(v) == 478, f"{tag} scored {len(v)} criteria, expected 478"


def test_script_runs_and_control_passes(tmp_path):
    require("datasets/dev/calibration/packet-key.json", SEALED)
    r = subprocess.run(
        [sys.executable, str(REPO / "scripts/methods_judge_panel.py"), "--out", str(tmp_path)],
        capture_output=True, text=True, cwd=REPO)
    assert r.returncode == 0, r.stderr
    assert "CONTROL FAILED" not in r.stderr
    report = json.loads((tmp_path / "report.json").read_text())
    assert report["populations"] == {"sampled": 150, "exported": 478}
