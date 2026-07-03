"""GAM data transfer operations."""

import sys

from gam.util.args import formatLocalTime
import time

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


def _getMain():
  return sys.modules['gam']

def __getattr__(name):
  """Fall back to gam module for any undefined names."""
  main = _getMain()
  try:
    return getattr(main, name)
  except AttributeError:
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")

def getTransferApplications(dt):
  try:
    return _getMain()._getMain().callGAPIpages(dt.applications(), 'list', 'applications',
                         throwReasons=[GAPI.UNKNOWN_ERROR, GAPI.FORBIDDEN],
                         customerId=GC.Values[GC.CUSTOMER_ID], fields='applications(id,name,transferParams)')
  except (GAPI.unknownError, GAPI.forbidden):
    accessErrorExit(None)

def _convertTransferAppIDtoName(apps, appID):
  for app in apps:
    if appID == app['id']:
      return app['name']
  return f'applicationId: {appID}'

DRIVE_AND_DOCS_APP_NAME = 'drive and docs'
GOOGLE_LOOKER_STUDIO_APP_NAME = 'looker studio'

SERVICE_NAME_CHOICE_MAP = {
  'datastudio': GOOGLE_LOOKER_STUDIO_APP_NAME,
  'drive': DRIVE_AND_DOCS_APP_NAME,
  'googledrive': DRIVE_AND_DOCS_APP_NAME,
  'gdrive': DRIVE_AND_DOCS_APP_NAME,
  'lookerstudio': GOOGLE_LOOKER_STUDIO_APP_NAME,
  }

def _validateTransferAppName(apps, appName):
  appName = appName.strip().lower()
  appName = SERVICE_NAME_CHOICE_MAP.get(appName, appName)
  appNameList = []
  for app in apps:
    if appName == app['name'].lower():
      return (app['name'], app['id'])
    appNameList.append(app['name'].lower())
  _getMain()._getMain().invalidChoiceExit(appName, appNameList, True)

PRIVACY_LEVEL_CHOICE_MAP = {
  'private': ['PRIVATE'],
  'shared': ['SHARED'],
  'all': ['PRIVATE', 'SHARED'],
  }

# gam create datatransfer|transfer <OldOwnerID> <ServiceNameList> <NewOwnerID>
#	[private|shared|all] [release_resources] (<ParameterKey> <ParameterValue>)*
#	[wait <Integer> <Integer>]
def doCreateDataTransfer():
  def _assignAppParameter(key, value, doubleBackup=False):
    keyValid = False
    for app in apps:
      for params in app.get('transferParams', []):
        if key == params['key']:
          appIndex = appIndicies.get(app['id'])
          if appIndex is not None:
            body['applicationDataTransfers'][appIndex].setdefault('applicationTransferParams', [])
            body['applicationDataTransfers'][appIndex]['applicationTransferParams'].append({'key': key, 'value': value})
            keyValid = True
          break
    if not keyValid:
      Cmd.Backup()
      if doubleBackup:
        Cmd.Backup()
      _getMain()._getMain().usageErrorExit(Msg.NO_DATA_TRANSFER_APP_FOR_PARAMETER.format(key))

  dt = _getMain()._getMain().buildGAPIObject(API.DATATRANSFER)
  apps = getTransferApplications(dt)
  old_owner = _getMain()._getMain().getEmailAddress(returnUIDprefix='uid:')
  body = {'oldOwnerUserId': _getMain()._getMain().convertEmailAddressToUID(old_owner)}
  appIndicies = {}
  appNameList = []
  waitInterval = waitRetries = 0
  i = 0
  body['applicationDataTransfers'] = []
  for appName in _getMain()._getMain().getString(Cmd.OB_SERVICE_NAME_LIST).split(','):
    appName, appId = _validateTransferAppName(apps, appName)
    body['applicationDataTransfers'].append({'applicationId': appId})
    appIndicies[appId] = i
    i += 1
    appNameList.append(appName)
  new_owner = _getMain()._getMain().getEmailAddress(returnUIDprefix='uid:')
  body['newOwnerUserId'] = _getMain()._getMain().convertEmailAddressToUID(new_owner)
  if body['oldOwnerUserId'] == body['newOwnerUserId']:
    Cmd.Backup()
    _getMain()._getMain().usageErrorExit(Msg.NEW_OWNER_MUST_DIFFER_FROM_OLD_OWNER)
  while Cmd.ArgumentsRemaining():
    myarg = _getMain()._getMain().getArgument()
    if myarg in PRIVACY_LEVEL_CHOICE_MAP:
      _assignAppParameter('PRIVACY_LEVEL', PRIVACY_LEVEL_CHOICE_MAP[myarg])
    elif myarg == 'releaseresources':
      if _getMain()._getMain().getBoolean():
        _assignAppParameter('RELEASE_RESOURCES', ['TRUE'])
    elif myarg == 'wait':
      waitInterval = _getMain()._getMain().getInteger(minVal=5, maxVal=60)
      waitRetries = _getMain()._getMain().getInteger(minVal=0)
    else:
      _assignAppParameter(Cmd.Previous().upper(), _getMain()._getMain().getString(Cmd.OB_PARAMETER_VALUE).upper().split(','), True)
  try:
    result = _getMain()._getMain().callGAPI(dt.transfers(), 'insert',
                      throwReasons=[GAPI.UNKNOWN_ERROR, GAPI.FORBIDDEN],
                      body=body, fields='id')
  except (GAPI.unknownError, GAPI.forbidden) as e:
    _getMain()._getMain().entityActionFailedExit([Ent.USER, old_owner], str(e))
  _getMain()._getMain().entityActionPerformed([Ent.TRANSFER_REQUEST, None])
  Ind.Increment()
  _getMain()._getMain().printEntity([Ent.TRANSFER_ID, result['id']])
  _getMain()._getMain().printEntity([Ent.SERVICE, ','.join(appNameList)])
  _getMain()._getMain().printKeyValueList([Msg.FROM, old_owner])
  _getMain()._getMain().printKeyValueList([Msg.TO, new_owner])
  Ind.Decrement()
  if waitRetries == 0:
    return
  retry = 0
  status = 'inProgress'
  dtId = result['id']
  while True:
    _getMain()._getMain().writeStderr(Ind.Spaces()+Msg.WAITING_FOR_DATA_TRANSFER_TO_COMPLETE_SLEEPING.format(waitInterval))
    time.sleep(waitInterval)
    try:
      result = _getMain()._getMain().callGAPI(dt.transfers(), 'get',
                        throwReasons=[GAPI.NOT_FOUND],
                        dataTransferId=dtId, fields='overallTransferStatusCode')
      if result['overallTransferStatusCode'] == 'completed':
        status = result['overallTransferStatusCode']
        break
      retry += 1
      if retry >= waitRetries:
        break
    except GAPI.notFound:
      _getMain()._getMain().entityActionFailedWarning([Ent.TRANSFER_ID, dtId], Msg.DOES_NOT_EXIST)
      break
  _getMain()._getMain().printEntity([Ent.TRANSFER_ID, dtId, Ent.STATUS, status])

def _showTransfer(apps, transfer, i, count):
  _getMain()._getMain().printEntity([Ent.TRANSFER_ID, transfer['id']], i, count)
  Ind.Increment()
  _getMain()._getMain().printKeyValueList(['Request Time', formatLocalTime(transfer['requestTime'])])
  _getMain()._getMain().printKeyValueList(['Old Owner', convertUserIDtoEmail(transfer['oldOwnerUserId'])])
  _getMain()._getMain().printKeyValueList(['New Owner', convertUserIDtoEmail(transfer['newOwnerUserId'])])
  _getMain()._getMain().printKeyValueList(['Overall Transfer Status', transfer['overallTransferStatusCode']])
  for app in transfer['applicationDataTransfers']:
    _getMain()._getMain().printKeyValueList(['Application', _convertTransferAppIDtoName(apps, app['applicationId'])])
    Ind.Increment()
    _getMain()._getMain().printKeyValueList(['Status', app['applicationTransferStatus']])
    _getMain()._getMain().printKeyValueList(['Parameters'])
    Ind.Increment()
    if 'applicationTransferParams' in app:
      for param in app['applicationTransferParams']:
        key = param['key']
        value = param.get('value', [])
        if value:
          _getMain()._getMain().printKeyValueList([key, ','.join(value)])
        else:
          _getMain()._getMain().printKeyValueList([key])
    else:
      _getMain()._getMain().printKeyValueList(['None'])
    Ind.Decrement()
    Ind.Decrement()
  Ind.Decrement()

# gam info datatransfer|transfer <TransferID>
def doInfoDataTransfer():
  dt = _getMain()._getMain().buildGAPIObject(API.DATATRANSFER)
  apps = getTransferApplications(dt)
  dtId = _getMain()._getMain().getString(Cmd.OB_TRANSFER_ID)
  _getMain()._getMain().checkForExtraneousArguments()
  try:
    transfer = _getMain()._getMain().callGAPI(dt.transfers(), 'get',
                        throwReasons=[GAPI.NOT_FOUND],
                        dataTransferId=dtId)
    _showTransfer(apps, transfer, 0, 0)
  except GAPI.notFound:
    _getMain()._getMain().entityActionFailedWarning([Ent.TRANSFER_ID, dtId], Msg.DOES_NOT_EXIST)

DATA_TRANSFER_STATUS_MAP = {
  'completed': 'completed',
  'failed': 'failed',
#  'pending': 'pending',
  'inprogress': 'inProgress',
  }
DATA_TRANSFER_SORT_TITLES = ['id', 'requestTime', 'oldOwnerUserEmail', 'newOwnerUserEmail',
                             'overallTransferStatusCode', 'application', 'applicationId', 'status']

# gam print datatransfers|transfers [todrive <ToDriveAttribute>*]
#	[olduser|oldowner <UserItem>] [newuser|newowner <UserItem>]
#	[status <String>] [delimiter <Character>]
#	(addcsvdata <FieldName> <String>)*
# gam show datatransfers|transfers
#	[olduser|oldowner <UserItem>] [newuser|newowner <UserItem>]
#	[status <String>] [delimiter <Character>]
def doPrintShowDataTransfers():
  dt = _getMain()._getMain().buildGAPIObject(API.DATATRANSFER)
  apps = getTransferApplications(dt)
  newOwnerUserId = None
  oldOwnerUserId = None
  status = None
  csvPF = _getMain()._getMain().CSVPrintFile(['id'], DATA_TRANSFER_SORT_TITLES) if Act.csvFormat() else None
  delimiter = GC.Values[GC.CSV_OUTPUT_FIELD_DELIMITER]
  addCSVData = {}
  while Cmd.ArgumentsRemaining():
    myarg = _getMain()._getMain().getArgument()
    if csvPF and myarg == 'todrive':
      csvPF.GetTodriveParameters()
    elif myarg in {'olduser', 'oldowner'}:
      oldOwnerUserId = _getMain()._getMain().convertEmailAddressToUID(_getMain()._getMain().getEmailAddress(returnUIDprefix='uid:'))
    elif myarg in {'newuser', 'newowner'}:
      newOwnerUserId = _getMain()._getMain().convertEmailAddressToUID(_getMain()._getMain().getEmailAddress(returnUIDprefix='uid:'))
    elif myarg == 'status':
      status = _getMain()._getMain().getChoice(DATA_TRANSFER_STATUS_MAP, mapChoice=True)
    elif myarg == 'delimiter':
      delimiter = _getMain()._getMain().getCharacter()
    elif csvPF and myarg == 'addcsvdata':
      _getMain()._getMain().getAddCSVData(addCSVData)
    else:
      _getMain()._getMain().unknownArgumentExit()
  try:
    transfers = _getMain()._getMain().callGAPIpages(dt.transfers(), 'list', 'dataTransfers',
                              throwReasons=[GAPI.UNKNOWN_ERROR, GAPI.FORBIDDEN, GAPI.INVALID_INPUT],
                              customerId=GC.Values[GC.CUSTOMER_ID], status=status,
                              newOwnerUserId=newOwnerUserId, oldOwnerUserId=oldOwnerUserId)
  except (GAPI.unknownError, GAPI.forbidden, GAPI.invalidInput) as e:
    _getMain()._getMain().entityActionFailedExit([Ent.TRANSFER_REQUEST, None], str(e))
  if not csvPF:
    count = len(transfers)
    _getMain()._getMain().performActionNumItems(count, Ent.TRANSFER_REQUEST)
    Ind.Increment()
    i = 0
    for transfer in sorted(transfers, key=lambda k: k['requestTime']):
      i += 1
      _showTransfer(apps, transfer, i, count)
    Ind.Decrement()
  else:
    for transfer in sorted(transfers, key=lambda k: k['requestTime']):
      row = {}
      row['id'] = transfer['id']
      row['requestTime'] = formatLocalTime(transfer['requestTime'])
      row['oldOwnerUserEmail'] = convertUserIDtoEmail(transfer['oldOwnerUserId'])
      row['newOwnerUserEmail'] = convertUserIDtoEmail(transfer['newOwnerUserId'])
      row['overallTransferStatusCode'] = transfer['overallTransferStatusCode']
      if addCSVData:
        row.update(addCSVData)
      for app in transfer['applicationDataTransfers']:
        xrow = row.copy()
        xrow['application'] = _convertTransferAppIDtoName(apps, app['applicationId'])
        xrow['applicationId'] = app['applicationId']
        xrow['status'] = app['applicationTransferStatus']
        for param in app.get('applicationTransferParams', []):
          key = param['key']
          xrow[key] = delimiter.join(param.get('value', [] if key != 'RELEASE_RESOURCES' else ['TRUE']))
        csvPF.WriteRowTitles(xrow)
  if csvPF:
    csvPF.writeCSVfile('Data Transfers')

# gam show transferapps
def doShowTransferApps():
  dt = _getMain()._getMain().buildGAPIObject(API.DATATRANSFER)
  _getMain()._getMain().checkForExtraneousArguments()
  Act.Set(Act.SHOW)
  try:
    apps = _getMain()._getMain().callGAPIpages(dt.applications(), 'list', 'applications',
                         throwReasons=[GAPI.UNKNOWN_ERROR, GAPI.FORBIDDEN],
                         customerId=GC.Values[GC.CUSTOMER_ID], fields='applications(id,name,transferParams)')
  except (GAPI.unknownError, GAPI.forbidden):
    accessErrorExit(None)
  count = len(apps)
  _getMain()._getMain().performActionNumItems(count, Ent.TRANSFER_APPLICATION)
  Ind.Increment()
  i = 0
  for app in apps:
    i += 1
    _getMain()._getMain().printKeyValueListWithCount([app['name']], i, count)
    Ind.Increment()
    _getMain()._getMain().printKeyValueList(['id', app['id']])
    transferParams = app.get('transferParams', [])
    if transferParams:
      _getMain()._getMain().printKeyValueList(['Parameters'])
      Ind.Increment()
      for param in transferParams:
        _getMain()._getMain().printKeyValueList(['key', param['key']])
        Ind.Increment()
        _getMain()._getMain().printKeyValueList(['value', ','.join(param['value'])])
        Ind.Decrement()
      Ind.Decrement()
    Ind.Decrement()
  Ind.Decrement()

# gam create org|ou <String> [description <String>] [parent <OrgUnitItem>] [buildpath]
