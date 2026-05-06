import logging
from pathlib import Path


def setup_logging(log_file: Path, level: int = logging.DEBUG) -> None:
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
