import requests
from bs4 import BeautifulSoup
import re
import unicodedata
from datetime import datetime
from zoneinfo import ZoneInfo


# Mapování názvů restaurací na jejich ID v URL
RESTAURANTS = {
    "Naše farma": "3571-nase-farma-~a-vime-co-jime~",
    "Sedláci": "1823-u-tri-sedlaku",
    "Klika": "1851-klika-kitchen-coffee",
    "Krajinská 27": "1836-krajinska-27",
    "Solnice": "6134-restaurace-solnice",
}


def get_menicka_values():
    """Jedno načtení pro původní přehled i samostatné bloky restaurací."""
    result = []
    values = {}
    available = []
    unavailable = []
    failed = []
    today = datetime.now(ZoneInfo('Europe/Prague')).date()

    for rest_name, rest_url_part in RESTAURANTS.items():
        url = f"https://www.menicka.cz/{rest_url_part}.html"
        dishes = []
        key = 'menicka_' + re.sub(r'\W+', '_', unicodedata.normalize(
            'NFKD', rest_name).encode('ascii', 'ignore').decode().lower()).strip('_')
        values[key] = ''

        try:
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            soup = BeautifulSoup(response.content, 'html.parser')

            # Hledáme všechny <li> elementy s třídami 'polevka' nebo 'jidlo'
            menu_items = []
            for menu in soup.find_all('div', class_='menicka'):
                heading = menu.find('div', class_='nadpis')
                if not heading:
                    continue
                date = re.search(r'\b(\d{1,2})\.\s*(\d{1,2})\.\s*(\d{4})\b', heading.get_text())
                if date and tuple(map(int, date.groups())) == (today.day, today.month, today.year):
                    menu_items = menu.find_all('li', class_=['polevka', 'jidlo'])
                    break

            for item in menu_items:
                # Extrahujeme text z <div class='polozka'>
                polozka_div = item.find('div', class_='polozka')
                if polozka_div:
                    # Odebereme span s řadovým číslem, zbytek je jídlo
                    for span in polozka_div.find_all('span', class_='poradi'):
                        span.decompose()

                    text = ' '.join(polozka_div.get_text(' ', strip=True).split())
                    # Odstraníme zbytkové čísla/písmena na konci (zbytky po parsování)
                    # Odstraníme na začátku: 150g, 0, 25l, atd.
                    text = re.sub(r'^/?\s*\d+(?:\s*[,\.]\s*\d+)?\s*(?:kg|g|ml|l|ks)\b\s*', '', text)
                    # Odstraníme na konci: 49, 137, 1711, atd.
                    text = re.sub(r'\s*[0-9]+\s*$', '', text)
                    text = text.strip()

                    # Vynechat oddělovače
                    if text and not text.startswith('---'):
                        dishes.append(text)

            if dishes:
                # Vzít jen prvních 5 jídel
                top_dishes = dishes[:5]
                dishes_str = " | ".join(text[:25] + '...' if len(text) > 25 else text
                                        for text in top_dishes)
                result.append(f"{rest_name}: {dishes_str}")
                lines = []
                for text in top_dishes:
                    if len(text) > 65:
                        shortened = text[:65]
                        if text[65] != ' ' and ' ' in shortened:
                            shortened = shortened.rsplit(' ', 1)[0]
                        text = shortened.rstrip() + '…'
                    lines.append(text)
                values[key] = '\n'.join(lines)
                available.append((rest_name, values[key]))
            else:
                result.append(f"{rest_name}: menu není dostupné")
                unavailable.append(rest_name)

        except Exception as e:
            result.append(f"{rest_name}: Chyba - {str(e)}")
            failed.append(rest_name)

    values['menicka'] = '\n'.join(result)
    values['menicka_datum'] = f'{today.day}. {today.month}.'
    values['menicka_nacteno'] = datetime.now(ZoneInfo('Europe/Prague')).strftime('%H:%M')
    status = []
    if unavailable:
        status.append('Bez nabídky: ' + ', '.join(unavailable))
    if failed:
        status.append('Nelze načíst: ' + ', '.join(failed))
    values['menicka_stav'] = ' · '.join(status)
    for index in range(1, 6):
        name, menu = available[index - 1] if index <= len(available) else ('', '')
        values[f'menicka_{index}_restaurace'] = name
        values[f'menicka_{index}_jidla'] = menu
    return values


def scrape_menicka_ceske_budejovice():
    """Původní formát pro stávající obrazovky."""
    return get_menicka_values()['menicka']


if __name__ == "__main__":
    menicka = scrape_menicka_ceske_budejovice()
    import sys
    sys.stdout.reconfigure(encoding='utf-8')
    print(menicka)
