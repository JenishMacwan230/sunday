"""
main.py
========
SUNDAY's entry point. Run this file to start the assistant:

    python main.py

WHAT HAPPENS WHEN YOU RUN IT:
  1. The memory database is prepared (and seeded with a few default
     shortcuts like "youtube" and "gmail").
  2. A background thread starts listening for the wake word ("sunday").
  3. The floating mic icon + system tray icon are shown on the main thread.

Either SAYING "Sunday" OR CLICKING the floating icon calls the exact same
`handle_command()` function below - that's what makes both trigger methods
behave identically.
"""

import threading

from core import memory, audio_listener
from core.speech_to_text import record_audio, transcribe
from core.intent_parser import parse_command
from core.text_to_speech import speak
from actions.action_executor import execute
from ui.floating_icon import run_ui
from config import COMMAND_SECONDS, COMMAND_MODEL_SIZE


def handle_command():
    """
    Runs ONE full command cycle:
      record your voice -> transcribe it -> ask the LLM what to do -> do it.

    Used as the callback for BOTH the wake word and the floating icon click,
    so the two trigger methods always behave identically.
    """
    audio_listener.set_busy(True)  # pause wake-word listening while we work
    try:
        speak("Listening")
        audio = record_audio(COMMAND_SECONDS)
        spoken_text = transcribe(audio, COMMAND_MODEL_SIZE)
        print(f"[SUNDAY] You said: {spoken_text}")

        if not spoken_text:
            speak("I didn't catch that")
            return

        # First check memory for an exact match - this skips the LLM call
        # entirely for things you've said before, which is both faster
        # and free.
        action = memory.lookup(spoken_text)
        if action is None:
            action = parse_command(spoken_text)
            memory.remember(spoken_text, action)

        execute(action)
    finally:
        audio_listener.set_busy(False)  # resume wake-word listening


def start_wake_word_thread():
    """
    Runs SUNDAY's "always listening" loop on a separate thread, so it
    never blocks the UI. `daemon=True` means this thread automatically
    stops when the main program exits.
    """
    thread = threading.Thread(
        target=audio_listener.start_listening,
        args=(handle_command,),
        daemon=True,
    )
    thread.start()


def main():
    print("[SUNDAY] Starting up...")
    memory.seed_defaults()

    start_wake_word_thread()

    # run_ui() blocks here until you quit the app - keep it last.
    run_ui(on_listen_trigger=handle_command)


if __name__ == "__main__":
    main()
