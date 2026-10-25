#!/bin/sh
set -eu
image=${1:?Pass the image to test}
network=moon-runtime-test
cleanup() {
  docker rm -f moon-runtime-nginx moon-runtime-app >/dev/null 2>&1 || true
  docker network rm "$network" >/dev/null 2>&1 || true
}
trap cleanup EXIT
docker network create "$network" >/dev/null
docker run -d --name moon-runtime-app --network "$network" --network-alias moon \
  --read-only --tmpfs /tmp:size=8m --cap-drop ALL --security-opt no-new-privileges \
  "$image" python -c 'from waitress import serve; from moon_server import MoonApp; serve(MoonApp(phase_source=lambda day:90),host="0.0.0.0",port=8080)' >/dev/null
docker run -d --name moon-runtime-nginx --network "$network" \
  --read-only --tmpfs /var/cache/moon:size=80m,mode=1777 \
  --tmpfs /var/cache/nginx:size=4m,mode=1777 --tmpfs /var/run:size=1m --tmpfs /tmp:size=4m \
  -v "$PWD/nginx/nginx.conf:/etc/nginx/nginx.conf:ro" \
  -v "$PWD/nginx/moon.conf:/etc/nginx/conf.d/default.conf:ro" nginx:stable-alpine >/dev/null
docker run --rm --network "$network" "$image" python -c '
import socket, time
for host in ["moon", "moon-runtime-nginx"]:
    for attempt in range(30):
        try:
            socket.create_connection((host, 8080), timeout=1).close()
            break
        except OSError:
            time.sleep(1)
    else:
        raise RuntimeError(f"{host} did not start")
'
docker run --rm --network "$network" --read-only --tmpfs /tmp:size=16m \
  --cap-drop ALL --security-opt no-new-privileges \
  -e IMPORT_KEY=test-only -e MOON_TEST_URL=http://moon-runtime-nginx:8080 \
  "$image" python -m unittest discover -v
docker run --rm --network none "$image" \
  python -c 'import os, pathlib; assert pathlib.Path("/etc/alpine-release").is_file(); assert os.geteuid() == 65534'
