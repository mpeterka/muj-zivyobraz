from datetime import datetime
import re
from urllib.parse import quote
from zoneinfo import ZoneInfo

from functions.wiki import _load_page, _item_text

MONTHS = ('Lednové', 'Únorové', 'Březnové', 'Dubnové', 'Květnové', 'Červnové',
          'Červencové', 'Srpnové', 'Zářijové', 'Říjnové', 'Listopadové', 'Prosincové')


def get_pranostika_values(today=None):
    today = today or datetime.now(ZoneInfo('Europe/Prague')).date()
    url = 'https://cs.wikiquote.org/wiki/' + quote(MONTHS[today.month - 1] + '_pranostiky')
    soup = _load_page(url)
    if soup is None:
        return {}
    daily = []
    for entry in soup.select('.mw-parser-output dl > dd'):
        day = entry.find_previous_sibling('dt')
        if day and re.match(rf'^{today.day}\.\s', day.get_text(' ', strip=True)):
            daily.append(_item_text(entry))
    daily = [text for text in daily if text]
    if daily:
        text = min(daily, key=len)
    else:
        heading = soup.find(lambda tag: tag.name == 'h2'
                            and 'Pranostiky pro celý měsíc' in tag.get_text(' ', strip=True))
        block = heading.find_next('ul') if heading else None
        monthly = [_item_text(item) for item in block.find_all('li', recursive=False)] if block else []
        monthly = [text for text in monthly if text]
        if not monthly:
            return {}
        text = monthly[(today.day - 1) % len(monthly)]
    return {'pranostika': text, 'pranostika_zdroj': url}
