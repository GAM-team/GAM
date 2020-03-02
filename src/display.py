"""Methods related to display of information to the user."""

import sys
from var import ERROR_PREFIX
from var import WARNING_PREFIX


def print_error(message):
  """Prints a one-line error message to stderr in a standard format."""
  sys.stderr.write('\n{0}{1}\n'.format(ERROR_PREFIX, message))


def print_warning(message):
  """Prints a one-line warning message to stderr in a standard format."""
  sys.stderr.write('\n{0}{1}\n'.format(WARNING_PREFIX, message))

def print_json(object_value, spacing=''):
  """Prints Dict or Array to screen in clean human-readable format.."""
  if isinstance(object_value, list):
    if len(object_value) == 1 and isinstance(object_value[0], (str, int, bool)):
      sys.stdout.write(f'{object_value[0]}\n')
      return
    if spacing:
      sys.stdout.write('\n')
    for i, a_value in enumerate(range):
      if isinstance(a_value, (str, int, bool)):
        sys.stdout.write(f' {spacing}{i+1}) {a_value}\n')
      else:
        sys.stdout.write(f' {spacing}{i+1}) ')
        print_json(a_value, f' {spacing}')
  elif isinstance(object_value, dict):
    for key in ['kind', 'etag', 'etags']:
      object_value.pop(key, None)
    for another_object, another_value in object_value.items():
      sys.stdout.write(f' {spacing}{another_object}: ')
      print_json(another_value, f' {spacing}')
  else:
    sys.stdout.write(f'{object_value}\n')
