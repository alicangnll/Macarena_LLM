"""MacarenaLLM -- entry point. All lab logic lives in the macarena/ package.

!!! MacarenaLLM - Developed by Ali Can Gonullu. !!!
!!! DANGER WARNING: This code will execute actual commands in a lab environment. !!!
!!! USE ONLY IN AN ISOLATED AND SECURED VIRTUAL ENVIRONMENT. !!!
!!! USAGE ON REAL SYSTEMS MAY LEAD TO SEVERE SYSTEM DAMAGE OR DATA LOSS. !!!
"""
from __future__ import annotations

import os
import sys

from macarena.audit import AuditLogger
from macarena.challenges import ProgressStore, ensure_lab_files
from macarena.config import DEFAULT_SERVER_NAME, SERVER_NAME_ENV, STUB_MODEL_ID, resolve_model_spec
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
    # share=False: never create a public gradio.live tunnel (security best practice).
    # Binding stays on loopback by default; the Docker image sets
    # MACARENA_SERVER_NAME=0.0.0.0 so the published port can reach the app.
    server_name = os.environ.get(SERVER_NAME_ENV, DEFAULT_SERVER_NAME)
    if server_name not in ("127.0.0.1", "localhost", "::1"):
        print(f"!!! WARNING: binding to {server_name} -- the lab is reachable from the network. !!!")
        print("!!! A vulnerable lab must only be exposed on an isolated, trusted network. !!!")
    demo.launch(share=False, server_name=server_name)


if __name__ == "__main__":
    main()
