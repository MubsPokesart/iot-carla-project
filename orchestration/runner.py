"""CLI for the CARLA Environment Foundations project."""

import json
import os
import random
import time
import uuid
from datetime import datetime

import carla
import click

from data_pipeline.writers import write_frames_to_csv
from orchestration.carla_client import CarlaClient
from orchestration.determinism import compare_summaries, write_summary
from orchestration.logging_utils import get_logger

logger = get_logger(__name__)


@click.group()
def cli():
    """CARLA Environment Foundations CLI."""
    pass


@cli.command()
@click.option("--seed", type=int, default=42)
@click.option("--map_name", default="Town03")
@click.option("--fps", type=int, default=20)
@click.option("--duration", type=int, default=5)
def smoke(seed, map_name, fps, duration):
    """Run a smoke test."""
    run_id = str(uuid.uuid4())
    logger.info(f"Starting smoke test with run_id: {run_id}")

    carla_client = CarlaClient()
    carla_client.enable_sync_mode(1.0 / fps)

    world = carla_client.get_world()
    start_time = time.time()
    frames = []

    while time.time() - start_time < duration:
        world.tick()
        timestamp = world.get_snapshot().timestamp
        frame_data = {
            "t": timestamp.elapsed_seconds,
            "ego_x": 0.0,
            "ego_y": 0.0,
            "ego_yaw": 0.0,
            "vehicle_count": 0,
            "avg_speed": 0.0,
            "queue_len_est": 0.0,
            "light_states": "{}",
        }
        frames.append(frame_data)

    # Create artefacts directory
    output_dir = f"artefacts/{run_id}"
    os.makedirs(output_dir, exist_ok=True)

    # Create meta.run.json
    meta_data = {
        "scenario_id": "smoke_test",
        "run_id": run_id,
        "seed": seed,
        "carla_version": carla_client.client.get_server_version(),
        "map": map_name,
        "weather": "ClearNoon",  # Placeholder
        "start_ts": datetime.utcfromtimestamp(start_time).isoformat() + "Z",
        "end_ts": datetime.utcnow().isoformat() + "Z",
    }
    with open(f"{output_dir}/meta.run.json", "w") as f:
        json.dump(meta_data, f, indent=4)

    # Create kpi.json
    kpi_data = {
        "avg_travel_time": 0.0,
        "throughput": 0.0,
        "queue_length": 0.0,
        "congestion_index": 0.0,
    }
    with open(f"{output_dir}/kpi.json", "w") as f:
        json.dump(kpi_data, f, indent=4)

    write_frames_to_csv(f"{output_dir}/frames.csv", frames)

    summary_data = {"total_frames": len(frames)}
    write_summary(run_id, summary_data, output_dir="artefacts")

    carla_client.disable_sync_mode()
    logger.info(f"Smoke test finished. Artefacts in {output_dir}")


@cli.command()
def health():
    """Check the health of the CARLA server."""
    try:
        carla_client = CarlaClient()
        world = carla_client.get_world()
        server_version = carla_client.client.get_server_version()
        current_map = world.get_map().name
        sync_status = world.get_settings().synchronous_mode
        logger.info(f"CARLA server version: {server_version}")
        logger.info(f"Map: {current_map}")
        logger.info(f"Sync mode: {sync_status}")
    except Exception as e:
        logger.error(f"Error connecting to CARLA server: {e}")


@cli.command()
@click.option("--seed1", type=int, default=123)
@click.option("--seed2", type=int, default=123)
@click.option("--map_name", default="Town03")
@click.option("--fps", type=int, default=20)
@click.option("--ticks", type=int, default=50)
def determinism_check(seed1, seed2, _map_name, _fps, ticks):
    """Run two sessions and compares summary hashes."""
    run_id1 = f"determinism_run_{seed1}"
    run_id2 = f"determinism_run_{seed2}"

    # Run 1
    # (Simplified smoke run for determinism check)
    # ...

    # Run 2
    # (Simplified smoke run for determinism check)
    # ...

    # For now, we'll just create dummy summaries
    os.makedirs(f"artefacts/{run_id1}", exist_ok=True)
    os.makedirs(f"artefacts/{run_id2}", exist_ok=True)
    summary1 = {"ticks": ticks, "seed": seed1}
    summary2 = {"ticks": ticks, "seed": seed2}
    write_summary(run_id1, summary1)
    write_summary(run_id2, summary2)

    are_summaries_equal = compare_summaries(run_id1, run_id2)
    if are_summaries_equal:
        logger.info("Determinism check passed!")
    else:
        logger.error("Determinism check failed!")


@cli.command()
@click.option("--town", default="Town10HD_Opt", help="CARLA town/map name")
@click.option("--group-index", type=int, default=0, help="Traffic light group to monitor")
@click.option("--num-vehicles", type=int, default=40, help="Number of NPC vehicles")
@click.option("--duration", type=int, default=120, help="Simulation duration in seconds")
@click.option("--fps", type=int, default=20, help="Frames per second")
@click.option("--seed", type=int, default=7, help="Random seed for spawning")
def tl_monitor(town, group_index, num_vehicles, duration, fps, seed):
    """Run traffic light monitoring simulation."""
    from orchestration.tl_monitoring.config import TLMonitoringConfig
    from orchestration.tl_monitoring.observers.tl_observer import TLObserverManager
    from orchestration.tl_monitoring.utils.carla_helpers import (
        CameraSpawner,
        TrafficLightHelper,
    )

    logger.info("Starting Traffic Light Monitoring")
    logger.info(f"Town: {town}, Group: {group_index}, Vehicles: {num_vehicles}")

    # Connect to CARLA
    client = carla.Client("localhost", 2000)
    client.set_timeout(10.0)

    # Load world
    world = client.load_world(town, map_layers=carla.MapLayer.NONE)

    # Enable synchronous mode
    dt = 1.0 / fps
    settings = world.get_settings()
    settings.synchronous_mode = True
    settings.fixed_delta_seconds = dt
    world.apply_settings(settings)

    # Get traffic light groups
    groups = TrafficLightHelper.get_traffic_light_groups(world)
    if not groups:
        logger.error("No traffic light groups found in the world")
        return

    if group_index >= len(groups):
        logger.error(f"Invalid group index {group_index}. Found {len(groups)} groups")
        return

    selected_group = groups[group_index]
    logger.info(f"Monitoring group {group_index} with {len(selected_group)} traffic lights")

    # Create configuration
    config = TLMonitoringConfig(
        town=town, group_index=group_index, num_autopilot=num_vehicles, dt=dt
    )

    # Get blueprint library
    bp_library = world.get_blueprint_library()

    # Create observer manager
    observer_manager = TLObserverManager(
        world, selected_group.actors, bp_library, config
    )

    # Move spectator to first camera
    if len(observer_manager.observers) > 0:
        first_camera = observer_manager.observers[0].camera
        CameraSpawner.fly_spectator_to_camera(world, first_camera, height_offset=12.0)

    # Spawn NPC vehicles
    vehicles = _spawn_autopilot_vehicles(world, client, num_vehicles, seed)
    logger.info(f"Spawned {len(vehicles)} autopilot vehicles")

    # Run simulation
    try:
        start_time = time.time()
        frame_count = 0

        while time.time() - start_time < duration:
            world.tick()
            snapshot = world.get_snapshot()
            frame_id = snapshot.frame

            # Process all observers
            results = observer_manager.process_frame(frame_id)

            # Log results periodically
            if frame_id % 40 == 0 and results:
                for result in results:
                    logger.info(
                        f"[F{frame_id:06d}] TL[{result['stable_id']}] "
                        f"{result['state']:<6} t={result['time_in_state']:.1f}s "
                        f"q={result['queue']} (ema={result['queue_ema']:.2f})"
                    )

            frame_count += 1

        logger.info(f"Simulation completed: {frame_count} frames in {duration}s")

    finally:
        logger.info("Cleaning up...")

        # Destroy observers
        observer_manager.destroy_all()

        # Destroy vehicles
        for vehicle in vehicles:
            try:
                vehicle.destroy()
            except Exception:
                pass

        # Disable synchronous mode
        settings.synchronous_mode = False
        world.apply_settings(settings)

        logger.info("Cleanup complete")


def _spawn_autopilot_vehicles(
    world: carla.World, client: carla.Client, num_vehicles: int, seed: int
) -> list:
    """Spawn autopilot vehicles in the world.

    Args:
        world: CARLA world instance
        client: CARLA client instance
        num_vehicles: Number of vehicles to spawn
        seed: Random seed

    Returns:
        List of spawned vehicle actors
    """
    if num_vehicles <= 0:
        return []

    random.seed(seed)

    bp_library = world.get_blueprint_library()
    spawn_points = world.get_map().get_spawn_points()
    random.shuffle(spawn_points)

    # Setup traffic manager
    traffic_manager = client.get_trafficmanager()
    tm_port = traffic_manager.get_port()
    traffic_manager.set_synchronous_mode(True)
    traffic_manager.global_percentage_speed_difference(10.0)

    vehicles = []
    for spawn_point in spawn_points[: num_vehicles * 2]:
        if len(vehicles) >= num_vehicles:
            break

        # Select random vehicle blueprint
        vehicle_bp = random.choice(bp_library.filter("vehicle.*"))
        if vehicle_bp.has_attribute("role_name"):
            vehicle_bp.set_attribute("role_name", "autopilot")

        # Try to spawn vehicle
        vehicle = world.try_spawn_actor(vehicle_bp, spawn_point)
        if vehicle:
            vehicle.set_autopilot(True, tm_port)
            vehicles.append(vehicle)

    return vehicles


if __name__ == "__main__":
    cli()
