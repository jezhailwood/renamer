# renamer

A command-line tool for batch-renaming files using composable rules. Rules can be chained to apply find-and-replace, regex, case, prefix and suffix transformations to filenames. The package installs a `renamer` command; `python -m renamer` is equivalent.

## Installation

Install from GitHub using pip:

```shell
pip install "renamer @ git+https://github.com/jezhailwood/renamer.git@v0.1.0"
```

Alternatively, add as a dependency in `pyproject.toml`:

```toml
dependencies = [
    "renamer @ git+https://github.com/jezhailwood/renamer.git@v0.1.0",
]
```

Replace `v0.1.0` with the [latest release tag](https://github.com/jezhailwood/renamer/tags).

## Quickstart

Run `renamer --help` for a full list of options.

By default, `renamer` operates on the current directory. Pass a path to target a specific directory:

```shell
renamer /path/to/files --prefix 'draft_'
```

All commands show a preview table and prompt for confirmation before making any changes. Pass `--yes` (or `-y`) to skip the prompt:

```shell
renamer /path/to/files --prefix 'draft_' --yes
```

### Prefix and suffix

Prepend or append a string to each filename. Both options are repeatable:

```shell
renamer --prefix '2026_'
renamer --suffix '_final'
renamer --prefix 'draft_' --suffix '_v1'
```

### Replace

Substitute a literal substring using `old:new` syntax:

```shell
renamer --replace 'IMG_:photo_'
renamer --replace ' :_'
```

### Regex

Apply a regex substitution using `pattern:replacement` syntax. Backreferences are supported:

```shell
renamer --regex '[0-9]+:NUM'
renamer --regex '(\d{4})-(\d{2})-(\d{2}):\3-\2-\1'
```

### Case

Transform the filename stem to upper, lower or title case:

```shell
renamer --case upper
renamer --case lower
renamer --case title
```

### Chaining rules

All options are repeatable and composable:

```shell
renamer --replace ' :_' --case lower --prefix '2026_' --suffix '_draft'
```

### Custom delimiter

If a search or replacement value contains `:`, use `--delimiter` (or `-d`) to specify an alternative separator for `--replace` and `--regex`:

```shell
renamer --replace 'old|new' --delimiter '|'
```

### Recursive

Pass `--recursive` (or `-r`) to include files in subdirectories:

```shell
renamer /path/to/files --prefix 'archive_' --recursive
```

## Notes

- **Log file.** Each run appends to `renamer.log` in the target directory. The log file is excluded from rename operations.
- **Hidden files.** Files whose name begins with `.`, and any files inside hidden directories, are excluded from rename operations.
- **Rule ordering.** Rules are always applied in the order `--replace`, `--regex`, `--case`, `--prefix`, `--suffix`, regardless of the order given on the command line.

## API reference

Full documentation is available at [jezhailwood.github.io/renamer](https://jezhailwood.github.io/renamer).

## Licence

Released under the [MIT Licence](LICENSE).
