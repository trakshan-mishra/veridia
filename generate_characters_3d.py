"""
Turn Veridia's 2D character portraits into real, rigged 3D characters using the
Meshy API (image-to-3D, then auto-rigging with basic walk/idle animation).

This is what actually gives you moving 3D NPCs instead of the procedural
capsule-rig fallback built into world.html. Run generate_assets.py FIRST —
this script reads the PNGs it produces.

Requires a Meshy account on the Pro tier or above (Meshy's API is not available
on the free tier as of writing — check meshy.ai/api for current pricing).

Setup:
    pip install requests --break-system-packages
    export MESHY_API_KEY="msy-..."     # https://www.meshy.ai/settings/api

Usage:
    python generate_characters_3d.py

Output (matches the .glb paths already wired into world.html's npcModel() calls):
    assets/village_elder.glb
    assets/vanguard.glb
    assets/chronicler.glb
    assets/gatekeeper.glb
    assets/bartender_npc.glb   (see note at bottom — not yet auto-loaded in the tavern scene)

world.html will auto-detect these files and upgrade from its procedural rig to
the real model with zero code changes, the next time it's loaded.
"""

import os
import time
import base64
import requests

MESHY_API_KEY = os.environ.get("MESHY_API_KEY")
if not MESHY_API_KEY:
    raise SystemExit("Set MESHY_API_KEY env var first: export MESHY_API_KEY=msy-...")

BASE = "https://api.meshy.ai/openapi/v1"
HEADERS = {"Authorization": f"Bearer {MESHY_API_KEY}", "Content-Type": "application/json"}

# name -> source PNG produced by generate_assets.py, and target .glb filename
CHARACTERS = [
    {"source": "assets/village_elder.png", "out": "village_elder.glb", "height": 1.75},
    {"source": "assets/vanguard.png", "out": "vanguard.glb", "height": 1.9},
    {"source": "assets/chronicler.png", "out": "chronicler.glb", "height": 1.8},
    {"source": "assets/gatekeeper.png", "out": "gatekeeper.glb", "height": 1.85},
    {"source": "assets/bartender_npc.png", "out": "bartender_npc.glb", "height": 1.75},
]


def image_to_data_uri(path: str) -> str:
    with open(path, "rb") as f:
        b64 = base64.b64encode(f.read()).decode("ascii")
    return f"data:image/png;base64,{b64}"


def poll(path: str) -> dict:
    while True:
        r = requests.get(f"{BASE}/{path}", headers=HEADERS, timeout=30)
        if not r.ok:
            raise RuntimeError(f"Poll failed [{r.status_code}]: {r.text}")
        task = r.json()
        status = task.get("status")
        if status == "SUCCEEDED":
            return task
        if status in ("FAILED", "CANCELED"):
            raise RuntimeError(f"Task {status}: {task}")
        time.sleep(4)


def image_to_3d(data_uri: str) -> str:
    """Returns the completed image-to-3d task id."""
    r = requests.post(
        f"{BASE}/image-to-3d",
        headers=HEADERS,
        json={"image_url": data_uri, "should_texture": True, "ai_model": "meshy-6"},
        timeout=60,
    )
    if not r.ok:
        raise RuntimeError(f"image-to-3d submit failed [{r.status_code}]: {r.text}")
    task_id = r.json()["result"]
    poll(f"image-to-3d/{task_id}")
    return task_id


def rig(task_id: str, height_meters: float) -> dict:
    """Rigs the completed image-to-3d task, returns the rigged task (with model_urls.glb)."""
    r = requests.post(
        f"{BASE}/rigging",
        headers=HEADERS,
        json={"input_task_id": task_id, "height_meters": height_meters},
        timeout=60,
    )
    if not r.ok:
        raise RuntimeError(f"rigging submit failed [{r.status_code}]: {r.text}")
    rig_task_id = r.json()["result"]
    return poll(f"rigging/{rig_task_id}")


def download(url: str, out_path: str):
    r = requests.get(url, timeout=120)
    r.raise_for_status()
    with open(out_path, "wb") as f:
        f.write(r.content)


def main():
    out_dir = "assets"
    os.makedirs(out_dir, exist_ok=True)

    for c in CHARACTERS:
        if not os.path.exists(c["source"]):
            print(f"SKIP {c['out']}: {c['source']} not found — run generate_assets.py first")
            continue
        print(f"Generating 3D model: {c['out']} (from {c['source']})...")
        data_uri = image_to_data_uri(c["source"])
        task_id = image_to_3d(data_uri)
        print("  mesh done, rigging...")
        rigged = rig(task_id, c["height"])
        glb_url = rigged.get("model_urls", {}).get("glb")
        if not glb_url:
            print(f"  WARNING: no glb in rigging result for {c['out']}: {rigged}")
            continue
        out_path = os.path.join(out_dir, c["out"])
        download(glb_url, out_path)
        print(f"  saved -> {out_path}")

    print("\nDone. Reload world.html — matching .glb files auto-upgrade from the")
    print("procedural rig to these real rigged models, no code changes needed.")
    print("\nNote: bartender_npc.glb is generated but not yet wired into the tavern")
    print("scene in world.html (the bartender is currently a 2D portrait in the")
    print("dialogue UI, not an in-world 3D model) — ask if you want that hooked up too.")


if __name__ == "__main__":
    main()
