# LRCD — Missing Instruments: Sourcing Status

> **Updated:** 2026-06-11  
> **Scope:** the 6 instruments flagged 🔴 Missing in `LRCD_Instrument_Index.xlsx`.  
> **Method:** searched the 209-issue Abu Dhabi Gazette markdown corpus (2009–2026) + public sources (abudhabi.gov.ae, dct.gov.ae, uaelegislation.gov.ae, web).  
> Drop this file into the project to update the index.

## Result summary

| Ref | Instrument | Year | New status | Where it is now |
|---|---|---|---|---|
| **L-04** | Law 31/2019 — Alcoholic Beverages | 2019 | ✅ **RESOLVED** | Full text recovered → `instruments/L-04_Law_31_2019_Alcoholic_Beverages.md` (from Gazette 2020 Issue 7) |
| **MAN-05** | Tour Guide Licensing Standards | 2019 | 🟡 **PARTIAL** | DCT Circular 6/2023 downloaded → `instruments/MAN-05_Circular_6_2023_TourGuides.*`; full standards on training portal (login) |
| **L-02** | Law 13/2006 — Control of Tourist Establishments | 2006 | ⛔ **Not public** | Pre-2009 local law; only *referenced* in gazette preambles (evidence below) |
| **L-01** | Law 7/2004 — Tourism Establishments | 2004 | ⛔ **Not public** | Pre-2009 local law; not online anywhere found |
| **EC-01** | EC Resolution 16/2005 — Hotel Classification | 2005 | ⛔ **Not public** | Pre-2009; implemented by Hotel Classification Manual you already hold (MAN-04) |
| **EC-02** | EC Resolution 17/2005 — Hotel Classification (suppl.) | 2005 | ⛔ **Not public** | Pre-2009; implemented by Hotel Apartments Manual you already hold (MAN-04b) |

**Net:** 1 fully recovered, 1 partially sourced, 4 confirmed unavailable from public sources (pre-2009 local Abu Dhabi legislation — predates the online gazette archive, which starts 2009; not on the federal portal `uaelegislation.gov.ae`, which is federal-only).

---

## ✅ L-04 — Law No. (31) of 2019, Alcoholic Beverages
- **Status:** Full Arabic text recovered from the gazette corpus.
- **File:** `instruments/L-04_Law_31_2019_Alcoholic_Beverages.md`
- **Primary source:** Abu Dhabi Official Gazette **2020, Issue 7** (`markdown/2020_issue07.md`) — publishes the law *and* its Executive Regulation. It repeals Law 8/1976 on alcoholic beverages.
- **Gazette URL:** https://www.abudhabi.gov.ae/-/media/sites/adgov/gazettes/2020/ar/2020-e7-ar.ashx

## 🟡 MAN-05 — Tour Guide Licensing Standards
- **Status:** Best available public instrument downloaded; full internal standards live on the DCT training platform behind login.
- **Files:** `instruments/MAN-05_Circular_6_2023_TourGuides.pdf` (+ `.md`) — DCT Circular 6/2023 on utilisation of DCT-licensed tour guides.
- **Circular URL:** https://dct.gov.ae/DataFolder/Circulars/Circular%206_2023_Utilisation%20of%20Tourist%20Guides%20Licensed%20by%20the%20Department%20of%20Culture%20and%20Tourism%20%E2%80%93%20Abu%20Dhabi.pdf
- **Full programme / standards (web, login):** https://adtt.dct.gov.ae/ — 9-module Tourist Guide Training & Licensing Program (licence valid 2 yrs; fee AED 2,700 expat / free Emirati).
- **Action:** request the consolidated standards PDF from DCT Industry Development internally.

## ⛔ L-02 — Law No. (13) of 2006, Control of Tourist Establishments
- **Status:** Not available as a public PDF (pre-2009 local law). Existence and substance confirmed.
- **Confirmation (press):** Khaleej Times — "New law sets control measures for Abu Dhabi tourism facilities" (vests oversight in ADTA; no tourism business without an ADTA licence).
- **Referenced in our corpus** (preamble citations), e.g. Gazette 2020 Issue 7 & 2018 Issue 2:
  - `…• وعلى القانون رقم (13) لسنة 2006 بشأن الرقابة على المنشآت السياحية…`
- **Where to get full text:** DCT internal legal records, or ADJD (adjd.gov.ae). Not on the online gazette (starts 2009).

## ⛔ L-01 — Law No. (7) of 2004, Tourism Establishments
- **Status:** Not found in any public source. Pre-2009 local law; establishes the early ADTA tourism framework.
- **Where to get full text:** DCT internal legal records / ADJD. Not online.

## ⛔ EC-01 / EC-02 — Executive Council Resolutions 16 & 17 of 2005 (Hotel Classification)
- **Status:** Not available as standalone PDFs (pre-2009). However, their operative content survives in the **classification manuals you already hold**:
  - MAN-04: Hotel Classification System Manual — https://dct.gov.ae/DataFolder/Files/Hotel-Classification-System-Manual.pdf
  - MAN-04b: Hotel Apartments Classification System Manual — https://dct.gov.ae/DataFolder/Files/Hotel-Apartment-Classification-System-Manual.pdf
- **Where to get the resolutions themselves:** DCT internal legal records / ADJD.

---

## Files added to the project
| File | What |
|---|---|
| `instruments/L-04_Law_31_2019_Alcoholic_Beverages.md` | Full text of Law 31/2019 (recovered) |
| `instruments/MAN-05_Circular_6_2023_TourGuides.pdf` | DCT tour-guide circular (downloaded) |
| `instruments/MAN-05_Circular_6_2023_TourGuides.md` | Markdown of the above |
| `MISSING_INSTRUMENTS_STATUS.md` | This status report |