FROM python:3.11-slim

RUN apt-get update && apt-get install -y --no-install-recommends \
    tesseract-ocr \
    poppler-utils \
    libgl1 \
    && rm -rf /var/lib/apt/lists/*

RUN pip install --no-cache-dir uv

# Keep the venv outside /app: docker-compose bind-mounts the host's apps/api over
# /app for live reload, which would otherwise shadow (and break) /app/.venv.
ENV UV_PROJECT_ENVIRONMENT=/opt/venv
ENV PATH="/opt/venv/bin:$PATH"
# Don't leave uv's wheel cache sitting in an image layer — it's multiple GB
# once torch/transformers are in the dependency tree.
ENV UV_NO_CACHE=1

WORKDIR /app
COPY pyproject.toml uv.lock ./
RUN uv sync --no-install-project

COPY . .
RUN uv sync

EXPOSE 8000
CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
