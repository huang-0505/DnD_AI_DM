#!/bin/bash
set -e

echo "Starting DND Data Collector container..."
echo "Architecture: $(uname -m)"
echo "Python version: $(python --version)"
echo "UV version: $(uv --version)"
echo "Using GOOGLE_APPLICATION_CREDENTIALS=${GOOGLE_APPLICATION_CREDENTIALS}"

# Activate virtual environment
echo "Activating virtual environment..."
source /.venv/bin/activate

# All arguments passed to the container
args="$@"
echo "Received args: $args"

if [[ -z "$args" ]]; then
    echo "No arguments provided. Opening interactive shell..."
    exec /bin/bash
else
    echo "Running cli.py with provided arguments..."
    # Use uv to run our CLI inside the managed environment
    uv run python cli.py "$@"
fi
