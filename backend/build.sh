#!/usr/bin/env bash
# Render build script for Python native runtime
set -o errexit

pip install --upgrade pip
pip install -r requirements.txt

mkdir -p /tmp/uploads /tmp/outputs
