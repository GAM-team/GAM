"""GAM calendar status events commands (Focus Time, OOO, Working Location)."""

import json

from gamlib import api as API
from gamlib import gapi as GAPI
from gamlib import msgs as Msg
from gamlib import settings as GC
from gam.var import Act, Cmd, Ent, Ind
from gam.util.api_call import callGAPI, callGAPIpages
from gam.util.args import (
    YYYYMMDD_FORMAT, checkArgumentPresent, getArgument, getChoice,
    getInteger, getString, getTimeOrDeltaFromNow, getYYYYMMDD,
)
from gam.util.csv_pf import CSVPrintFile, FormatJSONQuoteChar, cleanJSON, showJSON
from gam.util.display import (
    entityActionFailedWarning, entityActionPerformed, entityPerformAction,
    printEntity, printLine, userCalServiceNotEnabledWarning,
)
from gam.util.entity import getEntityArgument
from gam.util.errors import missingArgumentExit, missingChoiceExit, unknownArgumentExit, usageErrorExit
from gam.util.output import ISOformatTimeStamp, formatLocalTime
from gam.util.svcacct import buildGAPIServiceObject
from gam.util.access import entityUnknownWarning

from gam.cmd.calendar.core import checkCalendarExists
from gam.cmd.calendar.acls import (
    EVENT_TYPE_ENTITY_MAP, EVENT_TYPE_FOCUSTIME, EVENT_TYPE_OUTOFOFFICE,
    EVENT_TYPE_PROPERTIES_NAME_MAP, EVENT_TYPE_WORKINGLOCATION,
)
from gam.cmd.calendar.events import (
    EVENT_AUTO_DECLINE_MODE_CHOICE_MAP, EVENT_TIME_OBJECTS,
    _getCalendarEventReminders, _getEventDaysOfWeek,
    _printCalendarEvent, _setEventRecurrenceTimeZone,
)
from gam.cmd.resources import _getBuildingByNameOrId


def getStatusEventSummaryDecline(myarg, body, eventProperties):
  if myarg == 'summary':
    body['summary'] = getString(Cmd.OB_STRING, minLen=0)
  elif myarg == 'declinemode':
    body[eventProperties]['autoDeclineMode'] = getChoice(EVENT_AUTO_DECLINE_MODE_CHOICE_MAP, mapChoice=True)
  elif myarg == 'declinemessage':
    body[eventProperties]['declineMessage'] = getString(Cmd.OB_STRING)
  else:
    return False
  return True

def getStatusEventDateTime(dateType, dateList):
  if dateType == 'timerange':
    startTime = getTimeOrDeltaFromNow(returnDateTime=True)[0]
    endTime = getTimeOrDeltaFromNow(returnDateTime=True)[0]
    if startTime >= endTime:
      Cmd.Backup()
      usageErrorExit(Msg.INVALID_EVENT_TIMERANGE.format(dateType, startTime, endTime))
    recurrence = []
    while checkArgumentPresent(['recurrence']):
      recurrence.append(getString(Cmd.OB_RECURRENCE))
    dateList.append({'type': dateType, 'first': startTime, 'last': endTime,
                     'repeats': 1, 'ulast': endTime, 'udelta': {'days': 1}, 'recurrence': recurrence})
    return
  firstDate = getYYYYMMDD(minLen=1, returnDateTime=True).replace(tzinfo=GC.Values[GC.TIMEZONE])
  if dateType in {'date', 'allday'}:
    dateList.append({'type': 'date', 'first': firstDate, 'last': firstDate.shift(days=1),
                     'repeats': 1, 'ulast': firstDate.shift(days=1), 'udelta': {'days': 1}})
  elif dateType == 'range':
    lastDate = getYYYYMMDD(minLen=1, returnDateTime=True).replace(tzinfo=GC.Values[GC.TIMEZONE])
    dateList.append({'type': dateType, 'first': firstDate, 'last': lastDate.shift(days=1),
                     'repeats': 1, 'ulast': lastDate, 'udelta': {'days': 1}})
  elif dateType == 'daily':
    argRepeat = getInteger(minVal=1, maxVal=366)
    dateList.append({'type': dateType, 'first': firstDate, 'last': firstDate.shift(days=1),
                     'repeats': argRepeat, 'ulast': firstDate.shift(days=argRepeat), 'udelta': {'days': 1}})
  else: #weekly
    argRepeat = getInteger(minVal=1, maxVal=52)
    dateList.append({'type': dateType, 'first': firstDate, 'last': firstDate.shift(days=1),
                     'repeats': argRepeat, 'ulast': firstDate.shift(weeks=argRepeat), 'udelta': {'weeks': 1}})

STATUS_EVENTS_DATETIME_CHOICES = {'date', 'allday', 'range', 'daily', 'weekly', 'timerange'}

def getStatusEventProperties(myarg, body, parameters, dateList):
  if myarg in STATUS_EVENTS_DATETIME_CHOICES:
    getStatusEventDateTime(myarg, dateList)
  elif myarg == 'timezone':
    parameters['timeZone'] = getString(Cmd.OB_STRING)
  elif _getCalendarEventReminders(myarg, body):
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
    myarg = getArgument()
    if getStatusEventSummaryDecline(myarg, body, eventProperties):
      pass
    elif getStatusEventProperties(myarg, body, parameters, dateList):
      pass
    elif myarg == 'chatstatus':
      body[eventProperties]['chatStatus'] = getChoice(EVENT_CHAT_STATUS_CHOICE_MAP, mapChoice=True)
    else:
      unknownArgumentExit()

def getOutOfOfficeProperties(body, parameters, dateList):
  eventProperties = EVENT_TYPE_PROPERTIES_NAME_MAP[EVENT_TYPE_OUTOFOFFICE]
  body.update({'eventType': EVENT_TYPE_OUTOFOFFICE, 'summary': 'Out of office',
               eventProperties: {'autoDeclineMode': 'declineNone', 'declineMessage': 'Declined'},
               'transparency':'opaque'})
  while Cmd.ArgumentsRemaining():
    myarg = getArgument()
    if getStatusEventSummaryDecline(myarg, body, eventProperties):
      pass
    elif getStatusEventProperties(myarg, body, parameters, dateList):
      pass
    else:
      unknownArgumentExit()

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
    myarg = getArgument()
    if myarg in WORKING_LOCATION_CHOICE_MAP:
      location = WORKING_LOCATION_CHOICE_MAP[myarg]
      body[eventProperties]['type'] = location
      if location == 'homeOffice':
        pass
      elif location == 'customLocation':
        body[eventProperties][location] = {'label': getString(Cmd.OB_STRING)}
      else: #officeLocation
        body[eventProperties][location] = {'label': getString(Cmd.OB_STRING)}
        entry = body[eventProperties][location]
        while Cmd.ArgumentsRemaining():
          myarg = getArgument()
          if myarg in {'building', 'buildingid'}:
            entry['buildingId'] = _getBuildingByNameOrId(None)
          elif myarg in {'floor', 'floorname'}:
            entry['floorId'] = getString(Cmd.OB_STRING, minLen=0)
          elif myarg in {'section', 'floorsection'}:
            entry['floorSectionId'] = getString(Cmd.OB_STRING, minLen=0)
          elif myarg in {'desk', 'deskcode'}:
            entry['deskId'] = getString(Cmd.OB_STRING, minLen=0)
          elif myarg == 'endlocation':
            break
          else:
            Cmd.Backup()
            break
    elif getStatusEventProperties(myarg, body, parameters, dateList):
      pass
    else:
      unknownArgumentExit()
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
      missingArgumentExit('|'.join(WORKING_LOCATION_CHOICE_MAP))
  elif eventType == EVENT_TYPE_OUTOFOFFICE:
    getOutOfOfficeProperties(body, parameters, dateList)
  else: # elif eventType == EVENT_TYPE_FOCUSTIME:
    getFocusTimeProperties(body, parameters, dateList)
  if not dateList:
    missingChoiceExit(STATUS_EVENTS_DATETIME_CHOICES)
  datekvList = [Ent.CALENDAR, '', Ent.EVENT, '', Ent.DATE, '']
  timekvList = [Ent.CALENDAR, '', Ent.EVENT, '', Ent.START_TIME, '', Ent.END_TIME, '']
  if eventType == EVENT_TYPE_WORKINGLOCATION:
    location = body[eventProperties]['type']
    if location in body[eventProperties] and 'label' in body[eventProperties][location]:
      location += f"/{body[eventProperties][location]['label']}"
    datekvList.extend([Ent.LOCATION, location])
    timekvList.extend([Ent.LOCATION, location])
  i, count, users = getEntityArgument(users)
  for user in users:
    i += 1
    user, cal = buildGAPIServiceObject(API.CALENDAR, user, i, count)
    if not cal:
      continue
    jcount = len(dateList)
    entityPerformAction([Ent.CALENDAR, user, entityType, None], i, count)
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
            body['start']['dateTime'] = ISOformatTimeStamp(first)
            kvList[5] = body['start']['dateTime']
            body['end']['dateTime'] = ISOformatTimeStamp(last)
            kvList[7] = body['end']['dateTime']
          else:
            body['start']['date'] = first.strftime(YYYYMMDD_FORMAT)
            kvList[5] = body['start']['date']
            body['end']['date'] = (first.shift(days=1)).strftime(YYYYMMDD_FORMAT)
        else:
          body['start']['dateTime'] = ISOformatTimeStamp(first)
          kvList[5] = body['start']['dateTime']
          body['end']['dateTime'] = ISOformatTimeStamp(last)
          kvList[7] = body['end']['dateTime']
          if wlDate['recurrence']:
            body['recurrence'] = wlDate['recurrence']
            if not _setEventRecurrenceTimeZone(cal, calId, body, parameters, i, count):
              break
        try:
          event = callGAPI(cal.events(), 'insert',
                           throwReasons=GAPI.CALENDAR_THROW_REASONS+[GAPI.NOT_FOUND, GAPI.FORBIDDEN, GAPI.INVALID, GAPI.BAD_REQUEST,
                                                                     GAPI.TIME_RANGE_EMPTY, GAPI.MALFORMED_WORKING_LOCATION_EVENT],
                           calendarId=calId, body=body, fields='id')
          kvList[3] = event['id']
          entityActionPerformed(kvList, j, jcount)
          if wlDate['type'] == 'timerange':
            break
          first = first.shift(**wlDate['udelta'])
          last = last.shift(**wlDate['udelta'])
        except (GAPI.forbidden, GAPI.invalid) as e:
          entityActionFailedWarning([Ent.CALENDAR, user], str(e), i, count)
          break
        except (GAPI.badRequest, GAPI.timeRangeEmpty, GAPI.malformedWorkingLocationEvent) as e:
          entityActionFailedWarning(kvList, str(e), j, jcount)
          break
        except GAPI.notACalendarUser:
          userCalServiceNotEnabledWarning(user, i, count)
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
    myarg = getArgument()
    if myarg in STATUS_EVENTS_DATETIME_CHOICES:
      getStatusEventDateTime(myarg, dateList)
    else:
      unknownArgumentExit()
  if not dateList:
    missingChoiceExit(STATUS_EVENTS_DATETIME_CHOICES)
  basekvList = [Ent.CALENDAR, '', Ent.EVENT, '']
  i, count, users = getEntityArgument(users)
  for user in users:
    i += 1
    user, cal = buildGAPIServiceObject(API.CALENDAR, user, i, count)
    if not cal:
      continue
    jcount = len(dateList)
    entityPerformAction([Ent.CALENDAR, user, entityType, None], i, count)
    Ind.Increment()
    j = 0
    for wlDate in dateList:
      j += 1
      first = wlDate['first']
      last = wlDate['last']
      basekvList[1] = user
      events = []
      for _ in range(1, wlDate['repeats']+1):
        kwargs['timeMin'] = ISOformatTimeStamp(first)
        kwargs['timeMax'] = ISOformatTimeStamp(last)
        try:
          events = callGAPIpages(cal.events(), 'list', 'items',
                                 throwReasons=GAPI.CALENDAR_THROW_REASONS+[GAPI.NOT_FOUND, GAPI.FORBIDDEN, GAPI.INVALID, GAPI.BAD_REQUEST],
                                 calendarId=calId, fields=f'nextPageToken,items(id,start,end,{eventProperties})', **kwargs)
        except (GAPI.notFound, GAPI.forbidden, GAPI.invalid, GAPI.badRequest) as e:
          entityActionFailedWarning([Ent.CALENDAR, user], str(e), j, jcount)
          break
        except GAPI.notACalendarUser:
          userCalServiceNotEnabledWarning(user, i, count)
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
            callGAPI(cal.events(), 'delete',
                     throwReasons=GAPI.CALENDAR_THROW_REASONS+[GAPI.NOT_FOUND, GAPI.DELETED, GAPI.FORBIDDEN,
                                                               GAPI.INVALID, GAPI.REQUIRED, GAPI.REQUIRED_ACCESS_LEVEL],
                     calendarId=calId, eventId=eventId, sendUpdates='none')
            if 'date' in event['start']:
              kvList.extend([Ent.DATE, event['start']['date']])
              if eventType == EVENT_TYPE_WORKINGLOCATION:
                kvList.extend([Ent.LOCATION, location])
            else:
              kvList.extend([Ent.START_TIME, formatLocalTime(event['start']['dateTime']),
                             Ent.END_TIME, formatLocalTime(event['end']['dateTime'])])
              if eventType == EVENT_TYPE_WORKINGLOCATION:
                kvList.extend([Ent.LOCATION, location])
            entityActionPerformed(kvList, k, kcount)
          except (GAPI.notFound, GAPI.deleted) as e:
            if not checkCalendarExists(cal, calId, i, count):
              entityUnknownWarning(Ent.CALENDAR, calId, k, kcount)
              break
            entityActionFailedWarning([Ent.CALENDAR, calId, Ent.EVENT, eventId], str(e), k, kcount)
          except (GAPI.forbidden, GAPI.invalid, GAPI.required, GAPI.requiredAccessLevel) as e:
            entityActionFailedWarning([Ent.CALENDAR, calId, Ent.EVENT, eventId], str(e), k, kcount)
          except GAPI.notACalendarUser:
            userCalServiceNotEnabledWarning(user, i, count)
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
    printLine(json.dumps(cleanJSON({'primaryEmail': primaryEmail, 'calendarId': calId, 'event': event},
                                   timeObjects=EVENT_TIME_OBJECTS), ensure_ascii=False, sort_keys=True))
    return
  printEntity([eventEntityType, event['id']], k, kcount)
  skipObjects = {'id'}
  Ind.Increment()
  showJSON(None, event, skipObjects, EVENT_TIME_OBJECTS)
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
  csvPF = CSVPrintFile(['primaryEmail', 'calendarId', 'id'], 'sortall') if Act.csvFormat() else None
  FJQC = FormatJSONQuoteChar(csvPF)
  kwargs = {'eventTypes': [eventType], 'showDeleted': False, 'singleEvents': True,
            'timeMax': None, 'timeMin': None, 'orderBy': 'startTime'}
  calId = 'primary'
  showDayOfWeek = False
  dateList = []
  while Cmd.ArgumentsRemaining():
    myarg = getArgument()
    if csvPF and myarg == 'todrive':
      csvPF.GetTodriveParameters()
    elif myarg in STATUS_EVENTS_DATETIME_CHOICES:
      getStatusEventDateTime(myarg, dateList)
    elif myarg == 'showdayofweek':
      showDayOfWeek = True
    else:
      FJQC.GetFormatJSONQuoteChar(myarg, True)
  if not dateList:
    missingChoiceExit(STATUS_EVENTS_DATETIME_CHOICES)
  i, count, users = getEntityArgument(users)
  for user in users:
    i += 1
    user, cal = buildGAPIServiceObject(API.CALENDAR, user, i, count)
    if not cal:
      continue
    jcount = len(dateList)
    if not csvPF and not FJQC.formatJSON:
      entityPerformAction([Ent.CALENDAR, user, entityType, None], i, count)
    j = 0
    for wlDate in dateList:
      j += 1
      first = wlDate['first']
      last = wlDate['last']
      for _ in range(1, wlDate['repeats']+1):
        kwargs['timeMin'] = ISOformatTimeStamp(first)
        kwargs['timeMax'] = ISOformatTimeStamp(last)
        try:
          events = callGAPIpages(cal.events(), 'list', 'items',
                                 throwReasons=GAPI.CALENDAR_THROW_REASONS+[GAPI.NOT_FOUND, GAPI.FORBIDDEN, GAPI.INVALID, GAPI.BAD_REQUEST],
                                 calendarId=calId, fields=f'nextPageToken,items(id,start,end,eventType,{eventProperties},transparency,visibility)',
                                 **kwargs)
        except (GAPI.notFound, GAPI.forbidden, GAPI.invalid, GAPI.badRequest) as e:
          entityActionFailedWarning([Ent.CALENDAR, user], str(e), j, jcount)
          break
        except GAPI.notACalendarUser:
          userCalServiceNotEnabledWarning(user, i, count)
          break
        if not csvPF:
          kcount = len(events)
          Ind.Increment()
          k = 0
          for event in events:
            k += 1
            if showDayOfWeek:
              _getEventDaysOfWeek(event)
            _showCalendarStatusEvent(user, calId, Ent.EVENT, event, k, kcount, FJQC)
          Ind.Decrement()
        elif events:
          for event in events:
            if showDayOfWeek:
              _getEventDaysOfWeek(event)
            _printCalendarEvent(user, calId, event, csvPF, FJQC, {}, False)
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
