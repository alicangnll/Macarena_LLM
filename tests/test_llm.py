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
from macarena.llm import (
    DEFAULT_STUB_RESPONSE,
    ClientSlot,
    LLMLoadError,
    StubClient,
    build_prompt,
    clean_response,
    generation_kwargs,
)

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


def test_custom_hf_id_keeps_its_casing():
    """HF repo ids are case-sensitive -- only aliases fold to lowercase."""
    spec = resolve_model_spec("Qwen/Qwen2.5-Coder-1.5B-Instruct", cuda_available=lambda: False)
    assert spec.model_id == "Qwen/Qwen2.5-Coder-1.5B-Instruct"
    assert spec.is_instruct is True


def test_alias_matching_stays_case_insensitive():
    assert resolve_model_spec("GPT2", cuda_available=lambda: True).model_id == GPT2_MODEL_ID
    assert resolve_model_spec("DeepSeek", cuda_available=lambda: False).model_id == DEEPSEEK_MODEL_ID


# --- Apple Silicon (MPS) detection: CUDA > MPS > CPU ----------------------------
def test_default_mps_selects_deepseek_on_mps():
    spec = resolve_model_spec(cuda_available=lambda: False, mps_available=lambda: True)
    assert spec.model_id == DEEPSEEK_MODEL_ID
    assert spec.device == "mps" and spec.torch_dtype == "float16" and spec.is_instruct is True


def test_cuda_beats_mps():
    spec = resolve_model_spec(cuda_available=lambda: True, mps_available=lambda: True)
    assert spec.device == 0 and spec.torch_dtype == "bfloat16"


def test_explicit_gpt2_stays_cpu_even_with_mps():
    spec = resolve_model_spec("gpt2", cuda_available=lambda: False, mps_available=lambda: True)
    assert spec.device == -1


def test_explicit_deepseek_uses_mps_when_present():
    spec = resolve_model_spec("deepseek", cuda_available=lambda: False, mps_available=lambda: True)
    assert spec.device == "mps" and spec.torch_dtype == "float16"


def test_custom_hf_id_uses_mps_when_present():
    spec = resolve_model_spec(
        "Qwen/Qwen2.5-Coder-1.5B-Instruct", cuda_available=lambda: False, mps_available=lambda: True
    )
    assert spec.device == "mps"


def test_default_mps_detection_message(capsys):
    resolve_model_spec(cuda_available=lambda: False, mps_available=lambda: True)
    assert "MPS" in capsys.readouterr().out


# --- ClientSlot (runtime model swapping) --------------------------------------
def test_client_slot_swaps_the_active_client(monkeypatch):
    import macarena.llm as llm_mod

    class FakeClient(llm_mod.LLMClient):
        def load(self) -> None:  # offline stand-in: no HF download
            pass

    monkeypatch.setattr(llm_mod, "LLMClient", FakeClient)
    slot = ClientSlot(StubClient(_spec(STUB_MODEL_ID)))
    assert slot.client.spec.model_id == STUB_MODEL_ID

    slot.swap(_spec(GPT2_MODEL_ID))
    assert slot.client.spec.model_id == GPT2_MODEL_ID


def test_client_slot_failed_swap_keeps_previous_model(monkeypatch):
    import macarena.llm as llm_mod

    class BrokenClient(llm_mod.LLMClient):
        def load(self):
            raise LLMLoadError("no such repo")

    monkeypatch.setattr(llm_mod, "LLMClient", BrokenClient)
    slot = ClientSlot(StubClient(_spec(STUB_MODEL_ID)))

    try:
        slot.swap(_spec("broken/broken-model"))
    except LLMLoadError:
        pass
    else:
        raise AssertionError("swap should have re-raised the load failure")
    assert slot.client.spec.model_id == STUB_MODEL_ID  # old model stayed active


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
