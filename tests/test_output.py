"""Unit tests for gam.util.output — output formatting and utility functions."""

import pytest


class TestStripControlChars:
    """Test control character stripping."""

    def test_strips_null(self):
        from gam.util.output import _stripControlCharsFromName
        assert _stripControlCharsFromName('hello\x00world') == 'helloworld'

    def test_strips_cr(self):
        from gam.util.output import _stripControlCharsFromName
        assert _stripControlCharsFromName('hello\rworld') == 'helloworld'

    def test_strips_nl(self):
        from gam.util.output import _stripControlCharsFromName
        assert _stripControlCharsFromName('hello\nworld') == 'helloworld'

    def test_strips_multiple(self):
        from gam.util.output import _stripControlCharsFromName
        assert _stripControlCharsFromName('\x00he\rll\no') == 'hello'

    def test_clean_string_unchanged(self):
        from gam.util.output import _stripControlCharsFromName
        assert _stripControlCharsFromName('hello world') == 'hello world'

    def test_empty_string(self):
        from gam.util.output import _stripControlCharsFromName
        assert _stripControlCharsFromName('') == ''


class TestCurrentCount:
    """Test count display formatting."""

    def test_current_count_with_items(self):
        from gam.util.output import currentCount
        result = currentCount(3, 10)
        assert result == ' (3/10)'

    def test_current_count_nl(self):
        from gam.util.output import currentCountNL
        result = currentCountNL(3, 10)
        assert result == ' (3/10)\n'


class TestFormatKeyValueList:
    """Test key-value list formatting.

    formatKeyValueList processes pairs: [key1, val1, key2, val2, ...]
    Each key gets ': ' and its value appended.
    """

    def test_single_pair(self):
        from gam.util.output import formatKeyValueList
        result = formatKeyValueList('', ['Name', 'Alice'], '')
        assert result == 'Name: Alice'

    def test_multiple_pairs(self):
        from gam.util.output import formatKeyValueList
        result = formatKeyValueList('', ['Name', 'Alice', 'Age', 30], '')
        assert 'Name: Alice' in result
        assert 'Age: 30' in result

    def test_with_prefix_suffix(self):
        from gam.util.output import formatKeyValueList
        result = formatKeyValueList('  ', ['key', 'val'], '\n')
        assert result == '  key: val\n'

    def test_none_value(self):
        from gam.util.output import formatKeyValueList
        result = formatKeyValueList('', ['key', None], '')
        assert result == 'key:'

    def test_empty_list(self):
        from gam.util.output import formatKeyValueList
        result = formatKeyValueList('pre', [], 'suf')
        assert result == 'presuf'


class TestColoredText:
    """Test colored text creation."""

    def test_create_colored_text_returns_string(self):
        from gam.util.output import createColoredText
        result = createColoredText('hello', 'red')
        assert isinstance(result, str)
        assert 'hello' in result

    def test_create_red_text(self):
        from gam.util.output import createRedText
        result = createRedText('error')
        assert 'error' in result

    def test_create_green_text(self):
        from gam.util.output import createGreenText
        result = createGreenText('success')
        assert 'success' in result
