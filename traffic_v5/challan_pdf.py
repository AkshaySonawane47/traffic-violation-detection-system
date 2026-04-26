"""
challan_pdf.py
==============
Generates a professional A4 Traffic E-Challan PDF.
Uses fpdf2 (FPDF class) — no external fonts required.

Call:
    generate_challan(challan_id, plate, violation, owner,
                     img_path, date_str, time_str)
"""

from fpdf import FPDF
from datetime import datetime
import os

try:
    from config.settings import CHALLANS_DIR, FINE_NO_HELMET, FINE_TRIPLE_RIDING, FINE_OVERSPEED
except ImportError:
    CHALLANS_DIR       = "challans"
    FINE_NO_HELMET     = 1000
    FINE_TRIPLE_RIDING = 1000
    FINE_OVERSPEED     = 2000

os.makedirs(CHALLANS_DIR, exist_ok=True)

FINES = {
    "No Helmet":                                FINE_NO_HELMET,
    "Triple Riding":                            FINE_TRIPLE_RIDING,
    "No Helmet + Triple Riding":                FINE_NO_HELMET + FINE_TRIPLE_RIDING,
    "No Helmet + Overspeed":                    FINE_NO_HELMET + FINE_OVERSPEED,
    "Triple Riding + Overspeed":                FINE_TRIPLE_RIDING + FINE_OVERSPEED,
    "No Helmet + Triple Riding + Overspeed":    FINE_NO_HELMET + FINE_TRIPLE_RIDING + FINE_OVERSPEED,
    "Overspeed":                                FINE_OVERSPEED,
}

RULES = {
    "No Helmet":     "MV Act Sec.129 — Helmet is mandatory for all two-wheeler riders",
    "Triple Riding": "MV Act Sec.128 — Maximum 2 persons allowed on a two-wheeler",
    "Overspeed":     "MV Act Sec.183 — Exceeding the prescribed speed limit",
}


def get_fine(violation: str) -> int:
    """Return fine amount for a given violation string."""
    clean = violation.strip()
    # Try exact match first
    for k, v in FINES.items():
        if clean == k:
            return v
    # Partial sum
    total = 0
    if "No Helmet"     in violation: total += FINE_NO_HELMET
    if "Triple Riding" in violation: total += FINE_TRIPLE_RIDING
    if "Overspeed"     in violation: total += FINE_OVERSPEED
    return total if total else FINE_NO_HELMET


# ──────────────────────────────────────────────────────────────
#  HELPERS
# ──────────────────────────────────────────────────────────────
def _header_fill(pdf, r, g, b):
    pdf.set_fill_color(r, g, b)

def _row_box(pdf, x, y, w, h, fill_rgb=(245, 245, 245)):
    pdf.set_fill_color(*fill_rgb)
    pdf.set_draw_color(200, 200, 200)
    pdf.rect(x, y, w, h, 'FD')

def _label_value(pdf, x, y, w, label, value, fill_rgb=(245, 245, 245)):
    _row_box(pdf, x, y, w, 10, fill_rgb)
    pdf.set_font("Helvetica", "B", 10)
    pdf.set_text_color(60, 60, 60)
    pdf.set_xy(x + 2, y + 1.5)
    pdf.cell(55, 7, label + ":")
    pdf.set_font("Helvetica", "", 10)
    pdf.set_text_color(0, 0, 0)
    pdf.set_xy(x + 58, y + 1.5)
    pdf.cell(w - 60, 7, str(value)[:60])


# ──────────────────────────────────────────────────────────────
#  MAIN CHALLAN GENERATOR
# ──────────────────────────────────────────────────────────────
def generate_challan(challan_id, plate, violation, owner,
                     img_path, date_str, time_str):
    """
    Generate a professional PDF challan and save to challans/ folder.

    Parameters
    ----------
    challan_id : str  — unique ID (e.g. 'EC202504250003')
    plate      : str  — number plate
    violation  : str  — violation description
    owner      : dict — owner info dict
    img_path   : str  — evidence image path (embedded in PDF if exists)
    date_str   : str  — 'DD-MM-YYYY'
    time_str   : str  — 'HH:MM:SS'

    Returns
    -------
    str — path to saved PDF
    """
    fine = get_fine(violation)
    pdf  = FPDF()
    pdf.set_auto_page_break(auto=False)
    pdf.add_page()

    # ── HEADER BANNER ──────────────────────────────────────────
    pdf.set_fill_color(21, 67, 107)
    pdf.rect(0, 0, 210, 46, 'F')

    pdf.set_text_color(255, 255, 255)
    pdf.set_font("Helvetica", "B", 24)
    pdf.set_xy(0, 8)
    pdf.cell(210, 12, "TRAFFIC E-CHALLAN", align="C")

    pdf.set_font("Helvetica", "", 11)
    pdf.set_xy(0, 22)
    pdf.cell(210, 8, "AI-Based Automated Traffic Violation Detection System", align="C")

    pdf.set_font("Helvetica", "I", 9)
    pdf.set_xy(0, 32)
    pdf.cell(210, 8, "Traffic Police Department  |  Government of India", align="C")

    # ── CHALLAN ID STRIP ───────────────────────────────────────
    pdf.set_text_color(0, 0, 0)
    pdf.set_fill_color(255, 242, 204)
    pdf.set_draw_color(192, 0, 0)
    pdf.rect(10, 50, 190, 14, 'FD')

    pdf.set_font("Helvetica", "B", 11)
    pdf.set_text_color(192, 0, 0)
    pdf.set_xy(14, 53)
    pdf.cell(90, 8, f"Challan ID: {challan_id}")

    pdf.set_text_color(40, 40, 40)
    pdf.set_font("Helvetica", "", 10)
    pdf.set_xy(105, 53)
    pdf.cell(93, 8, f"Date: {date_str}   Time: {time_str}", align="R")

    # ── VEHICLE & OWNER SECTION ────────────────────────────────
    y = 70
    pdf.set_fill_color(21, 67, 107)
    pdf.set_text_color(255, 255, 255)
    pdf.set_font("Helvetica", "B", 11)
    pdf.rect(10, y, 190, 9, 'F')
    pdf.set_xy(13, y + 1)
    pdf.cell(185, 7, "  VEHICLE & OWNER DETAILS")
    y += 11

    owner_rows = [
        ("Number Plate", plate),
        ("Owner Name",   owner.get("Owner Name", "UNKNOWN")),
        ("Phone",        owner.get("Phone", "N/A")),
        ("Email",        owner.get("Email", "N/A")),
        ("Address",      str(owner.get("Address", "N/A")) + ", " +
                         str(owner.get("City", "")) + ", " +
                         str(owner.get("State", ""))),
    ]
    for label, val in owner_rows:
        _label_value(pdf, 10, y, 190, label, val)
        y += 11

    # ── VIOLATION SECTION ──────────────────────────────────────
    y += 4
    pdf.set_fill_color(180, 0, 0)
    pdf.set_text_color(255, 255, 255)
    pdf.set_font("Helvetica", "B", 11)
    pdf.rect(10, y, 190, 9, 'F')
    pdf.set_xy(13, y + 1)
    pdf.cell(185, 7, "  VIOLATION DETAILS")
    y += 11

    # Violation type row (highlighted)
    pdf.set_fill_color(252, 228, 214)
    pdf.set_draw_color(200, 200, 200)
    pdf.rect(10, y, 190, 11, 'FD')
    pdf.set_font("Helvetica", "B", 11)
    pdf.set_text_color(180, 0, 0)
    pdf.set_xy(13, y + 2)
    pdf.cell(55, 7, "Violation:")
    pdf.set_font("Helvetica", "B", 11)
    pdf.set_text_color(0, 0, 0)
    pdf.set_xy(70, y + 2)
    pdf.cell(127, 7, violation[:60])
    y += 13

    # Applicable rules
    parts = [p.strip() for p in violation.replace(" [UNREGISTERED]","").split("+")]
    for part in parts:
        # Find matching rule
        rule = "Motor Vehicles Act violation"
        for k, r in RULES.items():
            if k in part:
                rule = r
                break
        pdf.set_font("Helvetica", "I", 9)
        pdf.set_text_color(80, 80, 80)
        pdf.set_xy(13, y)
        pdf.cell(185, 6, f"  \u2022  {rule}")
        y += 7

    # Evidence image filename
    y += 3
    _label_value(pdf, 10, y, 190, "Evidence File",
                 os.path.basename(img_path) if img_path else "N/A",
                 (240, 240, 240))
    y += 13

    # ── EVIDENCE IMAGE (embedded) ──────────────────────────────
    if img_path and os.path.exists(img_path):
        try:
            # Try to embed image — max 80×60mm
            img_x = 10
            img_w = 80
            img_h = 55
            if y + img_h > 240:
                y = 240 - img_h
            pdf.set_draw_color(150, 150, 150)
            pdf.rect(img_x - 1, y - 1, img_w + 2, img_h + 2, 'D')
            pdf.image(img_path, img_x, y, img_w, img_h)

            # Caption next to image
            pdf.set_font("Helvetica", "I", 8)
            pdf.set_text_color(80, 80, 80)
            pdf.set_xy(img_x + img_w + 5, y + 4)
            pdf.multi_cell(100, 5,
                f"Evidence photograph captured at time of\n"
                f"violation. Plate: {plate}\n"
                f"Date: {date_str}  Time: {time_str}\n\n"
                f"This image is computer-generated evidence\n"
                f"from the AI Traffic Detection System.")
            y += img_h + 6
        except Exception:
            pass   # skip image if it can't be embedded

    # ── FINE AMOUNT BOX ────────────────────────────────────────
    if y > 238:
        y = 238
    pdf.set_fill_color(21, 67, 107)
    pdf.set_text_color(255, 255, 255)
    pdf.set_font("Helvetica", "B", 14)
    pdf.rect(10, y, 190, 14, 'F')
    pdf.set_xy(14, y + 3)
    pdf.cell(90, 8, "  TOTAL FINE AMOUNT:")
    pdf.set_xy(105, y + 3)
    pdf.cell(93, 8, f"Rs. {fine:,}/-", align="R")
    y += 16

    # Payment note
    pdf.set_text_color(180, 0, 0)
    pdf.set_font("Helvetica", "B", 9)
    pdf.set_xy(10, y)
    pdf.cell(190, 6, "Pay within 30 days to avoid legal action & penalty doubling.", align="C")
    y += 7

    pdf.set_text_color(60, 60, 60)
    pdf.set_font("Helvetica", "", 9)
    pdf.set_xy(10, y)
    pdf.cell(190, 5, "Pay at: parivahan.gov.in  |  mParivahan App  |  Nearest Traffic Office",
             align="C")

    # ── FOOTER ─────────────────────────────────────────────────
    pdf.set_fill_color(210, 210, 210)
    pdf.rect(0, 272, 210, 26, 'F')
    pdf.set_text_color(80, 80, 80)
    pdf.set_font("Helvetica", "I", 8)
    pdf.set_xy(0, 275)
    pdf.cell(210, 5, "This is a computer-generated E-Challan. Physical signature is not required.", align="C")
    pdf.set_xy(0, 281)
    pdf.cell(210, 5, "Disputes: traffic.complaints@police.gov.in  |  Helpline: 1095", align="C")
    pdf.set_xy(0, 287)
    pdf.cell(210, 5,
             f"Generated: {datetime.now().strftime('%d-%m-%Y %H:%M:%S')}  |  "
             f"System: AI Traffic Violation Detection System v5", align="C")

    # ── SAVE ───────────────────────────────────────────────────
    safe_plate = plate.replace(" ", "").replace("/", "")
    fname      = os.path.join(CHALLANS_DIR, f"{challan_id}_{safe_plate}.pdf")
    pdf.output(fname)
    print(f"[PDF] Saved: {fname}")
    return fname
