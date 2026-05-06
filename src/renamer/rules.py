import re
from enum import StrEnum, auto
from pathlib import Path
from typing import Protocol


class RenameRule(Protocol):
    def apply(self, path: Path) -> Path: ...


class ReplaceRule:
    def __init__(self, old: str, new: str) -> None:
        if not old:
            raise ValueError("'old' replacement value must not be empty")
        self.old = old
        self.new = new

    def apply(self, path: Path) -> Path:
        return path.with_name(path.name.replace(self.old, self.new))


class RegexRule:
    def __init__(self, pattern: str, replacement: str) -> None:
        try:
            self._compiled = re.compile(pattern)
        except re.error as e:
            raise ValueError(f"invalid regex pattern '{pattern}' ({e})") from e
        self.pattern = pattern
        self.replacement = replacement

    def apply(self, path: Path) -> Path:
        return path.with_name(self._compiled.sub(self.replacement, path.name))


class CaseMode(StrEnum):
    UPPER = auto()
    LOWER = auto()
    TITLE = auto()


class CaseRule:
    def __init__(self, mode: CaseMode) -> None:
        self.mode = mode

    def apply(self, path: Path) -> Path:
        return path.with_name(getattr(path.stem, self.mode.value)() + path.suffix)


class PrefixRule:
    def __init__(self, prefix: str) -> None:
        self.prefix = prefix

    def apply(self, path: Path) -> Path:
        return path.with_name(self.prefix + path.name)


class SuffixRule:
    def __init__(self, suffix: str) -> None:
        self.suffix = suffix

    def apply(self, path: Path) -> Path:
        return path.with_name(path.stem + self.suffix + path.suffix)
