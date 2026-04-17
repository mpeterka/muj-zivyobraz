import re
import requests
from bs4 import BeautifulSoup

WIKI_MAIN_PAGE = "https://cs.wikipedia.org/wiki/Hlavn%C3%AD_strana"

HEADERS = {
    "User-Agent": "zivyobraz-bot/1.0 (+https://zivyobraz.eu) Python-requests"
}


def _find_v_minulosti_block(soup: BeautifulSoup):
    """
    Pokusí se najít sekci „V minulosti“ na hlavní straně Wikipedie.
    Vrací element obsahující položky (typicky <ul> nebo wrapper s <li>), nebo None.
    """
    # 1) Najdi nadpis obsahující "V minulosti"
    heading = soup.find(
        lambda tag: tag.name in ("h2", "h3", "h4", "span")
        and tag.get_text(strip=True)
        and re.search(r"^\s*V\s+minulosti", tag.get_text(strip=True), re.IGNORECASE)
    )

    # 2) Pokud máme nadpis, zkus nejbližší následující <ul> nebo kontejner s <li>
    if heading:
        # projdi sourozence a hledej seznamy
        for sib in heading.find_all_next():
            # Pokud narazíme na jiný hlavní nadpis stejné nebo vyšší úrovně, skonči
            if sib is not heading and sib.name in ("h2", "h3"):
                break
            # Hledej seznam s položkami
            if sib.name == "ul" and sib.find("li"):
                return sib
            # Někdy je to ve wrapperu – pak hledej <li>
            if sib.find and sib.find("li"):
                return sib

    # 3) Fallback: hledej elementy, které v textu obsahují klíčovou frázi a mají <li>
    candidates = soup.find_all(string=re.compile(r"V\s+minulosti", re.IGNORECASE))
    for c in candidates:
        parent = c.parent
        # Projdi předky a hledej kontejner s li
        while parent and parent.name not in ("body", None):
            ul = parent.find("ul") if hasattr(parent, "find") else None
            if ul and ul.find("li"):
                return ul
            parent = parent.parent

    return None


essential_spaces_re = re.compile(r"\s+")


def _normalize_whitespace(text: str) -> str:
    return essential_spaces_re.sub(" ", text).strip()


def get_wiki_dnesek_v_minulosti():
    """
    Načte z Hlavní strany české Wikipedie sekci „V minulosti“
    a vrátí ji jako jediný řetězec.

    Return:
        dict: {"wiki_dnesek_v_minulosti": "..."}
    """
    try:
        resp = requests.get(WIKI_MAIN_PAGE, headers=HEADERS, timeout=15)
        resp.raise_for_status()
    except Exception as e:
        return {"wiki_dnesek_v_minulosti": f"Chyba při načítání Wikipedie: {e}"}

    soup = BeautifulSoup(resp.text, "html.parser")

    # Najdi nadpis sekce (např. "17. duben v minulosti")
    heading_text = None
    heading = soup.find(
        lambda tag: tag.name in ("h2", "h3", "h4", "span")
        and tag.get_text(strip=True)
        and re.search(r"^\s*V\s+minulosti", tag.get_text(strip=True), re.IGNORECASE)
    )
    if heading:
        heading_text = _normalize_whitespace(heading.get_text(strip=True))

    block = _find_v_minulosti_block(soup)
    if not block:
        return {"wiki_dnesek_v_minulosti": "Sekce 'V minulosti' nenalezena."}

    # Získej jednotlivé položky – preferuj <li>, případně odstavce
    items = []
    for li in block.find_all("li", recursive=True):
        # Odstraníme nežádoucí elementy jako obrázky a jejich titulky, které mohou generovat text jako "0"
        for tag in li.find_all(["img", "figure", "figcaption"]):
            tag.decompose()

        txt = _normalize_whitespace(li.get_text(" ", strip=True))
        # Odstranění úvodních čísel (často artefakt z meta-dat nebo obrázků na wiki)
        txt = re.sub(r"^[0\s]+", "", txt)
        # Odstranění výskytu "(na obrázku)"
        txt = re.sub(r"\s*\(na obrázku\)", "", txt)
        if txt:
            items.append(txt)
    if not items:
        # fallback: odstavce
        for p in block.find_all("p", recursive=True):
            txt = _normalize_whitespace(p.get_text(" ", strip=True))
            txt = re.sub(r"^[0\s]+", "", txt)
            txt = re.sub(r"\s*\(na obrázku\)", "", txt)
            if txt:
                items.append(txt)

    if not items:
        return {"wiki_dnesek_v_minulosti": "Obsah sekce 'V minulosti' je prázdný."}

    # Omez počet položek, aby se to vešlo rozumně na zivyobraz (např. 3–5 položek)
    items = items[:5]

    text = "\n".join(items)
    if heading_text:
        text = f"{heading_text}\n{text}"
    return {"wiki_dnesek_v_minulosti": text}


if __name__ == "__main__":
    print(get_wiki_dnesek_v_minulosti())
