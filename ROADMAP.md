**This roadmap outlines the planned and already implemented features for the parsing library.**

# Roadmap for Parsing Library Development

## Current Status
- [x] Package skeleton + `pyproject.toml`
- [x] BZ011 parser (initial) with basic tests
- [x] GitHub Actions: pytest on push + PR (matrix: ubuntu-latest, windows-latest)
- [x] Standardize output to exactly `time_stamp`, `cell_voltage`, `current_density`
- [x] BZ011: compute `current_density = Strom I / active_area_cm2` (units → A/cm²)
- [x] Greenlight: parser with same output schema as BZ011
- [x] Handle metadata: parsed from JSON (BZ011) / preamble (Greenlight) and included in output
- [x] Common parser interface (`BaseParser` ABC + `ParseResult` TypedDict)
- [x] Encoding handling: UTF-8 → latin-1 fallback, plus optional `encoding=` parameter
- [x] Light logging via stdlib `logging` (DEBUG on row skips, WARNING on file errors; NullHandler by default)
- [x] Fixtures: BZ011 + Greenlight samples under `tests/fixtures/`
- [x] Assert exact schema, field names, types, known-value rows
- [x] Validate metadata against spec (BZ011 `active_area_cm2` numeric + positive)
- [x] Edge cases: empty file, malformed row, missing metadata, missing column, CRLF vs LF
- [x] Add ruff lint step (CI + `pyproject.toml` config)
- [x] README: install (incl. `pip install git+https://...`), usage example, design decisions
- [x] Fill in scope statement and AI-assistance disclosure in README

## TODO

### Parser correctness
- [ ] Locale number formats (decimal comma) — currently BZ011-specific in `_parse_float`; consider a shared helper if a new format needs it.

# Ideas & Notes
- Maybe only certain tests. Tests are a little excessive right now.
- No hard-coded paths; accept file paths / file-like objects; works on Windows + Linux
- All parsing files are in the src folder. This can be used (github link) to install the package.
