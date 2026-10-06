import requests
from bs4 import BeautifulSoup
import re
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


def scrape_menicka_ceske_budejovice():
    """
    Stáhne web menicka.cz a extrahuje menu vybraných restaurací.
    Vrací string ve formátu: Restaurace: jídlo | jídlo | jídlo\nRestaurace 2: ...\n
    """
    result = []
    today = datetime.now(ZoneInfo('Europe/Prague')).date()

    for rest_name, rest_url_part in RESTAURANTS.items():
        url = f"https://www.menicka.cz/{rest_url_part}.html"
        dishes = []

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
                        # Omezit na 25 znaků, přidat "..." pokud je delší
                        if len(text) > 25:
                            text = text[:25] + "..."
                        dishes.append(text)

            if dishes:
                # Vzít jen prvních 5 jídel
                top_dishes = dishes[:5]
                dishes_str = " | ".join(top_dishes)
                result.append(f"{rest_name}: {dishes_str}")
            else:
                result.append(f"{rest_name}: menu není dostupné")

        except Exception as e:
            result.append(f"{rest_name}: Chyba - {str(e)}")

    return "\n".join(result)


if __name__ == "__main__":
    menicka = scrape_menicka_ceske_budejovice()
    import sys
    sys.stdout.reconfigure(encoding='utf-8')
    print(menicka)
