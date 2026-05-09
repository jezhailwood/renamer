"""Rename rule definitions.

Provides a `RenameRule` protocol and a set of rule classes: `ReplaceRule`, `RegexRule`,
`CaseRule`, `PrefixRule` and `SuffixRule`. Rules can be composed by passing a sequence
to `renamer.engine.build_plan`.
"""

import re
from enum import StrEnum, auto
from pathlib import Path
from typing import Protocol


class RenameRule(Protocol):
    """Protocol defining the interface for all rename rules.

    Any class with a matching `apply(path: Path) -> Path` method satisfies this protocol
    without needing to inherit from it (structural typing).
    """

    def apply(self, path: Path) -> Path:
        """Apply this rule to a path and return the renamed result.

        Args:
            path: The current file path.

        Returns:
            A new `pathlib.Path` with the rule applied to the filename.
            The parent directory is preserved.
        """
        ...


class ReplaceRule:
    """A rule that replaces a substring in the filename.

    Attributes:
        old: The substring to find.
        new: The replacement string.
    """

    def __init__(self, old: str, new: str) -> None:
        """Initialise a ReplaceRule.

        Args:
            old: The substring to find. Must not be empty.
            new: The replacement string. May be empty to delete the substring.

        Raises:
            ValueError: If `old` is empty.
        """
        if not old:
            raise ValueError("'old' replacement value must not be empty")
        self.old = old
        self.new = new

    def apply(self, path: Path) -> Path:  # noqa: D102
        return path.with_name(path.name.replace(self.old, self.new))


class RegexRule:
    r"""A rule that applies a regex substitution to the filename.

    The pattern is compiled at construction time. Backreferences (eg `\1`) are supported
    in the replacement string.

    Attributes:
        pattern: The regex pattern string.
        replacement: The replacement string.
    """

    def __init__(self, pattern: str, replacement: str) -> None:
        r"""Initialise a RegexRule.

        Args:
            pattern: The regex pattern string. Compiled and validated immediately.
            replacement: The replacement string. May include backreferences (eg `\1`).

        Raises:
            ValueError: If `pattern` is not a valid regular expression.
        """
        try:
            # Compile immediately so an invalid pattern raises at rule creation rather
            # than during a rename operation.
            self._compiled = re.compile(pattern)
        except re.error as e:
            raise ValueError(f"invalid regex pattern '{pattern}' ({e})") from e
        self.pattern = pattern
        self.replacement = replacement

    def apply(self, path: Path) -> Path:  # noqa: D102
        return path.with_name(self._compiled.sub(self.replacement, path.name))


class CaseMode(StrEnum):
    """Case transformation modes for `CaseRule`.

    Attributes:
        UPPER: Convert the filename stem to uppercase.
        LOWER: Convert the filename stem to lowercase.
        TITLE: Convert the filename stem to title case.
    """

    UPPER = auto()
    LOWER = auto()
    TITLE = auto()


class CaseRule:
    """A rule that transforms the case of the filename stem.

    The file extension is preserved unchanged.

    Attributes:
        mode: The `CaseMode` transformation to apply.
    """

    def __init__(self, mode: CaseMode) -> None:  # noqa: D107
        self.mode = mode

    def apply(self, path: Path) -> Path:
        """Apply the case transformation to the filename stem.

        Resolves to eg `path.stem.upper()` at runtime via the string method whose name
        matches the `CaseMode` enum value.
        """
        return path.with_name(getattr(path.stem, self.mode.value)() + path.suffix)


class PrefixRule:
    """A rule that prepends a string to the filename.

    Attributes:
        prefix: The string to prepend.
    """

    def __init__(self, prefix: str) -> None:  # noqa: D107
        self.prefix = prefix

    def apply(self, path: Path) -> Path:  # noqa: D102
        return path.with_name(self.prefix + path.name)


class SuffixRule:
    """A rule that appends a string to the filename stem.

    Attributes:
        suffix: The string to append.
    """

    def __init__(self, suffix: str) -> None:  # noqa: D107
        self.suffix = suffix

    def apply(self, path: Path) -> Path:  # noqa: D102
        return path.with_name(path.stem + self.suffix + path.suffix)
