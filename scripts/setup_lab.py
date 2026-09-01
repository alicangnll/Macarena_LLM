#!/usr/bin/env python3
"""Lay out the lab files for local runs.

Copies the canonical challenge files from labdata/ into a target directory
(default: the repository root, i.e. the lab's working directory) and applies
chmod 600 to root_only.txt (git cannot store file modes). main.py does this
automatically on startup; this script exists for manual setup / CI.
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from macarena.challenges import ensure_lab_files  # noqa: E402


def main() -> int:
    target = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else Path(__file__).resolve().parent.parent
    if not target.is_dir():
        print(f"Error: target directory does not exist: {target}")
        return 1
    copied = ensure_lab_files(target_dir=target)
    print(f"Lab files materialized in {target}: {', '.join(copied)}")
    print("Tip: export MACARENA_CHALLENGE_FLAG=MACARENA{...} to enable the env-exfil challenge locally.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
