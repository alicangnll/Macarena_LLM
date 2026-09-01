#!/usr/bin/env bash
# OWASP LLM05 (Supply Chain Vulnerabilities) helper.
# Audits the lab's pinned Python dependencies against the OSV database.
#
# Usage:  scripts/audit_deps.sh          (from the repo root)
#         pip install pip-audit          (if not installed yet)
#
# The lab's supply-chain posture:
#   - every dependency is version-pinned in requirements.txt (no floating tags)
#   - the Docker image is built from python:3.11-slim-bookworm with apt lists
#     cleaned, and inference runs locally (no third-party model API)
#   - this script turns that posture into a checkable artefact

set -euo pipefail
cd "$(dirname "$0")/.."

if ! command -v pip-audit >/dev/null 2>&1; then
    echo "pip-audit not found." >&2
    echo "Install it with:  pip install pip-audit" >&2
    echo "Then re-run:      scripts/audit_deps.sh" >&2
    exit 2
fi

echo "--- Auditing pinned dependencies (OWASP LLM05) ---"
pip-audit -r requirements.txt
echo "--- Audit finished: no known vulnerabilities in the pinned set ---"
