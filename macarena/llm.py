"""Model plumbing: lazy heavy imports, prompt formatting, generation, StubClient.

transformers/torch are imported ONLY inside load_pipeline(); importing this
module costs nothing (the test suite enforces that with an import canary).
"""
from __future__ import annotations

import os
from dataclasses import dataclass

from macarena.config import STUB_MODEL_ID, ModelSpec


class LLMError(Exception):
    pass


class LLMLoadError(LLMError):
    pass


def load_pipeline(spec: ModelSpec):
    """Load the Hugging Face pipeline for the given spec (heavy imports happen here)."""
    import torch
    from transformers import pipeline as hf_pipeline

    dtype = None
    if spec.torch_dtype == "bfloat16":
        dtype = torch.bfloat16  # memory efficiency and speed on newer GPUs

    print(f"Loading '{spec.model_id}' model... Device: {'GPU' if spec.device != -1 else 'CPU'}")
    try:
        # Load the model with appropriate dtype and device settings
        return hf_pipeline("text-generation", model=spec.model_id, torch_dtype=dtype, device=spec.device)
    except Exception as e:
        raise LLMLoadError(str(e)) from e


def build_prompt(spec: ModelSpec, user_input: str) -> str:
    """Prompt format per model family (identical to the original lab)."""
    if spec.is_instruct:
        # Specific prompt format for DeepSeek Coder (instruction-tuned)
        return f"You are a helpful AI assistant. Please respond to the user's request. User: {user_input}\n\nAssistant:"
    return user_input  # GPT-2 doesn't require a special format


def generation_kwargs(spec: ModelSpec, tokenizer) -> dict:
    """Generation parameters per model family (identical to the original lab)."""
    if spec.is_instruct:
        return {
            "max_new_tokens": spec.max_new_tokens,  # more tokens for longer answers
            "num_return_sequences": 1,
            "truncation": True,
            "do_sample": True,  # for more creative answers
            "top_k": 50,
            "top_p": 0.95,
            "temperature": 0.7,
            "eos_token_id": tokenizer.eos_token_id,  # model's end-of-sequence token
        }
    return {
        "max_new_tokens": spec.max_new_tokens,
        "num_return_sequences": 1,
        "truncation": True,
    }


def clean_response(spec: ModelSpec, formatted_prompt: str, generated_text: str) -> str:
    """Strip the echoed prompt if the model repeated it (identical to the original lab)."""
    if generated_text.startswith(formatted_prompt):
        return generated_text[len(formatted_prompt):].strip()
    return generated_text.strip()


@dataclass
class GenerationResult:
    response: str  # cleaned text shown in the UI
    raw: str       # raw generation (prompt echo included) -- the parser runs against this


class LLMClient:
    """Thin wrapper around the HF pipeline with lazy loading."""

    def __init__(self, spec: ModelSpec):
        self.spec = spec
        self.pipeline = None

    def load(self) -> None:
        self.pipeline = load_pipeline(self.spec)
        print(f"Hugging Face '{self.spec.model_id}' model loaded successfully.\n")

    def generate(self, user_input: str) -> GenerationResult:
        if self.pipeline is None:
            self.load()
        formatted_prompt = build_prompt(self.spec, user_input)
        response = self.pipeline(formatted_prompt, **generation_kwargs(self.spec, self.pipeline.tokenizer))
        generated_text = response[0]["generated_text"]
        return GenerationResult(clean_response(self.spec, formatted_prompt, generated_text), generated_text)


DEFAULT_STUB_RESPONSE = "Sure, I'll check the directory for you.\n```\nls -la\n```"


class StubClient(LLMClient):
    """Deterministic fake model: no download, no torch.

    Selected via MACARENA_MODEL=stub; the response can be scripted with the
    MACARENA_STUB_RESPONSE env var. Used by tests, CI and UI smoke runs.
    """

    def load(self) -> None:  # nothing to load
        pass

    def generate(self, user_input: str) -> GenerationResult:
        text = os.environ.get("MACARENA_STUB_RESPONSE", DEFAULT_STUB_RESPONSE)
        return GenerationResult(text, text)


class ClientSlot:
    """Mutable holder for the active client so the UI can hot-swap models.

    swap() builds and fully loads the new client BEFORE replacing the
    reference, so a concurrent generate() sees either the old (intact) client
    or the new (ready) one -- never a half-loaded pipeline. If loading fails
    it raises LLMLoadError and the previous model simply stays active.
    """

    def __init__(self, client: LLMClient) -> None:
        self.client = client

    def swap(self, spec: ModelSpec) -> LLMClient:
        client = StubClient(spec) if spec.model_id == STUB_MODEL_ID else LLMClient(spec)
        client.load()  # may raise LLMLoadError -- old client stays active
        self.client = client
        return client
