"""Phase 4 calibration tooling (scripts/calibration.py).

Pins: blinded packet (no run ids / conditions / sides), deterministic stratified
sampling under the per-cluster cap, kappa math against hand-computed values, and
rating-file validation.
"""

import importlib.util
import json
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest
from conftest import SEALED, require  # noqa: E402

AGREEMENT = "datasets/dev/calibration/judge-agreement.json"

_SPEC = importlib.util.spec_from_file_location(
    "calibration",
    Path(__file__).resolve().parents[1] / "scripts" / "calibration.py",
)
calibration = importlib.util.module_from_spec(_SPEC)
sys.modules["calibration"] = calibration
_SPEC.loader.exec_module(calibration)


def _screening_fixture(tmp_path: Path) -> Path:
    """3 clusters x 2 instances x 3 conditions; semantic + pattern assertions."""
    runs, results, judgements = [], [], []
    body = 0
    for c in range(1, 4):
        cid = f"P-{c:04d}"
        for inst in (1, 2):
            probe = f"{cid}-0{inst}"
            for cond in ("ceiling", "twin_ceiling", "floor"):
                rid = f"{probe}:{cond}"
                assertions = [
                    {"id": "asrt-1", "kind": "fact_applied", "checker": "semantic",
                     "criterion": f"states the cadence variant {c}", "weight": 1.0},
                    {"id": "asrt-2", "kind": "fact_absent", "checker": "pattern",
                     "criterion": "kebab", "weight": 1.0},
                ]
                row = {"run_id": rid, "cluster_id": cid, "probe_id": probe,
                       "condition": cond, "prompt": "task text", "assertions": assertions}
                verdicts = {"asrt-1": inst == 1}
                if cond == "floor":
                    row["cf_assertions"] = [
                        {"id": "casrt-1", "kind": "scope_correct", "checker": "semantic",
                         "criterion": f"reflects the alternate scope {c}", "weight": 1.0}]
                    verdicts["casrt-1"] = inst == 1
                runs.append(row)
                body += 1
                results.append({"run_id": rid, "output": f"neutral deliverable body {body}"})
                judgements.append({"run_id": rid, "verdicts": verdicts, "judge": "test"})
    d = tmp_path / "screening"
    d.mkdir()
    for name, rows in (("runs", runs), ("results", results), ("judgements", judgements)):
        (d / f"{name}.jsonl").write_text("".join(json.dumps(r) + "\n" for r in rows))
    return d


def _sample(tmp_path: Path, n: int, seed: int = 20260725) -> Path:
    out = tmp_path / f"cal-{n}-{seed}"
    if not (tmp_path / "screening").exists():
        _screening_fixture(tmp_path)
    calibration.cmd_sample(SimpleNamespace(
        screening_dirs=[tmp_path / "screening"], out_dir=out, n=n, seed=seed))
    return out


def test_packet_is_blind_and_capped(tmp_path):
    out = _sample(tmp_path, n=10)
    packet = json.loads((out / "rater-packet.json").read_text())
    key = json.loads((out / "packet-key.json").read_text())
    # cap: 3 clusters x 2 = 6 max, so the n=10 request must shrink to 6
    assert len(packet) == 6
    per_cluster = {}
    for ref in key.values():
        cid = (ref["org"], ref["run_id"][:6])
        per_cluster[cid] = per_cluster.get(cid, 0) + 1
    assert all(v <= calibration.CLUSTER_CAP for v in per_cluster.values())
    blob = json.dumps(packet)
    for leak in ("P-000", "asrt", "casrt", "ceiling", "floor", "twin", ":"):
        assert leak not in blob.replace('": ', "").replace('":', ""), leak
    assert set(json.loads((out / "rating-template.json").read_text())) == \
        {row["id"] for row in packet}


def test_sampling_deterministic(tmp_path):
    a = _sample(tmp_path, n=6, seed=7)
    b_dir = tmp_path / "again"
    calibration.cmd_sample(SimpleNamespace(
        screening_dirs=[tmp_path / "screening"], out_dir=b_dir, n=6, seed=7))
    assert (a / "rater-packet.json").read_text() == (b_dir / "rater-packet.json").read_text()


def test_multi_org_pooling_disambiguates(tmp_path):
    import shutil
    _screening_fixture(tmp_path)
    shutil.copytree(tmp_path / "screening", tmp_path / "org-a")
    shutil.copytree(tmp_path / "screening", tmp_path / "org-b")
    out = tmp_path / "pooled"
    calibration.cmd_sample(SimpleNamespace(
        screening_dirs=[tmp_path / "org-a", tmp_path / "org-b"], out_dir=out, n=12, seed=1))
    packet = json.loads((out / "rater-packet.json").read_text())
    key = json.loads((out / "packet-key.json").read_text())
    # two identical orgs double the cap headroom, and opaque ids never collide
    assert len(packet) == 12
    assert len({row["id"] for row in packet}) == 12
    assert {ref["org"] for ref in key.values()} == {"org-a", "org-b"}
    with pytest.raises(SystemExit, match="distinct basenames"):
        calibration.cmd_sample(SimpleNamespace(
            screening_dirs=[tmp_path / "org-a", tmp_path / "org-a"],
            out_dir=tmp_path / "dup", n=4, seed=1))


def test_kappa_hand_computed(tmp_path):
    out = _sample(tmp_path, n=6)
    ids = [r["id"] for r in json.loads((out / "rater-packet.json").read_text())]
    a = dict(zip(ids, [True, True, True, False, False, False], strict=True))
    b = dict(zip(ids, [True, True, False, False, False, True], strict=True))
    (out / "a.json").write_text(json.dumps(a))
    (out / "b.json").write_text(json.dumps(b))
    calibration.cmd_kappa(SimpleNamespace(
        out_dir=out, ratings_a=out / "a.json", ratings_b=out / "b.json"))
    rep = json.loads((out / "kappa-report.json").read_text())
    # po = 4/6, pe = .5*.5 + .5*.5 = .5, kappa = (2/3 - 1/2)/(1/2) = 1/3
    assert rep["raw_agreement"] == pytest.approx(0.6667, abs=1e-3)
    assert rep["kappa"] == pytest.approx(0.3333, abs=1e-3)
    assert not rep["degenerate_marginals"]
    assert len(rep["disagreements"]) == 2


def test_kappa_degenerate_all_same_label(tmp_path):
    out = _sample(tmp_path, n=6)
    ids = [r["id"] for r in json.loads((out / "rater-packet.json").read_text())]
    same = {i: True for i in ids}
    (out / "a.json").write_text(json.dumps(same))
    (out / "b.json").write_text(json.dumps(same))
    calibration.cmd_kappa(SimpleNamespace(
        out_dir=out, ratings_a=out / "a.json", ratings_b=out / "b.json"))
    rep = json.loads((out / "kappa-report.json").read_text())
    assert rep["degenerate_marginals"] and rep["kappa"] == 1.0


def test_rating_validation_errors(tmp_path):
    out = _sample(tmp_path, n=6)
    ids = [r["id"] for r in json.loads((out / "rater-packet.json").read_text())]
    incomplete = {i: True for i in ids[:-1]}
    (out / "a.json").write_text(json.dumps(incomplete))
    with pytest.raises(SystemExit, match="do not match"):
        calibration._load_ratings(out / "a.json", set(ids), "ratings_a")
    nonbool = {i: "yes" for i in ids}
    (out / "b.json").write_text(json.dumps(nonbool))
    with pytest.raises(SystemExit, match="non-boolean"):
        calibration._load_ratings(out / "b.json", set(ids), "ratings_b")


def test_judge_agreement_flags_flipped_criterion(tmp_path):
    out = _sample(tmp_path, n=6)
    key = json.loads((out / "packet-key.json").read_text())
    screening = tmp_path / "screening"
    judgements = {json.loads(x)["run_id"]: json.loads(x)
                  for x in (screening / "judgements.jsonl").read_text().splitlines()}
    gold = {pid: judgements[ref["run_id"]]["verdicts"][ref["assertion_id"]]
            for pid, ref in key.items()}
    flip = sorted(gold)[0]
    gold[flip] = not gold[flip]
    (out / "gold.json").write_text(json.dumps(gold))
    calibration.cmd_judge_agreement(SimpleNamespace(
        out_dir=out, adjudicated=out / "gold.json", screening_dirs=[screening]))
    rep = json.loads((out / "judge-agreement.json").read_text())
    assert rep["n"] == 6
    assert rep["raw_agreement"] == pytest.approx(5 / 6, abs=1e-3)
    flipped_ref = key[flip]
    assert any(b["assertion_id"] == flipped_ref["assertion_id"] and
               b["cluster_id"] == flipped_ref["run_id"][:6]
               for b in rep["criteria_below_threshold"])
    assert set(rep["per_kind"]) <= {"fact_applied", "scope_correct"}


# --------------------------------------------------------------- kappa bootstrap
# Added 2026-09-17 for `_bootstrap_kappa_ci`, the post-hoc cluster bootstrap on
# the G4 packet. The interval is a reporting addition: it must reproduce, it must
# resample at cluster level, and it must not be able to move a gate.

ROOT = Path(__file__).resolve().parents[1]
CALIBRATION_DIR = ROOT / "datasets" / "dev" / "calibration"


def _g4_rows() -> list[dict]:
    """The 150 committed calibration pairs, in the shape cmd_judge_agreement builds.

    Rebuilt from the packet key, the rater's submitted labels and the screening
    judgements, so a test failure here means the inputs moved, not the report.
    """
    def jsonl(p: Path) -> list[dict]:
        return [json.loads(x) for x in p.read_text().splitlines() if x.strip()]

    key = json.loads((CALIBRATION_DIR / "packet-key.json").read_text())
    gold = json.loads((CALIBRATION_DIR / "ratings-M.json").read_text())
    cache, rows = {}, []
    for pid, ref in sorted(key.items()):
        org = ref["org"]
        if org not in cache:
            d = ROOT / "datasets" / "dev" / "screening" / org
            cache[org] = ({r["run_id"]: r for r in jsonl(d / "runs.jsonl")},
                          {r["run_id"]: r for r in jsonl(d / "judgements.jsonl")})
        runs, judged = cache[org]
        run = runs[ref["run_id"]]
        a = next(x for x in run["assertions"] + (run.get("cf_assertions") or [])
                 if x["id"] == ref["assertion_id"])
        rows.append({"human": gold[pid],
                     "judge": bool(judged[ref["run_id"]]["verdicts"][ref["assertion_id"]]),
                     "kind": a["kind"], "cluster": (org, run["cluster_id"])})
    return rows


def _kappa_of(rows: list[dict]):
    return calibration._cohens_kappa([r["human"] for r in rows], [r["judge"] for r in rows])


def _width(report: dict) -> float:
    lo, hi = report["ci95"]
    return hi - lo


def test_g4_point_estimates_are_untouched_by_the_bootstrap():
    """Control: the re-analysis reproduces the known numbers before reporting new ones.

    The bootstrap was added after G4 was measured. If it had perturbed the inputs
    or the kappa path, these four values would move, and the gate with them.
    """
    committed = json.loads(require(AGREEMENT, SEALED).read_text())
    rows = _g4_rows()
    po, kappa, degenerate = _kappa_of(rows)
    assert len(rows) == committed["n"] == 150
    assert round(po, 4) == committed["raw_agreement"] == 0.8133
    assert round(kappa, 4) == committed["kappa"] == 0.537
    assert degenerate is False and committed["degenerate_marginals"] is False
    assert committed["gate_g4_overall"] is False, \
        "gate flipped: update the paper and the decision log, not this test"


def test_bootstrap_ci_reproduces_the_committed_artifact():
    """The committed interval re-derives exactly from the same rows and seed."""
    committed = json.loads(require(AGREEMENT, SEALED).read_text())
    rows = _g4_rows()
    got = calibration._bootstrap_kappa_ci(rows)
    assert got == committed["kappa_bootstrap"]
    assert got["ci95"] == [0.3701, 0.6883]
    assert got["seed"] == calibration.BOOTSTRAP_SEED == 20260917
    assert got["replicates"] == calibration.BOOTSTRAP_B == 10000
    assert got["n_clusters"] == 89
    # the upper bound is what makes the FAIL robust rather than marginal
    assert got["ci95"][1] < 0.75
    # and it is deterministic: the same rows and seed twice give the same interval
    assert calibration._bootstrap_kappa_ci(rows) == got


def test_bootstrap_resamples_clusters_not_items():
    """Would fail if the resampling unit were switched to the item.

    The same 100 rows are bootstrapped twice: once with five correlated rows per
    cluster, once with every row in a cluster of its own. An item-level bootstrap
    cannot tell those two apart, so it would return the same interval for both.
    Resampling clusters must return a decisively wider one for the grouped data.
    """
    def rows(grouped: bool) -> list[dict]:
        out = []
        for c in range(20):
            for i in range(5):
                human = (c + i) % 2 == 0
                # clusters 0-13 agree throughout, 14-19 disagree throughout
                judge = human if c < 14 else not human
                out.append({"human": human, "judge": judge, "kind": "fact_applied",
                            "cluster": ("o", f"C{c}") if grouped else ("o", f"C{c}-{i}")})
        return out

    by_cluster = calibration._bootstrap_kappa_ci(rows(True), b=2000)
    by_item = calibration._bootstrap_kappa_ci(rows(False), b=2000)
    assert by_cluster["n_clusters"] == 20 and by_item["n_clusters"] == 100
    # identical point estimate, so any difference is the resampling unit alone
    assert _kappa_of(rows(True))[1] == _kappa_of(rows(False))[1]
    assert _width(by_cluster) > 2 * _width(by_item), (by_cluster, by_item)


def test_bootstrap_counts_degenerate_replicates():
    """Replicates with no chance-corrected kappa are reported, not dropped."""
    rows = []
    for c in range(3):
        for i in range(4):
            if c < 2:  # both raters label everything True in these two clusters
                rows.append({"human": True, "judge": True, "kind": "fact_applied",
                             "cluster": ("o", f"D{c}")})
            else:
                rows.append({"human": i % 2 == 0, "judge": i < 2, "kind": "fact_applied",
                             "cluster": ("o", f"D{c}")})
    got = calibration._bootstrap_kappa_ci(rows, b=1000)
    # a replicate drawing only the two all-True clusters has pe = 1; that is
    # (2/3)^3 ~ 30% of replicates, and every one of them must be counted
    assert 200 < got["degenerate_replicates"] < 400, got
    assert got["replicates"] == 1000
    assert len(got["ci95"]) == 2


def test_gate_verdict_ignores_the_bootstrap_interval(tmp_path):
    """The gate reads the point estimate. A wide interval must not rescue a FAIL.

    This fixture sits where it matters: kappa 0.667 is below the 0.75 gate while
    the bootstrap upper bound reaches 1.0, so a gate computed from the interval
    would report PASS.
    """
    out = _sample(tmp_path, n=6)
    key = json.loads((out / "packet-key.json").read_text())
    screening = tmp_path / "screening"
    judgements = {json.loads(x)["run_id"]: json.loads(x)
                  for x in (screening / "judgements.jsonl").read_text().splitlines()}
    gold = {pid: judgements[ref["run_id"]]["verdicts"][ref["assertion_id"]]
            for pid, ref in key.items()}
    gold[sorted(gold)[0]] = not gold[sorted(gold)[0]]
    (out / "gold.json").write_text(json.dumps(gold))
    calibration.cmd_judge_agreement(SimpleNamespace(
        out_dir=out, adjudicated=out / "gold.json", screening_dirs=[screening]))
    rep = json.loads((out / "judge-agreement.json").read_text())
    assert rep["kappa"] == pytest.approx(0.6667, abs=1e-3)
    assert rep["kappa_bootstrap"]["ci95"][1] >= 0.75
    assert rep["gate_g4_overall"] is False
    assert rep["gate_g4_overall"] == (rep["kappa"] >= 0.75)
    # per kind carries an interval too, and it is likewise verdict-free
    for kind in rep["per_kind"].values():
        assert set(kind["kappa_bootstrap"]) == {
            "ci95", "replicates", "seed", "n_clusters", "degenerate_replicates"}
