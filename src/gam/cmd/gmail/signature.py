"""Gmail signature and vacation settings.

Part of the _gmail_monolith sub-package."""

"""GAM Gmail management: labels, messages, filters, forwarding, sendas, S/MIME, CSE, vacation."""

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

def setSignature(users):
  tagReplacements = _getMain()._initTagReplacements()
  signature, _, html = _getMain().getStringOrFile('sig')
  body = {}
  primary = False
  while Cmd.ArgumentsRemaining():
    myarg = _getMain().getArgument()
    if myarg == 'primary':
      primary = True
    elif myarg == 'html':
      html = _getMain().getBoolean()
    else:
      getSendAsAttributes(myarg, body, tagReplacements)
  if not tagReplacements['subs']:
    body['signature'] = _processSignature(tagReplacements, signature, html)
  i, count, users = _getMain().getEntityArgument(users)
  for user in users:
    i += 1
    user, gmail = _getMain().buildGAPIServiceObject(API.GMAIL, user, i, count)
    if not gmail:
      continue
    if tagReplacements['subs']:
      _getMain()._getTagReplacementFieldValues(user, i, count, tagReplacements)
      body['signature'] = _processSignature(tagReplacements, signature, html)
    if primary:
      try:
        result = _getMain().callGAPI(gmail.users().settings().sendAs(), 'list',
                          throwReasons=GAPI.GMAIL_THROW_REASONS,
                          userId='me')
        for sendas in result['sendAs']:
          if sendas.get('isPrimary', False):
            emailAddress = sendas['sendAsEmail']
            _processSendAs(user, i, count, Ent.SIGNATURE, emailAddress, i, count, gmail, 'patch', False, body=body, sendAsEmail=emailAddress, fields='')
            break
      except GAPI.serviceNotAvailable:
        _getMain().userGmailServiceNotEnabledWarning(user, i, count)
    else:
      _processSendAs(user, i, count, Ent.SIGNATURE, user, i, count, gmail, 'patch', False, body=body, sendAsEmail=user, fields='')

VACATION_START_STARTED = 'Started'
VACATION_END_NOT_SPECIFIED = 'NotSpecified'

def _showVacation(user, i, count, result, showDisabled, sigReplyFormat):
  enabled = result['enableAutoReply']
  if not enabled and not showDisabled:
    return
  _getMain().printEntity([Ent.USER, user, Ent.VACATION, None], i, count)
  Ind.Increment()
  _getMain().printKeyValueList(['Enabled', enabled])
  _getMain().printKeyValueList(['Contacts Only', result['restrictToContacts']])
  _getMain().printKeyValueList(['Domain Only', result['restrictToDomain']])
  if 'startTime' in result:
    _getMain().printKeyValueList(['Start Date', _getMain().formatLocalDatestamp(result['startTime'])])
  elif enabled:
    _getMain().printKeyValueList(['Start Date', VACATION_START_STARTED])
  if 'endTime' in result:
    _getMain().printKeyValueList(['End Date', _getMain().formatLocalDatestamp(result['endTime'])])
  elif enabled:
    _getMain().printKeyValueList(['End Date', VACATION_END_NOT_SPECIFIED])
  _getMain().printKeyValueList(['Subject', result.get('responseSubject', 'None')])
  if sigReplyFormat == SIG_REPLY_HTML:
    _getMain().printKeyValueList(['Message', None])
    Ind.Increment()
    if result.get('responseBodyPlainText'):
      _getMain().printKeyValueList([Ind.MultiLineText(result['responseBodyPlainText'])])
    elif result.get('responseBodyHtml'):
      _getMain().printKeyValueList([Ind.MultiLineText(result['responseBodyHtml'])])
    else:
      _getMain().printKeyValueList(['None'])
    Ind.Decrement()
  elif sigReplyFormat == SIG_REPLY_FORMAT:
    _getMain().printKeyValueList(['Message', None])
    Ind.Increment()
    if result.get('responseBodyPlainText'):
      _getMain().printKeyValueList([Ind.MultiLineText(result['responseBodyPlainText'])])
    elif result.get('responseBodyHtml'):
      _getMain().printKeyValueList([Ind.MultiLineText(_getMain().dehtml(result['responseBodyHtml']))])
    else:
      _getMain().printKeyValueList(['None'])
    Ind.Decrement()
  else: # SIG_REPLY_COMPACT
    if result.get('responseBodyPlainText'):
      _getMain().printKeyValueList(['Message', _getMain().escapeCRsNLs(result['responseBodyPlainText'])])
    elif result.get('responseBodyHtml'):
      _getMain().printKeyValueList(['Message', _getMain().escapeCRsNLs(result['responseBodyHtml'])])
    else:
      _getMain().printKeyValueList(['Message', 'None'])
  Ind.Decrement()

# gam <UserTypeEntity> vacation [<Boolean>] [subject <String>]
#	[<VacationMessageContent>
#	    (replace <Tag> <UserReplacement>)*
#	    (replaceregex <REMatchPattern> <RESubstitution> <Tag> <UserReplacement>)*]
#	[html [<Boolean>]] [contactsonly [<Boolean>]] [domainonly [<Boolean>]]
#	[start|startdate <Date>|Started] [end|enddate <Date>|NotSpecified]
def setVacation(users):
  body = {}
  if Cmd.PeekArgumentPresent(_getMain().TRUE_VALUES) or Cmd.PeekArgumentPresent(_getMain().FALSE_VALUES):
    body['enableAutoReply'] = _getMain().getBoolean(None)
  responseBodyType = 'responseBodyPlainText'
  message = subject = None
  tagReplacements = _getMain()._initTagReplacements()
  while Cmd.ArgumentsRemaining():
    myarg = _getMain().getArgument()
    if myarg == 'subject':
      subject = _getMain().getString(Cmd.OB_STRING, minLen=0)
    elif myarg in _getMain().SORF_MSG_FILE_ARGUMENTS:
      message, _, html = _getMain().getStringOrFile(myarg)
      if html:
        responseBodyType = 'responseBodyHtml'
    elif _getMain()._getTagReplacement(myarg, tagReplacements, True):
      pass
    elif myarg == 'html':
      if _getMain().getBoolean():
        responseBodyType = 'responseBodyHtml'
    elif myarg == 'contactsonly':
      body['restrictToContacts'] = _getMain().getBoolean()
    elif myarg == 'domainonly':
      body['restrictToDomain'] = _getMain().getBoolean()
    elif myarg in {'start', 'startdate'}:
      body['startTime'] = _getMain().getYYYYMMDD(returnTimeStamp=True, alternateValue=VACATION_START_STARTED)
    elif myarg in {'end', 'enddate'}:
      body['endTime'] = _getMain().getYYYYMMDD(returnTimeStamp=True, alternateValue=VACATION_END_NOT_SPECIFIED)
    else:
      _getMain().unknownArgumentExit()
  if message:
    if responseBodyType == 'responseBodyHtml':
      message = message.replace('\r', '').replace('\\n', '<br/>')
    else:
      message = message.replace('\r', '').replace('\\n', '\n')
    if tagReplacements['tags'] and not tagReplacements['subs']:
      message = _getMain()._processTagReplacements(tagReplacements, message)
    body[responseBodyType] = message
  if subject:
    if tagReplacements['tags'] and not tagReplacements['subs']:
      subject = _getMain()._processTagReplacements(tagReplacements, subject)
    body['responseSubject'] = subject
  i, count, users = _getMain().getEntityArgument(users)
  for user in users:
    i += 1
    user, gmail = _getMain().buildGAPIServiceObject(API.GMAIL, user, i, count)
    if not gmail:
      continue
    if (message or subject) and tagReplacements['subs']:
      _getMain()._getTagReplacementFieldValues(user, i, count, tagReplacements)
      if message:
        body[responseBodyType] = _getMain()._processTagReplacements(tagReplacements, message)
      if subject:
        body['responseSubject'] = _getMain()._processTagReplacements(tagReplacements, subject)
    try:
      oldBody = _getMain().callGAPI(gmail.users().settings(), 'getVacation',
                         throwReasons=GAPI.GMAIL_THROW_REASONS,
                         userId='me')
      if body.get(responseBodyType):
        oldBody.pop('responseBodyPlainText', None)
        oldBody.pop('responseBodyHtml', None)
      oldBody.update(body)
      result = _getMain().callGAPI(gmail.users().settings(), 'updateVacation',
                        throwReasons=GAPI.GMAIL_THROW_REASONS+[GAPI.INVALID_ARGUMENT,
                                                               GAPI.FAILED_PRECONDITION, GAPI.PERMISSION_DENIED],
                        userId='me', body=oldBody)
      _getMain().printEntity([Ent.USER, user, Ent.VACATION_ENABLED, result['enableAutoReply']], i, count)
    except (GAPI.invalidArgument, GAPI.failedPrecondition, GAPI.permissionDenied) as e:
      _getMain().entityActionFailedWarning([Ent.USER, user, Ent.VACATION_ENABLED, oldBody['enableAutoReply']], str(e), i, count)
    except GAPI.serviceNotAvailable:
      _getMain().userGmailServiceNotEnabledWarning(user, i, count)

# gam <UserTypeEntity> print vacation [compact] [enabledonly] [todrive <ToDriveAttribute>*]
# gam <UserTypeEntity> show vacation [compact|format|html] [enabledonly]
def printShowVacation(users):
  def _printVacation(user, result, showDisabled):
    enabled = result['enableAutoReply']
    if not enabled and not showDisabled:
      return
    row = {'User': user, 'enabled': enabled}
    row['contactsonly'] = result['restrictToContacts']
    row['domainonly'] = result['restrictToDomain']
    if 'startTime' in result:
      row['startdate'] = _getMain().formatLocalDatestamp(result['startTime'])
    elif enabled:
      row['startdate'] = VACATION_START_STARTED
    if 'endTime' in result:
      row['enddate'] = _getMain().formatLocalDatestamp(result['endTime'])
    elif enabled:
      row['enddate'] = VACATION_END_NOT_SPECIFIED
    row['subject'] = result.get('responseSubject', 'None')
    if result.get('responseBodyPlainText'):
      row['html'] = False
      row['message'] = _getMain().escapeCRsNLs(result['responseBodyPlainText'])
    elif result.get('responseBodyHtml'):
      row['html'] = True
      if sigReplyFormat == SIG_REPLY_HTML:
        row['message'] = _getMain().escapeCRsNLs(result['responseBodyHtml'])
      else:
        row['message'] = result['responseBodyHtml'].replace('\r', '').replace('\n', '')
    else:
      row['html'] = False
      row['message'] = 'None'
    csvPF.WriteRow(row)

  csvPF = _getMain().CSVPrintFile(['User', 'enabled', 'contactsonly', 'domainonly',
                        'startdate', 'enddate', 'subject', 'html', 'message']) if Act.csvFormat() else None
  showDisabled = True
  sigReplyFormat = SIG_REPLY_HTML
  while Cmd.ArgumentsRemaining():
    myarg = _getMain().getArgument()
    if csvPF and myarg == 'todrive':
      csvPF.GetTodriveParameters()
    elif (not csvPF and myarg in SIG_REPLY_OPTIONS_MAP) or (csvPF and myarg == 'compact'):
      sigReplyFormat = SIG_REPLY_OPTIONS_MAP[myarg]
    elif myarg == 'enabledonly':
      showDisabled = False
    else:
      _getMain().unknownArgumentExit()
  i, count, users = _getMain().getEntityArgument(users)
  for user in users:
    i += 1
    user, gmail = _getMain().buildGAPIServiceObject(API.GMAIL, user, i, count)
    if not gmail:
      continue
    if csvPF:
      _getMain().printGettingEntityItemForWhom(Ent.VACATION, user, i, count)
    try:
      result = _getMain().callGAPI(gmail.users().settings(), 'getVacation',
                        throwReasons=GAPI.GMAIL_THROW_REASONS,
                        userId='me')
      if not csvPF:
        _showVacation(user, i, count, result, showDisabled, sigReplyFormat)
      else:
        _printVacation(user, result, showDisabled)
    except GAPI.serviceNotAvailable:
      _getMain().userGmailServiceNotEnabledWarning(user, i, count)
  if csvPF:
    csvPF.writeCSVfile('Vacation')

