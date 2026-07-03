"""Copy/move utility functions, statistics, permission handling, and copyDriveFile.

Part of the copymove sub-package."""

"""File copy/move operations with permission handling.

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

MY_DRIVE = 'My Drive'
TEAM_DRIVE = 'Drive'

def _printStatistics(user, statistics, i, count, copy):
  if statistics[STAT_FOLDER_TOTAL]:
    if copy:
      _getMain().printEntityKVList([Ent.USER, user],
                        [Ent.Plural(Ent.DRIVE_FOLDER),
                         Msg.STATISTICS_COPY_FOLDER.format(statistics[STAT_FOLDER_TOTAL],
                                                           statistics[STAT_FOLDER_COPIED_MOVED],
                                                           statistics[STAT_FOLDER_SHORTCUT_CREATED],
                                                           statistics[STAT_FOLDER_SHORTCUT_EXISTS],
                                                           statistics[STAT_FOLDER_DUPLICATE],
                                                           statistics[STAT_FOLDER_MERGED],
                                                           statistics[STAT_FOLDER_FAILED],
                                                           statistics[STAT_FOLDER_NOT_WRITABLE],
                                                           statistics[STAT_FOLDER_PERMISSIONS_FAILED])],
                        i, count)
    else:
      _getMain().printEntityKVList([Ent.USER, user],
                        [Ent.Plural(Ent.DRIVE_FOLDER),
                         Msg.STATISTICS_MOVE_FOLDER.format(statistics[STAT_FOLDER_TOTAL],
                                                           statistics[STAT_FOLDER_COPIED_MOVED],
                                                           statistics[STAT_FOLDER_SHORTCUT_CREATED],
                                                           statistics[STAT_FOLDER_SHORTCUT_EXISTS],
                                                           statistics[STAT_FOLDER_DUPLICATE],
                                                           statistics[STAT_FOLDER_MERGED],
                                                           statistics[STAT_FOLDER_FAILED],
                                                           statistics[STAT_FOLDER_NOT_WRITABLE])],
                        i, count)
  if statistics[STAT_FILE_TOTAL]:
    if copy:
      _getMain().printEntityKVList([Ent.USER, user],
                        [Ent.Plural(Ent.DRIVE_FILE),
                         Msg.STATISTICS_COPY_FILE.format(statistics[STAT_FILE_TOTAL],
                                                         statistics[STAT_FILE_COPIED_MOVED],
                                                         statistics[STAT_FILE_SHORTCUT_CREATED],
                                                         statistics[STAT_FILE_SHORTCUT_EXISTS],
                                                         statistics[STAT_FILE_DUPLICATE],
                                                         statistics[STAT_FILE_FAILED],
                                                         statistics[STAT_FILE_NOT_COPYABLE_MOVABLE],
                                                         statistics[STAT_FILE_IN_SKIPIDS],
                                                         statistics[STAT_FILE_PERMISSIONS_FAILED],
                                                         statistics[STAT_FILE_PROTECTEDRANGES_FAILED])],
                        i, count)
    else:
      _getMain().printEntityKVList([Ent.USER, user],
                        [Ent.Plural(Ent.DRIVE_FILE),
                         Msg.STATISTICS_MOVE_FILE.format(statistics[STAT_FILE_TOTAL],
                                                         statistics[STAT_FILE_COPIED_MOVED],
                                                         statistics[STAT_FILE_SHORTCUT_CREATED],
                                                         statistics[STAT_FILE_SHORTCUT_EXISTS],
                                                         statistics[STAT_FILE_DUPLICATE],
                                                         statistics[STAT_FILE_FAILED],
                                                         statistics[STAT_FILE_NOT_COPYABLE_MOVABLE])],
                        i, count)
  if statistics[STAT_USER_NOT_ORGANIZER]:
    _getMain().printEntityKVList([Ent.USER, user],
                      [Ent.Plural(Ent.DRIVE_FILE_OR_FOLDER),
                       Msg.STATISTICS_USER_NOT_ORGANIZER.format(statistics[STAT_USER_NOT_ORGANIZER])],
                      i, count)

DUPLICATE_FILE_OVERWRITE_OLDER = 0
DUPLICATE_FILE_OVERWRITE_ALL = 1
DUPLICATE_FILE_DUPLICATE_NAME = 2
DUPLICATE_FILE_UNIQUE_NAME = 3
DUPLICATE_FILE_SKIP = 4
DUPLICATE_FOLDER_MERGE = 0
DUPLICATE_FOLDER_DUPLICATE_NAME = 1
DUPLICATE_FOLDER_UNIQUE_NAME = 2
DUPLICATE_FOLDER_SKIP = 3

DEST_PARENT_MYDRIVE_ROOT = 0
DEST_PARENT_MYDRIVE_FOLDER = 1
DEST_PARENT_SHAREDDRIVE_ROOT = 2
DEST_PARENT_SHAREDDRIVE_FOLDER = 3

COPY_NONINHERITED_PERMISSIONS_NEVER = 0
COPY_NONINHERITED_PERMISSIONS_ALWAYS = 1
COPY_NONINHERITED_PERMISSIONS_SYNC_ALL_FOLDERS = 2
COPY_NONINHERITED_PERMISSIONS_SYNC_UPDATED_FOLDERS = 3
COPY_NONINHERITED_PERMISSIONS_CHOICES_MAP = {
  'never': COPY_NONINHERITED_PERMISSIONS_NEVER,
  'always': COPY_NONINHERITED_PERMISSIONS_ALWAYS,
  'syncallfolders': COPY_NONINHERITED_PERMISSIONS_SYNC_ALL_FOLDERS,
  'syncupdatedfolders': COPY_NONINHERITED_PERMISSIONS_SYNC_UPDATED_FOLDERS,
  }

def initCopyMoveOptions(copyCmd):
  return {
    'copyCmd': copyCmd,
    'sourceDriveId': None,
    'destDriveId': None,
    'destParentType': False,
    'newFilename': None,
    'stripNamePrefix': None,
    'replaceFilename': [],
    'summary': False,
    'mergeWithParent': False,
    'mergeWithParentRetain': False,
    'retainSourceFolders': False,
    'sourceIsMyDriveSharedDrive': False,
    'showPermissionMessages': False,
    'sendEmailIfRequired': False,
    'useDomainAdminAccess': False,
    'copiedShortcutsPointToCopiedFiles': True,
    'createShortcutsForNonmovableFiles': False,
    'duplicateFiles': DUPLICATE_FILE_OVERWRITE_OLDER,
    'duplicateFolders': DUPLICATE_FOLDER_MERGE,
    'copyFilePermissions': False,
    'copyFileInheritedPermissions': True,
    'copyFileNonInheritedPermissions': COPY_NONINHERITED_PERMISSIONS_ALWAYS,
    'copyFolderPermissions': True,
    'copyMergeWithParentFolderPermissions': False,
    'copyMergedTopFolderPermissions': copyCmd,
    'copyMergedSubFolderPermissions': copyCmd,
    'copyTopFolderPermissions': True,
    'copySubFolderPermissions': True,
    'copyTopFolderInheritedPermissions': True,
    'copySubFolderInheritedPermissions': True,
    'copyTopFolderNonInheritedPermissions': COPY_NONINHERITED_PERMISSIONS_ALWAYS,
    'copySubFolderNonInheritedPermissions': COPY_NONINHERITED_PERMISSIONS_ALWAYS,
    'noCopyNonInheritedPermissions': COPY_NONINHERITED_PERMISSIONS_NEVER,
    'moveFilePermissions': True,
    'excludePermissionsFromDomains': set(),
    'includePermissionsFromDomains': set(),
    'mapPermissionsEmails': {},
    'mapPermissionsDomains': {},
    'copySheetProtectedRangesInheritedPermissions': False,
    'copySheetProtectedRangesNonInheritedPermissions': COPY_NONINHERITED_PERMISSIONS_NEVER,
    'copySubFiles': True,
    'copySubFolders': True,
    'copySubShortcuts': True,
    'fileNameMatchPattern': None,
    'folderNameMatchPattern': None,
    'shortcutNameMatchPattern': None,
    'mimeTypeCheck': MimeTypeCheck(),
    'notMimeTypes': False,
    'copySubFilesOwnedBy': {},
    'copyPermissionRoles': set(DRIVEFILE_ACL_ROLES_MAP.values()),
    'copyPermissionTypes': set(DRIVEFILE_ACL_PERMISSION_TYPES),
    'checkModifiedTime': False,
    'startEndTime': _getMain().StartEndTime(),
    }

DUPLICATE_FILE_CHOICES = {
  'overwriteall': DUPLICATE_FILE_OVERWRITE_ALL,
  'overwriteolder': DUPLICATE_FILE_OVERWRITE_OLDER,
  'duplicatename': DUPLICATE_FILE_DUPLICATE_NAME,
  'uniquename': DUPLICATE_FILE_UNIQUE_NAME,
  'skip': DUPLICATE_FILE_SKIP,
  }
DUPLICATE_FOLDER_CHOICES = {
  'merge': DUPLICATE_FOLDER_MERGE,
  'duplicatename': DUPLICATE_FOLDER_DUPLICATE_NAME,
  'uniquename': DUPLICATE_FOLDER_UNIQUE_NAME,
  'skip': DUPLICATE_FOLDER_SKIP,
  }

COPY_OWNED_BY_CHOICE_MAP = {
  'any': {},
  'me': {'mode': 'bool', 'value': True},
  'others': {'mode': 'bool', 'value': False},
  'users': {'mode': 'users', 'value': set()},
  'notusers': {'mode': 'notusers', 'value': set()},
  'regex': {'mode': 'regex', 'value': ''},
  'notregex': {'mode': 'notregex', 'value': ''}
}

def getCopyMoveOptions(myarg, copyMoveOptions):
# Copy/Move arguments
  if myarg == 'newfilename':
    copyMoveOptions['newFilename'] = _getMain().getString(Cmd.OB_DRIVE_FILE_NAME)
  elif myarg =='stripnameprefix':
    copyMoveOptions['stripNamePrefix'] = _getMain().getString(Cmd.OB_STRING, minLen=0)
  elif myarg == 'replacefilename':
    copyMoveOptions['replaceFilename'].append(_getMain().getREPatternSubstitution(re.IGNORECASE))
  elif myarg == 'showpermissionmessages':
    copyMoveOptions['showPermissionMessages'] = _getMain().getBoolean()
  elif myarg == 'sendemailifrequired':
    copyMoveOptions['sendEmailIfRequired'] = _getMain().getBoolean()
  elif myarg == 'summary':
    copyMoveOptions['summary'] = _getMain().getBoolean()
  elif myarg == 'mergewithparent':
    copyMoveOptions['mergeWithParent'] = _getMain().getBoolean()
    if copyMoveOptions['mergeWithParent']:
      copyMoveOptions['mergeWithParentRetain'] = False
  elif myarg == 'duplicatefiles':
    copyMoveOptions['duplicateFiles'] = _getMain().getChoice(DUPLICATE_FILE_CHOICES, mapChoice=True)
  elif myarg == 'duplicatefolders':
    copyMoveOptions['duplicateFolders'] = _getMain().getChoice(DUPLICATE_FOLDER_CHOICES, mapChoice=True)
  elif myarg == 'copyfolderpermissions':
    copyMoveOptions['copyFolderPermissions'] = _getMain().getBoolean()
  elif myarg == 'copymergewithparentfolderpermissions':
    copyMoveOptions['copyMergeWithParentFolderPermissions'] = _getMain().getBoolean()
  elif myarg == 'copymergedtopfolderpermissions':
    copyMoveOptions['copyMergedTopFolderPermissions'] = _getMain().getBoolean()
  elif myarg == 'copytopfolderpermissions':
    copyMoveOptions['copyTopFolderPermissions'] = _getMain().getBoolean()
  elif myarg == 'copytopfolderinheritedpermissions':
    copyMoveOptions['copyTopFolderInheritedPermissions'] = _getMain().getBoolean()
  elif myarg == 'copytopfoldernoninheritedpermissions':
    copyMoveOptions['copyTopFolderNonInheritedPermissions'] = _getMain().getChoice(COPY_NONINHERITED_PERMISSIONS_CHOICES_MAP, mapChoice=True)
  elif myarg == 'copymergedsubfolderpermissions':
    copyMoveOptions['copyMergedSubFolderPermissions'] = _getMain().getBoolean()
  elif myarg == 'copysubfolderpermissions':
    copyMoveOptions['copySubFolderPermissions'] = _getMain().getBoolean()
  elif myarg == 'copysubfolderinheritedpermissions':
    copyMoveOptions['copySubFolderInheritedPermissions'] = _getMain().getBoolean()
  elif myarg == 'copysubfoldernoninheritedpermissions':
    copyMoveOptions['copySubFolderNonInheritedPermissions'] = _getMain().getChoice(COPY_NONINHERITED_PERMISSIONS_CHOICES_MAP, mapChoice=True)
  elif myarg == 'excludepermissionsfromdomains':
    copyMoveOptions['excludePermissionsFromDomains'] = set(getString(Cmd.OB_DOMAIN_NAME_LIST).lower().replace(',', ' ').split())
    copyMoveOptions['includePermissionsFromDomains'] = set()
  elif myarg == 'includepermissionsfromdomains':
    copyMoveOptions['includePermissionsFromDomains'] = set(getString(Cmd.OB_DOMAIN_NAME_LIST).lower().replace(',', ' ').split())
    copyMoveOptions['excludePermissionsFromDomains'] = set()
  elif myarg == 'mappermissionsemail':
    sourceEmail = _getMain().getEmailAddress(noUid=True).lower()
    copyMoveOptions['mapPermissionsEmails'][sourceEmail] = _getMain().getEmailAddress(noUid=True).lower()
  elif myarg == 'mappermissionsemailfile':
    csvInputLocation = Cmd.Location()
    f, csvFile, _ = _getMain().openCSVFileReader(_getMain().getString(Cmd.OB_FILE_NAME))
    if 'sourceEmail' not in csvFile.fieldnames or 'destinationEmail' not in csvFile.fieldnames:
      Cmd.SetLocation(csvInputLocation)
      _getMain().usageErrorExit(Msg.MAP_PERMISSIONS_EMAIL_FILE_HEADERS_REQUIRED.format(myarg))
    for row in csvFile:
      copyMoveOptions['mapPermissionsEmails'][row['sourceEmail']] = row['destinationEmail']
    _getMain().closeFile(f)
  elif myarg == 'mappermissionsdomain':
    oldDomain = _getMain().getString(Cmd.OB_DOMAIN_NAME).lower()
    copyMoveOptions['mapPermissionsDomains'][oldDomain] = _getMain().getString(Cmd.OB_DOMAIN_NAME).lower()
  else:
# Move arguments
    if not copyMoveOptions['copyCmd']:
      if myarg == 'retainsourcefolders':
        copyMoveOptions['retainSourceFolders'] = _getMain().getBoolean()
      elif myarg == 'mergewithparentretain':
        copyMoveOptions['mergeWithParentRetain'] = _getMain().getBoolean()
        if copyMoveOptions['mergeWithParentRetain']:
          copyMoveOptions['mergeWithParent'] = False
      elif myarg == 'createshortcutsfornonmovablefiles':
        copyMoveOptions['createShortcutsForNonmovableFiles'] = _getMain().getBoolean()
      elif myarg == 'movefilepermissions':
        copyMoveOptions['moveFilePermissions'] = _getMain().getBoolean()
      else:
        return False
# Copy arguments
    else:
      if myarg == 'copiedshortcutspointtocopiedfiles':
        copyMoveOptions['copiedShortcutsPointToCopiedFiles'] = _getMain().getBoolean()
      elif myarg == 'copyfilepermissions':
        copyMoveOptions['copyFilePermissions'] = _getMain().getBoolean()
      elif myarg == 'copyfileinheritedpermissions':
        copyMoveOptions['copyFileInheritedPermissions'] = _getMain().getBoolean()
      elif myarg == 'copyfilenoninheritedpermissions':
        copyMoveOptions['copyFileNonInheritedPermissions'] = COPY_NONINHERITED_PERMISSIONS_ALWAYS if _getMain().getBoolean() else COPY_NONINHERITED_PERMISSIONS_NEVER
      elif myarg == 'copypermissionroles':
        copyMoveOptions['copyPermissionRoles'] = set()
        for prole in _getMain().getString(Cmd.OB_PERMISSION_ROLE_LIST).lower().replace(',', ' ').split():
          if prole in DRIVEFILE_ACL_ROLES_MAP:
            copyMoveOptions['copyPermissionRoles'].add(DRIVEFILE_ACL_ROLES_MAP[prole])
          else:
            _getMain().invalidChoiceExit(prole, DRIVEFILE_ACL_ROLES_MAP, True)
      elif myarg == 'copypermissiontypes':
        copyMoveOptions['copyPermissionTypes'] = set()
        for ptype in _getMain().getString(Cmd.OB_PERMISSION_TYPE_LIST).lower().replace(',', ' ').split():
          if ptype in DRIVEFILE_ACL_PERMISSION_TYPES:
            copyMoveOptions['copyPermissionTypes'].add(ptype)
          else:
            _getMain().invalidChoiceExit(ptype, DRIVEFILE_ACL_PERMISSION_TYPES, True)
      elif myarg == 'copysheetprotectedranges':
        if _getMain().getBoolean():
          copyMoveOptions['copySheetProtectedRangesInheritedPermissions'] = True
          copyMoveOptions['copySheetProtectedRangesNonInheritedPermissions'] = COPY_NONINHERITED_PERMISSIONS_ALWAYS
        else:
          copyMoveOptions['copySheetProtectedRangesInheritedPermissions'] = False
          copyMoveOptions['copySheetProtectedRangesNonInheritedPermissions'] = COPY_NONINHERITED_PERMISSIONS_NEVER
      elif myarg == 'copysheetprotectedrangesinheritedpermissions':
        copyMoveOptions['copySheetProtectedRangesInheritedPermissions'] = _getMain().getBoolean()
      elif myarg == 'copysheetprotectedrangesnoninheritedpermissions':
        copyMoveOptions['copySheetProtectedRangesNonInheritedPermissions'] = COPY_NONINHERITED_PERMISSIONS_ALWAYS if _getMain().getBoolean() else COPY_NONINHERITED_PERMISSIONS_NEVER
      elif myarg == 'copysubfiles':
        copyMoveOptions['copySubFiles'] = _getMain().getBoolean()
      elif myarg == 'copysubfolders':
        copyMoveOptions['copySubFolders'] = _getMain().getBoolean()
      elif myarg == 'copysubshortcuts':
        copyMoveOptions['copySubShortcuts'] = _getMain().getBoolean()
      elif myarg == 'filenamematchpattern':
        copyMoveOptions['fileNameMatchPattern'] = _getMain().getREPattern(re.IGNORECASE)
      elif myarg == 'foldernamematchpattern':
        copyMoveOptions['folderNameMatchPattern'] = _getMain().getREPattern(re.IGNORECASE)
      elif myarg == 'shortcutnamematchpattern':
        copyMoveOptions['shortcutNameMatchPattern'] = _getMain().getREPattern(re.IGNORECASE)
      elif myarg == 'filemimetype':
        copyMoveOptions['mimeTypeCheck'].Get()
      elif myarg == 'copysubfilesownedby':
        copyMoveOptions['copySubFilesOwnedBy'] = _getMain().getChoice(COPY_OWNED_BY_CHOICE_MAP, mapChoice=True)
        if copyMoveOptions['copySubFilesOwnedBy']:
          if copyMoveOptions['copySubFilesOwnedBy']['mode'] in {'users', 'notusers'}:
            copyMoveOptions['copySubFilesOwnedBy']['value'] = set(getString(Cmd.OB_EMAIL_ADDRESS_LIST).replace(',', ' ').lower().split())
          elif copyMoveOptions['copySubFilesOwnedBy']['mode'] in {'regex', 'notregex'}:
            copyMoveOptions['copySubFilesOwnedBy']['value'] = _getMain().getREPattern(re.IGNORECASE)
      elif myarg in {'start', 'starttime', 'end', 'endtime', 'range'}:
        copyMoveOptions['startEndTime'].Get(myarg)
        copyMoveOptions['checkModifiedTime'] = True
      else:
        return False
  return True

def _targetFilenameExists(destFilename, mimeType, targetChildren):
  destFilenameLower = destFilename.lower()
  for target in targetChildren:
    if destFilenameLower == target['name'].lower() and mimeType == target['mimeType']:
      return target
  return None

UNIQUE_PREFIX_PATTERN = re.compile(r'^(.+)\((\d+)\)$')

def _getFilenameParts(destFilename):
  base, ext = os.path.splitext(destFilename)
  if ext and base.endswith('.tar'):
    ext = '.tar'+ext
    base = base[:-4]
  elif len(ext) > 5:
    base = destFilename
    ext = ''
  mg = UNIQUE_PREFIX_PATTERN.match(base)
  if mg:
    return (mg.group(1), int(mg.group(2)), ext)
  return (base, 0, ext)

def _getFilenamePrefix(destFilename):
  base, _, _ = _getFilenameParts(destFilename)
  return base

def _getUniqueFilename(destFilename, mimeType, targetChildren):
  if _targetFilenameExists(destFilename, mimeType, targetChildren) is None:
    return destFilename
  base, _, ext = _getFilenameParts(destFilename)
  n = 0
  for target in targetChildren:
    tbase, tcnt, text = _getFilenameParts(target['name'])
    if base != tbase or ext != text:
      continue
    if tcnt > n:
      n = tcnt
  if ext:
    return f'{base}({n+1}){ext}'
  return f'{base}({n+1})'

def _copyPermissions(drive, user, i, count, j, jcount,
                     entityType, fileId, fileTitle, newFileId, newFileTitle,
                     statistics, stat, copyMoveOptions, atTop, copyInherited, copyNonInherited,
                     updateOwner):
  def getPermissions(fid):
    permissions = {}
    try:
      result = _getMain().callGAPIpages(drive.permissions(), 'list', 'permissions',
                             throwReasons=GAPI.DRIVE3_GET_ACL_REASONS,
                             retryReasons=GAPI.SERVICE_NOT_AVAILABLE_RETRY_REASONS,
                             fileId=fid,
                             fields='nextPageToken,permissions(allowFileDiscovery,domain,emailAddress,expirationTime,id,role,type,deleted,view,pendingOwner,permissionDetails)',
                             useDomainAdminAccess=copyMoveOptions['useDomainAdminAccess'], supportsAllDrives=True)
      for permission in result:
        permission.pop('teamDrivePermissionDetails', None)
        permission['inherited'] = permission.pop('permissionDetails', [{'inherited': False}])[0]['inherited']
        permissions[permission['id']] = permission
      return permissions
    except (GAPI.fileNotFound, GAPI.forbidden, GAPI.internalError,
            GAPI.insufficientAdministratorPrivileges, GAPI.insufficientFilePermissions,
            GAPI.unknownError, GAPI.invalid) as e:
      _getMain().entityActionFailedWarning([Ent.USER, user, entityType, fileTitle], str(e), j, jcount)
      _incrStatistic(statistics, stat)
    except (GAPI.serviceNotAvailable, GAPI.authError, GAPI.domainPolicy) as e:
      _getMain().userDriveServiceNotEnabledWarning(user, str(e), i, count)
      _incrStatistic(statistics, stat)
    return None

  def permissionKVList(user, entityType, title, permission):
    permstr = f"{['noninherited', 'inherited'][permission['inherited']]}/{permission['role']}/{permission['type']}"
    if permission['type'] in {'group', 'user'}:
      permstr += f"/{permission['emailAddress']}"
    elif permission['type'] == 'domain':
      permstr += f"/{permission['domain']}"
    return [Ent.USER, user, entityType, title, Ent.PERMISSION, permstr]

  def isPermissionCopyable(kvList, permission):
    role = permission['role']
    emailAddress = permission.get('emailAddress', '')
    permissionType = permission['type']
    domain = ''
    if copyMoveOptions['excludePermissionsFromDomains'] or copyMoveOptions['includePermissionsFromDomains']:
      if permissionType in {'group', 'user'}:
        atLoc = emailAddress.find('@')
        if atLoc > 0:
          domain = emailAddress[atLoc+1:].lower()
      elif permissionType == 'domain':
        domain = permission.get('domain', '').lower()
    if role not in copyMoveOptions['copyPermissionRoles']:
      notCopiedMessage = f'role {role} not selected'
    elif permissionType not in copyMoveOptions['copyPermissionTypes']:
      notCopiedMessage = f'type {permissionType} not selected'
    elif permission['inherited'] and not copyMoveOptions[copyInherited]:
      notCopiedMessage = 'inherited not selected'
    elif not permission['inherited'] and copyMoveOptions[copyNonInherited] == COPY_NONINHERITED_PERMISSIONS_NEVER:
      notCopiedMessage = 'noninherited not selected'
    elif role == 'owner':
      if emailAddress == user or copyMoveOptions['destDriveId'] or not updateOwner:
        notCopiedMessage = f'role {role} copy not required/appropriate'
      else:
        permission['role'] = 'writer'
        return True
    elif updateOwner and emailAddress == user:
      notCopiedMessage = 'user is now owner'
    elif domain and domain in copyMoveOptions['excludePermissionsFromDomains']:
      notCopiedMessage = f'domain {domain} excluded'
    elif domain and copyMoveOptions['includePermissionsFromDomains'] and domain not in copyMoveOptions['includePermissionsFromDomains']:
      notCopiedMessage = f'domain {domain} not included'
    elif permission.pop('deleted', False) or (permissionType in {'group', 'user'} and not emailAddress):
      notCopiedMessage = f"{permissionType} deleted or has blank email address"
    elif ((copyInherited == 'copySheetProtectedRangesInheritedPermissions' and copyMoveOptions[copyInherited]) or
          (copyNonInherited == 'copySheetProtectedRangesNonInheritedPermissions' and
           copyMoveOptions[copyNonInherited] != COPY_NONINHERITED_PERMISSIONS_NEVER)):
      if role in {'organizer', 'fileOrganizer'}:
        permission['role'] = 'writer'
      return True
    elif role == 'organizer' and (not atTop or copyMoveOptions['destParentType'] != DEST_PARENT_SHAREDDRIVE_ROOT):
      notCopiedMessage = f'role {role} not copyable to {Ent.Plural(Ent.DRIVE_FILE_OR_FOLDER)}'
    elif role == 'fileOrganizer' and entityType == Ent.DRIVE_FILE:
      notCopiedMessage = f'role {role} not copyable to {Ent.Plural(entityType)}'
    elif role == 'fileOrganizer' and not copyMoveOptions['destDriveId']:
      notCopiedMessage = f'role {role} only copyable to {Ent.Singular(Ent.SHAREDDRIVE)} {Ent.Plural(Ent.DRIVE_FOLDER)}'
    else:
      return True
    if copyMoveOptions['showPermissionMessages']:
      _getMain().entityActionNotPerformedWarning(kvList, notCopiedMessage, 0, 0)
    return False

  def getNonInheritedPermissions(permissions):
    nonInheritedPermIds = set()
    for permissionId, permission in permissions.items():
      if not permission['inherited']:
        nonInheritedPermIds.add(permissionId)
    return nonInheritedPermIds

  def mapPermissionsDomains(srcPerm):
    if 'emailAddress' in srcPerm:
      sourceEmail = srcPerm['emailAddress'].lower()
      destEmail = copyMoveOptions['mapPermissionsEmails'].get(sourceEmail, None)
      if destEmail:
        srcPerm['emailAddress'] = destEmail
        return True
      email, domain = sourceEmail.split('@', 1)
      if domain in copyMoveOptions['mapPermissionsDomains']:
        srcPerm['emailAddress'] = f"{email}@{copyMoveOptions['mapPermissionsDomains'][domain]}"
        return True
    elif 'domain' in srcPerm:
      domain = srcPerm['domain'].lower()
      if domain in copyMoveOptions['mapPermissionsDomains']:
        srcPerm['domain'] = copyMoveOptions['mapPermissionsDomains'][domain]
        return True
    return False

  sourcePerms = getPermissions(fileId)
  if sourcePerms is None:
    return
  Ind.Increment()
  copySourcePerms = {}
  deleteTargetPermIds = set()
  updateTargetPerms = {}
  for permissionId, permission in sourcePerms.items():
    kvList = permissionKVList(user, entityType, newFileTitle, permission)
    if isPermissionCopyable(kvList, permission):
      copySourcePerms[permissionId] = permission
  if copyMoveOptions[copyNonInherited] == COPY_NONINHERITED_PERMISSIONS_ALWAYS:
    if copyMoveOptions['mapPermissionsDomains'] or copyMoveOptions['mapPermissionsEmails']:
      for permissionId in getNonInheritedPermissions(copySourcePerms):
        mapPermissionsDomains(copySourcePerms[permissionId])
  elif copyMoveOptions[copyNonInherited] in {COPY_NONINHERITED_PERMISSIONS_SYNC_ALL_FOLDERS,
                                             COPY_NONINHERITED_PERMISSIONS_SYNC_UPDATED_FOLDERS}:
    targetPerms = getPermissions(newFileId)
    if targetPerms is None:
      Ind.Decrement()
      return
    sourceNonInheritedPermIDs = getNonInheritedPermissions(copySourcePerms)
    targetNonInheritedPermIDs = getNonInheritedPermissions(targetPerms)
# Permissions in Source only
    if copyMoveOptions['mapPermissionsDomains'] or copyMoveOptions['mapPermissionsEmails']:
      for permissionId in sourceNonInheritedPermIDs-targetNonInheritedPermIDs:
        mapPermissionsDomains(copySourcePerms[permissionId])
# Permissions in Target only
    deleteTargetPermIds = targetNonInheritedPermIDs-sourceNonInheritedPermIDs
# Permissions in Source and Target
    for permissionId in targetNonInheritedPermIDs&sourceNonInheritedPermIDs:
      srcPerm = copySourcePerms[permissionId]
      if (copyMoveOptions['mapPermissionsDomains'] or copyMoveOptions['mapPermissionsEmails']) and mapPermissionsDomains(srcPerm):
        deleteTargetPermIds.add(permissionId)
        continue
      tgtPerm = targetPerms[permissionId]
      updatePerm = {}
      for field in ['expirationTime', 'role', 'view', 'pendingOwner']:
        if field in srcPerm:
          if field not in tgtPerm:
            if field != 'pendingOwner' or srcPerm[field]:
              updatePerm[field] = srcPerm[field]
          elif srcPerm[field] != tgtPerm[field]:
            updatePerm[field] = srcPerm[field]
        elif field in tgtPerm:
          if field == 'expirationTime':
            updatePerm['removeExpiration'] = True
          elif field == 'pendingOwner':
            updatePerm[field] = False
      if updatePerm:
        updateTargetPerms[permissionId] = targetPerms[permissionId]
        updateTargetPerms[permissionId].update(updatePerm)
        updateTargetPerms[permissionId]['updates'] = updatePerm
      copySourcePerms.pop(permissionId)
  deleteUpdateKwargs = {'useDomainAdminAccess': copyMoveOptions['useDomainAdminAccess']}
  action = Act.Get()
  Act.Set(Act.COPY)
  kcount = len(copySourcePerms)
  k = 0
  for permissionId, permission in copySourcePerms.items():
    k += 1
    kvList = permissionKVList(user, entityType, newFileTitle, permission)
    permission.pop('id')
    permission.pop('inherited')
    if copyMoveOptions['destDriveId']:
      permission.pop('pendingOwner', None)
    sendNotificationEmail = False
    while True:
      try:
        _getMain().callGAPI(drive.permissions(), 'create',
                 throwReasons=GAPI.DRIVE_ACCESS_THROW_REASONS+GAPI.DRIVE3_CREATE_ACL_THROW_REASONS,
#                 retryReasons=[GAPI.INVALID_SHARING_REQUEST],
                 useDomainAdminAccess=copyMoveOptions['useDomainAdminAccess'],
                 fileId=newFileId, sendNotificationEmail=sendNotificationEmail, emailMessage=None,
                 body=permission, fields='', supportsAllDrives=True)
        if copyMoveOptions['showPermissionMessages']:
          _getMain().entityActionPerformed(kvList, k, kcount)
        break
      except (GAPI.badRequest, GAPI.invalid, GAPI.fileNotFound, GAPI.forbidden, GAPI.internalError,
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
              GAPI.teamDrivesFolderSharingNotSupported, GAPI.invalidLinkVisibility, GAPI.abusiveContentRestriction) as e:
        _getMain().entityActionFailedWarning(kvList, str(e), k, kcount)
        break
      except GAPI.invalidSharingRequest as e:
        if not copyMoveOptions['sendEmailIfRequired'] or sendNotificationEmail or 'You are trying to invite' not in str(e):
          _getMain().entityActionFailedWarning(kvList, str(e), k, kcount)
          break
        sendNotificationEmail = True
      except (GAPI.serviceNotAvailable, GAPI.authError, GAPI.domainPolicy) as e:
        _getMain().userDriveServiceNotEnabledWarning(user, str(e), i, count)
        _incrStatistic(statistics, stat)
        Ind.Decrement()
        Act.Set(action)
        return
  Act.Set(Act.DELETE)
  kcount = len(deleteTargetPermIds)
  k = 0
  for permissionId in deleteTargetPermIds:
    k += 1
    kvList = permissionKVList(user, entityType, newFileTitle, targetPerms[permissionId])
    try:
      _getMain().callGAPI(drive.permissions(), 'delete',
               throwReasons=GAPI.DRIVE_ACCESS_THROW_REASONS+GAPI.DRIVE3_DELETE_ACL_THROW_REASONS,
               **deleteUpdateKwargs,
               fileId=newFileId, permissionId=permissionId,  supportsAllDrives=True)
      if copyMoveOptions['showPermissionMessages']:
        _getMain().entityActionPerformed(kvList, k, kcount)
    except (GAPI.fileNotFound, GAPI.forbidden, GAPI.internalError, GAPI.insufficientFilePermissions, GAPI.unknownError, GAPI.invalid,
            GAPI.badRequest, GAPI.notFound, GAPI.permissionNotFound, GAPI.cannotRemoveOwner,
            GAPI.cannotModifyInheritedTeamDrivePermission, GAPI.cannotModifyInheritedPermission,
            GAPI.insufficientAdministratorPrivileges, GAPI.sharingRateLimitExceeded, GAPI.cannotDeletePermission,
            GAPI.fileNeverWritable) as e:
      _getMain().entityActionFailedWarning(kvList, str(e), k, kcount)
    except (GAPI.serviceNotAvailable, GAPI.authError, GAPI.domainPolicy) as e:
      _getMain().userDriveServiceNotEnabledWarning(user, str(e), i, count)
      _incrStatistic(statistics, stat)
      Ind.Decrement()
      Act.Set(action)
      return
  Act.Set(Act.UPDATE)
  kcount = len(updateTargetPerms)
  k = 0
  for permissionId, permission in updateTargetPerms.items():
    k += 1
    kvList = permissionKVList(user, entityType, newFileTitle, permission)
    removeExpiration = permission['updates'].pop('removeExpiration', False)
    try:
      _getMain().callGAPI(drive.permissions(), 'update',
               bailOnInternalError=True,
               throwReasons=GAPI.DRIVE_ACCESS_THROW_REASONS+GAPI.DRIVE3_UPDATE_ACL_THROW_REASONS+[GAPI.FILE_NEVER_WRITABLE],
               removeExpiration=removeExpiration,
               **deleteUpdateKwargs,
               fileId=newFileId, permissionId=permissionId, body=permission['updates'], supportsAllDrives=True)
      if copyMoveOptions['showPermissionMessages']:
        _getMain().entityActionPerformed(kvList, k, kcount)
    except (GAPI.notFound, GAPI.permissionNotFound,
            GAPI.fileNotFound, GAPI.forbidden, GAPI.internalError, GAPI.insufficientFilePermissions, GAPI.unknownError,
            GAPI.fileNeverWritable, GAPI.badRequest, GAPI.cannotRemoveOwner,
            GAPI.cannotModifyInheritedTeamDrivePermission, GAPI.cannotModifyInheritedPermission,
            GAPI.insufficientAdministratorPrivileges, GAPI.sharingRateLimitExceeded) as e:
      _getMain().entityActionFailedWarning(kvList, str(e), k, kcount)
    except (GAPI.serviceNotAvailable, GAPI.authError, GAPI.domainPolicy) as e:
      _getMain().userDriveServiceNotEnabledWarning(user, str(e), i, count)
      _incrStatistic(statistics, stat)
      Ind.Decrement()
      Act.Set(action)
      return
  Act.Set(action)
  Ind.Decrement()

def _updateSheetProtectedRangesACLchange(sheet, user, i, count, j, jcount, fileId, fileTitle,
                                         aclAdd, permission):
  ptype = permission['type']
  updList = 'users' if ptype == 'user' else 'groups' if ptype == 'group' else ''
  if updList:
    emailAddress = permission['emailAddress']
  else:
    updDomain = (ptype == 'domain') and (permission['domain'] == GC.Values[GC.DOMAIN])
    if not updDomain:
      return
  addEditor = aclAdd and (permission['role'] not in {'reader', 'commenter'})
  updateProtectedRangeRequests = []
  try:
    result = _getMain().callGAPI(sheet.spreadsheets(), 'get',
                      throwReasons=GAPI.SHEETS_ACCESS_THROW_REASONS,
                      spreadsheetId=fileId, fields='sheets(protectedRanges)')
    for rsheet in result.get('sheets', []):
      for protectedRange in rsheet.get('protectedRanges', []):
        editors = protectedRange.get('editors', None)
        if editors is None:
          continue
        updReqd = False
        if updList:
          if addEditor:
            if updList not in editors:
              editors[updList] = [emailAddress]
              updReqd = True
            elif emailAddress not in editors[updList]:
              editors[updList].append(emailAddress)
              updReqd = True
          else:
            if emailAddress in editors.get(updList, []):
              editors[updList].remove(emailAddress)
              updReqd = True
        elif updDomain:
          editors['domainUsersCanEdit'] = addEditor
          updReqd = True
        if updReqd:
          updateProtectedRangeRequests.append({'updateProtectedRange': {'protectedRange': protectedRange, 'fields': 'editors'}})
    if updateProtectedRangeRequests:
      _getMain().callGAPI(sheet.spreadsheets(), 'batchUpdate',
               throwReasons=GAPI.SHEETS_ACCESS_THROW_REASONS,
               spreadsheetId=fileId, body={'requests': updateProtectedRangeRequests})
  except (GAPI.notFound, GAPI.forbidden, GAPI.permissionDenied,
          GAPI.internalError, GAPI.insufficientFilePermissions, GAPI.badRequest,
          GAPI.invalid, GAPI.invalidArgument, GAPI.failedPrecondition) as e:
    _getMain().entityActionFailedWarning([Ent.USER, user, Ent.SPREADSHEET, fileTitle], str(e), j, jcount)
  except (GAPI.serviceNotAvailable, GAPI.authError, GAPI.domainPolicy) as e:
    _getMain().userDriveServiceNotEnabledWarning(user, str(e), i, count)

def _getSheetProtectedRanges(sheet, user, i, count, j, jcount, fileId, fileTitle,
                             statistics, stat):
  sheetProtectedRanges = []
  try:
    result = _getMain().callGAPI(sheet.spreadsheets(), 'get',
                      throwReasons=GAPI.SHEETS_ACCESS_THROW_REASONS,
                      spreadsheetId=fileId, fields='sheets(protectedRanges)')
    for rsheet in result.get('sheets', []):
      for protectedRange in rsheet.get('protectedRanges', []):
        sheetProtectedRanges.append({'updateProtectedRange': {'protectedRange': protectedRange, 'fields': 'editors'}})
  except (GAPI.notFound, GAPI.forbidden, GAPI.permissionDenied,
          GAPI.internalError, GAPI.insufficientFilePermissions, GAPI.badRequest,
          GAPI.invalid, GAPI.invalidArgument, GAPI.failedPrecondition) as e:
    _getMain().entityActionFailedWarning([Ent.USER, user, Ent.SPREADSHEET, fileTitle], str(e), j, jcount)
    _incrStatistic(statistics, stat)
  except (GAPI.serviceNotAvailable, GAPI.authError, GAPI.domainPolicy) as e:
    _getMain().userDriveServiceNotEnabledWarning(user, str(e), i, count)
    _incrStatistic(statistics, stat)
  return sheetProtectedRanges

def _updateSheetProtectedRanges(sheet, user, i, count, j, jcount, newFileId, newFileTitle, sheetProtectedRanges,
                                statistics, stat):
  try:
    _getMain().callGAPI(sheet.spreadsheets(), 'batchUpdate',
             throwReasons=GAPI.SHEETS_ACCESS_THROW_REASONS,
             spreadsheetId=newFileId, body={'requests': sheetProtectedRanges})
  except (GAPI.notFound, GAPI.forbidden, GAPI.permissionDenied,
          GAPI.internalError, GAPI.insufficientFilePermissions, GAPI.badRequest,
          GAPI.invalid, GAPI.invalidArgument, GAPI.failedPrecondition) as e:
    _getMain().entityActionFailedWarning([Ent.USER, user, Ent.SPREADSHEET, newFileTitle], str(e), j, jcount)
    _incrStatistic(statistics, stat)
  except (GAPI.serviceNotAvailable, GAPI.authError, GAPI.domainPolicy) as e:
    _getMain().userDriveServiceNotEnabledWarning(user, str(e), i, count)
    _incrStatistic(statistics, stat)

def _identicalSourceTarget(fileId, targetChildren):
  for target in targetChildren:
    if fileId == target['id']:
      return True
  return False

def _checkForDuplicateTargetFile(drive, user, k, kcount, child, destFilename, targetChildren, copyMoveOptions, statistics):
  destFilenameLower = destFilename.lower()
  for target in targetChildren:
    if not target.get('processed', False) and destFilenameLower == target['name'].lower() and child['mimeType'] == target['mimeType']:
      target['processed'] = True
      if copyMoveOptions['duplicateFiles'] in [DUPLICATE_FILE_OVERWRITE_ALL, DUPLICATE_FILE_OVERWRITE_OLDER]:
        if (copyMoveOptions['duplicateFiles'] == DUPLICATE_FILE_OVERWRITE_OLDER) and (child['modifiedTime'] <= target['modifiedTime']):
          _getMain().entityActionNotPerformedWarning([Ent.USER, user, Ent.DRIVE_FILE, child['name'], Ent.DRIVE_FILE, target['name']], Msg.DUPLICATE, k, kcount)
          _incrStatistic(statistics, STAT_FILE_DUPLICATE)
          return True
        if not target['capabilities']['canDelete']:
          _getMain().entityActionNotPerformedWarning([Ent.USER, user, Ent.DRIVE_FILE, child['name'], Ent.DRIVE_FILE, target['name']], Msg.NOT_DELETABLE, k, kcount)
          _incrStatistic(statistics, STAT_FILE_FAILED)
          return True
        try:
          _getMain().callGAPI(drive.files(), 'delete',
                   throwReasons=GAPI.DRIVE_ACCESS_THROW_REASONS+[GAPI.FILE_NEVER_WRITABLE],
                   fileId=target['id'], supportsAllDrives=True)
          child['name'] = destFilename
          return False
        except (GAPI.fileNotFound, GAPI.forbidden, GAPI.internalError, GAPI.insufficientFilePermissions, GAPI.unknownError, GAPI.fileNeverWritable) as e:
          _getMain().entityActionNotPerformedWarning([Ent.USER, user, Ent.DRIVE_FILE, child['name'], Ent.DRIVE_FILE, target['name']], f'{Msg.NOT_DELETABLE}: {str(e)}', k, kcount)
          _incrStatistic(statistics, STAT_FILE_FAILED)
          return True
      if copyMoveOptions['duplicateFiles'] == DUPLICATE_FILE_DUPLICATE_NAME:
        child['name'] = destFilename
        return False
      if copyMoveOptions['duplicateFiles'] == DUPLICATE_FILE_UNIQUE_NAME:
        child['name'] = _getUniqueFilename(destFilename, child['mimeType'], targetChildren)
        return False
      #copyMoveOptions['duplicateFiles'] == DUPLICATE_FILE_SKIP
      _getMain().entityActionNotPerformedWarning([Ent.USER, user, Ent.DRIVE_FILE, child['name'], Ent.DRIVE_FILE, target['name']], Msg.DUPLICATE, k, kcount)
      _incrStatistic(statistics, STAT_FILE_DUPLICATE)
      return True
  child['name'] = destFilename
  return False

def _getCopyMoveParentInfo(drive, user, i, count, j, jcount, newParentId, statistics):
# newParentId is known to be a folder
  try:
    result = _getMain().callGAPI(drive.files(), 'get',
                      throwReasons=GAPI.DRIVE_GET_THROW_REASONS,
                      fileId=newParentId, fields='name,driveId,parents,modifiedTime', supportsAllDrives=True)
    if 'driveId' not in result:
      result['driveId'] = None
      if result['name'] == MY_DRIVE and not result.get('parents', []):
        result['destParentType'] = DEST_PARENT_MYDRIVE_ROOT
      else:
        result['destParentType'] = DEST_PARENT_MYDRIVE_FOLDER
    else:
      if result['name'] == TEAM_DRIVE and not result.get('parents', []):
        result['name'] = _getSharedDriveNameFromId(drive, result['driveId'])
        result['destParentType'] = DEST_PARENT_SHAREDDRIVE_ROOT
      else:
        result['destParentType'] = DEST_PARENT_SHAREDDRIVE_FOLDER
    return result
  except (GAPI.fileNotFound, GAPI.forbidden, GAPI.internalError, GAPI.insufficientFilePermissions,
          GAPI.unknownError, GAPI.cannotCopyFile, GAPI.badRequest, GAPI.fileNeverWritable) as e:
    _getMain().entityActionFailedWarning([Ent.USER, user, Ent.DRIVE_FILE_OR_FOLDER_ID, newParentId], str(e), j, jcount)
  except (GAPI.serviceNotAvailable, GAPI.authError, GAPI.domainPolicy) as e:
    _getMain().userDriveServiceNotEnabledWarning(user, str(e), i, count)
  _incrStatistic(statistics, STAT_FILE_FAILED)
  return None

def _getCopyMoveTargetInfo(drive, user, i, count, j, jcount, source, destFilename, newParentId, statistics, parentParms):
  try:
    return _getMain().callGAPIpages(drive.files(), 'list', 'files',
                         throwReasons=GAPI.DRIVE_USER_THROW_REASONS,
                         retryReasons=[GAPI.UNKNOWN_ERROR],
                         q=f"mimeType = '{source['mimeType']}' and name contains '{escapeDriveFileName(_getFilenamePrefix(destFilename))}' and trashed = false and '{newParentId}' in parents",
                         orderBy='folder desc,name,modifiedTime desc',
                         fields='nextPageToken,files(id,name,capabilities,mimeType,modifiedTime)',
                         **parentParms[DFA_SEARCHARGS])
  except (GAPI.fileNotFound, GAPI.forbidden, GAPI.internalError, GAPI.insufficientFilePermissions,
          GAPI.unknownError, GAPI.cannotCopyFile, GAPI.badRequest, GAPI.fileNeverWritable) as e:
    _getMain().entityActionFailedWarning([Ent.USER, user, Ent.DRIVE_FILE_OR_FOLDER_ID, newParentId], str(e), j, jcount)
  except (GAPI.serviceNotAvailable, GAPI.authError, GAPI.domainPolicy) as e:
    _getMain().userDriveServiceNotEnabledWarning(user, str(e), i, count)
  _incrStatistic(statistics, STAT_FILE_FAILED)
  return None

def _verifyUserIsOrganizer(drive, user, i, count, fileId):
  role = _getMain().UNKNOWN
  try:
    permissionId = getPermissionIdForEmail(user, i, count, user)
    role = _getMain().callGAPI(drive.permissions(), 'get',
                    throwReasons=GAPI.DRIVE_ACCESS_THROW_REASONS+[GAPI.BAD_REQUEST, GAPI.PERMISSION_NOT_FOUND, GAPI.INSUFFICIENT_ADMINISTRATOR_PRIVILEGES],
                    useDomainAdminAccess=False,
                    fileId=fileId, permissionId=permissionId, fields='role', supportsAllDrives=True)['role']
    if role == 'organizer':
      return True
    _getMain().entityActionNotPerformedWarning([Ent.USER, user, Ent.SHAREDDRIVE_ID, fileId, Ent.ROLE, role], Msg.ROLE_MUST_BE_ORGANIZER, i, count)
  except (GAPI.fileNotFound, GAPI.forbidden, GAPI.internalError, GAPI.insufficientFilePermissions, GAPI.unknownError,
          GAPI.badRequest, GAPI.insufficientAdministratorPrivileges) as e:
    _getMain().entityActionFailedWarning([Ent.USER, user, Ent.SHAREDDRIVE_ID, fileId], str(e), i, count)
  except GAPI.permissionNotFound:
    _getMain().entityDoesNotHaveItemWarning([Ent.USER, user, Ent.SHAREDDRIVE_ID, fileId, Ent.PERMISSION_ID, permissionId], i, count)
  except (GAPI.serviceNotAvailable, GAPI.authError, GAPI.domainPolicy):
    _getMain().entityActionNotPerformedWarning([Ent.USER, user], Msg.UNABLE_TO_GET_PERMISSION_ID.format(user), i, count)
  return False

def _getCopyFolderNonInheritedPermissions(copyMoveOptions, copyNonInherited, sourceModifiedTime, targetModifiedTime):
  if ((copyMoveOptions[copyNonInherited] == COPY_NONINHERITED_PERMISSIONS_NEVER) or
      ((copyMoveOptions[copyNonInherited] == COPY_NONINHERITED_PERMISSIONS_SYNC_UPDATED_FOLDERS) and
       (sourceModifiedTime <= targetModifiedTime))):
    return 'noCopyNonInheritedPermissions'
  return copyNonInherited

def _checkForExistingShortcut(drive, fileId, fileName, parentId):
  try:
    existingShortcuts = _getMain().callGAPI(drive.files(), 'list',
                                 throwReasons=GAPI.DRIVE_USER_THROW_REASONS+[GAPI.INVALID_QUERY, GAPI.INVALID],
                                 retryReasons=[GAPI.UNKNOWN_ERROR],
                                 supportsAllDrives=True, includeItemsFromAllDrives=True,
                                 q=f"shortcutDetails.targetId = '{fileId}' and trashed = False", fields='files(id,name,parents)')['files']
    for shortcut in existingShortcuts:
      if parentId in shortcut.get('parents', []) and fileName == shortcut['name']:
        return shortcut['id']
  except (GAPI.invalidQuery, GAPI.invalid, GAPI.serviceNotAvailable, GAPI.authError, GAPI.domainPolicy):
    pass
  return None

copyReturnItemMap = {
  'returnidonly': 'id',
  'returnlinkonly': 'webViewLink',
  }

# gam <UserTypeEntity> copy drivefile <DriveFileEntity>
#	[newfilename <DriveFileName>] (replacefilename <REMatchPattern> <RESubstitution>)*
#	[stripnameprefix <String>]
#	[excludetrashed]
#	[(csv [todrive <ToDriveAttribute>*] (addcsvdata <FieldName> <String>)*)) |
#	 (returnidonly|returnlinkonly)]
#	[summary [<Boolean>]] [showpermissionsmessages [<Boolean>]]
#	[<DriveFileParentAttribute>]
#	[mergewithparent [<Boolean>]] [recursive [depth <Number>]]
#	<DriveFileCopyAttribute>*
#	[skipids <DriveFileEntity>]
#	[copysubfiles [<Boolean>]] [filenamematchpattern <REMatchPattern>] [filemimetype [not] <MimeTypeList>]
#	[copysubfilesownedby
#	    any|me|others|
#	    users <EmailAddressList>|
#	    notusers <EmailAddressList>|
#	    regex <REMatchPattern>|
#	    notregex <REMatchPattern>]
#	[([start|starttime <Date>|<Time>] [end|endtime <Date>|<Time>])|(range <Date>|<Time> <Date>|<Time>)]|
#	[copysubfolders [<Boolean>]] [foldernamematchpattern <REMatchPattern>]
#	[copysubshortcuts [<Boolean>]] [shortcutnamematchpattern <REMatchPattern>]
#	[duplicatefiles overwriteolder|overwriteall|duplicatename|uniquename|skip]
#	[duplicatefolders merge|duplicatename|uniquename|skip]
#	[copiedshortcutspointtocopiedfiles [<Boolean>]]
#	[copyfilepermissions [<Boolean>]]
#	[copyfileinheritedpermissions [<Boolean>]
#	[copyfilenoninheritedpermissions [<Boolean>]
#	[copyfolderpermissions [<Boolean>]]
#	[copymergewithparentfolderpermissions [<Boolean>]]
#	[copymergedtopfolderpermissions [<Boolean>]]
#	[copytopfolderpermissions [<Boolean>]]
#	[copytopfolderiheritedpermissions [<Boolean>]]
#	[copytopfoldernoniheritedpermissions never|always|syncallfolders|syncupdatedfolders]
#	[copymergedsubfolderpermissions [<Boolean>]]
#	[copysubfolderpermissions [<Boolean>]]
#	[copysubfolderinheritedpermissions [<Boolean>]]
#	[copysubfoldernoniheritedpermissions never|always|syncallfolders|syncupdatedfolders]
#	[copypermissionroles <DriveFileACLRoleList>]
#	[copypermissiontypes <DriveFileACLTypeList>]
#	[excludepermissionsfromdomains|includepermissionsfromdomains <DomainNameList>]
#	(mappermissionsemail <EmailAddress> <EmailAddress>)* [mappermissionsemailfile <CSVFileInput> endcsv]
#	(mappermissionsdomain <DomainName> <DomainName>)*
#	[copysheetprotectedranges [<Boolean>]]
#	[copysheetprotectedrangesinheritedpermissions [<Boolean>]]
#	[copysheetprotectedrangesnoninheritedpermissions [<Boolean>]]
#	[sendemailifrequired [<Boolean>]]
#	[suppressnotselectedmessages [<Boolean>]]
#	[verifyorganizer [<Boolean>]]
def copyDriveFile(users):
  def _writeCSVData(user, oldName, oldId, newName, newId, mimeType):
    row = {'User': user, 'name': oldName, 'id': oldId,
           'newName': newName, 'newId': newId, 'mimeType': mimeType}
    if addCSVData:
      row.update(addCSVData)
    csvPF.WriteRow(row)

  def _cloneFolderCopy(drive, user, i, count, j, jcount,
                       source, targetChildren, newFolderName, newParentId, newParentName, mergeParentModifiedTime,
                       statistics, copyMoveOptions, atTop):
    folderId = source.pop('id')
    folderName = source['name']
    folderNameId = f'{folderName}({folderId})'
    kvList = [Ent.USER, user, Ent.DRIVE_FOLDER, folderNameId]
    newParentNameId = f'{newParentName}({newParentId})'
# Merge top parent folder
    if atTop and copyMoveOptions['mergeWithParent']:
      action = Act.Get()
      Act.Set(Act.COPY_MERGE)
      if not csvPF:
        _getMain().entityPerformActionModifierItemValueList(kvList, Act.MODIFIER_CONTENTS_WITH, [Ent.DRIVE_FOLDER, newParentNameId], j, jcount)
      else:
        _writeCSVData(user, folderName, folderId, newParentName, newParentId, MIMETYPE_GA_FOLDER)
      Act.Set(action)
      _incrStatistic(statistics, STAT_FOLDER_MERGED)
      if (copyMoveOptions['copyFolderPermissions'] and
          copyMoveOptions['copyMergeWithParentFolderPermissions'] and
          copyMoveOptions['destParentType'] != DEST_PARENT_MYDRIVE_ROOT):
        copyFolderNonInheritedPermissions =\
            _getCopyFolderNonInheritedPermissions(copyMoveOptions,
                                                  'copyTopFolderNonInheritedPermissions',
                                                  source['modifiedTime'], mergeParentModifiedTime)
        _copyPermissions(drive, user, i, count, j, jcount,
                         Ent.DRIVE_FOLDER, folderId, folderName, newParentId, newFolderName,
                         statistics, STAT_FOLDER_PERMISSIONS_FAILED,
                         copyMoveOptions, True,
                         'copyTopFolderInheritedPermissions',
                         copyFolderNonInheritedPermissions,
                         True)
      return (newParentId, newParentName, True)
# Merge parent folders
    if copyMoveOptions['duplicateFolders'] == DUPLICATE_FOLDER_MERGE:
      newFolderNameLower = newFolderName.lower()
      for target in targetChildren:
        if not target.get('processed', False) and newFolderNameLower == target['name'].lower() and source['mimeType'] == target['mimeType']:
          target['processed'] = True
          if target['capabilities']['canAddChildren']:
            newFolderId = target['id']
            action = Act.Get()
            Act.Set(Act.COPY_MERGE)
            if not csvPF:
              _getMain().entityModifierItemValueListActionPerformed(kvList, Act.MODIFIER_CONTENTS_WITH, [Ent.DRIVE_FOLDER, f'{newFolderName}({newFolderId})'], j, jcount)
            else:
              _writeCSVData(user, folderName, folderId, newFolderName, newFolderId, MIMETYPE_GA_FOLDER)
            Act.Set(action)
            _incrStatistic(statistics, STAT_FOLDER_MERGED)
            if (copyMoveOptions['copyFolderPermissions'] and
                copyMoveOptions[['copyMergedSubFolderPermissions', 'copyMergedTopFolderPermissions'][atTop]] and
                (not atTop or copyMoveOptions['destParentType'] != DEST_PARENT_MYDRIVE_ROOT)):
              copyFolderNonInheritedPermissions =\
                  _getCopyFolderNonInheritedPermissions(copyMoveOptions,
                                                        ['copySubFolderNonInheritedPermissions', 'copyTopFolderNonInheritedPermissions'][atTop],
                                                        source['modifiedTime'], target['modifiedTime'])
              _copyPermissions(drive, user, i, count, j, jcount,
                               Ent.DRIVE_FOLDER, folderId, folderName, newFolderId, newFolderName,
                               statistics, STAT_FOLDER_PERMISSIONS_FAILED,
                               copyMoveOptions, atTop,
                               ['copySubFolderInheritedPermissions', 'copyTopFolderInheritedPermissions'][atTop],
                               copyFolderNonInheritedPermissions,
                               False)
            return (newFolderId, newFolderName, True)
          _getMain().entityActionFailedWarning(kvList+[Ent.DRIVE_FOLDER, newParentNameId], Msg.NOT_WRITABLE, j, jcount)
          _incrStatistic(statistics, STAT_FOLDER_NOT_WRITABLE)
          return (None, None, False)
    elif copyMoveOptions['duplicateFolders'] == DUPLICATE_FOLDER_UNIQUE_NAME:
      newFolderName = _getUniqueFilename(newFolderName, source['mimeType'], targetChildren)
    elif copyMoveOptions['duplicateFolders'] == DUPLICATE_FOLDER_SKIP:
      targetChild = _targetFilenameExists(newFolderName, source['mimeType'], targetChildren)
      if targetChild is not None:
        _getMain().entityModifierItemValueListActionNotPerformedWarning(kvList, Act.MODIFIER_TO,
                                                             [Ent.DRIVE_FOLDER, newParentNameId, Ent.DRIVE_FOLDER, f"{newFolderName}({targetChild['id']})"],
                                                             Msg.DUPLICATE, j, jcount)
        _incrStatistic(statistics, STAT_FOLDER_DUPLICATE)
        return (None, None, False)
# Copy parent folders
    body = source.copy()
    body.pop('capabilities', None)
    if copyMoveOptions['sourceDriveId'] or copyMoveOptions['destDriveId']:
      body.pop('copyRequiresWriterPermission', None)
      body.pop('writersCanShare', None)
    body.pop('trashed', None)
    body.pop('driveId', None)
    body['name'] = newFolderName
    try:
      result = _getMain().callGAPI(drive.files(), 'create',
                        throwReasons=GAPI.DRIVE_USER_THROW_REASONS+[GAPI.FORBIDDEN, GAPI.INSUFFICIENT_PERMISSIONS, GAPI.INSUFFICIENT_PARENT_PERMISSIONS,
                                                                    GAPI.INTERNAL_ERROR, GAPI.STORAGE_QUOTA_EXCEEDED,
                                                                    GAPI.TEAMDRIVE_FILE_LIMIT_EXCEEDED, GAPI.TEAMDRIVE_HIERARCHY_TOO_DEEP, GAPI.BAD_REQUEST],
                        body=body, fields='id,webViewLink,modifiedTime', supportsAllDrives=True)
      newFolderId = result['id']
      if returnIdLink:
        _getMain().writeStdout(f'{result[returnIdLink]}\n')
      elif not csvPF:
        _getMain().entityModifierItemValueListActionPerformed(kvList, Act.MODIFIER_TO,
                                                   [Ent.DRIVE_FOLDER, newParentNameId, Ent.DRIVE_FOLDER, f'{newFolderName}({newFolderId})'],
                                                   j, jcount)
      else:
        _writeCSVData(user, folderName, folderId, newFolderName, newFolderId, body['mimeType'])
      _incrStatistic(statistics, STAT_FOLDER_COPIED_MOVED)
      if (copyMoveOptions['copyFolderPermissions'] and
          copyMoveOptions[['copySubFolderPermissions', 'copyTopFolderPermissions'][atTop]]):
        _copyPermissions(drive, user, i, count, j, jcount,
                         Ent.DRIVE_FOLDER, folderId, folderName, newFolderId, newFolderName,
                         statistics, STAT_FOLDER_PERMISSIONS_FAILED,
                         copyMoveOptions, False,
                         ['copySubFolderInheritedPermissions', 'copyTopFolderInheritedPermissions'][atTop],
                         ['copySubFolderNonInheritedPermissions', 'copyTopFolderNonInheritedPermissions'][atTop],
                         True)
      return (newFolderId, newFolderName, False)
    except (GAPI.forbidden, GAPI.insufficientFilePermissions, GAPI.insufficientParentPermissions, GAPI.internalError,
            GAPI.storageQuotaExceeded, GAPI.teamDriveFileLimitExceeded, GAPI.teamDriveHierarchyTooDeep, GAPI.badRequest) as e:
      _getMain().entityActionFailedWarning([Ent.USER, user, Ent.DRIVE_FOLDER, newFolderName], str(e), j, jcount)
    except (GAPI.serviceNotAvailable, GAPI.authError, GAPI.domainPolicy) as e:
      _getMain().userDriveServiceNotEnabledWarning(user, str(e), i, count)
    _incrStatistic(statistics, STAT_FOLDER_FAILED)
    copyMoveOptions['retainSourceFolders'] = True
    return (None, None, False)

  def _makeCopyShortcut(drive, user, k, kcount, entityType, childId, childName, newChildName, newParentId, newParentName, targetId):
    kvList = [Ent.USER, user, entityType, f'{childName}({childId})']
    if entityType == Ent.DRIVE_FILE:
      targetEntityType = Ent.DRIVE_FILE_SHORTCUT
      statShortcutCreated = STAT_FILE_SHORTCUT_CREATED
      statShortcutExists = STAT_FILE_SHORTCUT_EXISTS
    else:
      targetEntityType = Ent.DRIVE_FOLDER_SHORTCUT
      statShortcutCreated = STAT_FOLDER_SHORTCUT_CREATED
      statShortcutExists = STAT_FOLDER_SHORTCUT_EXISTS
    newParentNameId = f'{newParentName}({newParentId})'
    action = Act.Get()
    existingShortcut = _checkForExistingShortcut(drive, targetId, newChildName, newParentId)
    if existingShortcut:
      Act.Set(Act.CREATE_SHORTCUT)
      _getMain().entityModifierItemValueListActionPerformed(kvList, Act.MODIFIER_PREVIOUSLY_IN,
                                                 [Ent.DRIVE_FOLDER, newParentNameId, targetEntityType, f"{childName}({existingShortcut})"],
                                                 k, kcount)
      Act.Set(action)
      _incrStatistic(statistics, statShortcutExists)
      return
    body = {'name': newChildName, 'mimeType': MIMETYPE_GA_SHORTCUT,
            'parents': [newParentId], 'shortcutDetails': {'targetId': targetId}}
    try:
      result = _getMain().callGAPI(drive.files(), 'create',
                        throwReasons=GAPI.DRIVE_USER_THROW_REASONS+[GAPI.FORBIDDEN, GAPI.INSUFFICIENT_PERMISSIONS, GAPI.INSUFFICIENT_PARENT_PERMISSIONS,
                                                                    GAPI.INVALID, GAPI.BAD_REQUEST, GAPI.FILE_NOT_FOUND, GAPI.UNKNOWN_ERROR,
                                                                    GAPI.STORAGE_QUOTA_EXCEEDED, GAPI.TEAMDRIVES_SHARING_RESTRICTION_NOT_ALLOWED,
                                                                    GAPI.TEAMDRIVE_FILE_LIMIT_EXCEEDED, GAPI.TEAMDRIVE_HIERARCHY_TOO_DEEP,
                                                                    GAPI.SHORTCUT_TARGET_INVALID, GAPI.SHARE_OUT_WARNING],
                        body=body, fields='id', supportsAllDrives=True)
      Act.Set(Act.CREATE_SHORTCUT)
      _getMain().entityModifierItemValueListActionPerformed(kvList, Act.MODIFIER_IN,
                                                 [Ent.DRIVE_FOLDER, newParentNameId, targetEntityType, f"{newChildName}({result['id']})"],
                                                 k, kcount)
      Act.Set(action)
      _incrStatistic(statistics, statShortcutCreated)
    except (GAPI.forbidden, GAPI.insufficientFilePermissions, GAPI.insufficientParentPermissions,
            GAPI.invalid, GAPI.badRequest, GAPI.fileNotFound, GAPI.unknownError,
            GAPI.storageQuotaExceeded, GAPI.teamDrivesSharingRestrictionNotAllowed,
            GAPI.teamDriveFileLimitExceeded, GAPI.teamDriveHierarchyTooDeep,
            GAPI.shortcutTargetInvalid, GAPI.shareOutWarning) as e:
      _getMain().entityActionFailedWarning(kvList+[Ent.DRIVE_FILE_SHORTCUT, childName], str(e), k, kcount)
      _incrStatistic(statistics, STAT_FILE_FAILED)

  def _checkChildCopyAllowed(childMimeType, childName, child):
    if childMimeType == MIMETYPE_GA_FOLDER:
      if not copyMoveOptions['copySubFolders']:
        return False
      nameMatchPattern = copyMoveOptions['folderNameMatchPattern']
    elif childMimeType == MIMETYPE_GA_SHORTCUT:
      if not copyMoveOptions['copySubShortcuts']:
        return False
      nameMatchPattern = copyMoveOptions['shortcutNameMatchPattern']
    else:
      if not copyMoveOptions['copySubFiles']:
        return False
      if copyMoveOptions['copySubFilesOwnedBy'] and child.get('driveId', None) is None:
        if copyMoveOptions['copySubFilesOwnedBy']['mode'] == 'bool':
          if child.get('ownedByMe', False) != copyMoveOptions['copySubFilesOwnedBy']['value']:
            return False
        else:
          childOwner = child.get('owners', [])
          if childOwner:
            childOwner = childOwner[0].get('emailAddress', '').lower()
          else:
            childOwner = ''
          if copyMoveOptions['copySubFilesOwnedBy']['mode'] == 'users':
            if childOwner not in copyMoveOptions['copySubFilesOwnedBy']['value']:
              return False
          elif copyMoveOptions['copySubFilesOwnedBy']['mode'] == 'notusers':
            if childOwner in copyMoveOptions['copySubFilesOwnedBy']['value']:
              return False
          elif copyMoveOptions['copySubFilesOwnedBy']['mode'] == 'regex':
            if not copyMoveOptions['copySubFilesOwnedBy']['value'].match(childOwner):
              return False
          else: # elif copyMoveOptions['copySubFilesOwnedBy']['mode'] == 'notregex':
            if copyMoveOptions['copySubFilesOwnedBy']['value'].match(childOwner):
              return False
      if not copyMoveOptions['mimeTypeCheck'].Check(childMimeType):
        return False
      if copyMoveOptions['checkModifiedTime']:
        childModifiedTime = child.get('modifiedTime', None)
        if not childModifiedTime:
          return False
        childModifiedTime = _getMain().formatLocalTime(childModifiedTime)
        if ((copyMoveOptions['startEndTime'].startTime is not None and childModifiedTime < copyMoveOptions['startEndTime'].startTime) or
            (copyMoveOptions['startEndTime'].endTime is not None and childModifiedTime > copyMoveOptions['startEndTime'].endTime)):
          return False
      nameMatchPattern = copyMoveOptions['fileNameMatchPattern']
    return not nameMatchPattern or nameMatchPattern.match(childName)

  def _recursiveFolderCopy(drive, user, i, count, j, jcount,
                           source, targetChildren, newFolderName, newParentId, newParentName, mergeParentModifiedTime, atTop, depth):
    folderId = source['id']
    newFolderId, newFolderName, existingTargetFolder = _cloneFolderCopy(drive, user, i, count, j, jcount,
                                                                        source, targetChildren, newFolderName,
                                                                        newParentId, newParentName, mergeParentModifiedTime,
                                                                        statistics, copyMoveOptions, atTop)
    if newFolderId is None:
      return
    newFolderNameId = f'{newFolderName}({newFolderId})'
    copiedSourceFiles[folderId] = newFolderId
    copiedTargetFiles.add(newFolderId) # Don't recopy folder copied into a sub-folder
    if maxdepth != -1 and depth > maxdepth:
      return
    depth += 1
    sourceChildren = _getMain().callGAPIpages(drive.files(), 'list', 'files',
                                   throwReasons=GAPI.DRIVE_USER_THROW_REASONS,
                                   retryReasons=[GAPI.UNKNOWN_ERROR],
                                   q=_getMain().WITH_PARENTS.format(folderId),
                                   orderBy='folder desc,name,modifiedTime desc',
                                   fields='nextPageToken,files(id,name,parents,appProperties,capabilities,contentHints,copyRequiresWriterPermission,'\
                                     'description,folderColorRgb,mimeType,modifiedTime,ownedByMe,properties,starred,driveId,trashed,viewedByMeTime,writersCanShare,'\
                                     'shortcutDetails(targetId,targetMimeType),owners(emailAddress))',
                                   pageSize=GC.Values[GC.DRIVE_MAX_RESULTS], **sourceSearchArgs)
    kcount = len(sourceChildren)
    if kcount > 0:
      if existingTargetFolder:
        subTargetChildren = _getMain().callGAPIpages(drive.files(), 'list', 'files',
                                          throwReasons=GAPI.DRIVE_USER_THROW_REASONS,
                                          retryReasons=[GAPI.UNKNOWN_ERROR],
                                          q=_getMain().ANY_NON_TRASHED_WITH_PARENTS.format(newFolderId),
                                          orderBy='folder desc,name,modifiedTime desc',
                                          fields='nextPageToken,files(id,name,capabilities,mimeType,modifiedTime)',
                                          **parentParms[DFA_SEARCHARGS])
      else:
        subTargetChildren = []
      Ind.Increment()
      k = 0
      for child in sourceChildren:
        k += 1
        childId = child['id']
        childName = child['name']
        childNameId = f'{childName}({childId})'
        childMimeType = child['mimeType']
        if childId in copiedTargetFiles: # Don't recopy file/folder copied into a sub-folder
          continue
        kvList = [Ent.USER, user, _getMain()._getEntityMimeType(child), childNameId]
        if childId in skipFileIdEntity['list']:
          if not suppressNotSelectedMessages:
            _getMain().entityActionNotPerformedWarning(kvList, Msg.IN_SKIPIDS, k, kcount)
          _incrStatistic(statistics, STAT_FILE_IN_SKIPIDS)
          continue
        if not _checkChildCopyAllowed(childMimeType, childName, child):
          if not suppressNotSelectedMessages:
            _getMain().entityActionNotPerformedWarning(kvList, Msg.NOT_SELECTED, k, kcount)
          continue
        child.pop('ownedByMe', None)
        child.pop('owners', None)
        trashed = child.pop('trashed', False)
        if (childId == newFolderId) or (excludeTrashed and trashed):
          _getMain().entityActionNotPerformedWarning(kvList,
                                          [Msg.NOT_COPYABLE, Msg.IN_TRASH_AND_EXCLUDE_TRASHED][trashed], k, kcount)
          _incrStatistic(statistics, STAT_FILE_NOT_COPYABLE_MOVABLE)
          continue
        if copyMoveOptions['replaceFilename']:
          newChildName = processFilenameReplacements(childName, copyMoveOptions['replaceFilename'])
        else:
          newChildName = childName
# If source child has already been copied, make shortcut to its copy
        if childId in copiedSourceFiles:
          _makeCopyShortcut(drive, user, k, kcount, _getMain()._getEntityMimeType(child), childId, childName,
                            newChildName, newFolderId, newFolderName, copiedSourceFiles[childId])
          continue
        child.pop('parents', [])
        child['parents'] = [newFolderId]
        if childMimeType == MIMETYPE_GA_FOLDER:
          _recursiveFolderCopy(drive, user, i, count, k, kcount,
                               child, subTargetChildren, newChildName, newFolderId, newFolderName, child['modifiedTime'],
                               False, depth)
        elif childMimeType == MIMETYPE_GA_SHORTCUT:
          shortcutsToCreate.append({'childName': childName, 'childId': childId, 'newChildName': newChildName,
                                    'newFolderId': newFolderId, 'newFolderName': newFolderName,
                                    'targetId': child['shortcutDetails']['targetId'], 'mimeType': child['shortcutDetails']['targetMimeType']})
        else:
          if not child.pop('capabilities')['canCopy']:
            _getMain().entityActionFailedWarning(kvList, Msg.NOT_COPYABLE, k, kcount)
            _incrStatistic(statistics, STAT_FILE_NOT_COPYABLE_MOVABLE)
            continue
          if existingTargetFolder:
            if _checkForDuplicateTargetFile(drive, user, k, kcount, child, newChildName, subTargetChildren, copyMoveOptions, statistics):
              continue
          else:
            child['name'] = newChildName
          child.pop('id')
          if copyMoveOptions['destDriveId']:
            child.pop('copyRequiresWriterPermission', None)
            child.pop('writersCanShare', None)
          child.pop('driveId', None)
          if childMimeType == MIMETYPE_GA_SHORTCUT:
            child.pop('folderColorRgb', None)
          child.pop('mimeType')
          try:
            result = _getMain().callGAPI(drive.files(), 'copy',
                              bailOnInternalError=True,
                              throwReasons=GAPI.DRIVE_COPY_THROW_REASONS+[GAPI.INTERNAL_ERROR, GAPI.INSUFFICIENT_PARENT_PERMISSIONS,
                                                                          GAPI.TEAMDRIVES_SHORTCUT_FILE_NOT_SUPPORTED, GAPI.SHARE_OUT_WARNING],
                              fileId=childId, body=child, fields='id,name', supportsAllDrives=True)
            if not csvPF:
              _getMain().entityModifierItemValueListActionPerformed(kvList, Act.MODIFIER_TO,
                                                         [Ent.DRIVE_FOLDER, newFolderNameId, Ent.DRIVE_FILE, f"{result['name']}({result['id']})"],
                                                         k, kcount)
            else:
              _writeCSVData(user, childName, childId, result['name'], result['id'], childMimeType)
            _incrStatistic(statistics, STAT_FILE_COPIED_MOVED)
            copiedSourceFiles[childId] = result['id']
            copiedTargetFiles.add(result['id']) # Don't recopy file copied into a sub-folder
            if (childMimeType == MIMETYPE_GA_SPREADSHEET and
                (copyMoveOptions['copySheetProtectedRangesInheritedPermissions'] or
                 copyMoveOptions['copySheetProtectedRangesNonInheritedPermissions'] != COPY_NONINHERITED_PERMISSIONS_NEVER)):
              protectedSheetRanges = _getSheetProtectedRanges(sheet, user, i, count, k, kcount, childId, childName,
                                                              statistics, STAT_FILE_PROTECTEDRANGES_FAILED)
              _copyPermissions(drive, user, i, count, k, kcount,
                               Ent.DRIVE_FILE, childId, childName, result['id'], result['name'],
                               statistics, STAT_FILE_PERMISSIONS_FAILED,
                               copyMoveOptions, False,
                               'copySheetProtectedRangesInheritedPermissions',
                               'copySheetProtectedRangesNonInheritedPermissions',
                               True)
              _updateSheetProtectedRanges(sheet, user, i, count, k, kcount, result['id'], result['name'], protectedSheetRanges,
                                          statistics, STAT_FILE_PROTECTEDRANGES_FAILED)
            elif copyMoveOptions['copyFilePermissions']:
              _copyPermissions(drive, user, i, count, k, kcount,
                               Ent.DRIVE_FILE, childId, childName, result['id'], result['name'],
                               statistics, STAT_FILE_PERMISSIONS_FAILED,
                               copyMoveOptions, False,
                               'copyFileInheritedPermissions',
                               'copyFileNonInheritedPermissions',
                               True)
          except (GAPI.fileNotFound, GAPI.forbidden, GAPI.internalError, GAPI.insufficientFilePermissions,
                  GAPI.insufficientParentPermissions, GAPI.unknownError,
                  GAPI.invalid, GAPI.cannotCopyFile, GAPI.badRequest, GAPI.responsePreparationFailure, GAPI.fileNeverWritable, GAPI.fieldNotWritable,
                  GAPI.teamDrivesSharingRestrictionNotAllowed, GAPI.rateLimitExceeded, GAPI.userRateLimitExceeded,
                  GAPI.internalError, GAPI.teamDrivesShortcutFileNotSupported, GAPI.shareOutWarning) as e:
            _getMain().entityActionFailedWarning(kvList, str(e), k, kcount)
            _incrStatistic(statistics, STAT_FILE_FAILED)
          except (GAPI.storageQuotaExceeded, GAPI.teamDriveFileLimitExceeded, GAPI.teamDriveHierarchyTooDeep) as e:
            _getMain().entityActionFailedWarning(kvList, str(e), k, kcount)
            _incrStatistic(statistics, STAT_FILE_FAILED)
            break
      Ind.Decrement()

  fileIdEntity = getDriveFileEntity()
  csvPF = None
  addCSVData = {}
  returnIdLink = None
  copyBody = {}
  parentBody = {}
  parentParms = initDriveFileAttributes()
  copyParameters = initDriveFileAttributes()
  copyMoveOptions = initCopyMoveOptions(True)
  excludeTrashed = newParentsSpecified = recursive = suppressNotSelectedMessages = False
  maxdepth = -1
  verifyOrganizer = True
  skipFileIdEntity = initDriveFileEntity()
  while Cmd.ArgumentsRemaining():
    myarg = _getMain().getArgument()
    if getCopyMoveOptions(myarg, copyMoveOptions):
      pass
    elif getDriveFileParentAttribute(myarg, parentParms):
      newParentsSpecified = True
    elif myarg in copyReturnItemMap:
      returnIdLink = copyReturnItemMap[myarg]
    elif myarg == 'excludetrashed':
      excludeTrashed = True
    elif myarg == 'recursive':
      recursive = _getMain().getBoolean()
    elif myarg == 'depth':
      maxdepth = _getMain().getInteger(minVal=-1)
    elif myarg == 'skipids':
      skipFileIdEntity = getDriveFileEntity()
    elif myarg == 'convert':
      _getMain().deprecatedArgument(myarg)
    elif myarg == 'csv':
      csvPF = _getMain().CSVPrintFile()
    elif csvPF and myarg == 'todrive':
      csvPF.GetTodriveParameters()
    elif csvPF and myarg == 'addcsvdata':
      _getMain().getAddCSVData(addCSVData)
    elif myarg == 'suppressnotselectedmessages':
      suppressNotSelectedMessages = _getMain().getBoolean()
    elif getDriveFileCopyAttribute(myarg, copyBody, copyParameters):
      pass
    elif myarg == 'verifyorganizer':
      verifyOrganizer = _getMain().getBoolean()
    else:
      _getMain().unknownArgumentExit()
  if csvPF:
    csvPF.SetTitles(['User', 'name', 'id', 'newName', 'newId', 'mimeType'])
    if addCSVData:
      csvPF.AddTitles(sorted(addCSVData.keys()))
  i, count, users = _getMain().getEntityArgument(users)
  for user in users:
    i += 1
    origUser = user
    user, drive, jcount = _validateUserGetFileIDs(user, i, count, fileIdEntity,
                                                  entityType=Ent.DRIVE_FILE_OR_FOLDER if returnIdLink is None else None)
    if jcount == 0:
      continue
    if not _getDriveFileParentInfo(drive, user, i, count, parentBody, parentParms):
      continue
    if (copyMoveOptions['copySheetProtectedRangesInheritedPermissions'] or
        copyMoveOptions['copySheetProtectedRangesNonInheritedPermissions'] != COPY_NONINHERITED_PERMISSIONS_NEVER):
      _, sheet = _getMain().buildGAPIServiceObject(API.SHEETS, user, i, count)
      if not sheet:
        continue
    copiedSourceFiles = {}
    copiedTargetFiles = set()
    shortcutsToCreate = []
    statistics = _initStatistics()
    if skipFileIdEntity['query'] or skipFileIdEntity[ROOT]:
      _validateUserGetFileIDs(origUser, i, count, skipFileIdEntity, drive=drive)
    Ind.Increment()
    j = 0
    for fileId in fileIdEntity['list']:
      j += 1
      try:
        source = _getMain().callGAPI(drive.files(), 'get',
                          throwReasons=GAPI.DRIVE_GET_THROW_REASONS,
                          fileId=fileId,
                          fields='id,name,parents,appProperties,capabilities,contentHints,copyRequiresWriterPermission,'\
                            'description,mimeType,modifiedTime,properties,starred,driveId,trashed,viewedByMeTime,writersCanShare',
                          supportsAllDrives=True)
# Source at root of Shared Drive?
        sourceMimeType = source['mimeType']
        if sourceMimeType == MIMETYPE_GA_FOLDER and source.get('driveId') and source['name'] == TEAM_DRIVE and not source.get('parents', []):
          copyMoveOptions['sourceIsMyDriveSharedDrive'] = True
          source['name'] = _getSharedDriveNameFromId(drive, source['driveId'])
        sourceName = source['name']
        sourceNameId = f"{sourceName}({source['id']})"
        copyMoveOptions['sourceDriveId'] = source.get('driveId')
        kvList = [Ent.USER, user, _getMain()._getEntityMimeType(source), sourceNameId]
        if fileId in copiedSourceFiles:
          _getMain().entityActionNotPerformedWarning(kvList, Msg.DUPLICATE, j, jcount)
          _incrStatistic(statistics, STAT_FILE_DUPLICATE)
          continue
        if fileId in skipFileIdEntity['list']:
          _getMain().entityActionNotPerformedWarning(kvList, Msg.IN_SKIPIDS, j, jcount)
          _incrStatistic(statistics, STAT_FILE_IN_SKIPIDS)
          continue
        trashed = source.pop('trashed', False)
        if excludeTrashed and trashed:
          _getMain().entityActionNotPerformedWarning(kvList, Msg.IN_TRASH_AND_EXCLUDE_TRASHED, j, jcount)
          _incrStatistic(statistics, STAT_FILE_NOT_COPYABLE_MOVABLE)
          continue
        if copyMoveOptions['sourceDriveId']:
# If copying from a Shared Drive, user has to be an organizer
          if verifyOrganizer and not _verifyUserIsOrganizer(drive, user, i, count, copyMoveOptions['sourceDriveId']):
            _incrStatistic(statistics, STAT_USER_NOT_ORGANIZER)
            continue
          sourceSearchArgs = {'driveId': copyMoveOptions['sourceDriveId'], 'corpora': 'drive', 'includeItemsFromAllDrives': True, 'supportsAllDrives': True}
        else:
          sourceSearchArgs = {}
        sourceParents = source.pop('parents', [])
        if newParentsSpecified:
          newParents = parentBody['parents']
          numNewParents = len(newParents)
          if numNewParents > 1:
            _getMain().entityActionNotPerformedWarning(kvList, Msg.MULTIPLE_PARENTS_SPECIFIED.format(numNewParents), j, jcount)
            _incrStatistic(statistics, STAT_FILE_FAILED)
            continue
        else:
          newParents = sourceParents if sourceParents else [ROOT]
        source['parents'] = newParents
        newParentId = newParents[0]
        dest = _getCopyMoveParentInfo(drive, user, i, count, j, jcount, newParentId, statistics)
        if dest is None:
          continue
        newParentName = dest['name']
        newParentNameId = f'{newParentName}({newParentId})'
        copyMoveOptions['destDriveId'] = dest['driveId']
        copyMoveOptions['destParentType'] = dest['destParentType']
        if copyMoveOptions['destDriveId']:
# If copying to a Shared Drive, user has to be an organizer
          if verifyOrganizer and not _verifyUserIsOrganizer(drive, user, i, count, copyMoveOptions['destDriveId']):
            _incrStatistic(statistics, STAT_USER_NOT_ORGANIZER)
            continue
          if not parentParms[DFA_SEARCHARGS]:
            parentParms[DFA_SEARCHARGS] = {'driveId': copyMoveOptions['destDriveId'], 'corpora': 'drive',
                                           'includeItemsFromAllDrives': True, 'supportsAllDrives': True}
        if copyMoveOptions['newFilename']:
          destName = copyMoveOptions['newFilename']
        elif (sourceMimeType == MIMETYPE_GA_FOLDER) and copyMoveOptions['mergeWithParent']:
          destName = dest['name']
        elif ((newParentsSpecified and newParentId not in sourceParents) or
              ((newParentId in sourceParents and
                (sourceMimeType == MIMETYPE_GA_FOLDER and copyMoveOptions['duplicateFolders'] != DUPLICATE_FOLDER_MERGE) or
                (sourceMimeType != MIMETYPE_GA_FOLDER and copyMoveOptions['duplicateFiles'] not in [DUPLICATE_FILE_OVERWRITE_ALL, DUPLICATE_FILE_OVERWRITE_OLDER])))):
          if copyMoveOptions['replaceFilename']:
            destName = processFilenameReplacements(sourceName, copyMoveOptions['replaceFilename'])
          else:
            destName = sourceName
        elif copyMoveOptions['replaceFilename']:
          destName = processFilenameReplacements(sourceName, copyMoveOptions['replaceFilename'])
        else:
          destName = f'Copy of {sourceName}'
        if copyMoveOptions['stripNamePrefix'] and destName.startswith(copyMoveOptions['stripNamePrefix']):
          destName = destName[len(copyMoveOptions['stripNamePrefix']):]
        targetChildren = _getCopyMoveTargetInfo(drive, user, i, count, j, jcount, source, destName, newParentId, statistics, parentParms)
        if targetChildren is None:
          continue
# Copy folder
        if sourceMimeType == MIMETYPE_GA_FOLDER:
          copiedTargetFiles.add(newParentId) # Don't recopy folder copied into a sub-folder
          if fileId == newParentId:
            _getMain().entityActionNotPerformedWarning(kvList, Msg.NOT_COPYABLE_INTO_ITSELF, j, jcount)
            _incrStatistic(statistics, STAT_FOLDER_FAILED)
            continue
          if copyMoveOptions['duplicateFolders'] == DUPLICATE_FOLDER_MERGE:
            if _identicalSourceTarget(fileId, targetChildren):
              _getMain().entityActionNotPerformedWarning(kvList, Msg.NOT_COPYABLE_SAME_NAME_CURRENT_FOLDER_MERGE, j, jcount)
              _incrStatistic(statistics, STAT_FOLDER_FAILED)
              continue
          elif copyMoveOptions['duplicateFolders'] == DUPLICATE_FOLDER_UNIQUE_NAME:
            destName = _getUniqueFilename(destName, sourceMimeType, targetChildren)
          elif copyMoveOptions['duplicateFolders'] == DUPLICATE_FOLDER_SKIP:
            targetChild = _targetFilenameExists(destName, sourceMimeType, targetChildren)
            if targetChild is not None:
              _getMain().entityModifierItemValueListActionNotPerformedWarning(kvList, Act.MODIFIER_TO,
                                                                   [Ent.DRIVE_FOLDER, newParentNameId, Ent.DRIVE_FOLDER, f"{destName}({targetChild['id']})"],
                                                                   Msg.DUPLICATE, j, jcount)
              _incrStatistic(statistics, STAT_FOLDER_DUPLICATE)
              continue
          if recursive:
            _recursiveFolderCopy(drive, user, i, count, j, jcount,
                                 source, targetChildren, destName, newParentId, newParentName, dest['modifiedTime'],
                                 True, 0)
            kcount = len(shortcutsToCreate)
            if kcount > 0:
              _getMain().entityPerformActionNumItems([Ent.USER, user], kcount, Ent.DRIVE_FILE_SHORTCUT, i, count)
              Ind.Increment()
              k = 0
              for shortcut in shortcutsToCreate:
                k += 1
                targetId = shortcut['targetId']
                if targetId in copiedSourceFiles and copyMoveOptions['copiedShortcutsPointToCopiedFiles']:
                  targetId = copiedSourceFiles[targetId]
                _makeCopyShortcut(drive, user, k, kcount, _getMain()._getEntityMimeType(shortcut), shortcut['childId'], shortcut['childName'],
                                  shortcut['newChildName'], shortcut['newFolderId'], shortcut['newFolderName'], targetId)
              Ind.Decrement()
          else:
            source.update(copyBody)
            _cloneFolderCopy(drive, user, i, count, j, jcount,
                             source, targetChildren, destName, newParentId, newParentName, dest['modifiedTime'],
                             statistics, copyMoveOptions, True)
# Copy file
        else:
          if not source.pop('capabilities')['canCopy']:
            _getMain().entityActionFailedWarning(kvList, Msg.NOT_COPYABLE, j, jcount)
            _incrStatistic(statistics, STAT_FILE_NOT_COPYABLE_MOVABLE)
            continue
          if copyMoveOptions['duplicateFiles'] in [DUPLICATE_FILE_OVERWRITE_ALL, DUPLICATE_FILE_OVERWRITE_OLDER] and _identicalSourceTarget(fileId, targetChildren):
            _getMain().entityActionNotPerformedWarning(kvList, Msg.NOT_COPYABLE_SAME_NAME_CURRENT_FOLDER_OVERWRITE, j, jcount)
            _incrStatistic(statistics, STAT_FILE_FAILED)
            continue
          if _checkForDuplicateTargetFile(drive, user, j, jcount, source, destName, targetChildren, copyMoveOptions, statistics):
            continue
          sourceId = source.pop('id')
          sourceMimeType = source.pop('mimeType')
          if copyMoveOptions['destDriveId']:
            source.pop('copyRequiresWriterPermission', None)
            source.pop('writersCanShare', None)
          source.pop('driveId', None)
          if sourceMimeType == MIMETYPE_GA_SHORTCUT:
            source.pop('folderColorRgb', None)
          source.update(copyBody)
          result = _getMain().callGAPI(drive.files(), 'copy',
                            bailOnInternalError=True,
                            throwReasons=GAPI.DRIVE_COPY_THROW_REASONS+[GAPI.INTERNAL_ERROR, GAPI.INSUFFICIENT_PARENT_PERMISSIONS],
                            fileId=fileId,
                            ignoreDefaultVisibility=copyParameters[DFA_IGNORE_DEFAULT_VISIBILITY],
                            keepRevisionForever=copyParameters[DFA_KEEP_REVISION_FOREVER],
                            body=source, fields='id,name,webViewLink', supportsAllDrives=True)
          if returnIdLink:
            _getMain().writeStdout(f'{result[returnIdLink]}\n')
          elif not csvPF:
            _getMain().entityModifierItemValueListActionPerformed(kvList, Act.MODIFIER_TO,
                                                       [Ent.DRIVE_FOLDER, newParentNameId, Ent.DRIVE_FILE, f"{result['name']}({result['id']})"],
                                                       j, jcount)
          else:
            _writeCSVData(user, sourceName, sourceId, result['name'], result['id'], sourceMimeType)
          _incrStatistic(statistics, STAT_FILE_COPIED_MOVED)
          if (sourceMimeType == MIMETYPE_GA_SPREADSHEET and
              (copyMoveOptions['copySheetProtectedRangesInheritedPermissions'] or
               copyMoveOptions['copySheetProtectedRangesNonInheritedPermissions'] != COPY_NONINHERITED_PERMISSIONS_NEVER)):
            protectedSheetRanges = _getSheetProtectedRanges(sheet, user, i, count, j, jcount, sourceId, sourceName,
                                                            statistics, STAT_FILE_PROTECTEDRANGES_FAILED)
            _copyPermissions(drive, user, i, count, j, jcount,
                             Ent.DRIVE_FILE, sourceId, sourceName, result['id'], result['name'],
                             statistics, STAT_FILE_PERMISSIONS_FAILED,
                             copyMoveOptions, False,
                             'copySheetProtectedRangesInheritedPermissions',
                             'copySheetProtectedRangesNonInheritedPermissions',
                             True)
            _updateSheetProtectedRanges(sheet, user, i, count, j, jcount, result['id'], result['name'], protectedSheetRanges,
                                        statistics, STAT_FILE_PROTECTEDRANGES_FAILED)
          elif copyMoveOptions['copyFilePermissions']:
            _copyPermissions(drive, user, i, count, j, jcount,
                             Ent.DRIVE_FILE, sourceId, sourceName, result['id'], result['name'],
                             statistics, STAT_FILE_PERMISSIONS_FAILED,
                             copyMoveOptions, False,
                             'copyFileInheritedPermissions',
                             'copyFileNonInheritedPermissions',
                             True)
      except (GAPI.fileNotFound, GAPI.forbidden, GAPI.internalError, GAPI.insufficientFilePermissions,
              GAPI.insufficientParentPermissions, GAPI.unknownError,
              GAPI.invalid, GAPI.badRequest, GAPI.cannotCopyFile, GAPI.responsePreparationFailure, GAPI.fileNeverWritable, GAPI.fieldNotWritable,
              GAPI.teamDrivesSharingRestrictionNotAllowed, GAPI.rateLimitExceeded, GAPI.userRateLimitExceeded,
              GAPI.storageQuotaExceeded, GAPI.teamDriveFileLimitExceeded, GAPI.teamDriveHierarchyTooDeep) as e:
        _getMain().entityActionFailedWarning([Ent.USER, user, Ent.DRIVE_FILE_OR_FOLDER_ID, fileId], str(e), j, jcount)
        _incrStatistic(statistics, STAT_FILE_FAILED)
      except (GAPI.serviceNotAvailable, GAPI.authError, GAPI.domainPolicy) as e:
        _getMain().userDriveServiceNotEnabledWarning(user, str(e), i, count)
        _incrStatistic(statistics, STAT_FILE_FAILED)
        break
    Ind.Decrement()
    if copyMoveOptions['summary']:
      _printStatistics(user, statistics, i, count, True)
  if csvPF:
    csvPF.writeCSVfile('Copied Files-Folders')

