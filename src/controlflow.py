"""Methods related to the central control flow of an application."""
import random
import sys
import time

import display  # TODO: Change to relative import when gam is setup as a package
from var import MESSAGE_HEADER_NOT_FOUND_IN_CSV_HEADERS
from var import MESSAGE_INVALID_JSON


def system_error_exit(return_code, message):
  """Raises a system exit with the given return code and message.

  Args:
    return_code: Int, the return code to yield when the system exits.
    message: An error message to print before the system exits.
  """
  if message:
    display.print_error(message)
  sys.exit(return_code)


def invalid_argument_exit(argument, command):
  '''Indicate that the argument is not valid for the command.

  Args:
    argument: the invalid argument
    command: the base GAM command
  '''
  system_error_exit(
      2,
      f'{argument} is not a valid argument for "{command}"')

def missing_argument_exit(argument, command):
  '''Indicate that the argument is missing for the command.

  Args:
    argument: the missingagrument
    command: the base GAM command
  '''
  system_error_exit(
      2,
      f'missing argument {argument} for "{command}"')

def expected_argument_exit(name, expected, argument):
  '''Indicate that the argument does not have an expected value for the command.

  Args:
    name: the field name
    expected: the expected values
    argument: the invalid argument
  '''
  system_error_exit(
      2,
      f'{name} must be one of {expected}; got {argument}')

def csv_field_error_exit(field_name, field_names):
  """Raises a system exit when a CSV field is malformed.

  Args:
    field_name: The CSV field name for which a header does not exist in the
      existing CSV headers.
    field_names: The known list of CSV headers.
  """
  system_error_exit(
      2,
      MESSAGE_HEADER_NOT_FOUND_IN_CSV_HEADERS.format(field_name,
                                                     ','.join(field_names)))


def invalid_json_exit(file_name):
  """Raises a sysyem exit when invalid JSON content is encountered."""
  system_error_exit(17, MESSAGE_INVALID_JSON.format(file_name))


def wait_on_failure(current_attempt_num,
                    total_num_retries,
                    error_message,
                    error_print_threshold=3):
  """Executes an exponential backoff-style system sleep.

  Args:
    current_attempt_num: Int, the current number of retries.
    total_num_retries: Int, the total number of times the current action will be
      retried.
    error_message: String, a message to be displayed that will give more context
      around why the action is being retried.
    error_print_threshold: Int, the number of attempts which will have their
      error messages suppressed. Any current_attempt_num greater than
      error_print_threshold will print the prescribed error.
  """
  wait_on_fail = min(2**current_attempt_num,
                     60) + float(random.randint(1, 1000)) / 1000
  if current_attempt_num > error_print_threshold:
    sys.stderr.write((f'Temporary error: {error_message}, Backing off: '
        f'{int(wait_on_fail)} seconds, Retry: '
        f'{current_attempt_num}/{total_num_retries}\n'))
    sys.stderr.flush()
  time.sleep(wait_on_fail)
