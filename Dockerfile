FROM python:3.11-slim

ENV PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

# Install Node.js (needed because `cmbenchmark web` calls npm on startup)
RUN apt-get update && apt-get install -y --no-install-recommends curl ca-certificates \
  && curl -fsSL https://deb.nodesource.com/setup_20.x | bash - \
  && apt-get install -y --no-install-recommends nodejs \
  && apt-get clean && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Python deps (includes fastapi/uvicorn via requirements.txt)
COPY requirements.txt ./
RUN pip install -r requirements.txt

# Copy source (frontend must be present because CLI expects /app/frontend)
COPY pyproject.toml README.md ./
COPY cmbenchmark ./cmbenchmark
COPY frontend ./frontend

# Install cmbenchmark CLI
RUN pip install -e .

EXPOSE 8000
CMD ["cmbenchmark", "web", "--host", "0.0.0.0", "--port", "8000"]