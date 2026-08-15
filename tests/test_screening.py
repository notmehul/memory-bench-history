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


def test_incremental_export_and_merge_import(tmp_path):
    """v0.4.3 wave mechanics: only unjudged / text-changed / forced criteria
    are exported; --merge keeps untouched verdicts; report refuses stale
    verdicts whose criterion text changed without a re-judge."""
    work = _work_dir(tmp_path)
    # Full first pass with sha recording.
    screen_probes.cmd_judge_export(SimpleNamespace(work_dir=work, ids=None))
    pending = json.loads((work / "pending-judge.json").read_text())
    vfile = work / "v1.json"
    vfile.write_text(json.dumps(
        {row["id"]: {k: True for k in row["criteria"]} for row in pending}))
    screen_probes.cmd_judge_import(
        SimpleNamespace(work_dir=work, verdicts=vfile, judge="j1"))
    # Nothing to do incrementally.
    screen_probes.cmd_judge_export(
        SimpleNamespace(work_dir=work, ids=None, incremental=True))
    assert json.loads((work / "pending-judge.json").read_text()) == []
    # Rewrite one criterion (ceiling row's casrt-1) and add a new one.
    runs = [json.loads(x) for x in (work / "runs.jsonl").read_text().splitlines()]
    runs[0]["cf_assertions"][0]["criterion"] = "the note omits the old cadence"
    runs[0]["assertions"].append(
        {"id": "asrt-css", "checker": "semantic", "kind": "fact_absent",
         "criterion": "does not present X", "weight": 1.0})
    (work / "runs.jsonl").write_text("".join(json.dumps(r) + "\n" for r in runs))
    screen_probes.cmd_judge_export(
        SimpleNamespace(work_dir=work, ids=None, incremental=True))
    pending = json.loads((work / "pending-judge.json").read_text())
    assert len(pending) == 1 and len(pending[0]["criteria"]) == 2
    mapping = json.loads((work / "pending-judge.map.json").read_text())
    assert set(mapping[pending[0]["id"]]["criteria"].values()) == {"casrt-1", "asrt-css"}
    # Report-time stale guard fires before the re-judge lands.
    row = runs[0]
    jrow = {r["run_id"]: r for r in (json.loads(x) for x in
            (work / "judgements.jsonl").read_text().splitlines())}["P-0001-01:ceiling"]
    assert jrow["criteria_sha"]["casrt-1"] != screen_probes._crit_sha(
        row["cf_assertions"][0]["criterion"])
    # Merge import: asrt-1 verdict survives, casrt-1 replaced, asrt-css added.
    v2 = work / "v2.json"
    v2.write_text(json.dumps({pending[0]["id"]: {k: False for k in pending[0]["criteria"]}}))
    screen_probes.cmd_judge_import(
        SimpleNamespace(work_dir=work, verdicts=v2, judge="j2", merge=True))
    final = {r["run_id"]: r for r in (json.loads(x) for x in
             (work / "judgements.jsonl").read_text().splitlines())}["P-0001-01:ceiling"]
    assert final["verdicts"] == {"asrt-1": True, "casrt-1": False, "asrt-css": False}
    assert final["judge"] == "j1+j2"
    # --force re-exports a named criterion even though it is judged and unchanged.
    force = work / "force.txt"
    force.write_text("P-0001 asrt-1\n")
    screen_probes.cmd_judge_export(
        SimpleNamespace(work_dir=work, ids=None, incremental=True, force=force))
    pending = json.loads((work / "pending-judge.json").read_text())
    assert sorted(len(p["criteria"]) for p in pending) == [1, 1]  # both rows' asrt-1


def _mk(rid, cond, assertions, cross=None, cf=None):
    return {"run_id": rid, "probe_id": rid.split(":")[0], "cluster_id": rid[:6],
            "condition": cond, "prompt": "", "assertions": assertions,
            "cross_assertions": cross, "cf_assertions": cf}


def test_s6_discrimination_gate(tmp_path):
    """S6: an instance whose ceiling output also satisfies the cf assertion
    set (non-inverting twin) is invalid even though ceiling/twin/floor pass."""
    base = [{"id": "asrt-1", "checker": "semantic", "kind": "fact_applied",
             "criterion": "small PRs before lunch", "weight": 1.0}]
    cf = [{"id": "casrt-1", "checker": "semantic", "kind": "fact_applied",
           "criterion": "large PRs after lunch", "weight": 1.0}]
    rows = []
    for inst in ("P-0001-01", "P-0001-02"):
        rows += [_mk(f"{inst}:floor", "floor", base, cf=cf),
                 _mk(f"{inst}:ceiling", "ceiling", base, cross=cf),
                 _mk(f"{inst}:twin_ceiling", "twin_ceiling", cf, cross=base)]
    results = [{"run_id": r["run_id"], "output": "some deliverable"} for r in rows]
    # -01: discriminating twin; -02: ceiling output ALSO passes cf side.
    verdicts = {
        "P-0001-01:floor": {"asrt-1": False, "casrt-1": False},
        "P-0001-01:ceiling": {"asrt-1": True, "casrt-1": False},
        "P-0001-01:twin_ceiling": {"casrt-1": True, "asrt-1": False},
        "P-0001-02:floor": {"asrt-1": False, "casrt-1": False},
        "P-0001-02:ceiling": {"asrt-1": True, "casrt-1": True},
        "P-0001-02:twin_ceiling": {"casrt-1": True, "asrt-1": False},
    }
    (tmp_path / "runs.jsonl").write_text("".join(json.dumps(r) + "\n" for r in rows))
    (tmp_path / "results.jsonl").write_text("".join(json.dumps(r) + "\n" for r in results))
    (tmp_path / "judgements.jsonl").write_text("".join(
        json.dumps({"run_id": k, "verdicts": v, "judge": "t"}) + "\n"
        for k, v in verdicts.items()))
    out = tmp_path / "report.json"
    screen_probes.cmd_report(SimpleNamespace(work_dir=tmp_path, out=out))
    rep = json.loads(out.read_text())
    inst = rep["clusters"]["P-0001"]["instances"]
    assert inst["P-0001-01"]["valid"] is True
    assert inst["P-0001-01"]["ceiling_vs_cf"] == 0.0
    assert inst["P-0001-02"]["valid"] is False
    assert inst["P-0001-02"]["ceiling_vs_cf"] == 1.0
    assert inst["P-0001-02"]["ceiling"] == 1.0 and inst["P-0001-02"]["twin_ceiling"] == 1.0
