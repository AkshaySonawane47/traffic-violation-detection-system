"""
send_emails.py
==============
Sends E-Challan emails to all owners with 'Pending' violations.
Attaches the PDF challan as email attachment.

SETUP (one-time):
  1. Open config/settings.py
  2. Set SENDER_EMAIL and SENDER_PASSWORD (Gmail App Password)
     Get App Password: myaccount.google.com → Security → App Passwords
  3. Run: python send_emails.py
"""

import smtplib, os
from email.mime.multipart import MIMEMultipart
from email.mime.text      import MIMEText
from email.mime.base      import MIMEBase
from email                import encoders
from violation_log        import get_all_violations

try:
    from config.settings import SENDER_EMAIL, SENDER_PASSWORD, CHALLANS_DIR
except ImportError:
    SENDER_EMAIL    = "your_email@gmail.com"
    SENDER_PASSWORD = "your_app_password"
    CHALLANS_DIR    = "challans"


def build_html(owner_name, challan_id, plate, violation, fine, date, time_):
    return f"""
<html><body style="font-family:Arial,sans-serif;color:#333;margin:0;padding:0;">
<div style="background:#15436B;padding:20px;text-align:center;">
  <h2 style="color:#fff;margin:0;letter-spacing:1px;">TRAFFIC E-CHALLAN NOTICE</h2>
  <p style="color:#bcd;margin:4px 0;font-size:13px;">
    AI-Based Automated Traffic Violation Detection System
  </p>
</div>

<div style="padding:24px;max-width:600px;margin:auto;">
  <p>Dear <strong>{owner_name}</strong>,</p>
  <p>Your vehicle has been detected committing a traffic violation by
     our AI-powered surveillance system. Please find the details below.</p>

  <table style="width:100%;border-collapse:collapse;margin:16px 0;font-size:14px;">
    <tr style="background:#f0f4f8;">
      <td style="padding:9px 12px;border:1px solid #ddd;font-weight:bold;width:40%;">Challan ID</td>
      <td style="padding:9px 12px;border:1px solid #ddd;">{challan_id}</td>
    </tr>
    <tr>
      <td style="padding:9px 12px;border:1px solid #ddd;font-weight:bold;">Vehicle Number</td>
      <td style="padding:9px 12px;border:1px solid #ddd;font-weight:bold;">{plate}</td>
    </tr>
    <tr style="background:#f0f4f8;">
      <td style="padding:9px 12px;border:1px solid #ddd;font-weight:bold;">Violation</td>
      <td style="padding:9px 12px;border:1px solid #ddd;color:#C00000;font-weight:bold;">{violation}</td>
    </tr>
    <tr>
      <td style="padding:9px 12px;border:1px solid #ddd;font-weight:bold;">Date &amp; Time</td>
      <td style="padding:9px 12px;border:1px solid #ddd;">{date} at {time_}</td>
    </tr>
    <tr style="background:#f0f4f8;">
      <td style="padding:9px 12px;border:1px solid #ddd;font-weight:bold;">Fine Amount</td>
      <td style="padding:9px 12px;border:1px solid #ddd;color:#C00000;font-size:16px;font-weight:bold;">
        Rs. {fine}/-
      </td>
    </tr>
  </table>

  <div style="background:#FFF3CD;border-left:4px solid #C00000;padding:14px;margin:16px 0;border-radius:3px;">
    <strong>Action Required:</strong> Please pay within <strong>30 days</strong>
    to avoid legal action and penalty doubling.
  </div>

  <p><strong>Payment Options:</strong></p>
  <ul>
    <li>Online: <a href="https://parivahan.gov.in">parivahan.gov.in</a></li>
    <li>App: mParivahan (Google Play / App Store)</li>
    <li>In-person: Nearest Traffic Police Office</li>
  </ul>

  <p>The PDF E-Challan is attached to this email for your records.</p>

  <hr style="border:none;border-top:1px solid #eee;margin:20px 0;">
  <p style="font-size:11px;color:#999;">
    This is an auto-generated email from the AI Traffic Violation Detection System.
    Do not reply to this email. For disputes: traffic.complaints@police.gov.in | Helpline: 1095
  </p>
</div>
</body></html>"""


def send_one(to_email, owner_name, challan_id, plate,
             violation, fine, date, time_, pdf_path):
    """Send a single challan email with PDF attachment."""
    subject = f"Traffic E-Challan {challan_id} | Vehicle {plate}"
    msg = MIMEMultipart("alternative")
    msg["From"]    = SENDER_EMAIL
    msg["To"]      = to_email
    msg["Subject"] = subject

    html = build_html(owner_name, challan_id, plate,
                      violation, fine, date, time_)
    msg.attach(MIMEText(html, "html"))

    # Attach PDF
    if pdf_path and os.path.exists(pdf_path):
        with open(pdf_path, "rb") as f:
            part = MIMEBase("application", "octet-stream")
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
    print(f"Total: {len(violations)}  |  Pending emails: {len(pending)}")

    sent = skipped = 0
    for v in pending:
        cid   = v.get("Challan ID", "")
        plate = v.get("Number Plate", "")
        name  = v.get("Owner Name", "UNKNOWN")
        email = v.get("Email", "")
        vtype = v.get("Violation Type", "")
        fine  = v.get("Fine (Rs)", 0)
        date  = v.get("Date", "")
        time_ = v.get("Time", "")

        # Find matching PDF
        pdf_path = None
        if os.path.isdir(CHALLANS_DIR):
            for f in os.listdir(CHALLANS_DIR):
                if cid in f and f.endswith(".pdf"):
                    pdf_path = os.path.join(CHALLANS_DIR, f)
                    break

        print(f"\n→ {cid} | {plate} | {name} | {email}")

        if not email or email in ("N/A", ""):
            print("  SKIPPED — no email address")
            skipped += 1
            continue

        try:
            send_one(email, name, cid, plate, vtype, fine,
                     date, time_, pdf_path)
            print("  SENT ✓")
            sent += 1
        except Exception as e:
            print(f"  FAILED: {e}")
            skipped += 1

    print(f"\nResult → Sent: {sent}  |  Skipped/Failed: {skipped}")


if __name__ == "__main__":
    print("=" * 50)
    print("  E-CHALLAN EMAIL SENDER")
    print("=" * 50)
    if "your_email" in SENDER_EMAIL:
        print("\n[ERROR] Configure SENDER_EMAIL and SENDER_PASSWORD")
        print("        in config/settings.py before sending.")
    else:
        ans = input("\nSend emails to all pending violations? (yes/no): ")
        if ans.strip().lower() == "yes":
            send_all()
        else:
            print("Aborted.")
