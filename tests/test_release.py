"""Release bundle: redaction, metadata, and the checks that keep answers out."""

import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

import release  # noqa: E402


def _seed_dir(root: Path, seed: int, *, twin: bool = False) -> Path:
    name = f"org-{seed:05d}" + ("-twin" if twin else "")
    d = root / name
    d.mkdir(parents=True)
    canary = f"mb-canary-{seed:05d}-deadbeef"
    org = {
        "org_id": f"org-{seed:05d}",
        "seed": seed,
        "generator_version": "v0.4",
        "difficulty": "L2",
        "entities": {
            "personas": [{"id": "persona:alice", "role": "engineer",
                          "authority_level": 2, "teams": ["team:eng"]}],
            "teams": [{"id": "team:eng", "members": ["persona:alice"]}],
            "projects": [],
        },
        "events": [{"event_id": "E-0001", "surface": "org/all-hands",
                    "visibility": "org_public", "participants": ["persona:alice"]}],
        "facts": [{"fact_id": "F-0001", "canonical": "the secret answer"},
                  {"fact_id": "F-0002", "canonical": "a planted distractor"}],
        "canaries": [canary],
    }
    (d / "org.json").write_text(json.dumps(org))
    (d / "events.jsonl").write_text(json.dumps({
        "event_id": "E-0001", "surface": "org/all-hands",
        "content": f"all-hands notes {canary}"}) + "\n")
    # withheld-by-policy files that must never reach a release
    (d / "events.annotated.jsonl").write_text("{}\n")
    if not twin:
        (d / "plan.json").write_text("{}")
        (d / "realization-map.json").write_text("{}")
        (d / "probes.jsonl").write_text(json.dumps({
            "probe_id": "P-0001-01", "archetype": "A4", "task": "write a checklist",
            "assertions": [{"id": "asrt-1", "criterion": "names an owner"}]}) + "\n")
        (d / "g3-report.json").write_text(json.dumps({"n_valid_instances": 1}))
    return d


@pytest.fixture
def datasets(tmp_path: Path) -> Path:
    root = tmp_path / "datasets"
    for seed in release.PUBLIC_SEEDS:
        _seed_dir(root, seed)
        _seed_dir(root, seed, twin=True)
    return root


@pytest.fixture
def built(tmp_path: Path, datasets: Path) -> Path:
    out = tmp_path / "release"
    assert release.main(["build", str(out), "--datasets", str(datasets)]) == 0
    return out


def test_build_ships_streams_probes_and_valid_sets(built: Path):
    for seed in release.PUBLIC_SEEDS:
        base = built / "data" / f"org-{seed:05d}"
        for fn in (*release.BASE_FILES, "org.json"):
            assert (base / fn).is_file()
        twin = built / "data" / f"org-{seed:05d}-twin"
        for fn in (*release.TWIN_FILES, "org.json"):
            assert (twin / fn).is_file()


def test_ledger_is_redacted_but_witness_index_survives(built: Path):
    org = json.loads((built / "data" / "org-00001" / "org.json").read_text())
    assert org["facts"] == []
    assert "the secret answer" not in json.dumps(org)
    # the runner needs these, so redaction must not touch them
    assert org["entities"]["personas"] and org["events"]
    assert org["canaries"]


def test_withheld_files_never_ship(built: Path):
    for name in release.WITHHELD_NAMES:
        assert not list(built.rglob(name)), f"{name} leaked into the release"


def test_manifest_counts_and_metadata(built: Path):
    m = json.loads((built / "MANIFEST.json").read_text())
    assert m["counts"]["valid_instances"] == len(release.PUBLIC_SEEDS)
    # 2 facts per org side, base + twin, per seed
    assert m["counts"]["facts_withheld"] == 4 * len(release.PUBLIC_SEEDS)
    assert m["license"] == {"data": "CC BY 4.0", "code": "MIT"}
    assert m["screening_worker"]["model"] == "gpt-5.4"
    croissant = json.loads((built / "croissant.json").read_text())
    assert croissant["conformsTo"] == "http://mlcommons.org/croissant/1.0"
    assert croissant["license"].startswith("https://creativecommons.org/licenses/by/4.0")
    rai = json.loads((built / "rai.json").read_text())
    assert "Synthetic" in rai["dataCollectionType"]
    assert rai["dataReleaseMaintenancePlan"]


def test_verify_passes_on_a_clean_build(built: Path, capsys):
    assert release.main(["verify", str(built)]) == 0
    assert "OK release" in capsys.readouterr().out


def test_verify_catches_a_leaked_ledger(built: Path, capsys):
    p = built / "data" / "org-00002" / "org.json"
    org = json.loads(p.read_text())
    org["facts"] = [{"fact_id": "F-0001", "canonical": "the secret answer"}]
    p.write_text(json.dumps(org))
    assert release.main(["verify", str(built)]) == 1
    assert "ground-truth ledger leaked" in capsys.readouterr().out


def test_verify_catches_a_missing_canary(built: Path, capsys):
    p = built / "data" / "org-00003" / "events.jsonl"
    p.write_text(p.read_text().replace("mb-canary-00003-deadbeef", "scrubbed"))
    assert release.main(["verify", str(built)]) == 1
    assert "canary" in capsys.readouterr().out


def test_verify_catches_a_tampered_file(built: Path, capsys):
    p = built / "data" / "org-00001" / "probes.jsonl"
    p.write_text(p.read_text() + json.dumps({"probe_id": "P-9999-01"}) + "\n")
    assert release.main(["verify", str(built)]) == 1
    assert "checksum mismatch" in capsys.readouterr().out


def test_verify_catches_a_reintroduced_withheld_file(built: Path, capsys):
    (built / "data" / "org-00001" / "plan.json").write_text("{}")
    assert release.main(["verify", str(built)]) == 1
    assert "withheld file present" in capsys.readouterr().out
