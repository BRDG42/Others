#!/usr/bin/env node
// Scheduler: publishes any queued posts whose `publishAt` time has passed.
// Designed to run on a cron (e.g. GitHub Actions every 15 min). After each run
// it rewrites the queue file, marking published items so they are not re-posted.
//
// Queue file: instagram/queue.json (array of entries). See queue.example.json.
// Each entry:
//   {
//     "id": "unique-string",
//     "type": "image" | "reel",
//     "mediaUrl": "https://.../public-media",
//     "caption": "text",
//     "coverUrl": "https://...",        // optional, reels only
//     "publishAt": "2026-06-20T09:00:00Z",
//     "status": "pending"                // managed by the scheduler
//   }
//
// Requires IG_USER_ID and IG_ACCESS_TOKEN in the environment.

const fs = require('fs');
const path = require('path');
const { publishImage, publishReel } = require('./lib');

const QUEUE_PATH = path.join(__dirname, 'queue.json');

function loadQueue() {
  if (!fs.existsSync(QUEUE_PATH)) {
    console.log('No queue.json found — nothing to do.');
    return null;
  }
  return JSON.parse(fs.readFileSync(QUEUE_PATH, 'utf8'));
}

function saveQueue(queue) {
  fs.writeFileSync(QUEUE_PATH, JSON.stringify(queue, null, 2) + '\n');
}

async function publishEntry(entry) {
  if (entry.type === 'image') {
    return publishImage({ imageUrl: entry.mediaUrl, caption: entry.caption || '' });
  }
  if (entry.type === 'reel') {
    return publishReel({ videoUrl: entry.mediaUrl, caption: entry.caption || '', coverUrl: entry.coverUrl });
  }
  throw new Error(`Unknown entry type: ${entry.type}`);
}

async function main() {
  const queue = loadQueue();
  if (!queue) return;

  const now = Date.now();
  let changed = false;

  for (const entry of queue) {
    if (entry.status === 'published' || entry.status === 'failed') continue;
    const due = new Date(entry.publishAt).getTime();
    if (Number.isNaN(due)) {
      console.warn(`⚠️  Skipping ${entry.id}: invalid publishAt "${entry.publishAt}"`);
      continue;
    }
    if (due > now) continue; // not yet due

    try {
      const result = await publishEntry(entry);
      entry.status = 'published';
      entry.publishedId = result.id;
      entry.publishedAt = new Date().toISOString();
      changed = true;
      console.log(`✅ Published ${entry.id} (${entry.type}) → media ${result.id}`);
    } catch (err) {
      entry.status = 'failed';
      entry.error = err.message;
      changed = true;
      console.error(`❌ Failed ${entry.id}: ${err.message}`);
    }
  }

  if (changed) {
    saveQueue(queue);
    console.log('Queue updated.');
  } else {
    console.log('Nothing due to publish.');
  }
}

main();
