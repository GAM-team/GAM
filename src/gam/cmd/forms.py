"""Google Forms management.

Part of the _gmail_monolith sub-package."""

"""GAM Gmail management: labels, messages, filters, forwarding, sendas, S/MIME, CSE, vacation."""

import json

from gamlib import api as API
from gamlib import gapi as GAPI
from gam.util.api import SvcAcctAPIDisabledExit
from gam.util.svcacct import buildGAPIServiceObject
from gam.util.api_call import callGAPI, callGAPIpages
from gam.util.args import (
    getAddCSVData,
    getArgument,
    getBoolean,
    getJSON,
    getString,
    getTimeOrDeltaFromNow,
)
from gam.util.csv_pf import (
    CSVPrintFile,
    FormatJSONQuoteChar,
    cleanJSON,
    flattenJSON,
    showJSON,
)
from gam.util.display import (
    entityActionFailedWarning,
    entityActionPerformed,
    entityPerformActionNumItems,
    printEntity,
    printEntityKVList,
    printLine,
    userDriveServiceNotEnabledWarning,
)
from gam.util.entity import getEntityArgument
from gam.util.errors import missingArgumentExit, unknownArgumentExit
from gam.util.output import writeStdout
from gam.cmd.drive.core import _getDriveFileParentInfo, getDriveFileParentAttribute, initDriveFileAttributes
from gam.cmd.drive.core import _validateUserGetFileIDs, getDriveFileEntity

from gam.var import Act, Cmd, Ent, Ind
from gam.constants import (
    MIMETYPE_GA_FORM,
)


def findFormRequest(field, newRequest, ubody):
  for request in ubody['requests']:
    if field in request:
      return request
  ubody['requests'].append(newRequest)
  return ubody['requests'][-1]

def updateFormInfoRequest(key, value, ubody):
  request = findFormRequest('updateFormInfo',
                            {'updateFormInfo': {'info': {}, 'updateMask': []}},
                            ubody)
  request['updateFormInfo']['info'][key] = value
  request['updateFormInfo']['updateMask'].append(key)

def updateFormSettingsRequest(key, value, ubody):
  request = findFormRequest('updateSettings',
                            {'updateSettings': {'settings': {'quizSettings': {}}, 'updateMask': []}},
                            ubody)
  request['updateSettings']['settings']['quizSettings'][key] = value
  request['updateSettings']['updateMask'].append(f'quizSettings.{key}')

def updateFormRequestUpdateMasks(ubody):
  for request in ubody['requests']:
    for k, v in request.items():
      if k in {'updateFormInfo', 'updateSettings'}:
        v['updateMask'] = ','.join(v['updateMask'])
        break

def _initPublishSettings():
  return {'publishSettings': {'publishState': {}}, 'updateMask': ''}

def _getPublishSettings(myarg, pbody):
  if myarg == 'ispublished':
    bval = getBoolean()
    pbody['publishSettings']['publishState']['isPublished'] = bval
    if not bval:
      pbody['publishSettings']['publishState']['isAcceptingResponses'] = bval
  elif myarg == 'isacceptingresponses':
    bval = getBoolean()
    pbody['publishSettings']['publishState']['isAcceptingResponses'] = bval
    if bval:
      pbody['publishSettings']['publishState']['isPublished'] = bval
  else:
    return False
  pbody['updateMask'] = 'publishState'
  return True

# gam <UserTypeEntity> create form
#	title <String> [description <String>] [isquiz [<Boolean>]] [<JSONData>]
#	[ispublished [<Boolean>] isacceptingresponses [<Boolean>]]
#	[drivefilename <DriveFileName>] [<DriveFileParentAttribute>]
#	[(csv [todrive <ToDriveAttribute>*]) | returnidonly]
def createForm(users):
  csvPF = None
  returnIdOnly = False
  title = ''
  body = {'mimeType': MIMETYPE_GA_FORM}
  ubody = {'includeFormInResponse': True, 'requests': []}
  pbody = _initPublishSettings()
  parentParms = initDriveFileAttributes()
  while Cmd.ArgumentsRemaining():
    myarg = getArgument()
    if myarg == 'title':
      title = getString(Cmd.OB_STRING)
      updateFormInfoRequest(myarg, title, ubody)
    elif myarg == 'description':
      updateFormInfoRequest(myarg, getString(Cmd.OB_STRING, minLen=0), ubody)
    elif myarg == 'isquiz':
      updateFormSettingsRequest('isQuiz', getBoolean(), ubody)
    elif myarg == 'json':
      jsonData = getJSON([])
      ubody['requests'].extend(jsonData.get('requests', []))
    elif _getPublishSettings(myarg, pbody):
      pass
    elif myarg == 'drivefilename':
      body['name'] = getString(Cmd.OB_DRIVE_FILE_NAME)
    elif getDriveFileParentAttribute(myarg, parentParms):
      pass
    elif myarg == 'returnidonly':
      returnIdOnly = True
    elif myarg == 'csv':
      csvPF = CSVPrintFile(['User', 'formId', 'name', 'title', 'responderUri'])
    elif csvPF and myarg == 'todrive':
      csvPF.GetTodriveParameters()
    else:
      unknownArgumentExit()
  if not title:
    missingArgumentExit('title')
  updateFormRequestUpdateMasks(ubody)
  if 'name' not in body:
    body['name']  = title
  i, count, users = getEntityArgument(users)
  for user in users:
    i += 1
    user, drive = buildGAPIServiceObject(API.DRIVE3, user, i, count)
    if not drive:
      continue
    if not _getDriveFileParentInfo(drive, user, i, count, body, parentParms):
      continue
    _, gform = buildGAPIServiceObject(API.FORMS, user, i, count)
    if not gform:
      continue
    try:
      result = callGAPI(drive.files(), 'create',
                        throwReasons=GAPI.DRIVE_USER_THROW_REASONS+[GAPI.FORBIDDEN, GAPI.INSUFFICIENT_PERMISSIONS, GAPI.INSUFFICIENT_PARENT_PERMISSIONS,
                                                                    GAPI.INVALID, GAPI.BAD_REQUEST, GAPI.CANNOT_ADD_PARENT,
                                                                    GAPI.FILE_NOT_FOUND, GAPI.UNKNOWN_ERROR, GAPI.STORAGE_QUOTA_EXCEEDED,
                                                                    GAPI.TEAMDRIVES_SHARING_RESTRICTION_NOT_ALLOWED,
                                                                    GAPI.TEAMDRIVE_FILE_LIMIT_EXCEEDED, GAPI.TEAMDRIVE_HIERARCHY_TOO_DEEP],
                        body=body, fields='id,name', supportsAllDrives=True)
      formId = result['id']
      form = callGAPI(gform.forms(), 'batchUpdate',
                      throwReasons=[GAPI.INVALID_ARGUMENT, GAPI.PERMISSION_DENIED],
                      formId=formId, body=ubody)
      if pbody['updateMask']:
        callGAPI(gform.forms(), 'setPublishSettings',
                 throwReasons=[GAPI.NOT_FOUND, GAPI.INVALID_ARGUMENT, GAPI.PERMISSION_DENIED],
                 formId=formId, body=pbody)
      if returnIdOnly:
        writeStdout(f'{formId}\n')
      elif not csvPF:
        entityActionPerformed([Ent.USER, user, Ent.FORM, title,
                               Ent.DRIVE_FILE, f"{result['name']}({formId})"])
      else:
        csvPF.WriteRow({'User': user, 'formId': formId,
                        'name': form['form']['info']['documentTitle'],
                        'title': form['form']['info']['title'],
                        'responderUri': form['form']['responderUri']})
    except (GAPI.forbidden, GAPI.insufficientFilePermissions, GAPI.insufficientParentPermissions,
            GAPI.invalid, GAPI.badRequest, GAPI.cannotAddParent,
            GAPI.fileNotFound, GAPI.unknownError, GAPI.storageQuotaExceeded, GAPI.teamDrivesSharingRestrictionNotAllowed,
            GAPI.teamDriveFileLimitExceeded, GAPI.teamDriveHierarchyTooDeep, GAPI.invalidArgument) as e:
      entityActionFailedWarning([Ent.USER, user, Ent.FORM, title, Ent.DRIVE_FILE, body['name']], str(e), i, count)
    except GAPI.permissionDenied:
      SvcAcctAPIDisabledExit()
    except (GAPI.serviceNotAvailable, GAPI.authError, GAPI.domainPolicy) as e:
      userDriveServiceNotEnabledWarning(user, str(e), i, count)
  if csvPF:
    csvPF.writeCSVfile('Forms')

# gam <UserTypeEntity> update form <DriveFileEntity>
#	[title <String>] [description <String>] [isquiz [Boolean>]] [<JSONData>]
#	[ispublished [<Boolean>] isacceptingresponses [<Boolean>]]
def updateForm(users):
  ubody = {'includeFormInResponse': False, 'requests': []}
  pbody = _initPublishSettings()
  fileIdEntity = getDriveFileEntity()
  while Cmd.ArgumentsRemaining():
    myarg = getArgument()
    if myarg == 'title':
      updateFormInfoRequest(myarg, getString(Cmd.OB_STRING), ubody)
    elif myarg == 'description':
      updateFormInfoRequest(myarg, getString(Cmd.OB_STRING, minLen=0), ubody)
    elif myarg == 'isquiz':
      updateFormSettingsRequest('isQuiz', getBoolean(), ubody)
    elif myarg == 'json':
      jsonData = getJSON([])
      ubody['requests'].extend(jsonData.get('requests', []))
    elif _getPublishSettings(myarg, pbody):
      pass
    else:
      unknownArgumentExit()
  updateFormRequestUpdateMasks(ubody)
  if not ubody['requests'] and not pbody['updateMask']:
    return
  i, count, users = getEntityArgument(users)
  for user in users:
    i += 1
    user, _, jcount = _validateUserGetFileIDs(user, i, count, fileIdEntity, entityType=Ent.FORM)
    if jcount == 0:
      continue
    _, gform = buildGAPIServiceObject(API.FORMS, user, i, count)
    if not gform:
      continue
    Ind.Increment()
    j = 0
    for formId in fileIdEntity['list']:
      j += 1
      try:
        if ubody['requests']:
          callGAPI(gform.forms(), 'batchUpdate',
                   throwReasons=[GAPI.NOT_FOUND, GAPI.INVALID_ARGUMENT, GAPI.PERMISSION_DENIED],
                   formId=formId, body=ubody)
        if pbody['updateMask']:
          callGAPI(gform.forms(), 'setPublishSettings',
                   throwReasons=[GAPI.NOT_FOUND, GAPI.INVALID_ARGUMENT, GAPI.PERMISSION_DENIED],
                   formId=formId, body=pbody)
        entityActionPerformed([Ent.USER, user, Ent.FORM, formId], j, jcount)
      except (GAPI.notFound, GAPI.invalidArgument) as e:
        entityActionFailedWarning([Ent.USER, user, Ent.FORM, formId], str(e), j, jcount)
    Ind.Decrement()

# gam <UserTypeEntity> print forms <DriveFileEntity> [todrive <ToDriveAttribute>*]
#	(addcsvdata <FieldName> <String>)*
#	[formatjson [quotechar <Character>]]
# gam <UserTypeEntity> show forms <DriveFileEntity>
#	[formatjson]
def printShowForms(users):
  csvPF = CSVPrintFile(['User', 'formId', 'name', 'title', 'description'], 'sortall') if Act.csvFormat() else None
  FJQC = FormatJSONQuoteChar(csvPF)
  fileIdEntity = getDriveFileEntity()
  addCSVData = {}
  while Cmd.ArgumentsRemaining():
    myarg = getArgument()
    if csvPF and myarg == 'todrive':
      csvPF.GetTodriveParameters()
    elif csvPF and myarg == 'addcsvdata':
      getAddCSVData(addCSVData)
    else:
      FJQC.GetFormatJSONQuoteChar(myarg, True)
  if csvPF and addCSVData:
    csvPF.AddTitles(sorted(addCSVData.keys()))
    if FJQC.formatJSON:
      csvPF.AddJSONTitles(sorted(addCSVData.keys()))
      csvPF.MoveJSONTitlesToEnd(['JSON'])
    csvPF.SetSortAllTitles()
  i, count, users = getEntityArgument(users)
  for user in users:
    i += 1
    user, _, jcount = _validateUserGetFileIDs(user, i, count, fileIdEntity,
                                              entityType=[Ent.FORM, None][csvPF is not None or FJQC.formatJSON])
    if jcount == 0:
      continue
    _, gform = buildGAPIServiceObject(API.FORMS, user, i, count)
    if not gform:
      continue
    Ind.Increment()
    j = 0
    for formId in fileIdEntity['list']:
      j += 1
      try:
        result = callGAPI(gform.forms(), 'get',
                          throwReasons=[GAPI.NOT_FOUND, GAPI.PERMISSION_DENIED],
                          formId=formId)
        if 'publishSettings' in result and 'publishState' in result['publishSettings']:
          result['publishSettings']['publishState'].setdefault('isPublished', False)
          result['publishSettings']['publishState'].setdefault('isAcceptingResponses', False)
        if not csvPF:
          if not FJQC.formatJSON:
            printEntity([Ent.FORM, result['formId']], j, jcount)
            Ind.Increment()
            showJSON(None, result)
            Ind.Decrement()
          else:
            printLine(json.dumps(cleanJSON(result), ensure_ascii=False, sort_keys=True))
        else:
          info = result.pop('info')
          baserow = {'User': user, 'formId': formId, 'name': info['documentTitle'],
                     'title': info.get('title', ''), 'description': info.get('description', '')}
          if addCSVData:
            baserow.update(addCSVData)
          row = flattenJSON(result, flattened=baserow.copy())
          if not FJQC.formatJSON:
            csvPF.WriteRowTitles(row)
          elif csvPF.CheckRowTitles(row):
            result['info'] = info
            baserow['JSON'] = json.dumps(cleanJSON(result), ensure_ascii=False, sort_keys=True)
            csvPF.WriteRowNoFilter(baserow)
      except GAPI.notFound as e:
        entityActionFailedWarning([Ent.USER, user, Ent.FORM, formId], str(e), j, jcount)
    Ind.Decrement()
  if csvPF:
    csvPF.writeCSVfile('Forms')

FORM_RESPONSE_TIME_OBJECTS = {'createTime', 'lastSubmittedTime'}

# gam <UserTypeEntity> print formresponses <DriveFileEntity> [todrive <ToDriveAttribute>*]
#	[filter <String> (filtertime<String> <Time>)*]
#	(addcsvdata <FieldName> <String>)*
#	[countsonly|(formatjson [quotechar <Character>])]
# gam <UserTypeEntity> show formresponses <DriveFileEntity>
#	[filter <String> (filtertime<String> <Time>)*]
#	[countsonly|formatjson]
def printShowFormResponses(users):
  csvPF = CSVPrintFile(['User', 'formId', 'responseId', 'createTime', 'lastSubmittedTime', 'respondentEmail', 'totalScore'],
                       'sortall', indexedTitles=['answers']) if Act.csvFormat() else None
  FJQC = FormatJSONQuoteChar(csvPF)
  frfilter = None
  filterTimes = {}
  fileIdEntity = getDriveFileEntity()
  countsOnly = False
  addCSVData = {}
  while Cmd.ArgumentsRemaining():
    myarg = getArgument()
    if csvPF and myarg == 'todrive':
      csvPF.GetTodriveParameters()
    elif myarg.startswith('filtertime'):
      filterTimes[myarg] = getTimeOrDeltaFromNow()
    elif myarg in {'filter', 'filters'}:
      frfilter = getString(Cmd.OB_STRING)
    elif myarg == 'countsonly':
      countsOnly = True
    elif csvPF and myarg == 'addcsvdata':
      getAddCSVData(addCSVData)
    else:
      FJQC.GetFormatJSONQuoteChar(myarg, True)
  if filterTimes and frfilter is not None:
    for filterTimeName, filterTimeValue in filterTimes.items():
      frfilter = frfilter.replace(f'#{filterTimeName}#', filterTimeValue)
  if csvPF:
    if countsOnly:
      csvPF.SetTitles(['User', 'formId', 'responses'])
    if addCSVData:
      csvPF.AddTitles(sorted(addCSVData.keys()))
      if FJQC.formatJSON:
        csvPF.AddJSONTitles(sorted(addCSVData.keys()))
        csvPF.MoveJSONTitlesToEnd(['JSON'])
    csvPF.SetSortAllTitles()
  i, count, users = getEntityArgument(users)
  for user in users:
    i += 1
    user, _, jcount = _validateUserGetFileIDs(user, i, count, fileIdEntity,
                                              entityType=[Ent.FORM, None][csvPF is not None or FJQC.formatJSON])
    if jcount == 0:
      continue
    _, gform = buildGAPIServiceObject(API.FORMS, user, i, count)
    if not gform:
      continue
    Ind.Increment()
    j = 0
    for formId in fileIdEntity['list']:
      j += 1
      try:
        results = callGAPIpages(gform.forms().responses(), 'list', 'responses',
                                throwReasons=[GAPI.NOT_FOUND, GAPI.PERMISSION_DENIED],
                                filter=frfilter, formId=formId)
        kcount = len(results)
        if countsOnly:
          if not csvPF:
            printEntityKVList([Ent.FORM, formId], [Ent.Plural(Ent.FORM_RESPONSE), kcount], j, jcount)
          else:
            row = {'User': user, 'formId': formId, 'responses': kcount}
            if addCSVData:
              row.update(addCSVData)
            csvPF.WriteRowTitles(row)
          continue
        if not csvPF:
          if not FJQC.formatJSON:
            entityPerformActionNumItems([Ent.FORM, formId], kcount, Ent.FORM_RESPONSE, j, jcount)
          Ind.Increment()
          k = 0
          for response in results:
            k += 1
            if not FJQC.formatJSON:
              printEntity([Ent.FORM_RESPONSE, response['responseId']], k, kcount)
              Ind.Increment()
              showJSON(None, response, timeObjects=FORM_RESPONSE_TIME_OBJECTS)
              Ind.Decrement()
            else:
              printLine(json.dumps(cleanJSON(response, timeObjects=FORM_RESPONSE_TIME_OBJECTS),
                                   ensure_ascii=False, sort_keys=True))
          Ind.Decrement()
        else:
          baserow = {'User': user, 'formId': formId}
          if addCSVData:
            baserow.update(addCSVData)
          for response in results:
            row = flattenJSON(response, flattened=baserow.copy())
            if not FJQC.formatJSON:
              csvPF.WriteRowTitles(row)
            elif csvPF.CheckRowTitles(row):
              row = baserow.copy()
              row.update({'responseId': response['responseId'],
                          'createTime': response['createTime'],
                          'lastSubmittedTime': response['lastSubmittedTime'],
                          'respondentEmail': response.get('respondentEmail', ''),
                          'totalScore': response.get('totalScore', ''),
                          'JSON': json.dumps(cleanJSON(response, timeObjects=FORM_RESPONSE_TIME_OBJECTS),
                                             ensure_ascii=False, sort_keys=True)})
              csvPF.WriteRowNoFilter(row)
      except GAPI.notFound as e:
        entityActionFailedWarning([Ent.USER, user, Ent.FORM, formId], str(e), j, jcount)
    Ind.Decrement()
  if csvPF:
    csvPF.writeCSVfile('Form Responses')

EMAILSETTINGS_OLD_NEW_OLD_FORWARD_ACTION_MAP = {
  'ARCHIVE': 'archive',
  'DELETE': 'trash',
  'KEEP': 'leaveInInBox',
  'MARK_READ': 'markRead',
  }

