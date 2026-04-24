"""
challan_pdf.py
Generates professional E-Challan PDF
"""

from fpdf import FPDF
from datetime import datetime
import os

os.makedirs("challans", exist_ok=True)

FINES = {
    "No Helmet":                                1000,
    "Triple Riding":                            1000,
    "No Helmet + Triple Riding":                2000,
    "No Helmet + Overspeed":                    3000,
    "Triple Riding + Overspeed":                3000,
    "No Helmet + Triple Riding + Overspeed":    4000,
    "Overspeed":                                2000,
}

def get_fine(violation):
    for k, v in FINES.items():
        if violation.strip() == k:
            return v
    # partial match
    total = 0
    if "No Helmet"     in violation: total += 1000
    if "Triple Riding" in violation: total += 1000
    if "Overspeed"     in violation: total += 2000
    return total if total else 1000


def generate_challan(challan_id, plate, violation, owner,
                     img_path, date_str, time_str):
    fine = get_fine(violation)
    pdf  = FPDF()
    pdf.add_page()

    # ── header ─────────────────────────────────────────
    pdf.set_fill_color(31, 78, 121)
    pdf.rect(0, 0, 210, 42, 'F')
    pdf.set_text_color(255,255,255)
    pdf.set_font("Helvetica","B", 22)
    pdf.set_xy(0, 7)
    pdf.cell(210, 10, "TRAFFIC E-CHALLAN", align="C")
    pdf.set_font("Helvetica","", 11)
    pdf.set_xy(0, 20)
    pdf.cell(210, 8,  "Automated Traffic Violation Detection System", align="C")
    pdf.set_font("Helvetica","", 9)
    pdf.set_xy(0, 30)
    pdf.cell(210, 8,  "Traffic Police | Government of India", align="C")

    # ── challan ID strip ────────────────────────────────
    pdf.set_text_color(0,0,0)
    pdf.set_fill_color(255,242,204)
    pdf.set_draw_color(192,0,0)
    pdf.rect(10, 47, 190, 14, 'FD')
    pdf.set_font("Helvetica","B",12)
    pdf.set_text_color(192,0,0)
    pdf.set_xy(13, 49); pdf.cell(90,8, f"Challan ID: {challan_id}")
    pdf.set_text_color(0,0,0)
    pdf.set_xy(105,49); pdf.cell(93,8, f"Date: {date_str}  |  Time: {time_str}", align="R")

    # ── owner section ───────────────────────────────────
    y = 68
    pdf.set_fill_color(31,78,121); pdf.set_text_color(255,255,255)
    pdf.set_font("Helvetica","B",12)
    pdf.set_xy(10, y); pdf.cell(190, 9, "  VEHICLE & OWNER DETAILS", fill=True)
    y += 12

    details = [
        ("Number Plate",  plate),
        ("Owner Name",    owner.get("Owner Name","UNKNOWN")),
        ("Phone",         owner.get("Phone","N/A")),
        ("Email",         owner.get("Email","N/A")),
        ("Address",       str(owner.get("Address","N/A")) + ", " +
                          str(owner.get("City","")) + ", " +
                          str(owner.get("State",""))),
    ]
    pdf.set_text_color(0,0,0)
    for label, val in details:
        pdf.set_fill_color(245,245,245)
        pdf.rect(10, y, 190, 10, 'FD')
        pdf.set_font("Helvetica","B",10); pdf.set_xy(12,y+1); pdf.cell(55,7,label+":")
        pdf.set_font("Helvetica","",10);  pdf.set_xy(68,y+1); pdf.cell(130,7,str(val))
        y += 11

    # ── violation section ───────────────────────────────
    y += 4
    pdf.set_fill_color(192,0,0); pdf.set_text_color(255,255,255)
    pdf.set_font("Helvetica","B",12)
    pdf.set_xy(10, y); pdf.cell(190, 9, "  VIOLATION DETAILS", fill=True)
    y += 12

    pdf.set_fill_color(252,228,214); pdf.set_text_color(0,0,0)
    pdf.rect(10, y, 190, 11, 'FD')
    pdf.set_font("Helvetica","B",11); pdf.set_xy(12,y+2); pdf.cell(60,7,"Violation:")
    pdf.set_font("Helvetica","",11);  pdf.set_xy(72,y+2); pdf.cell(125,7,violation)
    y += 13

    # Rules
    rules = {
        "No Helmet":     "MV Act Sec.129 - Helmet mandatory for all riders",
        "Triple Riding": "MV Act Sec.128 - Max 2 persons on two-wheeler",
        "Overspeed":     "MV Act Sec.183 - Speed limit violation",
    }
    for part in violation.split(" + "):
        rule = rules.get(part.strip(), "Motor Vehicles Act violation")
        pdf.set_font("Helvetica","I",9); pdf.set_text_color(80,80,80)
        pdf.set_xy(12,y); pdf.cell(186,6, f"  - {rule}")
        y += 7

    # Evidence image name
    y += 2
    pdf.set_fill_color(240,240,240); pdf.set_text_color(0,0,0)
    pdf.rect(10, y, 190, 10, 'FD')
    pdf.set_font("Helvetica","B",10); pdf.set_xy(12,y+1); pdf.cell(55,7,"Evidence:")
    pdf.set_font("Helvetica","",10);  pdf.set_xy(68,y+1)
    pdf.cell(130,7, os.path.basename(img_path) if img_path else "N/A")
    y += 14

    # ── fine box ────────────────────────────────────────
    pdf.set_fill_color(31,78,121); pdf.set_text_color(255,255,255)
    pdf.set_font("Helvetica","B",14)
    pdf.rect(10, y, 190, 14, 'FD')
    pdf.set_xy(13,y+3); pdf.cell(90,8,"  TOTAL FINE AMOUNT:")
    pdf.set_xy(105,y+3); pdf.cell(93,8,f"Rs. {fine}/-", align="R")
    y += 18

    # Pay note
    pdf.set_text_color(192,0,0); pdf.set_font("Helvetica","B",9)
    pdf.set_xy(10,y); pdf.cell(190,6,"Pay within 30 days. Late payment = 2x fine.", align="C")
    y += 7
    pdf.set_text_color(60,60,60); pdf.set_font("Helvetica","",9)
    pdf.set_xy(10,y); pdf.cell(190,5,"Pay at: parivahan.gov.in | mParivahan App | Traffic Police Office", align="C")

    # ── footer ──────────────────────────────────────────
    pdf.set_fill_color(220,220,220)
    pdf.rect(0, 272, 210, 25, 'F')
    pdf.set_text_color(80,80,80); pdf.set_font("Helvetica","I",8)
    pdf.set_xy(0,275); pdf.cell(210,5,"Computer-generated E-Challan. No signature required.", align="C")
    pdf.set_xy(0,281); pdf.cell(210,5,"Disputes: traffic.complaints@police.gov.in  |  Helpline: 1095", align="C")
    pdf.set_xy(0,287)
    pdf.cell(210,5,f"Generated: {datetime.now().strftime('%d-%m-%Y %H:%M:%S')}", align="C")

    # Save
    fname = os.path.join("challans", f"{challan_id}_{plate}.pdf")
    pdf.output(fname)
    print(f"[PDF] Saved: {fname}")
    return fname
