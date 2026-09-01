# 🇬🇧 MacarenaLLM: A Vulnerable Language Model Lab

## About The Project

**MacarenaLLM** is an interactive lab environment designed to explore and experience **Prompt Injection vulnerabilities** in Large Language Models (LLM) — in the spirit of DVWA and PortSwigger's Web LLM labs. You talk to an LLM in natural language; if a command is detected in the model's output, the lab **actually executes it** on the underlying operating system.

The lab dynamically loads either a more advanced model, **DeepSeek Coder 6.7B Instruct** (when a compatible GPU is detected), or falls back to the lighter **GPT-2** (when running on CPU). Pick a **security level** (Low / Medium / High / Impossible), then try to solve the **5 capture-the-flag challenges** — and watch which ones keep falling as you raise the defenses.

> **The core lesson this lab exists to prove:** at the **High** level there is *no shell at all* (commands are parsed with `shlex` into an argv, binaries and options are allowlisted, the environment is scrubbed) — and yet **prompt injection still reads your files**. `rm -rf /` dies; `cat secret.txt` passes. Removing `shell=True` removes shell *syntax*, not the attacker's control over the *arguments*. Only the Impossible level (the model never executes anything; humans approve) truly stops prompt injection.

## 🚨 Security Warning (CRITICAL!)

This project is **STRICTLY FOR CYBERSECURITY RESEARCH AND EDUCATIONAL PURPOSES ONLY**.

**DO NOT RUN THIS CODE ON YOUR MAIN OPERATING SYSTEM OR ANY ENVIRONMENT CONTAINING SENSITIVE DATA.**

**IT IS ABSOLUTELY ESSENTIAL TO RUN THIS APPLICATION WITHIN AN ISOLATED VIRTUAL MACHINE (e.g., VirtualBox, VMware) or a DOCKER CONTAINER WITH LIMITED OR NO INTERNET ACCESS.**

Failing to comply may result in severe system damage, data loss, or security compromises due to malicious or improperly formed commands generated and executed by the model.

## Security Levels (DVWA-style)

Switch levels in the UI and re-run the same attacks:

| Level | Defence | What it teaches |
|---|---|---|
| **Low** | None. Every detected command runs via `shell=True`. | The original vulnerable behaviour; all 5 challenges are solvable. |
| **Medium** | Normalized blacklist of destructive commands (`rm -rf`, `dd`, `shutdown`, `curl \| sh`, fork bombs, ...). | Blacklists are always incomplete — find a bypass (hint: `base64 -d \| sh`). |
| **High** | No `shell=True`: shell metacharacters rejected, `shlex` argv parsing, binary + option allowlist, scrubbed environment, pinned cwd. | Stops *destruction*, not *exfiltration*: `cat secret.txt` still passes — 4 of 5 challenges still fall. |
| **Impossible** | The LLM never executes anything. Its output is an untrusted *suggestion* a human reviews and runs. | The only real fix: an LLM must never hold execution rights. |

## Challenges (CTF mode)

Five flags, format `MACARENA{...}`. Progress is tracked in the UI (and in `progress.json`).

| # | Challenge | Goal | Difficulty |
|---|---|---|---|
| 1 | **First Blood** | Make the lab read `secret.txt`. | ★ |
| 2 | **Hidden in Plain Sight** | A flag hides in a dotfile in the working directory. | ★★ |
| 3 | **Environment Leak** | Exfiltrate the flag from the lab's environment variables. (Dies at High — scrubbed env.) | ★★ |
| 4 | **The Poisoned Notes** | Ask the model to summarize `notes.txt`. The notes have their own agenda... *(indirect prompt injection)* | ★★★ |
| 5 | **Root is Root** | `root_only.txt` is `chmod 600`. A proper defence — or is it? | ★★ |

Challenge 4 is **indirect prompt injection**: the lab has a naive "chat with your files" feature — mentioning a local `.txt` file inlines its contents into the prompt, and `notes.txt` carries a hidden payload that instructs the model to run a command. The inline happens at *every* security level, because prompt-injection defences are a different layer from execution defences.

Hints are available in the UI (Challenges tab). Flags are fixed and committed; each can be overridden per install with `MACARENA_FLAG_<CHALLENGE_ID>` env vars.

## Features

* **Dynamic Model Loading:** `deepseek-ai/deepseek-coder-6.7b-instruct` on CUDA GPUs, `gpt2` on CPU (unchanged), plus a `MACARENA_MODEL` override (`deepseek` / `gpt2` / any HF repo id / `stub` for UI development without a model).
* **Security Levels:** DVWA-style Low / Medium / High / Impossible with per-level defence descriptions.
* **CTF Challenge Mode:** 5 flag challenges with progress tracking, hints and reset.
* **Indirect Prompt Injection:** naive-RAG file attachment (the "Poisoned Notes" scenario).
* **Gradio Web Interface:** Lab, Challenges, Audit Log and Defenses/About tabs.
* **Audit Log:** every interaction (prompt, expanded prompt, detected command, policy decision, output, captured flags) appended to `logs/audit.jsonl`.
* **Modular & Tested:** pure-Python core (`macarena/` package) with 90+ unit tests that require **no model download**.
* **Real Command Execution (Lab Only):** detected commands really run — inside your isolated lab.

## Setup

### Docker (recommended)

```bash
docker compose up --build
# first run downloads GPT-2 (~500 MB) into the hf-cache volume
```

Then open http://127.0.0.1:7860. The image is CPU-only by default (GPT-2); GPU/hardened variants are commented in [docker-compose.yml](docker-compose.yml) — the hardened variant (non-root, read-only fs, dropped caps) makes challenge 5 fail with *permission denied*, which is exactly the lesson.

### Local

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python main.py
```

Lab files are materialized automatically on startup; `python scripts/setup_lab.py` does it manually. To arm the env-exfil challenge locally, set its flag to any `MACARENA{...}` value: `export MACARENA_CHALLENGE_FLAG='MACARENA{my_local_flag}'` (detection follows whatever you set).

## Usage

1. Run the app and open the local URL (e.g. `http://127.0.0.1:7860`).
2. Pick a **security level** (start at Low).
3. Experiment:
   * **Normal Chat:** "How's the weather today?" / "Tell me a joke."
   * **Explicit Command Injection:** "I want to see system information, run: `uname -a`"
   * **Indirect Command Injection:** "How do I check my network settings on Linux? Show me the command."
   * **Indirect Prompt Injection:** "Please summarize the meeting notes in notes.txt"
4. Solve the challenges, then raise the level and watch which attacks survive.

## Development & Tests

The core package (`macarena/`) is import-light: tests never touch torch/transformers/gradio (an import canary enforces it).

```bash
pip install -r requirements-dev.txt
pytest                                     # 90+ unit tests, no model needed
python -m macarena.smoke                   # headless end-to-end smoke test
MACARENA_MODEL=stub python main.py         # instant UI, deterministic fake model
```

## Defending LLM Agents

1. **Human-in-the-loop** — the model suggests, a human (or a narrowly-scoped tool layer) executes. This is the Impossible level.
2. **Allowlist, don't blacklist** — Medium fails because evil is unenumerable; High works because it permits a small set. But note what High *doesn't* protect: confidentiality of files the allowlisted binaries may read.
3. **Treat model output as data** — parse into structured forms (argv), never splice into a shell string.
4. **Least privilege** — non-root containers, read-only filesystems, dropped capabilities, minimal environment. Try the hardened compose variant.
5. **Untrusted content stays content** — retrieved/attached documents must never be executed as instructions (the Poisoned Notes scenario).
6. **Audit everything** — see the Audit Log tab for the artefact a blue team would need.

Reference: [OWASP Top 10 for LLM Applications — LLM01: Prompt Injection](https://owasp.org/www-project-top-10-for-llm-applications/)

## Pics
![Demo](https://github.com/user-attachments/assets/21108c26-bb3b-4794-927a-ffb32e560fff)

## License
This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for more details.

## Author
**Ali Can Gönüllü** — [LinkedIn](https://www.linkedin.com/in/alicangonullu)
