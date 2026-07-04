"""Cloud Identity group member management.

Part of the _cigroups_tmp sub-package."""

"""GAM Cloud Identity group management."""

import re
import json

from gam.util.args import formatLocalTime

from gamlib import api as API
from gamlib import settings as GC
from gamlib import gapi as GAPI
from gamlib import state as GM
from gamlib import msgs as Msg

from gam.var import Act, Cmd, Ent, Ind

from gam.cmd.groups.groups import (
    MEMBEROPTION_INCLUDEDERIVEDMEMBERSHIP, MEMBEROPTION_ISARCHIVED,
    MEMBEROPTION_ISSUSPENDED, MEMBEROPTION_NODUPLICATES, MEMBEROPTION_RECURSIVE,
)

from gam.cmd.cigroups.groups import ALL_CIGROUP_MEMBER_TYPES, CIGROUP_MEMBER_TYPES_MAP
from gam.util.access import entityUnknownWarning
from gam.util.api import buildGAPIObject, getHttpObj
from gam.util.api_call import callGAPI, callGAPIpages
from gam.util.args import (
    checkArgumentPresent,
    checkForExtraneousArguments,
    getAddCSVData,
    getArgument,
    getBoolean,
    getCharacter,
    getEmailAddress,
    getInteger,
    getJSON,
    getREPattern,
    getString,
)
from gam.util.csv_pf import (
    CSVPrintFile,
    FormatJSONQuoteChar,
    _getFieldsList,
    addFieldToFieldsList,
    cleanJSON,
    flattenJSON,
    getFieldsFromFieldsList,
    getFieldsList,
    showJSON,
)
from gam.util.display import (
    entityActionFailedWarning,
    entityActionPerformed,
    entityActionPerformedMessage,
    getPageMessage,
    getPageMessageForWhom,
    performActionModifierNumItems,
    performActionNumItems,
    printBlankLine,
    printEntitiesCount,
    printEntity,
    printGettingAllAccountEntities,
    printGettingAllEntityItemsForWhom,
    printGettingEntityItemForWhom,
    printKeyValueList,
    printLine,
)
from gam.util.entity import (
    ALL_GROUP_ROLES,
    _checkCIMemberCategory,
    _checkMemberIsSuspendedIsArchived,
    _checkMemberRole,
    _getCIRoleVerification,
    _getCustomersCustomerIdWithC,
    convertEmailAddressToUID,
    convertGroupCloudIDToEmail,
    convertGroupEmailToCloudID,
    convertOrgUnitIDtoPath,
    convertUIDtoEmailAddress,
    getCIGroupMemberRoleFixType,
    getCIGroupTransitiveMemberRoleFixType,
    getEntityList,
    getEntityToModify,
    setTrueCustomerId,
    shlexSplitList,
)
from gam.util.errors import (
    USAGE_ERROR_RC,
    entityActionFailedExit,
    invalidChoiceExit,
    missingArgumentExit,
    unknownArgumentExit,
    usageErrorExit,
)
from gam.util.fileio import UNKNOWN
from gam.util.orgunits import _getOrgunitsOrgUnitIdPath
from gam.util.output import systemErrorExit, writeStdout
CIGROUP_DISCUSSION_FORUM_LABEL = 'cloudidentity.googleapis.com/groups.discussion_forum'

UNKNOWN = 'Unknown'

def getCIGroupMemberTypes(myarg, typesSet):
  if myarg in {'type', 'types'}:
    for gtype in getString(Cmd.OB_GROUP_TYPE_LIST).lower().replace('_', '').replace(',', ' ').split():
      if gtype in CIGROUP_MEMBER_TYPES_MAP:
        typesSet.add(CIGROUP_MEMBER_TYPES_MAP[gtype])
      else:
        invalidChoiceExit(gtype, CIGROUP_MEMBER_TYPES_MAP, True)
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
  from gam.cmd.groups.members import CIGROUP_FIELDS_CHOICE_MAP, CIGROUP_TIME_OBJECTS, _checkCIMemberMatch, _showCIGroup, finalizeIPSGMGroupRolesMemberDisplayOptions, getIPSGMGroupRolesMemberDisplayOptions, getMemberMatchOptions, initIPSGMGroupMemberDisplayOptions, initMemberOptions
  def printCIGroupMemberTree(group_id, showRole):
    if not group_id in cachedGroupMembers:
      try:
        cachedGroupMembers[group_id] = callGAPIpages(ci.groups().memberships(), 'list', 'memberships',
                                                     throwReasons=GAPI.MEMBERS_THROW_REASONS,
                                                     retryReasons=GAPI.MEMBERS_RETRY_REASONS,
                                                     parent=group_id, view='FULL',
                                                     fields='nextPageToken,memberships(*)',
                                                     pageSize=GC.Values[GC.MEMBER_MAX_RESULTS])
      except (GAPI.groupNotFound, GAPI.domainNotFound, GAPI.domainCannotUseApis, GAPI.invalid, GAPI.forbidden):
        entityUnknownWarning(Ent.CLOUD_IDENTITY_GROUP, group_id, i, count)
        return
      except (GAPI.conditionNotMet, GAPI.serviceNotAvailable) as e:
        entityActionFailedWarning([Ent.CLOUD_IDENTITY_GROUP, group_id], str(e), i, count)
        return
    for member in cachedGroupMembers[group_id]:
      member_id = member.get('name', '')
      member_id = member_id.split('/')[-1]
      member_email = member.get('preferredMemberKey', {}).get('id')
      member_type = member.get('type', 'USER').lower()
      if showRole:
        getCIGroupMemberRoleFixType(member)
        printKeyValueList([member['role'].lower(), f'{member_email} ({member_type})'])
      else:
        writeStdout(f'{Ind.Spaces()}{member_email} ({member_type})\n')
      if member_type == 'group':
        Ind.Increment()
        printCIGroupMemberTree(f'groups/{member_id}', False)
        Ind.Decrement()

  def initGroupFieldsLists():
    if not groupFieldsLists['ci']:
      groupFieldsLists['ci'] = ['groupKey']

  cd = buildGAPIObject(API.DIRECTORY)
  ci = buildGAPIObject(API.CLOUDIDENTITY_GROUPS)
  entityList = getEntityList(Cmd.OB_GROUP_ENTITY)
  getAliases = getSecuritySettings = getUsers = True
  showJoinDate = True
  showMemberTree = showUpdateDate = False
  FJQC = FormatJSONQuoteChar()
  members = []
  groupFieldsLists = {'ci': None}
  entityType = Ent.MEMBER
  rolesSet = set()
  typesSet = set()
  memberOptions = initMemberOptions()
  memberDisplayOptions = initIPSGMGroupMemberDisplayOptions()
  cachedGroupMembers = {}
  while Cmd.ArgumentsRemaining():
    myarg = getArgument()
    if myarg == 'quick':
      getAliases = getUsers = False
    elif myarg == 'nousers':
      getUsers = False
    elif myarg == 'membertree':
      showMemberTree = True
    elif getIPSGMGroupRolesMemberDisplayOptions(myarg, rolesSet, memberDisplayOptions):
      getUsers = True
    elif getCIGroupMemberTypes(myarg, typesSet):
      pass
    elif getMemberMatchOptions(myarg, memberOptions):
      pass
    elif myarg == 'noaliases':
      getAliases = False
    elif myarg in {'allfields', 'ciallfields', 'allcifields'}:
      if not groupFieldsLists['ci']:
        groupFieldsLists['ci'] = []
      for field in CIGROUP_FIELDS_CHOICE_MAP:
        addFieldToFieldsList(field, CIGROUP_FIELDS_CHOICE_MAP, groupFieldsLists['ci'])
    elif myarg in CIGROUP_FIELDS_CHOICE_MAP:
      initGroupFieldsLists()
      addFieldToFieldsList(myarg, CIGROUP_FIELDS_CHOICE_MAP, groupFieldsLists['ci'])
    elif myarg in {'fields', 'cifields'}:
      initGroupFieldsLists()
      for field in _getFieldsList():
        if field in CIGROUP_FIELDS_CHOICE_MAP:
          addFieldToFieldsList(field, CIGROUP_FIELDS_CHOICE_MAP, groupFieldsLists['ci'])
        else:
          invalidChoiceExit(field, CIGROUP_FIELDS_CHOICE_MAP, True)
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
  fields = getFieldsFromFieldsList(groupFieldsLists['ci'])
  if not showJoinDate and not showUpdateDate:
    view = 'BASIC'
    pageSize = 1000
  else:
    view = 'FULL'
    pageSize = 500
  showCategory, checkShowCategory = finalizeIPSGMGroupRolesMemberDisplayOptions(cd, memberDisplayOptions, False)
  i = 0
  count = len(entityList)
  for group in entityList:
    i += 1
    _, name, group = convertGroupEmailToCloudID(ci, group, i, count)
    if not name or not group:
      continue
    try:
      cigInfo = callGAPI(ci.groups(), 'get',
                         throwReasons=GAPI.CIGROUP_GET_THROW_REASONS, retryReasons=GAPI.CIGROUP_RETRY_REASONS,
                         name=name, fields=fields)
      group = cigInfo['groupKey']['id']
      if not getAliases:
        cigInfo.pop('additionalGroupKeys', None)
      if getUsers and not showMemberTree:
        result = callGAPIpages(ci.groups().memberships(), 'list', 'memberships',
                               throwReasons=GAPI.MEMBERS_THROW_REASONS, retryReasons=GAPI.MEMBERS_RETRY_REASONS,
                               parent=name, view=view, fields='*', pageSize=pageSize)
        members = []
        for member in result:
          getCIGroupMemberRoleFixType(member)
          if ((member['type'] in typesSet) and
              _checkMemberRole(member, rolesSet) and
              _checkCIMemberMatch(member, memberOptions) and
              (not checkShowCategory or _checkCIMemberCategory(member, memberDisplayOptions))):
            members.append(member)
      if getSecuritySettings:
        cigInfo['SecuritySettings'] = callGAPI(ci.groups(), 'getSecuritySettings',
                                               throwReasons=GAPI.CIGROUP_GET_THROW_REASONS, retryReasons=GAPI.CIGROUP_RETRY_REASONS,
                                               name=f'{name}/securitySettings', readMask='*')
      if FJQC.formatJSON:
        if getUsers and not showMemberTree:
          cigInfo['members'] = members
        printLine(json.dumps(cleanJSON(cigInfo, timeObjects=CIGROUP_TIME_OBJECTS), ensure_ascii=False, sort_keys=True))
        continue
      _showCIGroup(cigInfo, group, i, count)
      if getUsers and not showMemberTree:
        Ind.Increment()
        printEntitiesCount(entityType, members)
        Ind.Increment()
        for member in members:
          memberEmail = member.get('preferredMemberKey', {}).get('id', member['name'])
          getCIGroupMemberRoleFixType(member)
          memberDetails = [member['role'].lower(), f'{memberEmail} ({member["type"].lower()})']
          if showCategory:
            memberDetails[1] += f' ({member["category"]})'
          if showJoinDate:
            memberDetails.extend(['joined', formatLocalTime(member['createTime']) if 'createTime' in member else UNKNOWN])
          if showUpdateDate:
            memberDetails.extend(['updated', formatLocalTime(member['updateTime']) if 'updateTime' in member else UNKNOWN])
          if 'expireTime' in member:
            memberDetails.extend(['expires', formatLocalTime(member['expireTime'])])
          printKeyValueList(memberDetails)
        Ind.Decrement()
        printKeyValueList([Msg.TOTAL_ITEMS_IN_ENTITY.format(Ent.Plural(entityType), Ent.Singular(Ent.CLOUD_IDENTITY_GROUP)), len(members)])
        Ind.Decrement()
      elif showMemberTree:
        Ind.Increment()
        printEntity([Ent.MEMBERSHIP_TREE, ''])
        Ind.Increment()
        printCIGroupMemberTree(name, True)
        Ind.Decrement()
        Ind.Decrement()
    except GAPI.notFound:
      entityActionFailedWarning([Ent.CLOUD_IDENTITY_GROUP, group], Msg.DOES_NOT_EXIST, i, count)
    except (GAPI.groupNotFound, GAPI.resourceNotFound, GAPI.domainNotFound, GAPI.domainCannotUseApis, GAPI.backendError,
            GAPI.invalid, GAPI.invalidArgument, GAPI.invalidMember, GAPI.invalidParameter, GAPI.invalidInput, GAPI.forbidden,
            GAPI.badRequest, GAPI.permissionDenied, GAPI.systemError, GAPI.serviceLimit, GAPI.serviceNotAvailable) as e:
      entityActionFailedWarning([Ent.CLOUD_IDENTITY_GROUP, group], str(e), i, count)

def checkCIGroupShowOwnedBy(showOwnedBy, members):
  for member in members:
    if member['preferredMemberKey']['id'] == showOwnedBy:
      if member['role'] == Ent.ROLE_OWNER:
        return True
  return False

def updateFieldsForCIGroupMatchPatterns(matchPatterns, fieldsList, csvPF=None):
  from gam.cmd.groups.members import CIGROUP_FIELDS_CHOICE_MAP
  for field in ['displayName', 'description']:
    if field in matchPatterns:
      if csvPF is not None:
        csvPF.AddField(field, CIGROUP_FIELDS_CHOICE_MAP, fieldsList)
      else:
        fieldsList.append(field)

CIPOLICY_TIME_OBJECTS = {'createTime', 'updateTime'}

def _filterPolicies(ci, pageMessage, ifilter):
  try:
    policies = callGAPIpages(ci.policies(), 'list', 'policies',
                             pageMessage=pageMessage,
                             throwReasons=[GAPI.INVALID, GAPI.INVALID_ARGUMENT, GAPI.PERMISSION_DENIED],
                             filter=ifilter, pageSize=100)
    # Google returns unordered results, sort them by setting type
    return sorted(policies, key=lambda p: p.get('setting', {}).get('type', ''))
  except (GAPI.invalid, GAPI.invalidArgument, GAPI.permissionDenied) as e:
    entityActionFailedWarning([Ent.POLICY, ifilter], str(e))
    return []

# Policies where GAM should offer additional guidance and information
CIPOLICY_ADDITIONAL_WARNINGS = {
  'settings/drive_and_docs.external_sharing': {
    'warningType': 'SUPERSEDED_POLICY',
    'warningMessage': 'CAUTION: Drive Sharing settings are superseded by Drive Trust Rules if Trust Rules has been enabled for your domain. Drive Trust Rule settings are not available in the Policy API today so GAM is not able to check if Trust Rules is enabled and if the settings/drive_and_docs.external_sharing policies are actually in effect for your domain. If Drive Trust Rules is enabled for your domain then this settings/drive_and_docs.external_sharing policy does not accurately reflect your current Drive sharing settings.'
  }
}

def _getPolicyAppNameFromId(httpObj, app):
  app['applicationName'] = UNKNOWN
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
    httpObj = getHttpObj(timeout=10)
    for app in policy['setting']['value'].get('apps', []):
      _getPolicyAppNameFromId(httpObj, app)
  # add any warnings to applicable policies
  if add_warnings and policy['setting']['type'] in CIPOLICY_ADDITIONAL_WARNINGS:
    policy['warning'] = CIPOLICY_ADDITIONAL_WARNINGS[policy['setting']['type']]
  if groupId := policy['policyQuery'].get('group'):
    if (not no_idmapping) or (groupEmailPattern is not None):
      _, _, groupEmail = convertGroupCloudIDToEmail(groups_ci, groupId)
      if not no_idmapping:
        policy['policyQuery']['groupEmail'] = groupEmail
      if groupEmailPattern is not None:
        return groupEmailPattern.match(groupEmail)
  elif orgId := policy['policyQuery'].get('orgUnit'):
    if (not no_idmapping) or (orgUnitPathPattern is not None):
      orgUnitPath = convertOrgUnitIDtoPath(cd, orgId)
      if not no_idmapping:
        policy['policyQuery']['orgUnitPath'] = orgUnitPath
      if orgUnitPathPattern is not None:
        return orgUnitPathPattern.match(orgUnitPath)
  return True

def _showPolicy(policy, FJQC, i=0, count=0):
  if FJQC is not None and FJQC.formatJSON:
    printLine(json.dumps(cleanJSON(policy, timeObjects=CIPOLICY_TIME_OBJECTS),
                         ensure_ascii=False, sort_keys=True))
    return
  printEntity([Ent.POLICY, policy['name']], i, count)
  Ind.Increment()
  policy.pop('name')
  showJSON(None, policy, timeObjects=CIPOLICY_TIME_OBJECTS)
  printBlankLine()
  Ind.Decrement()

def _showPolicies(policies, FJQC, add_warnings, no_appnames, no_idmapping,
                  groupEmailPattern, orgUnitPathPattern, cd, groups_ci):
  count = len(policies)
  if FJQC is None or not FJQC.formatJSON:
    if groupEmailPattern is None and orgUnitPathPattern is None:
      performActionNumItems(count, Ent.POLICY)
    else:
      performActionModifierNumItems(Msg.MAXIMUM_OF, count, Ent.POLICY)
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
    systemErrorExit(USAGE_ERROR_RC,
                    Msg.COMMAND_NOT_COMPATIBLE_WITH_ENABLE_DASA.format(Act.ToPerform().lower(), Cmd.ARG_CIPOLICIES))

# gam create policy
#	json <JSONData>
#	[(ou|orgunit <OrgUnitItem>)|(group <GroupItem>)|(query <String>)]
# gam update policy
#	json <JSONData>
#	[(ou|orgunit <OrgUnitItem>)|(group <GroupItem>)|(query <String>)]
def doCreateUpdateCIPolicy():
  _checkPoliciesWithDASA()
  ci = buildGAPIObject(API.CLOUDIDENTITY_POLICY)
  cd = buildGAPIObject(API.DIRECTORY)
  updateCmd = Act.Get() == Act.UPDATE
  groupEmail = orgUnit = query = None
  checkArgumentPresent('json', True)
  policy = getJSON(['customer', 'type'])
  if updateCmd:
    pname = policy.pop('name', None)
    if not pname:
      Cmd.Backup()
      usageErrorExit(Msg.POLICY_NAME_NOT_FOUND)
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
          policy['setting']['value']['wordList']['words'] = shlexSplitList(wordList, dataDelimiter=',')
  while Cmd.ArgumentsRemaining():
    myarg = getArgument()
    if myarg in {'ou', 'org', 'orgunit'}:
      if groupEmail:
        Cmd.Backup()
        usageErrorExit(Msg.ARE_MUTUALLY_EXCLUSIVE.format(myarg, 'group'))
      if query:
        Cmd.Backup()
        usageErrorExit(Msg.ARE_MUTUALLY_EXCLUSIVE.format(myarg, 'query'))
      orgUnit, targetResource = _getOrgunitsOrgUnitIdPath(cd, getString(Cmd.OB_ORGUNIT_PATH))
      policy['policyQuery'] = {'orgUnit': f"orgUnits/{targetResource}"}
    elif myarg == 'group':
      if orgUnit:
        Cmd.Backup()
        usageErrorExit(Msg.ARE_MUTUALLY_EXCLUSIVE.format(myarg, 'ou|org|orgunit'))
      if query:
        Cmd.Backup()
        usageErrorExit(Msg.ARE_MUTUALLY_EXCLUSIVE.format(myarg, 'query'))
      groupEmail = getEmailAddress(returnUIDprefix='uid:')
      targetResource = f"groups/{convertEmailAddressToUID(groupEmail, cd, emailType='group')}"
      policy['policyQuery'] = {'group': f"groups/{targetResource}"}
    elif myarg == 'query':
      if groupEmail:
        Cmd.Backup()
        usageErrorExit(Msg.ARE_MUTUALLY_EXCLUSIVE.format(myarg, 'group'))
      if orgUnit:
        Cmd.Backup()
        usageErrorExit(Msg.ARE_MUTUALLY_EXCLUSIVE.format(myarg, 'ou|org|orgunit'))
      query = getString(Cmd.OB_QUERY)
      policy['policyQuery'] = {'query': query}
    else:
      unknownArgumentExit()
  if 'policyQuery' not in policy:
    missingArgumentExit('ou|org|orgunit|group|query')
  policy['customer'] = _getCustomersCustomerIdWithC()
  try:
    if updateCmd:
      result = callGAPI(ci.policies(), 'patch',
                        bailOnInternalError=True,
                        throwReasons=[GAPI.INVALID, GAPI.INVALID_ARGUMENT, GAPI.UNIMPLEMENTED_ERROR,
                                      GAPI.NOT_FOUND, GAPI.PERMISSION_DENIED, GAPI.INTERNAL_ERROR],
                        name=pname, body=policy)
    else:
      result = callGAPI(ci.policies(), 'create',
                        bailOnInternalError=True,
                        throwReasons=[GAPI.INVALID, GAPI.INVALID_ARGUMENT, GAPI.UNIMPLEMENTED_ERROR,
                                      GAPI.NOT_FOUND, GAPI.PERMISSION_DENIED, GAPI.INTERNAL_ERROR],
                        body=policy)
    if result['done']:
      if 'error' not in result:
        if not updateCmd:
          pname = result['response'].get('id', pname)
        entityActionPerformed([Ent.POLICY, pname])
      else:
        entityActionFailedWarning([Ent.POLICY, pname], result['error']['message'])
    else:
      entityActionPerformedMessage([Ent.POLICY, pname], Msg.ACTION_IN_PROGRESS.format('delete'))
  except (GAPI.invalid, GAPI.invalidArgument, GAPI.unimplementedError,
          GAPI.notFound, GAPI.permissionDenied, GAPI.internalError) as e:
    entityActionFailedWarning([Ent.POLICY, pname], str(e))

# gam delete policies <CIPolicyNameEntity>
def doDeleteCIPolicies():
  _checkPoliciesWithDASA()
  ci = buildGAPIObject(API.CLOUDIDENTITY_POLICY)
  entityList = getEntityList(Cmd.OB_CIPOLICY_NAME_ENTITY)
  checkForExtraneousArguments()
  i = 0
  count = len(entityList)
  for pname in entityList:
    i += 1
    if pname.startswith('policies/'):
      try:
        policies  = [callGAPI(ci.policies(), 'get',
                              bailOnInternalError=True,
                              throwReasons=[GAPI.INVALID, GAPI.INVALID_ARGUMENT,
                                            GAPI.NOT_FOUND, GAPI.PERMISSION_DENIED, GAPI.INTERNAL_ERROR],
                              name=pname, fields='name')]
      except (GAPI.invalid, GAPI.invalidArgument, GAPI.notFound, GAPI.permissionDenied, GAPI.internalError) as e:
        entityActionFailedWarning([Ent.POLICY, pname], str(e), i, count)
        continue
    else:
      if pname.startswith('settings/'):
        pname = pname.split('/')[1]
      ifilter = f"setting.type.matches('{pname}')"
      printGettingAllAccountEntities(Ent.POLICY, ifilter)
      policies = _filterPolicies(ci, getPageMessage(), ifilter)
    jcount = len(policies)
    performActionNumItems(jcount, Ent.POLICY)
    Ind.Increment()
    j = 0
    for policy in policies:
      j += 1
      pname = policy['name']
      try:
        result = callGAPI(ci.policies(), 'delete',
                          bailOnInternalError=True,
                          throwReasons=[GAPI.INVALID, GAPI.INVALID_ARGUMENT,
                                        GAPI.NOT_FOUND, GAPI.PERMISSION_DENIED, GAPI.INTERNAL_ERROR],
                          name=pname)
        if result['done']:
          if 'error' not in result:
            entityActionPerformed([Ent.POLICY, pname], j, jcount)
          else:
            entityActionFailedWarning([Ent.POLICY, pname], result['error']['message'], j, jcount)
        else:
          entityActionPerformedMessage([Ent.POLICY, pname], Msg.ACTION_IN_PROGRESS.format('delete'), j, jcount)
      except (GAPI.invalid, GAPI.invalidArgument, GAPI.notFound, GAPI.permissionDenied, GAPI.internalError) as e:
        entityActionFailedWarning([Ent.POLICY, pname], str(e), j, jcount)
    Ind.Decrement()

# gam info policies <CIPolicyNameEntity>
#	[nowarnings] [noappnames] [noidmappiong]
#	[formatjson]
def doInfoCIPolicies():
  _checkPoliciesWithDASA()
  groups_ci = buildGAPIObject(API.CLOUDIDENTITY_GROUPS)
  ci = buildGAPIObject(API.CLOUDIDENTITY_POLICY)
  cd = buildGAPIObject(API.DIRECTORY)
  entityList = getEntityList(Cmd.OB_CIPOLICY_NAME_ENTITY)
  FJQC = FormatJSONQuoteChar()
  add_warnings = True
  no_appnames = no_idmapping = False
  while Cmd.ArgumentsRemaining():
    myarg = getArgument()
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
        policies  = [callGAPI(ci.policies(), 'get',
                              bailOnInternalError=True,
                              throwReasons=[GAPI.INVALID, GAPI.INVALID_ARGUMENT,
                                            GAPI.NOT_FOUND, GAPI.PERMISSION_DENIED, GAPI.INTERNAL_ERROR],
                              name=pname)]
      except (GAPI.invalid, GAPI.invalidArgument, GAPI.notFound, GAPI.permissionDenied, GAPI.internalError) as e:
        entityActionFailedWarning([Ent.POLICY, pname], str(e), i, count)
        continue
    else:
      if pname.startswith('settings/'):
        pname = pname.split('/')[1]
      ifilter = f"setting.type.matches('{pname}')"
      printGettingAllAccountEntities(Ent.POLICY, ifilter)
      policies = _filterPolicies(ci, getPageMessage(), ifilter)
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
    row = flattenJSON(policy, timeObjects=CIPOLICY_TIME_OBJECTS)
    if not FJQC.formatJSON:
      csvPF.WriteRowTitles(row)
    elif csvPF.CheckRowTitles(row):
      csvPF.WriteRowNoFilter({'name': policy['name'],
                              'JSON': json.dumps(cleanJSON(policy, timeObjects=CIPOLICY_TIME_OBJECTS),
                                                 ensure_ascii=False, sort_keys=True)})

  _checkPoliciesWithDASA()
  ci = buildGAPIObject(API.CLOUDIDENTITY_POLICY)
  groups_ci = buildGAPIObject(API.CLOUDIDENTITY_GROUPS)
  cd = buildGAPIObject(API.DIRECTORY)
  csvPF = CSVPrintFile(['name']) if Act.csvFormat() else None
  FJQC = FormatJSONQuoteChar(csvPF)
  ifilter = None
  add_warnings = True
  no_appnames = no_idmapping = False
  groupEmailPattern = orgUnitPathPattern = None
  while Cmd.ArgumentsRemaining():
    myarg = getArgument()
    if csvPF and myarg == 'todrive':
      csvPF.GetTodriveParameters()
    elif myarg == 'filter':
      ifilter = getString(Cmd.OB_STRING)
    elif myarg == 'nowarnings':
      add_warnings = False
    elif myarg == 'noappnames':
      no_appnames = True
    elif myarg == 'noidmapping':
      no_idmapping = True
    elif myarg == 'group':
      groupEmailPattern = getREPattern(re.IGNORECASE)
    elif myarg in {'ou', 'org', 'orgunit'}:
      orgUnitPathPattern = getREPattern(re.IGNORECASE)
    else:
      FJQC.GetFormatJSONQuoteChar(myarg, True)
  printGettingAllAccountEntities(Ent.POLICY, ifilter)
  policies = _filterPolicies(ci, getPageMessage(), ifilter)
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
  from gam.cmd.groups.members import CIGROUP_FIELDS_CHOICE_MAP, CIGROUP_FULL_FIELDS, CIGROUP_PRINT_ORDER, CIGROUP_TIME_OBJECTS, addMemberInfoToRow, checkGroupMatchPatterns, finalizeIPSGMGroupRolesMemberDisplayOptions, getGroupAllowExternalMembers, getGroupMatchPatterns, getMemberMatchOptions, getPGGroupRolesMemberDisplayOptions, initIPSGMGroupMemberDisplayOptions, initMemberOptions, mapCIGroupFieldNames, setMemberDisplaySortTitles, setMemberDisplayTitles
  def _printGroupRow(groupEntity, groupMembers):
    nonlocal itemCount
    for member in groupMembers:
      getCIGroupMemberRoleFixType(member)
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
      row['JSON'] = json.dumps(cleanJSON(groupEntity, timeObjects=CIGROUP_TIME_OBJECTS), ensure_ascii=False, sort_keys=True)
      if rolesSet and groupMembers is not None:
        row['JSON-members'] = json.dumps(groupMembers, ensure_ascii=False, sort_keys=True)
      csvPF.WriteRowNoFilter(row)
      return
    mapCIGroupFieldNames(groupEntity)
    for k, v in groupEntity.pop('labels', {}).items():
      if v == '':
        groupEntity[f'labels{GC.Values[GC.CSV_OUTPUT_SUBFIELD_DELIMITER]}{k}'] = True
      else:
        groupEntity[f'labels{GC.Values[GC.CSV_OUTPUT_SUBFIELD_DELIMITER]}{k}'] = v
    for key, value in sorted(flattenJSON(groupEntity, flattened={}, timeObjects=CIGROUP_TIME_OBJECTS).items()):
      csvPF.AddTitles(key)
      row[key] = value
    if rolesSet and groupMembers is not None:
      addMemberInfoToRow(row, groupMembers, typesSet, memberOptions, memberDisplayOptions, delimiter,
                         False, False, True)
    csvPF.WriteRow(row)

  cd = buildGAPIObject(API.DIRECTORY)
  ci = buildGAPIObject(API.CLOUDIDENTITY_GROUPS)
  setTrueCustomerId(cd)
  parent = f'customers/{GC.Values[GC.CUSTOMER_ID]}'
  delimiter = GC.Values[GC.CSV_OUTPUT_FIELD_DELIMITER]
  memberRestrictions = sortHeaders = False
  memberDisplayOptions = initIPSGMGroupMemberDisplayOptions()
  pageSize = 500
  groupFieldsLists = {'ci': ['groupKey']}
  csvPF = CSVPrintFile(['email'])
  FJQC = FormatJSONQuoteChar(csvPF)
  rolesSet = set()
  typesSet = set()
  memberOptions = initMemberOptions()
  allowExternalMembers = entitySelection = groupMembers = memberQuery = query = showOwnedBy = None
  matchPatterns = {}
  showItemCountOnly = False
  addCSVData = {}
  includeCSVDataInJSON = False
  while Cmd.ArgumentsRemaining():
    myarg = getArgument()
    if myarg == 'todrive':
      csvPF.GetTodriveParameters()
    elif myarg == 'showownedby':
      showOwnedBy = convertUIDtoEmailAddress(getEmailAddress(), emailTypes=['user'])
    elif myarg in {'cimember', 'enterprisemember', 'ciowner'}:
      emailAddress = convertUIDtoEmailAddress(getEmailAddress(), emailTypes=['user', 'group'])
      memberQuery = f"member_key_id == '{emailAddress}' && '{CIGROUP_DISCUSSION_FORUM_LABEL}' in labels && parent == '{parent}'"
      entitySelection = None
      if myarg == 'ciowner':
        showOwnedBy = emailAddress
    elif myarg == 'query':
      query = getString(Cmd.OB_QUERY)
      entitySelection = None
    elif getGroupMatchPatterns(myarg, matchPatterns, True):
      pass
    elif myarg == 'select':
      entitySelection = getEntityList(Cmd.OB_GROUP_ENTITY)
      query = None
    elif myarg == 'maxresults':
      pageSize = getInteger(minVal=1, maxVal=500)
    elif myarg == 'delimiter':
      delimiter = getCharacter()
    elif myarg in {'allfields', 'ciallfields', 'allcifields'}:
      sortHeaders = True
      groupFieldsLists = {'ci': []}
      for field in CIGROUP_FIELDS_CHOICE_MAP:
        addFieldToFieldsList(field, CIGROUP_FIELDS_CHOICE_MAP, groupFieldsLists['ci'])
    elif myarg == 'basic':
      sortHeaders = True
      groupFieldsLists = {'ci': ['*']}
    elif myarg == 'sortheaders':
      sortHeaders = getBoolean()
    elif myarg in CIGROUP_FIELDS_CHOICE_MAP:
      csvPF.AddField(myarg, CIGROUP_FIELDS_CHOICE_MAP, groupFieldsLists['ci'])
    elif myarg in {'fields', 'cifields'}:
      for field in _getFieldsList():
        if field in CIGROUP_FIELDS_CHOICE_MAP:
          csvPF.AddField(field, CIGROUP_FIELDS_CHOICE_MAP, groupFieldsLists['ci'])
        else:
          invalidChoiceExit(field, list(CIGROUP_FIELDS_CHOICE_MAP), True)
    elif getPGGroupRolesMemberDisplayOptions(myarg, rolesSet, memberDisplayOptions):
      pass
    elif getCIGroupMemberTypes(myarg, typesSet):
      pass
    elif getMemberMatchOptions(myarg, memberOptions):
      pass
    elif myarg == 'memberrestrictions':
      memberRestrictions = True
    elif myarg == 'showitemcountonly':
      showItemCountOnly = True
    elif myarg == 'addcsvdata':
      getAddCSVData(addCSVData)
    elif myarg == 'includecsvdatainjson':
      includeCSVDataInJSON = getBoolean()
    else:
      FJQC.GetFormatJSONQuoteChar(myarg, False)
  if not typesSet:
    typesSet = ALL_CIGROUP_MEMBER_TYPES
  showCategory, _ = finalizeIPSGMGroupRolesMemberDisplayOptions(cd, memberDisplayOptions, False)
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
    setMemberDisplayTitles(memberDisplayOptions, csvPF)
  if memberQuery:
    printGettingAllAccountEntities(Ent.CLOUD_IDENTITY_GROUP, memberQuery)
    try:
      result = callGAPIpages(ci.groups().memberships(), 'searchTransitiveGroups', 'memberships',
                             pageMessage=getPageMessage(showFirstLastItems=True), messageAttribute=['groupKey', 'id'],
                             throwReasons=GAPI.CIGROUP_LIST_USERKEY_THROW_REASONS, retryReasons=GAPI.CIGROUP_RETRY_REASONS,
                             parent='groups/-', query=memberQuery,
                             fields='nextPageToken,memberships(group,groupKey(id),relationType)', pageSize=pageSize)
      entitySelection = [{'email': entity['groupKey']['id'], 'name': entity['group']} for entity in result if entity['relationType'] == 'DIRECT']
    except (GAPI.resourceNotFound, GAPI.domainNotFound, GAPI.domainCannotUseApis,
            GAPI.forbidden, GAPI.badRequest, GAPI.invalid,
            GAPI.systemError, GAPI.permissionDenied, GAPI.invalidArgument, GAPI.serviceNotAvailable) as e:
      entityActionFailedWarning([Ent.CLOUD_IDENTITY_GROUP, None], str(e))
      return
  getFullFieldsList = []
  if entitySelection is None:
    if groupFieldsLists['ci']:
      for field in groupFieldsLists['ci']:
        if field in CIGROUP_FULL_FIELDS:
          getFullFieldsList.append(field)
    else:
      getFullFieldsList = list(CIGROUP_FULL_FIELDS)
    getFullFields = ','.join(getFullFieldsList)#
    if query:
      method = 'search'
      if 'parent' not in query:
        query += f" && parent == '{parent}'"
      kwargs = {'query': query}
    else:
      method = 'list'
      kwargs = {'parent': parent}
    printGettingAllAccountEntities(Ent.CLOUD_IDENTITY_GROUP, query)
    try:
      entityList = callGAPIpages(ci.groups(), method, 'groups',
                                 pageMessage=getPageMessage(showFirstLastItems=True), messageAttribute=['groupKey', 'id'],
                                 throwReasons=GAPI.CIGROUP_LIST_THROW_REASONS, retryReasons=GAPI.CIGROUP_RETRY_REASONS,
                                 view='FULL', fields=fieldsnp, pageSize=pageSize, **kwargs)
    except (GAPI.resourceNotFound, GAPI.domainNotFound, GAPI.domainCannotUseApis,
            GAPI.forbidden, GAPI.badRequest, GAPI.invalid, GAPI.invalidArgument,
            GAPI.systemError, GAPI.permissionDenied, GAPI.serviceNotAvailable) as e:
      entityActionFailedWarning([Ent.CLOUD_IDENTITY_GROUP, None], str(e))
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
        _, name, groupEmail = convertGroupEmailToCloudID(ci, group, i, count)
      printGettingEntityItemForWhom(Ent.CLOUD_IDENTITY_GROUP, groupEmail, i, count)
      kvList = [Ent.CLOUD_IDENTITY_GROUP, groupEmail]
      if name:
        try:
          ciGroup = callGAPI(ci.groups(), 'get',
                             throwReasons=GAPI.CIGROUP_GET_THROW_REASONS, retryReasons=GAPI.CIGROUP_RETRY_REASONS,
                             name=name, fields=fields)
          entityList.append(ciGroup)
        except (GAPI.notFound, GAPI.domainNotFound, GAPI.domainCannotUseApis,
                GAPI.forbidden, GAPI.badRequest, GAPI.invalid, GAPI.invalidArgument,
                GAPI.systemError, GAPI.permissionDenied, GAPI.serviceNotAvailable) as e:
          entityActionFailedWarning(kvList, str(e), i, count)
  itemCount = 0
  i = 0
  count = len(entityList)
  for groupEntity in entityList:
    i += 1
    groupEmail = groupEntity['groupKey']['id'].lower()
    if not checkGroupMatchPatterns(groupEmail, groupEntity, matchPatterns):
      continue
    kvList = [Ent.CLOUD_IDENTITY_GROUP, groupEmail]
    if getFullFields:
      try:
        fullInfo = callGAPI(ci.groups(), 'get',
                            throwReasons=GAPI.CIGROUP_GET_THROW_REASONS, retryReasons=GAPI.CIGROUP_RETRY_REASONS,
                            name=groupEntity['name'], fields=getFullFields)
        groupEntity.update(fullInfo)
      except (GAPI.notFound, GAPI.domainNotFound, GAPI.domainCannotUseApis,
              GAPI.forbidden, GAPI.badRequest, GAPI.invalid, GAPI.invalidArgument,
              GAPI.systemError, GAPI.permissionDenied, GAPI.serviceNotAvailable) as e:
        entityActionFailedWarning(kvList, str(e), i, count)
    if showCategory:
      allowExternalMembers = getGroupAllowExternalMembers(memberDisplayOptions['gs'], groupEmail, False,
                                                          kvList, i, count)
      if allowExternalMembers is None:
        continue
    groupMembers = {}
    if getRoles:
      printGettingEntityItemForWhom(getRoles, groupEmail, i, count)
      try:
        groupMembers = callGAPIpages(ci.groups().memberships(), 'list', 'memberships',
                                     throwReasons=GAPI.MEMBERS_THROW_REASONS, retryReasons=GAPI.MEMBERS_RETRY_REASONS,
                                     pageMessage=getPageMessage(), messageAttribute=['preferredMemberKey', 'id'],
                                     parent=groupEntity['name'], view='FULL', fields='*', pageSize=pageSize)
      except (GAPI.groupNotFound, GAPI.domainNotFound, GAPI.domainCannotUseApis, GAPI.invalid, GAPI.forbidden):
        entityUnknownWarning(Ent.CLOUD_IDENTITY_GROUP, groupEmail, i, count)
      except (GAPI.conditionNotMet, GAPI.serviceNotAvailable) as e:
        entityActionFailedWarning([Ent.CLOUD_IDENTITY_GROUP, groupEmail], str(e), i, count)
    if memberRestrictions:
      printGettingEntityItemForWhom(Ent.MEMBER_RESTRICTION, groupEmail, i, count)
      try:
        secInfo = callGAPI(ci.groups(), 'getSecuritySettings',
                           throwReasons=GAPI.CIGROUP_GET_THROW_REASONS, retryReasons=GAPI.CIGROUP_RETRY_REASONS,
                           name=f"{groupEntity['name']}/securitySettings", readMask='*')
        if 'memberRestriction' in secInfo:
          groupEntity['memberRestrictionQuery'] = secInfo['memberRestriction'].get('query', '')
          groupEntity['memberRestrictionEvaluation'] = secInfo['memberRestriction'].get('evaluation', {}).get('state', '')
      except (GAPI.notFound, GAPI.domainNotFound, GAPI.domainCannotUseApis,
              GAPI.forbidden, GAPI.badRequest, GAPI.invalid, GAPI.invalidArgument,
              GAPI.systemError, GAPI.permissionDenied, GAPI.serviceNotAvailable) as e:
        entityActionFailedWarning([Ent.CLOUD_IDENTITY_GROUP, groupEmail], str(e), i, count)
    _printGroupRow(groupEntity, groupMembers)
  if showItemCountOnly:
    writeStdout(f'{itemCount}\n')
    return
  if sortHeaders:
    sortTitles = ['email']
    if showCategory:
      sortTitles.append('allowExternalMembers')
    if addCSVData:
      sortTitles.extend(sorted(addCSVData.keys()))
    sortTitles.extend(CIGROUP_PRINT_ORDER)
    if rolesSet:
      setMemberDisplaySortTitles(memberDisplayOptions, sortTitles)
    csvPF.SetSortTitles(sortTitles)
  csvPF.SortRows('email', False)
  csvPF.writeCSVfile('Cloud Identity Groups')

# gam <UserTypeEntity> info cimember <GroupEntity>
def infoCIGroupMembers(entityList):
  from gam.cmd.groups.members import infoGroupMembers
  infoGroupMembers(entityList, True)

# gam info cimember <UserTypeEntity> <GroupEntity>
def doInfoCIGroupMembers():
  from gam.cmd.groups.members import infoGroupMembers
  infoGroupMembers(getEntityToModify(defaultEntityType=Cmd.ENTITY_USERS)[1], True)

def getCIGroupMembersEntityList(ci, entityList, query, subTitle, matchPatterns, fieldsList, csvPF):
  from gam.cmd.groups.members import clearUnneededGroupMatchPatterns
  if query:
    printGettingAllAccountEntities(Ent.CLOUD_IDENTITY_GROUP, query)
    parent = 'groups/-'
    try:
      result = callGAPIpages(ci.groups().memberships(), 'searchTransitiveGroups', 'memberships',
                             pageMessage=getPageMessage(showFirstLastItems=True), messageAttribute=['groupKey', 'id'],
                             throwReasons=GAPI.CIGROUP_LIST_USERKEY_THROW_REASONS, retryReasons=GAPI.CIGROUP_RETRY_REASONS,
                             parent=parent, query=query,
                             fields='nextPageToken,memberships(groupKey(id),relationType)', pageSize=500)
      entityList = [entity['groupKey']['id'] for entity in result if entity['relationType'] == 'DIRECT']
    except (GAPI.resourceNotFound, GAPI.domainNotFound, GAPI.domainCannotUseApis,
            GAPI.forbidden, GAPI.badRequest, GAPI.invalid,
            GAPI.systemError, GAPI.permissionDenied, GAPI.invalidArgument, GAPI.serviceNotAvailable) as e:
      entityActionFailedExit([Ent.CLOUD_IDENTITY_GROUP, parent], str(e))
  elif entityList is None:
    updateFieldsForCIGroupMatchPatterns(matchPatterns, fieldsList, csvPF)
    printGettingAllAccountEntities(Ent.CLOUD_IDENTITY_GROUP, subTitle)
    parent = f'customers/{GC.Values[GC.CUSTOMER_ID]}'
    try:
      entityList = callGAPIpages(ci.groups(), 'list', 'groups',
                                 pageMessage=getPageMessage(showFirstLastItems=True), messageAttribute=['groupKey', 'id'],
                                 throwReasons=GAPI.CIGROUP_LIST_THROW_REASONS, retryReasons=GAPI.CIGROUP_RETRY_REASONS,
                                 parent=parent, view='FULL',
                                 fields=f'nextPageToken,groups({",".join(set(fieldsList))})', pageSize=500)
    except (GAPI.resourceNotFound, GAPI.domainNotFound, GAPI.domainCannotUseApis,
            GAPI.forbidden, GAPI.badRequest, GAPI.invalid, GAPI.invalidArgument,
            GAPI.systemError, GAPI.permissionDenied, GAPI.serviceNotAvailable) as e:
      entityActionFailedExit([Ent.CLOUD_IDENTITY_GROUP, parent], str(e))
  else:
    clearUnneededGroupMatchPatterns(matchPatterns)
  return entityList

def getCIGroupTransitiveMembers(ci, groupName, membersList, i, count):
  try:
    groupMembers = callGAPIpages(ci.groups().memberships(), 'searchTransitiveMemberships', 'memberships',
                                 throwReasons=GAPI.CIGROUP_LIST_THROW_REASONS, retryReasons=GAPI.CIGROUP_RETRY_REASONS,
                                 parent=groupName,
                                 fields='nextPageToken,memberships(*)', pageSize=GC.Values[GC.MEMBER_MAX_RESULTS])
  except (GAPI.resourceNotFound, GAPI.domainNotFound, GAPI.domainCannotUseApis,
          GAPI.forbidden, GAPI.badRequest, GAPI.invalid, GAPI.invalidArgument, GAPI.systemError, GAPI.serviceNotAvailable):
    entityUnknownWarning(Ent.CLOUD_IDENTITY_GROUP, groupName, i, count)
    return False
  except GAPI.permissionDenied as e:
    entityActionFailedWarning([Ent.CLOUD_IDENTITY_GROUP, groupName], str(e))
    return False
  for member in groupMembers:
    membersList.append(getCIGroupTransitiveMemberRoleFixType(groupName, member))
  return True

def getCIGroupMembers(cd, ci, groupName, memberRoles, membersList, membersSet, i, count,
                      memberOptions, memberDisplayOptions, level, typesSet, groupEmail, kwargs):
  from gam.cmd.chat.members import _getChatSpaceMembers
  from gam.cmd.groups.members import _checkCIMemberMatch
  nameToPrint = groupEmail if groupEmail else groupName
  printGettingAllEntityItemsForWhom(memberRoles if memberRoles else Ent.ROLE_MANAGER_MEMBER_OWNER, nameToPrint, i, count)
  validRoles = _getCIRoleVerification(memberRoles)
  if memberOptions[MEMBEROPTION_INCLUDEDERIVEDMEMBERSHIP]:
    groupMembers = []
    if not getCIGroupTransitiveMembers(ci, groupName, groupMembers, i, count):
      return
    for member in groupMembers:
      if _checkMemberRole(member, validRoles):
        if member['type'] in typesSet and _checkCIMemberMatch(member, memberOptions):
          membersList.append(member)
    return
  if not groupEmail.startswith('space/'):
    try:
      groupMembers = callGAPIpages(ci.groups().memberships(), 'list', 'memberships',
                                   pageMessage=getPageMessageForWhom(),
                                   throwReasons=GAPI.CIGROUP_LIST_THROW_REASONS, retryReasons=GAPI.CIGROUP_RETRY_REASONS,
                                   parent=groupName, **kwargs)
    except (GAPI.resourceNotFound, GAPI.domainNotFound, GAPI.domainCannotUseApis,
            GAPI.forbidden, GAPI.badRequest, GAPI.invalid, GAPI.invalidArgument, GAPI.systemError,
            GAPI.permissionDenied, GAPI.serviceNotAvailable):
      entityUnknownWarning(Ent.CLOUD_IDENTITY_GROUP, nameToPrint, i, count)
      return
  else:
    groupMembers = _getChatSpaceMembers(cd, groupEmail, groupName)
  checkShowCategory = memberDisplayOptions['checkShowCategory']
  if not memberOptions[MEMBEROPTION_RECURSIVE]:
    if memberOptions[MEMBEROPTION_NODUPLICATES]:
      for member in groupMembers:
        getCIGroupMemberRoleFixType(member)
        memberName = member.get('preferredMemberKey', {}).get('id', '')
        if (_checkMemberRole(member, validRoles) and
            (not checkShowCategory or _checkCIMemberCategory(member, memberDisplayOptions)) and
            memberName not in membersSet):
          membersSet.add(memberName)
          if member['type'] in typesSet and _checkCIMemberMatch(member, memberOptions):
            membersList.append(member)
    else:
      for member in groupMembers:
        getCIGroupMemberRoleFixType(member)
        if (_checkMemberRole(member, validRoles) and
            (not checkShowCategory or _checkCIMemberCategory(member, memberDisplayOptions))):
          if member['type'] in typesSet and _checkCIMemberMatch(member, memberOptions):
            membersList.append(member)
  elif memberOptions[MEMBEROPTION_NODUPLICATES]:
    groupMemberList = []
    for member in groupMembers:
      getCIGroupMemberRoleFixType(member)
      memberName = member.get('preferredMemberKey', {}).get('id', '')
      if member['type'] != Ent.TYPE_GROUP:
        if (member['type'] in typesSet and
            _checkCIMemberMatch(member, memberOptions) and
            _checkMemberRole(member, validRoles) and
            (not checkShowCategory or _checkCIMemberCategory(member, memberDisplayOptions)) and
            memberName not in membersSet):
          membersSet.add(memberName)
          member['level'] = level
          member['subgroup'] = nameToPrint
          membersList.append(member)
      else:
        if memberName not in membersSet:
          membersSet.add(memberName)
          if (member['type'] in typesSet and
              _checkCIMemberMatch(member, memberOptions) and
              (not checkShowCategory or _checkCIMemberCategory(member, memberDisplayOptions))):
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
      getCIGroupMemberRoleFixType(member)
      memberName = member.get('preferredMemberKey', {}).get('id', '')
      if member['type'] != Ent.TYPE_GROUP:
        if (member['type'] in typesSet and
            _checkCIMemberMatch(member, memberOptions) and
            _checkMemberRole(member, validRoles) and
            (not checkShowCategory or _checkCIMemberCategory(member, memberDisplayOptions))):
          member['level'] = level
          member['subgroup'] = nameToPrint
          membersList.append(member)
      else:
        if (member['type'] in typesSet and
            _checkCIMemberMatch(member, memberOptions) and
            (not checkShowCategory or _checkCIMemberCategory(member, memberDisplayOptions))):
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
  from gam.cmd.groups.members import checkGroupMatchPatterns, finalizeIPSGMGroupRolesMemberDisplayOptions, getGroupAllowExternalMembers, getGroupMatchPatterns, getIPSGMGroupRolesMemberDisplayOptions, getMemberMatchOptions, initIPSGMGroupMemberDisplayOptions, initMemberOptions, mapCIGroupMemberFieldNames
  cd = buildGAPIObject(API.DIRECTORY)
  ci = buildGAPIObject(API.CLOUDIDENTITY_GROUPS)
  setTrueCustomerId(cd)
  parent = f'customers/{GC.Values[GC.CUSTOMER_ID]}'
  memberOptions = initMemberOptions()
  memberDisplayOptions = initIPSGMGroupMemberDisplayOptions()
  groupColumn = True
  subTitle = f'{Msg.ALL} {Ent.Plural(Ent.CLOUD_IDENTITY_GROUP)}'
  fieldsList = []
  groupFieldsLists = {'ci': ['groupKey', 'name']}
  csvPF = CSVPrintFile(['group'])
  FJQC = FormatJSONQuoteChar(csvPF)
  allowExternalMembers = entityList = query = showOwnedBy = None
  verifyAllowExternal = False
  rolesSet = set()
  typesSet = set()
  matchPatterns = {}
  listView = 'full'
  addCSVData = {}
  while Cmd.ArgumentsRemaining():
    myarg = getArgument()
    if myarg == 'todrive':
      csvPF.GetTodriveParameters()
    elif myarg == 'showownedby':
      showOwnedBy = convertUIDtoEmailAddress(getEmailAddress(), emailTypes=['user'])
    elif myarg in {'cimember', 'enterprisemember', 'ciowner'}:
      emailAddress = convertUIDtoEmailAddress(getEmailAddress(), emailTypes=['user', 'group'])
      query = f"member_key_id == '{emailAddress}' && '{CIGROUP_DISCUSSION_FORUM_LABEL}' in labels && parent == '{parent}'"
      entityList = None
      if myarg == 'ciowner':
        showOwnedBy = emailAddress
    elif myarg in {'cigroup', 'group'}:
      entityList = [getString(Cmd.OB_EMAIL_ADDRESS)]
      subTitle = f'{Ent.Singular(Ent.CLOUD_IDENTITY_GROUP)}={entityList[0]}'
      query = None
    elif getGroupMatchPatterns(myarg, matchPatterns, True):
      pass
    elif myarg == 'select':
      entityList = getEntityList(Cmd.OB_GROUP_ENTITY)
      subTitle = f'{Msg.SELECTED} {Ent.Plural(Ent.CLOUD_IDENTITY_GROUP)}'
      query = None
    elif getIPSGMGroupRolesMemberDisplayOptions(myarg, rolesSet, memberDisplayOptions):
      pass
    elif getCIGroupMemberTypes(myarg, typesSet):
      pass
    elif getMemberMatchOptions(myarg, memberOptions):
      pass
    elif getFieldsList(myarg, CIGROUPMEMBERS_FIELDS_CHOICE_MAP, fieldsList, initialField='preferredMemberKey'):
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
      verifyAllowExternal = getBoolean()
    elif myarg == 'addcsvdata':
      getAddCSVData(addCSVData)
    else:
      FJQC.GetFormatJSONQuoteChar(myarg, False)
  if listView == 'minimal' and memberOptions[MEMBEROPTION_RECURSIVE]:
    usageErrorExit(Msg.ARE_MUTUALLY_EXCLUSIVE.format('minimal', 'recursive'))
  if not typesSet:
    typesSet = {Ent.TYPE_USER} if memberOptions[MEMBEROPTION_RECURSIVE] else ALL_CIGROUP_MEMBER_TYPES
  showCategory, _ = finalizeIPSGMGroupRolesMemberDisplayOptions(cd, memberDisplayOptions, verifyAllowExternal)
  fields = ','.join(set(groupFieldsLists['ci']))
  entityList = getCIGroupMembersEntityList(ci, entityList, query, subTitle, matchPatterns, groupFieldsLists['ci'], csvPF)
  if not fieldsList:
    for field in CIGROUPMEMBERS_DEFAULT_FIELDS:
      addFieldToFieldsList(field, CIGROUPMEMBERS_FIELDS_CHOICE_MAP, fieldsList)
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
    rolesSet = ALL_GROUP_ROLES
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
      _, name, groupEmail = convertGroupEmailToCloudID(ci, group, i, count)
      if not name or not groupEmail:
        continue
      kvList = [Ent.CLOUD_IDENTITY_GROUP, groupEmail]
      try:
        groupEntity = callGAPI(ci.groups(), 'get',
                               throwReasons=GAPI.CIGROUP_GET_THROW_REASONS, retryReasons=GAPI.CIGROUP_RETRY_REASONS,
                               name=name, fields=fields)
      except (GAPI.notFound, GAPI.domainNotFound, GAPI.domainCannotUseApis,
              GAPI.forbidden, GAPI.badRequest, GAPI.invalid, GAPI.invalidArgument, GAPI.invalidArgument, GAPI.systemError,
              GAPI.permissionDenied, GAPI.serviceNotAvailable) as e:
        entityActionFailedWarning(kvList, str(e), i, count)
        continue
    groupEmail = groupEntity['groupKey']['id'].lower()
    kvList = [Ent.CLOUD_IDENTITY_GROUP, groupEmail]
    if showCategory:
      allowExternalMembers = getGroupAllowExternalMembers(memberDisplayOptions['gs'], groupEmail, verifyAllowExternal,
                                                          kvList, i, count)
      if allowExternalMembers is None:
        continue
    if not checkGroupMatchPatterns(groupEmail, groupEntity, matchPatterns):
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
      mapCIGroupMemberFieldNames(dmember)
      if not FJQC.formatJSON:
        if allowExternalMembers is not None:
          row['allowExternalMembers'] = allowExternalMembers
        if addCSVData:
          row.update(addCSVData)
        csvPF.WriteRowTitles(flattenJSON(dmember, flattened=row, timeObjects=CIGROUPMEMBERS_TIME_OBJECTS))
      else:
        row.update(dmember)
        fjrow = {}
        if groupColumn:
          fjrow['group'] = groupEmail
          if allowExternalMembers is not None:
            fjrow['allowExternalMembers'] = allowExternalMembers
        if addCSVData:
          fjrow.update(addCSVData)
        fjrow['JSON'] = json.dumps(cleanJSON(row, timeObjects=CIGROUPMEMBERS_TIME_OBJECTS),
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
  from gam.cmd.groups.members import _checkCIMemberMatch, checkGroupMatchPatterns, finalizeIPSGMGroupRolesMemberDisplayOptions, getGroupMatchPatterns, getIPSGMGroupRolesMemberDisplayOptions, getMemberMatchOptions, initIPSGMGroupMemberDisplayOptions, initMemberOptions
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
        membersList = callGAPIpages(ci.groups().memberships(), 'list', 'memberships',
                                    throwReasons=GAPI.CIGROUP_LIST_THROW_REASONS, retryReasons=GAPI.CIGROUP_RETRY_REASONS,
                                    parent=groupName, **kwargs)
        for member in membersList:
          getCIGroupMemberRoleFixType(member)
      except (GAPI.resourceNotFound, GAPI.domainNotFound, GAPI.domainCannotUseApis,
              GAPI.forbidden, GAPI.badRequest, GAPI.invalid, GAPI.invalidArgument, GAPI.systemError,
              GAPI.permissionDenied, GAPI.serviceNotAvailable):
        if depth == 0:
          entityUnknownWarning(Ent.CLOUD_IDENTITY_GROUP, groupEmail, i, count)
        return
    if showOwnedBy and not checkCIGroupShowOwnedBy(showOwnedBy, membersList):
      return
    if depth == 0:
      printEntity([Ent.CLOUD_IDENTITY_GROUP, groupEmail], i, count)
    if depth == 0 or Ent.TYPE_GROUP in typesSet:
      Ind.Increment()
    for member in sorted(membersList, key=lambda k: (_roleOrder(k.get('role', Ent.ROLE_MEMBER)), _typeOrder(k['type']))):
      if (_checkMemberIsSuspendedIsArchived(member, memberOptions[MEMBEROPTION_ISSUSPENDED], memberOptions[MEMBEROPTION_ISARCHIVED]) and
          (not checkShowCategory or _checkCIMemberCategory(member, memberDisplayOptions))):
        if (_checkMemberRole(member, rolesSet) and
            member['type'] in typesSet and
            _checkCIMemberMatch(member, memberOptions)):
          if listView != 'minimal':
            memberDetails = f'{member.get("role", Ent.ROLE_MEMBER)}, {member["type"]}, {member["preferredMemberKey"]["id"]}'
          else:
            memberDetails = f'{member.get("role", Ent.ROLE_MEMBER)}, {member["preferredMemberKey"]["id"]}'
          if showCategory:
            memberDetails += f', {member["category"]}'
          for field in ['createTime', 'updateTime', 'expireTime']:
            if field in member:
              memberDetails += f', {formatLocalTime(member[field])}'
          printKeyValueList([memberDetails])
        if not includeDerivedMembership and (member['type'] == Ent.TYPE_GROUP) and (maxdepth == -1 or depth < maxdepth):
          _, gname = member['name'].rsplit('/', 1)
          _showGroup(f'groups/{gname}', member['preferredMemberKey']['id'], depth+1)
    if depth == 0 or Ent.TYPE_GROUP in typesSet:
      Ind.Decrement()

  cd = buildGAPIObject(API.DIRECTORY)
  ci = buildGAPIObject(API.CLOUDIDENTITY_GROUPS)
  setTrueCustomerId(cd)
  parent = f'customers/{GC.Values[GC.CUSTOMER_ID]}'
  subTitle = f'{Msg.ALL} {Ent.Plural(Ent.CLOUD_IDENTITY_GROUP)}'
  groupFieldsLists = {'ci': ['groupKey', 'name']}
  entityList = query = showOwnedBy = None
  rolesSet = set()
  typesSet = set()
  memberOptions = initMemberOptions()
  memberDisplayOptions = initIPSGMGroupMemberDisplayOptions()
  matchPatterns = {}
  maxdepth = -1
  includeDerivedMembership = False
  listView = 'full'
  while Cmd.ArgumentsRemaining():
    myarg = getArgument()
    if myarg == 'showownedby':
      showOwnedBy = convertUIDtoEmailAddress(getEmailAddress(), emailTypes=['user'])
    elif myarg in {'cimember', 'enterprisemember', 'ciowner'}:
      emailAddress = convertUIDtoEmailAddress(getEmailAddress(), emailTypes=['user', 'group'])
      query = f"member_key_id == '{emailAddress}' && '{CIGROUP_DISCUSSION_FORUM_LABEL}' in labels parent == '{parent}'"
      entityList = None
      if myarg == 'ciowner':
        showOwnedBy = emailAddress
    elif myarg in {'cigroup', 'group'}:
      entityList = [getString(Cmd.OB_EMAIL_ADDRESS)]
      subTitle = f'{Ent.Singular(Ent.CLOUD_IDENTITY_GROUP)}={entityList[0]}'
      query = None
    elif getGroupMatchPatterns(myarg, matchPatterns, False):
      pass
    elif myarg == 'select':
      entityList = getEntityList(Cmd.OB_GROUP_ENTITY)
      subTitle = f'{Msg.SELECTED} {Ent.Plural(Ent.CLOUD_IDENTITY_GROUP)}'
      query = None
    elif getIPSGMGroupRolesMemberDisplayOptions(myarg, rolesSet, memberDisplayOptions):
      pass
    elif getCIGroupMemberTypes(myarg, typesSet):
      pass
    elif getMemberMatchOptions(myarg, memberOptions):
      pass
    elif myarg == 'depth':
      maxdepth = getInteger(minVal=-1)
    elif myarg == 'includederivedmembership':
      includeDerivedMembership = True
    elif myarg in {'minimal', 'basic', 'full'}:
      listView = myarg
    else:
      unknownArgumentExit()
  if not rolesSet:
    rolesSet = ALL_GROUP_ROLES
  if not typesSet:
    typesSet = ALL_CIGROUP_MEMBER_TYPES
  showCategory, checkShowCategory = finalizeIPSGMGroupRolesMemberDisplayOptions(cd, memberDisplayOptions, False)
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
      _, name, groupEmail = convertGroupEmailToCloudID(ci, group, i, count)
      if not name or not groupEmail:
        continue
      try:
        groupEntity = callGAPI(ci.groups(), 'get',
                               throwReasons=GAPI.CIGROUP_GET_THROW_REASONS, retryReasons=GAPI.CIGROUP_RETRY_REASONS,
                               name=name, fields=fields)
      except (GAPI.notFound, GAPI.domainNotFound, GAPI.domainCannotUseApis,
              GAPI.forbidden, GAPI.badRequest, GAPI.invalid, GAPI.invalidArgument, GAPI.systemError,
              GAPI.permissionDenied, GAPI.serviceNotAvailable) as e:
        entityActionFailedWarning([Ent.CLOUD_IDENTITY_GROUP, groupEmail], str(e), i, count)
        continue
    groupEmail = groupEntity['groupKey']['id'].lower()
    if checkGroupMatchPatterns(groupEmail, groupEntity, matchPatterns):
      _showGroup(groupEntity['name'], groupEmail, 0)

# gam print licenses [todrive <ToDriveAttribute>*]
#	[(products|product <ProductIDList>)|(skus|sku <SKUIDList>)|allskus|gsuite]
#	[maxresults <Integer>]
#	[countsonly]
