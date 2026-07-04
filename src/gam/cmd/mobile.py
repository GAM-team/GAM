"""GAM mobile device management."""

import json

from gamlib import api as API
from gamlib import settings as GC
from gamlib import gapi as GAPI
from gamlib import state as GM
from gamlib import msgs as Msg
from gam.var import Act, Cmd, Ent, Ind
from gam.util.api import buildGAPIObject
from gam.util.api_call import callGAPI, callGAPIpages, yieldGAPIpages
from gam.util.args import (
    UTF8,
    checkArgumentPresent,
    formatLocalTime,
    formatLocalTimestamp,
    getArgument,
    getCharacter,
    getChoice,
    getInteger,
    getOrderBySortOrder,
    getString,
    getTimeOrDeltaFromNow,
    normalizeEmailAddressOrUID,
    substituteQueryTimes,
)
from gam.util.csv_pf import (
    CSVPrintFile,
    DEFAULT_SKIP_OBJECTS,
    FormatJSONQuoteChar,
    cleanJSON,
    flattenJSON,
    getFieldsFromFieldsList,
    getFieldsList,
    getItemFieldsFromFieldsList,
    showJSON,
)
from gam.util.display import (
    entityActionFailedWarning,
    entityActionNotPerformedWarning,
    entityActionPerformed,
    getPageMessage,
    invalidQuery,
    printEntity,
    printEntityKVList,
    printGettingAllAccountEntities,
    printGotAccountEntities,
    printLine,
)
from gam.util.entity import _validateDeviceQuery, getDeviceQueries, getEntityList, getEntityToModify
from gam.util.errors import unknownArgumentExit, usageErrorExit
from gam.util.fileio import UNKNOWN
from gam.util.output import writeStdout
from gam.constants import PROJECTION_CHOICE_MAP


def getMobileDeviceEntity():
  cd = buildGAPIObject(API.DIRECTORY)
  if checkArgumentPresent('query'):
    query = getString(Cmd.OB_QUERY)
  else:
    resourceId = getString(Cmd.OB_MOBILE_DEVICE_ENTITY)
    if resourceId[:6].lower() == 'query:':
      query = resourceId[6:]
    else:
      Cmd.Backup()
      query = None
  if not query:
    return ([{'resourceId': device, 'email': []} for device in getEntityList(Cmd.OB_MOBILE_ENTITY)], cd, True)
  _validateDeviceQuery(Ent.MOBILE_DEVICE, query)
  try:
    printGettingAllAccountEntities(Ent.MOBILE_DEVICE, query)
    devices = callGAPIpages(cd.mobiledevices(), 'list', 'mobiledevices',
                            pageMessage=getPageMessage(),
                            throwReasons=[GAPI.INVALID_INPUT, GAPI.BAD_REQUEST, GAPI.RESOURCE_NOT_FOUND,
                                          GAPI.FORBIDDEN, GAPI.PERMISSION_DENIED],
                            customerId=GC.Values[GC.CUSTOMER_ID], query=query,
                            fields='nextPageToken,mobiledevices(resourceId,email)')
    return ([{'resourceId': device['resourceId'], 'email': device.get('email', [])} for device in devices], cd, False)
  except GAPI.invalidInput:
    Cmd.Backup()
    usageErrorExit(Msg.INVALID_QUERY)
  except (GAPI.badRequest, GAPI.resourceNotFound):
    accessErrorExit(cd)
  except (GAPI.forbidden, GAPI.permissionDenied) as e:
    ClientAPIAccessDeniedExit(str(e))

def _getUpdateDeleteMobileOptions(myarg, options):
  if myarg in {'matchusers', 'ifusers'}:
    _, matchUsers = getEntityToModify(defaultEntityType=Cmd.ENTITY_USERS)
    options['matchUsers'] = {normalizeEmailAddressOrUID(user) for user in matchUsers}
  elif myarg == 'doit':
    options['doit'] = True
  else:
    unknownArgumentExit()

def _getMobileDeviceUser(mobileDevice, options):
  if options['matchUsers']:
    if mobileDevice['email']:
      for deviceUser in mobileDevice['email']:
        if deviceUser.lower() in options['matchUsers']:
          return (deviceUser, True)
      return (mobileDevice['email'][0], False)
    return (UNKNOWN, False)
  if mobileDevice['email']:
    return (mobileDevice['email'][0], True)
  return (UNKNOWN, True)

# gam update mobile|mobiles <MobileDeviceEntity> action <MobileAction>
#	[doit] [matchusers <UserTypeEntity>]
def doUpdateMobileDevices():
  entityList, cd, doit = getMobileDeviceEntity()
  body = {}
  options = {'doit': doit, 'matchUsers': set()}
  while Cmd.ArgumentsRemaining():
    myarg = getArgument()
    if myarg == 'action':
      body['action'] = getChoice(MOBILE_ACTION_CHOICE_MAP, mapChoice=True)
    else:
      _getUpdateDeleteMobileOptions(myarg, options)
  if not body:
    entityActionNotPerformedWarning([Ent.MOBILE_DEVICE, None], Msg.NO_ACTION_SPECIFIED)
    return
  i = 0
  count = len(entityList)
  for device in entityList:
    i += 1
    resourceId = device['resourceId']
    deviceUser, status = _getMobileDeviceUser(device, options)
    if not status:
      entityActionNotPerformedWarning([Ent.MOBILE_DEVICE, resourceId, Ent.USER, deviceUser], Msg.USER_NOT_IN_MATCHUSERS, i, count)
    elif not options['doit']:
      entityActionNotPerformedWarning([Ent.MOBILE_DEVICE, resourceId, Ent.USER, deviceUser], Msg.USE_DOIT_ARGUMENT_TO_PERFORM_ACTION, i, count)
    else:
      try:
        callGAPI(cd.mobiledevices(), 'action',
                 bailOnInternalError=True,
                 throwReasons=[GAPI.INTERNAL_ERROR, GAPI.RESOURCE_ID_NOT_FOUND,
                               GAPI.BAD_REQUEST, GAPI.RESOURCE_NOT_FOUND,
                               GAPI.FORBIDDEN, GAPI.PERMISSION_DENIED],
                 customerId=GC.Values[GC.CUSTOMER_ID], resourceId=resourceId, body=body)
        printEntityKVList([Ent.MOBILE_DEVICE, resourceId, Ent.USER, deviceUser],
                          [Msg.ACTION_APPLIED, body['action']], i, count)
      except GAPI.internalError:
        entityActionFailedWarning([Ent.MOBILE_DEVICE, resourceId], Msg.DOES_NOT_EXIST, i, count)
      except (GAPI.resourceIdNotFound, GAPI.badRequest, GAPI.resourceNotFound, GAPI.forbidden) as e:
        entityActionFailedWarning([Ent.MOBILE_DEVICE, resourceId], str(e), i, count)
      except GAPI.permissionDenied as e:
        ClientAPIAccessDeniedExit(str(e))

# gam delete mobile|mobiles <MobileDeviceEntity>
#	[doit] [matchusers <UserTypeEntity>]
def doDeleteMobileDevices():
  entityList, cd, doit = getMobileDeviceEntity()
  options = {'doit': doit, 'matchUsers': set()}
  while Cmd.ArgumentsRemaining():
    myarg = getArgument()
    _getUpdateDeleteMobileOptions(myarg, options)
  i = 0
  count = len(entityList)
  for device in entityList:
    i += 1
    resourceId = device['resourceId']
    deviceUser, status = _getMobileDeviceUser(device, options)
    if not status:
      entityActionNotPerformedWarning([Ent.MOBILE_DEVICE, resourceId, Ent.USER, deviceUser], Msg.USER_NOT_IN_MATCHUSERS, i, count)
    elif not options['doit']:
      entityActionNotPerformedWarning([Ent.MOBILE_DEVICE, resourceId, Ent.USER, deviceUser], Msg.USE_DOIT_ARGUMENT_TO_PERFORM_ACTION, i, count)
    else:
      try:
        callGAPI(cd.mobiledevices(), 'delete',
                 bailOnInternalError=True,
                 throwReasons=[GAPI.INTERNAL_ERROR, GAPI.RESOURCE_ID_NOT_FOUND, GAPI.BAD_REQUEST, GAPI.RESOURCE_NOT_FOUND,
                               GAPI.FORBIDDEN, GAPI.PERMISSION_DENIED],
                 customerId=GC.Values[GC.CUSTOMER_ID], resourceId=resourceId)
        entityActionPerformed([Ent.MOBILE_DEVICE, resourceId, Ent.USER, deviceUser], i, count)
      except GAPI.internalError:
        entityActionFailedWarning([Ent.MOBILE_DEVICE, resourceId], Msg.DOES_NOT_EXIST, i, count)
      except (GAPI.resourceIdNotFound, GAPI.badRequest, GAPI.resourceNotFound) as e:
        entityActionFailedWarning([Ent.MOBILE_DEVICE, resourceId], str(e), i, count)
      except (GAPI.forbidden, GAPI.permissionDenied) as e:
        ClientAPIAccessDeniedExit(str(e))

MOBILE_FIELDS_CHOICE_MAP = {
  'adbstatus': 'adbStatus',
  'applications': 'applications',
  'basebandversion': 'basebandVersion',
  'bootloaderversion': 'bootloaderVersion',
  'brand': 'brand',
  'buildnumber': 'buildNumber',
  'defaultlanguage': 'defaultLanguage',
  'developeroptionsstatus': 'developerOptionsStatus',
  'devicecompromisedstatus': 'deviceCompromisedStatus',
  'deviceid': 'deviceId',
  'devicepasswordstatus': 'devicePasswordStatus',
  'email': 'email',
  'encryptionstatus': 'encryptionStatus',
  'firstsync': 'firstSync',
  'hardware': 'hardware',
  'hardwareid': 'hardwareId',
  'imei': 'imei',
  'kernelversion': 'kernelVersion',
  'lastsync': 'lastSync',
  'managedaccountisonownerprofile': 'managedAccountIsOnOwnerProfile',
  'manufacturer': 'manufacturer',
  'meid': 'meid',
  'model': 'model',
  'name': 'name',
  'networkoperator': 'networkOperator',
  'os': 'os',
  'otheraccountsinfo': 'otherAccountsInfo',
  'privilege': 'privilege',
  'releaseversion': 'releaseVersion',
  'resourceid': 'resourceId',
  'securitypatchlevel': 'securityPatchLevel',
  'serialnumber': 'serialNumber',
  'status': 'status',
  'supportsworkprofile': 'supportsWorkProfile',
  'type': 'type',
  'unknownsourcesstatus': 'unknownSourcesStatus',
  'useragent': 'userAgent',
  'wifimacaddress': 'wifiMacAddress',
  }

MOBILE_TIME_OBJECTS = {'firstSync', 'lastSync'}

def _initMobileFieldsParameters():
  return {'fieldsList': [], 'projection': None}

def _getMobileFieldsArguments(myarg, parameters):
  if myarg == 'allfields':
    parameters['projection'] = 'FULL'
    parameters['fieldsList'] = []
  elif myarg in PROJECTION_CHOICE_MAP:
    parameters['projection'] = PROJECTION_CHOICE_MAP[myarg]
    parameters['fieldsList'] = []
  elif getFieldsList(myarg, MOBILE_FIELDS_CHOICE_MAP, parameters['fieldsList'], initialField='resourceId'):
    pass
  else:
    return False
  return True

# gam info mobile|mobiles <MobileDeviceEntity>
#	[basic|full|allfields] <MobileFieldName>* [fields <MobileFieldNameList>] [formatjson]
def doInfoMobileDevices():
  entityList, cd, _ = getMobileDeviceEntity()
  parameters = _initMobileFieldsParameters()
  FJQC = FormatJSONQuoteChar()
  while Cmd.ArgumentsRemaining():
    myarg = getArgument()
    if _getMobileFieldsArguments(myarg, parameters):
      pass
    else:
      FJQC.GetFormatJSON(myarg)
  fields = getFieldsFromFieldsList(parameters['fieldsList'])
  i = 0
  count = len(entityList)
  for device in entityList:
    i += 1
    resourceId = device['resourceId']
    try:
      mobile = callGAPI(cd.mobiledevices(), 'get',
                        bailOnInternalError=True,
                        throwReasons=[GAPI.INTERNAL_ERROR, GAPI.RESOURCE_ID_NOT_FOUND, GAPI.BAD_REQUEST, GAPI.RESOURCE_NOT_FOUND,
                                      GAPI.FORBIDDEN, GAPI.PERMISSION_DENIED],
                        customerId=GC.Values[GC.CUSTOMER_ID], resourceId=resourceId, projection=parameters['projection'], fields=fields)
      if FJQC.formatJSON:
        printLine(json.dumps(cleanJSON(mobile, timeObjects=MOBILE_TIME_OBJECTS), ensure_ascii=False, sort_keys=True))
      else:
        printEntity([Ent.MOBILE_DEVICE, resourceId], i, count)
        Ind.Increment()
        attrib = 'deviceId'
        if attrib in mobile:
          mobile[attrib] = mobile[attrib].encode('unicode-escape').decode(UTF8)
        attrib = 'securityPatchLevel'
        if attrib in mobile and int(mobile[attrib]):
          mobile[attrib] = formatLocalTimestamp(mobile[attrib])
        showJSON(None, mobile, timeObjects=MOBILE_TIME_OBJECTS)
        Ind.Decrement()
    except GAPI.internalError:
      entityActionFailedWarning([Ent.MOBILE_DEVICE, resourceId], Msg.DOES_NOT_EXIST, i, count)
    except (GAPI.resourceIdNotFound, GAPI.badRequest, GAPI.resourceNotFound) as e:
      entityActionFailedWarning([Ent.MOBILE_DEVICE, resourceId], str(e), i, count)
    except (GAPI.forbidden, GAPI.permissionDenied) as e:
      ClientAPIAccessDeniedExit(str(e))

MOBILE_ORDERBY_CHOICE_MAP = {
  'deviceid': 'deviceId',
  'email': 'email',
  'lastsync': 'lastSync',
  'model': 'model',
  'name': 'name',
  'os': 'os',
  'status': 'status',
  'type': 'type',
  }

# gam print mobile [todrive <ToDriveAttribute>*]
#	[(query <QueryMobile>)|(queries <QueryMobileList>) [querytime<String> <Time>]]
#	[orderby <MobileOrderByFieldName> [ascending|descending]]
#	[basic|full|allfields] <MobileFieldName>* [fields <MobileFieldNameList>]
#	[delimiter <Character>] [appslimit <Number>] [oneappperrow] [listlimit <Number>]
#	[formatjson [quotechar <Character>]]
# 	[showitemcountonly]
def doPrintMobileDevices():
  def _appDetails(app):
    appDetails = []
    for field in ['displayName', 'packageName', 'versionName']:
      appDetails.append(app.get(field, '<None>'))
    appDetails.append(str(app.get('versionCode', '<None>')))
    permissions = app.get('permission', [])
    if permissions:
      appDetails.append('/'.join(permissions))
    else:
      appDetails.append('<None>')
    return '-'.join(appDetails)

  def _printMobile(mobile):
    if FJQC.formatJSON:
      if (not csvPF.rowFilter and not csvPF.rowDropFilter) or csvPF.CheckRowTitles(flattenJSON(mobile, listLimit=listLimit, timeObjects=MOBILE_TIME_OBJECTS)):
        csvPF.WriteRowNoFilter({'resourceId': mobile['resourceId'],
                                'JSON': json.dumps(cleanJSON(mobile, listLimit=listLimit, timeObjects=MOBILE_TIME_OBJECTS),
                                                   ensure_ascii=False, sort_keys=True)})
      return
    row = {}
    for attrib in mobile:
      if attrib in DEFAULT_SKIP_OBJECTS:
        pass
      elif attrib in {'name', 'email', 'otherAccountsInfo'}:
        if listLimit > 0:
          row[attrib] = delimiter.join(mobile[attrib][0:listLimit])
        elif listLimit == 0:
          row[attrib] = delimiter.join(mobile[attrib])
      elif attrib == 'deviceId':
        row[attrib] = mobile[attrib].encode('unicode-escape').decode(UTF8)
      elif attrib in MOBILE_TIME_OBJECTS:
        row[attrib] = formatLocalTime(mobile[attrib])
      elif attrib == 'securityPatchLevel' and int(mobile[attrib]):
        row[attrib] = formatLocalTimestamp(mobile[attrib])
      elif attrib != 'applications':
        row[attrib] = mobile[attrib]
    attrib = 'applications'
    if not oneAppPerRow or attrib not in mobile or appsLimit < 0:
      if attrib in mobile and appsLimit >= 0:
        applications = []
        j = 0
        for app in mobile[attrib]:
          j += 1
          if appsLimit and (j > appsLimit):
            break
          applications.append(_appDetails(app))
        row[attrib] = delimiter.join(applications)
      csvPF.WriteRowTitles(row)
    else:
      j = 0
      for app in mobile[attrib]:
        j += 1
        if appsLimit and (j > appsLimit):
          break
        appRow = row.copy()
        appRow[attrib] = _appDetails(app)
        csvPF.WriteRowTitles(appRow)

  cd = buildGAPIObject(API.DIRECTORY)
  parameters = _initMobileFieldsParameters()
  csvPF = CSVPrintFile('resourceId')
  FJQC = FormatJSONQuoteChar(csvPF)
  orderBy = sortOrder = None
  oneAppPerRow = False
  queryTimes = {}
  queries = [None]
  delimiter = GC.Values[GC.CSV_OUTPUT_FIELD_DELIMITER]
  listLimit = 1
  appsLimit = -1
  showItemCountOnly = False
  while Cmd.ArgumentsRemaining():
    myarg = getArgument()
    if myarg == 'todrive':
      csvPF.GetTodriveParameters()
    elif myarg in {'query', 'queries'}:
      queries = getDeviceQueries(myarg, Ent.MOBILE_DEVICE)
    elif myarg.startswith('querytime'):
      queryTimes[myarg] = getTimeOrDeltaFromNow()[0:19]
    elif myarg == 'orderby':
      orderBy, sortOrder = getOrderBySortOrder(MOBILE_ORDERBY_CHOICE_MAP)
    elif myarg == 'delimiter':
      delimiter = getCharacter()
    elif myarg == 'listlimit':
      listLimit = getInteger(minVal=-1)
    elif myarg == 'appslimit':
      appsLimit = getInteger(minVal=-1)
    elif myarg == 'oneappperrow':
      oneAppPerRow = True
    elif _getMobileFieldsArguments(myarg, parameters):
      pass
    elif myarg == 'showitemcountonly':
      showItemCountOnly = True
    else:
      FJQC.GetFormatJSONQuoteChar(myarg, True)
  if not FJQC.formatJSON:
    csvPF.SetSortTitles(['resourceId', 'deviceId', 'serialNumber', 'name', 'email', 'status'])
  if appsLimit >= 0:
    parameters['projection'] = 'FULL'
  fields = getItemFieldsFromFieldsList('mobiledevices', parameters['fieldsList'])
  substituteQueryTimes(queries, queryTimes)
  itemCount = 0
  for query in queries:
    printGettingAllAccountEntities(Ent.MOBILE_DEVICE, query)
    pageMessage = getPageMessage()
    totalItems = 0
    try:
      feed = yieldGAPIpages(cd.mobiledevices(), 'list', 'mobiledevices',
                            pageMessage=pageMessage,
                            throwReasons=[GAPI.INVALID_INPUT, GAPI.BAD_REQUEST, GAPI.RESOURCE_NOT_FOUND,
                                          GAPI.FORBIDDEN, GAPI.PERMISSION_DENIED],
                            customerId=GC.Values[GC.CUSTOMER_ID], query=query, projection=parameters['projection'],
                            orderBy=orderBy, sortOrder=sortOrder, fields=fields, maxResults=GC.Values[GC.MOBILE_MAX_RESULTS])
      for mobiles in feed:
        totalItems += len(mobiles)
        if showItemCountOnly:
          itemCount += len(mobiles)
          continue
        for mobile in mobiles:
          _printMobile(mobile)
      printGotAccountEntities(totalItems)
    except GAPI.invalidInput:
      entityActionFailedWarning([Ent.MOBILE_DEVICE, None], invalidQuery(query))
      return
    except (GAPI.badRequest, GAPI.resourceNotFound):
      accessErrorExit(cd)
    except (GAPI.forbidden, GAPI.permissionDenied) as e:
      ClientAPIAccessDeniedExit(str(e))
  if showItemCountOnly:
    writeStdout(f'{itemCount}\n')
    return
  csvPF.writeCSVfile('Mobile')

from gam.constants import (  # noqa: F401 - re-exported for backward compatibility
    GROUP_DISCOVER_CHOICES, GROUP_ASSIST_CONTENT_CHOICES, GROUP_MODERATE_CONTENT_CHOICES,
    GROUP_MODERATE_MEMBERS_CHOICES, GROUP_DEPRECATED_ATTRIBUTES, GROUP_DISCOVER_ATTRIBUTES,
    GROUP_ASSIST_CONTENT_ATTRIBUTES, GROUP_MODERATE_CONTENT_ATTRIBUTES,
    GROUP_MODERATE_MEMBERS_ATTRIBUTES, GROUP_BASIC_ATTRIBUTES, GROUP_SETTINGS_ATTRIBUTES,
    GROUP_ALIAS_ATTRIBUTES, GROUP_MERGED_ATTRIBUTES, GROUP_MERGED_ATTRIBUTES_PRINT_ORDER,
    GROUP_MERGED_TO_COMPONENT_MAP, GROUP_ATTRIBUTES_SET, GROUP_FIELDS_WITH_CRS_NLS,
)


