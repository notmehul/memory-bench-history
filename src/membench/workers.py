"""Worker implementations behind the `WorkerModel` protocol.

`CodexWorker` is the PINNED fixed task model — (gpt-5.4, effort medium,
codex-cli 0.144.5) per the dataset-plan standing decisions. The CLI version
pin is a protocol constraint: the harness is part of the instrument
(harness-sensitivity study, `datasets/dev/screening/harness-study-2026-07-25/`).
Transport mirrors `scripts/screen_probes.py`'s run path exactly so SUT runs
stay comparable to the committed floor/ceiling anchors: per-call temp
working dir, deliverable captured from `output.md` (never stdout), one
retry on empty/missing output or timeout.
"""

from __future__ import annotations

import subprocess
import tempfile
import time
from dataclasses import dataclass, field
from pathlib import Path

from .codex_bin import pinned_codex

MODEL = "gpt-5.4"
EFFORT = "medium"
RUN_TIMEOUT = 360

# Exact wording from the screening scaffold (screen_probes.py `_prompt`);
# the runner's task prompts deliberately omit it — transport belongs here.
TRANSPORT_INSTRUCTION = (
    "Write the deliverable to a file named output.md in the current "
    "directory."
)


class WorkerError(Exception):
    pass


@dataclass
class CodexWorker:
    """The pinned worker. `complete` is a pure prompt -> deliverable call."""

    counters: dict = field(default_factory=lambda: {"calls": 0, "seconds": 0.0})

    def complete(self, prompt: str, files: dict[str, str] | None = None) -> str:
        """`files` (relative path -> text) are materialized in the per-call
        working directory before the call — the seam tools-baseline adapters
        (grep-agent) use; codex's own file tools do the rest."""
        full = f"{prompt}\n\n{TRANSPORT_INSTRUCTION}"
        started = time.monotonic()
        last_err = "no output.md produced"
        codex = pinned_codex()
        try:
            for _ in range(2):
                with tempfile.TemporaryDirectory(prefix="mbworker-") as tmp:
                    tmp_path = Path(tmp)
                    for rel, text in (files or {}).items():
                        target = (tmp_path / rel).resolve()
                        if tmp_path.resolve() not in target.parents:
                            raise WorkerError(f"file path escapes workdir: {rel}")
                        target.parent.mkdir(parents=True, exist_ok=True)
                        target.write_text(text)
                    try:
                        subprocess.run(
                            [codex, "exec", "-C", str(tmp_path),
                             "-s", "workspace-write", "--skip-git-repo-check",
                             "-m", MODEL,
                             "-c", f"model_reasoning_effort={EFFORT}", "-"],
                            input=full, text=True, capture_output=True,
                            timeout=RUN_TIMEOUT,
                        )
                    except subprocess.TimeoutExpired:
                        last_err = "timeout"
                        continue
                    out = tmp_path / "output.md"
                    if out.exists() and out.read_text().strip():
                        return out.read_text().strip()
            raise WorkerError(f"codex worker failed after 2 attempts: {last_err}")
        finally:
            self.counters["calls"] += 1
            self.counters["seconds"] += time.monotonic() - started
