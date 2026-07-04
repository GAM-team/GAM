"""File tree building, permission matching, file entity selection.

"""

"""GAM Google Drive file, permission, shared drive, and label management."""

import re

from gam.cmd.drive.core import _getSharedDriveNameFromId, _mapDrive2QueryToDrive3, cleanFileIDsList, escapeDriveFileName, getEscapedDriveFileName, initDriveFileEntity
from gam.cmd.drive.revisions import _stripMeInOwners, _stripNotMeInOwners, _updateAnyOwnerQuery

from gamlib import api as API
from gamlib import settings as GC
from gamlib import gapi as GAPI
from gamlib import state as GM
from gamlib import msgs as Msg
from gam.util.entity import QUERY_SHORTCUTS_MAP
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

from gam.cmd.drive.core import (
    MimeTypeCheck,
    DRIVE_BY_NAME_CHOICE_MAP,
    LOCATION_ALL_DRIVES,
    LOCATION_CHOICE_MAP,
    LOCATION_ONLY_SHARED_DRIVES,
    _getSharedDriveNameFromId,
    _mapDrive2QueryToDrive3,
    cleanFileIDsList,
    escapeDriveFileName,
    getEscapedDriveFileName,
    initDriveFileEntity,
)
from gam.util.api import callGAPI, callGAPIpages
from gam.util.args import (
    StartEndTime,
    checkArgumentPresent,
    checkGetArgument,
    escapeCRsNLs,
    getArgument,
    getBoolean,
    getChoice,
    getInteger,
    getREPattern,
    getString,
    getTimeOrDeltaFromNow,
    splitEmailAddress,
)
from gam.util.display import entityActionFailedWarning, userDriveServiceNotEnabledWarning
from gam.util.errors import invalidChoiceExit, unknownArgumentExit, usageErrorExit

def initFileTree(drive, shareddrive, DLP, shareddriveFields, showParent, user, i, count):
  fileTree = {
    ORPHANS: {'info': {'id': ORPHANS, 'name': ORPHANS, 'mimeType': MIMETYPE_GA_FOLDER, 'ownedByMe': True, 'parents': []},
              'noParents': True, 'children': []},
    SHARED_WITHME: {'info': {'id': SHARED_WITHME, 'name': SHARED_WITHME, 'mimeType': MIMETYPE_GA_FOLDER, 'ownedByMe': False, 'parents': []},
                    'noParents': True, 'children': []},
    SHARED_DRIVES: {'info': {'id': SHARED_DRIVES, 'name': SHARED_DRIVES, 'mimeType': MIMETYPE_GA_FOLDER, 'ownedByMe': False, 'parents': [], 'driveId': SHARED_DRIVES},
                    'noParents': True, 'children': []},
    }
  try:
    if not shareddrive:
      fileId = ROOT
      f_file = callGAPI(drive.files(), 'get',
                        throwReasons=GAPI.DRIVE_USER_THROW_REASONS,
                        fileId=fileId, fields=FILEPATH_FIELDS)
      f_file['parents'] = []
      fileTree[f_file['id']] = {'info': f_file, 'noParents': True, 'children': []}
    elif 'driveId' in shareddrive:
      fileId = shareddrive['driveId']
      f_file = callGAPI(drive.files(), 'get',
                        throwReasons=GAPI.DRIVE_USER_THROW_REASONS+[GAPI.NOT_FOUND, GAPI.FILE_NOT_FOUND],
                        fileId=fileId, supportsAllDrives=True, fields=FILEPATH_FIELDS)
      f_file['parents'] = []
      fileTree[f_file['id']] = {'info': f_file, 'noParents': True, 'children': []}
      name = callGAPI(drive.drives(), 'get',
                      throwReasons=GAPI.DRIVE_USER_THROW_REASONS+[GAPI.FILE_NOT_FOUND, GAPI.NOT_FOUND],
                      driveId=fileId, fields='name')['name']
      fileTree[f_file['id']]['info']['name'] = f'{SHARED_DRIVES}/{name}'
    else:
      fileId = None
    if DLP and (DLP.getSharedDriveNames or DLP.checkLocation in {LOCATION_ALL_DRIVES, LOCATION_ONLY_SHARED_DRIVES}):
      tdrives = callGAPIpages(drive.drives(), 'list', 'drives',
                              throwReasons=GAPI.DRIVE_USER_THROW_REASONS+[GAPI.INVALID, GAPI.NO_LIST_TEAMDRIVES_ADMINISTRATOR_PRIVILEGE],
                              fields='nextPageToken,drives(id,name)', pageSize=100)
      for tdrive in tdrives:
        fileId = tdrive['id']
        if fileId not in fileTree:
          fileTree[fileId] = {'info': {'id': fileId, 'name': f'{SHARED_DRIVES}/{tdrive["name"]}', 'mimeType': MIMETYPE_GA_FOLDER},
                              'noParents': True, 'children': []}
        for field in shareddriveFields:
          if field in tdrive:
            fileTree[fileId]['info'][field] = tdrive[field]
        if showParent:
          fileTree[fileId]['info']['driveId'] = fileId
        fileTree[SHARED_DRIVES]['children'].append(fileId)
  except (GAPI.notFound, GAPI.fileNotFound, GAPI.invalid, GAPI.noListTeamDrivesAdministratorPrivilege) as e:
    entityActionFailedWarning([Ent.USER, user, Ent.SHAREDDRIVE, fileId], str(e), i, count)
    return (None, False)
  except (GAPI.serviceNotAvailable, GAPI.authError, GAPI.domainPolicy) as e:
    userDriveServiceNotEnabledWarning(user, str(e), i, count)
    return (None, False)
  return (fileTree, True)

def extendFileTree(fileTree, feed, DLP, stripCRsFromName):
  for f_file in feed:
    if DLP and (not DLP.CheckOnlySharedDrives(f_file) or not DLP.CheckExcludeTrashed(f_file)):
      continue
    if stripCRsFromName:
      f_file['name'] = _stripControlCharsFromName(f_file['name'])
    fileId = f_file['id']
    if not f_file.get('parents', []):
      if not f_file.get('driveId'):
        if f_file['mimeType'] == MIMETYPE_GA_FOLDER and f_file['name'] == MY_DRIVE:
          f_file['parents'] = []
        else:
          f_file['parents'] = [ORPHANS] if f_file.get('ownedByMe', False) and 'sharedWithMeTime' not in f_file else [SHARED_WITHME]
      else:
        f_file['parents'] = [SHARED_DRIVES] if 'sharedWithMeTime' not in f_file else [SHARED_WITHME]
    if fileId not in fileTree:
      fileTree[fileId] = {'info': f_file, 'children': []}
    else:
      fileTree[fileId]['info'] = f_file
    for parentId in f_file['parents']:
      if parentId not in fileTree:
        fileTree[parentId] = {'info': {'id': parentId, 'name': parentId, 'mimeType': MIMETYPE_GA_FOLDER}, 'children': []}
      fileTree[parentId]['children'].append(fileId)

def extendFileTreeParents(drive, fileTree, fields):
  def _followParent(fileId):
    try:
      result = callGAPI(drive.files(), 'get',
                        throwReasons=GAPI.DRIVE_GET_THROW_REASONS,
                        fileId=fileId, fields=fields, supportsAllDrives=True)
      if not result.get('parents', []):
        if not result.get('driveId'):
          result['parents'] = [ORPHANS] if result.get('ownedByMe', False) and 'sharedWithMeTime' not in result else [SHARED_WITHME]
        else:
          if result['name'] == TEAM_DRIVE:
            result['name'] = _getSharedDriveNameFromId(drive, result['driveId'])
          result['parents'] = [SHARED_DRIVES] if 'sharedWithMeTime' not in result else [SHARED_WITHME]
      fileTree[fileId]['info'] = result
      fileTree[fileId]['info']['noDisplay'] = True
      for parentId in result['parents']:
        if parentId not in fileTree:
          fileTree[parentId] = {'info': {'id': parentId, 'name': parentId, 'mimeType': MIMETYPE_GA_FOLDER}, 'children': []}
          _followParent(parentId)
        fileTree[parentId]['children'].append(fileId)
    except (GAPI.fileNotFound, GAPI.serviceNotAvailable, GAPI.authError, GAPI.domainPolicy):
      fileTree[fileId] = {'info': {'id': fileId, 'name': fileId, 'mimeType': MIMETYPE_GA_FOLDER, 'parents': [], 'noDisplay': True},
                          'children': []}

  for fileId in list(fileTree):
    f_file = fileTree[fileId]
    if 'parents' not in f_file['info'] and not f_file.get('noParents', False):
      f_file['info']['noDisplay'] = True
      _followParent(fileId)

def buildFileTree(feed, drive):
  fileTree = {
    ORPHANS: {'info': {'id': ORPHANS, 'name': ORPHANS, 'mimeType': MIMETYPE_GA_FOLDER, 'ownedByMe': True}, 'children': []},
    }
  try:
    f_file = callGAPI(drive.files(), 'get',
                      throwReasons=GAPI.DRIVE_USER_THROW_REASONS,
                      fileId=ROOT, fields=FILEPATH_FIELDS)
    fileTree[f_file['id']] = {'info': f_file, 'children': []}
  except (GAPI.serviceNotAvailable, GAPI.authError, GAPI.domainPolicy,
          GAPI.notFound, GAPI.invalid, GAPI.noListTeamDrivesAdministratorPrivilege):
    pass
  for f_file in feed:
    if 'parents' not in f_file:
      f_file['parents'] = []
    fileId = f_file['id']
    if fileId not in fileTree:
      fileTree[fileId] = {'info': f_file, 'children': []}
    else:
      fileTree[fileId]['info'] = f_file
    parents = f_file['parents']
    if not parents:
      parents = [ORPHANS]
    for parentId in parents:
      if parentId not in fileTree:
        fileTree[parentId] = {'info': {'id': parentId, 'name': parentId, 'mimeType': MIMETYPE_GA_FOLDER}, 'children': []}
      fileTree[parentId]['children'].append(fileId)
  return fileTree

def _validateACLOwnerType(location, body):
  if body.get('role', '') == 'owner' and body['type'] != 'user':
    Cmd.SetLocation(location)
    usageErrorExit(Msg.INVALID_PERMISSION_ATTRIBUTE_TYPE.format(f'role {body["role"]}', body['type']))

def _validateACLAttributes(myarg, location, body, field, validTypes):
  if field in body and body['type'] not in validTypes:
    Cmd.SetLocation(location-1)
    usageErrorExit(Msg.INVALID_PERMISSION_ATTRIBUTE_TYPE.format(myarg, body['type']))

def _validatePermissionOwnerType(location, body):
  if 'role' in body:
    badTypes = body['type']-{'user'}
    if 'owner' in body['role'] and badTypes:
      Cmd.SetLocation(location)
      usageErrorExit(Msg.INVALID_PERMISSION_ATTRIBUTE_TYPE.format('role owner', ','.join(badTypes)))

def _validatePermissionAttributes(myarg, location, body, field, validTypes):
  if field in body:
    badTypes = body['type']-validTypes
    if badTypes:
      Cmd.SetLocation(location-1)
      usageErrorExit(Msg.INVALID_PERMISSION_ATTRIBUTE_TYPE.format(myarg, ','.join(badTypes)))

DRIVEFILE_ACL_ROLES_MAP = {
  'commenter': 'commenter',
  'contentmanager': 'fileOrganizer',
  'contributor': 'writer',
  'editor': 'writer',
  'fileorganizer': 'fileOrganizer',
  'fileorganiser': 'fileOrganizer',
  'manager': 'organizer',
  'organizer': 'organizer',
  'organiser': 'organizer',
  'owner': 'owner',
  'read': 'reader',
  'reader': 'reader',
  'viewer': 'reader',
  'writer': 'writer',
  }

DRIVEFILE_ACL_PERMISSION_TYPES = ['anyone', 'domain', 'group', 'user'] # anyone must be first element
DRIVEFILE_ACL_PERMISSION_DETAILS_TYPES = ['file', 'member']

class PermissionMatch():
  _PERMISSION_MATCH_ACTION_MAP = {'process': True, 'skip': False}
  _PERMISSION_MATCH_MODE_MAP = {'or': True, 'and': False}

  def __init__(self):
    self.permissionMatches = []
    self.permissionMatchKeep = self.permissionMatchOr = True
    self.permissionFields = set()
    self.clearDefaultMatch = False
    self.checkDetails = False

  def GetMatch(self):
    startEndTime = StartEndTime('expirationstart', 'expirationend')
    roleLocation = withLinkLocation = expirationStartLocation = expirationEndLocation = deletedLocation = None
    requiredMatch = not checkArgumentPresent('not')
    body = {}
    while Cmd.ArgumentsRemaining():
      myarg = getArgument()
      if myarg in {'type', 'nottype'}:
        body[myarg] = set()
        body[myarg].add(getChoice(DRIVEFILE_ACL_PERMISSION_TYPES))
        self.permissionFields.add('type')
      elif myarg in {'typelist', 'nottypelist'}:
        arg = 'type' if myarg == 'typelist' else 'nottype'
        body[arg] = set()
        for ptype in getString(Cmd.OB_PERMISSION_TYPE_LIST).lower().replace(',', ' ').split():
          if ptype in DRIVEFILE_ACL_PERMISSION_TYPES:
            body[arg].add(ptype)
          else:
            invalidChoiceExit(ptype, DRIVEFILE_ACL_PERMISSION_TYPES, True)
        self.permissionFields.add('type')
      elif myarg in {'role', 'notrole'}:
        roleLocation = Cmd.Location()
        body[myarg] = set()
        body[myarg].add(getChoice(DRIVEFILE_ACL_ROLES_MAP, mapChoice=True))
        self.permissionFields.add('role')
      elif myarg in {'rolelist', 'notrolelist'}:
        arg = 'role' if myarg == 'rolelist' else 'notrole'
        body[arg] = set()
        roleLocation = Cmd.Location()
        for prole in getString(Cmd.OB_PERMISSION_ROLE_LIST).lower().replace(',', ' ').split():
          if prole in DRIVEFILE_ACL_ROLES_MAP:
            body[arg].add(DRIVEFILE_ACL_ROLES_MAP[prole])
          else:
            invalidChoiceExit(prole, DRIVEFILE_ACL_ROLES_MAP, True)
        self.permissionFields.add('role')
      elif myarg == 'emailaddress':
        body['emailAddress'] = getREPattern(re.IGNORECASE)
        self.permissionFields.add('emailAddress')
      elif myarg == 'emailaddresslist':
        body[myarg] = set(getString(Cmd.OB_EMAIL_ADDRESS_LIST).replace(',', ' ').lower().split())
        self.permissionFields.add('emailAddress')
      elif myarg == 'permissionidlist':
        body[myarg] = set(getString(Cmd.OB_PERMISSION_ID_LIST).replace(',', ' ').split())
        self.permissionFields.add('id')
      elif myarg in {'domain', 'notdomain'}:
        body[myarg] = getREPattern(re.IGNORECASE)
        self.permissionFields.add('domain')
        self.permissionFields.add('emailAddress')
      elif myarg in {'domainlist', 'notdomainlist'}:
        body[myarg] = set(getString(Cmd.OB_DOMAIN_NAME_LIST).replace(',', ' ').lower().split())
        self.permissionFields.add('domain')
        self.permissionFields.add('emailAddress')
      elif myarg == 'withlink':
        withLinkLocation = Cmd.Location()
        body['allowFileDiscovery'] = not getBoolean()
        self.permissionFields.add('allowFileDiscovery')
      elif myarg in {'allowfilediscovery', 'discoverable'}:
        withLinkLocation = Cmd.Location()
        body['allowFileDiscovery'] = getBoolean()
        self.permissionFields.add('allowFileDiscovery')
      elif myarg in {'name', 'displayname'}:
        body['displayName'] = getREPattern(re.IGNORECASE)
        self.permissionFields.add('displayName')
      elif myarg == 'expirationstart':
        expirationStartLocation = Cmd.Location()
        startEndTime.Get(myarg)
        body[myarg] = startEndTime.startDateTime
        self.permissionFields.add('expirationTime')
      elif myarg == 'expirationend':
        expirationEndLocation = Cmd.Location()
        startEndTime.Get(myarg)
        body[myarg] = startEndTime.endDateTime
        self.permissionFields.add('expirationTime')
      elif myarg == 'deleted':
        deletedLocation = Cmd.Location()
        body[myarg] = getBoolean()
        self.permissionFields.add('deleted')
      elif myarg == 'inherited':
        body[myarg] = getBoolean()
        self.permissionFields.add('permissionDetails')
        self.checkDetails = True
      elif myarg == 'permtype':
        body['permissionType'] = getChoice(DRIVEFILE_ACL_PERMISSION_DETAILS_TYPES)
        self.permissionFields.add('permissionDetails')
        self.checkDetails = True
      elif myarg in {'em', 'endmatch'}:
        break
      else:
        unknownArgumentExit()
    if self.clearDefaultMatch:
      self.permissionMatches = []
      self.clearDefaultMatch = False
    if body:
      if 'type' in body:
        _validatePermissionOwnerType(roleLocation, body)
        _validatePermissionAttributes('allowfilediscovery/withlink', withLinkLocation, body, 'allowFileDiscovery', {'anyone', 'domain'})
        _validatePermissionAttributes('expirationstart', expirationStartLocation, body, 'expirationstart', {'user', 'group'})
        _validatePermissionAttributes('expirationend', expirationEndLocation, body, 'expirationend', {'user', 'group'})
        _validatePermissionAttributes('deleted', deletedLocation, body, 'deleted', {'user', 'group'})
      self.permissionMatches.append((requiredMatch, body))

  def SetDefaultMatch(self, requiredMatch, body):
    self.clearDefaultMatch = True
    self.permissionMatches.append((requiredMatch, body))

  def ProcessArgument(self, myarg):
    if myarg in {'pm', 'permissionmatch'}:
      self.GetMatch()
    elif myarg in {'pma', 'permissionmatchaction'}:
      self.permissionMatchKeep = getChoice(PermissionMatch._PERMISSION_MATCH_ACTION_MAP, mapChoice=True)
    elif myarg in {'pmm', 'permissionmatchmode'}:
      self.permissionMatchOr = getChoice(PermissionMatch._PERMISSION_MATCH_MODE_MAP, mapChoice=True)
    else:
      return False
    return True

  @staticmethod
  def CheckPermissionMatch(permission, permissionMatch):
    match = False
    for field, value in permissionMatch[1].items():
      if field in {'type', 'role'}:
        if permission.get(field, '') not in value:
          break
      elif field == 'nottype':
        if permission.get('type', '') in value:
          break
      elif field == 'notrole':
        if permission.get('role', '') in value:
          break
      elif field in {'allowFileDiscovery', 'deleted'}:
        if value != permission.get(field, False):
          break
      elif field in {'inherited', 'permissionType'}:
        permDetails = permission.pop('permissionDetails', None)
        if permDetails:
          dfltValue = False if field == 'inherited' else ''
          permission['permissionDetails'] = []
          if permission.get('inheritedPermissionsDisabled', False):
            obreak = False
            for permissionDetail in permDetails:
              if permissionDetail.get('inherited', False):
                continue
              permission['permissionDetails'].append(permissionDetail)
              if value != permissionDetail.get(field, dfltValue):
                obreak = True
            if obreak:
              break
          else:
            permission['permissionDetails'].append(permDetails[len(permDetails)-1])
            if value != permDetails[0].get(field, dfltValue):
              break
        else:
          break
      elif field in {'expirationstart', 'expirationend'}:
        if 'expirationTime' in permission:
          expirationDateTime = arrow.get(permission['expirationTime'])
          if field == 'expirationstart':
            if expirationDateTime < value:
              break
          else:
            if expirationDateTime > value:
              break
        else:
          break
      elif field == 'emailaddresslist':
        emailAddress = permission.get('emailAddress')
        if emailAddress:
          if emailAddress.lower() not in value:
            break
        else:
          break
      elif field == 'permissionidlist':
        permissionId = permission.get('id')
        if permissionId:
          if permissionId not in value:
            break
        else:
          break
      elif field not in {'domain', 'notdomain', 'domainlist', 'notdomainlist'}:
        if not value.match(permission.get(field, '')):
          break
      else:
        if 'domain' in permission:
          domain = permission['domain'].lower()
        elif 'emailAddress' in permission and permission['emailAddress']:
          _, domain = splitEmailAddress(permission['emailAddress'].lower())
        else:
          break
        if ((field == 'domain' and not value.match(domain)) or
            (field == 'notdomain' and value.match(domain)) or
            (field == 'domainlist' and domain not in value) or
            (field == 'notdomainlist' and domain in value)):
          break
    else:
      match = True
    return match == permissionMatch[0]

  def GetMatchingPermissions(self, permissions):
    if not self.permissionMatches:
      return permissions
    matchingPermissions = []
    for permission in permissions:
      requiredMatches = 1 if self.permissionMatchOr else len(self.permissionMatches)
      for permissionMatch in self.permissionMatches:
        if self.CheckPermissionMatch(permission, permissionMatch):
          requiredMatches -= 1
          if requiredMatches == 0:
            if self.permissionMatchKeep:
              matchingPermissions.append(permission)
            break
      else:
        if not self.permissionMatchKeep:
          matchingPermissions.append(permission)
    return matchingPermissions

  def CheckPermissionMatches(self, permissions):
    if not self.permissionMatches:
      return True
    requiredMatches = 1 if self.permissionMatchOr else len(self.permissionMatches)
    for permission in permissions:
      for permissionMatch in self.permissionMatches:
        if self.CheckPermissionMatch(permission, permissionMatch):
          requiredMatches -= 1
          if requiredMatches == 0:
            return self.permissionMatchKeep
    return not self.permissionMatchKeep

def noFileSelectFileIdEntity(fileIdEntity):
  return (not fileIdEntity
          or (not fileIdEntity['dict']
              and not fileIdEntity['query']
              and not fileIdEntity['shareddrivefilequery']
              and not fileIdEntity['list']))

SHOW_OWNED_BY_CHOICE_MAP = {'any': None, 'me': True, 'others': False}

class DriveListParameters():
  def __init__(self, myargOptions):
    self.PM = PermissionMatch()
    self.myargOptions = myargOptions
    self.checkLocation = None
    self.excludeTrashed = False
    self.filenameMatchPattern = None
    self.getSharedDriveNames = False
    self.kwargs = {}
    self.fileIdEntity = {}
    self.locationFileIds = []
    self.locationSet = False
    self.maxItems = 0
    self.mimeTypeCheck = MimeTypeCheck()
    self.maximumFileSize = None
    self.minimumFileSize = None
    self.onlySharedDrives = False
    self.queryTimes = {}
    self.showOwnedBy = True
    self.showSharedByMe = None

  SHOW_SHARED_BY_ME_CHOICE_MAP = {'any': None, 'true': True, 'false': False}

  def ProcessArgument(self, myarg, fileIdEntity):
    if myarg == 'maxfiles':
      self.maxItems = getInteger(minVal=0)
    elif myarg == 'maximumfilesize':
      self.maximumFileSize = getInteger(minVal=0)
    elif myarg == 'minimumfilesize':
      self.minimumFileSize = getInteger(minVal=0)
    elif myarg == 'showsharedbyme':
      self.showSharedByMe = getChoice(self.SHOW_SHARED_BY_ME_CHOICE_MAP, mapChoice=True)
    elif myarg == 'filenamematchpattern':
      self.filenameMatchPattern = getREPattern(re.IGNORECASE)
    elif self.PM.ProcessArgument(myarg):
      pass
    elif myarg == 'anyowner':
      self.showOwnedBy = None
      self.UpdateAnyOwnerQuery()
    elif myarg == 'showownedby':
      self.showOwnedBy = getChoice(SHOW_OWNED_BY_CHOICE_MAP, mapChoice=True)
      self.UpdateQueryWithShowOwnedBy()
    elif myarg == 'showmimetype':
      self.mimeTypeCheck.Get()
      if self.myargOptions['mimeTypeInQuery']:
        self.AppendToQuery(self.mimeTypeCheck.AddMimeTypeToQuery(self.fileIdEntity.get('query', '')))
    elif myarg == 'excludetrashed':
      self.excludeTrashed = True
    elif myarg.startswith('querytime'):
      self.queryTimes[myarg] = getTimeOrDeltaFromNow()
    elif noFileSelectFileIdEntity(fileIdEntity):
      if self.myargOptions['allowQuery'] and myarg == 'query':
        self.AppendToQuery(getString(Cmd.OB_QUERY))
      elif self.myargOptions['allowQuery'] and myarg.startswith('query:'):
        self.AppendToQuery(Cmd.Previous().strip()[6:])
      elif self.myargOptions['allowQuery'] and myarg == 'fullquery':
        self.SetQuery(getString(Cmd.OB_QUERY, minLen=0))
      elif self.myargOptions['allowQuery'] and myarg in QUERY_SHORTCUTS_MAP:
        self.UpdateAnyOwnerQuery()
        self.AppendToQuery(QUERY_SHORTCUTS_MAP[myarg])
      elif self.myargOptions['allowChoose'] and myarg == 'choose':
        myarg = checkGetArgument()
        if myarg in DRIVE_BY_NAME_CHOICE_MAP:
          self.SetQuery(DRIVE_BY_NAME_CHOICE_MAP[myarg].format(getEscapedDriveFileName()))
        elif myarg in LOCATION_CHOICE_MAP:
          self.locationSet = True
          self.SetLocation(LOCATION_CHOICE_MAP[myarg])
        elif myarg.find(':') > 0:
          kw, value = myarg.split(':', 1)
          if kw in DRIVE_BY_NAME_CHOICE_MAP:
            self.SetQuery(DRIVE_BY_NAME_CHOICE_MAP[kw].format(escapeDriveFileName(value)))
          else:
            invalidChoiceExit(myarg, list(DRIVE_BY_NAME_CHOICE_MAP), True)
        else:
          invalidChoiceExit(myarg, list(DRIVE_BY_NAME_CHOICE_MAP)+list(LOCATION_CHOICE_MAP), True)
      elif self.myargOptions['allowCorpora'] and myarg == 'corpora':
        corpora = getChoice(CORPORA_CHOICE_MAP)
        self.kwargs['corpora'] = CORPORA_CHOICE_MAP[corpora]
        self.kwargs['includeItemsFromAllDrives'] = self.kwargs['supportsAllDrives'] = True
        self.onlySharedDrives = corpora in {'onlyshareddrives', 'onlyteamdrives'}
        self.getSharedDriveNames = True
        self.UpdateAnyOwnerQuery()
        self.SetLocationFileIDsList(LOCATION_CHOICE_MAP['alldrives' if not self.onlySharedDrives else 'onlyshareddrives'])
      else:
        return False
    else:
      if (myarg == 'query' or
          myarg.startswith('query:') or
          myarg == 'fullquery' or
          myarg in QUERY_SHORTCUTS_MAP or
          myarg in DRIVE_BY_NAME_CHOICE_MAP):
        usageErrorExit(Msg.ARE_MUTUALLY_EXCLUSIVE.format('select', myarg))
      return False
    return True

  def InitDriveIdEntity(self):
    if not self.fileIdEntity:
      self.fileIdEntity = initDriveFileEntity()
      self.fileIdEntity['query'] = ME_IN_OWNERS

  def AppendToQuery(self, query):
    self.InitDriveIdEntity()
    if self.fileIdEntity['query']:
      self.fileIdEntity['query'] += ' and ('+query+')'
    else:
      self.fileIdEntity['query'] = query

  def SetQuery(self, query):
    self.InitDriveIdEntity()
    self.fileIdEntity['query'] = query

  def UpdateAnyOwnerQuery(self):
    self.InitDriveIdEntity()
    self.fileIdEntity['query'] = _updateAnyOwnerQuery(self.fileIdEntity['query'])

  def UpdateQueryWithShowOwnedBy(self):
    self.InitDriveIdEntity()
    if self.showOwnedBy is None:
      self.fileIdEntity['query'] = _updateAnyOwnerQuery(self.fileIdEntity['query'])
    elif not self.showOwnedBy:
      if self.fileIdEntity['query'].find(NOT_ME_IN_OWNERS) >= 0:
        pass
      else:
        self.fileIdEntity['query'] = _stripMeInOwners(self.fileIdEntity['query'])
        if self.fileIdEntity['query']:
          self.fileIdEntity['query'] = NOT_ME_IN_OWNERS_AND+self.fileIdEntity['query']
        else:
          self.fileIdEntity['query'] = NOT_ME_IN_OWNERS
    else:
      if self.fileIdEntity['query'].find(ME_IN_OWNERS) >= 0:
        pass
      else:
        self.fileIdEntity['query'] = _stripNotMeInOwners(self.fileIdEntity['query'])
        if self.fileIdEntity['query']:
          self.fileIdEntity['query'] = ME_IN_OWNERS_AND+self.fileIdEntity['query']
        else:
          self.fileIdEntity['query'] = ME_IN_OWNERS

  def CheckShowOwnedBy(self, fileInfo):
    return self.showOwnedBy is None or fileInfo.get('ownedByMe', self.showOwnedBy) == self.showOwnedBy

  def CheckShowSharedByMe(self, fileInfo):
    return self.showSharedByMe is None or (fileInfo.get('shared', self.showSharedByMe) == self.showSharedByMe and fileInfo.get('ownedByMe', False))

  def SetLocationFileIDsList(self, location):
    self.locationFileIds = location['fileids']
    self.checkLocation = location['location']
    self.InitDriveIdEntity()
    cleanFileIDsList(self.fileIdEntity, self.locationFileIds)

  def SetLocation(self, location):
    self.SetLocationFileIDsList(location)
    if self.checkLocation in {LOCATION_ALL_DRIVES, LOCATION_ONLY_SHARED_DRIVES}:
      self.kwargs = {'corpora': 'allDrives', 'includeItemsFromAllDrives': True, 'supportsAllDrives': True}
      self.showOwnedBy = None
      self.fileIdEntity['query'] = ''
      self.onlySharedDrives = self.checkLocation == LOCATION_ONLY_SHARED_DRIVES
    elif location['setShowOwnedBy']:
      self.showOwnedBy = location['owner']
      if self.showOwnedBy is None:
        self.fileIdEntity['query'] = ''
      elif self.showOwnedBy:
        self.fileIdEntity['query'] = ME_IN_OWNERS
      else:
        self.fileIdEntity['query'] = NOT_ME_IN_OWNERS
    else:
      if self.fileIdEntity['query'].find(NOT_ME_IN_OWNERS) >= 0:
        self.fileIdEntity['query'] = NOT_ME_IN_OWNERS
      elif self.fileIdEntity['query'].find(ME_IN_OWNERS) >= 0:
        self.fileIdEntity['query'] = ME_IN_OWNERS

  def SetShowOwnedBy(self, showOwnedBy):
    self.showOwnedBy = showOwnedBy

  def GetFileIdEntity(self):
    if not self.fileIdEntity:
      self.fileIdEntity = initDriveFileEntity()
      self.fileIdEntity['query'] = ME_IN_OWNERS
    return self.fileIdEntity

  def AddMimeTypeToQuery(self):
    if not self.fileIdEntity:
      self.fileIdEntity = initDriveFileEntity()
    if self.mimeTypeCheck.mimeTypes or self.mimeTypeCheck.category:
      self.fileIdEntity['query'] = self.mimeTypeCheck.AddMimeTypeToQuery(self.fileIdEntity['query'])

  def Finalize(self, fileIdEntity):
    self.fileIdEntity.setdefault('query', '')
    if self.excludeTrashed:
      self.AppendToQuery('trashed=false')
    if self.fileIdEntity['query']:
      for queryTimeName, queryTimeValue in self.queryTimes.items():
        self.fileIdEntity['query'] = self.fileIdEntity['query'].replace(f'#{queryTimeName}#', queryTimeValue)
      self.fileIdEntity['query'] = _mapDrive2QueryToDrive3(self.fileIdEntity['query'])
    if not fileIdEntity.get('shareddrive'):
      if self.fileIdEntity['query']:
        if self.fileIdEntity['query'].find(NOT_ME_IN_OWNERS) >= 0 or (not self.showOwnedBy and self.showOwnedBy is not None):
          if not self.locationFileIds:
            self.SetLocationFileIDsList(LOCATION_CHOICE_MAP['ownedbyothers'])
          self.SetShowOwnedBy(False)
        elif self.fileIdEntity['query'].find(ME_IN_OWNERS) >= 0 or self.showOwnedBy:
          if not self.locationFileIds:
            self.SetLocationFileIDsList(LOCATION_CHOICE_MAP['ownedbyme'])
          self.SetShowOwnedBy(True)
        else:
          if not self.locationFileIds:
            self.SetLocationFileIDsList(LOCATION_CHOICE_MAP['ownedbyany'])
          self.SetShowOwnedBy(None)
      else:
        if not self.locationFileIds:
          self.SetLocationFileIDsList(LOCATION_CHOICE_MAP['ownedbyany'])
        self.SetShowOwnedBy(None)
    else:
      self.UpdateAnyOwnerQuery()
#      if not self.locationFileIds:
#        self.SetLocationFileIDsList(LOCATION_CHOICE_MAP['onlyshareddrives'])
      self.SetShowOwnedBy(None)

  def GetLocationFileIdsFromTree(self, fileTree, fileIdEntity):
    cleanList = []
    for fileId in self.locationFileIds:
      if fileId == ROOT or (fileId in fileTree and fileTree[fileId]['children']):
        cleanList.append(fileId)
    cleanFileIDsList(fileIdEntity, cleanList)

  def CheckExcludeTrashed(self, fileInfo):
    return not self.excludeTrashed or not fileInfo.get('trashed', False)

  def CheckFilenameMatch(self, fileInfo):
    return not self.filenameMatchPattern or self.filenameMatchPattern.match(fileInfo['name'])

  def CheckMimeType(self, fileInfo):
    return self.mimeTypeCheck.Check(fileInfo['mimeType'])

  def CheckFileSize(self, fileInfo, sizeField):
    size = int(fileInfo.get(sizeField, '0'))
    if self.minimumFileSize is not None and size < self.minimumFileSize:
      return False
    if self.maximumFileSize is not None and size > self.maximumFileSize:
      return False
    return True

  def CheckOnlySharedDrives(self, fileInfo):
    return not self.onlySharedDrives or fileInfo.get('driveId') is not None

  def CheckFilePermissionMatches(self, fileInfo):
    return self.PM.CheckPermissionMatches(fileInfo.get('permissions', []))

  def GetFileMatchingPermission(self, fileInfo):
    return self.PM.GetMatchingPermissions(fileInfo.get('permissions', []))

def _getGettingEntity(user, fileIdEntity):
  driveId = fileIdEntity.get('shareddrive', {}).get('driveId', None)
  if not driveId:
    return user
  return f"{user} on {Ent.Singular(Ent.SHAREDDRIVE_ID)}: {driveId}"

OWNED_BY_ME_FIELDS_TITLES = ['ownedByMe']
FILELIST_FIELDS_TITLES = ['id', 'name', 'mimeType', 'parents']
DRIVE_INDEXED_TITLES = ['parents', 'path', 'permissions']
CHECK_LOCATION_FIELDS_TITLES = ['driveId', 'id', 'mimeType', 'ownedByMe', 'parents', 'sharedWithMeTime', 'shared']

FILECOUNT_SUMMARY_NONE = 0
FILECOUNT_SUMMARY_ONLY = -1
FILECOUNT_SUMMARY_PLUS = 1
FILECOUNT_SUMMARY_CHOICE_MAP = {
  'none': FILECOUNT_SUMMARY_NONE,
  'only': FILECOUNT_SUMMARY_ONLY,
  'plus': FILECOUNT_SUMMARY_PLUS
  }
FILECOUNT_SUMMARY_USER = 'Summary'

SIZE_FIELD_CHOICE_MAP = {
  'size': 'size',
  'quotabytesused': 'quotaBytesUsed'
  }

# gam <UserTypeEntity> print filelist [todrive <ToDriveAttribute>*]
#	[((query <QueryDriveFile>) | (fullquery <QueryDriveFile>) | <DriveFileQueryShortcut>) (querytime<String> <Time>)*]
#	[continueoninvalidquery [<Boolean>]]
#	[choose <DriveFileNameEntity>|<DriveFileEntityShortcut>]
#	[corpora <CorporaAttribute>]
#	[select <DriveFileEntity> [selectsubquery <QueryDriveFile>]
#	    [(norecursion [<Boolean>])|(depth <Number>)] [showparent]]
#	[anyowner|(showownedby any|me|others)]
#	[showmimetype [not] <MimeTypeList>] [showmimetype category <MimeTypeNameList>] [mimetypeinquery [<Boolean>]]
#	[sizefield quotabytesused|size] [minimumfilesize <Integer>] [maximumfilesize <Integer>]
#	[filenamematchpattern <REMatchPattern>]
#	<PermissionMatch>* [<PermissionMatchMode>] [<PermissionMatchAction>] [pmfilter] [oneitemperrow]
#	[excludetrashed]
#	[maxfiles <Integer>] [nodataheaders <String>]
#	[countsonly [summary none|only|plus] [summaryuser <String>]
#		    [showsource] [showsize] [showsizeunits] [showmimetypesize]]
#	[countsrowfilter]
#	[filepath|fullpath [folderpathonly|parentpathonly [<Boolean>]] [pathdelimiter <Character>] [addpathstojson] [showdepth]] [buildtree]
#	[allfields|<DriveFieldName>*|(fields <DriveFieldNameList>)]
#	[showdrivename] [showshareddrivepermissions]
#	(showlabels details|ids)|(includelabels <DriveLabelIDList>)]
#	[includepermissionsforview published]
#	[showparentsidsaslist] [showpermissionslast]
#	(orderby <DriveFileOrderByFieldName> [ascending|descending])* [delimiter <Character>]
#	[stripcrsfromname]
#	(addcsvdata <FieldName> <String>)* [includecsvdatainjson [<Boolean>]]
#	[formatjson [quotechar <Character>]]
