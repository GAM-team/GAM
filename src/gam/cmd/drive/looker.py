"""Looker Studio asset and permission management.

Part of the drive sub-package, extracted from drive.py."""

"""GAM Google Drive file, permission, shared drive, and label management."""

import re
import json
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

LOOKERSTUDIO_ASSETTYPE_CHOICE_MAP = {
  'report': ['REPORT'],
  'datasource': ['DATA_SOURCE'],
  'all': ['REPORT', 'DATA_SOURCE'],
  }

def initLookerStudioAssetSelectionParameters():
  return ({'owner': None, 'title': None, 'includeTrashed': False}, {'assetTypes': ['REPORT']})

def getLookerStudioAssetSelectionParameters(myarg, parameters, assetTypes):
  if myarg in {'assettype', 'assettypes'}:
    assetTypes['assetTypes'] = _getMain().getChoice(LOOKERSTUDIO_ASSETTYPE_CHOICE_MAP, mapChoice=True)
  elif myarg == 'title':
    parameters['title'] = _getMain().getString(Cmd.OB_STRING)
  elif myarg == 'owner':
    parameters['owner'] = _getMain().getEmailAddress(noUid=True)
  elif myarg == 'includetrashed':
    parameters['includeTrashed'] = True
  else:
    return False
  return True

def _validateUserGetLookerStudioAssetIds(user, i, count, entity):
  if entity:
    if entity['dict']:
      entityList = [{'name': item, 'title': item} for item in entity['dict'][user]]
    else:
      entityList = [{'name': item, 'title': item} for item in entity['list']]
  else:
    entityList = []
  user, ds = _getMain().buildGAPIServiceObject(API.LOOKERSTUDIO, user, i, count)
  if not ds:
    return (user, None, None, 0)
  return (user, ds, entityList, len(entityList))

def _getLookerStudioAssetByID(ds, user, i, count, assetId):
  _getMain().printGettingAllEntityItemsForWhom(Ent.LOOKERSTUDIO_ASSET, user, i, count)
  try:
    return _getMain().callGAPI(ds.assets(), 'get',
                    throwReasons=GAPI.LOOKERSTUDIO_THROW_REASONS,
                    name=f'assets/{assetId}')
  except (GAPI.invalidArgument, GAPI.badRequest, GAPI.notFound, GAPI.permissionDenied, GAPI.internalError) as e:
    _getMain().entityActionFailedWarning([Ent.USER, user], str(e), i, count)
  except GAPI.serviceNotAvailable:
    _getMain().userLookerStudioServiceNotEnabledWarning(user, i, count)
  return None

def _getLookerStudioAssets(ds, user, i, count, parameters, assetTypes, fields, orderBy=None):
  assets = []
  for assetType in assetTypes['assetTypes']:
    entityType = Ent.LOOKERSTUDIO_ASSET_REPORT if assetType == 'REPORT' else Ent.LOOKERSTUDIO_ASSET_DATASOURCE
    _getMain().printGettingAllEntityItemsForWhom(entityType, user, i, count)
    parameters['assetTypes'] = assetType
    try:
      assets.extend(_getMain().callGAPIpages(ds.assets(), 'search', 'assets',
                                  pageMessage=_getMain().getPageMessage(),
                                  throwReasons=GAPI.LOOKERSTUDIO_THROW_REASONS,
                                  **parameters, orderBy=orderBy, fields=fields))
    except (GAPI.invalidArgument, GAPI.badRequest, GAPI.notFound, GAPI.permissionDenied, GAPI.internalError) as e:
      _getMain().entityActionFailedWarning([Ent.USER, user], str(e), i, count)
      return (None, 0)
    except GAPI.serviceNotAvailable:
      _getMain().userLookerStudioServiceNotEnabledWarning(user, i, count)
      return (None, 0)
  return (assets, len(assets))

LOOKERSTUDIO_ASSETS_ORDERBY_CHOICE_MAP = {
  'title': 'title'
  }
LOOKERSTUDIO_ASSETS_TIME_OBJECTS = {'updateTime', 'updateByMeTime', 'createTime', 'lastViewByMeTime'}

# gam <UserTypeEntity> print lookerstudioassets [todrive <ToDriveAttribute>*]
#	[([assettype report|datasource|all] [title <String>]
#	  [owner <Emailddress>] [includetrashed]
#	  [orderby title [ascending|descending]]) |
#	 (assetids <LookerStudioAssetIDEntity>)]
#	[stripcrsfromtitle]
#	[formatjson [quotechar <Character>]]
# gam <UserTypeEntity> show lookerstudioassets
#	[([assettype report|datasource|all] [title <String>]
#	  [owner <Emailddress>] [includetrashed]
#	  [orderby title [ascending|descending]]) |
#	 (assetids <LookerStudioAssetIDEntity>)]
#	[stripcrsfromtitle]
#	[formatjson]
def printShowLookerStudioAssets(users):
  def _printAsset(asset, user):
    if stripCRsFromTitle:
      asset['title'] = _stripControlCharsFromName(asset['title'])
    row = _getMain().flattenJSON(asset, flattened={'User': user})
    if not FJQC.formatJSON:
      csvPF.WriteRowTitles(row)
    elif csvPF.CheckRowTitles(row):
      csvPF.WriteRowNoFilter({'User': user, 'title': asset['title'],
                              'JSON': json.dumps(_getMain().cleanJSON(asset, timeObjects=LOOKERSTUDIO_ASSETS_TIME_OBJECTS), ensure_ascii=False, sort_keys=True)})

  def _showAsset(asset):
    if stripCRsFromTitle:
      asset['title'] = _stripControlCharsFromName(asset['title'])
    if FJQC.formatJSON:
      _getMain().printLine(json.dumps(_getMain().cleanJSON(asset, timeObjects=LOOKERSTUDIO_ASSETS_TIME_OBJECTS), ensure_ascii=False, sort_keys=False))
      return
    _getMain().printEntity([Ent.LOOKERSTUDIO_ASSET, asset['title']], j, jcount)
    Ind.Increment()
    _getMain().showJSON(None, asset, timeObjects=LOOKERSTUDIO_ASSETS_TIME_OBJECTS)
    Ind.Decrement()

  csvPF = _getMain().CSVPrintFile(['User', 'title']) if Act.csvFormat() else None
  FJQC = _getMain().FormatJSONQuoteChar(csvPF)
  OBY = _getMain().OrderBy(LOOKERSTUDIO_ASSETS_ORDERBY_CHOICE_MAP, ascendingKeyword='ascending', descendingKeyword='')
  parameters, assetTypes = initLookerStudioAssetSelectionParameters()
  assetIdEntity = None
  stripCRsFromTitle = False
  while Cmd.ArgumentsRemaining():
    myarg = _getMain().getArgument()
    if csvPF and myarg == 'todrive':
      csvPF.GetTodriveParameters()
    elif getLookerStudioAssetSelectionParameters(myarg, parameters, assetTypes):
      pass
    elif myarg in {'assetid', 'assetids'}:
      assetIdEntity = _getMain().getUserObjectEntity(Cmd.OB_USER_ENTITY, Ent.LOOKERSTUDIO_ASSETID)
    elif myarg == 'stripcrsfromtitle':
      stripCRsFromTitle = True
    elif myarg == 'orderby':
      OBY.GetChoice()
    else:
      FJQC.GetFormatJSONQuoteChar(myarg, True)
  i, count, users = _getMain().getEntityArgument(users)
  for user in users:
    i += 1
    user, ds, assets, jcount = _validateUserGetLookerStudioAssetIds(user, i, count, assetIdEntity)
    if not ds:
      continue
    if assetIdEntity is None:
      assets, jcount = _getLookerStudioAssets(ds, user, i, count, parameters, assetTypes, 'nextPageToken,assets', OBY.orderBy)
      if assets is None:
        continue
    if not csvPF:
      if not FJQC.formatJSON:
        _getMain().entityPerformActionNumItems([Ent.USER, user], jcount, Ent.LOOKERSTUDIO_ASSET, i, count)
      Ind.Increment()
      j = 0
      for asset in assets:
        j += 1
        if assetIdEntity:
          asset = _getLookerStudioAssetByID(ds, user, i, count, asset['name'])
        if asset:
          _showAsset(asset)
      Ind.Decrement()
    elif assets:
      for asset in assets:
        if assetIdEntity:
          asset = _getLookerStudioAssetByID(ds, user, i, count, asset['name'])
        if asset:
          _printAsset(asset, user)
    elif GC.Values[GC.CSV_OUTPUT_USERS_AUDIT]:
      csvPF.WriteRowNoFilter({'User': user})
  if csvPF:
    csvPF.writeCSVfile('Looker Studio Assets')

def _showLookerStudioPermissions(user, asset, permissions, j, jcount, FJQC):
  if FJQC is not None and FJQC.formatJSON:
    permissions['User'] = user
    permissions['assetId'] = asset['name']
    _getMain().printLine(json.dumps(_getMain().cleanJSON(permissions), ensure_ascii=False, sort_keys=False))
    return
  permissions = permissions['permissions']
  if permissions:
    _getMain().printEntity([Ent.LOOKERSTUDIO_ASSET, asset['title'], Ent.LOOKERSTUDIO_PERMISSION, ''], j, jcount)
  for role in ['OWNER', 'EDITOR', 'VIEWER']:
    members = permissions.get(role, {}).get('members', [])
    if members:
      lrole = role.lower()
      Ind.Increment()
      for member in members:
        _getMain().printKeyValueList([lrole, member])
      Ind.Decrement()

LOOKERSTUDIO_VIEW_PERMISSION_ROLE_CHOICE_MAP = {
  'editor': 'EDITOR',
  'owner': 'OWNER',
  'viewer': 'VIEWER',
  }

LOOKERSTUDIO_ADD_UPDATE_PERMISSION_ROLE_CHOICE_MAP = {
  'editor': 'EDITOR',
  'viewer': 'VIEWER',
  }

LOOKERSTUDIO_DELETE_PERMISSION_ROLE_CHOICE_MAP = {
  'any': None,
  'editor': None,
  'owner': None,
  'viewer': None,
  }

LOOKERSTUDIO_PERMISSION_MODIFIER_MAP = {
  Act.ADD: Act.MODIFIER_TO,
  Act.DELETE: Act.MODIFIER_FROM,
  Act.UPDATE: Act.MODIFIER_FOR
  }

# gam <UserTypeEntity> add lookerstudiopermissions
#	[([assettype report|datasource|all] [title <String>]
#	  [owner <Emailddress>] [includetrashed]
#	  [orderby title [ascending|descending]]) |
#	 (assetids <LookerStudioAssetIDEntity>)]
#	(role editor|viewer <LookerStudioPermissionEntity>)+
#	[nodetails]
# gam <UserTypeEntity> delete lookerstudiopermissions
#	([[assettype report|datasource|all] [title <String>]
#	  [owner <Emailddress>] [includetrashed]
#	  [orderby title [ascending|descending]]) |
#	 (assetids <LookerStudioAssetIDEntity>)]
#	(role any <LookerStudioPermissionEntity>)+
#	[nodetails]
# gam <UserTypeEntity> update lookerstudiopermissions
#	[([assettype report|datasource|all] [title <String>]
#	  [owner <Emailddress>] [includetrashed]
#	  [orderby title [ascending|descending]]) |
#	 (assetids <LookerStudioAssetIDEntity>)]
#	(role editor|viewer <LookerStudioPermissionEntity>)+
#	[nodetails]
