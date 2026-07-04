"""Unit tests for gam.util.csv_pf — RowFilterMatch and CSV output functions.

Tests cover all filter types: regex, boolean, count, date, time, length,
text, data, ranges, and their negations/combinations. Also covers
CSVPrintFile header processing, title management, and output formatting.
"""

import re

import pytest
import arrow


# ---------------------------------------------------------------------------
# RowFilterMatch tests
# ---------------------------------------------------------------------------

class TestRowFilterMatchRegex:
  """Test regex and notregex filter types."""

  def test_regex_match(self):
    from gam.util.csv_pf import RowFilterMatch
    row = {'name': 'John Smith', 'email': 'john@example.com'}
    titlesList = ['name', 'email']
    # filterVal: (columnPat, anyMatch, filterType, ...)
    columnPat = re.compile('^name$', re.IGNORECASE)
    rowFilter = [(columnPat, True, 'regex', re.compile('John', re.IGNORECASE))]
    assert RowFilterMatch(row, titlesList, rowFilter, True, [], True) is True

  def test_regex_no_match(self):
    from gam.util.csv_pf import RowFilterMatch
    row = {'name': 'Jane Doe'}
    titlesList = ['name']
    columnPat = re.compile('^name$', re.IGNORECASE)
    rowFilter = [(columnPat, True, 'regex', re.compile('^John$', re.IGNORECASE))]
    assert RowFilterMatch(row, titlesList, rowFilter, True, [], True) is False

  def test_notregex_match(self):
    from gam.util.csv_pf import RowFilterMatch
    row = {'name': 'Jane Doe'}
    titlesList = ['name']
    columnPat = re.compile('^name$', re.IGNORECASE)
    rowFilter = [(columnPat, True, 'notregex', re.compile('^John$', re.IGNORECASE))]
    assert RowFilterMatch(row, titlesList, rowFilter, True, [], True) is True

  def test_notregex_no_match(self):
    from gam.util.csv_pf import RowFilterMatch
    row = {'name': 'John Smith'}
    titlesList = ['name']
    columnPat = re.compile('^name$', re.IGNORECASE)
    rowFilter = [(columnPat, True, 'notregex', re.compile('John', re.IGNORECASE))]
    assert RowFilterMatch(row, titlesList, rowFilter, True, [], True) is False

  def test_regex_case_sensitive(self):
    from gam.util.csv_pf import RowFilterMatch
    row = {'name': 'john smith'}
    titlesList = ['name']
    columnPat = re.compile('^name$', re.IGNORECASE)
    # Case-sensitive regex should NOT match lowercase
    rowFilter = [(columnPat, True, 'regex', re.compile('^John', 0))]
    assert RowFilterMatch(row, titlesList, rowFilter, True, [], True) is False

  def test_regex_wildcard_column(self):
    """Regex column pattern matching multiple columns."""
    from gam.util.csv_pf import RowFilterMatch
    row = {'name': 'no', 'email': 'yes@match.com'}
    titlesList = ['name', 'email']
    # anyMatch=True: at least one column must match
    columnPat = re.compile('.*', re.IGNORECASE)
    rowFilter = [(columnPat, True, 'regex', re.compile('match', re.IGNORECASE))]
    assert RowFilterMatch(row, titlesList, rowFilter, True, [], True) is True


class TestRowFilterMatchBoolean:
  """Test boolean filter type."""

  def test_boolean_true_match(self):
    from gam.util.csv_pf import RowFilterMatch
    row = {'active': 'True'}
    titlesList = ['active']
    columnPat = re.compile('^active$', re.IGNORECASE)
    rowFilter = [(columnPat, True, 'boolean', True)]
    assert RowFilterMatch(row, titlesList, rowFilter, True, [], True) is True

  def test_boolean_true_no_match(self):
    from gam.util.csv_pf import RowFilterMatch
    row = {'active': 'False'}
    titlesList = ['active']
    columnPat = re.compile('^active$', re.IGNORECASE)
    rowFilter = [(columnPat, True, 'boolean', True)]
    assert RowFilterMatch(row, titlesList, rowFilter, True, [], True) is False

  def test_boolean_false_match(self):
    from gam.util.csv_pf import RowFilterMatch
    row = {'active': 'False'}
    titlesList = ['active']
    columnPat = re.compile('^active$', re.IGNORECASE)
    rowFilter = [(columnPat, True, 'boolean', False)]
    assert RowFilterMatch(row, titlesList, rowFilter, True, [], True) is True

  def test_boolean_native_bool(self):
    from gam.util.csv_pf import RowFilterMatch
    row = {'active': True}
    titlesList = ['active']
    columnPat = re.compile('^active$', re.IGNORECASE)
    rowFilter = [(columnPat, True, 'boolean', True)]
    assert RowFilterMatch(row, titlesList, rowFilter, True, [], True) is True

  def test_boolean_blank_is_false(self):
    """Blank string should be treated as False."""
    from gam.util.csv_pf import RowFilterMatch
    row = {'active': ''}
    titlesList = ['active']
    columnPat = re.compile('^active$', re.IGNORECASE)
    rowFilter = [(columnPat, True, 'boolean', False)]
    assert RowFilterMatch(row, titlesList, rowFilter, True, [], True) is True


class TestRowFilterMatchCount:
  """Test count/number filter types."""

  def test_count_equals(self):
    from gam.util.csv_pf import RowFilterMatch
    row = {'count': '5'}
    titlesList = ['count']
    columnPat = re.compile('^count$', re.IGNORECASE)
    rowFilter = [(columnPat, True, 'count', '=', 5)]
    assert RowFilterMatch(row, titlesList, rowFilter, True, [], True) is True

  def test_count_greater(self):
    from gam.util.csv_pf import RowFilterMatch
    row = {'count': '10'}
    titlesList = ['count']
    columnPat = re.compile('^count$', re.IGNORECASE)
    rowFilter = [(columnPat, True, 'count', '>', 5)]
    assert RowFilterMatch(row, titlesList, rowFilter, True, [], True) is True

  def test_count_less(self):
    from gam.util.csv_pf import RowFilterMatch
    row = {'count': '3'}
    titlesList = ['count']
    columnPat = re.compile('^count$', re.IGNORECASE)
    rowFilter = [(columnPat, True, 'count', '<', 5)]
    assert RowFilterMatch(row, titlesList, rowFilter, True, [], True) is True

  def test_count_not_equal(self):
    from gam.util.csv_pf import RowFilterMatch
    row = {'count': '3'}
    titlesList = ['count']
    columnPat = re.compile('^count$', re.IGNORECASE)
    rowFilter = [(columnPat, True, 'count', '!=', 5)]
    assert RowFilterMatch(row, titlesList, rowFilter, True, [], True) is True

  def test_count_gte(self):
    from gam.util.csv_pf import RowFilterMatch
    row = {'count': '5'}
    titlesList = ['count']
    columnPat = re.compile('^count$', re.IGNORECASE)
    rowFilter = [(columnPat, True, 'count', '>=', 5)]
    assert RowFilterMatch(row, titlesList, rowFilter, True, [], True) is True

  def test_count_lte(self):
    from gam.util.csv_pf import RowFilterMatch
    row = {'count': '5'}
    titlesList = ['count']
    columnPat = re.compile('^count$', re.IGNORECASE)
    rowFilter = [(columnPat, True, 'count', '<=', 5)]
    assert RowFilterMatch(row, titlesList, rowFilter, True, [], True) is True

  def test_count_blank_is_zero(self):
    """Blank string count should be treated as 0."""
    from gam.util.csv_pf import RowFilterMatch
    row = {'count': ''}
    titlesList = ['count']
    columnPat = re.compile('^count$', re.IGNORECASE)
    rowFilter = [(columnPat, True, 'count', '=', 0)]
    assert RowFilterMatch(row, titlesList, rowFilter, True, [], True) is True

  def test_count_non_digit_no_match(self):
    from gam.util.csv_pf import RowFilterMatch
    row = {'count': 'abc'}
    titlesList = ['count']
    columnPat = re.compile('^count$', re.IGNORECASE)
    rowFilter = [(columnPat, True, 'count', '=', 0)]
    assert RowFilterMatch(row, titlesList, rowFilter, True, [], True) is False

  def test_count_native_int(self):
    from gam.util.csv_pf import RowFilterMatch
    row = {'count': 5}
    titlesList = ['count']
    columnPat = re.compile('^count$', re.IGNORECASE)
    rowFilter = [(columnPat, True, 'count', '=', 5)]
    assert RowFilterMatch(row, titlesList, rowFilter, True, [], True) is True

  def test_number_alias(self):
    """'number' should work the same as 'count'."""
    from gam.util.csv_pf import RowFilterMatch
    row = {'val': '42'}
    titlesList = ['val']
    columnPat = re.compile('^val$', re.IGNORECASE)
    rowFilter = [(columnPat, True, 'number', '=', 42)]
    assert RowFilterMatch(row, titlesList, rowFilter, True, [], True) is True


class TestRowFilterMatchCountRange:
  """Test countrange/numberrange filter types."""

  def test_countrange_in_range(self):
    from gam.util.csv_pf import RowFilterMatch
    row = {'count': '5'}
    titlesList = ['count']
    columnPat = re.compile('^count$', re.IGNORECASE)
    rowFilter = [(columnPat, True, 'countrange', '=', 1, 10)]
    assert RowFilterMatch(row, titlesList, rowFilter, True, [], True) is True

  def test_countrange_out_of_range(self):
    from gam.util.csv_pf import RowFilterMatch
    row = {'count': '15'}
    titlesList = ['count']
    columnPat = re.compile('^count$', re.IGNORECASE)
    rowFilter = [(columnPat, True, 'countrange', '=', 1, 10)]
    assert RowFilterMatch(row, titlesList, rowFilter, True, [], True) is False

  def test_countrange_not_equal(self):
    """countrange with != should return True when value IS outside range."""
    from gam.util.csv_pf import RowFilterMatch
    row = {'count': '15'}
    titlesList = ['count']
    columnPat = re.compile('^count$', re.IGNORECASE)
    rowFilter = [(columnPat, True, 'countrange', '!=', 1, 10)]
    assert RowFilterMatch(row, titlesList, rowFilter, True, [], True) is True

  def test_countrange_boundary(self):
    """Boundary values should be inclusive."""
    from gam.util.csv_pf import RowFilterMatch
    row = {'count': '10'}
    titlesList = ['count']
    columnPat = re.compile('^count$', re.IGNORECASE)
    rowFilter = [(columnPat, True, 'countrange', '=', 1, 10)]
    assert RowFilterMatch(row, titlesList, rowFilter, True, [], True) is True


class TestRowFilterMatchLength:
  """Test length and lengthrange filter types."""

  def test_length_equals(self):
    from gam.util.csv_pf import RowFilterMatch
    row = {'name': 'hello'}
    titlesList = ['name']
    columnPat = re.compile('^name$', re.IGNORECASE)
    rowFilter = [(columnPat, True, 'length', '=', 5)]
    assert RowFilterMatch(row, titlesList, rowFilter, True, [], True) is True

  def test_length_greater(self):
    from gam.util.csv_pf import RowFilterMatch
    row = {'name': 'hello world'}
    titlesList = ['name']
    columnPat = re.compile('^name$', re.IGNORECASE)
    rowFilter = [(columnPat, True, 'length', '>', 5)]
    assert RowFilterMatch(row, titlesList, rowFilter, True, [], True) is True

  def test_lengthrange_in_range(self):
    from gam.util.csv_pf import RowFilterMatch
    row = {'name': 'hello'}
    titlesList = ['name']
    columnPat = re.compile('^name$', re.IGNORECASE)
    rowFilter = [(columnPat, True, 'lengthrange', '=', 3, 8)]
    assert RowFilterMatch(row, titlesList, rowFilter, True, [], True) is True

  def test_length_non_string_no_match(self):
    from gam.util.csv_pf import RowFilterMatch
    row = {'name': 12345}
    titlesList = ['name']
    columnPat = re.compile('^name$', re.IGNORECASE)
    rowFilter = [(columnPat, True, 'length', '=', 5)]
    assert RowFilterMatch(row, titlesList, rowFilter, True, [], True) is False


class TestRowFilterMatchText:
  """Test text and textrange filter types."""

  def test_text_equals(self):
    from gam.util.csv_pf import RowFilterMatch
    row = {'status': 'active'}
    titlesList = ['status']
    columnPat = re.compile('^status$', re.IGNORECASE)
    rowFilter = [(columnPat, True, 'text', '=', 'active')]
    assert RowFilterMatch(row, titlesList, rowFilter, True, [], True) is True

  def test_text_not_equal(self):
    from gam.util.csv_pf import RowFilterMatch
    row = {'status': 'inactive'}
    titlesList = ['status']
    columnPat = re.compile('^status$', re.IGNORECASE)
    rowFilter = [(columnPat, True, 'text', '!=', 'active')]
    assert RowFilterMatch(row, titlesList, rowFilter, True, [], True) is True

  def test_text_greater(self):
    from gam.util.csv_pf import RowFilterMatch
    row = {'status': 'b'}
    titlesList = ['status']
    columnPat = re.compile('^status$', re.IGNORECASE)
    rowFilter = [(columnPat, True, 'text', '>', 'a')]
    assert RowFilterMatch(row, titlesList, rowFilter, True, [], True) is True

  def test_textrange_in_range(self):
    from gam.util.csv_pf import RowFilterMatch
    row = {'status': 'banana'}
    titlesList = ['status']
    columnPat = re.compile('^status$', re.IGNORECASE)
    rowFilter = [(columnPat, True, 'textrange', '=', 'apple', 'cherry')]
    assert RowFilterMatch(row, titlesList, rowFilter, True, [], True) is True

  def test_textrange_out_of_range(self):
    from gam.util.csv_pf import RowFilterMatch
    row = {'status': 'zebra'}
    titlesList = ['status']
    columnPat = re.compile('^status$', re.IGNORECASE)
    rowFilter = [(columnPat, True, 'textrange', '=', 'apple', 'cherry')]
    assert RowFilterMatch(row, titlesList, rowFilter, True, [], True) is False


class TestRowFilterMatchData:
  """Test data and notdata filter types."""

  def test_data_match(self):
    from gam.util.csv_pf import RowFilterMatch
    row = {'role': 'admin'}
    titlesList = ['role']
    columnPat = re.compile('^role$', re.IGNORECASE)
    rowFilter = [(columnPat, True, 'data', {'admin', 'owner', 'editor'})]
    assert RowFilterMatch(row, titlesList, rowFilter, True, [], True) is True

  def test_data_no_match(self):
    from gam.util.csv_pf import RowFilterMatch
    row = {'role': 'viewer'}
    titlesList = ['role']
    columnPat = re.compile('^role$', re.IGNORECASE)
    rowFilter = [(columnPat, True, 'data', {'admin', 'owner', 'editor'})]
    assert RowFilterMatch(row, titlesList, rowFilter, True, [], True) is False

  def test_notdata_match(self):
    from gam.util.csv_pf import RowFilterMatch
    row = {'role': 'viewer'}
    titlesList = ['role']
    columnPat = re.compile('^role$', re.IGNORECASE)
    rowFilter = [(columnPat, True, 'notdata', {'admin', 'owner', 'editor'})]
    assert RowFilterMatch(row, titlesList, rowFilter, True, [], True) is True

  def test_notdata_no_match(self):
    from gam.util.csv_pf import RowFilterMatch
    row = {'role': 'admin'}
    titlesList = ['role']
    columnPat = re.compile('^role$', re.IGNORECASE)
    rowFilter = [(columnPat, True, 'notdata', {'admin', 'owner', 'editor'})]
    assert RowFilterMatch(row, titlesList, rowFilter, True, [], True) is False


class TestRowFilterMatchDate:
  """Test date and time filter types."""

  def test_date_greater(self):
    from gam.util.csv_pf import RowFilterMatch
    from gamlib import settings as GC
    GC.Values[GC.NEVER_TIME] = 'Never'
    row = {'created': '2025-06-15T10:30:00Z'}
    titlesList = ['created']
    columnPat = re.compile('^created$', re.IGNORECASE)
    rowFilter = [(columnPat, True, 'date', '>', '2025-01-01T00:00:00.000Z')]
    assert RowFilterMatch(row, titlesList, rowFilter, True, [], True) is True

  def test_date_less(self):
    from gam.util.csv_pf import RowFilterMatch
    from gamlib import settings as GC
    GC.Values[GC.NEVER_TIME] = 'Never'
    row = {'created': '2024-06-15T10:30:00Z'}
    titlesList = ['created']
    columnPat = re.compile('^created$', re.IGNORECASE)
    rowFilter = [(columnPat, True, 'date', '<', '2025-01-01T00:00:00.000Z')]
    assert RowFilterMatch(row, titlesList, rowFilter, True, [], True) is True

  def test_time_greater(self):
    from gam.util.csv_pf import RowFilterMatch
    from gamlib import settings as GC
    GC.Values[GC.NEVER_TIME] = 'Never'
    row = {'modified': '2025-06-15T10:30:00.000Z'}
    titlesList = ['modified']
    columnPat = re.compile('^modified$', re.IGNORECASE)
    rowFilter = [(columnPat, True, 'time', '>', '2025-01-01T00:00:00.000Z')]
    assert RowFilterMatch(row, titlesList, rowFilter, True, [], True) is True

  def test_date_empty_no_match(self):
    from gam.util.csv_pf import RowFilterMatch
    from gamlib import settings as GC
    GC.Values[GC.NEVER_TIME] = 'Never'
    row = {'created': ''}
    titlesList = ['created']
    columnPat = re.compile('^created$', re.IGNORECASE)
    rowFilter = [(columnPat, True, 'date', '>', '2025-01-01T00:00:00.000Z')]
    assert RowFilterMatch(row, titlesList, rowFilter, True, [], True) is False

  def test_date_non_string_no_match(self):
    from gam.util.csv_pf import RowFilterMatch
    from gamlib import settings as GC
    GC.Values[GC.NEVER_TIME] = 'Never'
    row = {'created': None}
    titlesList = ['created']
    columnPat = re.compile('^created$', re.IGNORECASE)
    rowFilter = [(columnPat, True, 'date', '>', '2025-01-01T00:00:00.000Z')]
    assert RowFilterMatch(row, titlesList, rowFilter, True, [], True) is False


class TestRowFilterMatchModes:
  """Test rowFilter mode combinations (Any vs All) and drop filters."""

  def test_no_filters_returns_true(self):
    from gam.util.csv_pf import RowFilterMatch
    row = {'name': 'anything'}
    assert RowFilterMatch(row, ['name'], [], True, [], True) is True

  def test_row_filter_mode_any(self):
    """Any mode: at least one filter must match to select."""
    from gam.util.csv_pf import RowFilterMatch
    row = {'a': 'yes', 'b': 'no'}
    titlesList = ['a', 'b']
    f1 = (re.compile('^a$', re.IGNORECASE), True, 'regex', re.compile('yes', re.IGNORECASE))
    f2 = (re.compile('^b$', re.IGNORECASE), True, 'regex', re.compile('yes', re.IGNORECASE))
    # f1 matches, f2 doesn't — Any mode should select
    assert RowFilterMatch(row, titlesList, [f1, f2], False, [], True) is True

  def test_row_filter_mode_all(self):
    """All mode: all filters must match to select."""
    from gam.util.csv_pf import RowFilterMatch
    row = {'a': 'yes', 'b': 'no'}
    titlesList = ['a', 'b']
    f1 = (re.compile('^a$', re.IGNORECASE), True, 'regex', re.compile('yes', re.IGNORECASE))
    f2 = (re.compile('^b$', re.IGNORECASE), True, 'regex', re.compile('yes', re.IGNORECASE))
    # f1 matches, f2 doesn't — All mode should NOT select
    assert RowFilterMatch(row, titlesList, [f1, f2], True, [], True) is False

  def test_drop_filter_any(self):
    """Drop filter in Any mode: any match drops the row."""
    from gam.util.csv_pf import RowFilterMatch
    row = {'status': 'deleted'}
    titlesList = ['status']
    dropFilter = [(re.compile('^status$', re.IGNORECASE), True, 'regex', re.compile('deleted', re.IGNORECASE))]
    assert RowFilterMatch(row, titlesList, [], True, dropFilter, False) is False

  def test_drop_filter_no_match_keeps(self):
    """Drop filter that doesn't match should keep the row."""
    from gam.util.csv_pf import RowFilterMatch
    row = {'status': 'active'}
    titlesList = ['status']
    dropFilter = [(re.compile('^status$', re.IGNORECASE), True, 'regex', re.compile('deleted', re.IGNORECASE))]
    assert RowFilterMatch(row, titlesList, [], True, dropFilter, False) is True

  def test_row_and_drop_filter_combined(self):
    """Row selected by rowFilter but dropped by dropFilter."""
    from gam.util.csv_pf import RowFilterMatch
    row = {'name': 'John', 'status': 'deleted'}
    titlesList = ['name', 'status']
    rowFilter = [(re.compile('^name$', re.IGNORECASE), True, 'regex', re.compile('John', re.IGNORECASE))]
    dropFilter = [(re.compile('^status$', re.IGNORECASE), True, 'regex', re.compile('deleted', re.IGNORECASE))]
    assert RowFilterMatch(row, titlesList, rowFilter, True, dropFilter, False) is False

  def test_column_not_in_titles(self):
    """Filter column not in titles should use [None] as columns."""
    from gam.util.csv_pf import RowFilterMatch
    row = {'name': 'John'}
    titlesList = ['name']
    # Filter on 'missing_col' which isn't in titlesList
    rowFilter = [(re.compile('^missing_col$', re.IGNORECASE), True, 'regex', re.compile('John', re.IGNORECASE))]
    # No columns match, so row.get(None, '') = '', regex doesn't match
    assert RowFilterMatch(row, titlesList, rowFilter, True, [], True) is False

  def test_any_match_across_columns(self):
    """anyMatch=True across multiple columns: any column matching suffices."""
    from gam.util.csv_pf import RowFilterMatch
    row = {'col1': 'no', 'col2': 'yes'}
    titlesList = ['col1', 'col2']
    # Match any column starting with 'col'
    columnPat = re.compile('^col', re.IGNORECASE)
    rowFilter = [(columnPat, True, 'regex', re.compile('yes', re.IGNORECASE))]
    assert RowFilterMatch(row, titlesList, rowFilter, True, [], True) is True

  def test_all_match_across_columns(self):
    """anyMatch=False (all mode) across columns: ALL columns must match."""
    from gam.util.csv_pf import RowFilterMatch
    row = {'col1': 'yes', 'col2': 'no'}
    titlesList = ['col1', 'col2']
    columnPat = re.compile('^col', re.IGNORECASE)
    rowFilter = [(columnPat, False, 'regex', re.compile('yes', re.IGNORECASE))]
    # col2 doesn't match — all mode fails
    assert RowFilterMatch(row, titlesList, rowFilter, True, [], True) is False


# ---------------------------------------------------------------------------
# CSVPrintFile title management tests
# ---------------------------------------------------------------------------

class TestCSVPrintFileTitles:
  """Test CSVPrintFile title management methods."""

  def test_add_title(self):
    from gam.util.csv_pf import CSVPrintFile
    pf = CSVPrintFile()
    pf.AddTitle('email')
    assert 'email' in pf.titlesList
    assert 'email' in pf.titlesSet

  def test_add_titles_no_duplicate(self):
    from gam.util.csv_pf import CSVPrintFile
    pf = CSVPrintFile()
    pf.AddTitles(['email'])
    pf.AddTitles(['email'])
    assert pf.titlesList.count('email') == 1

  def test_add_titles(self):
    from gam.util.csv_pf import CSVPrintFile
    pf = CSVPrintFile()
    pf.AddTitles(['email', 'name', 'role'])
    assert pf.titlesList == ['email', 'name', 'role']

  def test_remove_titles(self):
    from gam.util.csv_pf import CSVPrintFile
    pf = CSVPrintFile()
    pf.AddTitles(['email', 'name', 'role'])
    pf.RemoveTitles(['name'])
    assert 'name' not in pf.titlesList
    assert 'name' not in pf.titlesSet

  def test_set_titles(self):
    from gam.util.csv_pf import CSVPrintFile
    pf = CSVPrintFile()
    pf.AddTitles(['a', 'b', 'c'])
    pf.SetTitles(['x', 'y'])
    assert pf.titlesList == ['x', 'y']
    assert pf.titlesSet == {'x', 'y'}

  def test_insert_titles(self):
    from gam.util.csv_pf import CSVPrintFile
    pf = CSVPrintFile()
    pf.AddTitles(['b', 'c'])
    pf.InsertTitles(0, ['a'])
    assert pf.titlesList[0] == 'a'

  def test_move_titles_to_end(self):
    from gam.util.csv_pf import CSVPrintFile
    pf = CSVPrintFile()
    pf.AddTitles(['a', 'b', 'c'])
    pf.MoveTitlesToEnd(['a'])
    assert pf.titlesList == ['b', 'c', 'a']

  def test_add_sort_title(self):
    from gam.util.csv_pf import CSVPrintFile
    pf = CSVPrintFile()
    pf.AddSortTitle('email')
    assert 'email' in pf.sortTitlesList

  def test_add_sort_titles(self):
    from gam.util.csv_pf import CSVPrintFile
    pf = CSVPrintFile()
    pf.AddSortTitles(['email', 'name'])
    assert pf.sortTitlesList == ['email', 'name']


class TestCSVPrintFileRows:
  """Test CSVPrintFile row management."""

  def test_write_row_no_filter(self):
    from gam.util.csv_pf import CSVPrintFile
    pf = CSVPrintFile()
    pf.AddTitles(['name', 'email'])
    pf.WriteRowNoFilter({'name': 'John', 'email': 'john@example.com'})
    assert len(pf.rows) == 1
    assert pf.rows[0]['name'] == 'John'

  def test_append_row(self):
    from gam.util.csv_pf import CSVPrintFile
    pf = CSVPrintFile()
    pf.AddTitles(['name'])
    pf.AppendRow({'name': 'test'})
    assert len(pf.rows) == 1

  def test_header_filter_match_no_filter(self):
    from gam.util.csv_pf import CSVPrintFile
    pf = CSVPrintFile()
    # No filter = match all
    assert pf.headerFilter == []
    assert pf.headerDropFilter == []

  def test_header_filter_set(self):
    from gam.util.csv_pf import CSVPrintFile
    pf = CSVPrintFile()
    pattern = [(re.compile('^email$', re.IGNORECASE), True)]
    pf.SetHeaderFilter(pattern)
    assert pf.headerFilter == pattern


class TestCSVPrintFileMapTitles:
  """Test MapTitles method."""

  def test_map_titles_basic(self):
    from gam.util.csv_pf import CSVPrintFile
    pf = CSVPrintFile()
    pf.AddTitles(['old_name', 'old_email'])
    pf.MapTitles('old_name', 'name')
    pf.MapTitles('old_email', 'email')
    assert pf.titlesList == ['name', 'email']
    assert 'name' in pf.titlesSet
    assert 'old_name' not in pf.titlesSet
