"""Move Drive file operations and permission updates.

Part of the copymove sub-package."""

"""File copy/move operations with permission handling.

Part of the drive sub-package, extracted from drive.py."""

"""GAM Google Drive file, permission, shared drive, and label management."""

import re
import sys

from gam.cmd.drive.core import DFA_SEARCHARGS

from gam.cmd.drive.copymove.copymove_util import _checkForDuplicateTargetFile, _checkForExistingShortcut, _copyPermissions, _getCopyFolderNonInheritedPermissions, _getCopyMoveParentInfo, _getCopyMoveTargetInfo, _getUniqueFilename, _identicalSourceTarget, _printStatistics, _targetFilenameExists, _verifyUserIsOrganizer, getCopyMoveOptions, initCopyMoveOptions

from gamlib import glaction
from gamlib import glapi as API
from gamlib import glcfg as GC
from gamlib import glclargs
from gamlib import glentity
from gamlib import glgapi as GAPI
from gamlib import glglobals as GM
from gamlib import glindent
from gamlib import glmsgs as Msg
from gam.util.api import callGAPI, callGAPIpages
from gam.util.args import getArgument, getBoolean
from gam.util.display import (
    entityActionFailedWarning,
    entityActionNotPerformedWarning,
    entityActionPerformed,
    entityModifierItemValueListActionNotPerformedWarning,
    entityModifierItemValueListActionPerformed,
    entityPerformActionModifierItemValueList,
    userDriveServiceNotEnabledWarning,
)
from gam.util.entity import getEntityArgument
from gam.util.errors import unknownArgumentExit

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

def _updateMoveFilePermissions(drive, user, i, count,
                               entityType, fileId, fileTitle,
                               statistics, stat, copyMoveOptions):
  def getPermissions(fid):
    permissions = {}
    try:
      result = callGAPIpages(drive.permissions(), 'list', 'permissions',
                             throwReasons=GAPI.DRIVE3_GET_ACL_REASONS,
                             retryReasons=GAPI.SERVICE_NOT_AVAILABLE_RETRY_REASONS,
                             fileId=fid,
                             fields='nextPageToken,permissions(allowFileDiscovery,domain,emailAddress,expirationTime,id,role,type,deleted,view,pendingOwner,permissionDetails)',
                             useDomainAdminAccess=copyMoveOptions['useDomainAdminAccess'], supportsAllDrives=True)
      for permission in result:
        permission.pop('teamDrivePermissionDetails', None)
        if not permission.pop('permissionDetails', [{'inherited': False}])[0]['inherited']:
          permissions[permission['id']] = permission
      return permissions
    except (GAPI.fileNotFound, GAPI.forbidden, GAPI.internalError,
            GAPI.insufficientAdministratorPrivileges, GAPI.insufficientFilePermissions,
            GAPI.unknownError, GAPI.invalid):
      pass
    except (GAPI.serviceNotAvailable, GAPI.authError, GAPI.domainPolicy) as e:
      userDriveServiceNotEnabledWarning(user, str(e), i, count)
      _incrStatistic(statistics, stat)
    return None

  def permissionKVList(user, entityType, title, permission):
    permstr = f"noninherited/{permission['role']}/{permission['type']}"
    if permission['type'] in {'group', 'user'}:
      permstr += f"/{permission['emailAddress']}"
    elif permission['type'] == 'domain':
      permstr += f"/{permission['domain']}"
    return [Ent.USER, user, entityType, title, Ent.PERMISSION, permstr]

  def isPermissionDeletable(kvList, permission):
    if not copyMoveOptions['moveFilePermissions']:
      notMovedMessage = 'movefilepermissions false'
    elif permission.pop('deleted', False):
      notMovedMessage = f"{permission['type']} {permission['emailAddress']} deleted"
    elif copyMoveOptions['excludePermissionsFromDomains'] or copyMoveOptions['includePermissionsFromDomains']:
      domain = ''
      if permission['type'] in {'group', 'user'}:
        atLoc = permission.get('emailAddress', '').find('@')
        if atLoc > 0:
          domain = permission['emailAddress'][atLoc+1:].lower()
      elif permission['type'] == 'domain':
        domain = permission.get('domain', '').lower()
      if domain and domain in copyMoveOptions['excludePermissionsFromDomains']:
        notMovedMessage = f'domain {domain} excluded'
      elif domain and copyMoveOptions['includePermissionsFromDomains'] and domain not in copyMoveOptions['includePermissionsFromDomains']:
        notMovedMessage = f'domain {domain} not included'
      else:
        return False
    else:
      return False
    deleteSourcePerms[permission['id']] = permission.copy()
    if copyMoveOptions['showPermissionMessages']:
      entityActionNotPerformedWarning(kvList, notMovedMessage, 0, 0)
    return True

  def mapPermissionsDomains(kvList, permission):
    if 'emailAddress' in permission:
      sourceEmail = permission['emailAddress'].lower()
      destEmail = copyMoveOptions['mapPermissionsEmails'].get(sourceEmail, None)
      if destEmail:
        deleteSourcePerms[permission['id']] = permission.copy()
        if copyMoveOptions['showPermissionMessages']:
          notMovedMessage = f"email {sourceEmail} mapped to {destEmail}"
          entityActionNotPerformedWarning(kvList, notMovedMessage, 0, 0)
        permission['emailAddress'] = destEmail
        addSourcePerms[permission['id']] = permission
        return True
      email, domain = sourceEmail.split('@', 1)
      if domain in copyMoveOptions['mapPermissionsDomains']:
        destEmail = f"{email}@{copyMoveOptions['mapPermissionsDomains'][domain]}"
        deleteSourcePerms[permission['id']] = permission.copy()
        if copyMoveOptions['showPermissionMessages']:
          notMovedMessage = f"email {sourceEmail} mapped to {destEmail}"
          entityActionNotPerformedWarning(kvList, notMovedMessage, 0, 0)
        permission['emailAddress'] = destEmail
        addSourcePerms[permission['id']] = permission
        return True
    elif 'domain' in permission:
      domain = permission['domain'].lower()
      if domain in copyMoveOptions['mapPermissionsDomains']:
        deleteSourcePerms[permission['id']] = permission.copy()
        if copyMoveOptions['showPermissionMessages']:
          notMovedMessage = f"domain {domain} mapped to {copyMoveOptions['mapPermissionsDomains'][domain]}"
          entityActionNotPerformedWarning(kvList, notMovedMessage, 0, 0)
        permission['domain'] = copyMoveOptions['mapPermissionsDomains'][domain]
        addSourcePerms[permission['id']] = permission
        return True
    return False

  sourcePerms = getPermissions(fileId)
  if sourcePerms is None:
    return
  deleteSourcePerms = {}
  addSourcePerms = {}
  for permissionId, permission in sourcePerms.items():
    kvList = permissionKVList(user, entityType, fileTitle, permission)
    if permission.get('permissionDetails', {}).get('inherited', False):
      continue
    if (not isPermissionDeletable(kvList, permission) and
        (copyMoveOptions['mapPermissionsDomains'] or copyMoveOptions['mapPermissionsEmails'])):
      mapPermissionsDomains(kvList, permission)
  action = Act.Get()
  kcount = len(deleteSourcePerms)
  if kcount > 0:
    Act.Set(Act.DELETE)
    k = 0
    for permissionId, permission in deleteSourcePerms.items():
      k += 1
      kvList = permissionKVList(user, entityType, fileTitle, permission)
      try:
        callGAPI(drive.permissions(), 'delete',
                 throwReasons=GAPI.DRIVE_ACCESS_THROW_REASONS+GAPI.DRIVE3_DELETE_ACL_THROW_REASONS,
                 useDomainAdminAccess=copyMoveOptions['useDomainAdminAccess'],
                 fileId=fileId, permissionId=permissionId,  supportsAllDrives=True)
        if copyMoveOptions['showPermissionMessages']:
          entityActionPerformed(kvList, k, kcount)
      except (GAPI.fileNotFound, GAPI.forbidden, GAPI.internalError, GAPI.insufficientFilePermissions, GAPI.unknownError, GAPI.invalid,
              GAPI.badRequest, GAPI.notFound, GAPI.permissionNotFound, GAPI.cannotRemoveOwner,
              GAPI.cannotModifyInheritedTeamDrivePermission, GAPI.cannotModifyInheritedPermission,
              GAPI.insufficientAdministratorPrivileges, GAPI.sharingRateLimitExceeded, GAPI.cannotDeletePermission,
              GAPI.fileNeverWritable) as e:
        entityActionFailedWarning(kvList, str(e), k, kcount)
      except (GAPI.serviceNotAvailable, GAPI.authError, GAPI.domainPolicy) as e:
        userDriveServiceNotEnabledWarning(user, str(e), i, count)
        _incrStatistic(statistics, stat)
        Act.Set(action)
        return
  kcount = len(addSourcePerms)
  if kcount > 0:
    Act.Set(Act.CREATE)
    k = 0
    for permissionId, permission in addSourcePerms.items():
      k += 1
      kvList = permissionKVList(user, entityType, fileTitle, permission)
      permission.pop('id')
      if copyMoveOptions['destDriveId']:
        permission.pop('pendingOwner', None)
      sendNotificationEmail = False
      while True:
        try:
          callGAPI(drive.permissions(), 'create',
                   throwReasons=GAPI.DRIVE_ACCESS_THROW_REASONS+GAPI.DRIVE3_CREATE_ACL_THROW_REASONS,
#                   retryReasons=[GAPI.INVALID_SHARING_REQUEST],
                   fileId=fileId, sendNotificationEmail=sendNotificationEmail, emailMessage=None,
                   body=permission, fields='', useDomainAdminAccess=copyMoveOptions['useDomainAdminAccess'], supportsAllDrives=True)
          if copyMoveOptions['showPermissionMessages']:
            entityActionPerformed(kvList, k, kcount)
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
          entityActionFailedWarning(kvList, str(e), k, kcount)
          break
        except GAPI.invalidSharingRequest as e:
          if not copyMoveOptions['sendEmailIfRequired'] or sendNotificationEmail or 'You are trying to invite' not in str(e):
            entityActionFailedWarning(kvList, str(e), k, kcount)
            break
          sendNotificationEmail = True
        except (GAPI.serviceNotAvailable, GAPI.authError, GAPI.domainPolicy) as e:
          userDriveServiceNotEnabledWarning(user, str(e), i, count)
          _incrStatistic(statistics, stat)
          Act.Set(action)
          return
  Act.Set(action)

def _recursiveUpdateMovePermissions(drive, user, i, count,
                                    fileId, fileTitle,
                                    statistics, copyMoveOptions, sourceSearchArgs):
  _updateMoveFilePermissions(drive, user, i, count,
                             Ent.DRIVE_FOLDER, fileId, fileTitle,
                             statistics, STAT_FOLDER_PERMISSIONS_FAILED, copyMoveOptions)
  sourceChildren = callGAPIpages(drive.files(), 'list', 'files',
                                 throwReasons=GAPI.DRIVE_USER_THROW_REASONS,
                                 retryReasons=[GAPI.UNKNOWN_ERROR],
                                 q=_getMain().WITH_PARENTS.format(fileId),
                                 orderBy='folder desc,name,modifiedTime desc',
                                 fields='nextPageToken,files(id,name,mimeType)',
                                 pageSize=GC.Values[GC.DRIVE_MAX_RESULTS], **sourceSearchArgs)
  kcount = len(sourceChildren)
  if kcount > 0:
    Ind.Increment()
    k = 0
    for child in sourceChildren:
      k += 1
      childId = child['id']
      childName = child['name']
      if child['mimeType'] == MIMETYPE_GA_FOLDER:
        _recursiveUpdateMovePermissions(drive, user, i, count,
                                        childId, childName,
                                        statistics, copyMoveOptions, sourceSearchArgs)
      else:
        _updateMoveFilePermissions(drive, user, i, count,
                                   Ent.DRIVE_FILE, childId, childName,
                                   statistics, STAT_FILE_PERMISSIONS_FAILED, copyMoveOptions)
    Ind.Decrement()

# gam <UserTypeEntity> move drivefile <DriveFileEntity> [newfilename <DriveFileName>]
#	[summary [<Boolean>]] [showpermissionsmessages [<Boolean>]]
#	[<DriveFileParentAttribute>]
#       [mergewithparent|mergewithparentretain [<Boolean>]]
#	[createshortcutsfornonmovablefiles [<Boolean>]]
#	[duplicatefiles overwriteolder|overwriteall|duplicatename|uniquename|skip]
#	[duplicatefolders merge|duplicatename|uniquename|skip]
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
#	[synctopfoldernoniheritedpermissions [<Boolean>]] [syncsubfoldernoninheritedpermissions [<Boolean>]]
#	[movefilepermissions [<Boolean>]]
#	[excludepermissionsfromdomains|includepermissionsfromdomains <DomainNameList>]
#	(mappermissionsemail <EmailAddress> <EmailAddress>)* [mappermissionsemailfile <CSVFileInput> endcsv]
#	(mappermissionsdomain <DomainName> <DomainName>)*
#	[retainsourcefolders [<Boolean>]]
#	[sendemailifrequired [<Boolean>]]
#	[verifyorganizer [<Boolean>]]
def moveDriveFile(users):
  def _cloneFolderMove(drive, user, i, count, j, jcount,
                       source, targetChildren, newFolderName, newParentId, newParentName, mergeParentModifiedTime,
                       statistics, copyMoveOptions, atTop):
    folderId = source.pop('id')
    folderName = source['name']
    sourceMimeType = source['mimeType']
    folderNameId = f'{folderName}({folderId})'
    kvList = [Ent.USER, user, Ent.DRIVE_FOLDER, folderNameId]
    newParentNameId = f'{newParentName}({newParentId})'
# Merge top parent folder
    if atTop and (copyMoveOptions['mergeWithParent'] or copyMoveOptions['mergeWithParentRetain']):
      action = Act.Get()
      Act.Set(Act.MOVE_MERGE)
      entityPerformActionModifierItemValueList(kvList, Act.MODIFIER_CONTENTS_WITH, [Ent.DRIVE_FOLDER, newParentNameId], j, jcount)
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
                         False)
      source.pop('oldparents', None)
      return (newParentId, newParentName, True, True)
# Merge parent folders
    if atTop and copyMoveOptions['sourceIsMyDriveSharedDrive']:
      pass
    elif copyMoveOptions['duplicateFolders'] == DUPLICATE_FOLDER_MERGE:
      newFolderNameLower = newFolderName.lower()
      for target in targetChildren:
        if not target.get('processed', False) and newFolderNameLower == target['name'].lower() and sourceMimeType == target['mimeType']:
          target['processed'] = True
          if target['capabilities']['canAddChildren']:
            newFolderId = target['id']
            action = Act.Get()
            Act.Set(Act.MOVE_MERGE)
            entityModifierItemValueListActionPerformed(kvList, Act.MODIFIER_CONTENTS_WITH, [Ent.DRIVE_FOLDER, f'{newFolderName}({newFolderId})'], j, jcount)
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
            return (newFolderId, newFolderName, True, True)
          entityActionFailedWarning(kvList+[Ent.DRIVE_FOLDER, newParentNameId], Msg.NOT_WRITABLE, j, jcount)
          _incrStatistic(statistics, STAT_FOLDER_NOT_WRITABLE)
          copyMoveOptions['retainSourceFolders'] = True
          return (None, None, False, False)
    elif copyMoveOptions['duplicateFolders'] == DUPLICATE_FOLDER_UNIQUE_NAME:
      newFolderName = _getUniqueFilename(newFolderName, sourceMimeType, targetChildren)
    elif copyMoveOptions['duplicateFolders'] == DUPLICATE_FOLDER_SKIP:
      targetChild = _targetFilenameExists(newFolderName, sourceMimeType, targetChildren)
      if targetChild is not None:
        entityModifierItemValueListActionNotPerformedWarning(kvList, Act.MODIFIER_TO,
                                                             [Ent.DRIVE_FOLDER, newParentNameId, Ent.DRIVE_FOLDER, f"{newFolderName}({targetChild['id']})"],
                                                             Msg.DUPLICATE, j, jcount)
        _incrStatistic(statistics, STAT_FOLDER_DUPLICATE)
        copyMoveOptions['retainSourceFolders'] = True
        return (None, None, False, False)
# Update parents on: not retain and MD->MD, SD->MD, SD->SD
    if atTop and copyMoveOptions['sourceIsMyDriveSharedDrive']:
      pass
    elif (not copyMoveOptions['retainSourceFolders'] and (copyMoveOptions['sourceDriveId'] or not copyMoveOptions['destDriveId'])):
      if newFolderName != folderName:
        body = {'name': newFolderName}
      else:
        body = {}
      removeParents = ','.join([parentId for parentId in source.pop('oldparents', []) if parentId not in source['parents']])
      try:
        callGAPI(drive.files(), 'update',
                 throwReasons=GAPI.DRIVE_ACCESS_THROW_REASONS+[GAPI.BAD_REQUEST,
                                                               GAPI.INSUFFICIENT_PARENT_PERMISSIONS,
                                                               GAPI.FILE_OWNER_NOT_MEMBER_OF_TEAMDRIVE,
                                                               GAPI.FILE_OWNER_NOT_MEMBER_OF_WRITER_DOMAIN,
                                                               GAPI.FILE_WRITER_TEAMDRIVE_MOVE_IN_DISABLED,
                                                               GAPI.TARGET_USER_ROLE_LIMITED_BY_LICENSE_RESTRICTION,
                                                               GAPI.CANNOT_MOVE_TRASHED_ITEM_INTO_TEAMDRIVE,
                                                               GAPI.CANNOT_MOVE_TRASHED_ITEM_OUT_OF_TEAMDRIVE,
                                                               GAPI.CROSS_DOMAIN_MOVE_RESTRICTION,
                                                               GAPI.STORAGE_QUOTA_EXCEEDED],
                 fileId=folderId,
                 addParents=newParentId, removeParents=removeParents,
                 body=body, fields=None, supportsAllDrives=True)
        entityModifierItemValueListActionPerformed(kvList, Act.MODIFIER_TO,
                                                   [Ent.DRIVE_FOLDER, newParentNameId, Ent.DRIVE_FOLDER, f'{newFolderName}({folderId})'],
                                                   j, jcount)
        _incrStatistic(statistics, STAT_FILE_COPIED_MOVED)
        return (None, None, False, True)
      except (GAPI.badRequest, GAPI.insufficientParentPermissions, GAPI.fileOwnerNotMemberOfTeamDrive, GAPI.fileOwnerNotMemberOfWriterDomain,
              GAPI.fileWriterTeamDriveMoveInDisabled, GAPI.targetUserRoleLimitedByLicenseRestriction,
              GAPI.cannotMoveTrashedItemIntoTeamDrive, GAPI.cannotMoveTrashedItemOutOfTeamDrive,
              GAPI.crossDomainMoveRestriction, GAPI.storageQuotaExceeded) as e:
        entityActionFailedWarning([Ent.USER, user, Ent.DRIVE_FOLDER, folderName], str(e), j, jcount)
      except (GAPI.serviceNotAvailable, GAPI.authError, GAPI.domainPolicy) as e:
        userDriveServiceNotEnabledWarning(user, str(e), i, count)
      _incrStatistic(statistics, STAT_FILE_FAILED)
      copyMoveOptions['retainSourceFolders'] = True
      return (None, None, False, False)
# Create new parent on: retain or MD->SD
    source.pop('oldparents', None)
    body = source.copy()
    body.pop('capabilities', None)
    if copyMoveOptions['sourceDriveId'] or copyMoveOptions['destDriveId']:
      body.pop('copyRequiresWriterPermission', None)
      body.pop('writersCanShare', None)
    body.pop('trashed', None)
    if not copyMoveOptions['destDriveId']:
      body.pop('driveId', None)
    body['name'] = newFolderName
    try:
      result = callGAPI(drive.files(), 'create',
                        throwReasons=GAPI.DRIVE_USER_THROW_REASONS+[GAPI.FORBIDDEN, GAPI.INSUFFICIENT_PERMISSIONS, GAPI.INSUFFICIENT_PARENT_PERMISSIONS,
                                                                    GAPI.INTERNAL_ERROR, GAPI.STORAGE_QUOTA_EXCEEDED,
                                                                    GAPI.TEAMDRIVE_FILE_LIMIT_EXCEEDED, GAPI.TEAMDRIVE_HIERARCHY_TOO_DEEP,
                                                                    GAPI.BAD_REQUEST, GAPI.TARGET_USER_ROLE_LIMITED_BY_LICENSE_RESTRICTION],
                        body=body, fields='id', supportsAllDrives=True)
      newFolderId = result['id']
      action = Act.Get()
      Act.Set(Act.RECREATE)
      entityModifierItemValueListActionPerformed(kvList, Act.MODIFIER_IN,
                                                 [Ent.DRIVE_FOLDER, newParentNameId, Ent.DRIVE_FOLDER, f'{newFolderName}({newFolderId})'],
                                                 j, jcount)
      Act.Set(action)
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
      return (newFolderId, newFolderName, False, True)
    except (GAPI.forbidden, GAPI.insufficientFilePermissions, GAPI.insufficientParentPermissions,
            GAPI.internalError, GAPI.storageQuotaExceeded, GAPI.teamDriveFileLimitExceeded, GAPI.teamDriveHierarchyTooDeep,
            GAPI.badRequest, GAPI.targetUserRoleLimitedByLicenseRestriction) as e:
      entityActionFailedWarning([Ent.USER, user, Ent.DRIVE_FOLDER, newFolderName], str(e), j, jcount)
    except (GAPI.serviceNotAvailable, GAPI.authError, GAPI.domainPolicy) as e:
      userDriveServiceNotEnabledWarning(user, str(e), i, count)
    _incrStatistic(statistics, STAT_FOLDER_FAILED)
    copyMoveOptions['retainSourceFolders'] = True
    return (None, None, False, False)

  def _makeMoveShortcut(drive, user, k, kcount, entityType, childId, childName, newParentId, newParentName):
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
    existingShortcut = _checkForExistingShortcut(drive, childId, childName, newParentId)
    if existingShortcut:
      Act.Set(Act.CREATE_SHORTCUT)
      entityModifierItemValueListActionPerformed(kvList, Act.MODIFIER_PREVIOUSLY_IN,
                                                 [Ent.DRIVE_FOLDER, newParentNameId, targetEntityType, f"{childName}({existingShortcut})"],
                                                 k, kcount)
      Act.Set(action)
      _incrStatistic(statistics, statShortcutExists)
      return
    body = {'name': childName, 'mimeType': MIMETYPE_GA_SHORTCUT,
            'parents': [newParentId], 'shortcutDetails': {'targetId': childId}}
    try:
      result = callGAPI(drive.files(), 'create',
                        throwReasons=GAPI.DRIVE_USER_THROW_REASONS+[GAPI.FORBIDDEN, GAPI.INSUFFICIENT_PERMISSIONS, GAPI.INSUFFICIENT_PARENT_PERMISSIONS,
                                                                    GAPI.INVALID, GAPI.BAD_REQUEST, GAPI.FILE_NOT_FOUND, GAPI.UNKNOWN_ERROR,
                                                                    GAPI.STORAGE_QUOTA_EXCEEDED, GAPI.TEAMDRIVES_SHARING_RESTRICTION_NOT_ALLOWED,
                                                                    GAPI.TEAMDRIVE_FILE_LIMIT_EXCEEDED, GAPI.TEAMDRIVE_HIERARCHY_TOO_DEEP, GAPI.SHORTCUT_TARGET_INVALID,
                                                                    GAPI.TARGET_USER_ROLE_LIMITED_BY_LICENSE_RESTRICTION, GAPI.SHARE_OUT_WARNING],
                        body=body, fields='id', supportsAllDrives=True)
      Act.Set(Act.CREATE_SHORTCUT)
      entityModifierItemValueListActionPerformed(kvList, Act.MODIFIER_IN,
                                                 [Ent.DRIVE_FOLDER, newParentNameId, targetEntityType, f"{childName}({result['id']})"],
                                                 k, kcount)
      Act.Set(action)
      _incrStatistic(statistics, statShortcutCreated)
    except (GAPI.forbidden, GAPI.insufficientFilePermissions, GAPI.insufficientParentPermissions,
            GAPI.invalid, GAPI.badRequest, GAPI.fileNotFound, GAPI.unknownError,
            GAPI.storageQuotaExceeded, GAPI.teamDrivesSharingRestrictionNotAllowed,
            GAPI.teamDriveFileLimitExceeded, GAPI.teamDriveHierarchyTooDeep, GAPI.shortcutTargetInvalid,
            GAPI.targetUserRoleLimitedByLicenseRestriction, GAPI.shareOutWarning) as e:
      entityActionFailedWarning(kvList+[Ent.DRIVE_FILE_SHORTCUT, childName], str(e), k, kcount)
      _incrStatistic(statistics, STAT_FILE_FAILED)

  def _moveFile(drive, user, i, count, k, kcount, entityType, childId, childName, newChildName, newParentId, newParentName, removeParents, body):
    kvList = [Ent.USER, user, entityType, f'{childName}({childId})']
    newParentNameId = f'{newParentName}({newParentId})'
    if updateMovePermissions:
      _updateMoveFilePermissions(drive, user, i, count,
                                 entityType, childId, childName,
                                 statistics, STAT_FILE_PERMISSIONS_FAILED, copyMoveOptions)
    try:
      callGAPI(drive.files(), 'update',
               throwReasons=GAPI.DRIVE_ACCESS_THROW_REASONS+[GAPI.BAD_REQUEST,
                                                             GAPI.INSUFFICIENT_PARENT_PERMISSIONS,
                                                             GAPI.FILE_OWNER_NOT_MEMBER_OF_TEAMDRIVE,
                                                             GAPI.FILE_OWNER_NOT_MEMBER_OF_WRITER_DOMAIN,
                                                             GAPI.FILE_WRITER_TEAMDRIVE_MOVE_IN_DISABLED,
                                                             GAPI.SHARE_OUT_NOT_PERMITTED,
                                                             GAPI.TARGET_USER_ROLE_LIMITED_BY_LICENSE_RESTRICTION,
                                                             GAPI.CANNOT_MOVE_TRASHED_ITEM_INTO_TEAMDRIVE,
                                                             GAPI.CANNOT_MOVE_TRASHED_ITEM_OUT_OF_TEAMDRIVE,
                                                             GAPI.TEAMDRIVES_SHORTCUT_FILE_NOT_SUPPORTED,
                                                             GAPI.CROSS_DOMAIN_MOVE_RESTRICTION,
                                                             GAPI.STORAGE_QUOTA_EXCEEDED],
               fileId=childId, addParents=newParentId, removeParents=removeParents,
               body=body, fields='', supportsAllDrives=True)
      entityModifierItemValueListActionPerformed(kvList, Act.MODIFIER_TO,
                                                 [Ent.DRIVE_FOLDER, newParentNameId, entityType, f'{newChildName}({childId})'],
                                                 k, kcount)
      _incrStatistic(statistics, STAT_FILE_COPIED_MOVED)
      return
    except (GAPI.fileNotFound, GAPI.forbidden, GAPI.internalError, GAPI.unknownError, GAPI.badRequest,
            GAPI.shareOutNotPermitted, GAPI.targetUserRoleLimitedByLicenseRestriction,
            GAPI.cannotMoveTrashedItemIntoTeamDrive, GAPI.cannotMoveTrashedItemOutOfTeamDrive,
            GAPI.teamDrivesShortcutFileNotSupported, GAPI.storageQuotaExceeded) as e:
      entityActionFailedWarning(kvList, str(e), k, kcount)
      _incrStatistic(statistics, STAT_FILE_FAILED)
    except (GAPI.insufficientFilePermissions, GAPI.insufficientParentPermissions,
            GAPI.fileOwnerNotMemberOfTeamDrive, GAPI.fileOwnerNotMemberOfWriterDomain,
            GAPI.fileWriterTeamDriveMoveInDisabled,
            GAPI.crossDomainMoveRestriction) as e:
      if not copyMoveOptions['createShortcutsForNonmovableFiles']:
        entityActionFailedWarning(kvList, str(e), k, kcount)
        _incrStatistic(statistics, STAT_FILE_FAILED)
      else:
        _makeMoveShortcut(drive, user, k, kcount, entityType, childId, childName, newParentId, newParentName)
    copyMoveOptions['retainSourceFolders'] = True

  def _recursiveFolderMove(drive, user, i, count, j, jcount,
                           source, targetChildren, newFolderName, newParentId, newParentName, mergeParentModifiedTime, atTop):
    folderId = source['id']
    newFolderId, newFolderName, existingTargetFolder, status = _cloneFolderMove(drive, user, i, count, j, jcount,
                                                                                source, targetChildren, newFolderName,
                                                                                newParentId, newParentName, mergeParentModifiedTime,
                                                                                statistics, copyMoveOptions, atTop)
    if not status:
      return
    if newFolderId is None:
      if updateMovePermissions:
        _recursiveUpdateMovePermissions(drive, user, i, count,
                                        folderId, source['name'],
                                        statistics, copyMoveOptions, sourceSearchArgs)
      return
    movedFiles[newFolderId] = 1
    sourceChildren = callGAPIpages(drive.files(), 'list', 'files',
                                   throwReasons=GAPI.DRIVE_USER_THROW_REASONS,
                                   retryReasons=[GAPI.UNKNOWN_ERROR],
                                   q=_getMain().WITH_PARENTS.format(folderId),
                                   orderBy='folder desc,name,modifiedTime desc',
                                   fields='nextPageToken,files(id,name,parents,appProperties,capabilities,contentHints,copyRequiresWriterPermission,'\
                                     'description,folderColorRgb,mimeType,modifiedTime,properties,starred,driveId,trashed,viewedByMeTime,writersCanShare)',
                                   pageSize=GC.Values[GC.DRIVE_MAX_RESULTS], **sourceSearchArgs)
    kcount = len(sourceChildren)
    if kcount > 0:
      if existingTargetFolder:
        subTargetChildren = callGAPIpages(drive.files(), 'list', 'files',
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
        if movedFiles.get(childId):
          continue
        trashed = child.pop('trashed', False)
        if (childId == newFolderId) or (copyMoveOptions['destDriveId'] and trashed):
          entityActionNotPerformedWarning([Ent.USER, user, _getMain()._getEntityMimeType(child), childNameId],
                                          [Msg.NOT_MOVABLE, Msg.NOT_MOVABLE_IN_TRASH][trashed], k, kcount)
          _incrStatistic(statistics, STAT_FILE_NOT_COPYABLE_MOVABLE)
          continue
        childParents = child.pop('parents', [])
        child['parents'] = [newFolderId]
        if child['mimeType'] == MIMETYPE_GA_FOLDER:
          child['oldparents'] = childParents
          _recursiveFolderMove(drive, user, i, count, k, kcount,
                               child, subTargetChildren, childName, newFolderId, newFolderName, child['modifiedTime'], False)
        else:
          if existingTargetFolder and _checkForDuplicateTargetFile(drive, user, k, kcount, child, childName, subTargetChildren, copyMoveOptions, statistics):
            copyMoveOptions['retainSourceFolders'] = True
            continue
          if childName != child['name']:
            body = {'name': child['name']}
          else:
            body = {}
          removeParents = ','.join(childParents)
          _moveFile(drive, user, i, count, k, kcount, Ent.DRIVE_FILE, childId, childName, childName, newFolderId, newFolderName, removeParents, body)
      Ind.Decrement()
    sourceName = source['name']
    kvList = [Ent.USER, user, Ent.DRIVE_FOLDER, f"{sourceName}({folderId})"]
    if (atTop and (copyMoveOptions['mergeWithParentRetain'] or copyMoveOptions['sourceIsMyDriveSharedDrive'])) or copyMoveOptions['retainSourceFolders']:
      Act.Set(Act.RETAIN)
      entityActionPerformed(kvList, i, count)
    else:
      Act.Set(Act.DELETE)
      try:
        callGAPI(drive.files(), 'delete',
                 throwReasons=GAPI.DRIVE_ACCESS_THROW_REASONS+[GAPI.FILE_NEVER_WRITABLE],
                 fileId=folderId, supportsAllDrives=True)
        entityActionPerformed(kvList, i, count)
      except (GAPI.fileNotFound, GAPI.forbidden, GAPI.internalError, GAPI.insufficientFilePermissions, GAPI.unknownError,
              GAPI.fileNeverWritable) as e:
        entityActionFailedWarning(kvList, str(e), j, jcount)
      except (GAPI.serviceNotAvailable, GAPI.authError, GAPI.domainPolicy) as e:
        userDriveServiceNotEnabledWarning(user, str(e), i, count)
    Act.Set(Act.MOVE)
    return

  def anyFolderPermissionOperations():
    for field in ['copyMergeWithParentFolderPermissions',
                  'copyMergedTopFolderPermissions', 'copyMergedSubFolderPermissions',
                  'copyTopFolderPermissions', 'copySubFolderPermissions']:
      if copyMoveOptions[field]:
        return True
    return False

  fileIdEntity = getDriveFileEntity()
  parentBody = {}
  parentParms = initDriveFileAttributes()
  copyMoveOptions = initCopyMoveOptions(False)
  newParentsSpecified = False
  movedFiles = {}
  verifyOrganizer = True
  while Cmd.ArgumentsRemaining():
    myarg = getArgument()
    if getCopyMoveOptions(myarg, copyMoveOptions):
      pass
    elif getDriveFileParentAttribute(myarg, parentParms):
      newParentsSpecified = True
    elif myarg == 'verifyorganizer':
      verifyOrganizer = getBoolean()
    else:
      unknownArgumentExit()
  updateMovePermissions = ((not copyMoveOptions['moveFilePermissions']) or
                           copyMoveOptions['excludePermissionsFromDomains'] or copyMoveOptions['includePermissionsFromDomains'] or
                           copyMoveOptions['mapPermissionsDomains'] or copyMoveOptions['mapPermissionsEmails'])

  i, count, users = getEntityArgument(users)
  for user in users:
    i += 1
    user, drive, jcount = _validateUserGetFileIDs(user, i, count, fileIdEntity, entityType=Ent.DRIVE_FILE_OR_FOLDER)
    if jcount == 0:
      continue
    if not _getDriveFileParentInfo(drive, user, i, count, parentBody, parentParms):
      continue
    statistics = _initStatistics()
    Ind.Increment()
    j = 0
    for fileId in fileIdEntity['list']:
      j += 1
      try:
        source = callGAPI(drive.files(), 'get',
                          throwReasons=GAPI.DRIVE_GET_THROW_REASONS,
                          fileId=fileId,
                          fields='id,name,parents,appProperties,capabilities,contentHints,copyRequiresWriterPermission,'\
                            'description,mimeType,modifiedTime,properties,starred,driveId,trashed,viewedByMeTime,writersCanShare',
                          supportsAllDrives=True)
# Source at root of My Drive or Shared Drive?
        sourceMimeType = source['mimeType']
        if sourceMimeType == MIMETYPE_GA_FOLDER and source['name'] in [MY_DRIVE, TEAM_DRIVE] and not source.get('parents', []):
          copyMoveOptions['sourceIsMyDriveSharedDrive'] = True
          if source.get('driveId'):
            source['name'] = _getSharedDriveNameFromId(drive, source['driveId'])
        sourceName = source['name']
        sourceNameId = f"{sourceName}({source['id']})"
        copyMoveOptions['sourceDriveId'] = source.get('driveId')
        kvList = [Ent.USER, user, _getMain()._getEntityMimeType(source), sourceNameId]
        if fileId in movedFiles:
          entityActionNotPerformedWarning(kvList, Msg.DUPLICATE, j, jcount)
          _incrStatistic(statistics, STAT_FILE_DUPLICATE)
          continue
        if copyMoveOptions['sourceDriveId']:
# If moving from a Shared Drive, user has to be an organizer
          if verifyOrganizer and not _verifyUserIsOrganizer(drive, user, i, count, copyMoveOptions['sourceDriveId']):
            _incrStatistic(statistics, STAT_USER_NOT_ORGANIZER)
            continue
          if source['trashed']:
            entityActionNotPerformedWarning(kvList, Msg.NOT_MOVABLE_IN_TRASH, j, jcount)
            _incrStatistic(statistics, STAT_FILE_NOT_COPYABLE_MOVABLE)
            continue
          sourceSearchArgs = {'driveId': copyMoveOptions['sourceDriveId'], 'corpora': 'drive', 'includeItemsFromAllDrives': True, 'supportsAllDrives': True}
        else:
          sourceSearchArgs = {}
        sourceParents = source.pop('parents', [])
        if newParentsSpecified:
          newParents = parentBody['parents']
          numNewParents = len(newParents)
          if numNewParents > 1:
            entityActionNotPerformedWarning(kvList, Msg.MULTIPLE_PARENTS_SPECIFIED.format(numNewParents), j, jcount)
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
        if copyMoveOptions['destDriveId'] and not parentParms[DFA_SEARCHARGS]:
          parentParms[DFA_SEARCHARGS] = {'driveId': copyMoveOptions['destDriveId'], 'corpora': 'drive',
                                         'includeItemsFromAllDrives': True, 'supportsAllDrives': True}
        if copyMoveOptions['newFilename']:
          destName = copyMoveOptions['newFilename']
        elif (sourceMimeType == MIMETYPE_GA_FOLDER) and (copyMoveOptions['mergeWithParent'] or copyMoveOptions['mergeWithParentRetain']):
          destName = dest['name']
        else:
          destName = sourceName
        targetChildren = _getCopyMoveTargetInfo(drive, user, i, count, j, jcount, source, destName, newParentId, statistics, parentParms)
        if targetChildren is None:
          continue
        if copyMoveOptions['destDriveId']:
# If moving to a Shared Drive, user has to be an organizer
          if verifyOrganizer and not _verifyUserIsOrganizer(drive, user, i, count, copyMoveOptions['destDriveId']):
            _incrStatistic(statistics, STAT_USER_NOT_ORGANIZER)
            continue
# 3rd party shortcuts can't be moved to Shared Drives
          if sourceMimeType.startswith(MIMETYPE_GA_3P_SHORTCUT):
            entityActionNotPerformedWarning([Ent.USER, user, Ent.DRIVE_3PSHORTCUT, sourceNameId], Msg.NOT_MOVABLE, j, jcount)
            _incrStatistic(statistics, STAT_FILE_NOT_COPYABLE_MOVABLE)
            continue
# Move folder
        if sourceMimeType == MIMETYPE_GA_FOLDER:
          if fileId == newParentId:
            entityActionNotPerformedWarning(kvList, Msg.NOT_MOVABLE_INTO_ITSELF, j, jcount)
            _incrStatistic(statistics, STAT_FOLDER_FAILED)
            continue
          if copyMoveOptions['duplicateFolders'] == DUPLICATE_FOLDER_MERGE:
            if _identicalSourceTarget(fileId, targetChildren):
              entityActionNotPerformedWarning(kvList, Msg.NOT_MOVABLE_SAME_NAME_CURRENT_FOLDER_MERGE, j, jcount)
              _incrStatistic(statistics, STAT_FOLDER_FAILED)
              continue
          elif copyMoveOptions['duplicateFolders'] == DUPLICATE_FOLDER_UNIQUE_NAME:
            destName = _getUniqueFilename(destName, sourceMimeType, targetChildren)
          elif copyMoveOptions['duplicateFolders'] == DUPLICATE_FOLDER_SKIP:
            targetChild = _targetFilenameExists(destName, sourceMimeType, targetChildren)
            if targetChild is not None:
              entityModifierItemValueListActionNotPerformedWarning(kvList, Act.MODIFIER_TO,
                                                                   [Ent.DRIVE_FOLDER, newParentNameId, Ent.DRIVE_FOLDER, f"{destName}({targetChild['id']})"],
                                                                   Msg.DUPLICATE, j, jcount)
              _incrStatistic(statistics, STAT_FOLDER_DUPLICATE)
              continue
          if ((not copyMoveOptions['sourceDriveId'] and copyMoveOptions['destDriveId']) or
              (copyMoveOptions['mergeWithParent'] or copyMoveOptions['mergeWithParentRetain'] or copyMoveOptions['retainSourceFolders']) or
              (copyMoveOptions['duplicateFolders'] == DUPLICATE_FOLDER_MERGE and _targetFilenameExists(destName, sourceMimeType, targetChildren) is not None) or
              anyFolderPermissionOperations()):
            source['oldparents'] = sourceParents
            _recursiveFolderMove(drive, user, i, count, j, jcount,
                                 source, targetChildren, destName, newParentId, newParentName, dest['modifiedTime'], True)
            continue
          entityType = Ent.DRIVE_FOLDER
# Move file
        else:
          if copyMoveOptions['duplicateFiles'] in [DUPLICATE_FILE_OVERWRITE_ALL, DUPLICATE_FILE_OVERWRITE_OLDER] and _identicalSourceTarget(fileId, targetChildren):
            entityActionNotPerformedWarning(kvList, Msg.NOT_MOVABLE_SAME_NAME_CURRENT_FOLDER_OVERWRITE, j, jcount)
            _incrStatistic(statistics, STAT_FILE_FAILED)
            continue
          if _checkForDuplicateTargetFile(drive, user, j, jcount, source, destName, targetChildren, copyMoveOptions, statistics):
            continue
          destName = source['name'] # duplicatefiles uniquename may cause rename
          entityType = Ent.DRIVE_FILE
# Simple move file/folder
        if destName != sourceName:
          body = {'name': destName}
        else:
          body = {}
# All parents removed from top level moved item as non-path parents can't be determined
        removeParents = ','.join(sourceParents)
        _moveFile(drive, user, i, count, j, jcount, entityType, fileId, sourceName, destName, newParentId, newParentName, removeParents, body)
      except (GAPI.fileNotFound, GAPI.forbidden, GAPI.internalError, GAPI.insufficientFilePermissions, GAPI.unknownError,
              GAPI.invalid, GAPI.badRequest, GAPI.cannotCopyFile,
              GAPI.fileOwnerNotMemberOfTeamDrive, GAPI.fileOwnerNotMemberOfWriterDomain,
              GAPI.fileWriterTeamDriveMoveInDisabled,
              GAPI.cannotMoveTrashedItemIntoTeamDrive, GAPI.cannotMoveTrashedItemOutOfTeamDrive,
              GAPI.teamDrivesShortcutFileNotSupported, GAPI.crossDomainMoveRestriction) as e:
        entityActionFailedWarning([Ent.USER, user, Ent.DRIVE_FILE_OR_FOLDER_ID, fileId], str(e), j, jcount)
        _incrStatistic(statistics, STAT_FILE_FAILED)
      except (GAPI.serviceNotAvailable, GAPI.authError, GAPI.domainPolicy) as e:
        userDriveServiceNotEnabledWarning(user, str(e), i, count)
        _incrStatistic(statistics, STAT_FILE_FAILED)
        break
    Ind.Decrement()
    if copyMoveOptions['summary']:
      _printStatistics(user, statistics, i, count, False)

DELETE_DRIVEFILE_CHOICE_MAP = {'purge': 'delete', 'trash': 'trash', 'untrash': 'untrash'}
DELETE_DRIVEFILE_FUNCTION_TO_ACTION_MAP = {'delete': Act.PURGE, 'trash': Act.TRASH, 'untrash': Act.UNTRASH}
DELETE_DRIVEFILE_FUNCTION_TO_CAPABILITY_MAP = {'delete': 'canDelete', 'trash': 'canTrash', 'untrash': 'canUntrash'}

# gam <UserTypeEntity> delete drivefile <DriveFileEntity> [purge|trash|untrash] [shortcutandtarget [<Boolean>]]
