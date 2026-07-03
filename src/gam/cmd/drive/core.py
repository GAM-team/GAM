"""Drive search, entity handling, file attributes, mime type validation.

Part of the drive sub-package, extracted from drive.py."""

"""GAM Google Drive file, permission, shared drive, and label management."""

import re
import sys
import io
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

def __getattr__(name):
  """Fall back to gam module for any undefined names."""
  main = _getMain()
  try:
    return getattr(main, name)
  except AttributeError:
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")

ROOTID = 'rootid'

def doDriveSearch(drive, user, i, count, query=None, parentQuery=False, emptyQueryOK=False, orderBy=None, sharedDriveOnly=False, **kwargs):
  if query == 'allitems':
    query = None
  if GC.Values[GC.SHOW_GETTINGS]:
    _getMain().printGettingAllEntityItemsForWhom(Ent.DRIVE_FILE_OR_FOLDER, user, i, count, query=query)
  try:
    files = _getMain().callGAPIpages(drive.files(), 'list', 'files',
                          pageMessage=_getMain().getPageMessageForWhom(),
                          throwReasons=GAPI.DRIVE_USER_THROW_REASONS+[GAPI.INVALID_QUERY, GAPI.INVALID,
                                                                      GAPI.BAD_REQUEST, GAPI.FILE_NOT_FOUND,
                                                                      GAPI.NOT_FOUND, GAPI.TEAMDRIVE_MEMBERSHIP_REQUIRED],
                          retryReasons=[GAPI.UNKNOWN_ERROR],
                          q=query, orderBy=orderBy, fields='nextPageToken,files(id,driveId)', pageSize=GC.Values[GC.DRIVE_MAX_RESULTS], **kwargs)
    if files or not parentQuery:
      return [f_file['id'] for f_file in files if not sharedDriveOnly or f_file.get('driveId')]
    if emptyQueryOK:
      return []
    _getMain().entityActionNotPerformedWarning([Ent.USER, user, Ent.DRIVE_FILE_OR_FOLDER, None],
                                    _getMain().emptyQuery(query, Ent.DRIVE_FILE_OR_FOLDER if not parentQuery else Ent.DRIVE_PARENT_FOLDER), i, count)
  except (GAPI.invalidQuery, GAPI.invalid, GAPI.badRequest):
    _getMain().entityActionFailedWarning([Ent.USER, user, Ent.DRIVE_FILE_OR_FOLDER, None], _getMain().invalidQuery(query), i, count)
  except GAPI.fileNotFound:
    _getMain().printGotEntityItemsForWhom(0)
    if emptyQueryOK:
      return []
  except (GAPI.notFound, GAPI.teamDriveMembershipRequired) as e:
    _getMain().entityActionFailedWarning([Ent.USER, user, Ent.SHAREDDRIVE_ID, kwargs['driveId']], str(e), i, count)
  except (GAPI.serviceNotAvailable, GAPI.authError, GAPI.domainPolicy) as e:
    _getMain().userDriveServiceNotEnabledWarning(user, str(e), i, count)
  return None

def doSharedDriveSearch(drive, user, i, count, query, useDomainAdminAccess):
  if GC.Values[GC.SHOW_GETTINGS]:
    _getMain().printGettingAllEntityItemsForWhom(Ent.SHAREDDRIVE, user, i, count, query=query)
  try:
    files = _getMain().callGAPIpages(drive.drives(), 'list', 'drives',
                          pageMessage=_getMain().getPageMessageForWhom(),
                          throwReasons=GAPI.DRIVE_USER_THROW_REASONS+[GAPI.INVALID_QUERY, GAPI.INVALID,
                                                                      GAPI.QUERY_REQUIRES_ADMIN_CREDENTIALS,
                                                                      GAPI.NO_LIST_TEAMDRIVES_ADMINISTRATOR_PRIVILEGE,
                                                                      GAPI.INSUFFICIENT_ADMINISTRATOR_PRIVILEGES],
                          q=query, useDomainAdminAccess=useDomainAdminAccess,
                          fields='nextPageToken,drives(id)', pageSize=100)
    if files:
      return [f_file['id'] for f_file in files]
    _getMain().entityActionNotPerformedWarning([Ent.USER, user, Ent.DRIVE_FILE, None], _getMain().emptyQuery(query, Ent.SHAREDDRIVE), i, count)
  except (GAPI.invalidQuery, GAPI.invalid):
    _getMain().entityActionFailedWarning([Ent.USER, user, Ent.SHAREDDRIVE, None], _getMain().invalidQuery(query), i, count)
  except (GAPI.queryRequiresAdminCredentials, GAPI.noListTeamDrivesAdministratorPrivilege, GAPI.insufficientAdministratorPrivileges) as e:
    _getMain().entityActionFailedWarning([Ent.USER, user, Ent.SHAREDDRIVE, None], str(e), i, count)
  except (GAPI.serviceNotAvailable, GAPI.authError, GAPI.domainPolicy) as e:
    _getMain().userDriveServiceNotEnabledWarning(user, str(e), i, count)
  return None

def _getFileIdFromURL(fileId):
  loc = fileId.find('/d/')
  if loc > 0:
    fileId = fileId[loc+3:]
    loc = fileId.find('/')
    return fileId[:loc] if loc != -1 else fileId
  loc = fileId.find('?id=')
  if loc > 0:
    fileId = fileId[loc+4:]
    loc = fileId.find('&')
    return fileId[:loc] if loc != -1 else fileId
  loc = fileId.find('/files/')
  if loc > 0:
    fileId = fileId[loc+7:]
    loc = fileId.find('&')
    if loc > 0:
      return fileId[:loc]
    loc = fileId.find('?')
    return fileId[:loc] if loc != -1 else fileId
  loc = fileId.find('/folders/')
  if loc > 0:
    fileId = fileId[loc+9:]
    loc = fileId.find('&')
    if loc > 0:
      return fileId[:loc]
    loc = fileId.find('?')
    return fileId[:loc] if loc != -1 else fileId
  return None

def cleanFileIDsList(fileIdEntity, fileIds):
  fileIdEntity['list'] = []
  fileIdEntity[ROOT] = []
  i = 0
  for fileId in fileIds:
    if fileId[:8].lower() == 'https://' or fileId[:7].lower() == 'http://':
      fileId = _getFileIdFromURL(fileId)
      if fileId is None:
        continue
    elif fileId.lower() in {ROOT, ROOTID}:
      fileIdEntity[ROOT].append(i)
      fileId = fileId.lower()
    fileIdEntity['list'].append(fileId)
    i += 1

TITLE_QUERY_PATTERN = re.compile(r'title((?: *!?=)|(?: +contains))', flags=re.IGNORECASE)

def _mapDrive2QueryToDrive3(query):
  if query:
    query = TITLE_QUERY_PATTERN.sub(r'name\1', query).replace('modifiedDate', 'modifiedTime').replace('lastViewedByMeDate', 'viewedByMeTime')
    query = _getMain().mapQueryRelativeTimes(query, ['modifiedTime', 'viewedByMeTime'])
  return query

def escapeDriveFileName(filename):
  if filename.find("'") == -1 and filename.find('\\') == -1:
    return filename
  encfilename = ''
  for c in filename:
    if c == "'":
      encfilename += "\\'"
    elif c == '\\':
      encfilename += '\\\\'
    else:
      encfilename += c
  return encfilename

def getEscapedDriveFileName():
  return escapeDriveFileName(_getMain().getString(Cmd.OB_DRIVE_FILE_NAME))

def getEscapedDriveFolderName():
  return escapeDriveFileName(_getMain().getString(Cmd.OB_DRIVE_FOLDER_NAME))

def initDriveFileEntity():
  return {'list': [], 'shareddrivename': None, 'shareddriveadminquery': None, 'shareddrivefilequery': None,
          'query': None, 'dict': None, ROOT: [], 'shareddrive': {},
          'location': None, 'nonDomainAdminAccess': False}

DRIVE_BY_NAME_CHOICE_MAP = {
  'anyname': WITH_ANY_FILE_NAME,
  'anydrivefilename': WITH_ANY_FILE_NAME,
  'anyownername': WITH_ANY_FILE_NAME,
  'anyownerdrivefilename': WITH_ANY_FILE_NAME,
  'sharedname': WITH_ANY_FILE_NAME,
  'shareddrivefilename': WITH_ANY_FILE_NAME,
  'name': WITH_MY_FILE_NAME,
  'drivefilename': WITH_MY_FILE_NAME,
  'othername': WITH_OTHER_FILE_NAME,
  'otherdrivefilename': WITH_ANY_FILE_NAME,
  }

LOCATION_ALL_DRIVES = 0
LOCATION_MYDRIVE = 1
LOCATION_ORPHANS = 2
LOCATION_OWNEDBY_ANY = 3
LOCATION_OWNEDBY_OTHERS = 4
LOCATION_SHARED_WITHME = 5
LOCATION_ONLY_SHARED_DRIVES = 6

LOCATION_CHOICE_MAP = {
  'alldrives': {'fileids': [ROOT, ORPHANS, SHARED_WITHME, SHARED_DRIVES], 'owner': None, 'location': LOCATION_ALL_DRIVES, 'setShowOwnedBy': True},
  'root': {'fileids': [ROOT], 'owner': True, 'location': LOCATION_MYDRIVE, 'setShowOwnedBy': False},
  'rootwithorphans': {'fileids': [ROOT, ORPHANS], 'owner': True, 'location': LOCATION_MYDRIVE, 'setShowOwnedBy': False},
  'mydrive': {'fileids': [ROOT], 'owner': True, 'location': LOCATION_MYDRIVE, 'setShowOwnedBy': False},
  'mydrivewithorphans': {'fileids': [ROOT, ORPHANS], 'owner': True, 'location': LOCATION_MYDRIVE, 'setShowOwnedBy': False},
  'mydriveany': {'fileids': [ROOT, ORPHANS], 'owner': None, 'location': LOCATION_MYDRIVE, 'setShowOwnedBy': True},
  'mydriveme': {'fileids': [ROOT, ORPHANS], 'owner': True, 'location': LOCATION_MYDRIVE, 'setShowOwnedBy': True},
  'mydriveothers': {'fileids': [ROOT], 'owner': False, 'location': LOCATION_MYDRIVE, 'setShowOwnedBy': True},
  'onlyshareddrives': {'fileids': [SHARED_DRIVES], 'owner': False, 'location': LOCATION_ONLY_SHARED_DRIVES, 'setShowOwnedBy': True},
  'onlyteamdrives': {'fileids': [SHARED_DRIVES], 'owner': False, 'location': LOCATION_ONLY_SHARED_DRIVES, 'setShowOwnedBy': True},
  'orphans': {'fileids': [ORPHANS], 'owner': True, 'location': LOCATION_ORPHANS, 'setShowOwnedBy': True},
  'ownedbyany': {'fileids': [ROOT, ORPHANS, SHARED_WITHME], 'owner': None, 'location': LOCATION_OWNEDBY_ANY, 'setShowOwnedBy': True},
  'ownedbyme': {'fileids': [ROOT, ORPHANS, SHARED_WITHME], 'owner': True, 'location': LOCATION_MYDRIVE, 'setShowOwnedBy': True},
  'ownedbyothers': {'fileids': [ROOT, ORPHANS, SHARED_WITHME], 'owner': False, 'location': LOCATION_OWNEDBY_OTHERS, 'setShowOwnedBy': True},
  'sharedwithme': {'fileids': [ROOT, SHARED_WITHME], 'owner': False, 'location': LOCATION_OWNEDBY_OTHERS, 'setShowOwnedBy': True},
  'sharedwithmemydrive': {'fileids': [ROOT], 'owner': False, 'location': LOCATION_MYDRIVE, 'setShowOwnedBy': True},
  'sharedwithmenotmydrive': {'fileids': [SHARED_WITHME], 'owner': False, 'location': LOCATION_SHARED_WITHME, 'setShowOwnedBy': True},
  }

def getDriveFileEntity(queryShortcutsOK=True, DLP=None):
  def _getKeywordColonValue(kwColonValue):
    kw, value = kwColonValue.split(':', 1)
    kw = kw.lower().replace('_', '').replace('-', '')
    if kw == 'id':
      cleanFileIDsList(fileIdEntity, [value])
    elif kw == 'ids':
      cleanFileIDsList(fileIdEntity, value.replace(',', ' ').split())
    elif kw == 'query':
      fileIdEntity['query'] = _mapDrive2QueryToDrive3(value)
      fileIdEntity['nonDomainAdminAccess'] = True
    elif kw in DRIVE_BY_NAME_CHOICE_MAP:
      fileIdEntity['query'] = DRIVE_BY_NAME_CHOICE_MAP[kw].format(escapeDriveFileName(value))
      fileIdEntity['nonDomainAdminAccess'] = True
    else:
      return False
    return True

  def _getTDKeywordColonValue(kwColonValue):
    kw, value = kwColonValue.split(':', 1)
    kw = kw.lower().replace('_', '').replace('-', '')
    if kw in {'teamdriveid', 'shareddriveid'}:
      fileIdEntity['shareddrive']['driveId'] = value
    elif kw in {'teamdrive', 'shareddrive'}:
      fileIdEntity['shareddrivename'] = value
    elif kw in {'teamdriveadminquery', 'shareddriveadminquery'}:
      fileIdEntity['shareddriveadminquery'] = value
    elif kw in {'teamdrivefilename', 'shareddrivefilename'}:
      fileIdEntity['shareddrivefilequery'] = WITH_ANY_FILE_NAME.format(escapeDriveFileName(value))
    elif kw in {'teamdrivequery', 'shareddrivequery'}:
      fileIdEntity['shareddrivefilequery'] = _mapDrive2QueryToDrive3(value)
    else:
      return False
    return True

  fileIdEntity = initDriveFileEntity()
  entitySelector = _getMain().getEntitySelector()
  if entitySelector:
    entityList = _getMain().getEntitySelection(entitySelector, False)
    if isinstance(entityList, dict):
      fileIdEntity['dict'] = entityList
    else:
      cleanFileIDsList(fileIdEntity, entityList)
    return fileIdEntity
  fileIdEntity['location'] = Cmd.Location()
  myarg = _getMain().getString(Cmd.OB_DRIVE_FILE_ID, checkBlank=True)
  mycmd = myarg.lower().replace('_', '').replace('-', '')
  if mycmd == 'id':
    cleanFileIDsList(fileIdEntity, _getMain().getStringReturnInList(Cmd.OB_DRIVE_FILE_ID))
  elif mycmd == 'ids':
    cleanFileIDsList(fileIdEntity, _getMain().getString(Cmd.OB_DRIVE_FILE_ID).replace(',', ' ').split())
  elif mycmd == 'query':
    fileIdEntity['query'] = _mapDrive2QueryToDrive3(_getMain().getString(Cmd.OB_QUERY))
    fileIdEntity['nonDomainAdminAccess'] = True
  elif queryShortcutsOK and mycmd in QUERY_SHORTCUTS_MAP:
    fileIdEntity['query'] = QUERY_SHORTCUTS_MAP[mycmd]
    fileIdEntity['nonDomainAdminAccess'] = True
  elif mycmd in DRIVE_BY_NAME_CHOICE_MAP:
    fileIdEntity['query'] = DRIVE_BY_NAME_CHOICE_MAP[mycmd].format(getEscapedDriveFileName())
    fileIdEntity['nonDomainAdminAccess'] = True
  elif mycmd in {'rootid', 'mydriveid'}:
    cleanFileIDsList(fileIdEntity, [ROOTID])
    fileIdEntity['nonDomainAdminAccess'] = True
  elif not DLP and mycmd in {'root', 'mydrive'}:
    cleanFileIDsList(fileIdEntity, [ROOT])
    fileIdEntity['nonDomainAdminAccess'] = True
  elif DLP and mycmd in LOCATION_CHOICE_MAP:
    DLP.SetLocation(LOCATION_CHOICE_MAP[mycmd])
    cleanFileIDsList(fileIdEntity, DLP.locationFileIds)
    fileIdEntity['nonDomainAdminAccess'] = True
  elif mycmd.startswith('teamdrive') or mycmd.startswith('shareddrive'):
    fileIdEntity['shareddrive'] = {'driveId': None,
                                   'corpora': 'drive', 'includeItemsFromAllDrives': True, 'supportsAllDrives': True}
    while True:
      if mycmd in {'teamdriveid', 'shareddriveid'}:
        fileIdEntity['shareddrive']['driveId'] = _getMain().getString(Cmd.OB_SHAREDDRIVE_ID).strip()
      elif mycmd in {'teamdrive', 'shareddrive'}:
        fileIdEntity['shareddrivename'] = _getMain().getString(Cmd.OB_SHAREDDRIVE_NAME)
      elif mycmd in {'teamdriveadminquery', 'shareddriveadminquery'}:
        fileIdEntity['shareddriveadminquery'] = _getMain().getString(Cmd.OB_QUERY)
      elif mycmd in {'teamdrivefilename', 'shareddrivefilename'}:
        fileIdEntity['shareddrivefilequery'] = WITH_ANY_FILE_NAME.format(getEscapedDriveFileName())
      elif mycmd in {'teamdrivequery', 'shareddrivequery'}:
        fileIdEntity['shareddrivefilequery'] = _mapDrive2QueryToDrive3(_getMain().getString(Cmd.OB_QUERY))
      elif queryShortcutsOK and mycmd in SHAREDDRIVE_QUERY_SHORTCUTS_MAP:
        fileIdEntity['shareddrivefilequery'] = SHAREDDRIVE_QUERY_SHORTCUTS_MAP[mycmd]
      elif (mycmd.find(':') > 0) and _getTDKeywordColonValue(myarg):
        pass
      else:
        _getMain().unknownArgumentExit()
      if Cmd.ArgumentsRemaining():
        myarg = _getMain().getString(Cmd.OB_STRING)
        mycmd = myarg.lower().replace('_', '').replace('-', '')
        if (mycmd.startswith('teamdriveparent') or mycmd.startswith('shareddriveparent') or
            ((not (mycmd.startswith('teamdrive') or mycmd.startswith('shareddrive'))) and
             (not (queryShortcutsOK and mycmd in SHAREDDRIVE_QUERY_SHORTCUTS_MAP)))):
          Cmd.Backup()
          break
      else:
        break
    if not fileIdEntity['shareddrive'].get('driveId'):
      fileIdEntity['shareddrive']['corpora'] = CORPORA_ALL_DRIVES
  elif (mycmd.find(':') > 0) and _getKeywordColonValue(myarg):
    pass
  else:
    cleanFileIDsList(fileIdEntity, [myarg])
  return fileIdEntity

def getDriveFileEntitySharedDriveOnly():
  def _getTDKeywordColonValue(kwColonValue):
    kw, value = kwColonValue.split(':', 1)
    kw = kw.lower().replace('_', '').replace('-', '')
    if kw in {'teamdriveid', 'shareddriveid'}:
      fileIdEntity['shareddrive']['driveId'] = value
    elif kw in {'teamdrive', 'shareddrive'}:
      fileIdEntity['shareddrivename'] = value
    elif kw in {'teamdriveadminquery', 'shareddriveadminquery'}:
      fileIdEntity['shareddriveadminquery'] = value
    else:
      return False
    return True

  fileIdEntity = initDriveFileEntity()
  myarg = _getMain().getString(Cmd.OB_DRIVE_FILE_ID, checkBlank=True)
  mycmd = myarg.lower().replace('_', '').replace('-', '')
  if mycmd.startswith('teamdrive') or mycmd.startswith('shareddrive'):
    fileIdEntity['shareddrive'] = {'driveId': None,
                                 'corpora': 'drive', 'includeItemsFromAllDrives': True, 'supportsAllDrives': True}
    if mycmd in {'teamdriveid', 'shareddriveid'}:
      fileIdEntity['shareddrive']['driveId'] = _getMain().getString(Cmd.OB_SHAREDDRIVE_ID)
    elif mycmd in {'teamdrive', 'shareddrive'}:
      fileIdEntity['shareddrivename'] = _getMain().getString(Cmd.OB_SHAREDDRIVE_NAME)
    elif mycmd in {'teamdriveadminquery', 'shareddriveadminquery'}:
      fileIdEntity['shareddriveadminquery'] = _getMain().getString(Cmd.OB_QUERY)
    elif (mycmd.find(':') > 0) and _getTDKeywordColonValue(myarg):
      pass
    else:
      _getMain().unknownArgumentExit()
    if not fileIdEntity['shareddrive'].get('driveId'):
      fileIdEntity['shareddrive']['corpora'] = CORPORA_ALL_DRIVES
  elif (mycmd.find(':') > 0) and _getTDKeywordColonValue(myarg):
    pass
  else:
    _getMain().unknownArgumentExit()
  return fileIdEntity

def getSharedDriveEntity():
  def _getTDKeywordColonValue(kwColonValue):
    kw, value = kwColonValue.split(':', 1)
    kw = kw.lower().replace('_', '').replace('-', '')
    if kw in {'teamdriveid', 'shareddriveid'}:
      fileIdEntity['shareddrive']['driveId'] = value
    elif kw in {'teamdrive', 'shareddrive', 'name'}:
      fileIdEntity['shareddrivename'] = value
    else:
      return False
    return True

  fileIdEntity = initDriveFileEntity()
  myarg = _getMain().getString(Cmd.OB_DRIVE_FILE_ID, checkBlank=True)
  mycmd = myarg.lower().replace('_', '').replace('-', '')
  fileIdEntity['shareddrive'] = {'driveId': None,
                               'corpora': 'drive', 'includeItemsFromAllDrives': True, 'supportsAllDrives': True}
  if mycmd in {'teamdriveid', 'shareddriveid'}:
    fileIdEntity['shareddrive']['driveId'] = _getMain().getString(Cmd.OB_SHAREDDRIVE_ID)
  elif mycmd in {'teamdrive', 'shareddrive', 'name'}:
    fileIdEntity['shareddrivename'] = _getMain().getString(Cmd.OB_SHAREDDRIVE_NAME)
  elif (mycmd.find(':') > 0) and _getTDKeywordColonValue(myarg):
    pass
  else:
    fileIdEntity['shareddrive']['driveId'] = myarg
  return fileIdEntity

def _convertSharedDriveNameToId(drive, user, i, count, fileIdEntity, useDomainAdminAccess=False):
  try:
    if "\\'" in fileIdEntity['shareddrivename']:
      name = fileIdEntity['shareddrivename']
    else:
      name = fileIdEntity['shareddrivename'].replace("'", "\\'")
    tdlist = _getMain().callGAPIpages(drive.drives(), 'list', 'drives',
                           throwReasons=GAPI.DRIVE_USER_THROW_REASONS+[GAPI.INVALID_QUERY, GAPI.INVALID,
                                                                       GAPI.QUERY_REQUIRES_ADMIN_CREDENTIALS,
                                                                       GAPI.NO_LIST_TEAMDRIVES_ADMINISTRATOR_PRIVILEGE,
                                                                       GAPI.INSUFFICIENT_ADMINISTRATOR_PRIVILEGES,
                                                                       GAPI.FILE_NOT_FOUND],
                           useDomainAdminAccess=useDomainAdminAccess,
                           q=f"name='{name}'",
                           fields='nextPageToken,drives(id,name)', pageSize=100)
    if "\\'" in fileIdEntity['shareddrivename']:
      fileIdEntity['shareddrivename'] = fileIdEntity['shareddrivename'].replace("\\'", "'")
    if not tdlist:
      name = fileIdEntity['shareddrivename'].lower()
      feed = _getMain().callGAPIpages(drive.drives(), 'list', 'drives',
                           throwReasons=GAPI.DRIVE_USER_THROW_REASONS+[GAPI.NO_LIST_TEAMDRIVES_ADMINISTRATOR_PRIVILEGE,
                                                                       GAPI.INSUFFICIENT_ADMINISTRATOR_PRIVILEGES],
                           useDomainAdminAccess=useDomainAdminAccess,
                           fields='nextPageToken,drives(id,name)', pageSize=100)
      tdlist = [td for td in feed if td['name'].lower() == name]
  except (GAPI.serviceNotAvailable, GAPI.authError, GAPI.domainPolicy):
    _getMain().entityActionFailedWarning([Ent.USER, user, Ent.SHAREDDRIVE_NAME, fileIdEntity['shareddrivename']], Msg.DOES_NOT_EXIST, i, count)
    return False
  except (GAPI.invalidQuery, GAPI.invalid, GAPI.queryRequiresAdminCredentials,
          GAPI.noListTeamDrivesAdministratorPrivilege, GAPI.insufficientAdministratorPrivileges,
          GAPI.fileNotFound) as e:
    _getMain().entityActionFailedWarning([Ent.USER, user, Ent.SHAREDDRIVE_NAME, fileIdEntity['shareddrivename']], str(e), i, count)
    return False
  jcount = len(tdlist)
  if jcount == 1:
    fileIdEntity['shareddrive']['driveId'] = tdlist[0]['id']
    return True
  if jcount == 0:
    _getMain().entityActionFailedWarning([Ent.USER, user, Ent.SHAREDDRIVE_NAME, fileIdEntity['shareddrivename']], Msg.DOES_NOT_EXIST, i, count)
  else:
    _getMain().entityActionFailedWarning([Ent.USER, user, Ent.SHAREDDRIVE_NAME, fileIdEntity['shareddrivename']],
                              Msg.MULTIPLE_ENTITIES_FOUND.format(Ent.Plural(Ent.SHAREDDRIVE_ID), jcount,
                                                                 ','.join([td['id'] for td in tdlist])), i, count)
  return False

def _getSharedDriveNameFromId(drive, sharedDriveId, useDomainAdminAccess=False):
  sharedDriveName = GM.Globals[GM.MAP_SHAREDDRIVE_ID_TO_NAME].get(sharedDriveId)
  if not sharedDriveName:
    try:
      sharedDriveName = _getMain().callGAPI(drive.drives(), 'get',
                                 throwReasons=GAPI.DRIVE_USER_THROW_REASONS+[GAPI.FILE_NOT_FOUND, GAPI.NOT_FOUND],
                                 useDomainAdminAccess=useDomainAdminAccess,
                                 driveId=sharedDriveId, fields='name')['name']
    except (GAPI.fileNotFound, GAPI.notFound, GAPI.serviceNotAvailable, GAPI.authError, GAPI.domainPolicy):
      sharedDriveName = _getMain().TEAM_DRIVE
    GM.Globals[GM.MAP_SHAREDDRIVE_ID_TO_NAME][sharedDriveId] = sharedDriveName
  return sharedDriveName

def _getDriveFileNameFromId(drive, fileId, combineTitleId=True, useDomainAdminAccess=False):
  try:
    result = _getMain().callGAPI(drive.files(), 'get',
                      throwReasons=GAPI.DRIVE_ACCESS_THROW_REASONS,
                      fileId=fileId, fields='name,mimeType,driveId', supportsAllDrives=True)
    if result:
      fileName = result['name']
      if (result['mimeType'] == MIMETYPE_GA_FOLDER) and result.get('driveId') and (result['name'] == _getMain().TEAM_DRIVE):
        fileName = _getSharedDriveNameFromId(drive, result['driveId'])
      if combineTitleId:
        fileName += '('+fileId+')'
      return (fileName, _getMain()._getEntityMimeType(result), result['mimeType'])
  except GAPI.fileNotFound:
    if useDomainAdminAccess:
      try:
        result = _getMain().callGAPI(drive.drives(), 'get',
                          throwReasons=GAPI.DRIVE_USER_THROW_REASONS+[GAPI.FILE_NOT_FOUND, GAPI.NOT_FOUND],
                          useDomainAdminAccess=useDomainAdminAccess,
                          driveId=fileId, fields='name')
        if result:
          fileName = result['name']
          if combineTitleId:
            fileName += '('+fileId+')'
          return (fileName, Ent.DRIVE_FOLDER, MIMETYPE_GA_FOLDER)
      except (GAPI.fileNotFound, GAPI.notFound):
        pass
  except (GAPI.forbidden, GAPI.internalError, GAPI.insufficientFilePermissions, GAPI.internalError,
          GAPI.serviceNotAvailable, GAPI.authError, GAPI.domainPolicy):
    pass
  return (fileId, Ent.DRIVE_FILE_OR_FOLDER_ID, None)

def _simpleFileIdEntityList(fileIdEntityList):
  for fileId in fileIdEntityList:
    if fileId not in {ROOT, ORPHANS, SHARED_WITHME, SHARED_DRIVES}:
      return False
  return True

def _validateUserGetFileIDs(user, i, count, fileIdEntity, drive=None, entityType=None, orderBy=None, useDomainAdminAccess=False):
  def _identifyRoot():
    try:
      rootFolderId = _getMain().callGAPI(drive.files(), 'get',
                              throwReasons=GAPI.DRIVE_USER_THROW_REASONS,
                              fileId=ROOT, fields='id')['id']
      for j in fileIdEntity[ROOT]:
        fileIdEntity['list'][j] = rootFolderId
      return True
    except (GAPI.serviceNotAvailable, GAPI.authError, GAPI.domainPolicy) as e:
      _getMain().userDriveServiceNotEnabledWarning(user, str(e), i, count)
      return False

  if fileIdEntity['dict']:
    cleanFileIDsList(fileIdEntity, fileIdEntity['dict'][user])
  if not drive:
    user, drive = _getMain().buildGAPIServiceObject(API.DRIVE3, user, i, count)
    if not drive:
      return (user, None, 0)
  else:
    user = _getMain().convertUIDtoEmailAddress(user)
  if fileIdEntity['list'] and _simpleFileIdEntityList(fileIdEntity['list']):
    l = len(fileIdEntity['list'])
    if ROOT in fileIdEntity['list'] and fileIdEntity[ROOT]:
      if not _identifyRoot():
        return (user, None, 0)
    if entityType:
      _getMain().entityPerformActionNumItems([Ent.USER, user], l, entityType, i, count)
    return (user, drive, l)
  if fileIdEntity['shareddrivename'] and 'driveId' not in fileIdEntity:
    if not _convertSharedDriveNameToId(drive, user, i, count, fileIdEntity, useDomainAdminAccess):
      return (user, None, 0)
    if not fileIdEntity['shareddrivefilequery']:
      fileIdEntity['list'] = [fileIdEntity['shareddrive']['driveId']]
    fileIdEntity['shareddrive']['corpora'] = 'drive'
  elif fileIdEntity['shareddrive'].get('driveId'):
    if not fileIdEntity['shareddrivefilequery']:
      fileIdEntity['list'] = [fileIdEntity['shareddrive']['driveId']]
    fileIdEntity['shareddrive']['corpora'] = 'drive'
  if fileIdEntity['query']:
    fileIdEntity['list'] = doDriveSearch(drive, user, i, count, query=fileIdEntity['query'], orderBy=orderBy)
    if fileIdEntity['list'] is None:
      _getMain().setSysExitRC(_getMain().NO_ENTITIES_FOUND_RC)
      return (user, None, 0)
  elif fileIdEntity['shareddriveadminquery']:
    fileIdEntity['list'] = doSharedDriveSearch(drive, user, i, count, fileIdEntity['shareddriveadminquery'], useDomainAdminAccess)
    if fileIdEntity['list'] is None:
      _getMain().setSysExitRC(_getMain().NO_ENTITIES_FOUND_RC)
      return (user, None, 0)
  elif fileIdEntity['shareddrivefilequery']:
    if not fileIdEntity['shareddrive'].get('driveId'):
      fileIdEntity['shareddrive']['corpora'] = CORPORA_ALL_DRIVES
    fileIdEntity['list'] = doDriveSearch(drive, user, i, count, query=fileIdEntity['shareddrivefilequery'], orderBy=orderBy, sharedDriveOnly=True, **fileIdEntity['shareddrive'])
    if fileIdEntity['list'] is None or not fileIdEntity['list']:
      _getMain().setSysExitRC(_getMain().NO_ENTITIES_FOUND_RC)
      return (user, None, 0)
    fileIdEntity['shareddrive'].pop('driveId', None)
    fileIdEntity['shareddrive'].pop('corpora', None)
  elif fileIdEntity[ROOT]:
    if not _identifyRoot():
      return (user, None, 0)
  l = len(fileIdEntity['list'])
  if l == 0:
    _getMain().setSysExitRC(_getMain().NO_ENTITIES_FOUND_RC)
  if entityType:
    _getMain().entityPerformActionNumItems([Ent.USER, user], l, entityType, i, count)
  return (user, drive, l)

# Disc File Access paramaters
DFA_CREATED_TIME = 'createdTime'
DFA_MODIFIED_TIME = 'modifiedTime'
DFA_PRESERVE_FILE_TIMES = 'preserveFileTimes'
DFA_IGNORE_DEFAULT_VISIBILITY = 'ignoreDefaultVisibility'
DFA_KEEP_REVISION_FOREVER = 'keepRevisionForever'
DFA_URL = 'url'
DFA_LOCALFILEPATH = 'localFilepath'
DFA_LOCALFILENAME = 'localFilename'
DFA_LOCALMIMETYPE = 'localMimeType'
DFA_STRIPNAMEPREFIX = 'stripNamePrefix'
DFA_REPLACEFILENAME = 'replaceFileName'
DFA_OCRLANGUAGE = 'ocrLanguage'
DFA_PARENTID = 'parentId'
DFA_PARENTQUERY = 'parentQuery'
DFA_ADD_PARENT_IDS = 'addParentIds'
DFA_ADD_PARENT_NAMES = 'addParentNames'
DFA_REMOVE_PARENT_IDS = 'removeParentIds'
DFA_REMOVE_PARENT_NAMES = 'removeParentNames'
DFA_SHAREDDRIVE_PARENT = 'sharedDriveParent'
DFA_SHAREDDRIVE_PARENTID = 'sharedDriveParentId'
DFA_SHAREDDRIVE_PARENTQUERY = 'sharedDriveParentQuery'
DFA_KWARGS = 'kwargs'
DFA_SEARCHARGS = 'searchargs'
DFA_USE_CONTENT_AS_INDEXABLE_TEXT = 'useContentAsIndexableText'
DFA_TIMESTAMP = 'timestamp'
DFA_TIMEFORMAT = 'timeformat'

def _driveFileParentSpecified(parameters):
  return (parameters[DFA_PARENTID] or parameters[DFA_PARENTQUERY] or
          parameters[DFA_SHAREDDRIVE_PARENT] or parameters[DFA_SHAREDDRIVE_PARENTID] or
          parameters[DFA_SHAREDDRIVE_PARENTQUERY])

def _getDriveFileParentInfo(drive, user, i, count, body, parameters, emptyQueryOK=False, defaultToRoot=True, entityType=Ent.DRIVE_FILE):
  def _setSearchArgs(driveId):
    parameters[DFA_SEARCHARGS] = {'driveId': driveId, 'corpora': 'drive',
                                  'includeItemsFromAllDrives': True, 'supportsAllDrives': True}
  body.pop('parents', None)
  if parameters[DFA_PARENTID]:
    body.setdefault('parents', [])
    try:
      result = _getMain().callGAPI(drive.files(), 'get',
                        throwReasons=GAPI.DRIVE_USER_THROW_REASONS+[GAPI.FILE_NOT_FOUND],
                        fileId=parameters[DFA_PARENTID], fields='id,name,mimeType,driveId', supportsAllDrives=True)
      if result['mimeType'] != MIMETYPE_GA_FOLDER:
        _getMain().entityActionNotPerformedWarning([Ent.USER, user, entityType, None],
                                        f'parentid: {parameters[DFA_PARENTID]}, {Msg.NOT_AN_ENTITY.format((Ent.Singular(Ent.DRIVE_FOLDER)))}', i, count)
        return False
      body['parents'].append(result['id'])
      if result.get('driveId'):
        _setSearchArgs(result['driveId'])
    except GAPI.fileNotFound as e:
      _getMain().entityActionNotPerformedWarning([Ent.USER, user, entityType, None],
                                      f'parentid: {parameters[DFA_PARENTID]}, {str(e)}', i, count)
      return False
    except (GAPI.serviceNotAvailable, GAPI.authError, GAPI.domainPolicy) as e:
      _getMain().userDriveServiceNotEnabledWarning(user, str(e), i, count)
      return False
  if parameters[DFA_PARENTQUERY]:
    parents = doDriveSearch(drive, user, i, count, query=parameters[DFA_PARENTQUERY], parentQuery=True, emptyQueryOK=emptyQueryOK)
    if parents is None:
      _getMain().setSysExitRC(_getMain().NO_ENTITIES_FOUND_RC)
      return False
    body.setdefault('parents', [])
    for parent in parents:
      body['parents'].append(parent)
  if parameters[DFA_SHAREDDRIVE_PARENTID]:
    try:
      if not parameters[DFA_SHAREDDRIVE_PARENTQUERY]:
        body.setdefault('parents', [])
        result = _getMain().callGAPI(drive.files(), 'get',
                          throwReasons=GAPI.DRIVE_USER_THROW_REASONS+[GAPI.FILE_NOT_FOUND],
                          fileId=parameters[DFA_SHAREDDRIVE_PARENTID], fields='id,mimeType,driveId', supportsAllDrives=True)
        if result['mimeType'] != MIMETYPE_GA_FOLDER:
          _getMain().entityActionNotPerformedWarning([Ent.USER, user, entityType, None],
                                          f'shareddriveparentid: {parameters[DFA_SHAREDDRIVE_PARENTID]}, {Msg.NOT_AN_ENTITY.format(Ent.Singular(Ent.DRIVE_FOLDER))}', i, count)
          return False
        if not result.get('driveId'):
          _getMain().entityActionNotPerformedWarning([Ent.USER, user, entityType, None],
                                          f'shareddriveparentid: {parameters[DFA_SHAREDDRIVE_PARENTID]}, {Msg.NOT_AN_ENTITY.format(Ent.Singular(Ent.SHAREDDRIVE_FOLDER))}', i, count)
          return False
        body['parents'].append(result['id'])
        _setSearchArgs(result['driveId'])
      else:
        result = _getMain().callGAPI(drive.drives(), 'get',
                          throwReasons=GAPI.DRIVE_USER_THROW_REASONS+[GAPI.FILE_NOT_FOUND, GAPI.NOT_FOUND],
                          driveId=parameters[DFA_SHAREDDRIVE_PARENTID], fields='id')
        parameters[DFA_KWARGS]['corpora'] = 'drive'
        parameters[DFA_KWARGS]['driveId'] = result['id']
        _setSearchArgs(result['id'])
    except (GAPI.fileNotFound, GAPI.notFound) as e:
      _getMain().entityActionNotPerformedWarning([Ent.USER, user, entityType, None],
                                      f'shareddriveparentid: {parameters[DFA_SHAREDDRIVE_PARENTID]}, {str(e)}', i, count)
      return False
    except (GAPI.serviceNotAvailable, GAPI.authError, GAPI.domainPolicy) as e:
      _getMain().userDriveServiceNotEnabledWarning(user, str(e), i, count)
      return False
  if parameters[DFA_SHAREDDRIVE_PARENT]:
    tempIdEntity = {'shareddrivename': parameters[DFA_SHAREDDRIVE_PARENT], 'shareddrive': {}}
    if not _convertSharedDriveNameToId(drive, user, i, count, tempIdEntity):
      return False
    if not parameters[DFA_SHAREDDRIVE_PARENTQUERY]:
      body.setdefault('parents', [])
      body['parents'].append(tempIdEntity['shareddrive']['driveId'])
    else:
      parameters[DFA_KWARGS]['corpora'] = 'drive'
      parameters[DFA_KWARGS]['driveId'] = tempIdEntity['shareddrive']['driveId']
    _setSearchArgs(tempIdEntity['shareddrive']['driveId'])
  if parameters[DFA_SHAREDDRIVE_PARENTQUERY]:
    parents = doDriveSearch(drive, user, i, count, query=parameters[DFA_SHAREDDRIVE_PARENTQUERY], parentQuery=True, emptyQueryOK=emptyQueryOK,
                            sharedDriveOnly=True, **parameters[DFA_KWARGS])
    if parents is None:
      _getMain().setSysExitRC(_getMain().NO_ENTITIES_FOUND_RC)
      return False
    body.setdefault('parents', [])
    for parent in parents:
      body['parents'].append(parent)
  if defaultToRoot and ('parents' not in body or not body['parents']):
    body['parents'] = [ROOT]
  numParents = len(body.get('parents', []))
  if numParents > 1:
    _getMain().entityActionNotPerformedWarning([Ent.USER, user, entityType, None],
                                    Msg.MULTIPLE_PARENTS_SPECIFIED.format(numParents), i, count)
    return False
  return True

def _getDriveFileAddRemoveParentInfo(user, i, count, parameters, drive):
  addParents = parameters[DFA_ADD_PARENT_IDS][:]
  for query in parameters[DFA_ADD_PARENT_NAMES]:
    parents = doDriveSearch(drive, user, i, count, query=query, parentQuery=True)
    if parents is None:
      _getMain().setSysExitRC(_getMain().NO_ENTITIES_FOUND_RC)
      return (False, None, None)
    addParents.extend(parents)
  removeParents = parameters[DFA_REMOVE_PARENT_IDS][:]
  for query in parameters[DFA_REMOVE_PARENT_NAMES]:
    parents = doDriveSearch(drive, user, i, count, query=query, parentQuery=True)
    if parents is None:
      _getMain().setSysExitRC(_getMain().NO_ENTITIES_FOUND_RC)
      return (False, None, None)
    removeParents.extend(parents)
  return (True, addParents, removeParents)

def _validateUserGetSharedDriveFileIDs(user, i, count, fileIdEntity, drive=None, entityType=None):
  if fileIdEntity['dict']:
    cleanFileIDsList(fileIdEntity, fileIdEntity['dict'][user])
  if not drive:
    user, drive = _getMain().buildGAPIServiceObject(API.DRIVE3, user, i, count)
    if not drive:
      return (user, None, 0)
  else:
    user = _getMain().convertUIDtoEmailAddress(user)
  if fileIdEntity.get('shareddrivename') and not _convertSharedDriveNameToId(drive, user, i, count, fileIdEntity):
    return (user, None, 0)
  if fileIdEntity['shareddrivefilequery']:
    fileIdEntity['list'] = doDriveSearch(drive, user, i, count, query=fileIdEntity['shareddrivefilequery'], sharedDriveOnly=True, **fileIdEntity['shareddrive'])
    if fileIdEntity['list'] is None or not fileIdEntity['list']:
      _getMain().setSysExitRC(_getMain().NO_ENTITIES_FOUND_RC)
      return (user, None, 0)
    fileIdEntity['shareddrive'].pop('driveId', None)
    fileIdEntity['shareddrive'].pop('corpora', None)
  l = len(fileIdEntity['list'])
  if l == 0:
    _getMain().setSysExitRC(_getMain().NO_ENTITIES_FOUND_RC)
  if entityType:
    _getMain().entityPerformActionNumItems([Ent.USER, user], l, entityType, i, count)
  return (user, drive, l)

def _validateUserSharedDrive(user, i, count, fileIdEntity, useDomainAdminAccess=False):
  user, drive = _getMain().buildGAPIServiceObject(API.DRIVE3, user, i, count)
  if not drive:
    return (user, None)
  if fileIdEntity.get('shareddrivename'):
    if not _convertSharedDriveNameToId(drive, user, i, count, fileIdEntity, useDomainAdminAccess):
      return (user, None)
    fileIdEntity['shareddrive']['corpora'] = 'drive'
  return (user, drive)

DRIVE_LABEL_CHOICE_MAP = {
  'modified': 'modifiedByMe',
  'modifiedbyme': 'modifiedByMe',
  'restrict': 'copyRequiresWriterPermission',
  'restricted': 'copyRequiresWriterPermission',
  'star': 'starred',
  'starred': 'starred',
  'trash': 'trashed',
  'trashed': 'trashed',
  'view': 'viewedByMe',
  'viewed': 'viewedByMe',
  'viewedbyme': 'viewedByMe',
  }

MIMETYPE_CHOICE_MAP = {
  'gdoc': MIMETYPE_GA_DOCUMENT,
  'gdocument': MIMETYPE_GA_DOCUMENT,
  'gdrawing': MIMETYPE_GA_DRAWING,
  'gfile': MIMETYPE_GA_FILE,
  'gfolder': MIMETYPE_GA_FOLDER,
  'gdirectory': MIMETYPE_GA_FOLDER,
  'gform': MIMETYPE_GA_FORM,
  'gfusion': MIMETYPE_GA_FUSIONTABLE,
  'gfusiontable': MIMETYPE_GA_FUSIONTABLE,
  'gjam': MIMETYPE_GA_JAM,
  'gmap': MIMETYPE_GA_MAP,
  'gpresentation': MIMETYPE_GA_PRESENTATION,
  'gscript': MIMETYPE_GA_SCRIPT,
  'gshortcut': MIMETYPE_GA_SHORTCUT,
  'g3pshortcut': MIMETYPE_GA_3P_SHORTCUT,
  'gsite': MIMETYPE_GA_SITE,
  'gsheet': MIMETYPE_GA_SPREADSHEET,
  'gspreadsheet': MIMETYPE_GA_SPREADSHEET,
  'shortcut': MIMETYPE_GA_SHORTCUT,
  }

MIMETYPE_TYPES = ['application', 'audio', 'font', 'image', 'message', 'model', 'multipart', 'text', 'video']

def validateMimeType(mimeType):
  if mimeType in MIMETYPE_CHOICE_MAP:
    return MIMETYPE_CHOICE_MAP[mimeType]
  if mimeType.startswith(APPLICATION_VND_GOOGLE_APPS):
    return mimeType
  if mimeType.find('/') > 0:
    mediaType, subType = mimeType.split('/', 1)
    if mediaType in MIMETYPE_TYPES and subType:
      return mimeType
  _getMain().invalidChoiceExit(mimeType, list(MIMETYPE_CHOICE_MAP)+[f'({formatChoiceList(MIMETYPE_TYPES)})/mediatype'], True)

def getMimeType():
  return validateMimeType(_getMain().getString(Cmd.OB_MIMETYPE).lower())

class MimeTypeCheck():

  def __init__(self):
    self.mimeTypes = set()
    self.reverse = False
    self.category = set()

  def Get(self):
    if _getMain().checkArgumentPresent('category'):
      for mimeType in _getMain().getString(Cmd.OB_MIMETYPE_LIST).lower().replace(',', ' ').split():
        if mimeType in MIMETYPE_TYPES:
          self.category.add(mimeType)
        else:
          _getMain().invalidChoiceExit(mimeType, MIMETYPE_TYPES, True)
      return
    self.reverse = _getMain().checkArgumentPresent('not')
    for mimeType in _getMain().getString(Cmd.OB_MIMETYPE_LIST).lower().replace(',', ' ').split():
      self.mimeTypes.add(validateMimeType(mimeType))

  def AddMimeTypeToQuery(self, query):
    if query:
      query += ' and ('
    else:
      query = '('
    if not self.reverse:
      for mimeType in self.mimeTypes:
        query += f"mimeType = '{mimeType}' or "
      for mimeType in self.category:
        query += f"mimeType contains '{mimeType}' or "
      query = query[:-4]
    else:
      for mimeType in self.mimeTypes:
        query += f"mimeType != '{mimeType}' and "
      query = query[:-5]
    query += ')'
    return query

  def Check(self, fileMimeType):
    if not self.mimeTypes and not self.category:
      return True
    for mimeType in self.category:
      if fileMimeType.startswith(mimeType):
        return True
    if not self.reverse:
      return fileMimeType in self.mimeTypes
    return fileMimeType not in self.mimeTypes

def initDriveFileAttributes():
  return {DFA_CREATED_TIME: None,
          DFA_MODIFIED_TIME: None,
          DFA_PRESERVE_FILE_TIMES: False,
          DFA_IGNORE_DEFAULT_VISIBILITY: False,
          DFA_KEEP_REVISION_FOREVER: False,
          DFA_URL: None,
          DFA_LOCALFILEPATH: None,
          DFA_LOCALFILENAME: None,
          DFA_LOCALMIMETYPE: None,
          DFA_STRIPNAMEPREFIX: None,
          DFA_REPLACEFILENAME: [],
          DFA_OCRLANGUAGE: None,
          DFA_PARENTID: None,
          DFA_PARENTQUERY: None,
          DFA_ADD_PARENT_IDS: [],
          DFA_ADD_PARENT_NAMES: [],
          DFA_REMOVE_PARENT_IDS: [],
          DFA_REMOVE_PARENT_NAMES: [],
          DFA_SHAREDDRIVE_PARENT: None,
          DFA_SHAREDDRIVE_PARENTID: None,
          DFA_SHAREDDRIVE_PARENTQUERY: None,
          DFA_KWARGS: {},
          DFA_SEARCHARGS: {},
          DFA_USE_CONTENT_AS_INDEXABLE_TEXT: False,
          DFA_TIMESTAMP: False,
          DFA_TIMEFORMAT: None}

DRIVEFILE_PROPERTY_VISIBILITY_CHOICE_MAP = {
  'private': 'appProperties',
  'public': 'properties'
  }

DRIVE_FILE_CONTENT_RESTRICTIONS_CHOICE_MAP = {
  'readonly': 'readOnly',
  'ownerrestricted': 'ownerRestricted',
  }

DRIVE_FILE_ITEM_DOWNLOAD_RESTRICTION_CHOICE_MAP = {
  'downloadrestrictedforreaders': 'restrictedForReaders',
  'downloadrestrictedforwriters': 'restrictedForWriters',
  'restrictedforreaders': 'restrictedForReaders',
  'restrictedforwriters': 'restrictedForWriters',
  }

def getDriveFileProperty(visibility=None):
  key = _getMain().getString(Cmd.OB_PROPERTY_KEY)
  value = _getMain().getString(Cmd.OB_PROPERTY_VALUE, minLen=0) or None
  if visibility is None:
    if Cmd.PeekArgumentPresent(list(DRIVEFILE_PROPERTY_VISIBILITY_CHOICE_MAP.keys())):
      visibility = _getMain().getChoice(DRIVEFILE_PROPERTY_VISIBILITY_CHOICE_MAP, mapChoice=True)
    else:
      visibility = 'properties'
  return {'key': key, 'value': value, 'visibility': visibility}

def getDriveFileParentAttribute(myarg, parameters):
  if myarg == 'parentid':
    parameters[DFA_PARENTID] = _getMain().getString(Cmd.OB_DRIVE_FOLDER_ID)
  elif myarg == 'parentname':
    parameters[DFA_PARENTQUERY] = _getMain().MY_NON_TRASHED_FOLDER_NAME.format(getEscapedDriveFolderName())
  elif myarg in {'anyownerparentname', 'sharedparentname'}:
    parameters[DFA_PARENTQUERY] = _getMain().ANY_NON_TRASHED_FOLDER_NAME.format(getEscapedDriveFolderName())
  elif myarg in {'teamdriveparent', 'shareddriveparent'}:
    parameters[DFA_SHAREDDRIVE_PARENT] = _getMain().getString(Cmd.OB_SHAREDDRIVE_NAME)
  elif myarg in {'teamdriveparentid', 'shareddriveparentid'}:
    parameters[DFA_SHAREDDRIVE_PARENTID] = _getMain().getString(Cmd.OB_DRIVE_FOLDER_ID)
  elif myarg in {'teamdriveparentname', 'shareddriveparentname'}:
    parameters[DFA_SHAREDDRIVE_PARENTQUERY] = _getMain().ANY_NON_TRASHED_FOLDER_NAME.format(getEscapedDriveFolderName())
    parameters[DFA_KWARGS]['corpora'] = CORPORA_ALL_DRIVES
    parameters[DFA_KWARGS]['includeItemsFromAllDrives'] = True
    parameters[DFA_KWARGS]['supportsAllDrives'] = True
  elif myarg == 'enforcesingleparent':
    _getMain().deprecatedArgument(myarg)
  else:
    return False
  return True

def getDriveFileAddRemoveParentAttribute(myarg, parameters):
  if myarg in {'addparent', 'addparents'}:
    parameters[DFA_ADD_PARENT_IDS].extend(_getMain().getString(Cmd.OB_DRIVE_FOLDER_ID_LIST).replace(',', ' ').split())
  elif myarg in {'removeparent', 'removeparents'}:
    parameters[DFA_REMOVE_PARENT_IDS].extend(_getMain().getString(Cmd.OB_DRIVE_FOLDER_ID_LIST).replace(',', ' ').split())
  elif myarg == 'addparentname':
    parameters[DFA_ADD_PARENT_NAMES].append(_getMain().MY_NON_TRASHED_FOLDER_NAME.format(getEscapedDriveFolderName()))
  elif myarg == 'removeparentname':
    parameters[DFA_REMOVE_PARENT_NAMES].append(_getMain().MY_NON_TRASHED_FOLDER_NAME.format(getEscapedDriveFolderName()))
  elif myarg in {'addanyownerparentname', 'addsharedparentname'}:
    parameters[DFA_ADD_PARENT_NAMES].append(_getMain().ANY_NON_TRASHED_FOLDER_NAME.format(getEscapedDriveFolderName()))
  elif myarg in {'removeanyownerparentname', 'removesharedparentname'}:
    parameters[DFA_REMOVE_PARENT_NAMES].append(_getMain().ANY_NON_TRASHED_FOLDER_NAME.format(getEscapedDriveFolderName()))
  elif myarg == 'enforcesingleparent':
    _getMain().deprecatedArgument(myarg)
  else:
    return False
  return True

def _getDriveFileDownloadRestrictions(myarg, body):
  subField = myarg
  if subField.startswith('downloadrestrictions.'):
    _, subField = subField.split('.', 1)
  if subField.startswith('itemdownloadrestriction.'):
    _, subField = subField.split('.', 1)
  if subField == 'itemdownloadrestriction':
    subField = _getMain().getChoice(DRIVE_FILE_ITEM_DOWNLOAD_RESTRICTION_CHOICE_MAP)
  if subField in DRIVE_FILE_ITEM_DOWNLOAD_RESTRICTION_CHOICE_MAP:
    body.setdefault('downloadRestrictions', {'itemDownloadRestriction': {}})
    body['downloadRestrictions']['itemDownloadRestriction'][DRIVE_FILE_ITEM_DOWNLOAD_RESTRICTION_CHOICE_MAP[subField]] = _getMain().getBoolean()
    return True
  return False

def getDriveFileCopyAttribute(myarg, body, parameters):
  if myarg == 'ignoredefaultvisibility':
    parameters[DFA_IGNORE_DEFAULT_VISIBILITY] = _getMain().getBoolean()
  elif myarg in {'keeprevisionforever', 'pinned'}:
    parameters[DFA_KEEP_REVISION_FOREVER] = _getMain().getBoolean()
  elif myarg == 'ocrlanguage':
    parameters[DFA_OCRLANGUAGE] = _getMain().getLanguageCode(_getMain().LANGUAGE_CODES_MAP)
  elif myarg == 'description':
    body['description'] = _getMain().getStringWithCRsNLs()
  elif myarg == 'mimetype':
    body['mimeType'] = getMimeType()
  elif myarg in {'lastviewedbyme', 'lastviewedbyuser', 'lastviewedbymedate', 'lastviewedbymetime'}:
    body['viewedByMeTime'] = _getMain().getTimeOrDeltaFromNow()
  elif myarg in {'modifieddate', 'modifiedtime'}:
    body['modifiedTime'] = _getMain().getTimeOrDeltaFromNow()
  elif myarg == 'viewerscancopycontent':
    body['copyRequiresWriterPermission'] = not _getMain().getBoolean()
  elif myarg in {'copyrequireswriterpermission', 'restrict', 'restricted'}:
    body['copyRequiresWriterPermission'] = _getMain().getBoolean()
  elif myarg == 'writerscanshare':
    body['writersCanShare'] = _getMain().getBoolean()
  elif myarg == 'writerscantshare':
    body['writersCanShare'] = not _getMain().getBoolean()
  elif myarg == 'contentrestrictions':
    while Cmd.PeekArgumentPresent(list(DRIVE_FILE_CONTENT_RESTRICTIONS_CHOICE_MAP.keys())):
      body.setdefault('contentRestrictions', [{}])
      restriction = _getMain().getChoice(DRIVE_FILE_CONTENT_RESTRICTIONS_CHOICE_MAP, mapChoice=True)
      body['contentRestrictions'][0][restriction] = _getMain().getBoolean()
      if restriction == 'readOnly':
        if _getMain().checkArgumentPresent(['reason']):
          if body['contentRestrictions'][0][restriction]:
            body['contentRestrictions'][0]['reason'] = _getMain().getString(Cmd.OB_STRING, minLen=0)
          else:
            Cmd.Backup()
            _getMain().usageErrorExit(Msg.REASON_ONLY_VALID_WITH_CONTENTRESTRICTIONS_READONLY_TRUE)
  elif _getDriveFileDownloadRestrictions(myarg, body):
    pass
  elif myarg == 'inheritedpermissionsdisabled':
    body['inheritedPermissionsDisabled'] = _getMain().getBoolean()
  elif myarg == 'property':
    driveprop = getDriveFileProperty()
    body.setdefault(driveprop['visibility'], {})
    body[driveprop['visibility']][driveprop['key']] = driveprop['value']
  elif myarg == 'privateproperty':
    driveprop = getDriveFileProperty('appProperties')
    body.setdefault(driveprop['visibility'], {})
    body[driveprop['visibility']][driveprop['key']] = driveprop['value']
  elif myarg == 'publicproperty':
    driveprop = getDriveFileProperty('properties')
    body.setdefault(driveprop['visibility'], {})
    body[driveprop['visibility']][driveprop['key']] = driveprop['value']
  else:
    return False
  return True

def getDriveFileAttribute(myarg, body, parameters, updateCmd):
  if myarg == 'localfile':
    parameters[DFA_URL] = None
    parameters[DFA_LOCALFILEPATH] = _getMain().setFilePath(_getMain().getString(Cmd.OB_FILE_NAME), GC.INPUT_DIR)
    if parameters[DFA_LOCALFILEPATH] != '-':
      try:
        f = open(parameters[DFA_LOCALFILEPATH], 'rb')
        f.close()
        # See http://stackoverflow.com/a/39501288/1709587 for explanation.
        mtime = os.path.getmtime(parameters[DFA_LOCALFILEPATH])
        parameters[DFA_MODIFIED_TIME] = _getMain().formatLocalSecondsTimestamp(mtime)
        if not updateCmd:
          if platform.system() == 'Windows':
            ctime = os.path.getctime(parameters[DFA_LOCALFILEPATH])
          else:
            stat = os.stat(parameters[DFA_LOCALFILEPATH])
            if hasattr(stat, 'st_birthtime'):
              ctime = stat.st_birthtime
            else:
              # We're probably on Linux. No easy way to get creation dates here,
              # so we'll settle for when its content was last modified.
              ctime = stat.st_mtime
          parameters[DFA_CREATED_TIME] = _getMain().formatLocalSecondsTimestamp(ctime)
      except IOError as e:
        Cmd.Backup()
        _getMain().usageErrorExit(f'{parameters[DFA_LOCALFILEPATH]}: {str(e)}')
      parameters[DFA_LOCALFILENAME] = os.path.basename(parameters[DFA_LOCALFILEPATH])
      if not updateCmd:
        body.setdefault('name', parameters[DFA_LOCALFILENAME])
      body['mimeType'] = mimetypes.guess_type(parameters[DFA_LOCALFILEPATH])[0]
      if body['mimeType'] is None:
        body['mimeType'] = 'application/octet-stream'
    else:
      parameters[DFA_LOCALFILENAME] = '-'
      if body.get('mimeType') is None:
        body['mimeType'] = 'application/octet-stream'
    parameters[DFA_LOCALMIMETYPE] = body['mimeType']
  elif myarg == 'url':
    parameters[DFA_LOCALFILEPATH] = None
    parameters[DFA_URL] = _getMain().getString(Cmd.OB_URL)
  elif myarg =='stripnameprefix':
    parameters[DFA_STRIPNAMEPREFIX] = _getMain().getString(Cmd.OB_STRING, minLen=0)
  elif myarg == 'replacefilename':
    parameters[DFA_REPLACEFILENAME].append(_getMain().getREPatternSubstitution(re.IGNORECASE))
  elif myarg in {'convert', 'ocr'}:
    _getMain().deprecatedArgument(myarg)
    _getMain().stderrWarningMsg(Msg.USE_MIMETYPE_TO_SPECIFY_GOOGLE_FORMAT)
  elif myarg in DRIVE_LABEL_CHOICE_MAP:
    myarg = DRIVE_LABEL_CHOICE_MAP[myarg]
    body[myarg] = _getMain().getBoolean()
  elif not updateCmd and myarg in {'createddate', 'createdtime'}:
    body['createdTime'] = _getMain().getTimeOrDeltaFromNow()
  elif myarg == 'preservefiletimes':
    parameters[DFA_PRESERVE_FILE_TIMES] = _getMain().getBoolean()
  elif myarg == 'shortcut':
    body['mimeType'] = MIMETYPE_GA_SHORTCUT
    body['shortcutDetails'] = {'targetId': _getMain().getString(Cmd.OB_DRIVE_FOLDER_ID)}
  elif getDriveFileParentAttribute(myarg, parameters):
    pass
  elif myarg == 'foldercolorrgb':
    body['folderColorRgb'] = _getMain().getColor()
  elif myarg == 'usecontentasindexabletext':
    parameters[DFA_USE_CONTENT_AS_INDEXABLE_TEXT] = _getMain().getBoolean()
  elif myarg == 'indexabletext':
    body.setdefault('contentHints', {})
    body['contentHints']['indexableText'] = _getMain().getString(Cmd.OB_STRING)
  elif myarg == 'securityupdate':
    body['linkShareMetadata'] = {'securityUpdateEnabled': getBoolean(), 'securityUpdateEligible': True}
  elif myarg == 'timestamp':
    parameters[DFA_TIMESTAMP] = _getMain().getBoolean()
  elif myarg == 'timeformat':
    parameters[DFA_TIMEFORMAT] = _getMain().getString(Cmd.OB_DATETIME_FORMAT, minLen=0)
  elif getDriveFileCopyAttribute(myarg, body, parameters):
    pass
  else:
    _getMain().unknownArgumentExit()

def setPreservedFileTimes(body, parameters, updateCmd):
  body['modifiedTime'] = parameters[DFA_MODIFIED_TIME]
  if not updateCmd:
    body['createdTime'] = parameters[DFA_CREATED_TIME]

def getMediaBody(parameters):
  if parameters[DFA_URL]:
    try:
      status, c = _getMain().getHttpObj(timeout=10).request(parameters[DFA_URL])
      if status['status'] != '200':
        _getMain().entityActionFailedExit([Ent.URL, parameters[DFA_URL]], Msg.URL_ERROR.format(status['status']))
      parameters[DFA_LOCALMIMETYPE] = status['content-type']
      return googleapiclient.http.MediaIoBaseUpload(io.BytesIO(c), mimetype=status['content-type'], resumable=True)
    except (IOError, httplib2.error.ServerNotFoundError) as e:
      _getMain().systemErrorExit(_getMain().FILE_ERROR_RC, _getMain().fileErrorMessage(parameters[DFA_URL], str(e), entityType=Ent.URL))
  else:
    try:
      if parameters[DFA_LOCALFILEPATH] != '-':
        media_body = googleapiclient.http.MediaFileUpload(parameters[DFA_LOCALFILEPATH], mimetype=parameters[DFA_LOCALMIMETYPE], resumable=True)
      else:
        media_body = googleapiclient.http.MediaIoBaseUpload(io.BytesIO(sys.stdin.buffer.read()), mimetype=parameters[DFA_LOCALMIMETYPE], resumable=True)
      if media_body.size() == 0:
        media_body = None
      return media_body
    except IOError as e:
      _getMain().systemErrorExit(_getMain().FILE_ERROR_RC, _getMain().fileErrorMessage(parameters[DFA_LOCALFILEPATH], str(e)))

DRIVE_ACTIVITY_ACTION_MAP = {
  'comment': 'COMMENT',
  'create': 'CREATE',
  'delete': 'DELETE',
  'dlpchange': 'DLP_CHANGE',
  'edit': 'EDIT',
  'emptytrash': 'DELETE',
  'move': 'MOVE',
  'permissionchange': 'PERMISSION_CHANGE',
  'reference': 'REFERENCE',
  'rename': 'RENAME',
  'restore': 'RESTORE',
  'settingschange': 'SETTINGS_CHANGE',
  'trash': 'DELETE',
  'untrash': 'RESTORE',
  'upload': 'CREATE',
  }

CONSOLIDATION_GROUPING_STRATEGY_CHOICE_MAP = {'driveui': 'legacy', 'legacy': 'legacy', 'none': 'none'}

# gam <UserTypeEntity> print driveactivity [todrive <ToDriveAttribute>*]
#	[(fileid <DriveFileID>) | (folderid <DriveFolderID>) |
#	 (drivefilename <DriveFileName>) | (drivefoldername <DriveFolderName>) | (query <QueryDriveFile>)]
#	[([start <Date>|<Time>] [end <Date>|<Time>])|(range <Date>|<Time> <Date>|<Time>)|
#	 yesterday|today|thismonth|(previousmonths <Integer>)]
#	[action|actions [not] <DriveActivityActionList>] [maxactivities <Number>]
#	[consolidationstrategy legacy|none]
#	[idmapfile <CSVFileInput> endcsv]
#	[stripcrsfromname] [formatjson [quotechar <Character>]]
