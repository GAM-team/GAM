"""Pytest configuration and shared fixtures for GAM tests.

Path setup: GAM's modules use bare 'from util.X import ...' which requires the
gam package directory on sys.path. We add it in a fixture (not at module level)
to avoid shadowing Python's stdlib 'cmd' module during pytest configuration.
"""

# Make pytest discover this directory as the test root without needing
# a pytest.ini at the repo root.  Running `pytest` or `python -m pytest`
# from anywhere in the repo will find tests here.
collect_ignore_glob = []   # nothing to ignore; marker for rootdir detection

import os
import sys

import pytest
import arrow


@pytest.fixture(autouse=True)
def _gam_path_and_globals():
    """Add GAM's package dir to sys.path and initialize minimal global state.

    Done in a fixture rather than at module level to avoid polluting sys.path
    during pytest's own import of stdlib modules (e.g. cmd, which would collide
    with gam/cmd/).
    """
    gam_pkg_dir = os.path.join(os.path.dirname(__file__), '..', 'src', 'gam')
    gam_pkg_dir = os.path.normpath(gam_pkg_dir)

    # Temporarily prepend — will be cleaned up after test
    inserted = False
    if gam_pkg_dir not in sys.path:
        sys.path.insert(0, gam_pkg_dir)
        inserted = True

    # Also need src/ on path for 'gam' package imports
    src_dir = os.path.join(os.path.dirname(__file__), '..', 'src')
    src_dir = os.path.normpath(src_dir)
    src_inserted = False
    if src_dir not in sys.path:
        sys.path.insert(0, src_dir)
        src_inserted = True

    from gamlib import settings as GC
    from gamlib import state as GM

    # Ensure Values dict exists with minimal defaults
    if not GC.Values:
        GC.Values = {}
    GC.Values.setdefault(GC.DOMAIN, 'example.com')
    GC.Values.setdefault(GC.CUSTOMER_ID, 'C00000000')
    GC.Values.setdefault(GC.TIMEZONE, 'UTC')
    GC.Values.setdefault(GC.SHOW_COUNTS_MIN, 0)
    # CSV-related defaults needed by CSVPrintFile
    GC.Values.setdefault(GC.CSV_OUTPUT_HEADER_FORCE, [])
    GC.Values.setdefault(GC.CSV_OUTPUT_HEADER_REQUIRED, [])
    GC.Values.setdefault(GC.CSV_OUTPUT_HEADER_ORDER, [])
    GC.Values.setdefault(GC.CSV_OUTPUT_HEADER_FILTER, [])
    GC.Values.setdefault(GC.CSV_OUTPUT_HEADER_DROP_FILTER, [])
    GC.Values.setdefault(GC.CSV_OUTPUT_ROW_FILTER, [])
    GC.Values.setdefault(GC.CSV_OUTPUT_ROW_FILTER_MODE, 'allmatch')
    GC.Values.setdefault(GC.CSV_OUTPUT_ROW_DROP_FILTER, [])
    GC.Values.setdefault(GC.CSV_OUTPUT_ROW_DROP_FILTER_MODE, 'anymatch')
    GC.Values.setdefault(GC.CSV_OUTPUT_ROW_LIMIT, 0)
    GC.Values.setdefault(GC.CSV_OUTPUT_COLUMN_DELIMITER, ',')
    GC.Values.setdefault(GC.CSV_OUTPUT_QUOTE_CHAR, '"')
    GC.Values.setdefault(GC.CSV_OUTPUT_NO_ESCAPE_CHAR, False)
    GC.Values.setdefault(GC.CSV_OUTPUT_SORT_HEADERS, [])
    GC.Values.setdefault(GC.CSV_OUTPUT_TIMESTAMP_COLUMN, '')
    GC.Values.setdefault(GC.CSV_OUTPUT_LINE_TERMINATOR, '\n')
    GC.Values.setdefault(GC.NEVER_TIME, 'Never')
    GC.Values.setdefault(GC.OUTPUT_TIMEFORMAT, '')

    # Ensure Globals dict exists
    if not GM.Globals:
        GM.Globals = {}
    GM.Globals.setdefault(GM.STDOUT, None)
    GM.Globals.setdefault(GM.STDERR, None)
    GM.Globals.setdefault(GM.SYSEXITRC, 0)
    # CSV-related globals needed by CSVPrintFile
    GM.Globals.setdefault(GM.CSV_OUTPUT_TRANSPOSE, False)
    GM.Globals.setdefault(GM.CSV_TODRIVE, {})
    GM.Globals.setdefault(GM.CSV_OUTPUT_COLUMN_DELIMITER, None)
    GM.Globals.setdefault(GM.CSV_OUTPUT_QUOTE_CHAR, None)
    GM.Globals.setdefault(GM.CSV_OUTPUT_NO_ESCAPE_CHAR, None)
    GM.Globals.setdefault(GM.CSV_OUTPUT_SORT_HEADERS, [])
    GM.Globals.setdefault(GM.CSV_OUTPUT_TIMESTAMP_COLUMN, '')
    if not GM.Globals.get(GM.DATETIME_NOW):
        GM.Globals[GM.DATETIME_NOW] = arrow.now('UTC')

    yield

    # Clean up sys.path to avoid side effects between test files
    if inserted and gam_pkg_dir in sys.path:
        sys.path.remove(gam_pkg_dir)
    if src_inserted and src_dir in sys.path:
        sys.path.remove(src_dir)
