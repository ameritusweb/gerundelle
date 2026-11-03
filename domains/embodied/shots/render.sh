#!/bin/sh
# Render the scene headlessly to a PNG and print its console lines.
# usage: sh render.sh <out.png> [query] [width] [height]   (the server must be running on :8765)
out="$1"; q="${2:-}"; w="${3:-1400}"; h="${4:-900}"
prof="$TEMP/chr-embodied-$$"
timeout 120 "/c/Program Files/Google/Chrome/Application/chrome.exe" --headless=new --use-angle=swiftshader \
  --enable-unsafe-swiftshader --window-size="$w,$h" --virtual-time-budget=25000 --enable-logging=stderr --v=0 \
  --user-data-dir="$prof" --screenshot="$out" "http://127.0.0.1:8765/scene/index.html$q" 2>&1 \
  | grep -E "CONSOLE|Uncaught" | sed 's/.*CONSOLE[^"]*//'
rm -rf "$prof"
