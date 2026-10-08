import logging
import re

import requests
from bs4 import BeautifulSoup

WIKI_MAIN_PAGE = "https://cs.wikipedia.org/wiki/Hlavn%C3%AD_strana"
WIKI_NEWS_PAGE = "https://cs.wikipedia.org/wiki/Port%C3%A1l:Aktuality"
HEADERS = {"User-Agent": "zivyobraz-bot/1.0 (+https://zivyobraz.eu) Python-requests"}
logger = logging.getLogger(__name__)


def _load_page(url):
    try:
        response = requests.get(url, headers=HEADERS, timeout=15)
        response.raise_for_status()
        return BeautifulSoup(response.content.decode('utf-8'), 'html.parser')
    except requests.RequestException as error:
        logger.warning("Wikipedie se nenačetla: %s", error)
        return None


def _normalize_whitespace(text):
    text = re.sub(r'\s+', ' ', text).strip()
    return re.sub(r'\s+([.,;:!?])', r'\1', text)


def _item_text(item):
    for tag in item.select('img, figure, figcaption, .reference, .flagicon, [style*="visibility:hidden"], [style*="visibility: hidden"]'):
        tag.decompose()
    text = _normalize_whitespace(item.get_text(' ', strip=True))
    return re.sub(r'\s*\(na obrázku\)', '', text).strip()


def get_wiki_dnesek_v_minulosti():
    """Vrátí výročí a datum ze stejné sekce; při chybě zachová staré hodnoty."""
    soup = _load_page(WIKI_MAIN_PAGE)
    if soup is None:
        return {}
    heading = soup.find(
        lambda tag: (tag.name in ('h2', 'h3', 'h4') or 'mainpage-headline' in tag.get('class', []))
        and re.search(r'v\s+minulosti', tag.get_text(' ', strip=True), re.IGNORECASE)
    )
    if heading is None:
        logger.warning("Sekce Wikipedie 'V minulosti' nenalezena.")
        return {}
    date = re.search(r'(\d{1,2}\.\s*[^\W\d_]+)\s+v\s+minulosti',
                     _normalize_whitespace(heading.get_text(' ', strip=True)), re.IGNORECASE)
    # Hledej jen uvnitř sekce, nikdy v navigaci nebo v jiném článku.
    section = heading.find_parent(class_='mainpage-block')
    block = section.select_one('.mainpage-content > ul') if section else heading.find_next_sibling('ul')
    items = [_item_text(li) for li in block.find_all('li', recursive=False)] if block else []
    items = [text for text in items if text]
    if date is None or not items:
        logger.warning("Sekce Wikipedie nemá datum nebo obsah; hodnoty se nemění.")
        return {}
    return {
        'wiki_dnesek_v_minulosti': '\n'.join(items[:5]),
        'wiki_dnesek_v_minulosti_datum': date.group(1),
    }


def get_wiki_aktuality():
    """Pět nejnovějších datovaných zpráv z Portálu:Aktuality."""
    soup = _load_page(WIKI_NEWS_PAGE)
    if soup is None:
        return {}
    items = []
    for entry in soup.select('.mw-parser-output dl > dd'):
        heading = entry.find_previous_sibling('dt')
        if heading is None:
            continue
        date = re.match(r'\d{1,2}\.\s*[^\W\d_]+',
                        _normalize_whitespace(heading.get_text(' ', strip=True)))
        text = _item_text(entry)
        if date and text:
            items.append(f'{date.group(0)} – {text}')
        if len(items) == 5:
            break
    if not items:
        logger.warning("Aktuality Wikipedie nenalezeny; hodnota se nemění.")
        return {}
    return {'wiki_aktuality': '\n'.join(items)}


if __name__ == '__main__':
    print(get_wiki_dnesek_v_minulosti())
    print(get_wiki_aktuality())
