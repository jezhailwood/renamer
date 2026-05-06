from pathlib import Path

import typer
from rich.console import Console
from rich.table import Table

from renamer.engine import RenamePlan, apply_plan, build_plan
from renamer.logger import setup_logging
from renamer.rules import (
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
        raise typer.Exit(code=1)

    log_file_resolved = (target / LOG_FILE).resolve()
    paths = [
        p
        for p in (target.rglob("*") if recursive else target.iterdir())
        if p.is_file()
        and not any(part.startswith(".") for part in p.relative_to(target).parts)
        and p.resolve() != log_file_resolved
    ]

    try:
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
        raise typer.Exit(code=1)

    if not plan:
        typer.echo("Nothing to rename.")
        raise typer.Exit()

    preview_table(plan, target)

    if not yes:
        confirmed = typer.confirm("\nApply these renames?", default=False)
        if not confirmed:
            typer.echo("Aborted.")
            raise typer.Exit()

    apply_plan(plan)
    typer.echo("Done.")


def parse_pairs(
    values: list[str], delimiter: str, option: str
) -> list[tuple[str, str]]:
    pairs = []
    for v in values:
        parts = v.split(delimiter, maxsplit=1)
        if len(parts) != 2:
            raise ValueError(f"--{option} '{v}' must contain delimiter '{delimiter}'")
        pairs.append((parts[0], parts[1]))
    return pairs


def preview_table(plan: list[RenamePlan], target: Path) -> None:
    table = Table(title=f"Rename preview — {len(plan)} file(s)")
    table.add_column("from", style="dim")
    table.add_column("to")

    for rename in plan:
        table.add_row(
            str(rename.src.relative_to(target)), str(rename.dst.relative_to(target))
        )

    Console().print(table)
