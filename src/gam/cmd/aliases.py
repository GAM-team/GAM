"""GAM user and group alias management."""

import re
import time

from gamlib import glaction
from gamlib import glapi as API
from gamlib import glcfg as GC
from gamlib import glclargs
from gamlib import glentity
from gamlib import glgapi as GAPI
from gamlib import glglobals as GM
from gamlib import glindent
from gamlib import glmsgs as Msg
from gam.util.access import entityUnknownWarning
from gam.util.api import buildGAPIObject, callGAPI, callGAPIpages
from gam.util.args import (
    checkForExtraneousArguments,
    getAddCSVData,
    getArgument,
    getBoolean,
    getCharacter,
    getChoice,
    getEmailAddress,
    getInteger,
    getREPattern,
    getString,
    normalizeEmailAddressOrUID,
)
from gam.util.csv_pf import CSVPrintFile
from gam.util.display import (
    entityActionFailedWarning,
    entityActionNotPerformedWarning,
    entityActionPerformed,
    entityPerformActionNumItems,
    getPageMessage,
    invalidMember,
    invalidQuery,
    printEntity,
    printEntityKVList,
    printGettingAllAccountEntities,
    printGettingEntityItemForWhom,
)
from gam.util.entity import (
    _getDomainList,
    convertEntityToList,
    getEntityArgument,
    getEntityList,
    getEntityToModify,
    getQueries,
)
from gam.util.errors import entityActionFailedExit, unknownArgumentExit
from gam.util.orgunits import getOrgUnitItem
from gam.util.output import setSysExitRC
from gam.constants import ENTITY_IS_NOT_AN_ALIAS_RC, NO_ENTITIES_FOUND_RC

Act = glaction.GamAction()
Ent = glentity.GamEntity()
Ind = glindent.GamIndent()
Cmd = glclargs.GamCLArgs()


def doCreateUpdateAliases():
  from gam.cmd.ciuserinvitations import _getIsInvitableUser
  from gam.cmd.orgunits import ALIAS_TARGET_TYPES
  def verifyAliasTargetExists():
    if targetType != 'group':
      try:
        callGAPI(cd.users(), 'get',
                 throwReasons=GAPI.USER_GET_THROW_REASONS,
                 userKey=targetEmail, fields='primaryEmail')
        return 'user'
      except (GAPI.userNotFound, GAPI.domainNotFound, GAPI.domainCannotUseApis, GAPI.forbidden,
              GAPI.badRequest, GAPI.backendError, GAPI.systemError):
        if targetType == 'user':
          return None
    try:
      callGAPI(cd.groups(), 'get',
               throwReasons=GAPI.GROUP_GET_THROW_REASONS, retryReasons=GAPI.GROUP_GET_RETRY_REASONS,
               groupKey=targetEmail, fields='email')
      return 'group'
    except (GAPI.groupNotFound, GAPI.domainNotFound, GAPI.domainCannotUseApis, GAPI.forbidden,
            GAPI.badRequest, GAPI.invalid, GAPI.systemError):
      return None

  def deleteAliasOnUpdate():
# User alias
    if targetType != 'group':
      try:
        callGAPI(cd.users().aliases(), 'delete',
                 throwReasons=[GAPI.USER_NOT_FOUND, GAPI.BAD_REQUEST, GAPI.INVALID, GAPI.FORBIDDEN, GAPI.INVALID_RESOURCE,
                               GAPI.CONDITION_NOT_MET],
                 userKey=aliasEmail, alias=aliasEmail)
        printEntityKVList([Ent.USER_ALIAS, aliasEmail], [Act.PerformedName(Act.DELETE)], i, count)
        time.sleep(waitAfterDelete)
        return True
      except GAPI.conditionNotMet as e:
        entityActionFailedWarning([Ent.USER_ALIAS, aliasEmail], str(e), i, count)
        return False
      except (GAPI.userNotFound, GAPI.badRequest, GAPI.invalid, GAPI.forbidden, GAPI.invalidResource):
        if targetType == 'user':
          entityUnknownWarning(Ent.USER_ALIAS, aliasEmail, i, count)
          return False
# Group alias
    try:
      callGAPI(cd.groups().aliases(), 'delete',
               throwReasons=[GAPI.GROUP_NOT_FOUND, GAPI.BAD_REQUEST, GAPI.INVALID, GAPI.FORBIDDEN, GAPI.INVALID_RESOURCE,
                             GAPI.CONDITION_NOT_MET],
               groupKey=aliasEmail, alias=aliasEmail)
      time.sleep(waitAfterDelete)
      return True
    except GAPI.conditionNotMet as e:
      entityActionFailedWarning([Ent.GROUP_ALIAS, aliasEmail], str(e), i, count)
      return False
    except GAPI.forbidden:
      entityUnknownWarning(Ent.GROUP_ALIAS, aliasEmail, i, count)
      return False
    except (GAPI.groupNotFound, GAPI.badRequest, GAPI.invalid, GAPI.invalidResource):
      entityUnknownWarning(Ent.GROUP_ALIAS, aliasEmail, i, count)
      return False

  cd = buildGAPIObject(API.DIRECTORY)
  ci = None
  updateCmd = Act.Get() == Act.UPDATE
  aliasList = getEntityList(Cmd.OB_EMAIL_ADDRESS_ENTITY)
  targetType = getChoice(ALIAS_TARGET_TYPES)
  targetEmails = getEntityList(Cmd.OB_GROUP_ENTITY)
  entityLists = targetEmails if isinstance(targetEmails, dict) else None
  verifyNotInvitable = False
  verifyTarget = updateCmd
  waitAfterDelete = 2
  while Cmd.ArgumentsRemaining():
    myarg = getArgument()
    if (not updateCmd) and myarg == 'verifynotinvitable':
      verifyNotInvitable = True
    elif updateCmd and myarg == 'notargetverify':
      verifyTarget = False
    elif updateCmd and myarg == 'waitafterdelete':
      waitAfterDelete = getInteger(minVal=2, maxVal=10)
    else:
      unknownArgumentExit()
  i = 0
  count = len(aliasList)
  for aliasEmail in aliasList:
    i += 1
    if entityLists:
      targetEmails = entityLists[aliasEmail]
    aliasEmail = normalizeEmailAddressOrUID(aliasEmail, noUid=True, noLower=True)
    if verifyNotInvitable:
      isInvitableUser, ci = _getIsInvitableUser(ci, aliasEmail)
      if isInvitableUser:
        entityActionNotPerformedWarning([Ent.ALIAS_EMAIL, aliasEmail], Msg.EMAIL_ADDRESS_IS_UNMANAGED_ACCOUNT)
        continue
    body = {'alias': aliasEmail}
    jcount = len(targetEmails)
    if jcount > 0:
# Only process first target
      targetEmail = normalizeEmailAddressOrUID(targetEmails[0])
      if verifyTarget:
        targetType = verifyAliasTargetExists()
        if targetType is None:
          entityUnknownWarning(Ent.ALIAS_TARGET, targetEmail, i, count)
          continue
      if updateCmd and not deleteAliasOnUpdate():
        continue
# User alias
      if targetType != 'group':
        try:
          callGAPI(cd.users().aliases(), 'insert',
                   throwReasons=[GAPI.USER_NOT_FOUND, GAPI.BAD_REQUEST,
                                 GAPI.INVALID, GAPI.INVALID_INPUT, GAPI.FORBIDDEN, GAPI.DUPLICATE,
                                 GAPI.CONDITION_NOT_MET, GAPI.LIMIT_EXCEEDED],
                   userKey=targetEmail, body=body, fields='')
          entityActionPerformed([Ent.USER_ALIAS, aliasEmail, Ent.USER, targetEmail], i, count)
          continue
        except (GAPI.conditionNotMet, GAPI.limitExceeded) as e:
          entityActionFailedWarning([Ent.USER_ALIAS, aliasEmail, Ent.USER, targetEmail], str(e), i, count)
          continue
        except GAPI.duplicate:
          duplicateAliasGroupUserWarning(cd, [Ent.USER_ALIAS, aliasEmail, Ent.USER, targetEmail], i, count)
          continue
        except (GAPI.invalid, GAPI.invalidInput):
          entityActionFailedWarning([Ent.USER_ALIAS, aliasEmail, Ent.USER, targetEmail], Msg.INVALID_ALIAS, i, count)
          continue
        except (GAPI.userNotFound, GAPI.badRequest, GAPI.forbidden):
          if targetType == 'user':
            entityUnknownWarning(Ent.ALIAS_TARGET, targetEmail, i, count)
            continue
# Group alias
      try:
        callGAPI(cd.groups().aliases(), 'insert',
                 throwReasons=[GAPI.GROUP_NOT_FOUND, GAPI.USER_NOT_FOUND, GAPI.BAD_REQUEST,
                               GAPI.INVALID, GAPI.INVALID_INPUT, GAPI.FORBIDDEN, GAPI.DUPLICATE,
                               GAPI.CONDITION_NOT_MET, GAPI.LIMIT_EXCEEDED],
                 groupKey=targetEmail, body=body, fields='')
        entityActionPerformed([Ent.GROUP_ALIAS, aliasEmail, Ent.GROUP, targetEmail], i, count)
      except (GAPI.conditionNotMet, GAPI.limitExceeded) as e:
        entityActionFailedWarning([Ent.GROUP_ALIAS, aliasEmail, Ent.GROUP, targetEmail], str(e), i, count)
      except GAPI.duplicate:
        duplicateAliasGroupUserWarning(cd, [Ent.GROUP_ALIAS, aliasEmail, Ent.GROUP, targetEmail], i, count)
      except (GAPI.invalid, GAPI.invalidInput):
        entityActionFailedWarning([Ent.GROUP_ALIAS, aliasEmail, Ent.GROUP, targetEmail], Msg.INVALID_ALIAS, i, count)
      except (GAPI.groupNotFound, GAPI.userNotFound, GAPI.badRequest, GAPI.forbidden):
        entityUnknownWarning(Ent.ALIAS_TARGET, targetEmail, i, count)

# gam delete aliases|nicknames [user|group|target] <EmailAddressEntity>
def doDeleteAliases():
  from gam.cmd.orgunits import ALIAS_TARGET_TYPES
  cd = buildGAPIObject(API.DIRECTORY)
  targetType = getChoice(ALIAS_TARGET_TYPES, defaultChoice='target')
  entityList = getEntityList(Cmd.OB_EMAIL_ADDRESS_ENTITY)
  checkForExtraneousArguments()
  i = 0
  count = len(entityList)
  for aliasEmail in entityList:
    i += 1
    aliasEmail = normalizeEmailAddressOrUID(aliasEmail, noUid=True)
    aliasDeleted = False
    if targetType != 'group':
      try:
        result = callGAPI(cd.users().aliases(), 'list',
                          throwReasons=[GAPI.USER_NOT_FOUND, GAPI.BAD_REQUEST, GAPI.INVALID, GAPI.FORBIDDEN, GAPI.INVALID_RESOURCE,
                                        GAPI.CONDITION_NOT_MET],
                          userKey=aliasEmail, fields='aliases(alias)')
        for aliasEntry in result.get('aliases', []):
          if aliasEmail == aliasEntry['alias'].lower():
            aliasEmail = aliasEntry['alias']
            callGAPI(cd.users().aliases(), 'delete',
                     throwReasons=[GAPI.USER_NOT_FOUND, GAPI.BAD_REQUEST, GAPI.INVALID, GAPI.FORBIDDEN, GAPI.INVALID_RESOURCE,
                                   GAPI.CONDITION_NOT_MET],
                     userKey=aliasEmail, alias=aliasEmail)
            entityActionPerformed([Ent.USER_ALIAS, aliasEmail], i, count)
            aliasDeleted = True
            break
        if aliasDeleted:
          continue
      except GAPI.conditionNotMet as e:
        entityActionFailedWarning([Ent.USER_ALIAS, aliasEmail], str(e), i, count)
        continue
      except (GAPI.userNotFound, GAPI.badRequest, GAPI.invalid, GAPI.forbidden, GAPI.invalidResource):
        pass
      if targetType == 'user':
        entityUnknownWarning(Ent.USER_ALIAS, aliasEmail, i, count)
        continue
    try:
      result = callGAPI(cd.groups().aliases(), 'list',
                        throwReasons=[GAPI.GROUP_NOT_FOUND, GAPI.USER_NOT_FOUND, GAPI.BAD_REQUEST, GAPI.INVALID, GAPI.FORBIDDEN, GAPI.INVALID_RESOURCE,
                                      GAPI.CONDITION_NOT_MET],
                        groupKey=aliasEmail, fields='aliases(alias)')
      for aliasEntry in result.get('aliases', []):
        if aliasEmail == aliasEntry['alias'].lower():
          aliasEmail = aliasEntry['alias']
          callGAPI(cd.groups().aliases(), 'delete',
                   throwReasons=[GAPI.GROUP_NOT_FOUND, GAPI.USER_NOT_FOUND, GAPI.BAD_REQUEST, GAPI.INVALID, GAPI.FORBIDDEN, GAPI.INVALID_RESOURCE,
                                 GAPI.CONDITION_NOT_MET],
                   groupKey=aliasEmail, alias=aliasEmail)
          entityActionPerformed([Ent.GROUP_ALIAS, aliasEmail], i, count)
          aliasDeleted = True
          break
      if aliasDeleted:
        continue
    except GAPI.conditionNotMet as e:
      entityActionFailedWarning([Ent.GROUP_ALIAS, aliasEmail], str(e), i, count)
      continue
    except (GAPI.groupNotFound, GAPI.userNotFound, GAPI.badRequest, GAPI.invalid, GAPI.forbidden, GAPI.invalidResource):
      pass
    if targetType == 'group':
      entityUnknownWarning(Ent.GROUP_ALIAS, aliasEmail, i, count)
      continue
    entityUnknownWarning(Ent.ALIAS, aliasEmail, i, count)

# gam remove aliases|nicknames <EmailAddress> user|group <EmailAddressEntity>
def doRemoveAliases():
  cd = buildGAPIObject(API.DIRECTORY)
  targetEmail = getEmailAddress()
  targetType = getChoice(['user', 'group'])
  entityList = getEntityList(Cmd.OB_EMAIL_ADDRESS_ENTITY)
  checkForExtraneousArguments()
  count = len(entityList)
  i = 0
  if targetType == 'user':
    try:
      for aliasEmail in entityList:
        i += 1
        aliasEmail = normalizeEmailAddressOrUID(aliasEmail, noUid=True)
        callGAPI(cd.users().aliases(), 'delete',
                 throwReasons=[GAPI.USER_NOT_FOUND, GAPI.BAD_REQUEST, GAPI.INVALID, GAPI.FORBIDDEN, GAPI.INVALID_RESOURCE,
                               GAPI.CONDITION_NOT_MET],
                 userKey=targetEmail, alias=aliasEmail)
        entityActionPerformed([Ent.USER, targetEmail, Ent.USER_ALIAS, aliasEmail], i, count)
    except (GAPI.userNotFound, GAPI.badRequest, GAPI.invalid, GAPI.forbidden, GAPI.conditionNotMet) as e:
      entityActionFailedWarning([Ent.USER, targetEmail, Ent.USER_ALIAS, aliasEmail], str(e), i, count)
    except GAPI.invalidResource:
      entityActionFailedWarning([Ent.USER, targetEmail, Ent.USER_ALIAS, aliasEmail], Msg.DOES_NOT_EXIST, i, count)
  else:
    try:
      for aliasEmail in entityList:
        i += 1
        aliasEmail = normalizeEmailAddressOrUID(aliasEmail, noUid=True)
        callGAPI(cd.groups().aliases(), 'delete',
                 throwReasons=[GAPI.GROUP_NOT_FOUND, GAPI.USER_NOT_FOUND, GAPI.BAD_REQUEST, GAPI.INVALID, GAPI.FORBIDDEN, GAPI.INVALID_RESOURCE,
                               GAPI.CONDITION_NOT_MET],
                 groupKey=targetEmail, alias=aliasEmail)
        entityActionPerformed([Ent.GROUP, targetEmail, Ent.GROUP_ALIAS, aliasEmail], i, count)
    except (GAPI.groupNotFound, GAPI.userNotFound, GAPI.badRequest, GAPI.invalid, GAPI.forbidden, GAPI.conditionNotMet) as e:
      entityActionFailedWarning([Ent.GROUP, targetEmail, Ent.GROUP_ALIAS, aliasEmail], str(e), i, count)
    except GAPI.invalidResource:
      entityActionFailedWarning([Ent.GROUP, targetEmail, Ent.GROUP_ALIAS, aliasEmail], Msg.DOES_NOT_EXIST, i, count)

def _addUserAliases(cd, user, aliasList, i, count):
  jcount = len(aliasList)
  entityPerformActionNumItems([Ent.USER, user], jcount, Ent.USER_ALIAS, i, count)
  Ind.Increment()
  j = 0
  for aliasEmail in aliasList:
    j += 1
    aliasEmail = normalizeEmailAddressOrUID(aliasEmail, noUid=True, noLower=True)
    body = {'alias': aliasEmail}
    try:
      callGAPI(cd.users().aliases(), 'insert',
               throwReasons=[GAPI.USER_NOT_FOUND, GAPI.BAD_REQUEST,
                             GAPI.INVALID, GAPI.INVALID_INPUT, GAPI.FORBIDDEN, GAPI.DUPLICATE,
                             GAPI.CONDITION_NOT_MET, GAPI.LIMIT_EXCEEDED],
               userKey=user, body=body, fields='')
      entityActionPerformed([Ent.USER, user, Ent.USER_ALIAS, aliasEmail], j, jcount)
    except (GAPI.conditionNotMet, GAPI.limitExceeded) as e:
      entityActionFailedWarning([Ent.USER, user, Ent.USER_ALIAS, aliasEmail], str(e), j, jcount)
    except GAPI.duplicate:
      duplicateAliasGroupUserWarning(cd, [Ent.USER, user, Ent.USER_ALIAS, aliasEmail], j, jcount)
    except (GAPI.invalid, GAPI.invalidInput):
      entityActionFailedWarning([Ent.USER, user, Ent.USER_ALIAS, aliasEmail], Msg.INVALID_ALIAS, j, jcount)
    except (GAPI.userNotFound, GAPI.badRequest, GAPI.forbidden):
      entityUnknownWarning(Ent.USER, user, i, count)
  Ind.Decrement()

# gam <UserTypeEntity> delete alias|aliases
def deleteUsersAliases(users):
  cd = buildGAPIObject(API.DIRECTORY)
  checkForExtraneousArguments()
  i, count, users = getEntityArgument(users)
  for user in users:
    i += 1
    user = normalizeEmailAddressOrUID(user)
    try:
      user_aliases = callGAPI(cd.users(), 'get',
                              throwReasons=GAPI.USER_GET_THROW_REASONS,
                              userKey=user, fields='id,primaryEmail,aliases')
      user_id = user_aliases['id']
      user_primary = user_aliases['primaryEmail']
      jcount = len(user_aliases['aliases']) if ('aliases' in user_aliases) else 0
      entityPerformActionNumItems([Ent.USER, user_primary], jcount, Ent.ALIAS, i, count)
      if jcount == 0:
        setSysExitRC(NO_ENTITIES_FOUND_RC)
        continue
      Ind.Increment()
      j = 0
      for an_alias in user_aliases['aliases']:
        j += 1
        try:
          callGAPI(cd.users().aliases(), 'delete',
                   throwReasons=[GAPI.RESOURCE_ID_NOT_FOUND],
                   userKey=user_id, alias=an_alias)
          entityActionPerformed([Ent.USER, user_primary, Ent.ALIAS, an_alias], j, jcount)
        except GAPI.resourceIdNotFound:
          entityActionFailedWarning([Ent.USER, user_primary, Ent.ALIAS, an_alias], Msg.DOES_NOT_EXIST, j, jcount)
      Ind.Decrement()
    except (GAPI.userNotFound, GAPI.domainNotFound, GAPI.domainCannotUseApis, GAPI.forbidden,
            GAPI.badRequest, GAPI.backendError, GAPI.systemError):
      entityUnknownWarning(Ent.USER, user, i, count)

def infoAliases(entityList):

  from gam.cmd.groups.members import INFO_GROUP_OPTIONS
  from gam.cmd.users.manage import INFO_USER_OPTIONS
  def _showAliasInfo(uid, email, aliasEmail, entityType, aliasEntityType, i, count):
    if email.lower() != aliasEmail:
      printEntity([aliasEntityType, aliasEmail], i, count)
      Ind.Increment()
      printEntity([entityType, email])
      printEntity([Ent.UNIQUE_ID, uid])
      Ind.Decrement()
    else:
      setSysExitRC(ENTITY_IS_NOT_AN_ALIAS_RC)
      printEntityKVList([Ent.EMAIL, aliasEmail],
                        [f'Is a {Ent.Singular(entityType)}, not a {Ent.Singular(aliasEntityType)}'],
                        i, count)

  cd = buildGAPIObject(API.DIRECTORY)
  while Cmd.ArgumentsRemaining():
    myarg = getArgument()
# Ignore info group/user arguments that may have come from whatis
    if (myarg in INFO_GROUP_OPTIONS) or (myarg in INFO_USER_OPTIONS):
      if myarg == 'schemas':
        getString(Cmd.OB_SCHEMA_NAME_LIST)
    else:
      unknownArgumentExit()
  i = 0
  count = len(entityList)
  for aliasEmail in entityList:
    i += 1
    aliasEmail = normalizeEmailAddressOrUID(aliasEmail, noUid=True, noLower=True)
    try:
      result = callGAPI(cd.users(), 'get',
                        throwReasons=GAPI.USER_GET_THROW_REASONS,
                        userKey=aliasEmail, fields='id,primaryEmail')
      _showAliasInfo(result['id'], result['primaryEmail'], aliasEmail, Ent.USER_EMAIL, Ent.USER_ALIAS, i, count)
      continue
    except (GAPI.userNotFound, GAPI.badRequest):
      pass
    except (GAPI.domainNotFound, GAPI.domainCannotUseApis, GAPI.forbidden,
            GAPI.backendError, GAPI.systemError):
      entityUnknownWarning(Ent.USER_ALIAS, aliasEmail, i, count)
      continue
    try:
      result = callGAPI(cd.groups(), 'get',
                        throwReasons=GAPI.GROUP_GET_THROW_REASONS,
                        groupKey=aliasEmail, fields='id,email')
      _showAliasInfo(result['id'], result['email'], aliasEmail, Ent.GROUP_EMAIL, Ent.GROUP_ALIAS, i, count)
      continue
    except GAPI.groupNotFound:
      pass
    except (GAPI.domainNotFound, GAPI.domainCannotUseApis, GAPI.forbidden, GAPI.badRequest):
      entityUnknownWarning(Ent.GROUP_ALIAS, aliasEmail, i, count)
      continue
    entityUnknownWarning(Ent.EMAIL, aliasEmail, i, count)

# gam info aliases|nicknames <EmailAddressEntity>
def doInfoAliases():
  infoAliases(getEntityList(Cmd.OB_EMAIL_ADDRESS_ENTITY))

def initUserGroupDomainQueryFilters():
  if not GC.Values[GC.PRINT_AGU_DOMAINS]:
    return {'list': [{'customer': GC.Values[GC.CUSTOMER_ID]}], 'queries': [None]}
  return {'list': [{'domain': domain.lower()} for domain in GC.Values[GC.PRINT_AGU_DOMAINS].replace(',', ' ').split()], 'queries': [None]}

def getUserGroupDomainQueryFilters(myarg, kwargsDict):
  if myarg in {'domain', 'domains'}:
    kwargsDict['list'] = [{'domain': domain.lower()} for domain in getEntityList(Cmd.OB_DOMAIN_NAME_ENTITY)]
  elif myarg in {'query', 'queries'}:
    kwargsDict['queries'] = getQueries(myarg)
  else:
    return False
  return True

def makeUserGroupDomainQueryFilters(kwargsDict, isSuspended, isArchived, isDisabled):
  def addToQuery(query, keyword, value):
    pquery = query
    if not pquery:
      pquery = ''
    else:
      pquery += ' '
    pquery += f'{keyword}={value}'
    kwargsQueries.append((kwargs, pquery))

  kwargsQueries = []
  for kwargs in kwargsDict['list']:
    for query in kwargsDict['queries']:
      if isDisabled is not None:
        addToQuery(query, 'isArchived', isDisabled)
        addToQuery(query, 'isSuspended', isDisabled)
      elif isSuspended is not None or isArchived is not None:
        if isArchived is not None:
          addToQuery(query, 'isArchived', isArchived)
        if isSuspended is not None:
          addToQuery(query, 'isSuspended', isSuspended)
      else:
        kwargsQueries.append((kwargs, query))
  return kwargsQueries

def userFilters(kwargs, query, orgUnitPath):
  queryTitle = ''
  if kwargs.get('domain'):
    queryTitle += f'domain={kwargs["domain"]}, '
  if orgUnitPath is not None:
    if query is not None and query.find(orgUnitPath) == -1:
      query += f" orgUnitPath='{orgUnitPath}'"
    else:
      if query is None:
        query = ''
      else:
        query += ' '
      query += f"orgUnitPath='{orgUnitPath}'"
  if query is not None:
    queryTitle += f'query="{query}", '
  if queryTitle:
    return query, queryTitle[:-2]
  return query, queryTitle

# gam print aliases|nicknames [todrive <ToDriveAttribute>*]
#	([domain|domains <DomainNameEntity>] [(query <QueryUser>)|(queries <QueryUserList>)]
#	 [limittoou <OrgUnitItem>])
#	[user|users <EmailAddressList>] [group|groups <EmailAddressList>]
#	[select <UserTypeEntity>]
#	[issuspended [<Boolean>]] [isarchived [<Boolean>]]
#	[aliasmatchpattern <REMatchPattern>]
#	[shownoneditable] [nogroups] [nousers]
#	[onerowpertarget] [delimiter <Character>]
#	[suppressnoaliasrows]
#	(addcsvdata <FieldName> <String>)*
def doPrintAliases():
  from gam.cmd.groups.members import groupFilters
  def writeAliases(target, targetEmail, targetType):
    if not oneRowPerTarget:
      for alias in target.get('aliases', []):
        if aliasMatchPattern.match(alias):
          row = {'Alias': alias, 'Target': targetEmail, 'TargetType': targetType}
          if addCSVData:
            row.update(addCSVData)
          csvPF.WriteRow(row)
      if showNonEditable:
        for alias in target.get('nonEditableAliases', []):
          if aliasMatchPattern.match(alias):
            row = {'NonEditableAlias': alias, 'Target': targetEmail, 'TargetType': targetType}
            if addCSVData:
              row.update(addCSVData)
            csvPF.WriteRow(row)
    else:
      aliases = [alias for alias in target.get('aliases', []) if aliasMatchPattern.match(alias)]
      if showNonEditable:
        nealiases = [alias for alias in target.get('nonEditableAliases', []) if aliasMatchPattern.match(alias)]
      else:
        nealiases = []
      if suppressNoAliasRows and not aliases and not nealiases:
        return
      row = {'Target': targetEmail, 'TargetType': targetType, 'Aliases': delimiter.join(aliases)}
      if showNonEditable:
        row['NonEditableAliases'] = delimiter.join(nealiases)
      if addCSVData:
        row.update(addCSVData)
      csvPF.WriteRow(row)

  cd = buildGAPIObject(API.DIRECTORY)
  csvPF = CSVPrintFile()
  userFields = ['primaryEmail', 'aliases']
  groupFields = ['email', 'aliases']
  oneRowPerTarget = showNonEditable = suppressNoAliasRows = False
  kwargsDict = initUserGroupDomainQueryFilters()
  getGroups = getUsers = True
  groups = []
  users = []
  aliasMatchPattern = re.compile(r'^.*$')
  isArchived = isSuspended = orgUnitPath = None
  addCSVData = {}
  delimiter = GC.Values[GC.CSV_OUTPUT_FIELD_DELIMITER]
  while Cmd.ArgumentsRemaining():
    myarg = getArgument()
    if myarg == 'todrive':
      csvPF.GetTodriveParameters()
    elif myarg == 'shownoneditable':
      showNonEditable= True
      userFields.append('nonEditableAliases')
      groupFields.append('nonEditableAliases')
    elif myarg == 'nogroups':
      getGroups = False
    elif myarg == 'nousers':
      getUsers = False
    elif myarg == 'limittoou':
      orgUnitPath = getOrgUnitItem(pathOnly=True, cd=cd)
      orgUnitPathLower = orgUnitPath.lower()
      userFields.append('orgUnitPath')
      getGroups = False
    elif getUserGroupDomainQueryFilters(myarg, kwargsDict):
      pass
    elif myarg == 'select':
      _, users = getEntityToModify(defaultEntityType=Cmd.ENTITY_USERS)
    elif myarg == 'issuspended':
      isSuspended = getBoolean()
    elif myarg == 'isarchived':
      isArchived = getBoolean()
    elif myarg in {'user','users'}:
      users.extend(convertEntityToList(getString(Cmd.OB_EMAIL_ADDRESS_LIST, minLen=0)))
    elif myarg in {'group', 'groups'}:
      groups.extend(convertEntityToList(getString(Cmd.OB_EMAIL_ADDRESS_LIST, minLen=0)))
    elif myarg == 'aliasmatchpattern':
      aliasMatchPattern = getREPattern(re.IGNORECASE)
    elif myarg == 'onerowpertarget':
      oneRowPerTarget = True
    elif myarg == 'suppressnoaliasrows':
      suppressNoAliasRows = True
    elif myarg == 'addcsvdata':
      getAddCSVData(addCSVData)
    elif myarg == 'delimiter':
      delimiter = getCharacter()
    else:
      unknownArgumentExit()
  if (users or groups) and kwargsDict['queries'][0] is None:
    getUsers = getGroups = False
  if not oneRowPerTarget:
    titlesList = ['Alias', 'Target', 'TargetType']
    if showNonEditable:
      titlesList.insert(1, 'NonEditableAlias')
  else:
    titlesList = ['Target', 'TargetType', 'Aliases']
    if showNonEditable:
      titlesList.append('NonEditableAliases')
  csvPF.SetTitles(titlesList)
  if addCSVData:
    csvPF.AddTitles(sorted(addCSVData.keys()))
  if getUsers:
    for kwargsQuery in makeUserGroupDomainQueryFilters(kwargsDict, isSuspended, isArchived, None):
      kwargs = kwargsQuery[0]
      query = kwargsQuery[1]
      query, pquery = userFilters(kwargs, query, orgUnitPath)
      printGettingAllAccountEntities(Ent.USER, pquery)
      try:
        entityList = callGAPIpages(cd.users(), 'list', 'users',
                                   pageMessage=getPageMessage(showFirstLastItems=True), messageAttribute='primaryEmail',
                                   throwReasons=[GAPI.INVALID_ORGUNIT, GAPI.INVALID_INPUT, GAPI.DOMAIN_NOT_FOUND,
                                                 GAPI.RESOURCE_NOT_FOUND, GAPI.FORBIDDEN, GAPI.BAD_REQUEST,
                                                 GAPI.UNKNOWN_ERROR, GAPI.FAILED_PRECONDITION],
                                   retryReasons=GAPI.SERVICE_NOT_AVAILABLE_RETRY_REASONS+[GAPI.UNKNOWN_ERROR, GAPI.FAILED_PRECONDITION],
                                   query=query, orderBy='email',
                                   fields=f'nextPageToken,users({",".join(userFields)})',
                                   maxResults=GC.Values[GC.USER_MAX_RESULTS], **kwargs)
        for user in entityList:
          if orgUnitPath is None or orgUnitPathLower == user.get('orgUnitPath', '').lower():
            writeAliases(user, user['primaryEmail'], 'User')
      except (GAPI.invalidOrgunit, GAPI.invalidInput):
        entityActionFailedWarning([Ent.ALIAS, None], invalidQuery(query))
        continue
      except GAPI.domainNotFound as e:
        entityActionFailedWarning([Ent.ALIAS, None, Ent.DOMAIN, kwargs['domain']], str(e))
        continue
      except (GAPI.unknownError, GAPI.failedPrecondition) as e:
        entityActionFailedExit([Ent.USER, None], str(e))
      except (GAPI.resourceNotFound, GAPI.forbidden, GAPI.badRequest):
        accessErrorExit(cd)
  count = len(users)
  i = 0
  for user in users:
    i += 1
    user = normalizeEmailAddressOrUID(user)
    printGettingEntityItemForWhom(Ent.USER_ALIAS, user, i, count)
    try:
      result = callGAPI(cd.users().aliases(), 'list',
                        throwReasons=[GAPI.USER_NOT_FOUND, GAPI.BAD_REQUEST, GAPI.INVALID, GAPI.FORBIDDEN, GAPI.INVALID_RESOURCE,
                                      GAPI.CONDITION_NOT_MET],
                        userKey=user, fields='aliases(alias)')
      aliases = {'aliases': [alias['alias'] for alias in result.get('aliases', [])]}
      writeAliases(aliases, user, 'User')
    except (GAPI.userNotFound, GAPI.badRequest, GAPI.invalid, GAPI.forbidden, GAPI.invalidResource, GAPI.conditionNotMet) as e:
      entityActionFailedWarning([Ent.USER, user], str(e), i, count)
  if getGroups:
    for kwargsQuery in makeUserGroupDomainQueryFilters(kwargsDict, None, None, None):
      kwargs = kwargsQuery[0]
      query = kwargsQuery[1]
      query, pquery = groupFilters(kwargs, query)
      printGettingAllAccountEntities(Ent.GROUP, pquery)
      try:
        entityList = callGAPIpages(cd.groups(), 'list', 'groups',
                                   pageMessage=getPageMessage(showFirstLastItems=True), messageAttribute='email',
                                   throwReasons=GAPI.GROUP_LIST_USERKEY_THROW_REASONS,
                                   retryReasons=GAPI.SERVICE_NOT_AVAILABLE_RETRY_REASONS,
                                   query=query, orderBy='email',
                                   fields=f'nextPageToken,groups({",".join(groupFields)})', **kwargs)
        for group in entityList:
          writeAliases(group, group['email'], 'Group')
      except (GAPI.invalidMember, GAPI.invalidInput) as e:
        if not invalidMember(query):
          entityActionFailedExit([Ent.GROUP, None], str(e))
      except GAPI.domainNotFound as e:
        entityActionFailedWarning([Ent.ALIAS, None, Ent.DOMAIN, kwargs['domain']], str(e))
        continue
      except (GAPI.resourceNotFound, GAPI.forbidden, GAPI.badRequest):
        accessErrorExit(cd)
  count = len(groups)
  i = 0
  for group in groups:
    i += 1
    group = normalizeEmailAddressOrUID(group)
    printGettingEntityItemForWhom(Ent.GROUP_ALIAS, group, i, count)
    try:
      result = callGAPI(cd.groups().aliases(), 'list',
                        throwReasons=[GAPI.GROUP_NOT_FOUND, GAPI.BAD_REQUEST, GAPI.INVALID, GAPI.FORBIDDEN, GAPI.INVALID_RESOURCE,
                                      GAPI.CONDITION_NOT_MET],
                        groupKey=group, fields='aliases(alias)')
      aliases = {'aliases': [alias['alias'] for alias in result.get('aliases', [])]}
      writeAliases(aliases, group, 'Group')
    except (GAPI.groupNotFound, GAPI.badRequest, GAPI.invalid, GAPI.forbidden, GAPI.invalidResource, GAPI.conditionNotMet) as e:
      entityActionFailedWarning([Ent.GROUP, group], str(e), i, count)
  csvPF.writeCSVfile('Aliases')

# gam print addresses [todrive <ToDriveAttribute>*]
#	[domain <DomainName>]
def doPrintAddresses():
  cd = buildGAPIObject(API.DIRECTORY)
  kwargs = {'customer': GC.Values[GC.CUSTOMER_ID]}
  csvPF = CSVPrintFile()
  titlesList = ['Type', 'Email', 'Target']
  userFields = ['primaryEmail', 'aliases', 'nonEditableAliases', 'suspended']
  groupFields = ['email', 'aliases', 'nonEditableAliases']
  domainFields = ['domainName', 'isPrimary', 'domainAliases']
  resourceFields = ['resourceEmail']
  while Cmd.ArgumentsRemaining():
    myarg = getArgument()
    if myarg == 'todrive':
      csvPF.GetTodriveParameters()
    elif myarg == 'domain':
      kwargs['domain'] = getString(Cmd.OB_DOMAIN_NAME).lower()
      kwargs.pop('customer', None)
    else:
      unknownArgumentExit()
  csvPF.SetTitles(titlesList)
  printGettingAllAccountEntities(Ent.USER)
  try:
    entityList = callGAPIpages(cd.users(), 'list', 'users',
                               pageMessage=getPageMessage(showFirstLastItems=True), messageAttribute='primaryEmail',
                               throwReasons=[GAPI.RESOURCE_NOT_FOUND, GAPI.FORBIDDEN, GAPI.BAD_REQUEST,
                                             GAPI.UNKNOWN_ERROR, GAPI.FAILED_PRECONDITION],
                               retryReasons=GAPI.SERVICE_NOT_AVAILABLE_RETRY_REASONS+[GAPI.UNKNOWN_ERROR, GAPI.FAILED_PRECONDITION],
                               orderBy='email', fields=f'nextPageToken,users({",".join(userFields)})',
                               maxResults=GC.Values[GC.USER_MAX_RESULTS], **kwargs)
  except (GAPI.unknownError, GAPI.failedPrecondition) as e:
    entityActionFailedExit([Ent.USER, None], str(e))
  except (GAPI.resourceNotFound, GAPI.forbidden, GAPI.badRequest):
    accessErrorExit(cd)
  for user in entityList:
    userEmail = user['primaryEmail']
    prefix = '' if not user['suspended'] else 'Suspended'
    csvPF.WriteRow({'Type': f'{prefix}User', 'Email': userEmail})
    for alias in user.get('aliases', []):
      csvPF.WriteRow({'Type': f'{prefix}UserAlias', 'Email': alias, 'Target': userEmail})
    for alias in user.get('nonEditableAliases', []):
      csvPF.WriteRow({'Type': f'{prefix}UserNEAlias', 'Email': alias, 'Target': userEmail})
  printGettingAllAccountEntities(Ent.GROUP)
  try:
    entityList = callGAPIpages(cd.groups(), 'list', 'groups',
                               pageMessage=getPageMessage(showFirstLastItems=True), messageAttribute='email',
                               throwReasons=GAPI.GROUP_LIST_THROW_REASONS,
                               retryReasons=GAPI.SERVICE_NOT_AVAILABLE_RETRY_REASONS,
                               orderBy='email', fields=f'nextPageToken,groups({",".join(groupFields)})', **kwargs)
  except (GAPI.resourceNotFound, GAPI.domainNotFound, GAPI.forbidden, GAPI.badRequest):
    accessErrorExit(cd)
  for group in entityList:
    groupEmail = group['email']
    csvPF.WriteRow({'Type': 'Group', 'Email': groupEmail})
    for alias in group.get('aliases', []):
      csvPF.WriteRow({'Type': 'GroupAlias', 'Email': alias, 'Target': groupEmail})
    for alias in group.get('nonEditableAliases', []):
      csvPF.WriteRow({'Type': 'GroupNEAlias', 'Email': alias, 'Target': groupEmail})
  printGettingAllAccountEntities(Ent.RESOURCE_CALENDAR)
  try:
    entityList = callGAPIpages(cd.resources().calendars(), 'list', 'items',
                               pageMessage=getPageMessage(showFirstLastItems=True), messageAttribute='resourceEmail',
                               throwReasons=[GAPI.BAD_REQUEST, GAPI.RESOURCE_NOT_FOUND, GAPI.FORBIDDEN, GAPI.INVALID_INPUT],
                               customer=GC.Values[GC.CUSTOMER_ID], fields=f'nextPageToken,items({",".join(resourceFields)})')
  except (GAPI.badRequest, GAPI.resourceNotFound, GAPI.forbidden):
    accessErrorExit(cd)
  except GAPI.invalidInput as e:
    entityActionFailedWarning([Ent.RESOURCE_CALENDAR, ''], str(e))
    return
  for resource in entityList:
    csvPF.WriteRow({'Type': 'Resource', 'Email': resource['resourceEmail']})
  domains = _getDomainList(cd, GC.Values[GC.CUSTOMER_ID], f'domains({",".join(domainFields)})')
  for domain in domains:
    domainEmail = domain['domainName']
    csvPF.WriteRow({'Type': 'DomainPrimary' if domain['isPrimary'] else 'DomainSecondary', 'Email': domainEmail})
    for alias in domain.get('domainAliases', []):
      csvPF.WriteRow({'Type': 'DomainAlias', 'Email': alias['domainAliasName'], 'Target': domainEmail})
  csvPF.SortRowsTwoTitles('Type', 'Email', False)
  csvPF.writeCSVfile('Addresses')

# Contact commands utilities
#
