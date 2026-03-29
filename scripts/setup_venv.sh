#!/bin/bash
set -e

python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

echo "venv hazırlandı. Kaynak: source .venv/bin/activate"
