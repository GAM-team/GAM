"""GAM calendar events commands."""

import json
import re
import random
import uuid

import arrow

from gamlib import api as API
from gamlib import gapi as GAPI
from gamlib import msgs as Msg
from gamlib import settings as GC
from gamlib import state as GM
from gam.var import Act, Cmd, Ent, Ind
from gam.util.access import entityUnknownWarning
from gam.util.api import buildGAPIObject
from gam.util.api_call import callGAPI, callGAPIpages, checkGAPIError
from gam.util.args import (
    CALENDAR_EVENT_COLOR_MAP, YYYYMMDD_FORMAT,
    getArgument, checkArgumentPresent, checkForExtraneousArguments,
    getAddCSVData, getBoolean, getCalendarReminder, getChoice,
    getEmailAddress, getEventID, getEventTime, getHTTPError,
    getInteger, getJSON, getREPattern, getREPatternSubstitution,
    getString, getStringWithCRsNLs, getTimeOrDeltaFromNow, getYYYYMMDD,
)
from gam.util.batch import batchRequestID, executeBatch, RI_ENTITY, RI_ITEM, RI_J, RI_JCOUNT
from gam.util.csv_pf import (
    CSVPrintFile, FormatJSONQuoteChar, _getFieldsList,
    addFieldToFieldsList, cleanJSON, flattenJSON,
    getFieldsFromFieldsList, getItemFieldsFromFieldsList, showJSON,
)
from gam.util.display import (
    entityActionFailedWarning, entityActionNotPerformedWarning,
    entityActionPerformed, entityActionPerformedMessage,
    entityModifierNewValueActionPerformed,
    entityNumEntitiesActionNotPerformedWarning,
    entityPerformAction, entityPerformActionModifierNewValue,
    entityPerformActionNumItems,
    printEntity, printGettingEntityItemForWhom,
    printKeyValueList, printKeyValueWithCRsNLs, printLine,
    userCalServiceNotEnabledWarning,
)
from gam.util.entity import (
    convertEntityToList, getEntityArgument, getEntitySelection,
    getEntitySelector, getEntityToModify, getNormalizedEmailAddressEntity,
    convertUIDtoEmailAddress, normalizeEmailAddressOrUID,
)
from gam.util.errors import (
    invalidArgumentExit, invalidChoiceExit, missingArgumentExit,
    systemErrorExit, unknownArgumentExit,
)
from gam.util.fileio import closeFile
from gam.util.gdoc import openCSVFileReader
from gam.util.output import setSysExitRC, stderrErrorMsg
from gam.constants import (
    DAYS_OF_WEEK, GOOGLE_MEETID_FORMAT_REQUIRED, GOOGLE_MEETID_PATTERN,
    NO_ENTITIES_FOUND_RC, UNKNOWN, USAGE_ERROR_RC,
)

from gam.cmd.calendar import checkCalendarExists, getNormalizedCalIdCal
from gam.cmd.calendar.acls import EVENT_TYPES_CHOICE_MAP, EVENT_TYPE_BIRTHDAY
from gam.cmd.calendar.calendars import getUserCalendarEntity, _validateUserGetCalendarIds


def _createImportCalendarEvent(users, function):
  calendarEntity = getUserCalendarEntity()
  body, parameters = _getCalendarCreateImportUpdateEventOptions(function, Ent.USER)
  i, count, users = getEntityArgument(users)
  for user in users:
    i += 1
    user, cal, calIds, jcount = _validateUserGetCalendarIds(user, i, count, calendarEntity, Ent.EVENT, Act.MODIFIER_TO)
    if jcount == 0:
      continue
    Ind.Increment()
    _createCalendarEvents(user, cal, function, calIds, jcount, body, parameters)
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
  calendarEventEntity = getCalendarEventEntity()
  body, parameters = _getCalendarCreateImportUpdateEventOptions('update', Ent.USER)
  i, count, users = getEntityArgument(users)
  for user in users:
    i += 1
    origUser = user
    user, cal, calIds, jcount = _validateUserGetCalendarIds(user, i, count, calendarEntity, Ent.EVENT, Act.MODIFIER_IN)
    if jcount == 0:
      continue
    Ind.Increment()
    _updateCalendarEvents(origUser, user, cal, calIds, jcount, calendarEventEntity, body, parameters)
    Ind.Decrement()

# gam <UserTypeEntity> delete events <UserCalendarEntity> <EventEntity>
#	[batchsize <Integer>] [doit] [<EventNotificationAttribute>]
def deleteCalendarEvents(users):
  calendarEntity = getUserCalendarEntity()
  calendarEventEntity = getCalendarEventEntity()
  parameters = _getCalendarDeleteEventOptions()
  i, count, users = getEntityArgument(users)
  for user in users:
    i += 1
    origUser = user
    user, cal, calIds, jcount = _validateUserGetCalendarIds(user, i, count, calendarEntity, Ent.EVENT, Act.MODIFIER_FROM)
    if jcount == 0:
      continue
    Ind.Increment()
    _deleteCalendarEvents(origUser, user, cal, calIds, jcount, calendarEventEntity, parameters)
    Ind.Decrement()

# gam <UserTypeEntity> purge events <UserCalendarEntity> <EventEntity>
#	[batchsize <Integer>] [doit] [<EventNotificationAttribute>]
def purgeCalendarEvents(users):
  calendarEntity = getUserCalendarEntity()
  calendarEventEntity = getCalendarEventEntity()
  parameters = _getCalendarDeleteEventOptions()
  i, count, users = getEntityArgument(users)
  for user in users:
    i += 1
    origUser = user
    user, cal, calIds, jcount = _validateUserGetCalendarIds(user, i, count, calendarEntity, Ent.EVENT, Act.MODIFIER_FROM)
    if jcount == 0:
      continue
    Ind.Increment()
    _purgeCalendarEvents(origUser, user, cal, calIds, jcount, calendarEventEntity, parameters, False)
    Ind.Decrement()

# gam <UserTypeEntity> wipe events <UserCalendarEntity>
def wipeCalendarEvents(users):
  calendarEntity = getUserCalendarEntity()
  checkForExtraneousArguments()
  i, count, users = getEntityArgument(users)
  for user in users:
    i += 1
    user, cal, calIds, jcount = _validateUserGetCalendarIds(user, i, count, calendarEntity, Ent.EVENT, Act.MODIFIER_FROM)
    if jcount == 0:
      continue
    Ind.Increment()
    _wipeCalendarEvents(user, cal, calIds, jcount)
    Ind.Decrement()

# gam <UserTypeEntity> move events <UserCalendarEntity> <EventEntity> to|destination <CalendarItem> [<EventNotificationAttribute>]
def moveCalendarEvents(users):
  calendarEntity = getUserCalendarEntity()
  calendarEventEntity = getCalendarEventEntity()
  checkArgumentPresent(['to', 'destination'])
  newCalId = convertUIDtoEmailAddress(getString(Cmd.OB_CALENDAR_ITEM))
  parameters, _ = _getCalendarMoveEventsOptions()
  if not checkCalendarExists(None, newCalId, 0, 0, True):
    return
  i, count, users = getEntityArgument(users)
  for user in users:
    i += 1
    origUser = user
    user, cal, calIds, jcount = _validateUserGetCalendarIds(user, i, count, calendarEntity, Ent.EVENT, Act.MODIFIER_FROM, newCalId=newCalId)
    if jcount == 0:
      continue
    Ind.Increment()
    _moveCalendarEvents(origUser, user, cal, calIds, jcount, calendarEventEntity, newCalId, parameters)
    Ind.Decrement()

# gam <UserTypeEntity> empty calendartrash <UserCalendarEntity>
def emptyCalendarTrash(users):
  calendarEntity = getUserCalendarEntity()
  checkForExtraneousArguments()
  i, count, users = getEntityArgument(users)
  for user in users:
    i += 1
    Act.Set(Act.PURGE)
    user, cal, calIds, jcount = _validateUserGetCalendarIds(user, i, count, calendarEntity, Ent.TRASHED_EVENT, Act.MODIFIER_FROM)
    if jcount == 0:
      continue
    Ind.Increment()
    _emptyCalendarTrash(user, cal, calIds, jcount)
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
      return(getChoice(CALENDAR_ATTENDEE_OPTIONAL_CHOICE_MAP, defaultChoice=None, mapChoice=True),
             getChoice(CALENDAR_ATTENDEE_STATUS_CHOICE_MAP, defaultChoice=None, mapChoice=True))
    return (None, None)

  calendarEntity = getUserCalendarEntity()
  calendarEventEntity = getCalendarEventEntity()
  anyOrganizer = doIt = splitUpdate = False
  parameters = {'sendUpdates': 'none'}
  attendeeMap = {}
  errors = 0
  while Cmd.ArgumentsRemaining():
    myarg = getArgument()
    if myarg in {'csv', 'csvfile'}:
      errors = 0
      f, csvFile, _ = openCSVFileReader(getString(Cmd.OB_FILE_NAME), fieldnames=['addr', 'op', 'optional', 'status'])
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
          stderrErrorMsg(Msg.INVALID_ATTENDEE_CHANGE.format(','.join([updAddr, updOp, updStatus, updOptional])))
          errors += 1
          continue
        updAddr = normalizeEmailAddressOrUID(updAddr, noUid=True)
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
      closeFile(f)
    elif myarg == 'delete':
      updAddr = getEmailAddress(noUid=True)
      attendeeMap[updAddr] = {'op': 'delete'}
    elif myarg == 'deleteentity':
      for updAddr in getNormalizedEmailAddressEntity(noUid=True):
        attendeeMap[updAddr] = {'op': 'delete'}
    elif myarg in {'add', 'addstatus'}:
      updOptional, updStatus = getStatus(myarg)
      updAddr = getEmailAddress(noUid=True)
      attendeeMap[updAddr] = {'op': 'add', 'status': updStatus, 'optional': updOptional, 'done': False}
    elif myarg in {'addentity', 'addentitystatus'}:
      updOptional, updStatus = getStatus(myarg)
      for updAddr in getNormalizedEmailAddressEntity(noUid=True):
        attendeeMap[updAddr] = {'op': 'add', 'status': updStatus, 'optional': updOptional, 'done': False}
    elif myarg in {'update', 'updatestatus'}:
      updOptional, updStatus = getStatus(myarg)
      updAddr = getEmailAddress(noUid=True)
      attendeeMap[updAddr] = {'op': 'update', 'status': updStatus, 'optional': updOptional, 'done': False}
    elif myarg in {'updateentity', 'updateentitystatus'}:
      updOptional, updStatus = getStatus(myarg)
      for updAddr in getNormalizedEmailAddressEntity(noUid=True):
        attendeeMap[updAddr] = {'op': 'update', 'status': updStatus, 'optional': updOptional, 'done': False}
    elif myarg in {'replace', 'replacestatus'}:
      updOptional, updStatus = getStatus(myarg)
      updAddr = getEmailAddress(noUid=True)
      newAddr = getEmailAddress(noUid=True)
      attendeeMap[updAddr] = {'op': 'replace', 'status': updStatus, 'optional': updOptional, 'email': newAddr, 'done': False}
    elif myarg in {'anyorganizer', 'allevents'}:
      anyOrganizer = True
    elif _getCalendarSendUpdates(myarg, parameters):
      pass
    elif myarg == 'doit':
      doIt = True
    elif myarg == 'dryrun':
      doIt = False
    elif myarg == 'splitupdate':
      splitUpdate = True
    else:
      unknownArgumentExit()
  if not attendeeMap:
    missingArgumentExit(Msg.UPDATE_ATTENDEE_CHANGES)
  ucount = len(attendeeMap)
  if errors:
    systemErrorExit(USAGE_ERROR_RC, '')
  removeMessage = Msg.ATTENDEES_REMOVE
  addMessage = Msg.ATTENDEES_ADD_REMOVE if not splitUpdate else Msg.ATTENDEES_ADD
  fieldsList = ['attendees', 'id', 'organizer', 'status', 'summary']
  i, count, users = getEntityArgument(users)
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
      calId, cal, events, kcount = _validateCalendarGetEvents(origUser, user, cal, calId, j, jcount, calendarEventEntity,
                                                              fieldsList, True)
      if kcount == 0:
        continue
      Ind.Increment()
      k = 0
      for event in events:
        k += 1
        eventSummary = event.get('summary', event['id'])
        if event['status'] == 'cancelled':
          entityActionNotPerformedWarning([Ent.EVENT, eventSummary], Msg.EVENT_IS_CANCELED, k, kcount)
          continue
        if not anyOrganizer and not event.get('organizer', {}).get('self'):
          entityActionNotPerformedWarning([Ent.EVENT, eventSummary], Msg.USER_IS_NOT_ORGANIZER, k, kcount)
          continue
        needsUpdate = False
        for _, v in sorted(attendeeMap.items()):
          v['done'] = False
        updatedAttendeesAdd = []
        updatedAttendeesRemove = []
        entityPerformActionNumItems([Ent.EVENT, eventSummary], ucount, Ent.ATTENDEE, k, kcount)
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
            entityPerformAction([Ent.EVENT, eventSummary, Ent.ATTENDEE, oldAddr], u, ucount)
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
                entityPerformAction([Ent.EVENT, eventSummary, Ent.ATTENDEE, oldAddr], u, ucount)
                needsUpdate = True
              else:
                Act.Set(Act.SKIP)
                entityPerformAction([Ent.EVENT, eventSummary, Ent.ATTENDEE, oldAddr], u, ucount)
              updatedAttendeesAdd.append(attendee)
            else: #replace
              u += 1
              update['done'] = True
              attendee['email'] = update['email']
              attendee['responseStatus'] = updStatus if updStatus is not None else oldStatus
              attendee['optional'] = updOptional if updOptional is not None else oldOptional
              Act.Set(Act.REPLACE)
              entityPerformActionModifierNewValue([Ent.EVENT, eventSummary, Ent.ATTENDEE, oldAddr], Act.MODIFIER_WITH, update['email'], u, ucount)
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
            entityPerformAction([Ent.EVENT, eventSummary, Ent.ATTENDEE, newAddr], u, ucount)
            updatedAttendeesAdd.append(attendee)
            needsUpdate = True
        for newAddr, v in sorted(attendeeMap.items()):
          if not v['done']:
            u += 1
            Act.Set(Act.SKIP)
            entityPerformAction([Ent.EVENT, eventSummary, Ent.ATTENDEE, newAddr], u, ucount)
        Ind.Decrement()
        if needsUpdate:
          Act.Set(Act.UPDATE)
          if doIt:
            status = True
            if splitUpdate:
              try:
                callGAPI(cal.events(), 'patch',
                         throwReasons=GAPI.CALENDAR_THROW_REASONS+[GAPI.NOT_FOUND, GAPI.FORBIDDEN, GAPI.INVALID],
                         calendarId=calId, eventId=event['id'], body={'attendees': updatedAttendeesRemove},
                         sendUpdates=parameters['sendUpdates'], fields='')
                entityActionPerformedMessage([Ent.EVENT, eventSummary], removeMessage, j, jcount)
              except GAPI.notFound as e:
                if not checkCalendarExists(cal, calId, i, count):
                  entityUnknownWarning(Ent.CALENDAR, calId, j, jcount)
                  break
                entityActionFailedWarning([Ent.CALENDAR, calId, Ent.EVENT, eventSummary], str(e), k, kcount)
                status = False
              except (GAPI.forbidden, GAPI.invalid) as e:
                entityActionFailedWarning([Ent.CALENDAR, calId], str(e), j, jcount)
                break
              except GAPI.notACalendarUser:
                userCalServiceNotEnabledWarning(user, i, count)
                break
            if status:
              try:
                callGAPI(cal.events(), 'patch',
                         throwReasons=GAPI.CALENDAR_THROW_REASONS+[GAPI.NOT_FOUND, GAPI.FORBIDDEN, GAPI.INVALID],
                         calendarId=calId, eventId=event['id'], body={'attendees': updatedAttendeesAdd},
                         sendUpdates=parameters['sendUpdates'], fields='')
                entityActionPerformedMessage([Ent.EVENT, eventSummary], addMessage, jcount)
              except GAPI.notFound as e:
                if not checkCalendarExists(cal, calId, i, count):
                  entityUnknownWarning(Ent.CALENDAR, calId, j, jcount)
                  break
                entityActionFailedWarning([Ent.CALENDAR, calId, Ent.EVENT, eventSummary], str(e), k, kcount)
              except (GAPI.forbidden, GAPI.invalid) as e:
                entityActionFailedWarning([Ent.CALENDAR, calId], str(e), j, jcount)
                break
              except GAPI.notACalendarUser:
                userCalServiceNotEnabledWarning(user, i, count)
                break
          else:
            entityActionNotPerformedWarning([Ent.EVENT, eventSummary], Msg.USE_DOIT_ARGUMENT_TO_PERFORM_ACTION, j, jcount)
      Ind.Decrement()
    Ind.Decrement()

# gam <UserTypeEntity> info events <UserCalendarEntity> <EventEntity> [maxinstances <Number>]
#	[fields <EventFieldNameList>] [showdayofweek]
#	[formatjson]
def infoCalendarEvents(users):
  calendarEntity = getUserCalendarEntity()
  calendarEventEntity = getCalendarEventEntity()
  FJQC, fieldsList = _getCalendarInfoEventOptions(calendarEventEntity)
  i, count, users = getEntityArgument(users)
  for user in users:
    i += 1
    origUser = user
    user, cal, calIds, jcount = _validateUserGetCalendarIds(user, i, count, calendarEntity, Ent.EVENT, Act.MODIFIER_IN, showAction=not FJQC.formatJSON)
    if jcount == 0:
      continue
    Ind.Increment()
    _infoCalendarEvents(origUser, user, cal, calIds, jcount, calendarEventEntity, FJQC, fieldsList)
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
  calendarEventEntity = getCalendarEventEntity()
  csvPF, FJQC, fieldsList, addCSVData, attendeesList = _getCalendarPrintShowEventOptions(calendarEventEntity, Ent.USER)
  i, count, users = getEntityArgument(users)
  for user in users:
    i += 1
    origUser = user
    user, cal, calIds, jcount = _validateUserGetCalendarIds(user, i, count, calendarEntity, Ent.EVENT, Act.MODIFIER_FROM,
                                                            showAction=not csvPF and not FJQC.formatJSON)
    if jcount == 0:
      continue
    Ind.Increment()
    _printShowCalendarEvents(origUser, user, cal, calIds, jcount, calendarEventEntity,
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

def getCalendarEventEntity():
  calendarEventEntity = initCalendarEventEntity()
  while Cmd.ArgumentsRemaining():
    myarg = getArgument()
    if myarg in {'event', 'events'}:
      entitySelector = getEntitySelector()
      if entitySelector:
        entityList = getEntitySelection(entitySelector, False)
        if isinstance(entityList, dict):
          calendarEventEntity['dict'] = entityList
        else:
          calendarEventEntity['list'] = entityList
      else:
        calendarEventEntity['list'].extend(convertEntityToList(getString(Cmd.OB_EVENT_ID)))
    elif myarg in {'id', 'eventid'}:
      calendarEventEntity['list'].append(getString(Cmd.OB_EVENT_ID))
    elif myarg in {'q', 'query', 'eventquery'}:
      calendarEventEntity['queries'].append(getString(Cmd.OB_QUERY))
    elif myarg == 'matchfield':
      matchField = getChoice(LIST_EVENTS_MATCH_FIELDS, mapChoice=True)
      if matchField[0] == 'organizer' and matchField[1] == 'self':
        calendarEventEntity['matches'].append((matchField, getBoolean()))
      elif matchField[0] != 'attendees' or matchField[1] == 'match':
        calendarEventEntity['matches'].append((matchField, getREPattern(re.IGNORECASE)))
      elif matchField[0] == 'attendees' and matchField[1] in {'onlydomainlist', 'domainlist', 'notdomainlist'}:
        calendarEventEntity['matches'].append((matchField, set(getString(Cmd.OB_DOMAIN_NAME_LIST).replace(',', ' ').split())))
      elif matchField[1] == 'email':
        calendarEventEntity['matches'].append((matchField, getNormalizedEmailAddressEntity()))
      elif matchField[1] == 'organizer':
        calendarEventEntity['matches'].append((matchField, getBoolean(defaultValue=None), getNormalizedEmailAddressEntity()))
      else: #status
        calendarEventEntity['matches'].append((matchField,
                                               getChoice(CALENDAR_ATTENDEE_OPTIONAL_CHOICE_MAP, defaultChoice=False, mapChoice=True),
                                               getChoice(CALENDAR_ATTENDEE_STATUS_CHOICE_MAP, defaultChoice='needsAction', mapChoice=True),
                                               getNormalizedEmailAddressEntity()))
    elif myarg == 'maxinstances':
      calendarEventEntity['maxinstances'] = getInteger(minVal=-1)
    elif _getCalendarListEventsProperty(myarg, LIST_EVENTS_SELECT_PROPERTIES, calendarEventEntity['kwargs']):
      pass
    else:
      Cmd.Backup()
      break
  return calendarEventEntity

CALENDAR_EVENT_SENDUPDATES_CHOICE_MAP = {'all': 'all', 'externalonly': 'externalOnly', 'none': 'none'}

def _getCalendarSendUpdates(myarg, parameters):
  if myarg == 'sendnotifications':
    parameters['sendUpdates'] = 'all' if getBoolean() else 'none'
  elif myarg == 'notifyattendees':
    parameters['sendUpdates'] = 'all'
  elif myarg == 'sendupdates':
    parameters['sendUpdates'] = getChoice(CALENDAR_EVENT_SENDUPDATES_CHOICE_MAP, mapChoice=True)
  else:
    return False
  return True

def _getCalendarEventReminders(myarg, body):
  if myarg == 'noreminders':
    body['reminders'] = {'overrides': [], 'useDefault': False}
  elif myarg == 'reminder':
    body.setdefault('reminders', {'overrides': [], 'useDefault': False})
    body['reminders']['overrides'].append(getCalendarReminder())
  else:
    return False
  return True

CALENDAR_MIN_COLOR_INDEX = 1
CALENDAR_MAX_COLOR_INDEX = 24

CALENDAR_EVENT_MIN_COLOR_INDEX = 1
CALENDAR_EVENT_MAX_COLOR_INDEX = 11

CALENDAR_ATTENDEE_OPTIONAL_CHOICE_MAP = {
  'optional': True,
  'required': False,
  'true': True,
  'false': False,
  '': None,
  }
CALENDAR_ATTENDEE_STATUS_CHOICE_MAP = {
  'accepted': 'accepted',
  'declined': 'declined',
  'needsaction': 'needsAction',
  'tentative': 'tentative',
  '': None,
  }
CALENDAR_EVENT_STATUS_CHOICES = ['confirmed', 'tentative', 'cancelled']
CALENDAR_EVENT_TRANSPARENCY_CHOICES = ['opaque', 'transparent']
CALENDAR_EVENT_VISIBILITY_CHOICES = ['default', 'public', 'private', 'confedential']

EVENT_JSON_CLEAR_FIELDS = ['created', 'creator', 'endTimeUpspecified', 'hangoutLink', 'htmlLink', 'eventType',
                           'privateCopy', 'locked', 'recurringEventId', 'updated']
EVENT_JSON_INSERT_CLEAR_FIELDS = ['iCalUID', 'id', 'organizer']
EVENT_JSON_UPDATE_CLEAR_FIELDS = ['iCalUID', 'id', 'organizer']
EVENT_JSON_SUBFIELD_CLEAR_FIELDS = {
  'attendees': ['id', 'organizer', 'self'],
  'attachments': ['fileId', 'iconLink', 'mimeType', 'title'],
  'organizer': ['id', 'self'],
  }
EVENT_JSONATTENDEES_SUBFIELD_CLEAR_FIELDS = {
  'attendees': ['id', 'organizer', 'self'],
  }

def _validateCalendarGetEvents(origUser, user, origCal, calId, j, jcount, calendarEventEntity,
                               fieldsList, showAction):
  if calendarEventEntity['dict']:
    if origUser:
      if not GM.Globals[GM.CSV_SUBKEY_FIELD]:
        calEventIds = calendarEventEntity['dict'][calId]
      else:
        calEventIds = calendarEventEntity['dict'][origUser][calId]
    else:
      calEventIds = calendarEventEntity['dict'][calId]
  else:
    calEventIds = calendarEventEntity['list']
  calId, cal = getNormalizedCalIdCal(origCal, calId, user, j, jcount)
  if not cal:
    return (calId, cal, [], 0)
  eventIdsSet = set()
  eventsList = []
  fields = getFieldsFromFieldsList(fieldsList)
  ifields = getItemFieldsFromFieldsList('items', fieldsList)
  try:
    if not calEventIds:
      if len(calendarEventEntity['queries']) <= 1:
        if len(calendarEventEntity['queries']) == 1:
          calendarEventEntity['kwargs']['q'] = calendarEventEntity['queries'][0]
        events = callGAPIpages(cal.events(), 'list', 'items',
                               throwReasons=GAPI.CALENDAR_THROW_REASONS+[GAPI.NOT_FOUND, GAPI.FORBIDDEN, GAPI.INVALID],
                               calendarId=calId, fields=ifields,
                               maxResults=GC.Values[GC.EVENT_MAX_RESULTS], **calendarEventEntity['kwargs'])
        for event in events:
          for match in calendarEventEntity['matches']:
            if not _eventMatches(event, match):
              break
          else:
            eventsList.append(event)
      else:
        for query in calendarEventEntity['queries']:
          calendarEventEntity['kwargs']['q'] = query
          events = callGAPIpages(cal.events(), 'list', 'items',
                                 throwReasons=GAPI.CALENDAR_THROW_REASONS+[GAPI.NOT_FOUND, GAPI.FORBIDDEN, GAPI.INVALID],
                                 calendarId=calId, fields=ifields,
                                 maxResults=GC.Values[GC.EVENT_MAX_RESULTS], **calendarEventEntity['kwargs'])
          for event in events:
            for match in calendarEventEntity['matches']:
              if not _eventMatches(event, match):
                break
            else:
              eventId = event['id']
              if eventId not in eventIdsSet:
                eventsList.append(event)
                eventIdsSet.add(eventId)
    else:
      k = 0
      for eventId in calEventIds:
        k += 1
        if eventId not in eventIdsSet:
          eventsList.append(callGAPI(cal.events(), 'get',
                                     throwReasons=GAPI.CALENDAR_THROW_REASONS+[GAPI.NOT_FOUND, GAPI.DELETED, GAPI.FORBIDDEN],
                                     calendarId=calId, eventId=eventId, fields=fields))
          eventIdsSet.add(eventId)
    kcount = len(eventsList)
    if showAction:
      entityPerformActionNumItems([Ent.CALENDAR, calId], kcount, Ent.EVENT, j, jcount)
    if kcount == 0:
      setSysExitRC(NO_ENTITIES_FOUND_RC)
    return (calId, cal, eventsList, kcount)
  except (GAPI.notFound, GAPI.deleted) as e:
    if not checkCalendarExists(cal, calId, j, jcount):
      entityUnknownWarning(Ent.CALENDAR, calId, j, jcount)
    else:
      entityActionFailedWarning([Ent.CALENDAR, calId, Ent.EVENT, eventId], str(e), j, jcount)
  except (GAPI.forbidden, GAPI.invalid) as e:
    entityActionFailedWarning([Ent.CALENDAR, calId], str(e), j, jcount)
  except GAPI.notACalendarUser:
    userCalServiceNotEnabledWarning(calId, j, jcount)
  return (calId, cal, [], 0)

def _getCalendarCreateImportUpdateEventOptions(function, entityType):

  body = {}
  parameters = {'clearAttendees': False, 'replaceMode': False, 'clearResources': False,
                'attendees': [], 'removeAttendees': set(),
                'replaceDescription': [], 'sendUpdates': 'none',
                'csvPF': None, 'FJQC': FormatJSONQuoteChar(None), 'showDayOfWeek': False}
  while Cmd.ArgumentsRemaining():
    myarg = getArgument()
    if myarg == 'csv':
      parameters['csvPF'] = CSVPrintFile(['primaryEmail', 'calendarId', 'id'] if entityType == Ent.USER else ['calendarId', 'id'], 'sortall', indexedTitles=EVENT_INDEXED_TITLES)
      parameters['FJQC'].SetCsvPF(parameters['csvPF'])
    elif parameters['csvPF'] and myarg == 'todrive':
      parameters['csvPF'].GetTodriveParameters()
    elif myarg == 'showdayofweek':
      parameters['showDayOfWeek'] = True
    elif _getCalendarEventAttribute(myarg, body, parameters, function):
      pass
    else:
      parameters['FJQC'].GetFormatJSONQuoteChar(myarg, True)
  return (body, parameters)

def _setEventRecurrenceTimeZone(cal, calId, body, parameters, i, count):
  if ('recurrence' in body) and (('start' in body) or ('end' in body)):
    timeZone = parameters.get('timeZone')
    if not timeZone:
      try:
        timeZone = callGAPI(cal.calendars(), 'get',
                            throwReasons=GAPI.CALENDAR_THROW_REASONS+[GAPI.NOT_FOUND, GAPI.FORBIDDEN, GAPI.INVALID],
                            calendarId=calId, fields='timeZone')['timeZone']
      except (GAPI.notFound, GAPI.forbidden, GAPI.invalid) as e:
        entityActionFailedWarning([Ent.CALENDAR, calId], str(e), i, count)
        return False
      except GAPI.notACalendarUser:
        userCalServiceNotEnabledWarning(calId, i, count)
        return False
    if 'start' in body:
      body['start']['timeZone'] = timeZone
    if 'end' in body:
      body['end']['timeZone'] = timeZone
  return True

def _getEventDaysOfWeek(event):
  for attr in ['start', 'end']:
    if attr in event:
      if 'date' in event[attr]:
        try:
          dateTime = arrow.Arrow.strptime(event[attr]['date'], YYYYMMDD_FORMAT)
          event[attr]['dayOfWeek'] = DAYS_OF_WEEK[dateTime.weekday()]
        except ValueError:
          pass
      elif 'dateTime' in event[attr]:
        try:
          dateTime = arrow.get(event[attr]['dateTime'])
          event[attr]['dayOfWeek'] = DAYS_OF_WEEK[dateTime.weekday()]
        except (arrow.parser.ParserError, OverflowError):
          pass

def _createCalendarEvents(user, origCal, function, calIds, count, body, parameters):
  if parameters['attendees']:
    body['attendees'] = parameters.pop('attendees')
  fields = 'id' if parameters['csvPF'] is None else '*'
  i = 0
  for calId in calIds:
    i += 1
    calId, cal = getNormalizedCalIdCal(origCal, calId, user, i, count)
    if not cal:
      continue
    if not _setEventRecurrenceTimeZone(cal, calId, body, parameters, i, count):
      continue
    event = {'id': body.get('id', UNKNOWN)}
    if function == 'import' and body.get('status', '') == 'cancelled':
      entityActionNotPerformedWarning([Ent.CALENDAR, calId, Ent.EVENT, body.get('iCalUID', event['id'])], Msg.EVENT_IS_CANCELED, count)
      continue
    try:
      if function == 'insert':
        event = callGAPI(cal.events(), 'insert',
                         throwReasons=GAPI.CALENDAR_THROW_REASONS+[GAPI.INVALID, GAPI.REQUIRED, GAPI.TIME_RANGE_EMPTY, GAPI.EVENT_DURATION_EXCEEDS_LIMIT,
                                                                   GAPI.REQUIRED_ACCESS_LEVEL, GAPI.DUPLICATE, GAPI.FORBIDDEN,
                                                                   GAPI.MALFORMED_WORKING_LOCATION_EVENT, GAPI.BAD_REQUEST],
                         calendarId=calId, conferenceDataVersion=1, sendUpdates=parameters['sendUpdates'], supportsAttachments=True, body=body, fields=fields)
      else:
        event = callGAPI(cal.events(), 'import_',
                         throwReasons=GAPI.CALENDAR_THROW_REASONS+[GAPI.INVALID, GAPI.REQUIRED, GAPI.TIME_RANGE_EMPTY, GAPI.EVENT_DURATION_EXCEEDS_LIMIT,
                                                                   GAPI.REQUIRED_ACCESS_LEVEL, GAPI.DUPLICATE, GAPI.FORBIDDEN,
                                                                   GAPI.MALFORMED_WORKING_LOCATION_EVENT, GAPI.BAD_REQUEST,
                                                                   GAPI.PARTICIPANT_IS_NEITHER_ORGANIZER_NOR_ATTENDEE],
                         calendarId=calId, conferenceDataVersion=1, supportsAttachments=True, body=body, fields=fields)
      if parameters['csvPF'] is None:
        entityActionPerformed([Ent.CALENDAR, calId, Ent.EVENT, event['id']], i, count)
      else:
        if parameters['showDayOfWeek']:
          _getEventDaysOfWeek(event)
        _printCalendarEvent(user, calId, event, parameters['csvPF'], parameters['FJQC'], {}, False)
    except (GAPI.invalid, GAPI.required, GAPI.timeRangeEmpty, GAPI.eventDurationExceedsLimit,
            GAPI.requiredAccessLevel, GAPI.participantIsNeitherOrganizerNorAttendee,
            GAPI.malformedWorkingLocationEvent, GAPI.badRequest) as e:
      entityActionFailedWarning([Ent.CALENDAR, calId, Ent.EVENT, event['id']], str(e), i, count)
    except GAPI.duplicate as e:
      entityActionFailedWarning([Ent.CALENDAR, calId, Ent.EVENT, event['id']], str(e), i, count)
    except GAPI.forbidden as e:
      entityActionFailedWarning([Ent.CALENDAR, calId], str(e), i, count)
      break
    except GAPI.notACalendarUser:
      userCalServiceNotEnabledWarning(calId, i, count)
      break
  if parameters['csvPF']:
    parameters['csvPF'].writeCSVfile('Calendar Created Events')

# gam calendars <CalendarEntity> create event [id <String>] <EventAddAttribute>+
#	[showdayofweek]
#	[csv [todrive <ToDriveAttribute>*] [formatjson [quotechar <Character>]]]
# gam calendar <UserItem> addevent [id <String>] <EventAddAttribute>+
#	[showdayofweek]
#	[csv [todrive <ToDriveAttribute>*] [formatjson [quotechar <Character>]]]
def doCalendarsCreateEvent(calIds):
  body, parameters = _getCalendarCreateImportUpdateEventOptions('insert', Ent.CALENDAR)
  _createCalendarEvents(None, None, 'insert', calIds, len(calIds), body, parameters)

# gam calendars <CalendarEntity> import event icaluid <iCalUID> <EventImportAttribute>+
#	[showdayofweek]
#	[csv [todrive <ToDriveAttribute>*] [formatjson [quotechar <Character>]]]
def doCalendarsImportEvent(calIds):
  body, parameters = _getCalendarCreateImportUpdateEventOptions('import', Ent.CALENDAR)
  _createCalendarEvents(None, None, 'import', calIds, len(calIds), body, parameters)

def _updateCalendarEvents(origUser, user, origCal, calIds, count, calendarEventEntity, body, parameters):
  updateFieldList = []
  if parameters['replaceDescription']:
    updateFieldList.append('description')
  if not parameters['replaceMode'] and (parameters['attendees'] or parameters['removeAttendees'] or parameters['clearResources']):
    updateFieldList.append('attendees')
  updateFields = ','.join(updateFieldList)
  if 'attendees' not in updateFieldList:
    if parameters['attendees']:
      body['attendees'] = parameters.pop('attendees')
    elif parameters['clearAttendees']:
      body['attendees'] = []
  pfields = '' if parameters['csvPF'] is None else '*'
  i = 0
  for calId in calIds:
    i += 1
    calId, cal, calEventIds, jcount = _validateCalendarGetEventIDs(origUser, user, origCal, calId, i, count, calendarEventEntity)
    if jcount == 0:
      continue
    if not _setEventRecurrenceTimeZone(cal, calId, body, parameters, i, count):
      continue
    Ind.Increment()
    j = 0
    for eventId in calEventIds:
      j += 1
      try:
        if updateFieldList:
          event = callGAPI(cal.events(), 'get',
                           throwReasons=GAPI.CALENDAR_THROW_REASONS+[GAPI.NOT_FOUND, GAPI.DELETED, GAPI.FORBIDDEN, GAPI.BACKEND_ERROR],
                           retryReasons=GAPI.SERVICE_NOT_AVAILABLE_RETRY_REASONS+[GAPI.BACKEND_ERROR],
                           calendarId=calId, eventId=eventId, fields=updateFields)
          if 'description' in updateFieldList and 'description' in event:
            body['description'] = event['description']
            for replacement in parameters['replaceDescription']:
              body['description'] = re.sub(replacement[0], replacement[1], body['description'])
          if 'attendees' in updateFieldList:
            if not parameters['clearAttendees']:
              if 'attendees' in event:
                body['attendees'] = event['attendees']
                for addAttendee in parameters['attendees']:
                  for attendee in body['attendees']:
                    if attendee['email'].lower() == addAttendee['email']:
                      attendee.update(addAttendee)
                      break
                  else:
                    body['attendees'].append(addAttendee)
              elif parameters['attendees']:
                body['attendees'] = parameters['attendees']
              else:
                body['attendees'] = []
            elif parameters['attendees']:
              body['attendees'] = parameters['attendees']
            else:
              body['attendees'] = []
            if parameters['removeAttendees']:
              body['attendees'] = [attendee for attendee in body['attendees'] if attendee['email'].lower() not in parameters['removeAttendees']]
            if parameters['clearResources']:
              body['attendees'] = [attendee for attendee in body['attendees'] if not attendee['email'].lower().endswith('@resource.calendar.google.com')]
        event = callGAPI(cal.events(), 'patch',
                         throwReasons=GAPI.CALENDAR_THROW_REASONS+[GAPI.NOT_FOUND, GAPI.DELETED, GAPI.FORBIDDEN, GAPI.BACKEND_ERROR,
                                                                   GAPI.INVALID, GAPI.REQUIRED, GAPI.TIME_RANGE_EMPTY, GAPI.EVENT_DURATION_EXCEEDS_LIMIT,
                                                                   GAPI.REQUIRED_ACCESS_LEVEL, GAPI.CANNOT_CHANGE_ORGANIZER_OF_INSTANCE,
                                                                   GAPI.MALFORMED_WORKING_LOCATION_EVENT, GAPI.EVENT_TYPE_RESTRICTION, GAPI.BAD_REQUEST],
                         retryReasons=GAPI.SERVICE_NOT_AVAILABLE_RETRY_REASONS+[GAPI.BACKEND_ERROR],
                         calendarId=calId, eventId=eventId, conferenceDataVersion=1, sendUpdates=parameters['sendUpdates'], supportsAttachments=True,
                         body=body, fields=pfields)
        if parameters['csvPF'] is None:
          entityActionPerformed([Ent.CALENDAR, calId, Ent.EVENT, eventId], j, jcount)
        else:
          if parameters['showDayOfWeek']:
            _getEventDaysOfWeek(event)
          _printCalendarEvent(user, calId, event, parameters['csvPF'], parameters['FJQC'], {}, False)
      except (GAPI.notFound, GAPI.deleted) as e:
        if not checkCalendarExists(cal, calId, j, jcount):
          entityUnknownWarning(Ent.CALENDAR, calId, j, jcount)
          break
        entityActionFailedWarning([Ent.CALENDAR, calId, Ent.EVENT, eventId], str(e), j, jcount)
      except (GAPI.forbidden, GAPI.backendError, GAPI.invalid, GAPI.required, GAPI.timeRangeEmpty, GAPI.eventDurationExceedsLimit,
              GAPI.requiredAccessLevel, GAPI.cannotChangeOrganizerOfInstance, GAPI.malformedWorkingLocationEvent,
              GAPI.eventTypeRestriction, GAPI.badRequest) as e:
        entityActionFailedWarning([Ent.CALENDAR, calId, Ent.EVENT, eventId], str(e), j, jcount)
      except GAPI.notACalendarUser:
        userCalServiceNotEnabledWarning(calId, i, count)
        break
    Ind.Decrement()
  if parameters['csvPF']:
    parameters['csvPF'].writeCSVfile('Calendar Updated Events')

# gam calendars <CalendarEntity> update events [<EventEntity>] [replacemode] <EventUpdateAttribute>+ [<EventNotificationAttribute>]
#	[showdayofweek]
#	[csv [todrive <ToDriveAttribute>*] [formatjson [quotechar <Character>]]]
def doCalendarsUpdateEvents(calIds):
  calendarEventEntity = getCalendarEventEntity()
  body, parameters = _getCalendarCreateImportUpdateEventOptions('update', Ent.CALENDAR)
  _updateCalendarEvents(None, None, None, calIds, len(calIds), calendarEventEntity, body, parameters)

# gam calendar <CalendarEntity> updateevent <EventID> [replacemode] <EventUpdateAttribute>+ [<EventNotificationAttribute>]
#	[showdayofweek]
#	[csv [todrive <ToDriveAttribute>*] [formatjson [quotechar <Character>]]]
def doCalendarsUpdateEventsOld(calIds):
  calendarEventEntity = initCalendarEventEntity()
  calendarEventEntity['list'].append(getString(Cmd.OB_EVENT_ID))
  body, parameters = _getCalendarCreateImportUpdateEventOptions('update', Ent.CALENDAR)
  _updateCalendarEvents(None, None, None, calIds, len(calIds), calendarEventEntity, body, parameters)

def _getCalendarDeleteEventOptions(calendarEventEntity=None):
  parameters = {'sendUpdates': 'none', 'doIt': False, 'batch_size': 0}
  while Cmd.ArgumentsRemaining():
    myarg = getArgument()
    if _getCalendarSendUpdates(myarg, parameters):
      pass
    elif calendarEventEntity and myarg in {'id', 'eventid'}:
      calendarEventEntity['list'].append(getString(Cmd.OB_EVENT_ID))
    elif myarg == 'doit':
      parameters['doIt'] = True
    elif myarg == 'batchsize':
      parameters['batch_size'] = getInteger(minVal=0, maxVal=1000)
    else:
      unknownArgumentExit()
  return parameters

def _deleteCalendarEvents(origUser, user, origCal, calIds, count, calendarEventEntity, parameters):
  def _callbackDeleteEvents(request_id, _, exception):
    ri = request_id.splitlines()
    if exception is None:
      entityActionPerformed([Ent.CALENDAR, ri[RI_ENTITY], Ent.EVENT, ri[RI_ITEM]], int(ri[RI_J]), int(ri[RI_JCOUNT]))
    else:
      http_status, reason, message = checkGAPIError(exception)
      errMsg = getHTTPError({}, http_status, reason, message)
      entityActionFailedWarning([Ent.CALENDAR, ri[RI_ENTITY], Ent.EVENT, ri[RI_ITEM]], errMsg, int(ri[RI_J]), int(ri[RI_JCOUNT]))

  i = 0
  for calId in calIds:
    i += 1
    calId, cal, calEventIds, jcount = _validateCalendarGetEventIDs(origUser, user, origCal, calId, i, count, calendarEventEntity, doIt=parameters['doIt'])
    if jcount == 0:
      continue
    Ind.Increment()
    if parameters['batch_size'] == 0:
      j = 0
      for eventId in calEventIds:
        j += 1
        try:
          callGAPI(cal.events(), 'delete',
                   throwReasons=GAPI.CALENDAR_THROW_REASONS+[GAPI.NOT_FOUND, GAPI.DELETED, GAPI.FORBIDDEN,
                                                             GAPI.INVALID, GAPI.REQUIRED, GAPI.REQUIRED_ACCESS_LEVEL],
                   calendarId=calId, eventId=eventId, sendUpdates=parameters['sendUpdates'])
          entityActionPerformed([Ent.CALENDAR, calId, Ent.EVENT, eventId], j, jcount)
        except (GAPI.notFound, GAPI.deleted) as e:
          if not checkCalendarExists(cal, calId, i, count):
            entityUnknownWarning(Ent.CALENDAR, calId, i, count)
            break
          entityActionFailedWarning([Ent.CALENDAR, calId, Ent.EVENT, eventId], str(e), j, jcount)
        except (GAPI.forbidden, GAPI.invalid, GAPI.required, GAPI.requiredAccessLevel) as e:
          entityActionFailedWarning([Ent.CALENDAR, calId, Ent.EVENT, eventId], str(e), j, jcount)
        except GAPI.notACalendarUser:
          userCalServiceNotEnabledWarning(calId, i, count)
          break
    else:
      svcargs = dict([('calendarId', calId), ('eventId', None), ('sendUpdates', parameters['sendUpdates'])]+GM.Globals[GM.EXTRA_ARGS_LIST])
      method = getattr(cal.events(), 'delete')
      dbatch = cal.new_batch_http_request(callback=_callbackDeleteEvents)
      bcount = 0
      j = 0
      for eventId in calEventIds:
        j += 1
        svcparms = svcargs.copy()
        svcparms['eventId'] = eventId
        dbatch.add(method(**svcparms), request_id=batchRequestID(calId, i, count, j, jcount, svcparms['eventId']))
        bcount += 1
        if bcount >= parameters['batch_size']:
          executeBatch(dbatch)
          dbatch = cal.new_batch_http_request(callback=_callbackDeleteEvents)
          bcount = 0
      if bcount > 0:
        dbatch.execute()
    Ind.Decrement()

# gam calendars <CalendarEntity> delete event <EventEntity>
#	[batchsize <Integer>] [doit] [<EventNotificationAttribute>]
def doCalendarsDeleteEvents(calIds):
  calendarEventEntity = getCalendarEventEntity()
  parameters = _getCalendarDeleteEventOptions()
  _deleteCalendarEvents(None, None, None, calIds, len(calIds), calendarEventEntity, parameters)

# gam calendar <CalendarEntity> deleteevent (id|eventid <EventID>)+
#	[batchsize <Integer>] [doit] [<EventNotificationAttribute>]
def doCalendarsDeleteEventsOld(calIds):
  calendarEventEntity = initCalendarEventEntity()
  parameters = _getCalendarDeleteEventOptions(calendarEventEntity)
  _deleteCalendarEvents(None, None, None, calIds, len(calIds), calendarEventEntity, parameters)

def _getCalendarMoveEventsOptions(calendarEventEntity=None):
  parameters = {'sendUpdates': 'none'}
  newCalId = None
  while Cmd.ArgumentsRemaining():
    myarg = getArgument()
    if _getCalendarSendUpdates(myarg, parameters):
      pass
    elif calendarEventEntity and myarg in {'id', 'eventid'}:
      calendarEventEntity['list'].append(getString(Cmd.OB_EVENT_ID))
    elif calendarEventEntity and myarg == 'destination':
      newCalId = convertUIDtoEmailAddress(getString(Cmd.OB_CALENDAR_ITEM))
    else:
      unknownArgumentExit()
  return (parameters, newCalId)

def _moveCalendarEvents(origUser, user, origCal, calIds, count, calendarEventEntity, newCalId, parameters):
  i = 0
  for calId in calIds:
    i += 1
    calId, cal, calEventIds, jcount = _validateCalendarGetEventIDs(origUser, user, origCal, calId, i, count, calendarEventEntity)
    if jcount == 0:
      continue
    kvList = [Ent.USER, user] if user else []
    kvList.extend([Ent.CALENDAR, calId])
    Ind.Increment()
    j = 0
    for eventId in calEventIds:
      j += 1
      kvListEvent = kvList+[Ent.EVENT, eventId]
      kvListEventNewCal = kvListEvent+[Ent.CALENDAR, newCalId]
      try:
        callGAPI(cal.events(), 'move',
                 throwReasons=GAPI.CALENDAR_THROW_REASONS+[GAPI.NOT_FOUND, GAPI.FORBIDDEN, GAPI.REQUIRED_ACCESS_LEVEL,
                                                           GAPI.INVALID, GAPI.BAD_REQUEST, GAPI.EVENT_TYPE_RESTRICTION,
                                                           GAPI.CANNOT_CHANGE_ORGANIZER, GAPI.CANNOT_CHANGE_ORGANIZER_OF_INSTANCE],
                 calendarId=calId, eventId=eventId, destination=newCalId, sendUpdates=parameters['sendUpdates'], fields='')
        entityModifierNewValueActionPerformed(kvListEvent, Act.MODIFIER_TO, f'{Ent.Singular(Ent.CALENDAR)}: {newCalId}', j, jcount)
      except GAPI.notFound as e:
        if not checkCalendarExists(cal, calId, i, count):
          entityUnknownWarning(Ent.CALENDAR, calId, i, count)
          break
        entityActionFailedWarning(kvListEventNewCal, Ent.TypeNameMessage(Ent.EVENT, eventId, str(e)), j, jcount)
      except GAPI.requiredAccessLevel:
# Correct "You need to have reader access to this calendar." to "Writer access required to both calendars."
        entityActionFailedWarning(kvListEventNewCal, Msg.WRITER_ACCESS_REQUIRED_TO_BOTH_CALENDARS, j, jcount)
      except (GAPI.forbidden, GAPI.invalid, GAPI.badRequest, GAPI.eventTypeRestriction,
              GAPI.cannotChangeOrganizer, GAPI.cannotChangeOrganizerOfInstance) as e:
        entityActionFailedWarning(kvListEventNewCal, str(e), j, jcount)
      except GAPI.notACalendarUser:
        userCalServiceNotEnabledWarning(calId, i, count)
        break
    Ind.Decrement()

# gam calendars <CalendarEntity> move events <EventEntity> to|destination <CalendarItem> [<EventNotificationAttribute>]
def doCalendarsMoveEvents(calIds):
  calendarEventEntity = getCalendarEventEntity()
  checkArgumentPresent(['to', 'destination'])
  newCalId = convertUIDtoEmailAddress(getString(Cmd.OB_CALENDAR_ITEM))
  parameters, _ = _getCalendarMoveEventsOptions()
  if not checkCalendarExists(None, newCalId, 0, 0, True):
    return
  _moveCalendarEvents(None, None, None, calIds, len(calIds), calendarEventEntity, newCalId, parameters)

# gam calendars <CalendarEntity> moveevent (id|eventid <EventID>)+ destination <CalendarItem> [<EventNotificationAttribute>]
def doCalendarsMoveEventsOld(calIds):
  calendarEventEntity = initCalendarEventEntity()
  parameters, newCalId = _getCalendarMoveEventsOptions(calendarEventEntity)
  if not checkCalendarExists(None, newCalId, 0, 0, True):
    return
  _moveCalendarEvents(None, None, None, calIds, len(calIds), calendarEventEntity, newCalId, parameters)

def _purgeCalendarEvents(origUser, user, origCal, calIds, count, calendarEventEntity, parameters, emptyTrash):
  body = {'summary': f'GamPurgeCalendar-{random.randint(1, 99999):05}'}
  if user:
    entityValueList = [Ent.USER, user, Ent.CALENDAR, body['summary']]
  else:
    entityValueList = [Ent.CALENDAR, body['summary']]
  i = 0
  for calId in calIds:
    i += 1
    calId, cal = getNormalizedCalIdCal(origCal, calId, user, i, count)
    if not cal:
      continue
    try:
      purgeCalId = callGAPI(cal.calendars(), 'insert',
                            throwReasons=GAPI.CALENDAR_THROW_REASONS+[GAPI.FORBIDDEN],
                            body=body, fields='id')['id']
      Act.Set(Act.CREATE)
      entityActionPerformed(entityValueList)
      Ind.Increment()
      if not emptyTrash:
        Act.Set(Act.DELETE)
        _deleteCalendarEvents(origUser, user, cal, [calId], count, calendarEventEntity, parameters)
      Act.Set(Act.MOVE)
      calendarEventEntity['kwargs']['showDeleted'] = True
      _moveCalendarEvents(origUser, user, cal, [calId], count, calendarEventEntity, purgeCalId, parameters)
      calendarEventEntity['kwargs'].pop('showDeleted')
      Ind.Decrement()
      callGAPI(cal.calendars(), 'delete',
               throwReasons=GAPI.CALENDAR_THROW_REASONS+[GAPI.NOT_FOUND, GAPI.FORBIDDEN],
               calendarId=purgeCalId)
      Act.Set(Act.REMOVE)
      entityActionPerformed(entityValueList)
    except (GAPI.notFound, GAPI.forbidden) as e:
      entityActionFailedWarning([Ent.USER, user, Ent.CALENDAR, body['summary']], str(e))
    except GAPI.notACalendarUser:
      userCalServiceNotEnabledWarning(calId, i, count)

# gam calendars <CalendarEntity> purge event <EventEntity>
#	[batchsize <Integer>] [doit] [<EventNotificationAttribute>]
def doCalendarsPurgeEvents(calIds):
  calendarEventEntity = getCalendarEventEntity()
  parameters = _getCalendarDeleteEventOptions()
  _purgeCalendarEvents(None, None, None, calIds, len(calIds), calendarEventEntity, parameters, False)

def _wipeCalendarEvents(user, origCal, calIds, count):
  i = 0
  for calId in calIds:
    i += 1
    calId, cal = getNormalizedCalIdCal(origCal, calId, user, i, count)
    if not cal:
      continue
    try:
      callGAPI(cal.calendars(), 'clear',
               throwReasons=GAPI.CALENDAR_THROW_REASONS+[GAPI.NOT_FOUND, GAPI.FORBIDDEN, GAPI.INVALID,
                                                         GAPI.REQUIRED_ACCESS_LEVEL, GAPI.SERVICE_NOT_AVAILABLE],
               retryReasons=GAPI.SERVICE_NOT_AVAILABLE_RETRY_REASONS,
               calendarId=calId)
      entityActionPerformed([Ent.CALENDAR, calId], i, count)
    except (GAPI.notFound, GAPI.forbidden, GAPI.invalid, GAPI.requiredAccessLevel, GAPI.serviceNotAvailable) as e:
      entityActionFailedWarning([Ent.CALENDAR, calId], str(e), i, count)
    except GAPI.notACalendarUser:
      userCalServiceNotEnabledWarning(calId, i, count)

# gam calendars <CalendarEntity> wipe events
# gam calendar <CalendarEntity> wipe
def doCalendarsWipeEvents(calIds):
  checkArgumentPresent([Cmd.ARG_EVENT, Cmd.ARG_EVENTS])
  checkForExtraneousArguments()
  _wipeCalendarEvents(None, None, calIds, len(calIds))

def _emptyCalendarTrash(user, origCal, calIds, count):
  i = 0
  for calId in calIds:
    i += 1
    calId, cal = getNormalizedCalIdCal(origCal, calId, user, i, count)
    if not cal:
      continue
    Act.Set(Act.PURGE)
    calendarEventEntity = initCalendarEventEntity()
    try:
      events = callGAPIpages(cal.events(), 'list', 'items',
                             throwReasons=GAPI.CALENDAR_THROW_REASONS+[GAPI.NOT_FOUND, GAPI.FORBIDDEN],
                             calendarId=calId, showDeleted=True, fields='nextPageToken,items(id,status,organizer(self),recurringEventId)',
                             maxResults=GC.Values[GC.EVENT_MAX_RESULTS])
    except (GAPI.notFound, GAPI.forbidden) as e:
      entityActionFailedWarning([Ent.CALENDAR, calId], str(e), i, count)
      continue
    except GAPI.notACalendarUser:
      userCalServiceNotEnabledWarning(calId, i, count)
      continue
    for event in events:
      if event['status'] == 'cancelled' and event.get('organizer', {}).get('self', user is None) and not event.get('recurringEventId', ''):
        calendarEventEntity['list'].append(event['id'])
    jcount = len(calendarEventEntity['list'])
    if not user:
      entityPerformActionNumItems([Ent.CALENDAR, calId], jcount, Ent.TRASHED_EVENT, i, count)
      Ind.Increment()
    if jcount > 0:
      _purgeCalendarEvents(user, user, cal, [calId], 1, calendarEventEntity, {'sendUpdates': 'none', 'doIt': True, 'batch_size': 0}, True)
    if not user:
      Ind.Decrement()

# gam calendars <CalendarEntity> empty calendartrash
def doCalendarsEmptyTrash(calIds):
  checkForExtraneousArguments()
  Act.Set(Act.PURGE)
  _emptyCalendarTrash(None, None, calIds, len(calIds))

EVENT_SHOW_ORDER = ['id', 'summary', 'status', 'description', 'location',
                    'start', 'end', 'endTimeUnspecified',
                    'creator', 'organizer', 'created', 'updated', 'iCalUID']
EVENT_PRINT_ORDER = ['id', 'summary', 'status', 'description', 'location',
                     'created', 'updated', 'iCalUID']

EVENT_TIME_OBJECTS = {'created', 'updated'}

def _showCalendarEvent(primaryEmail, calId, eventEntityType, event, k, kcount, FJQC):
  if FJQC.formatJSON:
    if primaryEmail:
      printLine(json.dumps(cleanJSON({'primaryEmail': primaryEmail, 'calendarId': calId, 'event': event},
                                     timeObjects=EVENT_TIME_OBJECTS), ensure_ascii=False, sort_keys=True))
    else:
      printLine(json.dumps(cleanJSON({'calendarId': calId, 'event': event},
                                     timeObjects=EVENT_TIME_OBJECTS), ensure_ascii=False, sort_keys=True))
    return
  printEntity([eventEntityType, event['id']], k, kcount)
  skipObjects = {'id'}
  Ind.Increment()
  for field in EVENT_SHOW_ORDER:
    if field in event:
      if field != 'description':
        showJSON(field, event[field], skipObjects, EVENT_TIME_OBJECTS)
      else:
        printKeyValueWithCRsNLs(field, event[field])
      skipObjects.add(field)
  showJSON(None, event, skipObjects)
  Ind.Decrement()

def _printCalendarEvent(user, calId, event, csvPF, FJQC, addCSVData, attendeesList=False):
  row = {'calendarId': calId, 'id': event['id']}
  if user:
    row['primaryEmail'] = user
  if addCSVData:
    row.update(addCSVData)
  if attendeesList:
    attendees = event.pop('attendees', [])
    row['attendeesList'] = GC.Values[GC.CSV_OUTPUT_FIELD_DELIMITER].join([attendee['email'] for attendee in attendees])
  flattenJSON(event, flattened=row, timeObjects=EVENT_TIME_OBJECTS)
  if not FJQC.formatJSON:
    csvPF.WriteRowTitles(row)
  elif csvPF.CheckRowTitles(row):
    row = {'calendarId': calId, 'id': event['id'],
           'JSON': json.dumps(cleanJSON(event, timeObjects=EVENT_TIME_OBJECTS),
                              ensure_ascii=False, sort_keys=False)}
    if user:
      row['primaryEmail'] = user
    csvPF.WriteRowNoFilter(row)

def _printShowCalendarEvents(origUser, user, origCal, calIds, count, calendarEventEntity,
                             csvPF, FJQC, fieldsList, addCSVData, attendeesList):
  i = 0
  for calId in calIds:
    i += 1
    if csvPF:
      printGettingEntityItemForWhom(Ent.EVENT, calId, i, count)
    calId, _, events, jcount = _validateCalendarGetEvents(origUser, user, origCal, calId, i, count, calendarEventEntity,
                                                          fieldsList, not csvPF and not FJQC.formatJSON and not calendarEventEntity['countsOnly'])
    if not csvPF:
      if not calendarEventEntity['countsOnly']:
        Ind.Increment()
        j = 0
        for event in events:
          j += 1
          if calendarEventEntity['showDayOfWeek']:
            _getEventDaysOfWeek(event)
          _showCalendarEvent(user, calId, Ent.EVENT, event, j, jcount, FJQC)
        Ind.Decrement()
      else:
        printKeyValueList([Ent.Singular(Ent.CALENDAR), calId, Ent.Choose(Ent.EVENT, jcount), jcount])
    else:
      if not calendarEventEntity['countsOnly']:
        if events:
          for event in events:
            if calendarEventEntity['showDayOfWeek']:
              _getEventDaysOfWeek(event)
            _printCalendarEvent(user, calId, event, csvPF, FJQC, addCSVData, attendeesList)
        elif GC.Values[GC.CSV_OUTPUT_USERS_AUDIT] and user:
          csvPF.WriteRowNoFilter({'calendarId': calId, 'primaryEmail': user, 'id': ''})
      else:
        if calendarEventEntity['eventRowFilter']:
          jcount = 0
          for event in events:
            if calendarEventEntity['showDayOfWeek']:
              _getEventDaysOfWeek(event)
            row = {'calendarId': calId, 'id': event['id']}
            if user:
              row['primaryEmail'] = user
            flattenJSON(event, flattened=row, timeObjects=EVENT_TIME_OBJECTS)
            if csvPF.CheckRowTitles(row):
              jcount += 1
        row = {'calendarId': calId}
        if user:
          row['primaryEmail'] = user
        if addCSVData:
          row.update(addCSVData)
        row['events'] = jcount
        if not calendarEventEntity['eventRowFilter']:
          csvPF.WriteRow(row)
        else:
          csvPF.WriteRowNoFilter(row)

EVENT_FIELDS_CHOICE_MAP = {
  'anyonecanaddself': 'anyoneCanAddSelf',
  'attachments': 'attachments',
  'attendees': 'attendees',
  'attendeesomitted': 'attendeesOmitted',
  'colorid': 'colorId',
  'conferencedata': 'conferenceData',
  'created': 'created',
  'creator': 'creator',
  'description': 'description',
  'end': 'end',
  'endtime': 'end',
  'endtimeunspecified': 'endTimeUnspecified',
  'extendedproperties': 'extendedProperties',
  'focustimeproperties': 'focusTimeProperties',
  'gadget': 'gadget',
  'guestscaninviteothers': 'guestsCanInviteOthers',
  'guestscanmodify': 'guestsCanModify',
  'guestscanseeotherguests': 'guestsCanSeeOtherGuests',
  'hangoutlink': 'hangoutLink',
  'htmllink': 'htmlLink',
  'eventtype': 'eventType',
  'icaluid': 'iCalUID',
  'id': 'id',
  'location': 'location',
  'locked': 'locked',
  'organizer': 'organizer',
  'organiser': 'organizer',
  'originalstart': 'originalStartTime',
  'originalstarttime': 'originalStartTime',
  'outofofficeproperties': 'outOfOfficeProperties',
  'privatecopy': 'privateCopy',
  'recurrence': 'recurrence',
  'recurringeventid': 'recurringEventId',
  'reminders': 'reminders',
  'sequence': 'sequence',
  'source': 'source',
  'start': 'start',
  'starttime': 'start',
  'status': 'status',
  'summary': 'summary',
  'transparency': 'transparency',
  'updated': 'updated',
  'visibility': 'visibility',
  'workinglocationproperties': 'workingLocationProperties',
  }

EVENT_ATTACHMENTS_SUBFIELDS_CHOICE_MAP = {
  'fileid': 'fileId',
  'fileurl': 'fileUrl',
  'iconlink': 'iconLink',
  'mimetype': 'mimeType',
  'title': 'title',
  }

EVENT_ATTENDEES_SUBFIELDS_CHOICE_MAP = {
  'additionalguests': 'additionalGuests',
  'comment': 'comment',
  'displayname': 'displayName',
  'email': 'email',
  'id': 'id',
  'optional': 'optional',
  'organizer': 'organizer',
  'organiser': 'organizer',
  'resource': 'resource',
  'responsestatus': 'responseStatus',
  'self': 'self',
  }

EVENT_CONFERENCEDATA_SUBFIELDS_CHOICE_MAP = {
  'conferenceid': 'conferenceId',
  'conferencesolution': 'conferenceSolution',
  'createrequest': 'createRequest',
  'entrypoints': 'entryPoints',
  'notes': 'notes',
  'signature': 'signature',
  }

EVENT_CREATOR_SUBFIELDS_CHOICE_MAP = {
  'displayname': 'displayName',
  'email': 'email',
  'id': 'id',
  'self': 'self',
  }

EVENT_FOCUSTIME_SUBFIELDS_CHOICE_MAP = {
  'autodeclinemode': 'autoDeclineMode',
  'chatstatus': 'chatStatus',
  'declinemessage': 'declineMessage',
  }

EVENT_ORGANIZER_SUBFIELDS_CHOICE_MAP = {
  'displayname': 'displayName',
  'email': 'email',
  'id': 'id',
  'self': 'self',
  }

EVENT_OUTOFOFFICE_SUBFIELDS_CHOICE_MAP = {
  'autodeclinemode': 'autoDeclineMode',
  'declinemessage': 'declineMessage',
  }

EVENT_WORKINGLOCATION_SUBFIELDS_CHOICE_MAP = {
  'homeoffice': 'homeOffice',
  'customlocation': 'customLocation',
  'officelocation': 'officeLocation',
  }

EVENT_SUBFIELDS_CHOICE_MAP = {
  'attachments': EVENT_ATTACHMENTS_SUBFIELDS_CHOICE_MAP,
  'attendees': EVENT_ATTENDEES_SUBFIELDS_CHOICE_MAP,
  'conferencedata': EVENT_CONFERENCEDATA_SUBFIELDS_CHOICE_MAP,
  'creator': EVENT_CREATOR_SUBFIELDS_CHOICE_MAP,
  'focustimeproperties': EVENT_FOCUSTIME_SUBFIELDS_CHOICE_MAP,
  'organizer': EVENT_ORGANIZER_SUBFIELDS_CHOICE_MAP,
  'organiser': EVENT_ORGANIZER_SUBFIELDS_CHOICE_MAP,
  'outofofficeproperties': EVENT_OUTOFOFFICE_SUBFIELDS_CHOICE_MAP,
  'workinglocationproperties': EVENT_WORKINGLOCATION_SUBFIELDS_CHOICE_MAP,
}

def _getEventFields(fieldsList):
  if not fieldsList:
    fieldsList.append('id')
  for field in _getFieldsList():
    if field.find('.') == -1:
      if field in EVENT_FIELDS_CHOICE_MAP:
        addFieldToFieldsList(field, EVENT_FIELDS_CHOICE_MAP, fieldsList)
      else:
        invalidChoiceExit(field, EVENT_FIELDS_CHOICE_MAP, True)
    else:
      field, subField = field.split('.', 1)
      if field in EVENT_SUBFIELDS_CHOICE_MAP:
        if subField in EVENT_SUBFIELDS_CHOICE_MAP[field]:
          fieldsList.append(f'{EVENT_FIELDS_CHOICE_MAP[field]}.{EVENT_SUBFIELDS_CHOICE_MAP[field][subField]}')
        else:
          invalidChoiceExit(subField, list(EVENT_SUBFIELDS_CHOICE_MAP[field]), True)
      else:
        invalidChoiceExit(field, list(EVENT_SUBFIELDS_CHOICE_MAP), True)

def _addEventEntitySelectFields(calendarEventEntity, fieldsList):
  if fieldsList:
    _getEventMatchFields(calendarEventEntity, fieldsList)
    if calendarEventEntity['maxinstances'] != -1:
      fieldsList.append('recurrence')

def _getCalendarInfoEventOptions(calendarEventEntity):
  FJQC = FormatJSONQuoteChar()
  fieldsList = []
  while Cmd.ArgumentsRemaining():
    myarg = getArgument()
    if myarg == 'fields':
      _getEventFields(fieldsList)
    elif myarg == 'showdayofweek':
      calendarEventEntity['showDayOfWeek'] = True
    else:
      FJQC.GetFormatJSON(myarg)
  _addEventEntitySelectFields(calendarEventEntity, fieldsList)
  return (FJQC, fieldsList)

def _infoCalendarEvents(origUser, user, origCal, calIds, count, calendarEventEntity, FJQC, fieldsList):
  fields = getFieldsFromFieldsList(fieldsList)
  ifields = getItemFieldsFromFieldsList('items', fieldsList)
  i = 0
  for calId in calIds:
    i += 1
    calId, cal, calEventIds, jcount = _validateCalendarGetEventIDs(origUser, user, origCal, calId, i, count, calendarEventEntity, showAction=not FJQC.formatJSON)
    if jcount == 0:
      continue
    Ind.Increment()
    j = 0
    for eventId in calEventIds:
      j += 1
      try:
        event = callGAPI(cal.events(), 'get',
                         throwReasons=GAPI.CALENDAR_THROW_REASONS+[GAPI.NOT_FOUND, GAPI.DELETED, GAPI.FORBIDDEN],
                         calendarId=calId, eventId=eventId, fields=fields)
        if calendarEventEntity['maxinstances'] == -1 or 'recurrence' not in event:
          if calendarEventEntity['showDayOfWeek']:
            _getEventDaysOfWeek(event)
          _showCalendarEvent(user, calId, Ent.EVENT, event, j, jcount, FJQC)
        else:
          instances = callGAPIpages(cal.events(), 'instances', 'items',
                                    throwReasons=GAPI.CALENDAR_THROW_REASONS+[GAPI.NOT_FOUND, GAPI.DELETED, GAPI.FORBIDDEN],
                                    calendarId=calId, eventId=eventId, fields=ifields,
                                    maxItems=calendarEventEntity['maxinstances'], maxResults=GC.Values[GC.EVENT_MAX_RESULTS])
          lcount = len(instances)
          if not FJQC.formatJSON:
            entityPerformActionNumItems([Ent.EVENT, event['id']], lcount, Ent.INSTANCE, j, jcount)
          Ind.Increment()
          l = 0
          for instance in instances:
            l += 1
            if calendarEventEntity['showDayOfWeek']:
              _getEventDaysOfWeek(instance)
            _showCalendarEvent(user, calId, Ent.INSTANCE, instance, l, lcount, FJQC)
          Ind.Decrement()
      except (GAPI.notFound, GAPI.deleted) as e:
        if not checkCalendarExists(cal, calId, i, count):
          entityUnknownWarning(Ent.CALENDAR, calId, i, count)
          break
        entityActionFailedWarning([Ent.CALENDAR, calId, Ent.EVENT, eventId], str(e), j, jcount)
      except (GAPI.forbidden) as e:
        entityActionFailedWarning([Ent.CALENDAR, calId], str(e), i, count)
        break
      except GAPI.notACalendarUser:
        userCalServiceNotEnabledWarning(calId, i, count)
        break
    Ind.Decrement()

# gam calendars <CalendarEntity> info events <EventEntity> [maxinstances <Number>]
#	[fields <EventFieldNameList>] [showdayofweek]
#	[formatjson]
def doCalendarsInfoEvents(calIds):
  calendarEventEntity = getCalendarEventEntity()
  FJQC, fieldsList = _getCalendarInfoEventOptions(calendarEventEntity)
  _infoCalendarEvents(None, None, None, calIds, len(calIds), calendarEventEntity, FJQC, fieldsList)

EVENT_INDEXED_TITLES = ['attendees', 'attachments', 'recurrence']

def _getCalendarPrintShowEventOptions(calendarEventEntity, entityType):
  csvPF = CSVPrintFile(['primaryEmail', 'calendarId', 'id'] if entityType == Ent.USER else ['calendarId', 'id'], 'sortall', indexedTitles=EVENT_INDEXED_TITLES) if Act.csvFormat() else None
  FJQC = FormatJSONQuoteChar(csvPF)
  fieldsList = []
  addCSVData = {}
  addCSVDataLoc = 2 if entityType == Ent.USER else 1
  attendeesList = False
  while Cmd.ArgumentsRemaining():
    myarg = getArgument()
    if csvPF and myarg == 'todrive':
      csvPF.GetTodriveParameters()
    elif _getCalendarListEventsDisplayProperty(myarg, calendarEventEntity):
      pass
    elif myarg == 'fields':
      _getEventFields(fieldsList)
    elif csvPF and myarg == 'addcsvdata':
      getAddCSVData(addCSVData)
    elif myarg == 'countsonly':
      calendarEventEntity['countsOnly'] = True
    elif myarg == 'showdayofweek':
      calendarEventEntity['showDayOfWeek'] = True
    elif myarg == 'eventrowfilter':
      calendarEventEntity['eventRowFilter'] = True
    elif myarg == 'attendeeslist':
      attendeesList = True
    else:
      FJQC.GetFormatJSONQuoteChar(myarg, True)
  if calendarEventEntity['countsOnly'] and not calendarEventEntity['eventRowFilter']:
    fieldsList = ['id']
  if csvPF:
    if calendarEventEntity['countsOnly']:
      csvPF.SetFormatJSON(False)
      csvPF.RemoveTitles(['id'])
      if addCSVData:
        csvPF.InsertTitles(addCSVDataLoc, sorted(addCSVData.keys()))
      csvPF.AddTitles(['events'])
      csvPF.SetSortAllTitles()
      calendarEventEntity['countsOnlyTitles'] = csvPF.titlesList[:]
    else:
      if addCSVData:
        csvPF.InsertTitles(addCSVDataLoc, sorted(addCSVData.keys()))
      if not FJQC.formatJSON and not fieldsList:
        csvPF.AddTitles(EVENT_PRINT_ORDER)
      csvPF.SetSortAllTitles()
  _addEventEntitySelectFields(calendarEventEntity, fieldsList)
  return (csvPF, FJQC, fieldsList, addCSVData, attendeesList)

# gam calendars <CalendarEntity> print events <EventEntity> <EventDisplayProperties>*
#	[fields <EventFieldNameList>] [showdayofweek]
#	(addcsvdata <FieldName> <String>)*
#	[eventrowfilter]
#	[countsonly|(formatjson [quotechar <Character>])] [todrive <ToDriveAttribute>*]
# gam calendars <CalendarEntity> show events <EventEntity> <EventDisplayProperties>*
#	[fields <EventFieldNameList>] [showdayofweek]
#	[countsonly|formatjson]
def doCalendarsPrintShowEvents(calIds):
  calendarEventEntity = getCalendarEventEntity()
  csvPF, FJQC, fieldsList, addCSVData, attendeesList = _getCalendarPrintShowEventOptions(calendarEventEntity, Ent.CALENDAR)
  _printShowCalendarEvents(None, None, None, calIds, len(calIds), calendarEventEntity,
                           csvPF, FJQC, fieldsList, addCSVData, attendeesList)
  if csvPF:
    if calendarEventEntity['countsOnly'] and calendarEventEntity['eventRowFilter']:
      csvPF.SetTitles(calendarEventEntity['countsOnlyTitles'])
      csvPF.writeCSVfile('Calendar Events', True)
    else:
      csvPF.writeCSVfile('Calendar Events')

# <CalendarSettings> ::==
#	[description <String>] [location <String>] [summary <String>] [timezone <TimeZone>]
#	[autoacceptinvitations [<Boolean>]]

def _getEventTypes():
  typesList = []
  for field in _getFieldsList():
    if field in EVENT_TYPES_CHOICE_MAP:
      addFieldToFieldsList(field, EVENT_TYPES_CHOICE_MAP, typesList)
    else:
      invalidChoiceExit(field, EVENT_TYPES_CHOICE_MAP, True)
#  return ','.join(typesList)
  return typesList

LIST_EVENTS_DISPLAY_PROPERTIES = {
  'alwaysincludeemail': ('alwaysIncludeEmail', {GC.VAR_TYPE: GC.TYPE_BOOLEAN}),
  'icaluid': ('iCalUID', {GC.VAR_TYPE: GC.TYPE_STRING}),
  'maxattendees': ('maxAttendees', {GC.VAR_TYPE: GC.TYPE_INTEGER, GC.VAR_LIMITS: (1, None)}),
  'orderby': ('orderBy', {GC.VAR_TYPE: GC.TYPE_CHOICE, 'choices': {'starttime': 'startTime', 'updated': 'updated'}}),
  'timezone': ('timeZone', {GC.VAR_TYPE: GC.TYPE_STRING}),
  }

LIST_EVENTS_SELECT_PROPERTIES = {
  'after': ('timeMin', {GC.VAR_TYPE: GC.TYPE_DATETIME}),
  'before': ('timeMax', {GC.VAR_TYPE: GC.TYPE_DATETIME}),
  'endtime': ('timeMax', {GC.VAR_TYPE: GC.TYPE_DATETIME}),
  'includedeleted': ('showDeleted', {GC.VAR_TYPE: GC.TYPE_BOOLEAN}),
  'includehidden': ('showHiddenInvitations', {GC.VAR_TYPE: GC.TYPE_BOOLEAN}),
  'privateextendedproperty': ('privateExtendedProperty', {GC.VAR_TYPE: GC.TYPE_STRING}),
  'sharedextendedproperty': ('sharedExtendedProperty', {GC.VAR_TYPE: GC.TYPE_STRING}),
  'showdeletedevents': ('showDeleted', {GC.VAR_TYPE: GC.TYPE_BOOLEAN}),
  'showhiddeninvitations': ('showHiddenInvitations', {GC.VAR_TYPE: GC.TYPE_BOOLEAN}),
  'singleevents': ('singleEvents', {GC.VAR_TYPE: GC.TYPE_BOOLEAN}),
  'starttime': ('timeMin', {GC.VAR_TYPE: GC.TYPE_DATETIME}),
  'timemax': ('timeMax', {GC.VAR_TYPE: GC.TYPE_DATETIME}),
  'timemin': ('timeMin', {GC.VAR_TYPE: GC.TYPE_DATETIME}),
  'updated': ('updatedMin', {GC.VAR_TYPE: GC.TYPE_DATETIME}),
  'updatedmin': ('updatedMin', {GC.VAR_TYPE: GC.TYPE_DATETIME}),
  'eventtype': ('eventTypes', {GC.VAR_TYPE: GC.TYPE_CHOICE_LIST}),
  'eventtypes': ('eventTypes', {GC.VAR_TYPE: GC.TYPE_CHOICE_LIST}),
  }

LIST_EVENTS_MATCH_FIELDS = {
  'attendees': ['attendees', 'email'],
  'attendeesorganizer': ['attendees', 'organizer'],
  'attendeesorganiser': ['attendees', 'organizer'],
  'attendeesonlydomainlist': ['attendees', 'onlydomainlist'],
  'attendeesdomainlist': ['attendees', 'domainlist'],
  'attendeesnotdomainlist': ['attendees', 'notdomainlist'],
  'attendeespattern': ['attendees', 'match'],
  'attendeesstatus': ['attendees', 'status'],
  'description': ['description'],
  'hangoutlink': ['hangoutLink'],
  'location': ['location'],
  'summary': ['summary'],
  'creatorname': ['creator', 'displayName'],
  'creatoremail': ['creator', 'email'],
  'organizername': ['organizer', 'displayName'],
  'organizeremail': ['organizer', 'email'],
  'organizerself': ['organizer', 'self'],
  'organisername': ['organizer', 'displayName'],
  'organiseremail': ['organizer', 'email'],
  'organiserself': ['organizer', 'self'],
  'status': ['status'],
  'transparency': ['transparency'],
  'visibility': ['visibility'],
  }

def _getCalendarListEventsProperty(myarg, attributes, kwargs):
  attrName, attribute = attributes.get(myarg, (None, None))
  if not attrName:
    return False
  attrType = attribute[GC.VAR_TYPE]
  if attrType == GC.TYPE_BOOLEAN:
    kwargs[attrName] = True
  elif attrType == GC.TYPE_STRING:
    kwargs[attrName] = getString(Cmd.OB_STRING)
  elif attrType == GC.TYPE_CHOICE:
    kwargs[attrName] = getChoice(attribute['choices'], mapChoice=True)
  elif attrType == GC.TYPE_DATETIME:
    kwargs[attrName] = getTimeOrDeltaFromNow()
  elif attrType ==  GC.TYPE_INTEGER:
    minVal, maxVal = attribute[GC.VAR_LIMITS]
    kwargs[attrName] = getInteger(minVal=minVal, maxVal=maxVal)
  else: # elif attrType == GC.TYPE_CHOICE_LIST:
    if attrName == 'eventTypes':
      kwargs[attrName] = _getEventTypes()
  return True

def _getCalendarListEventsDisplayProperty(myarg, calendarEventEntity):
  return _getCalendarListEventsProperty(myarg, LIST_EVENTS_DISPLAY_PROPERTIES, calendarEventEntity['kwargs'])

def initCalendarEventEntity():
  return {'list': [], 'queries': [], 'kwargs': {}, 'dict': None,
          'matches': [], 'maxinstances': -1, 'showDayOfWeek': False,
          'countsOnly': False, 'eventRowFilter': False, 'countsOnlyTitles': []}

def _getCalendarEventAttribute(myarg, body, parameters, function):
  from gam.cmd.calendar.resources import _validateResourceId  # deferred: circular
  def clearJSONfields(body, clearFields):
    for field in clearFields:
      body.pop(field, None)

  def clearJSONsubfields(body, clearFields):
    for field, subfields in clearFields.items():
      if field in body:
        if isinstance(body[field], list):
          for item in body[field]:
            for subfield in subfields:
              item.pop(subfield, None)
        else:
          for subfield in subfields:
            body.pop(subfield, None)

  cd = None
  if function == 'insert' and myarg in {'id', 'eventid'}:
    body['id'] = getEventID()
  elif function == 'import' and myarg == 'icaluid':
    body['iCalUID'] = getString(Cmd.OB_ICALUID)
  elif myarg == 'description':
    body['description'] = getStringWithCRsNLs()
  elif function == 'update' and myarg == 'replacedescription':
    parameters['replaceDescription'].append(getREPatternSubstitution(re.IGNORECASE))
  elif myarg == 'location':
    body['location'] = getString(Cmd.OB_STRING, minLen=0)
  elif myarg == 'source':
    body['source'] = {'title': getString(Cmd.OB_STRING), 'url': getString(Cmd.OB_URL)}
  elif myarg == 'summary':
    body['summary'] = getString(Cmd.OB_STRING, minLen=0)
  elif myarg in  {'start', 'starttime'}:
    body['start'] = getEventTime()
  elif myarg in {'originalstart', 'originalstarttime'}:
    body['originalStart'] = getEventTime()
  elif myarg in {'end', 'endtime'}:
    body['end'] = getEventTime()
  elif myarg == 'allday':
    body['start'] = body['end'] = {'date': getYYYYMMDD()}
  elif myarg == 'range':
    body['start'] = {'date': getYYYYMMDD()}
    body['end'] = {'date': getYYYYMMDD()}
  elif myarg == 'timerange':
    body['start'] = {'dateTime': getTimeOrDeltaFromNow()}
    body['end'] = {'dateTime': getTimeOrDeltaFromNow()}
  elif myarg == 'birthday':
    body['eventType'] = EVENT_TYPE_BIRTHDAY
    body['visibility'] = 'private'
    body['transparency'] = 'transparent'
    bday = getYYYYMMDD(returnDateTime=True)
    body['start'] = body['end'] = {'date': bday.strftime(YYYYMMDD_FORMAT)}
    if bday.month != 2 or bday.day != 29:
      body['recurrence'] = ['RRULE:FREQ=YEARLY']
    else:
      body['recurrence'] = ['RRULE:FREQ=YEARLY;BYMONTH=2;BYMONTHDAY=-1']
  elif myarg == 'attachment':
    body.setdefault('attachments', [])
    body['attachments'].append({'title': getString(Cmd.OB_STRING), 'fileUrl': getString(Cmd.OB_URL)})
  elif function == 'update' and myarg == 'clearattachments':
    body['attachments'] = []
  elif myarg in {'hangoutsmeet', 'googlemeet'}:
    body['conferenceData'] = {'createRequest': {'conferenceSolutionKey': {'type': 'hangoutsMeet'}, 'requestId': f'{str(uuid.uuid4())}'}}
  elif myarg == 'conferencedata':
    checkArgumentPresent(['meet'], True)
    epLabel = getString(Cmd.OB_MEET_ID)
    if not GOOGLE_MEETID_PATTERN.match(epLabel):
      invalidArgumentExit(GOOGLE_MEETID_FORMAT_REQUIRED)
    body['conferenceData'] = {"conferenceId": epLabel,
	                      "conferenceSolution": {"key": {"type": "hangoutsMeet"}},
	                      "entryPoints": [{"entryPointType": "video", "label": f'meet.google.com/{epLabel}',
                                               "uri": f'https://meet.google.com/{epLabel}'}]}
  elif function == 'update' and myarg in {'clearhangoutsmeet', 'cleargooglemeet'}:
    body['conferenceData'] = None
  elif myarg == 'recurrence':
    body.setdefault('recurrence', [])
    body['recurrence'].append(getString(Cmd.OB_RECURRENCE))
  elif myarg == 'timezone':
    parameters['timeZone'] = getString(Cmd.OB_STRING)
  elif function == 'update' and myarg == 'replacemode':
    parameters['replaceMode'] = True
  elif function == 'update' and myarg == 'clearattendees':
    parameters['clearAttendees'] = True
  elif function == 'update' and myarg == 'removeattendee':
    parameters['removeAttendees'].add(getEmailAddress(noUid=True))
  elif function == 'update' and myarg == 'selectremoveattendees':
    _, attendeeList = getEntityToModify(defaultEntityType=Cmd.ENTITY_USERS)
    for attendee in attendeeList:
      parameters['removeAttendees'].add(normalizeEmailAddressOrUID(attendee, noUid=True))
  elif myarg == 'attendee':
    parameters['attendees'].append({'email': getEmailAddress(noUid=True)})
  elif myarg == 'optionalattendee':
    parameters['attendees'].append({'email': getEmailAddress(noUid=True), 'optional': True})
  elif myarg in {'attendeestatus', 'selectattendees'}:
    optional = getChoice(CALENDAR_ATTENDEE_OPTIONAL_CHOICE_MAP, defaultChoice=None, mapChoice=True)
    responseStatus = getChoice(CALENDAR_ATTENDEE_STATUS_CHOICE_MAP, defaultChoice=None, mapChoice=True)
    if myarg == 'attendeestatus':
      attendeeList = [getEmailAddress(noUid=True)]
    else:
      _, attendeeList = getEntityToModify(defaultEntityType=Cmd.ENTITY_USERS)
    for attendee in attendeeList:
      addAttendee = {'email': normalizeEmailAddressOrUID(attendee, noUid=True)}
      if optional is not None:
        addAttendee['optional'] = optional
      if responseStatus is not None:
        addAttendee['responseStatus'] = responseStatus
      parameters['attendees'].append(addAttendee)
  elif function == 'update' and myarg == 'clearresources':
    parameters['clearResources'] = True
  elif myarg == 'resource':
    if cd is None:
      cd = buildGAPIObject(API.DIRECTORY)
    parameters['attendees'].append({'email': _validateResourceId(cd, getString(Cmd.OB_RESOURCE_ID), 0, 0, True),
                                    'responseStatus': 'accepted', 'resource': True})
  elif myarg == 'removeresource':
    if cd is None:
      cd = buildGAPIObject(API.DIRECTORY)
    parameters['removeAttendees'].add(_validateResourceId(cd, getString(Cmd.OB_RESOURCE_ID), 0, 0, True))
  elif myarg == 'json':
    jsonData = getJSON(EVENT_JSON_CLEAR_FIELDS)
    if function == 'insert':
      body.update(jsonData)
      clearJSONfields(body, EVENT_JSON_INSERT_CLEAR_FIELDS)
    elif function == 'import':
      if 'id' in jsonData:
        jsonData['iCalUID'] = jsonData.pop('id')
      body.update(jsonData)
    elif function == 'update':
      if 'event' in jsonData and 'attendees' in jsonData['event']:
        parameters['attendees'].extend(jsonData['event'].pop('attendees'))
        clearJSONsubfields(parameters, EVENT_JSONATTENDEES_SUBFIELD_CLEAR_FIELDS)
      body.update(jsonData)
      clearJSONfields(body, EVENT_JSON_UPDATE_CLEAR_FIELDS)
    clearJSONsubfields(body, EVENT_JSON_SUBFIELD_CLEAR_FIELDS)
    if ('conferenceData' in body and body['conferenceData'] and
        'createRequest' in body['conferenceData'] and
        'status' in body['conferenceData']['createRequest']):
      body['conferenceData']['createRequest']['status'].pop('statusCode', None)
  elif myarg == 'jsonattendees':
    jsonData = getJSON([])
    if 'event' in jsonData and 'attendees' in jsonData['event']:
      parameters['attendees'].extend(jsonData['event']['attendees'])
    elif 'attendees' in jsonData:
      parameters['attendees'].extend(jsonData['attendees'])
    clearJSONsubfields(parameters, EVENT_JSONATTENDEES_SUBFIELD_CLEAR_FIELDS)
  elif function != 'import' and _getCalendarSendUpdates(myarg, parameters):
    pass
  elif myarg == 'anyonecanaddself':
    body['anyoneCanAddSelf'] = getBoolean()
  elif myarg == 'guestscaninviteothers':
    body['guestsCanInviteOthers'] = getBoolean()
  elif myarg == 'guestscantinviteothers':
    body['guestsCanInviteOthers'] = False
  elif myarg == 'guestscanmodify':
    body['guestsCanModify'] = getBoolean()
  elif myarg == 'guestscanseeotherguests':
    body['guestsCanSeeOtherGuests'] = getBoolean()
  elif myarg == 'guestscantseeotherguests':
    body['guestsCanSeeOtherGuests'] = False
  elif myarg == 'status':
    body['status'] = getChoice(CALENDAR_EVENT_STATUS_CHOICES)
  elif myarg == 'tentative':
    body['status'] = 'tentative'
  elif myarg == 'transparency':
    body['transparency'] = getChoice(CALENDAR_EVENT_TRANSPARENCY_CHOICES)
  elif myarg == 'available':
    body['transparency'] = 'transparent'
  elif myarg == 'visibility':
    body['visibility'] = getChoice(CALENDAR_EVENT_VISIBILITY_CHOICES)
  elif myarg in {'color', 'colour'}:
    body['colorId'] = getChoice(CALENDAR_EVENT_COLOR_MAP, mapChoice=True)
  elif myarg in {'colorindex', 'colorid', 'colourindex', 'colourid'}:
    body['colorId'] = getInteger(CALENDAR_EVENT_MIN_COLOR_INDEX, CALENDAR_EVENT_MAX_COLOR_INDEX)
  elif _getCalendarEventReminders(myarg, body):
    pass
  elif myarg == 'sequence':
    body['sequence'] = getInteger(minVal=0)
  elif myarg == 'privateproperty':
    body.setdefault('extendedProperties', {})
    body['extendedProperties'].setdefault('private', {})
    key = getString(Cmd.OB_PROPERTY_KEY)
    body['extendedProperties']['private'][key] = getString(Cmd.OB_PROPERTY_VALUE, minLen=0)
  elif myarg == 'sharedproperty':
    body.setdefault('extendedProperties', {})
    body['extendedProperties'].setdefault('shared', {})
    key = getString(Cmd.OB_PROPERTY_KEY)
    body['extendedProperties']['shared'][key] = getString(Cmd.OB_PROPERTY_VALUE, minLen=0)
  elif function == 'update' and myarg == 'clearprivateproperty':
    body.setdefault('extendedProperties', {})
    body['extendedProperties'].setdefault('private', {})
    body['extendedProperties']['private'][getString(Cmd.OB_PROPERTY_KEY)] = None
  elif function == 'update' and myarg == 'clearsharedproperty':
    body.setdefault('extendedProperties', {})
    body['extendedProperties'].setdefault('shared', {})
    body['extendedProperties']['shared'][getString(Cmd.OB_PROPERTY_KEY)] = None
  elif function == 'import' and myarg in {'organizername', 'organisername'}:
    body.setdefault('organizer', {})
    body['organizer']['displayName'] = getString(Cmd.OB_NAME)
  elif function == 'import' and myarg in {'organizeremail', 'organiseremail'}:
    body.setdefault('organizer', {})
    body['organizer']['email'] = getEmailAddress(noUid=True)
  else:
    return False
  return True

def _getEventMatchFields(calendarEventEntity, fieldsList):
  for match in calendarEventEntity['matches']:
    if match[0][0] != 'attendees':
      fieldsList.append(match[0][0])
    else:
      fieldsList.append('attendees/email')
      if match[0][1] == 'status':
        fieldsList.extend(['attendees/optional', 'attendees/responseStatus'])

def _eventMatches(event, match):
  if match[0][0] != 'attendees':
    eventAttr = event
    for attr in match[0]:
      eventAttr = eventAttr.get(attr, '')
      if not eventAttr:
        break
    if match[0][0] == 'organizer' and match[0][1] == 'self':
      return bool(eventAttr) == match[1]
    if match[0][0] != 'hangoutLink':
      return match[1].search(eventAttr) is not None
# vkj-przn-nvg or vkjprznnvg
    return match[1].search(eventAttr) is not None or match[1].search(eventAttr.replace('-', '')) is not None
  attendees = [attendee['email'] for attendee in event.get('attendees', []) if 'email' in attendee]
  if not attendees:
    return False
  if match[0][1] == 'email':
    for attendee in match[1]:
      if attendee not in attendees:
        return False
    return True
  if match[0][1] == 'match':
    for attendee in attendees:
      if match[1].search(attendee) is not None:
        return True
    return False
  if match[0][1] == 'onlydomainlist':
    for attendee in attendees:
      _, domain = attendee.lower().split('@', 1)
      if domain not in match[1]:
        return False
    return True
  if match[0][1] == 'domainlist':
    for attendee in attendees:
      _, domain = attendee.lower().split('@', 1)
      if domain in match[1]:
        return True
    return False
  if match[0][1] == 'notdomainlist':
    for attendee in attendees:
      _, domain = attendee.lower().split('@', 1)
      if domain not in match[1]:
        return True
    return False
  if match[0][1] == 'organizer':
    for matchEmail in match[2]:
      for attendee in event['attendees']:
        if 'email' in attendee and matchEmail == attendee['email']:
          if attendee.get('organizer', False) != match[1]:
            return False
          break
      else:
        return False
    return True
  # if match[0][1] == 'status':
  for matchEmail in match[3]:
    for attendee in event['attendees']:
      if 'email' in attendee and matchEmail == attendee['email']:
        if attendee.get('optional', False) != match[1] or attendee.get('responseStatus') != match[2]:
          return False
        break
    else:
      return False
  return True

def _validateCalendarGetEventIDs(origUser, user, origCal, calId, j, jcount, calendarEventEntity, doIt=True, showAction=True):
  if calendarEventEntity['dict']:
    if origUser:
      if not GM.Globals[GM.CSV_SUBKEY_FIELD]:
        calEventIds = calendarEventEntity['dict'][calId]
      else:
        calEventIds = calendarEventEntity['dict'][origUser][calId]
    else:
      calEventIds = calendarEventEntity['dict'][calId]
  else:
    calEventIds = calendarEventEntity['list']
  calId, cal = getNormalizedCalIdCal(origCal, calId, user, j, jcount)
  if not cal:
    return (calId, cal, None, 0)
  if not calEventIds:
    fieldsList = ['id']
    _getEventMatchFields(calendarEventEntity, fieldsList)
    fields = ','.join(fieldsList)
    try:
      eventIdsSet = set()
      calEventIds = []
      if len(calendarEventEntity['queries']) <= 1:
        if len(calendarEventEntity['queries']) == 1:
          calendarEventEntity['kwargs']['q'] = calendarEventEntity['queries'][0]
        events = callGAPIpages(cal.events(), 'list', 'items',
                               throwReasons=GAPI.CALENDAR_THROW_REASONS+[GAPI.NOT_FOUND, GAPI.FORBIDDEN, GAPI.INVALID],
                               calendarId=calId, fields=f'nextPageToken,items({fields})',
                               maxResults=GC.Values[GC.EVENT_MAX_RESULTS], **calendarEventEntity['kwargs'])
        for event in events:
          for match in calendarEventEntity['matches']:
            if not _eventMatches(event, match):
              break
          else:
            calEventIds.append(event['id'])
      else:
        for query in calendarEventEntity['queries']:
          calendarEventEntity['kwargs']['q'] = query
          events = callGAPIpages(cal.events(), 'list', 'items',
                                 throwReasons=GAPI.CALENDAR_THROW_REASONS+[GAPI.NOT_FOUND, GAPI.FORBIDDEN, GAPI.INVALID],
                                 calendarId=calId, fields=f'nextPageToken,items({fields})',
                                 maxResults=GC.Values[GC.EVENT_MAX_RESULTS], **calendarEventEntity['kwargs'])
          for event in events:
            for match in calendarEventEntity['matches']:
              if not _eventMatches(event, match):
                break
            else:
              eventId = event['id']
              if eventId not in eventIdsSet:
                calEventIds.append(eventId)
                eventIdsSet.add(eventId)
      kcount = len(calEventIds)
      if kcount == 0:
        entityNumEntitiesActionNotPerformedWarning([Ent.CALENDAR, calId], Ent.EVENT, kcount, Msg.NO_ENTITIES_MATCHED.format(Ent.Plural(Ent.EVENT)), j, jcount)
        setSysExitRC(NO_ENTITIES_FOUND_RC)
        return (calId, cal, None, 0)
    except GAPI.notFound:
      entityUnknownWarning(Ent.CALENDAR, calId, j, jcount)
      return (calId, cal, None, 0)
    except (GAPI.forbidden, GAPI.invalid) as e:
      entityActionFailedWarning([Ent.CALENDAR, calId], str(e), j, jcount)
      return (calId, cal, None, 0)
    except GAPI.notACalendarUser:
      userCalServiceNotEnabledWarning(calId, j, jcount)
      return (calId, cal, None, 0)
  else:
    kcount = len(calEventIds)
  if kcount == 0:
    setSysExitRC(NO_ENTITIES_FOUND_RC)
  if not doIt:
    if showAction:
      entityNumEntitiesActionNotPerformedWarning([Ent.CALENDAR, calId], Ent.EVENT, kcount, Msg.USE_DOIT_ARGUMENT_TO_PERFORM_ACTION, j, jcount)
    return (calId, cal, None, 0)
  if showAction:
    entityPerformActionNumItems([Ent.CALENDAR, calId], kcount, Ent.EVENT, j, jcount)
  return (calId, cal, calEventIds, kcount)

