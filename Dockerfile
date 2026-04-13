# Dockerfile
#
# A Dockerfile is a recipe — it describes exactly how to build
# a container image (a self-contained Linux environment with your app inside).
#
# Every line is a "layer". Docker caches layers — if requirements.txt
# doesn't change, it skips reinstalling packages on rebuild (much faster).

# ── Stage 1: Base image ───────────────────────────────────────────
# python:3.12-slim = official Python image, "slim" variant (no extras)
# Why slim? Full image is ~900MB. Slim is ~130MB. Smaller = faster pulls.
# Why 3.12? Matches what we've been developing on.
FROM python:3.12-slim

# ── Working directory ─────────────────────────────────────────────
# All commands after this run from /app inside the container.
# Also where your code will live.
WORKDIR /app

# ── System dependencies ───────────────────────────────────────────
# psycopg2 (PostgreSQL driver) needs libpq-dev to compile.
# --no-install-recommends keeps the image small (skips optional packages).
# rm -rf /var/lib/apt/lists/* clears apt cache → smaller image layer.
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        libpq-dev \
        gcc \
    && rm -rf /var/lib/apt/lists/*

# ── Python dependencies ───────────────────────────────────────────
# WHY copy requirements.txt BEFORE copying your code?
# Docker layer caching: if only your code changes (not requirements),
# Docker reuses the cached pip install layer → rebuild takes seconds, not minutes.
# If you copied everything first, any code change would trigger a full reinstall.
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# ── Application code ──────────────────────────────────────────────
# Copy everything else now.
# .dockerignore (created below) excludes __pycache__, .env, test files.
COPY . .

# ── Port ──────────────────────────────────────────────────────────
# EXPOSE tells Docker "this container listens on port 8000".
# It doesn't actually publish the port — that's done in docker-compose.yml.
# It's documentation + allows automatic port mapping tools to work.
EXPOSE 8000

# ── Startup command ───────────────────────────────────────────────
# uvicorn = the ASGI server that runs FastAPI
# main:app = "in main.py, use the variable named 'app'"
# --host 0.0.0.0 = listen on ALL network interfaces inside the container
#   (without this, uvicorn only listens on localhost, unreachable from outside)
# --port 8000 = port inside the container
# We do NOT use --reload here (that's for development only)
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]