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

from server.paths import DB_PATH

con = sqlite3.connect(DB_PATH)
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


def SendWhatsApp(query):
    """Parse contact name + message from voice command, look up phone number, and send via WhatsApp Web."""
    import difflib

    # ── Parse the query to extract contact name and message ─────
    # Supported patterns:
    #   "send message to [name] saying [message]"
    #   "send whatsapp to [name] saying [message]"
    #   "whatsapp [name] [message]"
    patterns = [
        r'send\s+(?:a\s+)?(?:whatsapp\s+)?message\s+(?:to|tu|two|2)\s+(.+?)\s+saying\s+(.+)',
        r'send\s+(?:a\s+)?whatsapp\s+(?:to|tu|two|2)\s+(.+?)\s+saying\s+(.+)',
        r'whatsapp\s+(\S+)\s+(.+)',
    ]

    contact_name = None
    message = None

    for pattern in patterns:
        match = re.search(pattern, query, re.IGNORECASE)
        if match:
            contact_name = match.group(1).strip()
            message = match.group(2).strip()
            break

    if not contact_name or not message:
        speak_text("Sorry, I couldn't understand the contact name or message. Please try again.")
        print(f"[WhatsApp] Failed to parse query: {query}")
        return

    # ── Look up the contact phone number (fuzzy match) ─────────
    try:
        db_con = sqlite3.connect(DB_PATH)
        db_cursor = db_con.cursor()
        db_cursor.execute('SELECT name, phone FROM contacts')
        contacts = db_cursor.fetchall()
        db_con.close()
    except Exception as e:
        speak_text("Error accessing contacts database.")
        print(f"[WhatsApp] DB error: {e}")
        return

    if not contacts:
        speak_text("You have no saved contacts. Please add a contact first.")
        return

    # Find the best fuzzy match for the contact name
    best_ratio = 0.0
    best_contact = None
    for db_name, db_phone in contacts:
        ratio = difflib.SequenceMatcher(None, contact_name.lower(), db_name.lower()).ratio()
        if ratio > best_ratio:
            best_ratio = ratio
            best_contact = (db_name, db_phone)

    if best_ratio < 0.6 or best_contact is None:
        speak_text(f"Contact {contact_name} not found. Please add them in the contacts panel.")
        print(f"[WhatsApp] No match for '{contact_name}' (best ratio: {best_ratio:.2f})")
        return

    matched_name, phone = best_contact
    print(f"[WhatsApp] Matched '{contact_name}' -> '{matched_name}' ({phone}) ratio={best_ratio:.2f}")

    # ── Send via WhatsApp Desktop app ───────────────────────────
    try:
        import urllib.parse
        import time
        import pyautogui

        speak_text(f"Sending message to {matched_name}")

        # Build whatsapp:// deep link — opens WhatsApp.exe directly
        phone_clean = phone.replace('+', '').replace(' ', '').replace('-', '')
        encoded_msg = urllib.parse.quote(message)
        whatsapp_url = f"whatsapp://send?phone={phone_clean}&text={encoded_msg}"

        # Launch WhatsApp Desktop with the pre-filled message
        os.startfile(whatsapp_url)

        # Wait for WhatsApp to open and load the chat
        time.sleep(8)

        # Press Enter to send the message
        pyautogui.press('enter')

        print(f"[WhatsApp] Message sent to {matched_name} ({phone}): {message}")
    except Exception as e:
        speak_text(f"Failed to send WhatsApp message. Error: {str(e)}")
        print(f"[WhatsApp] Error sending message: {e}")