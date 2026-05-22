"""
config/settings.py  — Central configuration. Edit only this file.
"""
DETECT_EVERY    = 3
RESIZE_W        = 640
YOLO_CONF       = 0.25
MAX_DISAPPEARED = 40
MAX_DISTANCE    = 120
HEAD_FRACTION   = 0.38
SKIN_THRESHOLD  = 0.14
FACE_NEIGHBORS  = 3
PLATE_MATCH_MIN = 0.20   # 20% threshold — always tries to match Excel
COOLDOWN_SEC    = 10
DISPLAY_MAX_W   = 720
SHOW_LEGEND     = True
SHOW_FPS        = True
SHOW_TRACKER_ID = True
OWNERS_FILE     = "bike_owners.xlsx"
VIOLATIONS_FILE = "violations.xlsx"
VIOLATION_DIR   = "violation_images"
CHALLANS_DIR    = "challans"
FINE_NO_HELMET     = 1000
FINE_TRIPLE_RIDING = 1000
SOUND_ALERT     = True
SENDER_EMAIL    = "your_email@gmail.com"
SENDER_PASSWORD = "your_app_password"

FINE_OVERSPEED     = 2000
