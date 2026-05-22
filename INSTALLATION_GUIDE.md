# 🚗 Traffic Violation Detection System - Complete Installation Guide

**Complete setup instructions for running this project on a NEW PC from scratch.**

---

## 📋 Table of Contents
1. [System Requirements](#system-requirements)
2. [Step-by-Step Installation](#step-by-step-installation)
3. [Project Structure](#project-structure)
4. [Quick Start Commands](#quick-start-commands)
5. [Troubleshooting](#troubleshooting)
6. [Performance Tips](#performance-tips)

---

## 🖥️ System Requirements

### Minimum Requirements
- **OS**: Windows 10/11, macOS 10.14+, or Linux (Ubuntu 18.04+)
- **Python**: 3.8 or higher
- **RAM**: 4 GB minimum (8 GB recommended)
- **Disk Space**: 5 GB (includes models downloaded on first run)
- **Processor**: Intel i5/AMD Ryzen 5 or better

### Software Prerequisites
- Python 3.8+ installed and added to PATH
- pip (Python package manager - comes with Python)
- Git (optional, for cloning repo)
- Webcam or video files (for testing)

---

## 🚀 Step-by-Step Installation

### **STEP 1: Download & Navigate to Project**

#### Option A: Using Git (Recommended)
```bash
git clone https://github.com/AkshaySonawane47/traffic-violation-detection-system.git
cd traffic-violation-detection-system
cd traffic_fixed
```

#### Option B: Manual Download
1. Click **Code** → **Download ZIP**
2. Extract the ZIP file
3. Open Command Prompt/Terminal in `traffic_fixed` folder

---

### **STEP 2: Create Python Virtual Environment** ✨

**Why?** Isolates project dependencies, prevents conflicts with other projects.

```bash
# Create virtual environment
python -m venv venv

# Activate it:

# On Windows:
venv\Scripts\activate

# On macOS/Linux:
source venv/bin/activate
```

✅ **You'll see `(venv)` prefix in your terminal when activated.**

---

### **STEP 3: Upgrade pip**

```bash
python -m pip install --upgrade pip
```

---

### **STEP 4: Install Dependencies**

```bash
pip install -r requirements.txt
```

**This installs:**
- `opencv-python` - Video processing
- `ultralytics` - YOLOv8 object detection
- `easyocr` - License plate OCR
- `pandas` - Excel file handling
- `openpyxl` - Excel read/write
- `fpdf2` - PDF challan generation
- `Pillow` - Image processing
- `numpy` - Numerical operations

⏱️ **Note:** First run may take **3-5 minutes** (downloads ML models ~200 MB)

---

### **STEP 5: Create Owner Database**

```bash
python create_owners.py
```

This generates `bike_owners.xlsx` with sample vehicle data:
- Plate: `BR02BS9361` → Owner: Akshay Sonawane
- Plate: `DL9SCD5588` → Owner: Lalit Wagh

**To add your own vehicles:** Edit `create_owners.py` before running.

---

### **STEP 6: Get Test Videos**

#### Option A: Download from YouTube (Recommended)
```bash
pip install yt-dlp

# Video 1: No helmet violation
yt-dlp -o "video_no_helmet.mp4" "https://youtube.com/shorts/A9J3E6BHwbM"

# Video 2: Triple riding violation
yt-dlp -o "video_triple.mp4" "https://youtube.com/shorts/u-VXR5fY8_k"
```

#### Option B: Use Your Own Videos
- **Format**: MP4, AVI, or MOV
- **Resolution**: 480p to 1080p
- **Duration**: 5-30 seconds minimum

---

### **STEP 7: Run the Detector** ▶️

```bash
# Basic detection
python detector.py video_no_helmet.mp4

# With ROI selection (draw detection zone first)
python detector.py video_triple.mp4 --roi

# Using webcam (press 'q' to quit)
python detector.py 0
```

**Output files generated:**
- ✅ `violations.xlsx` - Violation log
- ✅ `violation_images/` - Evidence screenshots
- ✅ `challans/` - PDF e-challans

---

## 📁 Project Structure

```
traffic_fixed/
│
├── detector.py           ← MAIN FILE (run this)
├── plate_ocr.py          ← License plate OCR & matching
├── tracker.py            ← Vehicle tracking
├── violation_log.py      ← Save violations to Excel
├── challan_pdf.py        ← Generate PDF challans
├── roi_selector.py       ← Draw detection zone
├── create_owners.py      ← Create vehicle database
│
├── config/
│   └── settings.py       ← ALL tunable parameters
│
├── requirements.txt      ← Python dependencies
├── README.md             ← Quick reference
├── INSTALLATION_GUIDE.md ← This file
│
├── bike_owners.xlsx      ← Vehicle database (auto-created)
├── violations.xlsx       ← Violation records (auto-created)
├── violation_images/     ← Evidence photos (auto-created)
└── challans/             ← PDF files (auto-created)
```

---

## ⚡ Quick Start Commands

**After setup, use these commands:**

```bash
# Activate environment (every time you open terminal)
source venv/bin/activate  # macOS/Linux
venv\Scripts\activate     # Windows

# Add vehicles to database
python create_owners.py

# Run on video file
python detector.py video.mp4

# Run on webcam
python detector.py 0

# Run with ROI selection
python detector.py video.mp4 --roi

# Deactivate environment
deactivate
```

---

## 🐛 Troubleshooting

### ❌ "Python not found" or "pip not found"
**Solution:** 
1. Reinstall Python from [python.org](https://python.org)
2. ✅ **CHECK: "Add Python to PATH"** during installation
3. Restart Command Prompt/Terminal

### ❌ "No module named 'cv2'" or other import errors
```bash
# Reinstall requirements
pip install --upgrade -r requirements.txt
```

### ❌ Virtual environment not activating
```bash
# Delete old venv and recreate
rmdir venv
python -m venv venv
venv\Scripts\activate  # Windows
```

### ❌ EasyOCR model download errors
```bash
# Clear cache and retry
pip install --upgrade easyocr
# Run detector again (will re-download models)
```

### ❌ "Video file not found"
- Ensure video is in the same folder as `detector.py`
- Use full path: `python detector.py C:\videos\myvideo.mp4`

### ❌ Low FPS or laggy detection (4GB RAM)
In `config/settings.py`, change:
```python
DETECT_EVERY = 20       # Skip frames (default: 3)
YOLO_CONF = 0.5         # Lower detection sensitivity
RESIZE_W = 480          # Smaller resolution
```

### ❌ No violations detected
1. Check `bike_owners.xlsx` has correct plate numbers
2. Ensure plate is clearly visible in video
3. Verify helmet/triple-riding is actually in video
4. Check `config/settings.py` thresholds

---

## ⚙️ Performance Tips

### For Slow Computers (4GB RAM):
```python
# In config/settings.py:
DETECT_EVERY = 20           # Process every 20th frame
RESIZE_W = 480              # Lower resolution
YOLO_CONF = 0.5             # Less strict detection
```

### For Better Accuracy:
```python
# In config/settings.py:
DETECT_EVERY = 1            # Process every frame
RESIZE_W = 1280             # Higher resolution
YOLO_CONF = 0.25            # More strict detection
```

### System Optimization:
- Close Chrome, VS Code, heavy apps while running
- Use 480p video for faster processing
- Disable sound alerts: `SOUND_ALERT = False`

---

## 🎯 What Gets Detected

| Violation | Detection Method | Fine |
|-----------|-----------------|------|
| **No Helmet** | Face detection + skin analysis | Rs. 1,000 |
| **Triple Riding** | Multiple person detection | Rs. 1,000 |
| **Overspeed** | Pixel displacement (optional) | Rs. 2,000 |

---

## 📧 Optional: Send Email Challans

Edit `config/settings.py`:
```python
SENDER_EMAIL = "your_email@gmail.com"
SENDER_PASSWORD = "your_app_password"  # Use Gmail App Password, not regular password
```

Then run:
```bash
python send_emails.py
```

> **Note:** Enable 2-Factor Authentication and create an App Password in Gmail settings.

---

## ✅ Verification Checklist

After installation, verify everything works:

- [ ] Virtual environment created and activated
- [ ] All requirements installed (`pip list` shows all packages)
- [ ] `bike_owners.xlsx` created
- [ ] Test video downloaded
- [ ] `python detector.py video.mp4` runs without errors
- [ ] `violations.xlsx` created after detection
- [ ] Evidence images saved in `violation_images/`

---

## 🆘 Need Help?

1. **Check Logs:** Look at terminal output for error messages
2. **Verify Paths:** Ensure all files are in correct directories
3. **Reinstall:** `pip install --force-reinstall -r requirements.txt`
4. **Fresh Start:** Delete `venv`, reinstall from scratch

---

## 📝 Notes

- **First run is slow** (downloads ML models)
- **Virtual environment** isolates project dependencies
- **All settings** can be tuned in `config/settings.py`
- **Violations logged** in `violations.xlsx`
- **Evidence saved** in `violation_images/` and `challans/`

---

**Happy Traffic Monitoring! 🚔**
