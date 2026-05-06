import logging
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path

from renamer.rules import RenameRule

logger = logging.getLogger(__name__)


@dataclass
class RenamePlan:
    src: Path
    dst: Path


def build_plan(paths: Sequence[Path], rules: Sequence[RenameRule]) -> list[RenamePlan]:
    logger.debug("building plan: %d path(s), %d rule(s)", len(paths), len(rules))

    seen_destinations = set()
    plan = []

    for path in paths:
        dst = path
        for rule in rules:
            dst = rule.apply(dst)

        if dst == path:
            continue

        if dst in seen_destinations:
            logger.warning("conflict: multiple files would be renamed to %s", dst)
            raise ValueError(f"multiple files would be renamed to {dst}")

        seen_destinations.add(dst)
        plan.append(RenamePlan(src=path, dst=dst))
        logger.debug("planned: %s → %s", path, dst)

    logger.info("plan built: %d rename(s)", len(plan))
    return plan


def apply_plan(plan: list[RenamePlan]) -> None:
    for op in plan:
        op.src.rename(op.dst)
        logger.info("renamed: %s → %s", op.src, op.dst)
