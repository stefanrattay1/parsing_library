"""Parser for Greenlight testbench .csv files.

File layout:
- Top: metadata "key,value,..." rows.
- Dashes-only and tilde-only separator rows mark the end of metadata.
- Then a long-name row, a units row, and a machine-header row whose first
  cell is "Time Stamp". Data rows follow.

current_density is read directly from the source column (already A/cm²),
mirroring the BZ011 output schema {time_stamp, cell_voltage, current_density}.
"""

from datetime import datetime
from pathlib import Path

from .base import BaseParser, ParseResult, get_logger, read_text_with_fallback

log = get_logger(__name__)

ERR_DATA_READ = "DATA_READ_ERROR"
ERR_HEADER_MISSING = "HEADER_MISSING"
ERR_COLUMN_MISSING = "COLUMN_MISSING"
ERR_ROW_SHORT = "ROW_TOO_SHORT"
ERR_ROW_TIMESTAMP = "ROW_TIMESTAMP_ERROR"
ERR_ROW_VALUE = "ROW_VALUE_ERROR"

_REQUIRED_COLUMNS = ("Time Stamp", "cell_voltage_001", "current_density")
_TIMESTAMP_FORMAT = "%Y-%m-%d %H:%M:%S.%f"


def _trim_trailing_empties(cols: list[str]) -> list[str]:
    end = len(cols)
    while end > 0 and cols[end - 1] == "":
        end -= 1
    return cols[:end]


class GreenlightParser(BaseParser):
    name = "greenlight"

    def __init__(self, data_path: Path, encoding: str | None = None):
        self.data_path = Path(data_path)
        self.encoding = encoding

    def parse(self) -> ParseResult:
        result: ParseResult = {"metadata": {}, "records": [], "errors": []}

        try:
            text = read_text_with_fallback(self.data_path, self.encoding)
        except (OSError, UnicodeDecodeError) as exc:
            log.warning("Greenlight data read failed: %s", exc)
            result["errors"].append({
                "code": ERR_DATA_READ,
                "message": f"Could not read data file {self.data_path}: {exc}",
                "line": None,
            })
            return result

        lines = text.splitlines()  # handles CRLF and LF transparently
        if not lines:
            result["errors"].append({"code": ERR_DATA_READ, "message": "File is empty", "line": None})
            return result

        metadata: dict[str, str] = {}
        header_lineno: int | None = None

        for idx, line in enumerate(lines):
            if not line.strip():
                continue
            cols = _trim_trailing_empties(line.split(","))
            if not cols:
                continue
            first = cols[0]
            if first.startswith("---") or first.startswith("~-~"):
                continue
            if first == "Time Stamp":
                header_lineno = idx
                break
            # Metadata "key,value" row. Skip rows whose value is empty.
            if len(cols) >= 2 and cols[1] != "":
                metadata[first] = cols[1]
            elif len(cols) == 1:
                metadata[first] = ""

        result["metadata"] = metadata

        if header_lineno is None:
            result["errors"].append({
                "code": ERR_HEADER_MISSING,
                "message": "Could not find header row starting with 'Time Stamp'",
                "line": None,
            })
            return result

        headers = lines[header_lineno].split(",")
        indices: dict[str, int] = {}
        for col in _REQUIRED_COLUMNS:
            try:
                indices[col] = headers.index(col)
            except ValueError:
                result["errors"].append({
                    "code": ERR_COLUMN_MISSING,
                    "message": f"Required column not found: '{col}'",
                    "line": None,
                })

        if result["errors"]:
            return result

        min_cols = max(indices.values()) + 1

        for offset, line in enumerate(lines[header_lineno + 1:], start=1):
            lineno = header_lineno + 1 + offset  # 1-based
            if not line.strip():
                continue

            cols = line.split(",")
            if len(cols) < min_cols:
                log.debug("Greenlight line %d: row too short (%d cols)", lineno, len(cols))
                result["errors"].append({
                    "code": ERR_ROW_SHORT,
                    "message": f"Expected ≥{min_cols} columns, got {len(cols)}",
                    "line": lineno,
                })
                continue

            try:
                time_stamp = datetime.strptime(cols[indices["Time Stamp"]].strip(), _TIMESTAMP_FORMAT)
            except ValueError as exc:
                log.debug("Greenlight line %d: bad timestamp: %s", lineno, exc)
                result["errors"].append({
                    "code": ERR_ROW_TIMESTAMP,
                    "message": str(exc),
                    "line": lineno,
                })
                continue

            try:
                cell_voltage = float(cols[indices["cell_voltage_001"]].strip())
                # source column is already A/cm² per the units row — direct mapping
                current_density = float(cols[indices["current_density"]].strip())
            except ValueError as exc:
                log.debug("Greenlight line %d: bad value: %s", lineno, exc)
                result["errors"].append({
                    "code": ERR_ROW_VALUE,
                    "message": str(exc),
                    "line": lineno,
                })
                continue

            result["records"].append({
                "time_stamp": time_stamp,
                "cell_voltage": cell_voltage,
                "current_density": current_density,
            })

        return result


def parse_greenlight(data_path: Path, encoding: str | None = None) -> ParseResult:
    """Parse a Greenlight CSV file (metadata preamble + data table).

    Args:
        data_path: Path to the .csv file.
        encoding: If given, force this text encoding. If ``None`` (default),
            try utf-8 first then latin-1.

    Returns:
        ``ParseResult`` dict with ``metadata``, ``records`` and ``errors``.
    """
    return GreenlightParser(data_path, encoding).parse()
