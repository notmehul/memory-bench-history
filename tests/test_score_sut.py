"""SUT scoring pipeline (scripts/score_sut.py): manifest from valid
instances, blinded judge round-trip via screen_probes, pair credit,
empty-output rule, cluster-robust aggregation."""

import importlib.util
import json
import sys
from pathlib import Path
from types import SimpleNamespace

ROOT = Path(__file__).resolve().parents[1]


def _load(name):
    spec = importlib.util.spec_from_file_location(name, ROOT / "scripts" / f"{name}.py")
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


score_sut = _load("score_sut")
screen_probes = sys.modules["screen_probes"]

SEM_B = {"id": "asrt-1", "kind": "fact_applied", "checker": "semantic",
         "criterion": "states the base value", "weight": 1.0}
SEM_C = {"id": "casrt-1", "kind": "fact_applied", "checker": "semantic",
         "criterion": "states the twin value", "weight": 1.0}


def _world(tmp_path):
    org, scr = tmp_path / "org", tmp_path / "scr"
    org.mkdir()
    scr.mkdir()
    probes = []
    for i in (1, 2, 3):
        probes.append({"probe_id": f"P-0001-0{i}", "cluster_id": "P-0001", "archetype": "A1",
                       "metrics": ["propagation_latency"], "assertions": [SEM_B],
                       "counterfactual_probe": {"assertions": [SEM_C]}})
    probes.append({"probe_id": "P-0002-01", "cluster_id": "P-0002", "archetype": "A7",
                   "metrics": ["staleness_rate"], "assertions": [SEM_B],
                   "counterfactual_probe": {"assertions": [SEM_C]}})
    (org / "probes.jsonl").write_text("".join(json.dumps(p) + "\n" for p in probes))
    report = {"clusters": {
        "P-0001": {"survive": True, "instances": {
            "P-0001-01": {"valid": True}, "P-0001-02": {"valid": True},
            "P-0001-03": {"valid": False}}},
        "P-0002": {"survive": True, "instances": {"P-0002-01": {"valid": True}}}}}
    (org / "g3-report.json").write_text(json.dumps(report))
    runs, results, judg = [], [], []
    for pid in ("P-0001-01", "P-0001-02", "P-0001-03", "P-0002-01"):
        cid = pid[:6]
        runs.append({"run_id": f"{pid}:floor", "probe_id": pid, "cluster_id": cid,
                     "condition": "floor", "assertions": [SEM_B], "cf_assertions": [SEM_C]})
        runs.append({"run_id": f"{pid}:ceiling", "probe_id": pid, "cluster_id": cid,
                     "condition": "ceiling", "assertions": [SEM_B]})
        runs.append({"run_id": f"{pid}:twin_ceiling", "probe_id": pid, "cluster_id": cid,
                     "condition": "twin_ceiling", "assertions": [SEM_C]})
        for c in ("floor", "ceiling", "twin_ceiling"):
            results.append({"run_id": f"{pid}:{c}", "output": f"{c} text"})
        judg.append({"run_id": f"{pid}:floor", "verdicts": {"asrt-1": False, "casrt-1": False}})
        judg.append({"run_id": f"{pid}:ceiling", "verdicts": {"asrt-1": True}})
        judg.append({"run_id": f"{pid}:twin_ceiling", "verdicts": {"casrt-1": True}})
    for name, rows in (("runs", runs), ("results", results), ("judgements", judg)):
        (scr / f"{name}.jsonl").write_text("".join(json.dumps(r) + "\n" for r in rows))
    # SUT outputs: P-0001-01 good both sides; P-0001-02 base only; P-0002-01 empty base
    base = [{"run_id": "P-0001-01:sut", "output": "base ok"},
            {"run_id": "P-0001-02:sut", "output": "base ok"},
            {"run_id": "P-0001-03:sut", "output": "ignored (invalid instance)"},
            {"run_id": "P-0002-01:sut", "output": None, "error": "worker failed"}]
    twin = [{"run_id": "P-0001-01:sut", "output": "twin ok"},
            {"run_id": "P-0001-02:sut", "output": "still base"},
            {"run_id": "P-0001-03:sut", "output": "x"},
            {"run_id": "P-0002-01:sut", "output": "twin ok"}]
    (tmp_path / "base.jsonl").write_text("".join(json.dumps(r) + "\n" for r in base))
    (tmp_path / "twin.jsonl").write_text("".join(json.dumps(r) + "\n" for r in twin))
    return org, scr


def test_manifest_judge_roundtrip_and_pair_credit(tmp_path):
    org, scr = _world(tmp_path)
    work = tmp_path / "work"
    score_sut.cmd_manifest(SimpleNamespace(
        org_dir=org, screening_dir=scr, work_dir=work, sut_base=tmp_path / "base.jsonl",
        sut_twin=tmp_path / "twin.jsonl", system="mock-system"))
    rows = [json.loads(x) for x in (work / "runs.jsonl").read_text().splitlines()]
    assert {r["run_id"] for r in rows} == {
        "P-0001-01:sut_base", "P-0001-01:sut_twin", "P-0001-02:sut_base",
        "P-0001-02:sut_twin", "P-0002-01:sut_base", "P-0002-01:sut_twin"}  # -03 invalid
    # blinded export: judge sees output + criteria only; empty output rows are skipped
    screen_probes.cmd_judge_export(SimpleNamespace(work_dir=work, ids=None))
    pending = json.loads((work / "pending-judge.json").read_text())
    assert all(set(p) == {"id", "criteria", "output"} for p in pending)
    assert len(pending) == 5  # the null-output base row is not exported
    mapping = json.loads((work / "pending-judge.map.json").read_text())
    verdicts = {}
    for row in pending:
        rid = mapping[row["id"]]["run_id"]
        good = {"P-0001-01:sut_base", "P-0001-01:sut_twin", "P-0001-02:sut_base",
                "P-0002-01:sut_twin"}
        verdicts[row["id"]] = {k: rid in good for k in row["criteria"]}
    vf = work / "v.json"
    vf.write_text(json.dumps(verdicts))
    screen_probes.cmd_judge_import(SimpleNamespace(work_dir=work, verdicts=vf, judge="t"))
    out = tmp_path / "report.json"
    score_sut.cmd_report(SimpleNamespace(org_dir=org, screening_dir=scr, work_dir=work,
                                         out=out))
    rep = json.loads(out.read_text())
    inst = rep["instances"]
    assert inst["P-0001-01"]["pair_credit"] is True
    assert inst["P-0001-02"]["pair_credit"] is False          # twin side failed
    assert inst["P-0002-01"]["sut_base"] == 0.0               # empty-output rule
    assert inst["P-0002-01"]["pair_credit"] is False
    assert inst["P-0001-01"]["norm_base"] == 1.0 and inst["P-0002-01"]["norm_base"] == 0.0
    assert rep["n_empty_deliverables"] == 1
    assert rep["by_rung"]["2"]["pair_credit_mean"] == 0.5
    assert rep["by_rung"]["2"]["n_clusters"] == 1
    assert rep["by_rung"]["1"]["pair_credit_mean"] == 0.0
    assert rep["by_metric"]["propagation_latency"]["n_instances"] == 2
    assert "single aggregate" in rep["note"]


def test_cluster_robust_se_inflates_with_intracluster_correlation():
    cr = score_sut._cluster_robust
    # two clusters, perfectly homogeneous within -> rho ~ 1, SE inflated vs iid
    mean, se, n, k = cr({"a": [1.0, 1.0, 1.0], "b": [0.0, 0.0, 0.0]})
    _, se_iid, _, _ = cr({"a": [1.0, 0.0, 1.0], "b": [0.0, 1.0, 0.0]})
    assert mean == 0.5 and n == 6 and k == 2 and se > se_iid
