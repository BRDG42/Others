#!/usr/bin/env bash
# Force-OCR the "thin" issues (markdown that extracted little text) and keep
# the OCR output only if it is substantially richer than the original.
set -uo pipefail
cd "$(dirname "${BASH_SOURCE[0]}")"

LOG="reocr.log"; : > "$LOG"
words() { wc -w < "$1" 2>/dev/null || echo 0; }

# Issues to reprocess (under ~300 words on first pass).
NAMES="2022_issue04 2022_issue11 2019_issue06 2019_issue08 2022_issue10 \
2021_issue07 2026_issue01 2018_issue12 2025_issue07 2019_issue12 2023_issue02 \
2020_issue01 2018_issue10 2019_issue02 2024_issue04 2023_issue06 2025_issue03 \
2022_issue02 2024_issue02 2025_issue01 2021_issue11"

for name in $NAMES; do
  pdf="pdf/${name}.pdf"; md="markdown/${name}.md"; ocr="pdf/${name}_focr.pdf"; tmp="markdown/${name}.reocr.md"
  before=$(words "$md")
  printf '%s: before=%s ... ' "$name" "$before" | tee -a "$LOG"
  if [[ ! -f "$pdf" ]]; then echo "no pdf, skip" | tee -a "$LOG"; continue; fi
  ocrmypdf -l ara+eng --force-ocr --quiet "$pdf" "$ocr" >>"$LOG" 2>&1 || { echo "OCR FAILED" | tee -a "$LOG"; continue; }
  markitdown "$ocr" -o "$tmp" 2>>"$LOG"
  after=$(words "$tmp")
  # Replace only if OCR is meaningfully richer: >100 more words AND >1.5x.
  if [[ "$after" -gt $((before + 100)) ]] && [[ "$after" -gt $((before * 3 / 2)) ]]; then
    mv "$tmp" "$md"
    echo "REPLACED -> after=$after" | tee -a "$LOG"
  else
    rm -f "$tmp"
    echo "kept original (ocr=$after not better)" | tee -a "$LOG"
  fi
  rm -f "$ocr"
done
echo "Done." | tee -a "$LOG"
