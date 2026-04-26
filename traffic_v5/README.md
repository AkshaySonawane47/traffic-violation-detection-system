# AI-Based Traffic Violation Detection System
### Final Year Project | Computer Vision | Python | OpenCV

---

## SYSTEM OVERVIEW

An intelligent real-time traffic monitoring system that detects violations
from video footage and automatically generates E-Challans.

**Violations Detected:**
| Violation | Detection Method | Fine |
|---|---|---|
| No Helmet | Haar face cascade + HSV skin analysis on head region | Rs. 1,000 |
| Triple Riding | Upper-body cascade + HOG detector | Rs. 1,000 |
| Overspeed *(optional)* | Pixel displacement estimation | Rs. 2,000 |

---

## FOLDER STRUCTURE

```
traffic_project/
├── detector.py          ← MAIN — run this
├── plate_ocr.py         ← Number plate OCR (EasyOCR)
├── violation_log.py     ← Save violations to Excel
├── challan_pdf.py       ← Generate PDF challans
├── send_emails.py       ← Email challans to owners
├── create_owners.py     ← Create bike_owners.xlsx database
├── tracker.py           ← Centroid vehicle tracker
├── roi_selector.py      ← Interactive ROI polygon selector
├── requirements.txt
│
├── config/
│   └── settings.py      ← ALL settings in one place
│
├── bike_owners.xlsx      ← Registered vehicle database
├── violations.xlsx       ← All violation records (auto-created)
├── violation_images/     ← Evidence screenshots
└── challans/             ← PDF challans
```

---

## STEP-BY-STEP SETUP

### 1. Install dependencies
```bash
pip install -r requirements.txt
```

### 2. Create owner database
```bash
python create_owners.py
```
Edit `create_owners.py` to add your own vehicle entries first.

### 3. Download test videos
```bash
pip install yt-dlp
yt-dlp -o "video1_triple.mp4"  "https://youtube.com/shorts/u-VXR5fY8_k"
yt-dlp -o "video2_helmet.mp4"  "https://youtube.com/shorts/A9J3E6BHwbM"
```

### 4. Run detection
```bash
# Basic run
python detector.py video1_triple.mp4

# With ROI selection (draw detection zone first)
python detector.py video2_helmet.mp4 --roi

# Webcam
python detector.py 0
```

### 5. Send emails (after detection)
```bash
# Set SENDER_EMAIL and SENDER_PASSWORD in config/settings.py first
python send_emails.py
```

---

## KNOWN PLATES IN DATABASE

| Plate | Owner | Test Video |
|---|---|---|
| BR02BS9361 | Akshay Sonawane | video1_triple.mp4 |
| DL9SCD5588 | Lalit Wagh | video2_helmet.mp4 |

---

## WHAT EACH FILE DOES

| File | Purpose |
|---|---|
| `detector.py` | Main loop — video reading, detection, drawing, challan trigger |
| `plate_ocr.py` | Preprocess plate crop + EasyOCR + fuzzy matching |
| `violation_log.py` | Append violation rows to violations.xlsx |
| `challan_pdf.py` | Generate styled A4 PDF with evidence image |
| `send_emails.py` | Send HTML email with PDF attachment via Gmail |
| `tracker.py` | Centroid tracker — assigns unique V# ID to each vehicle |
| `roi_selector.py` | Mouse-click polygon ROI selection + inside-polygon test |
| `config/settings.py` | All tunable parameters in one place |

---

## PERFORMANCE TIPS (4 GB RAM laptop)

- Set `DETECT_EVERY = 20` or higher in `config/settings.py`
- Set `RESIZE_W = 480`
- Close Chrome and other apps while running
- Use 480p video: `yt-dlp -f 'best[height<=480]' <url>`
- Disable sound: `SOUND_ALERT = False`

---

## SYSTEM FLOW

```
Video Frame
    ↓
MOG2 Background Subtraction  →  Motion Mask
    ↓
Find Contours  →  Filter by Size/Aspect Ratio
    ↓
Centroid Tracker  →  Vehicle ID assigned
    ↓
ROI Filter  →  Only process objects inside zone
    ↓
┌─────────────────────┐
│  For each vehicle:  │
│  1. Crop plate area │
│  2. OCR plate text  │
│  3. Match DB        │
│  4. Helmet check    │
│  5. Person count    │
└─────────────────────┘
    ↓ (if violation found)
Cooldown check  →  Skip if same plate < 20 seconds ago
    ↓
Save evidence image
    ↓
┌─────────────────┬──────────────────┐
│ Plate IN DB     │ Plate NOT in DB  │
│ PDF Challan +   │ Excel log only   │
│ Excel row       │ (no challan)     │
└─────────────────┴──────────────────┘
    ↓
Sound alert + display update
```

---

## LIMITATIONS

1. **Helmet detection accuracy** — Haar cascade approach works well in
   good lighting but may miss helmets in side-view or low-light scenarios.
   For production: train a YOLOv8 model on helmet/no-helmet dataset.

2. **OCR accuracy** — EasyOCR struggles with blurry, partially occluded,
   or tilted plates. Accuracy improves significantly with higher-resolution input.

3. **No GPU required** — Background subtraction + Haar cascades work on CPU,
   but processing speed is limited (~8-12 FPS on typical laptop).

4. **Single camera** — No multi-camera synchronisation or cross-camera tracking.

5. **Static background assumed** — MOG2 works best with fixed-angle CCTV.
   Moving camera (dashcam) will produce many false positives.

---

## FUTURE IMPROVEMENTS

| Feature | Technology |
|---|---|
| Accurate helmet detection | YOLOv8 trained on custom dataset |
| GPU acceleration | CUDA + TensorRT |
| Cloud deployment | AWS/GCP + Docker + FastAPI |
| Real-time dashboard | Flask/Streamlit web app |
| Multi-camera support | RTSP stream + distributed processing |
| License plate recognition | Specialized ANPR models (OpenALPR) |
| Smart city integration | MQTT + IoT sensor fusion |
| Mobile app for officers | React Native + REST API |

---

## VIVA KEY POINTS

1. **Why MOG2?** — Adaptive Gaussian Mixture model learns the background
   automatically, handles gradual lighting changes, and is fast enough for
   real-time CPU use.

2. **Why centroid tracking?** — Simple, no extra dependencies, sufficient
   for forward-moving traffic. For complex intersections, SORT or DeepSORT
   would be better.

3. **Why EasyOCR over Tesseract?** — EasyOCR handles more fonts, works
   better on non-standard angles, and has higher accuracy on Indian plates.

4. **Cooldown mechanism** — Prevents the same vehicle from getting 50
   challans in one video. Configurable duration in settings.py.

5. **ROI polygon** — Simulates the real CCTV scenario where you only want
   to check violations at a specific point (e.g. intersection, signal line).

6. **Plate-first logic** — Plates are read BEFORE checking for violations,
   ensuring accurate challan attribution. Unknown plates are logged but do
   not generate a formal challan.
