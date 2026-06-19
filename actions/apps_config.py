"""
actions/apps_config.py
=======================
A simple lookup table mapping spoken app names to how SUNDAY should launch
them on Windows. Kept in its OWN file, separate from the launching LOGIC in
app_launcher.py, so you can add your own apps here without touching any
actual code.

Two kinds of values work here:
  - Just the app's normal Windows name (e.g. "notepad", "calc") - Windows
    can usually find these on its own.
  - A full .exe path, copied from File Explorer's address bar, for apps
    Windows can't find by name alone (e.g. Spotify).

Add as many of your own apps as you like, following the same pattern.
"""

KNOWN_APPS = {
    "notepad": "notepad",
    "calculator": "calc",
    "paint": "mspaint",
    "word": "winword",
    "excel": "excel",
    "powerpoint": "powerpnt",
    "file explorer": "explorer",
    "vs code": "code",
    "visual studio code": "code",
    # Example of a full path - edit this to match where Spotify is
    # actually installed on YOUR machine:
    "spotify": r"C:\Users\%USERNAME%\AppData\Roaming\Spotify\Spotify.exe",
}
