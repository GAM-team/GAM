"""GAM user service management: ASPs, backup codes, user calendars."""

import json
import sys

from gam.cmd.calendar import (
    CALENDAR_ACL_ROLES_MAP,
    CALENDAR_ATTENDEE_OPTIONAL_CHOICE_MAP,
    CALENDAR_ATTENDEE_STATUS_CHOICE_MAP,
    CALENDAR_MAX_COLOR_INDEX,
    CALENDAR_MIN_COLOR_INDEX,
    EVENT_TIME_OBJECTS,
    EVENT_TYPE_ENTITY_MAP,
    EVENT_TYPE_FOCUSTIME,
    EVENT_TYPE_OUTOFOFFICE,
    EVENT_TYPE_PROPERTIES_NAME_MAP,
    EVENT_TYPE_WORKINGLOCATION,
)

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

APPLICATION_VND_GOOGLE_APPS = 'application/vnd.google-apps.'
MIMETYPE_GA_DOCUMENT = f'{APPLICATION_VND_GOOGLE_APPS}document'
MIMETYPE_GA_FOLDER = f'{APPLICATION_VND_GOOGLE_APPS}folder'
MIMETYPE_GA_FORM = f'{APPLICATION_VND_GOOGLE_APPS}form'
MIMETYPE_GA_PRESENTATION = f'{APPLICATION_VND_GOOGLE_APPS}presentation'
MIMETYPE_GA_SHORTCUT = f'{APPLICATION_VND_GOOGLE_APPS}shortcut'
MIMETYPE_GA_SPREADSHEET = f'{APPLICATION_VND_GOOGLE_APPS}spreadsheet'
MIMETYPE_GA_3P_SHORTCUT = f'{APPLICATION_VND_GOOGLE_APPS}drive-sdk'
ME_IN_OWNERS = "'me' in owners"
ME_IN_OWNERS_AND = ME_IN_OWNERS + " and "
NOT_ME_IN_OWNERS = "not " + ME_IN_OWNERS
NOT_ME_IN_OWNERS_AND = NOT_ME_IN_OWNERS + " and "


def _getMain():
  return sys.modules['gam']

def __getattr__(name):
  """Fall back to gam module for any undefined names."""
  main = _getMain()
  try:
    return getattr(main, name)
  except AttributeError:
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")

def _showASPs(user, asps, i=0, count=0):
  Act.Set(Act.SHOW)
  jcount = len(asps)
  _getMain().entityPerformActionNumItems([Ent.USER, user], jcount, Ent.APPLICATION_SPECIFIC_PASSWORD, i, count)
  if jcount == 0:
    _getMain().setSysExitRC(_getMain().NO_ENTITIES_FOUND_RC)
    return
  Ind.Increment()
  for asp in asps:
    if asp['creationTime'] == '0':
      created_date = _getMain().UNKNOWN
    else:
      created_date = _getMain().formatLocalTimestamp(asp['creationTime'])
    if asp['lastTimeUsed'] == '0':
      used_date = GC.NEVER
    else:
      used_date = _getMain().formatLocalTimestamp(asp['lastTimeUsed'])
    _getMain().printKeyValueList(['ID', asp['codeId']])
    Ind.Increment()
    _getMain().printKeyValueList(['Name', asp['name']])
    _getMain().printKeyValueList(['Created', created_date])
    _getMain().printKeyValueList(['Last Used', used_date])
    Ind.Decrement()
  Ind.Decrement()

# gam <UserTypeEntity> delete asps|applicationspecificpasswords all|<AspIDList>
def deleteASP(users):
  cd = _getMain().buildGAPIObject(API.DIRECTORY)
  codeIdList = _getMain().getString(Cmd.OB_ASP_ID_LIST).lower()
  if codeIdList == 'all':
    allCodeIds = True
  else:
    allCodeIds = False
    codeIds = codeIdList.replace(',', ' ').split()
    for codeId in codeIds:
      if not codeId.isdigit():
        Cmd.Backup()
        _getMain().usageErrorExit(Msg.INVALID_ENTITY.format(Ent.Singular(Ent.APPLICATION_SPECIFIC_PASSWORD), Msg.MUST_BE_NUMERIC))
  _getMain().checkForExtraneousArguments()
  i, count, users = _getMain().getEntityArgument(users)
  for user in users:
    i += 1
    user = _getMain().normalizeEmailAddressOrUID(user)
    if allCodeIds:
      try:
        asps = _getMain().callGAPIitems(cd.asps(), 'list', 'items',
                             throwReasons=[GAPI.USER_NOT_FOUND],
                             userKey=user, fields='items(codeId)')
        codeIds = [asp['codeId'] for asp in asps]
      except GAPI.userNotFound:
        _getMain().entityUnknownWarning(Ent.USER, user, i, count)
        continue
    jcount = len(codeIds)
    _getMain().entityPerformActionNumItems([Ent.USER, user], jcount, Ent.APPLICATION_SPECIFIC_PASSWORD, i, count)
    if jcount == 0:
      _getMain().setSysExitRC(_getMain().NO_ENTITIES_FOUND_RC)
      continue
    Ind.Increment()
    j = 0
    for codeId in codeIds:
      j += 1
      try:
        _getMain().callGAPI(cd.asps(), 'delete',
                 throwReasons=[GAPI.USER_NOT_FOUND, GAPI.INVALID, GAPI.INVALID_PARAMETER, GAPI.FORBIDDEN],
                 userKey=user, codeId=codeId)
        _getMain().entityActionPerformed([Ent.USER, user, Ent.APPLICATION_SPECIFIC_PASSWORD, codeId], j, jcount)
      except (GAPI.invalid, GAPI.invalidParameter, GAPI.forbidden) as e:
        _getMain().entityActionFailedWarning([Ent.USER, user, Ent.APPLICATION_SPECIFIC_PASSWORD, codeId], str(e), j, jcount)
      except GAPI.userNotFound:
        _getMain().entityUnknownWarning(Ent.USER, user, i, count)
        break
    Ind.Decrement()

# gam <UserTypeEntity> print asps|applicationspecificpasswords [todrive <ToDriveAttribute>*]
#	[oneitemperrow]
# gam <UserTypeEntity> show asps|applicationspecificpasswords
def printShowASPs(users):
  cd = _getMain().buildGAPIObject(API.DIRECTORY)
  csvPF = _getMain().CSVPrintFile(['User']) if Act.csvFormat() else None
  oneItemPerRow = False
  while Cmd.ArgumentsRemaining():
    myarg = _getMain().getArgument()
    if csvPF and myarg == 'todrive':
      csvPF.GetTodriveParameters()
    elif csvPF and myarg == 'oneitemperrow':
      oneItemPerRow = True
    else:
      _getMain().unknownArgumentExit()
  i, count, users = _getMain().getEntityArgument(users)
  for user in users:
    i += 1
    user = _getMain().normalizeEmailAddressOrUID(user)
    if csvPF:
      _getMain().printGettingEntityItemForWhom(Ent.APPLICATION_SPECIFIC_PASSWORD, user, i, count)
    try:
      asps = _getMain().callGAPIitems(cd.asps(), 'list', 'items',
                           throwReasons=[GAPI.USER_NOT_FOUND],
                           userKey=user)
      if not csvPF:
        _showASPs(user, asps, i, count)
      else:
        for asp in asps:
          asp.pop('userKey', None)
          if asp['creationTime'] == '0':
            asp['creationTime'] = _getMain().UNKNOWN
          else:
            asp['creationTime'] = formatLocalTimestamp(asp['creationTime'])
          if asp['lastTimeUsed'] == '0':
            asp['lastTimeUsed'] = GC.NEVER
          else:
            asp['lastTimeUsed'] = formatLocalTimestamp(asp['lastTimeUsed'])
        if not oneItemPerRow:
          csvPF.WriteRowTitles(_getMain().flattenJSON({'asps': asps}, flattened={'User': user}))
        else:
          for asp in asps:
            csvPF.WriteRowTitles(_getMain().flattenJSON({'asp': asp}, flattened={'User': user}))
    except GAPI.userNotFound:
      _getMain().entityUnknownWarning(Ent.USER, user, i, count)
  if csvPF:
    csvPF.writeCSVfile('Application Specific Passwords')

def _showBackupCodes(user, codes, i, count):
  Act.Set(Act.SHOW)
  jcount = 0
  for code in codes:
    if code.get('verificationCode'):
      jcount += 1
  _getMain().entityPerformActionNumItems([Ent.USER, user], jcount, Ent.BACKUP_VERIFICATION_CODES, i, count)
  if jcount == 0:
    _getMain().setSysExitRC(_getMain().NO_ENTITIES_FOUND_RC)
    return
  Ind.Increment()
  j = 0
  for code in codes:
    j += 1
    _getMain().printKeyValueList([f'{j:2}', code.get('verificationCode')])
  Ind.Decrement()

# gam <UserTypeEntity> update backupcodes|verificationcodes
def updateBackupCodes(users):
  cd = _getMain().buildGAPIObject(API.DIRECTORY)
  _getMain().checkForExtraneousArguments()
  i, count, users = _getMain().getEntityArgument(users)
  for user in users:
    i += 1
    user = _getMain().normalizeEmailAddressOrUID(user)
    userSuspended = _getMain().checkUserSuspended(cd, user, Ent.USER, i, count)
    if userSuspended is None:
      continue
    if not userSuspended:
      try:
        _getMain().callGAPI(cd.verificationCodes(), 'generate',
                 throwReasons=[GAPI.USER_NOT_FOUND, GAPI.INVALID, GAPI.INVALID_INPUT],
                 userKey=user)
        codes = _getMain().callGAPIitems(cd.verificationCodes(), 'list', 'items',
                              throwReasons=[GAPI.USER_NOT_FOUND],
                              userKey=user, fields='items(verificationCode)')
        _showBackupCodes(user, codes, i, count)
      except GAPI.userNotFound:
        _getMain().entityUnknownWarning(Ent.USER, user, i, count)
      except (GAPI.invalid, GAPI.invalidInput) as e:
        _getMain().entityActionFailedWarning([Ent.USER, user, Ent.BACKUP_VERIFICATION_CODES, None], str(e), i, count)
    else:
      _getMain().entityActionNotPerformedWarning([Ent.USER, user, Ent.BACKUP_VERIFICATION_CODES, None],
                                      Msg.IS_SUSPENDED_NO_BACKUPCODES, i, count)

# gam <UserTypeEntity> delete backupcodes|verificationcodes
def deleteBackupCodes(users):
  cd = _getMain().buildGAPIObject(API.DIRECTORY)
  _getMain().checkForExtraneousArguments()
  i, count, users = _getMain().getEntityArgument(users)
  for user in users:
    i += 1
    user = _getMain().normalizeEmailAddressOrUID(user)
    userSuspended = _getMain().checkUserSuspended(cd, user, Ent.USER, i, count)
    if userSuspended is None:
      continue
    if not userSuspended:
      try:
        _getMain().callGAPI(cd.verificationCodes(), 'invalidate',
                 throwReasons=[GAPI.USER_NOT_FOUND, GAPI.INVALID, GAPI.INVALID_INPUT],
                 userKey=user)
        _getMain().printEntityKVList([Ent.USER, user], [Ent.Plural(Ent.BACKUP_VERIFICATION_CODES), '', 'Invalidated'], i, count)
      except GAPI.userNotFound:
        _getMain().entityUnknownWarning(Ent.USER, user, i, count)
      except (GAPI.invalid, GAPI.invalidInput) as e:
        _getMain().entityActionFailedWarning([Ent.USER, user, Ent.BACKUP_VERIFICATION_CODES, None], str(e), i, count)
    else:
      _getMain().entityActionNotPerformedWarning([Ent.USER, user, Ent.BACKUP_VERIFICATION_CODES, None],
                                      Msg.IS_SUSPENDED_NO_BACKUPCODES, i, count)

# gam <UserTypeEntity> print backupcodes|verificationcodes [todrive <ToDriveAttribute>*]
#	[delimiter <Character>] [countsonly]
# gam <UserTypeEntity> show backupcodes|verificationcodes
def printShowBackupCodes(users):
  cd = _getMain().buildGAPIObject(API.DIRECTORY)
  csvPF = _getMain().CSVPrintFile(['User', 'verificationCodesCount', 'verificationCodes']) if Act.csvFormat() else None
  delimiter = GC.Values[GC.CSV_OUTPUT_FIELD_DELIMITER]
  counts_only = False
  while Cmd.ArgumentsRemaining():
    myarg = _getMain().getArgument()
    if csvPF and myarg == 'todrive':
      csvPF.GetTodriveParameters()
    elif myarg == 'delimiter':
      delimiter = _getMain().getCharacter()
    elif myarg == 'countsonly':
      counts_only = True
    else:
      _getMain().unknownArgumentExit()
  # if we're only getting counts, we don't want actual codes pulled down
  if counts_only:
    csvPF.RemoveTitles('verificationCodes')
    fields = 'items(etag)'
  else:
    fields = 'items(verificationCode)'
  i, count, users = _getMain().getEntityArgument(users)
  for user in users:
    i += 1
    user = _getMain().normalizeEmailAddressOrUID(user)
    if csvPF:
      _getMain().printGettingEntityItemForWhom(Ent.BACKUP_VERIFICATION_CODES, user, i, count)
    try:
      codes = _getMain().callGAPIitems(cd.verificationCodes(), 'list', 'items',
                            throwReasons=[GAPI.USER_NOT_FOUND],
                            userKey=user, fields=fields)
      if not csvPF:
        _showBackupCodes(user, codes, i, count)
      elif counts_only:
        csvPF.WriteRow({'User': user, 'verificationCodesCount': len(codes)})
      else:
        csvPF.WriteRow({'User': user,
                        'verificationCodesCount': len(codes),
                        'verificationCodes': delimiter.join([code['verificationCode'] for code in codes if 'verificationCode' in code])})
    except GAPI.userNotFound:
      _getMain().entityUnknownWarning(Ent.USER, user, i, count)
  if csvPF:
    csvPF.writeCSVfile('Backup Verification Codes')

def _getCalendarSelectProperty(myarg, kwargs):
  if myarg == 'minaccessrole':
    kwargs['minAccessRole'] = _getMain().getChoice(CALENDAR_ACL_ROLES_MAP, mapChoice=True)
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
      courseSelectionParameters['courseIds'].extend(_getMain().getEntityList(Cmd.OB_COURSE_ENTITY, shlexSplit=True))
    elif myarg == 'courseswithteacher':
      courseSelectionParameters['teacherId'] = _getMain().getEmailAddress()
      courseSelectionParameters['myCoursesAsTeacher'] = False
    elif myarg == 'mycoursesasteacher':
      courseSelectionParameters['myCoursesAsTeacher'] = True
      courseSelectionParameters['teacherId'] = None
    elif myarg == 'courseswithstudent':
      courseSelectionParameters['studentId'] = _getMain().getEmailAddress()
      courseSelectionParameters['myCoursesAsStudent'] = False
    elif myarg == 'mycoursesasstudent':
      courseSelectionParameters['myCoursesAsStudent'] = True
      courseSelectionParameters['studentId'] = None
    elif myarg in {'coursestate', 'coursestates', 'coursestatus'}:
      _getMain()._getCourseStates(Cmd.OB_COURSE_STATE_LIST, courseSelectionParameters['courseStates'])
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
    myarg = _getMain().getArgument()
    if myarg in {'calendar', 'calendars'}:
      entitySelector = _getMain().getEntitySelector()
      if entitySelector:
        entityList = _getMain().getEntitySelection(entitySelector, False)
        if isinstance(entityList, dict):
          calendarEntity['dict'] = entityList
        else:
          calendarEntity['list'] = entityList
      else:
        calendarEntity['list'].extend(_getMain().convertEntityToList(_getMain().getString(Cmd.OB_EMAIL_ADDRESS_LIST)))
    elif myarg == 'allcalendars':
      calendarEntity['all'] = True
    elif myarg == 'primary':
      calendarEntity['primary'] = True
    elif _getCalendarSelectProperty(myarg, calendarEntity['kwargs']):
      pass
    elif myarg == 'resource':
      calendarEntity['resourceIds'].append(_getMain().getString(Cmd.OB_RESOURCE_ID))
    elif myarg == 'resources':
      calendarEntity['resourceIds'].extend(_getMain().convertEntityToList(_getMain().getString(Cmd.OB_RESOURCE_ID, minLen=0), shlexSplit=True))
    elif _getCourseCalendarSelectionParameters(myarg):
      courseCalendarSelected = True
    elif _noSelectionMade() and (myarg.find('@') != -1 or myarg.find('id:') != -1):
      Cmd.Backup()
      calendarEntity['list'].append(_getMain().getEmailAddress())
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
    calendarEntity['croom'] = _getMain().buildGAPIObject(API.CLASSROOM)
  return calendarEntity

def _validateUserGetCalendarIds(user, i, count, calendarEntity,
                                itemType=None, modifier=None, showAction=True, setRC=True, newCalId=None, secondaryCalendarsOnly=False):
  if user and calendarEntity['dict']:
    calIds = calendarEntity['dict'][user][:]
  else:
    calIds = calendarEntity['list'][:]
  user, cal = _getMain().validateCalendar(user, i, count, noClientAccess=True)
  if not cal:
    return (user, None, None, 0)
  if calendarEntity['resourceIds']:
    cd = _getMain().buildGAPIObject(API.DIRECTORY)
    for resourceId in calendarEntity['resourceIds']:
      try:
        calIds.append(_getMain().callGAPI(cd.resources().calendars(), 'get',
                               throwReasons=[GAPI.BAD_REQUEST, GAPI.RESOURCE_NOT_FOUND, GAPI.FORBIDDEN],
                               customer=GC.Values[GC.CUSTOMER_ID], calendarResourceId=resourceId,
                               fields='resourceEmail')['resourceEmail'])
      except (GAPI.badRequest, GAPI.resourceNotFound, GAPI.forbidden):
        _getMain().checkEntityAFDNEorAccessErrorExit(cd, Ent.RESOURCE_CALENDAR, resourceId, i, count)
        return (user, None, None, 0)
  courseSelectionParameters = calendarEntity.get('courseSelectionParameters')
  if courseSelectionParameters is not None:
    if courseSelectionParameters['myCoursesAsTeacher']:
      courseSelectionParameters['teacherId'] = user
    if courseSelectionParameters['myCoursesAsStudent']:
      courseSelectionParameters['studentId'] = user
    coursesInfo = _getMain()._getCoursesInfo(calendarEntity['croom'], courseSelectionParameters,
                                  calendarEntity['courseShowProperties'])
    if coursesInfo is None:
      return (user, None, None, 0)
    calIds.extend([course['calendarId'] for course in coursesInfo if 'calendarId' in course])
  if calendarEntity['primary']:
    calIds.append(user)
  try:
    if calendarEntity['kwargs'] or calendarEntity['all']:
      result = _getMain().callGAPIpages(cal.calendarList(), 'list', 'items',
                             throwReasons=GAPI.CALENDAR_THROW_REASONS,
                             fields='nextPageToken,items/id', **calendarEntity['kwargs'])
      calIds.extend([calId['id'] for calId in result if not secondaryCalendarsOnly or calId['id'].find('@group.calendar.google.com') != -1])
    else:
      _getMain().callGAPI(cal.calendars(), 'get',
               throwReasons=GAPI.CALENDAR_THROW_REASONS,
               calendarId='primary', fields='')
  except GAPI.notACalendarUser:
    _getMain().userCalServiceNotEnabledWarning(user, i, count)
    return (user, None, None, 0)
  if newCalId:
    newcal = _getMain().buildGAPIObject(API.CALENDAR)
    if not _getMain().checkCalendarExists(newcal, newCalId, i, count):
      _getMain().entityActionFailedWarning([Ent.USER, user, Ent.CALENDAR, newCalId], Msg.DOES_NOT_EXIST, i, count)
      return (user, None, None, 0)
  jcount = len(calIds)
  if setRC and jcount == 0:
    _getMain().setSysExitRC(_getMain().NO_ENTITIES_FOUND_RC)
  if showAction:
    if not itemType:
      _getMain().entityPerformActionNumItems([Ent.USER, user], jcount, Ent.CALENDAR, i, count)
    elif not newCalId:
      _getMain().entityPerformActionSubItemModifierNumItems([Ent.USER, user], itemType, modifier, jcount, Ent.CALENDAR, i, count)
    else:
      _getMain().entityPerformActionSubItemModifierNumItemsModifierNewValue([Ent.USER, user], itemType, modifier, jcount, Ent.CALENDAR, Act.MODIFIER_TO, newCalId, i, count)
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
    myarg = _getMain().getArgument()
    if myarg == 'selected':
      body['selected'] = _getMain().getBoolean()
    elif myarg == 'hidden':
      body['hidden'] = _getMain().getBoolean()
    elif myarg == 'summary':
      body['summaryOverride'] = _getMain().getString(Cmd.OB_STRING)
    elif myarg in {'color', 'colour'}:
      body['colorId'] = _getMain().getChoice(_getMain().CALENDAR_COLOR_MAP, mapChoice=True)
    elif myarg in {'colorindex', 'colorid', 'colourindex', 'colourid'}:
      body['colorId'] = _getMain().getInteger(minVal=CALENDAR_MIN_COLOR_INDEX, maxVal=CALENDAR_MAX_COLOR_INDEX)
    elif myarg in {'backgroundcolor', 'backgroundcolour'}:
      body['backgroundColor'] = _getMain().getColor()
      body.setdefault('foregroundColor', '#000000')
    elif myarg in {'foregroundcolor', 'foregroundcolour'}:
      body['foregroundColor'] = _getMain().getColor()
    elif myarg == 'reminder':
      body.setdefault('defaultReminders', [])
      if not _getMain().checkArgumentPresent(Cmd.CLEAR_NONE_ARGUMENT):
        body['defaultReminders'].append(_getMain().getCalendarReminder(True))
    elif myarg == 'notification':
      body.setdefault('notificationSettings', {'notifications': []})
      method = _getMain().getChoice(CALENDAR_NOTIFICATION_METHODS+Cmd.CLEAR_NONE_ARGUMENT)
      if method not in Cmd.CLEAR_NONE_ARGUMENT:
        for ntype in _getMain()._getFieldsList():
          if ntype in CALENDAR_NOTIFICATION_TYPES_MAP:
            body['notificationSettings']['notifications'].append({'method': method,
                                                                  'type': CALENDAR_NOTIFICATION_TYPES_MAP[ntype]})
          else:
            _getMain().invalidChoiceExit(ntype, CALENDAR_NOTIFICATION_TYPES_MAP, True)
      else:
        body['notificationSettings']['notifications'] = []
    elif returnOnUnknownArgument:
      Cmd.Backup()
      return
    else:
      _getMain().unknownArgumentExit()

def _showCalendar(calendar, j, jcount, FJQC, acls=None):
  if FJQC.formatJSON:
    if acls:
      calendar['acls'] = [{'id': rule['id'], 'role': rule['role']} for rule in acls]
    _getMain().printLine(json.dumps(_getMain().cleanJSON(calendar), ensure_ascii=False, sort_keys=True))
    return
  _getMain()._showCalendarSettings(calendar, j, jcount)
  Ind.Increment()
  if 'primary' in calendar:
    _getMain().printKeyValueList(['Primary', calendar['primary']])
  if 'dataOwner' in calendar:
    _getMain().printKeyValueList(['Owner', calendar['dataOwner']])
  if 'accessRole' in calendar:
    _getMain().printKeyValueList(['Access Level', calendar['accessRole']])
  if 'deleted' in calendar:
    _getMain().printKeyValueList(['Deleted', calendar['deleted']])
  if 'hidden' in calendar:
    _getMain().printKeyValueList(['Hidden', calendar['hidden']])
  if 'selected' in calendar:
    _getMain().printKeyValueList(['Selected', calendar['selected']])
  if 'colorId' in calendar:
    _getMain().printKeyValueList(['Color ID', calendar['colorId'], 'Background Color', calendar['backgroundColor'], 'Foreground Color', calendar['foregroundColor']])
  if 'defaultReminders' in calendar:
    _getMain().printKeyValueList(['Default Reminders', None])
    Ind.Increment()
    for reminder in calendar['defaultReminders']:
      _getMain().printKeyValueList(['Method', reminder['method'], 'Minutes', reminder['minutes']])
    Ind.Decrement()
  if 'notificationSettings' in calendar:
    _getMain().printKeyValueList(['Notifications', None])
    Ind.Increment()
    for notification in calendar['notificationSettings'].get('notifications', []):
      _getMain().printKeyValueList(['Method', notification['method'], 'Type', notification['type']])
    Ind.Decrement()
  if acls:
    j = 0
    jcount = len(acls)
    _getMain().printEntitiesCount(Ent.CALENDAR_ACL, acls)
    Ind.Increment()
    for rule in acls:
      j += 1
      _getMain().printKeyValueListWithCount(_getMain().ACLRuleKeyValueList(rule), j, jcount)
    Ind.Decrement()
  Ind.Decrement()

# Process CalendarList functions
def _processCalendarList(user, i, count, calId, j, jcount, cal, function, **kwargs):
  try:
    _getMain().callGAPI(cal.calendarList(), function,
             throwReasons=[GAPI.NOT_FOUND, GAPI.DUPLICATE, GAPI.UNKNOWN_ERROR,
                           GAPI.CANNOT_CHANGE_OWN_ACL, GAPI.CANNOT_CHANGE_OWN_PRIMARY_SUBSCRIPTION,
                           GAPI.CANNOT_UNSUBSCRIBE_FROM_OWNED_CALENDAR],
             **kwargs)
    _getMain().entityActionPerformed([Ent.USER, user, Ent.CALENDAR, calId], j, jcount)
  except (GAPI.notFound, GAPI.duplicate, GAPI.unknownError, GAPI.serviceNotAvailable,
          GAPI.cannotChangeOwnAcl, GAPI.cannotChangeOwnPrimarySubscription,
          GAPI.cannotUnsubscribeFromOwnedCalendar) as e:
    _getMain().entityActionFailedWarning([Ent.USER, user, Ent.CALENDAR, calId], str(e), j, jcount)
  except GAPI.notACalendarUser:
    _getMain().userCalServiceNotEnabledWarning(user, i, count)

# gam <UserTypeEntity> add calendars <UserCalendarAddEntity> <CalendarAttribute>*
def addCalendars(users):
  calendarEntity = getUserCalendarEntity()
  body = {'selected': True, 'hidden': False}
  _getCalendarAttributes(body)
  colorRgbFormat = 'backgroundColor' in body or 'foregroundColor' in body
  i, count, users = _getMain().getEntityArgument(users)
  for user in users:
    i += 1
    user, cal, calIds, jcount = _validateUserGetCalendarIds(user, i, count, calendarEntity)
    if jcount == 0:
      continue
    Ind.Increment()
    j = 0
    for calId in calIds:
      j += 1
      body['id'] = calId = _getMain().normalizeCalendarId(calId, user)
      _processCalendarList(user, i, count, calId, j, jcount, cal, 'insert',
                           body=body, colorRgbFormat=colorRgbFormat, fields='')
    Ind.Decrement()

def _updateDeleteCalendars(users, calendarEntity, function, **kwargs):
  i, count, users = _getMain().getEntityArgument(users)
  for user in users:
    i += 1
    user, cal, calIds, jcount = _validateUserGetCalendarIds(user, i, count, calendarEntity)
    if jcount == 0:
      continue
    Ind.Increment()
    j = 0
    for calId in calIds:
      j += 1
      calId = _getMain().normalizeCalendarId(calId, user)
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
  _getMain().checkForExtraneousArguments()
  _updateDeleteCalendars(users, calendarEntity, 'delete')


# gam <UserTypeEntity> create calendars <CalendarSettings>
def createCalendar(users):
  calendarEntity = initUserCalendarEntity()
  body = _getMain().getCalendarSettings(summaryRequired=True)
  i, count, users = _getMain().getEntityArgument(users)
  for user in users:
    i += 1
    user, cal, _, _ = _validateUserGetCalendarIds(user, i, count, calendarEntity, showAction=False, setRC=False)
    if not cal:
      continue
    try:
      calId = _getMain().callGAPI(cal.calendars(), 'insert',
                       throwReasons=GAPI.CALENDAR_THROW_REASONS+[GAPI.FORBIDDEN],
                       body=body, fields='id')['id']
      _getMain().entityActionPerformed([Ent.USER, user, Ent.CALENDAR, calId], i, count)
    except GAPI.forbidden as e:
      _getMain().entityActionFailedWarning([Ent.USER, user], str(e), i, count)
    except GAPI.notACalendarUser:
      _getMain().userCalServiceNotEnabledWarning(user, i, count)

def addCreateCalendars(users):
  if Act.Get() == Act.ADD:
    addCalendars(users)
  else:
    createCalendar(users)

def _modifyRemoveCalendars(users, calendarEntity, function, **kwargs):
  i, count, users = _getMain().getEntityArgument(users)
  for user in users:
    i += 1
    user, cal, calIds, jcount = _validateUserGetCalendarIds(user, i, count, calendarEntity)
    if jcount == 0:
      continue
    Ind.Increment()
    j = 0
    for calId in calIds:
      j += 1
      calId = _getMain().normalizeCalendarId(calId, user)
      try:
        _getMain().callGAPI(cal.calendars(), function,
                 throwReasons=GAPI.CALENDAR_THROW_REASONS+[GAPI.NOT_FOUND, GAPI.CANNOT_DELETE_PRIMARY_CALENDAR,
                                                           GAPI.FORBIDDEN, GAPI.INVALID, GAPI.REQUIRED_ACCESS_LEVEL],
                 calendarId=calId, **kwargs)
        _getMain().entityActionPerformed([Ent.USER, user, Ent.CALENDAR, calId], j, jcount)
      except (GAPI.notFound, GAPI.cannotDeletePrimaryCalendar, GAPI.forbidden, GAPI.invalid, GAPI.requiredAccessLevel) as e:
        _getMain().entityActionFailedWarning([Ent.USER, user, Ent.CALENDAR, calId], str(e), j, jcount)
      except GAPI.notACalendarUser:
        _getMain().userCalServiceNotEnabledWarning(user, i, count)
        break
    Ind.Decrement()

# gam <UserTypeEntity> modify calendars <UserCalendarEntity> <CalendarSettings>
def modifyCalendars(users):
  calendarEntity = getUserCalendarEntity()
  body = _getMain().getCalendarSettings(summaryRequired=False)
  _modifyRemoveCalendars(users, calendarEntity, 'patch', body=body)

# gam <UserTypeEntity> remove calendars <UserCalendarEntity>
def removeCalendars(users):
  calendarEntity = getUserCalendarEntity()
  _getMain().checkForExtraneousArguments()
  _modifyRemoveCalendars(users, calendarEntity, 'delete')

def _getCalendarPermissions(cal, calendar):
  if calendar['accessRole'] == 'owner':
    try:
      return _getMain().callGAPIpages(cal.acl(), 'list', 'items',
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
  FJQC = _getMain().FormatJSONQuoteChar()
  fieldsList = []
  acls = []
  getCalPermissions = False
  while Cmd.ArgumentsRemaining():
    myarg = _getMain().getArgument()
    if myarg in [Cmd.ARG_ACLS, Cmd.ARG_CALENDARACLS, Cmd.ARG_PERMISSIONS]:
      getCalPermissions = True
    elif _getMain().getFieldsList(myarg, CALENDAR_LIST_FIELDS_CHOICE_MAP, fieldsList, initialField='id'):
      pass
    else:
      FJQC.GetFormatJSON(myarg)
  if fieldsList:
    if getCalPermissions:
      fieldsList.append('accessRole')
  fields = _getMain().getFieldsFromFieldsList(fieldsList)
  i, count, users = _getMain().getEntityArgument(users)
  for user in users:
    i += 1
    user, cal, calIds, jcount = _validateUserGetCalendarIds(user, i, count, calendarEntity, showAction=not FJQC.formatJSON)
    if jcount == 0:
      continue
    Ind.Increment()
    j = 0
    for calId in calIds:
      j += 1
      calId = _getMain().normalizeCalendarId(calId, user)
      try:
        result = _getMain().callGAPI(cal.calendarList(), 'get',
                          throwReasons=GAPI.CALENDAR_THROW_REASONS+[GAPI.NOT_FOUND],
                          calendarId=calId, fields=fields)
        if getCalPermissions:
          acls = _getCalendarPermissions(cal, result)
        _showCalendar(result, j, jcount, FJQC, acls)
      except GAPI.notFound as e:
        _getMain().entityActionFailedWarning([Ent.USER, user, Ent.CALENDAR, calId], str(e), j, jcount)
      except GAPI.notACalendarUser:
        _getMain().userCalServiceNotEnabledWarning(user, i, count)
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
  csvPF = _getMain().CSVPrintFile(['primaryEmail', 'calendarId'], 'sortall') if Act.csvFormat() else None
  FJQC = _getMain().FormatJSONQuoteChar(csvPF)
  kwargs = {}
  delimiter = GC.Values[GC.CSV_OUTPUT_FIELD_DELIMITER]
  fieldsList = []
  while Cmd.ArgumentsRemaining():
    myarg = _getMain().getArgument()
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
      delimiter = _getMain().getCharacter()
    elif _getMain().getFieldsList(myarg, CALENDAR_LIST_FIELDS_CHOICE_MAP, fieldsList, initialField='id'):
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
  fields = _getMain().getItemFieldsFromFieldsList('items', fieldsList)
  i, count, users = _getMain().getEntityArgument(users)
  for user in users:
    i += 1
    user, cal = _getMain().validateCalendar(user, i, count, noClientAccess=True)
    if not cal:
      continue
    if csvPF:
      _getMain().printGettingEntityItemForWhom(Ent.CALENDAR, user, i, count)
    try:
      calendars = _getMain().callGAPIpages(cal.calendarList(), 'list', 'items',
                                throwReasons=GAPI.CALENDAR_THROW_REASONS,
                                fields=fields, **kwargs)
    except GAPI.notACalendarUser:
      _getMain().userCalServiceNotEnabledWarning(user, i, count)
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
          _, domain = _getMain().splitEmailAddress(calendar['id'])
          if domain in excludeDomains:
            continue
        calendars.append(calendar)
    if not csvPF:
      jcount = len(calendars)
      if not FJQC.formatJSON:
        _getMain().entityPerformActionNumItems([Ent.USER, user], jcount, Ent.CALENDAR, i, count)
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
            _getMain().flattenJSON({'permissions': calPerms}, flattened=row)
          _getMain().flattenJSON(calendar, flattened=row, simpleLists=CALENDAR_SIMPLE_LISTS, delimiter=delimiter)
          if not FJQC.formatJSON:
            row.pop('id')
            csvPF.WriteRowTitles(row)
          elif csvPF.CheckRowTitles(row):
            if getCalPermissions:
              calendar.update({'permissions': calPerms})
            csvPF.WriteRowNoFilter({'primaryEmail': user, 'calendarId': calendar['id'],
                                    'JSON': json.dumps(_getMain().cleanJSON(calendar), ensure_ascii=False, sort_keys=True)})
      else:
        for calendar in calendars:
          baserow = {'primaryEmail': user, 'calendarId': calendar['id']}
          _getMain().flattenJSON(calendar, flattened=baserow, simpleLists=CALENDAR_SIMPLE_LISTS, delimiter=delimiter)
          for permission in _getCalendarPermissions(cal, calendar):
            row = baserow.copy()
            _getMain().flattenJSON({'permission': permission}, flattened=row)
            if not FJQC.formatJSON:
              row.pop('id')
              csvPF.WriteRowTitles(row)
            elif csvPF.CheckRowTitles(row):
              calendar.update({'permission': permission})
              csvPF.WriteRowNoFilter({'primaryEmail': user, 'calendarId': calendar['id'],
                                      'JSON': json.dumps(_getMain().cleanJSON(calendar), ensure_ascii=False, sort_keys=True)})
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
def printShowCalSettings(users):
  csvPF = _getMain().CSVPrintFile(['User'], 'sortall') if Act.csvFormat() else None
  FJQC = _getMain().FormatJSONQuoteChar(csvPF)
  fieldsList = []
  while Cmd.ArgumentsRemaining():
    myarg = _getMain().getArgument()
    if csvPF and myarg == 'todrive':
      csvPF.GetTodriveParameters()
    elif _getMain().getFieldsList(myarg, USER_CALENDAR_SETTINGS_FIELDS_CHOICE_MAP, fieldsList):
      pass
    else:
      FJQC.GetFormatJSONQuoteChar(myarg, True)
  fields = set(fieldsList)
  i, count, users = _getMain().getEntityArgument(users)
  for user in users:
    i += 1
    user, cal = _getMain().validateCalendar(user, i, count, noClientAccess=True)
    if not cal:
      continue
    try:
      feed = _getMain().callGAPIpages(cal.settings(), 'list', 'items',
                           throwReasons=GAPI.CALENDAR_THROW_REASONS)
    except GAPI.notACalendarUser:
      _getMain().userCalServiceNotEnabledWarning(user, i, count)
      continue
    settings = {}
    for setting in feed:
      if not fields or setting['id'] in fields:
        settings[setting['id']] = setting['value']
    if not csvPF:
      if not FJQC.formatJSON:
        _getMain().printEntityKVList([Ent.USER, user], [Ent.Plural(Ent.CALENDAR_SETTINGS), None], i, count)
        Ind.Increment()
        for attr in sorted(settings):
          _getMain().printKeyValueList([attr, settings[attr]])
        Ind.Decrement()
      else:
        _getMain().printLine(json.dumps({'User': user, 'settings': settings}, ensure_ascii=False, sort_keys=True))
    else:
      row = _getMain().flattenJSON(settings, flattened={'User': user})
      if not FJQC.formatJSON:
        csvPF.WriteRowTitles(row)
      elif csvPF.CheckRowTitles(row):
        csvPF.WriteRowNoFilter({'User': user, 'JSON': json.dumps(settings, ensure_ascii=False, sort_keys=True)})
  if csvPF:
    csvPF.writeCSVfile('Calendar Settings')

# gam <UserTypeEntity> create calendaracls <UserCalendarEntity> <CalendarACLRole> <CalendarACLScopeEntity> [sendnotifications <Boolean>]
def createCalendarACLs(users):
  calendarEntity = getUserCalendarEntity()
  role, ACLScopeEntity, sendNotifications = _getMain().getCalendarCreateUpdateACLsOptions(True)
  i, count, users = _getMain().getEntityArgument(users)
  for user in users:
    i += 1
    origUser = user
    user, cal, calIds, jcount = _validateUserGetCalendarIds(user, i, count, calendarEntity, Ent.CALENDAR_ACL, Act.MODIFIER_TO)
    if jcount == 0:
      continue
    Ind.Increment()
    _getMain()._doCalendarsCreateACLs(origUser, user, cal, calIds, jcount, role, ACLScopeEntity, sendNotifications)
    Ind.Decrement()

def updateDeleteCalendarACLs(users, calendarEntity, function, modifier, ACLScopeEntity, role, sendNotifications):
  i, count, users = _getMain().getEntityArgument(users)
  for user in users:
    i += 1
    origUser = user
    user, cal, calIds, jcount = _validateUserGetCalendarIds(user, i, count, calendarEntity, Ent.CALENDAR_ACL, modifier)
    if jcount == 0:
      continue
    Ind.Increment()
    _getMain()._doUpdateDeleteCalendarACLs(origUser, user, cal, function, calIds, jcount, ACLScopeEntity, role, sendNotifications)
    Ind.Decrement()

# gam <UserTypeEntity> update calendaracls <UserCalendarEntity> <CalendarACLRole> <CalendarACLScopeEntity> [sendnotifications <Boolean>]
def updateCalendarACLs(users):
  calendarEntity = getUserCalendarEntity()
  role, ACLScopeEntity, sendNotifications = _getMain().getCalendarCreateUpdateACLsOptions(True)
  updateDeleteCalendarACLs(users, calendarEntity, 'patch', Act.MODIFIER_IN, ACLScopeEntity, role, sendNotifications)

# gam <UserTypeEntity> delete calendaracls <UserCalendarEntity> [<CalendarACLRole>] <CalendarACLScopeEntity>
def deleteCalendarACLs(users):
  calendarEntity = getUserCalendarEntity()
  role, ACLScopeEntity = _getMain().getCalendarDeleteACLsOptions(True)
  updateDeleteCalendarACLs(users, calendarEntity, 'delete', Act.MODIFIER_FROM, ACLScopeEntity, role, False)

# gam <UserTypeEntity> info calendaracls <UserCalendarEntity> <CalendarACLScopeEntity>
#	[formatjson]
def infoCalendarACLs(users):
  calendarEntity = getUserCalendarEntity()
  ACLScopeEntity = _getMain().getCalendarSiteACLScopeEntity()
  FJQC = _getMain()._getCalendarInfoACLOptions()
  i, count, users = _getMain().getEntityArgument(users)
  for user in users:
    i += 1
    origUser = user
    user, cal, calIds, jcount = _validateUserGetCalendarIds(user, i, count, calendarEntity, Ent.CALENDAR_ACL, Act.MODIFIER_FROM, showAction=not FJQC.formatJSON)
    if jcount == 0:
      continue
    Ind.Increment()
    _getMain()._doInfoCalendarACLs(origUser, user, cal, calIds, jcount, ACLScopeEntity, FJQC)
    Ind.Decrement()

# gam <UserTypeEntity> print calendaracls <UserCalendarEntity> [todrive <ToDriveAttribute>*]
#	[noselfowner] (addcsvdata <FieldName> <String>)*
#	[formatjson [quotechar <Character>]]
# gam <UserTypeEntity> show calendaracls <UserCalendarEntity>
#	[noselfowner]
#	[formatjson]
def printShowCalendarACLs(users):
  calendarEntity = getUserCalendarEntity(default='all')
  csvPF, FJQC, noSelfOwner, addCSVData = _getMain()._getCalendarPrintShowACLOptions(['primaryEmail', 'calendarId'])
  i, count, users = _getMain().getEntityArgument(users)
  for user in users:
    i += 1
    user, cal, calIds, jcount = _validateUserGetCalendarIds(user, i, count, calendarEntity, Ent.CALENDAR_ACL, Act.MODIFIER_FROM, showAction=not csvPF and not FJQC.formatJSON)
    if jcount == 0:
      continue
    Ind.Increment()
    j = 0
    for calId in calIds:
      j += 1
      calId = _getMain().convertUIDtoEmailAddress(calId)
      _getMain()._printShowCalendarACLs(cal, user, Ent.CALENDAR, calId, j, jcount, csvPF, FJQC, noSelfOwner, addCSVData)
    Ind.Decrement()
  if csvPF:
    csvPF.writeCSVfile('Calendar ACLs')

# gam <CalendarEntity> transfer ownership <UserItem>
def doCalendarsTransferOwnership(calIds):
  Act.Set(Act.TRANSFER_OWNERSHIP)
  newDataOwner = _getMain().getEmailAddress()
  _getMain().checkForExtraneousArguments()
  count = len(calIds)
  i = 0
  for calId in calIds:
    i += 1
    calId, cal = _getMain().validateCalendar(calId, i, count)
    if not cal:
      continue
    try:
      _getMain().callGAPI(cal.calendars(), 'transferOwnership',
               throwReasons=[GAPI.NOT_FOUND, GAPI.INVALID, GAPI.INVALID_PARAMETER,
                             GAPI.FORBIDDEN, GAPI.AUTH_ERROR, GAPI.CONDITION_NOT_MET],
               calendarId=calId, newDataOwner=newDataOwner, useAdminAccess=True)
      _getMain().entityPerformActionModifierNewValue([Ent.CALENDAR, calId], Act.MODIFIER_TO, newDataOwner, i, count)
    except (GAPI.notFound, GAPI.invalid, GAPI.invalidParameter,
            GAPI.forbidden, GAPI.authError, GAPI.conditionNotMet) as e:
      _getMain().entityModifierNewValueActionFailedWarning([Ent.CALENDAR, calId], Act.MODIFIER_TO, newDataOwner, str(e), i, count)
    except AttributeError as e:
      _getMain().entityModifierNewValueActionFailedWarning([Ent.CALENDAR, calId], Act.MODIFIER_TO, newDataOwner, str(e), i, count)
      return

def _createImportCalendarEvent(users, function):
  calendarEntity = getUserCalendarEntity()
  body, parameters = _getMain()._getCalendarCreateImportUpdateEventOptions(function, Ent.USER)
  i, count, users = _getMain().getEntityArgument(users)
  for user in users:
    i += 1
    user, cal, calIds, jcount = _validateUserGetCalendarIds(user, i, count, calendarEntity, Ent.EVENT, Act.MODIFIER_TO)
    if jcount == 0:
      continue
    Ind.Increment()
    _getMain()._createCalendarEvents(user, cal, function, calIds, jcount, body, parameters)
    Ind.Decrement()

# gam <UserTypeEntity> create event <UserCalendarEntity> [id <String>] <EventAddAttribute>+
#	[showdayofweek]
#	[csv [todrive <ToDriveAttribute>*] [formatjson [quotechar <Character>]]]
def createCalendarEvent(users):
  _createImportCalendarEvent(users, 'insert')

# gam <UserTypeEntity> import event <UserCalendarEntity> icaluid <iCalUID> <EventImportAttribute>+
#	[showdayofweek]
#	[csv [todrive <ToDriveAttribute>*] [formatjson [quotechar <Character>]]]
def importCalendarEvent(users):
  _createImportCalendarEvent(users, 'import')

# gam <UserTypeEntity> update events <UserCalendarEntity> [<EventEntity>] [replacemode] <EventUpdateAttribute>+ [<EventNotificationAttribute>]
#	[showdayofweek]
#	[csv [todrive <ToDriveAttribute>*] [formatjson [quotechar <Character>]]]
def updateCalendarEvents(users):
  calendarEntity = getUserCalendarEntity()
  calendarEventEntity = _getMain().getCalendarEventEntity()
  body, parameters = _getMain()._getCalendarCreateImportUpdateEventOptions('update', Ent.USER)
  i, count, users = _getMain().getEntityArgument(users)
  for user in users:
    i += 1
    origUser = user
    user, cal, calIds, jcount = _validateUserGetCalendarIds(user, i, count, calendarEntity, Ent.EVENT, Act.MODIFIER_IN)
    if jcount == 0:
      continue
    Ind.Increment()
    _getMain()._updateCalendarEvents(origUser, user, cal, calIds, jcount, calendarEventEntity, body, parameters)
    Ind.Decrement()

# gam <UserTypeEntity> delete events <UserCalendarEntity> <EventEntity>
#	[batchsize <Integer>] [doit] [<EventNotificationAttribute>]
def deleteCalendarEvents(users):
  calendarEntity = getUserCalendarEntity()
  calendarEventEntity = _getMain().getCalendarEventEntity()
  parameters = _getMain()._getCalendarDeleteEventOptions()
  i, count, users = _getMain().getEntityArgument(users)
  for user in users:
    i += 1
    origUser = user
    user, cal, calIds, jcount = _validateUserGetCalendarIds(user, i, count, calendarEntity, Ent.EVENT, Act.MODIFIER_FROM)
    if jcount == 0:
      continue
    Ind.Increment()
    _getMain()._deleteCalendarEvents(origUser, user, cal, calIds, jcount, calendarEventEntity, parameters)
    Ind.Decrement()

# gam <UserTypeEntity> purge events <UserCalendarEntity> <EventEntity>
#	[batchsize <Integer>] [doit] [<EventNotificationAttribute>]
def purgeCalendarEvents(users):
  calendarEntity = getUserCalendarEntity()
  calendarEventEntity = _getMain().getCalendarEventEntity()
  parameters = _getMain()._getCalendarDeleteEventOptions()
  i, count, users = _getMain().getEntityArgument(users)
  for user in users:
    i += 1
    origUser = user
    user, cal, calIds, jcount = _validateUserGetCalendarIds(user, i, count, calendarEntity, Ent.EVENT, Act.MODIFIER_FROM)
    if jcount == 0:
      continue
    Ind.Increment()
    _getMain()._purgeCalendarEvents(origUser, user, cal, calIds, jcount, calendarEventEntity, parameters, False)
    Ind.Decrement()

# gam <UserTypeEntity> wipe events <UserCalendarEntity>
def wipeCalendarEvents(users):
  calendarEntity = getUserCalendarEntity()
  _getMain().checkForExtraneousArguments()
  i, count, users = _getMain().getEntityArgument(users)
  for user in users:
    i += 1
    user, cal, calIds, jcount = _validateUserGetCalendarIds(user, i, count, calendarEntity, Ent.EVENT, Act.MODIFIER_FROM)
    if jcount == 0:
      continue
    Ind.Increment()
    _getMain()._wipeCalendarEvents(user, cal, calIds, jcount)
    Ind.Decrement()

# gam <UserTypeEntity> move events <UserCalendarEntity> <EventEntity> to|destination <CalendarItem> [<EventNotificationAttribute>]
def moveCalendarEvents(users):
  calendarEntity = getUserCalendarEntity()
  calendarEventEntity = _getMain().getCalendarEventEntity()
  _getMain().checkArgumentPresent(['to', 'destination'])
  newCalId = _getMain().convertUIDtoEmailAddress(_getMain().getString(Cmd.OB_CALENDAR_ITEM))
  parameters, _ = _getMain()._getCalendarMoveEventsOptions()
  if not _getMain().checkCalendarExists(None, newCalId, 0, 0, True):
    return
  i, count, users = _getMain().getEntityArgument(users)
  for user in users:
    i += 1
    origUser = user
    user, cal, calIds, jcount = _validateUserGetCalendarIds(user, i, count, calendarEntity, Ent.EVENT, Act.MODIFIER_FROM, newCalId=newCalId)
    if jcount == 0:
      continue
    Ind.Increment()
    _getMain()._moveCalendarEvents(origUser, user, cal, calIds, jcount, calendarEventEntity, newCalId, parameters)
    Ind.Decrement()

# gam <UserTypeEntity> empty calendartrash <UserCalendarEntity>
def emptyCalendarTrash(users):
  calendarEntity = getUserCalendarEntity()
  _getMain().checkForExtraneousArguments()
  i, count, users = _getMain().getEntityArgument(users)
  for user in users:
    i += 1
    Act.Set(Act.PURGE)
    user, cal, calIds, jcount = _validateUserGetCalendarIds(user, i, count, calendarEntity, Ent.TRASHED_EVENT, Act.MODIFIER_FROM)
    if jcount == 0:
      continue
    Ind.Increment()
    _getMain()._emptyCalendarTrash(user, cal, calIds, jcount)
    Ind.Decrement()

# gam <UserTypeEntity> update calattendees <UserCalendarEntity> <EventEntity> [anyorganizer]
#	[<EventNotificationAttribute>] [splitupdate] [doit]
#	(csv|csvfile <CSVFileInput> endcsv)
#	(delete <EmailAddress>)*
#	(deleteentity <EmailAddressEntity>)*
#	(add <EmailAddress>)*
#	(addentity <EmailAddressEntity>)*
#	(addstatus [<AttendeeAttendance>] [<AttendeeStatus>] <EmailAddress>)*
#	(addentitystatus [<AttendeeAttendance>] [<AttendeeStatus>] <EmailAddressEntity>)*
#	(replace <EmailAddress> <EmailAddress>)*
#	(replacestatus [<AttendeeAttendance>] [<AttendeeStatus>] <EmailAddress> <EmailAddress>)*
#	(updatestatus [<AttendeeAttendance>] [<AttendeeStatus>] <EmailAddress>)*
#	(updateentitystatus [<AttendeeAttendance>] [<AttendeeStatus>] <EmailAddressEntity>)*
def updateCalendarAttendees(users):
  def getStatus(option):
    if option.endswith('status'):
      return(_getMain().getChoice(CALENDAR_ATTENDEE_OPTIONAL_CHOICE_MAP, defaultChoice=None, mapChoice=True),
             _getMain().getChoice(CALENDAR_ATTENDEE_STATUS_CHOICE_MAP, defaultChoice=None, mapChoice=True))
    return (None, None)

  calendarEntity = getUserCalendarEntity()
  calendarEventEntity = _getMain().getCalendarEventEntity()
  anyOrganizer = doIt = splitUpdate = False
  parameters = {'sendUpdates': 'none'}
  attendeeMap = {}
  errors = 0
  while Cmd.ArgumentsRemaining():
    myarg = _getMain().getArgument()
    if myarg in {'csv', 'csvfile'}:
      errors = 0
      f, csvFile, _ = _getMain().openCSVFileReader(_getMain().getString(Cmd.OB_FILE_NAME), fieldnames=['addr', 'op', 'optional', 'status'])
      for row in csvFile:
        updAddr = row['addr']
        updOp = row['op'].lower()
        updOptional = row['optional']
        updStatus = row['status']
        if not updAddr and not updOp:
          continue
        if updOptional:
          updOptional = updOptional.lower()
        if updStatus:
          updStatus = updStatus.lower()
        if (not updAddr or not updOp or
            (updOptional and updOptional not in CALENDAR_ATTENDEE_OPTIONAL_CHOICE_MAP) or
            (updStatus and updStatus not in CALENDAR_ATTENDEE_STATUS_CHOICE_MAP)):
          _getMain().stderrErrorMsg(Msg.INVALID_ATTENDEE_CHANGE.format(','.join([updAddr, updOp, updStatus, updOptional])))
          errors += 1
          continue
        updAddr = _getMain().normalizeEmailAddressOrUID(updAddr, noUid=True)
        if updOp == 'delete':
          attendeeMap[updAddr] = {'op': updOp, 'done': False}
        else:
          updOptional = CALENDAR_ATTENDEE_OPTIONAL_CHOICE_MAP[updOptional] if updOptional else None
          updStatus = CALENDAR_ATTENDEE_STATUS_CHOICE_MAP[updStatus] if updStatus else None
          if updOp == 'add':
            attendeeMap[updAddr] = {'op': updOp, 'status': updStatus, 'optional': updOptional, 'done': False}
          elif updOp == 'update':
            attendeeMap[updAddr] = {'op': updOp, 'status': updStatus, 'optional': updOptional, 'done': False}
          else: #replace
            attendeeMap[updAddr] = {'op': 'replace', 'status': updStatus, 'optional': updOptional, 'email': normalizeEmailAddressOrUID(updOp, noUid=True), 'done': False}
      _getMain().closeFile(f)
    elif myarg == 'delete':
      updAddr = _getMain().getEmailAddress(noUid=True)
      attendeeMap[updAddr] = {'op': 'delete'}
    elif myarg == 'deleteentity':
      for updAddr in _getMain().getNormalizedEmailAddressEntity(noUid=True):
        attendeeMap[updAddr] = {'op': 'delete'}
    elif myarg in {'add', 'addstatus'}:
      updOptional, updStatus = getStatus(myarg)
      updAddr = _getMain().getEmailAddress(noUid=True)
      attendeeMap[updAddr] = {'op': 'add', 'status': updStatus, 'optional': updOptional, 'done': False}
    elif myarg in {'addentity', 'addentitystatus'}:
      updOptional, updStatus = getStatus(myarg)
      for updAddr in _getMain().getNormalizedEmailAddressEntity(noUid=True):
        attendeeMap[updAddr] = {'op': 'add', 'status': updStatus, 'optional': updOptional, 'done': False}
    elif myarg in {'update', 'updatestatus'}:
      updOptional, updStatus = getStatus(myarg)
      updAddr = _getMain().getEmailAddress(noUid=True)
      attendeeMap[updAddr] = {'op': 'update', 'status': updStatus, 'optional': updOptional, 'done': False}
    elif myarg in {'updateentity', 'updateentitystatus'}:
      updOptional, updStatus = getStatus(myarg)
      for updAddr in _getMain().getNormalizedEmailAddressEntity(noUid=True):
        attendeeMap[updAddr] = {'op': 'update', 'status': updStatus, 'optional': updOptional, 'done': False}
    elif myarg in {'replace', 'replacestatus'}:
      updOptional, updStatus = getStatus(myarg)
      updAddr = _getMain().getEmailAddress(noUid=True)
      newAddr = _getMain().getEmailAddress(noUid=True)
      attendeeMap[updAddr] = {'op': 'replace', 'status': updStatus, 'optional': updOptional, 'email': newAddr, 'done': False}
    elif myarg in {'anyorganizer', 'allevents'}:
      anyOrganizer = True
    elif _getMain()._getCalendarSendUpdates(myarg, parameters):
      pass
    elif myarg == 'doit':
      doIt = True
    elif myarg == 'dryrun':
      doIt = False
    elif myarg == 'splitupdate':
      splitUpdate = True
    else:
      _getMain().unknownArgumentExit()
  if not attendeeMap:
    _getMain().missingArgumentExit(Msg.UPDATE_ATTENDEE_CHANGES)
  ucount = len(attendeeMap)
  if errors:
    _getMain().systemErrorExit(_getMain().USAGE_ERROR_RC, '')
  removeMessage = Msg.ATTENDEES_REMOVE
  addMessage = Msg.ATTENDEES_ADD_REMOVE if not splitUpdate else Msg.ATTENDEES_ADD
  fieldsList = ['attendees', 'id', 'organizer', 'status', 'summary']
  i, count, users = _getMain().getEntityArgument(users)
  for user in users:
    i += 1
    origUser = user
    user, cal, calIds, jcount = _validateUserGetCalendarIds(user, i, count, calendarEntity)
    if jcount == 0:
      continue
    Ind.Increment()
    j = 0
    for calId in calIds:
      j += 1
      Act.Set(Act.UPDATE)
      calId, cal, events, kcount = _getMain()._validateCalendarGetEvents(origUser, user, cal, calId, j, jcount, calendarEventEntity,
                                                              fieldsList, True)
      if kcount == 0:
        continue
      Ind.Increment()
      k = 0
      for event in events:
        k += 1
        eventSummary = event.get('summary', event['id'])
        if event['status'] == 'cancelled':
          _getMain().entityActionNotPerformedWarning([Ent.EVENT, eventSummary], Msg.EVENT_IS_CANCELED, k, kcount)
          continue
        if not anyOrganizer and not event.get('organizer', {}).get('self'):
          _getMain().entityActionNotPerformedWarning([Ent.EVENT, eventSummary], Msg.USER_IS_NOT_ORGANIZER, k, kcount)
          continue
        needsUpdate = False
        for _, v in sorted(attendeeMap.items()):
          v['done'] = False
        updatedAttendeesAdd = []
        updatedAttendeesRemove = []
        _getMain().entityPerformActionNumItems([Ent.EVENT, eventSummary], ucount, Ent.ATTENDEE, k, kcount)
        Ind.Increment()
        u = 0
        for attendee in event.get('attendees', []):
          oldAddr = attendee.get('email', '').lower()
          if not oldAddr:
            updatedAttendeesAdd.append(attendee)
            if splitUpdate:
              updatedAttendeesRemove.append(attendee)
            continue
          update = attendeeMap.get(oldAddr)
          if not update:
            updatedAttendeesAdd.append(attendee)
            if splitUpdate:
              updatedAttendeesRemove.append(attendee)
            continue
          updOp = update['op']
          if updOp == 'delete':
            u += 1
            update['done'] = True
            Act.Set(Act.DELETE)
            _getMain().entityPerformAction([Ent.EVENT, eventSummary, Ent.ATTENDEE, oldAddr], u, ucount)
            needsUpdate = True
          else:
            oldStatus = attendee.get('responseStatus')
            oldOptional = attendee.get('optional', False)
            updStatus = update['status']
            updOptional = update['optional']
            if updOp in {'add', 'update'}:
              u += 1
              update['done'] = True
              if ((updStatus is not None and updStatus != oldStatus) or
                  (updOptional is not None and updOptional != oldOptional)):
                attendee['responseStatus'] = updStatus if updStatus is not None else oldStatus
                attendee['optional'] = updOptional if updOptional is not None else oldOptional
                Act.Set(Act.UPDATE)
                _getMain().entityPerformAction([Ent.EVENT, eventSummary, Ent.ATTENDEE, oldAddr], u, ucount)
                needsUpdate = True
              else:
                Act.Set(Act.SKIP)
                _getMain().entityPerformAction([Ent.EVENT, eventSummary, Ent.ATTENDEE, oldAddr], u, ucount)
              updatedAttendeesAdd.append(attendee)
            else: #replace
              u += 1
              update['done'] = True
              attendee['email'] = update['email']
              attendee['responseStatus'] = updStatus if updStatus is not None else oldStatus
              attendee['optional'] = updOptional if updOptional is not None else oldOptional
              Act.Set(Act.REPLACE)
              _getMain().entityPerformActionModifierNewValue([Ent.EVENT, eventSummary, Ent.ATTENDEE, oldAddr], Act.MODIFIER_WITH, update['email'], u, ucount)
              updatedAttendeesAdd.append(attendee)
              needsUpdate = True
        for newAddr, v in sorted(attendeeMap.items()):
          if v['op'] == 'add' and not v['done']:
            u += 1
            v['done'] = True
            attendee = {'email': newAddr}
            if v['status'] is not None:
              attendee['responseStatus'] = v['status']
            if v['optional'] is not None:
              attendee['optional'] = v['optional']
            Act.Set(Act.ADD)
            _getMain().entityPerformAction([Ent.EVENT, eventSummary, Ent.ATTENDEE, newAddr], u, ucount)
            updatedAttendeesAdd.append(attendee)
            needsUpdate = True
        for newAddr, v in sorted(attendeeMap.items()):
          if not v['done']:
            u += 1
            Act.Set(Act.SKIP)
            _getMain().entityPerformAction([Ent.EVENT, eventSummary, Ent.ATTENDEE, newAddr], u, ucount)
        Ind.Decrement()
        if needsUpdate:
          Act.Set(Act.UPDATE)
          if doIt:
            status = True
            if splitUpdate:
              try:
                _getMain().callGAPI(cal.events(), 'patch',
                         throwReasons=GAPI.CALENDAR_THROW_REASONS+[GAPI.NOT_FOUND, GAPI.FORBIDDEN, GAPI.INVALID],
                         calendarId=calId, eventId=event['id'], body={'attendees': updatedAttendeesRemove},
                         sendUpdates=parameters['sendUpdates'], fields='')
                _getMain().entityActionPerformedMessage([Ent.EVENT, eventSummary], removeMessage, j, jcount)
              except GAPI.notFound as e:
                if not _getMain().checkCalendarExists(cal, calId, i, count):
                  _getMain().entityUnknownWarning(Ent.CALENDAR, calId, j, jcount)
                  break
                _getMain().entityActionFailedWarning([Ent.CALENDAR, calId, Ent.EVENT, eventSummary], str(e), k, kcount)
                status = False
              except (GAPI.forbidden, GAPI.invalid) as e:
                _getMain().entityActionFailedWarning([Ent.CALENDAR, calId], str(e), j, jcount)
                break
              except GAPI.notACalendarUser:
                _getMain().userCalServiceNotEnabledWarning(user, i, count)
                break
            if status:
              try:
                _getMain().callGAPI(cal.events(), 'patch',
                         throwReasons=GAPI.CALENDAR_THROW_REASONS+[GAPI.NOT_FOUND, GAPI.FORBIDDEN, GAPI.INVALID],
                         calendarId=calId, eventId=event['id'], body={'attendees': updatedAttendeesAdd},
                         sendUpdates=parameters['sendUpdates'], fields='')
                _getMain().entityActionPerformedMessage([Ent.EVENT, eventSummary], addMessage, jcount)
              except GAPI.notFound as e:
                if not _getMain().checkCalendarExists(cal, calId, i, count):
                  _getMain().entityUnknownWarning(Ent.CALENDAR, calId, j, jcount)
                  break
                _getMain().entityActionFailedWarning([Ent.CALENDAR, calId, Ent.EVENT, eventSummary], str(e), k, kcount)
              except (GAPI.forbidden, GAPI.invalid) as e:
                _getMain().entityActionFailedWarning([Ent.CALENDAR, calId], str(e), j, jcount)
                break
              except GAPI.notACalendarUser:
                _getMain().userCalServiceNotEnabledWarning(user, i, count)
                break
          else:
            _getMain().entityActionNotPerformedWarning([Ent.EVENT, eventSummary], Msg.USE_DOIT_ARGUMENT_TO_PERFORM_ACTION, j, jcount)
      Ind.Decrement()
    Ind.Decrement()

# gam <UserTypeEntity> info events <UserCalendarEntity> <EventEntity> [maxinstances <Number>]
#	[fields <EventFieldNameList>] [showdayofweek]
#	[formatjson]
def infoCalendarEvents(users):
  calendarEntity = getUserCalendarEntity()
  calendarEventEntity = _getMain().getCalendarEventEntity()
  FJQC, fieldsList = _getMain()._getCalendarInfoEventOptions(calendarEventEntity)
  i, count, users = _getMain().getEntityArgument(users)
  for user in users:
    i += 1
    origUser = user
    user, cal, calIds, jcount = _validateUserGetCalendarIds(user, i, count, calendarEntity, Ent.EVENT, Act.MODIFIER_IN, showAction=not FJQC.formatJSON)
    if jcount == 0:
      continue
    Ind.Increment()
    _getMain()._infoCalendarEvents(origUser, user, cal, calIds, jcount, calendarEventEntity, FJQC, fieldsList)
    Ind.Decrement()

# gam <UserTypeEntity> print events <UserCalendarEntity> <EventEntity> <EventDisplayProperties>*
#	[fields <EventFieldNameList>] [showdayofweek]
#	(addcsvdata <FieldName> <String>)*
#	[eventrowfilter]
#	[countsonly|(formatjson [quotechar <Character>])] [todrive <ToDriveAttribute>*]
# gam <UserTypeEntity> show events <UserCalendarEntity> <EventEntity> <EventDisplayProperties>*
#	[fields <EventFieldNameList>] [showdayofweek]
#	~[countsonly|formatjson]
def printShowCalendarEvents(users):
  calendarEntity = getUserCalendarEntity()
  calendarEventEntity = _getMain().getCalendarEventEntity()
  csvPF, FJQC, fieldsList, addCSVData, attendeesList = _getMain()._getCalendarPrintShowEventOptions(calendarEventEntity, Ent.USER)
  i, count, users = _getMain().getEntityArgument(users)
  for user in users:
    i += 1
    origUser = user
    user, cal, calIds, jcount = _validateUserGetCalendarIds(user, i, count, calendarEntity, Ent.EVENT, Act.MODIFIER_FROM,
                                                            showAction=not csvPF and not FJQC.formatJSON)
    if jcount == 0:
      continue
    Ind.Increment()
    _getMain()._printShowCalendarEvents(origUser, user, cal, calIds, jcount, calendarEventEntity,
                             csvPF, FJQC, fieldsList, addCSVData, attendeesList)
    Ind.Decrement()
  if csvPF:
    if calendarEventEntity['countsOnly'] and calendarEventEntity['eventRowFilter']:
      csvPF.SetTitles(calendarEventEntity['countsOnlyTitles'])
      csvPF.writeCSVfile('Calendar Events', True)
    else:
      csvPF.writeCSVfile('Calendar Events')

EVENT_AUTO_DECLINE_MODE_CHOICE_MAP = {
  'declinenone': 'declineNone',
  'declineallconflictinginvitations': 'declineAllConflictingInvitations',
  'declineonlynewconflictinginvitations': 'declineOnlyNewConflictingInvitations',
  'none': 'declineNone',
  'all': 'declineAllConflictingInvitations',
  'new': 'declineOnlyNewConflictingInvitations',
  }

def getStatusEventSummaryDecline(myarg, body, eventProperties):
  if myarg == 'summary':
    body['summary'] = _getMain().getString(Cmd.OB_STRING, minLen=0)
  elif myarg == 'declinemode':
    body[eventProperties]['autoDeclineMode'] = _getMain().getChoice(EVENT_AUTO_DECLINE_MODE_CHOICE_MAP, mapChoice=True)
  elif myarg == 'declinemessage':
    body[eventProperties]['declineMessage'] = _getMain().getString(Cmd.OB_STRING)
  else:
    return False
  return True

def getStatusEventDateTime(dateType, dateList):
  if dateType == 'timerange':
    startTime = _getMain().getTimeOrDeltaFromNow(returnDateTime=True)[0]
    endTime = _getMain().getTimeOrDeltaFromNow(returnDateTime=True)[0]
    if startTime >= endTime:
      Cmd.Backup()
      _getMain().usageErrorExit(Msg.INVALID_EVENT_TIMERANGE.format(dateType, startTime, endTime))
    recurrence = []
    while _getMain().checkArgumentPresent(['recurrence']):
      recurrence.append(_getMain().getString(Cmd.OB_RECURRENCE))
    dateList.append({'type': dateType, 'first': startTime, 'last': endTime,
                     'repeats': 1, 'ulast': endTime, 'udelta': {'days': 1}, 'recurrence': recurrence})
    return
  firstDate = _getMain().getYYYYMMDD(minLen=1, returnDateTime=True).replace(tzinfo=GC.Values[GC.TIMEZONE])
  if dateType in {'date', 'allday'}:
    dateList.append({'type': 'date', 'first': firstDate, 'last': firstDate.shift(days=1),
                     'repeats': 1, 'ulast': firstDate.shift(days=1), 'udelta': {'days': 1}})
  elif dateType == 'range':
    lastDate = _getMain().getYYYYMMDD(minLen=1, returnDateTime=True).replace(tzinfo=GC.Values[GC.TIMEZONE])
    dateList.append({'type': dateType, 'first': firstDate, 'last': lastDate.shift(days=1),
                     'repeats': 1, 'ulast': lastDate, 'udelta': {'days': 1}})
  elif dateType == 'daily':
    argRepeat = _getMain().getInteger(minVal=1, maxVal=366)
    dateList.append({'type': dateType, 'first': firstDate, 'last': firstDate.shift(days=1),
                     'repeats': argRepeat, 'ulast': firstDate.shift(days=argRepeat), 'udelta': {'days': 1}})
  else: #weekly
    argRepeat = _getMain().getInteger(minVal=1, maxVal=52)
    dateList.append({'type': dateType, 'first': firstDate, 'last': firstDate.shift(days=1),
                     'repeats': argRepeat, 'ulast': firstDate.shift(weeks=argRepeat), 'udelta': {'weeks': 1}})

STATUS_EVENTS_DATETIME_CHOICES = {'date', 'allday', 'range', 'daily', 'weekly', 'timerange'}

def getStatusEventProperties(myarg, body, parameters, dateList):
  if myarg in STATUS_EVENTS_DATETIME_CHOICES:
    getStatusEventDateTime(myarg, dateList)
  elif myarg == 'timezone':
    parameters['timeZone'] = _getMain().getString(Cmd.OB_STRING)
  elif _getMain()._getCalendarEventReminders(myarg, body):
    pass
  else:
    return False
  return True

EVENT_CHAT_STATUS_CHOICE_MAP = {
  'available': 'available',
  'dnd': 'doNotDisturb',
  'donotdisturb': 'doNotDisturb',
  }

def getFocusTimeProperties(body, parameters, dateList):
  eventProperties = EVENT_TYPE_PROPERTIES_NAME_MAP[EVENT_TYPE_FOCUSTIME]
  body.update({'eventType': EVENT_TYPE_FOCUSTIME, 'summary': 'Focus time',
               eventProperties: {'autoDeclineMode': 'declineNone', 'declineMessage': 'Declined', 'chatStatus': 'available'},
               'transparency':'opaque'})
  while Cmd.ArgumentsRemaining():
    myarg = _getMain().getArgument()
    if getStatusEventSummaryDecline(myarg, body, eventProperties):
      pass
    elif getStatusEventProperties(myarg, body, parameters, dateList):
      pass
    elif myarg == 'chatstatus':
      body[eventProperties]['chatStatus'] = _getMain().getChoice(EVENT_CHAT_STATUS_CHOICE_MAP, mapChoice=True)
    else:
      _getMain().unknownArgumentExit()

def getOutOfOfficeProperties(body, parameters, dateList):
  eventProperties = EVENT_TYPE_PROPERTIES_NAME_MAP[EVENT_TYPE_OUTOFOFFICE]
  body.update({'eventType': EVENT_TYPE_OUTOFOFFICE, 'summary': 'Out of office',
               eventProperties: {'autoDeclineMode': 'declineNone', 'declineMessage': 'Declined'},
               'transparency':'opaque'})
  while Cmd.ArgumentsRemaining():
    myarg = _getMain().getArgument()
    if getStatusEventSummaryDecline(myarg, body, eventProperties):
      pass
    elif getStatusEventProperties(myarg, body, parameters, dateList):
      pass
    else:
      _getMain().unknownArgumentExit()

WORKING_LOCATION_CHOICE_MAP = {
  'custom': 'customLocation',
  'home': 'homeOffice',
  'office': 'officeLocation',
  }

def getWorkingLocationProperties(body, parameters, dateList):
  eventProperties = EVENT_TYPE_PROPERTIES_NAME_MAP[EVENT_TYPE_WORKINGLOCATION]
  body.update({'eventType': EVENT_TYPE_WORKINGLOCATION, eventProperties: {},
               'visibility': 'public', 'transparency':'transparent'})
  location = ''
  while Cmd.ArgumentsRemaining():
    myarg = _getMain().getArgument()
    if myarg in WORKING_LOCATION_CHOICE_MAP:
      location = WORKING_LOCATION_CHOICE_MAP[myarg]
      body[eventProperties]['type'] = location
      if location == 'homeOffice':
        pass
      elif location == 'customLocation':
        body[eventProperties][location] = {'label': _getMain().getString(Cmd.OB_STRING)}
      else: #officeLocation
        body[eventProperties][location] = {'label': _getMain().getString(Cmd.OB_STRING)}
        entry = body[eventProperties][location]
        while Cmd.ArgumentsRemaining():
          myarg = _getMain().getArgument()
          if myarg in {'building', 'buildingid'}:
            entry['buildingId'] = _getMain()._getBuildingByNameOrId(None)
          elif myarg in {'floor', 'floorname'}:
            entry['floorId'] = _getMain().getString(Cmd.OB_STRING, minLen=0)
          elif myarg in {'section', 'floorsection'}:
            entry['floorSectionId'] = _getMain().getString(Cmd.OB_STRING, minLen=0)
          elif myarg in {'desk', 'deskcode'}:
            entry['deskId'] = _getMain().getString(Cmd.OB_STRING, minLen=0)
          elif myarg == 'endlocation':
            break
          else:
            Cmd.Backup()
            break
    elif getStatusEventProperties(myarg, body, parameters, dateList):
      pass
    else:
      _getMain().unknownArgumentExit()
  return location

# gam <UserTypeEntity> create focustime
#	[chatstatus available|donotdisturb]
#	[declinemode none|all|new]
#	[declinemessage <String>]
#	[summary <String>]
#	((date yyyy-mm-dd)|
#	 (range yyyy-mm-dd yyyy-mm-dd)|
#	 (daily yyyy-mm-dd N)|
#	 (weekly yyyy-mm-dd N)|
#	 (timerange <Time> <Time>) (recurrence <RRULE, EXRULE, RDATE and EXDATE line>)*)+
#	[timezone <String>]
#	(noreminders|(reminder email|popup <Number>)+)
# gam <UserTypeEntity> create outofoffice
#	[declinemode none|all|new]
#	[declinemessage <String>]
#	[summary <String>]
#	((date yyyy-mm-dd)|
#	 (range yyyy-mm-dd yyyy-mm-dd)|
#	 (daily yyyy-mm-dd N)|
#	 (weekly yyyy-mm-dd N)|
#	 (timerange <Time> <Time>) (recurrence <RRULE, EXRULE, RDATE and EXDATE line>)*)+
#	[timezone <String>]
#	(noreminders|(reminder email|popup <Number>)+)
# gam <UserTypeEntity> create workinglocation
#	(home|
#	 (custom <String>)|
#	 (office <String> [building|buildingid <String>] [floor|floorname <String>]
#	   		  [section|floorsection <String>] [desk|deskcode <String>]))
#	((date yyyy-mm-dd)|
#	 (range yyyy-mm-dd yyyy-mm-dd)|
#	 (daily yyyy-mm-dd N)|
#	 (weekly yyyy-mm-dd N)|
#	 (timerange <Time> <Time>) (recurrence <RRULE, EXRULE, RDATE and EXDATE line>)*)+
#	[timezone <String>]
#	(noreminders|(reminder email|popup <Number>)+)
def createStatusEvent(users, eventType):
  eventProperties = EVENT_TYPE_PROPERTIES_NAME_MAP[eventType]
  entityType = EVENT_TYPE_ENTITY_MAP[eventType]
  body = {'start': {}, 'end': {}, 'recurrence': None}
  calId = 'primary'
  parameters = {}
  dateList = []
  if eventType == EVENT_TYPE_WORKINGLOCATION:
    location =  getWorkingLocationProperties(body, parameters, dateList)
    if not location:
      _getMain().missingArgumentExit('|'.join(WORKING_LOCATION_CHOICE_MAP))
  elif eventType == EVENT_TYPE_OUTOFOFFICE:
    getOutOfOfficeProperties(body, parameters, dateList)
  else: # elif eventType == EVENT_TYPE_FOCUSTIME:
    getFocusTimeProperties(body, parameters, dateList)
  if not dateList:
    _getMain().missingChoiceExit(STATUS_EVENTS_DATETIME_CHOICES)
  datekvList = [Ent.CALENDAR, '', Ent.EVENT, '', Ent.DATE, '']
  timekvList = [Ent.CALENDAR, '', Ent.EVENT, '', Ent.START_TIME, '', Ent.END_TIME, '']
  if eventType == EVENT_TYPE_WORKINGLOCATION:
    location = body[eventProperties]['type']
    if location in body[eventProperties] and 'label' in body[eventProperties][location]:
      location += f"/{body[eventProperties][location]['label']}"
    datekvList.extend([Ent.LOCATION, location])
    timekvList.extend([Ent.LOCATION, location])
  i, count, users = _getMain().getEntityArgument(users)
  for user in users:
    i += 1
    user, cal = _getMain().buildGAPIServiceObject(API.CALENDAR, user, i, count)
    if not cal:
      continue
    jcount = len(dateList)
    _getMain().entityPerformAction([Ent.CALENDAR, user, entityType, None], i, count)
    Ind.Increment()
    j = 0
    for wlDate in dateList:
      j += 1
      kvList = timekvList if (wlDate['type'] == 'timerange' or eventType in {EVENT_TYPE_FOCUSTIME, EVENT_TYPE_OUTOFOFFICE}) else datekvList
      first = wlDate['first']
      last = wlDate['last']
      kvList[1] = user
      for _ in range(1, wlDate['repeats']+1):
        body.pop('recurrence', None)
        if wlDate['type'] != 'timerange':
          if eventType in {EVENT_TYPE_FOCUSTIME, EVENT_TYPE_OUTOFOFFICE}:
            body['start']['dateTime'] = _getMain().ISOformatTimeStamp(first)
            kvList[5] = body['start']['dateTime']
            body['end']['dateTime'] = _getMain().ISOformatTimeStamp(last)
            kvList[7] = body['end']['dateTime']
          else:
            body['start']['date'] = first.strftime(_getMain().YYYYMMDD_FORMAT)
            kvList[5] = body['start']['date']
            body['end']['date'] = (first.shift(days=1)).strftime(_getMain().YYYYMMDD_FORMAT)
        else:
          body['start']['dateTime'] = _getMain().ISOformatTimeStamp(first)
          kvList[5] = body['start']['dateTime']
          body['end']['dateTime'] = _getMain().ISOformatTimeStamp(last)
          kvList[7] = body['end']['dateTime']
          if wlDate['recurrence']:
            body['recurrence'] = wlDate['recurrence']
            if not _getMain()._setEventRecurrenceTimeZone(cal, calId, body, parameters, i, count):
              break
        try:
          event = _getMain().callGAPI(cal.events(), 'insert',
                           throwReasons=GAPI.CALENDAR_THROW_REASONS+[GAPI.NOT_FOUND, GAPI.FORBIDDEN, GAPI.INVALID, GAPI.BAD_REQUEST,
                                                                     GAPI.TIME_RANGE_EMPTY, GAPI.MALFORMED_WORKING_LOCATION_EVENT],
                           calendarId=calId, body=body, fields='id')
          kvList[3] = event['id']
          _getMain().entityActionPerformed(kvList, j, jcount)
          if wlDate['type'] == 'timerange':
            break
          first = first.shift(**wlDate['udelta'])
          last = last.shift(**wlDate['udelta'])
        except (GAPI.forbidden, GAPI.invalid) as e:
          _getMain().entityActionFailedWarning([Ent.CALENDAR, user], str(e), i, count)
          break
        except (GAPI.badRequest, GAPI.timeRangeEmpty, GAPI.malformedWorkingLocationEvent) as e:
          _getMain().entityActionFailedWarning(kvList, str(e), j, jcount)
          break
        except GAPI.notACalendarUser:
          _getMain().userCalServiceNotEnabledWarning(user, i, count)
          break
    Ind.Decrement()

def createFocusTime(users):
  createStatusEvent(users, EVENT_TYPE_FOCUSTIME)

def createOutOfOffice(users):
  createStatusEvent(users, EVENT_TYPE_OUTOFOFFICE)

def createWorkingLocation(users):
  createStatusEvent(users, EVENT_TYPE_WORKINGLOCATION)

# gam <UserTypeEntity> delete focustime|outofoffice|workinglocation
#	((date yyyy-mm-dd)|
#	 (range yyyy-mm-dd yyyy-mm-dd)|
#	 (daily yyyy-mm-dd N)|
#	 (weekly yyyy-mm-dd N)|
#	 (timerange <Time> <Time>))+
def deleteStatusEvent(users, eventType):
  eventProperties = EVENT_TYPE_PROPERTIES_NAME_MAP[eventType]
  entityType = EVENT_TYPE_ENTITY_MAP[eventType]
  kwargs = {'eventTypes': [eventType], 'showDeleted': False, 'singleEvents': True,
            'timeMax': None, 'timeMin': None, 'orderBy': 'startTime'}
  calId = 'primary'
  dateList = []
  while Cmd.ArgumentsRemaining():
    myarg = _getMain().getArgument()
    if myarg in STATUS_EVENTS_DATETIME_CHOICES:
      getStatusEventDateTime(myarg, dateList)
    else:
      _getMain().unknownArgumentExit()
  if not dateList:
    _getMain().missingChoiceExit(STATUS_EVENTS_DATETIME_CHOICES)
  basekvList = [Ent.CALENDAR, '', Ent.EVENT, '']
  i, count, users = _getMain().getEntityArgument(users)
  for user in users:
    i += 1
    user, cal = _getMain().buildGAPIServiceObject(API.CALENDAR, user, i, count)
    if not cal:
      continue
    jcount = len(dateList)
    _getMain().entityPerformAction([Ent.CALENDAR, user, entityType, None], i, count)
    Ind.Increment()
    j = 0
    for wlDate in dateList:
      j += 1
      first = wlDate['first']
      last = wlDate['last']
      basekvList[1] = user
      events = []
      for _ in range(1, wlDate['repeats']+1):
        kwargs['timeMin'] = _getMain().ISOformatTimeStamp(first)
        kwargs['timeMax'] = _getMain().ISOformatTimeStamp(last)
        try:
          events = _getMain().callGAPIpages(cal.events(), 'list', 'items',
                                 throwReasons=GAPI.CALENDAR_THROW_REASONS+[GAPI.NOT_FOUND, GAPI.FORBIDDEN, GAPI.INVALID, GAPI.BAD_REQUEST],
                                 calendarId=calId, fields=f'nextPageToken,items(id,start,end,{eventProperties})', **kwargs)
        except (GAPI.notFound, GAPI.forbidden, GAPI.invalid, GAPI.badRequest) as e:
          _getMain().entityActionFailedWarning([Ent.CALENDAR, user], str(e), j, jcount)
          break
        except GAPI.notACalendarUser:
          _getMain().userCalServiceNotEnabledWarning(user, i, count)
          break
        kcount = len(events)
        k = 0
        for event in events:
          k += 1
          eventId = event['id']
          basekvList[3] = eventId
          kvList = basekvList[:]
          if eventType == EVENT_TYPE_WORKINGLOCATION:
            location = event[eventProperties]['type']
            if location in event[eventProperties] and 'label' in event[eventProperties][location]:
              location += f"/{event[eventProperties][location]['label']}"
          try:
            _getMain().callGAPI(cal.events(), 'delete',
                     throwReasons=GAPI.CALENDAR_THROW_REASONS+[GAPI.NOT_FOUND, GAPI.DELETED, GAPI.FORBIDDEN,
                                                               GAPI.INVALID, GAPI.REQUIRED, GAPI.REQUIRED_ACCESS_LEVEL],
                     calendarId=calId, eventId=eventId, sendUpdates='none')
            if 'date' in event['start']:
              kvList.extend([Ent.DATE, event['start']['date']])
              if eventType == EVENT_TYPE_WORKINGLOCATION:
                kvList.extend([Ent.LOCATION, location])
            else:
              kvList.extend([Ent.START_TIME, _getMain().formatLocalTime(event['start']['dateTime']),
                             Ent.END_TIME, _getMain().formatLocalTime(event['end']['dateTime'])])
              if eventType == EVENT_TYPE_WORKINGLOCATION:
                kvList.extend([Ent.LOCATION, location])
            _getMain().entityActionPerformed(kvList, k, kcount)
          except (GAPI.notFound, GAPI.deleted) as e:
            if not _getMain().checkCalendarExists(cal, calId, i, count):
              _getMain().entityUnknownWarning(Ent.CALENDAR, calId, k, kcount)
              break
            _getMain().entityActionFailedWarning([Ent.CALENDAR, calId, Ent.EVENT, eventId], str(e), k, kcount)
          except (GAPI.forbidden, GAPI.invalid, GAPI.required, GAPI.requiredAccessLevel) as e:
            _getMain().entityActionFailedWarning([Ent.CALENDAR, calId, Ent.EVENT, eventId], str(e), k, kcount)
          except GAPI.notACalendarUser:
            _getMain().userCalServiceNotEnabledWarning(user, i, count)
            break
        first = first.shift(**wlDate['udelta'])
        last = last.shift(**wlDate['udelta'])
    Ind.Decrement()

def deleteFocusTime(users):
  deleteStatusEvent(users, EVENT_TYPE_FOCUSTIME)

def deleteOutOfOffice(users):
  deleteStatusEvent(users, EVENT_TYPE_OUTOFOFFICE)

def deleteWorkingLocation(users):
  deleteStatusEvent(users, EVENT_TYPE_WORKINGLOCATION)

def _showCalendarStatusEvent(primaryEmail, calId, eventEntityType, event, k, kcount, FJQC):
  if FJQC.formatJSON:
    _getMain().printLine(json.dumps(_getMain().cleanJSON({'primaryEmail': primaryEmail, 'calendarId': calId, 'event': event},
                                   timeObjects=EVENT_TIME_OBJECTS), ensure_ascii=False, sort_keys=True))
    return
  _getMain().printEntity([eventEntityType, event['id']], k, kcount)
  skipObjects = {'id'}
  Ind.Increment()
  _getMain().showJSON(None, event, skipObjects, EVENT_TIME_OBJECTS)
  Ind.Decrement()

# gam <UserTypeEntity> show focustime|outofoffice|workinglocation
#	((date yyyy-mm-dd)|
#	 (range yyyy-mm-dd yyyy-mm-dd)|
#	 (daily yyyy-mm-dd N)|
#	 (weekly yyyy-mm-dd N)|
#	 (timerange <Time> <Time>))+
#	[showdayofweek]
#	[formatjson]
# gam <UserTypeEntity> print focustime|outofoffice|workinglocation
#	((date yyyy-mm-dd)|
#	 (range yyyy-mm-dd yyyy-mm-dd)|
#	 (daily yyyy-mm-dd N)|
#	 (weekly yyyy-mm-dd N)|
#	 (timerange <Time> <Time>))+
#	[showdayofweek]
#	[formatjson [quotechar <Character>]] [todrive <ToDriveAttribute>*]
def printShowStatusEvent(users, eventType):
  eventProperties = EVENT_TYPE_PROPERTIES_NAME_MAP[eventType]
  entityType = EVENT_TYPE_ENTITY_MAP[eventType]
  csvPF = _getMain().CSVPrintFile(['primaryEmail', 'calendarId', 'id'], 'sortall') if Act.csvFormat() else None
  FJQC = _getMain().FormatJSONQuoteChar(csvPF)
  kwargs = {'eventTypes': [eventType], 'showDeleted': False, 'singleEvents': True,
            'timeMax': None, 'timeMin': None, 'orderBy': 'startTime'}
  calId = 'primary'
  showDayOfWeek = False
  dateList = []
  while Cmd.ArgumentsRemaining():
    myarg = _getMain().getArgument()
    if csvPF and myarg == 'todrive':
      csvPF.GetTodriveParameters()
    elif myarg in STATUS_EVENTS_DATETIME_CHOICES:
      getStatusEventDateTime(myarg, dateList)
    elif myarg == 'showdayofweek':
      showDayOfWeek = True
    else:
      FJQC.GetFormatJSONQuoteChar(myarg, True)
  if not dateList:
    _getMain().missingChoiceExit(STATUS_EVENTS_DATETIME_CHOICES)
  i, count, users = _getMain().getEntityArgument(users)
  for user in users:
    i += 1
    user, cal = _getMain().buildGAPIServiceObject(API.CALENDAR, user, i, count)
    if not cal:
      continue
    jcount = len(dateList)
    if not csvPF and not FJQC.formatJSON:
      _getMain().entityPerformAction([Ent.CALENDAR, user, entityType, None], i, count)
    j = 0
    for wlDate in dateList:
      j += 1
      first = wlDate['first']
      last = wlDate['last']
      for _ in range(1, wlDate['repeats']+1):
        kwargs['timeMin'] = _getMain().ISOformatTimeStamp(first)
        kwargs['timeMax'] = _getMain().ISOformatTimeStamp(last)
        try:
          events = _getMain().callGAPIpages(cal.events(), 'list', 'items',
                                 throwReasons=GAPI.CALENDAR_THROW_REASONS+[GAPI.NOT_FOUND, GAPI.FORBIDDEN, GAPI.INVALID, GAPI.BAD_REQUEST],
                                 calendarId=calId, fields=f'nextPageToken,items(id,start,end,eventType,{eventProperties},transparency,visibility)',
                                 **kwargs)
        except (GAPI.notFound, GAPI.forbidden, GAPI.invalid, GAPI.badRequest) as e:
          _getMain().entityActionFailedWarning([Ent.CALENDAR, user], str(e), j, jcount)
          break
        except GAPI.notACalendarUser:
          _getMain().userCalServiceNotEnabledWarning(user, i, count)
          break
        if not csvPF:
          kcount = len(events)
          Ind.Increment()
          k = 0
          for event in events:
            k += 1
            if showDayOfWeek:
              _getMain()._getEventDaysOfWeek(event)
            _showCalendarStatusEvent(user, calId, Ent.EVENT, event, k, kcount, FJQC)
          Ind.Decrement()
        elif events:
          for event in events:
            if showDayOfWeek:
              _getMain()._getEventDaysOfWeek(event)
            _getMain()._printCalendarEvent(user, calId, event, csvPF, FJQC, {}, False)
        elif GC.Values[GC.CSV_OUTPUT_USERS_AUDIT]:
          csvPF.WriteRowNoFilter({'primaryEmail': user})
        first = first.shift(**wlDate['udelta'])
        last = last.shift(**wlDate['udelta'])
  if csvPF:
    csvPF.writeCSVfile(f'Calendar {Ent.Plural(entityType)}')

def printShowFocusTime(users):
  printShowStatusEvent(users, EVENT_TYPE_FOCUSTIME)

def printShowOutOfOffice(users):
  printShowStatusEvent(users, EVENT_TYPE_OUTOFOFFICE)

def printShowWorkingLocation(users):
  printShowStatusEvent(users, EVENT_TYPE_WORKINGLOCATION)

YOUTUBE_CHANNEL_FIELDS_CHOICE_MAP = {
  'brandingsettings': 'brandingSettings',
  'contentdetails': 'contentDetails',
  'contentownerdetails': 'contentOwnerDetails',
  'id': 'id',
  'localizations': 'localizations',
  'snippet': 'snippet',
  'statistics': 'statistics',
  'status': 'status',
  'topicdetails': 'topicDetails',
  }

YOUTUBE_CHANNEL_TIME_OBJECTS = {'publishedAt'}

# gam <UserTypeEntity> show youtubechannels
#	(mine|
#	 (ids|channels <YouTubeChannelIDList>)|
#	 (forusername <String>)|
#	 (managedbyme <String>))
#	[languagecode <BCP47LanguageCode>]
#	[allfields|(fields <YouTubeChannelFieldNameList>)]
#	[formatjson]
# gam <UserTypeEntity> print youtubechannels [todrive <ToDriveAttribute>*]
#	(mine|
#	 (ids|channels <YouTubeChannelIDList>)|
#	 (forusername <String>)|
#	 (managedbyme <String>))
#	[languagecode <BCP47LanguageCode>]
#	[allfields|(fields <YouTubeChannelFieldNameList>)]
#	[formatjson [quotechar <Character>]]
def printShowYouTubeChannel(users):
  csvPF = _getMain().CSVPrintFile(['User', 'id'], 'sortall') if Act.csvFormat() else None
  FJQC = _getMain().FormatJSONQuoteChar(csvPF)
  kwargs = {'mine': True}
  languageCode = ''
  fieldsList = ['id']
  while Cmd.ArgumentsRemaining():
    myarg = _getMain().getArgument()
    if csvPF and myarg == 'todrive':
      csvPF.GetTodriveParameters()
    elif myarg == 'mine':
      kwargs = {'mine': True}
    elif myarg in {'id', 'ids', 'channel', 'channels'}:
      kwargs = {'id': ','.join(_getMain().getEntityList(Cmd.OB_YOUTUBE_CHANNEL_ID_LIST))}
    elif myarg == 'forusername':
      kwargs = {'forUsername': _getMain().getString(Cmd.OB_USER_NAME)}
    elif myarg == 'managedbyme':
      kwargs = {'managedByMe': True, 'onBehalfOfContentOwner': _getMain().getString(Cmd.OB_USER_NAME)}
    elif _getMain().getFieldsList(myarg, YOUTUBE_CHANNEL_FIELDS_CHOICE_MAP, fieldsList):
      pass
    elif myarg == 'allfields':
      for field in YOUTUBE_CHANNEL_FIELDS_CHOICE_MAP:
        _getMain().addFieldToFieldsList(field, YOUTUBE_CHANNEL_FIELDS_CHOICE_MAP, fieldsList)
    elif myarg in {'languagecode', 'hl'}:
      languageCode = _getMain().getLanguageCode(_getMain().BCP47_LANGUAGE_CODES_MAP)
    else:
      FJQC.GetFormatJSONQuoteChar(myarg, True)
  kwargs['part'] = ','.join(set(fieldsList))
  if languageCode:
    kwargs['hl'] = languageCode
  i, count, users = _getMain().getEntityArgument(users)
  for user in users:
    i += 1
    user, yt = _getMain().buildGAPIServiceObject(API.YOUTUBE, user, i, count)
    if not yt:
      continue
    try:
      channels = _getMain().callGAPIpages(yt.channels(), 'list', 'items',
                               throwReasons=GAPI.YOUTUBE_THROW_REASONS,
                               fields='nextPageToken,items', **kwargs)
    except (GAPI.unsupportedSupervisedAccount, GAPI.unsupportedLanguageCode) as e:
      _getMain().entityActionFailedWarning([Ent.USER, user], str(e), i, count)
      continue
    except GAPI.contentOwnerAccountNotFound as e:
      if 'managedByMe' in kwargs:
        _getMain().entityActionFailedWarning([Ent.USER, user, Ent.OWNER, kwargs['onBehalfOfContentOwner']], str(e), i, count)
      else:
        _getMain().entityActionFailedWarning([Ent.USER, user], str(e), i, count)
      continue
    except (GAPI.serviceNotAvailable, GAPI.authError):
      _getMain().userYouTubeServiceNotEnabledWarning(user, i, count)
      continue
    if not csvPF:
      jcount = len(channels)
      if not FJQC.formatJSON:
        _getMain().entityPerformActionNumItems([Ent.USER, user], jcount, Ent.YOUTUBE_CHANNEL, i, count)
      Ind.Increment()
      j = 0
      for channel in channels:
        j += 1
        if FJQC.formatJSON:
          _getMain().printLine(json.dumps(_getMain().cleanJSON(channel, timeObjects=YOUTUBE_CHANNEL_TIME_OBJECTS),
                               ensure_ascii=False, sort_keys=True))
          break
        _getMain().printEntity([Ent.YOUTUBE_CHANNEL, channel['id']], j, jcount)
        Ind.Increment()
        _getMain().showJSON(None, channel, skipObjects={'id'}, timeObjects=YOUTUBE_CHANNEL_TIME_OBJECTS)
        Ind.Decrement()
      Ind.Decrement()
    elif channels:
      for channel in channels:
        row = {'User': user, 'id': channel['id']}
        _getMain().flattenJSON(channel, flattened=row, timeObjects=YOUTUBE_CHANNEL_TIME_OBJECTS)
        if not FJQC.formatJSON:
          csvPF.WriteRowTitles(row)
        elif csvPF.CheckRowTitles(row):
          row = {'User': user, 'id': channel['id'],
                 'JSON': json.dumps(_getMain().cleanJSON(channel, timeObjects=YOUTUBE_CHANNEL_TIME_OBJECTS),
                                    ensure_ascii=False, sort_keys=True)}
          csvPF.WriteRowNoFilter(row)
    elif GC.Values[GC.CSV_OUTPUT_USERS_AUDIT]:
      csvPF.WriteRowNoFilter({'User': user})
  if csvPF:
    csvPF.writeCSVfile('YouTube Channels')

def _getEntityMimeType(fileEntry):
  if fileEntry['mimeType'] == MIMETYPE_GA_FOLDER:
    return Ent.DRIVE_FOLDER
  if fileEntry['mimeType'].startswith(MIMETYPE_GA_3P_SHORTCUT):
    return Ent.DRIVE_3PSHORTCUT
  if fileEntry['mimeType'] != MIMETYPE_GA_SHORTCUT:
    return Ent.DRIVE_FILE
  if 'shortcutDetails' not in fileEntry or 'targetMimeType' not in fileEntry['shortcutDetails']:
    return Ent.DRIVE_SHORTCUT
  return Ent.DRIVE_FOLDER_SHORTCUT if fileEntry['shortcutDetails']['targetMimeType'] == MIMETYPE_GA_FOLDER else Ent.DRIVE_FILE_SHORTCUT

def _getTargetEntityMimeType(fileEntry):
  return Ent.DRIVE_FOLDER if fileEntry['shortcutDetails']['targetMimeType'] == MIMETYPE_GA_FOLDER else Ent.DRIVE_FILE

CORPORA_ALL_DRIVES = 'allDrives'
CORPORA_CHOICE_MAP = {
  'alldrives': CORPORA_ALL_DRIVES,
  'allshareddrives': CORPORA_ALL_DRIVES,
  'allteamdrives': CORPORA_ALL_DRIVES,
  'domain': 'domain',
  'onlyshareddrives': CORPORA_ALL_DRIVES,
  'onlyteamdrives': CORPORA_ALL_DRIVES,
  'user': 'user',
  }

QUERY_SHORTCUTS_MAP = {
  'allfiles': f"mimeType != '{MIMETYPE_GA_FOLDER}'",
  'allfolders': f"mimeType = '{MIMETYPE_GA_FOLDER}'",
  'allforms': f"mimeType = '{MIMETYPE_GA_FORM}'",
  'allgooglefiles': f"mimeType != '{MIMETYPE_GA_FOLDER}' and mimeType contains 'vnd.google'",
  'allnongooglefiles': "not mimeType contains 'vnd.google'",
  'allshortcuts': f"mimeType = '{MIMETYPE_GA_SHORTCUT}'",
  'all3pshortcuts': f"mimeType = '{MIMETYPE_GA_3P_SHORTCUT}'",
  'allitems': 'allitems',
  'mycommentableitems': ME_IN_OWNERS_AND+f"(mimeType = '{MIMETYPE_GA_DOCUMENT}' or mimeType = '{MIMETYPE_GA_SPREADSHEET}' or mimeType = '{MIMETYPE_GA_PRESENTATION}')",
  'mydocs': ME_IN_OWNERS_AND+f"mimeType = '{MIMETYPE_GA_DOCUMENT}'",
  'myfiles': ME_IN_OWNERS_AND+f"mimeType != '{MIMETYPE_GA_FOLDER}'",
  'myfolders': ME_IN_OWNERS_AND+f"mimeType = '{MIMETYPE_GA_FOLDER}'",
  'myforms': ME_IN_OWNERS_AND+f"mimeType = '{MIMETYPE_GA_FORM}'",
  'mygooglefiles': ME_IN_OWNERS_AND+f"mimeType != '{MIMETYPE_GA_FOLDER}' and mimeType contains 'vnd.google'",
  'mynongooglefiles': ME_IN_OWNERS_AND+"not mimeType contains 'vnd.google'",
  'mypresentations': ME_IN_OWNERS_AND+f"mimeType = '{MIMETYPE_GA_PRESENTATION}'",
  'mypublishableitems': ME_IN_OWNERS_AND+f"(mimeType = '{MIMETYPE_GA_DOCUMENT}' or mimeType = '{MIMETYPE_GA_SPREADSHEET}' or mimeType = '{MIMETYPE_GA_FORM}' or mimeType = '{MIMETYPE_GA_PRESENTATION}')",
  'mysheets': ME_IN_OWNERS_AND+f"mimeType = '{MIMETYPE_GA_SPREADSHEET}'",
  'myshortcuts': ME_IN_OWNERS_AND+f"mimeType = '{MIMETYPE_GA_SHORTCUT}'",
  'myslides': ME_IN_OWNERS_AND+f"mimeType = '{MIMETYPE_GA_PRESENTATION}'",
  'my3pshortcuts': ME_IN_OWNERS_AND+f"mimeType = '{MIMETYPE_GA_3P_SHORTCUT}'",
  'myitems': ME_IN_OWNERS,
  'mytopfiles': ME_IN_OWNERS_AND+f"mimeType != '{MIMETYPE_GA_FOLDER}' and 'root' in parents",
  'mytopfolders': ME_IN_OWNERS_AND+f"mimeType = '{MIMETYPE_GA_FOLDER}' and 'root' in parents",
  'mytopitems': ME_IN_OWNERS_AND+"'root' in parents",
  'othersfiles': NOT_ME_IN_OWNERS_AND+f"mimeType != '{MIMETYPE_GA_FOLDER}'",
  'othersfolders': NOT_ME_IN_OWNERS_AND+f"mimeType = '{MIMETYPE_GA_FOLDER}'",
  'othersforms': NOT_ME_IN_OWNERS_AND+f"mimeType = '{MIMETYPE_GA_FORM}'",
  'othersgooglefiles': NOT_ME_IN_OWNERS_AND+f"mimeType != '{MIMETYPE_GA_FOLDER}' and mimeType contains 'vnd.google'",
  'othersnongooglefiles': NOT_ME_IN_OWNERS_AND+"not mimeType contains 'vnd.google'",
  'othersshortcuts': NOT_ME_IN_OWNERS_AND+f"mimeType = '{MIMETYPE_GA_SHORTCUT}'",
  'others3pshortcuts': NOT_ME_IN_OWNERS_AND+f"mimeType = '{MIMETYPE_GA_3P_SHORTCUT}'",
  'othersitems': NOT_ME_IN_OWNERS,
  'writablefiles': f"'me' in writers and mimeType != '{MIMETYPE_GA_FOLDER}'",
  }
SHAREDDRIVE_QUERY_SHORTCUTS_MAP = {
  'allfiles': f"mimeType != '{MIMETYPE_GA_FOLDER}'",
  'allfolders': f"mimeType = '{MIMETYPE_GA_FOLDER}'",
  'allgooglefiles': f"mimeType != '{MIMETYPE_GA_FOLDER}' and mimeType contains 'vnd.google'",
  'allnongooglefiles': "not mimeType contains 'vnd.google'",
  'allitems': 'allitems',
  }

