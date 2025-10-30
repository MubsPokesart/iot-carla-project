"""Flask API for the CARLA Environment Foundations project."""

import subprocess
import uuid

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


if __name__ == "__main__":
    app.run(debug=True, port=5001)
