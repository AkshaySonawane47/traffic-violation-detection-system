"""
config/settings.py  —  Central configuration
=============================================
Tuned for Indian traffic video (360×640, 30fps, close-up scenes).
"""

# ── Detection ─────────────────────────────────────────────────
DETECT_EVERY    = 3        # Process every 3rd frame (= 10 detections/sec @ 30fps)
RESIZE_W        = 640
COOLDOWN_SEC    = 8        # Per-plate-per-violation cooldown (seconds)
PLATE_MATCH_MIN = 0.35     # Fuzzy plate match threshold (lower = more lenient)

# ── YOLO ──────────────────────────────────────────────────────
YOLO_CONF       = 0.25     # Lower = catches more objects (bikes + persons)

# ── Helmet detection ──────────────────────────────────────────
FACE_NEIGHBORS  = 3        # Haar cascade sensitivity (lower = more sensitive)
SKIN_THRESHOLD  = 0.15     # Skin pixel % to trigger no-helmet violation
HEAD_FRACTION   = 0.35     # Top 35% of bounding box = head region

# ── Tracking ──────────────────────────────────────────────────
MAX_DISAPPEARED = 30
MAX_DISTANCE    = 80

# ── Display ───────────────────────────────────────────────────
DISPLAY_MAX_W   = 720
SHOW_LEGEND     = True
SHOW_FPS        = True
SHOW_TRACKER_ID = True

# ── Paths ─────────────────────────────────────────────────────
OWNERS_FILE     = "bike_owners.xlsx"
VIOLATIONS_FILE = "violations.xlsx"
VIOLATION_DIR   = "violation_images"
CHALLANS_DIR    = "challans"

# ── Fines (Rs.) ───────────────────────────────────────────────
FINE_NO_HELMET     = 1000
FINE_TRIPLE_RIDING = 1000
FINE_OVERSPEED     = 2000

# ── Alerts ────────────────────────────────────────────────────
SOUND_ALERT     = True

# ── Email ─────────────────────────────────────────────────────
SENDER_EMAIL    = "your_email@gmail.com"
SENDER_PASSWORD = "your_app_password"
