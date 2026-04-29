"""Parser for BZ011 testbench .dat files.

- Datum column uses day-month-year ordering with two-digit year.
- current_density [A/cm²] = Strom I [A] / active_area_cm2 [cm²]  (from metadata JSON).
- Timestamps are treated as naive (no timezone).
"""

import json
from datetime import datetime
from pathlib import Path

from .base import BaseParser, ParseResult, get_logger, read_text_with_fallback

log = get_logger(__name__)

# Error codes returned in the "errors" list of the result dict.
ERR_METADATA_READ = "METADATA_READ_ERROR"
ERR_METADATA_JSON = "METADATA_JSON_ERROR"
ERR_METADATA_KEY = "METADATA_KEY_ERROR"
ERR_METADATA_INVALID = "METADATA_INVALID"
ERR_DATA_READ = "DATA_READ_ERROR"
ERR_COLUMN_MISSING = "COLUMN_MISSING"
ERR_ROW_SHORT = "ROW_TOO_SHORT"
ERR_ROW_TIMESTAMP = "ROW_TIMESTAMP_ERROR"
ERR_ROW_VALUE = "ROW_VALUE_ERROR"

_REQUIRED_COLUMNS = ("Datum", "Spg U / V", "Strom I / A")
_TIMESTAMP_FORMAT = "%d.%m.%y %H:%M:%S"


def _parse_float(value: str) -> float:
    return float(value.strip().replace(",", "."))


class BZ011Parser(BaseParser):
    name = "bz011"

    def __init__(self, data_path: Path, metadata_path: Path, encoding: str | None = None):
        self.data_path = Path(data_path)
        self.metadata_path = Path(metadata_path)
        self.encoding = encoding

    def parse(self) -> ParseResult:
        result: ParseResult = {"metadata": None, "records": [], "errors": []}

        # --- metadata ---
        try:
            raw = read_text_with_fallback(self.metadata_path, self.encoding)
        except (OSError, UnicodeDecodeError) as exc:
            log.warning("BZ011 metadata read failed: %s", exc)
            result["errors"].append({
                "code": ERR_METADATA_READ,
                "message": f"Could not read metadata file {self.metadata_path}: {exc}",
                "line": None,
            })
            return result

        try:
            metadata_list = json.loads(raw)
            metadata = metadata_list[0] if isinstance(metadata_list, list) else metadata_list
        except (json.JSONDecodeError, IndexError) as exc:
            log.warning("BZ011 metadata JSON invalid: %s", exc)
            result["errors"].append({"code": ERR_METADATA_JSON, "message": str(exc), "line": None})
            return result

        try:
            active_area = metadata["active_area_cm2"]
        except KeyError:
            result["errors"].append({
                "code": ERR_METADATA_KEY,
                "message": "Missing key 'active_area_cm2' in metadata",
                "line": None,
            })
            return result

        # Validate active_area_cm2: must be a positive number (cm²).
        if not isinstance(active_area, (int, float)) or isinstance(active_area, bool) or active_area <= 0:
            result["errors"].append({
                "code": ERR_METADATA_INVALID,
                "message": f"'active_area_cm2' must be a positive number, got {active_area!r}",
                "line": None,
            })
            return result

        result["metadata"] = metadata

        # --- data file ---
        try:
            text = read_text_with_fallback(self.data_path, self.encoding)
        except (OSError, UnicodeDecodeError) as exc:
            log.warning("BZ011 data read failed: %s", exc)
            result["errors"].append({
                "code": ERR_DATA_READ,
                "message": f"Could not read data file {self.data_path}: {exc}",
                "line": None,
            })
            return result

        lines = text.splitlines()  # handles CRLF and LF transparently
        header_line = next((line for line in lines if line.strip()), None)
        if header_line is None:
            result["errors"].append({"code": ERR_DATA_READ, "message": "File is empty", "line": None})
            return result

        headers = header_line.split("\t")
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
        header_lineno = lines.index(header_line)

        for offset, line in enumerate(lines[header_lineno + 1:], start=1):
            lineno = header_lineno + 1 + offset  # 1-based
            if not line.strip():
                continue

            cols = line.split("\t")
            if len(cols) < min_cols:
                log.debug("BZ011 line %d: row too short (%d cols)", lineno, len(cols))
                result["errors"].append({
                    "code": ERR_ROW_SHORT,
                    "message": f"Expected ≥{min_cols} columns, got {len(cols)}",
                    "line": lineno,
                })
                continue

            try:
                time_stamp = datetime.strptime(cols[indices["Datum"]].strip(), _TIMESTAMP_FORMAT)
            except ValueError as exc:
                log.debug("BZ011 line %d: bad timestamp: %s", lineno, exc)
                result["errors"].append({
                    "code": ERR_ROW_TIMESTAMP,
                    "message": str(exc),
                    "line": lineno,
                })
                continue

            try:
                cell_voltage = _parse_float(cols[indices["Spg U / V"]])
                current_a = _parse_float(cols[indices["Strom I / A"]])
            except ValueError as exc:
                log.debug("BZ011 line %d: bad value: %s", lineno, exc)
                result["errors"].append({
                    "code": ERR_ROW_VALUE,
                    "message": str(exc),
                    "line": lineno,
                })
                continue

            result["records"].append({
                "time_stamp": time_stamp,
                "cell_voltage": cell_voltage,
                # Strom I [A] / active_area_cm2 [cm²] → A/cm²
                "current_density": current_a / active_area,
            })

        return result


def parse_bz011(data_path: Path, metadata_path: Path, encoding: str | None = None) -> ParseResult:
    """Parse a BZ011 .dat file together with its companion metadata JSON.

    Args:
        data_path: Path to the .dat file (tab-separated).
        metadata_path: Path to the JSON metadata file.
        encoding: If given, force this text encoding for both files. If
            ``None`` (default), try utf-8 first then latin-1.

    Returns:
        ``ParseResult`` dict with ``metadata``, ``records`` and ``errors``.
        File-level problems populate ``errors`` and return empty records.
        Row-level problems skip the offending row and append an error entry
        with the 1-based line number.
    """
    return BZ011Parser(data_path, metadata_path, encoding).parse()
