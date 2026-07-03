"""File creation, update, shortcuts.

Part of the drive sub-package, extracted from drive.py."""

"""GAM Google Drive file, permission, shared drive, and label management."""

import re
import sys

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

def processFilenameReplacements(name, replacements):
  for replacement in replacements:
    name = re.sub(replacement[0], replacement[1], name)
  return name

def addTimestampToFilename(parameters, body):
  tdtime = arrow.now(GC.Values[GC.TIMEZONE])
  body['name'] += ' - '
  if not parameters[DFA_TIMEFORMAT]:
    body['name'] += _getMain().ISOformatTimeStamp(tdtime)
  else:
    body['name'] += tdtime.strftime(parameters[DFA_TIMEFORMAT])

createReturnItemMap = {
  'returnidonly': 'id',
  'returnlinkonly': 'webViewLink',
  'returneditlinkonly': 'editLink'
  }

# gam <UserTypeEntity> create drivefile
#	[(localfile <FileName>|-)|(url <URL>)]
#	[(drivefilename|newfilename <DriveFileName>) | (replacefilename <REMatchPattern> <RESubstitution>)*]
#	[stripnameprefix <String>]
#	[timestamp <Boolean>]] [timeformat <DateTimeFormat>]
#	<DriveFileCreateAttribute>* [noduplicate]
#	[(csv [todrive <ToDriveAttribute>*] (addcsvdata <FieldName> <String>)*)) |
#	 (returnidonly|returnlinkonly|returneditlinkonly|showdetails)]
def createDriveFile(users):
  csvPF = media_body = None
  addCSVData = {}
  returnIdLink = None
  noDuplicate = showDetails = False
  body = {}
  newName = None
  assignLocalName = True
  parameters = initDriveFileAttributes()
  while Cmd.ArgumentsRemaining():
    myarg = _getMain().getArgument()
    if myarg in {'drivefilename', 'newfilename'}:
      newName = _getMain().getString(Cmd.OB_DRIVE_FILE_NAME)
      assignLocalName = False
    elif myarg in createReturnItemMap:
      returnIdLink = createReturnItemMap[myarg]
      showDetails = False
    elif myarg == 'showdetails':
      returnIdLink = None
      showDetails = True
    elif myarg == 'noduplicate':
      noDuplicate = True
    elif myarg == 'csv':
      csvPF = _getMain().CSVPrintFile()
    elif csvPF and myarg == 'todrive':
      csvPF.GetTodriveParameters()
    elif csvPF and myarg == 'addcsvdata':
      _getMain().getAddCSVData(addCSVData)
    else:
      getDriveFileAttribute(myarg, body, parameters, False)
  if assignLocalName and parameters[DFA_LOCALFILENAME] and parameters[DFA_LOCALFILENAME] != '-':
    newName = parameters[DFA_LOCALFILENAME]
  if newName:
    if parameters[DFA_STRIPNAMEPREFIX] and newName.startswith(parameters[DFA_STRIPNAMEPREFIX]):
      newName = newName[len(parameters[DFA_STRIPNAMEPREFIX]):]
    if parameters[DFA_REPLACEFILENAME]:
      body['name'] = processFilenameReplacements(newName, parameters[DFA_REPLACEFILENAME])
    else:
      body['name'] = newName
  else:
    body['name'] = 'Untitled'
  if parameters[DFA_TIMESTAMP]:
    addTimestampToFilename(parameters, body)
  if parameters[DFA_LOCALFILEPATH]:
    if parameters[DFA_LOCALFILEPATH] != '-' and parameters[DFA_PRESERVE_FILE_TIMES]:
      setPreservedFileTimes(body, parameters, False)
    if body.get('mimeType') == MIMETYPE_GA_SCRIPT_JSON:
      parameters[DFA_LOCALMIMETYPE] = body['mimeType']
    media_body = getMediaBody(parameters)
  elif parameters[DFA_URL]:
    media_body = getMediaBody(parameters)
    body['mimeType'] = parameters[DFA_LOCALMIMETYPE]
  if csvPF:
    csvPF.SetTitles(['User', 'name', 'id'])
    if showDetails:
      csvPF.AddTitles(['parentId', 'mimeType'])
    if addCSVData:
      csvPF.AddTitles(sorted(addCSVData.keys()))
  Act.Set(Act.CREATE)
  i, count, users = _getMain().getEntityArgument(users)
  for user in users:
    i += 1
    user, drive = _getMain().buildGAPIServiceObject(API.DRIVE3, user, i, count)
    if not drive:
      continue
    if not _getDriveFileParentInfo(drive, user, i, count, body, parameters):
      continue
    entityType = _getMain()._getEntityMimeType(body) if 'mimeType' in body else Ent.DRIVE_FILE
    try:
      if noDuplicate:
        # Check for existing file/folder, do not duplicate
        files = _getMain().callGAPIitems(drive.files(), 'list', 'files',
                              throwReasons=GAPI.DRIVE_USER_THROW_REASONS+[GAPI.INVALID_QUERY, GAPI.INVALID],
                              q=f"name = '{escapeDriveFileName(body['name'])}'and '{body['parents'][0]}' in parents and trashed = false",
                              fields='files(id)', **parameters['searchargs'])
        if files:
          _getMain().entityActionNotPerformedWarning([Ent.USER, user, entityType, body['name'], Ent.DRIVE_PARENT_FOLDER_ID, body['parents'][0]],
                                          f"{Msg.DUPLICATE} IDs {','.join([file['id'] for file in files])}", i, count)
          continue
      result = _getMain().callGAPI(drive.files(), 'create',
                        throwReasons=GAPI.DRIVE_USER_THROW_REASONS+[GAPI.FORBIDDEN, GAPI.INSUFFICIENT_PERMISSIONS, GAPI.INSUFFICIENT_PARENT_PERMISSIONS,
                                                                    GAPI.PERMISSION_DENIED, GAPI.INVALID, GAPI.BAD_REQUEST, GAPI.CANNOT_ADD_PARENT,
                                                                    GAPI.FILE_NOT_FOUND, GAPI.UNKNOWN_ERROR, GAPI.INTERNAL_ERROR,
                                                                    GAPI.STORAGE_QUOTA_EXCEEDED, GAPI.TEAMDRIVES_SHARING_RESTRICTION_NOT_ALLOWED,
                                                                    GAPI.TEAMDRIVE_FILE_LIMIT_EXCEEDED, GAPI.TEAMDRIVE_HIERARCHY_TOO_DEEP,
                                                                    GAPI.UPLOAD_TOO_LARGE, GAPI.TEAMDRIVES_SHORTCUT_FILE_NOT_SUPPORTED],
                        ocrLanguage=parameters[DFA_OCRLANGUAGE],
                        ignoreDefaultVisibility=parameters[DFA_IGNORE_DEFAULT_VISIBILITY],
                        keepRevisionForever=parameters[DFA_KEEP_REVISION_FOREVER],
                        useContentAsIndexableText=parameters[DFA_USE_CONTENT_AS_INDEXABLE_TEXT],
                        media_body=media_body, body=body, fields='id,name,mimeType,parents,webViewLink', supportsAllDrives=True)
      parentId = result['parents'][0] if 'parents' in result and result['parents'] else _getMain().UNKNOWN
      if returnIdLink:
        writeReturnIdLink(returnIdLink, parameters[DFA_LOCALMIMETYPE], result)
      elif not csvPF:
        kvList = [Ent.USER, user]
        if not showDetails:
          titleInfo = f'{result["name"]}({result["id"]})'
          if parameters[DFA_LOCALFILENAME]:
            kvList.extend([Ent.DRIVE_FILE, titleInfo])
          else:
            kvList.extend([_getMain()._getEntityMimeType(result), titleInfo])
        else:
          if result['mimeType'] != MIMETYPE_GA_FOLDER:
            kvList.extend([Ent.DRIVE_FILE, result['name'], Ent.DRIVE_FILE_ID, result['id']])
          else:
            kvList.extend([Ent.DRIVE_FOLDER, result['name'], Ent.DRIVE_FOLDER_ID, result['id']])
          kvList.extend([Ent.DRIVE_PARENT_FOLDER_ID, parentId, Ent.MIMETYPE, result['mimeType']])
        if media_body:
          _getMain().entityModifierNewValueActionPerformed(kvList, Act.MODIFIER_WITH_CONTENT_FROM, parameters[DFA_LOCALFILENAME] or parameters[DFA_URL], i, count)
        else:
          _getMain().entityActionPerformed(kvList, i, count)
      else:
        row = {'User': user, 'name': result['name'], 'id': result['id']}
        if showDetails:
          row.update({'parentId': parentId, 'mimeType': result['mimeType']})
        if addCSVData:
          row.update(addCSVData)
        csvPF.WriteRow(row)
    except (GAPI.forbidden, GAPI.insufficientFilePermissions, GAPI.insufficientParentPermissions,
            GAPI.invalidQuery, GAPI.permissionDenied, GAPI.invalid, GAPI.badRequest, GAPI.cannotAddParent,
            GAPI.fileNotFound, GAPI.unknownError, GAPI.storageQuotaExceeded, GAPI.teamDrivesSharingRestrictionNotAllowed,
            GAPI.teamDriveFileLimitExceeded, GAPI.teamDriveHierarchyTooDeep,
            GAPI.uploadTooLarge, GAPI.teamDrivesShortcutFileNotSupported) as e:
      _getMain().entityActionFailedWarning([Ent.USER, user, entityType, body['name']], str(e), i, count)
    except (GAPI.serviceNotAvailable, GAPI.authError, GAPI.domainPolicy) as e:
      _getMain().userDriveServiceNotEnabledWarning(user, str(e), i, count)
  if csvPF:
    csvPF.writeCSVfile('Files')

# gam <UserTypeEntity> create drivefolderpath
#	[pathdelimiter <Character>]
#	((fullpath <DriveFolderPath) |
#	 (path <DriveFolderPath [<DriveFileParentAttribute>]) |
#	 (list <DriveFolderNameList>) [<DriveFileParentAttribute>]))
#	[(csv [todrive <ToDriveAttribute>*] (addcsvdata <FieldName> <String>)*) |
#	 returnidonly]
def createDriveFolderPath(users):
  csvPF = None
  addCSVData = {}
  fullPath = parentSpecified = returnIdOnly = False
  parentBody = {}
  parentParms = initDriveFileAttributes()
  driveFolderNameList = []
  pathDelimiter = '/'
  while Cmd.ArgumentsRemaining():
    myarg = _getMain().getArgument()
    if myarg == 'pathdelimiter':
      pathDelimiter = _getMain().getCharacter()
    elif myarg == 'fullpath':
      folderPathLocation = Cmd.Location()
      driveFolderNameList = _getMain().getString(Cmd.OB_DRIVE_FOLDER_PATH).lstrip(pathDelimiter).strip(' ').split(pathDelimiter)
      if len(driveFolderNameList) > 0:
        if driveFolderNameList[0].lower() == _getMain().MY_DRIVE.lower():
          parentParms[DFA_PARENTID] = ROOT
          driveFolderNameList = driveFolderNameList[1:]
        elif driveFolderNameList[0].lower() == SHARED_DRIVES.lower() and len(driveFolderNameList) > 1:
          parentParms[DFA_SHAREDDRIVE_PARENT] = driveFolderNameList[1]
          driveFolderNameList = driveFolderNameList[2:]
        else:
          _getMain().usageErrorExit(Msg.FULL_PATH_MUST_START_WITH_DRIVE.format(_getMain().MY_DRIVE, f'{SHARED_DRIVES}{pathDelimiter}<SharedDriveName>'))
        fullPath = True
    elif myarg == 'path':
      folderPathLocation = Cmd.Location()
      driveFolderNameList = _getMain().getString(Cmd.OB_DRIVE_FOLDER_PATH).strip(' ').split(pathDelimiter)
    elif myarg == 'list':
      folderPathLocation = Cmd.Location()
      driveFolderNameList = _getMain().shlexSplitList(_getMain().getString(Cmd.OB_DRIVE_FOLDER_NAME_LIST), dataDelimiter=',')
    elif getDriveFileParentAttribute(myarg, parentParms):
      parentSpecified = True
    elif myarg == 'returnidonly':
      returnIdOnly = True
    elif myarg == 'csv':
      csvPF = _getMain().CSVPrintFile(['User', 'name', 'id', 'status', 'pathIndex', 'pathLength'], 'sortall')
    elif csvPF and myarg == 'todrive':
      csvPF.GetTodriveParameters()
    elif csvPF and myarg == 'addcsvdata':
      _getMain().getAddCSVData(addCSVData)
    else:
      _getMain().unknownArgumentExit()
  if not driveFolderNameList:
    Cmd.SetLocation(folderPathLocation)
    _getMain().emptyArgumentExit('fullpath|path|list')
  if fullPath and parentSpecified:
    _getMain().usageErrorExit(Msg.ARE_MUTUALLY_EXCLUSIVE.format('fullpath', '<DriveFileParentAttribute>'))
  for folderName in driveFolderNameList:
    if not folderName.strip():
      Cmd.SetLocation(folderPathLocation)
      _getMain().usageErrorExit(Msg.ALL_FOLDER_NAMES_MUST_BE_NON_BLANK.format(driveFolderNameList))
  if csvPF:
    if addCSVData:
      csvPF.AddTitles(sorted(addCSVData.keys()))
  i, count, users = _getMain().getEntityArgument(users)
  for user in users:
    i += 1
    user, drive = _getMain().buildGAPIServiceObject(API.DRIVE3, user, i, count)
    if not drive:
      continue
    if not _getDriveFileParentInfo(drive, user, i, count, parentBody, parentParms,
                                   defaultToRoot=True, entityType=Ent.DRIVE_FOLDER):
      continue
    parentId = parentBody['parents'][0]
    if parentParms.get('searchargs', {}).get('corpora', ''):
      query = _getMain().ANY_NON_TRASHED_FOLDER_NAME_WITH_PARENTS
    else:
      query = _getMain().MY_NON_TRASHED_FOLDER_NAME_WITH_PARENTS
    errors = False
    createOnly = False
    if not returnIdOnly and not csvPF:
      _getMain().entityPerformAction([Ent.USER, user, Ent.DRIVE_FOLDER_PATH, ''], i, count)
    jcount = len(driveFolderNameList)
    Ind.Increment()
    j = 0
    for folderName in driveFolderNameList:
      j += 1
      try:
        folderFound = False
        if not createOnly:
          op = 'Find Folder'
          result = _getMain().callGAPIpages(drive.files(), 'list', 'files',
                                 throwReasons=GAPI.DRIVE_USER_THROW_REASONS+[GAPI.BAD_REQUEST, GAPI.INSUFFICIENT_PERMISSIONS],
                                 retryReasons=[GAPI.UNKNOWN_ERROR],
                                 q=query.format(escapeDriveFileName(folderName), parentId),
                                 supportsAllDrives=True, includeItemsFromAllDrives=True,
                                 fields='nextPageToken,files(id,name)')
          if result:
            if len(result) > 1:
              _getMain().entityActionFailedWarning([Ent.USER, user, Ent.DRIVE_FOLDER, folderName], f'{op}: {len(result)} Folders with same name')
              errors = True
              break
            parentId = result[0]['id']
            parentName = result[0]['name']
            folderFound = True
            Act.Set(Act.EXISTS)
        if not folderFound:
          op = 'Create Folder'
          result = _getMain().callGAPI(drive.files(), 'create',
                            throwReasons=GAPI.DRIVE_USER_THROW_REASONS+[GAPI.FORBIDDEN, GAPI.INSUFFICIENT_PERMISSIONS, GAPI.INSUFFICIENT_PARENT_PERMISSIONS,
                                                                        GAPI.UNKNOWN_ERROR, GAPI.BAD_REQUEST,
                                                                        GAPI.STORAGE_QUOTA_EXCEEDED, GAPI.TEAMDRIVE_FILE_LIMIT_EXCEEDED, GAPI.TEAMDRIVE_HIERARCHY_TOO_DEEP],
                            body={'parents': [parentId], 'name': folderName, 'mimeType': MIMETYPE_GA_FOLDER}, fields='id,name', supportsAllDrives=True)
          parentId = result['id']
          parentName = result['name']
          createOnly = True
          Act.Set(Act.CREATE)
      except (GAPI.forbidden, GAPI.insufficientPermissions, GAPI.insufficientParentPermissions,
              GAPI.unknownError, GAPI.badRequest, GAPI.storageQuotaExceeded, GAPI.teamDriveFileLimitExceeded, GAPI.teamDriveHierarchyTooDeep) as e:
        _getMain().entityActionFailedWarning([Ent.USER, user, Ent.DRIVE_FOLDER, folderName], f'{op}: {str(e)}', j, jcount)
        errors = True
        break
      except (GAPI.serviceNotAvailable, GAPI.authError, GAPI.domainPolicy) as e:
        _getMain().userDriveServiceNotEnabledWarning(user, str(e), i, count)
        errors = True
        break
      if not returnIdOnly:
        if not csvPF:
          _getMain().entityActionPerformed([Ent.USER, user, Ent.DRIVE_FOLDER_NAME, f'{parentName}({parentId})'],
                                j, jcount)
        else:
          row = {'User': user, 'name': parentName, 'id': parentId, 'status': Act.Performed(), 'pathIndex': j, 'pathLength': jcount}
          if addCSVData:
            row.update(addCSVData)
          csvPF.WriteRow(row)
    if returnIdOnly and not errors:
      _getMain().writeStdout(f'{parentId}\n')
    Ind.Decrement()
  if csvPF:
    csvPF.writeCSVfile('Folders')

# gam <UserTypeEntity> create drivefileshortcut <DriveFileEntity> [shortcutname <String>]
#	[<DriveFileParentAttribute>|convertparents]
#	[(csv [todrive <ToDriveAttribute>*]) | returnidonly]
def createDriveFileShortcut(users):
  csvPF = baseShortcutName = None
  convertParents = newParentsSpecified = returnIdOnly = False
  fileIdEntity = getDriveFileEntity()
  parentBody = {}
  parentParms = initDriveFileAttributes()
  while Cmd.ArgumentsRemaining():
    myarg = _getMain().getArgument()
    if myarg == 'shortcutname':
      baseShortcutName = _getMain().getString(Cmd.OB_DRIVE_FILE_NAME)
    elif myarg == 'returnidonly':
      returnIdOnly = True
    elif myarg == 'csv':
      csvPF = _getMain().CSVPrintFile(['User', 'name', 'id', 'targetName', 'targetId'], 'sortall')
    elif csvPF and myarg == 'todrive':
      csvPF.GetTodriveParameters()
    elif getDriveFileParentAttribute(myarg, parentParms):
      if convertParents:
        _getMain().usageErrorExit(Msg.ARE_MUTUALLY_EXCLUSIVE.format(myarg, 'convertparents'))
      newParentsSpecified = True
    elif myarg == 'convertparents':
      if newParentsSpecified:
        _getMain().usageErrorExit(Msg.ARE_MUTUALLY_EXCLUSIVE.format(myarg, '<DriveFileParentAttribute>'))
      convertParents = True
    else:
      _getMain().unknownArgumentExit()
  if fileIdEntity['query']:
    fileIdEntity['query'] = fileIdEntity['query']+_getMain().AND_NOT_SHORTCUT
  elif fileIdEntity['shareddrivefilequery']:
    fileIdEntity['shareddrivefilequery'] = fileIdEntity['shareddrivefilequery']+_getMain().AND_NOT_SHORTCUT
  i, count, users = _getMain().getEntityArgument(users)
  for user in users:
    i += 1
    user, drive, jcount = _validateUserGetFileIDs(user, i, count, fileIdEntity)
    if not returnIdOnly and not csvPF:
      _getMain().entityPerformActionSubItemModifierNumItems([Ent.USER, user], Ent.DRIVE_FILE_SHORTCUT,
                                                 Act.MODIFIER_FOR, jcount, Ent.DRIVE_FILE_OR_FOLDER, i, count)
    if jcount == 0:
      continue
    if not _getDriveFileParentInfo(drive, user, i, count, parentBody, parentParms):
      continue
    if newParentsSpecified:
      newParents = parentBody['parents']
      numNewParents = len(newParents)
    elif not convertParents:
      try:
        rootFolderId = _getMain().callGAPI(drive.files(), 'get',
                                throwReasons=GAPI.DRIVE_USER_THROW_REASONS,
                                fileId=ROOT, fields='id')['id']
      except (GAPI.serviceNotAvailable, GAPI.authError, GAPI.domainPolicy) as e:
        _getMain().userDriveServiceNotEnabledWarning(user, str(e), i, count)
        continue
      newParents = [rootFolderId]
      numNewParents = 1
    Ind.Increment()
    j = 0
    for fileId in fileIdEntity['list']:
      j += 1
      Act.Set(Act.CREATE)
      try:
        target = _getMain().callGAPI(drive.files(), 'get',
                          throwReasons=GAPI.DRIVE_GET_THROW_REASONS,
                          fileId=fileId, fields='mimeType,name,parents', supportsAllDrives=True)
      except (GAPI.forbidden, GAPI.insufficientFilePermissions, GAPI.invalid, GAPI.badRequest,
              GAPI.fileNotFound, GAPI.unknownError, GAPI.teamDrivesSharingRestrictionNotAllowed) as e:
        _getMain().entityActionFailedWarning([Ent.USER, user, Ent.DRIVE_FILE_OR_FOLDER, fileId], str(e), j, jcount)
        continue
      except (GAPI.serviceNotAvailable, GAPI.authError, GAPI.domainPolicy) as e:
        _getMain().userDriveServiceNotEnabledWarning(user, str(e), i, count)
        break
      targetName = target['name']
      if baseShortcutName:
        shortcutName = baseShortcutName.replace('#filename#', targetName)
      else:
        shortcutName = targetName
      targetEntityType = _getMain()._getEntityMimeType(target)
      if convertParents:
        newParents = target.get('parents', [])[:-1]
        numNewParents = len(newParents)
        if numNewParents <= 1:
          _getMain().entityActionNotPerformedWarning([Ent.USER, user, targetEntityType, targetName, Ent.DRIVE_FILE_SHORTCUT, None],
                                          Msg.NO_PARENTS_TO_CONVERT_TO_SHORTCUTS, j, jcount)
          continue
      removeParents = []
      body = {'name': shortcutName, 'mimeType': MIMETYPE_GA_SHORTCUT, 'parents': None, 'shortcutDetails': {'targetId': fileId}}
      if not returnIdOnly and not csvPF:
        _getMain().entityPerformActionNumItems([Ent.USER, user, targetEntityType, targetName], numNewParents, Ent.DRIVE_FILE_SHORTCUT, j, jcount)
      try:
        existingShortcuts = _getMain().callGAPI(drive.files(), 'list',
                                     throwReasons=GAPI.DRIVE_USER_THROW_REASONS+[GAPI.INVALID_QUERY, GAPI.INVALID],
                                     retryReasons=[GAPI.UNKNOWN_ERROR],
                                     supportsAllDrives=True, includeItemsFromAllDrives=True,
                                     q=f"shortcutDetails.targetId = '{fileId}' and trashed = False", fields='files(id,name,parents)')['files']
      except (GAPI.invalidQuery, GAPI.invalid, GAPI.serviceNotAvailable, GAPI.authError, GAPI.domainPolicy):
        existingShortcuts = []
      Ind.Increment()
      k = 0
      for parentId in newParents:
        k += 1
        duplicateShortcut = False
        for shortcut in existingShortcuts:
          if parentId in shortcut['parents'] and shortcutName == shortcut['name']:
            _getMain().entityActionNotPerformedWarning([Ent.USER, user, targetEntityType, targetName, Ent.DRIVE_FILE_SHORTCUT, f'{shortcut["name"]}({shortcut["id"]})'],
                                            Msg.DUPLICATE, k, numNewParents)
            duplicateShortcut = True
            break
        if duplicateShortcut:
          continue
        body['parents'] = [parentId]
        try:
          result = _getMain().callGAPI(drive.files(), 'create',
                            throwReasons=GAPI.DRIVE_USER_THROW_REASONS+[GAPI.FORBIDDEN, GAPI.INSUFFICIENT_PERMISSIONS, GAPI.INSUFFICIENT_PARENT_PERMISSIONS,
                                                                        GAPI.INVALID, GAPI.BAD_REQUEST, GAPI.FILE_NOT_FOUND, GAPI.UNKNOWN_ERROR,
                                                                        GAPI.STORAGE_QUOTA_EXCEEDED, GAPI.TEAMDRIVES_SHARING_RESTRICTION_NOT_ALLOWED,
                                                                        GAPI.TEAMDRIVE_FILE_LIMIT_EXCEEDED, GAPI.TEAMDRIVE_HIERARCHY_TOO_DEEP,
                                                                        GAPI.SHORTCUT_TARGET_INVALID],
                            body=body, fields='id,name', supportsAllDrives=True)
          removeParents.append(parentId)
          if returnIdOnly:
            _getMain().writeStdout(f'{result["id"]}\n')
          elif not csvPF:
            _getMain().entityActionPerformed([Ent.USER, user, targetEntityType, targetName, Ent.DRIVE_FILE_SHORTCUT, f'{result["name"]}({result["id"]})'],
                                  k, numNewParents)
          else:
            csvPF.WriteRow({'User': user, 'name': result['name'], 'id': result['id'], 'targetName': targetName, 'targetId': fileId})
        except (GAPI.forbidden, GAPI.insufficientFilePermissions, GAPI.insufficientParentPermissions, GAPI.invalid, GAPI.badRequest,
                GAPI.fileNotFound, GAPI.unknownError, GAPI.storageQuotaExceeded, GAPI.teamDrivesSharingRestrictionNotAllowed,
                GAPI.teamDriveFileLimitExceeded, GAPI.teamDriveHierarchyTooDeep, GAPI.shortcutTargetInvalid) as e:
          _getMain().entityActionFailedWarning([Ent.USER, user, targetEntityType, targetName, Ent.DRIVE_FILE_SHORTCUT, body['name']], str(e), k, numNewParents)
      Ind.Decrement()
      if convertParents and removeParents:
        if not returnIdOnly and not csvPF:
          lcount = len(removeParents)
          Act.Set(Act.DELETE)
          _getMain().entityPerformActionNumItems([Ent.USER, user, targetEntityType, targetName], lcount, Ent.DRIVE_PARENT_FOLDER_REFERENCE, j, jcount)
        try:
          _getMain().callGAPI(drive.files(), 'update',
                   throwReasons=GAPI.DRIVE_ACCESS_THROW_REASONS+[GAPI.BAD_REQUEST],
                   fileId=fileId,
                   removeParents=','.join(removeParents), body={}, fields='id', supportsAllDrives=True)
          if not returnIdOnly and not csvPF:
            Ind.Increment()
            for l, parent in enumerate(removeParents):
              _getMain().entityActionPerformed([Ent.USER, user, targetEntityType, targetName, Ent.DRIVE_PARENT_FOLDER_REFERENCE, parent], l+1, lcount)
            Ind.Decrement()
        except (GAPI.forbidden, GAPI.insufficientFilePermissions, GAPI.invalid, GAPI.badRequest,
                GAPI.fileNotFound, GAPI.unknownError, GAPI.teamDrivesSharingRestrictionNotAllowed) as e:
          _getMain().entityActionFailedWarning([Ent.USER, user, targetEntityType, targetName, Ent.DRIVE_PARENT_FOLDER_REFERENCE, str(l)], str(e), j, jcount)
    Ind.Decrement()
  if csvPF:
    csvPF.writeCSVfile('Shortcuts')

SHORTCUT_CODE_VALID = 0
SHORTCUT_CODE_SHORTCUT_NOT_FOUND = 1
SHORTCUT_CODE_NOT_A_SHORTCUT = 2
SHORTCUT_CODE_TARGET_NOT_FOUND = 3
SHORTCUT_CODE_MIMETYPE_MISMATCH = 4

# gam <UserTypeEntity> check drivefileshortcut <DriveFileEntity>
#	[csv [todrive <ToDriveAttribute>*]]
def checkDriveFileShortcut(users):
  csvPF = None
  fileIdEntity = getDriveFileEntity()
  while Cmd.ArgumentsRemaining():
    myarg = _getMain().getArgument()
    if myarg == 'csv':
      csvPF = _getMain().CSVPrintFile(['User', 'name', 'id', 'owner', 'parentId', 'shortcutDetails.targetId', 'shortcutDetails.targetMimeType',
                            'targetName', 'targetId', 'targetMimeType', 'code'], 'sortall')
    elif csvPF and myarg == 'todrive':
      csvPF.GetTodriveParameters()
    else:
      _getMain().unknownArgumentExit()
  scfields = 'id,name,mimeType,owners(emailAddress),parents,shortcutDetails'
  trfields = 'id,name,mimeType'
  i, count, users = _getMain().getEntityArgument(users)
  for user in users:
    i += 1
    user, drive, jcount = _validateUserGetFileIDs(user, i, count, fileIdEntity)
    if not csvPF:
      _getMain().entityPerformActionNumItems([Ent.USER, user], jcount, Ent.DRIVE_FILE_SHORTCUT, i, count)
    if jcount == 0:
      continue
    Ind.Increment()
    j = 0
    for fileId in fileIdEntity['list']:
      j += 1
      row = {'User': user, 'id': fileId}
      try:
        scresult = _getMain().callGAPI(drive.files(), 'get',
                            throwReasons=GAPI.DRIVE_GET_THROW_REASONS,
                            fileId=fileId, fields=scfields, supportsAllDrives=True)
        row['name'] = scresult['name']
        if scresult['mimeType'] != MIMETYPE_GA_SHORTCUT:
          if not csvPF:
            _getMain().entityActionFailedWarning([Ent.USER, user, _getMain()._getEntityMimeType(scresult), fileId],
                                      Msg.INVALID_MIMETYPE.format(scresult['mimeType'], MIMETYPE_GA_SHORTCUT), j, jcount)
          else:
            row['code'] = SHORTCUT_CODE_NOT_A_SHORTCUT
            csvPF.WriteRow(row)
          continue
        if 'owners' in scresult:
          row['owner'] = scresult['owners'][0]['emailAddress']
        row['parentId'] = scresult['parents'][0]
        row[f'shortcutDetails{GC.Values[GC.CSV_OUTPUT_SUBFIELD_DELIMITER]}targetId'] = scresult['shortcutDetails']['targetId']
        row[f'shortcutDetails{GC.Values[GC.CSV_OUTPUT_SUBFIELD_DELIMITER]}targetMimeType'] = scresult['shortcutDetails']['targetMimeType']
        trfileId = scresult['shortcutDetails']['targetId']
        try:
          trresult = _getMain().callGAPI(drive.files(), 'get',
                              throwReasons=GAPI.DRIVE_GET_THROW_REASONS,
                              fileId=trfileId, fields=trfields, supportsAllDrives=True)
          row['targetName'] = trresult['name']
          row['targetId'] = trresult['id']
          row['targetMimeType'] = trresult['mimeType']
          entityList = [Ent.USER, user, Ent.DRIVE_FILE_SHORTCUT, f"{scresult['name']}({fileId})",
                        _getMain()._getEntityMimeType(trresult), f"{trresult['name']}({trfileId})"]
          if scresult['shortcutDetails']['targetMimeType'] == trresult['mimeType']:
            if not csvPF:
              _getMain().entityActionPerformed(entityList, j, jcount)
            else:
              row['code'] = SHORTCUT_CODE_VALID
          else:
            if not csvPF:
              _getMain().entityActionFailedWarning(entityList, Msg.MIMETYPE_MISMATCH.format(scresult['shortcutDetails']['targetMimeType'], trresult['mimeType']), j, jcount)
            else:
              row['code'] = SHORTCUT_CODE_MIMETYPE_MISMATCH
        except GAPI.fileNotFound:
          if not csvPF:
            _getMain().entityActionFailedWarning([Ent.USER, user, Ent.DRIVE_FILE_SHORTCUT, f"{scresult['name']}({fileId})",
                                       _getMain()._getTargetEntityMimeType(scresult), trfileId], Msg.NOT_FOUND, j, jcount)
          else:
            row['code'] = SHORTCUT_CODE_TARGET_NOT_FOUND
      except GAPI.fileNotFound:
        if not csvPF:
          _getMain().entityActionFailedWarning([Ent.USER, user, Ent.DRIVE_FILE_SHORTCUT, fileId], Msg.NOT_FOUND, j, jcount)
        else:
          row['code'] = SHORTCUT_CODE_SHORTCUT_NOT_FOUND
      except (GAPI.serviceNotAvailable, GAPI.authError, GAPI.domainPolicy) as e:
        _getMain().userDriveServiceNotEnabledWarning(user, str(e), i, count)
        break
      if csvPF:
        csvPF.WriteRow(row)
    Ind.Decrement()
  if csvPF:
    csvPF.writeCSVfile('Check Shortcuts')

# gam <UserTypeEntity> update drivefile <DriveFileEntity> [copy] [returnidonly|returnlinkonly]
#	[(localfile <FileName>|-)|(url <URL>)]
#	[retainname | (newfilename <DriveFileName>) | (replacefilename <REMatchPattern> <RESubstitution>)*]
#	[stripnameprefix <String>]
#	[timestamp <Boolean>]] [timeformat <DateTimeFormat>]
#	<DriveFileUpdateAttribute>*
#	[(gsheet|csvsheet <SheetEntity> [clearfilter])|(addsheet <String>)]
#	[charset <String>] [columndelimiter <Character>]
def updateDriveFile(users):
  fileIdEntity = getDriveFileEntity()
  body = {}
  newName = None
  assignLocalName = True
  parameters = initDriveFileAttributes()
  media_body = None
  addSheetBody = addSheetEntity = None
  updateSheetEntity = None
  clearFilter = False
  preserveModifiedTime = False
  encoding = GC.Values[GC.CHARSET]
  columnDelimiter = GC.Values[GC.CSV_INPUT_COLUMN_DELIMITER]
  returnIdLink = None
  operation = 'update'
  while Cmd.ArgumentsRemaining():
    myarg = _getMain().getArgument()
    if myarg == 'copy':
      operation = 'copy'
      Act.Set(Act.COPY)
    elif myarg == 'returnidonly':
      returnIdLink = 'id'
    elif myarg == 'returnlinkonly':
      returnIdLink = 'webViewLink'
    elif myarg == 'retainname':
      assignLocalName = False
    elif myarg == 'newfilename':
      newName = _getMain().getString(Cmd.OB_DRIVE_FILE_NAME)
      assignLocalName = False
    elif getDriveFileAddRemoveParentAttribute(myarg, parameters):
      pass
    elif myarg == 'addsheet':
      if updateSheetEntity:
        _getMain().usageErrorExit(Msg.ARE_MUTUALLY_EXCLUSIVE.format(myarg, 'csvsheet'))
      sheetTitle = _getMain().getString(Cmd.OB_STRING)
      addSheetEntity = {'sheetType': Ent.SHEET, 'sheetValue': sheetTitle, 'sheetId': None, 'sheetTitle': sheetTitle}
      addSheetBody = {'requests': [{'addSheet': {'properties': {'title': sheetTitle, 'sheetType': 'GRID'}}}]}
    elif myarg in {'gsheet', 'csvsheet'}:
      if addSheetEntity:
        _getMain().usageErrorExit(Msg.ARE_MUTUALLY_EXCLUSIVE.format(myarg, 'addsheet'))
      updateSheetEntity = _getMain().getSheetEntity(False)
    elif myarg == 'clearfilter':
      clearFilter = _getMain().getBoolean()
    elif myarg == 'charset':
      encoding = _getMain().getString(Cmd.OB_CHAR_SET)
    elif myarg == 'columndelimiter':
      columnDelimiter = _getMain().getCharacter()
    else:
      getDriveFileAttribute(myarg, body, parameters, True)
  if assignLocalName and parameters[DFA_LOCALFILENAME] and parameters[DFA_LOCALFILENAME] != '-':
    newName = parameters[DFA_LOCALFILENAME]
  if newName:
    if parameters[DFA_STRIPNAMEPREFIX] and newName.startswith(parameters[DFA_STRIPNAMEPREFIX]):
      newName = newName[len(parameters[DFA_STRIPNAMEPREFIX]):]
  if operation == 'update' and parameters[DFA_LOCALFILEPATH]:
    if parameters[DFA_LOCALFILEPATH] != '-' and parameters[DFA_PRESERVE_FILE_TIMES]:
      setPreservedFileTimes(body, parameters, True)
    if not addSheetEntity and not updateSheetEntity:
      media_body = getMediaBody(parameters)
  elif operation == 'update' and parameters[DFA_URL]:
    addSheetEntity =  updateSheetEntity = None
    media_body = getMediaBody(parameters)
    body['mimeType'] = parameters[DFA_LOCALMIMETYPE]
  elif operation == 'update' and parameters[DFA_PRESERVE_FILE_TIMES]:
    preserveModifiedTime = True
  i, count, users = _getMain().getEntityArgument(users)
  for user in users:
    i += 1
    user, drive, jcount = _validateUserGetFileIDs(user, i, count, fileIdEntity,
                                                  entityType=Ent.DRIVE_FILE_OR_FOLDER if returnIdLink is None else None)
    if jcount == 0:
      continue
    if not _getDriveFileParentInfo(drive, user, i, count, body, parameters, defaultToRoot=False):
      continue
    newParents = body.pop('parents', [])
    if operation == 'update':
      status, addParentsBase, removeParentsBase = _getDriveFileAddRemoveParentInfo(user, i, count, parameters, drive)
      if not status:
        continue
      Ind.Increment()
      j = 0
      for fileId in fileIdEntity['list']:
        j += 1
        try:
          addParents = addParentsBase[:]
          removeParents = removeParentsBase[:]
          if newParents or (not newName and parameters[DFA_REPLACEFILENAME]) or preserveModifiedTime:
            result = _getMain().callGAPI(drive.files(), 'get',
                              throwReasons=GAPI.DRIVE_GET_THROW_REASONS,
                              fileId=fileId, fields='name,parents,modifiedTime', supportsAllDrives=True)
            if newParents:
              addParents.extend(newParents)
              removeParents.extend(result.get('parents', []))
            if not newName and parameters[DFA_REPLACEFILENAME]:
              body['name'] = processFilenameReplacements(result['name'], parameters[DFA_REPLACEFILENAME])
            if preserveModifiedTime:
              body['modifiedTime'] = result['modifiedTime']
          if newName:
            if parameters[DFA_REPLACEFILENAME]:
              body['name'] = processFilenameReplacements(newName, parameters[DFA_REPLACEFILENAME])
            else:
              body['name'] = newName
            if parameters[DFA_TIMESTAMP]:
              addTimestampToFilename(parameters, body)
          if addSheetEntity or updateSheetEntity:
            entityValueList = [Ent.USER, user, Ent.DRIVE_FILE_ID, fileId]
            try:
              result = _getMain().callGAPI(drive.files(), 'get',
                                throwReasons=GAPI.DRIVE_USER_THROW_REASONS+[GAPI.FILE_NOT_FOUND],
                                fileId=fileId, fields='id,mimeType,capabilities(canEdit)', supportsAllDrives=True)
              if result['mimeType'] != MIMETYPE_GA_SPREADSHEET:
                _getMain().entityActionNotPerformedWarning(entityValueList, f'{Msg.NOT_A} {Ent.Singular(Ent.SPREADSHEET)}', j, jcount)
                continue
              if not result['capabilities']['canEdit']:
                _getMain().entityActionNotPerformedWarning(entityValueList, Msg.NOT_WRITABLE, j, jcount)
                continue
              _, sheet = _getMain().buildGAPIServiceObject(API.SHEETS, user)
              if sheet is None:
                continue
              if addSheetEntity:
                addresult = _getMain().callGAPI(sheet.spreadsheets(), 'batchUpdate',
                                     throwReasons=GAPI.SHEETS_ACCESS_THROW_REASONS,
                                     spreadsheetId=fileId, body=addSheetBody)
                sheetEntity = addSheetEntity.copy()
                sheetEntity['sheetId'] = addresult['replies'][0]['addSheet']['properties']['sheetId']
                entityValueList.extend([sheetEntity['sheetType'], sheetEntity['sheetTitle']])
                sheetEntity['sheetType'] = Ent.SHEET_ID # Temporarily set addsheet type to ID
              else:
                sheetEntity = updateSheetEntity.copy()
                entityValueList.extend([sheetEntity['sheetType'], sheetEntity['sheetValue']])
              spreadsheet = _getMain().callGAPI(sheet.spreadsheets(), 'get',
                                     throwReasons=GAPI.SHEETS_ACCESS_THROW_REASONS,
                                     spreadsheetId=fileId,
                                     fields='spreadsheetUrl,sheets(properties(sheetId,title),protectedRanges(range(sheetId),requestingUserCanEdit))')
              sheetId = _getMain().getSheetIdFromSheetEntity(spreadsheet, sheetEntity)
              if sheetId is None:
                _getMain().entityActionNotPerformedWarning(entityValueList, Msg.NOT_FOUND, j, jcount)
                continue
              if _getMain().protectedSheetId(spreadsheet, sheetId):
                _getMain().entityActionNotPerformedWarning(entityValueList, Msg.NOT_WRITABLE, j, jcount)
                continue
              if addSheetEntity: # Restore addsheet type
                sheetEntity['sheetType'] = Ent.SHEET
              result = _getMain().callGAPI(drive.files(), 'update',
                                throwReasons=GAPI.DRIVE_ACCESS_THROW_REASONS+[GAPI.BAD_REQUEST, GAPI.CANNOT_ADD_PARENT,
                                                                              GAPI.INSUFFICIENT_PARENT_PERMISSIONS,
                                                                              GAPI.CANNOT_MODIFY_VIEWERS_CAN_COPY_CONTENT,
                                                                              GAPI.TEAMDRIVES_PARENT_LIMIT,
                                                                              GAPI.TEAMDRIVES_FOLDER_MOVE_IN_NOT_SUPPORTED,
                                                                              GAPI.TEAMDRIVES_SHARING_RESTRICTION_NOT_ALLOWED],
                                fileId=fileId,
                                ocrLanguage=parameters[DFA_OCRLANGUAGE],
                                keepRevisionForever=parameters[DFA_KEEP_REVISION_FOREVER],
                                useContentAsIndexableText=parameters[DFA_USE_CONTENT_AS_INDEXABLE_TEXT],
                                addParents=','.join(addParents), removeParents=','.join(removeParents),
                                body=body, fields='id,name,mimeType,webViewLink', supportsAllDrives=True)
### File size check??
              sbody = {'requests': []}
              if clearFilter and updateSheetEntity:
                sbody['requests'].append({'clearBasicFilter': {'sheetId': sheetId}})
              sbody['requests'].append({'updateCells': {'range': {'sheetId': sheetId}, 'fields': '*'}})
              sbody['requests'].append({'pasteData': {'coordinate': {'sheetId': sheetId, 'rowIndex': '0', 'columnIndex': '0'},
                                                      'data': _getMain().readFile(parameters[DFA_LOCALFILEPATH], encoding=encoding),
                                                      'type': 'PASTE_NORMAL', 'delimiter': columnDelimiter}})
              _getMain().callGAPI(sheet.spreadsheets(), 'batchUpdate',
                       throwReasons=GAPI.SHEETS_ACCESS_THROW_REASONS,
                       spreadsheetId=fileId, body=sbody)
              if returnIdLink:
                _getMain().writeStdout(f'{result[returnIdLink]}\n')
              else:
                _getMain().entityModifierNewValueActionPerformed([Ent.USER, user, Ent.DRIVE_FILE, result['name'], sheetEntity['sheetType'], sheetEntity['sheetValue']],
                                                      Act.MODIFIER_WITH_CONTENT_FROM, parameters[DFA_LOCALFILENAME], j, jcount)
            except GAPI.fileNotFound as e:
              _getMain().entityActionFailedWarning([Ent.USER, user, Ent.DRIVE_FILE_ID, fileId], str(e), j, jcount)
            except (GAPI.notFound, GAPI.forbidden, GAPI.permissionDenied,
                    GAPI.internalError, GAPI.insufficientFilePermissions, GAPI.badRequest,
                    GAPI.invalid, GAPI.invalidArgument, GAPI.failedPrecondition) as e:
              _getMain().entityActionFailedWarning(entityValueList, str(e), j, jcount)
            except (GAPI.serviceNotAvailable, GAPI.authError, GAPI.domainPolicy) as e:
              _getMain().userDriveServiceNotEnabledWarning(user, str(e), i, count)
              break
          else:
            result = _getMain().callGAPI(drive.files(), 'update',
                              throwReasons=GAPI.DRIVE_ACCESS_THROW_REASONS+[GAPI.BAD_REQUEST, GAPI.CANNOT_ADD_PARENT,
                                                                            GAPI.INSUFFICIENT_PARENT_PERMISSIONS,
                                                                            GAPI.FILE_NEVER_WRITABLE, GAPI.CANNOT_MODIFY_VIEWERS_CAN_COPY_CONTENT,
                                                                            GAPI.SHARE_OUT_NOT_PERMITTED, GAPI.SHARE_OUT_NOT_PERMITTED_TO_USER,
                                                                            GAPI.TEAMDRIVES_PARENT_LIMIT, GAPI.TEAMDRIVES_FOLDER_MOVE_IN_NOT_SUPPORTED,
                                                                            GAPI.TEAMDRIVES_SHARING_RESTRICTION_NOT_ALLOWED,
                                                                            GAPI.CROSS_DOMAIN_MOVE_RESTRICTION, GAPI.UPLOAD_TOO_LARGE,
                                                                            GAPI.TEAMDRIVES_SHORTCUT_FILE_NOT_SUPPORTED,
                                                                            GAPI.FILE_OWNER_NOT_MEMBER_OF_WRITER_DOMAIN,
                                                                            GAPI.FILE_WRITER_TEAMDRIVE_MOVE_IN_DISABLED],
                              fileId=fileId,
                              ocrLanguage=parameters[DFA_OCRLANGUAGE],
                              keepRevisionForever=parameters[DFA_KEEP_REVISION_FOREVER],
                              useContentAsIndexableText=parameters[DFA_USE_CONTENT_AS_INDEXABLE_TEXT],
                              addParents=','.join(addParents), removeParents=','.join(removeParents),
                              media_body=media_body, body=body, fields='id,name,mimeType,webViewLink',
                              supportsAllDrives=True)
            if result:
              if returnIdLink:
                _getMain().writeStdout(f'{result[returnIdLink]}\n')
              elif media_body:
                _getMain().entityModifierNewValueActionPerformed([Ent.USER, user, Ent.DRIVE_FILE, result['name']],
                                                      Act.MODIFIER_WITH_CONTENT_FROM, parameters[DFA_LOCALFILENAME] or parameters[DFA_URL], j, jcount)
              else:
                _getMain().entityActionPerformed([Ent.USER, user, _getMain()._getEntityMimeType(result), result['name']], j, jcount)
            else:
              if returnIdLink:
                _getMain().writeStdout(f'{fileId}\n')
              else:
                _getMain().entityActionPerformed([Ent.USER, user, Ent.DRIVE_FILE_OR_FOLDER_ID, fileId], j, jcount)
        except (GAPI.fileNotFound, GAPI.forbidden, GAPI.internalError, GAPI.insufficientFilePermissions, GAPI.insufficientParentPermissions,
                GAPI.unknownError, GAPI.invalid, GAPI.badRequest, GAPI.cannotAddParent,
                GAPI.fileNeverWritable, GAPI.cannotModifyViewersCanCopyContent,
                GAPI.shareInNotPermitted, GAPI.shareOutNotPermitted, GAPI.shareOutNotPermittedToUser,
                GAPI.teamDrivesParentLimit, GAPI.teamDrivesFolderMoveInNotSupported,
                GAPI.teamDrivesSharingRestrictionNotAllowed, GAPI.crossDomainMoveRestriction,
                GAPI.uploadTooLarge, GAPI.teamDrivesShortcutFileNotSupported,
                GAPI.fileOwnerNotMemberOfWriterDomain, GAPI.fileWriterTeamDriveMoveInDisabled) as e:
          _getMain().entityActionFailedWarning([Ent.USER, user, Ent.DRIVE_FILE_OR_FOLDER_ID, fileId], str(e), j, jcount)
        except (GAPI.serviceNotAvailable, GAPI.authError, GAPI.domainPolicy) as e:
          _getMain().userDriveServiceNotEnabledWarning(user, str(e), i, count)
          break
      Ind.Decrement()
    else:
      if newName:
        if parameters[DFA_REPLACEFILENAME]:
          body['name'] = processFilenameReplacements(newName, parameters[DFA_REPLACEFILENAME])
        else:
          body['name'] = newName
        if parameters[DFA_TIMESTAMP]:
          addTimestampToFilename(parameters, body)
      Ind.Increment()
      j = 0
      for fileId in fileIdEntity['list']:
        j += 1
        try:
          result = _getMain().callGAPI(drive.files(), 'copy',
                            throwReasons=GAPI.DRIVE_COPY_THROW_REASONS+[GAPI.CANNOT_MODIFY_VIEWERS_CAN_COPY_CONTENT],
                            fileId=fileId,
                            ignoreDefaultVisibility=parameters[DFA_IGNORE_DEFAULT_VISIBILITY],
                            keepRevisionForever=parameters[DFA_KEEP_REVISION_FOREVER],
                            body=body, fields='id,name,webViewLink', supportsAllDrives=True)
          if returnIdLink:
            writeReturnIdLink(returnIdLink, parameters[DFA_LOCALMIMETYPE], result)
          else:
            _getMain().entityModifierNewValueItemValueListActionPerformed([Ent.USER, user, Ent.DRIVE_FILE, fileId],
                                                               Act.MODIFIER_TO, result['name'], [Ent.DRIVE_FILE_ID, result['id']], j, jcount)
        except (GAPI.fileNotFound, GAPI.forbidden, GAPI.internalError, GAPI.insufficientFilePermissions, GAPI.unknownError,
                GAPI.invalid, GAPI.cannotCopyFile, GAPI.badRequest, GAPI.responsePreparationFailure, GAPI.fileNeverWritable, GAPI.fieldNotWritable,
                GAPI.teamDrivesSharingRestrictionNotAllowed, GAPI.rateLimitExceeded, GAPI.userRateLimitExceeded,
                GAPI.cannotModifyViewersCanCopyContent) as e:
          _getMain().entityActionFailedWarning([Ent.USER, user, Ent.DRIVE_FILE, fileId], str(e), j, jcount)
        except (GAPI.storageQuotaExceeded, GAPI.teamDriveFileLimitExceeded, GAPI.teamDriveHierarchyTooDeep,) as e:
          _getMain().entityActionFailedWarning([Ent.USER, user, Ent.DRIVE_FILE, fileId], str(e), j, jcount)
          break
        except (GAPI.serviceNotAvailable, GAPI.authError, GAPI.domainPolicy) as e:
          _getMain().userDriveServiceNotEnabledWarning(user, str(e), i, count)
          break
      Ind.Decrement()

STAT_FOLDER_TOTAL = 0
STAT_FOLDER_COPIED_MOVED = 1
STAT_FOLDER_SHORTCUT_CREATED = 2
STAT_FOLDER_SHORTCUT_EXISTS = 3
STAT_FOLDER_MERGED = 4
STAT_FOLDER_DUPLICATE = 5
STAT_FOLDER_FAILED = 6
STAT_FOLDER_NOT_WRITABLE = 7
STAT_FOLDER_PERMISSIONS_FAILED = 8
STAT_FILE_TOTAL = 9
STAT_FILE_COPIED_MOVED = 10
STAT_FILE_SHORTCUT_CREATED = 11
STAT_FILE_SHORTCUT_EXISTS = 12
STAT_FILE_DUPLICATE = 13
STAT_FILE_FAILED = 14
STAT_FILE_NOT_COPYABLE_MOVABLE = 15
STAT_FILE_IN_SKIPIDS = 16
STAT_FILE_PERMISSIONS_FAILED = 17
STAT_FILE_PROTECTEDRANGES_FAILED = 18
STAT_USER_NOT_ORGANIZER = 19
STAT_LENGTH = 20

FOLDER_SUBTOTAL_STATS = [STAT_FOLDER_COPIED_MOVED, STAT_FOLDER_SHORTCUT_CREATED, STAT_FOLDER_SHORTCUT_EXISTS,
                         STAT_FOLDER_DUPLICATE, STAT_FOLDER_MERGED, STAT_FOLDER_FAILED, STAT_FOLDER_NOT_WRITABLE]
FILE_SUBTOTAL_STATS = [STAT_FILE_COPIED_MOVED, STAT_FILE_SHORTCUT_CREATED, STAT_FILE_SHORTCUT_EXISTS,
                       STAT_FILE_DUPLICATE, STAT_FILE_FAILED, STAT_FILE_NOT_COPYABLE_MOVABLE, STAT_FILE_IN_SKIPIDS]

def _initStatistics():
  return [0] * STAT_LENGTH

def _incrStatistic(statistics, stat):
  statistics[stat] += 1
  if stat in FOLDER_SUBTOTAL_STATS:
    statistics[STAT_FOLDER_TOTAL] += 1
  elif stat in FILE_SUBTOTAL_STATS:
    statistics[STAT_FILE_TOTAL] += 1

