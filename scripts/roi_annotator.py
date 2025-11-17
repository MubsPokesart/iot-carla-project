#!/usr/bin/env python3
"""Interactive ROI annotation tool for traffic light monitoring.

This tool allows users to manually annotate Region of Interest (ROI) polygons
on traffic light camera frames by clicking points on the image.
"""

import json
import os
import sys
from pathlib import Path

import cv2
import numpy as np


class ROIAnnotator:
    """Interactive tool for annotating ROI polygons on images."""

    def __init__(self, image_path: str, save_json_path: str):
        """Initialize the annotator.

        Args:
            image_path: Path to image to annotate
            save_json_path: Path to save ROI JSON file
        """
        self.image_path = image_path
        self.save_json_path = save_json_path

        # Load image
        self.original_image = cv2.imread(image_path)
        if self.original_image is None:
            raise RuntimeError(f"Cannot open image: {image_path}")

        self.current_image = self.original_image.copy()
        self.points = []
        self.window_name = "ROI Annotator"

    def _redraw(self) -> None:
        """Redraw the image with current polygon."""
        self.current_image = self.original_image.copy()

        # Draw points
        for i, (x, y) in enumerate(self.points):
            cv2.circle(self.current_image, (x, y), 5, (0, 255, 0), -1)

            # Draw connecting lines
            if i > 0:
                prev_x, prev_y = self.points[i - 1]
                cv2.line(self.current_image, (prev_x, prev_y), (x, y), (0, 255, 0), 2)

        # Draw completed polygon
        if len(self.points) >= 3:
            poly_points = np.array(self.points, np.int32).reshape((-1, 1, 2))
            cv2.polylines(
                self.current_image, [poly_points], isClosed=True, color=(0, 255, 255), thickness=2
            )

        cv2.imshow(self.window_name, self.current_image)

    def _on_mouse_click(self, event, x, y, flags, param) -> None:
        """Handle mouse click events.

        Args:
            event: Mouse event type
            x: X coordinate
            y: Y coordinate
            flags: Additional flags
            param: User data (unused)
        """
        if event == cv2.EVENT_LBUTTONDOWN:
            self.points.append([x, y])
            self._redraw()

    def annotate(self) -> None:
        """Run the interactive annotation loop."""
        cv2.imshow(self.window_name, self.current_image)
        cv2.setMouseCallback(self.window_name, self._on_mouse_click)

        print("\n=== ROI Annotator ===")
        print(f"Image: {self.image_path}")
        print("\nInstructions:")
        print("  - Left-click to add points")
        print("  - Press 's' to save")
        print("  - Press 'r' to reset")
        print("  - Press 'q' to quit without saving")
        print("  - Press 'u' to undo last point")
        print("\nNeed at least 3 points to form a polygon.\n")

        while True:
            key = cv2.waitKey(20) & 0xFF

            if key == ord("r"):
                # Reset points
                self.points = []
                self._redraw()
                print("Reset polygon")

            elif key == ord("u"):
                # Undo last point
                if self.points:
                    self.points.pop()
                    self._redraw()
                    print(f"Undone. Points: {len(self.points)}")

            elif key == ord("s"):
                # Save polygon
                if len(self.points) >= 3:
                    self._save_polygon()
                    print(f"\nSaved ROI with {len(self.points)} points → {self.save_json_path}")
                    break
                else:
                    print("Need at least 3 points to save!")

            elif key == ord("q"):
                print("\nQuit without saving")
                break

        cv2.destroyAllWindows()

    def _save_polygon(self) -> None:
        """Save the annotated polygon to JSON file."""
        # Create directory if it doesn't exist
        Path(self.save_json_path).parent.mkdir(parents=True, exist_ok=True)

        # Save to JSON
        data = {"polygon": self.points}
        with open(self.save_json_path, "w") as f:
            json.dump(data, f, indent=2)


def main():
    """Main entry point for the ROI annotator tool."""
    if len(sys.argv) not in (2, 3):
        print("Usage: python scripts/roi_annotator.py <image_path> [<save_json_path>]")
        print("\nExample:")
        print("  python scripts/roi_annotator.py outputs/Town03/tl_road1_lane2_s100/frame_000000.png")
        print("  python scripts/roi_annotator.py frame.png roi.json")
        sys.exit(1)

    image_path = sys.argv[1]

    # Default save path is roi.json in the same directory as the image
    if len(sys.argv) == 3:
        save_path = sys.argv[2]
    else:
        image_dir = os.path.dirname(image_path)
        save_path = os.path.join(image_dir, "roi.json")

    try:
        annotator = ROIAnnotator(image_path, save_path)
        annotator.annotate()
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
