"""GAM calendar ACL, event, and settings management."""



from gamlib import api as API
from gamlib import gapi as GAPI
from gam.var import Ent
from gam.util.api import buildGAPIObject
from gam.util.svcacct import buildGAPIServiceObject
from gam.util.api_call import callGAPI
from gam.util.display import (
    entityActionFailedWarning,
    userCalServiceNotEnabledWarning,
)
from gam.util.entity import convertUIDtoEmailAddress


# ACL utility functions (moved from gam/__init__.py)
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

