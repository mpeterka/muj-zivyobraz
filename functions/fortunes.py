import random
import os

def _get_fortune(filename, key):
    """
    Pomocná funkce pro načtení náhodné citace z fortune souboru.
    """
    file_path = os.path.join(os.path.dirname(__file__), "fortune-cs", filename)

    try:
        with open(file_path, "r", encoding="utf-8-sig") as f:
            content = f.read()
    except Exception as e:
        return {key: f"Chyba při čtení souboru: {e}"}

    # Fortune soubory jsou odděleny znakem % na samostatném řádku
    quotes = content.split("\n%\n")

    # Vyčištění
    quotes = [q.strip() for q in quotes if q.strip()]
    
    if not quotes:
        return {key: "Žádné citace nenalezeny."}
        
    return {key: random.choice(quotes)}

def cimrman():
    return _get_fortune("cimrman", "cimrman")

def plihal():
    return _get_fortune("plihal", "plihal")

def pratchet():
    return _get_fortune("pratchet", "pratchet")

def klsk_cz():
    return _get_fortune("klsk-cz", "klsk_cz")

def vodnsnky():
    return _get_fortune("vodnsnky", "vodnsnky")

def zemplcha():
    return _get_fortune("zemplcha", "zemplcha")

if __name__ == "__main__":
    print(cimrman())
    print(plihal())
    print(pratchet())
    print(klsk_cz())
    print(vodnsnky())
    print(zemplcha())
