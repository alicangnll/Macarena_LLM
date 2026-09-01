"""Audit logger/reader tests."""
from macarena.audit import AuditEvent, AuditLogger, read_events


def _event(**overrides):
    defaults = dict(
        ts="2026-01-01T00:00:00+00:00",
        session_id="s1",
        level="low",
        user_input="run ls",
        expanded_prompt="run ls",
        files_inlined=[],
        model_id="gpt2",
        llm_response="```ls -la```",
        detected_command="ls -la",
        policy_action="execute",
        policy_reason="No filtering",
        executed=True,
        command_output="...",
        flags_found=[],
        error=None,
    )
    defaults.update(overrides)
    return AuditEvent(**defaults)


def test_log_writes_one_json_line_and_round_trips(tmp_path):
    path = tmp_path / "audit.jsonl"
    AuditLogger(path).log(_event())
    events = read_events(path)
    assert len(events) == 1
    assert events[0]["user_input"] == "run ls"
    assert events[0]["policy_action"] == "execute"


def test_read_events_skips_corrupt_tail(tmp_path):
    path = tmp_path / "audit.jsonl"
    path.write_text(
        '{"ts": "1", "session_id": "a"}\n{"ts": "2", "session_id": "b"}\n{"trunc',
        encoding="utf-8",
    )
    events = read_events(path)
    assert [e["session_id"] for e in events] == ["a", "b"]


def test_read_events_limit_returns_newest(tmp_path):
    path = tmp_path / "audit.jsonl"
    logger = AuditLogger(path)
    for i in range(5):
        logger.log(_event(session_id=f"s{i}"))
    events = read_events(path, limit=2)
    assert [e["session_id"] for e in events] == ["s3", "s4"]


def test_logger_never_raises_on_unwritable_path(tmp_path):
    directory = tmp_path / "blocked"
    directory.mkdir()
    AuditLogger(directory).log(_event())  # opening a directory fails -> swallowed
    assert True


def test_read_events_missing_file_returns_empty(tmp_path):
    assert read_events(tmp_path / "nope.jsonl") == []
