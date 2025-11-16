# ================================================
# 📦 DnD Workflow Dockerfile
# Base: Python 3.11 + Slim + GCP SDK + UV + Docker client
# ================================================
FROM python:3.11-slim-bullseye

# Prevent apt from showing prompts
ENV DEBIAN_FRONTEND=noninteractive
ENV LANG=C.UTF-8
ENV PYTHONUNBUFFERED=1

# Use UV (modern dependency manager)
ENV UV_LINK_MODE=copy
ENV UV_PROJECT_ENVIRONMENT=/.venv

# ------------------------------------------------
# 🔹 Install System Dependencies
# ------------------------------------------------
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    curl apt-transport-https ca-certificates gnupg lsb-release \
    jq openssh-client docker-ce-cli && \
    rm -rf /var/lib/apt/lists/*

# ------------------------------------------------
# 🔹 Install Google Cloud SDK
# ------------------------------------------------
RUN mkdir -p /usr/share/keyrings && \
    curl https://packages.cloud.google.com/apt/doc/apt-key.gpg | \
    gpg --dearmor -o /usr/share/keyrings/cloud.google.gpg && \
    echo "deb [signed-by=/usr/share/keyrings/cloud.google.gpg] https://packages.cloud.google.com/apt cloud-sdk main" \
    > /etc/apt/sources.list.d/google-cloud-sdk.list && \
    apt-get update && \
    apt-get install -y google-cloud-sdk google-cloud-sdk-gke-gcloud-auth-plugin && \
    rm -rf /var/lib/apt/lists/*

# ------------------------------------------------
# 🔹 Install UV
# ------------------------------------------------
RUN pip install uv
ENV PATH="$PATH:/root/.local/bin"

# ------------------------------------------------
# 🔹 Create Non-Root User
# ------------------------------------------------
RUN useradd -ms /bin/bash app -d /home/app -u 1000 -p "$(openssl passwd -1 passw0rd)" && \
    usermod -aG docker app && \
    mkdir -p /app && chown app:app /app

# ------------------------------------------------
# 🔹 Set Working Directory
# ------------------------------------------------
WORKDIR /app
USER app

# ------------------------------------------------
# 🔹 Copy Dependency Files & Sync Packages
# ------------------------------------------------
COPY --chown=app:app pyproject.toml uv.lock* ./

# Install all dependencies in one layer for caching
RUN uv sync --frozen || (echo "⚠️  UV sync fallback to pip install"; pip install -r requirements.txt || true)

# ------------------------------------------------
# 🔹 Copy Source Code
# ------------------------------------------------
COPY --chown=app:app . ./

# ------------------------------------------------
# 🔹 Environment Variables (Default)
# ------------------------------------------------
ENV GCP_PROJECT="even-turbine-471117-u0"
ENV GCP_REGION="us-central1"
ENV GCS_BUCKET_NAME="ac215-ml-workflow-central1"
ENV GCS_PACKAGE_URI="gs://ac215-ml-workflow-central1/model-training"
ENV GOOGLE_APPLICATION_CREDENTIALS="/secrets/ml-workflow.json"

# ------------------------------------------------
# 🔹 Entrypoint
# ------------------------------------------------
ENTRYPOINT ["/bin/bash", "docker-entrypoint.sh"]
