"""CSV row filtering: match/skip field checks and row filter matching.

This module is a leaf dependency that breaks the args ↔ csv_pf cycle
by providing RowFilterMatch and checkMatchSkipFields in one place that
both args.py consumers and csv_pf.py can import from without circularity.
"""



import arrow

from gamlib import settings as GC
from util.args import NEVER_TIME, TRUE_FALSE, YYYYMMDD_FORMAT, YYYYMMDD_PATTERN
from util.output import ISOformatTimeStamp


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

def checkMatchSkipFields(row, fieldnames, matchFields, skipFields):
  for matchField, matchPattern in matchFields.items():
    if (matchField not in row) or not matchPattern.search(str(row[matchField])):
      return False
  for skipField, matchPattern in skipFields.items():
    if (skipField in row) and matchPattern.search(str(row[skipField])):
      return False
  if fieldnames and (GC.Values[GC.CSV_INPUT_ROW_FILTER] or GC.Values[GC.CSV_INPUT_ROW_DROP_FILTER]):
    return RowFilterMatch(row, fieldnames,
                          GC.Values[GC.CSV_INPUT_ROW_FILTER], GC.Values[GC.CSV_INPUT_ROW_FILTER_MODE],
                          GC.Values[GC.CSV_INPUT_ROW_DROP_FILTER], GC.Values[GC.CSV_INPUT_ROW_DROP_FILTER_MODE])
  return True

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
