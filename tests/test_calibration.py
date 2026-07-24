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
