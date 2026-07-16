import os
import re
# import sqlite3
import webbrowser
# from playsound import playsound
import eel

from server.command import speak_text
# from server.config import ASSISTANT_NAME
import pywhatkit as kit
import sqlite3

con = sqlite3.connect('sunday.db')
cursor = con.cursor()



def openCommand(query):
    query = query.replace('SUNDAY', "")
    query = query.replace("open", "").strip().lower()

    if query != "":
        try:
            # Try to find the application in sys_command table
            cursor.execute('SELECT path FROM sys_command WHERE LOWER(name) = ?', (query,))
            results = cursor.fetchall()

            if len(results) != 0:
                speak_text("Opening " + query)
                os.startfile(results[0][0])
                return

            # If not found, try to find the URL in web_command table
            cursor.execute('SELECT url FROM web_command WHERE LOWER(name) = ?', (query,))
            results = cursor.fetchall()
            
            if len(results) != 0:
                speak_text("Opening " + query)
                webbrowser.open(results[0][0])
                return

            # If still not found, try to open using os.system
            speak_text("Opening " + query)
            try:
                os.system('start ' + query)
            except Exception as e:
                speak_text(f"Unable to open {query}. Error: {str(e)}")

        except Exception as e:
            speak_text(f"Something went wrong: {str(e)}")


def PlayYoutube(query):
    search_term = extract_yt_term(query)
    if search_term:
        speak_text("Playing " + search_term + " on YouTube")
        kit.playonyt(search_term)
    else:
        speak_text("Sorry, I couldn't find what to play on YouTube.")



def extract_yt_term(command):
    pattern = r'play\s+(.*?)\s+on\s+youtube'
    match = re.search(pattern, command, re.IGNORECASE)
    return match.group(1) if match else None