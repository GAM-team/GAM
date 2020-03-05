"""Common file operations."""

import io
import os
import sys

import controlflow
import display
from var import GM_Globals
from var import GM_SYS_ENCODING
from var import UTF8_SIG


def _open_file(filename, mode, encoding=None, newline=None):
  """Opens a file with no error handling."""
  # Determine which encoding to use
  if 'b' in mode:
    encoding = None
  elif not encoding:
    encoding = GM_Globals[GM_SYS_ENCODING]
  elif 'r' in mode and encoding.lower().replace('-', '') == 'utf8':
    encoding = UTF8_SIG

  return open(
      os.path.expanduser(filename), mode, newline=newline, encoding=encoding)


def open_file(filename,
              mode='r',
              encoding=None,
              newline=None,
              strip_utf_bom=False):
  """Opens a file.

  Args:
    filename: String, the name of the file to open, or '-' to use stdin/stdout,
      to read/write, depending on the mode param, respectively.
    mode: String, the common file mode to open the file with. Default is read.
    encoding: String, the name of the encoding used to decode or encode the
      file. This should only be used in text mode.
    newline: See param description in
        https://docs.python.org/3.7/library/functions.html#open
    strip_utf_bom: Boolean, True if the file being opened should seek past the
      UTF Byte Order Mark before being returned.
        See more: https://en.wikipedia.org/wiki/UTF-8#Byte_order_mark

  Returns:
    The opened file.
  """
  try:
    if filename == '-':
      # Read from stdin, rather than a file
      if 'r' in mode:
        return io.StringIO(str(sys.stdin.read()))
      return sys.stdout

    # Open a file on disk
    f = _open_file(filename, mode, newline=newline, encoding=encoding)
    if strip_utf_bom:
      utf_bom = u'\ufeff'
      has_bom = False

      if 'b' in mode:
        has_bom = f.read(3).decode('UTF-8') == utf_bom
      elif f.encoding and not f.encoding.lower().startswith('utf'):
        # Convert UTF BOM into ISO-8859-1 via Bytes
        utf8_bom_bytes = utf_bom.encode('UTF-8')
        iso_8859_1_bom = utf8_bom_bytes.decode('iso-8859-1').encode(
            'iso-8859-1')
        has_bom = f.read(3).encode('iso-8859-1', 'replace') == iso_8859_1_bom
      else:
        has_bom = f.read(1) == utf_bom

      if not has_bom:
        f.seek(0)

    return f

  except IOError as e:
    controlflow.system_error_exit(6, e)


def close_file(f, force_flush=False):
  """Closes a file.

  Args:
    f: The file to close
    force_flush: Flush file to disk emptying Python and OS caches. See:
       https://stackoverflow.com/a/13762137/1503886

  Returns:
    Boolean, True if the file was successfully closed. False if an error
        was encountered while closing.
  """
  if force_flush:
    f.flush()
    os.fsync(f.fileno())
  try:
    f.close()
    return True
  except IOError as e:
    display.print_error(e)
    return False


def read_file(filename,
              mode='r',
              encoding=None,
              newline=None,
              continue_on_error=False,
              display_errors=True):
  """Reads a file from disk.

  Args:
    filename: String, the path of the file to open from disk, or "-" to read
      from stdin.
    mode: String, the mode in which to open the file.
    encoding: String, the name of the encoding used to decode or encode the
      file. This should only be used in text mode.
    newline: See param description in
        https://docs.python.org/3.7/library/functions.html#open
    continue_on_error: Boolean, If True, suppresses any IO errors and returns to
      the caller without any externalities.
    display_errors: Boolean, If True, prints error messages when errors are
      encountered and continue_on_error is True.

  Returns:
    The contents of the file, or stdin if filename == "-". Returns None if
    an error is encountered and continue_on_errors is True.
  """
  try:
    if filename == '-':
      # Read from stdin, rather than a file.
      return str(sys.stdin.read())

    with _open_file(filename, mode, newline=newline, encoding=encoding) as f:
      return f.read()

  except IOError as e:
    if continue_on_error:
      if display_errors:
        display.print_warning(e)
      return None
    controlflow.system_error_exit(6, e)
  except (LookupError, UnicodeDecodeError, UnicodeError) as e:
    controlflow.system_error_exit(2, str(e))


def write_file(filename,
               data,
               mode='w',
               continue_on_error=False,
               display_errors=True):
  """Writes data to a file.

  Args:
    filename: String, the path of the file to write to disk.
    data: Serializable data to write to the file.
    mode: String, the mode in which to open the file and write to it.
    continue_on_error: Boolean, If True, suppresses any IO errors and returns to
      the caller without any externalities.
    display_errors: Boolean, If True, prints error messages when errors are
      encountered and continue_on_error is True.

  Returns:
    Boolean, True if the write operation succeeded, or False if not.
  """
  try:
    with _open_file(filename, mode) as f:
      f.write(data)
    return True

  except IOError as e:
    if continue_on_error:
      if display_errors:
        display.print_error(e)
      return False
    else:
      controlflow.system_error_exit(6, e)
