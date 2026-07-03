"""Gmail settings: forwarding, IMAP, POP, language, sendas.

Part of the _gmail_monolith sub-package."""

"""GAM Gmail management: labels, messages, filters, forwarding, sendas, S/MIME, CSE, vacation."""

import re
import sys

from gam.cmd.gmail.messages import forwardMessagesThreads

from gamlib import glaction
from gamlib import glapi as API
from gamlib import glcfg as GC
from gamlib import glclargs
from gamlib import glentity
from gamlib import glgapi as GAPI
from gamlib import glglobals as GM
from gamlib import glindent
from gamlib import glmsgs as Msg
from gam.util.api import buildGAPIServiceObject, callGAPI, callGAPIitems
from gam.util.args import (
    LANGUAGE_CODES_MAP,
    SORF_SIG_FILE_ARGUMENTS,
    checkArgumentPresent,
    checkForExtraneousArguments,
    escapeCRsNLs,
    getArgument,
    getBoolean,
    getChoice,
    getLanguageCode,
    getString,
    getStringOrFile,
    normalizeEmailAddressOrUID,
)
from gam.util.csv_pf import CSVPrintFile, flattenJSON, getTodriveOnly
from gam.util.display import (
    entityActionFailedWarning,
    entityActionPerformed,
    entityPerformActionNumItems,
    printEntity,
    printEntityKVList,
    printGettingEntityItemForWhom,
    printKeyValueList,
    userGmailServiceNotEnabledWarning,
)
from gam.util.entity import _validateUserGetObjectList, getEntityArgument, getUserObjectEntity
from gam.util.errors import missingArgumentExit, missingChoiceExit, unknownArgumentExit
from gam.util.html import dehtml
from gam.util.output import writeStdout

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

def _showForward(user, i, count, result):
  if 'enabled' in result:
    enabled = result['enabled']
    kvList = [Ent.Singular(Ent.FORWARD_ENABLED), enabled]
    if enabled:
      kvList += [Ent.Singular(Ent.FORWARDING_ADDRESS), result['emailAddress']]
      kvList += [Ent.Singular(Ent.ACTION), result['disposition']]
  else:
    enabled = result['enable'] == 'true'
    kvList = [Ent.Singular(Ent.FORWARD_ENABLED), enabled]
    if enabled:
      kvList += [Ent.Singular(Ent.FORWARDING_ADDRESS), result['forwardTo']]
      kvList += [Ent.Singular(Ent.ACTION), EMAILSETTINGS_OLD_NEW_OLD_FORWARD_ACTION_MAP[result['action']]]
  printEntityKVList([Ent.USER, user], kvList, i, count)

EMAILSETTINGS_FORWARD_POP_ACTION_CHOICE_MAP = {
  'archive': 'archive',
  'delete': 'trash',
  'keep': 'leaveInInbox',
  'leaveininbox': 'leaveInInbox',
  'markread': 'markRead',
  'trash': 'trash',
  }

# gam <UserTypeEntity> forward <FalseValues>
# gam <UserTypeEntity> forward <TrueValues> keep|leaveininbox|archive|delete|trash|markread <EmailAddress>
def setForward(users):
  if checkArgumentPresent([Cmd.ARG_MESSAGE, Cmd.ARG_MESSAGES]):
    Act.Set(Act.FORWARD)
    forwardMessagesThreads(users, Ent.MESSAGE)
    return
  if checkArgumentPresent([Cmd.ARG_THREAD, Cmd.ARG_THREADS]):
    Act.Set(Act.FORWARD)
    forwardMessagesThreads(users, Ent.THREAD)
    return
  enable = getBoolean(None)
  body = {'enabled': enable}
  if enable:
    while Cmd.ArgumentsRemaining():
      myarg = getArgument()
      if myarg in EMAILSETTINGS_FORWARD_POP_ACTION_CHOICE_MAP:
        body['disposition'] = EMAILSETTINGS_FORWARD_POP_ACTION_CHOICE_MAP[myarg]
      elif myarg == 'confirm':
        pass
      elif myarg.find('@') != -1 or (not Cmd.ArgumentsRemaining() and 'emailAddress' not in body):
        body['emailAddress'] = normalizeEmailAddressOrUID(Cmd.Previous())
      else:
        unknownArgumentExit()
    if not body.get('disposition'):
      missingChoiceExit(EMAILSETTINGS_FORWARD_POP_ACTION_CHOICE_MAP)
    if not body.get('emailAddress'):
      missingArgumentExit(Cmd.OB_EMAIL_ADDRESS)
  i, count, users = getEntityArgument(users)
  for user in users:
    i += 1
    user, gmail = buildGAPIServiceObject(API.GMAIL, user, i, count)
    if not gmail:
      continue
    try:
      result = callGAPI(gmail.users().settings(), 'updateAutoForwarding',
                        throwReasons=GAPI.GMAIL_THROW_REASONS+[GAPI.INVALID, GAPI.FAILED_PRECONDITION, GAPI.PERMISSION_DENIED],
                        userId='me', body=body)
      _showForward(user, i, count, result)
    except (GAPI.invalid, GAPI.failedPrecondition, GAPI.permissionDenied) as e:
      if enable:
        entityActionFailedWarning([Ent.USER, user, Ent.FORWARDING_ADDRESS, body['emailAddress']], str(e), i, count)
      else:
        entityActionFailedWarning([Ent.USER, user], str(e), i, count)
    except GAPI.serviceNotAvailable:
      userGmailServiceNotEnabledWarning(user, i, count)

# gam <UserTypeEntity> print forward [enabledonly] [todrive <ToDriveAttribute>*]
# gam <UserTypeEntity> show forward
def printShowForward(users):
  def _printForward(user, result, showDisabled):
    if 'enabled' in result:
      enabled = result['enabled']
      if not enabled and not showDisabled:
        return
      row = {'User': user, 'forwardEnabled': enabled}
      if enabled:
        row['forwardTo'] = result['emailAddress']
        row['disposition'] = result['disposition']
    else:
      enabled = result['enable'] == 'true'
      if not enabled and not showDisabled:
        return
      row = {'User': user, 'forwardEnabled': enabled}
      if enabled:
        row['forwardTo'] = result['forwardTo']
        row['disposition'] = EMAILSETTINGS_OLD_NEW_OLD_FORWARD_ACTION_MAP[result['action']]
    csvPF.WriteRow(row)

  csvPF = CSVPrintFile(['User', 'forwardEnabled', 'forwardTo', 'disposition']) if Act.csvFormat() else None
  showDisabled = True
  while Cmd.ArgumentsRemaining():
    myarg = getArgument()
    if csvPF and myarg == 'todrive':
      csvPF.GetTodriveParameters()
    elif csvPF and myarg == 'enabledonly':
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
      printGettingEntityItemForWhom(Ent.FORWARD_ENABLED, user, i, count)
    try:
      result = callGAPI(gmail.users().settings(), 'getAutoForwarding',
                        throwReasons=GAPI.GMAIL_THROW_REASONS+[GAPI.FAILED_PRECONDITION],
                        userId='me')
      if not csvPF:
        _showForward(user, i, count, result)
      else:
        _printForward(user, result, showDisabled)
    except GAPI.failedPrecondition as e:
      entityActionFailedWarning([Ent.USER, user], str(e), i, count)
    except GAPI.serviceNotAvailable:
      userGmailServiceNotEnabledWarning(user, i, count)
  if csvPF:
    csvPF.writeCSVfile('Forward')

# Process ForwardingAddresses functions
def _showForwardingAddress(j, jcount, result):
  printEntityKVList([Ent.FORWARDING_ADDRESS, result['forwardingEmail']], ['Verification Status', result['verificationStatus']], j, jcount)

def _processForwardingAddress(user, i, count, emailAddress, j, jcount, gmail, function, **kwargs):
  userDefined = True
  try:
    result = callGAPI(gmail.users().settings().forwardingAddresses(), function,
                      throwReasons=GAPI.GMAIL_THROW_REASONS+[GAPI.NOT_FOUND, GAPI.ALREADY_EXISTS, GAPI.DUPLICATE,
                                                             GAPI.INVALID_ARGUMENT, GAPI.FAILED_PRECONDITION, GAPI.PERMISSION_DENIED],
                      userId='me', **kwargs)
    if function == 'get':
      _showForwardingAddress(j, count, result)
    else:
      entityActionPerformed([Ent.USER, user, Ent.FORWARDING_ADDRESS, emailAddress], j, jcount)
  except (GAPI.notFound, GAPI.alreadyExists, GAPI.duplicate, GAPI.invalidArgument, GAPI.failedPrecondition, GAPI.permissionDenied) as e:
    entityActionFailedWarning([Ent.USER, user, Ent.FORWARDING_ADDRESS, emailAddress], str(e), j, jcount)
  except GAPI.serviceNotAvailable:
    userGmailServiceNotEnabledWarning(user, i, count)
    userDefined = False
  return userDefined

# gam <UserTypeEntity> create forwardingaddresses <EmailAddressEntity>
def createForwardingAddresses(users):
  emailAddressEntity = getUserObjectEntity(Cmd.OB_EMAIL_ADDRESS_ENTITY, Ent.FORWARDING_ADDRESS)
  checkForExtraneousArguments()
  i, count, users = getEntityArgument(users)
  for user in users:
    i += 1
    user, gmail, emailAddresses, jcount = _validateUserGetObjectList(user, i, count, emailAddressEntity)
    if jcount == 0:
      continue
    Ind.Increment()
    j = 0
    for emailAddress in emailAddresses:
      j += 1
      emailAddress = normalizeEmailAddressOrUID(emailAddress, noUid=True)
      body = {'forwardingEmail': emailAddress}
      if not _processForwardingAddress(user, i, count, emailAddress, j, jcount, gmail, 'create', body=body, fields=''):
        break
    Ind.Decrement()

def _deleteInfoForwardingAddreses(users, function):
  emailAddressEntity = getUserObjectEntity(Cmd.OB_EMAIL_ADDRESS_ENTITY, Ent.FORWARDING_ADDRESS)
  checkForExtraneousArguments()
  i, count, users = getEntityArgument(users)
  for user in users:
    i += 1
    user, gmail, emailAddresses, jcount = _validateUserGetObjectList(user, i, count, emailAddressEntity)
    if jcount == 0:
      continue
    Ind.Increment()
    j = 0
    for emailAddress in emailAddresses:
      j += 1
      emailAddress = normalizeEmailAddressOrUID(emailAddress, noUid=True)
      if not _processForwardingAddress(user, i, count, emailAddress, j, jcount, gmail, function, forwardingEmail=emailAddress):
        break
    Ind.Decrement()

# gam <UserTypeEntity> delete forwardingaddresses <EmailAddressEntity>
def deleteForwardingAddresses(users):
  _deleteInfoForwardingAddreses(users, 'delete')

# gam <UserTypeEntity> info forwardingaddresses <EmailAddressEntity>
def infoForwardingAddresses(users):
  _deleteInfoForwardingAddreses(users, 'get')

# gam <UserTypeEntity> print forwardingaddresses [todrive <ToDriveAttribute>*]
# gam <UserTypeEntity> show forwardingaddresses
def printShowForwardingAddresses(users):
  csvPF = CSVPrintFile(['User', 'forwardingEmail', 'verificationStatus']) if Act.csvFormat() else None
  getTodriveOnly(csvPF)
  i, count, users = getEntityArgument(users)
  for user in users:
    i += 1
    user, gmail = buildGAPIServiceObject(API.GMAIL, user, i, count)
    if not gmail:
      continue
    if csvPF:
      printGettingEntityItemForWhom(Ent.FORWARDING_ADDRESS, user, i, count)
    try:
      results = callGAPIitems(gmail.users().settings().forwardingAddresses(), 'list', 'forwardingAddresses',
                              throwReasons=GAPI.GMAIL_THROW_REASONS+[GAPI.FAILED_PRECONDITION],
                              userId='me')
      if not csvPF:
        jcount = len(results)
        entityPerformActionNumItems([Ent.USER, user], jcount, Ent.FORWARDING_ADDRESS, i, count)
        Ind.Increment()
        j = 0
        for forward in results:
          j += 1
          _showForwardingAddress(j, jcount, forward)
        Ind.Decrement()
      elif results:
        for forward in results:
          csvPF.WriteRow({'User': user, 'forwardingEmail': forward['forwardingEmail'], 'verificationStatus': forward['verificationStatus']})
      elif GC.Values[GC.CSV_OUTPUT_USERS_AUDIT]:
        csvPF.WriteRowNoFilter({'User': user})
    except GAPI.failedPrecondition as e:
      entityActionFailedWarning([Ent.USER, user], str(e), i, count)
    except GAPI.serviceNotAvailable:
      userGmailServiceNotEnabledWarning(user, i, count)
  if csvPF:
    csvPF.writeCSVfile('Forwarding Addresses')

def _showImap(user, i, count, result):
  enabled = result['enabled']
  kvList = [Ent.Singular(Ent.IMAP_ENABLED), enabled]
  for item in result:
    if item != 'enabled':
      kvList += [item, result[item]]
  printEntityKVList([Ent.USER, user], kvList, i, count)
#
EMAILSETTINGS_IMAP_EXPUNGE_BEHAVIOR_CHOICE_MAP = {
  'archive': 'archive',
  'deleteforever': 'deleteForever',
  'trash': 'trash',
  }

EMAILSETTINGS_IMAP_MAX_FOLDER_SIZE_CHOICES = ['0', '1000', '2000', '5000', '10000']

def _imapDefaults(enable):
  return {'enabled': enable, 'autoExpunge': True, 'expungeBehavior': 'archive', 'maxFolderSize': 0}

def _setImap(user, body, i, count):
  user, gmail = buildGAPIServiceObject(API.GMAIL, user, i, count)
  if gmail:
    try:
      result = callGAPI(gmail.users().settings(), 'updateImap',
                        throwReasons=GAPI.GMAIL_THROW_REASONS+[GAPI.PERMISSION_DENIED],
                        userId='me', body=body)
      _showImap(user, i, count, result)
    except GAPI.permissionDenied as e:
      entityActionFailedWarning([Ent.USER, user], str(e), i, count)
    except GAPI.serviceNotAvailable:
      userGmailServiceNotEnabledWarning(user, i, count)

# gam <UserTypeEntity> imap|imap4 <Boolean> [noautoexpunge] [expungebehavior archive|deleteforever|trash] [maxfoldersize 0|1000|2000|5000|10000]
def setImap(users):
  body = _imapDefaults(getBoolean(None))
  while Cmd.ArgumentsRemaining():
    myarg = getArgument()
    if myarg == 'noautoexpunge':
      body['autoExpunge'] = False
    elif myarg == 'expungebehavior':
      body['expungeBehavior'] = getChoice(EMAILSETTINGS_IMAP_EXPUNGE_BEHAVIOR_CHOICE_MAP, mapChoice=True)
    elif myarg == 'maxfoldersize':
      body['maxFolderSize'] = int(getChoice(EMAILSETTINGS_IMAP_MAX_FOLDER_SIZE_CHOICES))
    else:
      unknownArgumentExit()
  i, count, users = getEntityArgument(users)
  for user in users:
    i += 1
    _setImap(user, body, i, count)

# gam <UserTypeEntity> print imap|imap4 [todrive <ToDriveAttribute>*]
# gam <UserTypeEntity> show imap|imap4
def printShowImap(users):
  csvPF = CSVPrintFile(['User', 'enabled']) if Act.csvFormat() else None
  getTodriveOnly(csvPF)
  i, count, users = getEntityArgument(users)
  for user in users:
    i += 1
    user, gmail = buildGAPIServiceObject(API.GMAIL, user, i, count)
    if not gmail:
      continue
    try:
      result = callGAPI(gmail.users().settings(), 'getImap',
                        throwReasons=GAPI.GMAIL_THROW_REASONS,
                        userId='me')
      if not csvPF:
        _showImap(user, i, count, result)
      else:
        csvPF.WriteRowTitles(flattenJSON(result, flattened={'User': user}))
    except GAPI.serviceNotAvailable:
      userGmailServiceNotEnabledWarning(user, i, count)
  if csvPF:
    csvPF.writeCSVfile('IMAP')

def _showPop(user, i, count, result):
  enabled = result['accessWindow'] != 'disabled'
  kvList = [Ent.Singular(Ent.POP_ENABLED), enabled]
  if enabled:
    kvList += ['For', result['accessWindow'], Ent.Singular(Ent.ACTION), result['disposition']]
  printEntityKVList([Ent.USER, user], kvList, i, count)
#
EMAILSETTINGS_POP_ENABLE_FOR_CHOICE_MAP = {
  'allmail': 'allMail',
  'fromnowon': 'fromNowOn',
  'mailfromnowon': 'fromNowOn',
  'newmail': 'fromNowOn',
  }

def _popDefaults(enable):
  return {'accessWindow': ['disabled', 'allMail'][enable], 'disposition': 'leaveInInbox'}

def _setPop(user, body, i, count):
  user, gmail = buildGAPIServiceObject(API.GMAIL, user, i, count)
  if gmail:
    try:
      result = callGAPI(gmail.users().settings(), 'updatePop',
                        throwReasons=GAPI.GMAIL_THROW_REASONS+[GAPI.PERMISSION_DENIED],
                        userId='me', body=body)
      _showPop(user, i, count, result)
    except GAPI.permissionDenied as e:
      entityActionFailedWarning([Ent.USER, user], str(e), i, count)
    except GAPI.serviceNotAvailable:
      userGmailServiceNotEnabledWarning(user, i, count)

# gam <UserTypeEntity> pop|pop3 <Boolean> [for allmail|newmail|mailfromnowon|fromnowown] [action keep|leaveininbox|archive|delete|trash|markread]
def setPop(users):
  body = _popDefaults(getBoolean(None))
  while Cmd.ArgumentsRemaining():
    myarg = getArgument()
    if myarg == 'for':
      body['accessWindow'] = getChoice(EMAILSETTINGS_POP_ENABLE_FOR_CHOICE_MAP, mapChoice=True)
    elif myarg == 'action':
      body['disposition'] = getChoice(EMAILSETTINGS_FORWARD_POP_ACTION_CHOICE_MAP, mapChoice=True)
    elif myarg == 'confirm':
      pass
    else:
      unknownArgumentExit()
  i, count, users = getEntityArgument(users)
  for user in users:
    i += 1
    _setPop(user, body, i, count)

# gam <UserTypeEntity> print pop|pop3 [todrive <ToDriveAttribute>*]
# gam <UserTypeEntity> show pop|pop3
def printShowPop(users):
  csvPF = CSVPrintFile(['User', 'enabled']) if Act.csvFormat() else None
  getTodriveOnly(csvPF)
  i, count, users = getEntityArgument(users)
  for user in users:
    i += 1
    user, gmail = buildGAPIServiceObject(API.GMAIL, user, i, count)
    if not gmail:
      continue
    try:
      result = callGAPI(gmail.users().settings(), 'getPop',
                        throwReasons=GAPI.GMAIL_THROW_REASONS,
                        userId='me')
      if not csvPF:
        _showPop(user, i, count, result)
      else:
        csvPF.WriteRowTitles(flattenJSON(result, flattened={'User': user, 'enabled': result['accessWindow'] != 'disabled'}))
    except GAPI.serviceNotAvailable:
      userGmailServiceNotEnabledWarning(user, i, count)
  if csvPF:
    csvPF.writeCSVfile('POP')

# gam <UserTypeEntity> language <Language>
def setLanguage(users):
  language = getLanguageCode(LANGUAGE_CODES_MAP)
  checkForExtraneousArguments()
  i, count, users = getEntityArgument(users)
  for user in users:
    i += 1
    user, gmail = buildGAPIServiceObject(API.GMAIL, user, i, count)
    if not gmail:
      continue
    try:
      result = callGAPI(gmail.users().settings(), 'updateLanguage',
                        throwReasons=GAPI.GMAIL_THROW_REASONS+[GAPI.PERMISSION_DENIED],
                        userId='me', body={'displayLanguage': language})
      entityActionPerformed([Ent.USER, user, Ent.LANGUAGE, result['displayLanguage']], i, count)
    except GAPI.permissionDenied as e:
      entityActionFailedWarning([Ent.USER, user], str(e), i, count)
    except GAPI.serviceNotAvailable:
      userGmailServiceNotEnabledWarning(user, i, count)

# gam <UserTypeEntity> print language [todrive <ToDriveAttribute>*]
# gam <UserTypeEntity> show language
def printShowLanguage(users):
  csvPF = CSVPrintFile(['User', 'displayLanguage']) if Act.csvFormat() else None
  getTodriveOnly(csvPF)
  i, count, users = getEntityArgument(users)
  for user in users:
    i += 1
    user, gmail = buildGAPIServiceObject(API.GMAIL, user, i, count)
    if not gmail:
      continue
    try:
      result = callGAPI(gmail.users().settings(), 'getLanguage',
                        throwReasons=GAPI.GMAIL_THROW_REASONS,
                        userId='me')
      if not csvPF:
        printEntity([Ent.USER, user, Ent.LANGUAGE, result['displayLanguage']], i, count)
      else:
        csvPF.WriteRowTitles(flattenJSON(result, flattened={'User': user}))
    except GAPI.serviceNotAvailable:
      userGmailServiceNotEnabledWarning(user, i, count)
  if csvPF:
    csvPF.writeCSVfile('Language')

SIG_REPLY_HTML = 0
SIG_REPLY_COMPACT = 1
SIG_REPLY_FORMAT = 2
SIG_REPLY_TEMPLATE = 3 # Does not go in MAP
SIG_REPLY_OPTIONS_MAP = {'html': SIG_REPLY_HTML, 'compact': SIG_REPLY_COMPACT, 'format': SIG_REPLY_FORMAT}
SMTPMSA_DISPLAY_FIELDS = ['host', 'port', 'securityMode']

def _showSendAs(result, j, jcount, sigReplyFormat, verifyOnly=False):
  if sigReplyFormat == SIG_REPLY_TEMPLATE:
    writeStdout(f"{escapeCRsNLs(result.get('signature', 'None'))}\n")
    return
  if result['displayName']:
    printEntity([Ent.SENDAS_ADDRESS, f'{result["displayName"]} <{result["sendAsEmail"]}>'], j, jcount)
  else:
    printEntity([Ent.SENDAS_ADDRESS, f'<{result["sendAsEmail"]}>'], j, jcount)
  Ind.Increment()
  if result.get('replyToAddress'):
    printKeyValueList(['ReplyTo', result['replyToAddress']])
  printKeyValueList(['IsPrimary', result.get('isPrimary', False)])
  printKeyValueList(['Default', result.get('isDefault', False)])
  if not result.get('isPrimary', False):
    printKeyValueList(['TreatAsAlias', result.get('treatAsAlias', False)])
  if 'smtpMsa' in result:
    for field in SMTPMSA_DISPLAY_FIELDS:
      if field in result['smtpMsa']:
        printKeyValueList([f'smtpMsa.{field}', result['smtpMsa'][field]])
  if 'verificationStatus' in result:
    printKeyValueList(['Verification Status', result['verificationStatus']])
  signature = result.get('signature')
  if verifyOnly:
    printKeyValueList(['Signature', bool(signature)])
  else:
    if not signature:
      signature = 'None'
    if sigReplyFormat == SIG_REPLY_HTML:
      printKeyValueList(['Signature', None])
      Ind.Increment()
      printKeyValueList([Ind.MultiLineText(signature)])
      Ind.Decrement()
    elif sigReplyFormat == SIG_REPLY_FORMAT:
      printKeyValueList(['Signature', None])
      Ind.Increment()
      printKeyValueList([Ind.MultiLineText(dehtml(signature))])
      Ind.Decrement()
    else: # SIG_REPLY_COMPACT
      printKeyValueList(['Signature', escapeCRsNLs(signature)])
  Ind.Decrement()

def _processSignature(tagReplacements, signature, html):
  if signature:
    signature = signature.replace('\r', '').replace('\\n', '<br/>')
    if tagReplacements['tags']:
      signature = _getMain()._processTagReplacements(tagReplacements, signature)
    if not html:
      signature = signature.replace('\n', '<br/>')
  return signature

# Process SendAs functions
def _processSendAs(user, i, count, entityType, emailAddress, j, jcount, gmail, function,
                   sigReplyFormat, verifyOnly=False, **kwargs):
  userDefined = True
  try:
    result = callGAPI(gmail.users().settings().sendAs(), function,
                      throwReasons=GAPI.GMAIL_THROW_REASONS+[GAPI.NOT_FOUND, GAPI.ALREADY_EXISTS, GAPI.DUPLICATE,
                                                             GAPI.CANNOT_DELETE_PRIMARY_SENDAS, GAPI.INVALID_ARGUMENT,
                                                             GAPI.FAILED_PRECONDITION, GAPI.PERMISSION_DENIED,
                                                             GAPI.INSUFFICIENT_PERMISSIONS],
                      userId='me', **kwargs)
    if function == 'get':
      _showSendAs(result, j, jcount, sigReplyFormat, verifyOnly)
    else:
      entityActionPerformed([Ent.USER, user, entityType, emailAddress], j, jcount)
  except (GAPI.notFound, GAPI.alreadyExists, GAPI.duplicate,
          GAPI.cannotDeletePrimarySendAs, GAPI.invalidArgument,
          GAPI.failedPrecondition, GAPI.permissionDenied, GAPI.insufficientPermissions) as e:
    entityActionFailedWarning([Ent.USER, user, entityType, emailAddress], str(e), j, jcount)
  except GAPI.serviceNotAvailable:
    userGmailServiceNotEnabledWarning(user, i, count)
    userDefined = False
  return userDefined

def getSendAsAttributes(myarg, body, tagReplacements):
  if _getMain()._getTagReplacement(myarg, tagReplacements, True):
    pass
  elif myarg == 'name':
    body['displayName'] = getString(Cmd.OB_NAME, minLen=0)
  elif myarg == 'replyto':
    body['replyToAddress'] = getString(Cmd.OB_EMAIL_ADDRESS, minLen=0)
    if len(body['replyToAddress']) > 0:
      body['replyToAddress'] = normalizeEmailAddressOrUID(body['replyToAddress'], noUid=True, noLower=True)
  elif myarg == 'default':
    body['isDefault'] = True
  elif myarg == 'treatasalias':
    body['treatAsAlias'] = getBoolean()
  else:
    unknownArgumentExit()

SMTPMSA_PORTS = ['25', '465', '587']
SMTPMSA_SECURITY_MODES = ['none', 'ssl', 'starttls']
SMTPMSA_REQUIRED_FIELDS = ['host', 'port', 'username', 'password']

# gam <UserTypeEntity> [create] sendas <EmailAddress> [name] <String>
#	[<SendAsContent>
#	    (replace <Tag> <UserReplacement>)*
#	    (replaceregex <REMatchPattern> <RESubstitution> <Tag> <UserReplacement>)*]
#	[html [<Boolean>]] [replyto <EmailAddress>] [default] [treatasalias <Boolean>]
#	[smtpmsa.host <SMTPHostName> smtpmsa.port 25|465|587
#	 smtpmsa.username <UserName> smtpmsa.password <Password>
#	 [smtpmsa.securitymode none|ssl|starttls]]
# gam <UserTypeEntity> update sendas <EmailAddress> [name <String>]
#	[<SendAsContent>
#	    (replace <Tag> <UserReplacement>)*
#	    (replaceregex <REMatchPattern> <RESubstitution> <Tag> <UserReplacement>)*]
#	[html [<Boolean>]] [replyto <EmailAddress>] [default] [treatasalias <Boolean>]
def createUpdateSendAs(users):
  updateCmd = Act.Get() == Act.UPDATE
  emailAddress = normalizeEmailAddressOrUID(getString(Cmd.OB_EMAIL_ADDRESS), noUid=True, noLower=True)
  if not updateCmd:
    body = {'sendAsEmail': emailAddress}
    checkArgumentPresent(['name'])
    body['displayName'] = getString(Cmd.OB_NAME)
  else:
    body = {}
  signature = None
  smtpMsa = {}
  tagReplacements = _getMain()._initTagReplacements()
  html = False
  while Cmd.ArgumentsRemaining():
    myarg = getArgument()
    if myarg in SORF_SIG_FILE_ARGUMENTS:
      signature, _, html = getStringOrFile(myarg)
    elif myarg == 'html':
      html = getBoolean()
    elif not updateCmd and myarg.startswith('smtpmsa.'):
      if myarg == 'smtpmsa.host':
        smtpMsa['host'] = getString(Cmd.OB_SMTP_HOST_NAME)
      elif myarg == 'smtpmsa.port':
        smtpMsa['port'] = int(getChoice(SMTPMSA_PORTS))
      elif myarg == 'smtpmsa.username':
        smtpMsa['username'] = getString(Cmd.OB_USER_NAME)
      elif myarg == 'smtpmsa.password':
        smtpMsa['password'] = getString(Cmd.OB_PASSWORD)
      elif myarg == 'smtpmsa.securitymode':
        smtpMsa['securityMode'] = getChoice(SMTPMSA_SECURITY_MODES)
      else:
        unknownArgumentExit()
    else:
      getSendAsAttributes(myarg, body, tagReplacements)
  if signature is not None and not tagReplacements['subs']:
    body['signature'] = _processSignature(tagReplacements, signature, html)
  if smtpMsa:
    for field in SMTPMSA_REQUIRED_FIELDS:
      if field not in smtpMsa:
        missingArgumentExit(f'smtpmsa.{field}')
    body['smtpMsa'] = smtpMsa
  kwargs = {'body': body, 'fields': ''}
  if updateCmd:
    kwargs['sendAsEmail'] = emailAddress
  i, count, users = getEntityArgument(users)
  for user in users:
    i += 1
    user, gmail = buildGAPIServiceObject(API.GMAIL, user, i, count)
    if not gmail:
      continue
    if signature is not None and tagReplacements['subs']:
      _getMain()._getTagReplacementFieldValues(user, i, count, tagReplacements)
      kwargs['body']['signature'] = _processSignature(tagReplacements, signature, html)
    _processSendAs(user, i, count, Ent.SENDAS_ADDRESS, emailAddress, i, count, gmail, ['create', 'patch'][updateCmd], False, **kwargs)

# gam <UserTypeEntity> delete sendas <EmailAddressEntity>
# gam <UserTypeEntity> info sendas <EmailAddressEntity> [compact|format|html]
def deleteInfoSendAs(users):
  function = 'delete' if Act.Get() == Act.DELETE else 'get'
  emailAddressEntity = getUserObjectEntity(Cmd.OB_EMAIL_ADDRESS_ENTITY, Ent.SENDAS_ADDRESS)
  sigReplyFormat = SIG_REPLY_HTML
  if function == 'get':
    while Cmd.ArgumentsRemaining():
      myarg = getArgument()
      if myarg in SIG_REPLY_OPTIONS_MAP:
        sigReplyFormat = SIG_REPLY_OPTIONS_MAP[myarg]
      else:
        unknownArgumentExit()
  else:
    checkForExtraneousArguments()
  i, count, users = getEntityArgument(users)
  for user in users:
    i += 1
    user, gmail, emailAddresses, jcount = _validateUserGetObjectList(user, i, count, emailAddressEntity)
    if jcount == 0:
      continue
    Ind.Increment()
    j = 0
    for emailAddress in emailAddresses:
      j += 1
      emailAddress = normalizeEmailAddressOrUID(emailAddress, noUid=True)
      if not _processSendAs(user, i, count, Ent.SENDAS_ADDRESS, emailAddress, j, jcount, gmail, function, sigReplyFormat, sendAsEmail=emailAddress):
        break
    Ind.Decrement()

# gam <UserTypeEntity> print sendas [compact]
#	[primary|default] [verifyonly] [todrive <ToDriveAttribute>*]
# gam <UserTypeEntity> show sendas [compact|format|html]
#	[primary|default] [verifyonly]
def printShowSendAs(users):
  csvPF = CSVPrintFile(['User', 'displayName', 'sendAsEmail', 'replyToAddress',
                        'isPrimary', 'isDefault', 'treatAsAlias', 'verificationStatus'],
                       'sortall') if Act.csvFormat() else None
  sigReplyFormat = SIG_REPLY_HTML
  selection=None
  verifyOnly = False
  while Cmd.ArgumentsRemaining():
    myarg = getArgument()
    if csvPF and myarg == 'todrive':
      csvPF.GetTodriveParameters()
    elif myarg == 'primary':
      selection = 'isPrimary'
    elif myarg == 'default':
      selection = 'isDefault'
    elif myarg == 'verifyonly':
      verifyOnly = True
    elif (not csvPF and myarg in SIG_REPLY_OPTIONS_MAP) or (csvPF and myarg == 'compact'):
      sigReplyFormat = SIG_REPLY_OPTIONS_MAP[myarg]
    else:
      unknownArgumentExit()
  i, count, users = getEntityArgument(users)
  for user in users:
    i += 1
    user, gmail = buildGAPIServiceObject(API.GMAIL, user, i, count)
    if not gmail:
      continue
    if csvPF:
      printGettingEntityItemForWhom(Ent.SENDAS_ADDRESS, user, i, count)
    try:
      results = callGAPIitems(gmail.users().settings().sendAs(), 'list', 'sendAs',
                              throwReasons=GAPI.GMAIL_THROW_REASONS,
                              userId='me')
      if not csvPF:
        jcount = len(results)
        entityPerformActionNumItems([Ent.USER, user], jcount if selection is None else 1, Ent.SENDAS_ADDRESS, i, count)
        Ind.Increment()
        j = 0
        for sendas in results:
          j += 1
          if (selection is None) or (sendas.get(selection, False)):
            _showSendAs(sendas, j, jcount, sigReplyFormat, verifyOnly)
        Ind.Decrement()
      elif results:
        for sendas in results:
          if (selection is None) or (sendas.get(selection, False)):
            row = {'User': user, 'isPrimary': False}
            for item in sendas:
              if item != 'smtpMsa':
                if item == 'signature':
                  if verifyOnly:
                    row[item] = bool(sendas[item])
                  elif sigReplyFormat != SIG_REPLY_COMPACT:
                    row[item] = sendas[item]
                  else:
                    row[item] = sendas[item].replace('\r', '').replace('\n', '')
                else:
                  row[item] = sendas[item]
              else:
                for field in SMTPMSA_DISPLAY_FIELDS:
                  if field in sendas[item]:
                    row[f'smtpMsa{GC.Values[GC.CSV_OUTPUT_SUBFIELD_DELIMITER]}{field}'] = sendas[item][field]
            csvPF.WriteRowTitles(row)
      elif GC.Values[GC.CSV_OUTPUT_USERS_AUDIT]:
        csvPF.WriteRowNoFilter({'User': user})
    except GAPI.serviceNotAvailable:
      userGmailServiceNotEnabledWarning(user, i, count)
  if csvPF:
    csvPF.writeCSVfile('SendAs')

# gam <UserTypeEntity> print signature [compact]
#	[primary] [verifyonly] [todrive <ToDriveAttribute>*]
# gam <UserTypeEntity> show signature|sig [compact|format|html|template]
#	[primary] [verifyonly]
def printShowSignature(users):
  csvPF = CSVPrintFile(['User', 'displayName', 'sendAsEmail', 'replyToAddress',
                        'isPrimary', 'isDefault', 'treatAsAlias', 'verificationStatus'],
                       'sortall') if Act.csvFormat() else None
  sigReplyFormat = SIG_REPLY_HTML
  selection = None
  verifyOnly = False
  while Cmd.ArgumentsRemaining():
    myarg = getArgument()
    if csvPF and myarg == 'todrive':
      csvPF.GetTodriveParameters()
    elif myarg == 'primary':
      selection = 'isPrimary'
    elif myarg == 'default':
      selection = 'isDefault'
    elif myarg == 'verifyonly':
      verifyOnly = True
    elif (not csvPF and myarg in SIG_REPLY_OPTIONS_MAP) or (csvPF and myarg == 'compact'):
      sigReplyFormat = SIG_REPLY_OPTIONS_MAP[myarg]
    elif not csvPF and myarg == 'template':
      sigReplyFormat = SIG_REPLY_TEMPLATE
    else:
      unknownArgumentExit()
  i, count, users = getEntityArgument(users)
  for user in users:
    i += 1
    user, gmail = buildGAPIServiceObject(API.GMAIL, user, i, count)
    if not gmail:
      continue
    if csvPF:
      printGettingEntityItemForWhom(Ent.SIGNATURE, user, i, count)
    try:
      if selection is None:
        sendas = callGAPI(gmail.users().settings().sendAs(), 'get',
                          throwReasons=GAPI.GMAIL_THROW_REASONS+[GAPI.NOT_FOUND],
                          userId='me', sendAsEmail=user)
      else:
        results = callGAPIitems(gmail.users().settings().sendAs(), 'list', 'sendAs',
                                throwReasons=GAPI.GMAIL_THROW_REASONS,
                                userId='me')
        for sendas in results:
          if sendas.get(selection, False):
            break
      if not csvPF:
        _showSendAs(sendas, 0, 0, sigReplyFormat, verifyOnly)
      else:
        row = {'User': user, 'isPrimary': False}
        for item in sendas:
          if item != 'smtpMsa':
            if item == 'signature':
              if verifyOnly:
                row[item] = bool(sendas[item])
              elif sigReplyFormat != SIG_REPLY_COMPACT:
                row[item] = sendas[item]
              else:
                row[item] = sendas[item].replace('\r', '').replace('\n', '')
            else:
              row[item] = sendas[item]
          else:
            for field in SMTPMSA_DISPLAY_FIELDS:
              if field in sendas[item]:
                row[f'smtpMsa{GC.Values[GC.CSV_OUTPUT_SUBFIELD_DELIMITER]}{field}'] = sendas[item][field]
        csvPF.WriteRowTitles(row)
    except GAPI.notFound as e:
      entityActionFailedWarning([Ent.USER, user], str(e), i, count)
    except GAPI.serviceNotAvailable:
      userGmailServiceNotEnabledWarning(user, i, count)
  if csvPF:
    csvPF.writeCSVfile('Signature')

# gam <UserTypeEntity> create smime file <FileName> [password <Password>]
#	[sendas|sendasemail <EmailAddress>] [default]
