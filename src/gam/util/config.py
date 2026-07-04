"""GAM configuration — SetGlobalVariables.

Reads gam.cfg and initializes all global runtime state.
"""

import collections
import configparser
import codecs
import datetime
import http.client
import json
import locale
import os
import re
import sys
import time

import httplib2
import arrow

from gam.var import Act, Cmd, Ent, Ind
from gamlib import api as API
from gamlib import settings as GC
from gam.util.fileio import setFilePath, readFile, writeFile, openFile
from gamlib import state as GM
from gamlib import msgs as Msg
from gamlib import skus as SKU

from util.args import getRowFilterDateOrDeltaFromNow
from util.args import getRowFilterTimeOrDeltaFromNow
from util.args import integerLimits
from util.args import LOCALE_CODES_MAP
from util.args import LANGUAGE_CODES_MAP
from util.args import TIMEZONE_FORMAT_REQUIRED
from util.args import (
    checkArgumentPresent, getArgument, getBoolean, getCharacter, getChoice,
    getFloat, getInteger, getLanguageCode, getREPattern, getString,
    shlexSplitList, shlexSplitListStatus,
    FALSE, FALSE_VALUES, TRUE, TRUE_FALSE, TRUE_VALUES, UTF8,
)
from util.csv_pf import CSVPrintFile
from util.display import printKeyValueList, printLine
from util.output import redactable_debug_print
from util.entity import getEntitiesFromCSVFile
from util.entity import getEntitiesFromFile
from util.errors import formatChoiceList, usageErrorExit, USAGE_ERROR_RC
from util.fileio import (
    initAPICallsRateCheck, openGAMCommandLog, StringIOobject,
    deleteFile, fileErrorMessage, openFile, readFile, setFilePath, writeFile,
    FILE_ERROR_RC,
)
from util.output import (
    ERROR_PREFIX, WARNING, WARNING_PREFIX,
    formatKeyValueList, printErrorMessage, stderrErrorMsg, systemErrorExit,
    writeStderr,
)
from gam.constants import (
    CONFIG_ERROR_RC, DEFAULT_FILE_APPEND_MODE, DEFAULT_FILE_READ_MODE,
    DEFAULT_FILE_WRITE_MODE, EV_GAMCFGDIR, EV_GAMCFGSECTION, EV_OLDGAMPATH,
    FN_GAM_CFG, GAM,
)


def SetGlobalVariables():


  def _stringInQuotes(value):
    return (len(value) > 1) and (((value.startswith('"') and value.endswith('"'))) or ((value.startswith("'") and value.endswith("'"))))

  def _stripStringQuotes(value):
    if _stringInQuotes(value):
      return value[1:-1]
    return value

  def _quoteStringIfLeadingTrailingBlanks(value):
    if not value:
      return "''"
    if _stringInQuotes(value):
      return value
    if (value[0] != ' ') and (value[-1] != ' '):
      return value
    return f"'{value}'"

  def _getDefault(itemName, itemEntry, oldGamPath):
    if GC.VAR_SIGFILE in itemEntry:
      GC.Defaults[itemName] = itemEntry[GC.VAR_SFFT][os.path.isfile(os.path.join(oldGamPath, itemEntry[GC.VAR_SIGFILE]))]
    elif GC.VAR_ENVVAR in itemEntry:
      value = os.environ.get(itemEntry[GC.VAR_ENVVAR], GC.Defaults[itemName])
      if itemEntry[GC.VAR_TYPE] in [GC.TYPE_INTEGER, GC.TYPE_FLOAT]:
        try:
          number = int(value) if itemEntry[GC.VAR_TYPE] == GC.TYPE_INTEGER else float(value)
          minVal, maxVal = itemEntry[GC.VAR_LIMITS]
          if (minVal is not None) and (number < minVal):
            number = minVal
          elif (maxVal is not None) and (number > maxVal):
            number = maxVal
        except ValueError:
          number = GC.Defaults[itemName]
        value = str(number)
      elif itemEntry[GC.VAR_TYPE] == GC.TYPE_STRING:
        value = _quoteStringIfLeadingTrailingBlanks(value)
      GC.Defaults[itemName] = value

  def _selectSection():
    value = getString(Cmd.OB_SECTION_NAME, minLen=0)
    if (not value) or (value.upper() == configparser.DEFAULTSECT):
      return configparser.DEFAULTSECT
    if GM.Globals[GM.PARSER].has_section(value):
      return value
    Cmd.Backup()
    usageErrorExit(formatKeyValueList('', [Ent.Singular(Ent.SECTION), value, Msg.NOT_FOUND], ''))

  def _showSections():
    printKeyValueList([Ent.Singular(Ent.CONFIG_FILE), GM.Globals[GM.GAM_CFG_FILE]])
    Ind.Increment()
    for section in [configparser.DEFAULTSECT]+sorted(GM.Globals[GM.PARSER].sections()):
      printKeyValueList([f'{section}{" *" if section == sectionName else ""}'])
    Ind.Decrement()

  def _checkMakeDir(itemName):
    if not os.path.isdir(GC.Defaults[itemName]):
      try:
        os.makedirs(GC.Defaults[itemName])
        printKeyValueList([Act.PerformedName(Act.CREATE), GC.Defaults[itemName]])
      except OSError as e:
        if not os.path.isdir(GC.Defaults[itemName]):
          systemErrorExit(FILE_ERROR_RC, e)

  def _copyCfgFile(srcFile, targetDir, oldGamPath):
    if (not srcFile) or os.path.isabs(srcFile):
      return
    dstFile = os.path.join(GC.Defaults[targetDir], srcFile)
    if os.path.isfile(dstFile):
      return
    srcFile = os.path.join(oldGamPath, srcFile)
    if not os.path.isfile(srcFile):
      return
    data = readFile(srcFile, continueOnError=True, displayError=False)
    if (data is not None) and writeFile(dstFile, data, continueOnError=True):
      printKeyValueList([Act.PerformedName(Act.COPY), srcFile, Msg.TO, dstFile])

  def _printValueError(sectionName, itemName, value, errMessage, sysRC=CONFIG_ERROR_RC):
    kvlMsg = formatKeyValueList('',
                                [Ent.Singular(Ent.CONFIG_FILE), GM.Globals[GM.GAM_CFG_FILE],
                                 Ent.Singular(Ent.SECTION), sectionName,
                                 Ent.Singular(Ent.ITEM), itemName,
                                 Ent.Singular(Ent.VALUE), value,
                                 errMessage],
                                '')
    if sysRC != 0:
      status['errors'] = True
      printErrorMessage(sysRC, kvlMsg)
    else:
      writeStderr(formatKeyValueList(Ind.Spaces(), [WARNING, kvlMsg], '\n'))

  def _getCfgBoolean(sectionName, itemName):
    value = GM.Globals[GM.PARSER].get(sectionName, itemName).lower()
    if value in TRUE_VALUES:
      return True
    if value in FALSE_VALUES:
      return False
    _printValueError(sectionName, itemName, value, f'{Msg.EXPECTED}: {formatChoiceList(TRUE_FALSE)}')
    return False

  def _getCfgCharacter(sectionName, itemName):
    value = codecs.escape_decode(bytes(_stripStringQuotes(GM.Globals[GM.PARSER].get(sectionName, itemName)), UTF8))[0].decode(UTF8)
    if not value and (itemName == 'csv_output_field_delimiter'):
      return ' '
    if not value and (itemName in {'csv_input_escape_char', 'csv_output_escape_char'}):
      return None
    if len(value) == 1:
      return value
    _printValueError(sectionName, itemName, f'"{value}"', f'{Msg.EXPECTED}: {integerLimits(1, 1, Msg.STRING_LENGTH)}')
    return ''

  def _getCfgChoice(sectionName, itemName):
    value = _stripStringQuotes(GM.Globals[GM.PARSER].get(sectionName, itemName)).lower()
    choices = GC.VAR_INFO[itemName][GC.VAR_CHOICES]
    if value in choices:
      return choices[value]
    _printValueError(sectionName, itemName, f'"{value}"', f'{Msg.EXPECTED}: {",".join(choices)}')
    return ''

  def _getCfgLocale(sectionName, itemName):
    value = _stripStringQuotes(GM.Globals[GM.PARSER].get(sectionName, itemName)).lower().replace('_', '-')
    if value in LOCALE_CODES_MAP:
      return LOCALE_CODES_MAP[value]
    _printValueError(sectionName, itemName, f'"{value}"', f'{Msg.EXPECTED}: {",".join(LOCALE_CODES_MAP)}')
    return ''

  def _getCfgNumber(sectionName, itemName):
    value = GM.Globals[GM.PARSER].get(sectionName, itemName)
    minVal, maxVal = GC.VAR_INFO[itemName][GC.VAR_LIMITS]
    try:
      number = int(value) if GC.VAR_INFO[itemName][GC.VAR_TYPE] == GC.TYPE_INTEGER else float(value)
      if ((minVal is None) or (number >= minVal)) and ((maxVal is None) or (number <= maxVal)):
        return number
      if (minVal is not None) and (number < minVal):
        number = minVal
      else:
        number = maxVal
      _printValueError(sectionName, itemName, value, f'{Msg.EXPECTED}: {integerLimits(minVal, maxVal)}, {Msg.USED}: {number}', sysRC=0)
      return number
    except ValueError:
      pass
    _printValueError(sectionName, itemName, value, f'{Msg.EXPECTED}: {integerLimits(minVal, maxVal)}')
    return 0

  def _getCfgHeaderFilter(sectionName, itemName):
    value = GM.Globals[GM.PARSER].get(sectionName, itemName)
    headerFilters = []
    if not value or (len(value) == 2 and _stringInQuotes(value)):
      return headerFilters
    splitStatus, filters = shlexSplitListStatus(value)
    if splitStatus:
      for filterStr in filters:
        try:
          headerFilters.append(re.compile(filterStr, re.IGNORECASE))
        except re.error as e:
          _printValueError(sectionName, itemName, f'"{filterStr}"', f'{Msg.INVALID_RE}: {e}')
    else:
      _printValueError(sectionName, itemName, f'"{value}"', f'{Msg.INVALID_LIST}: {filters}')
    return headerFilters

  def _getCfgHeaderFilterFromForce(sectionName, itemName):
    headerFilters = []
    for filterStr in GC.Values[itemName]:
      try:
        headerFilters.append(re.compile(fr'^{filterStr}$'))
      except re.error as e:
        _printValueError(sectionName, itemName, f'"{filterStr}"', f'{Msg.INVALID_RE}: {e}')
    return headerFilters

  ROW_FILTER_ANY_ALL_PATTERN = re.compile(r'^(any:|all:)(.+)$', re.IGNORECASE)
  ROW_FILTER_COMP_PATTERN = re.compile(r'^(date|time|count|length|number)\s*([<>]=?|=|!=)(.+)$', re.IGNORECASE)
  ROW_FILTER_RANGE_PATTERN = re.compile(r'^(daterange|timerange|countrange|lengthrange|numberrange)(=|!=)(\S+)/(\S+)$', re.IGNORECASE)
  ROW_FILTER_TIMEOFDAYRANGE_PATTERN = re.compile(r'^(timeofdayrange)(=|!=)(\d\d):(\d\d)/(\d\d):(\d\d)$', re.IGNORECASE)
  ROW_FILTER_BOOL_PATTERN = re.compile(r'^(boolean):(.+)$', re.IGNORECASE)
  ROW_FILTER_TEXT_PATTERN = re.compile(r'^(text)([<>]=?|=|!=)(.*)$', re.IGNORECASE)
  ROW_FILTER_TEXTRANGE_PATTERN = re.compile(r'^(textrange)(=|!=)(.*)/(.*)$', re.IGNORECASE)
  ROW_FILTER_RE_PATTERN = re.compile(r'^(regex|regexcs|notregex|notregexcs):(.*)$', re.IGNORECASE)
  ROW_FILTER_DATA_PATTERN = re.compile(r'^(data|notdata):(list|file|csvfile) +(.+)$', re.IGNORECASE)
  REGEX_CHARS = '^$*+|$[{('

  def _getCfgRowFilter(sectionName, itemName):
    value = GM.Globals[GM.PARSER].get(sectionName, itemName)
    rowFilters = []
    if not value:
      return rowFilters
    if value.startswith('{'):
      try:
        filterDict = json.loads(value.encode('unicode-escape').decode(UTF8))
      except (IndexError, KeyError, SyntaxError, TypeError, ValueError) as e:
        _printValueError(sectionName, itemName, f'"{value}"', f'{Msg.FAILED_TO_PARSE_AS_JSON}: {str(e)}')
        return rowFilters
    else:
      filterDict = {}
      status, filterList = shlexSplitListStatus(value)
      if not status:
        _printValueError(sectionName, itemName, f'"{value}"', f'{Msg.FAILED_TO_PARSE_AS_LIST}: {str(filterList)}')
        return rowFilters
      for filterVal in filterList:
        if not filterVal:
          continue
        try:
          filterTokens = shlexSplitList(filterVal, ':')
          column = filterTokens[0]
          filterStr = ':'.join(filterTokens[1:])
        except ValueError:
          _printValueError(sectionName, itemName, f'"{filterVal}"', f'{Msg.EXPECTED}: column:filter')
          continue
        filterDict[column] = filterStr
    for column, filterStr in filterDict.items():
      for c in REGEX_CHARS:
        if c in column:
          columnPat = column
          break
      else:
        columnPat = f'^{column}$'
      try:
        columnPat = re.compile(columnPat, re.IGNORECASE)
      except re.error as e:
        _printValueError(sectionName, itemName, f'"{column}"', f'{Msg.INVALID_RE}: {e}')
        continue
      anyMatch = True
      mg = ROW_FILTER_ANY_ALL_PATTERN.match(filterStr)
      if mg:
        anyMatch = mg.group(1).lower() == 'any:'
        filterStr = mg.group(2)
      mg = ROW_FILTER_COMP_PATTERN.match(filterStr)
      if mg:
        filterType = mg.group(1).lower()
        if filterType in {'date', 'time'}:
          if filterType == 'date':
            valid, filterValue = getRowFilterDateOrDeltaFromNow(mg.group(3))
          else:
            valid, filterValue = getRowFilterTimeOrDeltaFromNow(mg.group(3))
          if valid:
            rowFilters.append((columnPat, anyMatch, filterType, mg.group(2), filterValue))
          else:
            _printValueError(sectionName, itemName, f'"{column}": "{filterStr}"', f'{Msg.EXPECTED}: {filterValue}')
        else: # filterType in {'count', 'length', 'number'}:
          if mg.group(3).isdigit():
            rowFilters.append((columnPat, anyMatch, filterType, mg.group(2), int(mg.group(3))))
          else:
            _printValueError(sectionName, itemName, f'"{column}": "{filterStr}"', f'{Msg.EXPECTED}: <Number>')
        continue
      mg = ROW_FILTER_TEXT_PATTERN.match(filterStr)
      if mg:
        filterType = mg.group(1).lower()
        rowFilters.append((columnPat, anyMatch, filterType, mg.group(2), mg.group(3)))
        continue
      mg = ROW_FILTER_TEXTRANGE_PATTERN.match(filterStr)
      if mg:
        filterType = mg.group(1).lower()
        rowFilters.append((columnPat, anyMatch, filterType, mg.group(2), mg.group(3), mg.group(4)))
        continue
      mg = ROW_FILTER_RANGE_PATTERN.match(filterStr)
      if mg:
        filterType = mg.group(1).lower()
        if filterType in {'daterange', 'timerange'}:
          if filterType == 'daterange':
            valid1, filterValue1 = getRowFilterDateOrDeltaFromNow(mg.group(3))
            valid2, filterValue2 = getRowFilterDateOrDeltaFromNow(mg.group(4))
          else:
            valid1, filterValue1 = getRowFilterTimeOrDeltaFromNow(mg.group(3))
            valid2, filterValue2 = getRowFilterTimeOrDeltaFromNow(mg.group(4))
          if valid1 and valid2:
            rowFilters.append((columnPat, anyMatch, filterType, mg.group(2), filterValue1, filterValue2))
          else:
            _printValueError(sectionName, itemName, f'"{column}": "{filterStr}"', f'{Msg.EXPECTED}: {filterValue1}/{filterValue2}')
        else: #countrange|lengthrange|numberrange
          if mg.group(3).isdigit() and mg.group(4).isdigit():
            rowFilters.append((columnPat, anyMatch, filterType, mg.group(2), int(mg.group(3)), int(mg.group(4))))
          else:
            _printValueError(sectionName, itemName, f'"{column}": "{filterStr}"', f'{Msg.EXPECTED}: <Number>/<Number>')
        continue
      mg = ROW_FILTER_TIMEOFDAYRANGE_PATTERN.match(filterStr)
      if mg:
        filterType = mg.group(1).lower()
        startHour = int(mg.group(3))
        startMinute = int(mg.group(4))
        endHour = int(mg.group(5))
        endMinute = int(mg.group(6))
        if startHour > 23 or startMinute > 59 or endHour > 23 or endMinute > 59 or \
           endHour < startHour or (endHour == startHour and endMinute < startMinute):
          Cmd.Backup()
          usageErrorExit(Msg.INVALID_TIMEOFDAY_RANGE.format(f'{startHour:02d}:{startMinute:02d}', f'{endHour:02d}:{endMinute:02d}'))
        rowFilters.append((columnPat, anyMatch, filterType, mg.group(2), f'{startHour:02d}:{startMinute:02d}', f'{endHour:02d}:{endMinute:02d}'))
        continue
      mg = ROW_FILTER_BOOL_PATTERN.match(filterStr)
      if mg:
        filterType = mg.group(1).lower()
        filterValue = mg.group(2).lower()
        if filterValue in TRUE_VALUES:
          rowFilters.append((columnPat, anyMatch, filterType, True))
        elif filterValue in FALSE_VALUES:
          rowFilters.append((columnPat, anyMatch, filterType, False))
        else:
          _printValueError(sectionName, itemName, f'"{column}": "{filterStr}"', f'{Msg.EXPECTED}: <Boolean>')
        continue
      mg = ROW_FILTER_RE_PATTERN.match(filterStr)
      if mg:
        filterType = mg.group(1).lower()
        try:
          if filterType.endswith('cs'):
            filterType = filterType[0:-2]
            flags = 0
          else:
            flags = re.IGNORECASE
          rowFilters.append((columnPat, anyMatch, filterType, re.compile(mg.group(2), flags)))
        except re.error as e:
          _printValueError(sectionName, itemName, f'"{column}": "{filterStr}"', f'{Msg.INVALID_RE}: {e}')
        continue
      mg = ROW_FILTER_DATA_PATTERN.match(filterStr)
      if mg:
        filterType = mg.group(1).lower()
        filterSubType = mg.group(2).lower()
        if filterSubType == 'list':
          rowFilters.append((columnPat, anyMatch, filterType, set(shlexSplitList(mg.group(3)))))
          continue
        Cmd.MergeArguments(shlexSplitList(mg.group(3), ' '))
        if filterSubType == 'file':
          rowFilters.append((columnPat, anyMatch, filterType, getEntitiesFromFile(False, returnSet=True)))
        else: #elif filterSubType == 'csvfile':
          rowFilters.append((columnPat, anyMatch, filterType, getEntitiesFromCSVFile(False, returnSet=True)))
        Cmd.RestoreArguments()
        continue
      _printValueError(sectionName, itemName, f'"{column}": "{filterStr}"', f'{Msg.EXPECTED}: <RowValueFilter>')
    return rowFilters

  def _getCfgSection(sectionName, itemName):
    value = _stripStringQuotes(GM.Globals[GM.PARSER].get(sectionName, itemName))
    if (not value) or (value.upper() == configparser.DEFAULTSECT):
      return configparser.DEFAULTSECT
    if GM.Globals[GM.PARSER].has_section(value):
      return value
    _printValueError(sectionName, itemName, value, Msg.NOT_FOUND)
    return configparser.DEFAULTSECT

  def _getCfgPassword(sectionName, itemName):
    value = GM.Globals[GM.PARSER].get(sectionName, itemName)
    if isinstance(value, bytes):
      return value
    value = _stripStringQuotes(value)
    if value.startswith("b'") and value.endswith("'"):
      return bytes(value[2:-1], UTF8)
    if value:
      return value
    return ''

  def _validateLicenseSKUs(sectionName, itemName, skuList):
    GM.Globals[GM.LICENSE_SKUS] = []
    for sku in skuList.split(','):
      if '/' not in sku:
        productId, sku = SKU.getProductAndSKU(sku)
        if not productId:
          _printValueError(sectionName, itemName, sku, f'{Msg.EXPECTED}: {",".join(SKU.getSortedSKUList())}')
      else:
        (productId, sku) = sku.split('/')
      if (productId, sku) not in GM.Globals[GM.LICENSE_SKUS]:
        GM.Globals[GM.LICENSE_SKUS].append((productId, sku))

  def _validateDeveloperPreviewAPIs(sectionName, itemName, apiList):
    GM.Globals[GM.DEVELOPER_PREVIEW_APIS] = set()
    validAPIs = API.getAPIsList()
    for api in apiList.split(','):
      if api in validAPIs:
        GM.Globals[GM.DEVELOPER_PREVIEW_APIS].add(api)
      else:
        _printValueError(sectionName, itemName, api, f'{Msg.EXPECTED}: {",".join(sorted(validAPIs))}')

  def _validateGCPOrgId(sectionName, itemName, gcpOrgId):
    mg = re.match(r'organizations/\d+', gcpOrgId)
    if not mg:
      _printValueError(sectionName, itemName, gcpOrgId, f'{Msg.EXPECTED}: "organizations/<Number>"')

  def _getCfgString(sectionName, itemName):
    value = _stripStringQuotes(GM.Globals[GM.PARSER].get(sectionName, itemName))
    if itemName == GC.DOMAIN:
      value = value.strip()
    minLen, maxLen = GC.VAR_INFO[itemName].get(GC.VAR_LIMITS, (None, None))
    if ((minLen is None) or (len(value) >= minLen)) and ((maxLen is None) or (len(value) <= maxLen)):
      if itemName == GC.LICENSE_SKUS and value:
        _validateLicenseSKUs(sectionName, itemName, value)
      elif itemName == GC.DEVELOPER_PREVIEW_APIS and value:
        _validateDeveloperPreviewAPIs(sectionName, itemName, value.lower())
      elif itemName == GC.GCP_ORG_ID and value:
        _validateGCPOrgId(sectionName, itemName, value)
      return value
    _printValueError(sectionName, itemName, f'"{value}"', f'{Msg.EXPECTED}: {integerLimits(minLen, maxLen, Msg.STRING_LENGTH)}')
    return ''

  def _getCfgStringList(sectionName, itemName):
    value = GM.Globals[GM.PARSER].get(sectionName, itemName)
    stringlist = []
    if not value or (len(value) == 2 and _stringInQuotes(value)):
      return stringlist
    splitStatus, stringlist = shlexSplitListStatus(value)
    if not splitStatus:
      _printValueError(sectionName, itemName, f'"{value}"', f'{Msg.INVALID_LIST}: {stringlist}')
    return stringlist

  def _getCfgTimezone(sectionName, itemName):
    value = _stripStringQuotes(GM.Globals[GM.PARSER].get(sectionName, itemName))
    if value.lower() in {'utc', 'z'}:
      GM.Globals[GM.CONVERT_TO_LOCAL_TIME] = False
      return arrow.now('utc').tzinfo
    GM.Globals[GM.CONVERT_TO_LOCAL_TIME] = True
    if value.lower() == 'local':
      return arrow.now(value).tzinfo
    try:
      return arrow.now(value).tzinfo
    except (arrow.parser.ParserError, OverflowError):
      _printValueError(sectionName, itemName, value, f'{Msg.EXPECTED}: {TIMEZONE_FORMAT_REQUIRED}')
      GM.Globals[GM.CONVERT_TO_LOCAL_TIME] = False
      return arrow.now('utc').tzinfo

  def _getCfgDirectory(sectionName, itemName):
    dirPath = os.path.expanduser(_stripStringQuotes(GM.Globals[GM.PARSER].get(sectionName, itemName)))
    if (not dirPath) and (itemName in {GC.GMAIL_CSE_INCERT_DIR, GC.GMAIL_CSE_INKEY_DIR, GC.INPUT_DIR}):
      return dirPath
    if (not dirPath) or (not os.path.isabs(dirPath) and dirPath != '.'):
      if (sectionName != configparser.DEFAULTSECT) and (GM.Globals[GM.PARSER].has_option(sectionName, itemName)):
        dirPath = os.path.join(os.path.expanduser(_stripStringQuotes(GM.Globals[GM.PARSER].get(configparser.DEFAULTSECT, itemName))), dirPath)
      if not os.path.isabs(dirPath):
        dirPath = os.path.join(GM.Globals[GM.GAM_CFG_PATH], dirPath)
    return dirPath

  def _getCfgFile(sectionName, itemName):
    value = os.path.expanduser(_stripStringQuotes(GM.Globals[GM.PARSER].get(sectionName, itemName)))
    if value and not os.path.isabs(value):
      value = os.path.expanduser(os.path.join(_getCfgDirectory(sectionName, GC.CONFIG_DIR), value))
    elif not value and itemName == GC.CACERTS_PEM:
      value = os.path.join(GM.Globals[GM.GAM_PATH], GC.FN_CACERTS_PEM)
    return value

  def _readGamCfgFile(config, fileName):
    try:
      with open(fileName, DEFAULT_FILE_READ_MODE, encoding=GM.Globals[GM.SYS_ENCODING]) as f:
        config.read_file(f)
    except (configparser.DuplicateOptionError, configparser.DuplicateSectionError,
            configparser.MissingSectionHeaderError, configparser.ParsingError) as e:
      systemErrorExit(CONFIG_ERROR_RC, formatKeyValueList('',
                                                          [Ent.Singular(Ent.CONFIG_FILE), fileName,
                                                           Msg.INVALID, str(e)],
                                                          ''))
    except IOError as e:
      systemErrorExit(FILE_ERROR_RC, fileErrorMessage(fileName, e, Ent.CONFIG_FILE))

  def _writeGamCfgFile(config, fileName, action):
    GM.Globals[GM.SECTION] = None # No need to save section for inner gams
    try:
      with open(fileName, DEFAULT_FILE_WRITE_MODE, encoding=GM.Globals[GM.SYS_ENCODING]) as f:
        config.write(f)
      printKeyValueList([Ent.Singular(Ent.CONFIG_FILE), fileName, Act.PerformedName(action)])
    except IOError as e:
      stderrErrorMsg(fileErrorMessage(fileName, e, Ent.CONFIG_FILE))

  def _verifyValues(sectionName, inputFilterSectionName, outputFilterSectionName):
    itemNamePattern = getREPattern() if checkArgumentPresent('variables') else None
    printKeyValueList([Ent.Singular(Ent.SECTION), sectionName]) # Do not use printEntity
    Ind.Increment()
    for itemName, itemEntry in GC.VAR_INFO.items():
      if itemNamePattern and not itemNamePattern.search(itemName):
        continue
      sectName = sectionName
      if itemName in GC.CSV_INPUT_ROW_FILTER_ITEMS:
        if inputFilterSectionName:
          sectName = inputFilterSectionName
      elif itemName in GC.CSV_OUTPUT_ROW_FILTER_ITEMS:
        if outputFilterSectionName:
          sectName = outputFilterSectionName
      cfgValue = GM.Globals[GM.PARSER].get(sectName, itemName)
      varType = itemEntry[GC.VAR_TYPE]
      if varType == GC.TYPE_CHOICE:
        for choice, value in itemEntry[GC.VAR_CHOICES].items():
          if cfgValue == value:
            cfgValue = choice
            break
      elif varType not in [GC.TYPE_BOOLEAN, GC.TYPE_INTEGER, GC.TYPE_FLOAT, GC.TYPE_PASSWORD]:
        cfgValue = _quoteStringIfLeadingTrailingBlanks(cfgValue)
      if varType == GC.TYPE_FILE:
        expdValue = _getCfgFile(sectName, itemName)
        if cfgValue not in ("''", expdValue):
          cfgValue = f'{cfgValue} ; {expdValue}'
      elif varType == GC.TYPE_DIRECTORY:
        expdValue = _getCfgDirectory(sectName, itemName)
        if cfgValue not in ("''", expdValue):
          cfgValue = f'{cfgValue} ; {expdValue}'
      elif (itemName == GC.SECTION) and (sectName != configparser.DEFAULTSECT):
        continue
      printLine(f'{Ind.Spaces()}{itemName} = {cfgValue}')
    Ind.Decrement()

  def _chkCfgDirectories(sectionName):
    for itemName, itemEntry in GC.VAR_INFO.items():
      if itemEntry[GC.VAR_TYPE] == GC.TYPE_DIRECTORY:
        dirPath = GC.Values[itemName]
        if (not dirPath) and (itemName in {GC.GMAIL_CSE_INCERT_DIR, GC.GMAIL_CSE_INKEY_DIR, GC.INPUT_DIR}):
          return
        if (itemName != GC.CACHE_DIR or not GC.Values[GC.NO_CACHE]) and not os.path.isdir(dirPath):
          writeStderr(formatKeyValueList(WARNING_PREFIX,
                                         [Ent.Singular(Ent.CONFIG_FILE), GM.Globals[GM.GAM_CFG_FILE],
                                          Ent.Singular(Ent.SECTION), sectionName,
                                          Ent.Singular(Ent.ITEM), itemName,
                                          Ent.Singular(Ent.VALUE), dirPath,
                                          Msg.INVALID_PATH],
                                         '\n'))

  def _chkCfgFiles(sectionName):
    for itemName, itemEntry in GC.VAR_INFO.items():
      if itemEntry[GC.VAR_TYPE] == GC.TYPE_FILE:
        fileName = GC.Values[itemName]
        if (not fileName) and (itemName in {GC.EXTRA_ARGS, GC.CMDLOG}):
          continue
        if itemName == GC.CLIENT_SECRETS_JSON: # Added 6.57.01
          continue
        if GC.Values[GC.ENABLE_DASA] and itemName == GC.OAUTH2_TXT:
          continue
        if not os.path.isfile(fileName):
          writeStderr(formatKeyValueList([WARNING_PREFIX, ERROR_PREFIX][itemName == GC.CACERTS_PEM],
                                         [Ent.Singular(Ent.CONFIG_FILE), GM.Globals[GM.GAM_CFG_FILE],
                                          Ent.Singular(Ent.SECTION), sectionName,
                                          Ent.Singular(Ent.ITEM), itemName,
                                          Ent.Singular(Ent.VALUE), fileName,
                                          Msg.NOT_FOUND],
                                         '\n'))
          if itemName == GC.CACERTS_PEM:
            status['errors'] = True
        elif not os.access(fileName, itemEntry[GC.VAR_ACCESS]):
          if itemEntry[GC.VAR_ACCESS] == os.R_OK | os.W_OK:
            accessMsg = Msg.NEED_READ_WRITE_ACCESS
          elif itemEntry[GC.VAR_ACCESS] == os.R_OK:
            accessMsg = Msg.NEED_READ_ACCESS
          else:
            accessMsg = Msg.NEED_WRITE_ACCESS
          writeStderr(formatKeyValueList(ERROR_PREFIX,
                                         [Ent.Singular(Ent.CONFIG_FILE), GM.Globals[GM.GAM_CFG_FILE],
                                          Ent.Singular(Ent.SECTION), sectionName,
                                          Ent.Singular(Ent.ITEM), itemName,
                                          Ent.Singular(Ent.VALUE), fileName,
                                          accessMsg],
                                         '\n'))
          status['errors'] = True

  def _setCSVFile(fileName, mode, encoding, writeHeader, multi, delayOpen):
    if fileName != '-':
      fileName = setFilePath(fileName, GC.DRIVE_DIR)
    GM.Globals[GM.CSVFILE][GM.REDIRECT_NAME] = fileName
    GM.Globals[GM.CSVFILE][GM.REDIRECT_MODE] = mode
    GM.Globals[GM.CSVFILE][GM.REDIRECT_ENCODING] = encoding
    GM.Globals[GM.CSVFILE][GM.REDIRECT_WRITE_HEADER] = writeHeader
    GM.Globals[GM.CSVFILE][GM.REDIRECT_MULTIPROCESS] = multi
    GM.Globals[GM.CSVFILE][GM.REDIRECT_QUEUE] = None
    if not delayOpen and fileName != '-':
      GM.Globals[GM.CSVFILE][GM.REDIRECT_FD] = openFile(fileName, mode, newline='',
                                                        encoding=encoding, errors='backslashreplace')

  def _setSTDFile(stdtype, fileName, mode, multi):
    if stdtype == GM.STDOUT:
      GM.Globals[GM.SAVED_STDOUT] = None
    GM.Globals[stdtype][GM.REDIRECT_STD] = False
    if fileName == 'null':
      GM.Globals[stdtype][GM.REDIRECT_FD] = open(os.devnull, mode, encoding=UTF8)
    elif fileName == '-':
      GM.Globals[stdtype][GM.REDIRECT_STD] = True
      if stdtype == GM.STDOUT:
        GM.Globals[stdtype][GM.REDIRECT_FD] = os.fdopen(os.dup(sys.stdout.fileno()), mode, encoding=GM.Globals[GM.SYS_ENCODING])
      else:
        GM.Globals[stdtype][GM.REDIRECT_FD] = os.fdopen(os.dup(sys.stderr.fileno()), mode, encoding=GM.Globals[GM.SYS_ENCODING])
    else:
      fileName = setFilePath(fileName, GC.DRIVE_DIR)
      if multi and mode == DEFAULT_FILE_WRITE_MODE:
        deleteFile(fileName)
        mode = DEFAULT_FILE_APPEND_MODE
      GM.Globals[stdtype][GM.REDIRECT_FD] = openFile(fileName, mode)
    GM.Globals[stdtype][GM.REDIRECT_MULTI_FD] = GM.Globals[stdtype][GM.REDIRECT_FD] if not multi else StringIOobject()
    if (stdtype == GM.STDOUT) and (GC.Values[GC.DEBUG_LEVEL] > 0):
      GM.Globals[GM.SAVED_STDOUT] = sys.stdout
      sys.stdout = GM.Globals[stdtype][GM.REDIRECT_MULTI_FD]
    GM.Globals[stdtype][GM.REDIRECT_NAME] = fileName
    GM.Globals[stdtype][GM.REDIRECT_MODE] = mode
    GM.Globals[stdtype][GM.REDIRECT_MULTIPROCESS] = multi
    GM.Globals[stdtype][GM.REDIRECT_QUEUE] = 'stdout' if stdtype == GM.STDOUT else 'stderr'

  MULTIPROCESS_EXIT_COMP_PATTERN = re.compile(r'^rc([<>]=?|=|!=)(.+)$', re.IGNORECASE)
  MULTIPROCESS_EXIT_RANGE_PATTERN = re.compile(r'^rcrange(=|!=)(\S+)/(\S+)$', re.IGNORECASE)

  def _setMultiprocessExit():
    rcStr = getString(Cmd.OB_STRING)
    mg = MULTIPROCESS_EXIT_COMP_PATTERN.match(rcStr)
    if mg:
      if not mg.group(2).isdigit():
        usageErrorExit(f'{Msg.EXPECTED}: rc<Operator><Value>')
      GM.Globals[GM.MULTIPROCESS_EXIT_CONDITION] = {'comp': mg.group(1), 'value': int(mg.group(2))}
      return
    mg = MULTIPROCESS_EXIT_RANGE_PATTERN.match(rcStr)
    if mg:
      if not mg.group(2).isdigit() or not  mg.group(3).isdigit():
        usageErrorExit(f'{Msg.EXPECTED}: rcrange<Operator><Value>/Value>')
      GM.Globals[GM.MULTIPROCESS_EXIT_CONDITION] = {'range': mg.group(1), 'low': int(mg.group(2)), 'high': int(mg.group(3))}
      return
    usageErrorExit(f'{Msg.EXPECTED}: (rc<Operator><Value>)|(rcrange<Operator><Value>/Value>)')

  if not GM.Globals[GM.PARSER]:
    homePath = os.path.expanduser('~')
    GM.Globals[GM.GAM_CFG_PATH] = os.environ.get(EV_GAMCFGDIR, None)
    if GM.Globals[GM.GAM_CFG_PATH]:
      GM.Globals[GM.GAM_CFG_PATH] = os.path.expanduser(GM.Globals[GM.GAM_CFG_PATH])
    else:
      GM.Globals[GM.GAM_CFG_PATH] = os.path.join(homePath, '.gam')
    GC.Defaults[GC.CONFIG_DIR] = GM.Globals[GM.GAM_CFG_PATH]
    GC.Defaults[GC.CACHE_DIR] = os.path.join(GM.Globals[GM.GAM_CFG_PATH], 'gamcache')
    GC.Defaults[GC.DRIVE_DIR] = os.path.join(homePath, 'Downloads')
    GM.Globals[GM.GAM_CFG_FILE] = os.path.join(GM.Globals[GM.GAM_CFG_PATH], FN_GAM_CFG)
    if not os.path.isfile(GM.Globals[GM.GAM_CFG_FILE]):
      for itemName, itemEntry in GC.VAR_INFO.items():
        if itemEntry[GC.VAR_TYPE] == GC.TYPE_DIRECTORY:
          _getDefault(itemName, itemEntry, None)
      oldGamPath = os.environ.get(EV_OLDGAMPATH, GC.Defaults[GC.CONFIG_DIR])
      for itemName, itemEntry in GC.VAR_INFO.items():
        if itemEntry[GC.VAR_TYPE] != GC.TYPE_DIRECTORY:
          _getDefault(itemName, itemEntry, oldGamPath)
      GM.Globals[GM.PARSER] = configparser.RawConfigParser(defaults=collections.OrderedDict(sorted(list(GC.Defaults.items()), key=lambda t: t[0])))
      _checkMakeDir(GC.CONFIG_DIR)
      _checkMakeDir(GC.CACHE_DIR)
      _checkMakeDir(GC.DRIVE_DIR)
      for itemName, itemEntry in GC.VAR_INFO.items():
        if itemEntry[GC.VAR_TYPE] == GC.TYPE_FILE:
          srcFile = os.path.expanduser(_stripStringQuotes(GM.Globals[GM.PARSER].get(configparser.DEFAULTSECT, itemName)))
          _copyCfgFile(srcFile, GC.CONFIG_DIR, oldGamPath)
      _writeGamCfgFile(GM.Globals[GM.PARSER], GM.Globals[GM.GAM_CFG_FILE], Act.INITIALIZE)
    else:
      GM.Globals[GM.PARSER] = configparser.RawConfigParser(defaults=collections.OrderedDict(sorted(list(GC.Defaults.items()), key=lambda t: t[0])))
      _readGamCfgFile(GM.Globals[GM.PARSER], GM.Globals[GM.GAM_CFG_FILE])
  status = {'errors': False}
  inputFilterSectionName = outputFilterSectionName = None
  GM.Globals[GM.GAM_CFG_SECTION] = os.environ.get(EV_GAMCFGSECTION, None)
  if GM.Globals[GM.GAM_CFG_SECTION]:
    sectionName = GM.Globals[GM.GAM_CFG_SECTION]
    GM.Globals[GM.SECTION] = sectionName # Save section for inner gams
    if not GM.Globals[GM.PARSER].has_section(sectionName):
      usageErrorExit(formatKeyValueList('', [EV_GAMCFGSECTION, sectionName, Msg.NOT_FOUND], ''))
    if checkArgumentPresent(Cmd.SELECT_CMD):
      Cmd.Backup()
      usageErrorExit(formatKeyValueList('', [EV_GAMCFGSECTION, sectionName, 'select', Msg.NOT_ALLOWED], ''))
  else:
    sectionName = _getCfgSection(configparser.DEFAULTSECT, GC.SECTION)
# select <SectionName> [save] [verify [variables <RESearchPattern>]]
    if checkArgumentPresent(Cmd.SELECT_CMD):
      sectionName = _selectSection()
      GM.Globals[GM.SECTION] = sectionName # Save section for inner gams
# If command line is simply: gam select <SectionName>
# assume save
      if not Cmd.ArgumentsRemaining():
        GM.Globals[GM.PARSER].set(configparser.DEFAULTSECT, GC.SECTION, sectionName)
        _writeGamCfgFile(GM.Globals[GM.PARSER], GM.Globals[GM.GAM_CFG_FILE], Act.SAVE)
      else:
        while Cmd.ArgumentsRemaining():
          if checkArgumentPresent('save'):
            GM.Globals[GM.PARSER].set(configparser.DEFAULTSECT, GC.SECTION, sectionName)
            _writeGamCfgFile(GM.Globals[GM.PARSER], GM.Globals[GM.GAM_CFG_FILE], Act.SAVE)
          elif checkArgumentPresent('verify'):
            _verifyValues(sectionName, inputFilterSectionName, outputFilterSectionName)
          else:
            break
  GM.Globals[GM.GAM_CFG_SECTION_NAME] = sectionName
# showsections
  if checkArgumentPresent(Cmd.SHOWSECTIONS_CMD):
    _showSections()
# selectfilter|selectoutputfilter|selectinputfilter <SectionName>
  while True:
    filterCommand = getChoice([Cmd.SELECTFILTER_CMD, Cmd.SELECTOUTPUTFILTER_CMD, Cmd.SELECTINPUTFILTER_CMD], defaultChoice=None)
    if filterCommand is None:
      break
    if filterCommand != Cmd.SELECTINPUTFILTER_CMD:
      outputFilterSectionName = _selectSection()
    else:
      inputFilterSectionName = _selectSection()
# Handle todrive_nobrowser and todrive_noemail if not present
  value = GM.Globals[GM.PARSER].get(configparser.DEFAULTSECT, GC.TODRIVE_NOBROWSER)
  if value == '':
    GM.Globals[GM.PARSER].set(configparser.DEFAULTSECT, GC.TODRIVE_NOBROWSER, str(_getCfgBoolean(configparser.DEFAULTSECT, GC.NO_BROWSER)).lower())
  value = GM.Globals[GM.PARSER].get(configparser.DEFAULTSECT, GC.TODRIVE_NOEMAIL)
  if value == '':
    GM.Globals[GM.PARSER].set(configparser.DEFAULTSECT, GC.TODRIVE_NOEMAIL, str(not _getCfgBoolean(configparser.DEFAULTSECT, GC.NO_BROWSER)).lower())
# Handle todrive_sheet_timestamp and todrive_sheet_timeformat if not present
  for section in [sectionName, configparser.DEFAULTSECT]:
    value = GM.Globals[GM.PARSER].get(section, GC.TODRIVE_SHEET_TIMESTAMP)
    if value == 'copy':
      GM.Globals[GM.PARSER].set(section, GC.TODRIVE_SHEET_TIMESTAMP, str(_getCfgBoolean(section, GC.TODRIVE_TIMESTAMP)).lower())
    value = GM.Globals[GM.PARSER].get(section, GC.TODRIVE_SHEET_TIMEFORMAT)
    if value == 'copy':
      GM.Globals[GM.PARSER].set(section, GC.TODRIVE_SHEET_TIMEFORMAT, _getCfgString(section, GC.TODRIVE_TIMEFORMAT))
# Fix mistyped keyword cmdlog_max__backups
  for section in [configparser.DEFAULTSECT, sectionName]:
    if GM.Globals[GM.PARSER].has_option(section, GC.CMDLOG_MAX__BACKUPS):
      GM.Globals[GM.PARSER].set(section, GC.CMDLOG_MAX_BACKUPS, GM.Globals[GM.PARSER].get(section, GC.CMDLOG_MAX__BACKUPS))
      GM.Globals[GM.PARSER].remove_option(section, GC.CMDLOG_MAX__BACKUPS)
# config (<VariableName> [=] <Value>)* [save] [verify [variables <RESearchPattern>]]
  if checkArgumentPresent(Cmd.CONFIG_CMD):
    while Cmd.ArgumentsRemaining():
      if checkArgumentPresent('save'):
        _writeGamCfgFile(GM.Globals[GM.PARSER], GM.Globals[GM.GAM_CFG_FILE], Act.SAVE)
      elif checkArgumentPresent('verify'):
        _verifyValues(sectionName, inputFilterSectionName, outputFilterSectionName)
      else:
        itemName = getChoice(GC.VAR_INFO, defaultChoice=None)
        if itemName is None:
          break
        itemEntry = GC.VAR_INFO[itemName]
        checkArgumentPresent('=')
        varType = itemEntry[GC.VAR_TYPE]
        if varType == GC.TYPE_BOOLEAN:
          value = TRUE if getBoolean(None) else FALSE
        elif varType == GC.TYPE_CHARACTER:
          value = getCharacter()
        elif varType == GC.TYPE_CHOICE:
          value = getChoice(itemEntry[GC.VAR_CHOICES])
        elif varType == GC.TYPE_INTEGER:
          minVal, maxVal = itemEntry[GC.VAR_LIMITS]
          value = str(getInteger(minVal=minVal, maxVal=maxVal))
        elif varType == GC.TYPE_FLOAT:
          minVal, maxVal = itemEntry[GC.VAR_LIMITS]
          value = str(getFloat(minVal=minVal, maxVal=maxVal))
        elif varType == GC.TYPE_LOCALE:
          value = getLanguageCode(LOCALE_CODES_MAP)
        elif varType == GC.TYPE_PASSWORD:
          minLen, maxLen = itemEntry[GC.VAR_LIMITS]
          value = getString(Cmd.OB_STRING, checkBlank=True, minLen=minLen, maxLen=maxLen)
          if value and value.startswith("b'") and value.endswith("'"):
            value = bytes(value[2:-1], UTF8)
        elif varType == GC.TYPE_TIMEZONE:
          value = getString(Cmd.OB_STRING, checkBlank=True)
        else: # GC.TYPE_STRING, GC.TYPE_STRINGLIST
          minLen, maxLen = itemEntry.get(GC.VAR_LIMITS, (0, None))
          value = _quoteStringIfLeadingTrailingBlanks(getString(Cmd.OB_STRING, minLen=minLen, maxLen=maxLen))
        GM.Globals[GM.PARSER].set(sectionName, itemName, value)
  prevExtraArgsTxt = GC.Values.get(GC.EXTRA_ARGS, None)
  prevOauth2serviceJson = GC.Values.get(GC.OAUTH2SERVICE_JSON, None)
# Assign global variables, directories, timezone first as other variables depend on them
  for itemName, itemEntry in sorted(GC.VAR_INFO.items()):
    varType = itemEntry[GC.VAR_TYPE]
    if varType == GC.TYPE_DIRECTORY:
      GC.Values[itemName] = _getCfgDirectory(sectionName, itemName)
    elif varType == GC.TYPE_TIMEZONE:
      GC.Values[itemName] = _getCfgTimezone(sectionName, itemName)
  GM.Globals[GM.DATETIME_NOW] = arrow.now(GC.Values[GC.TIMEZONE])
# Everything else except row filters
  for itemName, itemEntry in sorted(GC.VAR_INFO.items()):
    varType = itemEntry[GC.VAR_TYPE]
    if varType == GC.TYPE_BOOLEAN:
      GC.Values[itemName] = _getCfgBoolean(sectionName, itemName)
    elif varType == GC.TYPE_CHARACTER:
      GC.Values[itemName] = _getCfgCharacter(sectionName, itemName)
    elif varType == GC.TYPE_CHOICE:
      GC.Values[itemName] = _getCfgChoice(sectionName, itemName)
    elif varType in [GC.TYPE_INTEGER, GC.TYPE_FLOAT]:
      GC.Values[itemName] = _getCfgNumber(sectionName, itemName)
    elif varType == GC.TYPE_HEADERFILTER:
      GC.Values[itemName] = _getCfgHeaderFilter(sectionName, itemName)
    elif varType == GC.TYPE_LOCALE:
      GC.Values[itemName] = _getCfgLocale(sectionName, itemName)
    elif varType == GC.TYPE_PASSWORD:
      GC.Values[itemName] = _getCfgPassword(sectionName, itemName)
    elif varType == GC.TYPE_STRING:
      GC.Values[itemName] = _getCfgString(sectionName, itemName)
    elif varType in {GC.TYPE_STRINGLIST, GC.TYPE_HEADERFORCEREQUIRED, GC.TYPE_HEADERORDER}:
      GC.Values[itemName] = _getCfgStringList(sectionName, itemName)
    elif varType == GC.TYPE_FILE:
      GC.Values[itemName] = _getCfgFile(sectionName, itemName)
# Row filters
  for itemName, itemEntry in sorted(GC.VAR_INFO.items()):
    varType = itemEntry[GC.VAR_TYPE]
    if varType == GC.TYPE_ROWFILTER:
      GC.Values[itemName] = _getCfgRowFilter(sectionName, itemName)
# Process selectfilter|selectoutputfilter|selectinputfilter
  if inputFilterSectionName:
    GC.Values[GC.CSV_INPUT_ROW_FILTER] = _getCfgRowFilter(inputFilterSectionName, GC.CSV_INPUT_ROW_FILTER)
    GC.Values[GC.CSV_INPUT_ROW_FILTER_MODE] = _getCfgChoice(inputFilterSectionName, GC.CSV_INPUT_ROW_FILTER_MODE)
    GC.Values[GC.CSV_INPUT_ROW_DROP_FILTER] = _getCfgRowFilter(inputFilterSectionName, GC.CSV_INPUT_ROW_DROP_FILTER)
    GC.Values[GC.CSV_INPUT_ROW_DROP_FILTER_MODE] = _getCfgChoice(inputFilterSectionName, GC.CSV_INPUT_ROW_DROP_FILTER_MODE)
    GC.Values[GC.CSV_INPUT_ROW_LIMIT] = _getCfgNumber(inputFilterSectionName, GC.CSV_INPUT_ROW_LIMIT)
  if outputFilterSectionName:
    GC.Values[GC.CSV_OUTPUT_HEADER_FORCE] = _getCfgStringList(outputFilterSectionName, GC.CSV_OUTPUT_HEADER_FORCE)
    if GC.Values[GC.CSV_OUTPUT_HEADER_FORCE]:
      GC.Values[GC.CSV_OUTPUT_HEADER_FILTER] = _getCfgHeaderFilterFromForce(outputFilterSectionName, GC.CSV_OUTPUT_HEADER_FORCE)
    else:
      GC.Values[GC.CSV_OUTPUT_HEADER_FILTER] = _getCfgHeaderFilter(outputFilterSectionName, GC.CSV_OUTPUT_HEADER_FILTER)
    GC.Values[GC.CSV_OUTPUT_HEADER_DROP_FILTER] = _getCfgHeaderFilter(outputFilterSectionName, GC.CSV_OUTPUT_HEADER_DROP_FILTER)
    GC.Values[GC.CSV_OUTPUT_HEADER_ORDER] = _getCfgStringList(outputFilterSectionName, GC.CSV_OUTPUT_HEADER_ORDER)
    GC.Values[GC.CSV_OUTPUT_HEADER_REQUIRED] = _getCfgStringList(outputFilterSectionName, GC.CSV_OUTPUT_HEADER_REQUIRED)
    GC.Values[GC.CSV_OUTPUT_ROW_FILTER] = _getCfgRowFilter(outputFilterSectionName, GC.CSV_OUTPUT_ROW_FILTER)
    GC.Values[GC.CSV_OUTPUT_ROW_FILTER_MODE] = _getCfgChoice(outputFilterSectionName, GC.CSV_OUTPUT_ROW_FILTER_MODE)
    GC.Values[GC.CSV_OUTPUT_ROW_DROP_FILTER] = _getCfgRowFilter(outputFilterSectionName, GC.CSV_OUTPUT_ROW_DROP_FILTER)
    GC.Values[GC.CSV_OUTPUT_ROW_DROP_FILTER_MODE] = _getCfgChoice(outputFilterSectionName, GC.CSV_OUTPUT_ROW_DROP_FILTER_MODE)
    GC.Values[GC.CSV_OUTPUT_ROW_LIMIT] = _getCfgNumber(outputFilterSectionName, GC.CSV_OUTPUT_ROW_LIMIT)
    GC.Values[GC.CSV_OUTPUT_SORT_HEADERS] = _getCfgStringList(outputFilterSectionName, GC.CSV_OUTPUT_SORT_HEADERS)
  elif GC.Values[GC.CSV_OUTPUT_HEADER_FORCE]:
    GC.Values[GC.CSV_OUTPUT_HEADER_FILTER] = _getCfgHeaderFilterFromForce(sectionName, GC.CSV_OUTPUT_HEADER_FORCE)
  if status['errors']:
    sys.exit(CONFIG_ERROR_RC)
# Global values cleanup
  GC.Values[GC.DOMAIN] = GC.Values[GC.DOMAIN].lower()
  if not GC.Values[GC.SMTP_FQDN]:
    GC.Values[GC.SMTP_FQDN] = None
# Inherit debug_level, output_dateformat, output_timeformat if not locally defined
  if GM.Globals[GM.PID] != 0:
    if GC.Values[GC.DEBUG_LEVEL] == 0:
      GC.Values[GC.DEBUG_LEVEL] = GM.Globals[GM.DEBUG_LEVEL]
    if not GC.Values[GC.OUTPUT_DATEFORMAT]:
      GC.Values[GC.OUTPUT_DATEFORMAT] = GM.Globals[GM.OUTPUT_DATEFORMAT]
    if not GC.Values[GC.OUTPUT_TIMEFORMAT]:
      GC.Values[GC.OUTPUT_TIMEFORMAT] = GM.Globals[GM.OUTPUT_TIMEFORMAT]
# Define lockfile: oauth2.txt.lock
  GM.Globals[GM.OAUTH2_TXT_LOCK] = f'{GC.Values[GC.OAUTH2_TXT]}.lock'
# Override httplib2 settings
  httplib2.debuglevel = GC.Values[GC.DEBUG_LEVEL]
# Override requests debuglevel also. Requests is used with
# SignJWT/WIF/GCE and a few other places.
  http.client.HTTPConnection.debuglevel = GC.Values[GC.DEBUG_LEVEL]
# Use our own print function for http.client so we can redact and cleanup
  http.client.print = redactable_debug_print
# Reset global variables if required
  if prevExtraArgsTxt != GC.Values[GC.EXTRA_ARGS]:
    GM.Globals[GM.EXTRA_ARGS_LIST] = [('prettyPrint', GC.Values[GC.DEBUG_LEVEL] > 0)]
    if GC.Values[GC.EXTRA_ARGS]:
      ea_config = configparser.ConfigParser()
      ea_config.optionxform = str
      ea_config.read(GC.Values[GC.EXTRA_ARGS])
      GM.Globals[GM.EXTRA_ARGS_LIST].extend(ea_config.items('extra-args'))
  if prevOauth2serviceJson != GC.Values[GC.OAUTH2SERVICE_JSON]:
    GM.Globals[GM.OAUTH2SERVICE_JSON_DATA] = {}
    GM.Globals[GM.OAUTH2SERVICE_CLIENT_ID] = None
  Cmd.SetEncoding(GM.Globals[GM.SYS_ENCODING])
# multiprocessexit (rc<Operator><Number>)|(rcrange=<Number>/<Number>)|(rcrange!=<Number>/<Number>)
  if checkArgumentPresent(Cmd.MULTIPROCESSEXIT_CMD):
    _setMultiprocessExit()
# redirect csv <FileName> [delayopen] [multiprocess] [append] [noheader] [charset <CharSet>]
#	       [columndelimiter <Character>] [quotechar <Character>]] [noescapechar [<Boolean>]]
#	       [sortheaders <StringList>] [timestampcolumn <String>] [transpose [<Boolean>]]
#	       [todrive <ToDriveAttribute>*]
# redirect stdout <FileName> [multiprocess] [append]
# redirect stdout null
# redirect stderr <FileName> [multiprocess] [append]
# redirect stderr stdout
# redirect stderr null
  while checkArgumentPresent(Cmd.REDIRECT_CMD):
    myarg = getChoice(['csv', 'stdout', 'stderr'])
    filename = re.sub(r'{{Section}}', sectionName, getString(Cmd.OB_FILE_NAME, checkBlank=True))
    if myarg == 'csv':
      multi = False
      mode =  DEFAULT_FILE_WRITE_MODE
      writeHeader = True
      encoding = GC.Values[GC.CHARSET]
      delayOpen = False
      while Cmd.ArgumentsRemaining():
        myarg = getArgument()
        if myarg == 'multiprocess':
          multi = True
        elif myarg == 'append':
          mode = DEFAULT_FILE_APPEND_MODE
        elif myarg == 'noheader':
          writeHeader = False
        elif myarg == 'charset':
          encoding = getString(Cmd.OB_CHAR_SET)
        elif myarg == 'delayopen':
          delayOpen = True
        elif myarg == 'columndelimiter':
          GM.Globals[GM.CSV_OUTPUT_COLUMN_DELIMITER] = GC.Values[GC.CSV_OUTPUT_COLUMN_DELIMITER] = getCharacter()
        elif myarg == 'quotechar':
          GM.Globals[GM.CSV_OUTPUT_QUOTE_CHAR] = GC.Values[GC.CSV_OUTPUT_QUOTE_CHAR] = getCharacter()
        elif myarg == 'noescapechar':
          GM.Globals[GM.CSV_OUTPUT_NO_ESCAPE_CHAR] = GC.Values[GC.CSV_OUTPUT_NO_ESCAPE_CHAR] = getBoolean()
        elif myarg == 'sortheaders':
          GM.Globals[GM.CSV_OUTPUT_SORT_HEADERS] = GC.Values[GC.CSV_OUTPUT_SORT_HEADERS] = getString(Cmd.OB_STRING_LIST, minLen=0).replace(',', ' ').split()
        elif myarg == 'timestampcolumn':
          GM.Globals[GM.CSV_OUTPUT_TIMESTAMP_COLUMN] = GC.Values[GC.CSV_OUTPUT_TIMESTAMP_COLUMN] = getString(Cmd.OB_STRING, minLen=0)
        elif myarg == 'transpose':
          GM.Globals[GM.CSV_OUTPUT_TRANSPOSE] = getBoolean()
        else:
          Cmd.Backup()
          break
      _setCSVFile(filename, mode, encoding, writeHeader, multi, delayOpen)
      GM.Globals[GM.CSVFILE][GM.REDIRECT_QUEUE_CSVPF] = CSVPrintFile()
      if checkArgumentPresent('todrive'):
        GM.Globals[GM.CSVFILE][GM.REDIRECT_QUEUE_CSVPF].GetTodriveParameters()
        GM.Globals[GM.CSV_TODRIVE] = GM.Globals[GM.CSVFILE][GM.REDIRECT_QUEUE_CSVPF].todrive.copy()
    elif myarg == 'stdout':
      if filename.lower() == 'null':
        multi = checkArgumentPresent('multiprocess')
        _setSTDFile(GM.STDOUT, 'null', DEFAULT_FILE_WRITE_MODE, multi)
      else:
        multi = checkArgumentPresent('multiprocess')
        mode = DEFAULT_FILE_APPEND_MODE if checkArgumentPresent('append') else DEFAULT_FILE_WRITE_MODE
        _setSTDFile(GM.STDOUT, filename, mode, multi)
    else: # myarg == 'stderr'
      if filename.lower() == 'null':
        multi = checkArgumentPresent('multiprocess')
        _setSTDFile(GM.STDERR, 'null', DEFAULT_FILE_WRITE_MODE, multi)
      elif filename.lower() != 'stdout':
        multi = checkArgumentPresent('multiprocess')
        mode = DEFAULT_FILE_APPEND_MODE if checkArgumentPresent('append') else DEFAULT_FILE_WRITE_MODE
        _setSTDFile(GM.STDERR, filename, mode, multi)
      else:
        multi = checkArgumentPresent('multiprocess')
        if not GM.Globals[GM.STDOUT]:
          _setSTDFile(GM.STDOUT, '-', DEFAULT_FILE_WRITE_MODE, multi)
        GM.Globals[GM.STDERR] = GM.Globals[GM.STDOUT].copy()
        GM.Globals[GM.STDERR][GM.REDIRECT_NAME] = 'stdout'
  if not GM.Globals[GM.STDOUT]:
    _setSTDFile(GM.STDOUT, '-', DEFAULT_FILE_WRITE_MODE, False)
  if not GM.Globals[GM.STDERR]:
    _setSTDFile(GM.STDERR, '-', DEFAULT_FILE_WRITE_MODE, False)
# If both csv and stdout are redirected to - with same multiprocess setting and csv doesn't have any todrive parameters, collapse csv onto stdout
  if (GM.Globals[GM.PID] == 0  and GM.Globals[GM.CSVFILE] and
      GM.Globals[GM.CSVFILE][GM.REDIRECT_NAME] == '-' and GM.Globals[GM.STDOUT][GM.REDIRECT_NAME] == '-' and
      GM.Globals[GM.CSVFILE][GM.REDIRECT_MULTIPROCESS] == GM.Globals[GM.STDOUT][GM.REDIRECT_MULTIPROCESS] and
      GM.Globals[GM.CSVFILE].get(GM.REDIRECT_QUEUE_CSVPF) and not GM.Globals[GM.CSVFILE][GM.REDIRECT_QUEUE_CSVPF].todrive):
    _setCSVFile('-', GM.Globals[GM.STDOUT].get(GM.REDIRECT_MODE, DEFAULT_FILE_WRITE_MODE), GC.Values[GC.CHARSET],
                GM.Globals[GM.CSVFILE].get(GM.REDIRECT_WRITE_HEADER, True), GM.Globals[GM.STDOUT][GM.REDIRECT_MULTIPROCESS], False)
  elif not GM.Globals[GM.CSVFILE]:
    _setCSVFile('-', GM.Globals[GM.STDOUT].get(GM.REDIRECT_MODE, DEFAULT_FILE_WRITE_MODE), GC.Values[GC.CHARSET], True, False, False)
  initAPICallsRateCheck()
# Main process
# Clear input row filters/limit from parser, children can define but shouldn't inherit global value
# Clear output header/row filters/limit from parser, children can define or they will inherit global value if not defined
  if GM.Globals[GM.PID] == 0:
    for itemName, itemEntry in sorted(GC.VAR_INFO.items()):
      varType = itemEntry[GC.VAR_TYPE]
      if varType in {GC.TYPE_HEADERFILTER, GC.TYPE_HEADERFORCEREQUIRED, GC.TYPE_HEADERORDER, GC.TYPE_ROWFILTER}:
        GM.Globals[GM.PARSER].set(sectionName, itemName, '')
      elif (varType == GC.TYPE_INTEGER) and itemName in {GC.CSV_INPUT_ROW_LIMIT, GC.CSV_OUTPUT_ROW_LIMIT}:
        GM.Globals[GM.PARSER].set(sectionName, itemName, '0')
# Child process
# Inherit main process output header/row filters/limit, print defaults if not locally defined
  else:
    if not GC.Values[GC.CSV_OUTPUT_HEADER_FILTER]:
      GC.Values[GC.CSV_OUTPUT_HEADER_FILTER] = GM.Globals[GM.CSV_OUTPUT_HEADER_FILTER][:]
    if not GC.Values[GC.CSV_OUTPUT_HEADER_DROP_FILTER]:
      GC.Values[GC.CSV_OUTPUT_HEADER_DROP_FILTER] = GM.Globals[GM.CSV_OUTPUT_HEADER_DROP_FILTER][:]
    if not GC.Values[GC.CSV_OUTPUT_HEADER_FORCE]:
      GC.Values[GC.CSV_OUTPUT_HEADER_FORCE] = GM.Globals[GM.CSV_OUTPUT_HEADER_FORCE][:]
    if not GC.Values[GC.CSV_OUTPUT_HEADER_ORDER]:
      GC.Values[GC.CSV_OUTPUT_HEADER_ORDER] = GM.Globals[GM.CSV_OUTPUT_HEADER_ORDER][:]
    if not GC.Values[GC.CSV_OUTPUT_HEADER_REQUIRED]:
      GC.Values[GC.CSV_OUTPUT_HEADER_REQUIRED] = GM.Globals[GM.CSV_OUTPUT_HEADER_REQUIRED][:]
    if not GC.Values[GC.CSV_OUTPUT_ROW_FILTER]:
      GC.Values[GC.CSV_OUTPUT_ROW_FILTER] = GM.Globals[GM.CSV_OUTPUT_ROW_FILTER][:]
      GC.Values[GC.CSV_OUTPUT_ROW_FILTER_MODE] = GM.Globals[GM.CSV_OUTPUT_ROW_FILTER_MODE]
    if not GC.Values[GC.CSV_OUTPUT_ROW_DROP_FILTER]:
      GC.Values[GC.CSV_OUTPUT_ROW_DROP_FILTER] = GM.Globals[GM.CSV_OUTPUT_ROW_DROP_FILTER][:]
      GC.Values[GC.CSV_OUTPUT_ROW_DROP_FILTER_MODE] = GM.Globals[GM.CSV_OUTPUT_ROW_DROP_FILTER_MODE]
    if not GC.Values[GC.CSV_OUTPUT_ROW_LIMIT]:
      GC.Values[GC.CSV_OUTPUT_ROW_LIMIT] = GM.Globals[GM.CSV_OUTPUT_ROW_LIMIT]
    if not GC.Values[GC.PRINT_AGU_DOMAINS]:
      GC.Values[GC.PRINT_AGU_DOMAINS] = GM.Globals[GM.PRINT_AGU_DOMAINS]
    if not GC.Values[GC.PRINT_CROS_OUS]:
      GC.Values[GC.PRINT_CROS_OUS] = GM.Globals[GM.PRINT_CROS_OUS]
    if not GC.Values[GC.PRINT_CROS_OUS_AND_CHILDREN]:
      GC.Values[GC.PRINT_CROS_OUS_AND_CHILDREN] = GM.Globals[GM.PRINT_CROS_OUS_AND_CHILDREN]
    GC.Values[GC.SHOW_GETTINGS] = GM.Globals[GM.SHOW_GETTINGS]
    GC.Values[GC.SHOW_GETTINGS_GOT_NL] = GM.Globals[GM.SHOW_GETTINGS_GOT_NL]
# customer_id, domain and admin_email must be set when enable_dasa = true
  if GC.Values[GC.ENABLE_DASA]:
    errors = 0
    for itemName in [GC.CUSTOMER_ID, GC.DOMAIN, GC.ADMIN_EMAIL]:
      if not GC.Values[itemName] or (itemName == GC.CUSTOMER_ID and GC.Values[itemName] == GC.MY_CUSTOMER):
        stderrErrorMsg(formatKeyValueList('',
                                          [Ent.Singular(Ent.CONFIG_FILE), GM.Globals[GM.GAM_CFG_FILE],
                                           Ent.Singular(Ent.SECTION), sectionName,
                                           itemName, GC.Values[itemName] or '""',
                                           GC.ENABLE_DASA, GC.Values[GC.ENABLE_DASA],
                                           Msg.NOT_COMPATIBLE],
                                          '\n'))
        errors += 1
    if errors:
      sys.exit(USAGE_ERROR_RC)
# If no select/options commands were executed or some were and there are more arguments on the command line,
# warn if the json files are missing and return True
  if (Cmd.Location() == 1) or (Cmd.ArgumentsRemaining()):
    _chkCfgDirectories(sectionName)
    if not Cmd.PeekArgumentPresent(['checkconn', 'checkconnection', 'comment', 'oauth', 'oauth2', 'version']):
      _chkCfgFiles(sectionName)
    if status['errors']:
      sys.exit(CONFIG_ERROR_RC)
    if GC.Values[GC.NO_CACHE]:
      GM.Globals[GM.CACHE_DIR] = None
      GM.Globals[GM.CACHE_DISCOVERY_ONLY] = False
    else:
      GM.Globals[GM.CACHE_DIR] = GC.Values[GC.CACHE_DIR]
      GM.Globals[GM.CACHE_DISCOVERY_ONLY] = GC.Values[GC.CACHE_DISCOVERY_ONLY]
# Set environment variables so GData API can find cacerts.pem
    os.environ['REQUESTS_CA_BUNDLE'] = GC.Values[GC.CACERTS_PEM]
    os.environ['DEFAULT_CA_BUNDLE_PATH'] = GC.Values[GC.CACERTS_PEM]
    os.environ['HTTPLIB2_CA_CERTS'] = GC.Values[GC.CACERTS_PEM]
    os.environ['SSL_CERT_FILE'] = GC.Values[GC.CACERTS_PEM]
    httplib2.CA_CERTS = GC.Values[GC.CACERTS_PEM]
# Needs to be set so oauthlib doesn't puke when Google changes our scopes
    os.environ['OAUTHLIB_RELAX_TOKEN_SCOPE'] = 'true'
# Set up command logging at top level only
    if (GM.Globals[GM.PID] == 0) and GC.Values[GC.CMDLOG]:
      openGAMCommandLog(GM.Globals, 'mainlog')
    return True
# We're done, nothing else to do
  return False

