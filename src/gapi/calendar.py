import sys

# TODO: get rid of these hacks
import __main__
from var import *

import display
import gapi
import utils

def normalizeCalendarId(calname, checkPrimary=False):
  if checkPrimary and calname.lower() == 'primary':
    return calname
  if not GC_Values[GC_DOMAIN]:
    GC_Values[GC_DOMAIN] = __main__._getValueFromOAuth('hd')
  return __main__.convertUIDtoEmailAddress(calname, email_types=['user', 'resource'])

def buildCalendarGAPIObject(calname):
  calendarId = normalizeCalendarId(calname)
  return (calendarId, __main__.buildGAPIServiceObject('calendar', calendarId))

def buildCalendarDataGAPIObject(calname):
  calendarId = normalizeCalendarId(calname)
  # Force service account token request. If we fail fall back to using admin for authentication
  cal = __main__.buildGAPIServiceObject('calendar', calendarId, False)
  if cal is None:
    _, cal = buildCalendarGAPIObject(__main__._getValueFromOAuth('email'))
  return (calendarId, cal)

def printShowACLs(csvFormat):
  calendarId, cal = buildCalendarDataGAPIObject(sys.argv[2])
  if not cal:
    return
  toDrive = False
  i = 4
  while i < len(sys.argv):
    myarg = sys.argv[i].lower().replace('_', '')
    if csvFormat and myarg == 'todrive':
      toDrive = True
      i += 1
    else:
      controlflow.invalid_argument_exit(sys.argv[i], f"gam calendar <email> {['showacl', 'printacl'][csvFormat]}")
  acls = gapi.get_all_pages(cal.acl(), 'list', 'items', calendarId=calendarId)
  i = 0
  if csvFormat:
    titles = []
    rows = []
  else:
    count = len(acls)
  for rule in acls:
    i += 1
    if csvFormat:
      row = utils.flatten_json(rule, None)
      for key in row:
        if key not in titles:
          titles.append(key)
      rows.append(row)
    else:
      print(f'Calendar: {calendarId}, ACL: {formatACLRule(rule)}{display.current_count(i, count)}')
  if csvFormat:
    display.write_csv_file(rows, titles, f'{calendarId} Calendar ACLs', toDrive)

def _getCalendarACLScope(i, body):
  body['scope'] = {}
  myarg = sys.argv[i].lower()
  body['scope']['type'] = myarg
  i += 1
  if myarg in ['user', 'group']:
    body['scope']['value'] = __main__.normalizeEmailAddressOrUID(sys.argv[i], noUid=True)
    i += 1
  elif myarg == 'domain':
    if i < len(sys.argv) and sys.argv[i].lower().replace('_', '') != 'sendnotifications':
      body['scope']['value'] = sys.argv[i].lower()
      i += 1
    else:
      body['scope']['value'] = GC_Values[GC_DOMAIN]
  elif myarg != 'default':
    body['scope']['type'] = 'user'
    body['scope']['value'] = __main__.normalizeEmailAddressOrUID(myarg, noUid=True)
  return i

CALENDAR_ACL_ROLES_MAP = {
  'editor': 'writer',
  'freebusy': 'freeBusyReader',
  'freebusyreader': 'freeBusyReader',
  'owner': 'owner',
  'read': 'reader',
  'reader': 'reader',
  'writer': 'writer',
  'none': 'none',
  }

def addACL(function):
  calendarId, cal = buildCalendarDataGAPIObject(sys.argv[2])
  if not cal:
    return
  myarg = sys.argv[4].lower().replace('_', '')
  if myarg not in CALENDAR_ACL_ROLES_MAP:
    controlflow.expected_argument_exit("Role", ", ".join(CALENDAR_ACL_ROLES_MAP), myarg)
  body = {'role': CALENDAR_ACL_ROLES_MAP[myarg]}
  i = _getCalendarACLScope(5, body)
  sendNotifications = True
  while i < len(sys.argv):
    myarg = sys.argv[i].lower().replace('_', '')
    if myarg == 'sendnotifications':
      sendNotifications = getBoolean(sys.argv[i+1], myarg)
      i += 2
    else:
      controlflow.invalid_argument_exit(sys.argv[i], f"gam calendar <email> {function.lower()}")
  print(f'Calendar: {calendarId}, {function} ACL: {formatACLRule(body)}')
  gapi.call(cal.acl(), 'insert', calendarId=calendarId, body=body, sendNotifications=sendNotifications)

def delACL():
  calendarId, cal = buildCalendarDataGAPIObject(sys.argv[2])
  if not cal:
    return
  if sys.argv[4].lower() == 'id':
    ruleId = sys.argv[5]
    print(f'Removing rights for {ruleId} to {calendarId}')
    gapi.call(cal.acl(), 'delete', calendarId=calendarId, ruleId=ruleId)
  else:
    body = {'role': 'none'}
    _getCalendarACLScope(5, body)
    print(f'Calendar: {calendarId}, Delete ACL: {formatACLScope(body)}')
    gapi.call(cal.acl(), 'insert', calendarId=calendarId, body=body, sendNotifications=False)

def wipeData():
  calendarId, cal = buildCalendarDataGAPIObject(sys.argv[2])
  if not cal:
    return
  gapi.call(cal.calendars(), 'clear', calendarId=calendarId)

def printEvents():
  calendarId, cal = buildCalendarDataGAPIObject(sys.argv[2])
  if not cal:
    return
  q = showDeleted = showHiddenInvitations = timeMin = timeMax = timeZone = updatedMin = None
  toDrive = False
  titles = []
  csvRows = []
  i = 4
  while i < len(sys.argv):
    myarg = sys.argv[i].lower().replace('_', '')
    if myarg == 'query':
      q = sys.argv[i+1]
      i += 2
    elif myarg == 'includedeleted':
      showDeleted = True
      i += 1
    elif myarg == 'includehidden':
      showHiddenInvitations = True
      i += 1
    elif myarg == 'after':
      timeMin = __main__.getTimeOrDeltaFromNow(sys.argv[i+1])
      i += 2
    elif myarg == 'before':
      timeMax = __main__.getTimeOrDeltaFromNow(sys.argv[i+1])
      i += 2
    elif myarg == 'timezone':
      timeZone = sys.argv[i+1]
      i += 2
    elif myarg == 'updated':
      updatedMin = __main__.getTimeOrDeltaFromNow(sys.argv[i+1])
      i += 2
    elif myarg == 'todrive':
      toDrive = True
      i += 1
    else:
      controlflow.invalid_argument_exit(sys.argv[i], "gam calendar <email> printevents")
  page_message = gapi.got_total_items_msg(f'Events for {calendarId}', '')
  results = gapi.get_all_pages(cal.events(), 'list', 'items', page_message=page_message,
                               calendarId=calendarId, q=q, showDeleted=showDeleted,
                               showHiddenInvitations=showHiddenInvitations,
                               timeMin=timeMin, timeMax=timeMax, timeZone=timeZone, updatedMin=updatedMin)
  for result in results:
    row = {'calendarId': calendarId}
    display.add_row_titles_to_csv_file(utils.flatten_json(result, flattened=row), csvRows, titles)
  display.sort_csv_titles(['calendarId', 'id', 'summary', 'status'], titles)
  display.write_csv_file(csvRows, titles, 'Calendar Events', toDrive)

def formatACLScope(rule):
  if rule['scope']['type'] != 'default':
    return f'(Scope: {rule["scope"]["type"]}:{rule["scope"]["value"]})'
  return f'(Scope: {rule["scope"]["type"]})'

def formatACLRule(rule):
  if rule['scope']['type'] != 'default':
    return f'(Scope: {rule["scope"]["type"]}:{rule["scope"]["value"]}, Role: {rule["role"]})'
  return f'(Scope: {rule["scope"]["type"]}, Role: {rule["role"]})'

def getSendUpdates(myarg, i, cal):
  if myarg == 'notifyattendees':
    sendUpdates = 'all'
    i += 1
  elif myarg == 'sendnotifications':
    sendUpdates = 'all' if getBoolean(sys.argv[i+1], myarg) else 'none'
    i += 2
  else: #'sendupdates':
    sendUpdatesMap = {}
    for val in cal._rootDesc['resources']['events']['methods']['delete']['parameters']['sendUpdates']['enum']:
      sendUpdatesMap[val.lower()] = val
    sendUpdates = sendUpdatesMap.get(sys.argv[i+1].lower(), False)
    if not sendUpdates:
      controlflow.expected_argument_exit("sendupdates", ", ".join(sendUpdatesMap), sys.argv[i+1])
    i += 2
  return (sendUpdates, i)

def moveOrDeleteEvent(moveOrDelete):
  calendarId, cal = buildCalendarDataGAPIObject(sys.argv[2])
  if not cal:
    return
  sendUpdates = None
  doit = False
  kwargs = {}
  i = 4
  while i < len(sys.argv):
    myarg = sys.argv[i].lower().replace('_', '')
    if myarg in ['notifyattendees', 'sendnotifications', 'sendupdates']:
      sendUpdates, i = getSendUpdates(myarg, i, cal)
    elif myarg in ['id', 'eventid']:
      eventId = sys.argv[i+1]
      i += 2
    elif myarg in ['query', 'eventquery']:
      controlflow.system_error_exit(2, f'query is no longer supported for {moveOrDelete}event. Use "gam calendar <email> printevents query <query> | gam csv - gam {moveOrDelete}event id ~id" instead.')
    elif myarg == 'doit':
      doit = True
      i += 1
    elif moveOrDelete == 'move' and myarg == 'destination':
      kwargs['destination'] = sys.argv[i+1]
      i += 2
    else:
      controlflow.invalid_argument_exit(sys.argv[i], f"gam calendar <email> {moveOrDelete}event")
  if doit:
    print(f' going to {moveOrDelete} eventId {eventId}')
    gapi.call(cal.events(), moveOrDelete, calendarId=calendarId, eventId=eventId, sendUpdates=sendUpdates, **kwargs)
  else:
    print(f' would {moveOrDelete} eventId {eventId}. Add doit to command to actually {moveOrDelete} event')

def infoEvent():
  calendarId, cal = buildCalendarDataGAPIObject(sys.argv[2])
  if not cal:
    return
  eventId = sys.argv[4]
  result = gapi.call(cal.events(), 'get', calendarId=calendarId, eventId=eventId)
  display.print_json(result)

def addOrUpdateEvent(action):
  calendarId, cal = buildCalendarDataGAPIObject(sys.argv[2])
  if not cal:
    return
  # only way for non-Google calendars to get updates is via email
  timeZone = None
  kwargs = {}
  body = {}
  if action == 'add':
    i = 4
    func = 'insert'
  else:
    eventId = sys.argv[4]
    kwargs = {'eventId': eventId}
    i = 5
    func = 'patch'
    requires_full_update = ['attendee', 'optionalattendee', 'removeattendee',
                            'replacedescription']
    for arg in sys.argv[i:]:
      if arg.replace('_', '').lower() in requires_full_update:
        func = 'update'
        body = gapi.call(cal.events(), 'get', calendarId=calendarId, eventId=eventId)
        break
  sendUpdates, body = getEventAttributes(i, cal, body, action)
  result = gapi.call(cal.events(), func, conferenceDataVersion=1,
          supportsAttachments=True, calendarId=calendarId,
          sendUpdates=sendUpdates, body=body, fields='id', **kwargs)
  print(f'Event {result["id"]} {action} finished')

def getEventAttributes(i, cal, body, action):
  # Default to external only so non-Google
  # calendars are notified of changes
  sendUpdates = 'externalOnly'
  action = 'update' if body else 'add'
  while i < len(sys.argv):
    myarg = sys.argv[i].lower().replace('_', '')
    if myarg in ['notifyattendees', 'sendnotifications', 'sendupdates']:
      sendUpdates, i = getSendUpdates(myarg, i, cal)
    elif myarg == 'attendee':
      body.setdefault('attendees', [])
      body['attendees'].append({'email': sys.argv[i+1]})
      i += 2
    elif myarg == 'removeattendee' and action == 'update':
      remove_email = sys.argv[i+1].lower()
      body['attendees'] = [attendee for attendee in body['attendees'] \
              if not (attendee['email'].lower() == remove_email)]
      i += 2
    elif myarg == 'optionalattendee':
      body.setdefault('attendees', [])
      body['attendees'].append({'email': sys.argv[i+1], 'optional': True})
      i += 2
    elif myarg == 'anyonecanaddself':
      body['anyoneCanAddSelf'] = True
      i += 1
    elif myarg == 'description':
      body['description'] = sys.argv[i+1].replace('\\n', '\n')
      i += 2
    elif myarg == 'replacedescription':
      search = sys.argv[i+1]
      replace = sys.argv[i+2]
      body['description'] = re.sub(search, replace, body['description'])
      i += 3
    elif myarg == 'start':
      if sys.argv[i+1].lower() == 'allday':
        body['start'] = {'date': __main__.getYYYYMMDD(sys.argv[i+2])}
        i += 3
      else:
        body['start'] = {'dateTime': __main__.getTimeOrDeltaFromNow(sys.argv[i+1])}
        i += 2
    elif myarg == 'end':
      if sys.argv[i+1].lower() == 'allday':
        body['end'] = {'date': getYYYYMMDD(sys.argv[i+2])}
        i += 3
      else:
        body['end'] = {'dateTime': __main__.getTimeOrDeltaFromNow(sys.argv[i+1])}
        i += 2
    elif myarg == 'guestscantinviteothers':
      body['guestsCanInviteOthers'] = False
      i += 1
    elif myarg == 'guestscaninviteothers':
      body['guestsCanInviteTohters'] = __main__.getBoolean(sys.argv[i+1], 'guestscaninviteothers')
      i += 2
    elif myarg == 'guestscantseeothers':
      body['guestsCanSeeOtherGuests'] = False
      i += 1
    elif myarg == 'guestscanseeothers':
      body['guestsCanSeeOtherGuests'] = __main__.getBoolean(sys.argv[i+1], 'guestscanseeothers')
      i += 2
    elif myarg == 'guestscanmodify':
      body['guestsCanModify'] = __main__.getBoolean(sys.argv[i+1], 'guestscanmodify')
      i += 2
    elif myarg == 'id':
      if action == 'update':
        controlflow.invalid_argument_exit('id', 'gam calendar <calendar> updateevent')
      body['id'] = sys.argv[i+1]
      i += 2
    elif myarg == 'summary':
      body['summary'] = sys.argv[i+1]
      i += 2
    elif myarg == 'location':
      body['location'] = sys.argv[i+1]
      i += 2
    elif myarg == 'available':
      body['transparency'] = 'transparent'
      i += 1
    elif myarg == 'transparency':
      validTransparency = ['opaque', 'transparent']
      if sys.argv[i+1].lower() in validTransparency:
        body['transparency'] = sys.argv[i+1].lower()
      else:
        controlflow.expected_argument_exit('transparency', ", ".join(validTransparency), sys.argv[i+1])
      i += 2
    elif myarg == 'visibility':
      validVisibility = ['default', 'public', 'private']
      if sys.argv[i+1].lower() in validVisibility:
        body['visibility'] = sys.argv[i+1].lower()
      else:
        controlflow.expected_argument_exit("visibility", ", ".join(validVisibility), sys.argv[i+1])
      i += 2
    elif myarg == 'tentative':
      body['status'] = 'tentative'
      i += 1
    elif myarg == 'status':
      validStatus = ['confirmed', 'tentative', 'cancelled']
      if sys.argv[i+1].lower() in validStatus:
        body['status'] = sys.argv[i+1].lower()
      else:
        controlflow.expected_argument_exit('visibility', ', '.join(validStatus), sys.argv[i+1])
      i += 2
    elif myarg == 'source':
      body['source'] = {'title': sys.argv[i+1], 'url': sys.argv[i+2]}
      i += 3
    elif myarg == 'noreminders':
      body['reminders'] = {'useDefault': False}
      i += 1
    elif myarg == 'reminder':
      body.setdefault('reminders', {'overrides': [], 'useDefault': False})
      body['reminders']['overrides'].append({'minutes': getInteger(sys.argv[i+1], myarg, minVal=0, maxVal=CALENDAR_REMINDER_MAX_MINUTES),
                                             'method': sys.argv[i+2]})
      i += 3
    elif myarg == 'recurrence':
      body.setdefault('recurrence', [])
      body['recurrence'].append(sys.argv[i+1])
      i += 2
    elif myarg == 'timezone':
      timeZone = sys.argv[i+1]
      i += 2
    elif myarg == 'privateproperty':
      if 'extendedProperties' not in body:
        body['extendedProperties'] = {'private': {}, 'shared': {}}
      body['extendedProperties']['private'][sys.argv[i+1]] = sys.argv[i+2]
      i += 3
    elif myarg == 'sharedproperty':
      if 'extendedProperties' not in body:
        body['extendedProperties'] = {'private': {}, 'shared': {}}
      body['extendedProperties']['shared'][sys.argv[i+1]] = sys.argv[i+2]
      i += 3
    elif myarg == 'colorindex':
      body['colorId'] = getInteger(sys.argv[i+1], myarg, CALENDAR_EVENT_MIN_COLOR_INDEX, CALENDAR_EVENT_MAX_COLOR_INDEX)
      i += 2
    elif myarg == 'hangoutsmeet':
      body['conferenceData'] = {'createRequest': {'requestId': f'{str(uuid.uuid4())}'}}
      i += 1
    else:
      controlflow.invalid_argument_exit(sys.argv[i], f'gam calendar <email> {action}event')
  if ('recurrence' in body) and (('start' in body) or ('end' in body)):
    if not timeZone:
      timeZone = gapi.call(cal.calendars(), 'get', calendarId=calendarId, fields='timeZone')['timeZone']
    if 'start' in body:
      body['start']['timeZone'] = timeZone
    if 'end' in body:
      body['end']['timeZone'] = timeZone
  return (sendUpdates, body)

def modifySettings():
  calendarId, cal = buildCalendarDataGAPIObject(sys.argv[2])
  if not cal:
    return
  body = {}
  i = 4
  while i < len(sys.argv):
    myarg = sys.argv[i].lower().replace('_', '')
    if myarg == 'description':
      body['description'] = sys.argv[i+1]
      i += 2
    elif myarg == 'location':
      body['location'] = sys.argv[i+1]
      i += 2
    elif myarg == 'summary':
      body['summary'] = sys.argv[i+1]
      i += 2
    elif myarg == 'timezone':
      body['timeZone'] = sys.argv[i+1]
      i += 2
    else:
      controlflow.invalid_argument_exit(sys.argv[i], "gam calendar <email> modify")
  gapi.call(cal.calendars(), 'patch', calendarId=calendarId, body=body)

def changeAttendees(users):
  do_it = True
  i = 5
  allevents = False
  start_date = end_date = None
  while len(sys.argv) > i:
    myarg = sys.argv[i].lower()
    if myarg == 'csv':
      csv_file = sys.argv[i+1]
      i += 2
    elif myarg == 'dryrun':
      do_it = False
      i += 1
    elif myarg == 'start':
      start_date = __main__.getTimeOrDeltaFromNow(sys.argv[i+1])
      i += 2
    elif myarg == 'end':
      end_date = __main__.getTimeOrDeltaFromNow(sys.argv[i+1])
      i += 2
    elif myarg == 'allevents':
      allevents = True
      i += 1
    else:
      controlflow.invalid_argument_exit(sys.argv[i], "gam <users> update calattendees")
  attendee_map = {}
  f = fileutils.open_file(csv_file)
  csvFile = csv.reader(f)
  for row in csvFile:
    attendee_map[row[0].lower()] = row[1].lower()
  fileutils.close_file(f)
  for user in users:
    sys.stdout.write(f'Checking user {user}\n')
    user, cal = buildCalendarGAPIObject(user)
    if not cal:
      continue
    page_token = None
    while True:
      events_page = gapi.call(cal.events(), 'list', calendarId=user,
                              pageToken=page_token, timeMin=start_date,
                              timeMax=end_date, showDeleted=False,
                              showHiddenInvitations=False)
      print(f'Got {len(events_page.get("items", []))}')
      for event in events_page.get('items', []):
        if event['status'] == 'cancelled':
          #print u' skipping cancelled event'
          continue
        try:
          event_summary = event['summary']
        except (KeyError, UnicodeEncodeError, UnicodeDecodeError):
          event_summary = event['id']
        try:
          if not allevents and event['organizer']['email'].lower() != user:
            #print(f' skipping not-my-event {event_summary}')
            continue
        except KeyError:
          pass # no email for organizer
        needs_update = False
        try:
          for attendee in event['attendees']:
            try:
              if attendee['email'].lower() in attendee_map:
                old_email = attendee['email'].lower()
                new_email = attendee_map[attendee['email'].lower()]
                print(f' SWITCHING attendee {old_email} to {new_email} for {event_summary}')
                event['attendees'].remove(attendee)
                event['attendees'].append({'email': new_email})
                needs_update = True
            except KeyError: # no email for that attendee
              pass
        except KeyError:
          continue # no attendees
        if needs_update:
          body = {}
          body['attendees'] = event['attendees']
          print(f'UPDATING {event_summary}')
          if do_it:
            gapi.call(cal.events(), 'patch', calendarId=user, eventId=event['id'], sendNotifications=False, body=body)
          else:
            print(' not pulling the trigger.')
        #else:
        #  print(f' no update needed for {event_summary}')
      try:
        page_token = events_page['nextPageToken']
      except KeyError:
        break

def deleteCalendar(users):
  calendarId = normalizeCalendarId(sys.argv[5])
  for user in users:
    user, cal = buildCalendarGAPIObject(user)
    if not cal:
      continue
    gapi.call(cal.calendarList(), 'delete', soft_errors=True, calendarId=calendarId)

CALENDAR_REMINDER_MAX_MINUTES = 40320

CALENDAR_MIN_COLOR_INDEX = 1
CALENDAR_MAX_COLOR_INDEX = 24

CALENDAR_EVENT_MIN_COLOR_INDEX = 1
CALENDAR_EVENT_MAX_COLOR_INDEX = 11

def getCalendarAttributes(i, body, function):
  colorRgbFormat = False
  while i < len(sys.argv):
    myarg = sys.argv[i].lower().replace('_', '')
    if myarg == 'selected':
      body['selected'] = getBoolean(sys.argv[i+1], myarg)
      i += 2
    elif myarg == 'hidden':
      body['hidden'] = getBoolean(sys.argv[i+1], myarg)
      i += 2
    elif myarg == 'summary':
      body['summaryOverride'] = sys.argv[i+1]
      i += 2
    elif myarg == 'colorindex':
      body['colorId'] = getInteger(sys.argv[i+1], myarg, minVal=CALENDAR_MIN_COLOR_INDEX, maxVal=CALENDAR_MAX_COLOR_INDEX)
      i += 2
    elif myarg == 'backgroundcolor':
      body['backgroundColor'] = getColor(sys.argv[i+1])
      colorRgbFormat = True
      i += 2
    elif myarg == 'foregroundcolor':
      body['foregroundColor'] = getColor(sys.argv[i+1])
      colorRgbFormat = True
      i += 2
    elif myarg == 'reminder':
      body.setdefault('defaultReminders', [])
      method = sys.argv[i+1].lower()
      if method not in CLEAR_NONE_ARGUMENT:
        if method not in CALENDAR_REMINDER_METHODS:
          controlflow.expected_argument_exit("Method", ", ".join(CALENDAR_REMINDER_METHODS+CLEAR_NONE_ARGUMENT), method)
        minutes = getInteger(sys.argv[i+2], myarg, minVal=0, maxVal=CALENDAR_REMINDER_MAX_MINUTES)
        body['defaultReminders'].append({'method': method, 'minutes': minutes})
        i += 3
      else:
        i += 2
    elif myarg == 'notification':
      body.setdefault('notificationSettings', {'notifications': []})
      method = sys.argv[i+1].lower()
      if method not in CLEAR_NONE_ARGUMENT:
        if method not in CALENDAR_NOTIFICATION_METHODS:
          controlflow.expected_argument_exit("Method", ", ".join(CALENDAR_NOTIFICATION_METHODS+CLEAR_NONE_ARGUMENT), method)
        eventType = sys.argv[i+2].lower()
        if eventType not in CALENDAR_NOTIFICATION_TYPES_MAP:
          controlflow.expected_argument_exit("Event", ", ".join(CALENDAR_NOTIFICATION_TYPES_MAP), eventType)
        body['notificationSettings']['notifications'].append({'method': method, 'type': CALENDAR_NOTIFICATION_TYPES_MAP[eventType]})
        i += 3
      else:
        i += 2
    else:
      controlflow.invalid_argument_exit(sys.argv[i], f"gam {function} calendar")
  return colorRgbFormat

def addCalendar(users):
  calendarId = normalizeCalendarId(sys.argv[5])
  body = {'id': calendarId, 'selected': True, 'hidden': False}
  colorRgbFormat = getCalendarAttributes(6, body, 'add')
  i = 0
  count = len(users)
  for user in users:
    i += 1
    user, cal = buildCalendarGAPIObject(user)
    if not cal:
      continue
    print(f'Subscribing {user} to calendar {calendarId}{display.current_count(i, count)}')
    gapi.call(cal.calendarList(), 'insert', soft_errors=True, body=body, colorRgbFormat=colorRgbFormat)

def updateCalendar(users):
  calendarId = normalizeCalendarId(sys.argv[5], checkPrimary=True)
  body = {}
  colorRgbFormat = getCalendarAttributes(6, body, 'update')
  i = 0
  count = len(users)
  for user in users:
    i += 1
    user, cal = buildCalendarGAPIObject(user)
    if not cal:
      continue
    print(f"Updating {user}'s subscription to calendar {calendarId}{display.current_count(i, count)}")
    calId = calendarId if calendarId != 'primary' else user
    gapi.call(cal.calendarList(), 'patch', soft_errors=True, calendarId=calId, body=body, colorRgbFormat=colorRgbFormat)

def _showCalendar(userCalendar, j, jcount):
  print(f'  Calendar: {userCalendar["id"]}{display.current_count(j, jcount)}')
  print(f'    Summary: {userCalendar.get("summaryOverride", userCalendar["summary"])}')
  print(f'    Description: {userCalendar.get("description", "")}')
  print(f'    Access Level: {userCalendar["accessRole"]}')
  print(f'    Timezone: {userCalendar["timeZone"]}')
  print(f'    Location: {userCalendar.get("location", "")}')
  print(f'    Hidden: {userCalendar.get("hidden", "False")}')
  print(f'    Selected: {userCalendar.get("selected", "False")}')
  print(f'    Color ID: {userCalendar["colorId"]}, Background Color: {userCalendar["backgroundColor"]}, Foreground Color: {userCalendar["foregroundColor"]}')
  print(f'    Default Reminders:')
  for reminder in userCalendar.get('defaultReminders', []):
    print(f'      Method: {reminder["method"]}, Minutes: {reminder["minutes"]}')
  print('    Notifications:')
  if 'notificationSettings' in userCalendar:
    for notification in userCalendar['notificationSettings'].get('notifications', []):
      print(f'      Method: {notification["method"]}, Type: {notification["type"]}')

def infoCalendar(users):
  calendarId = normalizeCalendarId(sys.argv[5], checkPrimary=True)
  i = 0
  count = len(users)
  for user in users:
    i += 1
    user, cal = buildCalendarGAPIObject(user)
    if not cal:
      continue
    result = gapi.call(cal.calendarList(), 'get',
                       soft_errors=True,
                       calendarId=calendarId)
    if result:
      print(f'User: {user}, Calendar:{display.current_count(i, count)}')
      _showCalendar(result, 1, 1)

def printShowCalendars(users, csvFormat):
  if csvFormat:
    todrive = False
    titles = []
    csvRows = []
  i = 5
  while i < len(sys.argv):
    myarg = sys.argv[i].lower()
    if csvFormat and myarg == 'todrive':
      todrive = True
      i += 1
    else:
      controlflow.invalid_argument_exit(myarg, f"gam <users> {['show', 'print'][csvFormat]} calendars")
  i = 0
  count = len(users)
  for user in users:
    i += 1
    user, cal = buildCalendarGAPIObject(user)
    if not cal:
      continue
    result = gapi.get_all_pages(cal.calendarList(), 'list', 'items', soft_errors=True)
    jcount = len(result)
    if not csvFormat:
      print(f'User: {user}, Calendars:{display.current_count(i, count)}')
      if jcount == 0:
        continue
      j = 0
      for userCalendar in result:
        j += 1
        _showCalendar(userCalendar, j, jcount)
    else:
      if jcount == 0:
        continue
      for userCalendar in result:
        row = {'primaryEmail': user}
        display.add_row_titles_to_csv_file(utils.flatten_json(userCalendar, flattened=row), csvRows, titles)
  if csvFormat:
    display.sort_csv_titles(['primaryEmail', 'id'], titles)
    display.write_csv_file(csvRows, titles, 'Calendars', todrive)

def showCalSettings(users):
  i = 0
  count = len(users)
  for user in users:
    i += 1
    user, cal = buildCalendarGAPIObject(user)
    if not cal:
      continue
    feed = gapi.get_all_pages(cal.settings(), 'list', 'items', soft_errors=True)
    if feed:
      print(f'User: {user}, Calendar Settings:{display.current_count(i, count)}')
      settings = {}
      for setting in feed:
        settings[setting['id']] = setting['value']
      for attr, value in sorted(settings.items()):
        print(f'  {attr}: {value}')

def transferSecCals(users):
  target_user = sys.argv[5]
  remove_source_user = sendNotifications = True
  i = 6
  while i < len(sys.argv):
    myarg = sys.argv[i].lower().replace('_', '')
    if myarg == 'keepuser':
      remove_source_user = False
      i += 1
    elif myarg == 'sendnotifications':
      sendNotifications = getBoolean(sys.argv[i+1], myarg)
      i += 2
    else:
      controlflow.invalid_argument_exit(sys.argv[i], "gam <users> transfer seccals")
  if remove_source_user:
    target_user, target_cal = buildCalendarGAPIObject(target_user)
    if not target_cal:
      return
  for user in users:
    user, source_cal = buildCalendarGAPIObject(user)
    if not source_cal:
      continue
    calendars = gapi.get_all_pages(source_cal.calendarList(), 'list', 'items', soft_errors=True,
                                   minAccessRole='owner', showHidden=True, fields='items(id),nextPageToken')
    for calendar in calendars:
      calendarId = calendar['id']
      if calendarId.find('@group.calendar.google.com') != -1:
        gapi.call(source_cal.acl(), 'insert', calendarId=calendarId,
                  body={'role': 'owner', 'scope': {'type': 'user', 'value': target_user}}, sendNotifications=sendNotifications)
        if remove_source_user:
          gapi.call(target_cal.acl(), 'insert', calendarId=calendarId,
                    body={'role': 'none', 'scope': {'type': 'user', 'value': user}}, sendNotifications=sendNotifications)
