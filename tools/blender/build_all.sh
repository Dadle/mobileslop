#!/usr/bin/env bash
# Regenerate every GLB in assets/models and the preview PNGs. Usage: tools/blender/build_all.sh
set -euo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"
export PREVIEW_DIR="${PREVIEW_DIR:-$(cd "$(dirname "$0")/../.." && pwd)/.previews}"
mkdir -p "$PREVIEW_DIR"
for s in make_characters make_props make_world make_upgrades; do
  echo "=== $s"
  blender -b --python "$HERE/$s.py" 2>&1 | grep -E "^\[(export|preview)\]|Error|Traceback|^  " || true
done
echo "=== verify"
blender -b --python "$HERE/verify_glb.py" 2>&1 | sed -n '/^=== /,$p' | grep -v "^Blender\|INFO"
