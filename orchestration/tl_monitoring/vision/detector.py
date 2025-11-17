"""Vehicle detection using YOLO model."""

from typing import List, Tuple

import numpy as np
from ultralytics import YOLO

from orchestration.tl_monitoring.config import (
    DEFAULT_YOLO_MODEL,
    VEHICLE_CLASSES,
)

BoundingBox = Tuple[int, int, int, int]  # (x1, y1, x2, y2)


class VehicleDetector:
    """Detects vehicles in images using YOLO object detection model."""

    def __init__(self, model_path: str = DEFAULT_YOLO_MODEL, device: str = "cpu"):
        """Initialize the vehicle detector.

        Args:
            model_path: Path to YOLO model file
            device: Device to run inference on ('cpu' or 'cuda')
        """
        self.model = YOLO(model_path)
        self.device = device
        self.vehicle_classes = VEHICLE_CLASSES

    def detect(self, image: np.ndarray) -> List[BoundingBox]:
        """Detect vehicles in a BGR image.

        Args:
            image: BGR image array from OpenCV

        Returns:
            List of bounding boxes (x1, y1, x2, y2) for detected vehicles
        """
        results = self.model.predict(image, verbose=False, device=self.device)

        if not results:
            return []

        detections = []
        for result in results:
            for box in result.boxes:
                class_name = result.names[int(box.cls)]

                if class_name not in self.vehicle_classes:
                    continue

                # Extract bounding box coordinates
                coords = box.xyxy[0].cpu().numpy().astype(int).tolist()
                x1, y1, x2, y2 = coords
                detections.append((x1, y1, x2, y2))

        return detections

    def set_device(self, device: str) -> None:
        """Change the inference device.

        Args:
            device: Device to use ('cpu' or 'cuda')
        """
        self.device = device
