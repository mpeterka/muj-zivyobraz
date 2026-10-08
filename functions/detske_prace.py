from datetime import date, datetime, timedelta
from zoneinfo import ZoneInfo


def get_detske_prace_values(today=None):
    """Třítýdenní rotace navazující na kalendář, změna v pondělí v 6:00."""
    if today is None:
        today = (datetime.now(ZoneInfo('Europe/Prague')) - timedelta(hours=6)).date()
    monday = today - timedelta(days=today.weekday())
    # Týden 5. 10. 2026: Majda odpadky, Matěj prádlo, Markét myčka.
    week = (monday - date(2026, 10, 5)).days // 7
    jobs = ('odpadky a podlahy', 'myčka', 'prádlo')
    assignments = (
        ('Majda', 'majda', jobs[week % 3]),
        ('Matěj', 'matej', jobs[(week + 2) % 3]),
        ('Markét', 'market', jobs[(week + 1) % 3]),
    )
    values = {f'detske_prace_{key}': job for name, key, job in assignments}
    values['detske_prace'] = '\n'.join(f'{name} · {job}' for name, key, job in assignments)
    values['detske_prace_nadpis'] = 'Služby tento týden'
    return values
