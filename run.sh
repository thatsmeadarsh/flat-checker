#!/bin/bash
cd "$(dirname "$0")"
if [ ! -d ".venv" ]; then
  python3 -m venv .venv
  .venv/bin/pip install -r requirements.txt -q
fi
echo "Starting Kochi Metro Flat Finder at http://localhost:5050"
.venv/bin/python app.py
