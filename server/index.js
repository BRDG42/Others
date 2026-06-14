/*
 * BRDG · Photographer Spotlight — Instagram publisher
 * ------------------------------------------------------------------
 * Receives the 7 rendered PNGs from the PWA and publishes them with the
 * Instagram Graph Content Publishing API:
 *   • the 5 square frames  → one carousel feed post (with caption)
 *   • the 2 story frames   → two stories
 *
 * Instagram fetches images by URL, so this service hosts the uploads at a
 * public /media/* route for the duration of the publish, then deletes them.
 *
 * The long-lived access token lives ONLY here (env), never in the browser.
 * Requests from the PWA are gated by a shared secret.
 *
 * Required env (see .env.example):
 *   IG_USER_ID        Instagram Business/Creator user id (numeric)
 *   IG_ACCESS_TOKEN   long-lived / system-user token with instagram_content_publish
 *   PUBLISH_SECRET    shared secret the PWA must send (x-publish-secret)
 *   PUBLIC_BASE_URL   this service's public https URL (e.g. https://xxx.onrender.com)
 * Optional:
 *   GRAPH_VERSION     default v21.0
 *   ALLOW_ORIGIN      CORS origin for the PWA (default *)
 *   IG_DRY_RUN        "1" → don't call Instagram, return fake ids (local testing)
 *   PORT              default 8080
 */
import express from 'express';
import cors from 'cors';
import crypto from 'node:crypto';
import fs from 'node:fs';
import os from 'node:os';
import path from 'node:path';

const {
  IG_USER_ID, IG_ACCESS_TOKEN, PUBLISH_SECRET, PUBLIC_BASE_URL,
  GRAPH_VERSION = 'v21.0', ALLOW_ORIGIN = '*', IG_DRY_RUN, PORT = 8080
} = process.env;

const DRY = IG_DRY_RUN === '1';
const GRAPH = `https://graph.facebook.com/${GRAPH_VERSION}`;
const MEDIA_DIR = fs.mkdtempSync(path.join(os.tmpdir(), 'brdg-media-'));

const app = express();
app.use(cors({ origin: ALLOW_ORIGIN }));
app.use(express.json({ limit: '40mb' }));
app.use('/media', express.static(MEDIA_DIR, { maxAge: '10m' }));

const sleep = (ms) => new Promise((r) => setTimeout(r, ms));

function requireSecret(req, res, next) {
  if (!PUBLISH_SECRET || req.header('x-publish-secret') !== PUBLISH_SECRET) {
    return res.status(401).json({ error: 'unauthorized' });
  }
  next();
}

// Persist a data: URL (or raw base64) to MEDIA_DIR, return its public URL.
function hostImage(dataUrl) {
  const b64 = String(dataUrl).replace(/^data:image\/\w+;base64,/, '');
  const name = crypto.randomBytes(12).toString('hex') + '.png';
  fs.writeFileSync(path.join(MEDIA_DIR, name), Buffer.from(b64, 'base64'));
  return { name, url: `${PUBLIC_BASE_URL}/media/${name}` };
}
function unlinkQuiet(name) { try { fs.unlinkSync(path.join(MEDIA_DIR, name)); } catch (e) {} }

async function graph(pathPart, params) {
  const body = new URLSearchParams({ ...params, access_token: IG_ACCESS_TOKEN });
  const res = await fetch(`${GRAPH}/${pathPart}`, { method: 'POST', body });
  const json = await res.json();
  if (!res.ok || json.error) {
    const msg = json.error ? `${json.error.message} (code ${json.error.code})` : `HTTP ${res.status}`;
    throw new Error(`Graph API: ${msg}`);
  }
  return json;
}

// A media container may process asynchronously; wait until it's publishable.
async function waitReady(creationId, tries = 30) {
  if (DRY) return;
  for (let i = 0; i < tries; i++) {
    const res = await fetch(`${GRAPH}/${creationId}?fields=status_code,status&access_token=${IG_ACCESS_TOKEN}`);
    const json = await res.json();
    if (json.status_code === 'FINISHED') return;
    if (json.status_code === 'ERROR') throw new Error(`Container ${creationId} failed: ${json.status || 'ERROR'}`);
    await sleep(2000);
  }
  throw new Error(`Container ${creationId} not ready in time`);
}

async function createContainer(params) {
  if (DRY) return 'dry_' + crypto.randomBytes(4).toString('hex');
  const json = await graph(`${IG_USER_ID}/media`, params);
  return json.id;
}
async function publishContainer(creationId) {
  if (DRY) return 'dry_media_' + crypto.randomBytes(4).toString('hex');
  const json = await graph(`${IG_USER_ID}/media_publish`, { creation_id: creationId });
  return json.id;
}

async function publishCarousel(imageUrls, caption) {
  const childIds = [];
  for (const url of imageUrls) {
    const id = await createContainer({ image_url: url, is_carousel_item: 'true' });
    await waitReady(id);
    childIds.push(id);
  }
  const containerId = await createContainer({ media_type: 'CAROUSEL', children: childIds.join(','), caption: caption || '' });
  await waitReady(containerId);
  return publishContainer(containerId);
}

async function publishStory(imageUrl) {
  const id = await createContainer({ image_url: imageUrl, media_type: 'STORIES' });
  await waitReady(id);
  return publishContainer(id);
}

app.get('/health', (req, res) => res.json({ ok: true, dryRun: DRY, graph: GRAPH_VERSION }));

app.post('/api/publish', requireSecret, async (req, res) => {
  const { caption = '', carousel = [], stories = [] } = req.body || {};
  if (!DRY && (!IG_USER_ID || !IG_ACCESS_TOKEN || !PUBLIC_BASE_URL)) {
    return res.status(500).json({ error: 'server not configured (IG_USER_ID / IG_ACCESS_TOKEN / PUBLIC_BASE_URL)' });
  }
  if (!Array.isArray(carousel) || carousel.length < 2 || carousel.length > 10) {
    return res.status(400).json({ error: 'carousel must have 2–10 images' });
  }

  const hosted = [];
  try {
    const carouselUrls = carousel.map((d) => { const h = hostImage(d); hosted.push(h.name); return h.url; });
    const storyUrls = stories.map((d) => { const h = hostImage(d); hosted.push(h.name); return h.url; });

    const result = { carousel: null, stories: [] };
    result.carousel = await publishCarousel(carouselUrls, caption);
    for (const url of storyUrls) result.stories.push(await publishStory(url));

    res.json({ ok: true, dryRun: DRY, ...result,
      permalink: result.carousel ? `https://www.instagram.com/` : null });
  } catch (err) {
    console.error('[publish]', err);
    res.status(502).json({ error: String(err.message || err) });
  } finally {
    // IG has fetched the images by now; clean up after a short grace period.
    setTimeout(() => hosted.forEach(unlinkQuiet), 60_000);
  }
});

app.listen(PORT, () => {
  console.log(`BRDG publisher on :${PORT}  dryRun=${DRY}  graph=${GRAPH_VERSION}`);
  if (DRY) console.log('DRY RUN — Instagram is not called; fake ids returned.');
});
