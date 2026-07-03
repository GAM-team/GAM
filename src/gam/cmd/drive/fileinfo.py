"""File counts, comments, paths, disk usage, share counts, tree printing.

Part of the drive sub-package, extracted from drive.py."""

"""GAM Google Drive file, permission, shared drive, and label management."""

import re
import sys
import platform

from gam.cmd.drive.core import _getDriveFileNameFromId, _validateUserGetFileIDs, getDriveFileEntity
import os

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

from gam.cmd.drive.core import (
    MimeTypeCheck, _getSharedDriveNameFromId, _simpleFileIdEntityList,
    _validateUserGetFileIDs, _validateUserSharedDrive,
    cleanFileIDsList, getDriveFileEntity, getSharedDriveEntity, initDriveFileEntity,
)
from gam.cmd.drive.filepaths import DRIVEFILE_ORDERBY_CHOICE_MAP, _setGetCheckFilePermissions
from gam.cmd.drive.filetree import (
    DriveListParameters,
    FILECOUNT_SUMMARY_CHOICE_MAP, FILECOUNT_SUMMARY_NONE,
    FILECOUNT_SUMMARY_ONLY, FILECOUNT_SUMMARY_USER,
    OWNED_BY_ME_FIELDS_TITLES, SHOW_OWNED_BY_CHOICE_MAP,
    SIZE_FIELD_CHOICE_MAP, _getGettingEntity,
    extendFileTree, extendFileTreeParents, initFileTree,
)
from gam.cmd.drive.filelist import (
    _checkUpdateLastModifiction, _getLastModificationPath,
    _initLastModification, _showLastModification, _updateLastModificationRow,
)
from gam.util.api import buildGAPIObject, callGAPI, callGAPIpages, yieldGAPIpages
from gam.util.args import (
    OrderBy,
    formatFileSize,
    formatLocalSecondsTimestamp,
    getAddCSVData,
    getArgument,
    getBoolean,
    getCharacter,
    getChoice,
    getInteger,
    getString,
)
from gam.util.csv_pf import CSVPrintFile, _getFieldsList, getFieldsFromFieldsList, getItemFieldsFromFieldsList
from gam.util.display import (
    entityActionFailedWarning,
    entityActionNotPerformedWarning,
    entityActionPerformed,
    getPageMessageForWhom,
    invalidQuery,
    printEntity,
    printEntityKVList,
    printGettingAllEntityItemsForWhom,
    printGotEntityItemsForWhom,
    printKeyValueList,
    printKeyValueListWithCount,
    userDriveServiceNotEnabledWarning,
)
from gam.util.entity import getEntityArgument
from gam.util.errors import invalidChoiceExit, unknownArgumentExit, usageErrorExit
from gam.util.output import writeStdout




def __getattr__(name):
  """Fall back to gam module for any undefined names."""
  main = _getMain()
  try:
    return getattr(main, name)
  except AttributeError:
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")

SHARED_DRIVE_MAX_FILES_FOLDERS = 500000
TEAM_DRIVE = 'Drive'
MY_DRIVE = 'My Drive'

def printShowFileCounts(users):
  def _setSelectionFields():
    if DLP.showOwnedBy is not None:
      fieldsList.extend(OWNED_BY_ME_FIELDS_TITLES)
    if (showSize or showSizeUnits) or (DLP.minimumFileSize is not None) or (DLP.maximumFileSize is not None):
      fieldsList.append(sizeField)
    if showLastModification:
      fieldsList.extend(['id,name,modifiedTime,lastModifyingUser(me, displayName, emailAddress),parents'])
    if DLP.filenameMatchPattern:
      fieldsList.append('name')
    if DLP.excludeTrashed:
      fieldsList.append('trashed')
    if DLP.PM.permissionMatches:
      fieldsList.extend(['id', 'permissions'])
    if DLP.onlySharedDrives or getPermissionsForSharedDrives:
      fieldsList.append('driveId')

  def showMimeTypeInfo(user, mimeTypeInfo, sharedDriveId, sharedDriveName, lastModification, i, count):
    if summary != FILECOUNT_SUMMARY_NONE:
      if count != 0:
        for mimeType, mtinfo in mimeTypeInfo.items():
          summaryMimeTypeInfo.setdefault(mimeType, {'count': 0, 'size': 0})
          summaryMimeTypeInfo[mimeType]['count'] += mtinfo['count']
          summaryMimeTypeInfo[mimeType]['size'] += mtinfo['size']
        if summary == FILECOUNT_SUMMARY_ONLY:
          return
    countTotal = sizeTotal = 0
    for mtinfo in mimeTypeInfo.values():
      countTotal += mtinfo['count']
      sizeTotal += mtinfo['size']
    if not csvPF:
      if sharedDriveId:
        kvList = [Ent.USER, user, Ent.SHAREDDRIVE, f'{sharedDriveName} ({sharedDriveId})']
      else:
        kvList = [Ent.USER, user]
      dataList = [Ent.Choose(Ent.DRIVE_FILE_OR_FOLDER, countTotal), countTotal]
      if showSize:
        dataList.extend(['Size', sizeTotal])
      if showSizeUnits:
        dataList.extend(['SizeUnits', formatFileSize(sizeTotal)])
      if sharedDriveId:
        dataList.extend(['Item cap', f"{countTotal/SHARED_DRIVE_MAX_FILES_FOLDERS:.2%}"])
      printEntityKVList(kvList, dataList, i, count)
      Ind.Increment()
      if showLastModification:
        _showLastModification(lastModification)
      for mimeType, mtinfo in sorted(mimeTypeInfo.items()):
        if not showMimeTypeSize:
          printKeyValueList([mimeType, mtinfo['count']])
        else:
          printKeyValueList([mimeType, f"{mtinfo['count']}, {mtinfo['size']}"])
      Ind.Decrement()
    else:
      if sharedDriveId:
        row = {'User': user, 'id': sharedDriveId, 'name': sharedDriveName, 'Total': countTotal, 'Item cap': f"{countTotal/SHARED_DRIVE_MAX_FILES_FOLDERS:.2%}"}
      else:
        row = {'User': user, 'Total': countTotal}
      if showSize:
        row['Size'] = sizeTotal
      if showSizeUnits:
        row['SizeUnits'] = formatFileSize(sizeTotal)
      if showLastModification:
        _updateLastModificationRow(row, lastModification)
      if addCSVData:
        row.update(addCSVData)
      for mimeType, mtinfo in sorted(mimeTypeInfo.items()):
        row[f'{mimeType}'] = mtinfo['count']
        if showMimeTypeSize:
          row[f'{mimeType}:Size'] = mtinfo['size']
      csvPF.WriteRowTitles(row)

  csvPF = CSVPrintFile() if Act.csvFormat() else None
  if csvPF:
    csvPF.SetZeroBlankMimeTypeCounts(True)
  fieldsList = ['mimeType']
  DLP = DriveListParameters({'allowChoose': False, 'allowCorpora': True, 'allowQuery': True, 'mimeTypeInQuery': True})
  pathDelimiter = '/'
  sharedDriveId = sharedDriveName = ''
  continueOnInvalidQuery = showSize = showSizeUnits = showLastModification = showMimeTypeSize = False
  sizeField = 'quotaBytesUsed'
  summary = FILECOUNT_SUMMARY_NONE
  summaryUser = FILECOUNT_SUMMARY_USER
  summaryMimeTypeInfo = {}
  fileIdEntity = {}
  addCSVData = {}
  summaryLastModification = _initLastModification()
  while Cmd.ArgumentsRemaining():
    myarg = getArgument()
    if csvPF and myarg == 'todrive':
      csvPF.GetTodriveParameters()
    elif DLP.ProcessArgument(myarg, fileIdEntity):
      pass
    elif myarg == 'select':
      if fileIdEntity:
        usageErrorExit(Msg.CAN_NOT_BE_SPECIFIED_MORE_THAN_ONCE.format('select'))
      fileIdEntity = getSharedDriveEntity()
    elif myarg == 'showsize':
      showSize = True
    elif myarg == 'showsizeunits':
      showSizeUnits = True
    elif myarg == 'showmimetypesize':
      showMimeTypeSize = showSize = True
    elif myarg == 'sizefield':
      sizeField = getChoice(SIZE_FIELD_CHOICE_MAP, mapChoice=True)
    elif myarg == 'showlastmodification':
      showLastModification = True
    elif myarg == 'summary':
      summary = getChoice(FILECOUNT_SUMMARY_CHOICE_MAP, mapChoice=True)
    elif myarg == 'summaryuser':
      summaryUser = getString(Cmd.OB_STRING)
    elif myarg == 'pathdelimiter':
      pathDelimiter = getCharacter()
    elif csvPF and myarg == 'addcsvdata':
      getAddCSVData(addCSVData)
    elif myarg == 'continueoninvalidquery':
      continueOnInvalidQuery = getBoolean()
    else:
      unknownArgumentExit()
  if not fileIdEntity:
    fileIdEntity = DLP.GetFileIdEntity()
  if not fileIdEntity.get('shareddrive'):
    btkwargs = DLP.kwargs
  else:
    btkwargs = fileIdEntity['shareddrive']
    fieldsList.append('driveId')
  DLP.Finalize(fileIdEntity)
  if DLP.PM.permissionMatches:
    getPermissionDetailsForMyDrive = DLP.PM.checkDetails
    getPermissionsForSharedDrives = True
    permissionsFields = f'nextPageToken,permissions({",".join(DLP.PM.permissionFields)})'
  else:
    getPermissionDetailsForMyDrive = getPermissionsForSharedDrives = False
  _setSelectionFields()
  if csvPF:
    sortTitles = ['User', 'id', 'name', 'Total', 'Item cap'] if fileIdEntity.get('shareddrive') else ['User', 'Total']
    if showSizeUnits:
      sortTitles.insert(sortTitles.index('Total')+1, 'SizeUnits')
    if showSize:
      sortTitles.insert(sortTitles.index('Total')+1, 'Size')
    if showLastModification:
      sortTitles.extend(['lastModifiedFileId', 'lastModifiedFileName',
                         'lastModifiedFileMimeType', 'lastModifiedFilePath',
                         'lastModifyingUser', 'lastModifiedTime'])
    if addCSVData:
      sortTitles.extend(sorted(addCSVData.keys()))
    csvPF.SetTitles(sortTitles)
    csvPF.SetSortAllTitles()
  pagesFields = getItemFieldsFromFieldsList('files', fieldsList)
  i, count, users = getEntityArgument(users)
  for user in users:
    i += 1
    user, drive = _validateUserSharedDrive(user, i, count, fileIdEntity)
    if not drive:
      continue
    sharedDriveId = fileIdEntity.get('shareddrive', {}).get('driveId', '')
    sharedDriveName = _getSharedDriveNameFromId(drive, sharedDriveId) if sharedDriveId else ''
    mimeTypeInfo = {}
    userLastModification = _initLastModification()
    gettingEntity = _getGettingEntity(user, fileIdEntity)
    printGettingAllEntityItemsForWhom(Ent.DRIVE_FILE_OR_FOLDER, gettingEntity, i, count, query=DLP.fileIdEntity['query'])
    try:
      feed = yieldGAPIpages(drive.files(), 'list', 'files',
                            pageMessage=getPageMessageForWhom(),
                            throwReasons=GAPI.DRIVE_USER_THROW_REASONS+[GAPI.INVALID_QUERY, GAPI.INVALID,
                                                                        GAPI.BAD_REQUEST, GAPI.FILE_NOT_FOUND,
                                                                        GAPI.NOT_FOUND, GAPI.TEAMDRIVE_MEMBERSHIP_REQUIRED],
                            retryReasons=[GAPI.UNKNOWN_ERROR],
                            q=DLP.fileIdEntity['query'],
                            fields=pagesFields, pageSize=GC.Values[GC.DRIVE_MAX_RESULTS], **btkwargs)
      for files in feed:
        for f_file in files:
          driveId = f_file.get('driveId')
          getCheckFilePermissions = _setGetCheckFilePermissions(f_file, getPermissionDetailsForMyDrive, getPermissionsForSharedDrives,
                                                                driveId, DLP)
          if (not DLP.CheckShowOwnedBy(f_file) or
              not DLP.CheckShowSharedByMe(f_file) or
              not DLP.CheckExcludeTrashed(f_file) or
              not DLP.CheckFileSize(f_file, sizeField) or
              not DLP.CheckFilenameMatch(f_file) or
              (not getCheckFilePermissions and not DLP.CheckFilePermissionMatches(f_file)) or
              (DLP.onlySharedDrives and not driveId)):
            continue
          if getCheckFilePermissions:
            try:
              f_file['permissions'] = callGAPIpages(drive.permissions(), 'list', 'permissions',
                                                    throwReasons=GAPI.DRIVE3_GET_ACL_REASONS+[GAPI.BAD_REQUEST],
                                                    retryReasons=GAPI.SERVICE_NOT_AVAILABLE_RETRY_REASONS,
                                                    fileId=f_file['id'], fields=permissionsFields, supportsAllDrives=True)
              if not DLP.CheckFilePermissionMatches(f_file):
                continue
              for permission in f_file['permissions']:
                permission.pop('teamDrivePermissionDetails', None)
            except (GAPI.fileNotFound, GAPI.forbidden, GAPI.internalError,
                    GAPI.insufficientAdministratorPrivileges, GAPI.insufficientFilePermissions,
                    GAPI.unknownError, GAPI.invalid, GAPI.badRequest,
                    GAPI.serviceNotAvailable, GAPI.authError, GAPI.domainPolicy):
              continue
          mimeTypeInfo.setdefault(f_file['mimeType'], {'count': 0, 'size': 0})
          mimeTypeInfo[f_file['mimeType']]['count'] += 1
          mimeTypeInfo[f_file['mimeType']]['size'] += int(f_file.get(sizeField, '0'))
          if showLastModification:
            _checkUpdateLastModifiction(f_file, userLastModification)
      _getLastModificationPath(drive, userLastModification, pathDelimiter)
      showMimeTypeInfo(user, mimeTypeInfo, sharedDriveId, sharedDriveName, userLastModification, i, count)
      if showLastModification and userLastModification['lastModifiedTime'] > summaryLastModification['lastModifiedTime']:
        summaryLastModification = userLastModification.copy()
    except (GAPI.invalidQuery, GAPI.invalid, GAPI.badRequest):
      entityActionFailedWarning([Ent.USER, user, Ent.DRIVE_FILE_OR_FOLDER, None], invalidQuery(DLP.fileIdEntity['query']), i, count)
      if not continueOnInvalidQuery:
        break
      continue
    except GAPI.fileNotFound:
      printGotEntityItemsForWhom(0)
    except (GAPI.notFound, GAPI.teamDriveMembershipRequired) as e:
      entityActionFailedWarning([Ent.USER, user, Ent.SHAREDDRIVE_ID, sharedDriveId], str(e), i, count)
    except (GAPI.serviceNotAvailable, GAPI.authError, GAPI.domainPolicy) as e:
      userDriveServiceNotEnabledWarning(user, str(e), i, count)
      continue
  if summary != FILECOUNT_SUMMARY_NONE:
    showMimeTypeInfo(summaryUser, summaryMimeTypeInfo,
                     '' if count > 1 else sharedDriveId,
                     '' if count > 1 else sharedDriveName,
                     summaryLastModification, 0, 0)
  if csvPF:
    csvPF.writeCSVfile('Drive File Counts')

# gam <UserTypeEntity> print drivelastmodification [todrive <ToDriveAttribute>*]
#	[select <SharedDriveEntity>]
#	[pathdelimiter <Character>]
#	(addcsvdata <FieldName> <String>)*
# gam <UserTypeEntity> show drivelastmodification
#	[select <SharedDriveEntity>]
#	[pathdelimiter <Character>]
def printShowDrivelastModifications(users):
  def showLastModificationInfo(user, sharedDriveId, sharedDriveName, lastModification, i, count):
    if not csvPF:
      if sharedDriveId:
        kvList = [Ent.USER, user, Ent.SHAREDDRIVE, f'{sharedDriveName} ({sharedDriveId})']
      else:
        kvList = [Ent.USER, user]
      printEntity(kvList, i, count)
      Ind.Increment()
      _showLastModification(lastModification)
      Ind.Decrement()
    else:
      if sharedDriveId:
        row = {'User': user, 'id': sharedDriveId, 'name': sharedDriveName}
      else:
        row = {'User': user}
      _updateLastModificationRow(row, lastModification)
      if addCSVData:
        row.update(addCSVData)
      csvPF.WriteRowTitles(row)

  csvPF = CSVPrintFile() if Act.csvFormat() else None
  fieldsList = ['id', 'driveId', 'name', 'mimeType', 'lastModifyingUser', 'modifiedTime', 'parents']
  DLP = DriveListParameters({'allowChoose': False, 'allowCorpora': False, 'allowQuery': False, 'mimeTypeInQuery': True})
  pathDelimiter = '/'
  sharedDriveId = sharedDriveName = ''
  fileIdEntity = {}
  addCSVData = {}
  while Cmd.ArgumentsRemaining():
    myarg = getArgument()
    if csvPF and myarg == 'todrive':
      csvPF.GetTodriveParameters()
    elif myarg == 'select':
      if fileIdEntity:
        usageErrorExit(Msg.CAN_NOT_BE_SPECIFIED_MORE_THAN_ONCE.format('select'))
      fileIdEntity = getSharedDriveEntity()
    elif myarg == 'pathdelimiter':
      pathDelimiter = getCharacter()
    elif csvPF and myarg == 'addcsvdata':
      getAddCSVData(addCSVData)
    else:
      unknownArgumentExit()
  if not fileIdEntity:
    fileIdEntity = DLP.GetFileIdEntity()
  if not fileIdEntity.get('shareddrive'):
    btkwargs = DLP.kwargs
  else:
    btkwargs = fileIdEntity['shareddrive']
    fieldsList.append('driveId')
  DLP.Finalize(fileIdEntity)
  if csvPF:
    sortTitles = ['User', 'id', 'name'] if fileIdEntity.get('shareddrive') else ['User']
    if addCSVData:
      sortTitles.extend(sorted(addCSVData.keys()))
    sortTitles.extend(['lastModifiedFileId', 'lastModifiedFileName',
                       'lastModifiedFileMimeType', 'lastModifiedFilePath',
                       'lastModifyingUser', 'lastModifiedTime'])
    csvPF.SetTitles(sortTitles)
    csvPF.SetSortAllTitles()
  pagesFields = getItemFieldsFromFieldsList('files', fieldsList)
  i, count, users = getEntityArgument(users)
  for user in users:
    i += 1
    user, drive = _validateUserSharedDrive(user, i, count, fileIdEntity)
    if not drive:
      continue
    sharedDriveId = fileIdEntity.get('shareddrive', {}).get('driveId', '')
    sharedDriveName = _getSharedDriveNameFromId(drive, sharedDriveId) if sharedDriveId else ''
    userLastModification = _initLastModification()
    gettingEntity = _getGettingEntity(user, fileIdEntity)
    printGettingAllEntityItemsForWhom(Ent.DRIVE_FILE_OR_FOLDER, gettingEntity, i, count)
    try:
      feed = yieldGAPIpages(drive.files(), 'list', 'files',
                            pageMessage=getPageMessageForWhom(),
                            throwReasons=GAPI.DRIVE_USER_THROW_REASONS+[GAPI.INVALID, GAPI.BAD_REQUEST, GAPI.FILE_NOT_FOUND,
                                                                        GAPI.NOT_FOUND, GAPI.TEAMDRIVE_MEMBERSHIP_REQUIRED],
                            retryReasons=[GAPI.UNKNOWN_ERROR],
                            fields=pagesFields, pageSize=GC.Values[GC.DRIVE_MAX_RESULTS], **btkwargs)
      for files in feed:
        for f_file in files:
          _checkUpdateLastModifiction(f_file, userLastModification)
      _getLastModificationPath(drive, userLastModification, pathDelimiter)
      showLastModificationInfo(user, sharedDriveId, sharedDriveName, userLastModification, i, count)
    except (GAPI.invalid, GAPI.badRequest) as e:
      entityActionFailedWarning([Ent.USER, user, Ent.DRIVE_FILE_OR_FOLDER, None], str(e), i, count)
      continue
    except GAPI.fileNotFound:
      printGotEntityItemsForWhom(0)
    except (GAPI.notFound, GAPI.teamDriveMembershipRequired) as e:
      entityActionFailedWarning([Ent.USER, user, Ent.SHAREDDRIVE_ID, sharedDriveId], str(e), i, count)
    except (GAPI.serviceNotAvailable, GAPI.authError, GAPI.domainPolicy) as e:
      userDriveServiceNotEnabledWarning(user, str(e), i, count)
      continue
  if csvPF:
    csvPF.writeCSVfile('Drive File Last Modification')

DISKUSAGE_SHOW_CHOICES = {'all', 'summary', 'summaryandtrash'}

# gam <UserTypeEntity> print diskusage <DriveFileEntity> [todrive <ToDriveAttribute>*]
#	[anyowner|(showownedby any|me|others)]
#	[sizefield quotabytesused|size]
#	[pathdelimiter <Character>] [excludetrashed] [stripcrsfromname]
#	(addcsvdata <FieldName> <String>)*
#	[noprogress] [show all|summary|summaryandtrash]
def printDiskUsage(users):
  def _getChildDriveFolderInfo(drive, fileEntry, user, i, count, depth):
    fileEntry['depth'] = depth
    q = _getMain().WITH_PARENTS.format(fileEntry['id'])
    try:
      children = callGAPIpages(drive.files(), 'list', 'files',
                               throwReasons=GAPI.DRIVE_USER_THROW_REASONS+[GAPI.INVALID_QUERY, GAPI.INVALID],
                               retryReasons=[GAPI.UNKNOWN_ERROR],
                               q=q, orderBy=orderBy, fields=pagesFields,
                               pageSize=GC.Values[GC.DRIVE_MAX_RESULTS], supportsAllDrives=True, includeItemsFromAllDrives=True)
    except (GAPI.invalidQuery, GAPI.invalid):
      entityActionFailedWarning([Ent.USER, user, Ent.DRIVE_FOLDER, None], invalidQuery(q), i, count)
      return
    except (GAPI.serviceNotAvailable, GAPI.authError, GAPI.domainPolicy) as e:
      userDriveServiceNotEnabledWarning(user, str(e), i, count)
      return
    Ind.Increment()
    if showProgress:
      entityActionPerformed([Ent.USER, user, Ent.DRIVE_FOLDER, fileEntry['path']])
    for childEntryInfo in children:
      trashed = childEntryInfo['trashed']
      if trashed and excludeTrashed:
        continue
      mimeType = childEntryInfo.pop('mimeType')
      if mimeType == MIMETYPE_GA_FOLDER:
        fileEntry['directFolderCount'] += 1
        fileEntry['totalFolderCount'] += 1
        if trashed:
          trashFolder['totalFolderCount'] += 1
          if childEntryInfo['explicitlyTrashed']:
            trashFolder['directFolderCount'] += 1
        childEntryInfo['User'] = user
        if includeOwner:
          owners = childEntryInfo.pop('owners', [])
          if owners:
            childEntryInfo['Owner'] = owners[0].get('emailAddress', 'Unknown')
        childEntryInfo.update(zeroFolderInfo)
        if stripCRsFromName:
          childEntryInfo['name'] = _stripControlCharsFromName(childEntryInfo['name'])
        childEntryInfo['path'] = fileEntry['path']+pathDelimiter+childEntryInfo['name']
        childEntryInfo.pop(sizeField, None)
        foldersList.append(childEntryInfo)
        _getChildDriveFolderInfo(drive, childEntryInfo, user, i, count, depth+1)
        fileEntry['totalFileCount'] += childEntryInfo['totalFileCount']
        fileEntry['totalFileSize'] += childEntryInfo['totalFileSize']
        fileEntry['totalFolderCount'] += childEntryInfo['totalFolderCount']
      elif mimeType != MIMETYPE_GA_SHORTCUT:
        if includeOwner and showOwnedBy is not None and childEntryInfo['ownedByMe'] != showOwnedBy:
          continue
        fsize = int(childEntryInfo.get(sizeField, '0'))
        fileEntry['directFileCount'] += 1
        fileEntry['directFileSize'] += fsize
        fileEntry['totalFileCount'] += 1
        fileEntry['totalFileSize'] += fsize
        if trashed:
          trashFolder['totalFileCount'] += 1
          trashFolder['totalFileSize'] += fsize
          if childEntryInfo['explicitlyTrashed']:
            trashFolder['directFileCount'] += 1
            trashFolder['directFileSize'] += fsize
    Ind.Decrement()

  csvPF = CSVPrintFile(['User', 'Owner', 'id', 'name', 'ownedByMe', 'trashed', 'explicitlyTrashed',
                        'directFileCount', 'directFileSize', 'directFolderCount',
                        'totalFileCount', 'totalFileSize', 'totalFolderCount', 'depth', 'path'])
  excludeTrashed = stripCRsFromName = False
  includeOwner = True
  orderBy = 'folder,name'
  zeroFolderInfo = {'directFileCount': 0, 'directFileSize': 0, 'directFolderCount': 0,
                    'totalFileCount': 0, 'totalFileSize': 0, 'totalFolderCount': 0}
  sizeField = 'quotaBytesUsed'
  showOwnedBy = showProgress = True
  pathDelimiter = '/'
  fileIdEntity = getDriveFileEntity()
  addCSVData = {}
  showResults = 'all'
  while Cmd.ArgumentsRemaining():
    myarg = getArgument()
    if myarg == 'todrive':
      csvPF.GetTodriveParameters()
    elif myarg == 'anyowner':
      showOwnedBy = None
    elif myarg == 'showownedby':
      showOwnedBy = getChoice(SHOW_OWNED_BY_CHOICE_MAP, mapChoice=True)
    elif myarg == 'sizefield':
      sizeField = getChoice(SIZE_FIELD_CHOICE_MAP, mapChoice=True)
    elif myarg == 'pathdelimiter':
      pathDelimiter = getCharacter()
    elif myarg == 'excludetrashed':
      excludeTrashed = True
    elif myarg == 'stripcrsfromname':
      stripCRsFromName = True
    elif myarg == 'addcsvdata':
      getAddCSVData(addCSVData)
    elif myarg == 'show':
      showResults = getChoice(DISKUSAGE_SHOW_CHOICES)
    elif myarg == 'noprogress':
      showProgress = False
    else:
      unknownArgumentExit()
  if addCSVData:
    csvPF.AddTitles(sorted(addCSVData.keys()))
  fieldsList = ['id', 'name', 'mimeType', sizeField, 'trashed', 'explicitlyTrashed', 'owners(emailAddress)', 'ownedByMe']
  pagesFields = getItemFieldsFromFieldsList('files', fieldsList)
  topFieldsList = fieldsList[:]
  topFieldsList.extend(['driveId', 'parents'])
  topFields = getFieldsFromFieldsList(topFieldsList)
  i, count, users = getEntityArgument(users)
  i = 0
  for user in users:
    i += 1
    origUser = user
    user, drive, jcount = _validateUserGetFileIDs(origUser, i, count, fileIdEntity, entityType=Ent.DRIVE_DISK_USAGE)
    if jcount == 0:
      continue
    j = 0
    for fileId in fileIdEntity['list']:
      j += 1
      foldersList = []
      trashFolder = {'User': user, 'id': 'Trash', 'name': 'Trash', 'path': 'Trash'}
      trashFolder.update(zeroFolderInfo)
      try:
        topFolder = callGAPI(drive.files(), 'get',
                                 throwReasons=GAPI.DRIVE_GET_THROW_REASONS,
                                 fileId=fileId, fields=topFields, supportsAllDrives=True)
        if stripCRsFromName:
          topFolder['name'] = _stripControlCharsFromName(topFolder['name'])
        mimeType = topFolder.pop('mimeType')
        if mimeType != MIMETYPE_GA_FOLDER:
          entityValueList = [Ent.USER, user, _getMain()._getEntityMimeType(topFolder), topFolder['name']]
          entityActionNotPerformedWarning(entityValueList, Msg.INVALID_MIMETYPE.format(mimeType, MIMETYPE_GA_FOLDER), i, count)
          continue
        if topFolder['trashed']:
          if excludeTrashed:
            entityValueList = [Ent.USER, user, Ent.DRIVE_FOLDER, topFolder['name']]
            entityActionNotPerformedWarning(entityValueList, Msg.IN_TRASH_AND_EXCLUDE_TRASHED, i, count)
            continue
          trashFolder['totalFolderCount'] += 1
          if topFolder['explicitlyTrashed']:
            trashFolder['directFolderCount'] += 1
        driveId = topFolder.pop('driveId', None)
        if driveId:
          includeOwner = False
          csvPF.RemoveTitles(['Owner', 'ownedByMe'])
          if topFolder['name'] == TEAM_DRIVE and not topFolder.get('parents'):
            topFolder['name'] = _getSharedDriveNameFromId(drive, driveId)
            topFolder['path'] = f'{SHARED_DRIVES}{pathDelimiter}{topFolder["name"]}'
          else:
            topFolder['path'] = topFolder['name']
          topFolder.pop('ownedByMe', None)
        elif topFolder['name'] == MY_DRIVE and not topFolder.get('parents'):
          topFolder['path'] = _getMain().MY_DRIVE
        else:
          topFolder['path'] = topFolder['name']
        topFolder['User'] = user
        if includeOwner:
          owners = topFolder.pop('owners', [])
          if owners:
            topFolder['Owner'] = owners[0].get('emailAddress', 'Unknown')
            trashFolder['Owner'] = topFolder['Owner']
        topFolder.pop('parents', None)
        topFolder.update(zeroFolderInfo)
        topFolder.pop(sizeField, None)
        foldersList.append(topFolder)
        _getChildDriveFolderInfo(drive, topFolder, user, i, count, -1)
      except GAPI.fileNotFound:
        entityActionFailedWarning([Ent.USER, user, Ent.DRIVE_FOLDER, fileId], Msg.NOT_FOUND, j, jcount)
        continue
      except (GAPI.notFound, GAPI.teamDriveMembershipRequired) as e:
        entityActionFailedWarning([Ent.USER, user, Ent.SHAREDDRIVE_ID, fileIdEntity['shareddrive']['driveId']], str(e), j, jcount)
        continue
      except (GAPI.serviceNotAvailable, GAPI.authError, GAPI.domainPolicy) as e:
        userDriveServiceNotEnabledWarning(user, str(e), i, count)
        break
      if showResults == 'all':
        for folder in foldersList:
          if addCSVData:
            folder.update(addCSVData)
          csvPF.WriteRow(folder)
      else:
        folder = foldersList[0]
        if addCSVData:
          folder.update(addCSVData)
        csvPF.WriteRow(folder)
      if showResults != 'summary' and not excludeTrashed:
        trashFolder['trashed'] = trashFolder['totalFileCount']+trashFolder['totalFolderCount'] > 0
        trashFolder['explicitlyTrashed'] = trashFolder['directFileCount']+trashFolder['directFolderCount'] > 0
        if addCSVData:
          trashFolder.update(addCSVData)
        trashFolder['depth'] = -1
        csvPF.WriteRow(trashFolder)
  csvPF.writeCSVfile('Drive Disk Usage')

FILESHARECOUNTS_OWNER = 'Owner'
FILESHARECOUNTS_TOTAL = 'Total'
FILESHARECOUNTS_SHARED = 'Shared'
FILESHARECOUNTS_SHARED_EXTERNAL = 'Shared External'
FILESHARECOUNTS_SHARED_INTERNAL = 'Shared Internal'

FILESHARECOUNTS_ZEROCOUNTS = {
  FILESHARECOUNTS_TOTAL: 0,
  FILESHARECOUNTS_SHARED: 0,
  FILESHARECOUNTS_SHARED_EXTERNAL: 0,
  FILESHARECOUNTS_SHARED_INTERNAL: 0,
  'anyone': 0, 'anyoneWithLink': 0,
  'externalDomain': 0, 'externalDomainWithLink': 0,
  'internalDomain': 0, 'internalDomainWithLink': 0,
  'externalGroup': 0, 'internalGroup': 0,
  'externalUser': 0, 'internalUser': 0,
  'deletedGroup': 0, 'deletedUser': 0,
  }

FILESHARECOUNTS_CATEGORIES = {
  'anyone': {False: 'anyone', True: 'anyoneWithLink'},
  'domain': {False: {False: 'externalDomain', True: 'externalDomainWithLink'}, True: {False: 'internalDomain', True: 'internalDomainWithLink'}},
  'group': {False: 'externalGroup', True: 'internalGroup'},
  'user': {False: 'externalUser', True: 'internalUser'},
  'deleted': {'group': 'deletedGroup', 'user': 'deletedUser'},
  }

# gam <UserTypeEntity> print filesharecounts [todrive <ToDriveAttribute>*]
#	[excludetrashed]
#	[internaldomains all|primary|<DomainNameList>]
#	[summary none|only|plus] [summaryuser <String>]
# gam <UserTypeEntity> show filesharecounts
#	[excludetrashed]
#	[internaldomains all|primary|<DomainNameList>]
#	[summary none|only|plus] [summaryuser <String>]
def printShowFileShareCounts(users):
  def incrementCounter(counter):
    if not counterSet[counter]:
      userShareCounts[counter] += 1
      counterSet[counter] = True

  def showShareCounts(user, shareCounts, i, count):
    if summary != FILECOUNT_SUMMARY_NONE:
      if count != 0:
        for field, shareCount in shareCounts.items():
          summaryShareCounts[field] += shareCount
        if summary == FILECOUNT_SUMMARY_ONLY:
          return
    if not csvPF:
      printEntity([Ent.USER, user, Ent.DRIVE_FILE_OR_FOLDER, shareCounts[FILESHARECOUNTS_TOTAL]], i, count)
      Ind.Increment()
      for field, shareCount in shareCounts.items():
        printKeyValueList([field, shareCount])
      Ind.Decrement()
    else:
      row = {FILESHARECOUNTS_OWNER: user}
      row.update(shareCounts)
      csvPF.WriteRow(row)

  cd = buildGAPIObject(API.DIRECTORY)
  csvPF = CSVPrintFile([FILESHARECOUNTS_OWNER]+list(FILESHARECOUNTS_ZEROCOUNTS.keys())) if Act.csvFormat() else None
  query =  ME_IN_OWNERS
  summary = FILECOUNT_SUMMARY_NONE
  summaryUser = FILECOUNT_SUMMARY_USER
  fileIdEntity = {}
  internalDomains = 'all'
  while Cmd.ArgumentsRemaining():
    myarg = getArgument()
    if csvPF and myarg == 'todrive':
      csvPF.GetTodriveParameters()
    elif myarg == 'excludetrashed':
      query += ' and trashed=false'
    elif myarg == 'internaldomains':
      internalDomains = getString(Cmd.OB_DOMAIN_NAME_LIST).replace(',', ' ').lower()
    elif myarg == 'summary':
      summary = getChoice(FILECOUNT_SUMMARY_CHOICE_MAP, mapChoice=True)
    elif myarg == 'summaryuser':
      summaryUser = getString(Cmd.OB_STRING)
    else:
      unknownArgumentExit()
  internalDomains = _getMain().finalizeInternalDomains(cd, internalDomains)
  summaryShareCounts = FILESHARECOUNTS_ZEROCOUNTS.copy()
  i, count, users = getEntityArgument(users)
  for user in users:
    i += 1
    user, drive = _validateUserSharedDrive(user, i, count, fileIdEntity)
    if not drive:
      continue
    userShareCounts = FILESHARECOUNTS_ZEROCOUNTS.copy()
    gettingEntity = _getGettingEntity(user, fileIdEntity)
    printGettingAllEntityItemsForWhom(Ent.DRIVE_FILE_OR_FOLDER, gettingEntity, i, count, query=query)
    try:
      feed = yieldGAPIpages(drive.files(), 'list', 'files',
                            pageMessage=getPageMessageForWhom(),
                            throwReasons=GAPI.DRIVE_USER_THROW_REASONS,
                            retryReasons=[GAPI.UNKNOWN_ERROR],
                            q=query, fields='nextPageToken,files(permissions(type,role,emailAddress,domain,allowFileDiscovery,deleted))',
                            pageSize=GC.Values[GC.DRIVE_MAX_RESULTS])
      for files in  feed:
        for f_file in files:
          counterSet = {FILESHARECOUNTS_TOTAL: False, FILESHARECOUNTS_SHARED: False,
                        FILESHARECOUNTS_SHARED_EXTERNAL: False, FILESHARECOUNTS_SHARED_INTERNAL: False}
          for permission in f_file['permissions']:
            if permission['role'] == 'owner':
              incrementCounter(FILESHARECOUNTS_TOTAL)
            else:
              incrementCounter(FILESHARECOUNTS_SHARED)
              ptype = permission['type']
              if ptype == 'anyone':
                incrementCounter(FILESHARECOUNTS_SHARED_EXTERNAL)
                userShareCounts[FILESHARECOUNTS_CATEGORIES[ptype][not permission['allowFileDiscovery']]] += 1
              else:
                domain = permission.get('domain', '')
                if not domain and ptype in ['user', 'group']:
                  if permission.get('deleted', False):
                    userShareCounts[FILESHARECOUNTS_CATEGORIES['deleted'][ptype]] += 1
                    continue
                  emailAddress = permission['emailAddress']
                  domain = emailAddress[emailAddress.find('@')+1:]
                internal = domain in internalDomains
                incrementCounter([FILESHARECOUNTS_SHARED_EXTERNAL, FILESHARECOUNTS_SHARED_INTERNAL][internal])
                if ptype == 'domain':
                  userShareCounts[FILESHARECOUNTS_CATEGORIES[ptype][internal][not permission['allowFileDiscovery']]] +=1
                else: # group, user
                  userShareCounts[FILESHARECOUNTS_CATEGORIES[ptype][internal]] += 1
      showShareCounts(user, userShareCounts, i, count)
    except (GAPI.serviceNotAvailable, GAPI.authError, GAPI.domainPolicy) as e:
      userDriveServiceNotEnabledWarning(user, str(e), i, count)
      continue
  if summary != FILECOUNT_SUMMARY_NONE:
    showShareCounts(summaryUser, summaryShareCounts, 0, 0)
  if csvPF:
    csvPF.writeCSVfile('Drive File Share Counts')

FILETREE_FIELDS_CHOICE_MAP = {
  'explicitlytrashed': 'explicitlyTrashed',
  'filesize': 'size',
  'id': 'id',
  'mime': 'mimeType',
  'mimetype': 'mimeType',
  'owners': 'owners',
  'parents': 'parents',
  'size': 'size',
  'trashed': 'trashed',
  'webviewlink': 'webViewLink',
  }

FILETREE_FIELDS_PRINT_ORDER = ['id', 'parents', 'owners', 'mimeType', 'size', 'explicitlyTrashed', 'trashed', 'webViewLink']

# gam <UserTypeEntity> print filetree [todrive <ToDriveAttribute>*]
#	[select <DriveFileEntity> [selectsubquery <QueryDriveFile>] [depth <Number>]]
#	[anyowner|(showownedby any|me|others)]
#	[showmimetype [not] <MimeTypeList>] [showmimetype category <MimeTypeNameList>]
#	[sizefield quotabytesused|size] [minimumfilesize <Integer>] [maximumfilesize <Integer>]
#	[filenamematchpattern <REMatchPattern>]
#	<PermissionMatch>* [<PermissionMatchMode>] [<PermissionMatchAction>]
#	[excludetrashed]
#	[fields <FileTreeFieldNameList>]
#	(orderby <DriveFileOrderByFieldName> [ascending|descending])* [delimiter <Character>]
#	[noindent] [stripcrsfromname]
# gam <UserTypeEntity> show filetree
#	[select <DriveFileEntity> [selectsubquery <QueryDriveFile>] [depth <Number>]]
#	[anyowner|(showownedby any|me|others)]
#	[showmimetype [not] <MimeTypeList>] [showmimetype category <MimeTypeNameList>]
#	[sizefield quotabytesused|size] [minimumfilesize <Integer>] [maximumfilesize <Integer>]
#	[filenamematchpattern <REMatchPattern>]
#	<PermissionMatch>* [<PermissionMatchMode>] [<PermissionMatchAction>]
#	[excludetrashed]
#	[fields <FileTreeFieldNameList>]
#	(orderby <DriveFileOrderByFieldName> [ascending|descending])* [delimiter <Character>]
#	[stripcrsfromname]
def printShowFileTree(users):
  def _showFileInfo(fileEntry, depth, j=0, jcount=0):
    if not DLP.CheckExcludeTrashed(fileEntry):
      return
    if stripCRsFromName:
      fileEntry['name'] = _stripControlCharsFromName(fileEntry['name'])
    if not csvPF:
      fileInfoList = []
      for field in FILETREE_FIELDS_PRINT_ORDER:
        if showFields[field]:
          if field == 'parents':
            parents = fileEntry.get(field, [])
            fileInfoList.extend([field, f'{len(parents)} [{delimiter.join(parents)}]'])
          elif field == 'owners':
            owners = [owner['emailAddress'] for owner in fileEntry.get(field, [])]
            if owners:
              fileInfoList.extend([field, delimiter.join(owners)])
          elif field in {'explicitlyTrashed', 'trashed'}:
            trashed = fileEntry.get(field, False)
            if trashed:
              fileInfoList.extend([field, trashed])
          elif field == 'size':
            fileInfoList.extend([field, fileEntry.get(sizeField, 0)])
          else:
            fileInfoList.extend([field, fileEntry.get(field, '')])
      if fileInfoList:
        printKeyValueListWithCount([fileEntry['name'], formatKeyValueList('(', fileInfoList, ')')], j, jcount)
      else:
        printKeyValueList([fileEntry['name']])
    else:
      userInfo['index'] += 1
      row = userInfo.copy()
      row['depth'] = depth
      row['name'] = ('' if noindent else Ind.SpacesSub1())+fileEntry['name']
      for field in FILETREE_FIELDS_PRINT_ORDER:
        if showFields[field]:
          if field == 'parents':
            row[field] = delimiter.join(fileEntry.get(field, []))
          elif field == 'owners':
            row[field] = delimiter.join([owner['emailAddress'] for owner in fileEntry.get(field, [])])
          elif field == 'size':
            row['size'] = fileEntry.get(sizeField, 0)
          else:
            row[field] = fileEntry.get(field, '')
      csvPF.WriteRow(row)

  def _showDriveFolderContents(fileEntry, depth):
    for childId in fileEntry['children']:
      childEntry = fileTree.get(childId)
      if childEntry:
        if not DLP.CheckExcludeTrashed(childEntry['info']):
          continue
        if (DLP.CheckMimeType(childEntry['info']) and
            DLP.CheckFileSize(childEntry['info'], sizeField) and
            DLP.CheckFilenameMatch(childEntry['info']) and
            DLP.CheckFilePermissionMatches(childEntry['info'])):
          _showFileInfo(childEntry['info'], depth)
        if childEntry['info']['mimeType'] == MIMETYPE_GA_FOLDER and (maxdepth == -1 or depth < maxdepth):
          Ind.Increment()
          _showDriveFolderContents(childEntry, depth+1)
          Ind.Decrement()

  def _showChildDriveFolderContents(drive, fileEntry, user, i, count, depth):
    if not DLP.CheckExcludeTrashed(fileEntry):
      return
    q = _getMain().WITH_PARENTS.format(fileEntry['id'])
    if selectSubQuery:
      q += ' and ('+selectSubQuery+')'
    try:
      children = callGAPIpages(drive.files(), 'list', 'files',
                               throwReasons=GAPI.DRIVE_USER_THROW_REASONS+[GAPI.INVALID_QUERY, GAPI.INVALID],
                               retryReasons=[GAPI.UNKNOWN_ERROR],
                               q=q, orderBy=OBY.orderBy, fields=pagesFields,
                               pageSize=GC.Values[GC.DRIVE_MAX_RESULTS], supportsAllDrives=True, includeItemsFromAllDrives=True)
    except (GAPI.invalidQuery, GAPI.invalid):
      entityActionFailedWarning([Ent.USER, user, Ent.DRIVE_FILE, None], invalidQuery(selectSubQuery), i, count)
      return
    except (GAPI.serviceNotAvailable, GAPI.authError, GAPI.domainPolicy) as e:
      userDriveServiceNotEnabledWarning(user, str(e), i, count)
      return
    for childEntryInfo in children:
      if not DLP.CheckExcludeTrashed(childEntryInfo):
        continue
      if (DLP.CheckShowOwnedBy(childEntryInfo) and
          DLP.CheckMimeType(childEntryInfo) and
          DLP.CheckFileSize(childEntryInfo, sizeField) and
          DLP.CheckFilenameMatch(childEntryInfo) and
          DLP.CheckFilePermissionMatches(childEntryInfo)):
        _showFileInfo(childEntryInfo, depth)
      if childEntryInfo['mimeType'] == MIMETYPE_GA_FOLDER and (maxdepth == -1 or depth < maxdepth):
        Ind.Increment()
        _showChildDriveFolderContents(drive, childEntryInfo, user, i, count, depth+1)
        Ind.Decrement()

  csvPF = CSVPrintFile(['User', 'index', 'depth', 'name']) if Act.csvFormat() else None
  maxdepth = -1
  fileIdEntity = {}
  selectSubQuery = ''
  sizeField = 'quotaBytesUsed'
  showFields = {}
  for mappedField in FILETREE_FIELDS_CHOICE_MAP.values():
    showFields[mappedField] = False
  buildTree = noindent = stripCRsFromName = False
  delimiter = GC.Values[GC.CSV_OUTPUT_FIELD_DELIMITER]
  OBY = OrderBy(DRIVEFILE_ORDERBY_CHOICE_MAP)
  DLP = DriveListParameters({'allowChoose': False, 'allowCorpora': False, 'allowQuery': False, 'mimeTypeInQuery': False})
  while Cmd.ArgumentsRemaining():
    myarg = getArgument()
    if csvPF and myarg == 'todrive':
      csvPF.GetTodriveParameters()
    elif DLP.ProcessArgument(myarg, fileIdEntity):
      pass
    elif myarg == 'select':
      if fileIdEntity:
        usageErrorExit(Msg.CAN_NOT_BE_SPECIFIED_MORE_THAN_ONCE.format('select'))
      fileIdEntity = getDriveFileEntity(DLP=DLP)
    elif myarg == 'selectsubquery':
      selectSubQuery = getString(Cmd.OB_QUERY, minLen=0)
    elif myarg == 'orderby':
      OBY.GetChoice()
    elif myarg == 'depth':
      maxdepth = getInteger(minVal=-1)
    elif myarg == 'sizefield':
      sizeField = getChoice(SIZE_FIELD_CHOICE_MAP, mapChoice=True)
    elif myarg == 'fields':
      for field in _getFieldsList():
        if field in FILETREE_FIELDS_CHOICE_MAP:
          showFields[FILETREE_FIELDS_CHOICE_MAP[field]] = True
          if csvPF:
            csvPF.AddTitle(FILETREE_FIELDS_CHOICE_MAP[field])
        else:
          invalidChoiceExit(field, FILETREE_FIELDS_CHOICE_MAP, True)
    elif myarg == 'delimiter':
      delimiter = getCharacter()
    elif csvPF and myarg == 'noindent':
      noindent = True
    elif myarg == 'stripcrsfromname':
      stripCRsFromName = True
    else:
      unknownArgumentExit()
  fieldsList = ['driveId', 'id', 'name', 'parents', 'mimeType', 'ownedByMe', 'owners(emailAddress)',
                'shared', sizeField, 'explicitlyTrashed', 'trashed', 'webViewLink']
  buildTree = (not fileIdEntity
               or (not fileIdEntity['dict']
                   and not fileIdEntity['query']
                   and not fileIdEntity['shareddrivefilequery']
                   and _simpleFileIdEntityList(fileIdEntity['list'])))
  if buildTree:
    if not fileIdEntity:
      fileIdEntity = initDriveFileEntity()
      DLP.GetFileIdEntity()
    if not fileIdEntity.get('shareddrive'):
      btkwargs = DLP.kwargs
      btkwargs['q'] = DLP.fileIdEntity['query']
      cleanFileIDsList(fileIdEntity, [ROOT, ORPHANS])
    else:
      btkwargs = fileIdEntity['shareddrive']
    DLP.Finalize(fileIdEntity)
  elif not fileIdEntity:
    fileIdEntity = initDriveFileEntity()
  if DLP.PM.permissionMatches:
    fieldsList.append('permissions')
  fields = getFieldsFromFieldsList(fieldsList)
  pagesFields = getItemFieldsFromFieldsList('files', fieldsList)
  shareddriveFields = []
  i, count, users = getEntityArgument(users)
  for user in users:
    i += 1
    origUser = user
    user, drive = _validateUserSharedDrive(user, i, count, fileIdEntity)
    if not drive:
      continue
    if buildTree:
      fileTree, status = initFileTree(drive, fileIdEntity.get('shareddrive'), DLP, shareddriveFields, True, user, i, count)
      if not status:
        continue
      gettingEntity = _getGettingEntity(user, fileIdEntity)
      printGettingAllEntityItemsForWhom(Ent.DRIVE_FILE_OR_FOLDER, gettingEntity, i, count, query=DLP.fileIdEntity['query'])
      try:
        feed = yieldGAPIpages(drive.files(), 'list', 'files',
                              pageMessage=getPageMessageForWhom(),
                              throwReasons=GAPI.DRIVE_USER_THROW_REASONS+[GAPI.NOT_FOUND, GAPI.TEAMDRIVE_MEMBERSHIP_REQUIRED],
                              retryReasons=[GAPI.UNKNOWN_ERROR],
                              orderBy=OBY.orderBy,
                              fields=pagesFields, pageSize=GC.Values[GC.DRIVE_MAX_RESULTS], **btkwargs)
        for files in feed:
          extendFileTree(fileTree, files, DLP, stripCRsFromName)
        extendFileTreeParents(drive, fileTree, fields)
        DLP.GetLocationFileIdsFromTree(fileTree, fileIdEntity)
      except (GAPI.notFound, GAPI.teamDriveMembershipRequired) as e:
        entityActionFailedWarning([Ent.USER, user, Ent.SHAREDDRIVE_ID, fileIdEntity['shareddrive']['driveId']], str(e), i, count)
        continue
      except (GAPI.serviceNotAvailable, GAPI.authError, GAPI.domainPolicy) as e:
        userDriveServiceNotEnabledWarning(user, str(e), i, count)
        continue
    else:
      fileTree = {}
    user, drive, jcount = _validateUserGetFileIDs(origUser, i, count, fileIdEntity, drive=drive, entityType=Ent.DRIVE_FILE_OR_FOLDER)
    if jcount == 0:
      continue
    if csvPF:
      userInfo = {'User': user, 'index': 0, 'depth': 0, 'name': ''}
    j = 0
    Ind.Increment()
    for fileId in fileIdEntity['list']:
      j += 1
      fileEntry = fileTree.get(fileId)
      if fileEntry:
        fileEntryInfo = fileEntry['info']
      else:
        try:
          fileEntryInfo = callGAPI(drive.files(), 'get',
                                   throwReasons=GAPI.DRIVE_GET_THROW_REASONS,
                                   fileId=fileId, fields=fields, supportsAllDrives=True)
          if (fileEntryInfo['mimeType'] == MIMETYPE_GA_FOLDER and fileEntryInfo.get('driveId') and
              fileEntryInfo['name'] == TEAM_DRIVE and not fileEntryInfo.get('parents', [])):
            fileEntryInfo['name'] = f"{SHARED_DRIVES}/{_getSharedDriveNameFromId(drive, fileId)}"
          if stripCRsFromName:
            fileEntryInfo['name'] = _stripControlCharsFromName(fileEntryInfo['name'])
          if buildTree:
            fileTree[fileId] = {'info': fileEntryInfo}
        except GAPI.fileNotFound:
          entityActionFailedWarning([Ent.USER, user, Ent.DRIVE_FILE_OR_FOLDER, fileId], Msg.NOT_FOUND, j, jcount)
          continue
        except (GAPI.notFound, GAPI.teamDriveMembershipRequired) as e:
          entityActionFailedWarning([Ent.USER, user, Ent.SHAREDDRIVE_ID, fileIdEntity['shareddrive']['driveId']], str(e), j, jcount)
          continue
        except (GAPI.serviceNotAvailable, GAPI.authError, GAPI.domainPolicy) as e:
          userDriveServiceNotEnabledWarning(user, str(e), i, count)
          break
      _showFileInfo(fileEntryInfo, -1, j, jcount)
      Ind.Increment()
      if buildTree:
        _showDriveFolderContents(fileEntry, 0)
      else:
        _showChildDriveFolderContents(drive, fileEntryInfo, user, i, count, 0)
      Ind.Decrement()
    Ind.Decrement()
  if csvPF:
    csvPF.writeCSVfile('Drive File Tree')

def getCreationModificationTimes(path_to_file):
  """
  Try to get the date that a file was created, falling back to when it was
  last modified if that isn't possible.
  See http://stackoverflow.com/a/39501288/1709587 for explanation.
  """
  mtime = os.path.getmtime(path_to_file)
  if platform.system() == 'Windows':
    ctime = os.path.getctime(path_to_file)
  else:
    stat = os.stat(path_to_file)
    try:
      ctime = stat.st_birthtime
    except AttributeError:
      # We're probably on Linux. No easy way to get creation dates here,
      # so we'll settle for when its content was last modified.
      ctime = stat.st_mtime
  return (formatLocalSecondsTimestamp(ctime), formatLocalSecondsTimestamp(mtime))

def writeReturnIdLink(returnIdLink, mimeType, result):
  if returnIdLink != 'editLink':
    writeStdout(f'{result[returnIdLink]}\n')
    return
  if mimeType is None:
    writeStdout(f'{result["webViewLink"]}\n')
    return
  for mt in MICROSOFT_FORMATS_LIST:
    if mimeType == mt['mime']:
      if mt['ext'][1] == 'd':
        writeStdout(f'https://docs.google.com/document/d/{result["id"]}/edit\n')
        return
      if mt['ext'][1] == 'x':
        writeStdout(f'https://docs.google.com/spreadsheets/d/{result["id"]}/edit\n')
        return
      if mt['ext'][1] == 'p':
        writeStdout(f'https://docs.google.com/presentation/d/{result["id"]}/edit\n')
        return
  writeStdout(f'https://drive.google.com/file/d/{result["id"]}/edit\n')

