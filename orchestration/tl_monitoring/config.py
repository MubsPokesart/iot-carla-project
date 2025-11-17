"""Configuration settings for Traffic Light Monitoring."""

from typing import Final, Set

# Simulation settings
DEFAULT_TOWN: Final[str] = "Town10HD_Opt"
DEFAULT_GROUP_INDEX: Final[int] = 0
DEFAULT_NUM_AUTOPILOT: Final[int] = 40
DEFAULT_DT: Final[float] = 0.05

# Camera settings
DEFAULT_RES: Final[tuple[int, int]] = (1280, 720)
DEFAULT_CAM_FOV: Final[int] = 70

# Output settings
DEFAULT_SAVE_ROOT: Final[str] = "outputs"
DEFAULT_SAVE_EVERY_N: Final[int] = 10

# Detection and tracking settings
DEFAULT_YOLO_MODEL: Final[str] = "yolo11n.pt"
VEHICLE_CLASSES: Final[Set[str]] = {
    "car",
    "truck",
    "bus",
    "motorbike",
    "motorcycle",
    "bicycle",
}

# Tracking parameters
IOU_MATCH_THRESHOLD: Final[float] = 0.3
TRACK_MAX_AGE: Final[int] = 20
STOP_SPEED_PX_THRESHOLD: Final[float] = 1.3
STRIPE_CONFIRM_FRAMES: Final[int] = 2

# Exponential moving average smoothing parameters
EMA_ALPHA_QUEUE: Final[float] = 0.3
EMA_ALPHA_ARRIVAL: Final[float] = 0.2
EMA_ALPHA_DISCHARGE: Final[float] = 0.2


class TLMonitoringConfig:
    """Configuration manager for TL monitoring settings."""

    def __init__(
        self,
        town: str = DEFAULT_TOWN,
        group_index: int = DEFAULT_GROUP_INDEX,
        num_autopilot: int = DEFAULT_NUM_AUTOPILOT,
        dt: float = DEFAULT_DT,
        resolution: tuple[int, int] = DEFAULT_RES,
        cam_fov: int = DEFAULT_CAM_FOV,
        save_root: str = DEFAULT_SAVE_ROOT,
        save_every_n: int = DEFAULT_SAVE_EVERY_N,
        yolo_model: str = DEFAULT_YOLO_MODEL,
    ):
        """Initialize configuration with provided or default values.

        Args:
            town: CARLA town/map name
            group_index: Traffic light group index to monitor
            num_autopilot: Number of NPC vehicles to spawn
            dt: Fixed delta seconds for synchronous mode
            resolution: Camera resolution (width, height)
            cam_fov: Camera field of view in degrees
            save_root: Root directory for saving outputs
            save_every_n: Save frames every N ticks
            yolo_model: YOLO model filename
        """
        self.town = town
        self.group_index = group_index
        self.num_autopilot = num_autopilot
        self.dt = dt
        self.resolution = resolution
        self.cam_fov = cam_fov
        self.save_root = save_root
        self.save_every_n = save_every_n
        self.yolo_model = yolo_model

    def to_dict(self) -> dict:
        """Convert configuration to dictionary.

        Returns:
            Dictionary representation of configuration
        """
        return {
            "town": self.town,
            "group_index": self.group_index,
            "num_autopilot": self.num_autopilot,
            "dt": self.dt,
            "resolution": self.resolution,
            "cam_fov": self.cam_fov,
            "save_root": self.save_root,
            "save_every_n": self.save_every_n,
            "yolo_model": self.yolo_model,
        }
