# Veřejný obrázek fáze Měsíce

## Účel a schválené požadavky

Živý obraz bude načítat PNG z veřejné HTTPS URL. Obrázek představuje fázi
Měsíce pro aktuální kalendářní den v Europe/Prague. Vstupem jsou rozměry;
výchozí velikost je 128 × 128 px, běžná 256 × 256 px, maximum 1024 px
na každé straně. Výstup je černobílý s ditheringem.

Podkladem je konkrétní záběr z filmu Cesta na Měsíc (1902), který vybral
uživatel. Odstraní se okolní pozadí, zachová obličej, raketa a filmová
textura. Podklad se distribuuje s aplikací a za provozu se nestahuje.

## Stav projektu a rozsah

Projekt v W:/github/muj-zivyobraz je Python 3.11 aplikace se schedulerem,
requests a Docker Compose. Nemá HTTP server. functions/faze_mesice.py už
získává číselnou fázi z MET Norway, ale používá UTC datum a offset hostitele.

Doplní se samostatný proces/služba moon a nginx. Scheduler a HTTP služba
sdílejí výpočet/načítání fáze, nikoliv běh scheduleru. HTTP služba neimportuje
main.py a nepotřebuje IMPORT_KEY. Neprovádí se jiné úpravy scheduleru.

## API a validace před cache

GET /moon.png?width=128&height=128 vrací image/png.
GET /moon.png vrací 128 × 128 px. Chybějící rozměr má hodnotu 128.
HEAD má stejné hlavičky jako GET a žádné tělo.

Povolena jsou pouze width a height, každé nejvýše jednou, v libovolném
pořadí. Hodnoty jsou desetinné ASCII číslice v kanonickém zápisu bez
počátečních nul, v rozsahu 32–1024. Prázdné hodnoty, další parametry,
duplicitní klíče, procentové kódování, znaménka a jiné oddělovače jsou 400.
Nginx i aplikace ověřují stejný kontrakt. Nginx ověřuje celý řetězec query,
nikoliv pouze $arg_width, který by schoval duplicitní parametry.

Ostatní cesty jsou 404; jiné metody 405. Vstup nesmí obsahovat datum, URL
podkladu nebo jiné hodnoty ovlivňující render. Hlavičky od klienta nemění
obsah obrázku. Query a hlavičky mají omezenou délku na proxy.

## Datum a fáze

Použije se dnešní datum a offset z Europe/Prague včetně změn letního času.
MET Norway poskytuje fázi pro zadaný den; nejde o animaci v reálném čase.
Sdílený modul umožní předat konkrétní datum pro testy.

HTTP služba drží jedinou úspěšnou hodnotu (datum, úhel) v paměti. Souběžné
požadavky sdílejí načítání. Výpadek se krátce utlumí, aby každý požadavek
nespouštěl nový síťový pokus. Časový limit MET je 10 sekund. Chybějící,
nečíselná nebo nefinite hodnota není platná fáze. Při chybě dnešní fáze je
odpověď 503, no-store a Retry-After; včerejší fáze se nevrací jako dnešní.

## Vykreslení

Transparentní podklad bude lokální RGBA PNG. Filmový obličej se používá
jako umělecká textura čelního disku, nikoliv jako mapa skutečných kráterů.
Maska fáze se počítá jako projekce osvětlené koule; přibývání svítí zprava,
ubývání zleva. Osvětlená plocha přechází plynule a není výběrem osmi ikon.

Kruhový disk se zarovná na obličej; drobný přesah rakety se zachová uvnitř
celkového rámečku. Neosvětlená část disku bude černá, okolí bílé. Raketa
nesmí vytvořit samostatný světlý objekt v novu; použije se stejná stranová
maska s omezením souřadnic do disku. Tato ilustrace nemodeluje libraci,
skutečný reliéf ani natočení podle pozorovatele.

Render se zmenší na cílovou velikost s malým okrajem; kontrast se upraví
mírně. Floyd–Steinberg dithering se provede až na konečném rozlišení.
Výstup PNG obsahuje pouze černou a bílou, má přesně požadované rozměry.
Žádný text ani dekorace. Neprovádí se render ve větším rozlišení než 1024.

## Cache a ochrana proti poisoning

Hotová PNG cachuje pouze nginx. Klíč je pevný prefix/verze rendereru
a normalizovaná dvojice rozměrů. Ekvivalentní pořadí parametrů a výchozí
hodnoty mají stejný klíč. Host, X-Forwarded-Host, raw query a klientská
cache hlavička se do klíče nepoužijí. Proxy nastaví pevný upstream Host,
nepředá cookies/Authorization ani klientské proxy hlavičky.

Úspěšná odpověď nastaví Cache-Control public s dobou nejvýše do následující
pražské půlnoci, ETag a X-Accel-Expires s absolutním časem stejné půlnoci.
Pouze status 200 se ukládá do cache. Chyby jsou no-store. Nginx nepoužívá
stale odpovědi, background update ani heuristické prodloužení TTL.
Pokud render přejde přes půlnoc, služba výsledek starého dne zahodí
a vrátí necachované 503 s krátkým Retry-After.

proxy_cache_lock omezí souběžné požadavky na stejný klíč. Doba locku
musí převyšovat upstream deadline. Po vypršení čekání mohou vzniknout
další upstream požadavky; globální limit a jediný renderer je dál omezují.
Externí If-None-Match se neposílá přímo upstreamu při naplnění cache;
ETag obsluhuje nginx a aplikace na samostatném přímém požadavku.

Nginx max_size 64 MiB a inactive 24h jsou průběžné limity. Cache a dočasné
soubory mají společný tmpfs s pevným stropem 80 MiB; tím se omezí i
dočasné překročení. Nginx keys_zone má 2 MiB. Cache je záměrně dočasná
a po restartu nginxu se doplní. Naplněné úložiště nesmí zastavit scheduler.

## Limity provozu

Nginx: limit 30 požadavků/min/IP, burst 10, překročení 429 a Retry-After.
Jde o konfigurovatelný výchozí limit, protože Živý obraz používá sdílené
servery. U přímého vstupu se používá socketová IP; real_ip je možné
zapnout pouze pro výslovně určenou důvěryhodnou nadřazenou proxy.

Aplikace: jeden proces, jeden render současně, nejvýše čtyři čekající
požadavky a globálně šest nových renderů/minutu s kapacitou špičky 2.
Žádný slovník limiteru pro každou IP, žádná PNG cache v RAM. Síťové
načítání dnešní fáze probíhá pod stejným omezením nákladné práce.
Přeplnění fronty je 503, překročení render budgetu 429. Obojí no-store.

Proces serveru má omezený počet vláken a backlog, proxy omezený počet
spojení. Moon kontejner má limit 256 MiB a nginx 128 MiB (včetně tmpfs).
Render 1024 × 1024 se změří. Při nesplnění limitu se upraví implementace,
nikoliv automaticky zvýší limit. Upstream timeout musí umožnit 10s MET
požadavek a render, ale nemá umožnit neomezené čekání.

## Nasazení

Moon není publikován na hostitelském portu. Nginx je dostupný na lokálním
portu pro stávající HTTPS proxy, s výchozím bindem 127.0.0.1. Přiložená
konfigurace zveřejní pouze /moon.png. Pro přímé HTTPS vystavení je třeba
konkrétní doména a certifikát; projekt nebude obsahovat domyšlené hodnoty,
privátní klíče ani automatické publikování na neznámý server.

Docker Compose oddělí přístup scheduleru k IMPORT_KEY od moon/nginx.
Dokumentace uvede lokální ověření, zapojení existující HTTPS proxy,
příklad URL a omezení sdílených IP.

Po ověření veřejné HTTPS URL se na obrazovce **Noční** vpravo nahoře
nahradí stávající symbol měsíce obrázkovým widgetem. Použije se velikost
stávajícího prostoru, URL bude požadovat odpovídající rozměry. Ostatní
prvky obrazovky se nemění. Před změnou se zaznamená původní nastavení
a po uložení se zkontroluje náhled. K dokončení je nutný přístup do
portálu Živého obrazu a existující veřejný hostitel; samotný lokální
endpoint nesplňuje požadavek funkčního widgetu.

## Ověření před dokončením

- Bitmapa: skutečný alpha kanál, odstraněné okolní pozadí, zachovaný
  obličej i raketa; vizuální kontrola originálu a výsledku.
- Fáze: nov, úplněk, obě čtvrti a srpky; správná strana osvětlení.
- PNG: 128, 256, 1024 a obdélníkový výstup; pouze černá a bílá.
- Datum: pražská půlnoc, letní čas, render přes půlnoc, výpadek MET.
- Vstupy: duplicity, neznámé klíče, různé pořadí, kódování a meze.
- Cache: HIT/MISS, kanonické klíče, spoofované Host/proxy hlavičky,
  no-store chyby, expirace a souběh stejných i různých rozměrů.
- Zátěž: 429/503, horní mez souběhu, paměť při 1024px a strop cache.
- Nginx -t a Docker Compose config; celý existující unittest suite.

## Zdroje

- Originál a informace o public domain:
  https://commons.wikimedia.org/wiki/File:Le_Voyage_dans_la_lune.jpg
- MET Norway: https://api.met.no/weatherapi/sunrise/3.0/documentation
- Živý obraz URL: https://zivyobraz.eu/docs/cs/webovy-portal/zdroj-obsahu/url/

Stav: návrh pro uživatelskou kontrolu před implementací HTTP služby.
