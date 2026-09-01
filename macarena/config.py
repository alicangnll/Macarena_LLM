"""Central configuration: model selection, paths and constants.

This module stays import-light on purpose: no torch / transformers / gradio
imports (the test suite enforces this with an import canary). Heavy imports
happen lazily in macarena.llm / macarena.ui only.
"""
from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Optional

# --- 1. Model identifiers (policy unchanged: DeepSeek on GPU, GPT-2 on CPU) ---
DEEPSEEK_MODEL_ID = "deepseek-ai/deepseek-coder-6.7b-instruct"
GPT2_MODEL_ID = "gpt2"
STUB_MODEL_ID = "macarena/stub"  # deterministic fake model: no download, used for tests/CI/UI smoke

# --- 2. Paths ---
APP_DIR = Path(__file__).resolve().parent.parent
LAB_DATA_DIR = APP_DIR / "labdata"  # canonical challenge files, copied to APP_DIR on startup
LOG_DIR = APP_DIR / "logs"
AUDIT_LOG_PATH = LOG_DIR / "audit.jsonl"
PROGRESS_PATH = APP_DIR / "progress.json"

# --- 3. Execution ---
EXEC_TIMEOUT_SECONDS = 20  # same value the original lab used

# --- 4. Consumption limits (OWASP LLM04: Model Denial of Service) ---
# Oversized prompts are rejected before they ever reach the model; generation
# length is separately bounded by ModelSpec.max_new_tokens.
MAX_INPUT_CHARS = 4000

# --- 5. Interface binding ---
# Local default stays on the loopback interface; the Docker image overrides
# this with 0.0.0.0 so the published port can reach the app (see Dockerfile).
SERVER_NAME_ENV = "MACARENA_SERVER_NAME"
DEFAULT_SERVER_NAME = "127.0.0.1"

# Environment variable carrying the env-exfiltration challenge flag
# (set in the Dockerfile / docker-compose; export it manually for local runs).
ENV_CHALLENGE_FLAG_VAR = "MACARENA_CHALLENGE_FLAG"


@dataclass(frozen=True)
class ModelSpec:
    """Everything the lab needs to know about the selected model."""

    model_id: str
    device: int           # 0 = first GPU, -1 = CPU (same convention as the original code)
    torch_dtype: Any      # "bfloat16" or None; resolved to torch.bfloat16 lazily in llm.py
    max_new_tokens: int
    is_instruct: bool     # True -> instruction-style prompt (DeepSeek), False -> raw input (GPT-2/stub)


def _default_cuda_check() -> bool:
    import torch  # lazy: only touched when a model is actually selected
    return torch.cuda.is_available()


# Human-friendly aliases accepted via MACARENA_MODEL / resolve_model_spec(override=...)
_ALIASES = {
    "deepseek": DEEPSEEK_MODEL_ID,
    "gpt2": GPT2_MODEL_ID,
    "stub": STUB_MODEL_ID,
}


def resolve_model_spec(
    override: Optional[str] = None,
    cuda_available: Optional[Callable[[], bool]] = None,
) -> ModelSpec:
    """Resolve which model to run.

    Precedence: explicit override > MACARENA_MODEL env var > CUDA detection
    (the original lab's dynamic behaviour). Accepted values: ``deepseek``,
    ``gpt2``, ``stub`` or any full Hugging Face repo id. Alias matching is
    case-insensitive, but a repo id keeps its original casing (HF ids are
    case-sensitive, e.g. ``Qwen/Qwen2.5-Coder-1.5B-Instruct``).
    """
    raw = (override or os.environ.get("MACARENA_MODEL", "") or "").strip()
    choice: Optional[str] = None
    if raw:
        lowered = raw.lower()
        choice = _ALIASES.get(lowered, raw)  # alias -> canonical id; else keep the user's casing

    cuda = cuda_available if cuda_available is not None else _default_cuda_check

    if choice == STUB_MODEL_ID:
        return ModelSpec(STUB_MODEL_ID, device=-1, torch_dtype=None, max_new_tokens=200, is_instruct=False)

    if choice == GPT2_MODEL_ID:
        return ModelSpec(GPT2_MODEL_ID, device=-1, torch_dtype=None, max_new_tokens=100, is_instruct=False)

    if choice == DEEPSEEK_MODEL_ID:
        if cuda():
            return ModelSpec(DEEPSEEK_MODEL_ID, device=0, torch_dtype="bfloat16", max_new_tokens=200, is_instruct=True)
        print("WARNING: DeepSeek Coder explicitly requested without a CUDA GPU -- it will run on CPU (unusably slow).")
        return ModelSpec(DEEPSEEK_MODEL_ID, device=-1, torch_dtype=None, max_new_tokens=200, is_instruct=True)

    if choice:  # arbitrary Hugging Face repo id
        if cuda():
            return ModelSpec(choice, device=0, torch_dtype="bfloat16", max_new_tokens=200, is_instruct=True)
        return ModelSpec(choice, device=-1, torch_dtype=None, max_new_tokens=200, is_instruct=True)

    # Default: the original dynamic selection
    if cuda():
        print("Compatible GPU detected. Loading 'deepseek-ai/deepseek-coder-6.7b-instruct' model.")
        return ModelSpec(DEEPSEEK_MODEL_ID, device=0, torch_dtype="bfloat16", max_new_tokens=200, is_instruct=True)
    print("Compatible GPU not found. Loading 'gpt2' model.")
    return ModelSpec(GPT2_MODEL_ID, device=-1, torch_dtype=None, max_new_tokens=100, is_instruct=False)
