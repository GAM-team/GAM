"""Group member management, display, add/remove/sync.

Part of the _groups_tmp sub-package."""

"""GAM group management."""

import re
import json
import sys

from gam.util.csv_pf import RI_ENTITY, RI_ROLE, RI_COUNT

from gam.util.entity import GROUP_ROLES_MAP

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

from util.csv_pf import RI_I, RI_COUNT, RI_ENTITY, RI_ITEM, RI_J, RI_JCOUNT, RI_ROLE

from gam.cmd.groups.groups import ALL_GROUP_MEMBER_TYPES, MEMBEROPTION_DISPLAYMATCH, MEMBEROPTION_GETDELIVERYSETTINGS, MEMBEROPTION_INCLUDEDERIVEDMEMBERSHIP, MEMBEROPTION_ISARCHIVED, MEMBEROPTION_ISSUSPENDED, MEMBEROPTION_MATCHPATTERN, MEMBEROPTION_MEMBERNAMES, MEMBEROPTION_NODUPLICATES, MEMBEROPTION_RECURSIVE, getGroupMemberTypes, GroupIsAbuseOrPostmaster, mapGroupEmailForSettings

def __getattr__(name):
  """Fall back to gam module for any undefined names."""
  main = _getMain()
  try:
    return getattr(main, name)
  except AttributeError:
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")

def initMemberOptions():
  return [False, False, False, False, None, None, False, None, True]

def getMemberMatchOptions(myarg, memberOptions):
  if myarg in {'memberemaildisplaypattern', 'memberemailskippattern'}:
    memberOptions[MEMBEROPTION_MATCHPATTERN] = _getMain().getREPattern(re.IGNORECASE)
    memberOptions[MEMBEROPTION_DISPLAYMATCH] = myarg == 'memberemaildisplaypattern'
  else:
    return False
  return True

def _checkMemberMatch(member, memberOptions):
  if not memberOptions[MEMBEROPTION_MATCHPATTERN]:
    return True
  if member['type'] != Ent.TYPE_CUSTOMER:
    if memberOptions[MEMBEROPTION_MATCHPATTERN].match(member['email']):
      return memberOptions[MEMBEROPTION_DISPLAYMATCH]
    return not memberOptions[MEMBEROPTION_DISPLAYMATCH]
  if memberOptions[MEMBEROPTION_MATCHPATTERN].match(member['id']):
    return memberOptions[MEMBEROPTION_DISPLAYMATCH]
  return not memberOptions[MEMBEROPTION_DISPLAYMATCH]

def _checkCIMemberMatch(member, memberOptions):
  if not memberOptions[MEMBEROPTION_MATCHPATTERN]:
    return True
  if memberOptions[MEMBEROPTION_MATCHPATTERN].match(member.get('preferredMemberKey', {}).get('id', '')):
    return memberOptions[MEMBEROPTION_DISPLAYMATCH]
  return not memberOptions[MEMBEROPTION_DISPLAYMATCH]

def initIPSGMGroupMemberDisplayOptions():
  return {Ent.ROLE_MEMBER: {'show': False, 'countOnly': False},
          Ent.ROLE_MANAGER: {'show': False, 'countOnly': False},
          Ent.ROLE_OWNER: {'show': False, 'countOnly': False},
          'totalCount': False,
          'categories': [], 'checkCategory': False, 'showCategory': False,
          'checkShowCategory': False,
          'internal': False, 'external': False,
          'internalDomains': 'all',
          'gs': None}

def getIPSGMGroupRolesMemberDisplayOptions(myarg, rolesSet, memberDisplayOptions):
  def setMemberDisplayOptionsRole():
    for role in rolesSet:
      memberDisplayOptions[role]['show'] = True

  if myarg in {'role', 'roles'}:
    for role in _getMain().getString(Cmd.OB_GROUP_ROLE_LIST).lower().replace(',', ' ').split():
      if role in _getMain().GROUP_ROLES_MAP:
        rolesSet.add(_getMain().GROUP_ROLES_MAP[role])
      else:
        _getMain().invalidChoiceExit(role, _getMain().GROUP_ROLES_MAP, True)
    setMemberDisplayOptionsRole()
  elif myarg in _getMain().GROUP_ROLES_MAP:
    rolesSet.add(_getMain().GROUP_ROLES_MAP[myarg])
    setMemberDisplayOptionsRole()
  elif myarg == 'members':
    role = Ent.ROLE_MEMBER
    rolesSet.add(role)
    memberDisplayOptions[role]['show'] = True
  elif myarg == 'managers':
    role = Ent.ROLE_MANAGER
    rolesSet.add(role)
    memberDisplayOptions[role]['show'] = True
  elif myarg == 'owners':
    role = Ent.ROLE_OWNER
    rolesSet.add(role)
    memberDisplayOptions[role]['show'] = True
  elif myarg == 'internal':
    memberDisplayOptions['internal'] = memberDisplayOptions['checkCategory'] = memberDisplayOptions['showCategory'] = True
  elif myarg == 'external':
    memberDisplayOptions['external'] = memberDisplayOptions['checkCategory'] = memberDisplayOptions['showCategory'] = True
  elif myarg == 'internaldomains':
    memberDisplayOptions['internalDomains'] = getString(Cmd.OB_DOMAIN_NAME_LIST).replace(',', ' ').lower()
  else:
    return False
  return True

def getPGGroupRolesMemberDisplayOptions(myarg, rolesSet, memberDisplayOptions):
  if myarg == 'memberscount':
    role = Ent.ROLE_MEMBER
    rolesSet.add(role)
    memberDisplayOptions[role]['show'] = True
    memberDisplayOptions[role]['countOnly'] = True
  elif myarg == 'managerscount':
    role = Ent.ROLE_MANAGER
    rolesSet.add(role)
    memberDisplayOptions[role]['show'] = True
    memberDisplayOptions[role]['countOnly'] = True
  elif myarg == 'ownerscount':
    role = Ent.ROLE_OWNER
    rolesSet.add(role)
    memberDisplayOptions[role]['show'] = True
    memberDisplayOptions[role]['countOnly'] = True
  elif myarg == 'totalcount':
    memberDisplayOptions['totalCount'] = True
  elif myarg == 'countsonly':
    for role in Ent.ROLE_LIST:
      memberDisplayOptions[role]['countOnly'] = True
  else:
    return getIPSGMGroupRolesMemberDisplayOptions(myarg, rolesSet, memberDisplayOptions)
  return True

def finalizeInternalDomains(cd, internalDomains):
  if internalDomains not in {'all', 'primary'}:
    internalDomains = set(internalDomains.split())
  else:
    if internalDomains == 'all':
      internalDomains = {domain['domainName'] for domain in _getDomainList(cd, GC.Values[GC.CUSTOMER_ID], 'domains(domainName)')}
    else:
      internalDomains = {domain['domainName'] for domain in _getDomainList(cd, GC.Values[GC.CUSTOMER_ID], 'domains(domainName,isPrimary)') if domain.get('isPrimary', False)}
  return internalDomains

def finalizeIPSGMGroupRolesMemberDisplayOptions(cd, memberDisplayOptions, verifyAllowExternal):
  if verifyAllowExternal:
    memberDisplayOptions['external'] = memberDisplayOptions['checkCategory'] = memberDisplayOptions['showCategory'] = True
    memberDisplayOptions['internal'] = False
  if memberDisplayOptions['showCategory']:
    memberDisplayOptions['gs'] = _getMain().buildGAPIObject(API.GROUPSSETTINGS)
  memberDisplayOptions['checkShowCategory'] = memberDisplayOptions['checkCategory'] or memberDisplayOptions['showCategory']
  if memberDisplayOptions['checkShowCategory']:
    memberDisplayOptions['internalDomains'] = finalizeInternalDomains(cd, memberDisplayOptions['internalDomains'])
  return memberDisplayOptions['showCategory'], memberDisplayOptions['checkShowCategory']

GROUP_FIELDS_CHOICE_MAP = {
  'admincreated': 'adminCreated',
  'aliases': ['aliases', 'nonEditableAliases'],
  'description': 'description',
  'directmemberscount': 'directMembersCount',
  'email': 'email',
  'id': 'id',
  'name': 'name',
  }
GROUP_INFO_PRINT_ORDER = ['id', 'name', 'description', 'directMembersCount', 'adminCreated']
INFO_GROUP_OPTIONS = {'nousers', 'groups'}

CIGROUP_FIELDS_CHOICE_MAP = {
  'additionalgroupkeys': 'additionalGroupKeys',
  'createtime': 'createTime',
  'description': 'description',
  'displayname': 'displayName',
  'dynamicgroupmetadata': 'dynamicGroupMetadata',
  'email': 'groupKey',
  'groupkey': 'groupKey',
  'id': 'name',
  'labels': 'labels',
  'name': 'displayName',
  'parent': 'parent',
  'updatetime': 'updateTime',
  }
CIGROUP_FULL_FIELDS = {'additionalGroupKeys', 'createTime', 'dynamicGroupMetadata', 'parent', 'updateTime'}
CIGROUP_FIELDS_WITH_CRS_NLS = {'description'}
CIGROUP_INFO_ORDER = ['id', 'name', 'description', 'createTime', 'updateTime',
                      'groupKey', 'additionalGroupKeys', 'labels', 'parent', 'dynamicGroupMetadata',
                      'SecuritySettings']
CIGROUP_PRINT_ORDER = ['id', 'name', 'description', 'createTime', 'updateTime',
                       'groupKey', 'additionalGroupKeys', 'parent', 'dynamicGroupMetadata',
                       'memberRestrictionQuery', 'memberRestrictionEvaluation']
CIGROUP_TIME_OBJECTS = {'createTime', 'updateTime', 'statusTime'}

def mapCIGroupFieldNames(group):
  if 'groupKey' in group:
    group['email'] = group['groupKey'].pop('id')
    if not group['groupKey']:
      group.pop('groupKey')
  if 'name' in group:
    group['id'] = group.pop('name')
  if 'displayName' in group:
    group['name'] = group.pop('displayName')

def _showCIGroup(group, groupEmail, i=0, count=0):
  _getMain().printEntity([Ent.CLOUD_IDENTITY_GROUP, groupEmail], i, count)
  mapCIGroupFieldNames(group)
  Ind.Increment()
  for key in CIGROUP_INFO_ORDER:
    if key not in group:
      continue
    value = group[key]
    if key == 'labels':
      for k, v in value.items():
        if v == '':
          value[k] = True
    if isinstance(value, (list, dict)):
      _getMain().showJSON(key, value, timeObjects=CIGROUP_TIME_OBJECTS)
    elif key not in CIGROUP_FIELDS_WITH_CRS_NLS:
      if key not in CIGROUP_TIME_OBJECTS:
        _getMain().printKeyValueList([key, value])
      else:
        _getMain().printKeyValueList([key, _getMain().formatLocalTime(value)])
    else:
      _getMain().printKeyValueWithCRsNLs(key, value)
  Ind.Decrement()

def infoGroups(entityList):
  def initGroupFieldsLists():
    if not groupFieldsLists['cd']:
      groupFieldsLists['cd'] = ['email']
    if not groupFieldsLists['ci']:
      groupFieldsLists['ci'] = []
    if not groupFieldsLists['gs']:
      groupFieldsLists['gs'] = []

  cd = _getMain().buildGAPIObject(API.DIRECTORY)
  ci = None
  getAliases = getUsers = True
  getCloudIdentity = getGroups = getSettings = False
  showDeprecatedAttributes = True
  FJQC = _getMain().FormatJSONQuoteChar()
  groups = []
  members = []
  groupFieldsLists = {'cd': None, 'ci': None, 'gs': None}
  isSuspended = isArchived = None
  rolesSet = set()
  typesSet = set()
  memberOptions = initMemberOptions()
  memberDisplayOptions = initIPSGMGroupMemberDisplayOptions()
  while Cmd.ArgumentsRemaining():
    myarg = _getMain().getArgument()
    if myarg == 'quick':
      getAliases = getUsers = False
    elif myarg == 'nousers':
      getUsers = False
    elif myarg == 'nodeprecated':
      showDeprecatedAttributes = not _getMain().getBoolean()
    elif myarg in _getMain().SUSPENDED_ARGUMENTS:
      isSuspended = _getMain()._getIsSuspended(myarg)
    elif myarg in _getMain().ARCHIVED_ARGUMENTS:
      isArchived = _getMain()._getIsArchived(myarg)
    elif myarg == 'noaliases':
      getAliases = False
    elif myarg == 'groups':
      getGroups = True
    elif getIPSGMGroupRolesMemberDisplayOptions(myarg, rolesSet, memberDisplayOptions):
      getUsers = True
    elif getGroupMemberTypes(myarg, typesSet):
      pass
    elif getMemberMatchOptions(myarg, memberOptions):
      pass
    elif myarg == 'basic':
      initGroupFieldsLists()
      for field in GROUP_FIELDS_CHOICE_MAP:
        _getMain().addFieldToFieldsList(field, GROUP_FIELDS_CHOICE_MAP, groupFieldsLists['cd'])
    elif myarg in {'ciallfields', 'allcifields'}:
      if not groupFieldsLists['ci']:
        groupFieldsLists['ci'] = []
      for field in CIGROUP_FIELDS_CHOICE_MAP:
        _getMain().addFieldToFieldsList(field, CIGROUP_FIELDS_CHOICE_MAP, groupFieldsLists['ci'])
    elif myarg in GROUP_FIELDS_CHOICE_MAP:
      initGroupFieldsLists()
      _getMain().addFieldToFieldsList(myarg, GROUP_FIELDS_CHOICE_MAP, groupFieldsLists['cd'])
    elif myarg in _getMain().GROUP_ATTRIBUTES_SET:
      initGroupFieldsLists()
      attrProperties = getGroupAttrProperties(myarg)
      groupFieldsLists['gs'].extend([attrProperties[0]])
    elif myarg == 'fields':
      initGroupFieldsLists()
      for field in _getMain()._getFieldsList():
        if field in GROUP_FIELDS_CHOICE_MAP:
          _getMain().addFieldToFieldsList(field, GROUP_FIELDS_CHOICE_MAP, groupFieldsLists['cd'])
        else:
          attrProperties = getGroupAttrProperties(field)
          if attrProperties is None:
            _getMain().invalidChoiceExit(field, list(GROUP_FIELDS_CHOICE_MAP)+list(_getMain().GROUP_ATTRIBUTES_SET), True)
          groupFieldsLists['gs'].extend([attrProperties[0]])
    elif myarg == 'cifields':
      initGroupFieldsLists()
      for field in _getMain()._getFieldsList():
        if field in CIGROUP_FIELDS_CHOICE_MAP:
          _getMain().addFieldToFieldsList(field, CIGROUP_FIELDS_CHOICE_MAP, groupFieldsLists['ci'])
        else:
          _getMain().invalidChoiceExit(field, list(CIGROUP_FIELDS_CHOICE_MAP), True)
# Ignore info user arguments that may have come from whatis
    elif myarg in _getMain().INFO_USER_OPTIONS:
      if myarg == 'schemas':
        _getMain().getString(Cmd.OB_SCHEMA_NAME_LIST)
    else:
      FJQC.GetFormatJSON(myarg)
  if isSuspended is not None and isArchived is not None:
    if isSuspended == isArchived:
      entityType = Ent.MEMBER_SUSPENDED_ARCHIVED if isSuspended else Ent.MEMBER_NOT_SUSPENDED_NOT_ARCHIVED
    else:
      entityType = Ent.MEMBER_SUSPENDED if isSuspended else Ent.MEMBER_ARCHIVED
  elif isSuspended is not None:
    entityType = Ent.MEMBER_SUSPENDED if isSuspended else Ent.MEMBER_NOT_SUSPENDED
  elif isArchived is not None:
    entityType = Ent.MEMBER_ARCHIVED if isArchived else Ent.MEMBER_NOT_ARCHIVED
  else:
    entityType = Ent.MEMBER
  if not typesSet:
    typesSet = ALL_GROUP_MEMBER_TYPES
  cdfields = _getMain().getFieldsFromFieldsList(groupFieldsLists['cd'])
  memberRoles = ','.join(sorted(rolesSet)) if rolesSet else None
  if groupFieldsLists['gs'] is None:
    getSettings = True
    gsfields = None
  elif groupFieldsLists['gs']:
    getSettings = True
    gsfields = _getMain().getFieldsFromFieldsList(groupFieldsLists['gs'])
  else:
    gsfields = None
  if getSettings:
    gs = _getMain().buildGAPIObject(API.GROUPSSETTINGS)
  if groupFieldsLists['ci']:
    getCloudIdentity = True
    cifields = _getMain().getFieldsFromFieldsList(groupFieldsLists['ci'])
    ci = _getMain().buildGAPIObject(API.CLOUDIDENTITY_GROUPS)
  else:
    cifields = None
  showCategory, checkShowCategory = finalizeIPSGMGroupRolesMemberDisplayOptions(cd, memberDisplayOptions, False)
  i = 0
  count = len(entityList)
  for group in entityList:
    i += 1
    ci, _, group = _getMain().convertGroupCloudIDToEmail(ci, group, i, count)
    try:
      basic_info = _getMain().callGAPI(cd.groups(), 'get',
                            throwReasons=GAPI.GROUP_GET_THROW_REASONS, retryReasons=GAPI.GROUP_GET_RETRY_REASONS,
                            groupKey=group, fields=cdfields)
      group = basic_info['email']
      if getCloudIdentity:
        _, name, groupEmail = _getMain().convertGroupEmailToCloudID(ci, group, i, count)
        if not name or not groupEmail:
          continue
        cigInfo = _getMain().callGAPI(ci.groups(), 'get',
                           throwReasons=GAPI.CIGROUP_GET_THROW_REASONS, retryReasons=GAPI.CIGROUP_RETRY_REASONS,
                           name=name, fields=cifields)
      else:
        cigInfo = {}
      settings = {}
      if getSettings and not GroupIsAbuseOrPostmaster(group):
 # Use email address retrieved from cd since GS API doesn't support uid
        settings = _getMain().callGAPI(gs.groups(), 'get',
                            throwReasons=GAPI.GROUP_SETTINGS_THROW_REASONS, retryReasons=GAPI.GROUP_SETTINGS_RETRY_REASONS,
                            groupUniqueId=mapGroupEmailForSettings(group), fields=gsfields)
      if getGroups:
        groups = _getMain().callGAPIpages(cd.groups(), 'list', 'groups',
                               throwReasons=GAPI.GROUP_LIST_USERKEY_THROW_REASONS,
                               retryReasons=GAPI.SERVICE_NOT_AVAILABLE_RETRY_REASONS,
                               userKey=group, orderBy='email', fields='nextPageToken,groups(name,email)')
      if getUsers:
        validRoles, listRoles, listFields = _getMain()._getRoleVerification(memberRoles, 'nextPageToken,members(email,id,role,status,type)')
        result = _getMain().callGAPIpages(cd.members(), 'list', 'members',
                               throwReasons=GAPI.MEMBERS_THROW_REASONS, retryReasons=GAPI.MEMBERS_RETRY_REASONS,
                               groupKey=group, roles=listRoles, fields=listFields, maxResults=GC.Values[GC.MEMBER_MAX_RESULTS])
        members = []
        for member in result:
          if ((member['type'] in typesSet) and
              _getMain()._checkMemberRoleIsSuspendedIsArchived(member, validRoles, isSuspended, isArchived) and
              _checkMemberMatch(member, memberOptions) and
              (not checkShowCategory or _getMain()._checkMemberCategory(member, memberDisplayOptions))):
            members.append(member)
      if FJQC.formatJSON:
        basic_info.update(settings)
        if cigInfo:
          basic_info['cloudIdentity'] = cigInfo
        if getGroups:
          basic_info['groups'] = groups
        if getUsers:
          basic_info['members'] = members
        _getMain().printLine(json.dumps(_getMain().cleanJSON(basic_info), ensure_ascii=False, sort_keys=True))
        continue
      _getMain().printEntity([Ent.GROUP, group], i, count)
      Ind.Increment()
      if cigInfo:
        _showCIGroup(cigInfo, None)
      _getMain().printEntity([Ent.GROUP_SETTINGS, None])
      Ind.Increment()
      for key in GROUP_INFO_PRINT_ORDER:
        if key not in basic_info:
          continue
        value = basic_info[key]
        if isinstance(value, list):
          _getMain().printKeyValueList([key, None])
          Ind.Increment()
          for val in value:
            _getMain().printKeyValueList([val])
          Ind.Decrement()
        elif key not in _getMain().GROUP_FIELDS_WITH_CRS_NLS:
          _getMain().printKeyValueList([key, value])
        else:
          _getMain().printKeyValueWithCRsNLs(key, value)
      if settings:
        for _, attr in sorted(_getMain().GROUP_SETTINGS_ATTRIBUTES.items()):
          key = attr[0]
          if key in settings:
            if key not in _getMain().GROUP_FIELDS_WITH_CRS_NLS:
              _getMain().printKeyValueList([key, settings[key]])
            else:
              _getMain().printKeyValueWithCRsNLs(key, settings[key])
        for key in _getMain().GROUP_MERGED_ATTRIBUTES_PRINT_ORDER:
          if key in settings:
            _getMain().printKeyValueList([key, settings[key]])
            Ind.Increment()
            showTitle = False
          else:
            showTitle = True
          if showDeprecatedAttributes:
            for _, subattr in sorted(_getMain().GROUP_MERGED_TO_COMPONENT_MAP[key].items()):
              subkey = subattr[0]
              if subkey in settings:
                if showTitle:
                  _getMain().printKeyValueList([key, ''])
                  Ind.Increment()
                  showTitle = False
                _getMain().printKeyValueList([subkey, settings[subkey]])
          if not showTitle:
            Ind.Decrement()
        if showDeprecatedAttributes:
          showTitle = True
          for _, attr in sorted(_getMain().GROUP_DEPRECATED_ATTRIBUTES.items()):
            subkey = attr[0]
            if subkey in settings:
              if showTitle:
                _getMain().printKeyValueList(['Deprecated', ''])
                Ind.Increment()
                showTitle = False
              if subkey != 'maxMessageBytes':
                _getMain().printKeyValueList([subkey, settings[subkey]])
              else:
                _getMain().printKeyValueList([subkey, _getMain().formatMaxMessageBytes(settings[subkey], _getMain().ONE_KILO_BYTES, _getMain().ONE_MEGA_BYTES)])
          if not showTitle:
            Ind.Decrement()
      Ind.Decrement()
      if getAliases:
        for up in ['aliases', 'nonEditableAliases']:
          aliases = basic_info.get(up, [])
          if aliases:
            _getMain().printEntitiesCount([Ent.NONEDITABLE_ALIAS, Ent.EMAIL_ALIAS][up == 'aliases'], aliases)
            Ind.Increment()
            for alias in aliases:
              _getMain().printKeyValueList(['alias', alias])
            Ind.Decrement()
      if getGroups:
        _getMain().printEntitiesCount(Ent.GROUP, groups)
        Ind.Increment()
        for groupm in groups:
          _getMain().printKeyValueList([groupm['name'], groupm['email']])
        Ind.Decrement()
      if getUsers:
        _getMain().printEntitiesCount(entityType, members)
        Ind.Increment()
        for member in members:
          memberDetails = [member.get('role', Ent.ROLE_MEMBER).lower(), f'{member.get("email", member["id"])} ({member["type"].lower()})']
          if showCategory:
            memberDetails[1] += f' ({member["category"]})'
          _getMain().printKeyValueList(memberDetails)
        Ind.Decrement()
        _getMain().printKeyValueList([Msg.TOTAL_ITEMS_IN_ENTITY.format(Ent.Plural(entityType), Ent.Singular(Ent.GROUP)), len(members)])
      Ind.Decrement()
    except GAPI.notFound:
      _getMain().entityActionFailedWarning([Ent.GROUP, group], Msg.DOES_NOT_EXIST, i, count)
    except (GAPI.groupNotFound, GAPI.resourceNotFound, GAPI.domainNotFound, GAPI.domainCannotUseApis, GAPI.backendError,
            GAPI.invalid, GAPI.invalidArgument, GAPI.invalidMember, GAPI.invalidParameter, GAPI.invalidInput, GAPI.forbidden,
            GAPI.badRequest, GAPI.permissionDenied, GAPI.systemError, GAPI.serviceLimit, GAPI.serviceNotAvailable, GAPI.authError) as e:
      _getMain().entityActionFailedWarning([Ent.GROUP, group], str(e), i, count)

# gam info groups <GroupEntity>
#	[nousers] [quick] [noaliases] [groups]
#	[basic] <GroupFieldName>* [fields <GroupFieldNameList>] [nodeprecated]
#	[ciallfields|(cifields <CIGroupFieldNameList>)]
#	[roles <GroupRoleList>] [members] [managers] [owners]
#	[internal] [internaldomains all|primary|<DomainNameList>] [external]
#	[notsuspended|suspended] [notarchived|archived]
#	[types <GroupMemberTypeList>]
#	[memberemaildisplaypattern|memberemailskippattern <REMatchPattern>]
#	[formatjson]
def doInfoGroups():
  infoGroups(_getMain().getEntityList(Cmd.OB_GROUP_ENTITY))

def groupFilters(kwargs, query):
  queryTitle = ''
  if kwargs.get('domain'):
    queryTitle += f'domain={kwargs["domain"]}, '
  if query is not None:
    queryTitle += f'query="{query}", '
  if queryTitle:
    return query, queryTitle[:-2]
  return query, queryTitle

def getGroupFilters(myarg, kwargsDict, showOwnedBy):
  if _getMain().getUserGroupDomainQueryFilters(myarg, kwargsDict):
    pass
  elif myarg in {'member', 'showownedby'}:
    emailAddressOrUID = _getMain().getEmailAddress()
    if emailAddressOrUID != GC.Values[GC.CUSTOMER_ID].lower():
      kwargsDict['queries'] = [f'memberKey={emailAddressOrUID}']
      key = 'email' if emailAddressOrUID.find('@') != -1 else 'id'
    else:
      kwargsDict['queries'] = [f'memberKey={GC.Values[GC.CUSTOMER_ID]}']
      key = 'id'
    if myarg == 'showownedby':
      showOwnedBy['key'] = key
      showOwnedBy['value'] = emailAddressOrUID
  else:
    return False
  return True

def checkGroupShowOwnedBy(showOwnedBy, members):
  for member in members:
    if (member.get('role', Ent.ROLE_MEMBER) == Ent.ROLE_OWNER) and (member.get(showOwnedBy['key'], '').lower() == showOwnedBy['value']):
      return True
  return False

def getGroupMatchPatterns(myarg, matchPatterns, ciGroupsAPI):
  if myarg == 'emailmatchpattern':
    matchPatterns['email'] = {'not': checkArgumentPresent('not'), 'pattern': _getMain().getREPattern(re.IGNORECASE)}
  elif myarg == 'namematchpattern':
    matchPatterns['name' if not ciGroupsAPI else 'displayName'] = {'not': checkArgumentPresent('not'), 'pattern': _getMain().getREPattern(re.IGNORECASE|re.UNICODE)}
  elif myarg == 'descriptionmatchpattern':
    matchPatterns['description'] = {'not': checkArgumentPresent('not'), 'pattern': _getMain().getREPattern(re.IGNORECASE|re.UNICODE)}
  elif not ciGroupsAPI and myarg == 'admincreatedmatch':
    matchPatterns['adminCreated'] = _getMain().getBoolean(None)
  else:
    return False
  return True

def updateFieldsForGroupMatchPatterns(matchPatterns, fieldsList, csvPF=None):
  for field in ['name', 'description', 'adminCreated']:
    if field in matchPatterns:
      if csvPF is not None:
        csvPF.AddField(field, GROUP_FIELDS_CHOICE_MAP, fieldsList)
      else:
        fieldsList.append(field)

def clearUnneededGroupMatchPatterns(matchPatterns):
  for field in ['name', 'displayName', 'description', 'adminCreated']:
    matchPatterns.pop(field, None)

def checkGroupMatchPatterns(groupEmail, group, matchPatterns):
  for field, matchp in matchPatterns.items():
    if field == 'email':
      if not matchp['not']:
        if not matchp['pattern'].match(groupEmail):
          return False
      else:
        if matchp['pattern'].match(groupEmail):
          return False
    elif field == 'adminCreated':
      if matchp != group[field]:
        return False
    else: # field in {'name', 'displayName', 'description'}:
      if not matchp['not']:
        if not matchp['pattern'].match(group.get(field, '')):
          return False
      else:
        if matchp['pattern'].match(group.get(field, '')):
          return False
  return True

MEMBERS_TITLES = {
  'combined': {
    'total': ['TotalCount', ''],
    Ent.ROLE_MEMBER: ['MembersCount', 'Members'],
    Ent.ROLE_MANAGER: ['ManagersCount', 'Managers'],
    Ent.ROLE_OWNER: ['OwnersCount', 'Owners']
    },
  'internal': {
    'total': ['TotalInternalCount', ''],
    Ent.ROLE_MEMBER: ['InternalMembersCount', 'InternalMembers'],
    Ent.ROLE_MANAGER: ['InternalManagersCount', 'InternalManagers'],
    Ent.ROLE_OWNER: ['InternalOwnersCount', 'InternalOwners']
    },
  'external': {
    'total': ['TotalExternalCount', ''],
    Ent.ROLE_MEMBER: ['ExternalMembersCount', 'ExternalMembers'],
    Ent.ROLE_MANAGER: ['ExternalManagersCount', 'ExternalManagers'],
    Ent.ROLE_OWNER: ['ExternalOwnersCount', 'ExternalOwners']
    }
  }

def setMemberDisplayTitles(memberDisplayOptions, csvPF):
  if memberDisplayOptions['totalCount']:
    csvPF.AddTitles(MEMBERS_TITLES['combined']['total'][0])
  if not memberDisplayOptions['internal'] and not memberDisplayOptions['external']:
    memberDisplayOptions['categories'].append('combined')
  else:
    if memberDisplayOptions['internal']:
      memberDisplayOptions['categories'].append('internal')
    if memberDisplayOptions['external']:
      memberDisplayOptions['categories'].append('external')
  for category in memberDisplayOptions['categories']:
    if memberDisplayOptions['totalCount'] and category != 'combined':
      csvPF.AddTitles(MEMBERS_TITLES[category]['total'][0])
    for role in Ent.ROLE_LIST:
      if memberDisplayOptions[role]['show']:
        csvPF.AddTitles(MEMBERS_TITLES[category][role][0])
        if not memberDisplayOptions[role]['countOnly']:
          csvPF.AddTitles(MEMBERS_TITLES[category][role][1])

def setMemberDisplaySortTitles(memberDisplayOptions, sortTitles):
  if memberDisplayOptions['totalCount']:
    sortTitles.append(MEMBERS_TITLES['combined']['total'][0])
  for category in memberDisplayOptions['categories']:
    if memberDisplayOptions['totalCount'] and category != 'combined':
      sortTitles.append(MEMBERS_TITLES[category]['total'][0])
    for role in Ent.ROLE_LIST:
      if memberDisplayOptions[role]['show']:
        sortTitles.append(MEMBERS_TITLES[category][role][0])
      if not memberDisplayOptions[role]['countOnly']:
        sortTitles.append(MEMBERS_TITLES[category][role][1])

def addMemberInfoToRow(row, groupMembers, typesSet, memberOptions, memberDisplayOptions, delimiter,
                       isSuspended, isArchived, ciGroupsAPI):
  membersInfo = {
    'combined': {'totalTitle': 'TotalCount',
                 Ent.ROLE_MEMBER: {'titles': ['MembersCount', 'Members'],
                                   'count': 0, 'email': []},
                 Ent.ROLE_MANAGER: {'titles': ['ManagersCount', 'Managers'],
                                    'count': 0, 'email': []},
                 Ent.ROLE_OWNER: {'titles': ['OwnersCount', 'Owners'],
                                  'count': 0, 'email': []}},
    'internal': {'totalTitle': 'TotalInternalCount',
                 Ent.ROLE_MEMBER: {'titles': ['InternalMembersCount', 'InternalMembers'],
                                   'count': 0, 'email': []},
                 Ent.ROLE_MANAGER: {'titles': ['InternalManagersCount', 'InternalManagers'],
                                    'count': 0, 'email': []},
                 Ent.ROLE_OWNER: {'titles': ['InternalOwnersCount', 'InternalOwners'],
                                  'count': 0, 'email': []}},
    'external': {'totalTitle': 'TotalExternalCount',
                 Ent.ROLE_MEMBER: {'titles': ['ExternalMembersCount', 'ExternalMembers'],
                                   'count': 0, 'email': []},
                 Ent.ROLE_MANAGER: {'titles': ['ExternalManagersCount', 'ExternalManagers'],
                                    'count': 0, 'email': []},
                 Ent.ROLE_OWNER: {'titles': ['ExternalOwnersCount', 'ExternalOwners'],
                                  'count': 0, 'email': []}}}
  _checkMatch = _checkMemberMatch if not ciGroupsAPI else _checkCIMemberMatch
  for member in groupMembers:
    if not ciGroupsAPI:
      member_email = member.get('email', member.get('id', None))
    else:
      member_email = member.get('preferredMemberKey', {}).get('id', member['name'])
    if not member_email:
      _getMain().writeStderr(f' Not sure what to do with: {member}\n')
      continue
    if not memberDisplayOptions['showCategory']:
      category = 'combined'
    else:
      if member_email.find('@') > 0:
        _, domain = member_email.lower().split('@', 1)
        category = 'internal' if domain in memberDisplayOptions['internalDomains'] else 'external'
      else:
        category = 'internal'
      if not memberDisplayOptions[category]:
        continue
    if ((member['type'] in typesSet) and
        (ciGroupsAPI or _getMain()._checkMemberIsSuspendedIsArchived(member, isSuspended, isArchived)) and
        _checkMatch(member, memberOptions)):
      role = member.get('role', Ent.ROLE_MEMBER)
      if role not in {Ent.ROLE_MEMBER, Ent.ROLE_MANAGER, Ent.ROLE_OWNER}:
        role = Ent.ROLE_MEMBER
      if memberDisplayOptions[role]['show']:
        membersInfo[category][role]['count'] += 1
        if not memberDisplayOptions[role]['countOnly']:
          membersInfo[category][role]['email'].append(member_email)
  totalCount = 0
  for category in memberDisplayOptions['categories']:
    categoryCount = 0
    for role in Ent.ROLE_LIST:
      if memberDisplayOptions[role]['show']:
        categoryCount += membersInfo[category][role]['count']
        row[membersInfo[category][role]['titles'][0]] = membersInfo[category][role]['count']
        if not memberDisplayOptions[role]['countOnly']:
          row[membersInfo[category][role]['titles'][1]] = delimiter.join(membersInfo[category][role]['email'])
    if memberDisplayOptions['totalCount'] and category != 'combined':
      row[membersInfo[category]['totalTitle']] = categoryCount
    totalCount += categoryCount
  if memberDisplayOptions['totalCount']:
    row['TotalCount'] = totalCount

# gam print groups [todrive <ToDriveAttribute>*]
#	[([domain|domains <DomainNameEntity>] ([member|showownedby <EmailItem>]|[(query <QueryGroup>)|(queries <QueryUserList>)]))|
#	 (group|group_ns|group_susp <GroupItem>)|
#	 (select <GroupEntity>)]
#	[emailmatchpattern [not] <REMatchPattern>] [namematchpattern [not] <REMatchPattern>]
#	[descriptionmatchpattern [not] <REMatchPattern>] (matchsetting [not] <GroupAttribute>)*
#	[admincreatedmatch <Boolean>]
#	[maxresults <Number>]
#	[allfields|([basic] [settings] <GroupFieldName>* [fields <GroupFieldNameList>])]
#	[ciallfields|(cifields <CIGroupFieldNameList>)]
#	[nodeprecated]
#	[roles <GroupRoleList>]
#	[members|memberscount] [managers|managerscount] [owners|ownerscount] [totalcount] [countsonly]
#	[internal] [internaldomains all|primary|<DomainNameList>] [external]
#	[includederivedmembership]
#	[notsuspended|suspended] [notarchived|archived]
#	[types <GroupMemberTypeList>]
#	[memberemaildisplaypattern|memberemailskippattern <REMatchPattern>]
#	[convertcrnl] [delimiter <Character>] [sortheaders]
#	(addcsvdata <FieldName> <String>)* [includecsvdatainjson [<Boolean>]]
#	[formatjson [quotechar <Character>]]
# 	[showitemcountonly]
def doPrintGroups():
  def _printGroupRow(groupEntity, groupSettings, groupMembers):
    nonlocal itemCount
    row = {}
    if matchSettings:
      if not isinstance(groupSettings, dict):
        return
      for key, matchp in matchSettings.items():
        gvalue = groupSettings.get(key)
        if matchp['notvalues'] and gvalue in matchp['notvalues']:
          return
        if matchp['values'] and gvalue not in matchp['values']:
          return
    if showOwnedBy and not checkGroupShowOwnedBy(showOwnedBy, groupMembers):
      return
    if showItemCountOnly:
      itemCount += 1
      return
    if deprecatedAttributesSet and isinstance(groupSettings, dict):
      deprecatedKeys = []
      for key in groupSettings:
        if key in deprecatedAttributesSet:
          deprecatedKeys.append(key)
      for key in deprecatedKeys:
        groupSettings.pop(key)
    if addCSVData:
      row.update(addCSVData)
    if FJQC.formatJSON:
      row['email'] = groupEntity['email']
      if addCSVData and includeCSVDataInJSON:
        groupEntity.update(addCSVData)
      row['JSON'] = json.dumps(_getMain().cleanJSON(groupEntity), ensure_ascii=False, sort_keys=True)
      if rolesSet and groupMembers is not None:
        row['JSON-members'] = json.dumps(groupMembers, ensure_ascii=False, sort_keys=True)
      if isinstance(groupSettings, dict):
        row['JSON-settings'] = json.dumps(_getMain().cleanJSON(groupSettings), ensure_ascii=False, sort_keys=True)
      groupCloudIdentity = ciGroups.get(row['email'], {})
      if groupCloudIdentity:
        row['JSON-cloudIdentity'] = json.dumps(_getMain().cleanJSON(groupCloudIdentity, timeObjects=CIGROUP_TIME_OBJECTS), ensure_ascii=False, sort_keys=True)
      csvPF.WriteRowNoFilter(row)
      return
    for field in groupFieldsLists['cd']:
      if field in groupEntity:
        if isinstance(groupEntity[field], list):
          row[field] = delimiter.join(groupEntity[field])
        elif convertCRNL and field in _getMain().GROUP_FIELDS_WITH_CRS_NLS:
          row[field] = _getMain().escapeCRsNLs(groupEntity[field])
        else:
          row[field] = groupEntity[field]
    if rolesSet and groupMembers is not None:
      addMemberInfoToRow(row, groupMembers, typesSet, memberOptions, memberDisplayOptions, delimiter,
                         isSuspended, isArchived, False)
    if isinstance(groupSettings, dict):
      for key, value in groupSettings.items():
        if key not in {'kind', 'etag', 'email', 'name', 'description'}:
          if value is None:
            value = ''
          csvPF.AddTitles(key)
          if convertCRNL and key in _getMain().GROUP_FIELDS_WITH_CRS_NLS:
            row[key] = _getMain().escapeCRsNLs(value)
          else:
            row[key] = value
    groupCloudEntity = ciGroups.get(row['email'], {})
    if groupCloudEntity:
      for k, v in groupCloudEntity.pop('labels', {}).items():
        if v == '':
          groupCloudEntity[f'labels{GC.Values[GC.CSV_OUTPUT_SUBFIELD_DELIMITER]}{k}'] = True
        else:
          groupCloudEntity[f'labels{GC.Values[GC.CSV_OUTPUT_SUBFIELD_DELIMITER]}{k}'] = v
      for key, value in sorted(_getMain().flattenJSON({'cloudIdentity': groupCloudEntity}, flattened={}, timeObjects=CIGROUP_TIME_OBJECTS).items()):
        csvPF.AddTitles(key)
        row[key] = value
    csvPF.WriteRow(row)

  def _callbackProcessGroupBasic(request_id, response, exception):
    ri = request_id.splitlines()
    i = int(ri[RI_I])
    if exception is not None:
      http_status, reason, message = _getMain().checkGAPIError(exception)
      if reason not in GAPI.DEFAULT_RETRY_REASONS+GAPI.GROUP_GET_RETRY_REASONS:
        if reason in GAPI.GROUP_GET_THROW_REASONS:
          _getMain().entityUnknownWarning(Ent.GROUP, ri[RI_ENTITY], i, int(ri[RI_COUNT]))
        else:
          errMsg = _getMain().getHTTPError({}, http_status, reason, message)
          _getMain().entityActionFailedWarning([Ent.GROUP, ri[RI_ENTITY], Ent.GROUP, None], errMsg, i, int(ri[RI_COUNT]))
        return
      _getMain().waitOnFailure(1, 10, reason, message)
      try:
        response = _getMain().callGAPI(cd.groups(), 'get',
                            throwReasons=GAPI.GROUP_GET_THROW_REASONS, retryReasons=GAPI.GROUP_GET_RETRY_REASONS,
                            groupKey=ri[RI_ENTITY], fields=cdfields)
      except (GAPI.groupNotFound, GAPI.domainNotFound, GAPI.domainCannotUseApis, GAPI.forbidden, GAPI.badRequest, GAPI.invalid, GAPI.systemError) as e:
        _getMain().entityActionFailedWarning([Ent.GROUP, ri[RI_ENTITY], Ent.GROUP, None], str(e), i, int(ri[RI_COUNT]))
        return
    entityList.append(response)

  def _callbackProcessGroupMembers(request_id, response, exception):
    ri = request_id.splitlines()
    i = int(ri[RI_I])
    totalItems = 0
    items = 'members'
    pageMessage = _getMain().getPageMessageForWhom(forWhom=ri[RI_ENTITY], showFirstLastItems=True)
    if exception is not None:
      http_status, reason, message = _getMain().checkGAPIError(exception)
      if reason not in GAPI.DEFAULT_RETRY_REASONS+GAPI.MEMBERS_RETRY_REASONS:
        errMsg = _getMain().getHTTPError({}, http_status, reason, message)
        _getMain().entityActionFailedWarning([Ent.GROUP, ri[RI_ENTITY], ri[RI_ROLE], None], errMsg, i, int(ri[RI_COUNT]))
        groupData[i]['required'] -= 1
        return
      _getMain().waitOnFailure(1, 10, reason, message)
      try:
        response = _getMain().callGAPI(cd.members(), 'list',
                            throwReasons=GAPI.MEMBERS_THROW_REASONS, retryReasons=GAPI.MEMBERS_RETRY_REASONS,
                            includeDerivedMembership=memberOptions[MEMBEROPTION_INCLUDEDERIVEDMEMBERSHIP],
                            groupKey=ri[RI_ENTITY], roles=ri[RI_ROLE], fields='nextPageToken,members(email,id,role,type,status)',
                            maxResults=GC.Values[GC.MEMBER_MAX_RESULTS])
      except (GAPI.groupNotFound, GAPI.domainNotFound, GAPI.invalid, GAPI.forbidden, GAPI.serviceNotAvailable) as e:
        _getMain().entityActionFailedWarning([Ent.GROUP, ri[RI_ENTITY], ri[RI_ROLE], None], str(e), i, int(ri[RI_COUNT]))
        groupData[i]['required'] -= 1
        return
    while True:
      pageToken, totalItems = _getMain()._processGAPIpagesResult(response, items, groupData[i][items], totalItems, pageMessage, 'email', ri[RI_ROLE])
      if not pageToken:
        _getMain()._finalizeGAPIpagesResult(pageMessage)
        break
      try:
        response = _getMain().callGAPI(cd.members(), 'list',
                            throwReasons=GAPI.MEMBERS_THROW_REASONS, retryReasons=GAPI.MEMBERS_RETRY_REASONS,
                            pageToken=pageToken,
                            includeDerivedMembership=memberOptions[MEMBEROPTION_INCLUDEDERIVEDMEMBERSHIP],
                            groupKey=ri[RI_ENTITY], roles=ri[RI_ROLE], fields='nextPageToken,members(email,id,role,type,status)',
                            maxResults=GC.Values[GC.MEMBER_MAX_RESULTS])
      except (GAPI.groupNotFound, GAPI.domainNotFound, GAPI.invalid, GAPI.forbidden, GAPI.serviceNotAvailable) as e:
        _getMain().entityActionFailedWarning([Ent.GROUP, ri[RI_ENTITY], ri[RI_ROLE], None], str(e), i, int(ri[RI_COUNT]))
        break
    groupData[i]['required'] -= 1

  def _callbackProcessGroupSettings(request_id, response, exception):
    ri = request_id.splitlines()
    i = int(ri[RI_I])
    if exception is not None:
      http_status, reason, message = _getMain().checkGAPIError(exception)
      if reason not in GAPI.DEFAULT_RETRY_REASONS+GAPI.GROUP_SETTINGS_RETRY_REASONS:
        errMsg = _getMain().getHTTPError({}, http_status, reason, message)
        _getMain().entityActionFailedWarning([Ent.GROUP, ri[RI_ENTITY], Ent.GROUP_SETTINGS, None], errMsg, i, int(ri[RI_COUNT]))
        groupData[i]['required'] -= 1
        return
      _getMain().waitOnFailure(1, 10, reason, message)
      try:
        response = _getMain().callGAPI(gs.groups(), 'get',
                            throwReasons=GAPI.GROUP_SETTINGS_THROW_REASONS, retryReasons=GAPI.GROUP_SETTINGS_RETRY_REASONS,
                            groupUniqueId=mapGroupEmailForSettings(ri[RI_ENTITY]), fields=gsfields)
      except GAPI.notFound:
        _getMain().entityActionFailedWarning([Ent.GROUP, ri[RI_ENTITY], Ent.GROUP_SETTINGS, None], Msg.DOES_NOT_EXIST, i, int(ri[RI_COUNT]))
        response = {}
      except (GAPI.groupNotFound, GAPI.domainNotFound, GAPI.domainCannotUseApis, GAPI.forbidden,
              GAPI.backendError, GAPI.invalid, GAPI.invalidParameter, GAPI.invalidInput, GAPI.badRequest, GAPI.permissionDenied,
              GAPI.systemError, GAPI.serviceLimit, GAPI.serviceNotAvailable, GAPI.authError) as e:
        _getMain().entityActionFailedWarning([Ent.GROUP, ri[RI_ENTITY], Ent.GROUP_SETTINGS, None], str(e), i, int(ri[RI_COUNT]))
        response = {}
    groupData[i]['settings'] = response
    groupData[i]['required'] -= 1

  def _writeCompleteRows():
    complete = [k for k in groupData if groupData[k]['required'] == 0]
    for k in complete:
      _printGroupRow(groupData[k]['entity'], groupData[k]['settings'], groupData[k]['members'])
      del groupData[k]

  cd = _getMain().buildGAPIObject(API.DIRECTORY)
  ci = None
  kwargsDict = _getMain().initUserGroupDomainQueryFilters()
  convertCRNL = GC.Values[GC.CSV_OUTPUT_CONVERT_CR_NL]
  delimiter = GC.Values[GC.CSV_OUTPUT_FIELD_DELIMITER]
  getCloudIdentity = getSettings = showCIgroupKey = sortHeaders = False
  memberDisplayOptions = initIPSGMGroupMemberDisplayOptions()
  maxResults = None
  groupFieldsLists = {'cd': ['email'], 'ci': [], 'gs': []}
  csvPF = _getMain().CSVPrintFile(groupFieldsLists['cd'])
  FJQC = _getMain().FormatJSONQuoteChar(csvPF)
  rolesSet = set()
  typesSet = set()
  memberOptions = initMemberOptions()
  entitySelection = isSuspended = isArchived = None
  showOwnedBy = {}
  matchPatterns = {}
  matchSettings = {}
  deprecatedAttributesSet = set()
  ciGroups = {}
  showItemCountOnly = False
  addCSVData = {}
  includeCSVDataInJSON = False
  while Cmd.ArgumentsRemaining():
    myarg = _getMain().getArgument()
    if myarg == 'todrive':
      csvPF.GetTodriveParameters()
    elif getGroupFilters(myarg, kwargsDict, showOwnedBy):
      pass
    elif getGroupMatchPatterns(myarg, matchPatterns, False):
      pass
    elif myarg in {'group', 'groupns', 'groupsusp'}:
      entitySelection = [_getMain().getString(Cmd.OB_EMAIL_ADDRESS)]
      if myarg == 'groupns':
        isSuspended = False
      elif myarg == 'groupsusp':
        isSuspended = True
    elif myarg == 'select':
      entitySelection = _getMain().getEntityList(Cmd.OB_GROUP_ENTITY)
    elif myarg in _getMain().SUSPENDED_ARGUMENTS:
      isSuspended = _getMain()._getIsSuspended(myarg)
    elif myarg in _getMain().ARCHIVED_ARGUMENTS:
      isArchived = _getMain()._getIsArchived(myarg)
    elif myarg == 'maxresults':
      maxResults = _getMain().getInteger(minVal=1, maxVal=200)
    elif myarg == 'nodeprecated':
      deprecatedAttributesSet.update([attr[0] for attr in _getMain().GROUP_DISCOVER_ATTRIBUTES.values()])
      deprecatedAttributesSet.update([attr[0] for attr in _getMain().GROUP_ASSIST_CONTENT_ATTRIBUTES.values()])
      deprecatedAttributesSet.update([attr[0] for attr in _getMain().GROUP_MODERATE_CONTENT_ATTRIBUTES.values()])
      deprecatedAttributesSet.update([attr[0] for attr in _getMain().GROUP_MODERATE_MEMBERS_ATTRIBUTES.values()])
      deprecatedAttributesSet.update([attr[0] for attr in _getMain().GROUP_DEPRECATED_ATTRIBUTES.values()])
    elif myarg in {'convertcrnl', 'converttextnl', 'convertfooternl'}:
      convertCRNL = True
    elif myarg == 'delimiter':
      delimiter = _getMain().getCharacter()
    elif myarg == 'basic':
      sortHeaders = True
      for field in GROUP_FIELDS_CHOICE_MAP:
        csvPF.AddField(field, GROUP_FIELDS_CHOICE_MAP, groupFieldsLists['cd'])
    elif myarg in {'ciallfields', 'allcifields'}:
      sortHeaders = True
      groupFieldsLists['ci'] = []
      for field in CIGROUP_FIELDS_CHOICE_MAP:
        _getMain().addFieldToFieldsList(field, CIGROUP_FIELDS_CHOICE_MAP, groupFieldsLists['ci'])
    elif myarg == 'settings':
      getSettings = sortHeaders = True
    elif myarg == 'allfields':
      getSettings = sortHeaders = True
      groupFieldsLists['cd'] = []
      groupFieldsLists['gs'] = []
      for field in GROUP_FIELDS_CHOICE_MAP:
        csvPF.AddField(field, GROUP_FIELDS_CHOICE_MAP, groupFieldsLists['cd'])
    elif myarg == 'sortheaders':
      sortHeaders = _getMain().getBoolean()
    elif myarg in GROUP_FIELDS_CHOICE_MAP:
      csvPF.AddField(myarg, GROUP_FIELDS_CHOICE_MAP, groupFieldsLists['cd'])
    elif myarg in _getMain().GROUP_ATTRIBUTES_SET:
      attrProperties = getGroupAttrProperties(myarg)
      csvPF.AddField(myarg, {myarg: attrProperties[0]}, groupFieldsLists['gs'])
    elif myarg == 'fields':
      for field in _getMain()._getFieldsList():
        if field in GROUP_FIELDS_CHOICE_MAP:
          csvPF.AddField(field, GROUP_FIELDS_CHOICE_MAP, groupFieldsLists['cd'])
        else:
          attrProperties = getGroupAttrProperties(field)
          if attrProperties is None:
            _getMain().invalidChoiceExit(field, list(GROUP_FIELDS_CHOICE_MAP)+list(_getMain().GROUP_ATTRIBUTES_SET), True)
          csvPF.AddField(field, {field: attrProperties[0]}, groupFieldsLists['gs'])
    elif myarg == 'cifields':
      for field in _getMain()._getFieldsList():
        if field in CIGROUP_FIELDS_CHOICE_MAP:
          _getMain().addFieldToFieldsList(field, CIGROUP_FIELDS_CHOICE_MAP, groupFieldsLists['ci'])
        else:
          _getMain().invalidChoiceExit(field, list(CIGROUP_FIELDS_CHOICE_MAP), True)
    elif myarg == 'matchsetting':
      valueList = _getMain().getChoice({'not': 'notvalues'}, mapChoice=True, defaultChoice='values')
      matchBody = {}
      getGroupAttrValue(_getMain().getString(Cmd.OB_FIELD_NAME).lower(), matchBody)
      for key, value in matchBody.items():
        matchSettings.setdefault(key, {'notvalues': [], 'values': []})
        matchSettings[key][valueList].append(value)
    elif getPGGroupRolesMemberDisplayOptions(myarg, rolesSet, memberDisplayOptions):
      pass
    elif getGroupMemberTypes(myarg, typesSet):
      pass
    elif getMemberMatchOptions(myarg, memberOptions):
      pass
    elif myarg == 'includederivedmembership':
      memberOptions[MEMBEROPTION_INCLUDEDERIVEDMEMBERSHIP] = True
    elif myarg == 'showitemcountonly':
      showItemCountOnly = True
    elif myarg == 'addcsvdata':
      _getMain().getAddCSVData(addCSVData)
    elif myarg == 'includecsvdatainjson':
      includeCSVDataInJSON = _getMain().getBoolean()
    else:
      FJQC.GetFormatJSONQuoteChar(myarg, False)
  if not typesSet:
    typesSet = ALL_GROUP_MEMBER_TYPES
  showCategory, _ = finalizeIPSGMGroupRolesMemberDisplayOptions(cd, memberDisplayOptions, False)
  if showCategory:
    groupFieldsLists['gs'].append('allowExternalMembers')
  updateFieldsForGroupMatchPatterns(matchPatterns, groupFieldsLists['cd'], csvPF)
  if groupFieldsLists['cd']:
    cdfields = ','.join(set(groupFieldsLists['cd']))
    cdfieldsnp = f'nextPageToken,groups({cdfields})'
  else:
    cdfields = cdfieldsnp = None
  if matchSettings:
    groupFieldsLists['gs'].extend(list(matchSettings))
  if groupFieldsLists['gs']:
    getSettings = True
    gsfields = ','.join(set(groupFieldsLists['gs']))
  else:
    gsfields = None
  if getSettings:
    gs = _getMain().buildGAPIObject(API.GROUPSSETTINGS)
  if groupFieldsLists['ci']:
    _getMain().setTrueCustomerId(cd)
    getCloudIdentity = True
    showCIgroupKey = 'groupKey' in groupFieldsLists['ci']
    if not showCIgroupKey:
      groupFieldsLists['ci'].append('groupKey(id)')
    cifields = ','.join(set(groupFieldsLists['ci']))
    ci = _getMain().buildGAPIObject(API.CLOUDIDENTITY_GROUPS)
  if FJQC.formatJSON:
    sortHeaders = False
    if showCategory:
      csvPF.AddJSONTitles(['allowExternalMembers'])
    if addCSVData:
      csvPF.AddJSONTitles(sorted(addCSVData.keys()))
    csvPF.AddJSONTitles('JSON')
    if rolesSet:
      csvPF.AddJSONTitle('JSON-members')
    if getSettings:
      csvPF.AddJSONTitle('JSON-settings')
    if getCloudIdentity:
      csvPF.AddJSONTitle('JSON-cloudIdentity')
  else:
    if showCategory:
      csvPF.AddTitles(['allowExternalMembers'])
    if addCSVData:
      csvPF.AddTitles(sorted(addCSVData.keys()))
    csvPF.SetSortAllTitles()
  getRolesSet = rolesSet.copy()
  if showOwnedBy:
    getRolesSet.add(Ent.ROLE_OWNER)
  getRoles = ','.join(sorted(getRolesSet))
  showDetails = getRoles or getSettings or getCloudIdentity
  if rolesSet:
    setMemberDisplayTitles(memberDisplayOptions, csvPF)
  if entitySelection is None:
    entityList = []
    for kwargsQuery in _getMain().makeUserGroupDomainQueryFilters(kwargsDict, None, None, None):
      kwargs = kwargsQuery[0]
      query  = kwargsQuery[1]
      query, pquery = groupFilters(kwargs, query)
      _getMain().printGettingAllAccountEntities(Ent.GROUP, pquery)
      try:
        entityList.extend(_getMain().callGAPIpages(cd.groups(), 'list', 'groups',
                                        pageMessage=_getMain().getPageMessage(showFirstLastItems=True), messageAttribute='email',
                                        throwReasons=GAPI.GROUP_LIST_USERKEY_THROW_REASONS,
                                        retryReasons=GAPI.SERVICE_NOT_AVAILABLE_RETRY_REASONS,
                                        orderBy='email', query=query, fields=cdfieldsnp, maxResults=maxResults, **kwargs))
      except (GAPI.invalidMember, GAPI.invalidInput) as e:
        if not _getMain().invalidMember(query):
          _getMain().entityActionFailedExit([Ent.GROUP, None], str(e))
      except (GAPI.resourceNotFound, GAPI.domainNotFound, GAPI.forbidden, GAPI.badRequest):
        if kwargs.get('domain'):
          _getMain().badRequestWarning(Ent.GROUP, Ent.DOMAIN, kwargs['domain'])
        else:
          accessErrorExit(cd)
  else:
    svcargs = dict([('groupKey', None), ('fields', cdfields)]+GM.Globals[GM.EXTRA_ARGS_LIST])
    cdmethod = getattr(cd.groups(), 'get')
    cdbatch = cd.new_batch_http_request(callback=_callbackProcessGroupBasic)
    cdbcount = 0
    entityList = []
    i = 0
    count = len(entitySelection)
    for groupEntity in entitySelection:
      i += 1
      groupEmail = _getMain().normalizeEmailAddressOrUID(groupEntity)
      svcparms = svcargs.copy()
      svcparms['groupKey'] = groupEmail
      _getMain().printGettingEntityItem(Ent.GROUP, groupEmail, i, count)
      cdbatch.add(cdmethod(**svcparms), request_id=_getMain().batchRequestID(groupEmail, i, count, 0, 0, None))
      cdbcount += 1
      if cdbcount >= GC.Values[GC.BATCH_SIZE]:
        _getMain().executeBatch(cdbatch)
        cdbatch = cd.new_batch_http_request(callback=_callbackProcessGroupBasic)
        cdbcount = 0
    if cdbcount > 0:
      cdbatch.execute()
  required = 0
  if getRoles:
    required += 1
    svcargs = dict([('groupKey', None), ('roles', getRoles), ('fields', 'nextPageToken,members(email,id,role,type,status)'),
                    ('includeDerivedMembership', memberOptions[MEMBEROPTION_INCLUDEDERIVEDMEMBERSHIP]),
                    ('maxResults', GC.Values[GC.MEMBER_MAX_RESULTS])]+GM.Globals[GM.EXTRA_ARGS_LIST])
  if getSettings:
    required += 1
    svcargsgs = dict([('groupUniqueId', None), ('fields', gsfields)]+GM.Globals[GM.EXTRA_ARGS_LIST])
  cdmethod = getattr(cd.members(), 'list')
  cdbatch = cd.new_batch_http_request(callback=_callbackProcessGroupMembers)
  cdbcount = 0
  if getSettings:
    gsmethod = getattr(gs.groups(), 'get')
    gsbatch = gs.new_batch_http_request(callback=_callbackProcessGroupSettings)
    gsbcount = 0
  groupData = {}
  itemCount = 0
  i = 0
  count = len(entityList)
  for groupEntity in entityList:
    i += 1
    groupEmail = groupEntity['email']
    if not checkGroupMatchPatterns(groupEmail, groupEntity, matchPatterns):
      continue
    if not showDetails:
      _printGroupRow(groupEntity, None, None)
      continue
    if getCloudIdentity:
      _, name, groupEmail = _getMain().convertGroupEmailToCloudID(ci, groupEmail, i, count)
      _getMain().printGettingEntityItemForWhom(Ent.CLOUD_IDENTITY_GROUP, groupEmail, i, count)
      if name and groupEmail:
        try:
          ciGroup = _getMain().callGAPI(ci.groups(), 'get',
                             throwReasons=GAPI.CIGROUP_GET_THROW_REASONS, retryReasons=GAPI.CIGROUP_RETRY_REASONS,
                             name=name, fields=cifields)
          key = ciGroup['groupKey']['id']
          if not showCIgroupKey:
            ciGroup.pop('groupKey')
          ciGroups[key] = ciGroup
        except (GAPI.notFound, GAPI.domainNotFound, GAPI.domainCannotUseApis,
                GAPI.forbidden, GAPI.badRequest, GAPI.invalid, GAPI.invalidArgument,
                GAPI.systemError, GAPI.permissionDenied, GAPI.serviceNotAvailable) as e:
          _getMain().entityActionFailedWarning([Ent.GROUP, groupEmail, Ent.CLOUD_IDENTITY_GROUP, None], str(e), i, count)
    groupData[i] = {'entity': groupEntity, 'cloudIdentity': {}, 'settings': getSettings, 'members': [], 'required': required}
    if getRoles:
      _getMain().printGettingEntityItemForWhom(getRoles, groupEmail, i, count)
      svcparms = svcargs.copy()
      svcparms['groupKey'] = groupEmail
      cdbatch.add(cdmethod(**svcparms), request_id=_getMain().batchRequestID(groupEmail, i, count, 0, 0, None, getRoles))
      cdbcount += 1
      if cdbcount >= GC.Values[GC.BATCH_SIZE]:
        _getMain().executeBatch(cdbatch)
        cdbatch = cd.new_batch_http_request(callback=_callbackProcessGroupMembers)
        cdbcount = 0
        _writeCompleteRows()
    if getSettings:
      if not GroupIsAbuseOrPostmaster(groupEmail):
        _getMain().printGettingEntityItemForWhom(Ent.GROUP_SETTINGS, groupEmail, i, count)
        svcparmsgs = svcargsgs.copy()
        svcparmsgs['groupUniqueId'] = mapGroupEmailForSettings(groupEmail)
        gsbatch.add(gsmethod(**svcparmsgs), request_id=_getMain().batchRequestID(groupEmail, i, count, 0, 0, None))
        gsbcount += 1
        if gsbcount >= GC.Values[GC.BATCH_SIZE]:
          _getMain().executeBatch(gsbatch)
          gsbatch = gs.new_batch_http_request(callback=_callbackProcessGroupSettings)
          gsbcount = 0
          _writeCompleteRows()
      else:
        groupData[i]['settings'] = False
        groupData[i]['required'] -= 1
  if cdbcount > 0:
    cdbatch.execute()
  if getSettings and gsbcount > 0:
    gsbatch.execute()
  _writeCompleteRows()
  if showItemCountOnly:
    _getMain().writeStdout(f'{itemCount}\n')
    return
  if sortHeaders:
    sortTitles = ['email']
    if showCategory:
      sortTitles.append('allowExternalMembers')
    if addCSVData:
      sortTitles.extend(sorted(addCSVData.keys()))
    sortTitles.extend(GROUP_INFO_PRINT_ORDER+['aliases', 'nonEditableAliases'])
    if getSettings:
      sortTitles += sorted([attr[0] for attr in _getMain().GROUP_SETTINGS_ATTRIBUTES.values()])
      for key in _getMain().GROUP_MERGED_ATTRIBUTES_PRINT_ORDER:
        sortTitles.append(key)
        if not deprecatedAttributesSet:
          sortTitles += sorted([attr[0] for attr in _getMain().GROUP_MERGED_TO_COMPONENT_MAP[key].values()])
      if not deprecatedAttributesSet:
        sortTitles += sorted([attr[0] for attr in _getMain().GROUP_DEPRECATED_ATTRIBUTES.values()])
    if rolesSet:
      setMemberDisplaySortTitles(memberDisplayOptions, sortTitles)
    csvPF.SetSortTitles(sortTitles)
  csvPF.SortRows('email', False)
  csvPF.writeCSVfile('Groups')

def mapCIGroupMemberFieldNames(member):
  member['email'] = member['preferredMemberKey'].pop('id')
  if not member['preferredMemberKey']:
    member.pop('preferredMemberKey')
  if 'name' in member:
    member['id'] = member.pop('name')

INFO_GROUPMEMBERS_FIELDS = ['role', 'type', 'status', 'delivery_settings']

# gam <UserTypeEntity> info member <GroupEntity>
def infoGroupMembers(entityList, ciGroupsAPI=False):
  if not ciGroupsAPI:
    cd = _getMain().buildGAPIObject(API.DIRECTORY)
    ci = None
    fieldsList = INFO_GROUPMEMBERS_FIELDS
    fields = ','.join(fieldsList)
  else:
    ci = _getMain().buildGAPIObject(API.CLOUDIDENTITY_GROUPS)
  entityType = GROUP_CIGROUP_ENTITYTYPE_MAP[ciGroupsAPI]
  groups = _getMain().getEntityList(Cmd.OB_GROUP_ENTITY)
  _getMain().checkForExtraneousArguments()
  groupsLists = groups if isinstance(groups, dict) else None
  i, count, entityList = _getMain().getEntityArgument(entityList)
  for user in entityList:
    i += 1
    memberKey = _getMain().normalizeEmailAddressOrUID(user)
    if groupsLists:
      groups = groupsLists[user]
    jcount = len(groups)
    _getMain().entityPerformActionNumItems([Ent.MEMBER, memberKey], jcount, entityType, i, count)
    Ind.Increment()
    j = 0
    for group in groups:
      j += 1
      if not ciGroupsAPI:
        try:
          ci, _, groupEmail = _getMain().convertGroupCloudIDToEmail(ci, group, i, count)
          result = _getMain().callGAPI(cd.members(), 'get',
                            throwReasons=GAPI.MEMBERS_THROW_REASONS+[GAPI.MEMBER_NOT_FOUND], retryReasons=GAPI.MEMBERS_RETRY_REASONS,
                            groupKey=groupEmail, memberKey=memberKey, fields=fields)
          result.setdefault('role', Ent.ROLE_MEMBER)
          _getMain().printEntity([entityType, groupEmail], j, jcount)
          Ind.Increment()
          for field in INFO_GROUPMEMBERS_FIELDS:
            _getMain().printKeyValueList([field, result[field]])
          Ind.Decrement()
        except (GAPI.groupNotFound, GAPI.domainNotFound, GAPI.domainCannotUseApis, GAPI.invalid, GAPI.forbidden, GAPI.serviceNotAvailable) as e:
          _getMain().entityActionFailedWarning([entityType, group], str(e), j, jcount)
        except GAPI.memberNotFound:
          _getMain().entityActionFailedWarning([entityType, group, Ent.MEMBER, memberKey], Msg.NOT_AN_ENTITY.format(Ent.Singular(Ent.MEMBER)), j, jcount)
      else:
        _, groupKey, groupEmail = _getMain().convertGroupEmailToCloudID(ci, group, j, jcount)
        if not groupKey or not groupEmail:
          continue
        try:
          memberName = _getMain().callGAPI(ci.groups().memberships(), 'lookup',
                                throwReasons=GAPI.GROUP_GET_THROW_REASONS+[GAPI.NOT_FOUND, GAPI.PERMISSION_DENIED],
                                parent=groupKey, memberKey_id=memberKey, fields='name').get('name')
          result = _getMain().callGAPI(ci.groups().memberships(), 'get',
                            name=memberName)
          _getMain().printEntity([entityType, groupEmail], j, jcount)
          Ind.Increment()
          _getMain().getCIGroupMemberRoleFixType(result)
          kvList = ['role', result['role']]
          if 'expireTime' in result:
            kvList.extend(['expireTime', formatLocalTime(result['expireTime'])])
          _getMain().printKeyValueList(kvList)
          _getMain().printKeyValueList(['type', result['type']])
          for field in ['createTime', 'updateTime']:
            _getMain().printKeyValueList([field, _getMain().formatLocalTime(result[field])])
          if 'deliverySetting' in result:
            _getMain().printKeyValueList(['deliverySetting', result['deliverySetting']])
          Ind.Decrement()
        except (GAPI.groupNotFound, GAPI.domainNotFound, GAPI.domainCannotUseApis, GAPI.invalid, GAPI.forbidden) as e:
          _getMain().entityActionFailedWarning([entityType, groupKey], str(e), j, jcount)
        except (GAPI.notFound, GAPI.memberNotFound, GAPI.permissionDenied):
          _getMain().entityActionFailedWarning([entityType, groupKey, Ent.MEMBER, memberKey], Msg.NOT_AN_ENTITY.format(Ent.Singular(Ent.MEMBER)), j, jcount)
    Ind.Decrement()

# gam info member <UserTypeEntity> <GroupEntity>
def doInfoGroupMembers():
  infoGroupMembers(_getMain().getEntityToModify(defaultEntityType=Cmd.ENTITY_USERS)[1], False)

def getGroupMembersEntityList(cd, entityList, matchPatterns, fieldsList, kwargsDict):
  if entityList is None:
    updateFieldsForGroupMatchPatterns(matchPatterns, fieldsList)
    entityList = []
    for kwargsQuery in _getMain().makeUserGroupDomainQueryFilters(kwargsDict, None, None, None):
      kwargs = kwargsQuery[0]
      query  = kwargsQuery[1]
      query, pquery = groupFilters(kwargs, query)
      _getMain().printGettingAllAccountEntities(Ent.GROUP, pquery)
      try:
        entityList.extend(_getMain().callGAPIpages(cd.groups(), 'list', 'groups',
                                        pageMessage=_getMain().getPageMessage(showFirstLastItems=True), messageAttribute='email',
                                        throwReasons=GAPI.GROUP_LIST_USERKEY_THROW_REASONS,
                                        retryReasons=GAPI.SERVICE_NOT_AVAILABLE_RETRY_REASONS,
                                        orderBy='email', query=query, fields=f'nextPageToken,groups({",".join(set(fieldsList))})', **kwargs))
      except (GAPI.invalidMember, GAPI.invalidInput) as e:
        if not _getMain().invalidMember(query):
          _getMain().entityActionFailedExit([Ent.GROUP, None], str(e))
      except (GAPI.resourceNotFound, GAPI.domainNotFound, GAPI.forbidden, GAPI.badRequest):
        if kwargs.get('domain'):
          _getMain().badRequestWarning(Ent.GROUP, Ent.DOMAIN, kwargs['domain'])
        else:
          accessErrorExit(cd)
  else:
    clearUnneededGroupMatchPatterns(matchPatterns)
  return entityList

def getGroupMembers(cd, groupEmail, memberRoles, membersList, membersSet, i, count,
                    memberOptions, memberDisplayOptions, level, typesSet):
  def _getMemberDeliverySettings(member):
    if 'delivery_settings' not in member:
      try:
        member['delivery_settings'] = _getMain().callGAPI(cd.members(), 'get',
                                               throwReasons=GAPI.MEMBERS_THROW_REASONS+[GAPI.MEMBER_NOT_FOUND],
                                               retryReasons=GAPI.MEMBERS_RETRY_REASONS,
                                               groupKey=groupEmail, memberKey=member['id'], fields='delivery_settings')['delivery_settings']
      except (GAPI.groupNotFound, GAPI.domainNotFound, GAPI.domainCannotUseApis, GAPI.invalid, GAPI.forbidden, GAPI.serviceNotAvailable):
        pass
      except GAPI.memberNotFound:
        pass
    else:
      memberOptions[MEMBEROPTION_GETDELIVERYSETTINGS] = False

  _getMain().printGettingAllEntityItemsForWhom(memberRoles if memberRoles else Ent.ROLE_MANAGER_MEMBER_OWNER, groupEmail, i, count)
  validRoles, listRoles, listFields = _getMain()._getRoleVerification(memberRoles, 'nextPageToken,members(email,id,role,status,type,delivery_settings)')
  if not groupEmail.startswith('space/'):
    try:
      groupMembers = _getMain().callGAPIpages(cd.members(), 'list', 'members',
                                   pageMessage=_getMain().getPageMessageForWhom(),
                                   throwReasons=GAPI.MEMBERS_THROW_REASONS, retryReasons=GAPI.MEMBERS_RETRY_REASONS,
                                   includeDerivedMembership=memberOptions[MEMBEROPTION_INCLUDEDERIVEDMEMBERSHIP],
                                   groupKey=groupEmail, roles=listRoles, fields=listFields, maxResults=GC.Values[GC.MEMBER_MAX_RESULTS])
    except (GAPI.groupNotFound, GAPI.domainNotFound, GAPI.domainCannotUseApis, GAPI.invalid, GAPI.forbidden, GAPI.serviceNotAvailable):
      _getMain().entityUnknownWarning(Ent.GROUP, groupEmail, i, count)
      return
  else:
    groupMembers =  _getMain()._getChatSpaceMembers(cd, groupEmail, '')
  checkShowCategory = memberDisplayOptions['checkShowCategory']
  if not memberOptions[MEMBEROPTION_RECURSIVE]:
    if memberOptions[MEMBEROPTION_NODUPLICATES]:
      for member in groupMembers:
        if (_getMain()._checkMemberRoleIsSuspendedIsArchived(member, validRoles, memberOptions[MEMBEROPTION_ISSUSPENDED], memberOptions[MEMBEROPTION_ISARCHIVED]) and
            (not checkShowCategory or _getMain()._checkMemberCategory(member, memberDisplayOptions)) and
            member['id'] not in membersSet):
          if memberOptions[MEMBEROPTION_GETDELIVERYSETTINGS]:
            _getMemberDeliverySettings(member)
          membersSet.add(member['id'])
          if member['type'] in typesSet and _checkMemberMatch(member, memberOptions):
            membersList.append(member)
    else:
      for member in groupMembers:
        if (_getMain()._checkMemberRoleIsSuspendedIsArchived(member, validRoles, memberOptions[MEMBEROPTION_ISSUSPENDED], memberOptions[MEMBEROPTION_ISARCHIVED]) and
            (not checkShowCategory or _getMain()._checkMemberCategory(member, memberDisplayOptions))):
          if memberOptions[MEMBEROPTION_GETDELIVERYSETTINGS]:
            _getMemberDeliverySettings(member)
          if member['type'] in typesSet and _checkMemberMatch(member, memberOptions):
            membersList.append(member)
  elif memberOptions[MEMBEROPTION_NODUPLICATES]:
    groupMemberList = []
    for member in groupMembers:
      if member['type'] != Ent.TYPE_GROUP:
        if ((member['type'] in typesSet and
             _checkMemberMatch(member, memberOptions) and
             _getMain()._checkMemberRoleIsSuspendedIsArchived(member, validRoles, memberOptions[MEMBEROPTION_ISSUSPENDED], memberOptions[MEMBEROPTION_ISARCHIVED]) and
             (not checkShowCategory or _getMain()._checkMemberCategory(member, memberDisplayOptions)) and
             member['id'] not in membersSet)):
          if memberOptions[MEMBEROPTION_GETDELIVERYSETTINGS]:
            _getMemberDeliverySettings(member)
          membersSet.add(member['id'])
          member['level'] = level
          member['subgroup'] = groupEmail
          membersList.append(member)
      else:
        if member['id'] not in membersSet:
          if memberOptions[MEMBEROPTION_GETDELIVERYSETTINGS]:
            _getMemberDeliverySettings(member)
          membersSet.add(member['id'])
          if (member['type'] in typesSet and
              _checkMemberMatch(member, memberOptions) and
              (not checkShowCategory or _getMain()._checkMemberCategory(member, memberDisplayOptions))):
            member['level'] = level
            member['subgroup'] = groupEmail
            membersList.append(member)
          groupMemberList.append(member['email'])
    for member in groupMemberList:
      getGroupMembers(cd, member, memberRoles, membersList, membersSet, i, count,
                      memberOptions, memberDisplayOptions, level+1, typesSet)
  else:
    for member in groupMembers:
      if member['type'] != Ent.TYPE_GROUP:
        if ((member['type'] in typesSet) and
            _checkMemberMatch(member, memberOptions) and
            _getMain()._checkMemberRoleIsSuspendedIsArchived(member, validRoles,
                                                  memberOptions[MEMBEROPTION_ISSUSPENDED],
                                                  memberOptions[MEMBEROPTION_ISARCHIVED]) and
            (not checkShowCategory or _getMain()._checkMemberCategory(member, memberDisplayOptions))):
          if memberOptions[MEMBEROPTION_GETDELIVERYSETTINGS]:
            _getMemberDeliverySettings(member)
          member['level'] = level
          member['subgroup'] = groupEmail
          membersList.append(member)
      else:
        if (member['type'] in typesSet and
            _checkMemberMatch(member, memberOptions) and
            (not checkShowCategory or _getMain()._checkMemberCategory(member, memberDisplayOptions))):
          member['level'] = level
          member['subgroup'] = groupEmail
          membersList.append(member)
        getGroupMembers(cd, member['email'], memberRoles, membersList, membersSet, i, count,
                        memberOptions, memberDisplayOptions, level+1, typesSet)

def getGroupAllowExternalMembers(gs, groupEmail, verifyAllowExternal, kvList, i, count):
  try:
    settings = _getMain().callGAPI(gs.groups(), 'get',
                        throwReasons=GAPI.GROUP_SETTINGS_THROW_REASONS, retryReasons=GAPI.GROUP_SETTINGS_RETRY_REASONS,
                        groupUniqueId=groupEmail, fields='allowExternalMembers')
    allowExternalMembers = settings['allowExternalMembers'] == 'true'
    if not verifyAllowExternal or not allowExternalMembers:
      return allowExternalMembers
    _getMain().entityActionNotPerformedWarning(kvList, 'allowExternalMembers=True', i, count)
  except GAPI.notFound:
    _getMain().entityActionFailedWarning(kvList, Msg.DOES_NOT_EXIST, i, count)
  except (GAPI.groupNotFound, GAPI.resourceNotFound, GAPI.domainNotFound, GAPI.domainCannotUseApis, GAPI.backendError,
          GAPI.invalid, GAPI.invalidMember, GAPI.invalidParameter, GAPI.invalidInput, GAPI.forbidden, GAPI.badRequest,
          GAPI.permissionDenied, GAPI.systemError, GAPI.serviceLimit, GAPI.serviceNotAvailable, GAPI.authError) as e:
    _getMain().entityActionFailedWarning(kvList, str(e), i, count)
  return None

GROUPMEMBERS_FIELDS_CHOICE_MAP = {
  'delivery': 'delivery_settings',
  'deliverysettings': 'delivery_settings',
  'email': 'email',
  'group': 'group',
  'groupemail': 'group',
  'id': 'id',
  'name': 'name',
  'role': 'role',
  'status': 'status',
  'type': 'type',
  'useremail': 'email',
  }

GROUPMEMBERS_DEFAULT_FIELDS = ['group', 'type', 'role', 'id', 'status', 'email']
GROUPMEMBERS_SORT_FIELDS = ['type', 'role', 'id', 'status', 'email']

# gam print group-members [todrive <ToDriveAttribute>*]
#	[([domain|domains <DomainNameEntity>] ([member|showownedby <EmailItem>]|[(query <QueryGroup>)|(queries <QueryUserList>)]))|
#	 (group|group_ns|group_susp <GroupItem>)|
#	 (select <GroupEntity>)]
#	[emailmatchpattern [not] <REMatchPattern>] [namematchpattern [not] <REMatchPattern>]
#	[descriptionmatchpattern [not] <REMatchPattern>]
#	[roles <GroupRoleList>] [members] [managers] [owners]
#	[internal] [internaldomains all|primary|<DomainNameList>] [external]
#	[notsuspended|suspended] [notarchived|archived]
#	[types <GroupMemberTypeList>]
#	[memberemaildisplaypattern|memberemailskippattern <REMatchPattern>]
#	[membernames] [showdeliverysettings]
#	<MembersFieldName>* [fields <MembersFieldNameList>]
#	[userfields <UserFieldNameList>]
#	[allschemas|(schemas|custom|customschemas <SchemaNameList>)]
#	[(recursive [noduplicates])|includederivedmembership] [nogroupemail]
#	[peoplelookup|(peoplelookupuser <EmailAddress>)]
#	[unknownname <String>] [cachememberinfo [Boolean]]
#	(addcsvdata <FieldName> <String>)* [includecsvdatainjson [<Boolean>]]
#	[formatjson [quotechar <Character>]]
def doPrintGroupMembers():
  def getNameFromPeople(memberId):
    try:
      info = _getMain().callGAPI(people.people(), 'get',
                      throwReasons=[GAPI.NOT_FOUND]+GAPI.PEOPLE_ACCESS_THROW_REASONS,
                      retryReasons=GAPI.SERVICE_NOT_AVAILABLE_RETRY_REASONS,
                      resourceName=f'people/{memberId}', personFields='names')
      if 'names' in info:
        for sourceType in ['PROFILE', 'CONTACT']:
          for name in info['names']:
            if name['metadata']['source']['type'] == sourceType:
              return name['displayName']
    except (GAPI.notFound, GAPI.serviceNotAvailable, GAPI.forbidden, GAPI.permissionDenied, GAPI.failedPrecondition):
      pass
    return unknownName

  cd = _getMain().buildGAPIObject(API.DIRECTORY)
  ci = None
  people = None
  memberOptions = initMemberOptions()
  memberDisplayOptions = initIPSGMGroupMemberDisplayOptions()
  groupColumn = True
  customerKey = GC.Values[GC.CUSTOMER_ID]
  kwargsDict = _getMain().initUserGroupDomainQueryFilters()
  subTitle = f'{Msg.ALL} {Ent.Plural(Ent.GROUP)}'
  fieldsList = []
  csvPF = _getMain().CSVPrintFile('group')
  FJQC = _getMain().FormatJSONQuoteChar(csvPF)
  allowExternalMembers = entityList = None
  showOwnedBy = {}
  cdfieldsList = ['email']
  userFieldsList = []
  schemaParms = _getMain()._initSchemaParms('basic')
  rolesSet = set()
  typesSet = set()
  matchPatterns = {}
  cacheMemberInfo = showDeliverySettings = verifyAllowExternal = False
  memberInfo = {}
  memberNames = {}
  unknownName = _getMain().UNKNOWN
  addCSVData = {}
  while Cmd.ArgumentsRemaining():
    myarg = _getMain().getArgument()
    if myarg == 'todrive':
      csvPF.GetTodriveParameters()
    elif getGroupFilters(myarg, kwargsDict, showOwnedBy):
      pass
    elif getGroupMatchPatterns(myarg, matchPatterns, False):
      pass
    elif myarg in {'group', 'groupns', 'groupsusp'}:
      entityList = [_getMain().getString(Cmd.OB_EMAIL_ADDRESS)]
      subTitle = f'{Ent.Singular(Ent.GROUP)}={entityList[0]}'
      if myarg == 'groupns':
        memberOptions[MEMBEROPTION_ISSUSPENDED] = False
      elif myarg == 'groupsusp':
        memberOptions[MEMBEROPTION_ISSUSPENDED] = True
    elif myarg == 'select':
      entityList = _getMain().getEntityList(Cmd.OB_GROUP_ENTITY)
      subTitle = f'{Msg.SELECTED} {Ent.Plural(Ent.GROUP)}'
    elif myarg in _getMain().SUSPENDED_ARGUMENTS:
      memberOptions[MEMBEROPTION_ISSUSPENDED] = _getMain()._getIsSuspended(myarg)
    elif myarg in _getMain().ARCHIVED_ARGUMENTS:
      memberOptions[MEMBEROPTION_ISARCHIVED] = _getMain()._getIsArchived(myarg)
    elif getIPSGMGroupRolesMemberDisplayOptions(myarg, rolesSet, memberDisplayOptions):
      pass
    elif getGroupMemberTypes(myarg, typesSet):
      pass
    elif getMemberMatchOptions(myarg, memberOptions):
      pass
    elif csvPF.GetFieldsListTitles(myarg, GROUPMEMBERS_FIELDS_CHOICE_MAP, fieldsList, initialField='email'):
      pass
    elif myarg == 'membernames':
      memberOptions[MEMBEROPTION_MEMBERNAMES] = True
    elif myarg == 'showdeliverysettings':
      showDeliverySettings = True
    elif myarg == 'userfields':
      for field in _getMain()._getFieldsList():
        if field in _getMain().USER_FIELDS_CHOICE_MAP:
          csvPF.AddField(field, _getMain().USER_FIELDS_CHOICE_MAP, userFieldsList)
        else:
          _getMain().invalidChoiceExit(field, _getMain().USER_FIELDS_CHOICE_MAP, True)
    elif myarg in {'allschemas', 'custom', 'schemas', 'customschemas'}:
      if myarg == 'allschemas':
        schemaParms = _getMain()._initSchemaParms('full')
      else:
        _getMain()._getSchemaNameList(schemaParms)
      userFieldsList.append('customSchemas')
    elif myarg == 'noduplicates':
      memberOptions[MEMBEROPTION_NODUPLICATES] = True
    elif myarg == 'recursive':
      memberOptions[MEMBEROPTION_RECURSIVE] = True
      memberOptions[MEMBEROPTION_INCLUDEDERIVEDMEMBERSHIP] = False
    elif myarg == 'includederivedmembership':
      memberOptions[MEMBEROPTION_INCLUDEDERIVEDMEMBERSHIP] = True
      memberOptions[MEMBEROPTION_RECURSIVE] = False
    elif myarg == 'nogroupemail':
      groupColumn = False
    elif myarg == 'peoplelookup':
      people = _getMain().buildGAPIObject(API.PEOPLE)
    elif myarg == 'peoplelookupuser':
      _, people = _getMain().buildGAPIServiceObject(API.PEOPLE, _getMain().getEmailAddress())
      if not people:
        return
    elif myarg == 'unknownname':
      unknownName = _getMain().getString(Cmd.OB_STRING)
    elif myarg == 'cachememberinfo':
      cacheMemberInfo = _getMain().getBoolean()
    elif myarg == 'verifyallowexternal':
      verifyAllowExternal = _getMain().getBoolean()
    elif myarg == 'addcsvdata':
      _getMain().getAddCSVData(addCSVData)
    else:
      FJQC.GetFormatJSONQuoteChar(myarg, False)
  if not typesSet:
    typesSet = {Ent.TYPE_USER} if memberOptions[MEMBEROPTION_RECURSIVE] else ALL_GROUP_MEMBER_TYPES
  showCategory, _ = finalizeIPSGMGroupRolesMemberDisplayOptions(cd, memberDisplayOptions, verifyAllowExternal)
  entityList = getGroupMembersEntityList(cd, entityList, matchPatterns, cdfieldsList, kwargsDict)
  if not fieldsList:
    for field in GROUPMEMBERS_DEFAULT_FIELDS:
      csvPF.AddField(field, {field: field}, fieldsList)
    if showDeliverySettings:
      field = 'delivery_settings'
      csvPF.AddField(field, {field: field}, fieldsList)
  elif 'name'in fieldsList:
    memberOptions[MEMBEROPTION_MEMBERNAMES] = True
    fieldsList.remove('name')
  if 'group' in fieldsList:
    fieldsList.remove('group')
  if userFieldsList:
    if not memberOptions[MEMBEROPTION_MEMBERNAMES] and 'name.fullName' in userFieldsList:
      memberOptions[MEMBEROPTION_MEMBERNAMES] = True
  if memberOptions[MEMBEROPTION_MEMBERNAMES]:
    if 'name.fullName' not in userFieldsList:
      userFieldsList.append('name.fullName')
    csvPF.AddTitles('name')
    csvPF.RemoveTitles([f'name{GC.Values[GC.CSV_OUTPUT_SUBFIELD_DELIMITER]}fullName'])
  if not groupColumn:
    csvPF.RemoveTitles(['group'])
  if showCategory:
    csvPF.AddTitles('category')
  if FJQC.formatJSON:
    csvPF.SetJSONTitles([])
    if groupColumn:
      csvPF.AddJSONTitles(['group'])
    if showCategory:
      csvPF.AddJSONTitles(['allowExternalMembers'])
    if addCSVData:
      csvPF.AddJSONTitles(sorted(addCSVData.keys()))
    csvPF.AddJSONTitles(['JSON'])
  else:
    if showCategory:
      csvPF.AddTitles(['allowExternalMembers'])
    if addCSVData:
      csvPF.AddTitles(sorted(addCSVData.keys()))
  memberOptions[MEMBEROPTION_GETDELIVERYSETTINGS] = 'delivery_settings' in fieldsList
  userFields = _getMain().getFieldsFromFieldsList(userFieldsList)
  if not rolesSet:
    rolesSet = _getMain().ALL_GROUP_ROLES
  getRolesSet = rolesSet.copy()
  if showOwnedBy:
    getRolesSet.add(Ent.ROLE_OWNER)
  getRoles = ','.join(sorted(getRolesSet))
  level = 0
  setCustomerMemberEmail = 'email' in fieldsList
  i = 0
  count = len(entityList)
  for group in entityList:
    i += 1
    if isinstance(group, dict):
      groupEmail = group['email']
    else:
      groupEmail = _getMain().convertUIDtoEmailAddress(group, cd, 'group', ciGroupsAPI=True)
      ci, _, groupEmail = _getMain().convertGroupCloudIDToEmail(ci, groupEmail, i, count)
    kvList = [Ent.CLOUD_IDENTITY_GROUP, groupEmail]
    if showCategory:
      allowExternalMembers = getGroupAllowExternalMembers(memberDisplayOptions['gs'], groupEmail, verifyAllowExternal,
                                                          kvList, i, count)
      if allowExternalMembers is None:
        continue
    if not checkGroupMatchPatterns(groupEmail, group, matchPatterns):
      continue
    membersList = []
    membersSet = set()
    getGroupMembers(cd, groupEmail, getRoles, membersList, membersSet, i, count,
                    memberOptions, memberDisplayOptions, level, typesSet)
    if showOwnedBy and not checkGroupShowOwnedBy(showOwnedBy, membersList):
      continue
    for member in membersList:
      if member['role'] not in rolesSet:
        continue
      memberId = member['id']
      row = {}
      if groupColumn:
        row['group'] = groupEmail
      if memberOptions[MEMBEROPTION_RECURSIVE]:
        row['level'] = member['level']
        row['subgroup'] = member['subgroup']
      for title in fieldsList:
        row[title] = member.get(title, '')
      if setCustomerMemberEmail and (memberId == customerKey):
        row['email'] = memberId
      if showCategory:
        row['category'] = member['category']
      memberType = member.get('type')
      if userFieldsList:
        if memberOptions[MEMBEROPTION_MEMBERNAMES]:
          row['name'] = unknownName
        if memberType == Ent.TYPE_USER:
          try:
            if not cacheMemberInfo or memberId not in memberInfo:
              mbinfo = _getMain().callGAPI(cd.users(), 'get',
                                throwReasons=GAPI.USER_GET_THROW_REASONS+[GAPI.SERVICE_NOT_AVAILABLE, GAPI.FAILED_PRECONDITION],
                                retryReasons=GAPI.SERVICE_NOT_AVAILABLE_RETRY_REASONS,
                                userKey=memberId, projection=schemaParms['projection'], customFieldMask=schemaParms['customFieldMask'],
                                fields=userFields)
              if memberOptions[MEMBEROPTION_MEMBERNAMES]:
                mname = mbinfo['name'].pop('fullName', unknownName)
                row['name'] = mname
                if not mbinfo['name']:
                  mbinfo.pop('name')
                if cacheMemberInfo:
                  memberNames[memberId] = mname
              if cacheMemberInfo:
                memberInfo[memberId] = mbinfo
            else:
              if memberOptions[MEMBEROPTION_MEMBERNAMES]:
                row['name'] = memberNames[memberId]
              mbinfo = memberInfo.get(memberId, {})
            if not FJQC.formatJSON:
              if addCSVData:
                row.update(addCSVData)
              csvPF.WriteRowTitles(_getMain().flattenJSON(mbinfo, flattened=row))
            else:
              row.update(mbinfo)
              fjrow = {}
              if groupColumn:
                fjrow['group'] = groupEmail
              if addCSVData:
                fjrow.update(addCSVData)
              fjrow['JSON'] = json.dumps(_getMain().cleanJSON(row, skipObjects=_getMain().USER_SKIP_OBJECTS, timeObjects=_getMain().USER_TIME_OBJECTS),
                                         ensure_ascii=False, sort_keys=True)
              csvPF.WriteRowNoFilter(fjrow)
            continue
          except GAPI.userNotFound:
            if memberOptions[MEMBEROPTION_MEMBERNAMES]:
              if people:
                if memberId not in memberNames:
                  memberNames[memberId] = getNameFromPeople(memberId)
              else:
                memberNames[memberId] = unknownName
              row['name'] = memberNames[memberId]
          except (GAPI.domainNotFound, GAPI.domainCannotUseApis, GAPI.forbidden,
                  GAPI.badRequest, GAPI.backendError, GAPI.systemError, GAPI.serviceNotAvailable, GAPI.failedPrecondition):
            if memberOptions[MEMBEROPTION_MEMBERNAMES] and cacheMemberInfo:
              memberNames[memberId] = unknownName
        elif memberType == Ent.TYPE_GROUP:
          if memberOptions[MEMBEROPTION_MEMBERNAMES]:
            try:
              if not cacheMemberInfo or memberId not in memberNames:
                row['name'] = _getMain().callGAPI(cd.groups(), 'get',
                                       throwReasons=GAPI.GROUP_GET_THROW_REASONS+[GAPI.SERVICE_NOT_AVAILABLE, GAPI.FAILED_PRECONDITION],
                                       retryReasons=GAPI.GROUP_GET_RETRY_REASONS,
                                       groupKey=memberId, fields='name')['name']
                if cacheMemberInfo:
                  memberNames[memberId] = row['name']
              else:
                row['name'] = memberNames[memberId]
            except (GAPI.groupNotFound, GAPI.domainNotFound, GAPI.domainCannotUseApis, GAPI.forbidden, GAPI.badRequest,
                    GAPI.invalid, GAPI.systemError, GAPI.serviceNotAvailable, GAPI.failedPrecondition):
              if memberOptions[MEMBEROPTION_MEMBERNAMES] and cacheMemberInfo:
                memberNames[memberId] = unknownName
        elif memberType == Ent.TYPE_CUSTOMER:
          if memberOptions[MEMBEROPTION_MEMBERNAMES]:
            try:
              if not cacheMemberInfo or memberId not in memberNames:
                row['name'] = _getMain().callGAPI(cd.customers(), 'get',
                                       throwReasons=[GAPI.BAD_REQUEST, GAPI.INVALID_INPUT, GAPI.RESOURCE_NOT_FOUND, GAPI.FORBIDDEN],
                                       customerKey=memberId, fields='customerDomain')['customerDomain']
                if cacheMemberInfo:
                  memberNames[memberId] = row['name']
              else:
                row['name'] = memberNames[memberId]
            except (GAPI.badRequest, GAPI.invalidInput, GAPI.resourceNotFound, GAPI.forbidden):
              if memberOptions[MEMBEROPTION_MEMBERNAMES] and cacheMemberInfo:
                memberNames[memberId] = unknownName
      if not FJQC.formatJSON:
        if allowExternalMembers is not None:
          row['allowExternalMembers'] = allowExternalMembers
        if addCSVData:
          row.update(addCSVData)
        csvPF.WriteRow(row)
      else:
        fjrow = {}
        if groupColumn:
          fjrow['group'] = groupEmail
        if allowExternalMembers is not None:
          fjrow['allowExternalMembers'] = allowExternalMembers
        if addCSVData:
          fjrow.update(addCSVData)
        fjrow['JSON'] = json.dumps(_getMain().cleanJSON(row, skipObjects=_getMain().USER_SKIP_OBJECTS, timeObjects=_getMain().USER_TIME_OBJECTS),
                                   ensure_ascii=False, sort_keys=True)
        csvPF.WriteRowNoFilter(fjrow)
  if not FJQC.formatJSON:
    sortTitles = ['group'] if groupColumn else []
    if showCategory:
      sortTitles.append('allowExternalMembers')
    if addCSVData:
      sortTitles.extend(sorted(addCSVData.keys()))
    sortTitles.extend(GROUPMEMBERS_SORT_FIELDS)
    if showCategory:
      emailIndex = sortTitles.index('email')
      sortTitles.insert(emailIndex+1, 'category')
    csvPF.SetSortTitles(sortTitles)
    csvPF.SortTitles()
    csvPF.SetSortTitles([])
    if memberOptions[MEMBEROPTION_RECURSIVE]:
      csvPF.MoveTitlesToEnd(['level', 'subgroup'])
  csvPF.writeCSVfile(f'Group Members ({subTitle})')

# gam show group-members
#	[([domain|domains <DomainNameEntity>] ([member|showownedby <EmailItem>]|[(query <QueryGroup>)|(queries <QueryUserList>)]))|
#	 (group|group_ns|group_susp <GroupItem>)|
#	 (select <GroupEntity>)]
#	[emailmatchpattern [not] <REMatchPattern>] [namematchpattern [not] <REMatchPattern>]
#	[descriptionmatchpattern [not] <REMatchPattern>]
#	[roles <GroupRoleList>] [members] [managers] [owners] [depth <Number>]
#	[internal] [internaldomains all|primary|<DomainNameList>] [external]
#	[notsuspended|suspended] [notarchived|archived]
#	[types <GroupMemberTypeList>]
#	[memberemaildisplaypattern|memberemailskippattern <REMatchPattern>]
#	[includederivedmembership]
def doShowGroupMembers():
  def _roleOrder(key):
    return {Ent.ROLE_OWNER: 0, Ent.ROLE_MANAGER: 1, Ent.ROLE_MEMBER: 2}.get(key, 3)

  def _typeOrder(key):
    return {Ent.TYPE_CUSTOMER: 0, Ent.TYPE_USER: 1, Ent.TYPE_GROUP: 2, Ent.TYPE_EXTERNAL: 3}.get(key, 4)

  def _statusOrder(key):
    return {'ACTIVE': 0, 'SUSPENDED': 1, 'UNKNOWN': 2}.get(key, 3)

  def _showGroup(groupEmail, depth):
    try:
      membersList = _getMain().callGAPIpages(cd.members(), 'list', 'members',
                                  throwReasons=GAPI.MEMBERS_THROW_REASONS, retryReasons=GAPI.MEMBERS_RETRY_REASONS,
                                  includeDerivedMembership=includeDerivedMembership,
                                  groupKey=groupEmail, fields='nextPageToken,members(email,id,role,status,type)', maxResults=GC.Values[GC.MEMBER_MAX_RESULTS])
      if showOwnedBy and not checkGroupShowOwnedBy(showOwnedBy, membersList):
        return
    except (GAPI.groupNotFound, GAPI.domainNotFound, GAPI.domainCannotUseApis, GAPI.invalid, GAPI.forbidden, GAPI.serviceNotAvailable):
      if depth == 0:
        _getMain().entityUnknownWarning(Ent.GROUP, groupEmail, i, count)
      return
    if depth == 0:
      _getMain().printEntity([Ent.GROUP, groupEmail], i, count)
    if depth == 0 or Ent.TYPE_GROUP in typesSet:
      Ind.Increment()
    for member in sorted(membersList, key=lambda k: (_roleOrder(k.get('role', Ent.ROLE_MEMBER)), _typeOrder(k['type']), _statusOrder(k.get('status', '')))):
      if (_getMain()._checkMemberIsSuspendedIsArchived(member, memberOptions[MEMBEROPTION_ISSUSPENDED], memberOptions[MEMBEROPTION_ISARCHIVED]) and
          (not checkShowCategory or _getMain()._checkMemberCategory(member, memberDisplayOptions))):
        if (member.get('role', Ent.ROLE_MEMBER) in rolesSet and
            member['type'] in typesSet and
            _checkMemberMatch(member, memberOptions)):
          memberDetails = f'{member.get("role", Ent.ROLE_MEMBER)}, {member["type"]}, {member.get("email", member["id"])}'
          if showCategory:
            memberDetails += f', {member["category"]}'
          memberDetails += f' , {member.get("status", "")}'
          _getMain().printKeyValueList([memberDetails])
        if not includeDerivedMembership and (member['type'] == Ent.TYPE_GROUP) and (maxdepth == -1 or depth < maxdepth):
          _showGroup(member['email'], depth+1)
    if depth == 0 or Ent.TYPE_GROUP in typesSet:
      Ind.Decrement()

  cd = _getMain().buildGAPIObject(API.DIRECTORY)
  ci = None
  kwargsDict = _getMain().initUserGroupDomainQueryFilters()
  entityList = None
  showOwnedBy = {}
  cdfieldsList = ['email']
  rolesSet = set()
  typesSet = set()
  memberOptions = initMemberOptions()
  memberDisplayOptions = initIPSGMGroupMemberDisplayOptions()
  matchPatterns = {}
  maxdepth = -1
  includeDerivedMembership = False
  while Cmd.ArgumentsRemaining():
    myarg = _getMain().getArgument()
    if getGroupFilters(myarg, kwargsDict, showOwnedBy):
      pass
    elif getGroupMatchPatterns(myarg, matchPatterns, False):
      pass
    elif myarg in {'group', 'groupns', 'groupsusp'}:
      entityList = [_getMain().getString(Cmd.OB_EMAIL_ADDRESS)]
      if myarg == 'groupns':
        memberOptions[MEMBEROPTION_ISSUSPENDED] = False
      elif myarg == 'groupsusp':
        memberOptions[MEMBEROPTION_ISSUSPENDED] = True
    elif myarg == 'select':
      entityList = _getMain().getEntityList(Cmd.OB_GROUP_ENTITY)
    elif myarg in _getMain().SUSPENDED_ARGUMENTS:
      memberOptions[MEMBEROPTION_ISSUSPENDED] = _getMain()._getIsSuspended(myarg)
    elif myarg in _getMain().ARCHIVED_ARGUMENTS:
      memberOptions[MEMBEROPTION_ISARCHIVED] = _getMain()._getIsArchived(myarg)
    elif getIPSGMGroupRolesMemberDisplayOptions(myarg, rolesSet, memberDisplayOptions):
      pass
    elif getGroupMemberTypes(myarg, typesSet):
      pass
    elif getMemberMatchOptions(myarg, memberOptions):
      pass
    elif myarg == 'depth':
      maxdepth = _getMain().getInteger(minVal=-1)
    elif myarg == 'includederivedmembership':
      includeDerivedMembership = True
    else:
      _getMain().unknownArgumentExit()
  if not rolesSet:
    rolesSet = _getMain().ALL_GROUP_ROLES
  if not typesSet:
    typesSet = ALL_GROUP_MEMBER_TYPES
  showCategory, checkShowCategory = finalizeIPSGMGroupRolesMemberDisplayOptions(cd, memberDisplayOptions, False)
  entityList = getGroupMembersEntityList(cd, entityList, matchPatterns, cdfieldsList, kwargsDict)
  i = 0
  count = len(entityList)
  for group in entityList:
    i += 1
    if isinstance(group, dict):
      groupEmail = group['email']
    else:
      groupEmail = _getMain().convertUIDtoEmailAddress(group, cd, 'group', ciGroupsAPI=True)
      ci, _, groupEmail = _getMain().convertGroupCloudIDToEmail(ci, groupEmail, i, count)
    if checkGroupMatchPatterns(groupEmail, group, matchPatterns):
      _showGroup(groupEmail, 0)

def getGroupParents(cd, groupParents, groupEmail, groupName, kwargs):
  groupParents[groupEmail] = {'name': groupName, 'parents': []}
  _getMain()._setUserGroupArgs(groupEmail, kwargs)
  try:
    entityList = _getMain().callGAPIpages(cd.groups(), 'list', 'groups',
                               throwReasons=GAPI.GROUP_LIST_USERKEY_THROW_REASONS,
                               retryReasons=GAPI.SERVICE_NOT_AVAILABLE_RETRY_REASONS,
                               orderBy='email', fields='nextPageToken,groups(email,name)', **kwargs)
    for parentGroup in entityList:
      groupParents[groupEmail]['parents'].append(parentGroup['email'])
      if parentGroup['email'] not in groupParents:
        getGroupParents(cd, groupParents, parentGroup['email'], parentGroup['name'], kwargs)
  except (GAPI.invalidMember, GAPI.invalidInput):
    _getMain().badRequestWarning(Ent.GROUP, Ent.MEMBER, groupEmail)
  except (GAPI.resourceNotFound, GAPI.domainNotFound, GAPI.forbidden, GAPI.badRequest):
    accessErrorExit(cd)

def showGroupParents(groupParents, groupEmail, role, i, count):
  kvList = [groupEmail, f'{groupParents[groupEmail]["name"]}']
  if role:
    kvList.extend([Ent.Singular(Ent.ROLE), role])
  _getMain().printKeyValueListWithCount(kvList, i, count)
  Ind.Increment()
  for parentEmail in groupParents[groupEmail]['parents']:
    showGroupParents(groupParents, parentEmail, None, 0, 0)
  Ind.Decrement()

def addJsonGroupParents(groupParents, userGroup, groupEmail):
  userGroup.setdefault('parents', [])
  for parentEmail in groupParents[groupEmail]['parents']:
    userGroup['parents'].append({'email': parentEmail, 'name': groupParents[parentEmail]['name'], 'parents': []})
    addJsonGroupParents(groupParents, userGroup['parents'][-1], parentEmail)

def printGroupParents(groupParents, groupEmail, row, csvPF, delimiter, showParentsAsList):
  if groupParents[groupEmail]['parents']:
    for parentEmail in groupParents[groupEmail]['parents']:
      row['parents'].append({'email': parentEmail, 'name': groupParents[parentEmail]['name']})
      printGroupParents(groupParents, parentEmail, row, csvPF, delimiter, showParentsAsList)
      del row['parents'][-1]
  else:
    if not showParentsAsList:
      csvPF.WriteRowTitles(_getMain().flattenJSON(row))
    else:
      crow = row.copy()
      if 'Role' in row:
        crow['Role'] = row['Role']
      parents = crow.pop('parents')
      crow['ParentsCount'] = len(parents)
      crow['Parents'] = delimiter.join([parent['email'] for parent in parents])
      crow['ParentsName'] = delimiter.join([parent['name'] for parent in parents])
      csvPF.WriteRow(_getMain().flattenJSON(crow))

# gam print grouptree <GroupEntity> [todrive <ToDriveAttribute>*]
#	[showparentsaslist [<Boolean>]] [delimiter <Character>]
#	[formatjson [quotechar <Character>]]
# gam show grouptree <GroupEntity>
#	[formatjson]
def doPrintShowGroupTree():
  cd = _getMain().buildGAPIObject(API.DIRECTORY)
  kwargs = {'customer': GC.Values[GC.CUSTOMER_ID]}
  csvPF = _getMain().CSVPrintFile(['Group', 'Name']) if Act.csvFormat() else None
  FJQC = _getMain().FormatJSONQuoteChar(csvPF)
  delimiter = GC.Values[GC.CSV_OUTPUT_FIELD_DELIMITER]
  showParentsAsList = False
  entityList = _getMain().getEntityList(Cmd.OB_GROUP_ENTITY)
  while Cmd.ArgumentsRemaining():
    myarg = _getMain().getArgument()
    if csvPF and myarg == 'todrive':
      csvPF.GetTodriveParameters()
    elif csvPF and myarg == 'delimiter':
      delimiter = _getMain().getCharacter()
    elif csvPF and myarg == 'showparentsaslist':
      showParentsAsList = _getMain().getBoolean()
    else:
      FJQC.GetFormatJSONQuoteChar(myarg, True)
  if csvPF and not FJQC.formatJSON:
    if not showParentsAsList:
      csvPF.SetIndexedTitles(['parents'])
    else:
      csvPF.AddTitles(['ParentsCount', 'Parents', 'ParentsName'])
  groupParents = {}
  i = 0
  count = len(entityList)
  if not csvPF and not FJQC.formatJSON:
    _getMain().performActionNumItems(count, Ent.GROUP_TREE)
  for group in entityList:
    i += 1
    groupEmail = _getMain().normalizeEmailAddressOrUID(group)
    if groupEmail not in groupParents:
      try:
        groupName = _getMain().callGAPI(cd.groups(), 'get',
                             throwReasons=GAPI.GROUP_GET_THROW_REASONS, retryReasons=GAPI.GROUP_GET_RETRY_REASONS,
                             groupKey=groupEmail, fields='name')['name']
      except (GAPI.groupNotFound, GAPI.domainNotFound, GAPI.domainCannotUseApis, GAPI.forbidden, GAPI.badRequest,
              GAPI.invalid, GAPI.systemError) as e:
        _getMain().entityActionFailedWarning([Ent.GROUP, groupEmail], str(e), i, count)
        continue
      getGroupParents(cd, groupParents, groupEmail, groupName, kwargs)
    if not FJQC.formatJSON:
      if not csvPF:
        showGroupParents(groupParents, groupEmail, None, i, count)
      else:
        row = {'Group': groupEmail, 'Name': groupParents[groupEmail]['name'], 'parents': []}
        printGroupParents(groupParents, groupEmail, row, csvPF, delimiter, showParentsAsList)
    else:
      groupInfo = {'email': groupEmail, 'name': groupParents[groupEmail]['name'], 'parents': []}
      addJsonGroupParents(groupParents, groupInfo, groupEmail)
      if not csvPF:
        _getMain().printLine(json.dumps(_getMain().cleanJSON(groupInfo), ensure_ascii=False, sort_keys=True))
      else:
        row = _getMain().flattenJSON(groupInfo)
        if csvPF.CheckRowTitles(row):
          csvPF.WriteRowNoFilter({'Group': groupEmail, 'Name': groupParents[groupEmail]['name'],
                                  'JSON': json.dumps(_getMain().cleanJSON(groupInfo),
                                                     ensure_ascii=False, sort_keys=True)})
  if csvPF:
    csvPF.writeCSVfile('Group Tree')

# gam create cigroup <EmailAddress>
#	[copyfrom <GroupItem>] <GroupAttribute>
#	[makeowner] [alias|aliases <CIGroupAliasList>]
#	[security|makesecuritygroup] [locked]
#	[dynamic <QueryDynamicGroup>]
