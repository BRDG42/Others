# BRDG · Photographer Spotlight — template system

A locked, reusable template for the recurring Instagram series
**"BRDG · Photographer Spotlight."** Each run = one photographer. Drop 5 photos,
edit a little text, export 7 export-ready PNGs.

## Files

| File | Role |
| --- | --- |
| `BRDG Photographer Spotlight.dc.html` | The template — all 7 frames, locked identity, Tweaks panel, PNG export. |
| `image-slot.js` | The `<image-slot>` web component: drag-and-drop photo layers that remember what you drop and are **shared by id**. |
| `spotlight/` | The same template packaged as an installable, fully-offline phone app (PWA). |

## Install on your phone (PWA)

The `spotlight/` folder is a Progressive Web App — real Gotham + Caveat and the
export library are vendored locally, so it runs **fully offline** once installed.

A PWA only installs when served over **HTTPS**, so host it via **GitHub Pages**:

1. Merge to `main`, then on GitHub: **Settings → Pages → Source: Deploy from a
   branch → `main` / root**.
2. Open **`https://brdg42.github.io/others/spotlight/`** on your phone.
3. **Share → Add to Home Screen.** It launches fullscreen and works offline.

On the phone: tap a photo slot to pick from your library, edit the text in the
**Edit** sheet, then **Share / Save 7 frames** to hand the PNGs straight to the
iOS/Android share sheet (→ Instagram).

## Deliverables (per photographer)

- **Carousel — 1080 × 1080 × 5:** intro (Option A · Cinematic) + work 01–04.
- **Story — 1080 × 1920 × 2:** tall intro (swipe cue + coral footer band) + work 01.

The portrait (`personal-shot`) and `work-01` are **shared by id**, so they appear in
both the carousel and the story from a single upload. You only ever drop 5 photos.

## Use it

**Drag-drop route (quick one-off)**
1. Open `BRDG Photographer Spotlight.dc.html` in a browser.
2. Drop the portrait on **PERSONAL SHOT**, the four shots on **WORK 01–04**.
3. Fill the **Tweaks** panel: name · @handle · location · bio · edition no.
4. Click **Export all 7 PNGs** (or the per-frame **PNG** buttons).

**Claude route (hands-off + captioned)**
1. Copy the template to `Spotlight — <Name>.dc.html`.
2. Set each `<image-slot>`'s `src` to the uploaded path (`personal-shot`,
   `work-01`…`work-04`), `fit="cover"`.
3. Set the text props (`photographerName`, `handle`, `location`, `bio`, `edition`).
4. Export each frame at native resolution (the export step temporarily clears the
   preview `transform: scale()` so frames capture at native 1080).

## Locked identity — do not redesign

- **Colors:** coral `#D9543F` · ink `#141414` · paper `#F4F1EA` · white `#FFFFFF`.
- **Logo:** lowercase **`brdg`**, bold italic (Logo A). The retired top-right "BRDG"
  stamp is not used.
- **Type:** Gotham → fallback **Montserrat**. **Caveat** script on one word only:
  *"Spotlight."*
- Every frame keeps the **coral hairline frame** (inset ~28px), the **bottom scrim**,
  and the **`brdg` wordmark** — these make the series instantly recognizable.

## Notes

- Slots cache drops in `localStorage` (keyed by id). **Reset photos** clears them.
- Text is cached too, so a refresh keeps your edits. Clear it with
  `localStorage.removeItem('brdg-spotlight-text')`.
- Export uses html2canvas (loaded from CDN), so the browser needs network access.
