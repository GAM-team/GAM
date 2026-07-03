"""OAuth token management and user deprovisioning.

Part of the _userop_tmp sub-package."""

"""GAM user operations: Looker Studio, user groups, licenses, photos, profile, sheets, tokens, deprovision."""

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

def deleteTokens(users):
  cd = _getMain().buildGAPIObject(API.DIRECTORY)
  _getMain().checkArgumentPresent('clientid', required=True)
  clientId = commonClientIds(_getMain().getString(Cmd.OB_CLIENT_ID))
  _getMain().checkForExtraneousArguments()
  i, count, users = _getMain().getEntityArgument(users)
  for user in users:
    i += 1
    user = _getMain().normalizeEmailAddressOrUID(user)
    try:
      _getMain().callGAPI(cd.tokens(), 'get',
               throwReasons=[GAPI.USER_NOT_FOUND, GAPI.DOMAIN_NOT_FOUND,
                             GAPI.DOMAIN_CANNOT_USE_APIS,
                             GAPI.NOT_FOUND, GAPI.RESOURCE_NOT_FOUND,
                             GAPI.FORBIDDEN, GAPI.PERMISSION_DENIED],
               userKey=user, clientId=clientId, fields='')
      _getMain().callGAPI(cd.tokens(), 'delete',
               throwReasons=[GAPI.USER_NOT_FOUND, GAPI.DOMAIN_NOT_FOUND,
                             GAPI.DOMAIN_CANNOT_USE_APIS,
                             GAPI.NOT_FOUND, GAPI.RESOURCE_NOT_FOUND,
                             GAPI.FORBIDDEN, GAPI.PERMISSION_DENIED],
               userKey=user, clientId=clientId)
      _getMain().entityActionPerformed([Ent.USER, user, Ent.ACCESS_TOKEN, clientId], i, count)
    except (GAPI.notFound, GAPI.resourceNotFound) as e:
      _getMain().entityActionFailedWarning([Ent.USER, user, Ent.ACCESS_TOKEN, clientId], str(e), i, count)
    except (GAPI.userNotFound, GAPI.domainNotFound, GAPI.domainCannotUseApis):
      _getMain().entityUnknownWarning(Ent.USER, user, i, count)
    except (GAPI.forbidden, GAPI.permissionDenied) as e:
      _getMain().ClientAPIAccessDeniedExit(str(e))

TOKENS_FIELDS_TITLES = ['clientId', 'displayText', 'anonymous', 'nativeApp', 'userKey', 'scopes']
TOKENS_AGGREGATE_FIELDS_TITLES = ['clientId', 'displayText', 'anonymous', 'nativeApp', 'users', 'scopes']
TOKENS_AGGREGATE_ORDERBY_CHOICE_MAP = {
  'clientid': 'clientId',
  'id': 'clientId',
  'displaytext': 'displayText',
  'appname': 'displayText',
  }
TOKENS_TITLE_MAP = {
  'clientId': 'Client ID',
  'displayText': 'App Name',
  'user': 'user',
  }

def _printShowTokens(entityType, users):
  def _printToken(token):
    row = {}
    for item in token:
      if item != 'scopes':
        row[item] = token.get(item, '')
      else:
        row[item] = delimiter.join(token.get('scopes', []))
    csvPF.WriteRow(row)

  def _showToken(token, keyTitle, keyField, j, jcount):
    _getMain().printKeyValueListWithCount([keyTitle, token[keyField]], j, jcount)
    Ind.Increment()
    for item in sorted(token):
      if item not in {keyField, 'scopes'}:
        _getMain().printKeyValueList([item, token.get(item, '')])
    item = 'scopes'
    _getMain().printKeyValueList([item, None])
    Ind.Increment()
    for it in sorted(token.get(item, [])):
      _getMain().printKeyValueList([it])
    Ind.Decrement()
    Ind.Decrement()

  def project_from_client_id(client_id):
    match = re.search(r'^\d+', client_id)
    return match.group()

  def get_gcp_info(results):
    for result in results:
      result['project'] = project_from_client_id(result.get('clientId'))
      if result['project'] in internal_projects:
        result['internal'] = True
        continue
      try:
        results = _getMain().callGAPI(crm1.projects(), 'getAncestry',
                           throwReasons=[GAPI.PERMISSION_DENIED],
                           projectId=result['project'])
        for ancestor in results.get('ancestor', []):
          if ancestor.get('resourceId', {}).get('type') == 'organization' and ancestor.get('resourceId', {}).get('id') == GC.Values[GC.GCP_ORG_ID]:
            result['internal'] = True
            internal_projects.add(result['project'])
      except GAPI.permissionDenied:
        # we don't have permission to get project. This might be an external project
        # or it might be an internal project we don't have rights to get.
        pass

  cd = _getMain().buildGAPIObject(API.DIRECTORY)
  csvPF = _getMain().CSVPrintFile() if Act.csvFormat() else None
  clientId = None
  aggregateUsersBy = ''
  orderBy = 'clientId'
  delimiter = GC.Values[GC.CSV_OUTPUT_FIELD_DELIMITER]
  aggregateTokensById = {}
  tokenNameIdMap = None
  getGCPDetails = False
  extra_titles = []
  while Cmd.ArgumentsRemaining():
    myarg = _getMain().getArgument()
    if csvPF and myarg == 'todrive':
      csvPF.GetTodriveParameters()
    elif myarg == 'clientid':
      clientId = commonClientIds(_getMain().getString(Cmd.OB_CLIENT_ID))
    elif myarg == 'orderby':
      orderBy = _getMain().getChoice(TOKENS_AGGREGATE_ORDERBY_CHOICE_MAP, mapChoice=True)
    elif myarg == 'aggregateusersby':
      aggregateUsersBy = _getMain().getChoice(TOKENS_AGGREGATE_ORDERBY_CHOICE_MAP, mapChoice=True)
      if aggregateUsersBy == 'displayText':
        tokenNameIdMap = {}
    elif myarg == 'usertokencounts':
      aggregateUsersBy = 'user'
    elif myarg == 'delimiter':
      delimiter = _getMain().getCharacter()
    elif myarg == 'gcpdetails':
      getGCPDetails = True
      extra_titles = ['project', 'internal']
    elif not entityType:
      Cmd.Backup()
      entityType, users = _getMain().getEntityToModify(defaultEntityType=Cmd.ENTITY_USERS)
    else:
      _getMain().unknownArgumentExit()
  if not entityType:
    users = _getMain().getItemsToModify(Cmd.ENTITY_ALL_USERS_NS, None)
  if csvPF:
    if not aggregateUsersBy:
      csvPF.SetTitles(['user'] + TOKENS_FIELDS_TITLES + extra_titles)
    elif aggregateUsersBy != 'user':
      csvPF.SetTitles(TOKENS_AGGREGATE_FIELDS_TITLES + extra_titles)
    else:
      csvPF.SetTitles(['user', 'tokenCount'])
  else:
    if not aggregateUsersBy:
      tokenTitle = TOKENS_TITLE_MAP[orderBy]
    else:
      tokenTitle = TOKENS_TITLE_MAP[aggregateUsersBy]
  if getGCPDetails:
    internal_projects = set() # cache
    crm = _getMain().buildGAPIObject('cloudresourcemanager')
    crm1 = _getMain().buildGAPIObject('cloudresourcemanagerv1')
    admin_email = _getMain()._getAdminEmail()
    admin_domain = _getMain().getEmailAddressDomain(admin_email)
    GC.Values[GC.GCP_ORG_ID] = _getMain().getGCPOrgId(crm, admin_email, admin_domain).split('/')[1]
  fields = ','.join(TOKENS_FIELDS_TITLES)
  i, count, users = _getMain().getEntityArgument(users)
  for user in users:
    i += 1
    user = _getMain().normalizeEmailAddressOrUID(user)
    try:
      if csvPF or aggregateUsersBy:
        _getMain().printGettingEntityItemForWhom(Ent.ACCESS_TOKEN, user, i, count)
      if clientId:
        results = [_getMain().callGAPI(cd.tokens(), 'get',
                            throwReasons=[GAPI.USER_NOT_FOUND, GAPI.DOMAIN_NOT_FOUND,
                                          GAPI.DOMAIN_CANNOT_USE_APIS, GAPI.BAD_REQUEST,
                                          GAPI.NOT_FOUND, GAPI.RESOURCE_NOT_FOUND,
                                          GAPI.FORBIDDEN, GAPI.PERMISSION_DENIED],
                            userKey=user, clientId=clientId, fields=fields)]
      else:
        results = _getMain().callGAPIitems(cd.tokens(), 'list', 'items',
                                throwReasons=[GAPI.USER_NOT_FOUND, GAPI.DOMAIN_NOT_FOUND,
                                              GAPI.DOMAIN_CANNOT_USE_APIS, GAPI.BAD_REQUEST,
                                              GAPI.FORBIDDEN, GAPI.PERMISSION_DENIED],
                                userKey=user, fields=f'items({fields})')
      if getGCPDetails:
        get_gcp_info(results)
      if not aggregateUsersBy:
        if not csvPF:
          jcount = len(results)
          _getMain().entityPerformActionNumItems([Ent.USER, user], jcount, Ent.ACCESS_TOKEN, i, count)
          Ind.Increment()
          j = 0
          for token in sorted(results, key=lambda k: k[orderBy]):
            j += 1
            _showToken(token, tokenTitle, orderBy, j, jcount)
          Ind.Decrement()
        elif results:
          for token in sorted(results, key=lambda k: k[orderBy]):
            row = {'user': user, 'scopes': delimiter.join(token.get('scopes', []))}
            for item in token:
              if item != 'scopes':
                row[item] = token.get(item, '')
            csvPF.WriteRow(row)
        elif GC.Values[GC.CSV_OUTPUT_USERS_AUDIT]:
          csvPF.WriteRowNoFilter({'user': user})
      elif aggregateUsersBy != 'user':
        if results:
          for token in results:
            tokcid = token['clientId']
            if tokcid not in aggregateTokensById:
              token.pop('userKey', None)
              token['users'] = 0
              aggregateTokensById[tokcid] = token
            aggregateTokensById[tokcid]['users'] += 1
            if tokenNameIdMap is not None:
              tokname = token['displayText']
              if tokname not in tokenNameIdMap:
                tokenNameIdMap[tokname] = set()
              tokenNameIdMap[tokname].add(tokcid)
      else: # aggregateUsersBy == 'user':
        aggregateTokensById[user] = jcount
    except (GAPI.notFound, GAPI.resourceNotFound) as e:
      _getMain().entityActionFailedWarning([Ent.USER, user, Ent.ACCESS_TOKEN, clientId], str(e), i, count)
    except (GAPI.userNotFound, GAPI.domainNotFound, GAPI.domainCannotUseApis, GAPI.badRequest):
      _getMain().entityUnknownWarning(Ent.USER, user, i, count)
    except (GAPI.forbidden, GAPI.permissionDenied) as e:
      _getMain().ClientAPIAccessDeniedExit(str(e))
  if aggregateUsersBy == 'clientId':
    if not csvPF:
      jcount = len(aggregateTokensById)
      _getMain().performActionNumItems(jcount, Ent.ACCESS_TOKEN)
      Ind.Increment()
      j = 0
      for _, token in sorted(aggregateTokensById.items()):
        j += 1
        _showToken(token, tokenTitle, aggregateUsersBy, j, jcount)
      Ind.Decrement()
    else:
      for _, token in sorted(aggregateTokensById.items()):
        _printToken(token)
  elif aggregateUsersBy == 'displayText':
    if not csvPF:
      jcount = len(aggregateTokensById)
      _getMain().performActionNumItems(jcount, Ent.ACCESS_TOKEN)
      Ind.Increment()
      j = 0
      for _, tokenIds in sorted(tokenNameIdMap.items()):
        for tokcid in sorted(tokenIds):
          j += 1
          _showToken(aggregateTokensById[tokcid], tokenTitle, aggregateUsersBy, j, jcount)
      Ind.Decrement()
    else:
      for _, tokenIds in sorted(tokenNameIdMap.items()):
        for tokcid in sorted(tokenIds):
          _printToken(aggregateTokensById[tokcid])
  else: # aggregateUsersBy == 'user':
    if not csvPF:
      jcount = len(aggregateTokensById)
      j = 0
      for user, count in sorted(aggregateTokensById.items()):
        j += 1
        _getMain().printEntityKVList([Ent.USER, user], [Ent.Plural(Ent.ACCESS_TOKEN), count], j, jcount)
    else:
      for user, count in sorted(aggregateTokensById.items()):
        csvPF.WriteRow({'user': user, 'tokenCount': count})
  if csvPF:
    csvPF.writeCSVfile('OAuth Tokens')

# gam <UserTypeEntity> print tokens|token [todrive <ToDriveAttribute>*] [clientid <ClientID>]
#	[usertokencounts|(aggregateusersby|orderby clientid|id|appname|displaytext)] [delimiter <Character>]
# gam <UserTypeEntity> show tokens|token|3lo|oauth [clientid <ClientID>]
#	[usertokencounts|(aggregateusersby|orderby clientid|id|appname|displaytext)] [delimiter <Character>]
def printShowTokens(users):
  _printShowTokens(Cmd.ENTITY_USERS, users)

# gam print tokens|token [todrive <ToDriveAttribute>*] [clientid <ClientID>]
#	[usertokencounts|(aggregateusersby|orderby clientid|id|appname|displaytext)] [delimiter <Character>]
#	[<UserTypeEntity>]
# gam show tokens|token [clientid <ClientID>]
#	[usertokencounts|(aggregateusersby|orderby clientid|id|appname|displaytext)] [delimiter <Character>]
#	[<UserTypeEntity>]
def doPrintShowTokens():
  _printShowTokens(None, None)

# gam <UserTypeEntity> deprovision|deprov [popimap] [signout] [turnoff2sv]
def deprovisionUser(users):
  cd = _getMain().buildGAPIObject(API.DIRECTORY)
  disablePopImap = signout = turnoff2sv = False
  while Cmd.ArgumentsRemaining():
    myarg = _getMain().getArgument()
    if myarg == 'popimap':
      disablePopImap = True
    elif myarg == 'signout':
      signout = True
    elif myarg == 'turnoff2sv':
      turnoff2sv = True
    else:
      _getMain().unknownArgumentExit()
  if disablePopImap:
    imapBody = _getMain()._imapDefaults(False)
    popBody = _getMain()._popDefaults(False)
  i, count, users = _getMain().getEntityArgument(users)
  for user in users:
    i += 1
    user = _getMain().normalizeEmailAddressOrUID(user)
    userSuspended = _getMain().checkUserSuspended(cd, user, Ent.USER, i, count)
    if userSuspended is None:
      continue
    try:
      _getMain().printGettingEntityItemForWhom(Ent.APPLICATION_SPECIFIC_PASSWORD, user, i, count)
      asps = _getMain().callGAPIitems(cd.asps(), 'list', 'items',
                           throwReasons=[GAPI.USER_NOT_FOUND],
                           userKey=user, fields='items(codeId)')
      codeIds = [asp['codeId'] for asp in asps]
      jcount = len(codeIds)
      _getMain().entityPerformActionNumItems([Ent.USER, user], jcount, Ent.APPLICATION_SPECIFIC_PASSWORD, i, count)
      if jcount > 0:
        Ind.Increment()
        j = 0
        for codeId in codeIds:
          j += 1
          try:
            _getMain().callGAPI(cd.asps(), 'delete',
                     throwReasons=[GAPI.USER_NOT_FOUND, GAPI.INVALID, GAPI.INVALID_PARAMETER, GAPI.FORBIDDEN],
                     userKey=user, codeId=codeId)
            _getMain().entityActionPerformed([Ent.USER, user, Ent.APPLICATION_SPECIFIC_PASSWORD, codeId], j, jcount)
          except (GAPI.invalid, GAPI.invalidParameter, GAPI.forbidden) as e:
            _getMain().entityActionFailedWarning([Ent.USER, user, Ent.APPLICATION_SPECIFIC_PASSWORD, codeId], str(e), j, jcount)
        Ind.Decrement()
#
      _getMain().printGettingEntityItemForWhom(Ent.BACKUP_VERIFICATION_CODES, user, i, count)
      try:
        codes = _getMain().callGAPIitems(cd.verificationCodes(), 'list', 'items',
                              throwReasons=[GAPI.USER_NOT_FOUND],
                              userKey=user, fields='items(verificationCode)')
        jcount = len(codes)
        _getMain().entityPerformActionNumItems([Ent.USER, user], jcount, Ent.BACKUP_VERIFICATION_CODES, i, count)
        if jcount > 0:
          if not userSuspended:
            _getMain().callGAPI(cd.verificationCodes(), 'invalidate',
                     throwReasons=[GAPI.USER_NOT_FOUND, GAPI.INVALID, GAPI.INVALID_INPUT],
                     userKey=user)
            _getMain().entityActionPerformed([Ent.USER, user, Ent.BACKUP_VERIFICATION_CODES, None], i, count)
          else:
            _getMain().entityActionNotPerformedWarning([Ent.USER, user, Ent.BACKUP_VERIFICATION_CODES, None],
                                            Msg.IS_SUSPENDED_NO_BACKUPCODES, i, count)
      except (GAPI.invalid, GAPI.invalidInput) as e:
        _getMain().entityActionFailedWarning([Ent.USER, user, Ent.BACKUP_VERIFICATION_CODES, None], str(e), i, count)
#
      _getMain().printGettingEntityItemForWhom(Ent.ACCESS_TOKEN, user, i, count)
      tokens = _getMain().callGAPIitems(cd.tokens(), 'list', 'items',
                             throwReasons=[GAPI.USER_NOT_FOUND],
                             userKey=user, fields='items(clientId)')
      jcount = len(tokens)
      _getMain().entityPerformActionNumItems([Ent.USER, user], jcount, Ent.ACCESS_TOKEN, i, count)
      if jcount > 0:
        Ind.Increment()
        j = 0
        for token in tokens:
          j += 1
          clientId = token['clientId']
          try:
            _getMain().callGAPI(cd.tokens(), 'delete',
                     throwReasons=[GAPI.USER_NOT_FOUND, GAPI.NOT_FOUND],
                     userKey=user, clientId=clientId)
            _getMain().entityActionPerformed([Ent.USER, user, Ent.ACCESS_TOKEN, clientId], j, jcount)
          except GAPI.notFound as e:
            _getMain().entityActionFailedWarning([Ent.USER, user, Ent.ACCESS_TOKEN, clientId], str(e), j, jcount)
        Ind.Decrement()
#
      if turnoff2sv:
        Act.Set(Act.TURNOFF2SV)
        try:
          _getMain().callGAPI(cd.twoStepVerification(), 'turnOff',
                   throwReasons=[GAPI.USER_NOT_FOUND, GAPI.INVALID, GAPI.DOMAIN_NOT_FOUND,
                                 GAPI.DOMAIN_CANNOT_USE_APIS, GAPI.FORBIDDEN],
                   userKey=user)
          _getMain().entityActionPerformed([Ent.USER, user], i, count)
        except GAPI.invalid as e:
          _getMain().entityActionFailedWarning([Ent.USER, user], str(e), i, count)
#
      if signout:
        Act.Set(Act.SIGNOUT)
        _getMain().callGAPI(cd.users(), 'signOut',
                 throwReasons=[GAPI.USER_NOT_FOUND, GAPI.INVALID, GAPI.DOMAIN_NOT_FOUND,
                               GAPI.DOMAIN_CANNOT_USE_APIS, GAPI.FORBIDDEN],
                 userKey=user)
        _getMain().entityActionPerformed([Ent.USER, user], i, count)
#
      Act.Set(Act.DEPROVISION)
      if disablePopImap:
        _getMain()._setImap(user, imapBody, i, count)
        _getMain()._setPop(user, popBody, i, count)
#
      _getMain().entityActionPerformed([Ent.USER, user], i, count)
    except GAPI.userNotFound:
      _getMain().entityUnknownWarning(Ent.USER, user, i, count)
    except (GAPI.domainNotFound, GAPI.domainCannotUseApis, GAPI.forbidden) as e:
      _getMain().entityActionFailedWarning([Ent.USER, user], str(e), i, count)

# gam <UserTypeEntity> watch gmail [maxmessages <Integer>]
