# MacarenaLLM lab image.
# python:3.11-slim-bookworm: buster is archived and gradio 5+ requires Python >= 3.10.
# NOTE: the lab runs as root ON PURPOSE -- challenge 5 ("Root is Root") is the lesson.
# The hardened alternative lives commented in docker-compose.yml.
FROM python:3.11-slim-bookworm

# Working directory
WORKDIR /app

# System dependencies used by the lab's example commands:
# procps (ps), iproute2 (ip), net-tools (netstat/ifconfig), file (file)
RUN apt-get update && apt-get install -y --no-install-recommends \
    procps \
    iproute2 \
    net-tools \
    file \
    && rm -rf /var/lib/apt/lists/*

# Python dependencies. TORCH_INDEX_URL picks the torch flavour:
#   default  https://download.pytorch.org/whl/cpu -> CPU wheels (~200 MB image)
#   GPU      override with "" -> plain PyPI Linux wheels (CUDA-bundled, 2+ GB)
# The GPU path is wired up by the `app-gpu` service in docker-compose.yml /
# scripts/lab_up.sh ("attach the GPU to Docker whenever one is detected").
# NOTE: Apple Silicon (MPS/Metal) CANNOT be passed into Docker -- macOS
# containers run in a Linux VM with no GPU. On a Mac the lab auto-detects MPS
# when run natively (python main.py) instead.
ARG TORCH_INDEX_URL=https://download.pytorch.org/whl/cpu
COPY requirements.txt requirements-dev.txt ./
RUN if [ -n "$TORCH_INDEX_URL" ]; then TORCH_FLAGS="--extra-index-url $TORCH_INDEX_URL"; else TORCH_FLAGS=""; fi && \
    pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt $TORCH_FLAGS

# Application code + canonical lab files
COPY main.py ./
COPY macarena ./macarena
COPY labdata ./labdata
COPY scripts ./scripts

# Env-exfiltration challenge flag + persistent model cache location.
# MACARENA_SERVER_NAME=0.0.0.0: the app must bind all interfaces INSIDE the
# container for the published port to reach it (workshop/classroom use).
# main.py prints a loud warning whenever it binds beyond the loopback.
ENV MACARENA_CHALLENGE_FLAG=MACARENA{3nv1r0nm3nt_l34k} \
    HF_HOME=/cache/huggingface \
    PYTHONUNBUFFERED=1 \
    MACARENA_SERVER_NAME=0.0.0.0

# root_only.txt must be owner-only (git cannot store file modes);
# main.py re-applies this on startup, the image bakes it in too.
# Lab files are also materialized here so the hardened (read-only, non-root)
# variant has them even though it cannot write to /app at runtime.
RUN chmod 600 /app/labdata/root_only.txt && \
    mkdir -p /app/logs /cache/huggingface && \
    python -c "from macarena.challenges import ensure_lab_files; ensure_lab_files()"

# Gradio's default port
EXPOSE 7860

# No curl in slim images -- use python's urllib for the healthcheck
HEALTHCHECK --interval=30s --timeout=10s --start-period=120s --retries=5 \
    CMD python -c "import urllib.request,sys; sys.exit(0 if urllib.request.urlopen('http://127.0.0.1:7860/', timeout=5).status==200 else 1)"

CMD ["python", "main.py"]
