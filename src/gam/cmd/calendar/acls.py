"""GAM calendar ACLs commands."""


from gamlib import api as API
from gamlib import gapi as GAPI
from gamlib import msgs as Msg
from gam.var import Act, Cmd, Ent, Ind
from gam.util.api_call import callGAPIpages
from gam.util.args import getArgument, checkForExtraneousArguments, getChoice
from gam.util.csv_pf import CSVPrintFile, FormatJSONQuoteChar
from gam.util.display import entityActionFailedWarning
from gam.util.entity import getEntityList, getEntityArgument, convertUIDtoEmailAddress
from gam.constants import NO_ENTITIES_FOUND_RC

from gam.cmd.calendar import validateCalendar


def createCalendarACLs(users):
  calendarEntity = getUserCalendarEntity()
  role, ACLScopeEntity, sendNotifications = getCalendarCreateUpdateACLsOptions(True)
  i, count, users = getEntityArgument(users)
  for user in users:
    i += 1
    origUser = user
    user, cal, calIds, jcount = _validateUserGetCalendarIds(user, i, count, calendarEntity, Ent.CALENDAR_ACL, Act.MODIFIER_TO)
    if jcount == 0:
      continue
    Ind.Increment()
    _doCalendarsCreateACLs(origUser, user, cal, calIds, jcount, role, ACLScopeEntity, sendNotifications)
    Ind.Decrement()

def updateDeleteCalendarACLs(users, calendarEntity, function, modifier, ACLScopeEntity, role, sendNotifications):
  i, count, users = getEntityArgument(users)
  for user in users:
    i += 1
    origUser = user
    user, cal, calIds, jcount = _validateUserGetCalendarIds(user, i, count, calendarEntity, Ent.CALENDAR_ACL, modifier)
    if jcount == 0:
      continue
    Ind.Increment()
    _doUpdateDeleteCalendarACLs(origUser, user, cal, function, calIds, jcount, ACLScopeEntity, role, sendNotifications)
    Ind.Decrement()

# gam <UserTypeEntity> update calendaracls <UserCalendarEntity> <CalendarACLRole> <CalendarACLScopeEntity> [sendnotifications <Boolean>]
def updateCalendarACLs(users):
  calendarEntity = getUserCalendarEntity()
  role, ACLScopeEntity, sendNotifications = getCalendarCreateUpdateACLsOptions(True)
  updateDeleteCalendarACLs(users, calendarEntity, 'patch', Act.MODIFIER_IN, ACLScopeEntity, role, sendNotifications)

# gam <UserTypeEntity> delete calendaracls <UserCalendarEntity> [<CalendarACLRole>] <CalendarACLScopeEntity>
def deleteCalendarACLs(users):
  calendarEntity = getUserCalendarEntity()
  role, ACLScopeEntity = getCalendarDeleteACLsOptions(True)
  updateDeleteCalendarACLs(users, calendarEntity, 'delete', Act.MODIFIER_FROM, ACLScopeEntity, role, False)

# gam <UserTypeEntity> info calendaracls <UserCalendarEntity> <CalendarACLScopeEntity>
#	[formatjson]
def infoCalendarACLs(users):
  calendarEntity = getUserCalendarEntity()
  ACLScopeEntity = getCalendarSiteACLScopeEntity()
  FJQC = _getCalendarInfoACLOptions()
  i, count, users = getEntityArgument(users)
  for user in users:
    i += 1
    origUser = user
    user, cal, calIds, jcount = _validateUserGetCalendarIds(user, i, count, calendarEntity, Ent.CALENDAR_ACL, Act.MODIFIER_FROM, showAction=not FJQC.formatJSON)
    if jcount == 0:
      continue
    Ind.Increment()
    _doInfoCalendarACLs(origUser, user, cal, calIds, jcount, ACLScopeEntity, FJQC)
    Ind.Decrement()

# gam <UserTypeEntity> print calendaracls <UserCalendarEntity> [todrive <ToDriveAttribute>*]
#	[noselfowner] (addcsvdata <FieldName> <String>)*
#	[formatjson [quotechar <Character>]]
# gam <UserTypeEntity> show calendaracls <UserCalendarEntity>
#	[noselfowner]
#	[formatjson]
def printShowCalendarACLs(users):
  calendarEntity = getUserCalendarEntity(default='all')
  csvPF, FJQC, noSelfOwner, addCSVData = _getCalendarPrintShowACLOptions(['primaryEmail', 'calendarId'])
  i, count, users = getEntityArgument(users)
  for user in users:
    i += 1
    user, cal, calIds, jcount = _validateUserGetCalendarIds(user, i, count, calendarEntity, Ent.CALENDAR_ACL, Act.MODIFIER_FROM, showAction=not csvPF and not FJQC.formatJSON)
    if jcount == 0:
      continue
    Ind.Increment()
    j = 0
    for calId in calIds:
      j += 1
      calId = convertUIDtoEmailAddress(calId)
      _printShowCalendarACLs(cal, user, Ent.CALENDAR, calId, j, jcount, csvPF, FJQC, noSelfOwner, addCSVData)
    Ind.Decrement()
  if csvPF:
    csvPF.writeCSVfile('Calendar ACLs')

# gam <CalendarEntity> transfer ownership <UserItem>
def getCalendarSiteACLScopeEntity():
  ACLScopeEntity = {'list': getEntityList(Cmd.OB_ACL_SCOPE_ENTITY), 'dict': None}
  if isinstance(ACLScopeEntity['list'], dict):
    ACLScopeEntity['dict'] = ACLScopeEntity['list']
  return ACLScopeEntity

def getCalendarCreateUpdateACLsOptions(getScopeEntity):
  role = getChoice(CALENDAR_ACL_ROLES_MAP, mapChoice=True)
  ACLScopeEntity = getCalendarSiteACLScopeEntity() if getScopeEntity else getCalendarACLScope()
  sendNotifications = getCalendarACLSendNotifications()
  checkForExtraneousArguments()
  return (role, ACLScopeEntity, sendNotifications)

def getCalendarDeleteACLsOptions(getScopeEntity):
  rolesMap = CALENDAR_ACL_ROLES_MAP.copy()
  rolesMap['id'] = 'id'
  role = getChoice(rolesMap, defaultChoice=None, mapChoice=True)
  ACLScopeEntity = getCalendarSiteACLScopeEntity() if getScopeEntity else getCalendarACLScope()
  checkForExtraneousArguments()
  return (role, ACLScopeEntity)

def _doCalendarsCreateACLs(origUser, user, origCal, calIds, count, role, ACLScopeEntity, sendNotifications):
  i = 0
  for calId in calIds:
    i += 1
    calId, cal, ruleIds, jcount = _normalizeCalIdGetRuleIds(origUser, user, origCal, calId, i, count, ACLScopeEntity)
    if jcount == 0:
      continue
    _createCalendarACLs(cal, Ent.CALENDAR, calId, i, count, role, ruleIds, jcount, sendNotifications)

# gam calendar <CalendarEntity> create <CalendarACLRole> <CalendarACLScope> [sendnotifications <Boolean>]
def doCalendarsCreateACL(calIds):
  role, ACLScopeEntity, sendNotifications = getCalendarCreateUpdateACLsOptions(False)
  _doCalendarsCreateACLs(None, None, None, calIds, len(calIds), role, ACLScopeEntity, sendNotifications)

# gam calendars <CalendarEntity> create acls <CalendarACLRole> <CalendarACLScopeEntity> [sendnotifications <Boolean>]
def doCalendarsCreateACLs(calIds):
  role, ACLScopeEntity, sendNotifications = getCalendarCreateUpdateACLsOptions(True)
  _doCalendarsCreateACLs(None, None, None, calIds, len(calIds), role, ACLScopeEntity, sendNotifications)

def _doUpdateDeleteCalendarACLs(origUser, user, origCal, function, calIds, count, ACLScopeEntity, role, sendNotifications):
  i = 0
  for calId in calIds:
    i += 1
    calId, cal, ruleIds, jcount = _normalizeCalIdGetRuleIds(origUser, user, origCal, calId, i, count, ACLScopeEntity)
    if jcount == 0:
      continue
    _updateDeleteCalendarACLs(cal, function, Ent.CALENDAR, calId, i, count, role, ruleIds, jcount, sendNotifications)

# gam calendar <CalendarEntity> update <CalendarACLRole> <CalendarACLScope> [sendnotifications <Boolean>]
def doCalendarsUpdateACL(calIds):
  role, ACLScopeEntity, sendNotifications = getCalendarCreateUpdateACLsOptions(False)
  _doUpdateDeleteCalendarACLs(None, None, None, 'patch', calIds, len(calIds), ACLScopeEntity, role, sendNotifications)

# gam calendars <CalendarEntity> update acls <CalendarACLRole> <CalendarACLScopeEntity> [sendnotifications <Boolean>]
def doCalendarsUpdateACLs(calIds):
  role, ACLScopeEntity, sendNotifications = getCalendarCreateUpdateACLsOptions(True)
  _doUpdateDeleteCalendarACLs(None, None, None, 'patch', calIds, len(calIds), ACLScopeEntity, role, sendNotifications)

# gam calendar <CalendarEntity> delete [<CalendarACLRole>] <CalendarACLScope>
def doCalendarsDeleteACL(calIds):
  role, ACLScopeEntity = getCalendarDeleteACLsOptions(False)
  _doUpdateDeleteCalendarACLs(None, None, None, 'delete', calIds, len(calIds), ACLScopeEntity, role, False)

# gam calendars <CalendarEntity> delete acls <CalendarACLScopeEntity>
def doCalendarsDeleteACLs(calIds):
  role, ACLScopeEntity = getCalendarDeleteACLsOptions(True)
  _doUpdateDeleteCalendarACLs(None, None, None, 'delete', calIds, len(calIds), ACLScopeEntity, role, False)

def _doInfoCalendarACLs(origUser, user, origCal, calIds, count, ACLScopeEntity, FJQC):
  i = 0
  for calId in calIds:
    i += 1
    calId, cal, ruleIds, jcount = _normalizeCalIdGetRuleIds(origUser, user, origCal, calId, i, count, ACLScopeEntity, showAction=not FJQC.formatJSON)
    if jcount == 0:
      continue
    _infoCalendarACLs(cal, user, Ent.CALENDAR, calId, i, count, ruleIds, jcount, FJQC)

def _getCalendarInfoACLOptions():
  return FormatJSONQuoteChar(formatJSONOnly=True)

# gam calendars <CalendarEntity> info acl|acls <CalendarACLScopeEntity>
#	[formatjson]
def doCalendarsInfoACLs(calIds):
  ACLScopeEntity = getCalendarSiteACLScopeEntity()
  FJQC = _getCalendarInfoACLOptions()
  _doInfoCalendarACLs(None, None, None, calIds, len(calIds), ACLScopeEntity, FJQC)

def _printShowCalendarACLs(cal, user, entityType, calId, i, count, csvPF, FJQC, noSelfOwner, addCSVData):
  if csvPF:
    printGettingEntityItemForWhom(Ent.CALENDAR_ACL, calId, i, count)
  try:
    acls = callGAPIpages(cal.acl(), 'list', 'items',
                         throwReasons=[GAPI.NOT_FOUND, GAPI.FORBIDDEN, GAPI.AUTH_ERROR],
                         calendarId=calId, fields='nextPageToken,items(id,role,scope)')
  except (GAPI.forbidden, GAPI.authError) as e:
    entityActionFailedWarning([entityType, calId], str(e), i, count)
    return
  except GAPI.notFound:
    entityUnknownWarning(entityType, calId, i, count)
    return
  jcount = len(acls)
  if jcount == 0:
    setSysExitRC(NO_ENTITIES_FOUND_RC)
  if not csvPF:
    if not FJQC.formatJSON:
      if not noSelfOwner:
        entityPerformActionNumItems([entityType, calId], jcount, Ent.CALENDAR_ACL, i, count)
      else:
        entityPerformActionModifierNumItems([entityType, calId], Msg.MAXIMUM_OF, jcount, Ent.CALENDAR_ACL, i, count)
    Ind.Increment()
    j = 0
    for rule in acls:
      j += 1
      if noSelfOwner and rule['role'] == 'owner' and rule['scope']['value'] == calId:
        continue
      _showCalendarACL(user, entityType, calId, rule, j, jcount, FJQC)
    Ind.Decrement()
  else:
    if entityType == Ent.CALENDAR:
      if acls:
        for rule in acls:
          if noSelfOwner and rule['role'] == 'owner' and rule['scope']['value'] == calId:
            continue
          row = {'calendarId': calId}
          if user:
            row['primaryEmail'] = user
          if addCSVData:
            row.update(addCSVData)
          flattenJSON(rule, flattened=row)
          if not FJQC.formatJSON:
            csvPF.WriteRowTitles(row)
          elif csvPF.CheckRowTitles(row):
            row = {'calendarId': calId,
                   'JSON': json.dumps(cleanJSON(rule), ensure_ascii=False, sort_keys=False)}
            if user:
              row['primaryEmail'] = user
            if addCSVData:
              row.update(addCSVData)
            csvPF.WriteRowNoFilter(row)
      elif GC.Values[GC.CSV_OUTPUT_USERS_AUDIT] and user:
        csvPF.WriteRowNoFilter({'calendarId': calId, 'primaryEmail': user})
    else: # Ent.RESOURCE_CALENDAR
      for rule in acls:
        if noSelfOwner and rule['role'] == 'owner' and rule['scope']['value'] == calId:
          continue
        row = {'resourceId': user, 'resourceEmail': calId}
        if addCSVData:
          row.update(addCSVData)
        flattenJSON(rule, flattened=row)
        if not FJQC.formatJSON:
          csvPF.WriteRowTitles(row)
        elif csvPF.CheckRowTitles(row):
          row = {'resourceId': user, 'resourceEmail': calId,
                 'JSON': json.dumps(cleanJSON(rule), ensure_ascii=False, sort_keys=False)}
          if addCSVData:
            row.update(addCSVData)
          csvPF.WriteRowNoFilter(row)

def _getCalendarPrintShowACLOptions(titles):
  csvPF = CSVPrintFile(titles, 'sortall') if Act.csvFormat() else None
  FJQC = FormatJSONQuoteChar(csvPF)
  noSelfOwner = False
  addCSVData = {}
  while Cmd.ArgumentsRemaining():
    myarg = getArgument()
    if csvPF and myarg == 'todrive':
      csvPF.GetTodriveParameters()
    elif myarg == 'noselfowner':
      noSelfOwner = True
    elif csvPF and myarg == 'addcsvdata':
      getAddCSVData(addCSVData)
    else:
      FJQC.GetFormatJSONQuoteChar(myarg, True)
  if csvPF:
    if addCSVData:
      csvPF.AddTitles(sorted(addCSVData.keys()))
      if FJQC.formatJSON:
        csvPF.AddJSONTitles(sorted(addCSVData.keys()))
        csvPF.MoveJSONTitlesToEnd(['JSON'])
    csvPF.SetSortAllTitles()
  return (csvPF, FJQC, noSelfOwner, addCSVData)

# gam calendars <CalendarEntity> print acls [todrive <ToDriveAttribute>*]
#	[noselfowner] (addcsvdata <FieldName> <String>)*
#	[formatjson [quotechar <Character>]]
# gam calendars <CalendarEntity> show acls
#	[noselfowner]
#	[formatjson]
# gam calendar <CalendarEntity> printacl [todrive <ToDriveAttribute>*]
#	[noselfowner] (addcsvdata <FieldName> <String>)*
#	[formatjson]
# gam calendar <CalendarEntity> showacl
#	[noselfowner]
#	[formatjson]
def doCalendarsPrintShowACLs(calIds):
  csvPF, FJQC, noSelfOwner, addCSVData = _getCalendarPrintShowACLOptions(['calendarId'])
  count = len(calIds)
  i = 0
  for calId in calIds:
    i += 1
    calId, cal = validateCalendar(calId, i, count)
    if not cal:
      continue
    _printShowCalendarACLs(cal, None, Ent.CALENDAR, calId, i, count, csvPF, FJQC, noSelfOwner, addCSVData)
  if csvPF:
    csvPF.writeCSVfile('Calendar ACLs')

EVENT_TYPE_BIRTHDAY = 'birthday'
EVENT_TYPE_DEFAULT = 'default'
EVENT_TYPE_FOCUSTIME = 'focusTime'
EVENT_TYPE_FROMGMAIL = 'fromGmail'
EVENT_TYPE_OUTOFOFFICE = 'outOfOffice'
EVENT_TYPE_WORKINGLOCATION = 'workingLocation'

EVENT_TYPES_CHOICE_MAP = {
  'birthday': EVENT_TYPE_BIRTHDAY,
  'default': EVENT_TYPE_DEFAULT,
  'focustime': EVENT_TYPE_FOCUSTIME,
  'fromgmail': EVENT_TYPE_FROMGMAIL,
  'outofoffice': EVENT_TYPE_OUTOFOFFICE,
  'workinglocation': EVENT_TYPE_WORKINGLOCATION,
  }

EVENT_TYPE_PROPERTIES_NAME_MAP = {
  EVENT_TYPE_DEFAULT: None,
  EVENT_TYPE_FOCUSTIME: f'{EVENT_TYPE_FOCUSTIME}Properties',
  EVENT_TYPE_FROMGMAIL: None,
  EVENT_TYPE_OUTOFOFFICE: f'{EVENT_TYPE_OUTOFOFFICE}Properties',
  EVENT_TYPE_WORKINGLOCATION: f'{EVENT_TYPE_WORKINGLOCATION}Properties',
  }

EVENT_TYPE_ENTITY_MAP = {
  EVENT_TYPE_BIRTHDAY: Ent.EVENT_BIRTHDAY,
  EVENT_TYPE_DEFAULT: None,
  EVENT_TYPE_FOCUSTIME: Ent.EVENT_FOCUSTIME,
  EVENT_TYPE_FROMGMAIL: None,
  EVENT_TYPE_OUTOFOFFICE: Ent.EVENT_OUTOFOFFICE,
  EVENT_TYPE_WORKINGLOCATION: Ent.EVENT_WORKINGLOCATION,
  }

def _normalizeResourceIdGetRuleIds(cd, resourceId, i, count, ACLScopeEntity, showAction=True):
  calId = _validateResourceId(cd, resourceId, i, count, False)
  if not calId:
    return (None, None, 0)
  if ACLScopeEntity['dict']:
    ruleIds = ACLScopeEntity['dict'][resourceId]
  else:
    ruleIds = ACLScopeEntity['list']
  jcount = len(ruleIds)
  if showAction:
    entityPerformActionNumItems([Ent.RESOURCE_CALENDAR, resourceId], jcount, Ent.CALENDAR_ACL, i, count)
  if jcount == 0:
    setSysExitRC(NO_ENTITIES_FOUND_RC)
  return (calId, ruleIds, jcount)

# gam resource <ResourceID> create calendaracls <CalendarACLRole> <CalendarACLScopeEntity> [sendnotifications <Boolean>]
# gam resources <ResourceEntity> create calendaracls <CalendarACLRole> <CalendarACLScopeEntity> [sendnotifications <Boolean>]
def doResourceCreateCalendarACLs(entityList):
  cal = buildGAPIObject(API.CALENDAR)
  cd = buildGAPIObject(API.DIRECTORY)
  role, ACLScopeEntity, sendNotifications = getCalendarCreateUpdateACLsOptions(True)
  i = 0
  count = len(entityList)
  for resourceId in entityList:
    i += 1
    calId, ruleIds, jcount = _normalizeResourceIdGetRuleIds(cd, resourceId, i, count, ACLScopeEntity)
    if jcount == 0:
      continue
    _createCalendarACLs(cal, Ent.RESOURCE_CALENDAR, calId, i, count, role, ruleIds, jcount, sendNotifications)

def _resourceUpdateDeleteCalendarACLs(entityList, function, ACLScopeEntity, role, sendNotifications):
  cal = buildGAPIObject(API.CALENDAR)
  cd = buildGAPIObject(API.DIRECTORY)
  i = 0
  count = len(entityList)
  for resourceId in entityList:
    i += 1
    calId, ruleIds, jcount = _normalizeResourceIdGetRuleIds(cd, resourceId, i, count, ACLScopeEntity)
    if jcount == 0:
      continue
    _updateDeleteCalendarACLs(cal, function, Ent.RESOURCE_CALENDAR, calId, i, count, role, ruleIds, jcount, sendNotifications)

# gam resource <ResourceID> update calendaracls <CalendarACLRole> <CalendarACLScopeEntity> [sendnotifications <Boolean>]
# gam resources <ResourceEntity> update calendaracls <CalendarACLRole> <CalendarACLScopeEntity> [sendnotifications <Boolean>]
def doResourceUpdateCalendarACLs(entityList):
  role, ACLScopeEntity, sendNotifications = getCalendarCreateUpdateACLsOptions(True)
  _resourceUpdateDeleteCalendarACLs(entityList, 'patch', ACLScopeEntity, role, sendNotifications)

# gam resource <ResourceID> delete calendaracls [<CalendarACLRole>] <CalendarACLScopeEntity>
# gam resources <ResourceEntity> delete calendaracls [<CalendarACLRole>] <CalendarACLScopeEntity>
def doResourceDeleteCalendarACLs(entityList):
  role, ACLScopeEntity = getCalendarDeleteACLsOptions(True)
  _resourceUpdateDeleteCalendarACLs(entityList, 'delete', ACLScopeEntity, role, False)

# gam resource <ResourceID> info calendaracls <CalendarACLScopeEntity>
#	[formatjson]
# gam resources <ResourceEntity> info calendaracls <CalendarACLScopeEntity>
#	[formatjson]
def doResourceInfoCalendarACLs(entityList):
  cal = buildGAPIObject(API.CALENDAR)
  cd = buildGAPIObject(API.DIRECTORY)
  ACLScopeEntity = getCalendarSiteACLScopeEntity()
  FJQC = _getCalendarInfoACLOptions()
  i = 0
  count = len(entityList)
  for resourceId in entityList:
    i += 1
    calId, ruleIds, jcount = _normalizeResourceIdGetRuleIds(cd, resourceId, i, count, ACLScopeEntity, showAction=not FJQC.formatJSON)
    if jcount == 0:
      continue
    _infoCalendarACLs(cal, resourceId, Ent.RESOURCE_CALENDAR, calId, i, count, ruleIds, jcount, FJQC)

# gam resource <ResourceID> print calendaracls [todrive <ToDriveAttribute>*]
#	[noselfowner] (addcsvdata <FieldName> <String>)*
#	[formatjson [quotechar <Character>]]
# gam resources <ResourceEntity> print calendaracls [todrive <ToDriveAttribute>*]
#	[noselfowner] (addcsvdata <FieldName> <String>)*
#	[formatjson [quotechar <Character>]]
# gam resource <ResourceID> show calendaracls
#	[noselfowner]
#	[formatjson]
# gam resources <ResourceEntity> show calendaracls
#	[noselfowner]
#	[formatjson]
def doResourcePrintShowCalendarACLs(entityList):
  cal = buildGAPIObject(API.CALENDAR)
  cd = buildGAPIObject(API.DIRECTORY)
  csvPF, FJQC, noSelfOwner, addCSVData = _getCalendarPrintShowACLOptions(['resourceId', 'resourceEmail'])
  i = 0
  count = len(entityList)
  for resourceId in entityList:
    i += 1
    calId = _validateResourceId(cd, resourceId, i, count, False)
    if not calId:
      continue
    _printShowCalendarACLs(cal, resourceId, Ent.RESOURCE_CALENDAR, calId, i, count, csvPF, FJQC, noSelfOwner, addCSVData)
  if csvPF:
    csvPF.writeCSVfile('Resource Calendar ACLs')


