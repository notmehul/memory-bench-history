"""Blinded judge-export/judge-import round-trip (screen_probes.py).

The judge must see only (output, criteria) — no run ids, conditions, or
base-vs-counterfactual side (probe-spec §3). These tests pin that contract.
"""

import importlib.util
import json
import sys
from pathlib import Path
from types import SimpleNamespace

_SPEC = importlib.util.spec_from_file_location(
    "screen_probes",
    Path(__file__).resolve().parents[1] / "scripts" / "screen_probes.py",
)
screen_probes = importlib.util.module_from_spec(_SPEC)
sys.modules["screen_probes"] = screen_probes
_SPEC.loader.exec_module(screen_probes)


def _work_dir(tmp_path: Path) -> Path:
    runs = [
        {
            "run_id": "P-0001-01:ceiling",
            "assertions": [
                {"id": "asrt-1", "checker": "semantic", "kind": "fact_applied",
                 "criterion": "the note states the review cadence", "weight": 1.0},
            ],
            "cf_assertions": [
                {"id": "casrt-1", "checker": "semantic", "kind": "fact_applied",
                 "criterion": "the note states the alternate cadence", "weight": 1.0},
            ],
        },
        {
            "run_id": "P-0001-01:floor",
            "assertions": [
                {"id": "asrt-1", "checker": "semantic", "kind": "fact_applied",
                 "criterion": "the note states the review cadence", "weight": 1.0},
            ],
        },
    ]
    results = [
        {"run_id": "P-0001-01:ceiling", "output": "ceiling deliverable"},
        {"run_id": "P-0001-01:floor", "output": "floor deliverable"},
    ]
    (tmp_path / "runs.jsonl").write_text(
        "".join(json.dumps(r) + "\n" for r in runs))
    (tmp_path / "results.jsonl").write_text(
        "".join(json.dumps(r) + "\n" for r in results))
    (tmp_path / "judgements.jsonl").write_text("")
    return tmp_path


def test_export_is_blind(tmp_path):
    work = _work_dir(tmp_path)
    screen_probes.cmd_judge_export(SimpleNamespace(work_dir=work, ids=None))
    pending = json.loads((work / "pending-judge.json").read_text())
    blob = json.dumps(pending)
    assert "P-0001" not in blob
    assert "asrt" not in blob and "casrt" not in blob
    assert "floor" not in blob.replace("floor deliverable", "")
    assert "ceiling" not in blob.replace("ceiling deliverable", "")
    for row in pending:
        assert set(row) == {"id", "criteria", "output"}
        assert all(k.startswith("c") for k in row["criteria"])


def test_import_round_trip(tmp_path):
    work = _work_dir(tmp_path)
    screen_probes.cmd_judge_export(SimpleNamespace(work_dir=work, ids=None))
    pending = json.loads((work / "pending-judge.json").read_text())
    verdicts = {row["id"]: {k: True for k in row["criteria"]} for row in pending}
    vfile = work / "verdicts.json"
    vfile.write_text(json.dumps(verdicts))
    screen_probes.cmd_judge_import(
        SimpleNamespace(work_dir=work, verdicts=vfile, judge="test-judge"))
    imported = {r["run_id"]: r for r in
                (json.loads(x) for x in
                 (work / "judgements.jsonl").read_text().splitlines())}
    assert set(imported) == {"P-0001-01:ceiling", "P-0001-01:floor"}
    ceiling = imported["P-0001-01:ceiling"]
    assert set(ceiling["verdicts"]) == {"asrt-1", "casrt-1"}
    assert ceiling["judge"] == "test-judge"


def test_ids_reexports_already_judged(tmp_path):
    work = _work_dir(tmp_path)
    (work / "judgements.jsonl").write_text(json.dumps({
        "run_id": "P-0001-01:ceiling",
        "verdicts": {"asrt-1": True, "casrt-1": True},
        "judge": "prior",
    }) + "\n")
    # Default export skips the judged row.
    screen_probes.cmd_judge_export(SimpleNamespace(work_dir=work, ids=None))
    assert len(json.loads((work / "pending-judge.json").read_text())) == 1
    # --ids re-exports it for blinded re-judging.
    ids = work / "rejudge.txt"
    ids.write_text("P-0001-01:ceiling\n")
    screen_probes.cmd_judge_export(SimpleNamespace(work_dir=work, ids=ids))
    pending = json.loads((work / "pending-judge.json").read_text())
    assert len(pending) == 1
    mapping = json.loads((work / "pending-judge.map.json").read_text())
    assert mapping[pending[0]["id"]]["run_id"] == "P-0001-01:ceiling"
