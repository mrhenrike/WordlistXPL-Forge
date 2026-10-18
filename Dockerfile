# WordlistXPL-Forge multi-stage Dockerfile
# Usage:
#   docker build -t wlf .                          # core (CPU only)
#   docker build --target gpu -t wlf-gpu .          # GPU (CUDA + torch)
#   docker build --target full -t wlf-full .        # all extras
#   docker run --rm wlf charset --length 8 -o /out/wl.lst

# ── Stage 0: base ────────────────────────────────────────────────────────────
FROM python:3.12-slim AS base

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

RUN groupadd -r wlf && useradd -r -g wlf -d /app wlf
WORKDIR /app

COPY pyproject.toml README.md wlf.py ./
COPY wlf/ wlf/
COPY wlf_modules/ wlf_modules/

RUN pip install --no-cache-dir .

USER wlf
ENTRYPOINT ["python", "wlf.py"]
CMD ["--help"]

# ── Stage 1: core (default) ─────────────────────────────────────────────────
FROM base AS core

# ── Stage 2: gpu ─────────────────────────────────────────────────────────────
FROM base AS gpu
USER root
RUN pip install --no-cache-dir "wordlistxpl-forge[gpu]" 2>/dev/null || \
    pip install --no-cache-dir torch transformers
USER wlf

# ── Stage 3: full (all extras) ──────────────────────────────────────────────
FROM base AS full
USER root
RUN pip install --no-cache-dir "wordlistxpl-forge[full]" 2>/dev/null || \
    pip install --no-cache-dir \
        easyocr Pillow openpyxl pdfplumber python-docx striprtf pypdf \
        torch transformers fastapi uvicorn pydantic argcomplete
USER wlf
