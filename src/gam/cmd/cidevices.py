"""GAM Cloud Identity device management."""

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


def _getMain():
  return sys.modules['gam']

def __getattr__(name):
  """Fall back to gam module for any undefined names."""
  main = _getMain()
  try:
    return getattr(main, name)
  except AttributeError:
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")

def buildGAPICIDeviceServiceObject():
  if not GC.Values[GC.ENABLE_DASA]:
    _, ci = _getMain().buildGAPIServiceObject(API.CLOUDIDENTITY_DEVICES, _getMain()._getAdminEmail(), displayError=True)
  else:
    ci = _getMain().buildGAPIObject(API.CLOUDIDENTITY_DEVICES)
  if not ci:
    sys.exit(GM.Globals[GM.SYSEXITRC])
  return ci

def getUpdateDeleteCIDeviceOptions(entityType, count, action, doit, actionChoices):
  kwargs = {}
  while Cmd.ArgumentsRemaining():
    myarg = _getMain().getArgument()
    if not action and myarg == 'action':
      action = _getMain().getChoice(actionChoices)
    elif action == 'wipe' and myarg == 'removeresetlock':
      kwargs = {'body': {'removeResetLock': True}}
    elif myarg == 'doit':
      doit = True
    else:
      _getMain().unknownArgumentExit()
  if not action:
    _getMain().actionNotPerformedNumItemsWarning(count, entityType, Msg.NO_ACTION_SPECIFIED)
    sys.exit(GM.Globals[GM.SYSEXITRC])
  if not doit:
    _getMain().actionNotPerformedNumItemsWarning(count, entityType, Msg.USE_DOIT_ARGUMENT_TO_PERFORM_ACTION)
    sys.exit(GM.Globals[GM.SYSEXITRC])
  return action, kwargs

def getCIDeviceEntity():
  ci = buildGAPICIDeviceServiceObject()
  customer = _getMain()._getCustomersCustomerIdNoC()
  if _getMain().checkArgumentPresent('devicesn'):
    query = f'serial:{_getMain().getString(Cmd.OB_SERIAL_NUMBER)}'
  elif _getMain().checkArgumentPresent('query'):
    query = _getMain().getString(Cmd.OB_QUERY)
  else:
    name = _getMain().getString(Cmd.OB_DEVICE_ENTITY)
    if name[:6].lower() == 'query:':
      query = name[6:]
    else:
      if name.lower() in {'id', 'name'}:
        name = _getMain().getString(Cmd.OB_DEVICE_ID)
      if not name.startswith('devices/'):
        name = f'devices/{name}'
      return ([{'name': name}], ci, customer, True)
  _getMain()._validateDeviceQuery(Ent.DEVICE, query)
  _getMain().printGettingAllAccountEntities(Ent.DEVICE, query)
  pageMessage = _getMain().getPageMessage()
  try:
    devices = _getMain().callGAPIpages(ci.devices(), 'list', 'devices',
                            throwReasons=[GAPI.INVALID, GAPI.INVALID_ARGUMENT, GAPI.PERMISSION_DENIED],
                            retryReasons=GAPI.SERVICE_NOT_AVAILABLE_RETRY_REASONS,
                            pageMessage=pageMessage,
                            customer=customer, filter=query,
                            fields='nextPageToken,devices(name)', pageSize=100)
    return (devices, ci, customer, False)
  except (GAPI.invalid, GAPI.invalidArgument):
    Cmd.Backup()
    _getMain().usageErrorExit(Msg.INVALID_QUERY)
  except GAPI.permissionDenied as e:
    _getMain().entityActionFailedWarning([Ent.DEVICE, None], str(e))
    return ([], ci, customer, False)

DEVICE_USERNAME_PATTERN = re.compile(r'^(devices/.+)/(deviceUsers/.+)$')
DEVICE_USERNAME_CLIENT_STATE_PATTERN = re.compile(r'^(devices/.+/deviceUsers/.+)/clientStates/(.+)$')
DEVICE_USERNAME_FORMAT_REQUIRED = 'devices/<String>/deviceUsers/<String>'
def getCIDeviceUserEntity():
  ci = buildGAPICIDeviceServiceObject()
  customer = _getMain()._getCustomersCustomerIdNoC()
  if _getMain().checkArgumentPresent('query'):
    query = _getMain().getString(Cmd.OB_QUERY)
  else:
    name = _getMain().getString(Cmd.OB_DEVICE_USER_ENTITY)
    if name[:6].lower() == 'query:':
      query = name[6:]
    else:
      if name.lower() in {'id', 'name'}:
        name = _getMain().getString(Cmd.OB_DEVICE_USER_ID)
      if DEVICE_USERNAME_PATTERN.match(name):
        return ([{'name': name}], ci, customer, True)
      Cmd.Backup()
      _getMain().invalidArgumentExit(DEVICE_USERNAME_FORMAT_REQUIRED)
  _getMain()._validateDeviceQuery(Ent.DEVICE_USER, query)
  _getMain().printGettingAllAccountEntities(Ent.DEVICE_USER, query)
  pageMessage = _getMain().getPageMessage()
  try:
    deviceUsers = _getMain().callGAPIpages(ci.devices().deviceUsers(), 'list', 'deviceUsers',
                                throwReasons=[GAPI.INVALID, GAPI.INVALID_ARGUMENT, GAPI.PERMISSION_DENIED],
                                retryReasons=GAPI.SERVICE_NOT_AVAILABLE_RETRY_REASONS,
                                pageMessage=pageMessage,
                                customer=customer, filter=query, parent='devices/-',
                                fields='nextPageToken,deviceUsers(name)', pageSize=20)
    return (deviceUsers, ci, customer, False)
  except GAPI.invalid:
    Cmd.Backup()
    _getMain().usageErrorExit(Msg.INVALID_QUERY)
  except (GAPI.invalidArgument, GAPI.permissionDenied) as e:
    _getMain().entityActionFailedWarning([Ent.DEVICE_USER, None], str(e))
    return ([], ci, customer, False)

def _makeDeviceId(name, device):
  deviceId = f'{name}'
  for field in ['deviceType', 'serialNumber', 'assetTag']:
    if field in device:
      deviceId += f', {field}: {device[field]}'
  return deviceId

DEVICE_TYPE_MAP = {
  'android': 'ANDROID',
  'chromeos': 'CHROME_OS',
  'googlesync': 'GOOGLE_SYNC',
  'ios': 'IOS',
  'linux': 'LINUX',
  'macos': 'MAC_OS',
  'windows': 'WINDOWS'
  }

DEVICE_TIME_OBJECTS = {'createTime', 'firstSyncTime', 'lastSyncTime', 'lastUpdateTime', 'securityPatchTime'}

# gam create device serialnumber <String> devicetype <DeviceType> [assettag <String>]
def doCreateCIDevice():
  ci = buildGAPICIDeviceServiceObject()
  customer = _getMain()._getCustomersCustomerIdNoC()
  body = {'deviceType': '', 'serialNumber': ''}
  while Cmd.ArgumentsRemaining():
    myarg = _getMain().getArgument()
    if myarg == 'serialnumber':
      body['serialNumber'] = _getMain().getString(Cmd.OB_STRING)
    elif myarg == 'devicetype':
      body['deviceType'] = _getMain().getChoice(DEVICE_TYPE_MAP, mapChoice=True)
    elif myarg in {'assettag', 'assteid'}:
      body['assetTag'] = _getMain().getString(Cmd.OB_STRING)
    else:
      _getMain().unknownArgumentExit()
  if not body['serialNumber']:
    _getMain().missingArgumentExit('serialnumber')
  if not body['deviceType']:
    _getMain().missingArgumentExit('devicetype')
  try:
    result = _getMain().callGAPI(ci.devices(), 'create',
                      throwReasons=[GAPI.INVALID, GAPI.INVALID_ARGUMENT, GAPI.PERMISSION_DENIED, GAPI.ALREADY_EXISTS],
                      customer=customer, body=body)
    if 'response' in result:
      _getMain().entityActionPerformed([Ent.COMPANY_DEVICE, _makeDeviceId(f'{result["response"]["name"]}', body)])
    else:
      _getMain().entityActionFailedWarning([Ent.COMPANY_DEVICE, _makeDeviceId('/devices/???', body)], result['error']['message'])
  except (GAPI.invalid, GAPI.invalidArgument, GAPI.permissionDenied, GAPI.alreadyExists) as e:
    _getMain().entityActionFailedWarning([Ent.COMPANY_DEVICE, _makeDeviceId('/devices/???', body)], str(e))

DEVICE_ACTION_CHOICES = {'cancelwipe', 'wipe'}

def _performCIDeviceAction(action):
  entityList, ci, customer, doit = getCIDeviceEntity()
  count = len(entityList)
  action, kwargs = getUpdateDeleteCIDeviceOptions(Ent.DEVICE, count, action, doit, DEVICE_ACTION_CHOICES)
  if action == 'delete':
    kwargs['customer'] = customer
  else:
    kwargs.setdefault('body', {})
    kwargs['body']['customer'] = customer
  i = 0
  for device in entityList:
    i += 1
    name = device['name']
    try:
      result = _getMain().callGAPI(ci.devices(), action,
                        bailOnInternalError=True,
                        throwReasons=[GAPI.NOT_FOUND, GAPI.INVALID, GAPI.INVALID_ARGUMENT,
                                      GAPI.FAILED_PRECONDITION, GAPI.PERMISSION_DENIED, GAPI.INTERNAL_ERROR],
                        name=name, **kwargs)
      if result['done']:
        if 'error' not in result:
          _getMain().entityActionPerformed([Ent.DEVICE, name], i, count)
        else:
          _getMain().entityActionFailedWarning([Ent.DEVICE, name], result['error']['message'], i, count)
      else:
        _getMain().entityActionPerformedMessage([Ent.DEVICE, name], Msg.ACTION_IN_PROGRESS.format(action), i, count)
    except GAPI.notFound:
      _getMain().entityUnknownWarning(Ent.DEVICE, f'{name}', i, count)
    except (GAPI.invalid, GAPI.invalidArgument, GAPI.failedPrecondition, GAPI.permissionDenied, GAPI.internalError) as e:
      _getMain().entityActionFailedWarning([Ent.DEVICE, f'{name}'], str(e), i, count)

# gam delete device <DeviceEntity> [doit]
def doDeleteCIDevice():
  _performCIDeviceAction('delete')

# gam cancelwipe device <DeviceEntity> [doit]
def doCancelWipeCIDevice():
  _performCIDeviceAction('cancelWipe')

# gam wipe device <DeviceEntity> [removeresetlock] [doit]
def doWipeCIDevice():
  _performCIDeviceAction('wipe')

# gam update device <DeviceEntity> action <DeviceAction> [removeresetlock] [doit]
def doUpdateCIDevice():
  _performCIDeviceAction(None)

DEVICE_MISSING_ACTION_MAP = {
  'delete': 'delete',
  'wipe': 'wipe',
  'donothing': 'none',
  'none': 'none',
  }

# gam sync devices
#	<CSVFileSelector>
#	[(query <QueryDevice>)|(queries <QueryDeviceList>) (querytime<String> <Time>)*]
#	(devicetype_column <String>)|(static_devicetype <DeviceType>)
#	(serialnumber_column <String>)
#	[assettag_column <String>]
#	[unassigned_missing_action delete|wipe|none|donothing]
#	[assigned_missing_action delete|wipe|none|donothing]
#	[preview]
def doSyncCIDevices():
  ci = buildGAPICIDeviceServiceObject()
  customer = _getMain()._getCustomersCustomerIdNoC()
  queryTimes = {}
  queries = [None]
  filename = None
  serialNumberColumn = 'serialNumber'
  deviceTypeColumn = 'deviceType'
  assetTagColumn = None
  staticDeviceType = None
  fieldsList = ['serialNumber', 'deviceType', 'lastSyncTime', 'name']
  unassignedMissingAction = 'delete'
  assignedMissingAction = 'none'
  preview = False
  while Cmd.ArgumentsRemaining():
    myarg = _getMain().getArgument()
    if myarg in ['filter', 'filters', 'query', 'queries']:
      queries = _getMain().getDeviceQueries(myarg, Ent.COMPANY_DEVICE)
    elif myarg.startswith('querytime'):
      queryTimes[myarg] = _getMain().getTimeOrDeltaFromNow()[0:19]
    elif myarg in {'csv', 'csvfile'}:
      filename = _getMain().getString(Cmd.OB_STRING)
    elif myarg == 'serialnumbercolumn':
      serialNumberColumn = _getMain().getString(Cmd.OB_STRING)
    elif myarg == 'devicetypecolumn':
      deviceTypeColumn = _getMain().getString(Cmd.OB_STRING)
    elif myarg in {'assettagcolumn', 'assetidcolumn'}:
      assetTagColumn = _getMain().getString(Cmd.OB_STRING)
      fieldsList.append('assetTag')
    elif myarg == 'staticdevicetype':
      staticDeviceType = _getMain().getChoice(DEVICE_TYPE_MAP, mapChoice=True)
    elif myarg == 'unassignedmissingaction':
      unassignedMissingAction = _getMain().getChoice(DEVICE_MISSING_ACTION_MAP, mapChoice=True)
    elif myarg == 'assignedmissingaction':
      assignedMissingAction = _getMain().getChoice(DEVICE_MISSING_ACTION_MAP, mapChoice=True)
    elif myarg == 'preview':
      preview = True
    else:
      _getMain().unknownArgumentExit()
  if not filename:
    _getMain().missingArgumentExit('csvfile')
  f, csvFile, fieldnames = _getMain().openCSVFileReader(filename)
  if serialNumberColumn not in fieldnames:
    _getMain().csvFieldErrorExit(serialNumberColumn, fieldnames)
  if not staticDeviceType and deviceTypeColumn not in fieldnames:
    _getMain().csvFieldErrorExit(deviceTypeColumn, fieldnames)
  if assetTagColumn and assetTagColumn not in fieldnames:
    _getMain().csvFieldErrorExit(assetTagColumn, fieldnames)
  localDevices = {}
  for row in csvFile:
    # upper() is very important to comparison since Google
    # always return uppercase serials
    localDevice = {'serialNumber': row[serialNumberColumn].strip().upper()}
    if staticDeviceType:
      localDevice['deviceType'] = staticDeviceType
    else:
      dt = row[deviceTypeColumn].strip()
      localDevice['deviceType'] = DEVICE_TYPE_MAP.get(dt.lower().replace('_', '').replace('-', ''), dt.upper())
    sndt = f"{localDevice['serialNumber']}-{localDevice['deviceType']}"
    if assetTagColumn:
      localDevice['assetTag'] = row[assetTagColumn].strip()
      sndt += f"-{localDevice['assetTag']}"
    localDevices[sndt] = localDevice
  _getMain().closeFile(f)
  fields = f'nextPageToken,devices({",".join(fieldsList)})'
  remoteDevices = {}
  remoteDeviceMap = {}
  _getMain().substituteQueryTimes(queries, queryTimes)
  for query in queries:
    _getMain().printGettingAllAccountEntities(Ent.COMPANY_DEVICE, query)
    pageMessage = _getMain().getPageMessage()
    try:
      result = _getMain().callGAPIpages(ci.devices(), 'list', 'devices',
                             throwReasons=[GAPI.INVALID, GAPI.INVALID_ARGUMENT, GAPI.PERMISSION_DENIED],
                             retryReasons=GAPI.SERVICE_NOT_AVAILABLE_RETRY_REASONS,
                             pageMessage=pageMessage,
                             customer=customer, filter=query, view='COMPANY_INVENTORY',
                             fields=fields, pageSize=100)
    except (GAPI.invalid, GAPI.invalidArgument, GAPI.permissionDenied) as e:
      _getMain().entityActionFailedWarning([Ent.COMPANY_DEVICE, None], str(e))
      return
    for remoteDevice in result:
      sn = remoteDevice['serialNumber']
      last_sync = remoteDevice.pop('lastSyncTime', _getMain().NEVER_TIME_NOMS)
      name = remoteDevice.pop('name')
      sndt = f"{remoteDevice['serialNumber']}-{remoteDevice['deviceType']}"
      if assetTagColumn:
        if 'assetTag' not in remoteDevice:
          remoteDevice['assetTag'] = ''
        sndt += f"-{remoteDevice['assetTag']}"
      remoteDevices[sndt] = remoteDevice
      remoteDeviceMap[sndt] = {'name': name}
      if last_sync == _getMain().NEVER_TIME_NOMS:
        remoteDeviceMap[sndt]['unassigned'] = True
  devicesToAdd = []
  for sndt, device in localDevices.items():
    if sndt not in remoteDevices:
      devicesToAdd.append(device)
  missingDevices = []
  for sndt, device in remoteDevices.items():
    if sndt not in localDevices:
      missingDevices.append(device)
  Act.Set([Act.CREATE, Act.CREATE_PREVIEW][preview])
  count = len(devicesToAdd)
  _getMain().performActionNumItems(count, Ent.COMPANY_DEVICE)
  i = 0
  for device in devicesToAdd:
    i += 1
    try:
      if not preview:
        result = _getMain().callGAPI(ci.devices(), 'create',
                          throwReasons=[GAPI.INVALID, GAPI.INVALID_ARGUMENT, GAPI.PERMISSION_DENIED, GAPI.ALREADY_EXISTS],
                          customer=customer, body=device)
        if 'error' in result:
          _getMain().entityActionFailedWarning([Ent.COMPANY_DEVICE, _makeDeviceId('/devices/???', device)], result['error']['message'], i, count)
          continue
        deviceId = _makeDeviceId(f'{result["response"]["name"]}', device)
      else:
        deviceId = _makeDeviceId('/devices/???', device)
      _getMain().entityActionPerformed([Ent.COMPANY_DEVICE, deviceId], i, count)
    except (GAPI.invalid, GAPI.invalidArgument, GAPI.permissionDenied, GAPI.alreadyExists) as e:
      _getMain().entityActionFailedWarning([Ent.COMPANY_DEVICE, _makeDeviceId('/devices/???', device)], str(e), i, count)
  Act.Set([Act.PROCESS, Act.PROCESS_PREVIEW][preview])
  count = len(missingDevices)
  _getMain().performActionNumItems(count, Ent.COMPANY_DEVICE)
  i = 0
  for device in missingDevices:
    i += 1
    sn = device['serialNumber']
    sndt = f"{sn}-{device['deviceType']}"
    if assetTagColumn:
      sndt += f"-{device['assetTag']}"
    name = remoteDeviceMap[sndt]['name']
    deviceId = _makeDeviceId(f'{name}', device)
    unassigned = remoteDeviceMap[sndt].get('unassigned')
    action = unassignedMissingAction if unassigned else assignedMissingAction
    if action == 'none':
      Act.Set([Act.NOACTION, Act.NOACTION_PREVIEW][preview])
      _getMain().entityActionPerformed([Ent.COMPANY_DEVICE, deviceId], i, count)
      continue
    if action == 'delete':
      Act.Set([Act.DELETE, Act.DELETE_PREVIEW][preview])
      kwargs = {'customer': customer}
    else:
      Act.Set([Act.WIPE, Act.WIPE_PREVIEW][preview])
      kwargs = {'body': {'customer': customer}}
    try:
      if not preview:
        result = _getMain().callGAPI(ci.devices(), action,
                          bailOnInternalError=True,
                          throwReasons=[GAPI.NOT_FOUND, GAPI.INVALID, GAPI.INVALID_ARGUMENT,
                                        GAPI.FAILED_PRECONDITION, GAPI.PERMISSION_DENIED, GAPI.INTERNAL_ERROR],
                          name=name, **kwargs)
      else:
        result = {'done': True}
      if result['done']:
        if 'error' not in result:
          _getMain().entityActionPerformed([Ent.COMPANY_DEVICE, deviceId], i, count)
        else:
          _getMain().entityActionFailedWarning([Ent.COMPANY_DEVICE, deviceId], result['error']['message'], i, count)
      else:
        _getMain().entityActionPerformedMessage([Ent.COMPANY_DEVICE, deviceId], Msg.ACTION_IN_PROGRESS.format(action), i, count)
    except GAPI.notFound:
      _getMain().entityUnknownWarning(Ent.COMPANY_DEVICE, deviceId, i, count)
    except (GAPI.invalid, GAPI.invalidArgument, GAPI.failedPrecondition, GAPI.permissionDenied, GAPI.internalError) as e:
      _getMain().entityActionFailedWarning([Ent.COMPANY_DEVICE, deviceId], str(e), i, count)

DEVICE_FIELDS_CHOICE_MAP = {
  'androidspecificattributes': 'androidSpecificAttributes',
  'assettag': 'assetTag',
  'basebandversion': 'basebandVersion',
  'bootloaderversion': 'bootloaderVersion',
  'brand': 'brand',
  'buildnumber': 'buildNumber',
  'compromisedstate': 'compromisedState',
  'createtime': 'createTime',
  'deviceid': 'deviceId',
  'devicetype': 'deviceType',
  'enableddeveloperoptions': 'enabledDeveloperOptions',
  'enabledusbdebugging': 'enabledUsbDebugging',
  'encryptionstate': 'encryptionState',
  'endpointverificationspecificattributes': 'endpointVerificationSpecificAttributes',
  'hostname': 'hostname',
  'imei': 'imei',
  'kernelversion': 'kernelVersion',
  'lastsynctime': 'lastSyncTime',
  'managementstate': 'managementState',
  'manufacturer': 'manufacturer',
  'meid': 'meid',
  'model': 'model',
  'name': 'name',
  'networkoperator': 'networkOperator',
  'osversion': 'osVersion',
  'otheraccounts': 'otherAccounts',
  'ownertype': 'ownerType',
  'releaseversion': 'releaseVersion',
  'securitypatchtime': 'securityPatchTime',
  'serialnumber': 'serialNumber',
  'unifieddeviceid': 'unifiedDeviceId',
  'wifimacaddresses': 'wifiMacAddresses'
  }

DEVICEUSER_FIELDS_CHOICE_MAP = {
  'compromisedstate': 'compromisedState',
  'createtime': 'createTime',
  'firstsynctime': 'firstSyncTime',
  'languagecode': 'languageCode',
  'lastsynctime': 'lastSyncTime',
  'managementstate': 'managementState',
  'name': 'name',
  'passwordstate': 'passwordState',
  'useragent': 'userAgent',
  'useremail': 'userEmail',
  }

# gam info device <DeviceEntity>
#	<DeviceFieldName>* [fields <DevieFieldNameList>] [userfields <DeviceUserFieldNameList>]
#	[nodeviceusers]
#	[formatjson]
def doInfoCIDevice():
  entityList, ci, customer, _ = getCIDeviceEntity()
  FJQC = _getMain().FormatJSONQuoteChar()
  fieldsList = []
  userFieldsList = []
  getDeviceUsers = True
  while Cmd.ArgumentsRemaining():
    myarg = _getMain().getArgument()
    if _getMain().getFieldsList(myarg, DEVICE_FIELDS_CHOICE_MAP, fieldsList, initialField='name'):
      pass
    elif _getMain().getFieldsList(myarg, DEVICEUSER_FIELDS_CHOICE_MAP, userFieldsList, initialField='name', fieldsArg='userfields'):
      pass
    elif myarg == 'nodeviceusers':
      getDeviceUsers = False
    else:
      FJQC.GetFormatJSON(myarg)
  fields = _getMain().getFieldsFromFieldsList(fieldsList)
  userFields = _getMain().getItemFieldsFromFieldsList('deviceUsers', userFieldsList)
  i = 0
  count = len(entityList)
  for device in entityList:
    i += 1
    name = device['name']
    try:
      device = _getMain().callGAPI(ci.devices(), 'get',
                        throwReasons=[GAPI.NOT_FOUND, GAPI.INVALID, GAPI.INVALID_ARGUMENT, GAPI.PERMISSION_DENIED],
                        name=name, customer=customer, fields=fields)
      if getDeviceUsers:
        device_users = _getMain().callGAPIpages(ci.devices().deviceUsers(), 'list', 'deviceUsers',
                                     throwReasons=[GAPI.INVALID, GAPI.INVALID_ARGUMENT, GAPI.PERMISSION_DENIED],
                                     parent=name, customer=customer, fields=userFields)
        for device_user in device_users:
          device_user['client_states'] = _getMain().callGAPIpages(ci.devices().deviceUsers().clientStates(), 'list', 'clientStates',
                                                       throwReasons=[GAPI.INVALID, GAPI.INVALID_ARGUMENT, GAPI.PERMISSION_DENIED],
                                                       parent=device_user['name'], customer=customer)
      else:
        device_users = []
      if FJQC.formatJSON:
        if getDeviceUsers:
          device['users'] = device_users
        _getMain().printLine(json.dumps(_getMain().cleanJSON(device, timeObjects=DEVICE_TIME_OBJECTS), ensure_ascii=False, sort_keys=True))
      else:
        _getMain().printEntity([Ent.DEVICE, device.pop('name')])
        Ind.Increment()
        _getMain().showJSON(None, device, timeObjects=DEVICE_TIME_OBJECTS)
        count = len(device_users)
        i = 0
        for device_user in device_users:
          i += 1
          _getMain().printEntity([Ent.DEVICE_USER, device_user.pop('name')], i, count)
          Ind.Increment()
          _getMain().showJSON(None, device_user, timeObjects=DEVICE_TIME_OBJECTS)
          Ind.Decrement()
        Ind.Decrement()
    except GAPI.notFound:
      _getMain().entityUnknownWarning(Ent.DEVICE, f'{name}')
    except (GAPI.invalid, GAPI.invalidArgument, GAPI.permissionDenied) as e:
      _getMain().entityActionFailedWarning([Ent.DEVICE, f'{name}'], str(e))

DEVICE_VIEW_CHOICE_MAP = {
  'all': (None, Ent.DEVICE),
  'company': ('COMPANY_INVENTORY', Ent.COMPANY_DEVICE),
  'personal': ('USER_ASSIGNED_DEVICES', Ent.PERSONAL_DEVICE),
  'nocompanydevices': ('USER_ASSIGNED_DEVICES', Ent.PERSONAL_DEVICE),
  'nopersonaldevices': ('COMPANY_INVENTORY', Ent.COMPANY_DEVICE)
  }
DEVICE_ORDERBY_CHOICE_MAP = {
  'createtime': 'create_time',
  'devicetype': 'device_type',
  'lastsynctime': 'last_sync_time',
  'model': 'model',
  'osversion': 'os_version',
  'serialnumber': 'serial_number'
  }

# gam print devices [todrive <ToDriveAttribute>*]
#	[(query <QueryDevice>)|(queries <QueryDeviceList>) (querytime<String> <Time>)*]
#	<DeviceFieldName>* [fields <DeviceFieldNameList>] [userfields <DeviceUserFieldNameList>]
#	[orderby <DeviceOrderByFieldName> [ascending|descending]]
#	[all|company|personal|nocompanydevices|nopersonaldevices]
#	[nodeviceusers|oneuserperrow]
#	[clientstates]
#	[formatjson [quotechar <Character>]]
# 	[showitemcountonly]
def doPrintCIDevices():
  ci = buildGAPICIDeviceServiceObject()
  customer = _getMain()._getCustomersCustomerIdNoC()
  parent = 'devices/-'
  csvPF = _getMain().CSVPrintFile(['name'], 'sortall') if Act.csvFormat() else None
  FJQC = _getMain().FormatJSONQuoteChar(csvPF)
  OBY = _getMain().OrderBy(DEVICE_ORDERBY_CHOICE_MAP)
  fieldsList = []
  userFieldsList = []
  queryTimes = {}
  queries = [None]
  view, entityType = DEVICE_VIEW_CHOICE_MAP['all']
  getDeviceUsers = True
  getClientStates = False
  oneUserPerRow = showItemCountOnly = False
  while Cmd.ArgumentsRemaining():
    myarg = _getMain().getArgument()
    if csvPF and myarg == 'todrive':
      csvPF.GetTodriveParameters()
    elif myarg in ['filter', 'filters', 'query', 'queries']:
      queries = _getMain().getDeviceQueries(myarg, entityType)
    elif myarg.startswith('querytime'):
      queryTimes[myarg] = _getMain().getTimeOrDeltaFromNow()[0:19]
    elif myarg == 'orderby':
      OBY.GetChoice()
    elif myarg in DEVICE_VIEW_CHOICE_MAP:
      view, entityType = DEVICE_VIEW_CHOICE_MAP[myarg]
    elif myarg == 'nodeviceusers':
      getDeviceUsers = False
    elif myarg == 'clientstates':
      getClientStates = True
    elif myarg in {'oneuserperrow', 'oneitemperrow'}:
      getDeviceUsers = oneUserPerRow = True
    elif _getMain().getFieldsList(myarg, DEVICE_FIELDS_CHOICE_MAP, fieldsList, initialField='name'):
      pass
    elif _getMain().getFieldsList(myarg, DEVICEUSER_FIELDS_CHOICE_MAP, userFieldsList, initialField='name', fieldsArg='userfields'):
      pass
    elif myarg == 'sortheaders':
      pass
    elif myarg == 'showitemcountonly':
      showItemCountOnly = True
    else:
      FJQC.GetFormatJSONQuoteChar(myarg, True)
  fields = _getMain().getItemFieldsFromFieldsList('devices', fieldsList)
  userFields = _getMain().getItemFieldsFromFieldsList('deviceUsers', userFieldsList)
  _getMain().substituteQueryTimes(queries, queryTimes)
  if FJQC.formatJSON and oneUserPerRow:
    csvPF.SetJSONTitles(['name', 'user.name', 'JSON'])
  itemCount = 0
  throwReasons = [GAPI.INVALID, GAPI.INVALID_ARGUMENT, GAPI.PERMISSION_DENIED]
  retryReasons = GAPI.SERVICE_NOT_AVAILABLE_RETRY_REASONS
  for query in queries:
    _getMain().printGettingAllAccountEntities(entityType, query)
    pageMessage = _getMain().getPageMessage()
    try:
      devices = _getMain().callGAPIpages(ci.devices(), 'list', 'devices',
                              pageMessage=pageMessage,
                              throwReasons=throwReasons,
                              retryReasons=retryReasons,
                              customer=customer, filter=query,
                              orderBy=OBY.orderBy, view=view, fields=fields, pageSize=100)
      if showItemCountOnly:
        itemCount += len(devices)
        continue
    except (GAPI.invalid, GAPI.invalidArgument, GAPI.permissionDenied) as e:
      _getMain().entityActionFailedWarning([entityType, None], str(e))
      continue
    if getDeviceUsers:
      ci._http.credentials.refresh(_getMain().transportCreateRequest())
      deviceDict = {}
      for device in devices:
        deviceDict[device['name']] = device
      _getMain().printGettingAllAccountEntities(Ent.DEVICE_USER, query)
      pageMessage = _getMain().getPageMessage()
      try:
        deviceUsers = _getMain().callGAPIpages(ci.devices().deviceUsers(), 'list', 'deviceUsers',
                                    pageMessage=pageMessage,
                                    throwReasons=throwReasons,
                                    retryReasons=retryReasons,
                                    customer=customer, filter=query, parent=parent,
                                    orderBy=OBY.orderBy, fields=userFields, pageSize=20)
        if getClientStates:
          _getMain().printGettingAllAccountEntities(Ent.DEVICE_USER_CLIENT_STATE, None)
          states = _getMain().callGAPIpages(ci.devices().deviceUsers().clientStates(), 'list', 'clientStates',
                                 pageMessage=pageMessage,
                                 throwReasons=throwReasons,
                                 retryReasons=retryReasons,
                                 customer=customer, filter=query, parent='devices/-/deviceUsers/-')
          for state in states:
            mg = DEVICE_USERNAME_CLIENT_STATE_PATTERN.match(state['name'])
            if mg:
              du = mg.group(1)
              state_name = mg.group(2)
              for deviceUser in deviceUsers:
                if deviceUser['name'] == du:
                  deviceUser.setdefault('clientstates', {})
                  deviceUser['clientstates'][state_name] = state
                  break
        for deviceUser in deviceUsers:
          mg = DEVICE_USERNAME_PATTERN.match(deviceUser['name'])
          if mg:
            deviceName = mg.group(1)
            if deviceName in deviceDict:
              deviceDict[deviceName].setdefault('users', [])
              deviceDict[deviceName]['users'].append(deviceUser)
      except (GAPI.invalid, GAPI.invalidArgument, GAPI.permissionDenied) as e:
        _getMain().entityActionFailedWarning([entityType, None], str(e))
    for device in devices:
      if not oneUserPerRow or 'users' not in device:
        row = _getMain().flattenJSON(device, timeObjects=DEVICE_TIME_OBJECTS)
        if not FJQC.formatJSON:
          csvPF.WriteRowTitles(row)
        elif csvPF.CheckRowTitles(row):
          csvPF.WriteRowNoFilter({'name': device['name'],
                                  'JSON': json.dumps(_getMain().cleanJSON(device, timeObjects=DEVICE_TIME_OBJECTS),
                                                     ensure_ascii=False, sort_keys=True)})
      else:
        deviceUsers = device.pop('users')
        baserow = _getMain().flattenJSON(device, timeObjects=DEVICE_TIME_OBJECTS)
        for deviceUser in deviceUsers:
          row = _getMain().flattenJSON({'user': deviceUser}, flattened=baserow.copy(), timeObjects=DEVICE_TIME_OBJECTS)
          if not FJQC.formatJSON:
            csvPF.WriteRowTitles(row)
          elif csvPF.CheckRowTitles(row):
            device['user'] = deviceUser
            csvPF.WriteRowNoFilter({'name': device['name'], 'user.name': deviceUser['name'],
                                    'JSON': json.dumps(_getMain().cleanJSON(device, timeObjects=DEVICE_TIME_OBJECTS),
                                                       ensure_ascii=False, sort_keys=True)})
  if showItemCountOnly:
    _getMain().writeStdout(f'{itemCount}\n')
    return
  csvPF.writeCSVfile('Devices')

DEVICE_USER_ACTION_CHOICES = {'approve', 'block', 'cancelwipe', 'wipe'}

def _performCIDeviceUserAction(action):
  entityList, ci, customer, doit = getCIDeviceUserEntity()
  count = len(entityList)
  action, kwargs = getUpdateDeleteCIDeviceOptions(Ent.DEVICE_USER, count, action, doit, DEVICE_USER_ACTION_CHOICES)
  if action == 'delete':
    kwargs['customer'] = customer
  else:
    kwargs.setdefault('body', {})
    kwargs['body']['customer'] = customer
  i = 0
  for deviceUser in entityList:
    i += 1
    name = deviceUser['name']
    try:
      result = _getMain().callGAPI(ci.devices().deviceUsers(), action,
                        bailOnInternalError=True,
                        throwReasons=[GAPI.NOT_FOUND, GAPI.INVALID, GAPI.INVALID_ARGUMENT,
                                      GAPI.FAILED_PRECONDITION, GAPI.PERMISSION_DENIED, GAPI.INTERNAL_ERROR],
                        name=name, **kwargs)
      if result['done']:
        if 'error' not in result:
          _getMain().entityActionPerformed([Ent.DEVICE_USER, name], i, count)
        else:
          _getMain().entityActionFailedWarning([Ent.DEVICE_USER, name], result['error']['message'], i, count)
      else:
        _getMain().entityActionPerformedMessage([Ent.DEVICE_USER, name], Msg.ACTION_IN_PROGRESS.format(action), i, count)
      Ind.Increment()
      _getMain().showJSON(None, result, timeObjects=DEVICE_TIME_OBJECTS)
      Ind.Decrement()
    except GAPI.notFound:
      _getMain().entityUnknownWarning(Ent.DEVICE_USER, f'{name}', i, count)
    except (GAPI.invalid, GAPI.invalidArgument, GAPI.failedPrecondition, GAPI.permissionDenied, GAPI.internalError) as e:
      _getMain().entityActionFailedWarning([Ent.DEVICE_USER, f'{name}'], str(e), i, count)

# gam approve deviceuser <DeviceUserEntity> [doit]
def doApproveCIDeviceUser():
  _performCIDeviceUserAction('approve')

# gam block deviceuser <DeviceUserEntity> [doit]
def doBlockCIDeviceUser():
  _performCIDeviceUserAction('block')

# gam delete deviceuser <DeviceUserEntity> [doit]
def doDeleteCIDeviceUser():
  _performCIDeviceUserAction('delete')

# gam cancelwipe deviceuser <DeviceUserEntity> [doit]
def doCancelWipeCIDeviceUser():
  _performCIDeviceUserAction('cancelWipe')

# gam wipe deviceuser <DeviceUserEntity> [doit]
def doWipeCIDeviceUser():
  _performCIDeviceUserAction('wipe')

# gam update deviceuser <DeviceUserEntity> action <DeviceUserAction> [doit]
def doUpdateCIDeviceUser():
  _performCIDeviceUserAction(None)

# gam info deviceuser <DeviceUserEntity>
#	<DeviceUserFieldName>* [fields <DevieUserFieldNameList>]
#	[formatjson]
def doInfoCIDeviceUser():
  entityList, ci, customer, _ = getCIDeviceUserEntity()
  FJQC = _getMain().FormatJSONQuoteChar()
  userFieldsList = []
  while Cmd.ArgumentsRemaining():
    myarg = _getMain().getArgument()
    if _getMain().getFieldsList(myarg, DEVICE_FIELDS_CHOICE_MAP, userFieldsList, initialField='name'):
      pass
    else:
      FJQC.GetFormatJSON(myarg)
  userFields = _getMain().getFieldsFromFieldsList(userFieldsList)
  i = 0
  count = len(entityList)
  for deviceUser in entityList:
    i += 1
    name = deviceUser['name']
    try:
      deviceUser = _getMain().callGAPI(ci.devices().deviceUsers(), 'get',
                            throwReasons=[GAPI.NOT_FOUND, GAPI.INVALID, GAPI.INVALID_ARGUMENT, GAPI.PERMISSION_DENIED],
                            name=name, customer=customer, fields=userFields)
      deviceUser['client_states'] = _getMain().callGAPIpages(ci.devices().deviceUsers().clientStates(), 'list', 'clientStates',
                                                  throwReasons=[GAPI.INVALID, GAPI.INVALID_ARGUMENT, GAPI.PERMISSION_DENIED],
                                                  parent=deviceUser['name'], customer=customer)
      if FJQC.formatJSON:
        _getMain().printLine(json.dumps(_getMain().cleanJSON(deviceUser, timeObjects=DEVICE_TIME_OBJECTS), ensure_ascii=False, sort_keys=True))
      else:
        _getMain().printEntity([Ent.DEVICE_USER, deviceUser.pop('name')], i, count)
        Ind.Increment()
        _getMain().showJSON(None, deviceUser, timeObjects=DEVICE_TIME_OBJECTS)
        Ind.Decrement()
    except GAPI.notFound:
      _getMain().entityUnknownWarning(Ent.DEVICE_USER, f'{name}', i, count)
    except (GAPI.invalid, GAPI.invalidArgument, GAPI.permissionDenied) as e:
      _getMain().entityActionFailedWarning([Ent.DEVICE_USER, f'{name}'], str(e), i, count)

# gam print deviceusers [todrive <ToDriveAttribute>*]
#	[select <DeviceID>]
#	[(query <QueryDevice>)|(queries <QueryDeviceList>) (querytime<String> <Time>)*]
#	<DeviceUserFieldName>* [fields <DevieUserFieldNameList>]
#	[orderby <DeviceOrderByFieldName> [ascending|descending]]
#	[formatjson [quotechar <Character>]]
# 	[showitemcountonly]
def doPrintCIDeviceUsers():
  ci = buildGAPICIDeviceServiceObject()
  customer = _getMain()._getCustomersCustomerIdNoC()
  csvPF = _getMain().CSVPrintFile(['name'], 'sortall') if Act.csvFormat() else None
  FJQC = _getMain().FormatJSONQuoteChar(csvPF)
  OBY = _getMain().OrderBy(DEVICE_ORDERBY_CHOICE_MAP)
  userFieldsList = []
  queryTimes = {}
  queries = [None]
  parent = 'devices/-'
  showItemCountOnly = False
  while Cmd.ArgumentsRemaining():
    myarg = _getMain().getArgument()
    if csvPF and myarg == 'todrive':
      csvPF.GetTodriveParameters()
    elif myarg == 'select':
      parent = _getMain().getString(Cmd.OB_DEVICE_ID)
      if not parent.startswith('devices/'):
        parent = f'devices/{parent}'
    elif myarg in ['filter', 'filters', 'query', 'queries']:
      queries = _getMain().getDeviceQueries(myarg, Ent.DEVICE_USER)
    elif myarg.startswith('querytime'):
      queryTimes[myarg] = _getMain().getTimeOrDeltaFromNow()[0:19]
    elif myarg == 'orderby':
      OBY.GetChoice()
    elif _getMain().getFieldsList(myarg, DEVICEUSER_FIELDS_CHOICE_MAP, userFieldsList, initialField='name'):
      pass
    elif myarg == 'sortheaders':
      pass
    elif myarg == 'showitemcountonly':
      showItemCountOnly = True
    else:
      FJQC.GetFormatJSONQuoteChar(myarg, True)
  userFields = _getMain().getItemFieldsFromFieldsList('deviceUsers', userFieldsList)
  _getMain().substituteQueryTimes(queries, queryTimes)
  itemCount = 0
  for query in queries:
    _getMain().printGettingAllAccountEntities(Ent.DEVICE_USER, query)
    pageMessage = _getMain().getPageMessage()
    try:
      deviceUsers = _getMain().callGAPIpages(ci.devices().deviceUsers(), 'list', 'deviceUsers',
                                  pageMessage=pageMessage,
                                  throwReasons=[GAPI.INVALID, GAPI.INVALID_ARGUMENT, GAPI.PERMISSION_DENIED],
                                  retryReasons=GAPI.SERVICE_NOT_AVAILABLE_RETRY_REASONS,
                                  customer=customer, filter=query,
                                  orderBy=OBY.orderBy, parent=parent, fields=userFields, pageSize=20)
      if showItemCountOnly:
        itemCount += len(deviceUsers)
        continue
      for deviceUser in deviceUsers:
        row = _getMain().flattenJSON(deviceUser, timeObjects=DEVICE_TIME_OBJECTS)
        if not FJQC.formatJSON:
          csvPF.WriteRowTitles(row)
        elif csvPF.CheckRowTitles(row):
          csvPF.WriteRowNoFilter({'name': deviceUser['name'],
                                'JSON': json.dumps(_getMain().cleanJSON(deviceUser, timeObjects=DEVICE_TIME_OBJECTS),
                                                     ensure_ascii=False, sort_keys=True)})
    except (GAPI.invalid, GAPI.invalidArgument, GAPI.permissionDenied) as e:
      _getMain().entityActionFailedWarning([Ent.DEVICE_USER, None], str(e))
      break
  if showItemCountOnly:
    _getMain().writeStdout(f'{itemCount}\n')
    return
  csvPF.writeCSVfile('Device Users')

DEVICE_USER_COMPLIANCE_STATE_CHOICE_MAP = {
  'compliant': 'COMPLIANT',
  'noncompliant': 'NON_COMPLIANT'
  }
DEVICE_USER_HEALTH_SCORE_CHOICE_MAP = {
  'verypoor': 'VERY_POOR',
  'poor': 'POOR',
  'neutral': 'NEUTRAL',
  'good': 'GOOD',
  'verygood': 'VERY_GOOD'
  }
DEVICE_USER_MANAGED_STATE_CHOICE_MAP = {
  'clear': None,
  'managed': 'MANAGED',
  'unmanaged': 'UNMANAGED'
  }
DEVICE_USER_CUSTOM_VALUE_TYPE_CHOICE_MAP = {
  'clear': 'clear',
  'bool': 'boolValue',
  'boolean': 'boolValue',
  'number': 'numberValue',
  'string': 'stringValue'
  }

# gam info deviceuserstate <DeviceUserEntity> [clientid <String>]
def doInfoCIDeviceUserState():
  _getMain().setTrueCustomerId()
  entityList, ci, customer, _ = getCIDeviceUserEntity()
  customerID = customer[10:]
  client_id = f'{customerID}-gam'
  while Cmd.ArgumentsRemaining():
    myarg = _getMain().getArgument()
    if myarg == 'clientid':
      client_id = f'{customerID}-{_getMain().getString(Cmd.OB_STRING)}'
    else:
      _getMain().unknownArgumentExit()
  count = len(entityList)
  i = 0
  for deviceUser in entityList:
    i += 1
    deviceUser = deviceUser['name']
    name = f'{deviceUser}/clientStates/{client_id}'
    try:
      result = _getMain().callGAPI(ci.devices().deviceUsers().clientStates(), 'get',
                        bailOnInternalError=True,
                        throwReasons=[GAPI.NOT_FOUND, GAPI.INVALID, GAPI.INVALID_ARGUMENT,
                                      GAPI.FAILED_PRECONDITION, GAPI.PERMISSION_DENIED, GAPI.INTERNAL_ERROR],
                        name=name, customer=customer)
      _getMain().printEntity([Ent.DEVICE_USER_CLIENT_STATE, name], i, count)
      Ind.Increment()
      result.pop('name', None)
      _getMain().showJSON(None, result, timeObjects=DEVICE_TIME_OBJECTS)
      Ind.Decrement()
    except GAPI.notFound:
      _getMain().entityUnknownWarning(Ent.DEVICE_USER, deviceUser, i, count)
    except (GAPI.invalid, GAPI.invalidArgument, GAPI.failedPrecondition, GAPI.permissionDenied, GAPI.internalError) as e:
      _getMain().entityActionFailedWarning([Ent.DEVICE_USER, deviceUser], str(e), i, count)

# gam update deviceuserstate <DeviceUserEntity> [clientid <String>]
#	[customid <String>] [assettags clear|<AssetTagList>]
#	[compliantstate|compliancestate compliant|noncompliant] [managedstate clear|managed|unmanaged]
#	[healthscore verypoor|poor|neutral|good|verygood] [scorereason clear|<String>]
#	(customvalue clear|(bool|boolean <String> <Boolean>)|(number <String> <Integer>)(string <String> <String>))*
def doUpdateCIDeviceUserState():
  _getMain().setTrueCustomerId()
  entityList, ci, customer, _ = getCIDeviceUserEntity()
  customerID = customer[10:]
  client_id = f'{customerID}-gam'
  body = {}
  while Cmd.ArgumentsRemaining():
    myarg = _getMain().getArgument()
    if myarg == 'clientid':
      client_id = f'{customerID}-{_getMain().getString(Cmd.OB_STRING)}'
    elif myarg in ['compliantstate', 'compliancestate']:
      body['complianceState'] = _getMain().getChoice(DEVICE_USER_COMPLIANCE_STATE_CHOICE_MAP, mapChoice=True)
    elif myarg == 'healthscore':
      body['healthScore'] = _getMain().getChoice(DEVICE_USER_HEALTH_SCORE_CHOICE_MAP, mapChoice=True)
    elif myarg in ['scorereason']:
      body['scoreReason'] = _getMain().getString(Cmd.OB_STRING)
      if body['scoreReason'] == 'clear':
        body['scoreReason'] = None
    elif myarg == 'customid':
      body['customId'] = _getMain().getString(Cmd.OB_STRING, minLen=0)
    elif myarg == 'managedstate':
      body['managed'] = _getMain().getChoice(DEVICE_USER_MANAGED_STATE_CHOICE_MAP, mapChoice=True)
    # TODO: assetTags and keyValuePairs can't be cleared; figure out why.
    elif myarg in ['assettag', 'assettags']:
      body['assetTags'] = _getMain().convertEntityToList(_getMain().getString(Cmd.OB_STRING, minLen=0), shlexSplit=True)
      if not body['assetTags'] or body['assetTags'] == ['clear']:
        body['assetTags'] = []
    elif myarg == 'customvalue':
      valueType = _getMain().getChoice(DEVICE_USER_CUSTOM_VALUE_TYPE_CHOICE_MAP, mapChoice=True)
      if valueType != 'clear':
        key = _getMain().getString(Cmd.OB_STRING)
        if valueType == 'boolValue':
          value = _getMain().getBoolean()
        elif valueType == 'numberValue':
          value = _getMain().getInteger()
        else: # stringValue
          value = _getMain().getString(Cmd.OB_STRING)
        body.setdefault('keyValuePairs', {})
        body['keyValuePairs'][key] = {valueType: value}
      else:
        body['keyValuePairs'] = {}
    else:
      _getMain().unknownArgumentExit()
  count = len(entityList)
  i = 0
  for deviceUser in entityList:
    i += 1
    deviceUser = deviceUser['name']
    name = f'{deviceUser}/clientStates/{client_id}'
    try:
      result = _getMain().callGAPI(ci.devices().deviceUsers().clientStates(), 'patch',
                        bailOnInternalError=True,
                        throwReasons=[GAPI.NOT_FOUND, GAPI.INVALID, GAPI.INVALID_ARGUMENT,
                                      GAPI.FAILED_PRECONDITION, GAPI.PERMISSION_DENIED, GAPI.INTERNAL_ERROR],
                        name=name, customer=customer, updateMask=','.join(body.keys()), body=body)
      if result['done']:
        if 'error' not in result:
          _getMain().entityActionPerformed([Ent.DEVICE_USER_CLIENT_STATE, name], i, count)
          result = result['response']
          result.pop('name')
        else:
          _getMain().entityActionFailedWarning([Ent.DEVICE_USER_CLIENT_STATE, name], result['error']['message'], i, count)
      else:
        _getMain().entityActionPerformedMessage([Ent.DEVICE_USER_CLIENT_STATE, name], Msg.ACTION_IN_PROGRESS.format('update Client State'), i, count)
      Ind.Increment()
      _getMain().showJSON(None, result, timeObjects=DEVICE_TIME_OBJECTS)
      Ind.Decrement()
    except GAPI.notFound:
      _getMain().entityUnknownWarning(Ent.DEVICE_USER, deviceUser)
    except (GAPI.invalid, GAPI.invalidArgument, GAPI.failedPrecondition, GAPI.permissionDenied, GAPI.internalError) as e:
      _getMain().entityActionFailedWarning([Ent.DEVICE_USER, deviceUser], str(e))

