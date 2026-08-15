"""Pinned codex-cli resolution: protocol paths refuse any other version."""

import pytest

from membench import codex_bin
from membench.codex_bin import (
    ENV_VAR,
    PINNED_VERSION,
    CodexPinError,
    codex_version,
    pinned_codex,
)


def _fake_version(table):
    return lambda binary="codex": table.get(binary)


def test_pinned_accepts_exact_version(monkeypatch):
    monkeypatch.delenv(ENV_VAR, raising=False)
    monkeypatch.setattr(codex_bin, "codex_version",
                        _fake_version({"codex": PINNED_VERSION}))
    assert pinned_codex() == "codex"


def test_pinned_rejects_upgraded_path_binary(monkeypatch):
    monkeypatch.delenv(ENV_VAR, raising=False)
    monkeypatch.setattr(codex_bin, "codex_version",
                        _fake_version({"codex": "0.147.0"}))
    with pytest.raises(CodexPinError, match="0.144.5.*0.147.0"):
        pinned_codex()


def test_env_override_is_honoured_and_checked(monkeypatch):
    monkeypatch.setenv(ENV_VAR, "/opt/pinned/codex")
    monkeypatch.setattr(codex_bin, "codex_version",
                        _fake_version({"/opt/pinned/codex": PINNED_VERSION,
                                       "codex": "0.147.0"}))
    assert pinned_codex() == "/opt/pinned/codex"
    monkeypatch.setattr(codex_bin, "codex_version",
                        _fake_version({"/opt/pinned/codex": "0.150.0"}))
    with pytest.raises(CodexPinError):
        pinned_codex()


def test_missing_binary_is_reported(monkeypatch):
    monkeypatch.setenv(ENV_VAR, "/definitely/not/here")
    assert codex_version("/definitely/not/here") is None
    with pytest.raises(CodexPinError, match="found None"):
        pinned_codex()


def test_unchecked_resolution_for_non_protocol_use(monkeypatch):
    monkeypatch.delenv(ENV_VAR, raising=False)
    monkeypatch.setattr(codex_bin, "codex_version",
                        _fake_version({"codex": "9.9.9"}))
    assert codex_bin.codex_bin(check=False) == "codex"
