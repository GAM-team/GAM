import pytest
from gam.util.config import (
    _stringInQuotes,
    _stripStringQuotes,
    _quoteStringIfLeadingTrailingBlanks,
)

class TestStringQuoteUtils:
    def test_string_in_quotes_single(self):
        """Should detect strings in single quotes."""
        assert _stringInQuotes("'hello'") == True
        
    def test_string_in_quotes_double(self):
        """Should detect strings in double quotes."""
        assert _stringInQuotes('"hello"') == True

    def test_string_not_in_quotes(self):
        """Should not detect strings missing quotes."""
        assert _stringInQuotes("hello") == False
        assert _stringInQuotes("'hello") == False
        assert _stringInQuotes('hello"') == False
        
    def test_strip_string_quotes_single(self):
        """Should strip single quotes."""
        assert _stripStringQuotes("'hello'") == "hello"
        
    def test_strip_string_quotes_double(self):
        """Should strip double quotes."""
        assert _stripStringQuotes('"hello"') == "hello"

    def test_strip_string_quotes_none(self):
        """Should return unchanged if no quotes."""
        assert _stripStringQuotes("hello") == "hello"
        
    def test_quote_string_leading_trailing_blanks_leading(self):
        """Should quote string with leading blanks."""
        assert _quoteStringIfLeadingTrailingBlanks(" hello") == "' hello'"

    def test_quote_string_leading_trailing_blanks_trailing(self):
        """Should quote string with trailing blanks."""
        assert _quoteStringIfLeadingTrailingBlanks("hello ") == "'hello '"

    def test_quote_string_leading_trailing_blanks_both(self):
        """Should quote string with both leading and trailing blanks."""
        assert _quoteStringIfLeadingTrailingBlanks(" hello ") == "' hello '"

    def test_quote_string_leading_trailing_blanks_none(self):
        """Should not quote string with no leading/trailing blanks."""
        assert _quoteStringIfLeadingTrailingBlanks("hello") == "hello"
        
    def test_quote_string_leading_trailing_blanks_already_quoted(self):
        """Should not add quotes if already quoted."""
        assert _quoteStringIfLeadingTrailingBlanks('" hello "') == '" hello "'
        assert _quoteStringIfLeadingTrailingBlanks("' hello '") == "' hello '"
