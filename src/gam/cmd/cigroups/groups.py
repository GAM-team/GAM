"""Cloud Identity group CRUD and listing.

Part of the _cigroups_tmp sub-package."""

"""GAM Cloud Identity group management."""

import re

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
from gam.util.access import entityUnknownWarning
from gam.util.api import buildGAPIObject, callGAPI, callGAPIpages
from gam.util.args import (
    NEVER_TIME,
    _getOptionalIsSuspendedIsArchived,
    checkArgumentPresent,
    checkForExtraneousArguments,
    formatLocalTime,
    getArgument,
    getChoice,
    getEmailAddress,
    getJSON,
    getREPattern,
    getREPatternSubstitution,
    getString,
    getTimeOrDeltaFromNow,
)
from gam.util.csv_pf import CSVPrintFile
from gam.util.display import (
    entityActionFailedWarning,
    entityActionNotPerformedWarning,
    entityActionPerformed,
    entityActionPerformedMessage,
    entityPerformActionNumItems,
    getPageMessageForWhom,
    printGettingAllEntityItemsForWhom,
)
from gam.util.entity import (
    checkGroupExists,
    convertGroupCloudIDToEmail,
    convertGroupEmailToCloudID,
    convertUIDtoEmailAddress,
    getCIGroupMemberRoleFixType,
    getEntityList,
    getEntityToModify,
)
from gam.util.errors import unknownArgumentExit

Act = glaction.GamAction()
Ent = glentity.GamEntity()
Ind = glindent.GamIndent()
Cmd = glclargs.GamCLArgs()


CIGROUP_DISCUSSION_FORUM_LABEL = 'cloudidentity.googleapis.com/groups.discussion_forum'
CIGROUP_DYNAMIC_LABEL = 'cloudidentity.googleapis.com/groups.dynamic'
CIGROUP_SECURITY_LABEL = 'cloudidentity.googleapis.com/groups.security'
CIGROUP_LOCKED_LABEL = 'cloudidentity.googleapis.com/groups.locked'


NEVER_TIME = '1970-01-01T00:00:00.000Z'


def doCreateCIGroup():
  from gam.cmd.groups.groups import doCreateGroup
  doCreateGroup(ciGroupsAPI=True)

# gam update cigroups <GroupEntity> [email <EmailAddress>]
#	[updateprimaryemail <RESEarchPattern> <RESubstitution> [preview]]
#	[copyfrom <GroupItem>] <GroupAttribute>*
#	[security|makesecuritygroup|dynamicsecurity|makedynamicsecuritygroup]
#	[dynamic <QueryDynamicGroup>]
#	[memberrestrictions <QueryMemberRestrictions>]
#	[locked|unlocked]
# gam update cigroups <GroupEntity> add|create [<GroupRole>]
#	[usersonly|groupsonly]
#	[notsuspended|suspended] [notarchived|archived]
#	[expire|expires <Time>] [preview] [actioncsv]
#	<UserTypeEntity>
# gam update cigroups <GroupEntity> delete|remove [<GroupRole>]
#	[usersonly|groupsonly]
#	[notsuspended|suspended] [notarchived|archived]
#	[preview] [actioncsv]
#	<UserTypeEntity>
# gam update cigroups <GroupEntity> sync [<GroupRole>|ignorerole]
#	[usersonly|groupsonly] [addonly|removeonly]
#	[notsuspended|suspended] [notarchived|archived]
#	[expire|expires <Time>] [preview] [actioncsv]
#	<UserTypeEntity>
# gam update cigroups <GroupEntity> update [<GroupRole>]
#	[usersonly|groupsonly]
#	[notsuspended|suspended] [notarchived|archived]
#	[expire|expires <Time>] [preview] [actioncsv]
#	<UserTypeEntity>
# gam update cigroups <GroupEntity> clear [member] [manager] [owner]
#	[usersonly|groupsonly]
#	[emailclearpattern|emailretainpattern <REMatchPattern>]
#	[preview] [actioncsv]
def doUpdateCIGroups():

  from gam.cmd.groups.groups import GROUP_ACCESS_TYPE_CHOICE_MAP, GROUP_CIGROUP_FIELDS_MAP, GROUP_JSON_SKIP_FIELDS, GROUP_PREVIEW_TITLES, GroupIsAbuseOrPostmaster, UPDATE_GROUP_SUBCMDS, checkReplyToCustom, getGroupAttrValue, getSettingsFromGroup, getSyncOperation, mapGroupEmailForSettings
  def _getExpireTime(role):
    if role == Ent.ROLE_MEMBER and checkArgumentPresent(['expire', 'expires']):
      return getTimeOrDeltaFromNow()
    return None

  def _getPreviewActionCSV():
    preview = checkArgumentPresent('preview')
    if checkArgumentPresent('actioncsv'):
      csvPF = CSVPrintFile(GROUP_PREVIEW_TITLES)
    else:
      csvPF = None
    return (preview, csvPF)

  def _validateSubkeyRoleGetMembers(group, role, origGroup, groupMemberLists, i, count):
    roleLower = role.lower()
    if roleLower in GROUP_ROLES_MAP:
      return (GROUP_ROLES_MAP[roleLower], groupMemberLists[origGroup][role])
    entityActionNotPerformedWarning([entityType, group, Ent.ROLE, role], Msg.INVALID_ROLE.format(','.join(sorted(GROUP_ROLES_MAP))), i, count)
    return (None, None)

  def _getRoleGroupMemberType(defaultRole=Ent.ROLE_MEMBER, allowIgnoreRole=False):
    if not allowIgnoreRole or not checkArgumentPresent(['ignorerole']):
      role = getChoice(GROUP_ROLES_MAP, defaultChoice=defaultRole, mapChoice=True)
    else:
      role = Ent.ROLE_ALL
    groupMemberType = getChoice({'usersonly': Ent.TYPE_USER, 'groupsonly': Ent.TYPE_GROUP}, defaultChoice='ALL', mapChoice=True)
    return (role, groupMemberType)

  def _getMemberEmail(member):
    if member['type'] == Ent.TYPE_CUSTOMER:
      return member['id']
    return member.get('preferredMemberKey', {}).get('id', '')

  def checkDynamicGroup(ci, group, i, count):
    try:
      result = callGAPI(ci.groups(), 'get',
                        throwReasons=GAPI.CIGROUP_GET_THROW_REASONS, retryReasons=GAPI.CIGROUP_RETRY_REASONS,
                        name=group, fields='labels')
      if CIGROUP_DYNAMIC_LABEL in result.get('labels', {}):
        entityActionNotPerformedWarning([entityType, group], Msg.DYNAMIC_GROUP_MEMBERSHIP_CANNOT_BE_MODIFIED, i, count)
        return True
      return False
    except (GAPI.notFound, GAPI.domainNotFound, GAPI.domainCannotUseApis,
            GAPI.forbidden, GAPI.badRequest, GAPI.invalid, GAPI.invalidArgument,
            GAPI.systemError, GAPI.permissionDenied, GAPI.serviceNotAvailable):
      return True

# Convert foo@googlemail.com to foo@gmail.com; eliminate periods in name for foo.bar@gmail.com
  def _cleanConsumerAddress(emailAddress, mapCleanToOriginal):
    atLoc = emailAddress.find('@')
    if atLoc > 0:
      if emailAddress[atLoc+1:] in {'gmail.com', 'googlemail.com'}:
        cleanEmailAddress = emailAddress[:atLoc].replace('.', '')+'@gmail.com'
        if cleanEmailAddress != emailAddress:
          mapCleanToOriginal[cleanEmailAddress] = emailAddress
          return cleanEmailAddress
    return emailAddress

  def _previewAction(group, members, role, jcount, action):
    Ind.Increment()
    j = 0
    for member in members:
      j += 1
      entityActionPerformed([entityType, group, role, member], j, jcount)
    Ind.Decrement()
    if csvPF:
      for member in members:
        csvPF.WriteRow({'group': group, 'email': member, 'role': role, 'action': Act.PerformedName(action), 'message': Act.PREVIEW})

  def _showSuccess(group, member, role, expireTime, j, jcount, optMsg=None):
    kvList = []
    if role is not None and role != 'None':
      kvList.append(f'{Ent.Singular(Ent.ROLE)}: {role}')
    if expireTime:
      kvList.extend(['expireTime', formatLocalTime(expireTime)])
    if optMsg:
      kvList.append(optMsg)
    entityActionPerformedMessage([entityType, group, Ent.MEMBER, member], ', '.join(kvList), j, jcount)
    if csvPF:
      csvPF.WriteRow({'group': group, 'email': member, 'role': role, 'action': Act.Performed(), 'message': Act.SUCCESS})

  def _showFailure(group, member, role, errMsg, j, jcount):
    entityActionFailedWarning([entityType, group, Ent.MEMBER, member], errMsg, j, jcount)
    if csvPF:
      csvPF.WriteRow({'group': group, 'email': member, 'role': role, 'action': Act.Failed(), 'message': errMsg})

  def _batchAddGroupMembers(group, i, count, addMembers, role, expireTime):
    Act.Set([Act.ADD, Act.ADD_PREVIEW][preview])
    jcount = len(addMembers)
    entityPerformActionNumItems([entityType, group], jcount, role, i, count)
    if jcount == 0:
      return
    if preview:
      _previewAction(group, addMembers, role, jcount, Act.ADD)
      return
    Ind.Increment()
    j = 0
    for member in addMembers:
      j += 1
      body = {'preferredMemberKey': {'id': member}, 'roles': [{'name': Ent.ROLE_MEMBER}]}
      if role != Ent.ROLE_MEMBER:
        body['roles'].append({'name': role})
      elif expireTime not in {None, NEVER_TIME}:
        body['roles'][0]['expiryDetail'] = {'expireTime': expireTime}
      try:
        callGAPI(ci.groups().memberships(), 'create',
                 throwReasons=GAPI.MEMBERS_THROW_REASONS+[GAPI.DUPLICATE, GAPI.MEMBER_NOT_FOUND, GAPI.RESOURCE_NOT_FOUND,
                                                          GAPI.INVALID_MEMBER, GAPI.CYCLIC_MEMBERSHIPS_NOT_ALLOWED,
                                                          GAPI.CONDITION_NOT_MET, GAPI.FAILED_PRECONDITION, GAPI.PERMISSION_DENIED,
                                                          GAPI.ALREADY_EXISTS, GAPI.INVALID_ARGUMENT, GAPI.CONFLICT],
                 parent=group, body=body, fields='')
        _showSuccess(group, member, role, expireTime, j, jcount)
      except (GAPI.groupNotFound, GAPI.domainNotFound, GAPI.domainCannotUseApis, GAPI.invalid, GAPI.forbidden):
        entityUnknownWarning(entityType, group, i, count)
      except (GAPI.duplicate, GAPI.memberNotFound, GAPI.resourceNotFound,
              GAPI.invalidMember, GAPI.cyclicMembershipsNotAllowed, GAPI.conditionNotMet,
              GAPI.failedPrecondition, GAPI.permissionDenied, GAPI.alreadyExists, GAPI.invalidArgument) as e:
        _showFailure(group, member, role, str(e), j, jcount)
      except GAPI.conflict:
        _showSuccess(group, member, role, expireTime, j, jcount, Msg.ACTION_MAY_BE_DELAYED)
    Ind.Decrement()

  def _batchRemoveGroupMembers(group, i, count, removeMembers, role):
    Act.Set([Act.REMOVE, Act.REMOVE_PREVIEW][preview])
    jcount = len(removeMembers)
    entityPerformActionNumItems([entityType, group], jcount, role, i, count)
    if jcount == 0:
      return
    if preview:
      _previewAction(group, removeMembers, role, jcount, Act.REMOVE)
      return
    Ind.Increment()
    j = 0
    for member in removeMembers:
      j += 1
      memberEmail = member['email']
      try:
        callGAPI(ci.groups().memberships(), 'delete',
                 throwReasons=GAPI.MEMBERS_THROW_REASONS+[GAPI.FAILED_PRECONDITION],
                 name=member['name'])
        _showSuccess(group, memberEmail, role, None, j, jcount)
      except (GAPI.memberNotFound, GAPI.invalidMember, GAPI.failedPrecondition, GAPI.permissionDenied) as e:
        _showFailure(group, memberEmail, role, str(e), j, jcount)
    Ind.Decrement()

  cd = buildGAPIObject(API.DIRECTORY)
  ci = buildGAPIObject(API.CLOUDIDENTITY_GROUPS)
  entityType = Ent.CLOUD_IDENTITY_GROUP
  csvPF = None
  getBeforeUpdate = preview = False
  entityList = getEntityList(Cmd.OB_GROUP_ENTITY)
  CL_subCommand = getChoice(UPDATE_GROUP_SUBCMDS, defaultChoice=None)
  lockGroup = None
  if not CL_subCommand:
    gs_body = {}
    ci_body = {}
    se_body = {}
    updatePrimaryEmail = []
    while Cmd.ArgumentsRemaining():
      myarg = getArgument()
      if myarg == 'email':
        ci_body['groupKey'] = {'id': getEmailAddress(noUid=True)}
      elif myarg == 'updateprimaryemail':
        updatePrimaryEmail = list(getREPatternSubstitution(re.IGNORECASE))
        updatePrimaryEmail.append(checkArgumentPresent(['preview']))
      elif myarg == 'getbeforeupdate':
        getBeforeUpdate = True
      elif myarg == 'dynamic':
        ci_body.setdefault('dynamicGroupMetadata', {'queries': []})
        ci_body['dynamicGroupMetadata']['queries'].append({'resourceType': 'USER',
                                                           'query': getString(Cmd.OB_QUERY)})
      elif myarg in {'security', 'makesecuritygroup'}:
        ci_body['labels'] = {CIGROUP_DISCUSSION_FORUM_LABEL: '',
                             CIGROUP_SECURITY_LABEL: ''}
      elif myarg in {'dynamicsecurity', 'makedynamicsecuritygroup'}:
        ci_body['labels'] = {CIGROUP_DISCUSSION_FORUM_LABEL: '',
                             CIGROUP_DYNAMIC_LABEL: '',
                             CIGROUP_SECURITY_LABEL: ''}
      elif myarg in {'lockedsecurity', 'makelockedsecuritygroup'}:
        ci_body['labels'] = {CIGROUP_DISCUSSION_FORUM_LABEL: '',
                             CIGROUP_LOCKED_LABEL: '',
                             CIGROUP_SECURITY_LABEL: ''}
      elif myarg in ['memberrestriction', 'memberrestrictions']:
        query = getString(Cmd.OB_QUERY, minLen=0)
        member_types = {'USER': '1', 'SERVICE_ACCOUNT': '2', 'GROUP': '3',}
        for key, val in member_types.items():
          query = query.replace(key, val)
        se_body['memberRestriction'] = {'query': query}
      elif myarg == 'locked':
        lockGroup = True
      elif myarg == 'unlocked':
        lockGroup = False
      elif myarg == 'json':
        gs_body.update(getJSON(GROUP_JSON_SKIP_FIELDS))
      elif myarg == 'accesstype':
        gs_body.update(getChoice(GROUP_ACCESS_TYPE_CHOICE_MAP, mapChoice=True))
      else:
        getGroupAttrValue(myarg, gs_body)
    if gs_body:
      gs = buildGAPIObject(API.GROUPSSETTINGS)
      gs_body = getSettingsFromGroup(cd, ','.join(entityList), gs, gs_body)
      for k, v in GROUP_CIGROUP_FIELDS_MAP.items():
        if k in gs_body:
          ci_body[v] = gs_body.pop(k)
      if gs_body:
        if not getBeforeUpdate:
          settings = gs_body
      elif not ci_body:
        return
    elif not ci_body and not se_body and not updatePrimaryEmail and lockGroup is None:
      return
    Act.Set(Act.UPDATE)
    i = 0
    count = len(entityList)
    for group in entityList:
      i += 1
      ci, _, group = convertGroupCloudIDToEmail(ci, group, i, count)
      if updatePrimaryEmail:
        if updatePrimaryEmail[0].search(group) is not None:
          ci_body['groupKey'] = {'id': re.sub(updatePrimaryEmail[0], updatePrimaryEmail[1], group)}
          if updatePrimaryEmail[2]:
            entityActionNotPerformedWarning([Ent.GROUP, group], Msg.UPDATE_PRIMARY_EMAIL_PREVIEW.format(ci_body['groupKey']['id']), i, count)
            continue
        else:
          entityActionNotPerformedWarning([Ent.GROUP, group], Msg.PRIMARY_EMAIL_DID_NOT_MATCH_PATTERN.format(updatePrimaryEmail[0].pattern), i, count)
          continue
      if gs_body and not GroupIsAbuseOrPostmaster(group):
        try:
          if group.find('@') == -1: # group settings API won't take uid so we make sure cd API is used so that we can grab real email.
            group = callGAPI(cd.groups(), 'get',
                             throwReasons=GAPI.GROUP_GET_THROW_REASONS, retryReasons=GAPI.GROUP_GET_RETRY_REASONS,
                             groupKey=group, fields='email')['email']
          if getBeforeUpdate:
            settings = callGAPI(gs.groups(), 'get',
                                throwReasons=GAPI.GROUP_SETTINGS_THROW_REASONS, retryReasons=GAPI.GROUP_SETTINGS_RETRY_REASONS,
                                groupUniqueId=mapGroupEmailForSettings(group), fields='*')
            settings.update(gs_body)
          if not checkReplyToCustom(group, settings, i, count):
            continue
        except GAPI.notFound:
          entityActionFailedWarning([entityType, group], Msg.DOES_NOT_EXIST, i, count)
          continue
        except (GAPI.groupNotFound, GAPI.domainNotFound, GAPI.domainCannotUseApis, GAPI.forbidden,
                GAPI.backendError, GAPI.invalid, GAPI.invalidInput, GAPI.badRequest, GAPI.permissionDenied,
                GAPI.systemError, GAPI.serviceLimit, GAPI.serviceNotAvailable, GAPI.authError) as e:
          entityActionFailedWarning([entityType, group], str(e), i, count)
          continue
      if gs_body and not GroupIsAbuseOrPostmaster(group):
        try:
          callGAPI(gs.groups(), 'update',
                   bailOnInvalidError='messageModerationLevel' in settings,
                   throwReasons=GAPI.GROUP_SETTINGS_THROW_REASONS, retryReasons=GAPI.GROUP_SETTINGS_RETRY_REASONS,
                   groupUniqueId=mapGroupEmailForSettings(group), body=settings, fields='')
        except GAPI.notFound:
          entityActionFailedWarning([entityType, group], Msg.DOES_NOT_EXIST, i, count)
          continue
        except (GAPI.groupNotFound, GAPI.domainNotFound, GAPI.domainCannotUseApis, GAPI.forbidden, GAPI.backendError,
                GAPI.invalid, GAPI.invalidArgument, GAPI.invalidAttributeValue, GAPI.invalidInput, GAPI.badRequest, GAPI.permissionDenied,
                GAPI.systemError, GAPI.serviceLimit, GAPI.serviceNotAvailable, GAPI.authError) as e:
          entityActionFailedWarning([entityType, group], str(e), i, count)
          continue
        except GAPI.required:
          entityActionFailedWarning([entityType, group], Msg.INVALID_JSON_SETTING, i, count)
          continue
      if ci_body or se_body or lockGroup is not None:
        _, name, groupEmail = convertGroupEmailToCloudID(ci, group, i, count)
        if not name or not groupEmail:
          continue
        twoUpdates = False
        if 'labels' in ci_body or lockGroup is not None:
          try:
            cigInfo = callGAPI(ci.groups(), 'get',
                               throwReasons=GAPI.CIGROUP_GET_THROW_REASONS,
                               retryReasons=GAPI.CIGROUP_RETRY_REASONS,
                               name=name, fields='labels')
          except (GAPI.notFound, GAPI.groupNotFound, GAPI.resourceNotFound, GAPI.domainNotFound, GAPI.domainCannotUseApis, GAPI.backendError,
                  GAPI.invalid, GAPI.invalidArgument, GAPI.invalidMember, GAPI.invalidParameter, GAPI.invalidInput, GAPI.forbidden,
                  GAPI.badRequest, GAPI.permissionDenied, GAPI.systemError, GAPI.serviceLimit, GAPI.serviceNotAvailable) as e:
            entityActionFailedWarning([Ent.CLOUD_IDENTITY_GROUP, group], str(e), i, count)
            continue
          # If a group currently isn't a security group or locked, and we want to add security and locked,
          # we have to do two commands to meet a beta requirement
          ci_body.setdefault('labels', {})
          if ((CIGROUP_SECURITY_LABEL not in cigInfo['labels']) and
              (CIGROUP_LOCKED_LABEL not in cigInfo['labels']) and
              ((CIGROUP_SECURITY_LABEL in ci_body['labels']) and
               ((CIGROUP_LOCKED_LABEL in ci_body['labels']) or lockGroup))):
            twoUpdates = True
          ci_body['labels'].update(cigInfo['labels'])
          if lockGroup is not None:
            if lockGroup:
              if CIGROUP_LOCKED_LABEL not in ci_body['labels']:
                ci_body['labels'][CIGROUP_LOCKED_LABEL] = ''
            else:
              if CIGROUP_LOCKED_LABEL in ci_body['labels']:
                ci_body['labels'].pop(CIGROUP_LOCKED_LABEL)
        if ci_body:
          try:
            if twoUpdates:
              ci_body['labels'].pop(CIGROUP_LOCKED_LABEL)
              callGAPI(ci.groups(), 'patch',
                       throwReasons=GAPI.CIGROUP_UPDATE_THROW_REASONS,
                       retryReasons=GAPI.CIGROUP_RETRY_REASONS,
                       name=name, body=ci_body, updateMask=','.join(list(ci_body.keys())))
              ci_body['labels'][CIGROUP_LOCKED_LABEL] = ''
            callGAPI(ci.groups(), 'patch',
                     throwReasons=GAPI.CIGROUP_UPDATE_THROW_REASONS,
                     retryReasons=GAPI.CIGROUP_RETRY_REASONS,
                     name=name, body=ci_body, updateMask=','.join(list(ci_body.keys())))
          except (GAPI.notFound, GAPI.groupNotFound, GAPI.domainNotFound, GAPI.domainCannotUseApis,
                  GAPI.forbidden, GAPI.badRequest, GAPI.invalid, GAPI.invalidInput, GAPI.invalidArgument,
                  GAPI.systemError, GAPI.permissionDenied, GAPI.failedPrecondition, GAPI.serviceNotAvailable) as e:
            entityActionFailedWarning([Ent.CLOUD_IDENTITY_GROUP, group], str(e), i, count)
            continue
        if se_body:
          # It seems like a bug that API requires /securitySettings appended to name.
          # We'll see if Google servers change this at some point.
          try:
            callGAPI(ci.groups(), 'updateSecuritySettings',
                     throwReasons=GAPI.CIGROUP_UPDATE_THROW_REASONS, retryReasons=GAPI.CIGROUP_RETRY_REASONS,
                     name=f'{name}/securitySettings', updateMask='member_restriction.query', body=se_body)
          except (GAPI.notFound, GAPI.groupNotFound, GAPI.domainNotFound, GAPI.domainCannotUseApis,
                  GAPI.forbidden, GAPI.badRequest, GAPI.invalid, GAPI.invalidInput, GAPI.invalidArgument,
                  GAPI.systemError, GAPI.permissionDenied, GAPI.failedPrecondition, GAPI.serviceNotAvailable) as e:
            entityActionFailedWarning([Ent.CLOUD_IDENTITY_GROUP, group], str(e), i, count)
            continue
      entityActionPerformed([entityType, group], i, count)
  elif CL_subCommand in {'create', 'add'}:
    baseRole, groupMemberType = _getRoleGroupMemberType()
    isSuspended, isArchived = _getOptionalIsSuspendedIsArchived()
    expireTime = _getExpireTime(baseRole)
    preview, csvPF = _getPreviewActionCSV()
    _, addMembers = getEntityToModify(defaultEntityType=Cmd.ENTITY_USERS,
                                      isSuspended=isSuspended, isArchived=isArchived, groupMemberType=groupMemberType)
    groupMemberLists = addMembers if isinstance(addMembers, dict) else None
    subkeyRoleField = GM.Globals[GM.CSV_SUBKEY_FIELD]
    checkForExtraneousArguments()
    i = 0
    count = len(entityList)
    for group in entityList:
      i += 1
      roleList = [baseRole]
      if groupMemberLists:
        if not subkeyRoleField:
          addMembers = groupMemberLists[group]
        else:
          roleList = groupMemberLists[group]
      origGroup = group
      _, parent, group = checkGroupExists(cd, ci, True, group, i, count)
      if not group or checkDynamicGroup(ci, parent, i, count):
        continue
      for role in roleList:
        if groupMemberLists and subkeyRoleField:
          role, addMembers = _validateSubkeyRoleGetMembers(group, role, origGroup, groupMemberLists, i, count)
          if role is None:
            continue
        _batchAddGroupMembers(parent, i, count,
                              [convertUIDtoEmailAddress(member, cd=cd, emailTypes='any',
                                                        checkForCustomerId=True, ciGroupsAPI=True) for member in addMembers],
                              role, expireTime)
  elif CL_subCommand in {'delete', 'remove'}:
    baseRole, groupMemberType = _getRoleGroupMemberType()
    isSuspended, isArchived = _getOptionalIsSuspendedIsArchived()
    preview, csvPF = _getPreviewActionCSV()
    _, removeMembers = getEntityToModify(defaultEntityType=Cmd.ENTITY_USERS,
                                         isSuspended=isSuspended, isArchived=isArchived, groupMemberType=groupMemberType)
    groupMemberLists = removeMembers if isinstance(removeMembers, dict) else None
    subkeyRoleField = GM.Globals[GM.CSV_SUBKEY_FIELD]
    checkForExtraneousArguments()
    i = 0
    count = len(entityList)
    for group in entityList:
      i += 1
      roleList = [baseRole]
      if groupMemberLists:
        if not subkeyRoleField:
          removeMembers = groupMemberLists[group]
        else:
          roleList = groupMemberLists[group]
      origGroup = group
      _, parent, group = checkGroupExists(cd, ci, True, group, i, count)
      if not group or checkDynamicGroup(ci, parent, i, count):
        continue
      for role in roleList:
        if groupMemberLists and subkeyRoleField:
          role, removeMembers = _validateSubkeyRoleGetMembers(group, role, origGroup, groupMemberLists, i, count)
          if role is None:
            continue
        Act.Set([Act.DELETE, Act.DELETE_PREVIEW][preview])
        jcount = len(removeMembers)
        entityPerformActionNumItems([entityType, group], jcount, Ent.MEMBER, i, count)
        if jcount == 0:
          continue
        if preview:
          _previewAction(group, removeMembers, role or Ent.ROLE_USER, jcount, Act.DELETE)
          continue
        Ind.Increment()
        j = 0
        for member in removeMembers:
          j += 1
          memberEmail = convertUIDtoEmailAddress(member, cd=cd, emailTypes='any',
                                                 checkForCustomerId=True, ciGroupsAPI=True)
          try:
            memberName = callGAPI(ci.groups().memberships(), 'lookup',
                                  throwReasons=GAPI.CIGROUP_GET_THROW_REASONS,
                                  parent=parent, memberKey_id=memberEmail, fields='name').get('name')
            callGAPI(ci.groups().memberships(), 'delete',
                     throwReasons=GAPI.MEMBERS_THROW_REASONS+[GAPI.FAILED_PRECONDITION],
                     name=memberName)
            _showSuccess(group, memberEmail, role, None, j, jcount)
          except (GAPI.groupNotFound, GAPI.domainNotFound, GAPI.domainCannotUseApis, GAPI.invalid, GAPI.invalidArgument, GAPI.forbidden,
                  GAPI.notFound, GAPI.memberNotFound, GAPI.permissionDenied, GAPI.invalidMember, GAPI.failedPrecondition) as e:
            _showFailure(group, memberEmail, role, str(e), j, jcount)
        Ind.Decrement()
  elif CL_subCommand == 'sync':
    baseRole, groupMemberType = _getRoleGroupMemberType(allowIgnoreRole=True)
    ignoreRole = baseRole == Ent.ROLE_ALL
    syncOperation = getSyncOperation()
    isSuspended, isArchived = _getOptionalIsSuspendedIsArchived()
    expireTime = _getExpireTime(baseRole)
    preview, csvPF = _getPreviewActionCSV()
    _, syncMembers = getEntityToModify(defaultEntityType=Cmd.ENTITY_USERS,
                                       isSuspended=isSuspended, isArchived=isArchived, groupMemberType=groupMemberType)
    groupMemberLists = syncMembers if isinstance(syncMembers, dict) else None
    subkeyRoleField = GM.Globals[GM.CSV_SUBKEY_FIELD]
    syncMembersSets = {}
    syncMembersMaps = {}
    currentMembersSets = {}
    currentMembersMaps = {}
    if groupMemberLists is None:
      syncMembersSets[baseRole] = set()
      syncMembersMaps[baseRole] = {}
      for member in syncMembers:
        syncMembersSets[baseRole].add(_cleanConsumerAddress(convertUIDtoEmailAddress(member, cd=cd, emailTypes='any',
                                                                                     checkForCustomerId=True, ciGroupsAPI=True), syncMembersMaps[baseRole]))
    checkForExtraneousArguments()
    i = 0
    count = len(entityList)
    for group in entityList:
      i += 1
      origGroup = group
      _, parent, group = checkGroupExists(cd, ci, True, group, i, count)
      if not group or checkDynamicGroup(ci, parent, i, count):
        continue
      if groupMemberLists is None:
        roleList = [baseRole]
      else:
        if not subkeyRoleField:
          roleList = [baseRole]
        else:
          roleList = groupMemberLists[origGroup]
        for role in roleList:
          role = role.upper()
          syncMembersSets[role] = set()
          syncMembersMaps[role] = {}
      rolesSet = set()
      for role in roleList:
        origRole = role
        role = role.upper()
        if groupMemberLists is None:
          rolesSet.add(role)
        else:
          if not subkeyRoleField:
            rolesSet.add(role)
            syncMembers = groupMemberLists[origGroup]
          else:
            role, syncMembers = _validateSubkeyRoleGetMembers(group, origRole, origGroup, groupMemberLists, i, count)
            if role is None:
              continue
            rolesSet.add(role)
          for member in syncMembers:
            syncMembersSets[role].add(_cleanConsumerAddress(convertUIDtoEmailAddress(member, cd=cd, emailTypes='any',
                                                                                     checkForCustomerId=True), syncMembersMaps[role]))
      if not rolesSet:
        continue
      memberRoles = ','.join(sorted(rolesSet))
      printGettingAllEntityItemsForWhom(memberRoles, group, entityType=entityType)
      try:
        result = callGAPIpages(ci.groups().memberships(), 'list', 'memberships',
                               pageMessage=getPageMessageForWhom(),
                               throwReasons=GAPI.MEMBERS_THROW_REASONS, retryReasons=GAPI.MEMBERS_RETRY_REASONS,
                               parent=parent, view='FULL',
                               fields='nextPageToken,memberships(name,preferredMemberKey(id),roles(name),type)',
                               pageSize=GC.Values[GC.MEMBER_MAX_RESULTS])
      except (GAPI.groupNotFound, GAPI.domainNotFound, GAPI.domainCannotUseApis, GAPI.invalid, GAPI.forbidden):
        entityUnknownWarning(Ent.CLOUD_IDENTITY_GROUP, group)
        continue
      except (GAPI.conditionNotMet, GAPI.serviceNotAvailable) as e:
        entityActionFailedWarning([Ent.CLOUD_IDENTITY_GROUP, group], str(e))
        continue
      currentMembersNames = {}
      for role in rolesSet:
        currentMembersSets[role] = set()
        currentMembersMaps[role] = {}
      for member in result:
        getCIGroupMemberRoleFixType(member)
        role = member['role'] if not ignoreRole else Ent.ROLE_ALL
        email = member.get('preferredMemberKey', {}).get('id', '')
        if groupMemberType in ('ALL', member['type']) and role in rolesSet:
          cleanAddress = _cleanConsumerAddress(email, currentMembersMaps[role])
          currentMembersSets[role].add(cleanAddress)
          currentMembersNames[cleanAddress] = member['name']
      del result
      if syncOperation != 'addonly':
        for role in rolesSet:
          _batchRemoveGroupMembers(parent, i, count,
                                   [{'name': currentMembersNames[emailAddress],
                                     'email': currentMembersMaps[role].get(emailAddress, emailAddress)} for emailAddress in currentMembersSets[role]-syncMembersSets[role]],
                                   role)
      if syncOperation != 'removeonly':
        for role in [Ent.ROLE_OWNER, Ent.ROLE_MANAGER, Ent.ROLE_MEMBER, Ent.ROLE_ALL]:
          if role in rolesSet:
            _batchAddGroupMembers(parent, i, count,
                                  [syncMembersMaps[role].get(emailAddress, emailAddress) for emailAddress in syncMembersSets[role]-currentMembersSets[role]],
                                  role if role != Ent.ROLE_ALL else Ent.ROLE_MEMBER, expireTime)
  elif CL_subCommand == 'update':
    baseRole, groupMemberType = _getRoleGroupMemberType()
    isSuspended, isArchived = _getOptionalIsSuspendedIsArchived()
    expireTime = _getExpireTime(baseRole)
    preview, csvPF = _getPreviewActionCSV()
    _, updateMembers = getEntityToModify(defaultEntityType=Cmd.ENTITY_USERS,
                                         isSuspended=isSuspended, isArchived=isArchived, groupMemberType=groupMemberType)
    groupMemberLists = updateMembers if isinstance(updateMembers, dict) else None
    subkeyRoleField = GM.Globals[GM.CSV_SUBKEY_FIELD]
    checkForExtraneousArguments()
    i = 0
    count = len(entityList)
    for group in entityList:
      i += 1
      roleList = [baseRole]
      if groupMemberLists:
        if not subkeyRoleField:
          updateMembers = groupMemberLists[group]
        else:
          roleList = groupMemberLists[group]
      origGroup = group
      _, parent, group = checkGroupExists(cd, ci, True, group, i, count)
      if not group or checkDynamicGroup(ci, parent, i, count):
        continue
      for role in roleList:
        if groupMemberLists and subkeyRoleField:
          role, updateMembers = _validateSubkeyRoleGetMembers(group, role, origGroup, groupMemberLists, i, count)
          if role is None:
            continue
        Act.Set([Act.UPDATE, Act.UPDATE_PREVIEW][preview])
        jcount = len(updateMembers)
        entityPerformActionNumItems([entityType, group], jcount, Ent.MEMBER, i, count)
        if jcount == 0:
          continue
        if preview:
          _previewAction(group, updateMembers, role, jcount, Act.UPDATE)
          continue
        Ind.Increment()
        j = 0
        for member in updateMembers:
          j += 1
          memberEmail = convertUIDtoEmailAddress(member, cd=cd, emailTypes='any',
                                                 checkForCustomerId=True, ciGroupsAPI=True)
          try:
            memberName = callGAPI(ci.groups().memberships(), 'lookup',
                                  throwReasons=GAPI.CIGROUP_GET_THROW_REASONS,
                                  parent=parent, memberKey_id=memberEmail, fields='name').get('name')
          except (GAPI.groupNotFound, GAPI.domainNotFound, GAPI.domainCannotUseApis, GAPI.invalid, GAPI.invalidArgument,
                  GAPI.forbidden, GAPI.notFound, GAPI.memberNotFound, GAPI.permissionDenied, GAPI.invalidMember) as e:
            _showFailure(group, memberEmail, role, str(e), j, jcount)
            continue
          preUpdateRoles = []
          addRoles = []
          removeRoles = []
          postUpdateRoles = []
          memberRoles = callGAPI(ci.groups().memberships(), 'get',
                                 name=memberName, fields='name,preferredMemberKey,roles,type')
          getCIGroupMemberRoleFixType(memberRoles)
          current_roles = [crole['name'] for crole in memberRoles['roles']]
          # When upgrading role, strip any expiryDetail from member before role changes
          if role != Ent.ROLE_MEMBER:
            if 'expireTime' in memberRoles:
              preUpdateRoles.append({'fieldMask': 'expiryDetail.expireTime',
                                     'membershipRole': {'name': Ent.ROLE_MEMBER, 'expiryDetail': {'expireTime': None}}})
          # When downgrading role or simply updating member expireTime, update expiryDetail after role changes
          elif expireTime:
            postUpdateRoles.append({'fieldMask': 'expiryDetail.expireTime',
                                    'membershipRole': {'name': role, 'expiryDetail': {'expireTime': expireTime if expireTime != NEVER_TIME else None}}})
          for crole in current_roles:
            if crole not in {Ent.ROLE_MEMBER, role}:
              removeRoles.append(crole)
          if role not in current_roles:
            new_role = {'name': role}
            if role == Ent.ROLE_MEMBER and expireTime not in {None, NEVER_TIME}:
              new_role['expiryDetail'] = {'expireTime': expireTime}
              postUpdateRoles = []
            addRoles.append(new_role)
          bodys = []
          if preUpdateRoles:
            bodys.append({'updateRolesParams': preUpdateRoles})
          if addRoles:
            bodys.append({'addRoles': addRoles})
          if removeRoles:
            bodys.append({'removeRoles': removeRoles})
          if postUpdateRoles:
            bodys.append({'updateRolesParams': postUpdateRoles})
          errors = False
          for body in bodys:
            try:
              callGAPI(ci.groups().memberships(), 'modifyMembershipRoles',
                       throwReasons=[GAPI.MEMBER_NOT_FOUND, GAPI.INVALID_MEMBER, GAPI.FAILED_PRECONDITION,
                                     GAPI.INVALID_ARGUMENT, GAPI.PERMISSION_DENIED],
                       name=memberName, body=body)
            except (GAPI.memberNotFound, GAPI.invalidMember, GAPI.failedPrecondition,
                    GAPI.invalidArgument, GAPI.permissionDenied) as e:
              _showFailure(group, memberEmail, role, str(e), j, jcount)
              errors = True
              break
          if not errors:
            _showSuccess(group, memberEmail, role, None, j, jcount)
        Ind.Decrement()
  else: #clear
    rolesSet = set()
    groupMemberType = 'ALL'
    isSuspended = None
    emailMatchPattern = None
    clearMatch = True
    qualifier = ''
    while Cmd.ArgumentsRemaining():
      myarg = getArgument()
      if myarg in GROUP_ROLES_MAP:
        rolesSet.add(GROUP_ROLES_MAP[myarg])
      elif myarg == 'usersonly':
        groupMemberType = Ent.TYPE_USER
      elif myarg == 'groupsonly':
        groupMemberType = Ent.TYPE_GROUP
      elif myarg in {'emailclearpattern', 'emailretainpattern'}:
        emailMatchPattern = getREPattern(re.IGNORECASE)
        clearMatch = myarg == 'emailclearpattern'
      elif myarg == 'preview':
        preview = True
      elif myarg == 'actioncsv':
        csvPF = CSVPrintFile(GROUP_PREVIEW_TITLES)
      else:
        unknownArgumentExit()
    Act.Set(Act.REMOVE)
    if not rolesSet:
      rolesSet.add(Ent.ROLE_MEMBER)
    memberRoles = ','.join(sorted(rolesSet))
    i = 0
    count = len(entityList)
    for group in entityList:
      i += 1
      _, parent, group = checkGroupExists(cd, ci, True, group, i, count)
      if not group or checkDynamicGroup(ci, parent, i, count):
        continue
      printGettingAllEntityItemsForWhom(memberRoles, group, qualifier=qualifier, entityType=entityType)
      try:
        result = callGAPIpages(ci.groups().memberships(), 'list', 'memberships',
                               pageMessage=getPageMessageForWhom(),
                               throwReasons=GAPI.MEMBERS_THROW_REASONS, retryReasons=GAPI.MEMBERS_RETRY_REASONS,
                               parent=parent, view='FULL',
                               fields='nextPageToken,memberships(name,preferredMemberKey(id),roles(name),type)',
                               pageSize=GC.Values[GC.MEMBER_MAX_RESULTS])
      except (GAPI.groupNotFound, GAPI.domainNotFound, GAPI.domainCannotUseApis, GAPI.invalid, GAPI.forbidden):
        entityUnknownWarning(entityType, group, i, count)
        continue
      except (GAPI.conditionNotMet, GAPI.serviceNotAvailable) as e:
        entityActionFailedWarning([entityType, group], str(e), i, count)
        continue
      removeMembers = {}
      for role in rolesSet:
        removeMembers[role] = []
      for member in result:
        getCIGroupMemberRoleFixType(member)
        memberName = member['name']
        memberEmail = _getMemberEmail(member)
        role = member['role']
        if groupMemberType in ('ALL', member['type']) and role in rolesSet:
          if emailMatchPattern is None:
            removeMembers[role].append({'name': memberName, 'email': memberEmail})
          elif member['type'] == Ent.TYPE_CUSTOMER:
            pass
          elif emailMatchPattern.match(email):
            if clearMatch:
              removeMembers[role].append({'name': memberName, 'email': memberEmail})
          else:
            if not clearMatch:
              removeMembers[role].append({'name': memberName, 'email': memberEmail})
      del result
      for role in rolesSet:
        _batchRemoveGroupMembers(group, i, count, removeMembers[role], role)
  if csvPF:
    csvPF.writeCSVfile('Cloud Identity Group Updates')

# gam delete cigroups <GroupEntity>
def doDeleteCIGroups():
  from gam.cmd.groups.groups import doDeleteGroups
  doDeleteGroups(ciGroupsAPI=True)

CIGROUP_MEMBER_TYPES_MAP = {
  'cbcmbrowser': Ent.TYPE_CBCM_BROWSER,
  'chromeosdevice': Ent.TYPE_OTHER,
  'customer': Ent.TYPE_CUSTOMER,
  'group': Ent.TYPE_GROUP,
  'other': Ent.TYPE_OTHER,
  'serviceaccount': Ent.TYPE_SERVICE_ACCOUNT,
  'user': Ent.TYPE_USER,
  }
ALL_CIGROUP_MEMBER_TYPES = {
  Ent.TYPE_CBCM_BROWSER, Ent.TYPE_CUSTOMER, Ent.TYPE_GROUP,
  Ent.TYPE_OTHER, Ent.TYPE_SERVICE_ACCOUNT, Ent.TYPE_USER}

