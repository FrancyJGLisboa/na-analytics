#!/usr/bin/env bash
set -euo pipefail

# na-analytics bootstrap — ensures the skill is ready to run.
# Called automatically on first use, or manually via: ./scripts/install.sh

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

echo "na-analytics: checking environment..."

# 1. Check Python 3.10+
if ! command -v python3 &>/dev/null; then
    echo "ERROR: Python 3 not found."
    case "$(uname -s)" in
        Darwin) echo "  Install: brew install python" ;;
        Linux)  echo "  Install: sudo apt install python3" ;;
        *)      echo "  Install Python 3.10+ from https://python.org" ;;
    esac
    exit 1
fi

PY_VERSION=$(python3 -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')
PY_MAJOR=$(echo "$PY_VERSION" | cut -d. -f1)
PY_MINOR=$(echo "$PY_VERSION" | cut -d. -f2)
if [ "$PY_MAJOR" -lt 3 ] || { [ "$PY_MAJOR" -eq 3 ] && [ "$PY_MINOR" -lt 10 ]; }; then
    echo "ERROR: Python 3.10+ required (found $PY_VERSION)"
    exit 1
fi
echo "  Python $PY_VERSION ✓"

# 2. Check/install uv (fast Python package manager)
if ! command -v uv &>/dev/null; then
    echo "  Installing uv..."
    curl -LsSf https://astral.sh/uv/install.sh | sh
    export PATH="$HOME/.local/bin:$PATH"
fi
echo "  uv ✓"

# 3. Create venv and install dependencies
if [ ! -d "$PROJECT_DIR/.venv" ]; then
    echo "  Creating virtual environment..."
    cd "$PROJECT_DIR"
    uv venv --python python3
fi

echo "  Installing dependencies (click, duckdb)..."
cd "$PROJECT_DIR"
uv pip install -e . --quiet 2>/dev/null || uv pip install -e .

echo ""
echo "na-analytics: ready."
echo ""
echo "Usage:"
echo "  uv run na-analytics list-indicators --commodity soja"
echo "  uv run na-analytics spread --commodity soja --indicator soja-mercado-fisico-sindicatos-e-cooperativas"
echo "  uv run na-analytics ppe --commodity soja"
