"""figures.py: direction rule (>=2/3 seeds), paired H2 math, and the full
report command on a synthetic work dir (radar.svg + results.md)."""

import json
from types import SimpleNamespace

from test_pilot import _load

figures = _load("figures")


def _summary(name, rung_means, per_seed):
    e = {"pair_credit_mean": rung_means, "se": 0.04,
         "ci95": [rung_means - 0.08, rung_means + 0.08],
         "per_seed_means": per_seed, "n_seeds": 3,
         "n_instances": 30, "n_clusters": 10}
    return {"system": name, "seeds": [1, 2, 3], "k": 1, "n_valid_instances": 30,
            "n_empty_deliverables": 0, "by_rung": {"1": e},
            "by_archetype": {a: e for a, _ in figures.AXES}, "by_metric": {},
            "per_seed_reports": {}, "cost": {"base": {"n_rows": 30}}}


def test_direction_calls_only_at_two_of_three_seeds():
    s = {"a": _summary("a", 0.6, [0.6, 0.6, 0.6]),
         "b": _summary("b", 0.5, [0.4, 0.7, 0.4]),   # a beats b in 2/3
         "c": _summary("c", 0.45, [0.5, 0.8, 0.1])}  # b beats c in 1/3 -> tie
    lines = figures.direction(s, "1")
    assert "a > b" in lines[0] and "2/3" in lines[0]
    assert "tie/unstable" in lines[1] and "1/3" in lines[1]


def test_paired_diff_is_cluster_robust_and_cross_seed(tmp_path):
    work = tmp_path
    for name, flip in (("x", True), ("y", False)):
        d = work / name
        d.mkdir()
        reports = {}
        for seed in ("1", "2"):
            inst = {f"p{i}": {"cluster_id": f"c{i // 2}", "pair_credit": flip}
                    for i in range(8)}
            rp = d / f"seed-{seed}.json"
            rp.write_text(json.dumps({"instances": inst}))
            reports[seed] = str(rp)
        (d / "pilot-summary.json").write_text(json.dumps(
            {"per_seed_reports": reports}))
    (line,) = figures.paired(work, "x", "y")
    assert "+1.000" in line and "n=16 paired instances, 2 seeds" in line
    assert "± 0.000" in line   # constant diff -> zero cluster variance


def test_report_writes_radar_and_results(tmp_path):
    for name in ("a", "b"):
        d = tmp_path / name
        d.mkdir()
        (d / "pilot-summary.json").write_text(json.dumps(
            _summary(name, 0.5 if name == "a" else 0.3,
                     [0.5, 0.5, 0.5] if name == "a" else [0.3, 0.3, 0.3])
            | {"cost": {"base": {"n_rows": 30, "n_empty": 0, "worker_seconds": 1.0,
                                 "wall_seconds": 2.0, "context_chars": 100}}}))
    figures.cmd_report(SimpleNamespace(work=tmp_path, systems="a,b",
                                       paired=None, out=None))
    out = tmp_path / "figures"
    assert (out / "radar.svg").stat().st_size > 1000
    md = (out / "results.md").read_text()
    assert "## By rung" in md and "a > b" in md and "## Cost" in md
    assert "never a single aggregate" in md.lower()
