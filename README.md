# Veridia — an open-world portfolio

A single-file Three.js village playable demo. Explore the vale of Veridia, take
bounties at the notice board, gather resources, help the villagers, trade with
Aldric, and read the builder's story carved through the world.

**Controls:** WASD move · mouse look · SHIFT sprint · SPACE jump · E interact /
gather · 1–9 dialogue options · J track quest · Q close.

## Run locally

Any static file server works — the app is pure client-side (Three.js is vendored
in `vendor/`, no build step):

```bash
python3 -m http.server 4173
# open http://127.0.0.1:4173/          (index.html)
```

## Deploy

The whole folder is the static site (`index.html` is the entry point). See the
GitHub + Cloudflare Pages steps in the deploy notes, then every `git push`
redeploys automatically.

- `index.html` / `world.html` — the game (identical; index is the entry point)
- `vendor/` — Three.js + GLTFLoader
- `assets/`, `*.glb` — 3D models
- `_headers` — Cloudflare Pages cache rules
