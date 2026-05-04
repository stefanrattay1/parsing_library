"""Tests for the Greenlight parser."""

from datetime import datetime
from pathlib import Path

import pytest

from rdm_parser.parsers.greenlight_parser import (
    ERR_COLUMN_MISSING,
    ERR_DATA_READ,
    ERR_HEADER_MISSING,
    ERR_ROW_SHORT,
    ERR_ROW_TIMESTAMP,
    ERR_ROW_VALUE,
    ERR_ZERO_VOLTAGE,
    GreenlightParser,
    parse_greenlight,
)

FIXTURES = Path(__file__).parent / "fixtures" / "greenlight"
VALID_CSV = FIXTURES / "valid_small.csv"


def _codes(result: dict) -> list[str]:
    return [e["code"] for e in result["errors"]]

DATA_DIR = Path(__file__).parent.parent / "data"
GREENLIGHT_CSV = DATA_DIR / "test_greenlight.csv"


def test_greenlight_returns_expected_keys():
    result = parse_greenlight(VALID_CSV)
    assert set(result.keys()) == {"metadata", "records", "errors"}
    assert result["errors"] == []


def test_greenlight_record_fields():
    result = parse_greenlight(VALID_CSV)
    assert len(result["records"]) == 3
    for rec in result["records"]:
        assert set(rec.keys()) == {"time_stamp", "cell_voltage", "current_density"}
        assert isinstance(rec["time_stamp"], datetime)
        assert isinstance(rec["cell_voltage"], float)
        assert isinstance(rec["current_density"], float)


def test_greenlight_current_density_direct_mapping():
    # Fixture rows have current_density values 0.1, 0.2, 0.4 — taken straight
    # from the source column (already A/cm²), not derived from current/area.
    result = parse_greenlight(VALID_CSV)
    densities = [r["current_density"] for r in result["records"]]
    assert densities == pytest.approx([0.1, 0.2, 0.4])


def test_greenlight_timestamp_ordering_preserved():
    result = parse_greenlight(VALID_CSV)
    stamps = [r["time_stamp"] for r in result["records"]]
    assert stamps == sorted(stamps)
    assert stamps[0] == datetime(2024, 1, 1, 0, 0, 0)


def test_greenlight_metadata_includes_known_keys():
    result = parse_greenlight(VALID_CSV)
    assert result["metadata"]["Station ID"] == "G99-TEST"
    assert result["metadata"]["Test Name"] == "fixture-small"


def test_greenlight_cell_voltage_from_cell_voltage_001():
    result = parse_greenlight(VALID_CSV)
    voltages = [r["cell_voltage"] for r in result["records"]]
    assert voltages == pytest.approx([0.7, 0.69, 0.68])


# --- File-level errors ------------------------------------------------------

def test_data_read_error_when_missing(tmp_path):
    missing = tmp_path / "does_not_exist.csv"
    result = parse_greenlight(missing)
    assert _codes(result) == [ERR_DATA_READ]
    assert result["records"] == []


def test_data_read_error_when_empty():
    result = parse_greenlight(FIXTURES / "empty.csv")
    assert _codes(result) == [ERR_DATA_READ]
    assert result["records"] == []


def test_header_missing_error_when_no_time_stamp_row():
    result = parse_greenlight(FIXTURES / "no_header.csv")
    assert _codes(result) == [ERR_HEADER_MISSING]
    assert result["records"] == []


def test_column_missing_error():
    result = parse_greenlight(FIXTURES / "missing_column.csv")
    assert ERR_COLUMN_MISSING in _codes(result)
    assert result["records"] == []
    msg = next(e["message"] for e in result["errors"] if e["code"] == ERR_COLUMN_MISSING)
    assert "current_density" in msg


# --- Row-level errors -------------------------------------------------------

def test_bad_rows_skipped_but_good_rows_kept():
    result = parse_greenlight(FIXTURES / "bad_rows.csv")
    # 5 data rows: ok, bad timestamp, bad value, too short, ok → 2 records, 3 errors.
    assert len(result["records"]) == 2
    assert len(result["errors"]) == 3
    codes = _codes(result)
    assert ERR_ROW_TIMESTAMP in codes
    assert ERR_ROW_VALUE in codes
    assert ERR_ROW_SHORT in codes


def test_bad_rows_error_line_numbers_are_1_based():
    result = parse_greenlight(FIXTURES / "bad_rows.csv")
    by_code = {e["code"]: e for e in result["errors"]}
    # preamble = 6 lines, header = line 7, then ok(8), bad ts(9), bad val(10), short(11), ok(12).
    assert by_code[ERR_ROW_TIMESTAMP]["line"] == 9
    assert by_code[ERR_ROW_VALUE]["line"] == 10
    assert by_code[ERR_ROW_SHORT]["line"] == 11


def test_bad_rows_kept_records_are_the_valid_ones():
    result = parse_greenlight(FIXTURES / "bad_rows.csv")
    stamps = [r["time_stamp"] for r in result["records"]]
    assert stamps == [
        datetime(2024, 1, 1, 0, 0, 0),
        datetime(2024, 1, 1, 0, 0, 4),
    ]


def test_crlf_data_file_parses_identically_to_lf():
    lf = parse_greenlight(VALID_CSV)
    crlf = parse_greenlight(FIXTURES / "valid_small_crlf.csv")
    assert crlf["errors"] == []
    assert [r["time_stamp"] for r in crlf["records"]] == [r["time_stamp"] for r in lf["records"]]


def test_class_api_matches_function_api():
    fn_result = parse_greenlight(VALID_CSV)
    cls_result = GreenlightParser(VALID_CSV).parse()
    assert cls_result["records"] == fn_result["records"]
    assert cls_result["metadata"] == fn_result["metadata"]


def test_zero_voltage_with_current_emits_warning_but_keeps_record(tmp_path):
    data_path = tmp_path / "zero_voltage_warning.csv"
    data_path.write_text(
        "Station ID,G99-TEST\n"
        "Test Name,fixture-small\n"
        "---\n"
        "Long Name Row,ignored\n"
        "Units Row,ignored\n"
        "Time Stamp,cell_voltage_001,current_density\n"
        "2024-01-01 00:00:00.000,0,0.1\n",
        encoding="utf-8",
    )

    result = parse_greenlight(data_path)

    assert len(result["records"]) == 1
    assert _codes(result) == [ERR_ZERO_VOLTAGE]
    assert result["errors"][0]["line"] == 7
    assert result["records"][0]["cell_voltage"] == 0.0
    assert result["records"][0]["current_density"] == pytest.approx(0.1)


def test_zero_voltage_without_current_does_not_emit_warning(tmp_path):
    data_path = tmp_path / "resting_zero_voltage.csv"
    data_path.write_text(
        "Station ID,G99-TEST\n"
        "Test Name,fixture-small\n"
        "---\n"
        "Long Name Row,ignored\n"
        "Units Row,ignored\n"
        "Time Stamp,cell_voltage_001,current_density\n"
        "2024-01-01 00:00:00.000,0,0\n",
        encoding="utf-8",
    )

    result = parse_greenlight(data_path)

    assert result["errors"] == []
    assert len(result["records"]) == 1


# --- Smoke test against the real data file ---------------------------------

@pytest.mark.skipif(not GREENLIGHT_CSV.exists(), reason="live data file not present")
def test_greenlight_parses_full_data_file_without_errors():
    result = parse_greenlight(GREENLIGHT_CSV)
    assert result["errors"] == []
    assert len(result["records"]) > 300
    assert result["metadata"].get("Station ID") == "G21-2370"
