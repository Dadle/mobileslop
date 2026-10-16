#!/usr/bin/env bash
# Runs Lane Rush from source.
# Usage: ./run.sh              -> play (portrait window)
#        ./run.sh --editor     -> open the project in the Godot editor
#        ./run.sh --import     -> (re)import assets headlessly
#        ./run.sh --test [s]   -> bot playtest for s seconds, screenshots in .screenshots/test/
#        ./run.sh --software   -> force the CPU (lavapipe) Vulkan driver
#
# GPU out of VRAM? If Godot prints "Couldn't create Vulkan device (VkResult error -2/-3)" another app
# (e.g. a local LLM server) is holding the GPU memory. This script then automatically retries with a
# non-snap Godot binary on the software Vulkan driver (slow, ~5 fps, but it runs). Free VRAM for 60 fps.
set -uo pipefail
cd "$(dirname "$0")"
GODOT=${GODOT:-godot-4}
NATIVE=.godot-bin/Godot_v4.7.2-stable_linux.x86_64
NATIVE_URL=https://github.com/godotengine/godot-builds/releases/download/4.7.2-stable/Godot_v4.7.2-stable_linux.x86_64.zip
LVP_ICD=/usr/share/vulkan/icd.d/lvp_icd.json

ensure_native() {
  if [ ! -x "$NATIVE" ]; then
    echo "Downloading non-snap Godot 4.7.2 for the software fallback (~80 MB)..." >&2
    mkdir -p .godot-bin && curl -sfL -o .godot-bin/godot.zip "$NATIVE_URL" && (cd .godot-bin && unzip -qo godot.zip && rm godot.zip)
  fi
  [ -x "$NATIVE" ]
}

software_run() {
  if ! ensure_native; then echo "Could not get a native Godot binary." >&2; exit 1; fi
  if [ ! -f "$LVP_ICD" ]; then echo "No lavapipe driver at $LVP_ICD (sudo apt install mesa-vulkan-drivers)." >&2; exit 1; fi
  echo "GPU unavailable: running on the CPU Vulkan driver (lavapipe). Expect low fps." >&2
  VK_DRIVER_FILES=$LVP_ICD exec "$NATIVE" --path . "$@"
}

# run $GODOT; if it dies with the Vulkan-device error, retry on software rendering
run_with_fallback() {
  local log; log=$(mktemp)
  "$GODOT" --path . "$@" 2> >(tee "$log" >&2)
  local rc=$?
  if grep -q "Couldn't create Vulkan device" "$log"; then rm -f "$log"; software_run "$@"; fi
  rm -f "$log"; return $rc
}

if ! command -v "$GODOT" >/dev/null; then
  echo "Godot 4 not found. Install with: sudo snap install godot-4   (or set GODOT=/path/to/godot)" >&2
  exit 1
fi
case "${1:-}" in
  --editor)   exec "$GODOT" --path . --editor ;;
  --import)   exec "$GODOT" --headless --path . --import ;;
  --software) shift; software_run --resolution 540x960 "$@" ;;
  --test)
    rm -rf .screenshots/test
    run_with_fallback --resolution 540x960 -- --autopilot --shots-dir "$PWD/.screenshots/test" --duration "${2:-90}" --shot-interval 5 ;;
  *) run_with_fallback --resolution 540x960 "$@" ;;
esac
