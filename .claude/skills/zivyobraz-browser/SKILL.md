---
name: zivyobraz-browser
description: Use when editing or checking screens (obrazovky) on zivyobraz.eu through the browser — changing widget text, checking a preview, finding a widget by its content or which {{hodnoty}} are registered. Covers URLs, finding widgets, saving and verifying.
---

# Ovládání zivyobraz.eu přes prohlížeč

Použij vestavěný prohlížeč (`mcp__Claude_Browser__*`); přihlášení v něm už drží.

## Obrazovky
Dobré ráno 6930, Obědové 6924, Přehled světa 6923, Noční 6925.

## URL
- Přehled obrazovek: `https://zivyobraz.eu/muj-ucet/obrazovky`
- Editor: `https://zivyobraz.eu/muj-ucet/obrazovky/editor/<id>`
- Nefunguje: `obrazovky.php?editor=<id>` (skončí na přehledu ePaperů).
- ID obrazovek najdeš v odkazech na přehledu: `[...document.querySelectorAll('a')].filter(a=>/editor\/\d+/.test(a.href))`.

## Widget najdi podle obsahu, ne podle ID
Číslo v `obsah_NN` se mění. Po načtení editoru (počkej ~2,5 s):
```js
[...document.querySelectorAll('textarea[name^=obsah_]')]
  .filter(t => t.value.includes('{{pranostika}}')).map(t => t.name)
```
Textový widget je `textarea.textblok-textarea`, jeho náhled v seznamu `.screenElementMainValue`.

## Změna a uložení
1. Nastav `textarea.value`, vyvolej `input` a `change` (`dispatchEvent(new Event(..., {bubbles:true}))`).
2. Ulož: `document.getElementById('ulozit').click()`, počkej ~3 s.
3. Ověř: načti editor znovu a přečti `textarea.value`. Hlášku o uložení nehledej, ta je nespolehlivá.

## Hodnoty ({{...}})
Hodnoty posílá `main.py`; v editoru jsou v `<option>` výběru hodnot (hledej jejich název v HTML). Nová hodnota se zaregistruje až po prvním odeslání ze serveru, takže **nejdřív nasaď kód (viz skill `karotka-restart`), pak edituj widget**.

## Náhled
- `resize_window` (např. 1100×800), `screenshot` se `scale` ~0.6, pak `zoom` na oblast. Po skončení `resize_window` s `preset: "desktop"`.
- `img`/`canvas` v editoru jsou data URI: nevypisuj je celé (`javascript_tool` přeteče). Vypisuj jen atributy nebo délky.
- Obrázky nikdy nečti nástrojem Read.

## Pozor
- Měň jen to, co úkol žádá; ostatní rozložení zachovej.
- Neukládej, když nevíš, že úpravu uživatel schválil.
