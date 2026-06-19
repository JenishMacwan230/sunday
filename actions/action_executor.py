"""
actions/action_executor.py
============================
The "router" of SUNDAY. It takes the JSON dict produced by the LLM
(core/intent_parser.py) and calls the ONE correct function to actually
perform it. This is the only place in the whole project where the LLM's
decision turns into a real action on your computer - keeping the model's
output and the actual execution cleanly separated.
"""

from core.text_to_speech import speak
from actions import app_launcher, browser_control, file_explorer, typing_tool


def execute(action: dict):
    """
    Looks at action["action"] and calls the matching function.
    Speaks a short confirmation either way, so you always know SUNDAY
    understood (or didn't understand) what you said.
    """
    action_type = action.get("action")

    if action_type == "open_app":
        app_launcher.open_app(action["target"])
        speak(f"Opening {action['target']}")

    elif action_type == "open_url":
        browser_control.open_url(action["target"])
        speak("Opening that in Chrome")

    elif action_type == "web_search":
        browser_control.web_search(action["engine"], action["query"])
        speak(f"Searching {action['engine']} for {action['query']}")

    elif action_type == "explorer_navigate":
        file_explorer.navigate(action["path"])
        speak(f"Navigating to {action['path']}")

    elif action_type == "open_file":
        file_explorer.open_file(action["path"])
        speak(f"Opening {action['path']}")

    elif action_type == "type_text":
        typing_tool.type_text(action["text"])
        # No spoken confirmation here on purpose - it would interrupt dictation.

    else:
        speak("Sorry, I didn't understand that command")
