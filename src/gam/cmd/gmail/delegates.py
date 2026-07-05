"""Gmail delegation management.

Part of the _gmail_monolith sub-package."""

"""GAM Gmail management: labels, messages, filters, forwarding, sendas, S/MIME, CSE, vacation."""


from gamlib import api as API
from gamlib import settings as GC
from gamlib import gapi as GAPI
from gamlib import msgs as Msg
from gam.util.api import buildGAPIObject
from gam.util.svcacct import buildGAPIServiceObject
from gam.util.api_call import callGAPI
from gam.util.args import checkArgumentPresent, checkForExtraneousArguments, getArgument
from gam.util.csv_pf import CSVPrintFile
from gam.util.display import (
    entityActionFailedWarning,
    entityActionPerformed,
    entityPerformActionModifierNumItems,
    entityPerformActionNumItems,
    printEntity,
    printGettingAllEntityItemsForWhom,
    printKeyValueList,
    userGmailServiceNotEnabledWarning,
)
from gam.util.entity import _validateUserGetObjectList, convertUIDtoEmailAddress, getEntityArgument, getUserObjectEntity
from gam.util.errors import unknownArgumentExit
from gam.util.output import writeStdout
from gam.util.email import send_email
from gam.cmd.users.manage import getNotifyArguments
from gam.cmd.delegates import _getDelegateName

from gam.var import Act, Cmd, Ent, Ind

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
  cd = buildGAPIObject(API.DIRECTORY)
  createCmd = Act.Get() != Act.DELETE
  aliasAllowed = not checkArgumentPresent(['convertalias'])
  delegateEntity = getUserObjectEntity(Cmd.OB_USER_ENTITY, Ent.DELEGATE)
  notify = {'notify': False, 'subject': '', 'message': '', 'html': False, 'charset': UTF8}
  if createCmd:
    while Cmd.ArgumentsRemaining():
      myarg = getArgument()
      if getNotifyArguments(myarg, notify, False):
        pass
      else:
        unknownArgumentExit()
  else:
    checkForExtraneousArguments()
  i, count, users = getEntityArgument(users)
  for user in users:
    i += 1
    user, gmail, delegates, jcount = _validateUserGetObjectList(user, i, count, delegateEntity)
    if jcount == 0:
      continue
    Ind.Increment()
    j = 0
    for delegate in delegates:
      j += 1
      delegateEmail = convertUIDtoEmailAddress(delegate, cd=cd, emailTypes=['user', 'group'], aliasAllowed=aliasAllowed)
      kvList = [Ent.USER, user, Ent.DELEGATE, delegateEmail]
      try:
        if createCmd:
          callGAPI(gmail.users().settings().delegates(), 'create',
                   throwReasons=GAPI.GMAIL_THROW_REASONS+[GAPI.ALREADY_EXISTS, GAPI.FAILED_PRECONDITION, GAPI.INVALID,
                                                          GAPI.NOT_FOUND, GAPI.INVALID_ARGUMENT, GAPI.PERMISSION_DENIED],
                   userId='me', body={'delegateEmail': delegateEmail})
          entityActionPerformed(kvList, j, jcount)
          if notify['notify']:
            Ind.Increment()
            sendCreateDelegateNotification(user, delegateEmail, notify, j, jcount)
            Ind.Decrement()
        else:
          callGAPI(gmail.users().settings().delegates(), 'delete',
                   throwReasons=GAPI.GMAIL_THROW_REASONS+[GAPI.NOT_FOUND, GAPI.INVALID_INPUT, GAPI.PERMISSION_DENIED],
                   userId='me', delegateEmail=delegateEmail)
          entityActionPerformed(kvList, j, jcount)
      except (GAPI.alreadyExists, GAPI.failedPrecondition, GAPI.invalid,
              GAPI.notFound, GAPI.invalidArgument, GAPI.permissionDenied) as e:
        entityActionFailedWarning(kvList, str(e), j, jcount)
      except GAPI.serviceNotAvailable:
        userGmailServiceNotEnabledWarning(user, i, count)
    Ind.Decrement()

# gam <UserTypeEntity> delegate to [convertalias] <UserEntity>
#	[notify [<Boolean>]
#	    [subject <String>]
#	    [from <EmailAaddress>] [mailbox <EmailAddress>]
#	    [replyto <EmailAaddress>]
#	    [<NotifyMessageContent>] [html [<Boolean>]]
#	]
def delegateTo(users):
  checkArgumentPresent('to', required=True)
  processDelegates(users)

# gam <UserTypeEntity> update delegate|delegates [convertalias] [<UserEntity>]
def updateDelegates(users):
  cd = buildGAPIObject(API.DIRECTORY)
  aliasAllowed = not checkArgumentPresent(['convertalias'])
  if Cmd.ArgumentsRemaining():
    delegateEntity = getUserObjectEntity(Cmd.OB_USER_ENTITY, Ent.DELEGATE)
    checkForExtraneousArguments()
  else:
    delegateEntity = None
  i, count, users = getEntityArgument(users)
  for user in users:
    i += 1
    if delegateEntity is None:
      user, gmail = buildGAPIServiceObject(API.GMAIL, user, i, count)
      if not gmail:
        continue
      try:
        result = callGAPI(gmail.users().settings().delegates(), 'list',
                          throwReasons=GAPI.GMAIL_THROW_REASONS+[GAPI.PERMISSION_DENIED],
                          userId='me')
      except GAPI.permissionDenied as e:
        entityActionFailedWarning([Ent.USER, user, Ent.DELEGATE, None], str(e), i, count)
        continue
      except GAPI.serviceNotAvailable:
        userGmailServiceNotEnabledWarning(user, i, count)
        continue
      delegates = result.get('delegates', []) if result is not None else []
      jcount = len(delegates)
      entityPerformActionModifierNumItems([Ent.USER, user], Msg.MAXIMUM_OF, jcount, Ent.DELEGATE, i, count)
    else:
      user, gmail, delegates, jcount = _validateUserGetObjectList(user, i, count, delegateEntity)
      if jcount == 0:
        continue
    Ind.Increment()
    j = 0
    for delegate in delegates:
      j += 1
      if delegateEntity is not None or delegate['verificationStatus'] == 'accepted':
        delegateEmail = delegate['delegateEmail'] if delegateEntity is None else convertUIDtoEmailAddress(delegate, cd=cd, aliasAllowed=aliasAllowed)
        try:
          callGAPI(gmail.users().settings().delegates(), 'create',
                   throwReasons=GAPI.GMAIL_THROW_REASONS+[GAPI.ALREADY_EXISTS, GAPI.FAILED_PRECONDITION,
                                                          GAPI.NOT_FOUND, GAPI.INVALID_ARGUMENT, GAPI.PERMISSION_DENIED],
                   userId='me', body={'delegateEmail': delegateEmail, 'verificationStatus': 'accepted'})
          entityActionPerformed([Ent.USER, user, Ent.DELEGATE, delegateEmail], j, jcount)
        except GAPI.alreadyExists:
          entityActionPerformed([Ent.USER, user, Ent.DELEGATE, delegateEmail], j, jcount)
        except (GAPI.failedPrecondition, GAPI.notFound, GAPI.invalidArgument, GAPI.permissionDenied) as e:
          entityActionFailedWarning([Ent.USER, user, Ent.DELEGATE, delegateEmail], str(e), j, jcount)
        except GAPI.serviceNotAvailable:
          userGmailServiceNotEnabledWarning(user, i, count)
    Ind.Decrement()

# gam <UserTypeEntity> print delegates|delegate [todrive <ToDriveAttribute>*] [shownames]
# gam <UserTypeEntity> show delegates|delegate [shownames] [csv]
def printShowDelegates(users):
  titlesList = ['User', 'delegateAddress', 'delegationStatus']
  csvPF = CSVPrintFile() if Act.csvFormat() else None
  cd = None
  csvStyle = showNames = False
  delegateNames = {}
  while Cmd.ArgumentsRemaining():
    myarg = getArgument()
    if csvPF and myarg == 'todrive':
      csvPF.GetTodriveParameters()
    elif not csvPF and myarg == 'csv':
      csvStyle = True
    elif myarg == 'shownames':
      cd = buildGAPIObject(API.DIRECTORY)
      titlesList = ['User', 'delegateName', 'delegateAddress', 'delegationStatus']
      showNames = True
    else:
      unknownArgumentExit()
  if csvPF:
    csvPF.AddTitles(titlesList)
  i, count, users = getEntityArgument(users)
  for user in users:
    i += 1
    user, gmail = buildGAPIServiceObject(API.GMAIL, user, i, count)
    if not gmail:
      continue
    if csvPF:
      printGettingAllEntityItemsForWhom(Ent.DELEGATE, user, i, count)
    try:
      result = callGAPI(gmail.users().settings().delegates(), 'list',
                        throwReasons=GAPI.GMAIL_THROW_REASONS+[GAPI.PERMISSION_DENIED, GAPI.FAILED_PRECONDITION],
                        userId='me')
      delegates = result.get('delegates', []) if result is not None else []
      if not csvPF:
        jcount = len(delegates)
        if not csvStyle:
          entityPerformActionNumItems([Ent.USER, user], jcount, Ent.DELEGATE, i, count)
          Ind.Increment()
          j = 0
          for delegate in delegates:
            j += 1
            status = delegate['verificationStatus']
            delegateEmail = delegate['delegateEmail']
            if cd:
              printEntity([Ent.DELEGATE, _getDelegateName(cd, delegateEmail, delegateNames)], j, jcount)
              Ind.Increment()
              printKeyValueList(['Status', status])
              printKeyValueList(['Delegate Email', delegateEmail])
              Ind.Decrement()
            else:
              printEntity([Ent.DELEGATE, delegateEmail], j, jcount)
              Ind.Increment()
              printKeyValueList(['Status', status])
              Ind.Decrement()
          Ind.Decrement()
        else:
          j = 0
          for delegate in delegates:
            j += 1
            status = delegate['verificationStatus']
            delegateEmail = delegate['delegateEmail']
            if cd:
              writeStdout(f'{user},{_getDelegateName(cd, delegateEmail, delegateNames)},{status},{delegateEmail}\n')
            else:
              writeStdout(f'{user},{status},{delegateEmail}\n')
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
      entityActionFailedWarning([Ent.USER, user, Ent.DELEGATE, None], str(e), i, count)
    except GAPI.serviceNotAvailable:
      userGmailServiceNotEnabledWarning(user, i, count)
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

