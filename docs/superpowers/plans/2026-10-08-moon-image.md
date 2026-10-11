# Moon Image Implementation Plan

> **For agentic workers:** Use superpowers:executing-plans inline. User requested continuous work in this chat.

**Goal:** Public PNG moon images for Živý obraz, with voyage and real styles.
**Architecture:** One bounded WSGI process renders local bitmaps using daily MET
phase data. Nginx validates and normalizes requests before caching until Prague
midnight. Docker Compose exposes only nginx on loopback for an existing HTTPS proxy.
**Tech Stack:** Python 3.11, Pillow 12.2, Waitress 3.0.2, nginx, Docker Compose.
**Spec:** ../specs/2026-10-08-moon-image-design.md

## Global Constraints

- Default 128 × 128; each dimension 32–1024; style voyage default, real optional.
- Prague calendar date; no stale previous-day phase or images.
- One renderer, four waiters, six renders/min with burst two; no PNG cache in Python.
- Nginx cache target 64 MiB; hard tmpfs ceiling 80 MiB; bounded container memory.
- Host, headers, duplicates and unrecognized query parameters cannot affect cache content.

## Review Focus

- Duplicate style/size parameters must be rejected even when a cache entry already exists.
- Midnight/DST must invalidate images without confusing UTC with the Prague date.
- Cache lock alone cannot enforce global CPU limits for distinct keys.
- Real source attribution and share-alike must travel with rendered PNGs.
- Public widget requires actual reachable HTTPS hosting; localhost is insufficient.

## Task 1: Renderer and source assets

Files: functions/moon_image.py, assets/moon/*, test_moon_image.py.
Interface: parse_options(query) -> (width, height, style);
render_moon(width, height, style, degrees) -> PNG bytes.

- [x] Write validation, cardinal phase, image size/palette and attribution tests.
- [x] Run `python -m unittest test_moon_image -q`; observed missing module before implementation.
- [x] Implement local source rendering and final-size Floyd–Steinberg conversion.
- [x] Run tests and visually inspect 128px voyage/full and real/quarter previews.

## Task 2: Daily phase and bounded server

Files: functions/faze_mesice.py, moon_server.py, test_faze_mesice.py, test_moon_server.py, requirements.txt.
Interface: faze_mesice(day=None) retains scheduler-compatible dict result;
MoonApp is WSGI and owns a single phase slot, render lock and token bucket.

- [x] Write tests for explicit Prague dates, finite phase values, midnight expiry,
  DST, failures, next-day invalidation, request limits, serialization and HEAD/ETag.
- [x] Observe failures for missing server and unsupported date argument.
- [x] Implement the shared date fix, server and resource limits.
- [x] Run the new test modules: 19 tests passed.

## Task 3: Nginx integration and deployable configuration

Files: nginx/*.conf, docker-compose.yml, test_nginx_integration.py, README.md.
Consumes: /moon.png plus Cache-Control, ETag, X-Accel-Expires and attribution headers.

- [x] Add reproducible real-nginx integration checks for canonical cache HIT,
  style separation, duplicate rejection, spoofed headers, HEAD/ETag and rate limits.
- [x] Run `docker compose config --quiet`, nginx -t and the integration checks.
- [x] Measure 1024px render cost and container memory; run full unittest suite.
- [x] Document proxy integration, source licensing and operational limits.
- [x] Review final diff; preserve clean verified changes on feature/moon-image.

## Task 4: Hosting and Noční widget

- [x] Identify user-provided public domain/server and existing nginx deployment.
- [x] Deploy and verify both public PNG style URLs.
- [x] Replace the top-right moon symbol in Noční with an image widget using voyage.
- [x] Save and verify the screen preview; record old widget values for recovery.

## Execution record

Ruling: continue implementation after explicit "Pracuj na tom" rather than repeat
design/plan approval; preserve previous spec and incorporate requested styles.
Native worktree creation returned "Not a git repository" because the chat root is
W:/mpeterka; fallback worktree is W:/_wt/muj-zivyobraz-moon, branch feature/moon-image.
Baseline: 32 tests passed after installing existing dependencies into local .venv.
Docker Desktop was initially stopped; started hidden for isolated integration tests.
Hosted on karotka.peterka.name through existing HTTPS nginx, with two new internal
containers and the image tag moon-0b2a04d (registry digest
sha256:f6822a66c41ddb3a710a19cfd1a3bc8ff8773bd3c9d12b01da78eee3bd45d21e).
Built on the server from the tracked 0b2a04d snapshot over the earlier deployed
image; Python dependencies are unchanged. Existing services were not restarted.
Final validation: 54 unittest cases (53 passed, nginx case skipped in ordinary
discovery); nginx integration separately passed. Public real/voyage PNGs, black
background, transparency and duplicate-background rejection verified. Static
review found no blockers. Render and cache HIT logs verified on server.
Screen Noční (6925): image x=854, y=14, 128x128, layer 2, voyage,
background-color=%23000. Extra portal dithering disabled because PNG already
uses Floyd–Steinberg. Saved and reloaded; preview has no white background box.
Old moon-stars icon is hidden for recovery: x=888, y=48, size=60, black,
rotation=0, layer=2. Private screen proof is kept in ignored .superpowers/deploy.
