"""GAM Chrome browser and browser token management."""

import json

from gamlib import api as API
from gamlib import settings as GC
from gamlib import gapi as GAPI
from gamlib import msgs as Msg
from gam.var import Act, Cmd, Ent, Ind
from gam.util.access import checkEntityAFDNEorAccessErrorExit
from gam.util.api import buildGAPIObject
from gam.util.api_call import callGAPI, callGAPIpages, yieldGAPIpages
from gam.util.args import (
    OrderBy,
    checkForExtraneousArguments,
    getArgument,
    getBoolean,
    getChoice,
    getInteger,
    getOrderBySortOrder,
    getString,
    getStringWithCRsNLs,
    getTimeOrDeltaFromNow,
    substituteQueryTimes,
)
from gam.util.csv_pf import (
    CSVPrintFile,
    FormatJSONQuoteChar,
    _getRawFields,
    cleanJSON,
    flattenJSON,
    getFieldsFromFieldsList,
    getFieldsList,
    getItemFieldsFromFieldsList,
    showJSON,
)
from gam.util.display import (
    entityActionFailedWarning,
    entityActionPerformed,
    getPageMessage,
    invalidQuery,
    performActionNumItems,
    printEntity,
    printGettingAllAccountEntities,
    printGettingEntityItemForWhom,
    printLine,
)
from gam.util.entity import (
    _getCustomerId,
    _getCustomerIdNoC,
    convertEntityToList,
    getDeviceQueries,
    getEntitiesFromCSVFile,
    getEntitiesFromFile,
    getEntityList,
    getEntityToModify,
    getItemsToModify,
)
from gam.util.errors import entityActionFailedExit, missingArgumentExit, unknownArgumentExit
from gam.util.orgunits import getOrgUnitItem
from gam.constants import PROJECTION_CHOICE_MAP
from gam.util.access import accessErrorExit


def doDeleteBrowsers():
  cbcm = buildGAPIObject(API.CBCM)
  customerId = _getCustomerIdNoC()
  deviceId = getString(Cmd.OB_DEVICE_ID)
  checkForExtraneousArguments()
  try:
    callGAPI(cbcm.chromebrowsers(), 'delete',
             throwReasons=[GAPI.BAD_REQUEST, GAPI.RESOURCE_NOT_FOUND, GAPI.FORBIDDEN],
             customer=customerId, deviceId=deviceId)
    entityActionPerformed([Ent.CHROME_BROWSER, deviceId])
  except (GAPI.badRequest, GAPI.resourceNotFound, GAPI.forbidden):
    checkEntityAFDNEorAccessErrorExit(None, Ent.CHROME_BROWSER, deviceId)

BROWSER_TIME_OBJECTS = {'firstRecordTime', 'lastActivityTime', 'lastPolicyFetchTime', 'lastRegistrationTime', 'lastStatusReportTime', 'safeBrowsingWarningsResetTime'}

def _showBrowser(browser, FJQC, i=0, count=0):
  if FJQC.formatJSON:
    printLine(json.dumps(cleanJSON(browser), ensure_ascii=False, sort_keys=True))
    return
  printEntity([Ent.CHROME_BROWSER, browser['deviceId']], i, count)
  Ind.Increment()
  showJSON(None, browser, timeObjects=BROWSER_TIME_OBJECTS, dictObjectsKey={'machinePolicies': 'name'})
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
  cbcm = buildGAPIObject(API.CBCM)
  customerId = _getCustomerIdNoC()
  deviceId = getString(Cmd.OB_DEVICE_ID)
  projection = 'BASIC'
  fieldsList = []
  rawFields = None
  FJQC = FormatJSONQuoteChar()
  while Cmd.ArgumentsRemaining():
    myarg = getArgument()
    if myarg == 'annotated':
      projection = 'BASIC'
      fieldsList = BROWSER_ANNOTATED_FIELDS_LIST
    elif myarg in PROJECTION_CHOICE_MAP:
      projection = PROJECTION_CHOICE_MAP[myarg]
      fieldsList = []
    elif getFieldsList(myarg, BROWSER_FIELDS_CHOICE_MAP, fieldsList, initialField='deviceId'):
      pass
    elif myarg == 'rawfields':
      projection = 'FULL'
      rawFields = _getRawFields('deviceId')
    else:
      FJQC.GetFormatJSON(myarg)
  if projection == 'BASIC' and set(fieldsList).intersection(BROWSER_FULL_ACCESS_FIELDS):
    projection = 'FULL'
  fields = getFieldsFromFieldsList(fieldsList) if not rawFields else rawFields
  try:
    browser = callGAPI(cbcm.chromebrowsers(), 'get',
                       throwReasons=[GAPI.BAD_REQUEST, GAPI.RESOURCE_NOT_FOUND, GAPI.INVALID_ARGUMENT, GAPI.FORBIDDEN],
                       customer=customerId, deviceId=deviceId, projection=projection, fields=fields)
    _showBrowser(browser, FJQC)
  except GAPI.invalidArgument as e:
    entityActionFailedWarning([Ent.CHROME_BROWSER, deviceId], str(e))
  except (GAPI.badRequest, GAPI.resourceNotFound, GAPI.forbidden):
    checkEntityAFDNEorAccessErrorExit(None, Ent.CHROME_BROWSER, deviceId)

# gam move browsers ou|org|orgunit <OrgUnitPath>
#	((ids <DeviceIDList>) |
#	 (queries <QueryBrowserList> [querytime<String> <Time>]) |
#	 (browserou <OrgUnitItem>) | (browserous <OrgUnitList>) |
#	 <FileSelector> | <CSVFileSelector>)
#	[batchsize <Integer>]
def doMoveBrowsers():
  cbcm = buildGAPIObject(API.CBCM)
  customerId = _getCustomerIdNoC()
  deviceIds = []
  batch_size = GC.Values[GC.BATCH_SIZE]
  orgUnitPath = ''
  queries = []
  queryTimes = {}
  while Cmd.ArgumentsRemaining():
    myarg = getArgument()
    if myarg in {'ou', 'org', 'orgunit'}:
      orgUnitPath = getOrgUnitItem()
    elif myarg == 'ids':
      deviceIds.extend(convertEntityToList(getString(Cmd.OB_DEVICE_ID_LIST, minLen=0)))
    elif myarg == 'file':
      deviceIds.extend(getEntitiesFromFile(False))
    elif myarg in {'csv', 'csvfile'}:
      deviceIds.extend(getEntitiesFromCSVFile(False))
    elif myarg in {'query', 'queries'}:
      queries = getDeviceQueries(myarg, Ent.CHROME_BROWSER)
    elif myarg.startswith('querytime'):
      queryTimes[myarg] = getTimeOrDeltaFromNow()[0:19]
    elif myarg == 'browserou':
      deviceIds.extend(getItemsToModify(Cmd.ENTITY_BROWSER_OU, getOrgUnitItem(pathOnly=True, absolutePath=True)))
    elif myarg == 'browserous':
      deviceIds.extend(getItemsToModify(Cmd.ENTITY_BROWSER_OUS, getEntityList(Cmd.OB_ORGUNIT_ENTITY, shlexSplit=True)))
    elif myarg == 'batchsize':
      batch_size = getInteger(minVal=1, maxVal=600)
    else:
      unknownArgumentExit()
  if not orgUnitPath:
    missingArgumentExit('orgunit')
  substituteQueryTimes(queries, queryTimes)
  if queries:
    deviceIds.extend(getItemsToModify(Cmd.ENTITY_BROWSER_QUERIES, queries))
  body = {'org_unit_path': orgUnitPath}
  bcount = 0
  jcount = len(deviceIds)
  j = 0
  while bcount < jcount:
    kcount = min(jcount-bcount, batch_size)
    try:
      body['resource_ids'] = deviceIds[bcount:bcount+kcount]
      callGAPI(cbcm.chromebrowsers(), 'moveChromeBrowsersToOu',
               mapNotFound=False,
               throwReasons=[GAPI.INVALID_ORGUNIT, GAPI.BAD_REQUEST, GAPI.RESOURCE_NOT_FOUND, GAPI.FORBIDDEN],
               customer=customerId, body=body)
      for deviceId in deviceIds:
        j += 1
        entityActionPerformed([Ent.ORGANIZATIONAL_UNIT, orgUnitPath, Ent.CHROME_BROWSER, deviceId], j, jcount)
      bcount += kcount
    except GAPI.invalidOrgunit:
      entityActionFailedWarning([Ent.ORGANIZATIONAL_UNIT, orgUnitPath], Msg.INVALID_ORGUNIT)
      break
    except (GAPI.badRequest, GAPI.resourceNotFound, GAPI.forbidden) as e:
      entityActionFailedWarning([Ent.ORGANIZATIONAL_UNIT, orgUnitPath, Ent.CHROME_BROWSER, f'IDs: {deviceIds[bcount]} - {deviceIds[bcount+kcount-1]}'], str(e))
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
  cbcm = buildGAPIObject(API.CBCM)
  customerId = _getCustomerIdNoC()
  _, entityList = getEntityToModify(defaultEntityType=Cmd.ENTITY_BROWSER, browserAllowed=True, crosAllowed=False, userAllowed=False)
  body = {}
  updateNotes = None
  while Cmd.ArgumentsRemaining():
    myarg = getArgument()
    if myarg in UPDATE_BROWSER_ARGUMENT_TO_PROPERTY_MAP:
      up = UPDATE_BROWSER_ARGUMENT_TO_PROPERTY_MAP[myarg]
      if up == 'annotatedNotes':
        body[up] = getStringWithCRsNLs()
        updateNotes = body[up] if myarg == 'updatenotes' and body[up].find('#notes#') != -1 else None
      else:
        body[up] = getString(Cmd.OB_STRING)
    else:
      unknownArgumentExit()
  i = 0
  count = len(entityList)
  for deviceId in entityList:
    i += 1
    try:
      browser = callGAPI(cbcm.chromebrowsers(), 'get',
                         throwReasons=[GAPI.BAD_REQUEST, GAPI.RESOURCE_NOT_FOUND, GAPI.FORBIDDEN],
                         customer=customerId, deviceId=deviceId,
                         projection='BASIC', fields=BROWSER_DEVICEID_ANNOTATED_FIELDS)
      if updateNotes:
        body['annotatedNotes'] = updateNotes.replace('#notes#', browser['annotatedNotes'])
      browser.update(body)
      callGAPI(cbcm.chromebrowsers(), 'update',
               throwReasons=[GAPI.BAD_REQUEST, GAPI.RESOURCE_NOT_FOUND, GAPI.FORBIDDEN],
               customer=customerId, deviceId=deviceId,
               body=browser, projection='BASIC', fields="deviceId")
      entityActionPerformed([Ent.CHROME_BROWSER, deviceId], i, count)
    except (GAPI.badRequest, GAPI.resourceNotFound, GAPI.forbidden):
      checkEntityAFDNEorAccessErrorExit(None, Ent.CHROME_BROWSER, deviceId, i, count)

def _getChromeProfileName():
  profileName = getString(Cmd.OB_CHROMEPROFILE_NAME)
  if not profileName.startswith('customers'):
    customerId = _getCustomerId()
    profileName = f'customers/{customerId}/profiles/{profileName}'
  return profileName

# gam delete chromeprofile <ChromeProfileName>
def doDeleteChromeProfile():
  cm = buildGAPIObject(API.CHROMEMANAGEMENT)
  profileName = _getChromeProfileName()
  checkForExtraneousArguments()
  try:
    callGAPI(cm.customers().profiles(), 'delete',
             throwReasons=[GAPI.INVALID_ARGUMENT, GAPI.NOT_FOUND, GAPI.PERMISSION_DENIED],
             name=profileName)
    entityActionPerformed([Ent.CHROME_PROFILE, profileName])
  except (GAPI.invalidArgument, GAPI.notFound, GAPI.permissionDenied) as e:
    entityActionFailedExit([Ent.CHROME_PROFILE, profileName], str(e))

CHROMEPROFILE_TIME_OBJECTS = {
  'firstEnrollmentTime',
  'lastActivityTime',
  'lastPolicyFetchTime',
  'lastPolicySyncTime',
  'lastStatusReportTime',
  }

def _showChromeProfile(profile, FJQC, i=0, count=0):
  if FJQC.formatJSON:
    printLine(json.dumps(cleanJSON(profile, timeObjects=CHROMEPROFILE_TIME_OBJECTS),
              ensure_ascii=False, sort_keys=True))
    return
  printEntity([Ent.CHROME_PROFILE, profile['name']], i, count)
  Ind.Increment()
  showJSON(None, profile, timeObjects=CHROMEPROFILE_TIME_OBJECTS)
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
  cm = buildGAPIObject(API.CHROMEMANAGEMENT)
  profileName = _getChromeProfileName()
  fieldsList = []
  FJQC = FormatJSONQuoteChar()
  while Cmd.ArgumentsRemaining():
    myarg = getArgument()
    if getFieldsList(myarg, CHROMEPROFILE_FIELDS_CHOICE_MAP, fieldsList, initialField='name'):
      pass
    else:
      FJQC.GetFormatJSON(myarg)
  fields = getFieldsFromFieldsList(fieldsList)
  try:
    profile = callGAPI(cm.customers().profiles(), 'get',
                       throwReasons=[GAPI.INVALID_ARGUMENT, GAPI.NOT_FOUND, GAPI.PERMISSION_DENIED],
                       name=profileName, fields=fields)
    _showChromeProfile(profile, FJQC)
  except (GAPI.invalidArgument, GAPI.notFound, GAPI.permissionDenied) as e:
    entityActionFailedExit([Ent.CHROME_PROFILE, profileName], str(e))

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
    row = flattenJSON(profile, timeObjects=CHROMEPROFILE_TIME_OBJECTS)
    if not FJQC.formatJSON:
      csvPF.WriteRowTitles(row)
    elif csvPF.CheckRowTitles(row):
      csvPF.WriteRowNoFilter({'name': profile['name'], 'profileId': profile['profileId'],
                              'JSON': json.dumps(cleanJSON(profile, timeObjects=CHROMEPROFILE_TIME_OBJECTS),
                                                 ensure_ascii=False, sort_keys=True)})

  cm = buildGAPIObject(API.CHROMEMANAGEMENT)
  csvPF = CSVPrintFile(['name', 'profileId']) if Act.csvFormat() else None
  FJQC = FormatJSONQuoteChar(csvPF)
  OBY = OrderBy(CHROMEPROFILE_ORDERBY_CHOICE_MAP)
  sortHeaders = False
  fieldsList = []
  cbfilter = None
  filterTimes = {}
  while Cmd.ArgumentsRemaining():
    myarg = getArgument()
    if csvPF and myarg == 'todrive':
      csvPF.GetTodriveParameters()
    elif getFieldsList(myarg, CHROMEPROFILE_FIELDS_CHOICE_MAP, fieldsList, initialField=['name', 'profileId']):
      pass
    elif myarg == 'orderby':
      OBY.GetChoice()
    elif myarg.startswith('filtertime'):
      filterTimes[myarg] = getTimeOrDeltaFromNow()
    elif myarg in {'filter', 'filters'}:
      cbfilter = getString(Cmd.OB_STRING)
    elif myarg == 'sortheaders':
      sortHeaders = True
    else:
      FJQC.GetFormatJSONQuoteChar(myarg, True)
  if filterTimes and cbfilter is not None:
    for filterTimeName, filterTimeValue in filterTimes.items():
      cbfilter = cbfilter.replace(f'#{filterTimeName}#', filterTimeValue)
  fields = getItemFieldsFromFieldsList('chromeBrowserProfiles', fieldsList)
  customerId = _getCustomerId()
  parent = f'customers/{customerId}'
  printGettingAllAccountEntities(Ent.CHROME_PROFILE, cbfilter)
  pageMessage = getPageMessage()
  try:
    feed = yieldGAPIpages(cm.customers().profiles(), 'list', 'chromeBrowserProfiles',
                          pageMessage=pageMessage,
                          throwReasons=[GAPI.INVALID_ARGUMENT, GAPI.PERMISSION_DENIED],
                          parent=parent, pageSize=200,
                          filter=cbfilter, orderBy=OBY.orderBy, fields=fields)
    for profiles in feed:
      if not csvPF:
        jcount = len(profiles)
        if not FJQC.formatJSON:
          performActionNumItems(jcount, Ent.CHROME_PROFILE)
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
    entityActionFailedExit([Ent.CHROME_PROFILE, cbfilter], str(e))
  if csvPF:
    if sortHeaders:
      csvPF.SetSortTitles(['name', 'profileId'])
    csvPF.writeCSVfile('Chrome Profiles')

def _getChromeProfileNameList():
  if not Cmd.PeekArgumentPresent(['select', 'commands', 'filter', 'filters']):
    return getString(Cmd.OB_CHROMEPROFILE_NAME_LIST).replace(',', ' ').split()
  return []

def _initChromeProfileNameParameters():
  cm = buildGAPIObject(API.CHROMEMANAGEMENT)
  return (cm, {'profileNameList': _getChromeProfileNameList(),
               'commandNameList': [],
               'customerId': _getCustomerId(),
               'cbfilter': None, 'filterTimes': {},
               'OBY': OrderBy(CHROMEPROFILE_ORDERBY_CHOICE_MAP)})

def _getChromeProfileNameParameters(myarg, parameters):
  if not parameters['cbfilter'] and not parameters['commandNameList'] and myarg == 'select':
    parameters['profileNameList'].extend(getEntityList(Cmd.OB_CHROMEPROFILE_NAME_LIST))
  elif not parameters['cbfilter'] and not parameters['profileNameList'] and myarg == 'commands':
    parameters['commandNameList'].extend(getEntityList(Cmd.OB_CHROMEPROFILE_COMMAND_NAME_LIST))
  elif not parameters['profileNameList'] and not parameters['commandNameList'] and myarg == 'orderby':
    parameters['OBY'].GetChoice()
  elif not parameters['profileNameList'] and not parameters['commandNameList'] and myarg.startswith('filtertime'):
    parameters['filterTimes'][myarg] = getTimeOrDeltaFromNow()
  elif not parameters['profileNameList'] and not parameters['commandNameList'] and myarg in {'filter', 'filters'}:
    parameters['cbfilter'] = getString(Cmd.OB_STRING)
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
  printGettingAllAccountEntities(Ent.CHROME_PROFILE, parameters['cbfilter'])
  pageMessage = getPageMessage()
  try:
    feed = yieldGAPIpages(cm.customers().profiles(), 'list', 'chromeBrowserProfiles',
                          pageMessage=pageMessage,
                          throwReasons=[GAPI.INVALID_ARGUMENT, GAPI.PERMISSION_DENIED],
                          parent=f'customers/{parameters["customerId"]}', pageSize=200,
                          filter=parameters['cbfilter'], orderBy=parameters['OBY'].orderBy,
                          fields='nextPageToken,chromeBrowserProfiles(name)')
    for profiles in feed:
      for profile in profiles:
        parameters['profileNameList'].append(profile['name'])
  except (GAPI.invalidArgument, GAPI.permissionDenied) as e:
    entityActionFailedExit([Ent.CHROME_PROFILE, parameters['cbfilter']], str(e))

CHROMEPROFILECOMMAND_TIME_OBJECTS = {
  'clientExecutionTime',
  'issueTime',
  }

def _showChromeProfileCommand(profcmd, FJQC, i=0, count=0):
  if FJQC.formatJSON:
    printLine(json.dumps(cleanJSON(profcmd, timeObjects=CHROMEPROFILECOMMAND_TIME_OBJECTS),
              ensure_ascii=False, sort_keys=True))
    return
  printEntity([Ent.CHROME_PROFILE_COMMAND, profcmd['name']], i, count)
  Ind.Increment()
  showJSON(None, profcmd, timeObjects=CHROMEPROFILECOMMAND_TIME_OBJECTS)
  Ind.Decrement()

def _printChromeProfileCommand(profcmd, csvPF, FJQC):
  row = flattenJSON(profcmd, timeObjects=CHROMEPROFILECOMMAND_TIME_OBJECTS)
  if not FJQC.formatJSON:
    csvPF.WriteRowTitles(row)
  elif csvPF.CheckRowTitles(row):
    csvPF.WriteRowNoFilter({'name': profcmd['name'],
                            'JSON': json.dumps(cleanJSON(profcmd, timeObjects=CHROMEPROFILECOMMAND_TIME_OBJECTS),
                                               ensure_ascii=False, sort_keys=True)})

# gam create chromeprofilecommand <ChromeProfileNameEntity>
#	[clearcache [<Boolean>]] [clearcookies [<Boolean>]]
#	[csv [todrive <ToDriveAttribute>*] [formatjson [quotechar <Character>]]]
def doCreateChromeProfileCommand():
  cm, parameters = _initChromeProfileNameParameters()
  body = {'commandType': 'clearBrowsingData', 'payload': {}}
  csvPF = None
  FJQC = FormatJSONQuoteChar(None)
  while Cmd.ArgumentsRemaining():
    myarg = getArgument()
    if _getChromeProfileNameParameters(myarg, parameters):
      pass
    elif myarg == 'clearcache':
      body['payload']['clearCache'] = getBoolean()
    elif myarg == 'clearcookies':
      body['payload']['clearCookies'] = getBoolean()
    elif myarg == 'csv':
      csvPF = CSVPrintFile(['name'], 'sortall')
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
      profcmd = callGAPI(cm.customers().profiles().commands(), 'create',
                         throwReasons=[GAPI.INVALID_ARGUMENT, GAPI.NOT_FOUND, GAPI.PERMISSION_DENIED],
                         parent=profileName, body=body)
      if csvPF is None:
        _showChromeProfileCommand(profcmd, FJQC, i, count)
      else:
        _printChromeProfileCommand(profcmd, csvPF, FJQC)
    except (GAPI.notFound) as e:
      entityActionFailedWarning([Ent.CHROME_PROFILE_COMMAND, profileName], str(e), i, count)
    except (GAPI.invalidArgument, GAPI.permissionDenied) as e:
      entityActionFailedExit([Ent.CHROME_PROFILE_COMMAND, profileName], str(e))
  if csvPF:
    csvPF.writeCSVfile('Chrome Profile Commands')

# gam info chromeprofilecommand <ChromeProfileCommandName>
#	[formatjson]
def doInfoChromeProfileCommand():
  cm = buildGAPIObject(API.CHROMEMANAGEMENT)
  profileCommandName = _getChromeProfileName()
  FJQC = FormatJSONQuoteChar()
  while Cmd.ArgumentsRemaining():
    myarg = getArgument()
    FJQC.GetFormatJSON(myarg)
  try:
    profcmd = callGAPI(cm.customers().profiles().commands(), 'get',
                       throwReasons=[GAPI.INVALID_ARGUMENT, GAPI.NOT_FOUND, GAPI.PERMISSION_DENIED],
                       name=profileCommandName)
    _showChromeProfileCommand(profcmd, FJQC)
  except (GAPI.invalidArgument, GAPI.notFound, GAPI.permissionDenied) as e:
    entityActionFailedExit([Ent.CHROME_PROFILE, profileCommandName], str(e))

# gam show chromeprofilecommands <ChromeProfileNameEntity>
#	[formatjson]
# gam print chromeprofilecommands <ChromeProfilNameEntity> [todrive <ToDriveAttribute>*]
#	[formatjson [quotechar <Character>]]
def doPrintShowChromeProfileCommands():
  csvPF = CSVPrintFile(['name']) if Act.csvFormat() else None
  FJQC = FormatJSONQuoteChar(csvPF)
  cm, parameters = _initChromeProfileNameParameters()
  while Cmd.ArgumentsRemaining():
    myarg = getArgument()
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
      printGettingEntityItemForWhom(Ent.CHROME_PROFILE_COMMAND, profileName, i, count)
      pageMessage = getPageMessage()
      try:
        profcmds = callGAPIpages(cm.customers().profiles().commands(), 'list', 'chromeBrowserProfileCommands',
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
        entityActionFailedWarning([Ent.CHROME_PROFILE, profileName], str(e), i, count)
      except (GAPI.invalidArgument, GAPI.permissionDenied) as e:
        entityActionFailedExit([Ent.CHROME_PROFILE, profileName], str(e))
  elif parameters['commandNameList']:
    count = len(parameters['commandNameList'])
    i = 0
    for profileCommandName in parameters['commandNameList']:
      i +=1
      try:
        profcmd = callGAPI(cm.customers().profiles().commands(), 'get',
                           throwReasons=[GAPI.INVALID_ARGUMENT, GAPI.NOT_FOUND, GAPI.PERMISSION_DENIED],
                           name=profileCommandName)
        if not csvPF:
          _showChromeProfileCommand(profcmd, FJQC, i, count)
        else:
          _printChromeProfileCommand(profcmd, csvPF, FJQC)
      except GAPI.notFound as e:
        entityActionFailedWarning([Ent.CHROME_PROFILE_COMMAND, profileCommandName], str(e), i, count)
      except (GAPI.invalidArgument, GAPI.permissionDenied) as e:
        entityActionFailedExit([Ent.CHROME_PROFILE, profileCommandName], str(e))
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
    row = flattenJSON(browser, timeObjects=BROWSER_TIME_OBJECTS)
    if not FJQC.formatJSON:
      csvPF.WriteRowTitles(row)
    elif csvPF.CheckRowTitles(row):
      csvPF.WriteRowNoFilter({'deviceId': browser['deviceId'],
                              'JSON': json.dumps(cleanJSON(browser, timeObjects=BROWSER_TIME_OBJECTS),
                                                 ensure_ascii=False, sort_keys=True)})

  cbcm = buildGAPIObject(API.CBCM)
  customerId = _getCustomerIdNoC()
  csvPF = CSVPrintFile(['deviceId']) if Act.csvFormat() else None
  FJQC = FormatJSONQuoteChar(csvPF)
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
    myarg = getArgument()
    if csvPF and myarg == 'todrive':
      csvPF.GetTodriveParameters()
    elif myarg in {'query', 'queries'}:
      queries = getDeviceQueries(myarg, Ent.CHROME_BROWSER)
    elif myarg.startswith('querytime'):
      queryTimes[myarg] = getTimeOrDeltaFromNow()[0:19]
    elif myarg in {'ou', 'org', 'orgunit', 'browserou'}:
      orgUnitPath = getOrgUnitItem(pathOnly=True, absolutePath=True)
    elif myarg == 'select':
      _, entityList = getEntityToModify(defaultEntityType=Cmd.ENTITY_BROWSER, browserAllowed=True, crosAllowed=False, userAllowed=False)
    elif myarg == 'orderby':
      orderBy, sortOrder = getOrderBySortOrder(BROWSER_ORDERBY_CHOICE_MAP, 'DESCENDING', True)
    elif myarg == 'annotated':
      projection = 'BASIC'
      fieldsList = BROWSER_ANNOTATED_FIELDS_LIST
    elif (myarg == 'projection') or myarg in PROJECTION_CHOICE_MAP:
      if myarg == 'projection':
        projection = getChoice(PROJECTION_CHOICE_MAP, mapChoice=True)
      else:
        projection = PROJECTION_CHOICE_MAP[myarg]
      fieldsList = []
    elif myarg == 'allfields':
      projection = 'FULL'
      sortHeaders = True
      fieldsList = []
    elif myarg == 'sortheaders':
      sortHeaders = True
    elif getFieldsList(myarg, BROWSER_FIELDS_CHOICE_MAP, fieldsList, initialField='deviceId'):
      pass
    elif myarg == 'rawfields':
      projection = 'FULL'
      rawFields = _getRawFields('deviceId')
    else:
      FJQC.GetFormatJSONQuoteChar(myarg, True)
  if projection == 'BASIC' and set(fieldsList).intersection(BROWSER_FULL_ACCESS_FIELDS):
    projection = 'FULL'
  if FJQC.formatJSON:
    sortHeaders = False
  substituteQueryTimes(queries, queryTimes)
  if entityList is None:
    fields = getItemFieldsFromFieldsList('browsers', fieldsList) if not rawFields else f'nextPageToken,browsers({rawFields})'
    for query in queries:
      printGettingAllAccountEntities(Ent.CHROME_BROWSER, query)
      pageMessage = getPageMessage()
      try:
        feed = yieldGAPIpages(cbcm.chromebrowsers(), 'list', 'browsers',
                              pageMessage=pageMessage, messageAttribute='deviceId',
                              throwReasons=[GAPI.INVALID_INPUT, GAPI.BAD_REQUEST, GAPI.INVALID_ARGUMENT, GAPI.INVALID_ORGUNIT, GAPI.FORBIDDEN],
                              retryReasons=GAPI.SERVICE_NOT_AVAILABLE_RETRY_REASONS,
                              customer=customerId, orgUnitPath=orgUnitPath, query=query, projection=projection,
                              orderBy=orderBy, sortOrder=sortOrder, fields=fields)
        for browsers in feed:
          if not csvPF:
            jcount = len(browsers)
            if not FJQC.formatJSON:
              performActionNumItems(jcount, Ent.CHROME_BROWSER)
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
          entityActionFailedWarning([Ent.CHROME_BROWSER, None], invalidQuery(query))
        else:
          entityActionFailedWarning([Ent.CHROME_BROWSER, None], str(e))
        return
      except (GAPI.invalidArgument, GAPI.invalidOrgunit, GAPI.forbidden) as e:
        entityActionFailedWarning([Ent.CHROME_BROWSER, None], str(e))
        return
      except (GAPI.badRequest, GAPI.resourceNotFound):
        accessErrorExit(None)
  else:
    sortRows = True
    jcount = len(entityList)
    fields = getFieldsFromFieldsList(fieldsList) if not rawFields else rawFields
    j = 0
    for deviceId in entityList:
      j += 1
      try:
        browser = callGAPI(cbcm.chromebrowsers(), 'get',
                           throwReasons=[GAPI.BAD_REQUEST, GAPI.RESOURCE_NOT_FOUND, GAPI.INVALID_ARGUMENT, GAPI.FORBIDDEN],
                           customer=customerId, deviceId=deviceId, projection=projection, fields=fields)
        _printBrowser(browser)
      except GAPI.invalidArgument as e:
        entityActionFailedWarning([Ent.CHROME_BROWSER, deviceId], str(e))
      except (GAPI.badRequest, GAPI.resourceNotFound, GAPI.forbidden):
        checkEntityAFDNEorAccessErrorExit(None, Ent.CHROME_BROWSER, deviceId)
  if csvPF:
    if sortRows and orderBy:
      csvPF.SortRows(orderBy, reverse=sortOrder == 'DESCENDING')
    if sortHeaders:
      csvPF.SetSortTitles(['deviceId'])
    csvPF.writeCSVfile('Browsers')

BROWSER_TOKEN_TIME_OBJECTS = {'createTime', 'expireTime', 'revokeTime'}

def _showBrowserToken(browser, FJQC, i=0, count=0):
  if FJQC.formatJSON:
    printLine(json.dumps(cleanJSON(browser), ensure_ascii=False, sort_keys=True))
    return
  printEntity([Ent.CHROME_BROWSER_ENROLLMENT_TOKEN, browser['token']], i, count)
  Ind.Increment()
  showJSON(None, browser, timeObjects=BROWSER_TOKEN_TIME_OBJECTS)
  Ind.Decrement()

# gam create browsertoken
#	[ou|org|orgunit|browserou <OrgUnitPath>] [expire|expires <Time>]
#	[formatjson]
def doCreateBrowserToken():
  cbcm = buildGAPIObject(API.CBCM)
  customerId = _getCustomerIdNoC()
  FJQC = FormatJSONQuoteChar()
  body = {'token_type': 'CHROME_BROWSER'}
  while Cmd.ArgumentsRemaining():
    myarg = getArgument()
    if myarg in {'ou', 'org', 'orgunit', 'browserou'}:
      body['org_unit_path'] = getOrgUnitItem(pathOnly=True, absolutePath=True)
    elif myarg in ['expire', 'expires']:
      body['expire_time'] = getTimeOrDeltaFromNow()
    else:
      FJQC.GetFormatJSON(myarg)
  try:
    browser = callGAPI(cbcm.enrollmentTokens(), 'create',
                       throwReasons=[GAPI.INVALID_INPUT, GAPI.BAD_REQUEST, GAPI.INVALID_ORGUNIT, GAPI.FORBIDDEN],
                       customer=customerId, body=body)
    if not FJQC.formatJSON:
      entityActionPerformed([Ent.CHROME_BROWSER_ENROLLMENT_TOKEN, browser['token']])
    Ind.Increment()
    _showBrowserToken(browser, FJQC, 0, 0)
    Ind.Decrement()
  except (GAPI.invalidInput, GAPI.invalidOrgunit) as e:
    entityActionFailedWarning([Ent.CHROME_BROWSER_ENROLLMENT_TOKEN, None], str(e))
  except (GAPI.badRequest, GAPI.resourceNotFound, GAPI.forbidden):
    accessErrorExit(None)

# gam revoke browsertoken <BrowserTokenPermanentID>
def doRevokeBrowserToken():
  cbcm = buildGAPIObject(API.CBCM)
  customerId = _getCustomerIdNoC()
  tokenPermanentId = getString(Cmd.OB_BROWSER_ENROLLEMNT_TOKEN_ID)
  checkForExtraneousArguments()
  try:
    callGAPI(cbcm.enrollmentTokens(), 'revoke',
             throwReasons=[GAPI.INVALID, GAPI.INVALID_INPUT, GAPI.BAD_REQUEST, GAPI.INVALID_ORGUNIT, GAPI.FORBIDDEN],
             customer=customerId, tokenPermanentId=tokenPermanentId)
    entityActionPerformed([Ent.CHROME_BROWSER_ENROLLMENT_TOKEN, tokenPermanentId])
  except (GAPI.invalid, GAPI.invalidInput, GAPI.badRequest, GAPI.resourceNotFound, GAPI.invalidOrgunit) as e:
    entityActionFailedWarning([Ent.CHROME_BROWSER_ENROLLMENT_TOKEN, tokenPermanentId], str(e))
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
    row = flattenJSON(browser, timeObjects=BROWSER_TOKEN_TIME_OBJECTS)
    if not FJQC.formatJSON:
      csvPF.WriteRowTitles(row)
    elif csvPF.CheckRowTitles(row):
      csvPF.WriteRowNoFilter({'token': browser['token'],
                              'JSON': json.dumps(cleanJSON(browser, timeObjects=BROWSER_TOKEN_TIME_OBJECTS),
                                                 ensure_ascii=False, sort_keys=True)})

  cbcm = buildGAPIObject(API.CBCM)
  customerId = _getCustomerIdNoC()
  csvPF = CSVPrintFile(['token']) if Act.csvFormat() else None
  FJQC = FormatJSONQuoteChar(csvPF)
  fieldsList = []
  orderBy = 'token'
  sortOrder = 'ASCENDING'
  orgUnitPath = None
  queries = [None]
  queryTimes = {}
  sortHeaders = False
  while Cmd.ArgumentsRemaining():
    myarg = getArgument()
    if csvPF and myarg == 'todrive':
      csvPF.GetTodriveParameters()
    elif myarg in {'query', 'queries'}:
      queries = getDeviceQueries(myarg, Ent.CHROME_BROWSER)
    elif myarg.startswith('querytime'):
      queryTimes[myarg] = getTimeOrDeltaFromNow()[0:19]
    elif myarg in {'ou', 'org', 'orgunit', 'browserou'}:
      orgUnitPath = getOrgUnitItem(pathOnly=True, absolutePath=True)
    elif myarg == 'orderby':
      orderBy, sortOrder = getOrderBySortOrder(BROWSER_TOKEN_FIELDS_CHOICE_MAP, 'DESCENDING', True)
    elif myarg == 'allfields':
      sortHeaders = True
      fieldsList = []
    elif myarg == 'sortheaders':
      sortHeaders = True
    elif getFieldsList(myarg, BROWSER_TOKEN_FIELDS_CHOICE_MAP, fieldsList, initialField='token'):
      pass
    else:
      FJQC.GetFormatJSONQuoteChar(myarg, True)
  fields = getItemFieldsFromFieldsList('chromeEnrollmentTokens', fieldsList)
  if FJQC.formatJSON:
    sortHeaders = False
  substituteQueryTimes(queries, queryTimes)
  for query in queries:
    printGettingAllAccountEntities(Ent.CHROME_BROWSER_ENROLLMENT_TOKEN, query)
    pageMessage = getPageMessage()
    try:
      browsers = callGAPIpages(cbcm.enrollmentTokens(), 'list', 'chromeEnrollmentTokens',
                               pageMessage=pageMessage,
                               throwReasons=[GAPI.INVALID_INPUT, GAPI.BAD_REQUEST, GAPI.INVALID_ORGUNIT, GAPI.FORBIDDEN],
                               customer=customerId, orgUnitPath=orgUnitPath, query=query,
                               fields=fields)
      if not csvPF:
        jcount = len(browsers)
        performActionNumItems(jcount, Ent.CHROME_BROWSER_ENROLLMENT_TOKEN)
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
        entityActionFailedWarning([Ent.CHROME_BROWSER_ENROLLMENT_TOKEN, None], invalidQuery(query))
      else:
        entityActionFailedWarning([Ent.CHROME_BROWSER_ENROLLMENT_TOKEN, None], str(e))
    except GAPI.invalidOrgunit as e:
      entityActionFailedWarning([Ent.CHROME_BROWSER_ENROLLMENT_TOKEN, None], str(e))
    except (GAPI.badRequest, GAPI.resourceNotFound, GAPI.forbidden):
      accessErrorExit(None)
  if csvPF:
    if orderBy:
      csvPF.SortRows(orderBy, reverse=sortOrder == 'DESCENDING')
    if sortHeaders:
      csvPF.SetSortTitles(['token'])
    csvPF.writeCSVfile('Chrome Browser Enrollment Tokens')

