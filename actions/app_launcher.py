"""
actions/app_launcher.py
========================
Handles the "open_app" action - launching a Windows application from its
spoken name.
"""

import os
import subprocess

from actions.apps_config import KNOWN_APPS


def open_app(app_name: str) -> bool:
    """
    Looks up `app_name` (e.g. "notepad", "spotify") in KNOWN_APPS and
    launches it. If it isn't in our list, we still try Windows' own
    `start` command with the raw name - it can often find apps anyway.
    """
    key = app_name.lower().strip()
    target = KNOWN_APPS.get(key, app_name)

    # os.path.expandvars turns "%USERNAME%" into your actual Windows username
    target = os.path.expandvars(target)

    try:
        # "start" is the same mechanism the Windows Run dialog (Win+R) uses,
        # so it can resolve plain app names as well as full paths.
        subprocess.Popen(f'start "" "{target}"', shell=True)
        return True
    except Exception as error:
        print(f"[SUNDAY] Failed to open '{app_name}': {error}")
        return False
