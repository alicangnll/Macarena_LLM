"""Executor tests: Low output parity, High shell=False path, Impossible no-op."""
import subprocess
from types import SimpleNamespace

import macarena.executor as executor
from macarena.executor import MINIMAL_ENV, execute
from macarena.policy import PolicyDecision, SecurityLevel, validate

LOW = SecurityLevel.LOW
HIGH = SecurityLevel.HIGH
IMPOSSIBLE = SecurityLevel.IMPOSSIBLE


def _low_decision():
    return validate("echo hello", LOW)


def test_low_output_format_matches_original():
    out = execute("echo hello", _low_decision(), LOW)
    assert out.startswith("\n--- RECEIVED COMMAND (Executing) ---\n")
    assert "Command: 'echo hello'" in out
    assert "Command Output:\n" in out
    assert "hello" in out
    assert out.endswith("--- END OF COMMAND ---\n")


def test_low_nonzero_exit_branch():
    out = execute("false", _low_decision(), LOW)
    assert "Error executing command (Return Code: 1)" in out
    assert "Error details:" in out


def test_low_missing_binary_branch(monkeypatch):
    def raise_fnf(*args, **kwargs):
        raise FileNotFoundError("nope")

    monkeypatch.setattr(executor.subprocess, "run", raise_fnf)
    out = execute("zzz-not-a-command", _low_decision(), LOW)
    assert "not found. Ensure it's installed." in out


def test_high_executes_without_shell_and_scrubbed_env():
    decision = validate("echo hi", HIGH)
    out = execute("echo hi", decision, HIGH)
    assert "hi" in out
    assert "WITHOUT shell" in out


def test_high_run_invocation_shape(monkeypatch):
    captured = {}

    def fake_run(argv, **kwargs):
        captured["argv"] = argv
        captured.update(kwargs)
        return SimpleNamespace(stdout="ok", stderr="")

    monkeypatch.setattr(executor.subprocess, "run", fake_run)
    decision = PolicyDecision(action="execute", reason="", argv=["echo", "hi"])
    execute("echo hi", decision, HIGH)
    assert captured["argv"][0].endswith("echo") or captured["argv"][0] == "echo"
    assert captured["shell"] is False
    assert captured["env"] == MINIMAL_ENV
    assert "MACARENA_CHALLENGE_FLAG" not in captured["env"]


def test_impossible_never_spawns_a_process(monkeypatch):
    called = []

    def recorder(*args, **kwargs):
        called.append((args, kwargs))
        return SimpleNamespace(stdout="", stderr="")

    monkeypatch.setattr(executor.subprocess, "run", recorder)
    decision = validate("cat secret.txt", IMPOSSIBLE)
    out = execute("cat secret.txt", decision, IMPOSSIBLE)
    assert called == []
    assert "NOT EXECUTED" in out
    assert "human approval required" in out
