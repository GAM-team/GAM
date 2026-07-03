"""User group membership and Looker Studio operations.

Part of the _userop_tmp sub-package."""

"""GAM user operations: Looker Studio, user groups, licenses, photos, profile, sheets, tokens, deprovision."""

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

def processLookerStudioPermissions(users):
  action = Act.Get()
  if action == Act.CREATE:
    action = Act.ADD
  modifier = LOOKERSTUDIO_PERMISSION_MODIFIER_MAP[action]
  parameters, assetTypes = _getMain().initLookerStudioAssetSelectionParameters()
  permissions = {}
  assetIdEntity = None
  showDetails = True
  while Cmd.ArgumentsRemaining():
    myarg = _getMain().getArgument()
    if _getMain().getLookerStudioAssetSelectionParameters(myarg, parameters, assetTypes):
      pass
    elif myarg in {'assetid', 'assetids'}:
      assetIdEntity = _getMain().getUserObjectEntity(Cmd.OB_USER_ENTITY, Ent.LOOKERSTUDIO_ASSETID)
    elif myarg == 'role':
      permissions.setdefault('permissions', {})
      if action in {Act.ADD, Act.UPDATE}:
        role = _getMain().getChoice(LOOKERSTUDIO_ADD_UPDATE_PERMISSION_ROLE_CHOICE_MAP, mapChoice=True)
      else:
        role = _getMain().getChoice(LOOKERSTUDIO_DELETE_PERMISSION_ROLE_CHOICE_MAP, mapChoice=True)
      permissions['permissions'].setdefault(role, {'members': []})
      permissions['permissions'][role]['members'].extend(_getMain().getEntityList(Cmd.OB_LOOKERSTUDIO_PERMISSION_ENTITY))
    elif myarg == 'nodetails':
      showDetails = False
    else:
      _getMain().unknownArgumentExit()
  if not permissions:
    if action in {Act.ADD, Act.UPDATE}:
      _getMain().missingArgumentExit('role editor|owner|viewer members')
    else:
      _getMain().missingArgumentExit('members')
  i, count, users = _getMain().getEntityArgument(users)
  for user in users:
    i += 1
    user, ds, assets, jcount = _getMain()._validateUserGetLookerStudioAssetIds(user, i, count, assetIdEntity)
    if not ds:
      continue
    if assetIdEntity is None:
      assets, jcount = _getMain()._getLookerStudioAssets(ds, user, i, count, parameters, assetTypes, 'nextPageToken,assets(name,title)', None)
      if assets is None:
        continue
    _getMain().entityPerformActionSubItemModifierNumItems([Ent.USER, user], Ent.LOOKERSTUDIO_PERMISSION, modifier, jcount, Ent.LOOKERSTUDIO_ASSET, i, count)
    j = 0
    for asset in assets:
      j += 1
      for role in permissions['permissions']:
        try:
          body = {'name': asset['name'], 'members': permissions['permissions'][role]['members']}
          if action in {Act.DELETE, Act.UPDATE}:
            results = _getMain().callGAPI(ds.assets().permissions(), 'revokeAllPermissions',
                               throwReasons=GAPI.LOOKERSTUDIO_THROW_REASONS,
                               name=asset['name'], body=body)
          if action in {Act.ADD, Act.UPDATE}:
            body['role'] = role
            results = _getMain().callGAPI(ds.assets().permissions(), 'addMembers',
                               throwReasons=GAPI.LOOKERSTUDIO_THROW_REASONS,
                               name=asset['name'], body=body)
          _getMain().entityActionPerformed([Ent.USER, user, Ent.LOOKERSTUDIO_ASSET, asset['title'], Ent.LOOKERSTUDIO_PERMISSION, ''], j, jcount)
          if showDetails:
            _getMain()._showLookerStudioPermissions(user, asset, results, j, jcount, None)
        except (GAPI.invalidArgument, GAPI.badRequest, GAPI.notFound, GAPI.permissionDenied, GAPI.internalError) as e:
          _getMain().entityActionFailedWarning([Ent.USER, user, Ent.LOOKERSTUDIO_ASSET, asset['title']], str(e), j, jcount)
          continue
        except GAPI.serviceNotAvailable:
          _getMain().userLookerStudioServiceNotEnabledWarning(user, i, count)
          break

# gam <UserTypeEntity> print lookerstudiopermissions [todrive <ToDriveAttribute>*]
#	[([assettype report|datasource|all] [title <String>]
#	  [owner <Emailddress>] [includetrashed]
#	  [orderby title [ascending|descending]]) |
#	 (assetids <LookerStudioAssetIDEntity>)]
#	[role editor|owner|viewer]
#	[formatjson [quotechar <Character>]]
# gam <UserTypeEntity> show lookerstudiopermissions
#	[([assettype report|datasource|all] [title <String>]
#	  [owner <Emailddress>] [includetrashed]
#	  [orderby title [ascending|descending]]) |
#	 (assetids <LookerStudioAssetIDEntity>)[
#	[role editor|owner|viewer]
#	[formatjson]
def printShowLookerStudioPermissions(users):
  def _printLookerStudioPermissions(user, asset, permissions):
    row = _getMain().flattenJSON(permissions, flattened={'User': user, 'assetId': asset['name']},
                      simpleLists=['members'], delimiter=delimiter)
    if not FJQC.formatJSON:
      csvPF.WriteRowTitles(row)
    elif csvPF.CheckRowTitles(row):
      csvPF.WriteRowNoFilter({'User': user, 'assetId': asset['name'],
                              'JSON': json.dumps(_getMain().cleanJSON(permissions), ensure_ascii=False, sort_keys=True)})

  csvPF = _getMain().CSVPrintFile(['User', 'assetId']) if Act.csvFormat() else None
  FJQC = _getMain().FormatJSONQuoteChar(csvPF)
  delimiter = GC.Values[GC.CSV_OUTPUT_FIELD_DELIMITER]
  parameters, assetTypes = _getMain().initLookerStudioAssetSelectionParameters()
  assetIdEntity = None
  role = None
  while Cmd.ArgumentsRemaining():
    myarg = _getMain().getArgument()
    if csvPF and myarg == 'todrive':
      csvPF.GetTodriveParameters()
    elif _getMain().getLookerStudioAssetSelectionParameters(myarg, parameters, assetTypes):
      pass
    elif myarg in {'assetid', 'assetids'}:
      assetIdEntity = _getMain().getUserObjectEntity(Cmd.OB_USER_ENTITY, Ent.LOOKERSTUDIO_ASSETID)
    elif myarg == 'role':
      role = _getMain().getChoice(LOOKERSTUDIO_VIEW_PERMISSION_ROLE_CHOICE_MAP, mapChoice=True)
    elif myarg == 'delimiter':
      delimiter = _getMain().getCharacter()
    else:
      FJQC.GetFormatJSONQuoteChar(myarg, True)
  i, count, users = _getMain().getEntityArgument(users)
  for user in users:
    i += 1
    user, ds, assets, jcount = _getMain()._validateUserGetLookerStudioAssetIds(user, i, count, assetIdEntity)
    if not ds:
      continue
    if assetIdEntity is None:
      assets, jcount = _getMain()._getLookerStudioAssets(ds, user, i, count, parameters, assetTypes, 'nextPageToken,assets(name,title)', None)
      if assets is None:
        continue
    if not csvPF:
      if not FJQC.formatJSON:
        _getMain().entityPerformActionNumItems([Ent.USER, user], jcount, Ent.LOOKERSTUDIO_ASSET, i, count)
    elif jcount == 0 and GC.Values[GC.CSV_OUTPUT_USERS_AUDIT]:
      csvPF.WriteRowNoFilter({'User': user})
      continue
    j = 0
    for asset in assets:
      j += 1
      try:
        permissions = _getMain().callGAPI(ds.assets(), 'getPermissions',
                               throwReasons=GAPI.LOOKERSTUDIO_THROW_REASONS,
                               name=asset['name'], role=role)
      except (GAPI.invalidArgument, GAPI.badRequest, GAPI.notFound, GAPI.permissionDenied, GAPI.internalError) as e:
        _getMain().entityActionFailedWarning([Ent.USER, user, Ent.LOOKERSTUDIO_ASSET, asset['title']], str(e), j, jcount)
        continue
      except GAPI.serviceNotAvailable:
        _getMain().userLookerStudioServiceNotEnabledWarning(user, i, count)
        break
      if not csvPF:
        Ind.Increment()
        _getMain()._showLookerStudioPermissions(user, asset, permissions, j, jcount, FJQC)
        Ind.Decrement()
      else:
        _printLookerStudioPermissions(user, asset, permissions)
  if csvPF:
    csvPF.writeCSVfile('Looker Studio Permissions')

def _validateSubkeyRoleGetGroups(user, role, origUser, userGroupLists, i, count):
  roleLower = role.lower()
  if roleLower in GROUP_ROLES_MAP:
    return (GROUP_ROLES_MAP[roleLower], userGroupLists[origUser][role])
  _getMain().entityActionNotPerformedWarning([Ent.USER, user, Ent.ROLE, role], Msg.INVALID_ROLE.format(','.join(sorted(GROUP_ROLES_MAP))), i, count)
  return (None, None)

def _addUserToGroups(cd, user, addGroupsSet, addGroups, i, count):
  jcount = len(addGroupsSet)
  _getMain().entityPerformActionModifierNumItems([Ent.USER, user], Act.MODIFIER_TO, jcount, Ent.GROUP, i, count)
  Ind.Increment()
  j = 0
  for group in sorted(addGroupsSet):
    j += 1
    role = addGroups[group]['role']
    body = {'email': user, 'role': role}
    if addGroups[group]['delivery_settings'] != _getMain().DELIVERY_SETTINGS_UNDEFINED:
      body['delivery_settings'] = addGroups[group]['delivery_settings']
    try:
      _getMain().callGAPI(cd.members(), 'insert',
               throwReasons=GAPI.MEMBERS_THROW_REASONS+[GAPI.DUPLICATE, GAPI.MEMBER_NOT_FOUND, GAPI.RESOURCE_NOT_FOUND,
                                                        GAPI.INVALID_MEMBER, GAPI.CYCLIC_MEMBERSHIPS_NOT_ALLOWED,
                                                        GAPI.CONDITION_NOT_MET, GAPI.CONFLICT],
               retryReasons=GAPI.MEMBERS_RETRY_REASONS,
               groupKey=group, body=body, fields='')
      _getMain().entityActionPerformed([Ent.GROUP, group, role, user], j, jcount)
    except (GAPI.groupNotFound, GAPI.domainNotFound, GAPI.domainCannotUseApis, GAPI.invalid):
      _getMain().entityUnknownWarning(Ent.GROUP, group, j, jcount)
    except (GAPI.duplicate, GAPI.cyclicMembershipsNotAllowed, GAPI.conditionNotMet, GAPI.serviceNotAvailable) as e:
      _getMain().entityActionFailedWarning([Ent.GROUP, group, role, user], str(e), j, jcount)
    except GAPI.conflict:
      _getMain().entityActionPerformedMessage([Ent.GROUP, group, role, user], Msg.ACTION_MAY_BE_DELAYED, j, jcount)
    except (GAPI.memberNotFound, GAPI.resourceNotFound, GAPI.invalidMember) as e:
      _getMain().entityActionFailedWarning([Ent.USER, user], str(e), i, count)
    except (GAPI.forbidden, GAPI.permissionDenied) as e:
      ClientAPIAccessDeniedExit(str(e))
  Ind.Decrement()

# gam <UserTypeEntity> add group|groups
#	([<GroupRole>] [[delivery] <DeliverySetting>] <GroupEntity>)+
def addUserToGroups(users):
  cd = _getMain().buildGAPIObject(API.DIRECTORY)
  baseRole = _getMain().getChoice(GROUP_ROLES_MAP, defaultChoice=Ent.ROLE_MEMBER, mapChoice=True)
  baseDeliverySettings = _getMain().getDeliverySettings()
  groupKeys = _getMain().getEntityList(Cmd.OB_GROUP_ENTITY)
  subkeyRoleField = GM.Globals[GM.CSV_SUBKEY_FIELD]
  if not isinstance(groupKeys, dict):
    userGroupLists = None
    addGroups = {}
    for group in groupKeys:
      addGroups[_getMain().normalizeEmailAddressOrUID(group)] = {'role': baseRole, 'delivery_settings': baseDeliverySettings}
    while Cmd.ArgumentsRemaining():
      role = _getMain().getChoice(GROUP_ROLES_MAP, defaultChoice=Ent.ROLE_MEMBER, mapChoice=True)
      deliverySettings = _getMain().getDeliverySettings()
      for group in _getMain().getEntityList(Cmd.OB_GROUP_ENTITY):
        addGroups[_getMain().normalizeEmailAddressOrUID(group)] = {'role': role, 'delivery_settings': deliverySettings}
  else:
    userGroupLists = groupKeys
    _getMain().checkForExtraneousArguments()
  i, count, users = _getMain().getEntityArgument(users)
  for user in users:
    i += 1
    origUser = user
    user = _getMain().normalizeEmailAddressOrUID(user)
    if userGroupLists:
      roleList = [baseRole]
      if not subkeyRoleField:
        groupKeys = userGroupLists[origUser]
      else:
        roleList = userGroupLists[origUser]
      addGroups = {}
      for role in roleList:
        if subkeyRoleField:
          role, groupKeys = _validateSubkeyRoleGetGroups(user, role, origUser, userGroupLists, i, count)
          if role is None:
            continue
        for group in groupKeys:
          addGroups[_getMain().normalizeEmailAddressOrUID(group)] = {'role': role, 'delivery_settings': DELIVERY_SETTINGS_UNDEFINED}
    _addUserToGroups(cd, user, set(addGroups), addGroups, i, count)

def _deleteUserFromGroups(cd, user, deleteGroupsSet, deleteGroups, i, count):
  jcount = len(deleteGroupsSet)
  _getMain().entityPerformActionModifierNumItems([Ent.USER, user], Act.MODIFIER_FROM, jcount, Ent.GROUP, i, count)
  Ind.Increment()
  j = 0
  for group in sorted(deleteGroupsSet):
    j += 1
    role = deleteGroups[group]['role']
    try:
      _getMain().callGAPI(cd.members(), 'delete',
               throwReasons=GAPI.MEMBERS_THROW_REASONS+[GAPI.MEMBER_NOT_FOUND, GAPI.INVALID_MEMBER,
                                                        GAPI.CONDITION_NOT_MET, GAPI.CONFLICT],
               retryReasons=GAPI.MEMBERS_RETRY_REASONS,
               groupKey=group, memberKey=user)
      _getMain().entityActionPerformed([Ent.GROUP, group, role, user], j, jcount)
    except (GAPI.groupNotFound, GAPI.domainNotFound, GAPI.domainCannotUseApis, GAPI.invalid):
      _getMain().entityUnknownWarning(Ent.GROUP, group, j, jcount)
    except (GAPI.memberNotFound, GAPI.invalidMember, GAPI.conditionNotMet, GAPI.serviceNotAvailable) as e:
      _getMain().entityActionFailedWarning([Ent.USER, user, Ent.GROUP, group], str(e), j, jcount)
    except GAPI.conflict:
      _getMain().entityActionPerformedMessage([Ent.GROUP, group, role, user], Msg.ACTION_MAY_BE_DELAYED, j, jcount)
    except (GAPI.forbidden, GAPI.permissionDenied) as e:
      ClientAPIAccessDeniedExit(str(e))
  Ind.Decrement()

def _getUserGroupOptionalDomainCustomerId():
  if _getMain().checkArgumentPresent('domain'):
    return {'domain': _getMain().getString(Cmd.OB_DOMAIN_NAME).lower()}
  if _getMain().checkArgumentPresent('customerid'):
    return {'customer': _getMain().getString(Cmd.OB_CUSTOMER_ID)}
  return {}

def _setUserGroupArgs(user, kwargs):
  if 'customer' in kwargs:
    if "'" not in user:
      kwargs['query'] = f'memberKey={user}'
    else:
      quser = user.replace("'", "\\'")
      kwargs['query'] = f'memberKey={quser}'
  else:
    kwargs['userKey'] = user

def checkUserGroupMatchPattern(groupEmail, matchPattern):
  if not matchPattern['not']:
    if not matchPattern['pattern'].match(groupEmail):
      return False
  else:
    if matchPattern['pattern'].match(groupEmail):
      return False
  return True

# gam <UserTypeEntity> delete group|groups
#	[(domain <DomainName>)|(customerid <CustomerID>)|
#	 (emailmatchpattern [not] <REMatchPattern>)|<GroupEntity>]
def deleteUserFromGroups(users):
  cd = _getMain().buildGAPIObject(API.DIRECTORY)
  groupKeys = None
  matchPattern = {}
  kwargs = _getUserGroupOptionalDomainCustomerId()
  if not kwargs:
    kwargs = {'customer': GC.Values[GC.CUSTOMER_ID]}
    deleteGroups = {}
    if Cmd.ArgumentsRemaining():
      if not _getMain().checkArgumentPresent('emailmatchpattern'):
        groupKeys = _getMain().getEntityList(Cmd.OB_GROUP_ENTITY)
        userGroupLists = groupKeys if isinstance(groupKeys, dict) else None
        for group in groupKeys:
          deleteGroups[_getMain().normalizeEmailAddressOrUID(group)] = {'role': Ent.MEMBER}
      else:
        matchPattern = {'not': checkArgumentPresent('not'), 'pattern': _getMain().getREPattern(re.IGNORECASE)}
      _getMain().checkForExtraneousArguments()
  else:
    _getMain().checkForExtraneousArguments()
  role = Ent.MEMBER
  i, count, users = _getMain().getEntityArgument(users)
  for user in users:
    i += 1
    origUser = user
    user = _getMain().normalizeEmailAddressOrUID(user)
    if groupKeys is None:
      _setUserGroupArgs(user, kwargs)
      try:
        result = _getMain().callGAPIpages(cd.groups(), 'list', 'groups',
                               throwReasons=GAPI.GROUP_LIST_USERKEY_THROW_REASONS,
                               retryReasons=GAPI.SERVICE_NOT_AVAILABLE_RETRY_REASONS,
                               orderBy='email', fields='nextPageToken,groups(email)', **kwargs)
      except (GAPI.invalidMember, GAPI.invalidInput):
        _getMain().badRequestWarning(Ent.GROUP, Ent.MEMBER, user)
        continue
      except (GAPI.resourceNotFound, GAPI.domainNotFound, GAPI.badRequest):
        accessErrorExit(cd)
      except (GAPI.forbidden, GAPI.permissionDenied) as e:
        ClientAPIAccessDeniedExit(str(e))
      deleteGroups = {}
      for group in result:
        if not matchPattern or checkUserGroupMatchPattern(group['email'], matchPattern):
          deleteGroups[group['email']] = {'role': role}
    elif userGroupLists:
      userGroupKeys = userGroupLists[origUser]
      deleteGroups = {}
      for group in userGroupKeys:
        deleteGroups[_getMain().normalizeEmailAddressOrUID(group)] = {'role': role}
    _deleteUserFromGroups(cd, user, set(deleteGroups), deleteGroups, i, count)

def _updateUserGroups(cd, user, updateGroupsSet, updateGroups, i, count):
  jcount = len(updateGroupsSet)
  _getMain().entityPerformActionNumItems([Ent.USER, user], jcount, Ent.GROUP, i, count)
  Ind.Increment()
  j = 0
  for group in sorted(updateGroupsSet):
    j += 1
    role = updateGroups[group]['role']
    body = {'email': user, 'role': role}
    if updateGroups[group]['delivery_settings'] != _getMain().DELIVERY_SETTINGS_UNDEFINED:
      body['delivery_settings'] = updateGroups[group]['delivery_settings']
    try:
      _getMain().callGAPI(cd.members(), 'patch',
               throwReasons=GAPI.MEMBERS_THROW_REASONS+[GAPI.MEMBER_NOT_FOUND, GAPI.INVALID_MEMBER, GAPI.CONDITION_NOT_MET],
               retryReasons=GAPI.MEMBERS_RETRY_REASONS,
               groupKey=group, memberKey=user, body=body, fields='')
      _getMain().entityActionPerformed([Ent.GROUP, group, role, user], j, jcount)
    except (GAPI.groupNotFound, GAPI.domainNotFound, GAPI.domainCannotUseApis, GAPI.invalid):
      _getMain().entityUnknownWarning(Ent.GROUP, group, j, jcount)
    except (GAPI.memberNotFound, GAPI.invalidMember, GAPI.conditionNotMet, GAPI.serviceNotAvailable) as e:
      _getMain().entityActionFailedWarning([Ent.USER, user, Ent.GROUP, group], str(e), j, jcount)
    except (GAPI.forbidden, GAPI.permissionDenied) as e:
      ClientAPIAccessDeniedExit(str(e))
  Ind.Decrement()

# gam <UserTypeEntity> update group|groups
#	[(domain <DomainName>)|(customerid <CustomerID>)]) [<GroupRole>] [[delivery] <DeliverySetting>]
#	([<GroupRole>] [[delivery] <DeliverySetting>] [<GroupEntity>])*
def updateUserGroups(users):
  cd = _getMain().buildGAPIObject(API.DIRECTORY)
  groupKeys = None
  kwargs = _getUserGroupOptionalDomainCustomerId()
  baseRole = _getMain().getChoice(GROUP_ROLES_MAP, defaultChoice=Ent.ROLE_MEMBER, mapChoice=True)
  baseDeliverySettings = _getMain().getDeliverySettings()
  if not kwargs:
    kwargs = {'customer': GC.Values[GC.CUSTOMER_ID]}
    if Cmd.ArgumentsRemaining():
      groupKeys = _getMain().getEntityList(Cmd.OB_GROUP_ENTITY)
      subkeyRoleField = GM.Globals[GM.CSV_SUBKEY_FIELD]
      if not isinstance(groupKeys, dict):
        userGroupLists = None
        updateGroups = {}
        for group in groupKeys:
          updateGroups[_getMain().normalizeEmailAddressOrUID(group)] = {'role': baseRole, 'delivery_settings': baseDeliverySettings}
        while Cmd.ArgumentsRemaining():
          role = _getMain().getChoice(GROUP_ROLES_MAP, defaultChoice=Ent.ROLE_MEMBER, mapChoice=True)
          deliverySettings = _getMain().getDeliverySettings()
          for group in _getMain().getEntityList(Cmd.OB_GROUP_ENTITY):
            updateGroups[_getMain().normalizeEmailAddressOrUID(group)] = {'role': role, 'delivery_settings': deliverySettings}
      else:
        userGroupLists = groupKeys
        _getMain().checkForExtraneousArguments()
  else:
    _getMain().checkForExtraneousArguments()
  i, count, users = _getMain().getEntityArgument(users)
  for user in users:
    i += 1
    origUser = user
    user = _getMain().normalizeEmailAddressOrUID(user)
    if groupKeys is None:
      _setUserGroupArgs(user, kwargs)
      try:
        result = _getMain().callGAPIpages(cd.groups(), 'list', 'groups',
                               throwReasons=GAPI.GROUP_LIST_USERKEY_THROW_REASONS,
                               retryReasons=GAPI.SERVICE_NOT_AVAILABLE_RETRY_REASONS,
                               orderBy='email', fields='nextPageToken,groups(email)', **kwargs)
      except (GAPI.invalidMember, GAPI.invalidInput):
        _getMain().badRequestWarning(Ent.GROUP, Ent.MEMBER, user)
        continue
      except (GAPI.resourceNotFound, GAPI.domainNotFound, GAPI.badRequest):
        accessErrorExit(cd)
      except (GAPI.forbidden, GAPI.permissionDenied) as e:
        ClientAPIAccessDeniedExit(str(e))
      updateGroups = {}
      for group in result:
        updateGroups[group['email']] = {'role': baseRole, 'delivery_settings': baseDeliverySettings}
    elif userGroupLists:
      roleList = [baseRole]
      if not subkeyRoleField:
        groupKeys = userGroupLists[origUser]
      else:
        roleList = userGroupLists[origUser]
      updateGroups = {}
      for role in roleList:
        if subkeyRoleField:
          role, groupKeys = _validateSubkeyRoleGetGroups(user, role, origUser, userGroupLists, i, count)
          if role is None:
            continue
        for group in groupKeys:
          updateGroups[_getMain().normalizeEmailAddressOrUID(group)] = {'role': role, 'delivery_settings': DELIVERY_SETTINGS_UNDEFINED}
    _updateUserGroups(cd, user, set(updateGroups), updateGroups, i, count)

# gam <UserTypeEntity> sync group|groups
#	[(domain <DomainName>)|(customerid <CustomerID>)]
#	[<GroupRole>] [[delivery] <DeliverySetting>] (<GroupEntity>)*
def syncUserWithGroups(users):
  cd = _getMain().buildGAPIObject(API.DIRECTORY)
  kwargs = _getUserGroupOptionalDomainCustomerId()
  if not kwargs:
    kwargs = {'customer': GC.Values[GC.CUSTOMER_ID]}
  baseRole = _getMain().getChoice(GROUP_ROLES_MAP, defaultChoice=Ent.ROLE_MEMBER, mapChoice=True)
  baseDeliverySettings = _getMain().getDeliverySettings()
  groupKeys = _getMain().getEntityList(Cmd.OB_GROUP_ENTITY)
  subkeyRoleField = GM.Globals[GM.CSV_SUBKEY_FIELD]
  if not isinstance(groupKeys, dict):
    userGroupLists = None
    syncGroups = {}
    for group in groupKeys:
      syncGroups[_getMain().normalizeEmailAddressOrUID(group)] = {'role': baseRole, 'delivery_settings': baseDeliverySettings}
    while Cmd.ArgumentsRemaining():
      role = _getMain().getChoice(GROUP_ROLES_MAP, defaultChoice=Ent.ROLE_MEMBER, mapChoice=True)
      deliverySettings = _getMain().getDeliverySettings()
      for group in _getMain().getEntityList(Cmd.OB_GROUP_ENTITY):
        syncGroups[_getMain().normalizeEmailAddressOrUID(group)] = {'role': role, 'delivery_settings': deliverySettings}
  else:
    userGroupLists = groupKeys
    _getMain().checkForExtraneousArguments()
  i, count, users = _getMain().getEntityArgument(users)
  for user in users:
    i += 1
    origUser = user
    user = _getMain().normalizeEmailAddressOrUID(user)
    if userGroupLists:
      roleList = [baseRole]
      if not subkeyRoleField:
        groupKeys = userGroupLists[origUser]
      else:
        roleList = userGroupLists[origUser]
      syncGroups = {}
      for role in roleList:
        if subkeyRoleField:
          role, groupKeys = _validateSubkeyRoleGetGroups(user, role, origUser, userGroupLists, i, count)
          if role is None:
            continue
        for group in groupKeys:
          syncGroups[_getMain().normalizeEmailAddressOrUID(group)] = {'role': role, 'delivery_settings': DELIVERY_SETTINGS_UNDEFINED}
    currGroups = {}
    _setUserGroupArgs(user, kwargs)
    try:
      entityList = _getMain().callGAPIpages(cd.groups(), 'list', 'groups',
                                 throwReasons=GAPI.GROUP_LIST_USERKEY_THROW_REASONS,
                                 retryReasons=GAPI.SERVICE_NOT_AVAILABLE_RETRY_REASONS,
                                 orderBy='email', fields='nextPageToken,groups(email)', **kwargs)
    except (GAPI.invalidMember, GAPI.invalidInput):
      _getMain().badRequestWarning(Ent.GROUP, Ent.MEMBER, user)
      continue
    except (GAPI.resourceNotFound, GAPI.domainNotFound, GAPI.badRequest):
      accessErrorExit(cd)
    except (GAPI.forbidden, GAPI.permissionDenied) as e:
      ClientAPIAccessDeniedExit(str(e))
    for groupEntity in entityList:
      groupEmail = groupEntity['email']
      try:
        result = _getMain().callGAPI(cd.members(), 'get',
                          throwReasons=GAPI.MEMBERS_THROW_REASONS+[GAPI.MEMBER_NOT_FOUND, GAPI.INVALID_MEMBER, GAPI.CONDITION_NOT_MET],
                          retryReasons=GAPI.MEMBERS_RETRY_REASONS,
                          groupKey=groupEmail, memberKey=user, fields='role,delivery_settings')
        currGroups[groupEmail] = {'role': result.get('role', Ent.MEMBER),
                                  'delivery_settings': result.get('delivery_settings', _getMain().DELIVERY_SETTINGS_UNDEFINED)}
      except (GAPI.groupNotFound, GAPI.domainNotFound, GAPI.domainCannotUseApis, GAPI.invalid, GAPI.forbidden):
        _getMain().entityUnknownWarning(Ent.GROUP, groupEmail, i, count)
      except (GAPI.memberNotFound, GAPI.invalidMember, GAPI.conditionNotMet, GAPI.serviceNotAvailable) as e:
        _getMain().entityActionFailedWarning([Ent.USER, user, Ent.GROUP, groupEmail], str(e), i, count)
    currGroupsSet = set(currGroups)
    syncGroupsSet = set(syncGroups)
    removeGroupsSet = currGroupsSet-syncGroupsSet
    addGroupsSet = syncGroupsSet-currGroupsSet
    updateGroupsSet = set()
    for group in currGroupsSet.intersection(syncGroupsSet):
      if (syncGroups[group]['role'] != currGroups[group]['role'] or
          (syncGroups[group]['delivery_settings'] != currGroups[group]['delivery_settings'] and
           syncGroups[group]['delivery_settings'] != _getMain().DELIVERY_SETTINGS_UNDEFINED)):
        updateGroupsSet.add(group)
    if removeGroupsSet or addGroupsSet or updateGroupsSet:
      if removeGroupsSet:
        Act.Set(Act.REMOVE)
        _deleteUserFromGroups(cd, user, removeGroupsSet, currGroups, i, count)
      if addGroupsSet:
        Act.Set(Act.ADD)
        _addUserToGroups(cd, user, addGroupsSet, syncGroups, i, count)
      if updateGroupsSet:
        Act.Set(Act.UPDATE)
        _updateUserGroups(cd, user, updateGroupsSet, syncGroups, i, count)
    else:
      _getMain().printEntityKVList([Ent.USER, user], [Msg.NO_CHANGES], i, count)

def _getUserGroupDomainCustomerId(myarg, kwargs):
  if myarg == 'domain':
    kwargs['domain'] = _getMain().getString(Cmd.OB_DOMAIN_NAME).lower()
    kwargs.pop('customer', None)
  elif myarg == 'customerid':
    kwargs['customer'] = _getMain().getString(Cmd.OB_CUSTOMER_ID)
    kwargs.pop('domain', None)
  else:
    return False
  return True

# gam <UserTypeEntity> check group|groups
#	[roles <GroupRoleList>] [includederivedmembership] [csv] <GroupEntity>
def checkUserInGroups(users):
  def _setCheckError():
    sysRC['sysRC'] = _getMain().CHECK_USER_GROUPS_ERROR_RC

  def _checkMember(result):
    role = result.get('role', Ent.MEMBER)
    if role in rolesSet:
      if not csvPF:
        _getMain().printEntity([Ent.USER, user, Ent.GROUP, groupEmail, Ent.ROLE, role], j, jcount)
      else:
        csvPF.WriteRow({'user': user, 'group': groupEmail, 'role': role})
    else:
      if not csvPF:
        _getMain().entityActionFailedWarning([Ent.USER, user, Ent.GROUP, groupEmail, Ent.ROLE, role], Msg.ROLE_NOT_IN_SET.format(rolesSet), j, jcount)
      else:
        csvPF.WriteRow({'user': user, 'group': groupEmail, 'role': notMemberOrRole})
      _setCheckError()

  cd = _getMain().buildGAPIObject(API.DIRECTORY)
  csvPF = None
  groupKeys = []
  checkGroupsSet = set()
  rolesSet = set()
  includeDerivedMembership = False
  sysRC = {'sysRC' : 0}
  while Cmd.ArgumentsRemaining():
    myarg = _getMain().getArgument()
    if myarg in {'role', 'roles'}:
      for role in _getMain().getString(Cmd.OB_GROUP_ROLE_LIST).lower().replace(',', ' ').split():
        if role in GROUP_ROLES_MAP:
          rolesSet.add(GROUP_ROLES_MAP[role])
        else:
          _getMain().invalidChoiceExit(role, GROUP_ROLES_MAP, True)
    elif myarg == 'includederivedmembership':
      includeDerivedMembership = True
    elif myarg == 'csv':
      csvPF = _getMain().CSVPrintFile(['user', 'group', 'role'])
    else:
      Cmd.Backup()
      groupKeys = _getMain().getEntityList(Cmd.OB_GROUP_ENTITY)
  if not rolesSet:
    rolesSet = _getMain().ALL_GROUP_ROLES
  notMemberOrRole = Msg.NOT_AN_ENTITY.format('|'.join(rolesSet))
  userGroupLists = groupKeys if isinstance(groupKeys, dict) else None
  for group in groupKeys:
    checkGroupsSet.add(_getMain().normalizeEmailAddressOrUID(group))
  i, count, users = _getMain().getEntityArgument(users)
  for user in users:
    i += 1
    origUser = user
    user = _getMain().normalizeEmailAddressOrUID(user)
    if userGroupLists:
      userGroupKeys = userGroupLists[origUser]
      checkGroupsSet = set()
      for group in userGroupKeys:
        checkGroupsSet.add(_getMain().normalizeEmailAddressOrUID(group))
    jcount = len(checkGroupsSet)
    _getMain().entityPerformActionModifierNumItems([Ent.USER, user], Act.MODIFIER_IN, jcount, Ent.GROUP, i, count)
    Ind.Increment()
    j = 0
    for groupEmail in sorted(checkGroupsSet):
      j += 1
      if not includeDerivedMembership:
        try:
          result = _getMain().callGAPI(cd.members(), 'get',
                            throwReasons=GAPI.MEMBERS_THROW_REASONS+[GAPI.MEMBER_NOT_FOUND, GAPI.INVALID_MEMBER, GAPI.CONDITION_NOT_MET],
                            retryReasons=GAPI.MEMBERS_RETRY_REASONS,
                            groupKey=groupEmail, memberKey=user, fields='role')
          _checkMember(result)
        except (GAPI.groupNotFound, GAPI.domainNotFound, GAPI.domainCannotUseApis, GAPI.invalid):
          _getMain().entityUnknownWarning(Ent.GROUP, groupEmail, j, jcount)
          _setCheckError()
        except GAPI.memberNotFound:
          if not csvPF:
            _getMain().entityActionFailedWarning([Ent.USER, user, Ent.GROUP, groupEmail], Msg.NOT_A_MEMBER, j, jcount)
          else:
            csvPF.WriteRow({'user': user, 'group': groupEmail, 'role': notMemberOrRole})
          _setCheckError()
        except (GAPI.invalidMember, GAPI.conditionNotMet, GAPI.serviceNotAvailable) as e:
          _getMain().entityActionFailedWarning([Ent.USER, user, Ent.GROUP, groupEmail], str(e), j, jcount)
          _setCheckError()
        except (GAPI.forbidden, GAPI.permissionDenied) as e:
          ClientAPIAccessDeniedExit(str(e))
      else:
        try:
          result = _getMain().callGAPIpages(cd.members(), 'list', 'members',
                                 throwReasons=GAPI.MEMBERS_THROW_REASONS, retryReasons=GAPI.MEMBERS_RETRY_REASONS,
                                 includeDerivedMembership=includeDerivedMembership,
                                 groupKey=groupEmail, fields='nextPageToken,members(email,role,type)', maxResults=GC.Values[GC.MEMBER_MAX_RESULTS])
          for member in result:
            if member['type'] != Ent.TYPE_USER or member['email'].lower() != user:
              continue
            _checkMember(member)
            break
          else:
            if not csvPF:
              _getMain().entityActionFailedWarning([Ent.USER, user, Ent.GROUP, groupEmail], Msg.NOT_A_MEMBER, j, jcount)
            else:
              csvPF.WriteRow({'user': user, 'group': groupEmail, 'role': notMemberOrRole})
            _setCheckError()
        except (GAPI.groupNotFound, GAPI.domainNotFound, GAPI.domainCannotUseApis, GAPI.invalid):
          _getMain().entityUnknownWarning(Ent.GROUP, groupEmail, j, jcount)
          _setCheckError()
        except (GAPI.invalidMember, GAPI.conditionNotMet, GAPI.serviceNotAvailable) as e:
          _getMain().entityActionFailedWarning([Ent.USER, user, Ent.GROUP, groupEmail], str(e), j, jcount)
          _setCheckError()
        except (GAPI.forbidden, GAPI.permissionDenied) as e:
          ClientAPIAccessDeniedExit(str(e))
    Ind.Decrement()
  if csvPF:
    csvPF.writeCSVfile('User Check Groups')
  _getMain().setSysExitRC(sysRC['sysRC'])

# gam <UserTypeEntity> print groups [todrive <ToDriveAttribute>*]
#	[(domain <DomainName>)|(customerid <CustomerID>)]
#	[roles <GroupRoleList>] [countsonly|totalonly|nodetails]
# gam <UserTypeEntity> show groups
#	[(domain <DomainName>)|(customerid <CustomerID>)]
#	[roles <GroupRoleList>] [countsonly|totalonly|nodetails]
def printShowUserGroups(users):
  cd = _getMain().buildGAPIObject(API.DIRECTORY)
  kwargs = {'customer': GC.Values[GC.CUSTOMER_ID]}
  csvPF = _getMain().CSVPrintFile(['User', 'Group', 'Role', 'Status', 'Delivery'], 'sortall') if Act.csvFormat() else None
  rolesSet = set()
  countsOnly = noDetails = totalOnly = False
  while Cmd.ArgumentsRemaining():
    myarg = _getMain().getArgument()
    if csvPF and myarg == 'todrive':
      csvPF.GetTodriveParameters()
    elif _getUserGroupDomainCustomerId(myarg, kwargs):
      pass
    elif myarg in {'role', 'roles'}:
      for role in _getMain().getString(Cmd.OB_GROUP_ROLE_LIST).lower().replace(',', ' ').split():
        if role in GROUP_ROLES_MAP:
          rolesSet.add(GROUP_ROLES_MAP[role])
        else:
          _getMain().invalidChoiceExit(role, GROUP_ROLES_MAP, True)
    elif myarg == 'countsonly':
      countsOnly = True
    elif myarg == 'totalonly':
      countsOnly = totalOnly = True
    elif myarg == 'nodetails':
      noDetails = True
    else:
      _getMain().unknownArgumentExit()
  if not rolesSet:
    rolesSet = _getMain().ALL_GROUP_ROLES
  allRoles = rolesSet == _getMain().ALL_GROUP_ROLES
  if noDetails:
    if csvPF:
      titles = ['User', 'Group']
      csvPF.SetTitles(titles)
      csvPF.SetSortTitles([])
  elif countsOnly:
    zeroCounts = {'User': None, 'Total': 0}
    if not totalOnly:
      for role in [Ent.ROLE_MEMBER, Ent.ROLE_MANAGER, Ent.ROLE_OWNER]:
        if role in rolesSet:
          zeroCounts[role] = 0
    if csvPF:
      titles = ['User', 'Total']
      if not totalOnly:
        for role in [Ent.ROLE_MEMBER, Ent.ROLE_MANAGER, Ent.ROLE_OWNER]:
          if role in rolesSet:
            titles.append(role)
      csvPF.SetTitles(titles)
      csvPF.SetSortTitles([])
  i, count, users = _getMain().getEntityArgument(users)
  for user in users:
    i += 1
    user = _getMain().normalizeEmailAddressOrUID(user)
    if csvPF:
      _getMain().printGettingAllEntityItemsForWhom(Ent.GROUP, user, i, count)
      pageMessage = _getMain().getPageMessageForWhom()
    else:
      pageMessage = None
    _setUserGroupArgs(user, kwargs)
    try:
      entityList = _getMain().callGAPIpages(cd.groups(), 'list', 'groups',
                                 pageMessage=pageMessage,
                                 throwReasons=GAPI.GROUP_LIST_USERKEY_THROW_REASONS,
                                 retryReasons=GAPI.SERVICE_NOT_AVAILABLE_RETRY_REASONS,
                                 orderBy='email', fields='nextPageToken,groups(email)', **kwargs)
    except (GAPI.invalidMember, GAPI.invalidInput):
      _getMain().badRequestWarning(Ent.GROUP, Ent.MEMBER, user)
      continue
    except (GAPI.resourceNotFound, GAPI.domainNotFound, GAPI.badRequest):
      if kwargs.get('domain'):
        _getMain().badRequestWarning(Ent.GROUP, Ent.DOMAIN, kwargs['domain'])
        return
      accessErrorExit(cd)
    except (GAPI.forbidden, GAPI.permissionDenied) as e:
      ClientAPIAccessDeniedExit(str(e))
    jcount = len(entityList)
    if totalOnly:
      if not csvPF:
        _getMain().printEntityKVList([Ent.USER, user], ['Total', jcount])
      else:
        csvPF.WriteRow({'User': user, 'Total': jcount})
      continue
    if not csvPF:
      if allRoles:
        _getMain().entityPerformActionNumItems([Ent.USER, user], jcount, Ent.GROUP, i, count)
      else:
        _getMain().entityPerformActionModifierNumItems([Ent.USER, user], Msg.MAXIMUM_OF, jcount, Ent.GROUP, i, count)
    elif jcount == 0 and GC.Values[GC.CSV_OUTPUT_USERS_AUDIT]:
      csvPF.WriteRowNoFilter({'User': user})
      continue
    if noDetails:
      Ind.Increment()
      j = 0
      for groupEntity in entityList:
        j += 1
        groupEmail = groupEntity['email']
        if not csvPF:
          _getMain().printEntity([Ent.GROUP, groupEmail], j, jcount)
        else:
          csvPF.WriteRow({'User': user, 'Group': groupEmail})
      Ind.Decrement()
      continue
    if countsOnly:
      userCounts = zeroCounts.copy()
      userCounts['User'] = user
    Ind.Increment()
    j = 0
    for groupEntity in entityList:
      j += 1
      groupEmail = groupEntity['email']
      try:
        result = _getMain().callGAPI(cd.members(), 'get',
                          throwReasons=GAPI.MEMBERS_THROW_REASONS+[GAPI.MEMBER_NOT_FOUND, GAPI.INVALID_MEMBER, GAPI.CONDITION_NOT_MET],
                          retryReasons=GAPI.MEMBERS_RETRY_REASONS,
                          groupKey=groupEmail, memberKey=user, fields='role,status,delivery_settings')
        role = result.get('role', Ent.MEMBER)
        status = result.get('status', 'UNKNOWN')
        delivery_settings = result.get('delivery_settings', '')
        if role in rolesSet:
          if countsOnly:
            userCounts[role] += 1
          elif not csvPF:
            _getMain().printEntity([Ent.GROUP, groupEmail, Ent.ROLE, role, Ent.STATUS, status, Ent.DELIVERY, delivery_settings], j, jcount)
          else:
            csvPF.WriteRow({'User': user, 'Group': groupEmail, 'Role': role, 'Status': status, 'Delivery': delivery_settings})
      except (GAPI.groupNotFound, GAPI.domainNotFound, GAPI.domainCannotUseApis, GAPI.invalid, GAPI.forbidden):
        _getMain().entityUnknownWarning(Ent.GROUP, groupEmail, j, jcount)
      except (GAPI.memberNotFound, GAPI.invalidMember, GAPI.conditionNotMet, GAPI.serviceNotAvailable) as e:
        _getMain().entityActionFailedWarning([Ent.USER, user, Ent.GROUP, groupEmail], str(e), j, jcount)
    if countsOnly:
      for role in [Ent.ROLE_MEMBER, Ent.ROLE_MANAGER, Ent.ROLE_OWNER]:
        if role in rolesSet:
          userCounts['Total'] += userCounts[role]
      if not csvPF:
        kvList = ['Total', userCounts['Total']]
        for role in [Ent.ROLE_MEMBER, Ent.ROLE_MANAGER, Ent.ROLE_OWNER]:
          if role in rolesSet:
            kvList.extend([role, userCounts[role]])
        _getMain().printEntityKVList([Ent.USER, user], kvList)
      else:
        csvPF.WriteRow(userCounts)
    Ind.Decrement()
  if csvPF:
    csvPF.writeCSVfile('User Groups')

# gam <UserTypeEntity> print grouptree [todrive <ToDriveAttribute>*]
#	[(domain <DomainName>)|(customerid <CustomerID>)]
#	[roles <GroupRoleList>]
#	[showparentsaslist [<Boolean>]] [delimiter <Character>]
#	[formatjson [quotechar <Character>]]
# gam <UserTypeEntity> show grouptree
#	[(domain <DomainName>)|(customerid <CustomerID>)]
#	[roles <GroupRoleList>]
#	[formatjson]
def printShowGroupTree(users):
  cd = _getMain().buildGAPIObject(API.DIRECTORY)
  kwargs = {'customer': GC.Values[GC.CUSTOMER_ID]}
  csvPF = _getMain().CSVPrintFile(['User', 'Group', 'Name']) if Act.csvFormat() else None
  FJQC = _getMain().FormatJSONQuoteChar(csvPF)
  delimiter = GC.Values[GC.CSV_OUTPUT_FIELD_DELIMITER]
  showParentsAsList = False
  rolesSet = set()
  while Cmd.ArgumentsRemaining():
    myarg = _getMain().getArgument()
    if csvPF and myarg == 'todrive':
      csvPF.GetTodriveParameters()
    elif _getUserGroupDomainCustomerId(myarg, kwargs):
      pass
    elif myarg in {'role', 'roles'}:
      for role in _getMain().getString(Cmd.OB_GROUP_ROLE_LIST).lower().replace(',', ' ').split():
        if role in GROUP_ROLES_MAP:
          rolesSet.add(GROUP_ROLES_MAP[role])
        else:
          _getMain().invalidChoiceExit(role, GROUP_ROLES_MAP, True)
    elif csvPF and myarg == 'delimiter':
      delimiter = _getMain().getCharacter()
    elif csvPF and myarg == 'showparentsaslist':
      showParentsAsList = _getMain().getBoolean()
    else:
      FJQC.GetFormatJSONQuoteChar(myarg, False)
  if csvPF:
    if rolesSet:
      csvPF.AddTitles('Role')
    if not FJQC.formatJSON:
      if not showParentsAsList:
        csvPF.SetIndexedTitles(['parents'])
      else:
        csvPF.AddTitles(['ParentsCount', 'Parents', 'ParentsName'])
    else:
      if rolesSet:
        csvPF.AddJSONTitles('Role')
      csvPF.AddJSONTitles('JSON')
  allRoles = rolesSet == _getMain().ALL_GROUP_ROLES
  groupParents = {}
  i, count, users = _getMain().getEntityArgument(users)
  for user in users:
    i += 1
    user = _getMain().normalizeEmailAddressOrUID(user)
    _setUserGroupArgs(user, kwargs)
    try:
      groups = _getMain().callGAPIpages(cd.groups(), 'list', 'groups',
                             throwReasons=GAPI.GROUP_LIST_USERKEY_THROW_REASONS,
                             retryReasons=GAPI.SERVICE_NOT_AVAILABLE_RETRY_REASONS,
                             orderBy='email', fields='nextPageToken,groups(email,name)', **kwargs)
    except (GAPI.invalidMember, GAPI.invalidInput):
      _getMain().entityUnknownWarning(Ent.USER, user, i, count)
      continue
    except (GAPI.forbidden, GAPI.permissionDenied) as e:
      ClientAPIAccessDeniedExit(str(e))
    j = 0
    jcount = len(groups)
    if not csvPF and not FJQC.formatJSON:
      if allRoles:
        _getMain().entityPerformActionNumItems([Ent.USER, user], jcount, Ent.GROUP_TREE, i, count)
      else:
        _getMain().entityPerformActionModifierNumItems([Ent.USER, user], Msg.MAXIMUM_OF, jcount, Ent.GROUP_TREE, i, count)
    Ind.Increment()
    for group in groups:
      j += 1
      groupEmail = group['email']
      if groupEmail not in groupParents:
        _getMain().getGroupParents(cd, groupParents, groupEmail, group['name'], kwargs)
      if rolesSet:
        try:
          result = _getMain().callGAPI(cd.members(), 'get',
                            throwReasons=GAPI.MEMBERS_THROW_REASONS+[GAPI.MEMBER_NOT_FOUND, GAPI.INVALID_MEMBER, GAPI.CONDITION_NOT_MET],
                            retryReasons=GAPI.MEMBERS_RETRY_REASONS,
                            groupKey=groupEmail, memberKey=user, fields='role')
          role = result.get('role', Ent.MEMBER)
          if role not in rolesSet:
            continue
        except (GAPI.groupNotFound, GAPI.domainNotFound, GAPI.domainCannotUseApis, GAPI.invalid, GAPI.forbidden):
          _getMain().entityUnknownWarning(Ent.GROUP, groupEmail, j, jcount)
          continue
        except (GAPI.memberNotFound, GAPI.invalidMember, GAPI.conditionNotMet, GAPI.serviceNotAvailable) as e:
          _getMain().entityActionFailedWarning([Ent.USER, user, Ent.GROUP, groupEmail], str(e), j, jcount)
          continue
      else:
        role = None
      if not FJQC.formatJSON:
        if not csvPF:
          _getMain().showGroupParents(groupParents, groupEmail, role, j, jcount)
        else:
          row = {'User': user, 'Group': groupEmail, 'Name': group['name'], 'parents': []}
          if role is not None:
            row['Role'] = role
          _getMain().printGroupParents(groupParents, groupEmail, row, csvPF, delimiter, showParentsAsList)
      else:
        groupInfo = {'email': groupEmail, 'name': group['name'], 'parents': []}
        if role is not None:
          groupInfo['role'] = role
        _getMain().addJsonGroupParents(groupParents, groupInfo, groupEmail)
        if not csvPF:
          _getMain().printLine(json.dumps(_getMain().cleanJSON(groupInfo), ensure_ascii=False, sort_keys=True))
        else:
          row = _getMain().flattenJSON(groupInfo)
          if csvPF.CheckRowTitles(row):
            row = {'User': user, 'Group': groupEmail, 'Name': group['name']}
            if rolesSet:
              row['Role'] = role
            row['JSON'] = json.dumps(_getMain().cleanJSON(groupInfo), ensure_ascii=False, sort_keys=True)
            csvPF.WriteRowNoFilter(row)
    Ind.Decrement()
  if csvPF:
    csvPF.writeCSVfile('User Group Trees')

# gam <UserTypeEntity> print groupslist [todrive <ToDriveAttribute>*]
#	[(domain <DomainName>)|(customerid <CustomerID>)]
#	[delimiter <Character>] [quotechar <Character>]
def printUserGroupsList(users):
  cd = _getMain().buildGAPIObject(API.DIRECTORY)
  kwargs = {'customer': GC.Values[GC.CUSTOMER_ID]}
  csvPF = _getMain().CSVPrintFile(['User', 'Groups', 'GroupsList'])
  FJQC = _getMain().FormatJSONQuoteChar(csvPF)
  delimiter = GC.Values[GC.CSV_OUTPUT_FIELD_DELIMITER]
  while Cmd.ArgumentsRemaining():
    myarg = _getMain().getArgument()
    if myarg == 'todrive':
      csvPF.GetTodriveParameters()
    elif _getUserGroupDomainCustomerId(myarg, kwargs):
      pass
    elif myarg == 'delimiter':
      delimiter = _getMain().getCharacter()
    else:
      FJQC.GetQuoteChar(myarg)
  i, count, users = _getMain().getEntityArgument(users)
  for user in users:
    i += 1
    user = _getMain().normalizeEmailAddressOrUID(user)
    _getMain().printGettingAllEntityItemsForWhom(Ent.GROUP, user, i, count)
    _setUserGroupArgs(user, kwargs)
    try:
      entityList = _getMain().callGAPIpages(cd.groups(), 'list', 'groups',
                                 pageMessage=_getMain().getPageMessageForWhom(),
                                 throwReasons=GAPI.GROUP_LIST_USERKEY_THROW_REASONS,
                                 retryReasons=GAPI.SERVICE_NOT_AVAILABLE_RETRY_REASONS,
                                 orderBy='email', fields='nextPageToken,groups(email)', **kwargs)
    except (GAPI.invalidMember, GAPI.invalidInput):
      _getMain().badRequestWarning(Ent.GROUP, Ent.MEMBER, user)
      continue
    except (GAPI.resourceNotFound, GAPI.domainNotFound, GAPI.badRequest):
      if kwargs.get('domain'):
        _getMain().badRequestWarning(Ent.GROUP, Ent.DOMAIN, kwargs['domain'])
        return
      accessErrorExit(cd)
    except (GAPI.forbidden, GAPI.permissionDenied) as e:
      ClientAPIAccessDeniedExit(str(e))
    csvPF.WriteRow({'User': user, 'Groups': len(entityList), 'GroupsList': delimiter.join([group['email'] for group in entityList])})
  csvPF.writeCSVfile('User GroupsList')

# License command utilities
LICENSE_PRODUCT_SKUIDS = 'productSkuIds'
LICENSE_PREVIEW_TITLES = ['user', 'productId', 'skuId', 'action', 'message']

