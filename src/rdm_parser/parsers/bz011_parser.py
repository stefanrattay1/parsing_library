"""Parser for BZ011 testbench .dat files.

Assumptions / design notes (fill in during implementation):
- Datum column uses day-month-year ordering.
- current_density = Strom I / A  /  active_area_cm2  (from metadata JSON).
- Timestamps are treated as naive (no timezone) unless stated otherwise.
"""

from pathlib import Path


def parse_bz011(data_path: Path, metadata_path: Path) -> dict:
    """Parse a BZ011 .dat file together with its companion metadata JSON.

    Returns:
        {"metadata": {...}, "records": [{"time_stamp": ..., "cell_voltage": ..., "current_density": ...}, ...]}
    """
    # TODO: implement
    raise NotImplementedError
