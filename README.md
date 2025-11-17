# CARLA Environment Foundations

This project provides a foundational environment for running and testing scenarios in the CARLA simulator. It includes a minimal orchestration CLI, a REST API for programmatic control, a simple web dashboard for viewing results, and comprehensive **Traffic Light Monitoring** capabilities for traffic flow analysis.

## Tech Stack

- **Python 3.10/3.11**
- **CARLA Simulator**
- **Flask**: For the REST API.
- **React + Vite**: For the web dashboard.
- **PyTest**: For testing.
- **pydantic & jsonschema**: For data validation.
- **Ultralytics YOLO**: For vehicle detection in traffic monitoring.
- **OpenCV**: For image processing and ROI annotation.
- **Makefile**: For development and orchestration tasks.
- **GitHub Actions**: For continuous integration.

## Getting Started

For detailed instructions on how to set up and run the project, please refer to the [Getting Started guide](docs/GETTING_STARTED.md).

## Usage

The `Makefile` provides several commands to streamline development and testing:

- `make setup`: Install all necessary dependencies.
- `make carla_up`: Provides instructions to start the CARLA simulator.
- `make smoke`: Run a smoke test to ensure the environment is working correctly.
- `make health`: Check the health of the CARLA server.
- `make determinism_check`: Run a determinism check to ensure that the simulator produces the same results given the same seed.
- `make tl-monitor`: Run traffic light monitoring simulation.
- `make annotate-roi IMAGE=<path>`: Launch ROI annotation tool for traffic monitoring.
- `make lint`: Run linters to check code quality.
- `make test`: Run all tests.
- `make web`: Run the web application in development mode.
- `make build-web`: Build the web application for production.

## Traffic Light Monitoring

The project includes a comprehensive traffic monitoring system that:
- Detects vehicles using YOLO
- Tracks vehicles across frames
- Analyzes queue lengths and waiting times
- Logs detailed metrics to CSV files

Quick start:
```bash
# Run monitoring
make tl-monitor

# Annotate ROI after first run
make annotate-roi IMAGE=outputs/Town10HD_Opt/tl_road1_lane2_s100/frame_000000.png
```

See [TL_MONITORING.md](docs/TL_MONITORING.md) for detailed documentation.

## Project Structure

```
carla-foundations/
  README.md
  Makefile
  pyproject.toml
  requirements.txt
  .github/workflows/ci.yml

  configs/         # Application configuration
  schemas/         # JSON schemas for data validation

  orchestration/   # Core orchestration logic
    runner.py      # CLI for running scenarios
    carla_client.py# CARLA simulator client
    tl_monitoring/ # Traffic light monitoring module

  data_pipeline/   # Data processing and validation
    validators.py  # Data validation logic
    writers.py     # Data writing logic

  api/             # Flask REST API
    app.py         # API endpoints

  web/             # React web dashboard
    src/           # React source code

  scripts/         # Helper scripts

  docs/            # Project documentation

  tests/           # Tests
```

## Contributing

Contributions are welcome! Please read the [contributing guide](docs/CONTRIBUTING.md) for more information.
