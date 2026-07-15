#!/usr/bin/env bash
# Runs the full Veridia asset pipeline in the right order, into ./assets/,
# which world.html already reads from directly.
set -e

if [ -z "$FAL_KEY" ]; then
  echo "Missing FAL_KEY. Run: export FAL_KEY=your-fal-ai-key"
  exit 1
fi

echo "== Step 1/3: 2D art (characters, sky, tavern, props) via fal.ai flux =="
python3 generate_assets.py

echo
echo "== Step 2/3: seamless PBR ground/wall/roof materials via fal.ai PATINA =="
python3 generate_textures_pbr.py

echo
if [ -z "$MESHY_API_KEY" ]; then
  echo "== Step 3/3: SKIPPED — MESHY_API_KEY not set =="
  echo "   Set it (export MESHY_API_KEY=msy-...) and re-run this script, or run"
  echo "   'python3 generate_characters_3d.py' on its own later, to add rigged"
  echo "   3D characters. world.html works fine without this step — it just"
  echo "   keeps using the built-in procedural character rigs."
else
  echo "== Step 3/3: rigged 3D characters via Meshy =="
  python3 generate_characters_3d.py
fi

echo
echo "All done. assets/ now contains everything world.html looks for."
echo "Open world.html in a browser to see the result."
