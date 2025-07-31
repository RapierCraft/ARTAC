#!/bin/bash

# ARTAC Safe Mode Startup Script
# Runs backend without auto-reload to prevent Claude Code session conflicts

set -e

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${BLUE}[ARTAC]${NC} Starting backend in safe mode (no auto-reload)..."

# Navigate to backend directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Activate virtual environment
if [[ -d "venv" ]]; then
    source venv/bin/activate
else
    echo -e "${YELLOW}[ARTAC]${NC} Virtual environment not found. Run start_dev.sh first to set up."
    exit 1
fi

# Set safe mode environment variable
export SAFE_RELOAD_MODE=true

echo -e "${GREEN}[ARTAC]${NC} ✅ Safe mode enabled - Claude Code sessions won't be disrupted"
echo -e "${BLUE}[ARTAC]${NC} Starting backend on http://localhost:8000..."

# Run without reload
uvicorn main:app --host 0.0.0.0 --port 8000