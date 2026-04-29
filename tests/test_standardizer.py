"""Tests for the top-level format-detecting dispatcher."""

from datetime import datetime
from pathlib import Path

from rdm_parser.standardizer import (
    ERR_FILE_READ,
    ERR_FORMAT_MISMATCH,
    ERR_FORMAT_UNKNOWN,
    ERR_METADATA_REQUIRED,
    parse_file,
)

ROOT = Path(__file__).parent
BZ011_DAT = ROOT / "fixtures" / "bz011" / "valid_small.dat"
BZ011_META = ROOT / "fixtures" / "bz011" / "valid_small.json"
GREENLIGHT_CSV = ROOT / "fixtures" / "greenlight" / "valid_small.csv"

STD_FIX = ROOT / "fixtures" / "standardizer"


def _codes(result: dict) -> list[str]:
    return [e["code"] for e in result["errors"]]


# --- Happy paths -----------------------------------------------------------

def test_dispatch_bz011_by_extension_and_content():
    result = parse_file(BZ011_DAT, BZ011_META)
    assert result["errors"] == []
    assert len(result["records"]) == 3
    assert result["records"][0]["time_stamp"] == datetime(2024, 8, 5, 13, 11, 2)
    assert result["metadata"]["testbench"] == "BZ011"


def test_dispatch_greenlight_by_extension_and_content():
    result = parse_file(GREENLIGHT_CSV)
    assert result["errors"] == []
    assert len(result["records"]) == 3
    assert result["metadata"]["Station ID"] == "G99-TEST"


def test_dispatch_bz011_when_extension_unknown_but_content_recognised():
    result = parse_file(STD_FIX / "bz011_as_txt.txt", BZ011_META)
    assert result["errors"] == []
    assert len(result["records"]) == 3


def test_dispatch_greenlight_when_extension_unknown_but_content_recognised():
    result = parse_file(STD_FIX / "greenlight_as_txt.txt")
    assert result["errors"] == []
    assert len(result["records"]) == 3


# --- Detection errors ------------------------------------------------------

def test_format_mismatch_csv_extension_with_bz011_content():
    result = parse_file(STD_FIX / "extension_lies.csv", BZ011_META)
    assert _codes(result) == [ERR_FORMAT_MISMATCH]
    assert result["records"] == []
    assert "greenlight" in result["errors"][0]["message"]
    assert "bz011" in result["errors"][0]["message"]


def test_format_mismatch_dat_extension_with_greenlight_content():
    result = parse_file(STD_FIX / "extension_lies.dat")
    assert _codes(result) == [ERR_FORMAT_MISMATCH]
    assert result["records"] == []


def test_format_unknown_when_neither_extension_nor_content_match():
    result = parse_file(STD_FIX / "junk.txt")
    assert _codes(result) == [ERR_FORMAT_UNKNOWN]
    assert result["records"] == []


def test_metadata_required_error_for_bz011_without_metadata_path():
    result = parse_file(BZ011_DAT)
    assert _codes(result) == [ERR_METADATA_REQUIRED]
    assert result["records"] == []


def test_file_read_error_when_missing(tmp_path):
    missing = tmp_path / "nope.dat"
    result = parse_file(missing)
    assert _codes(result) == [ERR_FILE_READ]
    assert result["records"] == []


def test_metadata_required_takes_precedence_over_actual_parse():
    # Even though the .dat file is well-formed, we must error out before parsing
    # if no metadata path was supplied.
    result = parse_file(BZ011_DAT, metadata_path=None)
    assert _codes(result) == [ERR_METADATA_REQUIRED]


# --- Forwarding ------------------------------------------------------------

def test_metadata_path_ignored_for_greenlight():
    # Passing a metadata_path for a Greenlight file should not break dispatch.
    result = parse_file(GREENLIGHT_CSV, metadata_path=BZ011_META)
    assert result["errors"] == []
    assert len(result["records"]) == 3


def test_accepts_str_paths():
    result = parse_file(str(GREENLIGHT_CSV))
    assert result["errors"] == []
    assert len(result["records"]) == 3
