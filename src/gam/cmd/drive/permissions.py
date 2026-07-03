"""Drive file permissions and ACLs.

Part of the drive sub-package, extracted from drive.py."""

"""GAM Google Drive file, permission, shared drive, and label management."""

import re
import json
import sys

from gam.cmd.drive.core import _getDriveFileNameFromId, _getSharedDriveNameFromId, _validateUserGetFileIDs, _validateUserSharedDrive, cleanFileIDsList, getDriveFileEntity, getSharedDriveEntity, initDriveFileEntity
from gam.cmd.drive.filepaths import _finalizeIncludePermissionsForView, _getIncludePermissionsForView, _mapDrivePermissionNames
from gam.cmd.drive.filetree import _validateACLAttributes, _validateACLOwnerType

from gam.util.csv_pf import RI_ENTITY, RI_I, RI_COUNT, RI_J, RI_JCOUNT, RI_ITEM

from gamlib import glaction
from gamlib import glapi as API
from gamlib import glcfg as GC
from gamlib import glclargs
from gamlib import glentity
from gamlib import glgapi as GAPI
from gamlib import glglobals as GM
from gamlib import glindent
from gamlib import glmsgs as Msg
from gam.util.api import (
    _getAdminEmail,
    buildGAPIServiceObject,
    callGAPI,
    callGAPIpages,
    checkGAPIError,
    waitOnFailure,
)
from gam.util.args import (
    OrderBy,
    checkArgumentPresent,
    checkForExtraneousArguments,
    formatLocalTime,
    getACLRoles,
    getArgument,
    getBoolean,
    getCharacter,
    getChoice,
    getEmailAddress,
    getHTTPError,
    getJSON,
    getPermissionId,
    getString,
    getTimeOrDeltaFromNow,
)
from gam.util.csv_pf import (
    CSVPrintFile,
    FormatJSONQuoteChar,
    _getFieldsList,
    batchRequestID,
    cleanJSON,
    flattenJSON,
    getItemFieldsFromFieldsList,
)
from gam.util.display import (
    entityActionFailedWarning,
    entityActionNotPerformedWarning,
    entityActionPerformed,
    entityActionPerformedMessage,
    entityDoesNotHaveItemWarning,
    entityPerformActionNumItems,
    entityPerformActionSubItemModifierNumItems,
    invalidQuery,
    printEntityKVList,
    printGettingAllEntityItemsForWhom,
    printKeyValueList,
    printKeyValueListWithCount,
    printLine,
    userDriveServiceNotEnabledWarning,
)
from gam.util.entity import getEntityArgument, getEntityList
from gam.util.errors import (
    deprecatedArgument,
    invalidChoiceExit,
    missingArgumentExit,
    unknownArgumentExit,
    usageErrorExit,
)
from gam.util.fileio import UNKNOWN
from gam.util.output import executeBatch

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

def printEmptyDriveFolders(users):
  def _checkChildDriveFolderContents(drive, fileEntry, user, i, count, pathList):
    query = _getMain().WITH_PARENTS.format(fileEntry ['id'])
    try:
      children = callGAPIpages(drive.files(), 'list', 'files',
                               throwReasons=GAPI.DRIVE_USER_THROW_REASONS+[GAPI.INVALID_QUERY, GAPI.INVALID,
                                                                           GAPI.BAD_REQUEST],
                               retryReasons=[GAPI.UNKNOWN_ERROR],
                               q=query, fields='nextPageToken,files(id,name,mimeType,ownedByMe)',
                               pageSize=GC.Values[GC.DRIVE_MAX_RESULTS], **fileIdEntity['shareddrive'])
      if not children:
        if sharedDriveId or fileEntry.get('ownedByMe', False):
          row = {'User': user, 'id': fileEntry['id'], 'name': pathDelimiter.join(pathList)}
          if sharedDriveId:
            row['driveId'] = sharedDriveId
          csvPF.WriteRow(row)
        return
      for childEntryInfo in children:
        if childEntryInfo['mimeType'] == MIMETYPE_GA_FOLDER:
          _checkChildDriveFolderContents(drive, childEntryInfo, user, i, count, pathList+[childEntryInfo['name']])
    except (GAPI.invalidQuery, GAPI.invalid, GAPI.badRequest):
      entityActionFailedWarning([Ent.USER, user, Ent.DRIVE_FILE, None], invalidQuery(query), i, count)
    except (GAPI.serviceNotAvailable, GAPI.authError, GAPI.domainPolicy) as e:
      userDriveServiceNotEnabledWarning(user, str(e), i, count)

  csvPF = CSVPrintFile(['User', 'id', 'name']) if Act.csvFormat() else None
  fileIdEntity = {}
  pathDelimiter = '/'
  while Cmd.ArgumentsRemaining():
    myarg = getArgument()
    if csvPF and myarg == 'todrive':
      csvPF.GetTodriveParameters()
    elif myarg == 'select':
      DLP = DriveListParameters({'allowChoose': False, 'allowCorpora': False, 'allowQuery': False, 'mimeTypeInQuery': True})
      fileIdEntity = getDriveFileEntity(DLP=DLP)
    elif myarg == 'pathdelimiter':
      pathDelimiter = getCharacter()
    else:
      unknownArgumentExit()
  if not fileIdEntity:
    fileIdEntity = initDriveFileEntity()
    cleanFileIDsList(fileIdEntity, [ROOT])
  i, count, users = getEntityArgument(users)
  for user in users:
    i += 1
    user, drive = _validateUserSharedDrive(user, i, count, fileIdEntity)
    if not drive:
      continue
    fileId = sharedDriveId = fileIdEntity.get('shareddrive', {}).get('driveId', '')
    if not sharedDriveId:
      fileId = fileIdEntity['list'][0]
    try:
      printGettingAllEntityItemsForWhom(Ent.DRIVE_FOLDER, user, i, count)
      fileEntryInfo = callGAPI(drive.files(), 'get',
                               throwReasons=GAPI.DRIVE_USER_THROW_REASONS+[GAPI.FILE_NOT_FOUND, GAPI.NOT_FOUND, GAPI.TEAMDRIVE_MEMBERSHIP_REQUIRED],
                               retryReasons=[GAPI.UNKNOWN_ERROR],
                               fileId=fileId, fields='id,name,mimeType,ownedByMe,driveId', supportsAllDrives=True)
      if 'driveId' in fileEntryInfo:
        sharedDriveId = fileEntryInfo['driveId']
        fileIdEntity['shareddrive'] = {'driveId': sharedDriveId, 'corpora': 'drive', 'includeItemsFromAllDrives': True, 'supportsAllDrives': True}
        csvPF.AddTitles(['driveId'])
        csvPF.MoveTitlesToEnd(['name'])
        pathList = [f'{SHARED_DRIVES}/{_getSharedDriveNameFromId(drive, sharedDriveId)}']
      else:
        pathList = [fileEntryInfo['name']]
      mimeType = fileEntryInfo['mimeType']
      if mimeType != MIMETYPE_GA_FOLDER:
        entityValueList = [Ent.USER, user, _getMain()._getEntityMimeType(fileEntryInfo), fileEntryInfo['name']]
        entityActionNotPerformedWarning(entityValueList, Msg.INVALID_MIMETYPE.format(mimeType, MIMETYPE_GA_FOLDER), i, count)
        continue
      _checkChildDriveFolderContents(drive, fileEntryInfo, user, i, count, pathList)
    except (GAPI.fileNotFound, GAPI.notFound) as e:
      entityActionFailedWarning([Ent.USER, user, Ent.DRIVE_FOLDER, fileId], str(e), i, count)
    except GAPI.teamDriveMembershipRequired as e:
      entityActionFailedWarning([Ent.USER, user, Ent.SHAREDDRIVE_ID, fileId], str(e), i, count)
    except (GAPI.serviceNotAvailable, GAPI.authError, GAPI.domainPolicy) as e:
      userDriveServiceNotEnabledWarning(user, str(e), i, count)
  if csvPF:
    csvPF.writeCSVfile('Empty Folders')

# gam <UserTypeEntity> delete emptydrivefolders
#	[select <DriveFileEntity>]
#	[<SharedDriveEntity>]
#	[pathdelimiter <Character>]
def deleteEmptyDriveFolders(users):
  def _deleteEmptyChildDriveFolders(drive, fileEntry, user, i, count, pathList, atTop):
    query = _getMain().WITH_PARENTS.format(fileEntry ['id'])
    try:
      children = callGAPIpages(drive.files(), 'list', 'files',
                               throwReasons=GAPI.DRIVE_USER_THROW_REASONS+[GAPI.INVALID_QUERY, GAPI.INVALID,
                                                                           GAPI.BAD_REQUEST],
                               retryReasons=[GAPI.UNKNOWN_ERROR],
                               q=query, fields='nextPageToken,files(id,name,mimeType,ownedByMe)',
                               pageSize=GC.Values[GC.DRIVE_MAX_RESULTS], **fileIdEntity['shareddrive'])
      numChildren = len(children)
      for childEntryInfo in children:
        if childEntryInfo['mimeType'] == MIMETYPE_GA_FOLDER:
          numChildren -= _deleteEmptyChildDriveFolders(drive, childEntryInfo, user, i, count, pathList+[childEntryInfo['name']], False)
      if numChildren == 0 and not atTop:
        try:
          callGAPI(drive.files(), 'delete',
                   throwReasons=GAPI.DRIVE_ACCESS_THROW_REASONS,
                   fileId=fileEntry['id'], supportsAllDrives=True)
          entityActionPerformed([Ent.USER, user, Ent.DRIVE_FOLDER_ID, fileEntry['id'],
                                 Ent.DRIVE_FOLDER, pathDelimiter.join(pathList)], i, count)
          return 1
        except (GAPI.fileNotFound, GAPI.forbidden, GAPI.internalError, GAPI.insufficientFilePermissions, GAPI.unknownError) as e:
          entityActionFailedWarning([Ent.USER, user, Ent.DRIVE_FOLDER, fileEntry['name']], str(e), i, count)
    except (GAPI.invalidQuery, GAPI.invalid, GAPI.badRequest):
      entityActionFailedWarning([Ent.USER, user, Ent.DRIVE_FILE, None], invalidQuery(query), i, count)
    except (GAPI.serviceNotAvailable, GAPI.authError, GAPI.domainPolicy) as e:
      userDriveServiceNotEnabledWarning(user, str(e), i, count)
    return 0

  Act.Set(Act.DELETE_EMPTY)
  fileIdEntity = {}
  pathDelimiter = '/'
  while Cmd.ArgumentsRemaining():
    myarg = getArgument()
    if myarg == 'select':
      DLP = DriveListParameters({'allowChoose': False, 'allowCorpora': False, 'allowQuery': False, 'mimeTypeInQuery': True})
      fileIdEntity = getDriveFileEntity(DLP=DLP)
    elif myarg == 'pathdelimiter':
      pathDelimiter = getCharacter()
    else:
      fileIdEntity = getSharedDriveEntity()
  if not fileIdEntity:
    fileIdEntity = initDriveFileEntity()
    cleanFileIDsList(fileIdEntity, [ROOT])
  checkForExtraneousArguments()
  i, count, users = getEntityArgument(users)
  for user in users:
    i += 1
    user, drive = _validateUserSharedDrive(user, i, count, fileIdEntity)
    if not drive:
      continue
    printEntityKVList([Ent.USER, user],
                      [f'{Act.ToPerform()} {Ent.Plural(Ent.DRIVE_FILE_OR_FOLDER)}'],
                      i, count)
    Ind.Increment()
    fileId = sharedDriveId = fileIdEntity.get('shareddrive', {}).get('driveId', '')
    if not sharedDriveId:
      fileId = fileIdEntity['list'][0]
    try:
      printGettingAllEntityItemsForWhom(Ent.DRIVE_FOLDER, user, i, count)
      fileEntryInfo = callGAPI(drive.files(), 'get',
                               throwReasons=GAPI.DRIVE_USER_THROW_REASONS+[GAPI.FILE_NOT_FOUND, GAPI.NOT_FOUND, GAPI.TEAMDRIVE_MEMBERSHIP_REQUIRED],
                               retryReasons=[GAPI.UNKNOWN_ERROR],
                               fileId=fileId, fields='id,name,mimeType,ownedByMe,driveId', supportsAllDrives=True)
      if 'driveId' in fileEntryInfo:
        sharedDriveId = fileEntryInfo['driveId']
        fileIdEntity['shareddrive'] = {'driveId': sharedDriveId, 'corpora': 'drive', 'includeItemsFromAllDrives': True, 'supportsAllDrives': True}
        pathList = [f'{SHARED_DRIVES}/{_getSharedDriveNameFromId(drive, sharedDriveId)}']
      else:
        pathList = [fileEntryInfo['name']]
      mimeType = fileEntryInfo['mimeType']
      if mimeType != MIMETYPE_GA_FOLDER:
        entityValueList = [Ent.USER, user, _getMain()._getEntityMimeType(fileEntryInfo), fileEntryInfo['name']]
        entityActionNotPerformedWarning(entityValueList, Msg.INVALID_MIMETYPE.format(mimeType, MIMETYPE_GA_FOLDER), i, count)
        continue
      _deleteEmptyChildDriveFolders(drive, fileEntryInfo, user, i, count, pathList, True)
    except (GAPI.fileNotFound, GAPI.notFound) as e:
      entityActionFailedWarning([Ent.USER, user, Ent.DRIVE_FOLDER, fileId], str(e), i, count)
    except GAPI.teamDriveMembershipRequired as e:
      entityActionFailedWarning([Ent.USER, user, Ent.SHAREDDRIVE_ID, fileId], str(e), i, count)
    except (GAPI.serviceNotAvailable, GAPI.authError, GAPI.domainPolicy) as e:
      userDriveServiceNotEnabledWarning(user, str(e), i, count)
    Ind.Decrement()

# gam <UserTypeEntity> empty drivetrash [<SharedDriveEntity>]
def emptyDriveTrash(users):
  if Cmd.ArgumentsRemaining():
    fileIdEntity = getSharedDriveEntity()
  else:
    fileIdEntity = {}
  checkForExtraneousArguments()
  kwargs = {'driveId': None}
  i, count, users = getEntityArgument(users)
  for user in users:
    i += 1
    if not fileIdEntity:
      user, drive = buildGAPIServiceObject(API.DRIVE3, user, i, count)
      if not drive:
        continue
    else:
      user, drive = _validateUserSharedDrive(user, i, count, fileIdEntity)
      if not drive:
        continue
      kwargs['driveId'] = fileIdEntity['shareddrive']['driveId']
    try:
      callGAPI(drive.files(), 'emptyTrash',
               throwReasons=GAPI.DRIVE_USER_THROW_REASONS+[GAPI.NOT_FOUND, GAPI.INSUFFICIENT_FILE_PERMISSIONS],
               **kwargs)
      entityActionPerformed([Ent.USER, user, Ent.DRIVE_TRASH, kwargs['driveId']], i, count)
    except (GAPI.notFound, GAPI.insufficientFilePermissions) as e:
      entityActionFailedWarning([Ent.USER, user, Ent.SHAREDDRIVE_ID, kwargs['driveId']], str(e), i, count)
    except (GAPI.serviceNotAvailable, GAPI.authError, GAPI.domainPolicy) as e:
      userDriveServiceNotEnabledWarning(user, str(e), i, count)

def _getDriveFileACLPrintKeysTimeObjects():
  printKeys = ['id', 'role', 'type', 'emailAddress', 'domain', 'permissionDetails',
               'expirationTime', 'photoLink', 'allowFileDiscovery', 'deleted',
               'pendingOwner', 'view']
  timeObjects = {'expirationTime'}
  return (printKeys, timeObjects)

# DriveFileACL commands utilities
def _showDriveFilePermissionJSON(user, fileId, fileName, createdTime, permission, timeObjects):
  _mapDrivePermissionNames(permission)
  row = {'Owner': user, 'id': fileId, 'permission': permission}
  if createdTime is not None:
    row['createdTime'] = createdTime
  if fileId != fileName:
    row['name'] = fileName
  printLine(json.dumps(cleanJSON(row, timeObjects=timeObjects), ensure_ascii=False, sort_keys=True))

def _showDriveFilePermissionsJSON(user, fileId, fileName, createdTime, permissions, timeObjects):
  for permission in permissions:
    _mapDrivePermissionNames(permission)
  row = {'Owner': user, 'id': fileId, 'permissions': permissions}
  if createdTime is not None:
    row['createdTime'] = createdTime
  if fileId != fileName:
    row['name'] = fileName
  printLine(json.dumps(cleanJSON(row, timeObjects=timeObjects), ensure_ascii=False, sort_keys=True))

def _showDriveFilePermission(permission, printKeys, timeObjects, i=0, count=0):
  if permission.get('displayName'):
    name = permission['displayName']
  elif 'id' in permission:
    if permission['id'] == 'anyone':
      name = 'Anyone'
    elif permission['id'] == 'anyoneWithLink':
      name = 'Anyone with Link'
    else:
      name = permission['id']
  else:
    name = 'Permission'
  _mapDrivePermissionNames(permission)
  printKeyValueListWithCount([name], i, count)
  Ind.Increment()
  for key in printKeys:
    value = permission.get(key)
    if value is None:
      continue
    if key == 'permissionDetails':
      printKeyValueList([key, ''])
      Ind.Increment()
      for detail in value:
        printKeyValueList(['inherited', detail['inherited']])
        Ind.Increment()
        if detail['inherited']:
          printKeyValueList(['inheritedFrom', detail.get('inheritedFrom', UNKNOWN)])
        printKeyValueList(['permissionType', detail['permissionType']])
        printKeyValueList(['role', detail['role']])
        if 'additionalRoles' in detail:
          printKeyValueList(['additionalRoles', ','.join(detail['additionalRoles'])])
        Ind.Decrement()
      Ind.Decrement()
    elif key not in timeObjects:
      printKeyValueList([key, value])
    else:
      printKeyValueList([key, formatLocalTime(value)])
  Ind.Decrement()

def _showDriveFilePermissions(entityType, fileName, permissions, printKeys, timeObjects, j, jcount):
  kcount = len(permissions)
  entityPerformActionNumItems([entityType, fileName], kcount, Ent.PERMITTEE, j, jcount)
  Ind.Increment()
  k = 0
  for permission in permissions:
    k += 1
    _showDriveFilePermission(permission, printKeys, timeObjects, k, kcount)
  Ind.Decrement()

def _checkFileIdEntityDomainAccess(fileIdEntity, useDomainAdminAccess):
  if useDomainAdminAccess and fileIdEntity['nonDomainAdminAccess']:
    Cmd.SetLocation(fileIdEntity['location'])
    usageErrorExit(Msg.INVALID_FILE_SELECTION_WITH_ADMIN_ACCESS)

# gam [<UserTypeEntity>] create drivefileacl <DriveFileEntity> [asadmin]
#	anyone|(user <UserItem>)|(group <GroupItem>)|(domain <DomainName>)  (role <DriveFileACLRole>)]
#	[withlink|(allowfilediscovery|discoverable [<Boolean>])] [expiration <Time>]
#	(mappermissionsdomain <DomainName> <DomainName>)*
#	[moveToNewOwnersRoot [<Boolean>]]
#	[updatesheetprotectedranges  [<Boolean>]]
#	[sendemail|sendnotification] [emailmessage <String>]
#	[showtitles] [nodetails|(csv [todrive <ToDriveAttribute>*] [formatjson [quotechar <Character>]])]
def createDriveFileACL(users, useDomainAdminAccess=False):
  def _showResult(permission, showAction):
    if updateSheetProtectedRanges and mimeType == MIMETYPE_GA_SPREADSHEET:
      _updateSheetProtectedRangesACLchange(sheet, user, i, count, j, jcount, fileId, fileName, True, permission)
    if csvPF:
      baserow = {'Owner': user, 'id': fileId}
      if showTitles:
        baserow['name'] = fileName
      row = baserow.copy()
      _mapDrivePermissionNames(permission)
      flattenJSON({'permission': permission}, flattened=row, timeObjects=timeObjects)
      if not FJQC.formatJSON:
        csvPF.WriteRowTitles(row)
      elif csvPF.CheckRowTitles(row):
        row = baserow.copy()
        row['JSON'] = json.dumps(cleanJSON({'permission': permission}, timeObjects=timeObjects),
                                 ensure_ascii=False, sort_keys=True)
        csvPF.WriteRowNoFilter(row)
    else:
      if showAction:
        entityActionPerformed([Ent.USER, user, entityType, fileName, Ent.PERMISSION_ID, permissionId], j, jcount)
      if showDetails:
        _showDriveFilePermission(permission, printKeys, timeObjects)

  moveToNewOwnersRoot = False
  sendNotificationEmail = showTitles = _transferOwnership = updateSheetProtectedRanges = False
  roleLocation = withLinkLocation = expirationLocation = None
  emailMessage = None
  showDetails = True
  csvPF = None
  FJQC = FormatJSONQuoteChar(csvPF)
  fileIdEntity = getDriveFileEntity()
  body = {}
  body['type'] = permType = getChoice(DRIVEFILE_ACL_PERMISSION_TYPES)
  if permType != 'anyone':
    if permType != 'domain':
      body['emailAddress'] = permissionId = getEmailAddress()
    else:
      body['domain'] = permissionId = getString(Cmd.OB_DOMAIN_NAME)
  else:
    permissionId = 'anyone'
  mapPermissionsDomains = {}
  while Cmd.ArgumentsRemaining():
    myarg = getArgument()
    if myarg == 'withlink':
      withLinkLocation = Cmd.Location()
      body['allowFileDiscovery'] = False
    elif myarg in {'allowfilediscovery', 'discoverable'}:
      withLinkLocation = Cmd.Location()
      body['allowFileDiscovery'] = getBoolean()
    elif myarg == 'role':
      roleLocation = Cmd.Location()
      body['role'] = getChoice(DRIVEFILE_ACL_ROLES_MAP, mapChoice=True)
      if body['role'] == 'owner':
        sendNotificationEmail = _transferOwnership = True
    elif myarg == 'mappermissionsdomain':
      oldDomain = getString(Cmd.OB_DOMAIN_NAME).lower()
      mapPermissionsDomains[oldDomain] = getString(Cmd.OB_DOMAIN_NAME).lower()
    elif myarg == 'enforcesingleparent':
      deprecatedArgument(myarg)
    elif myarg == 'movetonewownersroot':
      moveToNewOwnersRoot = getBoolean()
    elif myarg in {'expiration', 'expires'}:
      expirationLocation = Cmd.Location()
      body['expirationTime'] = getTimeOrDeltaFromNow()
    elif myarg in {'sendemail', 'sendnotification'}:
      sendNotificationEmail = True
    elif myarg == 'emailmessage':
      sendNotificationEmail = True
      emailMessage = getString(Cmd.OB_STRING)
    elif myarg == 'showtitles':
      showTitles = True
    elif myarg == 'updatesheetprotectedranges':
      updateSheetProtectedRanges = getBoolean()
    elif myarg == 'nodetails':
      showDetails = False
    elif myarg == 'csv':
      csvPF = CSVPrintFile(['Owner', 'id'], 'sortall')
      FJQC.SetCsvPF(csvPF)
    elif csvPF and myarg == 'todrive':
      csvPF.GetTodriveParameters()
    elif myarg in _getMain().ADMIN_ACCESS_OPTIONS:
      useDomainAdminAccess = True
    else:
      FJQC.GetFormatJSONQuoteChar(myarg)
  _checkFileIdEntityDomainAccess(fileIdEntity, useDomainAdminAccess)
  if 'role' not in body:
    missingArgumentExit(f'role {formatChoiceList(DRIVEFILE_ACL_ROLES_MAP)}')
  if mapPermissionsDomains:
    if permType != 'anyone':
      if permType != 'domain':
        atLoc = permissionId.find('@')
        if atLoc != -1:
          mappedDomain = mapPermissionsDomains.get(permissionId[atLoc+1:], None)
          if mappedDomain:
            body['emailAddress'] = permissionId = f"{permissionId[:atLoc]}@{mappedDomain}"
      else:
        mappedDomain = mapPermissionsDomains.get(permissionId, None)
        if mappedDomain:
          body['domain'] = permissionId = mappedDomain
  _validateACLOwnerType(roleLocation, body)
  _validateACLAttributes('allowfilediscovery/withlink', withLinkLocation, body, 'allowFileDiscovery', ['anyone', 'domain'])
  _validateACLAttributes('expiration', expirationLocation, body, 'expirationTime', ['user', 'group'])
  printKeys, timeObjects = _getDriveFileACLPrintKeysTimeObjects()
  if csvPF:
    if showTitles:
      csvPF.AddTitles('name')
      csvPF.SetSortAllTitles()
    if FJQC.formatJSON:
      csvPF.SetJSONTitles(csvPF.titlesList+['JSON'])
  i, count, users = getEntityArgument(users)
  for user in users:
    i += 1
    user, drive, jcount = _validateUserGetFileIDs(user, i, count, fileIdEntity,
                                                  entityType=Ent.DRIVE_FILE_OR_FOLDER_ACL if not csvPF else None,
                                                  useDomainAdminAccess=useDomainAdminAccess)
    if jcount == 0:
      continue
    sheet = None
    Ind.Increment()
    j = 0
    for fileId in fileIdEntity['list']:
      j += 1
      try:
        fileName = fileId
        entityType = Ent.DRIVE_FILE_OR_FOLDER_ID
        if showTitles or updateSheetProtectedRanges:
          fileName, entityType, mimeType = _getDriveFileNameFromId(drive, fileId, combineTitleId=not csvPF)
          if updateSheetProtectedRanges and mimeType == MIMETYPE_GA_SPREADSHEET:
            if not sheet:
              _, sheet = buildGAPIServiceObject(API.SHEETS, user, i, count)
              if not sheet:
                break
        try:
          permission = callGAPI(drive.permissions(), 'create',
                                bailOnInternalError=True,
                                throwReasons=GAPI.DRIVE_ACCESS_THROW_REASONS+GAPI.DRIVE3_CREATE_ACL_THROW_REASONS+[GAPI.FILE_NEVER_WRITABLE],
                                moveToNewOwnersRoot=moveToNewOwnersRoot,
                                useDomainAdminAccess=useDomainAdminAccess,
                                fileId=fileId, sendNotificationEmail=sendNotificationEmail, emailMessage=emailMessage,
                                transferOwnership=_transferOwnership, body=body, fields='*', supportsAllDrives=True)
          _showResult(permission, True)
        except GAPI.invalidSharingRequest  as e:
          errMsg = str(e)
          if ('successfully shared but emails could not be sent' not in errMsg) or ('emailAddress' not in body):
            entityActionFailedWarning([Ent.USER, user, entityType, fileName, Ent.PERMISSION_ID, permissionId], errMsg, j, jcount)
          else:
            if not csvPF:
              entityActionPerformedMessage([Ent.USER, user, entityType, fileName, Ent.PERMISSION_ID, permissionId], errMsg, j, jcount)
            tempPermId = getPermissionIdForEmail(user, i, count, body['emailAddress'])
            permission = callGAPI(drive.permissions(), 'get',
                                  throwReasons=GAPI.DRIVE_ACCESS_THROW_REASONS+[GAPI.BAD_REQUEST, GAPI.PERMISSION_NOT_FOUND, GAPI.INSUFFICIENT_ADMINISTRATOR_PRIVILEGES],
                                  useDomainAdminAccess=useDomainAdminAccess,
                                  fileId=fileId, permissionId=tempPermId, fields='*', supportsAllDrives=True)
            _showResult(permission, False)
      except (GAPI.badRequest, GAPI.invalid, GAPI.fileNotFound, GAPI.forbidden, GAPI.internalError,
              GAPI.permissionNotFound, GAPI.cannotSetExpiration, GAPI.cannotSetExpirationOnAnyoneOrDomain,
              GAPI.expirationDateNotAllowedForSharedDriveMembers, GAPI.expirationDatesMustBeInTheFuture,
              GAPI.insufficientFilePermissions, GAPI.unknownError, GAPI.ownershipChangeAcrossDomainNotPermitted,
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
              GAPI.fileNeverWritable, GAPI.abusiveContentRestriction) as e:
        entityActionFailedWarning([Ent.USER, user, entityType, fileName, Ent.PERMISSION_ID, permissionId], str(e), j, jcount)
      except GAPI.notFound as e:
        entityActionFailedWarning([Ent.USER, user, Ent.SHAREDDRIVE, fileName], str(e), j, jcount)
      except (GAPI.serviceNotAvailable, GAPI.authError, GAPI.domainPolicy) as e:
        userDriveServiceNotEnabledWarning(user, str(e), i, count)
        break
    Ind.Decrement()
  if csvPF:
    csvPF.writeCSVfile('Drive File ACLs')

def doCreateDriveFileACL():
  createDriveFileACL([_getAdminEmail()], True)

# gam [<UserTypeEntity>] update drivefileacl <DriveFileEntity> <DriveFilePermissionIDorEmail> [asadmin]
#	(role <DriveFileACLRole>) [expiration <Time>] [removeexpiration [<Boolean>]]
#	[updatesheetprotectedranges [<Boolean>]]
#	[showtitles] [nodetails|(csv [todrive <ToDriveAttribute>*] [formatjson [quotechar <Character>]])]
def updateDriveFileACLs(users, useDomainAdminAccess=False):
  def _showResult(permission, showAction):
    if updateSheetProtectedRanges and mimeType == MIMETYPE_GA_SPREADSHEET:
      _updateSheetProtectedRangesACLchange(sheet, user, i, count, j, jcount, fileId, fileName, True, permission)
    if csvPF:
      baserow = {'Owner': user, 'id': fileId}
      if showTitles:
        baserow['name'] = fileName
      row = baserow.copy()
      _mapDrivePermissionNames(permission)
      flattenJSON({'permission': permission}, flattened=row, timeObjects=timeObjects)
      if not FJQC.formatJSON:
        csvPF.WriteRowTitles(row)
      elif csvPF.CheckRowTitles(row):
        row = baserow.copy()
        row['JSON'] = json.dumps(cleanJSON({'permission': permission}, timeObjects=timeObjects),
                                 ensure_ascii=False, sort_keys=True)
        csvPF.WriteRowNoFilter(row)
    else:
      if showAction:
        entityActionPerformed([Ent.USER, user, entityType, fileName, Ent.PERMISSION_ID, permissionId], j, jcount)
      if showDetails:
        _showDriveFilePermission(permission, printKeys, timeObjects)

  fileIdEntity = getDriveFileEntity()
  isEmail, permissionId = getPermissionId()
  removeExpiration = showTitles = updateSheetProtectedRanges = False
  showDetails = True
  csvPF = None
  FJQC = FormatJSONQuoteChar(csvPF)
  body = {}
  while Cmd.ArgumentsRemaining():
    myarg = getArgument()
    if myarg == 'role':
      body['role'] = getChoice(DRIVEFILE_ACL_ROLES_MAP, mapChoice=True)
    elif myarg in {'expiration', 'expires'}:
      body['expirationTime'] = getTimeOrDeltaFromNow()
    elif myarg == 'removeexpiration':
      removeExpiration = getBoolean()
    elif myarg == 'showtitles':
      showTitles = True
    elif myarg == 'updatesheetprotectedranges':
      updateSheetProtectedRanges = getBoolean()
    elif myarg == 'nodetails':
      showDetails = False
    elif myarg == 'csv':
      csvPF = CSVPrintFile(['Owner', 'id'], 'sortall')
      FJQC.SetCsvPF(csvPF)
    elif csvPF and myarg == 'todrive':
      csvPF.GetTodriveParameters()
    elif myarg == 'transferownership':
      deprecatedArgument(myarg)
      getBoolean()
    elif myarg in _getMain().ADMIN_ACCESS_OPTIONS:
      useDomainAdminAccess = True
    else:
      FJQC.GetFormatJSONQuoteChar(myarg)
  _checkFileIdEntityDomainAccess(fileIdEntity, useDomainAdminAccess)
  if 'role' not in body:
    missingArgumentExit(f'role {formatChoiceList(DRIVEFILE_ACL_ROLES_MAP)}')
  printKeys, timeObjects = _getDriveFileACLPrintKeysTimeObjects()
  if csvPF and showTitles:
    csvPF.AddTitles('name')
    csvPF.SetSortAllTitles()
    if FJQC.formatJSON:
      csvPF.SetJSONTitles(csvPF.titlesList+['JSON'])
  i, count, users = getEntityArgument(users)
  for user in users:
    i += 1
    user, drive, jcount = _validateUserGetFileIDs(user, i, count, fileIdEntity,
                                                  entityType=Ent.DRIVE_FILE_OR_FOLDER_ACL if not csvPF else None,
                                                  useDomainAdminAccess=useDomainAdminAccess)
    if jcount == 0:
      continue
    if isEmail:
      permissionId = getPermissionIdForEmail(user, i, count, permissionId)
      if not permissionId:
        return
      isEmail = False
    sheet = None
    Ind.Increment()
    j = 0
    for fileId in fileIdEntity['list']:
      j += 1
      try:
        fileName = fileId
        entityType = Ent.DRIVE_FILE_OR_FOLDER_ID
        if showTitles or updateSheetProtectedRanges:
          fileName, entityType, mimeType = _getDriveFileNameFromId(drive, fileId, combineTitleId=not csvPF)
          if updateSheetProtectedRanges and mimeType == MIMETYPE_GA_SPREADSHEET:
            if not sheet:
              _, sheet = buildGAPIServiceObject(API.SHEETS, user, i, count)
              if not sheet:
                break
        permission = callGAPI(drive.permissions(), 'update',
                              bailOnInternalError=True,
                              throwReasons=GAPI.DRIVE_ACCESS_THROW_REASONS+GAPI.DRIVE3_UPDATE_ACL_THROW_REASONS+[GAPI.FILE_NEVER_WRITABLE],
                              useDomainAdminAccess=useDomainAdminAccess,
                              fileId=fileId, permissionId=permissionId, removeExpiration=removeExpiration,
                              transferOwnership=body.get('role', '') == 'owner', body=body, fields='*', supportsAllDrives=True)
        _showResult(permission, True)
      except (GAPI.fileNotFound, GAPI.forbidden, GAPI.internalError, GAPI.insufficientFilePermissions, GAPI.unknownError,
              GAPI.cannotSetExpiration, GAPI.cannotSetExpirationOnAnyoneOrDomain,
              GAPI.expirationDateNotAllowedForSharedDriveMembers, GAPI.expirationDatesMustBeInTheFuture,
              GAPI.badRequest, GAPI.invalidOwnershipTransfer, GAPI.cannotRemoveOwner,
              GAPI.fileNeverWritable, GAPI.ownershipChangeAcrossDomainNotPermitted, GAPI.sharingRateLimitExceeded,
              GAPI.targetUserRoleLimitedByLicenseRestriction, GAPI.insufficientAdministratorPrivileges,
              GAPI.publishOutNotPermitted, GAPI.shareInNotPermitted, GAPI.shareOutNotPermitted, GAPI.shareOutNotPermittedToUser,
              GAPI.organizerOnNonTeamDriveItemNotSupported, GAPI.fileOrganizerOnNonTeamDriveNotSupported,
              GAPI.cannotUpdatePermission, GAPI.cannotModifyInheritedTeamDrivePermission, GAPI.cannotModifyInheritedPermission,
              GAPI.fieldNotWritable) as e:
        entityActionFailedWarning([Ent.USER, user, entityType, fileName], str(e), j, jcount)
      except (GAPI.notFound, GAPI.teamDriveDomainUsersOnlyRestriction, GAPI.teamDriveTeamMembersOnlyRestriction,
              GAPI.cannotShareTeamDriveTopFolderWithAnyoneOrDomains, GAPI.ownerOnTeamDriveItemNotSupported,
              GAPI.fileOrganizerNotYetEnabledForThisTeamDrive, GAPI.fileOrganizerOnFoldersInSharedDriveOnly) as e:
        entityActionFailedWarning([Ent.USER, user, Ent.SHAREDDRIVE, fileName], str(e), j, jcount)
      except GAPI.permissionNotFound:
        entityDoesNotHaveItemWarning([Ent.USER, user, entityType, fileName, Ent.PERMISSION_ID, permissionId], j, jcount)
      except (GAPI.serviceNotAvailable, GAPI.authError, GAPI.domainPolicy) as e:
        userDriveServiceNotEnabledWarning(user, str(e), i, count)
        break
    Ind.Decrement()
  if csvPF:
    csvPF.writeCSVfile('Drive File ACLs')

def doUpdateDriveFileACLs():
  updateDriveFileACLs([_getAdminEmail()], True)

# gam [<UserTypeEntity>] create permissions <DriveFileEntity> <DriveFilePermissionsEntity> [asadmin]
#	[expiration <Time>] [sendemail|sendnotification] [emailmessage <String>]
#	[moveToNewOwnersRoot [<Boolean>]]
#	<PermissionMatch>* [<PermissionMatchAction>]
def createDriveFilePermissions(users, useDomainAdminAccess=False):
  def convertJSONPermissions(jsonPermissions):
    permissions = []
    for permission in PM.GetMatchingPermissions(jsonPermissions):
      if permission.get('deleted', False):
        continue
      if permission['type'] in {'anyone', 'domain'}:
        permItem = permission['type'] if permission['allowFileDiscovery'] else permission['type']+'withlink'
        if permission['type'] == 'domain':
          permItem += ':'+permission['domain']
      else:
        permItem = permission['type']+':'+permission['emailAddress']
      permissions.append(permItem+';'+permission['role'].lower())
    return permissions

  def _makePermissionBody(permission):
    body = {}
    try:
      scope, role = permission.split(';', 1)
      scope = scope.lower()
      role = role.lower()
      if scope in {'anyone', 'anyonewithlink'}:
        body['type'] = 'anyone'
        body['allowFileDiscovery'] = scope != 'anyonewithlink'
      else:
        body['type'], value = scope.split(':', 1)
        if body['type'] == 'domainwithlink':
          body['allowFileDiscovery'] = False
          body['type'] = 'domain'
        if body['type'] not in DRIVEFILE_ACL_PERMISSION_TYPES[1:]:
          return None
        if body['type'] != 'domain':
          body['emailAddress'] = value
        else:
          body['domain'] = value
      body['role'] = DRIVEFILE_ACL_ROLES_MAP.get(role)
      if not body['role']:
        return None
      if expiration:
        body['expirationTime'] = expiration
      return body
    except ValueError:
      return None

  def _callbackCreatePermission(request_id, _, exception):
    ri = request_id.splitlines()
    if int(ri[RI_J]) == 1:
      entityPerformActionNumItems([Ent.DRIVE_FILE_OR_FOLDER_ID, ri[RI_ENTITY]], int(ri[RI_JCOUNT]), Ent.PERMITTEE, int(ri[RI_I]), int(ri[RI_COUNT]))
      Ind.Increment()
    if exception is None:
      entityActionPerformed([Ent.DRIVE_FILE_OR_FOLDER_ID, ri[RI_ENTITY], Ent.PERMITTEE, ri[RI_ITEM]], int(ri[RI_J]), int(ri[RI_JCOUNT]))
    else:
      http_status, reason, message = checkGAPIError(exception)
      if reason not in GAPI.DEFAULT_RETRY_REASONS+[GAPI.SERVICE_LIMIT]:
        if reason in GAPI.DRIVE_ACCESS_THROW_REASONS+GAPI.DRIVE3_CREATE_ACL_THROW_REASONS:
          entityActionFailedWarning([Ent.DRIVE_FILE_OR_FOLDER_ID, ri[RI_ENTITY], Ent.PERMITTEE, ri[RI_ITEM]], message, int(ri[RI_J]), int(ri[RI_JCOUNT]))
        else:
          errMsg = getHTTPError({}, http_status, reason, message)
          entityActionFailedWarning([Ent.DRIVE_FILE_OR_FOLDER_ID, ri[RI_ENTITY], Ent.PERMITTEE, ri[RI_ITEM]], errMsg, int(ri[RI_J]), int(ri[RI_JCOUNT]))
        if int(ri[RI_J]) == int(ri[RI_JCOUNT]):
          Ind.Decrement()
        return
      waitOnFailure(1, 10, reason, message)
      try:
        callGAPI(drive.permissions(), 'create',
                 bailOnInternalError=True,
                 throwReasons=GAPI.DRIVE_ACCESS_THROW_REASONS+GAPI.DRIVE3_CREATE_ACL_THROW_REASONS, retryReasons=[GAPI.SERVICE_LIMIT],
                 useDomainAdminAccess=useDomainAdminAccess,
                 fileId=ri[RI_ENTITY], sendNotificationEmail=sendNotificationEmail, emailMessage=emailMessage,
                 body=_makePermissionBody(ri[RI_ITEM]), fields='', supportsAllDrives=True)
        entityActionPerformed([Ent.DRIVE_FILE_OR_FOLDER_ID, ri[RI_ENTITY], Ent.PERMITTEE, ri[RI_ITEM]], int(ri[RI_J]), int(ri[RI_JCOUNT]))
      except (GAPI.badRequest, GAPI.invalid, GAPI.fileNotFound, GAPI.forbidden, GAPI.internalError,
              GAPI.cannotSetExpiration, GAPI.cannotSetExpirationOnAnyoneOrDomain,
              GAPI.expirationDateNotAllowedForSharedDriveMembers, GAPI.expirationDatesMustBeInTheFuture,
              GAPI.insufficientFilePermissions, GAPI.unknownError, GAPI.ownershipChangeAcrossDomainNotPermitted,
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
              GAPI.invalidSharingRequest, GAPI.fileNeverWritable, GAPI.abusiveContentRestriction,
              GAPI.serviceNotAvailable, GAPI.authError, GAPI.domainPolicy) as e:
        entityActionFailedWarning([Ent.DRIVE_FILE_OR_FOLDER_ID, ri[RI_ENTITY], Ent.PERMITTEE, ri[RI_ITEM]], str(e), int(ri[RI_J]), int(ri[RI_JCOUNT]))
      except GAPI.notFound as e:
        entityActionFailedWarning([Ent.SHAREDDRIVE, ri[RI_ENTITY], Ent.PERMITTEE, ri[RI_ITEM]], str(e), int(ri[RI_J]), int(ri[RI_JCOUNT]))
    if int(ri[RI_J]) == int(ri[RI_JCOUNT]):
      Ind.Decrement()

  moveToNewOwnersRoot = False
  sendNotificationEmail = False
  emailMessage = expiration = None
  fileIdEntity = getDriveFileEntity()
  if not checkArgumentPresent('json'):
    permissions = getEntityList(Cmd.OB_DRIVE_FILE_PERMISSION_ENTITY)
    jsonData = None
    PM = None
  else:
    permissions = []
    jsonData = getJSON([])
    PM = PermissionMatch()
    PM.SetDefaultMatch(False, {'role': 'owner'})
  while Cmd.ArgumentsRemaining():
    myarg = getArgument()
    if myarg == 'enforcesingleparent':
      deprecatedArgument(myarg)
    elif myarg == 'movetonewownersroot':
      moveToNewOwnersRoot = getBoolean()
    elif myarg in {'expiration', 'expires'}:
      expiration = getTimeOrDeltaFromNow()
    elif myarg in {'sendemail', 'sendnotification'}:
      sendNotificationEmail = True
    elif myarg == 'emailmessage':
      sendNotificationEmail = True
      emailMessage = getString(Cmd.OB_STRING)
    elif myarg in _getMain().ADMIN_ACCESS_OPTIONS:
      useDomainAdminAccess = True
    elif PM and PM.ProcessArgument(myarg):
      pass
    else:
      unknownArgumentExit()
  _checkFileIdEntityDomainAccess(fileIdEntity, useDomainAdminAccess)
  if jsonData:
    if 'permission' in jsonData:
      permissions = convertJSONPermissions([jsonData['permission']])
    elif 'permissions' in jsonData:
      permissions = convertJSONPermissions(jsonData['permissions'])
  permissionsLists = permissions if isinstance(permissions, dict) else None
  i, count, users = getEntityArgument(users)
  for user in users:
    i += 1
    origUser = user
    user, drive, jcount = _validateUserGetFileIDs(user, i, count, fileIdEntity, useDomainAdminAccess=useDomainAdminAccess)
    if not drive:
      continue
    entityPerformActionSubItemModifierNumItems([Ent.USER, user], Ent.DRIVE_FILE_OR_FOLDER_ACL, Act.MODIFIER_TO, jcount, Ent.DRIVE_FILE_OR_FOLDER, i, count)
    if jcount == 0:
      continue
    try:
      callGAPI(drive.about(), 'get',
               throwReasons=GAPI.DRIVE_USER_THROW_REASONS,
               fields='kind')
    except (GAPI.serviceNotAvailable, GAPI.authError, GAPI.domainPolicy) as e:
      userDriveServiceNotEnabledWarning(user, str(e), i, count)
      continue
    Ind.Increment()
    svcargs = dict([('fileId', None), ('sendNotificationEmail', sendNotificationEmail), ('emailMessage', emailMessage),
                    ('useDomainAdminAccess', useDomainAdminAccess),
                    ('body', None), ('fields', ''), ('supportsAllDrives', True)]+GM.Globals[GM.EXTRA_ARGS_LIST])
    method = getattr(drive.permissions(), 'create')
    dbatch = drive.new_batch_http_request(callback=_callbackCreatePermission)
    bcount = 0
    j = 0
    for fileId in fileIdEntity['list']:
      j += 1
      if permissionsLists:
        if not GM.Globals[GM.CSV_SUBKEY_FIELD]:
          permissions = permissionsLists[fileId]
        else:
          permissions = permissionsLists[origUser][fileId]
      kcount = len(permissions)
      if kcount == 0:
        continue
      k = 0
      for permission in permissions:
        k += 1
        svcparms = svcargs.copy()
        svcparms['fileId'] = fileId
        svcparms['body'] = _makePermissionBody(permission)
        if not svcparms['body']:
          entityActionFailedWarning([Ent.DRIVE_FILE_OR_FOLDER_ID, fileId, Ent.PERMITTEE, permission], Msg.INVALID, k, kcount)
          continue
        if svcparms['body']['role'] == 'owner':
          svcparms['moveToNewOwnersRoot'] = moveToNewOwnersRoot
          svcparms['transferOwnership'] = svcparms['sendNotificationEmail'] = True
        dbatch.add(method(**svcparms), request_id=batchRequestID(fileId, j, jcount, k, kcount, permission))
        bcount += 1
        if bcount >= GC.Values[GC.BATCH_SIZE]:
          executeBatch(dbatch)
          dbatch = drive.new_batch_http_request(callback=_callbackCreatePermission)
          bcount = 0
    if bcount > 0:
      dbatch.execute()
    Ind.Decrement()

def doCreatePermissions():
  createDriveFilePermissions([_getAdminEmail()], True)

# gam [<UserTypeEntity>] delete drivefileacl <DriveFileEntity> <DriveFilePermissionIDorEmail> [asadmin]
#	[updatesheetprotectedranges  [<Boolean>]]
#	[showtitles]
def deleteDriveFileACLs(users, useDomainAdminAccess=False):
  fileIdEntity = getDriveFileEntity()
  isEmail, permissionId = getPermissionId()
  showTitles = updateSheetProtectedRanges = False
  while Cmd.ArgumentsRemaining():
    myarg = getArgument()
    if myarg == 'showtitles':
      showTitles = getBoolean()
    elif myarg == 'updatesheetprotectedranges':
      updateSheetProtectedRanges = getBoolean()
    elif myarg in _getMain().ADMIN_ACCESS_OPTIONS:
      useDomainAdminAccess = True
    else:
      unknownArgumentExit()
  _checkFileIdEntityDomainAccess(fileIdEntity, useDomainAdminAccess)
  i, count, users = getEntityArgument(users)
  for user in users:
    i += 1
    user, drive, jcount = _validateUserGetFileIDs(user, i, count, fileIdEntity, entityType=Ent.DRIVE_FILE_OR_FOLDER_ACL, useDomainAdminAccess=useDomainAdminAccess)
    if jcount == 0:
      continue
    if isEmail:
      permissionId = getPermissionIdForEmail(user, i, count, permissionId)
      if not permissionId:
        return
      isEmail = False
    sheet = None
    Ind.Increment()
    j = 0
    for fileId in fileIdEntity['list']:
      j += 1
      try:
        fileName = fileId
        entityType = Ent.DRIVE_FILE_OR_FOLDER_ID
        if showTitles or updateSheetProtectedRanges:
          fileName, entityType, mimeType = _getDriveFileNameFromId(drive, fileId)
          if updateSheetProtectedRanges and mimeType == MIMETYPE_GA_SPREADSHEET:
            permission = callGAPI(drive.permissions(), 'get',
                                  throwReasons=GAPI.DRIVE_ACCESS_THROW_REASONS+[GAPI.BAD_REQUEST, GAPI.PERMISSION_NOT_FOUND, GAPI.INSUFFICIENT_ADMINISTRATOR_PRIVILEGES],
                                  useDomainAdminAccess=useDomainAdminAccess,
                                  fileId=fileId, permissionId=permissionId, fields='type,emailAddress,domain,role', supportsAllDrives=True)
            if not sheet:
              _, sheet = buildGAPIServiceObject(API.SHEETS, user, i, count)
              if not sheet:
                break
        callGAPI(drive.permissions(), 'delete',
                 throwReasons=GAPI.DRIVE_ACCESS_THROW_REASONS+GAPI.DRIVE3_DELETE_ACL_THROW_REASONS,
                 useDomainAdminAccess=useDomainAdminAccess,
                 fileId=fileId, permissionId=permissionId, supportsAllDrives=True)
        entityActionPerformed([Ent.USER, user, entityType, fileName, Ent.PERMISSION_ID, permissionId], j, jcount)
        if updateSheetProtectedRanges and mimeType == MIMETYPE_GA_SPREADSHEET:
          _updateSheetProtectedRangesACLchange(sheet, user, i, count, j, jcount, fileId, fileName, False, permission)
      except (GAPI.fileNotFound, GAPI.forbidden, GAPI.internalError, GAPI.insufficientFilePermissions, GAPI.unknownError, GAPI.invalid,
              GAPI.badRequest, GAPI.cannotRemoveOwner,
              GAPI.cannotModifyInheritedTeamDrivePermission, GAPI.cannotModifyInheritedPermission,
              GAPI.insufficientAdministratorPrivileges, GAPI.sharingRateLimitExceeded, GAPI.cannotDeletePermission,
              GAPI.fileNeverWritable) as e:
        entityActionFailedWarning([Ent.USER, user, entityType, fileName], str(e), j, jcount)
      except GAPI.notFound as e:
        entityActionFailedWarning([Ent.USER, user, Ent.SHAREDDRIVE, fileName], str(e), j, jcount)
      except GAPI.permissionNotFound:
        entityDoesNotHaveItemWarning([Ent.USER, user, entityType, fileName, Ent.PERMISSION_ID, permissionId], j, jcount)
      except (GAPI.serviceNotAvailable, GAPI.authError, GAPI.domainPolicy) as e:
        userDriveServiceNotEnabledWarning(user, str(e), i, count)
        break
    Ind.Decrement()

def doDeleteDriveFileACLs():
  deleteDriveFileACLs([_getAdminEmail()], True)

# gam [<UserTypeEntity>] delete permissions <DriveFileEntity> <DriveFilePermissionIDEntity> [asadmin]
#	<PermissionMatch>* [<PermissionMatchAction>]
def deletePermissions(users, useDomainAdminAccess=False):
  def convertJSONPermissions(jsonPermissions):
    permissionIds = []
    for permission in PM.GetMatchingPermissions(jsonPermissions):
      if permission.get('role', '') == 'owner':
        continue
      permissionIds.append(permission['id'])
    return permissionIds

  def _callbackDeletePermissionId(request_id, _, exception):
    ri = request_id.splitlines()
    if int(ri[RI_J]) == 1:
      entityPerformActionNumItems([Ent.DRIVE_FILE_OR_FOLDER_ID, ri[RI_ENTITY]], int(ri[RI_JCOUNT]), Ent.PERMISSION_ID, int(ri[RI_I]), int(ri[RI_COUNT]))
      Ind.Increment()
    if exception is None:
      entityActionPerformed([Ent.DRIVE_FILE_OR_FOLDER_ID, ri[RI_ENTITY], Ent.PERMISSION_ID, ri[RI_ITEM]], int(ri[RI_J]), int(ri[RI_JCOUNT]))
    else:
      http_status, reason, message = checkGAPIError(exception)
      if reason not in GAPI.DEFAULT_RETRY_REASONS+[GAPI.SERVICE_LIMIT]:
        if reason == GAPI.PERMISSION_NOT_FOUND:
          entityDoesNotHaveItemWarning([Ent.DRIVE_FILE_OR_FOLDER_ID, ri[RI_ENTITY], Ent.PERMISSION_ID, ri[RI_ITEM]], int(ri[RI_J]), int(ri[RI_JCOUNT]))
        elif reason in GAPI.DRIVE3_DELETE_ACL_THROW_REASONS:
          entityActionFailedWarning([Ent.DRIVE_FILE_OR_FOLDER_ID, ri[RI_ENTITY], Ent.PERMISSION_ID, ri[RI_ITEM]], message, int(ri[RI_J]), int(ri[RI_JCOUNT]))
        else:
          errMsg = getHTTPError({}, http_status, reason, message)
          entityActionFailedWarning([Ent.DRIVE_FILE_OR_FOLDER_ID, ri[RI_ENTITY], Ent.PERMISSION_ID, ri[RI_ITEM]], errMsg, int(ri[RI_J]), int(ri[RI_JCOUNT]))
        if int(ri[RI_J]) == int(ri[RI_JCOUNT]):
          Ind.Decrement()
        return
      waitOnFailure(1, 10, reason, message)
      try:
        callGAPI(drive.permissions(), 'delete',
                 throwReasons=GAPI.DRIVE_ACCESS_THROW_REASONS+GAPI.DRIVE3_DELETE_ACL_THROW_REASONS,
                 retryReasons=[GAPI.SERVICE_LIMIT],
                 useDomainAdminAccess=useDomainAdminAccess,
                 fileId=ri[RI_ENTITY], permissionId=ri[RI_ITEM], supportsAllDrives=True)
        entityActionPerformed([Ent.DRIVE_FILE_OR_FOLDER_ID, ri[RI_ENTITY], Ent.PERMISSION_ID, ri[RI_ITEM]], int(ri[RI_J]), int(ri[RI_JCOUNT]))
      except (GAPI.fileNotFound, GAPI.forbidden, GAPI.internalError, GAPI.insufficientFilePermissions, GAPI.unknownError, GAPI.invalid,
              GAPI.badRequest, GAPI.notFound, GAPI.permissionNotFound, GAPI.cannotRemoveOwner,
              GAPI.cannotModifyInheritedTeamDrivePermission, GAPI.cannotModifyInheritedPermission,
              GAPI.insufficientAdministratorPrivileges, GAPI.sharingRateLimitExceeded, GAPI.cannotDeletePermission,
              GAPI.fileNeverWritable,
              GAPI.serviceNotAvailable, GAPI.authError, GAPI.domainPolicy) as e:
        entityActionFailedWarning([Ent.DRIVE_FILE_OR_FOLDER_ID, ri[RI_ENTITY], Ent.PERMISSION_ID, ri[RI_ITEM]], str(e), int(ri[RI_J]), int(ri[RI_JCOUNT]))
    if int(ri[RI_J]) == int(ri[RI_JCOUNT]):
      Ind.Decrement()

  fileIdEntity = getDriveFileEntity()
  if not checkArgumentPresent('json'):
    permissionIds = getEntityList(Cmd.OB_DRIVE_FILE_PERMISSION_ID_ENTITY)
    jsonData = None
    PM = None
  else:
    permissionIds = []
    jsonData = getJSON([])
    PM = PermissionMatch()
    PM.SetDefaultMatch(False, {'role': 'owner'})
  while Cmd.ArgumentsRemaining():
    myarg = getArgument()
    if myarg in _getMain().ADMIN_ACCESS_OPTIONS:
      useDomainAdminAccess = True
    elif PM and PM.ProcessArgument(myarg):
      pass
    else:
      unknownArgumentExit()
  _checkFileIdEntityDomainAccess(fileIdEntity, useDomainAdminAccess)
  if jsonData:
    if 'permission' in jsonData:
      permissionIds = convertJSONPermissions([jsonData['permission']])
    elif 'permissions' in jsonData:
      permissionIds = convertJSONPermissions(jsonData['permissions'])
  permissionIdsLists = permissionIds if isinstance(permissionIds, dict) else None
  i, count, users = getEntityArgument(users)
  for user in users:
    i += 1
    origUser = user
    user, drive, jcount = _validateUserGetFileIDs(user, i, count, fileIdEntity, useDomainAdminAccess=useDomainAdminAccess)
    if not drive:
      continue
    entityPerformActionSubItemModifierNumItems([Ent.USER, user], Ent.DRIVE_FILE_OR_FOLDER_ACL, Act.MODIFIER_FROM, jcount, Ent.DRIVE_FILE_OR_FOLDER, i, count)
    if jcount == 0:
      continue
    try:
      callGAPI(drive.about(), 'get',
               throwReasons=GAPI.DRIVE_USER_THROW_REASONS,
               fields='kind')
    except (GAPI.serviceNotAvailable, GAPI.authError, GAPI.domainPolicy) as e:
      userDriveServiceNotEnabledWarning(user, str(e), i, count)
      continue
    Ind.Increment()
    svcargs = dict([('fileId', None), ('permissionId', None), ('useDomainAdminAccess', useDomainAdminAccess), ('supportsAllDrives', True)]+GM.Globals[GM.EXTRA_ARGS_LIST])
    method = getattr(drive.permissions(), 'delete')
    dbatch = drive.new_batch_http_request(callback=_callbackDeletePermissionId)
    bcount = 0
    j = 0
    for fileId in fileIdEntity['list']:
      j += 1
      if permissionIdsLists:
        if not GM.Globals[GM.CSV_SUBKEY_FIELD]:
          permissionIds = permissionIdsLists[fileId]
        else:
          permissionIds = permissionIdsLists[origUser][fileId]
      kcount = len(permissionIds)
      if kcount == 0:
        continue
      k = 0
      for permissionId in permissionIds:
        k += 1
        svcparms = svcargs.copy()
        svcparms['fileId'] = fileId
        svcparms['permissionId'] = permissionId
        dbatch.add(method(**svcparms), request_id=batchRequestID(fileId, j, jcount, k, kcount, permissionId))
        bcount += 1
        if bcount >= GC.Values[GC.BATCH_SIZE]:
          executeBatch(dbatch)
          dbatch = drive.new_batch_http_request(callback=_callbackDeletePermissionId)
          bcount = 0
    if bcount > 0:
      dbatch.execute()
    Ind.Decrement()

def doDeletePermissions():
  deletePermissions([_getAdminEmail()], True)

# gam [<UserTypeEntity>] info drivefileacl <DriveFileEntity> <DriveFilePermissionIDorEmail> [asadmin]
#	[showtitles] [formatjson]
def infoDriveFileACLs(users, useDomainAdminAccess=False):
  fileIdEntity = getDriveFileEntity()
  isEmail, permissionId = getPermissionId()
  showTitles = False
  FJQC = FormatJSONQuoteChar()
  while Cmd.ArgumentsRemaining():
    myarg = getArgument()
    if myarg == 'showtitles':
      showTitles = getBoolean()
    elif myarg in _getMain().ADMIN_ACCESS_OPTIONS:
      useDomainAdminAccess = True
    else:
      FJQC.GetFormatJSON(myarg)
  _checkFileIdEntityDomainAccess(fileIdEntity, useDomainAdminAccess)
  printKeys, timeObjects = _getDriveFileACLPrintKeysTimeObjects()
  i, count, users = getEntityArgument(users)
  for user in users:
    i += 1
    user, drive, jcount = _validateUserGetFileIDs(user, i, count, fileIdEntity, entityType=[Ent.DRIVE_FILE_OR_FOLDER_ACL, None][FJQC.formatJSON],
                                                  useDomainAdminAccess=useDomainAdminAccess)
    if jcount == 0:
      continue
    if isEmail:
      permissionId = getPermissionIdForEmail(user, i, count, permissionId)
      if not permissionId:
        return
      isEmail = False
    Ind.Increment()
    j = 0
    for fileId in fileIdEntity['list']:
      j += 1
      try:
        fileName = fileId
        entityType = Ent.DRIVE_FILE_OR_FOLDER_ID
        if showTitles:
          fileName, entityType, _ = _getDriveFileNameFromId(drive, fileId, not FJQC.formatJSON, useDomainAdminAccess)
        permission = callGAPI(drive.permissions(), 'get',
                              throwReasons=GAPI.DRIVE_ACCESS_THROW_REASONS+[GAPI.BAD_REQUEST, GAPI.PERMISSION_NOT_FOUND, GAPI.INSUFFICIENT_ADMINISTRATOR_PRIVILEGES],
                              useDomainAdminAccess=useDomainAdminAccess,
                              fileId=fileId, permissionId=permissionId, fields='*', supportsAllDrives=True)
        if not FJQC.formatJSON:
          jcount = len(permission)
          entityPerformActionNumItems([entityType, fileName], jcount, Ent.PERMITTEE)
          Ind.Increment()
          _showDriveFilePermission(permission, printKeys, timeObjects, j, jcount)
          Ind.Decrement()
        else:
          _showDriveFilePermissionJSON(user, fileId, fileName, None, permission, timeObjects)
      except (GAPI.fileNotFound, GAPI.forbidden, GAPI.internalError, GAPI.insufficientFilePermissions, GAPI.unknownError,
              GAPI.badRequest, GAPI.insufficientAdministratorPrivileges) as e:
        entityActionFailedWarning([Ent.USER, user, entityType, fileName], str(e), j, jcount)
      except GAPI.permissionNotFound:
        entityDoesNotHaveItemWarning([Ent.USER, user, entityType, fileName, Ent.PERMISSION_ID, permissionId], j, jcount)
      except (GAPI.serviceNotAvailable, GAPI.authError, GAPI.domainPolicy) as e:
        userDriveServiceNotEnabledWarning(user, str(e), i, count)
        break
    Ind.Decrement()

def doInfoDriveFileACLs():
  infoDriveFileACLs([_getAdminEmail()], True)

def getDriveFilePermissionsFields(myarg, fieldsList):
  if myarg in DRIVE_PERMISSIONS_SUBFIELDS_CHOICE_MAP:
    fieldsList.append(DRIVE_PERMISSIONS_SUBFIELDS_CHOICE_MAP[myarg])
  elif myarg == 'basicpermissions':
    fieldsList.extend(DRIVEFILE_BASIC_PERMISSION_FIELDS[:-1])
  elif myarg == 'fields':
    for field in _getFieldsList():
      if field in DRIVE_PERMISSIONS_SUBFIELDS_CHOICE_MAP:
        fieldsList.append(DRIVE_PERMISSIONS_SUBFIELDS_CHOICE_MAP[field])
      elif field == 'basicpermissions':
        fieldsList.extend(DRIVEFILE_BASIC_PERMISSION_FIELDS[:-1])
      else:
        invalidChoiceExit(field, DRIVE_PERMISSIONS_SUBFIELDS_CHOICE_MAP, True)
  else:
    return False
  return True

# gam [<UserTypeEntity>] print drivefileacls <DriveFileEntity> [todrive <ToDriveAttribute>*]
#	(role|roles <DriveFileACLRoleList>)*
#	<PermissionMatch>* [<PermissionMatchAction>] [pmselect]
#	[includepermissionsforview published]
#	[oneitemperrow] [<DrivePermissionsFieldName>*|(fields <DrivePermissionsFieldNameList>)]
#	[showtitles|(addtitle <String>)]]
#	(orderby <DriveFileOrderByFieldName> [ascending|descending])*
#	[formatjson [quotechar <Character>]] [asadmin]
# gam [<UserTypeEntity>] show drivefileacls <DriveFileEntity>
#	(role|roles <DriveFileACLRoleList>)*
#	<PermissionMatch>* [<PermissionMatchAction>] [pmselect]
#	[includepermissionsforview published]
#	[oneitemperrow] [<DrivePermissionsFieldName>*|(fields <DrivePermissionsFieldNameList>)]
#	[showtitles|(addtitle <String>)]]
#	(orderby <DriveFileOrderByFieldName> [ascending|descending])*
#	[formatjson] [asadmin]
def printShowDriveFileACLs(users, useDomainAdminAccess=False):
  def _printPermissionRow(baserow, permission):
    row = baserow.copy()
    flattenJSON({'permission': permission}, flattened=row, timeObjects=timeObjects)
    if not FJQC.formatJSON:
      csvPF.WriteRowTitles(row)
    elif csvPF.CheckRowTitles(row):
      row = baserow.copy()
      row['JSON'] = json.dumps(cleanJSON({'permission': permission}, timeObjects=timeObjects),
                               ensure_ascii=False, sort_keys=True)
      csvPF.WriteRowNoFilter(row)

  csvPF = CSVPrintFile(['Owner', 'id'], 'sortall') if Act.csvFormat() else None
  FJQC = FormatJSONQuoteChar(csvPF)
  fileIdEntity = getDriveFileEntity()
  aclRolesMap = DRIVEFILE_ACL_ROLES_MAP.copy()
  if fileIdEntity['shareddrivename'] or fileIdEntity['shareddriveadminquery'] or fileIdEntity['shareddrivefilequery'] or fileIdEntity['shareddrive']:
    aclRolesMap['owner'] = 'organizer'
  addTitle = None
  roles = set()
  oneItemPerRow = pmselect = showTitles = False
  includePermissionsForView = set()
  fieldsList = []
  OBY = OrderBy(DRIVEFILE_ORDERBY_CHOICE_MAP)
  PM = PermissionMatch()
  while Cmd.ArgumentsRemaining():
    myarg = getArgument()
    if csvPF and myarg == 'todrive':
      csvPF.GetTodriveParameters()
    elif myarg in {'role', 'roles'}:
      roles |= getACLRoles(aclRolesMap)
    elif myarg == 'oneitemperrow':
      oneItemPerRow = True
    elif myarg == 'orderby':
      OBY.GetChoice()
    elif myarg in {'showtitles', 'addtitle'}:
      if myarg == 'showtitles':
        showTitles = True
        addTitle = None
      else:
        addTitle = getString(Cmd.OB_STRING)
        showTitles = False
      if csvPF:
        csvPF.AddTitles('name')
        csvPF.SetSortAllTitles()
    elif getDriveFilePermissionsFields(myarg, fieldsList):
      pass
    elif myarg in _getMain().ADMIN_ACCESS_OPTIONS:
      useDomainAdminAccess = True
    elif myarg == 'pmselect':
      pmselect = True
    elif myarg == 'pmfilter': # Ignore, this is the default behavior
      pass
    elif PM.ProcessArgument(myarg):
      pass
    elif myarg == 'includepermissionsforview':
      _getIncludePermissionsForView(includePermissionsForView)
    else:
      FJQC.GetFormatJSONQuoteChar(myarg, True)
  _checkFileIdEntityDomainAccess(fileIdEntity, useDomainAdminAccess)
  if fieldsList:
    if roles:
      fieldsList.append('role')
  includePermissionsForView = _finalizeIncludePermissionsForView(includePermissionsForView)
  fields = getItemFieldsFromFieldsList('permissions', fieldsList, True)
  printKeys, timeObjects = _getDriveFileACLPrintKeysTimeObjects()
  i, count, users = getEntityArgument(users)
  for user in users:
    i += 1
    user, drive, jcount = _validateUserGetFileIDs(user, i, count, fileIdEntity,
                                                  entityType=[Ent.DRIVE_FILE_OR_FOLDER, None][csvPF is not None or FJQC.formatJSON],
                                                  orderBy=OBY.orderBy, useDomainAdminAccess=useDomainAdminAccess)
    if jcount == 0:
      continue
    Ind.Increment()
    j = 0
    for fileId in fileIdEntity['list']:
      j += 1
      fileName = fileId
      entityType = Ent.DRIVE_FILE_OR_FOLDER_ID
      if showTitles:
        fileName, entityType, _ = _getDriveFileNameFromId(drive, fileId, not (csvPF or FJQC.formatJSON), useDomainAdminAccess)
      elif addTitle:
        fileName = f'{addTitle} ({fileId})'
        entityType = Ent.DRIVE_FILE_OR_FOLDER
      try:
        permissions = callGAPIpages(drive.permissions(), 'list', 'permissions',
                                    throwReasons=GAPI.DRIVE3_GET_ACL_REASONS+[GAPI.NOT_FOUND],
                                    retryReasons=GAPI.SERVICE_NOT_AVAILABLE_RETRY_REASONS,
                                    useDomainAdminAccess=useDomainAdminAccess,
                                    includePermissionsForView=includePermissionsForView,
                                    fileId=fileId, fields=fields, supportsAllDrives=True)
        for permission in permissions:
          permission.pop('teamDrivePermissionDetails', None)
      except (GAPI.fileNotFound, GAPI.forbidden, GAPI.internalError,
              GAPI.insufficientAdministratorPrivileges, GAPI.insufficientFilePermissions,
              GAPI.unknownError, GAPI.invalid) as e:
        entityActionFailedWarning([Ent.USER, user, entityType, fileName], str(e), j, jcount)
        continue
      except GAPI.notFound as e:
        entityActionFailedWarning([Ent.USER, user, Ent.SHAREDDRIVE, fileName], str(e), j, jcount)
        continue
      except (GAPI.serviceNotAvailable, GAPI.authError, GAPI.domainPolicy) as e:
        userDriveServiceNotEnabledWarning(user, str(e), i, count)
        break
      if pmselect:
        if not PM.CheckPermissionMatches(permissions):
          continue
      else:
        permissions = PM.GetMatchingPermissions(permissions)
      if roles:
        matchingPermissions = []
        for permission in permissions:
          if roles and permission['role'] not in roles:
            continue
          matchingPermissions.append(permission)
        permissions = matchingPermissions
      if not csvPF:
        if not FJQC.formatJSON:
          _showDriveFilePermissions(entityType, fileName, permissions, printKeys, timeObjects, j, jcount)
        else:
          if oneItemPerRow:
            for permission in permissions:
              _showDriveFilePermissionJSON(user, fileId, fileName, None, permission, timeObjects)
          else:
            _showDriveFilePermissionsJSON(user, fileId, fileName, None, permissions, timeObjects)
      else:
        baserow = {'Owner': user, 'id': fileId}
        if showTitles or addTitle:
          baserow['name'] = fileName
        if oneItemPerRow:
          for permission in permissions:
            _mapDrivePermissionNames(permission)
            pdetails = permission.pop('permissionDetails', [])
            if not pdetails:
              _printPermissionRow(baserow, permission)
            else:
              for pdetail in pdetails:
                permission['permissionDetails'] = pdetail
                _printPermissionRow(baserow, permission)
        else:
          row = baserow.copy()
          for permission in permissions:
            _mapDrivePermissionNames(permission)
          flattenJSON({'permissions': permissions}, flattened=row, timeObjects=timeObjects)
          if not FJQC.formatJSON:
            csvPF.WriteRowTitles(row)
          elif csvPF.CheckRowTitles(row):
            baserow['JSON'] = json.dumps(cleanJSON({'permissions': permissions}, timeObjects=timeObjects),
                                         ensure_ascii=False, sort_keys=True)
            csvPF.WriteRowNoFilter(baserow)
    Ind.Decrement()
  if csvPF:
    if not oneItemPerRow:
      csvPF.SetIndexedTitles(['permissions'])
    csvPF.writeCSVfile('Drive File ACLs')

def doPrintShowDriveFileACLs():
  printShowDriveFileACLs([_getAdminEmail()], True)

DRIVELABELS_PROJECTION_CHOICE_MAP = {'basic': 'LABEL_VIEW_BASIC', 'full': 'LABEL_VIEW_FULL'}
DRIVELABELS_PERMISSION_ROLE_MAP = {
  'applier': 'APPLIER',
  'editor': 'EDITOR',
  'organizer': 'ORGANIZER',
  'organiser': 'ORGANIZER',
  'reader': 'READER',
  }
DRIVELABELS_TIME_OBJECTS = {'createTime', 'publishTime', 'disableTime', 'revisionCreateTime'}

