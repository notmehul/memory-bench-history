"""Pilot CLI + cross-seed orchestrator on the small runner fixture with
MockWorker: only-valid filtering, resumability, twin runs driven by the
base org's probes, cost columns, and the cross-seed summary math."""

import importlib.util
import json
import sys
from pathlib import Path
from types import SimpleNamespace

from test_runner import ORG, PROBE, STREAM

from membench import pilot
from membench.adapters import MockWorker

ROOT = Path(__file__).resolve().parents[1]


def _load(name):
    if name in sys.modules:
        return sys.modules[name]
    spec = importlib.util.spec_from_file_location(name, ROOT / "scripts" / f"{name}.py")
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


run_pilot = _load("run_pilot")
screen_probes = sys.modules["screen_probes"]

SEM_B = {"id": "asrt-1", "kind": "fact_applied", "checker": "semantic",
         "criterion": "states the base value", "weight": 1.0}
SEM_C = {"id": "casrt-1", "kind": "fact_applied", "checker": "semantic",
         "criterion": "states the twin value", "weight": 1.0}
# valid instances of surviving clusters: P-0001-01, P-0001-02, P-0003-01, P-0003-02
# (P-0001-03 invalid; P-0002-01 valid but its cluster does not survive)
PROBES = [
    dict(PROBE, probe_id="P-0001-01", cluster_id="P-0001", archetype="A1"),
    dict(PROBE, probe_id="P-0001-02", cluster_id="P-0001", archetype="A1"),
    dict(PROBE, probe_id="P-0001-03", cluster_id="P-0001", archetype="A1"),
    dict(PROBE, probe_id="P-0002-01", cluster_id="P-0002", archetype="A7"),
    dict(PROBE, probe_id="P-0003-01", cluster_id="P-0003", archetype="A7"),
    dict(PROBE, probe_id="P-0003-02", cluster_id="P-0003", archetype="A7"),
]
VALID = {"P-0001-01", "P-0001-02", "P-0003-01", "P-0003-02"}
G3 = {"clusters": {
    "P-0001": {"survive": True, "instances": {
        "P-0001-01": {"valid": True}, "P-0001-02": {"valid": True},
        "P-0001-03": {"valid": False}}},
    "P-0002": {"survive": False, "instances": {"P-0002-01": {"valid": True}}},
    "P-0003": {"survive": True, "instances": {
        "P-0003-01": {"valid": True}, "P-0003-02": {"valid": True}}}}}


def _jsonl(path, rows):
    path.write_text("".join(json.dumps(r) + "\n" for r in rows))


def make_seed(datasets: Path, seed: int, twin_org_id: str):
    """datasets/org-0000N (+probes, g3), org-0000N-twin (no probes),
    screening/org-0000N (floor/ceiling/twin anchors + verdicts)."""
    base, twin, scr = run_pilot.seed_dirs(datasets, seed)
    for d in (base, twin, scr):
        d.mkdir(parents=True)
    probes = [dict(p, metrics=["m1"], assertions=[SEM_B],
                   counterfactual_probe={"assertions": [SEM_C]}) for p in PROBES]
    (base / "org.json").write_text(json.dumps(ORG))
    _jsonl(base / "events.jsonl", STREAM)
    _jsonl(base / "probes.jsonl", probes)
    (base / "g3-report.json").write_text(json.dumps(G3))
    (twin / "org.json").write_text(json.dumps(dict(ORG, org_id=twin_org_id)))
    _jsonl(twin / "events.jsonl", STREAM)
    runs, results, judg = [], [], []
    for p in probes:
        pid, cid = p["probe_id"], p["cluster_id"]
        runs += [
            {"run_id": f"{pid}:floor", "probe_id": pid, "cluster_id": cid,
             "condition": "floor", "assertions": [SEM_B], "cf_assertions": [SEM_C]},
            {"run_id": f"{pid}:ceiling", "probe_id": pid, "cluster_id": cid,
             "condition": "ceiling", "assertions": [SEM_B]},
            {"run_id": f"{pid}:twin_ceiling", "probe_id": pid, "cluster_id": cid,
             "condition": "twin_ceiling", "assertions": [SEM_C]}]
        results += [{"run_id": f"{pid}:{c}", "output": f"{c} text"}
                    for c in ("floor", "ceiling", "twin_ceiling")]
        judg += [{"run_id": f"{pid}:floor", "verdicts": {"asrt-1": False, "casrt-1": False}},
                 {"run_id": f"{pid}:ceiling", "verdicts": {"asrt-1": True}},
                 {"run_id": f"{pid}:twin_ceiling", "verdicts": {"casrt-1": True}}]
    _jsonl(scr / "runs.jsonl", runs)
    _jsonl(scr / "results.jsonl", results)
    _jsonl(scr / "judgements.jsonl", judg)
    return base, twin, scr


def _worker():
    # persona line: "You are Bob, engineer (eng) at <org_id>."
    return MockWorker(responses={"at org-test.": "base ok", "at org-twin.": "twin ok"})


def test_only_valid_filtering_run_ids_and_cost_columns(tmp_path):
    base, _twin, _ = make_seed(tmp_path, 1, "org-twin")
    out = tmp_path / "base.jsonl"
    meta = pilot.run_side("nomemory", base, out, _worker(), system="nomemory")
    rows = pilot.read_rows(out)
    assert set(rows) == {f"{pid}:sut" for pid in VALID}
    assert meta["n_skipped_invalid"] == 2 and meta["n_target"] == 4 and meta["n_new_rows"] == 4
    row = rows["P-0001-01:sut"]
    assert row["output"] == "base ok"
    assert {"context_chars", "seconds", "wall_seconds", "prompt_sha"} <= set(row)
    saved = json.loads((tmp_path / "base.jsonl.meta.json").read_text())
    assert saved["side"] == "base" and saved["k"] == 1 and saved["only_valid"] is True
    assert saved["worker"]["harness"] == "codex-cli 0.144.5"
    # --no-only-valid injects every probe
    meta_all = pilot.run_side("nomemory", base, tmp_path / "all.jsonl", _worker(),
                              only_valid=False)
    assert meta_all["n_target"] == 6 and meta_all["n_skipped_invalid"] == 0


def test_resumable_skips_done_rows_and_retries_null_outputs(tmp_path):
    base, _twin, _ = make_seed(tmp_path, 1, "org-twin")
    out = tmp_path / "base.jsonl"
    # a prior partial run: one good row, one null deliverable (must be retried)
    _jsonl(out, [{"run_id": "P-0001-01:sut", "output": "earlier"},
                 {"run_id": "P-0001-02:sut", "output": None, "error": "timeout"}])
    worker = _worker()
    meta = pilot.run_side("nomemory", base, out, worker)
    assert meta["n_resumed"] == 1 and meta["n_new_rows"] == 3
    assert len(worker.calls) == 3
    rows = pilot.read_rows(out)
    assert rows["P-0001-01:sut"]["output"] == "earlier"      # kept, not re-run
    assert rows["P-0001-02:sut"]["output"] == "base ok"      # retried, last row wins
    assert len(out.read_text().splitlines()) == 5            # append-only
    # a full re-run is a no-op
    meta2 = pilot.run_side("nomemory", base, out, _worker())
    assert meta2["n_new_rows"] == 0 and meta2["n_resumed"] == 4


def test_twin_run_uses_base_probes_against_twin_org(tmp_path):
    base, twin, _ = make_seed(tmp_path, 1, "org-twin")
    worker = _worker()
    meta = pilot.run_side("fulltranscript", twin, tmp_path / "twin.jsonl", worker,
                          probes_from=base, side="twin")
    assert meta["org"] == "org-00001-twin" and meta["probes_from"] == "org-00001"
    rows = pilot.read_rows(tmp_path / "twin.jsonl")
    assert set(rows) == {f"{pid}:sut" for pid in VALID}
    assert all(r["output"] == "twin ok" for r in rows.values())
    assert all("at org-twin." in c for c in worker.calls)
    assert "standup-decision-kebab" in worker.calls[0]        # twin stream ingested


def _judge(score_dir: Path):
    """Simulated blinded judge: verdicts keyed only by output text."""
    screen_probes.cmd_judge_export(SimpleNamespace(work_dir=score_dir, ids=None))
    pending = json.loads((score_dir / "pending-judge.json").read_text())
    verdicts = {}
    for row in pending:
        assert set(row) == {"id", "criteria", "output"}
        verdicts[row["id"]] = {
            k: (("base" in c and row["output"] == "base ok")
                or ("twin" in c and row["output"] == "twin ok"))
            for k, c in row["criteria"].items()}
    vf = score_dir / "verdicts.json"
    vf.write_text(json.dumps(verdicts))
    screen_probes.cmd_judge_import(SimpleNamespace(work_dir=score_dir, verdicts=vf,
                                                   judge="test-judge"))


def test_run_pilot_end_to_end_cross_seed_summary(tmp_path, monkeypatch):
    datasets = tmp_path / "datasets"
    make_seed(datasets, 1, "org-twin")     # twin side answered -> pair credit 1.0
    make_seed(datasets, 2, "org-other")    # twin side unanswered -> pair credit 0.0
    monkeypatch.setattr(run_pilot, "MockWorker", _worker)
    work = tmp_path / "work"
    argv = ["--system", "nomemory", "--seeds", "1,2", "--work", str(work),
            "--datasets", str(datasets)]
    assert run_pilot.main(["run", *argv, "--dry-run"]) == 0
    for seed in (1, 2):
        p = run_pilot._paths(work, "nomemory", seed, 1)
        assert p["base"].exists() and p["twin"].exists()
        assert (p["score"] / "runs.jsonl").exists()
        _judge(p["score"])
    # resumable: a second run adds no rows
    assert run_pilot.main(["run", *argv, "--dry-run"]) == 0
    p1 = run_pilot._paths(work, "nomemory", 1, 1)
    assert len(p1["base"].read_text().splitlines()) == 4

    assert run_pilot.main(["report", *argv]) == 0
    summary = json.loads((work / "nomemory" / "pilot-summary.json").read_text())
    assert summary["n_valid_instances"] == 8
    seed1 = json.loads(p1["report"].read_text())
    assert all(i["pair_credit"] for i in seed1["instances"].values())
    assert seed1["instances"]["P-0001-01"]["norm_base"] == 1.0
    # rung 2 (A1): seed 1 mean 1.0, seed 2 mean 0.0 -> mean over seeds 0.5
    r2 = summary["by_rung"]["2"]
    assert r2["per_seed_means"] == [1.0, 0.0] and r2["pair_credit_mean"] == 0.5
    assert r2["n_seeds"] == 2 and r2["n_instances"] == 4 and r2["n_clusters"] == 2
    assert summary["by_rung"]["1"]["pair_credit_mean"] == 0.5     # A7
    assert summary["by_archetype"]["A1"]["n_instances"] == 4
    assert "aggregate" in summary["note"] and "overall" not in summary
    assert summary["cost"]["base"]["n_rows"] == 8 and summary["cost"]["twin"]["n_empty"] == 0
    assert set(summary["by_rung"]) == {"1", "2"}


def test_supermemory_registry_freezes_settle_policy():
    # docs/vendor-configs.md (2026-08-27): pilot runs must wait out async ingestion.
    from membench.adapters import MockWorker
    from membench.pilot import build_adapter

    a = build_adapter("supermemory", MockWorker())
    assert a.wait_for_processing is True
    assert a.ingest_settle_seconds == 5 and a.settle_timeout == 600
    # isolation amendment (docs/vendor-configs.md 2026-09-02): run_side passes
    # the org dir name so hosted container tags are disjoint per org side
    b = build_adapter("supermemory", MockWorker(), namespace="org-00001-twin")
    assert b.namespace == "org-00001-twin"
