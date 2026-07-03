"""GAM mobile device management."""

import json

from gamlib import glaction
from gamlib import glapi as API
from gamlib import glcfg as GC
from gamlib import glclargs
from gamlib import glentity
from gamlib import glgapi as GAPI
from gamlib import glglobals as GM
from gamlib import glindent
from gamlib import glmsgs as Msg
from gam.util.api import buildGAPIObject, callGAPI, callGAPIpages, yieldGAPIpages
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

Act = glaction.GamAction()
Ent = glentity.GamEntity()
Ind = glindent.GamIndent()
Cmd = glclargs.GamCLArgs()


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

GROUP_DISCOVER_CHOICES = {
  'allmemberscandiscover': 'ALL_MEMBERS_CAN_DISCOVER',
  'allindomaincandiscover': 'ALL_IN_DOMAIN_CAN_DISCOVER',
  'anyonecandiscover': 'ANYONE_CAN_DISCOVER',
  }
GROUP_ASSIST_CONTENT_CHOICES = {
  'allmembers': 'ALL_MEMBERS',
  'ownersandmanagers': 'OWNERS_AND_MANAGERS',
  'managersonly': 'MANAGERS_ONLY',
  'ownersonly': 'OWNERS_ONLY',
  'none': 'NONE',
  }
GROUP_MODERATE_CONTENT_CHOICES = {
  'allmembers': 'ALL_MEMBERS',
  'ownersandmanagers': 'OWNERS_AND_MANAGERS',
  'ownersonly': 'OWNERS_ONLY',
  'none': 'NONE',
  }
GROUP_MODERATE_MEMBERS_CHOICES = {
  'allmembers': 'ALL_MEMBERS',
  'ownersandmanagers': 'OWNERS_AND_MANAGERS',
  'ownersonly': 'OWNERS_ONLY',
  'none': 'NONE',
  }
GROUP_DEPRECATED_ATTRIBUTES = {
  'allowgooglecommunication': ['allowGoogleCommunication', {GC.VAR_TYPE: GC.TYPE_BOOLEAN}],
  'favoriterepliesontop': ['favoriteRepliesOnTop', {GC.VAR_TYPE: GC.TYPE_BOOLEAN}],
  'maxmessagebytes': ['maxMessageBytes', {GC.VAR_TYPE: GC.TYPE_INTEGER, GC.VAR_LIMITS: (1024, 1048576)}],
  'messagedisplayfont': ['messageDisplayFont', {GC.VAR_TYPE: GC.TYPE_CHOICE,
                                                'choices': {'defaultfont': 'DEFAULT_FONT', 'fixedwidthfont': 'FIXED_WIDTH_FONT'}}],
  'whocanaddreferences': ['whoCanAddReferences', {GC.VAR_TYPE: GC.TYPE_CHOICE, 'choices': GROUP_ASSIST_CONTENT_CHOICES}],
  'whocanmarkfavoritereplyonowntopic': ['whoCanMarkFavoriteReplyOnOwnTopic', {GC.VAR_TYPE: GC.TYPE_CHOICE, 'choices': GROUP_ASSIST_CONTENT_CHOICES}],
  }
GROUP_DISCOVER_ATTRIBUTES = {
  'showingroupdirectory': ['showInGroupDirectory', {GC.VAR_TYPE: GC.TYPE_BOOLEAN}],
  }
GROUP_ASSIST_CONTENT_ATTRIBUTES = {
  'whocanassigntopics': ['whoCanAssignTopics', {GC.VAR_TYPE: GC.TYPE_CHOICE, 'choices': GROUP_ASSIST_CONTENT_CHOICES}],
  'whocanenterfreeformtags': ['whoCanEnterFreeFormTags', {GC.VAR_TYPE: GC.TYPE_CHOICE, 'choices': GROUP_ASSIST_CONTENT_CHOICES}],
  'whocanhideabuse': ['whoCanHideAbuse', {GC.VAR_TYPE: GC.TYPE_CHOICE, 'choices': GROUP_ASSIST_CONTENT_CHOICES}],
  'whocanmaketopicssticky': ['whoCanMakeTopicsSticky', {GC.VAR_TYPE: GC.TYPE_CHOICE, 'choices': GROUP_ASSIST_CONTENT_CHOICES}],
  'whocanmarkduplicate': ['whoCanMarkDuplicate', {GC.VAR_TYPE: GC.TYPE_CHOICE, 'choices': GROUP_ASSIST_CONTENT_CHOICES}],
  'whocanmarkfavoritereplyonanytopic': ['whoCanMarkFavoriteReplyOnAnyTopic', {GC.VAR_TYPE: GC.TYPE_CHOICE, 'choices': GROUP_ASSIST_CONTENT_CHOICES}],
  'whocanmarknoresponseneeded': ['whoCanMarkNoResponseNeeded', {GC.VAR_TYPE: GC.TYPE_CHOICE, 'choices': GROUP_ASSIST_CONTENT_CHOICES}],
  'whocanmodifytagsandcategories': ['whoCanModifyTagsAndCategories', {GC.VAR_TYPE: GC.TYPE_CHOICE, 'choices': GROUP_ASSIST_CONTENT_CHOICES}],
  'whocantaketopics': ['whoCanTakeTopics', {GC.VAR_TYPE: GC.TYPE_CHOICE, 'choices': GROUP_ASSIST_CONTENT_CHOICES}],
  'whocanunassigntopic': ['whoCanUnassignTopic', {GC.VAR_TYPE: GC.TYPE_CHOICE, 'choices': GROUP_ASSIST_CONTENT_CHOICES}],
  'whocanunmarkfavoritereplyonanytopic': ['whoCanUnmarkFavoriteReplyOnAnyTopic', {GC.VAR_TYPE: GC.TYPE_CHOICE, 'choices': GROUP_ASSIST_CONTENT_CHOICES}],
  }
GROUP_MODERATE_CONTENT_ATTRIBUTES = {
  'whocanapprovemessages': ['whoCanApproveMessages', {GC.VAR_TYPE: GC.TYPE_CHOICE, 'choices': GROUP_MODERATE_CONTENT_CHOICES}],
  'whocandeleteanypost': ['whoCanDeleteAnyPost', {GC.VAR_TYPE: GC.TYPE_CHOICE, 'choices': GROUP_MODERATE_CONTENT_CHOICES}],
  'whocandeletetopics': ['whoCanDeleteTopics', {GC.VAR_TYPE: GC.TYPE_CHOICE, 'choices': GROUP_MODERATE_CONTENT_CHOICES}],
  'whocanlocktopics': ['whoCanLockTopics', {GC.VAR_TYPE: GC.TYPE_CHOICE, 'choices': GROUP_MODERATE_CONTENT_CHOICES}],
  'whocanmovetopicsin': ['whoCanMoveTopicsIn', {GC.VAR_TYPE: GC.TYPE_CHOICE, 'choices': GROUP_MODERATE_CONTENT_CHOICES}],
  'whocanmovetopicsout': ['whoCanMoveTopicsOut', {GC.VAR_TYPE: GC.TYPE_CHOICE, 'choices': GROUP_MODERATE_CONTENT_CHOICES}],
  'whocanpostannouncements': ['whoCanPostAnnouncements', {GC.VAR_TYPE: GC.TYPE_CHOICE, 'choices': GROUP_MODERATE_CONTENT_CHOICES}],
  }
GROUP_MODERATE_MEMBERS_ATTRIBUTES = {
  'whocanadd': ['whoCanAdd', {GC.VAR_TYPE: GC.TYPE_CHOICE,
                              'choices': {'allmanagerscanadd': 'ALL_MANAGERS_CAN_ADD', 'allownerscanadd': 'ALL_OWNERS_CAN_ADD',
                                          'allmemberscanadd': 'ALL_MEMBERS_CAN_ADD', 'nonecanadd': 'NONE_CAN_ADD'}}],
  'whocanapprovemembers': ['whoCanApproveMembers', {GC.VAR_TYPE: GC.TYPE_CHOICE,
                                                    'choices': {'allownerscanapprove': 'ALL_OWNERS_CAN_APPROVE', 'allmanagerscanapprove': 'ALL_MANAGERS_CAN_APPROVE',
                                                                'allmemberscanapprove': 'ALL_MEMBERS_CAN_APPROVE', 'nonecanapprove': 'NONE_CAN_APPROVE'}}],
  'whocanbanusers': ['whoCanBanUsers', {GC.VAR_TYPE: GC.TYPE_CHOICE, 'choices': GROUP_MODERATE_MEMBERS_CHOICES}],
  'whocaninvite': ['whoCanInvite', {GC.VAR_TYPE: GC.TYPE_CHOICE,
                                    'choices': {'allmemberscaninvite': 'ALL_MEMBERS_CAN_INVITE', 'allmanagerscaninvite': 'ALL_MANAGERS_CAN_INVITE',
                                                'allownerscaninvite': 'ALL_OWNERS_CAN_INVITE', 'nonecaninvite': 'NONE_CAN_INVITE'}}],
  'whocanmodifymembers': ['whoCanModifyMembers', {GC.VAR_TYPE: GC.TYPE_CHOICE, 'choices': GROUP_MODERATE_MEMBERS_CHOICES}],
  }
GROUP_BASIC_ATTRIBUTES = {
  'description': ['description', {GC.VAR_TYPE: GC.TYPE_STRING}],
  'name': ['name', {GC.VAR_TYPE: GC.TYPE_STRING}],
  'displayname': ['name', {GC.VAR_TYPE: GC.TYPE_STRING}],
  }
GROUP_SETTINGS_ATTRIBUTES = {
  'allowexternalmembers': ['allowExternalMembers', {GC.VAR_TYPE: GC.TYPE_BOOLEAN}],
  'allowwebposting': ['allowWebPosting', {GC.VAR_TYPE: GC.TYPE_BOOLEAN}],
  'archiveonly': ['archiveOnly', {GC.VAR_TYPE: GC.TYPE_BOOLEAN}],
  'customfootertext': ['customFooterText', {GC.VAR_TYPE: GC.TYPE_STRING}],
  'customreplyto': ['customReplyTo', {GC.VAR_TYPE: GC.TYPE_EMAIL_OPTIONAL}],
  'customrolesenabledforsettingstobemerged': ['customRolesEnabledForSettingsToBeMerged', {GC.VAR_TYPE: GC.TYPE_BOOLEAN}],
  'defaultmessagedenynotificationtext': ['defaultMessageDenyNotificationText', {GC.VAR_TYPE: GC.TYPE_STRING}],
  'defaultsender': ['defaultSender', {GC.VAR_TYPE: GC.TYPE_CHOICE,
                                      'choices': {'self': 'DEFAULT_SELF', 'defaultself': 'DEFAULT_SELF', 'group': 'GROUP'}}],
  'enablecollaborativeinbox': ['enableCollaborativeInbox', {GC.VAR_TYPE: GC.TYPE_BOOLEAN}],
  'includecustomfooter': ['includeCustomFooter', {GC.VAR_TYPE: GC.TYPE_BOOLEAN}],
  'includeinglobaladdresslist': ['includeInGlobalAddressList', {GC.VAR_TYPE: GC.TYPE_BOOLEAN}],
  'isarchived': ['isArchived', {GC.VAR_TYPE: GC.TYPE_BOOLEAN}],
  'memberscanpostasthegroup': ['membersCanPostAsTheGroup', {GC.VAR_TYPE: GC.TYPE_BOOLEAN}],
  'messagemoderationlevel': ['messageModerationLevel', {GC.VAR_TYPE: GC.TYPE_CHOICE,
                                                        'choices': {'moderateallmessages': 'MODERATE_ALL_MESSAGES', 'moderatenonmembers': 'MODERATE_NON_MEMBERS',
                                                                    'moderatenewmembers': 'MODERATE_NEW_MEMBERS', 'moderatenone': 'MODERATE_NONE'}}],
  'primarylanguage': ['primaryLanguage', {GC.VAR_TYPE: GC.TYPE_LANGUAGE}],
  'replyto': ['replyTo', {GC.VAR_TYPE: GC.TYPE_CHOICE,
                          'choices': {'replytocustom': 'REPLY_TO_CUSTOM', 'replytosender': 'REPLY_TO_SENDER', 'replytolist': 'REPLY_TO_LIST',
                                      'replytoowner': 'REPLY_TO_OWNER', 'replytoignore': 'REPLY_TO_IGNORE', 'replytomanagers': 'REPLY_TO_MANAGERS'}}],
  'sendmessagedenynotification': ['sendMessageDenyNotification', {GC.VAR_TYPE: GC.TYPE_BOOLEAN}],
  'spammoderationlevel': ['spamModerationLevel', {GC.VAR_TYPE: GC.TYPE_CHOICE,
                                                  'choices': {'allow': 'ALLOW', 'moderate': 'MODERATE', 'silentlymoderate': 'SILENTLY_MODERATE', 'reject': 'REJECT'}}],
  'whocanaddexternalmembers': ['whoCanAddExternalMembers', {GC.VAR_TYPE: GC.TYPE_CHOICE,
                                                            'choices': {'onlyadminscanaddexternalmembers': 'ONLY_ADMINS_CAN_ADD_EXTERNAL_MEMBERS',
                                                                        'enduserscanaddexternalmembers': 'END_USERS_CAN_ADD_EXTERNAL_MEMBERS'}}],
  'whocancontactowner': ['whoCanContactOwner', {GC.VAR_TYPE: GC.TYPE_CHOICE,
                                                'choices': {'anyonecancontact': 'ANYONE_CAN_CONTACT', 'allindomaincancontact': 'ALL_IN_DOMAIN_CAN_CONTACT',
                                                            'allmemberscancontact': 'ALL_MEMBERS_CAN_CONTACT', 'allmanagerscancontact': 'ALL_MANAGERS_CAN_CONTACT',
                                                            'allownerscancontact': 'ALL_OWNERS_CAN_CONTACT'}}],
  'whocanjoin': ['whoCanJoin', {GC.VAR_TYPE: GC.TYPE_CHOICE,
                                'choices': {'anyonecanjoin': 'ANYONE_CAN_JOIN', 'allindomaincanjoin': 'ALL_IN_DOMAIN_CAN_JOIN',
                                            'invitedcanjoin': 'INVITED_CAN_JOIN', 'canrequesttojoin': 'CAN_REQUEST_TO_JOIN'}}],
  'whocanleavegroup': ['whoCanLeaveGroup', {GC.VAR_TYPE: GC.TYPE_CHOICE,
                                            'choices': {'allmanagerscanleave': 'ALL_MANAGERS_CAN_LEAVE', 'allownerscanleave': 'ALL_OWNERS_CAN_LEAVE',
                                                        'allmemberscanleave': 'ALL_MEMBERS_CAN_LEAVE', 'nonecanleave': 'NONE_CAN_LEAVE'}}],
  'whocanpostmessage': ['whoCanPostMessage', {GC.VAR_TYPE: GC.TYPE_CHOICE,
                                              'choices': {'nonecanpost': 'NONE_CAN_POST', 'allmanagerscanpost': 'ALL_MANAGERS_CAN_POST',
                                                          'allmemberscanpost': 'ALL_MEMBERS_CAN_POST', 'allownerscanpost': 'ALL_OWNERS_CAN_POST',
                                                          'allindomaincanpost': 'ALL_IN_DOMAIN_CAN_POST', 'anyonecanpost': 'ANYONE_CAN_POST'}}],
  'whocanviewgroup': ['whoCanViewGroup', {GC.VAR_TYPE: GC.TYPE_CHOICE,
                                          'choices': {'anyonecanview': 'ANYONE_CAN_VIEW', 'allindomaincanview': 'ALL_IN_DOMAIN_CAN_VIEW',
                                                      'allmemberscanview': 'ALL_MEMBERS_CAN_VIEW', 'allmanagerscanview': 'ALL_MANAGERS_CAN_VIEW',
                                                      'allownerscanview': 'ALL_OWNERS_CAN_VIEW'}}],
  'whocanviewmembership': ['whoCanViewMembership', {GC.VAR_TYPE: GC.TYPE_CHOICE,
                                                    'choices': {'allindomaincanview': 'ALL_IN_DOMAIN_CAN_VIEW', 'allmemberscanview': 'ALL_MEMBERS_CAN_VIEW',
                                                                'allmanagerscanview': 'ALL_MANAGERS_CAN_VIEW', 'allownerscanview': 'ALL_OWNERS_CAN_VIEW'}}],
  }
GROUP_ALIAS_ATTRIBUTES = {
  'collaborative': ['enableCollaborativeInbox', {GC.VAR_TYPE: GC.TYPE_BOOLEAN}],
  'gal': ['includeInGlobalAddressList', {GC.VAR_TYPE: GC.TYPE_BOOLEAN}],
  }
GROUP_MERGED_ATTRIBUTES = {
  'whocandiscovergroup': ['whoCanDiscoverGroup', {GC.VAR_TYPE: GC.TYPE_CHOICE, 'choices': GROUP_DISCOVER_CHOICES}],
  'whocanassistcontent': ['whoCanAssistContent', {GC.VAR_TYPE: GC.TYPE_CHOICE, 'choices': GROUP_ASSIST_CONTENT_CHOICES}],
  'whocanmoderatecontent': ['whoCanModerateContent', {GC.VAR_TYPE: GC.TYPE_CHOICE, 'choices': GROUP_MODERATE_CONTENT_CHOICES}],
  'whocanmoderatemembers': ['whoCanModerateMembers', {GC.VAR_TYPE: GC.TYPE_CHOICE, 'choices': GROUP_MODERATE_MEMBERS_CHOICES}],
  }
GROUP_MERGED_ATTRIBUTES_PRINT_ORDER = ['whoCanDiscoverGroup', 'whoCanAssistContent', 'whoCanModerateContent', 'whoCanModerateMembers']
GROUP_MERGED_TO_COMPONENT_MAP = {
  'whoCanDiscoverGroup': GROUP_DISCOVER_ATTRIBUTES,
  'whoCanAssistContent': GROUP_ASSIST_CONTENT_ATTRIBUTES,
  'whoCanModerateContent': GROUP_MODERATE_CONTENT_ATTRIBUTES,
  'whoCanModerateMembers': GROUP_MODERATE_MEMBERS_ATTRIBUTES,
  }
GROUP_ATTRIBUTES_SET = set(list(GROUP_BASIC_ATTRIBUTES)+list(GROUP_SETTINGS_ATTRIBUTES)+list(GROUP_ALIAS_ATTRIBUTES)+
                           list(GROUP_ASSIST_CONTENT_ATTRIBUTES)+list(GROUP_MODERATE_CONTENT_ATTRIBUTES)+list(GROUP_MODERATE_MEMBERS_ATTRIBUTES)+
                           list(GROUP_MERGED_ATTRIBUTES)+list(GROUP_DEPRECATED_ATTRIBUTES))
GROUP_FIELDS_WITH_CRS_NLS = {'customFooterText', 'defaultMessageDenyNotificationText', 'description'}

