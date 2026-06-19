"""
actions/file_explorer.py
==========================
Handles voice-driven File Explorer navigation - things like:
  "open file explorer" -> "go to D drive" -> "open Photos" -> "open vacation.jpg"

SUNDAY keeps track of a "current folder" between commands (the
ExplorerState class below), so each new instruction builds on the last
one - the same way you'd click deeper into folders by hand.

NOTE: each step re-opens a FRESH Explorer window at the new path. This is
the simplest and most reliable approach on Windows. Steering the SAME
window instead would require a more advanced library (pywinauto) - see the
README's "Future Enhancements" section if you want to upgrade to that later.
"""

import os
import subprocess


class ExplorerState:
    """Remembers where SUNDAY currently 'is' in the file system."""

    def __init__(self):
        self.current_path = os.path.expanduser("~")  # starts at your user folder


# One shared instance - every voice command reads/updates the same "location".
_state = ExplorerState()


def navigate(folder_or_drive: str):
    """
    Moves SUNDAY's current folder one level into `folder_or_drive`, then
    opens a fresh Explorer window there.
    Examples of `folder_or_drive`: "Photos", "D:\\", "Documents"
    """
    candidate = os.path.join(_state.current_path, folder_or_drive)

    if os.path.isdir(candidate):
        _state.current_path = candidate
    elif os.path.isdir(folder_or_drive):
        # handles full paths or drive letters typed/spoken directly, e.g. "D:\\"
        _state.current_path = folder_or_drive
    else:
        print(f"[SUNDAY] Couldn't find folder '{folder_or_drive}' in {_state.current_path}")
        return

    subprocess.Popen(f'explorer "{_state.current_path}"')


def open_file(filename: str):
    """Opens a specific file inside SUNDAY's current folder."""
    path = os.path.join(_state.current_path, filename)
    if os.path.isfile(path):
        os.startfile(path)
    else:
        print(f"[SUNDAY] Couldn't find file '{filename}' in {_state.current_path}")


def go_home():
    """Resets SUNDAY's current folder back to your user folder."""
    _state.current_path = os.path.expanduser("~")
    subprocess.Popen(f'explorer "{_state.current_path}"')
