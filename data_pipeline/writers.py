"""CSV writing utilities for frame data."""

import csv


def write_frames_to_csv(filepath, frames):
    """Write a list of frame data to a CSV file."""
    with open(filepath, "w", newline="") as csvfile:
        if not frames:
            return
        writer = csv.DictWriter(csvfile, fieldnames=frames[0].keys())
        writer.writeheader()
        writer.writerows(frames)
