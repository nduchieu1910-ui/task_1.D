# Chay toan bo test va in bang kiem tra nhiem vu 1.6
Set-Location $PSScriptRoot
& .\.venv\Scripts\python.exe -m pytest -v
& .\.venv\Scripts\python.exe scripts\check_task.py
