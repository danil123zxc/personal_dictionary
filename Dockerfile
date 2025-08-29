# syntax=docker/dockerfile:1
ARG PYTHON_VERSION=3.12.3
FROM python:${PYTHON_VERSION}-slim AS base

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PIP_NO_CACHE_DIR=1
ENV PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app

# Create non-root user
ARG UID=10001
RUN useradd -m -u "${UID}" -s /bin/bash appuser

# Set cache directories
ENV HOME=/home/appuser \
    HF_HOME=/home/appuser/.cache/huggingface \
    TRANSFORMERS_CACHE=/home/appuser/.cache/huggingface/transformers \
    SENTENCE_TRANSFORMERS_HOME=/home/appuser/.cache/sentence-transformers \
    XDG_CACHE_HOME=/home/appuser/.cache

# Create cache directories
RUN mkdir -p /home/appuser/.cache/huggingface/transformers \
             /home/appuser/.cache/sentence-transformers \
             /home/appuser/.cache \
 && chown -R appuser:appuser /home/appuser/.cache

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    git \
    curl \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements file
COPY requirements.txt ./

# Upgrade pip and install dependencies
RUN pip install --upgrade pip setuptools wheel

# Install PyTorch CPU version first (for better caching)
RUN pip install --no-cache-dir \
    torch --index-url https://download.pytorch.org/whl/cpu \
    torchvision --index-url https://download.pytorch.org/whl/cpu \
    torchaudio --index-url https://download.pytorch.org/whl/cpu

# Install all other requirements
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Set ownership
RUN chown -R appuser:appuser /app

# Switch to non-root user
USER appuser

EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

CMD ["uvicorn", "src.api.main:app", "--host", "0.0.0.0", "--port", "8000"]

