"""GAM file I/O helpers — open/read/write/delete files, file path utilities.

Pure file operations that depend only on gamlib modules and util.output.
"""

import codecs
import io
import logging
import os
import sys
import time
from logging.handlers import RotatingFileHandler

from pathvalidate import sanitize_filename, sanitize_filepath

from gamlib import glcfg as GC
from gamlib import glentity
from gamlib import glglobals as GM
from gamlib import glmsgs as Msg


from gam.var import Act, Ent, Ind
from util.output import (
    stderrErrorMsg,
    stderrWarningMsg,
    setSysExitRC,
    systemErrorExit,
    formatKeyValueList,
    currentCountNL,
    writeStderr,
    flushStderr,
)

# Constants duplicated from __init__.py to avoid circular imports.
UTF8_SIG = 'utf-8-sig'
DEFAULT_FILE_READ_MODE = 'r'
DEFAULT_FILE_WRITE_MODE = 'w'
UNKNOWN = 'Unknown'
FILE_ERROR_RC = 6
ACTION_FAILED_RC = 50
CONFIG_ERROR_RC = 13
WARNING = 'WARNING'
WARNING_PREFIX = WARNING + ': '

# Ent is an instance of GamEntity created in __init__.py.
# For the default parameter value of fileErrorMessage, we use the
# class-level constant directly.
_ENT_FILE = glentity.GamEntity.FILE



def cleanFilename(filename):
  return sanitize_filename(filename, '_')

def setFilePath(filename, cfgDir):
  if filename.startswith('./') or filename.startswith('.\\'):
    return os.path.join(os.getcwd(), filename[2:])
  if filename == '-':
    return filename
  filename = os.path.expanduser(filename)
  if os.path.isabs(filename):
    return filename
  return os.path.join(GC.Values[cfgDir], filename)

def uniqueFilename(targetFolder, filetitle, overwrite, extension=None):
  filename = filetitle
  y = 0
  while True:
    if extension is not None and filename.lower()[-len(extension):] != extension.lower():
      filename += extension
    filepath = os.path.join(targetFolder, filename)
    if overwrite or not os.path.isfile(filepath):
      return (filepath, filename)
    y += 1
    filename = f'({y})-{filetitle}'

def cleanFilepath(filepath):
  return sanitize_filepath(filepath, platform='auto')

def fileErrorMessage(filename, e, entityType=_ENT_FILE):
  return f'{Ent.Singular(entityType)}: {filename}, {str(e)}'


def fdErrorMessage(f, defaultFilename, e):
  return fileErrorMessage(getattr(f, 'name') if hasattr(f, 'name') else defaultFilename, e)

# Set file encoding to handle UTF8 BOM
def setEncoding(mode, encoding):
  if 'b' in mode:
    return {}
  if not encoding:
    encoding = GM.Globals[GM.SYS_ENCODING]
  if 'r' in mode and encoding.lower().replace('-', '') == 'utf8':
    encoding = UTF8_SIG
  return {'encoding': encoding}

def StringIOobject(initbuff=None):
  if initbuff is None:
    return io.StringIO()
  return io.StringIO(initbuff)

# Open a file
def openFile(filename, mode=DEFAULT_FILE_READ_MODE, encoding=None, errors=None, newline=None,
             continueOnError=False, displayError=True, stripUTFBOM=False):
  try:
    if filename != '-':
      kwargs = setEncoding(mode, encoding)
      f = open(os.path.expanduser(filename), mode, errors=errors, newline=newline, **kwargs)
      if stripUTFBOM:
        if 'b' in mode:
          if f.read(3) != b'\xef\xbb\xbf':
            f.seek(0)
        elif not kwargs['encoding'].lower().startswith('utf'):
          if f.read(3).encode('iso-8859-1', 'replace') != codecs.BOM_UTF8:
            f.seek(0)
        else:
          if f.read(1) != '\ufeff':
            f.seek(0)
      return f
    if 'r' in mode:
      return StringIOobject(str(sys.stdin.read()))
    if 'b' not in mode:
      return sys.stdout
    return os.fdopen(os.dup(sys.stdout.fileno()), 'wb')
  except (IOError, LookupError, UnicodeDecodeError, UnicodeError) as e:
    if continueOnError:
      if displayError:
        stderrWarningMsg(fileErrorMessage(filename, e))
        setSysExitRC(FILE_ERROR_RC)
      return None
    systemErrorExit(FILE_ERROR_RC, fileErrorMessage(filename, e))

# Close a file
def closeFile(f, forceFlush=False):
  try:
    if forceFlush:
      # Necessary to make sure file is flushed by both Python and OS
      # https://stackoverflow.com/a/13762137/1503886
      f.flush()
      os.fsync(f.fileno())
    f.close()
    return True
  except IOError as e:
    stderrErrorMsg(fdErrorMessage(f, UNKNOWN, e))
    setSysExitRC(FILE_ERROR_RC)
    return False

# Read a file
def readFile(filename, mode=DEFAULT_FILE_READ_MODE, encoding=None, newline=None,
             continueOnError=False, displayError=True):
  try:
    if filename != '-':
      kwargs = setEncoding(mode, encoding)
      with open(os.path.expanduser(filename), mode, newline=newline, **kwargs) as f:
        return f.read()
    return str(sys.stdin.read())
  except (IOError, LookupError, UnicodeDecodeError, UnicodeError) as e:
    if continueOnError:
      if displayError:
        stderrWarningMsg(fileErrorMessage(filename, e))
        setSysExitRC(FILE_ERROR_RC)
      return None
    systemErrorExit(FILE_ERROR_RC, fileErrorMessage(filename, e))

# Write a file
def writeFile(filename, data, mode=DEFAULT_FILE_WRITE_MODE,
              continueOnError=False, displayError=True):
  try:
    if filename != '-':
      kwargs = setEncoding(mode, None)
      with open(os.path.expanduser(filename), mode, **kwargs) as f:
        f.write(data)
      return True
    GM.Globals[GM.STDOUT].get(GM.REDIRECT_MULTI_FD, sys.stdout).write(data)
    return True
  except (IOError, LookupError, UnicodeDecodeError, UnicodeError) as e:
    if continueOnError:
      if displayError:
        stderrErrorMsg(fileErrorMessage(filename, e))
      setSysExitRC(FILE_ERROR_RC)
      return False
    systemErrorExit(FILE_ERROR_RC, fileErrorMessage(filename, e))

# Write a file, return error
def writeFileReturnError(filename, data, mode=DEFAULT_FILE_WRITE_MODE):
  try:
    kwargs = {'encoding': GM.Globals[GM.SYS_ENCODING]} if 'b' not in mode else {}
    with open(os.path.expanduser(filename), mode, **kwargs) as f:
      f.write(data)
    return (True, None)
  except (IOError, LookupError, UnicodeDecodeError, UnicodeError) as e:
    return (False, e)

# Delete a file
def deleteFile(filename, continueOnError=False, displayError=True):
  if os.path.isfile(filename):
    try:
      os.remove(filename)
    except OSError as e:
      if continueOnError:
        if displayError:
          stderrWarningMsg(fileErrorMessage(filename, e))
        return
      systemErrorExit(FILE_ERROR_RC, fileErrorMessage(filename, e))

def getGDocSheetDataRetryWarning(entityValueList, errMsg, i=0, count=0):
  action = Act.Get()
  Act.Set(Act.RETRIEVE_DATA)
  stderrWarningMsg(formatKeyValueList(Ind.Spaces(),
                                      Ent.FormatEntityValueList(entityValueList)+[Act.NotPerformed(), errMsg, 'Retry', ''],
                                      currentCountNL(i, count)))
  Act.Set(action)

def getGDocSheetDataFailedExit(entityValueList, errMsg, i=0, count=0):
  Act.Set(Act.RETRIEVE_DATA)
  systemErrorExit(ACTION_FAILED_RC, formatKeyValueList(Ind.Spaces(),
                                                       Ent.FormatEntityValueList(entityValueList)+[Act.NotPerformed(), errMsg],
                                                       currentCountNL(i, count)))

def incrAPICallsRetryData(errMsg, delta):
  GM.Globals[GM.API_CALLS_RETRY_DATA].setdefault(errMsg, [0, 0.0])
  GM.Globals[GM.API_CALLS_RETRY_DATA][errMsg][0] += 1
  GM.Globals[GM.API_CALLS_RETRY_DATA][errMsg][1] += delta

def initAPICallsRateCheck():
  GM.Globals[GM.RATE_CHECK_COUNT] = 0
  GM.Globals[GM.RATE_CHECK_START] = time.time()

def checkAPICallsRate():
  GM.Globals[GM.RATE_CHECK_COUNT] += 1
  if GM.Globals[GM.RATE_CHECK_COUNT] >= GC.Values[GC.API_CALLS_RATE_LIMIT]:
    current = time.time()
    delta = int(current-GM.Globals[GM.RATE_CHECK_START])
    if 0 <= delta < 60:
      delta = (60-delta)+3
      error_message = f'API calls per 60 seconds limit {GC.Values[GC.API_CALLS_RATE_LIMIT]} exceeded'
      writeStderr(f'{WARNING_PREFIX}{error_message}: Backing off: {delta} seconds\n')
      flushStderr()
      time.sleep(delta)
      if GC.Values[GC.SHOW_API_CALLS_RETRY_DATA]:
        incrAPICallsRetryData(error_message, delta)
      GM.Globals[GM.RATE_CHECK_START] = time.time()
    else:
      GM.Globals[GM.RATE_CHECK_START] = current
    GM.Globals[GM.RATE_CHECK_COUNT] = 0

def openGAMCommandLog(Globals, name):
  try:
    Globals[GM.CMDLOG_LOGGER] = logging.getLogger(name)
    Globals[GM.CMDLOG_LOGGER].setLevel(logging.INFO)
    Globals[GM.CMDLOG_HANDLER] = RotatingFileHandler(GC.Values[GC.CMDLOG],
                                                     maxBytes=1024*GC.Values[GC.CMDLOG_MAX_KILO_BYTES],
                                                     backupCount=GC.Values[GC.CMDLOG_MAX_BACKUPS],
                                                     encoding=GC.Values[GC.CHARSET])
    Globals[GM.CMDLOG_LOGGER].addHandler(Globals[GM.CMDLOG_HANDLER])
  except Exception as e:
    Globals[GM.CMDLOG_LOGGER] = None
    systemErrorExit(CONFIG_ERROR_RC, Msg.LOGGING_INITIALIZATION_ERROR.format(str(e)))

def writeGAMCommandLog(Globals, logCmd, sysRC):
  from util.args import currentISOformatTimeStamp
  Globals[GM.CMDLOG_LOGGER].info(f'{currentISOformatTimeStamp()},{sysRC},{logCmd}')

def closeGAMCommandLog(Globals):
  try:
    Globals[GM.CMDLOG_HANDLER].flush()
    Globals[GM.CMDLOG_HANDLER].close()
    Globals[GM.CMDLOG_LOGGER].removeHandler(Globals[GM.CMDLOG_HANDLER])
  except Exception:
    pass
  Globals[GM.CMDLOG_LOGGER] = None

def adjustRedirectedSTDFilesIfNotMultiprocessing():
  def adjustRedirectedSTDFile(stdtype):
    rdFd = GM.Globals[stdtype].get(GM.REDIRECT_FD)
    rdMultiFd = GM.Globals[stdtype].get(GM.REDIRECT_MULTI_FD)
    if rdFd and rdMultiFd and rdFd != rdMultiFd:
      try:
        rdFd.write(rdMultiFd.getvalue())
        rdMultiFd.close()
        GM.Globals[stdtype][GM.REDIRECT_MULTI_FD] = rdFd
        if (stdtype == GM.STDOUT) and (GM.Globals.get(GM.SAVED_STDOUT) is not None):
          sys.stdout = rdFd
      except IOError as e:
        systemErrorExit(FILE_ERROR_RC, e)

  adjustRedirectedSTDFile(GM.STDOUT)
  if GM.Globals[GM.STDERR].get(GM.REDIRECT_NAME) != 'stdout':
    adjustRedirectedSTDFile(GM.STDERR)
  else:
    GM.Globals[GM.STDERR][GM.REDIRECT_MULTI_FD] = GM.Globals[GM.STDOUT][GM.REDIRECT_MULTI_FD]


def closeSTDFilesIfNotMultiprocessing(closeSTD):
  def closeSTDFile(stdtype, stdfile):
    rdFd = GM.Globals[stdtype].get(GM.REDIRECT_FD)
    rdMultiFd = GM.Globals[stdtype].get(GM.REDIRECT_MULTI_FD)
    if rdFd and rdMultiFd and (rdFd == rdMultiFd) and (rdFd != stdfile):
      try:
        rdFd.flush()
        if closeSTD:
          rdFd.close()
      except BrokenPipeError:
        pass

  closeSTDFile(GM.STDOUT, sys.stdout)
  if GM.Globals[GM.STDERR].get(GM.REDIRECT_NAME) != 'stdout':
    closeSTDFile(GM.STDERR, sys.stderr)

