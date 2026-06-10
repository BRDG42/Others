#!/usr/bin/env bash
#
# download_and_convert.sh
# ------------------------------------------------------------------
# Downloads every Abu Dhabi Official Gazette PDF listed in
# gazette_urls.txt and converts each one to Markdown with markitdown.
# Scanned issues (mostly 2009-2017) that yield little/no text are
# automatically OCR'd in Arabic+English with ocrmypdf and re-converted.
#
# Source page: https://www.abudhabi.gov.ae/ar/policies-and-legislations
#
# USAGE:
#   chmod +x download_and_convert.sh
#   ./download_and_convert.sh
#
# REQUIREMENTS:
#   - bash, curl
#   - markitdown          ->  pip install 'markitdown[all]'
#   - ocrmypdf + tesseract-ocr-ara (for scanned issues)
#         Debian/Ubuntu:  apt-get install ocrmypdf tesseract-ocr-ara
#
# Safe to re-run: already-downloaded PDFs and already-converted,
# non-empty .md files are skipped.
# ------------------------------------------------------------------

set -uo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
URL_FILE="${SCRIPT_DIR}/gazette_urls.txt"
PDF_DIR="${SCRIPT_DIR}/pdf"
MD_DIR="${SCRIPT_DIR}/markdown"
LOG="${SCRIPT_DIR}/run.log"

# Word count at or below which a conversion is treated as "scanned".
MIN_WORDS="${MIN_WORDS:-20}"

mkdir -p "$PDF_DIR" "$MD_DIR"
: > "$LOG"

if ! command -v markitdown >/dev/null 2>&1; then
  echo "ERROR: markitdown not found. Install with:  pip install 'markitdown[all]'" >&2
  exit 1
fi

HAVE_OCR=1
if ! command -v ocrmypdf >/dev/null 2>&1; then
  HAVE_OCR=0
  echo "WARNING: ocrmypdf not found; scanned issues will stay empty." | tee -a "$LOG"
fi

words() { wc -w < "$1" 2>/dev/null || echo 0; }

TOTAL=$(grep -cE '^[0-9]{4}_' "$URL_FILE")
echo "Found $TOTAL gazette issues to process." | tee -a "$LOG"

n=0
grep -E '^[0-9]{4}_' "$URL_FILE" | while read -r name url; do
  n=$((n+1))
  pdf="${PDF_DIR}/${name}.pdf"
  ocr="${PDF_DIR}/${name}_ocr.pdf"
  md="${MD_DIR}/${name}.md"

  printf '[%d/%d] %s\n' "$n" "$TOTAL" "$name" | tee -a "$LOG"

  # ---- skip if already converted to non-trivial markdown ----
  if [[ -s "$md" ]] && [[ $(words "$md") -gt "$MIN_WORDS" ]]; then
    echo "    md: already converted ($(words "$md") words), skipping" | tee -a "$LOG"
    continue
  fi

  # ---- download (skip if already a valid PDF) ----
  if [[ -f "$pdf" ]] && head -c4 "$pdf" | grep -q '%PDF'; then
    echo "    pdf: already present, skipping download" | tee -a "$LOG"
  else
    curl -sSL --fail --retry 3 --retry-delay 2 --max-time 600 \
         -A "Mozilla/5.0 (gazette-archiver)" \
         -o "$pdf" "$url"
    if [[ $? -ne 0 ]] || ! head -c4 "$pdf" | grep -q '%PDF'; then
      echo "    DOWNLOAD FAILED" | tee -a "$LOG"
      rm -f "$pdf"
      continue
    fi
    echo "    downloaded $(du -h "$pdf" | cut -f1)" | tee -a "$LOG"
  fi

  # ---- first pass: convert the original PDF ----
  markitdown "$pdf" -o "$md" 2>>"$LOG"
  w=$(words "$md")

  # ---- second pass: OCR if little/no text was extracted ----
  if [[ "$w" -le "$MIN_WORDS" ]]; then
    if [[ "$HAVE_OCR" -eq 1 ]]; then
      echo "    only $w words -> scanned; running OCR (ara+eng)..." | tee -a "$LOG"
      if [[ ! -f "$ocr" ]]; then
        ocrmypdf -l ara+eng --skip-text --quiet "$pdf" "$ocr" >>"$LOG" 2>&1 || \
          ocrmypdf -l ara+eng --force-ocr --quiet "$pdf" "$ocr" >>"$LOG" 2>&1 || true
      fi
      if [[ -f "$ocr" ]] && head -c4 "$ocr" | grep -q '%PDF'; then
        markitdown "$ocr" -o "$md" 2>>"$LOG"
        w=$(words "$md")
        echo "    after OCR: $w words" | tee -a "$LOG"
      else
        echo "    OCR FAILED" | tee -a "$LOG"
      fi
    fi
  fi

  if [[ "$w" -gt "$MIN_WORDS" ]]; then
    echo "    converted -> ${md} ($w words)" | tee -a "$LOG"
  else
    echo "    WARNING: still little/no text after processing ($w words)." | tee -a "$LOG"
  fi
done

echo
echo "Done. PDFs in:     $PDF_DIR"
echo "      Markdown in: $MD_DIR"
echo "      Full log:    $LOG"
