"""Centralized path helpers for PyInstaller compatibility.

When running as a bundled .exe, PyInstaller sets `sys._MEIPASS` to the
temporary directory where bundled data files are extracted.  For a --onedir
build the data sits next to the .exe.

- `BUNDLE_DIR`  → where read-only bundled assets live (client/, YesBoss.mp3, …)
- `APP_DIR`     → where the .exe (or main.py) lives — writable; used for sunday.db
"""

import os
import sys

# ── Frozen (PyInstaller .exe) vs. normal Python ────────────────
if getattr(sys, 'frozen', False):
    # Running as a PyInstaller bundle
    BUNDLE_DIR = sys._MEIPASS          # read-only bundled assets
    APP_DIR = os.path.dirname(sys.executable)  # writable, next to .exe
else:
    # Running as normal Python script
    BUNDLE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    APP_DIR = BUNDLE_DIR

# ── Convenience paths ──────────────────────────────────────────
DB_PATH = os.path.join(APP_DIR, 'sunday.db')
CLIENT_DIR = os.path.join(BUNDLE_DIR, 'client')
