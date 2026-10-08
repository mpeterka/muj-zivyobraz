from datetime import datetime
import re
from urllib.parse import quote
from zoneinfo import ZoneInfo

from functions.wiki import _load_page, _item_text

MONTHS = ('Lednové', 'Únorové', 'Březnové', 'Dubnové', 'Květnové', 'Červnové',
          'Červencové', 'Srpnové', 'Zářijové', 'Říjnové', 'Listopadové', 'Prosincové')
DAY_PAGE_MONTHS = ('leden', 'únor', 'březen', 'duben', 'květen', 'červen',
                  'červenec', 'srpen', 'září', 'říjen', 'listopad', 'prosinec')


def _shortest(texts):
    texts = [text for text in texts if text]
    return min(texts, key=len) if texts else None


def _from_wikipedia(today):
    url = 'https://cs.wikipedia.org/wiki/' + quote(f'{today.day}._{DAY_PAGE_MONTHS[today.month - 1]}')
    soup = _load_page(url)
    heading = soup.find('h2', id='Pranostiky') if soup else None
    wrapper = heading.find_parent(class_='mw-heading') if heading else None
    if wrapper is None:
        return None
    items = [li for sibling in wrapper.find_next_siblings() for li in sibling.find_all('li')]
    text = _shortest(_item_text(li) for li in items)
    return (text, url, 'Wikipedie') if text else None


def _from_wikiquote(today):
    url = 'https://cs.wikiquote.org/wiki/' + quote(MONTHS[today.month - 1] + '_pranostiky')
    soup = _load_page(url)
    if soup is None:
        return None
    daily = []
    for entry in soup.select('.mw-parser-output dl > dd'):
        day = entry.find_previous_sibling('dt')
        if day and re.match(rf'^{today.day}\.\s', day.get_text(' ', strip=True)):
            daily.append(_item_text(entry))
    text = _shortest(daily)
    if not text:
        heading = soup.find(lambda tag: tag.name == 'h2'
                            and 'Pranostiky pro celý měsíc' in tag.get_text(' ', strip=True))
        block = heading.find_next('ul') if heading else None
        monthly = [_item_text(item) for item in block.find_all('li', recursive=False)] if block else []
        monthly = [t for t in monthly if t]
        text = monthly[(today.day - 1) % len(monthly)] if monthly else None
    return (text, url, 'Wikicitáty') if text else None


def get_pranostika_values(today=None):
    today = today or datetime.now(ZoneInfo('Europe/Prague')).date()
    found = _from_wikipedia(today) or _from_wikiquote(today)
    if not found:
        return {}
    text, url, name = found
    return {'pranostika': text, 'pranostika_zdroj': url, 'pranostika_zdroj_nazev': name}
