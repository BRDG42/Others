# BRDG · Spotlight — Instagram publisher

A tiny backend that auto-posts a Spotlight set from the PWA:

- the **5 square frames → one carousel** feed post (with caption)
- the **2 story frames → two stories**

It uses Instagram's official **Graph Content Publishing API**. The PWA renders
the 7 PNGs, sends them here, and this service hosts them at a public URL (so
Instagram can fetch them) and runs the publish. Your access token stays here,
never in the browser.

> **Why a backend at all?** Instagram only publishes from a server, fetches
> images by public URL, and requires a secret token — none of which can live in
> a static site. GitHub Pages can't run this; deploy it to any Node host.

---

## 1. Instagram / Meta setup (you do this once)

1. Convert the Instagram account to **Business or Creator** and link it to a
   **Facebook Page**.
2. Create an app at <https://developers.facebook.com> → add **Instagram Graph API**.
3. Get a **long-lived access token** (or a System User token) with scopes:
   `instagram_basic`, `instagram_content_publish`, `pages_show_list`,
   `pages_read_engagement`.
4. Find your **Instagram user id**:
   - `GET /me/accounts` → your Page id
   - `GET /{page-id}?fields=instagram_business_account` → the IG user id
5. **Going live:** publishing to the account in production needs **Advanced
   Access** for `instagram_content_publish` (Meta **App Review** + business
   verification). While the app is in **Development mode** you can publish to
   accounts with a role on the app (great for testing).

Limits worth knowing: image URLs must be public **JPEG/PNG**, and accounts have
a rolling **25 posts / 24 h** publish cap.

## 2. Deploy

Any Node ≥18 host works (Render, Railway, Fly.io, a VPS). Example (Render):

1. New **Web Service** → point at this `server/` folder.
2. Build: `npm install` · Start: `npm start`
3. Set the environment variables from `.env.example`:
   - `IG_USER_ID`, `IG_ACCESS_TOKEN`, `PUBLISH_SECRET`
   - `PUBLIC_BASE_URL` = the service's own https URL (e.g. `https://brdg-spotlight.onrender.com`)
   - `ALLOW_ORIGIN` = `https://brdg42.github.io`
4. Deploy, then open `/health` → `{"ok":true,...}`.

`PUBLISH_SECRET`: generate with `openssl rand -hex 24`.

## 3. Connect the app

In the PWA: **Export → Publish to IG → Connection settings** → paste the
**Publisher URL** and the **Secret**. Tick the confirm box → **Publish**.

## Test without Instagram (dry run)

```bash
cd server
npm install
IG_DRY_RUN=1 PUBLISH_SECRET=test PUBLIC_BASE_URL=http://localhost:8080 npm start
# health
curl localhost:8080/health
```

In dry-run the publish flow runs but Instagram is **not** called — it returns
fake ids — so you can verify wiring before going live.

## API

`POST /api/publish` — header `x-publish-secret: <PUBLISH_SECRET>`

```json
{ "caption": "…", "carousel": ["data:image/png;base64,…", "… ×5"], "stories": ["…", "… ×2"] }
```

→ `{ "ok": true, "carousel": "<media-id>", "stories": ["<id>","<id>"] }`

`GET /health` — liveness + whether dry-run is on.

## Security notes

- The token and secret live only in env vars here — never commit a real `.env`.
- Set `ALLOW_ORIGIN` to your PWA origin so only it can call the API.
- Uploaded images are written to a temp dir and deleted ~60s after publish.
