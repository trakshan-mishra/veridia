"""
Generate seamless, tileable PBR ground/wall/roof materials for Veridia using
fal.ai's PATINA text-to-material endpoint (fal-ai/patina/material).

Unlike a plain text-to-image call, PATINA is trained specifically to produce
materials that actually tile without visible seams, plus companion normal/
roughness maps — which is what makes a ground texture look right when it's
repeated hundreds of times across a terrain mesh.

Setup:
    pip install requests --break-system-packages
    export FAL_KEY="your-fal-ai-api-key"   # same key as generate_assets.py

Usage:
    python generate_textures_pbr.py

Output:
    assets/tex_ground_grass.png            (+ _normal.png, _roughness.png)
    assets/tex_ground_dirt_path.png        (+ _normal.png, _roughness.png)
    assets/tex_ground_cobblestone.png      (+ _normal.png, _roughness.png)
    assets/tex_wall_wood_plaster.png       (+ _normal.png, _roughness.png)
    assets/tex_roof_clay_tile.png          (+ _normal.png, _roughness.png)

Only the base *_.png files are wired into world.html today (it uses simple
MeshLambertMaterial maps). The _normal/_roughness maps are saved alongside so
you can upgrade world.html to MeshStandardMaterial with real PBR lighting
later without regenerating anything.
"""

import os
import time
import requests

FAL_KEY = os.environ.get("FAL_KEY")
if not FAL_KEY:
    raise SystemExit("Set FAL_KEY env var first: export FAL_KEY=your-fal-ai-key")

PATINA_URL = "https://queue.fal.run/fal-ai/patina/material"
HEADERS = {"Authorization": f"Key {FAL_KEY}", "Content-Type": "application/json"}

MASTER_STYLE = (
    "dark moody anime fantasy in the style of Redo of Healer, dusk village setting, "
    "warm ambient rim lighting, painterly cel-shaded rendering, muted warm-orange and "
    "deep-purple palette, high detail, consistent single art style across the whole set"
)
TEXTURE_SUFFIX = (
    ", " + MASTER_STYLE + ", seamless tileable texture, flat orthographic lighting, "
    "no baked shadows, no vignette, material swatch"
)

MATERIALS = [
    {"name": "tex_ground_grass", "prompt": "soft village grass field, warm dusk tint" + TEXTURE_SUFFIX},
    {"name": "tex_ground_dirt_path", "prompt": "worn dirt village path, small pebbles, grass edges" + TEXTURE_SUFFIX},
    {"name": "tex_ground_cobblestone", "prompt": "cobblestone town square paving, weathered stone" + TEXTURE_SUFFIX},
    {"name": "tex_wall_wood_plaster", "prompt": "half-timbered wood and plaster village house wall" + TEXTURE_SUFFIX},
    {"name": "tex_roof_clay_tile", "prompt": "red clay roof tiles, weathered fantasy village roofing" + TEXTURE_SUFFIX},
]


def submit_job(prompt: str) -> dict:
    resp = requests.post(PATINA_URL, headers=HEADERS, json={"prompt": prompt}, timeout=30)
    if not resp.ok:
        raise RuntimeError(f"Submit failed [{resp.status_code}]: {resp.text}")
    return resp.json()


def poll_job(submit_result: dict) -> dict:
    status_url = submit_result.get("status_url")
    result_url = submit_result.get("response_url")
    if not status_url or not result_url:
        raise RuntimeError(f"Unexpected submit response: {submit_result}")
    while True:
        status = requests.get(status_url, headers=HEADERS, timeout=30).json()
        state = status.get("status")
        if state == "COMPLETED":
            r = requests.get(result_url, headers=HEADERS, timeout=30)
            if not r.ok:
                raise RuntimeError(f"Result fetch failed [{r.status_code}]: {r.text}")
            return r.json()
        if state == "FAILED":
            raise RuntimeError(f"Job failed: {status}")
        time.sleep(2)


def download(url: str, out_path: str):
    r = requests.get(url, timeout=60)
    r.raise_for_status()
    with open(out_path, "wb") as f:
        f.write(r.content)


def main():
    out_dir = "assets"
    os.makedirs(out_dir, exist_ok=True)

    for mat in MATERIALS:
        print(f"Generating material: {mat['name']}...")
        result = poll_job(submit_job(mat["prompt"]))
        images = result.get("images", [])
        if not images:
            print(f"  WARNING: no images returned for {mat['name']}, skipping")
            continue
        # images[0] is the base color/albedo texture; remaining entries are PBR maps
        # (map_type field distinguishes normal/roughness/etc — see fal docs for exact keys)
        base = images[0]
        download(base["url"], os.path.join(out_dir, f"{mat['name']}.png"))
        print(f"  saved -> assets/{mat['name']}.png")
        for extra in images[1:]:
            map_type = extra.get("map_type", "map")
            out_path = os.path.join(out_dir, f"{mat['name']}_{map_type}.png")
            download(extra["url"], out_path)
            print(f"  saved -> {out_path}")

    print(f"\nDone. {len(MATERIALS)} seamless PBR materials saved into ./assets/")


if __name__ == "__main__":
    main()
