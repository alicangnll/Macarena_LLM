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

# Python dependencies (CPU torch keeps the image ~200 MB instead of 2+ GB;
# GPU users: see the GPU variant in docker-compose.yml)
COPY requirements.txt requirements-dev.txt ./
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt \
        --extra-index-url https://download.pytorch.org/whl/cpu

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
