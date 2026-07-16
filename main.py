import ctypes
import socket
import eel
import shutil
import os

from server.paths import BUNDLE_DIR, APP_DIR, DB_PATH, CLIENT_DIR

# ── Ensure sunday.db exists next to the .exe ───────────────────
# On first run the bundled template is copied to the writable APP_DIR.
_bundled_db = os.path.join(BUNDLE_DIR, 'sunday.db')
if not os.path.exists(DB_PATH) and os.path.exists(_bundled_db):
    shutil.copy2(_bundled_db, DB_PATH)
    print(f'[Init] Copied template database to {DB_PATH}')

import server.command  # Registers eel.expose functions (takeCommand)

eel.init(CLIENT_DIR)

window_width  = 360
window_height = 650
window_x      = 0
window_y      = 0

with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
    s.bind(('localhost', 0))
    server_port = s.getsockname()[1]

eel.start(
    'index.html',
    mode='chrome-app',
    block=True,
    size=(window_width, window_height),
    position=(window_x, window_y),
    options={
        'port': server_port,
        'chromeFlags': [
            '--disable-features=TranslateUI',
            '--no-first-run',
            '--disable-default-apps',
            # f'--window-size={window_width},{window_height}',
            # f'--window-position={window_x},{window_y}',
        ],
    },
)