"""GAM output helpers — write/flush/print/format functions.

These are pure output functions that write to stdout/stderr via GM.Globals.
No circular dependency risk — they only depend on gamlib modules and
simple string constants.
"""

import re
import sys
import time

import arrow

from gamlib import settings as GC
from gamlib import state as GM
from gamlib import msgs as Msg
from gam.constants import DEBUG_REDACTION_PATTERNS
from gam.var import Ind


# These constants are duplicated from __init__.py to avoid circular imports.
# They are simple string literals that never change.
ERROR = 'ERROR'
ERROR_PREFIX = ERROR + ': '
WARNING = 'WARNING'
WARNING_PREFIX = WARNING + ': '
STDOUT_STDERR_ERROR_RC = 66


# stdin/stdout/stderr
def readStdin(prompt):
  return input(prompt)

def stdErrorExit(e):
  try:
    sys.stderr.write(f'\n{ERROR_PREFIX}{str(e)}\n')
  except IOError:
    pass
  sys.exit(STDOUT_STDERR_ERROR_RC)

def writeStdout(data):
  try:
    GM.Globals[GM.STDOUT].get(GM.REDIRECT_MULTI_FD, sys.stdout).write(data)
  except IOError as e:
    stdErrorExit(e)

def flushStdout():
  try:
    GM.Globals[GM.STDOUT].get(GM.REDIRECT_MULTI_FD, sys.stdout).flush()
  except IOError as e:
    stdErrorExit(e)

def writeStderr(data):
  flushStdout()
  try:
    GM.Globals[GM.STDERR].get(GM.REDIRECT_MULTI_FD, sys.stderr).write(data)
  except IOError as e:
    stdErrorExit(e)

def flushStderr():
  try:
    GM.Globals[GM.STDERR].get(GM.REDIRECT_MULTI_FD, sys.stderr).flush()
  except IOError as e:
    stdErrorExit(e)

# Error messages
def setSysExitRC(sysRC):
  GM.Globals[GM.SYSEXITRC] = sysRC

def stderrErrorMsg(message):
  writeStderr(f'\n{ERROR_PREFIX}{message}\n')

def stderrWarningMsg(message):
  writeStderr(f'\n{WARNING_PREFIX}{message}\n')

def systemErrorExit(sysRC, message):
  if message:
    stderrErrorMsg(message)
  sys.exit(sysRC)

def printErrorMessage(sysRC, message):
  setSysExitRC(sysRC)
  writeStderr(f'\n{Ind.Spaces()}{ERROR_PREFIX}{message}\n')

def printWarningMessage(sysRC, message):
  setSysExitRC(sysRC)
  writeStderr(f'\n{Ind.Spaces()}{WARNING_PREFIX}{message}\n')

def supportsColoredText():
  """Determines if the current terminal environment supports colored text.

  Returns:
    Bool, True if the current terminal environment supports colored text via
    ANSI escape characters.
  """
  # Make a rudimentary check for Windows. Though Windows does seem to support
  # colorization with VT100 emulation, it is disabled by default. Therefore,
  # we'll simply disable it in GAM on Windows for now.
  return not sys.platform.startswith('win')

def createColoredText(text, color):
  """Uses ANSI escape characters to create colored text in supported terminals.

  See more at https://en.wikipedia.org/wiki/ANSI_escape_code#Colors

  Args:
    text: String, The text to colorize using ANSI escape characters.
    color: String, An ANSI escape sequence denoting the color of the text to be
      created. See more at https://en.wikipedia.org/wiki/ANSI_escape_code#Colors

  Returns:
    The input text with appropriate ANSI escape characters to create
    colorization in a supported terminal environment.
  """
  END_COLOR_SEQUENCE = '\033[0m'  # Ends the applied color formatting
  if supportsColoredText():
    return color + text + END_COLOR_SEQUENCE
  return text  # Hand back the plain text, uncolorized.

def createRedText(text):
  """Uses ANSI encoding to create red colored text if supported."""
  return createColoredText(text, '\033[91m')

def createGreenText(text):
  """Uses ANSI encoding to create green colored text if supported."""
  return createColoredText(text, '\u001b[32m')

def createYellowText(text):
  """Uses ANSI encoding to create yellow text if supported."""
  return createColoredText(text, '\u001b[33m')

def executeBatch(dbatch):
  dbatch.execute()
  if GC.Values[GC.INTER_BATCH_WAIT] > 0:
    time.sleep(GC.Values[GC.INTER_BATCH_WAIT])

def _stripControlCharsFromName(name):
  for cc in ['\x00', '\r', '\n']:
    name = name.replace(cc, '')
  return name

def currentCount(i, count):
  return f' ({i}/{count})' if (count > GC.Values[GC.SHOW_COUNTS_MIN]) else ''

def currentCountNL(i, count):
  return f' ({i}/{count})\n' if (count > GC.Values[GC.SHOW_COUNTS_MIN]) else '\n'

# Format a key value list
#   key, value	-> "key: value" + ", " if not last item
#   key, ''	-> "key:" + ", " if not last item
#   key, None	-> "key" + " " if not last item
def formatKeyValueList(prefixStr, kvList, suffixStr):
  msg = prefixStr
  i = 0
  l = len(kvList)
  while i < l:
    if isinstance(kvList[i], (bool, float, int)):
      msg += str(kvList[i])
    else:
      msg += kvList[i]
    i += 1
    if i < l:
      val = kvList[i]
      if (val is not None) or (i == l-1):
        msg += ':'
        if (val is not None) and (not isinstance(val, str) or val):
          msg += ' '
          if isinstance(val, (bool, float, int)):
            msg += str(val)
          else:
            msg += val
        i += 1
        if i < l:
          msg += ', '
      else:
        i += 1
        if i < l:
          msg += ' '
  msg += suffixStr
  return msg

def redactable_debug_print(*args):
  processed_args = []
  for arg in args:
    if arg.startswith('b\''):
      sbytes = arg[2:-1]
      sbytes = bytes(sbytes, 'utf-8')
      arg = sbytes.decode()
      arg = arg.replace('\\r\\n', "\n          ")
    if GC.Values[GC.DEBUG_REDACTION]:
      for pattern, replace in DEBUG_REDACTION_PATTERNS:
        arg = re.sub(pattern, replace, arg)
    processed_args.append(arg)
  print(*processed_args)

def showAPICallsRetryData():
  if GC.Values.get(GC.SHOW_API_CALLS_RETRY_DATA) and GM.Globals[GM.API_CALLS_RETRY_DATA]:
    Ind.Reset()
    writeStderr(Msg.API_CALLS_RETRY_DATA)
    Ind.Increment()
    for k, v in sorted(GM.Globals[GM.API_CALLS_RETRY_DATA].items()):
      m, s = divmod(int(v[1]), 60)
      h, m = divmod(m, 60)
      writeStderr(formatKeyValueList(Ind.Spaces(), [k, f'{v[0]}/{h}:{m:02d}:{s:02d}'], '\n'))
    Ind.Decrement()

# Timestamp functions (moved from args.py to break fileio↔args cycle)
def ISOformatTimeStamp(timestamp):
  return timestamp.isoformat('T', 'seconds')


def currentISOformatTimeStamp(timespec='milliseconds'):
  return arrow.now(GC.Values[GC.TIMEZONE]).isoformat('T', timespec)


