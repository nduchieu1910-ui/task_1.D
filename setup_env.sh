#!/usr/bin/env bash
# Tao moi truong cho D tren macOS/Linux. Chay 1 lan:  bash setup_env.sh
set -e
cd "$(dirname "$0")"
echo "[1/4] Kiem tra Python..."; python3 --version
[ -d .venv ] || { echo "[2/4] Tao .venv..."; python3 -m venv .venv; }
echo "[3/4] Cai thu vien..."
.venv/bin/python -m pip install --upgrade pip
.venv/bin/python -m pip install -r requirements.txt
echo "[4/4] Kiem tra nhiem vu 1.6..."
.venv/bin/python scripts/check_task.py
echo; echo "XONG. Lan sau: source .venv/bin/activate && bash run_app.sh"
