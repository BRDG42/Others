# Instagram Auto-Publisher

Publish posts to an Instagram **Business/Creator** account via the official
**Instagram Graph API** — single images, Reels, and scheduled posts.

> **No passwords, ever.** This tool does not use your Instagram login. It uses a
> Graph API access token that **you** generate and control, passed in via
> environment variables / GitHub secrets. You can revoke it at any time in the
> Meta dashboard.

## What it does

| File | Purpose |
|------|---------|
| `lib.js` | Core Graph API helpers (image + reel publishing, container polling) |
| `publish.js` | CLI to publish one post right now |
| `scheduler.js` | Publishes due items from `queue.json` |
| `queue.example.json` | Sample queue format — copy to `queue.json` |
| `../.github/workflows/instagram-publish.yml` | Cron that runs the scheduler every 15 min |

Requires **Node.js 18+** (uses built-in `fetch`). No `npm install` needed.

---

## One-time setup

You need four things from Meta. This is required by Instagram — there is no way
around it for programmatic posting.

1. **Convert the account to Business or Creator**
   Instagram app → Settings → *Account type and tools* → Switch to Professional.

2. **Link it to a Facebook Page**
   In the same flow, connect the Instagram account to a Facebook Page you own.

3. **Create a Meta app**
   Go to <https://developers.facebook.com/apps> → *Create App* → add the
   **Instagram Graph API** product. Request the permissions:
   `instagram_basic`, `instagram_content_publish`, `pages_show_list`,
   `pages_read_engagement`.

4. **Get your IDs and a long-lived token**
   Use the [Graph API Explorer](https://developers.facebook.com/tools/explorer):
   - Generate a User token with the permissions above.
   - Exchange it for a **long-lived token** (~60 days) — see
     [Long-Lived Tokens](https://developers.facebook.com/docs/facebook-login/guides/access-tokens/get-long-lived).
   - Find your **Instagram Business account ID**:
     `GET /me/accounts` → pick your Page → `GET /{page-id}?fields=instagram_business_account`.

You now have:
- `IG_USER_ID` — the Instagram Business account ID (numeric)
- `IG_ACCESS_TOKEN` — the long-lived token

> **Token expiry:** long-lived tokens last ~60 days. Refresh before expiry, or
> set up [system-user tokens](https://developers.facebook.com/docs/marketing-api/system-users)
> for a non-expiring option.

---

## Media hosting requirement

The Graph API does **not** accept file uploads — it fetches media from a
**public URL** you provide (`image_url` / `video_url`). Host your media anywhere
publicly reachable (S3, Cloudinary, GitHub raw, a CDN) and pass the URL.

- Images: JPEG, ≤ 8 MB recommended.
- Reels: MP4/MOV, vertical 9:16, ≤ 100 MB / ~90s for reliable processing.

---

## Publish one post now

```bash
export IG_USER_ID=1784xxxxxxxxxxx
export IG_ACCESS_TOKEN=EAAG...your-long-lived-token

# Single image
node instagram/publish.js image \
  --url "https://your-host.com/photo.jpg" \
  --caption "Hello from the API 👋 #brdgconcept"

# Reel (polls until Instagram finishes processing, then publishes)
node instagram/publish.js reel \
  --url "https://your-host.com/video.mp4" \
  --caption "New drop 🎬" \
  --cover "https://your-host.com/cover.jpg"
```

---

## Scheduling

1. Copy the example queue and edit it:
   ```bash
   cp instagram/queue.example.json instagram/queue.json
   ```
2. Add entries with a future `publishAt` (ISO 8601, UTC recommended):
   ```json
   {
     "id": "2026-06-20-launch",
     "type": "image",
     "mediaUrl": "https://your-host.com/photo.jpg",
     "caption": "Launching today!",
     "publishAt": "2026-06-20T09:00:00Z",
     "status": "pending"
   }
   ```
3. Run the scheduler (publishes anything due, marks it `published`):
   ```bash
   node instagram/scheduler.js
   ```

### Automate with GitHub Actions

The workflow `.github/workflows/instagram-publish.yml` runs the scheduler every
15 minutes and commits the updated queue back.

Add your secrets once: repo **Settings → Secrets and variables → Actions → New
repository secret**:
- `IG_USER_ID`
- `IG_ACCESS_TOKEN`

Then commit entries to `queue.json` whenever you want to schedule a post. The
cron handles the rest. You can also trigger it manually from the **Actions** tab
(*Run workflow*).

> The cron granularity is 15 min, so a post goes out at the first cron tick
> **after** its `publishAt`.

---

## Limits & notes

- Instagram allows **25 API-published posts per 24 hours** per account.
- Carousels (multi-image) aren't included yet — ask if you want them added.
- Stories are **not** supported by the content-publishing API.
- If a publish fails, the queue entry is marked `failed` with the error message;
  fix the cause and reset `status` to `pending` to retry.
