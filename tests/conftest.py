"""Checks that need material the public repository does not carry.

The public repository is exported from a private one (`scripts/export_public.py`).
A check that needs withheld material skips there, naming the file and the reason,
instead of failing on a missing path. In the private repository every file is
present and every check runs.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]

SEALED = ("the G4 calibration ratings and rater key stay sealed until a second "
          "independent rater has rated the packet")
HOLDOUT = "it reads holdout-seed material, which stays private with the seeds"
HISTORY = ("it reads the dated development record, which lives in "
           "github.com/notmehul/memory-bench-history")
LEDGER = "it needs the ground-truth ledger, which scripts/release.py withholds"
DATASET = ("it needs the dataset; copy it into datasets/dev as the README's "
           "'Get the dataset' section shows")
CONSTRUCTION = ("it exercises dataset-construction tooling, which lives in "
                "github.com/notmehul/memory-bench-history")


def require(rel: str, why: str) -> Path:
    path = ROOT / rel
    if not path.exists():
        pytest.skip(f"{rel} is not in this checkout: {why}")
    return path


def require_ledger(org: str = "org-00001") -> Path:
    path = require(f"datasets/dev/{org}/org.json", LEDGER)
    if not json.loads(path.read_text()).get("facts"):
        pytest.skip(f"datasets/dev/{org}/org.json is redacted: {LEDGER}")
    return path
