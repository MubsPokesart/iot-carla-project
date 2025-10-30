"""Validation utilities for run metadata and schemas."""

import json

from jsonschema import validate


def validate_run_meta(run_meta_data, schema_path="schemas/run_meta.schema.json"):
    """Validate run metadata against the schema."""
    with open(schema_path) as f:
        schema = json.load(f)
    validate(instance=run_meta_data, schema=schema)
