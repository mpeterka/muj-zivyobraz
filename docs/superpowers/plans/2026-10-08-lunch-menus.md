# Lunch menus implementation plan

**Goal:** Make screen 6924 readable with two columns of restaurant blocks.
**Architecture:** One scrape produces the unchanged legacy `menicka` value and separate bounded multiline values. Five display slots contain only restaurants with today's offer; unavailable restaurants share a status line. The scheduled job uploads the values together.
**Spec:** User-approved conversation: retain the 25-character limit, cut at word boundaries for the new view, use separate bold headings and fixed body font, retain all five scraped dishes and show menu date/load time.
**Constraints:** No dependency changes. Preserve existing screens and schedule. Update only screen 6924. Empty slots must overwrite older values. HTTP failures must be distinguishable from absent menus.

### Task 1: Data and integration
- [ ] Add parser tests for separate lines, legacy compatibility, truncation, five-dish bound, absent/error menus and cleared slots.
- [ ] Run the new tests before implementation; expect missing new entry point.
- [ ] Add `get_menicka_values()` in `functions/menicka.py`; retain the legacy wrapper. Update `main.py` to upload all values and document the keys in `README.md`.
- [ ] Run `python -m unittest discover -v`; inspect the diff and commit.

### Task 2: Deployment and screen
- [ ] Push the approved change; wait for the image build, then recreate only `muj-zivyobraz` on karotka.
- [ ] Run the menu job and confirm successful upload.
- [ ] Save the original screen form locally, create five separate heading/body slots, reduce weather height, and add date/time/status.
- [ ] Verify real menus in the saved/reloaded preview and a five-slot maximum-length layout. Save a screenshot artifact.

**Review focus:** Today's dates only; legacy output unchanged; empty/error slots clear old menus; longer first words remain bounded; five full menus fit without shrinking other restaurants' font.
**Execution:** Inline under existing authorization. Use current clean checkout as in the previous approved deployment.
