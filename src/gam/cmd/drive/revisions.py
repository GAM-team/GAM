"""File revision management.

Part of the drive sub-package, extracted from drive.py."""

"""GAM Google Drive file, permission, shared drive, and label management."""

import re
import sys

from gam.cmd.drive.core import _getDriveFileNameFromId, _validateUserGetFileIDs, getDriveFileEntity

from gamlib import glaction
from gamlib import glapi as API
from gamlib import glcfg as GC
from gamlib import glclargs
from gamlib import glentity
from gamlib import glgapi as GAPI
from gamlib import glglobals as GM
from gamlib import glindent
from gamlib import glmsgs as Msg

Act = glaction.GamAction()
Ent = glentity.GamEntity()
Ind = glindent.GamIndent()
Cmd = glclargs.GamCLArgs()

APPLICATION_VND_GOOGLE_APPS = 'application/vnd.google-apps.'
MIMETYPE_GA_DOCUMENT = f'{APPLICATION_VND_GOOGLE_APPS}document'
MIMETYPE_GA_DRAWING = f'{APPLICATION_VND_GOOGLE_APPS}drawing'
MIMETYPE_GA_FILE = f'{APPLICATION_VND_GOOGLE_APPS}file'
MIMETYPE_GA_FOLDER = f'{APPLICATION_VND_GOOGLE_APPS}folder'
MIMETYPE_GA_FORM = f'{APPLICATION_VND_GOOGLE_APPS}form'
MIMETYPE_GA_FUSIONTABLE = f'{APPLICATION_VND_GOOGLE_APPS}fusiontable'
MIMETYPE_GA_JAM = f'{APPLICATION_VND_GOOGLE_APPS}jam'
MIMETYPE_GA_MAP = f'{APPLICATION_VND_GOOGLE_APPS}map'
MIMETYPE_GA_PRESENTATION = f'{APPLICATION_VND_GOOGLE_APPS}presentation'
MIMETYPE_GA_SCRIPT = f'{APPLICATION_VND_GOOGLE_APPS}script'
MIMETYPE_GA_SCRIPT_JSON = f'{APPLICATION_VND_GOOGLE_APPS}script+json'
MIMETYPE_GA_SHORTCUT = f'{APPLICATION_VND_GOOGLE_APPS}shortcut'
MIMETYPE_GA_3P_SHORTCUT = f'{APPLICATION_VND_GOOGLE_APPS}drive-sdk'
MIMETYPE_GA_SITE = f'{APPLICATION_VND_GOOGLE_APPS}site'
MIMETYPE_GA_SPREADSHEET = f'{APPLICATION_VND_GOOGLE_APPS}spreadsheet'
ME_IN_OWNERS = "'me' in owners"
ME_IN_OWNERS_AND = ME_IN_OWNERS + " and "
NOT_ME_IN_OWNERS = "not " + ME_IN_OWNERS
NOT_ME_IN_OWNERS_AND = NOT_ME_IN_OWNERS + " and "
WITH_ANY_FILE_NAME = "name = '{0}'"
WITH_MY_FILE_NAME = ME_IN_OWNERS_AND + WITH_ANY_FILE_NAME
WITH_OTHER_FILE_NAME = NOT_ME_IN_OWNERS_AND + WITH_ANY_FILE_NAME
ROOT = 'root'
ORPHANS = 'Orphans'
SHARED_WITHME = 'SharedWithMe'
SHARED_DRIVES = 'SharedDrives'

def _getMain():
  return sys.modules['gam']

def __getattr__(name):
  """Fall back to gam module for any undefined names."""
  main = _getMain()
  try:
    return getattr(main, name)
  except AttributeError:
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")

def getRevisionsEntity():
  revisionsEntity = {'list': [], 'dict': None, 'count': None, 'time': None, 'range': None}
  startEndTime = _getMain().StartEndTime()
  entitySelector = _getMain().getEntitySelector()
  if entitySelector:
    entityList = _getMain().getEntitySelection(entitySelector, False)
    if isinstance(entityList, dict):
      revisionsEntity['dict'] = entityList
    else:
      revisionsEntity['list'] = entityList
  else:
    myarg = _getMain().getString(Cmd.OB_DRIVE_FILE_REVISION_ID, checkBlank=True)
    mycmd = myarg.lower()
    if mycmd == 'id':
      revisionsEntity['list'] = _getMain().getStringReturnInList(Cmd.OB_DRIVE_FILE_REVISION_ID)
    elif mycmd[:3] == 'id:':
      revisionsEntity['list'] = [myarg[3:]]
    elif mycmd == 'ids':
      revisionsEntity['list'] = _getMain().getString(Cmd.OB_DRIVE_FILE_REVISION_ID).replace(',', ' ').split()
    elif mycmd[:4] == 'ids:':
      revisionsEntity['list'] = myarg[4:].replace(',', ' ').split()
    elif mycmd in {'first', 'last', 'allexceptfirst', 'allexceptlast'}:
      revisionsEntity['count'] = (mycmd, _getMain().getInteger(minVal=1))
    elif mycmd in {'before', 'after'}:
      dateTime, _, _ = _getMain().getTimeOrDeltaFromNow(True)
      revisionsEntity['time'] = (mycmd, dateTime)
    elif mycmd == 'range':
      startEndTime.Get(mycmd)
      revisionsEntity['range'] = (mycmd, startEndTime.startDateTime, startEndTime.endDateTime)
    else:
      revisionsEntity['list'] = [myarg]
  return revisionsEntity

def _selectRevisionIds(drive, fileId, origUser, user, i, count, j, jcount, revisionsEntity):
  if revisionsEntity['list']:
    return revisionsEntity['list']
  if revisionsEntity['dict']:
    if not GM.Globals[GM.CSV_SUBKEY_FIELD]:
      return revisionsEntity['dict'][fileId]
    return revisionsEntity['dict'][origUser][fileId]
  try:
    results = _getMain().callGAPIpages(drive.revisions(), 'list', 'revisions',
                            throwReasons=GAPI.DRIVE_ACCESS_THROW_REASONS+[GAPI.BAD_REQUEST, GAPI.REVISIONS_NOT_SUPPORTED],
                            fileId=fileId, fields='nextPageToken,revisions(id,modifiedTime)',
                            pageSize=GC.Values[GC.DRIVE_MAX_RESULTS])
  except (GAPI.fileNotFound, GAPI.forbidden, GAPI.internalError, GAPI.insufficientFilePermissions, GAPI.unknownError,
          GAPI.badRequest, GAPI.revisionsNotSupported) as e:
    _getMain().entityActionFailedWarning([Ent.USER, user, Ent.DRIVE_FILE_OR_FOLDER_ID, fileId], str(e), j, jcount)
    return []
  except (GAPI.serviceNotAvailable, GAPI.authError, GAPI.domainPolicy) as e:
    _getMain().userDriveServiceNotEnabledWarning(user, str(e), i, count)
    return []
  numRevisions = len(results)
  if numRevisions == 0:
    return []
  if revisionsEntity['count']:
    countType = revisionsEntity['count'][0]
    count = revisionsEntity['count'][1]
    revisionIds = [revision['id'] for revision in results]
    if countType == 'first':
      if count >= numRevisions:
        return revisionIds
      return revisionIds[:count]
    if countType == 'last':
      if count >= numRevisions:
        return revisionIds
      return revisionIds[-count:]
    if countType == 'allexceptfirst':
      if count >= numRevisions:
        return []
      return revisionIds[count:]
# count: allexceptlast
    if count >= numRevisions:
      return []
    return revisionIds[:-count]
  revisionIds = []
  if revisionsEntity['time']:
    dateTime = revisionsEntity['time'][1]
    count = 0
    if revisionsEntity['time'][0] == 'before':
      for revision in results:
        modifiedDateTime = arrow.get(revision['modifiedTime'])
        if modifiedDateTime >= dateTime:
          break
        revisionIds.append(revision['id'])
        count += 1
      if count >= numRevisions:
        return revisionIds[:-1]
      return revisionIds
# time: after
    for revision in results:
      modifiedDateTime = arrow.get(revision['modifiedTime'])
      if modifiedDateTime >= dateTime:
        revisionIds.append(revision['id'])
        count += 1
    if count >= numRevisions:
      return revisionIds[1:]
    return revisionIds
# range
  startDateTime = revisionsEntity['range'][1]
  endDateTime = revisionsEntity['range'][2]
  count = 0
  for revision in results:
    modifiedDateTime = arrow.get(revision['modifiedTime'])
    if modifiedDateTime >= startDateTime:
      if modifiedDateTime >= endDateTime:
        break
      revisionIds.append(revision['id'])
      count += 1
  if count >= numRevisions:
    return revisionIds[1:]
  return revisionIds

# gam <UserTypeEntity> delete filerevisions <DriveFileEntity> select <DriveFileRevisionIdEntity> [previewdelete]
#	[showtitles] [doit] [max_to_delete <Number>]
def deleteFileRevisions(users):
  fileIdEntity = getDriveFileEntity()
  revisionsEntity = None
  previewDelete = showTitles = doIt = False
  maxToProcess = 1
  while Cmd.ArgumentsRemaining():
    myarg = _getMain().getArgument()
    if myarg == 'select':
      revisionsEntity = getRevisionsEntity()
    elif myarg == 'previewdelete':
      previewDelete = True
    elif myarg == 'showtitles':
      showTitles = True
    elif myarg == 'doit':
      doIt = True
    elif myarg in {'maxtodelete', 'maxtoprocess'}:
      maxToProcess = _getMain().getInteger(minVal=0)
    else:
      _getMain().unknownArgumentExit()
  if not revisionsEntity:
    _getMain().missingArgumentExit('select <DriveFileRevisionIdEntity>')
  i, count, users = _getMain().getEntityArgument(users)
  for user in users:
    i += 1
    origUser = user
    user, drive, jcount = _validateUserGetFileIDs(user, i, count, fileIdEntity)
    if jcount == 0:
      continue
    j = 0
    for fileId in fileIdEntity['list']:
      j += 1
      fileName = fileId
      entityType = Ent.DRIVE_FILE_OR_FOLDER_ID
      if showTitles:
        fileName, entityType, _ = _getDriveFileNameFromId(drive, fileId)
      revisionIds = _selectRevisionIds(drive, fileId, origUser, user, i, count, j, jcount, revisionsEntity)
      kcount = len(revisionIds)
      if kcount == 0:
        _getMain().entityNumEntitiesActionNotPerformedWarning([Ent.USER, user, entityType, fileName], Ent.DRIVE_FILE_REVISION, kcount,
                                                   Msg.NO_ENTITIES_MATCHED.format(Ent.Plural(Ent.DRIVE_FILE_REVISION)), j, jcount)
        _getMain().setSysExitRC(_getMain().NO_ENTITIES_FOUND_RC)
        continue
      if not previewDelete:
        if maxToProcess and kcount > maxToProcess:
          _getMain().entityNumEntitiesActionNotPerformedWarning([Ent.USER, user, entityType, fileName], Ent.DRIVE_FILE_REVISION, kcount,
                                                     Msg.COUNT_N_EXCEEDS_MAX_TO_PROCESS_M.format(kcount, Act.ToPerform(), maxToProcess), j, jcount)
          continue
        if not doIt:
          _getMain().entityNumEntitiesActionNotPerformedWarning([Ent.USER, user, entityType, fileName], Ent.DRIVE_FILE_REVISION, kcount,
                                                     Msg.USE_DOIT_ARGUMENT_TO_PERFORM_ACTION, j, jcount)
          continue
        _getMain().entityPerformActionNumItems([Ent.USER, user, entityType, fileName], kcount, Ent.DRIVE_FILE_REVISION, j, jcount)
      else:
        _getMain().entityPerformActionNumItemsModifier([Ent.USER, user, entityType, fileName], kcount, Ent.DRIVE_FILE_REVISION, Msg.PREVIEW_ONLY, j, jcount)
      Ind.Increment()
      k = 0
      for revisionId in revisionIds:
        k += 1
        if not previewDelete:
          try:
            _getMain().callGAPI(drive.revisions(), 'delete',
                     throwReasons=GAPI.DRIVE_ACCESS_THROW_REASONS+[GAPI.BAD_REQUEST, GAPI.REVISION_NOT_FOUND, GAPI.REVISION_DELETION_NOT_SUPPORTED,
                                                                   GAPI.CANNOT_DELETE_ONLY_REVISION, GAPI.REVISIONS_NOT_SUPPORTED],
                     fileId=fileId, revisionId=revisionId)
            _getMain().entityActionPerformed([Ent.USER, user, entityType, fileName, Ent.DRIVE_FILE_REVISION, revisionId], k, kcount)
          except (GAPI.fileNotFound, GAPI.forbidden, GAPI.internalError, GAPI.insufficientFilePermissions, GAPI.unknownError,
                  GAPI.badRequest, GAPI.revisionDeletionNotSupported, GAPI.cannotDeleteOnlyRevision, GAPI.revisionsNotSupported) as e:
            _getMain().entityActionFailedWarning([Ent.USER, user, entityType, fileName], str(e), j, jcount)
          except GAPI.revisionNotFound:
            _getMain().entityDoesNotHaveItemWarning([Ent.USER, user, entityType, fileName, Ent.DRIVE_FILE_REVISION, revisionId], k, kcount)
          except (GAPI.serviceNotAvailable, GAPI.authError, GAPI.domainPolicy) as e:
            _getMain().userDriveServiceNotEnabledWarning(user, str(e), i, count)
            break
        else:
          _getMain().entityActionNotPerformedWarning([Ent.USER, user, entityType, fileName, Ent.DRIVE_FILE_REVISION, revisionId], Msg.PREVIEW_ONLY, k, kcount)
      Ind.Decrement()

REVISIONS_FIELDS_CHOICE_MAP = {
  'keepforever': 'keepForever',
  'published': 'published',
  'publishauto': 'publishAuto',
  'publishedoutsidedomain': 'publishedOutsideDomain'
  }
# gam <UserTypeEntity> update filerevisions <DriveFileEntity> select <DriveFileRevisionIdEntity> [previewupdate]
#	[published [<Boolean>]] [publishauto [<Boolean>]] [publishedoutsidedomain [<Boolean>]]
#	[keepforever [<Boolean>]}
#	[showtitles] [doit] [max_to_update <Number>]
def updateFileRevisions(users):
  fileIdEntity = getDriveFileEntity()
  revisionsEntity = None
  previewUpdate = showTitles = doIt = False
  maxToProcess = 1
  body = {}
  while Cmd.ArgumentsRemaining():
    myarg = _getMain().getArgument()
    if myarg == 'select':
      revisionsEntity = getRevisionsEntity()
    elif myarg in REVISIONS_FIELDS_CHOICE_MAP:
      body[REVISIONS_FIELDS_CHOICE_MAP[myarg]] = _getMain().getBoolean()
    elif myarg == 'previewupdate':
      previewUpdate = True
    elif myarg == 'showtitles':
      showTitles = True
    elif myarg == 'doit':
      doIt = True
    elif myarg in {'maxtoupdate', 'maxtoprocess'}:
      maxToProcess = _getMain().getInteger(minVal=0)
    else:
      _getMain().unknownArgumentExit()
  if not revisionsEntity:
    _getMain().missingArgumentExit('select <DriveFileRevisionIdEntity>')
  i, count, users = _getMain().getEntityArgument(users)
  for user in users:
    i += 1
    origUser = user
    user, drive, jcount = _validateUserGetFileIDs(user, i, count, fileIdEntity)
    if jcount == 0:
      continue
    j = 0
    for fileId in fileIdEntity['list']:
      j += 1
      fileName = fileId
      entityType = Ent.DRIVE_FILE_OR_FOLDER_ID
      if showTitles:
        fileName, entityType, _ = _getDriveFileNameFromId(drive, fileId)
      revisionIds = _selectRevisionIds(drive, fileId, origUser, user, i, count, j, jcount, revisionsEntity)
      kcount = len(revisionIds)
      if kcount == 0:
        _getMain().entityNumEntitiesActionNotPerformedWarning([Ent.USER, user, entityType, fileName], Ent.DRIVE_FILE_REVISION, kcount,
                                                   Msg.NO_ENTITIES_MATCHED.format(Ent.Plural(Ent.DRIVE_FILE_REVISION)), j, jcount)
        _getMain().setSysExitRC(_getMain().NO_ENTITIES_FOUND_RC)
        continue
      if not previewUpdate:
        if maxToProcess and kcount > maxToProcess:
          _getMain().entityNumEntitiesActionNotPerformedWarning([Ent.USER, user, entityType, fileName], Ent.DRIVE_FILE_REVISION, kcount,
                                                     Msg.COUNT_N_EXCEEDS_MAX_TO_PROCESS_M.format(kcount, Act.ToPerform(), maxToProcess), j, jcount)
          continue
        if not doIt:
          _getMain().entityNumEntitiesActionNotPerformedWarning([Ent.USER, user, entityType, fileName], Ent.DRIVE_FILE_REVISION, kcount,
                                                     Msg.USE_DOIT_ARGUMENT_TO_PERFORM_ACTION, j, jcount)
          continue
        _getMain().entityPerformActionNumItems([Ent.USER, user, entityType, fileName], kcount, Ent.DRIVE_FILE_REVISION, j, jcount)
      else:
        _getMain().entityPerformActionNumItemsModifier([Ent.USER, user, entityType, fileName], kcount, Ent.DRIVE_FILE_REVISION, Msg.PREVIEW_ONLY, j, jcount)
      Ind.Increment()
      k = 0
      for revisionId in revisionIds:
        k += 1
        if not previewUpdate:
          try:
            _getMain().callGAPI(drive.revisions(), 'update',
                     throwReasons=GAPI.DRIVE_ACCESS_THROW_REASONS+[GAPI.BAD_REQUEST, GAPI.REVISION_NOT_FOUND, GAPI.REVISIONS_NOT_SUPPORTED],
                     fileId=fileId, revisionId=revisionId, body=body)
            _getMain().entityActionPerformed([Ent.USER, user, entityType, fileName, Ent.DRIVE_FILE_REVISION, revisionId], k, kcount)
          except (GAPI.fileNotFound, GAPI.forbidden, GAPI.internalError, GAPI.insufficientFilePermissions, GAPI.unknownError,
                  GAPI.badRequest, GAPI.revisionsNotSupported) as e:
            _getMain().entityActionFailedWarning([Ent.USER, user, entityType, fileName], str(e), j, jcount)
          except GAPI.revisionNotFound:
            _getMain().entityDoesNotHaveItemWarning([Ent.USER, user, entityType, fileName, Ent.DRIVE_FILE_REVISION, revisionId], k, kcount)
          except (GAPI.serviceNotAvailable, GAPI.authError, GAPI.domainPolicy) as e:
            _getMain().userDriveServiceNotEnabledWarning(user, str(e), i, count)
            break
        else:
          _getMain().entityActionNotPerformedWarning([Ent.USER, user, entityType, fileName, Ent.DRIVE_FILE_REVISION, revisionId], Msg.PREVIEW_ONLY, k, kcount)
      Ind.Decrement()

def _selectRevisionResults(results, fileId, origUser, revisionsEntity, previewDelete):
  numRevisions = len(results)
  if numRevisions == 0:
    return results
  if revisionsEntity['count']:
    countType = revisionsEntity['count'][0]
    count = revisionsEntity['count'][1]
    if countType == 'first':
      if count >= numRevisions:
        if previewDelete:
          return results[:-1]
        return results
      return results[:count]
    if countType == 'last':
      if count >= numRevisions:
        if previewDelete:
          return results[1:]
        return results
      return results[-count:]
    if countType == 'allexceptfirst':
      if count >= numRevisions:
        return []
      return results[count:]
# count: allexceptlast
    if count >= numRevisions:
      return []
    return results[:-count]
  if revisionsEntity['time']:
    dateTime = revisionsEntity['time'][1]
    count = 0
    if revisionsEntity['time'][0] == 'before':
      for revision in results:
        modifiedDateTime = arrow.get(revision['modifiedTime'])
        if modifiedDateTime >= dateTime:
          break
        count += 1
      if count >= numRevisions:
        if previewDelete:
          return results[:-1]
        return results
      return results[:count]
# time: after
    for revision in results:
      modifiedDateTime = arrow.get(revision['modifiedTime'])
      if modifiedDateTime >= dateTime:
        break
      count += 1
    if count == 0:
      if previewDelete:
        return results[1:]
      return results
    if count >= numRevisions:
      return []
    return results[count:]
  if revisionsEntity['range']:
    startDateTime = revisionsEntity['range'][1]
    endDateTime = revisionsEntity['range'][2]
    count = 0
    selectedResults = []
    for revision in  results:
      modifiedDateTime = arrow.get(revision['modifiedTime'])
      if modifiedDateTime >= startDateTime:
        if modifiedDateTime >= endDateTime:
          break
        selectedResults.append(revision)
        count += 1
    if count >= numRevisions:
      if previewDelete:
        return selectedResults[1:]
    return selectedResults
# revisionsIds
  selectedResults = []
  if revisionsEntity['dict']:
    if not GM.Globals[GM.CSV_SUBKEY_FIELD]:
      revisionIds = revisionsEntity['dict'][fileId]
    else:
      revisionIds = revisionsEntity['dict'][origUser][fileId]
  else:
    revisionIds = revisionsEntity['list']
  return [revision for revision in results if revision['id'] in revisionIds]

FILEREVISIONS_FIELDS_CHOICE_MAP = {
  'filesize': 'size',
  'id': 'id',
  'keepforever': 'keepForever',
  'lastmodifyinguser': 'lastModifyingUser',
  'lastmodifyingusername': 'lastModifyingUser.displayName',
  'md5checksum': 'md5Checksum',
  'mimetype': 'mimeType',
  'modifieddate': 'modifiedTime',
  'modifiedtime': 'modifiedTime',
  'originalfilename': 'originalFilename',
  'pinned': 'keepForever',
  'published': 'published',
  'publishauto': 'publishAuto',
  'publishedoutsidedomain': 'publishedOutsideDomain',
  'size': 'size',
  }

FILEREVISIONS_TIME_OBJECTS = {'modifiedTime'}

def _showRevision(revision, i=0, count=0):
  _getMain().printEntity([Ent.DRIVE_FILE_REVISION, revision['id']], i, count)
  Ind.Increment()
  _getMain().showJSON(None, revision, ['id'], timeObjects=FILEREVISIONS_TIME_OBJECTS)
  Ind.Decrement()

DRIVE_REVISIONS_INDEXED_TITLES = ['revisions']

# gam <UserTypeEntity> show filerevisions <DriveFileEntity>
#	[select <DriveFileRevisionIDEntity>]
#	[previewdelete] [showtitles]
#	[<RevisionsFieldName>*|(fields <RevisionsFieldNameList>)]
#	(orderby <DriveFileOrderByFieldName> [ascending|descending])*
#	[stripcrsfromname]
# gam <UserTypeEntity> print filerevisions <DriveFileEntity> [todrive <ToDriveAttribute>*]
#	[select <DriveFileRevisionIDEntity>]
#	[previewdelete] [showtitles] [oneitemperrow]
#	[<RevisionsFieldName>*|(fields <RevisionsFieldNameList>)]
#	(orderby <DriveFileOrderByFieldName> [ascending|descending])*
#	[stripcrsfromname]
def printShowFileRevisions(users):
  csvPF = _getMain().CSVPrintFile(['Owner', 'id']) if Act.csvFormat() else None
  fieldsList = []
  fileIdEntity = getDriveFileEntity()
  revisionsEntity = None
  oneItemPerRow = previewDelete = showTitles = stripCRsFromName = False
  OBY = _getMain().OrderBy(DRIVEFILE_ORDERBY_CHOICE_MAP)
  while Cmd.ArgumentsRemaining():
    myarg = _getMain().getArgument()
    if csvPF and myarg == 'todrive':
      csvPF.GetTodriveParameters()
    elif myarg == 'select':
      revisionsEntity = getRevisionsEntity()
    elif csvPF and myarg == 'oneitemperrow':
      oneItemPerRow = True
      if csvPF:
        csvPF.AddTitles('revision.id')
    elif myarg == 'orderby':
      OBY.GetChoice()
    elif myarg == 'previewdelete':
      previewDelete = True
    elif myarg == 'showtitles':
      showTitles = True
      if csvPF:
        csvPF.AddTitles('name')
    elif myarg == 'stripcrsfromname':
      stripCRsFromName = True
    elif _getMain().getFieldsList(myarg, FILEREVISIONS_FIELDS_CHOICE_MAP, fieldsList, initialField='id'):
      pass
    else:
      _getMain().unknownArgumentExit()
  if fieldsList:
    fields = _getMain().getItemFieldsFromFieldsList('revisions', fieldsList)
  else:
    fields = '*'
  i, count, users = _getMain().getEntityArgument(users)
  for user in users:
    i += 1
    origUser = user
    user, drive, jcount = _validateUserGetFileIDs(user, i, count, fileIdEntity,
                                                  entityType=[Ent.DRIVE_FILE_OR_FOLDER, None][csvPF is not None],
                                                  orderBy=OBY.orderBy)
    if jcount == 0:
      continue
    Ind.Increment()
    j = 0
    for fileId in fileIdEntity['list']:
      j += 1
      fileName = fileId
      entityType = Ent.DRIVE_FILE_OR_FOLDER_ID
      if showTitles:
        fileName, entityType, _ = _getDriveFileNameFromId(drive, fileId, not csvPF)
        if stripCRsFromName:
          fileName = _getMain()._stripControlCharsFromName(fileName)
      try:
        results = _getMain().callGAPIpages(drive.revisions(), 'list', 'revisions',
                                throwReasons=GAPI.DRIVE_ACCESS_THROW_REASONS+[GAPI.BAD_REQUEST, GAPI.REVISIONS_NOT_SUPPORTED],
                                fileId=fileId, fields=fields, pageSize=GC.Values[GC.DRIVE_MAX_RESULTS])
      except (GAPI.fileNotFound, GAPI.forbidden, GAPI.internalError, GAPI.insufficientFilePermissions, GAPI.unknownError,
              GAPI.badRequest, GAPI.revisionsNotSupported) as e:
        _getMain().entityActionFailedWarning([Ent.USER, user, Ent.DRIVE_FILE_OR_FOLDER_ID, fileId], str(e), j, jcount)
        continue
      except (GAPI.serviceNotAvailable, GAPI.authError, GAPI.domainPolicy) as e:
        _getMain().userDriveServiceNotEnabledWarning(user, str(e), i, count)
        break
      if revisionsEntity:
        results = _selectRevisionResults(results, fileId, origUser, revisionsEntity, previewDelete)
      if not csvPF:
        kcount = len(results)
        _getMain().entityPerformActionNumItems([entityType, fileName], kcount, Ent.DRIVE_FILE_REVISION, j, jcount)
        Ind.Increment()
        k = 0
        for revision in results:
          k += 1
          _showRevision(revision, k, kcount)
        Ind.Decrement()
      elif results:
        if oneItemPerRow:
          for revision in results:
            row = {'Owner': user, 'id': fileId}
            if showTitles:
              row['name'] = fileName
            csvPF.WriteRowTitles(_getMain().flattenJSON({'revision': revision}, flattened=row, timeObjects=FILEREVISIONS_TIME_OBJECTS))
        else:
          if showTitles:
            csvPF.WriteRowTitles(_getMain().flattenJSON({'revisions': results}, flattened={'Owner': user, 'id': fileId, 'name': fileName}, timeObjects=FILEREVISIONS_TIME_OBJECTS))
          else:
            csvPF.WriteRowTitles(_getMain().flattenJSON({'revisions': results}, flattened={'Owner': user, 'id': fileId}, timeObjects=FILEREVISIONS_TIME_OBJECTS))
    Ind.Decrement()
  if csvPF:
    if oneItemPerRow:
      csvPF.SetSortTitles(['Owner', 'id', 'name', 'revision.id'])
    else:
      csvPF.SetSortTitles(['Owner', 'id', 'revisions'])
      csvPF.SetIndexedTitles(DRIVE_REVISIONS_INDEXED_TITLES)
    csvPF.writeCSVfile('Drive File Revisions')

def _stripMeInOwners(query):
  if not query:
    return query
  query = query.replace(ME_IN_OWNERS_AND, '')
  query = query.replace(_getMain().AND_ME_IN_OWNERS, '')
  return query.replace(ME_IN_OWNERS, '').strip()

def _stripNotMeInOwners(query):
  if not query:
    return query
  query = query.replace(NOT_ME_IN_OWNERS_AND, '')
  query = query.replace(_getMain().AND_NOT_ME_IN_OWNERS, '')
  return query.replace(NOT_ME_IN_OWNERS, '').strip()

def _updateAnyOwnerQuery(query):
  query = _stripNotMeInOwners(query)
  return _stripMeInOwners(query)

