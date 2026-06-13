// Core Instagram Graph API helpers — no third-party dependencies (Node 18+).
//
// Auth model: this code NEVER touches an Instagram username/password. It uses
// the official Instagram Graph API, which requires:
//   - An Instagram Business or Creator account
//   - Linked to a Facebook Page
//   - A Meta app with the `instagram_content_publish` permission
//   - A long-lived access token (held by you, passed in via env vars)
//
// Required environment variables:
//   IG_USER_ID       Instagram Business account ID (numeric)
//   IG_ACCESS_TOKEN  Long-lived access token
// Optional:
//   IG_API_VERSION   Graph API version (default: v21.0)

const API_VERSION = process.env.IG_API_VERSION || 'v21.0';
const BASE = `https://graph.facebook.com/${API_VERSION}`;

function requireEnv() {
  const userId = process.env.IG_USER_ID;
  const token = process.env.IG_ACCESS_TOKEN;
  if (!userId || !token) {
    throw new Error(
      'Missing credentials. Set IG_USER_ID and IG_ACCESS_TOKEN environment variables. ' +
      'See instagram/README.md for how to obtain them.'
    );
  }
  return { userId, token };
}

async function graph(method, path, params) {
  const { token } = requireEnv();
  const url = new URL(`${BASE}/${path}`);
  const body = new URLSearchParams({ ...params, access_token: token });
  const opts = { method };
  if (method === 'GET') {
    for (const [k, v] of body) url.searchParams.set(k, v);
  } else {
    opts.body = body;
  }
  const res = await fetch(url, opts);
  const json = await res.json().catch(() => ({}));
  if (!res.ok || json.error) {
    const e = json.error || {};
    throw new Error(
      `Graph API ${method} ${path} failed: ${res.status} ${e.message || ''}` +
      (e.error_user_msg ? ` — ${e.error_user_msg}` : '')
    );
  }
  return json;
}

const sleep = (ms) => new Promise((r) => setTimeout(r, ms));

// Create + publish a single image post. `imageUrl` must be a public URL.
async function publishImage({ imageUrl, caption = '' }) {
  if (!imageUrl) throw new Error('imageUrl is required');
  const { userId } = requireEnv();
  const container = await graph('POST', `${userId}/media`, {
    image_url: imageUrl,
    caption,
  });
  return publishContainer(container.id);
}

// Create + publish a Reel. `videoUrl` must be a public URL. Reels are processed
// asynchronously, so we poll the container until it is FINISHED before publishing.
async function publishReel({ videoUrl, caption = '', coverUrl, shareToFeed = true, maxWaitMs = 5 * 60 * 1000 }) {
  if (!videoUrl) throw new Error('videoUrl is required');
  const { userId } = requireEnv();
  const params = {
    media_type: 'REELS',
    video_url: videoUrl,
    caption,
    share_to_feed: String(shareToFeed),
  };
  if (coverUrl) params.cover_url = coverUrl;

  const container = await graph('POST', `${userId}/media`, params);
  await waitForContainer(container.id, maxWaitMs);
  return publishContainer(container.id);
}

// Poll a media container until processing finishes (needed for video/Reels).
async function waitForContainer(creationId, maxWaitMs) {
  const start = Date.now();
  let delay = 3000;
  while (Date.now() - start < maxWaitMs) {
    const { status_code } = await graph('GET', creationId, { fields: 'status_code' });
    if (status_code === 'FINISHED') return;
    if (status_code === 'ERROR' || status_code === 'EXPIRED') {
      throw new Error(`Media processing ${status_code} for container ${creationId}`);
    }
    await sleep(delay);
    delay = Math.min(delay * 1.5, 15000);
  }
  throw new Error(`Timed out waiting for container ${creationId} to finish processing`);
}

async function publishContainer(creationId) {
  const { userId } = requireEnv();
  const published = await graph('POST', `${userId}/media_publish`, {
    creation_id: creationId,
  });
  return { id: published.id, creationId };
}

module.exports = { publishImage, publishReel, requireEnv, API_VERSION };
