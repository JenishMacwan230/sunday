"""
core/intent_parser.py
======================
This is SUNDAY's "brain". It sends your transcribed command to a LOCAL LLM
(running through Ollama) and asks it to reply with ONE JSON object
describing exactly what to do.

WHY HAVE THE LLM OUTPUT JSON INSTEAD OF "DOING" THINGS ITSELF?
Because we never want a language model directly executing code on your
computer - that's unpredictable and hard to debug. Instead, the LLM's only
job is to decide WHAT should happen; actions/action_executor.py is the
only place that actually DOES it.
"""

import json
import ollama

from config import OLLAMA_MODEL
from core.memory import context_string

SYSTEM_PROMPT_TEMPLATE = """You convert a spoken command into ONE JSON object. No prose, no markdown, no explanation - JSON only.

Possible actions:
{{"action":"open_app","target":"<application name>"}}
{{"action":"open_url","target":"<full url>"}}
{{"action":"web_search","engine":"google|youtube","query":"<search text>"}}
{{"action":"explorer_navigate","path":"<folder or drive name>"}}
{{"action":"open_file","path":"<file name>"}}
{{"action":"type_text","text":"<text to type>"}}
{{"action":"unknown"}}

Known shortcuts (use these directly when the user references them):
{memory_context}
"""


def parse_command(spoken_text: str) -> dict:
    """
    Sends `spoken_text` to the local LLM and returns a Python dict
    describing the action to take. Falls back to {"action": "unknown"} if
    the model's reply can't be understood as valid JSON, so a bad response
    can never crash the rest of the assistant.
    """
    system_prompt = SYSTEM_PROMPT_TEMPLATE.format(memory_context=context_string())

    response = ollama.chat(
        model=OLLAMA_MODEL,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": spoken_text},
        ],
        format="json",  # tells Ollama to constrain its output to valid JSON
    )

    raw_reply = response["message"]["content"]

    try:
        return json.loads(raw_reply)
    except (json.JSONDecodeError, KeyError):
        print(f"[SUNDAY] Could not understand LLM reply: {raw_reply}")
        return {"action": "unknown"}
