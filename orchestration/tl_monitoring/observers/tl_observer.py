"""Traffic Light Observer for monitoring traffic flow at intersections."""

import os
import time
from pathlib import Path
from queue import Empty, Queue
from typing import Optional, Tuple

import carla
import cv2
import numpy as np

from orchestration.tl_monitoring.config import (
    STOP_SPEED_PX_THRESHOLD,
    STRIPE_CONFIRM_FRAMES,
    TLMonitoringConfig,
)
from orchestration.tl_monitoring.log.tl_logger import TLMetricsLogger
from orchestration.tl_monitoring.utils.carla_helpers import (
    CameraSpawner,
    TrafficLightHelper,
)
from orchestration.tl_monitoring.utils.roi import ROIManager
from orchestration.tl_monitoring.vision.detector import VehicleDetector
from orchestration.tl_monitoring.vision.tracker import TrackManager


class TLObserver:
    """Observes and monitors a single traffic light."""

    def __init__(
        self,
        world: carla.World,
        tl_actor: carla.TrafficLight,
        blueprint_library: carla.BlueprintLibrary,
        config: TLMonitoringConfig,
    ):
        """Initialize traffic light observer.

        Args:
            world: CARLA world instance
            tl_actor: Traffic light actor to monitor
            blueprint_library: CARLA blueprint library
            config: Monitoring configuration
        """
        self.world = world
        self.tl_actor = tl_actor
        self.config = config

        # Generate stable ID for this traffic light
        self.stable_id = TrafficLightHelper.get_stable_id(world, tl_actor)

        # Setup output directory
        self.save_dir = os.path.join(
            config.save_root, config.town, f"tl_{self.stable_id}"
        )
        Path(self.save_dir).mkdir(parents=True, exist_ok=True)

        # Spawn camera
        self.camera = CameraSpawner.spawn_tl_camera(
            world,
            tl_actor,
            blueprint_library,
            resolution=config.resolution,
            fov=config.cam_fov,
        )

        # Setup camera queue for synchronous image retrieval
        self.image_queue: Queue = Queue()
        self.camera.listen(self.image_queue.put)

        # Load or initialize ROI polygons
        self.roi_path = os.path.join(self.save_dir, "roi.json")
        self.stopline_path = os.path.join(self.save_dir, "stopline.json")

        self.roi_polygon = ROIManager.load_polygon(self.roi_path)
        self.stopline_polygon = ROIManager.load_polygon(self.stopline_path)

        if self.roi_polygon is None:
            print(
                f"[WARN] No ROI for TL {self.stable_id}. "
                "Annotate a saved frame with scripts/roi_annotator.py"
            )

        if self.stopline_polygon is None and self.roi_polygon is not None:
            self.stopline_polygon = ROIManager.derive_stopline_from_roi(self.roi_polygon)
            ROIManager.save_polygon(
                self.stopline_path, self.stopline_polygon.tolist()
            )

        # Initialize detection and tracking
        self.detector = VehicleDetector(config.yolo_model)
        self.tracker = TrackManager()

        # Initialize logger
        self.logger = TLMetricsLogger(self.save_dir, tl_actor, config.dt)

        # Draw debug visualization
        CameraSpawner.draw_camera_ray(world, self.camera)

        print(f"[TLObserver] Initialized TL {self.stable_id} → {self.save_dir}")

    def destroy(self) -> None:
        """Clean up resources."""
        for cleanup_func in (self.camera.stop, self.camera.destroy, self.logger.close):
            try:
                cleanup_func()
            except Exception:
                pass

    @staticmethod
    def _compute_centroid(bbox: Tuple[int, int, int, int]) -> Tuple[int, int]:
        """Compute centroid of bounding box.

        Args:
            bbox: Bounding box (x1, y1, x2, y2)

        Returns:
            Centroid coordinates (cx, cy)
        """
        x1, y1, x2, y2 = bbox
        return (int((x1 + x2) / 2), int((y1 + y2) / 2))

    def _retrieve_image(self, frame_id: int) -> Optional[np.ndarray]:
        """Retrieve camera image for the given frame.

        Args:
            frame_id: Frame number to retrieve

        Returns:
            BGR image array or None if not available
        """
        try:
            # Retrieve images until we get the matching frame
            while True:
                event = self.image_queue.get(timeout=1.0)
                if event.frame == frame_id:
                    height, width = event.height, event.width
                    raw_data = np.frombuffer(event.raw_data, dtype=np.uint8)
                    image = raw_data.reshape((height, width, 4))[:, :, :3].copy()
                    return image
        except Empty:
            return None

    def process_frame(self, frame_id: int) -> Optional[dict]:
        """Process a single frame and update metrics.

        Args:
            frame_id: Frame number to process

        Returns:
            Dictionary with monitoring results or None if failed
        """
        # Retrieve camera image
        image = self._retrieve_image(frame_id)
        if image is None:
            return None

        # Save raw frame periodically
        if frame_id % self.config.save_every_n == 0:
            frame_path = os.path.join(self.save_dir, f"frame_{frame_id:06d}.png")
            cv2.imwrite(frame_path, image)

        # Update traffic light state timer
        self.logger.update_state_timer(self.config.dt)

        # Detect and track vehicles
        detections = self.detector.detect(image)
        tracks = self.tracker.update(detections, self.config.dt)

        # Analyze queue and crossings
        queue_count = 0
        waiting_times = []
        crossings = 0

        current_time = time.time()

        for track_id, track in list(tracks.items()):
            bbox = track["box"]
            cx, cy = self._compute_centroid(bbox)
            speed_px = track["speed_px"]

            # Check if vehicle is in ROI and stopped
            in_roi = (
                self.roi_polygon is not None
                and ROIManager.point_in_polygon((cx, cy), self.roi_polygon)
            )
            is_stopped = speed_px < STOP_SPEED_PX_THRESHOLD

            # Update queue status
            if in_roi and is_stopped:
                queue_count += 1

                if not track["in_queue"]:
                    track["in_queue"] = True
                    if track["first_queue_time"] is None:
                        track["first_queue_time"] = current_time
                        self.logger.log_arrival()

                if track["first_queue_time"] is not None:
                    wait_time = max(0.0, current_time - track["first_queue_time"])
                    waiting_times.append(wait_time)
            else:
                if track["in_queue"] and track["first_queue_time"] is not None:
                    wait_time = max(0.0, current_time - track["first_queue_time"])
                    waiting_times.append(wait_time)

            # Check for stop-line crossing
            in_stopline = (
                self.stopline_polygon is not None
                and ROIManager.point_in_polygon((cx, cy), self.stopline_polygon)
            )

            if in_stopline:
                track["in_stripe_frames"] = min(999, track["in_stripe_frames"] + 1)
            else:
                # Vehicle left stopline after being in it long enough
                if (
                    track["in_stripe_frames"] >= STRIPE_CONFIRM_FRAMES
                    and track["in_queue"]
                    and not track.get("crossed", False)
                ):
                    if track["first_queue_time"] is not None:
                        wait_time = max(0.0, current_time - track["first_queue_time"])
                        self.logger.log_crossing(frame_id, track["id"], wait_time)

                    track["crossed"] = True
                    track["in_queue"] = False
                    track["first_queue_time"] = None
                    crossings += 1

                track["in_stripe_frames"] = 0

            # Draw visualization
            color = (0, 255, 0) if in_roi else (0, 0, 255)
            x1, y1, x2, y2 = bbox
            cv2.rectangle(image, (x1, y1), (x2, y2), color, 2)
            cv2.circle(image, (cx, cy), 3, color, -1)

        # Draw ROI polygons
        if self.roi_polygon is not None:
            ROIManager.draw_polygon(image, self.roi_polygon, (0, 255, 255))

        if self.stopline_polygon is not None:
            ROIManager.draw_polygon(image, self.stopline_polygon, (255, 255, 0))

        # Log metrics
        self.logger.log_tick(frame_id, queue_count, waiting_times, crossings)

        # Save visualization periodically
        if frame_id % self.config.save_every_n == 0:
            vis_path = os.path.join(self.save_dir, f"vis_{frame_id:06d}.png")
            cv2.imwrite(vis_path, image)

        # Return monitoring results
        return {
            "frame": frame_id,
            "stable_id": self.stable_id,
            "state": self.logger.last_state,
            "time_in_state": self.logger.time_in_state,
            "queue": queue_count,
            "queue_ema": self.logger.queue_ema,
        }


class TLObserverManager:
    """Manages multiple traffic light observers."""

    def __init__(
        self,
        world: carla.World,
        traffic_lights: list[carla.TrafficLight],
        blueprint_library: carla.BlueprintLibrary,
        config: TLMonitoringConfig,
    ):
        """Initialize observer manager.

        Args:
            world: CARLA world instance
            traffic_lights: List of traffic lights to monitor
            blueprint_library: CARLA blueprint library
            config: Monitoring configuration
        """
        self.observers = [
            TLObserver(world, tl, blueprint_library, config) for tl in traffic_lights
        ]

    def process_frame(self, frame_id: int) -> list[dict]:
        """Process frame for all observers.

        Args:
            frame_id: Frame number to process

        Returns:
            List of results from all observers
        """
        results = []
        for observer in self.observers:
            try:
                result = observer.process_frame(frame_id)
                if result:
                    results.append(result)
            except Exception as e:
                print(f"[ERROR] Observer {observer.stable_id}: {e}")
        return results

    def destroy_all(self) -> None:
        """Destroy all observers."""
        for observer in self.observers:
            try:
                observer.destroy()
            except Exception:
                pass

    def __len__(self) -> int:
        """Get number of observers."""
        return len(self.observers)
