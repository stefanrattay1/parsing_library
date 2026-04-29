"""Parser for BZ011 testbench .dat files.

Assumptions / design notes (fill in during implementation):
- Datum column uses day-month-year ordering.
- current_density = Strom I / A  /  active_area_cm2  (from metadata JSON).
- Timestamps are treated as naive (no timezone) unless stated otherwise.
"""

import json
from datetime import datetime
from pathlib import Path

# Error codes returned in the "errors" list of the result dict.
ERR_METADATA_READ = "METADATA_READ_ERROR"
ERR_METADATA_JSON = "METADATA_JSON_ERROR"
ERR_METADATA_KEY = "METADATA_KEY_ERROR"
ERR_DATA_READ = "DATA_READ_ERROR"
ERR_COLUMN_MISSING = "COLUMN_MISSING"
ERR_ROW_SHORT = "ROW_TOO_SHORT"
ERR_ROW_TIMESTAMP = "ROW_TIMESTAMP_ERROR"
ERR_ROW_VALUE = "ROW_VALUE_ERROR"

_REQUIRED_COLUMNS = ("Datum", "Spg U / V", "Strom I / A")
_TIMESTAMP_FORMAT = "%d.%m.%y %H:%M:%S"


def _parse_float(value: str) -> float:
    return float(value.strip().replace(",", "."))


def parse_bz011(data_path: Path, metadata_path: Path) -> dict:
    """Parse a BZ011 .dat file together with its companion metadata JSON.

    Returns:
        {
            "metadata": {...} | None,
            "records": [{"time_stamp": ..., "cell_voltage": ..., "current_density": ...}, ...],
            "errors": [{"code": ..., "message": ..., "line": int | None}, ...],
        }

    File-level problems (unreadable files, missing required columns) populate
    "errors" and return an empty "records" list. Row-level problems skip the
    offending row and append an error entry with the 1-based line number.
    """
    result: dict = {"metadata": None, "records": [], "errors": []}

    # --- metadata ---
    try:
        raw = metadata_path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError) as exc:
        result["errors"].append({
            "code": ERR_METADATA_READ,
            "message": f"Could not read metadata file {metadata_path}: {exc}",
            "line": None,
        })
        return result

    try:
        metadata_list = json.loads(raw)
        metadata = metadata_list[0] if isinstance(metadata_list, list) else metadata_list
    except (json.JSONDecodeError, IndexError) as exc:
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

    result["metadata"] = metadata

    # --- data file ---
    try:
        text = data_path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError) as exc:
        result["errors"].append({
            "code": ERR_DATA_READ,
            "message": f"Could not read data file {data_path}: {exc}",
            "line": None,
        })
        return result

    lines = text.splitlines()
    header_line = next((l for l in lines if l.strip()), None)
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
            result["errors"].append({
                "code": ERR_ROW_SHORT,
                "message": f"Expected ≥{min_cols} columns, got {len(cols)}",
                "line": lineno,
            })
            continue

        try:
            time_stamp = datetime.strptime(cols[indices["Datum"]].strip(), _TIMESTAMP_FORMAT)
        except ValueError as exc:
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
            result["errors"].append({
                "code": ERR_ROW_VALUE,
                "message": str(exc),
                "line": lineno,
            })
            continue

        result["records"].append({
            "time_stamp": time_stamp,
            "cell_voltage": cell_voltage,
            "current_density": current_a / active_area,
        })

    return result
