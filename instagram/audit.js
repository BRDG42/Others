#!/usr/bin/env node
// Content audit: pulls your existing Instagram posts via the Graph API and
// prints an analysis (cadence, formats, engagement, hashtags, top/bottom posts).
// Optionally exports the raw data so it can be reviewed in detail.
//
// Usage:
//   node instagram/audit.js                 # print summary to console
//   node instagram/audit.js --json out.json # also write raw posts to a file
//   node instagram/audit.js --limit 100     # how many recent posts to pull (default 50)
//
// Requires IG_USER_ID and IG_ACCESS_TOKEN. Reads only — never posts.
// The export contains captions + public metrics only (no tokens/secrets), so it
// is safe to share for review.

const fs = require('fs');
const { requireEnv, API_VERSION } = require('./lib');

const FIELDS = [
  'id', 'caption', 'media_type', 'media_product_type',
  'permalink', 'timestamp', 'like_count', 'comments_count',
].join(',');

function arg(name, fallback) {
  const i = process.argv.indexOf(name);
  return i !== -1 && process.argv[i + 1] ? process.argv[i + 1] : fallback;
}

async function fetchAllMedia(limit) {
  const { userId, token } = requireEnv();
  const posts = [];
  let url = `https://graph.facebook.com/${API_VERSION}/${userId}/media` +
    `?fields=${FIELDS}&limit=50&access_token=${encodeURIComponent(token)}`;

  while (url && posts.length < limit) {
    const res = await fetch(url);
    const json = await res.json();
    if (json.error) throw new Error(`Graph API: ${json.error.message}`);
    posts.push(...(json.data || []));
    url = json.paging && json.paging.next ? json.paging.next : null;
  }
  return posts.slice(0, limit);
}

const hashtagsOf = (caption = '') => (caption.match(/#[\w]+/g) || []).map((h) => h.toLowerCase());
const fmtDate = (ts) => new Date(ts).toISOString().slice(0, 10);

function summarize(posts) {
  if (posts.length === 0) return console.log('No posts found on this account.');

  const sorted = [...posts].sort((a, b) => new Date(a.timestamp) - new Date(b.timestamp));
  const first = sorted[0].timestamp;
  const last = sorted[sorted.length - 1].timestamp;
  const days = Math.max(1, (new Date(last) - new Date(first)) / 86400000);

  // Format breakdown
  const byType = {};
  for (const p of posts) {
    const t = p.media_product_type === 'REELS' ? 'REEL' : p.media_type;
    byType[t] = (byType[t] || 0) + 1;
  }

  // Engagement
  const eng = posts.map((p) => ({
    ...p,
    likes: p.like_count || 0,
    comments: p.comments_count || 0,
    total: (p.like_count || 0) + (p.comments_count || 0),
  }));
  const avgLikes = Math.round(eng.reduce((s, p) => s + p.likes, 0) / eng.length);
  const avgComments = Math.round(eng.reduce((s, p) => s + p.comments, 0) / eng.length);
  const byEng = [...eng].sort((a, b) => b.total - a.total);

  // Hashtags
  const tagCounts = {};
  for (const p of posts) for (const h of hashtagsOf(p.caption)) tagCounts[h] = (tagCounts[h] || 0) + 1;
  const topTags = Object.entries(tagCounts).sort((a, b) => b[1] - a[1]).slice(0, 10);

  // Captions
  const capLens = posts.map((p) => (p.caption || '').length);
  const avgCap = Math.round(capLens.reduce((s, n) => s + n, 0) / capLens.length);
  const noCaption = posts.filter((p) => !(p.caption || '').trim()).length;

  const line = (s = '') => console.log(s);
  line('\n══════════════════════════════════════════════');
  line('  BRDG CONCEPT — CONTENT AUDIT');
  line('══════════════════════════════════════════════');
  line(`Posts analysed:   ${posts.length}`);
  line(`Date range:       ${fmtDate(first)} → ${fmtDate(last)}`);
  line(`Posting cadence:  ${(posts.length / (days / 7)).toFixed(1)} posts / week`);

  line('\n── Format mix ─────────────────────────────────');
  for (const [t, n] of Object.entries(byType).sort((a, b) => b[1] - a[1])) {
    line(`  ${t.padEnd(12)} ${n}  (${Math.round((n / posts.length) * 100)}%)`);
  }

  line('\n── Engagement ─────────────────────────────────');
  line(`  Avg likes:      ${avgLikes}`);
  line(`  Avg comments:   ${avgComments}`);

  line('\n── Top 5 posts ────────────────────────────────');
  for (const p of byEng.slice(0, 5)) {
    line(`  ${fmtDate(p.timestamp)}  ♥${String(p.likes).padStart(4)} 💬${String(p.comments).padStart(3)}  ${p.permalink}`);
  }
  line('\n── Bottom 3 posts ─────────────────────────────');
  for (const p of byEng.slice(-3)) {
    line(`  ${fmtDate(p.timestamp)}  ♥${String(p.likes).padStart(4)} 💬${String(p.comments).padStart(3)}  ${p.permalink}`);
  }

  line('\n── Hashtags ───────────────────────────────────');
  line(topTags.length ? topTags.map(([h, n]) => `  ${h} ×${n}`).join('\n') : '  (none used)');

  line('\n── Captions ───────────────────────────────────');
  line(`  Avg length:     ${avgCap} chars`);
  line(`  Posts w/o caption: ${noCaption}`);
  line('══════════════════════════════════════════════\n');
}

async function main() {
  const limit = parseInt(arg('--limit', '50'), 10);
  const jsonOut = arg('--json', null);
  try {
    const posts = await fetchAllMedia(limit);
    summarize(posts);
    if (jsonOut) {
      fs.writeFileSync(jsonOut, JSON.stringify(posts, null, 2));
      console.log(`Raw data written to ${jsonOut} (captions + public metrics only — safe to share).`);
    }
  } catch (err) {
    console.error(`❌ ${err.message}`);
    process.exit(1);
  }
}

main();
