"""
actions/typing_tool.py
========================
Handles the "type_text" action - dictating text into whatever window
currently has focus (a Word doc, a chat box, a search bar, etc.).
"""

import time
import keyboard


def type_text(text: str):
    """
    Types `text` into the currently focused window, simulating real
    keystrokes via the `keyboard` library.
    """
    time.sleep(0.3)  # tiny pause - gives the target window a moment to be ready
    keyboard.write(text)
