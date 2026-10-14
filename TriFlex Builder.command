#!/bin/bash
# Double-click in Finder to open the TriFlex variant builder.
cd "$(dirname "$0")" || exit 1
if [ ! -x .venv/bin/python ]; then
  echo "Setting up Python environment (first run only)..."
  python3 -m venv .venv && .venv/bin/pip install -r cad/requirements.txt || exit 1
fi
exec .venv/bin/python cad/gui.py
