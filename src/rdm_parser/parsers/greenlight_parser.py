"""Parser for Greenlight testbench .csv files.

Assumptions / design notes (fill in during implementation):
- Metadata preamble precedes the data table inside the CSV.
- current_density column is already in A/cm2 — direct mapping.
- Timestamps are treated as naive (no timezone) unless stated otherwise.
"""

from pathlib import Path


def parse_greenlight(data_path: Path) -> dict:
    """Parse a Greenlight CSV file (metadata preamble + data table).

    Returns:
        {"metadata": {...}, "records": [{"time_stamp": ..., "cell_voltage": ..., "current_density": ...}, ...]}
    """
    # TODO: implement
    raise NotImplementedError
