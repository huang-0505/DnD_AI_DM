#!/bin/bash

# docker-entrypoint.sh
# Entry point script for the DnD Combat Simulator container
# Provides interactive shell access for development

echo "======================================"
echo "🎲 DnD Combat Simulator Container"
echo "======================================"
echo "Container is running!"
echo "Architecture: $(uname -m)"
echo ""

# Activate virtual environment
echo "Activating virtual environment..."
source /.venv/bin/activate

echo "Environment ready! Virtual environment activated."
echo "Python version: $(python --version)"
echo "UV version: $(uv --version)"
echo ""

echo "Available commands:"
echo "  python cli.py --init-db    - Initialize embedding databases"
echo "  python cli.py              - Start combat simulation with AI"
echo "  python cli.py --no-ai      - Start combat without AI"
echo "  python db_tool.py embed    - Generate embeddings manually"
echo "  python db_tool.py retrieve - Query embeddings"
echo ""
echo "Directories:"
echo "  input/   - JSON data files"
echo "  output/  - Embedding databases"
echo "  secrets/ - GCP credentials"
echo ""
echo "======================================"

# Start interactive bash shell with virtual environment activated
exec /bin/bash
