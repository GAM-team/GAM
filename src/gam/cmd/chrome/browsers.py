"""GAM Chrome browser management."""

import json

from gamlib import api as API
from gamlib import settings as GC
from gamlib import gapi as GAPI
from gamlib import msgs as Msg
from gam.var import Act, Cmd, Ent, Ind
from gam.util.access import checkEntityAFDNEorAccessErrorExit
from gam.util.api import buildGAPIObject
from gam.util.api_call import callGAPI, yieldGAPIpages
from gam.util.args import (
    checkForExtraneousArguments,
    getArgument,
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
    printLine,
)
from gam.util.customer import _getCustomerIdNoC
from gam.util.entity import (
    convertEntityToList,
    getDeviceQueries,
    getEntitiesFromCSVFile,
    getEntitiesFromFile,
    getEntityList,
    getEntityToModify,
    getItemsToModify,
)
from gam.util.errors import missingArgumentExit, unknownArgumentExit
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


