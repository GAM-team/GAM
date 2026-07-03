"""Cloud Identity group member management.

Part of the _cigroups_tmp sub-package."""

"""GAM Cloud Identity group management."""

import re
import json
import sys

from gam.util.args import formatLocalTime

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

from gam.cmd.groups.groups import (
    MEMBEROPTION_INCLUDEDERIVEDMEMBERSHIP, MEMBEROPTION_ISARCHIVED,
    MEMBEROPTION_ISSUSPENDED, MEMBEROPTION_NODUPLICATES, MEMBEROPTION_RECURSIVE,
)

from gam.cmd.cigroups.groups import ALL_CIGROUP_MEMBER_TYPES, CIGROUP_MEMBER_TYPES_MAP
CIGROUP_DISCUSSION_FORUM_LABEL = 'cloudidentity.googleapis.com/groups.discussion_forum'

def __getattr__(name):
  """Fall back to gam module for any undefined names."""
  main = _getMain()
  try:
    return getattr(main, name)
  except AttributeError:
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")

UNKNOWN = 'Unknown'

def getCIGroupMemberTypes(myarg, typesSet):
  if myarg in {'type', 'types'}:
    for gtype in _getMain().getString(Cmd.OB_GROUP_TYPE_LIST).lower().replace('_', '').replace(',', ' ').split():
      if gtype in CIGROUP_MEMBER_TYPES_MAP:
        typesSet.add(CIGROUP_MEMBER_TYPES_MAP[gtype])
      else:
        _getMain().invalidChoiceExit(gtype, CIGROUP_MEMBER_TYPES_MAP, True)
  else:
    return False
  return True

# gam info cigroups <GroupEntity>
#	[nousers|membertree] [quick] [noaliases] [nojoindate] [showupdatedate]
#	[nosecurity|nosecuritysettings]
#	[allfields|<CIGroupFieldName>*|(fields <CIGroupFieldNameList>)]
#	[roles <GroupRoleList>] [members] [managers] [owners]
#	[internal] [internaldomains all|primary|<DomainNameList>] [external]
#	[types <CIGroupMemberTypeList>]
#	[memberemaildisplaypattern|memberemailskippattern <REMatchPattern>]
#	[formatjson]
def doInfoCIGroups():
  def printCIGroupMemberTree(group_id, showRole):
    if not group_id in cachedGroupMembers:
      try:
        cachedGroupMembers[group_id] = _getMain().callGAPIpages(ci.groups().memberships(), 'list', 'memberships',
                                                     throwReasons=GAPI.MEMBERS_THROW_REASONS,
                                                     retryReasons=GAPI.MEMBERS_RETRY_REASONS,
                                                     parent=group_id, view='FULL',
                                                     fields='nextPageToken,memberships(*)',
                                                     pageSize=GC.Values[GC.MEMBER_MAX_RESULTS])
      except (GAPI.groupNotFound, GAPI.domainNotFound, GAPI.domainCannotUseApis, GAPI.invalid, GAPI.forbidden):
        _getMain().entityUnknownWarning(Ent.CLOUD_IDENTITY_GROUP, group_id, i, count)
        return
      except (GAPI.conditionNotMet, GAPI.serviceNotAvailable) as e:
        _getMain().entityActionFailedWarning([Ent.CLOUD_IDENTITY_GROUP, group_id], str(e), i, count)
        return
    for member in cachedGroupMembers[group_id]:
      member_id = member.get('name', '')
      member_id = member_id.split('/')[-1]
      member_email = member.get('preferredMemberKey', {}).get('id')
      member_type = member.get('type', 'USER').lower()
      if showRole:
        _getMain().getCIGroupMemberRoleFixType(member)
        _getMain().printKeyValueList([member['role'].lower(), f'{member_email} ({member_type})'])
      else:
        _getMain().writeStdout(f'{Ind.Spaces()}{member_email} ({member_type})\n')
      if member_type == 'group':
        Ind.Increment()
        printCIGroupMemberTree(f'groups/{member_id}', False)
        Ind.Decrement()

  def initGroupFieldsLists():
    if not groupFieldsLists['ci']:
      groupFieldsLists['ci'] = ['groupKey']

  cd = _getMain().buildGAPIObject(API.DIRECTORY)
  ci = _getMain().buildGAPIObject(API.CLOUDIDENTITY_GROUPS)
  entityList = _getMain().getEntityList(Cmd.OB_GROUP_ENTITY)
  getAliases = getSecuritySettings = getUsers = True
  showJoinDate = True
  showMemberTree = showUpdateDate = False
  FJQC = _getMain().FormatJSONQuoteChar()
  members = []
  groupFieldsLists = {'ci': None}
  entityType = Ent.MEMBER
  rolesSet = set()
  typesSet = set()
  memberOptions = _getMain().initMemberOptions()
  memberDisplayOptions = _getMain().initIPSGMGroupMemberDisplayOptions()
  cachedGroupMembers = {}
  while Cmd.ArgumentsRemaining():
    myarg = _getMain().getArgument()
    if myarg == 'quick':
      getAliases = getUsers = False
    elif myarg == 'nousers':
      getUsers = False
    elif myarg == 'membertree':
      showMemberTree = True
    elif _getMain().getIPSGMGroupRolesMemberDisplayOptions(myarg, rolesSet, memberDisplayOptions):
      getUsers = True
    elif getCIGroupMemberTypes(myarg, typesSet):
      pass
    elif _getMain().getMemberMatchOptions(myarg, memberOptions):
      pass
    elif myarg == 'noaliases':
      getAliases = False
    elif myarg in {'allfields', 'ciallfields', 'allcifields'}:
      if not groupFieldsLists['ci']:
        groupFieldsLists['ci'] = []
      for field in _getMain().CIGROUP_FIELDS_CHOICE_MAP:
        _getMain().addFieldToFieldsList(field, _getMain().CIGROUP_FIELDS_CHOICE_MAP, groupFieldsLists['ci'])
    elif myarg in _getMain().CIGROUP_FIELDS_CHOICE_MAP:
      initGroupFieldsLists()
      _getMain().addFieldToFieldsList(myarg, _getMain().CIGROUP_FIELDS_CHOICE_MAP, groupFieldsLists['ci'])
    elif myarg in {'fields', 'cifields'}:
      initGroupFieldsLists()
      for field in _getMain()._getFieldsList():
        if field in _getMain().CIGROUP_FIELDS_CHOICE_MAP:
          _getMain().addFieldToFieldsList(field, _getMain().CIGROUP_FIELDS_CHOICE_MAP, groupFieldsLists['ci'])
        else:
          _getMain().invalidChoiceExit(field, _getMain().CIGROUP_FIELDS_CHOICE_MAP, True)
    elif myarg == 'nojoindate':
      showJoinDate = False
    elif myarg == 'showupdatedate':
      showUpdateDate = True
    elif myarg in ['nosecurity', 'nosecuritysettings']:
      getSecuritySettings = False
    else:
      FJQC.GetFormatJSON(myarg)
  if not typesSet:
    typesSet = ALL_CIGROUP_MEMBER_TYPES
  fields = _getMain().getFieldsFromFieldsList(groupFieldsLists['ci'])
  if not showJoinDate and not showUpdateDate:
    view = 'BASIC'
    pageSize = 1000
  else:
    view = 'FULL'
    pageSize = 500
  showCategory, checkShowCategory = _getMain().finalizeIPSGMGroupRolesMemberDisplayOptions(cd, memberDisplayOptions, False)
  i = 0
  count = len(entityList)
  for group in entityList:
    i += 1
    _, name, group = _getMain().convertGroupEmailToCloudID(ci, group, i, count)
    if not name or not group:
      continue
    try:
      cigInfo = _getMain()._getMain().callGAPI(ci.groups(), 'get',
                         throwReasons=GAPI.CIGROUP_GET_THROW_REASONS, retryReasons=GAPI.CIGROUP_RETRY_REASONS,
                         name=name, fields=fields)
      group = cigInfo['groupKey']['id']
      if not getAliases:
        cigInfo.pop('additionalGroupKeys', None)
      if getUsers and not showMemberTree:
        result = _getMain().callGAPIpages(ci.groups().memberships(), 'list', 'memberships',
                               throwReasons=GAPI.MEMBERS_THROW_REASONS, retryReasons=GAPI.MEMBERS_RETRY_REASONS,
                               parent=name, view=view, fields='*', pageSize=pageSize)
        members = []
        for member in result:
          _getMain().getCIGroupMemberRoleFixType(member)
          if ((member['type'] in typesSet) and
              _getMain()._checkMemberRole(member, rolesSet) and
              _getMain()._checkCIMemberMatch(member, memberOptions) and
              (not checkShowCategory or _getMain()._checkCIMemberCategory(member, memberDisplayOptions))):
            members.append(member)
      if getSecuritySettings:
        cigInfo['SecuritySettings'] = _getMain().callGAPI(ci.groups(), 'getSecuritySettings',
                                               throwReasons=GAPI.CIGROUP_GET_THROW_REASONS, retryReasons=GAPI.CIGROUP_RETRY_REASONS,
                                               name=f'{name}/securitySettings', readMask='*')
      if FJQC.formatJSON:
        if getUsers and not showMemberTree:
          cigInfo['members'] = members
        _getMain().printLine(json.dumps(_getMain().cleanJSON(cigInfo, timeObjects=_getMain().CIGROUP_TIME_OBJECTS), ensure_ascii=False, sort_keys=True))
        continue
      _getMain()._showCIGroup(cigInfo, group, i, count)
      if getUsers and not showMemberTree:
        Ind.Increment()
        _getMain().printEntitiesCount(entityType, members)
        Ind.Increment()
        for member in members:
          memberEmail = member.get('preferredMemberKey', {}).get('id', member['name'])
          _getMain().getCIGroupMemberRoleFixType(member)
          memberDetails = [member['role'].lower(), f'{memberEmail} ({member["type"].lower()})']
          if showCategory:
            memberDetails[1] += f' ({member["category"]})'
          if showJoinDate:
            memberDetails.extend(['joined', formatLocalTime(member['createTime']) if 'createTime' in member else UNKNOWN])
          if showUpdateDate:
            memberDetails.extend(['updated', formatLocalTime(member['updateTime']) if 'updateTime' in member else UNKNOWN])
          if 'expireTime' in member:
            memberDetails.extend(['expires', formatLocalTime(member['expireTime'])])
          _getMain().printKeyValueList(memberDetails)
        Ind.Decrement()
        _getMain().printKeyValueList([Msg.TOTAL_ITEMS_IN_ENTITY.format(Ent.Plural(entityType), Ent.Singular(Ent.CLOUD_IDENTITY_GROUP)), len(members)])
        Ind.Decrement()
      elif showMemberTree:
        Ind.Increment()
        _getMain().printEntity([Ent.MEMBERSHIP_TREE, ''])
        Ind.Increment()
        printCIGroupMemberTree(name, True)
        Ind.Decrement()
        Ind.Decrement()
    except GAPI.notFound:
      _getMain().entityActionFailedWarning([Ent.CLOUD_IDENTITY_GROUP, group], Msg.DOES_NOT_EXIST, i, count)
    except (GAPI.groupNotFound, GAPI.resourceNotFound, GAPI.domainNotFound, GAPI.domainCannotUseApis, GAPI.backendError,
            GAPI.invalid, GAPI.invalidArgument, GAPI.invalidMember, GAPI.invalidParameter, GAPI.invalidInput, GAPI.forbidden,
            GAPI.badRequest, GAPI.permissionDenied, GAPI.systemError, GAPI.serviceLimit, GAPI.serviceNotAvailable) as e:
      _getMain().entityActionFailedWarning([Ent.CLOUD_IDENTITY_GROUP, group], str(e), i, count)

def checkCIGroupShowOwnedBy(showOwnedBy, members):
  for member in members:
    if member['preferredMemberKey']['id'] == showOwnedBy:
      if member['role'] == Ent.ROLE_OWNER:
        return True
  return False

def updateFieldsForCIGroupMatchPatterns(matchPatterns, fieldsList, csvPF=None):
  for field in ['displayName', 'description']:
    if field in matchPatterns:
      if csvPF is not None:
        csvPF.AddField(field, _getMain().CIGROUP_FIELDS_CHOICE_MAP, fieldsList)
      else:
        fieldsList.append(field)

CIPOLICY_TIME_OBJECTS = {'createTime', 'updateTime'}

def _filterPolicies(ci, pageMessage, ifilter):
  try:
    policies = _getMain().callGAPIpages(ci.policies(), 'list', 'policies',
                             pageMessage=pageMessage,
                             throwReasons=[GAPI.INVALID, GAPI.INVALID_ARGUMENT, GAPI.PERMISSION_DENIED],
                             filter=ifilter, pageSize=100)
    # Google returns unordered results, sort them by setting type
    return sorted(policies, key=lambda p: p.get('setting', {}).get('type', ''))
  except (GAPI.invalid, GAPI.invalidArgument, GAPI.permissionDenied) as e:
    _getMain().entityActionFailedWarning([Ent.POLICY, ifilter], str(e))
    return []

# Policies where GAM should offer additional guidance and information
CIPOLICY_ADDITIONAL_WARNINGS = {
  'settings/drive_and_docs.external_sharing': {
    'warningType': 'SUPERSEDED_POLICY',
    'warningMessage': 'CAUTION: Drive Sharing settings are superseded by Drive Trust Rules if Trust Rules has been enabled for your domain. Drive Trust Rule settings are not available in the Policy API today so GAM is not able to check if Trust Rules is enabled and if the settings/drive_and_docs.external_sharing policies are actually in effect for your domain. If Drive Trust Rules is enabled for your domain then this settings/drive_and_docs.external_sharing policy does not accurately reflect your current Drive sharing settings.'
  }
}

def _getPolicyAppNameFromId(httpObj, app):
  app['applicationName'] = _getMain().UNKNOWN
  appId = app['applicationId']
  url = f'https://workspace.google.com/marketplace/app/_/{appId}'
  try:
    resp, content = httpObj.request(url, 'GET')
  except:
    return
  if resp.status != 200:
    return
  if isinstance(content, bytes):
    content = content.decode()
  pattern = f'https://workspace.google.com/marketplace/app/(.+?)/{appId}'
  a = re.search(pattern, content)
  if a:
    app['applicationName'] = a.group(1)

def _cleanPolicy(policy, add_warnings, no_appnames, no_idmapping,
                 groupEmailPattern, orgUnitPathPattern,
                 cd, groups_ci):
  # convert any wordlists into spaced strings to reduce output complexity
  if policy['setting']['type'] == 'settings/detector.word_list':
    wordList = ''
    for word in policy['setting']['value']['wordList']['words']:
      wordList += "'"
      wordList += word.replace("'", r"\'")
      wordList += "',"
    if wordList:
      wordList = wordList[:-1]
    policy['setting']['value']['wordList'] = wordList
  # get application name for application id
  if policy['setting']['type'] == 'settings/workspace_marketplace.apps_allowlist' and not no_appnames:
    httpObj = _getMain().getHttpObj(timeout=10)
    for app in policy['setting']['value'].get('apps', []):
      _getPolicyAppNameFromId(httpObj, app)
  # add any warnings to applicable policies
  if add_warnings and policy['setting']['type'] in CIPOLICY_ADDITIONAL_WARNINGS:
    policy['warning'] = CIPOLICY_ADDITIONAL_WARNINGS[policy['setting']['type']]
  if groupId := policy['policyQuery'].get('group'):
    if (not no_idmapping) or (groupEmailPattern is not None):
      _, _, groupEmail = _getMain().convertGroupCloudIDToEmail(groups_ci, groupId)
      if not no_idmapping:
        policy['policyQuery']['groupEmail'] = groupEmail
      if groupEmailPattern is not None:
        return groupEmailPattern.match(groupEmail)
  elif orgId := policy['policyQuery'].get('orgUnit'):
    if (not no_idmapping) or (orgUnitPathPattern is not None):
      orgUnitPath = _getMain().convertOrgUnitIDtoPath(cd, orgId)
      if not no_idmapping:
        policy['policyQuery']['orgUnitPath'] = orgUnitPath
      if orgUnitPathPattern is not None:
        return orgUnitPathPattern.match(orgUnitPath)
  return True

def _showPolicy(policy, FJQC, i=0, count=0):
  if FJQC is not None and FJQC.formatJSON:
    _getMain().printLine(json.dumps(_getMain().cleanJSON(policy, timeObjects=CIPOLICY_TIME_OBJECTS),
                         ensure_ascii=False, sort_keys=True))
    return
  _getMain().printEntity([Ent.POLICY, policy['name']], i, count)
  Ind.Increment()
  policy.pop('name')
  _getMain().showJSON(None, policy, timeObjects=CIPOLICY_TIME_OBJECTS)
  _getMain().printBlankLine()
  Ind.Decrement()

def _showPolicies(policies, FJQC, add_warnings, no_appnames, no_idmapping,
                  groupEmailPattern, orgUnitPathPattern, cd, groups_ci):
  count = len(policies)
  if FJQC is None or not FJQC.formatJSON:
    if groupEmailPattern is None and orgUnitPathPattern is None:
      _getMain().performActionNumItems(count, Ent.POLICY)
    else:
      _getMain().performActionModifierNumItems(Msg.MAXIMUM_OF, count, Ent.POLICY)
  Ind.Increment()
  i = 0
  for policy in policies:
    i += 1
    if _cleanPolicy(policy, add_warnings, no_appnames, no_idmapping,
                    groupEmailPattern, orgUnitPathPattern, cd, groups_ci):
      _showPolicy(policy, FJQC, i, count)
  Ind.Decrement()

def _checkPoliciesWithDASA():
  if GC.Values[GC.ENABLE_DASA]:
    _getMain().systemErrorExit(_getMain().USAGE_ERROR_RC,
                    Msg.COMMAND_NOT_COMPATIBLE_WITH_ENABLE_DASA.format(Act.ToPerform().lower(), Cmd.ARG_CIPOLICIES))

# gam create policy
#	json <JSONData>
#	[(ou|orgunit <OrgUnitItem>)|(group <GroupItem>)|(query <String>)]
# gam update policy
#	json <JSONData>
#	[(ou|orgunit <OrgUnitItem>)|(group <GroupItem>)|(query <String>)]
def doCreateUpdateCIPolicy():
  _checkPoliciesWithDASA()
  ci = _getMain().buildGAPIObject(API.CLOUDIDENTITY_POLICY)
  cd = _getMain().buildGAPIObject(API.DIRECTORY)
  updateCmd = Act.Get() == Act.UPDATE
  groupEmail = orgUnit = query = None
  _getMain().checkArgumentPresent('json', True)
  policy = _getMain().getJSON(['customer', 'type'])
  if updateCmd:
    pname = policy.pop('name', None)
    if not pname:
      Cmd.Backup()
      _getMain().usageErrorExit(Msg.POLICY_NAME_NOT_FOUND)
  else:
    policy.pop('name', None)
    pname = 'New Policy'
  if 'policyQuery' in policy:
    policy['policyQuery'].pop('orgUnitPath', None)
    policy['policyQuery'].pop('groupEmail', None)
    policy['policyQuery'].pop('sortOrder', None)
    if 'orgUnit' in policy['policyQuery'] or 'group' in policy['policyQuery']:
      policy['policyQuery'].pop('query', None)
  if 'setting' in policy:
    if 'value' in policy['setting']:
      policy['setting']['value'].pop('createTime', None)
      policy['setting']['value'].pop('deleteTime', None)
      policy['setting']['value'].pop('updateTime', None)
      if policy['setting']['type'] == 'settings/detector.word_list':
        if isinstance(policy['setting']['value']['wordList'], str):
          wordList = policy['setting']['value'].pop('wordList')
          policy['setting']['value']['wordList']['words'] = _getMain().shlexSplitList(wordList, dataDelimiter=',')
  while Cmd.ArgumentsRemaining():
    myarg = _getMain().getArgument()
    if myarg in {'ou', 'org', 'orgunit'}:
      if groupEmail:
        Cmd.Backup()
        _getMain().usageErrorExit(Msg.ARE_MUTUALLY_EXCLUSIVE.format(myarg, 'group'))
      if query:
        Cmd.Backup()
        _getMain().usageErrorExit(Msg.ARE_MUTUALLY_EXCLUSIVE.format(myarg, 'query'))
      orgUnit, targetResource = _getMain()._getOrgunitsOrgUnitIdPath(cd, _getMain().getString(Cmd.OB_ORGUNIT_PATH))
      policy['policyQuery'] = {'orgUnit': f"orgUnits/{targetResource}"}
    elif myarg == 'group':
      if orgUnit:
        Cmd.Backup()
        _getMain().usageErrorExit(Msg.ARE_MUTUALLY_EXCLUSIVE.format(myarg, 'ou|org|orgunit'))
      if query:
        Cmd.Backup()
        _getMain().usageErrorExit(Msg.ARE_MUTUALLY_EXCLUSIVE.format(myarg, 'query'))
      groupEmail = _getMain().getEmailAddress(returnUIDprefix='uid:')
      targetResource = f"groups/{_getMain().convertEmailAddressToUID(groupEmail, cd, emailType='group')}"
      policy['policyQuery'] = {'group': f"groups/{targetResource}"}
    elif myarg == 'query':
      if groupEmail:
        Cmd.Backup()
        _getMain().usageErrorExit(Msg.ARE_MUTUALLY_EXCLUSIVE.format(myarg, 'group'))
      if orgUnit:
        Cmd.Backup()
        _getMain().usageErrorExit(Msg.ARE_MUTUALLY_EXCLUSIVE.format(myarg, 'ou|org|orgunit'))
      query = _getMain().getString(Cmd.OB_QUERY)
      policy['policyQuery'] = {'query': query}
    else:
      _getMain().unknownArgumentExit()
  if 'policyQuery' not in policy:
    _getMain().missingArgumentExit('ou|org|orgunit|group|query')
  policy['customer'] = _getMain()._getCustomersCustomerIdWithC()
  try:
    if updateCmd:
      result = _getMain()._getMain().callGAPI(ci.policies(), 'patch',
                        bailOnInternalError=True,
                        throwReasons=[GAPI.INVALID, GAPI.INVALID_ARGUMENT, GAPI.UNIMPLEMENTED_ERROR,
                                      GAPI.NOT_FOUND, GAPI.PERMISSION_DENIED, GAPI.INTERNAL_ERROR],
                        name=pname, body=policy)
    else:
      result = _getMain()._getMain().callGAPI(ci.policies(), 'create',
                        bailOnInternalError=True,
                        throwReasons=[GAPI.INVALID, GAPI.INVALID_ARGUMENT, GAPI.UNIMPLEMENTED_ERROR,
                                      GAPI.NOT_FOUND, GAPI.PERMISSION_DENIED, GAPI.INTERNAL_ERROR],
                        body=policy)
    if result['done']:
      if 'error' not in result:
        if not updateCmd:
          pname = result['response'].get('id', pname)
        _getMain().entityActionPerformed([Ent.POLICY, pname])
      else:
        _getMain().entityActionFailedWarning([Ent.POLICY, pname], result['error']['message'])
    else:
      _getMain().entityActionPerformedMessage([Ent.POLICY, pname], Msg.ACTION_IN_PROGRESS.format('delete'))
  except (GAPI.invalid, GAPI.invalidArgument, GAPI.unimplementedError,
          GAPI.notFound, GAPI.permissionDenied, GAPI.internalError) as e:
    _getMain().entityActionFailedWarning([Ent.POLICY, pname], str(e))

# gam delete policies <CIPolicyNameEntity>
def doDeleteCIPolicies():
  _checkPoliciesWithDASA()
  ci = _getMain().buildGAPIObject(API.CLOUDIDENTITY_POLICY)
  entityList = _getMain().getEntityList(Cmd.OB_CIPOLICY_NAME_ENTITY)
  _getMain().checkForExtraneousArguments()
  i = 0
  count = len(entityList)
  for pname in entityList:
    i += 1
    if pname.startswith('policies/'):
      try:
        policies  = [_getMain()._getMain().callGAPI(ci.policies(), 'get',
                              bailOnInternalError=True,
                              throwReasons=[GAPI.INVALID, GAPI.INVALID_ARGUMENT,
                                            GAPI.NOT_FOUND, GAPI.PERMISSION_DENIED, GAPI.INTERNAL_ERROR],
                              name=pname, fields='name')]
      except (GAPI.invalid, GAPI.invalidArgument, GAPI.notFound, GAPI.permissionDenied, GAPI.internalError) as e:
        _getMain().entityActionFailedWarning([Ent.POLICY, pname], str(e), i, count)
        continue
    else:
      if pname.startswith('settings/'):
        pname = pname.split('/')[1]
      ifilter = f"setting.type.matches('{pname}')"
      _getMain().printGettingAllAccountEntities(Ent.POLICY, ifilter)
      policies = _filterPolicies(ci, _getMain().getPageMessage(), ifilter)
    jcount = len(policies)
    _getMain().performActionNumItems(jcount, Ent.POLICY)
    Ind.Increment()
    j = 0
    for policy in policies:
      j += 1
      pname = policy['name']
      try:
        result = _getMain()._getMain().callGAPI(ci.policies(), 'delete',
                          bailOnInternalError=True,
                          throwReasons=[GAPI.INVALID, GAPI.INVALID_ARGUMENT,
                                        GAPI.NOT_FOUND, GAPI.PERMISSION_DENIED, GAPI.INTERNAL_ERROR],
                          name=pname)
        if result['done']:
          if 'error' not in result:
            _getMain().entityActionPerformed([Ent.POLICY, pname], j, jcount)
          else:
            _getMain().entityActionFailedWarning([Ent.POLICY, pname], result['error']['message'], j, jcount)
        else:
          _getMain().entityActionPerformedMessage([Ent.POLICY, pname], Msg.ACTION_IN_PROGRESS.format('delete'), j, jcount)
      except (GAPI.invalid, GAPI.invalidArgument, GAPI.notFound, GAPI.permissionDenied, GAPI.internalError) as e:
        _getMain().entityActionFailedWarning([Ent.POLICY, pname], str(e), j, jcount)
    Ind.Decrement()

# gam info policies <CIPolicyNameEntity>
#	[nowarnings] [noappnames] [noidmappiong]
#	[formatjson]
def doInfoCIPolicies():
  _checkPoliciesWithDASA()
  groups_ci = _getMain().buildGAPIObject(API.CLOUDIDENTITY_GROUPS)
  ci = _getMain().buildGAPIObject(API.CLOUDIDENTITY_POLICY)
  cd = _getMain().buildGAPIObject(API.DIRECTORY)
  entityList = _getMain().getEntityList(Cmd.OB_CIPOLICY_NAME_ENTITY)
  FJQC = _getMain().FormatJSONQuoteChar()
  add_warnings = True
  no_appnames = no_idmapping = False
  while Cmd.ArgumentsRemaining():
    myarg = _getMain().getArgument()
    if myarg == 'nowarnings':
      add_warnings = False
    elif myarg == 'noappnames':
      no_appnames = True
    elif myarg == 'noidmapping':
      no_idmapping = True
    else:
      FJQC.GetFormatJSON(myarg)
  i = 0
  count = len(entityList)
  for pname in entityList:
    i += 1
    if pname.startswith('policies/'):
      try:
        policies  = [_getMain()._getMain().callGAPI(ci.policies(), 'get',
                              bailOnInternalError=True,
                              throwReasons=[GAPI.INVALID, GAPI.INVALID_ARGUMENT,
                                            GAPI.NOT_FOUND, GAPI.PERMISSION_DENIED, GAPI.INTERNAL_ERROR],
                              name=pname)]
      except (GAPI.invalid, GAPI.invalidArgument, GAPI.notFound, GAPI.permissionDenied, GAPI.internalError) as e:
        _getMain().entityActionFailedWarning([Ent.POLICY, pname], str(e), i, count)
        continue
    else:
      if pname.startswith('settings/'):
        pname = pname.split('/')[1]
      ifilter = f"setting.type.matches('{pname}')"
      _getMain().printGettingAllAccountEntities(Ent.POLICY, ifilter)
      policies = _filterPolicies(ci, _getMain().getPageMessage(), ifilter)
    _showPolicies(policies, FJQC, add_warnings, no_appnames, no_idmapping,
                  None, None, cd, groups_ci)

# gam print policies [todrive <ToDriveAttribute>*]
#	[filter <String>]  [nowarnings] [noappnames] [noidmappiong]
#	[group <REMatchPattern>] [ou|org|orgunit <REMatchPattern>]
#	[formatjson [quotechar <Character>]]
# gam show policies
#	[filter <String>]  [nowarnings] [noappnames] [noidmappiong]
#	[group <REMatchPattern>] [ou|org|orgunit <REMatchPattern>]
#	[formatjson]
def doPrintShowCIPolicies():

  def _printPolicy(policy):
    row = _getMain().flattenJSON(policy, timeObjects=CIPOLICY_TIME_OBJECTS)
    if not FJQC.formatJSON:
      csvPF.WriteRowTitles(row)
    elif csvPF.CheckRowTitles(row):
      csvPF.WriteRowNoFilter({'name': policy['name'],
                              'JSON': json.dumps(_getMain().cleanJSON(policy, timeObjects=CIPOLICY_TIME_OBJECTS),
                                                 ensure_ascii=False, sort_keys=True)})

  _checkPoliciesWithDASA()
  ci = _getMain().buildGAPIObject(API.CLOUDIDENTITY_POLICY)
  groups_ci = _getMain().buildGAPIObject(API.CLOUDIDENTITY_GROUPS)
  cd = _getMain().buildGAPIObject(API.DIRECTORY)
  csvPF = _getMain().CSVPrintFile(['name']) if Act.csvFormat() else None
  FJQC = _getMain().FormatJSONQuoteChar(csvPF)
  ifilter = None
  add_warnings = True
  no_appnames = no_idmapping = False
  groupEmailPattern = orgUnitPathPattern = None
  while Cmd.ArgumentsRemaining():
    myarg = _getMain().getArgument()
    if csvPF and myarg == 'todrive':
      csvPF.GetTodriveParameters()
    elif myarg == 'filter':
      ifilter = _getMain().getString(Cmd.OB_STRING)
    elif myarg == 'nowarnings':
      add_warnings = False
    elif myarg == 'noappnames':
      no_appnames = True
    elif myarg == 'noidmapping':
      no_idmapping = True
    elif myarg == 'group':
      groupEmailPattern = _getMain().getREPattern(re.IGNORECASE)
    elif myarg in {'ou', 'org', 'orgunit'}:
      orgUnitPathPattern = _getMain().getREPattern(re.IGNORECASE)
    else:
      FJQC.GetFormatJSONQuoteChar(myarg, True)
  _getMain().printGettingAllAccountEntities(Ent.POLICY, ifilter)
  policies = _filterPolicies(ci, _getMain().getPageMessage(), ifilter)
  if not csvPF:
    _showPolicies(policies, FJQC, add_warnings, no_appnames, no_idmapping,
                  groupEmailPattern, orgUnitPathPattern, cd, groups_ci)
  else:
    for policy in policies:
      if _cleanPolicy(policy, add_warnings, no_appnames, no_idmapping,
                      groupEmailPattern, orgUnitPathPattern, cd, groups_ci):
        _printPolicy(policy)
  if csvPF:
    csvPF.writeCSVfile('Policies')

# gam print cigroups [todrive <ToDriveAttribute>*]
#	[(cimember|ciowner <UserItem>)|(select <GroupEntity>)|(query <String>)]
#	[showownedby <UserItem>]
#	[emailmatchpattern [not] <REMatchPattern>] [namematchpattern [not] <REMatchPattern>]
#	[descriptionmatchpattern [not] <REMatchPattern>]
#	[basic|allfields|(<CIGroupFieldName>* [fields <CIGroupFieldNameList>])]
#	[roles <GroupRoleList>] [memberrestrictions]
#	[members|memberscount] [managers|managerscount] [owners|ownerscount] [totalcount] [countsonly]
#	[internal] [internaldomains all|primary|<DomainNameList>] [external]
#	[types <CIGroupMemberTypeList>]
#	[memberemaildisplaypattern|memberemailskippattern <REMatchPattern>]
#	[convertcrnl] [delimiter <Character>]
#	(addcsvdata <FieldName> <String>)* [includecsvdatainjson [<Boolean>]]
#	[formatjson [quotechar <Character>]]
# 	[showitemcountonly]
def doPrintCIGroups():
  def _printGroupRow(groupEntity, groupMembers):
    nonlocal itemCount
    for member in groupMembers:
      _getMain().getCIGroupMemberRoleFixType(member)
    if showOwnedBy and not checkCIGroupShowOwnedBy(showOwnedBy, groupMembers):
      return
    if showItemCountOnly:
      itemCount += 1
      return
    if not keepName:
      groupEntity.pop('name', None)
    row = {}
    if allowExternalMembers is not None:
      row['allowExternalMembers'] = allowExternalMembers
    if addCSVData:
      row.update(addCSVData)
    if FJQC.formatJSON:
      row['email'] = groupEntity['groupKey']['id'].lower()
      if addCSVData and includeCSVDataInJSON:
        groupEntity.update(addCSVData)
      row['JSON'] = json.dumps(_getMain().cleanJSON(groupEntity, timeObjects=_getMain().CIGROUP_TIME_OBJECTS), ensure_ascii=False, sort_keys=True)
      if rolesSet and groupMembers is not None:
        row['JSON-members'] = json.dumps(groupMembers, ensure_ascii=False, sort_keys=True)
      csvPF.WriteRowNoFilter(row)
      return
    _getMain().mapCIGroupFieldNames(groupEntity)
    for k, v in groupEntity.pop('labels', {}).items():
      if v == '':
        groupEntity[f'labels{GC.Values[GC.CSV_OUTPUT_SUBFIELD_DELIMITER]}{k}'] = True
      else:
        groupEntity[f'labels{GC.Values[GC.CSV_OUTPUT_SUBFIELD_DELIMITER]}{k}'] = v
    for key, value in sorted(_getMain().flattenJSON(groupEntity, flattened={}, timeObjects=_getMain().CIGROUP_TIME_OBJECTS).items()):
      csvPF.AddTitles(key)
      row[key] = value
    if rolesSet and groupMembers is not None:
      _getMain().addMemberInfoToRow(row, groupMembers, typesSet, memberOptions, memberDisplayOptions, delimiter,
                         False, False, True)
    csvPF.WriteRow(row)

  cd = _getMain().buildGAPIObject(API.DIRECTORY)
  ci = _getMain().buildGAPIObject(API.CLOUDIDENTITY_GROUPS)
  _getMain().setTrueCustomerId(cd)
  parent = f'customers/{GC.Values[GC.CUSTOMER_ID]}'
  delimiter = GC.Values[GC.CSV_OUTPUT_FIELD_DELIMITER]
  memberRestrictions = sortHeaders = False
  memberDisplayOptions = _getMain().initIPSGMGroupMemberDisplayOptions()
  pageSize = 500
  groupFieldsLists = {'ci': ['groupKey']}
  csvPF = _getMain().CSVPrintFile(['email'])
  FJQC = _getMain().FormatJSONQuoteChar(csvPF)
  rolesSet = set()
  typesSet = set()
  memberOptions = _getMain().initMemberOptions()
  allowExternalMembers = entitySelection = groupMembers = memberQuery = query = showOwnedBy = None
  matchPatterns = {}
  showItemCountOnly = False
  addCSVData = {}
  includeCSVDataInJSON = False
  while Cmd.ArgumentsRemaining():
    myarg = _getMain().getArgument()
    if myarg == 'todrive':
      csvPF.GetTodriveParameters()
    elif myarg == 'showownedby':
      showOwnedBy = _getMain().convertUIDtoEmailAddress(_getMain().getEmailAddress(), emailTypes=['user'])
    elif myarg in {'cimember', 'enterprisemember', 'ciowner'}:
      emailAddress = _getMain().convertUIDtoEmailAddress(_getMain().getEmailAddress(), emailTypes=['user', 'group'])
      memberQuery = f"member_key_id == '{emailAddress}' && '{CIGROUP_DISCUSSION_FORUM_LABEL}' in labels && parent == '{parent}'"
      entitySelection = None
      if myarg == 'ciowner':
        showOwnedBy = emailAddress
    elif myarg == 'query':
      query = _getMain().getString(Cmd.OB_QUERY)
      entitySelection = None
    elif _getMain().getGroupMatchPatterns(myarg, matchPatterns, True):
      pass
    elif myarg == 'select':
      entitySelection = _getMain().getEntityList(Cmd.OB_GROUP_ENTITY)
      query = None
    elif myarg == 'maxresults':
      pageSize = _getMain().getInteger(minVal=1, maxVal=500)
    elif myarg == 'delimiter':
      delimiter = _getMain().getCharacter()
    elif myarg in {'allfields', 'ciallfields', 'allcifields'}:
      sortHeaders = True
      groupFieldsLists = {'ci': []}
      for field in _getMain().CIGROUP_FIELDS_CHOICE_MAP:
        _getMain().addFieldToFieldsList(field, _getMain().CIGROUP_FIELDS_CHOICE_MAP, groupFieldsLists['ci'])
    elif myarg == 'basic':
      sortHeaders = True
      groupFieldsLists = {'ci': ['*']}
    elif myarg == 'sortheaders':
      sortHeaders = _getMain().getBoolean()
    elif myarg in _getMain().CIGROUP_FIELDS_CHOICE_MAP:
      csvPF.AddField(myarg, _getMain().CIGROUP_FIELDS_CHOICE_MAP, groupFieldsLists['ci'])
    elif myarg in {'fields', 'cifields'}:
      for field in _getMain()._getFieldsList():
        if field in _getMain().CIGROUP_FIELDS_CHOICE_MAP:
          csvPF.AddField(field, _getMain().CIGROUP_FIELDS_CHOICE_MAP, groupFieldsLists['ci'])
        else:
          _getMain().invalidChoiceExit(field, list(_getMain().CIGROUP_FIELDS_CHOICE_MAP), True)
    elif _getMain().getPGGroupRolesMemberDisplayOptions(myarg, rolesSet, memberDisplayOptions):
      pass
    elif getCIGroupMemberTypes(myarg, typesSet):
      pass
    elif _getMain().getMemberMatchOptions(myarg, memberOptions):
      pass
    elif myarg == 'memberrestrictions':
      memberRestrictions = True
    elif myarg == 'showitemcountonly':
      showItemCountOnly = True
    elif myarg == 'addcsvdata':
      _getMain().getAddCSVData(addCSVData)
    elif myarg == 'includecsvdatainjson':
      includeCSVDataInJSON = _getMain().getBoolean()
    else:
      FJQC.GetFormatJSONQuoteChar(myarg, False)
  if not typesSet:
    typesSet = ALL_CIGROUP_MEMBER_TYPES
  showCategory, _ = _getMain().finalizeIPSGMGroupRolesMemberDisplayOptions(cd, memberDisplayOptions, False)
  fields = ','.join(set(groupFieldsLists['ci']))
  csvPF.MapTitles('name', 'id')
  csvPF.MapTitles('displayName', 'name')
  csvPF.RemoveTitles('labels')
  updateFieldsForCIGroupMatchPatterns(matchPatterns, groupFieldsLists['ci'], csvPF)
  if groupFieldsLists['ci'] and groupFieldsLists['ci'][0] != '*':
    keepName = 'name' in groupFieldsLists['ci']
    groupFieldsLists['ci'].append('name')
    fields = ','.join(set(groupFieldsLists['ci']))
  else:
    keepName = True
    fields = '*'
  fieldsnp = f'nextPageToken,groups({fields})'
  if FJQC.formatJSON:
    sortHeaders = False
    if showCategory:
      csvPF.AddJSONTitles(['allowExternalMembers'])
    if addCSVData:
      csvPF.AddJSONTitles(sorted(addCSVData.keys()))
    csvPF.AddJSONTitles('JSON')
    if rolesSet:
      csvPF.AddJSONTitle('JSON-members')
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
  if rolesSet:
    _getMain().setMemberDisplayTitles(memberDisplayOptions, csvPF)
  if memberQuery:
    _getMain().printGettingAllAccountEntities(Ent.CLOUD_IDENTITY_GROUP, memberQuery)
    try:
      result = _getMain().callGAPIpages(ci.groups().memberships(), 'searchTransitiveGroups', 'memberships',
                             pageMessage=_getMain().getPageMessage(showFirstLastItems=True), messageAttribute=['groupKey', 'id'],
                             throwReasons=GAPI.CIGROUP_LIST_USERKEY_THROW_REASONS, retryReasons=GAPI.CIGROUP_RETRY_REASONS,
                             parent='groups/-', query=memberQuery,
                             fields='nextPageToken,memberships(group,groupKey(id),relationType)', pageSize=pageSize)
      entitySelection = [{'email': entity['groupKey']['id'], 'name': entity['group']} for entity in result if entity['relationType'] == 'DIRECT']
    except (GAPI.resourceNotFound, GAPI.domainNotFound, GAPI.domainCannotUseApis,
            GAPI.forbidden, GAPI.badRequest, GAPI.invalid,
            GAPI.systemError, GAPI.permissionDenied, GAPI.invalidArgument, GAPI.serviceNotAvailable) as e:
      _getMain().entityActionFailedWarning([Ent.CLOUD_IDENTITY_GROUP, None], str(e))
      return
  getFullFieldsList = []
  if entitySelection is None:
    if groupFieldsLists['ci']:
      for field in groupFieldsLists['ci']:
        if field in _getMain().CIGROUP_FULL_FIELDS:
          getFullFieldsList.append(field)
    else:
      getFullFieldsList = list(_getMain().CIGROUP_FULL_FIELDS)
    getFullFields = ','.join(getFullFieldsList)#
    if query:
      method = 'search'
      if 'parent' not in query:
        query += f" && parent == '{parent}'"
      kwargs = {'query': query}
    else:
      method = 'list'
      kwargs = {'parent': parent}
    _getMain().printGettingAllAccountEntities(Ent.CLOUD_IDENTITY_GROUP, query)
    try:
      entityList = _getMain().callGAPIpages(ci.groups(), method, 'groups',
                                 pageMessage=_getMain().getPageMessage(showFirstLastItems=True), messageAttribute=['groupKey', 'id'],
                                 throwReasons=GAPI.CIGROUP_LIST_THROW_REASONS, retryReasons=GAPI.CIGROUP_RETRY_REASONS,
                                 view='FULL', fields=fieldsnp, pageSize=pageSize, **kwargs)
    except (GAPI.resourceNotFound, GAPI.domainNotFound, GAPI.domainCannotUseApis,
            GAPI.forbidden, GAPI.badRequest, GAPI.invalid, GAPI.invalidArgument,
            GAPI.systemError, GAPI.permissionDenied, GAPI.serviceNotAvailable) as e:
      _getMain().entityActionFailedWarning([Ent.CLOUD_IDENTITY_GROUP, None], str(e))
      return
  else:
    getFullFields = ''
    entityList = []
    i = 0
    count = len(entitySelection)
    for group in entitySelection:
      i += 1
      if isinstance(group, dict):
        name = group['name']
        groupEmail = group['email']
      else:
        _, name, groupEmail = _getMain().convertGroupEmailToCloudID(ci, group, i, count)
      _getMain().printGettingEntityItemForWhom(Ent.CLOUD_IDENTITY_GROUP, groupEmail, i, count)
      kvList = [Ent.CLOUD_IDENTITY_GROUP, groupEmail]
      if name:
        try:
          ciGroup = _getMain()._getMain().callGAPI(ci.groups(), 'get',
                             throwReasons=GAPI.CIGROUP_GET_THROW_REASONS, retryReasons=GAPI.CIGROUP_RETRY_REASONS,
                             name=name, fields=fields)
          entityList.append(ciGroup)
        except (GAPI.notFound, GAPI.domainNotFound, GAPI.domainCannotUseApis,
                GAPI.forbidden, GAPI.badRequest, GAPI.invalid, GAPI.invalidArgument,
                GAPI.systemError, GAPI.permissionDenied, GAPI.serviceNotAvailable) as e:
          _getMain().entityActionFailedWarning(kvList, str(e), i, count)
  itemCount = 0
  i = 0
  count = len(entityList)
  for groupEntity in entityList:
    i += 1
    groupEmail = groupEntity['groupKey']['id'].lower()
    if not _getMain().checkGroupMatchPatterns(groupEmail, groupEntity, matchPatterns):
      continue
    kvList = [Ent.CLOUD_IDENTITY_GROUP, groupEmail]
    if getFullFields:
      try:
        fullInfo = _getMain()._getMain().callGAPI(ci.groups(), 'get',
                            throwReasons=GAPI.CIGROUP_GET_THROW_REASONS, retryReasons=GAPI.CIGROUP_RETRY_REASONS,
                            name=groupEntity['name'], fields=getFullFields)
        groupEntity.update(fullInfo)
      except (GAPI.notFound, GAPI.domainNotFound, GAPI.domainCannotUseApis,
              GAPI.forbidden, GAPI.badRequest, GAPI.invalid, GAPI.invalidArgument,
              GAPI.systemError, GAPI.permissionDenied, GAPI.serviceNotAvailable) as e:
        _getMain().entityActionFailedWarning(kvList, str(e), i, count)
    if showCategory:
      allowExternalMembers = _getMain().getGroupAllowExternalMembers(memberDisplayOptions['gs'], groupEmail, False,
                                                          kvList, i, count)
      if allowExternalMembers is None:
        continue
    groupMembers = {}
    if getRoles:
      _getMain().printGettingEntityItemForWhom(getRoles, groupEmail, i, count)
      try:
        groupMembers = _getMain().callGAPIpages(ci.groups().memberships(), 'list', 'memberships',
                                     throwReasons=GAPI.MEMBERS_THROW_REASONS, retryReasons=GAPI.MEMBERS_RETRY_REASONS,
                                     pageMessage=_getMain().getPageMessage(), messageAttribute=['preferredMemberKey', 'id'],
                                     parent=groupEntity['name'], view='FULL', fields='*', pageSize=pageSize)
      except (GAPI.groupNotFound, GAPI.domainNotFound, GAPI.domainCannotUseApis, GAPI.invalid, GAPI.forbidden):
        _getMain().entityUnknownWarning(Ent.CLOUD_IDENTITY_GROUP, groupEmail, i, count)
      except (GAPI.conditionNotMet, GAPI.serviceNotAvailable) as e:
        _getMain().entityActionFailedWarning([Ent.CLOUD_IDENTITY_GROUP, groupEmail], str(e), i, count)
    if memberRestrictions:
      _getMain().printGettingEntityItemForWhom(Ent.MEMBER_RESTRICTION, groupEmail, i, count)
      try:
        secInfo = _getMain()._getMain().callGAPI(ci.groups(), 'getSecuritySettings',
                           throwReasons=GAPI.CIGROUP_GET_THROW_REASONS, retryReasons=GAPI.CIGROUP_RETRY_REASONS,
                           name=f"{groupEntity['name']}/securitySettings", readMask='*')
        if 'memberRestriction' in secInfo:
          groupEntity['memberRestrictionQuery'] = secInfo['memberRestriction'].get('query', '')
          groupEntity['memberRestrictionEvaluation'] = secInfo['memberRestriction'].get('evaluation', {}).get('state', '')
      except (GAPI.notFound, GAPI.domainNotFound, GAPI.domainCannotUseApis,
              GAPI.forbidden, GAPI.badRequest, GAPI.invalid, GAPI.invalidArgument,
              GAPI.systemError, GAPI.permissionDenied, GAPI.serviceNotAvailable) as e:
        _getMain().entityActionFailedWarning([Ent.CLOUD_IDENTITY_GROUP, groupEmail], str(e), i, count)
    _printGroupRow(groupEntity, groupMembers)
  if showItemCountOnly:
    _getMain().writeStdout(f'{itemCount}\n')
    return
  if sortHeaders:
    sortTitles = ['email']
    if showCategory:
      sortTitles.append('allowExternalMembers')
    if addCSVData:
      sortTitles.extend(sorted(addCSVData.keys()))
    sortTitles.extend(_getMain().CIGROUP_PRINT_ORDER)
    if rolesSet:
      _getMain().setMemberDisplaySortTitles(memberDisplayOptions, sortTitles)
    csvPF.SetSortTitles(sortTitles)
  csvPF.SortRows('email', False)
  csvPF.writeCSVfile('Cloud Identity Groups')

# gam <UserTypeEntity> info cimember <GroupEntity>
def infoCIGroupMembers(entityList):
  _getMain().infoGroupMembers(entityList, True)

# gam info cimember <UserTypeEntity> <GroupEntity>
def doInfoCIGroupMembers():
  _getMain().infoGroupMembers(_getMain().getEntityToModify(defaultEntityType=Cmd.ENTITY_USERS)[1], True)

def getCIGroupMembersEntityList(ci, entityList, query, subTitle, matchPatterns, fieldsList, csvPF):
  if query:
    _getMain().printGettingAllAccountEntities(Ent.CLOUD_IDENTITY_GROUP, query)
    parent = 'groups/-'
    try:
      result = _getMain().callGAPIpages(ci.groups().memberships(), 'searchTransitiveGroups', 'memberships',
                             pageMessage=_getMain().getPageMessage(showFirstLastItems=True), messageAttribute=['groupKey', 'id'],
                             throwReasons=GAPI.CIGROUP_LIST_USERKEY_THROW_REASONS, retryReasons=GAPI.CIGROUP_RETRY_REASONS,
                             parent=parent, query=query,
                             fields='nextPageToken,memberships(groupKey(id),relationType)', pageSize=500)
      entityList = [entity['groupKey']['id'] for entity in result if entity['relationType'] == 'DIRECT']
    except (GAPI.resourceNotFound, GAPI.domainNotFound, GAPI.domainCannotUseApis,
            GAPI.forbidden, GAPI.badRequest, GAPI.invalid,
            GAPI.systemError, GAPI.permissionDenied, GAPI.invalidArgument, GAPI.serviceNotAvailable) as e:
      _getMain().entityActionFailedExit([Ent.CLOUD_IDENTITY_GROUP, parent], str(e))
  elif entityList is None:
    updateFieldsForCIGroupMatchPatterns(matchPatterns, fieldsList, csvPF)
    _getMain().printGettingAllAccountEntities(Ent.CLOUD_IDENTITY_GROUP, subTitle)
    parent = f'customers/{GC.Values[GC.CUSTOMER_ID]}'
    try:
      entityList = _getMain().callGAPIpages(ci.groups(), 'list', 'groups',
                                 pageMessage=_getMain().getPageMessage(showFirstLastItems=True), messageAttribute=['groupKey', 'id'],
                                 throwReasons=GAPI.CIGROUP_LIST_THROW_REASONS, retryReasons=GAPI.CIGROUP_RETRY_REASONS,
                                 parent=parent, view='FULL',
                                 fields=f'nextPageToken,groups({",".join(set(fieldsList))})', pageSize=500)
    except (GAPI.resourceNotFound, GAPI.domainNotFound, GAPI.domainCannotUseApis,
            GAPI.forbidden, GAPI.badRequest, GAPI.invalid, GAPI.invalidArgument,
            GAPI.systemError, GAPI.permissionDenied, GAPI.serviceNotAvailable) as e:
      _getMain().entityActionFailedExit([Ent.CLOUD_IDENTITY_GROUP, parent], str(e))
  else:
    _getMain().clearUnneededGroupMatchPatterns(matchPatterns)
  return entityList

def getCIGroupTransitiveMembers(ci, groupName, membersList, i, count):
  try:
    groupMembers = _getMain().callGAPIpages(ci.groups().memberships(), 'searchTransitiveMemberships', 'memberships',
                                 throwReasons=GAPI.CIGROUP_LIST_THROW_REASONS, retryReasons=GAPI.CIGROUP_RETRY_REASONS,
                                 parent=groupName,
                                 fields='nextPageToken,memberships(*)', pageSize=GC.Values[GC.MEMBER_MAX_RESULTS])
  except (GAPI.resourceNotFound, GAPI.domainNotFound, GAPI.domainCannotUseApis,
          GAPI.forbidden, GAPI.badRequest, GAPI.invalid, GAPI.invalidArgument, GAPI.systemError, GAPI.serviceNotAvailable):
    _getMain().entityUnknownWarning(Ent.CLOUD_IDENTITY_GROUP, groupName, i, count)
    return False
  except GAPI.permissionDenied as e:
    _getMain().entityActionFailedWarning([Ent.CLOUD_IDENTITY_GROUP, groupName], str(e))
    return False
  for member in groupMembers:
    membersList.append(_getMain().getCIGroupTransitiveMemberRoleFixType(groupName, member))
  return True

def getCIGroupMembers(cd, ci, groupName, memberRoles, membersList, membersSet, i, count,
                      memberOptions, memberDisplayOptions, level, typesSet, groupEmail, kwargs):
  nameToPrint = groupEmail if groupEmail else groupName
  _getMain().printGettingAllEntityItemsForWhom(memberRoles if memberRoles else Ent.ROLE_MANAGER_MEMBER_OWNER, nameToPrint, i, count)
  validRoles = _getMain()._getCIRoleVerification(memberRoles)
  if memberOptions[MEMBEROPTION_INCLUDEDERIVEDMEMBERSHIP]:
    groupMembers = []
    if not getCIGroupTransitiveMembers(ci, groupName, groupMembers, i, count):
      return
    for member in groupMembers:
      if _getMain()._checkMemberRole(member, validRoles):
        if member['type'] in typesSet and _getMain()._checkCIMemberMatch(member, memberOptions):
          membersList.append(member)
    return
  if not groupEmail.startswith('space/'):
    try:
      groupMembers = _getMain().callGAPIpages(ci.groups().memberships(), 'list', 'memberships',
                                   pageMessage=_getMain().getPageMessageForWhom(),
                                   throwReasons=GAPI.CIGROUP_LIST_THROW_REASONS, retryReasons=GAPI.CIGROUP_RETRY_REASONS,
                                   parent=groupName, **kwargs)
    except (GAPI.resourceNotFound, GAPI.domainNotFound, GAPI.domainCannotUseApis,
            GAPI.forbidden, GAPI.badRequest, GAPI.invalid, GAPI.invalidArgument, GAPI.systemError,
            GAPI.permissionDenied, GAPI.serviceNotAvailable):
      _getMain().entityUnknownWarning(Ent.CLOUD_IDENTITY_GROUP, nameToPrint, i, count)
      return
  else:
    groupMembers = _getMain()._getChatSpaceMembers(cd, groupEmail, groupName)
  checkShowCategory = memberDisplayOptions['checkShowCategory']
  if not memberOptions[MEMBEROPTION_RECURSIVE]:
    if memberOptions[MEMBEROPTION_NODUPLICATES]:
      for member in groupMembers:
        _getMain().getCIGroupMemberRoleFixType(member)
        memberName = member.get('preferredMemberKey', {}).get('id', '')
        if (_getMain()._checkMemberRole(member, validRoles) and
            (not checkShowCategory or _getMain()._checkCIMemberCategory(member, memberDisplayOptions)) and
            memberName not in membersSet):
          membersSet.add(memberName)
          if member['type'] in typesSet and _getMain()._checkCIMemberMatch(member, memberOptions):
            membersList.append(member)
    else:
      for member in groupMembers:
        _getMain().getCIGroupMemberRoleFixType(member)
        if (_getMain()._checkMemberRole(member, validRoles) and
            (not checkShowCategory or _getMain()._checkCIMemberCategory(member, memberDisplayOptions))):
          if member['type'] in typesSet and _getMain()._checkCIMemberMatch(member, memberOptions):
            membersList.append(member)
  elif memberOptions[MEMBEROPTION_NODUPLICATES]:
    groupMemberList = []
    for member in groupMembers:
      _getMain().getCIGroupMemberRoleFixType(member)
      memberName = member.get('preferredMemberKey', {}).get('id', '')
      if member['type'] != Ent.TYPE_GROUP:
        if (member['type'] in typesSet and
            _getMain()._checkCIMemberMatch(member, memberOptions) and
            _getMain()._checkMemberRole(member, validRoles) and
            (not checkShowCategory or _getMain()._checkCIMemberCategory(member, memberDisplayOptions)) and
            memberName not in membersSet):
          membersSet.add(memberName)
          member['level'] = level
          member['subgroup'] = nameToPrint
          membersList.append(member)
      else:
        if memberName not in membersSet:
          membersSet.add(memberName)
          if (member['type'] in typesSet and
              _getMain()._checkCIMemberMatch(member, memberOptions) and
              (not checkShowCategory or _getMain()._checkCIMemberCategory(member, memberDisplayOptions))):
            member['level'] = level
            member['subgroup'] = nameToPrint
            membersList.append(member)
          _, gname = member['name'].rsplit('/', 1)
          groupMemberList.append((f'groups/{gname}', memberName))
    for member in groupMemberList:
      getCIGroupMembers(cd, ci, member[0], memberRoles, membersList, membersSet, i, count,
                        memberOptions, memberDisplayOptions, level+1, typesSet, member[1], kwargs)
  else:
    for member in groupMembers:
      _getMain().getCIGroupMemberRoleFixType(member)
      memberName = member.get('preferredMemberKey', {}).get('id', '')
      if member['type'] != Ent.TYPE_GROUP:
        if (member['type'] in typesSet and
            _getMain()._checkCIMemberMatch(member, memberOptions) and
            _getMain()._checkMemberRole(member, validRoles) and
            (not checkShowCategory or _getMain()._checkCIMemberCategory(member, memberDisplayOptions))):
          member['level'] = level
          member['subgroup'] = nameToPrint
          membersList.append(member)
      else:
        if (member['type'] in typesSet and
            _getMain()._checkCIMemberMatch(member, memberOptions) and
            (not checkShowCategory or _getMain()._checkCIMemberCategory(member, memberDisplayOptions))):
          member['level'] = level
          member['subgroup'] = nameToPrint
          membersList.append(member)
        _, gname = member['name'].rsplit('/', 1)
        getCIGroupMembers(cd, ci, f'groups/{gname}', memberRoles, membersList, membersSet, i, count,
                          memberOptions, memberDisplayOptions, level+1, typesSet, memberName, kwargs)

CIGROUPMEMBERS_FIELDS_CHOICE_MAP = {
  'createtime': 'createTime',
  'delivery': 'deliverySetting',
  'deliverysettings': 'deliverySetting',
  'email': 'preferredMemberKey',
  'expiretime': 'expireTime',
  'id': 'name',
  'memberkey': 'preferredMemberKey',
  'name': 'name',
  'preferredmemberkey': 'preferredMemberKey',
  'role': 'roles',
  'roles': 'roles',
  'type': 'type',
  'updatetime': 'updateTime',
  'useremail': 'preferredMemberKey',
  }
CIGROUPMEMBERS_DEFAULT_FIELDS = [
  'type', 'roles', 'name', 'preferredmemberkey', 'createtime', 'updatetime', 'expiretime']
CIGROUPMEMBERS_SORT_FIELDS = [
  'type', 'role', 'id', 'email',
  'name', 'preferredMemberKey.id', 'preferredMemberKey.namespace',
  'createTime', 'updateTime', 'expireTime'
  ]
CIGROUPMEMBERS_TIME_OBJECTS = {'createTime', 'updateTime', 'expireTime'}

def _getCIListGroupMembersArgs(listView):
  if listView == 'full':
    return  {'view': 'FULL', 'pageSize': GC.Values[GC.MEMBER_MAX_RESULTS_CI_FULL],
             'fields': 'nextPageToken,memberships(*)'}
  if listView == 'basic':
    return  {'view': 'FULL', 'pageSize': GC.Values[GC.MEMBER_MAX_RESULTS_CI_FULL],
             'fields': 'nextPageToken,memberships(name,preferredMemberKey,roles,type)'}
  return {'view': 'BASIC', 'pageSize': GC.Values[GC.MEMBER_MAX_RESULTS_CI_BASIC],
             'fields': 'nextPageToken,memberships(*)'}

# gam print cigroup-members [todrive <ToDriveAttribute>*]
#	[(cimember|ciowner <UserItem>)|(cigroup <GroupItem>)|(select <GroupEntity>)]
#	[showownedby <UserItem>]
#	[emailmatchpattern [not] <REMatchPattern>] [namematchpattern [not] <REMatchPattern>]
#	[descriptionmatchpattern [not] <REMatchPattern>]
#	[roles <GroupRoleList>] [members] [managers] [owners]
#	[internal] [internaldomains all|primary|<DomainNameList>] [external]
#	[verifyallowexternal [<Boolean>]]
#	[types <CIGroupMemberTypeList>]
#	[memberemaildisplaypattern|memberemailskippattern <REMatchPattern>]
#	<CIGroupMembersFieldName>* [fields <CIGroupMembersFieldNameList>]
#	[minimal|basic|full]
#	[(recursive [noduplicates])|includederivedmembership] [nogroupeemail]
#	(addcsvdata <FieldName> <String>)* [includecsvdatainjson [<Boolean>]]
#	[formatjson [quotechar <Character>]]
def doPrintCIGroupMembers():
  cd = _getMain().buildGAPIObject(API.DIRECTORY)
  ci = _getMain().buildGAPIObject(API.CLOUDIDENTITY_GROUPS)
  _getMain().setTrueCustomerId(cd)
  parent = f'customers/{GC.Values[GC.CUSTOMER_ID]}'
  memberOptions = _getMain().initMemberOptions()
  memberDisplayOptions = _getMain().initIPSGMGroupMemberDisplayOptions()
  groupColumn = True
  subTitle = f'{Msg.ALL} {Ent.Plural(Ent.CLOUD_IDENTITY_GROUP)}'
  fieldsList = []
  groupFieldsLists = {'ci': ['groupKey', 'name']}
  csvPF = _getMain().CSVPrintFile(['group'])
  FJQC = _getMain().FormatJSONQuoteChar(csvPF)
  allowExternalMembers = entityList = query = showOwnedBy = None
  verifyAllowExternal = False
  rolesSet = set()
  typesSet = set()
  matchPatterns = {}
  listView = 'full'
  addCSVData = {}
  while Cmd.ArgumentsRemaining():
    myarg = _getMain().getArgument()
    if myarg == 'todrive':
      csvPF.GetTodriveParameters()
    elif myarg == 'showownedby':
      showOwnedBy = _getMain().convertUIDtoEmailAddress(_getMain().getEmailAddress(), emailTypes=['user'])
    elif myarg in {'cimember', 'enterprisemember', 'ciowner'}:
      emailAddress = _getMain().convertUIDtoEmailAddress(_getMain().getEmailAddress(), emailTypes=['user', 'group'])
      query = f"member_key_id == '{emailAddress}' && '{CIGROUP_DISCUSSION_FORUM_LABEL}' in labels && parent == '{parent}'"
      entityList = None
      if myarg == 'ciowner':
        showOwnedBy = emailAddress
    elif myarg in {'cigroup', 'group'}:
      entityList = [_getMain().getString(Cmd.OB_EMAIL_ADDRESS)]
      subTitle = f'{Ent.Singular(Ent.CLOUD_IDENTITY_GROUP)}={entityList[0]}'
      query = None
    elif _getMain().getGroupMatchPatterns(myarg, matchPatterns, True):
      pass
    elif myarg == 'select':
      entityList = _getMain().getEntityList(Cmd.OB_GROUP_ENTITY)
      subTitle = f'{Msg.SELECTED} {Ent.Plural(Ent.CLOUD_IDENTITY_GROUP)}'
      query = None
    elif _getMain().getIPSGMGroupRolesMemberDisplayOptions(myarg, rolesSet, memberDisplayOptions):
      pass
    elif getCIGroupMemberTypes(myarg, typesSet):
      pass
    elif _getMain().getMemberMatchOptions(myarg, memberOptions):
      pass
    elif _getMain().getFieldsList(myarg, CIGROUPMEMBERS_FIELDS_CHOICE_MAP, fieldsList, initialField='preferredMemberKey'):
      pass
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
    elif myarg in {'minimal', 'basic', 'full'}:
      listView = myarg
    elif myarg == 'verifyallowexternal':
      verifyAllowExternal = _getMain().getBoolean()
    elif myarg == 'addcsvdata':
      _getMain().getAddCSVData(addCSVData)
    else:
      FJQC.GetFormatJSONQuoteChar(myarg, False)
  if listView == 'minimal' and memberOptions[MEMBEROPTION_RECURSIVE]:
    _getMain().usageErrorExit(Msg.ARE_MUTUALLY_EXCLUSIVE.format('minimal', 'recursive'))
  if not typesSet:
    typesSet = {Ent.TYPE_USER} if memberOptions[MEMBEROPTION_RECURSIVE] else ALL_CIGROUP_MEMBER_TYPES
  showCategory, _ = _getMain().finalizeIPSGMGroupRolesMemberDisplayOptions(cd, memberDisplayOptions, verifyAllowExternal)
  fields = ','.join(set(groupFieldsLists['ci']))
  entityList = getCIGroupMembersEntityList(ci, entityList, query, subTitle, matchPatterns, groupFieldsLists['ci'], csvPF)
  if not fieldsList:
    for field in CIGROUPMEMBERS_DEFAULT_FIELDS:
      _getMain().addFieldToFieldsList(field, CIGROUPMEMBERS_FIELDS_CHOICE_MAP, fieldsList)
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
  displayFieldsList = fieldsList[:]
  if 'roles' in displayFieldsList:
    displayFieldsList.remove('roles')
    displayFieldsList.append('role')
  if not rolesSet:
    rolesSet = _getMain().ALL_GROUP_ROLES
  getRolesSet = rolesSet.copy()
  if showOwnedBy:
    getRolesSet.add(Ent.ROLE_OWNER)
  getRoles = ','.join(sorted(getRolesSet))
  kwargs = _getCIListGroupMembersArgs(listView)
  level = 0
  i = 0
  count = len(entityList)
  for group in entityList:
    i += 1
    if isinstance(group, dict):
      groupEntity = group
    else:
      _, name, groupEmail = _getMain().convertGroupEmailToCloudID(ci, group, i, count)
      if not name or not groupEmail:
        continue
      kvList = [Ent.CLOUD_IDENTITY_GROUP, groupEmail]
      try:
        groupEntity = _getMain()._getMain().callGAPI(ci.groups(), 'get',
                               throwReasons=GAPI.CIGROUP_GET_THROW_REASONS, retryReasons=GAPI.CIGROUP_RETRY_REASONS,
                               name=name, fields=fields)
      except (GAPI.notFound, GAPI.domainNotFound, GAPI.domainCannotUseApis,
              GAPI.forbidden, GAPI.badRequest, GAPI.invalid, GAPI.invalidArgument, GAPI.invalidArgument, GAPI.systemError,
              GAPI.permissionDenied, GAPI.serviceNotAvailable) as e:
        _getMain().entityActionFailedWarning(kvList, str(e), i, count)
        continue
    groupEmail = groupEntity['groupKey']['id'].lower()
    kvList = [Ent.CLOUD_IDENTITY_GROUP, groupEmail]
    if showCategory:
      allowExternalMembers = _getMain().getGroupAllowExternalMembers(memberDisplayOptions['gs'], groupEmail, verifyAllowExternal,
                                                          kvList, i, count)
      if allowExternalMembers is None:
        continue
    if not _getMain().checkGroupMatchPatterns(groupEmail, groupEntity, matchPatterns):
      continue
    membersList = []
    membersSet = set()
    getCIGroupMembers(cd, ci, groupEntity['name'], getRoles, membersList, membersSet, i, count,
                      memberOptions, memberDisplayOptions, level, typesSet, groupEmail, kwargs)
    if showOwnedBy and not checkCIGroupShowOwnedBy(showOwnedBy, membersList):
      continue
    for member in membersList:
      if member['role'] not in rolesSet:
        continue
      row = {}
      if groupColumn:
        row['group'] = groupEmail
      dmember = {}
      for field in displayFieldsList:
        if field in member:
          dmember[field] = member[field]
      if memberOptions[MEMBEROPTION_RECURSIVE]:
        row['level'] = member['level']
        row['subgroup'] = member['subgroup']
      if showCategory:
        row['category'] = member['category']
      if listView == 'minimal':
        dmember.pop('type', None)
      _getMain().mapCIGroupMemberFieldNames(dmember)
      if not FJQC.formatJSON:
        if allowExternalMembers is not None:
          row['allowExternalMembers'] = allowExternalMembers
        if addCSVData:
          row.update(addCSVData)
        csvPF.WriteRowTitles(_getMain().flattenJSON(dmember, flattened=row, timeObjects=CIGROUPMEMBERS_TIME_OBJECTS))
      else:
        row.update(dmember)
        fjrow = {}
        if groupColumn:
          fjrow['group'] = groupEmail
          if allowExternalMembers is not None:
            fjrow['allowExternalMembers'] = allowExternalMembers
        if addCSVData:
          fjrow.update(addCSVData)
        fjrow['JSON'] = json.dumps(_getMain().cleanJSON(row, timeObjects=CIGROUPMEMBERS_TIME_OBJECTS),
                                   ensure_ascii=False, sort_keys=True)
        csvPF.WriteRowNoFilter(fjrow)
  if not FJQC.formatJSON:
    sortTitles = ['group'] if groupColumn else []
    if showCategory:
      sortTitles.append('allowExternalMembers')
    if addCSVData:
      sortTitles.extend(sorted(addCSVData.keys()))
    sortTitles.extend(CIGROUPMEMBERS_SORT_FIELDS)
    if showCategory:
      emailIndex = sortTitles.index('email')
      sortTitles.insert(emailIndex+1, 'category')
    csvPF.SetSortTitles(sortTitles)
    csvPF.SortTitles()
    csvPF.SetSortTitles([])
    if memberOptions[MEMBEROPTION_RECURSIVE]:
      csvPF.MoveTitlesToEnd(['level', 'subgroup'])
  csvPF.writeCSVfile(f'Cloud Identity Group Members ({subTitle})')

# gam show cigroup-members
#	[(cimember|ciowner <UserItem>)|(cigroup <GroupItem>)|(select <GroupEntity>)]
#	[showownedby <UserItem>]
#	[emailmatchpattern [not] <REMatchPattern>] [namematchpattern [not] <REMatchPattern>]
#	[descriptionmatchpattern [not] <REMatchPattern>]
#	[roles <GroupRoleList>] [members] [managers] [owners]
#	[internal] [internaldomains all|primary|<DomainNameList>] [external]
#	[types <CIGroupMemberTypeList>]
#	[memberemaildisplaypattern|memberemailskippattern <REMatchPattern>]
#	[minimal|basic|full]
#	[(depth <Number>) | includederivedmembership]
def doShowCIGroupMembers():
  def _roleOrder(key):
    return {Ent.ROLE_OWNER: 0, Ent.ROLE_MANAGER: 1, Ent.ROLE_MEMBER: 2}.get(key, 3)

  def _typeOrder(key):
    return {Ent.TYPE_CUSTOMER: 0, Ent.TYPE_USER: 1, Ent.TYPE_GROUP: 2,
            Ent.TYPE_CBCM_BROWSER: 3, Ent.TYPE_OTHER: 4, Ent.TYPE_EXTERNAL: 5}.get(key, 6)

  def _showGroup(groupName, groupEmail, depth):
    if includeDerivedMembership:
      membersList = []
      if not getCIGroupTransitiveMembers(ci, groupName, membersList, i, count):
        return
    else:
      try:
        membersList = _getMain().callGAPIpages(ci.groups().memberships(), 'list', 'memberships',
                                    throwReasons=GAPI.CIGROUP_LIST_THROW_REASONS, retryReasons=GAPI.CIGROUP_RETRY_REASONS,
                                    parent=groupName, **kwargs)
        for member in membersList:
          _getMain().getCIGroupMemberRoleFixType(member)
      except (GAPI.resourceNotFound, GAPI.domainNotFound, GAPI.domainCannotUseApis,
              GAPI.forbidden, GAPI.badRequest, GAPI.invalid, GAPI.invalidArgument, GAPI.systemError,
              GAPI.permissionDenied, GAPI.serviceNotAvailable):
        if depth == 0:
          _getMain().entityUnknownWarning(Ent.CLOUD_IDENTITY_GROUP, groupEmail, i, count)
        return
    if showOwnedBy and not checkCIGroupShowOwnedBy(showOwnedBy, membersList):
      return
    if depth == 0:
      _getMain().printEntity([Ent.CLOUD_IDENTITY_GROUP, groupEmail], i, count)
    if depth == 0 or Ent.TYPE_GROUP in typesSet:
      Ind.Increment()
    for member in sorted(membersList, key=lambda k: (_roleOrder(k.get('role', Ent.ROLE_MEMBER)), _typeOrder(k['type']))):
      if (_getMain()._checkMemberIsSuspendedIsArchived(member, memberOptions[MEMBEROPTION_ISSUSPENDED], memberOptions[MEMBEROPTION_ISARCHIVED]) and
          (not checkShowCategory or _getMain()._checkCIMemberCategory(member, memberDisplayOptions))):
        if (_getMain()._checkMemberRole(member, rolesSet) and
            member['type'] in typesSet and
            _getMain()._checkCIMemberMatch(member, memberOptions)):
          if listView != 'minimal':
            memberDetails = f'{member.get("role", Ent.ROLE_MEMBER)}, {member["type"]}, {member["preferredMemberKey"]["id"]}'
          else:
            memberDetails = f'{member.get("role", Ent.ROLE_MEMBER)}, {member["preferredMemberKey"]["id"]}'
          if showCategory:
            memberDetails += f', {member["category"]}'
          for field in ['createTime', 'updateTime', 'expireTime']:
            if field in member:
              memberDetails += f', {formatLocalTime(member[field])}'
          _getMain().printKeyValueList([memberDetails])
        if not includeDerivedMembership and (member['type'] == Ent.TYPE_GROUP) and (maxdepth == -1 or depth < maxdepth):
          _, gname = member['name'].rsplit('/', 1)
          _showGroup(f'groups/{gname}', member['preferredMemberKey']['id'], depth+1)
    if depth == 0 or Ent.TYPE_GROUP in typesSet:
      Ind.Decrement()

  cd = _getMain().buildGAPIObject(API.DIRECTORY)
  ci = _getMain().buildGAPIObject(API.CLOUDIDENTITY_GROUPS)
  _getMain().setTrueCustomerId(cd)
  parent = f'customers/{GC.Values[GC.CUSTOMER_ID]}'
  subTitle = f'{Msg.ALL} {Ent.Plural(Ent.CLOUD_IDENTITY_GROUP)}'
  groupFieldsLists = {'ci': ['groupKey', 'name']}
  entityList = query = showOwnedBy = None
  rolesSet = set()
  typesSet = set()
  memberOptions = _getMain().initMemberOptions()
  memberDisplayOptions = _getMain().initIPSGMGroupMemberDisplayOptions()
  matchPatterns = {}
  maxdepth = -1
  includeDerivedMembership = False
  listView = 'full'
  while Cmd.ArgumentsRemaining():
    myarg = _getMain().getArgument()
    if myarg == 'showownedby':
      showOwnedBy = _getMain().convertUIDtoEmailAddress(_getMain().getEmailAddress(), emailTypes=['user'])
    elif myarg in {'cimember', 'enterprisemember', 'ciowner'}:
      emailAddress = _getMain().convertUIDtoEmailAddress(_getMain().getEmailAddress(), emailTypes=['user', 'group'])
      query = f"member_key_id == '{emailAddress}' && '{CIGROUP_DISCUSSION_FORUM_LABEL}' in labels parent == '{parent}'"
      entityList = None
      if myarg == 'ciowner':
        showOwnedBy = emailAddress
    elif myarg in {'cigroup', 'group'}:
      entityList = [_getMain().getString(Cmd.OB_EMAIL_ADDRESS)]
      subTitle = f'{Ent.Singular(Ent.CLOUD_IDENTITY_GROUP)}={entityList[0]}'
      query = None
    elif _getMain().getGroupMatchPatterns(myarg, matchPatterns, False):
      pass
    elif myarg == 'select':
      entityList = _getMain().getEntityList(Cmd.OB_GROUP_ENTITY)
      subTitle = f'{Msg.SELECTED} {Ent.Plural(Ent.CLOUD_IDENTITY_GROUP)}'
      query = None
    elif _getMain().getIPSGMGroupRolesMemberDisplayOptions(myarg, rolesSet, memberDisplayOptions):
      pass
    elif getCIGroupMemberTypes(myarg, typesSet):
      pass
    elif _getMain().getMemberMatchOptions(myarg, memberOptions):
      pass
    elif myarg == 'depth':
      maxdepth = _getMain().getInteger(minVal=-1)
    elif myarg == 'includederivedmembership':
      includeDerivedMembership = True
    elif myarg in {'minimal', 'basic', 'full'}:
      listView = myarg
    else:
      _getMain().unknownArgumentExit()
  if not rolesSet:
    rolesSet = _getMain().ALL_GROUP_ROLES
  if not typesSet:
    typesSet = ALL_CIGROUP_MEMBER_TYPES
  showCategory, checkShowCategory = _getMain().finalizeIPSGMGroupRolesMemberDisplayOptions(cd, memberDisplayOptions, False)
  fields = ','.join(set(groupFieldsLists['ci']))
  entityList = getCIGroupMembersEntityList(ci, entityList, query, subTitle, matchPatterns, groupFieldsLists['ci'], None)
  kwargs = _getCIListGroupMembersArgs(listView)
  i = 0
  count = len(entityList)
  for group in entityList:
    i += 1
    if isinstance(group, dict):
      groupEntity = group
    else:
      _, name, groupEmail = _getMain().convertGroupEmailToCloudID(ci, group, i, count)
      if not name or not groupEmail:
        continue
      try:
        groupEntity = _getMain()._getMain().callGAPI(ci.groups(), 'get',
                               throwReasons=GAPI.CIGROUP_GET_THROW_REASONS, retryReasons=GAPI.CIGROUP_RETRY_REASONS,
                               name=name, fields=fields)
      except (GAPI.notFound, GAPI.domainNotFound, GAPI.domainCannotUseApis,
              GAPI.forbidden, GAPI.badRequest, GAPI.invalid, GAPI.invalidArgument, GAPI.systemError,
              GAPI.permissionDenied, GAPI.serviceNotAvailable) as e:
        _getMain().entityActionFailedWarning([Ent.CLOUD_IDENTITY_GROUP, groupEmail], str(e), i, count)
        continue
    groupEmail = groupEntity['groupKey']['id'].lower()
    if _getMain().checkGroupMatchPatterns(groupEmail, groupEntity, matchPatterns):
      _showGroup(groupEntity['name'], groupEmail, 0)

# gam print licenses [todrive <ToDriveAttribute>*]
#	[(products|product <ProductIDList>)|(skus|sku <SKUIDList>)|allskus|gsuite]
#	[maxresults <Integer>]
#	[countsonly]
