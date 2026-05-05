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
from datetime import datetime
from pathlib import Path
from typing import Any, TypedDict


class ParseError(TypedDict):
    """Non-fatal parser error entry.

    Attributes:
        code: Stable machine-readable error code.
        message: Human-readable explanation of the failure.
        line: 1-based row number when the error is tied to input data,
            otherwise ``None``.
    """

    code: str
    message: str
    line: int | None


class DescriptiveMetadata(TypedDict):
    """Normalized metadata shared by all parser outputs.

    Attributes:
        schema: Stable metadata schema identifier.
        source_format: Parser/source format name.
        format_version: Source format version when present in the input.
        station_id: Concrete station or bench identifier when available.
        test_name: Human-readable test or experiment title.
        experiment_type: High-level experiment category.
        sample_name: Human-readable sample identifier.
        started_at: Normalized start timestamp string when available.
        operator_name: Operator/user name when present.
        location: Physical lab or bench location when present.
        active_area_cm2: Active area used for normalization, if known.
        source_record_id: External source-system identifier.
        source_metadata: Lossless source-specific metadata dictionary.
    """

    schema: str
    source_format: str
    format_version: str | None
    station_id: str | None
    test_name: str | None
    experiment_type: str | None
    sample_name: str | None
    started_at: str | None
    operator_name: str | None
    location: str | None
    active_area_cm2: int | float | None
    source_record_id: str | int | None
    source_metadata: dict[str, Any]


class ParseResult(TypedDict):
    """Standard parser output.

    Attributes:
        metadata: Normalized descriptive metadata dictionary, or ``None``
            when metadata could not be obtained.
        records: Parsed and normalized data rows.
        errors: Non-fatal issues collected during parsing.
    """

    metadata: DescriptiveMetadata | None
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


def normalize_metadata_timestamp(value: object) -> str | None:
    """Return a normalized metadata timestamp string when possible."""
    if value is None:
        return None
    if isinstance(value, str):
        text = value.strip()
        if not text:
            return None
    else:
        text = str(value)

    try:
        return datetime.strptime(text, "%Y-%m-%d %H:%M:%S").isoformat()
    except ValueError:
        return text


def build_metadata(
    *,
    source_format: str,
    source_metadata: dict[str, Any],
    format_version: object = None,
    station_id: object = None,
    test_name: object = None,
    experiment_type: object = None,
    sample_name: object = None,
    started_at: object = None,
    operator_name: object = None,
    location: object = None,
    active_area_cm2: int | float | None = None,
    source_record_id: object = None,
) -> DescriptiveMetadata:
    """Build the shared descriptive metadata envelope for parser results."""

    def _clean_text(value: object) -> str | None:
        if value is None:
            return None
        if isinstance(value, str):
            stripped = value.strip()
            return stripped or None
        return str(value)

    cleaned_source_metadata = dict(source_metadata)

    return {
        "schema": "rdm_parser.metadata.v1",
        "source_format": source_format,
        "format_version": _clean_text(format_version),
        "station_id": _clean_text(station_id),
        "test_name": _clean_text(test_name),
        "experiment_type": _clean_text(experiment_type),
        "sample_name": _clean_text(sample_name),
        "started_at": normalize_metadata_timestamp(started_at),
        "operator_name": _clean_text(operator_name),
        "location": _clean_text(location),
        "active_area_cm2": active_area_cm2,
        "source_record_id": _clean_text(source_record_id),
        "source_metadata": cleaned_source_metadata,
    }
