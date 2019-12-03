"""Methods related to display of information to the user."""

import sys
import utils
from var import ERROR_PREFIX
from var import WARNING_PREFIX


def print_error(message):
  """Prints a one-line error message to stderr in a standard format."""
  sys.stderr.write(
      utils.convertUTF8('\n{0}{1}\n'.format(ERROR_PREFIX, message)))


def print_warning(message):
  """Prints a one-line warning message to stderr in a standard format."""
  sys.stderr.write(
      utils.convertUTF8('\n{0}{1}\n'.format(WARNING_PREFIX, message)))
