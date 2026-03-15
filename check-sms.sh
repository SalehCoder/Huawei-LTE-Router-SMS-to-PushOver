#!/bin/bash
# Bare-metal runner — activates venv and runs the script.
# Use this for direct cron jobs or manual runs without Docker.
# For Docker deployment, use: docker compose up -d

# Change to script directory
cd "$(dirname "$0")"
SCRIPT_DIR="$(pwd)"

# Check if virtual environment exists
if [ ! -d "$SCRIPT_DIR/venv" ]; then
    echo "Error: Virtual environment not found!"
    echo "Please run setup.sh first:"
    echo "  ./setup.sh"
    exit 1
fi

# Activate virtual environment and run the script
source "$SCRIPT_DIR/venv/bin/activate"
python3 check-sms.py
deactivate
