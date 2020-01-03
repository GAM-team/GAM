"""Tests for controlflow."""

import unittest
from unittest.mock import patch

import controlflow


class ControlFlowTest(unittest.TestCase):

  def test_system_error_exit_raises_systemexit_error(self):
    with self.assertRaises(SystemExit):
      controlflow.system_error_exit(1, 'exit message')

  def test_system_error_exit_raises_systemexit_with_return_code(self):
    with self.assertRaises(SystemExit) as context_manager:
      controlflow.system_error_exit(100, 'exit message')
    self.assertEqual(context_manager.exception.code, 100)

  @patch.object(controlflow.display, 'print_error')
  def test_system_error_exit_prints_error_before_exiting(self, mock_print_err):
    with self.assertRaises(SystemExit):
      controlflow.system_error_exit(100, 'exit message')
    self.assertIn('exit message', mock_print_err.call_args[0][0])

  def test_csv_field_error_exit_raises_systemexit_error(self):
    with self.assertRaises(SystemExit):
      controlflow.csv_field_error_exit('aField',
                                       ['unusedField1', 'unusedField2'])

  def test_csv_field_error_exit_exits_code_2(self):
    with self.assertRaises(SystemExit) as context_manager:
      controlflow.csv_field_error_exit('aField',
                                       ['unusedField1', 'unusedField2'])
    self.assertEqual(context_manager.exception.code, 2)

  @patch.object(controlflow.display, 'print_error')
  def test_csv_field_error_exit_prints_error_details(self, mock_print_err):
    with self.assertRaises(SystemExit):
      controlflow.csv_field_error_exit('aField',
                                       ['unusedField1', 'unusedField2'])
    printed_message = mock_print_err.call_args[0][0]
    self.assertIn('aField', printed_message)
    self.assertIn('unusedField1', printed_message)
    self.assertIn('unusedField2', printed_message)

  def test_invalid_json_exit_raises_systemexit_error(self):
    with self.assertRaises(SystemExit):
      controlflow.invalid_json_exit('filename')

  def test_invalid_json_exit_exit_exits_code_17(self):
    with self.assertRaises(SystemExit) as context_manager:
      controlflow.invalid_json_exit('filename')
    self.assertEqual(context_manager.exception.code, 17)

  @patch.object(controlflow.display, 'print_error')
  def test_invalid_json_exit_prints_error_details(self, mock_print_err):
    with self.assertRaises(SystemExit):
      controlflow.invalid_json_exit('filename')
    printed_message = mock_print_err.call_args[0][0]
    self.assertIn('filename', printed_message)

  @patch.object(controlflow.time, 'sleep')
  def test_wait_on_failure_waits_exponentially(self, mock_sleep):
    controlflow.wait_on_failure(1, 5, 'Backoff attempt #1')
    controlflow.wait_on_failure(2, 5, 'Backoff attempt #2')
    controlflow.wait_on_failure(3, 5, 'Backoff attempt #3')

    sleep_calls = mock_sleep.call_args_list
    self.assertGreaterEqual(sleep_calls[0][0][0], 2**1)
    self.assertGreaterEqual(sleep_calls[1][0][0], 2**2)
    self.assertGreaterEqual(sleep_calls[2][0][0], 2**3)

  @patch.object(controlflow.time, 'sleep')
  def test_wait_on_failure_does_not_exceed_60_secs_wait(self, mock_sleep):
    total_attempts = 20
    for attempt in range(1, total_attempts + 1):
      controlflow.wait_on_failure(
          attempt,
          total_attempts,
          'Attempt #%s' % attempt,
          # Suppress messages while we make a lot of attempts.
          error_print_threshold=total_attempts + 1)
      # Wait time may be between 60 and 61 secs, due to rand addition.
      self.assertLessEqual(mock_sleep.call_args[0][0], 61)

  # Prevent the system from actually sleeping and thus slowing down the test.
  @patch.object(controlflow.time, 'sleep')
  def test_wait_on_failure_prints_errors(self, unused_mock_sleep):
    message = 'An error message to display'
    with patch.object(controlflow.sys.stderr, 'write') as mock_stderr_write:
      controlflow.wait_on_failure(1, 5, message, error_print_threshold=0)
    self.assertIn(message, mock_stderr_write.call_args[0][0])

  @patch.object(controlflow.time, 'sleep')
  def test_wait_on_failure_only_prints_after_threshold(self, unused_mock_sleep):
    total_attempts = 5
    threshold = 3
    with patch.object(controlflow.sys.stderr, 'write') as mock_stderr_write:
      for attempt in range(1, total_attempts + 1):
        controlflow.wait_on_failure(
            attempt,
            total_attempts,
            'Attempt #%s' % attempt,
            error_print_threshold=threshold)
    self.assertEqual(total_attempts - threshold, mock_stderr_write.call_count)
