# AI Traffic Violation Detection System — FINAL

## Quick Start
```bash
pip install -r requirements.txt
python create_owners.py          # create bike_owners.xlsx
python detector.py video2_without_helmet.mp4   # test no-helmet
python detector.py video_with_helmet.mp4       # test with helmet
python detector.py video2_without_helmet.mp4 --roi  # draw detection zone
```

## What Each File Does
| File | Purpose |
|---|---|
| detector.py | Main — YOLO + helmet + OCR + challan |
| plate_ocr.py | 4-pass OCR + 3-method fuzzy matching |
| tracker.py | Centroid tracker with velocity prediction |
| violation_log.py | Save to violations.xlsx |
| challan_pdf.py | Generate PDF challan |
| roi_selector.py | Draw detection polygon |
| config/settings.py | ALL tuneable parameters |

## What Was Fixed

### OCR → UNKNOWN problem
- Confidence threshold: 0.25 → **0.10** (catches blurry plates)
- Match threshold: 0.45 → **0.20** (catches partial reads)
- Added **OCR correction variants**: 0↔O, 1↔I, 8↔B, 5↔S etc.
- Added **difflib SequenceMatcher** as 3rd scoring method
- 4-pass preprocessing: adaptive-INV + OTSU + gray + colour

### Excel matching broken
- Switched from openpyxl cell-by-cell to **pandas** (dtype=str)
- All keys normalized: `strip().upper().replace(' ','')` 
- All values `str()`-cast (handles cells stored as int/float)

### Helmet false positives
- HEAD_FRACTION: 0.38 → **0.28** (only true forehead)
- Added **dark colour check**: V-mean < 75 → likely dark helmet → OK
- **Voting**: need BOTH skin AND face cascade to fire (was any one)
- Edge density check **removed** (fired on textured helmets)

### Yellow box on wrong object
- Yellow box now = **RIDER union box** (person detection)
- Cyan outline = bike YOLO box (separate layer)
- Green small box = number plate

### Plate drifts randomly
- Plate always searched relative to **BIKE box** (never person box)
- On persons-only path, plate search is skipped (no anchor)
- Fallback = deterministic `bike_bottom + 5px`

### Person-bike linking too strict
- X tolerance: bw*0.25 → **max(bw*0.5, 60px)**
- Y range: ±bh → **bike_top - bh*1.5 to bike_bottom + bh*0.5**
- Added condition 3: person bottom within 30px of bike bottom

## Tuning Guide
All in `config/settings.py`:

| Setting | Default | Effect |
|---|---|---|
| PLATE_MATCH_MIN | 0.20 | Lower = matches more plates from Excel |
| SKIN_THRESHOLD | 0.20 | Lower = more sensitive helmet detection |
| HEAD_FRACTION | 0.28 | Higher = bigger head region checked |
| YOLO_CONF | 0.25 | Lower = detects more bikes/persons |
| DETECT_EVERY | 3 | Lower = more detections (slower) |
| COOLDOWN_SEC | 10 | Lower = can re-flag same plate sooner |
