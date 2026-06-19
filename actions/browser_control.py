"""
actions/browser_control.py
============================
Handles everything related to opening Chrome - either a direct URL
(e.g. "open youtube") or a search query (e.g. "search cute cats on
youtube").

We launch Chrome directly with the FINAL url rather than simulating typing
into the address bar - it's far more reliable and doesn't depend on which
window happens to have focus. This is the one part of SUNDAY that needs an
internet connection, since loading any real web page requires one.
"""

import subprocess
import urllib.parse

from config import CHROME_PATH

SEARCH_URL_TEMPLATES = {
    "google": "https://www.google.com/search?q={query}",
    "youtube": "https://www.youtube.com/results?search_query={query}",
}


def open_url(url: str):
    """Opens any URL directly in Chrome, in a new window/tab."""
    if not url.startswith(("http://", "https://")):
        url = "https://" + url  # be forgiving if the LLM forgot the scheme
    subprocess.Popen([CHROME_PATH, url])


def web_search(engine: str, query: str):
    """
    Builds a search-results URL for the given engine ("google" or
    "youtube") and opens it directly, so SUNDAY lands you straight on the
    results page instead of just opening the homepage.
    """
    template = SEARCH_URL_TEMPLATES.get(engine.lower(), SEARCH_URL_TEMPLATES["google"])
    encoded_query = urllib.parse.quote_plus(query)
    url = template.format(query=encoded_query)
    subprocess.Popen([CHROME_PATH, url])
