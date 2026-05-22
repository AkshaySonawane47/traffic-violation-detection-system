"""
tracker.py  —  Centroid Tracker with smooth ID persistence
==========================================================
Improved from previous version:
  - max_distance increased to 120px (was 80) for faster-moving bikes
  - max_disappeared increased to 40 (was 30) — less ID churn on occlusion
  - Added velocity prediction: if object moves fast, predict next position
    before matching so it doesn't get a new ID on fast movement
"""

import numpy as np
from collections import OrderedDict


class CentroidTracker:
    def __init__(self, max_disappeared=40, max_distance=120):
        self.next_id         = 0
        self.objects         = OrderedDict()    # id → (cx, cy)
        self.disappeared     = OrderedDict()    # id → frames missing
        self.velocities      = OrderedDict()    # id → (vx, vy) last velocity
        self.max_disappeared = max_disappeared
        self.max_distance    = max_distance

    def _centroid(self, x, y, w, h):
        return (int(x + w / 2), int(y + h / 2))

    def _register(self, cx, cy):
        self.objects[self.next_id]     = (cx, cy)
        self.disappeared[self.next_id] = 0
        self.velocities[self.next_id]  = (0, 0)
        self.next_id += 1

    def _deregister(self, obj_id):
        del self.objects[obj_id]
        del self.disappeared[obj_id]
        if obj_id in self.velocities:
            del self.velocities[obj_id]

    def update(self, boxes):
        """
        boxes: list of (x, y, w, h)
        Returns: dict {id: (cx, cy)}
        """
        if len(boxes) == 0:
            for obj_id in list(self.disappeared.keys()):
                self.disappeared[obj_id] += 1
                if self.disappeared[obj_id] > self.max_disappeared:
                    self._deregister(obj_id)
            return self.objects

        input_centroids = [self._centroid(*b) for b in boxes]

        if len(self.objects) == 0:
            for cx, cy in input_centroids:
                self._register(cx, cy)
            return self.objects

        obj_ids   = list(self.objects.keys())
        obj_cents = list(self.objects.values())

        # Apply velocity prediction to get expected positions
        predicted = []
        for oid, (cx, cy) in zip(obj_ids, obj_cents):
            vx, vy = self.velocities.get(oid, (0, 0))
            predicted.append((cx + vx, cy + vy))

        # Distance matrix using predicted positions
        D = np.zeros((len(predicted), len(input_centroids)), dtype=np.float32)
        for r, (px, py) in enumerate(predicted):
            for c, (nx, ny) in enumerate(input_centroids):
                D[r, c] = np.sqrt((px - nx)**2 + (py - ny)**2)

        rows = D.min(axis=1).argsort()
        cols = D.argmin(axis=1)[rows]

        used_rows = set()
        used_cols = set()

        for row, col in zip(rows, cols):
            if row in used_rows or col in used_cols:
                continue
            if D[row, col] > self.max_distance:
                continue
            obj_id      = obj_ids[row]
            old_cx, old_cy = self.objects[obj_id]
            new_cx, new_cy = input_centroids[col]
            # Update velocity (smoothed)
            old_vx, old_vy = self.velocities.get(obj_id, (0, 0))
            vx = int((new_cx - old_cx) * 0.5 + old_vx * 0.5)
            vy = int((new_cy - old_cy) * 0.5 + old_vy * 0.5)
            self.objects[obj_id]     = (new_cx, new_cy)
            self.disappeared[obj_id] = 0
            self.velocities[obj_id]  = (vx, vy)
            used_rows.add(row)
            used_cols.add(col)

        for row in set(range(len(obj_ids))) - used_rows:
            obj_id = obj_ids[row]
            self.disappeared[obj_id] += 1
            if self.disappeared[obj_id] > self.max_disappeared:
                self._deregister(obj_id)

        for col in set(range(len(input_centroids))) - used_cols:
            self._register(*input_centroids[col])

        return self.objects
