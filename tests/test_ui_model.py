"""Model-tab handler tests (runtime HF model selection).

These import macarena.ui (and therefore gradio); they skip automatically
where gradio is not installed. No network: failing loads are simulated.
"""
import pytest

pytest.importorskip("gradio")

import macarena.llm as llm_mod
from macarena.config import GPT2_MODEL_ID, STUB_MODEL_ID, resolve_model_spec
from macarena.llm import LLMLoadError, StubClient
from macarena.ui import _load_model, _model_status_md
from tests.test_llm import _spec


def _slot():
    return llm_mod.ClientSlot(StubClient(_spec(STUB_MODEL_ID)))


def test_load_model_preset_swaps_to_stub():
    slot = _slot()
    status = _load_model(slot, STUB_MODEL_ID, "")
    assert status.startswith("✅") and "macarena/stub" in status


def test_load_model_custom_id_is_used_verbatim(monkeypatch):
    import macarena.ui as ui_mod

    class FakeClient(llm_mod.LLMClient):
        def load(self) -> None:
            pass

    monkeypatch.setattr(llm_mod, "LLMClient", FakeClient)
    # arbitrary HF ids make resolve_model_spec probe CUDA (torch) -- inject a
    # torch-free answer, exactly like the injected cuda checks elsewhere
    monkeypatch.setattr(
        ui_mod, "resolve_model_spec", lambda selected: resolve_model_spec(selected, cuda_available=lambda: False)
    )
    slot = _slot()
    status = _load_model(slot, "custom", "Qwen/Qwen2.5-Coder-1.5B-Instruct")
    assert status.startswith("✅")
    assert "Qwen/Qwen2.5-Coder-1.5B-Instruct" in status  # casing preserved
    assert slot.client.spec.model_id == "Qwen/Qwen2.5-Coder-1.5B-Instruct"


def test_load_model_custom_without_id_warns():
    slot = _slot()
    status = _load_model(slot, "custom", "   ")
    assert status.startswith("⚠️")
    assert slot.client.spec.model_id == STUB_MODEL_ID


def test_load_model_failure_keeps_previous_model(monkeypatch):
    class BrokenClient(llm_mod.LLMClient):
        def load(self):
            raise LLMLoadError("connection error")

    monkeypatch.setattr(llm_mod, "LLMClient", BrokenClient)
    slot = _slot()
    status = _load_model(slot, GPT2_MODEL_ID, "")
    assert status.startswith("❌") and "previous model stays active" in status
    assert slot.client.spec.model_id == STUB_MODEL_ID


def test_model_status_md_describes_the_active_client():
    slot = _slot()
    md = _model_status_md(slot)
    assert "macarena/stub" in md and "CPU" in md and "base/completion" in md

    spec = resolve_model_spec("deepseek", cuda_available=lambda: True)
    md_gpu = _model_status_md(llm_mod.ClientSlot(StubClient(spec)))
    assert "GPU" in md_gpu and "instruction-tuned" in md_gpu
