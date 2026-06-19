"""
core/text_to_speech.py
=======================
Gives SUNDAY a voice. Whenever it performs an action, it speaks a short
confirmation out loud (e.g. "Opening YouTube"), so you get feedback without
needing to look at the screen.

pyttsx3 is fully offline - it uses the voices already installed on Windows
(via SAPI5), so this works with no internet connection and no API cost.
"""

import pyttsx3
from config import VOICE_FEEDBACK_ENABLED, SPEECH_RATE

# We create ONE engine instance and reuse it everywhere, instead of creating
# a new one on every call (that would be slow and can cause audio glitches).
_engine = pyttsx3.init()
_engine.setProperty("rate", SPEECH_RATE)


def speak(text: str):
    """Speaks `text` out loud, if voice feedback is enabled in config.py."""
    print(f"[SUNDAY] {text}")
    if not VOICE_FEEDBACK_ENABLED:
        return
    _engine.say(text)
    _engine.runAndWait()
