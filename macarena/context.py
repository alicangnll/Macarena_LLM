"""Naive-RAG file attachment -- the vector for the indirect-injection challenge.

When the user's message mentions a local ``.txt`` file, the lab naively
appends the file's raw contents to the prompt (like countless "chat with your
files" demos). notes.txt carries a hidden payload, so the *file* gets to
inject instructions into the model. This happens at EVERY security level:
prompt-injection defences are a different layer from execution defences.

Pure Python: no torch / transformers / gradio imports (enforced by tests).
"""
from __future__ import annotations

import os
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import List

from macarena.config import APP_DIR

# Bare (optionally ./-prefixed) .txt filenames; dotfiles intentionally not matched.
# The lookbehind also rejects names preceded by "/" so "sub/x.txt" and "../x.txt"
# never produce a reference at all.
FILE_REF_RE = re.compile(r"(?<![\w./])((?:\./)?[A-Za-z0-9_][\w.-]*\.txt)\b")

MAX_INLINE_FILES = 3
MAX_INLINE_TOTAL_BYTES = 20 * 1024


@dataclass
class InlineResult:
    prompt: str
    files_inlined: List[str] = field(default_factory=list)
    skipped: List[str] = field(default_factory=list)


def find_file_references(user_input: str) -> List[str]:
    """Bare .txt filenames mentioned in the input, in order, deduplicated."""
    refs: List[str] = []
    for match in FILE_REF_RE.findall(user_input):
        name = match[2:] if match.startswith("./") else match
        if name not in refs:
            refs.append(name)
    return refs


def inline_files(user_input: str, base_dir: Path = APP_DIR) -> InlineResult:
    """Expand the user input with the contents of referenced local .txt files.

    Containment: only bare basenames resolvable inside base_dir, ``.txt``
    suffix only -- no separators, no ``..``, no absolute paths.
    """
    result = InlineResult(prompt=user_input)
    budget = MAX_INLINE_TOTAL_BYTES

    references = find_file_references(user_input)
    for name in references[:MAX_INLINE_FILES]:
        # Defence in depth: the regex already keeps us to bare basenames
        if "/" in name or ".." in name or not name.endswith(".txt"):
            result.skipped.append(name)
            continue

        path = base_dir / name
        if not path.is_file():
            result.skipped.append(name)
            continue
        try:
            size = path.stat().st_size
            if size > budget:
                result.skipped.append(name)
                continue
            content = path.read_text(encoding="utf-8", errors="replace")
        except OSError:
            result.skipped.append(name)
            continue

        budget -= size
        result.files_inlined.append(name)
        result.prompt += f"\n\n[Attached file: {name}]\n<<<\n{content}\n>>>"

    for name in references[MAX_INLINE_FILES:]:
        result.skipped.append(name)  # over the cap: referenced but never read

    return result
