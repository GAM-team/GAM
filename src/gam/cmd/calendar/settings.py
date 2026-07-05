"""GAM calendar settings commands."""

import json

from gamlib import gapi as GAPI
from gam.var import Act, Cmd, Ent, Ind
from gam.util.api_call import callGAPI, callGAPIpages
from gam.util.args import getArgument
from gam.util.csv_pf import CSVPrintFile, FormatJSONQuoteChar, cleanJSON, flattenJSON, getFieldsFromFieldsList, getFieldsList
from gam.util.display import entityActionFailedWarning, entityActionPerformed, printEntityKVList, printKeyValueList, printLine, userCalServiceNotEnabledWarning
from gam.util.entity import getEntityArgument

from gam.cmd.calendar.core import validateCalendar, getCalendarSettings, _showCalendarSettings
from gam.cmd.calendar.calendars import USER_CALENDAR_SETTINGS_FIELDS_CHOICE_MAP

def printShowCalSettings(users):
  csvPF = CSVPrintFile(['User'], 'sortall') if Act.csvFormat() else None
  FJQC = FormatJSONQuoteChar(csvPF)
  fieldsList = []
  while Cmd.ArgumentsRemaining():
    myarg = getArgument()
    if csvPF and myarg == 'todrive':
      csvPF.GetTodriveParameters()
    elif getFieldsList(myarg, USER_CALENDAR_SETTINGS_FIELDS_CHOICE_MAP, fieldsList):
      pass
    else:
      FJQC.GetFormatJSONQuoteChar(myarg, True)
  fields = set(fieldsList)
  i, count, users = getEntityArgument(users)
  for user in users:
    i += 1
    user, cal = validateCalendar(user, i, count, noClientAccess=True)
    if not cal:
      continue
    try:
      feed = callGAPIpages(cal.settings(), 'list', 'items',
                           throwReasons=GAPI.CALENDAR_THROW_REASONS)
    except GAPI.notACalendarUser:
      userCalServiceNotEnabledWarning(user, i, count)
      continue
    settings = {}
    for setting in feed:
      if not fields or setting['id'] in fields:
        settings[setting['id']] = setting['value']
    if not csvPF:
      if not FJQC.formatJSON:
        printEntityKVList([Ent.USER, user], [Ent.Plural(Ent.CALENDAR_SETTINGS), None], i, count)
        Ind.Increment()
        for attr in sorted(settings):
          printKeyValueList([attr, settings[attr]])
        Ind.Decrement()
      else:
        printLine(json.dumps({'User': user, 'settings': settings}, ensure_ascii=False, sort_keys=True))
    else:
      row = flattenJSON(settings, flattened={'User': user})
      if not FJQC.formatJSON:
        csvPF.WriteRowTitles(row)
      elif csvPF.CheckRowTitles(row):
        csvPF.WriteRowNoFilter({'User': user, 'JSON': json.dumps(settings, ensure_ascii=False, sort_keys=True)})
  if csvPF:
    csvPF.writeCSVfile('Calendar Settings')

# gam <UserTypeEntity> create calendaracls <UserCalendarEntity> <CalendarACLRole> <CalendarACLScopeEntity> [sendnotifications <Boolean>]
# Re-exported from core; kept here for backward compatibility.

# gam calendars <CalendarEntity> modify <CalendarSettings>
def doCalendarsModifySettings(calIds):
  body = getCalendarSettings(summaryRequired=False)
  count = len(calIds)
  i = 0
  for calId in calIds:
    i += 1
    calId, cal = validateCalendar(calId, i, count)
    if not cal:
      continue
    try:
      callGAPI(cal.calendars(), 'patch',
               throwReasons=GAPI.CALENDAR_THROW_REASONS+[GAPI.NOT_FOUND, GAPI.FORBIDDEN, GAPI.INVALID],
               calendarId=calId, body=body)
      entityActionPerformed([Ent.CALENDAR, calId], i, count)
    except (GAPI.notFound, GAPI.forbidden, GAPI.invalid) as e:
      entityActionFailedWarning([Ent.CALENDAR, calId], str(e), i, count)
    except GAPI.notACalendarUser:
      userCalServiceNotEnabledWarning(calId, i, count)

CALENDAR_SETTINGS_FIELDS_CHOICE_MAP = {
  'autoacceptinvitations': 'autoAcceptInvitations',
  'conferenceproperties': 'conferenceProperties',
  'dataowner': 'dataOwner',
  'description': 'description',
  'id': 'id',
  'location': 'location',
  'summary': 'summary',
  'timezone': 'timeZone',
  }

# gam calendars <CalendarEntity> print settings [todrive <ToDriveAttribute>*]
#	[fields <CalendarSettingsFieldList>]
#	[formatjson] [quotechar <Character>}
# gam calendars <CalendarEntity> show settings
#	[fields <CalendarSettingsFieldList>]
#	[formatjson]
def doCalendarsPrintShowSettings(calIds):
  csvPF = CSVPrintFile(['calendarId'], 'sortall') if Act.csvFormat() else None
  FJQC = FormatJSONQuoteChar(csvPF)
  fieldsList = []
  while Cmd.ArgumentsRemaining():
    myarg = getArgument()
    if csvPF and myarg == 'todrive':
      csvPF.GetTodriveParameters()
    elif getFieldsList(myarg, CALENDAR_SETTINGS_FIELDS_CHOICE_MAP, fieldsList, initialField='id'):
      pass
    else:
      FJQC.GetFormatJSONQuoteChar(myarg, True)
  fields = getFieldsFromFieldsList(fieldsList)
  count = len(calIds)
  i = 0
  for calId in calIds:
    i += 1
    calId, cal = validateCalendar(calId, i, count)
    if not cal:
      continue
    try:
      calendar = callGAPI(cal.calendars(), 'get',
                          throwReasons=GAPI.CALENDAR_THROW_REASONS+[GAPI.NOT_FOUND, GAPI.FORBIDDEN],
                          calendarId=calId, fields=fields)
      if not csvPF:
        if not FJQC.formatJSON:
          _showCalendarSettings(calendar, i, count)
        else:
          printLine(json.dumps(cleanJSON(calendar), ensure_ascii=False, sort_keys=True))
      else:
        row = flattenJSON(calendar)
        if not FJQC.formatJSON:
          row['calendarId'] = row.pop('id')
          csvPF.WriteRowTitles(row)
        elif csvPF.CheckRowTitles(row):
          csvPF.WriteRowNoFilter({'calendarId': calId, 'JSON': json.dumps(cleanJSON(calendar), ensure_ascii=False, sort_keys=True)})
    except (GAPI.notFound, GAPI.forbidden) as e:
      entityActionFailedWarning([Ent.CALENDAR, calId], str(e), i, count)
    except GAPI.notACalendarUser:
      userCalServiceNotEnabledWarning(calId, i, count)
  if csvPF:
    csvPF.writeCSVfile('Calendar Settings')

