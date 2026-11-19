#!/usr/bin/env bash
cd "$(dirname "$0")" && .venv/bin/python -m pytest -v && .venv/bin/python scripts/check_task.py
