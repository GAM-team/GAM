"""Vault hold, query, and count management.

Part of the _vault_tmp sub-package."""

"""GAM Google Vault management."""

import re
import json
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

from gam.cmd.vault.matters import (
    VAULT_CORPUS_ARGUMENT_MAP,
    VAULT_CORPUS_QUERY_MAP,
    VAULT_COUNTS_CORPUS_ARGUMENT_MAP,
    VAULT_QUERY_ARGS,
    VAULT_VOICE_COVERED_DATA_MAP,
    _buildVaultQuery,
    _validateVaultQuery,
    convertHoldNameToID,
    convertMatterNameToID,
    convertQueryNameToID,
    formatVaultNameId,
    getMatterItem,
    warnMatterNotOpen,
)

def _cleanVaultHold(hold, cd):
  if cd is not None:
    if 'accounts' in hold:
      accountType = 'group' if hold['corpus'] == 'GROUPS' else 'user'
      for i in range(0, len(hold['accounts'])):
        hold['accounts'][i]['email'] = _getMain().convertUIDtoEmailAddress(f'uid:{hold["accounts"][i]["accountId"]}', cd, accountType)
    if 'orgUnit' in hold:
      hold['orgUnit']['orgUnitPath'] = _getMain().convertOrgUnitIDtoPath(cd, hold['orgUnit']['orgUnitId'])
  query = hold.get('query')
  if query:
    if 'driveQuery' in hold['query']:
      hold['query']['driveQuery'].pop('includeTeamDriveFiles', None)

VAULT_HOLD_TIME_OBJECTS = {'holdTime', 'updateTime', 'startTime', 'endTime'}

def _showVaultHold(matterNameId, hold, cd, FJQC, k=0, kcount=0):
  _cleanVaultHold(hold, cd)
  if FJQC is not None and FJQC.formatJSON:
    _getMain().printLine(json.dumps(_getMain().cleanJSON(hold, timeObjects=VAULT_HOLD_TIME_OBJECTS), ensure_ascii=False, sort_keys=False))
    return
  if matterNameId is not None:
    _getMain().printEntity([Ent.VAULT_MATTER, matterNameId, Ent.VAULT_HOLD, formatVaultNameId(hold['name'], hold['holdId'])], k, kcount)
  Ind.Increment()
  _getMain().showJSON(None, hold, timeObjects=VAULT_HOLD_TIME_OBJECTS)
  Ind.Decrement()

def _useVaultQueryForHold(v, matterId, matterNameId, body):
  _, _, _, query = convertQueryNameToID(v, _getMain().getString(Cmd.OB_QUERY_ITEM), matterId, matterNameId)
  body['corpus'] = query['corpus']
  method = query.get('method')
  if method == 'ACCOUNT':
    body['accounts'] = []
    for email in query['accountInfo']['emails']:
      body['accounts'].append({'email': email})
  elif method == 'ORG_UNIT':
    body['orgUnit'] = {'orgUnitId': query['orgUnitInfo']['orgUnitId']}
  queryType = VAULT_CORPUS_QUERY_MAP[query['corpus']]
  if queryType is None:
    return
  body['query'] = {queryType: {}}
  if query['corpus'] == 'DRIVE':
    body['query'][queryType]['includeSharedDriveFiles'] = query['driveOptions'].get('includeSharedDrives', False)
  elif query['corpus'] in {'GROUPS', 'MAIL'}:
    if query.get('terms'):
      body['query'][queryType]['terms'] = query['terms']
    if query.get('startTime'):
      body['query'][queryType]['startTime'] = query['startTime']
    if query.get('endTime'):
      body['query'][queryType]['endTime'] = query['endTime']
  elif query['corpus'] == 'HANGOUTS_CHAT':
    body['query'][queryType]['includeRooms'] = query['hangoutsChatOptions'].get('includeRooms', False)
  elif query['corpus'] == 'VOICE':
    body['query'][queryType]['coveredData'] = query['voiceOptions']['coveredData']

def _getHoldQueryParameters(myarg, queryParameters):
  if myarg == 'query':
    queryParameters['queryLocation'] = Cmd.Location()
    queryParameters['query'] = _getMain().getString(Cmd.OB_QUERY)
  elif myarg == 'terms':
    queryParameters['terms'] = _getMain().getString(Cmd.OB_STRING)
  elif myarg in {'start', 'starttime'}:
    queryParameters['startTime'] = _getMain().getTimeOrDeltaFromNow()
  elif myarg in {'end', 'endtime'}:
    queryParameters['endTime'] = _getMain().getTimeOrDeltaFromNow()
  elif myarg == 'includerooms':
    queryParameters['includeRooms'] = _getMain().getBoolean()
  elif myarg in {'includeshareddrives', 'includeteamdrives'}:
    queryParameters['includeSharedDriveFiles'] = _getMain().getBoolean()
  elif myarg == 'covereddata':
    queryParameters.setdefault('coveredData', [])
    queryParameters['coveredData'].append(_getMain().getChoice(VAULT_VOICE_COVERED_DATA_MAP, mapChoice=True))
  else:
    return False
  return True

def _setHoldQuery(body, queryParameters):
  queryType = VAULT_CORPUS_QUERY_MAP[body['corpus']]
  if queryType is None:
    return
  body['query'] = {queryType: {}}
  if body['corpus'] == 'DRIVE':
    if queryParameters.get('query'):
      try:
        body['query'][queryType] = json.loads(queryParameters['query'])
      except (IndexError, KeyError, SyntaxError, TypeError, ValueError) as e:
        Cmd.SetLocation(queryParameters['queryLocation'])
        _getMain().usageErrorExit(f'{str(e)}: {queryParameters["query"]}')
    elif queryParameters.get('includeSharedDriveFiles'):
      body['query'][queryType]['includeSharedDriveFiles'] = queryParameters['includeSharedDriveFiles']
  elif body['corpus'] in {'GROUPS', 'MAIL'}:
    if queryParameters.get('query'):
      body['query'][queryType]['terms'] = queryParameters['query']
    elif queryParameters.get('terms'):
      body['query'][queryType]['terms'] = queryParameters['terms']
    if queryParameters.get('startTime'):
      body['query'][queryType]['startTime'] = queryParameters['startTime']
    if queryParameters.get('endTime'):
      body['query'][queryType]['endTime'] = queryParameters['endTime']
  elif body['corpus'] == 'HANGOUTS_CHAT':
    if queryParameters.get('includeRooms'):
      body['query'][queryType]['includeRooms'] = queryParameters['includeRooms']
  elif body['corpus'] == 'VOICE':
    if queryParameters.get('coveredData'):
      body['query'][queryType]['coveredData'] = queryParameters['coveredData']

# gam create vaulthold|hold matter <MatterItem> [name <String>]
#	vaultquery <QueryItem>
#	[showdetails|returnidonly]
# gam create vaulthold|hold matter <MatterItem> [name <String>]
#	corpus calendar|drive|mail|groups|hangouts_chat|voice
#	[(accounts|groups|users <EmailItemList>) | (orgunit|org|ou <OrgUnit>)]
#	[query <QueryVaultCorpus>]
#	[terms <String>] [start|starttime <Date>|<Time>] [end|endtime <Date>|<Time>]
#	[includerooms <Boolean>]
#	[covereddata calllogs|textmessages|voicemails]
#	[includeshareddrives <Boolean>]
#	[showdetails|returnidonly]
def doCreateVaultHold():
  v = _getMain().buildGAPIObject(API.VAULT)
  body = {}
  matterId = None
  accounts = []
  queryParameters = {}
  returnIdOnly = showDetails = usedVaultQuery  = False
  while Cmd.ArgumentsRemaining():
    myarg = _getMain().getArgument()
    if myarg == 'matter':
      matterId, matterNameId = getMatterItem(v)
    elif myarg == 'name':
      body['name'] = _getMain().getString(Cmd.OB_STRING)
    elif matterId is not None and myarg == 'vaultquery':
      _useVaultQueryForHold(v, matterId, matterNameId, body)
      usedVaultQuery = True
    elif myarg == 'corpus':
      body['corpus'] = _getMain().getChoice(VAULT_CORPUS_ARGUMENT_MAP, mapChoice=True)
    elif myarg in {'accounts', 'users', 'groups'}:
      accountsLocation = Cmd.Location()
      accounts = _getMain().getEntityList(Cmd.OB_EMAIL_ADDRESS_ENTITY)
    elif myarg in {'ou', 'org', 'orgunit'}:
      body['orgUnit'] = {'orgUnitId': _getMain().getOrgUnitId()[1]}
    elif _getHoldQueryParameters(myarg, queryParameters):
      pass
    elif myarg == 'showdetails':
      showDetails = True
      returnIdOnly = False
    elif myarg == 'returnidonly':
      returnIdOnly = True
      showDetails = False
    else:
      _getMain().unknownArgumentExit()
  if matterId is None:
    _getMain().missingArgumentExit('matter')
  if not body.get('corpus'):
    _getMain().missingArgumentExit(f'corpus {"|".join(VAULT_CORPUS_ARGUMENT_MAP)}')
  if 'name' not in body:
    body['name'] = f'GAM {body["corpus"]} Hold - {ISOformatTimeStamp(todaysTime())}'
  if not usedVaultQuery:
    _setHoldQuery(body, queryParameters)
  if accounts:
    body['accounts'] = []
    cd = _getMain().buildGAPIObject(API.DIRECTORY)
    accountType = 'group' if body['corpus'] == 'GROUPS' else 'user'
    for account in accounts:
      body['accounts'].append({'accountId': _getMain().convertEmailAddressToUID(account, cd, accountType, accountsLocation)})
  try:
    hold = _getMain().callGAPI(v.matters().holds(), 'create',
                    throwReasons=[GAPI.ALREADY_EXISTS, GAPI.BAD_REQUEST, GAPI.BACKEND_ERROR, GAPI.FAILED_PRECONDITION,
                                  GAPI.FORBIDDEN, GAPI.PERMISSION_DENIED, GAPI.INVALID_ARGUMENT],
                    matterId=matterId, body=body)
    if not returnIdOnly:
      _getMain().entityActionPerformed([Ent.VAULT_MATTER, matterNameId, Ent.VAULT_HOLD, formatVaultNameId(hold['name'], hold['holdId'])])
      if showDetails:
        _showVaultHold(None, hold, None, None)
    else:
      _getMain().writeStdout(f'{hold["holdId"]}\n')
  except (GAPI.alreadyExists, GAPI.badRequest, GAPI.backendError, GAPI.failedPrecondition,
          GAPI.forbidden, GAPI.permissionDenied, GAPI.invalidArgument) as e:
    _getMain().entityActionFailedWarning([Ent.VAULT_MATTER, matterNameId, Ent.VAULT_HOLD, body.get('name')], str(e))

# gam update vaulthold|hold <HoldItem> matter <MatterItem>
#	[([addaccounts|addgroups|addusers <EmailItemList>] [removeaccounts|removegroups|removeusers <EmailItemList>]) | (orgunit|org|ou <OrgUnit>)]
#	[query <QueryVaultCorpus>]
#	[terms <String>] [start|starttime <Date>|<Time>] [end|endtime <Date>|<Time>]
#	[includerooms <Boolean>]
#	[covereddata calllogs|textmessages|voicemails]
#	[includeshareddrives <Boolean>]
#	[showdetails]
def doUpdateVaultHold():
  v = _getMain().buildGAPIObject(API.VAULT)
  holdName = _getMain().getString(Cmd.OB_HOLD_ITEM)
  body = {}
  cd = matterId = None
  addAccounts = []
  addAccountIds = []
  removeAccounts = []
  removeAccountIds = []
  queryParameters = {}
  showDetails = False
  while Cmd.ArgumentsRemaining():
    myarg = _getMain().getArgument()
    if myarg == 'matter':
      matterId, matterNameId = getMatterItem(v)
      holdId, holdName, holdNameId = convertHoldNameToID(v, holdName, matterId, matterNameId)
    elif myarg in {'addusers', 'addaccounts', 'addgroups'}:
      addAccountsLocation = Cmd.Location()
      addAccounts = _getMain().getEntityList(Cmd.OB_EMAIL_ADDRESS_ENTITY)
    elif myarg in {'removeusers', 'removeaccounts', 'removegroups'}:
      removeAccountsLocation = Cmd.Location()
      removeAccounts = _getMain().getEntityList(Cmd.OB_EMAIL_ADDRESS_ENTITY)
    elif myarg in {'ou', 'org', 'orgunit'}:
      body['orgUnit'] = {'orgUnitId': _getMain().getOrgUnitId()[1]}
    elif _getHoldQueryParameters(myarg, queryParameters):
      pass
    elif myarg == 'showdetails':
      showDetails = True
    else:
      _getMain().unknownArgumentExit()
  if matterId is None:
    _getMain().missingArgumentExit('matter')
  try:
    old_body = _getMain().callGAPI(v.matters().holds(), 'get',
                        throwReasons=[GAPI.NOT_FOUND, GAPI.BAD_REQUEST, GAPI.FORBIDDEN, GAPI.PERMISSION_DENIED, GAPI.INVALID_ARGUMENT],
                        matterId=matterId, holdId=holdId, fields='name,corpus,query,orgUnit')
  except (GAPI.notFound, GAPI.badRequest, GAPI.forbidden, GAPI.permissionDenied, GAPI.invalidArgument) as e:
    _getMain().entityActionFailedWarning([Ent.VAULT_MATTER, matterNameId, Ent.VAULT_HOLD, holdNameId], str(e))
    return
  accountType = 'group' if old_body['corpus'] == 'GROUPS' else 'user'
  if addAccounts:
    if cd is None:
      cd = _getMain().buildGAPIObject(API.DIRECTORY)
    for account in addAccounts:
      addAccountIds.append({'email': account, 'id': _getMain().convertEmailAddressToUID(account, cd, accountType, addAccountsLocation)})
  if removeAccounts:
    if cd is None:
      cd = _getMain().buildGAPIObject(API.DIRECTORY)
    for account in removeAccounts:
      removeAccountIds.append({'email': account, 'id': _getMain().convertEmailAddressToUID(account, cd, accountType, removeAccountsLocation)})
  if queryParameters or body.get('orgUnit'):
    body['corpus'] = old_body['corpus']
    if 'orgUnit' in old_body and 'orgUnit' not in body:
      # bah, API requires this to be sent on update even when it's not changing
      body['orgUnit'] = old_body['orgUnit']
    if queryParameters:
      _setHoldQuery(body, queryParameters)
    else:
      body['query'] = old_body['query']
  if body:
    try:
      hold = _getMain().callGAPI(v.matters().holds(), 'update',
                      throwReas=[GAPI.NOT_FOUND, GAPI.BAD_REQUEST, GAPI.FORBIDDEN, GAPI.PERMISSION_DENIED, GAPI.INVALID_ARGUMENT],
                      matterId=matterId, holdId=holdId, body=body)
      _getMain().entityActionPerformed([Ent.VAULT_MATTER, matterNameId, Ent.VAULT_HOLD, holdNameId])
    except (GAPI.notFound, GAPI.badRequest, GAPI.forbidden, GAPI.permissionDenied, GAPI.invalidArgument) as e:
      _getMain().entityActionFailedWarning([Ent.VAULT_MATTER, matterNameId, Ent.VAULT_HOLD, holdNameId], str(e))
      return
  jcount = len(addAccountIds)
  if jcount > 0:
    Act.Set(Act.ADD)
    _getMain().entityPerformActionNumItems([Ent.VAULT_MATTER, matterNameId, Ent.VAULT_HOLD, holdNameId], jcount, Ent.ACCOUNT)
    Ind.Increment()
    j = 0
    for account in addAccountIds:
      j += 1
      try:
        _getMain().callGAPI(v.matters().holds().accounts(), 'create',
                 throwReasons=[GAPI.ALREADY_EXISTS, GAPI.BACKEND_ERROR, GAPI.FORBIDDEN, GAPI.PERMISSION_DENIED, GAPI.INVALID_ARGUMENT],
                 matterId=matterId, holdId=holdId, body={'accountId': account['id']})
        _getMain().entityActionPerformed([Ent.VAULT_MATTER, matterNameId, Ent.VAULT_HOLD, holdNameId, Ent.ACCOUNT, account['email']], j, jcount)
      except (GAPI.alreadyExists, GAPI.backendError) as e:
        _getMain().entityActionFailedWarning([Ent.VAULT_MATTER, matterNameId, Ent.VAULT_HOLD, holdNameId, Ent.ACCOUNT, account['email']], str(e), j, jcount)
      except (GAPI.forbidden, GAPI.permissionDenied, GAPI.invalidArgument) as e:
        _getMain().entityActionFailedWarning([Ent.VAULT_MATTER, matterNameId, Ent.VAULT_HOLD, None], str(e))
        return
    Ind.Decrement()
  jcount = len(removeAccountIds)
  if jcount > 0:
    Act.Set(Act.REMOVE)
    if cd is None:
      cd = _getMain().buildGAPIObject(API.DIRECTORY)
    _getMain().entityPerformActionNumItems([Ent.VAULT_MATTER, matterNameId, Ent.VAULT_HOLD, holdNameId], jcount, Ent.ACCOUNT)
    Ind.Increment()
    j = 0
    for account in removeAccountIds:
      j += 1
      try:
        _getMain().callGAPI(v.matters().holds().accounts(), 'delete',
                 throwReasons=[GAPI.NOT_FOUND, GAPI.BACKEND_ERROR, GAPI.FORBIDDEN, GAPI.PERMISSION_DENIED, GAPI.INVALID_ARGUMENT],
                 matterId=matterId, holdId=holdId, accountId=account['id'])
        _getMain().entityActionPerformed([Ent.VAULT_MATTER, matterNameId, Ent.VAULT_HOLD, holdNameId, Ent.ACCOUNT, account['email']], j, jcount)
      except (GAPI.alreadyExists, GAPI.backendError) as e:
        _getMain().entityActionFailedWarning([Ent.VAULT_MATTER, matterNameId, Ent.VAULT_HOLD, holdNameId, Ent.ACCOUNT, account['email']], str(e), j, jcount)
      except (GAPI.forbidden, GAPI.permissionDenied, GAPI.invalidArgument) as e:
        _getMain().entityActionFailedWarning([Ent.VAULT_MATTER, matterNameId, Ent.VAULT_HOLD, None], str(e))
        return
    Ind.Decrement()
  if showDetails:
    _showVaultHold(None, hold, cd, None)

# gam delete vaulthold|hold <HoldItem> matter <MatterItem>
# gam delete vaulthold|hold <MatterItem> <HoldItem>
def doDeleteVaultHold():
  v = _getMain().buildGAPIObject(API.VAULT)
  if not Cmd.ArgumentIsAhead('matter'):
    matterId, matterNameId = getMatterItem(v)
    holdId, holdName, holdNameId = convertHoldNameToID(v, _getMain().getString(Cmd.OB_HOLD_ITEM), matterId, matterNameId)
  else:
    holdName = _getMain().getString(Cmd.OB_HOLD_ITEM)
  while Cmd.ArgumentsRemaining():
    myarg = _getMain().getArgument()
    if myarg == 'matter':
      matterId, matterNameId = getMatterItem(v)
      holdId, holdName, holdNameId = convertHoldNameToID(v, holdName, matterId, matterNameId)
    else:
      _getMain().unknownArgumentExit()
  try:
    _getMain().callGAPI(v.matters().holds(), 'delete',
             throwReasons=[GAPI.NOT_FOUND, GAPI.BAD_REQUEST, GAPI.FORBIDDEN, GAPI.PERMISSION_DENIED, GAPI.INVALID_ARGUMENT],
             matterId=matterId, holdId=holdId)
    _getMain().entityActionPerformed([Ent.VAULT_MATTER, matterNameId, Ent.VAULT_HOLD, holdNameId])
  except (GAPI.notFound, GAPI.badRequest, GAPI.forbidden, GAPI.permissionDenied, GAPI.invalidArgument) as e:
    _getMain().entityActionFailedWarning([Ent.VAULT_MATTER, matterNameId, Ent.VAULT_HOLD, holdNameId], str(e))

VAULT_HOLD_FIELDS_CHOICE_MAP = {
  'accounts': 'accounts',
  'accounts.acountid': 'accounts.accountId',
  'accounts.email': 'accounts.email',
  'accounts.firstname': 'accounts.firstName',
  'accounts.holdtime': 'accounts.holdTime',
  'accounts.lastname': 'accounts.lastName',
  'corpus': 'corpus',
  'holdid': 'holdId',
  'name': 'name',
  'orgunit': 'orgUnit',
  'orgunit.holdtime': 'orgUnit.holdTime',
  'orgunit.ordunitid': 'orgUnit.orgUnitId',
  'query': 'query',
  'updatetime': 'updateTime',
  }

# gam info vaulthold|hold <HoldItem> matter <MatterItem>
#	[fields <VaultHoldFieldNameList>] [shownames]
#	[formatjson]
# gam info vaulthold|hold <MatterItem> <HoldItem>
#	[fields <VaultHoldFieldNameList>] [shownames]
#	[formatjson]
def doInfoVaultHold():
  v = _getMain().buildGAPIObject(API.VAULT)
  if not Cmd.ArgumentIsAhead('matter'):
    matterId, matterNameId = getMatterItem(v)
    holdId, holdName, holdNameId = convertHoldNameToID(v, _getMain().getString(Cmd.OB_HOLD_ITEM), matterId, matterNameId)
  else:
    holdName = _getMain().getString(Cmd.OB_HOLD_ITEM)
  cd = None
  fieldsList = []
  FJQC = _getMain().FormatJSONQuoteChar()
  while Cmd.ArgumentsRemaining():
    myarg = _getMain().getArgument()
    if myarg == 'matter':
      matterId, matterNameId = getMatterItem(v)
      holdId, holdName, holdNameId = convertHoldNameToID(v, holdName, matterId, matterNameId)
    elif myarg == 'shownames':
      cd = _getMain().buildGAPIObject(API.DIRECTORY)
    elif _getMain().getFieldsList(myarg, VAULT_HOLD_FIELDS_CHOICE_MAP, fieldsList, initialField=['holdId', 'name']):
      pass
    else:
      FJQC.GetFormatJSON(myarg)
  fields = _getMain()._getMain().getFieldsFromFieldsList(fieldsList)
  try:
    hold = _getMain().callGAPI(v.matters().holds(), 'get',
                    throwReasons=[GAPI.NOT_FOUND, GAPI.BAD_REQUEST, GAPI.FORBIDDEN, GAPI.PERMISSION_DENIED, GAPI.INVALID_ARGUMENT],
                    matterId=matterId, holdId=holdId, fields=fields)
    _showVaultHold(matterNameId, hold, cd, FJQC)
  except (GAPI.notFound, GAPI.badRequest, GAPI.forbidden, GAPI.permissionDenied, GAPI.invalidArgument) as e:
    _getMain().entityActionFailedWarning([Ent.VAULT_MATTER, matterNameId, Ent.VAULT_HOLD, holdNameId], str(e))

PRINT_VAULT_HOLDS_TITLES = ['matterId', 'matterName', 'holdId', 'name', 'updateTime']

# gam print vaultholds|holds [todrive <ToDriveAttribute>*] [matters <MatterItemList>]
#	[fields <VaultHoldFieldNameList>] [shownames]
#	[formatjson [quotechar <Character>]]
#	[oneitemperrow]
# gam show vaultholds|holds [matters <MatterItemList>]
#	[fields <VaultHoldFieldNameList>] [shownames]
#	[formatjson]
def doPrintShowVaultHolds():
  def _printVaultHold(hold):
    row = _getMain().flattenJSON(hold, flattened={'matterId': matterId, 'matterName': matterName}, timeObjects=VAULT_HOLD_TIME_OBJECTS)
    if not FJQC.formatJSON:
      csvPF.WriteRowTitles(row)
    elif csvPF.CheckRowTitles(row):
      csvPF.WriteRowNoFilter({'matterId': matterId, 'matterName': matterName,
                              'holdId': hold['holdId'], 'name': hold['name'],
                              'JSON': json.dumps(_getMain().cleanJSON(hold, timeObjects=VAULT_HOLD_TIME_OBJECTS), ensure_ascii=False, sort_keys=True)})

  v = _getMain().buildGAPIObject(API.VAULT)
  csvPF = _getMain().CSVPrintFile(PRINT_VAULT_HOLDS_TITLES, 'sortall') if Act.csvFormat() else None
  FJQC = _getMain().FormatJSONQuoteChar()
  matters = []
  cd = None
  fieldsList = []
  oneItemPerRow = False
  while Cmd.ArgumentsRemaining():
    myarg = _getMain().getArgument()
    if csvPF and myarg == 'todrive':
      csvPF.GetTodriveParameters()
    elif myarg in {'matter', 'matters'}:
      matters = _getMain().shlexSplitList(_getMain().getString(Cmd.OB_MATTER_ITEM_LIST))
    elif myarg == 'shownames':
      cd = _getMain().buildGAPIObject(API.DIRECTORY)
    elif _getMain().getFieldsList(myarg, VAULT_HOLD_FIELDS_CHOICE_MAP, fieldsList, initialField=['holdId', 'name']):
      pass
    elif csvPF and myarg == 'oneitemperrow':
      oneItemPerRow = True
    else:
      FJQC.GetFormatJSONQuoteChar(myarg, False)
  fields = _getMain().getItemFieldsFromFieldsList('holds', fieldsList)
  if csvPF and FJQC.formatJSON:
    csvPF.SetJSONTitles(PRINT_VAULT_HOLDS_TITLES+['JSON'])
  if not matters:
    _getMain().printGettingAllAccountEntities(Ent.VAULT_MATTER, qualifier=' (OPEN)')
    try:
      results = _getMain()._getMain().callGAPIpages(v.matters(), 'list', 'matters',
                              pageMessage=_getMain().getPageMessage(),
                              throwReasons=[GAPI.FORBIDDEN, GAPI.PERMISSION_DENIED, GAPI.INVALID_ARGUMENT],
                              view='BASIC', state='OPEN', fields='matters(matterId,name,state),nextPageToken')
    except (GAPI.forbidden, GAPI.permissionDenied, GAPI.invalidArgument) as e:
      _getMain().entityActionFailedWarning([Ent.VAULT_HOLD, None], str(e))
      return
  else:
    results = []
    for matter in matters:
      matterId, matterName, _, state = convertMatterNameToID(v, matter)
      results.append({'matterId': matterId, 'name': matterName, 'state': state})
  jcount = len(results)
  if not csvPF:
    if jcount == 0:
      _getMain().setSysExitRC(_getMain().NO_ENTITIES_FOUND_RC)
  j = 0
  for matter in results:
    j += 1
    matterId = matter['matterId']
    matterName = matter['name']
    matterNameId = formatVaultNameId(matterName, matterId)
    if csvPF:
      _getMain().printGettingAllEntityItemsForWhom(Ent.VAULT_HOLD, f'{Ent.Singular(Ent.VAULT_MATTER)}: {matterNameId}', j, jcount)
      pageMessage = _getMain().getPageMessageForWhom()
    else:
      pageMessage = None
    if matter['state'] == 'OPEN':
      try:
        holds = _getMain()._getMain().callGAPIpages(v.matters().holds(), 'list', 'holds',
                              pageMessage=pageMessage,
                              throwReasons=[GAPI.FAILED_PRECONDITION, GAPI.FORBIDDEN, GAPI.PERMISSION_DENIED, GAPI.INVALID_ARGUMENT],
                              matterId=matterId, fields=fields)
      except GAPI.failedPrecondition:
        warnMatterNotOpen(v, matter, matterNameId, j, jcount)
        continue
      except (GAPI.forbidden, GAPI.permissionDenied, GAPI.invalidArgument) as e:
        _getMain().entityActionFailedWarning([Ent.VAULT_HOLD, None], str(e))
        break
    else:
      warnMatterNotOpen(None, matter, matterNameId, j, jcount)
      continue
    if not csvPF:
      kcount = len(holds)
      if not FJQC.formatJSON:
        _getMain().entityPerformActionNumItems([Ent.VAULT_MATTER, matterNameId], kcount, Ent.VAULT_HOLD, j, jcount)
      Ind.Increment()
      k = 0
      for hold in holds:
        k += 1
        _showVaultHold(matterNameId, hold, cd, FJQC, k, kcount)
      Ind.Decrement()
    else:
      for hold in holds:
        _cleanVaultHold(hold, cd)
        if not oneItemPerRow or not hold.get('accounts', []):
          _printVaultHold(hold)
        else:
          for account in hold.pop('accounts'):
            hold['account'] = account
            _printVaultHold(hold)
  if csvPF:
    csvPF.writeCSVfile('Vault Holds')

PRINT_USER_VAULT_HOLDS_TITLES = ['User', 'matterId', 'matterName', 'holdId', 'name', 'orgUnitId', 'orgUnitPath']

# gam <UserTypeEntity> print vaultholds|holds [todrive <ToDriveAttribute>*]
# gam <UserTypeEntity> show vaultholds|holds
def printShowUserVaultHolds(entityList):
  cd = _getMain().buildGAPIObject(API.DIRECTORY)
  v = _getMain().buildGAPIObject(API.VAULT)
  csvPF = _getMain().CSVPrintFile(PRINT_USER_VAULT_HOLDS_TITLES, 'sortall') if Act.csvFormat() else None
  while Cmd.ArgumentsRemaining():
    myarg = _getMain().getArgument()
    if csvPF and myarg == 'todrive':
      csvPF.GetTodriveParameters()
    else:
      _getMain().unknownArgumentExit()
  _getMain().printGettingAllAccountEntities(Ent.VAULT_MATTER, qualifier=' (OPEN)')
  try:
    matters = _getMain()._getMain().callGAPIpages(v.matters(), 'list', 'matters',
                            pageMessage=_getMain().getPageMessage(),
                            throwReasons=[GAPI.FORBIDDEN, GAPI.PERMISSION_DENIED, GAPI.INVALID_ARGUMENT],
                            view='BASIC', state='OPEN', fields='matters(matterId,name,state),nextPageToken')
  except (GAPI.forbidden, GAPI.permissionDenied, GAPI.invalidArgument) as e:
    _getMain().entityActionFailedWarning([Ent.VAULT_HOLD, None], str(e))
    return
  jcount = len(matters)
  j = 0
  for matter in matters:
    j += 1
    matterId = matter['matterId']
    matterName = matter['name']
    matterNameId = formatVaultNameId(matterName, matterId)
    _getMain().printGettingAllEntityItemsForWhom(Ent.VAULT_HOLD, f'{Ent.Singular(Ent.VAULT_MATTER)}: {matterNameId}', j, jcount)
    try:
      matter['holds'] = _getMain().callGAPIpages(v.matters().holds(), 'list', 'holds',
                                      pageMessage=_getMain().getPageMessageForWhom(),
                                      throwReasons=[GAPI.FAILED_PRECONDITION, GAPI.FORBIDDEN, GAPI.PERMISSION_DENIED, GAPI.INVALID_ARGUMENT],
                                      matterId=matterId, fields='holds(holdId,name,accounts(accountId,email),orgUnit(orgUnitId)),nextPageToken')
    except GAPI.failedPrecondition:
      warnMatterNotOpen(v, matter, matterNameId, j, jcount)
    except (GAPI.forbidden, GAPI.permissionDenied, GAPI.invalidArgument) as e:
      _getMain().entityActionFailedWarning([Ent.VAULT_HOLD, None], str(e), j, jcount)
  totalHolds = 0
  _, _, entityList = _getMain().getEntityArgument(entityList)
  for user in entityList:
    user = _getMain().normalizeEmailAddressOrUID(user)
    orgUnits = _getMain().getAllParentOrgUnitsForUser(cd, user)
    for matter in matters:
      matterId = matter['matterId']
      matterName = matter['name']
      matterNameId = formatVaultNameId(matterName, matterId)
      for hold in matter.get('holds', []):
        if 'orgUnit' in hold:
          orgUnitId = hold['orgUnit'].get('orgUnitId')
          if orgUnitId in orgUnits:
            if not csvPF:
              _getMain().printEntityMessage([Ent.USER, user,
                                  Ent.ORGANIZATIONAL_UNIT, orgUnits[orgUnitId],
                                  Ent.VAULT_MATTER, formatVaultNameId(matter['name'], matter['matterId']),
                                  Ent.VAULT_HOLD, formatVaultNameId(hold['name'], hold['holdId'])],
                                 Msg.ON_VAULT_HOLD)
            else:
              csvPF.WriteRow({'User': user, 'matterId': matterId, 'matterName': matterName,
                              'holdId': hold['holdId'], 'name': hold['name'],
                              'orgUnitId': orgUnitId, 'orgUnitPath': orgUnits[orgUnitId]})
            totalHolds += 1
        else:
          for account in hold.get('accounts', []):
            if user == account.get('email', '').lower() or user == account.get('accountId', ''):
              if not csvPF:
                _getMain().printEntityMessage([Ent.USER, user,
                                    Ent.VAULT_MATTER, formatVaultNameId(matter['name'], matter['matterId']),
                                    Ent.VAULT_HOLD, formatVaultNameId(hold['name'], hold['holdId'])],
                                   Msg.ON_VAULT_HOLD)
              else:
                csvPF.WriteRow({'User': user, 'matterId': matterId, 'matterName': matterName,
                                'holdId': hold['holdId'], 'name': hold['name']})
              totalHolds += 1
              break
  if csvPF:
    csvPF.writeCSVfile('User Vault Holds')
  else:
    _getMain().printKeyValueList(['Total Holds', totalHolds])

def _cleanVaultQuery(query, cd, drive):
  if 'query' in query:
    if cd is not None and 'orgUnitInfo' in query['query']:
      query['query']['orgUnitInfo']['orgUnitPath'] = _getMain().convertOrgUnitIDtoPath(cd, query['query']['orgUnitInfo']['orgUnitId'])
    if drive is not None and 'sharedDriveInfo' in query['query']:
      query['query']['sharedDriveInfo']['sharedDriveNames'] = []
      for sharedDriveId in query['query']['sharedDriveInfo']['sharedDriveIds']:
        query['query']['sharedDriveInfo']['sharedDriveNames'].append(_getMain()._getSharedDriveNameFromId(drive, sharedDriveId, False))
    query['query'].pop('searchMethod', None)
    query['query'].pop('teamDriveInfo', None)

VAULT_QUERY_TIME_OBJECTS = {'createTime', 'endTime', 'startTime', 'versionDate'}

def _showVaultQuery(matterNameId, query, cd, drive, FJQC, k=0, kcount=0):
  _cleanVaultQuery(query, cd, drive)
  if FJQC is not None and FJQC.formatJSON:
    _getMain().printLine(json.dumps(_getMain().cleanJSON(query, timeObjects=VAULT_QUERY_TIME_OBJECTS), ensure_ascii=False, sort_keys=False))
    return
  _getMain().printEntity([Ent.VAULT_MATTER, matterNameId, Ent.VAULT_QUERY, formatVaultNameId(query['displayName'], query['savedQueryId'])], k, kcount)
  Ind.Increment()
  _getMain().showJSON(None, query, timeObjects=VAULT_QUERY_TIME_OBJECTS)
  Ind.Decrement()

def doCreateCopyVaultQuery(copyCmd):
  v = _getMain().buildGAPIObject(API.VAULT)
  body = {'query': {'dataScope': 'ALL_DATA'}, 'displayName': ''}
  matterId, matterNameId = getMatterItem(v)
  if copyCmd:
    _, queryName, _, body['query'] = convertQueryNameToID(v, _getMain().getString(Cmd.OB_QUERY_ITEM), matterId, matterNameId)
  targetId = None
  cd = drive = None
  FJQC = _getMain().FormatJSONQuoteChar()
  returnIdOnly = showDetails = False
  while Cmd.ArgumentsRemaining():
    myarg = _getMain().getArgument()
    if myarg == 'name':
      body['displayName'] = _getMain().getString(Cmd.OB_STRING)
    elif copyCmd and myarg == 'targetmatter':
      targetId, targetNameId = getMatterItem(v)
    elif not copyCmd and myarg in VAULT_QUERY_ARGS:
      _buildVaultQuery(myarg, body['query'], VAULT_CORPUS_ARGUMENT_MAP)
    elif myarg == 'shownames':
      cd = _getMain().buildGAPIObject(API.DIRECTORY)
      _, drive = _getMain().buildGAPIServiceObject(API.DRIVE3, _getMain()._getAdminEmail())
      if drive is None:
        return
    elif myarg == 'showdetails':
      showDetails = True
      returnIdOnly = False
    elif myarg == 'returnidonly':
      returnIdOnly = True
      showDetails = False
    else:
      FJQC.GetFormatJSON(myarg)
  if copyCmd:
    if targetId is None:
      targetId = matterId
      targetNameId = matterNameId
    if not body['displayName']:
      body['displayName'] = f'Copy of {queryName}' if matterId == targetId else queryName
    resultId = targetId
    resultNameId = targetNameId
  else:
    _validateVaultQuery(body, VAULT_CORPUS_ARGUMENT_MAP)
    if not body['displayName']:
      body['displayName'] = 'GAM {body["query"]["corpus"]} Query - {ISOformatTimeStamp(todaysTime())}'
    resultId = matterId
    resultNameId = matterNameId
  try:
    result = _getMain().callGAPI(v.matters().savedQueries(), 'create',
                      throwReasons=[GAPI.NOT_FOUND, GAPI.BAD_REQUEST, GAPI.FORBIDDEN, GAPI.PERMISSION_DENIED, GAPI.INVALID_ARGUMENT, GAPI.ALREADY_EXISTS],
                      matterId=resultId, body=body)
    if not returnIdOnly:
      if not FJQC.formatJSON:
        _getMain().entityActionPerformed([Ent.VAULT_MATTER, matterNameId, Ent.VAULT_QUERY, formatVaultNameId(result['displayName'], result['savedQueryId'])])
      if showDetails or FJQC.formatJSON:
        _showVaultQuery(resultNameId, result, cd, drive, FJQC)
    else:
      _getMain().writeStdout(f'{result["savedQueryId"]}\n')
  except (GAPI.notFound, GAPI.badRequest, GAPI.forbidden, GAPI.permissionDenied, GAPI.invalidArgument, GAPI.alreadyExists) as e:
    _getMain().entityActionFailedWarning([Ent.VAULT_MATTER, resultNameId, Ent.VAULT_QUERY, body['displayName']], str(e))

# gam create vaultquery <MatterItem> [name <String>]
#	corpus calendar|drive|gemini|groups|hangouts_chat|mail|voice
#	[scope all_data|held_data|unprocessed_data]
#	(accounts <EmailAddressEntity>) | (orgunit|org|ou <OrgUnitPath>) | everyone|entireorg
#	(documentids  (<DriveFileIDList>|(select <FileSelector>|<CSVFileSelector>))) |
#	(shareddrives|teamdrives (<SharedDriveIDList>|(select <FileSelector>|<CSVFileSelector>))) |
#	[(includeshareddrives <Boolean>)|(shareddrivesoption included|included_if_account_is_not_a_member|not_included)]
#	(sitesurl (<URLList>||(select <FileSelector>|<CSVFileSelector>)))
#	[driveversiondate <Date>|<Time>]
#	[includerooms <Boolean>]
#	(rooms (<ChatSpaceList>|(select <FileSelector>|<CSVFileSelector>))) |
#	[terms <String>] [start|starttime <Date>|<Time>] [end|endtime <Date>|<Time>] [timezone <TimeZone>]
#	[locationquery <StringList>] [peoplequery <StringList>] [minuswords <StringList>]
#	[responsestatuses <AttendeeStatus>(,<AttendeeStatus>)*] [calendarversiondate <Date>|<Time>]
#	(covereddata calllogs|textmessages|voicemails)*
#	[<JSONData>]
#	[shownames]
#	[showdetails|returnidonly|formatjson]
def doCreateVaultQuery():
  doCreateCopyVaultQuery(False)

# gam copy vaultquery <MatterItem> <QueryItem> [targetmatter <MatterItem>] [name <String>]
#	[shownames]
#	[showdetails|returnidonly|formatjson]
def doCopyVaultQuery():
  doCreateCopyVaultQuery(True)

# gam delete vaultquery <QueryItem> matter <MatterItem>
# gam delete vaultquery <MatterItem> <QueryItem>
def doDeleteVaultQuery():
  v = _getMain().buildGAPIObject(API.VAULT)
  if not Cmd.ArgumentIsAhead('matter'):
    matterId, matterNameId = getMatterItem(v)
    queryId, queryName, queryNameId, _ = convertQueryNameToID(v, _getMain().getString(Cmd.OB_QUERY_ITEM), matterId, matterNameId)
  else:
    queryName = _getMain().getString(Cmd.OB_QUERY_ITEM)
  while Cmd.ArgumentsRemaining():
    myarg = _getMain().getArgument()
    if myarg == 'matter':
      matterId, matterNameId = getMatterItem(v)
      queryId, queryName, queryNameId, _ = convertQueryNameToID(v, queryName, matterId, matterNameId)
    else:
      _getMain().unknownArgumentExit()
  try:
    _getMain().callGAPI(v.matters().savedQueries(), 'delete',
             throwReasons=[GAPI.NOT_FOUND, GAPI.BAD_REQUEST, GAPI.FORBIDDEN, GAPI.PERMISSION_DENIED, GAPI.INVALID_ARGUMENT],
             matterId=matterId, savedQueryId=queryId)
    _getMain().entityActionPerformed([Ent.VAULT_MATTER, matterNameId, Ent.VAULT_QUERY, queryNameId])
  except (GAPI.notFound, GAPI.badRequest, GAPI.forbidden, GAPI.permissionDenied, GAPI.invalidArgument) as e:
    _getMain().entityActionFailedWarning([Ent.VAULT_MATTER, matterNameId, Ent.VAULT_QUERY, queryNameId], str(e))

VAULT_QUERY_FIELDS_CHOICE_MAP = {
  'createtime': 'createTime',
  'displayname': 'displayName',
  'matterid': 'matterId',
  'name': 'displayName',
  'query': 'query',
  'queryid': 'savedQueryId',
  'savedqueryid': 'savedQueryId',
  }

# gam info vaultquery <QueryItem> matter <MatterItem>
#	[fields <VaultQueryFieldNameList>] [shownames]
#	[formatjson]
# gam info vaultquery <MatterItem> <QueryItem>
#	[fields <VaultQueryFieldNameList>] [shownames]
#	[formatjson]
def doInfoVaultQuery():
  v = _getMain().buildGAPIObject(API.VAULT)
  if not Cmd.ArgumentIsAhead('matter'):
    matterId, matterNameId = getMatterItem(v)
    queryId, queryName, queryNameId, _ = convertQueryNameToID(v, _getMain().getString(Cmd.OB_QUERY_ITEM), matterId, matterNameId)
  else:
    queryName = _getMain().getString(Cmd.OB_QUERY_ITEM)
  cd = drive = None
  fieldsList = []
  FJQC = _getMain().FormatJSONQuoteChar()
  while Cmd.ArgumentsRemaining():
    myarg = _getMain().getArgument()
    if myarg == 'matter':
      matterId, matterNameId = getMatterItem(v)
      queryId, queryName, queryNameId, _ = convertQueryNameToID(v, queryName, matterId, matterNameId)
    elif myarg == 'shownames':
      cd = _getMain().buildGAPIObject(API.DIRECTORY)
      _, drive = _getMain().buildGAPIServiceObject(API.DRIVE3, _getMain()._getAdminEmail())
      if drive is None:
        return
    elif _getMain().getFieldsList(myarg, VAULT_QUERY_FIELDS_CHOICE_MAP, fieldsList, initialField=['savedQueryId', 'displayName']):
      pass
    else:
      FJQC.GetFormatJSON(myarg)
  fields = _getMain()._getMain().getFieldsFromFieldsList(fieldsList)
  try:
    query = _getMain().callGAPI(v.matters().savedQueries(), 'get',
                    throwReasons=[GAPI.NOT_FOUND, GAPI.BAD_REQUEST, GAPI.FORBIDDEN, GAPI.PERMISSION_DENIED, GAPI.INVALID_ARGUMENT],
                    matterId=matterId, savedQueryId=queryId, fields=fields)
    _showVaultQuery(matterNameId, query, cd, drive, FJQC)
  except (GAPI.notFound, GAPI.badRequest, GAPI.forbidden, GAPI.permissionDenied, GAPI.invalidArgument) as e:
    _getMain().entityActionFailedWarning([Ent.VAULT_MATTER, matterNameId, Ent.VAULT_QUERY, queryNameId], str(e))

PRINT_VAULT_QUERIES_TITLES = ['matterId', 'matterName', 'savedQueryId', 'displayName']

# gam print vaultqueries [todrive <ToDriveAttribute>*] [matters <MatterItemList>]
#	[fields <VaultQueryFieldNameList>] [shownames]
#	[formatjson [quotechar <Character>]]
# gam show vaultqueries [matters <MatterItemList>]
#	[fields <VaultQueryFieldNameList>] [shownames]
#	[formatjson]
def doPrintShowVaultQueries():
  v = _getMain().buildGAPIObject(API.VAULT)
  csvPF = _getMain().CSVPrintFile(PRINT_VAULT_QUERIES_TITLES, 'sortall') if Act.csvFormat() else None
  FJQC = _getMain().FormatJSONQuoteChar(csvPF)
  matters = []
  cd = drive = None
  fieldsList = []
  while Cmd.ArgumentsRemaining():
    myarg = _getMain().getArgument()
    if csvPF and myarg == 'todrive':
      csvPF.GetTodriveParameters()
    elif myarg in {'matter', 'matters'}:
      matters = _getMain().shlexSplitList(_getMain().getString(Cmd.OB_MATTER_ITEM_LIST))
    elif myarg == 'shownames':
      cd = _getMain().buildGAPIObject(API.DIRECTORY)
      _, drive = _getMain().buildGAPIServiceObject(API.DRIVE3, _getMain()._getAdminEmail())
      if drive is None:
        return
    elif _getMain().getFieldsList(myarg, VAULT_QUERY_FIELDS_CHOICE_MAP, fieldsList, initialField=['savedQueryId', 'displayName']):
      pass
    else:
      FJQC.GetFormatJSONQuoteChar(myarg, False)
  fields = _getMain().getItemFieldsFromFieldsList('savedQueries', fieldsList)
  if csvPF and FJQC.formatJSON:
    csvPF.SetJSONTitles(PRINT_VAULT_QUERIES_TITLES+['JSON'])
  if not matters:
    _getMain().printGettingAllAccountEntities(Ent.VAULT_MATTER, qualifier=' (OPEN)')
    try:
      results = _getMain()._getMain().callGAPIpages(v.matters(), 'list', 'matters',
                              pageMessage=_getMain().getPageMessage(),
                              throwReasons=[GAPI.FORBIDDEN, GAPI.PERMISSION_DENIED, GAPI.INVALID_ARGUMENT],
                              view='BASIC', state='OPEN', fields='matters(matterId,name,state),nextPageToken')
    except (GAPI.forbidden, GAPI.permissionDenied, GAPI.invalidArgument) as e:
      _getMain().entityActionFailedWarning([Ent.VAULT_QUERY, None], str(e))
      return
  else:
    results = []
    for matter in matters:
      matterId, matterName, _, state = convertMatterNameToID(v, matter)
      results.append({'matterId': matterId, 'name': matterName, 'state': state})
  jcount = len(results)
  if not csvPF:
    if jcount == 0:
      _getMain().setSysExitRC(_getMain().NO_ENTITIES_FOUND_RC)
  j = 0
  for matter in results:
    j += 1
    matterId = matter['matterId']
    matterName = matter['name']
    matterNameId = formatVaultNameId(matterName, matterId)
    if csvPF:
      _getMain().printGettingAllEntityItemsForWhom(Ent.VAULT_QUERY, f'{Ent.Singular(Ent.VAULT_MATTER)}: {matterNameId}', j, jcount)
      pageMessage = _getMain().getPageMessageForWhom()
    else:
      pageMessage = None
    if matter['state'] == 'OPEN':
      try:
        queries = _getMain()._getMain().callGAPIpages(v.matters().savedQueries(), 'list', 'savedQueries',
                                pageMessage=pageMessage,
                                throwReasons=[GAPI.FAILED_PRECONDITION, GAPI.FORBIDDEN, GAPI.PERMISSION_DENIED, GAPI.INVALID_ARGUMENT],
                                matterId=matterId, fields=fields)
      except GAPI.failedPrecondition:
        warnMatterNotOpen(v, matter, matterNameId, j, jcount)
        continue
      except (GAPI.forbidden, GAPI.permissionDenied, GAPI.invalidArgument) as e:
        _getMain().entityActionFailedWarning([Ent.VAULT_QUERY, None], str(e))
        break
    else:
      warnMatterNotOpen(None, matter, matterNameId, j, jcount)
      continue
    if not csvPF:
      kcount = len(queries)
      if not FJQC.formatJSON:
        _getMain().entityPerformActionNumItems([Ent.VAULT_MATTER, matterNameId], kcount, Ent.VAULT_QUERY, j, jcount)
      Ind.Increment()
      k = 0
      for query in queries:
        k += 1
        _showVaultQuery(matterNameId, query, cd, drive, FJQC, k, kcount)
      Ind.Decrement()
    else:
      for query in queries:
        _cleanVaultQuery(query, cd, drive)
        row = _getMain().flattenJSON(query, flattened={'matterId': matterId, 'matterName': matterName}, timeObjects=VAULT_QUERY_TIME_OBJECTS)
        if not FJQC.formatJSON:
          csvPF.WriteRowTitles(row)
        elif csvPF.CheckRowTitles(row):
          csvPF.WriteRowNoFilter({'matterId': matterId, 'matterName': matterName,
                                  'savedQueryId': query['savedQueryId'], 'displayName': query['displayName'],
                                  'JSON': json.dumps(_getMain().cleanJSON(query, timeObjects=VAULT_QUERY_TIME_OBJECTS), ensure_ascii=False, sort_keys=True)})
  if csvPF:
    csvPF.writeCSVfile('Vault Saved Queries')

def validateCollaborators(cd):
  collaborators = []
  for collaborator in _getMain().getEntityList(Cmd.OB_COLLABORATOR_ENTITY):
    collaborators.append({'email': collaborator, 'id': _getMain().convertEmailAddressToUID(collaborator, cd)})
  return collaborators

def _cleanVaultMatter(matter, cd):
  if cd is not None:
    if 'matterPermissions' in matter:
      for i in range(0, len(matter['matterPermissions'])):
        matter['matterPermissions'][i]['email'] = _getMain().convertUserIDtoEmail(matter["matterPermissions"][i]["accountId"], cd)

def _showVaultMatter(matter, cd, FJQC, j=0, jcount=0):
  _cleanVaultMatter(matter, cd)
  if FJQC is not None and FJQC.formatJSON:
    _getMain().printLine(json.dumps(_getMain().cleanJSON(matter), ensure_ascii=False, sort_keys=False))
    return
  _getMain().printEntity([Ent.VAULT_MATTER, formatVaultNameId(matter['name'], matter['matterId'])], j, jcount)
  Ind.Increment()
  _getMain().showJSON(None, matter)
  Ind.Decrement()

# gam create vaultmatter|matter [name <String>] [description <string>]
#	[collaborator|collaborators <CollaboratorItemList>] [sendemails <Boolean>] [ccme <Boolean>]
#	[showdetails|returnidonly]
def doCreateVaultMatter():
  v = _getMain().buildGAPIObject(API.VAULT)
  body = {}
  cbody = {'matterPermission': {'role': 'COLLABORATOR', 'accountId': ''}, 'sendEmails': False, 'ccMe': False}
  collaborators = []
  cd = None
  returnIdOnly = showDetails = False
  while Cmd.ArgumentsRemaining():
    myarg = _getMain().getArgument()
    if myarg == 'name':
      body['name'] = _getMain().getString(Cmd.OB_STRING)
    elif myarg == 'description':
      body['description'] = _getMain().getString(Cmd.OB_STRING, minLen=0)
    elif myarg in {'collaborator', 'collaborators'}:
      if not cd:
        cd = _getMain().buildGAPIObject(API.DIRECTORY)
      collaborators.extend(validateCollaborators(cd))
    elif myarg == 'sendemails':
      cbody['sendEmails'] = _getMain().getBoolean()
    elif myarg == 'ccme':
      cbody['ccMe'] = _getMain().getBoolean()
    elif myarg == 'showdetails':
      showDetails = True
      returnIdOnly = False
    elif myarg == 'returnidonly':
      returnIdOnly = True
      showDetails = False
    else:
      _getMain().unknownArgumentExit()
  if 'name' not in body:
    body['name'] = f'GAM Matter - {ISOformatTimeStamp(todaysTime())}'
  try:
    matter = _getMain().callGAPI(v.matters(), 'create',
                      throwReasons=[GAPI.ALREADY_EXISTS, GAPI.FORBIDDEN, GAPI.PERMISSION_DENIED, GAPI.INVALID_ARGUMENT],
                      body=body)
    matterId = matter['matterId']
    matterNameId = formatVaultNameId(matter['name'], matterId)
    if not returnIdOnly:
      _getMain().entityActionPerformed([Ent.VAULT_MATTER, matterNameId])
    else:
      _getMain().writeStdout(f'{matterId}\n')
  except (GAPI.alreadyExists, GAPI.forbidden, GAPI.permissionDenied, GAPI.invalidArgument) as e:
    _getMain().entityActionFailedWarning([Ent.VAULT_MATTER, body['name']], str(e))
    return
  jcount = len(collaborators)
  if jcount > 0:
    Act.Set(Act.ADD)
    if not returnIdOnly:
      _getMain().entityPerformActionNumItems([Ent.VAULT_MATTER, matterNameId], jcount, Ent.COLLABORATOR)
    Ind.Increment()
    j = 0
    for collaborator in collaborators:
      j += 1
      cbody['matterPermission']['accountId'] = collaborator['id']
      try:
        _getMain().callGAPI(v.matters(), 'addPermissions',
                 throwReasons=[GAPI.FAILED_PRECONDITION, GAPI.FORBIDDEN, GAPI.PERMISSION_DENIED, GAPI.INVALID_ARGUMENT],
                 matterId=matterId, body=cbody)
        if not returnIdOnly:
          _getMain().entityActionPerformed([Ent.VAULT_MATTER, matterNameId, Ent.COLLABORATOR, collaborator['email']], j, jcount)
      except (GAPI.failedPrecondition, GAPI.forbidden, GAPI.permissionDenied, GAPI.invalidArgument) as e:
        _getMain().entityActionFailedWarning([Ent.VAULT_MATTER, matterNameId], str(e))
        break
    Ind.Decrement()
  if showDetails:
    _showVaultMatter(matter, cd, None)

VAULT_MATTER_ACTIONS = {
  'close': Act.CLOSE,
  'reopen': Act.REOPEN,
  'delete': Act.DELETE,
  'undelete': Act.UNDELETE,
  }

def doActionVaultMatter(action, matterId=None, matterNameId=None, v=None):
  if v is None:
    v = _getMain().buildGAPIObject(API.VAULT)
    matterId, matterNameId = getMatterItem(v)
  else:
    Act.Set(VAULT_MATTER_ACTIONS[action])
  _getMain().checkForExtraneousArguments()
  action_kwargs = {} if action == 'delete' else {'body': {}}
  try:
    _getMain().callGAPI(v.matters(), action,
             throwReasons=[GAPI.NOT_FOUND, GAPI.FAILED_PRECONDITION, GAPI.FORBIDDEN, GAPI.PERMISSION_DENIED, GAPI.INVALID_ARGUMENT],
             matterId=matterId, **action_kwargs)
    _getMain().entityActionPerformed([Ent.VAULT_MATTER, matterNameId])
  except (GAPI.notFound, GAPI.failedPrecondition, GAPI.forbidden, GAPI.permissionDenied, GAPI.invalidArgument) as e:
    _getMain().entityActionFailedWarning([Ent.VAULT_MATTER, matterNameId], str(e))

# gam close vaultmatter|matter <MatterItem>
def doCloseVaultMatter():
  doActionVaultMatter('close')

# gam reopen vaultmatter|matter <MatterItem>
def doReopenVaultMatter():
  doActionVaultMatter('reopen')

# gam delete vaultmatter|matter <MatterItem>
def doDeleteVaultMatter():
  doActionVaultMatter('delete')

# gam undelete vaultmatter|matter <MatterItem>
def doUndeleteVaultMatter():
  doActionVaultMatter('undelete')

# gam update vaultmatter|matter <MatterItem> [name <String>] [description <string>]
#	[addcollaborator|addcollaborators <CollaboratorItemList>] [removecollaborator|removecollaborators <CollaboratorItemList>]
def doUpdateVaultMatter():
  v = _getMain().buildGAPIObject(API.VAULT)
  matterId, matterNameId = getMatterItem(v)
  body = {}
  addCollaborators = []
  removeCollaborators = []
  cd = None
  while Cmd.ArgumentsRemaining():
    myarg = _getMain().getArgument()
    if myarg == 'action':
      action = _getMain().getChoice(VAULT_MATTER_ACTIONS)
      doActionVaultMatter(action, matterId, matterNameId, v)
      return
    if myarg == 'name':
      body['name'] = _getMain().getString(Cmd.OB_STRING)
    elif myarg == 'description':
      body['description'] = _getMain().getString(Cmd.OB_STRING, minLen=0)
    elif myarg in {'addcollaborator', 'addcollaborators'}:
      if not cd:
        cd = _getMain().buildGAPIObject(API.DIRECTORY)
      addCollaborators.extend(validateCollaborators(cd))
    elif myarg in {'removecollaborator', 'removecollaborators'}:
      if not cd:
        cd = _getMain().buildGAPIObject(API.DIRECTORY)
      removeCollaborators.extend(validateCollaborators(cd))
    else:
      _getMain().unknownArgumentExit()
  if body:
    try:
      if 'name' not in body or 'description' not in body:
        # bah, API requires name/description to be sent on update even when it's not changing
        result = _getMain().callGAPI(v.matters(), 'get',
                          throwReasons=[GAPI.NOT_FOUND, GAPI.FORBIDDEN, GAPI.PERMISSION_DENIED, GAPI.INVALID_ARGUMENT],
                          matterId=matterId, view='BASIC')
        body.setdefault('name', result['name'])
        body.setdefault('description', result.get('description'))
      _getMain().callGAPI(v.matters(), 'update',
               throwReasons=[GAPI.NOT_FOUND, GAPI.FAILED_PRECONDITION, GAPI.FORBIDDEN],
               matterId=matterId, body=body)
      _getMain().entityActionPerformed([Ent.VAULT_MATTER, matterNameId])
    except (GAPI.notFound, GAPI.failedPrecondition, GAPI.forbidden, GAPI.permissionDenied, GAPI.invalidArgument) as e:
      _getMain().entityActionFailedWarning([Ent.VAULT_MATTER, matterNameId], str(e))
      return
  jcount = len(addCollaborators)
  if jcount > 0:
    Act.Set(Act.ADD)
    _getMain().entityPerformActionNumItems([Ent.VAULT_MATTER, matterNameId], jcount, Ent.COLLABORATOR)
    Ind.Increment()
    j = 0
    for collaborator in addCollaborators:
      j += 1
      try:
        _getMain().callGAPI(v.matters(), 'addPermissions',
                 throwReasons=[GAPI.FAILED_PRECONDITION, GAPI.FORBIDDEN, GAPI.PERMISSION_DENIED, GAPI.INVALID_ARGUMENT],
                 matterId=matterId, body={'matterPermission': {'role': 'COLLABORATOR', 'accountId': collaborator['id']}})
        _getMain().entityActionPerformed([Ent.VAULT_MATTER, matterNameId, Ent.COLLABORATOR, collaborator['email']], j, jcount)
      except (GAPI.failedPrecondition, GAPI.forbidden, GAPI.permissionDenied, GAPI.invalidArgument) as e:
        _getMain().entityActionFailedWarning([Ent.VAULT_MATTER, matterNameId], str(e))
        break
    Ind.Decrement()
  jcount = len(removeCollaborators)
  if jcount > 0:
    Act.Set(Act.REMOVE)
    _getMain().entityPerformActionNumItems([Ent.VAULT_MATTER, matterNameId], jcount, Ent.COLLABORATOR)
    Ind.Increment()
    j = 0
    for collaborator in removeCollaborators:
      j += 1
      try:
        _getMain().callGAPI(v.matters(), 'removePermissions',
                 throwReasons=[GAPI.FAILED_PRECONDITION, GAPI.FORBIDDEN, GAPI.PERMISSION_DENIED, GAPI.INVALID_ARGUMENT],
                 matterId=matterId, body={'accountId': collaborator['id']})
        _getMain().entityActionPerformed([Ent.VAULT_MATTER, matterNameId, Ent.COLLABORATOR, collaborator['email']], j, jcount)
      except (GAPI.failedPrecondition, GAPI.forbidden, GAPI.permissionDenied, GAPI.invalidArgument) as e:
        _getMain().entityActionFailedWarning([Ent.VAULT_MATTER, matterNameId], str(e))
        break
    Ind.Decrement()

VAULT_MATTER_FIELDS_CHOICE_MAP = {
  'matterid': 'matterId',
  'name': 'name',
  'description': 'description',
  'state': 'state',
  'matterpermissions': 'matterPermissions',
  }

# gam info vaultmatter|matter <MatterItem>
#	[basic|full|(fields <VaultMatterFieldNameList>)]
#	[formatjson]
def doInfoVaultMatter():
  v = _getMain().buildGAPIObject(API.VAULT)
  matterId, matterNameId = getMatterItem(v)
  view = 'FULL'
  fieldsList = []
  FJQC = _getMain().FormatJSONQuoteChar()
  while Cmd.ArgumentsRemaining():
    myarg = _getMain().getArgument()
    if myarg in _getMain().PROJECTION_CHOICE_MAP:
      view = _getMain().PROJECTION_CHOICE_MAP[myarg]
    elif _getMain().getFieldsList(myarg, VAULT_MATTER_FIELDS_CHOICE_MAP, fieldsList, initialField=['matterId', 'name']):
      pass
    else:
      FJQC.GetFormatJSON(myarg)
  fields = _getMain()._getMain().getFieldsFromFieldsList(fieldsList)
  try:
    matter = _getMain().callGAPI(v.matters(), 'get',
                      throwReasons=[GAPI.NOT_FOUND, GAPI.FORBIDDEN, GAPI.PERMISSION_DENIED, GAPI.INVALID_ARGUMENT],
                      matterId=matterId, view=view, fields=fields)
    cd = _getMain().buildGAPIObject(API.DIRECTORY) if 'matterPermissions' in matter else None
    _showVaultMatter(matter, cd, FJQC)
  except (GAPI.notFound, GAPI.forbidden, GAPI.permissionDenied, GAPI.invalidArgument) as e:
    _getMain().entityActionFailedWarning([Ent.VAULT_MATTER, matterNameId], str(e))

VAULT_MATTER_STATE_MAP = {'open': 'OPEN', 'closed': 'CLOSED', 'deleted': 'DELETED'}
PRINT_VAULT_MATTERS_TITLES = ['matterId', 'name', 'description', 'state']

# gam print vaultmatters|matters [todrive <ToDriveAttribute>*] [matterstate <MatterStateList>]
#	[basic|full|(fields <VaultMatterFieldNameList>)]
#	[formatjson [quotechar <Character>]]
# gam show vaultmatters|matters [matterstate <MatterStateList>]
#	[basic|full|(fields <VaultMatterFieldNameList>)]
#	[formatjson]
def doPrintShowVaultMatters():
  v = _getMain().buildGAPIObject(API.VAULT)
  csvPF = _getMain().CSVPrintFile(PRINT_VAULT_MATTERS_TITLES, 'sortall') if Act.csvFormat() else None
  FJQC = _getMain().FormatJSONQuoteChar(csvPF)
  cd = None
  view = 'FULL'
  fieldsList = []
  matterStatesList = []
  while Cmd.ArgumentsRemaining():
    myarg = _getMain().getArgument()
    if csvPF and myarg == 'todrive':
      csvPF.GetTodriveParameters()
    elif myarg == 'matterstate':
      for state in _getMain().getString(Cmd.OB_STATE_NAME_LIST).lower().replace('_', '').replace(',', ' ').split():
        if state in VAULT_MATTER_STATE_MAP:
          matterStatesList.append(VAULT_MATTER_STATE_MAP[state])
        else:
          _getMain().invalidChoiceExit(state, list(VAULT_MATTER_STATE_MAP), True)
    elif myarg in _getMain().PROJECTION_CHOICE_MAP:
      view = _getMain().PROJECTION_CHOICE_MAP[myarg]
    elif _getMain().getFieldsList(myarg, VAULT_MATTER_FIELDS_CHOICE_MAP, fieldsList, initialField=['matterId', 'name']):
      pass
    else:
      FJQC.GetFormatJSONQuoteChar(myarg, False)
  if fieldsList and matterStatesList:
    fieldsList.append('state')
  fields = f'nextPageToken,matters({_getMain().getFieldsFromFieldsList(fieldsList)})' if fieldsList else None
  if csvPF and FJQC.formatJSON:
    csvPF.SetJSONTitles(PRINT_VAULT_MATTERS_TITLES+['JSON'])
  # If no states are set, there is no filtering; if 1 state is set, the API can filter; else GAM filters
  matterStates = set()
  stateParm = None
  if matterStatesList:
    if len(matterStatesList) == 1:
      stateParm = matterStatesList[0]
    else:
      matterStates = set(matterStatesList)
    qualifier = f' ({",".join(matterStatesList)})'
  else:
    qualifier = ''
  _getMain().printGettingAllAccountEntities(Ent.VAULT_MATTER, qualifier=qualifier)
  try:
    matters = _getMain()._getMain().callGAPIpages(v.matters(), 'list', 'matters',
                            pageMessage=_getMain().getPageMessage(),
                            throwReasons=[GAPI.FORBIDDEN, GAPI.PERMISSION_DENIED, GAPI.INVALID_ARGUMENT, GAPI.INVALID_ARGUMENT],
                            view=view, state=stateParm, fields=fields)
  except (GAPI.forbidden, GAPI.permissionDenied, GAPI.invalidArgument, GAPI.invalidArgument) as e:
    _getMain().entityActionFailedWarning([Ent.VAULT_MATTER, None], str(e))
    return
  jcount = len(matters)
  if view == 'FULL':
    cd = _getMain().buildGAPIObject(API.DIRECTORY)
  if not csvPF:
    if jcount == 0:
      _getMain().setSysExitRC(_getMain().NO_ENTITIES_FOUND_RC)
    if not FJQC.formatJSON:
      _getMain().performActionNumItems(jcount, Ent.VAULT_MATTER)
    Ind.Increment()
    j = 0
    for matter in matters:
      j += 1
      if not matterStates or matter['state'] in matterStates:
        _showVaultMatter(matter, cd, FJQC, j, jcount)
    Ind.Decrement()
  else:
    for matter in matters:
      if not matterStates or matter['state'] in matterStates:
        _cleanVaultMatter(matter, cd)
        row = _getMain().flattenJSON(matter)
        if not FJQC.formatJSON:
          csvPF.WriteRowTitles(row)
        elif csvPF.CheckRowTitles(row):
          csvPF.WriteRowNoFilter({'matterId': matter['matterId'], 'name': matter['name'],
                                  'JSON': json.dumps(_getMain().cleanJSON(matter), ensure_ascii=False, sort_keys=True)})
  if csvPF:
    csvPF.writeCSVfile('Vault Matters')

PRINT_VAULT_COUNTS_TITLES = ['account', 'count', 'error']

# gam print vaultcounts [todrive <ToDriveAttributes>*]
#	matter <MatterItem> <QueryItem>
#	[wait <Integer>]
# gam print vaultcounts [todrive <ToDriveAttributes>*]
#	matter <MatterItem>
#	corpus mail|groups
#	[scope all_data|held_data|unprocessed_data]
#	(accounts <EmailAddressEntity>) | (orgunit|org|ou <OrgUnitPath>) | everyone|entireorg
#	[terms <String>] [start|starttime <Date>|<Time>] [end|endtime <Date>|<Time>] [timezone <TimeZone>]
#	[excludedrafts <Boolean>]
#	[<JSONData>]
#	[wait <Integer>]
#	[include_suspended_zeros [<Boolean>]]
# gam print vaultcounts [todrive <ToDriveAttributes>*]
#	 matter <MatterItem> operation <String> [wait <Integer>]
def doPrintVaultCounts():
  v = _getMain().buildGAPIObject(API.VAULT)
  csvPF = _getMain().CSVPrintFile(PRINT_VAULT_COUNTS_TITLES, 'sortall')
  includeSuspendedZeros = False
  matterId = name = None
  operationWait = 15
  body = {'view': 'ALL', 'query': {}}
  while Cmd.ArgumentsRemaining():
    myarg = _getMain().getArgument()
    if csvPF and myarg == 'todrive':
      csvPF.GetTodriveParameters()
    elif myarg == 'matter':
      matterId, matterNameId = getMatterItem(v)
    elif matterId is not None and myarg == 'vaultquery':
      _, _, _, body['query'] = convertQueryNameToID(v, _getMain().getString(Cmd.OB_QUERY_ITEM), matterId, matterNameId)
    elif myarg == 'operation':
      name = _getMain().getString(Cmd.OB_STRING)
    elif myarg in VAULT_QUERY_ARGS:
      _buildVaultQuery(myarg, body['query'], VAULT_COUNTS_CORPUS_ARGUMENT_MAP)
    elif myarg == 'wait':
      operationWait = _getMain().getInteger(minVal=1)
    elif myarg == "includesuspendedzeros":
      includeSuspendedZeros = _getMain().getBoolean()
    else:
      _getMain().unknownArgumentExit()
  if not matterId:
    _getMain().missingArgumentExit('matter')
  if name:
    operation = {'name': name}
    doWait = False
  else:
    _validateVaultQuery(body, VAULT_COUNTS_CORPUS_ARGUMENT_MAP)
    try:
      operation = _getMain().callGAPI(v.matters(), 'count',
                           throwReasons=[GAPI.INVALID_ARGUMENT],
                           matterId=matterId, body=body)
    except GAPI.invalidArgument as e:
      _getMain().entityActionFailedExit([Ent.VAULT_MATTER, matterId], str(e))
    doWait = True
  _getMain().printGettingAllAccountEntities(Ent.VAULT_MATTER_ARTIFACT, qualifier=f' for {Ent.Singular(Ent.VAULT_OPERATION)}: {operation["name"]}',
                                 accountType=Ent.VAULT_MATTER)
  while not operation.get('done'):
    if doWait:
      _getMain().stderrEntityMessage([Ent.VAULT_OPERATION, operation['name']], Msg.IS_NOT_DONE_CHECKING_IN_SECONDS.format(operationWait))
      time.sleep(operationWait)
    try:
      operation = _getMain().callGAPI(v.operations(), 'get',
                           throwReasons=[GAPI.NOT_FOUND],
                           name=operation['name'])
    except GAPI.notFound as e:
      _getMain().entityActionFailedExit([Ent.VAULT_OPERATION, operation['name']], str(e))
    doWait = True
  response = operation.get('response', {})
  query = operation['metadata']['query']
  search_method = query.get('method')
  # ARGH count results don't include accounts with zero items.
  # so we keep track of which accounts we searched and can report
  # zero data for them.
  if search_method == 'ACCOUNT':
    query_accounts = query.get('accountInfo', {}).get('emails', [])
  elif search_method == 'ENTIRE_ORG':
    query_accounts = _getMain().getItemsToModify(Cmd.ENTITY_ALL_USERS if not includeSuspendedZeros else Cmd.ENTITY_ALL_USERS_NS_SUSP,
                                      '')
  elif search_method == 'ORG_UNIT':
    query_accounts = _getMain().getItemsToModify(Cmd.ENTITY_OU if not includeSuspendedZeros else Cmd.ENTITY_OU_NS_SUSP,
                                      query['orgUnitInfo']['orgUnitId'])
  else:
    query_accounts = []
  mailcounts = response.get('mailCountResult', {})
  groupcounts = response.get('groupsCountResult', {})
  for a_count in [mailcounts, groupcounts]:
    for errored_account in a_count.get('accountCountErrors', []):
      email = errored_account.get('account', {}).get('email', '')
      if email:
        csvPF.WriteRow({'account': email, 'error': errored_account.get('errorType')})
        if email in query_accounts:
          query_accounts.remove(email)
    for account in a_count.get('nonQueryableAccounts', []):
      csvPF.WriteRow({'account': account, 'error': 'Not queried because not on hold'})
      if account in query_accounts:
        query_accounts.remove(account)
    for account in a_count.get('accountCounts', []):
      email = account.get('account', {}).get('email', '')
      if email:
        csvPF.WriteRow({'account': email, 'count': account.get('count', 0)})
        if email in query_accounts:
          query_accounts.remove(email)
  for account in query_accounts:
    csvPF.WriteRow({'account': account, 'count': 0})
  csvPF.writeCSVfile('Vault Counts')

# gam [<UserTypeEntity>] create site <SiteName> <SiteAttribute>*
# gam [<UserTypeEntity>] update site <SiteEntity> <SiteAttribute>+
# gam [<UserTypeEntity>] info site <SiteEntity> [withmappings] [role|roles all|<SiteACLRoleList>]
# gam [<UserTypeEntity>] print sites [todrive <ToDriveAttribute>*] [domain|domains <DomainNameEntity>] [includeallsites]
#	[withmappings] [role|roles all|<SiteACLRoleList>] [startindex <Number>] [maxresults <Number>] [convertcrnl] [delimiter <Character>]
# gam [<UserTypeEntity>] show sites [domain|domains <DomainNameEntity>] [includeallsites]
#	[withmappings] [role|roles all|<SiteACLRoleList>] [startindex <Number>] [maxresults <Number>] [convertcrnl]
# gam [<UserTypeEntity>] create siteacls <SiteEntity> <SiteACLRole> <SiteACLScopeEntity>
# gam [<UserTypeEntity>] update siteacls <SiteEntity> <SiteACLRole> <SiteACLScopeEntity>
# gam [<UserTypeEntity>] delete siteacls <SiteEntity> <SiteACLScopeEntity>
# gam [<UserTypeEntity>] info siteacls <SiteEntity> <SiteACLScopeEntity>
# gam [<UserTypeEntity>] show siteacls <SiteEntity>
# gam [<UserTypeEntity>] print siteacls <SiteEntity> [todrive <ToDriveAttribute>*]
# gam [<UserTypeEntity>] print siteactivity <SiteEntity> [todrive <ToDriveAttribute>*]
#	[startindex <Number>] [maxresults <Number>] [updated_min <Date>] [updated_max <Date>]
