# SUNDAY — Local Voice-Controlled Desktop Assistant

SUNDAY listens for its name, turns what you say into a structured command
using a **local** LLM (no cloud, no API key), and then performs the action
on your Windows laptop — opening apps, navigating File Explorer, dictating
text, or jumping straight to a website in Chrome.

This README is written assuming you're newer to Python — every step says
not just *what* to run, but *why*.

---

## 1. How the project is organized

```
SUNDAY/
├── main.py                  <- run this file to start SUNDAY
├── config.py                <- every adjustable setting lives here
├── requirements.txt         <- list of Python packages to install
├── memory.db                <- auto-created on first run (your learned shortcuts)
│
├── core/                    <- SUNDAY's senses + brain
│   ├── audio_listener.py    <- background loop listening for "sunday"
│   ├── speech_to_text.py    <- microphone recording + Whisper transcription
│   ├── intent_parser.py     <- talks to the local LLM (Ollama)
│   ├── text_to_speech.py    <- speaks confirmations back to you
│   └── memory.py            <- remembers your frequent shortcuts (SQLite)
│
├── actions/                 <- SUNDAY's hands — one file per capability
│   ├── action_executor.py   <- routes the LLM's decision to the right file below
│   ├── app_launcher.py      <- opens applications
│   ├── apps_config.py       <- editable list of app name -> path
│   ├── browser_control.py   <- opens Chrome / runs searches
│   ├── file_explorer.py     <- step-by-step Explorer navigation
│   └── typing_tool.py       <- types dictated text
│
├── ui/
│   └── floating_icon.py     <- the floating mic icon + system tray icon
│
└── assets/
    └── mic_icon.png         <- icon used by the floating UI
```

**Why split into so many small files?** Each file does exactly one job. If
"opening apps" misbehaves, you know to look in `app_launcher.py` and
nowhere else. This also means you can extend one feature (say, add a new
action type) without touching code that has nothing to do with it.

A quick Python note for each file: every `.py` file is a **module**, and a
folder containing an `__init__.py` file is a **package** — that's why
`core/`, `actions/`, and `ui/` each have one. It just tells Python "treat
this folder as a place I can import code from."

---

## 2. Prerequisites

| Requirement | Notes |
|---|---|
| Windows 10/11 | The app/file/browser control code is Windows-specific |
| Python 3.10+ | [python.org](https://python.org) — tick "Add Python to PATH" during install |
| Google Chrome | Installed at the default path, or update `CHROME_PATH` in `config.py` |
| A working microphone | Built-in laptop mic is fine |
| ~8 GB free RAM | For running the local LLM comfortably |
| [Ollama](https://ollama.com) | The local LLM runtime — separate install, see below |

---

## 3. Installation

Open **PowerShell** or **Command Prompt** in the `SUNDAY` folder, then:

```bash
# 1. Create a virtual environment (an isolated space for this project's packages)
python -m venv venv
venv\Scripts\activate

# 2. Install all required Python packages
pip install -r requirements.txt
```

**What's a virtual environment?** Normally, packages you `pip install` go
into your one global Python installation. A virtual environment (`venv`)
creates a private copy just for this project, so SUNDAY's packages never
conflict with anything else you have installed. You'll see `(venv)` appear
in your terminal prompt once it's active — run `venv\Scripts\activate`
again any time you reopen a terminal to work on this project.

### Install Ollama and the LLM model

```bash
# Download & install Ollama from https://ollama.com (Windows installer)

# Then pull the model SUNDAY uses for understanding commands (~4-5 GB, one-time):
ollama pull qwen2.5:7b-instruct

# Confirm it works:
ollama run qwen2.5:7b-instruct "Reply with the single word: ready"
```

Ollama runs as a background Windows service after installation — you don't
need to keep a terminal open for it.

---

## 4. Running SUNDAY

```bash
venv\Scripts\activate
python main.py
```

The first run will take a little longer — `faster-whisper` downloads its
speech models the first time they're used, and caches them after that.

You should see:
```
[SUNDAY] Starting up...
[SUNDAY] Listening for the wake word 'sunday'...
```
...and a small blue mic icon should appear in the top-left of your screen.

**Try it:** say *"Sunday"*, wait for the "Listening" confirmation, then say
*"open YouTube"*.

To trigger a command without speaking the wake word, just **click the
floating icon** — it behaves identically.

---

## 5. Customizing SUNDAY

| I want to... | Edit this file |
|---|---|
| Change the wake word | `config.py` → `WAKE_WORD` |
| Add/change which apps SUNDAY can open | `actions/apps_config.py` |
| Add a permanent shortcut (e.g. "netflix") | Edit the `defaults` dict in `core/memory.py`, or just say it a couple of times — SUNDAY learns it automatically |
| Use a smaller/faster or larger/more-accurate LLM | `config.py` → `OLLAMA_MODEL` (must match a model you've `ollama pull`'d) |
| Point to a different Chrome install | `config.py` → `CHROME_PATH` |
| Turn off spoken confirmations | `config.py` → `VOICE_FEEDBACK_ENABLED = False` |

---

## 6. How a command actually flows through the code

1. **`audio_listener.py`** records a short clip every couple of seconds and
   checks it for the word "sunday" using a tiny, fast Whisper model.
2. Once detected, **`main.py`**'s `handle_command()` takes over: it records
   a longer clip and transcribes it with a more accurate Whisper model.
3. **`memory.py`** checks if you've said this exact phrase before. If yes,
   it skips straight to step 5 — no LLM call needed, instant response.
4. If it's new, **`intent_parser.py`** sends the text to your local LLM
   (via Ollama) and gets back ONE JSON object describing the action.
5. **`action_executor.py`** reads that JSON and calls the matching function
   in `actions/` (open a URL, launch an app, navigate Explorer, type text).
6. **`text_to_speech.py`** speaks a short confirmation.

---

## 7. Troubleshooting

| Problem | Likely fix |
|---|---|
| `ModuleNotFoundError` | Make sure `(venv)` is showing in your terminal — run `venv\Scripts\activate` first |
| Nothing happens when you say "Sunday" | Check your microphone is set as the default recording device in Windows Sound settings |
| LLM replies are slow | Try a smaller model, e.g. `phi3:mini`, and update `OLLAMA_MODEL` in `config.py` |
| `keyboard` module needs admin rights | Some systems require running the terminal "as Administrator" for global keyboard control |
| Chrome doesn't open | Double check `CHROME_PATH` in `config.py` matches where Chrome is actually installed |
| Icon doesn't appear | Confirm `assets/mic_icon.png` exists and `PySide6` installed correctly |

---

## 8. Adding SUNDAY to Windows startup (optional)

1. Press `Win + R`, type `shell:startup`, press Enter.
2. Create a shortcut to a small `.bat` file in this folder containing:
   ```bat
   call venv\Scripts\activate.bat
   pythonw main.py
   ```
   (`pythonw` instead of `python` runs without a visible console window.)
3. Place that shortcut inside the startup folder. SUNDAY will now launch
   automatically every time you log in.

---

## 9. Future upgrade ideas

- Swap the simple Whisper-based wake-word check for **openWakeWord**, a
  dedicated wake-word engine — more CPU-efficient for 24/7 listening.
- Use **pywinauto** in `file_explorer.py` to steer the *same* Explorer
  window instead of opening a new one each step.
- Add a small settings window (PySide6) to edit shortcuts visually instead
  of editing files directly.
