"""Shared parser interface and helpers.

Lightweight base for testbench parsers. Each concrete parser returns the same
standard ``ParseResult`` shape so downstream code can be format-agnostic.

The interface is intentionally minimal — just enough to (a) document the
contract and (b) host shared helpers (encoding fallback, logger). Concrete
parsers are exposed as both classes and module-level functions for
backward compatibility.
"""

import logging
from abc import ABC, abstractmethod
from pathlib import Path
from typing import TypedDict


class ParseError(TypedDict):
    code: str
    message: str
    line: int | None


class ParseResult(TypedDict):
    metadata: dict | None
    records: list[dict]
    errors: list[ParseError]


class BaseParser(ABC):
    """Abstract testbench parser.

    Subclasses construct with their format-specific paths/options and
    implement ``parse()`` to return a ``ParseResult``.
    """

    name: str = ""

    @abstractmethod
    def parse(self) -> ParseResult:  # pragma: no cover - interface only
        ...


def get_logger(name: str) -> logging.Logger:
    """Return a logger that is silent by default.

    The library does not configure handlers; applications opt in by adding
    their own. A NullHandler is attached so ``logging`` does not emit
    "No handlers could be found" warnings.
    """
    logger = logging.getLogger(name)
    if not logger.handlers:
        logger.addHandler(logging.NullHandler())
    return logger


def read_text_with_fallback(path: Path, encoding: str | None = None) -> str:
    """Read a text file, falling back to latin-1 on UnicodeDecodeError.

    If ``encoding`` is given, only that encoding is tried. If ``None``, the
    function tries utf-8 first then latin-1 — covers most testbench files
    where stray bytes (e.g. ``cm²``) appear in otherwise-ASCII output.
    """
    if encoding is not None:
        return path.read_text(encoding=encoding)
    try:
        return path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return path.read_text(encoding="latin-1")
