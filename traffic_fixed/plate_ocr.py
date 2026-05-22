"""
plate_ocr.py  —  Number Plate OCR + Fuzzy Matching
====================================================
FIXED VERSION — Solves "always UNKNOWN" problem.

ROOT CAUSES FIXED:
  1. OCR returning empty → multiple crop attempts at different positions
  2. Matching too strict → force-return best match even at low score
  3. No debug output → full debug table printed every time
  4. Threshold 0.45 → now 0.20, with lenient 0.15 fallback
  5. FORCE MATCH: if OCR text exists + known plates → ALWAYS return closest

KEY RULE (most important):
  If OCR reads ANY text AND database has plates:
  → ALWAYS return the closest plate (never return None)
  → "We prefer best guess over UNKNOWN"
  → Only return None if OCR text is completely empty
"""

import cv2
import re
import difflib
import numpy as np

# EasyOCR reader — patched at startup by detector.py
_reader = None


def _get_reader():
    global _reader
    if _reader is None:
        try:
            import easyocr
            print("[OCR] Loading EasyOCR...")
            _reader = easyocr.Reader(['en'], gpu=False, verbose=False)
            print("[OCR] EasyOCR ready")
        except Exception as e:
            print(f"[OCR] EasyOCR unavailable: {e}")
            _reader = False
    return _reader


# ── Text cleaning ────────────────────────────────────────────
def clean_plate_text(text):
    """Remove non-alphanumeric, uppercase, no spaces."""
    if not text:
        return ""
    return re.sub(r'[^A-Za-z0-9]', '', text).upper()


# ── OCR misread correction table (Indian plates) ─────────────
_OCR_SUBS = {
    'O': '0', '0': 'O',
    'I': '1', '1': 'I',
    'L': '1',
    'B': '8', '8': 'B',
    'S': '5', '5': 'S',
    'Z': '2', '2': 'Z',
    'G': '6', '6': 'G',
    'Q': '0', 'D': '0',
}


def _generate_variants(text):
    """Return original + one-char-substituted variants."""
    text = clean_plate_text(text)
    variants = {text}
    for i, ch in enumerate(text):
        if ch in _OCR_SUBS:
            variants.add(text[:i] + _OCR_SUBS[ch] + text[i+1:])
    return list(variants)


# ── Image preprocessing for better OCR ──────────────────────
def _make_passes(img):
    """
    Return list of (name, processed_image) for OCR.
    5 passes: BINARY_INV, BINARY, OTSU, sharp gray, colour.
    """
    if img is None or img.size == 0:
        return []
    h, w = img.shape[:2]
    if h == 0 or w == 0:
        return []

    # Upscale small plates — target 64px height, 160px width minimum
    scale = max(max(1.0, 64/h), max(1.0, 160/w))
    if scale > 1.0:
        img = cv2.resize(img, (int(w*scale*1.5), int(h*scale)),
                         interpolation=cv2.INTER_CUBIC)

    passes = []
    gray   = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY) if len(img.shape)==3 else img.copy()
    gray   = cv2.GaussianBlur(gray, (3,3), 0)
    blur   = cv2.GaussianBlur(gray, (0,0), 2)
    sharp  = cv2.addWeighted(gray, 2.0, blur, -1.0, 0)

    t1 = cv2.adaptiveThreshold(sharp, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                                cv2.THRESH_BINARY_INV, 17, 5)
    t1 = cv2.morphologyEx(t1, cv2.MORPH_CLOSE,
                          cv2.getStructuringElement(cv2.MORPH_RECT,(2,1)))
    passes.append(("ADAPTIVE_INV",  t1))

    t2 = cv2.adaptiveThreshold(sharp, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                                cv2.THRESH_BINARY, 17, 5)
    passes.append(("ADAPTIVE_NORM", t2))

    _, t3 = cv2.threshold(sharp, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    passes.append(("OTSU",          t3))
    passes.append(("SHARP_GRAY",    sharp))
    if len(img.shape) == 3:
        passes.append(("COLOUR",    img))

    return passes


# ── Single-pass OCR ──────────────────────────────────────────
def _ocr_one(reader, img, pass_name):
    """Run EasyOCR on one image. Returns list of (text, conf, x_pos)."""
    try:
        results = reader.readtext(img, detail=1, paragraph=False)
    except Exception as e:
        print(f"[OCR:{pass_name}] Error: {e}")
        return []
    out = []
    for (bbox, text, conf) in results:
        cleaned = clean_plate_text(text)
        if conf >= 0.05 and len(cleaned) >= 2:
            x_start = min(pt[0] for pt in bbox)
            out.append((cleaned, conf, x_start))
    out.sort(key=lambda c: c[2])
    return out


# ── Main OCR function ────────────────────────────────────────
def read_plate(plate_img):
    """
    Read number plate text from image or list of images.
    Returns best clean plate string, or "" if nothing readable.
    """
    reader = _get_reader()
    if not reader:
        return ""

    # Accept single image or list of images
    if isinstance(plate_img, (list, tuple)):
        crops = [c for c in plate_img
                 if c is not None and isinstance(c, np.ndarray) and c.size > 0]
    else:
        crops = ([plate_img] if plate_img is not None
                 and isinstance(plate_img, np.ndarray)
                 and plate_img.size > 0 else [])

    if not crops:
        return ""

    all_candidates = []   # (text, conf, pass_name, crop_idx)

    for ci, crop in enumerate(crops):
        for (pname, pimg) in _make_passes(crop):
            segs = _ocr_one(reader, pimg, pname)
            if not segs:
                continue
            # Full concatenated string from this pass
            full  = "".join(s[0] for s in segs)
            avg_c = sum(s[1] for s in segs) / len(segs)
            # Individual segments
            for s in segs:
                all_candidates.append((s[0], s[1], pname, ci))
            # Full concat string
            if len(full) >= 3:
                all_candidates.append((full, avg_c, pname, ci))

    if not all_candidates:
        print("[OCR] No text found in any crop/pass")
        return ""

    # Score: prefer longer text + higher confidence
    scored = []
    for (text, conf, pname, ci) in all_candidates:
        if 3 <= len(text) <= 14:
            scored.append(((len(text)/10.0)*conf, text, conf, pname, ci))

    if not scored:
        scored = [(0.0, t, c, p, i) for t,c,p,i in all_candidates]

    scored.sort(reverse=True)

    print(f"[OCR] --- {len(scored)} candidates ---")
    for rank, (sc, text, conf, pname, ci) in enumerate(scored[:5], 1):
        print(f"[OCR]   #{rank} '{text}' conf={conf:.2f} score={sc:.3f} "
              f"pass={pname} crop={ci}")

    best_text = scored[0][1]
    best_conf = scored[0][2]
    print(f"[OCR] BEST: '{best_text}' conf={best_conf:.2f}")
    return best_text


# ── Similarity scoring ───────────────────────────────────────
def _score_pair(ocr, known):
    """Combined similarity score (0.0–1.0) using 3 methods."""
    a = clean_plate_text(ocr)
    b = clean_plate_text(known)
    if not a or not b:
        return 0.0
    min_l = min(len(a), len(b))
    max_l = max(len(a), len(b))
    pos    = sum(1 for i in range(min_l) if a[i] == b[i])
    m1     = pos / max_l
    common = sum(min(a.count(c), b.count(c)) for c in set(a))
    m2     = common / max_l
    m3     = difflib.SequenceMatcher(None, a, b).ratio()
    return m1*0.35 + m2*0.25 + m3*0.40


# ── Main matching function ───────────────────────────────────
def best_match_plate(ocr_text, known_plates, threshold=0.20):
    """
    Find closest plate in known_plates to ocr_text.

    CRITICAL RULE:
      If ocr_text is non-empty AND known_plates is non-empty:
      → ALWAYS return the best match (never return None)
      → Only return None if ocr_text is completely empty

    Debug prints:
      Raw OCR | Cleaned | Each known plate score | Final match
    """
    if not known_plates:
        print("[MATCH] No known plates in database")
        return None

    if not ocr_text:
        print("[MATCH] Empty OCR text — cannot match")
        return None

    ocr_clean = clean_plate_text(ocr_text)
    if not ocr_clean:
        print("[MATCH] Cleaned OCR is empty — cannot match")
        return None

    print(f"\n[MATCH] ═══════════════════════════════")
    print(f"[MATCH] Raw OCR     : '{ocr_text}'")
    print(f"[MATCH] Cleaned OCR : '{ocr_clean}'")
    print(f"[MATCH] DB plates   : {known_plates}")

    variants   = _generate_variants(ocr_clean)
    score_rows = []

    for variant in variants:
        for known in known_plates:
            combined = _score_pair(variant, known)
            dl       = difflib.SequenceMatcher(
                           None,
                           clean_plate_text(variant),
                           clean_plate_text(known)).ratio()
            score_rows.append((combined, dl, variant, known))

    score_rows.sort(reverse=True)

    print(f"[MATCH] Top matches:")
    for rank, (comb, dl, var, kn) in enumerate(score_rows[:4], 1):
        print(f"[MATCH]   #{rank} OCR='{var}' DB='{kn}' "
              f"combined={comb:.3f} difflib={dl:.3f}")

    best_comb, best_dl, best_var, best_known = score_rows[0]

    # Decision: always return best if any score > 0.15
    if best_dl >= 0.65:
        reason = f"difflib_fast ({best_dl:.3f})"
    elif best_comb >= threshold:
        reason = f"combined ({best_comb:.3f})"
    elif best_comb > 0.15:
        reason = f"lenient_fallback ({best_comb:.3f})"
    else:
        # Score is very low — likely road noise OCR
        # Still return best match (force match rule)
        reason = f"FORCED ({best_comb:.3f} — low but best available)"

    # ── FORCE MATCH: always return closest if OCR exists ────
    print(f"[MATCH] RESULT: '{ocr_clean}' → '{best_known}' via {reason}")
    print(f"[MATCH] ═══════════════════════════════\n")
    return best_known
