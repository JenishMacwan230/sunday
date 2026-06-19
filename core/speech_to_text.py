"""
core/speech_to_text.py
=======================
Handles turning audio (your voice) into text, using faster-whisper.

Two separate functions on purpose:
  - record_audio(seconds)    -> just captures sound from your microphone
  - transcribe(audio, model) -> turns recorded sound into text

Keeping "recording" and "transcribing" separate lets audio_listener.py use
the tiny/fast model on short wake-word chunks, while main.py uses the
bigger/more-accurate model on your full spoken command.
"""

import numpy as np
import sounddevice as sd
from faster_whisper import WhisperModel

from config import WHISPER_DEVICE, WHISPER_COMPUTE_TYPE

SAMPLE_RATE = 16000  # 16kHz is what Whisper models expect as input

# Whisper models are loaded once and cached here, keyed by size ("tiny",
# "base", etc.), so we never reload the same model from disk twice.
_loaded_models = {}


def get_model(model_size: str) -> WhisperModel:
    """Loads a whisper model the first time it's needed, then reuses it."""
    if model_size not in _loaded_models:
        print(f"[SUNDAY] Loading Whisper model '{model_size}' (first time only)...")
        _loaded_models[model_size] = WhisperModel(
            model_size, device=WHISPER_DEVICE, compute_type=WHISPER_COMPUTE_TYPE
        )
    return _loaded_models[model_size]


def record_audio(seconds: float) -> np.ndarray:
    """
    Records `seconds` of audio from the default microphone and returns it
    as a NumPy array of floating-point samples (the format Whisper expects).
    """
    frame_count = int(seconds * SAMPLE_RATE)
    audio = sd.rec(frame_count, samplerate=SAMPLE_RATE, channels=1, dtype="float32")
    sd.wait()  # blocks here until the recording finishes
    return audio.flatten()


def transcribe(audio: np.ndarray, model_size: str) -> str:
    """
    Runs a NumPy audio array through the given whisper model and returns
    the recognised text, lowercased and trimmed of extra whitespace.
    """
    model = get_model(model_size)
    segments, _info = model.transcribe(audio, language="en")
    text = " ".join(segment.text for segment in segments)
    return text.strip().lower()
