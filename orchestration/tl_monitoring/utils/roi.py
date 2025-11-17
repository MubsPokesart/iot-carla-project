"""Region of Interest (ROI) utilities for traffic monitoring."""

import json
from pathlib import Path
from typing import List, Optional, Tuple

import cv2
import numpy as np

Polygon = np.ndarray  # Shape: (N, 2) with dtype int32
Point = Tuple[float, float]


class ROIManager:
    """Manages Region of Interest polygons for traffic monitoring."""

    @staticmethod
    def load_polygon(json_path: str) -> Optional[Polygon]:
        """Load polygon from JSON file.

        Args:
            json_path: Path to JSON file containing polygon data

        Returns:
            Numpy array of polygon points or None if not found/invalid
        """
        try:
            with open(json_path, "r") as f:
                data = json.load(f)

            points = data.get("polygon", [])
            if len(points) < 3:
                return None

            return np.array(points, dtype=np.int32)

        except (FileNotFoundError, json.JSONDecodeError, ValueError):
            return None

    @staticmethod
    def save_polygon(json_path: str, polygon: List[List[int]]) -> None:
        """Save polygon to JSON file.

        Args:
            json_path: Path to save JSON file
            polygon: List of [x, y] points
        """
        Path(json_path).parent.mkdir(parents=True, exist_ok=True)

        with open(json_path, "w") as f:
            json.dump({"polygon": polygon}, f, indent=2)

    @staticmethod
    def point_in_polygon(point: Point, polygon: Polygon) -> bool:
        """Check if a point is inside a polygon.

        Args:
            point: (x, y) coordinates
            polygon: Polygon as numpy array

        Returns:
            True if point is inside polygon
        """
        # Ensure polygon is in correct shape for OpenCV
        poly = polygon.reshape((-1, 1, 2)) if polygon.ndim == 2 else polygon

        result = cv2.pointPolygonTest(poly, (float(point[0]), float(point[1])), False)
        return result >= 0

    @staticmethod
    def derive_stopline_from_roi(roi_polygon: Polygon, band_px: int = 8) -> Polygon:
        """Derive a stop-line band from ROI polygon.

        Creates a thin horizontal band at the bottom of the ROI polygon
        to detect vehicles crossing the stop line.

        Args:
            roi_polygon: ROI polygon points
            band_px: Width of the stop-line band in pixels

        Returns:
            Stop-line polygon as quadrilateral
        """
        points = roi_polygon.reshape(-1, 2)

        # Find all edges and select the bottommost one
        pairs = [(points[i], points[(i + 1) % len(points)]) for i in range(len(points))]
        bottommost_edge = max(pairs, key=lambda ab: (ab[0][1] + ab[1][1]) / 2.0)

        (x1, y1), (x2, y2) = bottommost_edge

        # Calculate edge vector and normal
        edge_vector = np.array([x2 - x1, y2 - y1], dtype=np.float32)
        normal = np.array([-edge_vector[1], edge_vector[0]], dtype=np.float32)
        normal = normal / (np.linalg.norm(normal) + 1e-6)

        # Ensure normal points upward (negative y direction)
        if normal[1] > 0:
            normal = -normal

        # Create quadrilateral band
        p1 = np.array([x1, y1], np.float32)
        p2 = np.array([x2, y2], np.float32)
        p3 = p2 + normal * band_px
        p4 = p1 + normal * band_px

        quad = np.stack([p1, p2, p3, p4], axis=0).astype(np.int32)
        return quad

    @staticmethod
    def draw_polygon(
        image: np.ndarray, polygon: Polygon, color: Tuple[int, int, int], thickness: int = 2
    ) -> None:
        """Draw polygon on image (modifies in place).

        Args:
            image: Image to draw on
            polygon: Polygon to draw
            color: BGR color tuple
            thickness: Line thickness
        """
        cv2.polylines(
            image, [polygon.reshape((-1, 1, 2))], isClosed=True, color=color, thickness=thickness
        )
