# Veridia asset pipeline — master prompt + generation scripts

## 1. Master style prompt (use this everywhere, for consistency)

Every generation call — 2D art, textures, 3D characters — should carry this same
style backbone so nothing looks like it came from a different game:

```
MASTER_STYLE = (
    "dark moody anime fantasy in the style of Redo of Healer, dusk village setting, "
    "warm ambient rim lighting, painterly cel-shaded rendering, expressive character "
    "silhouettes, muted warm-orange and deep-purple palette, subtle film grain, "
    "high detail, consistent single art style across the whole set"
)
```

Then each asset type appends a role-specific suffix on top of `MASTER_STYLE`:

- **Character sprite**: `+ ", full body character sprite, T-pose or neutral standing pose, transparent background, game asset, clean silhouette for 3D conversion"`
  (T-pose / neutral standing matters a lot — it's what makes the image-to-3D and
  auto-rig steps below actually work well. Side-on action poses convert badly.)
- **PBR texture/material**: `+ ", seamless tileable texture, flat orthographic lighting, no baked shadows, no vignette, material swatch, physically based rendering"`
- **Sky panorama**: `+ ", 360 equirectangular skybox panorama, no ground, no characters, no foreground objects"`

Keeping one master string and appending suffixes (rather than writing each prompt
from scratch) is what keeps 20+ generated assets feeling like one game.

## 2. What generates what

| Script | Provider | Produces |
|---|---|---|
| `generate_assets.py` | fal.ai `flux/dev` | 2D character portraits, sky panoramas, tavern scenes, prop icons |
| `generate_textures_pbr.py` | fal.ai PATINA | Seamless ground/wall/roof PBR material sets |
| `generate_characters_3d.py` | Meshy API | Rigged + animated `.glb` characters, built from the 2D portraits above |

All three write into `./assets/`, matching exactly what `world.html` already expects
(including the `.glb` progressive-enhancement paths already wired into the code).

## 3. Setup — API keys needed

```bash
export FAL_KEY="your-fal-ai-key"        # https://fal.ai/dashboard/keys — same key for flux + PATINA
export MESHY_API_KEY="msy-..."          # https://www.meshy.ai/settings/api — requires Pro tier or above
pip install requests --break-system-packages
```

## 4. Run order (or just run `./run_pipeline.sh`)

```bash
python generate_assets.py          # 2D art first — characters, sky, tavern, props
python generate_textures_pbr.py    # ground/wall/roof PBR materials
python generate_characters_3d.py   # turns the 2D character art into rigged, animated .glb models
```

`generate_characters_3d.py` depends on the PNGs from step 1 already existing in
`assets/`, so run it last.

## 5. Cost ballpark (at time of writing)

- flux/dev 2D image: ~$0.003–0.01 each × ~19 assets ≈ under $0.20 total
- PATINA material set: ~$0.08–0.10 each × 5 materials ≈ ~$0.45 total
- Meshy image-to-3d + rig per character: a few credits each on a Pro-tier plan
  (Meshy's API requires Pro tier or above — check meshy.ai/api for current pricing)

Prices and endpoints shift often in this space — re-check fal.ai/pricing and
meshy.ai/api before a big batch run.
