"""Multi-object tracking for vehicle tracking across frames."""

import math
from typing import Dict, List, Optional, Tuple

from orchestration.tl_monitoring.config import (
    IOU_MATCH_THRESHOLD,
    TRACK_MAX_AGE,
)

BoundingBox = Tuple[int, int, int, int]  # (x1, y1, x2, y2)


class Track:
    """Represents a single tracked vehicle."""

    def __init__(self, track_id: int, bbox: BoundingBox):
        """Initialize a new track.

        Args:
            track_id: Unique identifier for this track
            bbox: Initial bounding box (x1, y1, x2, y2)
        """
        self.id = track_id
        self.box = bbox
        self.centroid: Optional[Tuple[float, float]] = self._compute_centroid(bbox)
        self.speed_px = 0.0
        self.age = 1
        self.missed_detections = 0

        # Queue-related state
        self.first_queue_time: Optional[float] = None
        self.in_queue = False
        self.in_stripe_frames = 0
        self.crossed = False

    @staticmethod
    def _compute_centroid(bbox: BoundingBox) -> Tuple[float, float]:
        """Compute centroid of bounding box.

        Args:
            bbox: Bounding box (x1, y1, x2, y2)

        Returns:
            Centroid coordinates (cx, cy)
        """
        x1, y1, x2, y2 = bbox
        return ((x1 + x2) / 2.0, (y1 + y2) / 2.0)

    def update(self, bbox: BoundingBox, dt: float) -> None:
        """Update track with new detection.

        Args:
            bbox: New bounding box
            dt: Time delta since last update
        """
        self.box = bbox
        new_centroid = self._compute_centroid(bbox)

        # Calculate pixel speed
        if self.centroid is not None:
            px, py = self.centroid
            cx, cy = new_centroid
            distance = math.hypot(cx - px, cy - py)
            self.speed_px = distance / max(dt, 1e-6)
        else:
            self.speed_px = 0.0

        self.centroid = new_centroid
        self.missed_detections = 0

    def increment_age(self) -> None:
        """Increment track age and missed detections."""
        self.age += 1
        self.missed_detections += 1

    def to_dict(self) -> dict:
        """Convert track to dictionary representation.

        Returns:
            Dictionary with track information
        """
        return {
            "id": self.id,
            "box": self.box,
            "centroid": self.centroid,
            "speed_px": self.speed_px,
            "age": self.age,
            "miss": self.missed_detections,
            "first_queue_time": self.first_queue_time,
            "in_queue": self.in_queue,
            "in_stripe_frames": self.in_stripe_frames,
            "crossed": self.crossed,
        }


class TrackManager:
    """Manages multiple vehicle tracks using IoU-based matching."""

    def __init__(
        self,
        iou_threshold: float = IOU_MATCH_THRESHOLD,
        max_age: int = TRACK_MAX_AGE,
    ):
        """Initialize the track manager.

        Args:
            iou_threshold: Minimum IoU for track-detection matching
            max_age: Maximum frames a track can be unmatched before deletion
        """
        self.tracks: Dict[int, Track] = {}
        self.next_id = 1
        self.iou_threshold = iou_threshold
        self.max_age = max_age

    @staticmethod
    def _compute_iou(bbox_a: BoundingBox, bbox_b: BoundingBox) -> float:
        """Compute Intersection over Union between two bounding boxes.

        Args:
            bbox_a: First bounding box (x1, y1, x2, y2)
            bbox_b: Second bounding box (x1, y1, x2, y2)

        Returns:
            IoU value between 0 and 1
        """
        ax1, ay1, ax2, ay2 = bbox_a
        bx1, by1, bx2, by2 = bbox_b

        # Compute intersection
        ix1 = max(ax1, bx1)
        iy1 = max(ay1, by1)
        ix2 = min(ax2, bx2)
        iy2 = min(ay2, by2)

        iw = max(0, ix2 - ix1)
        ih = max(0, iy2 - iy1)
        intersection = iw * ih

        # Compute union
        area_a = (ax2 - ax1) * (ay2 - ay1)
        area_b = (bx2 - bx1) * (by2 - by1)
        union = area_a + area_b - intersection

        return intersection / union if union > 0 else 0.0

    def update(self, detections: List[BoundingBox], dt: float) -> Dict[int, dict]:
        """Update tracks with new detections.

        Args:
            detections: List of bounding boxes from detector
            dt: Time delta since last update

        Returns:
            Dictionary of active tracks {track_id: track_dict}
        """
        # Age all existing tracks
        for track in self.tracks.values():
            track.increment_age()

        # Match detections to tracks using IoU
        unmatched_detections = set(range(len(detections)))

        for track in list(self.tracks.values()):
            best_match_idx = -1
            best_iou = -1.0

            for det_idx in list(unmatched_detections):
                iou_value = self._compute_iou(track.box, detections[det_idx])
                if iou_value > best_iou:
                    best_iou = iou_value
                    best_match_idx = det_idx

            # Update track if match found
            if best_iou >= self.iou_threshold:
                track.update(detections[best_match_idx], dt)
                unmatched_detections.remove(best_match_idx)

        # Create new tracks for unmatched detections
        for det_idx in unmatched_detections:
            new_track = Track(self.next_id, detections[det_idx])
            self.tracks[self.next_id] = new_track
            self.next_id += 1

        # Remove old tracks
        tracks_to_remove = [
            tid
            for tid, track in self.tracks.items()
            if track.missed_detections > self.max_age
        ]
        for tid in tracks_to_remove:
            del self.tracks[tid]

        # Return tracks as dictionaries
        return {tid: track.to_dict() for tid, track in self.tracks.items()}

    def get_track_count(self) -> int:
        """Get the number of active tracks.

        Returns:
            Number of active tracks
        """
        return len(self.tracks)

    def clear(self) -> None:
        """Clear all tracks."""
        self.tracks.clear()
        self.next_id = 1
