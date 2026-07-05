"""Gmail message/thread operations: select, archive, process, export, forward, draft, import.

Part of the _gmail_monolith sub-package."""

"""GAM Gmail management: labels, messages, filters, forwarding, sendas, S/MIME, CSE, vacation."""

import re



import googleapiclient.errors
import googleapiclient.http

from gam.util.batch import (
    RI_ENTITY,
    RI_J,
    RI_JCOUNT,
    RI_ITEM
)
from gam.cmd.gmail.labels import _getUserGmailLabels, _initLabelNameMap, _convertLabelNamesToIds, MESSAGES_MAX_TO_KEYWORDS
import io
import base64
import os
import time

from gamlib import api as API
from gamlib import settings as GC
from gamlib import gapi as GAPI
from gamlib import state as GM
from gamlib import msgs as Msg
from gam.util.api import _getAdminEmail, buildGAPIObject
from gam.util.svcacct import buildGAPIServiceObject
from gam.util.api_call import callGAPI, callGAPIpages, checkGAPIError
from gam.util.args import (
    SORF_MSG_FILE_ARGUMENTS,
    UTF8,
    checkArgumentPresent,
    getArgument,
    getBoolean,
    getCharSet,
    getEmailAddress,
    getFilename,
    getHTTPError,
    getInteger,
    getREPattern,
    getString,
    getStringOrFile,
    getTimeOrDeltaFromNow,
    splitEmailAddress
)
from gam.util.batch import batchRequestID
from gam.util.csv_pf import CSVPrintFile
from gam.util.display import (
    entityActionFailedWarning,
    entityActionNotPerformedWarning,
    entityActionPerformed,
    entityActionPerformedMessage,
    entityNumEntitiesActionNotPerformedWarning,
    entityPerformActionNumItems,
    getPageMessageForWhom,
    printGettingAllEntityItemsForWhom,
    userGmailServiceNotEnabledWarning
)
from gam.util.entity import (
    _validateUserGetMessageIds,
    getEntityArgument,
    getEntityList,
    shlexSplitList,
    splitEmailAddressOrUID,
)
from gam.util.errors import entityDoesNotExistExit, missingArgumentExit, unknownArgumentExit
from gam.util.fileio import (
    readFile,
    setFilePath,
    uniqueFilename,
    writeFileReturnError
)
from gam.util.batch import executeBatch
from gam.util.output import setSysExitRC, stderrWarningMsg
from gam.constants import NO_ENTITIES_FOUND_RC
from gam.util.tags import (
    _getTagReplacement,
    _getTagReplacementFieldValues,
    _initTagReplacements,
    _processTagReplacements,
    _substituteForUser,
    getRecipients,
)

from gam.var import Act, Cmd, Ent, Ind

from email.header import decode_header
from email import message_from_string
from email.policy import SMTP as policySMTP
from email.charset import add_charset
from email.charset import QP
from tempfile import TemporaryFile
from email.generator import Generator
from email.utils import formatdate
from email.header import Header
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
UTF8 = 'utf-8'

def _initMessageThreadParameters(entityType, doIt, maxToProcess):
  listType = 'messages' if entityType == Ent.MESSAGE else 'threads'
  return {'currLabelOp': 'and', 'prevLabelOp': 'and', 'labelGroupOpen':  False,
          'query': '', 'queryTimes': {},
          'entityType': entityType, 'messageEntity': None, 'doIt': doIt, 'quick': True,
          'labelMatchPattern': None, 'senderMatchPattern': None,
          'labelIds': [],
          'maxToProcess': maxToProcess, 'maxItems': 0, 'maxMessagesPerThread': 0,
          'maxToKeywords': [MESSAGES_MAX_TO_KEYWORDS[Act.Get()], 'maxtoprocess'],
          'listType': listType, 'fields': f'nextPageToken,{listType}(id)'}

LABEL_QUERY_REPLACEMENT_CHARACTERS = ' &()"|{}/'

def _getMessageSelectParameters(myarg, parameters):
  if myarg == 'query':
    if parameters['query']:
      if parameters['labelGroupOpen']:
        parameters['query'] += ')'
        parameters['labelGroupOpen'] = False
      parameters['query'] += ' '
    parameters['query'] += f'({getString(Cmd.OB_QUERY)})'
  elif myarg.startswith('querytime'):
    parameters['queryTimes'][myarg] = getDateOrDeltaFromNow().replace('-', '/')
  elif myarg == 'matchlabel':
    labelTemp = getString(Cmd.OB_LABEL_NAME).lower()
    labelName = ''
    for c in labelTemp:
      labelName += c if c not in LABEL_QUERY_REPLACEMENT_CHARACTERS else '-'
    if not parameters['labelGroupOpen']:
      if parameters['query']:
        parameters['query'] += ' '
      parameters['query'] += '('
      parameters['labelGroupOpen'] = True
    else:
      parameters['query'] += ' '
    parameters['query'] += f'label:{labelName}'
  elif myarg in {'or', 'and'}:
    parameters['prevLabelOp'] = parameters['currLabelOp']
    parameters['currLabelOp'] = myarg
    if parameters['labelGroupOpen'] and parameters['currLabelOp'] != parameters['prevLabelOp']:
      parameters['query'] += ')'
      parameters['labelGroupOpen'] = False
    if parameters['currLabelOp'] == 'or' and parameters['query']:
      parameters['query'] += ' OR'
  elif myarg == 'labelmatchpattern':
    parameters['labelMatchPattern'] = getREPattern(re.IGNORECASE)
  elif myarg == 'sendermatchpattern':
    parameters['senderMatchPattern'] = getREPattern(re.IGNORECASE)
  elif myarg == 'labelids':
    parameters['labelIds'].extend(getEntityList(Cmd.OB_LABEL_ID_LIST))
  elif myarg == 'ids':
    parameters['messageEntity'] = getUserObjectEntity(Cmd.OB_MESSAGE_ID, parameters['entityType'])
  elif myarg == 'quick':
    parameters['quick'] = True
  elif myarg == 'notquick':
    parameters['quick'] = False
  elif myarg == 'doit':
    parameters['doIt'] = True
  elif myarg in parameters['maxToKeywords']:
    parameters['maxToProcess'] = getInteger(minVal=0)
  elif myarg == 'maxmessagesperthread':
    parameters['maxMessagesPerThread'] = getInteger(minVal=0)
  else:
    return False
  return True

MESSAGE_TIME_QUERY_PATTERN = re.compile(r'(after:|before:|older:|newer:)(\d{4})/(\d{2})/(\d{2})')

def _mapMessageQueryDates(parameters):
  query = parameters['query']
  pos = 0
  while True:
    mg = MESSAGE_TIME_QUERY_PATTERN.search(query, pos)
    if not mg:
      break
    try:
      dt = arrow.Arrow(int(mg.groups()[1]), int(mg.groups()[2]), int(mg.groups()[3]), tzinfo=GC.Values[GC.TIMEZONE])
      query = query[:mg.start(2)]+str(dt.int_timestamp)+query[mg.end(4):]
    except ValueError:
      pass
    pos = mg.end()
  parameters['query'] = query

def _finalizeMessageSelectParameters(parameters, queryOrIdsRequired):
  if parameters['query']:
    if parameters['labelGroupOpen']:
      parameters['query'] += ')'
    if parameters['queryTimes']:
      for queryTimeName, queryTimeValue in parameters['queryTimes'].items():
        parameters['query'] = parameters['query'].replace(f'#{queryTimeName}#', queryTimeValue)
    _mapMessageQueryDates(parameters)
  elif queryOrIdsRequired and parameters['messageEntity'] is None and not parameters['labelIds']:
    missingArgumentExit('query|matchlabel|ids|labelids')
  else:
    parameters['query'] = None
  parameters['maxItems'] = parameters['maxToProcess'] if parameters['quick'] and not parameters['labelMatchPattern'] else 0

# gam <UserTypeEntity> archive messages <GroupItem>
#	(((query <QueryGmail> [querytime<String> <Date>]*) (matchlabel <LabelName>) [or|and])+
#	 [labelids <LabelIDList>]
#	 [quick|notquick] [doit] [max_to_archive <Number>])|(ids <MessageIDEntity>)
#	[csv [todrive <ToDriveAttribute>*]]
def archiveMessages(users):
  def _processMessageFailed(user, idsList, errMsg, j=0, jcount=0):
    if not csvPF:
      entityActionFailedWarning([Ent.USER, user, entityType, idsList], errMsg, j, jcount)
    else:
      csvPF.WriteRow({'User': user, entityHeader: idsList, 'action': Act.Failed(), 'error': errMsg})

  entityType = Ent.MESSAGE
  entityHeader = 'id'
  parameters = _initMessageThreadParameters(entityType, False, 0)
  group = getEmailAddress()
  csvPF = None
  while Cmd.ArgumentsRemaining():
    myarg = getArgument()
    if _getMessageSelectParameters(myarg, parameters):
      pass
    elif myarg == 'csv':
      csvPF = CSVPrintFile(['User', entityHeader, 'action', 'error'])
    elif csvPF and myarg == 'todrive':
      csvPF.GetTodriveParameters()
    else:
      unknownArgumentExit()
  _finalizeMessageSelectParameters(parameters, False)
  if not GC.Values[GC.USER_SERVICE_ACCOUNT_ACCESS_ONLY]:
    gm = buildGAPIObject(API.GROUPSMIGRATION)
    cd = buildGAPIObject(API.DIRECTORY)
    try:
      group = callGAPI(cd.groups(), 'get',
                       throwReasons=GAPI.GROUP_GET_THROW_REASONS,
                       groupKey=group, fields='email')['email']
    except (GAPI.groupNotFound, GAPI.domainNotFound, GAPI.domainCannotUseApis, GAPI.forbidden, GAPI.badRequest):
      entityDoesNotExistExit(Ent.GROUP, group)
  i, count, users = getEntityArgument(users)
  for user in users:
    i += 1
    user, gmail, messageIds = _validateUserGetMessageIds(user, i, count, parameters['messageEntity'])
    if not gmail:
      continue
    if GC.Values[GC.USER_SERVICE_ACCOUNT_ACCESS_ONLY]:
      _, gm = buildGAPIServiceObject(API.GROUPSMIGRATION, user, i, count)
      if not gm:
        continue
    service = gmail.users().messages()
    try:
      if parameters['messageEntity'] is None:
        printGettingAllEntityItemsForWhom(entityType, user, i, count, query=parameters['query'])
        listResult = callGAPIpages(service, 'list', parameters['listType'],
                                   pageMessage=getPageMessageForWhom(), maxItems=parameters['maxItems'],
                                   throwReasons=GAPI.GMAIL_THROW_REASONS+GAPI.GMAIL_LIST_THROW_REASONS,
                                   userId='me', q=parameters['query'], labelIds=parameters['labelIds'],
                                   fields=parameters['fields'],
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
      entityNumEntitiesActionNotPerformedWarning([Ent.USER, user], entityType, jcount, Msg.NO_ENTITIES_MATCHED.format(Ent.Plural(entityType)), i, count)
      setSysExitRC(NO_ENTITIES_FOUND_RC)
      continue
    if parameters['messageEntity'] is None:
      if parameters['maxToProcess'] and jcount > parameters['maxToProcess']:
        entityNumEntitiesActionNotPerformedWarning([Ent.USER, user], entityType, jcount, Msg.COUNT_N_EXCEEDS_MAX_TO_PROCESS_M.format(jcount, Act.ToPerform(), parameters['maxToProcess']), i, count)
        continue
      if not parameters['doIt']:
        entityNumEntitiesActionNotPerformedWarning([Ent.USER, user], entityType, jcount, Msg.USE_DOIT_ARGUMENT_TO_PERFORM_ACTION, i, count)
        continue
    entityPerformActionNumItems([Ent.USER, user], jcount, entityType, i, count)
    Ind.Increment()
    j = 0
    for messageId in messageIds:
      j += 1
      try:
        message = callGAPI(service, 'get',
                           throwReasons=GAPI.GMAIL_THROW_REASONS+[GAPI.NOT_FOUND, GAPI.INVALID_MESSAGE_ID],
                           userId='me', id=messageId, format='raw')
        stream = io.BytesIO()
        stream.write(base64.urlsafe_b64decode(str(message['raw'])))
        try:
          callGAPI(gm.archive(), 'insert',
                   throwReasons=GAPI.GMAIL_THROW_REASONS+[GAPI.NOT_FOUND, GAPI.BAD_REQUEST, GAPI.INVALID,
                                                          GAPI.FAILED_PRECONDITION, GAPI.FORBIDDEN],
                   retryReasons=[GAPI.NOT_FOUND],
                   groupId=group, media_body=googleapiclient.http.MediaIoBaseUpload(stream, mimetype='message/rfc822', resumable=True))
          if not csvPF:
            entityActionPerformed([Ent.USER, user, entityType, messageId], j, jcount)
          else:
            csvPF.WriteRow({'User': user, entityHeader: messageId, 'action': Act.Performed()})
        except GAPI.serviceNotAvailable:
          userGmailServiceNotEnabledWarning(user, i, count)
          break
        except GAPI.notFound as e:
          _processMessageFailed(user, messageId, str(e), j, jcount)
          break
        except (GAPI.badRequest, GAPI.invalid, GAPI.failedPrecondition, GAPI.forbidden,
                googleapiclient.errors.MediaUploadSizeError) as e:
          _processMessageFailed(user, messageId, str(e), j, jcount)
      except GAPI.serviceNotAvailable:
        userGmailServiceNotEnabledWarning(user, i, count)
        break
      except (GAPI.notFound, GAPI.invalidMessageId) as e:
        _processMessageFailed(user, messageId, str(e), j, jcount)
    Ind.Decrement()
  if csvPF:
    csvPF.writeCSVfile(f'{Act.ToPerform()} Messages')

def _processMessagesThreads(users, entityType):
  def _processMessageFailed(user, idsList, errMsg, j=0, jcount=0):
    if not csvPF:
      entityActionFailedWarning([Ent.USER, user, entityType, idsList], errMsg, j, jcount)
    else:
      csvPF.WriteRow({'User': user, entityHeader: idsList, 'action': Act.Failed(), 'error': errMsg})

  def _batchDeleteModifyMessages(gmail, function, user, jcount, messageIds, body):
    mcount = 0
    bcount = min(jcount-mcount, GC.Values[GC.MESSAGE_BATCH_SIZE])
    while bcount > 0:
      body['ids'] = messageIds[mcount:mcount+bcount]
      idsCount = min(5, bcount)
      idsList = ','.join(body['ids'][0:idsCount])
      if bcount > 5:
        idsList += ',...'
      try:
        callGAPI(gmail.users().messages(), function,
                 throwReasons=GAPI.GMAIL_THROW_REASONS+[GAPI.INVALID_MESSAGE_ID, GAPI.INVALID, GAPI.INVALID_ARGUMENT,
                                                        GAPI.FAILED_PRECONDITION, GAPI.PERMISSION_DENIED, GAPI.QUOTA_EXCEEDED],
                 userId='me', body=body)
        for messageId in body['ids']:
          mcount += 1
          if not csvPF:
            entityActionPerformed([Ent.USER, user, entityType, messageId], mcount, jcount)
          else:
            csvPF.WriteRow({'User': user, entityHeader: messageId, 'action': Act.Performed()})
      except GAPI.serviceNotAvailable:
        mcount += bcount
      except (GAPI.invalid, GAPI.invalidArgument, GAPI.permissionDenied, GAPI.quotaExceeded) as e:
        _processMessageFailed(user, idsList, f'{str(e)} ({mcount+1}-{mcount+bcount}/{jcount})')
        mcount += bcount
      except GAPI.invalidMessageId:
        _processMessageFailed(user, idsList, f'{Msg.INVALID_MESSAGE_ID} ({mcount+1}-{mcount+bcount}/{jcount})')
        mcount += bcount
      except GAPI.failedPrecondition:
        _processMessageFailed(user, idsList, f'{Msg.FAILED_PRECONDITION} ({mcount+1}-{mcount+bcount}/{jcount})')
        mcount += bcount
      bcount = min(jcount-mcount, GC.Values[GC.MESSAGE_BATCH_SIZE])

  _GMAIL_ERROR_REASON_TO_MESSAGE_MAP = {GAPI.NOT_FOUND: Msg.DOES_NOT_EXIST,
                                        GAPI.INVALID_MESSAGE_ID: Msg.INVALID_MESSAGE_ID,
                                        GAPI.FAILED_PRECONDITION: Msg.FAILED_PRECONDITION,
                                        GAPI.QUOTA_EXCEEDED: Msg.QUOTA_EXCEEDED}

  def _callbackProcessMessage(request_id, _, exception):
    ri = request_id.splitlines()
    if exception is None:
      if not csvPF:
        entityActionPerformed([Ent.USER, ri[RI_ENTITY], entityType, ri[RI_ITEM]], int(ri[RI_J]), int(ri[RI_JCOUNT]))
      else:
        csvPF.WriteRow({'User': ri[RI_ENTITY], entityHeader: ri[RI_ITEM], 'action': Act.Performed()})
    else:
      http_status, reason, message = checkGAPIError(exception)
      _processMessageFailed(ri[RI_ENTITY], ri[RI_ITEM],
                            getHTTPError(_GMAIL_ERROR_REASON_TO_MESSAGE_MAP, http_status, reason, message),
                            int(ri[RI_J]), int(ri[RI_JCOUNT]))

  def _batchProcessMessagesThreads(service, function, user, jcount, messageIds, **kwargs):
    svcargs = dict([('userId', 'me'), ('id', None), ('fields', '')]+list(kwargs.items())+GM.Globals[GM.EXTRA_ARGS_LIST])
    method = getattr(service, function)
    dbatch = gmail.new_batch_http_request(callback=_callbackProcessMessage)
    bcount = 0
    j = 0
    for messageId in messageIds:
      j += 1
      svcparms = svcargs.copy()
      svcparms['id'] = messageId
      dbatch.add(method(**svcparms), request_id=batchRequestID(user, 0, 0, j, jcount, svcparms['id']))
      bcount += 1
      if bcount == GC.Values[GC.EMAIL_BATCH_SIZE]:
        executeBatch(dbatch)
        dbatch = gmail.new_batch_http_request(callback=_callbackProcessMessage)
        bcount = 0
    if bcount > 0:
      dbatch.execute()

  parameters = _initMessageThreadParameters(entityType, False, 1)
  includeSpamTrash = False
  function = {Act.DELETE: 'delete', Act.MODIFY: 'modify', Act.SPAM: 'spam', Act.TRASH: 'trash', Act.UNTRASH: 'untrash'}[Act.Get()]
  labelNameMap = {}
  addLabelNames = []
  addLabelIds = []
  removeLabelNames = []
  removeLabelIds = []
  csvPF = None
  entityHeader = 'id' if entityType == Ent.MESSAGE else 'threadId'
  while Cmd.ArgumentsRemaining():
    myarg = getArgument()
    if _getMessageSelectParameters(myarg, parameters):
      pass
    elif (function == 'modify') and (myarg == 'addlabel'):
      addLabelNames.append(getString(Cmd.OB_LABEL_NAME))
    elif (function == 'modify') and (myarg == 'removelabel'):
      removeLabelNames.append(getString(Cmd.OB_LABEL_NAME))
    elif myarg == 'csv':
      csvPF = CSVPrintFile(['User', entityHeader, 'action', 'error'])
    elif csvPF and myarg == 'todrive':
      csvPF.GetTodriveParameters()
    else:
      unknownArgumentExit()
  if function == 'modify' and not addLabelNames and not removeLabelNames:
    missingArgumentExit('(addlabel <LabelName>)|(removelabel <LabelName>)')
  _finalizeMessageSelectParameters(parameters, True)
  includeSpamTrash = Act.Get() in [Act.DELETE, Act.MODIFY, Act.UNTRASH]
  if function == 'spam':
    function = 'modify'
    addLabelIds = ['SPAM']
    removeLabelIds = ['INBOX']
  i, count, users = getEntityArgument(users)
  for user in users:
    i += 1
    user, gmail, messageIds = _validateUserGetMessageIds(user, i, count, parameters['messageEntity'])
    if not gmail:
      continue
    service = gmail.users().messages() if entityType == Ent.MESSAGE else gmail.users().threads()
    if addLabelNames or removeLabelNames:
      userGmailLabels = _getUserGmailLabels(gmail, user, i, count, 'labels(id,name,type)')
      if not userGmailLabels:
        continue
      labelNameMap = _initLabelNameMap(userGmailLabels)
      addLabelIds = _convertLabelNamesToIds(gmail, user, i, count, addLabelNames, labelNameMap, True)
      removeLabelIds = _convertLabelNamesToIds(gmail, user, i, count, removeLabelNames, labelNameMap, False)
      if not addLabelIds and not removeLabelIds:
        entityActionNotPerformedWarning([Ent.USER, user], Msg.NO_LABELS_TO_PROCESS, i, count)
        continue
    try:
      if parameters['messageEntity'] is None:
        printGettingAllEntityItemsForWhom(Ent.MESSAGE, user, i, count, query=parameters['query'])
        listResult = callGAPIpages(service, 'list', parameters['listType'],
                                   pageMessage=getPageMessageForWhom(), maxItems=parameters['maxItems'],
                                   throwReasons=GAPI.GMAIL_THROW_REASONS+GAPI.GMAIL_LIST_THROW_REASONS,
                                   userId='me', q=parameters['query'], labelIds=parameters['labelIds'],
                                   fields=parameters['fields'], includeSpamTrash=includeSpamTrash,
                                   maxResults=GC.Values[GC.MESSAGE_MAX_RESULTS])
        messageIds = [message['id'] for message in listResult]
      else:
        # Need to get authorization set up for batch
        callGAPI(gmail.users(), 'getProfile',
                 throwReasons=GAPI.GMAIL_THROW_REASONS+GAPI.GMAIL_LIST_THROW_REASONS,
                 userId='me', fields='')
    except (GAPI.failedPrecondition, GAPI.permissionDenied, GAPI.invalid, GAPI.invalidArgument) as e:
      entityActionFailedWarning([Ent.USER, user], str(e), i, count)
      continue
    except GAPI.serviceNotAvailable:
      userGmailServiceNotEnabledWarning(user, i, count)
      continue
    jcount = len(messageIds)
    if jcount == 0:
      entityNumEntitiesActionNotPerformedWarning([Ent.USER, user], entityType, jcount, Msg.NO_ENTITIES_MATCHED.format(Ent.Plural(entityType)), i, count)
      setSysExitRC(NO_ENTITIES_FOUND_RC)
      continue
    if parameters['messageEntity'] is None:
      if parameters['maxToProcess'] and jcount > parameters['maxToProcess']:
        entityNumEntitiesActionNotPerformedWarning([Ent.USER, user], entityType, jcount,
                                                   Msg.COUNT_N_EXCEEDS_MAX_TO_PROCESS_M.format(jcount, Act.ToPerform(), parameters['maxToProcess']),
                                                   i, count)
        continue
      if not parameters['doIt']:
        entityNumEntitiesActionNotPerformedWarning([Ent.USER, user], entityType, jcount, Msg.USE_DOIT_ARGUMENT_TO_PERFORM_ACTION, i, count)
        continue
    entityPerformActionNumItems([Ent.USER, user], jcount, entityType, i, count)
    Ind.Increment()
    if function == 'delete' and entityType == Ent.MESSAGE:
      _batchDeleteModifyMessages(gmail, 'batchDelete', user, jcount, messageIds, {'ids': []})
    elif function == 'modify' and entityType == Ent.MESSAGE:
      _batchDeleteModifyMessages(gmail, 'batchModify', user, jcount, messageIds, {'ids': [], 'addLabelIds': addLabelIds, 'removeLabelIds': removeLabelIds})
    else:
      if addLabelIds or removeLabelIds:
        kwargs = {'body': {'addLabelIds': addLabelIds, 'removeLabelIds': removeLabelIds}}
      else:
        kwargs = {}
      _batchProcessMessagesThreads(service, function, user, jcount, messageIds, **kwargs)
    Ind.Decrement()
  if csvPF:
    csvPF.writeCSVfile(f'{Act.ToPerform()} Messages')

# gam <UserTypeEntity> delete message|messages
#	(((query <QueryGmail> [querytime<String> <Date>]*) (matchlabel <LabelName>) [or|and])+
#	 [labelids <LabelIDList>]
#	 [quick|notquick] [doit] [max_to_delete <Number>])|(ids <MessageIDEntity>)
#	[csv [todrive <ToDriveAttribute>*]]
# gam <UserTypeEntity> modify message|messages
#	(((query <QueryGmail> [querytime<String> <Date>]*) (matchlabel <LabelName>) [or|and])+
#	 [labelids <LabelIDList>]
#	 [quick|notquick] [doit] [max_to_modify <Number>])|(ids <MessageIDEntity>)
#	(addlabel <LabelName>)* (removelabel <LabelName>)*
#	[csv [todrive <ToDriveAttribute>*]]
# gam <UserTypeEntity> spam message|messages
#	(((query <QueryGmail> [querytime<String> <Date>]*) (matchlabel <LabelName>) [or|and])+
#	 [labelids <LabelIDList>]
#	 [quick|notquick] [doit] [max_to_spam <Number>])|(ids <MessageIDEntity>)
#	[csv [todrive <ToDriveAttribute>*]]
# gam <UserTypeEntity> trash message|messages
#	(((query <QueryGmail> [querytime<String> <Date>]*) (matchlabel <LabelName>) [or|and])+
#	 [labelids <LabelIDList>]
#	 [quick|notquick] [doit] [max_to_trash <Number>])|(ids <MessageIDEntity>)
#	[csv [todrive <ToDriveAttribute>*]]
# gam <UserTypeEntity> untrash message|messages
#	(((query <QueryGmail> [querytime<String> <Date>]*) (matchlabel <LabelName>) [or|and])+
#	 [labelids <LabelIDList>]
#	 [quick|notquick] [doit] [max_to_untrash <Number>])|(ids <MessageIDEntity>)
#	[csv [todrive <ToDriveAttribute>*]]
def processMessages(users):
  _processMessagesThreads(users, Ent.MESSAGE)

# gam <UserTypeEntity> delete thread|threads
#	(((query <QueryGmail> [querytime<String> <Date>]*) (matchlabel <LabelName>) [or|and])+
#	 [labelids <LabelIDList>]
#	 [quick|notquick] [doit] [max_to_delete <Number>])|(ids <ThreadIDEntity>)
#	[csv [todrive <ToDriveAttribute>*]]
# gam <UserTypeEntity> modify thread|threads
#	(((query <QueryGmail> [querytime<String> <Date>]*) (matchlabel <LabelName>) [or|and])+
#	 [labelids <LabelIDList>]
#	 [quick|notquick] [doit] [max_to_modify <Number>])|(ids <ThreadIDEntity>)
#	(addlabel <LabelName>)* (removelabel <LabelName>)*
#	[csv [todrive <ToDriveAttribute>*]]
# gam <UserTypeEntity> spam thread|threads
#	(((query <QueryGmail> [querytime<String> <Date>]*) (matchlabel <LabelName>) [or|and])+
#	 [labelids <LabelIDList>]
#	 [quick|notquick] [doit] [max_to_spam <Number>])|(ids <ThreadIDEntity>)
#	[csv [todrive <ToDriveAttribute>*]]
# gam <UserTypeEntity> trash thread|threads
#	(((query <QueryGmail> [querytime<String> <Date>]*) (matchlabel <LabelName>) [or|and])+
#	 [labelids <LabelIDList>]
#	 [quick|notquick] [doit] [max_to_trash <Number>])|(ids <ThreadIDEntity>)
#	[csv [todrive <ToDriveAttribute>*]]
# gam <UserTypeEntity> untrash thread|threads
#	(((query <QueryGmail> [querytime<String> <Date>]*) (matchlabel <LabelName>) [or|and])+
#	 [labelids <LabelIDList>]
#	 [quick|notquick] [doit] [max_to_untrash <Number>])|(ids <ThreadIDEntity>)
#	[csv [todrive <ToDriveAttribute>*]]
def processThreads(users):
  _processMessagesThreads(users, Ent.THREAD)

def exportMessagesThreads(users, entityType):
  parameters = _initMessageThreadParameters(entityType, False, 1)
  targetFolderPattern = GC.Values[GC.DRIVE_DIR]
  targetNamePattern = None
  includeSpamTrash = overwrite = False
  while Cmd.ArgumentsRemaining():
    myarg = getArgument()
    if _getMessageSelectParameters(myarg, parameters):
      pass
    elif myarg == 'targetfolder':
      targetFolderPattern = setFilePath(getString(Cmd.OB_FILE_PATH), GC.DRIVE_DIR)
    elif myarg == 'targetname':
      targetNamePattern = getString(Cmd.OB_FILE_NAME)
    elif myarg == 'overwrite':
      overwrite = getBoolean()
    else:
      unknownArgumentExit()
  _finalizeMessageSelectParameters(parameters, True)
  i, count, users = getEntityArgument(users)
  for user in users:
    i += 1
    user, gmail, entityIds = _validateUserGetMessageIds(user, i, count, parameters['messageEntity'])
    if not gmail:
      continue
    _, userName, _ = splitEmailAddressOrUID(user)
    targetFolder = _substituteForUser(targetFolderPattern, user, userName)
    if not os.path.isdir(targetFolder):
      os.makedirs(targetFolder)
    targetName = _substituteForUser(targetNamePattern, user, userName) if targetNamePattern else None
    service = gmail.users().messages() if entityType == Ent.MESSAGE else gmail.users().threads()
    try:
      if parameters['messageEntity'] is None:
        printGettingAllEntityItemsForWhom(entityType, user, i, count, query=parameters['query'])
        listResult = callGAPIpages(service, 'list', parameters['listType'],
                                   pageMessage=getPageMessageForWhom(), maxItems=parameters['maxItems'],
                                   throwReasons=GAPI.GMAIL_THROW_REASONS+GAPI.GMAIL_LIST_THROW_REASONS,
                                   userId='me', q=parameters['query'], labelIds=parameters['labelIds'],
                                   fields=parameters['fields'], includeSpamTrash=includeSpamTrash,
                                   maxResults=GC.Values[GC.MESSAGE_MAX_RESULTS])
        entityIds = [entity['id'] for entity in listResult]
    except (GAPI.failedPrecondition, GAPI.permissionDenied, GAPI.invalid, GAPI.invalidArgument) as e:
      entityActionFailedWarning([Ent.USER, user], str(e), i, count)
      continue
    except GAPI.serviceNotAvailable:
      userGmailServiceNotEnabledWarning(user, i, count)
      continue
    jcount = len(entityIds)
    if jcount == 0:
      entityNumEntitiesActionNotPerformedWarning([Ent.USER, user], entityType, jcount, Msg.NO_ENTITIES_MATCHED.format(Ent.Plural(entityType)), i, count)
      setSysExitRC(NO_ENTITIES_FOUND_RC)
      continue
    if parameters['messageEntity'] is None:
      if parameters['maxToProcess'] and jcount > parameters['maxToProcess']:
        entityNumEntitiesActionNotPerformedWarning([Ent.USER, user], entityType, jcount, Msg.COUNT_N_EXCEEDS_MAX_TO_PROCESS_M.format(jcount, Act.ToPerform(), parameters['maxToProcess']), i, count)
        continue
    entityPerformActionNumItems([Ent.USER, user], jcount, entityType, i, count)
    Ind.Increment()
    j = 0
    for entityId in entityIds:
      j += 1
      if entityType == Ent.THREAD:
        try:
          result = callGAPI(gmail.users().threads(), 'get',
                             throwReasons=GAPI.GMAIL_THROW_REASONS+[GAPI.NOT_FOUND, GAPI.INVALID_ARGUMENT],
                             userId='me', id=entityId, fields='messages(id)')
          messageIds = [message['id'] for message in result['messages']]
          kcount = len(messageIds)
          entityPerformActionNumItems([Ent.USER, user, Ent.THREAD, entityId], kcount, Ent.MESSAGE, j, jcount)
          Ind.Increment()
          k = 0
        except GAPI.serviceNotAvailable:
          userGmailServiceNotEnabledWarning(user, i, count)
          break
        except (GAPI.notFound, GAPI.invalidArgument) as e:
          entityActionFailedWarning([Ent.USER, user, Ent.THREAD, entityId], str(e), j, jcount)
          continue
      else:
        messageIds = [entityId]
        kcount = jcount
        k = j-1
      for messageId in messageIds:
        k += 1
        try:
          result = callGAPI(gmail.users().messages(), 'get',
                            throwReasons=GAPI.GMAIL_THROW_REASONS+[GAPI.NOT_FOUND, GAPI.INVALID_MESSAGE_ID],
                            userId='me', id=messageId, format='raw')
          if targetName:
            msgName = targetName.replace('#id#', messageId)
          else:
            msgName = f'Msg-{messageId}.eml'
          filename, _ = uniqueFilename(targetFolder, msgName, overwrite)
          status, e = writeFileReturnError(filename, base64.urlsafe_b64decode(str(result['raw'])), mode='wb')
          if status:
            entityActionPerformed([Ent.MESSAGE, filename])
          else:
            entityActionFailedWarning([Ent.MESSAGE, filename], str(e))
        except GAPI.serviceNotAvailable:
          userGmailServiceNotEnabledWarning(user, i, count)
          break
        except (GAPI.notFound, GAPI.invalidMessageId) as e:
          entityActionFailedWarning([Ent.USER, user, Ent.MESSAGE, messageId], str(e), k, kcount)
          continue
      if entityType == Ent.THREAD:
        Ind.Decrement()
    Ind.Decrement()

# gam <UserTypeEntity> export message|messages
#	(((query <QueryGmail> [querytime<String> <Date>]*) (matchlabel <LabelName>) [or|and])+ [quick|notquick] [max_to_export <Number>])|(ids <MessageIDEntity>)
#	[targetfolder <FilePath>] [targetname <FileName>] [overwrite [<Boolean>]]
def exportMessages(users):
  exportMessagesThreads(users, Ent.MESSAGE)

# gam <UserTypeEntity> export thread|threads
#	(((query <QueryGmail> [querytime<String> <Date>]*) (matchlabel <LabelName>) [or|and])+ [quick|notquick] [max_to_export <Number>])|(ids <ThreadIDEntity>)
#	[targetfolder <FilePath>] [targetname <FileName>] [overwrite [<Boolean>]]
def exportThreads(users):
  exportMessagesThreads(users, Ent.THREAD)

HEADER_ENCODE_PATTERN = re.compile(r'=\?([^?]*?)\?[qQbB]\?(.*?)\?=', re.VERBOSE | re.MULTILINE)

def _decodeHeader(header):
  header = header.encode(UTF8, 'replace').decode(UTF8)
  while True:
    mg = HEADER_ENCODE_PATTERN.search(header)
    if not mg:
      return header
    try:
      header = header[:mg.start()]+decode_header(mg.group())[0][0].decode(mg.group(1))+header[mg.end():]
    except LookupError:
      stderrWarningMsg(Msg.INVALID_CHARSET.format(mg.group(1)))
      return header

# gam <UserTypeEntity> forward message|messages [recipient|to] <RecipientEntity>
#	(((query <QueryGmail> [querytime<String> <Date>]*) (matchlabel <LabelName>) [or|and])+ [quick|notquick] [doit] [max_to_forward <Number>])|(ids <MessageIDEntity>)
#	[subject <String>] [addorigfieldstosubject [<Boolean>]] [altcharset <String>]
# gam <UserTypeEntity> forward thread|threads [recipient|to] <RecipientEntity>
#	(((query <QueryGmail> [querytime<String> <Date>]*) (matchlabel <LabelName>) [or|and])+ [quick|notquick] [doit] [max_to_forward <Number>])|(ids <ThreadIDEntity>)
#	[subject <String>] [addorigfieldstosubject [<Boolean>]] [altcharset <String>]
def forwardMessagesThreads(users, entityType):
  checkArgumentPresent({'recipient', 'recipients', 'to'})
  recipients = getRecipients()
  parameters = _initMessageThreadParameters(entityType, False, 1)
  addOriginalFieldsToSubject = includeSpamTrash = False
  subject = ''
  encodings = [UTF8]
  while Cmd.ArgumentsRemaining():
    myarg = getArgument()
    if _getMessageSelectParameters(myarg, parameters):
      pass
    elif myarg == 'subject':
      subject = getString(Cmd.OB_STRING)
    elif myarg == 'addorigfieldstosubject':
      addOriginalFieldsToSubject = getBoolean()
    elif myarg == 'altcharset':
      encodings.append(getString(Cmd.OB_CHAR_SET))
    else:
      unknownArgumentExit()
  _finalizeMessageSelectParameters(parameters, True)
  msgTo = ','.join(recipients)
  i, count, users = getEntityArgument(users)
  for user in users:
    i += 1
    user, gmail, entityIds = _validateUserGetMessageIds(user, i, count, parameters['messageEntity'])
    if not gmail:
      continue
    service = gmail.users().messages() if entityType == Ent.MESSAGE else gmail.users().threads()
    if parameters['messageEntity'] is None:
      try:
        printGettingAllEntityItemsForWhom(entityType, user, i, count, query=parameters['query'])
        listResult = callGAPIpages(service, 'list', parameters['listType'],
                                   pageMessage=getPageMessageForWhom(), maxItems=parameters['maxItems'],
                                   throwReasons=GAPI.GMAIL_THROW_REASONS+GAPI.GMAIL_LIST_THROW_REASONS,
                                   userId='me', q=parameters['query'], labelIds=parameters['labelIds'],
                                   fields=parameters['fields'], includeSpamTrash=includeSpamTrash,
                                   maxResults=GC.Values[GC.MESSAGE_MAX_RESULTS])
        entityIds = [entity['id'] for entity in listResult]
      except (GAPI.failedPrecondition, GAPI.permissionDenied, GAPI.invalid, GAPI.invalidArgument) as e:
        entityActionFailedWarning([Ent.USER, user], str(e), i, count)
        continue
      except GAPI.serviceNotAvailable:
        userGmailServiceNotEnabledWarning(user, i, count)
        continue
    jcount = len(entityIds)
    if jcount == 0:
      entityNumEntitiesActionNotPerformedWarning([Ent.USER, user], entityType, jcount, Msg.NO_ENTITIES_MATCHED.format(Ent.Plural(entityType)), i, count)
      setSysExitRC(NO_ENTITIES_FOUND_RC)
      continue
    if parameters['messageEntity'] is None:
      if parameters['maxToProcess'] and jcount > parameters['maxToProcess']:
        entityNumEntitiesActionNotPerformedWarning([Ent.USER, user], entityType, jcount, Msg.COUNT_N_EXCEEDS_MAX_TO_PROCESS_M.format(jcount, Act.ToPerform(), parameters['maxToProcess']), i, count)
        continue
      if not parameters['doIt']:
        entityNumEntitiesActionNotPerformedWarning([Ent.USER, user], entityType, jcount, Msg.USE_DOIT_ARGUMENT_TO_PERFORM_ACTION, i, count)
        continue
    entityPerformActionNumItems([Ent.USER, user], jcount, entityType, i, count)
    Ind.Increment()
    j = 0
    for entityId in entityIds:
      j += 1
      if entityType == Ent.THREAD:
        try:
          result = callGAPI(gmail.users().threads(), 'get',
                             throwReasons=GAPI.GMAIL_THROW_REASONS+[GAPI.NOT_FOUND, GAPI.INVALID_MESSAGE_ID],
                             userId='me', id=entityId, fields='messages(id)')
          messageIds = [message['id'] for message in result['messages']]
          kcount = len(messageIds)
          entityPerformActionNumItems([Ent.USER, user, Ent.THREAD, entityId], kcount, Ent.MESSAGE, j, jcount)
          Ind.Increment()
          k = 0
        except GAPI.serviceNotAvailable:
          userGmailServiceNotEnabledWarning(user, i, count)
          break
        except (GAPI.notFound, GAPI.invalidMessageId) as e:
          entityActionFailedWarning([Ent.USER, user, Ent.THREAD, entityId], str(e), j, jcount)
          continue
      else:
        messageIds = [entityId]
        kcount = jcount
        k = j-1
      for messageId in messageIds:
        k += 1
        try:
          result = callGAPI(gmail.users().messages(), 'get',
                            throwReasons=GAPI.GMAIL_THROW_REASONS+[GAPI.NOT_FOUND, GAPI.INVALID_MESSAGE_ID],
                            userId='me', id=messageId, format='raw')
          for encoding in encodings:
            try:
              message = message_from_string(base64.urlsafe_b64decode(str(result['raw'])).decode(encoding), policy=policySMTP)
              break
            except UnicodeDecodeError as e:
              errMsg = str(e)
          else:
            entityActionNotPerformedWarning([Ent.RECIPIENT, msgTo, entityType, messageId], errMsg, k, kcount)
            continue
          if not subject:
            msgSubject = f"Fwd: {_decodeHeader(message['Subject'])}"
          else:
            msgSubject = f"Subject: {subject}"
          if addOriginalFieldsToSubject:
            msgSubject += ' (Original'
            for header in ['From', 'To', 'Date']:
              if header in message:
                msgSubject += f' {header}: {message[header]}'
            msgSubject += ')'
          for header in ['To', 'Cc', 'Bcc', 'Subject']:
            if header in message:
              del message[header]
          message['To'] = msgTo
          message['Subject'] = msgSubject
          try:
            result = callGAPI(gmail.users().messages(), 'send',
                              throwReasons=[GAPI.SERVICE_NOT_AVAILABLE, GAPI.AUTH_ERROR, GAPI.DOMAIN_POLICY,
                                            GAPI.INVALID, GAPI.INVALID_ARGUMENT, GAPI.FORBIDDEN, GAPI.PERMISSION_DENIED],
                              userId='me', body={'raw': base64.urlsafe_b64encode(message.as_bytes()).decode(encoding)}, fields='id')
            entityActionPerformedMessage([Ent.RECIPIENT, msgTo], f"{result['id']}", k, kcount)
          except (GAPI.serviceNotAvailable, GAPI.authError, GAPI.domainPolicy,
                  GAPI.invalid, GAPI.invalidArgument, GAPI.forbidden, GAPI.permissionDenied, UnicodeEncodeError) as e:
            entityActionFailedWarning([Ent.RECIPIENT, msgTo], str(e), k, kcount)
        except GAPI.serviceNotAvailable:
          userGmailServiceNotEnabledWarning(user, i, count)
          break
        except (GAPI.notFound, GAPI.invalidMessageId) as e:
          entityActionFailedWarning([Ent.USER, user, Ent.MESSAGE, messageId], str(e), k, kcount)
          continue
      if entityType == Ent.THREAD:
        Ind.Decrement()
    Ind.Decrement()

SMTP_HEADERS_MAP = {
  'accept-language': 'Accept-Language',
  'alternate-recipient': 'Alternate-Recipient',
  'autoforwarded': 'Autoforwarded',
  'autosubmitted': 'Autosubmitted',
  'bcc': 'Bcc',
  'cc': 'Cc',
  'comments': 'Comments',
  'content-alternative': 'Content-Alternative',
  'content-base': 'Content-Base',
  'content-description': 'Content-Description',
  'content-disposition': 'Content-Disposition',
  'content-duration': 'Content-Duration',
  'content-id': 'Content-ID',
  'content-identifier': 'Content-Identifier',
  'content-language': 'Content-Language',
  'content-location': 'Content-Location',
  'content-md5': 'Content-MD5',
  'content-return': 'Content-Return',
  'content-transfer-encoding': 'Content-Transfer-Encoding',
  'content-type': 'Content-Type',
  'content-features': 'Content-features',
  'conversion': 'Conversion',
  'conversion-with-loss': 'Conversion-With-Loss',
  'dl-expansion-history': 'DL-Expansion-History',
  'date': 'Date',
  'deferred-delivery': 'Deferred-Delivery',
  'delivered-to': 'Delivered-To',
  'delivery-date': 'Delivery-Date',
  'discarded-x400-ipms-extensions': 'Discarded-X400-IPMS-Extensions',
  'discarded-x400-mts-extensions': 'Discarded-X400-MTS-Extensions',
  'disclose-recipients': 'Disclose-Recipients',
  'disposition-notification-options': 'Disposition-Notification-Options',
  'disposition-notification-to': 'Disposition-Notification-To',
  'encoding': 'Encoding',
  'encrypted': 'Encrypted',
  'expires': 'Expires',
  'expiry-date': 'Expiry-Date',
  'from': 'From',
  'generate-delivery-report': 'Generate-Delivery-Report',
  'importance': 'Importance',
  'in-reply-to': 'In-Reply-To',
  'incomplete-copy': 'Incomplete-Copy',
  'keywords': 'Keywords',
  'language': 'Language',
  'latest-delivery-time': 'Latest-Delivery-Time',
  'list-archive': 'List-Archive',
  'list-help': 'List-Help',
  'list-id': 'List-ID',
  'list-owner': 'List-Owner',
  'list-post': 'List-Post',
  'list-subscribe': 'List-Subscribe',
  'list-unsubscribe': 'List-Unsubscribe',
  'mime-version': 'MIME-Version',
  'message-context': 'Message-Context',
  'message-id': 'Message-ID',
  'message-type': 'Message-Type',
  'obsoletes': 'Obsoletes',
  'original-encoded-information-types': 'Original-Encoded-Information-Types',
  'original-message-id': 'Original-Message-ID',
  'originator-return-address': 'Originator-Return-Address',
  'pics-label': 'PICS-Label',
  'prevent-nondelivery-report': 'Prevent-NonDelivery-Report',
  'priority': 'Priority',
  'received': 'Received',
  'recipient': 'To',
  'references': 'References',
  'reply-by': 'Reply-By',
  'reply-to': 'Reply-To',
  'resent-bcc': 'Resent-Bcc',
  'resent-cc': 'Resent-Cc',
  'resent-date': 'Resent-Date',
  'resent-from': 'Resent-From',
  'resent-message-id': 'Resent-Message-ID',
  'resent-reply-to': 'Resent-Reply-To',
  'resent-sender': 'Resent-Sender',
  'resent-to': 'Resent-To',
  'return-path': 'Return-Path',
  'sender': 'Sender',
  'sensitivity': 'Sensitivity',
  'subject': 'Subject',
  'supersedes': 'Supersedes',
  'to': 'To',
  'x400-content-identifier': 'X400-Content-Identifier',
  'x400-content-return': 'X400-Content-Return',
  'x400-content-type': 'X400-Content-Type',
  'x400-mts-identifier': 'X400-MTS-Identifier',
  'x400-originator': 'X400-Originator',
  'x400-received': 'X400-Received',
  'x400-recipients': 'X400-Recipients',
  'x400-trace': 'X400-Trace',
  }

SMTP_ADDRESS_HEADERS = {
  'Bcc',
  'Cc',
  'Delivered-To',
  'From',
  'Reply-To',
  'Resent-Bcc',
  'Resent-Cc',
  'Resent-Reply-To',
  'Resent-Sender',
  'Resent-To',
  'Sender',
  'To',
  }

SMTP_DATE_HEADERS = {
  'date',
  'delivery-date',
  'expires',
  'expiry-date',
  'latest-delivery-time',
  'reply-by',
  'resent-date',
  }

SMTP_NAME_ADDRESS_PATTERN = re.compile(r'^(.+?)\s*<(.+)>$')

IMPORT_INSERT = {'import', 'insert'}

def _draftImportInsertMessage(users, operation):
  def _appendToHeader(header, value):
    try:
      header.append(value)
    except UnicodeDecodeError:
      header.append(value, UTF8)

  labelNameMap = {}
  addLabelNames = []
  msgHTML = msgText = ''
  msgHeaders = {}
  tagReplacements = _initTagReplacements()
  attachments = []
  embeddedImages = []
  internalDateSource = 'receivedTime'
  deleted = processForCalendar = substituteForUserInHeaders = False
  neverMarkSpam = True
  emlFile = False
  emlEncoding = 'ascii'
  while Cmd.ArgumentsRemaining():
    myarg = getArgument()
    if myarg in SMTP_HEADERS_MAP:
      if myarg == 'content-type':
        unknownArgumentExit()
      if myarg in SMTP_DATE_HEADERS:
        msgDate, _, _ = getTimeOrDeltaFromNow(True)
        msgHeaders[SMTP_HEADERS_MAP[myarg]] = formatdate(time.mktime(msgDate.timetuple()) + msgDate.microsecond/1E6, True)
        if myarg == 'date':
          internalDateSource = 'dateHeader'
      else:
        value = getString(Cmd.OB_STRING)
        if (value.find('#user#') >= 0) or (value.find('#email#') >= 0) or (value.find('#username#') >= 0):
          substituteForUserInHeaders = True
        msgHeaders[SMTP_HEADERS_MAP[myarg]] = value
    elif myarg == 'header':
      header = getString(Cmd.OB_STRING, minLen=1)
      if header.lower() == 'content-type':
        unknownArgumentExit()
      value = getString(Cmd.OB_STRING)
      if (value.find('#user#') >= 0) or (value.find('#email#') >= 0) or (value.find('#username#') >= 0):
        substituteForUserInHeaders = True
      msgHeaders[SMTP_HEADERS_MAP.get(header.lower(), header)] = value
    elif myarg in SORF_MSG_FILE_ARGUMENTS:
      if 'html' in myarg:
        msgHTML, _, _ = getStringOrFile(myarg)
      else:
        msgText, _, _ = getStringOrFile(myarg)
      emlFile = False
    elif myarg == 'emlfile':
      filename = getString(Cmd.OB_FILE_NAME)
      if checkArgumentPresent('charset'):
        emlEncoding = getString(Cmd.OB_CHAR_SET)
      filename = setFilePath(filename, GC.INPUT_DIR)
      msgText = readFile(filename, encoding=emlEncoding)
      emlFile = True
      internalDateSource = 'dateHeader'
      if checkArgumentPresent('emlutf8'):
        emlEncoding = UTF8
    elif _getTagReplacement(myarg, tagReplacements, True):
      pass
    elif operation in IMPORT_INSERT and myarg == 'addlabel':
      addLabelNames.append(getString(Cmd.OB_LABEL_NAME, minLen=1))
    elif operation in IMPORT_INSERT and myarg == 'labels':
      addLabelNames.extend(shlexSplitList(getString(Cmd.OB_LABEL_NAME_LIST)))
    elif operation in IMPORT_INSERT and myarg == 'deleted':
      deleted = getBoolean()
    elif myarg == 'attach':
      attachments.append((getFilename(), getCharSet()))
    elif myarg == 'embedimage':
      embeddedImages.append((getFilename(), getString(Cmd.OB_STRING)))
    elif operation == 'import' and myarg == 'nevermarkspam':
      neverMarkSpam = getBoolean()
    elif operation == 'import' and myarg == 'checkspam':
      neverMarkSpam = not getBoolean()
    elif operation == 'import' and myarg == 'processforcalendar':
      processForCalendar = getBoolean()
    else:
      unknownArgumentExit()
  if not msgText and not msgHTML:
    missingArgumentExit('textmessage|textfile|htmlmessage|htmlfile|empfile')
  if not emlFile:
    msgText = msgText.replace('\r', '').replace('\\n', '\n')
    msgHTML = msgHTML.replace('\r', '').replace('\\n', '<br/>')
    if not tagReplacements['tags']:
      tmpText = msgText
      tmpHTML = msgHTML
  if operation != 'draft':
    if not emlFile:
      if 'To' not in msgHeaders:
        msgHeaders['To'] = '#user#'
        substituteForUserInHeaders = True
      if 'From' not in msgHeaders:
        msgHeaders['From'] = _getAdminEmail()
    kwargs = {'internalDateSource': internalDateSource, 'deleted': deleted}
    if operation == 'import':
      function = 'import_'
      kwargs.update({'neverMarkSpam': neverMarkSpam, 'processForCalendar': processForCalendar})
    else: #'insert':
      function = 'insert'
  else:
    function = 'create'
  add_charset(UTF8, QP, QP, UTF8)
  i, count, users = getEntityArgument(users)
  for user in users:
    i += 1
    user, gmail = buildGAPIServiceObject(API.GMAIL, user, i, count)
    if not gmail:
      continue
    userName, _ = splitEmailAddress(user)
    if not emlFile:
      if tagReplacements['tags']:
        if tagReplacements['subs']:
          _getTagReplacementFieldValues(user, i, count, tagReplacements)
        tmpText = _processTagReplacements(tagReplacements, msgText)
        tmpHTML = _processTagReplacements(tagReplacements, msgHTML)
      if attachments or embeddedImages:
        if tmpText and tmpHTML:
          message = MIMEMultipart('alternative')
          textpart = MIMEText(tmpText, 'plain', UTF8)
          message.attach(textpart)
          htmlpart = MIMEText(tmpHTML, 'html', UTF8)
          message.attach(htmlpart)
        elif tmpHTML:
          message = MIMEMultipart()
          htmlpart = MIMEText(tmpHTML, 'html', UTF8)
          message.attach(htmlpart)
        else:
          message = MIMEMultipart()
          textpart = MIMEText(tmpText, 'plain', UTF8)
          message.attach(textpart)
        _addAttachmentsToMessage(message, attachments)
        _addEmbeddedImagesToMessage(message, embeddedImages)
      else:
        if tmpText and tmpHTML:
          message = MIMEMultipart('alternative')
          textpart = MIMEText(tmpText, 'plain', UTF8)
          message.attach(textpart)
          htmlpart = MIMEText(tmpHTML, 'html', UTF8)
          message.attach(htmlpart)
        elif tmpHTML:
          message = MIMEText(tmpHTML, 'html', UTF8)
        else:
          message = MIMEText(tmpText, 'plain', UTF8)
      for header, value in msgHeaders.items():
        if substituteForUserInHeaders:
          value = _substituteForUser(value, user, userName)
        message[header] = Header()
        if header in SMTP_ADDRESS_HEADERS:
          match = SMTP_NAME_ADDRESS_PATTERN.match(value.strip())
          if match:
            _appendToHeader(message[header], match.group(1))
            _appendToHeader(message[header], match.group(2))
          else:
            _appendToHeader(message[header], value)
        else:
          _appendToHeader(message[header], value)
      tmpFile = TemporaryFile(mode='w+', encoding=UTF8)
      g = Generator(tmpFile, False)
      g.flatten(message)
      tmpFile.seek(0)
      body = {'raw': base64.urlsafe_b64encode(bytes(tmpFile.read(), UTF8)).decode()}
      tmpFile.close()
    else:
      for header, value in msgHeaders.items():
        if substituteForUserInHeaders:
          value = _substituteForUser(value, user, userName)
        msgText = re.sub(fr'(?sm)\n{header}:.+?(?=[\r\n]+[a-zA-Z0-9-]+:)', f'\n{header}: {value}', msgText, 1)
      message_bytes = msgText.encode(emlEncoding)
      base64_bytes = base64.b64encode(message_bytes)
      body = {'raw': base64_bytes.decode(emlEncoding)}
    try:
      if operation != 'draft':
        if addLabelNames:
          userGmailLabels = _getUserGmailLabels(gmail, user, i, count, 'labels(id,name,type)')
          if not userGmailLabels:
            continue
          labelNameMap = _initLabelNameMap(userGmailLabels)
          body['labelIds'] = _convertLabelNamesToIds(gmail, user, i, count, addLabelNames, labelNameMap, True)
        else:
          body['labelIds'] = ['INBOX']
        result = callGAPI(gmail.users().messages(), function,
                          throwReasons=GAPI.GMAIL_THROW_REASONS+[GAPI.PERMISSION_DENIED],
                          userId='me', body=body, fields='id', **kwargs)
      else:
        result = callGAPI(gmail.users().drafts(), function,
                          throwReasons=GAPI.GMAIL_THROW_REASONS+[GAPI.INVALID_ARGUMENT, GAPI.PERMISSION_DENIED],
                          userId='me', body={'message': body}, fields='id')
      entityActionPerformed([Ent.USER, user, Ent.MESSAGE, result['id']], i, count)
    except (GAPI.invalidArgument, GAPI.permissionDenied) as e:
      entityActionFailedWarning([Ent.USER, user], str(e), i, count)
    except GAPI.serviceNotAvailable:
      userGmailServiceNotEnabledWarning(user, i, count)

# gam <UserTypeEntity> draft message
#	<MessageContent>
#	(replace <Tag> <UserReplacement>)*
#	(replaceregex <REMatchPattern> <RESubstitution> <Tag> <UserReplacement>)*
#	(<SMTPDateHeader> <Time>)* (<SMTPHeader> <String>)* (header <String> <String>)*
#	(attach <FileName> [charset <CharSet>])*
#	(embedimage <FileName> <String>)*
def draftMessage(users):
  _draftImportInsertMessage(users, 'draft')

# gam <UserTypeEntity> import message
#	<MessageContent>
#	(replace <Tag> <UserReplacement>)*
#	(replaceregex <REMatchPattern> <RESubstitution> <Tag> <UserReplacement>)*
#	(<SMTPDateHeader> <Time>)* (<SMTPHeader> <String>)* (header <String> <String>)*
#	(addlabel <LabelName>)* [labels <LabelNameList>]
#	(attach <FileName> [charset <CharSet>])*
#	(embedimage <FileName> <String>)*
#	[deleted [<Boolean>]] [nevermarkspam [<Boolean>]] [processforcalendar [<Boolean>]]
def importMessage(users):
  _draftImportInsertMessage(users, 'import')

# gam <UserTypeEntity> insert message
#	<MessageContent>
#	(replace <Tag> <UserReplacement>)*
#	(replaceregex <REMatchPattern> <RESubstitution> <Tag> <UserReplacement>)*
#	(<SMTPDateHeader> <Time>)* (<SMTPHeader> <String>)* (header <String> <String>)*
#	(addlabel <LabelName>)* [labels <LabelNameList>]
#	(attach <FileName> [charset <CharSet>])*
#	(embedimage <FileName> <String>)*
#	[deleted [<Boolean>]]
def insertMessage(users):
  _draftImportInsertMessage(users, 'insert')

