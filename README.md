# zivyobraz.eu udělátka

Aplikace běží v cyklu a jednou za hodinu odesílá data do `zivyobraz.eu` API.

Meníčka se aktualizují každý den v 7:00–14:00 každou hodinu a v 18:00
v časové zóně `Europe/Prague`, také při spuštění aplikace. Načítá se pouze
nabídka pro dnešní datum; české znaky a mezery se upraví před zkrácením názvů.

Klementinum používá oficiální CSV z
[otevřených dat ČHMÚ](https://opendata.chmi.cz/meteorology/climate/historical_csv/data/daily/temperature/)
pro stanici `0-203-0-11514`. Minimum a maximum jsou historické denní extrémy
z dostupných ukončených let od roku 1775. Průměr je aritmetický průměr
denních průměrů pro stejné kalendářní datum z tohoto období, nikoliv klimatický
normál 1991–2020. Používají se pouze hodnoty s dobrou kvalitou (`QUALITY=0`).
Soubory se čtou postupně a výsledky pro aktuální měsíc se ukládají do paměti;
při změně měsíce nebo restartu se načtou znovu. Při chybě se prázdná data neodesílají.

## Testy

```shell
python -m unittest discover -v
```

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

## Ruční spuštění funkcí (Unix signály)

Všechny funkce lze vyvolat zvenku pomocí Unix signálu:

```bash
# Spusť všechny funkce
kill -SIGUSR1 <pid>

# Graceful shutdown
kill -SIGTERM <pid>
```

Nebo z hostitele pokud běží lokálně:
```bash
kill -SIGUSR1 $(pgrep -f "python main.py")
```

**Signály:**
- `SIGUSR1` - Spustit **všechny** naplánované funkce
- `SIGTERM` / `SIGINT` - Graceful shutdown

## Environment proměnné

- `IMPORT_KEY` - Klíč pro API zivyobraz.eu (povinné)

## Logy

Aplikace loguje všechny požadavky a chyby. Běží-li v Docker Compose, logy najdeš pomocí:

```bash
docker-compose logs -f
```

Při spuštění zobrazí své PID:
```
2026-03-16 10:15:30 - INFO - Starting application...
2026-03-16 10:15:30 - INFO - PID: 42
2026-03-16 10:15:30 - INFO - Signal handlers registered:
2026-03-16 10:15:30 - INFO -   SIGUSR1 - Run all jobs
```
