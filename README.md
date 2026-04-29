# rdm-parser

Modular Python parsing library that standardizes time series data currently for two datatypes plus metadata.

## Scope

This submission uses the **Full Workflow Focus**. This is part one. The seocond part is published here:
 github.com/stefanrattay1/repo2_

## Installation

```bash
# Install directly from GitHub (recommended for downstream projects)
pip install git+https://github.com/stefanrattay1/parsing_library.git

# Editable install from a local clone (for development on this repo)
pip install -e /path/to/parsing_library
```

**Requirements:** Python 3.10 or later

The library is pure Python (≥3.10) with no extern dependencies. For python installation on Linux, you can use:

```bash
sudo apt update && sudo apt install -y python3 python3-pip
```
Windows:

```powershell
# Install latest Python 3.x
winget install Python.Python.3.13

# Or search first to see what's available
winget search Python.Python

```

## Usage

Each parser returns the same `ParseResult` dict:

```python
{
    "metadata": {...} | None,
    "records": [
        {"time_stamp": datetime, "cell_voltage": float, "current_density": float},
        ...
    ],
    "errors": [{"code": str, "message": str, "line": int | None}, ...],
}
```

### BZ011 (.dat + JSON metadata)

```python
from pathlib import Path
from rdm_parser.parsers import parse_bz011

result = parse_bz011(
    Path("BZ011_Rohdaten.dat"),
    Path("metadata_BZ011_Rohdaten.json"),
)

print(len(result["records"]), "rows")
print(result["records"][0])
# {'time_stamp': datetime.datetime(2024, 8, 5, 13, 11, 2),
#  'cell_voltage': 0.5, 'current_density': 0.1}
```

### Greenlight (.csv with metadata preamble)

```python
from rdm_parser.parsers import parse_greenlight

result = parse_greenlight(Path("test_greenlight.csv"))
print(result["metadata"]["Station ID"])
```

### Class API

For longer-lived parser instances or extension points, the underlying classes are also exported:

```python
from rdm_parser.parsers import BZ011Parser, GreenlightParser

result = BZ011Parser(data_path, metadata_path).parse()
```

### Logging

The library uses `logging` with a `NullHandler` — silent by default. Opt in:

```python
import logging
logging.basicConfig(level=logging.DEBUG)
logging.getLogger("rdm_parser").setLevel(logging.DEBUG)
```

Skipped rows are logged at `DEBUG`; file-level read failures at `WARNING`.

## Running Tests
 (in the bsae dir)
```bash
pip install -e ".[dev]"
pytest
ruff check src tests
```

### AI Assistance Disclosure

AI assistance was used for small advice along the way and for agentic coding. Agentic coding (claude code with sonnet4.6 and opus4.7) included: empty structure generation, python methods code generation with input, output and  intended logic as a prompt. The roadmap was written by hand and added to context as a reference for the agent.

## Design Decisions

### Metadata
This is very specific to the files given. Some metadata could also be read from data files themselves.
- **BZ011** stores metadata in a separate JSON file (an array). The first element must contain `active_area_cm2` as a positive number. The whole metadata object is included in the result.
- **Greenlight** stores metadata as `key,value` lines at the top of the CSV, above a dashes separator. All non-empty pairs are collected into the result's `metadata` dict as strings.

### Timestamps
- BZ011 uses the format `%d.%m.%y %H:%M:%S` (day-month-year).
- Greenlight uses `%Y-%m-%d %H:%M:%S.%f`.
- Both return naive `datetime` objects with no timezone. If you need ISO strings or UTC, convert them in your application.

### Units
- BZ011 computes `current_density = current [A] / active_area_cm2 [cm²]`.
- Greenlight provides `current_density` directly in A/cm²; no conversion needed.
- The output is always in **A/cm²**.

### Encoding
- Both parsers try UTF-8 first, then fall back to latin-1 (Greenlight files often contain `cm²` as a non-UTF-8 byte). Pass `encoding="..."` to force a specific encoding.
- Line endings (CRLF and LF) are handled automatically (windows and unix).

### Error Reporting
- If the whole file fails (unreadable, missing column, bad metadata), `errors` is populated and `records` is empty.
- If a single row fails (bad timestamp, non-numeric value, too few columns), that row is skipped and an entry is added to `errors` with the 1-based line number. Parsing continues.

### Known Limitations
- Decimal-comma numbers (e.g. `1,5`) are only supported in BZ011 (`Spg U / V` and `Strom I / A`). Greenlight is assumed to use `.` as the decimal separator.
- Files are loaded fully into memory. Fine for typical testbench output sizes, but not suitable for multi-GB logs.
- No timezone support. Callers must apply the correct timezone if needed.
