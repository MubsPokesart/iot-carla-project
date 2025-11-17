# Traffic Light Monitoring

## Overview

The Traffic Light (TL) Monitoring module provides comprehensive traffic flow analysis at intersections using CARLA simulator. It combines computer vision, object tracking, and queue analysis to measure key performance indicators (KPIs) for traffic management.

## Features

- **Vehicle Detection**: YOLO-based real-time vehicle detection
- **Multi-Object Tracking**: IoU-based tracking across frames
- **Queue Analysis**: Automatic queue length estimation and waiting time tracking
- **Stop-Line Detection**: Crossing detection using region-of-interest (ROI) polygons
- **KPI Logging**: CSV-based metrics logging for analysis
- **REST API**: Flask API for remote monitoring and control
- **Deterministic IDs**: Stable traffic light identifiers across runs

## Quick Start

### 1. Install Dependencies

```bash
make setup
```

This installs all required packages including:
- `ultralytics` (YOLO)
- `opencv-python` (Image processing)
- `PyYAML` (Configuration)

### 2. Start CARLA Server

```bash
# Linux/Mac
./CarlaUE4.sh -quality-level=Epic -carla-rpc-port=2000

# Windows
CarlaUE4.exe -quality-level=Epic -carla-rpc-port=2000 -prefernvidiagpus
```

### 3. Run Traffic Light Monitoring

```bash
make tl-monitor
```

Or with custom parameters:

```bash
python -m orchestration.runner tl-monitor \
  --town Town10HD_Opt \
  --group-index 0 \
  --num-vehicles 40 \
  --duration 120 \
  --fps 20 \
  --seed 7
```

### 4. Annotate ROI Polygons

After the first run, annotate the Region of Interest (ROI) for each traffic light:

```bash
# Find a saved frame
ls outputs/Town10HD_Opt/tl_*/frame_*.png

# Annotate it
make annotate-roi IMAGE=outputs/Town10HD_Opt/tl_road1_lane2_s100/frame_000000.png
```

**Annotation Instructions**:
- Left-click to add polygon points
- Press `s` to save
- Press `r` to reset
- Press `u` to undo last point
- Press `q` to quit without saving

## Architecture

### Module Structure

```
orchestration/tl_monitoring/
├── __init__.py
├── config.py              # Configuration settings
├── vision/
│   ├── detector.py        # YOLO vehicle detection
│   └── tracker.py         # Multi-object tracking
├── utils/
│   ├── carla_helpers.py   # CARLA-specific utilities
│   └── roi.py             # ROI polygon management
├── observers/
│   └── tl_observer.py     # Main observer class
└── log/
    └── tl_logger.py       # Metrics logger
```

### Data Flow

```
CARLA World
    ↓
Camera Sensor → Image Queue
    ↓
Vehicle Detector (YOLO)
    ↓
Multi-Object Tracker
    ↓
Queue Analyzer (ROI-based)
    ↓
Metrics Logger (CSV)
```

## Configuration

Edit `configs/tl_monitoring.yaml`:

```yaml
simulation:
  town: "Town10HD_Opt"
  group_index: 0
  num_autopilot: 40
  dt: 0.05

camera:
  resolution:
    width: 1280
    height: 720
  fov: 70

detection:
  yolo_model: "yolo11n.pt"
  device: "cpu"  # or "cuda"

tracking:
  iou_threshold: 0.3
  max_age: 20
  stop_speed_threshold: 1.3
```

## Output Files

For each traffic light, the following files are generated in `outputs/<town>/tl_<stable_id>/`:

### ticks.csv
Per-frame metrics:
- `t_sec`: Simulation time (seconds)
- `frame`: Frame number
- `state`: Traffic light state (Red, Yellow, Green)
- `time_in_state`: Time in current state (seconds)
- `queue_count`: Number of stopped vehicles in ROI
- `queue_ema`: Exponential moving average of queue length
- `avg_wait`: Average waiting time (seconds)
- `max_wait`: Maximum waiting time (seconds)
- `num_long_wait_60s`: Vehicles waiting >60 seconds
- `arrival_ema`: Arrival rate (vehicles/second)
- `discharge_ema`: Discharge rate (vehicles/second)

### crossings.csv
Per-vehicle crossing events:
- `t_sec`: Simulation time
- `frame`: Frame number
- `track_id`: Vehicle track ID
- `wait_time_sec`: Total waiting time

### roi.json
ROI polygon coordinates:
```json
{
  "polygon": [[x1, y1], [x2, y2], ...]
}
```

### stopline.json
Stop-line polygon (auto-derived from ROI)

### Visualization Files
- `frame_*.png`: Raw camera frames (every N frames)
- `vis_*.png`: Annotated frames with bounding boxes and ROI

## REST API

### Start Monitoring Session

```bash
POST /api/tl-monitor/start
```

**Request Body**:
```json
{
  "town": "Town10HD_Opt",
  "group_index": 0,
  "num_vehicles": 40,
  "duration": 120,
  "fps": 20,
  "seed": 7
}
```

**Response**:
```json
{
  "session_id": "uuid",
  "status": "started",
  "town": "Town10HD_Opt"
}
```

### List All Runs

```bash
GET /api/tl-monitor/runs
```

**Response**:
```json
{
  "runs": [
    {
      "town": "Town10HD_Opt",
      "tl_id": "tl_road1_lane2_s100",
      "path": "outputs/Town10HD_Opt/tl_road1_lane2_s100",
      "latest_metrics": {
        "time": 120.0,
        "frame": 2400,
        "state": "Green",
        "queue_count": 5,
        "queue_ema": 4.8,
        "avg_wait": 12.5
      },
      "has_crossings": true
    }
  ]
}
```

### Get Detailed Metrics

```bash
GET /api/tl-monitor/runs/<town>/<tl_id>/metrics
```

**Response**:
```json
{
  "tl_id": "tl_road1_lane2_s100",
  "town": "Town10HD_Opt",
  "ticks": [...],
  "total_ticks": 2400,
  "crossings": [...],
  "total_crossings": 150,
  "avg_crossing_wait": 10.5
}
```

### Get ROI Polygon

```bash
GET /api/tl-monitor/runs/<town>/<tl_id>/roi
```

## Advanced Usage

### Custom YOLO Model

Use a different YOLO model:

```python
from orchestration.tl_monitoring.config import TLMonitoringConfig

config = TLMonitoringConfig(yolo_model="yolo11s.pt")
```

### GPU Acceleration

Enable CUDA for faster inference:

```yaml
# configs/tl_monitoring.yaml
detection:
  device: "cuda"
```

### Adjust Queue Detection

Tune the stop speed threshold:

```yaml
tracking:
  stop_speed_threshold: 2.0  # Higher = more lenient
```

## Troubleshooting

### No ROI Warning

**Problem**: `[WARN] No ROI for TL tl_road1_lane2_s100`

**Solution**: Annotate the ROI using the tool:
```bash
make annotate-roi IMAGE=outputs/Town10HD_Opt/tl_road1_lane2_s100/frame_000000.png
```

### Camera Not Capturing

**Problem**: Empty image queue

**Solution**:
- Ensure CARLA is running in synchronous mode
- Check camera spawn position doesn't collide with objects
- Verify traffic light exists in the selected group

### Low Detection Accuracy

**Problem**: Vehicles not detected

**Solution**:
- Use a larger YOLO model (yolo11m.pt or yolo11l.pt)
- Enable GPU acceleration
- Adjust camera position/FOV

### High CPU Usage

**Problem**: Simulation runs slowly

**Solution**:
- Reduce `num_vehicles`
- Lower `fps`
- Use smaller YOLO model (yolo11n.pt)
- Disable visualization saves

## Performance Tips

1. **Use GPU**: Set `device: "cuda"` for 5-10x faster detection
2. **Optimize Camera**: Reduce resolution for faster processing
3. **Batch Processing**: Process multiple frames before logging
4. **Limit Saves**: Increase `save_every_n` to reduce I/O

## Contributing

When adding features to TL monitoring:

1. Follow OOP principles (see CLAUDE.md)
2. Keep files under 500 lines
3. Add type hints
4. Write tests
5. Update this documentation

## References

- [CARLA Documentation](https://carla.readthedocs.io/)
- [Ultralytics YOLO](https://docs.ultralytics.com/)
- [OpenCV Python](https://docs.opencv.org/4.x/d6/d00/tutorial_py_root.html)
