#!/usr/bin/env bash
set -euo pipefail
source "$(dirname "$0")/.venv/bin/activate"
python -m app.cli

