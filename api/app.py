"""Flask API for the CARLA Environment Foundations project."""

import csv
import json
import os
import subprocess
import uuid
from pathlib import Path

from flask import Flask, jsonify, request

from orchestration.carla_client import CarlaClient

app = Flask(__name__)


@app.route("/api/health", methods=["GET"])
def health():
    """Check the health of the CARLA server."""
    try:
        carla_client = CarlaClient()
        world = carla_client.get_world()
        server_version = carla_client.client.get_server_version()
        current_map = world.get_map().name
        sync_status = world.get_settings().synchronous_mode
        return (
            jsonify(
                {
                    "carla_version": server_version,
                    "map": current_map,
                    "sync": sync_status,
                }
            ),
            200,
        )
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/run/smoke", methods=["POST"])
def run_smoke():
    """Run a smoke test."""
    data = request.get_json()
    seed = data.get("seed", 42)
    run_map = data.get("map", "Town03")
    fps = data.get("fps", 20)
    duration = data.get("duration", 5)
    run_id = str(uuid.uuid4())

    try:
        # Run smoke test in a separate process
        subprocess.Popen(
            [
                "python",
                "-m",
                "orchestration.runner",
                "smoke",
                "--seed",
                str(seed),
                "--map",
                run_map,
                "--fps",
                str(fps),
                "--duration",
                str(duration),
            ]
        )
        return jsonify({"run_id": run_id, "status": "started"})
    except Exception as e:
        return jsonify({"run_id": run_id, "status": "error", "message": str(e)}), 500


@app.route("/api/runs/<run_id>/summary", methods=["GET"])
def get_summary(run_id):
    """Get the summary of a run."""
    # This is a placeholder implementation.
    # In a real application, you would fetch the summary from a database or file system.
    summary_path = f"artefacts/{run_id}/summary.json"
    try:
        with open(summary_path) as f:
            summary_data = f.read()
        return jsonify(summary_data)
    except FileNotFoundError:
        return jsonify({"error": "Summary not found"}), 404


@app.route("/api/tl-monitor/start", methods=["POST"])
def start_tl_monitor():
    """Start a traffic light monitoring session."""
    data = request.get_json() or {}
    town = data.get("town", "Town10HD_Opt")
    group_index = data.get("group_index", 0)
    num_vehicles = data.get("num_vehicles", 40)
    duration = data.get("duration", 120)
    fps = data.get("fps", 20)
    seed = data.get("seed", 7)

    session_id = str(uuid.uuid4())

    try:
        # Run TL monitoring in a separate process
        subprocess.Popen(
            [
                "python",
                "-m",
                "orchestration.runner",
                "tl-monitor",
                "--town",
                town,
                "--group-index",
                str(group_index),
                "--num-vehicles",
                str(num_vehicles),
                "--duration",
                str(duration),
                "--fps",
                str(fps),
                "--seed",
                str(seed),
            ]
        )
        return jsonify({"session_id": session_id, "status": "started", "town": town})
    except Exception as e:
        return jsonify({"session_id": session_id, "status": "error", "message": str(e)}), 500


@app.route("/api/tl-monitor/runs", methods=["GET"])
def list_tl_monitor_runs():
    """List all traffic light monitoring runs."""
    outputs_dir = "outputs"

    if not os.path.exists(outputs_dir):
        return jsonify({"runs": []})

    runs = []
    for town_dir in Path(outputs_dir).iterdir():
        if not town_dir.is_dir():
            continue

        town_name = town_dir.name

        for tl_dir in town_dir.iterdir():
            if not tl_dir.is_dir() or not tl_dir.name.startswith("tl_"):
                continue

            tl_id = tl_dir.name
            ticks_csv = tl_dir / "ticks.csv"
            crossings_csv = tl_dir / "crossings.csv"

            if ticks_csv.exists():
                # Read last few lines to get latest metrics
                try:
                    with open(ticks_csv, "r") as f:
                        reader = csv.DictReader(f)
                        rows = list(reader)
                        if rows:
                            latest = rows[-1]
                            runs.append(
                                {
                                    "town": town_name,
                                    "tl_id": tl_id,
                                    "path": str(tl_dir),
                                    "latest_metrics": {
                                        "time": float(latest.get("t_sec", 0)),
                                        "frame": int(latest.get("frame", 0)),
                                        "state": latest.get("state", "Unknown"),
                                        "queue_count": int(latest.get("queue_count", 0)),
                                        "queue_ema": float(latest.get("queue_ema", 0)),
                                        "avg_wait": float(latest.get("avg_wait", 0)),
                                    },
                                    "has_crossings": crossings_csv.exists(),
                                }
                            )
                except Exception as e:
                    print(f"Error reading {ticks_csv}: {e}")

    return jsonify({"runs": runs})


@app.route("/api/tl-monitor/runs/<town>/<tl_id>/metrics", methods=["GET"])
def get_tl_metrics(town, tl_id):
    """Get detailed metrics for a specific traffic light."""
    tl_dir = Path("outputs") / town / tl_id

    if not tl_dir.exists():
        return jsonify({"error": "Traffic light run not found"}), 404

    ticks_csv = tl_dir / "ticks.csv"
    crossings_csv = tl_dir / "crossings.csv"

    metrics = {"tl_id": tl_id, "town": town}

    # Read tick metrics
    if ticks_csv.exists():
        try:
            with open(ticks_csv, "r") as f:
                reader = csv.DictReader(f)
                ticks = list(reader)
                metrics["ticks"] = ticks[-100:]  # Last 100 ticks
                metrics["total_ticks"] = len(ticks)
        except Exception as e:
            metrics["tick_error"] = str(e)

    # Read crossing events
    if crossings_csv.exists():
        try:
            with open(crossings_csv, "r") as f:
                reader = csv.DictReader(f)
                crossings = list(reader)
                metrics["crossings"] = crossings
                metrics["total_crossings"] = len(crossings)

                # Compute average wait time
                if crossings:
                    wait_times = [float(c.get("wait_time_sec", 0)) for c in crossings]
                    metrics["avg_crossing_wait"] = sum(wait_times) / len(wait_times)
        except Exception as e:
            metrics["crossing_error"] = str(e)

    return jsonify(metrics)


@app.route("/api/tl-monitor/runs/<town>/<tl_id>/roi", methods=["GET"])
def get_tl_roi(town, tl_id):
    """Get ROI polygon for a traffic light."""
    roi_path = Path("outputs") / town / tl_id / "roi.json"

    if not roi_path.exists():
        return jsonify({"error": "ROI not found", "has_roi": False}), 404

    try:
        with open(roi_path, "r") as f:
            roi_data = json.load(f)
        return jsonify({"has_roi": True, "roi": roi_data})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    app.run(debug=True, port=5001)
