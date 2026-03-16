# Žijící Obraz - Aplikace

Aplikace běží v cyklu a jednou za hodinu odesílá data do `zivyobraz.eu` API.

## Funkce

### Popelnice
Odesílá stav popelnice:
- **pondělí**: `trash3-fill` (naplný den)
- **ostatní dny**: `dot` (prázdný)

## Spuštění

### 1. Pomocí Docker Compose (Doporučeno)

```bash
# 1. Zkopíruj .env soubor
cp .env.example .env

# 2. Vyplň svůj IMPORT_KEY
# Upravit .env a vložit svůj klíč

# 3. Spusť aplikaci
docker-compose up -d

# 4. Sleduj logy
docker-compose logs -f
```

### 2. Lokálně (Python)

```bash
# Instalace závislostí
pip install -r requirements.txt

# Spuštění
IMPORT_KEY=your_key_here python main.py
```

## Struktura projektu

```
├── main.py              # Hlavní aplikace a scheduler
├── functions/
│   ├── __init__.py
│   └── popelnice.py     # Logika pro popelnici
├── requirements.txt     # Python závislosti
├── Dockerfile          # Docker konfigurace
├── docker-compose.yml  # Docker Compose konfigurace
└── .env.example        # Příklad environment proměnných
```

## Přidání nové funkce

Vytvoř nový soubor v `functions/` a přidej job do `main.py`:

```python
# functions/nova_funkce.py
def get_nova_funkce_value():
    return "some_value"

# main.py
from functions.nova_funkce import get_nova_funkce_value

def job_nova_funkce():
    value = get_nova_funkce_value()
    call_function("nova_funkce", value)

scheduler.add_job(
    job_nova_funkce,
    'interval',
    hours=1,
    id='nova_funkce'
)
```

## Environment proměnné

- `IMPORT_KEY` - Klíč pro API zivyobraz.eu (povinné)

## Logy

Aplikace loguje všechny požadavky a chyby. Běží-li v Docker Compose, logy najdeš pomocí:

```bash
docker-compose logs -f
```
