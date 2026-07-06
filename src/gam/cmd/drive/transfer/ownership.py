"""Drive transfer, ownership transfer, and claim operations.

Part of the transfer sub-package."""

"""File delete/trash/download/transfer/claim operations.

"""

"""GAM Google Drive file, permission, shared drive, and label management."""


from gamlib import api as API
from gamlib import settings as GC
from gamlib import gapi as GAPI
from gamlib import state as GM
from gamlib import msgs as Msg
from gam.util.svcacct import buildGAPIServiceObject
from gam.util.api_call import callGAPI, callGAPIpages
from gam.util.args import (
    OrderBy,
    escapeDriveFileName,
    getArgument,
    getBoolean,
    getCharacter,
    getChoice,
    getEmailAddress,
    getString,
    normalizeEmailAddressOrUID,
    splitEmailAddress,
)
from gam.util.csv_pf import CSVPrintFile
from gam.util.display import (
    entityActionFailedWarning,
    entityActionNotPerformedWarning,
    entityActionPerformed,
    entityDoesNotHaveItemWarning,
    entityModifierItemValueListActionPerformed,
    entityModifierNewValueItemValueListActionPerformed,
    entityPerformActionItemValue,
    entityPerformActionModifierNumItemsModifier,
    entityPerformActionNumItems,
    entityPerformActionNumItemsModifier,
    getPageMessageForWhom,
    printGettingAllEntityItemsForWhom,
    printKeyValueList,
    setGettingAllEntityItemsForWhom,
    userDriveServiceNotEnabledWarning,
)
from gam.cmd.drive.core import _getEntityMimeType
from gam.util.entity import (
    getEntityArgument,
    getEntityList,
    getEntityToModify,
)
from gam.util.errors import unknownArgumentExit, usageErrorExit
from gam.util.fileio import UNKNOWN
from gam.util.output import formatKeyValueList, printWarningMessage, systemErrorExit, formatFileSize
from gam.constants import MY_DRIVE, MY_NON_TRASHED_FOLDER_NAME, MY_NON_TRASHED_FOLDER_NAME_WITH_PARENTS, NON_TRASHED, TARGET_DRIVE_SPACE_ERROR_RC, WITH_PARENTS
from gam.util.tags import _substituteForUser

from gam.var import Act, Cmd, Ent, Ind
from gam.cmd.drive.core import (
    DRIVEFILE_ORDERBY_CHOICE_MAP,
    _checkForExistingShortcut,
    _getDriveFileParentInfo,
    _validateUserGetFileIDs,
    getDriveFileEntity,
    getDriveFileParentAttribute,
    initDriveFileAttributes,
    initDriveFileEntity,
)
from gam.cmd.drive.filepaths import (
    addFilePathsToRow,
    initFilePathInfo,
)
from gam.cmd.drive.filetree import buildFileTree
from gam.cmd.drive.transfer.fileops import TRANSFER_DRIVEFILE_ACL_ROLES_MAP

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

def transferDrive(users):

  def _getOwnerUser(childEntryInfo):
    if 'owners' not in childEntryInfo or not childEntryInfo['owners']:
      return (UNKNOWN, None)
    ownerUser = childEntryInfo['owners'][0]['emailAddress']
    if ownerUser not in thirdPartyOwners:
      _, ownerDrive = buildGAPIServiceObject(API.DRIVE3, ownerUser, displayError=False)
      thirdPartyOwners[ownerUser] = ownerDrive
    else:
      ownerDrive = thirdPartyOwners[ownerUser]
    return (ownerUser, ownerDrive)

  TARGET_PARENT_ID = 0
  TARGET_ORPHANS_PARENT_ID = 1

  def _buildTargetFile(folderName, folderParentId):
    try:
      op = 'Find Target Folder'
      result = callGAPIpages(targetDrive.files(), 'list', 'files',
                             throwReasons=GAPI.DRIVE_USER_THROW_REASONS+[GAPI.BAD_REQUEST],
                             retryReasons=[GAPI.UNKNOWN_ERROR],
                             orderBy=OBY.orderBy,
                             q=MY_NON_TRASHED_FOLDER_NAME_WITH_PARENTS.format(escapeDriveFileName(folderName), folderParentId),
                             fields='nextPageToken,files(id)')
      if result:
        return result[0]['id']
      op = 'Create Target Folder'
      return callGAPI(targetDrive.files(), 'create',
                      throwReasons=GAPI.DRIVE_USER_THROW_REASONS+[GAPI.FORBIDDEN, GAPI.INSUFFICIENT_PERMISSIONS, GAPI.INSUFFICIENT_PARENT_PERMISSIONS,
                                                                  GAPI.UNKNOWN_ERROR, GAPI.BAD_REQUEST, GAPI.STORAGE_QUOTA_EXCEEDED,
                                                                  GAPI.TEAMDRIVE_FILE_LIMIT_EXCEEDED, GAPI.TEAMDRIVE_HIERARCHY_TOO_DEEP],
                      body={'parents': [folderParentId], 'name': folderName, 'mimeType': MIMETYPE_GA_FOLDER}, fields='id')['id']
    except (GAPI.forbidden, GAPI.insufficientPermissions, GAPI.insufficientParentPermissions, GAPI.unknownError, GAPI.badRequest,
            GAPI.storageQuotaExceeded, GAPI.teamDriveFileLimitExceeded, GAPI.teamDriveHierarchyTooDeep) as e:
      entityActionFailedWarning([Ent.USER, targetUser, Ent.DRIVE_FOLDER, folderName], f'{op}: {str(e)}')
    except (GAPI.serviceNotAvailable, GAPI.authError, GAPI.domainPolicy) as e:
      userDriveServiceNotEnabledWarning(targetUser, str(e))
    return None

  def _buildTargetUserFolder():
    folderName = _substituteForUser(targetUserFolderPattern, sourceUser, sourceUserName)
    if not folderName:
      return targetFolderId
    return _buildTargetFile(folderName, targetFolderId)

  def _buildTargetUserOrphansFolder():
    folderName = _substituteForUser(targetUserOrphansFolderPattern, sourceUser, sourceUserName)
    if folderName:
      targetIds[TARGET_ORPHANS_PARENT_ID] = _buildTargetFile(folderName, targetIds[TARGET_PARENT_ID])
      if targetIds[TARGET_ORPHANS_PARENT_ID] is None:
        targetIds[TARGET_ORPHANS_PARENT_ID] = targetIds[TARGET_PARENT_ID]
    else:
      targetIds[TARGET_ORPHANS_PARENT_ID] = targetIds[TARGET_PARENT_ID]

  def _getMappedParentForRootParentOrOrphan(childEntryInfo, atSelectTop):
    if 'parents' not in childEntryInfo or not childEntryInfo['parents']:
      return (None, targetIds[TARGET_ORPHANS_PARENT_ID])
    if atSelectTop:
      return (childEntryInfo['parents'], targetIds[TARGET_PARENT_ID])
    for parentId in childEntryInfo['parents']:
      if parentId == sourceRootId:
        return ([sourceRootId], targetIds[TARGET_PARENT_ID])
    return (None, None)

  def _setUpdateRole(permission):
    return {'role': permission['role']}

  def _makeXferShortcut(drive, user, j, jcount, entityType, childId, childName, newParentId):
    kvList = [Ent.USER, user, entityType, f'{childName}({childId})']
    targetEntityType = Ent.DRIVE_FILE_SHORTCUT if entityType == Ent.DRIVE_FILE else Ent.DRIVE_FOLDER_SHORTCUT
    action = Act.Get()
    existingShortcut = _checkForExistingShortcut(drive, childId, childName, newParentId)
    if existingShortcut:
      Act.Set(Act.CREATE_SHORTCUT)
      entityModifierItemValueListActionPerformed(kvList, Act.MODIFIER_PREVIOUSLY_IN,
                                                 [Ent.DRIVE_FOLDER, newParentId, targetEntityType, f"{childName}({existingShortcut})"],
                                                 j, jcount)
      Act.Set(action)
      return
    body = {'name': childName, 'mimeType': MIMETYPE_GA_SHORTCUT,
            'parents': [newParentId], 'shortcutDetails': {'targetId': childId}}
    try:
      result = callGAPI(drive.files(), 'create',
                        throwReasons=GAPI.DRIVE_USER_THROW_REASONS+[GAPI.FORBIDDEN, GAPI.INSUFFICIENT_PERMISSIONS, GAPI.INSUFFICIENT_PARENT_PERMISSIONS,
                                                                    GAPI.INVALID, GAPI.BAD_REQUEST, GAPI.FILE_NOT_FOUND, GAPI.UNKNOWN_ERROR,
                                                                    GAPI.STORAGE_QUOTA_EXCEEDED, GAPI.TEAMDRIVES_SHARING_RESTRICTION_NOT_ALLOWED,
                                                                    GAPI.TEAMDRIVE_FILE_LIMIT_EXCEEDED, GAPI.TEAMDRIVE_HIERARCHY_TOO_DEEP, GAPI.SHORTCUT_TARGET_INVALID],
                        body=body, fields='id', supportsAllDrives=True)
      Act.Set(Act.CREATE_SHORTCUT)
      entityModifierItemValueListActionPerformed(kvList, Act.MODIFIER_IN,
                                                 [Ent.DRIVE_FOLDER, newParentId, targetEntityType, f"{childName}({result['id']})"],
                                                 j, jcount)
    except (GAPI.forbidden, GAPI.insufficientFilePermissions, GAPI.insufficientParentPermissions, GAPI.invalid, GAPI.badRequest,
            GAPI.fileNotFound, GAPI.unknownError, GAPI.storageQuotaExceeded, GAPI.teamDrivesSharingRestrictionNotAllowed,
	    GAPI.teamDriveFileLimitExceeded, GAPI.teamDriveHierarchyTooDeep, GAPI.shortcutTargetInvalid) as e:
      entityActionFailedWarning(kvList+[Ent.DRIVE_FILE_SHORTCUT, childName], str(e), j, jcount)
    Act.Set(action)

# Recreate source user shortcut in target user
  def _transferShortcut(j, jcount, childEntryInfo, childId, childName, newParentId):
    entityType =  Ent.DRIVE_FOLDER_SHORTCUT if childEntryInfo['shortcutDetails']['targetMimeType'] == MIMETYPE_GA_FOLDER else Ent.DRIVE_FILE_SHORTCUT
    kvList = [Ent.USER, sourceUser, entityType, f'{childName}({childId})']
    action = Act.Get()
    body = {'name': childName, 'mimeType': MIMETYPE_GA_SHORTCUT,
            'parents': [newParentId], 'shortcutDetails': {'targetId': childEntryInfo['shortcutDetails']['targetId']}}
    Act.Set(Act.RECREATE)
    try:
      result = callGAPI(targetDrive.files(), 'create',
                        throwReasons=GAPI.DRIVE_USER_THROW_REASONS+[GAPI.FORBIDDEN, GAPI.INSUFFICIENT_PERMISSIONS, GAPI.INSUFFICIENT_PARENT_PERMISSIONS,
                                                                    GAPI.INVALID, GAPI.BAD_REQUEST, GAPI.FILE_NOT_FOUND, GAPI.UNKNOWN_ERROR,
                                                                    GAPI.STORAGE_QUOTA_EXCEEDED, GAPI.TEAMDRIVES_SHARING_RESTRICTION_NOT_ALLOWED,
                                                                    GAPI.TEAMDRIVE_FILE_LIMIT_EXCEEDED, GAPI.TEAMDRIVE_HIERARCHY_TOO_DEEP, GAPI.SHORTCUT_TARGET_INVALID],
                        body=body, fields='id', supportsAllDrives=True)
      shortcutId = result['id']
      entityModifierNewValueItemValueListActionPerformed(kvList, Act.MODIFIER_IN, None, [Ent.USER, targetUser,
                                                                                         Ent.DRIVE_FOLDER, newParentId, entityType, f"{shortcutId})"],
                                                         j, jcount)
    except (GAPI.forbidden, GAPI.insufficientFilePermissions, GAPI.insufficientParentPermissions, GAPI.invalid, GAPI.badRequest,
            GAPI.fileNotFound, GAPI.unknownError, GAPI.storageQuotaExceeded, GAPI.teamDrivesSharingRestrictionNotAllowed,
            GAPI.teamDriveFileLimitExceeded, GAPI.teamDriveHierarchyTooDeep, GAPI.shortcutTargetInvalid) as e:
      entityActionFailedWarning(kvList+[Ent.DRIVE_FILE_SHORTCUT, childName], str(e), j, jcount)
      Act.Set(action)
      return
    if ownerRetainRoleBody['role'] == 'none':
      Act.Set(Act.DELETE_SHORTCUT)
      kvList = [Ent.USER, sourceUser, entityType, f'{childName}({childId})']
      try:
        callGAPI(sourceDrive.files(), 'delete',
                 throwReasons=GAPI.DRIVE_ACCESS_THROW_REASONS+[GAPI.FILE_NEVER_WRITABLE],
                 fileId=childId, supportsAllDrives=True)
        entityActionPerformed(kvList, j, jcount)
      except (GAPI.fileNotFound, GAPI.forbidden, GAPI.internalError, GAPI.insufficientFilePermissions, GAPI.unknownError, GAPI.fileNeverWritable) as e:
        entityActionFailedWarning(kvList, str(e), j, jcount)
    Act.Set(action)

  def _transferFile(childEntry, i, count, j, jcount, atSelectTop):
    childEntryInfo = childEntry['info']
    childFileId = childEntryInfo['id']
    childFileName = childEntryInfo['name']
    childFileType = _getEntityMimeType(childEntryInfo)
# Owned files
    if childEntryInfo['ownedByMe']:
      childEntryInfo['sourcePermission'] = {'role': 'owner'}
      for permission in childEntryInfo.get('permissions', []):
        if targetPermissionId == permission['id']:
          childEntryInfo['targetPermission'] = _setUpdateRole(permission)
          updateTargetPermission = True
          break
      else:
        childEntryInfo['targetPermission'] = {'role': 'none'}
        updateTargetPermission = False
      if csvPF:
        csvPF.WriteRow({'OldOwner': sourceUser, 'NewOwner': targetUser, 'type': Ent.Singular(childFileType), 'id': childFileId, 'name': childFileName, 'role': 'owner'})
        return
      Act.Set(Act.TRANSFER_OWNERSHIP)
      addTargetParent = None
      removeSourceParents = set()
      removeTargetParents = set()
      childParents = childEntryInfo.get('parents', [])
      if childParents:
        for parentId in childParents:
          if parentId in parentIdMap:
            addTargetParent = parentIdMap[parentId]
            if parentId != sourceRootId:
              removeSourceParents.add(parentId)
            elif not mergeWithTarget and targetFolderId != targetRootId:
              removeTargetParents.add(targetRootId)
      else:
        if targetIds[TARGET_ORPHANS_PARENT_ID] is None:
          _buildTargetUserOrphansFolder()
        addTargetParent = targetIds[TARGET_ORPHANS_PARENT_ID]
        removeTargetParents.add(targetRootId)
      try:
        actionUser = sourceUser
        if childEntryInfo['mimeType'] != MIMETYPE_GA_SHORTCUT:
          if not updateTargetPermission:
            op = 'Create Source ACL'
            callGAPI(sourceDrive.permissions(), 'create',
                     throwReasons=GAPI.DRIVE_ACCESS_THROW_REASONS+[GAPI.BAD_REQUEST, GAPI.INVALID_SHARING_REQUEST, GAPI.SHARING_RATE_LIMIT_EXCEEDED],
                     fileId=childFileId, sendNotificationEmail=False, body=targetWriterPermissionsBody, fields='')
          op = 'Update Source ACL'
          callGAPI(sourceDrive.permissions(), 'update',
                   throwReasons=GAPI.DRIVE_ACCESS_THROW_REASONS+[GAPI.BAD_REQUEST, GAPI.INVALID_OWNERSHIP_TRANSFER,
                                                                 GAPI.PERMISSION_NOT_FOUND, GAPI.SHARING_RATE_LIMIT_EXCEEDED],
                   fileId=childFileId, permissionId=targetPermissionId,
                   transferOwnership=True, body={'role': 'owner'}, fields='')
          if removeSourceParents:
            op = 'Remove Source Parents'
            callGAPI(sourceDrive.files(), 'update',
                     throwReasons=GAPI.DRIVE_ACCESS_THROW_REASONS, retryReasons=[GAPI.BAD_REQUEST, GAPI.FILE_NOT_FOUND], triesLimit=3,
                     fileId=childFileId, removeParents=','.join(removeSourceParents), fields='')
          actionUser = targetUser
          if addTargetParent or removeTargetParents:
            op = 'Add/Remove Target Parents'
            callGAPI(targetDrive.files(), 'update',
                     throwReasons=GAPI.DRIVE_ACCESS_THROW_REASONS+[GAPI.CANNOT_ADD_PARENT, GAPI.INSUFFICIENT_PARENT_PERMISSIONS],
                     retryReasons=[GAPI.BAD_REQUEST, GAPI.FILE_NOT_FOUND], triesLimit=3,
                     fileId=childFileId,
                     addParents=addTargetParent, removeParents=','.join(removeTargetParents), fields='')
          entityModifierNewValueItemValueListActionPerformed([Ent.USER, sourceUser, childFileType, childFileName], Act.MODIFIER_TO, None, [Ent.USER, targetUser], j, jcount)
        else:
          if topSourceId in childParents:
            _transferShortcut(j, jcount, childEntryInfo, childFileId, childFileName, addTargetParent)
          else:
            entityModifierNewValueItemValueListActionPerformed([Ent.USER, sourceUser, childFileType, childFileName], Act.MODIFIER_TO, None, [Ent.USER, targetUser], j, jcount)
      except (GAPI.fileNotFound, GAPI.forbidden, GAPI.internalError, GAPI.unknownError,
              GAPI.badRequest, GAPI.sharingRateLimitExceeded, GAPI.cannotAddParent, GAPI.insufficientParentPermissions) as e:
        entityActionFailedWarning([Ent.USER, actionUser, childFileType, childFileName], f'{op}: {str(e)}', j, jcount)
      except (GAPI.insufficientFilePermissions, GAPI.fileOwnerNotMemberOfWriterDomain, GAPI.crossDomainMoveRestriction) as e:
        if not createShortcutsForNonmovableFiles:
          entityActionFailedWarning([Ent.USER, actionUser, childFileType, childFileName], f'{op}: {str(e)}', j, jcount)
        else:
          _makeXferShortcut(targetDrive, targetUser, j, jcount, childFileType, childFileId, childFileName, addTargetParent)
      except GAPI.permissionNotFound:
        entityDoesNotHaveItemWarning([Ent.USER, actionUser, childFileType, childFileName, Ent.PERMISSION_ID, targetPermissionId], j, jcount)
      except GAPI.invalidSharingRequest as e:
        entityActionFailedWarning([Ent.USER, actionUser, childFileType, childFileName], Ent.TypeNameMessage(Ent.PERMISSION_ID, targetPermissionId, str(e)), j, jcount)
      except (GAPI.serviceNotAvailable, GAPI.authError, GAPI.domainPolicy) as e:
        userDriveServiceNotEnabledWarning(actionUser, str(e), i, count)
# Non-owned files
    else:
      Act.Set(Act.PROCESS)
      for permission in childEntryInfo.get('permissions', []):
        if sourcePermissionId == permission['id']:
          childEntryInfo['sourcePermission'] = _setUpdateRole(permission)
          getSourcePermissionFromOwner = False
          break
      else:
        childEntryInfo['sourcePermission'] = nonOwnerRetainRoleBody
        getSourcePermissionFromOwner = True
      for permission in childEntryInfo.get('permissions', []):
        if targetPermissionId == permission['id']:
          childEntryInfo['targetPermission'] = _setUpdateRole(permission)
          getTargetPermissionFromOwner = False
          break
      else:
        childEntryInfo['targetPermission'] = {'role': 'none'}
        getTargetPermissionFromOwner = True
      ownerUser, ownerDrive = _getOwnerUser(childEntryInfo)
      if not ownerDrive:
        entityActionNotPerformedWarning([Ent.USER, sourceUser, childFileType, childFileName],
                                        Msg.SERVICE_NOT_APPLICABLE_THIS_ADDRESS.format(ownerUser), j, jcount)
        return
      if getSourcePermissionFromOwner or getTargetPermissionFromOwner:
        try:
          permissions = callGAPIpages(ownerDrive.permissions(), 'list', 'permissions',
                                      throwReasons=GAPI.DRIVE3_GET_ACL_REASONS+[GAPI.BAD_REQUEST],
                                      retryReasons=GAPI.SERVICE_NOT_AVAILABLE_RETRY_REASONS,
                                      fileId=childFileId, fields='nextPageToken,permissions')
          if getSourcePermissionFromOwner:
            for permission in permissions:
              if sourcePermissionId == permission['id']:
                childEntryInfo['sourcePermission'] = _setUpdateRole(permission)
                break
            else:
              childEntryInfo['sourcePermission'] = nonOwnerRetainRoleBody
          if getTargetPermissionFromOwner:
            for permission in permissions:
              if targetPermissionId == permission['id']:
                childEntryInfo['targetPermission'] = _setUpdateRole(permission)
                break
            else:
              childEntryInfo['targetPermission'] = {'role': 'none'}
        except (GAPI.fileNotFound, GAPI.forbidden, GAPI.internalError,
                GAPI.insufficientAdministratorPrivileges, GAPI.insufficientFilePermissions,
                GAPI.unknownError, GAPI.invalid, GAPI.badRequest) as e:
          entityActionFailedWarning([Ent.USER, ownerUser, childFileType, childFileName], str(e), j, jcount)
          return
        except (GAPI.serviceNotAvailable, GAPI.authError, GAPI.domainPolicy) as e:
          userDriveServiceNotEnabledWarning(ownerUser, str(e), i, count)
          return
      if csvPF:
        csvPF.WriteRow({'OldOwner': sourceUser, 'NewOwner': targetUser, 'type': Ent.Singular(childFileType),
                        'id': childFileId, 'name': childFileName, 'role': childEntryInfo['sourcePermission']['role']})
        return
      if (childFileType == Ent.DRIVE_FOLDER) and (childEntryInfo['targetPermission']['role'] == 'none') and (ownerRetainRoleBody['role'] == 'none'):
        if targetIds[TARGET_ORPHANS_PARENT_ID] is None:
          _buildTargetUserOrphansFolder()
        parentIdMap[childFileId] = _buildTargetFile(childFileName, targetIds[TARGET_ORPHANS_PARENT_ID])
        entityActionPerformed([Ent.USER, sourceUser, childFileType, childFileName], j, jcount)
        return
      existingParentIds, mappedParentId = _getMappedParentForRootParentOrOrphan(childEntryInfo, atSelectTop)
      if mappedParentId is not None:
# Give temporary writer access to target user so other actions can be performed
        if childEntryInfo['targetPermission']['role'] in {'none', 'reader'}:
          try:
            callGAPI(ownerDrive.permissions(), 'create',
                     throwReasons=GAPI.DRIVE_ACCESS_THROW_REASONS+[GAPI.INVALID_SHARING_REQUEST, GAPI.SHARING_RATE_LIMIT_EXCEEDED],
                     fileId=childFileId, sendNotificationEmail=False, body=targetWriterPermissionsBody, fields='')
          except (GAPI.fileNotFound, GAPI.forbidden, GAPI.internalError, GAPI.insufficientFilePermissions, GAPI.unknownError,
                  GAPI.badRequest, GAPI.sharingRateLimitExceeded) as e:
            entityActionFailedWarning([Ent.USER, ownerUser, childFileType, childFileName], str(e), j, jcount)
            return
          except GAPI.invalidSharingRequest as e:
            entityActionFailedWarning([Ent.USER, ownerUser, childFileType, childFileName],
                                      Ent.TypeNameMessage(Ent.PERMISSION_ID, sourcePermissionId, str(e)), j, jcount)
            return
          except (GAPI.serviceNotAvailable, GAPI.authError, GAPI.domainPolicy) as e:
            userDriveServiceNotEnabledWarning(ownerUser, str(e), i, count)
            return
        if existingParentIds is not None:
# We have to make a shortcut to a non-owned non-orphan as we can't change the parents
          try:
            body = {'name': childFileName, 'mimeType': MIMETYPE_GA_SHORTCUT, 'parents': [mappedParentId], 'shortcutDetails': {'targetId': childFileId}}
            callGAPI(targetDrive.files(), 'create',
                     throwReasons=GAPI.DRIVE_USER_THROW_REASONS+[GAPI.FORBIDDEN, GAPI.INSUFFICIENT_PERMISSIONS, GAPI.INSUFFICIENT_PARENT_PERMISSIONS,
                                                                 GAPI.INVALID, GAPI.BAD_REQUEST, GAPI.FILE_NOT_FOUND, GAPI.UNKNOWN_ERROR,
                                                                 GAPI.STORAGE_QUOTA_EXCEEDED, GAPI.TEAMDRIVES_SHARING_RESTRICTION_NOT_ALLOWED,
                                                                 GAPI.TEAMDRIVE_FILE_LIMIT_EXCEEDED, GAPI.TEAMDRIVE_HIERARCHY_TOO_DEEP],
                     body=body, fields='', supportsAllDrives=True)
          except (GAPI.forbidden, GAPI.insufficientFilePermissions, GAPI.insufficientParentPermissions, GAPI.invalid, GAPI.badRequest,
                  GAPI.fileNotFound, GAPI.unknownError, GAPI.storageQuotaExceeded, GAPI.teamDrivesSharingRestrictionNotAllowed,
                  GAPI.teamDriveFileLimitExceeded, GAPI.teamDriveHierarchyTooDeep) as e:
            entityActionFailedWarning([Ent.USER, targetUser, childFileType, childFileName, Ent.DRIVE_FILE_SHORTCUT, body['name']], str(e), j, jcount)
            return
# Delete existing parents
          try:
            callGAPI(sourceDrive.files(), 'update',
                     throwReasons=GAPI.DRIVE_ACCESS_THROW_REASONS+[GAPI.BAD_REQUEST],
                     retryReasons=[GAPI.FILE_NOT_FOUND], triesLimit=3,
                     fileId=childFileId,
                     removeParents=','.join(existingParentIds), body={}, fields='')
          except (GAPI.fileNotFound, GAPI.forbidden, GAPI.internalError, GAPI.insufficientFilePermissions, GAPI.unknownError,
                  GAPI.badRequest) as e:
            entityActionFailedWarning([Ent.USER, sourceUser, childFileType, childFileName], str(e), j, jcount)
            return
          except (GAPI.serviceNotAvailable, GAPI.authError, GAPI.domainPolicy) as e:
            userDriveServiceNotEnabledWarning(sourceUser, str(e), i, count)
            return
# 5.31.03 - Non-owned files without parents are SharedWithMe, parents can not be changed
#        else:
## We can add a parent when transferring an orphan
#          try:
#            callGAPI(targetDrive.files(), 'update',
#                     throwReasons=GAPI.DRIVE_ACCESS_THROW_REASONS+[GAPI.BAD_REQUEST, GAPI.CANNOT_ADD_PARENT, GAPI.INSUFFICIENT_PARENT_PERMISSIONS],
#                     retryReasons=[GAPI.FILE_NOT_FOUND], triesLimit=3,
#                     fileId=childFileId,
#                     addParents=mappedParentId, body={}, fields='')
#          except (GAPI.fileNotFound, GAPI.forbidden, GAPI.internalError, GAPI.insufficientFilePermissions, GAPI.insufficientParentPermissions, GAPI.unknownError,
#                  GAPI.badRequest, GAPI.cannotAddParent) as e:
#            entityActionFailedWarning([Ent.USER, targetUser, childFileType, childFileName], str(e), j, jcount)
#            return
#          except (GAPI.serviceNotAvailable, GAPI.authError, GAPI.domainPolicy) as e:
#            userDriveServiceNotEnabledWarning(targetUser, str(e), i, count)
#            return
      entityActionPerformed([Ent.USER, sourceUser, childFileType, childFileName], j, jcount)

  def _manageRoleRetention(childEntry, i, count, j, jcount, atSelectTop):
    def _setTargetInsertBody(permission):
      return {'role': permission['role'], 'type': 'user', 'emailAddress': targetUser}

    def _checkForDiminishedTargetRole(currentPermission, newPermission):
      if currentPermission['role'] in {'owner', 'organizer', 'fileOrganizer', 'writer'}:
        return False
      if (currentPermission['role'] == 'commenter') and (newPermission['role'] == 'reader'):
        return False
      return True

    childEntryInfo = childEntry['info']
    childFileId = childEntryInfo['id']
    childFileName = childEntryInfo['name']
    childFileType = _getEntityMimeType(childEntryInfo)
    if childEntryInfo['mimeType'] == MIMETYPE_GA_SHORTCUT:
      if showRetentionMessages:
        entityActionNotPerformedWarning([Ent.USER, sourceUser, childFileType, childFileName, Ent.ROLE, ownerRetainRoleBody['role']], Msg.NOT_APPROPRIATE, j, jcount)
      return
    if childEntryInfo['ownedByMe']:
      try:
        if ownerRetainRoleBody['role'] != 'none':
          if ownerRetainRoleBody['role'] != 'writer':
            callGAPI(targetDrive.permissions(), 'update',
                     throwReasons=GAPI.DRIVE_ACCESS_THROW_REASONS+[GAPI.PERMISSION_NOT_FOUND, GAPI.BAD_REQUEST, GAPI.SHARING_RATE_LIMIT_EXCEEDED],
                     fileId=childFileId, permissionId=sourcePermissionId, body=ownerRetainRoleBody, fields='')
        else:
          callGAPI(targetDrive.permissions(), 'delete',
                   throwReasons=GAPI.DRIVE_ACCESS_THROW_REASONS+GAPI.DRIVE3_DELETE_ACL_THROW_REASONS,
                   fileId=childFileId, permissionId=sourcePermissionId)
        if showRetentionMessages:
          entityActionPerformed([Ent.USER, sourceUser, childFileType, childFileName, Ent.ROLE, ownerRetainRoleBody['role']], j, jcount)
      except (GAPI.fileNotFound, GAPI.forbidden, GAPI.internalError, GAPI.insufficientFilePermissions, GAPI.unknownError, GAPI.invalid,
              GAPI.badRequest, GAPI.notFound, GAPI.cannotRemoveOwner,
              GAPI.cannotModifyInheritedTeamDrivePermission, GAPI.cannotModifyInheritedPermission,
              GAPI.insufficientAdministratorPrivileges, GAPI.sharingRateLimitExceeded, GAPI.cannotDeletePermission,
              GAPI.fileNeverWritable) as e:
        entityActionFailedWarning([Ent.USER, sourceUser, childFileType, childFileName], str(e), j, jcount)
      except GAPI.permissionNotFound:
        entityDoesNotHaveItemWarning([Ent.USER, sourceUser, childFileType, childFileName, Ent.PERMISSION_ID, sourcePermissionId], j, jcount)
      except (GAPI.serviceNotAvailable, GAPI.authError, GAPI.domainPolicy) as e:
        userDriveServiceNotEnabledWarning(sourceUser, str(e), i, count)
    else:
      ownerUser, ownerDrive = _getOwnerUser(childEntryInfo)
      if not ownerDrive:
        return
      if nonOwnerRetainRoleBody['role'] == 'current':
        sourceUpdateRole = childEntryInfo['sourcePermission']
      else:
        sourceUpdateRole = nonOwnerRetainRoleBody
      if 'targetPermission' not in childEntryInfo:
        childEntryInfo['targetPermission'] = {'role': 'current'}
        errorTargetRole = True
      else:
        errorTargetRole = False
      if nonOwnerTargetRoleBody['role'] == 'current':
        targetInsertBody = _setTargetInsertBody(childEntryInfo['targetPermission'])
        resetTargetRole = False
      elif nonOwnerTargetRoleBody['role'] == 'source':
        targetInsertBody = _setTargetInsertBody(childEntryInfo['sourcePermission'])
        resetTargetRole = True
      else:
        targetInsertBody = _setTargetInsertBody(nonOwnerTargetRoleBody)
        resetTargetRole = True
      if not errorTargetRole:
        if resetTargetRole:
          resetTargetRole = _checkForDiminishedTargetRole(childEntryInfo['targetPermission'], targetInsertBody)
        else:
          _, mappedParentId = _getMappedParentForRootParentOrOrphan(childEntryInfo, atSelectTop)
          if mappedParentId is not None and childEntryInfo['targetPermission']['role'] in {'none', 'reader'}:
            resetTargetRole = True
# Update owner permissions
      try:
        if nonOwnerRetainRoleBody['role'] != 'none':
          if nonOwnerRetainRoleBody['role'] != 'current':
            callGAPI(ownerDrive.permissions(), 'update',
                     throwReasons=GAPI.DRIVE_ACCESS_THROW_REASONS+[GAPI.PERMISSION_NOT_FOUND, GAPI.BAD_REQUEST, GAPI.SHARING_RATE_LIMIT_EXCEEDED],
                     fileId=childFileId, permissionId=sourcePermissionId, body=sourceUpdateRole, fields='')
        else:
          try:
            callGAPI(ownerDrive.permissions(), 'delete',
                     throwReasons=GAPI.DRIVE_ACCESS_THROW_REASONS+GAPI.DRIVE3_DELETE_ACL_THROW_REASONS,
                     fileId=childFileId, permissionId=sourcePermissionId)
          except GAPI.permissionNotFound:
            pass
        if showRetentionMessages:
          entityActionPerformed([Ent.USER, sourceUser, childFileType, childFileName, Ent.ROLE, sourceUpdateRole['role']], j, jcount)
      except (GAPI.fileNotFound, GAPI.forbidden, GAPI.internalError, GAPI.insufficientFilePermissions, GAPI.unknownError, GAPI.invalid,
              GAPI.badRequest, GAPI.notFound, GAPI.cannotRemoveOwner,
              GAPI.cannotModifyInheritedTeamDrivePermission, GAPI.cannotModifyInheritedPermission,
              GAPI.insufficientAdministratorPrivileges, GAPI.sharingRateLimitExceeded, GAPI.cannotDeletePermission,
              GAPI.fileNeverWritable) as e:
        entityActionFailedWarning([Ent.USER, ownerUser, childFileType, childFileName], str(e), j, jcount)
      except GAPI.permissionNotFound:
        entityDoesNotHaveItemWarning([Ent.USER, ownerUser, childFileType, childFileName, Ent.PERMISSION_ID, sourcePermissionId], j, jcount)
      except (GAPI.serviceNotAvailable, GAPI.authError, GAPI.domainPolicy) as e:
        userDriveServiceNotEnabledWarning(ownerUser, str(e), i, count)
# Update target permissions
      if resetTargetRole and targetUser != ownerUser:
        try:
          if nonOwnerTargetRoleBody['role'] != 'none':
            if nonOwnerTargetRoleBody['role'] != 'current' and targetInsertBody['role'] not in {'current', 'none'}:
              callGAPI(ownerDrive.permissions(), 'create',
                       throwReasons=GAPI.DRIVE_ACCESS_THROW_REASONS+[GAPI.INVALID_SHARING_REQUEST, GAPI.SHARING_RATE_LIMIT_EXCEEDED],
                       fileId=childFileId, sendNotificationEmail=False, body=targetInsertBody, fields='')
          else:
            try:
              callGAPI(ownerDrive.permissions(), 'delete',
                       throwReasons=GAPI.DRIVE_ACCESS_THROW_REASONS+GAPI.DRIVE3_DELETE_ACL_THROW_REASONS,
                       fileId=childFileId, permissionId=targetPermissionId)
            except GAPI.permissionNotFound:
              pass
          if showRetentionMessages:
            entityActionPerformed([Ent.USER, targetUser, childFileType, childFileName, Ent.ROLE, targetInsertBody['role']], j, jcount)
        except (GAPI.fileNotFound, GAPI.forbidden, GAPI.internalError, GAPI.insufficientFilePermissions, GAPI.unknownError, GAPI.invalid,
                GAPI.badRequest, GAPI.notFound, GAPI.permissionNotFound, GAPI.cannotRemoveOwner,
                GAPI.cannotModifyInheritedTeamDrivePermission, GAPI.cannotModifyInheritedPermission,
                GAPI.insufficientAdministratorPrivileges, GAPI.sharingRateLimitExceeded, GAPI.cannotDeletePermission,
                GAPI.fileNeverWritable) as e:
          entityActionFailedWarning([Ent.USER, ownerUser, childFileType, childFileName], str(e), j, jcount)
        except GAPI.invalidSharingRequest as e:
          entityActionFailedWarning([Ent.USER, ownerUser, childFileType, childFileName], Ent.TypeNameMessage(Ent.PERMISSION_ID, targetPermissionId, str(e)), j, jcount)
        except (GAPI.serviceNotAvailable, GAPI.authError, GAPI.domainPolicy) as e:
          userDriveServiceNotEnabledWarning(sourceUser, str(e), i, count)
      elif showRetentionMessages:
        entityActionPerformed([Ent.USER, targetUser, childFileType, childFileName, Ent.ROLE, childEntryInfo['targetPermission']['role']], j, jcount)

  def _transferDriveFilesFromTree(fileEntry, i, count):
    jcount = len(fileEntry['children'])
    if jcount == 0:
      return
    j = 0
    for childFileId in fileEntry['children']:
      j += 1
      childEntry = fileTree.get(childFileId)
      if not childEntry or childFileId in filesTransferred:
        continue
      if childFileId in skipFileIdEntity['list']:
        entityActionNotPerformedWarning([Ent.USER, sourceUser, _getEntityMimeType(childEntry['info']), f'{childEntry["info"]["name"]} ({childFileId})'],
                                        Msg.IN_SKIPIDS, j, jcount)
        continue
      filesTransferred.add(childFileId)
      _transferFile(childEntry, i, count, j, jcount, False)
      if childEntry['info']['mimeType'] == MIMETYPE_GA_FOLDER:
        Ind.Increment()
        _transferDriveFilesFromTree(childEntry, i, count)
        Ind.Decrement()

  def _manageRoleRetentionDriveFilesFromTree(fileEntry, i, count):
    jcount = len(fileEntry['children'])
    if jcount == 0:
      return
    j = 0
    for childFileId in fileEntry['children']:
      j += 1
      childEntry = fileTree.get(childFileId)
      if not childEntry or childFileId in filesTransferred or childFileId in skipFileIdEntity['list']:
        continue
      filesTransferred.add(childFileId)
      _manageRoleRetention(childEntry, i, count, j, jcount, False)
      if childEntry['info']['mimeType'] == MIMETYPE_GA_FOLDER:
        Ind.Increment()
        _manageRoleRetentionDriveFilesFromTree(childEntry, i, count)
        Ind.Decrement()

  def _identifyDriveFileAndChildren(fileEntry, i, count):
    fileId = fileEntry['id']
    if fileId not in fileTree:
      fileTree[fileId] = {'info': fileEntry, 'children': []}
    if fileEntry['mimeType'] != MIMETYPE_GA_FOLDER:
      return
    try:
      children = callGAPIpages(sourceDrive.files(), 'list', 'files',
                               throwReasons=GAPI.DRIVE_USER_THROW_REASONS,
                               retryReasons=[GAPI.UNKNOWN_ERROR],
                               orderBy=OBY.orderBy, q=WITH_PARENTS.format(fileId),
                               fields='nextPageToken,files(id,name,parents,mimeType,ownedByMe,trashed,owners(emailAddress,permissionId),permissions(id,role),shortcutDetails)',
                               pageSize=GC.Values[GC.DRIVE_MAX_RESULTS])
    except (GAPI.serviceNotAvailable, GAPI.authError, GAPI.domainPolicy) as e:
      userDriveServiceNotEnabledWarning(sourceUser, str(e), i, count)
      return
    for childEntry in children:
      if not childEntry['trashed']:
        childId = childEntry['id']
        if childId in skipFileIdEntity['list']:
          entityActionNotPerformedWarning([Ent.USER, sourceUser, _getEntityMimeType(childEntry), f'{childEntry["name"]} ({childId})'],
                                          Msg.IN_SKIPIDS)
          continue
        fileTree[fileId]['children'].append(childId)
        _identifyDriveFileAndChildren(childEntry, i, count)

  def _transferDriveFileAndChildren(fileEntry, i, count, j, jcount, atSelectTop):
    fileId = fileEntry['info']['id']
    if fileId in filesTransferred:
      return
    if fileEntry['info']['name'] != MY_DRIVE:
      filesTransferred.add(fileId)
      if not atSelectTop or not mergeWithTarget:
        _transferFile(fileEntry, i, count, j, jcount, atSelectTop)
    kcount = len(fileEntry['children'])
    if kcount == 0:
      return
    k = 0
    for childFileId in fileEntry['children']:
      k += 1
      childEntry = fileTree.get(childFileId)
      if childEntry:
        Ind.Increment()
        _transferDriveFileAndChildren(childEntry, i, count, k, kcount, False)
        Ind.Decrement()

  def _manageRoleRetentionDriveFileAndChildren(fileEntry, i, count, j, jcount, atSelectTop):
    fileId = fileEntry['info']['id']
    if fileId in filesTransferred:
      return
    if fileEntry['info']['name'] != MY_DRIVE:
      filesTransferred.add(fileId)
      if not atSelectTop or not mergeWithTarget:
        _manageRoleRetention(fileEntry, i, count, j, jcount, atSelectTop)
    kcount = len(fileEntry['children'])
    if kcount == 0:
      return
    k = 0
    for childFileId in fileEntry['children']:
      k += 1
      childEntry = fileTree.get(childFileId)
      if childEntry:
        Ind.Increment()
        _manageRoleRetentionDriveFileAndChildren(childEntry, i, count, k, kcount, False)
        Ind.Decrement()

  targetUser = getEmailAddress()
  buildTree = True
  csvPF = None
  OBY = OrderBy(DRIVEFILE_ORDERBY_CHOICE_MAP)
  ownerRetainRoleBody = {'role': 'none'}
  nonOwnerRetainRoleBody = {}
  nonOwnerTargetRoleBody = {'role': 'source'}
  showRetentionMessages = True
  targetFolderId = targetFolderName = None
  targetUserFolderPattern = '#user# old files'
  targetUserOrphansFolderPattern = '#user# orphaned files'
  targetIds = [None, None]
  createShortcutsForNonmovableFiles = False
  mergeWithTarget = False
  thirdPartyOwners = {}
  skipFileIdEntity = initDriveFileEntity()
  while Cmd.ArgumentsRemaining():
    myarg = getArgument()
    if myarg == 'keepuser':
      ownerRetainRoleBody['role'] = 'writer'
    elif myarg == 'retainrole':
      ownerRetainRoleBody['role'] = getChoice(TRANSFER_DRIVEFILE_ACL_ROLES_MAP, mapChoice=True)
      if ownerRetainRoleBody['role'] in {'source', 'current'}:
        ownerRetainRoleBody['role'] = 'writer'
    elif myarg == 'nonownerretainrole':
      nonOwnerRetainRoleBody['role'] = getChoice(TRANSFER_DRIVEFILE_ACL_ROLES_MAP, mapChoice=True)
      if nonOwnerRetainRoleBody['role'] == 'source':
        nonOwnerRetainRoleBody['role'] = 'current'
    elif myarg == 'nonownertargetrole':
      nonOwnerTargetRoleBody['role'] = getChoice(TRANSFER_DRIVEFILE_ACL_ROLES_MAP, mapChoice=True)
    elif myarg == 'noretentionmessages':
      showRetentionMessages = False
    elif myarg == 'orderby':
      OBY.GetChoice()
    elif myarg == 'targetfolderid':
      targetFolderIdLocation = Cmd.Location()
      targetFolderId = getString(Cmd.OB_DRIVE_FILE_ID, minLen=0)
    elif myarg == 'targetfoldername':
      targetFolderNameLocation = Cmd.Location()
      targetFolderName = getString(Cmd.OB_DRIVE_FILE_NAME, minLen=0)
    elif myarg == 'targetuserfoldername':
      targetUserFolderPattern = getString(Cmd.OB_DRIVE_FILE_NAME, minLen=0)
    elif myarg == 'targetuserorphansfoldername':
      targetUserOrphansFolderPattern = getString(Cmd.OB_DRIVE_FILE_NAME, minLen=0)
    elif myarg == 'select':
      fileIdEntity = getDriveFileEntity()
      buildTree = False
    elif myarg == 'mergewithtarget':
      mergeWithTarget = getBoolean()
    elif myarg == 'createshortcutsfornonmovablefiles':
      createShortcutsForNonmovableFiles = getBoolean()
    elif myarg == 'skipids':
      skipFileIdEntity = getDriveFileEntity()
    elif myarg == 'preview':
      csvPF = CSVPrintFile(['OldOwner', 'NewOwner', 'type', 'id', 'name', 'role'])
    elif csvPF and myarg == 'todrive':
      csvPF.GetTodriveParameters()
    else:
      unknownArgumentExit()
  if not nonOwnerRetainRoleBody:
    nonOwnerRetainRoleBody = ownerRetainRoleBody
  if not OBY.orderBy:
    OBY.SetItems('folder,createdTime')
  targetUser, targetDrive = buildGAPIServiceObject(API.DRIVE3, targetUser)
  if not targetDrive:
    return
  try:
    result = callGAPI(targetDrive.about(), 'get',
                      throwReasons=GAPI.DRIVE_USER_THROW_REASONS,
                      fields='storageQuota,user(permissionId)')
    if result['storageQuota'].get('limit'):
      targetDriveFree = int(result['storageQuota']['limit'])-int(result['storageQuota']['usageInDrive'])
    else:
      targetDriveFree = None
    targetPermissionId = result['user']['permissionId']
    result = callGAPI(targetDrive.files(), 'get',
                      throwReasons=GAPI.DRIVE_USER_THROW_REASONS,
                      fileId=ROOT, fields='id,name')
    targetRootId = result['id']
    if not targetFolderId and not targetFolderName:
      targetFolderId = targetRootId
      targetFolderName = result['name']
    else:
      if targetFolderId:
        targetFolder = callGAPI(targetDrive.files(), 'get',
                                throwReasons=GAPI.DRIVE_GET_THROW_REASONS,
                                fileId=targetFolderId, fields='id,name,mimeType,ownedByMe')
        if targetFolder['mimeType'] != MIMETYPE_GA_FOLDER:
          Cmd.SetLocation(targetFolderIdLocation)
          usageErrorExit(formatKeyValueList(Ind.Spaces(),
                                            [Ent.Singular(Ent.USER), targetUser,
                                             Ent.Singular(Ent.DRIVE_FOLDER_ID), targetFolderId,
                                             Msg.NOT_AN_ENTITY.format(Ent.Singular(Ent.DRIVE_FOLDER))],
                                            '\n'))
        if not targetFolder['ownedByMe']:
          Cmd.SetLocation(targetFolderIdLocation)
          usageErrorExit(formatKeyValueList(Ind.Spaces(),
                                            [Ent.Singular(Ent.USER), targetUser,
                                             Ent.Singular(Ent.DRIVE_FOLDER_ID), targetFolderId,
                                             Msg.NOT_OWNED_BY.format(targetUser)],
                                            '\n'))
        targetFolderId = targetFolder['id']
        targetFolderName = targetFolder['name']
      elif targetFolderName:
        result = callGAPIpages(targetDrive.files(), 'list', 'files',
                               throwReasons=GAPI.DRIVE_USER_THROW_REASONS,
                               retryReasons=[GAPI.UNKNOWN_ERROR],
                               q=MY_NON_TRASHED_FOLDER_NAME.format(escapeDriveFileName(targetFolderName)),
                               fields='nextPageToken,files(id)')
        if not result:
          Cmd.SetLocation(targetFolderNameLocation)
          usageErrorExit(formatKeyValueList(Ind.Spaces(),
                                            [Ent.Singular(Ent.USER), targetUser,
                                             Ent.Singular(Ent.DRIVE_FOLDER), targetFolderName,
                                             Msg.DOES_NOT_EXIST],
                                            '\n'))
        targetFolderId = result[0]['id']
  except GAPI.fileNotFound:
    Cmd.SetLocation(targetFolderIdLocation)
    usageErrorExit(formatKeyValueList(Ind.Spaces(),
                                      [Ent.Singular(Ent.USER), targetUser,
                                       Ent.Singular(Ent.DRIVE_FOLDER_ID), targetFolderId,
                                       Msg.DOES_NOT_EXIST],
                                      '\n'))
  except (GAPI.serviceNotAvailable, GAPI.authError, GAPI.domainPolicy) as e:
    userDriveServiceNotEnabledWarning(targetUser, str(e))
    return
  targetWriterPermissionsBody = {'role': 'writer', 'type': 'user', 'emailAddress': targetUser}
  i, count, users = getEntityArgument(users)
  for user in users:
    i += 1
    origUser = user
    if buildTree:
      sourceUser, sourceDrive = buildGAPIServiceObject(API.DRIVE3, user, i, count)
      if not sourceDrive:
        continue
    else:
      sourceUser, sourceDrive, jcount = _validateUserGetFileIDs(user, i, count, fileIdEntity, entityType=Ent.DRIVE_FOLDER)
      if jcount == 0:
        continue
    sourceUserName, _ = splitEmailAddress(sourceUser)
    try:
      result = callGAPI(sourceDrive.about(), 'get',
                        throwReasons=GAPI.DRIVE_USER_THROW_REASONS,
                        fields='storageQuota,user(permissionId)')
      sourceDriveSize = int(result['storageQuota']['usageInDrive'])
      sourcePermissionId = result['user']['permissionId']
      sourceRootId = callGAPI(sourceDrive.files(), 'get',
                              throwReasons=GAPI.DRIVE_USER_THROW_REASONS,
                              fileId=ROOT, fields='id')['id']
      if (targetDriveFree is not None) and (targetDriveFree < sourceDriveSize):
        printWarningMessage(TARGET_DRIVE_SPACE_ERROR_RC,
                            (f'{Msg.NO_TRANSFER_LACK_OF_DISK_SPACE} '
                             f'{formatKeyValueList("", ["Source drive size", formatFileSize(sourceDriveSize), "Target drive free", formatFileSize(targetDriveFree)], "")}'))
        continue
      printKeyValueList(['Source drive size', formatFileSize(sourceDriveSize),
                         'Target drive free', formatFileSize(targetDriveFree) if targetDriveFree is not None else 'UNLIMITED'])
      if targetDriveFree is not None:
        targetDriveFree = targetDriveFree-sourceDriveSize # prep targetDriveFree for next user
      if not csvPF:
        targetIds[TARGET_PARENT_ID] = _buildTargetUserFolder()
        if targetIds[TARGET_PARENT_ID] is None:
          return
      Ind.Increment()
      if skipFileIdEntity['query'] or skipFileIdEntity[ROOT]:
        _validateUserGetFileIDs(origUser, i, count, skipFileIdEntity, drive=sourceDrive)
      if buildTree:
        topSourceId = sourceRootId
        parentIdMap = {sourceRootId: targetIds[TARGET_PARENT_ID]}
        printGettingAllEntityItemsForWhom(Ent.DRIVE_FILE_OR_FOLDER, Ent.TypeName(Ent.SOURCE_USER, user), i, count)
        feed = callGAPIpages(sourceDrive.files(), 'list', 'files',
                             pageMessage=getPageMessageForWhom(),
                             throwReasons=GAPI.DRIVE_USER_THROW_REASONS,
                             retryReasons=[GAPI.UNKNOWN_ERROR],
                             orderBy=OBY.orderBy, q=NON_TRASHED,
                             fields='nextPageToken,files(id,name,parents,mimeType,ownedByMe,owners(emailAddress,permissionId),permissions(id,role),shortcutDetails)',
                             pageSize=GC.Values[GC.DRIVE_MAX_RESULTS])
        fileTree = buildFileTree(feed, sourceDrive)
        del feed
        filesTransferred = set()
        _transferDriveFilesFromTree(fileTree[sourceRootId], i, count)
        if fileTree[ORPHANS]['children']:
          if not csvPF:
            _buildTargetUserOrphansFolder()
          _transferDriveFilesFromTree(fileTree[ORPHANS], i, count)
        if not csvPF:
          Act.Set(Act.RETAIN)
          filesTransferred = set()
          _manageRoleRetentionDriveFilesFromTree(fileTree[sourceRootId], i, count)
          if fileTree[ORPHANS]['children']:
            _manageRoleRetentionDriveFilesFromTree(fileTree[ORPHANS], i, count)
      else:
        j = 0
        for fileId in fileIdEntity['list']:
          j += 1
          fileTree = {}
          parentIdMap = {sourceRootId: targetIds[TARGET_PARENT_ID]}
          Act.Set(Act.TRANSFER_OWNERSHIP)
          try:
            fileEntry = callGAPI(sourceDrive.files(), 'get',
                                 throwReasons=GAPI.DRIVE_GET_THROW_REASONS,
                                 fileId=fileId,
                                 fields='id,name,parents,mimeType,ownedByMe,trashed,owners(emailAddress,permissionId),permissions(id,role),shortcutDetails')
            entityType = _getEntityMimeType(fileEntry)
            if fileId in skipFileIdEntity['list']:
              entityActionNotPerformedWarning([Ent.USER, sourceUser, entityType, f'{fileEntry["name"]} ({fileId})'],
                                              Msg.IN_SKIPIDS, j, jcount)
              continue
            entityPerformActionItemValue([Ent.USER, sourceUser], entityType, f'{fileEntry["name"]} ({fileId})', j, jcount)
            if not mergeWithTarget:
              topSourceId = None
              for parentId in fileEntry.get('parents', []):
                parentIdMap[parentId] = targetIds[TARGET_PARENT_ID]
            else:
              topSourceId = fileId
              parentIdMap[fileId] = targetIds[TARGET_PARENT_ID]
            _identifyDriveFileAndChildren(fileEntry, i, count)
            filesTransferred = set()
            _transferDriveFileAndChildren(fileTree[fileId], i, count, j, jcount, True)
            if not csvPF:
              Act.Set(Act.RETAIN)
              filesTransferred = set()
              _manageRoleRetentionDriveFileAndChildren(fileTree[fileId], i, count, j, jcount, True)
          except GAPI.fileNotFound:
            entityActionFailedWarning([Ent.USER, sourceUser, Ent.DRIVE_FILE_OR_FOLDER, fileId], Msg.NOT_FOUND, j, jcount)
          except (GAPI.serviceNotAvailable, GAPI.authError, GAPI.domainPolicy) as e:
            userDriveServiceNotEnabledWarning(sourceUser, str(e), i, count)
            break
      Ind.Decrement()
    except (GAPI.serviceNotAvailable, GAPI.authError, GAPI.domainPolicy) as e:
      userDriveServiceNotEnabledWarning(sourceUser, str(e), i, count)
  if csvPF:
    csvPF.writeCSVfile('Files to Transfer')

def validateUserGetPermissionId(user, i=0, count=0, drive=None):
  if drive is None:
    _, drive = buildGAPIServiceObject(API.DRIVE3, user, i, count)
  if drive:
    try:
      result = callGAPI(drive.about(), 'get',
                        throwReasons=GAPI.DRIVE_USER_THROW_REASONS,
                        fields='user(permissionId)')
      return (drive, result['user']['permissionId'])
    except (GAPI.serviceNotAvailable, GAPI.authError, GAPI.domainPolicy) as e:
      userDriveServiceNotEnabledWarning(user, str(e), i, count)
  return (None, None)

def getPermissionIdForEmail(user, i, count, email):
  currentSvcAcctAPI = GM.Globals[GM.CURRENT_SVCACCT_API]
  currentSvcAcctAPIScopes = GM.Globals[GM.CURRENT_SVCACCT_API_SCOPES]
  _, drive = buildGAPIServiceObject(API.DRIVE2, user, i, count)
  GM.Globals[GM.CURRENT_SVCACCT_API] = currentSvcAcctAPI
  GM.Globals[GM.CURRENT_SVCACCT_API_SCOPES] = currentSvcAcctAPIScopes
  if drive:
    try:
      return callGAPI(drive.permissions(), 'getIdForEmail',
                      throwReasons=GAPI.DRIVE_USER_THROW_REASONS,
                      email=email, fields='id')['id']
    except (GAPI.serviceNotAvailable, GAPI.authError, GAPI.domainPolicy):
      entityActionNotPerformedWarning([Ent.USER, user], Msg.UNABLE_TO_GET_PERMISSION_ID.format(email), i, count)
      systemErrorExit(GM.Globals[GM.SYSEXITRC], None)
  return None

# gam <UserTypeEntity> transfer ownership <DriveFileEntity> <UserItem>
#	[<DriveFileParentAttribute>] [includetrashed] [norecursion [<Boolean>]]
#	(orderby <DriveFileOrderByFieldName> [ascending|descending])*
#	[preview] [filepath] [pathdelimiter <Character>] [buildtree]
#	[todrive <ToDriveAttribute>*]
def transferOwnership(users):
  def _identifyFilesToTransfer(fileEntry):
    for childFileId in fileEntry['children']:
      if childFileId in filesTransferred:
        continue
      filesTransferred.add(childFileId)
      childEntry = fileTree.get(childFileId)
      if childEntry:
        childEntryInfo = childEntry['info']
        if includeTrashed or not childEntryInfo['trashed']:
          if childEntryInfo['ownedByMe']:
            filesToTransfer[childFileId] = {'name': childEntryInfo['name'], 'type': _getEntityMimeType(childEntryInfo)}
          if childEntryInfo['mimeType'] == MIMETYPE_GA_FOLDER:
            _identifyFilesToTransfer(childEntry)

  def _identifyChildrenToTransfer(fileEntry, user, i, count):
    q = WITH_PARENTS.format(fileEntry['id'])
    setGettingAllEntityItemsForWhom(Ent.DRIVE_FILE_OR_FOLDER, user, query=q)
    pageMessage = getPageMessageForWhom(clearLastGotMsgLen=False)
    try:
      children = callGAPIpages(drive.files(), 'list', 'files',
                               pageMessage=pageMessage, noFinalize=True,
                               throwReasons=GAPI.DRIVE_USER_THROW_REASONS,
                               retryReasons=[GAPI.UNKNOWN_ERROR],
                               orderBy=OBY.orderBy, q=q,
                               fields='nextPageToken,files(id,name,parents,mimeType,ownedByMe,trashed)',
                               pageSize=GC.Values[GC.DRIVE_MAX_RESULTS])
    except (GAPI.serviceNotAvailable, GAPI.authError, GAPI.domainPolicy) as e:
      userDriveServiceNotEnabledWarning(user, str(e), i, count)
      return
    for childEntryInfo in children:
      childFileId = childEntryInfo['id']
      if filepath:
        fileTree[childFileId] = {'info': childEntryInfo}
      if childFileId in filesTransferred:
        continue
      filesTransferred.add(childFileId)
      if includeTrashed or not childEntryInfo['trashed']:
        if childEntryInfo['ownedByMe']:
          filesToTransfer[childFileId] = {'name': childEntryInfo['name'], 'type': _getEntityMimeType(childEntryInfo)}
        if childEntryInfo['mimeType'] == MIMETYPE_GA_FOLDER:
          _identifyChildrenToTransfer(childEntryInfo, user, i, count)

  fileIdEntity = getDriveFileEntity()
  body = {}
  newOwner = getEmailAddress()
  OBY = OrderBy(DRIVEFILE_ORDERBY_CHOICE_MAP)
  changeParents = filepath = includeTrashed = noRecursion = False
  pathDelimiter = '/'
  csvPF = fileTree = None
  addParents = ''
  parentBody = {}
  parentParms = initDriveFileAttributes()
  buildTree = False
  while Cmd.ArgumentsRemaining():
    myarg = getArgument()
    if myarg == 'includetrashed':
      includeTrashed = True
    elif myarg == 'norecursion':
      noRecursion = getBoolean()
    elif myarg == 'orderby':
      OBY.GetChoice()
    elif myarg == 'filepath':
      filepath = True
    elif myarg == 'pathdelimiter':
      pathDelimiter = getCharacter()
    elif myarg == 'buildtree':
      buildTree = True
    elif myarg == 'preview':
      csvPF = CSVPrintFile(['OldOwner', 'NewOwner', 'type', 'id', 'name'])
    elif csvPF and myarg == 'todrive':
      csvPF.GetTodriveParameters()
    elif getDriveFileParentAttribute(myarg, parentParms):
      changeParents = True
    else:
      unknownArgumentExit()
  Act.Set(Act.TRANSFER_OWNERSHIP)
  targetDrive, permissionId = validateUserGetPermissionId(newOwner)
  if not permissionId:
    return
  if changeParents:
    if not _getDriveFileParentInfo(targetDrive, newOwner, 0, 0, parentBody, parentParms):
      return
    addParents = ','.join(parentBody['parents'])
  if csvPF:
    if filepath:
      csvPF.AddTitles('paths')
  else:
    filepath = False
  body = {'role': 'owner'}
  bodyAdd = {'role': 'writer', 'type': 'user', 'emailAddress': newOwner}
  i, count, users = getEntityArgument(users)
  for user in users:
    i += 1
    user, drive, jcount = _validateUserGetFileIDs(user, i, count, fileIdEntity, entityType=Ent.DRIVE_FILE_OR_FOLDER)
    if jcount == 0:
      continue
    if filepath:
      filePathInfo = initFilePathInfo(pathDelimiter)
    filesTransferred = set()
    if buildTree:
      printGettingAllEntityItemsForWhom(Ent.DRIVE_FILE_OR_FOLDER, user, i, count)
      try:
        feed = callGAPIpages(drive.files(), 'list', 'files',
                             pageMessage=getPageMessageForWhom(),
                             throwReasons=GAPI.DRIVE_USER_THROW_REASONS,
                             retryReasons=[GAPI.UNKNOWN_ERROR],
                             orderBy=OBY.orderBy,
                             fields='nextPageToken,files(id,name,parents,mimeType,ownedByMe,trashed)',
                             pageSize=GC.Values[GC.DRIVE_MAX_RESULTS])
        fileTree = buildFileTree(feed, drive)
        del feed
      except (GAPI.serviceNotAvailable, GAPI.authError, GAPI.domainPolicy) as e:
        userDriveServiceNotEnabledWarning(user, str(e), i, count)
        continue
    else:
      fileTree = {}
    Ind.Increment()
    j = 0
    for fileId in fileIdEntity['list']:
      j += 1
      kvList = [Ent.USER, user, Ent.DRIVE_FILE_OR_FOLDER, fileId]
      if buildTree:
        fileEntry = fileTree.get(fileId)
        if not fileEntry:
          entityActionFailedWarning(kvList, Msg.NOT_FOUND, j, jcount)
          continue
        fileEntryInfo = fileEntry['info']
      else:
        try:
          fileEntryInfo = callGAPI(drive.files(), 'get',
                                   throwReasons=GAPI.DRIVE_GET_THROW_REASONS,
                                   fileId=fileId, fields='id,name,parents,mimeType,ownedByMe,trashed,shortcutDetails')
        except GAPI.fileNotFound:
          entityActionFailedWarning(kvList, Msg.NOT_FOUND, j, jcount)
          continue
        except (GAPI.serviceNotAvailable, GAPI.authError, GAPI.domainPolicy) as e:
          userDriveServiceNotEnabledWarning(user, str(e), i, count)
          break
        if filepath:
          fileTree[fileId] = {'info': fileEntryInfo}
      entityType = _getEntityMimeType(fileEntryInfo)
      entityPerformActionItemValue([Ent.USER, user], entityType, f'{fileEntryInfo["name"]} ({fileId})', j, jcount)
      if fileId in filesTransferred:
        continue
      filesTransferred.add(fileId)
      filesToTransfer = {}
      if includeTrashed or not fileEntryInfo['trashed']:
        if fileEntryInfo['ownedByMe'] and fileEntryInfo['name'] != MY_DRIVE:
          filesToTransfer[fileId] = {'name': fileEntryInfo['name'], 'type': entityType}
          if changeParents:
            filesToTransfer[fileId]['addParents'] = addParents
            filesToTransfer[fileId]['removeParents'] = ','.join(fileEntryInfo.get('parents', []))
          if fileEntryInfo['mimeType'] == MIMETYPE_GA_SHORTCUT and entityType != Ent.DRIVE_SHORTCUT:
            filesToTransfer[fileId]['shortcutDetails'] = fileEntryInfo['shortcutDetails']
        if fileEntryInfo['mimeType'] == MIMETYPE_GA_FOLDER and not noRecursion:
          if buildTree:
            _identifyFilesToTransfer(fileEntry)
          else:
            _identifyChildrenToTransfer(fileEntryInfo, user, i, count)
      if csvPF:
        for xferFileId, fileInfo in filesToTransfer.items():
          row = {'OldOwner': user, 'NewOwner': newOwner, 'type': Ent.Singular(fileInfo['type']), 'id': xferFileId, 'name': fileInfo['name']}
          if filepath:
            addFilePathsToRow(drive, fileTree, fileTree[xferFileId]['info'], filePathInfo, csvPF, row)
          csvPF.WriteRow(row)
        continue
      Ind.Increment()
      kcount = len(filesToTransfer)
      entityPerformActionNumItemsModifier([Ent.USER, user], kcount, Ent.DRIVE_FILE_OR_FOLDER, f'{Act.MODIFIER_TO} {Ent.Singular(Ent.USER)}: {newOwner}', i, count)
      Ind.Increment()
      k = 0
      for xferFileId, fileInfo in filesToTransfer.items():
        k += 1
        entityType = fileInfo['type']
        fileDesc = f'{fileInfo["name"]} ({xferFileId})'
        kvList = [Ent.USER, user, entityType, fileDesc]
        try:
          if entityType not in {Ent.DRIVE_SHORTCUT, Ent.DRIVE_FILE_SHORTCUT, Ent.DRIVE_FOLDER_SHORTCUT}:
            if changeParents:
              removeParents = fileInfo.get('removeParents', '')
              if removeParents:
                callGAPI(drive.files(), 'update',
                         throwReasons=GAPI.DRIVE_ACCESS_THROW_REASONS,
                         fileId=xferFileId, removeParents=removeParents, fields='', supportsAllDrives=True)
                action = Act.Get()
                Act.Set(Act.REMOVE)
                entityModifierNewValueItemValueListActionPerformed(kvList, Act.MODIFIER_FROM, None, [Ent.DRIVE_FOLDER, fileInfo['removeParents']], k, kcount)
                Act.Set(action)
            callGAPI(drive.permissions(), 'update',
                     throwReasons=GAPI.DRIVE_ACCESS_THROW_REASONS+[GAPI.PERMISSION_NOT_FOUND],
                     fileId=xferFileId, permissionId=permissionId, transferOwnership=True, body=body, fields='')
            entityModifierNewValueItemValueListActionPerformed(kvList, Act.MODIFIER_TO, None, [Ent.USER, newOwner], k, kcount)
          else:
            if changeParents and entityType != Ent.DRIVE_SHORTCUT:
              callGAPI(drive.files(), 'delete',
                       throwReasons=GAPI.DRIVE_ACCESS_THROW_REASONS,
                       fileId=xferFileId, supportsAllDrives=True)
              action = Act.Get()
              Act.Set(Act.DELETE_SHORTCUT)
              entityActionPerformed(kvList, k, kcount)
              Act.Set(action)
            else:
              entityModifierNewValueItemValueListActionPerformed(kvList, Act.MODIFIER_TO, None, [Ent.USER, newOwner], k, kcount)
        except GAPI.permissionNotFound:
          # this might happen if target user isn't explicitly in ACL (i.e. shared with anyone)
          try:
            callGAPI(drive.permissions(), 'create',
                     throwReasons=GAPI.DRIVE_ACCESS_THROW_REASONS+[GAPI.INVALID_SHARING_REQUEST],
                     fileId=xferFileId, sendNotificationEmail=False, body=bodyAdd, fields='')
            callGAPI(drive.permissions(), 'update',
                     throwReasons=GAPI.DRIVE_ACCESS_THROW_REASONS+[GAPI.PERMISSION_NOT_FOUND],
                     fileId=xferFileId, permissionId=permissionId, transferOwnership=True, body=body, fields='')
            entityModifierNewValueItemValueListActionPerformed(kvList, Act.MODIFIER_TO, None, [Ent.USER, newOwner], k, kcount)
          except GAPI.invalidSharingRequest as e:
            entityActionFailedWarning(kvList, Ent.TypeNameMessage(Ent.PERMISSION_ID, permissionId, str(e)), k, kcount)
            continue
          except GAPI.permissionNotFound:
            entityDoesNotHaveItemWarning(kvList+[Ent.PERMISSION_ID, permissionId], k, kcount)
            continue
          except GAPI.fileNotFound:
            entityActionFailedWarning(kvList, Msg.DOES_NOT_EXIST, k, kcount)
            continue
          except (GAPI.forbidden, GAPI.insufficientFilePermissions) as e:
            entityActionFailedWarning(kvList, str(e), k, kcount)
            continue
          except (GAPI.serviceNotAvailable, GAPI.authError, GAPI.domainPolicy) as e:
            userDriveServiceNotEnabledWarning(user, str(e), i, count)
            continue
        except GAPI.fileNotFound:
          entityActionFailedWarning(kvList, Msg.DOES_NOT_EXIST, k, kcount)
          continue
        except (GAPI.forbidden, GAPI.insufficientFilePermissions) as e:
          entityActionFailedWarning(kvList, str(e), k, kcount)
          continue
        except (GAPI.serviceNotAvailable, GAPI.authError, GAPI.domainPolicy) as e:
          userDriveServiceNotEnabledWarning(user, str(e), i, count)
          break
        kvList = [Ent.USER, newOwner, entityType, fileDesc]
        try:
          if entityType not in {Ent.DRIVE_SHORTCUT, Ent.DRIVE_FILE_SHORTCUT, Ent.DRIVE_FOLDER_SHORTCUT}:
            if changeParents and 'addParents' in fileInfo:
              if entityType != Ent.DRIVE_FILE_SHORTCUT:
                callGAPI(targetDrive.files(), 'update',
                         throwReasons=GAPI.DRIVE_ACCESS_THROW_REASONS+[GAPI.CANNOT_ADD_PARENT, GAPI.INSUFFICIENT_PARENT_PERMISSIONS],
                         fileId=xferFileId, addParents=fileInfo['addParents'], fields='', supportsAllDrives=True)
                action = Act.Get()
                Act.Set(Act.ADD)
                entityModifierNewValueItemValueListActionPerformed(kvList, Act.MODIFIER_TO, None, [Ent.DRIVE_FOLDER, fileInfo['addParents']], k, kcount)
                Act.Set(action)
          else:
            if changeParents and 'addParents' in fileInfo and entityType != Ent.DRIVE_SHORTCUT:
              body = {'name': fileInfo['name'], 'mimeType': MIMETYPE_GA_SHORTCUT,
                      'parents': [fileInfo['addParents']], 'shortcutDetails': {'targetId': fileInfo['shortcutDetails']['targetId']}}
              callGAPI(targetDrive.files(), 'create',
                       throwReasons=GAPI.DRIVE_USER_THROW_REASONS+[GAPI.FORBIDDEN, GAPI.INSUFFICIENT_PERMISSIONS, GAPI.INSUFFICIENT_PARENT_PERMISSIONS,
                                                                   GAPI.INVALID, GAPI.BAD_REQUEST, GAPI.FILE_NOT_FOUND, GAPI.UNKNOWN_ERROR,
                                                                   GAPI.STORAGE_QUOTA_EXCEEDED, GAPI.TEAMDRIVES_SHARING_RESTRICTION_NOT_ALLOWED,
                                                                   GAPI.TEAMDRIVE_FILE_LIMIT_EXCEEDED, GAPI.TEAMDRIVE_HIERARCHY_TOO_DEEP, GAPI.SHORTCUT_TARGET_INVALID,
                                                                   GAPI.TARGET_USER_ROLE_LIMITED_BY_LICENSE_RESTRICTION],
                                body=body, fields='id', supportsAllDrives=True)
              Act.Set(Act.CREATE_SHORTCUT)
              entityModifierNewValueItemValueListActionPerformed(kvList, Act.MODIFIER_IN, None, [Ent.DRIVE_FOLDER, fileInfo['addParents']], k, kcount)
              Act.Set(action)
        except GAPI.fileNotFound:
          entityActionFailedWarning(kvList, Msg.DOES_NOT_EXIST, k, kcount)
        except (GAPI.forbidden, GAPI.cannotAddParent, GAPI.insufficientPermissions, GAPI.insufficientParentPermissions,
                GAPI.invalid, GAPI.badRequest, GAPI.unknownError) as e:
          entityActionFailedWarning(kvList, str(e), k, kcount)
        except (GAPI.serviceNotAvailable, GAPI.authError, GAPI.domainPolicy) as e:
          userDriveServiceNotEnabledWarning(newOwner, str(e), 0, 0)
      Ind.Decrement()
      Ind.Decrement()
    Ind.Decrement()
  if csvPF:
    csvPF.writeCSVfile('Files to Transfer Ownership')

# gam <UserTypeEntity> claim ownership <DriveFileEntity>
#	[<DriveFileParentAttribute>] [includetrashed]
#	[skipids <DriveFileEntity>] [onlyUsers|skipusers <UserTypeEntity>] [subdomains <DomainNameEntity>]
#	[restricted [<Boolean>]] [writerscanshare|writerscantshare [<Boolean>]]
#	[keepuser | (retainrole reader|commenter|writer|editor|none)] [noretentionmessages]
#	(orderby <DriveFileOrderByFieldName> [ascending|descending])*
#	[preview] [filepath] [pathdelimiter <Character>] [buildtree]
#	[todrive <ToDriveAttribute>*]
def claimOwnership(users):
  def _identifyFilesToClaim(fileEntry):
    for childFileId in fileEntry['children']:
      if childFileId in filesTransferred or childFileId in skipFileIdEntity['list']:
        continue
      filesTransferred.add(childFileId)
      childEntry = fileTree.get(childFileId)
      if childEntry:
        childEntryInfo = childEntry['info']
        if includeTrashed or not childEntryInfo['trashed']:
          owner = childEntryInfo['owners'][0]['emailAddress']
          if (not childEntryInfo['ownedByMe']) and ((not checkOwner) or (checkOnly and owner in onlyOwners) or (checkSkip and owner not in skipOwners)):
            oldOwnerPermissionIds[owner] = childEntryInfo['owners'][0]['permissionId']
            filesToClaim.setdefault(owner, {})
            if childFileId not in filesToClaim[owner]:
              filesToClaim[owner][childFileId] = {'name': childEntryInfo['name'], 'type': _getEntityMimeType(childEntryInfo)}
          if childEntryInfo['mimeType'] == MIMETYPE_GA_FOLDER:
            _identifyFilesToClaim(childEntry)

  def _identifyChildrenToClaim(fileEntry, user, i, count):
    q = WITH_PARENTS.format(fileEntry['id'])
    setGettingAllEntityItemsForWhom(Ent.DRIVE_FILE_OR_FOLDER, user, query=q)
    pageMessage = getPageMessageForWhom(clearLastGotMsgLen=False)
    try:
      children = callGAPIpages(drive.files(), 'list', 'files',
                               pageMessage=pageMessage, noFinalize=True,
                               throwReasons=GAPI.DRIVE_USER_THROW_REASONS,
                               retryReasons=[GAPI.UNKNOWN_ERROR],
                               orderBy=OBY.orderBy, q=q,
                               fields='nextPageToken,files(id,name,parents,mimeType,ownedByMe,trashed,owners(emailAddress,permissionId))',
                               pageSize=GC.Values[GC.DRIVE_MAX_RESULTS])
    except (GAPI.serviceNotAvailable, GAPI.authError, GAPI.domainPolicy) as e:
      userDriveServiceNotEnabledWarning(user, str(e), i, count)
      return
    for childEntryInfo in children:
      childFileId = childEntryInfo['id']
      if childFileId in filesTransferred or childFileId in skipFileIdEntity['list']:
        continue
      filesTransferred.add(childFileId)
      if includeTrashed or not childEntryInfo['trashed']:
        if filepath:
          fileTree[childFileId] = {'info': childEntryInfo}
        owner = childEntryInfo['owners'][0]['emailAddress']
        if (not childEntryInfo['ownedByMe']) and ((not checkOwner) or (checkOnly and owner in onlyOwners) or (checkSkip and owner not in skipOwners)):
          oldOwnerPermissionIds[owner] = childEntryInfo['owners'][0]['permissionId']
          filesToClaim.setdefault(owner, {})
          if childFileId not in filesToClaim[owner]:
            filesToClaim[owner][childFileId] = {'name': childEntryInfo['name'], 'type': _getEntityMimeType(childEntryInfo)}
        if childEntryInfo['mimeType'] == MIMETYPE_GA_FOLDER:
          _identifyChildrenToClaim(childEntryInfo, user, i, count)

  def _processRetainedRole(user, i, count, oldOwner, entityType, ofileId, fileDesc, l, lcount):
    oldOwnerPermissionId = oldOwnerPermissionIds[oldOwner]
    Act.Set(Act.RETAIN)
    try:
      if sourceRetainRoleBody['role'] != 'none':
        if sourceRetainRoleBody['role'] != 'writer':
          callGAPI(sourceDrive.permissions(), 'update',
                   throwReasons=GAPI.DRIVE_ACCESS_THROW_REASONS+[GAPI.PERMISSION_NOT_FOUND, GAPI.BAD_REQUEST],
                   fileId=ofileId, permissionId=oldOwnerPermissionId, body=sourceRetainRoleBody, fields='')
      else:
        callGAPI(sourceDrive.permissions(), 'delete',
                 throwReasons=GAPI.DRIVE_ACCESS_THROW_REASONS+GAPI.DRIVE3_DELETE_ACL_THROW_REASONS,
                 fileId=ofileId, permissionId=oldOwnerPermissionId)
      if showRetentionMessages:
        entityActionPerformed([Ent.USER, oldOwner, entityType, fileDesc, Ent.ROLE, sourceRetainRoleBody['role']], l, lcount)
    except (GAPI.fileNotFound, GAPI.forbidden, GAPI.internalError, GAPI.insufficientFilePermissions, GAPI.unknownError, GAPI.invalid,
            GAPI.badRequest, GAPI.notFound, GAPI.cannotRemoveOwner,
            GAPI.cannotModifyInheritedTeamDrivePermission, GAPI.cannotModifyInheritedPermission,
            GAPI.insufficientAdministratorPrivileges, GAPI.sharingRateLimitExceeded, GAPI.cannotDeletePermission,
            GAPI.fileNeverWritable) as e:
      entityActionFailedWarning([Ent.USER, oldOwner, entityType, fileDesc], str(e), l, lcount)
    except GAPI.permissionNotFound:
      entityDoesNotHaveItemWarning([Ent.USER, oldOwner, entityType, fileDesc, Ent.PERMISSION_ID, oldOwnerPermissionId], l, lcount)
    except (GAPI.serviceNotAvailable, GAPI.authError, GAPI.domainPolicy) as e:
      userDriveServiceNotEnabledWarning(user, str(e), i, count)
    Act.Set(Act.CLAIM_OWNERSHIP)

  fileIdEntity = getDriveFileEntity()
  skipFileIdEntity = initDriveFileEntity()
  OBY = OrderBy(DRIVEFILE_ORDERBY_CHOICE_MAP)
  body = {}
  checkOnly = checkSkip = False
  onlyOwners = set()
  skipOwners = set()
  subdomains = []
  filepath = includeTrashed = False
  pathDelimiter = '/'
  addParents = ''
  parentBody = {}
  parentParms = initDriveFileAttributes()
  sourceRetainRoleBody = {'role': 'writer'}
  showRetentionMessages = True
  oldOwnerPermissionIds = {}
  csvPF = fileTree = None
  buildTree = changeParents = False
  bodyShare = {}
  while Cmd.ArgumentsRemaining():
    myarg = getArgument()
    if myarg == 'keepuser':
      sourceRetainRoleBody['role'] = 'writer'
    elif myarg == 'retainrole':
      sourceRetainRoleBody['role'] = getChoice(TRANSFER_DRIVEFILE_ACL_ROLES_MAP, mapChoice=True)
    elif myarg == 'noretentionmessages':
      showRetentionMessages = False
    elif myarg == 'skipids':
      skipFileIdEntity = getDriveFileEntity()
    elif myarg == 'onlyusers':
      _, userList = getEntityToModify(defaultEntityType=Cmd.ENTITY_USERS)
      checkOnly = True
      onlyOwners = {normalizeEmailAddressOrUID(user, noUid=True) for user in userList}
    elif myarg == 'skipusers':
      _, userList = getEntityToModify(defaultEntityType=Cmd.ENTITY_USERS)
      checkSkip = len(userList) > 0
      skipOwners = {normalizeEmailAddressOrUID(user, noUid=True) for user in userList}
    elif myarg == 'subdomains':
      subdomains = getEntityList(Cmd.OB_DOMAIN_NAME_ENTITY)
    elif myarg == 'includetrashed':
      includeTrashed = True
    elif myarg == 'orderby':
      OBY.GetChoice()
    elif myarg == 'restricted':
      bodyShare['copyRequiresWriterPermission'] = getBoolean()
    elif myarg == 'writerscanshare':
      bodyShare['writersCanShare'] = getBoolean()
    elif myarg == 'writerscantshare':
      bodyShare['writersCanShare'] = not getBoolean()
    elif myarg == 'filepath':
      filepath = True
    elif myarg == 'pathdelimiter':
      pathDelimiter = getCharacter()
    elif myarg == 'buildtree':
      buildTree = True
    elif myarg == 'preview':
      csvPF = CSVPrintFile(['OldOwner', 'NewOwner', 'type', 'id', 'name'])
    elif csvPF and myarg == 'todrive':
      csvPF.GetTodriveParameters()
    elif getDriveFileParentAttribute(myarg, parentParms):
      changeParents = True
    else:
      unknownArgumentExit()
  if checkOnly and checkSkip:
    usageErrorExit(Msg.ARE_MUTUALLY_EXCLUSIVE.format('onlyusers', 'skipusers'))
  checkOwner = checkOnly or checkSkip
  Act.Set(Act.CLAIM_OWNERSHIP)
  if csvPF:
    if filepath:
      csvPF.AddTitles('paths')
  else:
    filepath = False
  body = {'role': 'owner'}
  i, count, users = getEntityArgument(users)
  for user in users:
    i += 1
    origUser = user
    user, drive, jcount = _validateUserGetFileIDs(user, i, count, fileIdEntity)
    if not drive:
      continue
    _, permissionId = validateUserGetPermissionId(user, i, count, drive)
    if not permissionId:
      continue
    if changeParents:
      if not _getDriveFileParentInfo(drive, user, i, count, parentBody, parentParms):
        return
      addParents = ','.join(parentBody['parents'])
    entityPerformActionNumItems([Ent.USER, user], jcount, Ent.DRIVE_FILE_OR_FOLDER, i, count)
    if jcount == 0:
      continue
    if filepath:
      filePathInfo = initFilePathInfo(pathDelimiter)
    filesTransferred = set()
    bodyAdd = {'role': 'writer', 'type': 'user', 'emailAddress': user}
    if skipFileIdEntity['query'] or skipFileIdEntity[ROOT]:
      _validateUserGetFileIDs(origUser, i, count, skipFileIdEntity, drive=drive)
    if buildTree:
      printGettingAllEntityItemsForWhom(Ent.DRIVE_FILE_OR_FOLDER, user, i, count)
      try:
        feed = callGAPIpages(drive.files(), 'list', 'files',
                             pageMessage=getPageMessageForWhom(),
                             throwReasons=GAPI.DRIVE_USER_THROW_REASONS,
                             retryReasons=[GAPI.UNKNOWN_ERROR],
                             orderBy=OBY.orderBy,
                             fields='nextPageToken,files(id,name,parents,mimeType,ownedByMe,trashed,owners(emailAddress,permissionId))',
                             pageSize=GC.Values[GC.DRIVE_MAX_RESULTS])
        fileTree = buildFileTree(feed, drive)
        del feed
      except (GAPI.serviceNotAvailable, GAPI.authError, GAPI.domainPolicy) as e:
        userDriveServiceNotEnabledWarning(user, str(e), i, count)
        continue
    else:
      fileTree = {}
    Ind.Increment()
    j = 0
    for fileId in fileIdEntity['list']:
      j += 1
      filesToClaim = {}
      kvList = [Ent.USER, user, Ent.DRIVE_FILE_OR_FOLDER, fileId]
      if buildTree:
        fileEntry = fileTree.get(fileId)
        if not fileEntry:
          entityActionFailedWarning(kvList, Msg.NOT_FOUND, j, jcount)
          continue
        fileEntryInfo = fileEntry['info']
      else:
        try:
          fileEntryInfo = callGAPI(drive.files(), 'get',
                                   throwReasons=GAPI.DRIVE_GET_THROW_REASONS,
                                   fileId=fileId,
                                   fields='id,name,parents,mimeType,ownedByMe,trashed,shortcutDetails,owners(emailAddress,permissionId)')
        except GAPI.fileNotFound:
          entityActionFailedWarning(kvList, Msg.NOT_FOUND, j, jcount)
          continue
        except (GAPI.serviceNotAvailable, GAPI.authError, GAPI.domainPolicy) as e:
          userDriveServiceNotEnabledWarning(user, str(e), i, count)
          break
        if filepath:
          fileTree[fileId] = {'info': fileEntryInfo}
      entityType = _getEntityMimeType(fileEntryInfo)
      if fileId in skipFileIdEntity['list']:
        entityActionNotPerformedWarning([Ent.USER, user, entityType, f'{fileEntryInfo["name"]} ({fileId})'],
                                        Msg.IN_SKIPIDS, j, jcount)
        continue
      entityPerformActionItemValue([Ent.USER, user], entityType, f'{fileEntryInfo["name"]} ({fileId})', j, jcount)
      if fileId in filesTransferred:
        continue
      filesTransferred.add(fileId)
      if fileId not in skipFileIdEntity['list'] and (includeTrashed or not fileEntryInfo['trashed']):
        owner = fileEntryInfo['owners'][0]['emailAddress']
        if (not fileEntryInfo['ownedByMe']) and ((not checkOwner) or (checkOnly and owner in onlyOwners) or (checkSkip and owner not in skipOwners)):
          oldOwnerPermissionIds[owner] = fileEntryInfo['owners'][0]['permissionId']
          filesToClaim.setdefault(owner, {})
          if fileId not in filesToClaim[owner]:
            filesToClaim[owner][fileId] = {'name': fileEntryInfo['name'], 'type': entityType}
            if changeParents:
              filesToClaim[owner][fileId]['addParents'] = addParents
              filesToClaim[owner][fileId]['removeParents'] = ','.join(fileEntryInfo.get('parents', []))
            if fileEntryInfo['mimeType'] == MIMETYPE_GA_SHORTCUT and entityType != Ent.DRIVE_SHORTCUT:
              filesToClaim[owner][fileId]['shortcutDetails'] = fileEntryInfo['shortcutDetails']
        if fileEntryInfo['mimeType'] == MIMETYPE_GA_FOLDER:
          if buildTree:
            _identifyFilesToClaim(fileEntry)
          else:
            _identifyChildrenToClaim(fileEntryInfo, user, i, count)
      if csvPF:
        for oldOwner, oldOwnerFilesToClaim in filesToClaim.items():
          for claimFileId, fileInfo in oldOwnerFilesToClaim.items():
            row = {'NewOwner': user, 'OldOwner': oldOwner, 'type': Ent.Singular(fileInfo['type']), 'id': claimFileId, 'name': fileInfo['name']}
            if filepath:
              addFilePathsToRow(drive, fileTree, fileTree[claimFileId]['info'], filePathInfo, csvPF, row)
            csvPF.WriteRow(row)
        continue
      Ind.Increment()
      kcount = len(filesToClaim)
      entityPerformActionNumItems([Ent.USER, user], kcount, Ent.USER, i, count)
      Ind.Increment()
      k = 0
      for oldOwner, oldOwnerFilesToClaim in filesToClaim.items():
        k += 1
        _, userDomain = splitEmailAddress(oldOwner)
        lcount = len(oldOwnerFilesToClaim)
        if userDomain == GC.Values[GC.DOMAIN] or userDomain in subdomains:
          _, sourceDrive = buildGAPIServiceObject(API.DRIVE3, oldOwner, k, kcount)
          if not sourceDrive:
            continue
          entityPerformActionNumItemsModifier([Ent.USER, user], lcount, Ent.DRIVE_FILE_OR_FOLDER,
                                              f'{Act.MODIFIER_FROM} {Ent.Singular(Ent.USER)}: {oldOwner}', k, kcount)
          Ind.Increment()
          l = 0
          for xferFileId, fileInfo in oldOwnerFilesToClaim.items():
            l += 1
            entityType = fileInfo['type']
            fileDesc = f'{fileInfo["name"]} ({xferFileId})'
            kvList = [Ent.USER, oldOwner, entityType, fileDesc]
            try:
              if entityType not in {Ent.DRIVE_SHORTCUT, Ent.DRIVE_FILE_SHORTCUT, Ent.DRIVE_FOLDER_SHORTCUT}:
                if bodyShare:
                  callGAPI(sourceDrive.files(), 'update',
                           fileId=xferFileId, body=bodyShare, fields='')
                if changeParents:
                  removeParents = fileInfo.get('removeParents', '')
                  if removeParents:
                    callGAPI(sourceDrive.files(), 'update',
                             throwReasons=GAPI.DRIVE_ACCESS_THROW_REASONS,
                             fileId=xferFileId, removeParents=removeParents, fields='', supportsAllDrives=True)
                    action = Act.Get()
                    Act.Set(Act.REMOVE)
                    entityModifierNewValueItemValueListActionPerformed(kvList, Act.MODIFIER_FROM, None,
                                                                       [Ent.DRIVE_FOLDER, removeParents], l, lcount)
                    Act.Set(action)
                callGAPI(sourceDrive.permissions(), 'update',
                         throwReasons=GAPI.DRIVE_ACCESS_THROW_REASONS+[GAPI.PERMISSION_NOT_FOUND],
                         fileId=xferFileId, permissionId=permissionId, transferOwnership=True, body=body, fields='')
                kvList = [Ent.USER, user, entityType, fileDesc]
                entityModifierNewValueItemValueListActionPerformed(kvList, Act.MODIFIER_FROM, None, [Ent.USER, oldOwner], l, lcount)
                _processRetainedRole(user, i, count, oldOwner, entityType, xferFileId, fileDesc, l, lcount)
              else:
                if changeParents and entityType != Ent.DRIVE_SHORTCUT:
                  callGAPI(sourceDrive.files(), 'delete',
                           throwReasons=GAPI.DRIVE_ACCESS_THROW_REASONS,
                           fileId=xferFileId, supportsAllDrives=True)
                  action = Act.Get()
                  Act.Set(Act.DELETE_SHORTCUT)
                  entityActionPerformed(kvList, l, lcount)
                  Act.Set(action)
                else:
                  kvList = [Ent.USER, user, entityType, fileDesc]
                  entityModifierNewValueItemValueListActionPerformed(kvList, Act.MODIFIER_FROM, None, [Ent.USER, oldOwner], l, lcount)
            except GAPI.permissionNotFound:
              # if claimer not in ACL (file might be visible for all with link)
              try:
                callGAPI(sourceDrive.permissions(), 'create',
                         throwReasons=GAPI.DRIVE_ACCESS_THROW_REASONS+[GAPI.INVALID_SHARING_REQUEST],
                         fileId=xferFileId, sendNotificationEmail=False, body=bodyAdd, fields='')
                callGAPI(sourceDrive.permissions(), 'update',
                         throwReasons=GAPI.DRIVE_ACCESS_THROW_REASONS+[GAPI.PERMISSION_NOT_FOUND],
                         fileId=xferFileId, permissionId=permissionId, transferOwnership=True, body=body, fields='')
                entityModifierNewValueItemValueListActionPerformed(kvList, Act.MODIFIER_FROM, None, [Ent.USER, oldOwner], l, lcount)
                _processRetainedRole(user, i, count, oldOwner, entityType, xferFileId, fileDesc, l, lcount)
              except GAPI.invalidSharingRequest as e:
                entityActionFailedWarning(kvList, Ent.TypeNameMessage(Ent.PERMISSION_ID, permissionId, str(e)), l, lcount)
                continue
              except GAPI.permissionNotFound:
                entityDoesNotHaveItemWarning(kvList+[Ent.PERMISSION_ID, permissionId], l, lcount)
                continue
              except GAPI.fileNotFound:
                entityActionFailedWarning(kvList, Msg.DOES_NOT_EXIST, l, lcount)
                continue
              except (GAPI.forbidden, GAPI.insufficientFilePermissions) as e:
                entityActionFailedWarning(kvList, str(e), l, lcount)
                continue
              except (GAPI.serviceNotAvailable, GAPI.authError, GAPI.domainPolicy) as e:
                userDriveServiceNotEnabledWarning(user, str(e), i, count)
                continue
            except GAPI.fileNotFound:
              entityActionFailedWarning(kvList, Msg.DOES_NOT_EXIST, l, lcount)
              continue
            except (GAPI.forbidden, GAPI.insufficientFilePermissions) as e:
              entityActionFailedWarning(kvList, str(e), l, lcount)
              continue
            except (GAPI.serviceNotAvailable, GAPI.authError, GAPI.domainPolicy) as e:
              userDriveServiceNotEnabledWarning(user, str(e), i, count)
              break
            kvList = [Ent.USER, user, entityType, fileDesc]
            try:
              if entityType not in {Ent.DRIVE_SHORTCUT, Ent.DRIVE_FILE_SHORTCUT, Ent.DRIVE_FOLDER_SHORTCUT}:
                if changeParents and 'addParents' in fileInfo:
                  callGAPI(drive.files(), 'update',
                           throwReasons=GAPI.DRIVE_ACCESS_THROW_REASONS+[GAPI.CANNOT_ADD_PARENT, GAPI.INSUFFICIENT_PARENT_PERMISSIONS],
                           fileId=xferFileId, addParents=fileInfo['addParents'], fields='', supportsAllDrives=True)
                  action = Act.Get()
                  Act.Set(Act.ADD)
                  entityModifierNewValueItemValueListActionPerformed(kvList, Act.MODIFIER_TO, None, [Ent.DRIVE_FOLDER, fileInfo['addParents']], l, lcount)
                  Act.Set(action)
              else:
                if changeParents and 'addParents' in fileInfo and entityType != Ent.DRIVE_SHORTCUT:
                  body = {'name': fileInfo['name'], 'mimeType': MIMETYPE_GA_SHORTCUT,
                          'parents': [fileInfo['addParents']], 'shortcutDetails': {'targetId': fileInfo['shortcutDetails']['targetId']}}
                  callGAPI(drive.files(), 'create',
                           throwReasons=GAPI.DRIVE_USER_THROW_REASONS+[GAPI.FORBIDDEN, GAPI.INSUFFICIENT_PERMISSIONS, GAPI.INSUFFICIENT_PARENT_PERMISSIONS,
                                                                       GAPI.INVALID, GAPI.BAD_REQUEST, GAPI.FILE_NOT_FOUND, GAPI.UNKNOWN_ERROR,
                                                                       GAPI.STORAGE_QUOTA_EXCEEDED, GAPI.TEAMDRIVES_SHARING_RESTRICTION_NOT_ALLOWED,
                                                                       GAPI.TEAMDRIVE_FILE_LIMIT_EXCEEDED, GAPI.TEAMDRIVE_HIERARCHY_TOO_DEEP, GAPI.SHORTCUT_TARGET_INVALID,
                                                                       GAPI.TARGET_USER_ROLE_LIMITED_BY_LICENSE_RESTRICTION],
                           body=body, fields='id', supportsAllDrives=True)
                  Act.Set(Act.CREATE_SHORTCUT)
                  entityModifierNewValueItemValueListActionPerformed(kvList, Act.MODIFIER_IN, None, [Ent.DRIVE_FOLDER, fileInfo['addParents']], l, lcount)
                  Act.Set(action)
            except GAPI.fileNotFound:
              entityActionFailedWarning(kvList, Msg.DOES_NOT_EXIST, l, lcount)
            except (GAPI.forbidden, GAPI.insufficientFilePermissions, GAPI.insufficientParentPermissions, GAPI.cannotAddParent) as e:
              entityActionFailedWarning(kvList, str(e), l, lcount)
            except (GAPI.serviceNotAvailable, GAPI.authError, GAPI.domainPolicy) as e:
              userDriveServiceNotEnabledWarning(user, str(e), i, count)
          Ind.Decrement()
        else:
          entityPerformActionModifierNumItemsModifier([Ent.USER, user], 'Not Performed', kcount, Ent.DRIVE_FILE_OR_FOLDER,
                                                      f'{Act.MODIFIER_FROM} {Ent.Singular(Ent.USER)}: {oldOwner}', j, jcount)
          Ind.Increment()
          l = 0
          for xferFileId, fileInfo in oldOwnerFilesToClaim.items():
            l += 1
            entityActionNotPerformedWarning([Ent.USER, user, fileInfo['type'], f'{fileInfo["name"]} ({xferFileId})'],
                                            Msg.USER_IN_OTHER_DOMAIN.format(Ent.Singular(Ent.USER), oldOwner), l, lcount)
          Ind.Decrement()
      Ind.Decrement()
      Ind.Decrement()
    Ind.Decrement()
  if csvPF:
    csvPF.writeCSVfile('Files to Claim Ownership')

# gam <UserTypeEntity> print emptydrivefolders [todrive <ToDriveAttribute>*]
#	[select <DriveFileEntity>]
#	[pathdelimiter <Character>]
