"""
config.py
=========
Central settings file for SUNDAY.

WHY THIS FILE EXISTS:
Instead of scattering "magic values" (model names, file paths, timings)
across every script, we keep them all here. If you ever want to change the
wake word, swap the LLM model, or point to a different Chrome install, you
only need to edit THIS file - nothing else.
"""

import os

# ----------------------------------------------------------------------
# WAKE WORD SETTINGS
# ----------------------------------------------------------------------
# The word SUNDAY listens for in the background to "wake up" and start
# recording your actual command.
WAKE_WORD = "sunday"

# How many seconds of audio we record and check, on a loop, while waiting
# for the wake word. Smaller = reacts faster but uses more CPU.
WAKE_CHUNK_SECONDS = 2.5

# How many seconds SUNDAY records AFTER waking up, to capture your command.
COMMAND_SECONDS = 5

# ----------------------------------------------------------------------
# SPEECH-TO-TEXT (faster-whisper) SETTINGS
# ----------------------------------------------------------------------
# We use TWO whisper models on purpose:
#   - a tiny, very fast one just to spot the wake word (cheap, runs constantly)
#   - a slightly bigger, more accurate one to transcribe your real command
#     (runs only after you've been "woken up", so speed matters less there)
WAKE_WORD_MODEL_SIZE = "tiny"
COMMAND_MODEL_SIZE = "base"

WHISPER_DEVICE = "cpu"          # change to "cuda" if you have a supported NVIDIA GPU
WHISPER_COMPUTE_TYPE = "int8"   # int8 = fastest on CPU, with minimal accuracy loss

# ----------------------------------------------------------------------
# LOCAL LLM (Ollama) SETTINGS
# ----------------------------------------------------------------------
OLLAMA_MODEL = "qwen2.5:7b-instruct"

# ----------------------------------------------------------------------
# BROWSER SETTINGS
# ----------------------------------------------------------------------
# Update this path if Chrome is installed somewhere else on your machine.
CHROME_PATH = r"C:\Program Files\Google\Chrome\Application\chrome.exe"

# ----------------------------------------------------------------------
# PATHS (you shouldn't normally need to touch these)
# ----------------------------------------------------------------------
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MEMORY_DB_PATH = os.path.join(BASE_DIR, "memory.db")
ASSETS_DIR = os.path.join(BASE_DIR, "assets")
MIC_ICON_PATH = os.path.join(ASSETS_DIR, "mic_icon.png")

# ----------------------------------------------------------------------
# VOICE FEEDBACK
# ----------------------------------------------------------------------
VOICE_FEEDBACK_ENABLED = True
SPEECH_RATE = 175   # words per minute for text-to-speech
