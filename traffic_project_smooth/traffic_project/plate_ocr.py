"""
plate_ocr.py
Reads number plate text from a cropped image using EasyOCR.
Also does fuzzy matching against known plates from Excel.
"""

import cv2
import re
import numpy as np

# EasyOCR reader — loaded once (slow first time, fast after)
_reader = None

def _get_reader():
    global _reader
    if _reader is None:
        try:
            import easyocr
            print("[OCR] Loading EasyOCR (first time is slow)...")
            _reader = easyocr.Reader(['en'], gpu=False, verbose=False)
            print("[OCR] EasyOCR ready")
        except Exception as e:
            print(f"[OCR] EasyOCR not available: {e}")
            _reader = False
    return _reader


def preprocess_plate(img):
    """
    Enhance plate image for better OCR:
    1. Resize to standard size
    2. Grayscale
    3. Sharpen
    4. Threshold
    """
    if img is None or img.size == 0:
        return None

    # Resize — bigger = better OCR
    h, w = img.shape[:2]
    scale = max(1, 120 // max(h, 1))
    img = cv2.resize(img, (w*scale*2, h*scale*2),
                     interpolation=cv2.INTER_CUBIC)

    # Grayscale
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY) \
           if len(img.shape) == 3 else img

    # Sharpen
    kernel = np.array([[0,-1,0],[-1,5,-1],[0,-1,0]])
    gray = cv2.filter2D(gray, -1, kernel)

    # Adaptive threshold — handles different lighting
    thresh = cv2.adaptiveThreshold(
        gray, 255,
        cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
        cv2.THRESH_BINARY, 15, 4
    )
    return thresh


def clean_plate_text(text):
    """
    Clean OCR output:
    - Remove spaces
    - Uppercase
    - Fix common OCR errors (0→O, 1→I etc in letter positions)
    - Keep only alphanumeric
    """
    if not text:
        return ""
    # Remove everything except letters and digits
    text = re.sub(r'[^A-Za-z0-9]', '', text).upper()
    return text


def read_plate(plate_img):
    """
    Try to read plate text from image.
    Returns cleaned plate string or empty string.
    """
    reader = _get_reader()
    if not reader:
        return ""

    try:
        proc = preprocess_plate(plate_img)
        if proc is None:
            return ""

        # Read with EasyOCR
        results = reader.readtext(proc, detail=1, paragraph=False)

        if not results:
            # Try on original image too
            results = reader.readtext(plate_img, detail=1, paragraph=False)

        if not results:
            return ""

        # Pick result with highest confidence
        best = max(results, key=lambda r: r[2])
        text = clean_plate_text(best[1])
        conf = best[2]

        if conf > 0.3 and len(text) >= 4:
            print(f"[OCR] Read: '{text}'  confidence: {conf:.2f}")
            return text
        return ""

    except Exception as e:
        print(f"[OCR] Error: {e}")
        return ""


def similarity(a, b):
    """
    Calculate how similar two plate strings are.
    Uses character matching score.
    Returns 0.0 to 1.0
    """
    a = clean_plate_text(a)
    b = clean_plate_text(b)
    if not a or not b:
        return 0.0

    # Count matching characters at same position
    min_len = min(len(a), len(b))
    max_len = max(len(a), len(b))
    if max_len == 0:
        return 0.0

    matches = sum(1 for i in range(min_len) if a[i] == b[i])

    # Also count characters in common (regardless of position)
    common = sum(min(a.count(c), b.count(c)) for c in set(a))

    score = (matches * 2 + common) / (max_len * 3)
    return score


def best_match_plate(ocr_text, known_plates, threshold=0.45):
    """
    Given OCR text, find the best matching plate from known_plates list.
    Returns matched plate string or None if no good match found.

    threshold: 0.0-1.0, lower = more lenient matching
    """
    if not ocr_text or not known_plates:
        return None

    ocr_clean = clean_plate_text(ocr_text)
    if not ocr_clean:
        return None

    scores = []
    for plate in known_plates:
        s = similarity(ocr_clean, plate)
        scores.append((s, plate))

    scores.sort(reverse=True)
    best_score, best_plate = scores[0]

    print(f"[MATCH] OCR='{ocr_clean}' → Best='{best_plate}' score={best_score:.2f}")

    if best_score >= threshold:
        return best_plate

    return None
