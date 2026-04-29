# rdm-parser

Reusable Python parsing library that standardizes time series data from multiple testbench formats (BZ011, Greenlight) into a common schema compatible with MongoDB Time Series collections.

## Scope

This submission uses the **Full Workflow Focus**. AI assistance was used for … *(fill in)*.

## Installation

```bash
# Editable install from local clone
pip install -e /path/to/repo1_parsing_library

# Or directly from GitHub
pip install git+https://github.com/<user>/repo1_parsing_library.git
```

## Usage

```python
# TODO: add minimal usage example once implementation complete
```

## Running Tests

```bash
pip install -e ".[dev]"
pytest
```

## Design Decisions

### Metadata Handling
*(TODO)*

### Timestamp Handling
*(TODO — BZ011 Datum uses day-month-year ordering; timestamps are treated as naive/local unless documented otherwise)*

### Unit Handling
*(TODO — BZ011 current_density is calculated as current_A / active_area_cm2)*

### Known Limitations
*(TODO)*
