"""
tracker.py
==========
Centroid-based vehicle tracker.
Assigns a unique integer ID to each detected vehicle and keeps it
across frames using nearest-centroid matching.

Why centroid tracking (not SORT/DeepSORT)?
  - No extra dependencies (no scipy, no filterpy)
  - Fast enough for real-time CPU use
  - Sufficient for traffic camera scenarios (mostly forward motion)

Usage (internal — called by detector.py):
    from tracker import CentroidTracker
    ct = CentroidTracker(max_disappeared=30, max_distance=80)

    # Each frame: pass list of (x, y, w, h) bounding boxes
    objects = ct.update(boxes)
    # objects = {id: (cx, cy)}
"""

import numpy as np
from collections import OrderedDict


class CentroidTracker:
    """
    Tracks objects across frames using centroid distance matching.

    Attributes
    ----------
    next_id         : int   — incrementing unique ID counter
    objects         : dict  — {id: (cx, cy)}
    disappeared     : dict  — {id: frames_missing}
    max_disappeared : int   — drop track after N missing frames
    max_distance    : float — max pixel distance for centroid match
    """

    def __init__(self, max_disappeared: int = 30, max_distance: float = 80):
        self.next_id         = 0
        self.objects         = OrderedDict()   # id → (cx, cy)
        self.disappeared     = OrderedDict()   # id → frames missing
        self.max_disappeared = max_disappeared
        self.max_distance    = max_distance

    # ──────────────────────────────────────────────────
    def _centroid(self, x, y, w, h):
        return (int(x + w / 2), int(y + h / 2))

    def _register(self, cx, cy):
        self.objects[self.next_id]     = (cx, cy)
        self.disappeared[self.next_id] = 0
        self.next_id += 1

    def _deregister(self, obj_id):
        del self.objects[obj_id]
        del self.disappeared[obj_id]

    # ──────────────────────────────────────────────────
    def update(self, boxes):
        """
        Parameters
        ----------
        boxes : list of (x, y, w, h)

        Returns
        -------
        objects : dict {id: (cx, cy)}
        """
        # No detections this frame
        if len(boxes) == 0:
            for obj_id in list(self.disappeared.keys()):
                self.disappeared[obj_id] += 1
                if self.disappeared[obj_id] > self.max_disappeared:
                    self._deregister(obj_id)
            return self.objects

        # Compute centroids for current detections
        input_centroids = [self._centroid(*b) for b in boxes]

        # No existing tracks → register all
        if len(self.objects) == 0:
            for cx, cy in input_centroids:
                self._register(cx, cy)
            return self.objects

        # Match existing tracks to new centroids
        obj_ids     = list(self.objects.keys())
        obj_cents   = list(self.objects.values())

        # Distance matrix: rows=existing, cols=new
        D = np.zeros((len(obj_cents), len(input_centroids)), dtype=np.float32)
        for r, (ox, oy) in enumerate(obj_cents):
            for c, (nx, ny) in enumerate(input_centroids):
                D[r, c] = np.sqrt((ox - nx)**2 + (oy - ny)**2)

        # Greedy match: sort by smallest distance
        rows = D.min(axis=1).argsort()
        cols = D.argmin(axis=1)[rows]

        used_rows = set()
        used_cols = set()

        for row, col in zip(rows, cols):
            if row in used_rows or col in used_cols:
                continue
            if D[row, col] > self.max_distance:
                continue
            obj_id = obj_ids[row]
            self.objects[obj_id]     = input_centroids[col]
            self.disappeared[obj_id] = 0
            used_rows.add(row)
            used_cols.add(col)

        # Unmatched existing tracks → increment disappeared
        for row in set(range(len(obj_ids))) - used_rows:
            obj_id = obj_ids[row]
            self.disappeared[obj_id] += 1
            if self.disappeared[obj_id] > self.max_disappeared:
                self._deregister(obj_id)

        # Unmatched new centroids → register as new objects
        for col in set(range(len(input_centroids))) - used_cols:
            self._register(*input_centroids[col])

        return self.objects
