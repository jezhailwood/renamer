"""Command-line interface.

Provides a single Typer command that finds files in a directory, builds a rename
plan from the supplied rules, displays a preview table, and optionally applies
the renames.

Rules are applied in a fixed order regardless of how options are supplied on the command
line: `--replace`, `--regex`, `--case`, `--prefix`, `--suffix`.

Typical `renamer` usage:

    renamer /path/to/files --prefix 'draft_' --suffix '_final'
    renamer --replace 'IMG_:photo_' --yes
    renamer --regex '[0-9]+:NUM' --recursive
"""

from pathlib import Path

import typer
from rich.console import Console
from rich.table import Table

from .engine import RenamePlan, apply_plan, build_plan
from .logger import setup_logging
from .rules import (
    CaseMode,
    CaseRule,
    PrefixRule,
    RegexRule,
    ReplaceRule,
    SuffixRule,
)

LOG_FILE = "renamer.log"


app = typer.Typer()


@app.command()
def main(
    path: Path = typer.Argument(default=None),
    replace: list[str] = typer.Option(default_factory=list),
    regex: list[str] = typer.Option(default_factory=list),
    delimiter: str = typer.Option(":", "--delimiter", "-d"),
    case: CaseMode | None = typer.Option(None, "--case", "-c"),
    prefix: list[str] = typer.Option(default_factory=list),
    suffix: list[str] = typer.Option(default_factory=list),
    recursive: bool = typer.Option(False, "--recursive", "-r"),
    yes: bool = typer.Option(False, "--yes", "-y"),
) -> None:
    """Batch-rename files in a directory using composable rules.

    Finds files in `path` (or the current working directory if omitted), applies
    the specified rules and displays a preview table. Prompts for confirmation before
    applying unless `--yes` is passed. Hidden files are excluded, as is the log file.

    Rules are always applied in the order: `--replace`, `--regex`, `--case`, `--prefix`,
    `--suffix`, regardless of the order arguments are given on the command line.

    Args:
        path: Directory containing the files to rename. Defaults to the current working
            directory.
        replace: `old{delimiter}new` pair for literal substitution. Repeatable.
        regex: `pattern{delimiter}replacement` pair for regex substitution. Repeatable.
        delimiter: Separator used to split `--replace` and `--regex` values. Defaults to
            `:`. Must be a shell-safe character.
        case: Case transformation to apply to the filename stem.
        prefix: String to prepend to each filename. Repeatable.
        suffix: String to append to each filename stem. Repeatable.
        recursive: If `True`, include files in subdirectories.
        yes: If `True`, skip the confirmation prompt and apply renames immediately.
    """
    if not replace and not regex and case is None and not prefix and not suffix:
        typer.echo(
            "Error: at least one --replace, --regex, --case, --prefix or --suffix "
            "is required",
            err=True,
        )
        raise typer.Exit(code=1)

    target = path or Path.cwd()
    if not target.exists():
        typer.echo(f"Error: path '{target}' does not exist", err=True)
        raise typer.Exit(code=1)
    if not target.is_dir():
        typer.echo(f"Error: path '{target}' is not a directory", err=True)
        raise typer.Exit(code=1)

    setup_logging(log_file=target / LOG_FILE)

    try:
        replace_pairs = parse_pairs(replace, delimiter, "replace")
        regex_pairs = parse_pairs(regex, delimiter, "regex")
    except ValueError as e:
        typer.echo(f"Error: {e}", err=True)
        raise typer.Exit(code=1) from None

    # Construct an absolute, resolved path so the log file can be reliably excluded from
    # the file list, regardless of relative paths or symlinks.
    log_file_resolved = (target / LOG_FILE).resolve()
    paths = [
        p
        for p in (target.rglob("*") if recursive else target.iterdir())
        if p.is_file()  # Exclude directories.
        and not any(
            part.startswith(".") for part in p.relative_to(target).parts
        )  # Exclude hidden files, including any files within hidden directories.
        and p.resolve() != log_file_resolved  # Exclude the log file.
    ]

    try:
        # Rule type order is fixed regardless of argument order on the command line.
        # Typer collects each repeatable option into its own list, so interleaving
        # across option types isn't possible.
        rules = (
            [ReplaceRule(old, new) for old, new in replace_pairs]
            + [RegexRule(pattern, replacement) for pattern, replacement in regex_pairs]
            + ([CaseRule(case)] if case is not None else [])
            + [PrefixRule(p) for p in prefix]
            + [SuffixRule(s) for s in suffix]
        )
        plan = build_plan(paths, rules)
    except ValueError as e:
        typer.echo(f"Error: {e}", err=True)
        raise typer.Exit(code=1) from None

    if not plan:
        typer.echo("Nothing to rename.")
        raise typer.Exit()  # Clean exit; code defaults to 0.

    preview_table(plan, target)

    if not yes:
        confirmed = typer.confirm("\nApply these renames?", default=False)
        if not confirmed:
            typer.echo("Aborted.")
            raise typer.Exit()  # Clean exit; code defaults to 0.

    apply_plan(plan)
    typer.echo("Done.")


def parse_pairs(
    values: list[str], delimiter: str, option: str
) -> list[tuple[str, str]]:
    """Split a list of delimited strings into `(left, right)` pairs.

    Args:
        values: Strings to split, each expected to contain `delimiter`.
        delimiter: The separator to split on. Only the first occurrence is used.
        option: The CLI option name, used in error messages.

    Returns:
        A list of `(left, right)` tuples in the same order as `values`.

    Raises:
        ValueError: If any value does not contain `delimiter`.
    """
    pairs = []
    for v in values:
        parts = v.split(delimiter, maxsplit=1)
        if len(parts) != 2:
            raise ValueError(f"--{option} '{v}' must contain delimiter '{delimiter}'")
        pairs.append((parts[0], parts[1]))
    return pairs


def preview_table(plan: list[RenamePlan], target: Path) -> None:
    """Render a Rich table summarising the planned renames.

    Paths are displayed relative to `target`. The source column is dimmed and the table
    title includes the total number of files to be renamed.

    Args:
        plan: The list of planned rename operations to display.
        target: The base directory, used to compute relative paths.
    """
    table = Table(title=f"Rename preview — {len(plan)} file(s)")
    table.add_column("from", style="dim")
    table.add_column("to")

    for rename in plan:
        table.add_row(
            str(rename.src.relative_to(target)), str(rename.dst.relative_to(target))
        )

    Console().print(table)
