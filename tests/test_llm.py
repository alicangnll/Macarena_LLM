"""LLM plumbing tests (no torch needed) + the import-purity canary."""
import os
import subprocess
import sys
from pathlib import Path
from types import SimpleNamespace

from macarena.config import (
    DEEPSEEK_MODEL_ID,
    GPT2_MODEL_ID,
    STUB_MODEL_ID,
    ModelSpec,
    resolve_model_spec,
)
from macarena.llm import DEFAULT_STUB_RESPONSE, StubClient, build_prompt, clean_response, generation_kwargs

REPO_ROOT = Path(__file__).resolve().parent.parent


def _spec(model_id=GPT2_MODEL_ID, instruct=False, tokens=100):
    return ModelSpec(model_id=model_id, device=-1, torch_dtype=None, max_new_tokens=tokens, is_instruct=instruct)


# --- prompt formatting / cleaning (verbatim ports) -------------------------
def test_build_prompt_deepseek_format():
    spec = _spec(DEEPSEEK_MODEL_ID, instruct=True)
    assert build_prompt(spec, "hi") == (
        "You are a helpful AI assistant. Please respond to the user's request. User: hi\n\nAssistant:"
    )


def test_build_prompt_gpt2_passthrough():
    assert build_prompt(_spec(), "hi") == "hi"


def test_clean_response_strips_echoed_prompt():
    spec = _spec(DEEPSEEK_MODEL_ID, instruct=True)
    prompt = build_prompt(spec, "hi")
    raw = prompt + "\nls -la"
    assert clean_response(spec, prompt, raw) == "ls -la"


def test_clean_response_without_prefix():
    assert clean_response(_spec(), "", "  hello  ") == "hello"


def test_generation_kwargs_branches():
    tokenizer = SimpleNamespace(eos_token_id=50256)
    instruct_kwargs = generation_kwargs(_spec(instruct=True), tokenizer)
    assert instruct_kwargs["temperature"] == 0.7 and instruct_kwargs["eos_token_id"] == 50256
    gpt2_kwargs = generation_kwargs(_spec(), tokenizer)
    assert "temperature" not in gpt2_kwargs and gpt2_kwargs["truncation"] is True


# --- StubClient --------------------------------------------------------------
def test_stub_client_default_response(monkeypatch):
    monkeypatch.delenv("MACARENA_STUB_RESPONSE", raising=False)
    result = StubClient(_spec(STUB_MODEL_ID)).generate("anything")
    assert result.response == DEFAULT_STUB_RESPONSE
    assert result.raw == DEFAULT_STUB_RESPONSE
    assert "ls -la" in DEFAULT_STUB_RESPONSE


def test_stub_client_env_scripted_response(monkeypatch):
    monkeypatch.setenv("MACARENA_STUB_RESPONSE", "```\ncat secret.txt\n```")
    result = StubClient(_spec(STUB_MODEL_ID)).generate("anything")
    assert result.response == "```\ncat secret.txt\n```"


# --- model resolution precedence ----------------------------------------------
def test_explicit_override_beats_cuda():
    spec = resolve_model_spec("gpt2", cuda_available=lambda: True)
    assert spec.model_id == GPT2_MODEL_ID and spec.device == -1


def test_env_var_override(monkeypatch):
    monkeypatch.setenv("MACARENA_MODEL", "stub")
    spec = resolve_model_spec(cuda_available=lambda: False)
    assert spec.model_id == STUB_MODEL_ID


def test_default_gpu_selects_deepseek():
    spec = resolve_model_spec(cuda_available=lambda: True)
    assert spec.model_id == DEEPSEEK_MODEL_ID
    assert spec.device == 0 and spec.is_instruct is True


def test_default_cpu_selects_gpt2():
    spec = resolve_model_spec(cuda_available=lambda: False)
    assert spec.model_id == GPT2_MODEL_ID and spec.device == -1


def test_forced_deepseek_without_gpu_warns_but_complies(capsys):
    spec = resolve_model_spec("deepseek", cuda_available=lambda: False)
    assert spec.model_id == DEEPSEEK_MODEL_ID and spec.device == -1
    assert "unusably slow" in capsys.readouterr().out


# --- import purity canary ------------------------------------------------------
def test_pure_modules_never_import_heavy_dependencies():
    code = (
        "import sys\n"
        "import macarena.config, macarena.parser, macarena.policy, macarena.challenges, \\\n"
        "       macarena.context, macarena.audit, macarena.llm\n"
        "heavy = [m for m in ('torch', 'transformers', 'gradio') if m in sys.modules]\n"
        "assert not heavy, heavy\n"
        "print('PURE')\n"
    )
    result = subprocess.run(
        [sys.executable, "-c", code],
        cwd=str(REPO_ROOT),
        capture_output=True,
        text=True,
        env={k: v for k, v in os.environ.items()},
    )
    assert result.returncode == 0, result.stderr
    assert "PURE" in result.stdout
