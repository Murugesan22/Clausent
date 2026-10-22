#!/usr/bin/env bash
# Exit immediately if a command exits with a non-zero status
set -o errexit

echo "=== Installing Python Backend Dependencies ==="
pip install --no-cache-dir -r backend/requirements.txt

echo "=== Build Step Completed Successfully ==="
