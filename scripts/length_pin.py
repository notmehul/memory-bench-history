#!/usr/bin/env python3
"""Pin distractor canonical lengths to the probed length distribution.

    python scripts/length_pin.py prep  datasets/dev/org-00001
    # (content agent rewrites _len_edits.json -> _len_edits_done.json)
    python scripts/length_pin.py apply datasets/dev/org-00001

prep assigns each distractor a target word count drawn round-robin from the
(shuffled, seeded) multiset of probed canonical lengths — the two length
distributions become equal by construction, the same trick as position
bands. Facts already at their target are skipped. apply validates the
rewrites (exact word count, numbers preserved, uniqueness) and updates
org.json + realization-map.json.
"""

import json
import random
import re
import sys
from pathlib import Path


def prep(org_dir: Path) -> int:
    org = json.loads((org_dir / "org.json").read_text())
    probed_wcs = sorted(
        len(f["canonical"].split()) for f in org["facts"] if not f["distractor"]
    )
    distractors = sorted(
        (f for f in org["facts"] if f["distractor"]), key=lambda f: f["fact_id"]
    )
    rng = random.Random(org["seed"] + 31)
    targets = [probed_wcs[i % len(probed_wcs)] for i in range(len(distractors))]
    rng.shuffle(targets)
    edits = {}
    for f, target in zip(distractors, targets, strict=True):
        if len(f["canonical"].split()) != target:
            edits[f["canonical"]] = {"target_word_count": target}
    (org_dir / "_len_edits.json").write_text(json.dumps(edits, indent=1))
    print(f"{org_dir.name}: {len(edits)} distractor canonicals to length-pin")
    return 0


def apply(org_dir: Path) -> int:
    spec = json.loads((org_dir / "_len_edits.json").read_text())
    done_path = org_dir / "_len_edits_done.json"
    if spec and not done_path.exists():
        print("no _len_edits_done.json")
        return 1
    edits = json.loads(done_path.read_text()) if spec else {}
    org = json.loads((org_dir / "org.json").read_text())
    existing = {f["canonical"] for f in org["facts"]}
    bad, seen = [], set()
    for old, new in edits.items():
        if new in seen or (new in existing and new != old):
            bad.append(f"duplicate: {new[:60]}")
        seen.add(new)
    good = {}
    failed_spec = {}
    for old, new in edits.items():
        want = spec[old]["target_word_count"]
        ok = (
            len(new.split()) == want
            and set(re.findall(r"\d[\d,.%]*", old))
            == set(re.findall(r"\d[\d,.%]*", new))
        )
        (good if ok else failed_spec).__setitem__(
            old, new if ok else spec[old]
        )
    if failed_spec:
        # apply the good rewrites, leave the failures for a retry round
        edits = good
        (org_dir / "_len_edits.json").write_text(json.dumps(failed_spec, indent=1))
        done_path.unlink(missing_ok=True)
        print(f"{len(good)} applied, {len(failed_spec)} need retry")
    if bad and not failed_spec:
        print("VALIDATION FAILED:")
        for b in bad[:10]:
            print("  -", b)
        return 1
    mapping = json.loads((org_dir / "realization-map.json").read_text())
    for f in org["facts"]:
        if f["canonical"] in edits:
            f["canonical"] = edits[f["canonical"]]
    for tpl, prose in list(mapping.items()):
        if prose in edits:
            mapping[tpl] = edits[prose]
    (org_dir / "org.json").write_text(json.dumps(org, indent=1))
    (org_dir / "realization-map.json").write_text(json.dumps(mapping, indent=1))
    if not (org_dir / "_len_edits.json").exists() or not failed_spec:
        (org_dir / "_len_edits.json").unlink(missing_ok=True)
    done_path.unlink(missing_ok=True)
    print(f"{org_dir.name}: {len(edits)} canonicals length-pinned")
    return 3 if failed_spec else 0


if __name__ == "__main__":
    cmd, org_dir = sys.argv[1], Path(sys.argv[2])
    sys.exit(prep(org_dir) if cmd == "prep" else apply(org_dir))
