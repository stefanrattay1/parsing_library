"""Top-level dispatcher.

``parse_file()`` detects the testbench format from the input file and
delegates to the matching parser, returning the standard ``ParseResult``
shape:

    {
        "metadata": {...} | None,
        "records": [{"time_stamp", "cell_voltage", "current_density"}, ...],
        "errors": [{"code", "message", "line"}, ...],
    }

Format detection runs **two** checks:

1. **Extension** — ``.dat`` → BZ011, ``.csv`` → Greenlight.
2. **Content** — first non-blank line of the file:
   - starts with ``Datum\\t``  → BZ011
   - starts with ``Format,``    → Greenlight

If either check yields nothing, the other wins. If both yield a result and
they disagree, an ``ERR_FORMAT_MISMATCH`` is returned (the file extension
lies about the contents — better to fail loudly than silently mis-parse).
"""

from pathlib import Path

from .parsers.base import ParseResult, get_logger, read_text_with_fallback
from .parsers.bz011_parser import BZ011Parser
from .parsers.greenlight_parser import GreenlightParser

log = get_logger(__name__)

ERR_FILE_READ = "FILE_READ_ERROR"
ERR_FORMAT_UNKNOWN = "FORMAT_UNKNOWN"
ERR_FORMAT_MISMATCH = "FORMAT_MISMATCH"
ERR_METADATA_REQUIRED = "METADATA_REQUIRED"

FORMAT_BZ011 = "bz011"
FORMAT_GREENLIGHT = "greenlight"


def _detect_by_extension(path: Path) -> str | None:
    suffix = path.suffix.lower()
    if suffix == ".dat":
        return FORMAT_BZ011
    if suffix == ".csv":
        return FORMAT_GREENLIGHT
    return None


def _detect_by_content(text: str) -> str | None:
    for line in text.splitlines():
        if not line.strip():
            continue
        if line.startswith("Datum\t") or line.startswith("Datum "):
            return FORMAT_BZ011
        if line.startswith("Format,"):
            return FORMAT_GREENLIGHT
        return None  # first non-blank line didn't match either
    return None


def _error_result(code: str, message: str) -> ParseResult:
    return {"metadata": None, "records": [], "errors": [{"code": code, "message": message, "line": None}]}


def parse_file(
    data_path: str | Path,
    metadata_path: str | Path | None = None,
    encoding: str | None = None,
) -> ParseResult:
    """Detect the testbench format of ``data_path`` and parse it.

    Args:
        data_path: Path to the data file (.dat for BZ011, .csv for Greenlight).
        metadata_path: Required for BZ011 (companion JSON). Ignored for Greenlight.
        encoding: Forwarded to the underlying parser. ``None`` = utf-8 with latin-1 fallback.

    Returns:
        A ``ParseResult`` dict. On detection failure, ``records`` is empty
        and ``errors`` carries one of:
            - ``FILE_READ_ERROR`` — could not read the data file.
            - ``FORMAT_UNKNOWN`` — neither extension nor content match a known format.
            - ``FORMAT_MISMATCH`` — extension and content disagree.
            - ``METADATA_REQUIRED`` — detected BZ011 but no metadata_path was given.
    """
    data_path = Path(data_path)

    try:
        text = read_text_with_fallback(data_path, encoding)
    except (OSError, UnicodeDecodeError) as exc:
        log.warning("parse_file: could not read %s: %s", data_path, exc)
        return _error_result(ERR_FILE_READ, f"Could not read data file {data_path}: {exc}")

    by_ext = _detect_by_extension(data_path)
    by_content = _detect_by_content(text)

    if by_ext is None and by_content is None:
        return _error_result(
            ERR_FORMAT_UNKNOWN,
            f"Could not detect format of {data_path} (extension={data_path.suffix!r}, content unrecognized)",
        )

    if by_ext is not None and by_content is not None and by_ext != by_content:
        return _error_result(
            ERR_FORMAT_MISMATCH,
            f"Extension suggests {by_ext} but content looks like {by_content} for {data_path}",
        )

    fmt = by_content or by_ext

    if fmt == FORMAT_BZ011:
        if metadata_path is None:
            return _error_result(
                ERR_METADATA_REQUIRED,
                f"BZ011 requires a metadata JSON path; none provided for {data_path}",
            )
        return BZ011Parser(data_path, Path(metadata_path), encoding=encoding).parse()

    if fmt == FORMAT_GREENLIGHT:
        return GreenlightParser(data_path, encoding=encoding).parse()

    # Unreachable — both branches above cover the only two possible fmt values.
    return _error_result(ERR_FORMAT_UNKNOWN, f"Unhandled format: {fmt!r}")
