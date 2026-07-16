import pyttsx3
import speech_recognition as sr
import threading
import time
import eel
import sqlite3
import difflib
import os
import re
import pygame

from server.paths import DB_PATH

# ── Cooldown Duration (seconds) ───────────────────────────────
COOLDOWN_SECONDS = 1

# ── Mute / Pause State ─────────────────────────────────────────
_is_muted = False
_is_paused = False
_state_lock = threading.Lock()

# ── Database Initialization ────────────────────────────────────
try:
    con = sqlite3.connect(DB_PATH)
    cursor = con.cursor()
    cursor.execute('CREATE TABLE IF NOT EXISTS sys_command (id integer primary key, name VARCHAR(100), path VARCHAR(1000))')
    cursor.execute('CREATE TABLE IF NOT EXISTS web_command (id integer primary key, name VARCHAR(100), url VARCHAR(1000))')
    cursor.execute('CREATE TABLE IF NOT EXISTS contacts (id integer primary key, name VARCHAR(100), phone VARCHAR(20))')
    con.commit()
    con.close()
except Exception as e:
    print(f'Error initializing database: {e}')

# ── TTS Engine (singleton — don't re-init every call) ─────────
_engine = None
_engine_lock = threading.Lock()

def _get_engine():
    global _engine
    if _engine is None:
        _engine = pyttsx3.init()
        _engine.setProperty('rate', 175)
        _engine.setProperty('volume', 1.0)
        voices = _engine.getProperty('voices')
        for voice in voices:
            if 'english' in voice.name.lower() or 'zira' in voice.name.lower() or 'david' in voice.name.lower():
                _engine.setProperty('voice', voice.id)
                break
    return _engine


def speak_text(text):
    """Speak text using a persistent TTS engine (faster, no re-init lag)."""
    if not text or not text.strip():
        return
    if _is_muted:
        print(f"[Muted] Would have said: {text}")
        return
    with _engine_lock:
        engine = _get_engine()
        engine.say(text)
        engine.runAndWait()


# ═══════════════════════════════════════════════════════════════
#  RECOGNIZER — two separate tunings
# ═══════════════════════════════════════════════════════════════
# WAKE recognizer: optimized to catch a short trigger phrase quickly and
# cheaply. We deliberately keep phrase_time_limit short here — its ONLY
# job is to hear "hey sunday", not the command that follows.
_wake_recognizer = None

def _get_wake_recognizer():
    global _wake_recognizer
    if _wake_recognizer is None:
        r = sr.Recognizer()
        r.pause_threshold = 0.6
        r.phrase_threshold = 0.3
        r.non_speaking_duration = 0.4
        r.energy_threshold = 400
        r.dynamic_energy_threshold = True
        r.dynamic_energy_adjustment_damping = 0.15
        r.dynamic_energy_ratio = 1.5
        _wake_recognizer = r
    return _wake_recognizer


# COMMAND recognizer: optimized to capture a full spoken sentence without
# clipping. Longer pause_threshold means it waits for a real pause before
# cutting you off, instead of chopping "vs code" into "vs".
_cmd_recognizer = None

def _get_cmd_recognizer():
    global _cmd_recognizer
    if _cmd_recognizer is None:
        r = sr.Recognizer()
        r.pause_threshold = 1.1
        r.phrase_threshold = 0.3
        r.non_speaking_duration = 0.6
        r.energy_threshold = 400
        r.dynamic_energy_threshold = True
        r.dynamic_energy_adjustment_damping = 0.15
        r.dynamic_energy_ratio = 1.5
        _cmd_recognizer = r
    return _cmd_recognizer


# ═══════════════════════════════════════════════════════════════
#  KNOWN COMMAND VOCABULARY + FUZZY CORRECTION
# ═══════════════════════════════════════════════════════════════
# Google's free STT can't take a custom vocabulary, so we can't stop it
# from mishearing "leetcode" as "lead code" at the source. Instead we
# fuzzy-correct AFTER recognition: if a chunk of what it heard is close
# enough to something we know about, we swap in the known term.

_STATIC_VOCAB = [
    'vs code', 'visual studio code', 'chrome', 'youtube', 'leetcode',
    'flipkart', 'spotify', 'notepad', 'file explorer', 'calculator',
    'settings', 'terminal', 'command prompt', 'whatsapp', 'gmail',
    'send message', 'send whatsapp',
]

def _load_known_vocab():
    """Pull known app/site names from the db and merge with static list."""
    vocab = list(_STATIC_VOCAB)
    try:
        con = sqlite3.connect(DB_PATH)
        cursor = con.cursor()
        cursor.execute('SELECT name FROM sys_command')
        vocab += [r[0].lower() for r in cursor.fetchall()]
        cursor.execute('SELECT name FROM web_command')
        vocab += [r[0].lower() for r in cursor.fetchall()]
        con.close()
    except Exception as e:
        print(f'[Vocab] Could not load db vocab: {e}')
    return vocab


def correct_query(query, threshold=0.78):
    """
    Fuzzy-match trailing words in `query` against known commands and
    substitute in the closest known term when confidence is high enough.
    E.g. 'open lead code' -> 'open leetcode', 'open vs' -> 'open vs code'
    (only if 'vs' is a strong-enough partial match).
    """
    if not query:
        return query

    vocab = _load_known_vocab()
    words = query.split()

    # Try to find the best-matching known phrase against the trailing
    # 1, 2, or 3 words of the command (that's where app/site names live:
    # "open X", "play X on youtube", etc.)
    best_ratio = 0.0
    best_match = None
    best_span = None

    for window_size in (1, 2, 3):
        if window_size > len(words):
            continue
        tail = ' '.join(words[-window_size:])
        for term in vocab:
            ratio = difflib.SequenceMatcher(None, tail, term).ratio()
            if ratio > best_ratio:
                best_ratio = ratio
                best_match = term
                best_span = window_size

    if best_ratio >= threshold and best_match:
        corrected = ' '.join(words[:-best_span] + [best_match])
        if corrected != query:
            print(f"[Correction] '{query}' -> '{corrected}' (ratio={best_ratio:.2f})")
        return corrected

    return query


# ═══════════════════════════════════════════════════════════════
#  COMMAND CAPTURE
# ═══════════════════════════════════════════════════════════════
@eel.expose
def takeCommand():
    """Standalone listen (used outside of wake-word flow, e.g. a mic button)."""
    return _listen_and_recognize(_get_cmd_recognizer(), timeout=8, phrase_time_limit=8)


@eel.expose
def listenForCommand():
    """
    Dedicated command listen, called by the frontend RIGHT AFTER a wake
    word is detected (separate from the wake-word audio clip). This is
    what fixes truncated commands like 'vs code' -> 'vs'.
    """
    return _listen_and_recognize(_get_cmd_recognizer(), timeout=6, phrase_time_limit=10)


def _listen_and_recognize(recognizer, timeout, phrase_time_limit):
    try:
        with sr.Microphone() as source:
            print("Calibrating for ambient noise...")
            recognizer.adjust_for_ambient_noise(source, duration=0.5)
            print("Listening...")
            audio = recognizer.listen(source, timeout=timeout, phrase_time_limit=phrase_time_limit)

        print("Recognizing...")
        query = recognizer.recognize_google(audio, language='en-IN')
        print(f"User said: {query}")
        query = query.lower()
        query = correct_query(query)
        return query

    except sr.WaitTimeoutError:
        print("No speech detected within timeout.")
        return ""
    except sr.UnknownValueError:
        print("Could not understand audio.")
        return ""
    except sr.RequestError as e:
        print(f"Google Speech API error: {e}")
        try:
            query = recognizer.recognize_sphinx(audio)
            print(f"[Offline] User said: {query}")
            return correct_query(query.lower())
        except Exception:
            return ""
    except Exception as e:
        print(f"Unexpected error: {e}")
        return ""


@eel.expose
def set_mute(muted):
    global _is_muted
    with _state_lock:
        _is_muted = bool(muted)
    print(f"Mute set to: {_is_muted}")
    return _is_muted


@eel.expose
def get_mute():
    return _is_muted


@eel.expose
def set_paused(paused):
    global _is_paused
    with _state_lock:
        _is_paused = bool(paused)
    print(f"Paused set to: {_is_paused}")
    return _is_paused


@eel.expose
def get_paused():
    return _is_paused


@eel.expose
def allCommands():
    if _is_paused:
        print("[Paused] Ignoring command — assistant is paused.")
        return "__PAUSED__"
    query = takeCommand()
    print(query)
    if not query:
        return query
    return _execute_command(query)


@eel.expose
def processCommand(query):
    """Process a command from already-captured text (no new listen needed)."""
    if _is_paused:
        return "__PAUSED__"
    if not query or not query.strip():
        return ""
    query = query.strip().lower()
    query = correct_query(query)
    print(f"[processCommand] Processing: {query}")
    return _execute_command(query)


def _execute_command(query):
    if 'open' in query:
        from server.feature import openCommand
        openCommand(query)
    elif 'on youtube' in query:
        from server.feature import PlayYoutube
        PlayYoutube(query)
    elif re.search(r'send\s+(?:a\s+)?(?:the\s+)?message', query) or 'whatsapp' in query or 'send whatsapp' in query:
        from server.feature import SendWhatsApp
        SendWhatsApp(query)
    else:
        speak_text("Command not recognized. Please try again.")
        print("Command not recognized. Please try again.")

    # ── 3-second cooldown / reset pause after every command ────
    print(f"[Cooldown] Waiting {COOLDOWN_SECONDS}s before next command...")
    time.sleep(COOLDOWN_SECONDS)
    print("[Cooldown] Ready for next command.")

    return query


@eel.expose
def get_cooldown_seconds():
    """Return the cooldown duration so the frontend can display a countdown."""
    return COOLDOWN_SECONDS


@eel.expose
def add_app_path(name, path_or_url, app_type):
    try:
        con = sqlite3.connect(DB_PATH)
        cursor = con.cursor()
        if app_type == 'system':
            cursor.execute('INSERT INTO sys_command VALUES (null, ?, ?)', (name, path_or_url))
        else:
            cursor.execute('INSERT INTO web_command VALUES (null, ?, ?)', (name, path_or_url))
        con.commit()
        con.close()
        return True
    except Exception as e:
        print(f'Error adding app path: {e}')
        return False


@eel.expose
def get_all_app_paths():
    try:
        con = sqlite3.connect(DB_PATH)
        cursor = con.cursor()
        cursor.execute('SELECT id, name, path FROM sys_command')
        sys_results = [{'id': r[0], 'name': r[1], 'path': r[2], 'type': 'system'} for r in cursor.fetchall()]
        cursor.execute('SELECT id, name, url FROM web_command')
        web_results = [{'id': r[0], 'name': r[1], 'path': r[2], 'type': 'web'} for r in cursor.fetchall()]
        con.close()
        return sys_results + web_results
    except Exception as e:
        print(f'Error getting app paths: {e}')
        return []


@eel.expose
def delete_app_path(app_id, app_type):
    try:
        con = sqlite3.connect(DB_PATH)
        cursor = con.cursor()
        if app_type == 'system':
            cursor.execute('DELETE FROM sys_command WHERE id = ?', (app_id,))
        else:
            cursor.execute('DELETE FROM web_command WHERE id = ?', (app_id,))
        con.commit()
        con.close()
        return True
    except Exception as e:
        print(f'Error deleting app path: {e}')
        return False


# ═══════════════════════════════════════════════════════════════
#  CONTACTS CRUD (for WhatsApp messaging)
# ═══════════════════════════════════════════════════════════════

@eel.expose
def add_contact(name, phone):
    try:
        con = sqlite3.connect(DB_PATH)
        cursor = con.cursor()
        cursor.execute('INSERT INTO contacts VALUES (null, ?, ?)', (name, phone))
        con.commit()
        con.close()
        return True
    except Exception as e:
        print(f'Error adding contact: {e}')
        return False


@eel.expose
def get_all_contacts():
    try:
        con = sqlite3.connect(DB_PATH)
        cursor = con.cursor()
        cursor.execute('SELECT id, name, phone FROM contacts')
        results = [{'id': r[0], 'name': r[1], 'phone': r[2]} for r in cursor.fetchall()]
        con.close()
        return results
    except Exception as e:
        print(f'Error getting contacts: {e}')
        return []


@eel.expose
def delete_contact(contact_id):
    try:
        con = sqlite3.connect(DB_PATH)
        cursor = con.cursor()
        cursor.execute('DELETE FROM contacts WHERE id = ?', (contact_id,))
        con.commit()
        con.close()
        return True
    except Exception as e:
        print(f'Error deleting contact: {e}')
        return False


# ═══════════════════════════════════════════════════════════════
#  WAKE WORD DETECTION — detection ONLY, no command in this clip
# ═══════════════════════════════════════════════════════════════
_WAKE_PHRASE = 'hey sunday'

def _detect_wake_word(text, threshold=0.72):
    """
    Fuzzy-matches sliding word windows against 'hey sunday'.
    Returns (found: bool, remaining_command: str) — remaining_command is
    kept for logging/debugging only; the real command capture happens in
    a separate listenForCommand() call from the frontend.
    """
    words = text.split()
    best_ratio = 0.0
    best_end = -1

    for window_size in (1, 2, 3):
        for start in range(len(words) - window_size + 1):
            window = ' '.join(words[start:start + window_size])
            ratio = difflib.SequenceMatcher(None, window, _WAKE_PHRASE).ratio()
            if ratio > best_ratio:
                best_ratio = ratio
                best_end = start + window_size

    if best_ratio >= threshold:
        remaining = ' '.join(words[best_end:]).strip()
        return True, remaining

    return False, ''


_YES_BOSS_MP3 = os.path.join(os.path.dirname(__file__), 'YesBoss.mp3')
pygame.mixer.init()


def _play_yes_boss():
    try:
        pygame.mixer.music.load(_YES_BOSS_MP3)
        pygame.mixer.music.play()
        while pygame.mixer.music.get_busy():
            pygame.time.wait(50)
        print("[Wake Word] YesBoss.mp3 played.")
    except Exception as e:
        print(f"[Wake Word] Error playing YesBoss.mp3: {e}")
        speak_text("Yes boss")


@eel.expose
def listenForWakeWord():
    """
    Listen ONLY for the wake word 'Hey Sunday'. Deliberately short
    phrase_time_limit — this clip's one job is catching the trigger
    phrase quickly, not the command after it.

    Returns:
      {'status': 'detected'}      — wake word heard; frontend should now
                                      call listenForCommand() separately.
      {'status': 'not_detected'}
      {'status': '__MUTED__'}
      {'status': '__PAUSED__'}
    """
    if _is_muted:
        return {'status': '__MUTED__'}
    if _is_paused:
        return {'status': '__PAUSED__'}

    r = _get_wake_recognizer()

    try:
        with sr.Microphone() as source:
            r.adjust_for_ambient_noise(source, duration=0.5)
            audio = r.listen(source, timeout=5, phrase_time_limit=3)

        frame_count = len(audio.frame_data)
        duration_sec = frame_count / (audio.sample_rate * audio.sample_width)
        if duration_sec < 0.4:
            return {'status': 'not_detected'}

        text = r.recognize_google(audio, language='en-IN').lower()
        print(f"[Wake Word] Heard: {text}")

        detected, remaining_command = _detect_wake_word(text)
        if detected:
            print("[Wake Word] *** HEY SUNDAY detected! ***")
            _play_yes_boss()
            # NOTE: remaining_command from this clip is unreliable (it's
            # from a 3s clip meant only to catch the trigger phrase).
            # The frontend should call listenForCommand() next instead
            # of relying on this value for anything but debug logging.
            return {'status': 'detected', 'command': remaining_command}

        return {'status': 'not_detected', 'heard': text}

    except sr.WaitTimeoutError:
        return {'status': 'not_detected'}
    except sr.UnknownValueError:
        return {'status': 'not_detected'}
    except sr.RequestError as e:
        print(f"[Wake Word] Speech API error: {e}")
        return {'status': 'not_detected'}
    except Exception as e:
        print(f"[Wake Word] Error: {e}")
        return {'status': 'not_detected'}