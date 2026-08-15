"""Resolve the pinned codex CLI binary for protocol paths.

The fixed worker is (gpt-5.4, effort medium, codex-cli 0.144.5). The
harness is part of the instrument (harness-sensitivity study,
`datasets/dev/screening/harness-study-2026-07-25/`), so protocol paths
must refuse to run under any other CLI version — package managers upgrade
`codex` silently (observed 2026-08-14: Homebrew moved PATH to 0.147.0).

Resolution order:
  1. `$MEMBENCH_CODEX_BIN` if set;
  2. `codex` on PATH.
`pinned_codex()` verifies `--version` and raises unless it matches
PINNED_VERSION. Non-protocol callers (content authoring, QA) may use
`codex_bin(check=False)`.
"""

from __future__ import annotations

import os
import subprocess

PINNED_VERSION = "0.144.5"
ENV_VAR = "MEMBENCH_CODEX_BIN"


class CodexPinError(RuntimeError):
    pass


def codex_bin(check: bool = True) -> str:
    binary = os.environ.get(ENV_VAR) or "codex"
    if check:
        found = codex_version(binary)
        if found != PINNED_VERSION:
            raise CodexPinError(
                f"protocol path requires codex-cli {PINNED_VERSION}, found "
                f"{found!r} at {binary!r}. Install the pinned version and set "
                f"{ENV_VAR}=<path> (e.g. npm install --prefix ~/.local/codex-"
                f"{PINNED_VERSION} @openai/codex@{PINNED_VERSION})."
            )
    return binary


def pinned_codex() -> str:
    return codex_bin(check=True)


def codex_version(binary: str = "codex") -> str | None:
    try:
        out = subprocess.run([binary, "--version"], capture_output=True,
                             text=True, timeout=30).stdout.strip()
    except (OSError, subprocess.TimeoutExpired):
        return None
    # "codex-cli 0.144.5"
    return out.split()[-1] if out else None
