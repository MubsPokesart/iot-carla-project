"""Tests for vehicle tracker."""

import pytest

from orchestration.tl_monitoring.vision.tracker import Track, TrackManager


class TestTrack:
    """Test Track class."""

    def test_track_initialization(self):
        """Test track is initialized correctly."""
        bbox = (10, 20, 50, 80)
        track = Track(track_id=1, bbox=bbox)

        assert track.id == 1
        assert track.box == bbox
        assert track.centroid == (30.0, 50.0)
        assert track.speed_px == 0.0
        assert track.age == 1
        assert track.missed_detections == 0

    def test_track_update(self):
        """Test track updates with new detection."""
        bbox1 = (10, 20, 50, 80)
        track = Track(track_id=1, bbox=bbox1)

        bbox2 = (15, 25, 55, 85)
        track.update(bbox2, dt=0.1)

        assert track.box == bbox2
        assert track.centroid == (35.0, 55.0)
        assert track.speed_px > 0
        assert track.missed_detections == 0

    def test_track_to_dict(self):
        """Test track converts to dictionary."""
        bbox = (10, 20, 50, 80)
        track = Track(track_id=1, bbox=bbox)
        track_dict = track.to_dict()

        assert track_dict["id"] == 1
        assert track_dict["box"] == bbox
        assert "centroid" in track_dict
        assert "speed_px" in track_dict


class TestTrackManager:
    """Test TrackManager class."""

    def test_manager_initialization(self):
        """Test manager is initialized correctly."""
        manager = TrackManager()

        assert len(manager.tracks) == 0
        assert manager.next_id == 1

    def test_create_new_tracks(self):
        """Test creating new tracks from detections."""
        manager = TrackManager()
        detections = [(10, 20, 50, 80), (100, 120, 150, 180)]

        tracks = manager.update(detections, dt=0.1)

        assert len(tracks) == 2
        assert 1 in tracks
        assert 2 in tracks

    def test_update_existing_tracks(self):
        """Test updating existing tracks with new detections."""
        manager = TrackManager()

        # First frame
        detections1 = [(10, 20, 50, 80)]
        tracks1 = manager.update(detections1, dt=0.1)
        assert len(tracks1) == 1

        # Second frame - similar detection
        detections2 = [(12, 22, 52, 82)]
        tracks2 = manager.update(detections2, dt=0.1)

        # Should still have only 1 track (updated)
        assert len(tracks2) == 1
        assert 1 in tracks2

    def test_remove_old_tracks(self):
        """Test old tracks are removed."""
        manager = TrackManager(max_age=2)

        # Create track
        detections = [(10, 20, 50, 80)]
        manager.update(detections, dt=0.1)

        # Update without matching detection for 3 frames
        for _ in range(3):
            tracks = manager.update([], dt=0.1)

        # Track should be removed
        assert len(tracks) == 0

    def test_compute_iou(self):
        """Test IoU computation."""
        bbox1 = (0, 0, 10, 10)
        bbox2 = (5, 5, 15, 15)

        iou = TrackManager._compute_iou(bbox1, bbox2)

        assert 0 < iou < 1
        assert iou == pytest.approx(0.142857, rel=1e-3)

    def test_track_count(self):
        """Test getting track count."""
        manager = TrackManager()
        detections = [(10, 20, 50, 80), (100, 120, 150, 180)]

        manager.update(detections, dt=0.1)
        assert manager.get_track_count() == 2

    def test_clear_tracks(self):
        """Test clearing all tracks."""
        manager = TrackManager()
        detections = [(10, 20, 50, 80), (100, 120, 150, 180)]

        manager.update(detections, dt=0.1)
        assert manager.get_track_count() == 2

        manager.clear()
        assert manager.get_track_count() == 0
        assert manager.next_id == 1
