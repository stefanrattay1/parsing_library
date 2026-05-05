"""Public package exports for rdm-parser.

The root package exposes the small API surface intended for downstream use:
format detection via ``parse_file()``, the shared parser contract, direct parser
classes, and standardizer error constants.
"""

from .parsers.base import BaseParser, DescriptiveMetadata, ParseResult
from .parsers.bz011_parser import BZ011Parser
from .parsers.greenlight_parser import GreenlightParser
from .standardizer import (
    ERR_FILE_READ,
    ERR_FORMAT_MISMATCH,
    ERR_FORMAT_UNKNOWN,
    ERR_METADATA_REQUIRED,
    parse_file,
)

__all__ = [
    "parse_file",
    "BaseParser",
    "DescriptiveMetadata",
    "ParseResult",
    "BZ011Parser",
    "GreenlightParser",
    "ERR_FILE_READ",
    "ERR_FORMAT_UNKNOWN",
    "ERR_FORMAT_MISMATCH",
    "ERR_METADATA_REQUIRED",
]
