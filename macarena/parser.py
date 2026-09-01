"""Command extraction from raw LLM output.

A faithful port of the original lab's parsing logic -- behaviour is
intentionally identical, quirks included: the regexes run against the *raw*
generated text (which may still contain the echoed prompt), and the two
false-positive rules below sanitize the result.

Pure Python: no torch / transformers / gradio imports (enforced by tests).
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Optional

from macarena.config import DEEPSEEK_MODEL_ID

# --- Command detection patterns (unchanged from the original lab) ---
CODE_BLOCK_RE = re.compile(r"```(?:[a-zA-Z0-9_-]*\n)?(.*?)```", re.DOTALL)
BACKTICK_RE = re.compile(r"`([^`]+)`")

# Common commands searched in plain text when no code formatting is found.
# Word boundaries avoid partial matches (e.g. 'cat' inside 'category').
COMMON_COMMANDS = (
    "ls -la", "pwd", "uname -a", "cat /etc/passwd", "whoami", "ip addr", "ifconfig",
    "ps aux", "df -h", "hostname", "netstat -tuln", "id", "echo", "mkdir", "touch",
)


@dataclass(frozen=True)
class ParseResult:
    command: Optional[str]  # the command to run, or None
    note: Optional[str]     # sanitization note for the interaction log, or None


def extract_command(llm_output: str, user_input: str = "", model_id: str = "") -> ParseResult:
    """Extract a potential shell command from the LLM's raw output.

    Priority: markdown code block > single backticks > known common commands.
    """
    potential_command = None

    code_block_match = CODE_BLOCK_RE.search(llm_output)
    backtick_match = BACKTICK_RE.search(llm_output)

    if code_block_match:
        potential_command = code_block_match.group(1).strip()
    elif backtick_match:
        potential_command = backtick_match.group(1).strip()
    else:
        for cmd in COMMON_COMMANDS:
            if re.search(r"\b" + re.escape(cmd) + r"\b", llm_output):
                potential_command = cmd
                break

    if not potential_command:
        return ParseResult(None, None)

    # Prevent the user's input itself from being detected as a command (False Positive)
    if user_input.strip() == potential_command:
        return ParseResult(None, "Detected command is identical to user input. Sanitized (False Positive).")

    # Prevent the model's internal instructions from being detected as commands (especially for DeepSeek)
    if model_id == DEEPSEEK_MODEL_ID and (
        "You are a helpful AI assistant" in potential_command or "Assistant:" in potential_command
    ):
        return ParseResult(None, "Detected command contains model's internal instructions. Sanitized.")

    return ParseResult(potential_command, None)
