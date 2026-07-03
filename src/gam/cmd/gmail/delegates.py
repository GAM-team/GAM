"""Gmail delegation management.

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

UTF8 = 'utf-8'

def sendCreateDelegateNotification(user, delegate, basenotify, i=0, count=0, msgFrom=None):
# Substitute for #user#, #delegate#
  def _substituteForPattern(field, pattern, value):
    if field.find('#') == -1:
      return field
    return field.replace(pattern, value)

  def _makeSubstitutions(field):
    notify[field] = _substituteForPattern(notify[field], '#user#', user)
    notify[field] = _substituteForPattern(notify[field], '#delegate#', delegate)

  notify = basenotify.copy()
  if not notify['subject']:
    notify['subject'] = Msg.CREATE_DELEGATE_NOTIFY_SUBJECT
  _makeSubstitutions('subject')
  if not notify['message']:
    notify['message'] = Msg.CREATE_DELEGATE_NOTIFY_MESSAGE
  elif notify['html']:
    notify['message'] = notify['message'].replace('\r', '').replace('\\n', '<br/>')
  else:
    notify['message'] = notify['message'].replace('\r', '').replace('\\n', '\n')
  _makeSubstitutions('message')
  if 'from' in notify:
    msgFrom = notify['from']
  msgReplyTo = notify.get('replyto', None)
  mailBox = notify.get('mailbox', None)
  send_email(notify['subject'], notify['message'], delegate, i, count,
             msgFrom=msgFrom, msgReplyTo=msgReplyTo, html=notify['html'], charset=notify['charset'], mailBox=mailBox)

# gam <UserTypeEntity> create delegate|delegates [convertalias] <UserEntity>
#	[notify [<Boolean>]
#	    [subject <String>]
#	    [from <EmailAaddress>] [mailbox <EmailAddress>]
#	    [replyto <EmailAaddress>]
#	    [<NotifyMessageContent>] [html [<Boolean>]]
#	]
# gam <UserTypeEntity> delete delegate|delegates [convertalias] <UserEntity>
def processDelegates(users):
  cd = _getMain().buildGAPIObject(API.DIRECTORY)
  createCmd = Act.Get() != Act.DELETE
  aliasAllowed = not _getMain().checkArgumentPresent(['convertalias'])
  delegateEntity = _getMain().getUserObjectEntity(Cmd.OB_USER_ENTITY, Ent.DELEGATE)
  notify = {'notify': False, 'subject': '', 'message': '', 'html': False, 'charset': UTF8}
  if createCmd:
    while Cmd.ArgumentsRemaining():
      myarg = _getMain().getArgument()
      if _getMain().getNotifyArguments(myarg, notify, False):
        pass
      else:
        _getMain().unknownArgumentExit()
  else:
    _getMain().checkForExtraneousArguments()
  i, count, users = _getMain().getEntityArgument(users)
  for user in users:
    i += 1
    user, gmail, delegates, jcount = _getMain()._validateUserGetObjectList(user, i, count, delegateEntity)
    if jcount == 0:
      continue
    Ind.Increment()
    j = 0
    for delegate in delegates:
      j += 1
      delegateEmail = _getMain().convertUIDtoEmailAddress(delegate, cd=cd, emailTypes=['user', 'group'], aliasAllowed=aliasAllowed)
      kvList = [Ent.USER, user, Ent.DELEGATE, delegateEmail]
      try:
        if createCmd:
          _getMain().callGAPI(gmail.users().settings().delegates(), 'create',
                   throwReasons=GAPI.GMAIL_THROW_REASONS+[GAPI.ALREADY_EXISTS, GAPI.FAILED_PRECONDITION, GAPI.INVALID,
                                                          GAPI.NOT_FOUND, GAPI.INVALID_ARGUMENT, GAPI.PERMISSION_DENIED],
                   userId='me', body={'delegateEmail': delegateEmail})
          _getMain().entityActionPerformed(kvList, j, jcount)
          if notify['notify']:
            Ind.Increment()
            sendCreateDelegateNotification(user, delegateEmail, notify, j, jcount)
            Ind.Decrement()
        else:
          _getMain().callGAPI(gmail.users().settings().delegates(), 'delete',
                   throwReasons=GAPI.GMAIL_THROW_REASONS+[GAPI.NOT_FOUND, GAPI.INVALID_INPUT, GAPI.PERMISSION_DENIED],
                   userId='me', delegateEmail=delegateEmail)
          _getMain().entityActionPerformed(kvList, j, jcount)
      except (GAPI.alreadyExists, GAPI.failedPrecondition, GAPI.invalid,
              GAPI.notFound, GAPI.invalidArgument, GAPI.permissionDenied) as e:
        _getMain().entityActionFailedWarning(kvList, str(e), j, jcount)
      except GAPI.serviceNotAvailable:
        _getMain().userGmailServiceNotEnabledWarning(user, i, count)
    Ind.Decrement()

# gam <UserTypeEntity> delegate to [convertalias] <UserEntity>
#	[notify [<Boolean>]
#	    [subject <String>]
#	    [from <EmailAaddress>] [mailbox <EmailAddress>]
#	    [replyto <EmailAaddress>]
#	    [<NotifyMessageContent>] [html [<Boolean>]]
#	]
def delegateTo(users):
  _getMain().checkArgumentPresent('to', required=True)
  processDelegates(users)

# gam <UserTypeEntity> update delegate|delegates [convertalias] [<UserEntity>]
def updateDelegates(users):
  cd = _getMain().buildGAPIObject(API.DIRECTORY)
  aliasAllowed = not _getMain().checkArgumentPresent(['convertalias'])
  if Cmd.ArgumentsRemaining():
    delegateEntity = _getMain().getUserObjectEntity(Cmd.OB_USER_ENTITY, Ent.DELEGATE)
    _getMain().checkForExtraneousArguments()
  else:
    delegateEntity = None
  i, count, users = _getMain().getEntityArgument(users)
  for user in users:
    i += 1
    if delegateEntity is None:
      user, gmail = _getMain().buildGAPIServiceObject(API.GMAIL, user, i, count)
      if not gmail:
        continue
      try:
        result = _getMain().callGAPI(gmail.users().settings().delegates(), 'list',
                          throwReasons=GAPI.GMAIL_THROW_REASONS+[GAPI.PERMISSION_DENIED],
                          userId='me')
      except GAPI.permissionDenied as e:
        _getMain().entityActionFailedWarning([Ent.USER, user, Ent.DELEGATE, None], str(e), i, count)
        continue
      except GAPI.serviceNotAvailable:
        _getMain().userGmailServiceNotEnabledWarning(user, i, count)
        continue
      delegates = result.get('delegates', []) if result is not None else []
      jcount = len(delegates)
      _getMain().entityPerformActionModifierNumItems([Ent.USER, user], Msg.MAXIMUM_OF, jcount, Ent.DELEGATE, i, count)
    else:
      user, gmail, delegates, jcount = _getMain()._validateUserGetObjectList(user, i, count, delegateEntity)
      if jcount == 0:
        continue
    Ind.Increment()
    j = 0
    for delegate in delegates:
      j += 1
      if delegateEntity is not None or delegate['verificationStatus'] == 'accepted':
        delegateEmail = delegate['delegateEmail'] if delegateEntity is None else _getMain().convertUIDtoEmailAddress(delegate, cd=cd, aliasAllowed=aliasAllowed)
        try:
          _getMain().callGAPI(gmail.users().settings().delegates(), 'create',
                   throwReasons=GAPI.GMAIL_THROW_REASONS+[GAPI.ALREADY_EXISTS, GAPI.FAILED_PRECONDITION,
                                                          GAPI.NOT_FOUND, GAPI.INVALID_ARGUMENT, GAPI.PERMISSION_DENIED],
                   userId='me', body={'delegateEmail': delegateEmail, 'verificationStatus': 'accepted'})
          _getMain().entityActionPerformed([Ent.USER, user, Ent.DELEGATE, delegateEmail], j, jcount)
        except GAPI.alreadyExists:
          _getMain().entityActionPerformed([Ent.USER, user, Ent.DELEGATE, delegateEmail], j, jcount)
        except (GAPI.failedPrecondition, GAPI.notFound, GAPI.invalidArgument, GAPI.permissionDenied) as e:
          _getMain().entityActionFailedWarning([Ent.USER, user, Ent.DELEGATE, delegateEmail], str(e), j, jcount)
        except GAPI.serviceNotAvailable:
          _getMain().userGmailServiceNotEnabledWarning(user, i, count)
    Ind.Decrement()

# gam <UserTypeEntity> print delegates|delegate [todrive <ToDriveAttribute>*] [shownames]
# gam <UserTypeEntity> show delegates|delegate [shownames] [csv]
def printShowDelegates(users):
  titlesList = ['User', 'delegateAddress', 'delegationStatus']
  csvPF = _getMain().CSVPrintFile() if Act.csvFormat() else None
  cd = None
  csvStyle = showNames = False
  delegateNames = {}
  while Cmd.ArgumentsRemaining():
    myarg = _getMain().getArgument()
    if csvPF and myarg == 'todrive':
      csvPF.GetTodriveParameters()
    elif not csvPF and myarg == 'csv':
      csvStyle = True
    elif myarg == 'shownames':
      cd = _getMain().buildGAPIObject(API.DIRECTORY)
      titlesList = ['User', 'delegateName', 'delegateAddress', 'delegationStatus']
      showNames = True
    else:
      _getMain().unknownArgumentExit()
  if csvPF:
    csvPF.AddTitles(titlesList)
  i, count, users = _getMain().getEntityArgument(users)
  for user in users:
    i += 1
    user, gmail = _getMain().buildGAPIServiceObject(API.GMAIL, user, i, count)
    if not gmail:
      continue
    if csvPF:
      _getMain().printGettingAllEntityItemsForWhom(Ent.DELEGATE, user, i, count)
    try:
      result = _getMain().callGAPI(gmail.users().settings().delegates(), 'list',
                        throwReasons=GAPI.GMAIL_THROW_REASONS+[GAPI.PERMISSION_DENIED, GAPI.FAILED_PRECONDITION],
                        userId='me')
      delegates = result.get('delegates', []) if result is not None else []
      if not csvPF:
        jcount = len(delegates)
        if not csvStyle:
          _getMain().entityPerformActionNumItems([Ent.USER, user], jcount, Ent.DELEGATE, i, count)
          Ind.Increment()
          j = 0
          for delegate in delegates:
            j += 1
            status = delegate['verificationStatus']
            delegateEmail = delegate['delegateEmail']
            if cd:
              _getMain().printEntity([Ent.DELEGATE, _getMain()._getDelegateName(cd, delegateEmail, delegateNames)], j, jcount)
              Ind.Increment()
              _getMain().printKeyValueList(['Status', status])
              _getMain().printKeyValueList(['Delegate Email', delegateEmail])
              Ind.Decrement()
            else:
              _getMain().printEntity([Ent.DELEGATE, delegateEmail], j, jcount)
              Ind.Increment()
              _getMain().printKeyValueList(['Status', status])
              Ind.Decrement()
          Ind.Decrement()
        else:
          j = 0
          for delegate in delegates:
            j += 1
            status = delegate['verificationStatus']
            delegateEmail = delegate['delegateEmail']
            if cd:
              _getMain().writeStdout(f'{user},{_getDelegateName(cd, delegateEmail, delegateNames)},{status},{delegateEmail}\n')
            else:
              _getMain().writeStdout(f'{user},{status},{delegateEmail}\n')
      elif delegates:
        if showNames:
          for delegate in delegates:
            csvPF.WriteRow({'User': user, 'delegateName': _getDelegateName(cd, delegate['delegateEmail'], delegateNames),
                            'delegateAddress': delegate['delegateEmail'], 'delegationStatus': delegate['verificationStatus']})
        else:
          for delegate in delegates:
            csvPF.WriteRow({'User': user, 'delegateAddress': delegate['delegateEmail'],
                            'delegationStatus': delegate['verificationStatus']})
      elif GC.Values[GC.CSV_OUTPUT_USERS_AUDIT]:
        csvPF.WriteRowNoFilter({'User': user})
    except (GAPI.permissionDenied, GAPI.failedPrecondition) as e:
      _getMain().entityActionFailedWarning([Ent.USER, user, Ent.DELEGATE, None], str(e), i, count)
    except GAPI.serviceNotAvailable:
      _getMain().userGmailServiceNotEnabledWarning(user, i, count)
  if csvPF:
    csvPF.writeCSVfile('Delegates')

FILTER_ADD_LABEL_TO_ARGUMENT_MAP = {
  'IMPORTANT': 'important',
  'STARRED': 'star',
  'TRASH': 'trash',
  }

FILTER_REMOVE_LABEL_TO_ARGUMENT_MAP = {
  'IMPORTANT': 'notimportant',
  'INBOX': 'archive',
  'SPAM': 'neverspam',
  'UNREAD': 'markread',
  }

