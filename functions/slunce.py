from datetime import datetime, time, timedelta
import logging
from zoneinfo import ZoneInfo

import requests

logger = logging.getLogger(__name__)
PRAGUE = ZoneInfo('Europe/Prague')


def get_slunce_zitra_values(today=None):
    tomorrow = (today or datetime.now(PRAGUE).date()) + timedelta(days=1)
    offset = datetime.combine(tomorrow, time(12), PRAGUE).strftime('%z')
    try:
        response = requests.get(
            'https://api.met.no/weatherapi/sunrise/3.0/sun',
            params={'lat': 48.9747, 'lon': 14.4743,
                    'date': tomorrow.isoformat(), 'offset': offset[:3] + ':' + offset[3:]},
            headers={'User-Agent': 'muj-zivyobraz/1.0 github.com/mpeterka/muj-zivyobraz'},
            timeout=10,
        )
        response.raise_for_status()
        properties = response.json()['properties']
        values = {}
        for event, key in [('sunrise', 'vychod'), ('sunset', 'zapad')]:
            instant = datetime.fromisoformat(properties[event]['time']).astimezone(PRAGUE)
            if instant.date() != tomorrow:
                raise ValueError('Unexpected date in sun response')
            values[f'slunce_zitra_{key}'] = f'{instant.hour}:{instant.minute:02d}'
        values['slunce_zitra_datum'] = f'{tomorrow.day}. {tomorrow.month}.'
        return values
    except (requests.RequestException, KeyError, TypeError, ValueError) as exc:
        logger.error('slunce_zitra: %s', exc)
        return None
