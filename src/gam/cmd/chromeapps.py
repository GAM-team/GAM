"""GAM Chrome app, AUE, and version management."""

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
from gam.util.access import checkEntityAFDNEorAccessErrorExit
from gam.util.api import buildGAPIObject, buildGAPIObjectNoAuthentication, callGAPI, callGAPIpages
from gam.util.args import (
    OrderBy,
    YYYYMMDD_FORMAT,
    getArgument,
    getBoolean,
    getCharacter,
    getChoice,
    getInteger,
    getString,
    getYYYYMMDD,
    makeOrgUnitPathAbsolute,
    makeOrgUnitPathRelative,
    todaysDate,
)
from gam.util.csv_pf import (
    CSVPrintFile,
    FormatJSONQuoteChar,
    cleanJSON,
    flattenJSON,
    showJSON,
)
from gam.util.display import (
    actionNotPerformedNumItemsWarning,
    entityActionFailedWarning,
    entityPerformActionNumItems,
    getPageMessage,
    performActionNumItems,
    printEntity,
    printGettingAllAccountEntities,
    printKeyValueList,
    printLine,
)
from gam.util.entity import convertEntityToList, getEntityList
from gam.util.errors import missingArgumentExit, unknownArgumentExit
from gam.util.fileio import UNKNOWN
from gam.util.orgunits import getOrgUnitId

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

def doInfoChromeApp():
  cm = buildGAPIObject(API.CHROMEMANAGEMENT_APPDETAILS)
  app_type = getChoice(_getMain().CHROME_APPS_TYPE_CHOICES)
  app_id = getString(Cmd.OB_APP_ID)
  FJQC = FormatJSONQuoteChar()
  while Cmd.ArgumentsRemaining():
    myarg = getArgument()
    FJQC.GetFormatJSON(myarg)
  if app_type == 'chrome':
    service = cm.customers().apps().chrome()
  elif app_type == 'android':
    service = cm.customers().apps().android()
  else:
    service = cm.customers().apps().web()
  try:
    appDetails = callGAPI(service, 'get',
                          throwReasons=[GAPI.BAD_REQUEST, GAPI.NOT_FOUND, GAPI.FORBIDDEN],
                          name=f'customers/{GC.Values[GC.CUSTOMER_ID]}/apps/{app_type}/{app_id}')
    if FJQC.formatJSON:
      printLine(json.dumps(cleanJSON(appDetails), ensure_ascii=False, sort_keys=True))
      return
    printEntity([Ent.CHROME_APP, app_id])
    Ind.Increment()
    showJSON(None, appDetails, timeObjects=_getMain().CHROME_APPS_TIME_OBJECTS)
    Ind.Decrement()
  except (GAPI.badRequest, GAPI.notFound, GAPI.forbidden):
    checkEntityAFDNEorAccessErrorExit(None, Ent.CHROME_APP, f'{app_type}/{app_id}')

def _getPrintChromeGetting(subou, pfilter, entityType):
  orgUnitPath = subou[0]
  orgUnitId = subou[1]
  query = pfilter
  if orgUnitId is not None:
    if query:
      query += ' AND '
    else:
      query = ''
    query += f'orgUnitPath={orgUnitPath}'
  printGettingAllAccountEntities(entityType, query)
  return (orgUnitPath, orgUnitId)

CHROME_APPS_ORDERBY_CHOICE_MAP = {
  'appname': 'app_name',
  'apptype': 'appType',
  'installtype': 'install_type',
  'numberofpermissions': 'number_of_permissions',
  'totalinstallcount': 'total_install_count',
  }
CHROME_APPS_TITLES = [
  'displayName',
  'browserDeviceCount', 'osUserCount',
  'appType', 'description',
  'appInstallType', 'appSource',
  'disabled', 'homepageUri', 'permissions'
  ]

# gam print chromeapps [todrive <ToDriveAttribute>*]
#	[(ou <OrgUnitItem>)|(ou_and_children <OrgUnitItem>)|
#	 (ous <OrgUnitList>)|(ous_and_children <OrgUnitList>)]
#	[filter <String>]
#	[orderby appname|apptype|installtype|numberofpermissions|totalinstallcount]
#	[formatjson [quotechar <Character>]] [delimiter <Character>]
# gam show chromeapps
#	[(ou <OrgUnitItem>)|(ou_and_children <OrgUnitItem>)|
#	 (ous <OrgUnitList>)|(ous_and_children <OrgUnitList>)]
#	[filter <String>]
#	[orderby appname|apptype|installtype|numberofpermissions|totalinstallcount]
#	[formatjson]
def doPrintShowChromeApps():
  def _printApp(app):
    if showOrgUnit:
      app['orgUnitPath'] = orgUnitPath
    row = flattenJSON(app, simpleLists=['permissions'], delimiter=delimiter)
    if not FJQC.formatJSON:
      csvPF.WriteRowTitles(row)
    elif csvPF.CheckRowTitles(row):
      csvPF.WriteRowNoFilter({'appId': app['appId'],
                              'JSON': json.dumps(cleanJSON(app), ensure_ascii=False, sort_keys=True)})

  def _showApp(app, i=0, count=0):
    if showOrgUnit:
      app['orgUnitPath'] = orgUnitPath
    if FJQC.formatJSON:
      printLine(json.dumps(cleanJSON(app), ensure_ascii=False, sort_keys=True))
      return
    printEntity([Ent.CHROME_APP, app['appId']], i, count)
    Ind.Increment()
    showJSON(None, app)
    Ind.Decrement()

  cd = buildGAPIObject(API.DIRECTORY)
  cm = buildGAPIObject(API.CHROMEMANAGEMENT)
  customerId = _getMain()._getCustomersCustomerIdWithC()
  csvPF = CSVPrintFile(['appId']) if Act.csvFormat() else None
  FJQC = FormatJSONQuoteChar(csvPF)
  delimiter = GC.Values[GC.CSV_OUTPUT_FIELD_DELIMITER]
  ous = [None]
  directlyInOU = True
  showOrgUnit = False
  orderBy = pfilter = None
  while Cmd.ArgumentsRemaining():
    myarg = getArgument()
    if csvPF and myarg == 'todrive':
      csvPF.GetTodriveParameters()
    elif myarg in _getMain().ORGUNIT_ENTITIES_MAP:
      myarg = _getMain().ORGUNIT_ENTITIES_MAP[myarg]
      ous = convertEntityToList(getString(Cmd.OB_ENTITY, minLen=0), shlexSplit=True, nonListEntityType=myarg in [Cmd.ENTITY_OU, Cmd.ENTITY_OU_AND_CHILDREN])
      directlyInOU = myarg in {Cmd.ENTITY_OU, Cmd.ENTITY_OUS}
    elif myarg == 'filter':
      pfilter = getString(Cmd.OB_STRING)
    elif myarg == 'orderby':
      orderBy = getChoice(CHROME_APPS_ORDERBY_CHOICE_MAP, mapChoice=True)
    elif myarg == 'delimiter':
      delimiter = getCharacter()
    else:
      FJQC.GetFormatJSONQuoteChar(myarg, True)
  if ous[0] is not None:
    showOrgUnit = True
  if csvPF and not FJQC.formatJSON:
    csvPF.AddTitles(CHROME_APPS_TITLES)
    if showOrgUnit:
      csvPF.AddTitle('orgUnitPath')
  for ou in ous:
    if ou is not None:
      ou = makeOrgUnitPathAbsolute(ou)
      _, orgUnitId = getOrgUnitId(cd, ou)
      ouList = [(ou, orgUnitId[3:])]
    else:
      ouList = [('/', None)]
    if not directlyInOU:
      try:
        orgs = callGAPI(cd.orgunits(), 'list',
                        throwReasons=GAPI.ORGUNIT_GET_THROW_REASONS,
                        customerId=GC.Values[GC.CUSTOMER_ID], orgUnitPath=makeOrgUnitPathRelative(ou),
                        type='all', fields='organizationUnits(orgUnitPath,orgUnitId)')
      except (GAPI.invalidOrgunit, GAPI.orgunitNotFound, GAPI.backendError, GAPI.badRequest, GAPI.invalidCustomerId, GAPI.loginRequired):
        checkEntityDNEorAccessErrorExit(cd, Ent.ORGANIZATIONAL_UNIT, ou)
        return
      ouList.extend([(subou['orgUnitPath'], subou['orgUnitId'][3:]) for subou in sorted(orgs.get('organizationUnits', []), key=lambda k: k['orgUnitPath'])])
    for subou in ouList:
      orgUnitPath, orgUnitId = _getPrintChromeGetting(subou, pfilter, Ent.CHROME_APP)
      pageMessage = getPageMessage()
      try:
        apps = callGAPIpages(cm.customers().reports(), 'countInstalledApps', 'installedApps',
                             throwReasons=[GAPI.INVALID, GAPI.INVALID_ARGUMENT, GAPI.PERMISSION_DENIED, GAPI.SERVICE_NOT_AVAILABLE],
                             retryReasons=GAPI.SERVICE_NOT_AVAILABLE_RETRY_REASONS,
                             pageMessage=pageMessage,
                             customer=customerId, orgUnitId=orgUnitId, filter=pfilter, orderBy=orderBy)
      except (GAPI.invalid, GAPI.invalidArgument, GAPI.permissionDenied, GAPI.serviceNotAvailable) as e:
        entityActionFailedWarning([Ent.CHROME_APP, None], str(e))
        return
      if not csvPF:
        jcount = len(apps)
        if not FJQC.formatJSON:
          entityPerformActionNumItems([Ent.ORGANIZATIONAL_UNIT, orgUnitPath], jcount, Ent.CHROME_APP)
        Ind.Increment()
        j = 0
        for app in apps:
          j += 1
          _showApp(app, j, jcount)
        Ind.Decrement()
      else:
        for app in apps:
          _printApp(app)
  if csvPF:
    csvPF.writeCSVfile('Chrome Installed Applications')

CHROME_APP_DEVICES_APPTYPE_CHOICE_MAP = {
  'extension': 'EXTENSION',
  'app': 'APP',
  'theme': 'THEME',
  'hostedapp': 'HOSTED_APP',
  'androidapp': 'ANDROID_APP',
  }
CHROME_APP_DEVICES_ORDERBY_CHOICE_MAP = {
  'deviceid': 'deviceId',
  'machine': 'machine',
  }
CHROME_APP_DEVICES_TITLES = ['appType', 'deviceId', 'machine']

# gam print chromeappdevices [todrive <ToDriveAttribute>*]
#	appid <AppID> apptype extension|app|theme|hostedapp|androidapp
#	[(ou <OrgUnitItem>)|(ou_and_children <OrgUnitItem>)|
#	 (ous <OrgUnitList>)|(ous_and_children <OrgUnitList>)]
#	[start <Date>] [end <Date>]
#	[orderby deviceid|machine]
#	[formatjson [quotechar <Character>]]
# gam show chromeappdevices
#	appid <AppID> apptype extension|app|theme|hostedapp|androidapp
#	[(ou <OrgUnitItem>)|(ou_and_children <OrgUnitItem>)|
#	 (ous <OrgUnitList>)|(ous_and_children <OrgUnitList>)]
#	[start <Date>] [end <Date>]
#	[orderby deviceid|machine]
#	[formatjson]
def doPrintShowChromeAppDevices():
  def _printDevice(device):
    device['appId'] = appId
    device['appType'] = appType
    if showOrgUnit:
      device['orgUnitPath'] = orgUnitPath
    row = flattenJSON(device)
    if not FJQC.formatJSON:
      csvPF.WriteRow(row)
    elif csvPF.CheckRowTitles(row):
      csvPF.WriteRowNoFilter({'appId': device['appId'],
                              'JSON': json.dumps(cleanJSON(device), ensure_ascii=False, sort_keys=True)})

  def _showDevice(device, i=0, count=0):
    device['appId'] = appId
    device['appType'] = appType
    if showOrgUnit:
      device['orgUnitPath'] = orgUnitPath
    if FJQC.formatJSON:
      printLine(json.dumps(cleanJSON(device), ensure_ascii=False, sort_keys=True))
      return
    printEntity([Ent.CHROME_APP, device['appId']], i, count)
    Ind.Increment()
    showJSON(None, device)
    Ind.Decrement()

  cd = buildGAPIObject(API.DIRECTORY)
  cm = buildGAPIObject(API.CHROMEMANAGEMENT)
  customerId = _getMain()._getCustomersCustomerIdWithC()
  csvPF = CSVPrintFile(['appId']) if Act.csvFormat() else None
  FJQC = FormatJSONQuoteChar(csvPF)
  ous = [None]
  directlyInOU = True
  showOrgUnit = False
  appId = appType = orderBy = None
  startDate = endDate = pfilter = None
  while Cmd.ArgumentsRemaining():
    myarg = getArgument()
    if csvPF and myarg == 'todrive':
      csvPF.GetTodriveParameters()
    elif myarg in _getMain().ORGUNIT_ENTITIES_MAP:
      myarg = _getMain().ORGUNIT_ENTITIES_MAP[myarg]
      ous = convertEntityToList(getString(Cmd.OB_ENTITY, minLen=0), shlexSplit=True, nonListEntityType=myarg in [Cmd.ENTITY_OU, Cmd.ENTITY_OU_AND_CHILDREN])
      directlyInOU = myarg in {Cmd.ENTITY_OU, Cmd.ENTITY_OUS}
    elif myarg == 'appid':
      appId = getString(Cmd.OB_APP_ID)
    elif myarg == 'apptype':
      appType = getChoice(CHROME_APP_DEVICES_APPTYPE_CHOICE_MAP, mapChoice=True)
    elif myarg in CROS_START_ARGUMENTS:
      startDate, _ = _getMain()._getFilterDateTime()
      startDate = startDate.strftime(YYYYMMDD_FORMAT)
    elif myarg in CROS_END_ARGUMENTS:
      endDate, _ = _getMain()._getFilterDateTime()
      endDate = endDate.strftime(YYYYMMDD_FORMAT)
    elif myarg == 'orderby':
      orderBy = getChoice(CHROME_APP_DEVICES_ORDERBY_CHOICE_MAP, mapChoice=True)
    else:
      FJQC.GetFormatJSONQuoteChar(myarg, True)
  if appId is None:
    missingArgumentExit('appid')
  if appType is None:
    missingArgumentExit('apptype')
  if endDate:
    pfilter = f'last_active_date<={endDate}'
  if startDate:
    if pfilter:
      pfilter += ' AND '
    else:
      pfilter = ''
    pfilter += f'last_active_date>={startDate}'
  if ous[0] is not None:
    showOrgUnit = True
  if csvPF and not FJQC.formatJSON:
    csvPF.AddTitles(CHROME_APP_DEVICES_TITLES)
    if showOrgUnit:
      csvPF.AddTitle('orgUnitPath')
  for ou in ous:
    if ou is not None:
      ou = makeOrgUnitPathAbsolute(ou)
      _, orgUnitId = getOrgUnitId(cd, ou)
      ouList = [(ou, orgUnitId[3:])]
    else:
      ouList = [('/', None)]
    if not directlyInOU:
      try:
        orgs = callGAPI(cd.orgunits(), 'list',
                        throwReasons=GAPI.ORGUNIT_GET_THROW_REASONS,
                        customerId=GC.Values[GC.CUSTOMER_ID], orgUnitPath=makeOrgUnitPathRelative(ou),
                        type='all', fields='organizationUnits(orgUnitPath,orgUnitId)')
      except (GAPI.invalidOrgunit, GAPI.orgunitNotFound, GAPI.backendError, GAPI.badRequest, GAPI.invalidCustomerId, GAPI.loginRequired):
        checkEntityDNEorAccessErrorExit(cd, Ent.ORGANIZATIONAL_UNIT, ou)
        return
      ouList.extend([(subou['orgUnitPath'], subou['orgUnitId'][3:]) for subou in sorted(orgs.get('organizationUnits', []), key=lambda k: k['orgUnitPath'])])
    for subou in ouList:
      orgUnitPath, orgUnitId = _getPrintChromeGetting(subou, pfilter, Ent.CHROME_APP_DEVICE)
      pageMessage = getPageMessage()
      try:
        devices = callGAPIpages(cm.customers().reports(), 'findInstalledAppDevices', 'devices',
                                throwReasons=[GAPI.INVALID, GAPI.INVALID_ARGUMENT, GAPI.PERMISSION_DENIED, GAPI.SERVICE_NOT_AVAILABLE],
                                retryReasons=GAPI.SERVICE_NOT_AVAILABLE_RETRY_REASONS,
                                pageMessage=pageMessage,
                                appId=appId, appType=appType,
                                customer=customerId, orgUnitId=orgUnitId, filter=pfilter, orderBy=orderBy)
      except (GAPI.invalid, GAPI.invalidArgument, GAPI.permissionDenied, GAPI.serviceNotAvailable) as e:
        entityActionFailedWarning([Ent.CHROME_APP_DEVICE, None], str(e))
        return
      if not csvPF:
        jcount = len(devices)
        if not FJQC.formatJSON:
          entityPerformActionNumItems([Ent.ORGANIZATIONAL_UNIT, orgUnitPath], jcount, Ent.CHROME_APP_DEVICE)
        Ind.Increment()
        j = 0
        for device in devices:
          j += 1
          _showDevice(device, j, jcount)
        Ind.Decrement()
      else:
        for device in devices:
          _printDevice(device)
  if csvPF:
    csvPF.writeCSVfile('Chrome Installed Application Devices')


CHROME_AUE_TITLES = ['aueMonth', 'aueYear', 'expired']

# gam print chromeaues [todrive <ToDriveAttribute>*]
#	[(ou <OrgUnitItem>)|(ou_and_children <OrgUnitItem>)|
#	 (ous <OrgUnitList>)|(ous_and_children <OrgUnitList>)]
#	[minauedate <Date>] [maxauedate <Date>]
#	[formatjson [quotechar <Character>]]
# gam show chromeaues
#	[(ou <OrgUnitItem>)|(ou_and_children <OrgUnitItem>)|
#	 (ous <OrgUnitList>)|(ous_and_children <OrgUnitList>)]
#	[minauedate <Date>] [maxauedate <Date>]
#	[formatjson]
def doPrintShowChromeAues():
  def _printAue(aue):
    if showOrgUnit:
      aue['orgUnitPath'] = orgUnitPath
    row = flattenJSON(aue)
    if not FJQC.formatJSON:
      csvPF.WriteRow(row)
    elif csvPF.CheckRowTitles(row):
      csvPF.WriteRowNoFilter({'model': aue['model'], 'count': aue['count'],
                              'JSON': json.dumps(cleanJSON(aue), ensure_ascii=False, sort_keys=True)})

  def _showAue(aue, i=0, count=0):
    if showOrgUnit:
      aue['orgUnitPath'] = orgUnitPath
    if FJQC.formatJSON:
      printLine(json.dumps(cleanJSON(aue), ensure_ascii=False, sort_keys=True))
      return
    printEntity([Ent.CHROME_MODEL, aue['model']], i, count)
    Ind.Increment()
    showJSON(None, aue)
    Ind.Decrement()

  cd = buildGAPIObject(API.DIRECTORY)
  cm = buildGAPIObject(API.CHROMEMANAGEMENT)
  customerId = _getMain()._getCustomersCustomerIdWithC()
  csvPF = CSVPrintFile(['model', 'count']) if Act.csvFormat() else None
  FJQC = FormatJSONQuoteChar(csvPF)
  ous = [None]
  directlyInOU = True
  showOrgUnit = False
  minAueDate = maxAueDate = pfilter = None
  while Cmd.ArgumentsRemaining():
    myarg = getArgument()
    if csvPF and myarg == 'todrive':
      csvPF.GetTodriveParameters()
    elif myarg in _getMain().ORGUNIT_ENTITIES_MAP:
      myarg = _getMain().ORGUNIT_ENTITIES_MAP[myarg]
      ous = convertEntityToList(getString(Cmd.OB_ENTITY, minLen=0), shlexSplit=True, nonListEntityType=myarg in [Cmd.ENTITY_OU, Cmd.ENTITY_OU_AND_CHILDREN])
      directlyInOU = myarg in {Cmd.ENTITY_OU, Cmd.ENTITY_OUS}
    elif myarg == 'minauedate':
      minAueDate, _ = _getMain()._getFilterDateTime()
      minAueDate = minAueDate.strftime(YYYYMMDD_FORMAT)
    elif myarg == 'maxauedate':
      maxAueDate, _ = _getMain()._getFilterDateTime()
      maxAueDate = maxAueDate.strftime(YYYYMMDD_FORMAT)
    else:
      FJQC.GetFormatJSONQuoteChar(myarg, True)
  if minAueDate:
    pfilter = f'minAueDate={minAueDate}'
  if maxAueDate:
    if pfilter:
      pfilter += ' AND '
    else:
      pfilter = ''
    pfilter += f'maxAueDate>={maxAueDate}'
  if ous[0] is not None:
    showOrgUnit = True
  if csvPF and not FJQC.formatJSON:
    csvPF.AddTitles(CHROME_AUE_TITLES)
    if showOrgUnit:
      csvPF.AddTitle('orgUnitPath')
  for ou in ous:
    if ou is not None:
      ou = makeOrgUnitPathAbsolute(ou)
      _, orgUnitId = getOrgUnitId(cd, ou)
      ouList = [(ou, orgUnitId[3:])]
    else:
      ouList = [('/', None)]
    if not directlyInOU:
      try:
        orgs = callGAPI(cd.orgunits(), 'list',
                        throwReasons=GAPI.ORGUNIT_GET_THROW_REASONS,
                        customerId=GC.Values[GC.CUSTOMER_ID], orgUnitPath=makeOrgUnitPathRelative(ou),
                        type='all', fields='organizationUnits(orgUnitPath,orgUnitId)')
      except (GAPI.invalidOrgunit, GAPI.orgunitNotFound, GAPI.backendError, GAPI.badRequest, GAPI.invalidCustomerId, GAPI.loginRequired):
        checkEntityDNEorAccessErrorExit(cd, Ent.ORGANIZATIONAL_UNIT, ou)
        return
      ouList.extend([(subou['orgUnitPath'], subou['orgUnitId'][3:]) for subou in sorted(orgs.get('organizationUnits', []), key=lambda k: k['orgUnitPath'])])
    for subou in ouList:
      orgUnitPath, orgUnitId = _getPrintChromeGetting(subou, pfilter, Ent.CHROME_MODEL)
      try:
        aues = callGAPI(cm.customers().reports(), 'countChromeDevicesReachingAutoExpirationDate',
                        throwReasons=[GAPI.INVALID, GAPI.INVALID_ARGUMENT, GAPI.PERMISSION_DENIED, GAPI.SERVICE_NOT_AVAILABLE],
                        retryReasons=GAPI.SERVICE_NOT_AVAILABLE_RETRY_REASONS,
                        customer=customerId, orgUnitId=orgUnitId, minAueDate=minAueDate, maxAueDate=maxAueDate).get('deviceAueCountReports', [])
      except (GAPI.invalid, GAPI.invalidArgument, GAPI.permissionDenied, GAPI.serviceNotAvailable) as e:
        entityActionFailedWarning([Ent.CHROME_MODEL, None], str(e))
        return
      jcount = len(aues)
      if not csvPF:
        Ind.Increment()
        j = 0
        for aue in sorted(aues, key=lambda k: k.get('model', UNKNOWN)):
          j += 1
          aue['count'] = int(aue['count'])
          _showAue(aue, j, jcount)
        Ind.Decrement()
      else:
        for aue in sorted(aues, key=lambda k: k.get('model', UNKNOWN)):
          aue['count'] = int(aue['count'])
          _printAue(aue)
  if csvPF:
    csvPF.writeCSVfile('Chrome AUEs')

CHROME_NEEDSATTN_TITLES = ['noRecentPolicySyncCount', 'noRecentUserActivityCount', 'pendingUpdate',
                          'osVersionNotCompliantCount', 'unsupportedPolicyCount']

# gam print chromeneedsattn [todrive <ToDriveAttribute>*]
#	[(ou <OrgUnitItem>)|(ou_and_children <OrgUnitItem>)|
#	 (ous <OrgUnitList>)|(ous_and_children <OrgUnitList>)]
#	[formatjson [quotechar <Character>]]
# gam show chromeneedsattn
#	[(ou <OrgUnitItem>)|(ou_and_children <OrgUnitItem>)|
#	 (ous <OrgUnitList>)|(ous_and_children <OrgUnitList>)]
#	[formatjson]
def doPrintShowChromeNeedsAttn():
  def _printNeedsAttn(needsattn):
    if showOrgUnit:
      needsattn['orgUnitPath'] = orgUnitPath
    row = flattenJSON(needsattn)
    if not FJQC.formatJSON:
      csvPF.WriteRow(row)
    elif csvPF.CheckRowTitles(row):
      row = {'orgUnitPath': orgUnitPath} if showOrgUnit else {}
      row['JSON'] = json.dumps(cleanJSON(needsattn), ensure_ascii=False, sort_keys=True)
      csvPF.WriteRowNoFilter(row)

  def _showNeedsAttn(needsattn, i=0, count=0):
    if showOrgUnit:
      needsattn['orgUnitPath'] = orgUnitPath
    if FJQC.formatJSON:
      printLine(json.dumps(cleanJSON(needsattn), ensure_ascii=False, sort_keys=True))
      return
    if showOrgUnit:
      printEntity([Ent.ORGANIZATIONAL_UNIT, orgUnitPath], i, count)
    Ind.Increment()
    showJSON(None, needsattn)
    Ind.Decrement()

  cd = buildGAPIObject(API.DIRECTORY)
  cm = buildGAPIObject(API.CHROMEMANAGEMENT)
  customerId = _getMain()._getCustomersCustomerIdWithC()
  csvPF = CSVPrintFile([]) if Act.csvFormat() else None
  FJQC = FormatJSONQuoteChar(csvPF)
  ous = [None]
  directlyInOU = True
  showOrgUnit = False
  while Cmd.ArgumentsRemaining():
    myarg = getArgument()
    if csvPF and myarg == 'todrive':
      csvPF.GetTodriveParameters()
    elif myarg in _getMain().ORGUNIT_ENTITIES_MAP:
      myarg = _getMain().ORGUNIT_ENTITIES_MAP[myarg]
      ous = convertEntityToList(getString(Cmd.OB_ENTITY, minLen=0), shlexSplit=True, nonListEntityType=myarg in [Cmd.ENTITY_OU, Cmd.ENTITY_OU_AND_CHILDREN])
      directlyInOU = myarg in {Cmd.ENTITY_OU, Cmd.ENTITY_OUS}
    else:
      FJQC.GetFormatJSONQuoteChar(myarg, True)
  if ous[0] is not None:
    showOrgUnit = True
  if csvPF:
    if not FJQC.formatJSON:
      csvPF.AddTitles(CHROME_NEEDSATTN_TITLES)
      if showOrgUnit:
        csvPF.AddTitle('orgUnitPath')
    elif showOrgUnit:
      csvPF.SetJSONTitles(['orgUnitPath', 'JSON'])
  for ou in ous:
    if ou is not None:
      ou = makeOrgUnitPathAbsolute(ou)
      _, orgUnitId = getOrgUnitId(cd, ou)
      ouList = [(ou, orgUnitId[3:])]
    else:
      ouList = [('/', None)]
    if not directlyInOU:
      try:
        orgs = callGAPI(cd.orgunits(), 'list',
                        throwReasons=GAPI.ORGUNIT_GET_THROW_REASONS,
                        customerId=GC.Values[GC.CUSTOMER_ID], orgUnitPath=makeOrgUnitPathRelative(ou),
                        type='all', fields='organizationUnits(orgUnitPath,orgUnitId)')
      except (GAPI.invalidOrgunit, GAPI.orgunitNotFound, GAPI.backendError, GAPI.badRequest, GAPI.invalidCustomerId, GAPI.loginRequired):
        checkEntityDNEorAccessErrorExit(cd, Ent.ORGANIZATIONAL_UNIT, ou)
        return
      ouList.extend([(subou['orgUnitPath'], subou['orgUnitId'][3:]) for subou in sorted(orgs.get('organizationUnits', []), key=lambda k: k['orgUnitPath'])])
    count = len(ouList)
    i = 0
    for subou in ouList:
      i += 1
      orgUnitPath, orgUnitId = _getPrintChromeGetting(subou, None, Ent.CHROME_DEVICE)
      try:
        result = callGAPI(cm.customers().reports(), 'countChromeDevicesThatNeedAttention',
                          throwReasons=[GAPI.INVALID, GAPI.INVALID_ARGUMENT, GAPI.PERMISSION_DENIED, GAPI.SERVICE_NOT_AVAILABLE],
                          retryReasons=GAPI.SERVICE_NOT_AVAILABLE_RETRY_REASONS,
                          customer=customerId, orgUnitId=orgUnitId, readMask=','.join(CHROME_NEEDSATTN_TITLES))
        for k, v in result.items():
          result[k] = int(v)
        for field in CHROME_NEEDSATTN_TITLES:
          result.setdefault(field, 0)
      except (GAPI.invalid, GAPI.invalidArgument, GAPI.permissionDenied, GAPI.serviceNotAvailable) as e:
        entityActionFailedWarning([Ent.ORGANIZATIONAL_UNIT, orgUnitId], str(e))
        return
      if not csvPF:
        _showNeedsAttn(result, i, count)
      else:
        _printNeedsAttn(result)
  if csvPF:
    csvPF.writeCSVfile('Chrome Devices Needing Attention')

CHROME_DEVICE_COUNTS_MODE_CHOICES = ['all', 'active', 'perboottype', 'perreleasechannel']
CHROME_DEVICE_COUNTS_MODE_FUNCTIONS = {
  'all': ['countActiveDevices', 'countDevicesPerBootType', 'countDevicesPerReleaseChannel'],
  'active': ['countActiveDevices'],
  'perboottype': ['countDevicesPerBootType'],
  'perreleasechannel': ['countDevicesPerReleaseChannel']
  }
CHROME_DEVICE_COUNTS_MODE_CSV_TITLE = {
  'all': 'Chrome Device Counts',
  'active': 'Chrome Active Devices',
  'perboottype': 'Chrome Devices per Boot Type',
  'perreleasechannel': 'Chrome Devices per Release Channel'
  }

# gam print chromedevicecounts [todrive <ToDriveAttribute>*]
#	(mode all|active|perboottype|perreleasechannel)* [date <Date>]
#	[formatjson [quotechar <Character>]]
# gam show chromedevicecounts
#	(mode all|active|perboottype|perreleasechannel)* [date <Date>]
#	[formatjson]
def doPrintShowChromeDeviceCounts():
  cm = buildGAPIObject(API.CHROMEMANAGEMENT)
  customerId = _getMain()._getCustomersCustomerIdWithC()
  csvPF = CSVPrintFile(['date']) if Act.csvFormat() else None
  FJQC = FormatJSONQuoteChar(csvPF)
  pdate = todaysDate()
  functionList = []
  titleMode = 'all'
  while Cmd.ArgumentsRemaining():
    myarg = getArgument()
    if csvPF and myarg == 'todrive':
      csvPF.GetTodriveParameters()
    elif myarg == 'mode':
      mode = getChoice(CHROME_DEVICE_COUNTS_MODE_CHOICES)
      titleMode = mode if not functionList else 'all'
      functionList.extend(CHROME_DEVICE_COUNTS_MODE_FUNCTIONS[mode])
    elif myarg == 'date':
      pdate = getYYYYMMDD(returnDateTime=True)
    else:
      FJQC.GetFormatJSONQuoteChar(myarg, True)
  if not functionList:
    mode = titleMode = 'all'
    functionList = CHROME_DEVICE_COUNTS_MODE_FUNCTIONS[mode]
  pfdate = pdate.strftime(YYYYMMDD_FORMAT)
  kwargs = {'date_day': pdate.day, 'date_month': pdate.month, 'date_year': pdate.year}
  counts = {}
  titles = ['date']
  try:
    for function in functionList:
      result = callGAPI(cm.customers().reports(), function,
                        throwReasons=[GAPI.INVALID, GAPI.INVALID_ARGUMENT, GAPI.PERMISSION_DENIED, GAPI.SERVICE_NOT_AVAILABLE],
                        retryReasons=GAPI.SERVICE_NOT_AVAILABLE_RETRY_REASONS,
                        customer=customerId, **kwargs)
      counts.update(result)
      titles.extend(result.keys())
  except (GAPI.invalid, GAPI.invalidArgument, GAPI.permissionDenied, GAPI.serviceNotAvailable) as e:
    entityActionFailedWarning([Ent.CHROME_DEVICE_COUNT, None], str(e))
    return
  for k, v in counts.items():
    counts[k] = int(v)
  if not csvPF:
    if not FJQC.formatJSON:
      showJSON(f'{CHROME_DEVICE_COUNTS_MODE_CSV_TITLE[titleMode]} - {pfdate}', counts, sortDictKeys=False)
    else:
      printLine(json.dumps(counts, ensure_ascii=False, sort_keys=False))
  else:
    csvPF.SetTitles(titles)
    row = {'date': pfdate}
    flattenJSON(counts, flattened=row)
    if not FJQC.formatJSON:
      csvPF.WriteRow(row)
    elif csvPF.CheckRowTitles(row):
      csvPF.WriteRowNoFilter({'date': pfdate, 'JSON': json.dumps(counts, ensure_ascii=False, sort_keys=False)})
    csvPF.writeCSVfile(CHROME_DEVICE_COUNTS_MODE_CSV_TITLE[titleMode])

CHROME_VERSIONS_TITLES = ['channel', 'system', 'deviceOsVersion']

# gam print chromeversions [todrive <ToDriveAttribute>*]
#	[(ou <OrgUnitItem>)|(ou_and_children <OrgUnitItem>)|
#	 (ous <OrgUnitList>)|(ous_and_children <OrgUnitList>)]
#	[start <Date>] [end <Date>]
#	[recentfirst [<Boolean>]]
#	[formatjson [quotechar <Character>]]
# gam show chromeversions
#	[(ou <OrgUnitItem>)|(ou_and_children <OrgUnitItem>)|
#	 (ous <OrgUnitList>)|(ous_and_children <OrgUnitList>)]
#	[start <Date>] [end <Date>]
#	[recentfirst [<Boolean>]]
#	[formatjson]
def doPrintShowChromeVersions():
  def _getVersionKey(v):
    if 'version' not in v:
      return (0, 0, 0, 0)
    k = v['version'].split('.')
    for i, x in enumerate(k):
      k[i] = int(x)
    return tuple(k)

  def _printVersion(version):
    if showOrgUnit:
      version['orgUnitPath'] = orgUnitPath
    if 'version' not in version:
      version['version'] = UNKNOWN
    row = flattenJSON(version)
    if not FJQC.formatJSON:
      csvPF.WriteRow(row)
    elif csvPF.CheckRowTitles(row):
      csvPF.WriteRowNoFilter({'version': version['version'], 'count': version['count'],
                              'JSON': json.dumps(cleanJSON(version), ensure_ascii=False, sort_keys=True)})

  def _showVersion(version, i=0, count=0):
    if showOrgUnit:
      version['orgUnitPath'] = orgUnitPath
    if 'version' not in version:
      version['version'] = UNKNOWN
    if FJQC.formatJSON:
      printLine(json.dumps(cleanJSON(version), ensure_ascii=False, sort_keys=True))
      return
    printEntity([Ent.CHROME_VERSION, version['version']], i, count)
    Ind.Increment()
    showJSON(None, version)
    Ind.Decrement()

  cd = buildGAPIObject(API.DIRECTORY)
  cm = buildGAPIObject(API.CHROMEMANAGEMENT)
  customerId = _getMain()._getCustomersCustomerIdWithC()
  csvPF = CSVPrintFile(['version', 'count']) if Act.csvFormat() else None
  FJQC = FormatJSONQuoteChar(csvPF)
  ous = [None]
  directlyInOU = True
  reverse = showOrgUnit = False
  startDate = endDate = pfilter = None
  while Cmd.ArgumentsRemaining():
    myarg = getArgument()
    if csvPF and myarg == 'todrive':
      csvPF.GetTodriveParameters()
    elif myarg in _getMain().ORGUNIT_ENTITIES_MAP:
      myarg = _getMain().ORGUNIT_ENTITIES_MAP[myarg]
      ous = convertEntityToList(getString(Cmd.OB_ENTITY, minLen=0), shlexSplit=True, nonListEntityType=myarg in [Cmd.ENTITY_OU, Cmd.ENTITY_OU_AND_CHILDREN])
      directlyInOU = myarg in {Cmd.ENTITY_OU, Cmd.ENTITY_OUS}
    elif myarg in CROS_START_ARGUMENTS:
      startDate, _ = _getMain()._getFilterDateTime()
      startDate = startDate.strftime(YYYYMMDD_FORMAT)
    elif myarg in CROS_END_ARGUMENTS:
      endDate, _ = _getMain()._getFilterDateTime()
      endDate = endDate.strftime(YYYYMMDD_FORMAT)
    elif myarg == 'recentfirst':
      reverse = getBoolean()
    else:
      FJQC.GetFormatJSONQuoteChar(myarg, True)
  if endDate:
    pfilter = f'last_active_date<={endDate}'
  if startDate:
    if pfilter:
      pfilter += ' AND '
    else:
      pfilter = ''
    pfilter += f'last_active_date>={startDate}'
  if ous[0] is not None:
    showOrgUnit = True
  if csvPF and not FJQC.formatJSON:
    csvPF.AddTitles(CHROME_VERSIONS_TITLES)
    if showOrgUnit:
      csvPF.AddTitle('orgUnitPath')
  for ou in ous:
    if ou is not None:
      ou = makeOrgUnitPathAbsolute(ou)
      _, orgUnitId = getOrgUnitId(cd, ou)
      ouList = [(ou, orgUnitId[3:])]
    else:
      ouList = [('/', None)]
    if not directlyInOU:
      try:
        orgs = callGAPI(cd.orgunits(), 'list',
                        throwReasons=GAPI.ORGUNIT_GET_THROW_REASONS,
                        customerId=GC.Values[GC.CUSTOMER_ID], orgUnitPath=makeOrgUnitPathRelative(ou),
                        type='all', fields='organizationUnits(orgUnitPath,orgUnitId)')
      except (GAPI.invalidOrgunit, GAPI.orgunitNotFound, GAPI.backendError, GAPI.badRequest, GAPI.invalidCustomerId, GAPI.loginRequired):
        checkEntityDNEorAccessErrorExit(cd, Ent.ORGANIZATIONAL_UNIT, ou)
        return
      ouList.extend([(subou['orgUnitPath'], subou['orgUnitId'][3:]) for subou in sorted(orgs.get('organizationUnits', []), key=lambda k: k['orgUnitPath'])])
    for subou in ouList:
      orgUnitPath, orgUnitId = _getPrintChromeGetting(subou, pfilter, Ent.CHROME_VERSION)
      pageMessage = getPageMessage()
      try:
        versions = callGAPIpages(cm.customers().reports(), 'countChromeVersions', 'browserVersions',
                                 throwReasons=[GAPI.INVALID, GAPI.INVALID_ARGUMENT, GAPI.PERMISSION_DENIED, GAPI.SERVICE_NOT_AVAILABLE],
                                 retryReasons=GAPI.SERVICE_NOT_AVAILABLE_RETRY_REASONS,
                                 pageMessage=pageMessage,
                                 customer=customerId, orgUnitId=orgUnitId, filter=pfilter)
      except (GAPI.invalid, GAPI.invalidArgument, GAPI.permissionDenied, GAPI.serviceNotAvailable) as e:
        entityActionFailedWarning([Ent.CHROME_VERSION, None], str(e))
        return
      if not csvPF:
        jcount = len(versions)
        if not FJQC.formatJSON:
          entityPerformActionNumItems([Ent.ORGANIZATIONAL_UNIT, orgUnitPath], jcount, Ent.CHROME_VERSION)
        Ind.Increment()
        j = 0
        for version in sorted(versions, key=_getVersionKey, reverse=reverse):
          j += 1
          version['count'] = int(version['count'])
          _showVersion(version, j, jcount)
        Ind.Decrement()
      else:
        for version in sorted(versions, key=_getVersionKey, reverse=reverse):
          version['count'] = int(version['count'])
          _printVersion(version)
  if csvPF:
    csvPF.writeCSVfile('Chrome Versions')

def getPlatformChannelMap(cv, entityType):
  if cv is None:
    cv = buildGAPIObjectNoAuthentication(API.CHROMEVERSIONHISTORY)
  if entityType == Ent.CHROME_PLATFORM:
    svc = cv.platforms()
    parent = 'chrome'
    field = 'platformType'
  else: # elif entityType == Ent.CHROME_CHANNEL:
    svc = cv.platforms().channels()
    parent = 'chrome/platforms/all'
    field = 'channelType'
  try:
    pcitems = callGAPIpages(svc, 'list', CHROME_VERSIONHISTORY_ITEMS[entityType],
                            throwReasons=[GAPI.INVALID, GAPI.INVALID_ARGUMENT, GAPI.PERMISSION_DENIED],
                            parent=parent, fields=f'nextPageToken,{CHROME_VERSIONHISTORY_ITEMS[entityType]}')
    pcMap = {'all': 'all'}
    for pcitem in pcitems:
      pcType = pcitem[field].lower()
      pcMap[pcType.replace('_', '')] = pcType
  except (GAPI.invalid, GAPI.invalidArgument, GAPI.permissionDenied) as e:
    entityActionFailedWarning([entityType, None], str(e))
    pcMap = {}
  return (cv, pcMap)

def getRelativeMilestone(cv, channel, minus):
  ''' takes a channel and minus_versions like stable and -1. returns current given  milestone number '''
  if cv is None:
    cv = buildGAPIObjectNoAuthentication(API.CHROMEVERSIONHISTORY)
  try:
    releases = callGAPIpages(cv.platforms().channels().versions().releases(), 'list', 'releases',
                             throwReasons=[GAPI.INVALID, GAPI.INVALID_ARGUMENT, GAPI.PERMISSION_DENIED],
                             parent=f'chrome/platforms/all/channels/{channel}/versions/all',
                             fields='nextPageToken,releases(version)')
  except (GAPI.invalid, GAPI.invalidArgument, GAPI.permissionDenied) as e:
    entityActionFailedWarning([Ent.CHROME_RELEASE, None], str(e))
    return (cv, False, str(e))
  milestones = []
  # Note that milestones are usually sequential but some numbers
  # may be skipped. For example, there was no Chrome 82 stable.
  # Thus we need to do more than find the latest version and subtract.
  for release in releases:
    if 'version' in release:
      milestone = int(release['version'].split('.')[0])
      if milestone not in milestones:
        milestones.append(int(milestone))
  milestones.sort(reverse=True)
  try:
    return (cv, True, str(milestones[minus]))
  except IndexError:
    return (cv, False, f'{channel}-{0}:{channel}-{len(milestones)-1}')

CHROME_HISTORY_ENTITY_CHOICE_MAP = {
  'platforms': Ent.CHROME_PLATFORM,
  'channels': Ent.CHROME_CHANNEL,
  'versions': Ent.CHROME_VERSION,
  'releases': Ent.CHROME_RELEASE,
  }
CHROME_VERSIONHISTORY_ORDERBY_CHOICE_MAP = {
  Ent.CHROME_VERSION:  {
    'channel': 'channel',
    'name': 'name',
    'platform': 'platform',
    'version': 'version'
    },
  Ent.CHROME_RELEASE: {
    'channel': 'channel',
    'endtime': 'endtime',
    'fraction': 'fraction',
    'name': 'name',
    'platform': 'platform',
    'starttime': 'starttime',
    'version': 'version'
    }
  }
CHROME_VERSIONHISTORY_TITLES = {
  Ent.CHROME_PLATFORM: ['platform'],
  Ent.CHROME_CHANNEL:  ['channel', 'platform'],
  Ent.CHROME_VERSION: ['version', 'channel', 'platform',
                       'major_version', 'minor_version', 'build', 'patch'],
  Ent.CHROME_RELEASE: ['version', 'channel', 'platform',
                       'major_version', 'minor_version', 'build', 'patch',
                       'fraction', 'fractionGroup', 'serving.startTime',
                       'serving.endTime', 'pinnable']

  }
CHROME_VERSIONHISTORY_ITEMS = {
  Ent.CHROME_PLATFORM: 'platforms',
  Ent.CHROME_CHANNEL: 'channels',
  Ent.CHROME_VERSION: 'versions',
  Ent.CHROME_RELEASE: 'releases'
  }
CHROME_VERSIONHISTORY_TIMEOBJECTS = {
  Ent.CHROME_PLATFORM: None,
  Ent.CHROME_CHANNEL:  None,
  Ent.CHROME_VERSION: None,
  Ent.CHROME_RELEASE: ['startTime', 'endTime']
  }

# gam print chromehistory platforms [todrive <ToDriveAttribute>*]
#	[formatjson [quotechar <Character>]]
# gam show chromehistory platforms
#	[formatjson]

# gam print chromehistory channels [todrive <ToDriveAttribute>*]
#	[platform <ChromePlatformType>]
#	[formatjson [quotechar <Character>]]
# gam show chromehistory channels
#	[platform <ChromePlatformType>]
#	[formatjson]

# gam print chromehistory versions [todrive <ToDriveAttribute>*]
#	[platform <ChromePlatformType>] [channel <ChromeChannelType>]
#	(orderby <ChromeVersionsOrderByFieldName> [ascending|descending])*
#	[filter <String>]
#	[formatjson [quotechar <Character>]]
# gam show chromehistory versions
#	[platform <ChromePlatformType>] [channel <ChromeChannelType>]
#	(orderby <ChromeVersionsOrderByFieldName> [ascending|descending])*
#	[filter <String>]
#	[formatjson]

# gam print chromehistory releases [todrive <ToDriveAttribute>*]
#	[platform <ChromePlatformType>] [channel <ChromeChannelType>] [version <String>]
#	(orderby <ChromeReleasessOrderByFieldName> [ascending|descending])*
#	[filter <String>]
#	[formatjson [quotechar <Character>]]
# gam show chromehistory releases
#	[platform <ChromePlatformType>] [channel <ChromeChannelType>] [version <String>]
#	(orderby <ChromeReleasessOrderByFieldName> [ascending|descending])*
#	[filter <String>]
#	[formatjson]

def doPrintShowChromeHistory():
  def addDetailFields(citem):
    for key in list(citem):
      if key.endswith('Type'):
        citem[key[:-4]] = citem.pop(key)
    if 'channel' in citem:
      citem['channel'] = citem['channel'].lower()
    else:
      channel_match = re.search(r"\/channels\/([^/]*)", citem['name'])
      if channel_match:
        try:
          citem['channel'] = channel_match.group(1)
        except IndexError:
          pass
    if 'platform' in citem:
      citem['platform'] = citem['platform'].lower()
    else:
      platform_match = re.search(r"\/platforms\/([^/]*)", citem['name'])
      if platform_match:
        try:
          citem['platform'] = platform_match.group(1)
        except IndexError:
          pass
    if citem.get('version', '').count('.') == 3:
      citem['major_version'], citem['minor_version'], citem['build'], citem['patch'] = citem['version'].split('.')
    citem.pop('name')

  def _printItem(citem):
    addDetailFields(citem)
    row = flattenJSON(citem, timeObjects=CHROME_VERSIONHISTORY_TIMEOBJECTS[entityType])
    if not FJQC.formatJSON:
      csvPF.WriteRow(row)
    elif csvPF.CheckRowTitles(row):
      keyField = CHROME_VERSIONHISTORY_TITLES[entityType][0]
      csvPF.WriteRowNoFilter({keyField: citem[keyField],
                              'JSON': json.dumps(cleanJSON(citem), ensure_ascii=False, sort_keys=True)})

  def _showItem(citem, i=0, count=0):
    addDetailFields(citem)
    keyField = CHROME_VERSIONHISTORY_TITLES[entityType][0]
    if FJQC.formatJSON:
      printLine(json.dumps(cleanJSON(citem), ensure_ascii=False, sort_keys=True))
      return
    printEntity([entityType, citem[keyField]], i, count)
    Ind.Increment()
    citem = flattenJSON(citem, timeObjects=CHROME_VERSIONHISTORY_TIMEOBJECTS[entityType])
    for field in CHROME_VERSIONHISTORY_TITLES[entityType]:
      if field in citem:
        printKeyValueList([field, citem[field]])
    Ind.Decrement()

  cv = buildGAPIObjectNoAuthentication(API.CHROMEVERSIONHISTORY)
  entityType = getChoice(CHROME_HISTORY_ENTITY_CHOICE_MAP, mapChoice=True)
  csvPF = CSVPrintFile(CHROME_VERSIONHISTORY_TITLES[entityType][0:1]) if Act.csvFormat() else None
  FJQC = FormatJSONQuoteChar(csvPF)
  platformMap = None
  channelMap = None
  cplatform = 'all'
  channel = 'all'
  version = 'all'
  kwargs = {}
  if entityType in {Ent.CHROME_VERSION, Ent.CHROME_RELEASE}:
    OBY = OrderBy(CHROME_VERSIONHISTORY_ORDERBY_CHOICE_MAP[entityType])
  while Cmd.ArgumentsRemaining():
    myarg = getArgument()
    if csvPF and myarg == 'todrive':
      csvPF.GetTodriveParameters()
    elif entityType != Ent.CHROME_PLATFORM and myarg == 'platform':
      if platformMap is None:
        _, platformMap = getPlatformChannelMap(cv, Ent.CHROME_PLATFORM)
      cplatform = getChoice(platformMap, mapChoice=True)
    elif entityType in {Ent.CHROME_VERSION, Ent.CHROME_RELEASE} and myarg == 'channel':
      if channelMap is None:
        _, channelMap = getPlatformChannelMap(cv, Ent.CHROME_CHANNEL)
      channel = getChoice(channelMap, mapChoice=True)
    elif entityType == Ent.CHROME_RELEASE and myarg == 'version':
      version = getString(Cmd.OB_CHROME_VERSION)
    elif entityType in {Ent.CHROME_VERSION, Ent.CHROME_RELEASE} and myarg == 'orderby':
      OBY.GetChoice()
    elif entityType in {Ent.CHROME_VERSION, Ent.CHROME_RELEASE} and myarg == 'filter':
      kwargs['filter'] = getString(Cmd.OB_STRING)
    else:
      FJQC.GetFormatJSONQuoteChar(myarg, True)
  if csvPF and not FJQC.formatJSON:
    csvPF.AddTitles(CHROME_VERSIONHISTORY_TITLES[entityType][1:])
  if entityType == Ent.CHROME_PLATFORM:
    svc = cv.platforms()
    parent = 'chrome'
  elif entityType == Ent.CHROME_CHANNEL:
    svc = cv.platforms().channels()
    parent = f'chrome/platforms/{cplatform}'
  elif entityType == Ent.CHROME_VERSION:
    svc = cv.platforms().channels().versions()
    parent = f'chrome/platforms/{cplatform}/channels/{channel}'
    kwargs['orderBy'] = OBY.orderBy
  else: #elif entityType == Ent.CHROME_RELEASE
    svc = cv.platforms().channels().versions().releases()
    parent = f'chrome/platforms/{cplatform}/channels/{channel}/versions/{version}'
    kwargs['orderBy'] = OBY.orderBy
  printGettingAllAccountEntities(entityType)
  pageMessage = getPageMessage()
  try:
    citems = callGAPIpages(svc, 'list', CHROME_VERSIONHISTORY_ITEMS[entityType],
                           throwReasons=[GAPI.INVALID, GAPI.INVALID_ARGUMENT, GAPI.PERMISSION_DENIED],
                           pageMessage=pageMessage,
                           parent=parent, fields=f'nextPageToken,{CHROME_VERSIONHISTORY_ITEMS[entityType]}',
                           **kwargs)
  except (GAPI.invalid, GAPI.invalidArgument, GAPI.permissionDenied) as e:
    entityActionFailedWarning([entityType, None], str(e))
    return
  if not csvPF:
    jcount = len(citems)
    if not FJQC.formatJSON:
      performActionNumItems(jcount, entityType)
    j = 0
    for citem in citems:
      j += 1
      _showItem(citem, j, jcount)
  else:
    for citem in citems:
      _printItem(citem)
  if csvPF:
    csvPF.writeCSVfile(Ent.Plural(entityType))

# gam print chromesnvalidity [todrive <ToDriveAttribute>*]
#	cros_sn <SerialNumberEntity> [listlimit <Number>]
#	[delimiter <Character>]
def doPrintChromeSnValidity():
  cd = buildGAPIObject(API.DIRECTORY)
  csvPF = CSVPrintFile(['serialNumber', 'exactMatches', 'exactMatchDeviceIds', 'prefixMatches', 'prefixMatchDeviceIds'])
  delimiter = GC.Values[GC.CSV_OUTPUT_FIELD_DELIMITER]
  serialNumberList = []
  listLimit = 0
  while Cmd.ArgumentsRemaining():
    myarg = getArgument()
    if csvPF and myarg == 'todrive':
      csvPF.GetTodriveParameters()
    elif myarg == 'crossn':
      serialNumberList = getEntityList(Cmd.OB_STRING_LIST)
    elif myarg == 'listlimit':
      listLimit = getInteger(minVal=0)
    elif myarg == 'delimiter':
      delimiter = getCharacter()
    else:
      unknownArgumentExit()
  if not serialNumberList:
    actionNotPerformedNumItemsWarning(0, Ent.CROS_SERIAL_NUMBER, Msg.NO_SERIAL_NUMBERS_SPECIFIED)
    return
  for serialNumber in serialNumberList:
    query = f'id:{serialNumber}'
    printGettingAllAccountEntities(Ent.CROS_DEVICE, query)
    try:
      devices = callGAPIpages(cd.chromeosdevices(), 'list', 'chromeosdevices',
                              pageMessage=getPageMessage(),
                              throwReasons=[GAPI.INVALID_INPUT, GAPI.BAD_REQUEST, GAPI.RESOURCE_NOT_FOUND, GAPI.FORBIDDEN],
                              retryReasons=GAPI.SERVICE_NOT_AVAILABLE_RETRY_REASONS,
                              customerId=GC.Values[GC.CUSTOMER_ID],
                              query=query, fields='nextPageToken,chromeosdevices(deviceId,serialNumber)',
                              orderBy='serialNumber', maxResults=GC.Values[GC.DEVICE_MAX_RESULTS])
    except (GAPI.invalidInput, GAPI.badRequest, GAPI.resourceNotFound, GAPI.forbidden):
      accessErrorExit(cd)
    exactMatches = prefixMatches = 0
    exactMatchDeviceIds = []
    prefixMatchDeviceIds = []
    serialNumberLower = serialNumber.lower()
    for device in devices:
      if device['serialNumber'].lower() == serialNumberLower:
        exactMatches += 1
        if not listLimit or exactMatches <= listLimit:
          exactMatchDeviceIds.append(device['deviceId'])
      else:
        prefixMatches += 1
        if not listLimit or prefixMatches <= listLimit:
          prefixMatchDeviceIds.append(device['deviceId'])
    row = {'serialNumber': serialNumber,
           'exactMatches': exactMatches,
           'exactMatchDeviceIds': delimiter.join(exactMatchDeviceIds),
           'prefixMatches': prefixMatches,
           'prefixMatchDeviceIds': delimiter.join(prefixMatchDeviceIds)}
    csvPF.WriteRow(row)
  if csvPF:
    csvPF.writeCSVfile('Chrome Serial Number Validity')

# Mobile command utilities
MOBILE_ACTION_CHOICE_MAP = {
  'accountwipe': 'admin_account_wipe',
  'adminaccountwipe': 'admin_account_wipe',
  'wipeaccount': 'admin_account_wipe',
  'adminremotewipe': 'admin_remote_wipe',
  'wipe': 'admin_remote_wipe',
  'approve': 'approve',
  'block': 'block',
  'cancelremotewipethenactivate': 'cancel_remote_wipe_then_activate',
  'cancelremotewipethenblock': 'cancel_remote_wipe_then_block',
  }

