import ctypes
import socket
import eel
import server.command  # Registers eel.expose functions (takeCommand)

eel.init('client')

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