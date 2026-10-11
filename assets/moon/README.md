# Filmový Měsíc

- `source.jpg`: vybraný originál, 257 × 264 px.
- `real-source.jpg`: Full Moon Luc Viatour, originál 1411 × 1424 px.
  Autor Luc Viatour / https://lucnix.be. Licence CC BY-SA 3.0:
  https://creativecommons.org/licenses/by-sa/3.0/
  Zdroj: https://commons.wikimedia.org/wiki/File:Full_Moon_Luc_Viatour.jpg
  Originál: https://upload.wikimedia.org/wikipedia/commons/d/dd/Full_Moon_Luc_Viatour.jpg
  Odvozené obrázky stylu real jsou rovněž CC BY-SA 3.0. Úpravy: výřez,
  maska fáze, změna velikosti a černobílý dithering. Autor, licence a zdroj
  jsou také v PNG textových metadatech a HTTP hlavičkách. Fotografie je
  téměř úplněk; vlastní stíny záběru se matematicky neodstraňují.
- `melies-cutout.png`: odvozený podklad s průhledným okolím, vytvořený
  vestavěným ImageGen nástrojem. Zachovává obličej a raketu. Jde o AI úpravu
  bitmapy, nikoliv o pixelově identickou ruční masku originálu.

Film: Le Voyage dans la lune / Cesta na Měsíc (1902), Georges Méliès.
Zdroj: https://commons.wikimedia.org/wiki/File:Le_Voyage_dans_la_lune.jpg
Originál: https://upload.wikimedia.org/wikipedia/commons/0/04/Le_Voyage_dans_la_lune.jpg
Wikimedia Commons označuje originál jako public domain.

Použitý prompt pro ImageGen:

> Use case: background-extraction. Edit target: supplied original 1902 Le
> Voyage dans la lune film still. Remove ONLY black background outside the
> moon and protruding rocket, producing genuinely transparent alpha. Preserve
> exactly the original moon face, crater texture, expression, rocket lodged
> in its eye, original black and white tones and film grain. Do not redraw or
> invent detail, do not remove the rocket, do not erase dark areas inside
> subject. Keep entire silhouette including protruding rocket inside a square
> canvas with small transparent margin. This is a reusable bitmap for 128px
> and 256px moon phase icons. No text, no added elements.
