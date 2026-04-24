# Traffic Violation Detection System
### Detects: No Helmet | Triple Riding | Overspeed

---

## FOLDER STRUCTURE

```
traffic_project/
├── detector.py        ← MAIN — run this
├── plate_ocr.py       ← OCR for number plate reading
├── violation_log.py   ← saves violations to Excel
├── challan_pdf.py     ← generates PDF challan
├── send_emails.py     ← sends email to owner
├── create_owners.py   ← creates bike_owners.xlsx
├── requirements.txt
│
├── bike_owners.xlsx      ← owner database
├── violations.xlsx       ← all violation records
├── violation_images/     ← evidence screenshots
└── challans/             ← PDF challans
```

---

## STEP BY STEP

### 1. Install packages
```
pip install opencv-python easyocr openpyxl fpdf2 pillow numpy
```

### 2. Download your videos using yt-dlp
```
pip install yt-dlp
yt-dlp -o "video1_triple.mp4" "https://youtube.com/shorts/u-VXR5fY8_k"
yt-dlp -o "video2_helmet.mp4" "https://youtube.com/shorts/A9J3E6BHwbM"
```

### 3. Create owner database
```
python create_owners.py
```

### 4. Run detection on video
```
python detector.py video1_triple.mp4
python detector.py video2_helmet.mp4
```

### 5. Send emails (after detection)
- Open send_emails.py
- Add your Gmail and App Password
- Run: `python send_emails.py`

---

## KNOWN PLATES IN YOUR DATABASE

| Plate        | Owner           | Video              |
|--------------|-----------------|--------------------|
| BR02BS9361   | Akshay Sonawane | video1_triple.mp4  |
| DL9SCD5588   | Lalit Wagh      | video2_helmet.mp4  |

---

## WHAT GETS DETECTED

| Violation     | How detected              | Fine    |
|---------------|---------------------------|---------|
| No Helmet     | Face visible = no helmet  | Rs 1000 |
| Triple Riding | HOG counts 3+ persons     | Rs 1000 |
| Overspeed     | Pixel speed estimation    | Rs 2000 |

---

## TIPS FOR SLOW PC (4GB RAM)
- In detector.py: change PROCESS_EVERY = 4 to 6 or 8
- Close Chrome and other apps while running
- Use 480p video for faster processing
