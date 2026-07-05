"""GAM calendar list commands (create, info, print, etc.)."""

import json

from gamlib import api as API
from gamlib import gapi as GAPI
from gamlib import msgs as Msg
from gamlib import settings as GC
from gam.var import Act, Cmd, Ent, Ind
from gam.util.access import checkEntityAFDNEorAccessErrorExit
from gam.util.api import buildGAPIObject
from gam.util.api_call import callGAPI, callGAPIpages
from gam.util.args import (
    CALENDAR_COLOR_MAP,
    getArgument, checkArgumentPresent, checkForExtraneousArguments,
    getBoolean, getCalendarReminder, getCharacter, getChoice,
    getColor, getEmailAddress, getInteger, getString, splitEmailAddress,
)
from gam.util.csv_pf import (
    CSVPrintFile, FormatJSONQuoteChar, _getFieldsList, cleanJSON,
    flattenJSON, getFieldsList, getFieldsFromFieldsList, getItemFieldsFromFieldsList,
)
from gam.util.display import (
    entityActionFailedWarning, entityActionPerformed,
    entityModifierNewValueActionFailedWarning, entityPerformActionModifierNewValue,
    entityPerformActionNumItems, entityPerformActionSubItemModifierNumItems,
    entityPerformActionSubItemModifierNumItemsModifierNewValue,
    printEntitiesCount, printGettingEntityItemForWhom,
    printKeyValueList, printKeyValueListWithCount, printLine,
    userCalServiceNotEnabledWarning,
)
from gam.util.entity import convertEntityToList, getEntityList, getEntityArgument, getEntitySelection, getEntitySelector
from gam.util.errors import invalidChoiceExit, unknownArgumentExit
from gam.util.output import setSysExitRC
from gam.constants import NO_ENTITIES_FOUND_RC

from gam.cmd.calendar.core import checkCalendarExists, validateCalendar, normalizeCalendarId, CALENDAR_ACL_ROLES_MAP
from gam.cmd.calendar.core import (
    ACLRuleKeyValueList,
    CALENDAR_MIN_COLOR_INDEX,
    CALENDAR_MAX_COLOR_INDEX,
    _showCalendarSettings,
    getCalendarSettings,
)
from gam.cmd.courses.courses import _getCourseStates, _getCoursesInfo, _initCourseShowProperties


def _getCalendarSelectProperty(myarg, kwargs):
  if myarg == 'minaccessrole':
    kwargs['minAccessRole'] = getChoice(CALENDAR_ACL_ROLES_MAP, mapChoice=True)
  elif myarg == 'showdeleted':
    kwargs['showDeleted'] = True
  elif myarg == 'showhidden':
    kwargs['showHidden'] = True
  else:
    return False
  return True

def initUserCalendarEntity():
  return {'list': [], 'kwargs': {}, 'dict': None, 'all': False, 'primary': False, 'resourceIds': []}

def getUserCalendarEntity(default='primary', noSelectionKwargs=None):

  def _initCourseCalendarSelectionParameters():
    return {'courseIds': [], 'teacherId': None, 'myCoursesAsTeacher': False,
            'studentId': None, 'myCoursesAsStudent': False, 'courseStates': []}

  def _getCourseCalendarSelectionParameters(myarg):
    if myarg in {'course', 'courses', 'class', 'classes'}:
      courseSelectionParameters['courseIds'].extend(getEntityList(Cmd.OB_COURSE_ENTITY, shlexSplit=True))
    elif myarg == 'courseswithteacher':
      courseSelectionParameters['teacherId'] = getEmailAddress()
      courseSelectionParameters['myCoursesAsTeacher'] = False
    elif myarg == 'mycoursesasteacher':
      courseSelectionParameters['myCoursesAsTeacher'] = True
      courseSelectionParameters['teacherId'] = None
    elif myarg == 'courseswithstudent':
      courseSelectionParameters['studentId'] = getEmailAddress()
      courseSelectionParameters['myCoursesAsStudent'] = False
    elif myarg == 'mycoursesasstudent':
      courseSelectionParameters['myCoursesAsStudent'] = True
      courseSelectionParameters['studentId'] = None
    elif myarg in {'coursestate', 'coursestates', 'coursestatus'}:
      _getCourseStates(Cmd.OB_COURSE_STATE_LIST, courseSelectionParameters['courseStates'])
    else:
      return False
    return True

  def _noSelectionMade():
    return (not calendarEntity['list'] and not calendarEntity['kwargs'] and calendarEntity['dict'] is None and
            not calendarEntity['all'] and not calendarEntity['primary'] and not calendarEntity['resourceIds'] and
            not courseCalendarSelected)

  calendarEntity = initUserCalendarEntity()
  courseSelectionParameters = _initCourseCalendarSelectionParameters()
  courseCalendarSelected = False
  while Cmd.ArgumentsRemaining():
    myarg = getArgument()
    if myarg in {'calendar', 'calendars'}:
      entitySelector = getEntitySelector()
      if entitySelector:
        entityList = getEntitySelection(entitySelector, False)
        if isinstance(entityList, dict):
          calendarEntity['dict'] = entityList
        else:
          calendarEntity['list'] = entityList
      else:
        calendarEntity['list'].extend(convertEntityToList(getString(Cmd.OB_EMAIL_ADDRESS_LIST)))
    elif myarg == 'allcalendars':
      calendarEntity['all'] = True
    elif myarg == 'primary':
      calendarEntity['primary'] = True
    elif _getCalendarSelectProperty(myarg, calendarEntity['kwargs']):
      pass
    elif myarg == 'resource':
      calendarEntity['resourceIds'].append(getString(Cmd.OB_RESOURCE_ID))
    elif myarg == 'resources':
      calendarEntity['resourceIds'].extend(convertEntityToList(getString(Cmd.OB_RESOURCE_ID, minLen=0), shlexSplit=True))
    elif _getCourseCalendarSelectionParameters(myarg):
      courseCalendarSelected = True
    elif _noSelectionMade() and (myarg.find('@') != -1 or myarg.find('id:') != -1):
      Cmd.Backup()
      calendarEntity['list'].append(getEmailAddress())
    else:
      Cmd.Backup()
      break
  if _noSelectionMade():
    if not noSelectionKwargs:
      calendarEntity[default] = True
    else:
      calendarEntity['all'] = True
      calendarEntity['kwargs'].update(noSelectionKwargs)
  elif (courseCalendarSelected and
        (courseSelectionParameters['courseIds'] or
         courseSelectionParameters['teacherId'] or courseSelectionParameters['myCoursesAsTeacher'] or
         courseSelectionParameters['studentId'] or courseSelectionParameters['myCoursesAsStudent'])):
    calendarEntity['courseSelectionParameters'] = courseSelectionParameters
    calendarEntity['courseShowProperties'] = _initCourseShowProperties(['calendarId'])
    calendarEntity['croom'] = buildGAPIObject(API.CLASSROOM)
  return calendarEntity

def _validateUserGetCalendarIds(user, i, count, calendarEntity,
                                itemType=None, modifier=None, showAction=True, setRC=True, newCalId=None, secondaryCalendarsOnly=False):
  if user and calendarEntity['dict']:
    calIds = calendarEntity['dict'][user][:]
  else:
    calIds = calendarEntity['list'][:]
  user, cal = validateCalendar(user, i, count, noClientAccess=True)
  if not cal:
    return (user, None, None, 0)
  if calendarEntity['resourceIds']:
    cd = buildGAPIObject(API.DIRECTORY)
    for resourceId in calendarEntity['resourceIds']:
      try:
        calIds.append(callGAPI(cd.resources().calendars(), 'get',
                               throwReasons=[GAPI.BAD_REQUEST, GAPI.RESOURCE_NOT_FOUND, GAPI.FORBIDDEN],
                               customer=GC.Values[GC.CUSTOMER_ID], calendarResourceId=resourceId,
                               fields='resourceEmail')['resourceEmail'])
      except (GAPI.badRequest, GAPI.resourceNotFound, GAPI.forbidden):
        checkEntityAFDNEorAccessErrorExit(cd, Ent.RESOURCE_CALENDAR, resourceId, i, count)
        return (user, None, None, 0)
  courseSelectionParameters = calendarEntity.get('courseSelectionParameters')
  if courseSelectionParameters is not None:
    if courseSelectionParameters['myCoursesAsTeacher']:
      courseSelectionParameters['teacherId'] = user
    if courseSelectionParameters['myCoursesAsStudent']:
      courseSelectionParameters['studentId'] = user
    coursesInfo = _getCoursesInfo(calendarEntity['croom'], courseSelectionParameters,
                                  calendarEntity['courseShowProperties'])
    if coursesInfo is None:
      return (user, None, None, 0)
    calIds.extend([course['calendarId'] for course in coursesInfo if 'calendarId' in course])
  if calendarEntity['primary']:
    calIds.append(user)
  try:
    if calendarEntity['kwargs'] or calendarEntity['all']:
      result = callGAPIpages(cal.calendarList(), 'list', 'items',
                             throwReasons=GAPI.CALENDAR_THROW_REASONS,
                             fields='nextPageToken,items/id', **calendarEntity['kwargs'])
      calIds.extend([calId['id'] for calId in result if not secondaryCalendarsOnly or calId['id'].find('@group.calendar.google.com') != -1])
    else:
      callGAPI(cal.calendars(), 'get',
               throwReasons=GAPI.CALENDAR_THROW_REASONS,
               calendarId='primary', fields='')
  except GAPI.notACalendarUser:
    userCalServiceNotEnabledWarning(user, i, count)
    return (user, None, None, 0)
  if newCalId:
    newcal = buildGAPIObject(API.CALENDAR)
    if not checkCalendarExists(newcal, newCalId, i, count):
      entityActionFailedWarning([Ent.USER, user, Ent.CALENDAR, newCalId], Msg.DOES_NOT_EXIST, i, count)
      return (user, None, None, 0)
  jcount = len(calIds)
  if setRC and jcount == 0:
    setSysExitRC(NO_ENTITIES_FOUND_RC)
  if showAction:
    if not itemType:
      entityPerformActionNumItems([Ent.USER, user], jcount, Ent.CALENDAR, i, count)
    elif not newCalId:
      entityPerformActionSubItemModifierNumItems([Ent.USER, user], itemType, modifier, jcount, Ent.CALENDAR, i, count)
    else:
      entityPerformActionSubItemModifierNumItemsModifierNewValue([Ent.USER, user], itemType, modifier, jcount, Ent.CALENDAR, Act.MODIFIER_TO, newCalId, i, count)
  return (user, cal, calIds, jcount)

CALENDAR_NOTIFICATION_METHODS = ['email']
CALENDAR_NOTIFICATION_TYPES_MAP = {
  'eventcreation': 'eventCreation',
  'eventchange': 'eventChange',
  'eventcancellation': 'eventCancellation',
  'eventresponse': 'eventResponse',
  'agenda': 'agenda',
  }

def _getCalendarAttributes(body, returnOnUnknownArgument=False):
  while Cmd.ArgumentsRemaining():
    myarg = getArgument()
    if myarg == 'selected':
      body['selected'] = getBoolean()
    elif myarg == 'hidden':
      body['hidden'] = getBoolean()
    elif myarg == 'summary':
      body['summaryOverride'] = getString(Cmd.OB_STRING)
    elif myarg in {'color', 'colour'}:
      body['colorId'] = getChoice(CALENDAR_COLOR_MAP, mapChoice=True)
    elif myarg in {'colorindex', 'colorid', 'colourindex', 'colourid'}:
      body['colorId'] = getInteger(minVal=CALENDAR_MIN_COLOR_INDEX, maxVal=CALENDAR_MAX_COLOR_INDEX)
    elif myarg in {'backgroundcolor', 'backgroundcolour'}:
      body['backgroundColor'] = getColor()
      body.setdefault('foregroundColor', '#000000')
    elif myarg in {'foregroundcolor', 'foregroundcolour'}:
      body['foregroundColor'] = getColor()
    elif myarg == 'reminder':
      body.setdefault('defaultReminders', [])
      if not checkArgumentPresent(Cmd.CLEAR_NONE_ARGUMENT):
        body['defaultReminders'].append(getCalendarReminder(True))
    elif myarg == 'notification':
      body.setdefault('notificationSettings', {'notifications': []})
      method = getChoice(CALENDAR_NOTIFICATION_METHODS+Cmd.CLEAR_NONE_ARGUMENT)
      if method not in Cmd.CLEAR_NONE_ARGUMENT:
        for ntype in _getFieldsList():
          if ntype in CALENDAR_NOTIFICATION_TYPES_MAP:
            body['notificationSettings']['notifications'].append({'method': method,
                                                                  'type': CALENDAR_NOTIFICATION_TYPES_MAP[ntype]})
          else:
            invalidChoiceExit(ntype, CALENDAR_NOTIFICATION_TYPES_MAP, True)
      else:
        body['notificationSettings']['notifications'] = []
    elif returnOnUnknownArgument:
      Cmd.Backup()
      return
    else:
      unknownArgumentExit()

def _showCalendar(calendar, j, jcount, FJQC, acls=None):
  if FJQC.formatJSON:
    if acls:
      calendar['acls'] = [{'id': rule['id'], 'role': rule['role']} for rule in acls]
    printLine(json.dumps(cleanJSON(calendar), ensure_ascii=False, sort_keys=True))
    return
  _showCalendarSettings(calendar, j, jcount)
  Ind.Increment()
  if 'primary' in calendar:
    printKeyValueList(['Primary', calendar['primary']])
  if 'dataOwner' in calendar:
    printKeyValueList(['Owner', calendar['dataOwner']])
  if 'accessRole' in calendar:
    printKeyValueList(['Access Level', calendar['accessRole']])
  if 'deleted' in calendar:
    printKeyValueList(['Deleted', calendar['deleted']])
  if 'hidden' in calendar:
    printKeyValueList(['Hidden', calendar['hidden']])
  if 'selected' in calendar:
    printKeyValueList(['Selected', calendar['selected']])
  if 'colorId' in calendar:
    printKeyValueList(['Color ID', calendar['colorId'], 'Background Color', calendar['backgroundColor'], 'Foreground Color', calendar['foregroundColor']])
  if 'defaultReminders' in calendar:
    printKeyValueList(['Default Reminders', None])
    Ind.Increment()
    for reminder in calendar['defaultReminders']:
      printKeyValueList(['Method', reminder['method'], 'Minutes', reminder['minutes']])
    Ind.Decrement()
  if 'notificationSettings' in calendar:
    printKeyValueList(['Notifications', None])
    Ind.Increment()
    for notification in calendar['notificationSettings'].get('notifications', []):
      printKeyValueList(['Method', notification['method'], 'Type', notification['type']])
    Ind.Decrement()
  if acls:
    j = 0
    jcount = len(acls)
    printEntitiesCount(Ent.CALENDAR_ACL, acls)
    Ind.Increment()
    for rule in acls:
      j += 1
      printKeyValueListWithCount(ACLRuleKeyValueList(rule), j, jcount)
    Ind.Decrement()
  Ind.Decrement()

# Process CalendarList functions
def _processCalendarList(user, i, count, calId, j, jcount, cal, function, **kwargs):
  try:
    callGAPI(cal.calendarList(), function,
             throwReasons=[GAPI.NOT_FOUND, GAPI.DUPLICATE, GAPI.UNKNOWN_ERROR,
                           GAPI.CANNOT_CHANGE_OWN_ACL, GAPI.CANNOT_CHANGE_OWN_PRIMARY_SUBSCRIPTION,
                           GAPI.CANNOT_UNSUBSCRIBE_FROM_OWNED_CALENDAR],
             **kwargs)
    entityActionPerformed([Ent.USER, user, Ent.CALENDAR, calId], j, jcount)
  except (GAPI.notFound, GAPI.duplicate, GAPI.unknownError, GAPI.serviceNotAvailable,
          GAPI.cannotChangeOwnAcl, GAPI.cannotChangeOwnPrimarySubscription,
          GAPI.cannotUnsubscribeFromOwnedCalendar) as e:
    entityActionFailedWarning([Ent.USER, user, Ent.CALENDAR, calId], str(e), j, jcount)
  except GAPI.notACalendarUser:
    userCalServiceNotEnabledWarning(user, i, count)

# gam <UserTypeEntity> add calendars <UserCalendarAddEntity> <CalendarAttribute>*
def addCalendars(users):
  calendarEntity = getUserCalendarEntity()
  body = {'selected': True, 'hidden': False}
  _getCalendarAttributes(body)
  colorRgbFormat = 'backgroundColor' in body or 'foregroundColor' in body
  i, count, users = getEntityArgument(users)
  for user in users:
    i += 1
    user, cal, calIds, jcount = _validateUserGetCalendarIds(user, i, count, calendarEntity)
    if jcount == 0:
      continue
    Ind.Increment()
    j = 0
    for calId in calIds:
      j += 1
      body['id'] = calId = normalizeCalendarId(calId, user)
      _processCalendarList(user, i, count, calId, j, jcount, cal, 'insert',
                           body=body, colorRgbFormat=colorRgbFormat, fields='')
    Ind.Decrement()

def _updateDeleteCalendars(users, calendarEntity, function, **kwargs):
  i, count, users = getEntityArgument(users)
  for user in users:
    i += 1
    user, cal, calIds, jcount = _validateUserGetCalendarIds(user, i, count, calendarEntity)
    if jcount == 0:
      continue
    Ind.Increment()
    j = 0
    for calId in calIds:
      j += 1
      calId = normalizeCalendarId(calId, user)
      _processCalendarList(user, i, count, calId, j, jcount, cal, function,
                           calendarId=calId, **kwargs)
    Ind.Decrement()

# gam <UserTypeEntity> update calendars <UserCalendarEntity> <CalendarAttribute>+
def updateCalendars(users):
  calendarEntity = getUserCalendarEntity()
  body = {}
  _getCalendarAttributes(body)
  colorRgbFormat = 'backgroundColor' in body or 'foregroundColor' in body
  _updateDeleteCalendars(users, calendarEntity, 'patch', body=body, colorRgbFormat=colorRgbFormat, fields='')

# gam <UserTypeEntity> delete calendars <UserCalendarEntity>
def deleteCalendars(users):
  calendarEntity = getUserCalendarEntity()
  checkForExtraneousArguments()
  _updateDeleteCalendars(users, calendarEntity, 'delete')


# gam <UserTypeEntity> create calendars <CalendarSettings>
def createCalendar(users):
  calendarEntity = initUserCalendarEntity()
  body = getCalendarSettings(summaryRequired=True)
  i, count, users = getEntityArgument(users)
  for user in users:
    i += 1
    user, cal, _, _ = _validateUserGetCalendarIds(user, i, count, calendarEntity, showAction=False, setRC=False)
    if not cal:
      continue
    try:
      calId = callGAPI(cal.calendars(), 'insert',
                       throwReasons=GAPI.CALENDAR_THROW_REASONS+[GAPI.FORBIDDEN],
                       body=body, fields='id')['id']
      entityActionPerformed([Ent.USER, user, Ent.CALENDAR, calId], i, count)
    except GAPI.forbidden as e:
      entityActionFailedWarning([Ent.USER, user], str(e), i, count)
    except GAPI.notACalendarUser:
      userCalServiceNotEnabledWarning(user, i, count)

def addCreateCalendars(users):
  if Act.Get() == Act.ADD:
    addCalendars(users)
  else:
    createCalendar(users)

def _modifyRemoveCalendars(users, calendarEntity, function, **kwargs):
  i, count, users = getEntityArgument(users)
  for user in users:
    i += 1
    user, cal, calIds, jcount = _validateUserGetCalendarIds(user, i, count, calendarEntity)
    if jcount == 0:
      continue
    Ind.Increment()
    j = 0
    for calId in calIds:
      j += 1
      calId = normalizeCalendarId(calId, user)
      try:
        callGAPI(cal.calendars(), function,
                 throwReasons=GAPI.CALENDAR_THROW_REASONS+[GAPI.NOT_FOUND, GAPI.CANNOT_DELETE_PRIMARY_CALENDAR,
                                                           GAPI.FORBIDDEN, GAPI.INVALID, GAPI.REQUIRED_ACCESS_LEVEL],
                 calendarId=calId, **kwargs)
        entityActionPerformed([Ent.USER, user, Ent.CALENDAR, calId], j, jcount)
      except (GAPI.notFound, GAPI.cannotDeletePrimaryCalendar, GAPI.forbidden, GAPI.invalid, GAPI.requiredAccessLevel) as e:
        entityActionFailedWarning([Ent.USER, user, Ent.CALENDAR, calId], str(e), j, jcount)
      except GAPI.notACalendarUser:
        userCalServiceNotEnabledWarning(user, i, count)
        break
    Ind.Decrement()

# gam <UserTypeEntity> modify calendars <UserCalendarEntity> <CalendarSettings>
def modifyCalendars(users):
  calendarEntity = getUserCalendarEntity()
  body = getCalendarSettings(summaryRequired=False)
  _modifyRemoveCalendars(users, calendarEntity, 'patch', body=body)

# gam <UserTypeEntity> remove calendars <UserCalendarEntity>
def removeCalendars(users):
  calendarEntity = getUserCalendarEntity()
  checkForExtraneousArguments()
  _modifyRemoveCalendars(users, calendarEntity, 'delete')

def _getCalendarPermissions(cal, calendar):
  if calendar['accessRole'] == 'owner':
    try:
      return callGAPIpages(cal.acl(), 'list', 'items',
                           throwReasons=GAPI.CALENDAR_THROW_REASONS+[GAPI.NOT_FOUND],
                           calendarId=calendar['id'], fields='nextPageToken,items(id,role,scope)')
    except (GAPI.notACalendarUser, GAPI.notFound):
      pass
  return []

CALENDAR_LIST_FIELDS_CHOICE_MAP = {
  'accessrole': 'accessRole',
  'backgroundcolor': 'backgroundColor',
  'backgroundcolour': 'backgroundColor',
  'colorid': 'colorId',
  'conferenceproperties': 'conferenceProperties',
  'dataowner': 'dataOwner',
  'defaultreminders': 'defaultReminders',
  'deleted': 'deleted',
  'description': 'description',
  'foregroundcolor': 'foregroundColor',
  'foregroundcolour': 'foregroundColor',
  'hidden': 'hidden',
  'id': 'id',
  'location': 'location',
  'notificationsettings': 'notificationSettings',
  'primary': 'primary',
  'selected': 'selected',
  'summary': ['summary', 'summaryOverride'],
  'summaryoverride': ['summary', 'summaryOverride'],
  'timezone': 'timeZone',
   }

# gam <UserTypeEntity> info calendars <UserCalendarEntity>
#	[fields <CalendarFieldList>]  [permissions]
#	[formatjson]
def infoCalendars(users):
  calendarEntity = getUserCalendarEntity()
  FJQC = FormatJSONQuoteChar()
  fieldsList = []
  acls = []
  getCalPermissions = False
  while Cmd.ArgumentsRemaining():
    myarg = getArgument()
    if myarg in [Cmd.ARG_ACLS, Cmd.ARG_CALENDARACLS, Cmd.ARG_PERMISSIONS]:
      getCalPermissions = True
    elif getFieldsList(myarg, CALENDAR_LIST_FIELDS_CHOICE_MAP, fieldsList, initialField='id'):
      pass
    else:
      FJQC.GetFormatJSON(myarg)
  if fieldsList:
    if getCalPermissions:
      fieldsList.append('accessRole')
  fields = getFieldsFromFieldsList(fieldsList)
  i, count, users = getEntityArgument(users)
  for user in users:
    i += 1
    user, cal, calIds, jcount = _validateUserGetCalendarIds(user, i, count, calendarEntity, showAction=not FJQC.formatJSON)
    if jcount == 0:
      continue
    Ind.Increment()
    j = 0
    for calId in calIds:
      j += 1
      calId = normalizeCalendarId(calId, user)
      try:
        result = callGAPI(cal.calendarList(), 'get',
                          throwReasons=GAPI.CALENDAR_THROW_REASONS+[GAPI.NOT_FOUND],
                          calendarId=calId, fields=fields)
        if getCalPermissions:
          acls = _getCalendarPermissions(cal, result)
        _showCalendar(result, j, jcount, FJQC, acls)
      except GAPI.notFound as e:
        entityActionFailedWarning([Ent.USER, user, Ent.CALENDAR, calId], str(e), j, jcount)
      except GAPI.notACalendarUser:
        userCalServiceNotEnabledWarning(user, i, count)
        break
    Ind.Decrement()

CALENDAR_SIMPLE_LISTS = {'allowedConferenceSolutionTypes'}
CALENDAR_EXCLUDE_OPTIONS = {'noprimary', 'nogroups', 'noresources', 'nosystem', 'nousers'}
CALENDAR_EXCLUDE_DOMAINS = {
  'nogroups': 'group.calendar.google.com',
  'noresources': 'resource.calendar.google.com',
  'nosystem': 'group.v.calendar.google.com',
  }

# gam <UserTypeEntity> print calendars <UserCalendarEntity> [todrive <ToDriveAttribute>*]
#	[primary] <CalendarSelectProperty>* [noprimary] [nogroups] [noresources] [nosystem] [nousers]
#	[fields <CalendarFieldList>] [permissions] [oneitemperrow]
#	[formatjson [quotechar <Character>]] [delimiter <Character>]
# gam <UserTypeEntity> show calendars <UserCalendarEntity>
#	[primary] <CalendarSelectProperty>* [noprimary] [nogroups] [noresources] [nosystem] [nousers]
#	[fields <CalendarFieldList>] [permissions]
#	[formatjson]
def printShowCalendars(users):
  acls = []
  getCalPermissions = oneItemPerRow = noPrimary = primaryOnly = False
  excludes = set()
  excludeDomains = set()
  csvPF = CSVPrintFile(['primaryEmail', 'calendarId'], 'sortall') if Act.csvFormat() else None
  FJQC = FormatJSONQuoteChar(csvPF)
  kwargs = {}
  delimiter = GC.Values[GC.CSV_OUTPUT_FIELD_DELIMITER]
  fieldsList = []
  while Cmd.ArgumentsRemaining():
    myarg = getArgument()
    if csvPF and myarg == 'todrive':
      csvPF.GetTodriveParameters()
    elif myarg in [Cmd.ARG_ACLS, Cmd.ARG_CALENDARACLS, Cmd.ARG_PERMISSIONS]:
      getCalPermissions = True
    elif myarg == 'oneitemperrow':
      oneItemPerRow = True
    elif myarg == 'allcalendars':
      pass
    elif myarg == 'primary':
      primaryOnly = True
    elif _getCalendarSelectProperty(myarg, kwargs):
      pass
    elif myarg in CALENDAR_EXCLUDE_OPTIONS:
      excludes.add(myarg)
    elif myarg == 'delimiter':
      delimiter = getCharacter()
    elif getFieldsList(myarg, CALENDAR_LIST_FIELDS_CHOICE_MAP, fieldsList, initialField='id'):
      pass
    else:
      FJQC.GetFormatJSONQuoteChar(myarg, True)
  for exclude in excludes:
    if exclude == 'noprimary':
      noPrimary = True
    elif exclude == 'nousers':
      excludeDomains.add(GC.Values[GC.DOMAIN])
    else:
      excludeDomains.add(CALENDAR_EXCLUDE_DOMAINS[exclude])
  if fieldsList:
    if getCalPermissions:
      fieldsList.append('accessRole')
    if noPrimary or primaryOnly:
      fieldsList.append('primary')
  fields = getItemFieldsFromFieldsList('items', fieldsList)
  i, count, users = getEntityArgument(users)
  for user in users:
    i += 1
    user, cal = validateCalendar(user, i, count, noClientAccess=True)
    if not cal:
      continue
    if csvPF:
      printGettingEntityItemForWhom(Ent.CALENDAR, user, i, count)
    try:
      calendars = callGAPIpages(cal.calendarList(), 'list', 'items',
                                throwReasons=GAPI.CALENDAR_THROW_REASONS,
                                fields=fields, **kwargs)
    except GAPI.notACalendarUser:
      userCalServiceNotEnabledWarning(user, i, count)
      continue
    if primaryOnly:
      for calendar in calendars:
        if calendar.get('primary', False):
          calendars = [calendar]
          break
      else:
        calendars = []
    elif noPrimary or excludeDomains:
      allCalendars = calendars[:]
      calendars = []
      for calendar in allCalendars:
        primary = calendar.get('primary', False)
        if noPrimary and primary:
          continue
        if not primary and excludeDomains:
          _, domain = splitEmailAddress(calendar['id'])
          if domain in excludeDomains:
            continue
        calendars.append(calendar)
    if not csvPF:
      jcount = len(calendars)
      if not FJQC.formatJSON:
        entityPerformActionNumItems([Ent.USER, user], jcount, Ent.CALENDAR, i, count)
      Ind.Increment()
      j = 0
      for calendar in calendars:
        j += 1
        if getCalPermissions:
          acls = _getCalendarPermissions(cal, calendar)
        _showCalendar(calendar, j, jcount, FJQC, acls)
      Ind.Decrement()
    elif calendars:
      if not getCalPermissions or not oneItemPerRow:
        for calendar in calendars:
          row = {'primaryEmail': user, 'calendarId': calendar['id']}
          if getCalPermissions:
            calPerms = _getCalendarPermissions(cal, calendar)
            flattenJSON({'permissions': calPerms}, flattened=row)
          flattenJSON(calendar, flattened=row, simpleLists=CALENDAR_SIMPLE_LISTS, delimiter=delimiter)
          if not FJQC.formatJSON:
            row.pop('id')
            csvPF.WriteRowTitles(row)
          elif csvPF.CheckRowTitles(row):
            if getCalPermissions:
              calendar.update({'permissions': calPerms})
            csvPF.WriteRowNoFilter({'primaryEmail': user, 'calendarId': calendar['id'],
                                    'JSON': json.dumps(cleanJSON(calendar), ensure_ascii=False, sort_keys=True)})
      else:
        for calendar in calendars:
          baserow = {'primaryEmail': user, 'calendarId': calendar['id']}
          flattenJSON(calendar, flattened=baserow, simpleLists=CALENDAR_SIMPLE_LISTS, delimiter=delimiter)
          for permission in _getCalendarPermissions(cal, calendar):
            row = baserow.copy()
            flattenJSON({'permission': permission}, flattened=row)
            if not FJQC.formatJSON:
              row.pop('id')
              csvPF.WriteRowTitles(row)
            elif csvPF.CheckRowTitles(row):
              calendar.update({'permission': permission})
              csvPF.WriteRowNoFilter({'primaryEmail': user, 'calendarId': calendar['id'],
                                      'JSON': json.dumps(cleanJSON(calendar), ensure_ascii=False, sort_keys=True)})
    elif GC.Values[GC.CSV_OUTPUT_USERS_AUDIT]:
      csvPF.WriteRowNoFilter({'primaryEmail': user})
  if csvPF:
    csvPF.writeCSVfile('Calendars')

USER_CALENDAR_SETTINGS_FIELDS_CHOICE_MAP = {
  'autoaddhangouts': 'autoAddHangouts',
  'datefieldorder': 'dateFieldOrder',
  'defaulteventlength': 'defaultEventLength',
  'format24hourtime': 'format24HourTime',
  'hideinvitations': 'hideInvitations',
  'hideinvitationssetting': 'hideInvitationsSetting',
  'hideweekends': 'hideWeekends',
  'locale': 'locale',
  'remindonrespondedeventsonly': 'remindOnRespondedEventsOnly',
  'showdeclinedevents': 'showDeclinedEvents',
  'timezone': 'timezone',
  'usekeyboardshortcuts': 'useKeyboardShortcuts',
  'weekstart': 'weekStart'
  }

# gam <UserTypeEntity> print calsettings  [todrive <ToDriveAttribute>*]
#	[fields <UserCalendarSettingsFieldList>]
#	[formatjson] [quotechar <Character>}
# gam <UserTypeEntity> show calsettings
#	[formatjson]
def doCalendarsTransferOwnership(calIds):
  Act.Set(Act.TRANSFER_OWNERSHIP)
  newDataOwner = getEmailAddress()
  checkForExtraneousArguments()
  count = len(calIds)
  i = 0
  for calId in calIds:
    i += 1
    calId, cal = validateCalendar(calId, i, count)
    if not cal:
      continue
    try:
      callGAPI(cal.calendars(), 'transferOwnership',
               throwReasons=[GAPI.NOT_FOUND, GAPI.INVALID, GAPI.INVALID_PARAMETER,
                             GAPI.FORBIDDEN, GAPI.AUTH_ERROR, GAPI.CONDITION_NOT_MET],
               calendarId=calId, newDataOwner=newDataOwner, useAdminAccess=True)
      entityPerformActionModifierNewValue([Ent.CALENDAR, calId], Act.MODIFIER_TO, newDataOwner, i, count)
    except (GAPI.notFound, GAPI.invalid, GAPI.invalidParameter,
            GAPI.forbidden, GAPI.authError, GAPI.conditionNotMet) as e:
      entityModifierNewValueActionFailedWarning([Ent.CALENDAR, calId], Act.MODIFIER_TO, newDataOwner, str(e), i, count)
    except AttributeError as e:
      entityModifierNewValueActionFailedWarning([Ent.CALENDAR, calId], Act.MODIFIER_TO, newDataOwner, str(e), i, count)
      return

