"""Tests for ROI utilities."""

import json
import tempfile
from pathlib import Path

import numpy as np
import pytest

from orchestration.tl_monitoring.utils.roi import ROIManager


class TestROIManager:
    """Test ROIManager class."""

    def test_load_polygon_success(self):
        """Test loading polygon from JSON file."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump({"polygon": [[10, 20], [30, 40], [50, 60]]}, f)
            temp_path = f.name

        try:
            polygon = ROIManager.load_polygon(temp_path)
            assert polygon is not None
            assert polygon.shape == (3, 2)
            assert np.array_equal(polygon, [[10, 20], [30, 40], [50, 60]])
        finally:
            Path(temp_path).unlink()

    def test_load_polygon_not_found(self):
        """Test loading polygon from non-existent file."""
        polygon = ROIManager.load_polygon("nonexistent.json")
        assert polygon is None

    def test_load_polygon_invalid(self):
        """Test loading polygon with too few points."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump({"polygon": [[10, 20]]}, f)
            temp_path = f.name

        try:
            polygon = ROIManager.load_polygon(temp_path)
            assert polygon is None
        finally:
            Path(temp_path).unlink()

    def test_save_polygon(self):
        """Test saving polygon to JSON file."""
        with tempfile.TemporaryDirectory() as temp_dir:
            save_path = Path(temp_dir) / "roi.json"
            polygon = [[10, 20], [30, 40], [50, 60]]

            ROIManager.save_polygon(str(save_path), polygon)

            assert save_path.exists()

            with open(save_path) as f:
                data = json.load(f)

            assert data["polygon"] == polygon

    def test_point_in_polygon_inside(self):
        """Test point inside polygon."""
        # Square polygon
        polygon = np.array([[0, 0], [100, 0], [100, 100], [0, 100]], dtype=np.int32)
        point = (50, 50)

        assert ROIManager.point_in_polygon(point, polygon) is True

    def test_point_in_polygon_outside(self):
        """Test point outside polygon."""
        polygon = np.array([[0, 0], [100, 0], [100, 100], [0, 100]], dtype=np.int32)
        point = (150, 150)

        assert ROIManager.point_in_polygon(point, polygon) is False

    def test_point_in_polygon_on_edge(self):
        """Test point on polygon edge."""
        polygon = np.array([[0, 0], [100, 0], [100, 100], [0, 100]], dtype=np.int32)
        point = (50, 0)

        result = ROIManager.point_in_polygon(point, polygon)
        assert result is True

    def test_derive_stopline_from_roi(self):
        """Test deriving stopline from ROI polygon."""
        # Rectangle polygon
        roi = np.array([[0, 0], [100, 0], [100, 100], [0, 100]], dtype=np.int32)

        stopline = ROIManager.derive_stopline_from_roi(roi, band_px=10)

        assert stopline.shape == (4, 2)
        assert stopline.dtype == np.int32

    def test_derive_stopline_custom_band(self):
        """Test deriving stopline with custom band width."""
        roi = np.array([[0, 0], [100, 0], [100, 100], [0, 100]], dtype=np.int32)

        stopline = ROIManager.derive_stopline_from_roi(roi, band_px=20)

        assert stopline.shape == (4, 2)

    def test_draw_polygon(self):
        """Test drawing polygon on image."""
        # Create blank image
        image = np.zeros((200, 200, 3), dtype=np.uint8)
        polygon = np.array([[50, 50], [150, 50], [150, 150], [50, 150]], dtype=np.int32)

        # Should not raise exception
        ROIManager.draw_polygon(image, polygon, (0, 255, 0), thickness=2)

        # Check that image was modified (not all zeros)
        assert np.any(image > 0)
