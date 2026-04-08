import random
import os

def zemeplocha_cs():
    """
    Vrací náhodnou citaci ze světa Zeměplochy ze souboru zemeplocha-cs.
    """
    file_path = os.path.join(os.path.dirname(__file__), "zemeplocha-cs")
    
    # Soubor je nyní v UTF-8 po PowerShell konverzi
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()
    except Exception as e:
        return {"zemeplocha_cs": f"Chyba při čtení souboru: {e}"}
        
    # Fortune soubory jsou odděleny znakem % na samostatném řádku
    quotes = content.split("\n%\n")
    
    # Vyčištění
    quotes = [q.strip().lstrip('\ufeff') for q in quotes if q.strip()]
        
    return {"zemeplocha_cs": random.choice(quotes)}

if __name__ == "__main__":
    print(zemeplocha_cs())
