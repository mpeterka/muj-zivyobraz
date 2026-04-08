import requests
from bs4 import BeautifulSoup
import re


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

    for rest_name, rest_url_part in RESTAURANTS.items():
        url = f"https://www.menicka.cz/{rest_url_part}.html"
        dishes = []

        try:
            response = requests.get(url, timeout=10)
            response.encoding = 'cp1250'  # Web používá windows-1250
            soup = BeautifulSoup(response.text, 'html.parser')

            # Hledáme všechny <li> elementy s třídami 'polevka' nebo 'jidlo'
            menu_items = soup.find_all('li', class_=['polevka', 'jidlo'])

            for item in menu_items:
                # Extrahujeme text z <div class='polozka'>
                polozka_div = item.find('div', class_='polozka')
                if polozka_div:
                    # Odebereme span s řadovým číslem, zbytek je jídlo
                    for span in polozka_div.find_all('span', class_='poradi'):
                        span.decompose()

                    text = polozka_div.get_text(strip=True)
                    # Odstraníme zbytkové čísla/písmena na konci (zbytky po parsování)
                    # Odstraníme na začátku: 150g, 0, 25l, atd.
                    text = re.sub(r'^[0-9\s,\.]*[gklsšč]*\s*', '', text)
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
