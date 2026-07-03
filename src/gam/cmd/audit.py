"""GAM audit monitor commands (GDATA).\n\nExtracted from gam/__init__.py. Provides mailbox monitor\ncreation/deletion/listing and doWhatIs command."""

import re
import sys

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


def _getMain():
  return sys.modules['gam']

def __getattr__(name):
  """Fall back to gam module for any undefined names."""
  main = _getMain()
  try:
    return getattr(main, name)
  except AttributeError:
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")

def getAuditParameters(emailAddressRequired=True, requestIdRequired=True, destUserRequired=False):
  auditObject = _getMain().getEmailAuditObject()
  emailAddress = _getMain().getEmailAddress(noUid=True, optional=not emailAddressRequired)
  parameters = {}
  if emailAddress:
    parameters['auditUser'] = emailAddress
    parameters['auditUserName'], auditObject.domain = _getMain().splitEmailAddress(emailAddress)
    if requestIdRequired:
      parameters['requestId'] = _getMain().getString(Cmd.OB_REQUEST_ID)
    if destUserRequired:
      destEmailAddress = _getMain().getEmailAddress(noUid=True)
      parameters['auditDestUser'] = destEmailAddress
      parameters['auditDestUserName'], destDomain = _getMain().splitEmailAddress(destEmailAddress)
      if auditObject.domain != destDomain:
        Cmd.Backup()
        _getMain().invalidArgumentExit(f'{parameters["auditDestUserName"]}@{auditObject.domain}')
  return (auditObject, parameters)

# Audit monitor command utilities
def _showMailboxMonitorRequestStatus(request, i=0, count=0):
  _getMain().printKeyValueListWithCount(['Destination', _getMain().normalizeEmailAddressOrUID(request['destUserName'])], i, count)
  Ind.Increment()
  _getMain().printKeyValueList(['Begin', request.get('beginDate', 'immediately')])
  _getMain().printKeyValueList(['End', request['endDate']])
  _getMain().printKeyValueList(['Monitor Incoming', request['outgoingEmailMonitorLevel']])
  _getMain().printKeyValueList(['Monitor Outgoing', request['incomingEmailMonitorLevel']])
  _getMain().printKeyValueList(['Monitor Chats', request.get('chatMonitorLevel', 'NONE')])
  _getMain().printKeyValueList(['Monitor Drafts', request.get('draftMonitorLevel', 'NONE')])
  Ind.Decrement()

# gam audit monitor create <EmailAddress> <DestEmailAddress> [begin <DateTime>] [end <DateTime>] [incoming_headers] [outgoing_headers] [nochats] [nodrafts] [chat_headers] [draft_headers]
def doCreateMonitor():
  auditObject, parameters = getAuditParameters(emailAddressRequired=True, requestIdRequired=False, destUserRequired=True)
  #end_date defaults to 30 days in the future...
  end_date = GM.Globals[GM.DATETIME_NOW].shift(days=30).strftime(_getMain().YYYYMMDD_HHMM_FORMAT)
  begin_date = None
  incoming_headers_only = outgoing_headers_only = drafts_headers_only = chats_headers_only = False
  drafts = chats = True
  while Cmd.ArgumentsRemaining():
    myarg = _getMain().getArgument()
    if myarg == 'begin':
      begin_date = _getMain().getYYYYMMDD_HHMM()
    elif myarg == 'end':
      end_date = _getMain().getYYYYMMDD_HHMM()
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
      _getMain().unknownArgumentExit()
  try:
    request = _getMain().callGData(auditObject, 'createEmailMonitor',
                        throwErrors=[GDATA.INVALID_VALUE, GDATA.INVALID_INPUT, GDATA.DOES_NOT_EXIST, GDATA.INVALID_DOMAIN],
                        source_user=parameters['auditUserName'], destination_user=parameters['auditDestUserName'], end_date=end_date, begin_date=begin_date,
                        incoming_headers_only=incoming_headers_only, outgoing_headers_only=outgoing_headers_only,
                        drafts=drafts, drafts_headers_only=drafts_headers_only, chats=chats, chats_headers_only=chats_headers_only)
    _getMain().entityActionPerformed([Ent.USER, parameters['auditUser'], Ent.AUDIT_MONITOR_REQUEST, None])
    Ind.Increment()
    _showMailboxMonitorRequestStatus(request)
    Ind.Decrement()
  except (GDATA.invalidValue, GDATA.invalidInput) as e:
    _getMain().entityActionFailedWarning([Ent.USER, parameters['auditUser'], Ent.AUDIT_MONITOR_REQUEST, None], str(e))
  except (GDATA.doesNotExist, GDATA.invalidDomain) as e:
    if str(e).find(parameters['auditUser']) != -1:
      _getMain().entityUnknownWarning(Ent.USER, parameters['auditUser'])
    else:
      _getMain().entityActionFailedWarning([Ent.USER, parameters['auditUser'], Ent.AUDIT_MONITOR_REQUEST, None], str(e))

# gam audit monitor delete <EmailAddress> <DestEmailAddress>
def doDeleteMonitor():
  auditObject, parameters = getAuditParameters(emailAddressRequired=True, requestIdRequired=False, destUserRequired=True)
  _getMain().checkForExtraneousArguments()
  try:
    _getMain().callGData(auditObject, 'deleteEmailMonitor',
              throwErrors=[GDATA.INVALID_INPUT, GDATA.DOES_NOT_EXIST, GDATA.INVALID_DOMAIN],
              source_user=parameters['auditUserName'], destination_user=parameters['auditDestUserName'])
    _getMain().entityActionPerformed([Ent.USER, parameters['auditUser'], Ent.AUDIT_MONITOR_REQUEST, parameters['auditDestUser']])
  except GDATA.invalidInput as e:
    _getMain().entityActionFailedWarning([Ent.USER, parameters['auditUser'], Ent.AUDIT_MONITOR_REQUEST, None], str(e))
  except (GDATA.doesNotExist, GDATA.invalidDomain) as e:
    if str(e).find(parameters['auditUser']) != -1:
      _getMain().entityUnknownWarning(Ent.USER, parameters['auditUser'])
    else:
      _getMain().entityActionFailedWarning([Ent.USER, parameters['auditUser'], Ent.AUDIT_MONITOR_REQUEST, None], str(e))

# gam audit monitor list <EmailAddress>
def doShowMonitors():
  auditObject, parameters = getAuditParameters(emailAddressRequired=True, requestIdRequired=False, destUserRequired=False)
  _getMain().checkForExtraneousArguments()
  try:
    results = _getMain().callGData(auditObject, 'getEmailMonitors',
                        throwErrors=[GDATA.DOES_NOT_EXIST, GDATA.INVALID_DOMAIN],
                        user=parameters['auditUserName'])
    jcount = len(results) if (results) else 0
    _getMain().entityPerformActionNumItems([Ent.USER, parameters['auditUser']], jcount, Ent.AUDIT_MONITOR_REQUEST)
    if jcount == 0:
      _getMain().setSysExitRC(_getMain().NO_ENTITIES_FOUND_RC)
      return
    Ind.Increment()
    j = 0
    for request in results:
      j += 1
      _showMailboxMonitorRequestStatus(request, j, jcount)
    Ind.Decrement()
  except (GDATA.doesNotExist, GDATA.invalidDomain):
    _getMain().entityUnknownWarning(Ent.USER, parameters['auditUser'])

# gam whatis <EmailItem> [noinfo] [noinvitablecheck]
