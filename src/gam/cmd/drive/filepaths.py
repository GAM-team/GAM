"""File path resolution, Drive info mapping, field handling.

"""

"""GAM Google Drive file, permission, shared drive, and label management."""

import re
import json

from gam.cmd.drive.core import _getSharedDriveNameFromId, _validateUserGetFileIDs, getDriveFileEntity
from gam.cmd.drive.filetree import extendFileTree, extendFileTreeParents, initFileTree
from gam.cmd.drive.labels import normalizeDriveLabelID

from gam.util.csv_pf import DEFAULT_SKIP_OBJECTS

from gamlib import api as API
from gamlib import settings as GC
from gamlib import gapi as GAPI
from gamlib import state as GM
from gamlib import msgs as Msg
from gam.constants import MY_DRIVE, TEAM_DRIVE

from gam.var import Act, Cmd, Ent, Ind

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

from gam.cmd.drive.core import DRIVE_LABEL_CHOICE_MAP  # cross-module ref
from gam.util.api_call import callGAPI, callGAPIitems, callGAPIpages
from gam.util.args import (
    OrderBy,
    StartEndTime,
    checkArgumentPresent,
    escapeCRsNLs,
    getArgument,
    getBoolean,
    getCharacter,
    getChoice,
    splitEmailAddress,
)
from gam.util.csv_pf import (
    FormatJSONQuoteChar,
    _getFieldsList,
    addFieldToFieldsList,
    cleanJSON,
    getFieldsFromFieldsList,
    getItemFieldsFromFieldsList,
    showJSON,
)
from gam.util.display import (
    entityActionFailedWarning,
    printEntity,
    printKeyValueList,
    printLine,
    userDriveServiceNotEnabledWarning,
)
from gam.util.entity import (
    _getEntityMimeType,
    getEntityArgument,
    getEntityList,
)
from gam.util.errors import invalidChoiceExit
from gam.util.output import writeStdout

def initFilePathInfo(delimiter):
  return {'ids': {}, 'allPaths': {}, 'localPaths': None, 'delimiter': delimiter}

def getFilePaths(drive, fileTree, initialResult, filePathInfo, addParentsToTree=False,
                 fullpath=False, showDepth=False, folderPathOnly=False, parentPathOnly=False):
  def _getParentName(result):
    if (result['mimeType'] == MIMETYPE_GA_FOLDER) and result.get('driveId') and (result['name'] == TEAM_DRIVE):
      parentName = _getSharedDriveNameFromId(drive, result['driveId'])
      if parentName != TEAM_DRIVE:
        return f'{SHARED_DRIVES}{filePathInfo["delimiter"]}{parentName}'
    return result['name']

  def _followParent(paths, parentId):
    result = None
    paths.setdefault(parentId, {})
    if fileTree:
      parentEntry = fileTree.get(parentId)
      if not parentEntry:
        if not addParentsToTree:
          return
        parentEntry = fileTree[parentId] = {'info': {'id': parentId, 'name': parentId, 'mimeType': MIMETYPE_GA_FOLDER}, 'children': []}
      if parentEntry['info']['name'] == parentEntry['info']['id'] and parentEntry['info']['id'] not in {ORPHANS, SHARED_WITHME, SHARED_DRIVES}:
        try:
          result = callGAPI(drive.files(), 'get',
                            throwReasons=GAPI.DRIVE_GET_THROW_REASONS,
                            fileId=parentId, fields='name,parents,mimeType,driveId', supportsAllDrives=True)
          parentEntry['info']['name'] = _getParentName(result)
          parentEntry['info']['parents'] = result.get('parents', [])
        except (GAPI.fileNotFound, GAPI.serviceNotAvailable, GAPI.authError, GAPI.domainPolicy):
          pass
      filePathInfo['ids'][parentId] = parentEntry['info']['name']
      parents = parentEntry['info'].get('parents', [])
    else:
      try:
        result = callGAPI(drive.files(), 'get',
                          throwReasons=GAPI.DRIVE_GET_THROW_REASONS,
                          fileId=parentId, fields='name,parents,mimeType,driveId', supportsAllDrives=True)
        filePathInfo['ids'][parentId] = _getParentName(result)
        parents = result.get('parents', [])
      except (GAPI.fileNotFound, GAPI.serviceNotAvailable, GAPI.authError, GAPI.domainPolicy):
        return
    for lparentId in parents:
      if lparentId not in filePathInfo['allPaths']:
        _followParent(paths[parentId], lparentId)
        filePathInfo['allPaths'][lparentId] = paths[parentId][lparentId]
      else:
        paths[parentId][lparentId] = filePathInfo['allPaths'][lparentId]

  def _makeFilePaths(localPaths, fplist, filePaths, name, maxDepth):
    for k, v in localPaths.items():
      fplist.append(filePathInfo['ids'].get(k, ''))
      if not v:
        fp = fplist[:]
        if showDepth:
          depth = len(fp)
          if depth > maxDepth:
            maxDepth = depth-1
        fp.reverse()
        if not parentPathOnly:
          if initialMimeType == MIMETYPE_GA_FOLDER or not folderPathOnly:
            fp.append(name)
        filePaths.append(filePathInfo['delimiter'].join(fp))
      else:
        maxDepth = _makeFilePaths(v, fplist, filePaths, name, maxDepth)
      fplist.pop()
    return maxDepth

  filePaths = []
  parents = initialResult.get('parents', [])
  initialMimeType = initialResult['mimeType']
  if parents:
    filePathInfo['localPaths'] = {}
    for parentId in parents:
      if parentId not in filePathInfo['allPaths']:
        _followParent(filePathInfo['allPaths'], parentId)
      filePathInfo['localPaths'][parentId] = filePathInfo['allPaths'][parentId]
    fplist = []
    maxDepth = _makeFilePaths(filePathInfo['localPaths'], fplist, filePaths, initialResult['name'], -1)
  else:
    if (fullpath and initialMimeType == MIMETYPE_GA_FOLDER and
        ((initialResult['name'] == MY_DRIVE) or
         (initialResult.get('driveId') and initialResult['name'].startswith(SHARED_DRIVES)))):
      filePaths.append(initialResult['name'])
    maxDepth = 0
  return (_getEntityMimeType(initialResult), filePaths, maxDepth)

def addFilePathsToRow(drive, fileTree, fileEntryInfo, filePathInfo, csvPF, row,
                      fullpath=False, showDepth=False, folderPathOnly=False, parentPathOnly=False):
  _, paths, maxDepth = getFilePaths(drive, fileTree, fileEntryInfo, filePathInfo,
                                    fullpath=fullpath, showDepth=showDepth, folderPathOnly=folderPathOnly, parentPathOnly=parentPathOnly)
  kcount = len(paths)
  if showDepth:
    row['depth'] = maxDepth
  row['paths'] = kcount
  k = 0
  for path in sorted(paths):
    key = f'path{GC.Values[GC.CSV_OUTPUT_SUBFIELD_DELIMITER]}{k}'
    csvPF.AddTitles(key)
    if GC.Values[GC.CSV_OUTPUT_CONVERT_CR_NL] and (path.find('\n') >= 0 or path.find('\r') >= 0):
      row[key] = escapeCRsNLs(path)
    else:
      row[key] = path
    k += 1

def addFilePathsToInfo(drive, fileTree, fileEntryInfo, filePathInfo, addParentsToTree=False, folderPathOnly=False, parentPathOnly=False):
  _, paths, _ = getFilePaths(drive, fileTree, fileEntryInfo, filePathInfo, addParentsToTree=addParentsToTree,
                             showDepth=False, folderPathOnly=folderPathOnly, parentPathOnly=parentPathOnly)
  fileEntryInfo['paths'] = []
  for path in sorted(paths):
    if GC.Values[GC.CSV_OUTPUT_CONVERT_CR_NL] and (path.find('\n') >= 0 or path.find('\r') >= 0):
      fileEntryInfo['paths'].append(escapeCRsNLs(path))
    else:
      fileEntryInfo['paths'].append(path)

DRIVEFILE_ORDERBY_CHOICE_MAP = {
  'createddate': 'createdTime',
  'createdtime': 'createdTime',
  'folder': 'folder',
  'lastviewedbyme': 'viewedByMeTime',
  'lastviewedbymedate': 'viewedByMeTime',
  'lastviewedbymetime': 'viewedByMeTime',
  'lastviewedbyuser': 'viewedByMeTime',
  'modifiedbyme': 'modifiedByMeTime',
  'modifiedbymedate': 'modifiedByMeTime',
  'modifiedbymetime': 'modifiedByMeTime',
  'modifiedbyuser': 'modifiedByMeTime',
  'modifieddate': 'modifiedTime',
  'modifiedtime': 'modifiedTime',
  'name': 'name',
  'namenatural': 'name_natural',
  'quotabytesused': 'quotaBytesUsed',
  'quotaused': 'quotaBytesUsed',
  'recency': 'recency',
  'sharedwithmedate': 'sharedWithMeTime',
  'sharedwithmetime': 'sharedWithMeTime',
  'starred': 'starred',
  'title': 'name',
  'titlenatural': 'name_natural',
  'viewedbymedate': 'viewedByMeTime',
  'viewedbymetime': 'viewedByMeTime',
  }

def _mapDriveUser(field):
  if 'me' in field:
    field['isAuthenticatedUser'] = field.pop('me')
  if 'photoLink' in field:
    field['picture'] = {'url': field.pop('photoLink')}

def _mapDrivePermissionNames(permission):
  emailAddress = permission.get('emailAddress')
  if emailAddress:
    _, permission['domain'] = splitEmailAddress(emailAddress)

def _mapDriveInfo(f_file, parentsSubFields, showParentsIdsAsList):
  if 'parents' in f_file:
    parents = f_file.pop('parents')
    if showParentsIdsAsList:
      f_file['parentsIds'] = parents
    elif len(parents) != 1 or parents[0] != ORPHANS:
      f_file['parents'] = []
      for parentId in parents:
        parent = {}
        if parentsSubFields['id']:
          parent['id'] = parentId
        if parentsSubFields['isRoot']:
          parent['isRoot'] = parentId == parentsSubFields['rootFolderId']
        f_file['parents'].append(parent)

  appProperties = f_file.pop('appProperties', [])
  properties = f_file.pop('properties', [])
  if appProperties:
    f_file.setdefault('properties', [])
    for key, value in sorted(appProperties.items()):
      f_file['properties'].append({'key': key, 'value': value, 'visibility': 'PRIVATE'})
  if properties:
    f_file.setdefault('properties', [])
    for key, value in sorted(properties.items()):
      f_file['properties'].append({'key': key, 'value': value, 'visibility': 'PUBLIC'})

  for permission in f_file.get('permissions', []):
    emailAddress = permission.get('emailAddress')
    if emailAddress:
      _, permission['domain'] = splitEmailAddress(emailAddress)

DRIVEFILE_BASIC_PERMISSION_FIELDS = [
  'displayName', 'id', 'emailAddress', 'domain', 'role', 'type',
  'allowFileDiscovery', 'expirationTime', 'deleted', 'inheritedPermissionsDisabled',
  'permissionDetails' #permissionDetails must be last
  ]

DRIVE_FIELDS_CHOICE_MAP = {
  'alternatelink': 'webViewLink',
  'appdatacontents': 'spaces',
  'appproperties': 'appProperties',
  'basicpermissions': ['permissions.displayName', 'permissions.id', 'permissions.emailAddress', 'permissions.domain',
                       'permissions.role', 'permissions.type', 'permissions.allowFileDiscovery',
                       'permissions.expirationTime', 'permissions.deleted', 'permissions.inheritedPermissionsDisabled'],
  'cancomment': 'capabilities.canComment',
  'canreadrevisions': 'capabilities.canReadRevisions',
  'capabilities': 'capabilities',
  'contenthints': 'contentHints',
  'contentrestrictions': 'contentRestrictions',
  'copyable': 'capabilities.canCopy',
  'copyrequireswriterpermission': 'copyRequiresWriterPermission',
  'createddate': 'createdTime',
  'createdtime': 'createdTime',
  'description': 'description',
  'downloadrestrictions': 'downloadRestrictions',
  'driveid': 'driveId',
  'drivename': 'driveId',
  'editable': 'capabilities.canEdit',
  'explicitlytrashed': 'explicitlyTrashed',
  'exportlinks': 'exportLinks',
  'fileextension': 'fileExtension',
  'filesize': 'size',
  'foldercolorrgb': 'folderColorRgb',
  'fullfileextension': 'fullFileExtension',
  'hasaugmentedpermissions': 'hasAugmentedPermissions',
  'hasthumbnail': 'hasThumbnail',
  'headrevisionid': 'headRevisionId',
  'iconlink': 'iconLink',
  'id': 'id',
  'imagemediametadata': 'imageMediaMetadata',
  'inheritedpermissionsdisabled': 'inheritedPermissionsDisabled',
  'isappauthorized': 'isAppAuthorized',
  'labelinfo': 'labelInfo',
  'labels': ['modifiedByMe', 'copyRequiresWriterPermission', 'starred', 'trashed', 'viewedByMe'],
  'lastmodifyinguser': 'lastModifyingUser',
  'lastmodifyingusername': 'lastModifyingUser.displayName',
  'lastviewedbyme': 'viewedByMeTime',
  'lastviewedbymedate': 'viewedByMeTime',
  'lastviewedbymetime': 'viewedByMeTime',
  'lastviewedbyuser': 'viewedByMeTime',
  'linksharemetadata': 'linkShareMetadata',
  'md5': 'md5Checksum',
  'md5checksum': 'md5Checksum',
  'md5sum': 'md5Checksum',
  'mime': 'mimeType',
  'mimetype': 'mimeType',
  'modifiedbymedate': 'modifiedByMeTime',
  'modifiedbymetime': 'modifiedByMeTime',
  'modifiedbyuser': 'modifiedByMeTime',
  'modifieddate': 'modifiedTime',
  'modifiedtime': 'modifiedTime',
  'name': 'name',
  'originalfilename': 'originalFilename',
  'ownedbyme': 'ownedByMe',
  'ownernames': 'owners.displayName',
  'owners': 'owners',
  'parents': 'parents',
  'permissiondetails': 'permissions.permissionDetails',
  'permissionids': 'permissionIds',
  'permissions': 'permissions',
  'properties': 'properties',
  'quotabytesused': 'quotaBytesUsed',
  'quotaused': 'quotaBytesUsed',
  'resourcekey': 'resourceKey',
  'shareable': 'capabilities.canShare',
  'shared': 'shared',
  'shareddriveid': 'driveId',
  'shareddrivename': 'driveId',
  'sharedwithmedate': 'sharedWithMeTime',
  'sharedwithmetime': 'sharedWithMeTime',
  'sharinguser': 'sharingUser',
  'shortcutdetails': 'shortcutDetails',
  'sha1checksum': 'sha1Checksum',
  'sha256checksum': 'sha256Checksum',
  'size': 'size',
  'spaces': 'spaces',
  'teamdriveid': 'driveId',
  'teamdrivename': 'driveId',
  'thumbnaillink': 'thumbnailLink',
  'thumbnailversion': 'thumbnailVersion',
  'title': 'name',
  'trasheddate': 'trashedTime',
  'trashedtime': 'trashedTime',
  'trashinguser': 'trashingUser',
  'userpermission': 'ownedByMe,capabilities.canEdit,capabilities.canComment',
  'version': 'version',
  'videomediametadata': 'videoMediaMetadata',
  'viewedbymedate': 'viewedByMeTime',
  'viewedbymetime': 'viewedByMeTime',
  'viewerscancopycontent': 'copyRequiresWriterPermission',
  'webcontentlink': 'webContentLink',
  'webviewlink': 'webViewLink',
  'writerscanshare': 'writersCanShare',
  }

DRIVE_CAPABILITIES_SUBFIELDS_CHOICE_MAP = {
  'canacceptownership': 'canAcceptOwnership',
  'canaddchildren': 'canAddChildren',
  'canaddfolderfromanotherdrive': 'canAddFolderFromAnotherDrive',
  'canaddmydriveparent': 'canAddMyDriveParent',
  'canchangecopyrequireswriterpermission': 'canChangeCopyRequiresWriterPermission',
  'canchangecopyrequireswriterpermissionrestriction': 'canChangeCopyRequiresWriterPermissionRestriction',
  'canchangedownloadrestriction': 'canChangeDownloadRestriction',
  'canchangedomainusersonlyrestriction': 'canChangeDomainUsersOnlyRestriction',
  'canchangedrivebackground': 'canChangeDriveBackground',
  'canchangedrivemembersonlyrestriction': 'canChangeDriveMembersOnlyRestriction',
  'canchangesecurityupdateenabled': 'canChangeSecurityUpdateEnabled',
  'canchangesharingfoldersrequiresorganizerpermissionrestriction': 'canChangeSharingFoldersRequiresOrganizerPermissionRestriction',
  'canchangeviewerscancopycontent': 'canChangeViewersCanCopyContent',
  'cancomment': 'canComment',
  'cancopy': 'canCopy',
  'candelete': 'canDelete',
  'candeletechildren': 'canDeleteChildren',
  'candeletedrive': 'canDeleteDrive',
  'candisableinheritedpermissions': 'canDisableInheritedPermissions',
  'candownload': 'canDownload',
  'canedit': 'canEdit',
  'canenableinheritedpermissions': 'canEnableInheritedPermissions',
  'canlistchildren': 'canListChildren',
  'canmanagemembers': 'canManageMembers',
  'canmodifycontent': 'canModifyContent',
  'canmodifycontentrestriction': 'canModifyContentRestriction',
  'canmodifyeditorcontentrestriction': 'canModifyEditorContentRestriction',
  'canmodifylabels': 'canModifyLabels',
  'canmodifyownercontentrestriction': 'canModifyOwnerContentRestriction',
  'canmovechildrenoutofdrive': 'canMoveChildrenOutOfDrive',
  'canmovechildrenoutofteamdrive': 'canMoveChildrenOutOfDrive',
  'canmovechildrenwithindrive': 'canMoveChildrenWithinDrive',
  'canmovechildrenwithinteamdrive': 'canMoveChildrenWithinDrive',
  'canmoveitemintodrive':  'canMoveItemIntoDrive',
  'canmoveitemintoteamdrive':  'canMoveItemIntoDrive',
  'canmoveitemoutofdrive': 'canMoveItemOutOfDrive',
  'canmoveitemoutofteamdrive': 'canMoveItemOutOfDrive',
  'canmoveitemwithindrive': 'canMoveItemWithinDrive',
  'canmoveitemwithinteamdrive': 'canMoveItemWithinDrive',
  'canmoveteamdriveitem': 'canMoveTeamDriveItem',
  'canreaddrive': 'canReadDrive',
  'canreadlabels': 'canReadLabels',
  'canreadrevisions': 'canReadRevisions',
  'canreadteamdrive': 'canReadDrive',
  'canremovechildren': 'canRemoveChildren',
  'canremovecontentrestriction': 'canRemoveContentRestriction',
  'canremovemydriveparent': 'canRemoveMyDriveParent',
  'canrename': 'canRename',
  'canrenamedrive': 'canRenameDrive',
  'canresetdriverestrictions': 'canResetDriveRestrictions',
  'canshare': 'canShare',
  'cantrash': 'canTrash',
  'cantrashchildren': 'canTrashChildren',
  'canuntrash': 'canUntrash',
  }

DRIVE_CONTENT_RESTRICTIONS_SUBFIELDS_CHOICE_MAP = {
  'ownerrestricted': 'ownerRestricted',
  'readonly': 'readOnly',
  'reason': 'reason',
  'restrictinguser': 'restrictingUser',
  'restrictiontime': 'restrictionTime',
  'type': 'type',
  }

DRIVE_DOWNLOAD_RESTRICTIONS_SUBFIELDS_CHOICE_MAP = {
  'itemdownloadrestriction': 'itemDownloadRestriction',
  'effectivedownloadrestrictionwithcontext': 'effectiveDownloadRestrictionWithContext',
  }

DRIVE_LABELINFO_SUBFIELDS_CHOICE_MAP = {
  'id': 'labels(id)',
  'fields': 'labels(fields)',
  'revisionid': 'labels(revisionId)',
  }

DRIVE_OWNERS_SUBFIELDS_CHOICE_MAP = {
  'displayname': 'displayName',
  'emailaddress': 'emailAddress',
  'isauthenticateduser': 'me',
  'me': 'me',
  'permissionid': 'permissionId',
  'photolink': 'photoLink',
  'picture': 'photoLink',
  }

DRIVE_PARENTS_SUBFIELDS_CHOICE_MAP = {
  'id': 'id',
  'isroot': 'isRoot',
  }

DRIVE_PERMISSIONS_SUBFIELDS_CHOICE_MAP = {
  'additionalroles': 'role',
  'allowfilediscovery': 'allowFileDiscovery',
  'deleted': 'deleted',
  'displayname': 'displayName',
  'domain': 'domain',
  'emailaddress': 'emailAddress',
  'expirationdate': 'expirationTime',
  'expirationtime': 'expirationTime',
  'id': 'id',
  'inheritedpermissionsdisabled': 'inheritedPermissionsDisabled',
  'name': 'displayName',
  'pendingowner': 'pendingOwner',
  'permissiondetails': 'permissionDetails',
  'photolink': 'photoLink',
  'role': 'role',
  'shareddrivepermissiondetails': 'permissionDetails',
  'teamdrivepermissiondetails': 'permissionDetails',
  'type': 'type',
  'view': 'view',
  'withlink': 'allowFileDiscovery',
  }

DRIVE_SHARINGUSER_SUBFIELDS_CHOICE_MAP = {
  'displayname': 'displayName',
  'emailaddress': 'emailAddress',
  'isauthenticateduser': 'me',
  'me': 'me',
  'name': 'displayName',
  'permissionid': 'permissionId',
  'photolink': 'photoLink',
  'picture': 'photoLink',
  }

DRIVE_SHORTCUTDETAILS_SUBFIELDS_CHOICE_MAP = {
  'targetid': 'targetId',
  'targetmimetype': 'targetMimeType',
  'targetresourcekey': 'targetResourceKey',
  }

DRIVE_SUBFIELDS_CHOICE_MAP = {
  'capabilities': DRIVE_CAPABILITIES_SUBFIELDS_CHOICE_MAP,
  'contentrestrictions': DRIVE_CONTENT_RESTRICTIONS_SUBFIELDS_CHOICE_MAP,
  'downloadrestrictions': DRIVE_DOWNLOAD_RESTRICTIONS_SUBFIELDS_CHOICE_MAP,
  'labelinfo': DRIVE_LABELINFO_SUBFIELDS_CHOICE_MAP,
  'labels': DRIVE_LABEL_CHOICE_MAP,
  'lastmodifyinguser': DRIVE_SHARINGUSER_SUBFIELDS_CHOICE_MAP,
  'owners': DRIVE_OWNERS_SUBFIELDS_CHOICE_MAP,
  'parents': DRIVE_PARENTS_SUBFIELDS_CHOICE_MAP,
  'permissions': DRIVE_PERMISSIONS_SUBFIELDS_CHOICE_MAP,
  'sharinguser': DRIVE_SHARINGUSER_SUBFIELDS_CHOICE_MAP,
  'trashinguser': DRIVE_SHARINGUSER_SUBFIELDS_CHOICE_MAP,
  'shortcutdetails': DRIVE_SHORTCUTDETAILS_SUBFIELDS_CHOICE_MAP,
}

DRIVE_LIST_FIELDS = {'owners', 'parents', 'permissions', 'permissionIds', 'spaces'}

FILEINFO_FIELDS_TITLES = ['name', 'mimeType']
FILEPATH_FIELDS_TITLES = ['name', 'id', 'mimeType', 'ownedByMe', 'parents', 'sharedWithMeTime', 'driveId']
FILEPATH_FIELDS = ','.join(FILEPATH_FIELDS_TITLES)

DRIVE_TIME_OBJECTS = {'createdTime', 'viewedByMeTime', 'modifiedByMeTime', 'modifiedTime', 'restrictionTime', 'sharedWithMeTime', 'trashedTime'}

def _getIncludeLabels(includeLabels):
  labelIds = getEntityList(Cmd.OB_CLASSIFICATION_LABEL_ID, shlexSplit=True)
  for labelId in labelIds:
    includeLabels.add(normalizeDriveLabelID(labelId))

def _finalizeIncludeLabels(includeLabels):
  if includeLabels:
    return ','.join(includeLabels)
  return None

DRIVEFILE_PERMISSIONS_FOR_VIEW_CHOICES = ['published']

def _getIncludePermissionsForView(includePermissionsForView):
  ipfwList = getEntityList(Cmd.OB_STRING_LIST)
  for ipfw in ipfwList:
    if ipfw in DRIVEFILE_PERMISSIONS_FOR_VIEW_CHOICES:
      includePermissionsForView.add(ipfw)
    else:
      invalidChoiceExit(ipfw, DRIVEFILE_PERMISSIONS_FOR_VIEW_CHOICES, True)

def _finalizeIncludePermissionsForView(includePermissionsForView):
  if includePermissionsForView:
    return ','.join(includePermissionsForView)
  return None

def _getDriveFieldSubField(field, fieldsList, parentsSubFields):
  field, subField = field.split('.', 1)
  if field in DRIVE_SUBFIELDS_CHOICE_MAP:
    if field == 'parents':
      fieldsList.append(DRIVE_FIELDS_CHOICE_MAP[field])
      parentsSubFields[DRIVE_SUBFIELDS_CHOICE_MAP[field][subField]] = True
    elif subField in DRIVE_SUBFIELDS_CHOICE_MAP[field]:
      if field != 'labels':
        if not isinstance(DRIVE_SUBFIELDS_CHOICE_MAP[field][subField], list):
          fieldsList.append(f'{DRIVE_FIELDS_CHOICE_MAP[field]}.{DRIVE_SUBFIELDS_CHOICE_MAP[field][subField]}')
        else:
          for subSubField in DRIVE_SUBFIELDS_CHOICE_MAP[field][subField]:
            fieldsList.append(f'{DRIVE_FIELDS_CHOICE_MAP[field]}.{subSubField}')
      else:
        fieldsList.append(DRIVE_SUBFIELDS_CHOICE_MAP[field][subField])
    else:
      invalidChoiceExit(subField, list(DRIVE_SUBFIELDS_CHOICE_MAP[field]), True)
  else:
    invalidChoiceExit(field, list(DRIVE_SUBFIELDS_CHOICE_MAP), True)

class DriveFileFields():
  def __init__(self):
    self.showSharedDriveNames = False
    self.allFields = False
    self.OBY = OrderBy(DRIVEFILE_ORDERBY_CHOICE_MAP)
    self.fieldsList = []
    self.includeLabels = set()
    self.includePermissionsForView = set()
    self.parentsSubFields = {'id': False, 'isRoot': False, 'rootFolderId': None}

  def SetAllParentsSubFields(self):
    self.parentsSubFields['id'] = self.parentsSubFields['isRoot'] = True

  def ProcessArgument(self, myarg):
    if myarg == 'allfields':
      self.fieldsList = []
      self.allFields = True
    elif myarg in DRIVE_LABEL_CHOICE_MAP:
      addFieldToFieldsList(myarg, DRIVE_LABEL_CHOICE_MAP, self.fieldsList)
    elif myarg in DRIVE_FIELDS_CHOICE_MAP:
      addFieldToFieldsList(myarg, DRIVE_FIELDS_CHOICE_MAP, self.fieldsList)
      if myarg == 'parents':
        self.SetAllParentsSubFields()
      elif myarg in {'drivename', 'shareddrivename', 'teamdrivename'}:
        self.showSharedDriveNames = True
    elif myarg == 'fields':
      for field in _getFieldsList():
        if field in DRIVE_LABEL_CHOICE_MAP:
          addFieldToFieldsList(field, DRIVE_LABEL_CHOICE_MAP, self.fieldsList)
        elif field.find('.') == -1:
          if field in DRIVE_FIELDS_CHOICE_MAP:
            addFieldToFieldsList(field, DRIVE_FIELDS_CHOICE_MAP, self.fieldsList)
            if field == 'parents':
              self.SetAllParentsSubFields()
            elif field in {'drivename', 'shareddrivename', 'teamdrivename'}:
              self.showSharedDriveNames = True
          else:
            invalidChoiceExit(field, list(DRIVE_FIELDS_CHOICE_MAP)+list(DRIVE_LABEL_CHOICE_MAP), True)
        else:
          _getDriveFieldSubField(field, self.fieldsList, self.parentsSubFields)
    elif myarg == 'includelabels':
      _getIncludeLabels(self.includeLabels)
    elif myarg == 'includepermissionsforview':
      _getIncludePermissionsForView(self.includePermissionsForView)
    elif myarg.find('.') != -1:
      _getDriveFieldSubField(myarg, self.fieldsList, self.parentsSubFields)
    elif myarg == 'orderby':
      self.OBY.GetChoice()
    elif myarg in {'showdrivename', 'showshareddrivename', 'showteamdrivename'}:
      self.showSharedDriveNames = True
    else:
      return False
    return True

  @property
  def orderBy(self):
    return self.OBY.orderBy

def _setSkipObjects(skipObjects, skipTitles, fieldsList):
  for field in skipTitles:
    if field != 'parents':
      if field not in fieldsList:
        skipObjects.add(field)
        fieldsList.append(field)
    else:
      for xfield in fieldsList:
        if xfield.startswith('parents'):
          break
      else:
        skipObjects.add(field)
      fieldsList.append('parents')

def _setGetPermissionsForMyDriveSharedDrives(fieldsList, permissionsFieldsList):
  getPermissionDetailsForMyDrive = getPermissionsForSharedDrives = False
  permissionsFields = None
  for field in fieldsList:
    if field.startswith('permissions'):
      if field.find('.') != -1:
        field, subField = field.split('.', 1)
        permissionsFieldsList.append(subField)
      else:
        permissionsFieldsList.append('*')
  if permissionsFieldsList:
    if 'permissionDetails' in permissionsFieldsList:
      getPermissionDetailsForMyDrive = True
    getPermissionsForSharedDrives = True
    permissionsFields = getItemFieldsFromFieldsList('permissions', permissionsFieldsList, True)
  return (getPermissionDetailsForMyDrive, getPermissionsForSharedDrives, permissionsFields)

# Do file permissions have to be gotten by API call?
def _setGetCheckFilePermissions(fileinfo, getPermissionDetailsForMyDrive, getPermissionsForSharedDrives, driveId, DLP):
  filePerms = fileinfo.get('permissions')
  if getPermissionsForSharedDrives and driveId and not filePerms:
    return True
  if getPermissionDetailsForMyDrive:
    return True
  if DLP.PM.checkDetails:
    if not filePerms:
      return True
    permDetails = filePerms[0].get('permissionDetails')
    if (not permDetails) or 'inherited' not in permDetails[0]:
      return True
  return False

SHOWLABELS_CHOICES = {'details', 'ids'}

def _formatFileDriveLabels(showLabels, labels, result, printMode, delimiter):
  if showLabels == 'details':
    result['labels'] = labels
  else:
    if printMode:
      result['labels'] = len(labels)
    result['labelsIds'] = delimiter.join([label['id'] for label in labels])

# gam <UserTypeEntity> info drivefile <DriveFileEntity>
#	[returnidonly]
#	[filepath|fullpath] [folderpathonly|parentpathonly [<Boolean>]] [pathdelimiter <Character>]
#	[allfields|<DriveFieldName>*|(fields <DriveFieldNameList>)] [formatjson]
#	(orderby <DriveFileOrderByFieldName> [ascending|descending])*
#	[showdrivename] [showshareddrivepermissions]
#	[(showlabels details|ids)|(includelabels <DriveLabelIDList>)]
#	[includepermissionsforview published]
#	[showparentsidsaslist] [followshortcuts [<Boolean>]]
#	[stripcrsfromname] [formatjson]
# gam <UserTypeEntity> show fileinfo <DriveFileEntity>
#	[returnidonly]
#	[filepath|fullpath] [folderpathonly|parentpathonly [<Boolean>]] [pathdelimiter <Character>]
#	[allfields|<DriveFieldName>*|(fields <DriveFieldNameList>)] [formatjson]
#	(orderby <DriveFileOrderByFieldName> [ascending|descending])*
#	[showdrivename] [showshareddrivepermissions]
#	[(showlabels details|ids)|(includelabels <DriveLabelIDList>)]
#	[includepermissionsforview published]
#	[showparentsidsaslist] [followshortcuts [<Boolean>]]
#	[stripcrsfromname] [formatjson]
def showFileInfo(users):
  def _setSelectionFields():
    _setSkipObjects(skipObjects, FILEINFO_FIELDS_TITLES, DFF.fieldsList)
    if filepath:
      _setSkipObjects(skipObjects, FILEPATH_FIELDS_TITLES, DFF.fieldsList)
    if getPermissionsForSharedDrives or DFF.showSharedDriveNames:
      _setSkipObjects(skipObjects, ['driveId'], DFF.fieldsList)
    if followShortcuts:
      _setSkipObjects(skipObjects, ['mimeType', 'shortcutDetails'], DFF.fieldsList)

  getPermissionsForSharedDrives = filepath = fullpath = folderPathOnly = parentPathOnly = followShortcuts = \
    returnIdOnly = showParentsIdsAsList = showNoParents = stripCRsFromName = False
  pathDelimiter = '/'
  showLabels = None
  permissionsFieldsList = []
  simpleLists = []
  skipObjects = set()
  fileIdEntity = getDriveFileEntity()
  DFF = DriveFileFields()
  FJQC = FormatJSONQuoteChar()
  while Cmd.ArgumentsRemaining():
    myarg = getArgument()
    if myarg == 'filepath':
      filepath = True
    elif myarg == 'fullpath':
      filepath = fullpath = True
    elif myarg == 'folderpathonly':
      folderPathOnly = getBoolean()
    elif myarg == 'parentpathonly':
      parentPathOnly = getBoolean()
    elif myarg == 'pathdelimiter':
      pathDelimiter = getCharacter()
    elif myarg == 'showparentsidsaslist':
      showParentsIdsAsList = True
      simpleLists.append('parentsIds')
    elif myarg == 'stripcrsfromname':
      stripCRsFromName = True
    elif myarg == 'showlabels':
      showLabels = getChoice(SHOWLABELS_CHOICES)
    elif myarg == 'showshareddrivepermissions':
      permissionsFieldsList = DRIVEFILE_BASIC_PERMISSION_FIELDS.copy()
    elif myarg == 'returnidonly':
      returnIdOnly = True
    elif myarg == 'followshortcuts':
      followShortcuts = getBoolean()
    elif DFF.ProcessArgument(myarg):
      pass
    else:
      FJQC.GetFormatJSON(myarg)
  _, getPermissionsForSharedDrives, permissionsFields = _setGetPermissionsForMyDriveSharedDrives(DFF.fieldsList, permissionsFieldsList)
  if DFF.fieldsList:
    _setSelectionFields()
    if followShortcuts:
      DFF.fieldsList.extend(['mimeType', 'shortcutDetails'])
    fields = getFieldsFromFieldsList(DFF.fieldsList)
    showNoParents = 'parents' in DFF.fieldsList
  else:
    fields = '*'
    DFF.SetAllParentsSubFields()
    skipObjects = skipObjects.union(DEFAULT_SKIP_OBJECTS)
    showNoParents = True
  includeLabels = _finalizeIncludeLabels(DFF.includeLabels)
  includePermissionsForView = _finalizeIncludePermissionsForView(DFF.includePermissionsForView)
  pathFields = FILEPATH_FIELDS
  i, count, users = getEntityArgument(users)
  for user in users:
    i += 1
    if returnIdOnly:
      GC.Values[GC.SHOW_GETTINGS] = False
    user, drive, jcount = _validateUserGetFileIDs(user, i, count, fileIdEntity,
                                                  entityType=[Ent.DRIVE_FILE_OR_FOLDER, None][FJQC.formatJSON or returnIdOnly],
                                                  orderBy=DFF.orderBy)
    if jcount == 0:
      continue
    if returnIdOnly:
      for fileId in fileIdEntity['list']:
        writeStdout(f'{fileId}\n')
      continue
    if not showParentsIdsAsList and DFF.parentsSubFields['isRoot']:
      try:
        DFF.parentsSubFields['rootFolderId'] = callGAPI(drive.files(), 'get',
                                                        throwReasons=GAPI.DRIVE_USER_THROW_REASONS,
                                                        fileId=ROOT, fields='id')['id']
      except (GAPI.serviceNotAvailable, GAPI.authError, GAPI.domainPolicy) as e:
        userDriveServiceNotEnabledWarning(user, str(e), i, count)
        continue
    if filepath:
      filePathInfo = initFilePathInfo(pathDelimiter)
      if fullpath:
        fileTree, status = initFileTree(drive, fileIdEntity.get('shareddrive'), None, [], True, user, i, count)
        if not status:
          continue
      else:
        fileTree =  None
    Ind.Increment()
    j = 0
    for fileId in fileIdEntity['list']:
      j += 1
      try:
        result = callGAPI(drive.files(), 'get',
                          throwReasons=GAPI.DRIVE_GET_THROW_REASONS+[GAPI.INVALID],
                          fileId=fileId, includeLabels=includeLabels, includePermissionsForView=includePermissionsForView,
                          fields=fields, supportsAllDrives=True)
        if followShortcuts and result['mimeType'] == MIMETYPE_GA_SHORTCUT:
          fileId = result['shortcutDetails']['targetId']
          result = callGAPI(drive.files(), 'get',
                            throwReasons=GAPI.DRIVE_GET_THROW_REASONS+[GAPI.INVALID],
                            fileId=fileId, includeLabels=includeLabels, includePermissionsForView=includePermissionsForView,
                            fields=fields, supportsAllDrives=True)
        if stripCRsFromName:
          result['name'] = _stripControlCharsFromName(result['name'])
        driveId = result.get('driveId')
        if driveId:
          if result['mimeType'] == MIMETYPE_GA_FOLDER and result['name'] == TEAM_DRIVE:
            result['name'] = _getSharedDriveNameFromId(drive, driveId)
          if DFF.showSharedDriveNames:
            result['driveName'] = _getSharedDriveNameFromId(drive, driveId)
        if showNoParents:
          result.setdefault('parents', [])
        if getPermissionsForSharedDrives and driveId and 'permissions' not in result:
          try:
            result['permissions'] = callGAPIpages(drive.permissions(), 'list', 'permissions',
                                                  throwReasons=GAPI.DRIVE3_GET_ACL_REASONS,
                                                  retryReasons=GAPI.SERVICE_NOT_AVAILABLE_RETRY_REASONS,
                                                  fileId=fileId, fields=permissionsFields, supportsAllDrives=True)
            for permission in result['permissions']:
              permission.pop('teamDrivePermissionDetails', None)
          except (GAPI.insufficientAdministratorPrivileges, GAPI.insufficientFilePermissions) as e:
            if fields != '*':
              entityActionFailedWarning([Ent.USER, user, Ent.DRIVE_FILE_OR_FOLDER_ID, fileId], str(e), j, jcount)
              continue
        if showLabels is not None:
          labels = callGAPIitems(drive.files(), 'listLabels', 'labels',
                                 throwReasons=GAPI.DRIVE_GET_THROW_REASONS,
                                 retryReasons=GAPI.SERVICE_NOT_AVAILABLE_RETRY_REASONS+[GAPI.UNKNOWN_ERROR],
                                 fileId=fileId)
          _formatFileDriveLabels(showLabels, labels, result, False, ' ')
        if not FJQC.formatJSON:
          printEntity([_getEntityMimeType(result), f'{result["name"]} ({fileId})'], j, jcount)
          Ind.Increment()
        if filepath:
          if fullpath:
            extendFileTree(fileTree, [result], None, False)
            extendFileTreeParents(drive, fileTree, pathFields)
          if not FJQC.formatJSON:
            _, paths, _ = getFilePaths(drive, fileTree, result, filePathInfo, addParentsToTree=True,
                                       fullpath=fullpath, folderPathOnly=folderPathOnly, parentPathOnly=parentPathOnly)
            kcount = len(paths)
            printKeyValueList(['paths', kcount])
            Ind.Increment()
            for path in sorted(paths):
              printKeyValueList(['path', path])
            Ind.Decrement()
          else:
            addFilePathsToInfo(drive, fileTree, result, filePathInfo,
                               addParentsToTree=True, folderPathOnly=folderPathOnly, parentPathOnly=parentPathOnly)
        if fullpath:
          # Save simple parents list as mappings turn it into a list of dicts
          fpparents = result['parents'][:]
        _mapDriveInfo(result, DFF.parentsSubFields, showParentsIdsAsList)
        if not FJQC.formatJSON:
          showJSON(None, result, skipObjects=skipObjects, timeObjects=DRIVE_TIME_OBJECTS, simpleLists=simpleLists,
                   dictObjectsKey={'owners': 'displayName', 'fields': 'id', 'labels': 'id', 'user': 'emailAddress', 'parents': 'id',
                                   'permissions': 'displayName', 'permissionDetails': 'inherited'})
          Ind.Decrement()
        else:
          printLine(json.dumps(cleanJSON(result, skipObjects=skipObjects, timeObjects=DRIVE_TIME_OBJECTS), ensure_ascii=False, sort_keys=True))
        if fullpath:
          # Restore simple parents list
          fileTree[fileId]['info']['parents'] = fpparents[:]
      except (GAPI.fileNotFound, GAPI.forbidden, GAPI.internalError,
              GAPI.insufficientFilePermissions, GAPI.unknownError, GAPI.invalid) as e:
        entityActionFailedWarning([Ent.USER, user, Ent.DRIVE_FILE_OR_FOLDER_ID, fileId], str(e), j, jcount)
      except (GAPI.serviceNotAvailable, GAPI.authError, GAPI.domainPolicy) as e:
        userDriveServiceNotEnabledWarning(user, str(e), i, count)
        break
    Ind.Decrement()

