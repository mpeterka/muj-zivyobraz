import json
import logging
import requests
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)
URL = 'https://www.alik.cz/v/js?5;nahodne;korektni'
MAX_LENGTH = 300


def get_vtipy_values():
    """Read the embed feed without executing JavaScript; keep punchlines intact."""
    try:
        response = requests.get(URL, timeout=15)
        response.raise_for_status()
        script = response.content.decode('utf-8-sig')
        marker = '}(document.currentScript,'
        if marker not in script:
            raise ValueError('Joke feed format changed')
        jokes, _ = json.JSONDecoder().raw_decode(script.rsplit(marker, 1)[1].lstrip())
        if not isinstance(jokes, list) or not all(isinstance(joke, str) for joke in jokes):
            raise ValueError('Joke feed is not a list of HTML strings')
        for joke in jokes:
            soup = BeautifulSoup(joke, 'html.parser')
            for tag in soup.find_all(['script', 'style']):
                tag.decompose()
            text = ' '.join(soup.get_text(' ', strip=True).split())
            if text and len(text) <= MAX_LENGTH:
                return {'vtipy': text}
        logger.warning('No complete joke within %s characters', MAX_LENGTH)
    except (requests.exceptions.RequestException, ValueError) as error:
        logger.warning('Could not load joke: %s', error)
    return {}
