"""Logger for traffic light monitoring metrics and events."""

import csv
import os
from pathlib import Path
from typing import List, Optional

import carla
import numpy as np

from orchestration.tl_monitoring.config import (
    EMA_ALPHA_ARRIVAL,
    EMA_ALPHA_DISCHARGE,
    EMA_ALPHA_QUEUE,
)


class TLMetricsLogger:
    """Logs traffic light monitoring metrics to CSV files."""

    def __init__(self, save_dir: str, tl_actor: carla.TrafficLight, dt: float):
        """Initialize metrics logger.

        Args:
            save_dir: Directory to save log files
            tl_actor: Traffic light actor being monitored
            dt: Time delta between ticks (seconds)
        """
        self.save_dir = save_dir
        self.tl_actor = tl_actor
        self.dt = dt

        # Create output directory
        Path(save_dir).mkdir(parents=True, exist_ok=True)

        # Initialize CSV files
        self._init_csv_files()

        # Exponential moving averages
        self.queue_ema = 0.0
        self.arrival_ema = 0.0
        self.discharge_ema = 0.0

        # State tracking
        self.last_state: Optional[str] = None
        self.time_in_state = 0.0
        self.total_time = 0.0

        # Event counters
        self.recent_arrivals = 0
        self.recent_discharges = 0
        self._sec_accumulator = 0.0

    def _init_csv_files(self) -> None:
        """Initialize CSV files for logging."""
        # Ticks log (per-frame metrics)
        self.tick_csv = open(os.path.join(self.save_dir, "ticks.csv"), "w", newline="")
        self.tick_writer = csv.writer(self.tick_csv)
        self.tick_writer.writerow([
            "t_sec",
            "frame",
            "state",
            "time_in_state",
            "queue_count",
            "queue_ema",
            "avg_wait",
            "max_wait",
            "num_long_wait_60s",
            "arrival_ema",
            "discharge_ema",
        ])

        # Crossings log (per-vehicle crossing events)
        self.cross_csv = open(
            os.path.join(self.save_dir, "crossings.csv"), "w", newline=""
        )
        self.cross_writer = csv.writer(self.cross_csv)
        self.cross_writer.writerow(["t_sec", "frame", "track_id", "wait_time_sec"])

    def get_state_name(self) -> str:
        """Get current traffic light state name.

        Returns:
            State name as string
        """
        try:
            return self.tl_actor.get_state().name
        except Exception:
            return str(self.tl_actor.get_state())

    def update_state_timer(self, dt: float) -> None:
        """Update the timer for current traffic light state.

        Args:
            dt: Time delta since last update
        """
        current_state = self.get_state_name()

        if current_state == self.last_state:
            self.time_in_state += dt
        else:
            self.last_state = current_state
            self.time_in_state = dt

    def log_tick(
        self,
        frame: int,
        queue_count: int,
        waiting_times: List[float],
        crossings_this_tick: int,
    ) -> None:
        """Log metrics for a single tick.

        Args:
            frame: Frame number
            queue_count: Number of vehicles in queue
            waiting_times: List of waiting times for queued vehicles
            crossings_this_tick: Number of vehicles that crossed this tick
        """
        self.total_time += self.dt
        self._sec_accumulator += self.dt

        # Update queue EMA
        self.queue_ema = (
            EMA_ALPHA_QUEUE * queue_count + (1 - EMA_ALPHA_QUEUE) * self.queue_ema
        )

        # Track discharges
        self.recent_discharges += crossings_this_tick

        # Calculate waiting time statistics
        avg_wait = float(np.mean(waiting_times)) if waiting_times else 0.0
        max_wait = float(np.max(waiting_times)) if waiting_times else 0.0
        long_waiters = sum(1 for w in waiting_times if w >= 60.0)

        # Update arrival and discharge EMAs (per second)
        if self._sec_accumulator >= 1.0 - 1e-6:
            discharge_rate = self.recent_discharges / self._sec_accumulator
            arrival_rate = self.recent_arrivals / self._sec_accumulator

            self.discharge_ema = (
                EMA_ALPHA_DISCHARGE * discharge_rate
                + (1 - EMA_ALPHA_DISCHARGE) * self.discharge_ema
            )
            self.arrival_ema = (
                EMA_ALPHA_ARRIVAL * arrival_rate
                + (1 - EMA_ALPHA_ARRIVAL) * self.arrival_ema
            )

            self.recent_arrivals = 0
            self.recent_discharges = 0
            self._sec_accumulator = 0.0

        # Write to CSV
        self.tick_writer.writerow([
            round(self.total_time, 3),
            frame,
            self.last_state,
            round(self.time_in_state, 3),
            int(queue_count),
            round(self.queue_ema, 3),
            round(avg_wait, 3),
            round(max_wait, 3),
            int(long_waiters),
            round(self.arrival_ema, 3),
            round(self.discharge_ema, 3),
        ])

    def log_crossing(self, frame: int, track_id: int, wait_time: float) -> None:
        """Log a vehicle crossing event.

        Args:
            frame: Frame number
            track_id: Track ID of the vehicle
            wait_time: Total waiting time in seconds
        """
        self.cross_writer.writerow([
            round(self.total_time, 3),
            frame,
            track_id,
            round(wait_time, 3),
        ])

    def log_arrival(self) -> None:
        """Log a vehicle arrival to the queue."""
        self.recent_arrivals += 1

    def get_metrics(self) -> dict:
        """Get current metrics snapshot.

        Returns:
            Dictionary of current metrics
        """
        return {
            "total_time": self.total_time,
            "state": self.last_state,
            "time_in_state": self.time_in_state,
            "queue_ema": self.queue_ema,
            "arrival_ema": self.arrival_ema,
            "discharge_ema": self.discharge_ema,
        }

    def close(self) -> None:
        """Close all log files."""
        for file_handle in (self.tick_csv, self.cross_csv):
            try:
                file_handle.close()
            except Exception as e:
                print(f"[WARN] Failed to close log file: {e}")
