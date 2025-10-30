# Troubleshooting

This document provides solutions to common problems.

## `carla` module not found

If you get an error like `ModuleNotFoundError: No module named 'carla'`, it means the CARLA Python API is not installed correctly.

**Solution:**

1.  Make sure you have installed the correct version of the `carla` Python package that matches your CARLA Simulator version.
2.  You can find the Python wheel file in the `PythonAPI` directory of your CARLA installation.
3.  Install it using pip: `pip install <path-to-carla-wheel-file>`.

## Connection refused error when running health check

If you get a "connection refused" error, it means the script could not connect to the CARLA Simulator.

**Solution:**

1.  Make sure the CARLA Simulator is running.
2.  Check the host and port in `orchestration/carla_client.py` and make sure they match your CARLA Simulator configuration.
