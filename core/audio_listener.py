"""
core/audio_listener.py
=======================
This is SUNDAY's "always listening" ear. It runs in an infinite loop on a
background thread, recording short clips and checking each one for the
wake word ("sunday", set in config.py).

We deliberately use the SMALL/fast whisper model here ("tiny") because this
loop runs constantly in the background - it needs to be cheap on your CPU.
Once the wake word is heard, control is handed off to a callback function
(passed in from main.py) that does the heavier work of capturing your
real command.
"""

import time
from config import WAKE_WORD, WAKE_CHUNK_SECONDS, WAKE_WORD_MODEL_SIZE
from core.speech_to_text import record_audio, transcribe

# Prevents SUNDAY from triggering itself again while it's already busy
# handling a command (set/cleared by main.py).
_busy = False


def set_busy(value: bool):
    """main.py calls this to pause/resume wake-word listening."""
    global _busy
    _busy = value


def start_listening(on_wake_word_detected):
    """
    Runs forever - intended to be launched on its own background thread.
    `on_wake_word_detected` is a function (passed in from main.py) that
    gets called with no arguments every time SUNDAY hears its name.
    """
    print(f"[SUNDAY] Listening for the wake word '{WAKE_WORD}'...")
    while True:
        if _busy:
            # SUNDAY is already handling a command - skip this cycle.
            time.sleep(0.2)
            continue

        audio_chunk = record_audio(WAKE_CHUNK_SECONDS)
        heard_text = transcribe(audio_chunk, WAKE_WORD_MODEL_SIZE)

        if WAKE_WORD in heard_text:
            print(f"[SUNDAY] Wake word detected (heard: '{heard_text}')")
            on_wake_word_detected()
