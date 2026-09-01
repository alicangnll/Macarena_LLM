"""UI interaction guard tests (OWASP LLM04: oversized input never reaches the model).

These are the only tests that import macarena.ui (and therefore gradio);
they skip automatically where gradio is not installed.
"""
import pytest

pytest.importorskip("gradio")

from macarena.audit import AuditLogger
from macarena.challenges import ProgressStore
from macarena.config import MAX_INPUT_CHARS, resolve_model_spec
from macarena.llm import StubClient
from macarena.ui import _interaction


class ExplodingClient(StubClient):
    """Fails the test loudly if the guard lets an oversized prompt through."""

    def generate(self, user_input):  # pragma: no cover -- only reached on a bug
        raise AssertionError("the LLM must not be called for oversized input")


def test_oversized_input_is_rejected_before_generation(tmp_path):
    spec = resolve_model_spec("stub", cuda_available=lambda: False)
    client = ExplodingClient(spec)
    audit = AuditLogger(tmp_path / "audit.jsonl")
    progress = ProgressStore(tmp_path / "progress.json")

    log, response, output, inline_md, flag_md, badge, table = _interaction(
        "a" * (MAX_INPUT_CHARS + 1), "low", "session-1", client, audit, progress
    )

    assert "rejected" in log and "LLM04" in log
    assert response == "" and output == ""
    # the rejection is audited like any other interaction
    events = (tmp_path / "audit.jsonl").read_text(encoding="utf-8").strip().splitlines()
    assert len(events) == 1
    assert '"input_too_long"' in events[0]


def test_normal_input_still_reaches_the_model(tmp_path, monkeypatch):
    monkeypatch.setenv("MACARENA_STUB_RESPONSE", "```\nls\n```")
    spec = resolve_model_spec("stub", cuda_available=lambda: False)
    client = StubClient(spec)
    audit = AuditLogger(tmp_path / "audit.jsonl")
    progress = ProgressStore(tmp_path / "progress.json")

    log, response, output, *_ = _interaction(
        "please run `ls`", "low", "session-2", client, audit, progress
    )

    assert response != ""
    assert "--- RECEIVED COMMAND (Executing) ---" in output
