#!/bin/bash
# Kate — Personal AI Assistant launcher
# This script is called when you type 'kate' or 'hi kate' in any terminal

KATE_DIR="$(cd "$(dirname "$0")" && pwd)"
PYTHON=$(which python3)

# Load environment
source ~/.zshrc 2>/dev/null || true

exec "$PYTHON" "$KATE_DIR/jarvis.py" chat
