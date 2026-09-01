"""MacarenaLLM -- entry point. All lab logic lives in the macarena/ package.

!!! MacarenaLLM - Developed by Ali Can Gonullu. !!!
!!! DANGER WARNING: This code will execute actual commands in a lab environment. !!!
!!! USE ONLY IN AN ISOLATED AND SECURED VIRTUAL ENVIRONMENT. !!!
!!! USAGE ON REAL SYSTEMS MAY LEAD TO SEVERE SYSTEM DAMAGE OR DATA LOSS. !!!
"""
from __future__ import annotations

import sys

from macarena.audit import AuditLogger
from macarena.challenges import ProgressStore, ensure_lab_files
from macarena.config import STUB_MODEL_ID, resolve_model_spec
from macarena.llm import LLMClient, LLMLoadError, StubClient
from macarena.ui import build_blocks


def main() -> None:
    # --- 1. Basic Configuration and SECURITY WARNING ---
    print("!!! MacarenaLLM - Developed by Ali Can Gonullu. !!!")
    print("!!! LinkedIn : https://www.linkedin.com/in/alicangonullu !!!")
    print("!!! DANGER WARNING: This code will execute actual commands in a lab environment. !!!")
    print("!!! USE ONLY IN AN ISOLATED AND SECURED VIRTUAL ENVIRONMENT. !!!")
    print("!!! USAGE ON REAL SYSTEMS MAY LEAD TO SEVERE SYSTEM DAMAGE OR DATA LOSS. !!!\n")

    # --- 2. Lab files and model selection (DeepSeek on GPU, GPT-2 on CPU, stub for CI) ---
    ensure_lab_files()
    spec = resolve_model_spec()

    if spec.model_id == STUB_MODEL_ID:
        client = StubClient(spec)
    else:
        client = LLMClient(spec)
        try:
            client.load()
        except LLMLoadError as e:
            print(f"Error loading Hugging Face model: {e}")
            print("Please ensure you have enough RAM/GPU memory and have run 'pip install transformers torch accelerate'.")
            print("If you encounter issues loading DeepSeek, you can force using 'gpt2' with MACARENA_MODEL=gpt2.")
            sys.exit(1)

    # --- 3. Create and launch the Gradio interface ---
    demo = build_blocks(client, AuditLogger(), ProgressStore())

    print("\n--- Launching Gradio Interface ---")
    print("Access the interface by visiting the 'Running on local URL' address below.")
    # share=False ensures the interface is only accessible locally (security best practice)
    demo.launch(share=False)


if __name__ == "__main__":
    main()
