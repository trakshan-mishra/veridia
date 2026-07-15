# Deploy — exact commands

The `site/` folder is the whole website (static, no build step).
- `index.html` — **Veridia**, the 3D open-world landing (Three.js via CDN)
- `portfolio.html` — the classic scrolling portfolio (linked from the world's top-right corner)

Download it from the chat, unzip, then:

## Option A — Cloudflare Pages via CLI (fastest)
```bash
# one-time
npm install -g wrangler
wrangler login

# deploy (run from the folder that contains index.html)
cd site
wrangler pages deploy . --project-name trakshan-portfolio
```
You get a live URL like `https://trakshan-portfolio.pages.dev` immediately.
Re-run the same `wrangler pages deploy` command to publish updates.

## Option B — Cloudflare dashboard (no CLI)
1. dash.cloudflare.com → **Workers & Pages → Create → Pages → Upload assets**
2. Drag the `site/` folder in → name the project → **Deploy**.

## Option C — GitHub + auto-deploys
```bash
cd site
git init && git add -A && git commit -m "portfolio"
git remote add origin https://github.com/trakshan-mishra/portfolio.git
git push -u origin main
```
Then Cloudflare Pages → **Connect to Git** → pick the repo →
Framework preset: **None** · Build command: *(empty)* · Output dir: `/` → Deploy.
Every `git push` redeploys.

## Custom domain
Pages project → **Custom domains** → add `trakshan.dev` (or whatever you own) → follow the DNS prompt.

## Photo note
Visitors can only VIEW the avatar. To set it: drop your photo on the circle in the design editor here, then copy the generated `.image-slots.state.json` into `site/` and redeploy.
