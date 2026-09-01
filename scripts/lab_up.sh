#!/usr/bin/env bash
# Start the MacarenaLLM lab -- with the GPU attached to Docker whenever the
# platform actually allows it ("GPU algilanirsa mutlaka Docker'a bagla").
#
#   Linux + NVIDIA GPU + NVIDIA Container Toolkit -> app-gpu service
#     (CUDA torch build, all GPUs reserved, DeepSeek Coder 6.7B auto-selected)
#   Apple Silicon (M1-M4)                         -> Docker CANNOT receive the
#     GPU: macOS containers run in a Linux VM and MPS/Metal has no passthrough
#     (the NVIDIA toolkit needs a Linux host). The CPU service starts instead,
#     with a hint for the native MPS path, where the lab auto-detects the GPU.
#   anything else                                 -> default CPU service (GPT-2)
set -euo pipefail
cd "$(dirname "$0")/.."

have_nvidia_gpu()  { command -v nvidia-smi >/dev/null 2>&1 && nvidia-smi >/dev/null 2>&1; }
have_nvidia_toolkit() { docker info 2>/dev/null | grep -qi nvidia; }

if have_nvidia_gpu && have_nvidia_toolkit; then
    echo "[lab_up] NVIDIA GPU + container toolkit detected -- starting the GPU service (CUDA, DeepSeek)."
    exec docker compose up --build -d app-gpu
elif [ "$(uname -s)" = "Darwin" ] && [ "$(uname -m)" = "arm64" ]; then
    echo "[lab_up] Apple Silicon detected."
    echo "[lab_up] Docker on macOS runs containers in a Linux VM with NO GPU passthrough"
    echo "[lab_up] (MPS/Metal cannot enter a Linux container; NVIDIA toolkit needs a Linux host),"
    echo "[lab_up] so the container cannot use this machine's GPU. Starting the CPU service (GPT-2)."
    echo "[lab_up] To use the M-series GPU, run the lab natively instead -- it auto-detects MPS:"
    echo "[lab_up]     source .venv/bin/activate && python main.py    # DeepSeek Coder 6.7B on MPS"
    exec docker compose up --build -d
else
    echo "[lab_up] No usable container GPU detected -- starting the CPU service (GPT-2)."
    exec docker compose up --build -d
fi
