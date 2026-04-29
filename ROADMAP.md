**This roadmap outlines the planned and already implemented features for the parsing library.**

# Roadmap for Parsing Library Development

## Current Status
- [x] Package skeleton + `pyproject.toml`
- [x] BZ011 parser (initial) with basic tests 
- [x] GitHub Actions: pytest on push + PR (matrix: ubuntu-latest, windows-latest)

## TODO

### Parser correctness (against spec)
- [ ] Standardize output to exactly `time_stamp`, `cell_voltage`, `current_density` (drop source column names), This format already: 2024-08-05T13:11:02
- [ ] BZ011: compute `current_density = Strom I / active_area_cm2` (from metadata JSON), NOTE UNITS
- [ ] Greenlight: parser similar logic as BZ011
- [ ] Handle metadata: parse from JSON, include in output

### Architecture
- [ ] Common parser interface (base class) so new formats can be added without rewrites
- [ ] Handle locale number formats (decimal comma) and encoding (UTF-8 / latin-1) (Can this be auto-detected or should it be a parameter?)
- [ ] Logging for debugging and error handling (e.g. malformed rows, missing metadata)

### Tests
- [started] Fixtures: small BZ011 + Greenlight samples (committed under `tests/fixtures/`)
- [ ] Assert exact schema, field names, types (datetime), and a known-value row
- [ ] Validate metadata against spec (e.g. active area in cm², timestamp format) (Half done for BZ011)
- [ ] Edge cases: empty file, malformed row, missing metadata, CRLF vs LF, .. ?

### CI
- [ ] Add ruff lint step

### Docs (README)
- [ ] Install via `pip install -e .` and `pip install git+https://...` (include link to GitHub repo, also for the second repo), FOCUS on link installation
- [ ] Usage example: parse → records + metadata → JSON matching the spec example
- [ ] Design decisions: metadata handling, timestamp/timezone, units, known limitations
- [ ] State chosen scope (Full Workflow) and AI-assistance disclosure


# Ideas & Notes
- No hard-coded paths; accept file paths / file-like objects; works on Windows + Linux
- All parsing files are in the src folder. This can be used (github link) to install the package.