"""Shared drive management, ownership, organizers.

Part of the drive sub-package, extracted from drive.py."""

"""GAM Google Drive file, permission, shared drive, and label management."""

import re
import json
import sys

from gam.cmd.drive.core import _convertSharedDriveNameToId, _getSharedDriveNameFromId
from gam.cmd.drive.filepaths import _mapDrivePermissionNames
from gam.cmd.drive.files import _initStatistics
from gam.cmd.drive.permissions import _getDriveFileACLPrintKeysTimeObjects, _showDriveFilePermissionJSON, _showDriveFilePermissions, _showDriveFilePermissionsJSON, getDriveFilePermissionsFields
import uuid
import time

from gam.cmd.drive.core import getSharedDriveEntity, _validateUserSharedDrive

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

def doPrintShowOwnership():
  rep = _getMain().buildGAPIObject(API.REPORTS)
  customerId = GC.Values[GC.CUSTOMER_ID]
  if customerId == GC.MY_CUSTOMER:
    customerId = None
  csvPF = _getMain().CSVPrintFile('Owner') if Act.csvFormat() else None
  FJQC = _getMain().FormatJSONQuoteChar(csvPF)
  addCSVData = {}
  showComplete = False
  entityType = Ent.DRIVE_FILE_OR_FOLDER_ID
  myarg = _getMain().getString(Cmd.OB_DRIVE_FILE_ID, checkBlank=True)
  mycmd = myarg.lower().replace('_', '').replace('-', '')
  if mycmd == 'id':
    fileId = _getMain().getString(Cmd.OB_DRIVE_FILE_ID, checkBlank=True)
  elif mycmd == 'drivefilename':
    entityType = Ent.DRIVE_FILE_OR_FOLDER
    fileId = _getMain().getString(Cmd.OB_DRIVE_FILE_NAME, checkBlank=True)
  elif mycmd.find(':') != -1:
    kw, fileId = myarg.split(':', 1)
    kw = kw.lower().replace('_', '').replace('-', '')
    if fileId.isspace():
      Cmd.Backup()
      _getMain().blankArgumentExit(Cmd.OB_DRIVE_FILE_ID)
    if kw == 'id':
      pass
    elif kw == 'drivefilename':
      entityType = Ent.DRIVE_FILE_OR_FOLDER
    else:
      Cmd.Backup()
      _getMain().invalidArgumentExit(Cmd.OB_DRIVE_FILE_ID)
  else:
    fileId = myarg
  if not fileId:
    Cmd.Backup()
    _getMain().invalidArgumentExit(Cmd.OB_DRIVE_FILE_ID)
  if entityType == Ent.DRIVE_FILE_OR_FOLDER_ID:
    filters = f'doc_id=={fileId}'
  else:
    filters = f'doc_title=={fileId}'
  while Cmd.ArgumentsRemaining():
    myarg = _getMain().getArgument()
    if csvPF and myarg == 'todrive':
      csvPF.GetTodriveParameters()
    elif csvPF and myarg == 'addcsvdata':
      _getMain().getAddCSVData(addCSVData)
    else:
      FJQC.GetFormatJSONQuoteChar(myarg, True)
  if csvPF and not FJQC.formatJSON:
    csvPF.AddTitles(['id', 'name', 'type', 'ownerIsSharedDrive', 'driveId', 'event'])
    if addCSVData:
      csvPF.AddTitles(sorted(addCSVData.keys()))
    csvPF.SetSortAllTitles()
  foundIds = {}
  try:
    feed = _getMain().callGAPIpages(rep.activities(), 'list', 'items',
                         throwReasons=[GAPI.BAD_REQUEST, GAPI.INVALID, GAPI.AUTH_ERROR],
                         applicationName='drive', userKey='all', customerId=customerId,
                         filters=filters, fields='nextPageToken,items(events(name,parameters))')
  except GAPI.badRequest:
    _getMain().systemErrorExit(_getMain().BAD_REQUEST_RC, Msg.BAD_REQUEST)
  except GAPI.invalid as e:
    _getMain().systemErrorExit(_getMain().GOOGLE_API_ERROR_RC, str(e))
  except GAPI.authError:
    accessErrorExit(None)
  for activity in feed:
    events = activity.pop('events')
    for event in events:
      fileInfo = {'event': event['name']}
      for item in event.get('parameters', []):
        if item['name'] == 'primary_event':
          if not item['boolValue']:
            break
        elif item['name'] == 'doc_id':
          if item['value'] in foundIds:
            break
          fileInfo['id'] = item['value']
        elif event['name'] == 'change_owner' and item['name'] == 'new_owner':
          fileInfo['Owner'] = item['value']
        elif event['name'] != 'change_owner' and item['name'] == 'owner':
          fileInfo['Owner'] = item['value']
        elif item['name'] == 'doc_title':
          fileInfo['name'] = item['value']
        elif item['name'] == 'doc_type':
          fileInfo['type'] = item['value']
        elif item['name'] == 'owner_is_shared_drive':
          fileInfo['ownerIsSharedDrive'] = item['boolValue']
        elif item['name'] == 'shared_drive_id':
          fileInfo['driveId'] = item['value']
      else:
        if 'Owner' in fileInfo and 'id' in fileInfo:
          foundIds[fileInfo['id']] = True
          if not csvPF:
            if not FJQC.formatJSON:
              _getMain().printEntityKVList([Ent.OWNER, fileInfo['Owner']],
                                ['id', fileInfo['id'], 'name', fileInfo.get('name', ''),
                                 'type', fileInfo.get('type', ''),
                                 'ownerIsSharedDrive', fileInfo.get('ownerIsSharedDrive', False),
                                 'driveId', fileInfo.get('driveId', ''),
                                 'event', fileInfo['event']])
            else:
              _getMain().printLine(json.dumps(_getMain().cleanJSON(fileInfo), ensure_ascii=False, sort_keys=True))
          else:
            if addCSVData:
              fileInfo.update(addCSVData)
            row = _getMain().flattenJSON(fileInfo)
            if not FJQC.formatJSON:
              csvPF.WriteRowTitles(row)
            elif csvPF.CheckRowTitles(row):
              csvPF.WriteRowNoFilter({'JSON': json.dumps(_getMain().cleanJSON(fileInfo), ensure_ascii=False, sort_keys=True)})
          if entityType == Ent.DRIVE_FILE_OR_FOLDER_ID:
            showComplete = True
            break
      if showComplete:
        break
    if showComplete:
      break
  if not foundIds:
    _getMain().entityActionFailedWarning([entityType, fileId], Msg.NOT_FOUND)
  if csvPF:
    csvPF.writeCSVfile('Drive File Ownership')

def _getSharedDriveTheme(myarg, body):
  if myarg in {'theme', 'themeid'}:
    body.pop('backgroundImageFile', None)
    body.pop('colorRgb', None)
    body['themeId'] = _getMain().getString(Cmd.OB_STRING, checkBlank=True)
  elif myarg == 'customtheme':
    body.pop('themeId', None)
    body['backgroundImageFile'] = {
      'id': _getMain().getString(Cmd.OB_DRIVE_FILE_ID, checkBlank=True),
      'xCoordinate': _getMain().getFloat(minVal=0.0, maxVal=1.0),
      'yCoordinate': _getMain().getFloat(minVal=0.0, maxVal=1.0),
      'width': _getMain().getFloat(minVal=0.0, maxVal=1.0)
      }
  elif myarg in {'color', 'colour'}:
    body.pop('themeId', None)
    body['colorRgb'] = _getMain().getColor()
  else:
    return False
  return True

SHAREDDRIVE_RESTRICTIONS_MAP = {
  'adminmanagedrestrictions': 'adminManagedRestrictions',
  'allowcontentmanagerstosharefolders': 'sharingFoldersRequiresOrganizerPermission',
  'copyrequireswriterpermission': 'copyRequiresWriterPermission',
  'domainusersonly': 'domainUsersOnly',
  'downloadrestrictedforreaders': 'restrictedForReaders',
  'downloadrestrictedforwriters': 'restrictedForWriters',
  'drivemembersonly': 'driveMembersOnly',
  'sharingfoldersrequiresorganizerpermission': 'sharingFoldersRequiresOrganizerPermission',
  'teammembersonly': 'driveMembersOnly',
  }
SHAREDDRIVE_DOWNLOAD_RESTRICTIONS_MAP = {
  'restrictedforreaders': 'downloadrestrictedforreaders',
  'restrictedforwriters': 'downloadrestrictedforwriters',
  }

def _getSharedDriveRestrictions(myarg, body):
  def _setRestriction(restriction):
    body.setdefault('restrictions', {})
    if restriction in {'downloadrestrictedforreaders', 'downloadrestrictedforwriters'}:
      body['restrictions'].setdefault('downloadRestriction', {})
      body['restrictions']['downloadRestriction'][SHAREDDRIVE_RESTRICTIONS_MAP[restriction]] = _getMain().getBoolean()
    elif restriction != 'allowcontentmanagerstosharefolders':
      body['restrictions'][SHAREDDRIVE_RESTRICTIONS_MAP[restriction]] = _getMain().getBoolean()
    else:
      body['restrictions'][SHAREDDRIVE_RESTRICTIONS_MAP[restriction]] = not _getMain().getBoolean()

  if myarg.startswith('restrictions.'):
    _, subField = myarg.split('.', 1)
    if subField.startswith('downloadrestrictions.'):
      _, subField = subField.split('.', 1)
      if subField in SHAREDDRIVE_DOWNLOAD_RESTRICTIONS_MAP:
        _setRestriction(SHAREDDRIVE_DOWNLOAD_RESTRICTIONS_MAP[subField])
        return True
    elif subField in SHAREDDRIVE_RESTRICTIONS_MAP:
      _setRestriction(subField)
      return True
    _getMain().invalidChoiceExit(subField, SHAREDDRIVE_RESTRICTIONS_MAP, True)
  if myarg in SHAREDDRIVE_RESTRICTIONS_MAP:
    _setRestriction(myarg)
    return True
  return False

def _checkSharedDriveRestrictions(body):
  if 'restrictions' in body and 'copyRequiresWriterPermission' in body['restrictions'] and 'downloadRestriction' in body['restrictions']:
    _getMain().usageErrorExit(Msg.ARE_MUTUALLY_EXCLUSIVE.format('copyrequireswriterpermission', 'downloadrestrictedforreaders|downloadrestrictedforwriters'))

def _moveSharedDriveToOU(orgUnit, orgUnitId, driveId, user, i, count, ci, returnIdOnly):
  action = Act.Get()
  name = f'orgUnits/-/memberships/shared_drive;{driveId}'
  if ci is None:
    ci = _getMain().buildGAPIObject(API.CLOUDIDENTITY_ORGUNITS_BETA)
  cibody = {'customer': _getMain()._getCustomersCustomerIdWithC(),
            'destinationOrgUnit': f'orgUnits/{orgUnitId[3:]}'}
  try:
    _getMain().callGAPI(ci.orgUnits().memberships(), 'move',
             throwReasons=GAPI.DRIVE_USER_THROW_REASONS+[GAPI.NOT_FOUND, GAPI.FORBIDDEN,
                                                         GAPI.INVALID_ARGUMENT, GAPI.ABORTED],
             name=name, body=cibody)
    if not returnIdOnly:
      Act.Set(Act.MOVE)
      _getMain().entityModifierNewValueActionPerformed([Ent.USER, user, Ent.SHAREDDRIVE, driveId], Act.MODIFIER_TO,
                                            f'{Ent.Singular(Ent.ORGANIZATIONAL_UNIT)}: {orgUnit}', i, count)
  except (GAPI.notFound, GAPI.forbidden, GAPI.aborted, GAPI.badRequest, GAPI.internalError,
          GAPI.noManageTeamDriveAdministratorPrivilege, GAPI.invalidArgument) as e:
    _getMain().entityActionFailedWarning([Ent.USER, user, Ent.SHAREDDRIVE_ID, driveId], str(e), i, count)
  except (GAPI.serviceNotAvailable, GAPI.authError, GAPI.domainPolicy) as e:
    _getMain().userDriveServiceNotEnabledWarning(user, str(e), i, count)
  Act.Set(action)
  return ci

# gam <UserTypeEntity> create shareddrive <Name> [asadmin]
#	[(theme|themeid <String>) | ([customtheme <DriveFileID> <Float> <Float> <Float>] [color <ColorValue>])]
#	(<SharedDriveRestrictionsFieldName> <Boolean>)*
#	[hide|hidden <Boolean>] [ou|org|orgunit <OrgUnitItem>]
#	[errorretries <Integer>] [updateinitialdelay <Integer>] [updateretrydelay <Integer>]
#	[movetoorgunitdelay <Integer>]
#	[(csv [todrive <ToDriveAttribute>*] (addcsvdata <FieldName> <String>)*) | returnidonly]
def createSharedDrive(users, useDomainAdminAccess=False):
  def waitingForCreationToComplete(sleep_time):
    _getMain().writeStderr(Ind.Spaces()+Msg.WAITING_FOR_ITEM_CREATION_TO_COMPLETE_SLEEPING.format(Ent.Singular(Ent.SHAREDDRIVE), sleep_time))
    time.sleep(sleep_time)

  requestId = str(uuid.uuid4())
  body = {'name': _getMain().getString(Cmd.OB_NAME, checkBlank=True)}
  updateBody = {}
  csvPF = None
  addCSVData = {}
  hide = returnIdOnly = False
  orgUnit = orgUnitId = ci = None
  errorRetries = 5
  updateInitialDelay = 10
  updateRetryDelay = 10
  moveToOrgUnitDelay = 20
  while Cmd.ArgumentsRemaining():
    myarg = _getMain().getArgument()
    if _getSharedDriveTheme(myarg, body):
      pass
    elif _getSharedDriveRestrictions(myarg, updateBody):
      pass
    elif myarg in {'hide', 'hidden'}:
      hide = _getMain().getBoolean()
    elif myarg in {'ou', 'org', 'orgunit'}:
      orgUnit, orgUnitId = _getMain().getOrgUnitId()
    elif myarg == 'returnidonly':
      returnIdOnly = True
    elif myarg == 'csv':
      csvPF = _getMain().CSVPrintFile()
    elif csvPF and myarg == 'todrive':
      csvPF.GetTodriveParameters()
    elif csvPF and myarg == 'addcsvdata':
      _getMain().getAddCSVData(addCSVData)
    elif myarg in _getMain().ADMIN_ACCESS_OPTIONS:
      useDomainAdminAccess = True
    elif myarg == 'errorretries':
      errorRetries = _getMain().getInteger(minVal=0, maxVal=10)
    elif myarg == 'updateinitialdelay':
      updateInitialDelay = _getMain().getInteger(minVal=0, maxVal=60)
    elif myarg == 'updateretrydelay':
      updateRetryDelay = _getMain().getInteger(minVal=0, maxVal=60)
    elif myarg == 'movetoorgunitdelay':
      moveToOrgUnitDelay = _getMain().getInteger(minVal=0, maxVal=60)
    else:
      _getMain().unknownArgumentExit()
  _checkSharedDriveRestrictions(body)
  if csvPF:
    csvPF.SetTitles(['User', 'name', 'id'])
    if addCSVData:
      csvPF.AddTitles(sorted(addCSVData.keys()))
  for field in ['backgroundImageFile', 'colorRgb']:
    if field in body:
      updateBody[field] = body.pop(field)
  i, count, users = _getMain().getEntityArgument(users)
  for user in users:
    i += 1
    user, drive = _getMain().buildGAPIServiceObject(API.DRIVE3, user, i, count)
    if not drive:
      continue
    doUpdate = False
    Act.Set(Act.CREATE)
    retry = 0
    while True:
      try:
        shareddrive = _getMain().callGAPI(drive.drives(), 'create',
                               bailOnTransientError=True,
                               throwReasons=GAPI.DRIVE_USER_THROW_REASONS+[GAPI.TRANSIENT_ERROR, GAPI.TEAMDRIVE_ALREADY_EXISTS,
                                                                           GAPI.INSUFFICIENT_PERMISSIONS, GAPI.INSUFFICIENT_FILE_PERMISSIONS,
                                                                           GAPI.DUPLICATE, GAPI.BAD_REQUEST, GAPI.USER_CANNOT_CREATE_TEAMDRIVES],
                               requestId=requestId, body=body, fields='id')
        driveId = shareddrive['id']
        if returnIdOnly:
          _getMain().writeStdout(f'{driveId}\n')
        elif not csvPF:
          _getMain().entityActionPerformed([Ent.USER, user, Ent.SHAREDDRIVE_NAME, body['name'], Ent.SHAREDDRIVE_ID, driveId], i, count)
        else:
          row = {'User': user, 'name': body['name'], 'id': driveId}
          if addCSVData:
            row.update(addCSVData)
          csvPF.WriteRow(row)
        doUpdate = True
        break
      except (GAPI.transientError, GAPI.teamDriveAlreadyExists) as e:
        retry += 1
        if retry > errorRetries:
          _getMain().entityActionFailedWarning([Ent.USER, user, Ent.REQUEST_ID, requestId], str(e), i, count)
          break
        requestId = str(uuid.uuid4())
      except GAPI.duplicate:
        _getMain().entityActionFailedWarning([Ent.USER, user, Ent.REQUEST_ID, requestId], Msg.DUPLICATE, i, count)
        break
      except (GAPI.insufficientPermissions, GAPI.insufficientFilePermissions, GAPI.badRequest, GAPI.userCannotCreateTeamDrives) as e:
        _getMain().entityActionFailedWarning([Ent.USER, user, Ent.REQUEST_ID, requestId], str(e), i, count)
        break
      except (GAPI.serviceNotAvailable, GAPI.authError, GAPI.domainPolicy) as e:
        _getMain().userDriveServiceNotEnabledWarning(user, str(e), i, count)
        break
    if not (doUpdate or updateBody or hide or orgUnit):
      continue
    waitingForCreationToComplete(updateInitialDelay)
    created = False
    retry = 0
    while not created:
      try:
        _getMain().callGAPI(drive.drives(), 'get',
                 throwReasons=GAPI.DRIVE_USER_THROW_REASONS+[GAPI.FILE_NOT_FOUND, GAPI.NOT_FOUND],
                 useDomainAdminAccess=useDomainAdminAccess,
                 driveId=driveId, fields='id')
        created = True
        break
      except (GAPI.fileNotFound, GAPI.notFound) as e:
        retry += 1
        if retry > errorRetries:
          _getMain().entityActionFailedWarning([Ent.USER, user, Ent.SHAREDDRIVE_ID, driveId], str(e), i, count)
          break
        waitingForCreationToComplete(updateRetryDelay)
    if not created:
      continue
    try:
      if updateBody:
        Act.Set(Act.UPDATE)
        try:
          _getMain().callGAPI(drive.drives(), 'update',
                   bailOnInternalError=True,
                   throwReasons=GAPI.DRIVE_USER_THROW_REASONS+[GAPI.NOT_FOUND, GAPI.FORBIDDEN,
                                                               GAPI.NO_MANAGE_TEAMDRIVE_ADMINISTRATOR_PRIVILEGE,
                                                               GAPI.OUTSIDE_DOMAIN_MEMBER_CANNOT_CHANGE_TEAMDRIVE_RESTRICTIONS,
                                                               GAPI.BAD_REQUEST, GAPI.INTERNAL_ERROR, GAPI.PERMISSION_DENIED,
                                                               GAPI.FILE_NOT_FOUND],
                   useDomainAdminAccess=useDomainAdminAccess, driveId=driveId, body=updateBody)
          if not returnIdOnly and not csvPF:
            _getMain().entityActionPerformed([Ent.USER, user, Ent.SHAREDDRIVE_ID, driveId], i, count)
        except GAPI.fileNotFound as e:
          _getMain().entityActionFailedWarning([Ent.USER, user, Ent.SHAREDDRIVE_ID, driveId,
                                     Ent.DRIVE_FILE, body.get('backgroundImageFile', {}).get('id', _getMain().UNKNOWN)],
                                    str(e), i, count)
      if hide:
        Act.Set(Act.HIDE)
        _getMain().callGAPI(drive.drives(), 'hide',
                 throwReasons=GAPI.DRIVE_USER_THROW_REASONS+[GAPI.NOT_FOUND, GAPI.FORBIDDEN],
                 driveId=driveId)
        if not returnIdOnly and not csvPF:
          _getMain().entityActionPerformed([Ent.USER, user, Ent.SHAREDDRIVE_ID, driveId], i, count)
      if orgUnit:
        waitingForCreationToComplete(moveToOrgUnitDelay)
        ci = _moveSharedDriveToOU(orgUnit, orgUnitId, driveId, user, i, count, ci, returnIdOnly or csvPF)
    except (GAPI.notFound, GAPI.forbidden, GAPI.badRequest,
            GAPI.noManageTeamDriveAdministratorPrivilege, GAPI.outsideDomainMemberCannotChangeTeamDriveRestrictions) as e:
      _getMain().entityActionFailedWarning([Ent.USER, user, Ent.SHAREDDRIVE_ID, driveId], str(e), i, count)
    except (GAPI.serviceNotAvailable, GAPI.authError, GAPI.domainPolicy) as e:
      _getMain().userDriveServiceNotEnabledWarning(user, str(e), i, count)
  if csvPF:
    csvPF.writeCSVfile('SharedDrives')

# gam create shareddrive <Name>
#	[(theme|themeid <String>) | ([customtheme <DriveFileID> <Float> <Float> <Float>] [color <ColorValue>])]
#	(<SharedDriveRestrictionsFieldName> <Boolean>)*
#	[hide|hidden <Boolean>]
#	[errorretries <Integer>] [updateinitialdelay <Integer>] [updateretrydelay <Integer>]
#	[movetoorgunitdelay <Integer>]
#	[(csv [todrive <ToDriveAttribute>*] (addcsvdata <FieldName> <String>)*) | returnidonly]
def doCreateSharedDrive():
  createSharedDrive([_getMain()._getAdminEmail()], True)

# gam <UserTypeEntity> update shareddrive <SharedDriveEntity> [asadmin] [name <Name>]
#	[(theme|themeid <String>) | ([customtheme <DriveFileID> <Float> <Float> <Float>] [color <ColorValue>])]
#	(<SharedDriveRestrictionsFieldName> <Boolean>)*
#	[hide|hidden <Boolean>] [ou|org|orgunit <OrgUnitItem>]
def updateSharedDrive(users, useDomainAdminAccess=False):
  fileIdEntity = getSharedDriveEntity()
  body = {}
  hide = None
  orgUnit = orgUnitId = ci = None
  while Cmd.ArgumentsRemaining():
    myarg = _getMain().getArgument()
    if myarg == 'name':
      body['name'] = _getMain().getString(Cmd.OB_NAME, checkBlank=True)
    elif myarg in {'ou', 'org', 'orgunit'}:
      orgUnit, orgUnitId = _getMain().getOrgUnitId()
    elif _getSharedDriveTheme(myarg, body):
      pass
    elif _getSharedDriveRestrictions(myarg, body):
      pass
    elif myarg in {'hide', 'hidden'}:
      hide = _getMain().getBoolean()
    elif myarg in _getMain().ADMIN_ACCESS_OPTIONS:
      useDomainAdminAccess = True
    else:
      _getMain().unknownArgumentExit()
  _checkSharedDriveRestrictions(body)
  i, count, users = _getMain().getEntityArgument(users)
  for user in users:
    i += 1
    user, drive = _validateUserSharedDrive(user, i, count, fileIdEntity, useDomainAdminAccess=useDomainAdminAccess)
    if not drive:
      continue
    try:
      driveId = fileIdEntity['shareddrive']['driveId']
      if body:
        result = _getMain().callGAPI(drive.drives(), 'update',
                          bailOnInternalError=True,
                          throwReasons=GAPI.DRIVE_USER_THROW_REASONS+[GAPI.NOT_FOUND, GAPI.FORBIDDEN, GAPI.BAD_REQUEST,
                                                                      GAPI.NO_MANAGE_TEAMDRIVE_ADMINISTRATOR_PRIVILEGE,
                                                                      GAPI.OUTSIDE_DOMAIN_MEMBER_CANNOT_CHANGE_TEAMDRIVE_RESTRICTIONS,
                                                                      GAPI.INTERNAL_ERROR, GAPI.FILE_NOT_FOUND],
                          useDomainAdminAccess=useDomainAdminAccess, driveId=driveId, body=body, fields='name')
        _getMain().entityActionPerformed([Ent.USER, user, Ent.SHAREDDRIVE_NAME, result['name'], Ent.SHAREDDRIVE_ID, driveId], i, count)
      if hide is not None:
        if hide:
          Act.Set(Act.HIDE)
          function = 'hide'
        else:
          Act.Set(Act.UNHIDE)
          function = 'unhide'
        _getMain().callGAPI(drive.drives(), function,
                 throwReasons=GAPI.DRIVE_USER_THROW_REASONS+[GAPI.NOT_FOUND, GAPI.FORBIDDEN],
                 driveId=driveId)
        _getMain().entityActionPerformed([Ent.USER, user, Ent.SHAREDDRIVE_ID, driveId], i, count)
      if orgUnit:
        ci = _moveSharedDriveToOU(orgUnit, orgUnitId, driveId, user, i, count, ci, False)
    except (GAPI.notFound, GAPI.forbidden, GAPI.badRequest, GAPI.internalError,
            GAPI.noManageTeamDriveAdministratorPrivilege, GAPI.outsideDomainMemberCannotChangeTeamDriveRestrictions) as e:
      _getMain().entityActionFailedWarning([Ent.USER, user, Ent.SHAREDDRIVE_ID, driveId], str(e), i, count)
    except GAPI.fileNotFound as e:
      _getMain().entityActionFailedWarning([Ent.USER, user, Ent.SHAREDDRIVE_ID, driveId,
                                 Ent.DRIVE_FILE, body.get('backgroundImageFile', {}).get('id', _getMain().UNKNOWN)],
                                str(e), i, count)
    except (GAPI.serviceNotAvailable, GAPI.authError, GAPI.domainPolicy) as e:
      _getMain().userDriveServiceNotEnabledWarning(user, str(e), i, count)
    Act.Set(Act.UPDATE)

def doUpdateSharedDrive():
  updateSharedDrive([_getMain()._getAdminEmail()], True)

# gam <UserTypeEntity> delete shareddrive <SharedDriveEntity>
#	[asadmin [allowitemdeletion]
def deleteSharedDrive(users):
  fileIdEntity = getSharedDriveEntity()
  allowItemDeletion = useDomainAdminAccess = False
  while Cmd.ArgumentsRemaining():
    myarg = _getMain().getArgument()
    if myarg in {'nukefromorbit', 'allowitemdeletion'}:
      allowItemDeletion = useDomainAdminAccess = True
    elif myarg in _getMain().ADMIN_ACCESS_OPTIONS:
      useDomainAdminAccess = True
    else:
      _getMain().unknownArgumentExit()
  i, count, users = _getMain().getEntityArgument(users)
  for user in users:
    i += 1
    user, drive = _validateUserSharedDrive(user, i, count, fileIdEntity)
    if not drive:
      continue
    try:
      driveId = fileIdEntity['shareddrive']['driveId']
      _getMain().callGAPI(drive.drives(), 'delete',
               throwReasons=GAPI.DRIVE_USER_THROW_REASONS+[GAPI.NOT_FOUND, GAPI.FORBIDDEN,
                                                           GAPI.CANNOT_DELETE_RESOURCE_WITH_CHILDREN, GAPI.INSUFFICIENT_FILE_PERMISSIONS,
                                                           GAPI.NO_MANAGE_TEAMDRIVE_ADMINISTRATOR_PRIVILEGE],
               driveId=driveId, allowItemDeletion=allowItemDeletion, useDomainAdminAccess=useDomainAdminAccess)
      _getMain().entityActionPerformed([Ent.USER, user, Ent.SHAREDDRIVE_ID, driveId], i, count)
    except (GAPI.notFound, GAPI.forbidden,
            GAPI.cannotDeleteResourceWithChildren, GAPI.insufficientFilePermissions,
            GAPI.noManageTeamDriveAdministratorPrivilege) as e:
      _getMain().entityActionFailedWarning([Ent.USER, user, Ent.SHAREDDRIVE_ID, driveId], str(e), i, count)
    except (GAPI.serviceNotAvailable, GAPI.authError, GAPI.domainPolicy) as e:
      _getMain().userDriveServiceNotEnabledWarning(user, str(e), i, count)

# gam delete shareddrive <SharedDriveEntity> [allowitemdeletion]
def doDeleteSharedDrive():
  deleteSharedDrive([_getMain()._getAdminEmail()])

# gam <UserTypeEntity> hide/unhide shareddrive <SharedDriveEntity>
def hideUnhideSharedDrive(users):
  fileIdEntity = getSharedDriveEntity()
  _getMain().checkForExtraneousArguments()
  function = 'hide' if Act.Get() == Act.HIDE else 'unhide'
  i, count, users = _getMain().getEntityArgument(users)
  for user in users:
    i += 1
    user, drive = _validateUserSharedDrive(user, i, count, fileIdEntity)
    if not drive:
      continue
    try:
      driveId = fileIdEntity['shareddrive']['driveId']
      _getMain().callGAPI(drive.drives(), function,
               throwReasons=GAPI.DRIVE_USER_THROW_REASONS+[GAPI.NOT_FOUND, GAPI.FORBIDDEN],
               driveId=driveId)
      _getMain().entityActionPerformed([Ent.USER, user, Ent.SHAREDDRIVE_ID, driveId], i, count)
    except (GAPI.notFound, GAPI.forbidden) as e:
      _getMain().entityActionFailedWarning([Ent.USER, user, Ent.SHAREDDRIVE_ID, driveId], str(e), i, count)
    except (GAPI.serviceNotAvailable, GAPI.authError, GAPI.domainPolicy) as e:
      _getMain().userDriveServiceNotEnabledWarning(user, str(e), i, count)

# gam hide/unhide shareddrive <SharedDriveEntity>
def doHideUnhideSharedDrive():
  hideUnhideSharedDrive([_getMain()._getAdminEmail()])

SHAREDDRIVE_FIELDS_CHOICE_MAP = {
  'backgroundimagefile': 'backgroundImageFile',
  'backgroundimagelink': 'backgroundImageLink',
  'capabilities': 'capabilities',
  'colorrgb': 'colorRgb',
  'createddate': 'createdTime',
  'createdtime': 'createdTime',
  'id': 'id',
  'hidden': 'hidden',
  'name': 'name',
  'restrictions': 'restrictions',
  'themeid': 'themeId',
  }
SHAREDDRIVE_LIST_FIELDS_CHOICE_MAP = {
  'org': 'orgUnitId',
  'orgunit': 'orgUnitId',
  'orgunitid': 'orgUnitId',
  'ou': 'orgUnitId',
  }
SHAREDDRIVE_TIME_OBJECTS = {'createdTime'}
SHAREDDRIVE_ROLES_CAPABILITIES_MAP = {
  'commenter': {'canComment': True, 'canEdit': False},
  'reader': {'canComment': False, 'canEdit': False},
  'writer': {'canEdit': True, 'canTrashChildren': False},
  'fileOrganizer': {'canTrashChildren': True, 'canManageMembers': False},
  'organizer': {'canManageMembers': True},
  }
SHAREDDRIVE_API_GUI_ROLES_MAP = {
  'commenter': 'Commenter',
  'fileOrganizer': 'Content manager',
  'organizer': 'Manager',
  'reader': 'Viewer',
  'writer': 'Contributor',
  'unknown': 'Unknown'
  }

def _getSharedDriveRole(shareddrive):
  if 'capabilities' not in shareddrive:
    return None
  for role, capabilities in SHAREDDRIVE_ROLES_CAPABILITIES_MAP.items():
    match = True
    for capability in capabilities:
      if capabilities[capability] != shareddrive['capabilities'].get(capability, ''):
        match = False
        break
    if match:
      break
  else:
    role = 'unknown'
  return role

def _showSharedDrive(user, shareddrive, j, jcount, FJQC):
  if FJQC.formatJSON:
    _getMain().printLine(json.dumps(_getMain().cleanJSON(shareddrive, timeObjects=SHAREDDRIVE_TIME_OBJECTS), ensure_ascii=False, sort_keys=True))
    return
  _getMain().printEntity([Ent.USER, user, Ent.SHAREDDRIVE, f'{shareddrive["name"]} ({shareddrive["id"]})'], j, jcount)
  Ind.Increment()
  _getMain().printEntity([Ent.SHAREDDRIVE_ID, shareddrive['id']])
  _getMain().printEntity([Ent.SHAREDDRIVE_NAME, shareddrive['name']])
  if 'hidden' in shareddrive:
    _getMain().printKeyValueList(['hidden', shareddrive['hidden']])
  if 'createdTime' in shareddrive:
    _getMain().printKeyValueList(['createdTime', formatLocalTime(shareddrive['createdTime'])])
  for setting in ['backgroundImageLink', 'colorRgb', 'themeId', 'orgUnit', 'orgUnitId', 'webViewLink']:
    if setting in shareddrive:
      _getMain().printKeyValueList([setting, shareddrive[setting]])
  if 'role' in shareddrive:
    _getMain().printKeyValueList(['role', shareddrive['role']])
  for setting in ['capabilities', 'restrictions']:
    if setting in shareddrive:
      _getMain().showJSON(setting, shareddrive[setting])
  Ind.Decrement()

# gam <UserTypeEntity> info shareddrive <SharedDriveEntity>
#	[asadmin]
#	[fields <SharedDriveFieldNameList>]
#	[guiroles [<Boolean>]] [formatjson]
def infoSharedDrive(users, useDomainAdminAccess=False):
  fileIdEntity = getSharedDriveEntity()
  fieldsList = []
  FJQC = _getMain().FormatJSONQuoteChar()
  guiRoles = False
  while Cmd.ArgumentsRemaining():
    myarg = _getMain().getArgument()
    if myarg in _getMain().ADMIN_ACCESS_OPTIONS:
      useDomainAdminAccess = True
    elif _getMain().getFieldsList(myarg, SHAREDDRIVE_FIELDS_CHOICE_MAP, fieldsList, initialField=['id', 'name']):
      pass
    elif myarg == 'guiroles':
      guiRoles = _getMain().getBoolean()
    else:
      FJQC.GetFormatJSON(myarg)
  fields = _getMain().getFieldsFromFieldsList(fieldsList) if fieldsList else '*'
  i, count, users = _getMain().getEntityArgument(users)
  for user in users:
    i += 1
    user, drive = _validateUserSharedDrive(user, i, count, fileIdEntity, useDomainAdminAccess=useDomainAdminAccess)
    if not drive:
      continue
    try:
      driveId = fileIdEntity['shareddrive']['driveId']
      shareddrive = _getMain().callGAPI(drive.drives(), 'get',
                             throwReasons=GAPI.DRIVE_USER_THROW_REASONS+[GAPI.FILE_NOT_FOUND, GAPI.NOT_FOUND],
                             useDomainAdminAccess=useDomainAdminAccess,
                             driveId=driveId, fields=fields)
      role = _getSharedDriveRole(shareddrive)
      if role:
        shareddrive['role'] = role if not guiRoles else SHAREDDRIVE_API_GUI_ROLES_MAP[role]
      _showSharedDrive(user, shareddrive, i, count, FJQC)
    except (GAPI.fileNotFound, GAPI.notFound) as e:
      _getMain().entityActionFailedWarning([Ent.USER, user, Ent.SHAREDDRIVE_ID, driveId], str(e), i, count)
    except (GAPI.serviceNotAvailable, GAPI.authError, GAPI.domainPolicy) as e:
      _getMain().userDriveServiceNotEnabledWarning(user, str(e), i, count)

def doInfoSharedDrive():
  infoSharedDrive([_getMain()._getAdminEmail()], True)

SHAREDDRIVE_ACL_ROLES_MAP = {
  'commenter': 'commenter',
  'contentmanager': 'fileOrganizer',
  'contributor': 'writer',
  'editor': 'writer',
  'fileorganizer': 'fileOrganizer',
  'fileorganiser': 'fileOrganizer',
  'manager': 'organizer',
  'organizer': 'organizer',
  'organiser': 'organizer',
  'owner': 'organizer',
  'read': 'reader',
  'reader': 'reader',
  'viewer': 'reader',
  'writer': 'writer',
  }

SHOWWEBVIEWLINK_CHOICES = {'text', 'hyperlink'}

# gam <UserTypeEntity> print shareddrives [todrive <ToDriveAttribute>*]
#	[asadmin [shareddriveadminquery|query <QuerySharedDrive>]]
#	[matchname <REMatchPattern>] [orgunit|org|ou <OrgUnitPath>]
#	(role|roles <SharedDriveACLRoleList>)*
#	[fields <SharedDriveFieldNameList>] [noorgunits [<Boolean>]]
#	[showwebviewlink [text|hyperlink]]
#	[guiroles [<Boolean>]] [formatjson [quotechar <Character>]]
# 	[showitemcountonly]
# gam <UserTypeEntity> show shareddrives
#	[asadmin [shareddriveadminquery|query <QuerySharedDrive>]]
#	[matchname <REMatchPattrn>] [orgunit|org|ou <OrgUnitPath>]
#	(role|roles <SharedDriveACLRoleLIst>)*
#	[fields <SharedDriveFieldNameList>] [noorgunits [<Boolean>]]
#	[showwebviewlink [text|hyperlink]]
#	[guiroles [<Boolean>]] [formatjson]
# 	[showitemcountonly]
def printShowSharedDrives(users, useDomainAdminAccess=False):
  def stripNonShowFields(shareddrive):
    if orgUnitIdToPathMap:
      td_ouid = shareddrive.get('orgUnitId')
      if td_ouid:
        shareddrive['orgUnit'] = orgUnitIdToPathMap.get(f'id:{td_ouid}', _getMain().UNKNOWN)
    if showWebViewLink:
      if showWebViewLink == 'text':
        shareddrive['webViewLink'] = 'https://drive.google.com/drive/folders/'+shareddrive['id']
      else:
        shareddrive['webViewLink'] = '=HYPERLINK("https://drive.google.com/drive/folders/'+shareddrive['id']+'", "'+shareddrive['name']+'")'
    if not showFields:
      return shareddrive
    sshareddrive = {}
    for field in showFields:
      if field in shareddrive:
        sshareddrive[field] = shareddrive[field]
    return sshareddrive

  csvPF = _getMain().CSVPrintFile(['User', 'id', 'name'], ['User', 'id', 'name', 'role']) if Act.csvFormat() else None
  FJQC = _getMain().FormatJSONQuoteChar(csvPF)
  roles = set()
  cd = orgUnitId = query = matchPattern = None
  showFields = set()
  fieldsList = []
  SHAREDDRIVE_FIELDS_CHOICE_MAP.update(SHAREDDRIVE_LIST_FIELDS_CHOICE_MAP)
  showOrgUnitPaths = True
  orgUnitIdToPathMap = None
  guiRoles = showItemCountOnly = False
  showWebViewLink = ''
  while Cmd.ArgumentsRemaining():
    myarg = _getMain().getArgument()
    if csvPF and myarg == 'todrive':
      csvPF.GetTodriveParameters()
    elif myarg in {'teamdriveadminquery', 'shareddriveadminquery', 'query'}:
      queryLocation = Cmd.Location()
      query = _getMain().getString(Cmd.OB_QUERY, minLen=0) or None
      if query:
        query = _getMain().mapQueryRelativeTimes(query, ['createdTime'])
    elif myarg == 'matchname':
      matchPattern = _getMain().getREPattern(re.IGNORECASE)
    elif myarg in {'ou', 'org', 'orgunit'}:
      orgLocation = Cmd.Location()
      if cd is None:
        cd = _getMain().buildGAPIObject(API.DIRECTORY)
      _, orgUnitId = _getMain().getOrgUnitId(cd)
      orgUnitId = orgUnitId[3:]
    elif myarg in {'role', 'roles'}:
      roles |= _getMain().getACLRoles(SHAREDDRIVE_ACL_ROLES_MAP)
    elif myarg == 'checkgroups':
      pass
    elif myarg in _getMain().ADMIN_ACCESS_OPTIONS:
      useDomainAdminAccess = True
    elif _getMain().getFieldsList(myarg, SHAREDDRIVE_FIELDS_CHOICE_MAP, fieldsList, initialField=['id', 'name']):
      pass
    elif myarg == 'noorgunits':
      showOrgUnitPaths = not _getMain().getBoolean()
    elif myarg == 'guiroles':
      guiRoles = _getMain().getBoolean()
    elif myarg == 'showwebviewlink':
      showWebViewLink = _getMain().getChoice(SHOWWEBVIEWLINK_CHOICES)
    elif myarg == 'showitemcountonly':
      showItemCountOnly = True
      showOrgUnitPaths = False
    else:
      FJQC.GetFormatJSONQuoteChar(myarg, True)
  if query and not useDomainAdminAccess:
    Cmd.SetLocation(queryLocation-1)
    _getMain().usageErrorExit(Msg.ONLY_ADMINISTRATORS_CAN_PERFORM_SHARED_DRIVE_QUERIES)
  if orgUnitId is not None and not useDomainAdminAccess:
    Cmd.SetLocation(orgLocation-1)
    _getMain().usageErrorExit(Msg.ONLY_ADMINISTRATORS_CAN_SPECIFY_SHARED_DRIVE_ORGUNIT)
  if fieldsList:
    showFields = set(fieldsList)
  if csvPF and not useDomainAdminAccess:
    if fieldsList:
      showFields.add('role')
    csvPF.AddTitle('role')
    if FJQC.formatJSON:
      csvPF.AddJSONTitles(['role'])
      csvPF.MoveJSONTitlesToEnd(['JSON'])
  if showOrgUnitPaths and useDomainAdminAccess and ((not showFields) or ('orgUnitId' in showFields)):
    orgUnitIdToPathMap = _getMain().getOrgUnitIdToPathMap(cd)
    if showFields:
      showFields.add('orgUnit')
  if showWebViewLink:
    if showFields:
      showFields.add('webViewLink')
    if csvPF:
      csvPF.AddTitle('webViewLink')
      if FJQC.formatJSON:
        csvPF.AddJSONTitles(['webViewLink'])
        csvPF.MoveJSONTitlesToEnd(['JSON'])
  i, count, users = _getMain().getEntityArgument(users)
  for user in users:
    i += 1
    user, drive = _getMain().buildGAPIServiceObject(API.DRIVE3, user, i, count)
    if not drive:
      continue
    if useDomainAdminAccess:
      _getMain().printGettingAllAccountEntities(Ent.SHAREDDRIVE, query)
      pageMessage = _getMain().getPageMessage()
    else:
      _getMain().printGettingAllEntityItemsForWhom(Ent.SHAREDDRIVE, user, i, count, query)
      pageMessage = _getMain().getPageMessageForWhom()
    try:
      feed = _getMain().callGAPIpages(drive.drives(), 'list', 'drives',
                           pageMessage=pageMessage,
                           throwReasons=GAPI.DRIVE_USER_THROW_REASONS+[GAPI.INVALID_QUERY, GAPI.INVALID,
                                                                       GAPI.QUERY_REQUIRES_ADMIN_CREDENTIALS,
                                                                       GAPI.NO_LIST_TEAMDRIVES_ADMINISTRATOR_PRIVILEGE,
                                                                       GAPI.INSUFFICIENT_ADMINISTRATOR_PRIVILEGES,
                                                                       GAPI.FILE_NOT_FOUND],
                           q=query, useDomainAdminAccess=useDomainAdminAccess,
                           fields='*', pageSize=100)
    except (GAPI.invalidQuery, GAPI.invalid, GAPI.queryRequiresAdminCredentials,
            GAPI.noListTeamDrivesAdministratorPrivilege, GAPI.insufficientAdministratorPrivileges,
            GAPI.fileNotFound) as e:
      _getMain().entityActionFailedWarning([Ent.USER, user, Ent.SHAREDDRIVE, None], str(e), i, count)
      continue
    except (GAPI.serviceNotAvailable, GAPI.authError, GAPI.domainPolicy) as e:
      _getMain().userDriveServiceNotEnabledWarning(user, str(e), i, count)
      continue
    matchedFeed = []
    if not useDomainAdminAccess:
      for shareddrive in feed:
        if matchPattern is not None and matchPattern.match(shareddrive['name']) is None:
          continue
        role = _getSharedDriveRole(shareddrive)
        if not roles or role in roles:
          shareddrive['role'] = role if not guiRoles else SHAREDDRIVE_API_GUI_ROLES_MAP[role]
          matchedFeed.append(shareddrive)
    elif matchPattern is not None or orgUnitId is not None:
      for shareddrive in feed:
        if ((matchPattern is not None and matchPattern.match(shareddrive['name']) is None) or
            (orgUnitId is not None and orgUnitId != shareddrive.get('orgUnitId'))):
          continue
        matchedFeed.append(shareddrive)
    else:
      matchedFeed = feed
    jcount = len(matchedFeed)
    if jcount == 0:
      _getMain().setSysExitRC(_getMain().NO_ENTITIES_FOUND_RC)
    if showItemCountOnly:
      _getMain().writeStdout(f'{jcount}\n')
      return
    if not csvPF:
      if not FJQC.formatJSON:
        _getMain().entityPerformActionNumItems([Ent.USER, user], jcount, Ent.SHAREDDRIVE, i, count)
      Ind.Increment()
      j = 0
      for shareddrive in sorted(matchedFeed, key=lambda k: k['name']):
        j += 1
        shareddrive = stripNonShowFields(shareddrive)
        _showSharedDrive(user, shareddrive, j, jcount, FJQC)
      Ind.Decrement()
    elif matchedFeed:
      for shareddrive in sorted(matchedFeed, key=lambda k: k['name']):
        shareddrive = stripNonShowFields(shareddrive)
        if FJQC.formatJSON:
          row = {'User': user, 'id': shareddrive['id'], 'name': shareddrive['name']}
          if not useDomainAdminAccess:
            row['role'] = shareddrive['role'] if not guiRoles else SHAREDDRIVE_API_GUI_ROLES_MAP[shareddrive['role']]
          if showWebViewLink:
            row['webViewLink'] = shareddrive['webViewLink']
          row['JSON'] = json.dumps(_getMain().cleanJSON(shareddrive, timeObjects=SHAREDDRIVE_TIME_OBJECTS), ensure_ascii=False, sort_keys=True)
          csvPF.WriteRow(row)
        else:
          csvPF.WriteRowTitles(_getMain().flattenJSON(shareddrive, flattened={'User': user}, timeObjects=SHAREDDRIVE_TIME_OBJECTS))
    elif GC.Values[GC.CSV_OUTPUT_USERS_AUDIT]:
      csvPF.WriteRowNoFilter({'User': user})
  if csvPF:
    csvPF.writeCSVfile('SharedDrives')

def doPrintShowSharedDrives():
  printShowSharedDrives([_getMain()._getAdminEmail()], True)

# gam print oushareddrives [todrive <ToDriveAttribute>*]
#	[ou|org|orgunit <OrgUnitPath>]
#	[formatjson [quotechar <Character>]]
# 	[showitemcountonly]
# gam show oushareddrives
#	[ou|org|orgunit <OrgUnitPath>]
#	[formatjson]
# 	[showitemcountonly]
def doPrintShowOrgunitSharedDrives():
  def _getOrgUnitSharedDriveInfo(shareddrive):
    shareddrive['driveId'] = shareddrive['name'].rsplit(';')[1]
    shareddrive['driveName'] = _getSharedDriveNameFromId(drive, shareddrive['driveId'], True)
    shareddrive['orgUnitPath'] = orgUnitPath

  def _showOrgUnitSharedDrive(shareddrive, j, jcount, FJQC):
    if FJQC.formatJSON:
      _getMain().printLine(json.dumps(_getMain().cleanJSON(shareddrive), ensure_ascii=False, sort_keys=True))
      return
    _getMain().printEntity([Ent.NAME, f'{shareddrive["name"]}'], j, jcount)
    Ind.Increment()
    _getMain().printEntity([Ent.TYPE, shareddrive['type']])
    _getMain().printEntity([Ent.MEMBER, shareddrive['member']])
    _getMain().printEntity([Ent.MEMBER_URI, shareddrive['memberUri']])
    _getMain().printEntity([Ent.SHAREDDRIVE_ID, shareddrive['driveId']])
    _getMain().printEntity([Ent.SHAREDDRIVE_NAME, shareddrive['driveName']])
    _getMain().printEntity([Ent.ORGANIZATIONAL_UNIT, shareddrive['orgUnitPath']])
    Ind.Decrement()

  ci = _getMain().buildGAPIObject(API.CLOUDIDENTITY_ORGUNITS_BETA)
  cd = _getMain().buildGAPIObject(API.DIRECTORY)
  _, drive = _getMain().buildGAPIServiceObject(API.DRIVE3, _getMain()._getAdminEmail())
  if drive is None:
    return
  csvPF = _getMain().CSVPrintFile(['name', 'type', 'member', 'memberUri', 'driveId', 'driveName', 'orgUnitPath']) if Act.csvFormat() else None
  FJQC = _getMain().FormatJSONQuoteChar(csvPF)
  orgUnitPath = '/'
  showItemCountOnly = False
  while Cmd.ArgumentsRemaining():
    myarg = _getMain().getArgument()
    if csvPF and myarg == 'todrive':
      csvPF.GetTodriveParameters()
    elif myarg in {'ou', 'org', 'orgunit'}:
      orgUnitPath = _getMain().getString(Cmd.OB_ORGUNIT_ITEM)
    elif myarg == 'showitemcountonly':
      showItemCountOnly = True
    else:
      FJQC.GetFormatJSONQuoteChar(myarg, True)
  if csvPF and FJQC.formatJSON:
    csvPF.SetJSONTitles(['name', 'JSON'])
  orgUnitPath, orgUnitId = _getMain().getOrgUnitId(cd, orgUnitPath)
  _getMain().printGettingAllEntityItemsForWhom(Ent.SHAREDDRIVE, orgUnitPath, entityType=Ent.ORGANIZATIONAL_UNIT)
  sds = _getMain().callGAPIpages(ci.orgUnits().memberships(), 'list', 'orgMemberships',
                      pageMessage=_getMain().getPageMessageForWhom(),
                      parent=f'orgUnits/{orgUnitId[3:]}',
                      customer=_getMain()._getCustomersCustomerIdWithC(),
                      filter="type == 'shared_drive'")
  jcount = len(sds)
  if jcount == 0:
    _getMain().setSysExitRC(_getMain().NO_ENTITIES_FOUND_RC)
  if showItemCountOnly:
    _getMain().writeStdout(f'{jcount}\n')
    return
  if not csvPF:
    if not FJQC.formatJSON:
      _getMain().entityPerformActionNumItems([Ent.ORGANIZATIONAL_UNIT, orgUnitPath], jcount, Ent.SHAREDDRIVE)
    Ind.Increment()
    j = 0
    for shareddrive in sds:
      j += 1
      _getOrgUnitSharedDriveInfo(shareddrive)
      _showOrgUnitSharedDrive(shareddrive, j, jcount, FJQC)
    Ind.Decrement()
  else:
    for shareddrive in sds:
      _getOrgUnitSharedDriveInfo(shareddrive)
      if FJQC.formatJSON:
        row = {'name': shareddrive['name']}
        row['JSON'] = json.dumps(_getMain().cleanJSON(shareddrive), ensure_ascii=False, sort_keys=True)
        csvPF.WriteRow(row)
      else:
        csvPF.WriteRowTitles(_getMain().flattenJSON(shareddrive))
  if csvPF:
    csvPF.writeCSVfile('OrgUnit {orgUnitPath} SharedDrives')

# gam [<UserTypeEntity>] copy shareddriveacls <SharedDriveEntity> to <SharedDriveEntity>
#	[asadmin]
#	[showpermissionsmessages [<Boolean>]]
#	[excludepermissionsfromdomains|includepermissionsfromdomains <DomainNameList>]
#	(mappermissionsemail <EmailAddress> <EmailAddress>)* [mappermissionsemailfile <CSVFileInput> endcsv]
#	(mappermissionsdomain <DomainName> <DomainName>)*
# gam [<UserTypeEntity>] sync shareddriveacls <SharedDriveEntity> with <SharedDriveEntity>
#	[asadmin]
#	[showpermissionsmessages [<Boolean>]]
#	[excludepermissionsfromdomains|includepermissionsfromdomains <DomainNameList>]
#	(mappermissionsemail <EmailAddress> <EmailAddress>)* [mappermissionsemailfile <CSVFileInput> endcsv]
#	(mappermissionsdomain <DomainName> <DomainName>)*
def copySyncSharedDriveACLs(users, useDomainAdminAccess=False):
  copyMoveOptions = initCopyMoveOptions(True)
  srcFileIdEntity = getSharedDriveEntity()
  _getMain().checkArgumentPresent(['to', 'with'], True)
  tgtFileIdEntity = getSharedDriveEntity()
  while Cmd.ArgumentsRemaining():
    myarg = _getMain().getArgument()
    if getCopyMoveOptions(myarg, copyMoveOptions):
      pass
    elif myarg in _getMain().ADMIN_ACCESS_OPTIONS:
      useDomainAdminAccess = True
    else:
      _getMain().unknownArgumentExit()
  copyMoveOptions['useDomainAdminAccess'] = useDomainAdminAccess
  copyMoveOptions['copyTopFolderNonInheritedPermissions'] =\
    COPY_NONINHERITED_PERMISSIONS_ALWAYS if Act.Get() == Act.COPY else COPY_NONINHERITED_PERMISSIONS_SYNC_ALL_FOLDERS
  copyMoveOptions['copyMergeWithParentFolderPermissions'] = True
  copyMoveOptions['copyTopFolderInheritedPermissions'] = False
  copyMoveOptions['destParentType'] = DEST_PARENT_SHAREDDRIVE_ROOT
  i, count, users = _getMain().getEntityArgument(users)
  for user in users:
    i += 1
    user, drive = _validateUserSharedDrive(user, i, count, srcFileIdEntity)
    if not drive:
      continue
    if not srcFileIdEntity.get('shareddrivename'):
      srcFileIdEntity['shareddrivename'] = _getSharedDriveNameFromId(drive, srcFileIdEntity['shareddrive']['driveId'],
                                                                     useDomainAdminAccess)
    if tgtFileIdEntity.get('shareddrivename'):
      if not _convertSharedDriveNameToId(drive, user, i, count, tgtFileIdEntity, useDomainAdminAccess):
        continue
      tgtFileIdEntity['shareddrive']['corpora'] = 'drive'
    else:
      tgtFileIdEntity['shareddrivename'] = _getSharedDriveNameFromId(drive, tgtFileIdEntity['shareddrive']['driveId'],
                                                                     useDomainAdminAccess)
    statistics = _initStatistics()
    copyMoveOptions['sourceDriveId'] = srcFileIdEntity['shareddrive']['driveId']
    copyMoveOptions['destDriveId'] = tgtFileIdEntity['shareddrive']['driveId']
    _getMain().entityPerformActionModifierItemValueList([Ent.USER, user, Ent.SHAREDDRIVE, srcFileIdEntity['shareddrivename']],
                                             f"{Ent.Plural(Ent.PERMISSION)} {Act.MODIFIER_TO}",
                                             [Ent.SHAREDDRIVE, tgtFileIdEntity['shareddrivename']], i, count)
    _copyPermissions(drive, user, i, count, 0, 0,
                     Ent.SHAREDDRIVE, srcFileIdEntity['shareddrive']['driveId'], srcFileIdEntity['shareddrivename'],
                     tgtFileIdEntity['shareddrive']['driveId'], tgtFileIdEntity['shareddrivename'],
                     statistics, STAT_FOLDER_PERMISSIONS_FAILED,
                     copyMoveOptions, True,
                     'copyTopFolderInheritedPermissions',
                     'copyTopFolderNonInheritedPermissions',
                     False)

def doCopySyncSharedDriveACLs():
  copySyncSharedDriveACLs([_getMain()._getAdminEmail()], True)

SHOW_NO_PERMISSIONS_DRIVES_CHOICE_MAP = {
  'true': 1,
  'false': 0,
  'only': -1,
  }

# gam [<UserTypeEntity>] print shareddriveacls [todrive <ToDriveAttribute>*]
#	[asadmin] [shareddriveadminquery|query <QuerySharedDrive>]
#	[matchname <REMatchPattern>] [orgunit|org|ou <OrgUnitPath>]
#	[user|group <EmailAddress> [checkgroups]] (role|roles <SharedDriveACLRoleList>)*
#	<PermissionMatch>* [<PermissionMatchAction>] [pmselect]
#	[oneitemperrow] [maxitems <Integer>]
#	[shownopermissionsdrives false|true|only]
#	[<DrivePermissionsFieldName>*|(fields <DrivePermissionsFieldNameList>)]
#	(addcsvdata <FieldName> <String>)*
#	[formatjson [quotechar <Character>]]
# gam [<UserTypeEntity>] show shareddriveacls
#	[asadmin] [shareddriveadminquery|query <QuerySharedDrive>]
#	[matchname <REMatchPattern>] [orgunit|org|ou <OrgUnitPath>]
#	[user|group <EmailAddress> [checkgroups]] (role|roles <SharedDriveACLRoleList>)*
#	<PermissionMatch>* [<PermissionMatchAction>] [pmselect]
#	[oneitemperrow] [maxitems <Integer>]
#	[shownopermissionsdrives false|true|only]
#	[<DrivePermissionsFieldName>*|(fields <DrivePermissionsFieldNameList>)]
#	[formatjson]
def printShowSharedDriveACLs(users, useDomainAdminAccess=False):
  def _printPermissionRow(baserow, permission):
    row = baserow.copy()
    _getMain().flattenJSON({'permission': permission}, flattened=row, timeObjects=timeObjects)
    if not FJQC.formatJSON:
      csvPF.WriteRowTitles(row)
    elif csvPF.CheckRowTitles(row):
      row = baserow.copy()
      row['JSON'] = json.dumps(cleanJSON({'permission': permission}, timeObjects=timeObjects),
                               ensure_ascii=False, sort_keys=True)
      csvPF.WriteRowNoFilter(row)

  csvPF = _getMain().CSVPrintFile(['User', 'id', 'name', 'createdTime'], 'sortall') if Act.csvFormat() else None
  FJQC = _getMain().FormatJSONQuoteChar(csvPF)
  roles = set()
  checkGroups = oneItemPerRow = pmselect = False
  showNoPermissionsDrives = SHOW_NO_PERMISSIONS_DRIVES_CHOICE_MAP['false']
  fieldsList = []
  cd = emailAddress = orgUnitId = query = matchPattern = permtype = None
  PM = PermissionMatch()
  maxItems = 0
  addCSVData = {}
  while Cmd.ArgumentsRemaining():
    myarg = _getMain().getArgument()
    if csvPF and myarg == 'todrive':
      csvPF.GetTodriveParameters()
    elif myarg in {'teamdriveadminquery', 'shareddriveadminquery', 'query'}:
      queryLocation = Cmd.Location()
      query = _getMain().getString(Cmd.OB_QUERY, minLen=0) or None
      if query:
        query = _getMain().mapQueryRelativeTimes(query, ['createdTime'])
    elif myarg == 'matchname':
      matchPattern = _getMain().getREPattern(re.IGNORECASE)
    elif myarg in {'ou', 'org', 'orgunit'}:
      orgLocation = Cmd.Location()
      if cd is None:
        cd = _getMain().buildGAPIObject(API.DIRECTORY)
      _, orgUnitId = _getMain().getOrgUnitId(cd)
      orgUnitId = orgUnitId[3:]
    elif myarg in {'user', 'group'}:
      permtype = myarg
      emailAddress = _getMain().getEmailAddress(noUid=True)
    elif myarg in {'role', 'roles'}:
      roles |= _getMain().getACLRoles(SHAREDDRIVE_ACL_ROLES_MAP)
    elif myarg == 'checkgroups':
      checkGroups = True
    elif myarg == 'oneitemperrow':
      oneItemPerRow = True
    elif myarg == 'maxitems':
      maxItems = _getMain().getInteger(minVal=0)
    elif getDriveFilePermissionsFields(myarg, fieldsList):
      pass
    elif myarg in _getMain().ADMIN_ACCESS_OPTIONS:
      useDomainAdminAccess = True
    elif PM.ProcessArgument(myarg):
      pass
    elif myarg == 'pmselect':
      pmselect = True
    elif myarg == 'shownopermissionsdrives':
      showNoPermissionsDrives = _getMain().getChoice(SHOW_NO_PERMISSIONS_DRIVES_CHOICE_MAP, mapChoice=True)
    elif csvPF and myarg == 'addcsvdata':
      _getMain().getAddCSVData(addCSVData)
    else:
      FJQC.GetFormatJSONQuoteChar(myarg, True)
  if query and not useDomainAdminAccess:
    Cmd.SetLocation(queryLocation-1)
    _getMain().usageErrorExit(Msg.ONLY_ADMINISTRATORS_CAN_PERFORM_SHARED_DRIVE_QUERIES)
  if orgUnitId is not None and not useDomainAdminAccess:
    Cmd.SetLocation(orgLocation-1)
    _getMain().usageErrorExit(Msg.ONLY_ADMINISTRATORS_CAN_SPECIFY_SHARED_DRIVE_ORGUNIT)
  if fieldsList:
    if permtype is not None:
      fieldsList.extend(['type', 'emailAddress'])
    if roles:
      fieldsList.append('role')
  fields = _getMain().getItemFieldsFromFieldsList('permissions', fieldsList, True)
  printKeys, timeObjects = _getDriveFileACLPrintKeysTimeObjects()
  if checkGroups:
    if emailAddress:
      cd = _getMain().buildGAPIObject(API.DIRECTORY)
      try:
        groups = _getMain().callGAPIpages(cd.groups(), 'list', 'groups',
                               throwReasons=GAPI.GROUP_LIST_USERKEY_THROW_REASONS,
                               retryReasons=GAPI.SERVICE_NOT_AVAILABLE_RETRY_REASONS,
                               userKey=emailAddress, orderBy='email', fields='nextPageToken,groups(email)')
      except (GAPI.invalidMember, GAPI.invalidInput):
        _getMain().badRequestWarning(Ent.GROUP, Ent.MEMBER, emailAddress)
        return
      except (GAPI.resourceNotFound, GAPI.domainNotFound, GAPI.forbidden, GAPI.badRequest):
        accessErrorExit(cd)
      groupsSet = {group['email'] for group in groups}
    else:
      checkGroups = False
  if csvPF and addCSVData:
    csvPF.AddTitles(sorted(addCSVData.keys()))
    if FJQC.formatJSON:
      csvPF.AddJSONTitles(sorted(addCSVData.keys()))
      csvPF.MoveJSONTitlesToEnd(['JSON'])
  i, count, users = _getMain().getEntityArgument(users)
  for user in users:
    i += 1
    user, drive = _getMain().buildGAPIServiceObject(API.DRIVE3, user, i, count)
    if not drive:
      continue
    feed = None
    if permtype == 'user':
      _, userdrive = _getMain().buildGAPIServiceObject(API.DRIVE3, emailAddress, displayError=False)
      if userdrive is not None:
        try:
          feed = _getMain().callGAPIpages(userdrive.drives(), 'list', 'drives',
                               throwReasons=GAPI.DRIVE_USER_THROW_REASONS+[GAPI.INVALID, GAPI.NO_LIST_TEAMDRIVES_ADMINISTRATOR_PRIVILEGE],
                               fields='nextPageToken,drives(id,name,createdTime,orgUnitId)', pageSize=100)
        except (GAPI.invalid, GAPI.noListTeamDrivesAdministratorPrivilege):
          pass
        except (GAPI.serviceNotAvailable, GAPI.authError, GAPI.domainPolicy):
          pass
    if feed is None:
      if useDomainAdminAccess:
        _getMain().printGettingAllAccountEntities(Ent.SHAREDDRIVE, query)
        pageMessage = _getMain().getPageMessage()
      else:
        _getMain().printGettingAllEntityItemsForWhom(Ent.SHAREDDRIVE, user, i, count, query)
        pageMessage = _getMain().getPageMessageForWhom()
      try:
        feed = _getMain().callGAPIpages(drive.drives(), 'list', 'drives',
                             pageMessage=pageMessage,
                             throwReasons=GAPI.DRIVE_USER_THROW_REASONS+[GAPI.INVALID_QUERY, GAPI.INVALID,
                                                                         GAPI.QUERY_REQUIRES_ADMIN_CREDENTIALS,
                                                                         GAPI.NO_LIST_TEAMDRIVES_ADMINISTRATOR_PRIVILEGE,
                                                                         GAPI.INSUFFICIENT_ADMINISTRATOR_PRIVILEGES],
                             q=query, useDomainAdminAccess=useDomainAdminAccess,
                             fields='nextPageToken,drives(id,name,createdTime,orgUnitId)', pageSize=100)
      except (GAPI.invalidQuery, GAPI.invalid, GAPI.queryRequiresAdminCredentials,
              GAPI.noListTeamDrivesAdministratorPrivilege, GAPI.insufficientAdministratorPrivileges) as e:
        _getMain().entityActionFailedWarning([Ent.USER, user, Ent.SHAREDDRIVE, None], str(e), i, count)
        continue
      except (GAPI.serviceNotAvailable, GAPI.authError, GAPI.domainPolicy) as e:
        _getMain().userDriveServiceNotEnabledWarning(user, str(e), i, count)
        continue
    matchFeed = []
    jcount = len(feed)
    j = 0
    for shareddrive in feed:
      j += 1
      if ((matchPattern is not None and matchPattern.match(shareddrive['name']) is None) or
          (orgUnitId is not None and orgUnitId != shareddrive.get('orgUnitId'))):
        continue
      _getMain().printGettingAllEntityItemsForWhom(Ent.PERMISSION, shareddrive['name'], j, jcount)
      shareddrive['createdTime'] = formatLocalTime(shareddrive['createdTime'])
      shareddrive['permissions'] = []
      try:
        permissions = _getMain().callGAPIpages(drive.permissions(), 'list', 'permissions',
                                    pageMessage=_getMain().getPageMessageForWhom(),
                                    throwReasons=GAPI.DRIVE3_GET_ACL_REASONS,
                                    retryReasons=GAPI.SERVICE_NOT_AVAILABLE_RETRY_REASONS,
                                    useDomainAdminAccess=useDomainAdminAccess,
                                    fileId=shareddrive['id'], fields=fields, supportsAllDrives=True)
        if not permissions:
          if showNoPermissionsDrives == 0: # no permissions and showNoPermissionDrives False - ignore
            continue
          matchFeed.append(shareddrive) # no permissions and showNoPermissionDrives Only/True - keep
          continue
        if showNoPermissionsDrives < 0: # permissions and showNoPermissionDrives Only/True - ignore
          continue
        if pmselect:
          if not PM.CheckPermissionMatches(permissions):
            continue
        else:
          permissions = PM.GetMatchingPermissions(permissions)
        for permission in permissions:
          if roles and permission['role'] not in roles:
            continue
          permission.pop('teamDrivePermissionDetails', None)
          if permtype is None:
            shareddrive['permissions'].append(permission)
          elif permission['type'] == permtype and permission['emailAddress'] == emailAddress:
            shareddrive['permissions'].append(permission)
          elif checkGroups and permission['emailAddress'] in groupsSet:
            shareddrive['permissions'].append(permission)
        if shareddrive['permissions']:
          numItems = len(shareddrive['permissions'])
          if numItems > maxItems > 0:
            shareddrive['permissions'] = shareddrive['permissions'][0:maxItems]
          matchFeed.append(shareddrive)
      except (GAPI.fileNotFound, GAPI.forbidden, GAPI.internalError,
              GAPI.insufficientAdministratorPrivileges, GAPI.insufficientFilePermissions,
              GAPI.unknownError, GAPI.invalid):
        pass
    jcount = len(matchFeed)
    if jcount == 0:
      _getMain().setSysExitRC(_getMain().NO_ENTITIES_FOUND_RC)
    if not csvPF:
      if not FJQC.formatJSON:
        _getMain().entityPerformActionNumItems([Ent.USER, user], jcount, Ent.SHAREDDRIVE, i, count)
      Ind.Increment()
      j = 0
      for shareddrive in sorted(matchFeed, key=lambda k: k['name']):
        j += 1
        if not FJQC.formatJSON:
          _showDriveFilePermissions(Ent.SHAREDDRIVE, f'{shareddrive["name"]} ({shareddrive["id"]}) - {shareddrive["createdTime"]}',
                                    shareddrive['permissions'], printKeys, timeObjects, j, jcount)
        else:
          if oneItemPerRow and shareddrive['permissions']:
            for permission in shareddrive['permissions']:
              _showDriveFilePermissionJSON(user, shareddrive['id'], shareddrive['name'], shareddrive['createdTime'], permission, timeObjects)
          else:
            _showDriveFilePermissionsJSON(user, shareddrive['id'], shareddrive['name'], shareddrive['createdTime'], shareddrive['permissions'], timeObjects)
      Ind.Decrement()
    elif matchFeed:
      if oneItemPerRow:
        for shareddrive in sorted(matchFeed, key=lambda k: k['name']):
          baserow = {'User': user, 'id': shareddrive['id'], 'name': shareddrive['name'], 'createdTime': shareddrive['createdTime']}
          if addCSVData:
            baserow.update(addCSVData)
          if shareddrive['permissions']:
            for permission in shareddrive['permissions']:
              _mapDrivePermissionNames(permission)
              pdetails = permission.pop('permissionDetails', [])
              if not pdetails:
                _printPermissionRow(baserow, permission)
              else:
                for pdetail in pdetails:
                  permission['permissionDetails'] = pdetail
                  _printPermissionRow(baserow, permission)
          else:
            if not FJQC.formatJSON:
              csvPF.WriteRowTitles(baserow)
            elif csvPF.CheckRowTitles(baserow):
              baserow['JSON'] = json.dumps({})
              csvPF.WriteRowNoFilter(baserow)
      else:
        for shareddrive in sorted(matchFeed, key=lambda k: k['name']):
          baserow = {'User': user, 'id': shareddrive['id'], 'name': shareddrive['name'], 'createdTime': shareddrive['createdTime']}
          if addCSVData:
            baserow.update(addCSVData)
          row = baserow.copy()
          if shareddrive['permissions']:
            for permission in shareddrive['permissions']:
              _mapDrivePermissionNames(permission)
            _getMain().flattenJSON({'permissions': shareddrive['permissions']}, flattened=row, timeObjects=timeObjects)
            if not FJQC.formatJSON:
              csvPF.WriteRowTitles(row)
            elif csvPF.CheckRowTitles(row):
              baserow['JSON'] = json.dumps(cleanJSON({'permissions': shareddrive['permissions']}, timeObjects=timeObjects),
                                           ensure_ascii=False, sort_keys=True)
              csvPF.WriteRowNoFilter(baserow)
          else:
            if not FJQC.formatJSON:
              csvPF.WriteRowTitles(baserow)
            elif csvPF.CheckRowTitles(baserow):
              baserow['JSON'] = json.dumps({})
              csvPF.WriteRowNoFilter(baserow)
  if csvPF:
    if not oneItemPerRow:
      csvPF.SetIndexedTitles(['permissions'])
    csvPF.writeCSVfile('SharedDrive ACLs')

def doPrintShowSharedDriveACLs():
  printShowSharedDriveACLs([_getMain()._getAdminEmail()], True)

PRINT_ORGANIZER_TYPES = {'group', 'user'}

# gam [<UserTypeEntity>] print shareddriveorganizers [todrive <ToDriveAttribute>*]
#	[adminaccess|asadmin]
#	[(shareddriveadminquery|query <QuerySharedDrive>) |
#	 (shareddrives|teamdrives (<SharedDriveIDList>|(select <FileSelector>|<CSVFileSelector>)))]
#	[matchname <REMatchPattern>] [orgunit|org|ou <OrgUnitPath>]
#	[domainlist <DomainList>]
#	[includetypes user|group]
#	[oneorganizer [<Boolean>]]
#	[shownorganizerdrives false|true|only]
#	[includefileorganizers [<Boolean>]]
#	[delimiter <Character>]
def printSharedDriveOrganizers(users, useDomainAdminAccess=False):
  csvPF = _getMain().CSVPrintFile(['id', 'name', 'organizers', 'createdTime'], 'sortall')
  delimiter = GC.Values[GC.CSV_OUTPUT_FIELD_DELIMITER]
  roles = set(['organizer'])
  includeTypes = set()
  showNoOrganizerDrives = SHOW_NO_PERMISSIONS_DRIVES_CHOICE_MAP['true']
  fieldsList = ['role', 'type', 'emailAddress']
  cd = entityList = orgUnitId = query = matchPattern = None
  domainList = set([(GC.Values[GC.DOMAIN] if GC.Values[GC.DOMAIN] else _getMain()._getValueFromOAuth('hd'))])
  oneOrganizer = True
  while Cmd.ArgumentsRemaining():
    myarg = _getMain().getArgument()
    if csvPF and myarg == 'todrive':
      csvPF.GetTodriveParameters()
    elif myarg == 'delimiter':
      delimiter = _getMain().getCharacter()
    elif myarg in {'shareddrive', 'shareddrives', 'teamdrive', 'teamdrives'}:
      sharedDriveArg = myarg
      itemList = _getMain().getString(Cmd.OB_SHAREDDRIVE_ID_LIST)
      if itemList != 'select':
        entityList =  itemList.replace(',', ' ').split()
      else:
        entityList = _getMain().getEntityList(Cmd.OB_SHAREDDRIVE_ID_LIST)
    elif myarg in {'teamdriveadminquery', 'shareddriveadminquery', 'query'}:
      queryArg = myarg
      queryLocation = Cmd.Location()
      query = _getMain().getString(Cmd.OB_QUERY, minLen=0) or None
      if query:
        query = _getMain().mapQueryRelativeTimes(query, ['createdTime'])
    elif myarg == 'matchname':
      matchPattern = _getMain().getREPattern(re.IGNORECASE)
    elif myarg in {'ou', 'org', 'orgunit'}:
      orgLocation = Cmd.Location()
      if cd is None:
        cd = _getMain().buildGAPIObject(API.DIRECTORY)
      orgUnitPath, orgUnitId = _getMain().getOrgUnitId(cd)
      orgUnitId = orgUnitId[3:]
      orgUnitInfo = {'orgUnit': orgUnitPath, 'orgUnitId': orgUnitId}
    elif myarg in _getMain().ADMIN_ACCESS_OPTIONS:
      useDomainAdminAccess = True
    elif myarg == 'domainlist':
      domainList = set(_getMain().getString(Cmd.OB_DOMAIN_NAME_LIST, minLen=0).replace(',', ' ').lower().split())
    elif myarg == 'includetypes':
      for itype in _getMain().getString(Cmd.OB_ORGANIZER_TYPE_LIST).lower().replace(',', ' ').split():
        if itype in PRINT_ORGANIZER_TYPES:
          includeTypes.add(itype)
        else:
          _getMain().invalidChoiceExit(itype, PRINT_ORGANIZER_TYPES, True)
    elif myarg == 'oneorganizer':
      oneOrganizer = _getMain().getBoolean()
    elif myarg == 'shownoorganizerdrives':
      showNoOrganizerDrives = _getMain().getChoice(SHOW_NO_PERMISSIONS_DRIVES_CHOICE_MAP, defaultChoice=1, mapChoice=True)
    elif myarg in {'includefileorganizers', 'includecontentmanagers'}:
      if _getMain().getBoolean():
        roles.add('fileOrganizer')
    else:
      _getMain().unknownArgumentExit()
  if query:
    if not useDomainAdminAccess:
      Cmd.SetLocation(queryLocation-1)
      _getMain().usageErrorExit(Msg.ONLY_ADMINISTRATORS_CAN_PERFORM_SHARED_DRIVE_QUERIES)
    if entityList:
      Cmd.SetLocation(queryLocation-1)
      _getMain().usageErrorExit(Msg.ARE_MUTUALLY_EXCLUSIVE.format(queryArg, sharedDriveArg))
  if orgUnitId is not None:
    if not useDomainAdminAccess:
      Cmd.SetLocation(orgLocation-1)
      _getMain().usageErrorExit(Msg.ONLY_ADMINISTRATORS_CAN_SPECIFY_SHARED_DRIVE_ORGUNIT)
    csvPF.AddTitles(['orgUnit', 'orgUnitId'])
  if not includeTypes:
    includeTypes = set(['user'])
  fields = _getMain().getItemFieldsFromFieldsList('permissions', fieldsList, True)
  i, count, users = _getMain().getEntityArgument(users)
  for user in users:
    i += 1
    user, drive = _getMain().buildGAPIServiceObject(API.DRIVE3, user, i, count)
    if not drive:
      continue
    if entityList is None:
      if useDomainAdminAccess:
        _getMain().printGettingAllAccountEntities(Ent.SHAREDDRIVE, query)
        pageMessage = _getMain().getPageMessage()
      else:
        _getMain().printGettingAllEntityItemsForWhom(Ent.SHAREDDRIVE, user, i, count, query)
        pageMessage = _getMain().getPageMessageForWhom()
      try:
        feed = _getMain().callGAPIpages(drive.drives(), 'list', 'drives',
                             pageMessage=pageMessage,
                             throwReasons=GAPI.DRIVE_USER_THROW_REASONS+[GAPI.INVALID_QUERY, GAPI.INVALID,
                                                                         GAPI.QUERY_REQUIRES_ADMIN_CREDENTIALS,
                                                                         GAPI.NO_LIST_TEAMDRIVES_ADMINISTRATOR_PRIVILEGE,
                                                                         GAPI.INSUFFICIENT_ADMINISTRATOR_PRIVILEGES],
                             q=query, useDomainAdminAccess=useDomainAdminAccess,
                             fields='nextPageToken,drives(id,name,createdTime,orgUnitId)', pageSize=100)
      except (GAPI.invalidQuery, GAPI.invalid, GAPI.queryRequiresAdminCredentials,
              GAPI.noListTeamDrivesAdministratorPrivilege, GAPI.insufficientAdministratorPrivileges) as e:
        _getMain().entityActionFailedWarning([Ent.USER, user, Ent.SHAREDDRIVE, None], str(e), i, count)
        continue
      except (GAPI.serviceNotAvailable, GAPI.authError, GAPI.domainPolicy) as e:
        _getMain().userDriveServiceNotEnabledWarning(user, str(e), i, count)
        continue
    else:
      feed = []
      jcount = len(entityList)
      j = 0
      for driveId in entityList:
        j +=1
        try:
          feed.append(_getMain().callGAPI(drive.drives(), 'get',
                               throwReasons=GAPI.DRIVE_USER_THROW_REASONS+[GAPI.FILE_NOT_FOUND, GAPI.NOT_FOUND],
                               useDomainAdminAccess=useDomainAdminAccess,
                               driveId=driveId, fields='id,name,createdTime,orgUnitId'))
        except (GAPI.fileNotFound, GAPI.notFound) as e:
          _getMain().entityActionNotPerformedWarning([Ent.USER, user, Ent.SHAREDDRIVE_ID, driveId], str(e), j, jcount)
          continue
        except (GAPI.serviceNotAvailable, GAPI.authError, GAPI.domainPolicy) as e:
          _getMain().userDriveServiceNotEnabledWarning(user, str(e), i, count)
          break
    matchFeed = []
    jcount = len(feed)
    j = 0
    for shareddrive in feed:
      j += 1
      if ((matchPattern is not None and matchPattern.match(shareddrive['name']) is None) or
          (orgUnitId is not None and orgUnitId != shareddrive.get('orgUnitId'))):
        continue
      _getMain().printGettingAllEntityItemsForWhom(Ent.PERMISSION, shareddrive['name'], j, jcount)
      shareddrive['createdTime'] = formatLocalTime(shareddrive['createdTime'])
      shareddrive['organizers'] = []
      try:
        permissions = _getMain().callGAPIpages(drive.permissions(), 'list', 'permissions',
                                    pageMessage=_getMain().getPageMessageForWhom(),
                                    throwReasons=GAPI.DRIVE3_GET_ACL_REASONS,
                                    retryReasons=GAPI.SERVICE_NOT_AVAILABLE_RETRY_REASONS,
                                    useDomainAdminAccess=useDomainAdminAccess,
                                    fileId=shareddrive['id'], fields=fields, supportsAllDrives=True)
        for permission in permissions:
          if permission['type'] in includeTypes and permission['role'] in roles and permission.get('emailAddress', ''):
            if domainList:
              _, domain = permission['emailAddress'].lower().split('@', 1)
              if domain not in domainList:
                continue
            shareddrive['organizers'].append(permission['emailAddress'])
            if oneOrganizer:
              break
        if not shareddrive['organizers']:
          if showNoOrganizerDrives == 0: # no organizers and showNoOrganizerDrives False - ignore
            continue
          matchFeed.append(shareddrive) # no organizers and showNoOrganizerDrives Only/True - keep
          continue
        if showNoOrganizerDrives < 0: # organizers and showNoOrganizerDrives Only/True - ignore
          continue
        matchFeed.append(shareddrive)
      except (GAPI.fileNotFound, GAPI.forbidden, GAPI.internalError,
              GAPI.insufficientAdministratorPrivileges, GAPI.insufficientFilePermissions,
              GAPI.unknownError, GAPI.invalid):
        pass
    if len(matchFeed) == 0:
      _getMain().setSysExitRC(_getMain().NO_ENTITIES_FOUND_RC)
    for shareddrive in sorted(matchFeed, key=lambda k: k['name']):
      row = {'id': shareddrive['id'], 'name': shareddrive['name'],
             'organizers': delimiter.join(shareddrive['organizers']),
             'createdTime': shareddrive['createdTime']}
      if orgUnitId:
        row.update(orgUnitInfo)
      csvPF.WriteRowTitles(row)
  if csvPF:
    csvPF.writeCSVfile('SharedDrive Organizers')

def doPrintSharedDriveOrganizers():
  printSharedDriveOrganizers([_getMain()._getAdminEmail()], True)

