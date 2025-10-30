"""CARLA client for the CARLA Environment Foundations project."""

import carla


class CarlaClient:
    """A client for interacting with the CARLA simulator."""

    def __init__(self, host="localhost", port=2000, timeout=10.0):
        """Initialize the CARLA client."""
        self.client = carla.Client(host, port)
        self.client.set_timeout(timeout)
        self.world = self.client.get_world()

    def enable_sync_mode(self, fixed_delta_seconds=0.05):
        """Enable synchronous mode in the CARLA simulator."""
        settings = self.world.get_settings()
        settings.synchronous_mode = True
        settings.fixed_delta_seconds = fixed_delta_seconds
        self.world.apply_settings(settings)

    def disable_sync_mode(self):
        """Disable synchronous mode in the CARLA simulator."""
        settings = self.world.get_settings()
        settings.synchronous_mode = False
        settings.fixed_delta_seconds = None
        self.world.apply_settings(settings)

    def get_world(self):
        """Get the CARLA world."""
        return self.world

    def tick(self):
        """Tick the CARLA world."""
        return self.world.tick()
