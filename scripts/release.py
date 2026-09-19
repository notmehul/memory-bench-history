"""Build and verify the public release bundle (standards-audit B9; gate G5).

The release ships what a third party needs to RUN the benchmark and SCORE a
system, and withholds what would let them reverse-engineer the answers or
contaminate the holdout seeds.

Shipped, per public seed: the SUT-facing event stream (`events.jsonl`), the
probe set with its assertions (`probes.jsonl`; criteria are required for
scoring, and an open benchmark publishes them), the frozen valid set
(`g3-report.json`), and the counterfactual twin's stream. Plus Croissant +
RAI metadata, the data license, a maintenance plan, and checksums.

Withheld: the ground-truth fact ledger (`org.json`'s `facts`, 126 facts per
seed recording which are probed and which are planted distractors), the
probe plans
(`plan.json`), the template-to-prose provenance (`realization-map.json`), the
annotated scoring stream (`events.annotated.jsonl`), the generator itself, the
unscreened holdout seeds 4-5, and every rater key. `org.json` still ships in
REDACTED form because the runner needs its persona/team/event-witness index to
deliver the stream per principal; `load_ledger` reads `facts` but the runner
never touches it, so the released copy carries `facts: []`.

Canary strings stay embedded in every released stream: a model trained on this
data can be detected by prompting for them (`docs/standards-audit.md` §A).

Usage:
  python scripts/release.py build <out_dir> [--datasets datasets/dev]
  python scripts/release.py verify <out_dir>
"""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
from pathlib import Path

PUBLIC_SEEDS = (1, 2, 3)
HOLDOUT_SEEDS = (4, 5)

BASE_FILES = ("events.jsonl", "probes.jsonl", "g3-report.json")
TWIN_FILES = ("events.jsonl",)

# Never copied into a release, by filename. `verify` fails on any of these.
WITHHELD_NAMES = (
    "plan.json",
    "realization-map.json",
    "events.annotated.jsonl",
    "packet-key.json",
    "KEY-do-not-open.json",
    "rating-template.json",
    "ratings-M.json",
    "rater-M-filled-2026-09-14.xlsx",
    "judge-agreement.json",
)

VERSION = "1.0.0"
# Hosting decided 2026-09-14 (Mehul): HuggingFace. The dataset has no DOI of its
# own; the two papers do (Zenodo, 2026-09-19), and the concept DOIs below always
# resolve to each paper's latest version.
DATASET_URL = "https://huggingface.co/datasets/notmehul/memory-bench"
HOMEPAGE = "https://github.com/notmehul/memory-bench"
HISTORY_URL = "https://github.com/notmehul/memory-bench-history"
PAPER_DOI = "10.5281/zenodo.22838320"
METHODS_DOI = "10.5281/zenodo.22838602"

CITE = (
    "Srivastava, M. (2026). memory-bench: A Screened Benchmark Dataset and "
    "Validity Study for Organizational Memory in Agent Harnesses. Zenodo. "
    f"https://doi.org/{PAPER_DOI}"
)


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def redact_org(src: Path) -> tuple[dict, int]:
    """Strip the ground-truth ledger, keep the witness index the runner needs."""
    data = json.loads(src.read_text())
    n_facts = len(data.get("facts") or [])
    data["facts"] = []
    data["_redacted"] = (
        "Ground-truth fact ledger withheld from the public release "
        "(docs/dataset-plan.md, gate G5). Personas, teams, projects and the "
        "event witness index are retained: the runner needs them to deliver "
        "the stream per principal."
    )
    return data, n_facts


# --------------------------------------------------------------------- build

def _copy_seed(src_root: Path, out: Path, seed: int) -> list[dict]:
    org = f"org-{seed:05d}"
    entries: list[dict] = []
    for name, files in ((org, BASE_FILES), (f"{org}-twin", TWIN_FILES)):
        src, dst = src_root / name, out / "data" / name
        if not src.is_dir():
            raise SystemExit(f"missing source dir {src}")
        dst.mkdir(parents=True, exist_ok=True)
        for fn in files:
            if not (src / fn).is_file():
                raise SystemExit(f"missing {src / fn}")
            shutil.copy2(src / fn, dst / fn)
            entries.append({"path": f"data/{name}/{fn}", "withheld": None})
        redacted, n_facts = redact_org(src / "org.json")
        (dst / "org.json").write_text(json.dumps(redacted, indent=1))
        entries.append({"path": f"data/{name}/org.json",
                        "withheld": f"{n_facts} ground-truth facts"})
    return entries


def _croissant(out: Path, files: list[dict]) -> dict:
    """Croissant 1.0 metadata (NeurIPS D&B / MLCommons)."""
    return {
        "@context": {
            "@vocab": "https://schema.org/",
            "cr": "http://mlcommons.org/croissant/",
            "sc": "https://schema.org/",
            "data": {"@id": "cr:data", "@type": "@json"},
            "dataType": {"@id": "cr:dataType", "@type": "@vocab"},
            "distribution": "cr:distribution",
            "field": "cr:field",
            "fileObject": "cr:fileObject",
            "recordSet": "cr:recordSet",
            "source": "cr:source",
        },
        "@type": "sc:Dataset",
        "conformsTo": "http://mlcommons.org/croissant/1.0",
        "name": "memory-bench",
        "version": VERSION,
        "description": (
            "A screened benchmark for organizational memory in agent harnesses. "
            "Three simulated software organizations, each a multi-week stream of "
            "meetings, messages and documents delivered per principal, with "
            "behavioral work-task probes injected at eval time and scored "
            "against machine-checkable assertions. Every probe instance is "
            "paired with a counterfactual twin: an instance is credited only if "
            "both the base and twin sides pass, so knowledge answerable from "
            "priors earns nothing. 371 valid paired instances across four probe "
            "archetypes, screened under a pinned worker with fully blinded "
            "judging. The ground-truth ledger and two holdout seeds are withheld."
        ),
        "license": "https://creativecommons.org/licenses/by/4.0/",
        "url": HOMEPAGE,
        "citeAs": CITE,
        "identifier": DATASET_URL,
        "keywords": [
            "agent memory", "organizational memory", "continual learning",
            "benchmark", "counterfactual evaluation", "LLM agents",
        ],
        "datePublished": "2026-09-14",
        "distribution": [
            {
                "@type": "cr:FileObject",
                "@id": f["path"],
                "name": f["path"],
                "contentUrl": f["path"],
                "encodingFormat": ("application/jsonlines"
                                   if f["path"].endswith(".jsonl")
                                   else "application/json"),
                "sha256": f["sha256"],
            }
            for f in files
        ],
        "recordSet": [
            {
                "@type": "cr:RecordSet",
                "@id": "events",
                "name": "events",
                "description": (
                    "The SUT-facing event stream, one JSON event per line in "
                    "positional order. Carries no timestamps: temporal order is "
                    "positional throughout (see limitations)."
                ),
                "field": [
                    {"@type": "cr:Field", "@id": "events/event_id",
                     "name": "event_id", "dataType": "sc:Text"},
                    {"@type": "cr:Field", "@id": "events/surface",
                     "name": "surface", "dataType": "sc:Text",
                     "description": "meeting, chat, document or PR"},
                    {"@type": "cr:Field", "@id": "events/content",
                     "name": "content", "dataType": "sc:Text"},
                ],
            },
            {
                "@type": "cr:RecordSet",
                "@id": "probes",
                "name": "probes",
                "description": (
                    "Behavioural work tasks injected after a named event, with "
                    "the assertions they are scored against and the twin "
                    "counterpart that makes pair credit possible."
                ),
                "field": [
                    {"@type": "cr:Field", "@id": "probes/probe_id",
                     "name": "probe_id", "dataType": "sc:Text"},
                    {"@type": "cr:Field", "@id": "probes/archetype",
                     "name": "archetype", "dataType": "sc:Text",
                     "description": "A1 staleness, A2 scope/conflict, "
                                    "A4 working rules, A7 commitments"},
                    {"@type": "cr:Field", "@id": "probes/task",
                     "name": "task", "dataType": "sc:Text"},
                    {"@type": "cr:Field", "@id": "probes/assertions",
                     "name": "assertions", "dataType": "sc:Text"},
                ],
            },
        ],
    }


def _rai(out: Path) -> dict:
    """Responsible AI metadata (MLCommons RAI extension to Croissant)."""
    return {
        "@context": {"@vocab": "http://mlcommons.org/croissant/RAI/"},
        "dataCollection": (
            "Fully synthetic. A seeded generator mints an organization "
            "(personas, teams, projects, policies) and a multi-week event "
            "timeline; an LLM renders each event into prose against a fixed "
            "rendering contract. No real person, company, or communication log "
            "was collected, scraped, or used."
        ),
        "dataCollectionType": "Synthetic generation",
        "dataCollectionRawData": (
            "None. The generator and its seeds are withheld pending the v2 "
            "decision, so the released streams cannot be regenerated by third "
            "parties; regeneration is the project's contamination answer."
        ),
        "dataAnnotationProtocol": (
            "Probe assertions were authored against a computable belief oracle "
            "and screened through a five-gate pipeline (G0-G5). Semantic "
            "verdicts come from a blinded LLM judge that sees only the "
            "deliverable text and a criterion, never the run id, condition, or "
            "side; the judge model is from a different provider than the "
            "worker and never the family that authored the assertions."
        ),
        "dataAnnotationPlatform": (
            "In-repo tooling: scripts/screen_probes.py (blinded export/import), "
            "scripts/calibration.py (human calibration packet)."
        ),
        "dataAnnotationAnalysis": (
            "Judge false-accept rate measured against a 20-decoy adversarial "
            "set: 2/41 as measured, 0/39 after adjudicating two criteria an "
            "under-specified decoy legitimately satisfied. Judge-vs-human "
            "agreement measured on a blinded 150-pair packet (gate G4). "
            "Inter-rater agreement is not reported: v1 used a single "
            "author-rater, a disclosed downgrade."
        ),
        "personalSensitiveInformation": (
            "None. All personas, organizations, and events are fictional. Names "
            "were generated, not sampled from real people. No PII, no "
            "proprietary business content."
        ),
        "dataSocialImpact": (
            "Intended to make memory-system evaluation harder to game. Publishing "
            "the assertions makes the benchmark open-book by construction: a "
            "system tuned against these criteria will score well without "
            "generalizing, which is why the generator and two holdout seeds are "
            "withheld and canary strings are embedded in every stream."
        ),
        "dataLimitations": (
            "Simulated organizations, not real logs. Three screened seeds. "
            "Screening anchors were measured under a single pinned worker "
            "(gpt-5.4, since deprecated by the provider): probe validity is "
            "task-model-relative, measured at 37/54 vs 17/54 cluster survival "
            "across two workers under identical rules, so a different worker "
            "requires its own screening pass. Event streams carry no "
            "timestamps; temporal order is positional. Shared-store "
            "configurations do not enforce per-principal visibility and v1 does "
            "not score leakage."
        ),
        "dataUseCases": (
            "Evaluating whether an agent memory system retains working rules, "
            "drops superseded facts, and resolves scope and authority conflicts "
            "across organizational tiers. Not a general long-context or "
            "chat-memory benchmark."
        ),
        "dataBiases": (
            "Generator-authored facts could in principle be guessable from "
            "priors; counterfactual twin pairing with pass-both-or-zero "
            "crediting structurally cancels this, and the measured memoryless "
            "floor is approximately zero on every capability rung."
        ),
        "dataReleaseMaintenancePlan": (
            "See MAINTENANCE.md. The binding commitment is the re-anchoring "
            "procedure: when the pinned worker becomes unavailable, anchors are "
            "re-screened under a successor by fixed rules with task text "
            "byte-identical, producing a new valid set. Anchors and results "
            "from different workers are never mixed."
        ),
    }


def _maintenance() -> str:
    return """# Maintenance plan

## What can rot, and what we do about it

An agentic benchmark has a dependency no dataset paper usually carries: the
worker model that established what each probe instance is worth. Every
instance here passed a floor gate (a memoryless worker cannot answer it) and a
ceiling gate (a worker given the facts can answer it), both measured under one
pinned worker. Those anchors are not a property of the data alone.

That dependency is not hypothetical. The worker this dataset was screened
under (gpt-5.4, effort medium, codex-cli 0.144.5) was deprecated by its
provider during the study, which is why v1 publishes no comparative system
numbers. The procedure below is what we did about it, written down so a third
party can do it without asking us.

## Re-anchoring procedure

1. **Pick the successor by rule, not by taste.** The nearest same-provider
   successor available at the time the pinned worker became unreachable.
   Record the model id, the reasoning-effort setting, and the exact harness
   version; pin all three the way 0.144.5 was pinned.
2. **Re-run the anchors** for the public seeds under the new pin: floor,
   ceiling, and twin-ceiling for every instance.
3. **Apply the frozen gate rules mechanically.** No criterion edits, no
   adjudications, no re-judging of anything that already has a verdict. Task
   text must stay byte-identical. Verify with the prompt-equality check
   before reusing any cached output.
4. **Publish the new valid set as its own thing.** It will not be the same 371
   instances, and that is the expected result, not a defect: probe validity is
   task-model-relative and we measured how much (37/54 vs 17/54 cluster
   survival across two workers under identical rules).
5. **Never mix.** Anchors from one worker and system results from another
   cannot be combined. Normalization and pair validity both break, and the
   resulting numbers mean nothing.

## Versioning

Semantic versioning on the dataset. A new screened seed or a re-anchored valid
set is a minor version; any change to the streams, probes, or assertions is a
major version and gets a new DOI. Withheld material stays withheld across
versions.

## Contamination

Canary strings are embedded in every released stream. If a model reproduces
one, it has been trained on this data. The generator and the two unscreened
holdout seeds are withheld so fresh organizations can be minted if the public
seeds become contaminated.

## Contact

Issues and correspondence through the repository.
"""


def _readme(manifest: dict) -> str:
    n = manifest["counts"]
    return f"""---
license: cc-by-4.0
pretty_name: memory-bench
language:
  - en
tags:
  - agent-memory
  - organizational-memory
  - benchmark
  - counterfactual-evaluation
  - llm-agents
size_categories:
  - n<1K
configs:
  - config_name: default
    data_files:
      - split: probes
        path: data/org-*/probes.jsonl
---

# memory-bench v{VERSION}, public release

A screened benchmark for organizational memory in agent harnesses: does a
memory system keep a rule that was stated once, drop a fact that was
superseded, and pick the right one when tiers conflict?

**{n['valid_instances']} valid paired probe instances** across {n['public_seeds']} simulated
organizations, drawn from {n['probes']} probes over {n['events']} events. Scored as pair
credit: an instance counts only if the base task and its counterfactual twin
both pass, so anything answerable from priors earns nothing.

## Layout

```
data/org-0000N/        events.jsonl    the stream, one event per line
                       probes.jsonl    work tasks + scoring assertions
                       g3-report.json  the frozen valid set
                       org.json        personas/teams/event witness index
                                       (ground-truth ledger REDACTED)
data/org-0000N-twin/   events.jsonl    counterfactual stream
                       org.json        redacted, as above
croissant.json         dataset metadata (Croissant 1.0)
rai.json               responsible-AI metadata
CHECKSUMS.txt          sha256 of every shipped file
MANIFEST.json          what shipped, what was withheld, and why
MAINTENANCE.md         versioning + the re-anchoring procedure
LICENSE-DATA           CC BY 4.0
```

## What is withheld, and why

The ground-truth fact ledger ({n['facts_withheld']} facts across the public
seeds) stays private: it records which facts are probed and which are planted
distractors, so publishing it would let a system learn the generator's
planting patterns rather than remember the organization. The generator and the
two unscreened holdout seeds are withheld for the same reason. They are the
answer if the public seeds are ever contaminated.

The probe assertions ARE published. Scoring is impossible without them, and an
open benchmark that hides its criteria cannot be checked. This makes the set
open-book by construction: a system tuned against these criteria will score
well here and generalize nowhere, and the canary strings embedded in every
stream are how you detect one that trained on this data.

## A warning about the anchors

Every instance's validity was established under one pinned worker model, which
its provider has since deprecated. Probe validity is task-model-relative: we
measured 37/54 versus 17/54 cluster survival across two workers under
identical rules. **The valid set shipped here is valid relative to that
worker, not in the abstract.** Running a different worker without re-screening
produces numbers that do not mean what they appear to mean. `MAINTENANCE.md`
gives the procedure.

## Papers and code

- Dataset and validity study: [doi:{PAPER_DOI}](https://doi.org/{PAPER_DOI})
- Construction methodology: [doi:{METHODS_DOI}](https://doi.org/{METHODS_DOI})
- Harness, screening and scoring, and the evidence behind every number:
  [{HOMEPAGE.removeprefix("https://")}]({HOMEPAGE})
- Development record: [{HISTORY_URL.removeprefix("https://")}]({HISTORY_URL})

## Citation

{CITE}

## License

Data: CC BY 4.0 (`LICENSE-DATA`). Code in the repository: MIT.
"""


def _license_data() -> str:
    return """Creative Commons Attribution 4.0 International (CC BY 4.0)

Copyright (c) 2026 Mehul Srivastava

This dataset is licensed under the Creative Commons Attribution 4.0
International License. You are free to share and adapt the material for any
purpose, including commercially, provided you give appropriate credit, provide
a link to the license, and indicate if changes were made.

Full license text: https://creativecommons.org/licenses/by/4.0/legalcode
Summary: https://creativecommons.org/licenses/by/4.0/

Attribution: see the citation in README.md.

Code in the memory-bench repository is licensed separately under MIT; see
LICENSE in the repository root.
"""


def cmd_build(args) -> int:
    out: Path = args.out_dir
    if out.exists():
        shutil.rmtree(out)
    out.mkdir(parents=True)

    entries: list[dict] = []
    for seed in PUBLIC_SEEDS:
        entries += _copy_seed(args.datasets, out, seed)

    counts = {"public_seeds": len(PUBLIC_SEEDS), "holdout_seeds": len(HOLDOUT_SEEDS),
              "probes": 0, "events": 0, "valid_instances": 0, "facts_withheld": 0}
    for seed in PUBLIC_SEEDS:
        org = out / "data" / f"org-{seed:05d}"
        counts["probes"] += sum(
            1 for x in (org / "probes.jsonl").read_text().splitlines() if x.strip())
        counts["events"] += sum(
            1 for x in (org / "events.jsonl").read_text().splitlines() if x.strip())
        counts["valid_instances"] += json.loads(
            (org / "g3-report.json").read_text())["n_valid_instances"]
    counts["facts_withheld"] = sum(
        int(e["withheld"].split()[0]) for e in entries
        if e["withheld"] and "facts" in e["withheld"])

    for e in entries:
        e["sha256"] = sha256(out / e["path"])
        e["bytes"] = (out / e["path"]).stat().st_size

    manifest = {
        "name": "memory-bench",
        "version": VERSION,
        "built": "2026-09-14",
        "counts": counts,
        "public_seeds": [f"org-{s:05d}" for s in PUBLIC_SEEDS],
        "withheld": {
            "ground_truth_ledger": "org.json `facts` on every released seed",
            "probe_plans": "plan.json",
            "realization_provenance": "realization-map.json",
            "annotated_scoring_stream": "events.annotated.jsonl",
            "generator": "not released pending the v2 decision",
            "holdout_seeds": [f"org-{s:05d}" for s in HOLDOUT_SEEDS],
            "rater_keys": "packet-key.json, KEY-do-not-open.json",
        },
        "screening_worker": {
            "model": "gpt-5.4", "effort": "medium", "harness": "codex-cli 0.144.5",
            "status": "deprecated by the provider 2026-09; see MAINTENANCE.md",
        },
        "judge": {"model": "claude-sonnet-5", "rubric": "v2", "blinded": True},
        "specs": {"probe_spec": "v0.4.3", "judge_rubric": "v2"},
        "license": {"data": "CC BY 4.0", "code": "MIT"},
        "files": entries,
    }
    (out / "MANIFEST.json").write_text(json.dumps(manifest, indent=1))

    croissant_files = [{"path": e["path"], "sha256": e["sha256"]} for e in entries]
    (out / "croissant.json").write_text(json.dumps(_croissant(out, croissant_files), indent=1))
    (out / "rai.json").write_text(json.dumps(_rai(out), indent=1))
    (out / "MAINTENANCE.md").write_text(_maintenance())
    (out / "README.md").write_text(_readme(manifest))
    (out / "LICENSE-DATA").write_text(_license_data())
    (out / "CHECKSUMS.txt").write_text(
        "".join(f"{e['sha256']}  {e['path']}\n"
                for e in sorted(entries, key=lambda x: x["path"])))

    print(f"release v{VERSION} -> {out}: {counts['valid_instances']} valid instances, "
          f"{counts['probes']} probes, {counts['events']} events across "
          f"{counts['public_seeds']} seeds; {counts['facts_withheld']} ledger facts withheld")
    return 0


# -------------------------------------------------------------------- verify

def cmd_verify(args) -> int:
    out: Path = args.out_dir
    manifest = json.loads((out / "MANIFEST.json").read_text())
    failures: list[str] = []

    for name in WITHHELD_NAMES:
        for hit in out.rglob(name):
            failures.append(f"withheld file present: {hit.relative_to(out)}")

    for e in manifest["files"]:
        p = out / e["path"]
        if not p.is_file():
            failures.append(f"manifest lists a missing file: {e['path']}")
        elif sha256(p) != e["sha256"]:
            failures.append(f"checksum mismatch: {e['path']}")

    for org_dir in sorted((out / "data").iterdir()):
        org = json.loads((org_dir / "org.json").read_text())
        if org.get("facts"):
            failures.append(f"ground-truth ledger leaked in {org_dir.name}/org.json "
                            f"({len(org['facts'])} facts)")
        canaries = org.get("canaries") or []
        stream = (org_dir / "events.jsonl").read_text()
        if not canaries:
            failures.append(f"{org_dir.name}: no canary recorded")
        for c in canaries:
            if c not in stream:
                failures.append(f"{org_dir.name}: canary {c} missing from events.jsonl")

    for required in ("croissant.json", "rai.json", "MAINTENANCE.md", "README.md",
                     "LICENSE-DATA", "CHECKSUMS.txt"):
        if not (out / required).is_file():
            failures.append(f"missing release file: {required}")

    croissant = json.loads((out / "croissant.json").read_text())
    if croissant.get("conformsTo") != "http://mlcommons.org/croissant/1.0":
        failures.append("croissant.json does not declare conformance to Croissant 1.0")
    if len(croissant.get("distribution", [])) != len(manifest["files"]):
        failures.append("croissant.json distribution does not cover every shipped file")

    if failures:
        for f in failures:
            print(f"FAIL {f}")
        print(f"\n{len(failures)} problem(s); release is NOT shippable")
        return 1
    print(f"OK release v{manifest['version']}: {len(manifest['files'])} files, "
          f"checksums match, ledger withheld, canaries present, metadata complete")
    return 0


# ----------------------------------------------------------------------- cli

def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    sub = ap.add_subparsers(dest="cmd", required=True)
    b = sub.add_parser("build")
    b.add_argument("out_dir", type=Path)
    b.add_argument("--datasets", type=Path, default=Path("datasets/dev"))
    v = sub.add_parser("verify")
    v.add_argument("out_dir", type=Path)
    args = ap.parse_args(argv)
    return {"build": cmd_build, "verify": cmd_verify}[args.cmd](args)


if __name__ == "__main__":
    raise SystemExit(main())
