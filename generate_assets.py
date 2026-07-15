"""
Generate anime-style (Redo of Healer-inspired) character sprites and village
props using the fal.ai API.

Setup:
    pip install requests --break-system-packages
    export FAL_KEY="your-fal-ai-api-key"   # get one at https://fal.ai/dashboard/keys

Usage:
    python generate_assets.py

Notes:
    - Uses fal-ai/flux/dev for stylized 2D character/prop art (fast, good anime style control).
    - Swap the model endpoint for fal-ai/flux-pro or a LoRA-tuned anime checkpoint if you
      want a more consistent house style across all characters.
    - Output images are saved locally, then you drop them into your site's /assets folder
      and reference them from world.html (as sprite billboards or textures).
"""

import os
import time
import requests

FAL_KEY = '52f0aa46-5b83-4108-b754-b4ae172b1ce3:afd6c1678c01d89e706fd770eac6f778'
if not FAL_KEY:
    raise SystemExit("Set FAL_KEY env var first: export FAL_KEY=your-fal-ai-key")

FAL_MODEL = "fal-ai/flux/dev"
FAL_QUEUE_URL = f"https://queue.fal.run/{FAL_MODEL}"

HEADERS = {
    "Authorization": f"Key {FAL_KEY}",
    "Content-Type": "application/json",
}

# ---------- MASTER STYLE PROMPT — shared across generate_assets.py, ----------
# ---------- generate_textures_pbr.py, and generate_characters_3d.py  ----------
MASTER_STYLE = (
    "dark moody anime fantasy in the style of Redo of Healer, dusk village setting, "
    "warm ambient rim lighting, painterly cel-shaded rendering, expressive character "
    "silhouettes, muted warm-orange and deep-purple palette, subtle film grain, "
    "high detail, consistent single art style across the whole set"
)

# Style suffix for character sprites (transparent background, full body, NEUTRAL POSE —
# a neutral/T-pose standing sprite is what makes generate_characters_3d.py's image-to-3D
# + auto-rig step work well; an action pose converts badly)
STYLE_SUFFIX = (
    ", " + MASTER_STYLE + ", full body character sprite, T-pose or neutral standing pose, "
    "transparent background, game asset, clean silhouette for 3D conversion"
)

# Style suffix for environment textures (seamless/tileable, no character, no background scene)
TEXTURE_SUFFIX = (
    ", " + MASTER_STYLE + ", seamless tileable texture, flat orthographic lighting, "
    "no baked shadows, no vignette, material swatch, game texture asset"
)

ASSETS = [
    {
        "name": "chronicler",
        "prompt": "hooded scholar NPC character, holding a glowing scroll" + STYLE_SUFFIX,
    },
    {
        "name": "vanguard",
        "prompt": "armored warrior guard NPC character, standing at attention" + STYLE_SUFFIX,
    },
    {
        "name": "gatekeeper",
        "prompt": "mysterious cloaked gatekeeper NPC character, staff in hand" + STYLE_SUFFIX,
    },
    {
        "name": "village_elder",
        "prompt": "elderly village elder NPC character, warm robes, kind expression" + STYLE_SUFFIX,
    },
    {
        "name": "player_default",
        "prompt": "young adventurer protagonist character, traveling cloak, determined pose" + STYLE_SUFFIX,
    },
    {
        "name": "village_prop_lamp",
        "prompt": "ornate street lamp post, warm glowing light, fantasy village prop"
        + STYLE_SUFFIX,
    },
    # NOTE: ground/wall/roof PBR materials are generated separately by
    # generate_textures_pbr.py (fal.ai PATINA), which produces true seamless
    # tileable materials rather than a single flat image. Run that script too.
    {
        "name": "sky_dusk_gradient",
        "prompt": (
            "dusk sky gradient, deep purple to warm orange horizon, soft clouds, "
            "faint early stars, anime painterly style, 360 skybox panorama, "
            "no ground, no characters"
        ),
        "image_size": "landscape_16_9",
    },
    {
        "name": "sky_sunrise_gradient",
        "prompt": (
            "sunrise sky gradient, soft pink and gold horizon fading to pale blue, "
            "thin morning clouds catching light, anime painterly style, "
            "360 skybox panorama, no ground, no characters"
        ),
        "image_size": "landscape_16_9",
    },
    {
        "name": "sky_night_gradient",
        "prompt": (
            "clear night sky, deep indigo to black gradient, scattered stars, "
            "faint moon glow, anime painterly style, 360 skybox panorama, "
            "no ground, no characters"
        ),
        "image_size": "landscape_16_9",
    },
    {
        "name": "prop_tree_anime",
        "prompt": "stylized anime fantasy tree, warm dusk lighting, rounded foliage"
        + STYLE_SUFFIX,
    },
    {
        "name": "village_pond",
        "prompt": (
            "small tranquil village pond, lily pads, reflecting dusk sky, stone edging, "
            "wooden dock, fireflies" + STYLE_SUFFIX
        ),
    },
    {
        "name": "tavern_exterior",
        "prompt": (
            "cozy fantasy village tavern building exterior, warm glowing windows, "
            "wooden sign hanging above door, smoke from chimney" + STYLE_SUFFIX
        ),
    },
    {
        "name": "tavern_interior",
        "prompt": (
            "cozy tavern interior, wooden bar counter, hanging lanterns, barrels, "
            "warm firelight, anime painterly style, game background scene"
        ),
    },
    {
        "name": "bartender_npc",
        "prompt": "friendly tavern bartender NPC character, apron, polishing a mug"
        + STYLE_SUFFIX,
    },
    {
        "name": "prop_drink_mug",
        "prompt": "wooden mug of ale with foam, glowing warm highlight, item icon"
        + STYLE_SUFFIX,
    },
]


def submit_job(prompt: str, image_size: str = "square_hd") -> dict:
    resp = requests.post(
        FAL_QUEUE_URL,
        headers=HEADERS,
        json={
            "prompt": prompt,
            "image_size": image_size,
            "num_images": 1,
        },
        timeout=30,
    )
    if not resp.ok:
        raise RuntimeError(f"Submit failed [{resp.status_code}]: {resp.text}")
    # fal returns request_id plus ready-to-use status_url / response_url —
    # use those directly rather than reconstructing them ourselves.
    return resp.json()


def poll_job(submit_result: dict) -> dict:
    status_url = submit_result.get("status_url")
    result_url = submit_result.get("response_url")
    if not status_url or not result_url:
        raise RuntimeError(f"Unexpected submit response, no status/response url: {submit_result}")

    while True:
        status_resp = requests.get(status_url, headers=HEADERS, timeout=30)
        if not status_resp.ok:
            raise RuntimeError(f"Status check failed [{status_resp.status_code}]: {status_resp.text}")
        status = status_resp.json()

        state = status.get("status")
        if state == "COMPLETED":
            result_resp = requests.get(result_url, headers=HEADERS, timeout=30)
            if not result_resp.ok:
                raise RuntimeError(f"Result fetch failed [{result_resp.status_code}]: {result_resp.text}")
            return result_resp.json()
        if state == "FAILED":
            raise RuntimeError(f"Job failed: {status}")
        time.sleep(2)


def download_image(url: str, out_path: str):
    r = requests.get(url, timeout=60)
    r.raise_for_status()
    with open(out_path, "wb") as f:
        f.write(r.content)


def main():
    out_dir = "assets"
    os.makedirs(out_dir, exist_ok=True)

    for asset in ASSETS:
        print(f"Generating: {asset['name']}...")
        submit_result = submit_job(asset["prompt"], asset.get("image_size", "square_hd"))
        result = poll_job(submit_result)
        image_url = result["images"][0]["url"]
        out_path = os.path.join(out_dir, f"{asset['name']}.png")
        download_image(image_url, out_path)
        print(f"  saved -> {out_path}")

    print(f"\nDone. {len(ASSETS)} images saved directly into ./{out_dir}/")
    print("Place that folder next to world.html (same directory) and it'll pick them up.")


if __name__ == "__main__":
    main()