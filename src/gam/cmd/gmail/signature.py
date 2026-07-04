"""Gmail signature and vacation settings.

Part of the _gmail_monolith sub-package."""

"""GAM Gmail management: labels, messages, filters, forwarding, sendas, S/MIME, CSE, vacation."""


from gam.cmd.gmail.settings import _processSendAs, _processSignature, getSendAsAttributes

from gamlib import api as API
from gamlib import gapi as GAPI
from gam.util.svcacct import buildGAPIServiceObject
from gam.util.api_call import callGAPI
from gam.util.output import formatLocalDatestamp
from gam.util.args import (
    FALSE_VALUES,
    SORF_MSG_FILE_ARGUMENTS,
    TRUE_VALUES,
    escapeCRsNLs,
    getArgument,
    getBoolean,
    getString,
    getStringOrFile,
    getYYYYMMDD,
)
from gam.util.csv_pf import CSVPrintFile
from gam.util.display import (
    entityActionFailedWarning,
    printEntity,
    printGettingEntityItemForWhom,
    printKeyValueList,
    userGmailServiceNotEnabledWarning,
)
from gam.util.entity import getEntityArgument
from gam.util.errors import unknownArgumentExit
from gam.util.html import dehtml
from gam.util.tags import (
    _getTagReplacement,
    _getTagReplacementFieldValues,
    _initTagReplacements,
    _processTagReplacements,
)

from gam.var import Act, Cmd, Ent, Ind

def setSignature(users):
  tagReplacements = _initTagReplacements()
  signature, _, html = getStringOrFile('sig')
  body = {}
  primary = False
  while Cmd.ArgumentsRemaining():
    myarg = getArgument()
    if myarg == 'primary':
      primary = True
    elif myarg == 'html':
      html = getBoolean()
    else:
      getSendAsAttributes(myarg, body, tagReplacements)
  if not tagReplacements['subs']:
    body['signature'] = _processSignature(tagReplacements, signature, html)
  i, count, users = getEntityArgument(users)
  for user in users:
    i += 1
    user, gmail = buildGAPIServiceObject(API.GMAIL, user, i, count)
    if not gmail:
      continue
    if tagReplacements['subs']:
      _getTagReplacementFieldValues(user, i, count, tagReplacements)
      body['signature'] = _processSignature(tagReplacements, signature, html)
    if primary:
      try:
        result = callGAPI(gmail.users().settings().sendAs(), 'list',
                          throwReasons=GAPI.GMAIL_THROW_REASONS,
                          userId='me')
        for sendas in result['sendAs']:
          if sendas.get('isPrimary', False):
            emailAddress = sendas['sendAsEmail']
            _processSendAs(user, i, count, Ent.SIGNATURE, emailAddress, i, count, gmail, 'patch', False, body=body, sendAsEmail=emailAddress, fields='')
            break
      except GAPI.serviceNotAvailable:
        userGmailServiceNotEnabledWarning(user, i, count)
    else:
      _processSendAs(user, i, count, Ent.SIGNATURE, user, i, count, gmail, 'patch', False, body=body, sendAsEmail=user, fields='')

VACATION_START_STARTED = 'Started'
VACATION_END_NOT_SPECIFIED = 'NotSpecified'

def _showVacation(user, i, count, result, showDisabled, sigReplyFormat):
  enabled = result['enableAutoReply']
  if not enabled and not showDisabled:
    return
  printEntity([Ent.USER, user, Ent.VACATION, None], i, count)
  Ind.Increment()
  printKeyValueList(['Enabled', enabled])
  printKeyValueList(['Contacts Only', result['restrictToContacts']])
  printKeyValueList(['Domain Only', result['restrictToDomain']])
  if 'startTime' in result:
    printKeyValueList(['Start Date', formatLocalDatestamp(result['startTime'])])
  elif enabled:
    printKeyValueList(['Start Date', VACATION_START_STARTED])
  if 'endTime' in result:
    printKeyValueList(['End Date', formatLocalDatestamp(result['endTime'])])
  elif enabled:
    printKeyValueList(['End Date', VACATION_END_NOT_SPECIFIED])
  printKeyValueList(['Subject', result.get('responseSubject', 'None')])
  if sigReplyFormat == SIG_REPLY_HTML:
    printKeyValueList(['Message', None])
    Ind.Increment()
    if result.get('responseBodyPlainText'):
      printKeyValueList([Ind.MultiLineText(result['responseBodyPlainText'])])
    elif result.get('responseBodyHtml'):
      printKeyValueList([Ind.MultiLineText(result['responseBodyHtml'])])
    else:
      printKeyValueList(['None'])
    Ind.Decrement()
  elif sigReplyFormat == SIG_REPLY_FORMAT:
    printKeyValueList(['Message', None])
    Ind.Increment()
    if result.get('responseBodyPlainText'):
      printKeyValueList([Ind.MultiLineText(result['responseBodyPlainText'])])
    elif result.get('responseBodyHtml'):
      printKeyValueList([Ind.MultiLineText(dehtml(result['responseBodyHtml']))])
    else:
      printKeyValueList(['None'])
    Ind.Decrement()
  else: # SIG_REPLY_COMPACT
    if result.get('responseBodyPlainText'):
      printKeyValueList(['Message', escapeCRsNLs(result['responseBodyPlainText'])])
    elif result.get('responseBodyHtml'):
      printKeyValueList(['Message', escapeCRsNLs(result['responseBodyHtml'])])
    else:
      printKeyValueList(['Message', 'None'])
  Ind.Decrement()

# gam <UserTypeEntity> vacation [<Boolean>] [subject <String>]
#	[<VacationMessageContent>
#	    (replace <Tag> <UserReplacement>)*
#	    (replaceregex <REMatchPattern> <RESubstitution> <Tag> <UserReplacement>)*]
#	[html [<Boolean>]] [contactsonly [<Boolean>]] [domainonly [<Boolean>]]
#	[start|startdate <Date>|Started] [end|enddate <Date>|NotSpecified]
def setVacation(users):
  body = {}
  if Cmd.PeekArgumentPresent(TRUE_VALUES) or Cmd.PeekArgumentPresent(FALSE_VALUES):
    body['enableAutoReply'] = getBoolean(None)
  responseBodyType = 'responseBodyPlainText'
  message = subject = None
  tagReplacements = _initTagReplacements()
  while Cmd.ArgumentsRemaining():
    myarg = getArgument()
    if myarg == 'subject':
      subject = getString(Cmd.OB_STRING, minLen=0)
    elif myarg in SORF_MSG_FILE_ARGUMENTS:
      message, _, html = getStringOrFile(myarg)
      if html:
        responseBodyType = 'responseBodyHtml'
    elif _getTagReplacement(myarg, tagReplacements, True):
      pass
    elif myarg == 'html':
      if getBoolean():
        responseBodyType = 'responseBodyHtml'
    elif myarg == 'contactsonly':
      body['restrictToContacts'] = getBoolean()
    elif myarg == 'domainonly':
      body['restrictToDomain'] = getBoolean()
    elif myarg in {'start', 'startdate'}:
      body['startTime'] = getYYYYMMDD(returnTimeStamp=True, alternateValue=VACATION_START_STARTED)
    elif myarg in {'end', 'enddate'}:
      body['endTime'] = getYYYYMMDD(returnTimeStamp=True, alternateValue=VACATION_END_NOT_SPECIFIED)
    else:
      unknownArgumentExit()
  if message:
    if responseBodyType == 'responseBodyHtml':
      message = message.replace('\r', '').replace('\\n', '<br/>')
    else:
      message = message.replace('\r', '').replace('\\n', '\n')
    if tagReplacements['tags'] and not tagReplacements['subs']:
      message = _processTagReplacements(tagReplacements, message)
    body[responseBodyType] = message
  if subject:
    if tagReplacements['tags'] and not tagReplacements['subs']:
      subject = _processTagReplacements(tagReplacements, subject)
    body['responseSubject'] = subject
  i, count, users = getEntityArgument(users)
  for user in users:
    i += 1
    user, gmail = buildGAPIServiceObject(API.GMAIL, user, i, count)
    if not gmail:
      continue
    if (message or subject) and tagReplacements['subs']:
      _getTagReplacementFieldValues(user, i, count, tagReplacements)
      if message:
        body[responseBodyType] = _processTagReplacements(tagReplacements, message)
      if subject:
        body['responseSubject'] = _processTagReplacements(tagReplacements, subject)
    try:
      oldBody = callGAPI(gmail.users().settings(), 'getVacation',
                         throwReasons=GAPI.GMAIL_THROW_REASONS,
                         userId='me')
      if body.get(responseBodyType):
        oldBody.pop('responseBodyPlainText', None)
        oldBody.pop('responseBodyHtml', None)
      oldBody.update(body)
      result = callGAPI(gmail.users().settings(), 'updateVacation',
                        throwReasons=GAPI.GMAIL_THROW_REASONS+[GAPI.INVALID_ARGUMENT,
                                                               GAPI.FAILED_PRECONDITION, GAPI.PERMISSION_DENIED],
                        userId='me', body=oldBody)
      printEntity([Ent.USER, user, Ent.VACATION_ENABLED, result['enableAutoReply']], i, count)
    except (GAPI.invalidArgument, GAPI.failedPrecondition, GAPI.permissionDenied) as e:
      entityActionFailedWarning([Ent.USER, user, Ent.VACATION_ENABLED, oldBody['enableAutoReply']], str(e), i, count)
    except GAPI.serviceNotAvailable:
      userGmailServiceNotEnabledWarning(user, i, count)

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
      row['startdate'] = formatLocalDatestamp(result['startTime'])
    elif enabled:
      row['startdate'] = VACATION_START_STARTED
    if 'endTime' in result:
      row['enddate'] = formatLocalDatestamp(result['endTime'])
    elif enabled:
      row['enddate'] = VACATION_END_NOT_SPECIFIED
    row['subject'] = result.get('responseSubject', 'None')
    if result.get('responseBodyPlainText'):
      row['html'] = False
      row['message'] = escapeCRsNLs(result['responseBodyPlainText'])
    elif result.get('responseBodyHtml'):
      row['html'] = True
      if sigReplyFormat == SIG_REPLY_HTML:
        row['message'] = escapeCRsNLs(result['responseBodyHtml'])
      else:
        row['message'] = result['responseBodyHtml'].replace('\r', '').replace('\n', '')
    else:
      row['html'] = False
      row['message'] = 'None'
    csvPF.WriteRow(row)

  csvPF = CSVPrintFile(['User', 'enabled', 'contactsonly', 'domainonly',
                        'startdate', 'enddate', 'subject', 'html', 'message']) if Act.csvFormat() else None
  showDisabled = True
  sigReplyFormat = SIG_REPLY_HTML
  while Cmd.ArgumentsRemaining():
    myarg = getArgument()
    if csvPF and myarg == 'todrive':
      csvPF.GetTodriveParameters()
    elif (not csvPF and myarg in SIG_REPLY_OPTIONS_MAP) or (csvPF and myarg == 'compact'):
      sigReplyFormat = SIG_REPLY_OPTIONS_MAP[myarg]
    elif myarg == 'enabledonly':
      showDisabled = False
    else:
      unknownArgumentExit()
  i, count, users = getEntityArgument(users)
  for user in users:
    i += 1
    user, gmail = buildGAPIServiceObject(API.GMAIL, user, i, count)
    if not gmail:
      continue
    if csvPF:
      printGettingEntityItemForWhom(Ent.VACATION, user, i, count)
    try:
      result = callGAPI(gmail.users().settings(), 'getVacation',
                        throwReasons=GAPI.GMAIL_THROW_REASONS,
                        userId='me')
      if not csvPF:
        _showVacation(user, i, count, result, showDisabled, sigReplyFormat)
      else:
        _printVacation(user, result, showDisabled)
    except GAPI.serviceNotAvailable:
      userGmailServiceNotEnabledWarning(user, i, count)
  if csvPF:
    csvPF.writeCSVfile('Vacation')

