"""GAM usage reports and activity reports."""

import arrow

import datetime
import re

from gamlib import api as API
from gamlib import settings as GC
from gamlib import gapi as GAPI
from gamlib import state as GM
from gamlib import msgs as Msg
from gam.var import Act, Cmd, Ent, Ind
from gam.util.access import accessErrorExit, entityUnknownWarning
from gam.util.api import _getAdminEmail, buildGAPIObject
from gam.util.api_call import callGAPI, callGAPIpages
from gam.util.args import (
    DELTA_DATE_FORMAT_REQUIRED,
    DELTA_DATE_PATTERN,
    PLUS_MINUS,
    StartEndTime,
    TODAY_NOW,
    YYYYMMDDTHHMMSSZ_FORMAT,
    YYYYMMDD_FORMAT,
    YYYYMMDD_FORMAT_REQUIRED,
    escapeCRsNLs,
    formatLocalTime,
    getAddCSVData,
    getArgument,
    getBoolean,
    getChoice,
    getDelta,
    getEmailAddress,
    getInteger,
    getNumberRangeList,
    getString,
    getTimeOrDeltaFromNow,
    normalizeEmailAddressOrUID,
    orgUnitPathQuery,
    todaysDate,
)
from gam.util.output import ISOformatTimeStamp
from gam.util.csv_pf import CSVPrintFile, flattenJSON, getTodriveOnly
from gam.util.display import (
    BAD_REQUEST_RC,
    getPageMessage,
    getPageMessageForWhom,
    printEntity,
    printGettingAllEntityItemsForWhom,
    printGettingEntityItemForWhom,
)
from gam.util.entity import getEntityToModify
from gam.util.errors import invalidArgumentExit, invalidChoiceExit, unknownArgumentExit, usageErrorExit
from gam.util.fileio import UNKNOWN
from gam.util.orgunits import getOrgUnitId
from gam.util.output import (
    printErrorMessage,
    printWarningMessage,
    setSysExitRC,
    stderrWarningMsg,
    systemErrorExit,
)
from gam.constants import DATA_NOT_AVALIABLE_RC, DAYS_OF_WEEK, ENTITY_IS_AN_UNMANAGED_ACCOUNT_RC, ENTITY_IS_A_GROUP_ALIAS_RC, ENTITY_IS_A_GROUP_RC, ENTITY_IS_A_USER_ALIAS_RC, ENTITY_IS_A_USER_RC, ENTITY_IS_UKNOWN_RC, GOOGLE_API_ERROR_RC
from gam.cmd.aliases import infoAliases
from gam.cmd.ciuserinvitations import _getCIUserInvitationsEntity, _getIsInvitableUser, infoCIUserInvitations
from gam.cmd.groups.members import infoGroups
from gam.cmd.users.display import infoUsers


def doWhatIs():
  def _showPrimaryType(entityType, email):
    printEntity([entityType, email])

  def _showAliasType(entityType, email, primaryEntityType, primaryEmail):
    printEntity([entityType, email, primaryEntityType, primaryEmail])

  cd = buildGAPIObject(API.DIRECTORY)
  email = getEmailAddress()
  showInfo = invitableCheck = True
  while Cmd.ArgumentsRemaining():
    myarg = getArgument()
    if myarg == 'noinfo':
      showInfo = False
    elif myarg == 'noinvitablecheck':
      invitableCheck = False
    else:
      unknownArgumentExit()
  try:
    result = callGAPI(cd.users(), 'get',
                      throwReasons=GAPI.USER_GET_THROW_REASONS,
                      userKey=email, fields='id,primaryEmail')
    if (result['primaryEmail'].lower() == email) or (result['id'] == email):
      if showInfo:
        infoUsers(entityList=[email])
      else:
        _showPrimaryType(Ent.USER, email)
      setSysExitRC(ENTITY_IS_A_USER_RC)
    else:
      if showInfo:
        infoAliases(entityList=[email])
      else:
        _showAliasType(Ent.USER_ALIAS, email, Ent.USER, result['primaryEmail'])
      setSysExitRC(ENTITY_IS_A_USER_ALIAS_RC)
    return
  except (GAPI.userNotFound, GAPI.badRequest):
    pass
  except (GAPI.domainNotFound, GAPI.domainCannotUseApis, GAPI.forbidden,
          GAPI.backendError, GAPI.systemError):
    entityUnknownWarning(Ent.EMAIL, email)
    setSysExitRC(ENTITY_IS_UKNOWN_RC)
    return
  try:
    result = callGAPI(cd.groups(), 'get',
                      throwReasons=GAPI.GROUP_GET_THROW_REASONS,
                      groupKey=email, fields='id,email')
    if (result['email'].lower() == email) or (result['id'] == email):
      if showInfo:
        infoGroups([email])
      else:
        _showPrimaryType(Ent.GROUP, email)
      setSysExitRC(ENTITY_IS_A_GROUP_RC)
    else:
      if showInfo:
        infoAliases(entityList=[email])
      else:
        _showAliasType(Ent.GROUP_ALIAS, email, Ent.GROUP, result['email'])
      setSysExitRC(ENTITY_IS_A_GROUP_ALIAS_RC)
    return
  except (GAPI.groupNotFound, GAPI.forbidden):
    pass
  except (GAPI.domainNotFound, GAPI.domainCannotUseApis, GAPI.badRequest):
    entityUnknownWarning(Ent.EMAIL, email)
    setSysExitRC(ENTITY_IS_UKNOWN_RC)
    return
  if not invitableCheck:
    isInvitableUser = False
    ci = None
  else:
    isInvitableUser, ci = _getIsInvitableUser(None, email)
  if isInvitableUser:
    if showInfo:
      name, user, ci = _getCIUserInvitationsEntity(ci, email)
      infoCIUserInvitations(name, user, ci, None)
    else:
      _showPrimaryType(Ent.USER_INVITATION, email)
    setSysExitRC(ENTITY_IS_AN_UNMANAGED_ACCOUNT_RC)
  else:
    entityUnknownWarning(Ent.EMAIL, email)
    setSysExitRC(ENTITY_IS_UKNOWN_RC)

def _adjustTryDate(errMsg, numDateChanges, limitDateChanges, prevTryDate):
  match_date = re.match('Data for dates later than (.*) is not yet available. Please check back later', errMsg)
  if match_date:
    tryDate = match_date.group(1)
  else:
    match_date = re.match('Start date can not be later than (.*)', errMsg)
    if match_date:
      tryDate = match_date.group(1)
    else:
      match_date = re.match('End date greater than LastReportedDate.', errMsg)
      if match_date:
        tryDateTime = arrow.Arrow.strptime(prevTryDate, YYYYMMDD_FORMAT).shift(days=-1)
        tryDate = tryDateTime.strftime(YYYYMMDD_FORMAT)
  if (not match_date) or (numDateChanges > limitDateChanges >= 0):
    printWarningMessage(DATA_NOT_AVALIABLE_RC, errMsg)
    return None
  return tryDate

def _checkDataRequiredServices(result, tryDate, dataRequiredServices, parameterServices=None, checkUserEmail=False):
# -1: Data not available:
#  0: Backup to earlier date
#  1: Data available
  dataWarnings = result.get('warnings', [])
  usageReports = result.get('usageReports', [])
  # move to day before if we don't have at least one usageReport with parameters
  if not usageReports or not usageReports[0].get('parameters', []):
    tryDateTime = arrow.Arrow.strptime(tryDate, YYYYMMDD_FORMAT).shift(days=-1)
    return (0, tryDateTime.strftime(YYYYMMDD_FORMAT), None)
  for warning in dataWarnings:
    if warning['code'] == 'PARTIAL_DATA_AVAILABLE':
      for app in warning['data']:
        if app['key'] == 'application' and app['value'] != 'docs' and app['value'] in dataRequiredServices:
          tryDateTime = arrow.Arrow.strptime(tryDate, YYYYMMDD_FORMAT).shift(days=-1)
          return (0, tryDateTime.strftime(YYYYMMDD_FORMAT), None)
    elif warning['code'] == 'DATA_NOT_AVAILABLE':
      for app in warning['data']:
        if app['key'] == 'application' and app['value'] != 'docs' and app['value'] in dataRequiredServices:
          return (-1, tryDate, None)
  if parameterServices:
    requiredServices = parameterServices.copy()
    for item in usageReports[0].get('parameters', []):
      if 'name' not in item:
        continue
      service, _ = item['name'].split(':', 1)
      if service in requiredServices:
        requiredServices.remove(service)
        if not requiredServices:
          break
    else:
      tryDateTime = arrow.Arrow.strptime(tryDate, YYYYMMDD_FORMAT).shift(days=-1)
      return (0, tryDateTime.strftime(YYYYMMDD_FORMAT), None)
  if checkUserEmail:
    if 'entity' not in usageReports[0] or 'userEmail' not in usageReports[0]['entity']:
      tryDateTime = arrow.Arrow.strptime(tryDate, YYYYMMDD_FORMAT).shift(days=-1)
      return (0, tryDateTime.strftime(YYYYMMDD_FORMAT), None)
  return (1, tryDate, usageReports)

CUSTOMER_REPORT_SERVICES = {
  'accounts',
  'app_maker',
  'apps_scripts',
  'calendar',
  'chat',
  'classroom',
  'cros',
  'device_management',
  'docs',
  'drive',
  'gmail',
  'gplus',
  'meet',
  'sites',
  }

USER_REPORT_SERVICES = {
  'accounts',
  'chat',
  'classroom',
  'docs',
  'drive',
  'gmail',
  'gplus',
  }

CUSTOMER_USER_CHOICES = {'customer', 'user'}

# gam report usageparameters customer|user [todrive <ToDriveAttribute>*]
def doReportUsageParameters():
  report = getChoice(CUSTOMER_USER_CHOICES)
  csvPF = CSVPrintFile(['parameter'], 'sortall')
  getTodriveOnly(csvPF)
  rep = buildGAPIObject(API.REPORTS)
  if report == 'customer':
    service = rep.customerUsageReports()
    dataRequiredServices = CUSTOMER_REPORT_SERVICES
    kwargs = {}
  else: # 'user'
    service = rep.userUsageReport()
    dataRequiredServices = USER_REPORT_SERVICES
    kwargs = {'userKey': _getAdminEmail()}
  customerId = GC.Values[GC.CUSTOMER_ID]
  if customerId == GC.MY_CUSTOMER:
    customerId = None
  tryDate = todaysDate().strftime(YYYYMMDD_FORMAT)
  allParameters = set()
  while True:
    try:
      result = callGAPI(service, 'get',
                        throwReasons=[GAPI.INVALID, GAPI.BAD_REQUEST],
                        date=tryDate, customerId=customerId, fields='warnings,usageReports(parameters(name))', **kwargs)
      fullData, tryDate, usageReports = _checkDataRequiredServices(result, tryDate, dataRequiredServices)
      if fullData < 0:
        printWarningMessage(DATA_NOT_AVALIABLE_RC, Msg.NO_USAGE_PARAMETERS_DATA_AVAILABLE)
        return
      if usageReports:
        for parameter in usageReports[0]['parameters']:
          name = parameter.get('name')
          if name:
            allParameters.add(name)
      if fullData == 1:
        break
    except GAPI.badRequest:
      printErrorMessage(BAD_REQUEST_RC, Msg.BAD_REQUEST)
      return
    except GAPI.invalid as e:
      tryDate = _adjustTryDate(str(e), 0, -1, tryDate)
      if not tryDate:
        break
  for parameter in sorted(allParameters):
    csvPF.WriteRow({'parameter': parameter})
  csvPF.writeCSVfile(f'{report.capitalize()} Report Usage Parameters')

def getUserOrgUnits(cd, orgUnit, orgUnitId):
  try:
    if orgUnit == orgUnitId:
      orgUnit = callGAPI(cd.orgunits(), 'get',
                         throwReasons=GAPI.ORGUNIT_GET_THROW_REASONS,
                         customerId=GC.Values[GC.CUSTOMER_ID], orgUnitPath=orgUnit, fields='orgUnitPath')['orgUnitPath']
    printGettingAllEntityItemsForWhom(Ent.USER, orgUnit, qualifier=Msg.IN_THE.format(Ent.Singular(Ent.ORGANIZATIONAL_UNIT)),
                                      entityType=Ent.ORGANIZATIONAL_UNIT)
    result = callGAPIpages(cd.users(), 'list', 'users',
                           pageMessage=getPageMessageForWhom(),
                           throwReasons=[GAPI.INVALID_ORGUNIT, GAPI.ORGUNIT_NOT_FOUND,
                                         GAPI.INVALID_INPUT, GAPI.BAD_REQUEST, GAPI.RESOURCE_NOT_FOUND, GAPI.FORBIDDEN],
                           retryReasons=GAPI.SERVICE_NOT_AVAILABLE_RETRY_REASONS,
                           customer=GC.Values[GC.CUSTOMER_ID], query=orgUnitPathQuery(orgUnit, None, None), orderBy='email',
                           fields='nextPageToken,users(primaryEmail,orgUnitPath)', maxResults=GC.Values[GC.USER_MAX_RESULTS])
    userOrgUnits = {}
    for user in result:
      userOrgUnits[user['primaryEmail']] = user['orgUnitPath']
    return userOrgUnits
  except (GAPI.badRequest, GAPI.invalidInput, GAPI.invalidOrgunit, GAPI.orgunitNotFound, GAPI.backendError,
          GAPI.invalidCustomerId, GAPI.loginRequired, GAPI.resourceNotFound, GAPI.forbidden):
    checkEntityDNEorAccessErrorExit(cd, Ent.ORGANIZATIONAL_UNIT, orgUnit)

# Convert report mb item to gb
def convertReportMBtoGB(name, item):
  if item is not None:
    item['intValue'] = f"{int(item['intValue'])/1024:.2f}"
  return name.replace('_in_mb', '_in_gb')

REPORTS_PARAMETERS_SIMPLE_TYPES = ['intValue', 'boolValue', 'datetimeValue', 'stringValue']

# gam report usage user [todrive <ToDriveAttribute>*]
#	[(user all|<UserItem>)|(orgunit|org|ou <OrgUnitPath> [showorgunit])|(select <UserTypeEntity>)]
#	[([start|startdate <Date>] [end|enddate <Date>])|(range <Date> <Date>)|
#	 thismonth|(previousmonths <Integer>)]
#	[skipdates <Date>[:<Date>](,<Date>[:<Date>])*] [skipdaysofweek <DayOfWeek>(,<DayOfWeek>)*]
#	[fields|parameters <String>)]
#	[convertmbtogb]
#	(addcsvdata <FieldName> <String>)*
# gam report usage customer [todrive <ToDriveAttribute>*]
#	[([start|startdate <Date>] [end|enddate <Date>])|(range <Date> <Date>)|
#	 thismonth|(previousmonths <Integer>)]
#	[skipdates <Date>[:<Date>](,<Date>[:<Date>])*] [skipdaysofweek <DayOfWeek>(,<DayOfWeek>)*]
#	[fields|parameters <String>)]
#	[convertmbtogb]
#	(addcsvdata <FieldName> <String>)*
def doReportUsage():
  def usageEntitySelectors():
    selectorChoices = Cmd.USER_ENTITY_SELECTORS+Cmd.USER_CSVDATA_ENTITY_SELECTORS
    if GC.Values[GC.USER_SERVICE_ACCOUNT_ACCESS_ONLY]:
      selectorChoices += Cmd.SERVICE_ACCOUNT_ONLY_ENTITY_SELECTORS[:]+[Cmd.ENTITY_USER, Cmd.ENTITY_USERS]
    else:
      selectorChoices += Cmd.BASE_ENTITY_SELECTORS[:]+Cmd.USER_ENTITIES[:]
    return selectorChoices

  def validateYYYYMMDD(argstr):
    if argstr in TODAY_NOW or argstr[0] in PLUS_MINUS:
      if argstr == 'NOW':
        argstr = 'TODAY'
      deltaDate = getDelta(argstr, DELTA_DATE_PATTERN)
      if deltaDate is None:
        Cmd.Backup()
        invalidArgumentExit(DELTA_DATE_FORMAT_REQUIRED)
      return deltaDate
    try:
      argDate = arrow.Arrow.strptime(argstr, YYYYMMDD_FORMAT)
      return arrow.Arrow(argDate.year, argDate.month, argDate.day, tzinfo=GC.Values[GC.TIMEZONE])
    except ValueError:
      Cmd.Backup()
      invalidArgumentExit(YYYYMMDD_FORMAT_REQUIRED)

  report = getChoice(CUSTOMER_USER_CHOICES)
  rep = buildGAPIObject(API.REPORTS)
  titles = ['date']
  if report == 'customer':
    fullDataServices = CUSTOMER_REPORT_SERVICES
    userReports = False
    service = rep.customerUsageReports()
    kwargs = [{}]
  else: # 'user'
    fullDataServices = USER_REPORT_SERVICES
    userReports = True
    service = rep.userUsageReport()
    kwargs = [{'userKey': 'all'}]
    titles.append('user')
  csvPF = CSVPrintFile()
  customerId = GC.Values[GC.CUSTOMER_ID]
  if customerId == GC.MY_CUSTOMER:
    customerId = None
  parameters = set()
  convertMbToGb = select = showOrgUnit = False
  userKey = 'all'
  cd = orgUnit = orgUnitId = None
  userOrgUnits = {}
  startEndTime = StartEndTime('startdate', 'enddate', 'date')
  skipDayNumbers = []
  skipDates = set()
  addCSVData = {}
  while Cmd.ArgumentsRemaining():
    myarg = getArgument()
    if csvPF and myarg == 'todrive':
      csvPF.GetTodriveParameters()
    elif myarg in {'start', 'startdate', 'end', 'enddate', 'range', 'thismonth', 'previousmonths'}:
      startEndTime.Get(myarg)
    elif userReports and myarg in {'ou', 'org', 'orgunit'}:
      if cd is None:
        cd = buildGAPIObject(API.DIRECTORY)
      orgUnit, orgUnitId = getOrgUnitId(cd)
      select = False
    elif userReports and myarg == 'showorgunit':
      showOrgUnit = True
    elif myarg in {'fields', 'parameters'}:
      for field in getString(Cmd.OB_STRING).replace(',', ' ').split():
        if ':' in field:
          repsvc, _ = field.split(':', 1)
          if repsvc in fullDataServices:
            parameters.add(field)
          else:
            invalidChoiceExit(repsvc, fullDataServices, True)
        else:
          Cmd.Backup()
          invalidArgumentExit('service:parameter')
    elif myarg == 'skipdates':
      for skip in getString(Cmd.OB_STRING).upper().split(','):
        if skip.find(':') == -1:
          skipDates.add(validateYYYYMMDD(skip))
        else:
          skipStart, skipEnd = skip.split(':', 1)
          skipStartDate = validateYYYYMMDD(skipStart)
          skipEndDate = validateYYYYMMDD(skipEnd)
          if skipEndDate < skipStartDate:
            Cmd.Backup()
            usageErrorExit(Msg.INVALID_DATE_TIME_RANGE.format(myarg, skipEnd, myarg, skipStart))
          while skipStartDate <= skipEndDate:
            skipDates.add(skipStartDate)
            skipStartDate = skipStartDate.shift(days=1)
    elif myarg == 'skipdaysofweek':
      skipdaynames = getString(Cmd.OB_STRING).lower().split(',')
      dow = [d.lower() for d in DAYS_OF_WEEK]
      skipDayNumbers = [dow.index(d) for d in skipdaynames if d in dow]
    elif userReports and myarg == 'user':
      userKey = getString(Cmd.OB_EMAIL_ADDRESS)
      orgUnit = orgUnitId = None
      select = False
    elif userReports and (myarg == 'select' or myarg in usageEntitySelectors()):
      if myarg != 'select':
        Cmd.Backup()
      _, users = getEntityToModify(defaultEntityType=Cmd.ENTITY_USERS)
      orgUnit = orgUnitId = None
      select = True
    elif myarg == 'convertmbtogb':
      convertMbToGb = True
    elif myarg == 'addcsvdata':
      getAddCSVData(addCSVData)
    else:
      unknownArgumentExit()
  if startEndTime.endDateTime is None:
    startEndTime.endDateTime = todaysDate()
  if startEndTime.startDateTime is None:
    startEndTime.startDateTime = startEndTime.endDateTime.shift(days=-30)
  startDateTime = startEndTime.startDateTime
  startDate = startDateTime.strftime(YYYYMMDD_FORMAT)
  endDateTime = startEndTime.endDateTime
  endDate = endDateTime.strftime(YYYYMMDD_FORMAT)
  startUseDate = endUseDate = None
  if not orgUnitId:
    showOrgUnit = False
  if userReports:
    if select:
      Ent.SetGetting(Ent.REPORT)
      kwargs = [{'userKey': normalizeEmailAddressOrUID(user)} for user in users]
    elif userKey == 'all':
      if orgUnitId:
        kwargs[0]['orgUnitID'] = orgUnitId
        userOrgUnits = getUserOrgUnits(cd, orgUnit, orgUnitId)
        forWhom = f'users in orgUnit {orgUnit}'
      else:
        forWhom = 'all users'
      printGettingEntityItemForWhom(Ent.REPORT, forWhom)
    else:
      Ent.SetGetting(Ent.REPORT)
      kwargs = [{'userKey': normalizeEmailAddressOrUID(userKey)}]
      printGettingEntityItemForWhom(Ent.REPORT, kwargs[0]['userKey'])
    if showOrgUnit:
      titles.append('orgUnitPath')
  else:
    pageMessage = None
  if addCSVData:
    titles.extend(sorted(addCSVData.keys()))
  csvPF.SetTitles(titles)
  csvPF.SetSortAllTitles()
  parameters = ','.join(parameters) if parameters else None
  while startDateTime <= endDateTime:
    if startDateTime.weekday() in skipDayNumbers or startDateTime in skipDates:
      startDateTime = startDateTime.shift(days=1)
      continue
    useDate = startDateTime.strftime(YYYYMMDD_FORMAT)
    startDateTime = startDateTime.shift(days=1)
    try:
      for kwarg in kwargs:
        if userReports:
          if not select and userKey == 'all':
            pageMessage = getPageMessageForWhom(forWhom, showDate=useDate)
          else:
            pageMessage = getPageMessageForWhom(kwarg['userKey'], showDate=useDate)
        try:
          usage = callGAPIpages(service, 'get', 'usageReports',
                                pageMessage=pageMessage,
                                throwReasons=[GAPI.INVALID, GAPI.INVALID_INPUT, GAPI.BAD_REQUEST, GAPI.FORBIDDEN],
                                retryReasons=GAPI.SERVICE_NOT_AVAILABLE_RETRY_REASONS,
                                customerId=customerId, date=useDate,
                                parameters=parameters, **kwarg)
        except GAPI.badRequest:
          continue
        for entity in usage:
          row = {'date': useDate}
          if userReports:
            if 'userEmail' in entity['entity']:
              row['user'] = entity['entity']['userEmail']
              if showOrgUnit:
                row['orgUnitPath'] = userOrgUnits.get(row['user'], UNKNOWN)
            else:
              row['user'] = UNKNOWN
          if addCSVData:
            row.update(addCSVData)
          for item in entity.get('parameters', []):
            if 'name' not in item:
              continue
            name = item['name']
            if name == 'cros:device_version_distribution':
              versions = {}
              for version in item['msgValue']:
                versions[version['version_number']] = version['num_devices']
              for k, v in sorted(versions.items(), reverse=True):
                title = f'cros:num_devices_chrome_{k}'
                row[title] = v
            else:
              for ptype in REPORTS_PARAMETERS_SIMPLE_TYPES:
                if ptype in item:
                  if ptype != 'datetimeValue':
                    if convertMbToGb and name.endswith('_in_mb'):
                      name = convertReportMBtoGB(name, item)
                    row[name] = item[ptype]
                  else:
                    row[name] = formatLocalTime(item[ptype])
                  break
              else:
                row[name] = ''
          if not startUseDate:
            startUseDate = useDate
          endUseDate = useDate
          csvPF.WriteRowTitles(row)
    except GAPI.invalid as e:
      stderrWarningMsg(str(e))
      break
    except GAPI.invalidInput as e:
      systemErrorExit(GOOGLE_API_ERROR_RC, str(e))
    except GAPI.forbidden as e:
      accessErrorExit(None, str(e))
  if startUseDate:
    reportName = f'{report.capitalize()} Usage Report - {startUseDate}:{endUseDate}'
  else:
    reportName = f'{report.capitalize()} Usage Report - {startDate}:{endDate} - No Data'
  csvPF.writeCSVfile(reportName)

NL_SPACES_PATTERN = re.compile(r'\n +')
DISABLED_REASON_TIME_PATTERN = re.compile(r'.*(\d{4}/\d{2}/\d{2}-\d{2}:\d{2}:\d{2})')

REPORT_ALIASES_CHOICE_MAP = {
  'access': 'accesstransparency',
  'calendars': 'calendar',
  'cloud': 'gcp',
  'currents': 'gplus',
  'customers': 'customer',
  'domain': 'customer',
  'devices': 'mobile',
  'doc': 'drive',
  'docs': 'drive',
  'enterprisegroups': 'groupsenterprise',
  'gemini': 'geminiinworkspaceapps',
  'geminiforworkspace': 'geminiinworkspaceapps',
  'group': 'groups',
  'google+': 'gplus',
  'hangoutsmeet': 'meet',
  'logins': 'login',
  'lookerstudio': 'datastudio',
  'oauthtoken': 'token',
  'tokens': 'token',
  'users': 'user',
  }

REPORT_CHOICE_MAP = {
  'accessevaluation': 'access_evaluation',
  'accesstransparency': 'access_transparency',
  'admin': 'admin',
  'admindataaction': 'admin_data_action',
  'assignments': 'assignments',
  'calendar': 'calendar',
  'chat': 'chat',
  'chrome': 'chrome',
  'classroom': 'classroom',
  'cloudsearch': 'cloud_search',
  'contacts': 'contacts',
  'contextawareaccess': 'context_aware_access',
  'customer': 'customer',
  'datamigration': 'data_migration',
  'datastudio': 'data_studio',
  'directorysync': 'directory_sync',
  'drive': 'drive',
  'gcp': 'gcp',
  'geminiinworkspaceapps': 'gemini_in_workspace_apps',
  'gmail': 'gmail',
  'gplus': 'gplus',
  'graduation':'graduation',
  'groups': 'groups',
  'groupsenterprise': 'groups_enterprise',
  'jamboard': 'jamboard',
  'keep': 'keep',
  'ldap': 'ldap',
  'login': 'login',
  'meet': 'meet',
  'meethardware': 'meet_hardware',
  'mobile': 'mobile',
  'profile': 'profile',
  'rules': 'rules',
  'saml': 'saml',
  'takeout': 'takeout',
  'tasks': 'tasks',
  'token': 'token',
  'usage': 'usage',
  'usageparameters': 'usageparameters',
  'user': 'user',
  'useraccounts': 'user_accounts',
  'vault': 'vault',
  }

REPORT_ACTIVITIES_UPPERCASE_EVENTS = {
  'access_transparency',
  'admin',
  'chrome',
  'cloud_search',
  'context_aware_access',
  'data_migration',
  'data_studio',
  'directory_sync',
  'gcp',
  'jamboard',
  'meet_hardware',
  'mobile',
  'profile',
  'takeout',
  }

REPORT_ACTIVITIES_FILTER_MAP = {
  'applicationinfofilter': 'applicationInfoFilter',
  'groupidfilter': 'groupIdFilter',
  'networkinfofilter': 'networkInfoFilter',
  'resourcedetailsfilter': 'resourceDetailsFilter',
  'statusfilter': 'statusFilter',
  }

REPORT_ACTIVITIES_TIME_OBJECTS = {'time'}

# gam report <ActivityApplictionName> [todrive <ToDriveAttribute>*]
#	[(user all|<UserItem>)|(orgunit|org|ou <OrgUnitPath> [showorgunit])|(select <UserTypeEntity>)]
#	[userisactor]
#	[([start <Time>] [end <Time>])|(range <Time> <Time>)|
#	 yesterday|today|thismonth|(previousmonths <Integer>)]
#	[filter <String> (filtertime<String> <Time>)*]
#	[event|events <EventNameList>] [ip <String>]
#	[gmaileventtypes <NumberRangeList>]
#	[groupidfilter <String>] [resourcedetailsfilter <String>]
#	[networkinfofilter <String>] [statusfilter <String>]
#	[applicationinfofilter <String>] [includesensitivedata]
#	[notimesort]
#	[maxactivities <Number>] [maxevents <Number>] [maxresults <Number>]
#	[countsonly [bydate|summary] [eventrowfilter]]
#	(addcsvdata <FieldName> <String>)* [shownoactivities]
# gam report users|user [todrive <ToDriveAttribute>*]
#	[(user all|<UserItem>)|(orgunit|org|ou <OrgUnitPath> [showorgunit])|(select <UserTypeEntity>)]
#	[allverifyuser <UserItem>]
#	[(date <Date>)|(range <Date> <Date>)|
#	 yesterday|today|thismonth|(previousmonths <Integer>)]
#	[nodatechange | (fulldatarequired all|<UserServiceNameList>)]
#	[filter <String> (filtertime<String> <Time>)*]
#	[(fields|parameters <String>)|(services <UserServiceNameList>)]
#	[aggregatebydate|aggregatebyuser [Boolean]]
#	[maxresults <Number>]
#	[convertmbtogb]
#	(addcsvdata <FieldName> <String>)*
# gam report customers|customer|domain [todrive <ToDriveAttribute>*]
#	[(date <Date>)|(range <Date> <Date>)|
#	 yesterday|today|thismonth|(previousmonths <Integer>)]
#	[nodatechange | (fulldatarequired all|<CustomerServiceNameList>)]
#	[(fields|parameters <String>)|(services <CustomerServiceNameList>)] [noauthorizedapps]
#	[convertmbtogb]
#	(addcsvdata <FieldName> <String>)*
def doReport():
  def processUserUsage(usage, lastDate):
    if not usage:
      return (True, lastDate)
    if lastDate == usage[0]['date']:
      return (False, lastDate)
    lastDate = usage[0]['date']
    for user_report in usage:
      if 'entity' not in user_report:
        continue
      row = {'date': user_report['date']}
      if 'userEmail' in user_report['entity']:
        row['email'] = user_report['entity']['userEmail']
        if showOrgUnit:
          row['orgUnitPath'] = userOrgUnits.get(row['email'], UNKNOWN)
      else:
        row['email'] = UNKNOWN
      if addCSVData:
        row.update(addCSVData)
      for item in user_report.get('parameters', []):
        if 'name' not in item:
          continue
        name = item['name']
        repsvc, _ = name.split(':', 1)
        if repsvc not in includeServices:
          continue
        if name == 'accounts:disabled_reason' and 'stringValue' in item:
          mg = DISABLED_REASON_TIME_PATTERN.match(item['stringValue'])
          if mg:
            try:
              disabledTime = formatLocalTime(arrow.Arrow.strptime(mg.group(1), '%Y/%m/%d-%H:%M:%S').replace(tzinfo='UTC').strftime(YYYYMMDDTHHMMSSZ_FORMAT))
              row['accounts:disabled_time'] = disabledTime
              csvPF.AddTitles('accounts:disabled_time')
            except ValueError:
              pass
        elif convertMbToGb and name.endswith('_in_mb'):
          name = convertReportMBtoGB(name, item)
        csvPF.AddTitles(name)
        for ptype in REPORTS_PARAMETERS_SIMPLE_TYPES:
          if ptype in item:
            if ptype != 'datetimeValue':
              row[name] = item[ptype]
            else:
              row[name] = formatLocalTime(item[ptype])
            break
        else:
          row[name] = ''
      csvPF.WriteRow(row)
    return (True, lastDate)

  def processAggregateUserUsageByUser(usage, lastDate):
    if not usage:
      return (True, lastDate)
    if lastDate == usage[0]['date']:
      return (False, lastDate)
    lastDate = usage[0]['date']
    for user_report in usage:
      if 'entity' not in user_report:
        continue
      if 'userEmail' not in user_report['entity']:
        continue
      email = user_report['entity']['userEmail']
      for item in user_report.get('parameters', []):
        if 'name' not in item:
          continue
        name = item['name']
        repsvc, _ = name.split(':', 1)
        if repsvc not in includeServices:
          continue
        if 'intValue' in item:
          if convertMbToGb and name.endswith('_in_mb'):
            name = convertReportMBtoGB(name, None)
          csvPF.AddTitles(name)
          eventCounts.setdefault(email, {})
          eventCounts[email].setdefault(name, 0)
          eventCounts[email][name] += int(item['intValue'])
    return (True, lastDate)

  def processAggregateUserUsageByDate(usage, lastDate):
    if not usage:
      return (True, lastDate)
    if lastDate == usage[0]['date']:
      return (False, lastDate)
    lastDate = usage[0]['date']
    for user_report in usage:
      if 'entity' not in user_report:
        continue
      for item in user_report.get('parameters', []):
        if 'name' not in item:
          continue
        name = item['name']
        repsvc, _ = name.split(':', 1)
        if repsvc not in includeServices:
          continue
        if 'intValue' in item:
          if convertMbToGb and name.endswith('_in_mb'):
            name = convertReportMBtoGB(name, None)
          csvPF.AddTitles(name)
          eventCounts.setdefault(lastDate, {})
          eventCounts[lastDate].setdefault(name, 0)
          eventCounts[lastDate][name] += int(item['intValue'])
    return (True, lastDate)

  def processCustomerUsageOneRow(usage, lastDate):
    if not usage:
      return (True, lastDate)
    if lastDate == usage[0]['date']:
      return (False, lastDate)
    lastDate = usage[0]['date']
    row = {'date': lastDate}
    if addCSVData:
      row.update(addCSVData)
    for item in usage[0].get('parameters', []):
      if 'name' not in item:
        continue
      name = item['name']
      repsvc, _ = name.split(':', 1)
      if repsvc not in includeServices:
        continue
      for ptype in REPORTS_PARAMETERS_SIMPLE_TYPES:
        if ptype in item:
          if convertMbToGb and name.endswith('_in_mb'):
            name = convertReportMBtoGB(name, item)
          csvPF.AddTitles(name)
          if ptype != 'datetimeValue':
            row[name] = item[ptype]
          else:
            row[name] = formatLocalTime(item[ptype])
          break
      else:
        if 'msgValue' in item:
          if name == 'accounts:authorized_apps':
            if noAuthorizedApps:
              continue
            for app in item['msgValue']:
              appName = f'App: {escapeCRsNLs(app["client_name"])}'
              for key in ['num_users', 'client_id']:
                title = f'{appName}{GC.Values[GC.CSV_OUTPUT_SUBFIELD_DELIMITER]}{key}'
                csvPF.AddTitles(title)
                row[title] = app[key]
          elif name == 'cros:device_version_distribution':
            versions = {}
            for version in item['msgValue']:
              versions[version['version_number']] = version['num_devices']
            for k, v in sorted(versions.items(), reverse=True):
              title = f'cros:device_version{GC.Values[GC.CSV_OUTPUT_SUBFIELD_DELIMITER]}{k}'
              csvPF.AddTitles(title)
              row[title] = v
          else:
            values = []
            for subitem in item['msgValue']:
              if 'count' in subitem:
                mycount = myvalue = None
                for key, value in subitem.items():
                  if key == 'count':
                    mycount = value
                  else:
                    myvalue = value
                  if mycount and myvalue:
                    values.append(f'{myvalue}:{mycount}')
                value = ' '.join(values)
              elif 'version_number' in subitem and 'num_devices' in subitem:
                values.append(f'{subitem["version_number"]}:{subitem["num_devices"]}')
              else:
                continue
              value = ' '.join(sorted(values, reverse=True))
            csvPF.AddTitles(name)
            row['name'] = value
    csvPF.WriteRow(row)
    return (True, lastDate)

  def processCustomerUsage(usage, lastDate):
    if not usage:
      return (True, lastDate)
    if lastDate == usage[0]['date']:
      return (False, lastDate)
    lastDate = usage[0]['date']
    for item in usage[0].get('parameters', []):
      if 'name' not in item:
        continue
      name = item['name']
      repsvc, _ = name.split(':', 1)
      if repsvc not in includeServices:
        continue
      for ptype in REPORTS_PARAMETERS_SIMPLE_TYPES:
        if ptype in item:
          row = {'date': lastDate}
          if addCSVData:
            row.update(addCSVData)
          if ptype != 'datetimeValue':
            if convertMbToGb and name.endswith('_in_mb'):
              name = convertReportMBtoGB(name, item)
            row.update({'name': name, 'value': item[ptype]})
          else:
            row.update({'name': name, 'value': formatLocalTime(item[ptype])})
          csvPF.WriteRow(row)
          break
      else:
        if 'msgValue' in item:
          if name == 'accounts:authorized_apps':
            if noAuthorizedApps:
              continue
            for subitem in item['msgValue']:
              app = {'date': lastDate}
              if addCSVData:
                app.update(addCSVData)
              for an_item in subitem:
                if an_item == 'client_name':
                  app['name'] = f'App: {escapeCRsNLs(subitem[an_item])}'
                elif an_item == 'num_users':
                  app['value'] = f'{subitem[an_item]} users'
                elif an_item == 'client_id':
                  app['client_id'] = subitem[an_item]
              authorizedApps.append(app)
          elif name == 'cros:device_version_distribution':
            values = []
            for subitem in item['msgValue']:
              values.append(f'{subitem["version_number"]}:{subitem["num_devices"]}')
            row = {'date': lastDate}
            if addCSVData:
              row.update(addCSVData)
            row.update({'name': name, 'value': ' '.join(sorted(values, reverse=True))})
            csvPF.WriteRow(row)
          else:
            values = []
            for subitem in item['msgValue']:
              if 'count' in subitem:
                mycount = myvalue = None
                for key, value in subitem.items():
                  if key == 'count':
                    mycount = value
                  else:
                    myvalue = value
                  if mycount and myvalue:
                    values.append(f'{myvalue}:{mycount}')
              else:
                continue
            row = {'date': lastDate}
            if addCSVData:
              row.update(addCSVData)
            row.update({'name': name, 'value': ' '.join(sorted(values, reverse=True))})
            csvPF.WriteRow(row)
    csvPF.SortRowsTwoTitles('date', 'name', False)
    if authorizedApps:
      csvPF.AddTitle('client_id')
      for row in sorted(authorizedApps, key=lambda k: (k['date'], k['name'].lower())):
        csvPF.WriteRow(row)
    return (True, lastDate)

  def _computeUsedQuotaInPercentage(events):
    if ('accounts:total_quota_in_mb' in events) and (events['accounts:total_quota_in_mb'] > 0) and ('accounts:used_quota_in_mb' in events):
      events['accounts:used_quota_in_percentage'] = int(events['accounts:used_quota_in_mb']/events['accounts:total_quota_in_mb']*100)
    else:
      events['accounts:used_quota_in_percentage'] = 0

  def _getActivitiesFilters(myarg):
    if myarg in REPORT_ACTIVITIES_FILTER_MAP:
      kwargs[REPORT_ACTIVITIES_FILTER_MAP[myarg]] = getString(Cmd.OB_STRING)
      return True
    return False

  # dynamically extend our choices with other reports Google dynamically adds
  rep = buildGAPIObject(API.REPORTS)
  dyn_choices = rep._rootDesc \
          .get('resources', {}) \
          .get('activities', {}) \
          .get('methods', {}) \
          .get('list', {}) \
          .get('parameters', {}) \
          .get('applicationName', {}) \
          .get('enum', [])
  for dyn_choice in dyn_choices:
    if dyn_choice.replace('_', '') not in REPORT_CHOICE_MAP and \
       dyn_choice not in REPORT_CHOICE_MAP.values():
      REPORT_CHOICE_MAP[dyn_choice.replace('_', '')] = dyn_choice
  report = getChoice(REPORT_CHOICE_MAP, choiceAliases=REPORT_ALIASES_CHOICE_MAP, mapChoice=True)
  if report == 'usage':
    doReportUsage()
    return
  if report == 'usageparameters':
    doReportUsageParameters()
    return
  customerId = GC.Values[GC.CUSTOMER_ID]
  if customerId == GC.MY_CUSTOMER:
    customerId = None
  csvPF = CSVPrintFile()
  filters = actorIpAddress = orgUnit = orgUnitId = None
  showOrgUnit = False
  parameters = set()
  parameterServices = set()
  eventCounts = {}
  eventNames = []
  startEndTime = StartEndTime('start', 'end')
  filterTimes = {}
  maxActivities = maxEvents = 0
  maxResults = 1000
  aggregateByDate = aggregateByUser = convertMbToGb = countsOnly = countsByDate = countsSummary = \
    eventRowFilter = exitUserLoop = noAuthorizedApps = normalizeUsers = select = userCustomerRange = False
  sortAllTimes = True
  limitDateChanges = -1
  allVerifyUser = userKey = 'all'
  cd = orgUnit = orgUnitId = None
  userOrgUnits = {}
  gmailEventTypes = set()
  customerReports = userReports = False
  if report == 'customer':
    customerReports = True
    service = rep.customerUsageReports()
    fullDataServices = CUSTOMER_REPORT_SERVICES
  elif report == 'user':
    userReports = True
    service = rep.userUsageReport()
    fullDataServices = USER_REPORT_SERVICES
  else:
    service = rep.activities()
  usageReports = customerReports or userReports
  activityReports = not usageReports
  dataRequiredServices = set()
  addCSVData = {}
  mapAdminUsersToFilter = True
  showNoActivities = False
  if usageReports:
    includeServices = set()
  kwargs = {}
  while Cmd.ArgumentsRemaining():
    myarg = getArgument()
    if myarg == 'todrive':
      csvPF.GetTodriveParameters()
    elif myarg in {'range', 'thismonth', 'previousmonths'}:
      startEndTime.Get(myarg)
      userCustomerRange = True
    elif myarg in {'ou', 'org', 'orgunit'}:
      if cd is None:
        cd = buildGAPIObject(API.DIRECTORY)
      orgUnit, orgUnitId = getOrgUnitId(cd)
      select = False
    elif myarg == 'showorgunit':
      showOrgUnit = True
    elif usageReports and myarg in {'date', 'yesterday', 'today'}:
      startEndTime.Get('start' if myarg == 'date' else myarg)
      startEndTime.endDateTime = startEndTime.startDateTime
      userCustomerRange = False
    elif usageReports and myarg in {'nodatechange', 'limitdatechanges'}:
      if myarg == 'nodatechange':
        limitDateChanges = 0
      else:
        limitDateChanges = getInteger(minVal=-1)
      if (limitDateChanges == 0) and (startEndTime.startDateTime is not None) and (startEndTime.endDateTime == startEndTime.startDateTime):
        userCustomerRange = True
    elif usageReports and myarg in {'fields', 'parameters'}:
      for field in getString(Cmd.OB_STRING).replace(',', ' ').split():
        if ':' in field:
          repsvc, _ = field.split(':', 1)
          if repsvc in fullDataServices:
            parameters.add(field)
            parameterServices.add(repsvc)
            includeServices.add(repsvc)
          else:
            invalidChoiceExit(repsvc, fullDataServices, True)
        else:
          Cmd.Backup()
          invalidArgumentExit('service:parameter')
    elif usageReports and myarg == 'fulldatarequired':
      fdr = getString(Cmd.OB_SERVICE_NAME_LIST, minLen=0).lower()
      if fdr:
        if fdr != 'all':
          for repsvc in fdr.replace(',', ' ').split():
            if repsvc in fullDataServices:
              dataRequiredServices.add(repsvc)
            else:
              invalidChoiceExit(repsvc, fullDataServices, True)
        else:
          dataRequiredServices = fullDataServices
    elif usageReports and myarg in {'service', 'services'}:
      for repsvc in getString(Cmd.OB_SERVICE_NAME_LIST).lower().replace(',', ' ').split():
        if repsvc in fullDataServices:
          parameterServices.add(repsvc)
          includeServices.add(repsvc)
        else:
          invalidChoiceExit(repsvc, fullDataServices, True)
    elif usageReports and myarg == 'convertmbtogb':
      convertMbToGb = True
    elif customerReports and myarg == 'noauthorizedapps':
      noAuthorizedApps = True
    elif activityReports and myarg == 'maxactivities':
      maxActivities = getInteger(minVal=0)
    elif activityReports and myarg == 'maxevents':
      maxEvents = getInteger(minVal=0)
    elif activityReports and myarg in {'start', 'starttime', 'end', 'endtime', 'yesterday', 'today'}:
      startEndTime.Get(myarg)
    elif activityReports and myarg in {'event', 'events'}:
      for event in getString(Cmd.OB_EVENT_NAME_LIST).replace(',', ' ').split():
        event = event.lower() if report not in REPORT_ACTIVITIES_UPPERCASE_EVENTS else event.upper()
        if event not in eventNames:
          eventNames.append(event)
    elif activityReports and myarg == 'ip':
      actorIpAddress = getString(Cmd.OB_STRING)
    elif activityReports and myarg == 'notimesort':
      sortAllTimes = False
    elif activityReports and myarg == 'countsonly':
      countsOnly = True
    elif activityReports and myarg == 'bydate':
      countsByDate = True
    elif activityReports and myarg == 'summary':
      countsSummary = True
    elif activityReports and myarg == 'eventrowfilter':
      eventRowFilter = True
    elif activityReports and _getActivitiesFilters(myarg):
      pass
    elif activityReports and (report == 'gmail')  and myarg == 'gmaileventtypes':
      gmailEventTypes = set(getNumberRangeList())
    elif activityReports and myarg == 'userisactor':
      mapAdminUsersToFilter = False
    elif activityReports and myarg == 'includesensitivedata':
      kwargs['includeSensitiveData'] = True
    elif myarg == 'addcsvdata':
      getAddCSVData(addCSVData)
    elif activityReports and myarg == 'shownoactivities':
      showNoActivities = True
    elif not customerReports and myarg.startswith('filtertime'):
      filterTimes[myarg] = getTimeOrDeltaFromNow()
    elif not customerReports and myarg in {'filter', 'filters'}:
      filters = getString(Cmd.OB_STRING)
    elif not customerReports and myarg == 'maxresults':
      maxResults = getInteger(minVal=1, maxVal=1000)
    elif not customerReports and myarg == 'user':
      userKey = getString(Cmd.OB_EMAIL_ADDRESS)
      orgUnit = orgUnitId = None
      select = False
    elif not customerReports and myarg == 'select':
      _, users = getEntityToModify(defaultEntityType=Cmd.ENTITY_USERS)
      orgUnit = orgUnitId = None
      select = True
    elif userReports and myarg == 'aggregatebydate':
      aggregateByDate = getBoolean()
    elif userReports and myarg == 'aggregatebyuser':
      aggregateByUser = getBoolean()
    elif userReports and myarg == 'allverifyuser':
      allVerifyUser = getEmailAddress()
    else:
      unknownArgumentExit()
  if aggregateByDate and aggregateByUser:
    usageErrorExit(Msg.ARE_MUTUALLY_EXCLUSIVE.format('aggregateByDate', 'aggregateByUser'))
  if countsOnly and countsByDate and countsSummary:
    usageErrorExit(Msg.ARE_MUTUALLY_EXCLUSIVE.format('bydate', 'summary'))
  parameters = ','.join(parameters) if parameters else None
  if usageReports and not includeServices:
    includeServices = set(fullDataServices)
  if filterTimes and filters is not None:
    for filterTimeName, filterTimeValue in filterTimes.items():
      filters = filters.replace(f'#{filterTimeName}#', filterTimeValue)
  if not orgUnitId:
    showOrgUnit = False
  if userReports:
    if startEndTime.startDateTime is None:
      startEndTime.startDateTime = startEndTime.endDateTime = todaysDate()
    if select:
      normalizeUsers = True
      orgUnitId = None
      Ent.SetGetting(Ent.REPORT)
    elif userKey == 'all':
      if orgUnitId:
        if showOrgUnit:
          userOrgUnits = getUserOrgUnits(cd, orgUnit, orgUnitId)
        forWhom = f'users in orgUnit {orgUnit}'
      else:
        forWhom = 'all users'
      printGettingEntityItemForWhom(Ent.REPORT, forWhom)
      users = ['all']
    else:
      Ent.SetGetting(Ent.REPORT)
      users = [normalizeEmailAddressOrUID(userKey)]
      orgUnitId = None
    if aggregateByDate:
      titles = ['date']
    elif aggregateByUser:
      titles = ['email'] if not showOrgUnit else ['email', 'orgUnitPath']
    else:
      titles = ['email', 'date'] if not showOrgUnit else ['email', 'orgUnitPath', 'date']
    if addCSVData:
      titles.extend(sorted(addCSVData.keys()))
    csvPF.SetTitles(titles)
    csvPF.SetSortAllTitles()
    i = 0
    count = len(users)
    for user in users:
      i += 1
      if normalizeUsers:
        user = normalizeEmailAddressOrUID(user)
      if user != 'all':
        printGettingEntityItemForWhom(Ent.REPORT, user, i, count)
        verifyUser = user
      else:
        verifyUser = allVerifyUser
      startDateTime = startEndTime.startDateTime
      endDateTime = startEndTime.endDateTime
      lastDate = None
      numDateChanges = 0
      while startDateTime <= endDateTime:
        tryDate = startDateTime.strftime(YYYYMMDD_FORMAT)
        try:
          if not userCustomerRange:
            result = callGAPI(service, 'get',
                              throwReasons=[GAPI.INVALID, GAPI.INVALID_INPUT, GAPI.BAD_REQUEST, GAPI.FORBIDDEN],
                              userKey=verifyUser, date=tryDate, customerId=customerId,
                              orgUnitID=orgUnitId, parameters=parameters,
                              fields='warnings,usageReports', maxResults=1)
            prevTryDate = tryDate
            fullData, tryDate, usageReports = _checkDataRequiredServices(result, tryDate,
                                                                         dataRequiredServices, parameterServices, True)
            if fullData < 0:
              printWarningMessage(DATA_NOT_AVALIABLE_RC, Msg.NO_REPORT_AVAILABLE.format(report))
              break
            numDateChanges += 1
            if fullData == 0:
              if numDateChanges > limitDateChanges >= 0:
                break
              startDateTime = endDateTime = arrow.Arrow.strptime(tryDate, YYYYMMDD_FORMAT)
              continue
          if not select and userKey == 'all':
            pageMessage = getPageMessageForWhom(forWhom, showDate=tryDate)
          else:
            pageMessage = getPageMessageForWhom(user, showDate=tryDate)
          prevTryDate = tryDate
          usage = callGAPIpages(service, 'get', 'usageReports',
                                pageMessage=pageMessage,
                                throwReasons=[GAPI.INVALID, GAPI.INVALID_INPUT, GAPI.BAD_REQUEST, GAPI.FORBIDDEN],
                                retryReasons=GAPI.SERVICE_NOT_AVAILABLE_RETRY_REASONS,
                                userKey=user, date=tryDate, customerId=customerId,
                                orgUnitID=orgUnitId, filters=filters, parameters=parameters,
                                maxResults=maxResults)
          if aggregateByDate:
            status, lastDate = processAggregateUserUsageByDate(usage, lastDate)
          elif aggregateByUser:
            status, lastDate = processAggregateUserUsageByUser(usage, lastDate)
          else:
            status, lastDate = processUserUsage(usage, lastDate)
          if not status:
            break
        except GAPI.invalid as e:
          if userCustomerRange:
            break
          numDateChanges += 1
          tryDate = _adjustTryDate(str(e), numDateChanges, limitDateChanges, tryDate)
          if not tryDate:
            break
          startDateTime = endDateTime = arrow.Arrow.strptime(tryDate, YYYYMMDD_FORMAT)
          continue
        except GAPI.invalidInput as e:
          systemErrorExit(GOOGLE_API_ERROR_RC, str(e))
        except GAPI.badRequest:
          if user != 'all':
            entityUnknownWarning(Ent.USER, user, i, count)
          else:
            printErrorMessage(BAD_REQUEST_RC, Msg.BAD_REQUEST)
            exitUserLoop = True
          break
        except GAPI.forbidden as e:
          accessErrorExit(None, str(e))
        startDateTime = startDateTime.shift(days=1)
      if exitUserLoop:
        break
      if user != 'all' and lastDate is None and GC.Values[GC.CSV_OUTPUT_USERS_AUDIT]:
        csvPF.WriteRowNoFilter({'date': prevTryDate, 'email': user})
    if aggregateByDate:
      for usageDate, events in eventCounts.items():
        row = {'date': usageDate}
        if addCSVData:
          row.update(addCSVData)
        if 'accounts:used_quota_in_percentage' in events:
          _computeUsedQuotaInPercentage(events)
        for event, count in events.items():
          if convertMbToGb and event.endswith('_in_gb'):
            count = f'{count/1024:.2f}'
          row[event] = count
        csvPF.WriteRow(row)
      csvPF.SortRows('date', False)
      csvPF.writeCSVfile(f'User Reports Aggregate - {tryDate}')
    elif aggregateByUser:
      for email, events in eventCounts.items():
        row = {'email': email}
        if showOrgUnit:
          row['orgUnitPath'] = userOrgUnits.get(email, UNKNOWN)
        if addCSVData:
          row.update(addCSVData)
        if 'accounts:used_quota_in_percentage' in events:
          _computeUsedQuotaInPercentage(events)
        for event, count in events.items():
          if convertMbToGb and event.endswith('_in_gb'):
            count = f'{count/1024:.2f}'
          row[event] = count
        csvPF.WriteRow(row)
      csvPF.SortRows('email', False)
      csvPF.writeCSVfile('User Reports Aggregate - User')
    else:
      csvPF.SortRowsTwoTitles('email', 'date', False)
      csvPF.writeCSVfile(f'User Reports - {tryDate}')
  elif customerReports:
    if startEndTime.startDateTime is None:
      startEndTime.startDateTime = startEndTime.endDateTime = todaysDate()
    csvPF.SetTitles('date')
    if addCSVData:
      csvPF.AddTitles(sorted(addCSVData.keys()))
    if not userCustomerRange or (startEndTime.startDateTime == startEndTime.endDateTime):
      csvPF.AddTitles(['name', 'value'])
    authorizedApps = []
    startDateTime = startEndTime.startDateTime
    endDateTime = startEndTime.endDateTime
    lastDate = None
    numDateChanges = 0
    while startDateTime <= endDateTime:
      tryDate = startDateTime.strftime(YYYYMMDD_FORMAT)
      try:
        if not userCustomerRange:
          result = callGAPI(service, 'get',
                            throwReasons=[GAPI.INVALID, GAPI.INVALID_INPUT, GAPI.BAD_REQUEST, GAPI.FORBIDDEN],
                            date=tryDate, customerId=customerId, parameters=parameters, fields='warnings,usageReports')
          fullData, tryDate, usageReports = _checkDataRequiredServices(result, tryDate,
                                                                       dataRequiredServices, parameterServices)
          if fullData < 0:
            printWarningMessage(DATA_NOT_AVALIABLE_RC, Msg.NO_REPORT_AVAILABLE.format(report))
            break
          numDateChanges += 1
          if fullData == 0:
            if numDateChanges > limitDateChanges >= 0:
              break
            startDateTime = endDateTime = arrow.Arrow.strptime(tryDate, YYYYMMDD_FORMAT)
            continue
        usage = callGAPIpages(service, 'get', 'usageReports',
                              throwReasons=[GAPI.INVALID, GAPI.INVALID_INPUT, GAPI.FORBIDDEN],
                              date=tryDate, customerId=customerId, parameters=parameters)
        if not userCustomerRange or (startEndTime.startDateTime == startEndTime.endDateTime):
          status, lastDate = processCustomerUsage(usage, lastDate)
        else:
          status, lastDate = processCustomerUsageOneRow(usage, lastDate)
        if not status:
          break
      except GAPI.invalid as e:
        if userCustomerRange:
          break
        numDateChanges += 1
        tryDate = _adjustTryDate(str(e), numDateChanges, limitDateChanges, tryDate)
        if not tryDate:
          break
        startDateTime = endDateTime = arrow.Arrow.strptime(tryDate, YYYYMMDD_FORMAT)
        continue
      except GAPI.invalidInput as e:
        systemErrorExit(GOOGLE_API_ERROR_RC, str(e))
      except GAPI.forbidden as e:
        accessErrorExit(None, str(e))
      startDateTime = startDateTime.shift(days=1)
    csvPF.writeCSVfile(f'Customer Report - {tryDate}')
  else: # activityReports
    csvPF.SetTitles('name')
    if addCSVData:
      csvPF.AddTitles(sorted(addCSVData.keys()))
    csvPF.SetSortAllTitles()
    if select:
      pageMessage = getPageMessage()
      normalizeUsers = True
      orgUnitId = None
    elif userKey == 'all':
      if orgUnitId:
        if showOrgUnit:
          userOrgUnits = getUserOrgUnits(cd, orgUnit, orgUnitId)
        printGettingAllEntityItemsForWhom(Ent.ACTIVITY, f'users in orgUnit {orgUnit}', query=filters)
      else:
        printGettingAllEntityItemsForWhom(Ent.ACTIVITY, 'all users', query=filters)
      pageMessage = getPageMessage()
      users = ['all']
    else:
      Ent.SetGetting(Ent.ACTIVITY)
      pageMessage = getPageMessage()
      users = [normalizeEmailAddressOrUID(userKey)]
      orgUnitId = None
    zeroEventCounts = {}
    if not eventNames:
      eventNames.append(None)
    else:
      for eventName in eventNames:
        zeroEventCounts[eventName] = 0
    mapUsersToFilter = False
    count = len(users)
# gmail requires a start time and an end time no more than 30 days apart
    if report == 'gmail':
      if startEndTime.startTime is None:
        if startEndTime.endTime is None:
          startEndTime.endDateTime = todaysDate()
          startEndTime.endTime = ISOformatTimeStamp(startEndTime.endDateTime)
        startEndTime.startDateTime = startEndTime.endDateTime.shift(days=-30)
        startEndTime.startTime = ISOformatTimeStamp(startEndTime.startDateTime)
      elif startEndTime.endTime is None:
        startEndTime.endDateTime = startEndTime.startDateTime.shift(days=30)
        startEndTime.endTime = ISOformatTimeStamp(startEndTime.endDateTime)
# admin uses userKey for who executed the command, map user to filter EMAIL_USER==user
# unless userisactor was specified
    elif report == 'admin':
      if mapAdminUsersToFilter:
        if select or count != 1 or users[0] != 'all':
          if filters is None:
            mapUsersToFilter = True
            filters = 'USER_EMAIL==#user#'
          elif  'USER_EMAIL==' not in filters:
            mapUsersToFilter = True
            filters = filters+',USER_EMAIL==#user#'
# chrome does not use userKey, map user to filter DEVICE_USER==user
    elif report == 'chrome':
      if select or count != 1 or users[0] != 'all':
        if filters is None:
          mapUsersToFilter = True
          filters = 'DEVICE_USER==#user#'
        elif 'DEVICE_USER==' not in filters:
          mapUsersToFilter = True
          filters = filters+',DEVICE_USER==#user#'
    i = 0
    for user in users:
      i += 1
      if normalizeUsers:
        user = normalizeEmailAddressOrUID(user)
      pfilters = filters
      if select or user != 'all':
        puser = user
        if mapUsersToFilter:
          pfilters = filters.replace('#user#', user)
          user = 'all'
        printGettingAllEntityItemsForWhom(Ent.ACTIVITY, puser, i, count, query=pfilters)
      for eventName in eventNames:
        try:
          feed = callGAPIpages(service, 'list', 'items',
                               pageMessage=pageMessage, maxItems=maxActivities,
                               throwReasons=[GAPI.BAD_REQUEST, GAPI.INVALID, GAPI.INVALID_INPUT, GAPI.AUTH_ERROR, GAPI.SERVICE_NOT_AVAILABLE],
                               retryReasons=GAPI.SERVICE_NOT_AVAILABLE_RETRY_REASONS,
                               applicationName=report, userKey=user, customerId=customerId,
                               actorIpAddress=actorIpAddress, orgUnitID=orgUnitId,
                               startTime=startEndTime.startTime, endTime=startEndTime.endTime,
                               eventName=eventName, filters=pfilters, maxResults=maxResults, **kwargs)
        except GAPI.badRequest:
          if user != 'all':
            entityUnknownWarning(Ent.USER, user, i, count)
            continue
          printErrorMessage(BAD_REQUEST_RC, Msg.BAD_REQUEST)
          break
        except (GAPI.invalid, GAPI.invalidInput, GAPI.serviceNotAvailable) as e:
          systemErrorExit(GOOGLE_API_ERROR_RC, str(e))
        except GAPI.authError:
          accessErrorExit(None)
        for activity in feed:
          events = activity.pop('events')
          actor = activity['actor'].get('email')
          if not actor:
            actor = 'id:'+activity['actor'].get('profileId', UNKNOWN)
          if showOrgUnit:
            activity['actor']['orgUnitPath'] = userOrgUnits.get(actor, UNKNOWN)
          if countsOnly and countsByDate:
            eventTime = activity.get('id', {}).get('time', UNKNOWN)
            if eventTime != UNKNOWN:
              try:
                eventTime = arrow.get(eventTime)
              except (arrow.parser.ParserError, OverflowError):
                eventTime = UNKNOWN
            if eventTime != UNKNOWN:
              eventDate = eventTime.strftime(YYYYMMDD_FORMAT)
            else:
              eventDate = UNKNOWN
          if not countsOnly or eventRowFilter:
            activity_row = flattenJSON(activity, timeObjects=REPORT_ACTIVITIES_TIME_OBJECTS)
            purge_parameters = True
            numEvents = 0
            for event in events:
              # filter gmail event types
              if gmailEventTypes:
                keepEvent = True
                for item in event.get('parameters', []):
                  if item['name'] == 'event_info':
                    for parm in item.get('messageValue', {}).get('parameter', []):
                      if parm['name'] == 'mail_event_type':
                        if int(parm['intValue']) not in gmailEventTypes:
                          keepEvent = False
                        break
                    break
                if not keepEvent:
                  continue
              numEvents += 1
              for item in event.get('parameters', []):
                itemSet = set(item)
                if not itemSet.symmetric_difference({'name'}):
                  event[item['name']] = ''
                elif not itemSet.symmetric_difference({'value', 'name'}):
                  event[item['name']] = NL_SPACES_PATTERN.sub('', item['value'])
                elif not itemSet.symmetric_difference({'intValue', 'name'}):
                  if item['name'] in {'start_time', 'end_time'}:
                    val = item.get('intValue')
                    if val is not None:
                      val = int(val)
                      if val >= 62135683200:
                        event[item['name']] = ISOformatTimeStamp(arrow.Arrow.fromtimestamp(val-62135683200, GC.Values[GC.TIMEZONE]))
                      else:
                        event[item['name']] = val
                  else:
                    event[item['name']] = item['intValue']
                elif not itemSet.symmetric_difference({'boolValue', 'name'}):
                  event[item['name']] = item['boolValue']
                elif not itemSet.symmetric_difference({'multiValue', 'name'}):
                  event[item['name']] = ' '.join(item['multiValue'])
                elif item['name'] == 'scope_data':
                  parts = {}
                  for message in item['multiMessageValue']:
                    for mess in message['parameter']:
                      value = mess.get('value', ' '.join(mess.get('multiValue', [])))
                      parts[mess['name']] = parts.get(mess['name'], [])+[value]
                  for part, v in parts.items():
                    if part == 'scope_name':
                      part = 'scope'
                    event[part] = ' '.join(v)
                else:
                  purge_parameters = False
              if purge_parameters:
                event.pop('parameters', None)
              row = flattenJSON(event)
              row.update(activity_row)
              if not countsOnly:
                if addCSVData:
                  row.update(addCSVData)
                csvPF.WriteRowTitles(row)
                if numEvents >= maxEvents > 0:
                  break
              elif csvPF.CheckRowTitles(row):
                eventName = event['name']
                if not countsSummary:
                  eventCounts.setdefault(actor, {})
                  if not countsByDate:
                    eventCounts[actor].setdefault(eventName, 0)
                    eventCounts[actor][eventName] += 1
                  else:
                    eventCounts[actor].setdefault(eventDate, {})
                    eventCounts[actor][eventDate].setdefault(eventName, 0)
                    eventCounts[actor][eventDate][eventName] += 1
                else:
                  eventCounts.setdefault(eventName, 0)
                  eventCounts[eventName] += 1
          elif not countsSummary:
            eventCounts.setdefault(actor, {})
            if not countsByDate:
              for event in events:
                eventName = event['name']
                eventCounts[actor].setdefault(eventName, 0)
                eventCounts[actor][eventName] += 1
            else:
              for event in events:
                eventName = event['name']
                eventCounts[actor].setdefault(eventDate, {})
                eventCounts[actor][eventDate].setdefault(eventName, 0)
                eventCounts[actor][eventDate][eventName] += 1
          else:
            for event in events:
              eventCounts.setdefault(event['name'], 0)
              eventCounts[event['name']] += 1
    if not countsOnly:
      if not csvPF.rows and showNoActivities:
        row = {'name': 'NoActivities'}
        if addCSVData:
          row.update(addCSVData)
        csvPF.WriteRowTitles(row)
      elif sortAllTimes:
        csvPF.SortRows('id.time', True)
    else:
      if eventRowFilter:
        csvPF.SetRowFilter([], GC.Values[GC.CSV_OUTPUT_ROW_FILTER_MODE])
        csvPF.SetRowDropFilter([], GC.Values[GC.CSV_OUTPUT_ROW_DROP_FILTER_MODE])
      if not countsSummary:
        titles = ['emailAddress']
        if countsOnly and countsByDate:
          titles.append('date')
        csvPF.SetTitles(titles)
        csvPF.SetSortTitles(titles)
        if addCSVData:
          csvPF.AddTitles(sorted(addCSVData.keys()))
        if eventCounts:
          if not countsByDate:
            for actor, events in eventCounts.items():
              row = {'emailAddress': actor}
              row.update(zeroEventCounts)
              for event, count in events.items():
                row[event] = count
              if addCSVData:
                row.update(addCSVData)
              csvPF.WriteRowTitles(row)
          else:
            for actor, eventDates in eventCounts.items():
              for eventDate, events in eventDates.items():
                row = {'emailAddress': actor, 'date': eventDate}
                row.update(zeroEventCounts)
                for event, count in events.items():
                  row[event] = count
                if addCSVData:
                  row.update(addCSVData)
                csvPF.WriteRowTitles(row)
        elif showNoActivities:
          row = {'emailAddress': 'NoActivities'}
          if addCSVData:
            row.update(addCSVData)
            csvPF.WriteRow(row)
      else:
        csvPF.SetTitles(['event', 'count'])
        if addCSVData:
          csvPF.AddTitles(sorted(addCSVData.keys()))
        if eventCounts:
          for event, count in sorted(eventCounts.items()):
            row = {'event': event, 'count': count}
            if addCSVData:
              row.update(addCSVData)
            csvPF.WriteRow(row)
        elif showNoActivities:
          row = {'event': 'NoActivities', 'count': 0}
          if addCSVData:
            row.update(addCSVData)
          csvPF.WriteRow(row)
    csvPF.writeCSVfile(f'{report.capitalize()} Activity Report', eventRowFilter)

# Substitute for #user#, #email#, #usernamne#
