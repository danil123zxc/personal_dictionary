# syntax=docker/dockerfile:1
ARG PYTHON_VERSION=3.12.3
FROM python:${PYTHON_VERSION}-slim AS base

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

ARG UID=10001
RUN useradd -m -u "${UID}" -s /bin/bash appuser

ENV HOME=/home/appuser \
    HF_HOME=/home/appuser/.cache/huggingface \
    TRANSFORMERS_CACHE=/home/appuser/.cache/huggingface/transformers \
    SENTENCE_TRANSFORMERS_HOME=/home/appuser/.cache/sentence-transformers \
    XDG_CACHE_HOME=/home/appuser/.cache

RUN mkdir -p /home/appuser/.cache/huggingface/transformers \
             /home/appuser/.cache/sentence-transformers \
             /home/appuser/.cache \
 && chown -R appuser:appuser /home/appuser/.cache

COPY requirements.txt .
RUN sed -i "s/\r$//" requirements.txt

RUN --mount=type=cache,target=/root/.cache/pip \
    pip install --index-url https://download.pytorch.org/whl/cpu torch torchvision torchaudio \
 && pip install --no-cache-dir -r requirements.txt

COPY . .
RUN chown -R appuser:appuser /app

EXPOSE 8000
CMD ["uvicorn","app.main:app","--host","0.0.0.0","--port","8000"]

