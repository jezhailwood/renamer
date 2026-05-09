"""Logging configuration.

Configures a file-based handler on the `renamer` logger.
"""

import logging
from pathlib import Path


def setup_logging(log_file: Path, level: int = logging.DEBUG) -> None:
    """Configure file-based logging for renamer.

    Attaches a file handler to the `renamer` root logger. If handlers are already
    attached, the function returns immediately to prevent duplicate log entries if
    called more than once (eg in tests).

    Args:
        log_file: Path to the log file. Created if it does not exist.
        level: Logging level for the file handler. Defaults to `logging.DEBUG`.
    """
    root_logger = logging.getLogger("renamer")
    root_logger.setLevel(logging.DEBUG)

    if root_logger.handlers:
        return

    formatter = logging.Formatter(
        fmt="%(asctime)s [%(levelname)-8s] %(name)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    handler = logging.FileHandler(log_file, encoding="utf-8")
    handler.setLevel(level)
    handler.setFormatter(formatter)

    root_logger.addHandler(handler)
