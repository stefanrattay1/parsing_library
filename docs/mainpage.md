# rdm-parser

`rdm-parser` is a pure-Python library for standardizing time series data from multiple lab export formats into one shared result shape.

## What The Library Provides

- `parse_file()` for format detection and dispatch.
- Dedicated parsers for BZ011 and Greenlight input files.
- A shared `ParseResult` contract with `metadata`, `records`, and `errors`.
- Non-fatal row-level error reporting so callers can keep partial data.

## Public API

The generated API reference focuses on the exported surface from `rdm_parser`:

- `parse_file()` for format auto-detection.
- `BaseParser` as the minimal parser contract.
- `ParseResult` as the standard result schema.
- `BZ011Parser` and `GreenlightParser` for direct parser usage.
- Standardizer error constants exposed from the package root.

## Data Model

All parsers return a dictionary with this shape:

```python
{
    "metadata": {
        "schema": "rdm_parser.metadata.v1",
        "source_format": "bz011" | "greenlight",
        "station_id": str | None,
        "test_name": str | None,
        "started_at": str | None,
        "active_area_cm2": float | None,
        "source_metadata": {...},
        ...
    } | None,
    "records": [
        {"time_stamp": datetime, "cell_voltage": float, "current_density": float},
        ...
    ],
    "errors": [{"code": str, "message": str, "line": int | None}, ...],
}
```

## Supported Formats

### BZ011

- Reads a tab-separated `.dat` file together with a JSON metadata file.
- Computes current density from current and `active_area_cm2`.

### Greenlight

- Reads a `.csv` file with a metadata preamble and row data.
- Uses the current density values already present in the file.

## Build The Docs Locally

Run Doxygen from the repository root:

```bash
doxygen Doxyfile
```

Generated HTML is written to `docs/doxygen/html/index.html`.