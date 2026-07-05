"""GAM entity resolution utilities.

UID-to-email conversion, entity list expansion, group member
checking, entity selectors, and customer ID helpers.
"""

import os
import platform
import re
import sys

from gamlib import api as API
from gamlib import settings as GC
from gamlib import gapi as GAPI
from gamlib import state as GM
from gamlib import msgs as Msg



# Convert User UID from API call to email address
def convertUserIDtoEmail(uid, cd=None):
  primaryEmail = GM.Globals[GM.MAP_USER_ID_TO_NAME].get(uid)
  if not primaryEmail:
    if cd is None:
      cd = buildGAPIObject(API.DIRECTORY)
    try:
      primaryEmail = callGAPI(cd.users(), 'get',
                              throwReasons=GAPI.USER_GET_THROW_REASONS,
                              userKey=uid, fields='primaryEmail')['primaryEmail']
    except (GAPI.userNotFound, GAPI.domainNotFound, GAPI.domainCannotUseApis, GAPI.forbidden,
            GAPI.badRequest, GAPI.backendError, GAPI.systemError):
      primaryEmail = f'uid:{uid}'
    GM.Globals[GM.MAP_USER_ID_TO_NAME][uid] = primaryEmail
  return primaryEmail

# Convert UID to split email address
# Return (foo@bar.com, foo, bar.com)
def splitEmailAddressOrUID(emailAddressOrUID):
  normalizedEmailAddressOrUID = normalizeEmailAddressOrUID(emailAddressOrUID)
  atLoc = normalizedEmailAddressOrUID.find('@')
  if atLoc > 0:
    return (normalizedEmailAddressOrUID, normalizedEmailAddressOrUID[:atLoc], normalizedEmailAddressOrUID[atLoc+1:])
  try:
    cd = buildGAPIObject(API.DIRECTORY)
    result = callGAPI(cd.users(), 'get',
                      throwReasons=GAPI.USER_GET_THROW_REASONS,
                      userKey=normalizedEmailAddressOrUID, fields='primaryEmail')
    if 'primaryEmail' in result:
      normalizedEmailAddressOrUID = result['primaryEmail'].lower()
      atLoc = normalizedEmailAddressOrUID.find('@')
      return (normalizedEmailAddressOrUID, normalizedEmailAddressOrUID[:atLoc], normalizedEmailAddressOrUID[atLoc+1:])
  except (GAPI.userNotFound, GAPI.domainNotFound, GAPI.domainCannotUseApis, GAPI.forbidden,
          GAPI.badRequest, GAPI.backendError, GAPI.systemError):
    pass
  return (normalizedEmailAddressOrUID, normalizedEmailAddressOrUID, GC.Values[GC.DOMAIN])

# Convert Org Unit Id to Org Unit Path
def convertOrgUnitIDtoPath(cd, orgUnitId):
  if orgUnitId.lower().startswith('orgunits/'):
    orgUnitId = f'id:{orgUnitId[9:]}'
  orgUnitPath = GM.Globals[GM.MAP_ORGUNIT_ID_TO_NAME].get(orgUnitId)
  if not orgUnitPath:
    if cd is None:
      cd = buildGAPIObject(API.DIRECTORY)
    try:
      orgUnitPath = callGAPI(cd.orgunits(), 'get',
                             throwReasons=GAPI.ORGUNIT_GET_THROW_REASONS,
                             customerId=GC.Values[GC.CUSTOMER_ID], orgUnitPath=orgUnitId, fields='orgUnitPath')['orgUnitPath']
    except (GAPI.invalidOrgunit, GAPI.orgunitNotFound, GAPI.backendError, GAPI.badRequest, GAPI.invalidCustomerId, GAPI.loginRequired):
      orgUnitPath = orgUnitId
    GM.Globals[GM.MAP_ORGUNIT_ID_TO_NAME][orgUnitId] = orgUnitPath
  return orgUnitPath

from gam.constants import DATA_ERROR_RC, INVALID_ENTITY_RC, NO_ENTITIES_FOUND_RC, UNKNOWN_ERROR_RC
from gamlib import skus as SKU
from util.args import ARCHIVED_ARGUMENTS, FALSE_VALUES, SUSPENDED_ARGUMENTS, TRUE_VALUES, _getIsArchived, _getIsSuspended, checkArgumentPresent, checkDataField, checkSubkeyField, getArgument, getCharSet, getChoice, getDelimiter, getMatchSkipFields, getREPattern, getString, makeOrgUnitPathAbsolute, normalizeEmailAddressOrUID, orgUnitPathQuery, shlexSplitList, shlexSplitListStatus, splitEmailAddress, validateEmailAddressOrUID
from util.row_filter import checkMatchSkipFields
from util.display import ENTITY_DOES_NOT_EXIST_RC, entityActionFailedWarning, entityActionNotPerformedWarning, entityDoesNotExistWarning, entityPerformActionNumItems, getPageMessage, getPageMessageForWhom, printGettingAllAccountEntities, printGettingAllEntityItemsForWhom, printGotEntityItemsForWhom, setGettingAllEntityItemsForWhom
from util.errors import csvDataAlreadySavedErrorExit, csvFieldErrorExit, invalidArgumentExit, invalidChoiceExit, missingArgumentExit, usageErrorExit
from util.fileio import closeFile, openFile, setFilePath
from util.gdoc import getGDocData, getStorageFileData, openCSVFileReader
from util.output import formatKeyValueList, printErrorMessage, setSysExitRC, stderrErrorMsg, systemErrorExit, writeStderr
from gam.util.access import accessErrorExit
from util.access import accessErrorExit, checkEntityDNEorAccessErrorExit, entityUnknownWarning
from util.api import ClientAPIAccessDeniedExit, _getAdminEmail, buildGAPIObject
from util.svcacct import buildGAPIServiceObject
from util.api_call import callGAPI, callGAPIitems, callGAPIpages, yieldGAPIpages
from gam.var import Act, Cmd, Ent
from gam.util.access import accessErrorExitNonDirectory
from util.customer import _getCustomerIdNoC
from util.course_scope import removeCourseIdScope

def getQueries(myarg):
  if myarg in {'query', 'filter'}:
    return [getString(Cmd.OB_QUERY)]
  return shlexSplitList(getString(Cmd.OB_QUERY_LIST))

def _validateDeviceQuery(entityType, query):
  if ':' in query:
    qfield, qvalue = query.split(':', 1)
    qfield = qfield.strip()
  else:
    qfield = ''
    qvalue = query
  if (not qfield) or (not qvalue)  or ('?' in query):
    Cmd.Backup()
    usageErrorExit(Msg.INVALID_DEVICE_QUERY.format(Ent.Singular(entityType), query))

def getDeviceQueries(myarg, entityType):
  if myarg in {'query', 'filter'}:
    queries = [getString(Cmd.OB_QUERY)]
  else:
    queries = shlexSplitList(getString(Cmd.OB_QUERY_LIST))
  for query in queries:
    _validateDeviceQuery(entityType, query)
  return queries

def convertEntityToList(entity, shlexSplit=False, nonListEntityType=False):
  if not entity:
    return []
  if isinstance(entity, (list, set, dict)):
    return list(entity)
  if nonListEntityType:
    return [entity.strip()]
  if not shlexSplit:
    return entity.replace(',', ' ').split()
  return shlexSplitList(entity)

GROUP_ROLES_MAP = {
  'owner': 'OWNER',
  'owners': 'OWNER',
  'manager': 'MANAGER',
  'managers': 'MANAGER',
  'member': 'MEMBER',
  'members': 'MEMBER',
  }
ALL_GROUP_ROLES = {'MANAGER', 'MEMBER', 'OWNER'}

def _getRoleVerification(memberRoles, fields):
  if memberRoles and memberRoles.find(Ent.ROLE_MEMBER) != -1:
    return (set(memberRoles.split(',')), None, fields if fields.find('role') != -1 else fields[:-1]+',role)')
  return (set(), memberRoles, fields)

def _getCIRoleVerification(memberRoles):
  if memberRoles:
    return set(memberRoles.split(','))
  return set()

def _checkMemberStatusIsSuspendedIsArchived(memberStatus, isSuspended, isArchived):
  if isSuspended is None and isArchived is None:
    return True
  if isSuspended is not None and isArchived is not None:
    if isSuspended == isArchived:
      if not isSuspended:
        return memberStatus not in {'SUSPENDED', 'ARCHIVED'}
      return memberStatus in {'SUSPENDED', 'ARCHIVED'}
    if isSuspended:
      return memberStatus == 'SUSPENDED'
    return memberStatus == 'ARCHIVED'
  if isSuspended is not None:
    if (not isSuspended and memberStatus != 'SUSPENDED') or (isSuspended and memberStatus == 'SUSPENDED'):
      return True
  if isArchived is not None:
    if (not isArchived and memberStatus != 'ARCHIVED') or (isArchived and memberStatus == 'ARCHIVED'):
      return True
  return False

def _checkMemberIsSuspendedIsArchived(member, isSuspended, isArchived):
  return _checkMemberStatusIsSuspendedIsArchived(member.get('status', 'UNKNOWN'), isSuspended, isArchived)

def _checkMemberRole(member, validRoles):
  return not validRoles or member.get('role', Ent.ROLE_MEMBER) in validRoles

def _checkMemberRoleIsSuspendedIsArchived(member, validRoles, isSuspended, isArchived):
  return _checkMemberRole(member, validRoles) and _checkMemberIsSuspendedIsArchived(member, isSuspended, isArchived)

def _checkMemberCategory(member, memberDisplayOptions):
  member_email = member.get('email', member.get('id', ''))
  if member_email.find('@') > 0:
    _, domain = member_email.lower().split('@', 1)
    category = 'internal' if domain in memberDisplayOptions['internalDomains'] else 'external'
  else:
    category = 'internal'
  if memberDisplayOptions['showCategory']:
    member['category'] = category
  if memberDisplayOptions['checkCategory']:
    return bool(memberDisplayOptions[category])
  return True

def _checkCIMemberCategory(member, memberDisplayOptions):
  member_email = member.get('preferredMemberKey', {}).get('id', '')
  if member_email.find('@') > 0:
    _, domain = member_email.lower().split('@', 1)
    category = 'internal' if domain in memberDisplayOptions['internalDomains'] else 'external'
  else:
    category = 'internal'
  if memberDisplayOptions['showCategory']:
    member['category'] = category
  if memberDisplayOptions['checkCategory']:
    return bool(memberDisplayOptions[category])
  return True

def getCIGroupMemberRoleFixType(member):
  ''' fixes missing type/id and returns the highest role of member '''
  if 'type' not in member:
    if 'id' not in member['preferredMemberKey']:
      member['preferredMemberKey']['id'] = GC.Values[GC.CUSTOMER_ID]
      member['type'] = Ent.TYPE_CUSTOMER
    elif member['preferredMemberKey']['id'] == GC.Values[GC.CUSTOMER_ID]:
      member['type'] = Ent.TYPE_CUSTOMER
    else:
      member['type'] = Ent.TYPE_OTHER
  roles = {}
  memberRoles = member.get('roles', [{'name': Ent.ROLE_MEMBER}])
  for role in memberRoles:
    roles[role['name']] = role
  for a_role in [Ent.ROLE_OWNER, Ent.ROLE_MANAGER, Ent.ROLE_MEMBER]:
    if a_role in roles:
      member['role'] = a_role
      if 'expiryDetail' in roles[a_role]:
        member['expireTime'] = roles[a_role]['expiryDetail']['expireTime']
      return
  member['role'] = memberRoles[0]['name']

def getCIGroupTransitiveMemberRoleFixType(groupName, tmember):
  ''' map transitive member to normal member '''
  tid = tmember['preferredMemberKey'][0].get('id', GC.Values[GC.CUSTOMER_ID]) if tmember['preferredMemberKey'] else ''
  if '/' in tmember['member']:
    ttype, tname = tmember['member'].split('/')
  else:
    ttype = ''
    tname = tmember['member']
  member = {'name': f'{groupName}/membershipd/{tname}', 'preferredMemberKey': {'id': tid}}
  if 'type' not in tmember:
    if tid == GC.Values[GC.CUSTOMER_ID]:
      member['type'] = Ent.TYPE_CUSTOMER
    elif ttype == 'users':
      member['type'] = Ent.TYPE_USER if not tid.endswith('.iam.gserviceaccount.com') else Ent.TYPE_SERVICE_ACCOUNT
    elif ttype == 'groups':
      member['type'] = Ent.TYPE_GROUP
    elif tid.startswith('cbcm-browser.'):
      member['type'] = Ent.TYPE_CBCM_BROWSER
    else:
      member['type'] = Ent.TYPE_OTHER
  else:
    member['type'] = tmember['type']
  if 'roles' in tmember:
    memberRoles = []
    for trole in tmember['roles']:
      if 'role' in trole:
        trole['name'] = trole.pop('role')
      if trole['name'] == 'ADMIN':
        trole['name'] = Ent.ROLE_MANAGER
      memberRoles.append(trole)
  else:
    memberRoles = [{'name': Ent.ROLE_MEMBER}]
  roles = {}
  for role in memberRoles:
    roles[role['name']] = role
  for a_role in [Ent.ROLE_OWNER, Ent.ROLE_MANAGER, Ent.ROLE_MEMBER]:
    if a_role in roles:
      member['role'] = a_role
      if 'expiryDetail' in roles[a_role]:
        member['expireTime'] = roles[a_role]['expiryDetail']['expireTime']
      break
  else:
    member['role'] = memberRoles[0]['name']
  return member

def convertGroupCloudIDToEmail(ci, group, i=0, count=0):
  if not group.startswith('groups/'):
    group = normalizeEmailAddressOrUID(group, ciGroupsAPI=True)
    if not group.startswith('groups/'):
      return (ci, None, group)
  if not ci:
    ci = buildGAPIObject(API.CLOUDIDENTITY_GROUPS)
  try:
    ciGroup = callGAPI(ci.groups(), 'get',
                       throwReasons=GAPI.CIGROUP_GET_THROW_REASONS, retryReasons=GAPI.CIGROUP_RETRY_REASONS,
                       name=group, fields='groupKey(id)')
    return (ci, None, ciGroup['groupKey']['id'])
  except (GAPI.notFound, GAPI.domainNotFound, GAPI.domainCannotUseApis,
          GAPI.forbidden, GAPI.badRequest, GAPI.invalid, GAPI.invalidArgument,
          GAPI.systemError, GAPI.permissionDenied, GAPI.serviceNotAvailable) as e:
    action = Act.Get()
    Act.Set(Act.LOOKUP)
    entityActionFailedWarning([Ent.CLOUD_IDENTITY_GROUP, group, Ent.GROUP, None], str(e), i, count)
    Act.Set(action)
    return (ci, None, None)

def convertGroupEmailToCloudID(ci, group, i=0, count=0):
  group = normalizeEmailAddressOrUID(group, ciGroupsAPI=True)
  if not group.startswith('groups/') and group.find('@') == -1:
    group = 'groups/'+group
  if group.startswith('groups/'):
    ci, _, groupEmail = convertGroupCloudIDToEmail(ci, group, i, count)
    return (ci, group, groupEmail)
  if not ci:
    ci = buildGAPIObject(API.CLOUDIDENTITY_GROUPS)
  try:
    ciGroup = callGAPI(ci.groups(), 'lookup',
                       throwReasons=GAPI.CIGROUP_GET_THROW_REASONS, retryReasons=GAPI.CIGROUP_RETRY_REASONS,
                       groupKey_id=group, fields='name')
    return (ci, ciGroup['name'], group)
  except (GAPI.notFound, GAPI.domainNotFound, GAPI.domainCannotUseApis,
          GAPI.forbidden, GAPI.badRequest, GAPI.invalid, GAPI.invalidArgument,
          GAPI.systemError, GAPI.failedPrecondition, GAPI.permissionDenied, GAPI.serviceNotAvailable) as e:
    action = Act.Get()
    Act.Set(Act.LOOKUP)
    entityActionFailedWarning([Ent.CLOUD_IDENTITY_GROUP, group], str(e), i, count)
    Act.Set(action)
    return (ci, None, None)

CIGROUP_DISCUSSION_FORUM_LABEL = 'cloudidentity.googleapis.com/groups.discussion_forum'
CIGROUP_DYNAMIC_LABEL = 'cloudidentity.googleapis.com/groups.dynamic'
CIGROUP_SECURITY_LABEL = 'cloudidentity.googleapis.com/groups.security'
CIGROUP_LOCKED_LABEL = 'cloudidentity.googleapis.com/groups.locked'

def getCIGroupMembershipGraph(ci, member):
  if not ci:
    ci = buildGAPIObject(API.CLOUDIDENTITY_GROUPS)
  parent = 'groups/-'
  try:
    result = callGAPI(ci.groups().memberships(), 'getMembershipGraph',
                      throwReasons=GAPI.CIGROUP_LIST_THROW_REASONS, retryReasons=GAPI.CIGROUP_RETRY_REASONS,
                      parent=parent,
                      query=f"member_key_id == '{member}' && '{CIGROUP_DISCUSSION_FORUM_LABEL}' in labels")
    return (ci, result.get('response', {}))
  except (GAPI.resourceNotFound, GAPI.domainNotFound, GAPI.domainCannotUseApis,
          GAPI.forbidden, GAPI.badRequest, GAPI.invalid, GAPI.invalidArgument,
          GAPI.systemError, GAPI.permissionDenied, GAPI.serviceNotAvailable) as e:
    action = Act.Get()
    Act.Set(Act.LOOKUP)
    entityActionFailedWarning([Ent.CLOUD_IDENTITY_GROUP, parent], str(e))
    Act.Set(action)
    return (ci, None)

def checkGroupExists(cd, ci, ciGroupsAPI, group, i=0, count=0):
  group = normalizeEmailAddressOrUID(group, ciGroupsAPI=ciGroupsAPI)
  if not ciGroupsAPI:
    if not group.startswith('groups/'):
      try:
        result = callGAPI(cd.groups(), 'get',
                          throwReasons=GAPI.GROUP_GET_THROW_REASONS, retryReasons=GAPI.GROUP_GET_RETRY_REASONS,
                          groupKey=group, fields='email')
        return (ci, None, result['email'])
      except (GAPI.groupNotFound, GAPI.domainNotFound, GAPI.domainCannotUseApis, GAPI.forbidden, GAPI.badRequest, GAPI.invalid, GAPI.systemError):
        entityUnknownWarning(Ent.GROUP, group, i, count)
        return (ci, None, None)
    else:
      ci, _, groupEmail = convertGroupCloudIDToEmail(ci, group, i, count)
      return (ci, None, groupEmail)
  else:
    if not group.startswith('groups/') and group.find('@') == -1:
      group = 'groups/'+group
    if group.startswith('groups/'):
      try:
        result = callGAPI(ci.groups(), 'get',
                          throwReasons=GAPI.CIGROUP_GET_THROW_REASONS, retryReasons=GAPI.CIGROUP_RETRY_REASONS,
                          name=group, fields='name,groupKey(id)')
        return (ci, result['name'], result['groupKey']['id'])
      except (GAPI.notFound, GAPI.domainNotFound, GAPI.domainCannotUseApis,
              GAPI.forbidden, GAPI.badRequest, GAPI.invalid, GAPI.invalidArgument,
              GAPI.systemError, GAPI.permissionDenied, GAPI.serviceNotAvailable):
        entityUnknownWarning(Ent.CLOUD_IDENTITY_GROUP, group, i, count)
        return (ci, None, None)
    else:
      return convertGroupEmailToCloudID(ci, group, i, count)

# Turn the entity into a list of Users/CrOS devices
def getItemsToModify(entityType, entity, memberRoles=None, isSuspended=None, isArchived=None,
                     groupMemberType='USER', noListConversion=False, recursive=False, noCLArgs=False):
  def _incrEntityDoesNotExist(entityType):
    entityError['entityType'] = entityType
    entityError[ENTITY_ERROR_DNE] += 1

  def _showInvalidEntity(entityType, entityName):
    entityError['entityType'] = entityType
    entityError[ENTITY_ERROR_INVALID] += 1
    printErrorMessage(INVALID_ENTITY_RC, formatKeyValueList('', [Ent.Singular(entityType), entityName, Msg.INVALID], ''))

  def _addGroupUsersToUsers(group, domains, recursive, includeDerivedMembership):
    printGettingAllEntityItemsForWhom(memberRoles if memberRoles else Ent.ROLE_MANAGER_MEMBER_OWNER, group, entityType=Ent.GROUP)
    validRoles, listRoles, listFields = _getRoleVerification(memberRoles, 'nextPageToken,members(email,type,status)')
    try:
      result = callGAPIpages(cd.members(), 'list', 'members',
                             pageMessage=getPageMessageForWhom(),
                             throwReasons=GAPI.MEMBERS_THROW_REASONS, retryReasons=GAPI.MEMBERS_RETRY_REASONS,
                             includeDerivedMembership=includeDerivedMembership,
                             groupKey=group, roles=listRoles, fields=listFields, maxResults=GC.Values[GC.MEMBER_MAX_RESULTS])
    except (GAPI.groupNotFound, GAPI.domainNotFound, GAPI.domainCannotUseApis, GAPI.invalid, GAPI.forbidden, GAPI.serviceNotAvailable):
      entityUnknownWarning(Ent.GROUP, group)
      _incrEntityDoesNotExist(Ent.GROUP)
      return
    for member in result:
      if member['type'] == Ent.TYPE_USER:
        email = member['email'].lower()
        if email in entitySet:
          continue
        if _checkMemberRoleIsSuspendedIsArchived(member, validRoles, isSuspended, isArchived):
          if domains:
            _, domain = splitEmailAddress(email)
            if domain not in domains:
              continue
          entitySet.add(email)
          entityList.append(email)
      elif recursive and member['type'] == Ent.TYPE_GROUP:
        _addGroupUsersToUsers(member['email'], domains, recursive, includeDerivedMembership)

  def _addCIGroupUsersToUsers(groupName, groupEmail, recursive):
    printGettingAllEntityItemsForWhom(memberRoles if memberRoles else Ent.ROLE_MANAGER_MEMBER_OWNER, groupEmail, entityType=Ent.CLOUD_IDENTITY_GROUP)
    validRoles = _getCIRoleVerification(memberRoles)
    try:
      result = callGAPIpages(ci.groups().memberships(), 'list', 'memberships',
                             pageMessage=getPageMessageForWhom(),
                             throwReasons=GAPI.CIGROUP_LIST_THROW_REASONS, retryReasons=GAPI.CIGROUP_RETRY_REASONS,
                             parent=groupName, view='FULL',
                             fields='nextPageToken,memberships(name,preferredMemberKey(id),roles(name),type)', pageSize=GC.Values[GC.MEMBER_MAX_RESULTS])
    except (GAPI.resourceNotFound, GAPI.domainNotFound, GAPI.domainCannotUseApis,
            GAPI.forbidden, GAPI.badRequest, GAPI.invalid, GAPI.invalidArgument,
            GAPI.systemError, GAPI.permissionDenied, GAPI.serviceNotAvailable):
      entityUnknownWarning(Ent.CLOUD_IDENTITY_GROUP, groupEmail)
      _incrEntityDoesNotExist(Ent.CLOUD_IDENTITY_GROUP)
      return
    for member in result:
      getCIGroupMemberRoleFixType(member)
      if member['type'] == Ent.TYPE_USER:
        email = member.get('preferredMemberKey', {}).get('id', '')
        if (email and _checkMemberRole(member, validRoles) and email not in entitySet):
          entitySet.add(email)
          entityList.append(email)
      elif recursive and member['type'] == Ent.TYPE_GROUP and _checkMemberRole(member, validRoles):
        _, gname = member['name'].rsplit('/', 1)
        _addCIGroupUsersToUsers(f'groups/{gname}', f'groups/{gname}', recursive)

  GM.Globals[GM.CLASSROOM_SERVICE_NOT_AVAILABLE] = False
  ENTITY_ERROR_DNE = 'doesNotExist'
  ENTITY_ERROR_INVALID = 'invalid'
  entityError = {'entityType': None, ENTITY_ERROR_DNE: 0, ENTITY_ERROR_INVALID: 0}
  entityList = []
  entitySet = set()
  entityLocation = Cmd.Location()
  if entityType in {Cmd.ENTITY_USER, Cmd.ENTITY_USERS}:
    if not GC.Values[GC.USER_SERVICE_ACCOUNT_ACCESS_ONLY] and not GC.Values[GC.DOMAIN]:
      buildGAPIObject(API.DIRECTORY)
    result = convertEntityToList(entity, nonListEntityType=entityType == Cmd.ENTITY_USER)
    for user in result:
      if validateEmailAddressOrUID(user):
        if user not in entitySet:
          entitySet.add(user)
          entityList.append(user)
      else:
        _showInvalidEntity(Ent.USER, user)
    if GC.Values[GC.USER_SERVICE_ACCOUNT_ACCESS_ONLY]:
      return entityList
  elif entityType in Cmd.ALL_USER_ENTITY_TYPES:
    cd = buildGAPIObject(API.DIRECTORY)
    if entityType == Cmd.ENTITY_ALL_USERS and ((isSuspended is not None) or (isArchived is not None)):
      if isSuspended is not None:
        query = f'isSuspended={isSuspended}'
        if isArchived is not None:
          query += f' isArchived={isArchived}'
      else:
        query = f'isArchived={isArchived}'
    else:
      query = Cmd.ALL_USERS_QUERY_MAP[entityType]
    printGettingAllAccountEntities(Ent.USER, query=query)
    try:
      result = callGAPIpages(cd.users(), 'list', 'users',
                             pageMessage=getPageMessage(),
                             throwReasons=[GAPI.BAD_REQUEST, GAPI.RESOURCE_NOT_FOUND, GAPI.FORBIDDEN],
                             retryReasons=GAPI.SERVICE_NOT_AVAILABLE_RETRY_REASONS,
                             customer=GC.Values[GC.CUSTOMER_ID], query=query, orderBy='email',
                             fields='nextPageToken,users(primaryEmail)',
                             maxResults=GC.Values[GC.USER_MAX_RESULTS])
    except (GAPI.badRequest, GAPI.resourceNotFound, GAPI.forbidden):
      accessErrorExit(cd)
    entityList = [user['primaryEmail'] for user in result]
  elif entityType == Cmd.ENTITY_ALL_USERS_ARCH_OR_SUSP:
    cd = buildGAPIObject(API.DIRECTORY)
    for query in ['isSuspended=True', 'isArchived=True']:
      printGettingAllAccountEntities(Ent.USER, query)
      try:
        result = callGAPIpages(cd.users(), 'list', 'users',
                               pageMessage=getPageMessage(),
                               throwReasons=[GAPI.BAD_REQUEST, GAPI.RESOURCE_NOT_FOUND, GAPI.FORBIDDEN],
                               retryReasons=GAPI.SERVICE_NOT_AVAILABLE_RETRY_REASONS,
                               customer=GC.Values[GC.CUSTOMER_ID], query=query, orderBy='email',
                               fields='nextPageToken,users(primaryEmail)',
                               maxResults=GC.Values[GC.USER_MAX_RESULTS])
      except (GAPI.badRequest, GAPI.resourceNotFound, GAPI.forbidden):
        accessErrorExit(cd)
      entitySet |= {user['primaryEmail'] for user in result}
    entityList = sorted(list(entitySet))
  elif entityType in Cmd.DOMAIN_ENTITY_TYPES:
    if entityType == Cmd.ENTITY_DOMAINS and ((isSuspended is not None) or (isArchived is not None)):
      if isSuspended is not None:
        query = f'isSuspended={isSuspended}'
        if isArchived is not None:
          query += f' isArchived={isArchived}'
      else:
        query = f'isArchived={isArchived}'
    else:
      query = Cmd.DOMAINS_QUERY_MAP[entityType]
    cd = buildGAPIObject(API.DIRECTORY)
    domains = convertEntityToList(entity)
    for domain in domains:
      printGettingAllEntityItemsForWhom(Ent.USER, domain, query=query, entityType=Ent.DOMAIN)
      try:
        result = callGAPIpages(cd.users(), 'list', 'users',
                               pageMessage=getPageMessageForWhom(),
                               throwReasons=[GAPI.BAD_REQUEST, GAPI.RESOURCE_NOT_FOUND, GAPI.DOMAIN_NOT_FOUND, GAPI.FORBIDDEN],
                               retryReasons=GAPI.SERVICE_NOT_AVAILABLE_RETRY_REASONS,
                               domain=domain, query=query, orderBy='email',
                               fields='nextPageToken,users(primaryEmail)',
                               maxResults=GC.Values[GC.USER_MAX_RESULTS])
      except (GAPI.badRequest, GAPI.resourceNotFound, GAPI.domainNotFound, GAPI.forbidden):
        checkEntityDNEorAccessErrorExit(cd, Ent.DOMAIN, domain)
        _incrEntityDoesNotExist(Ent.DOMAIN)
        continue
      entityList.extend([user['primaryEmail'] for user in result])
  elif entityType in Cmd.GROUP_ENTITY_TYPES or entityType in Cmd.GROUPS_ENTITY_TYPES:
    isArchived, isSuspended = Cmd.GROUPS_QUERY_MAP.get(entityType, (isArchived, isSuspended))
    includeDerivedMembership = entityType in {Cmd.ENTITY_GROUP_INDE, Cmd.ENTITY_GROUPS_INDE}
    cd = buildGAPIObject(API.DIRECTORY)
    groups = convertEntityToList(entity, nonListEntityType=entityType in Cmd.GROUP_ENTITY_TYPES)
    for group in groups:
      if validateEmailAddressOrUID(group, checkPeople=False):
        group = normalizeEmailAddressOrUID(group)
        printGettingAllEntityItemsForWhom(memberRoles if memberRoles else Ent.ROLE_MANAGER_MEMBER_OWNER, group, entityType=Ent.GROUP)
        validRoles, listRoles, listFields = _getRoleVerification(memberRoles, 'nextPageToken,members(email,id,type,status)')
        try:
          result = callGAPIpages(cd.members(), 'list', 'members',
                                 pageMessage=getPageMessageForWhom(),
                                 throwReasons=GAPI.MEMBERS_THROW_REASONS, retryReasons=GAPI.MEMBERS_RETRY_REASONS,
                                 includeDerivedMembership=includeDerivedMembership,
                                 groupKey=group, roles=listRoles, fields=listFields, maxResults=GC.Values[GC.MEMBER_MAX_RESULTS])
        except (GAPI.groupNotFound, GAPI.domainNotFound, GAPI.domainCannotUseApis, GAPI.invalid, GAPI.forbidden, GAPI.serviceNotAvailable):
          entityUnknownWarning(Ent.GROUP, group)
          _incrEntityDoesNotExist(Ent.GROUP)
          continue
        for member in result:
          email = member['email'].lower() if member['type'] != Ent.TYPE_CUSTOMER else member['id']
          if ((groupMemberType in ('ALL', member['type'])) and
              (not includeDerivedMembership or (member['type'] == Ent.TYPE_USER)) and
              _checkMemberRoleIsSuspendedIsArchived(member, validRoles, isSuspended, isArchived) and
              email not in entitySet):
            entitySet.add(email)
            entityList.append(email)
      else:
        _showInvalidEntity(Ent.GROUP, group)
  elif entityType in Cmd.GROUP_USERS_ENTITY_TYPES:
    isArchived, isSuspended = Cmd.GROUP_USERS_QUERY_MAP.get(entityType, (isArchived, isSuspended))
    cd = buildGAPIObject(API.DIRECTORY)
    groups = convertEntityToList(entity)
    includeDerivedMembership = False
    domains = []
    rolesSet = set()
    if not noCLArgs:
      while Cmd.ArgumentsRemaining():
        myarg = getArgument()
        if myarg in GROUP_ROLES_MAP:
          rolesSet.add(GROUP_ROLES_MAP[myarg])
        elif myarg == 'primarydomain':
          domains.append(GC.Values[GC.DOMAIN])
        elif myarg == 'domains':
          domains.extend(getEntityList(Cmd.OB_DOMAIN_NAME_ENTITY))
        elif myarg == 'recursive':
          recursive = True
          includeDerivedMembership = False
        elif myarg == 'includederivedmembership':
          includeDerivedMembership = True
          recursive = False
        elif entityType == Cmd.ENTITY_GROUP_USERS_SELECT and myarg in SUSPENDED_ARGUMENTS:
          isSuspended = _getIsSuspended(myarg)
        elif entityType == Cmd.ENTITY_GROUP_USERS_SELECT and myarg in ARCHIVED_ARGUMENTS:
          isArchived = _getIsArchived(myarg)
        elif myarg == 'end':
          break
        else:
          Cmd.Backup()
          missingArgumentExit('end')
    if rolesSet:
      memberRoles = ','.join(sorted(rolesSet))
    for group in groups:
      if validateEmailAddressOrUID(group, checkPeople=False):
        _addGroupUsersToUsers(normalizeEmailAddressOrUID(group), domains, recursive, includeDerivedMembership)
      else:
        _showInvalidEntity(Ent.GROUP, group)
  elif entityType in {Cmd.ENTITY_CIGROUP, Cmd.ENTITY_CIGROUPS}:
    ci = buildGAPIObject(API.CLOUDIDENTITY_GROUPS)
    groups = convertEntityToList(entity, nonListEntityType=entityType in {Cmd.ENTITY_CIGROUP})
    for group in groups:
      if validateEmailAddressOrUID(group, checkPeople=False, ciGroupsAPI=True):
        _, name, groupEmail = convertGroupEmailToCloudID(ci, group)
        printGettingAllEntityItemsForWhom(memberRoles if memberRoles else Ent.ROLE_MANAGER_MEMBER_OWNER, groupEmail, entityType=Ent.CLOUD_IDENTITY_GROUP)
        validRoles = _getCIRoleVerification(memberRoles)
        try:
          result = callGAPIpages(ci.groups().memberships(), 'list', 'memberships',
                                 pageMessage=getPageMessageForWhom(),
                                 throwReasons=GAPI.CIGROUP_LIST_THROW_REASONS, retryReasons=GAPI.CIGROUP_RETRY_REASONS,
                                 parent=name, view='FULL',
                                 fields='nextPageToken,memberships(preferredMemberKey(id),roles(name),type)',
                                 pageSize=GC.Values[GC.MEMBER_MAX_RESULTS])
        except (GAPI.resourceNotFound, GAPI.domainNotFound, GAPI.domainCannotUseApis,
                GAPI.forbidden, GAPI.badRequest, GAPI.invalid, GAPI.invalidArgument,
                GAPI.systemError, GAPI.permissionDenied, GAPI.serviceNotAvailable):
          entityUnknownWarning(Ent.CLOUD_IDENTITY_GROUP, groupEmail)
          _incrEntityDoesNotExist(Ent.CLOUD_IDENTITY_GROUP)
          continue
        for member in result:
          getCIGroupMemberRoleFixType(member)
          email = member.get('preferredMemberKey', {}).get('id', '')
          if (email and (groupMemberType in ('ALL', member['type'])) and
              _checkMemberRole(member, validRoles) and email not in entitySet):
            entitySet.add(email)
            entityList.append(email)
      else:
        _showInvalidEntity(Ent.CLOUD_IDENTITY_GROUP, groupEmail)
  elif entityType in {Cmd.ENTITY_CIGROUP_USERS}:
    ci = buildGAPIObject(API.CLOUDIDENTITY_GROUPS)
    groups = convertEntityToList(entity)
    rolesSet = set()
    if not noCLArgs:
      while Cmd.ArgumentsRemaining():
        myarg = getArgument()
        if myarg in GROUP_ROLES_MAP:
          rolesSet.add(GROUP_ROLES_MAP[myarg])
        elif myarg == 'recursive':
          recursive = True
        elif myarg == 'end':
          break
        else:
          Cmd.Backup()
          missingArgumentExit('end')
    if rolesSet:
      memberRoles = ','.join(sorted(rolesSet))
    for group in groups:
      _, name, groupEmail = convertGroupEmailToCloudID(ci, group)
      if name and groupEmail:
        _addCIGroupUsersToUsers(name, groupEmail, recursive)
      else:
        _showInvalidEntity(Ent.GROUP, group)
  elif entityType in Cmd.OU_ENTITY_TYPES or entityType in Cmd.OUS_ENTITY_TYPES:
    isArchived, isSuspended = Cmd.OU_QUERY_MAP.get(entityType, (isArchived, isSuspended))
    cd = buildGAPIObject(API.DIRECTORY)
    ous = convertEntityToList(entity, shlexSplit=True, nonListEntityType=entityType in Cmd.OU_ENTITY_TYPES)
    directlyInOU = entityType in Cmd.OU_DIRECT_ENTITY_TYPES
    qualifier = Msg.DIRECTLY_IN_THE.format(Ent.Singular(Ent.ORGANIZATIONAL_UNIT)) if directlyInOU else Msg.IN_THE.format(Ent.Singular(Ent.ORGANIZATIONAL_UNIT))
    fields = 'nextPageToken,users(primaryEmail,orgUnitPath)' if directlyInOU else 'nextPageToken,users(primaryEmail)'
    for ou in ous:
      if ou == 'root':
        ou = '/'
      ou = makeOrgUnitPathAbsolute(ou)
      if ou.startswith('id:'):
        try:
          ou = callGAPI(cd.orgunits(), 'get',
                        throwReasons=GAPI.ORGUNIT_GET_THROW_REASONS,
                        customerId=GC.Values[GC.CUSTOMER_ID],
                        orgUnitPath=ou, fields='orgUnitPath')['orgUnitPath']
        except (GAPI.invalidOrgunit, GAPI.orgunitNotFound, GAPI.backendError, GAPI.badRequest,
                GAPI.invalidCustomerId, GAPI.loginRequired):
          checkEntityDNEorAccessErrorExit(cd, Ent.ORGANIZATIONAL_UNIT, ou)
          _incrEntityDoesNotExist(Ent.ORGANIZATIONAL_UNIT)
          continue
      ouLower = ou.lower()
      printGettingAllEntityItemsForWhom(Ent.USER, ou, qualifier=Msg.IN_THE.format(Ent.Singular(Ent.ORGANIZATIONAL_UNIT)),
                                        entityType=Ent.ORGANIZATIONAL_UNIT)
      pageMessage = getPageMessageForWhom()
      usersInOU = 0
      try:
        feed = yieldGAPIpages(cd.users(), 'list', 'users',
                              pageMessage=pageMessage, messageAttribute='primaryEmail',
                              throwReasons=[GAPI.INVALID_ORGUNIT, GAPI.ORGUNIT_NOT_FOUND,
                                            GAPI.INVALID_INPUT, GAPI.BAD_REQUEST, GAPI.RESOURCE_NOT_FOUND, GAPI.FORBIDDEN],
                              retryReasons=GAPI.SERVICE_NOT_AVAILABLE_RETRY_REASONS,
                              customer=GC.Values[GC.CUSTOMER_ID], query=orgUnitPathQuery(ou, isSuspended, isArchived), orderBy='email',
                              fields=fields, maxResults=GC.Values[GC.USER_MAX_RESULTS])
        for users in feed:
          if directlyInOU:
            for user in users:
              if ouLower == user.get('orgUnitPath', '').lower():
                usersInOU += 1
                entityList.append(user['primaryEmail'])
          else:
            entityList.extend([user['primaryEmail'] for user in users])
            usersInOU += len(users)
        setGettingAllEntityItemsForWhom(Ent.USER, ou, qualifier=qualifier)
        printGotEntityItemsForWhom(usersInOU)
      except (GAPI.invalidInput, GAPI.invalidOrgunit, GAPI.orgunitNotFound, GAPI.backendError, GAPI.badRequest,
              GAPI.invalidCustomerId, GAPI.loginRequired, GAPI.resourceNotFound, GAPI.forbidden):
        checkEntityDNEorAccessErrorExit(cd, Ent.ORGANIZATIONAL_UNIT, ou)
        _incrEntityDoesNotExist(Ent.ORGANIZATIONAL_UNIT)
  elif entityType in {Cmd.ENTITY_QUERY, Cmd.ENTITY_QUERIES}:
    cd = buildGAPIObject(API.DIRECTORY)
    queries = convertEntityToList(entity, shlexSplit=True, nonListEntityType=entityType == Cmd.ENTITY_QUERY)
    for query in queries:
      printGettingAllAccountEntities(Ent.USER, query)
      try:
        result = callGAPIpages(cd.users(), 'list', 'users',
                               pageMessage=getPageMessage(),
                               throwReasons=[GAPI.INVALID_ORGUNIT, GAPI.ORGUNIT_NOT_FOUND,
                                             GAPI.INVALID_INPUT, GAPI.BAD_REQUEST, GAPI.RESOURCE_NOT_FOUND, GAPI.FORBIDDEN],
                               retryReasons=GAPI.SERVICE_NOT_AVAILABLE_RETRY_REASONS,
                               customer=GC.Values[GC.CUSTOMER_ID], query=query, orderBy='email',
                               fields='nextPageToken,users(primaryEmail,suspended,archived)',
                               maxResults=GC.Values[GC.USER_MAX_RESULTS])
      except (GAPI.invalidOrgunit, GAPI.orgunitNotFound, GAPI.invalidInput):
        Cmd.Backup()
        usageErrorExit(Msg.INVALID_QUERY)
      except (GAPI.badRequest, GAPI.resourceNotFound, GAPI.forbidden):
        accessErrorExit(cd)
      for user in result:
        email = user['primaryEmail']
        if ((isSuspended is None or isSuspended == user['suspended']) and
            (isArchived is None or isArchived == user['archived']) and
            email not in entitySet):
          entitySet.add(email)
          entityList.append(email)
  elif entityType == Cmd.ENTITY_LICENSES:
    skusList = []
    for item in entity.split(','):
      productId, sku = SKU.getProductAndSKU(item)
      if not productId:
        _incrEntityDoesNotExist(Ent.SKU)
      elif (productId, sku) not in skusList:
        skusList.append((productId, sku))
    if skusList:
      entityList = doPrintLicenses(returnFields=['userId'], skus=skusList)
  elif entityType in {Cmd.ENTITY_COURSEPARTICIPANTS, Cmd.ENTITY_TEACHERS, Cmd.ENTITY_STUDENTS}:
    croom = buildGAPIObject(API.CLASSROOM)
    if not noListConversion:
      courseIdList = convertEntityToList(entity)
    else:
      courseIdList = [entity]
    _, _, coursesInfo = _getCoursesOwnerInfo(croom, courseIdList, GC.Values[GC.USE_COURSE_OWNER_ACCESS])
    for courseId, courseInfo in coursesInfo.items():
      try:
        if entityType in {Cmd.ENTITY_COURSEPARTICIPANTS, Cmd.ENTITY_TEACHERS}:
          printGettingAllEntityItemsForWhom(Ent.TEACHER, removeCourseIdScope(courseId), entityType=Ent.COURSE)
          result = callGAPIpages(courseInfo['croom'].courses().teachers(), 'list', 'teachers',
                                 pageMessage=getPageMessageForWhom(),
                                 throwReasons=[GAPI.NOT_FOUND, GAPI.BAD_REQUEST, GAPI.SERVICE_NOT_AVAILABLE,
                                               GAPI.FORBIDDEN, GAPI.PERMISSION_DENIED],
                                 retryReasons=GAPI.SERVICE_NOT_AVAILABLE_RETRY_REASONS,
                                 courseId=courseId, fields='nextPageToken,teachers/profile/emailAddress',
                                 pageSize=GC.Values[GC.CLASSROOM_MAX_RESULTS])
          for teacher in result:
            email = teacher['profile'].get('emailAddress', None)
            if email and (email not in entitySet):
              entitySet.add(email)
              entityList.append(email)
        if entityType in {Cmd.ENTITY_COURSEPARTICIPANTS, Cmd.ENTITY_STUDENTS}:
          printGettingAllEntityItemsForWhom(Ent.STUDENT, removeCourseIdScope(courseId), entityType=Ent.COURSE)
          result = callGAPIpages(courseInfo['croom'].courses().students(), 'list', 'students',
                                 pageMessage=getPageMessageForWhom(),
                                 throwReasons=[GAPI.NOT_FOUND, GAPI.BAD_REQUEST, GAPI.SERVICE_NOT_AVAILABLE,
                                               GAPI.FORBIDDEN, GAPI.PERMISSION_DENIED],
                                 retryReasons=GAPI.SERVICE_NOT_AVAILABLE_RETRY_REASONS,
                                 courseId=courseId, fields='nextPageToken,students/profile/emailAddress',
                                 pageSize=GC.Values[GC.CLASSROOM_MAX_RESULTS])
          for student in result:
            email = student['profile'].get('emailAddress', None)
            if email and (email not in entitySet):
              entitySet.add(email)
              entityList.append(email)
      except GAPI.notFound:
        entityDoesNotExistWarning(Ent.COURSE, removeCourseIdScope(courseId))
        _incrEntityDoesNotExist(Ent.COURSE)
      except GAPI.serviceNotAvailable as e:
        entityActionNotPerformedWarning([Ent.COURSE, removeCourseIdScope(courseId)], str(e))
        GM.Globals[GM.CLASSROOM_SERVICE_NOT_AVAILABLE] = True
        break
      except (GAPI.forbidden, GAPI.permissionDenied, GAPI.badRequest) as e:
        ClientAPIAccessDeniedExit(str(e))
  elif entityType == Cmd.ENTITY_CROS:
    buildGAPIObject(API.DIRECTORY)
    for deviceId in convertEntityToList(entity):
      if deviceId not in entitySet:
        entitySet.add(deviceId)
        entityList.append(deviceId)
  elif entityType == Cmd.ENTITY_ALL_CROS:
    cd = buildGAPIObject(API.DIRECTORY)
    printGettingAllAccountEntities(Ent.CROS_DEVICE)
    try:
      result = callGAPIpages(cd.chromeosdevices(), 'list', 'chromeosdevices',
                             pageMessage=getPageMessage(),
                             throwReasons=[GAPI.INVALID_INPUT, GAPI.BAD_REQUEST, GAPI.RESOURCE_NOT_FOUND, GAPI.FORBIDDEN],
                             retryReasons=GAPI.SERVICE_NOT_AVAILABLE_RETRY_REASONS,
                             customerId=GC.Values[GC.CUSTOMER_ID],
                             fields='nextPageToken,chromeosdevices(deviceId)',
                             maxResults=GC.Values[GC.DEVICE_MAX_RESULTS])
    except (GAPI.invalidInput, GAPI.badRequest, GAPI.resourceNotFound, GAPI.forbidden):
      accessErrorExit(cd)
    entityList = [device['deviceId'] for device in result]
  elif entityType in {Cmd.ENTITY_CROS_QUERY, Cmd.ENTITY_CROS_QUERIES, Cmd.ENTITY_CROS_SN}:
    cd = buildGAPIObject(API.DIRECTORY)
    queries = convertEntityToList(entity, shlexSplit=entityType == Cmd.ENTITY_CROS_QUERIES,
                                  nonListEntityType=entityType == Cmd.ENTITY_CROS_QUERY)
    if entityType == Cmd.ENTITY_CROS_SN:
      queries = [f'id:{query}' for query in queries]
    for query in queries:
      _validateDeviceQuery(Ent.CROS_DEVICE, query)
      printGettingAllAccountEntities(Ent.CROS_DEVICE, query)
      try:
        result = callGAPIpages(cd.chromeosdevices(), 'list', 'chromeosdevices',
                               pageMessage=getPageMessage(),
                               throwReasons=[GAPI.INVALID_INPUT, GAPI.BAD_REQUEST, GAPI.RESOURCE_NOT_FOUND, GAPI.FORBIDDEN],
                               retryReasons=GAPI.SERVICE_NOT_AVAILABLE_RETRY_REASONS,
                               customerId=GC.Values[GC.CUSTOMER_ID], query=query,
                               fields='nextPageToken,chromeosdevices(deviceId)',
                               maxResults=GC.Values[GC.DEVICE_MAX_RESULTS])
      except GAPI.invalidInput:
        Cmd.Backup()
        usageErrorExit(Msg.INVALID_QUERY)
      except (GAPI.badRequest, GAPI.resourceNotFound, GAPI.forbidden):
        accessErrorExit(cd)
      for device in result:
        deviceId = device['deviceId']
        if deviceId not in entitySet:
          entitySet.add(deviceId)
          entityList.append(deviceId)
  elif entityType in Cmd.CROS_OU_ENTITY_TYPES or entityType in Cmd.CROS_OUS_ENTITY_TYPES:
    cd = buildGAPIObject(API.DIRECTORY)
    ous = convertEntityToList(entity, shlexSplit=True, nonListEntityType=entityType in Cmd.CROS_OU_ENTITY_TYPES)
    numOus = len(ous)
    includeChildOrgunits = entityType in Cmd.CROS_OU_CHILDREN_ENTITY_TYPES
    allQualifier = Msg.DIRECTLY_IN_THE.format(Ent.Choose(Ent.ORGANIZATIONAL_UNIT, numOus)) if not includeChildOrgunits else Msg.IN_THE.format(Ent.Choose(Ent.ORGANIZATIONAL_UNIT, numOus))
    if entityType in Cmd.CROS_OU_QUERY_ENTITY_TYPES:
      queries = getDeviceQueries('query', Ent.CROS_DEVICE)
    elif entityType in Cmd.CROS_OU_QUERIES_ENTITY_TYPES:
      queries = getDeviceQueries('queries', Ent.CROS_DEVICE)
    else:
      queries = [None]
    for ou in ous:
      if ou == 'root':
        ou = '/'
      ou = makeOrgUnitPathAbsolute(ou)
      oneQualifier = Msg.DIRECTLY_IN_THE.format(Ent.Singular(Ent.ORGANIZATIONAL_UNIT)) if not includeChildOrgunits else Msg.IN_THE.format(Ent.Singular(Ent.ORGANIZATIONAL_UNIT))
      for query in queries:
        printGettingAllEntityItemsForWhom(Ent.CROS_DEVICE, ou,
                                          query=query, qualifier=oneQualifier, entityType=Ent.ORGANIZATIONAL_UNIT)
        try:
          result = callGAPIpages(cd.chromeosdevices(), 'list', 'chromeosdevices',
                                 pageMessage=getPageMessageForWhom(),
                                 throwReasons=[GAPI.INVALID_INPUT, GAPI.INVALID_ORGUNIT, GAPI.ORGUNIT_NOT_FOUND,
                                               GAPI.BAD_REQUEST, GAPI.RESOURCE_NOT_FOUND, GAPI.FORBIDDEN],
                                 retryReasons=GAPI.SERVICE_NOT_AVAILABLE_RETRY_REASONS,
                                 customerId=GC.Values[GC.CUSTOMER_ID], query=query,
                                 orgUnitPath=ou, includeChildOrgunits=includeChildOrgunits,
                                 fields='nextPageToken,chromeosdevices(deviceId)', maxResults=GC.Values[GC.DEVICE_MAX_RESULTS])
        except GAPI.invalidInput:
          Cmd.Backup()
          usageErrorExit(Msg.INVALID_QUERY)
        except (GAPI.invalidOrgunit, GAPI.orgunitNotFound, GAPI.badRequest, GAPI.resourceNotFound, GAPI.forbidden):
          checkEntityDNEorAccessErrorExit(cd, Ent.ORGANIZATIONAL_UNIT, ou)
          _incrEntityDoesNotExist(Ent.ORGANIZATIONAL_UNIT)
          continue
        if query is None:
          entityList.extend([device['deviceId'] for device in result])
        else:
          for device in result:
            deviceId = device['deviceId']
            if deviceId not in entitySet:
              entitySet.add(deviceId)
              entityList.append(deviceId)
    Ent.SetGettingQualifier(Ent.CROS_DEVICE, allQualifier)
    Ent.SetGettingForWhom(','.join(ous))
    printGotEntityItemsForWhom(len(entityList))
  elif entityType == Cmd.ENTITY_BROWSER:
    result = convertEntityToList(entity)
    for deviceId in result:
      if deviceId not in entitySet:
        entitySet.add(deviceId)
        entityList.append(deviceId)
  elif entityType in {Cmd.ENTITY_BROWSER_OU, Cmd.ENTITY_BROWSER_OUS}:
    cbcm = buildGAPIObject(API.CBCM)
    customerId = _getCustomerIdNoC()
    ous = convertEntityToList(entity, shlexSplit=True, nonListEntityType=entityType == Cmd.ENTITY_BROWSER_OU)
    numOus = len(ous)
    allQualifier = Msg.DIRECTLY_IN_THE.format(Ent.Choose(Ent.ORGANIZATIONAL_UNIT, numOus))
    oneQualifier = Msg.DIRECTLY_IN_THE.format(Ent.Singular(Ent.ORGANIZATIONAL_UNIT))
    for ou in ous:
      ou = makeOrgUnitPathAbsolute(ou)
      printGettingAllEntityItemsForWhom(Ent.CHROME_BROWSER, ou, qualifier=oneQualifier, entityType=Ent.ORGANIZATIONAL_UNIT)
      try:
        result = callGAPIpages(cbcm.chromebrowsers(), 'list', 'browsers',
                               pageMessage=getPageMessageForWhom(),
                               throwReasons=[GAPI.BAD_REQUEST, GAPI.INVALID_ORGUNIT, GAPI.FORBIDDEN],
                               retryReasons=GAPI.SERVICE_NOT_AVAILABLE_RETRY_REASONS,
                               customer=customerId, orgUnitPath=ou, projection='BASIC',
                               orderBy='id', sortOrder='ASCENDING', fields='nextPageToken,browsers(deviceId)')
      except (GAPI.badRequest, GAPI.invalidOrgunit, GAPI.forbidden):
        checkEntityDNEorAccessErrorExit(None, Ent.ORGANIZATIONAL_UNIT, ou)
        _incrEntityDoesNotExist(Ent.ORGANIZATIONAL_UNIT)
        continue
      entityList.extend([browser['deviceId'] for browser in result])
    Ent.SetGettingQualifier(Ent.CHROME_BROWSER, allQualifier)
    Ent.SetGettingForWhom(','.join(ous))
    printGotEntityItemsForWhom(len(entityList))
  elif entityType in {Cmd.ENTITY_BROWSER_QUERY, Cmd.ENTITY_BROWSER_QUERIES}:
    cbcm = buildGAPIObject(API.CBCM)
    customerId = _getCustomerIdNoC()
    queries = convertEntityToList(entity, shlexSplit=entityType == Cmd.ENTITY_BROWSER_QUERIES,
                                  nonListEntityType=entityType == Cmd.ENTITY_BROWSER_QUERY)
    for query in queries:
      printGettingAllAccountEntities(Ent.CHROME_BROWSER, query)
      try:
        result = callGAPIpages(cbcm.chromebrowsers(), 'list', 'browsers',
                               pageMessage=getPageMessage(),
                               throwReasons=[GAPI.INVALID_INPUT, GAPI.BAD_REQUEST, GAPI.RESOURCE_NOT_FOUND, GAPI.FORBIDDEN],
                               retryReasons=GAPI.SERVICE_NOT_AVAILABLE_RETRY_REASONS,
                               customer=customerId, query=query, projection='BASIC',
                               orderBy='id', sortOrder='ASCENDING', fields='nextPageToken,browsers(deviceId)')
      except GAPI.invalidInput:
        Cmd.Backup()
        usageErrorExit(Msg.INVALID_QUERY)
      except (GAPI.badRequest, GAPI.resourceNotFound, GAPI.forbidden) as e:
        accessErrorExitNonDirectory(API.CBCM, str(e))
      for device in result:
        deviceId = device['deviceId']
        if deviceId not in entitySet:
          entitySet.add(deviceId)
          entityList.append(deviceId)
  else:
    systemErrorExit(UNKNOWN_ERROR_RC, 'getItemsToModify coding error')
  for errorType in [ENTITY_ERROR_DNE, ENTITY_ERROR_INVALID]:
    if entityError[errorType] > 0:
      Cmd.SetLocation(entityLocation-1)
      writeStderr(Cmd.CommandLineWithBadArgumentMarked(False))
      count = entityError[errorType]
      if errorType == ENTITY_ERROR_DNE:
        stderrErrorMsg(Msg.BAD_ENTITIES_IN_SOURCE.format(count, Ent.Choose(entityError['entityType'], count),
                                                         Msg.DO_NOT_EXIST if count != 1 else Msg.DOES_NOT_EXIST))
        sys.exit(ENTITY_DOES_NOT_EXIST_RC)
      else:
        stderrErrorMsg(Msg.BAD_ENTITIES_IN_SOURCE.format(count, Msg.INVALID, Ent.Choose(entityError['entityType'], count)))
        sys.exit(INVALID_ENTITY_RC)
  return entityList

def splitEntityList(entity, dataDelimiter):
  if not entity:
    return []
  if not dataDelimiter:
    return [entity]
  return entity.split(dataDelimiter)

def splitEntityListShlex(entity, dataDelimiter):
  if not entity:
    return (True, [])
  if not dataDelimiter:
    return (True, [entity])
  return shlexSplitListStatus(entity, dataDelimiter)

def fileDataErrorExit(filename, row, itemName, value, errMessage):
  if itemName:
    systemErrorExit(DATA_ERROR_RC,
                    formatKeyValueList('',
                                       [Ent.Singular(Ent.FILE), filename,
                                        Ent.Singular(Ent.ROW), row,
                                        Ent.Singular(Ent.ITEM), itemName,
                                        Ent.Singular(Ent.VALUE), value,
                                        errMessage],
                                       ''))
  else:
    systemErrorExit(DATA_ERROR_RC,
                    formatKeyValueList('',
                                       [Ent.Singular(Ent.FILE), filename,
                                        Ent.Singular(Ent.ROW), row,
                                        Ent.Singular(Ent.VALUE), value,
                                        errMessage],
                                       ''))

# <FileSelector>
def getEntitiesFromFile(shlexSplit, returnSet=False):
  filename = getString(Cmd.OB_FILE_NAME)
  filenameLower = filename.lower()
  if filenameLower not in {'gcsv', 'gdoc', 'gcscsv', 'gcsdoc'}:
    encoding = getCharSet()
    filename = setFilePath(filename, GC.INPUT_DIR)
    f = openFile(filename, encoding=encoding, stripUTFBOM=True)
  elif filenameLower in {'gcsv', 'gdoc'}:
    f = getGDocData(filenameLower)
    getCharSet()
  else: #filenameLower in {'gcscsv', 'gcsdoc'}:
    f = getStorageFileData(filenameLower)
    getCharSet()
  dataDelimiter = getDelimiter()
  entitySet = set()
  entityList = []
  i = 0
  for row in f:
    i += 1
    if shlexSplit:
      splitStatus, itemList = splitEntityListShlex(row.strip(), dataDelimiter)
      if not splitStatus:
        fileDataErrorExit(filename, i, None, row.strip(), f'{Msg.INVALID_LIST}: {itemList}')
    else:
      itemList = splitEntityList(row.strip(), dataDelimiter)
    for item in itemList:
      item = item.strip()
      if item and (item not in entitySet):
        entitySet.add(item)
        entityList.append(item)
  closeFile(f)
  return entityList if not returnSet else entitySet

# <CSVFileSelector>
def getEntitiesFromCSVFile(shlexSplit, returnSet=False):
  fileFieldName = getString(Cmd.OB_FILE_NAME_FIELD_NAME)
  if platform.system() == 'Windows' and not fileFieldName.startswith('-:'):
    drive, fileFieldName = os.path.splitdrive(fileFieldName)
  else:
    drive = ''
  if fileFieldName.find(':') == -1:
    Cmd.Backup()
    invalidArgumentExit(Cmd.OB_FILE_NAME_FIELD_NAME)
  fileFieldNameList = fileFieldName.split(':')
  filename = drive+fileFieldNameList[0]
  f, csvFile, fieldnames = openCSVFileReader(filename)
  for fieldName in fileFieldNameList[1:]:
    if fieldName not in fieldnames:
      csvFieldErrorExit(fieldName, fieldnames, backupArg=True, checkForCharset=True)
  matchFields, skipFields = getMatchSkipFields(fieldnames)
  dataDelimiter = getDelimiter()
  entitySet = set()
  entityList = []
  i = 1
  for row in csvFile:
    i += 1
    if checkMatchSkipFields(row, None, matchFields, skipFields):
      for fieldName in fileFieldNameList[1:]:
        if shlexSplit:
          splitStatus, itemList = splitEntityListShlex(row[fieldName].strip(), dataDelimiter)
          if not splitStatus:
            fileDataErrorExit(filename, i, fieldName, row[fieldName].strip(), f'{Msg.INVALID_LIST}: {itemList}')
        else:
          itemList = splitEntityList(row[fieldName].strip(), dataDelimiter)
        for item in itemList:
          item = item.strip()
          if item and (item not in entitySet):
            entitySet.add(item)
            entityList.append(item)
  closeFile(f)
  return entityList if not returnSet else entitySet

# <CSVFileSelector>
#	keyfield <FieldName> [keypattern <RESearchPattern>] [keyvalue <RESubstitution>] [delimiter <Character>]
#	subkeyfield <FieldName> [keypattern <RESearchPattern>] [keyvalue <RESubstitution>] [delimiter <Character>]
#	(matchfield|skipfield <FieldName> <RESearchPattern>)*
#	[datafield <FieldName>(:<FieldName>)* [delimiter <Character>]]
def getEntitiesFromCSVbyField():

  def getKeyFieldInfo(keyword, required, globalKeyField):
    if not checkArgumentPresent(keyword, required=required):
      GM.Globals[globalKeyField] = None
      return (None, None, None, None)
    keyField = GM.Globals[globalKeyField] = getString(Cmd.OB_FIELD_NAME)
    if keyField not in fieldnames:
      csvFieldErrorExit(keyField, fieldnames, backupArg=True)
    if checkArgumentPresent('keypattern'):
      keyPattern = getREPattern()
    else:
      keyPattern = None
    if checkArgumentPresent('keyvalue'):
      keyValue = getString(Cmd.OB_STRING)
    else:
      keyValue = keyField
    keyDelimiter = getDelimiter()
    return (keyField, keyPattern, keyValue, keyDelimiter)

  def getKeyList(row, keyField, keyPattern, keyValue, keyDelimiter, matchFields, skipFields):
    item = row[keyField].strip()
    if not item:
      return []
    if not checkMatchSkipFields(row, None, matchFields, skipFields):
      return []
    if keyPattern:
      keyList = [keyPattern.sub(keyValue, keyItem.strip()) for keyItem in splitEntityList(item, keyDelimiter)]
    else:
      keyList = [re.sub(keyField, keyItem.strip(), keyValue) for keyItem in splitEntityList(item, keyDelimiter)]
    return [key for key in keyList if key]

  filename = getString(Cmd.OB_FILE_NAME)
  f, csvFile, fieldnames = openCSVFileReader(filename)
  mainKeyField, mainKeyPattern, mainKeyValue, mainKeyDelimiter = getKeyFieldInfo('keyfield', True, GM.CSV_KEY_FIELD)
  subKeyField, subKeyPattern, subKeyValue, subKeyDelimiter = getKeyFieldInfo('subkeyfield', False, GM.CSV_SUBKEY_FIELD)
  matchFields, skipFields = getMatchSkipFields(fieldnames)
  if checkArgumentPresent('datafield'):
    if GM.Globals[GM.CSV_DATA_DICT]:
      csvDataAlreadySavedErrorExit()
    GM.Globals[GM.CSV_DATA_FIELD] = getString(Cmd.OB_FIELD_NAME, checkBlank=True)
    dataFields = GM.Globals[GM.CSV_DATA_FIELD].split(':')
    for dataField in dataFields:
      if dataField not in fieldnames:
        csvFieldErrorExit(dataField, fieldnames, backupArg=True)
    dataDelimiter = getDelimiter()
  else:
    GM.Globals[GM.CSV_DATA_FIELD] = None
    dataFields = []
    dataDelimiter = None
  entitySet = set()
  entityList = []
  csvDataKeys = {}
  GM.Globals[GM.CSV_DATA_DICT] = {}
  if not subKeyField:
    for row in csvFile:
      mainKeyList = getKeyList(row, mainKeyField, mainKeyPattern, mainKeyValue, mainKeyDelimiter, matchFields, skipFields)
      if not mainKeyList:
        continue
      for mainKey in mainKeyList:
        if mainKey not in entitySet:
          entitySet.add(mainKey)
          entityList.append(mainKey)
          if GM.Globals[GM.CSV_DATA_FIELD]:
            csvDataKeys[mainKey] = set()
            GM.Globals[GM.CSV_DATA_DICT][mainKey] = []
      for dataField in dataFields:
        if dataField in row:
          dataList = splitEntityList(row[dataField].strip(), dataDelimiter)
          for dataValue in dataList:
            dataValue = dataValue.strip()
            if not dataValue:
              continue
            for mainKey in mainKeyList:
              if dataValue not in csvDataKeys[mainKey]:
                csvDataKeys[mainKey].add(dataValue)
                GM.Globals[GM.CSV_DATA_DICT][mainKey].append(dataValue)
  else:
    csvSubKeys = {}
    for row in csvFile:
      mainKeyList = getKeyList(row, mainKeyField, mainKeyPattern, mainKeyValue, mainKeyDelimiter, matchFields, skipFields)
      if not mainKeyList:
        continue
      for mainKey in mainKeyList:
        if mainKey not in entitySet:
          entitySet.add(mainKey)
          entityList.append(mainKey)
          csvSubKeys[mainKey] = set()
          csvDataKeys[mainKey] = {}
          GM.Globals[GM.CSV_DATA_DICT][mainKey] = {}
      subKeyList = getKeyList(row, subKeyField, subKeyPattern, subKeyValue, subKeyDelimiter, {}, {})
      if not subKeyList:
        continue
      for mainKey in mainKeyList:
        for subKey in subKeyList:
          if subKey not in csvSubKeys[mainKey]:
            csvSubKeys[mainKey].add(subKey)
            if GM.Globals[GM.CSV_DATA_FIELD]:
              csvDataKeys[mainKey][subKey] = set()
              GM.Globals[GM.CSV_DATA_DICT][mainKey][subKey] = []
      for dataField in dataFields:
        if dataField in row:
          dataList = splitEntityList(row[dataField].strip(), dataDelimiter)
          for dataValue in dataList:
            dataValue = dataValue.strip()
            if not dataValue:
              continue
            for mainKey in mainKeyList:
              for subKey in subKeyList:
                if dataValue not in csvDataKeys[mainKey][subKey]:
                  csvDataKeys[mainKey][subKey].add(dataValue)
                  GM.Globals[GM.CSV_DATA_DICT][mainKey][subKey].append(dataValue)
  closeFile(f)
  return entityList

# Typically used to map courseparticipants to students or teachers
def mapEntityType(entityType, typeMap):
  if (typeMap is not None) and (entityType in typeMap):
    return typeMap[entityType]
  return entityType

def getEntityArgument(entityList):
  if entityList is None:
    return (0, 0, entityList)
  if isinstance(entityList, dict):
    clLoc = Cmd.Location()
    Cmd.SetLocation(GM.Globals[GM.ENTITY_CL_DELAY_START])
    entityList = getItemsToModify(**entityList)
    Cmd.SetLocation(clLoc)
  return (0, len(entityList), entityList)

def getEntityToModify(defaultEntityType=None, browserAllowed=False, crosAllowed=False, userAllowed=True,
                      typeMap=None, isSuspended=None, isArchived=None, groupMemberType='USER', delayGet=False):
  if GC.Values[GC.USER_SERVICE_ACCOUNT_ACCESS_ONLY]:
    crosAllowed = False
    selectorChoices = Cmd.SERVICE_ACCOUNT_ONLY_ENTITY_SELECTORS[:]
  else:
    selectorChoices = Cmd.BASE_ENTITY_SELECTORS[:]
  if userAllowed:
    selectorChoices += Cmd.USER_ENTITY_SELECTORS+Cmd.USER_CSVDATA_ENTITY_SELECTORS
  if crosAllowed:
    selectorChoices += Cmd.CROS_ENTITY_SELECTORS+Cmd.CROS_CSVDATA_ENTITY_SELECTORS
  if browserAllowed:
    selectorChoices = Cmd.BROWSER_ENTITY_SELECTORS
  entitySelector = getChoice(selectorChoices, defaultChoice=None)
  if entitySelector:
    choices = []
    if entitySelector == Cmd.ENTITY_SELECTOR_ALL:
      if userAllowed:
        choices += Cmd.USER_ENTITY_SELECTOR_ALL_SUBTYPES
      if crosAllowed:
        choices += Cmd.CROS_ENTITY_SELECTOR_ALL_SUBTYPES
      entityType = Cmd.ENTITY_SELECTOR_ALL_SUBTYPES_MAP[getChoice(choices)]
      if not delayGet:
        return (Cmd.ENTITY_USERS if entityType != Cmd.ENTITY_ALL_CROS else Cmd.ENTITY_CROS,
                getItemsToModify(entityType, None))
      GM.Globals[GM.ENTITY_CL_DELAY_START] = Cmd.Location()
      buildGAPIObject(API.DIRECTORY)
      return (Cmd.ENTITY_USERS if entityType != Cmd.ENTITY_ALL_CROS else Cmd.ENTITY_CROS,
              {'entityType': entityType, 'entity': None})
    if userAllowed:
      if entitySelector == Cmd.ENTITY_SELECTOR_FILE:
        return (Cmd.ENTITY_USERS, getItemsToModify(Cmd.ENTITY_USERS, getEntitiesFromFile(False)))
      if entitySelector in [Cmd.ENTITY_SELECTOR_CSV, Cmd.ENTITY_SELECTOR_CSVFILE]:
        return (Cmd.ENTITY_USERS, getItemsToModify(Cmd.ENTITY_USERS, getEntitiesFromCSVFile(False)))
    if crosAllowed:
      if entitySelector == Cmd.ENTITY_SELECTOR_CROSFILE:
        return (Cmd.ENTITY_CROS, getEntitiesFromFile(False))
      if entitySelector in [Cmd.ENTITY_SELECTOR_CROSCSV, Cmd.ENTITY_SELECTOR_CROSCSVFILE]:
        return (Cmd.ENTITY_CROS, getEntitiesFromCSVFile(False))
      if entitySelector == Cmd.ENTITY_SELECTOR_CROSFILE_SN:
        return (Cmd.ENTITY_CROS, getItemsToModify(Cmd.ENTITY_CROS_SN, getEntitiesFromFile(False)))
      if entitySelector in [Cmd.ENTITY_SELECTOR_CROSCSV_SN, Cmd.ENTITY_SELECTOR_CROSCSVFILE_SN]:
        return (Cmd.ENTITY_CROS, getItemsToModify(Cmd.ENTITY_CROS_SN, getEntitiesFromCSVFile(False)))
    if browserAllowed:
      if entitySelector == Cmd.ENTITY_SELECTOR_FILE:
        return (Cmd.ENTITY_BROWSER, getEntitiesFromFile(False))
      if entitySelector in [Cmd.ENTITY_SELECTOR_CSV, Cmd.ENTITY_SELECTOR_CSVFILE]:
        return (Cmd.ENTITY_BROWSER, getEntitiesFromCSVFile(False))
    if entitySelector == Cmd.ENTITY_SELECTOR_DATAFILE:
      if userAllowed:
        choices += Cmd.USER_ENTITY_SELECTOR_DATAFILE_CSVKMD_SUBTYPES if not GC.Values[GC.USER_SERVICE_ACCOUNT_ACCESS_ONLY] else [Cmd.ENTITY_USERS]
      if crosAllowed:
        choices += Cmd.CROS_ENTITY_SELECTOR_DATAFILE_CSVKMD_SUBTYPES
      entityType = mapEntityType(getChoice(choices), typeMap)
      return (Cmd.ENTITY_USERS if entityType not in Cmd.CROS_ENTITY_SELECTOR_DATAFILE_CSVKMD_SUBTYPES else Cmd.ENTITY_CROS,
              getItemsToModify(entityType, getEntitiesFromFile(shlexSplit=entityType in Cmd.OUS_ENTITY_TYPES | {Cmd.ENTITY_CROS_OUS, Cmd.ENTITY_CROS_OUS_AND_CHILDREN})))
    if entitySelector == Cmd.ENTITY_SELECTOR_CSVDATAFILE:
      if userAllowed:
        choices += Cmd.USER_ENTITY_SELECTOR_DATAFILE_CSVKMD_SUBTYPES if not GC.Values[GC.USER_SERVICE_ACCOUNT_ACCESS_ONLY] else [Cmd.ENTITY_USERS]
      if crosAllowed:
        choices += Cmd.CROS_ENTITY_SELECTOR_DATAFILE_CSVKMD_SUBTYPES
      entityType = mapEntityType(getChoice(choices), typeMap)
      return (Cmd.ENTITY_USERS if entityType not in Cmd.CROS_ENTITY_SELECTOR_DATAFILE_CSVKMD_SUBTYPES else Cmd.ENTITY_CROS,
              getItemsToModify(entityType, getEntitiesFromCSVFile(shlexSplit=entityType in Cmd.OUS_ENTITY_TYPES | {Cmd.ENTITY_CROS_OUS, Cmd.ENTITY_CROS_OUS_AND_CHILDREN})))
    if entitySelector == Cmd.ENTITY_SELECTOR_CSVKMD:
      if userAllowed:
        choices += Cmd.USER_ENTITY_SELECTOR_DATAFILE_CSVKMD_SUBTYPES if not GC.Values[GC.USER_SERVICE_ACCOUNT_ACCESS_ONLY] else [Cmd.ENTITY_USERS]
      if crosAllowed:
        choices += Cmd.CROS_ENTITY_SELECTOR_DATAFILE_CSVKMD_SUBTYPES
      entityType = mapEntityType(getChoice(choices, choiceAliases=Cmd.ENTITY_ALIAS_MAP), typeMap)
      return (Cmd.ENTITY_USERS if entityType not in Cmd.CROS_ENTITY_SELECTOR_DATAFILE_CSVKMD_SUBTYPES else Cmd.ENTITY_CROS,
              getItemsToModify(entityType, getEntitiesFromCSVbyField()))
    if entitySelector in [Cmd.ENTITY_SELECTOR_CSVDATA, Cmd.ENTITY_SELECTOR_CROSCSVDATA]:
      checkDataField()
      return (Cmd.ENTITY_USERS if entitySelector == Cmd.ENTITY_SELECTOR_CSVDATA else Cmd.ENTITY_CROS,
              GM.Globals[GM.CSV_DATA_DICT])
  entityChoices = []
  if userAllowed:
    entityChoices += Cmd.USER_ENTITIES if not GC.Values[GC.USER_SERVICE_ACCOUNT_ACCESS_ONLY] else [Cmd.ENTITY_USER, Cmd.ENTITY_USERS]
  if crosAllowed:
    entityChoices += Cmd.CROS_ENTITIES
  if browserAllowed:
    entityChoices += Cmd.BROWSER_ENTITIES
  entityType = mapEntityType(getChoice(entityChoices, choiceAliases=Cmd.ENTITY_ALIAS_MAP, defaultChoice=defaultEntityType), typeMap)
  if not entityType:
    invalidChoiceExit(Cmd.Current(), selectorChoices+entityChoices, False)
  if entityType not in Cmd.CROS_ENTITIES+Cmd.BROWSER_ENTITIES:
    entityClass = Cmd.ENTITY_USERS
    if entityType == Cmd.ENTITY_OAUTHUSER:
      return (entityClass, [_getAdminEmail()])
    entityItem = getString(Cmd.OB_USER_ENTITY, minLen=0)
  elif entityType in Cmd.CROS_ENTITIES:
    entityClass = Cmd.ENTITY_CROS
    entityItem = getString(Cmd.OB_CROS_ENTITY, minLen=0)
  else:
    entityClass = Cmd.ENTITY_BROWSER
    entityItem = getString(Cmd.OB_BROWSER_ENTITY, minLen=0)
  if not delayGet:
    if entityClass == Cmd.ENTITY_USERS:
      return (entityClass, getItemsToModify(entityType, entityItem,
                                            isSuspended=isSuspended, isArchived=isArchived, groupMemberType=groupMemberType))
    return (entityClass, getItemsToModify(entityType, entityItem))
  GM.Globals[GM.ENTITY_CL_DELAY_START] = Cmd.Location()
  if not GC.Values[GC.USER_SERVICE_ACCOUNT_ACCESS_ONLY]:
    buildGAPIObject(API.DIRECTORY)
  if entityClass == Cmd.ENTITY_USERS:
    if entityType in Cmd.GROUP_USERS_ENTITY_TYPES | {Cmd.ENTITY_CIGROUP_USERS}:
      # Skip over sub-arguments
      while Cmd.ArgumentsRemaining():
        myarg = getArgument()
        if myarg in GROUP_ROLES_MAP or myarg in {'primarydomain', 'recursive', 'includederivedmembership'}:
          pass
        elif myarg == 'domains':
          Cmd.Advance()
        elif ((entityType == Cmd.ENTITY_GROUP_USERS_SELECT) and
              (myarg in SUSPENDED_ARGUMENTS) or (myarg in ARCHIVED_ARGUMENTS)):
          if myarg in {'issuspended', 'isarchived'}:
            if Cmd.PeekArgumentPresent(TRUE_VALUES) or Cmd.PeekArgumentPresent(FALSE_VALUES):
              Cmd.Advance()
        elif myarg == 'end':
          break
        else:
          Cmd.Backup()
          missingArgumentExit('end')
    return (entityClass,
            {'entityType': entityType, 'entity': entityItem, 'isSuspended': isSuspended, 'isArchived': isArchived,
             'groupMemberType': groupMemberType})
  if entityClass == Cmd.ENTITY_CROS:
    if entityType in {Cmd.ENTITY_CROS_OU_QUERY, Cmd.ENTITY_CROS_OU_AND_CHILDREN_QUERY, Cmd.ENTITY_CROS_OUS_QUERY, Cmd.ENTITY_CROS_OUS_AND_CHILDREN_QUERY,
                      Cmd.ENTITY_CROS_OU_QUERIES, Cmd.ENTITY_CROS_OU_AND_CHILDREN_QUERIES, Cmd.ENTITY_CROS_OUS_QUERIES, Cmd.ENTITY_CROS_OUS_AND_CHILDREN_QUERIES}:
      Cmd.Advance()
  return (entityClass,
          {'entityType': entityType, 'entity': entityItem})

def getEntitySelector():
  return getChoice(Cmd.ENTITY_LIST_SELECTORS, defaultChoice=None)

def getEntitySelection(entitySelector, shlexSplit):
  if entitySelector in [Cmd.ENTITY_SELECTOR_FILE]:
    return getEntitiesFromFile(shlexSplit)
  if entitySelector in [Cmd.ENTITY_SELECTOR_CSV, Cmd.ENTITY_SELECTOR_CSVFILE]:
    return getEntitiesFromCSVFile(shlexSplit)
  if entitySelector == Cmd.ENTITY_SELECTOR_CSVKMD:
    return getEntitiesFromCSVbyField()
  if entitySelector in [Cmd.ENTITY_SELECTOR_CSVSUBKEY]:
    checkSubkeyField()
    return GM.Globals[GM.CSV_DATA_DICT]
  if entitySelector in [Cmd.ENTITY_SELECTOR_CSVDATA]:
    checkDataField()
    return GM.Globals[GM.CSV_DATA_DICT]
  return []

def getEntityList(item, shlexSplit=False):
  entitySelector = getEntitySelector()
  if entitySelector:
    return getEntitySelection(entitySelector, shlexSplit)
  return convertEntityToList(getString(item, minLen=0), shlexSplit=shlexSplit)

def getNormalizedEmailAddressEntity(shlexSplit=False, noUid=True, noLower=False):
  return [normalizeEmailAddressOrUID(emailAddress, noUid=noUid, noLower=noLower) for emailAddress in getEntityList(Cmd.OB_EMAIL_ADDRESS_ENTITY, shlexSplit)]

def getUserObjectEntity(clObject, itemType, shlexSplit=False):
  entity = {'item': itemType, 'list': getEntityList(clObject, shlexSplit), 'dict': None}
  if isinstance(entity['list'], dict):
    entity['dict'] = entity['list']
  return entity

def _validateUserGetObjectList(user, i, count, entity, api=API.GMAIL, showAction=True):
  if entity['dict']:
    entityList = entity['dict'][user]
  else:
    entityList = entity['list']
  user, svc = buildGAPIServiceObject(api, user, i, count)
  if not svc:
    return (user, None, [], 0)
  jcount = len(entityList)
  if showAction:
    entityPerformActionNumItems([Ent.USER, user], jcount, entity['item'], i, count)
  if jcount == 0:
    setSysExitRC(NO_ENTITIES_FOUND_RC)
  return (user, svc, entityList, jcount)

def _validateUserGetMessageIds(user, i, count, entity):
  if entity:
    if entity['dict']:
      entityList = entity['dict'][user]
    else:
      entityList = entity['list']
  else:
    entityList = []
  user, gmail = buildGAPIServiceObject(API.GMAIL, user, i, count)
  if not gmail:
    return (user, None, None)
  return (user, gmail, entityList)

def checkUserExists(cd, user, entityType=None, i=0, count=0):
  if entityType is None:
    entityType = Ent.USER
  user = normalizeEmailAddressOrUID(user)
  try:
    return callGAPI(cd.users(), 'get',
                    throwReasons=GAPI.USER_GET_THROW_REASONS,
                    userKey=user, fields='primaryEmail')['primaryEmail']
  except (GAPI.userNotFound, GAPI.domainNotFound, GAPI.domainCannotUseApis, GAPI.forbidden,
          GAPI.badRequest, GAPI.backendError, GAPI.systemError):
    entityUnknownWarning(entityType, user, i, count)
    return None

def checkUserSuspended(cd, user, entityType=None, i=0, count=0):
  if entityType is None:
    entityType = Ent.USER
  user = normalizeEmailAddressOrUID(user)
  try:
    return callGAPI(cd.users(), 'get',
                    throwReasons=GAPI.USER_GET_THROW_REASONS,
                    userKey=user, fields='suspended')['suspended']
  except (GAPI.userNotFound, GAPI.domainNotFound, GAPI.domainCannotUseApis, GAPI.forbidden,
          GAPI.badRequest, GAPI.backendError, GAPI.systemError):
    entityUnknownWarning(entityType, user, i, count)
    return None

def _getDomainList(cd, customer, fields):
  try:
    return callGAPIitems(cd.domains(), 'list', 'domains',
                         throwReasons=[GAPI.BAD_REQUEST, GAPI.NOT_FOUND,
                                       GAPI.FORBIDDEN, GAPI.PERMISSION_DENIED],
                         customer=customer, fields=fields)
  except (GAPI.badRequest, GAPI.notFound):
    accessErrorExit(cd)
  except (GAPI.forbidden, GAPI.permissionDenied) as e:
    ClientAPIAccessDeniedExit(str(e))

PRINT_PRIVILEGES_FIELDS = ['serviceId', 'serviceName', 'privilegeName', 'isOuScopable', 'childPrivileges']

