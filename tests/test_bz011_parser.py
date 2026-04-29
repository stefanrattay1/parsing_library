"""Tests for the BZ011 parser."""

import pytest
from pathlib import Path

DATA_DIR = Path(__file__).parent.parent / "data"
BZ011_DAT = DATA_DIR / "BZ011_Rohdaten.dat"
BZ011_META = DATA_DIR / "metadata_BZ011_Rohdaten.json"


def test_bz011_returns_expected_keys():
    # TODO: implement — result should have "metadata" and "records" keys
    pytest.skip("not implemented yet")


def test_bz011_record_fields():
    # TODO: each record must have exactly time_stamp, cell_voltage, current_density
    pytest.skip("not implemented yet")


def test_bz011_current_density_calculation():
    # TODO: verify current_density = current_A / active_area_cm2
    pytest.skip("not implemented yet")


def test_bz011_timestamp_ordering_preserved():
    # TODO: timestamps must appear in the same order as in the source file
    pytest.skip("not implemented yet")
