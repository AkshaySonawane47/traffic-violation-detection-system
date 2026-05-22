"""
roi_selector.py
===============
Interactive ROI (Region of Interest) polygon selector.
Click points on the first video frame to draw a polygon zone.
Only objects whose centroid is inside this polygon will be checked
for violations — simulating a real CCTV detection zone.

Usage:
    from roi_selector import select_roi
    polygon = select_roi(first_frame)
    # polygon = [(x1,y1), (x2,y2), ...] or None if skipped
"""

import cv2
import numpy as np


# ──────────────────────────────────────────────────────────────
#  Interactive polygon drawing
# ──────────────────────────────────────────────────────────────
_points  = []
_drawing = False
_done    = False


def _mouse_cb(event, x, y, flags, param):
    global _points, _done
    if _done:
        return
    if event == cv2.EVENT_LBUTTONDOWN:
        _points.append((x, y))
    elif event == cv2.EVENT_RBUTTONDOWN:
        # Right-click = finish polygon
        _done = True


def select_roi(frame):
    """
    Show frame, let user click to place polygon points.
    Right-click or press ENTER to confirm.
    Press ESC to skip ROI (full frame used).

    Returns
    -------
    list of (x,y) tuples  or  None
    """
    global _points, _done
    _points = []
    _done   = False

    clone  = frame.copy()
    win    = "Draw ROI — Left-click: add point | Right-click / ENTER: done | ESC: skip"
    cv2.namedWindow(win, cv2.WINDOW_NORMAL)
    cv2.resizeWindow(win, min(frame.shape[1], 960), min(frame.shape[0], 600))
    cv2.setMouseCallback(win, _mouse_cb)

    instructions = [
        "LEFT-CLICK  : Add polygon point",
        "RIGHT-CLICK : Finish polygon",
        "ENTER       : Confirm",
        "ESC         : Skip ROI (use full frame)",
        "BACKSPACE   : Remove last point",
    ]

    while True:
        disp = clone.copy()

        # Draw instruction overlay
        overlay = disp.copy()
        cv2.rectangle(overlay, (5, 5), (320, 20 + len(instructions) * 18), (0,0,0), -1)
        cv2.addWeighted(overlay, 0.55, disp, 0.45, 0, disp)
        for i, txt in enumerate(instructions):
            cv2.putText(disp, txt, (10, 22 + i * 18),
                cv2.FONT_HERSHEY_SIMPLEX, 0.42, (255, 255, 0), 1)

        # Draw current polygon
        if len(_points) > 1:
            pts = np.array(_points, dtype=np.int32)
            cv2.polylines(disp, [pts], _done, (0, 255, 255), 2)
            if _done:
                cv2.fillPoly(
                    cv2.addWeighted(disp.copy(), 0.35, disp, 0.65, 0, disp.copy()),
                    [pts], (0, 255, 100))

        for pt in _points:
            cv2.circle(disp, pt, 5, (0, 255, 0), -1)

        cv2.imshow(win, disp)
        key = cv2.waitKey(20) & 0xFF

        if key == 27:           # ESC → skip
            cv2.destroyWindow(win)
            return None

        if key == 8 and _points: # BACKSPACE → remove last point
            _points.pop()
            _done = False

        if (key == 13 or _done) and len(_points) >= 3:  # ENTER or right-click
            _done = True
            break

    cv2.destroyWindow(win)
    print(f"[ROI] Polygon set with {len(_points)} points: {_points}")
    return _points


# ──────────────────────────────────────────────────────────────
#  Point-in-polygon test
# ──────────────────────────────────────────────────────────────
def point_in_roi(cx, cy, polygon):
    """
    Returns True if (cx, cy) is inside the polygon.
    Uses OpenCV pointPolygonTest.
    """
    if polygon is None or len(polygon) < 3:
        return True   # no ROI = full frame
    pts = np.array(polygon, dtype=np.int32)
    result = cv2.pointPolygonTest(pts, (float(cx), float(cy)), False)
    return result >= 0


def draw_roi(frame, polygon, color=(0, 255, 255)):
    """Draw the ROI polygon on the frame (in-place)."""
    if polygon is None or len(polygon) < 3:
        return
    pts = np.array(polygon, dtype=np.int32)
    cv2.polylines(frame, [pts], True, color, 2)

    # Semi-transparent fill
    overlay = frame.copy()
    cv2.fillPoly(overlay, [pts], (0, 255, 255))
    cv2.addWeighted(overlay, 0.10, frame, 0.90, 0, frame)
