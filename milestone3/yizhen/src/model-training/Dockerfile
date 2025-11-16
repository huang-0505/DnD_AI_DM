# ============================================
# Base Image
# ============================================
FROM python:3.12-slim-bookworm

# ============================================
# System Setup
# ============================================
ARG DEBIAN_PACKAGES="build-essential git curl wget unzip gzip ca-certificates gnupg lsb-release"

ENV DEBIAN_FRONTEND=noninteractive
ENV LANG=C.UTF-8
ENV PYTHONUNBUFFERED=1
ENV UV_LINK_MODE=copy
ENV UV_PROJECT_ENVIRONMENT=/.venv

# Install dependencies
RUN set -ex; \
    apt-get update && \
    apt-get upgrade -y && \
    apt-get install -y --no-install-recommends $DEBIAN_PACKAGES && \
    # Install Google Cloud SDK
    echo "deb [signed-by=/usr/share/keyrings/cloud.google.gpg] https://packages.cloud.google.com/apt cloud-sdk main" | \
        tee -a /etc/apt/sources.list.d/google-cloud-sdk.list && \
    curl -s https://packages.cloud.google.com/apt/doc/apt-key.gpg | gpg --dearmor -o /usr/share/keyrings/cloud.google.gpg && \
    apt-get update && apt-get install -y google-cloud-sdk && \
    pip install --no-cache-dir --upgrade pip && \
    pip install uv && \
    useradd -ms /bin/bash app -d /home/app -u 1000 && \
    mkdir -p /app /persistent /.venv && \
    chown -R app:app /app /persistent /.venv && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

# ============================================
# Switch to app user
# ============================================
USER app
WORKDIR /app

# ============================================
# Python Dependencies
# ============================================
COPY --chown=app:app pyproject.toml uv.lock* ./
RUN uv sync --frozen

# ============================================
# Copy Source Code
# ============================================
COPY --chown=app:app . ./

# ============================================
# Entrypoint
# ============================================
ENTRYPOINT ["/bin/bash","docker-entrypoint.sh"]
