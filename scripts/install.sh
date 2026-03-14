#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

echo "Installing na-analytics..."

# Ensure noticiasagricolas_etl is installed
if ! python -c "import noticiasagricolas_etl" 2>/dev/null; then
    echo "Installing noticiasagricolas_etl dependency..."
    uv pip install -e ~/noticiasagricolas_etl/
fi

# Install na-analytics
uv pip install -e "$PROJECT_DIR"

echo "Done. Run 'na-analytics --help' to get started."
