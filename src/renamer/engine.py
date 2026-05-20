"""Rename plan construction and execution.

Provides `RenamePlan` to represent a single src → dst rename operation, and two
functions: `build_plan` to apply a sequence of rules to a set of paths and return
a validated list of planned renames, and `apply_plan` to execute that plan on disk.
"""

import logging
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path

from .rules import RenameRule

logger = logging.getLogger(__name__)


@dataclass
class RenamePlan:
    """A planned rename operation.

    Attributes:
        src: The current file path.
        dst: The intended destination path after renaming.
    """

    src: Path
    dst: Path


def build_plan(paths: Sequence[Path], rules: Sequence[RenameRule]) -> list[RenamePlan]:
    """Apply rules to paths and return a validated rename plan.

    Applies each rule in sequence to every path. Paths whose name is unchanged after all
    rules are applied are excluded from the plan. Raises if any two paths would resolve
    to the same destination.

    Args:
        paths: The files to rename.
        rules: The rules to apply, in order.

    Returns:
        A list of `RenamePlan` objects, one per file that would be renamed.

    Raises:
        ValueError: If two or more paths would be renamed to the same destination.
    """
    logger.debug("building plan: %d path(s), %d rule(s)", len(paths), len(rules))

    seen_destinations = set()
    plan = []

    for path in paths:
        dst = path
        for rule in rules:
            dst = rule.apply(dst)

        # Exclude files whose name is unchanged after all rules are applied.
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
    """Execute a rename plan on disk.

    Renames each file from its `src` to its `dst` path. Failed operations are logged and
        skipped; remaining renames continue.

    Args:
        plan: The list of rename operations to perform.

    Raises:
        RuntimeError: If one or more renames fail, after all operations have been
            attempted.
    """
    failures = []

    for op in plan:
        try:
            op.src.rename(op.dst)
            logger.info("renamed: %s → %s", op.src, op.dst)
        except OSError as e:
            logger.error("failed to rename %s → %s: %s", op.src, op.dst, e)
            failures.append(op)

    if failures:
        raise RuntimeError(
            f"{len(failures)} of {len(plan)} rename(s) failed - see log for details"
        )
