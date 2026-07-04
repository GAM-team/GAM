"""Vault hold, query, and count management.

Part of the _vault_tmp sub-package."""

"""GAM Google Vault management."""

import json

from gam.cmd.vault.matters import _buildVaultQuery, _validateVaultQuery, convertHoldNameToID, convertMatterNameToID, convertQueryNameToID, formatVaultNameId, getMatterItem, warnMatterNotOpen

from gam.cmd.vault.matters import (
    VAULT_CORPUS_ARGUMENT_MAP,
    VAULT_CORPUS_QUERY_MAP,
    VAULT_COUNTS_CORPUS_ARGUMENT_MAP,
    VAULT_QUERY_ARGS,
    VAULT_VOICE_COVERED_DATA_MAP,
)
import time

from gamlib import api as API
from gamlib import gapi as GAPI
from gamlib import msgs as Msg
from gam.constants import NO_ENTITIES_FOUND_RC, PROJECTION_CHOICE_MAP

from gam.var import Act, Cmd, Ent, Ind

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
from gam.util.api import _getAdminEmail, buildGAPIObject
from gam.util.svcacct import buildGAPIServiceObject
from gam.util.api_call import callGAPI, callGAPIpages
from gam.util.args import (
    checkForExtraneousArguments,
    getArgument,
    getBoolean,
    getChoice,
    getInteger,
    getString,
    getTimeOrDeltaFromNow,
    normalizeEmailAddressOrUID,
)
from gam.util.csv_pf import (
    CSVPrintFile,
    FormatJSONQuoteChar,
    cleanJSON,
    flattenJSON,
    getFieldsFromFieldsList,
    getFieldsList,
    getItemFieldsFromFieldsList,
    showJSON,
)
from gam.util.display import (
    entityActionFailedWarning,
    entityActionPerformed,
    entityPerformActionNumItems,
    getPageMessage,
    getPageMessageForWhom,
    performActionNumItems,
    printEntity,
    printEntityMessage,
    printGettingAllAccountEntities,
    printGettingAllEntityItemsForWhom,
    printKeyValueList,
    printLine,
    stderrEntityMessage,
)
from gam.util.entity import (
    convertEmailAddressToUID,
    convertOrgUnitIDtoPath,
    convertUIDtoEmailAddress,
    convertUserIDtoEmail,
    getEntityArgument,
    getEntityList,
    getItemsToModify,
    shlexSplitList,
)
from gam.util.errors import (
    entityActionFailedExit,
    invalidChoiceExit,
    missingArgumentExit,
    unknownArgumentExit,
    usageErrorExit,
)
from gam.util.orgunits import getAllParentOrgUnitsForUser, getOrgUnitId
from gam.util.output import setSysExitRC, writeStdout
from gam.cmd.drive.core import _getSharedDriveNameFromId

def _cleanVaultHold(hold, cd):
  if cd is not None:
    if 'accounts' in hold:
      accountType = 'group' if hold['corpus'] == 'GROUPS' else 'user'
      for i in range(0, len(hold['accounts'])):
        hold['accounts'][i]['email'] = convertUIDtoEmailAddress(f'uid:{hold["accounts"][i]["accountId"]}', cd, accountType)
    if 'orgUnit' in hold:
      hold['orgUnit']['orgUnitPath'] = convertOrgUnitIDtoPath(cd, hold['orgUnit']['orgUnitId'])
  query = hold.get('query')
  if query:
    if 'driveQuery' in hold['query']:
      hold['query']['driveQuery'].pop('includeTeamDriveFiles', None)

VAULT_HOLD_TIME_OBJECTS = {'holdTime', 'updateTime', 'startTime', 'endTime'}

def _showVaultHold(matterNameId, hold, cd, FJQC, k=0, kcount=0):
  _cleanVaultHold(hold, cd)
  if FJQC is not None and FJQC.formatJSON:
    printLine(json.dumps(cleanJSON(hold, timeObjects=VAULT_HOLD_TIME_OBJECTS), ensure_ascii=False, sort_keys=False))
    return
  if matterNameId is not None:
    printEntity([Ent.VAULT_MATTER, matterNameId, Ent.VAULT_HOLD, formatVaultNameId(hold['name'], hold['holdId'])], k, kcount)
  Ind.Increment()
  showJSON(None, hold, timeObjects=VAULT_HOLD_TIME_OBJECTS)
  Ind.Decrement()

def _useVaultQueryForHold(v, matterId, matterNameId, body):
  _, _, _, query = convertQueryNameToID(v, getString(Cmd.OB_QUERY_ITEM), matterId, matterNameId)
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
    queryParameters['query'] = getString(Cmd.OB_QUERY)
  elif myarg == 'terms':
    queryParameters['terms'] = getString(Cmd.OB_STRING)
  elif myarg in {'start', 'starttime'}:
    queryParameters['startTime'] = getTimeOrDeltaFromNow()
  elif myarg in {'end', 'endtime'}:
    queryParameters['endTime'] = getTimeOrDeltaFromNow()
  elif myarg == 'includerooms':
    queryParameters['includeRooms'] = getBoolean()
  elif myarg in {'includeshareddrives', 'includeteamdrives'}:
    queryParameters['includeSharedDriveFiles'] = getBoolean()
  elif myarg == 'covereddata':
    queryParameters.setdefault('coveredData', [])
    queryParameters['coveredData'].append(getChoice(VAULT_VOICE_COVERED_DATA_MAP, mapChoice=True))
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
        usageErrorExit(f'{str(e)}: {queryParameters["query"]}')
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
  v = buildGAPIObject(API.VAULT)
  body = {}
  matterId = None
  accounts = []
  queryParameters = {}
  returnIdOnly = showDetails = usedVaultQuery  = False
  while Cmd.ArgumentsRemaining():
    myarg = getArgument()
    if myarg == 'matter':
      matterId, matterNameId = getMatterItem(v)
    elif myarg == 'name':
      body['name'] = getString(Cmd.OB_STRING)
    elif matterId is not None and myarg == 'vaultquery':
      _useVaultQueryForHold(v, matterId, matterNameId, body)
      usedVaultQuery = True
    elif myarg == 'corpus':
      body['corpus'] = getChoice(VAULT_CORPUS_ARGUMENT_MAP, mapChoice=True)
    elif myarg in {'accounts', 'users', 'groups'}:
      accountsLocation = Cmd.Location()
      accounts = getEntityList(Cmd.OB_EMAIL_ADDRESS_ENTITY)
    elif myarg in {'ou', 'org', 'orgunit'}:
      body['orgUnit'] = {'orgUnitId': getOrgUnitId()[1]}
    elif _getHoldQueryParameters(myarg, queryParameters):
      pass
    elif myarg == 'showdetails':
      showDetails = True
      returnIdOnly = False
    elif myarg == 'returnidonly':
      returnIdOnly = True
      showDetails = False
    else:
      unknownArgumentExit()
  if matterId is None:
    missingArgumentExit('matter')
  if not body.get('corpus'):
    missingArgumentExit(f'corpus {"|".join(VAULT_CORPUS_ARGUMENT_MAP)}')
  if 'name' not in body:
    body['name'] = f'GAM {body["corpus"]} Hold - {ISOformatTimeStamp(todaysTime())}'
  if not usedVaultQuery:
    _setHoldQuery(body, queryParameters)
  if accounts:
    body['accounts'] = []
    cd = buildGAPIObject(API.DIRECTORY)
    accountType = 'group' if body['corpus'] == 'GROUPS' else 'user'
    for account in accounts:
      body['accounts'].append({'accountId': convertEmailAddressToUID(account, cd, accountType, accountsLocation)})
  try:
    hold = callGAPI(v.matters().holds(), 'create',
                    throwReasons=[GAPI.ALREADY_EXISTS, GAPI.BAD_REQUEST, GAPI.BACKEND_ERROR, GAPI.FAILED_PRECONDITION,
                                  GAPI.FORBIDDEN, GAPI.PERMISSION_DENIED, GAPI.INVALID_ARGUMENT],
                    matterId=matterId, body=body)
    if not returnIdOnly:
      entityActionPerformed([Ent.VAULT_MATTER, matterNameId, Ent.VAULT_HOLD, formatVaultNameId(hold['name'], hold['holdId'])])
      if showDetails:
        _showVaultHold(None, hold, None, None)
    else:
      writeStdout(f'{hold["holdId"]}\n')
  except (GAPI.alreadyExists, GAPI.badRequest, GAPI.backendError, GAPI.failedPrecondition,
          GAPI.forbidden, GAPI.permissionDenied, GAPI.invalidArgument) as e:
    entityActionFailedWarning([Ent.VAULT_MATTER, matterNameId, Ent.VAULT_HOLD, body.get('name')], str(e))

# gam update vaulthold|hold <HoldItem> matter <MatterItem>
#	[([addaccounts|addgroups|addusers <EmailItemList>] [removeaccounts|removegroups|removeusers <EmailItemList>]) | (orgunit|org|ou <OrgUnit>)]
#	[query <QueryVaultCorpus>]
#	[terms <String>] [start|starttime <Date>|<Time>] [end|endtime <Date>|<Time>]
#	[includerooms <Boolean>]
#	[covereddata calllogs|textmessages|voicemails]
#	[includeshareddrives <Boolean>]
#	[showdetails]
def doUpdateVaultHold():
  v = buildGAPIObject(API.VAULT)
  holdName = getString(Cmd.OB_HOLD_ITEM)
  body = {}
  cd = matterId = None
  addAccounts = []
  addAccountIds = []
  removeAccounts = []
  removeAccountIds = []
  queryParameters = {}
  showDetails = False
  while Cmd.ArgumentsRemaining():
    myarg = getArgument()
    if myarg == 'matter':
      matterId, matterNameId = getMatterItem(v)
      holdId, holdName, holdNameId = convertHoldNameToID(v, holdName, matterId, matterNameId)
    elif myarg in {'addusers', 'addaccounts', 'addgroups'}:
      addAccountsLocation = Cmd.Location()
      addAccounts = getEntityList(Cmd.OB_EMAIL_ADDRESS_ENTITY)
    elif myarg in {'removeusers', 'removeaccounts', 'removegroups'}:
      removeAccountsLocation = Cmd.Location()
      removeAccounts = getEntityList(Cmd.OB_EMAIL_ADDRESS_ENTITY)
    elif myarg in {'ou', 'org', 'orgunit'}:
      body['orgUnit'] = {'orgUnitId': getOrgUnitId()[1]}
    elif _getHoldQueryParameters(myarg, queryParameters):
      pass
    elif myarg == 'showdetails':
      showDetails = True
    else:
      unknownArgumentExit()
  if matterId is None:
    missingArgumentExit('matter')
  try:
    old_body = callGAPI(v.matters().holds(), 'get',
                        throwReasons=[GAPI.NOT_FOUND, GAPI.BAD_REQUEST, GAPI.FORBIDDEN, GAPI.PERMISSION_DENIED, GAPI.INVALID_ARGUMENT],
                        matterId=matterId, holdId=holdId, fields='name,corpus,query,orgUnit')
  except (GAPI.notFound, GAPI.badRequest, GAPI.forbidden, GAPI.permissionDenied, GAPI.invalidArgument) as e:
    entityActionFailedWarning([Ent.VAULT_MATTER, matterNameId, Ent.VAULT_HOLD, holdNameId], str(e))
    return
  accountType = 'group' if old_body['corpus'] == 'GROUPS' else 'user'
  if addAccounts:
    if cd is None:
      cd = buildGAPIObject(API.DIRECTORY)
    for account in addAccounts:
      addAccountIds.append({'email': account, 'id': convertEmailAddressToUID(account, cd, accountType, addAccountsLocation)})
  if removeAccounts:
    if cd is None:
      cd = buildGAPIObject(API.DIRECTORY)
    for account in removeAccounts:
      removeAccountIds.append({'email': account, 'id': convertEmailAddressToUID(account, cd, accountType, removeAccountsLocation)})
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
      hold = callGAPI(v.matters().holds(), 'update',
                      throwReas=[GAPI.NOT_FOUND, GAPI.BAD_REQUEST, GAPI.FORBIDDEN, GAPI.PERMISSION_DENIED, GAPI.INVALID_ARGUMENT],
                      matterId=matterId, holdId=holdId, body=body)
      entityActionPerformed([Ent.VAULT_MATTER, matterNameId, Ent.VAULT_HOLD, holdNameId])
    except (GAPI.notFound, GAPI.badRequest, GAPI.forbidden, GAPI.permissionDenied, GAPI.invalidArgument) as e:
      entityActionFailedWarning([Ent.VAULT_MATTER, matterNameId, Ent.VAULT_HOLD, holdNameId], str(e))
      return
  jcount = len(addAccountIds)
  if jcount > 0:
    Act.Set(Act.ADD)
    entityPerformActionNumItems([Ent.VAULT_MATTER, matterNameId, Ent.VAULT_HOLD, holdNameId], jcount, Ent.ACCOUNT)
    Ind.Increment()
    j = 0
    for account in addAccountIds:
      j += 1
      try:
        callGAPI(v.matters().holds().accounts(), 'create',
                 throwReasons=[GAPI.ALREADY_EXISTS, GAPI.BACKEND_ERROR, GAPI.FORBIDDEN, GAPI.PERMISSION_DENIED, GAPI.INVALID_ARGUMENT],
                 matterId=matterId, holdId=holdId, body={'accountId': account['id']})
        entityActionPerformed([Ent.VAULT_MATTER, matterNameId, Ent.VAULT_HOLD, holdNameId, Ent.ACCOUNT, account['email']], j, jcount)
      except (GAPI.alreadyExists, GAPI.backendError) as e:
        entityActionFailedWarning([Ent.VAULT_MATTER, matterNameId, Ent.VAULT_HOLD, holdNameId, Ent.ACCOUNT, account['email']], str(e), j, jcount)
      except (GAPI.forbidden, GAPI.permissionDenied, GAPI.invalidArgument) as e:
        entityActionFailedWarning([Ent.VAULT_MATTER, matterNameId, Ent.VAULT_HOLD, None], str(e))
        return
    Ind.Decrement()
  jcount = len(removeAccountIds)
  if jcount > 0:
    Act.Set(Act.REMOVE)
    if cd is None:
      cd = buildGAPIObject(API.DIRECTORY)
    entityPerformActionNumItems([Ent.VAULT_MATTER, matterNameId, Ent.VAULT_HOLD, holdNameId], jcount, Ent.ACCOUNT)
    Ind.Increment()
    j = 0
    for account in removeAccountIds:
      j += 1
      try:
        callGAPI(v.matters().holds().accounts(), 'delete',
                 throwReasons=[GAPI.NOT_FOUND, GAPI.BACKEND_ERROR, GAPI.FORBIDDEN, GAPI.PERMISSION_DENIED, GAPI.INVALID_ARGUMENT],
                 matterId=matterId, holdId=holdId, accountId=account['id'])
        entityActionPerformed([Ent.VAULT_MATTER, matterNameId, Ent.VAULT_HOLD, holdNameId, Ent.ACCOUNT, account['email']], j, jcount)
      except (GAPI.alreadyExists, GAPI.backendError) as e:
        entityActionFailedWarning([Ent.VAULT_MATTER, matterNameId, Ent.VAULT_HOLD, holdNameId, Ent.ACCOUNT, account['email']], str(e), j, jcount)
      except (GAPI.forbidden, GAPI.permissionDenied, GAPI.invalidArgument) as e:
        entityActionFailedWarning([Ent.VAULT_MATTER, matterNameId, Ent.VAULT_HOLD, None], str(e))
        return
    Ind.Decrement()
  if showDetails:
    _showVaultHold(None, hold, cd, None)

# gam delete vaulthold|hold <HoldItem> matter <MatterItem>
# gam delete vaulthold|hold <MatterItem> <HoldItem>
def doDeleteVaultHold():
  v = buildGAPIObject(API.VAULT)
  if not Cmd.ArgumentIsAhead('matter'):
    matterId, matterNameId = getMatterItem(v)
    holdId, holdName, holdNameId = convertHoldNameToID(v, getString(Cmd.OB_HOLD_ITEM), matterId, matterNameId)
  else:
    holdName = getString(Cmd.OB_HOLD_ITEM)
  while Cmd.ArgumentsRemaining():
    myarg = getArgument()
    if myarg == 'matter':
      matterId, matterNameId = getMatterItem(v)
      holdId, holdName, holdNameId = convertHoldNameToID(v, holdName, matterId, matterNameId)
    else:
      unknownArgumentExit()
  try:
    callGAPI(v.matters().holds(), 'delete',
             throwReasons=[GAPI.NOT_FOUND, GAPI.BAD_REQUEST, GAPI.FORBIDDEN, GAPI.PERMISSION_DENIED, GAPI.INVALID_ARGUMENT],
             matterId=matterId, holdId=holdId)
    entityActionPerformed([Ent.VAULT_MATTER, matterNameId, Ent.VAULT_HOLD, holdNameId])
  except (GAPI.notFound, GAPI.badRequest, GAPI.forbidden, GAPI.permissionDenied, GAPI.invalidArgument) as e:
    entityActionFailedWarning([Ent.VAULT_MATTER, matterNameId, Ent.VAULT_HOLD, holdNameId], str(e))

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
  v = buildGAPIObject(API.VAULT)
  if not Cmd.ArgumentIsAhead('matter'):
    matterId, matterNameId = getMatterItem(v)
    holdId, holdName, holdNameId = convertHoldNameToID(v, getString(Cmd.OB_HOLD_ITEM), matterId, matterNameId)
  else:
    holdName = getString(Cmd.OB_HOLD_ITEM)
  cd = None
  fieldsList = []
  FJQC = FormatJSONQuoteChar()
  while Cmd.ArgumentsRemaining():
    myarg = getArgument()
    if myarg == 'matter':
      matterId, matterNameId = getMatterItem(v)
      holdId, holdName, holdNameId = convertHoldNameToID(v, holdName, matterId, matterNameId)
    elif myarg == 'shownames':
      cd = buildGAPIObject(API.DIRECTORY)
    elif getFieldsList(myarg, VAULT_HOLD_FIELDS_CHOICE_MAP, fieldsList, initialField=['holdId', 'name']):
      pass
    else:
      FJQC.GetFormatJSON(myarg)
  fields = getFieldsFromFieldsList(fieldsList)
  try:
    hold = callGAPI(v.matters().holds(), 'get',
                    throwReasons=[GAPI.NOT_FOUND, GAPI.BAD_REQUEST, GAPI.FORBIDDEN, GAPI.PERMISSION_DENIED, GAPI.INVALID_ARGUMENT],
                    matterId=matterId, holdId=holdId, fields=fields)
    _showVaultHold(matterNameId, hold, cd, FJQC)
  except (GAPI.notFound, GAPI.badRequest, GAPI.forbidden, GAPI.permissionDenied, GAPI.invalidArgument) as e:
    entityActionFailedWarning([Ent.VAULT_MATTER, matterNameId, Ent.VAULT_HOLD, holdNameId], str(e))

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
    row = flattenJSON(hold, flattened={'matterId': matterId, 'matterName': matterName}, timeObjects=VAULT_HOLD_TIME_OBJECTS)
    if not FJQC.formatJSON:
      csvPF.WriteRowTitles(row)
    elif csvPF.CheckRowTitles(row):
      csvPF.WriteRowNoFilter({'matterId': matterId, 'matterName': matterName,
                              'holdId': hold['holdId'], 'name': hold['name'],
                              'JSON': json.dumps(cleanJSON(hold, timeObjects=VAULT_HOLD_TIME_OBJECTS), ensure_ascii=False, sort_keys=True)})

  v = buildGAPIObject(API.VAULT)
  csvPF = CSVPrintFile(PRINT_VAULT_HOLDS_TITLES, 'sortall') if Act.csvFormat() else None
  FJQC = FormatJSONQuoteChar()
  matters = []
  cd = None
  fieldsList = []
  oneItemPerRow = False
  while Cmd.ArgumentsRemaining():
    myarg = getArgument()
    if csvPF and myarg == 'todrive':
      csvPF.GetTodriveParameters()
    elif myarg in {'matter', 'matters'}:
      matters = shlexSplitList(getString(Cmd.OB_MATTER_ITEM_LIST))
    elif myarg == 'shownames':
      cd = buildGAPIObject(API.DIRECTORY)
    elif getFieldsList(myarg, VAULT_HOLD_FIELDS_CHOICE_MAP, fieldsList, initialField=['holdId', 'name']):
      pass
    elif csvPF and myarg == 'oneitemperrow':
      oneItemPerRow = True
    else:
      FJQC.GetFormatJSONQuoteChar(myarg, False)
  fields = getItemFieldsFromFieldsList('holds', fieldsList)
  if csvPF and FJQC.formatJSON:
    csvPF.SetJSONTitles(PRINT_VAULT_HOLDS_TITLES+['JSON'])
  if not matters:
    printGettingAllAccountEntities(Ent.VAULT_MATTER, qualifier=' (OPEN)')
    try:
      results = callGAPIpages(v.matters(), 'list', 'matters',
                              pageMessage=getPageMessage(),
                              throwReasons=[GAPI.FORBIDDEN, GAPI.PERMISSION_DENIED, GAPI.INVALID_ARGUMENT],
                              view='BASIC', state='OPEN', fields='matters(matterId,name,state),nextPageToken')
    except (GAPI.forbidden, GAPI.permissionDenied, GAPI.invalidArgument) as e:
      entityActionFailedWarning([Ent.VAULT_HOLD, None], str(e))
      return
  else:
    results = []
    for matter in matters:
      matterId, matterName, _, state = convertMatterNameToID(v, matter)
      results.append({'matterId': matterId, 'name': matterName, 'state': state})
  jcount = len(results)
  if not csvPF:
    if jcount == 0:
      setSysExitRC(NO_ENTITIES_FOUND_RC)
  j = 0
  for matter in results:
    j += 1
    matterId = matter['matterId']
    matterName = matter['name']
    matterNameId = formatVaultNameId(matterName, matterId)
    if csvPF:
      printGettingAllEntityItemsForWhom(Ent.VAULT_HOLD, f'{Ent.Singular(Ent.VAULT_MATTER)}: {matterNameId}', j, jcount)
      pageMessage = getPageMessageForWhom()
    else:
      pageMessage = None
    if matter['state'] == 'OPEN':
      try:
        holds = callGAPIpages(v.matters().holds(), 'list', 'holds',
                              pageMessage=pageMessage,
                              throwReasons=[GAPI.FAILED_PRECONDITION, GAPI.FORBIDDEN, GAPI.PERMISSION_DENIED, GAPI.INVALID_ARGUMENT],
                              matterId=matterId, fields=fields)
      except GAPI.failedPrecondition:
        warnMatterNotOpen(v, matter, matterNameId, j, jcount)
        continue
      except (GAPI.forbidden, GAPI.permissionDenied, GAPI.invalidArgument) as e:
        entityActionFailedWarning([Ent.VAULT_HOLD, None], str(e))
        break
    else:
      warnMatterNotOpen(None, matter, matterNameId, j, jcount)
      continue
    if not csvPF:
      kcount = len(holds)
      if not FJQC.formatJSON:
        entityPerformActionNumItems([Ent.VAULT_MATTER, matterNameId], kcount, Ent.VAULT_HOLD, j, jcount)
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
  cd = buildGAPIObject(API.DIRECTORY)
  v = buildGAPIObject(API.VAULT)
  csvPF = CSVPrintFile(PRINT_USER_VAULT_HOLDS_TITLES, 'sortall') if Act.csvFormat() else None
  while Cmd.ArgumentsRemaining():
    myarg = getArgument()
    if csvPF and myarg == 'todrive':
      csvPF.GetTodriveParameters()
    else:
      unknownArgumentExit()
  printGettingAllAccountEntities(Ent.VAULT_MATTER, qualifier=' (OPEN)')
  try:
    matters = callGAPIpages(v.matters(), 'list', 'matters',
                            pageMessage=getPageMessage(),
                            throwReasons=[GAPI.FORBIDDEN, GAPI.PERMISSION_DENIED, GAPI.INVALID_ARGUMENT],
                            view='BASIC', state='OPEN', fields='matters(matterId,name,state),nextPageToken')
  except (GAPI.forbidden, GAPI.permissionDenied, GAPI.invalidArgument) as e:
    entityActionFailedWarning([Ent.VAULT_HOLD, None], str(e))
    return
  jcount = len(matters)
  j = 0
  for matter in matters:
    j += 1
    matterId = matter['matterId']
    matterName = matter['name']
    matterNameId = formatVaultNameId(matterName, matterId)
    printGettingAllEntityItemsForWhom(Ent.VAULT_HOLD, f'{Ent.Singular(Ent.VAULT_MATTER)}: {matterNameId}', j, jcount)
    try:
      matter['holds'] = callGAPIpages(v.matters().holds(), 'list', 'holds',
                                      pageMessage=getPageMessageForWhom(),
                                      throwReasons=[GAPI.FAILED_PRECONDITION, GAPI.FORBIDDEN, GAPI.PERMISSION_DENIED, GAPI.INVALID_ARGUMENT],
                                      matterId=matterId, fields='holds(holdId,name,accounts(accountId,email),orgUnit(orgUnitId)),nextPageToken')
    except GAPI.failedPrecondition:
      warnMatterNotOpen(v, matter, matterNameId, j, jcount)
    except (GAPI.forbidden, GAPI.permissionDenied, GAPI.invalidArgument) as e:
      entityActionFailedWarning([Ent.VAULT_HOLD, None], str(e), j, jcount)
  totalHolds = 0
  _, _, entityList = getEntityArgument(entityList)
  for user in entityList:
    user = normalizeEmailAddressOrUID(user)
    orgUnits = getAllParentOrgUnitsForUser(cd, user)
    for matter in matters:
      matterId = matter['matterId']
      matterName = matter['name']
      matterNameId = formatVaultNameId(matterName, matterId)
      for hold in matter.get('holds', []):
        if 'orgUnit' in hold:
          orgUnitId = hold['orgUnit'].get('orgUnitId')
          if orgUnitId in orgUnits:
            if not csvPF:
              printEntityMessage([Ent.USER, user,
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
                printEntityMessage([Ent.USER, user,
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
    printKeyValueList(['Total Holds', totalHolds])

def _cleanVaultQuery(query, cd, drive):
  if 'query' in query:
    if cd is not None and 'orgUnitInfo' in query['query']:
      query['query']['orgUnitInfo']['orgUnitPath'] = convertOrgUnitIDtoPath(cd, query['query']['orgUnitInfo']['orgUnitId'])
    if drive is not None and 'sharedDriveInfo' in query['query']:
      query['query']['sharedDriveInfo']['sharedDriveNames'] = []
      for sharedDriveId in query['query']['sharedDriveInfo']['sharedDriveIds']:
        query['query']['sharedDriveInfo']['sharedDriveNames'].append(_getSharedDriveNameFromId(drive, sharedDriveId, False))
    query['query'].pop('searchMethod', None)
    query['query'].pop('teamDriveInfo', None)

VAULT_QUERY_TIME_OBJECTS = {'createTime', 'endTime', 'startTime', 'versionDate'}

def _showVaultQuery(matterNameId, query, cd, drive, FJQC, k=0, kcount=0):
  _cleanVaultQuery(query, cd, drive)
  if FJQC is not None and FJQC.formatJSON:
    printLine(json.dumps(cleanJSON(query, timeObjects=VAULT_QUERY_TIME_OBJECTS), ensure_ascii=False, sort_keys=False))
    return
  printEntity([Ent.VAULT_MATTER, matterNameId, Ent.VAULT_QUERY, formatVaultNameId(query['displayName'], query['savedQueryId'])], k, kcount)
  Ind.Increment()
  showJSON(None, query, timeObjects=VAULT_QUERY_TIME_OBJECTS)
  Ind.Decrement()

def doCreateCopyVaultQuery(copyCmd):
  v = buildGAPIObject(API.VAULT)
  body = {'query': {'dataScope': 'ALL_DATA'}, 'displayName': ''}
  matterId, matterNameId = getMatterItem(v)
  if copyCmd:
    _, queryName, _, body['query'] = convertQueryNameToID(v, getString(Cmd.OB_QUERY_ITEM), matterId, matterNameId)
  targetId = None
  cd = drive = None
  FJQC = FormatJSONQuoteChar()
  returnIdOnly = showDetails = False
  while Cmd.ArgumentsRemaining():
    myarg = getArgument()
    if myarg == 'name':
      body['displayName'] = getString(Cmd.OB_STRING)
    elif copyCmd and myarg == 'targetmatter':
      targetId, targetNameId = getMatterItem(v)
    elif not copyCmd and myarg in VAULT_QUERY_ARGS:
      _buildVaultQuery(myarg, body['query'], VAULT_CORPUS_ARGUMENT_MAP)
    elif myarg == 'shownames':
      cd = buildGAPIObject(API.DIRECTORY)
      _, drive = buildGAPIServiceObject(API.DRIVE3, _getAdminEmail())
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
    result = callGAPI(v.matters().savedQueries(), 'create',
                      throwReasons=[GAPI.NOT_FOUND, GAPI.BAD_REQUEST, GAPI.FORBIDDEN, GAPI.PERMISSION_DENIED, GAPI.INVALID_ARGUMENT, GAPI.ALREADY_EXISTS],
                      matterId=resultId, body=body)
    if not returnIdOnly:
      if not FJQC.formatJSON:
        entityActionPerformed([Ent.VAULT_MATTER, matterNameId, Ent.VAULT_QUERY, formatVaultNameId(result['displayName'], result['savedQueryId'])])
      if showDetails or FJQC.formatJSON:
        _showVaultQuery(resultNameId, result, cd, drive, FJQC)
    else:
      writeStdout(f'{result["savedQueryId"]}\n')
  except (GAPI.notFound, GAPI.badRequest, GAPI.forbidden, GAPI.permissionDenied, GAPI.invalidArgument, GAPI.alreadyExists) as e:
    entityActionFailedWarning([Ent.VAULT_MATTER, resultNameId, Ent.VAULT_QUERY, body['displayName']], str(e))

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
  v = buildGAPIObject(API.VAULT)
  if not Cmd.ArgumentIsAhead('matter'):
    matterId, matterNameId = getMatterItem(v)
    queryId, queryName, queryNameId, _ = convertQueryNameToID(v, getString(Cmd.OB_QUERY_ITEM), matterId, matterNameId)
  else:
    queryName = getString(Cmd.OB_QUERY_ITEM)
  while Cmd.ArgumentsRemaining():
    myarg = getArgument()
    if myarg == 'matter':
      matterId, matterNameId = getMatterItem(v)
      queryId, queryName, queryNameId, _ = convertQueryNameToID(v, queryName, matterId, matterNameId)
    else:
      unknownArgumentExit()
  try:
    callGAPI(v.matters().savedQueries(), 'delete',
             throwReasons=[GAPI.NOT_FOUND, GAPI.BAD_REQUEST, GAPI.FORBIDDEN, GAPI.PERMISSION_DENIED, GAPI.INVALID_ARGUMENT],
             matterId=matterId, savedQueryId=queryId)
    entityActionPerformed([Ent.VAULT_MATTER, matterNameId, Ent.VAULT_QUERY, queryNameId])
  except (GAPI.notFound, GAPI.badRequest, GAPI.forbidden, GAPI.permissionDenied, GAPI.invalidArgument) as e:
    entityActionFailedWarning([Ent.VAULT_MATTER, matterNameId, Ent.VAULT_QUERY, queryNameId], str(e))

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
  v = buildGAPIObject(API.VAULT)
  if not Cmd.ArgumentIsAhead('matter'):
    matterId, matterNameId = getMatterItem(v)
    queryId, queryName, queryNameId, _ = convertQueryNameToID(v, getString(Cmd.OB_QUERY_ITEM), matterId, matterNameId)
  else:
    queryName = getString(Cmd.OB_QUERY_ITEM)
  cd = drive = None
  fieldsList = []
  FJQC = FormatJSONQuoteChar()
  while Cmd.ArgumentsRemaining():
    myarg = getArgument()
    if myarg == 'matter':
      matterId, matterNameId = getMatterItem(v)
      queryId, queryName, queryNameId, _ = convertQueryNameToID(v, queryName, matterId, matterNameId)
    elif myarg == 'shownames':
      cd = buildGAPIObject(API.DIRECTORY)
      _, drive = buildGAPIServiceObject(API.DRIVE3, _getAdminEmail())
      if drive is None:
        return
    elif getFieldsList(myarg, VAULT_QUERY_FIELDS_CHOICE_MAP, fieldsList, initialField=['savedQueryId', 'displayName']):
      pass
    else:
      FJQC.GetFormatJSON(myarg)
  fields = getFieldsFromFieldsList(fieldsList)
  try:
    query = callGAPI(v.matters().savedQueries(), 'get',
                    throwReasons=[GAPI.NOT_FOUND, GAPI.BAD_REQUEST, GAPI.FORBIDDEN, GAPI.PERMISSION_DENIED, GAPI.INVALID_ARGUMENT],
                    matterId=matterId, savedQueryId=queryId, fields=fields)
    _showVaultQuery(matterNameId, query, cd, drive, FJQC)
  except (GAPI.notFound, GAPI.badRequest, GAPI.forbidden, GAPI.permissionDenied, GAPI.invalidArgument) as e:
    entityActionFailedWarning([Ent.VAULT_MATTER, matterNameId, Ent.VAULT_QUERY, queryNameId], str(e))

PRINT_VAULT_QUERIES_TITLES = ['matterId', 'matterName', 'savedQueryId', 'displayName']

# gam print vaultqueries [todrive <ToDriveAttribute>*] [matters <MatterItemList>]
#	[fields <VaultQueryFieldNameList>] [shownames]
#	[formatjson [quotechar <Character>]]
# gam show vaultqueries [matters <MatterItemList>]
#	[fields <VaultQueryFieldNameList>] [shownames]
#	[formatjson]
def doPrintShowVaultQueries():
  v = buildGAPIObject(API.VAULT)
  csvPF = CSVPrintFile(PRINT_VAULT_QUERIES_TITLES, 'sortall') if Act.csvFormat() else None
  FJQC = FormatJSONQuoteChar(csvPF)
  matters = []
  cd = drive = None
  fieldsList = []
  while Cmd.ArgumentsRemaining():
    myarg = getArgument()
    if csvPF and myarg == 'todrive':
      csvPF.GetTodriveParameters()
    elif myarg in {'matter', 'matters'}:
      matters = shlexSplitList(getString(Cmd.OB_MATTER_ITEM_LIST))
    elif myarg == 'shownames':
      cd = buildGAPIObject(API.DIRECTORY)
      _, drive = buildGAPIServiceObject(API.DRIVE3, _getAdminEmail())
      if drive is None:
        return
    elif getFieldsList(myarg, VAULT_QUERY_FIELDS_CHOICE_MAP, fieldsList, initialField=['savedQueryId', 'displayName']):
      pass
    else:
      FJQC.GetFormatJSONQuoteChar(myarg, False)
  fields = getItemFieldsFromFieldsList('savedQueries', fieldsList)
  if csvPF and FJQC.formatJSON:
    csvPF.SetJSONTitles(PRINT_VAULT_QUERIES_TITLES+['JSON'])
  if not matters:
    printGettingAllAccountEntities(Ent.VAULT_MATTER, qualifier=' (OPEN)')
    try:
      results = callGAPIpages(v.matters(), 'list', 'matters',
                              pageMessage=getPageMessage(),
                              throwReasons=[GAPI.FORBIDDEN, GAPI.PERMISSION_DENIED, GAPI.INVALID_ARGUMENT],
                              view='BASIC', state='OPEN', fields='matters(matterId,name,state),nextPageToken')
    except (GAPI.forbidden, GAPI.permissionDenied, GAPI.invalidArgument) as e:
      entityActionFailedWarning([Ent.VAULT_QUERY, None], str(e))
      return
  else:
    results = []
    for matter in matters:
      matterId, matterName, _, state = convertMatterNameToID(v, matter)
      results.append({'matterId': matterId, 'name': matterName, 'state': state})
  jcount = len(results)
  if not csvPF:
    if jcount == 0:
      setSysExitRC(NO_ENTITIES_FOUND_RC)
  j = 0
  for matter in results:
    j += 1
    matterId = matter['matterId']
    matterName = matter['name']
    matterNameId = formatVaultNameId(matterName, matterId)
    if csvPF:
      printGettingAllEntityItemsForWhom(Ent.VAULT_QUERY, f'{Ent.Singular(Ent.VAULT_MATTER)}: {matterNameId}', j, jcount)
      pageMessage = getPageMessageForWhom()
    else:
      pageMessage = None
    if matter['state'] == 'OPEN':
      try:
        queries = callGAPIpages(v.matters().savedQueries(), 'list', 'savedQueries',
                                pageMessage=pageMessage,
                                throwReasons=[GAPI.FAILED_PRECONDITION, GAPI.FORBIDDEN, GAPI.PERMISSION_DENIED, GAPI.INVALID_ARGUMENT],
                                matterId=matterId, fields=fields)
      except GAPI.failedPrecondition:
        warnMatterNotOpen(v, matter, matterNameId, j, jcount)
        continue
      except (GAPI.forbidden, GAPI.permissionDenied, GAPI.invalidArgument) as e:
        entityActionFailedWarning([Ent.VAULT_QUERY, None], str(e))
        break
    else:
      warnMatterNotOpen(None, matter, matterNameId, j, jcount)
      continue
    if not csvPF:
      kcount = len(queries)
      if not FJQC.formatJSON:
        entityPerformActionNumItems([Ent.VAULT_MATTER, matterNameId], kcount, Ent.VAULT_QUERY, j, jcount)
      Ind.Increment()
      k = 0
      for query in queries:
        k += 1
        _showVaultQuery(matterNameId, query, cd, drive, FJQC, k, kcount)
      Ind.Decrement()
    else:
      for query in queries:
        _cleanVaultQuery(query, cd, drive)
        row = flattenJSON(query, flattened={'matterId': matterId, 'matterName': matterName}, timeObjects=VAULT_QUERY_TIME_OBJECTS)
        if not FJQC.formatJSON:
          csvPF.WriteRowTitles(row)
        elif csvPF.CheckRowTitles(row):
          csvPF.WriteRowNoFilter({'matterId': matterId, 'matterName': matterName,
                                  'savedQueryId': query['savedQueryId'], 'displayName': query['displayName'],
                                  'JSON': json.dumps(cleanJSON(query, timeObjects=VAULT_QUERY_TIME_OBJECTS), ensure_ascii=False, sort_keys=True)})
  if csvPF:
    csvPF.writeCSVfile('Vault Saved Queries')

def validateCollaborators(cd):
  collaborators = []
  for collaborator in getEntityList(Cmd.OB_COLLABORATOR_ENTITY):
    collaborators.append({'email': collaborator, 'id': convertEmailAddressToUID(collaborator, cd)})
  return collaborators

def _cleanVaultMatter(matter, cd):
  if cd is not None:
    if 'matterPermissions' in matter:
      for i in range(0, len(matter['matterPermissions'])):
        matter['matterPermissions'][i]['email'] = convertUserIDtoEmail(matter["matterPermissions"][i]["accountId"], cd)

def _showVaultMatter(matter, cd, FJQC, j=0, jcount=0):
  _cleanVaultMatter(matter, cd)
  if FJQC is not None and FJQC.formatJSON:
    printLine(json.dumps(cleanJSON(matter), ensure_ascii=False, sort_keys=False))
    return
  printEntity([Ent.VAULT_MATTER, formatVaultNameId(matter['name'], matter['matterId'])], j, jcount)
  Ind.Increment()
  showJSON(None, matter)
  Ind.Decrement()

# gam create vaultmatter|matter [name <String>] [description <string>]
#	[collaborator|collaborators <CollaboratorItemList>] [sendemails <Boolean>] [ccme <Boolean>]
#	[showdetails|returnidonly]
def doCreateVaultMatter():
  v = buildGAPIObject(API.VAULT)
  body = {}
  cbody = {'matterPermission': {'role': 'COLLABORATOR', 'accountId': ''}, 'sendEmails': False, 'ccMe': False}
  collaborators = []
  cd = None
  returnIdOnly = showDetails = False
  while Cmd.ArgumentsRemaining():
    myarg = getArgument()
    if myarg == 'name':
      body['name'] = getString(Cmd.OB_STRING)
    elif myarg == 'description':
      body['description'] = getString(Cmd.OB_STRING, minLen=0)
    elif myarg in {'collaborator', 'collaborators'}:
      if not cd:
        cd = buildGAPIObject(API.DIRECTORY)
      collaborators.extend(validateCollaborators(cd))
    elif myarg == 'sendemails':
      cbody['sendEmails'] = getBoolean()
    elif myarg == 'ccme':
      cbody['ccMe'] = getBoolean()
    elif myarg == 'showdetails':
      showDetails = True
      returnIdOnly = False
    elif myarg == 'returnidonly':
      returnIdOnly = True
      showDetails = False
    else:
      unknownArgumentExit()
  if 'name' not in body:
    body['name'] = f'GAM Matter - {ISOformatTimeStamp(todaysTime())}'
  try:
    matter = callGAPI(v.matters(), 'create',
                      throwReasons=[GAPI.ALREADY_EXISTS, GAPI.FORBIDDEN, GAPI.PERMISSION_DENIED, GAPI.INVALID_ARGUMENT],
                      body=body)
    matterId = matter['matterId']
    matterNameId = formatVaultNameId(matter['name'], matterId)
    if not returnIdOnly:
      entityActionPerformed([Ent.VAULT_MATTER, matterNameId])
    else:
      writeStdout(f'{matterId}\n')
  except (GAPI.alreadyExists, GAPI.forbidden, GAPI.permissionDenied, GAPI.invalidArgument) as e:
    entityActionFailedWarning([Ent.VAULT_MATTER, body['name']], str(e))
    return
  jcount = len(collaborators)
  if jcount > 0:
    Act.Set(Act.ADD)
    if not returnIdOnly:
      entityPerformActionNumItems([Ent.VAULT_MATTER, matterNameId], jcount, Ent.COLLABORATOR)
    Ind.Increment()
    j = 0
    for collaborator in collaborators:
      j += 1
      cbody['matterPermission']['accountId'] = collaborator['id']
      try:
        callGAPI(v.matters(), 'addPermissions',
                 throwReasons=[GAPI.FAILED_PRECONDITION, GAPI.FORBIDDEN, GAPI.PERMISSION_DENIED, GAPI.INVALID_ARGUMENT],
                 matterId=matterId, body=cbody)
        if not returnIdOnly:
          entityActionPerformed([Ent.VAULT_MATTER, matterNameId, Ent.COLLABORATOR, collaborator['email']], j, jcount)
      except (GAPI.failedPrecondition, GAPI.forbidden, GAPI.permissionDenied, GAPI.invalidArgument) as e:
        entityActionFailedWarning([Ent.VAULT_MATTER, matterNameId], str(e))
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
    v = buildGAPIObject(API.VAULT)
    matterId, matterNameId = getMatterItem(v)
  else:
    Act.Set(VAULT_MATTER_ACTIONS[action])
  checkForExtraneousArguments()
  action_kwargs = {} if action == 'delete' else {'body': {}}
  try:
    callGAPI(v.matters(), action,
             throwReasons=[GAPI.NOT_FOUND, GAPI.FAILED_PRECONDITION, GAPI.FORBIDDEN, GAPI.PERMISSION_DENIED, GAPI.INVALID_ARGUMENT],
             matterId=matterId, **action_kwargs)
    entityActionPerformed([Ent.VAULT_MATTER, matterNameId])
  except (GAPI.notFound, GAPI.failedPrecondition, GAPI.forbidden, GAPI.permissionDenied, GAPI.invalidArgument) as e:
    entityActionFailedWarning([Ent.VAULT_MATTER, matterNameId], str(e))

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
  v = buildGAPIObject(API.VAULT)
  matterId, matterNameId = getMatterItem(v)
  body = {}
  addCollaborators = []
  removeCollaborators = []
  cd = None
  while Cmd.ArgumentsRemaining():
    myarg = getArgument()
    if myarg == 'action':
      action = getChoice(VAULT_MATTER_ACTIONS)
      doActionVaultMatter(action, matterId, matterNameId, v)
      return
    if myarg == 'name':
      body['name'] = getString(Cmd.OB_STRING)
    elif myarg == 'description':
      body['description'] = getString(Cmd.OB_STRING, minLen=0)
    elif myarg in {'addcollaborator', 'addcollaborators'}:
      if not cd:
        cd = buildGAPIObject(API.DIRECTORY)
      addCollaborators.extend(validateCollaborators(cd))
    elif myarg in {'removecollaborator', 'removecollaborators'}:
      if not cd:
        cd = buildGAPIObject(API.DIRECTORY)
      removeCollaborators.extend(validateCollaborators(cd))
    else:
      unknownArgumentExit()
  if body:
    try:
      if 'name' not in body or 'description' not in body:
        # bah, API requires name/description to be sent on update even when it's not changing
        result = callGAPI(v.matters(), 'get',
                          throwReasons=[GAPI.NOT_FOUND, GAPI.FORBIDDEN, GAPI.PERMISSION_DENIED, GAPI.INVALID_ARGUMENT],
                          matterId=matterId, view='BASIC')
        body.setdefault('name', result['name'])
        body.setdefault('description', result.get('description'))
      callGAPI(v.matters(), 'update',
               throwReasons=[GAPI.NOT_FOUND, GAPI.FAILED_PRECONDITION, GAPI.FORBIDDEN],
               matterId=matterId, body=body)
      entityActionPerformed([Ent.VAULT_MATTER, matterNameId])
    except (GAPI.notFound, GAPI.failedPrecondition, GAPI.forbidden, GAPI.permissionDenied, GAPI.invalidArgument) as e:
      entityActionFailedWarning([Ent.VAULT_MATTER, matterNameId], str(e))
      return
  jcount = len(addCollaborators)
  if jcount > 0:
    Act.Set(Act.ADD)
    entityPerformActionNumItems([Ent.VAULT_MATTER, matterNameId], jcount, Ent.COLLABORATOR)
    Ind.Increment()
    j = 0
    for collaborator in addCollaborators:
      j += 1
      try:
        callGAPI(v.matters(), 'addPermissions',
                 throwReasons=[GAPI.FAILED_PRECONDITION, GAPI.FORBIDDEN, GAPI.PERMISSION_DENIED, GAPI.INVALID_ARGUMENT],
                 matterId=matterId, body={'matterPermission': {'role': 'COLLABORATOR', 'accountId': collaborator['id']}})
        entityActionPerformed([Ent.VAULT_MATTER, matterNameId, Ent.COLLABORATOR, collaborator['email']], j, jcount)
      except (GAPI.failedPrecondition, GAPI.forbidden, GAPI.permissionDenied, GAPI.invalidArgument) as e:
        entityActionFailedWarning([Ent.VAULT_MATTER, matterNameId], str(e))
        break
    Ind.Decrement()
  jcount = len(removeCollaborators)
  if jcount > 0:
    Act.Set(Act.REMOVE)
    entityPerformActionNumItems([Ent.VAULT_MATTER, matterNameId], jcount, Ent.COLLABORATOR)
    Ind.Increment()
    j = 0
    for collaborator in removeCollaborators:
      j += 1
      try:
        callGAPI(v.matters(), 'removePermissions',
                 throwReasons=[GAPI.FAILED_PRECONDITION, GAPI.FORBIDDEN, GAPI.PERMISSION_DENIED, GAPI.INVALID_ARGUMENT],
                 matterId=matterId, body={'accountId': collaborator['id']})
        entityActionPerformed([Ent.VAULT_MATTER, matterNameId, Ent.COLLABORATOR, collaborator['email']], j, jcount)
      except (GAPI.failedPrecondition, GAPI.forbidden, GAPI.permissionDenied, GAPI.invalidArgument) as e:
        entityActionFailedWarning([Ent.VAULT_MATTER, matterNameId], str(e))
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
  v = buildGAPIObject(API.VAULT)
  matterId, matterNameId = getMatterItem(v)
  view = 'FULL'
  fieldsList = []
  FJQC = FormatJSONQuoteChar()
  while Cmd.ArgumentsRemaining():
    myarg = getArgument()
    if myarg in PROJECTION_CHOICE_MAP:
      view = PROJECTION_CHOICE_MAP[myarg]
    elif getFieldsList(myarg, VAULT_MATTER_FIELDS_CHOICE_MAP, fieldsList, initialField=['matterId', 'name']):
      pass
    else:
      FJQC.GetFormatJSON(myarg)
  fields = getFieldsFromFieldsList(fieldsList)
  try:
    matter = callGAPI(v.matters(), 'get',
                      throwReasons=[GAPI.NOT_FOUND, GAPI.FORBIDDEN, GAPI.PERMISSION_DENIED, GAPI.INVALID_ARGUMENT],
                      matterId=matterId, view=view, fields=fields)
    cd = buildGAPIObject(API.DIRECTORY) if 'matterPermissions' in matter else None
    _showVaultMatter(matter, cd, FJQC)
  except (GAPI.notFound, GAPI.forbidden, GAPI.permissionDenied, GAPI.invalidArgument) as e:
    entityActionFailedWarning([Ent.VAULT_MATTER, matterNameId], str(e))

VAULT_MATTER_STATE_MAP = {'open': 'OPEN', 'closed': 'CLOSED', 'deleted': 'DELETED'}
PRINT_VAULT_MATTERS_TITLES = ['matterId', 'name', 'description', 'state']

# gam print vaultmatters|matters [todrive <ToDriveAttribute>*] [matterstate <MatterStateList>]
#	[basic|full|(fields <VaultMatterFieldNameList>)]
#	[formatjson [quotechar <Character>]]
# gam show vaultmatters|matters [matterstate <MatterStateList>]
#	[basic|full|(fields <VaultMatterFieldNameList>)]
#	[formatjson]
def doPrintShowVaultMatters():
  v = buildGAPIObject(API.VAULT)
  csvPF = CSVPrintFile(PRINT_VAULT_MATTERS_TITLES, 'sortall') if Act.csvFormat() else None
  FJQC = FormatJSONQuoteChar(csvPF)
  cd = None
  view = 'FULL'
  fieldsList = []
  matterStatesList = []
  while Cmd.ArgumentsRemaining():
    myarg = getArgument()
    if csvPF and myarg == 'todrive':
      csvPF.GetTodriveParameters()
    elif myarg == 'matterstate':
      for state in getString(Cmd.OB_STATE_NAME_LIST).lower().replace('_', '').replace(',', ' ').split():
        if state in VAULT_MATTER_STATE_MAP:
          matterStatesList.append(VAULT_MATTER_STATE_MAP[state])
        else:
          invalidChoiceExit(state, list(VAULT_MATTER_STATE_MAP), True)
    elif myarg in PROJECTION_CHOICE_MAP:
      view = PROJECTION_CHOICE_MAP[myarg]
    elif getFieldsList(myarg, VAULT_MATTER_FIELDS_CHOICE_MAP, fieldsList, initialField=['matterId', 'name']):
      pass
    else:
      FJQC.GetFormatJSONQuoteChar(myarg, False)
  if fieldsList and matterStatesList:
    fieldsList.append('state')
  fields = f'nextPageToken,matters({getFieldsFromFieldsList(fieldsList)})' if fieldsList else None
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
  printGettingAllAccountEntities(Ent.VAULT_MATTER, qualifier=qualifier)
  try:
    matters = callGAPIpages(v.matters(), 'list', 'matters',
                            pageMessage=getPageMessage(),
                            throwReasons=[GAPI.FORBIDDEN, GAPI.PERMISSION_DENIED, GAPI.INVALID_ARGUMENT, GAPI.INVALID_ARGUMENT],
                            view=view, state=stateParm, fields=fields)
  except (GAPI.forbidden, GAPI.permissionDenied, GAPI.invalidArgument, GAPI.invalidArgument) as e:
    entityActionFailedWarning([Ent.VAULT_MATTER, None], str(e))
    return
  jcount = len(matters)
  if view == 'FULL':
    cd = buildGAPIObject(API.DIRECTORY)
  if not csvPF:
    if jcount == 0:
      setSysExitRC(NO_ENTITIES_FOUND_RC)
    if not FJQC.formatJSON:
      performActionNumItems(jcount, Ent.VAULT_MATTER)
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
        row = flattenJSON(matter)
        if not FJQC.formatJSON:
          csvPF.WriteRowTitles(row)
        elif csvPF.CheckRowTitles(row):
          csvPF.WriteRowNoFilter({'matterId': matter['matterId'], 'name': matter['name'],
                                  'JSON': json.dumps(cleanJSON(matter), ensure_ascii=False, sort_keys=True)})
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
  v = buildGAPIObject(API.VAULT)
  csvPF = CSVPrintFile(PRINT_VAULT_COUNTS_TITLES, 'sortall')
  includeSuspendedZeros = False
  matterId = name = None
  operationWait = 15
  body = {'view': 'ALL', 'query': {}}
  while Cmd.ArgumentsRemaining():
    myarg = getArgument()
    if csvPF and myarg == 'todrive':
      csvPF.GetTodriveParameters()
    elif myarg == 'matter':
      matterId, matterNameId = getMatterItem(v)
    elif matterId is not None and myarg == 'vaultquery':
      _, _, _, body['query'] = convertQueryNameToID(v, getString(Cmd.OB_QUERY_ITEM), matterId, matterNameId)
    elif myarg == 'operation':
      name = getString(Cmd.OB_STRING)
    elif myarg in VAULT_QUERY_ARGS:
      _buildVaultQuery(myarg, body['query'], VAULT_COUNTS_CORPUS_ARGUMENT_MAP)
    elif myarg == 'wait':
      operationWait = getInteger(minVal=1)
    elif myarg == "includesuspendedzeros":
      includeSuspendedZeros = getBoolean()
    else:
      unknownArgumentExit()
  if not matterId:
    missingArgumentExit('matter')
  if name:
    operation = {'name': name}
    doWait = False
  else:
    _validateVaultQuery(body, VAULT_COUNTS_CORPUS_ARGUMENT_MAP)
    try:
      operation = callGAPI(v.matters(), 'count',
                           throwReasons=[GAPI.INVALID_ARGUMENT],
                           matterId=matterId, body=body)
    except GAPI.invalidArgument as e:
      entityActionFailedExit([Ent.VAULT_MATTER, matterId], str(e))
    doWait = True
  printGettingAllAccountEntities(Ent.VAULT_MATTER_ARTIFACT, qualifier=f' for {Ent.Singular(Ent.VAULT_OPERATION)}: {operation["name"]}',
                                 accountType=Ent.VAULT_MATTER)
  while not operation.get('done'):
    if doWait:
      stderrEntityMessage([Ent.VAULT_OPERATION, operation['name']], Msg.IS_NOT_DONE_CHECKING_IN_SECONDS.format(operationWait))
      time.sleep(operationWait)
    try:
      operation = callGAPI(v.operations(), 'get',
                           throwReasons=[GAPI.NOT_FOUND],
                           name=operation['name'])
    except GAPI.notFound as e:
      entityActionFailedExit([Ent.VAULT_OPERATION, operation['name']], str(e))
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
    query_accounts = getItemsToModify(Cmd.ENTITY_ALL_USERS if not includeSuspendedZeros else Cmd.ENTITY_ALL_USERS_NS_SUSP,
                                      '')
  elif search_method == 'ORG_UNIT':
    query_accounts = getItemsToModify(Cmd.ENTITY_OU if not includeSuspendedZeros else Cmd.ENTITY_OU_NS_SUSP,
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
