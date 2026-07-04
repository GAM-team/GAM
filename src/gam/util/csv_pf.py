"""GAM CSV Print Framework utilities.

CSV output formatting, row/header filtering, JSON flattening,
and Google Drive upload (todrive) for print/show commands.
"""

import csv
import io
import re
import sys
import webbrowser

import arrow
import googleapiclient.http

from gamlib import api as API
from gamlib import settings as GC
from gamlib import gapi as GAPI
from gamlib import state as GM
from gamlib import msgs as Msg
from gam.constants import DEFAULT_FILE_APPEND_MODE, INSUFFICIENT_PERMISSIONS_RC, MAX_GOOGLE_SHEET_CELLS, NO_CSV_DATA_TO_UPLOAD_RC, ROOT
from tempfile import TemporaryFile
from util.api import _getAdminEmail, buildGAPIObject
from util.svcacct import buildGAPIServiceObject, chooseSaAPI
from util.api_call import callGAPI, callGAPIpages
from util.args import LOCALE_CODES_MAP, NEVER_TIME, TRUE_FALSE, UTF8, YYYYMMDD_FORMAT, YYYYMMDD_PATTERN, escapeCRsNLs, formatLocalTime, formatLocalTimestamp, getArgument, getBoolean, getCharacter, getChoice, getInteger, getLanguageCode, getSheetEntity, getSheetIdFromSheetEntity, getString, normalizeEmailAddressOrUID, protectedSheetId, todaysTime
from util.display import ACTION_FAILED_RC, entityActionFailedWarning, entityActionPerformed, printBlankLine, printJSONKey, printJSONValue, printKeyValueList, userDriveServiceNotEnabledWarning
from util.email import send_email
from util.entity import MIMETYPE_GA_FOLDER, MIMETYPE_GA_SPREADSHEET, checkUserExists, getEntityArgument
from util.errors import USAGE_ERROR_RC, invalidArgumentExit, invalidChoiceExit, missingArgumentExit, unknownArgumentExit, usageErrorExit
from util.fileio import FILE_ERROR_RC, StringIOobject, closeFile, fdErrorMessage, openFile
from util.output import ISOformatTimeStamp, WARNING, currentCountNL, formatKeyValueList, printWarningMessage, setSysExitRC, stderrErrorMsg, stderrWarningMsg, systemErrorExit, writeStdout
from gam.var import Act, Cmd, Ent, Ind



def addFieldToFieldsList(fieldName, fieldsChoiceMap, fieldsList):
  fields = fieldsChoiceMap[fieldName.lower()]
  if isinstance(fields, list):
    fieldsList.extend(fields)
  else:
    fieldsList.append(fields)

def _getFieldsList():
  return getString(Cmd.OB_FIELD_NAME_LIST).lower().replace('_', '').replace(',', ' ').split()

def _getRawFields(requiredField=None):
  rawFields = getString(Cmd.OB_FIELDS)
  if requiredField is None or requiredField in rawFields:
    return rawFields
  return f'{requiredField},{rawFields}'

def CheckInputRowFilterHeaders(titlesList, rowFilter, rowDropFilter):
  status = True
  for filterVal in rowFilter:
    columns = [t for t in titlesList if filterVal[0].match(t)]
    if not columns:
      stderrErrorMsg(Msg.COLUMN_DOES_NOT_MATCH_ANY_INPUT_COLUMNS.format(GC.CSV_INPUT_ROW_FILTER, filterVal[0].pattern))
      status = False
  for filterVal in rowDropFilter:
    columns = [t for t in titlesList if filterVal[0].match(t)]
    if not columns:
      stderrErrorMsg(Msg.COLUMN_DOES_NOT_MATCH_ANY_INPUT_COLUMNS.format(GC.CSV_INPUT_ROW_DROP_FILTER, filterVal[0].pattern))
      status = False
  if not status:
    sys.exit(USAGE_ERROR_RC)

def _stripTimeFromDateTime(rowDate):
  if YYYYMMDD_PATTERN.match(rowDate):
    try:
      rowTime = arrow.Arrow.strptime(rowDate, YYYYMMDD_FORMAT)
    except ValueError:
      return None
  else:
    try:
      rowTime = arrow.get(rowDate)
    except (arrow.parser.ParserError, OverflowError):
      return None
  return ISOformatTimeStamp(arrow.Arrow(rowTime.year, rowTime.month, rowTime.day, tzinfo='UTC'))

def _getHourMinuteFromDateTime(rowDate):
  if YYYYMMDD_PATTERN.match(rowDate):
    return None
  try:
    rowTime = arrow.get(rowDate)
  except (arrow.parser.ParserError, OverflowError):
    return None
  return f'{rowTime.hour:02d}:{rowTime.minute:02d}'

def RowFilterMatch(row, titlesList, rowFilter, rowFilterModeAll, rowDropFilter, rowDropFilterModeAll):
  def rowRegexFilterMatch(filterPattern):
    if anyMatch:
      for column in columns:
        if filterPattern.search(str(row.get(column, ''))):
          return True
      return False
    for column in columns:
      if not filterPattern.search(str(row.get(column, ''))):
        return False
    return True

  def rowNotRegexFilterMatch(filterPattern):
    if anyMatch:
      for column in columns:
        if filterPattern.search(str(row.get(column, ''))):
          return False
      return True
    for column in columns:
      if not filterPattern.search(str(row.get(column, ''))):
        return True

    return False


  def rowDateTimeFilterMatch(dateMode, op, filterDate):
    def checkMatch(rowDate):
      if not rowDate or not isinstance(rowDate, str):
        return False
      if rowDate == GC.Values[GC.NEVER_TIME]:
        rowDate = NEVER_TIME
      if dateMode:
        rowDate = _stripTimeFromDateTime(rowDate)
        if not rowDate:
          return False
      if op == '<':
        return rowDate < filterDate
      if op == '<=':
        return rowDate <= filterDate
      if op == '>':
        return rowDate > filterDate
      if op == '>=':
        return rowDate >= filterDate
      if op == '!=':
        return rowDate != filterDate
      return rowDate == filterDate

    if anyMatch:
      for column in columns:
        if checkMatch(row.get(column, '')):
          return True
      return False
    for column in columns:
      if not checkMatch(row.get(column, '')):
        return False
    return True

  def rowDateTimeRangeFilterMatch(dateMode, op, filterDateL, filterDateR):
    def checkMatch(rowDate):
      if not rowDate or not isinstance(rowDate, str):
        return False
      if rowDate == GC.Values[GC.NEVER_TIME]:
        rowDate = NEVER_TIME
      if dateMode:
        rowDate = _stripTimeFromDateTime(rowDate)
        if not rowDate:
          return False
      if op == '!=':
        return not filterDateL <= rowDate <= filterDateR
      return filterDateL <= rowDate <= filterDateR

    if anyMatch:
      for column in columns:
        if checkMatch(row.get(column, '')):
          return True
      return False
    for column in columns:
      if not checkMatch(row.get(column, '')):
        return False
    return True


  def rowTimeOfDayRangeFilterMatch(op, startHourMinute, endHourMinute):
    def checkMatch(rowDate):
      if not rowDate or not isinstance(rowDate, str) or rowDate == GC.Values[GC.NEVER_TIME]:
        return False
      rowHourMinute = _getHourMinuteFromDateTime(rowDate)
      if not rowHourMinute:
        return False
      if op == '!=':
        return not startHourMinute <= rowHourMinute <= endHourMinute
      return startHourMinute <= rowHourMinute <= endHourMinute

    if anyMatch:
      for column in columns:
        if checkMatch(row.get(column, '')):
          return True
      return False
    for column in columns:
      if not checkMatch(row.get(column, '')):
        return False
    return True

  def rowCountFilterMatch(op, filterCount):
    def checkMatch(rowCount):
      if isinstance(rowCount, str):
##### Blank = 0
        if not rowCount:
          rowCount = '0'
        elif not rowCount.isdigit():
          return False
        rowCount = int(rowCount)
      elif not isinstance(rowCount, int):
        return False
      if op == '<':
        return rowCount < filterCount
      if op == '<=':
        return rowCount <= filterCount
      if op == '>':
        return rowCount > filterCount
      if op == '>=':
        return rowCount >= filterCount
      if op == '!=':
        return rowCount != filterCount
      return rowCount == filterCount

    if anyMatch:
      for column in columns:
        if checkMatch(row.get(column, 0)):
          return True
      return False
    for column in columns:
      if not checkMatch(row.get(column, 0)):
        return False
    return True

  def rowCountRangeFilterMatch(op, filterCountL, filterCountR):
    def checkMatch(rowCount):
      if isinstance(rowCount, str):
        if not rowCount.isdigit():
          return False
        rowCount = int(rowCount)
      elif not isinstance(rowCount, int):
        return False
      if op == '!=':
        return not filterCountL <= rowCount <= filterCountR
      return filterCountL <= rowCount <= filterCountR

    if anyMatch:
      for column in columns:
        if checkMatch(row.get(column, 0)):
          return True
      return False
    for column in columns:
      if not checkMatch(row.get(column, 0)):
        return False
    return True

  def rowLengthFilterMatch(op, filterLength):
    def checkMatch(rowString):
      if not isinstance(rowString, str):
        return False
      rowLength = len(rowString)
      if op == '<':
        return rowLength < filterLength
      if op == '<=':
        return rowLength <= filterLength
      if op == '>':
        return rowLength > filterLength
      if op == '>=':
        return rowLength >= filterLength
      if op == '!=':
        return rowLength != filterLength
      return rowLength == filterLength

    if anyMatch:
      for column in columns:
        if checkMatch(row.get(column, '')):
          return True
      return False
    for column in columns:
      if not checkMatch(row.get(column, '')):
        return False
    return True

  def rowLengthRangeFilterMatch(op, filterLengthL, filterLengthR):
    def checkMatch(rowString):
      if not isinstance(rowString, str):
        return False
      rowLength = len(rowString)
      if op == '!=':
        return not filterLengthL <= rowLength <= filterLengthR
      return filterLengthL <= rowLength <= filterLengthR

    if anyMatch:
      for column in columns:
        if checkMatch(row.get(column, '')):
          return True
      return False
    for column in columns:
      if not checkMatch(row.get(column, '')):
        return False
    return True

  def rowBooleanFilterMatch(filterBoolean):
    def checkMatch(rowBoolean):
      if isinstance(rowBoolean, bool):
        return rowBoolean == filterBoolean
      if isinstance(rowBoolean, str):
        if rowBoolean.lower() in TRUE_FALSE:
          return rowBoolean.capitalize() == str(filterBoolean)
##### Blank = False
        if not rowBoolean:
          return not filterBoolean
      return False

    if anyMatch:
      for column in columns:
        if checkMatch(row.get(column, False)):
          return True
      return False
    for column in columns:
      if not checkMatch(row.get(column, False)):
        return False
    return True

  def rowDataFilterMatch(filterData):
    if anyMatch:
      for column in columns:
        if str(row.get(column, '')) in filterData:
          return True
      return False
    for column in columns:
      if str(row.get(column, '')) not in filterData:
        return False
    return True

  def rowNotDataFilterMatch(filterData):
    if anyMatch:
      for column in columns:
        if str(row.get(column, '')) in filterData:
          return False
      return True
    for column in columns:
      if str(row.get(column, '')) not in filterData:
        return True
    return False

  def rowTextFilterMatch(op, filterText):
    def checkMatch(rowText):
      if not isinstance(rowText, str):
        rowText = str(rowText)
      if op == '<':
        return rowText < filterText
      if op == '<=':
        return rowText <= filterText
      if op == '>':
        return rowText > filterText
      if op == '>=':
        return rowText >= filterText
      if op == '!=':
        return rowText != filterText
      return rowText == filterText

    if anyMatch:
      for column in columns:
        if checkMatch(row.get(column, '')):
          return True
      return False
    for column in columns:
      if not checkMatch(row.get(column, '')):
        return False
    return True

  def rowTextRangeFilterMatch(op, filterTextL, filterTextR):
    def checkMatch(rowText):
      if not isinstance(rowText, str):
        rowText = str(rowText)
      if op == '!=':
        return not filterTextL <= rowText <= filterTextR
      return filterTextL <= rowText <= filterTextR

    if anyMatch:
      for column in columns:
        if checkMatch(row.get(column, '')):
          return True
      return False
    for column in columns:
      if not checkMatch(row.get(column, '')):
        return False
    return True

  def filterMatch(filterVal):
    match filterVal[2]:
      case 'regex':
        return rowRegexFilterMatch(filterVal[3])
      case 'notregex':
        return rowNotRegexFilterMatch(filterVal[3])
      case 'date' | 'time':
        return rowDateTimeFilterMatch(filterVal[2] == 'date', filterVal[3], filterVal[4])
      case 'daterange' | 'timerange':
        return rowDateTimeRangeFilterMatch(filterVal[2] == 'date', filterVal[3], filterVal[4], filterVal[5])
      case 'timeofdayrange':
        return rowTimeOfDayRangeFilterMatch(filterVal[3], filterVal[4], filterVal[5])
      case 'count' | 'number':
        return rowCountFilterMatch(filterVal[3], filterVal[4])
      case 'countrange' | 'numberrange':
        return rowCountRangeFilterMatch(filterVal[3], filterVal[4], filterVal[5])
      case 'length':
        return rowLengthFilterMatch(filterVal[3], filterVal[4])
      case 'lengthrange':
        return rowLengthRangeFilterMatch(filterVal[3], filterVal[4], filterVal[5])
      case 'boolean':
        return rowBooleanFilterMatch(filterVal[3])
      case 'data':
        return rowDataFilterMatch(filterVal[3])
      case 'notdata':
        return rowNotDataFilterMatch(filterVal[3])
      case 'text':
        return rowTextFilterMatch(filterVal[3], filterVal[4])
      case 'textrange':
        return rowTextRangeFilterMatch(filterVal[3], filterVal[4], filterVal[5])
      case _:
        return False

  if rowFilter:
    anyMatches = False
    for filterVal in rowFilter:
      columns = [t for t in titlesList if filterVal[0].match(t)]
      if not columns:
        columns = [None]
      anyMatch = filterVal[1]
      if filterMatch(filterVal):
        if not rowFilterModeAll: # Any - any match selects
          anyMatches = True
          break
      else:
        if rowFilterModeAll: # All - any match failure doesn't select
          return False
    if not rowFilterModeAll and not anyMatches: # Any - no matches doesn't select
      return False
  if rowDropFilter:
    allMatches = True
    for filterVal in rowDropFilter:
      columns = [t for t in titlesList if filterVal[0].match(t)]
      if not columns:
        columns = [None]
      anyMatch = filterVal[1]
      if filterMatch(filterVal):
        if not rowDropFilterModeAll: # Any - any match drops
          return False
      else:
        if rowDropFilterModeAll: # All - any match failure doesn't drop
          allMatches = False
          break
    if rowDropFilterModeAll and allMatches: # All - all matches drops
      return False
  return True

# myarg is command line argument
# fieldChoiceMap maps myarg to API field names
#FIELD_CHOICE_MAP = {
#  'foo': 'foo',
#  'foobar': 'fooBar',
#  }
# fieldsList is the list of API fields
def getFieldsList(myarg, fieldsChoiceMap, fieldsList, initialField=None, fieldsArg='fields', onlyFieldsArg=False):
  def addInitialField():
    if isinstance(initialField, list):
      fieldsList.extend(initialField)
    else:
      fieldsList.append(initialField)

  def addMappedFields(mappedFields):
    if isinstance(mappedFields, list):
      fieldsList.extend(mappedFields)
    else:
      fieldsList.append(mappedFields)

  if not onlyFieldsArg and myarg in fieldsChoiceMap:
    if not fieldsList and initialField is not None:
      addInitialField()
    addMappedFields(fieldsChoiceMap[myarg])
  elif myarg == fieldsArg:
    if not fieldsList and initialField is not None:
      addInitialField()
    for field in _getFieldsList():
      if field in fieldsChoiceMap:
        addMappedFields(fieldsChoiceMap[field])
      else:
        invalidChoiceExit(field, fieldsChoiceMap, True)
  else:
    return False
  return True

def getFieldsFromFieldsList(fieldsList):
  if fieldsList:
    return ','.join(set(fieldsList)).replace('.', '/')
  return None

def getItemFieldsFromFieldsList(item, fieldsList, returnItemIfNoneList=False):
  if fieldsList:
    return f'nextPageToken,{item}({",".join(set(fieldsList))})'.replace('.', '/')
  if not returnItemIfNoneList:
    return None
  return f'nextPageToken,{item}'

class CSVPrintFile:

  def __init__(self, titles=None, sortTitles=None, indexedTitles=None):
    self.rows = []
    self.rowCount = 0
    self.outputTranspose = GM.Globals[GM.CSV_OUTPUT_TRANSPOSE]
    self.todrive = GM.Globals[GM.CSV_TODRIVE]
    self.titlesSet = set()
    self.titlesList = []
    self.JSONtitlesSet = set()
    self.JSONtitlesList = []
    self.sortHeaders = []
    self.SetHeaderForce(GC.Values[GC.CSV_OUTPUT_HEADER_FORCE])
    self.SetHeaderRequired(GC.Values[GC.CSV_OUTPUT_HEADER_REQUIRED])
    if not self.headerForce and titles is not None:
      self.SetTitles(titles)
      self.SetJSONTitles(titles)
    self.SetHeaderOrder(GC.Values[GC.CSV_OUTPUT_HEADER_ORDER])
    if GM.Globals.get(GM.CSV_OUTPUT_COLUMN_DELIMITER) is None:
      GM.Globals[GM.CSV_OUTPUT_COLUMN_DELIMITER] = GC.Values.get(GC.CSV_OUTPUT_COLUMN_DELIMITER, ',')
    self.SetColumnDelimiter(GM.Globals[GM.CSV_OUTPUT_COLUMN_DELIMITER])
    if GM.Globals.get(GM.CSV_OUTPUT_QUOTE_CHAR) is None:
      GM.Globals[GM.CSV_OUTPUT_QUOTE_CHAR] = GC.Values.get(GC.CSV_OUTPUT_QUOTE_CHAR, '"')
    if GM.Globals.get(GM.CSV_OUTPUT_NO_ESCAPE_CHAR) is None:
      GM.Globals[GM.CSV_OUTPUT_NO_ESCAPE_CHAR] = GC.Values.get(GC.CSV_OUTPUT_NO_ESCAPE_CHAR, False)
    self.SetNoEscapeChar(GM.Globals[GM.CSV_OUTPUT_NO_ESCAPE_CHAR])
    self.SetQuoteChar(GM.Globals[GM.CSV_OUTPUT_QUOTE_CHAR])
#    if GM.Globals.get(GM.CSV_OUTPUT_SORT_HEADERS) is None:
    if not GM.Globals.get(GM.CSV_OUTPUT_SORT_HEADERS):
      GM.Globals[GM.CSV_OUTPUT_SORT_HEADERS] = GC.Values.get(GC.CSV_OUTPUT_SORT_HEADERS, [])
    self.SetSortHeaders(GM.Globals[GM.CSV_OUTPUT_SORT_HEADERS])
#    if GM.Globals.get(GM.CSV_OUTPUT_TIMESTAMP_COLUMN) is None:
    if not GM.Globals.get(GM.CSV_OUTPUT_TIMESTAMP_COLUMN):
      GM.Globals[GM.CSV_OUTPUT_TIMESTAMP_COLUMN] = GC.Values.get(GC.CSV_OUTPUT_TIMESTAMP_COLUMN, '')
    self.SetTimestampColumn(GM.Globals[GM.CSV_OUTPUT_TIMESTAMP_COLUMN])
    self.SetFormatJSON(False)
    self.SetNodataFields(False, None, None, None, False)
    self.SetFixPaths(False)
    self.SetShowPermissionsLast(False)
    self.sortTitlesSet = set()
    self.sortTitlesList = []
    if sortTitles is not None:
      if not isinstance(sortTitles, str) or sortTitles != 'sortall':
        self.SetSortTitles(sortTitles)
      else:
        self.SetSortAllTitles()
    self.SetIndexedTitles(indexedTitles if indexedTitles is not None else [])
    self.SetHeaderFilter(GC.Values[GC.CSV_OUTPUT_HEADER_FILTER])
    self.SetHeaderDropFilter(GC.Values[GC.CSV_OUTPUT_HEADER_DROP_FILTER])
    self.SetRowFilter(GC.Values[GC.CSV_OUTPUT_ROW_FILTER], GC.Values[GC.CSV_OUTPUT_ROW_FILTER_MODE])
    self.SetRowDropFilter(GC.Values[GC.CSV_OUTPUT_ROW_DROP_FILTER], GC.Values[GC.CSV_OUTPUT_ROW_DROP_FILTER_MODE])
    self.SetRowLimit(GC.Values[GC.CSV_OUTPUT_ROW_LIMIT])
    self.SetZeroBlankMimeTypeCounts(False)

  def AddTitle(self, title):
    self.titlesSet.add(title)
    self.titlesList.append(title)

  def AddTitles(self, titles):
    for title in titles if isinstance(titles, list) else [titles]:
      if title not in self.titlesSet:
        self.AddTitle(title)

  def InsertTitles(self, position, titles):
    for title in titles if isinstance(titles, list) else [titles]:
      if title not in self.titlesSet:
        self.titlesSet.add(title)
        self.titlesList.insert(position, title)
        position += 1

  def SetTitles(self, titles):
    self.titlesSet = set()
    self.titlesList = []
    self.AddTitles(titles)

  def RemoveTitles(self, titles):
    for title in titles if isinstance(titles, list) else [titles]:
      if title in self.titlesSet:
        self.titlesSet.remove(title)
        self.titlesList.remove(title)

  def MoveTitlesToEnd(self, titles):
    self.RemoveTitles(titles)
    self.AddTitles(titles)

  def MapTitles(self, ov, nv):
    if ov in self.titlesSet:
      self.titlesSet.remove(ov)
      self.titlesSet.add(nv)
      for i, v in enumerate(self.titlesList):
        if v == ov:
          self.titlesList[i] = nv
          break

  def AddSortTitle(self, title):
    self.sortTitlesSet.add(title)
    self.sortTitlesList.append(title)

  def AddSortTitles(self, titles):
    for title in titles if isinstance(titles, list) else [titles]:
      if title not in self.sortTitlesSet:
        self.AddSortTitle(title)

  def SetSortTitles(self, titles):
    self.sortTitlesSet = set()
    self.sortTitlesList = []
    self.AddSortTitles(titles)

  def SetSortAllTitles(self):
    self.sortTitlesList = self.titlesList[:]
    self.sortTitlesSet = set(self.sortTitlesList)

  def AddJSONTitle(self, title):
    self.JSONtitlesSet.add(title)
    self.JSONtitlesList.append(title)

  def AddJSONTitles(self, titles):
    for title in titles if isinstance(titles, list) else [titles]:
      if title not in self.JSONtitlesSet:
        self.AddJSONTitle(title)

  def RemoveJSONTitles(self, titles):
    for title in titles if isinstance(titles, list) else [titles]:
      if title in self.JSONtitlesSet:
        self.JSONtitlesSet.remove(title)
        self.JSONtitlesList.remove(title)

  def MoveJSONTitlesToEnd(self, titles):
    for title in titles if isinstance(titles, list) else [titles]:
      if title in self.JSONtitlesList:
        self.JSONtitlesList.remove(title)
      self.JSONtitlesList.append(title)

  def SetJSONTitles(self, titles):
    self.JSONtitlesSet = set()
    self.JSONtitlesList = []
    self.AddJSONTitles(titles)

# fieldName is command line argument
# fieldNameMap maps fieldName to API field names; CSV file header will be API field name
#ARGUMENT_TO_PROPERTY_MAP = {
#  'admincreated': 'adminCreated',
#  'aliases': ['aliases', 'nonEditableAliases'],
#  }
# fieldsList is the list of API fields
  def AddField(self, fieldName, fieldNameMap, fieldsList):
    fields = fieldNameMap[fieldName.lower()]
    if isinstance(fields, list):
      for field in fields:
        if field not in fieldsList:
          fieldsList.append(field)
          self.AddTitles(field.replace('.', GC.Values[GC.CSV_OUTPUT_SUBFIELD_DELIMITER]))
    elif fields not in fieldsList:
      fieldsList.append(fields)
      self.AddTitles(fields.replace('.', GC.Values[GC.CSV_OUTPUT_SUBFIELD_DELIMITER]))

  def addInitialField(self, initialField, fieldsChoiceMap, fieldsList):
    if isinstance(initialField, list):
      for field in initialField:
        self.AddField(field, fieldsChoiceMap, fieldsList)
    else:
      self.AddField(initialField, fieldsChoiceMap, fieldsList)

  def GetFieldsListTitles(self, fieldName, fieldsChoiceMap, fieldsList, initialField=None):
    if fieldName in fieldsChoiceMap:
      if not fieldsList and initialField is not None:
        self.addInitialField(initialField, fieldsChoiceMap, fieldsList)
      self.AddField(fieldName, fieldsChoiceMap, fieldsList)
    elif fieldName == 'fields':
      if not fieldsList and initialField is not None:
        self.addInitialField(initialField, fieldsChoiceMap, fieldsList)
      for field in _getFieldsList():
        if field in fieldsChoiceMap:
          self.AddField(field, fieldsChoiceMap, fieldsList)
        else:
          invalidChoiceExit(field, fieldsChoiceMap, True)
    else:
      return False
    return True

  TDSHEET_ENTITY_MAP = {'tdsheet': 'sheetEntity', 'tdbackupsheet': 'backupSheetEntity', 'tdcopysheet': 'copySheetEntity'}
  TDSHARE_ACL_ROLES_MAP = {
    'commenter': 'commenter',
    'contributor': 'writer',
    'editor': 'writer',
    'read': 'reader',
    'reader': 'reader',
    'viewer': 'reader',
    'writer': 'writer',
    }


  def GetTodriveParameters(self):
    def invalidTodriveFileIdExit(entityValueList, message, location):
      Cmd.SetLocation(location-1)
      usageErrorExit(formatKeyValueList('', Ent.FormatEntityValueList([Ent.DRIVE_FILE_ID, self.todrive['fileId']]+entityValueList)+[message], ''))

    def invalidTodriveParentExit(entityType, message):
      Cmd.SetLocation(tdparentLocation-1)
      if not localParent:
        usageErrorExit(Msg.INVALID_ENTITY.format(Ent.Singular(entityType),
                                                 formatKeyValueList('',
                                                                    [Ent.Singular(Ent.CONFIG_FILE), GM.Globals[GM.GAM_CFG_FILE],
                                                                     Ent.Singular(Ent.ITEM), GC.TODRIVE_PARENT,
                                                                     Ent.Singular(Ent.VALUE), self.todrive['parent'],
                                                                     message],
                                                                    '')))
      else:
        usageErrorExit(Msg.INVALID_ENTITY.format(Ent.Singular(entityType), message))

    def invalidTodriveUserExit(entityType, message):
      Cmd.SetLocation(tduserLocation-1)
      if not localUser:
        usageErrorExit(Msg.INVALID_ENTITY.format(Ent.Singular(entityType),
                                                 formatKeyValueList('',
                                                                    [Ent.Singular(Ent.CONFIG_FILE), GM.Globals[GM.GAM_CFG_FILE],
                                                                     Ent.Singular(Ent.ITEM), GC.TODRIVE_USER,
                                                                     Ent.Singular(Ent.VALUE), self.todrive['user'],
                                                                     message],
                                                                    '')))
      else:
        usageErrorExit(Msg.INVALID_ENTITY.format(Ent.Singular(entityType), message))

    def getDriveObject():
      if not GC.Values[GC.TODRIVE_CLIENTACCESS]:
        _, drive = buildGAPIServiceObject(chooseSaAPI(API.DRIVETD, API.DRIVE3), self.todrive['user'])
        if not drive:
          invalidTodriveUserExit(Ent.USER, Msg.NOT_FOUND)
      else:
        drive = buildGAPIObject(API.DRIVE3)
      return drive

    CELL_WRAP_MAP = {'clip': 'CLIP', 'overflow': 'OVERFLOW_CELL', 'overflowcell': 'OVERFLOW_CELL', 'wrap': 'WRAP'}
    CELL_NUMBER_FORMAT_MAP = {'text': 'TEXT', 'number': 'NUMBER'}

    localUser = localParent = False
    tdfileidLocation = tdparentLocation = tdaddsheetLocation = tdupdatesheetLocation = tduserLocation = Cmd.Location()
    tdsheetLocation = {}
    for sheetEntity in self.TDSHEET_ENTITY_MAP.values():
      tdsheetLocation[sheetEntity] = Cmd.Location()
    self.todrive = {'user': GC.Values[GC.TODRIVE_USER], 'title': None, 'description': None,
                    'sheetEntity': None, 'addsheet': False, 'updatesheet': False, 'sheettitle': None,
                    'cellwrap': None, 'cellnumberformat': None, 'clearfilter': GC.Values[GC.TODRIVE_CLEARFILTER],
                    'backupSheetEntity': None, 'copySheetEntity': None,
                    'locale': GC.Values[GC.TODRIVE_LOCALE], 'timeZone': GC.Values[GC.TODRIVE_TIMEZONE],
                    'timestamp': GC.Values[GC.TODRIVE_TIMESTAMP], 'timeformat': GC.Values[GC.TODRIVE_TIMEFORMAT],
                    'noescapechar': GC.Values[GC.TODRIVE_NO_ESCAPE_CHAR],
                    'daysoffset': None, 'hoursoffset': None,
                    'sheettimestamp': GC.Values[GC.TODRIVE_SHEET_TIMESTAMP], 'sheettimeformat': GC.Values[GC.TODRIVE_SHEET_TIMEFORMAT],
                    'sheetdaysoffset': None, 'sheethoursoffset': None,
                    'fileId': None, 'parentId': None, 'parent': GC.Values[GC.TODRIVE_PARENT], 'retaintitle': False,
                    'localcopy': GC.Values[GC.TODRIVE_LOCALCOPY], 'uploadnodata': GC.Values[GC.TODRIVE_UPLOAD_NODATA],
                    'nobrowser': GC.Values[GC.TODRIVE_NOBROWSER], 'noemail': GC.Values[GC.TODRIVE_NOEMAIL], 'returnidonly': False,
                    'alert': [], 'share': [], 'notify': False, 'subject': None, 'from': None}
    while Cmd.ArgumentsRemaining():
      myarg = getArgument()
      if myarg == 'tduser':
        self.todrive['user'] = getString(Cmd.OB_EMAIL_ADDRESS)
        tduserLocation = Cmd.Location()
        localUser = True
      elif myarg == 'tdtitle':
        self.todrive['title'] = getString(Cmd.OB_STRING, minLen=0)
      elif myarg == 'tddescription':
        self.todrive['description'] = getString(Cmd.OB_STRING)
      elif myarg in self.TDSHEET_ENTITY_MAP:
        sheetEntity = self.TDSHEET_ENTITY_MAP[myarg]
        tdsheetLocation[sheetEntity] = Cmd.Location()
        self.todrive[sheetEntity] = getSheetEntity(True)
      elif myarg == 'tdaddsheet':
        tdaddsheetLocation = Cmd.Location()
        self.todrive['addsheet'] = getBoolean()
        if self.todrive['addsheet']:
          self.todrive['updatesheet'] = False
      elif myarg == 'tdupdatesheet':
        tdupdatesheetLocation = Cmd.Location()
        self.todrive['updatesheet'] = getBoolean()
        if self.todrive['updatesheet']:
          self.todrive['addsheet'] = False
      elif myarg == 'tdcellwrap':
        self.todrive['cellwrap'] = getChoice(CELL_WRAP_MAP, mapChoice=True)
      elif myarg == 'tdcellnumberformat':
        self.todrive['cellnumberformat'] = getChoice(CELL_NUMBER_FORMAT_MAP, mapChoice=True)
      elif myarg == 'tdclearfilter':
        self.todrive['clearfilter'] = getBoolean()
      elif myarg == 'tdlocale':
        self.todrive['locale'] = getLanguageCode(LOCALE_CODES_MAP)
      elif myarg == 'tdtimezone':
        self.todrive['timeZone'] = getString(Cmd.OB_STRING, minLen=0)
      elif myarg == 'tdtimestamp':
        self.todrive['timestamp'] = getBoolean()
      elif myarg == 'tdtimeformat':
        self.todrive['timeformat'] = getString(Cmd.OB_STRING, minLen=0)
      elif myarg == 'tdsheettitle':
        self.todrive['sheettitle'] = getString(Cmd.OB_STRING, minLen=0)
      elif myarg == 'tdsheettimestamp':
        self.todrive['sheettimestamp'] = getBoolean()
      elif myarg == 'tdsheettimeformat':
        self.todrive['sheettimeformat'] = getString(Cmd.OB_STRING, minLen=0)
      elif myarg == 'tddaysoffset':
        self.todrive['daysoffset'] = getInteger(minVal=0)
      elif myarg == 'tdhoursoffset':
        self.todrive['hoursoffset'] = getInteger(minVal=0)
      elif myarg == 'tdsheetdaysoffset':
        self.todrive['sheetdaysoffset'] = getInteger(minVal=0)
      elif myarg == 'tdsheethoursoffset':
        self.todrive['sheethoursoffset'] = getInteger(minVal=0)
      elif myarg == 'tdfileid':
        self.todrive['fileId'] = getString(Cmd.OB_DRIVE_FILE_ID)
        tdfileidLocation = Cmd.Location()
      elif myarg == 'tdretaintitle':
        self.todrive['retaintitle'] = getBoolean()
      elif myarg == 'tdparent':
        self.todrive['parent'] = escapeDriveFileName(getString(Cmd.OB_DRIVE_FOLDER_NAME, minLen=0))
        tdparentLocation = Cmd.Location()
        localParent = True
      elif myarg == 'tdlocalcopy':
        self.todrive['localcopy'] = getBoolean()
      elif myarg == 'tduploadnodata':
        self.todrive['uploadnodata'] = getBoolean()
      elif myarg == 'tdnobrowser':
        self.todrive['nobrowser'] = getBoolean()
      elif myarg == 'tdnoemail':
        self.todrive['noemail'] = getBoolean()
      elif myarg == 'tdreturnidonly':
        self.todrive['returnidonly'] = getBoolean()
      elif myarg == 'tdnoescapechar':
        self.todrive['noescapechar'] = getBoolean()
      elif myarg == 'tdalert':
        self.todrive['alert'].append({'emailAddress': normalizeEmailAddressOrUID(getString(Cmd.OB_EMAIL_ADDRESS))})
      elif myarg == 'tdshare':
        self.todrive['share'].append({'emailAddress': normalizeEmailAddressOrUID(getString(Cmd.OB_EMAIL_ADDRESS)),
                                      'type': 'user',
                                      'role': getChoice(self.TDSHARE_ACL_ROLES_MAP, mapChoice=True)})
      elif myarg == 'tdnotify':
        self.todrive['notify'] = getBoolean()
      elif myarg == 'tdsubject':
        self.todrive['subject'] = getString(Cmd.OB_STRING, minLen=0)
      elif myarg == 'tdfrom':
        self.todrive['from'] = getString(Cmd.OB_EMAIL_ADDRESS)
      else:
        Cmd.Backup()
        break
    if self.todrive['addsheet']:
      if not self.todrive['fileId']:
        Cmd.SetLocation(tdaddsheetLocation-1)
        missingArgumentExit('tdfileid')
      if self.todrive['sheetEntity'] and self.todrive['sheetEntity']['sheetId']:
        Cmd.SetLocation(tdsheetLocation[sheetEntity]-1)
        invalidArgumentExit('tdsheet <String>')
    if self.todrive['updatesheet'] and (not self.todrive['fileId'] or not self.todrive['sheetEntity']):
      Cmd.SetLocation(tdupdatesheetLocation-1)
      missingArgumentExit('tdfileid and tdsheet')
    if self.todrive['sheetEntity'] and self.todrive['sheetEntity']['sheetId'] and (not self.todrive['fileId'] or not self.todrive['updatesheet']):
      Cmd.SetLocation(tdsheetLocation['sheetEntity']-1)
      missingArgumentExit('tdfileid and tdupdatesheet')
    if not self.todrive['user'] or GC.Values[GC.TODRIVE_CLIENTACCESS]:
      self.todrive['user'] = _getAdminEmail()
    if not GC.Values[GC.USER_SERVICE_ACCOUNT_ACCESS_ONLY] and not GC.Values[GC.TODRIVE_CLIENTACCESS]:
      user = checkUserExists(buildGAPIObject(API.DIRECTORY), self.todrive['user'])
      if not user:
        invalidTodriveUserExit(Ent.USER, Msg.NOT_FOUND)
      self.todrive['user'] = user
    else:
      self.todrive['user'] = normalizeEmailAddressOrUID(self.todrive['user'])
    if self.todrive['fileId']:
      drive = getDriveObject()
      try:
        result = callGAPI(drive.files(), 'get',
                          throwReasons=GAPI.DRIVE_GET_THROW_REASONS,
                          fileId=self.todrive['fileId'], fields='id,mimeType,capabilities(canEdit)', supportsAllDrives=True)
        if result['mimeType'] == MIMETYPE_GA_FOLDER:
          invalidTodriveFileIdExit([], Msg.NOT_AN_ENTITY.format(Ent.Singular(Ent.DRIVE_FILE)), tdfileidLocation)
        if not result['capabilities']['canEdit']:
          invalidTodriveFileIdExit([], Msg.NOT_WRITABLE, tdfileidLocation)
        if self.todrive['sheetEntity']:
          if result['mimeType'] != MIMETYPE_GA_SPREADSHEET:
            invalidTodriveFileIdExit([], f'{Msg.NOT_A} {Ent.Singular(Ent.SPREADSHEET)}', tdfileidLocation)
          if not GC.Values[GC.TODRIVE_CLIENTACCESS]:
            _, sheet = buildGAPIServiceObject(chooseSaAPI(API.SHEETSTD, API.SHEETS), self.todrive['user'])
            if sheet is None:
              invalidTodriveUserExit(Ent.USER, Msg.NOT_FOUND)
          else:
            sheet = buildGAPIObject(API.SHEETS)
          try:
            spreadsheet = callGAPI(sheet.spreadsheets(), 'get',
                                   throwReasons=GAPI.SHEETS_ACCESS_THROW_REASONS,
                                   spreadsheetId=self.todrive['fileId'],
                                   fields='spreadsheetUrl,sheets(properties(sheetId,title),protectedRanges(range(sheetId),requestingUserCanEdit))')
            for sheetEntity in self.TDSHEET_ENTITY_MAP.values():
              if self.todrive[sheetEntity]:
                sheetId = getSheetIdFromSheetEntity(spreadsheet, self.todrive[sheetEntity])
                if sheetId is None:
                  if not self.todrive['addsheet'] and ((sheetEntity != 'sheetEntity') or (self.todrive[sheetEntity]['sheetType'] == Ent.SHEET_ID)):
                    invalidTodriveFileIdExit([self.todrive[sheetEntity]['sheetType'], self.todrive[sheetEntity]['sheetValue']], Msg.NOT_FOUND, tdsheetLocation[sheetEntity])
                else:
                  if self.todrive['addsheet']:
                    invalidTodriveFileIdExit([self.todrive[sheetEntity]['sheetType'], self.todrive[sheetEntity]['sheetValue']], Msg.ALREADY_EXISTS, tdsheetLocation[sheetEntity])
                  if protectedSheetId(spreadsheet, sheetId):
                    invalidTodriveFileIdExit([self.todrive[sheetEntity]['sheetType'], self.todrive[sheetEntity]['sheetValue']], Msg.NOT_WRITABLE, tdsheetLocation[sheetEntity])
                self.todrive[sheetEntity]['sheetId'] = sheetId
          except (GAPI.notFound, GAPI.forbidden, GAPI.permissionDenied,
                  GAPI.internalError, GAPI.insufficientFilePermissions, GAPI.badRequest,
                  GAPI.invalid, GAPI.invalidArgument, GAPI.failedPrecondition) as e:
            invalidTodriveFileIdExit([], str(e), tdfileidLocation)
      except GAPI.fileNotFound:
        invalidTodriveFileIdExit([], Msg.NOT_FOUND, tdfileidLocation)
      except (GAPI.serviceNotAvailable, GAPI.authError, GAPI.domainPolicy) as e:
        invalidTodriveUserExit(Ent.USER, str(e))
    elif not self.todrive['parent'] or self.todrive['parent'] == ROOT:
      self.todrive['parentId'] = ROOT
    else:
      drive = getDriveObject()
      if self.todrive['parent'].startswith('id:'):
        try:
          result = callGAPI(drive.files(), 'get',
                            throwReasons=GAPI.DRIVE_USER_THROW_REASONS+[GAPI.FILE_NOT_FOUND, GAPI.INVALID],
                            fileId=self.todrive['parent'][3:], fields='id,mimeType,capabilities(canEdit)', supportsAllDrives=True)
        except GAPI.fileNotFound:
          invalidTodriveParentExit(Ent.DRIVE_FOLDER_ID, Msg.NOT_FOUND)
        except GAPI.invalid as e:
          invalidTodriveParentExit(Ent.DRIVE_FOLDER_ID, str(e))
        except (GAPI.serviceNotAvailable, GAPI.authError, GAPI.domainPolicy) as e:
          invalidTodriveUserExit(Ent.USER, str(e))
        if result['mimeType'] != MIMETYPE_GA_FOLDER:
          invalidTodriveParentExit(Ent.DRIVE_FOLDER_ID, Msg.NOT_AN_ENTITY.format(Ent.Singular(Ent.DRIVE_FOLDER)))
        if not result['capabilities']['canEdit']:
          invalidTodriveParentExit(Ent.DRIVE_FOLDER_ID, Msg.NOT_WRITABLE)
        self.todrive['parentId'] = result['id']
      else:
        try:
          results = callGAPIpages(drive.files(), 'list', 'files',
                                  throwReasons=GAPI.DRIVE_USER_THROW_REASONS+[GAPI.INVALID_QUERY],
                                  retryReasons=[GAPI.UNKNOWN_ERROR],
                                  q=f"name = '{self.todrive['parent']}'",
                                  fields='nextPageToken,files(id,mimeType,capabilities(canEdit))',
                                  pageSize=1, supportsAllDrives=True)
        except GAPI.invalidQuery:
          invalidTodriveParentExit(Ent.DRIVE_FOLDER_NAME, Msg.NOT_FOUND)
        except (GAPI.serviceNotAvailable, GAPI.authError, GAPI.domainPolicy) as e:
          invalidTodriveUserExit(Ent.USER, str(e))
        if not results:
          invalidTodriveParentExit(Ent.DRIVE_FOLDER_NAME, Msg.NOT_FOUND)
        if results[0]['mimeType'] != MIMETYPE_GA_FOLDER:
          invalidTodriveParentExit(Ent.DRIVE_FOLDER_NAME, Msg.NOT_AN_ENTITY.format(Ent.Singular(Ent.DRIVE_FOLDER)))
        if not results[0]['capabilities']['canEdit']:
          invalidTodriveParentExit(Ent.DRIVE_FOLDER_NAME, Msg.NOT_WRITABLE)
        self.todrive['parentId'] = results[0]['id']

  def SortTitles(self):
    if not self.sortTitlesList:
      return
    restoreTitles = []
    for title in self.sortTitlesList:
      if title in self.titlesSet:
        self.titlesList.remove(title)
        restoreTitles.append(title)
    self.titlesList.sort()
    for title in restoreTitles[::-1]:
      self.titlesList.insert(0, title)

  def RemoveIndexedTitles(self, titles):
    for title in titles if isinstance(titles, list) else [titles]:
      if title in self.indexedTitles:
        self.indexedTitles.remove(title)

  def SetIndexedTitles(self, indexedTitles):
    self.indexedTitles = indexedTitles

  def SortIndexedTitles(self, titlesList):
    for field in self.indexedTitles:
      fieldDotN = re.compile(fr'({field}){GC.Values[GC.CSV_OUTPUT_SUBFIELD_DELIMITER]}(\d+)(.*)')
      indexes = []
      subtitles = []
      for i, v in enumerate(titlesList):
        mg = fieldDotN.match(v)
        if mg:
          indexes.append(i)
          subtitles.append(mg.groups(''))
      for i, ii in enumerate(indexes):
        titlesList[ii] = [f'{subtitle[0]}{GC.Values[GC.CSV_OUTPUT_SUBFIELD_DELIMITER]}{subtitle[1]}{subtitle[2]}' for subtitle in sorted(subtitles, key=lambda k: (int(k[1]), k[2]))][i]

  @staticmethod
  def FixPathsTitles(titlesList):
# Put paths before path.0
    try:
      index = titlesList.index(f'path{GC.Values[GC.CSV_OUTPUT_SUBFIELD_DELIMITER]}0')
      titlesList.remove('paths')
      titlesList.insert(index, 'paths')
    except ValueError:
      pass

  def FixNodataTitles(self):
    if self.mapNodataFields:
      titles = []
      addPermissionsTitle = not self.oneItemPerRow
      for field in self.nodataFields:
        if field.find('(') != -1:
          field, subFields = field.split('(', 1)
          if field in self.driveListFields:
            if field != 'permissions':
              titles.append(field)
            elif addPermissionsTitle:
              titles.append(field)
              addPermissionsTitle = False
            titles.extend([f'{field}{GC.Values[GC.CSV_OUTPUT_SUBFIELD_DELIMITER]}0{GC.Values[GC.CSV_OUTPUT_SUBFIELD_DELIMITER]}{subField}' for subField in subFields[:-1].split(',') if subField])
          else:
            titles.extend([f'{field}{GC.Values[GC.CSV_OUTPUT_SUBFIELD_DELIMITER]}{subField}' for subField in subFields[:-1].split(',') if subField])
        elif field.find('.') != -1:
          field, subField = field.split('.', 1)
          if field in self.driveListFields:
            if field != 'permissions':
              titles.append(field)
            elif addPermissionsTitle:
              titles.append(field)
              addPermissionsTitle = False
            titles.append(f'{field}{GC.Values[GC.CSV_OUTPUT_SUBFIELD_DELIMITER]}0{GC.Values[GC.CSV_OUTPUT_SUBFIELD_DELIMITER]}{subField}')
          else:
            titles.append(f'{field}{GC.Values[GC.CSV_OUTPUT_SUBFIELD_DELIMITER]}{subField}')
        elif field.lower() in self.driveSubfieldsChoiceMap:
          if field in self.driveListFields:
            if field != 'permissions':
              titles.append(field)
            elif addPermissionsTitle:
              titles.append(field)
              addPermissionsTitle = False
            for subField in self.driveSubfieldsChoiceMap[field.lower()].values():
              if not isinstance(subField, list):
                titles.append(f'{field}{GC.Values[GC.CSV_OUTPUT_SUBFIELD_DELIMITER]}0{GC.Values[GC.CSV_OUTPUT_SUBFIELD_DELIMITER]}{subField}')
              else:
                titles.extend([f'{field}{GC.Values[GC.CSV_OUTPUT_SUBFIELD_DELIMITER]}0{GC.Values[GC.CSV_OUTPUT_SUBFIELD_DELIMITER]}{subSubField}' for subSubField in subField])
          else:
            for subField in self.driveSubfieldsChoiceMap[field.lower()].values():
              if not isinstance(subField, list):
                titles.append(f'{field}{GC.Values[GC.CSV_OUTPUT_SUBFIELD_DELIMITER]}{subField}')
              else:
                titles.extend([f'{field}{GC.Values[GC.CSV_OUTPUT_SUBFIELD_DELIMITER]}{subSubField}' for subSubField in subField])
        else:
          titles.append(field)
        if self.oneItemPerRow:
          for i, title in enumerate(titles):
            if title.startswith('permissions.0'):
              titles[i] = title.replace('permissions.0', 'permission')
      if not self.formatJSON:
        self.SetTitles(titles)
        self.SetSortTitles(['Owner', 'id', 'name', 'title'])
        self.SortTitles()
      else:
        self.SetJSONTitles(titles)
    else:
      self.SetTitles(self.nodataFields)
      self.SetJSONTitles(self.nodataFields)

  def MovePermsToEnd(self):
# Put permissions at end of titles
    try:
      last = len(self.titlesList)
      start = end = self.titlesList.index('permissions')
      while end < last and self.titlesList[end].startswith('permissions'):
        end += 1
      self.titlesList = self.titlesList[:start]+self.titlesList[end:]+self.titlesList[start:end]
    except ValueError:
      pass

  def SetColumnDelimiter(self, columnDelimiter):
    self.columnDelimiter = columnDelimiter

  def SetNoEscapeChar(self, noEscapeChar):
    self.noEscapeChar = noEscapeChar

  def SetQuoteChar(self, quoteChar):
    self.quoteChar = quoteChar

  def SetTimestampColumn(self, timestampColumn):
    self.timestampColumn = timestampColumn
    if not GC.Values[GC.OUTPUT_TIMEFORMAT]:
      self.todaysTime = ISOformatTimeStamp(todaysTime())
    else:
      self.todaysTime = todaysTime().strftime(GC.Values[GC.OUTPUT_TIMEFORMAT])

  def SetSortHeaders(self, sortHeaders):
    self.sortHeaders = sortHeaders

  def SetFormatJSON(self, formatJSON):
    self.formatJSON = formatJSON

  def SetNodataFields(self, mapNodataFields, nodataFields, driveListFields, driveSubfieldsChoiceMap, oneItemPerRow):
    self.mapNodataFields = mapNodataFields
    self.nodataFields = nodataFields
    self.driveListFields = driveListFields
    self.driveSubfieldsChoiceMap = driveSubfieldsChoiceMap
    self.oneItemPerRow = oneItemPerRow

  def SetFixPaths(self, fixPaths):
    self.fixPaths = fixPaths

  def SetShowPermissionsLast(self, showPermissionsLast):
    self.showPermissionsLast = showPermissionsLast

  def FixCourseAliasesTitles(self):
# Put Aliases.* after Aliases
    try:
      aliasesIndex = self.sortTitlesList.index('Aliases')
      index = self.titlesList.index('Aliases.0')
      tempSortTitlesList = self.sortTitlesList[:]
      self.SetSortTitles(tempSortTitlesList[:aliasesIndex+1])
      while self.titlesList[index].startswith('Aliases.'):
        self.AddSortTitle(self.titlesList[index])
        index += 1
      self.AddSortTitles(tempSortTitlesList[aliasesIndex+1:])
    except ValueError:
      pass

  def RearrangeCourseTitles(self, ttitles, stitles):
# Put teachers and students after courseMaterialSets if present, otherwise at end
    for title in ttitles['list']:
      if title in self.titlesList:
        self.titlesList.remove(title)
    for title in stitles['list']:
      if title in self.titlesList:
        self.titlesList.remove(title)
    try:
      cmsIndex = self.titlesList.index('courseMaterialSets')
      self.titlesList = self.titlesList[:cmsIndex]+ttitles['list']+stitles['list']+self.titlesList[cmsIndex:]
    except ValueError:
      self.titlesList.extend(ttitles['list'])
      self.titlesList.extend(stitles['list'])

  def SortRows(self, title, reverse):
    if title in self.titlesSet:
      self.rows.sort(key=lambda k: k[title], reverse=reverse)

  def SortRowsTwoTitles(self, title1, title2, reverse):
    if title1 in self.titlesSet and title2 in self.titlesSet:
      self.rows.sort(key=lambda k: (k[title1], k[title2]), reverse=reverse)

  def SetRowFilter(self, rowFilter, rowFilterMode):
    self.rowFilter = rowFilter
    self.rowFilterMode = rowFilterMode

  def SetRowDropFilter(self, rowDropFilter, rowDropFilterMode):
    self.rowDropFilter = rowDropFilter
    self.rowDropFilterMode = rowDropFilterMode

  def SetRowLimit(self, rowLimit):
    self.rowLimit = rowLimit

  def AppendRow(self, row):
    if self.timestampColumn:
      row[self.timestampColumn] = self.todaysTime
    if not self.rowLimit or self.rowCount < self.rowLimit:
      self.rowCount +=1
      self.rows.append(row)

  def WriteRowNoFilter(self, row):
    self.AppendRow(row)

  def WriteRow(self, row):
    if RowFilterMatch(row, self.titlesList, self.rowFilter, self.rowFilterMode, self.rowDropFilter, self.rowDropFilterMode):
      self.AppendRow(row)

  def WriteRowTitles(self, row):
    for title in row:
      if title not in self.titlesSet:
        self.AddTitle(title)
    if RowFilterMatch(row, self.titlesList, self.rowFilter, self.rowFilterMode, self.rowDropFilter, self.rowDropFilterMode):
      self.AppendRow(row)

  def WriteRowTitlesNoFilter(self, row):
    for title in row:
      if title not in self.titlesSet:
        self.AddTitle(title)
    self.AppendRow(row)

  def WriteRowTitlesJSONNoFilter(self, row):
    for title in row:
      if title not in self.JSONtitlesSet:
        self.AddJSONTitle(title)
    self.AppendRow(row)

  def CheckRowTitles(self, row):
    if not self.rowFilter and not self.rowDropFilter:
      return True
    for title in row:
      if title not in self.titlesSet:
        self.AddTitle(title)
    return RowFilterMatch(row, self.titlesList, self.rowFilter, self.rowFilterMode, self.rowDropFilter, self.rowDropFilterMode)

  def UpdateMimeTypeCounts(self, row, mimeTypeInfo, sizeField):
    saveList = self.titlesList[:]
    saveSet = set(self.titlesSet)
    for title in row:
      if title not in self.titlesSet:
        self.AddTitle(title)
    if RowFilterMatch(row, self.titlesList, self.rowFilter, self.rowFilterMode, self.rowDropFilter, self.rowDropFilterMode):
      mimeTypeInfo.setdefault(row['mimeType'], {'count': 0, 'size': 0})
      mimeTypeInfo[row['mimeType']]['count'] += 1
      mimeTypeInfo[row['mimeType']]['size'] += int(row.get(sizeField, '0'))
    self.titlesList = saveList[:]
    self.titlesSet = set(saveSet)

  def SetZeroBlankMimeTypeCounts(self, zeroBlankMimeTypeCounts):
    self.zeroBlankMimeTypeCounts = zeroBlankMimeTypeCounts

  def ZeroBlankMimeTypeCounts(self):
    for row in self.rows:
      for title in self.titlesList:
        if title not in self.sortTitlesSet and title not in row:
          row[title] = 0

  def CheckOutputRowFilterHeaders(self):
    for filterVal in self.rowFilter:
      columns = [t for t in self.titlesList if filterVal[0].match(t)]
      if not columns:
        stderrWarningMsg(Msg.COLUMN_DOES_NOT_MATCH_ANY_OUTPUT_COLUMNS.format(GC.CSV_OUTPUT_ROW_FILTER, filterVal[0].pattern))
    for filterVal in self.rowDropFilter:
      columns = [t for t in self.titlesList if filterVal[0].match(t)]
      if not columns:
        stderrWarningMsg(Msg.COLUMN_DOES_NOT_MATCH_ANY_OUTPUT_COLUMNS.format(GC.CSV_OUTPUT_ROW_DROP_FILTER, filterVal[0].pattern))

  def SetHeaderFilter(self, headerFilter):
    self.headerFilter = headerFilter

  def SetHeaderDropFilter(self, headerDropFilter):
    self.headerDropFilter = headerDropFilter

  def SetHeaderForce(self, headerForce):
    self.headerForce = headerForce
    self.SetTitles(headerForce)
    self.SetJSONTitles(headerForce)

  def SetHeaderRequired(self, headerRequired):
    self.headerRequired = headerRequired

  def SetHeaderOrder(self, headerOrder):
    self.headerOrder = headerOrder

  def orderHeaders(self, titlesList):
    for title in self.headerOrder:
      if title in titlesList:
        titlesList.remove(title)
    return self.headerOrder+titlesList

  @staticmethod
  def HeaderFilterMatch(filters, title):
    for filterStr in filters:
      if filterStr.match(title):
        return True
    return False

  def FilterHeaders(self):
    if self.headerDropFilter:
      self.titlesList = [t for t in self.titlesList if not self.HeaderFilterMatch(self.headerDropFilter, t)]
    if self.headerFilter:
      self.titlesList = [t for t in self.titlesList if self.HeaderFilterMatch(self.headerFilter, t)]
    self.titlesSet = set(self.titlesList)
    if not self.titlesSet:
      systemErrorExit(USAGE_ERROR_RC, Msg.NO_COLUMNS_SELECTED_WITH_CSV_OUTPUT_HEADER_FILTER.format(GC.CSV_OUTPUT_HEADER_FILTER, GC.CSV_OUTPUT_HEADER_DROP_FILTER))

  def FilterJSONHeaders(self):
    if self.headerDropFilter:
      self.JSONtitlesList = [t for t in self.JSONtitlesList if not self.HeaderFilterMatch(self.headerDropFilter, t)]
    if self.headerFilter:
      self.JSONtitlesList = [t for t in self.JSONtitlesList if self.HeaderFilterMatch(self.headerFilter, t)]
    self.JSONtitlesSet = set(self.JSONtitlesList)
    if not self.JSONtitlesSet:
      systemErrorExit(USAGE_ERROR_RC, Msg.NO_COLUMNS_SELECTED_WITH_CSV_OUTPUT_HEADER_FILTER.format(GC.CSV_OUTPUT_HEADER_FILTER, GC.CSV_OUTPUT_HEADER_DROP_FILTER))

  @staticmethod
  def _todriveCSVErrorExit(entityValueList, errMsg):
    systemErrorExit(ACTION_FAILED_RC, formatKeyValueList(Ind.Spaces(),
                                                         Ent.FormatEntityValueList(entityValueList)+[Act.NotPerformed(), errMsg],
                                                         currentCountNL(0, 0)))

  @staticmethod
  def _itemgetter(*items):
    if len(items) == 1:
      item = items[0]
      def g(obj):
        return obj.get(item, '')
    else:
      def g(obj):
        return tuple(obj.get(item, '') for item in items)
    return g

  def _writeCSVData(self, writer, titlesList, extrasaction):
    try:
      if not self.outputTranspose:
        if GM.Globals[GM.CSVFILE][GM.REDIRECT_WRITE_HEADER]:
          writer.writerow(dict((item, item) for item in writer.fieldnames))
        if not self.sortHeaders:
          writer.writerows(self.rows)
        else:
          for row in sorted(self.rows, key=self._itemgetter(*self.sortHeaders)):
            writer.writerow(row)
      else:
        writer.writerows(self.rows)
      return True
    except IOError as e:
      stderrErrorMsg(e)
      return False

  def _setDialect(self, lineterminator, noEscapeChar):
    writerDialect = {
      'delimiter': self.columnDelimiter,
      'doublequote': True,
      'escapechar': '\\' if not noEscapeChar else None,
      'lineterminator': lineterminator,
      'quotechar': self.quoteChar,
      'quoting': csv.QUOTE_MINIMAL,
      'skipinitialspace': False,
      'strict': False}
    return writerDialect

  def _normalizeSortHeaders(self, titlesList):
    if self.sortHeaders:
      writerKeyMap = {}
      for k in titlesList:
        writerKeyMap[k.lower()] = k
      self.sortHeaders = [writerKeyMap[k.lower()] for k in self.sortHeaders if k.lower() in writerKeyMap]

  def _writeCSVToStdout(self, titlesList, extrasaction):
    csvFile = StringIOobject()
    writerDialect = self._setDialect('\n', self.noEscapeChar)
    writer = csv.DictWriter(csvFile, titlesList, extrasaction=extrasaction, **writerDialect)
    if self._writeCSVData(writer, titlesList, extrasaction):
      try:
        GM.Globals[GM.STDOUT][GM.REDIRECT_MULTI_FD].write(csvFile.getvalue())
      except IOError as e:
        stderrErrorMsg(fdErrorMessage(GM.Globals[GM.STDOUT][GM.REDIRECT_MULTI_FD], 'stdout', e))
        setSysExitRC(FILE_ERROR_RC)
    closeFile(csvFile)

  def _writeCSVToFile(self, titlesList, extrasaction):
    csvFile = GM.Globals[GM.CSVFILE].get(GM.REDIRECT_FD, None)
    if not csvFile:
      csvFile = openFile(GM.Globals[GM.CSVFILE][GM.REDIRECT_NAME], GM.Globals[GM.CSVFILE][GM.REDIRECT_MODE], newline='',
                         encoding=GM.Globals[GM.CSVFILE][GM.REDIRECT_ENCODING], errors='backslashreplace',
                         continueOnError=True)
    if csvFile:
      writerDialect = self._setDialect(str(GC.Values[GC.CSV_OUTPUT_LINE_TERMINATOR]), self.noEscapeChar)
      writer = csv.DictWriter(csvFile, titlesList, extrasaction=extrasaction, **writerDialect)
      self._writeCSVData(writer, titlesList, extrasaction)
      closeFile(csvFile)

  def _writeCSVToDrive(self, list_type, titlesList, extrasaction):
    numRows = len(self.rows)
    numColumns = len(titlesList)
    if numRows == 0 and not self.todrive['uploadnodata']:
      printKeyValueList([Msg.NO_CSV_DATA_TO_UPLOAD])
      setSysExitRC(NO_CSV_DATA_TO_UPLOAD_RC)
      return
    if self.todrive['addsheet'] or self.todrive['updatesheet']:
      csvFile = TemporaryFile(mode='w+', encoding=UTF8)
    else:
      csvFile = StringIOobject()
    writerDialect = self._setDialect('\n', self.todrive['noescapechar'])
    writer = csv.DictWriter(csvFile, titlesList, extrasaction=extrasaction, **writerDialect)
    if self._writeCSVData(writer, titlesList, extrasaction):
      if ((self.todrive['title'] is None) or
           (not self.todrive['title'] and not self.todrive['timestamp'])):
        title = f'{GC.Values[GC.DOMAIN]} - {list_type}'
      else:
        title = self.todrive['title']
      if ((self.todrive['sheettitle'] is None) or
          (not self.todrive['sheettitle'] and not self.todrive['sheettimestamp'])):
        if ((self.todrive['sheetEntity'] is None) or
            (not self.todrive['sheetEntity']['sheetTitle'])):
          sheetTitle = title
        else:
          sheetTitle = self.todrive['sheetEntity']['sheetTitle']
      else:
        sheetTitle = self.todrive['sheettitle']
      tdbasetime = tdtime = arrow.now(GC.Values[GC.TIMEZONE])
      if self.todrive['daysoffset'] is not None or self.todrive['hoursoffset'] is not None:
        tdtime = tdbasetime.shift(days=-self.todrive['daysoffset'] if self.todrive['daysoffset'] is not None else 0,
                                  hours=-self.todrive['hoursoffset'] if self.todrive['hoursoffset'] is not None else 0)
      if self.todrive['timestamp']:
        if title:
          title += ' - '
        if not self.todrive['timeformat']:
          title += ISOformatTimeStamp(tdtime)
        else:
          title += tdtime.strftime(self.todrive['timeformat'])
      if self.todrive['sheettimestamp']:
        if self.todrive['sheetdaysoffset'] is not None or self.todrive['sheethoursoffset'] is not None:
          tdtime = tdbasetime.shift(days=-self.todrive['sheetdaysoffset'] if self.todrive['sheetdaysoffset'] is not None else 0,
                                    hours=-self.todrive['sheethoursoffset'] if self.todrive['sheethoursoffset'] is not None else 0)
        if sheetTitle:
          sheetTitle += ' - '
        if not self.todrive['sheettimeformat']:
          sheetTitle += ISOformatTimeStamp(tdtime)
        else:
          sheetTitle += tdtime.strftime(self.todrive['sheettimeformat'])
      action = Act.Get()
      if not GC.Values[GC.TODRIVE_CLIENTACCESS]:
        user, drive = buildGAPIServiceObject(chooseSaAPI(API.DRIVETD, API.DRIVE3), self.todrive['user'])
        if not drive:
          closeFile(csvFile)
          return
      else:
        user = self.todrive['user']
        drive = buildGAPIObject(API.DRIVE3)
      importSize = csvFile.tell()
# Add/Update sheet
      try:
        if self.todrive['addsheet'] or self.todrive['updatesheet']:
          Act.Set(Act.CREATE if self.todrive['addsheet'] else Act.UPDATE)
          result = callGAPI(drive.about(), 'get',
                            throwReasons=GAPI.DRIVE_USER_THROW_REASONS,
                            fields='maxImportSizes')
          if numRows*numColumns > MAX_GOOGLE_SHEET_CELLS or importSize > int(result['maxImportSizes'][MIMETYPE_GA_SPREADSHEET]):
            self._todriveCSVErrorExit([Ent.USER, user], Msg.RESULTS_TOO_LARGE_FOR_GOOGLE_SPREADSHEET)
          fields = ','.join(['id', 'mimeType', 'webViewLink', 'name', 'capabilities(canEdit)'])
          body = {'description': self.todrive['description']}
          if body['description'] is None:
            body['description'] = Cmd.QuotedArgumentList(Cmd.AllArguments())
          if not self.todrive['retaintitle']:
            body['name'] = title
          result = callGAPI(drive.files(), 'update',
                            throwReasons=GAPI.DRIVE_USER_THROW_REASONS+[GAPI.INSUFFICIENT_PERMISSIONS, GAPI.INSUFFICIENT_PARENT_PERMISSIONS,
                                                                        GAPI.FILE_NOT_FOUND, GAPI.UNKNOWN_ERROR],
                            fileId=self.todrive['fileId'], body=body, fields=fields, supportsAllDrives=True)
          entityValueList = [Ent.USER, user, Ent.DRIVE_FILE_ID, self.todrive['fileId']]
          if not result['capabilities']['canEdit']:
            self._todriveCSVErrorExit(entityValueList, Msg.NOT_WRITABLE)
          if result['mimeType'] != MIMETYPE_GA_SPREADSHEET:
            self._todriveCSVErrorExit(entityValueList, f'{Msg.NOT_A} {Ent.Singular(Ent.SPREADSHEET)}')
          if not GC.Values[GC.TODRIVE_CLIENTACCESS]:
            _, sheet = buildGAPIServiceObject(chooseSaAPI(API.SHEETSTD, API.SHEETS), user)
            if sheet is None:
              return
          else:
            sheet = buildGAPIObject(API.SHEETS)
          csvFile.seek(0)
          spreadsheet = None
          if self.todrive['updatesheet']:
            for sheetEntity in self.TDSHEET_ENTITY_MAP.values():
              if self.todrive[sheetEntity]:
                entityValueList = [Ent.USER, user, Ent.SPREADSHEET, title, self.todrive[sheetEntity]['sheetType'], self.todrive[sheetEntity]['sheetValue']]
                if spreadsheet is None:
                  spreadsheet = callGAPI(sheet.spreadsheets(), 'get',
                                         throwReasons=GAPI.SHEETS_ACCESS_THROW_REASONS,
                                         spreadsheetId=self.todrive['fileId'],
                                         fields='spreadsheetUrl,sheets(properties(sheetId,title),protectedRanges(range(sheetId),requestingUserCanEdit))')
                sheetId = getSheetIdFromSheetEntity(spreadsheet, self.todrive[sheetEntity])
                if sheetId is None:
                  if ((sheetEntity != 'sheetEntity') or (self.todrive[sheetEntity]['sheetType'] == Ent.SHEET_ID)):
                    self._todriveCSVErrorExit(entityValueList, Msg.NOT_FOUND)
                  self.todrive['addsheet'] = True
                else:
                  if protectedSheetId(spreadsheet, sheetId):
                    self._todriveCSVErrorExit(entityValueList, Msg.NOT_WRITABLE)
                  self.todrive[sheetEntity]['sheetId'] = sheetId
          if self.todrive['addsheet']:
            body = {'requests': [{'addSheet': {'properties': {'title': sheetTitle, 'sheetType': 'GRID'}}}]}
            try:
              addresult = callGAPI(sheet.spreadsheets(), 'batchUpdate',
                                   throwReasons=GAPI.SHEETS_ACCESS_THROW_REASONS,
                                   spreadsheetId=self.todrive['fileId'], body=body)
              self.todrive['sheetEntity'] = {'sheetId': addresult['replies'][0]['addSheet']['properties']['sheetId']}
            except (GAPI.notFound, GAPI.forbidden, GAPI.permissionDenied,
                    GAPI.internalError, GAPI.insufficientFilePermissions, GAPI.insufficientParentPermissions, GAPI.badRequest,
                    GAPI.invalid, GAPI.invalidArgument, GAPI.failedPrecondition) as e:
              self._todriveCSVErrorExit(entityValueList, str(e))
          body = {'requests': []}
          if not self.todrive['addsheet']:
            if self.todrive['backupSheetEntity']:
              body['requests'].append({'copyPaste': {'source': {'sheetId': self.todrive['sheetEntity']['sheetId']},
                                                     'destination': {'sheetId': self.todrive['backupSheetEntity']['sheetId']}, 'pasteType': 'PASTE_NORMAL'}})
            if self.todrive['clearfilter']:
              body['requests'].append({'clearBasicFilter': {'sheetId': self.todrive['sheetEntity']['sheetId']}})
            if self.todrive['sheettitle']:
              body['requests'].append({'updateSheetProperties':
                                         {'properties': {'sheetId': self.todrive['sheetEntity']['sheetId'], 'title': sheetTitle}, 'fields': 'title'}})
          body['requests'].append({'updateCells': {'range': {'sheetId': self.todrive['sheetEntity']['sheetId']}, 'fields': '*'}})
          if self.todrive['cellwrap']:
            body['requests'].append({'repeatCell': {'range': {'sheetId': self.todrive['sheetEntity']['sheetId']},
                                                    'fields': 'userEnteredFormat.wrapStrategy',
                                                    'cell': {'userEnteredFormat': {'wrapStrategy': self.todrive['cellwrap']}}}})
          if self.todrive['cellnumberformat']:
            body['requests'].append({'repeatCell': {'range': {'sheetId': self.todrive['sheetEntity']['sheetId']},
                                                    'fields': 'userEnteredFormat.numberFormat',
                                                    'cell': {'userEnteredFormat': {'numberFormat': {'type': self.todrive['cellnumberformat']}}}}})
          body['requests'].append({'pasteData': {'coordinate': {'sheetId': self.todrive['sheetEntity']['sheetId'], 'rowIndex': '0', 'columnIndex': '0'},
                                                 'data': csvFile.read(), 'type': 'PASTE_NORMAL', 'delimiter': self.columnDelimiter}})
          if self.todrive['copySheetEntity']:
            body['requests'].append({'copyPaste': {'source': {'sheetId': self.todrive['sheetEntity']['sheetId']},
                                                   'destination': {'sheetId': self.todrive['copySheetEntity']['sheetId']}, 'pasteType': 'PASTE_NORMAL'}})
          try:
            callGAPI(sheet.spreadsheets(), 'batchUpdate',
                     throwReasons=GAPI.SHEETS_ACCESS_THROW_REASONS,
                     spreadsheetId=self.todrive['fileId'], body=body)
          except (GAPI.notFound, GAPI.forbidden, GAPI.permissionDenied,
                  GAPI.internalError, GAPI.insufficientFilePermissions, GAPI.badRequest,
                  GAPI.invalid, GAPI.invalidArgument, GAPI.failedPrecondition) as e:
            self._todriveCSVErrorExit(entityValueList, str(e))
          closeFile(csvFile)
# Create/update file
        else:
          if GC.Values[GC.TODRIVE_CONVERSION]:
            result = callGAPI(drive.about(), 'get',
                              throwReasons=GAPI.DRIVE_USER_THROW_REASONS,
                              fields='maxImportSizes')
            if numRows*len(titlesList) > MAX_GOOGLE_SHEET_CELLS or importSize > int(result['maxImportSizes'][MIMETYPE_GA_SPREADSHEET]):
              printKeyValueList([WARNING, Msg.RESULTS_TOO_LARGE_FOR_GOOGLE_SPREADSHEET])
              mimeType = 'text/csv'
            else:
              mimeType = MIMETYPE_GA_SPREADSHEET
          else:
            mimeType = 'text/csv'
          fields = ','.join(['id', 'mimeType', 'webViewLink'])
          body = {'description': self.todrive['description'], 'mimeType': mimeType}
          if body['description'] is None:
            body['description'] = Cmd.QuotedArgumentList(Cmd.AllArguments())
          if not self.todrive['fileId'] or not self.todrive['retaintitle']:
            body['name'] = title
          try:
            if not self.todrive['fileId']:
              Act.Set(Act.CREATE)
              body['parents'] = [self.todrive['parentId']]
              result = callGAPI(drive.files(), 'create',
                                bailOnInternalError=True,
                                throwReasons=GAPI.DRIVE_USER_THROW_REASONS+[GAPI.FORBIDDEN, GAPI.INSUFFICIENT_PERMISSIONS, GAPI.INSUFFICIENT_PARENT_PERMISSIONS,
                                                                            GAPI.FILE_NOT_FOUND, GAPI.UNKNOWN_ERROR, GAPI.INTERNAL_ERROR, GAPI.STORAGE_QUOTA_EXCEEDED,
                                                                            GAPI.TEAMDRIVE_FILE_LIMIT_EXCEEDED, GAPI.TEAMDRIVE_HIERARCHY_TOO_DEEP],
                                body=body,
                                media_body=googleapiclient.http.MediaIoBaseUpload(io.BytesIO(csvFile.getvalue().encode()), mimetype='text/csv', resumable=True),
                                fields=fields, supportsAllDrives=True)
            else:
              Act.Set(Act.UPDATE)
              result = callGAPI(drive.files(), 'update',
                                bailOnInternalError=True,
                                throwReasons=GAPI.DRIVE_USER_THROW_REASONS+[GAPI.INSUFFICIENT_PERMISSIONS, GAPI.INSUFFICIENT_PARENT_PERMISSIONS,
                                                                            GAPI.FILE_NOT_FOUND, GAPI.UNKNOWN_ERROR, GAPI.INTERNAL_ERROR],
                                fileId=self.todrive['fileId'],
                                body=body,
                                media_body=googleapiclient.http.MediaIoBaseUpload(io.BytesIO(csvFile.getvalue().encode()), mimetype='text/csv', resumable=True),
                                fields=fields, supportsAllDrives=True)
            spreadsheetId = result['id']
          except GAPI.internalError as e:
            entityActionFailedWarning([Ent.DRIVE_FILE, body['name']], Msg.UPLOAD_CSV_FILE_INTERNAL_ERROR.format(str(e), str(numRows)))
            closeFile(csvFile)
            return
          closeFile(csvFile)
          if not self.todrive['fileId'] and self.todrive['share']:
            Act.Set(Act.SHARE)
            for share in self.todrive['share']:
              if share['emailAddress'] != user:
                try:
                  callGAPI(drive.permissions(), 'create',
                           bailOnInternalError=True,
                           throwReasons=GAPI.DRIVE_ACCESS_THROW_REASONS+GAPI.DRIVE3_CREATE_ACL_THROW_REASONS,
                           fileId=spreadsheetId, sendNotificationEmail=False, body=share, fields='', supportsAllDrives=True)
                  entityActionPerformed([Ent.USER, user, Ent.SPREADSHEET, title,
                                         Ent.TARGET_USER, share['emailAddress'], Ent.ROLE, share['role']])
                except (GAPI.badRequest, GAPI.invalid, GAPI.fileNotFound, GAPI.forbidden, GAPI.internalError,
                        GAPI.insufficientFilePermissions, GAPI.insufficientParentPermissions, GAPI.unknownError, GAPI.ownershipChangeAcrossDomainNotPermitted,
                        GAPI.teamDriveDomainUsersOnlyRestriction, GAPI.teamDriveTeamMembersOnlyRestriction,
                        GAPI.targetUserRoleLimitedByLicenseRestriction, GAPI.insufficientAdministratorPrivileges, GAPI.sharingRateLimitExceeded,
                        GAPI.publishOutNotPermitted, GAPI.shareInNotPermitted, GAPI.shareOutNotPermitted, GAPI.shareOutNotPermittedToUser,
                        GAPI.cannotShareTeamDriveTopFolderWithAnyoneOrDomains, GAPI.cannotShareTeamDriveWithNonGoogleAccounts,
                        GAPI.ownerOnTeamDriveItemNotSupported,
                        GAPI.organizerOnNonTeamDriveNotSupported, GAPI.organizerOnNonTeamDriveItemNotSupported,
                        GAPI.fileOrganizerNotYetEnabledForThisTeamDrive,
                        GAPI.fileOrganizerOnFoldersInSharedDriveOnly,
                        GAPI.fileOrganizerOnNonTeamDriveNotSupported,
                        GAPI.cannotModifyInheritedPermission,
                        GAPI.teamDrivesFolderSharingNotSupported, GAPI.invalidLinkVisibility,
                        GAPI.invalidSharingRequest, GAPI.fileNeverWritable, GAPI.abusiveContentRestriction) as e:
                  entityActionFailedWarning([Ent.USER, user, Ent.SPREADSHEET, title,
                                             Ent.TARGET_USER, share['emailAddress'], Ent.ROLE, share['role']],
                                            str(e))
          if ((result['mimeType'] == MIMETYPE_GA_SPREADSHEET) and
              (self.todrive['sheetEntity'] or self.todrive['locale'] or self.todrive['timeZone'] or
               self.todrive['sheettitle'] or self.todrive['cellwrap'] or self.todrive['cellnumberformat'])):
            if not GC.Values[GC.TODRIVE_CLIENTACCESS]:
              _, sheet = buildGAPIServiceObject(chooseSaAPI(API.SHEETSTD, API.SHEETS), user)
              if sheet is None:
                return
            else:
              sheet = buildGAPIObject(API.SHEETS)
            try:
              body = {'requests': []}
              if self.todrive['sheetEntity'] or self.todrive['sheettitle'] or self.todrive['cellwrap']:
                spreadsheet = callGAPI(sheet.spreadsheets(), 'get',
                                       throwReasons=GAPI.SHEETS_ACCESS_THROW_REASONS,
                                       spreadsheetId=spreadsheetId, fields='sheets/properties')
                spreadsheet['sheets'][0]['properties']['title'] = sheetTitle
                body['requests'].append({'updateSheetProperties':
                                         {'properties': spreadsheet['sheets'][0]['properties'], 'fields': 'title'}})
                if self.todrive['cellwrap']:
                  body['requests'].append({'repeatCell': {'range': {'sheetId': spreadsheet['sheets'][0]['properties']['sheetId']},
                                                          'fields': 'userEnteredFormat.wrapStrategy',
                                                          'cell': {'userEnteredFormat': {'wrapStrategy': self.todrive['cellwrap']}}}})
              if self.todrive['locale']:
                body['requests'].append({'updateSpreadsheetProperties':
                                           {'properties': {'locale': self.todrive['locale']}, 'fields': 'locale'}})
              if self.todrive['timeZone']:
                body['requests'].append({'updateSpreadsheetProperties':
                                           {'properties': {'timeZone': self.todrive['timeZone']}, 'fields': 'timeZone'}})
              if body['requests']:
                callGAPI(sheet.spreadsheets(), 'batchUpdate',
                         throwReasons=GAPI.SHEETS_ACCESS_THROW_REASONS,
                         spreadsheetId=spreadsheetId, body=body)
            except (GAPI.notFound, GAPI.forbidden, GAPI.permissionDenied,
                    GAPI.internalError, GAPI.insufficientFilePermissions, GAPI.badRequest,
                    GAPI.invalid, GAPI.invalidArgument, GAPI.failedPrecondition,
                    GAPI.teamDriveFileLimitExceeded, GAPI.teamDriveHierarchyTooDeep) as e:
              self._todriveCSVErrorExit([Ent.USER, user, Ent.SPREADSHEET, title], str(e))
        Act.Set(action)
        file_url = result['webViewLink']
        msg_txt = f'{Msg.DATA_UPLOADED_TO_DRIVE_FILE}:\n{file_url}'
        if not self.todrive['returnidonly']:
          printKeyValueList([msg_txt])
        else:
          if self.todrive['fileId']:
            writeStdout(f'{self.todrive["fileId"]}\n')
          else:
            writeStdout(f'{spreadsheetId}\n')
        if not self.todrive['subject']:
          subject = title
        else:
          subject = self.todrive['subject'].replace('#file#', title).replace('#sheet#', sheetTitle)
        if not self.todrive['noemail']:
          send_email(subject, msg_txt, user, clientAccess=GC.Values[GC.TODRIVE_CLIENTACCESS], msgFrom=self.todrive['from'])
        if self.todrive['notify']:
          for recipient in self.todrive['share']+self.todrive['alert']:
            if recipient['emailAddress'] != user:
              send_email(subject, msg_txt, recipient['emailAddress'], clientAccess=GC.Values[GC.TODRIVE_CLIENTACCESS], msgFrom=self.todrive['from'])
        if not self.todrive['nobrowser']:
          webbrowser.open(file_url)
      except (GAPI.forbidden, GAPI.insufficientPermissions):
        printWarningMessage(INSUFFICIENT_PERMISSIONS_RC, Msg.INSUFFICIENT_PERMISSIONS_TO_PERFORM_TASK)
      except (GAPI.fileNotFound, GAPI.unknownError, GAPI.internalError, GAPI.storageQuotaExceeded) as e:
        if not self.todrive['fileId']:
          entityActionFailedWarning([Ent.DRIVE_FOLDER, self.todrive['parentId']], str(e))
        else:
          entityActionFailedWarning([Ent.DRIVE_FILE, self.todrive['fileId']], str(e))
      except (GAPI.serviceNotAvailable, GAPI.authError, GAPI.domainPolicy) as e:
        userDriveServiceNotEnabledWarning(user, str(e), 0, 0)
    else:
      closeFile(csvFile)

  def _prepareHeaders(self, clearRowFilters):
    if self.zeroBlankMimeTypeCounts:
      self.ZeroBlankMimeTypeCounts()
    if not clearRowFilters and (self.rowFilter or self.rowDropFilter):
      self.CheckOutputRowFilterHeaders()
    if self.headerFilter or self.headerDropFilter:
      if not self.formatJSON:
        self.FilterHeaders()
      else:
        self.FilterJSONHeaders()
      extrasaction = 'ignore'
    else:
      extrasaction = 'raise'
    if not self.formatJSON:
      if not self.headerForce:
        if self.headerRequired:
          self.AddTitles(self.headerRequired)
        self.SortTitles()
        self.SortIndexedTitles(self.titlesList)
        if self.fixPaths:
          self.FixPathsTitles(self.titlesList)
        if self.showPermissionsLast:
          self.MovePermsToEnd()
        if not self.rows and self.nodataFields is not None:
          self.FixNodataTitles()
      else:
        self.titlesList = self.headerForce
      if self.timestampColumn:
        self.AddTitle(self.timestampColumn)
      if self.headerOrder:
        self.titlesList = self.orderHeaders(self.titlesList)
      titlesList = self.titlesList
    else:
      if not self.headerForce:
        if self.headerRequired:
          for i, v in enumerate(self.JSONtitlesList):
            if v.startswith('JSON'):
              j = i
              for title in self.headerRequired:
                self.JSONtitlesList.insert(j, title)
                self.JSONtitlesSet.add(title)
                j += 1
              break
          else:
            self.AddJSONTitles(self.headerRequired)
        if self.fixPaths:
          self.FixPathsTitles(self.JSONtitlesList)
        if not self.rows and self.nodataFields is not None:
          self.FixNodataTitles()
      else:
        self.JSONtitlesList = self.headerForce
      if self.timestampColumn:
        for i, v in enumerate(self.JSONtitlesList):
          if v.startswith('JSON'):
            self.JSONtitlesList.insert(i, self.timestampColumn)
            self.JSONtitlesSet.add(self.timestampColumn)
            break
        else:
          self.AddJSONTitle(self.timestampColumn)
      if self.headerOrder:
        self.JSONtitlesList = self.orderHeaders(self.JSONtitlesList)
      titlesList = self.JSONtitlesList
    self._normalizeSortHeaders(titlesList)
    return titlesList, extrasaction

  def writeCSVfile(self, list_type, clearRowFilters=False):

    if GM.Globals[GM.CSVFILE][GM.REDIRECT_QUEUE] is not None:
      GM.Globals[GM.CSVFILE][GM.REDIRECT_QUEUE].put((GM.REDIRECT_QUEUE_NAME, list_type))
      GM.Globals[GM.CSVFILE][GM.REDIRECT_QUEUE].put((GM.REDIRECT_QUEUE_TODRIVE, self.todrive))
      GM.Globals[GM.CSVFILE][GM.REDIRECT_QUEUE].put((GM.REDIRECT_QUEUE_CSVPF,
                                                     (self.titlesList, self.sortTitlesList, self.indexedTitles,
                                                      self.formatJSON, self.JSONtitlesList,
                                                      self.columnDelimiter, self.noEscapeChar, self.quoteChar,
                                                      self.sortHeaders, self.timestampColumn,
                                                      self.fixPaths,
                                                      self.mapNodataFields,
                                                      self.nodataFields,
                                                      self.driveListFields,
                                                      self.driveSubfieldsChoiceMap,
                                                      self.oneItemPerRow,
                                                      self.showPermissionsLast,
                                                      self.zeroBlankMimeTypeCounts)))
      if clearRowFilters:
        GM.Globals[GM.CSVFILE][GM.REDIRECT_QUEUE].put((GM.REDIRECT_QUEUE_CLEAR_ROW_FILTERS, clearRowFilters))
      GM.Globals[GM.CSVFILE][GM.REDIRECT_QUEUE].put((GM.REDIRECT_QUEUE_DATA, self.rows))
      return
    titlesList, extrasaction = self._prepareHeaders(clearRowFilters)
    if self.outputTranspose:
      newRows = []
      newTitlesList = list(range(len(self.rows) + 1))
      for title in titlesList:
        i = 0
        newRow = {i: title}
        for row in self.rows:
          i += 1
          newRow[i] = row.get(title)
        newRows.append(newRow)
      titlesList = newTitlesList
      self.rows = newRows
    if (not self.todrive) or self.todrive['localcopy']:
      if GM.Globals[GM.CSVFILE][GM.REDIRECT_NAME] == '-':
        if GM.Globals[GM.STDOUT][GM.REDIRECT_MULTI_FD]:
          self._writeCSVToStdout(titlesList, extrasaction)
        else:
          GM.Globals[GM.CSVFILE][GM.REDIRECT_NAME] = GM.Globals[GM.STDOUT][GM.REDIRECT_NAME]
          self._writeCSVToFile(titlesList, extrasaction)
      else:
        self._writeCSVToFile(titlesList, extrasaction)
    if self.todrive:
      self._writeCSVToDrive(list_type, titlesList, extrasaction)
    if GM.Globals[GM.CSVFILE][GM.REDIRECT_MODE] == DEFAULT_FILE_APPEND_MODE:
      GM.Globals[GM.CSVFILE][GM.REDIRECT_WRITE_HEADER] = False

def writeEntityNoHeaderCSVFile(entityType, entityList):
  csvPF = CSVPrintFile(entityType)
  _, _, entityList = getEntityArgument(entityList)
  if entityType == Ent.USER:
    for entity in entityList:
      csvPF.WriteRowNoFilter({entityType: normalizeEmailAddressOrUID(entity)})
  else:
    for entity in entityList:
      csvPF.WriteRowNoFilter({entityType: entity})
  GM.Globals[GM.CSVFILE][GM.REDIRECT_WRITE_HEADER] = False
  csvPF.writeCSVfile(Ent.Plural(entityType))

def getTodriveOnly(csvPF):
  while Cmd.ArgumentsRemaining():
    myarg = getArgument()
    if csvPF and myarg == 'todrive':
      csvPF.GetTodriveParameters()
    else:
      unknownArgumentExit()

DEFAULT_SKIP_OBJECTS = {'kind', 'etag', 'etags', '@type'}

# Clean a JSON object
def cleanJSON(topStructure, listLimit=None, skipObjects=None, timeObjects=None):
  def _clean(structure, key, subSkipObjects):
    if not isinstance(structure, (dict, list)):
      if key not in timeObjects:
        if isinstance(structure, str) and GC.Values[GC.CSV_OUTPUT_CONVERT_CR_NL]:
          return escapeCRsNLs(structure)
        return structure
      if isinstance(structure, str) and not structure.isdigit():
        return formatLocalTime(structure)
      return formatLocalTimestamp(structure)
    if isinstance(structure, list):
      listLen = len(structure)
      listLen = min(listLen, listLimit or listLen)
      return [_clean(v, '', DEFAULT_SKIP_OBJECTS) for v in structure[0:listLen]]
    return {k: _clean(v, k, DEFAULT_SKIP_OBJECTS) for k, v in sorted(structure.items()) if k not in subSkipObjects}

  timeObjects = timeObjects or set()
  return _clean(topStructure, '', DEFAULT_SKIP_OBJECTS.union(skipObjects or set()))

# Flatten a JSON object
def flattenJSON(topStructure, flattened=None,
                listLimit=None, skipObjects=None, timeObjects=None, noLenObjects=None, simpleLists=None, delimiter=None):
  def _flatten(structure, key, path):
    if not isinstance(structure, (dict, list)):
      if key not in timeObjects:
        if isinstance(structure, str):
          if GC.Values[GC.CSV_OUTPUT_CONVERT_CR_NL] and (structure.find('\n') >= 0 or structure.find('\r') >= 0):
            flattened[path] = escapeCRsNLs(structure)
          else:
            flattened[path] = structure
        else:
          flattened[path] = structure
      else:
        if isinstance(structure, str) and not structure.isdigit():
          flattened[path] = formatLocalTime(structure)
        else:
          flattened[path] = formatLocalTimestamp(structure)
    elif isinstance(structure, list):
      listLen = len(structure)
      listLen = min(listLen, listLimit or listLen)
      if key in simpleLists:
        flattened[path] = delimiter.join(structure[:listLen])
      else:
        if key not in noLenObjects:
          flattened[path] = listLen
        for i in range(listLen):
          _flatten(structure[i], '', f'{path}{GC.Values[GC.CSV_OUTPUT_SUBFIELD_DELIMITER]}{i}')
    else:
      if structure:
        for k, v in sorted(structure.items()):
          if k not in DEFAULT_SKIP_OBJECTS:
            _flatten(v, k, f'{path}{GC.Values[GC.CSV_OUTPUT_SUBFIELD_DELIMITER]}{k}')
      else:
        flattened[path] = ''

  flattened = flattened or {}
  allSkipObjects = DEFAULT_SKIP_OBJECTS.union(skipObjects or set())
  timeObjects = timeObjects or set()
  noLenObjects = noLenObjects or set()
  simpleLists = simpleLists or set()
  for k, v in sorted(topStructure.items()):
    if k not in allSkipObjects:
      _flatten(v, k, k)
  return flattened

# Show a json object
def showJSON(showName, showValue, skipObjects=None, timeObjects=None,
             simpleLists=None, dictObjectsKey=None, sortDictKeys=True):
  def _show(objectName, objectValue, subObjectKey, subObjectName, level, subSkipObjects):
    if objectName in subSkipObjects:
      return
    if objectName is not None:
      printJSONKey(objectName)
    subObjectKey = dictObjectsKey.get(objectName)
    if isinstance(objectValue, list):
      if objectName in simpleLists:
        printJSONValue(' '.join(objectValue))
        return
      if len(objectValue) == 1 and isinstance(objectValue[0], (str, bool, float, int)):
        if objectName is not None:
          printJSONValue(objectValue[0])
        else:
          printKeyValueList([objectValue[0]])
        return
      if objectName is not None:
        printBlankLine()
        Ind.Increment()
      for subValue in objectValue:
        if isinstance(subValue, (str, bool, float, int)):
          printKeyValueList([subValue])
        else:
          _show(None, subValue, subObjectKey, objectName, level+1, DEFAULT_SKIP_OBJECTS)
      if objectName is not None:
        Ind.Decrement()
    elif isinstance(objectValue, dict):
      if not subObjectKey:
        subObjectKey = dictObjectsKey.get(subObjectName)
      indentAfterFirst = unindentAfterLast = False
      if objectName is not None:
        printBlankLine()
        Ind.Increment()
      elif level > 0:
        indentAfterFirst = unindentAfterLast = True
      subObjects = sorted(objectValue) if sortDictKeys else objectValue.keys()
      if subObjectKey:
        if subObjectKey in subObjects:
          subObjects.remove(subObjectKey)
          subObjects.insert(0, subObjectKey)
          subObjectKey = None
        elif subObjectName == 'permissions': # subObjectKey in displayName
          if 'id' in objectValue:
            if objectValue['id'] == 'anyone':
              objectValue[subObjectKey] = 'Anyone'
            elif objectValue['id'] == 'anyoneWithLink':
              objectValue[subObjectKey] = 'Anyone with Link'
            else:
              objectValue[subObjectKey] = objectValue['id']
            subObjects.insert(0, subObjectKey)
      for subObject in subObjects:
        if subObject not in subSkipObjects:
          _show(subObject, objectValue[subObject], subObjectKey, None, level+1, DEFAULT_SKIP_OBJECTS)
          if indentAfterFirst:
            Ind.Increment()
            indentAfterFirst = False
      if objectName is not None or ((not indentAfterFirst) and unindentAfterLast):
        Ind.Decrement()
    else:
      if objectName not in timeObjects:
        if isinstance(objectValue, str) and (objectValue.find('\n') >= 0 or objectValue.find('\r') >= 0):
          if GC.Values[GC.SHOW_CONVERT_CR_NL]:
            printJSONValue(escapeCRsNLs(objectValue))
          else:
            printBlankLine()
            Ind.Increment()
            printKeyValueList([Ind.MultiLineText(objectValue)])
            Ind.Decrement()
        else:
          printJSONValue(objectValue if objectValue is not None else '')
      else:
        if isinstance(objectValue, str) and not objectValue.isdigit():
          printJSONValue(formatLocalTime(objectValue))
        else:
          printJSONValue(formatLocalTimestamp(objectValue))

  timeObjects = timeObjects or set()
  simpleLists = simpleLists or set()
  dictObjectsKey = dictObjectsKey or {}
  _show(showName, showValue, None, None, 0, DEFAULT_SKIP_OBJECTS.union(skipObjects or set()))

class FormatJSONQuoteChar:

  def __init__(self, csvPF=None, formatJSONOnly=False):
    self.SetCsvPF(csvPF)
    self.SetFormatJSON(False)
    self.SetQuoteChar(GM.Globals.get(GM.CSV_OUTPUT_QUOTE_CHAR, GC.Values.get(GC.CSV_OUTPUT_QUOTE_CHAR, '"')))
    if not formatJSONOnly:
      return
    while Cmd.ArgumentsRemaining():
      myarg = getArgument()
      if myarg == 'formatjson':
        self.SetFormatJSON(True)
        return
      unknownArgumentExit()

  def SetCsvPF(self, csvPF):
    self.csvPF = csvPF

  def SetFormatJSON(self, formatJSON):
    self.formatJSON = formatJSON
    if self.csvPF:
      self.csvPF.SetFormatJSON(formatJSON)

  def GetFormatJSON(self, myarg):
    if myarg == 'formatjson':
      self.SetFormatJSON(True)
      return
    unknownArgumentExit()

  def SetQuoteChar(self, quoteChar):
    self.quoteChar = quoteChar
    if self.csvPF:
      self.csvPF.SetQuoteChar(quoteChar)

  def GetQuoteChar(self, myarg):
    if self.csvPF and myarg == 'quotechar':
      self.SetQuoteChar(getCharacter())
      return
    unknownArgumentExit()

  def GetFormatJSONQuoteChar(self, myarg, addTitle=False, noExit=False):
    if myarg == 'formatjson':
      self.SetFormatJSON(True)
      if self.csvPF and addTitle:
        self.csvPF.AddJSONTitles('JSON')
      return True
    if self.csvPF and myarg == 'quotechar':
      self.SetQuoteChar(getCharacter())
      return True
    if noExit:
      return False
    unknownArgumentExit()

# Batch processing request_id fields
RI_ENTITY = 0
RI_I = 1
RI_COUNT = 2
RI_J = 3
RI_JCOUNT = 4
RI_ITEM = 5
RI_ROLE = 6
RI_OPTION = 7

def batchRequestID(entityName, i, count, j, jcount, item, role=None, option=None):
  if role is None and option is None:
    return f'{entityName}\n{i}\n{count}\n{j}\n{jcount}\n{item}'
  return f'{entityName}\n{i}\n{count}\n{j}\n{jcount}\n{item}\n{role}\n{option}'
