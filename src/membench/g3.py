"""Read the frozen G3 verdicts (`<org_dir>/g3-report.json`).

Only VALID instances of SURVIVING clusters ship (probe-spec §3, screening
report): the v1 freeze counts 371 such instances across seeds 1–3
(125 + 131 + 115). Instances flagged valid inside a dropped cluster
(9 across the three seeds) are excluded — a cluster that failed G3 does not
ship any of its instances.
"""

from __future__ import annotations

import json
from pathlib import Path


def valid_instances(report: dict) -> set[str]:
    return {pid
            for c in report["clusters"].values() if c.get("survive", True)
            for pid, i in c["instances"].items() if i["valid"]}


def load_valid_instances(org_dir: Path) -> set[str]:
    return valid_instances(json.loads((org_dir / "g3-report.json").read_text()))
