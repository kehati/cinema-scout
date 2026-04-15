FROM python:3.11-slim

# 1. Pull the official uv binary into the container
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

WORKDIR /app

# 2. Copy only the uv configuration files first (for Docker layer caching)
COPY pyproject.toml uv.lock ./

# 3. Use uv to install dependencies natively for linux/arm64
# The --system flag tells it to install globally, skipping the need for a .venv inside Docker
RUN uv pip install --system -r pyproject.toml

# 4. Copy your Python scripts
COPY . .

# Keep the container alive on a loop
CMD ["python", "ingest.py"]