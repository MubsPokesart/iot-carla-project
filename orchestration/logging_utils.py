"""This module contains logging utilities for the CARLA Environment Foundations project."""
import logging


def def get_logger(name, level=logging.INFO):
    """Get a logger instance."""
    logging.basicConfig(
        level=level, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    return logging.getLogger(name)
