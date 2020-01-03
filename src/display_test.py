"""Tests for display."""

import unittest
from unittest.mock import patch

import display
from var import ERROR_PREFIX
from var import WARNING_PREFIX


class DisplayTest(unittest.TestCase):

  def test_print_error_prints_to_stderr(self):
    message = 'test error'
    with patch.object(display.sys.stderr, 'write') as mock_write:
      display.print_error(message)
    printed_message = mock_write.call_args[0][0]
    self.assertIn(message, printed_message)

  def test_print_error_prints_error_prefix(self):
    message = 'test error'
    with patch.object(display.sys.stderr, 'write') as mock_write:
      display.print_error(message)
    printed_message = mock_write.call_args[0][0]
    self.assertLess(
        printed_message.find(ERROR_PREFIX), printed_message.find(message),
        'The error prefix does not appear before the error message')

  def test_print_error_ends_message_with_newline(self):
    message = 'test error'
    with patch.object(display.sys.stderr, 'write') as mock_write:
      display.print_error(message)
    printed_message = mock_write.call_args[0][0]
    self.assertRegex(printed_message, '\n$',
                     'The error message does not end in a newline.')

  def test_print_warning_prints_to_stderr(self):
    message = 'test warning'
    with patch.object(display.sys.stderr, 'write') as mock_write:
      display.print_error(message)
    printed_message = mock_write.call_args[0][0]
    self.assertIn(message, printed_message)

  def test_print_warning_prints_error_prefix(self):
    message = 'test warning'
    with patch.object(display.sys.stderr, 'write') as mock_write:
      display.print_error(message)
    printed_message = mock_write.call_args[0][0]
    self.assertLess(
        printed_message.find(WARNING_PREFIX), printed_message.find(message),
        'The warning prefix does not appear before the error message')

  def test_print_warning_ends_message_with_newline(self):
    message = 'test warning'
    with patch.object(display.sys.stderr, 'write') as mock_write:
      display.print_error(message)
    printed_message = mock_write.call_args[0][0]
    self.assertRegex(printed_message, '\n$',
                     'The warning message does not end in a newline.')
