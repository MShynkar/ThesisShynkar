"""Shared helpers for the diploma measurement scripts.

Run every script from the `backend/` directory with the project venv, e.g.:

    cd backend
    ./.venv/Scripts/python.exe ../scripts/dipl_measurements/env_report.py

The scripts deliberately reuse the application's own settings, DB session and
Ollama client so that what we measure is exactly what the running system does
(no separate code path). Nothing here mutates application code.
"""
import os
import sys

# Windows consoles default to cp1252; force UTF-8 so Cyrillic queries print.
try:
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
except Exception:
    pass

# Make `app` importable when invoked from the repo root or from backend/.
_HERE = os.path.dirname(os.path.abspath(__file__))
_BACKEND = os.path.normpath(os.path.join(_HERE, "..", "..", "backend"))
if _BACKEND not in sys.path:
    sys.path.insert(0, _BACKEND)
# The app loads `.env` relative to CWD; make sure we read backend/.env.
os.chdir(_BACKEND)
