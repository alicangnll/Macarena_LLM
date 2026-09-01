"""JSONL audit logging -- one line per interaction.

The audit trail never breaks the lab: all I/O errors are swallowed. It is a
teaching artefact (students replay how an attack unfolded) and lives in
logs/audit.jsonl, which is gitignored and contains captured flags.
"""
from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional

from macarena.config import AUDIT_LOG_PATH


@dataclass
class AuditEvent:
    ts: str                            # UTC ISO timestamp
    session_id: str
    level: str
    user_input: str
    expanded_prompt: str
    files_inlined: List[str] = field(default_factory=list)
    model_id: str = ""
    llm_response: str = ""
    detected_command: Optional[str] = None
    policy_action: str = "none"
    policy_reason: str = ""
    executed: bool = False
    command_output: str = ""
    flags_found: List[str] = field(default_factory=list)
    error: Optional[str] = None

    def to_dict(self) -> dict:
        return dict(self.__dict__)


class AuditLogger:
    """Appends one JSON object per line; never raises."""

    def __init__(self, path: Path = AUDIT_LOG_PATH):
        self.path = path

    def log(self, event: AuditEvent) -> None:
        try:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            with self.path.open("a", encoding="utf-8") as fh:
                fh.write(json.dumps(event.to_dict(), ensure_ascii=False) + "\n")
                fh.flush()
                os.fsync(fh.fileno())
        except Exception:
            pass  # auditing must never break the lab


def read_events(path: Path = AUDIT_LOG_PATH, limit: int = 200) -> List[dict]:
    """Read the last `limit` events; corrupt/partial lines are skipped."""
    try:
        lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
    except OSError:
        return []
    events: List[dict] = []
    for line in lines:
        line = line.strip()
        if not line:
            continue
        try:
            events.append(json.loads(line))
        except ValueError:
            continue  # tolerate a truncated tail
    return events[-limit:]
