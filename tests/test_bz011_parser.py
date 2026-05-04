"""Tests for the BZ011 parser."""

from datetime import datetime
from pathlib import Path

import pytest

from rdm_parser.parsers.bz011_parser import (
    ERR_COLUMN_MISSING,
    ERR_DATA_READ,
    ERR_METADATA_INVALID,
    ERR_METADATA_JSON,
    ERR_METADATA_KEY,
    ERR_METADATA_READ,
    ERR_ROW_SHORT,
    ERR_ROW_TIMESTAMP,
    ERR_ROW_VALUE,
    ERR_ZERO_VOLTAGE,
    BZ011Parser,
    parse_bz011,
)

FIXTURES = Path(__file__).parent / "fixtures" / "bz011"
VALID_DAT = FIXTURES / "valid_small.dat"
VALID_META = FIXTURES / "valid_small.json"


def _codes(result: dict) -> list[str]:
    return [e["code"] for e in result["errors"]]


# --- Happy path -------------------------------------------------------------

def test_valid_small_parses_without_errors():
    result = parse_bz011(VALID_DAT, VALID_META)
    assert result["errors"] == []
    assert len(result["records"]) == 3


def test_valid_small_returns_expected_keys():
    result = parse_bz011(VALID_DAT, VALID_META)
    assert set(result.keys()) == {"metadata", "records", "errors"}


def test_valid_small_record_fields():
    result = parse_bz011(VALID_DAT, VALID_META)
    for rec in result["records"]:
        assert set(rec.keys()) == {"time_stamp", "cell_voltage", "current_density"}
        assert isinstance(rec["time_stamp"], datetime)
        assert isinstance(rec["cell_voltage"], float)
        assert isinstance(rec["current_density"], float)


def test_valid_small_current_density_calculation():
    # active_area_cm2 = 25, first row current = 2.5 → density = 0.1
    result = parse_bz011(VALID_DAT, VALID_META)
    assert result["records"][0]["current_density"] == pytest.approx(0.1)
    assert result["records"][1]["current_density"] == pytest.approx(0.2)
    assert result["records"][2]["current_density"] == pytest.approx(0.4)


def test_valid_small_timestamp_ordering_preserved():
    result = parse_bz011(VALID_DAT, VALID_META)
    stamps = [r["time_stamp"] for r in result["records"]]
    assert stamps == sorted(stamps)


def test_valid_small_metadata_passthrough():
    result = parse_bz011(VALID_DAT, VALID_META)
    assert result["metadata"]["active_area_cm2"] == 25
    assert result["metadata"]["testbench"] == "BZ011"


# --- File-level errors ------------------------------------------------------

def test_metadata_read_error_when_missing(tmp_path):
    missing = tmp_path / "does_not_exist.json"
    result = parse_bz011(VALID_DAT, missing)
    assert _codes(result) == [ERR_METADATA_READ]
    assert result["records"] == []
    assert result["metadata"] is None


def test_metadata_json_error_on_invalid_json():
    result = parse_bz011(VALID_DAT, FIXTURES / "bad_metadata.json")
    assert _codes(result) == [ERR_METADATA_JSON]
    assert result["records"] == []


def test_metadata_key_error_when_active_area_missing():
    result = parse_bz011(VALID_DAT, FIXTURES / "missing_key.json")
    assert _codes(result) == [ERR_METADATA_KEY]
    assert result["records"] == []


def test_metadata_invalid_when_active_area_not_positive():
    result = parse_bz011(VALID_DAT, FIXTURES / "negative_area.json")
    assert _codes(result) == [ERR_METADATA_INVALID]
    assert result["records"] == []


def test_metadata_invalid_when_active_area_not_numeric():
    result = parse_bz011(VALID_DAT, FIXTURES / "string_area.json")
    assert _codes(result) == [ERR_METADATA_INVALID]
    assert result["records"] == []


def test_data_read_error_when_missing(tmp_path):
    missing = tmp_path / "does_not_exist.dat"
    result = parse_bz011(missing, VALID_META)
    assert _codes(result) == [ERR_DATA_READ]
    assert result["records"] == []
    # metadata still loaded successfully before data read failed
    assert result["metadata"] is not None


def test_data_read_error_when_empty():
    result = parse_bz011(FIXTURES / "empty.dat", VALID_META)
    assert _codes(result) == [ERR_DATA_READ]
    assert result["records"] == []


def test_column_missing_error():
    result = parse_bz011(FIXTURES / "missing_column.dat", VALID_META)
    assert ERR_COLUMN_MISSING in _codes(result)
    assert result["records"] == []
    msg = next(e["message"] for e in result["errors"] if e["code"] == ERR_COLUMN_MISSING)
    assert "Strom I / A" in msg


# --- Row-level errors -------------------------------------------------------

def test_bad_rows_skipped_but_good_rows_kept():
    result = parse_bz011(FIXTURES / "bad_rows.dat", VALID_META)
    # 5 data rows: row 1 OK, row 2 bad timestamp, row 3 bad value,
    # row 4 too short, row 5 OK → 2 valid records, 3 errors.
    assert len(result["records"]) == 2
    assert len(result["errors"]) == 3
    codes = _codes(result)
    assert ERR_ROW_TIMESTAMP in codes
    assert ERR_ROW_VALUE in codes
    assert ERR_ROW_SHORT in codes


def test_bad_rows_error_line_numbers_are_1_based():
    result = parse_bz011(FIXTURES / "bad_rows.dat", VALID_META)
    by_code = {e["code"]: e for e in result["errors"]}
    # Header is line 1 → bad timestamp on line 3, bad value on line 4, short row on line 5.
    assert by_code[ERR_ROW_TIMESTAMP]["line"] == 3
    assert by_code[ERR_ROW_VALUE]["line"] == 4
    assert by_code[ERR_ROW_SHORT]["line"] == 5


def test_crlf_data_file_parses_identically_to_lf():
    lf = parse_bz011(VALID_DAT, VALID_META)
    crlf = parse_bz011(FIXTURES / "valid_small_crlf.dat", VALID_META)
    assert crlf["errors"] == []
    assert [r["time_stamp"] for r in crlf["records"]] == [r["time_stamp"] for r in lf["records"]]
    assert len(crlf["records"]) == len(lf["records"]) == 3


def test_class_api_matches_function_api():
    fn_result = parse_bz011(VALID_DAT, VALID_META)
    cls_result = BZ011Parser(VALID_DAT, VALID_META).parse()
    assert cls_result["records"] == fn_result["records"]
    assert cls_result["metadata"] == fn_result["metadata"]


def test_bad_rows_kept_records_are_the_valid_ones():
    result = parse_bz011(FIXTURES / "bad_rows.dat", VALID_META)
    stamps = [r["time_stamp"] for r in result["records"]]
    assert stamps == [
        datetime(2024, 8, 5, 13, 11, 2),
        datetime(2024, 8, 5, 13, 11, 6),
    ]


def test_zero_voltage_with_current_emits_warning_but_keeps_record(tmp_path):
    data_path = tmp_path / "initialization_warning.dat"
    data_path.write_text(
        "Datum\tSpg U / V\tStrom I / A\tSet Kommentar\n"
        "05.08.24 13:13:57\t0\t0.488\tInitialisierung_0\n",
        encoding="utf-8",
    )

    result = parse_bz011(data_path, VALID_META)

    assert len(result["records"]) == 1
    assert _codes(result) == [ERR_ZERO_VOLTAGE]
    assert result["errors"][0]["line"] == 2
    assert "Initialisierung_0" in result["errors"][0]["message"]
    assert result["records"][0]["cell_voltage"] == 0.0
    assert result["records"][0]["current_density"] == pytest.approx(0.01952)


def test_zero_voltage_without_current_does_not_emit_warning(tmp_path):
    data_path = tmp_path / "resting_zero_voltage.dat"
    data_path.write_text(
        "Datum\tSpg U / V\tStrom I / A\n"
        "05.08.24 13:13:57\t0\t0\n",
        encoding="utf-8",
    )

    result = parse_bz011(data_path, VALID_META)

    assert result["errors"] == []
    assert len(result["records"]) == 1
