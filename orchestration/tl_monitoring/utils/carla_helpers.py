"""CARLA-specific helper functions for traffic light monitoring."""

import math
from typing import List, Optional

import carla

from orchestration.tl_monitoring.config import DEFAULT_CAM_FOV, DEFAULT_RES


class TrafficLightGroup:
    """Represents a group of related traffic lights."""

    def __init__(self, group_id: int, actors: List[carla.TrafficLight]):
        """Initialize traffic light group.

        Args:
            group_id: Unique identifier for this group
            actors: List of traffic light actors in this group
        """
        self.group_id = group_id
        self.actors = actors
        self.representative = actors[0] if actors else None

    def __len__(self) -> int:
        """Get number of traffic lights in group."""
        return len(self.actors)

    def __repr__(self) -> str:
        """String representation of group."""
        return f"TrafficLightGroup(id={self.group_id}, count={len(self)})"


class TrafficLightHelper:
    """Helper class for traffic light operations in CARLA."""

    @staticmethod
    def get_traffic_light_groups(world: carla.World) -> List[TrafficLightGroup]:
        """Get all traffic light groups in the world.

        Args:
            world: CARLA world instance

        Returns:
            List of TrafficLightGroup objects
        """
        groups = []
        seen_ids = set()

        traffic_lights = world.get_actors().filter("traffic.traffic_light*")

        for tl in traffic_lights:
            group_lights = tl.get_group_traffic_lights() or [tl]
            group_key = frozenset(light.id for light in group_lights)

            if group_key in seen_ids:
                continue

            seen_ids.add(group_key)
            group_id = len(groups)
            groups.append(TrafficLightGroup(group_id, list(group_lights)))

        # Sort by minimum ID for consistency
        groups.sort(key=lambda g: min(light.id for light in g.actors))

        return groups

    @staticmethod
    def get_tl_center(tl: carla.TrafficLight) -> carla.Location:
        """Get the center location of a traffic light.

        Args:
            tl: Traffic light actor

        Returns:
            Center location of the traffic light
        """
        transform = tl.get_transform()
        trigger_volume = getattr(tl, "trigger_volume", None) or (
            tl.get_trigger_volume() if hasattr(tl, "get_trigger_volume") else None
        )

        if trigger_volume and getattr(trigger_volume, "location", None):
            return transform.transform(trigger_volume.location)

        return transform.location

    @staticmethod
    def get_stable_id(world: carla.World, tl: carla.TrafficLight) -> str:
        """Generate a stable, deterministic ID for a traffic light.

        Uses road ID, lane ID, and distance along the road to create
        a consistent identifier across simulation runs.

        Args:
            world: CARLA world instance
            tl: Traffic light actor

        Returns:
            Stable string identifier
        """
        carla_map = world.get_map()
        center = TrafficLightHelper.get_tl_center(tl)

        waypoint = carla_map.get_waypoint(
            center, project_to_road=True, lane_type=carla.LaneType.Driving
        )

        # Use s-coordinate if available, otherwise use distance
        s_value = getattr(waypoint, "s", None)
        if s_value is not None:
            s_index = int(round(float(s_value) * 100))
        else:
            distance = waypoint.transform.location.distance(center)
            s_index = int(round(distance * 100))

        return f"road{waypoint.road_id}_lane{waypoint.lane_id}_s{s_index}"


class CameraSpawner:
    """Handles camera spawning for traffic light monitoring."""

    @staticmethod
    def _forward_vector(yaw_degrees: float) -> carla.Vector3D:
        """Calculate forward vector from yaw angle.

        Args:
            yaw_degrees: Yaw angle in degrees

        Returns:
            Forward direction vector
        """
        radians = math.radians(yaw_degrees)
        return carla.Vector3D(math.cos(radians), math.sin(radians), 0.0)

    @staticmethod
    def _right_vector(yaw_degrees: float) -> carla.Vector3D:
        """Calculate right vector from yaw angle.

        Args:
            yaw_degrees: Yaw angle in degrees

        Returns:
            Right direction vector
        """
        radians = math.radians(yaw_degrees + 90.0)
        return carla.Vector3D(math.cos(radians), math.sin(radians), 0.0)

    @staticmethod
    def spawn_tl_camera(
        world: carla.World,
        tl: carla.TrafficLight,
        blueprint_library: carla.BlueprintLibrary,
        back_m: float = 15.0,
        side_m: float = 1.2,
        height_m: float = 5.0,
        resolution: tuple[int, int] = DEFAULT_RES,
        fov: int = DEFAULT_CAM_FOV,
    ) -> carla.Actor:
        """Spawn camera to monitor a traffic light.

        Args:
            world: CARLA world instance
            tl: Traffic light to monitor
            blueprint_library: CARLA blueprint library
            back_m: Distance behind traffic light in meters
            side_m: Lateral offset in meters
            height_m: Height above ground in meters
            resolution: Camera resolution (width, height)
            fov: Field of view in degrees

        Returns:
            Spawned camera actor
        """
        # Configure camera blueprint
        cam_bp = blueprint_library.find("sensor.camera.rgb")
        cam_bp.set_attribute("image_size_x", str(resolution[0]))
        cam_bp.set_attribute("image_size_y", str(resolution[1]))
        cam_bp.set_attribute("fov", str(fov))

        # Get traffic light location and lane information
        carla_map = world.get_map()
        center = TrafficLightHelper.get_tl_center(tl)
        waypoint = carla_map.get_waypoint(
            center, project_to_road=True, lane_type=carla.LaneType.Driving
        )

        # Calculate camera position
        lane_yaw = waypoint.transform.rotation.yaw
        facing_yaw = (lane_yaw + 180.0) % 360.0

        fwd = CameraSpawner._forward_vector(facing_yaw)
        right = CameraSpawner._right_vector(facing_yaw)

        cam_location = carla.Location(
            center.x - fwd.x * back_m + right.x * side_m,
            center.y - fwd.y * back_m + right.y * side_m,
            center.z + height_m,
        )

        # Calculate pitch to look at traffic light
        dx = center.x - cam_location.x
        dy = center.y - cam_location.y
        dz = center.z - cam_location.z
        pitch = math.degrees(math.atan2(dz, math.hypot(dx, dy))) - fov * 0.10

        # Spawn camera
        camera_transform = carla.Transform(
            cam_location, carla.Rotation(pitch=pitch, yaw=facing_yaw, roll=0.0)
        )

        camera = world.spawn_actor(cam_bp, camera_transform)
        return camera

    @staticmethod
    def draw_camera_ray(
        world: carla.World, camera: carla.Actor, life_time: float = 6.0
    ) -> None:
        """Draw a debug arrow showing camera direction.

        Args:
            world: CARLA world instance
            camera: Camera actor
            life_time: How long to display the arrow
        """
        transform = camera.get_transform()
        fwd = CameraSpawner._forward_vector(transform.rotation.yaw)

        start = transform.location
        end = carla.Location(start.x + fwd.x * 8, start.y + fwd.y * 8, start.z + fwd.z * 8)

        world.debug.draw_arrow(
            start,
            end,
            thickness=0.08,
            arrow_size=0.3,
            color=carla.Color(0, 255, 0),
            life_time=life_time,
        )

    @staticmethod
    def fly_spectator_to_camera(
        world: carla.World, camera: carla.Actor, height_offset: float = 12.0
    ) -> None:
        """Move spectator camera above the monitoring camera.

        Args:
            world: CARLA world instance
            camera: Camera to fly to
            height_offset: Height above camera in meters
        """
        transform = camera.get_transform()
        spectator_location = carla.Location(
            transform.location.x, transform.location.y, transform.location.z + height_offset
        )

        spectator_transform = carla.Transform(
            spectator_location, carla.Rotation(pitch=-90)
        )

        world.get_spectator().set_transform(spectator_transform)
