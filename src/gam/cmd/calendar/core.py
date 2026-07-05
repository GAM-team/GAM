"""Shared constants and lightweight helpers for the calendar package.

This module exists to break circular imports between sibling modules
(acls, calendars, events, settings, resources).  It may only import from
the stdlib, gamlib/, gam/util/, gam/var, and gam/constants — NEVER from
sibling modules within gam/cmd/calendar/.
"""

from gamlib import api as API
from gamlib import gapi as GAPI
from gamlib import settings as GC
from gam.var import Cmd, Ent, Ind
from gam.util.access import checkEntityAFDNEorAccessErrorExit
from gam.util.api import buildGAPIObject
from gam.util.api_call import callGAPI
from gam.util.args import getArgument, getBoolean, getString, getStringWithCRsNLs
from gam.util.display import (
    entityActionFailedWarning,
    printEntity,
    printKeyValueList,
    printKeyValueWithCRsNLs,
    userCalServiceNotEnabledWarning,
)
from gam.util.svcacct import buildGAPIServiceObject
from gam.util.errors import entityDoesNotExistExit, missingArgumentExit, unknownArgumentExit
from gam.util.uid import convertUIDtoEmailAddress


# ---------------------------------------------------------------------------
# Constants (moved from events.py)
# ---------------------------------------------------------------------------

CALENDAR_MIN_COLOR_INDEX = 1
CALENDAR_MAX_COLOR_INDEX = 24


# ---------------------------------------------------------------------------
# Lightweight helpers (moved from acls.py)
# ---------------------------------------------------------------------------

def ACLRuleKeyValueList(rule):
  if rule['scope']['type'] != 'default':
    return ['Scope', f'{rule["scope"]["type"]}:{rule["scope"]["value"]}', 'Role', rule['role']]
  return ['Scope', f'{rule["scope"]["type"]}', 'Role', rule['role']]


# ---------------------------------------------------------------------------
# Resource validation (moved from resources.py)
# ---------------------------------------------------------------------------

def _validateResourceId(cd, resourceId, i, count, exitOnNotFound):
  try:
    return callGAPI(cd.resources().calendars(), 'get',
                    throwReasons=[GAPI.BAD_REQUEST, GAPI.RESOURCE_NOT_FOUND, GAPI.FORBIDDEN],
                    customer=GC.Values[GC.CUSTOMER_ID], calendarResourceId=resourceId, fields='resourceEmail')['resourceEmail']
  except (GAPI.badRequest, GAPI.resourceNotFound, GAPI.forbidden):
    if exitOnNotFound:
      entityDoesNotExistExit(Ent.RESOURCE_CALENDAR, resourceId, i, count)
    checkEntityAFDNEorAccessErrorExit(cd, Ent.RESOURCE_CALENDAR, resourceId, i, count)
    return None


# ---------------------------------------------------------------------------
# Calendar settings helpers (moved from settings.py)
# ---------------------------------------------------------------------------

# gam <UserTypeEntity> create calendaracls <UserCalendarEntity> <CalendarACLRole> <CalendarACLScopeEntity> [sendnotifications <Boolean>]
def _getCalendarSetting(myarg, body):
  if myarg == 'description':
    body['description'] = getStringWithCRsNLs()
  elif myarg == 'location':
    body['location'] = getString(Cmd.OB_STRING, minLen=0)
  elif myarg == 'summary':
    body['summary'] = getString(Cmd.OB_STRING)
  elif myarg == 'timezone':
    body['timeZone'] = getString(Cmd.OB_STRING)
  elif myarg == 'autoacceptinvitations':
    body['autoAcceptInvitations'] = getBoolean()
  else:
    return False
  return True

def getCalendarSettings(summaryRequired=False):
  body = {}
  while Cmd.ArgumentsRemaining():
    myarg = getArgument()
    if _getCalendarSetting(myarg, body):
      pass
    else:
      unknownArgumentExit()
  if summaryRequired and not body.get('summary', None):
    missingArgumentExit('summary <String>')
  return body

def _showCalendarSettings(calendar, j, jcount):
  printEntity([Ent.CALENDAR, calendar['id']], j, jcount)
  Ind.Increment()
  if 'dataOwner' in calendar:
    printKeyValueList(['Owner', calendar['dataOwner']])
  if 'summaryOverride' in calendar or 'summary' in calendar:
    printKeyValueList(['Summary', calendar.get('summaryOverride', calendar.get('summary', ''))])
  if 'description' in calendar:
    printKeyValueWithCRsNLs('Description', calendar['description'])
  if 'location' in calendar:
    printKeyValueList(['Location', calendar['location']])
  if 'timeZone' in calendar:
    printKeyValueList(['Timezone', calendar['timeZone']])
  if 'conferenceProperties' in calendar:
    printKeyValueList(['ConferenceProperties', None])
    Ind.Increment()
    printKeyValueList(['AllowedConferenceSolutionTypes', ','.join(calendar.get('conferenceProperties', {}).get('allowedConferenceSolutionTypes', []))])
    Ind.Decrement()
  if 'autoAcceptInvitations' in calendar:
    printKeyValueList(['AutoAcceptInvitations', calendar['autoAcceptInvitations']])
  Ind.Decrement()


# ---------------------------------------------------------------------------
# Calendar validation helpers (moved from __init__.py)
# ---------------------------------------------------------------------------

def normalizeCalendarId(calId, user):
  if not user or calId.lower() != 'primary':
    return convertUIDtoEmailAddress(calId, emailTypes=['user', 'resource'])
  return user

def checkCalendarExists(cal, calId, i, count, showMessage=False):
  if not cal:
    cal = buildGAPIObject(API.CALENDAR)
  try:
    return callGAPI(cal.calendars(), 'get',
                    throwReasons=GAPI.CALENDAR_THROW_REASONS+[GAPI.NOT_FOUND],
                    calendarId=calId, fields='id')['id']
  except GAPI.notFound as e:
    if showMessage:
      entityActionFailedWarning([Ent.CALENDAR, calId], str(e))
    return None
  except GAPI.notACalendarUser:
    if showMessage:
      userCalServiceNotEnabledWarning(calId, i, count)
    return None

def validateCalendar(calId, i=0, count=0, noClientAccess=False):
  cal = None
  if not calId.endswith('.calendar.google.com'):
    calId, cal = buildGAPIServiceObject(API.CALENDAR, calId, i, count, displayError=noClientAccess)
  if not cal:
    if noClientAccess:
      return (calId, None)
    cal = buildGAPIObject(API.CALENDAR)
  try:
    callGAPI(cal.calendars(), 'get',
             throwReasons=GAPI.CALENDAR_THROW_REASONS+[GAPI.NOT_FOUND],
             calendarId=calId, fields='')
    return (calId, cal)
  except GAPI.notFound as e:
    entityActionFailedWarning([Ent.CALENDAR, calId], str(e), i, count)
  except GAPI.notACalendarUser:
    userCalServiceNotEnabledWarning(calId, i, count)
  return (calId, None)

def getNormalizedCalIdCal(cal, calId, user, i=0, count=0):
  if not cal:
    return validateCalendar(calId, i, count)
  return (normalizeCalendarId(calId, user), cal)

CALENDAR_ACL_ROLES_MAP = {
  'editor': 'writer',
  'freebusy': 'freeBusyReader',
  'freebusyreader': 'freeBusyReader',
  'owner': 'owner',
  'read': 'reader',
  'reader': 'reader',
  'writer': 'writer',
  'writerwithoutprivateaccess': 'writerWithoutPrivateAccess',
  'none': 'none',
  }

ACL_SCOPE_CHOICES = ['default', 'user', 'group', 'domain'] # default must be first element
