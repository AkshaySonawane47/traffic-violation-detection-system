"""
plate_ocr.py
============
Number plate OCR using EasyOCR + multi-pass preprocessing pipeline.
Also handles fuzzy plate matching against known plates from Excel.

Pipeline:
    raw crop → resize → grayscale → denoise → sharpen → threshold
             → EasyOCR → clean text → fuzzy match

Why EasyOCR?
  - Works without internet after first download
  - Handles blurry / low-res plates better than Tesseract
  - GPU=False ensures it works on any laptop
"""

import cv2
import re
import numpy as np

# EasyOCR reader — loaded ONCE at startup (first load is ~10 seconds)
_reader = None


def _get_reader():
    global _reader
    if _reader is None:
        try:
            import easyocr
            print("[OCR] Loading EasyOCR model (first time ~10 sec)...")
            _reader = easyocr.Reader(['en'], gpu=False, verbose=False)
            print("[OCR] EasyOCR ready")
        except Exception as e:
            print(f"[OCR] EasyOCR unavailable: {e}")
            _reader = False
    return _reader


# ──────────────────────────────────────────────────────────────
#  IMAGE PREPROCESSING PIPELINE
# ──────────────────────────────────────────────────────────────
def preprocess_plate(img):
    """
    Multi-step enhancement for plate OCR accuracy.

    Steps
    -----
    1. Upscale to standard height (better OCR on small crops)
    2. Grayscale conversion
    3. Gaussian denoise
    4. Unsharp mask sharpening
    5. Adaptive threshold (handles uneven lighting)
    6. Morphological closing (fills gaps in letters)
    """
    if img is None or img.size == 0:
        return None

    # Step 1: Upscale — target height 80px, scale proportionally
    h, w = img.shape[:2]
    if h < 80:
        scale = 80 / max(h, 1)
        img   = cv2.resize(img, (int(w * scale * 2), int(h * scale * 2)),
                           interpolation=cv2.INTER_CUBIC)

    # Step 2: Grayscale
    if len(img.shape) == 3:
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    else:
        gray = img.copy()

    # Step 3: Denoise
    gray = cv2.GaussianBlur(gray, (3, 3), 0)

    # Step 4: Unsharp mask sharpening
    blurred = cv2.GaussianBlur(gray, (0, 0), 3)
    gray    = cv2.addWeighted(gray, 1.5, blurred, -0.5, 0)

    # Step 5: Adaptive threshold
    thresh = cv2.adaptiveThreshold(
        gray, 255,
        cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
        cv2.THRESH_BINARY_INV, 19, 6
    )

    # Step 6: Morphological closing — connect broken letter strokes
    k      = cv2.getStructuringElement(cv2.MORPH_RECT, (2, 2))
    thresh = cv2.morphologyEx(thresh, cv2.MORPH_CLOSE, k)

    return thresh


# ──────────────────────────────────────────────────────────────
#  TEXT CLEANING
# ──────────────────────────────────────────────────────────────
def clean_plate_text(text):
    """
    Clean raw OCR output:
      - Remove all non-alphanumeric characters
      - Uppercase
      - Strip spaces
    Common OCR corrections are intentionally NOT applied here
    because they can corrupt valid plates (e.g. converting 0→O
    breaks plates that genuinely have '0').
    """
    if not text:
        return ""
    return re.sub(r'[^A-Za-z0-9]', '', text).upper()


# ──────────────────────────────────────────────────────────────
#  OCR ENTRY POINT
# ──────────────────────────────────────────────────────────────
def read_plate(plate_img):
    """
    Read number plate text from a cropped image.

    Runs two passes:
      Pass 1 — preprocessed (enhanced) image
      Pass 2 — original image (in case preprocessing hurts quality)

    Returns the best result (highest confidence, min 4 chars).
    """
    reader = _get_reader()
    if not reader:
        return ""

    results_all = []

    try:
        # Pass 1: preprocessed
        proc = preprocess_plate(plate_img)
        if proc is not None:
            r1 = reader.readtext(proc, detail=1, paragraph=False,
                                 allowlist='ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789')
            results_all.extend(r1)

        # Pass 2: original (grayscale)
        if len(plate_img.shape) == 3:
            gray_orig = cv2.cvtColor(plate_img, cv2.COLOR_BGR2GRAY)
        else:
            gray_orig = plate_img
        r2 = reader.readtext(gray_orig, detail=1, paragraph=False,
                             allowlist='ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789')
        results_all.extend(r2)

        if not results_all:
            return ""

        # Pick highest-confidence result with ≥4 chars
        candidates = [
            (clean_plate_text(r[1]), r[2])
            for r in results_all
            if r[2] > 0.25 and len(clean_plate_text(r[1])) >= 4
        ]
        if not candidates:
            return ""

        best_text, best_conf = max(candidates, key=lambda x: x[1])
        print(f"[OCR] '{best_text}'  conf={best_conf:.2f}")
        return best_text

    except Exception as e:
        print(f"[OCR] Error: {e}")
        return ""


# ──────────────────────────────────────────────────────────────
#  FUZZY PLATE MATCHING
# ──────────────────────────────────────────────────────────────
def similarity(a, b):
    """
    Compute similarity score between two plate strings.
    Combines positional character matching + set overlap.
    Returns 0.0–1.0.
    """
    a = clean_plate_text(a)
    b = clean_plate_text(b)
    if not a or not b:
        return 0.0

    min_len = min(len(a), len(b))
    max_len = max(len(a), len(b))
    if max_len == 0:
        return 0.0

    # Positional matches
    pos_matches = sum(1 for i in range(min_len) if a[i] == b[i])

    # Character frequency overlap
    common = sum(min(a.count(c), b.count(c)) for c in set(a))

    # Weighted score: position matters 2x more than set overlap
    score = (pos_matches * 2 + common) / (max_len * 3)
    return score


def best_match_plate(ocr_text, known_plates, threshold=0.45):
    """
    Find the best matching plate from known_plates list.
    Returns matched plate string or None if score < threshold.
    """
    if not ocr_text or not known_plates:
        return None

    ocr_clean = clean_plate_text(ocr_text)
    if not ocr_clean:
        return None

    scores = [(similarity(ocr_clean, p), p) for p in known_plates]
    scores.sort(reverse=True)
    best_score, best_plate = scores[0]

    print(f"[MATCH] OCR='{ocr_clean}' → Best='{best_plate}' score={best_score:.2f}")
    return best_plate if best_score >= threshold else None
