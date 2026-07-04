"""GAM batch/multiprocess/thread/loop/list infrastructure.

Multi-process and thread-based batch command execution, CSV command
processing, loop handling, and list/count commands.
"""

import logging
import multiprocessing
import os
import queue
import re
import shlex
import signal
import subprocess
import sys
import threading
import time

from gamlib import api as API
from gamlib import clargs
from gamlib import settings as GC
from gamlib import entity
Ent = entity.GamEntity()
from gamlib import state as GM
from gamlib import msgs as Msg

from util.csv_pf import CSVPrintFile
from gam.constants import HARD_ERROR_RC, KEYBOARD_INTERRUPT_RC
from util.api import buildGAPIObject
from util.args import UTF8, checkArgumentPresent, checkForExtraneousArguments, checkMatchSkipFields, getBoolean, getCharSet, getDelimiter, getInteger, getMatchSkipFields, getString, normalizeEmailAddressOrUID, todaysTime
from util.csv_pf import CheckInputRowFilterHeaders
from util.display import actionPerformedNumItems
from util.entity import getEntityArgument, getEntityList, getEntityToModify
from util.errors import USAGE_ERROR_RC, csvFieldErrorExit, formatChoiceList, missingArgumentExit, usageErrorExit
from util.fileio import FILE_ERROR_RC, StringIOobject, adjustRedirectedSTDFilesIfNotMultiprocessing, closeFile, closeGAMCommandLog, fdErrorMessage, fileErrorMessage, openFile, openGAMCommandLog, setFilePath, writeGAMCommandLog
from util.gdoc import getGDocData, getStorageFileData, openCSVFileReader
from util.output import ERROR_PREFIX, currentISOformatTimeStamp, flushStderr, flushStdout, readStdin, setSysExitRC, systemErrorExit, writeStderr, writeStdout
from gam.constants import GAM
from gam.var import Cmd, Ind




class NullHandler(logging.Handler):
  def emit(self, record):
    pass

def initializeLogging():
  nh = NullHandler()
  logging.getLogger().addHandler(nh)

def saveNonPickleableValues():
  savedValues = {GM.CSVFILE: {}, GM.STDOUT: {}, GM.STDERR: {},
                 GM.SAVED_STDOUT: None, GM.CMDLOG_HANDLER: None, GM.CMDLOG_LOGGER: None}
  savedValues[GM.CSVFILE][GM.REDIRECT_FD] = GM.Globals[GM.CSVFILE].pop(GM.REDIRECT_FD, None)
  savedValues[GM.STDOUT][GM.REDIRECT_FD] = GM.Globals[GM.STDOUT].pop(GM.REDIRECT_FD, None)
  savedValues[GM.STDOUT][GM.REDIRECT_MULTI_FD] = GM.Globals[GM.STDOUT].pop(GM.REDIRECT_MULTI_FD, None)
  savedValues[GM.STDERR][GM.REDIRECT_FD] = GM.Globals[GM.STDERR].pop(GM.REDIRECT_FD, None)
  savedValues[GM.STDERR][GM.REDIRECT_MULTI_FD] = GM.Globals[GM.STDERR].pop(GM.REDIRECT_MULTI_FD, None)
  savedValues[GM.SAVED_STDOUT] = GM.Globals[GM.SAVED_STDOUT]
  GM.Globals[GM.SAVED_STDOUT] = None
  savedValues[GM.CMDLOG_HANDLER] = GM.Globals[GM.CMDLOG_HANDLER]
  GM.Globals[GM.CMDLOG_HANDLER] = None
  savedValues[GM.CMDLOG_LOGGER] = GM.Globals[GM.CMDLOG_LOGGER]
  GM.Globals[GM.CMDLOG_LOGGER] = None
  return savedValues

def restoreNonPickleableValues(savedValues):
  GM.Globals[GM.CSVFILE][GM.REDIRECT_FD] = savedValues[GM.CSVFILE][GM.REDIRECT_FD]
  GM.Globals[GM.STDOUT][GM.REDIRECT_FD] = savedValues[GM.STDOUT][GM.REDIRECT_FD]
  GM.Globals[GM.STDOUT][GM.REDIRECT_MULTI_FD] = savedValues[GM.STDOUT][GM.REDIRECT_MULTI_FD]
  GM.Globals[GM.STDERR][GM.REDIRECT_FD] = savedValues[GM.STDERR][GM.REDIRECT_FD]
  GM.Globals[GM.STDERR][GM.REDIRECT_MULTI_FD] = savedValues[GM.STDERR][GM.REDIRECT_MULTI_FD]
  GM.Globals[GM.SAVED_STDOUT] = savedValues[GM.SAVED_STDOUT]
  GM.Globals[GM.CMDLOG_HANDLER] = savedValues[GM.CMDLOG_HANDLER]
  GM.Globals[GM.CMDLOG_LOGGER] = savedValues[GM.CMDLOG_LOGGER]

def CSVFileQueueHandler(mpQueue, mpQueueStdout, mpQueueStderr, csvPF, datetimeNow, tzinfo, output_timeformat):
  global Cmd

  def reopenSTDFile(stdtype):
    if GM.Globals[stdtype][GM.REDIRECT_NAME] == 'null':
      GM.Globals[stdtype][GM.REDIRECT_FD] = open(os.devnull, GM.Globals[stdtype][GM.REDIRECT_MODE], encoding=UTF8)
    elif GM.Globals[stdtype][GM.REDIRECT_NAME] == '-':
      GM.Globals[stdtype][GM.REDIRECT_FD] = os.fdopen(os.dup([sys.stderr.fileno(), sys.stdout.fileno()][stdtype == GM.STDOUT]),
                                                      GM.Globals[stdtype][GM.REDIRECT_MODE], encoding=GM.Globals[GM.SYS_ENCODING])
    elif stdtype == GM.STDERR and GM.Globals[stdtype][GM.REDIRECT_NAME] == 'stdout':
      GM.Globals[stdtype][GM.REDIRECT_FD] = GM.Globals[GM.STDOUT][GM.REDIRECT_FD]
    else:
      GM.Globals[stdtype][GM.REDIRECT_FD] = openFile(GM.Globals[stdtype][GM.REDIRECT_NAME], GM.Globals[stdtype][GM.REDIRECT_MODE])
    if stdtype == GM.STDERR and GM.Globals[stdtype][GM.REDIRECT_NAME] == 'stdout':
      GM.Globals[stdtype][GM.REDIRECT_MULTI_FD] = GM.Globals[GM.STDOUT][GM.REDIRECT_MULTI_FD]
    else:
      GM.Globals[stdtype][GM.REDIRECT_MULTI_FD] = GM.Globals[stdtype][GM.REDIRECT_FD] if not GM.Globals[stdtype][GM.REDIRECT_MULTIPROCESS] else StringIOobject()

  GM.Globals[GM.DATETIME_NOW] = datetimeNow
  GC.Values[GC.TIMEZONE] = tzinfo
  GC.Values[GC.OUTPUT_TIMEFORMAT] = output_timeformat
  clearRowFilters = False
  if multiprocessing.get_start_method() != 'fork':
    signal.signal(signal.SIGINT, signal.SIG_IGN)
    Cmd = clargs.GamCLArgs()
  else:
    csvPF.SetColumnDelimiter(GC.Values[GC.CSV_OUTPUT_COLUMN_DELIMITER])
    csvPF.SetNoEscapeChar(GC.Values[GC.CSV_OUTPUT_NO_ESCAPE_CHAR])
    csvPF.SetQuoteChar(GC.Values[GC.CSV_OUTPUT_QUOTE_CHAR])
    csvPF.SetSortHeaders(GC.Values[GC.CSV_OUTPUT_SORT_HEADERS])
    csvPF.SetTimestampColumn(GC.Values[GC.CSV_OUTPUT_TIMESTAMP_COLUMN])
    csvPF.SetHeaderFilter(GC.Values[GC.CSV_OUTPUT_HEADER_FILTER])
    csvPF.SetHeaderDropFilter(GC.Values[GC.CSV_OUTPUT_HEADER_DROP_FILTER])
    csvPF.SetRowFilter(GC.Values[GC.CSV_OUTPUT_ROW_FILTER], GC.Values[GC.CSV_OUTPUT_ROW_FILTER_MODE])
    csvPF.SetRowDropFilter(GC.Values[GC.CSV_OUTPUT_ROW_DROP_FILTER], GC.Values[GC.CSV_OUTPUT_ROW_DROP_FILTER_MODE])
    csvPF.SetRowLimit(GC.Values[GC.CSV_OUTPUT_ROW_LIMIT])
  list_type = 'CSV'
  while True:
    dataType, dataItem = mpQueue.get()
    if dataType == GM.REDIRECT_QUEUE_NAME:
      list_type = dataItem
    elif dataType == GM.REDIRECT_QUEUE_TODRIVE:
      csvPF.todrive = dataItem
    elif dataType == GM.REDIRECT_QUEUE_CSVPF:
      csvPF.AddTitles(dataItem[0])
      csvPF.SetSortTitles(dataItem[1])
      csvPF.SetIndexedTitles(dataItem[2])
      csvPF.SetFormatJSON(dataItem[3])
      csvPF.AddJSONTitles(dataItem[4])
      csvPF.SetColumnDelimiter(dataItem[5])
      csvPF.SetNoEscapeChar(dataItem[6])
      csvPF.SetQuoteChar(dataItem[7])
      csvPF.SetSortHeaders(dataItem[8])
      csvPF.SetTimestampColumn(dataItem[9])
      csvPF.SetFixPaths(dataItem[10])
      csvPF.SetNodataFields(dataItem[11], dataItem[12], dataItem[13], dataItem[14], dataItem[15])
      csvPF.SetShowPermissionsLast(dataItem[16])
      csvPF.SetZeroBlankMimeTypeCounts(dataItem[17])
    elif dataType == GM.REDIRECT_QUEUE_DATA:
      csvPF.rows.extend(dataItem)
    elif dataType == GM.REDIRECT_QUEUE_ARGS:
      Cmd.InitializeArguments(dataItem)
    elif dataType == GM.REDIRECT_QUEUE_GLOBALS:
      GM.Globals = dataItem
      if multiprocessing.get_start_method() != 'fork':
        reopenSTDFile(GM.STDOUT)
        reopenSTDFile(GM.STDERR)
    elif dataType == GM.REDIRECT_QUEUE_VALUES:
      GC.Values = dataItem
      csvPF.SetColumnDelimiter(GC.Values[GC.CSV_OUTPUT_COLUMN_DELIMITER])
      csvPF.SetNoEscapeChar(GC.Values[GC.CSV_OUTPUT_NO_ESCAPE_CHAR])
#      csvPF.SetQuoteChar(GC.Values[GC.CSV_OUTPUT_QUOTE_CHAR])
      csvPF.SetSortHeaders(GC.Values[GC.CSV_OUTPUT_SORT_HEADERS])
      csvPF.SetTimestampColumn(GC.Values[GC.CSV_OUTPUT_TIMESTAMP_COLUMN])
      csvPF.SetHeaderFilter(GC.Values[GC.CSV_OUTPUT_HEADER_FILTER])
      csvPF.SetHeaderDropFilter(GC.Values[GC.CSV_OUTPUT_HEADER_DROP_FILTER])
      if not clearRowFilters:
        csvPF.SetRowFilter(GC.Values[GC.CSV_OUTPUT_ROW_FILTER], GC.Values[GC.CSV_OUTPUT_ROW_FILTER_MODE])
        csvPF.SetRowDropFilter(GC.Values[GC.CSV_OUTPUT_ROW_DROP_FILTER], GC.Values[GC.CSV_OUTPUT_ROW_DROP_FILTER_MODE])
      else:
        csvPF.SetRowFilter([], GC.Values[GC.CSV_OUTPUT_ROW_FILTER_MODE])
        csvPF.SetRowDropFilter([], GC.Values[GC.CSV_OUTPUT_ROW_DROP_FILTER_MODE])
      csvPF.SetRowLimit(GC.Values[GC.CSV_OUTPUT_ROW_LIMIT])
    elif dataType == GM.REDIRECT_QUEUE_CLEAR_ROW_FILTERS:
      clearRowFilters = dataItem
    else: #GM.REDIRECT_QUEUE_EOF
      break
  csvPF.writeCSVfile(list_type)
  if mpQueueStdout:
    mpQueueStdout.put((0, GM.REDIRECT_QUEUE_DATA, GM.Globals[GM.STDOUT][GM.REDIRECT_MULTI_FD].getvalue()))
  else:
    flushStdout()
  if mpQueueStderr and mpQueueStderr is not mpQueueStdout:
    mpQueueStderr.put((0, GM.REDIRECT_QUEUE_DATA, GM.Globals[GM.STDERR][GM.REDIRECT_MULTI_FD].getvalue()))
  else:
    flushStderr()

def initializeCSVFileQueueHandler(mpManager, mpQueueStdout, mpQueueStderr):
  mpQueue = mpManager.Queue()
  mpQueueHandler = multiprocessing.Process(target=CSVFileQueueHandler,
                                           args=(mpQueue, mpQueueStdout, mpQueueStderr,
                                                 GM.Globals[GM.CSVFILE][GM.REDIRECT_QUEUE_CSVPF],
                                                 GM.Globals[GM.DATETIME_NOW], GC.Values[GC.TIMEZONE],
                                                 GC.Values[GC.OUTPUT_TIMEFORMAT]))
  mpQueueHandler.start()
  return (mpQueue, mpQueueHandler)

def terminateCSVFileQueueHandler(mpQueue, mpQueueHandler):
  GM.Globals[GM.PARSER] = None
  GM.Globals[GM.CSVFILE][GM.REDIRECT_QUEUE] = None
  if multiprocessing.get_start_method() != 'fork':
    mpQueue.put((GM.REDIRECT_QUEUE_ARGS, Cmd.AllArguments()))
    savedValues = saveNonPickleableValues()
    mpQueue.put((GM.REDIRECT_QUEUE_GLOBALS, GM.Globals))
    restoreNonPickleableValues(savedValues)
    mpQueue.put((GM.REDIRECT_QUEUE_VALUES, GC.Values))
  mpQueue.put((GM.REDIRECT_QUEUE_EOF, None))
  mpQueueHandler.join()

def StdQueueHandler(mpQueue, stdtype, gmGlobals, gcValues):

  PROCESS_MSG = '{0}: {1:6d}, {2:>5s}: {3}, RC: {4:3d}, Cmd: {5}\n'

  def _writeData(data):
    fd.write(data)

  def _writePidData(pid, data):
    try:
      if pid != 0 and GC.Values[GC.SHOW_MULTIPROCESS_INFO]:
        _writeData(PROCESS_MSG.format(pidData[pid]['queue'], pid, 'Start', pidData[pid]['start'], 0, pidData[pid]['cmd']))
      if data[1] is not None:
        _writeData(data[1])
      if GC.Values[GC.SHOW_MULTIPROCESS_INFO]:
        _writeData(PROCESS_MSG.format(pidData[pid]['queue'], pid, 'End', currentISOformatTimeStamp(), data[0], pidData[pid]['cmd']))
      fd.flush()
    except IOError as e:
      systemErrorExit(FILE_ERROR_RC, fdErrorMessage(fd, GM.Globals[stdtype][GM.REDIRECT_NAME], e))

  if multiprocessing.get_start_method() != 'fork':
    signal.signal(signal.SIGINT, signal.SIG_IGN)
    GM.Globals = gmGlobals.copy()
    GC.Values = gcValues.copy()
  pid0DataItem = [KEYBOARD_INTERRUPT_RC, None]
  pidData = {}
  if multiprocessing.get_start_method() != 'fork':
    if GM.Globals[stdtype][GM.REDIRECT_NAME] == 'null':
      fd = open(os.devnull, GM.Globals[stdtype][GM.REDIRECT_MODE], encoding=UTF8)
    elif GM.Globals[stdtype][GM.REDIRECT_NAME] == '-':
      fd = os.fdopen(os.dup([sys.stderr.fileno(), sys.stdout.fileno()][GM.Globals[stdtype][GM.REDIRECT_QUEUE] == 'stdout']),
                     GM.Globals[stdtype][GM.REDIRECT_MODE], encoding=GM.Globals[GM.SYS_ENCODING])
    elif GM.Globals[stdtype][GM.REDIRECT_NAME] == 'stdout' and GM.Globals[stdtype][GM.REDIRECT_QUEUE] == 'stderr':
      fd = os.fdopen(os.dup(sys.stdout.fileno()), GM.Globals[stdtype][GM.REDIRECT_MODE], encoding=GM.Globals[GM.SYS_ENCODING])
    else:
      fd = openFile(GM.Globals[stdtype][GM.REDIRECT_NAME], GM.Globals[stdtype][GM.REDIRECT_MODE])
  else:
    fd = GM.Globals[stdtype][GM.REDIRECT_FD]
  while True:
    try:
      pid, dataType, dataItem = mpQueue.get()
    except (EOFError, ValueError):
      break
    if dataType == GM.REDIRECT_QUEUE_START:
      pidData[pid] = {'queue': GM.Globals[stdtype][GM.REDIRECT_QUEUE],
                      'start': currentISOformatTimeStamp(),
                      'cmd': Cmd.QuotedArgumentList(dataItem)}
      if pid == 0 and GC.Values[GC.SHOW_MULTIPROCESS_INFO]:
        fd.write(PROCESS_MSG.format(pidData[pid]['queue'], pid, 'Start', pidData[pid]['start'], 0, pidData[pid]['cmd']))
    elif dataType == GM.REDIRECT_QUEUE_DATA:
      _writeData(dataItem)
    elif dataType == GM.REDIRECT_QUEUE_END:
      if pid != 0:
        _writePidData(pid, dataItem)
        del pidData[pid]
      else:
        pid0DataItem = dataItem
    else: #GM.REDIRECT_QUEUE_EOF
      break
  for pid in pidData:
    if pid != 0:
      _writePidData(pid, [KEYBOARD_INTERRUPT_RC, None])
  _writePidData(0, pid0DataItem)
  if fd not in [sys.stdout, sys.stderr]:
    try:
      fd.flush()
      fd.close()
    except IOError:
      pass
  GM.Globals[stdtype][GM.REDIRECT_FD] = None

def initializeStdQueueHandler(mpManager, stdtype, gmGlobals, gcValues):
  mpQueue = mpManager.Queue()
  mpQueueHandler = multiprocessing.Process(target=StdQueueHandler, args=(mpQueue, stdtype, gmGlobals, gcValues))
  mpQueueHandler.start()
  return (mpQueue, mpQueueHandler)

def batchWriteStderr(data):
  try:
    sys.stderr.write(data)
    sys.stderr.flush()
  except IOError as e:
    systemErrorExit(FILE_ERROR_RC, fileErrorMessage('stderr', e))

def writeStdQueueHandler(mpQueue, item):
  while True:
    try:
      mpQueue.put(item)
      return
    except Exception as e:
      time.sleep(1)
      batchWriteStderr(f'{currentISOformatTimeStamp()},{item[0]}/{GM.Globals[GM.NUM_BATCH_ITEMS]},Error,{str(e)}\n')

def terminateStdQueueHandler(mpQueue, mpQueueHandler):
  mpQueue.put((0, GM.REDIRECT_QUEUE_EOF, None))
  mpQueueHandler.join()

def ProcessGAMCommandMulti(pid, numItems, logCmd, mpQueueCSVFile, mpQueueStdout, mpQueueStderr,
                           debugLevel, todrive, printAguDomains,
                           printCrosOUs, printCrosOUsAndChildren,
                           output_dateformat, output_timeformat,
                           csvColumnDelimiter, csvNoEscapeChar, csvQuoteChar,
                           csvSortHeaders, csvTimestampColumn,
                           csvHeaderFilter, csvHeaderDropFilter,
                           csvHeaderForce, csvHeaderOrder, csvHeaderRequired,
                           csvRowFilter, csvRowFilterMode, csvRowDropFilter, csvRowDropFilterMode,
                           csvRowLimit,
                           showGettings, showGettingsGotNL,
                           args):
  from gam import ProcessGAMCommand
  global mplock

  with mplock:
    initializeLogging()
    if multiprocessing.get_start_method() != 'fork':
      signal.signal(signal.SIGINT, signal.SIG_IGN)
    GM.Globals[GM.API_CALLS_RETRY_DATA] = {}
    GM.Globals[GM.CMDLOG_LOGGER] = None
    GM.Globals[GM.CSVFILE] = {}
    GM.Globals[GM.CSV_DATA_DICT] = {}
    GM.Globals[GM.CSV_KEY_FIELD] = None
    GM.Globals[GM.CSV_SUBKEY_FIELD] = None
    GM.Globals[GM.CSV_DATA_FIELD] = None
    GM.Globals[GM.CSV_OUTPUT_COLUMN_DELIMITER] = csvColumnDelimiter
    GM.Globals[GM.CSV_OUTPUT_NO_ESCAPE_CHAR] = csvNoEscapeChar
    GM.Globals[GM.CSV_OUTPUT_HEADER_DROP_FILTER] = csvHeaderDropFilter[:]
    GM.Globals[GM.CSV_OUTPUT_HEADER_FILTER] = csvHeaderFilter[:]
    GM.Globals[GM.CSV_OUTPUT_HEADER_FORCE] = csvHeaderForce[:]
    GM.Globals[GM.CSV_OUTPUT_HEADER_ORDER] = csvHeaderOrder[:]
    GM.Globals[GM.CSV_OUTPUT_HEADER_REQUIRED] = csvHeaderRequired[:]
    GM.Globals[GM.CSV_OUTPUT_QUOTE_CHAR] = csvQuoteChar
    GM.Globals[GM.CSV_OUTPUT_ROW_DROP_FILTER] = csvRowDropFilter[:]
    GM.Globals[GM.CSV_OUTPUT_ROW_DROP_FILTER_MODE] = csvRowDropFilterMode
    GM.Globals[GM.CSV_OUTPUT_ROW_FILTER] = csvRowFilter[:]
    GM.Globals[GM.CSV_OUTPUT_ROW_FILTER_MODE] = csvRowFilterMode
    GM.Globals[GM.CSV_OUTPUT_ROW_LIMIT] = csvRowLimit
    GM.Globals[GM.CSV_OUTPUT_SORT_HEADERS] = csvSortHeaders[:]
    GM.Globals[GM.CSV_OUTPUT_TIMESTAMP_COLUMN] = csvTimestampColumn
    GM.Globals[GM.CSV_TODRIVE] = todrive.copy()
    GM.Globals[GM.DEBUG_LEVEL] = debugLevel
    GM.Globals[GM.OUTPUT_DATEFORMAT] = output_dateformat
    GM.Globals[GM.OUTPUT_TIMEFORMAT] = output_timeformat
    GM.Globals[GM.NUM_BATCH_ITEMS] = numItems
    GM.Globals[GM.PID] = pid
    GM.Globals[GM.PRINT_AGU_DOMAINS] = printAguDomains[:]
    GM.Globals[GM.PRINT_CROS_OUS] = printCrosOUs[:]
    GM.Globals[GM.PRINT_CROS_OUS_AND_CHILDREN] = printCrosOUsAndChildren[:]
    GM.Globals[GM.SAVED_STDOUT] = None
    GM.Globals[GM.SHOW_GETTINGS] = showGettings
    GM.Globals[GM.SHOW_GETTINGS_GOT_NL] = showGettingsGotNL
    GM.Globals[GM.SYSEXITRC] = 0
    GM.Globals[GM.PARSER] = None
    if mpQueueCSVFile:
      GM.Globals[GM.CSVFILE][GM.REDIRECT_QUEUE] = mpQueueCSVFile
    if mpQueueStdout:
      GM.Globals[GM.STDOUT] = {GM.REDIRECT_NAME: '', GM.REDIRECT_FD: None, GM.REDIRECT_MULTI_FD: StringIOobject()}
      if debugLevel:
        sys.stdout = GM.Globals[GM.STDOUT][GM.REDIRECT_MULTI_FD]
#      mpQueueStdout.put((pid, GM.REDIRECT_QUEUE_START, args))
      writeStdQueueHandler(mpQueueStdout,(pid, GM.REDIRECT_QUEUE_START, args))
    else:
      GM.Globals[GM.STDOUT] = {}
    if mpQueueStderr:
      if mpQueueStderr is not mpQueueStdout:
        GM.Globals[GM.STDERR] = {GM.REDIRECT_NAME: '', GM.REDIRECT_FD: None, GM.REDIRECT_MULTI_FD: StringIOobject()}
#        mpQueueStderr.put((pid, GM.REDIRECT_QUEUE_START, args))
        writeStdQueueHandler(mpQueueStderr, (pid, GM.REDIRECT_QUEUE_START, args))
      else:
        GM.Globals[GM.STDERR][GM.REDIRECT_MULTI_FD] = GM.Globals[GM.STDOUT][GM.REDIRECT_MULTI_FD]
    else:
      GM.Globals[GM.STDERR] = {}
  sysRC = ProcessGAMCommand(args)
  with mplock:
    if mpQueueStdout:
#      mpQueueStdout.put((pid, GM.REDIRECT_QUEUE_END, [sysRC, GM.Globals[GM.STDOUT][GM.REDIRECT_MULTI_FD].getvalue()]))
      writeStdQueueHandler(mpQueueStdout, (pid, GM.REDIRECT_QUEUE_END, [sysRC, GM.Globals[GM.STDOUT][GM.REDIRECT_MULTI_FD].getvalue()]))
      GM.Globals[GM.STDOUT][GM.REDIRECT_MULTI_FD].close()
      GM.Globals[GM.STDOUT][GM.REDIRECT_MULTI_FD] = None
    if mpQueueStderr and mpQueueStderr is not mpQueueStdout:
#      mpQueueStderr.put((pid, GM.REDIRECT_QUEUE_END, [sysRC, GM.Globals[GM.STDERR][GM.REDIRECT_MULTI_FD].getvalue()]))
      writeStdQueueHandler(mpQueueStderr, (pid, GM.REDIRECT_QUEUE_END, [sysRC, GM.Globals[GM.STDERR][GM.REDIRECT_MULTI_FD].getvalue()]))
      GM.Globals[GM.STDERR][GM.REDIRECT_MULTI_FD].close()
      GM.Globals[GM.STDERR][GM.REDIRECT_MULTI_FD] = None
  return (pid, sysRC, logCmd)

ERROR_PLURAL_SINGULAR = [Msg.ERRORS, Msg.ERROR]
PROCESS_PLURAL_SINGULAR = [Msg.PROCESSES, Msg.PROCESS]
THREAD_PLURAL_SINGULAR = [Msg.THREADS, Msg.THREAD]

def checkChildProcessRC(rc):
# Comparison
  if 'comp' in GM.Globals[GM.MULTIPROCESS_EXIT_CONDITION]:
    op = GM.Globals[GM.MULTIPROCESS_EXIT_CONDITION]['comp']
    value = GM.Globals[GM.MULTIPROCESS_EXIT_CONDITION]['value']
    if op == '<':
      return rc < value
    if op == '<=':
      return rc <= value
    if op == '>':
      return rc > value
    if op == '>=':
      return rc >= value
    if op == '!=':
      return rc != value
    return rc == value
# Range
  op = GM.Globals[GM.MULTIPROCESS_EXIT_CONDITION]['range']
  low = GM.Globals[GM.MULTIPROCESS_EXIT_CONDITION]['low']
  high = GM.Globals[GM.MULTIPROCESS_EXIT_CONDITION]['high']
  if op == '!=':
    return not low <= rc <= high
  return low <= rc <= high

def initGamWorker(l):
  global mplock
  mplock = l

def MultiprocessGAMCommands(items, showCmds):
  def poolCallback(result):
    poolProcessResults[0] -= 1
    if showCmds:
      batchWriteStderr(f'{currentISOformatTimeStamp()},{result[0]}/{numItems},End,{result[1]},{result[2]}\n')
    if GM.Globals[GM.CMDLOG_LOGGER]:
      GM.Globals[GM.CMDLOG_LOGGER].info(f'{currentISOformatTimeStamp()},{result[1]},{result[2]}')
    if GM.Globals[GM.MULTIPROCESS_EXIT_CONDITION] is not None and checkChildProcessRC(result[1]):
      GM.Globals[GM.MULTIPROCESS_EXIT_PROCESSING] = True

  def signal_handler(*_):
    nonlocal controlC
    controlC = True

  def handleControlC(source):
    nonlocal controlC
    batchWriteStderr(f'Control-C (Multiprocess-{source})\n')
    setSysExitRC(KEYBOARD_INTERRUPT_RC)
    batchWriteStderr(Msg.BATCH_CSV_TERMINATE_N_PROCESSES.format(currentISOformatTimeStamp(),
                                                                numItems, poolProcessResults[0],
                                                                PROCESS_PLURAL_SINGULAR[poolProcessResults[0] == 1]))
    pool.terminate()
    controlC = False

  if not items:
    return
  GM.Globals[GM.NUM_BATCH_ITEMS] = numItems = len(items)
  numPoolProcesses = min(numItems, GC.Values[GC.NUM_THREADS])
  if GC.Values[GC.MULTIPROCESS_POOL_LIMIT] == -1:
    parallelPoolProcesses = -1
  elif GC.Values[GC.MULTIPROCESS_POOL_LIMIT] == 0:
    parallelPoolProcesses = numPoolProcesses
  else:
    parallelPoolProcesses = min(numItems, GC.Values[GC.MULTIPROCESS_POOL_LIMIT])
#  origSigintHandler = signal.signal(signal.SIGINT, signal.SIG_IGN)
  signal.signal(signal.SIGINT, signal.SIG_IGN)
  mpManager = multiprocessing.Manager()
  l = mpManager.Lock()
  try:
    if multiprocessing.get_start_method() != 'fork':
      pool = mpManager.Pool(processes=numPoolProcesses, initializer=initGamWorker, initargs=(l,), maxtasksperchild=200)
    else:
      pool = multiprocessing.Pool(processes=numPoolProcesses, initializer=initGamWorker, initargs=(l,), maxtasksperchild=200)
  except IOError as e:
    systemErrorExit(FILE_ERROR_RC, e)
  except AssertionError as e:
    Cmd.SetLocation(0)
    usageErrorExit(str(e))
  if multiprocessing.get_start_method() != 'fork':
    savedValues = saveNonPickleableValues()
  if GM.Globals[GM.STDOUT][GM.REDIRECT_MULTIPROCESS]:
    mpQueueStdout, mpQueueHandlerStdout = initializeStdQueueHandler(mpManager, GM.STDOUT, GM.Globals, GC.Values)
    mpQueueStdout.put((0, GM.REDIRECT_QUEUE_START, Cmd.AllArguments()))
  else:
    mpQueueStdout = None
  if GM.Globals[GM.STDERR][GM.REDIRECT_MULTIPROCESS]:
    if GM.Globals[GM.STDERR][GM.REDIRECT_NAME] != 'stdout':
      mpQueueStderr, mpQueueHandlerStderr = initializeStdQueueHandler(mpManager, GM.STDERR, GM.Globals, GC.Values)
      mpQueueStderr.put((0, GM.REDIRECT_QUEUE_START, Cmd.AllArguments()))
    else:
      mpQueueStderr = mpQueueStdout
  else:
    mpQueueStderr = None
  if multiprocessing.get_start_method() != 'fork':
    restoreNonPickleableValues(savedValues)
  if mpQueueStdout:
    mpQueueStdout.put((0, GM.REDIRECT_QUEUE_DATA, GM.Globals[GM.STDOUT][GM.REDIRECT_MULTI_FD].getvalue()))
    GM.Globals[GM.STDOUT][GM.REDIRECT_MULTI_FD].truncate(0)
  if mpQueueStderr and mpQueueStderr is not mpQueueStdout:
    mpQueueStderr.put((0, GM.REDIRECT_QUEUE_DATA, GM.Globals[GM.STDERR][GM.REDIRECT_MULTI_FD].getvalue()))
    GM.Globals[GM.STDERR][GM.REDIRECT_MULTI_FD].truncate(0)
  if GM.Globals[GM.CSVFILE][GM.REDIRECT_MULTIPROCESS]:
    mpQueueCSVFile, mpQueueHandlerCSVFile = initializeCSVFileQueueHandler(mpManager, mpQueueStdout, mpQueueStderr)
  else:
    mpQueueCSVFile = None
#  signal.signal(signal.SIGINT, origSigintHandler)
  controlC = False
  signal.signal(signal.SIGINT, signal_handler)
  batchWriteStderr(Msg.USING_N_PROCESSES.format(currentISOformatTimeStamp(),
                                                numItems, numPoolProcesses,
                                                PROCESS_PLURAL_SINGULAR[numPoolProcesses == 1]))
  try:
    pid = 0
    poolProcessResults = {pid: 0}
    for item in items:
      if GM.Globals[GM.MULTIPROCESS_EXIT_PROCESSING]:
        break
      if controlC:
        break
      if item[0] == Cmd.COMMIT_BATCH_CMD:
        batchWriteStderr(Msg.COMMIT_BATCH_WAIT_N_PROCESSES.format(currentISOformatTimeStamp(),
                                                                   numItems, poolProcessResults[0],
                                                                   PROCESS_PLURAL_SINGULAR[poolProcessResults[0] == 1]))
        while poolProcessResults[0] > 0:
          time.sleep(1)
          completedProcesses = []
          for p, result in poolProcessResults.items():
            if p != 0 and result.ready():
              poolCallback(result.get())
              completedProcesses.append(p)
          for p in completedProcesses:
            del poolProcessResults[p]
        batchWriteStderr(Msg.COMMIT_BATCH_COMPLETE.format(currentISOformatTimeStamp(), numItems, Msg.PROCESSES))
        if len(item) > 1:
          readStdin(f'{currentISOformatTimeStamp()},0/{numItems},{Cmd.QuotedArgumentList(item[1:])}')
        continue
      if item[0] == Cmd.PRINT_CMD:
        batchWriteStderr(Cmd.QuotedArgumentList(item[1:])+'\n')
        continue
      if item[0] == Cmd.SLEEP_CMD:
        batchWriteStderr(f'{currentISOformatTimeStamp()},0/{numItems},Sleepiing {item[1]} seconds\n')
        time.sleep(int(item[1]))
        continue
      pid += 1
      if not showCmds and ((pid % 100 == 0) or (pid == numItems)):
        batchWriteStderr(Msg.PROCESSING_ITEM_N_OF_M.format(currentISOformatTimeStamp(), pid, numItems))
      if showCmds or GM.Globals[GM.CMDLOG_LOGGER]:
        logCmd = Cmd.QuotedArgumentList(item)
        if showCmds:
          batchWriteStderr(f'{currentISOformatTimeStamp()},{pid}/{numItems},Start,0,{logCmd}\n')
      else:
        logCmd = ''
      poolProcessResults[pid] = pool.apply_async(ProcessGAMCommandMulti,
                                                 [pid, numItems, logCmd, mpQueueCSVFile, mpQueueStdout, mpQueueStderr,
                                                  GC.Values[GC.DEBUG_LEVEL], GM.Globals[GM.CSV_TODRIVE],
                                                  GC.Values[GC.PRINT_AGU_DOMAINS],
                                                  GC.Values[GC.PRINT_CROS_OUS], GC.Values[GC.PRINT_CROS_OUS_AND_CHILDREN],
                                                  GC.Values[GC.OUTPUT_DATEFORMAT], GC.Values[GC.OUTPUT_TIMEFORMAT],
                                                  GC.Values[GC.CSV_OUTPUT_COLUMN_DELIMITER],
                                                  GC.Values[GC.CSV_OUTPUT_NO_ESCAPE_CHAR],
                                                  GC.Values[GC.CSV_OUTPUT_QUOTE_CHAR],
                                                  GC.Values[GC.CSV_OUTPUT_SORT_HEADERS],
                                                  GC.Values[GC.CSV_OUTPUT_TIMESTAMP_COLUMN],
                                                  GC.Values[GC.CSV_OUTPUT_HEADER_FILTER],
                                                  GC.Values[GC.CSV_OUTPUT_HEADER_DROP_FILTER],
                                                  GC.Values[GC.CSV_OUTPUT_HEADER_FORCE],
                                                  GC.Values[GC.CSV_OUTPUT_HEADER_ORDER],
                                                  GC.Values[GC.CSV_OUTPUT_HEADER_REQUIRED],
                                                  GC.Values[GC.CSV_OUTPUT_ROW_FILTER],
                                                  GC.Values[GC.CSV_OUTPUT_ROW_FILTER_MODE],
                                                  GC.Values[GC.CSV_OUTPUT_ROW_DROP_FILTER],
                                                  GC.Values[GC.CSV_OUTPUT_ROW_DROP_FILTER_MODE],
                                                  GC.Values[GC.CSV_OUTPUT_ROW_LIMIT],
                                                  GC.Values[GC.SHOW_GETTINGS], GC.Values[GC.SHOW_GETTINGS_GOT_NL],
                                                  item])
      poolProcessResults[0] += 1
      if parallelPoolProcesses > 0:
        while poolProcessResults[0] == parallelPoolProcesses:
          completedProcesses = []
          for p, result in poolProcessResults.items():
            if p != 0 and result.ready():
              poolCallback(result.get())
              completedProcesses.append(p)
          if completedProcesses:
            for p in completedProcesses:
              del poolProcessResults[p]
            break
          time.sleep(1)
    processWaitStart = time.time()
    if not controlC:
      if GC.Values[GC.PROCESS_WAIT_LIMIT] > 0:
        waitRemaining = GC.Values[GC.PROCESS_WAIT_LIMIT]
      else:
        waitRemaining = 'unlimited'
      while poolProcessResults[0] > 0:
        batchWriteStderr(Msg.BATCH_CSV_WAIT_N_PROCESSES.format(currentISOformatTimeStamp(),
                                                               numItems, poolProcessResults[0],
                                                               PROCESS_PLURAL_SINGULAR[poolProcessResults[0] == 1],
                                                               Msg.BATCH_CSV_WAIT_LIMIT.format(waitRemaining)))
        completedProcesses = []
        for p, result in poolProcessResults.items():
          if p != 0 and result.ready():
            poolCallback(result.get())
            completedProcesses.append(p)
        for p in completedProcesses:
          del poolProcessResults[p]
        if poolProcessResults[0] > 0:
          if controlC:
            handleControlC('SIG')
            break
          time.sleep(5)
          if GC.Values[GC.PROCESS_WAIT_LIMIT] > 0:
            delta = int(time.time()-processWaitStart)
            if delta >= GC.Values[GC.PROCESS_WAIT_LIMIT]:
              batchWriteStderr(Msg.BATCH_CSV_TERMINATE_N_PROCESSES.format(currentISOformatTimeStamp(),
                                                                          numItems, poolProcessResults[0],
                                                                          PROCESS_PLURAL_SINGULAR[poolProcessResults[0] == 1]))
              pool.terminate()
              break
            waitRemaining = GC.Values[GC.PROCESS_WAIT_LIMIT] - delta
      pool.close()
    else:
      handleControlC('SIG')
  except KeyboardInterrupt:
    handleControlC('KBI')
  pool.join()
  batchWriteStderr(Msg.BATCH_CSV_PROCESSING_COMPLETE.format(currentISOformatTimeStamp(), numItems))
  if mpQueueCSVFile:
    terminateCSVFileQueueHandler(mpQueueCSVFile, mpQueueHandlerCSVFile)
  if mpQueueStdout:
    mpQueueStdout.put((0, GM.REDIRECT_QUEUE_END, [GM.Globals[GM.SYSEXITRC], GM.Globals[GM.STDOUT][GM.REDIRECT_MULTI_FD].getvalue()]))
    GM.Globals[GM.STDOUT][GM.REDIRECT_MULTI_FD].close()
    GM.Globals[GM.STDOUT][GM.REDIRECT_MULTI_FD] = None
    terminateStdQueueHandler(mpQueueStdout, mpQueueHandlerStdout)
  if mpQueueStderr and mpQueueStderr is not mpQueueStdout:
    mpQueueStderr.put((0, GM.REDIRECT_QUEUE_END, [GM.Globals[GM.SYSEXITRC], GM.Globals[GM.STDERR][GM.REDIRECT_MULTI_FD].getvalue()]))
    GM.Globals[GM.STDERR][GM.REDIRECT_MULTI_FD].close()
    GM.Globals[GM.STDERR][GM.REDIRECT_MULTI_FD] = None
    terminateStdQueueHandler(mpQueueStderr, mpQueueHandlerStderr)

def threadBatchWorker(showCmds=False, numItems=0):
  while True:
    pid, item, logCmd = GM.Globals[GM.TBATCH_QUEUE].get()
    try:
      sysRC = subprocess.call(item, stdout=GM.Globals[GM.STDOUT].get(GM.REDIRECT_MULTI_FD, sys.stdout),
                              stderr=GM.Globals[GM.STDERR].get(GM.REDIRECT_MULTI_FD, sys.stderr))
      if showCmds:
        batchWriteStderr(f'{currentISOformatTimeStamp()},{pid}/{numItems},End,{sysRC},{logCmd}\n')
      if GM.Globals[GM.MULTIPROCESS_EXIT_CONDITION] is not None and checkChildProcessRC(sysRC):
        GM.Globals[GM.MULTIPROCESS_EXIT_PROCESSING] = True
    except Exception as e:
      batchWriteStderr(f'{currentISOformatTimeStamp()},{pid}/{numItems},Error,{str(e)},{logCmd}\n')
    GM.Globals[GM.TBATCH_QUEUE].task_done()

BATCH_COMMANDS = [Cmd.GAM_CMD, Cmd.COMMIT_BATCH_CMD, Cmd.PRINT_CMD, Cmd.SLEEP_CMD, Cmd.DATETIME_CMD, Cmd.SET_CMD, Cmd.CLEAR_CMD]
TBATCH_COMMANDS = [Cmd.GAM_CMD, Cmd.COMMIT_BATCH_CMD, Cmd.EXECUTE_CMD, Cmd.PRINT_CMD, Cmd.SLEEP_CMD, Cmd.DATETIME_CMD, Cmd.SET_CMD, Cmd.CLEAR_CMD]

def ThreadBatchGAMCommands(items, showCmds):
  if not items:
    return
  pythonCmd = [sys.executable]
  if not getattr(sys, 'frozen', False): # we're not frozen
    pythonCmd.append(os.path.realpath(Cmd.Argument(0)))
  GM.Globals[GM.NUM_BATCH_ITEMS] = numItems = len(items)
  numWorkerThreads = min(numItems, GC.Values[GC.NUM_TBATCH_THREADS])
# GM.Globals[GM.TBATCH_QUEUE].put() gets blocked when trying to create more items than there are workers
  GM.Globals[GM.TBATCH_QUEUE] = queue.Queue(maxsize=numWorkerThreads)
  batchWriteStderr(Msg.USING_N_PROCESSES.format(currentISOformatTimeStamp(),
                                                numItems, numWorkerThreads,
                                                THREAD_PLURAL_SINGULAR[numWorkerThreads == 1]))
  for _ in range(numWorkerThreads):
    t = threading.Thread(target=threadBatchWorker, kwargs={'showCmds': showCmds, 'numItems': numItems})
    t.daemon = True
    t.start()
  pid = 0
  numThreadsInUse = 0
  for item in items:
    if GM.Globals[GM.MULTIPROCESS_EXIT_PROCESSING]:
      break
    if item[0] == Cmd.COMMIT_BATCH_CMD:
      batchWriteStderr(Msg.COMMIT_BATCH_WAIT_N_PROCESSES.format(currentISOformatTimeStamp(),
                                                                numItems, numThreadsInUse,
                                                                THREAD_PLURAL_SINGULAR[numThreadsInUse == 1]))
      GM.Globals[GM.TBATCH_QUEUE].join()
      batchWriteStderr(Msg.COMMIT_BATCH_COMPLETE.format(currentISOformatTimeStamp(), numItems, Msg.THREADS))
      numThreadsInUse = 0
      if len(item) > 1:
        readStdin(f'{currentISOformatTimeStamp()},0/{numItems},{Cmd.QuotedArgumentList(item[1:])}')
      continue
    if item[0] == Cmd.PRINT_CMD:
      batchWriteStderr(f'{currentISOformatTimeStamp()},0/{numItems},{Cmd.QuotedArgumentList(item[1:])}\n')
      continue
    if item[0] == Cmd.SLEEP_CMD:
      batchWriteStderr(f'{currentISOformatTimeStamp()},0/{numItems},Sleeping {item[1]} seconds\n')
      time.sleep(int(item[1]))
      continue
    pid += 1
    if not showCmds and ((pid % 100 == 0) or (pid == numItems)):
      batchWriteStderr(Msg.PROCESSING_ITEM_N_OF_M.format(currentISOformatTimeStamp(), pid, numItems))
    if showCmds:
      logCmd = Cmd.QuotedArgumentList(item)
      batchWriteStderr(f'{currentISOformatTimeStamp()},{pid}/{numItems},Start,{Cmd.QuotedArgumentList(item)}\n')
    else:
      logCmd = ''
    if item[0] == Cmd.GAM_CMD:
      GM.Globals[GM.TBATCH_QUEUE].put((pid, pythonCmd+item[1:], logCmd))
    else:
      GM.Globals[GM.TBATCH_QUEUE].put((pid, item[1:], logCmd))
    numThreadsInUse += 1
  GM.Globals[GM.TBATCH_QUEUE].join()
  if showCmds:
    batchWriteStderr(f'{currentISOformatTimeStamp()},0/{numItems},Complete\n')

def _getShowCommands():
  if checkArgumentPresent('showcmds'):
    return getBoolean()
  return GC.Values[GC.SHOW_COMMANDS]

def _getSkipRows():
  if checkArgumentPresent('skiprows'):
    return getInteger(minVal=0)
#  return GC.Values[GC.CSV_INPUT_ROW_SKIP]
  return 0

def _getMaxRows():
  if checkArgumentPresent('maxrows'):
    return getInteger(minVal=0)
  return GC.Values[GC.CSV_INPUT_ROW_LIMIT]

# gam batch <BatchContent> [showcmds [<Boolean>]]
def doBatch(threadBatch=False):
  filename = getString(Cmd.OB_FILE_NAME)
  if (filename == '-') and (GC.Values[GC.DEBUG_LEVEL] > 0):
    Cmd.Backup()
    usageErrorExit(Msg.BATCH_CSV_LOOP_DASH_DEBUG_INCOMPATIBLE.format(Cmd.BATCH_CMD))
  filenameLower = filename.lower()
  if filenameLower not in {'gdoc', 'gcsdoc'}:
    encoding = getCharSet()
    filename = setFilePath(filename, GC.INPUT_DIR)
    f = openFile(filename, encoding=encoding, stripUTFBOM=True)
  elif filenameLower == 'gdoc':
    f = getGDocData(filenameLower)
    getCharSet()
  else: #filenameLower == 'gcsdoc':
    f = getStorageFileData(filenameLower)
    getCharSet()
  showCmds = _getShowCommands()
  checkForExtraneousArguments()
  validCommands = BATCH_COMMANDS if not threadBatch else TBATCH_COMMANDS
  kwValues = {}
  items = []
  errors = 0
  try:
    for line in f:
      if line.startswith('#'):
        continue
      if kwValues:
        for kw, value in kwValues.items():
          line = line.replace(f'%{kw}%', value)
      try:
        argv = shlex.split(line)
      except ValueError as e:
        writeStderr(f'Command: >>>{line.strip()}<<<\n')
        writeStderr(f'{ERROR_PREFIX}{str(e)}\n')
        errors += 1
        continue
      if argv:
        cmd = argv[0].strip().lower()
        if cmd == Cmd.DATETIME_CMD:
          if len(argv) == 2:
            kwValues['datetime'] = todaysTime().strftime(argv[1])
          else:
            writeStderr(f'Command: >>>{Cmd.QuotedArgumentList([argv[0]])}<<< {Cmd.QuotedArgumentList(argv[1:])}\n')
            writeStderr(f'{ERROR_PREFIX}{Cmd.ARGUMENT_ERROR_NAMES[Cmd.ARGUMENT_INVALID][1]}: {Msg.EXPECTED} <{Cmd.DATETIME_CMD} DateTimeFormat>)>\n')
            errors += 1
          continue
        if cmd == Cmd.SET_CMD:
          if len(argv) == 3:
            kwValues[argv[1]] = argv[2]
          else:
            writeStderr(f'Command: >>>{Cmd.QuotedArgumentList([argv[0]])}<<< {Cmd.QuotedArgumentList(argv[1:])}\n')
            writeStderr(f'{ERROR_PREFIX}{Cmd.ARGUMENT_ERROR_NAMES[Cmd.ARGUMENT_INVALID][1]}: {Msg.EXPECTED} <{Cmd.SET_CMD} keyword value>)>\n')
            errors += 1
          continue
        if cmd == Cmd.CLEAR_CMD:
          if len(argv) == 2:
            kwValues.pop(argv[1], None)
          else:
            writeStderr(f'Command: >>>{Cmd.QuotedArgumentList([argv[0]])}<<< {Cmd.QuotedArgumentList(argv[1:])}\n')
            writeStderr(f'{ERROR_PREFIX}{Cmd.ARGUMENT_ERROR_NAMES[Cmd.ARGUMENT_INVALID][1]}: {Msg.EXPECTED} <{Cmd.CLEAR_CMD} keyword>)>\n')
            errors += 1
          continue
        if cmd == Cmd.SLEEP_CMD:
          if len(argv) != 2 or not argv[1].isdigit():
            writeStderr(f'Command: >>>{Cmd.QuotedArgumentList([argv[0]])}<<< {Cmd.QuotedArgumentList(argv[1:])}\n')
            writeStderr(f'{ERROR_PREFIX}{Cmd.ARGUMENT_ERROR_NAMES[Cmd.ARGUMENT_INVALID][1]}: {Msg.EXPECTED} <{Cmd.SLEEP_CMD} integer>)>\n')
            errors += 1
            continue
        if (not cmd) or ((len(argv) == 1) and (cmd not in [Cmd.COMMIT_BATCH_CMD, Cmd.PRINT_CMD])):
          continue
        if cmd in validCommands:
          items.append(argv)
        else:
          writeStderr(f'Command: >>>{Cmd.QuotedArgumentList([argv[0]])}<<< {Cmd.QuotedArgumentList(argv[1:])}\n')
          writeStderr(f'{ERROR_PREFIX}{Cmd.ARGUMENT_ERROR_NAMES[Cmd.ARGUMENT_INVALID][1]}: {Msg.EXPECTED} <{formatChoiceList(validCommands)}>\n')
          errors += 1
  except IOError as e:
    systemErrorExit(FILE_ERROR_RC, fileErrorMessage(filename, e))
  closeFile(f)
  if errors == 0:
    if not threadBatch:
      MultiprocessGAMCommands(items, showCmds)
    else:
      ThreadBatchGAMCommands(items, showCmds)
  else:
    writeStderr(Msg.BATCH_NOT_PROCESSED_ERRORS.format(ERROR_PREFIX, filename, errors, ERROR_PLURAL_SINGULAR[errors == 1]))
    setSysExitRC(USAGE_ERROR_RC)

# gam tbatch <BatchContent> [showcmds [<Boolean>]]
def doThreadBatch():
  adjustRedirectedSTDFilesIfNotMultiprocessing()
  doBatch(True)

def doAutoBatch(entityType, entityList, CL_command):
  remaining = Cmd.Remaining()
  items = []
  initial_argv = [Cmd.GAM_CMD]
  if GM.Globals[GM.SECTION] and not GM.Globals[GM.GAM_CFG_SECTION]:
    initial_argv.extend([Cmd.SELECT_CMD, GM.Globals[GM.SECTION]])
  for entity in entityList:
    items.append(initial_argv+[entityType, entity, CL_command]+remaining)
  MultiprocessGAMCommands(items, GC.Values[GC.SHOW_COMMANDS])

# Process command line arguments, find substitutions
# An argument containing instances of ~~xxx~!~pattern~!~replacement~~ has ~~...~~ replaced by re.sub(pattern, replacement, value of field xxx from the CSV file)
# For example, ~~primaryEmail~!~^(.+)@(.+)$~!~\1 AT \2~~ would replace foo@bar.com (from the primaryEmail column) with foo AT bar.com
# An argument containing instances of ~~xxx~~ has xxx replaced by the value of field xxx from the CSV file
# An argument containing exactly ~xxx is replaced by the value of field xxx from the CSV file
# Otherwise, the argument is preserved as is

SUB_PATTERN = re.compile(r'~~(.+?)~~')
RE_PATTERN = re.compile(r'~~(.+?)~!~(.+?)~!~(.+?)~~')
SUB_TYPE = 'sub'
RE_TYPE = 're'

# SubFields is a dictionary; the key is the argument number, the value is a list of tuples that mark
# the substition (type, fieldname, start, end). Type is 'sub' for simple substitution, 're' for regex substitution.
# Example: update user '~User' address type work unstructured '~~Street~~, ~~City~~, ~~State~~ ~~ZIP~~' primary
# {2: [('sub', 'User', 0, 5)], 7: [('sub', 'Street', 0, 10), ('sub', 'City', 12, 20), ('sub', 'State', 22, 31), ('sub', 'ZIP', 32, 39)]}
def getSubFields(initial_argv, fieldNames):
  subFields = {}
  GAM_argv = initial_argv[:]
  GAM_argvI = len(GAM_argv)
  while Cmd.ArgumentsRemaining():
    myarg = Cmd.Current()
    if not myarg:
      GAM_argv.append(myarg)
    elif SUB_PATTERN.search(myarg):
      pos = 0
      subFields.setdefault(GAM_argvI, [])
      while True:
        submatch = SUB_PATTERN.search(myarg, pos)
        if not submatch:
          break
        rematch = RE_PATTERN.match(submatch.group(0))
        if not rematch:
          fieldName = submatch.group(1)
          if fieldName not in fieldNames:
            csvFieldErrorExit(fieldName, fieldNames)
          subFields[GAM_argvI].append((SUB_TYPE, fieldName, submatch.start(), submatch.end()))
        else:
          fieldName = rematch.group(1)
          if fieldName not in fieldNames:
            csvFieldErrorExit(fieldName, fieldNames)
          try:
            re.compile(rematch.group(2))
            subFields[GAM_argvI].append((RE_TYPE, fieldName, submatch.start(), submatch.end(), rematch.group(2), rematch.group(3)))
          except re.error as e:
            usageErrorExit(f'{Cmd.OB_RE_PATTERN} {Msg.ERROR}: {e}')
        pos = submatch.end()
      GAM_argv.append(myarg)
    elif myarg[0] == '~':
      fieldName = myarg[1:]
      if fieldName in fieldNames:
        subFields[GAM_argvI] = [(SUB_TYPE, fieldName, 0, len(myarg))]
        GAM_argv.append(myarg)
      else:
        csvFieldErrorExit(fieldName, fieldNames)
    else:
      GAM_argv.append(myarg)
    GAM_argvI += 1
    Cmd.Advance()
  return(GAM_argv, subFields)

def processSubFields(GAM_argv, row, subFields):
  argv = GAM_argv[:]
  for GAM_argvI, fields in subFields.items():
    oargv = argv[GAM_argvI][:]
    argv[GAM_argvI] = ''
    pos = 0
    for field in fields:
      argv[GAM_argvI] += oargv[pos:field[2]]
      if field[0] == SUB_TYPE:
        if row[field[1]]:
          argv[GAM_argvI] += row[field[1]]
      else:
        if row[field[1]]:
          argv[GAM_argvI] += re.sub(field[4], field[5], row[field[1]])
      pos = field[3]
    argv[GAM_argvI] += oargv[pos:]
  return argv

# gam csv <CSVLoopContent> [warnifnodata]
#	[columndelimiter <Character>] [quotechar <Character>] [fields <FieldNameList>]
#	(matchfield|skipfield <FieldName> <RESearchPattern>)* [showcmds [<Boolean>]]
#	[skiprows <Integer>] [maxrows <Integer>]
#	gam <GAM argument list>
def doCSV(testMode=False):
  filename = getString(Cmd.OB_FILE_NAME)
  if (filename == '-') and (GC.Values[GC.DEBUG_LEVEL] > 0):
    Cmd.Backup()
    usageErrorExit(Msg.BATCH_CSV_LOOP_DASH_DEBUG_INCOMPATIBLE.format(Cmd.CSV_CMD))
  f, csvFile, fieldnames = openCSVFileReader(filename)
  matchFields, skipFields = getMatchSkipFields(fieldnames)
  showCmds = _getShowCommands()
  skipRows = _getSkipRows()
  maxRows = _getMaxRows()
  checkArgumentPresent(Cmd.GAM_CMD, required=True)
  if not Cmd.ArgumentsRemaining():
    missingArgumentExit(Cmd.OB_GAM_ARGUMENT_LIST)
  initial_argv = [Cmd.GAM_CMD]
  if GM.Globals[GM.SECTION] and not GM.Globals[GM.GAM_CFG_SECTION] and not Cmd.PeekArgumentPresent(Cmd.SELECT_CMD):
    initial_argv.extend([Cmd.SELECT_CMD, GM.Globals[GM.SECTION]])
  GAM_argv, subFields = getSubFields(initial_argv, fieldnames)
  if GC.Values[GC.CSV_INPUT_ROW_FILTER] or GC.Values[GC.CSV_INPUT_ROW_DROP_FILTER]:
    CheckInputRowFilterHeaders(fieldnames, GC.Values[GC.CSV_INPUT_ROW_FILTER], GC.Values[GC.CSV_INPUT_ROW_DROP_FILTER])
  items = []
  i = 0
  for row in csvFile:
    if checkMatchSkipFields(row, fieldnames, matchFields, skipFields):
      i += 1
      if skipRows:
        if i <= skipRows:
          continue
        i = 1
        skipRows = 0
      items.append(processSubFields(GAM_argv, row, subFields))
      if maxRows and i >= maxRows:
        break
  closeFile(f)
  if not testMode:
    MultiprocessGAMCommands(items, showCmds)
  else:
    numItems = min(len(items), 10)
    writeStdout(Msg.CSV_FILE_HEADERS.format(filename))
    Ind.Increment()
    for field in fieldnames:
      writeStdout(f'{Ind.Spaces()}{field}\n')
    Ind.Decrement()
    writeStdout(Msg.CSV_SAMPLE_COMMANDS.format(numItems, GAM))
    Ind.Increment()
    for i in range(numItems):
      writeStdout(f'{Ind.Spaces()}{Cmd.QuotedArgumentList(items[i])}\n')
    Ind.Decrement()

def doCSVTest():
  doCSV(testMode=True)

# gam loop <CSVLoopContent> [warnifnodata]
#	[columndelimiter <Character>] [quotechar <Character>] [fields <FieldNameList>]
#	(matchfield|skipfield <FieldName> <RESearchPattern>)* [showcmds [<Boolean>]]
#	[skiprows <Integer>] [maxrows <Integer>]
#	gam <GAM argument list>
def doLoop(loopCmd):
  from gam import ProcessGAMCommand
  filename = getString(Cmd.OB_FILE_NAME)
  if (filename == '-') and (GC.Values[GC.DEBUG_LEVEL] > 0):
    Cmd.Backup()
    usageErrorExit(Msg.BATCH_CSV_LOOP_DASH_DEBUG_INCOMPATIBLE.format(Cmd.LOOP_CMD))
  f, csvFile, fieldnames = openCSVFileReader(filename)
  matchFields, skipFields = getMatchSkipFields(fieldnames)
  showCmds = _getShowCommands()
  skipRows = _getSkipRows()
  maxRows = _getMaxRows()
  checkArgumentPresent(Cmd.GAM_CMD, required=True)
  if not Cmd.ArgumentsRemaining():
    missingArgumentExit(Cmd.OB_GAM_ARGUMENT_LIST)
  if GC.Values[GC.CSV_INPUT_ROW_FILTER] or GC.Values[GC.CSV_INPUT_ROW_DROP_FILTER]:
    CheckInputRowFilterHeaders(fieldnames, GC.Values[GC.CSV_INPUT_ROW_FILTER], GC.Values[GC.CSV_INPUT_ROW_DROP_FILTER])
  choice = Cmd.Current().strip().lower()
  if choice == Cmd.LOOP_CMD:
    usageErrorExit(Msg.NESTED_LOOP_CMD_NOT_ALLOWED)
# gam loop ... gam redirect|select|config ... process gam.cfg on each iteration
# gam redirect|select|config ... loop ... gam redirect|select|config ... process gam.cfg on each iteration
# gam loop ... gam !redirect|select|config ... no further processing of gam.cfg
# gam redirect|select|config ... loop ... gam !redirect|select|config ... no further processing of gam.cfg
  processGamCfg = choice in Cmd.GAM_META_COMMANDS
  GAM_argv, subFields = getSubFields([Cmd.GAM_CMD], fieldnames)
  multi = GM.Globals[GM.CSVFILE][GM.REDIRECT_MULTIPROCESS]
  if multi:
    mpManager = multiprocessing.Manager()
    mpQueue, mpQueueHandler = initializeCSVFileQueueHandler(mpManager, None, None)
  else:
    mpQueue = None
  GM.Globals[GM.CSVFILE][GM.REDIRECT_QUEUE] = mpQueue
# Set up command logging at top level only
  if GM.Globals[GM.CMDLOG_LOGGER]:
    LoopGlobals = GM.Globals
  else:
    LoopGlobals = {GM.CMDLOG_LOGGER: None, GM.CMDLOG_HANDLER: None}
    if (GM.Globals[GM.PID] > 0) and GC.Values[GC.CMDLOG]:
      openGAMCommandLog(LoopGlobals, 'looplog')
  if LoopGlobals[GM.CMDLOG_LOGGER]:
    writeGAMCommandLog(LoopGlobals, loopCmd, '*')
  if not showCmds:
    i = 0
    for row in csvFile:
      if checkMatchSkipFields(row, fieldnames, matchFields, skipFields):
        i += 1
        if skipRows:
          if i <= skipRows:
            continue
          i = 1
          skipRows = 0
        item = processSubFields(GAM_argv, row, subFields)
        logCmd = Cmd.QuotedArgumentList(item)
        if i % 100 == 0:
          batchWriteStderr(Msg.PROCESSING_ITEM_N.format(currentISOformatTimeStamp(), i))
        sysRC = ProcessGAMCommand(item, processGamCfg=processGamCfg, inLoop=True)
        if (GM.Globals[GM.PID] > 0) and LoopGlobals[GM.CMDLOG_LOGGER]:
          writeGAMCommandLog(LoopGlobals, logCmd, sysRC)
        if (sysRC > 0) and (GM.Globals[GM.SYSEXITRC] <= HARD_ERROR_RC):
          break
        if maxRows and i >= maxRows:
          break
    closeFile(f)
  else:
    items = []
    i = 0
    for row in csvFile:
      if checkMatchSkipFields(row, fieldnames, matchFields, skipFields):
        i += 1
        if skipRows:
          if i <= skipRows:
            continue
          i = 1
          skipRows = 0
        items.append(processSubFields(GAM_argv, row, subFields))
        if maxRows and i >= maxRows:
          break
    closeFile(f)
    numItems = len(items)
    pid = 0
    for item in items:
      pid += 1
      logCmd = Cmd.QuotedArgumentList(item)
      batchWriteStderr(f'{currentISOformatTimeStamp()},{pid}/{numItems},Start,0,{logCmd}\n')
      sysRC = ProcessGAMCommand(item, processGamCfg=processGamCfg, inLoop=True)
      batchWriteStderr(f'{currentISOformatTimeStamp()},{pid}/{numItems},End,{sysRC},{logCmd}\n')
      if (GM.Globals[GM.PID] > 0) and LoopGlobals[GM.CMDLOG_LOGGER]:
        writeGAMCommandLog(LoopGlobals, logCmd, sysRC)
      if (sysRC > 0) and (GM.Globals[GM.SYSEXITRC] <= HARD_ERROR_RC):
        break
  if (GM.Globals[GM.PID] > 0) and LoopGlobals[GM.CMDLOG_LOGGER]:
    closeGAMCommandLog(LoopGlobals)
  if multi:
    terminateCSVFileQueueHandler(mpQueue, mpQueueHandler)

def _doList(entityList, entityType):
  buildGAPIObject(API.DIRECTORY)
  if GM.Globals[GM.CSV_DATA_DICT]:
    keyField = GM.Globals[GM.CSV_KEY_FIELD]
    dataField = GM.Globals[GM.CSV_DATA_FIELD]
  else:
    keyField = 'Entity'
    dataField = 'Data'
  csvPF = CSVPrintFile(keyField)
  if checkArgumentPresent('todrive'):
    csvPF.GetTodriveParameters()
  if entityList is None:
    entityList = getEntityList(Cmd.OB_ENTITY)
  showData = checkArgumentPresent('data')
  if showData:
    if not entityType:
      itemType, itemList = getEntityToModify(crosAllowed=True)
    else:
      itemType = None
      itemList = getEntityList(Cmd.OB_ENTITY)
    entityItemLists = itemList if isinstance(itemList, dict) else None
    csvPF.AddTitle(dataField)
  else:
    entityItemLists = None
  dataDelimiter = getDelimiter()
  checkForExtraneousArguments()
  _, _, entityList = getEntityArgument(entityList)
  for entity in entityList:
    entityEmail = normalizeEmailAddressOrUID(entity)
    if showData:
      if entityItemLists:
        if entity not in entityItemLists:
          csvPF.WriteRow({keyField: entityEmail})
          continue
        itemList = entityItemLists[entity]
        if itemType == Cmd.ENTITY_USERS:
          for i, item in enumerate(itemList):
            itemList[i] = normalizeEmailAddressOrUID(item)
      if dataDelimiter:
        csvPF.WriteRow({keyField: entityEmail, dataField: dataDelimiter.join(itemList)})
      else:
        for item in itemList:
          csvPF.WriteRow({keyField: entityEmail, dataField: item})
    else:
      csvPF.WriteRow({keyField: entityEmail})
  csvPF.writeCSVfile('Entity')

# gam list [todrive <ToDriveAttribute>*] <EntityList> [data <CrOSTypeEntity>|<UserTypeEntity> [delimiter <Character>]]
def doListType():
  _doList(None, None)

# gam <CrOSTypeEntity> list [todrive <ToDriveAttribute>*] [data <EntityList> [delimiter <Character>]]
def doListCrOS(entityList):
  _doList(entityList, Cmd.ENTITY_CROS)

# gam <UserTypeEntity> list [todrive <ToDriveAttribute>*] [data <EntityList> [delimiter <Character>]]
def doListUser(entityList):
  _doList(entityList, Cmd.ENTITY_USERS)

def _showCount(entityList, entityType):
  buildGAPIObject(API.DIRECTORY)
  checkForExtraneousArguments()
  _, count, entityList = getEntityArgument(entityList)
  actionPerformedNumItems(count, entityType)

# gam <CrOSTypeEntity> show count
def showCountCrOS(entityList):
  _showCount(entityList, Ent.CHROME_DEVICE)

# gam <UserTypeEntity> show count
def showCountUser(entityList):
  _showCount(entityList, Ent.USER)
