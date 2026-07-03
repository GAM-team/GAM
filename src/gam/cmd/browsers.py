"""GAM Chrome browser and browser token management."""

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

def doDeleteBrowsers():
  cbcm = _getMain().buildGAPIObject(API.CBCM)
  customerId = _getMain()._getCustomerIdNoC()
  deviceId = _getMain().getString(Cmd.OB_DEVICE_ID)
  _getMain().checkForExtraneousArguments()
  try:
    _getMain().callGAPI(cbcm.chromebrowsers(), 'delete',
             throwReasons=[GAPI.BAD_REQUEST, GAPI.RESOURCE_NOT_FOUND, GAPI.FORBIDDEN],
             customer=customerId, deviceId=deviceId)
    _getMain().entityActionPerformed([Ent.CHROME_BROWSER, deviceId])
  except (GAPI.badRequest, GAPI.resourceNotFound, GAPI.forbidden):
    _getMain().checkEntityAFDNEorAccessErrorExit(None, Ent.CHROME_BROWSER, deviceId)

BROWSER_TIME_OBJECTS = {'firstRecordTime', 'lastActivityTime', 'lastPolicyFetchTime', 'lastRegistrationTime', 'lastStatusReportTime', 'safeBrowsingWarningsResetTime'}

def _showBrowser(browser, FJQC, i=0, count=0):
  if FJQC.formatJSON:
    _getMain().printLine(json.dumps(_getMain().cleanJSON(browser), ensure_ascii=False, sort_keys=True))
    return
  _getMain().printEntity([Ent.CHROME_BROWSER, browser['deviceId']], i, count)
  Ind.Increment()
  _getMain().showJSON(None, browser, timeObjects=BROWSER_TIME_OBJECTS, dictObjectsKey={'machinePolicies': 'name'})
  Ind.Decrement()

BROWSER_FIELDS_CHOICE_MAP = {
  'annotatedassetid': 'annotatedAssetId',
  'annotatedlocation': 'annotatedLocation',
  'annotatednotes': 'annotatedNotes',
  'annotateduser': 'annotatedUser',
  'asset': 'annotatedAssetId',
  'assetid': 'annotatedAssetId',
  'browsers': 'browsers',
  'browserversions': 'browserVersions',
  'deviceid': 'deviceId',
  'deviceidentifiershistory': 'deviceIdentifiersHistory',
  'extensioncount': 'extensionCount',
  'lastactivitytime': 'lastActivityTime',
  'lastdeviceuser': 'lastDeviceUser',
  'lastdeviceusers': 'lastDeviceUsers',
  'lastpolicyfetchtime': 'lastPolicyFetchTime',
  'lastregistrationtime': 'lastRegistrationTime',
  'laststatusreporttime': 'lastStatusReportTime',
  'location': 'annotatedLocation',
  'machineextensionpolicies': 'machineExtensionPolicies',
  'machinename': 'machineName',
  'machinepolicies': 'machinePolicies',
  'notes': 'annotatedNotes',
  'org': 'orgUnitPath',
  'orgunit': 'orgUnitPath',
  'orgunitpath': 'orgUnitPath',
  'osarchitecture':  'osArchitecture',
  'osplatform': 'osPlatform',
  'osplatformversion': 'osPlatformVersion',
  'osversion': 'osVersion',
  'ou': 'orgUnitPath',
  'policycount': 'policyCount',
  'safebrowsingclickthroughcount': 'safeBrowsingClickThroughCount',
  'serialnumber': 'serialNumber',
  'user': 'annotatedUser',
  'virtualdeviceid': 'virtualDeviceId',
  }
BROWSER_ANNOTATED_FIELDS_LIST = ['annotatedAssetId', 'annotatedLocation', 'annotatedNotes', 'annotatedUser', 'deviceId']
BROWSER_FULL_ACCESS_FIELDS = {'browsers', 'lastDeviceUsers', 'lastStatusReportTime', 'machinePolicies'}

# gam info browser <DeviceID>
#	(basic|full|annotated |
#	 (<BrowserFieldName>* [fields <BrowserFieldNameList>]) |
#	 (rawfields <BrowserFieldNameList>))
#	[formatjson]
def doInfoBrowsers():
  cbcm = _getMain().buildGAPIObject(API.CBCM)
  customerId = _getMain()._getCustomerIdNoC()
  deviceId = _getMain().getString(Cmd.OB_DEVICE_ID)
  projection = 'BASIC'
  fieldsList = []
  rawFields = None
  FJQC = _getMain().FormatJSONQuoteChar()
  while Cmd.ArgumentsRemaining():
    myarg = _getMain().getArgument()
    if myarg == 'annotated':
      projection = 'BASIC'
      fieldsList = BROWSER_ANNOTATED_FIELDS_LIST
    elif myarg in _getMain().PROJECTION_CHOICE_MAP:
      projection = _getMain().PROJECTION_CHOICE_MAP[myarg]
      fieldsList = []
    elif _getMain().getFieldsList(myarg, BROWSER_FIELDS_CHOICE_MAP, fieldsList, initialField='deviceId'):
      pass
    elif myarg == 'rawfields':
      projection = 'FULL'
      rawFields = _getMain()._getRawFields('deviceId')
    else:
      FJQC.GetFormatJSON(myarg)
  if projection == 'BASIC' and set(fieldsList).intersection(BROWSER_FULL_ACCESS_FIELDS):
    projection = 'FULL'
  fields = _getMain().getFieldsFromFieldsList(fieldsList) if not rawFields else rawFields
  try:
    browser = _getMain().callGAPI(cbcm.chromebrowsers(), 'get',
                       throwReasons=[GAPI.BAD_REQUEST, GAPI.RESOURCE_NOT_FOUND, GAPI.INVALID_ARGUMENT, GAPI.FORBIDDEN],
                       customer=customerId, deviceId=deviceId, projection=projection, fields=fields)
    _showBrowser(browser, FJQC)
  except GAPI.invalidArgument as e:
    _getMain().entityActionFailedWarning([Ent.CHROME_BROWSER, deviceId], str(e))
  except (GAPI.badRequest, GAPI.resourceNotFound, GAPI.forbidden):
    _getMain().checkEntityAFDNEorAccessErrorExit(None, Ent.CHROME_BROWSER, deviceId)

# gam move browsers ou|org|orgunit <OrgUnitPath>
#	((ids <DeviceIDList>) |
#	 (queries <QueryBrowserList> [querytime<String> <Time>]) |
#	 (browserou <OrgUnitItem>) | (browserous <OrgUnitList>) |
#	 <FileSelector> | <CSVFileSelector>)
#	[batchsize <Integer>]
def doMoveBrowsers():
  cbcm = _getMain().buildGAPIObject(API.CBCM)
  customerId = _getMain()._getCustomerIdNoC()
  deviceIds = []
  batch_size = GC.Values[GC.BATCH_SIZE]
  orgUnitPath = ''
  queries = []
  queryTimes = {}
  while Cmd.ArgumentsRemaining():
    myarg = _getMain().getArgument()
    if myarg in {'ou', 'org', 'orgunit'}:
      orgUnitPath = _getMain().getOrgUnitItem()
    elif myarg == 'ids':
      deviceIds.extend(_getMain().convertEntityToList(_getMain().getString(Cmd.OB_DEVICE_ID_LIST, minLen=0)))
    elif myarg == 'file':
      deviceIds.extend(_getMain().getEntitiesFromFile(False))
    elif myarg in {'csv', 'csvfile'}:
      deviceIds.extend(_getMain().getEntitiesFromCSVFile(False))
    elif myarg in {'query', 'queries'}:
      queries = _getMain().getDeviceQueries(myarg, Ent.CHROME_BROWSER)
    elif myarg.startswith('querytime'):
      queryTimes[myarg] = _getMain().getTimeOrDeltaFromNow()[0:19]
    elif myarg == 'browserou':
      deviceIds.extend(_getMain().getItemsToModify(Cmd.ENTITY_BROWSER_OU, _getMain().getOrgUnitItem(pathOnly=True, absolutePath=True)))
    elif myarg == 'browserous':
      deviceIds.extend(_getMain().getItemsToModify(Cmd.ENTITY_BROWSER_OUS, _getMain().getEntityList(Cmd.OB_ORGUNIT_ENTITY, shlexSplit=True)))
    elif myarg == 'batchsize':
      batch_size = _getMain().getInteger(minVal=1, maxVal=600)
    else:
      _getMain().unknownArgumentExit()
  if not orgUnitPath:
    _getMain().missingArgumentExit('orgunit')
  _getMain().substituteQueryTimes(queries, queryTimes)
  if queries:
    deviceIds.extend(_getMain().getItemsToModify(Cmd.ENTITY_BROWSER_QUERIES, queries))
  body = {'org_unit_path': orgUnitPath}
  bcount = 0
  jcount = len(deviceIds)
  j = 0
  while bcount < jcount:
    kcount = min(jcount-bcount, batch_size)
    try:
      body['resource_ids'] = deviceIds[bcount:bcount+kcount]
      _getMain().callGAPI(cbcm.chromebrowsers(), 'moveChromeBrowsersToOu',
               mapNotFound=False,
               throwReasons=[GAPI.INVALID_ORGUNIT, GAPI.BAD_REQUEST, GAPI.RESOURCE_NOT_FOUND, GAPI.FORBIDDEN],
               customer=customerId, body=body)
      for deviceId in deviceIds:
        j += 1
        _getMain().entityActionPerformed([Ent.ORGANIZATIONAL_UNIT, orgUnitPath, Ent.CHROME_BROWSER, deviceId], j, jcount)
      bcount += kcount
    except GAPI.invalidOrgunit:
      _getMain().entityActionFailedWarning([Ent.ORGANIZATIONAL_UNIT, orgUnitPath], Msg.INVALID_ORGUNIT)
      break
    except (GAPI.badRequest, GAPI.resourceNotFound, GAPI.forbidden) as e:
      _getMain().entityActionFailedWarning([Ent.ORGANIZATIONAL_UNIT, orgUnitPath, Ent.CHROME_BROWSER, f'IDs: {deviceIds[bcount]} - {deviceIds[bcount+kcount-1]}'], str(e))
      bcount += kcount

UPDATE_BROWSER_ARGUMENT_TO_PROPERTY_MAP = {
  'annotatedassetid': 'annotatedAssetId',
  'annotatedlocation': 'annotatedLocation',
  'annotatednotes': 'annotatedNotes',
  'annotateduser': 'annotatedUser',
  'asset': 'annotatedAssetId',
  'assetid': 'annotatedAssetId',
  'location': 'annotatedLocation',
  'notes': 'annotatedNotes',
  'updatenotes': 'annotatedNotes',
  'user': 'annotatedUser',
  }

BROWSER_DEVICEID_ANNOTATED_FIELDS = 'deviceId,annotatedAssetId,annotatedLocation,annotatedNotes,annotatedUser'

# gam update browser <BrowserEntity> <BrowserAttibute>+ [updatenotes <String>]
def doUpdateBrowsers():
  cbcm = _getMain().buildGAPIObject(API.CBCM)
  customerId = _getMain()._getCustomerIdNoC()
  _, entityList = _getMain().getEntityToModify(defaultEntityType=Cmd.ENTITY_BROWSER, browserAllowed=True, crosAllowed=False, userAllowed=False)
  body = {}
  updateNotes = None
  while Cmd.ArgumentsRemaining():
    myarg = _getMain().getArgument()
    if myarg in UPDATE_BROWSER_ARGUMENT_TO_PROPERTY_MAP:
      up = UPDATE_BROWSER_ARGUMENT_TO_PROPERTY_MAP[myarg]
      if up == 'annotatedNotes':
        body[up] = _getMain().getStringWithCRsNLs()
        updateNotes = body[up] if myarg == 'updatenotes' and body[up].find('#notes#') != -1 else None
      else:
        body[up] = _getMain().getString(Cmd.OB_STRING)
    else:
      _getMain().unknownArgumentExit()
  i = 0
  count = len(entityList)
  for deviceId in entityList:
    i += 1
    try:
      browser = _getMain().callGAPI(cbcm.chromebrowsers(), 'get',
                         throwReasons=[GAPI.BAD_REQUEST, GAPI.RESOURCE_NOT_FOUND, GAPI.FORBIDDEN],
                         customer=customerId, deviceId=deviceId,
                         projection='BASIC', fields=BROWSER_DEVICEID_ANNOTATED_FIELDS)
      if updateNotes:
        body['annotatedNotes'] = updateNotes.replace('#notes#', browser['annotatedNotes'])
      browser.update(body)
      _getMain().callGAPI(cbcm.chromebrowsers(), 'update',
               throwReasons=[GAPI.BAD_REQUEST, GAPI.RESOURCE_NOT_FOUND, GAPI.FORBIDDEN],
               customer=customerId, deviceId=deviceId,
               body=browser, projection='BASIC', fields="deviceId")
      _getMain().entityActionPerformed([Ent.CHROME_BROWSER, deviceId], i, count)
    except (GAPI.badRequest, GAPI.resourceNotFound, GAPI.forbidden):
      _getMain().checkEntityAFDNEorAccessErrorExit(None, Ent.CHROME_BROWSER, deviceId, i, count)

def _getChromeProfileName():
  profileName = _getMain().getString(Cmd.OB_CHROMEPROFILE_NAME)
  if not profileName.startswith('customers'):
    customerId = _getMain()._getCustomerId()
    profileName = f'customers/{customerId}/profiles/{profileName}'
  return profileName

# gam delete chromeprofile <ChromeProfileName>
def doDeleteChromeProfile():
  cm = _getMain().buildGAPIObject(API.CHROMEMANAGEMENT)
  profileName = _getChromeProfileName()
  _getMain().checkForExtraneousArguments()
  try:
    _getMain().callGAPI(cm.customers().profiles(), 'delete',
             throwReasons=[GAPI.INVALID_ARGUMENT, GAPI.NOT_FOUND, GAPI.PERMISSION_DENIED],
             name=profileName)
    _getMain().entityActionPerformed([Ent.CHROME_PROFILE, profileName])
  except (GAPI.invalidArgument, GAPI.notFound, GAPI.permissionDenied) as e:
    _getMain().entityActionFailedExit([Ent.CHROME_PROFILE, profileName], str(e))

CHROMEPROFILE_TIME_OBJECTS = {
  'firstEnrollmentTime',
  'lastActivityTime',
  'lastPolicyFetchTime',
  'lastPolicySyncTime',
  'lastStatusReportTime',
  }

def _showChromeProfile(profile, FJQC, i=0, count=0):
  if FJQC.formatJSON:
    _getMain().printLine(json.dumps(_getMain().cleanJSON(profile, timeObjects=CHROMEPROFILE_TIME_OBJECTS),
              ensure_ascii=False, sort_keys=True))
    return
  _getMain().printEntity([Ent.CHROME_PROFILE, profile['name']], i, count)
  Ind.Increment()
  _getMain().showJSON(None, profile, timeObjects=CHROMEPROFILE_TIME_OBJECTS)
  Ind.Decrement()

CHROMEPROFILE_FIELDS_CHOICE_MAP = {
  'affiliationstate': 'affiliationState',
  'annotatedlocation': 'annotatedLocation',
  'annotateduser': 'annotatedUser',
  'attestationcredential': 'attestationCredential',
  'browserchannel': 'browserChannel',
  'browserversion': 'browserVersion',
  'deviceinfo': 'deviceInfo',
  'displayname': 'displayName',
  'extensioncount': 'extensionCount',
  'firstenrollmenttime': 'firstEnrollmentTime',
  'identityprovider':'identityProvider',
  'lastactivitytime': 'lastActivityTime',
  'lastpolicyfetchtime': 'lastPolicyFetchTime',
  'lastpolicysynctime': 'lastPolicySyncTime',
  'laststatusreporttime': 'lastStatusReportTime',
  'name': 'name',
  'osplatformtype': 'osPlatformType',
  'osplatformversion':'osPlatformVersion',
  'osversion': 'osVersion',
  'policycount': 'policyCount',
  'profileid': 'profileId',
  'profilepermanentid': 'profilePermanentId',
  'reportingdata': 'reportingData',
  'useremail': 'userEmail',
  'userid': 'userId',
   }

# gam info chromeprofile <ChromeProfileName>
#	<ChromeProfileFieldName>* [fields <ChromeProfileFieldNameList>]
#	[formatjson]
def doInfoChromeProfile():
  cm = _getMain().buildGAPIObject(API.CHROMEMANAGEMENT)
  profileName = _getChromeProfileName()
  fieldsList = []
  FJQC = _getMain().FormatJSONQuoteChar()
  while Cmd.ArgumentsRemaining():
    myarg = _getMain().getArgument()
    if _getMain().getFieldsList(myarg, CHROMEPROFILE_FIELDS_CHOICE_MAP, fieldsList, initialField='name'):
      pass
    else:
      FJQC.GetFormatJSON(myarg)
  fields = _getMain().getFieldsFromFieldsList(fieldsList)
  try:
    profile = _getMain().callGAPI(cm.customers().profiles(), 'get',
                       throwReasons=[GAPI.INVALID_ARGUMENT, GAPI.NOT_FOUND, GAPI.PERMISSION_DENIED],
                       name=profileName, fields=fields)
    _showChromeProfile(profile, FJQC)
  except (GAPI.invalidArgument, GAPI.notFound, GAPI.permissionDenied) as e:
    _getMain().entityActionFailedExit([Ent.CHROME_PROFILE, profileName], str(e))

CHROMEPROFILE_ORDERBY_CHOICE_MAP = {
  'affiliationstate': 'affiliationState',
  'browserchannel': 'browserChannel',
  'browserversion': 'browserVersion',
  'displayname': 'displayName',
  'extensioncount': 'extensionCount',
  'firstenrollmenttime': 'firstEnrollmentTime',
  'identityprovider': 'identityProvider',
  'lastactivitytime': 'lastActivityTime',
  'lastpolicysynctime': 'lastPolicySyncTime',
  'laststatusreporttime': 'lastStatusReportTime',
  'osplatformtype': 'osPlatformType',
  'osversion': 'osVersion',
  'policycount': 'policyCount',
  'profileid': 'profileId',
  'useremail': 'userEmail',
  }

# gam show chromeprofiles
#	[filter <String> (filtertime<String> <Time>)*]
#	[orderby <ChromeProfileOrderByFieldName> [ascending|descending]]
#	<ChromeProfileFieldName>* [fields <ChromeProfileFieldNameList>]
#	[formatjson]
# gam print chromeprofiles [todrive <ToDriveAttribute>*]
#	[filter <String> (filtertime<String> <Time>)*]
#	[orderby <ChromeProfileOrderByFieldName> [ascending|descending]]
#	<ChromeProfileFieldName>* [fields <ChromeProfileFieldNameList>]
#	[formatjson [quotechar <Character>]]
def doPrintShowChromeProfiles():
  def _printProfile(profile):
    row = _getMain().flattenJSON(profile, timeObjects=CHROMEPROFILE_TIME_OBJECTS)
    if not FJQC.formatJSON:
      csvPF.WriteRowTitles(row)
    elif csvPF.CheckRowTitles(row):
      csvPF.WriteRowNoFilter({'name': profile['name'], 'profileId': profile['profileId'],
                              'JSON': json.dumps(_getMain().cleanJSON(profile, timeObjects=CHROMEPROFILE_TIME_OBJECTS),
                                                 ensure_ascii=False, sort_keys=True)})

  cm = _getMain().buildGAPIObject(API.CHROMEMANAGEMENT)
  csvPF = _getMain().CSVPrintFile(['name', 'profileId']) if Act.csvFormat() else None
  FJQC = _getMain().FormatJSONQuoteChar(csvPF)
  OBY = _getMain().OrderBy(CHROMEPROFILE_ORDERBY_CHOICE_MAP)
  sortHeaders = False
  fieldsList = []
  cbfilter = None
  filterTimes = {}
  while Cmd.ArgumentsRemaining():
    myarg = _getMain().getArgument()
    if csvPF and myarg == 'todrive':
      csvPF.GetTodriveParameters()
    elif _getMain().getFieldsList(myarg, CHROMEPROFILE_FIELDS_CHOICE_MAP, fieldsList, initialField=['name', 'profileId']):
      pass
    elif myarg == 'orderby':
      OBY.GetChoice()
    elif myarg.startswith('filtertime'):
      filterTimes[myarg] = _getMain().getTimeOrDeltaFromNow()
    elif myarg in {'filter', 'filters'}:
      cbfilter = _getMain().getString(Cmd.OB_STRING)
    elif myarg == 'sortheaders':
      sortHeaders = True
    else:
      FJQC.GetFormatJSONQuoteChar(myarg, True)
  if filterTimes and cbfilter is not None:
    for filterTimeName, filterTimeValue in filterTimes.items():
      cbfilter = cbfilter.replace(f'#{filterTimeName}#', filterTimeValue)
  fields = _getMain().getItemFieldsFromFieldsList('chromeBrowserProfiles', fieldsList)
  customerId = _getMain()._getCustomerId()
  parent = f'customers/{customerId}'
  _getMain().printGettingAllAccountEntities(Ent.CHROME_PROFILE, cbfilter)
  pageMessage = _getMain().getPageMessage()
  try:
    feed = _getMain().yieldGAPIpages(cm.customers().profiles(), 'list', 'chromeBrowserProfiles',
                          pageMessage=pageMessage,
                          throwReasons=[GAPI.INVALID_ARGUMENT, GAPI.PERMISSION_DENIED],
                          parent=parent, pageSize=200,
                          filter=cbfilter, orderBy=OBY.orderBy, fields=fields)
    for profiles in feed:
      if not csvPF:
        jcount = len(profiles)
        if not FJQC.formatJSON:
          _getMain().performActionNumItems(jcount, Ent.CHROME_PROFILE)
        Ind.Increment()
        j = 0
        for profile in profiles:
          j += 1
          _showChromeProfile(profile, FJQC, j, jcount)
        Ind.Decrement()
      else:
        for profile in profiles:
          _printProfile(profile)
  except (GAPI.invalidArgument, GAPI.permissionDenied) as e:
    _getMain().entityActionFailedExit([Ent.CHROME_PROFILE, cbfilter], str(e))
  if csvPF:
    if sortHeaders:
      csvPF.SetSortTitles(['name', 'profileId'])
    csvPF.writeCSVfile('Chrome Profiles')

def _getChromeProfileNameList():
  if not Cmd.PeekArgumentPresent(['select', 'commands', 'filter', 'filters']):
    return _getMain().getString(Cmd.OB_CHROMEPROFILE_NAME_LIST).replace(',', ' ').split()
  return []

def _initChromeProfileNameParameters():
  cm = _getMain().buildGAPIObject(API.CHROMEMANAGEMENT)
  return (cm, {'profileNameList': _getChromeProfileNameList(),
               'commandNameList': [],
               'customerId': _getMain()._getCustomerId(),
               'cbfilter': None, 'filterTimes': {},
               'OBY': _getMain().OrderBy(CHROMEPROFILE_ORDERBY_CHOICE_MAP)})

def _getChromeProfileNameParameters(myarg, parameters):
  if not parameters['cbfilter'] and not parameters['commandNameList'] and myarg == 'select':
    parameters['profileNameList'].extend(_getMain().getEntityList(Cmd.OB_CHROMEPROFILE_NAME_LIST))
  elif not parameters['cbfilter'] and not parameters['profileNameList'] and myarg == 'commands':
    parameters['commandNameList'].extend(_getMain().getEntityList(Cmd.OB_CHROMEPROFILE_COMMAND_NAME_LIST))
  elif not parameters['profileNameList'] and not parameters['commandNameList'] and myarg == 'orderby':
    parameters['OBY'].GetChoice()
  elif not parameters['profileNameList'] and not parameters['commandNameList'] and myarg.startswith('filtertime'):
    parameters['filterTimes'][myarg] = _getMain().getTimeOrDeltaFromNow()
  elif not parameters['profileNameList'] and not parameters['commandNameList'] and myarg in {'filter', 'filters'}:
    parameters['cbfilter'] = _getMain().getString(Cmd.OB_STRING)
  else:
    return False
  return True

def _getChromeProfileNameEntityForCommand(cm, parameters):
  if parameters['cbfilter'] is None:
    customerId = parameters['customerId']
    if parameters['profileNameList']:
      for i, profileName in enumerate(parameters['profileNameList']):
        if not profileName.startswith('customers'):
          parameters['profileNameList'][i] = f'customers/{customerId}/profiles/{profileName}'
    elif parameters['commandNameList']:
      for i, commandName in enumerate(parameters['commandNameList']):
        if not commandName.startswith('customers'):
          parameters['commandNameList'][i] = f'customers/{customerId}/profiles/{commandName}'
    return
  if parameters['filterTimes']:
    for filterTimeName, filterTimeValue in parameters['filterTimes'].items():
      parameters['cbfilter'] = parameters['cbfilter'].replace(f'#{filterTimeName}#', filterTimeValue)
  _getMain().printGettingAllAccountEntities(Ent.CHROME_PROFILE, parameters['cbfilter'])
  pageMessage = _getMain().getPageMessage()
  try:
    feed = _getMain().yieldGAPIpages(cm.customers().profiles(), 'list', 'chromeBrowserProfiles',
                          pageMessage=pageMessage,
                          throwReasons=[GAPI.INVALID_ARGUMENT, GAPI.PERMISSION_DENIED],
                          parent=f'customers/{parameters["customerId"]}', pageSize=200,
                          filter=parameters['cbfilter'], orderBy=parameters['OBY'].orderBy,
                          fields='nextPageToken,chromeBrowserProfiles(name)')
    for profiles in feed:
      for profile in profiles:
        parameters['profileNameList'].append(profile['name'])
  except (GAPI.invalidArgument, GAPI.permissionDenied) as e:
    _getMain().entityActionFailedExit([Ent.CHROME_PROFILE, parameters['cbfilter']], str(e))

CHROMEPROFILECOMMAND_TIME_OBJECTS = {
  'clientExecutionTime',
  'issueTime',
  }

def _showChromeProfileCommand(profcmd, FJQC, i=0, count=0):
  if FJQC.formatJSON:
    _getMain().printLine(json.dumps(_getMain().cleanJSON(profcmd, timeObjects=CHROMEPROFILECOMMAND_TIME_OBJECTS),
              ensure_ascii=False, sort_keys=True))
    return
  _getMain().printEntity([Ent.CHROME_PROFILE_COMMAND, profcmd['name']], i, count)
  Ind.Increment()
  _getMain().showJSON(None, profcmd, timeObjects=CHROMEPROFILECOMMAND_TIME_OBJECTS)
  Ind.Decrement()

def _printChromeProfileCommand(profcmd, csvPF, FJQC):
  row = _getMain().flattenJSON(profcmd, timeObjects=CHROMEPROFILECOMMAND_TIME_OBJECTS)
  if not FJQC.formatJSON:
    csvPF.WriteRowTitles(row)
  elif csvPF.CheckRowTitles(row):
    csvPF.WriteRowNoFilter({'name': profcmd['name'],
                            'JSON': json.dumps(_getMain().cleanJSON(profcmd, timeObjects=CHROMEPROFILECOMMAND_TIME_OBJECTS),
                                               ensure_ascii=False, sort_keys=True)})

# gam create chromeprofilecommand <ChromeProfileNameEntity>
#	[clearcache [<Boolean>]] [clearcookies [<Boolean>]]
#	[csv [todrive <ToDriveAttribute>*] [formatjson [quotechar <Character>]]]
def doCreateChromeProfileCommand():
  cm, parameters = _initChromeProfileNameParameters()
  body = {'commandType': 'clearBrowsingData', 'payload': {}}
  csvPF = None
  FJQC = _getMain().FormatJSONQuoteChar(None)
  while Cmd.ArgumentsRemaining():
    myarg = _getMain().getArgument()
    if _getChromeProfileNameParameters(myarg, parameters):
      pass
    elif myarg == 'clearcache':
      body['payload']['clearCache'] = _getMain().getBoolean()
    elif myarg == 'clearcookies':
      body['payload']['clearCookies'] = _getMain().getBoolean()
    elif myarg == 'csv':
      csvPF = _getMain().CSVPrintFile(['name'], 'sortall')
      FJQC.SetCsvPF(csvPF)
    elif csvPF and myarg == 'todrive':
      csvPF.GetTodriveParameters()
    else:
      FJQC.GetFormatJSONQuoteChar(myarg, True)
  _getChromeProfileNameEntityForCommand(cm, parameters)
  count = len(parameters['profileNameList'])
  i = 0
  for profileName in parameters['profileNameList']:
    i +=1
    try:
      profcmd = _getMain().callGAPI(cm.customers().profiles().commands(), 'create',
                         throwReasons=[GAPI.INVALID_ARGUMENT, GAPI.NOT_FOUND, GAPI.PERMISSION_DENIED],
                         parent=profileName, body=body)
      if csvPF is None:
        _showChromeProfileCommand(profcmd, FJQC, i, count)
      else:
        _printChromeProfileCommand(profcmd, csvPF, FJQC)
    except (GAPI.notFound) as e:
      _getMain().entityActionFailedWarning([Ent.CHROME_PROFILE_COMMAND, profileName], str(e), i, count)
    except (GAPI.invalidArgument, GAPI.permissionDenied) as e:
      _getMain().entityActionFailedExit([Ent.CHROME_PROFILE_COMMAND, profileName], str(e))
  if csvPF:
    csvPF.writeCSVfile('Chrome Profile Commands')

# gam info chromeprofilecommand <ChromeProfileCommandName>
#	[formatjson]
def doInfoChromeProfileCommand():
  cm = _getMain().buildGAPIObject(API.CHROMEMANAGEMENT)
  profileCommandName = _getChromeProfileName()
  FJQC = _getMain().FormatJSONQuoteChar()
  while Cmd.ArgumentsRemaining():
    myarg = _getMain().getArgument()
    FJQC.GetFormatJSON(myarg)
  try:
    profcmd = _getMain().callGAPI(cm.customers().profiles().commands(), 'get',
                       throwReasons=[GAPI.INVALID_ARGUMENT, GAPI.NOT_FOUND, GAPI.PERMISSION_DENIED],
                       name=profileCommandName)
    _showChromeProfileCommand(profcmd, FJQC)
  except (GAPI.invalidArgument, GAPI.notFound, GAPI.permissionDenied) as e:
    _getMain().entityActionFailedExit([Ent.CHROME_PROFILE, profileCommandName], str(e))

# gam show chromeprofilecommands <ChromeProfileNameEntity>
#	[formatjson]
# gam print chromeprofilecommands <ChromeProfilNameEntity> [todrive <ToDriveAttribute>*]
#	[formatjson [quotechar <Character>]]
def doPrintShowChromeProfileCommands():
  csvPF = _getMain().CSVPrintFile(['name']) if Act.csvFormat() else None
  FJQC = _getMain().FormatJSONQuoteChar(csvPF)
  cm, parameters = _initChromeProfileNameParameters()
  while Cmd.ArgumentsRemaining():
    myarg = _getMain().getArgument()
    if csvPF and myarg == 'todrive':
      csvPF.GetTodriveParameters()
    elif _getChromeProfileNameParameters(myarg, parameters):
      pass
    else:
      FJQC.GetFormatJSONQuoteChar(myarg, True)
  _getChromeProfileNameEntityForCommand(cm, parameters)
  if parameters['profileNameList']:
    count = len(parameters['profileNameList'])
    i = 0
    for profileName in parameters['profileNameList']:
      i +=1
      _getMain().printGettingEntityItemForWhom(Ent.CHROME_PROFILE_COMMAND, profileName, i, count)
      pageMessage = _getMain().getPageMessage()
      try:
        profcmds = _getMain().callGAPIpages(cm.customers().profiles().commands(), 'list', 'chromeBrowserProfileCommands',
                                 pageMessage=pageMessage,
                                 throwReasons=[GAPI.NOT_FOUND, GAPI.INVALID_ARGUMENT, GAPI.PERMISSION_DENIED],
                                 parent=profileName, pageSize=100)
        if not csvPF:
          jcount = len(profcmds)
          Ind.Increment()
          j = 0
          for profcmd in profcmds:
            j += 1
            _showChromeProfileCommand(profcmd, FJQC, j, jcount)
          Ind.Decrement()
        else:
          for profcmd in profcmds:
            _printChromeProfileCommand(profcmd, csvPF, FJQC)
      except GAPI.notFound as e:
        _getMain().entityActionFailedWarning([Ent.CHROME_PROFILE, profileName], str(e), i, count)
      except (GAPI.invalidArgument, GAPI.permissionDenied) as e:
        _getMain().entityActionFailedExit([Ent.CHROME_PROFILE, profileName], str(e))
  elif parameters['commandNameList']:
    count = len(parameters['commandNameList'])
    i = 0
    for profileCommandName in parameters['commandNameList']:
      i +=1
      try:
        profcmd = _getMain().callGAPI(cm.customers().profiles().commands(), 'get',
                           throwReasons=[GAPI.INVALID_ARGUMENT, GAPI.NOT_FOUND, GAPI.PERMISSION_DENIED],
                           name=profileCommandName)
        if not csvPF:
          _showChromeProfileCommand(profcmd, FJQC, i, count)
        else:
          _printChromeProfileCommand(profcmd, csvPF, FJQC)
      except GAPI.notFound as e:
        _getMain().entityActionFailedWarning([Ent.CHROME_PROFILE_COMMAND, profileCommandName], str(e), i, count)
      except (GAPI.invalidArgument, GAPI.permissionDenied) as e:
        _getMain().entityActionFailedExit([Ent.CHROME_PROFILE, profileCommandName], str(e))
  if csvPF:
    csvPF.writeCSVfile('Chrome Profile Commands')

BROWSER_ORDERBY_CHOICE_MAP = {
  'annotatedassetid': 'annotated_asset_id', 'asset': 'annotated_asset_id', 'assetid': 'annotated_asset_id',
  'annotatedlocation': 'annotated_location', 'location': 'annotated_location',
  'annotatednotes': 'notes', 'notes': 'notes',
  'annotateduser': 'annotated_user', 'user': 'annotated_user',
  'browserversionchannel': 'browser_version_channel',
  'browserversionsortable': 'browser_version_sortable',
  'deviceid': 'id', 'id': 'id',
  'enrollmentdate': 'enrollment_date',
  'extensioncount': 'extension_count',
  'lastactivity': 'last_activity',
  'lastsignedinuser': 'last_signed_in_user',
  'lastsync': 'last_sync',
  'machinename': 'machine_name',
  'orgunit': 'org_unit', 'ou': 'org_unit', 'org': 'org_unit',
  'osversion': 'os_version',
  'osversionsortable': 'os_version_sortable',
  'platformmajorversion': 'platform_major_version',
  'policycount': 'policy_count',
  #  'safebrowsingclickthrough': 'safe_browsing_clickthrough',
  }

# gam show browsers
#	([ou|org|orgunit|browserou <OrgUnitPath>] [(query <QueryBrowser)|(queries <QueryBrowserList>))|(select <BrowserEntity>))
#	[querytime<String> <Time>]
#	[orderby <BrowserOrderByFieldName> [ascending|descending]]
#	(basic|full|annotated |
#	 (<BrowserFieldName>* [fields <BrowserFieldNameList>]) |
#	 (rawfields <BrowserFieldNameList>))
#	(<BrowserFieldName>* [fields <BrowserFieldNameList>]|(rawfields <BrowserFieldNameList>)
#	[formatjson]
# gam print browsers [todrive <ToDriveAttribute>*]
#	([ou|org|orgunit|browserou <OrgUnitPath>] [(query <QueryBrowser)|(queries <QueryBrowserList>))|(select <BrowserEntity>))
#	[querytime<String> <Time>]
#	[orderby <BrowserOrderByFieldName> [ascending|descending]]
#	(basic|full|annotated |
#	 (<BrowserFieldName>* [fields <BrowserFieldNameList>]) |
#	 (rawfields <BrowserFieldNameList>))
#	(<BrowserFieldName>* [fields <BrowserFieldNameList>]|(rawfields <BrowserFieldNameList>)
#	[sortheaders] [formatjson [quotechar <Character>]]
def doPrintShowBrowsers():
  def _printBrowser(browser):
    row = _getMain().flattenJSON(browser, timeObjects=BROWSER_TIME_OBJECTS)
    if not FJQC.formatJSON:
      csvPF.WriteRowTitles(row)
    elif csvPF.CheckRowTitles(row):
      csvPF.WriteRowNoFilter({'deviceId': browser['deviceId'],
                              'JSON': json.dumps(_getMain().cleanJSON(browser, timeObjects=BROWSER_TIME_OBJECTS),
                                                 ensure_ascii=False, sort_keys=True)})

  cbcm = _getMain().buildGAPIObject(API.CBCM)
  customerId = _getMain()._getCustomerIdNoC()
  csvPF = _getMain().CSVPrintFile(['deviceId']) if Act.csvFormat() else None
  FJQC = _getMain().FormatJSONQuoteChar(csvPF)
  fieldsList = []
  rawFields = None
  projection = 'BASIC'
  orderBy = 'id'
  sortOrder = 'ASCENDING'
  entityList = orgUnitPath = None
  queries = [None]
  queryTimes = {}
  sortHeaders = sortRows = False
  while Cmd.ArgumentsRemaining():
    myarg = _getMain().getArgument()
    if csvPF and myarg == 'todrive':
      csvPF.GetTodriveParameters()
    elif myarg in {'query', 'queries'}:
      queries = _getMain().getDeviceQueries(myarg, Ent.CHROME_BROWSER)
    elif myarg.startswith('querytime'):
      queryTimes[myarg] = _getMain().getTimeOrDeltaFromNow()[0:19]
    elif myarg in {'ou', 'org', 'orgunit', 'browserou'}:
      orgUnitPath = _getMain().getOrgUnitItem(pathOnly=True, absolutePath=True)
    elif myarg == 'select':
      _, entityList = _getMain().getEntityToModify(defaultEntityType=Cmd.ENTITY_BROWSER, browserAllowed=True, crosAllowed=False, userAllowed=False)
    elif myarg == 'orderby':
      orderBy, sortOrder = _getMain().getOrderBySortOrder(BROWSER_ORDERBY_CHOICE_MAP, 'DESCENDING', True)
    elif myarg == 'annotated':
      projection = 'BASIC'
      fieldsList = BROWSER_ANNOTATED_FIELDS_LIST
    elif (myarg == 'projection') or myarg in _getMain().PROJECTION_CHOICE_MAP:
      if myarg == 'projection':
        projection = _getMain().getChoice(_getMain().PROJECTION_CHOICE_MAP, mapChoice=True)
      else:
        projection = _getMain().PROJECTION_CHOICE_MAP[myarg]
      fieldsList = []
    elif myarg == 'allfields':
      projection = 'FULL'
      sortHeaders = True
      fieldsList = []
    elif myarg == 'sortheaders':
      sortHeaders = True
    elif _getMain().getFieldsList(myarg, BROWSER_FIELDS_CHOICE_MAP, fieldsList, initialField='deviceId'):
      pass
    elif myarg == 'rawfields':
      projection = 'FULL'
      rawFields = _getMain()._getRawFields('deviceId')
    else:
      FJQC.GetFormatJSONQuoteChar(myarg, True)
  if projection == 'BASIC' and set(fieldsList).intersection(BROWSER_FULL_ACCESS_FIELDS):
    projection = 'FULL'
  if FJQC.formatJSON:
    sortHeaders = False
  _getMain().substituteQueryTimes(queries, queryTimes)
  if entityList is None:
    fields = _getMain().getItemFieldsFromFieldsList('browsers', fieldsList) if not rawFields else f'nextPageToken,browsers({rawFields})'
    for query in queries:
      _getMain().printGettingAllAccountEntities(Ent.CHROME_BROWSER, query)
      pageMessage = _getMain().getPageMessage()
      try:
        feed = _getMain().yieldGAPIpages(cbcm.chromebrowsers(), 'list', 'browsers',
                              pageMessage=pageMessage, messageAttribute='deviceId',
                              throwReasons=[GAPI.INVALID_INPUT, GAPI.BAD_REQUEST, GAPI.INVALID_ARGUMENT, GAPI.INVALID_ORGUNIT, GAPI.FORBIDDEN],
                              retryReasons=GAPI.SERVICE_NOT_AVAILABLE_RETRY_REASONS,
                              customer=customerId, orgUnitPath=orgUnitPath, query=query, projection=projection,
                              orderBy=orderBy, sortOrder=sortOrder, fields=fields)
        for browsers in feed:
          if not csvPF:
            jcount = len(browsers)
            if not FJQC.formatJSON:
              _getMain().performActionNumItems(jcount, Ent.CHROME_BROWSER)
            Ind.Increment()
            j = 0
            for browser in browsers:
              j += 1
              _showBrowser(browser, FJQC, j, jcount)
            Ind.Decrement()
          else:
            for browser in browsers:
              _printBrowser(browser)
      except GAPI.invalidInput as e:
        if query:
          _getMain().entityActionFailedWarning([Ent.CHROME_BROWSER, None], _getMain().invalidQuery(query))
        else:
          _getMain().entityActionFailedWarning([Ent.CHROME_BROWSER, None], str(e))
        return
      except (GAPI.invalidArgument, GAPI.invalidOrgunit, GAPI.forbidden) as e:
        _getMain().entityActionFailedWarning([Ent.CHROME_BROWSER, None], str(e))
        return
      except (GAPI.badRequest, GAPI.resourceNotFound):
        accessErrorExit(None)
  else:
    sortRows = True
    jcount = len(entityList)
    fields = _getMain().getFieldsFromFieldsList(fieldsList) if not rawFields else rawFields
    j = 0
    for deviceId in entityList:
      j += 1
      try:
        browser = _getMain().callGAPI(cbcm.chromebrowsers(), 'get',
                           throwReasons=[GAPI.BAD_REQUEST, GAPI.RESOURCE_NOT_FOUND, GAPI.INVALID_ARGUMENT, GAPI.FORBIDDEN],
                           customer=customerId, deviceId=deviceId, projection=projection, fields=fields)
        _printBrowser(browser)
      except GAPI.invalidArgument as e:
        _getMain().entityActionFailedWarning([Ent.CHROME_BROWSER, deviceId], str(e))
      except (GAPI.badRequest, GAPI.resourceNotFound, GAPI.forbidden):
        _getMain().checkEntityAFDNEorAccessErrorExit(None, Ent.CHROME_BROWSER, deviceId)
  if csvPF:
    if sortRows and orderBy:
      csvPF.SortRows(orderBy, reverse=sortOrder == 'DESCENDING')
    if sortHeaders:
      csvPF.SetSortTitles(['deviceId'])
    csvPF.writeCSVfile('Browsers')

BROWSER_TOKEN_TIME_OBJECTS = {'createTime', 'expireTime', 'revokeTime'}

def _showBrowserToken(browser, FJQC, i=0, count=0):
  if FJQC.formatJSON:
    _getMain().printLine(json.dumps(_getMain().cleanJSON(browser), ensure_ascii=False, sort_keys=True))
    return
  _getMain().printEntity([Ent.CHROME_BROWSER_ENROLLMENT_TOKEN, browser['token']], i, count)
  Ind.Increment()
  _getMain().showJSON(None, browser, timeObjects=BROWSER_TOKEN_TIME_OBJECTS)
  Ind.Decrement()

# gam create browsertoken
#	[ou|org|orgunit|browserou <OrgUnitPath>] [expire|expires <Time>]
#	[formatjson]
def doCreateBrowserToken():
  cbcm = _getMain().buildGAPIObject(API.CBCM)
  customerId = _getMain()._getCustomerIdNoC()
  FJQC = _getMain().FormatJSONQuoteChar()
  body = {'token_type': 'CHROME_BROWSER'}
  while Cmd.ArgumentsRemaining():
    myarg = _getMain().getArgument()
    if myarg in {'ou', 'org', 'orgunit', 'browserou'}:
      body['org_unit_path'] = _getMain().getOrgUnitItem(pathOnly=True, absolutePath=True)
    elif myarg in ['expire', 'expires']:
      body['expire_time'] = _getMain().getTimeOrDeltaFromNow()
    else:
      FJQC.GetFormatJSON(myarg)
  try:
    browser = _getMain().callGAPI(cbcm.enrollmentTokens(), 'create',
                       throwReasons=[GAPI.INVALID_INPUT, GAPI.BAD_REQUEST, GAPI.INVALID_ORGUNIT, GAPI.FORBIDDEN],
                       customer=customerId, body=body)
    if not FJQC.formatJSON:
      _getMain().entityActionPerformed([Ent.CHROME_BROWSER_ENROLLMENT_TOKEN, browser['token']])
    Ind.Increment()
    _showBrowserToken(browser, FJQC, 0, 0)
    Ind.Decrement()
  except (GAPI.invalidInput, GAPI.invalidOrgunit) as e:
    _getMain().entityActionFailedWarning([Ent.CHROME_BROWSER_ENROLLMENT_TOKEN, None], str(e))
  except (GAPI.badRequest, GAPI.resourceNotFound, GAPI.forbidden):
    accessErrorExit(None)

# gam revoke browsertoken <BrowserTokenPermanentID>
def doRevokeBrowserToken():
  cbcm = _getMain().buildGAPIObject(API.CBCM)
  customerId = _getMain()._getCustomerIdNoC()
  tokenPermanentId = _getMain().getString(Cmd.OB_BROWSER_ENROLLEMNT_TOKEN_ID)
  _getMain().checkForExtraneousArguments()
  try:
    _getMain().callGAPI(cbcm.enrollmentTokens(), 'revoke',
             throwReasons=[GAPI.INVALID, GAPI.INVALID_INPUT, GAPI.BAD_REQUEST, GAPI.INVALID_ORGUNIT, GAPI.FORBIDDEN],
             customer=customerId, tokenPermanentId=tokenPermanentId)
    _getMain().entityActionPerformed([Ent.CHROME_BROWSER_ENROLLMENT_TOKEN, tokenPermanentId])
  except (GAPI.invalid, GAPI.invalidInput, GAPI.badRequest, GAPI.resourceNotFound, GAPI.invalidOrgunit) as e:
    _getMain().entityActionFailedWarning([Ent.CHROME_BROWSER_ENROLLMENT_TOKEN, tokenPermanentId], str(e))
  except GAPI.forbidden:
    accessErrorExit(None)

BROWSER_TOKEN_FIELDS_CHOICE_MAP = {
  'createtime': 'createTime',
  'creatorid': 'creatorId',
  'customerid': 'customerId',
  'expiretime': 'expireTime',
  'org': 'orgUnitPath',
  'orgunit': 'orgUnitPath',
  'orgunitpath': 'orgUnitPath',
  'ou': 'orgUnitPath',
  'revoketime': 'revokeTime',
  'revokerid': 'revokerId',
  'state': 'state',
  'token': 'token',
  'tokenpermanentid': 'tokenPermanentId',
  }

# gam show browsertokens
#	([ou|org|orgunit|browserou <OrgUnitPath>] [(query <QueryBrowserToken)|(queries <QueryBrowserTokenList>)))
#	[querytime<String> <Time>]
#	[orderby <BrowserTokenFieldName> [ascending|descending]]
#	[allfields] <BrowserTokenFieldName>* [fields <BrowserTokenFieldNameList>]
#	[formatjson]
# gam print browsertokens [todrive <ToDriveAttribute>*]
#	([ou|org|orgunit|browserou <OrgUnitPath>] [(query <QueryBrowserToken)|(queries <QueryBrowserTokenList>)))
#	[querytime<String> <Time>]
#	[orderby <BrowserTokenFieldName> [ascending|descending]]
#	[allfields] <BrowserTokenFieldName>* [fields <BrowserTokenFieldNameList>]
#	[sortheaders] [formatjson [quotechar <Character>]]
def doPrintShowBrowserTokens():
  def _printBrowserToken(browser):
    row = _getMain().flattenJSON(browser, timeObjects=BROWSER_TOKEN_TIME_OBJECTS)
    if not FJQC.formatJSON:
      csvPF.WriteRowTitles(row)
    elif csvPF.CheckRowTitles(row):
      csvPF.WriteRowNoFilter({'token': browser['token'],
                              'JSON': json.dumps(_getMain().cleanJSON(browser, timeObjects=BROWSER_TOKEN_TIME_OBJECTS),
                                                 ensure_ascii=False, sort_keys=True)})

  cbcm = _getMain().buildGAPIObject(API.CBCM)
  customerId = _getMain()._getCustomerIdNoC()
  csvPF = _getMain().CSVPrintFile(['token']) if Act.csvFormat() else None
  FJQC = _getMain().FormatJSONQuoteChar(csvPF)
  fieldsList = []
  orderBy = 'token'
  sortOrder = 'ASCENDING'
  orgUnitPath = None
  queries = [None]
  queryTimes = {}
  sortHeaders = False
  while Cmd.ArgumentsRemaining():
    myarg = _getMain().getArgument()
    if csvPF and myarg == 'todrive':
      csvPF.GetTodriveParameters()
    elif myarg in {'query', 'queries'}:
      queries = _getMain().getDeviceQueries(myarg, Ent.CHROME_BROWSER)
    elif myarg.startswith('querytime'):
      queryTimes[myarg] = _getMain().getTimeOrDeltaFromNow()[0:19]
    elif myarg in {'ou', 'org', 'orgunit', 'browserou'}:
      orgUnitPath = _getMain().getOrgUnitItem(pathOnly=True, absolutePath=True)
    elif myarg == 'orderby':
      orderBy, sortOrder = _getMain().getOrderBySortOrder(BROWSER_TOKEN_FIELDS_CHOICE_MAP, 'DESCENDING', True)
    elif myarg == 'allfields':
      sortHeaders = True
      fieldsList = []
    elif myarg == 'sortheaders':
      sortHeaders = True
    elif _getMain().getFieldsList(myarg, BROWSER_TOKEN_FIELDS_CHOICE_MAP, fieldsList, initialField='token'):
      pass
    else:
      FJQC.GetFormatJSONQuoteChar(myarg, True)
  fields = _getMain().getItemFieldsFromFieldsList('chromeEnrollmentTokens', fieldsList)
  if FJQC.formatJSON:
    sortHeaders = False
  _getMain().substituteQueryTimes(queries, queryTimes)
  for query in queries:
    _getMain().printGettingAllAccountEntities(Ent.CHROME_BROWSER_ENROLLMENT_TOKEN, query)
    pageMessage = _getMain().getPageMessage()
    try:
      browsers = _getMain().callGAPIpages(cbcm.enrollmentTokens(), 'list', 'chromeEnrollmentTokens',
                               pageMessage=pageMessage,
                               throwReasons=[GAPI.INVALID_INPUT, GAPI.BAD_REQUEST, GAPI.INVALID_ORGUNIT, GAPI.FORBIDDEN],
                               customer=customerId, orgUnitPath=orgUnitPath, query=query,
                               fields=fields)
      if not csvPF:
        jcount = len(browsers)
        _getMain().performActionNumItems(jcount, Ent.CHROME_BROWSER_ENROLLMENT_TOKEN)
        Ind.Increment()
        j = 0
        for browser in browsers:
          j += 1
          _showBrowserToken(browser, FJQC, j, jcount)
        Ind.Decrement()
      else:
        for browser in browsers:
          _printBrowserToken(browser)
    except GAPI.invalidInput as e:
      if query:
        _getMain().entityActionFailedWarning([Ent.CHROME_BROWSER_ENROLLMENT_TOKEN, None], _getMain().invalidQuery(query))
      else:
        _getMain().entityActionFailedWarning([Ent.CHROME_BROWSER_ENROLLMENT_TOKEN, None], str(e))
    except GAPI.invalidOrgunit as e:
      _getMain().entityActionFailedWarning([Ent.CHROME_BROWSER_ENROLLMENT_TOKEN, None], str(e))
    except (GAPI.badRequest, GAPI.resourceNotFound, GAPI.forbidden):
      accessErrorExit(None)
  if csvPF:
    if orderBy:
      csvPF.SortRows(orderBy, reverse=sortOrder == 'DESCENDING')
    if sortHeaders:
      csvPF.SetSortTitles(['token'])
    csvPF.writeCSVfile('Chrome Browser Enrollment Tokens')

