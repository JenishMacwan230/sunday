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
import signal
import sys

from config import COMMAND_SECONDS, COMMAND_MODEL_SIZE, DEBUG_CONSOLE_OUTPUT, QUIET_MODE
from core import memory, audio_listener
from core.speech_to_text import record_audio_with_vad, transcribe
from core.intent_parser import parse_command
from core.text_to_speech import speak
from actions.action_executor import execute
from ui.floating_icon import run_ui


def _log(message: str, verbose: bool = False):
    """Print only if not in quiet mode, or if verbose is True (important events)."""
    if QUIET_MODE and not verbose:
        return
    if DEBUG_CONSOLE_OUTPUT:
        print(f"[SUNDAY] {message}")


def signal_handler(sig, frame):
    """Handle Ctrl+C gracefully."""
    print("\n[SUNDAY] Shutting down gracefully...")
    sys.exit(0)


def handle_command():
    """
    Runs ONE full command cycle:
      record your voice -> transcribe it -> ask the LLM what to do -> do it.

    Used as the callback for BOTH the wake word and the floating icon click,
    so the two trigger methods always behave identically.
    """
    audio_listener.set_busy(True)  # pause wake-word listening while we work
    try:
        print("\n" + "=" * 50)
        print("[SUNDAY] 🎤 STEP 1: Recording your command...")
        print("=" * 50)
        audio = record_audio_with_vad(COMMAND_SECONDS)

        # Check if we actually got any audio
        audio_duration = len(audio) / 16000 if len(audio) > 0 else 0
        print(f"[SUNDAY] 📊 STEP 2: Recording done — got {len(audio)} samples ({audio_duration:.2f}s of audio)")

        if len(audio) == 0:
            print("[SUNDAY] ❌ No audio captured at all!")
            speak("I didn't catch that")
            return

        print(f"[SUNDAY] 🧠 STEP 3: Transcribing with model '{COMMAND_MODEL_SIZE}'...")
        spoken_text = transcribe(audio, COMMAND_MODEL_SIZE)

        print(f"[SUNDAY] 📝 STEP 4: Transcription result = '{spoken_text}'")

        if not spoken_text:
            print("[SUNDAY] ❌ Transcription returned empty (silence or hallucination filtered)")
            speak("I didn't catch that")
            return

        # Show what was heard
        print(f"\n>>> YOU SAID: {spoken_text}\n")

        # Robust stop command detection - check for multiple common phrases
        stop_phrases = {"stop", "stop sunday", "quit", "exit", "shut down",
                        "shutdown", "goodbye", "close sunday", "quit sunday",
                        "exit sunday", "turn off"}
        spoken_lower = spoken_text.strip().lower()

        if spoken_lower in stop_phrases:
            print(f"[SUNDAY] 🛑 STEP 5: Stop phrase detected: '{spoken_lower}'")
            action = {"action": "stop"}
        else:
            # First check memory for an exact match - this skips the LLM call
            # entirely for things you've said before, which is both faster
            # and free.
            action = memory.lookup(spoken_text)
            if action is not None:
                print(f"[SUNDAY] 💾 STEP 5: Found in memory → {action}")
            else:
                print(f"[SUNDAY] 🤖 STEP 5: Sending to LLM for intent parsing...")
                action = parse_command(spoken_text)
                print(f"[SUNDAY] 🎯 STEP 6: LLM returned → {action}")
                memory.remember(spoken_text, action)

        print(f"[SUNDAY] ▶️  Executing action: {action}")
        execute(action)
    except Exception as e:
        print(f"[SUNDAY] 💥 ERROR in handle_command: {e}")
        import traceback
        traceback.print_exc()
    finally:
        audio_listener.set_busy(False)  # resume wake-word listening
        print("[SUNDAY] 👂 Resuming wake-word listening...\n")


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
    # Register Ctrl+C handler for graceful shutdown
    signal.signal(signal.SIGINT, signal_handler)
    
    _log("Starting up...", verbose=True)
    memory.seed_defaults()

    start_wake_word_thread()

    # run_ui() blocks here until you quit the app - keep it last.
    try:
        run_ui(on_listen_trigger=handle_command)
    except KeyboardInterrupt:
        print("\n[SUNDAY] Shutting down gracefully...")
        sys.exit(0)


if __name__ == "__main__":
    main()
