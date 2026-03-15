#!/bin/bash

# Setup script for Huawei SMS to PushOver
# This script creates a virtual environment and installs dependencies

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
VENV_DIR="$SCRIPT_DIR/venv"

echo "========================================="
echo "Huawei SMS to PushOver - Setup"
echo "========================================="
echo ""

# Check if Python 3 is installed
if ! command -v python3 &> /dev/null; then
    echo "Error: Python 3 is not installed"
    echo "Please install Python 3 and try again"
    exit 1
fi

PYTHON_VERSION=$(python3 --version)
echo "Found: $PYTHON_VERSION"
echo ""

# Check if virtual environment already exists
if [ -d "$VENV_DIR" ]; then
    echo "Virtual environment already exists at: $VENV_DIR"
    read -p "Do you want to recreate it? (y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        echo "Removing existing virtual environment..."
        rm -rf "$VENV_DIR"
    else
        echo "Using existing virtual environment"
    fi
fi

# Create virtual environment if it doesn't exist
if [ ! -d "$VENV_DIR" ]; then
    echo "Creating virtual environment..."
    python3 -m venv "$VENV_DIR"
    echo "Virtual environment created at: $VENV_DIR"
    echo ""
fi

# Activate virtual environment
echo "Activating virtual environment..."
source "$VENV_DIR/bin/activate"

# Upgrade pip
echo "Upgrading pip..."
pip install --upgrade pip

# Install dependencies
echo ""
echo "Installing dependencies from requirements.txt..."
pip install -r "$SCRIPT_DIR/requirements.txt"

echo ""
echo "========================================="
echo "Setup completed successfully!"
echo "========================================="
echo ""
echo "Next steps:"
echo "1. Copy .env.example to .env:"
echo "   cp .env.example .env"
echo ""
echo "2. Edit .env and configure your settings:"
echo "   nano .env"
echo ""
echo "3. Run the script:"
echo "   ./check-sms.sh"
echo ""
echo "To manually activate the virtual environment:"
echo "   source venv/bin/activate"
echo ""
