---
name: karotka-restart
description: Use when deploying or restarting the muj-zivyobraz service on the server karotka.peterka.name — after a push to GitHub main, to pull the new image, recreate the container, or check its logs.
---

# Nasazení a restart muj-zivyobraz na karotka

Server: `karotka.peterka.name` (SSH), compose adresář `/home/karotka`, služba `muj-zivyobraz`.

## Postup
1. Testy: `.venv/Scripts/python.exe -m unittest discover` (z kořene repa).
2. Push na `main` (`git push origin HEAD:main`). V pracovním stromu mohou být cizí rozpracované změny; commituj jen soubory úkolu (`git add <soubory>`, ne `-A`).
3. Počkej na CI (GitHub Actions „Build and Push Docker Image“), ne na čas:
   ```bash
   gh run watch $(gh run list --limit 1 --json databaseId -q '.[0].databaseId') --exit-status
   gh run list --limit 1
   ```
   Poslední běh musí být `success` a patřit k tvému commitu. Čekání dlouhé přes pár sekund pusť na pozadí.
4. Nasazení:
   ```bash
   ssh karotka.peterka.name "cd /home/karotka && docker compose pull muj-zivyobraz && docker compose up -d --no-deps muj-zivyobraz"
   ```
5. Kontrola po ~15 s:
   ```bash
   ssh karotka.peterka.name "cd /home/karotka && docker compose logs --tail 30 muj-zivyobraz"
   ```
   Čekej `Multiple values sent | Status: 200`, `Scheduler started` a řádky `Added job ...`. Chyby/tracebacky = nasazení nehotové.

## Poznámky
- Joby běží při startu, po SIGUSR1 a podle cronu; po restartu se hodnoty hned znovu odešlou.
- Změna widgetu na zivyobraz.eu se dělá až po nasazení, viz skill `zivyobraz-browser`.
- Restart bez nové image: stačí krok 4 bez `pull`, nebo `docker compose restart muj-zivyobraz`.
- Nepouštěj `docker compose down` ani akce na jiných službách v `/home/karotka`.
