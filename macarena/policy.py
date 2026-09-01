"""DVWA-style security levels for command execution.

The pedagogical core of the lab:

* LOW        -- the original vulnerable behaviour (shell=True, no checks).
* MEDIUM     -- a normalized blacklist. Blacklists are always incomplete and
                the level is *deliberately* bypassable -- that is the lesson.
* HIGH       -- no shell=True at all: shell metacharacters rejected, shlex
                parsing, binary + option allowlist, scrubbed environment.
                Destructive commands die here -- and yet prompt injection
                STILL succeeds for read-style commands such as `cat secret.txt`
                because operands pass through. Removing the shell is NOT a
                prompt-injection defence.
* IMPOSSIBLE -- the LLM never holds execution rights; humans approve.

Pure Python: no torch / transformers / gradio imports (enforced by tests).
"""
from __future__ import annotations

import re
import shlex
import shutil
from dataclasses import dataclass
from enum import Enum
from typing import List, Optional

# Directories binaries may be resolved from at the HIGH level
WHICH_PATHS = "/usr/bin:/bin"


class SecurityLevel(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    IMPOSSIBLE = "impossible"


@dataclass(frozen=True)
class PolicyDecision:
    action: str                        # "execute" | "block" | "human_approval"
    reason: str                        # human-readable; shown in the UI and audit log
    matched_rule: Optional[str] = None  # e.g. "medium.rm_rf", "high.metachar"
    argv: Optional[List[str]] = None   # populated only at HIGH (shell=False execution)


def _which(binary: str) -> Optional[str]:
    """Resolve a binary inside the allowlisted directories only.

    Kept as a named function so tests can monkeypatch it on platforms where
    e.g. `ip`/`netstat` do not exist.
    """
    return shutil.which(binary, path=WHICH_PATHS)


# --- MEDIUM: blacklist on a normalized command string. Deliberately bypassable. ---
MEDIUM_RULES: List[tuple] = [
    ("medium.rm_rf", re.compile(r"\brm\s+(-\w+\s+)*-\w*[rf]\w*")),          # rm -rf / rm -r -f ...
    ("medium.dd", re.compile(r"\bdd\b")),                                   # dd if=/dev/zero of=/dev/sda
    ("medium.mkfs", re.compile(r"\b(mkfs(\.\w+)?|wipefs|shred)\b")),
    ("medium.blockdev", re.compile(r"/dev/(sd[a-z]|nvme|hd[a-z]|mmcblk)")),
    ("medium.shutdown", re.compile(r"\b(shutdown|reboot|halt|poweroff)\b|\binit\s+[06]\b")),
    ("medium.forkbomb", re.compile(r":\(\)\s*\{.*\}\s*;\s*:")),              # classic :(){ :|:& };:
    ("medium.remote_exec", re.compile(r"(curl|wget)[^|]*\|\s*(ba|z|da|k)?sh\b")),  # curl ... | sh
    ("medium.chmod_root", re.compile(r"chmod\s+(-[Rr]+\s+)?[0-7]*[67][0-7]{2}\s+/(?=\s|$)")),  # chmod 777 /
    ("medium.etc_write", re.compile(r">\s*/etc/(passwd|shadow|sudoers)\b")),
    ("medium.kill", re.compile(r"\b(killall|pkill)\b")),
    ("medium.pkg_install", re.compile(r"\b(apt(-get)?\s+(install|remove)|pip3?\s+install)\b")),
]


def _normalize_for_blacklist(command: str) -> str:
    """Lower-case, collapse whitespace and strip quote characters.

    Closes the trivial `r""m -rf` style bypasses while (intentionally)
    leaving many others open.
    """
    s = command.lower()
    s = re.sub(r"\s+", " ", s).strip()
    return s.translate(str.maketrans("", "", "'\"`"))


# --- HIGH: strict allowlist, executed WITHOUT a shell ---
HIGH_METACHARS = set(";|&$()<>`\\\n*?[]~")  # also kills pipelines, $(), redirection, globs

HIGH_BINARIES = {
    "ls", "cat", "head", "tail", "pwd", "whoami", "id", "uname", "hostname",
    "echo", "date", "wc", "file", "stat", "grep", "df", "ps", "find", "ip", "netstat",
}
# env/printenv, curl, wget, python, nc, bash ... deliberately NOT allowlisted.

# Per-binary allowed options/flags. A missing key means "no options at all".
# Operands (non-dash arguments) pass through freely -- that is the
# confidentiality gap the lab demonstrates at HIGH.
HIGH_OPTIONS = {
    "ls": {"-l", "-a", "-la", "-al", "-h", "-lah", "-alh", "-t", "-1", "-R"},
    "grep": {"-i", "-n", "-r", "-v", "-c", "-H", "-E", "-F"},
    "head": {"-n"},
    "tail": {"-n"},
    "find": {"-name", "-type", "-maxdepth"},
    "ip": {"addr", "route", "link", "show"},  # treated as a subcommand allowlist
    "cat": set(),
    "echo": set(),
    "wc": set(),
    "stat": set(),
    "file": set(),
}
IP_SUBCOMMANDS = HIGH_OPTIONS["ip"]

# find options that must never pass, whatever the allowlist above says
FIND_FORBIDDEN = {"-exec", "-execdir", "-ok", "-delete", "-fprintf", "-fprint"}


def _block(rule: str, reason: str) -> PolicyDecision:
    return PolicyDecision(action="block", reason=reason, matched_rule=rule)


def _validate_medium(command: str) -> PolicyDecision:
    normalized = _normalize_for_blacklist(command)
    for rule_id, pattern in MEDIUM_RULES:
        if pattern.search(normalized):
            return _block(
                rule_id,
                f"Blocked by Medium blacklist (rule: {rule_id}). Blacklists are bypassable -- try High.",
            )
    return PolicyDecision(action="execute", reason="Passed the Medium blacklist (still shell=True).")


def _validate_high(command: str) -> PolicyDecision:
    for ch in command:
        if ch in HIGH_METACHARS:
            return _block(
                "high.metachar",
                f"Shell metacharacter {ch!r} is not allowed at the High level (no shell is involved).",
            )

    try:
        argv = shlex.split(command)
    except ValueError as e:
        return _block("high.shlex", f"Command could not be parsed safely: {e}")

    if not argv:
        return _block("high.empty", "Empty command.")

    binary = argv[0]
    if binary not in HIGH_BINARIES:
        return _block("high.allowlist", f"Binary '{binary}' is not on the High-level allowlist.")
    if _which(binary) is None:
        return _block("high.allowlist", f"Binary '{binary}' could not be resolved in {WHICH_PATHS}.")

    allowed_options = HIGH_OPTIONS.get(binary)  # None -> no options at all
    for arg in argv[1:]:
        if binary == "ip":  # ip: every token must be a known-safe subcommand
            if arg not in IP_SUBCOMMANDS:
                return _block("high.option", f"'ip {arg}' is not on the subcommand allowlist.")
            continue
        if arg.startswith("-") and arg != "-":
            if binary == "find" and arg in FIND_FORBIDDEN:
                return _block("high.find_exec", f"'find {arg}' can execute/deleting things -- never allowed.")
            if allowed_options is None or arg not in allowed_options:
                return _block("high.option", f"Option '{arg}' is not allowed for '{binary}' at the High level.")
        # operands (file names, patterns...) pass through -- the deliberate confidentiality gap

    return PolicyDecision(
        action="execute",
        reason="Allowlisted argv, executed WITHOUT a shell (shell=False, scrubbed env).",
        argv=argv,
    )


LEVEL_DESCRIPTIONS = {
    SecurityLevel.LOW: (
        "**🟥 Low** -- No filtering: the original vulnerable behaviour. Every detected command "
        "runs with `shell=True`. Start here; all 5 challenges are solvable."
    ),
    SecurityLevel.MEDIUM: (
        "**🟧 Medium** -- A normalized blacklist blocks the obvious destructive commands "
        "(`rm -rf`, `dd`, `shutdown`, `curl ... | sh`, ...). Blacklists are always incomplete: "
        "find a bypass, then switch to High."
    ),
    SecurityLevel.HIGH: (
        "**🟨 High** -- No `shell=True` at all: shell metacharacters rejected, `shlex` parsing, "
        "binary + option allowlist, scrubbed environment. Destructive commands die here -- "
        "**but file reads like `cat secret.txt` still pass. Removing the shell does NOT stop "
        "prompt injection.** 4 of 5 challenges remain solvable."
    ),
    SecurityLevel.IMPOSSIBLE: (
        "**🟩 Impossible** -- The LLM never executes anything. Its output is treated as an "
        "untrusted *suggestion* that a human reviews and runs themselves. This is the only "
        "level where prompt injection truly fails."
    ),
}


def validate(command: str, level: SecurityLevel) -> PolicyDecision:
    """Decide what happens to a model-generated command at the given level."""
    if level == SecurityLevel.LOW:
        return PolicyDecision(action="execute", reason="No filtering (original vulnerable behaviour).")

    if level == SecurityLevel.MEDIUM:
        return _validate_medium(command)

    if level == SecurityLevel.HIGH:
        return _validate_high(command)

    return PolicyDecision(
        action="human_approval",
        reason="Impossible level: model output is a suggestion only -- a human must approve and run it.",
    )
