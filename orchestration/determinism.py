"""This module contains functions for checking determinism in the CARLA simulator."""
import hashlib
import json


def def calculate_hash(data):
    """Calculate the SHA256 hash of a dictionary."""
    encoded_data = json.dumps(data, sort_keys=True).encode("utf-8")
    return hashlib.sha256(encoded_data).hexdigest()


def def write_summary(run_id, summary_data, output_dir="artefacts"):
    """Write a summary file and its hash."""
    summary_path = f"{output_dir}/{run_id}/summary.json"
    hash_path = f"{output_dir}/{run_id}/summary.hash"

    with open(summary_path, "w") as f:
        json.dump(summary_data, f, indent=4)

    summary_hash = calculate_hash(summary_data)
    with open(hash_path, "w") as f:
        f.write(summary_hash)
    return summary_hash


def def compare_summaries(run_id1, run_id2, output_dir="artefacts"):
    """Compare the hashes of two run summaries."""
    hash_path1 = f"{output_dir}/{run_id1}/summary.hash"
    hash_path2 = f"{output_dir}/{run_id2}/summary.hash"

    with open(hash_path1) as f:
        hash1 = f.read()
    with open(hash_path2) as f:
        hash2 = f.read()

    return hash1 == hash2
