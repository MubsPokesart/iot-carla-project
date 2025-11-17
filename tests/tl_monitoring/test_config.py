"""Tests for TL monitoring configuration."""

from orchestration.tl_monitoring.config import (
    DEFAULT_TOWN,
    TLMonitoringConfig,
    VEHICLE_CLASSES,
)


class TestTLMonitoringConfig:
    """Test TLMonitoringConfig class."""

    def test_config_initialization_defaults(self):
        """Test config initialization with default values."""
        config = TLMonitoringConfig()

        assert config.town == DEFAULT_TOWN
        assert config.group_index == 0
        assert config.num_autopilot == 40
        assert config.dt == 0.05
        assert config.resolution == (1280, 720)
        assert config.cam_fov == 70
        assert config.save_root == "outputs"
        assert config.save_every_n == 10
        assert config.yolo_model == "yolo11n.pt"

    def test_config_initialization_custom(self):
        """Test config initialization with custom values."""
        config = TLMonitoringConfig(
            town="Town03",
            group_index=1,
            num_autopilot=20,
            dt=0.1,
            resolution=(640, 480),
            cam_fov=90,
            save_root="my_outputs",
            save_every_n=5,
            yolo_model="yolo11s.pt",
        )

        assert config.town == "Town03"
        assert config.group_index == 1
        assert config.num_autopilot == 20
        assert config.dt == 0.1
        assert config.resolution == (640, 480)
        assert config.cam_fov == 90
        assert config.save_root == "my_outputs"
        assert config.save_every_n == 5
        assert config.yolo_model == "yolo11s.pt"

    def test_config_to_dict(self):
        """Test converting config to dictionary."""
        config = TLMonitoringConfig(town="Town05", group_index=2)
        config_dict = config.to_dict()

        assert isinstance(config_dict, dict)
        assert config_dict["town"] == "Town05"
        assert config_dict["group_index"] == 2
        assert "dt" in config_dict
        assert "resolution" in config_dict
        assert "yolo_model" in config_dict

    def test_vehicle_classes_constant(self):
        """Test vehicle classes constant."""
        assert "car" in VEHICLE_CLASSES
        assert "truck" in VEHICLE_CLASSES
        assert "bus" in VEHICLE_CLASSES
        assert len(VEHICLE_CLASSES) >= 5
