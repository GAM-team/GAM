"""GAM audit monitor commands (GDATA).

Mailbox monitor creation/deletion/listing and the doWhatIs command.
"""

import re

from gamlib import api as API
from gamlib import settings as GC
from gamlib import gapi as GAPI
from gamlib import state as GM
from gamlib import msgs as Msg
from gam.var import Act, Cmd, Ent, Ind
from gam.util.access import entityUnknownWarning
from gam.util.api import getEmailAuditObject
from gam.util.api_call import callGData
from gam.util.args import (
    YYYYMMDD_HHMM_FORMAT,
    checkForExtraneousArguments,
    getArgument,
    getEmailAddress,
    getString,
    getYYYYMMDD_HHMM,
    normalizeEmailAddressOrUID,
    splitEmailAddress,
)
from gam.util.display import (
    entityActionFailedWarning,
    entityActionPerformed,
    entityPerformActionNumItems,
    printKeyValueList,
    printKeyValueListWithCount,
)
from gam.util.errors import invalidArgumentExit, unknownArgumentExit
from gam.util.output import setSysExitRC
from gam.constants import NO_ENTITIES_FOUND_RC


def getAuditParameters(emailAddressRequired=True, requestIdRequired=True, destUserRequired=False):
  auditObject = getEmailAuditObject()
  emailAddress = getEmailAddress(noUid=True, optional=not emailAddressRequired)
  parameters = {}
  if emailAddress:
    parameters['auditUser'] = emailAddress
    parameters['auditUserName'], auditObject.domain = splitEmailAddress(emailAddress)
    if requestIdRequired:
      parameters['requestId'] = getString(Cmd.OB_REQUEST_ID)
    if destUserRequired:
      destEmailAddress = getEmailAddress(noUid=True)
      parameters['auditDestUser'] = destEmailAddress
      parameters['auditDestUserName'], destDomain = splitEmailAddress(destEmailAddress)
      if auditObject.domain != destDomain:
        Cmd.Backup()
        invalidArgumentExit(f'{parameters["auditDestUserName"]}@{auditObject.domain}')
  return (auditObject, parameters)

# Audit monitor command utilities
def _showMailboxMonitorRequestStatus(request, i=0, count=0):
  printKeyValueListWithCount(['Destination', normalizeEmailAddressOrUID(request['destUserName'])], i, count)
  Ind.Increment()
  printKeyValueList(['Begin', request.get('beginDate', 'immediately')])
  printKeyValueList(['End', request['endDate']])
  printKeyValueList(['Monitor Incoming', request['outgoingEmailMonitorLevel']])
  printKeyValueList(['Monitor Outgoing', request['incomingEmailMonitorLevel']])
  printKeyValueList(['Monitor Chats', request.get('chatMonitorLevel', 'NONE')])
  printKeyValueList(['Monitor Drafts', request.get('draftMonitorLevel', 'NONE')])
  Ind.Decrement()

# gam audit monitor create <EmailAddress> <DestEmailAddress> [begin <DateTime>] [end <DateTime>] [incoming_headers] [outgoing_headers] [nochats] [nodrafts] [chat_headers] [draft_headers]
def doCreateMonitor():
  auditObject, parameters = getAuditParameters(emailAddressRequired=True, requestIdRequired=False, destUserRequired=True)
  #end_date defaults to 30 days in the future...
  end_date = GM.Globals[GM.DATETIME_NOW].shift(days=30).strftime(YYYYMMDD_HHMM_FORMAT)
  begin_date = None
  incoming_headers_only = outgoing_headers_only = drafts_headers_only = chats_headers_only = False
  drafts = chats = True
  while Cmd.ArgumentsRemaining():
    myarg = getArgument()
    if myarg == 'begin':
      begin_date = getYYYYMMDD_HHMM()
    elif myarg == 'end':
      end_date = getYYYYMMDD_HHMM()
    elif myarg == 'incomingheaders':
      incoming_headers_only = True
    elif myarg == 'outgoingheaders':
      outgoing_headers_only = True
    elif myarg == 'nochats':
      chats = False
    elif myarg == 'nodrafts':
      drafts = False
    elif myarg == 'chatheaders':
      chats_headers_only = True
    elif myarg == 'draftheaders':
      drafts_headers_only = True
    else:
      unknownArgumentExit()
  try:
    request = callGData(auditObject, 'createEmailMonitor',
                        throwErrors=[GDATA.INVALID_VALUE, GDATA.INVALID_INPUT, GDATA.DOES_NOT_EXIST, GDATA.INVALID_DOMAIN],
                        source_user=parameters['auditUserName'], destination_user=parameters['auditDestUserName'], end_date=end_date, begin_date=begin_date,
                        incoming_headers_only=incoming_headers_only, outgoing_headers_only=outgoing_headers_only,
                        drafts=drafts, drafts_headers_only=drafts_headers_only, chats=chats, chats_headers_only=chats_headers_only)
    entityActionPerformed([Ent.USER, parameters['auditUser'], Ent.AUDIT_MONITOR_REQUEST, None])
    Ind.Increment()
    _showMailboxMonitorRequestStatus(request)
    Ind.Decrement()
  except (GDATA.invalidValue, GDATA.invalidInput) as e:
    entityActionFailedWarning([Ent.USER, parameters['auditUser'], Ent.AUDIT_MONITOR_REQUEST, None], str(e))
  except (GDATA.doesNotExist, GDATA.invalidDomain) as e:
    if str(e).find(parameters['auditUser']) != -1:
      entityUnknownWarning(Ent.USER, parameters['auditUser'])
    else:
      entityActionFailedWarning([Ent.USER, parameters['auditUser'], Ent.AUDIT_MONITOR_REQUEST, None], str(e))

# gam audit monitor delete <EmailAddress> <DestEmailAddress>
def doDeleteMonitor():
  auditObject, parameters = getAuditParameters(emailAddressRequired=True, requestIdRequired=False, destUserRequired=True)
  checkForExtraneousArguments()
  try:
    callGData(auditObject, 'deleteEmailMonitor',
              throwErrors=[GDATA.INVALID_INPUT, GDATA.DOES_NOT_EXIST, GDATA.INVALID_DOMAIN],
              source_user=parameters['auditUserName'], destination_user=parameters['auditDestUserName'])
    entityActionPerformed([Ent.USER, parameters['auditUser'], Ent.AUDIT_MONITOR_REQUEST, parameters['auditDestUser']])
  except GDATA.invalidInput as e:
    entityActionFailedWarning([Ent.USER, parameters['auditUser'], Ent.AUDIT_MONITOR_REQUEST, None], str(e))
  except (GDATA.doesNotExist, GDATA.invalidDomain) as e:
    if str(e).find(parameters['auditUser']) != -1:
      entityUnknownWarning(Ent.USER, parameters['auditUser'])
    else:
      entityActionFailedWarning([Ent.USER, parameters['auditUser'], Ent.AUDIT_MONITOR_REQUEST, None], str(e))

# gam audit monitor list <EmailAddress>
def doShowMonitors():
  auditObject, parameters = getAuditParameters(emailAddressRequired=True, requestIdRequired=False, destUserRequired=False)
  checkForExtraneousArguments()
  try:
    results = callGData(auditObject, 'getEmailMonitors',
                        throwErrors=[GDATA.DOES_NOT_EXIST, GDATA.INVALID_DOMAIN],
                        user=parameters['auditUserName'])
    jcount = len(results) if (results) else 0
    entityPerformActionNumItems([Ent.USER, parameters['auditUser']], jcount, Ent.AUDIT_MONITOR_REQUEST)
    if jcount == 0:
      setSysExitRC(NO_ENTITIES_FOUND_RC)
      return
    Ind.Increment()
    j = 0
    for request in results:
      j += 1
      _showMailboxMonitorRequestStatus(request, j, jcount)
    Ind.Decrement()
  except (GDATA.doesNotExist, GDATA.invalidDomain):
    entityUnknownWarning(Ent.USER, parameters['auditUser'])

# gam whatis <EmailItem> [noinfo] [noinvitablecheck]

# Dispatch tables and routing (moved from __init__.py)
# Additional imports for dispatch
from gam.util.args import getChoice
from gam.constants import CMD_ACTION, CMD_FUNCTION

AUDIT_SUBCOMMANDS_WITH_OBJECTS = {
  'monitor':
    {'create': (Act.CREATE, doCreateMonitor),
     'delete': (Act.DELETE, doDeleteMonitor),
     'list': (Act.LIST, doShowMonitors),
    },
  }

def processAuditCommands():
  CL_subCommand = getChoice(list(AUDIT_SUBCOMMANDS_WITH_OBJECTS))
  CL_objectName = getChoice(AUDIT_SUBCOMMANDS_WITH_OBJECTS[CL_subCommand])
  Act.Set(AUDIT_SUBCOMMANDS_WITH_OBJECTS[CL_subCommand][CL_objectName][CMD_ACTION])
  AUDIT_SUBCOMMANDS_WITH_OBJECTS[CL_subCommand][CL_objectName][CMD_FUNCTION]()

