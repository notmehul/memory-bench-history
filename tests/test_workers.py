"""CodexWorker transport: pinned flags, retry, timeout — no live codex calls."""

import subprocess
from pathlib import Path

import pytest

from membench.workers import (
    EFFORT,
    MODEL,
    RUN_TIMEOUT,
    TRANSPORT_INSTRUCTION,
    CodexWorker,
    WorkerError,
)


@pytest.fixture(autouse=True)
def _stub_pin(monkeypatch):
    # The version pin is exercised in test_codex_bin.py; here we test transport.
    monkeypatch.setattr("membench.workers.pinned_codex", lambda: "codex")


class FakeRun:
    """Scriptable subprocess.run stand-in: per-call output.md contents
    (None = write nothing, "" = write empty, "TIMEOUT" sentinel = raise)."""

    def __init__(self, scripts):
        self.scripts = list(scripts)
        self.calls = []

    def __call__(self, argv, **kwargs):
        self.calls.append((argv, kwargs))
        action = self.scripts.pop(0)
        if action == "TIMEOUT":
            raise subprocess.TimeoutExpired(argv, kwargs["timeout"])
        if action is not None:
            cwd = Path(argv[argv.index("-C") + 1])
            (cwd / "output.md").write_text(action)


def test_success_path_and_pinned_transport(monkeypatch):
    fake = FakeRun(["the deliverable\n"])
    monkeypatch.setattr("membench.workers.subprocess.run", fake)
    worker = CodexWorker()
    assert worker.complete("Task: write a note") == "the deliverable"
    assert worker.counters["calls"] == 1
    argv, kwargs = fake.calls[0]
    assert argv[0:2] == ["codex", "exec"]
    assert argv[argv.index("-m") + 1] == MODEL == "gpt-5.4"
    assert f"model_reasoning_effort={EFFORT}" in argv
    assert EFFORT == "medium"
    assert "-s" in argv and argv[argv.index("-s") + 1] == "workspace-write"
    assert "--skip-git-repo-check" in argv
    assert argv[-1] == "-"
    assert kwargs["timeout"] == RUN_TIMEOUT == 360
    assert kwargs["input"].startswith("Task: write a note")
    assert kwargs["input"].endswith(TRANSPORT_INSTRUCTION)


def test_retry_on_empty_then_success(monkeypatch):
    fake = FakeRun([None, "second try wins"])
    monkeypatch.setattr("membench.workers.subprocess.run", fake)
    worker = CodexWorker()
    assert worker.complete("p") == "second try wins"
    assert len(fake.calls) == 2
    assert worker.counters["calls"] == 1


def test_timeout_raises_clear_error(monkeypatch):
    fake = FakeRun(["TIMEOUT", "TIMEOUT"])
    monkeypatch.setattr("membench.workers.subprocess.run", fake)
    worker = CodexWorker()
    with pytest.raises(WorkerError, match="after 2 attempts: timeout"):
        worker.complete("p")
    assert len(fake.calls) == 2
    assert worker.counters["calls"] == 1


def test_files_are_materialized_in_workdir_and_cannot_escape(monkeypatch):
    seen = {}

    class Recorder(FakeRun):
        def __call__(self, argv, **kwargs):
            cwd = Path(argv[argv.index("-C") + 1])
            seen["hist"] = (cwd / "history" / "00001_e.md").read_text()
            return super().__call__(argv, **kwargs)

    fake = Recorder(["ok"])
    monkeypatch.setattr("membench.workers.subprocess.run", fake)
    assert CodexWorker().complete("p", files={"history/00001_e.md": "event text"}) == "ok"
    assert seen["hist"] == "event text"
    with pytest.raises(WorkerError, match="escapes workdir"):
        CodexWorker().complete("p", files={"../evil.md": "x"})
