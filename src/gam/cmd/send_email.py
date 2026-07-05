"""GAM email sending and tag replacement utilities."""

import time


from gamlib import api as API
from gamlib import settings as GC
from gamlib import gapi as GAPI
from gamlib import msgs as Msg
from gam.var import Act, Cmd, Ent, Ind
from gam.util.api import _getAdminEmail
from gam.util.svcacct import buildGAPIServiceObject
from gam.util.api_call import callGAPI, callGAPIpages
from gam.util.args import (
    SORF_MSG_FILE_ARGUMENTS,
    UTF8,
    checkArgumentPresent,
    getArgument,
    getBoolean,
    getCharSet,
    getDateOrDeltaFromNow,
    getEmailAddress,
    getFilename,
    getString,
    getStringOrFile,
    getTimeOrDeltaFromNow,
    normalizeEmailAddressOrUID,
)
from gam.util.display import (
    entityActionFailedWarning,
    entityNumEntitiesActionNotPerformedWarning,
    entityPerformActionModifierNumItems,
    getPageMessageForWhom,
    printGettingAllEntityItemsForWhom,
    userGmailServiceNotEnabledWarning,
)
from gam.util.email import send_email
from gam.util.entity import getEntityArgument, getEntityList
from gam.util.errors import (
    missingArgumentExit,
    unknownArgumentExit,
    usageErrorExit,
)
from gam.util.output import setSysExitRC
from gam.util.tags import (  # noqa: F401  # re-export
    ADDRESS_FIELDS_PRINT_ORDER,
    CASE_MARKERS,
    LC_PATTERN,
    PC_PATTERN,
    RTL_PATTERN,
    RT_MARKERS,
    RT_PATTERN,
    SKIP_PATTERNS,
    TAG_ADDRESS_ARGUMENT_TO_FIELD_MAP,
    TAG_EMAIL_ARGUMENT_TO_FIELD_MAP,
    TAG_EXTERNALID_ARGUMENT_TO_FIELD_MAP,
    TAG_FIELD_SUBFIELD_CHOICE_MAP,
    TAG_GENDER_ARGUMENT_TO_FIELD_MAP,
    TAG_IM_ARGUMENT_TO_FIELD_MAP,
    TAG_KEYWORD_ARGUMENT_TO_FIELD_MAP,
    TAG_LOCATION_ARGUMENT_TO_FIELD_MAP,
    TAG_NAME_ARGUMENT_TO_FIELD_MAP,
    TAG_ORGANIZATION_ARGUMENT_TO_FIELD_MAP,
    TAG_OTHEREMAIL_ARGUMENT_TO_FIELD_MAP,
    TAG_PHONE_ARGUMENT_TO_FIELD_MAP,
    TAG_POSIXACCOUNT_ARGUMENT_TO_FIELD_MAP,
    TAG_RELATION_ARGUMENT_TO_FIELD_MAP,
    TAG_REPLACE_PATTERN,
    TAG_SSHPUBLICKEY_ARGUMENT_TO_FIELD_MAP,
    TAG_WEBSITE_ARGUMENT_TO_FIELD_MAP,
    UC_PATTERN,
    _getTagReplacement,
    _getTagReplacementFieldValues,
    _initTagReplacements,
    _processTagReplacements,
    _substituteForUser,
    getRecipients,
    sendCreateUpdateUserNotification,
)
from gam.constants import NO_ENTITIES_FOUND_RC
from gam.cmd.gmail.modify import SMTP_DATE_HEADERS, SMTP_HEADERS_MAP
from gam.cmd.gmail.modify import SMTP_DATE_HEADERS, SMTP_HEADERS_MAP, _decodeHeader


from email.utils import formatdate


# gam sendemail [recipient|to] <RecipientEntity>
#	[from <EmailAddress>] [mailbox <EmailAddress>] [replyto <EmailAddress>]
#	[cc <RecipientEntity>] [bcc <RecipientEntity>] [singlemessage]
#	[subject <String>] [<MessageContent>] [html [<Boolean>]]
#	(replace <Tag> <String>)*
#	(replaceregex <REMatchPattern> <RESubstitution>  <Tag> <String>)*
#	(attach <FileName> [charset <CharSet>])*
#	(embedimage <FileName> <String>)*
#	[newuser <EmailAddress> firstname|givenname <String> lastname|familyname <string> password <Password>]
#	(<SMTPDateHeader> <Time>)* (<SMTPHeader> <String>)* (header <String> <String>)*
#	[threadid <String>]
# gam <UserTypeEntity> sendemail recipient|to <RecipientEntity>
#	[replyto <EmailAddress>]
#	[cc <RecipientEntity>] [bcc <RecipientEntity>] [singlemessage]
#	[subject <String>] [<MessageContent>] [html [<Boolean>]]
#	(replace <Tag> <String>)*
#	(replaceregex <REMatchPattern> <RESubstitution>  <Tag> <String>)*
#	(attach <FileName> [charset <CharSet>])*
#	(embedimage <FileName> <String>)*
#	[newuser <EmailAddress> firstname|givenname <String> lastname|familyname <string> password <Password>]
#	(<SMTPDateHeader> <Time>)* (<SMTPHeader> <String>)* (header <String> <String>)*
#	[threadid <String>]
# gam <UserTypeEntity> sendemail from <EmailAddress>
#	[replyto <EmailAddress>]
#	[cc <RecipientEntity>] [bcc <RecipientEntity>] [singlemessage]
#	[subject <String>] [<MessageContent> ][html [<Boolean>]]
#	(replace <Tag> <String>)*
#	(replaceregex <REMatchPattern> <RESubstitution>  <Tag> <String>)*
#	(attach <FileName> [charset <CharSet>])*
#	(embedimage <FileName> <String>)*
#	[newuser <EmailAddress> firstname|givenname <String> lastname|familyname <string> password <Password>]
#	(<SMTPDateHeader> <Time>)* (<SMTPHeader> <String>)* (header <String> <String>)*
#	[threadid <String>]
def doSendEmail(users=None):
  body = {}
  notify = {'subject': '', 'message': '', 'html': False, 'charset': UTF8, 'password': ''}
  msgFroms = [_getAdminEmail()]
  count = 1
  if users is None:
    checkArgumentPresent({'recipient', 'recipients', 'to'})
    recipients = getRecipients()
  else:
    _, count, entityList = getEntityArgument(users)
    if checkArgumentPresent({'recipient', 'recipients', 'to'}):
      msgFroms = [normalizeEmailAddressOrUID(entity) for entity in entityList]
      recipients = getRecipients()
    elif checkArgumentPresent({'from'}):
      recipients = [normalizeEmailAddressOrUID(entity) for entity in entityList]
      msgFroms = [getString(Cmd.OB_EMAIL_ADDRESS)]
      count = 1
    else:
      missingArgumentExit('recipient|to|from')
  msgHeaders = {}
  ccRecipients = []
  bccRecipients = []
  mailBox = None
  msgReplyTo = None
  threadId = None
  singleMessage = False
  tagReplacements = _initTagReplacements()
  attachments = []
  embeddedImages = []
  while Cmd.ArgumentsRemaining():
    myarg = getArgument()
    if users is None and myarg == 'from':
      msgFroms = [getString(Cmd.OB_EMAIL_ADDRESS)]
      count = 1
    elif myarg == 'replyto':
      msgReplyTo = getString(Cmd.OB_EMAIL_ADDRESS)
    elif myarg == 'subject':
      notify['subject'] = getString(Cmd.OB_STRING)
    elif myarg in SORF_MSG_FILE_ARGUMENTS:
      notify['message'], notify['charset'], notify['html'] = getStringOrFile(myarg)
    elif myarg == 'cc':
      ccRecipients = getRecipients()
    elif myarg == 'bcc':
      bccRecipients = getRecipients()
    elif myarg == 'mailbox':
      mailBox = getString(Cmd.OB_EMAIL_ADDRESS)
    elif myarg == 'singlemessage':
      singleMessage = True
    elif myarg == 'html':
      notify['html'] = getBoolean()
    elif myarg == 'newuser':
      body['primaryEmail'] = getEmailAddress()
    elif myarg in {'firstname', 'givenname'}:
      body.setdefault('name', {})
      body['name']['givenName'] = getString(Cmd.OB_STRING, minLen=0, maxLen=60)
    elif myarg in {'lastname', 'familyname'}:
      body.setdefault('name', {})
      body['name']['familyName'] = getString(Cmd.OB_STRING, minLen=0, maxLen=60)
    elif myarg in {'password', 'notifypassword'}:
      body['password'] = notify['password'] = getString(Cmd.OB_PASSWORD, maxLen=100)
    elif _getTagReplacement(myarg, tagReplacements, False):
      pass
    elif myarg == 'attach':
      attachments.append((getFilename(), getCharSet()))
    elif myarg == 'embedimage':
      embeddedImages.append((getFilename(), getString(Cmd.OB_STRING)))
    elif myarg in SMTP_HEADERS_MAP:
      if myarg in SMTP_DATE_HEADERS:
        msgDate, _, _ = getTimeOrDeltaFromNow(True)
        msgHeaders[SMTP_HEADERS_MAP[myarg]] = formatdate(time.mktime(msgDate.timetuple()) + msgDate.microsecond/1E6, True)
      else:
        msgHeaders[SMTP_HEADERS_MAP[myarg]] = getString(Cmd.OB_STRING)
    elif myarg == 'header':
      header = getString(Cmd.OB_STRING, minLen=1)
      msgHeaders[SMTP_HEADERS_MAP.get(header.lower(), header)] = getString(Cmd.OB_STRING)
    elif myarg == 'threadid':
      threadId = getString(Cmd.OB_STRING)
    else:
      unknownArgumentExit()
  notify['message'] = notify['message'].replace('\r', '').replace('\\n', '\n')
  if tagReplacements['tags']:
    notify['message'] = _processTagReplacements(tagReplacements, notify['message'])
  if tagReplacements['tags']:
    notify['subject'] = _processTagReplacements(tagReplacements, notify['subject'])
  jcount = len(recipients)
  if body.get('primaryEmail'):
    if (recipients and ('password' in body) and ('name' in body) and ('givenName' in body['name']) and ('familyName' in body['name'])):
      notify['recipients'] = recipients
      sendCreateUpdateUserNotification(body, notify, tagReplacements, msgFrom=msgFroms[0])
    else:
      usageErrorExit(Msg.NEWUSER_REQUIREMENTS, True)
    return
  if ccRecipients or bccRecipients:
    singleMessage = True
  i = 0
  for msgFrom in msgFroms:
    i += 1
    if singleMessage:
      entityPerformActionModifierNumItems([Ent.USER, msgFrom],
                                          Act.MODIFIER_TO, jcount+len(ccRecipients)+len(bccRecipients), Ent.RECIPIENT, i, count)
      send_email(notify['subject'], notify['message'], ','.join(recipients), i, count,
                 msgFrom=msgFrom, msgReplyTo=msgReplyTo, html=notify['html'], charset=notify['charset'],
                 attachments=attachments, embeddedImages=embeddedImages, msgHeaders=msgHeaders,
                 ccRecipients=','.join(ccRecipients), bccRecipients=','.join(bccRecipients),
                 mailBox=mailBox, threadId=threadId)
    else:
      entityPerformActionModifierNumItems([Ent.USER, msgFrom], Act.MODIFIER_TO, jcount, Ent.RECIPIENT, i, count)
      Ind.Increment()
      j = 0
      for recipient in recipients:
        j += 1
        send_email(notify['subject'], notify['message'], recipient, j, jcount,
                   msgFrom=msgFrom, msgReplyTo=msgReplyTo, html=notify['html'], charset=notify['charset'],
                   attachments=attachments, embeddedImages=embeddedImages, msgHeaders=msgHeaders, mailBox=mailBox, threadId=threadId)
      Ind.Decrement()

# gam <UserTypeEntity> sendreply
#	(((query <QueryGmail> [querytime<String> <Date>]*) [or|and])+) | (ids <MessageIDEntity>)
#	[replyto <EmailAddress>]
#	[subject <String>] [<MessageContent>] [html [<Boolean>]]
#	(attach <FileName> [charset <CharSet>])*
#	(embedimage <FileName> <String>)*
#	(<SMTPDateHeader> <Time>)* (<SMTPHeader> <String>)* (header <String> <String>)*
def doSendReply(users):
  def _getHeaderValue(name):
    for header in messageInfo['payload']['headers']:
      if name == header['name']:
        return _decodeHeader(header['value'])
    return ''

  notify = {'subject': '', 'message': '', 'html': False, 'charset': UTF8}
  query = ''
  queryTimes = {}
  messageIds = []
  msgHeaders = {}
  msgReplyTo = None
  attachments = []
  embeddedImages = []
  while Cmd.ArgumentsRemaining():
    myarg = getArgument()
    if myarg == 'query':
      selectLocation = Cmd.Location()
      if query:
        query += ' '
      query += f'({getString(Cmd.OB_QUERY)})'
    elif myarg.startswith('querytime'):
      queryTimes[myarg] = getDateOrDeltaFromNow().replace('-', '/')
    elif myarg in {'or', 'and'}:
      if query:
        query += f' {myarg.upper()}'
    elif myarg == 'ids':
      selectLocation = Cmd.Location()
      messageIds = getEntityList(Cmd.OB_MESSAGE_ID)
    elif myarg == 'subject':
      notify['subject'] = getString(Cmd.OB_STRING)
    elif myarg in SORF_MSG_FILE_ARGUMENTS:
      notify['message'], notify['charset'], notify['html'] = getStringOrFile(myarg)
    elif myarg == 'replyto':
      msgReplyTo = getString(Cmd.OB_EMAIL_ADDRESS)
    elif myarg == 'html':
      notify['html'] = getBoolean()
    elif myarg == 'attach':
      attachments.append((getFilename(), getCharSet()))
    elif myarg == 'embedimage':
      embeddedImages.append((getFilename(), getString(Cmd.OB_STRING)))
    elif myarg in SMTP_HEADERS_MAP:
      if myarg in SMTP_DATE_HEADERS:
        msgDate, _, _ = getTimeOrDeltaFromNow(True)
        msgHeaders[SMTP_HEADERS_MAP[myarg]] = formatdate(time.mktime(msgDate.timetuple()) + msgDate.microsecond/1E6, True)
      else:
        msgHeaders[SMTP_HEADERS_MAP[myarg]] = getString(Cmd.OB_STRING)
    elif myarg == 'header':
      header = getString(Cmd.OB_STRING, minLen=1)
      msgHeaders[SMTP_HEADERS_MAP.get(header.lower(), header)] = getString(Cmd.OB_STRING)
    else:
      unknownArgumentExit()
  if query and messageIds:
    Cmd.SetLocation(selectLocation-1)
    usageErrorExit(Msg.ARE_MUTUALLY_EXCLUSIVE.format('query <QueryGmail>', 'ids <MessageIDEntity>'))
  notify['message'] = notify['message'].replace('\r', '').replace('\\n', '\n')
  i, count, users = getEntityArgument(users)
  for user in users:
    i += 1
    user, gmail = buildGAPIServiceObject(API.GMAIL, user, i, count)
    if not gmail:
      continue
    try:
      if query:
        printGettingAllEntityItemsForWhom(Ent.MESSAGE, user, i, count, query=query)
        listResult = callGAPIpages(gmail.users().messages(), 'list', 'messages',
                                   pageMessage=getPageMessageForWhom(),
                                   throwReasons=GAPI.GMAIL_THROW_REASONS+GAPI.GMAIL_LIST_THROW_REASONS,
                                   userId='me', q=query, fields='nextPageToken,messages(id)',
                                   maxResults=GC.Values[GC.MESSAGE_MAX_RESULTS])
        messageIds = [message['id'] for message in listResult]
    except (GAPI.failedPrecondition, GAPI.permissionDenied, GAPI.invalid, GAPI.invalidArgument) as e:
      entityActionFailedWarning([Ent.USER, user], str(e), i, count)
      continue
    except GAPI.serviceNotAvailable:
      userGmailServiceNotEnabledWarning(user, i, count)
      continue
    jcount = len(messageIds)
    if jcount == 0:
      entityNumEntitiesActionNotPerformedWarning([Ent.USER, user], Ent.MESSAGE, jcount, Msg.NO_ENTITIES_MATCHED.format(Ent.Plural(Ent.MESSAGE)), i, count)
      setSysExitRC(NO_ENTITIES_FOUND_RC)
      continue
    entityPerformActionModifierNumItems([Ent.USER, user], Act.MODIFIER_TO, jcount, Ent.RECIPIENT, i, count)
    Ind.Increment()
    j = 0
    for messageId in messageIds:
      j += 1
      try:
        messageInfo = callGAPI(gmail.users().messages(), 'get',
                               throwReasons=GAPI.GMAIL_THROW_REASONS+[GAPI.NOT_FOUND, GAPI.INVALID_MESSAGE_ID],
                               userId='me', id=messageId, fields='id,threadId,payload(headers)')
        threadId = messageInfo['threadId']
        msgHeaders['References'] = msgHeaders['In-Reply-To'] = _getHeaderValue('Message-ID')
        msgSubject = notify['subject'] if notify['subject'] else f"Re: {_getHeaderValue('Subject')}"
        recipient = _getHeaderValue('From')
        send_email(msgSubject, notify['message'], recipient, j, jcount,
                   msgFrom=user, msgReplyTo=msgReplyTo, html=notify['html'], charset=notify['charset'],
                   attachments=attachments, embeddedImages=embeddedImages, msgHeaders=msgHeaders, threadId=threadId,
                   action=Act.SENDREPLY)
      except GAPI.notFound:
        entityActionFailedWarning([Ent.USER, user, Ent.MESSAGE, messageId], Msg.DOES_NOT_EXIST, j, jcount)
      except GAPI.invalidMessageId:
        entityActionFailedWarning([Ent.USER, user, Ent.MESSAGE, messageId], Msg.INVALID_MESSAGE_ID, j, jcount)
      except (GAPI.failedPrecondition, GAPI.permissionDenied, GAPI.invalid, GAPI.invalidArgument) as e:
        entityActionFailedWarning([Ent.USER, user], str(e), i, count)
        break
      except GAPI.serviceNotAvailable:
        userGmailServiceNotEnabledWarning(user, i, count)
        break
    Ind.Decrement()


