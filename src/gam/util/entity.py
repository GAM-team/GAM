"""GAM entity resolution utilities.

UID-to-email conversion, entity list expansion, group member
checking, entity selectors, and customer ID helpers.
"""

import csv
import os
import platform
import re
import shlex
import sys
import warnings

from cryptography import x509
from cryptography.hazmat.backends import default_backend

from gamlib import glapi as API
from gamlib import glcfg as GC
from gamlib import glgapi as GAPI
from gamlib import glglobals as GM
from gamlib import glmsgs as Msg


def _getMain():
  return sys.modules['gam']


def getUserEmailFromID(uid, cd):
  try:
    result = _getMain().callGAPI(cd.users(), 'get',
                      throwReasons=GAPI.USER_GET_THROW_REASONS,
                      retryReasons=GAPI.SERVICE_NOT_AVAILABLE_RETRY_REASONS,
                      userKey=uid, fields='primaryEmail')
    return result.get('primaryEmail')
  except (GAPI.userNotFound, GAPI.domainNotFound, GAPI.domainCannotUseApis, GAPI.forbidden,
          GAPI.badRequest, GAPI.backendError, GAPI.systemError, GAPI.serviceNotAvailable):
    return None

def getGroupEmailFromID(uid, cd):
  try:
    result = _getMain().callGAPI(cd.groups(), 'get',
                      throwReasons=GAPI.GROUP_GET_THROW_REASONS,
                      retryReasons=GAPI.SERVICE_NOT_AVAILABLE_RETRY_REASONS,
                      groupKey=uid, fields='email')
    return result.get('email')
  except (GAPI.groupNotFound, GAPI.domainNotFound, GAPI.domainCannotUseApis, GAPI.forbidden,
          GAPI.badRequest, GAPI.serviceNotAvailable):
    return None

def getServiceAccountEmailFromID(account_id, sal=None):
  if sal is None:
    sal = _getMain().buildGAPIObject(API.SERVICEACCOUNTLOOKUP)
  try:
    certs = _getMain().callGAPI(sal.serviceaccounts(), 'lookup',
                     throwReasons = [GAPI.BAD_REQUEST, GAPI.NOT_FOUND, GAPI.RESOURCE_NOT_FOUND,  GAPI.INVALID_ARGUMENT],
                     account=account_id)
  except (GAPI.badRequest, GAPI.notFound, GAPI.resourceNotFound, GAPI.invalidArgument):
    return None
  sa_cn_rx = r'CN=(.+)\.(.+)\.iam\.gservice.*'
  sa_emails = []
  for _, raw_cert in certs.items():
    cert = x509.load_pem_x509_certificate(raw_cert.encode(), default_backend())
    # suppress crytography warning due to long service account email
    with warnings.catch_warnings():
      warnings.filterwarnings('ignore', message='.*Attribute\'s length.*')
      mg = re.match(sa_cn_rx, cert.issuer.rfc4514_string())
    if mg:
      sa_email = f'{mg.group(1)}@{mg.group(2)}.iam.gserviceaccount.com'
      if sa_email not in sa_emails:
        sa_emails.append(sa_email)
  return GC.Values[GC.CSV_OUTPUT_FIELD_DELIMITER].join(sa_emails)

# Convert UID to email address and type
def convertUIDtoEmailAddressWithType(emailAddressOrUID, cd=None, sal=None, emailTypes=None,
                                     checkForCustomerId=False, ciGroupsAPI=False, aliasAllowed=True):
  if emailTypes is None:
    emailTypes = ['user']
  elif not isinstance(emailTypes, list):
    emailTypes = [emailTypes] if emailTypes != 'any' else ['user', 'group']
  if checkForCustomerId and (emailAddressOrUID == GC.Values[GC.CUSTOMER_ID]):
    return (emailAddressOrUID, 'email')
  normalizedEmailAddressOrUID = _getMain().normalizeEmailAddressOrUID(emailAddressOrUID, ciGroupsAPI=ciGroupsAPI)
  if ciGroupsAPI and emailAddressOrUID.startswith('groups/'):
    return emailAddressOrUID
  if normalizedEmailAddressOrUID.find('@') > 0 and aliasAllowed:
    return (normalizedEmailAddressOrUID, 'email')
  if cd is None:
    cd = _getMain().buildGAPIObject(API.DIRECTORY)
  if 'user' in emailTypes and 'group' in emailTypes:
    # Google User IDs *TEND* to be integers while groups tend to have letters
    # thus we can optimize which check we try first. We'll still check
    # both since there is no guarantee this will always be true.
    if normalizedEmailAddressOrUID.isdigit():
      uid = getUserEmailFromID(normalizedEmailAddressOrUID, cd)
      if uid:
        return (uid, 'user')
      uid = getGroupEmailFromID(normalizedEmailAddressOrUID, cd)
      if uid:
        return (uid, 'group')
    else:
      uid = getGroupEmailFromID(normalizedEmailAddressOrUID, cd)
      if uid:
        return (uid, 'group')
      uid = getUserEmailFromID(normalizedEmailAddressOrUID, cd)
      if uid:
        return (uid, 'user')
  elif 'user' in emailTypes:
    uid = getUserEmailFromID(normalizedEmailAddressOrUID, cd)
    if uid:
      return (uid, 'user')
  elif 'group' in emailTypes:
    uid = getGroupEmailFromID(normalizedEmailAddressOrUID, cd)
    if uid:
      return (uid, 'group')
  if 'resource' in emailTypes:
    try:
      result = _getMain().callGAPI(cd.resources().calendars(), 'get',
                        throwReasons=[GAPI.BAD_REQUEST, GAPI.RESOURCE_NOT_FOUND, GAPI.FORBIDDEN],
                        calendarResourceId=normalizedEmailAddressOrUID,
                        customer=GC.Values[GC.CUSTOMER_ID], fields='resourceEmail')
      if 'resourceEmail' in result:
        return (result['resourceEmail'].lower(), 'resource')
    except (GAPI.badRequest, GAPI.resourceNotFound, GAPI.forbidden):
      pass
  if 'serviceaccount' in emailTypes:
    uid = getServiceAccountEmailFromID(normalizedEmailAddressOrUID, sal)
    if uid:
      return (uid, 'serviceaccount')
  return (normalizedEmailAddressOrUID, 'unknown')

NON_EMAIL_MEMBER_PREFIXES = (
                              "cbcm-browser.",
                              "chrome-os-device.",
                            )
# Convert UID to email address
def convertUIDtoEmailAddress(emailAddressOrUID, cd=None, emailTypes=None,
                             checkForCustomerId=False, ciGroupsAPI=False, aliasAllowed=True):
  if ciGroupsAPI:
    if emailAddressOrUID.startswith(NON_EMAIL_MEMBER_PREFIXES):
      return emailAddressOrUID
    normalizedEmailAddressOrUID = _getMain().normalizeEmailAddressOrUID(emailAddressOrUID, ciGroupsAPI=ciGroupsAPI)
    if normalizedEmailAddressOrUID.startswith(NON_EMAIL_MEMBER_PREFIXES):
      return normalizedEmailAddressOrUID
  email, _ = convertUIDtoEmailAddressWithType(emailAddressOrUID, cd, None, emailTypes,
                                              checkForCustomerId, ciGroupsAPI, aliasAllowed)
  return email

# Convert email address to User/Group UID; called immediately after getting email address from command line
def convertEmailAddressToUID(emailAddressOrUID, cd=None, emailType='user', savedLocation=None):
  normalizedEmailAddressOrUID = _getMain().normalizeEmailAddressOrUID(emailAddressOrUID)
  if normalizedEmailAddressOrUID.find('@') == -1:
    return normalizedEmailAddressOrUID
  if cd is None:
    cd = _getMain().buildGAPIObject(API.DIRECTORY)
  if emailType != 'group':
    try:
      return _getMain().callGAPI(cd.users(), 'get',
                      throwReasons=GAPI.USER_GET_THROW_REASONS,
                      userKey=normalizedEmailAddressOrUID, fields='id')['id']
    except (GAPI.userNotFound, GAPI.domainNotFound, GAPI.domainCannotUseApis, GAPI.forbidden,
            GAPI.badRequest, GAPI.backendError, GAPI.systemError):
      if emailType == 'user':
        if savedLocation is not None:
          _getMain().Cmd.SetLocation(savedLocation)
        _getMain().entityDoesNotExistExit(_getMain().Ent.USER, normalizedEmailAddressOrUID, errMsg=_getMain().getPhraseDNEorSNA(normalizedEmailAddressOrUID))
  try:
    return _getMain().callGAPI(cd.groups(), 'get',
                    throwReasons=GAPI.GROUP_GET_THROW_REASONS, retryReasons=GAPI.GROUP_GET_RETRY_REASONS,
                    groupKey=normalizedEmailAddressOrUID, fields='id')['id']
  except (GAPI.groupNotFound, GAPI.domainNotFound, GAPI.domainCannotUseApis, GAPI.forbidden, GAPI.badRequest, GAPI.invalid, GAPI.systemError):
    if savedLocation is not None:
      _getMain().Cmd.SetLocation(savedLocation)
    _getMain().entityDoesNotExistExit([_getMain().Ent.USER, _getMain().Ent.GROUP][emailType == 'group'], normalizedEmailAddressOrUID, errMsg=_getMain().getPhraseDNEorSNA(normalizedEmailAddressOrUID))

# Convert User UID from API call to email address
def convertUserIDtoEmail(uid, cd=None):
  primaryEmail = GM.Globals[GM.MAP_USER_ID_TO_NAME].get(uid)
  if not primaryEmail:
    if cd is None:
      cd = _getMain().buildGAPIObject(API.DIRECTORY)
    try:
      primaryEmail = _getMain().callGAPI(cd.users(), 'get',
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
  normalizedEmailAddressOrUID = _getMain().normalizeEmailAddressOrUID(emailAddressOrUID)
  atLoc = normalizedEmailAddressOrUID.find('@')
  if atLoc > 0:
    return (normalizedEmailAddressOrUID, normalizedEmailAddressOrUID[:atLoc], normalizedEmailAddressOrUID[atLoc+1:])
  try:
    cd = _getMain().buildGAPIObject(API.DIRECTORY)
    result = _getMain().callGAPI(cd.users(), 'get',
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
      cd = _getMain().buildGAPIObject(API.DIRECTORY)
    try:
      orgUnitPath = _getMain().callGAPI(cd.orgunits(), 'get',
                             throwReasons=GAPI.ORGUNIT_GET_THROW_REASONS,
                             customerId=GC.Values[GC.CUSTOMER_ID], orgUnitPath=orgUnitId, fields='orgUnitPath')['orgUnitPath']
    except (GAPI.invalidOrgunit, GAPI.orgunitNotFound, GAPI.backendError, GAPI.badRequest, GAPI.invalidCustomerId, GAPI.loginRequired):
      orgUnitPath = orgUnitId
    GM.Globals[GM.MAP_ORGUNIT_ID_TO_NAME][orgUnitId] = orgUnitPath
  return orgUnitPath

def shlexSplitList(entity, dataDelimiter=' ,'):
  lexer = shlex.shlex(entity, posix=True)
  lexer.whitespace = dataDelimiter
  lexer.whitespace_split = True
  try:
    return list(lexer)
  except ValueError as e:
    _getMain().Cmd.Backup()
    _getMain().usageErrorExit(str(e))

def shlexSplitListStatus(entity, dataDelimiter=' ,'):
  lexer = shlex.shlex(entity, posix=True)
  lexer.whitespace = dataDelimiter
  lexer.whitespace_split = True
  try:
    return (True, list(lexer))
  except ValueError as e:
    return (False, str(e))

def getQueries(myarg):
  if myarg in {'query', 'filter'}:
    return [_getMain().getString(_getMain().Cmd.OB_QUERY)]
  return shlexSplitList(_getMain().getString(_getMain().Cmd.OB_QUERY_LIST))

def _validateDeviceQuery(entityType, query):
  if ':' in query:
    qfield, qvalue = query.split(':', 1)
    qfield = qfield.strip()
  else:
    qfield = ''
    qvalue = query
  if (not qfield) or (not qvalue)  or ('?' in query):
    _getMain().Cmd.Backup()
    _getMain().usageErrorExit(Msg.INVALID_DEVICE_QUERY.format(_getMain().Ent.Singular(entityType), query))

def getDeviceQueries(myarg, entityType):
  if myarg in {'query', 'filter'}:
    queries = [_getMain().getString(_getMain().Cmd.OB_QUERY)]
  else:
    queries = shlexSplitList(_getMain().getString(_getMain().Cmd.OB_QUERY_LIST))
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
  if memberRoles and memberRoles.find(_getMain().Ent.ROLE_MEMBER) != -1:
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
  return not validRoles or member.get('role', _getMain().Ent.ROLE_MEMBER) in validRoles

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
      member['type'] = _getMain().Ent.TYPE_CUSTOMER
    elif member['preferredMemberKey']['id'] == GC.Values[GC.CUSTOMER_ID]:
      member['type'] = _getMain().Ent.TYPE_CUSTOMER
    else:
      member['type'] = _getMain().Ent.TYPE_OTHER
  roles = {}
  memberRoles = member.get('roles', [{'name': _getMain().Ent.ROLE_MEMBER}])
  for role in memberRoles:
    roles[role['name']] = role
  for a_role in [_getMain().Ent.ROLE_OWNER, _getMain().Ent.ROLE_MANAGER, _getMain().Ent.ROLE_MEMBER]:
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
      member['type'] = _getMain().Ent.TYPE_CUSTOMER
    elif ttype == 'users':
      member['type'] = _getMain().Ent.TYPE_USER if not tid.endswith('.iam.gserviceaccount.com') else _getMain().Ent.TYPE_SERVICE_ACCOUNT
    elif ttype == 'groups':
      member['type'] = _getMain().Ent.TYPE_GROUP
    elif tid.startswith('cbcm-browser.'):
      member['type'] = _getMain().Ent.TYPE_CBCM_BROWSER
    else:
      member['type'] = _getMain().Ent.TYPE_OTHER
  else:
    member['type'] = tmember['type']
  if 'roles' in tmember:
    memberRoles = []
    for trole in tmember['roles']:
      if 'role' in trole:
        trole['name'] = trole.pop('role')
      if trole['name'] == 'ADMIN':
        trole['name'] = _getMain().Ent.ROLE_MANAGER
      memberRoles.append(trole)
  else:
    memberRoles = [{'name': _getMain().Ent.ROLE_MEMBER}]
  roles = {}
  for role in memberRoles:
    roles[role['name']] = role
  for a_role in [_getMain().Ent.ROLE_OWNER, _getMain().Ent.ROLE_MANAGER, _getMain().Ent.ROLE_MEMBER]:
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
    group = _getMain().normalizeEmailAddressOrUID(group, ciGroupsAPI=True)
    if not group.startswith('groups/'):
      return (ci, None, group)
  if not ci:
    ci = _getMain().buildGAPIObject(API.CLOUDIDENTITY_GROUPS)
  try:
    ciGroup = _getMain().callGAPI(ci.groups(), 'get',
                       throwReasons=GAPI.CIGROUP_GET_THROW_REASONS, retryReasons=GAPI.CIGROUP_RETRY_REASONS,
                       name=group, fields='groupKey(id)')
    return (ci, None, ciGroup['groupKey']['id'])
  except (GAPI.notFound, GAPI.domainNotFound, GAPI.domainCannotUseApis,
          GAPI.forbidden, GAPI.badRequest, GAPI.invalid, GAPI.invalidArgument,
          GAPI.systemError, GAPI.permissionDenied, GAPI.serviceNotAvailable) as e:
    action = _getMain().Act.Get()
    _getMain().Act.Set(_getMain().Act.LOOKUP)
    _getMain().entityActionFailedWarning([_getMain().Ent.CLOUD_IDENTITY_GROUP, group, _getMain().Ent.GROUP, None], str(e), i, count)
    _getMain().Act.Set(action)
    return (ci, None, None)

def convertGroupEmailToCloudID(ci, group, i=0, count=0):
  group = _getMain().normalizeEmailAddressOrUID(group, ciGroupsAPI=True)
  if not group.startswith('groups/') and group.find('@') == -1:
    group = 'groups/'+group
  if group.startswith('groups/'):
    ci, _, groupEmail = convertGroupCloudIDToEmail(ci, group, i, count)
    return (ci, group, groupEmail)
  if not ci:
    ci = _getMain().buildGAPIObject(API.CLOUDIDENTITY_GROUPS)
  try:
    ciGroup = _getMain().callGAPI(ci.groups(), 'lookup',
                       throwReasons=GAPI.CIGROUP_GET_THROW_REASONS, retryReasons=GAPI.CIGROUP_RETRY_REASONS,
                       groupKey_id=group, fields='name')
    return (ci, ciGroup['name'], group)
  except (GAPI.notFound, GAPI.domainNotFound, GAPI.domainCannotUseApis,
          GAPI.forbidden, GAPI.badRequest, GAPI.invalid, GAPI.invalidArgument,
          GAPI.systemError, GAPI.failedPrecondition, GAPI.permissionDenied, GAPI.serviceNotAvailable) as e:
    action = _getMain().Act.Get()
    _getMain().Act.Set(_getMain().Act.LOOKUP)
    _getMain().entityActionFailedWarning([_getMain().Ent.CLOUD_IDENTITY_GROUP, group], str(e), i, count)
    _getMain().Act.Set(action)
    return (ci, None, None)

CIGROUP_DISCUSSION_FORUM_LABEL = 'cloudidentity.googleapis.com/groups.discussion_forum'
CIGROUP_DYNAMIC_LABEL = 'cloudidentity.googleapis.com/groups.dynamic'
CIGROUP_SECURITY_LABEL = 'cloudidentity.googleapis.com/groups.security'
CIGROUP_LOCKED_LABEL = 'cloudidentity.googleapis.com/groups.locked'

def getCIGroupMembershipGraph(ci, member):
  if not ci:
    ci = _getMain().buildGAPIObject(API.CLOUDIDENTITY_GROUPS)
  parent = 'groups/-'
  try:
    result = _getMain().callGAPI(ci.groups().memberships(), 'getMembershipGraph',
                      throwReasons=GAPI.CIGROUP_LIST_THROW_REASONS, retryReasons=GAPI.CIGROUP_RETRY_REASONS,
                      parent=parent,
                      query=f"member_key_id == '{member}' && '{CIGROUP_DISCUSSION_FORUM_LABEL}' in labels")
    return (ci, result.get('response', {}))
  except (GAPI.resourceNotFound, GAPI.domainNotFound, GAPI.domainCannotUseApis,
          GAPI.forbidden, GAPI.badRequest, GAPI.invalid, GAPI.invalidArgument,
          GAPI.systemError, GAPI.permissionDenied, GAPI.serviceNotAvailable) as e:
    action = _getMain().Act.Get()
    _getMain().Act.Set(_getMain().Act.LOOKUP)
    _getMain().entityActionFailedWarning([_getMain().Ent.CLOUD_IDENTITY_GROUP, parent], str(e))
    _getMain().Act.Set(action)
    return (ci, None)

def checkGroupExists(cd, ci, ciGroupsAPI, group, i=0, count=0):
  group = _getMain().normalizeEmailAddressOrUID(group, ciGroupsAPI=ciGroupsAPI)
  if not ciGroupsAPI:
    if not group.startswith('groups/'):
      try:
        result = _getMain().callGAPI(cd.groups(), 'get',
                          throwReasons=GAPI.GROUP_GET_THROW_REASONS, retryReasons=GAPI.GROUP_GET_RETRY_REASONS,
                          groupKey=group, fields='email')
        return (ci, None, result['email'])
      except (GAPI.groupNotFound, GAPI.domainNotFound, GAPI.domainCannotUseApis, GAPI.forbidden, GAPI.badRequest, GAPI.invalid, GAPI.systemError):
        _getMain().entityUnknownWarning(_getMain().Ent.GROUP, group, i, count)
        return (ci, None, None)
    else:
      ci, _, groupEmail = convertGroupCloudIDToEmail(ci, group, i, count)
      return (ci, None, groupEmail)
  else:
    if not group.startswith('groups/') and group.find('@') == -1:
      group = 'groups/'+group
    if group.startswith('groups/'):
      try:
        result = _getMain().callGAPI(ci.groups(), 'get',
                          throwReasons=GAPI.CIGROUP_GET_THROW_REASONS, retryReasons=GAPI.CIGROUP_RETRY_REASONS,
                          name=group, fields='name,groupKey(id)')
        return (ci, result['name'], result['groupKey']['id'])
      except (GAPI.notFound, GAPI.domainNotFound, GAPI.domainCannotUseApis,
              GAPI.forbidden, GAPI.badRequest, GAPI.invalid, GAPI.invalidArgument,
              GAPI.systemError, GAPI.permissionDenied, GAPI.serviceNotAvailable):
        _getMain().entityUnknownWarning(_getMain().Ent.CLOUD_IDENTITY_GROUP, group, i, count)
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
    _getMain().printErrorMessage(_getMain().INVALID_ENTITY_RC, _getMain().formatKeyValueList('', [_getMain().Ent.Singular(entityType), entityName, Msg.INVALID], ''))

  def _addGroupUsersToUsers(group, domains, recursive, includeDerivedMembership):
    _getMain().printGettingAllEntityItemsForWhom(memberRoles if memberRoles else _getMain().Ent.ROLE_MANAGER_MEMBER_OWNER, group, entityType=_getMain().Ent.GROUP)
    validRoles, listRoles, listFields = _getRoleVerification(memberRoles, 'nextPageToken,members(email,type,status)')
    try:
      result = _getMain().callGAPIpages(cd.members(), 'list', 'members',
                             pageMessage=_getMain().getPageMessageForWhom(),
                             throwReasons=GAPI.MEMBERS_THROW_REASONS, retryReasons=GAPI.MEMBERS_RETRY_REASONS,
                             includeDerivedMembership=includeDerivedMembership,
                             groupKey=group, roles=listRoles, fields=listFields, maxResults=GC.Values[GC.MEMBER_MAX_RESULTS])
    except (GAPI.groupNotFound, GAPI.domainNotFound, GAPI.domainCannotUseApis, GAPI.invalid, GAPI.forbidden, GAPI.serviceNotAvailable):
      _getMain().entityUnknownWarning(_getMain().Ent.GROUP, group)
      _incrEntityDoesNotExist(_getMain().Ent.GROUP)
      return
    for member in result:
      if member['type'] == _getMain().Ent.TYPE_USER:
        email = member['email'].lower()
        if email in entitySet:
          continue
        if _checkMemberRoleIsSuspendedIsArchived(member, validRoles, isSuspended, isArchived):
          if domains:
            _, domain = _getMain().splitEmailAddress(email)
            if domain not in domains:
              continue
          entitySet.add(email)
          entityList.append(email)
      elif recursive and member['type'] == _getMain().Ent.TYPE_GROUP:
        _addGroupUsersToUsers(member['email'], domains, recursive, includeDerivedMembership)

  def _addCIGroupUsersToUsers(groupName, groupEmail, recursive):
    _getMain().printGettingAllEntityItemsForWhom(memberRoles if memberRoles else _getMain().Ent.ROLE_MANAGER_MEMBER_OWNER, groupEmail, entityType=_getMain().Ent.CLOUD_IDENTITY_GROUP)
    validRoles = _getCIRoleVerification(memberRoles)
    try:
      result = _getMain().callGAPIpages(ci.groups().memberships(), 'list', 'memberships',
                             pageMessage=_getMain().getPageMessageForWhom(),
                             throwReasons=GAPI.CIGROUP_LIST_THROW_REASONS, retryReasons=GAPI.CIGROUP_RETRY_REASONS,
                             parent=groupName, view='FULL',
                             fields='nextPageToken,memberships(name,preferredMemberKey(id),roles(name),type)', pageSize=GC.Values[GC.MEMBER_MAX_RESULTS])
    except (GAPI.resourceNotFound, GAPI.domainNotFound, GAPI.domainCannotUseApis,
            GAPI.forbidden, GAPI.badRequest, GAPI.invalid, GAPI.invalidArgument,
            GAPI.systemError, GAPI.permissionDenied, GAPI.serviceNotAvailable):
      _getMain().entityUnknownWarning(_getMain().Ent.CLOUD_IDENTITY_GROUP, groupEmail)
      _incrEntityDoesNotExist(_getMain().Ent.CLOUD_IDENTITY_GROUP)
      return
    for member in result:
      getCIGroupMemberRoleFixType(member)
      if member['type'] == _getMain().Ent.TYPE_USER:
        email = member.get('preferredMemberKey', {}).get('id', '')
        if (email and _checkMemberRole(member, validRoles) and email not in entitySet):
          entitySet.add(email)
          entityList.append(email)
      elif recursive and member['type'] == _getMain().Ent.TYPE_GROUP and _checkMemberRole(member, validRoles):
        _, gname = member['name'].rsplit('/', 1)
        _addCIGroupUsersToUsers(f'groups/{gname}', f'groups/{gname}', recursive)

  GM.Globals[GM.CLASSROOM_SERVICE_NOT_AVAILABLE] = False
  ENTITY_ERROR_DNE = 'doesNotExist'
  ENTITY_ERROR_INVALID = 'invalid'
  entityError = {'entityType': None, ENTITY_ERROR_DNE: 0, ENTITY_ERROR_INVALID: 0}
  entityList = []
  entitySet = set()
  entityLocation = _getMain().Cmd.Location()
  if entityType in {_getMain().Cmd.ENTITY_USER, _getMain().Cmd.ENTITY_USERS}:
    if not GC.Values[GC.USER_SERVICE_ACCOUNT_ACCESS_ONLY] and not GC.Values[GC.DOMAIN]:
      _getMain().buildGAPIObject(API.DIRECTORY)
    result = convertEntityToList(entity, nonListEntityType=entityType == _getMain().Cmd.ENTITY_USER)
    for user in result:
      if _getMain().validateEmailAddressOrUID(user):
        if user not in entitySet:
          entitySet.add(user)
          entityList.append(user)
      else:
        _showInvalidEntity(_getMain().Ent.USER, user)
    if GC.Values[GC.USER_SERVICE_ACCOUNT_ACCESS_ONLY]:
      return entityList
  elif entityType in _getMain().Cmd.ALL_USER_ENTITY_TYPES:
    cd = _getMain().buildGAPIObject(API.DIRECTORY)
    if entityType == _getMain().Cmd.ENTITY_ALL_USERS and ((isSuspended is not None) or (isArchived is not None)):
      if isSuspended is not None:
        query = f'isSuspended={isSuspended}'
        if isArchived is not None:
          query += f' isArchived={isArchived}'
      else:
        query = f'isArchived={isArchived}'
    else:
      query = _getMain().Cmd.ALL_USERS_QUERY_MAP[entityType]
    _getMain().printGettingAllAccountEntities(_getMain().Ent.USER, query=query)
    try:
      result = _getMain().callGAPIpages(cd.users(), 'list', 'users',
                             pageMessage=_getMain().getPageMessage(),
                             throwReasons=[GAPI.BAD_REQUEST, GAPI.RESOURCE_NOT_FOUND, GAPI.FORBIDDEN],
                             retryReasons=GAPI.SERVICE_NOT_AVAILABLE_RETRY_REASONS,
                             customer=GC.Values[GC.CUSTOMER_ID], query=query, orderBy='email',
                             fields='nextPageToken,users(primaryEmail)',
                             maxResults=GC.Values[GC.USER_MAX_RESULTS])
    except (GAPI.badRequest, GAPI.resourceNotFound, GAPI.forbidden):
      _getMain().accessErrorExit(cd)
    entityList = [user['primaryEmail'] for user in result]
  elif entityType == _getMain().Cmd.ENTITY_ALL_USERS_ARCH_OR_SUSP:
    cd = _getMain().buildGAPIObject(API.DIRECTORY)
    for query in ['isSuspended=True', 'isArchived=True']:
      _getMain().printGettingAllAccountEntities(_getMain().Ent.USER, query)
      try:
        result = _getMain().callGAPIpages(cd.users(), 'list', 'users',
                               pageMessage=_getMain().getPageMessage(),
                               throwReasons=[GAPI.BAD_REQUEST, GAPI.RESOURCE_NOT_FOUND, GAPI.FORBIDDEN],
                               retryReasons=GAPI.SERVICE_NOT_AVAILABLE_RETRY_REASONS,
                               customer=GC.Values[GC.CUSTOMER_ID], query=query, orderBy='email',
                               fields='nextPageToken,users(primaryEmail)',
                               maxResults=GC.Values[GC.USER_MAX_RESULTS])
      except (GAPI.badRequest, GAPI.resourceNotFound, GAPI.forbidden):
        _getMain().accessErrorExit(cd)
      entitySet |= {user['primaryEmail'] for user in result}
    entityList = sorted(list(entitySet))
  elif entityType in _getMain().Cmd.DOMAIN_ENTITY_TYPES:
    if entityType == _getMain().Cmd.ENTITY_DOMAINS and ((isSuspended is not None) or (isArchived is not None)):
      if isSuspended is not None:
        query = f'isSuspended={isSuspended}'
        if isArchived is not None:
          query += f' isArchived={isArchived}'
      else:
        query = f'isArchived={isArchived}'
    else:
      query = _getMain().Cmd.DOMAINS_QUERY_MAP[entityType]
    cd = _getMain().buildGAPIObject(API.DIRECTORY)
    domains = convertEntityToList(entity)
    for domain in domains:
      _getMain().printGettingAllEntityItemsForWhom(_getMain().Ent.USER, domain, query=query, entityType=_getMain().Ent.DOMAIN)
      try:
        result = _getMain().callGAPIpages(cd.users(), 'list', 'users',
                               pageMessage=_getMain().getPageMessageForWhom(),
                               throwReasons=[GAPI.BAD_REQUEST, GAPI.RESOURCE_NOT_FOUND, GAPI.DOMAIN_NOT_FOUND, GAPI.FORBIDDEN],
                               retryReasons=GAPI.SERVICE_NOT_AVAILABLE_RETRY_REASONS,
                               domain=domain, query=query, orderBy='email',
                               fields='nextPageToken,users(primaryEmail)',
                               maxResults=GC.Values[GC.USER_MAX_RESULTS])
      except (GAPI.badRequest, GAPI.resourceNotFound, GAPI.domainNotFound, GAPI.forbidden):
        _getMain().checkEntityDNEorAccessErrorExit(cd, _getMain().Ent.DOMAIN, domain)
        _incrEntityDoesNotExist(_getMain().Ent.DOMAIN)
        continue
      entityList.extend([user['primaryEmail'] for user in result])
  elif entityType in _getMain().Cmd.GROUP_ENTITY_TYPES or entityType in _getMain().Cmd.GROUPS_ENTITY_TYPES:
    isArchived, isSuspended = _getMain().Cmd.GROUPS_QUERY_MAP.get(entityType, (isArchived, isSuspended))
    includeDerivedMembership = entityType in {_getMain().Cmd.ENTITY_GROUP_INDE, _getMain().Cmd.ENTITY_GROUPS_INDE}
    cd = _getMain().buildGAPIObject(API.DIRECTORY)
    groups = convertEntityToList(entity, nonListEntityType=entityType in _getMain().Cmd.GROUP_ENTITY_TYPES)
    for group in groups:
      if _getMain().validateEmailAddressOrUID(group, checkPeople=False):
        group = _getMain().normalizeEmailAddressOrUID(group)
        _getMain().printGettingAllEntityItemsForWhom(memberRoles if memberRoles else _getMain().Ent.ROLE_MANAGER_MEMBER_OWNER, group, entityType=_getMain().Ent.GROUP)
        validRoles, listRoles, listFields = _getRoleVerification(memberRoles, 'nextPageToken,members(email,id,type,status)')
        try:
          result = _getMain().callGAPIpages(cd.members(), 'list', 'members',
                                 pageMessage=_getMain().getPageMessageForWhom(),
                                 throwReasons=GAPI.MEMBERS_THROW_REASONS, retryReasons=GAPI.MEMBERS_RETRY_REASONS,
                                 includeDerivedMembership=includeDerivedMembership,
                                 groupKey=group, roles=listRoles, fields=listFields, maxResults=GC.Values[GC.MEMBER_MAX_RESULTS])
        except (GAPI.groupNotFound, GAPI.domainNotFound, GAPI.domainCannotUseApis, GAPI.invalid, GAPI.forbidden, GAPI.serviceNotAvailable):
          _getMain().entityUnknownWarning(_getMain().Ent.GROUP, group)
          _incrEntityDoesNotExist(_getMain().Ent.GROUP)
          continue
        for member in result:
          email = member['email'].lower() if member['type'] != _getMain().Ent.TYPE_CUSTOMER else member['id']
          if ((groupMemberType in ('ALL', member['type'])) and
              (not includeDerivedMembership or (member['type'] == _getMain().Ent.TYPE_USER)) and
              _checkMemberRoleIsSuspendedIsArchived(member, validRoles, isSuspended, isArchived) and
              email not in entitySet):
            entitySet.add(email)
            entityList.append(email)
      else:
        _showInvalidEntity(_getMain().Ent.GROUP, group)
  elif entityType in _getMain().Cmd.GROUP_USERS_ENTITY_TYPES:
    isArchived, isSuspended = _getMain().Cmd.GROUP_USERS_QUERY_MAP.get(entityType, (isArchived, isSuspended))
    cd = _getMain().buildGAPIObject(API.DIRECTORY)
    groups = convertEntityToList(entity)
    includeDerivedMembership = False
    domains = []
    rolesSet = set()
    if not noCLArgs:
      while _getMain().Cmd.ArgumentsRemaining():
        myarg = _getMain().getArgument()
        if myarg in GROUP_ROLES_MAP:
          rolesSet.add(GROUP_ROLES_MAP[myarg])
        elif myarg == 'primarydomain':
          domains.append(GC.Values[GC.DOMAIN])
        elif myarg == 'domains':
          domains.extend(getEntityList(_getMain().Cmd.OB_DOMAIN_NAME_ENTITY))
        elif myarg == 'recursive':
          recursive = True
          includeDerivedMembership = False
        elif myarg == 'includederivedmembership':
          includeDerivedMembership = True
          recursive = False
        elif entityType == _getMain().Cmd.ENTITY_GROUP_USERS_SELECT and myarg in _getMain().SUSPENDED_ARGUMENTS:
          isSuspended = _getMain()._getIsSuspended(myarg)
        elif entityType == _getMain().Cmd.ENTITY_GROUP_USERS_SELECT and myarg in _getMain().ARCHIVED_ARGUMENTS:
          isArchived = _getMain()._getIsArchived(myarg)
        elif myarg == 'end':
          break
        else:
          _getMain().Cmd.Backup()
          _getMain().missingArgumentExit('end')
    if rolesSet:
      memberRoles = ','.join(sorted(rolesSet))
    for group in groups:
      if _getMain().validateEmailAddressOrUID(group, checkPeople=False):
        _addGroupUsersToUsers(_getMain().normalizeEmailAddressOrUID(group), domains, recursive, includeDerivedMembership)
      else:
        _showInvalidEntity(_getMain().Ent.GROUP, group)
  elif entityType in {_getMain().Cmd.ENTITY_CIGROUP, _getMain().Cmd.ENTITY_CIGROUPS}:
    ci = _getMain().buildGAPIObject(API.CLOUDIDENTITY_GROUPS)
    groups = convertEntityToList(entity, nonListEntityType=entityType in {_getMain().Cmd.ENTITY_CIGROUP})
    for group in groups:
      if _getMain().validateEmailAddressOrUID(group, checkPeople=False, ciGroupsAPI=True):
        _, name, groupEmail = convertGroupEmailToCloudID(ci, group)
        _getMain().printGettingAllEntityItemsForWhom(memberRoles if memberRoles else _getMain().Ent.ROLE_MANAGER_MEMBER_OWNER, groupEmail, entityType=_getMain().Ent.CLOUD_IDENTITY_GROUP)
        validRoles = _getCIRoleVerification(memberRoles)
        try:
          result = _getMain().callGAPIpages(ci.groups().memberships(), 'list', 'memberships',
                                 pageMessage=_getMain().getPageMessageForWhom(),
                                 throwReasons=GAPI.CIGROUP_LIST_THROW_REASONS, retryReasons=GAPI.CIGROUP_RETRY_REASONS,
                                 parent=name, view='FULL',
                                 fields='nextPageToken,memberships(preferredMemberKey(id),roles(name),type)',
                                 pageSize=GC.Values[GC.MEMBER_MAX_RESULTS])
        except (GAPI.resourceNotFound, GAPI.domainNotFound, GAPI.domainCannotUseApis,
                GAPI.forbidden, GAPI.badRequest, GAPI.invalid, GAPI.invalidArgument,
                GAPI.systemError, GAPI.permissionDenied, GAPI.serviceNotAvailable):
          _getMain().entityUnknownWarning(_getMain().Ent.CLOUD_IDENTITY_GROUP, groupEmail)
          _incrEntityDoesNotExist(_getMain().Ent.CLOUD_IDENTITY_GROUP)
          continue
        for member in result:
          getCIGroupMemberRoleFixType(member)
          email = member.get('preferredMemberKey', {}).get('id', '')
          if (email and (groupMemberType in ('ALL', member['type'])) and
              _checkMemberRole(member, validRoles) and email not in entitySet):
            entitySet.add(email)
            entityList.append(email)
      else:
        _showInvalidEntity(_getMain().Ent.CLOUD_IDENTITY_GROUP, groupEmail)
  elif entityType in {_getMain().Cmd.ENTITY_CIGROUP_USERS}:
    ci = _getMain().buildGAPIObject(API.CLOUDIDENTITY_GROUPS)
    groups = convertEntityToList(entity)
    rolesSet = set()
    if not noCLArgs:
      while _getMain().Cmd.ArgumentsRemaining():
        myarg = _getMain().getArgument()
        if myarg in GROUP_ROLES_MAP:
          rolesSet.add(GROUP_ROLES_MAP[myarg])
        elif myarg == 'recursive':
          recursive = True
        elif myarg == 'end':
          break
        else:
          _getMain().Cmd.Backup()
          _getMain().missingArgumentExit('end')
    if rolesSet:
      memberRoles = ','.join(sorted(rolesSet))
    for group in groups:
      _, name, groupEmail = convertGroupEmailToCloudID(ci, group)
      if name and groupEmail:
        _addCIGroupUsersToUsers(name, groupEmail, recursive)
      else:
        _showInvalidEntity(_getMain().Ent.GROUP, group)
  elif entityType in _getMain().Cmd.OU_ENTITY_TYPES or entityType in _getMain().Cmd.OUS_ENTITY_TYPES:
    isArchived, isSuspended = _getMain().Cmd.OU_QUERY_MAP.get(entityType, (isArchived, isSuspended))
    cd = _getMain().buildGAPIObject(API.DIRECTORY)
    ous = convertEntityToList(entity, shlexSplit=True, nonListEntityType=entityType in _getMain().Cmd.OU_ENTITY_TYPES)
    directlyInOU = entityType in _getMain().Cmd.OU_DIRECT_ENTITY_TYPES
    qualifier = Msg.DIRECTLY_IN_THE.format(_getMain().Ent.Singular(_getMain().Ent.ORGANIZATIONAL_UNIT)) if directlyInOU else Msg.IN_THE.format(_getMain().Ent.Singular(_getMain().Ent.ORGANIZATIONAL_UNIT))
    fields = 'nextPageToken,users(primaryEmail,orgUnitPath)' if directlyInOU else 'nextPageToken,users(primaryEmail)'
    for ou in ous:
      if ou == 'root':
        ou = '/'
      ou = _getMain().makeOrgUnitPathAbsolute(ou)
      if ou.startswith('id:'):
        try:
          ou = _getMain().callGAPI(cd.orgunits(), 'get',
                        throwReasons=GAPI.ORGUNIT_GET_THROW_REASONS,
                        customerId=GC.Values[GC.CUSTOMER_ID],
                        orgUnitPath=ou, fields='orgUnitPath')['orgUnitPath']
        except (GAPI.invalidOrgunit, GAPI.orgunitNotFound, GAPI.backendError, GAPI.badRequest,
                GAPI.invalidCustomerId, GAPI.loginRequired):
          _getMain().checkEntityDNEorAccessErrorExit(cd, _getMain().Ent.ORGANIZATIONAL_UNIT, ou)
          _incrEntityDoesNotExist(_getMain().Ent.ORGANIZATIONAL_UNIT)
          continue
      ouLower = ou.lower()
      _getMain().printGettingAllEntityItemsForWhom(_getMain().Ent.USER, ou, qualifier=Msg.IN_THE.format(_getMain().Ent.Singular(_getMain().Ent.ORGANIZATIONAL_UNIT)),
                                        entityType=_getMain().Ent.ORGANIZATIONAL_UNIT)
      pageMessage = _getMain().getPageMessageForWhom()
      usersInOU = 0
      try:
        feed = _getMain().yieldGAPIpages(cd.users(), 'list', 'users',
                              pageMessage=pageMessage, messageAttribute='primaryEmail',
                              throwReasons=[GAPI.INVALID_ORGUNIT, GAPI.ORGUNIT_NOT_FOUND,
                                            GAPI.INVALID_INPUT, GAPI.BAD_REQUEST, GAPI.RESOURCE_NOT_FOUND, GAPI.FORBIDDEN],
                              retryReasons=GAPI.SERVICE_NOT_AVAILABLE_RETRY_REASONS,
                              customer=GC.Values[GC.CUSTOMER_ID], query=_getMain().orgUnitPathQuery(ou, isSuspended, isArchived), orderBy='email',
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
        _getMain().setGettingAllEntityItemsForWhom(_getMain().Ent.USER, ou, qualifier=qualifier)
        _getMain().printGotEntityItemsForWhom(usersInOU)
      except (GAPI.invalidInput, GAPI.invalidOrgunit, GAPI.orgunitNotFound, GAPI.backendError, GAPI.badRequest,
              GAPI.invalidCustomerId, GAPI.loginRequired, GAPI.resourceNotFound, GAPI.forbidden):
        _getMain().checkEntityDNEorAccessErrorExit(cd, _getMain().Ent.ORGANIZATIONAL_UNIT, ou)
        _incrEntityDoesNotExist(_getMain().Ent.ORGANIZATIONAL_UNIT)
  elif entityType in {_getMain().Cmd.ENTITY_QUERY, _getMain().Cmd.ENTITY_QUERIES}:
    cd = _getMain().buildGAPIObject(API.DIRECTORY)
    queries = convertEntityToList(entity, shlexSplit=True, nonListEntityType=entityType == _getMain().Cmd.ENTITY_QUERY)
    for query in queries:
      _getMain().printGettingAllAccountEntities(_getMain().Ent.USER, query)
      try:
        result = _getMain().callGAPIpages(cd.users(), 'list', 'users',
                               pageMessage=_getMain().getPageMessage(),
                               throwReasons=[GAPI.INVALID_ORGUNIT, GAPI.ORGUNIT_NOT_FOUND,
                                             GAPI.INVALID_INPUT, GAPI.BAD_REQUEST, GAPI.RESOURCE_NOT_FOUND, GAPI.FORBIDDEN],
                               retryReasons=GAPI.SERVICE_NOT_AVAILABLE_RETRY_REASONS,
                               customer=GC.Values[GC.CUSTOMER_ID], query=query, orderBy='email',
                               fields='nextPageToken,users(primaryEmail,suspended,archived)',
                               maxResults=GC.Values[GC.USER_MAX_RESULTS])
      except (GAPI.invalidOrgunit, GAPI.orgunitNotFound, GAPI.invalidInput):
        _getMain().Cmd.Backup()
        _getMain().usageErrorExit(Msg.INVALID_QUERY)
      except (GAPI.badRequest, GAPI.resourceNotFound, GAPI.forbidden):
        _getMain().accessErrorExit(cd)
      for user in result:
        email = user['primaryEmail']
        if ((isSuspended is None or isSuspended == user['suspended']) and
            (isArchived is None or isArchived == user['archived']) and
            email not in entitySet):
          entitySet.add(email)
          entityList.append(email)
  elif entityType == _getMain().Cmd.ENTITY_LICENSES:
    skusList = []
    for item in entity.split(','):
      productId, sku = _getMain().SKU.getProductAndSKU(item)
      if not productId:
        _incrEntityDoesNotExist(_getMain().Ent.SKU)
      elif (productId, sku) not in skusList:
        skusList.append((productId, sku))
    if skusList:
      entityList = _getMain().doPrintLicenses(returnFields=['userId'], skus=skusList)
  elif entityType in {_getMain().Cmd.ENTITY_COURSEPARTICIPANTS, _getMain().Cmd.ENTITY_TEACHERS, _getMain().Cmd.ENTITY_STUDENTS}:
    croom = _getMain().buildGAPIObject(API.CLASSROOM)
    if not noListConversion:
      courseIdList = convertEntityToList(entity)
    else:
      courseIdList = [entity]
    _, _, coursesInfo = _getMain()._getCoursesOwnerInfo(croom, courseIdList, GC.Values[GC.USE_COURSE_OWNER_ACCESS])
    for courseId, courseInfo in coursesInfo.items():
      try:
        if entityType in {_getMain().Cmd.ENTITY_COURSEPARTICIPANTS, _getMain().Cmd.ENTITY_TEACHERS}:
          _getMain().printGettingAllEntityItemsForWhom(_getMain().Ent.TEACHER, _getMain().removeCourseIdScope(courseId), entityType=_getMain().Ent.COURSE)
          result = _getMain().callGAPIpages(courseInfo['croom'].courses().teachers(), 'list', 'teachers',
                                 pageMessage=_getMain().getPageMessageForWhom(),
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
        if entityType in {_getMain().Cmd.ENTITY_COURSEPARTICIPANTS, _getMain().Cmd.ENTITY_STUDENTS}:
          _getMain().printGettingAllEntityItemsForWhom(_getMain().Ent.STUDENT, _getMain().removeCourseIdScope(courseId), entityType=_getMain().Ent.COURSE)
          result = _getMain().callGAPIpages(courseInfo['croom'].courses().students(), 'list', 'students',
                                 pageMessage=_getMain().getPageMessageForWhom(),
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
        _getMain().entityDoesNotExistWarning(_getMain().Ent.COURSE, _getMain().removeCourseIdScope(courseId))
        _incrEntityDoesNotExist(_getMain().Ent.COURSE)
      except GAPI.serviceNotAvailable as e:
        _getMain().entityActionNotPerformedWarning([_getMain().Ent.COURSE, _getMain().removeCourseIdScope(courseId)], str(e))
        GM.Globals[GM.CLASSROOM_SERVICE_NOT_AVAILABLE] = True
        break
      except (GAPI.forbidden, GAPI.permissionDenied, GAPI.badRequest) as e:
        _getMain().ClientAPIAccessDeniedExit(str(e))
  elif entityType == _getMain().Cmd.ENTITY_CROS:
    _getMain().buildGAPIObject(API.DIRECTORY)
    for deviceId in convertEntityToList(entity):
      if deviceId not in entitySet:
        entitySet.add(deviceId)
        entityList.append(deviceId)
  elif entityType == _getMain().Cmd.ENTITY_ALL_CROS:
    cd = _getMain().buildGAPIObject(API.DIRECTORY)
    _getMain().printGettingAllAccountEntities(_getMain().Ent.CROS_DEVICE)
    try:
      result = _getMain().callGAPIpages(cd.chromeosdevices(), 'list', 'chromeosdevices',
                             pageMessage=_getMain().getPageMessage(),
                             throwReasons=[GAPI.INVALID_INPUT, GAPI.BAD_REQUEST, GAPI.RESOURCE_NOT_FOUND, GAPI.FORBIDDEN],
                             retryReasons=GAPI.SERVICE_NOT_AVAILABLE_RETRY_REASONS,
                             customerId=GC.Values[GC.CUSTOMER_ID],
                             fields='nextPageToken,chromeosdevices(deviceId)',
                             maxResults=GC.Values[GC.DEVICE_MAX_RESULTS])
    except (GAPI.invalidInput, GAPI.badRequest, GAPI.resourceNotFound, GAPI.forbidden):
      _getMain().accessErrorExit(cd)
    entityList = [device['deviceId'] for device in result]
  elif entityType in {_getMain().Cmd.ENTITY_CROS_QUERY, _getMain().Cmd.ENTITY_CROS_QUERIES, _getMain().Cmd.ENTITY_CROS_SN}:
    cd = _getMain().buildGAPIObject(API.DIRECTORY)
    queries = convertEntityToList(entity, shlexSplit=entityType == _getMain().Cmd.ENTITY_CROS_QUERIES,
                                  nonListEntityType=entityType == _getMain().Cmd.ENTITY_CROS_QUERY)
    if entityType == _getMain().Cmd.ENTITY_CROS_SN:
      queries = [f'id:{query}' for query in queries]
    for query in queries:
      _validateDeviceQuery(_getMain().Ent.CROS_DEVICE, query)
      _getMain().printGettingAllAccountEntities(_getMain().Ent.CROS_DEVICE, query)
      try:
        result = _getMain().callGAPIpages(cd.chromeosdevices(), 'list', 'chromeosdevices',
                               pageMessage=_getMain().getPageMessage(),
                               throwReasons=[GAPI.INVALID_INPUT, GAPI.BAD_REQUEST, GAPI.RESOURCE_NOT_FOUND, GAPI.FORBIDDEN],
                               retryReasons=GAPI.SERVICE_NOT_AVAILABLE_RETRY_REASONS,
                               customerId=GC.Values[GC.CUSTOMER_ID], query=query,
                               fields='nextPageToken,chromeosdevices(deviceId)',
                               maxResults=GC.Values[GC.DEVICE_MAX_RESULTS])
      except GAPI.invalidInput:
        _getMain().Cmd.Backup()
        _getMain().usageErrorExit(Msg.INVALID_QUERY)
      except (GAPI.badRequest, GAPI.resourceNotFound, GAPI.forbidden):
        _getMain().accessErrorExit(cd)
      for device in result:
        deviceId = device['deviceId']
        if deviceId not in entitySet:
          entitySet.add(deviceId)
          entityList.append(deviceId)
  elif entityType in _getMain().Cmd.CROS_OU_ENTITY_TYPES or entityType in _getMain().Cmd.CROS_OUS_ENTITY_TYPES:
    cd = _getMain().buildGAPIObject(API.DIRECTORY)
    ous = convertEntityToList(entity, shlexSplit=True, nonListEntityType=entityType in _getMain().Cmd.CROS_OU_ENTITY_TYPES)
    numOus = len(ous)
    includeChildOrgunits = entityType in _getMain().Cmd.CROS_OU_CHILDREN_ENTITY_TYPES
    allQualifier = Msg.DIRECTLY_IN_THE.format(_getMain().Ent.Choose(_getMain().Ent.ORGANIZATIONAL_UNIT, numOus)) if not includeChildOrgunits else Msg.IN_THE.format(_getMain().Ent.Choose(_getMain().Ent.ORGANIZATIONAL_UNIT, numOus))
    if entityType in _getMain().Cmd.CROS_OU_QUERY_ENTITY_TYPES:
      queries = getDeviceQueries('query', _getMain().Ent.CROS_DEVICE)
    elif entityType in _getMain().Cmd.CROS_OU_QUERIES_ENTITY_TYPES:
      queries = getDeviceQueries('queries', _getMain().Ent.CROS_DEVICE)
    else:
      queries = [None]
    for ou in ous:
      if ou == 'root':
        ou = '/'
      ou = _getMain().makeOrgUnitPathAbsolute(ou)
      oneQualifier = Msg.DIRECTLY_IN_THE.format(_getMain().Ent.Singular(_getMain().Ent.ORGANIZATIONAL_UNIT)) if not includeChildOrgunits else Msg.IN_THE.format(_getMain().Ent.Singular(_getMain().Ent.ORGANIZATIONAL_UNIT))
      for query in queries:
        _getMain().printGettingAllEntityItemsForWhom(_getMain().Ent.CROS_DEVICE, ou,
                                          query=query, qualifier=oneQualifier, entityType=_getMain().Ent.ORGANIZATIONAL_UNIT)
        try:
          result = _getMain().callGAPIpages(cd.chromeosdevices(), 'list', 'chromeosdevices',
                                 pageMessage=_getMain().getPageMessageForWhom(),
                                 throwReasons=[GAPI.INVALID_INPUT, GAPI.INVALID_ORGUNIT, GAPI.ORGUNIT_NOT_FOUND,
                                               GAPI.BAD_REQUEST, GAPI.RESOURCE_NOT_FOUND, GAPI.FORBIDDEN],
                                 retryReasons=GAPI.SERVICE_NOT_AVAILABLE_RETRY_REASONS,
                                 customerId=GC.Values[GC.CUSTOMER_ID], query=query,
                                 orgUnitPath=ou, includeChildOrgunits=includeChildOrgunits,
                                 fields='nextPageToken,chromeosdevices(deviceId)', maxResults=GC.Values[GC.DEVICE_MAX_RESULTS])
        except GAPI.invalidInput:
          _getMain().Cmd.Backup()
          _getMain().usageErrorExit(Msg.INVALID_QUERY)
        except (GAPI.invalidOrgunit, GAPI.orgunitNotFound, GAPI.badRequest, GAPI.resourceNotFound, GAPI.forbidden):
          _getMain().checkEntityDNEorAccessErrorExit(cd, _getMain().Ent.ORGANIZATIONAL_UNIT, ou)
          _incrEntityDoesNotExist(_getMain().Ent.ORGANIZATIONAL_UNIT)
          continue
        if query is None:
          entityList.extend([device['deviceId'] for device in result])
        else:
          for device in result:
            deviceId = device['deviceId']
            if deviceId not in entitySet:
              entitySet.add(deviceId)
              entityList.append(deviceId)
    _getMain().Ent.SetGettingQualifier(_getMain().Ent.CROS_DEVICE, allQualifier)
    _getMain().Ent.SetGettingForWhom(','.join(ous))
    _getMain().printGotEntityItemsForWhom(len(entityList))
  elif entityType == _getMain().Cmd.ENTITY_BROWSER:
    result = convertEntityToList(entity)
    for deviceId in result:
      if deviceId not in entitySet:
        entitySet.add(deviceId)
        entityList.append(deviceId)
  elif entityType in {_getMain().Cmd.ENTITY_BROWSER_OU, _getMain().Cmd.ENTITY_BROWSER_OUS}:
    cbcm = _getMain().buildGAPIObject(API.CBCM)
    customerId = _getMain()._getCustomerIdNoC()
    ous = convertEntityToList(entity, shlexSplit=True, nonListEntityType=entityType == _getMain().Cmd.ENTITY_BROWSER_OU)
    numOus = len(ous)
    allQualifier = Msg.DIRECTLY_IN_THE.format(_getMain().Ent.Choose(_getMain().Ent.ORGANIZATIONAL_UNIT, numOus))
    oneQualifier = Msg.DIRECTLY_IN_THE.format(_getMain().Ent.Singular(_getMain().Ent.ORGANIZATIONAL_UNIT))
    for ou in ous:
      ou = _getMain().makeOrgUnitPathAbsolute(ou)
      _getMain().printGettingAllEntityItemsForWhom(_getMain().Ent.CHROME_BROWSER, ou, qualifier=oneQualifier, entityType=_getMain().Ent.ORGANIZATIONAL_UNIT)
      try:
        result = _getMain().callGAPIpages(cbcm.chromebrowsers(), 'list', 'browsers',
                               pageMessage=_getMain().getPageMessageForWhom(),
                               throwReasons=[GAPI.BAD_REQUEST, GAPI.INVALID_ORGUNIT, GAPI.FORBIDDEN],
                               retryReasons=GAPI.SERVICE_NOT_AVAILABLE_RETRY_REASONS,
                               customer=customerId, orgUnitPath=ou, projection='BASIC',
                               orderBy='id', sortOrder='ASCENDING', fields='nextPageToken,browsers(deviceId)')
      except (GAPI.badRequest, GAPI.invalidOrgunit, GAPI.forbidden):
        _getMain().checkEntityDNEorAccessErrorExit(None, _getMain().Ent.ORGANIZATIONAL_UNIT, ou)
        _incrEntityDoesNotExist(_getMain().Ent.ORGANIZATIONAL_UNIT)
        continue
      entityList.extend([browser['deviceId'] for browser in result])
    _getMain().Ent.SetGettingQualifier(_getMain().Ent.CHROME_BROWSER, allQualifier)
    _getMain().Ent.SetGettingForWhom(','.join(ous))
    _getMain().printGotEntityItemsForWhom(len(entityList))
  elif entityType in {_getMain().Cmd.ENTITY_BROWSER_QUERY, _getMain().Cmd.ENTITY_BROWSER_QUERIES}:
    cbcm = _getMain().buildGAPIObject(API.CBCM)
    customerId = _getMain()._getCustomerIdNoC()
    queries = convertEntityToList(entity, shlexSplit=entityType == _getMain().Cmd.ENTITY_BROWSER_QUERIES,
                                  nonListEntityType=entityType == _getMain().Cmd.ENTITY_BROWSER_QUERY)
    for query in queries:
      _getMain().printGettingAllAccountEntities(_getMain().Ent.CHROME_BROWSER, query)
      try:
        result = _getMain().callGAPIpages(cbcm.chromebrowsers(), 'list', 'browsers',
                               pageMessage=_getMain().getPageMessage(),
                               throwReasons=[GAPI.INVALID_INPUT, GAPI.BAD_REQUEST, GAPI.RESOURCE_NOT_FOUND, GAPI.FORBIDDEN],
                               retryReasons=GAPI.SERVICE_NOT_AVAILABLE_RETRY_REASONS,
                               customer=customerId, query=query, projection='BASIC',
                               orderBy='id', sortOrder='ASCENDING', fields='nextPageToken,browsers(deviceId)')
      except GAPI.invalidInput:
        _getMain().Cmd.Backup()
        _getMain().usageErrorExit(Msg.INVALID_QUERY)
      except (GAPI.badRequest, GAPI.resourceNotFound, GAPI.forbidden) as e:
        _getMain().accessErrorExitNonDirectory(API.CBCM, str(e))
      for device in result:
        deviceId = device['deviceId']
        if deviceId not in entitySet:
          entitySet.add(deviceId)
          entityList.append(deviceId)
  else:
    _getMain().systemErrorExit(_getMain().UNKNOWN_ERROR_RC, 'getItemsToModify coding error')
  for errorType in [ENTITY_ERROR_DNE, ENTITY_ERROR_INVALID]:
    if entityError[errorType] > 0:
      _getMain().Cmd.SetLocation(entityLocation-1)
      _getMain().writeStderr(_getMain().Cmd.CommandLineWithBadArgumentMarked(False))
      count = entityError[errorType]
      if errorType == ENTITY_ERROR_DNE:
        _getMain().stderrErrorMsg(Msg.BAD_ENTITIES_IN_SOURCE.format(count, _getMain().Ent.Choose(entityError['entityType'], count),
                                                         Msg.DO_NOT_EXIST if count != 1 else Msg.DOES_NOT_EXIST))
        sys.exit(_getMain().ENTITY_DOES_NOT_EXIST_RC)
      else:
        _getMain().stderrErrorMsg(Msg.BAD_ENTITIES_IN_SOURCE.format(count, Msg.INVALID, _getMain().Ent.Choose(entityError['entityType'], count)))
        sys.exit(_getMain().INVALID_ENTITY_RC)
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
    _getMain().systemErrorExit(_getMain().DATA_ERROR_RC,
                    _getMain().formatKeyValueList('',
                                       [_getMain().Ent.Singular(_getMain().Ent.FILE), filename,
                                        _getMain().Ent.Singular(_getMain().Ent.ROW), row,
                                        _getMain().Ent.Singular(_getMain().Ent.ITEM), itemName,
                                        _getMain().Ent.Singular(_getMain().Ent.VALUE), value,
                                        errMessage],
                                       ''))
  else:
    _getMain().systemErrorExit(_getMain().DATA_ERROR_RC,
                    _getMain().formatKeyValueList('',
                                       [_getMain().Ent.Singular(_getMain().Ent.FILE), filename,
                                        _getMain().Ent.Singular(_getMain().Ent.ROW), row,
                                        _getMain().Ent.Singular(_getMain().Ent.VALUE), value,
                                        errMessage],
                                       ''))

# <FileSelector>
def getEntitiesFromFile(shlexSplit, returnSet=False):
  filename = _getMain().getString(_getMain().Cmd.OB_FILE_NAME)
  filenameLower = filename.lower()
  if filenameLower not in {'gcsv', 'gdoc', 'gcscsv', 'gcsdoc'}:
    encoding = _getMain().getCharSet()
    filename = _getMain().setFilePath(filename, GC.INPUT_DIR)
    f = _getMain().openFile(filename, encoding=encoding, stripUTFBOM=True)
  elif filenameLower in {'gcsv', 'gdoc'}:
    f = _getMain().getGDocData(filenameLower)
    _getMain().getCharSet()
  else: #filenameLower in {'gcscsv', 'gcsdoc'}:
    f = _getMain().getStorageFileData(filenameLower)
    _getMain().getCharSet()
  dataDelimiter = _getMain().getDelimiter()
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
  _getMain().closeFile(f)
  return entityList if not returnSet else entitySet

# <CSVFileSelector>
def getEntitiesFromCSVFile(shlexSplit, returnSet=False):
  fileFieldName = _getMain().getString(_getMain().Cmd.OB_FILE_NAME_FIELD_NAME)
  if platform.system() == 'Windows' and not fileFieldName.startswith('-:'):
    drive, fileFieldName = os.path.splitdrive(fileFieldName)
  else:
    drive = ''
  if fileFieldName.find(':') == -1:
    _getMain().Cmd.Backup()
    _getMain().invalidArgumentExit(_getMain().Cmd.OB_FILE_NAME_FIELD_NAME)
  fileFieldNameList = fileFieldName.split(':')
  filename = drive+fileFieldNameList[0]
  f, csvFile, fieldnames = _getMain().openCSVFileReader(filename)
  for fieldName in fileFieldNameList[1:]:
    if fieldName not in fieldnames:
      _getMain().csvFieldErrorExit(fieldName, fieldnames, backupArg=True, checkForCharset=True)
  matchFields, skipFields = _getMain().getMatchSkipFields(fieldnames)
  dataDelimiter = _getMain().getDelimiter()
  entitySet = set()
  entityList = []
  i = 1
  for row in csvFile:
    i += 1
    if _getMain().checkMatchSkipFields(row, None, matchFields, skipFields):
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
  _getMain().closeFile(f)
  return entityList if not returnSet else entitySet

# <CSVFileSelector>
#	keyfield <FieldName> [keypattern <RESearchPattern>] [keyvalue <RESubstitution>] [delimiter <Character>]
#	subkeyfield <FieldName> [keypattern <RESearchPattern>] [keyvalue <RESubstitution>] [delimiter <Character>]
#	(matchfield|skipfield <FieldName> <RESearchPattern>)*
#	[datafield <FieldName>(:<FieldName>)* [delimiter <Character>]]
def getEntitiesFromCSVbyField():

  def getKeyFieldInfo(keyword, required, globalKeyField):
    if not _getMain().checkArgumentPresent(keyword, required=required):
      GM.Globals[globalKeyField] = None
      return (None, None, None, None)
    keyField = GM.Globals[globalKeyField] = _getMain().getString(_getMain().Cmd.OB_FIELD_NAME)
    if keyField not in fieldnames:
      _getMain().csvFieldErrorExit(keyField, fieldnames, backupArg=True)
    if _getMain().checkArgumentPresent('keypattern'):
      keyPattern = _getMain().getREPattern()
    else:
      keyPattern = None
    if _getMain().checkArgumentPresent('keyvalue'):
      keyValue = _getMain().getString(_getMain().Cmd.OB_STRING)
    else:
      keyValue = keyField
    keyDelimiter = _getMain().getDelimiter()
    return (keyField, keyPattern, keyValue, keyDelimiter)

  def getKeyList(row, keyField, keyPattern, keyValue, keyDelimiter, matchFields, skipFields):
    item = row[keyField].strip()
    if not item:
      return []
    if not _getMain().checkMatchSkipFields(row, None, matchFields, skipFields):
      return []
    if keyPattern:
      keyList = [keyPattern.sub(keyValue, keyItem.strip()) for keyItem in splitEntityList(item, keyDelimiter)]
    else:
      keyList = [re.sub(keyField, keyItem.strip(), keyValue) for keyItem in splitEntityList(item, keyDelimiter)]
    return [key for key in keyList if key]

  filename = _getMain().getString(_getMain().Cmd.OB_FILE_NAME)
  f, csvFile, fieldnames = _getMain().openCSVFileReader(filename)
  mainKeyField, mainKeyPattern, mainKeyValue, mainKeyDelimiter = getKeyFieldInfo('keyfield', True, GM.CSV_KEY_FIELD)
  subKeyField, subKeyPattern, subKeyValue, subKeyDelimiter = getKeyFieldInfo('subkeyfield', False, GM.CSV_SUBKEY_FIELD)
  matchFields, skipFields = _getMain().getMatchSkipFields(fieldnames)
  if _getMain().checkArgumentPresent('datafield'):
    if GM.Globals[GM.CSV_DATA_DICT]:
      _getMain().csvDataAlreadySavedErrorExit()
    GM.Globals[GM.CSV_DATA_FIELD] = _getMain().getString(_getMain().Cmd.OB_FIELD_NAME, checkBlank=True)
    dataFields = GM.Globals[GM.CSV_DATA_FIELD].split(':')
    for dataField in dataFields:
      if dataField not in fieldnames:
        _getMain().csvFieldErrorExit(dataField, fieldnames, backupArg=True)
    dataDelimiter = _getMain().getDelimiter()
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
  _getMain().closeFile(f)
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
    clLoc = _getMain().Cmd.Location()
    _getMain().Cmd.SetLocation(GM.Globals[GM.ENTITY_CL_DELAY_START])
    entityList = getItemsToModify(**entityList)
    _getMain().Cmd.SetLocation(clLoc)
  return (0, len(entityList), entityList)

def getEntityToModify(defaultEntityType=None, browserAllowed=False, crosAllowed=False, userAllowed=True,
                      typeMap=None, isSuspended=None, isArchived=None, groupMemberType='USER', delayGet=False):
  if GC.Values[GC.USER_SERVICE_ACCOUNT_ACCESS_ONLY]:
    crosAllowed = False
    selectorChoices = _getMain().Cmd.SERVICE_ACCOUNT_ONLY_ENTITY_SELECTORS[:]
  else:
    selectorChoices = _getMain().Cmd.BASE_ENTITY_SELECTORS[:]
  if userAllowed:
    selectorChoices += _getMain().Cmd.USER_ENTITY_SELECTORS+_getMain().Cmd.USER_CSVDATA_ENTITY_SELECTORS
  if crosAllowed:
    selectorChoices += _getMain().Cmd.CROS_ENTITY_SELECTORS+_getMain().Cmd.CROS_CSVDATA_ENTITY_SELECTORS
  if browserAllowed:
    selectorChoices = _getMain().Cmd.BROWSER_ENTITY_SELECTORS
  entitySelector = _getMain().getChoice(selectorChoices, defaultChoice=None)
  if entitySelector:
    choices = []
    if entitySelector == _getMain().Cmd.ENTITY_SELECTOR_ALL:
      if userAllowed:
        choices += _getMain().Cmd.USER_ENTITY_SELECTOR_ALL_SUBTYPES
      if crosAllowed:
        choices += _getMain().Cmd.CROS_ENTITY_SELECTOR_ALL_SUBTYPES
      entityType = _getMain().Cmd.ENTITY_SELECTOR_ALL_SUBTYPES_MAP[_getMain().getChoice(choices)]
      if not delayGet:
        return (_getMain().Cmd.ENTITY_USERS if entityType != _getMain().Cmd.ENTITY_ALL_CROS else _getMain().Cmd.ENTITY_CROS,
                getItemsToModify(entityType, None))
      GM.Globals[GM.ENTITY_CL_DELAY_START] = _getMain().Cmd.Location()
      _getMain().buildGAPIObject(API.DIRECTORY)
      return (_getMain().Cmd.ENTITY_USERS if entityType != _getMain().Cmd.ENTITY_ALL_CROS else _getMain().Cmd.ENTITY_CROS,
              {'entityType': entityType, 'entity': None})
    if userAllowed:
      if entitySelector == _getMain().Cmd.ENTITY_SELECTOR_FILE:
        return (_getMain().Cmd.ENTITY_USERS, getItemsToModify(_getMain().Cmd.ENTITY_USERS, getEntitiesFromFile(False)))
      if entitySelector in [_getMain().Cmd.ENTITY_SELECTOR_CSV, _getMain().Cmd.ENTITY_SELECTOR_CSVFILE]:
        return (_getMain().Cmd.ENTITY_USERS, getItemsToModify(_getMain().Cmd.ENTITY_USERS, getEntitiesFromCSVFile(False)))
    if crosAllowed:
      if entitySelector == _getMain().Cmd.ENTITY_SELECTOR_CROSFILE:
        return (_getMain().Cmd.ENTITY_CROS, getEntitiesFromFile(False))
      if entitySelector in [_getMain().Cmd.ENTITY_SELECTOR_CROSCSV, _getMain().Cmd.ENTITY_SELECTOR_CROSCSVFILE]:
        return (_getMain().Cmd.ENTITY_CROS, getEntitiesFromCSVFile(False))
      if entitySelector == _getMain().Cmd.ENTITY_SELECTOR_CROSFILE_SN:
        return (_getMain().Cmd.ENTITY_CROS, getItemsToModify(_getMain().Cmd.ENTITY_CROS_SN, getEntitiesFromFile(False)))
      if entitySelector in [_getMain().Cmd.ENTITY_SELECTOR_CROSCSV_SN, _getMain().Cmd.ENTITY_SELECTOR_CROSCSVFILE_SN]:
        return (_getMain().Cmd.ENTITY_CROS, getItemsToModify(_getMain().Cmd.ENTITY_CROS_SN, getEntitiesFromCSVFile(False)))
    if browserAllowed:
      if entitySelector == _getMain().Cmd.ENTITY_SELECTOR_FILE:
        return (_getMain().Cmd.ENTITY_BROWSER, getEntitiesFromFile(False))
      if entitySelector in [_getMain().Cmd.ENTITY_SELECTOR_CSV, _getMain().Cmd.ENTITY_SELECTOR_CSVFILE]:
        return (_getMain().Cmd.ENTITY_BROWSER, getEntitiesFromCSVFile(False))
    if entitySelector == _getMain().Cmd.ENTITY_SELECTOR_DATAFILE:
      if userAllowed:
        choices += _getMain().Cmd.USER_ENTITY_SELECTOR_DATAFILE_CSVKMD_SUBTYPES if not GC.Values[GC.USER_SERVICE_ACCOUNT_ACCESS_ONLY] else [_getMain().Cmd.ENTITY_USERS]
      if crosAllowed:
        choices += _getMain().Cmd.CROS_ENTITY_SELECTOR_DATAFILE_CSVKMD_SUBTYPES
      entityType = mapEntityType(_getMain().getChoice(choices), typeMap)
      return (_getMain().Cmd.ENTITY_USERS if entityType not in _getMain().Cmd.CROS_ENTITY_SELECTOR_DATAFILE_CSVKMD_SUBTYPES else _getMain().Cmd.ENTITY_CROS,
              getItemsToModify(entityType, getEntitiesFromFile(shlexSplit=entityType in _getMain().Cmd.OUS_ENTITY_TYPES | {_getMain().Cmd.ENTITY_CROS_OUS, _getMain().Cmd.ENTITY_CROS_OUS_AND_CHILDREN})))
    if entitySelector == _getMain().Cmd.ENTITY_SELECTOR_CSVDATAFILE:
      if userAllowed:
        choices += _getMain().Cmd.USER_ENTITY_SELECTOR_DATAFILE_CSVKMD_SUBTYPES if not GC.Values[GC.USER_SERVICE_ACCOUNT_ACCESS_ONLY] else [_getMain().Cmd.ENTITY_USERS]
      if crosAllowed:
        choices += _getMain().Cmd.CROS_ENTITY_SELECTOR_DATAFILE_CSVKMD_SUBTYPES
      entityType = mapEntityType(_getMain().getChoice(choices), typeMap)
      return (_getMain().Cmd.ENTITY_USERS if entityType not in _getMain().Cmd.CROS_ENTITY_SELECTOR_DATAFILE_CSVKMD_SUBTYPES else _getMain().Cmd.ENTITY_CROS,
              getItemsToModify(entityType, getEntitiesFromCSVFile(shlexSplit=entityType in _getMain().Cmd.OUS_ENTITY_TYPES | {_getMain().Cmd.ENTITY_CROS_OUS, _getMain().Cmd.ENTITY_CROS_OUS_AND_CHILDREN})))
    if entitySelector == _getMain().Cmd.ENTITY_SELECTOR_CSVKMD:
      if userAllowed:
        choices += _getMain().Cmd.USER_ENTITY_SELECTOR_DATAFILE_CSVKMD_SUBTYPES if not GC.Values[GC.USER_SERVICE_ACCOUNT_ACCESS_ONLY] else [_getMain().Cmd.ENTITY_USERS]
      if crosAllowed:
        choices += _getMain().Cmd.CROS_ENTITY_SELECTOR_DATAFILE_CSVKMD_SUBTYPES
      entityType = mapEntityType(_getMain().getChoice(choices, choiceAliases=_getMain().Cmd.ENTITY_ALIAS_MAP), typeMap)
      return (_getMain().Cmd.ENTITY_USERS if entityType not in _getMain().Cmd.CROS_ENTITY_SELECTOR_DATAFILE_CSVKMD_SUBTYPES else _getMain().Cmd.ENTITY_CROS,
              getItemsToModify(entityType, getEntitiesFromCSVbyField()))
    if entitySelector in [_getMain().Cmd.ENTITY_SELECTOR_CSVDATA, _getMain().Cmd.ENTITY_SELECTOR_CROSCSVDATA]:
      _getMain().checkDataField()
      return (_getMain().Cmd.ENTITY_USERS if entitySelector == _getMain().Cmd.ENTITY_SELECTOR_CSVDATA else _getMain().Cmd.ENTITY_CROS,
              GM.Globals[GM.CSV_DATA_DICT])
  entityChoices = []
  if userAllowed:
    entityChoices += _getMain().Cmd.USER_ENTITIES if not GC.Values[GC.USER_SERVICE_ACCOUNT_ACCESS_ONLY] else [_getMain().Cmd.ENTITY_USER, _getMain().Cmd.ENTITY_USERS]
  if crosAllowed:
    entityChoices += _getMain().Cmd.CROS_ENTITIES
  if browserAllowed:
    entityChoices += _getMain().Cmd.BROWSER_ENTITIES
  entityType = mapEntityType(_getMain().getChoice(entityChoices, choiceAliases=_getMain().Cmd.ENTITY_ALIAS_MAP, defaultChoice=defaultEntityType), typeMap)
  if not entityType:
    _getMain().invalidChoiceExit(_getMain().Cmd.Current(), selectorChoices+entityChoices, False)
  if entityType not in _getMain().Cmd.CROS_ENTITIES+_getMain().Cmd.BROWSER_ENTITIES:
    entityClass = _getMain().Cmd.ENTITY_USERS
    if entityType == _getMain().Cmd.ENTITY_OAUTHUSER:
      return (entityClass, [_getMain()._getAdminEmail()])
    entityItem = _getMain().getString(_getMain().Cmd.OB_USER_ENTITY, minLen=0)
  elif entityType in _getMain().Cmd.CROS_ENTITIES:
    entityClass = _getMain().Cmd.ENTITY_CROS
    entityItem = _getMain().getString(_getMain().Cmd.OB_CROS_ENTITY, minLen=0)
  else:
    entityClass = _getMain().Cmd.ENTITY_BROWSER
    entityItem = _getMain().getString(_getMain().Cmd.OB_BROWSER_ENTITY, minLen=0)
  if not delayGet:
    if entityClass == _getMain().Cmd.ENTITY_USERS:
      return (entityClass, getItemsToModify(entityType, entityItem,
                                            isSuspended=isSuspended, isArchived=isArchived, groupMemberType=groupMemberType))
    return (entityClass, getItemsToModify(entityType, entityItem))
  GM.Globals[GM.ENTITY_CL_DELAY_START] = _getMain().Cmd.Location()
  if not GC.Values[GC.USER_SERVICE_ACCOUNT_ACCESS_ONLY]:
    _getMain().buildGAPIObject(API.DIRECTORY)
  if entityClass == _getMain().Cmd.ENTITY_USERS:
    if entityType in _getMain().Cmd.GROUP_USERS_ENTITY_TYPES | {_getMain().Cmd.ENTITY_CIGROUP_USERS}:
      # Skip over sub-arguments
      while _getMain().Cmd.ArgumentsRemaining():
        myarg = _getMain().getArgument()
        if myarg in GROUP_ROLES_MAP or myarg in {'primarydomain', 'recursive', 'includederivedmembership'}:
          pass
        elif myarg == 'domains':
          _getMain().Cmd.Advance()
        elif ((entityType == _getMain().Cmd.ENTITY_GROUP_USERS_SELECT) and
              (myarg in _getMain().SUSPENDED_ARGUMENTS) or (myarg in _getMain().ARCHIVED_ARGUMENTS)):
          if myarg in {'issuspended', 'isarchived'}:
            if _getMain().Cmd.PeekArgumentPresent(_getMain().TRUE_VALUES) or _getMain().Cmd.PeekArgumentPresent(_getMain().FALSE_VALUES):
              _getMain().Cmd.Advance()
        elif myarg == 'end':
          break
        else:
          _getMain().Cmd.Backup()
          _getMain().missingArgumentExit('end')
    return (entityClass,
            {'entityType': entityType, 'entity': entityItem, 'isSuspended': isSuspended, 'isArchived': isArchived,
             'groupMemberType': groupMemberType})
  if entityClass == _getMain().Cmd.ENTITY_CROS:
    if entityType in {_getMain().Cmd.ENTITY_CROS_OU_QUERY, _getMain().Cmd.ENTITY_CROS_OU_AND_CHILDREN_QUERY, _getMain().Cmd.ENTITY_CROS_OUS_QUERY, _getMain().Cmd.ENTITY_CROS_OUS_AND_CHILDREN_QUERY,
                      _getMain().Cmd.ENTITY_CROS_OU_QUERIES, _getMain().Cmd.ENTITY_CROS_OU_AND_CHILDREN_QUERIES, _getMain().Cmd.ENTITY_CROS_OUS_QUERIES, _getMain().Cmd.ENTITY_CROS_OUS_AND_CHILDREN_QUERIES}:
      _getMain().Cmd.Advance()
  return (entityClass,
          {'entityType': entityType, 'entity': entityItem})

def getEntitySelector():
  return _getMain().getChoice(_getMain().Cmd.ENTITY_LIST_SELECTORS, defaultChoice=None)

def getEntitySelection(entitySelector, shlexSplit):
  if entitySelector in [_getMain().Cmd.ENTITY_SELECTOR_FILE]:
    return getEntitiesFromFile(shlexSplit)
  if entitySelector in [_getMain().Cmd.ENTITY_SELECTOR_CSV, _getMain().Cmd.ENTITY_SELECTOR_CSVFILE]:
    return getEntitiesFromCSVFile(shlexSplit)
  if entitySelector == _getMain().Cmd.ENTITY_SELECTOR_CSVKMD:
    return getEntitiesFromCSVbyField()
  if entitySelector in [_getMain().Cmd.ENTITY_SELECTOR_CSVSUBKEY]:
    _getMain().checkSubkeyField()
    return GM.Globals[GM.CSV_DATA_DICT]
  if entitySelector in [_getMain().Cmd.ENTITY_SELECTOR_CSVDATA]:
    _getMain().checkDataField()
    return GM.Globals[GM.CSV_DATA_DICT]
  return []

def getEntityList(item, shlexSplit=False):
  entitySelector = getEntitySelector()
  if entitySelector:
    return getEntitySelection(entitySelector, shlexSplit)
  return convertEntityToList(_getMain().getString(item, minLen=0), shlexSplit=shlexSplit)

def getNormalizedEmailAddressEntity(shlexSplit=False, noUid=True, noLower=False):
  return [_getMain().normalizeEmailAddressOrUID(emailAddress, noUid=noUid, noLower=noLower) for emailAddress in getEntityList(_getMain().Cmd.OB_EMAIL_ADDRESS_ENTITY, shlexSplit)]

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
  user, svc = _getMain().buildGAPIServiceObject(api, user, i, count)
  if not svc:
    return (user, None, [], 0)
  jcount = len(entityList)
  if showAction:
    _getMain().entityPerformActionNumItems([_getMain().Ent.USER, user], jcount, entity['item'], i, count)
  if jcount == 0:
    _getMain().setSysExitRC(_getMain().NO_ENTITIES_FOUND_RC)
  return (user, svc, entityList, jcount)

def _validateUserGetMessageIds(user, i, count, entity):
  if entity:
    if entity['dict']:
      entityList = entity['dict'][user]
    else:
      entityList = entity['list']
  else:
    entityList = []
  user, gmail = _getMain().buildGAPIServiceObject(API.GMAIL, user, i, count)
  if not gmail:
    return (user, None, None)
  return (user, gmail, entityList)

def checkUserExists(cd, user, entityType=None, i=0, count=0):
  if entityType is None:
    entityType = _getMain().Ent.USER
  user = _getMain().normalizeEmailAddressOrUID(user)
  try:
    return _getMain().callGAPI(cd.users(), 'get',
                    throwReasons=GAPI.USER_GET_THROW_REASONS,
                    userKey=user, fields='primaryEmail')['primaryEmail']
  except (GAPI.userNotFound, GAPI.domainNotFound, GAPI.domainCannotUseApis, GAPI.forbidden,
          GAPI.badRequest, GAPI.backendError, GAPI.systemError):
    _getMain().entityUnknownWarning(entityType, user, i, count)
    return None

def checkUserSuspended(cd, user, entityType=None, i=0, count=0):
  if entityType is None:
    entityType = _getMain().Ent.USER
  user = _getMain().normalizeEmailAddressOrUID(user)
  try:
    return _getMain().callGAPI(cd.users(), 'get',
                    throwReasons=GAPI.USER_GET_THROW_REASONS,
                    userKey=user, fields='suspended')['suspended']
  except (GAPI.userNotFound, GAPI.domainNotFound, GAPI.domainCannotUseApis, GAPI.forbidden,
          GAPI.badRequest, GAPI.backendError, GAPI.systemError):
    _getMain().entityUnknownWarning(entityType, user, i, count)
    return None

def _getCustomerId():
  customerId = GC.Values[GC.CUSTOMER_ID]
  if customerId != GC.MY_CUSTOMER and customerId[0] != 'C':
    customerId = 'C' + customerId
  return customerId

def _getCustomerIdNoC():
  customerId = GC.Values[GC.CUSTOMER_ID]
  if customerId[0] == 'C':
    return customerId[1:]
  return customerId

def _getCustomersCustomerIdNoC():
  customerId = GC.Values[GC.CUSTOMER_ID]
  if customerId.startswith('C'):
    customerId = customerId[1:]
  return f'customers/{customerId}'

def _getCustomersCustomerIdWithC():
  customerId = GC.Values[GC.CUSTOMER_ID]
  if customerId != GC.MY_CUSTOMER and customerId[0] != 'C':
    customerId = 'C' + customerId
  return f'customers/{customerId}'

def _getDomainList(cd, customer, fields):
  from gam.util.access import accessErrorExit, ClientAPIAccessDeniedExit
  try:
    return _getMain().callGAPIitems(cd.domains(), 'list', 'domains',
                         throwReasons=[GAPI.BAD_REQUEST, GAPI.NOT_FOUND,
                                       GAPI.FORBIDDEN, GAPI.PERMISSION_DENIED],
                         customer=customer, fields=fields)
  except (GAPI.badRequest, GAPI.notFound):
    accessErrorExit(cd)
  except (GAPI.forbidden, GAPI.permissionDenied) as e:
    ClientAPIAccessDeniedExit(str(e))

def setTrueCustomerId(cd=None, forceUpdate=False):
  from gam.util.access import ClientAPIAccessDeniedExit
  if GC.Values[GC.CUSTOMER_ID] == GC.MY_CUSTOMER or forceUpdate:
    if not cd:
      cd = _getMain().buildGAPIObject(API.DIRECTORY)
    try:
      customerInfo = _getMain().callGAPI(cd.customers(), 'get',
                              throwReasons=[GAPI.BAD_REQUEST, GAPI.INVALID_INPUT, GAPI.RESOURCE_NOT_FOUND,
                                            GAPI.FORBIDDEN, GAPI.PERMISSION_DENIED],
                              customerKey=GC.MY_CUSTOMER,
                              fields='id')
      GC.Values[GC.CUSTOMER_ID] = customerInfo['id']
    except (GAPI.badRequest, GAPI.invalidInput, GAPI.resourceNotFound):
      pass
    except (GAPI.forbidden, GAPI.permissionDenied) as e:
      ClientAPIAccessDeniedExit(str(e))

PRINT_PRIVILEGES_FIELDS = ['serviceId', 'serviceName', 'privilegeName', 'isOuScopable', 'childPrivileges']

# Drive MIME type constants (moved from cmd/userservices.py)
APPLICATION_VND_GOOGLE_APPS = 'application/vnd.google-apps.'
MIMETYPE_GA_DOCUMENT = f'{APPLICATION_VND_GOOGLE_APPS}document'
MIMETYPE_GA_FOLDER = f'{APPLICATION_VND_GOOGLE_APPS}folder'
MIMETYPE_GA_FORM = f'{APPLICATION_VND_GOOGLE_APPS}form'
MIMETYPE_GA_PRESENTATION = f'{APPLICATION_VND_GOOGLE_APPS}presentation'
MIMETYPE_GA_SHORTCUT = f'{APPLICATION_VND_GOOGLE_APPS}shortcut'
MIMETYPE_GA_SPREADSHEET = f'{APPLICATION_VND_GOOGLE_APPS}spreadsheet'
MIMETYPE_GA_3P_SHORTCUT = f'{APPLICATION_VND_GOOGLE_APPS}drive-sdk'
ME_IN_OWNERS = "'me' in owners"
ME_IN_OWNERS_AND = ME_IN_OWNERS + " and "
NOT_ME_IN_OWNERS = "not " + ME_IN_OWNERS
NOT_ME_IN_OWNERS_AND = NOT_ME_IN_OWNERS + " and "

def _getEntityMimeType(fileEntry):
  Ent = _getMain().Ent
  if fileEntry['mimeType'] == MIMETYPE_GA_FOLDER:
    return Ent.DRIVE_FOLDER
  if fileEntry['mimeType'].startswith(MIMETYPE_GA_3P_SHORTCUT):
    return Ent.DRIVE_3PSHORTCUT
  if fileEntry['mimeType'] != MIMETYPE_GA_SHORTCUT:
    return Ent.DRIVE_FILE
  if 'shortcutDetails' not in fileEntry or 'targetMimeType' not in fileEntry['shortcutDetails']:
    return Ent.DRIVE_SHORTCUT
  return Ent.DRIVE_FOLDER_SHORTCUT if fileEntry['shortcutDetails']['targetMimeType'] == MIMETYPE_GA_FOLDER else Ent.DRIVE_FILE_SHORTCUT

def _getTargetEntityMimeType(fileEntry):
  Ent = _getMain().Ent
  return Ent.DRIVE_FOLDER if fileEntry['shortcutDetails']['targetMimeType'] == MIMETYPE_GA_FOLDER else Ent.DRIVE_FILE

QUERY_SHORTCUTS_MAP = {
  'allfiles': f"mimeType != '{MIMETYPE_GA_FOLDER}'",
  'allfolders': f"mimeType = '{MIMETYPE_GA_FOLDER}'",
  'allforms': f"mimeType = '{MIMETYPE_GA_FORM}'",
  'allgooglefiles': f"mimeType != '{MIMETYPE_GA_FOLDER}' and mimeType contains 'vnd.google'",
  'allnongooglefiles': "not mimeType contains 'vnd.google'",
  'allshortcuts': f"mimeType = '{MIMETYPE_GA_SHORTCUT}'",
  'all3pshortcuts': f"mimeType = '{MIMETYPE_GA_3P_SHORTCUT}'",
  'allitems': 'allitems',
  'mycommentableitems': ME_IN_OWNERS_AND+f"(mimeType = '{MIMETYPE_GA_DOCUMENT}' or mimeType = '{MIMETYPE_GA_SPREADSHEET}' or mimeType = '{MIMETYPE_GA_PRESENTATION}')",
  'mydocs': ME_IN_OWNERS_AND+f"mimeType = '{MIMETYPE_GA_DOCUMENT}'",
  'myfiles': ME_IN_OWNERS_AND+f"mimeType != '{MIMETYPE_GA_FOLDER}'",
  'myfolders': ME_IN_OWNERS_AND+f"mimeType = '{MIMETYPE_GA_FOLDER}'",
  'myforms': ME_IN_OWNERS_AND+f"mimeType = '{MIMETYPE_GA_FORM}'",
  'mygooglefiles': ME_IN_OWNERS_AND+f"mimeType != '{MIMETYPE_GA_FOLDER}' and mimeType contains 'vnd.google'",
  'mynongooglefiles': ME_IN_OWNERS_AND+"not mimeType contains 'vnd.google'",
  'mypresentations': ME_IN_OWNERS_AND+f"mimeType = '{MIMETYPE_GA_PRESENTATION}'",
  'mypublishableitems': ME_IN_OWNERS_AND+f"(mimeType = '{MIMETYPE_GA_DOCUMENT}' or mimeType = '{MIMETYPE_GA_SPREADSHEET}' or mimeType = '{MIMETYPE_GA_FORM}' or mimeType = '{MIMETYPE_GA_PRESENTATION}')",
  'mysheets': ME_IN_OWNERS_AND+f"mimeType = '{MIMETYPE_GA_SPREADSHEET}'",
  'myshortcuts': ME_IN_OWNERS_AND+f"mimeType = '{MIMETYPE_GA_SHORTCUT}'",
  'myslides': ME_IN_OWNERS_AND+f"mimeType = '{MIMETYPE_GA_PRESENTATION}'",
  'my3pshortcuts': ME_IN_OWNERS_AND+f"mimeType = '{MIMETYPE_GA_3P_SHORTCUT}'",
  'myitems': ME_IN_OWNERS,
  'mytopfiles': ME_IN_OWNERS_AND+f"mimeType != '{MIMETYPE_GA_FOLDER}' and 'root' in parents",
  'mytopfolders': ME_IN_OWNERS_AND+f"mimeType = '{MIMETYPE_GA_FOLDER}' and 'root' in parents",
  'mytopitems': ME_IN_OWNERS_AND+"'root' in parents",
  'othersfiles': NOT_ME_IN_OWNERS_AND+f"mimeType != '{MIMETYPE_GA_FOLDER}'",
  'othersfolders': NOT_ME_IN_OWNERS_AND+f"mimeType = '{MIMETYPE_GA_FOLDER}'",
  'othersforms': NOT_ME_IN_OWNERS_AND+f"mimeType = '{MIMETYPE_GA_FORM}'",
  'othersgooglefiles': NOT_ME_IN_OWNERS_AND+f"mimeType != '{MIMETYPE_GA_FOLDER}' and mimeType contains 'vnd.google'",
  'othersnongooglefiles': NOT_ME_IN_OWNERS_AND+"not mimeType contains 'vnd.google'",
  'othersshortcuts': NOT_ME_IN_OWNERS_AND+f"mimeType = '{MIMETYPE_GA_SHORTCUT}'",
  'others3pshortcuts': NOT_ME_IN_OWNERS_AND+f"mimeType = '{MIMETYPE_GA_3P_SHORTCUT}'",
  'othersitems': NOT_ME_IN_OWNERS,
  'writablefiles': f"'me' in writers and mimeType != '{MIMETYPE_GA_FOLDER}'",
  }
SHAREDDRIVE_QUERY_SHORTCUTS_MAP = {
  'allfiles': f"mimeType != '{MIMETYPE_GA_FOLDER}'",
  'allfolders': f"mimeType = '{MIMETYPE_GA_FOLDER}'",
  'allgooglefiles': f"mimeType != '{MIMETYPE_GA_FOLDER}' and mimeType contains 'vnd.google'",
  'allnongooglefiles': "not mimeType contains 'vnd.google'",
  'allitems': 'allitems',
  }

