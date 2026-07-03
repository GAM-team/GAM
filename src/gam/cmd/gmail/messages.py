"""Gmail message/thread operations: select, archive, process, export, forward, draft, import.

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
    labelTemp = _getMain().getString(Cmd.OB_LABEL_NAME).lower()
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
    parameters['labelMatchPattern'] = _getMain().getREPattern(re.IGNORECASE)
  elif myarg == 'sendermatchpattern':
    parameters['senderMatchPattern'] = _getMain().getREPattern(re.IGNORECASE)
  elif myarg == 'labelids':
    parameters['labelIds'].extend(_getMain().getEntityList(Cmd.OB_LABEL_ID_LIST))
  elif myarg == 'ids':
    parameters['messageEntity'] = getUserObjectEntity(Cmd.OB_MESSAGE_ID, parameters['entityType'])
  elif myarg == 'quick':
    parameters['quick'] = True
  elif myarg == 'notquick':
    parameters['quick'] = False
  elif myarg == 'doit':
    parameters['doIt'] = True
  elif myarg in parameters['maxToKeywords']:
    parameters['maxToProcess'] = _getMain().getInteger(minVal=0)
  elif myarg == 'maxmessagesperthread':
    parameters['maxMessagesPerThread'] = _getMain().getInteger(minVal=0)
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
    _getMain().missingArgumentExit('query|matchlabel|ids|labelids')
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
      _getMain().entityActionFailedWarning([Ent.USER, user, entityType, idsList], errMsg, j, jcount)
    else:
      csvPF.WriteRow({'User': user, entityHeader: idsList, 'action': Act.Failed(), 'error': errMsg})

  entityType = Ent.MESSAGE
  entityHeader = 'id'
  parameters = _initMessageThreadParameters(entityType, False, 0)
  group = _getMain().getEmailAddress()
  csvPF = None
  while Cmd.ArgumentsRemaining():
    myarg = _getMain().getArgument()
    if _getMessageSelectParameters(myarg, parameters):
      pass
    elif myarg == 'csv':
      csvPF = _getMain().CSVPrintFile(['User', entityHeader, 'action', 'error'])
    elif csvPF and myarg == 'todrive':
      csvPF.GetTodriveParameters()
    else:
      _getMain().unknownArgumentExit()
  _finalizeMessageSelectParameters(parameters, False)
  if not GC.Values[GC.USER_SERVICE_ACCOUNT_ACCESS_ONLY]:
    gm = _getMain().buildGAPIObject(API.GROUPSMIGRATION)
    cd = _getMain().buildGAPIObject(API.DIRECTORY)
    try:
      group = _getMain().callGAPI(cd.groups(), 'get',
                       throwReasons=GAPI.GROUP_GET_THROW_REASONS,
                       groupKey=group, fields='email')['email']
    except (GAPI.groupNotFound, GAPI.domainNotFound, GAPI.domainCannotUseApis, GAPI.forbidden, GAPI.badRequest):
      _getMain().entityDoesNotExistExit(Ent.GROUP, group)
  i, count, users = _getMain().getEntityArgument(users)
  for user in users:
    i += 1
    user, gmail, messageIds = _getMain()._validateUserGetMessageIds(user, i, count, parameters['messageEntity'])
    if not gmail:
      continue
    if GC.Values[GC.USER_SERVICE_ACCOUNT_ACCESS_ONLY]:
      _, gm = _getMain().buildGAPIServiceObject(API.GROUPSMIGRATION, user, i, count)
      if not gm:
        continue
    service = gmail.users().messages()
    try:
      if parameters['messageEntity'] is None:
        _getMain().printGettingAllEntityItemsForWhom(entityType, user, i, count, query=parameters['query'])
        listResult = _getMain().callGAPIpages(service, 'list', parameters['listType'],
                                   pageMessage=_getMain().getPageMessageForWhom(), maxItems=parameters['maxItems'],
                                   throwReasons=GAPI.GMAIL_THROW_REASONS+GAPI.GMAIL_LIST_THROW_REASONS,
                                   userId='me', q=parameters['query'], labelIds=parameters['labelIds'],
                                   fields=parameters['fields'],
                                   maxResults=GC.Values[GC.MESSAGE_MAX_RESULTS])
        messageIds = [message['id'] for message in listResult]
    except (GAPI.failedPrecondition, GAPI.permissionDenied, GAPI.invalid, GAPI.invalidArgument) as e:
      _getMain().entityActionFailedWarning([Ent.USER, user], str(e), i, count)
      continue
    except GAPI.serviceNotAvailable:
      _getMain().userGmailServiceNotEnabledWarning(user, i, count)
      continue
    jcount = len(messageIds)
    if jcount == 0:
      _getMain().entityNumEntitiesActionNotPerformedWarning([Ent.USER, user], entityType, jcount, Msg.NO_ENTITIES_MATCHED.format(Ent.Plural(entityType)), i, count)
      _getMain().setSysExitRC(_getMain().NO_ENTITIES_FOUND_RC)
      continue
    if parameters['messageEntity'] is None:
      if parameters['maxToProcess'] and jcount > parameters['maxToProcess']:
        _getMain().entityNumEntitiesActionNotPerformedWarning([Ent.USER, user], entityType, jcount, Msg.COUNT_N_EXCEEDS_MAX_TO_PROCESS_M.format(jcount, Act.ToPerform(), parameters['maxToProcess']), i, count)
        continue
      if not parameters['doIt']:
        _getMain().entityNumEntitiesActionNotPerformedWarning([Ent.USER, user], entityType, jcount, Msg.USE_DOIT_ARGUMENT_TO_PERFORM_ACTION, i, count)
        continue
    _getMain().entityPerformActionNumItems([Ent.USER, user], jcount, entityType, i, count)
    Ind.Increment()
    j = 0
    for messageId in messageIds:
      j += 1
      try:
        message = _getMain().callGAPI(service, 'get',
                           throwReasons=GAPI.GMAIL_THROW_REASONS+[GAPI.NOT_FOUND, GAPI.INVALID_MESSAGE_ID],
                           userId='me', id=messageId, format='raw')
        stream = io.BytesIO()
        stream.write(base64.urlsafe_b64decode(str(message['raw'])))
        try:
          _getMain().callGAPI(gm.archive(), 'insert',
                   throwReasons=GAPI.GMAIL_THROW_REASONS+[GAPI.NOT_FOUND, GAPI.BAD_REQUEST, GAPI.INVALID,
                                                          GAPI.FAILED_PRECONDITION, GAPI.FORBIDDEN],
                   retryReasons=[GAPI.NOT_FOUND],
                   groupId=group, media_body=googleapiclient.http.MediaIoBaseUpload(stream, mimetype='message/rfc822', resumable=True))
          if not csvPF:
            _getMain().entityActionPerformed([Ent.USER, user, entityType, messageId], j, jcount)
          else:
            csvPF.WriteRow({'User': user, entityHeader: messageId, 'action': Act.Performed()})
        except GAPI.serviceNotAvailable:
          _getMain().userGmailServiceNotEnabledWarning(user, i, count)
          break
        except GAPI.notFound as e:
          _processMessageFailed(user, messageId, str(e), j, jcount)
          break
        except (GAPI.badRequest, GAPI.invalid, GAPI.failedPrecondition, GAPI.forbidden,
                googleapiclient.errors.MediaUploadSizeError) as e:
          _processMessageFailed(user, messageId, str(e), j, jcount)
      except GAPI.serviceNotAvailable:
        _getMain().userGmailServiceNotEnabledWarning(user, i, count)
        break
      except (GAPI.notFound, GAPI.invalidMessageId) as e:
        _processMessageFailed(user, messageId, str(e), j, jcount)
    Ind.Decrement()
  if csvPF:
    csvPF.writeCSVfile(f'{Act.ToPerform()} Messages')

def _processMessagesThreads(users, entityType):
  def _processMessageFailed(user, idsList, errMsg, j=0, jcount=0):
    if not csvPF:
      _getMain().entityActionFailedWarning([Ent.USER, user, entityType, idsList], errMsg, j, jcount)
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
        _getMain().callGAPI(gmail.users().messages(), function,
                 throwReasons=GAPI.GMAIL_THROW_REASONS+[GAPI.INVALID_MESSAGE_ID, GAPI.INVALID, GAPI.INVALID_ARGUMENT,
                                                        GAPI.FAILED_PRECONDITION, GAPI.PERMISSION_DENIED, GAPI.QUOTA_EXCEEDED],
                 userId='me', body=body)
        for messageId in body['ids']:
          mcount += 1
          if not csvPF:
            _getMain().entityActionPerformed([Ent.USER, user, entityType, messageId], mcount, jcount)
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
        _getMain().entityActionPerformed([Ent.USER, ri[RI_ENTITY], entityType, ri[RI_ITEM]], int(ri[RI_J]), int(ri[RI_JCOUNT]))
      else:
        csvPF.WriteRow({'User': ri[RI_ENTITY], entityHeader: ri[RI_ITEM], 'action': Act.Performed()})
    else:
      http_status, reason, message = _getMain().checkGAPIError(exception)
      _processMessageFailed(ri[RI_ENTITY], ri[RI_ITEM],
                            _getMain().getHTTPError(_GMAIL_ERROR_REASON_TO_MESSAGE_MAP, http_status, reason, message),
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
      dbatch.add(method(**svcparms), request_id=_getMain().batchRequestID(user, 0, 0, j, jcount, svcparms['id']))
      bcount += 1
      if bcount == GC.Values[GC.EMAIL_BATCH_SIZE]:
        _getMain().executeBatch(dbatch)
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
    myarg = _getMain().getArgument()
    if _getMessageSelectParameters(myarg, parameters):
      pass
    elif (function == 'modify') and (myarg == 'addlabel'):
      addLabelNames.append(_getMain().getString(Cmd.OB_LABEL_NAME))
    elif (function == 'modify') and (myarg == 'removelabel'):
      removeLabelNames.append(_getMain().getString(Cmd.OB_LABEL_NAME))
    elif myarg == 'csv':
      csvPF = _getMain().CSVPrintFile(['User', entityHeader, 'action', 'error'])
    elif csvPF and myarg == 'todrive':
      csvPF.GetTodriveParameters()
    else:
      _getMain().unknownArgumentExit()
  if function == 'modify' and not addLabelNames and not removeLabelNames:
    _getMain().missingArgumentExit('(addlabel <LabelName>)|(removelabel <LabelName>)')
  _finalizeMessageSelectParameters(parameters, True)
  includeSpamTrash = Act.Get() in [Act.DELETE, Act.MODIFY, Act.UNTRASH]
  if function == 'spam':
    function = 'modify'
    addLabelIds = ['SPAM']
    removeLabelIds = ['INBOX']
  i, count, users = _getMain().getEntityArgument(users)
  for user in users:
    i += 1
    user, gmail, messageIds = _getMain()._validateUserGetMessageIds(user, i, count, parameters['messageEntity'])
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
        _getMain().entityActionNotPerformedWarning([Ent.USER, user], Msg.NO_LABELS_TO_PROCESS, i, count)
        continue
    try:
      if parameters['messageEntity'] is None:
        _getMain().printGettingAllEntityItemsForWhom(Ent.MESSAGE, user, i, count, query=parameters['query'])
        listResult = _getMain().callGAPIpages(service, 'list', parameters['listType'],
                                   pageMessage=_getMain().getPageMessageForWhom(), maxItems=parameters['maxItems'],
                                   throwReasons=GAPI.GMAIL_THROW_REASONS+GAPI.GMAIL_LIST_THROW_REASONS,
                                   userId='me', q=parameters['query'], labelIds=parameters['labelIds'],
                                   fields=parameters['fields'], includeSpamTrash=includeSpamTrash,
                                   maxResults=GC.Values[GC.MESSAGE_MAX_RESULTS])
        messageIds = [message['id'] for message in listResult]
      else:
        # Need to get authorization set up for batch
        _getMain().callGAPI(gmail.users(), 'getProfile',
                 throwReasons=GAPI.GMAIL_THROW_REASONS+GAPI.GMAIL_LIST_THROW_REASONS,
                 userId='me', fields='')
    except (GAPI.failedPrecondition, GAPI.permissionDenied, GAPI.invalid, GAPI.invalidArgument) as e:
      _getMain().entityActionFailedWarning([Ent.USER, user], str(e), i, count)
      continue
    except GAPI.serviceNotAvailable:
      _getMain().userGmailServiceNotEnabledWarning(user, i, count)
      continue
    jcount = len(messageIds)
    if jcount == 0:
      _getMain().entityNumEntitiesActionNotPerformedWarning([Ent.USER, user], entityType, jcount, Msg.NO_ENTITIES_MATCHED.format(Ent.Plural(entityType)), i, count)
      _getMain().setSysExitRC(_getMain().NO_ENTITIES_FOUND_RC)
      continue
    if parameters['messageEntity'] is None:
      if parameters['maxToProcess'] and jcount > parameters['maxToProcess']:
        _getMain().entityNumEntitiesActionNotPerformedWarning([Ent.USER, user], entityType, jcount,
                                                   Msg.COUNT_N_EXCEEDS_MAX_TO_PROCESS_M.format(jcount, Act.ToPerform(), parameters['maxToProcess']),
                                                   i, count)
        continue
      if not parameters['doIt']:
        _getMain().entityNumEntitiesActionNotPerformedWarning([Ent.USER, user], entityType, jcount, Msg.USE_DOIT_ARGUMENT_TO_PERFORM_ACTION, i, count)
        continue
    _getMain().entityPerformActionNumItems([Ent.USER, user], jcount, entityType, i, count)
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
    myarg = _getMain().getArgument()
    if _getMessageSelectParameters(myarg, parameters):
      pass
    elif myarg == 'targetfolder':
      targetFolderPattern = _getMain().setFilePath(_getMain().getString(Cmd.OB_FILE_PATH), GC.DRIVE_DIR)
    elif myarg == 'targetname':
      targetNamePattern = _getMain().getString(Cmd.OB_FILE_NAME)
    elif myarg == 'overwrite':
      overwrite = _getMain().getBoolean()
    else:
      _getMain().unknownArgumentExit()
  _finalizeMessageSelectParameters(parameters, True)
  i, count, users = _getMain().getEntityArgument(users)
  for user in users:
    i += 1
    user, gmail, entityIds = _getMain()._validateUserGetMessageIds(user, i, count, parameters['messageEntity'])
    if not gmail:
      continue
    _, userName, _ = _getMain().splitEmailAddressOrUID(user)
    targetFolder = _getMain()._substituteForUser(targetFolderPattern, user, userName)
    if not os.path.isdir(targetFolder):
      os.makedirs(targetFolder)
    targetName = _getMain()._substituteForUser(targetNamePattern, user, userName) if targetNamePattern else None
    service = gmail.users().messages() if entityType == Ent.MESSAGE else gmail.users().threads()
    try:
      if parameters['messageEntity'] is None:
        _getMain().printGettingAllEntityItemsForWhom(entityType, user, i, count, query=parameters['query'])
        listResult = _getMain().callGAPIpages(service, 'list', parameters['listType'],
                                   pageMessage=_getMain().getPageMessageForWhom(), maxItems=parameters['maxItems'],
                                   throwReasons=GAPI.GMAIL_THROW_REASONS+GAPI.GMAIL_LIST_THROW_REASONS,
                                   userId='me', q=parameters['query'], labelIds=parameters['labelIds'],
                                   fields=parameters['fields'], includeSpamTrash=includeSpamTrash,
                                   maxResults=GC.Values[GC.MESSAGE_MAX_RESULTS])
        entityIds = [entity['id'] for entity in listResult]
    except (GAPI.failedPrecondition, GAPI.permissionDenied, GAPI.invalid, GAPI.invalidArgument) as e:
      _getMain().entityActionFailedWarning([Ent.USER, user], str(e), i, count)
      continue
    except GAPI.serviceNotAvailable:
      _getMain().userGmailServiceNotEnabledWarning(user, i, count)
      continue
    jcount = len(entityIds)
    if jcount == 0:
      _getMain().entityNumEntitiesActionNotPerformedWarning([Ent.USER, user], entityType, jcount, Msg.NO_ENTITIES_MATCHED.format(Ent.Plural(entityType)), i, count)
      _getMain().setSysExitRC(_getMain().NO_ENTITIES_FOUND_RC)
      continue
    if parameters['messageEntity'] is None:
      if parameters['maxToProcess'] and jcount > parameters['maxToProcess']:
        _getMain().entityNumEntitiesActionNotPerformedWarning([Ent.USER, user], entityType, jcount, Msg.COUNT_N_EXCEEDS_MAX_TO_PROCESS_M.format(jcount, Act.ToPerform(), parameters['maxToProcess']), i, count)
        continue
    _getMain().entityPerformActionNumItems([Ent.USER, user], jcount, entityType, i, count)
    Ind.Increment()
    j = 0
    for entityId in entityIds:
      j += 1
      if entityType == Ent.THREAD:
        try:
          result = _getMain().callGAPI(gmail.users().threads(), 'get',
                             throwReasons=GAPI.GMAIL_THROW_REASONS+[GAPI.NOT_FOUND, GAPI.INVALID_ARGUMENT],
                             userId='me', id=entityId, fields='messages(id)')
          messageIds = [message['id'] for message in result['messages']]
          kcount = len(messageIds)
          _getMain().entityPerformActionNumItems([Ent.USER, user, Ent.THREAD, entityId], kcount, Ent.MESSAGE, j, jcount)
          Ind.Increment()
          k = 0
        except GAPI.serviceNotAvailable:
          _getMain().userGmailServiceNotEnabledWarning(user, i, count)
          break
        except (GAPI.notFound, GAPI.invalidArgument) as e:
          _getMain().entityActionFailedWarning([Ent.USER, user, Ent.THREAD, entityId], str(e), j, jcount)
          continue
      else:
        messageIds = [entityId]
        kcount = jcount
        k = j-1
      for messageId in messageIds:
        k += 1
        try:
          result = _getMain().callGAPI(gmail.users().messages(), 'get',
                            throwReasons=GAPI.GMAIL_THROW_REASONS+[GAPI.NOT_FOUND, GAPI.INVALID_MESSAGE_ID],
                            userId='me', id=messageId, format='raw')
          if targetName:
            msgName = targetName.replace('#id#', messageId)
          else:
            msgName = f'Msg-{messageId}.eml'
          filename, _ = _getMain().uniqueFilename(targetFolder, msgName, overwrite)
          status, e = _getMain().writeFileReturnError(filename, base64.urlsafe_b64decode(str(result['raw'])), mode='wb')
          if status:
            _getMain().entityActionPerformed([Ent.MESSAGE, filename])
          else:
            _getMain().entityActionFailedWarning([Ent.MESSAGE, filename], str(e))
        except GAPI.serviceNotAvailable:
          _getMain().userGmailServiceNotEnabledWarning(user, i, count)
          break
        except (GAPI.notFound, GAPI.invalidMessageId) as e:
          _getMain().entityActionFailedWarning([Ent.USER, user, Ent.MESSAGE, messageId], str(e), k, kcount)
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
  header = header.encode(_getMain().UTF8, 'replace').decode(_getMain().UTF8)
  while True:
    mg = HEADER_ENCODE_PATTERN.search(header)
    if not mg:
      return header
    try:
      header = header[:mg.start()]+decode_header(mg.group())[0][0].decode(mg.group(1))+header[mg.end():]
    except LookupError:
      _getMain().stderrWarningMsg(Msg.INVALID_CHARSET.format(mg.group(1)))
      return header

# gam <UserTypeEntity> forward message|messages [recipient|to] <RecipientEntity>
#	(((query <QueryGmail> [querytime<String> <Date>]*) (matchlabel <LabelName>) [or|and])+ [quick|notquick] [doit] [max_to_forward <Number>])|(ids <MessageIDEntity>)
#	[subject <String>] [addorigfieldstosubject [<Boolean>]] [altcharset <String>]
# gam <UserTypeEntity> forward thread|threads [recipient|to] <RecipientEntity>
#	(((query <QueryGmail> [querytime<String> <Date>]*) (matchlabel <LabelName>) [or|and])+ [quick|notquick] [doit] [max_to_forward <Number>])|(ids <ThreadIDEntity>)
#	[subject <String>] [addorigfieldstosubject [<Boolean>]] [altcharset <String>]
def forwardMessagesThreads(users, entityType):
  _getMain().checkArgumentPresent({'recipient', 'recipients', 'to'})
  recipients = _getMain().getRecipients()
  parameters = _initMessageThreadParameters(entityType, False, 1)
  addOriginalFieldsToSubject = includeSpamTrash = False
  subject = ''
  encodings = [UTF8]
  while Cmd.ArgumentsRemaining():
    myarg = _getMain().getArgument()
    if _getMessageSelectParameters(myarg, parameters):
      pass
    elif myarg == 'subject':
      subject = _getMain().getString(Cmd.OB_STRING)
    elif myarg == 'addorigfieldstosubject':
      addOriginalFieldsToSubject = _getMain().getBoolean()
    elif myarg == 'altcharset':
      encodings.append(_getMain().getString(Cmd.OB_CHAR_SET))
    else:
      _getMain().unknownArgumentExit()
  _finalizeMessageSelectParameters(parameters, True)
  msgTo = ','.join(recipients)
  i, count, users = _getMain().getEntityArgument(users)
  for user in users:
    i += 1
    user, gmail, entityIds = _getMain()._validateUserGetMessageIds(user, i, count, parameters['messageEntity'])
    if not gmail:
      continue
    service = gmail.users().messages() if entityType == Ent.MESSAGE else gmail.users().threads()
    if parameters['messageEntity'] is None:
      try:
        _getMain().printGettingAllEntityItemsForWhom(entityType, user, i, count, query=parameters['query'])
        listResult = _getMain().callGAPIpages(service, 'list', parameters['listType'],
                                   pageMessage=_getMain().getPageMessageForWhom(), maxItems=parameters['maxItems'],
                                   throwReasons=GAPI.GMAIL_THROW_REASONS+GAPI.GMAIL_LIST_THROW_REASONS,
                                   userId='me', q=parameters['query'], labelIds=parameters['labelIds'],
                                   fields=parameters['fields'], includeSpamTrash=includeSpamTrash,
                                   maxResults=GC.Values[GC.MESSAGE_MAX_RESULTS])
        entityIds = [entity['id'] for entity in listResult]
      except (GAPI.failedPrecondition, GAPI.permissionDenied, GAPI.invalid, GAPI.invalidArgument) as e:
        _getMain().entityActionFailedWarning([Ent.USER, user], str(e), i, count)
        continue
      except GAPI.serviceNotAvailable:
        _getMain().userGmailServiceNotEnabledWarning(user, i, count)
        continue
    jcount = len(entityIds)
    if jcount == 0:
      _getMain().entityNumEntitiesActionNotPerformedWarning([Ent.USER, user], entityType, jcount, Msg.NO_ENTITIES_MATCHED.format(Ent.Plural(entityType)), i, count)
      _getMain().setSysExitRC(_getMain().NO_ENTITIES_FOUND_RC)
      continue
    if parameters['messageEntity'] is None:
      if parameters['maxToProcess'] and jcount > parameters['maxToProcess']:
        _getMain().entityNumEntitiesActionNotPerformedWarning([Ent.USER, user], entityType, jcount, Msg.COUNT_N_EXCEEDS_MAX_TO_PROCESS_M.format(jcount, Act.ToPerform(), parameters['maxToProcess']), i, count)
        continue
      if not parameters['doIt']:
        _getMain().entityNumEntitiesActionNotPerformedWarning([Ent.USER, user], entityType, jcount, Msg.USE_DOIT_ARGUMENT_TO_PERFORM_ACTION, i, count)
        continue
    _getMain().entityPerformActionNumItems([Ent.USER, user], jcount, entityType, i, count)
    Ind.Increment()
    j = 0
    for entityId in entityIds:
      j += 1
      if entityType == Ent.THREAD:
        try:
          result = _getMain().callGAPI(gmail.users().threads(), 'get',
                             throwReasons=GAPI.GMAIL_THROW_REASONS+[GAPI.NOT_FOUND, GAPI.INVALID_MESSAGE_ID],
                             userId='me', id=entityId, fields='messages(id)')
          messageIds = [message['id'] for message in result['messages']]
          kcount = len(messageIds)
          _getMain().entityPerformActionNumItems([Ent.USER, user, Ent.THREAD, entityId], kcount, Ent.MESSAGE, j, jcount)
          Ind.Increment()
          k = 0
        except GAPI.serviceNotAvailable:
          _getMain().userGmailServiceNotEnabledWarning(user, i, count)
          break
        except (GAPI.notFound, GAPI.invalidMessageId) as e:
          _getMain().entityActionFailedWarning([Ent.USER, user, Ent.THREAD, entityId], str(e), j, jcount)
          continue
      else:
        messageIds = [entityId]
        kcount = jcount
        k = j-1
      for messageId in messageIds:
        k += 1
        try:
          result = _getMain().callGAPI(gmail.users().messages(), 'get',
                            throwReasons=GAPI.GMAIL_THROW_REASONS+[GAPI.NOT_FOUND, GAPI.INVALID_MESSAGE_ID],
                            userId='me', id=messageId, format='raw')
          for encoding in encodings:
            try:
              message = message_from_string(base64.urlsafe_b64decode(str(result['raw'])).decode(encoding), policy=policySMTP)
              break
            except UnicodeDecodeError as e:
              errMsg = str(e)
          else:
            _getMain().entityActionNotPerformedWarning([Ent.RECIPIENT, msgTo, entityType, messageId], errMsg, k, kcount)
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
            result = _getMain().callGAPI(gmail.users().messages(), 'send',
                              throwReasons=[GAPI.SERVICE_NOT_AVAILABLE, GAPI.AUTH_ERROR, GAPI.DOMAIN_POLICY,
                                            GAPI.INVALID, GAPI.INVALID_ARGUMENT, GAPI.FORBIDDEN, GAPI.PERMISSION_DENIED],
                              userId='me', body={'raw': base64.urlsafe_b64encode(message.as_bytes()).decode(encoding)}, fields='id')
            _getMain().entityActionPerformedMessage([Ent.RECIPIENT, msgTo], f"{result['id']}", k, kcount)
          except (GAPI.serviceNotAvailable, GAPI.authError, GAPI.domainPolicy,
                  GAPI.invalid, GAPI.invalidArgument, GAPI.forbidden, GAPI.permissionDenied, UnicodeEncodeError) as e:
            _getMain().entityActionFailedWarning([Ent.RECIPIENT, msgTo], str(e), k, kcount)
        except GAPI.serviceNotAvailable:
          _getMain().userGmailServiceNotEnabledWarning(user, i, count)
          break
        except (GAPI.notFound, GAPI.invalidMessageId) as e:
          _getMain().entityActionFailedWarning([Ent.USER, user, Ent.MESSAGE, messageId], str(e), k, kcount)
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
      header.append(value, _getMain().UTF8)

  labelNameMap = {}
  addLabelNames = []
  msgHTML = msgText = ''
  msgHeaders = {}
  tagReplacements = _getMain()._initTagReplacements()
  attachments = []
  embeddedImages = []
  internalDateSource = 'receivedTime'
  deleted = processForCalendar = substituteForUserInHeaders = False
  neverMarkSpam = True
  emlFile = False
  emlEncoding = 'ascii'
  while Cmd.ArgumentsRemaining():
    myarg = _getMain().getArgument()
    if myarg in SMTP_HEADERS_MAP:
      if myarg == 'content-type':
        _getMain().unknownArgumentExit()
      if myarg in SMTP_DATE_HEADERS:
        msgDate, _, _ = _getMain().getTimeOrDeltaFromNow(True)
        msgHeaders[SMTP_HEADERS_MAP[myarg]] = formatdate(time.mktime(msgDate.timetuple()) + msgDate.microsecond/1E6, True)
        if myarg == 'date':
          internalDateSource = 'dateHeader'
      else:
        value = _getMain().getString(Cmd.OB_STRING)
        if (value.find('#user#') >= 0) or (value.find('#email#') >= 0) or (value.find('#username#') >= 0):
          substituteForUserInHeaders = True
        msgHeaders[SMTP_HEADERS_MAP[myarg]] = value
    elif myarg == 'header':
      header = _getMain().getString(Cmd.OB_STRING, minLen=1)
      if header.lower() == 'content-type':
        _getMain().unknownArgumentExit()
      value = _getMain().getString(Cmd.OB_STRING)
      if (value.find('#user#') >= 0) or (value.find('#email#') >= 0) or (value.find('#username#') >= 0):
        substituteForUserInHeaders = True
      msgHeaders[SMTP_HEADERS_MAP.get(header.lower(), header)] = value
    elif myarg in _getMain().SORF_MSG_FILE_ARGUMENTS:
      if 'html' in myarg:
        msgHTML, _, _ = _getMain().getStringOrFile(myarg)
      else:
        msgText, _, _ = _getMain().getStringOrFile(myarg)
      emlFile = False
    elif myarg == 'emlfile':
      filename = _getMain().getString(Cmd.OB_FILE_NAME)
      if _getMain().checkArgumentPresent('charset'):
        emlEncoding = _getMain().getString(Cmd.OB_CHAR_SET)
      filename = _getMain().setFilePath(filename, GC.INPUT_DIR)
      msgText = _getMain().readFile(filename, encoding=emlEncoding)
      emlFile = True
      internalDateSource = 'dateHeader'
      if _getMain().checkArgumentPresent('emlutf8'):
        emlEncoding = _getMain().UTF8
    elif _getMain()._getTagReplacement(myarg, tagReplacements, True):
      pass
    elif operation in IMPORT_INSERT and myarg == 'addlabel':
      addLabelNames.append(_getMain().getString(Cmd.OB_LABEL_NAME, minLen=1))
    elif operation in IMPORT_INSERT and myarg == 'labels':
      addLabelNames.extend(_getMain().shlexSplitList(_getMain().getString(Cmd.OB_LABEL_NAME_LIST)))
    elif operation in IMPORT_INSERT and myarg == 'deleted':
      deleted = _getMain().getBoolean()
    elif myarg == 'attach':
      attachments.append((_getMain().getFilename(), _getMain().getCharSet()))
    elif myarg == 'embedimage':
      embeddedImages.append((_getMain().getFilename(), _getMain().getString(Cmd.OB_STRING)))
    elif operation == 'import' and myarg == 'nevermarkspam':
      neverMarkSpam = _getMain().getBoolean()
    elif operation == 'import' and myarg == 'checkspam':
      neverMarkSpam = not _getMain().getBoolean()
    elif operation == 'import' and myarg == 'processforcalendar':
      processForCalendar = _getMain().getBoolean()
    else:
      _getMain().unknownArgumentExit()
  if not msgText and not msgHTML:
    _getMain().missingArgumentExit('textmessage|textfile|htmlmessage|htmlfile|empfile')
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
        msgHeaders['From'] = _getMain()._getAdminEmail()
    kwargs = {'internalDateSource': internalDateSource, 'deleted': deleted}
    if operation == 'import':
      function = 'import_'
      kwargs.update({'neverMarkSpam': neverMarkSpam, 'processForCalendar': processForCalendar})
    else: #'insert':
      function = 'insert'
  else:
    function = 'create'
  add_charset(_getMain().UTF8, QP, QP, _getMain().UTF8)
  i, count, users = _getMain().getEntityArgument(users)
  for user in users:
    i += 1
    user, gmail = _getMain().buildGAPIServiceObject(API.GMAIL, user, i, count)
    if not gmail:
      continue
    userName, _ = _getMain().splitEmailAddress(user)
    if not emlFile:
      if tagReplacements['tags']:
        if tagReplacements['subs']:
          _getMain()._getTagReplacementFieldValues(user, i, count, tagReplacements)
        tmpText = _getMain()._processTagReplacements(tagReplacements, msgText)
        tmpHTML = _getMain()._processTagReplacements(tagReplacements, msgHTML)
      if attachments or embeddedImages:
        if tmpText and tmpHTML:
          message = MIMEMultipart('alternative')
          textpart = MIMEText(tmpText, 'plain', _getMain().UTF8)
          message.attach(textpart)
          htmlpart = MIMEText(tmpHTML, 'html', _getMain().UTF8)
          message.attach(htmlpart)
        elif tmpHTML:
          message = MIMEMultipart()
          htmlpart = MIMEText(tmpHTML, 'html', _getMain().UTF8)
          message.attach(htmlpart)
        else:
          message = MIMEMultipart()
          textpart = MIMEText(tmpText, 'plain', _getMain().UTF8)
          message.attach(textpart)
        _addAttachmentsToMessage(message, attachments)
        _addEmbeddedImagesToMessage(message, embeddedImages)
      else:
        if tmpText and tmpHTML:
          message = MIMEMultipart('alternative')
          textpart = MIMEText(tmpText, 'plain', _getMain().UTF8)
          message.attach(textpart)
          htmlpart = MIMEText(tmpHTML, 'html', _getMain().UTF8)
          message.attach(htmlpart)
        elif tmpHTML:
          message = MIMEText(tmpHTML, 'html', _getMain().UTF8)
        else:
          message = MIMEText(tmpText, 'plain', _getMain().UTF8)
      for header, value in msgHeaders.items():
        if substituteForUserInHeaders:
          value = _getMain()._substituteForUser(value, user, userName)
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
      tmpFile = TemporaryFile(mode='w+', encoding=_getMain().UTF8)
      g = Generator(tmpFile, False)
      g.flatten(message)
      tmpFile.seek(0)
      body = {'raw': base64.urlsafe_b64encode(bytes(tmpFile.read(), _getMain().UTF8)).decode()}
      tmpFile.close()
    else:
      for header, value in msgHeaders.items():
        if substituteForUserInHeaders:
          value = _getMain()._substituteForUser(value, user, userName)
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
        result = _getMain().callGAPI(gmail.users().messages(), function,
                          throwReasons=GAPI.GMAIL_THROW_REASONS+[GAPI.PERMISSION_DENIED],
                          userId='me', body=body, fields='id', **kwargs)
      else:
        result = _getMain().callGAPI(gmail.users().drafts(), function,
                          throwReasons=GAPI.GMAIL_THROW_REASONS+[GAPI.INVALID_ARGUMENT, GAPI.PERMISSION_DENIED],
                          userId='me', body={'message': body}, fields='id')
      _getMain().entityActionPerformed([Ent.USER, user, Ent.MESSAGE, result['id']], i, count)
    except (GAPI.invalidArgument, GAPI.permissionDenied) as e:
      _getMain().entityActionFailedWarning([Ent.USER, user], str(e), i, count)
    except GAPI.serviceNotAvailable:
      _getMain().userGmailServiceNotEnabledWarning(user, i, count)

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

def printShowMessagesThreads(users, entityType):

  def _getBodyData(payload, getOrigMsg):
    data = headers = ''
    for part in payload.get('parts', []):
      if getOrigMsg:
        if show_all_headers:
          if not headers:
            headers = '---------- Original message ----------\n'
          for header in part.get('headers', []):
            headers += header['name']+': '+_decodeHeader(header['value'])+'\n'
        elif 'headers' in part:
          for name in headersToShow:
            for header in part['headers']:
              if name == header['name'].lower():
                if not headers:
                  headers = '---------- Original message ----------\n'
                headers += SMTP_HEADERS_MAP.get(name, header['name'])+': '+_decodeHeader(header['value'])+'\n'
        if headers:
          headers += 'Body:\n'
          data = Ind.INDENT_SPACES_PER_LEVEL
      if part['mimeType'] == 'text/plain':
        if 'data' in part['body']:
          data += base64.urlsafe_b64decode(str(part['body']['data'])).decode(UTF8)+'\n'
      elif show_html and part['mimeType'] == 'text/html':
        if 'data' in part['body']:
          data += base64.urlsafe_b64decode(str(part['body']['data'])).decode(UTF8)+'\n'
      elif part['mimeType'] == 'text/rfc822-headers':
        if 'data' in part['body']:
          data += _decodeHeader(base64.urlsafe_b64decode(str(part['body']['data'])).decode(UTF8)+'\n')
      else:
        data += _getBodyData(part, part['mimeType'] == 'message/rfc822')
    if getOrigMsg:
      data = data.replace('\n', f'\n{Ind.INDENT_SPACES_PER_LEVEL}').rstrip()
    return headers+data

  def _getMessageBody(payload):
    if 'attachmentId' not in payload.get('body', {}) and 'data' in payload.get('body', {}):
      return base64.urlsafe_b64decode(str(payload['body']['data'])).decode(_getMain().UTF8)
    data = _getBodyData(payload, False)
    if data:
      return data
    return 'Body not available'

  ATTACHMENT_NAME_PATTERN = re.compile(r'^.*name="?(.*?)(?:"|;|$)')
  CHARSET_NAME_PATTERN = re.compile(r'^.*charset="?(.*?)(?:"|;|$)')

  def _showAttachmentMimeTypeSizeCharset(part, charset):
    _getMain().printKeyValueList(['mimeType', part['mimeType']])
    _getMain().printKeyValueList(['size', part['body']['size']])
    if charset:
      _getMain().printKeyValueList(['charset', charset])

  def _showSaveAttachments(messageId, payload, attachmentNamePattern, j, jcount):
    for part in payload.get('parts', []):
      if 'attachmentId' in part['body']:
        for header in part['headers']:
          if header['name'] in {'Content-Type', 'Content-Disposition'}:
            mg = ATTACHMENT_NAME_PATTERN.match(header['value'])
            if not mg:
              continue
            attachmentName = mg.group(1)
            if (not attachmentNamePattern) or attachmentNamePattern.match(attachmentName):
              charset = ''
              if part['mimeType'] == 'text/plain':
                mg = CHARSET_NAME_PATTERN.match(header['value'])
                if mg:
                  charset = mg.group(1)
              if (part['mimeType'] == 'text/plain' and not noshow_text_plain) or save_attachments or upload_attachments:
                try:
                  result = _getMain().callGAPI(gmail.users().messages().attachments(), 'get',
                                    throwReasons=GAPI.GMAIL_THROW_REASONS+[GAPI.NOT_FOUND],
                                    messageId=messageId, id=part['body']['attachmentId'], userId='me')
                  if 'data' in result:
                    if show_attachments:
                      _getMain().printKeyValueList(['Attachment', attachmentName])
                      Ind.Increment()
                      if part['mimeType'] == 'text/plain':
                        try:
                          _getMain().printKeyValueList([Ind.MultiLineText(base64.urlsafe_b64decode(str(result['data'])).decode(charset)+'\n')])
                        except (LookupError, UnicodeDecodeError, UnicodeError):
                          _showAttachmentMimeTypeSizeCharset(part, charset)
                      else:
                        _showAttachmentMimeTypeSizeCharset(part, charset)
                      Ind.Decrement()
                    if save_attachments:
                      filename, _ = _getMain().uniqueFilename(targetFolder, _getMain().cleanFilename(attachmentName), overwrite)
                      action = Act.Get()
                      Act.Set(Act.DOWNLOAD)
                      status, e = _getMain().writeFileReturnError(filename, base64.urlsafe_b64decode(str(result['data'])), mode='wb')
                      if status:
                        _getMain().entityActionPerformed([Ent.ATTACHMENT, filename])
                      else:
                        _getMain().entityActionFailedWarning([Ent.ATTACHMENT, filename], str(e))
                      Act.Set(action)
                    if upload_attachments:
                      filename = _getMain().cleanFilename(attachmentName)
                      uploadAttachmentBody.update({'name': filename, 'mimeType': part['mimeType']})
                      action = Act.Get()
                      Act.Set(Act.CREATE)
                      media_body = googleapiclient.http.MediaIoBaseUpload(io.BytesIO(base64.urlsafe_b64decode(str(result['data']))), mimetype=part['mimeType'], resumable=True)
                      try:
                        result = _getMain().callGAPI(drive.files(), 'create',
                                          throwReasons=GAPI.DRIVE_USER_THROW_REASONS+[GAPI.FORBIDDEN, GAPI.INSUFFICIENT_PERMISSIONS, GAPI.INSUFFICIENT_PARENT_PERMISSIONS,
                                                                                      GAPI.INVALID, GAPI.BAD_REQUEST, GAPI.CANNOT_ADD_PARENT,
                                                                                      GAPI.FILE_NOT_FOUND, GAPI.UNKNOWN_ERROR, GAPI.INTERNAL_ERROR,
                                                                                      GAPI.STORAGE_QUOTA_EXCEEDED, GAPI.TEAMDRIVES_SHARING_RESTRICTION_NOT_ALLOWED,
                                                                                      GAPI.TEAMDRIVE_FILE_LIMIT_EXCEEDED, GAPI.TEAMDRIVE_HIERARCHY_TOO_DEEP,
                                                                                      GAPI.UPLOAD_TOO_LARGE, GAPI.TEAMDRIVES_SHORTCUT_FILE_NOT_SUPPORTED],
                                          media_body=media_body, body=uploadAttachmentBody, fields='id,name', supportsAllDrives=True)
                        _getMain().entityModifierItemValueListActionPerformed([Ent.DRIVE_FILE, f"{result['name']}({result['id']})"],
                                                                   Act.MODIFIER_WITH_CONTENT_FROM, [Ent.ATTACHMENT, filename], j, jcount)
                      except (GAPI.forbidden, GAPI.insufficientPermissions, GAPI.insufficientParentPermissions,
                              GAPI.invalid, GAPI.badRequest, GAPI.cannotAddParent,
                              GAPI.fileNotFound, GAPI.unknownError, GAPI.internalError,
                              GAPI.storageQuotaExceeded, GAPI.teamdrivesSharingRestrictionNotAllowed,
                              GAPI.teamdrivefileLimitExceeded, GAPI.teamdriveHierarchyTooDeep,
                              GAPI.uploadTooLarge, GAPI.teamdrivesShortcutFileNotSupported) as e:
                        _getMain().entityModifierItemValueListActionFailedWarning([Ent.DRIVE_FILE, None],
                                                                       Act.MODIFIER_WITH_CONTENT_FROM, [Ent.ATTACHMENT, filename], str(e), j, jcount)
                      except (GAPI.serviceNotAvailable, GAPI.authError, GAPI.domainPolicy) as e:
                        _getMain().userDriveServiceNotEnabledWarning(user, str(e), i, count)
                      Act.Set(action)
                except (GAPI.serviceNotAvailable, GAPI.notFound):
                  pass
              elif show_attachments:
                _getMain().printKeyValueList(['Attachment', attachmentName])
                Ind.Increment()
                _showAttachmentMimeTypeSizeCharset(part, charset)
                Ind.Decrement()
            break
      else:
        _showSaveAttachments(messageId, part, attachmentNamePattern, j, jcount)

  def _initSenderLabelsMap(sender):
    if sender not in senderLabelsMaps:
      senderLabelsMaps[sender] = {'*None*': {'name': '*None*', 'count': 0, 'size': 0, 'type': LABEL_TYPE_USER, 'match': labelMatchPattern is None}}
      for label in labels['labels']:
        senderLabelsMaps[sender][label['id']] = {'name': label['name'], 'count': 0, 'size': 0, 'type': label['type'],
                                                'match': True if not labelMatchPattern else labelMatchPattern.match(label['name']) is not None}
    return senderLabelsMaps[sender]

  def _getMatchMessageLabels(result, sender):
    labelsMap = _initSenderLabelsMap(sender)
    messageLabels = []
    match = False
    for labelId in result.get('labelIds', []):
      if labelId in labelsMap:
        match |= labelsMap[labelId]['match']
        if not onlyUser or labelsMap[labelId]['type'] != LABEL_TYPE_SYSTEM:
          messageLabels.append(labelsMap[labelId]['name'])
      else:
        messageLabels.append(labelId)
    if labelMatchPattern and not match:
      return None
    return messageLabels

  def _checkSenderMatch(result):
    for header in result['payload'].get('headers', []):
      sender = _decodeHeader(header['value'])
      if header['name'] == 'Sender' and senderMatchPattern.match(sender):
        return sender
    return None

  def _checkSenderMatchCount(result):
    for header in result['payload'].get('headers', []):
      sender = _decodeHeader(header['value'])
      if header['name'] == 'Sender' and senderMatchPattern.match(sender):
        senderCounts.setdefault(sender, {'count': 0, 'size': 0})
        senderCounts[sender]['count'] += 1
        senderCounts[sender]['size'] += result['sizeEstimate']
        return sender
    return None

  def _qualifyMessage(user, result):
    if senderMatchPattern:
      sender = _checkSenderMatchCount(result)
      if not sender:
        return (False, None)
    else:
      sender = user
    if show_labels or labelMatchPattern:
      messageLabels = _getMatchMessageLabels(result, sender)
      if messageLabels is None:
        return (False, None)
      return (True, messageLabels)
    return (True, None)

  def _convertDateTime(headerValue):
    dateTimeValue = headerValue.replace('GMT', '+0000')
    dateTimeValue = dateTimeValue.replace('UT', '+0000')
    pLoc = dateTimeValue.find(' (')
    if pLoc > 0:
      dateTimeValue = dateTimeValue[:pLoc]
    try:
      dateTimeValue = arrow.Arrow.strptime(dateTimeValue, _getMain().RFC2822_TIME_FORMAT)
      if dateHeaderConvertTimezone:
        dateTimeValue = dateTimeValue.to(GC.Values[GC.TIMEZONE])
      return dateTimeValue.strftime(dateHeaderFormat)
    except ValueError:
      return headerValue

  def _showMessage(user, result, j, jcount, checkMax=True):
    if checkMax and parameters['maxToProcess'] and parameters['messagesProcessed'] == parameters['maxToProcess']:
      return
    status, messageLabels = _qualifyMessage(user, result)
    if not status:
      return
    _getMain().printEntity([Ent.MESSAGE, result['id']], j, jcount)
    Ind.Increment()
    if show_snippet:
      _getMain().printKeyValueList(['Snippet', dehtml(result['snippet']).replace('\n', ' ')])
    if show_all_headers:
      for header in result['payload'].get('headers', []):
        headerValue = _decodeHeader(header['value'])
        if dateHeaderFormat and header['name'].lower() in SMTP_DATE_HEADERS:
          headerValue = _convertDateTime(headerValue)
        _getMain().printKeyValueList([header['name'], headerValue])
    else:
      for name in headersToShow:
        for header in result['payload'].get('headers', []):
          if name == header['name'].lower():
            headerValue = _decodeHeader(header['value'])
            if dateHeaderFormat and name in SMTP_DATE_HEADERS:
              headerValue = _convertDateTime(headerValue)
            _getMain().printKeyValueList([SMTP_HEADERS_MAP.get(name, header['name']), headerValue])
    if show_date:
      _getMain().printKeyValueList(['Date', formatLocalTimestamp(result['internalDate'])])
    if show_size:
      _getMain().printKeyValueList(['SizeEstimate', result['sizeEstimate']])
    if show_labels:
      _getMain().printKeyValueList(['Labels', delimiter.join(messageLabels)])
    if show_body:
      _getMain().printKeyValueList(['Body', None])
      Ind.Increment()
      _getMain().printKeyValueList([Ind.MultiLineText(_getMessageBody(result['payload']))])
      Ind.Decrement()
    if show_attachments or save_attachments or upload_attachments:
      _showSaveAttachments(result['id'], result['payload'], attachmentNamePattern, j, jcount)
    Ind.Decrement()
    if checkMax:
      parameters['messagesProcessed'] += 1

  def _getAttachments(messageId, payload, attachmentNamePattern, attachments):
    for part in payload.get('parts', []):
      if 'attachmentId' in part['body']:
        for header in part['headers']:
          if header['name'] in {'Content-Type', 'Content-Disposition'}:
            mg = ATTACHMENT_NAME_PATTERN.match(header['value'])
            if not mg:
              continue
            attachmentName = mg.group(1)
            charset = ''
            if part['mimeType'] == 'text/plain':
              mg = CHARSET_NAME_PATTERN.match(header['value'])
              if mg:
                charset = mg.group(1)
            if (not attachmentNamePattern) or attachmentNamePattern.match(attachmentName):
              attachments.append((attachmentName, part['mimeType'], part['body']['size'], charset))
            break
      else:
        _getAttachments(messageId, part, attachmentNamePattern, attachments)

  def _printMessage(user, result, checkMax=True):
    if checkMax and parameters['maxToProcess'] and parameters['messagesProcessed'] == parameters['maxToProcess']:
      return
    status, messageLabels = _qualifyMessage(user, result)
    if not status:
      return
    row = {'User': user, 'threadId': result['threadId'], 'id': result['id']}
    if show_snippet:
      row['Snippet'] = dehtml(result['snippet']).replace('\n', ' ')
    if show_all_headers:
      headerCounts = {}
      for header in result['payload'].get('headers', []):
        headerCounts.setdefault(header['name'], 0)
        headerValue = _decodeHeader(header['value'])
        if dateHeaderFormat and header['name'].lower() in SMTP_DATE_HEADERS:
          headerValue = _convertDateTime(headerValue)
        if headerCounts[header['name']] == 0:
          row[header['name']] = headerValue
        else:
          row[f'{header["name"]} {headerCounts[header["name"]]}'] = headerValue
        headerCounts[header['name']] += 1
    else:
      for name in headersToShow:
        j = 0
        for header in result['payload'].get('headers', []):
          if name == header['name'].lower():
            headerValue = _decodeHeader(header['value'])
            if dateHeaderFormat and name in SMTP_DATE_HEADERS:
              headerValue = _convertDateTime(headerValue)
            if j == 0:
              row[SMTP_HEADERS_MAP.get(name, header['name'])] = headerValue
            else:
              row[f'{SMTP_HEADERS_MAP.get(name, header["name"])} {j}'] = headerValue
            j += 1
    if show_date:
      row['Date'] = formatLocalTimestamp(result['internalDate'])
    if show_size:
      row['SizeEstimate'] = result['sizeEstimate']
    if show_labels:
      row['LabelsCount'] = len(messageLabels)
      row['Labels'] = delimiter.join(messageLabels)
    if show_body:
      if not convertCRNL:
        row['Body'] = _getMessageBody(result['payload'])
      else:
        row['Body'] = escapeCRsNLs(_getMessageBody(result['payload']))
    if show_attachments:
      attachments = []
      _getAttachments(result['id'], result['payload'], attachmentNamePattern, attachments)
      row['Attachments'] = len(attachments)
      for i, attachment in enumerate(attachments):
        row[f'Attachments{GC.Values[GC.CSV_OUTPUT_SUBFIELD_DELIMITER]}{i}{GC.Values[GC.CSV_OUTPUT_SUBFIELD_DELIMITER]}name'] = attachment[0]
        row[f'Attachments{GC.Values[GC.CSV_OUTPUT_SUBFIELD_DELIMITER]}{i}{GC.Values[GC.CSV_OUTPUT_SUBFIELD_DELIMITER]}mimeType'] = attachment[1]
        row[f'Attachments{GC.Values[GC.CSV_OUTPUT_SUBFIELD_DELIMITER]}{i}{GC.Values[GC.CSV_OUTPUT_SUBFIELD_DELIMITER]}size'] = attachment[2]
        row[f'Attachments{GC.Values[GC.CSV_OUTPUT_SUBFIELD_DELIMITER]}{i}{GC.Values[GC.CSV_OUTPUT_SUBFIELD_DELIMITER]}charset'] = attachment[3]
    if addCSVData:
      row.update(addCSVData)
    csvPF.WriteRowTitles(row)
    if checkMax:
      parameters['messagesProcessed'] += 1

  def _countMessageLabels(user, result):
    if senderMatchPattern:
      sender = _checkSenderMatch(result)
      if not sender:
        return False
    else:
      sender = user
    labelsMap = _initSenderLabelsMap(sender)
    labelIds = result.get('labelIds', [])
    if labelIds:
      for labelId in labelIds:
        if labelId in labelsMap:
          labelsMap[labelId]['count'] += 1
          labelsMap[labelId]['size'] += result['sizeEstimate']
        else:
          labelsMap[labelId] = {'name': labelId, 'count': 1, 'size': result['sizeEstimate'], 'type': LABEL_TYPE_USER,
                                'match': True if not labelMatchPattern else labelMatchPattern.match(labelId) is not None}
    elif not labelMatchPattern:
      labelsMap['*None*']['count'] += 1
      labelsMap['*None*']['size'] += result['sizeEstimate']

  def _countMessages(_, result):
    if senderMatchPattern and not _checkSenderMatchCount(result):
      return
    messageThreadCounts['messages'] += 1
    messageThreadCounts['size'] += result['sizeEstimate']

  def _showThread(user, result, j, jcount):
    if parameters['maxToProcess'] and parameters['messagesProcessed'] == parameters['maxToProcess']:
      return
    if senderMatchPattern:
      for message in result['messages']:
        if _checkSenderMatch(message):
          break
      else:
        return
    messageThreadCounts['threads'] += 1
    _getMain().printEntity([Ent.THREAD, result['id']], j, jcount)
    Ind.Increment()
    if show_snippet and 'snippet' in result:
      _getMain().printKeyValueList(['Snippet', dehtml(result['snippet']).replace('\n', ' ')])
    kcount = len(result['messages'])
    k = 0
    for message in result['messages']:
      k += 1
      _showMessage(user, message, k, kcount, False)
      if k == parameters['maxMessagesPerThread']:
        break
    Ind.Decrement()
    parameters['messagesProcessed'] += 1

  def _printThread(user, result):
    if parameters['maxToProcess'] and parameters['messagesProcessed'] == parameters['maxToProcess']:
      return
    if senderMatchPattern:
      for message in result['messages']:
        if _checkSenderMatch(message):
          break
      else:
        return
    k = 0
    for message in result['messages']:
      k += 1
      _printMessage(user, message, False)
      if k == parameters['maxMessagesPerThread']:
        break
    messageThreadCounts['threads'] += 1
    parameters['messagesProcessed'] += 1

  def _countThreadLabels(user, result):
    for message in result['messages']:
      _countMessageLabels(user, message)

  def _countThreads(_, result):
    if senderMatchPattern:
      for message in result['messages']:
        if _checkSenderMatchCount(message):
          messageThreadCounts['size'] += message['sizeEstimate']
          break
      else:
        return
    else:
      k = 0
      for message in result['messages']:
        k += 1
        messageThreadCounts['size'] += message['sizeEstimate']
        if k == parameters['maxMessagesPerThread']:
          break
    messageThreadCounts['threads'] += 1

  _GMAIL_ERROR_REASON_TO_MESSAGE_MAP = {GAPI.NOT_FOUND: Msg.DOES_NOT_EXIST, GAPI.INVALID_MESSAGE_ID: Msg.INVALID_MESSAGE_ID}

  def _handleGmailError(exception, ri):
    http_status, reason, message = _getMain().checkGAPIError(exception)
    errMsg = _getMain().getHTTPError(_GMAIL_ERROR_REASON_TO_MESSAGE_MAP, http_status, reason, message)
    if reason not in GAPI.DEFAULT_RETRY_REASONS:
      if not csvPF:
        _getMain().printKeyValueListWithCount([Ent.Singular(entityType), ri[RI_ITEM], errMsg], int(ri[RI_J]), int(ri[RI_JCOUNT]))
        _getMain().setSysExitRC(_getMain().ACTION_FAILED_RC)
      else:
        _getMain().entityActionFailedWarning([Ent.USER, ri[RI_ENTITY], entityType, ri[RI_ITEM]], errMsg, int(ri[RI_J]), int(ri[RI_JCOUNT]))
      return
    try:
      response = _getMain().callGAPI(service, 'get',
                          throwReasons=GAPI.GMAIL_THROW_REASONS+[GAPI.NOT_FOUND, GAPI.INVALID_MESSAGE_ID],
                          userId='me', id=ri[RI_ITEM], format=['metadata', 'full'][show_size or show_body or show_attachments or save_attachments or upload_attachments])
      if countsOnly:
        _callbacks['process'](ri[RI_ENTITY], response)
      else:
        if not csvPF:
          _callbacks['process'](ri[RI_ENTITY], response, int(ri[RI_J]), int(ri[RI_JCOUNT]))
        else:
          _callbacks['process'](ri[RI_ENTITY], response)
    except GAPI.notFound:
      _getMain().entityActionFailedWarning([Ent.USER, ri[RI_ENTITY], entityType, ri[RI_ITEM]], Msg.DOES_NOT_EXIST, int(ri[RI_J]), int(ri[RI_JCOUNT]))
    except GAPI.invalidMessageId:
      _getMain().entityActionFailedWarning([Ent.USER, ri[RI_ENTITY], entityType, ri[RI_ITEM]], Msg.INVALID_MESSAGE_ID, int(ri[RI_J]), int(ri[RI_JCOUNT]))
    except GAPI.serviceNotAvailable:
      _getMain().userGmailServiceNotEnabledWarning(ri[RI_ENTITY], int(ri[RI_I]), int(ri[RI_COUNT]))

  def _callbackShow(request_id, response, exception):
    ri = request_id.splitlines()
    if exception is None:
      _callbacks['process'](ri[RI_ENTITY], response, int(ri[RI_J]), int(ri[RI_JCOUNT]))
    else:
      _handleGmailError(exception, ri)

  def _callbackPrint(request_id, response, exception):
    ri = request_id.splitlines()
    if exception is None:
      _callbacks['process'](ri[RI_ENTITY], response)
    else:
      _handleGmailError(exception, ri)

  def _callbackCountLabels(request_id, response, exception):
    ri = request_id.splitlines()
    if exception is None:
      _callbacks['process'](ri[RI_ENTITY], response)
    else:
      _handleGmailError(exception, ri)

  def _batchPrintShowMessagesThreads(service, user, jcount, messageIds):
    svcargs = dict([('userId', 'me'), ('id', None), ('format', ['metadata', 'full'][show_body or show_attachments or save_attachments or upload_attachments])]+GM.Globals[GM.EXTRA_ARGS_LIST])
    if countsOnly:
      if show_labels:
        if not senderMatchPattern:
          svcargs['fields'] = 'labelIds,sizeEstimate' if entityType == Ent.MESSAGE else 'messages(labelIds,sizeEstimate)'
        else:
          svcargs['fields'] = 'labelIds,sizeEstimate,payload' if entityType == Ent.MESSAGE else 'messages(labelIds,sizeEstimate,payload)'
      else:
        if not senderMatchPattern:
          svcargs['fields'] = 'sizeEstimate' if entityType == Ent.MESSAGE else 'messages(sizeEstimate)'
        else:
          svcargs['fields'] = 'sizeEstimate,payload' if entityType == Ent.MESSAGE else 'messages(sizeEstimate,payload)'
    method = getattr(service, 'get')
    dbatch = gmail.new_batch_http_request(callback=_callbacks['batch'])
    bcount = 0
    j = 0
    for messageId in messageIds:
      j += 1
      svcparms = svcargs.copy()
      svcparms['id'] = messageId
      dbatch.add(method(**svcparms), request_id=_getMain().batchRequestID(user, 0, 0, j, jcount, svcparms['id']))
      bcount += 1
      if not labelMatchPattern and parameters['maxToProcess'] and j == parameters['maxToProcess']:
        break
      if bcount == GC.Values[GC.EMAIL_BATCH_SIZE]:
        _getMain().executeBatch(dbatch)
        dbatch = gmail.new_batch_http_request(callback=_callbacks['batch'])
        bcount = 0
        if labelMatchPattern and parameters['messagesProcessed'] == parameters['maxToProcess']:
          break
    if bcount > 0:
      dbatch.execute()

  parameters = _initMessageThreadParameters(entityType, True, 0)
  convertCRNL = GC.Values[GC.CSV_OUTPUT_CONVERT_CR_NL]
  delimiter = GC.Values[GC.CSV_OUTPUT_FIELD_DELIMITER]
  countsOnly = positiveCountsOnly = includeSpamTrash = onlyUser = overwrite = save_attachments = upload_attachments = False
  show_all_headers = show_attachments = show_body = show_date = show_html = show_labels = show_size = show_snippet = False
  noshow_text_plain = False
  attachmentNamePattern = None
  targetFolderPattern = GC.Values[GC.DRIVE_DIR]
  defaultHeaders = ['Date', 'Subject', 'From', 'Reply-To', 'To', 'Delivered-To', 'Content-Type', 'Message-ID']
  headersToShow = [header.lower() for header in defaultHeaders]
  csvPF = _getMain().CSVPrintFile() if Act.csvFormat() else None
  showMode = Act.Get() == Act.SHOW
  dateHeaderFormat = ''
  dateHeaderConvertTimezone = False
  uploadAttachmentBody = {}
  addCSVData = {}
  parentParms = _getMain().initDriveFileAttributes()
  while Cmd.ArgumentsRemaining():
    myarg = _getMain().getArgument()
    if csvPF and myarg == 'todrive':
      csvPF.GetTodriveParameters()
    elif _getMessageSelectParameters(myarg, parameters):
      pass
    elif myarg == 'headers':
      headersToShow = _getMain().getString(Cmd.OB_STRING, minLen=0).lower().replace(',', ' ').split()
      show_all_headers = headersToShow and headersToShow[0] == 'all'
    elif not showMode and myarg in {'convertcrnl', 'converttextnl', 'convertbodynl'}:
      convertCRNL = True
    elif myarg == 'delimiter':
      delimiter = _getMain().getCharacter()
    elif myarg == 'showdate':
      show_date = True
    elif myarg == 'showbody':
      show_body = True
    elif myarg == 'showhtml':
      show_html = True
    elif myarg == 'showlabels':
      show_labels = True
    elif myarg == 'showsize':
      show_size = True
    elif myarg == 'showsnippet':
      show_snippet = True
    elif myarg == 'showattachments':
      show_attachments = True
    elif myarg == 'noshowtextplain':
      noshow_text_plain = True
    elif myarg == 'attachmentnamepattern':
      attachmentNamePattern = _getMain().getREPattern(re.IGNORECASE)
    elif showMode and myarg == 'saveattachments':
      save_attachments = True
    elif showMode and myarg == 'targetfolder':
      targetFolderPattern = _getMain().setFilePath(_getMain().getString(Cmd.OB_FILE_PATH), GC.DRIVE_DIR)
    elif showMode and myarg == 'overwrite':
      overwrite = _getMain().getBoolean()
    elif showMode and myarg == 'uploadattachments':
      upload_attachments = True
    elif showMode and _getMain().getDriveFileParentAttribute(myarg, parentParms):
      pass
    elif myarg == 'includespamtrash':
      includeSpamTrash = True
    elif myarg == 'countsonly':
      countsOnly = True
    elif myarg == 'positivecountsonly':
      countsOnly = positiveCountsOnly = True
    elif myarg in {'onlyuser', 'useronly'}:
      onlyUser = _getMain().getBoolean()
    elif myarg == 'dateheaderformat':
      dateHeaderFormat = _getMain().getString(Cmd.OB_STRING, minLen=0)
      if dateHeaderFormat == 'iso':
        dateHeaderFormat = _getMain().IS08601_TIME_FORMAT
      elif dateHeaderFormat == 'rfc2822':
        dateHeaderFormat = _getMain().RFC2822_TIME_FORMAT
    elif myarg == 'dateheaderconverttimezone':
      dateHeaderConvertTimezone = _getMain().getBoolean()
      if not dateHeaderFormat:
        dateHeaderFormat = _getMain().RFC2822_TIME_FORMAT
    elif csvPF and myarg == 'addcsvdata':
      _getMain().getAddCSVData(addCSVData)
    else:
      _getMain().unknownArgumentExit()
  labelMatchPattern = parameters['labelMatchPattern']
  senderMatchPattern = parameters['senderMatchPattern']
  if senderMatchPattern and not show_all_headers and 'sender' not in headersToShow:
    headersToShow.append('sender')
  _finalizeMessageSelectParameters(parameters, False)
  if csvPF:
    if countsOnly:
      if show_labels:
        if not senderMatchPattern:
          sortTitles = ['User']
        else:
          sortTitles = ['User', 'Sender']
        csvPF.SetIndexedTitles(['Labels'])
        _callbacks = {'batch': _callbackCountLabels, 'process': _countMessageLabels if entityType == Ent.MESSAGE else _countThreadLabels}
      else:
        if not senderMatchPattern:
          sortTitles = ['User', parameters['listType']]
        else:
          sortTitles = ['User', 'Sender', parameters['listType']]
        _callbacks = {'batch': _callbackCountLabels, 'process': _countMessages if entityType == Ent.MESSAGE else _countThreads}
      if show_size:
        sortTitles.append('size')
      if addCSVData:
        sortTitles.extend(sorted(addCSVData.keys()))
      csvPF.SetTitles(sortTitles)
    else:
      sortTitles = ['User', 'threadId', 'id']
      if show_all_headers:
        sortTitles.extend(defaultHeaders)
      elif headersToShow:
        sortTitles.extend([SMTP_HEADERS_MAP.get(header, header) for header in headersToShow])
      if show_size:
        sortTitles.append('SizeEstimate')
      if show_labels:
        sortTitles.extend(['LabelsCount', 'Labels'])
      if show_snippet:
        sortTitles.append('Snippet')
      if show_body:
        sortTitles.append('Body')
      if addCSVData:
        sortTitles.extend(sorted(addCSVData.keys()))
      _callbacks = {'batch': _callbackPrint, 'process': _printMessage if entityType == Ent.MESSAGE else _printThread}
    csvPF.SetTitles(sortTitles)
    csvPF.SetSortTitles(sortTitles)
  else:
    if countsOnly:
      if show_labels:
        _callbacks = {'batch': _callbackCountLabels, 'process': _countMessageLabels if entityType == Ent.MESSAGE else _countThreadLabels}
      else:
        _callbacks = {'batch': _callbackCountLabels, 'process': _countMessages if entityType == Ent.MESSAGE else _countThreads}
    else:
      _callbacks = {'batch': _callbackShow, 'process': _showMessage if entityType == Ent.MESSAGE else _showThread}
  i, count, users = _getMain().getEntityArgument(users)
  for user in users:
    i += 1
    user, gmail, messageIds = _getMain()._validateUserGetMessageIds(user, i, count, parameters['messageEntity'])
    if not gmail:
      continue
    service = gmail.users().messages() if entityType == Ent.MESSAGE else gmail.users().threads()
    if upload_attachments:
      _, drive = _getMain().buildGAPIServiceObject(API.DRIVE3, user, i, count)
      if not drive:
        continue
      if not _getMain()._getDriveFileParentInfo(drive, user, i, count, uploadAttachmentBody, parentParms):
        continue
    if show_labels or labelMatchPattern:
      labels = _getUserGmailLabels(gmail, user, i, count, 'labels(id,name,type)')
      if not labels:
        continue
      senderLabelsMaps = {}
      if not senderMatchPattern:
        _initSenderLabelsMap(user)
    messageThreadCounts = {'User': user, parameters['listType']: 0, 'size': 0}
    if addCSVData:
      messageThreadCounts.update(addCSVData)
    senderCounts = {}
    if save_attachments:
      _, userName, _ = _getMain().splitEmailAddressOrUID(user)
      targetFolder = _getMain()._substituteForUser(targetFolderPattern, user, userName)
      if not os.path.isdir(targetFolder):
        os.makedirs(targetFolder)
    try:
      if parameters['messageEntity'] is None:
        _getMain().printGettingAllEntityItemsForWhom(entityType, user, i, count, query=parameters['query'])
        listResult = _getMain().callGAPIpages(service, 'list', parameters['listType'],
                                   pageMessage=_getMain().getPageMessageForWhom(), maxItems=parameters['maxItems'],
                                   throwReasons=GAPI.GMAIL_THROW_REASONS+GAPI.GMAIL_LIST_THROW_REASONS,
                                   userId='me', q=parameters['query'], labelIds=parameters['labelIds'],
                                   fields=parameters['fields'], includeSpamTrash=includeSpamTrash,
                                   maxResults=GC.Values[GC.MESSAGE_MAX_RESULTS])
        messageIds = [message['id'] for message in listResult]
      else:
        # Need to get authorization set up for batch
        _getMain().callGAPI(gmail.users(), 'getProfile',
                 throwReasons=GAPI.GMAIL_THROW_REASONS+GAPI.GMAIL_LIST_THROW_REASONS,
                 userId='me', fields='')
    except (GAPI.failedPrecondition, GAPI.permissionDenied, GAPI.invalid, GAPI.invalidArgument) as e:
      _getMain().entityActionFailedWarning([Ent.USER, user], str(e), i, count)
      continue
    except GAPI.serviceNotAvailable:
      _getMain().userGmailServiceNotEnabledWarning(user, i, count)
      continue
    jcount = len(messageIds)
    if jcount == 0:
      _getMain().setSysExitRC(_getMain().NO_ENTITIES_FOUND_RC)
    if countsOnly and not show_labels and not senderMatchPattern and not show_size:
      if not positiveCountsOnly or jcount > 0:
        if not csvPF:
          _getMain().printEntityKVList([Ent.USER, user], [parameters['listType'], jcount], i, count)
        else:
          row = {'User': user, parameters['listType']: jcount}
          if addCSVData:
            row.update(addCSVData)
          csvPF.WriteRow(row)
      continue
    if not csvPF and not countsOnly:
      if (parameters['messageEntity'] is not None or
          ((parameters['maxToProcess'] == 0 or jcount <= parameters['maxToProcess']) and
           (not labelMatchPattern and not senderMatchPattern))):
        _getMain().entityPerformActionNumItems([Ent.USER, user], jcount, entityType, i, count)
      elif not labelMatchPattern and not senderMatchPattern:
        _getMain().entityPerformActionNumItemsModifier([Ent.USER, user], parameters['maxToProcess'], entityType, f'of {jcount} Total {Ent.Plural(entityType)}', i, count)
      else:
        _getMain().entityPerformActionModifierNumItemsModifier([Ent.USER, user], Msg.MAXIMUM_OF, parameters['maxToProcess'] or jcount, entityType,
                                                    f'of {jcount} Total {Ent.Plural(entityType)}', i, count)
    if parameters['messageEntity'] is None and not labelMatchPattern and parameters['maxToProcess'] and (jcount > parameters['maxToProcess']):
      jcount = parameters['maxToProcess']
    parameters['messagesProcessed'] = 0
    if not csvPF:
      Ind.Increment()
      _batchPrintShowMessagesThreads(service, user, jcount, messageIds)
      Ind.Decrement()
    else:
      _batchPrintShowMessagesThreads(service, user, jcount, messageIds)
    if countsOnly:
      if show_labels:
        if onlyUser or positiveCountsOnly or labelMatchPattern:
          for sender in senderLabelsMaps:
            userLabelsMap = {}
            for labelId, label in senderLabelsMaps[sender].items():
              if (label['match'] and
                  (not onlyUser or label['type'] != LABEL_TYPE_SYSTEM) and
                  (not positiveCountsOnly or label['count'] > 0)):
                userLabelsMap[labelId] = label
            senderLabelsMaps[sender] = userLabelsMap
        if not csvPF:
          for sender, labelsMap in sorted(senderLabelsMaps.items()):
            jcount = len(labelsMap)
            kvlist = [Ent.USER, user]
            if senderMatchPattern:
              kvlist.extend([Ent.SENDER, sender])
            _getMain().entityPerformActionNumItems(kvlist, jcount, Ent.LABEL, i, count)
            Ind.Increment()
            j = 0
            for label in sorted(labelsMap.values(), key=lambda k: k['name']):
              j += 1
              if not show_size:
                _getMain().printEntityKVList([Ent.LABEL, label['name']], ['Count', label['count'], 'Type', label['type']], j, jcount)
              else:
                _getMain().printEntityKVList([Ent.LABEL, label['name']], ['Count', label['count'], 'Size', label['size'], 'Type', label['type']], j, jcount)
            Ind.Decrement()
        else:
          for sender, labelsMap in sorted(senderLabelsMaps.items()):
            row = {'User': user}
            if senderMatchPattern:
              row['Sender'] = sender
            if not show_size:
              for label in labelsMap.values():
                label.pop('size', None)
            if addCSVData:
              row.update(addCSVData)
            csvPF.WriteRowTitles(_getMain().flattenJSON({'Labels': sorted(labelsMap.values(), key=lambda k: k['name'])}, flattened=row))
      elif not senderMatchPattern:
        v = messageThreadCounts[parameters['listType']]
        if not positiveCountsOnly or v > 0:
          if not csvPF:
            if not show_size:
              _getMain().printEntityKVList([Ent.USER, user], [parameters['listType'], v], i, count)
            else:
              _getMain().printEntityKVList([Ent.USER, user], [parameters['listType'], v, 'size', messageThreadCounts['size']], i, count)
          else:
            if not show_size:
              messageThreadCounts.pop('size', None)
            csvPF.WriteRow(messageThreadCounts)
      else:
        if not show_size:
          if not csvPF:
            for k, v in sorted(senderCounts.items()):
              if not positiveCountsOnly or v['count'] > 0:
                _getMain().printEntityKVList([Ent.USER, user, Ent.SENDER, k], [parameters['listType'], v['count']], i, count)
          else:
            for k, v in sorted(senderCounts.items()):
              if not positiveCountsOnly or v['count'] > 0:
                row = {'User': user, 'Sender': k, parameters['listType']: v['count']}
                if addCSVData:
                  row.update(addCSVData)
                csvPF.WriteRow(row)
        else:
          if not csvPF:
            for k, v in sorted(senderCounts.items()):
              if not positiveCountsOnly or v['count'] > 0:
                _getMain().printEntityKVList([Ent.USER, user, Ent.SENDER, k], [parameters['listType'], v['count'], 'size', v['size']], i, count)
          else:
            for k, v in sorted(senderCounts.items()):
              if not positiveCountsOnly or v['count'] > 0:
                row = {'User': user, 'Sender': k, parameters['listType']: v['count'], 'size': v['size']}
                if addCSVData:
                  row.update(addCSVData)
                csvPF.WriteRow(row)
  if csvPF:
    if not countsOnly:
      csvPF.RemoveTitles(['SizeEstimate', 'LabelsCount', 'Labels', 'Snippet', 'Body'])
      if show_size:
        csvPF.AddTitle('SizeEstimate')
      if show_labels:
        csvPF.AddTitles(['LabelsCount', 'Labels'])
      if show_snippet:
        csvPF.AddTitle('Snippet')
      if show_body:
        csvPF.AddTitle('Body')
      csvPF.SetSortAllTitles()
      csvPF.writeCSVfile('Messages')
    else:
      csvPF.writeCSVfile('Message Counts' if not show_labels else 'Message Label Counts')

# gam <UserTypeEntity> print message|messages [todrive <ToDriveAttribute>*]
#	(((query <QueryGmail> [querytime<String> <Date>]*) (matchlabel <LabelName>) [or|and])*
#	 [labelids <LabelIDList>]
#	 [quick|notquick] [max_to_print <Number>] [includespamtrash])|(ids <MessageIDEntity>)
#	[labelmatchpattern <REMatchPattern>] [sendermatchpattern <REMatchPattern>]
#	[headers all|<SMTPHeaderList>] [dateheaderformat iso|rfc2822|<String>] [dateheaderconverttimezone [<Boolean>]]
#	[showlabels] [useronly] [delimiter <Character>] [showbody] [showhtml] [showdate] [showsize] [showsnippet]
#	[convertcrnl] [delimiter <Character>]
#	[countsonly|positivecountsonly] [useronly]
#	[[attachmentnamepattern <REMatchPattern>]
#	    [showattachments [noshowtextplain]]]
#	(addcsvdata <FieldName> <String>)*
# gam <UserTypeEntity> show message|messages
#	(((query <QueryGmail> [querytime<String> <Date>]*) (matchlabel <LabelName>) [or|and])*
#	 [labelids <LabelIDList>]
#	 [quick|notquick] [max_to_show <Number>] [includespamtrash])|(ids <MessageIDEntity>)
#	[labelmatchpattern <REMatchPattern>] [sendermatchpattern <REMatchPattern>]
#	[headers all|<SMTPHeaderList>] [dateheaderformat iso|rfc2822|<String>] [dateheaderconverttimezone [<Boolean>]]
#	[showlabels] [useronly] [showbody] [showhtml] [showdate] [showsize] [showsnippet]
#	[countsonly|positivecountsonly]
#	[[attachmentnamepattern <REMatchPattern>]
#	    [showattachments [noshowtextplain]]
#	    [saveattachments [targetfolder <FilePath>] [overwrite [<Boolean>]]]
#	    [uploadattachments [<DriveFileParentAttribute>]]]
def printShowMessages(users):
  printShowMessagesThreads(users, Ent.MESSAGE)

# gam <UserTypeEntity> print thread|threads [todrive <ToDriveAttribute>*]
#	(((query <QueryGmail> [querytime<String> <Date>]*) (matchlabel <LabelName>) [or|and])*
#	 [labelids <LabelIDList>]
#	 [quick|notquick] [max_to_print <Number>] [includespamtrash])|(ids <ThreadIDEntity>)
#	[labelmatchpattern <REMatchPattern>]
#	[headers all|<SMTPHeaderList>] [dateheaderformat iso|rfc2822|<String>] [dateheaderconverttimezone [<Boolean>]]
#	[showlabels] [showbody] [showhtml] [showdate] [showsize] [showsnippet]
#	[convertcrnl] [delimiter <Character>]
#	[countsonly|positivecountsonly] [useronly]
#	[[attachmentnamepattern <REMatchPattern>]
#	    [showattachments [noshowtextplain]]]
#	(addcsvdata <FieldName> <String>)*
# gam <UserTypeEntity> show thread|threads
#	(((query <QueryGmail> [querytime<String> <Date>]*) (matchlabel <LabelName>) [or|and])*
#	 [labelids <LabelIDList>]
#	 [quick|notquick] [max_to_show <Number>] [includespamtrash])|(ids <ThreadIDEntity>)
#	[labelmatchpattern <REMatchPattern>]
#	[headers all|<SMTPHeaderList>] [dateheaderformat iso|rfc2822|<String>] [dateheaderconverttimezone [<Boolean>]]
#	[showlabels] [showbody] [showhtml] [showdate] [showsize] [showsnippet]
#	[countsonly|positivecountsonly] [useronly]
#	[[attachmentnamepattern <REMatchPattern>]
#	    [showattachments [noshowtextplain]]
#	    [saveattachments [targetfolder <FilePath>] [overwrite [<Boolean>]]]
#	    [uploadattachments [<DriveFileParentAttribute>]]]
def printShowThreads(users):
  printShowMessagesThreads(users, Ent.THREAD)

