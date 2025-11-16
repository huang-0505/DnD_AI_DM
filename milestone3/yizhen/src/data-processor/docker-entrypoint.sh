#!/bin/bash
set -e

echo "============================================"
echo "🚀 DnD Data Processor container started!"
echo "============================================"
echo "Architecture: $(uname -m)"
echo "Python version: $(python --version)"
echo "UV version: $(uv --version || echo 'uv not installed')"
echo "GCP Project ID: ${GCP_PROJECT}"
echo "GCS Bucket: ${GCS_BUCKET_NAME}"
echo "Credentials: ${GOOGLE_APPLICATION_CREDENTIALS}"
echo "--------------------------------------------"

# Activate virtual environment if present
if [ -d "/.venv" ]; then
  echo "Activating virtual environment..."
  source /.venv/bin/activate
else
  echo "⚠️  No virtual environment found at /.venv"
fi

# Capture command-line args
args="$@"
echo "Received args: ${args}"

# No args → open shell
if [[ -z "${args}" ]]; then
  echo "💡 No command provided — opening interactive shell."
  exec /bin/bash
else
  echo "▶️  Running command: uv run python ${args}"
  uv run python ${args}
fi
