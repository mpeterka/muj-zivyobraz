import random
import os

def _get_fortune(filename, key):
    """
    Pomocná funkce pro načtení náhodné citace z fortune souboru.
    """
    file_path = os.path.join(os.path.dirname(__file__), filename)
    
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()
    except Exception as e:
        return {key: f"Chyba při čtení souboru: {e}"}
        
    # Fortune soubory jsou odděleny znakem % na samostatném řádku
    quotes = content.split("\n%\n")
    
    # Vyčištění
    quotes = [q.strip().lstrip('\ufeff') for q in quotes if q.strip()]
    
    if not quotes:
        return {key: "Žádné citace nenalezeny."}
        
    return {key: random.choice(quotes)}

def pratchett():
    return _get_fortune("pratchett", "pratchett")

def plihal():
    return _get_fortune("plihal", "plihal")

def cimrman():
    return _get_fortune("cimrman", "cimrman")

if __name__ == "__main__":
    print(pratchett())
    print(plihal())
    print(cimrman())
