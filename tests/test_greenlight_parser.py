"""Tests for the Greenlight parser."""

import pytest
from pathlib import Path

DATA_DIR = Path(__file__).parent.parent / "data"
GREENLIGHT_CSV = DATA_DIR / "test_greenlight.csv"


def test_greenlight_returns_expected_keys():
    # TODO: implement — result should have "metadata" and "records" keys
    pytest.skip("not implemented yet")


def test_greenlight_record_fields():
    # TODO: each record must have exactly time_stamp, cell_voltage, current_density
    pytest.skip("not implemented yet")


def test_greenlight_current_density_direct_mapping():
    # TODO: current_density is a direct mapping from the source column (already A/cm2)
    pytest.skip("not implemented yet")


def test_greenlight_timestamp_ordering_preserved():
    # TODO: timestamps must appear in the same order as in the source file
    pytest.skip("not implemented yet")
