"""
send_emails.py
Send E-Challan emails to all pending violations.

SETUP BEFORE USING:
1. Open this file
2. Set SENDER_EMAIL = "your_gmail@gmail.com"
3. Set SENDER_PASSWORD = "your 16-digit app password"
   Get App Password: myaccount.google.com → Security → App Passwords
4. Run: python send_emails.py
"""

import smtplib, os
from email.mime.multipart import MIMEMultipart
from email.mime.text      import MIMEText
from email.mime.base      import MIMEBase
from email                import encoders
from violation_log        import get_all_violations

# ── CHANGE THESE ───────────────────────────────────────
SENDER_EMAIL    = "your_email@gmail.com"
SENDER_PASSWORD = "your_app_password"
# ───────────────────────────────────────────────────────


def send_one(to_email, owner_name, challan_id, plate,
             violation, fine, pdf_path):

    subject = f"Traffic E-Challan {challan_id} | Vehicle {plate}"

    body = f"""
<html><body style="font-family:Arial;color:#333;">
<div style="background:#1F4E79;padding:18px;text-align:center;">
  <h2 style="color:white;margin:0;">TRAFFIC E-CHALLAN NOTICE</h2>
  <p style="color:#ccc;margin:4px 0;">Automated Traffic Violation System</p>
</div>
<div style="padding:18px;">
  <p>Dear <strong>{owner_name}</strong>,</p>
  <p>Your vehicle has been detected in a traffic violation.</p>
  <table style="width:100%;border-collapse:collapse;margin:12px 0;">
    <tr style="background:#f2f2f2;">
      <td style="padding:7px;border:1px solid #ddd;font-weight:bold;">Challan ID</td>
      <td style="padding:7px;border:1px solid #ddd;">{challan_id}</td>
    </tr>
    <tr>
      <td style="padding:7px;border:1px solid #ddd;font-weight:bold;">Vehicle</td>
      <td style="padding:7px;border:1px solid #ddd;">{plate}</td>
    </tr>
    <tr style="background:#f2f2f2;">
      <td style="padding:7px;border:1px solid #ddd;font-weight:bold;">Violation</td>
      <td style="padding:7px;border:1px solid #ddd;color:#C00000;"><strong>{violation}</strong></td>
    </tr>
    <tr>
      <td style="padding:7px;border:1px solid #ddd;font-weight:bold;">Fine</td>
      <td style="padding:7px;border:1px solid #ddd;color:#C00000;"><strong>Rs. {fine}/-</strong></td>
    </tr>
  </table>
  <div style="background:#FFF2CC;padding:12px;border-left:4px solid #C00000;margin:12px 0;">
    Pay within <strong>30 days</strong> to avoid legal action.
  </div>
  <p>Pay at: <a href="https://parivahan.gov.in">parivahan.gov.in</a> | mParivahan App</p>
  <p style="font-size:12px;color:#888;">Auto-generated. Do not reply.</p>
</div></body></html>
"""
    msg = MIMEMultipart()
    msg["From"]    = SENDER_EMAIL
    msg["To"]      = to_email
    msg["Subject"] = subject
    msg.attach(MIMEText(body, "html"))

    if pdf_path and os.path.exists(pdf_path):
        with open(pdf_path, "rb") as f:
            part = MIMEBase("application","octet-stream")
            part.set_payload(f.read())
            encoders.encode_base64(part)
            part.add_header("Content-Disposition",
                f'attachment; filename="{os.path.basename(pdf_path)}"')
            msg.attach(part)

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as s:
        s.login(SENDER_EMAIL, SENDER_PASSWORD)
        s.sendmail(SENDER_EMAIL, to_email, msg.as_string())


def send_all():
    violations = get_all_violations()
    pending    = [v for v in violations if v.get("Status") == "Pending"]

    print(f"Total: {len(violations)}  |  Pending: {len(pending)}")
    sent = skipped = 0

    for v in pending:
        cid    = v.get("Challan ID","")
        plate  = v.get("Number Plate","")
        name   = v.get("Owner Name","UNKNOWN")
        email  = v.get("Email","")
        vtype  = v.get("Violation Type","")
        fine   = v.get("Fine (Rs)", 0)

        # Find PDF
        pdf_path = None
        for f in os.listdir("challans"):
            if cid in f:
                pdf_path = os.path.join("challans", f)
                break

        print(f"\n→ {cid} | {plate} | {name} | {email}")

        if not email or email == "N/A":
            print("  SKIPPED — no email")
            skipped += 1
            continue

        try:
            send_one(email, name, cid, plate, vtype, fine, pdf_path)
            print("  SENT ✓")
            sent += 1
        except Exception as e:
            print(f"  FAILED: {e}")
            skipped += 1

    print(f"\nDone → Sent: {sent}  |  Skipped: {skipped}")


if __name__ == "__main__":
    print("="*50)
    print("  E-CHALLAN EMAIL SENDER")
    print("="*50)
    if "your_email" in SENDER_EMAIL:
        print("\n[ERROR] Set SENDER_EMAIL and SENDER_PASSWORD first!")
        print("Open send_emails.py and update lines 16-17")
    else:
        confirm = input("\nSend emails to all pending violations? (yes/no): ")
        if confirm.lower() == "yes":
            send_all()
