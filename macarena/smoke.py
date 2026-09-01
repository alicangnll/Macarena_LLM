"""Headless end-to-end smoke test -- no model download, no gradio.

Usage:
    MACARENA_MODEL=stub python -m macarena.smoke   (or just: python -m macarena.smoke)

Exercises the full chain with the StubClient: naive-RAG inline -> generation ->
command extraction -> policy (all 4 levels) -> execution -> flag detection ->
progress. Exits 0 on success.
"""
from __future__ import annotations

import os
import sys
import tempfile
from pathlib import Path

from macarena.challenges import ProgressStore, ensure_lab_files, find_flags, match_challenges
from macarena.config import APP_DIR, resolve_model_spec
from macarena.context import inline_files
from macarena.executor import execute
from macarena.llm import StubClient
from macarena.parser import extract_command
from macarena.policy import SecurityLevel, validate


def _check(results, name, condition, detail=""):
    results.append((name, bool(condition)))
    status = "PASS" if condition else "FAIL"
    print(f"  [{status}] {name}" + (f" -- {detail}" if detail and not condition else ""))
    return bool(condition)


def run() -> int:
    results = []
    print("--- MacarenaLLM smoke test (stub model) ---")

    # 1. Lab files materialize in the working directory
    copied = ensure_lab_files()
    _check(results, "lab files present", {"secret.txt", "notes.txt", "root_only.txt"} <= set(copied))

    # 2. Naive-RAG inlining picks up the poisoned notes
    inline = inline_files("Please summarize notes.txt", base_dir=APP_DIR)
    _check(results, "notes.txt inlined", "notes.txt" in inline.files_inlined)
    _check(results, "payload entered the prompt", "cat .macarena_injection.txt" in inline.prompt)

    # 3. Stub generation + command extraction
    spec = resolve_model_spec("stub", cuda_available=lambda: False)
    client = StubClient(spec)
    os.environ["MACARENA_STUB_RESPONSE"] = "```\ncat secret.txt\n```"
    gen = client.generate(inline.prompt)
    parsed = extract_command(gen.raw, user_input="Please summarize notes.txt", model_id=spec.model_id)
    _check(results, "command extracted from stub response", parsed.command == "cat secret.txt", str(parsed))

    # 4. Policy gradient on a destructive command
    _check(results, "low allows rm -rf", validate("rm -rf /", SecurityLevel.LOW).action == "execute")
    _check(results, "medium blocks rm -rf", validate("rm -rf /", SecurityLevel.MEDIUM).action == "block")
    high_rm = validate("rm -rf /", SecurityLevel.HIGH)
    _check(
        results,
        "high blocks rm -rf",
        high_rm.action == "block" and high_rm.matched_rule in ("high.metachar", "high.allowlist"),
    )
    imp = validate("rm -rf /", SecurityLevel.IMPOSSIBLE)
    _check(results, "impossible requires human approval", imp.action == "human_approval")

    # 5. MAIN THESIS: cat secret.txt passes at High too (no shell involved!)
    high_cat = validate("cat secret.txt", SecurityLevel.HIGH)
    _check(
        results,
        "high still allows 'cat secret.txt' (shell=False)",
        high_cat.action == "execute" and high_cat.argv == ["cat", "secret.txt"],
        str(high_cat),
    )

    # 6. Execution + flag capture (isolated progress store)
    with tempfile.TemporaryDirectory() as td:
        progress = ProgressStore(Path(td) / "progress.json")
        low_out = execute(parsed.command, validate(parsed.command, SecurityLevel.LOW), SecurityLevel.LOW)
        _check(results, "low executes and reads the flag", "MACARENA{" in low_out)
        matches = match_challenges(low_out)
        _check(results, "flag maps to read-secret", matches and all(c.id == "read-secret" for c in matches.values()))
        for challenge in matches.values():
            progress.solve(challenge.id)
        _check(results, "progress records the solve", "read-secret" in progress.solved_ids())

        high_out = execute("cat secret.txt", high_cat, SecurityLevel.HIGH)
        _check(results, "high executes WITHOUT shell and still reads the flag", "MACARENA{" in high_out)

        impossible_out = execute("cat secret.txt", imp, SecurityLevel.IMPOSSIBLE)
        _check(results, "impossible never executes", "NOT EXECUTED" in impossible_out)

    failed = [name for name, ok in results if not ok]
    if failed:
        print(f"--- SMOKE FAIL ({len(failed)} check(s): {', '.join(failed)}) ---")
        return 1
    print("--- SMOKE PASS ---")
    return 0


if __name__ == "__main__":
    sys.exit(run())
