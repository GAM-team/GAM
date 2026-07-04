"""Google Sheets management.

Part of the _userop_tmp sub-package."""

"""GAM user operations: Looker Studio, user groups, licenses, photos, profile, sheets, tokens, deprovision."""

import json

from gamlib import api as API
from gamlib import settings as GC
from gamlib import gapi as GAPI
from gamlib import msgs as Msg
from gam.util.svcacct import buildGAPIServiceObject
from gam.util.api_call import callGAPI, callGAPIitems
from gam.util.args import getArgument, getBoolean, getJSON, getString
from gam.util.csv_pf import (
    CSVPrintFile,
    FormatJSONQuoteChar,
    _getFieldsList,
    cleanJSON,
    flattenJSON,
    getFieldsFromFieldsList,
    getFieldsList,
    showJSON,
)
from gam.util.display import (
    entityActionFailedWarning,
    entityActionPerformed,
    entityPerformActionNumItems,
    printEntity,
    printKeyValueList,
    printKeyValueListWithCount,
    printLine,
    userDriveServiceNotEnabledWarning,
)
from gam.util.entity import convertEntityToList, getEntityArgument
from gam.util.errors import invalidChoiceExit, usageErrorExit
from gam.util.output import writeStdout
from gam.constants import ROOT
from gam.cmd.drive.core import _getDriveFileParentInfo, getDriveFileParentAttribute, initDriveFileAttributes
from gam.cmd.drive.core import _validateUserGetFileIDs
from gam.cmd.drive.core import getDriveFileEntity

from gam.var import Act, Cmd, Ent, Ind

ERROR_PREFIX = 'ERROR: '

def createSheet(users):
  parameters = initDriveFileAttributes()
  parentBody = {}
  changeParents = returnIdOnly = False
  addParents = ''
  removeParents = ROOT
  body = {}
  FJQC = FormatJSONQuoteChar()
  while Cmd.ArgumentsRemaining():
    myarg = getArgument()
    if myarg == 'json':
      body = getJSON([])
    elif getDriveFileParentAttribute(myarg, parameters):
      changeParents = True
    elif myarg == 'returnidonly':
      returnIdOnly = True
    else:
      FJQC.GetFormatJSON(myarg)
  i, count, users = getEntityArgument(users)
  for user in users:
    i += 1
    user, sheet = buildGAPIServiceObject(API.SHEETS, user, i, count)
    if not sheet:
      continue
    if changeParents:
      user, drive = buildGAPIServiceObject(API.DRIVE3, user, i, count)
      if not drive:
        continue
      if not _getDriveFileParentInfo(drive, user, i, count, parentBody, parameters):
        continue
      addParents = ','.join(parentBody['parents'])
    try:
      result = callGAPI(sheet.spreadsheets(), 'create',
                        throwReasons=GAPI.SHEETS_ACCESS_THROW_REASONS,
                        body=body)
      spreadsheetId = result['spreadsheetId']
      if not returnIdOnly and not FJQC.formatJSON:
        entityActionPerformed([Ent.USER, user, Ent.SPREADSHEET, spreadsheetId], i, count)
      parentId = ROOT
      parentMsg = Act.SUCCESS
      if changeParents:
        try:
          callGAPI(drive.files(), 'update',
                   throwReasons=GAPI.DRIVE_ACCESS_THROW_REASONS+[GAPI.CANNOT_ADD_PARENT, GAPI.INSUFFICIENT_PARENT_PERMISSIONS],
                   fileId=result['spreadsheetId'],
                   addParents=addParents, removeParents=removeParents, fields='', supportsAllDrives=True)
          parentId = addParents
        except (GAPI.fileNotFound, GAPI.forbidden, GAPI.permissionDenied,
                GAPI.internalError, GAPI.insufficientFilePermissions, GAPI.insufficientParentPermissions, GAPI.badRequest,
                GAPI.invalid, GAPI.invalidArgument, GAPI.failedPrecondition,
                GAPI.cannotAddParent) as e:
          parentMsg = f'{ERROR_PREFIX}{addParents}: {str(e)}'
        except (GAPI.serviceNotAvailable, GAPI.authError, GAPI.domainPolicy) as e:
          parentMsg = f'{ERROR_PREFIX}{addParents}: {str(e)}'
      if returnIdOnly:
        writeStdout(f'{spreadsheetId}\n')
        continue
      if FJQC.formatJSON:
        printLine('{'+f'"User": "{user}", "spreadsheetId": "{spreadsheetId}", "parentId": "{parentId}", '\
                    '"parentAssignment": "{parentMsg}", "JSON": {json.dumps(result, ensure_ascii=False, sort_keys=False)}'+'}')
        continue
      Ind.Increment()
      for field in ['spreadsheetId', 'spreadsheetUrl']:
        printKeyValueList([field, result[field]])
      printKeyValueList(['parentId', parentId])
      printKeyValueList(['parentAssignment', parentMsg])
      for field in ['properties', 'sheets', 'namedRanges', 'developerMetadata']:
        if field in result:
          showJSON(field, result[field])
      Ind.Decrement()
    except (GAPI.notFound, GAPI.forbidden, GAPI.internalError,
            GAPI.insufficientFilePermissions, GAPI.unknownError, GAPI.badRequest,
            GAPI.invalid, GAPI.invalidArgument) as e:
      entityActionFailedWarning([Ent.USER, user, Ent.SPREADSHEET, ''], str(e), i, count)
    except (GAPI.serviceNotAvailable, GAPI.authError, GAPI.domainPolicy) as e:
      userDriveServiceNotEnabledWarning(user, str(e), i, count)

def _validateUserGetSpreadsheetIDs(user, i, count, fileIdEntity, showEntityType):
  user, _, jcount = _validateUserGetFileIDs(user, i, count, fileIdEntity, entityType=Ent.SPREADSHEET if showEntityType else None)
  if jcount == 0:
    return (user, None, 0)
  user, sheet = buildGAPIServiceObject(API.SHEETS, user, i, count)
  if not sheet:
    return (user, None, 0)
  return (user, sheet, jcount)

# gam <UserTypeEntity> update sheet <DriveFileEntity>
#	((json [charset <Charset>] <SpreadsheetJSONUpdateRequest>) |
#	 (json file <FileName> [charset <Charset>]))
#	[formatjson]
def updateSheets(users):
  spreadsheetIdEntity = getDriveFileEntity()
  body = {}
  FJQC = FormatJSONQuoteChar()
  while Cmd.ArgumentsRemaining():
    myarg = getArgument()
    if myarg == 'json':
      body = getJSON([])
    else:
      FJQC.GetFormatJSON(myarg)
  i, count, users = getEntityArgument(users)
  for user in users:
    i += 1
    user, sheet, jcount = _validateUserGetSpreadsheetIDs(user, i, count, spreadsheetIdEntity, not FJQC.formatJSON)
    if jcount == 0:
      continue
    Ind.Increment()
    j = 0
    for spreadsheetId in spreadsheetIdEntity['list']:
      j += 1
      try:
        result = callGAPI(sheet.spreadsheets(), 'batchUpdate',
                          throwReasons=GAPI.SHEETS_ACCESS_THROW_REASONS,
                          spreadsheetId=spreadsheetId, body=body)
        if FJQC.formatJSON:
          printLine('{'+f'"User": "{user}", "spreadsheetId": "{spreadsheetId}", "JSON": {json.dumps(result, ensure_ascii=False, sort_keys=False)}'+'}')
          continue
        entityActionPerformed([Ent.USER, user, Ent.SPREADSHEET, spreadsheetId], j, jcount)
        Ind.Increment()
        for field in ['replies', 'updatedSpreadsheet']:
          if field in result:
            showJSON(field, result[field])
        Ind.Decrement()
      except (GAPI.notFound, GAPI.forbidden, GAPI.permissionDenied,
              GAPI.internalError, GAPI.insufficientFilePermissions, GAPI.badRequest,
              GAPI.invalid, GAPI.invalidArgument, GAPI.failedPrecondition) as e:
        entityActionFailedWarning([Ent.USER, user, Ent.SPREADSHEET, spreadsheetId], str(e), j, jcount)
      except (GAPI.serviceNotAvailable, GAPI.authError, GAPI.domainPolicy) as e:
        userDriveServiceNotEnabledWarning(user, str(e), i, count)
        break
    Ind.Decrement()

SPREADSHEET_FIELDS_CHOICE_MAP = {
  'developermetadata': 'developerMetadata',
  'namedranges': 'namedRanges',
  'properties': 'properties',
  'sheets': 'sheets',
  'spreadsheetid': 'spreadsheetId',
  'spreadsheeturl': 'spreadsheetUrl',
  }

SPREADSHEET_SHEETS_SUBFIELDS_CHOICE_MAP = {
  'properties': 'sheets.properties',
  'data': 'sheets.data',
  'merges': 'sheets.merges',
  'conditionalformats': 'sheets.conditionalFormats',
  'filterviews': 'sheets.filterViews',
  'protectedranges': 'sheets.protectedRanges',
  'basicfilter': 'sheets.basicFilter',
  'charts': 'sheets.charts',
  'bandedranges': 'sheets.bandedRanges',
  'developermetadata': 'sheets.developerMetadata',
  'rowgroups': 'sheets.rowGroups',
  'columngroups': 'sheets.columnGroups',
  'slicers': 'sheets.slicers',
  }

# gam <UserTypeEntity> info|show sheet <DriveFileEntity>
#	[fields <SpreadsheetFieldList>] [sheetsfields <SpreadsheetSheetsFieldList>]
#	(range <SpreadsheetRange>)* (rangelist <SpreadsheetRangeList>)*
#	[includegriddata [<Boolean>]] [shownames]
#	[formatjson]
# gam <UserTypeEntity> print sheet <DriveFileEntity> [todrive <ToDriveAttribute>*]
#	[fields <SpreadsheetFieldList>] [sheetsfields <SpreadsheetSheetsFieldList>]
#	(range <SpreadsheetRange>)* (rangelist <SpreadsheetRangeList>)*
#	[includegriddata [<Boolean>]] [shownames]
#	[formatjson [quotechar <Character>]]
def infoPrintShowSheets(users):
  csvPF = CSVPrintFile(['User', 'spreadsheetId'], 'sortall') if Act.csvFormat() else None
  FJQC = FormatJSONQuoteChar(csvPF)
  spreadsheetIdEntity = getDriveFileEntity()
  fieldsList = []
  ranges = []
  includeGridData = showSheetNames = False
  while Cmd.ArgumentsRemaining():
    myarg = getArgument()
    if csvPF and myarg == 'todrive':
      csvPF.GetTodriveParameters()
    elif myarg == 'range':
      ranges.append(getString(Cmd.OB_SPREADSHEET_RANGE))
    elif myarg == 'rangelist':
      ranges.extend(convertEntityToList(getString(Cmd.OB_SPREADSHEET_RANGE_LIST), shlexSplit=True))
    elif myarg == 'includegriddata':
      includeGridData = getBoolean()
    elif getFieldsList(myarg, SPREADSHEET_FIELDS_CHOICE_MAP, fieldsList, initialField='spreadsheetId'):
      pass
    elif myarg == 'sheetsfields':
      for field in _getFieldsList():
        if field in SPREADSHEET_SHEETS_SUBFIELDS_CHOICE_MAP:
          fieldsList.append(SPREADSHEET_SHEETS_SUBFIELDS_CHOICE_MAP[field])
        else:
          invalidChoiceExit(field, SPREADSHEET_SHEETS_SUBFIELDS_CHOICE_MAP, True)
    elif myarg == 'shownames':
      showSheetNames = True
    else:
      FJQC.GetFormatJSONQuoteChar(myarg, True)
  if csvPF and showSheetNames:
    csvPF.AddTitles('spreadsheetName')
    csvPF.SetSortAllTitles()
    if FJQC.formatJSON:
      csvPF.AddJSONTitles('spreadsheetName')
      csvPF.MoveJSONTitlesToEnd(['JSON'])
  if includeGridData and fieldsList:
    fieldsList.append(SPREADSHEET_SHEETS_SUBFIELDS_CHOICE_MAP['data'])
  fields = getFieldsFromFieldsList(fieldsList)
  i, count, users = getEntityArgument(users)
  for user in users:
    i += 1
    user, sheet, jcount = _validateUserGetSpreadsheetIDs(user, i, count, spreadsheetIdEntity, not FJQC.formatJSON)
    if jcount == 0:
      continue
    if showSheetNames:
      _, drive = buildGAPIServiceObject(API.DRIVE3, user, i, count)
      if not drive:
        continue
    Ind.Increment()
    j = 0
    for spreadsheetId in spreadsheetIdEntity['list']:
      j += 1
      try:
        result = callGAPI(sheet.spreadsheets(), 'get',
                          throwReasons=GAPI.SHEETS_ACCESS_THROW_REASONS,
                          spreadsheetId=spreadsheetId, ranges=ranges, includeGridData=includeGridData, fields=fields)
        if not includeGridData and 'sheets' in result:
          for usheet in result['sheets']:
            usheet.pop('data', None)
        if showSheetNames:
          try:
            spreadsheetName = callGAPI(drive.files(), 'get',
                                       throwReasons=GAPI.DRIVE_GET_THROW_REASONS,
                                       fileId=spreadsheetId, fields='name', supportsAllDrives=True)['name']
          except (GAPI.fileNotFound, GAPI.serviceNotAvailable, GAPI.authError, GAPI.domainPolicy):
            spreadsheetName = spreadsheetId
        if not csvPF:
          if FJQC.formatJSON:
            baserow = {'User': user, 'spreadsheetId': spreadsheetId}
            if showSheetNames:
              baserow['spreadsheetName'] = spreadsheetName
            baserow['JSON'] =  result
            printLine(json.dumps(baserow, ensure_ascii=False, sort_keys=False)+'\n')
            continue
          if showSheetNames:
            printEntity([Ent.SPREADSHEET, f'{spreadsheetName}({spreadsheetId})'], j, jcount)
          else:
            printEntity([Ent.SPREADSHEET, spreadsheetId], j, jcount)
          Ind.Increment()
          if 'spreadsheetUrl' in result:
            printKeyValueList(['spreadsheetUrl', result['spreadsheetUrl']])
          for field in ['properties', 'sheets', 'namedRanges', 'developerMetadata', 'dataSources', 'dataSourceSchedules']:
            if field in result:
              if field != 'sheets':
                showJSON(field, result[field])
              else:
                jcount = len(result[field])
                j = 0
                for usheet in result[field]:
                  j += 1
                  printEntity([Ent.SHEET, usheet.get('properties', {}).get('title', '')], j, jcount)
                  Ind.Increment()
                  showJSON(None, usheet)
                  Ind.Decrement()
          Ind.Decrement()
        else:
          baserow = {'User': user, 'spreadsheetId': spreadsheetId}
          if showSheetNames:
            baserow['spreadsheetName'] = spreadsheetName
          row = flattenJSON(result, flattened=baserow.copy())
          if not FJQC.formatJSON:
            csvPF.WriteRowTitles(row)
          elif csvPF.CheckRowTitles(row):
            baserow['JSON'] = json.dumps(cleanJSON(result), ensure_ascii=False, sort_keys=False)
            csvPF.WriteRowNoFilter(baserow)
      except (GAPI.notFound, GAPI.forbidden, GAPI.permissionDenied,
              GAPI.internalError, GAPI.insufficientFilePermissions, GAPI.badRequest,
              GAPI.invalid, GAPI.invalidArgument, GAPI.failedPrecondition) as e:
        entityActionFailedWarning([Ent.USER, user, Ent.SPREADSHEET, spreadsheetId], str(e), j, jcount)
      except (GAPI.serviceNotAvailable, GAPI.authError, GAPI.domainPolicy) as e:
        userDriveServiceNotEnabledWarning(user, str(e), i, count)
        break
    Ind.Decrement()
  if csvPF:
    csvPF.writeCSVfile('Spreadsheet')

SHEET_VALUE_INPUT_OPTIONS_MAP = {
  'raw': 'RAW',
  'userentered': 'USER_ENTERED',
  }
SHEET_DIMENSIONS_MAP = {
  'rows': 'ROWS',
  'columns': 'COLUMNS',
  }
SHEET_VALUE_RENDER_OPTIONS_MAP = {
  'formula': 'FORMULA',
  'formattedvalue': 'FORMATTED_VALUE',
  'unformattedvalue': 'UNFORMATTED_VALUE',
  }
SHEET_DATETIME_RENDER_OPTIONS_MAP = {
  'serialnumber': 'SERIAL_NUMBER',
  'formattedstring': 'FORMATTED_STRING',
  }
SHEET_INSERT_DATA_OPTIONS_MAP = {
  'overwrite': 'OVERWRITE',
  'insertrows': 'INSERT_ROWS',
  }

def _getSpreadsheetRangesValues(append):
  spreadsheetRangesValues = []
  kwargs = {
    'valueInputOption': 'USER_ENTERED',
    'includeValuesInResponse': False,
    'responseValueRenderOption': 'FORMATTED_VALUE',
    'responseDateTimeRenderOption': 'FORMATTED_STRING',
    }
  if append:
    kwargs['insertDataOption'] = 'INSERT_ROWS'
  FJQC = FormatJSONQuoteChar()
  while Cmd.ArgumentsRemaining():
    myarg = getArgument()
    if myarg == 'json':
      if append and spreadsheetRangesValues:
        usageErrorExit(Msg.ONLY_ONE_JSON_RANGE_ALLOWED)
      spreadsheetRangeValue = getJSON([])
      if isinstance(spreadsheetRangeValue, dict) and 'valueRanges' in spreadsheetRangeValue:
        spreadsheetRangesValues.extend(spreadsheetRangeValue['valueRanges'])
      elif isinstance(spreadsheetRangeValue, list):
        spreadsheetRangesValues.extend(spreadsheetRangeValue)
      else:
        spreadsheetRangesValues.append(spreadsheetRangeValue)
      if append and len(spreadsheetRangesValues) > 1:
        Cmd.Backup()
        usageErrorExit(Msg.ONLY_ONE_JSON_RANGE_ALLOWED)
    elif myarg in SHEET_VALUE_INPUT_OPTIONS_MAP:
      kwargs['valueInputOption'] = SHEET_VALUE_INPUT_OPTIONS_MAP[myarg]
    elif myarg == 'includevaluesinresponse':
      kwargs['includeValuesInResponse'] = getBoolean()
    elif myarg in SHEET_VALUE_RENDER_OPTIONS_MAP:
      kwargs['responseValueRenderOption'] = SHEET_VALUE_RENDER_OPTIONS_MAP[myarg]
    elif myarg in SHEET_DATETIME_RENDER_OPTIONS_MAP:
      kwargs['responseDateTimeRenderOption'] = SHEET_DATETIME_RENDER_OPTIONS_MAP[myarg]
    elif append and myarg in SHEET_INSERT_DATA_OPTIONS_MAP:
      kwargs['insertDataOption'] = SHEET_INSERT_DATA_OPTIONS_MAP[myarg]
    else:
      FJQC.GetFormatJSON(myarg)
  return (kwargs, spreadsheetRangesValues, FJQC)

def _showValueRange(valueRange):
  Ind.Increment()
  printKeyValueList(['majorDimension', valueRange['majorDimension']])
  printKeyValueList(['range', valueRange['range']])
  printKeyValueList(['value', '{'+f'"values": {json.dumps(valueRange.get("values", []), ensure_ascii=False, sort_keys=False)}'+'}'])
  Ind.Decrement()

def _showUpdateValuesResponse(result, k, kcount):
  printKeyValueListWithCount(['updatedRange', result['updatedRange']], k, kcount)
  Ind.Increment()
  for field in ['updatedRows', 'updatedColumns', 'updatedCells']:
    printKeyValueList([field, result[field]])
  if 'updatedData' in result:
    printKeyValueList(['updatedData', ''])
    _showValueRange(result['updatedData'])
  Ind.Decrement()

# gam <UserTypeEntity> append sheetrange <DriveFileEntity>
#	((json [charset <Charset>] <SpreadsheetJSONRangeValues>|<SpreadsheetJSONRangeValuesList>) |
#	 (json file <FileName> [charset <Charset>]))
#	[overwrite|insertrows]
#	[raw|userentered] [serialnumber|formattedstring] [formula|formattedvalue|unformattedvalue]
#	[includevaluesinresponse [<Boolean>]] [formatjson]
def appendSheetRanges(users):
  spreadsheetIdEntity = getDriveFileEntity()
  kwargs, spreadsheetRangesValues, FJQC = _getSpreadsheetRangesValues(True)
  kcount = len(spreadsheetRangesValues)
  body = spreadsheetRangesValues[0] if kcount > 0 else {}
  i, count, users = getEntityArgument(users)
  for user in users:
    i += 1
    user, sheet, jcount = _validateUserGetSpreadsheetIDs(user, i, count, spreadsheetIdEntity, not FJQC.formatJSON)
    if jcount == 0:
      continue
    Ind.Increment()
    j = 0
    for spreadsheetId in spreadsheetIdEntity['list']:
      j += 1
      if not FJQC.formatJSON:
        entityPerformActionNumItems([Ent.USER, user, Ent.SPREADSHEET, spreadsheetId], kcount, Ent.SPREADSHEET_RANGE, j, jcount)
      Ind.Increment()
      k = 1
      try:
        result = callGAPI(sheet.spreadsheets().values(), 'append',
                          throwReasons=GAPI.SHEETS_ACCESS_THROW_REASONS,
                          spreadsheetId=spreadsheetId, range=body['range'], body=body, **kwargs)
        if FJQC.formatJSON:
          printLine('{'+f'"User": "{user}", "spreadsheetId": "{spreadsheetId}", "JSON": {json.dumps(result, ensure_ascii=False, sort_keys=False)}'+'}')
          continue
        for field in ['tableRange']:
          if field in result:
            printKeyValueList([field, result[field]])
        _showUpdateValuesResponse(result['updates'], k, kcount)
      except (GAPI.notFound, GAPI.forbidden, GAPI.permissionDenied,
              GAPI.internalError, GAPI.insufficientFilePermissions, GAPI.badRequest,
              GAPI.invalid, GAPI.invalidArgument, GAPI.failedPrecondition) as e:
        entityActionFailedWarning([Ent.USER, user, Ent.SPREADSHEET, spreadsheetId], str(e), j, jcount)
      except (GAPI.serviceNotAvailable, GAPI.authError, GAPI.domainPolicy) as e:
        userDriveServiceNotEnabledWarning(user, str(e), i, count)
        break
      Ind.Decrement()
    Ind.Decrement()

# gam <UserTypeEntity> update sheetrange <DriveFileEntity>
#	((json [charset <Charset>] <SpreadsheetJSONRangeValues>|<SpreadsheetJSONRangeValuesList>)+
#	 (json file <FileName> [charset <Charset>]))+
#	[raw|userentered] [serialnumber|formattedstring] [formula|formattedvalue|unformattedvalue]
#	[includevaluesinresponse [<Boolean>]] [formatjson]
def updateSheetRanges(users):
  spreadsheetIdEntity = getDriveFileEntity()
  body, spreadsheetRangesValues, FJQC = _getSpreadsheetRangesValues(False)
  body['data'] = spreadsheetRangesValues
  kcount = len(spreadsheetRangesValues)
  i, count, users = getEntityArgument(users)
  for user in users:
    i += 1
    user, sheet, jcount = _validateUserGetSpreadsheetIDs(user, i, count, spreadsheetIdEntity, not FJQC.formatJSON)
    if jcount == 0:
      continue
    Ind.Increment()
    j = 0
    for spreadsheetId in spreadsheetIdEntity['list']:
      j += 1
      if not FJQC.formatJSON:
        entityPerformActionNumItems([Ent.USER, user, Ent.SPREADSHEET, spreadsheetId], kcount, Ent.SPREADSHEET_RANGE, j, jcount)
      Ind.Increment()
      try:
        result = callGAPI(sheet.spreadsheets().values(), 'batchUpdate',
                          throwReasons=GAPI.SHEETS_ACCESS_THROW_REASONS,
                          spreadsheetId=spreadsheetId, body=body)
        if FJQC.formatJSON:
          printLine('{'+f'"User": "{user}", "spreadsheetId": "{spreadsheetId}", "JSON": {json.dumps(result, ensure_ascii=False, sort_keys=False)}'+'}')
          continue
        for field in ['totalUpdatedRows', 'totalUpdatedColumns', 'totalUpdatedCells', 'totalUpdatedSheets']:
          printKeyValueList([field, result[field]])
        k = 0
        for response in result.get('responses', []):
          k += 1
          _showUpdateValuesResponse(response, k, kcount)
      except (GAPI.notFound, GAPI.forbidden, GAPI.permissionDenied,
              GAPI.internalError, GAPI.insufficientFilePermissions, GAPI.badRequest,
              GAPI.invalid, GAPI.invalidArgument, GAPI.failedPrecondition) as e:
        entityActionFailedWarning([Ent.USER, user, Ent.SPREADSHEET, spreadsheetId], str(e), j, jcount)
      except (GAPI.serviceNotAvailable, GAPI.authError, GAPI.domainPolicy) as e:
        userDriveServiceNotEnabledWarning(user, str(e), i, count)
        break
      Ind.Decrement()
    Ind.Decrement()

# gam <UserTypeEntity> clear sheetrange <DriveFileEntity>
#	(range <SpreadsheetRange>)* (rangelist <SpreadsheetRangeList>)*
#	[formatjson]
def clearSheetRanges(users):
  spreadsheetIdEntity = getDriveFileEntity()
  body = {'ranges': []}
  FJQC = FormatJSONQuoteChar()
  while Cmd.ArgumentsRemaining():
    myarg = getArgument()
    if myarg == 'range':
      body['ranges'].append(getString(Cmd.OB_SPREADSHEET_RANGE))
    elif myarg == 'rangelist':
      body['ranges'].extend(convertEntityToList(getString(Cmd.OB_SPREADSHEET_RANGE_LIST), shlexSplit=True))
    else:
      FJQC.GetFormatJSON(myarg)
  kcount = len(body['ranges'])
  i, count, users = getEntityArgument(users)
  for user in users:
    i += 1
    user, sheet, jcount = _validateUserGetSpreadsheetIDs(user, i, count, spreadsheetIdEntity, not FJQC.formatJSON)
    if jcount == 0:
      continue
    Ind.Increment()
    j = 0
    for spreadsheetId in spreadsheetIdEntity['list']:
      j += 1
      if not FJQC.formatJSON:
        entityPerformActionNumItems([Ent.USER, user, Ent.SPREADSHEET, spreadsheetId], kcount, Ent.SPREADSHEET_RANGE, j, jcount)
      Ind.Increment()
      try:
        result = callGAPIitems(sheet.spreadsheets().values(), 'batchClear', 'clearedRanges',
                               throwReasons=GAPI.SHEETS_ACCESS_THROW_REASONS,
                               spreadsheetId=spreadsheetId, body=body)
        if FJQC.formatJSON:
          printLine('{'+f'"User": "{user}", "spreadsheetId": "{spreadsheetId}", "JSON": {json.dumps({"clearedRanges": result}, ensure_ascii=False, sort_keys=False)}'+'}')
          continue
        k = 0
        for clearedRange in result:
          k += 1
          printKeyValueListWithCount(['range', clearedRange], k, kcount)
      except (GAPI.notFound, GAPI.forbidden, GAPI.permissionDenied,
              GAPI.internalError, GAPI.insufficientFilePermissions, GAPI.badRequest,
              GAPI.invalid, GAPI.invalidArgument, GAPI.failedPrecondition) as e:
        entityActionFailedWarning([Ent.USER, user, Ent.SPREADSHEET, spreadsheetId], str(e), j, jcount)
      except (GAPI.serviceNotAvailable, GAPI.authError, GAPI.domainPolicy) as e:
        userDriveServiceNotEnabledWarning(user, str(e), i, count)
        break
      Ind.Decrement()
    Ind.Decrement()

# gam <UserTypeEntity> print sheetrange <DriveFileEntity> [todrive <ToDriveAttribute>*]
#	(range <SpreadsheetRange>)* (rangelist <SpreadsheetRangeList>)*
#	[rows|columns] [serialnumber|formattedstring] [formula|formattedvalue|unformattedvalue]
#	[formatjson [quotechar <Character>] [valuerangesonly [<Boolean>]]]
# gam <UserTypeEntity> show sheetrange <DriveFileEntity>
#	(range <SpreadsheetRange>)* (rangelist <SpreadsheetRangeList>)*
#	[rows|columns] [serialnumber|formattedstring] [formula|formattedvalue|unformattedvalue]
#	[formatjson [valuerangesonly [<Boolean>]]]
def printShowSheetRanges(users):
  csvPF = CSVPrintFile(['User', 'spreadsheetId'], 'sortall') if Act.csvFormat() else None
  FJQC = FormatJSONQuoteChar(csvPF)
  spreadsheetIdEntity = getDriveFileEntity()
  spreadsheetRanges = []
  kwargs = {
    'majorDimension': 'ROWS',
    'valueRenderOption': 'FORMATTED_VALUE',
    'dateTimeRenderOption': 'FORMATTED_STRING',
    }
  valueRangesOnly = False
  while Cmd.ArgumentsRemaining():
    myarg = getArgument()
    if csvPF and myarg == 'todrive':
      csvPF.GetTodriveParameters()
    elif myarg == 'range':
      spreadsheetRanges.append(getString(Cmd.OB_SPREADSHEET_RANGE))
    elif myarg == 'rangelist':
      spreadsheetRanges.extend(convertEntityToList(getString(Cmd.OB_SPREADSHEET_RANGE_LIST), shlexSplit=True))
    elif myarg == 'valuerangesonly':
      valueRangesOnly = getBoolean()
    elif myarg in SHEET_DIMENSIONS_MAP:
      kwargs['majorDimension'] = SHEET_DIMENSIONS_MAP[myarg]
    elif myarg in SHEET_VALUE_RENDER_OPTIONS_MAP:
      kwargs['valueRenderOption'] = SHEET_VALUE_RENDER_OPTIONS_MAP[myarg]
    elif myarg in SHEET_DATETIME_RENDER_OPTIONS_MAP:
      kwargs['dateTimeRenderOption'] = SHEET_DATETIME_RENDER_OPTIONS_MAP[myarg]
    else:
      FJQC.GetFormatJSONQuoteChar(myarg, True)
  if csvPF and FJQC.formatJSON and valueRangesOnly:
    csvPF.SetJSONTitles(['JSON'])
  i, count, users = getEntityArgument(users)
  for user in users:
    i += 1
    user, sheet, jcount = _validateUserGetSpreadsheetIDs(user, i, count, spreadsheetIdEntity, not csvPF and not FJQC.formatJSON)
    if jcount == 0:
      continue
    Ind.Increment()
    j = 0
    for spreadsheetId in spreadsheetIdEntity['list']:
      j += 1
      try:
        result = callGAPI(sheet.spreadsheets().values(), 'batchGet',
                          throwReasons=GAPI.SHEETS_ACCESS_THROW_REASONS,
                          spreadsheetId=spreadsheetId, ranges=spreadsheetRanges, fields='valueRanges', **kwargs)
        valueRanges = result.get('valueRanges', [])
        if not csvPF:
          if FJQC.formatJSON:
            if not valueRangesOnly:
              printLine('{'+f'"User": "{user}", "spreadsheetId": "{spreadsheetId}", "JSON": {json.dumps(result, ensure_ascii=False, sort_keys=False)}'+'}')
            else:
              printLine(json.dumps(result.get('valueRanges', []), ensure_ascii=False, sort_keys=False))
            continue
          kcount = len(valueRanges)
          entityPerformActionNumItems([Ent.USER, user, Ent.SPREADSHEET, spreadsheetId], kcount, Ent.SPREADSHEET_RANGE, j, jcount)
          Ind.Increment()
          k = 0
          for valueRange in valueRanges:
            k += 1
            printKeyValueListWithCount(['range', valueRange['range']], k, kcount)
            _showValueRange(valueRange)
          Ind.Decrement()
        elif valueRanges:
          row = flattenJSON(result, flattened={'User': user, 'spreadsheetId': spreadsheetId})
          if not FJQC.formatJSON:
            csvPF.WriteRowTitles(row)
          elif csvPF.CheckRowTitles(row):
            if not valueRangesOnly:
              csvPF.WriteRowNoFilter({'User': user, 'spreadsheetId': spreadsheetId,
                                      'JSON': json.dumps(result, ensure_ascii=False, sort_keys=False)})
            else:
              csvPF.WriteRowNoFilter({'JSON': json.dumps(result.get('valueRanges', []), ensure_ascii=False, sort_keys=False)})
        elif GC.Values[GC.CSV_OUTPUT_USERS_AUDIT]:
          csvPF.WriteRowNoFilter({'User': user})
      except (GAPI.notFound, GAPI.forbidden, GAPI.permissionDenied,
              GAPI.internalError, GAPI.insufficientFilePermissions, GAPI.badRequest,
              GAPI.invalid, GAPI.invalidArgument, GAPI.failedPrecondition) as e:
        entityActionFailedWarning([Ent.USER, user, Ent.SPREADSHEET, spreadsheetId], str(e), j, jcount)
      except (GAPI.serviceNotAvailable, GAPI.authError, GAPI.domainPolicy) as e:
        userDriveServiceNotEnabledWarning(user, str(e), i, count)
        break
    Ind.Decrement()
  if csvPF:
    csvPF.writeCSVfile('Spreadsheet')

# Token commands utilities
def commonClientIds(clientId):
  if clientId == 'gasmo':
    return '1095133494869.apps.googleusercontent.com'
  return clientId

# gam <UserTypeEntity> delete token|tokens|3lo|oauth clientid <ClientID>
