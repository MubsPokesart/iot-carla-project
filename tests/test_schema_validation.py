"""Tests for schema validation."""

import json

import jsonschema


def test_run_meta_schema():
    """Test the run metadata schema validation."""
    with open("schemas/run_meta.schema.json") as f:
        schema = json.load(f)

    # This will raise an exception if the schema is invalid
    jsonschema.Draft7Validator.check_schema(schema)

    # Example valid data
    valid_data = {
        "scenario_id": "test_scenario",
        "run_id": "test_run",
        "seed": 42,
        "carla_version": "0.9.13",
        "map": "Town03",
        "weather": "ClearNoon",
        "start_ts": "2025-10-30T12:00:00Z",
        "end_ts": "2025-10-30T12:05:00Z",
    }
    jsonschema.validate(instance=valid_data, schema=schema)

    # Example invalid data
    invalid_data = {
        "scenario_id": "test_scenario",
        "run_id": "test_run",
        "seed": "not-an-integer",
        "carla_version": "0.9.13",
        "map": "Town03",
        "weather": "ClearNoon",
        "start_ts": "2025-10-30T12:00:00Z",
        "end_ts": "2025-10-30T12:05:00Z",
    }
    with open("schemas/run_meta.schema.json") as f:
        schema = json.load(f)
    try:
        jsonschema.validate(instance=invalid_data, schema=schema)
    except jsonschema.exceptions.ValidationError as e:
        assert "is not of type 'integer'" in str(e)


def test_kpi_schema():
    """Test the KPI schema validation."""
    with open("schemas/kpi.schema.json") as f:
        schema = json.load(f)

    # This will raise an exception if the schema is invalid
    jsonschema.Draft7Validator.check_schema(schema)

    # Example valid data
    valid_data = {
        "avg_travel_time": 120.5,
        "throughput": 50.2,
        "queue_length": 10.0,
        "congestion_index": 0.5,
    }
    jsonschema.validate(instance=valid_data, schema=schema)

    # Example invalid data
    invalid_data = {
        "avg_travel_time": "not-a-number",
        "throughput": 50.2,
        "queue_length": 10.0,
        "congestion_index": 0.5,
    }
    with open("schemas/kpi.schema.json") as f:
        schema = json.load(f)
    try:
        jsonschema.validate(instance=invalid_data, schema=schema)
    except jsonschema.exceptions.ValidationError as e:
        assert "is not of type 'number'" in str(e)
