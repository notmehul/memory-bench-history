#!/usr/bin/env python3
"""Blinded salience check: prep a sample or score an answer file.

    python scripts/blind_check.py prep  datasets/dev/org-00003 out.json key.json
    python scripts/blind_check.py score key.json answers.json

Sampling excludes same-topic siblings within one sample (a rater who sees
both members of a probed/near-miss pair can compare them directly, which
tests relative phrasing rather than class distinguishability).
"""

import json
import random
import sys
from pathlib import Path

from membench.realize import load_annotated

BAR = 0.65


def prep(org_dir: Path, out: Path, key_out: Path) -> int:
    org = json.loads((org_dir / "org.json").read_text())
    facts = {f["fact_id"]: f for f in org["facts"]}
    events = load_annotated(org_dir / "events.annotated.jsonl")
    rng = random.Random(org["seed"] + 777)
    pool: dict[bool, list] = {True: [], False: []}
    for e in events:
        for s in e["_annotations"]["embeds_facts"]:
            f = facts[s["fact_id"]]
            pool[not f["distractor"]].append(
                (f.get("topic", ""), e["content"][s["span"][0]:s["span"][1]])
            )
    pick, used_topics = [], set()
    for cls in (True, False):
        rng.shuffle(pool[cls])
        chosen = []
        for topic, text in pool[cls]:
            if topic in used_topics:
                continue
            used_topics.add(topic)
            chosen.append((text, cls))
            if len(chosen) == 10:
                break
        pick += chosen
    rng.shuffle(pick)
    out.write_text(json.dumps(
        [{"id": i + 1, "text": t} for i, (t, _) in enumerate(pick)], indent=1))
    key_out.write_text(json.dumps({i + 1: c for i, (_, c) in enumerate(pick)}))
    print(f"prepped 20 excerpts from {org_dir.name}")
    return 0


def score(key_path: Path, ans_path: Path) -> int:
    key = {int(k): v for k, v in json.loads(key_path.read_text()).items()}
    ans = {int(k): v for k, v in json.loads(ans_path.read_text()).items()}
    correct = sum((ans.get(i) == "probed") == key[i] for i in key)
    acc = correct / len(key)
    verdict = "PASS" if acc < BAR else "FAIL"
    print(f"blinded rater: {correct}/{len(key)} = {acc:.0%} (bar <{BAR:.0%}) -> {verdict}")
    return 0 if acc < BAR else 1


if __name__ == "__main__":
    cmd = sys.argv[1]
    if cmd == "prep":
        sys.exit(prep(Path(sys.argv[2]), Path(sys.argv[3]), Path(sys.argv[4])))
    sys.exit(score(Path(sys.argv[2]), Path(sys.argv[3])))
