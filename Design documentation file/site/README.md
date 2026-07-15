# Trakshan Mishra — Portfolio (deployable)

Static site. No build step, no server.

## Deploy to Cloudflare Pages
1. Push this `site/` folder to a GitHub repo (or drag-drop the folder in the Pages dashboard).
2. Cloudflare dashboard → **Workers & Pages → Create → Pages → Upload assets** (or connect the repo).
3. Build settings: **none** (no framework, no build command, output dir = `/`).
4. Deploy. Done — `index.html` is the whole site.

Also works on Netlify / Vercel / GitHub Pages the same way.

## Photo
The avatar image is read-only for visitors: the slot loads the photo you saved
(`.image-slots.state.json`, written when you drop a photo in the design editor)
and cannot be modified on the deployed site. To change it, drop a new photo in
the editor and re-copy the sidecar file into this folder.

## Files
- `index.html` — the site
- `support.js` — component runtime
- `image-slot.js` — read-only avatar loader
- `.image-slots.state.json` — your saved photo (copy it here after you drop one; without it visitors see the "TM" monogram)
