# Determinism

This document explains how to run the determinism check.

The determinism check runs two simulations with the same seed and compares the hashes of the resulting summary files.

## Running the check

To run the determinism check, use the following command:

```bash
python -m orchestration.runner determinism-check
```

You can also provide different seeds to see the check fail:

```bash
python -m orchestration.runner determinism-check --seed1 123 --seed2 456
```

The summary files and their hashes are stored in the `artefacts` directory.
