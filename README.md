# zivyobraz.eu udělátka

## Obrázek fáze Měsíce

Samostatná služba poskytuje `GET /moon.png` (také `HEAD`). Příklady:

```text
/moon.png
/moon.png?width=128&height=128&style=voyage
/moon.png?width=256&height=256&style=real
/moon.png?width=128&height=128&style=voyage&background-color=%23000
```

Výchozí rozměry jsou 128 × 128 px a styl `voyage` (Cesta na Měsíc, obličej
s raketou a odstraněným pozadím). Styl `real` používá fotografii Luc Viatour.
Každý rozměr musí být celé číslo 32–1024 bez počátečních nul. Pořadí
parametrů je libovolné; neznámé a duplicitní parametry jsou 400.
Výstup je černobílý PNG s Floyd–Steinberg ditheringem v konečné velikosti.
Pozadí a zastíněná část jsou průhledné. Nepovinný `background-color`
je vyplní barvou `#RGB` nebo `#RRGGBB`; v URL musí být `#` jako `%23`.
Jiné kódování parametrů není povoleno. Barva pozadí je součástí cache klíče.
Velikost URL musí odpovídat velikosti widgetu, aby portál nemusel PNG zmenšovat.

Fáze odpovídá dnešnímu datu v `Europe/Prague`, s denní aktualizací z MET
Norway. Nginx cache expiruje nejpozději o následující pražské půlnoci.
Při výpadku dnešního zdroje je odpověď 503; včerejší obrázek se nenabízí.

Spuštění pouze obrázkové služby (bez `IMPORT_KEY`):

```shell
docker compose up -d --build moon moon-nginx
curl -I 'http://127.0.0.1:8088/moon.png?style=voyage'
```

Nginx je dostupný pouze na `127.0.0.1:8088` (port lze změnit přes `MOON_PORT`).
Moon nemá publikovaný port. Pokud HTTPS nginx běží na stejném hostiteli,
do existujícího TLS serveru přidej následující location; původní query
zůstane zachována. Tato vnější proxy sama obrázky necachuje:

```nginx
location = /moon.png {
    proxy_pass http://127.0.0.1:8088;
    proxy_set_header Host moon;
    proxy_pass_header Date;
    proxy_read_timeout 40s;
}
```

Pokud je vnější proxy v Dockeru, připoj ji do stejné sítě a použij interní
adresu `moon-nginx:8080`; localhost uvnitř kontejneru znamená tento kontejner.
Bez konkrétní domény a TLS konfigurace není služba dostupná z internetu.

Výchozí IP limit je 30 požadavků/min s burst 10, nejvýše 8 spojení/IP.
Za vnější proxy všechny požadavky sdílejí její IP, pokud nezapneš real_ip
**pouze pro přesně určený důvěryhodný proxy rozsah**. Klientské
`X-Forwarded-For` není standardně důvěryhodné. Živý obraz také může mít
sdílené IP; limit lze upravit v `nginx/moon.conf`.

Globální limit je 6 renderů/min, burst 2. Renderuje se sériově, nejvýše
4 požadavky čekají; přebytek je 503, vyčerpaný limit 429 s Retry-After.
PNG se v Pythonu necachují. Nginx cache má target 64 MiB, pevný tmpfs
strop 80 MiB a keys_zone 2 MiB; po restartu nginxu se doplní znovu.
Memory limit: moon 256 MiB, nginx 128 MiB. Hlavička `X-Moon-Cache`
ukazuje MISS/HIT. Nginx ukládá pouze úspěšné odpovědi; chyby jsou no-store.

`docker compose logs -f moon moon-nginx` ukáže skutečné rendery i přístupy.
`moon_render` loguje datum, styl, rozměry, pozadí, fázi, dobu v ms a velikost PNG.
Nginx loguje `cache=HIT/MISS`, status, počet bajtů a dobu požadavku/upstreamu.
Souhrn renderů za poslední den: `docker compose logs --since 24h moon | grep -c moon_render`.

Podklady a licence: [assets/moon/README.md](assets/moon/README.md).
Fotografie `real`: **Luc Viatour / https://lucnix.be**, [zdroj](https://commons.wikimedia.org/wiki/File:Full_Moon_Luc_Viatour.jpg),
**CC BY-SA 3.0**. Odvozená PNG jsou také CC BY-SA 3.0; autor, zdroj,
licence a popis úprav jsou v metadatech PNG, HTTP credit/Link hlavičkách.
Při dalším zveřejnění fotografie uváděj příslušný kredit a licenci.

Integrační test vyžaduje čerstvou cache a plný render budget. Použij
oddělený Compose project a volný `MOON_PORT`, spusť pouze `moon` a
`moon-nginx`; poté nastav `MOON_TEST_URL=http://127.0.0.1:<port>` a spusť
`python -m unittest test_nginx_integration -v`. Test používá skutečný
nginx i MET, ověřuje cache, style, validaci, HEAD/ETag a oba rate limity.

Aplikace běží v cyklu a jednou za hodinu odesílá data do `zivyobraz.eu` API.

Meníčka se aktualizují každý den v 7:00–14:00 každou hodinu a v 18:00
v časové zóně `Europe/Prague`, také při spuštění aplikace. Načítá se pouze
nabídka pro dnešní datum; české znaky a mezery se upraví před zkrácením názvů.

Původní `menicka` zachovává stejný formát i limit 25 znaků. Samostatné hodnoty
`menicka_nase_farma`, `menicka_sedlaci`, `menicka_klika`, `menicka_krajinska_27`
a `menicka_solnice` obsahují nejvýše pět jídel, každé na vlastním řádku;
názvy se zkracují do 65 znaků na hranici slova a doplňují znakem `…`.
Obrazovka 6924 používá pět dvojic `menicka_1_restaurace` / `menicka_1_jidla`
až `menicka_5_restaurace` / `menicka_5_jidla`. Obsazené bloky obsahují pouze
restaurace s dnešní nabídkou; neobsazené hodnoty se vyprázdní.
`menicka_stav` rozlišuje chybějící nabídku a chybu načtení.
`menicka_datum` označuje hledaný den nabídky ve formátu `D. M.` bez roku;
obědový nadpis používá `Kam na oběd · {{menicka_datum}}`, aby zůstalo vidět
stáří nabídky i při výpadku aktualizace. `menicka_nacteno` označuje čas
dokončení načtení v Praze. Všechny hodnoty se odesílají jedním požadavkem.

Klementinum používá oficiální CSV z
[otevřených dat ČHMÚ](https://opendata.chmi.cz/meteorology/climate/historical_csv/data/daily/temperature/)
pro stanici `0-203-0-11514`. Minimum a maximum jsou historické denní extrémy
z dostupných ukončených let od roku 1775. Průměr je aritmetický průměr
denních průměrů pro stejné kalendářní datum z tohoto období, nikoliv klimatický
normál 1991–2020. Používají se pouze hodnoty s dobrou kvalitou (`QUALITY=0`).
Soubory se čtou postupně a výsledky pro aktuální měsíc se ukládají do paměti;
při změně měsíce nebo restartu se načtou znovu. Při chybě se prázdná data neodesílají.

Proměnná `vtipy` obsahuje jeden náhodný český vtip z Alíkova veřejného
vkládacího skriptu. Aktualizuje se při startu a každých 6 hodin.
Vybírají se celé vtipy do 300 znaků, bez doplněného dovětku se zdrojem.
Pokud zdroj neodpovídá nebo nenabídne dostatečně krátký vtip, předchozí
hodnota na Živém obrazu zůstane zachována.

## Monitoring

Prometheus metriky jsou na `http://muj-zivyobraz:8000/metrics` v Docker síti.
Port se nepublikuje na hostitele. Endpoint neobsahuje importní klíč ani hodnoty
odesílaného obsahu. Obsahuje procesní metriky, počty úspěšných/chybných uploadů,
čas posledního úspěšného uploadu, počty dokončení/výjimek úloh, jejich dobu běhu
a poslední dokončení. Dokončení úlohy samo o sobě nezaručuje nová data: zdrojové
funkce mohou při nedostupnosti dat vrátit prázdný výsledek.

## Testy

Wikipedie se načítá při startu a v 5:00, 12:00 a 18:00 (`Europe/Prague`).
`wiki_dnesek_v_minulosti` obsahuje až pět výročí a
`wiki_dnesek_v_minulosti_datum` datum z nadpisu stejné stažené sekce
(například `8. říjen`). Nadpis obrazovky používá
`{{wiki_dnesek_v_minulosti_datum}} v minulosti`.
`wiki_aktuality` obsahuje až tři nejnovější datované zprávy z
[Portálu:Aktuality](https://cs.wikipedia.org/wiki/Port%C3%A1l:Aktuality).
Při chybě nebo chybějícím obsahu se předchozí hodnoty zachovají.

```shell
python -m unittest discover -v
```

## Funkce

### Dětské služby
`detske_prace` obsahuje tři řádky v pořadí Majda, Matěj, Markét.
`detske_prace_nadpis` je „Služby tento týden“; jednotlivé úkoly jsou také
v `detske_prace_majda`, `detske_prace_matej` a `detske_prace_market`.
Rotace navazuje na kalendář: od 5. 10. 2026 má Majda odpadky a podlahy,
Matěj prádlo a Markét myčku. Další týden má Majda myčku, Matěj odpadky
a podlahy a Markét prádlo. Cyklus se opakuje po třech týdnech.
Služby platí i o víkendu a mění se v pondělí v 00:00 (`Europe/Prague`).
Hodnoty se obnoví při startu, na SIGUSR1 a denně v 00:00, 6:00, 12:00 a 18:00.
Kalendář ani síťový zdroj se pro výpočet nepoužívá.

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

### Slunce zitra

Hodnoty slunce_zitra_vychod, slunce_zitra_zapad a slunce_zitra_datum pro Ceske Budejovice. Zdroj: MET Norway Sunrise 3.0 (https://api.met.no/weatherapi/sunrise/3.0/documentation), licence https://api.met.no/license_data.html. Aktualizace pri startu a v 00:00, 06:00, 12:00 a 18:00 v Europe/Prague.


### Pranostika

Hodnota pranostika vybira kratkou pranostiku pro aktualni den z ceskych Wikicitatu. Pokud pro den chybi, pouzije pranostiku pro aktualni mesic. Zdroj: https://cs.wikiquote.org/wiki/Pranostiky (CC BY-SA), odkaz na konkretni mesic v pranostika_zdroj. Aktualizace pri startu a v 00:00, 06:00, 12:00, 18:00 Europe/Prague.


## Tracing

Nastavení OTEL_EXPORTER_OTLP_ENDPOINT zapne vlastní spany plánovaných úloh a requests instrumentaci. Cloud token aplikace nepotřebuje; odesílá do interního Alloy. URL atributy redigované, nevytváří další OTel metrics/log exportery. Nasazení, firewall a rollback jsou zdokumentovány v projektu Karotka, monitoring/tracing-deployment.md.

## Verze a nasazení

`APP_DEPLOYMENT_VERSION` určuje bezpečný label metriky `zivyobraz_build_info`;
chybějící/neplatná hodnota se označí unknown. Metrika
`zivyobraz_application_start_timestamp_seconds` ukazuje start procesu.
Dashboard Živý obraz propojuje fialovou značku nasazení s dobou běhu úloh,
chybami uploadů a RAM. Značku zapíše skript `monitoring/record-deployment.ps1`
z projektu Karotka; postup je v `monitoring/deployment-markers.md`.
