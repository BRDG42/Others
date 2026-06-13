#!/usr/bin/env node
// CLI for publishing a single post to Instagram immediately.
//
// Usage:
//   node instagram/publish.js image --url <public-image-url> --caption "text"
//   node instagram/publish.js reel  --url <public-video-url> --caption "text" [--cover <url>]
//
// Requires IG_USER_ID and IG_ACCESS_TOKEN in the environment.

const { publishImage, publishReel } = require('./lib');

function parseArgs(argv) {
  const [type, ...rest] = argv;
  const opts = {};
  for (let i = 0; i < rest.length; i += 2) {
    const key = rest[i].replace(/^--/, '');
    opts[key] = rest[i + 1];
  }
  return { type, opts };
}

async function main() {
  const { type, opts } = parseArgs(process.argv.slice(2));

  if (!type || !['image', 'reel'].includes(type)) {
    console.error('Usage: node instagram/publish.js <image|reel> --url <url> --caption "text" [--cover <url>]');
    process.exit(1);
  }
  if (!opts.url) {
    console.error('Error: --url is required (must be a public URL).');
    process.exit(1);
  }

  try {
    let result;
    if (type === 'image') {
      result = await publishImage({ imageUrl: opts.url, caption: opts.caption || '' });
    } else {
      result = await publishReel({ videoUrl: opts.url, caption: opts.caption || '', coverUrl: opts.cover });
    }
    console.log(`✅ Published ${type}. Media ID: ${result.id}`);
  } catch (err) {
    console.error(`❌ ${err.message}`);
    process.exit(1);
  }
}

main();
