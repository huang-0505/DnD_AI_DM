# Dockerfile
# Container image for DnD Combat Simulator
# Uses Python 3.12 with all required dependencies

FROM python:3.12-slim-bookworm

ARG DEBIAN_PACKAGES="build-essential curl"

# Prevent apt from showing prompts
ENV DEBIAN_FRONTEND=noninteractive

# Python configuration
ENV LANG=C.UTF-8
ENV PYTHONUNBUFFERED=1

# Tell uv to copy packages from the wheel into the site-packages
ENV UV_LINK_MODE=copy
ENV UV_PROJECT_ENVIRONMENT=/.venv

# Ensure we have an up to date baseline, install dependencies and
# create a user so we don't run the app as root
RUN set -ex; \
    for i in $(seq 1 8); do mkdir -p "/usr/share/man/man${i}"; done && \
    apt-get update && \
    apt-get upgrade -y && \
    apt-get install -y --no-install-recommends $DEBIAN_PACKAGES && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/* && \
    pip install --no-cache-dir --upgrade pip && \
    pip install uv && \
    useradd -ms /bin/bash dnd -d /home/dnd -u 1000 && \
    mkdir -p /app && \
    chown dnd:dnd /app && \
    mkdir -p /.venv && \
    chown dnd:dnd /.venv

# Switch to non-root user
USER dnd
WORKDIR /app

# Copy dependency files first for better layer caching
COPY --chown=dnd:dnd pyproject.toml uv.lock* ./

# Install dependencies in a separate layer for better caching
RUN uv sync --frozen

# Copy the rest of the source code
COPY --chown=dnd:dnd . ./

# Entry point
ENTRYPOINT ["/bin/bash", "docker-entrypoint.sh"]
