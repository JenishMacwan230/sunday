# SUNDAY

SUNDAY is a Windows desktop voice assistant built with Python, Eel, and a browser-based UI. It listens for a wake word or manual mic input, understands spoken commands, and can open apps, open websites, or play YouTube searches.

## What it can do

- Listen for commands from the app window
- Listen for the wake word and then wait for the next command
- Open installed apps from saved paths
- Open websites from saved URLs
- Play a YouTube search query
- Mute, pause, and show a short cooldown after each command
- Store custom app and website shortcuts in SQLite

## Screenshots

Put your images in `client/assets/image/` and update the filenames below to match your files.

![SUNDAY home screen](client/assets/image/home-screen.png)
![Wake word mode](client/assets/image/wake-word-mode.png)
![App paths manager](client/assets/image/app-paths.png)

## Project structure

```text
SUNDAY/
├── main.py
├── requirements.txt
├── README.md
├── sunday.db
├── server/
│   ├── command.py
│   ├── feature.py
│   └── db.py
└── client/
    ├── index.html
    ├── app.js
    ├── controller.js
    ├── styles.css
    └── assets/
        └── image/
```

## How it works

`main.py` starts the app with Eel and loads the UI from `client/index.html`. The browser window runs as a small desktop app.

`server/command.py` handles speech recognition, text-to-speech, mute/pause state, wake-word detection, and the command cooldown.

`server/feature.py` handles the actual actions, such as opening apps from the SQLite database, opening web links, or sending a YouTube search to the browser.

`client/app.js` controls the interface state, the mic button, cooldown display, mute/pause buttons, and the app paths modal.

## Requirements

- Windows 10 or Windows 11
- Python 3.13 or compatible version for your environment
- Google Chrome installed on the machine
- A working microphone

## Setup

1. Open a terminal in the project folder.
2. Activate your virtual environment if you are using one.

```powershell
envsunday\Scripts\activate
```

3. Install dependencies.

```powershell
pip install -r requirements.txt
```

4. If you are using a fresh environment and any imports are missing, install the missing packages that your local setup requires.

## Run the app

```powershell
python main.py
```

The app opens as a small desktop window in Chrome app mode.

## Using SUNDAY

- Use **Manual** mode to click the mic and speak a command right away.
- Use **Wake Word** mode to keep listening for "Hey Sunday" first.
- Use the **Mute** button to stop spoken responses.
- Use the **Pause** button to temporarily block commands.
- Use **App Paths** to save custom app paths or URLs.

## Supported commands

The assistant currently recognizes commands such as:

- `open chrome`
- `open notepad`
- `open youtube`
- `play lo-fi on youtube`
- `open <saved app name>`
- `open <saved website name>`

## App paths database

Saved shortcuts are stored in `sunday.db` in two tables:

- `sys_command` for Windows apps and local paths
- `web_command` for websites and URLs

You can add entries from the UI with the App Paths modal.

## Notes for adding images

If you want to replace the sample screenshots later, keep the files in:

`client/assets/image/`

Suggested filenames:

- `home-screen.png`
- `wake-word-mode.png`
- `app-paths.png`

## Troubleshooting

- If the microphone does not respond, check Windows microphone permissions and confirm the correct input device is selected.
- If app opening fails, confirm the saved path is correct and the app exists on the machine.
- If voice output does not play, check that audio output is not muted in Windows.
- If the window does not launch correctly, make sure Chrome is installed and available to Eel.

<!-- ## License

Add your preferred license here if you want to publish the project. -->