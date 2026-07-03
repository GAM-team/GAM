"""Chat members, messages, reactions, and events.

Part of the _chat_tmp sub-package."""

"""GAM Google Chat management."""

import uuid

from gamlib import glaction
from gamlib import glapi as API
from gamlib import glcfg as GC
from gamlib import glclargs
from gamlib import glentity
from gamlib import glgapi as GAPI
from gamlib import glglobals as GM
from gamlib import glindent
from gamlib import glmsgs as Msg
from gam.util.api import _getAdminEmail, buildGAPIObject, callGAPI, callGAPIpages
from gam.util.args import (
    AND_OR_CONJUNCTION_MAP,
    OrderBy,
    SORF_TEXT_ARGUMENTS,
    StartEndTime,
    getAddCSVData,
    getArgument,
    getBoolean,
    getChoice,
    getEmailAddress,
    getString,
    getStringOrFile,
    normalizeEmailAddressOrUID,
    substituteQueryTimes,
)
from gam.util.csv_pf import (
    CSVPrintFile,
    FormatJSONQuoteChar,
    getFieldsFromFieldsList,
    getFieldsList,
    getItemFieldsFromFieldsList,
)
from gam.util.display import (
    entityActionFailedWarning,
    entityActionPerformed,
    entityPerformAction,
    entityPerformActionNumItems,
    userChatServiceNotEnabledWarning,
)
from gam.util.entity import (
    convertEmailAddressToUID,
    convertUIDtoEmailAddressWithType,
    getEntityArgument,
    getEntityList,
    getEntityToModify,
    getNormalizedEmailAddressEntity,
)
from gam.util.errors import missingArgumentExit, unknownArgumentExit, usageErrorExit
from gam.util.output import stderrWarningMsg, writeStdout

Act = glaction.GamAction()
Ent = glentity.GamEntity()
Ind = glindent.GamIndent()
Cmd = glclargs.GamCLArgs()


def _getChatMemberEmail(cd, member):
  if 'member' in member:
    if member['member']['type'] == 'HUMAN':
      _, memberUid = member['member']['name'].split('/')
      member['member']['email'], _ = convertUIDtoEmailAddressWithType(f'uid:{memberUid}', cd, None, emailTypes=['user'])
      if member['member']['email'].find('@') == -1:
        member['member']['email'] = 'id:'+member['member']['email']
  elif 'groupMember' in member:
    _, memberUid = member['groupMember']['name'].split('/')
    member['groupMember']['email'], _ = convertUIDtoEmailAddressWithType(f'uid:{memberUid}', cd, None, emailTypes=['group'])

def _getChatSpaceMembers(cd, chatSpace, ciGroupName):
  if chatSpace.startswith('space/'):
    _, chatSpace = chatSpace.split('/', 1)
    chatSpace = 'spaces/'+chatSpace
  kwargsUAA = {'useAdminAccess': True, 'filter': 'member.type != "BOT"'}
  user, chat, kvList = buildChatServiceObject(API.CHAT_MEMBERSHIPS_ADMIN, _getAdminEmail(), 0, 0, [Ent.CHAT_SPACE, chatSpace], True)
  memberList = []
  if not chat:
    return memberList
  fields = getItemFieldsFromFieldsList('memberships', [])
  qfilter = f'{Ent.Singular(Ent.CHAT_SPACE)}: {chatSpace}, {kwargsUAA["filter"]}'
  try:
    members = callGAPIpages(chat.spaces().members(), 'list', 'memberships',
                            pageMessage=_getChatPageMessage(Ent.CHAT_MEMBER, user, 0, 0, qfilter),
                            throwReasons=[GAPI.NOT_FOUND, GAPI.INVALID_ARGUMENT, GAPI.PERMISSION_DENIED],
                            retryReasons=GAPI.SERVICE_NOT_AVAILABLE_RETRY_REASONS,
                            parent=chatSpace, fields=fields, pageSize=GC.Values[GC.CHAT_MAX_RESULTS], **kwargsUAA)
    for member in members:
      _getChatMemberEmail(cd, member)
      gmember = {}
      if 'member' in member:
        if member['member']['type'] == 'HUMAN':
          _, memberUid = member['member']['name'].split('/')
          gmember['type'] = Ent.TYPE_USER
          email, _ = convertUIDtoEmailAddressWithType(f'uid:{memberUid}', cd, None, emailTypes=['user'])
          role = Ent.ROLE_MANAGER if member['role'] == 'ROLE_MANAGER' else Ent.ROLE_MEMBER
          if not ciGroupName:
            gmember['id'] = memberUid
            gmember['email'] = email
            gmember['role'] = role
            gmember['status'] = member['state']
          else:
            gmember['name'] = f'{ciGroupName}/memberships/{memberUid}'
            gmember['preferredMemberKey'] = {'id': email}
            gmember['roles'] = [{'name': role}]
            gmember['createTime'] = member['createTime']
          memberList.append(gmember)
      elif 'groupMember' in member:
        _, memberUid = member['groupMember']['name'].split('/')
        gmember['type'] = Ent.TYPE_GROUP
        role = Ent.ROLE_MANAGER if member['role'] == 'ROLE_MANAGER' else Ent.ROLE_MEMBER
        email, _ = convertUIDtoEmailAddressWithType(f'uid:{memberUid}', cd, None, emailTypes=['group'])
        if not ciGroupName:
          gmember['id'] = memberUid
          gmember['email'] = email
          gmember['role'] = role
          gmember['status'] = member['state']
        else:
          gmember['name'] = f'{ciGroupName}/memberships/{memberUid}'
          gmember['preferredMemberKey'] = {'id': email}
          gmember['roles'] = [{'name': role}]
          gmember['createTime'] = member['createTime']
        memberList.append(gmember)
    return memberList
  except (GAPI.notFound, GAPI.invalidArgument, GAPI.permissionDenied) as e:
    exitIfChatNotConfigured(chat, kvList, str(e), 0, 0)
    return memberList

def normalizeUserMember(user, userList):
  userList.append(normalizeEmailAddressOrUID(user))

def getUserMemberID(cd, user, userList):
  userList.append(convertEmailAddressToUID(user, cd, emailType='user'))

def getGroupMemberID(cd, group, groupList):
  groupList.append(convertEmailAddressToUID(group, cd, emailType='group'))

# gam <UserTypeEntity> create chatmember <ChatSpace>
#	[type human|bot] [role member|manager|owner]
#	(user <UserItem>)* (members <UserTypeEntity>)*
#	(group <GroupItem>)* (groups <GroupEntity>)*
#	[formatjson|returnidonly]
# gam <UserItem> create chatmember asadmin <ChatSpace>
#	[type human|bot] [role member|manager|owner]
#	(user <UserItem>)* (members <UserTypeEntity>)*
#	(group <GroupItem>)* (groups <GroupEntity>)*
#	[formatjson|returnidonly]
def createChatMember(users):
  def addMembers(members, field, entityType, i, count):
    jcount = len(members)
    entityPerformActionNumItems(kvList, jcount, entityType, i, count)
    if jcount == 0:
      return
    kvList.extend([entityType, ''])
    Ind.Increment()
    j = 0
    for body in members:
      j += 1
      kvList[-1] = body[field]['name']
      try:
        member = callGAPI(chat.spaces().members(), 'create',
                          bailOnInternalError=True,
                          throwReasons=[GAPI.ALREADY_EXISTS, GAPI.NOT_FOUND, GAPI.INVALID, GAPI.INVALID_ARGUMENT,
                                        GAPI.INTERNAL_ERROR, GAPI.PERMISSION_DENIED, GAPI.FAILED_PRECONDITION],
                          parent=parent, body=body, **kwargsUAA)
        if role != 'ROLE_MEMBER' and entityType in (Ent.CHAT_MANAGER_USER, Ent.CHAT_OWNER_USER):
          member = callGAPI(chat.spaces().members(), 'patch',
                            bailOnInternalError=True,
                            throwReasons=[GAPI.NOT_FOUND, GAPI.INVALID_ARGUMENT, GAPI.INTERNAL_ERROR,
                                          GAPI.PERMISSION_DENIED, GAPI.FAILED_PRECONDITION],
                            name=member['name'], updateMask='role', body={'role': role}, **kwargsUAA)
        if not returnIdOnly:
          kvList[-1] = member['name']
          _getChatMemberEmail(cd, member)
          if not FJQC.formatJSON:
            entityActionPerformed(kvList, j, jcount)
          Ind.Increment()
          _showChatItem(member, Ent.CHAT_MEMBER, FJQC)
          Ind.Decrement()
        else:
          writeStdout(f'{member["name"]}\n')
      except (GAPI.alreadyExists, GAPI.notFound, GAPI.invalid, GAPI.invalidArgument, GAPI.permissionDenied, GAPI.internalError) as e:
        entityActionFailedWarning(kvList, str(e))
      except GAPI.failedPrecondition:
        userChatServiceNotEnabledWarning(user, i, count)
  Ind.Decrement()

  cd = buildGAPIObject(API.DIRECTORY)
  FJQC = FormatJSONQuoteChar()
  parent = None
  role = CHAT_MEMBER_ROLE_MAP['member']
  mtype = CHAT_MEMBER_TYPE_MAP['human']
  userList = []
  groupList = []
  returnIdOnly = False
  useAdminAccess, api, kwargsUAA = _getChatAdminAccess(API.CHAT_MEMBERSHIPS_ADMIN, API.CHAT_MEMBERSHIPS)
  while Cmd.ArgumentsRemaining():
    myarg = getArgument()
    if myarg == 'space' or myarg.startswith('spaces/') or myarg.startswith('space/'):
      parent = getSpaceName(myarg)
    elif myarg == 'user':
      normalizeUserMember(getEmailAddress(returnUIDprefix='uid:'), userList)
    elif myarg in {'member', 'members'}:
      _, members = getEntityToModify(defaultEntityType=Cmd.ENTITY_USERS)
      for user in members:
        normalizeUserMember(user, userList)
    elif myarg == 'group':
      getGroupMemberID(cd, getEmailAddress(returnUIDprefix='uid:'), groupList)
    elif myarg == 'groups':
      for group in getEntityList(Cmd.OB_GROUP_ENTITY):
        getGroupMemberID(cd, group, groupList)
    elif myarg == 'role':
      role = getChoice(CHAT_MEMBER_ROLE_MAP, mapChoice=True)
    elif myarg == 'type':
      mtype = getChoice(CHAT_MEMBER_TYPE_MAP, mapChoice=True)
    elif myarg == 'returnidonly':
      returnIdOnly = True
    else:
      FJQC.GetFormatJSON(myarg)
  if not parent:
    missingArgumentExit('space')
  if not userList and not groupList:
    missingArgumentExit('user|members|group|groups')
  userEntityType = CHAT_ROLE_ENTITY_TYPE_MAP[role]
  userMembers = []
  for user in userList:
    userMembers.append({'member': {'name': f'users/{user}', 'type': mtype}})
  groupMembers = []
  for group in groupList:
    groupMembers.append({'groupMember': {'name': f'groups/{group}'}})
  i, count, users = getEntityArgument(users)
  if useAdminAccess:
    _chkChatAdminAccess(count)
  for user in users:
    i += 1
    user, chat, kvList = buildChatServiceObject(api, user, i, count, [Ent.CHAT_SPACE, parent], useAdminAccess)
    if not chat:
      continue
    Ind.Increment()
    if userMembers:
      addMembers(userMembers, 'member', userEntityType, i, count)
    if groupMembers:
      addMembers(groupMembers, 'groupMember', Ent.CHAT_MEMBER_GROUP, i, count)
    Ind.Decrement()

def _deleteChatMembers(chat, kvList, jcount, memberNames, i, count, kwargsUAA):
  j = 0
  for name in memberNames:
    j += 1
    kvList[-1] = name
    try:
      callGAPI(chat.spaces().members(), 'delete',
               bailOnInternalError=True,
               throwReasons=[GAPI.NOT_FOUND, GAPI.INVALID_ARGUMENT, GAPI.PERMISSION_DENIED, GAPI.INTERNAL_ERROR],
               name=name, **kwargsUAA)
      entityActionPerformed(kvList, j, jcount)
    except GAPI.notFound as e:
      entityActionFailedWarning(kvList, str(e), j, jcount)
    except (GAPI.invalidArgument, GAPI.permissionDenied, GAPI.internalError) as e:
      exitIfChatNotConfigured(chat, kvList, str(e), i, count)

# gam <UserTypeEntity> delete chatmember <ChatSpace>
#	((user <UserItem>)|(members <UserTypeEntity>)|
#	 (group <GroupItem>)|(groups <GroupEntity>))+
# gam <UserItem> delete chatmember asadmin <ChatSpace>
#	((user <UserItem>)|(members <UserTypeEntity>)|
#	 (group <GroupItem>)|(groups <GroupEntity>))+
# gam <UserTypeEntity> remove chatmember
#	members <ChatMemberList>
# gam <UserItem> remove chatmember asadmin
#	members <ChatMemberList>
# gam <UserTypeEntity> update chatmember <ChatSpace>
#	role member|manager|owner
#	((user <UserItem>)|(members <UserTypeEntity>))+
# gam <UserTypeEntity> modify chatmember
#	role member|manager|owner
#	members <ChatMemberList>
# gam <UserItem> update chatmember asadmin<ChatSpace>
#	role member|manager|owner
#	((user <UserItem>)|(members <UserTypeEntity>))+
# gam <UserItem> modify chatmember asadmin
#	role member|manager|owner
#	members <ChatMemberList>
def deleteUpdateChatMember(users):
  cd = buildGAPIObject(API.DIRECTORY)
  FJQC = FormatJSONQuoteChar()
  action = Act.Get()
  deleteMode =  action in {Act.DELETE, Act.REMOVE}
  parent = None
  body = {}
  memberNames = []
  userList = []
  groupList = []
  useAdminAccess, api, kwargsUAA = _getChatAdminAccess(API.CHAT_MEMBERSHIPS_ADMIN, API.CHAT_MEMBERSHIPS)
  while Cmd.ArgumentsRemaining():
    myarg = getArgument()
    if action in {Act.UPDATE, Act.MODIFY} and myarg == 'role':
      body['role'] = getChoice(CHAT_MEMBER_ROLE_MAP, mapChoice=True)
      continue
    if action in {Act.REMOVE, Act.MODIFY}:
      if myarg in {'member', 'members'}:
        memberNames.extend(getString(Cmd.OB_CHAT_MEMBER).replace(',', ' ').split())
      else:
        unknownArgumentExit()
    else: # {Act.DELETE, Act.UPDATE}
      if myarg == 'space' or myarg.startswith('spaces/') or myarg.startswith('space/'):
        parent = getSpaceName(myarg)
      elif myarg == 'user':
        normalizeUserMember(getEmailAddress(returnUIDprefix='uid:'), userList)
      elif myarg in {'member', 'members'}:
        _, members = getEntityToModify(defaultEntityType=Cmd.ENTITY_USERS)
        for user in members:
          normalizeUserMember(user, userList)
      elif deleteMode and myarg == 'group':
        getGroupMemberID(cd, getEmailAddress(returnUIDprefix='uid:'), groupList)
      elif deleteMode and myarg == 'groups':
        for group in getEntityList(Cmd.OB_GROUP_ENTITY):
          getGroupMemberID(cd, group, groupList)
      else:
        unknownArgumentExit()
  if not deleteMode and 'role' not in body:
    missingArgumentExit('role')
  if action in {Act.REMOVE, Act.MODIFY}:
    if not memberNames:
      missingArgumentExit('members')
  else: # {Act.DELETE, Act.UPDATE}
    if not parent:
      missingArgumentExit('space')
    if not userList and not groupList:
      missingArgumentExit('user|members|group|groups')
    for user in userList:
      memberNames.append(f'{parent}/members/{user}')
    for group in groupList:
      memberNames.append(f'{parent}/members/group-{group}')
  i, count, users = getEntityArgument(users)
  if useAdminAccess:
    _chkChatAdminAccess(count)
  for user in users:
    i += 1
    user, chat, kvList = buildChatServiceObject(api, user, i, count, [Ent.CHAT_SPACE, parent] if parent is not None else None, useAdminAccess)
    if not chat:
      continue
    jcount = len(memberNames)
    entityPerformActionNumItems(kvList, jcount, Ent.CHAT_MEMBER, i, count)
    kvList.extend([Ent.CHAT_MEMBER, ''])
    Ind.Increment()
    if deleteMode:
      _deleteChatMembers(chat, kvList, jcount, memberNames, i, count, kwargsUAA)
    else:
      j = 0
      for name in memberNames:
        j += 1
        kvList[-1] = name
        try:
          member = callGAPI(chat.spaces().members(), 'patch',
                            bailOnInternalError=True,
                            throwReasons=[GAPI.NOT_FOUND, GAPI.INVALID_ARGUMENT, GAPI.INTERNAL_ERROR,
                                          GAPI.PERMISSION_DENIED, GAPI.FAILED_PRECONDITION],
                            name=name, updateMask='role', body=body, **kwargsUAA)
          _getChatMemberEmail(cd, member)
          Ind.Increment()
          _showChatItem(member, Ent.CHAT_MEMBER, FJQC, j, jcount)
          Ind.Decrement()
        except GAPI.notFound as e:
          entityActionFailedWarning(kvList, str(e), j, jcount)
        except (GAPI.invalidArgument, GAPI.permissionDenied, GAPI.internalError) as e:
          exitIfChatNotConfigured(chat, kvList, str(e), i, count)
        except GAPI.failedPrecondition:
          userChatServiceNotEnabledWarning(user, i, count)
          continue
    Ind.Decrement()

CHAT_SYNC_PREVIEW_TITLES = ['space', 'member', 'role', 'action', 'message']

# gam <UserTypeEntity> sync chatmembers [asadmin] <ChatSpace>
#	[role member|manager|owner] [type human|bot]
#	[addonly|removeonly]
#	[preview [actioncsv]]
#	(users <UserTypeEntity>)* (groups <GroupEntity>)*
def syncChatMembers(users):
  def _previewAction(members, entityType, jcount, action):
    Ind.Increment()
    j = 0
    for member in members:
      j += 1
      entityActionPerformed([Ent.CHAT_SPACE, parent, entityType, member, Ent.ROLE, role], j, jcount)
    Ind.Decrement()
    if csvPF:
      for member in members:
        csvPF.WriteRow({'space': parent, 'member': member, 'role': role, 'action': Act.PerformedName(action), 'message': Act.PREVIEW})

  def addMembers(memberNames, members, entityType, i, count):
    jcount = len(memberNames)
    entityPerformActionNumItems(kvList, jcount, entityType, i, count)
    if jcount == 0:
      return
    if preview:
      _previewAction(memberNames, entityType, jcount, Act.REMOVE)
      return
    kvList.extend([entityType, ''])
    Ind.Increment()
    j = 0
    for memberName in memberNames:
      j += 1
      body = members[memberName]
      kvList[-1] = memberName
      try:
        callGAPI(chat.spaces().members(), 'create',
                 bailOnInternalError=True,
                 throwReasons=[GAPI.ALREADY_EXISTS, GAPI.NOT_FOUND, GAPI.INVALID, GAPI.INVALID_ARGUMENT, GAPI.PERMISSION_DENIED, GAPI.INTERNAL_ERROR],
                 parent=parent, body=body, **kwargsUAA)
        if role != 'ROLE_MEMBER' and entityType == Ent.CHAT_MANAGER_USER:
          callGAPI(chat.spaces().members(), 'patch',
                   bailOnInternalError=True,
                   throwReasons=[GAPI.NOT_FOUND, GAPI.INVALID_ARGUMENT, GAPI.PERMISSION_DENIED, GAPI.INTERNAL_ERROR],
                   name=memberName, updateMask='role', body={'role': role}, **kwargsUAA)
        entityActionPerformed(kvList, j, jcount)
      except (GAPI.alreadyExists, GAPI.notFound, GAPI.invalid, GAPI.invalidArgument, GAPI.permissionDenied, GAPI.internalError) as e:
        entityActionFailedWarning(kvList, str(e), j, jcount)
    Ind.Decrement()
    del kvList[-2:]

  def deleteMembers(memberNames, entityType, i, count):
    jcount = len(memberNames)
    entityPerformActionNumItems(kvList, jcount, entityType, i, count)
    if jcount == 0:
      return
    if preview:
      _previewAction(memberNames, entityType, jcount, Act.ADD)
      return
    kvList.extend([entityType, ''])
    Ind.Increment()
    _deleteChatMembers(chat, kvList, jcount, memberNames, i, count, kwargsUAA)
    Ind.Decrement()
    del kvList[-2:]

  useAdminAccess, api, kwargsUAA = _getChatAdminAccess(API.CHAT_MEMBERSHIPS_ADMIN, API.CHAT_MEMBERSHIPS)
  cd = buildGAPIObject(API.DIRECTORY)
  parent = None
  role = CHAT_MEMBER_ROLE_MAP['member']
  mtype = CHAT_MEMBER_TYPE_MAP['human']
  syncOperation = 'addremove'
  kwargs = {}
  preview = False
  csvPF = None
  userList = []
  usersSpecified = False
  groupList = []
  groupsSpecified = False
  while Cmd.ArgumentsRemaining():
    myarg = getArgument()
    if myarg == 'space' or myarg.startswith('spaces/') or myarg.startswith('space/'):
      parent = getSpaceName(myarg)
    elif myarg == 'role':
      role = getChoice(CHAT_MEMBER_ROLE_MAP, mapChoice=True)
    elif myarg == 'type':
      mtype = getChoice(CHAT_MEMBER_TYPE_MAP, mapChoice=True)
    elif myarg in {'addonly', 'removeonly'}:
      syncOperation = myarg
    elif myarg == 'preview':
      preview = True
    elif myarg == 'actioncsv':
      csvPF = CSVPrintFile(CHAT_SYNC_PREVIEW_TITLES)
    elif myarg == 'users':
      for user in getEntityList(Cmd.OB_USER_ENTITY):
        getUserMemberID(cd, user, userList)
      usersSpecified = True
    elif myarg in {'member', 'members'}:
      _, members = getEntityToModify(defaultEntityType=Cmd.ENTITY_USERS)
      for user in members:
        getUserMemberID(cd, user, userList)
      usersSpecified = True
    elif myarg == 'groups':
      for group in getEntityList(Cmd.OB_GROUP_ENTITY):
        getGroupMemberID(cd, group, groupList)
      groupsSpecified = True
    else:
      unknownArgumentExit()
  if not parent:
    missingArgumentExit('space')
  userEntityType = CHAT_ROLE_ENTITY_TYPE_MAP[role]
  userMembers = {}
  syncUsersSet = set()
  for user in userList:
    memberName = f'{parent}/members/{user}'
    userMembers[memberName] = {'member': {'name': f'users/{user}', 'type': mtype}}
    syncUsersSet.add(memberName)
  groupMembers = {}
  syncGroupsSet = set()
  for group in groupList:
    memberName = f'{parent}/members/group-{group}'
    groupMembers[memberName] = {'groupMember': {'name': f'groups/{group}'}}
    syncGroupsSet.add(memberName)
  qfilter = f'{Ent.Singular(Ent.CHAT_SPACE)}: {parent}'
  i, count, users = getEntityArgument(users)
  if useAdminAccess:
    kwargs['filter'] = 'member.type != "BOT"'
    _chkChatAdminAccess(count)
  for user in users:
    i += 1
    user, chat, kvList = buildChatServiceObject(api, user, i, count, [Ent.CHAT_SPACE, parent], useAdminAccess)
    if not chat:
      continue
    currentUsersSet = set()
    currentGroupsSet = set()
    try:
      members = callGAPIpages(chat.spaces().members(), 'list', 'memberships',
                              pageMessage=_getChatPageMessage(Ent.CHAT_MEMBER, user, i, count, qfilter),
                              throwReasons=[GAPI.NOT_FOUND, GAPI.INVALID_ARGUMENT, GAPI.PERMISSION_DENIED, GAPI.FAILED_PRECONDITION],
                              retryReasons=GAPI.SERVICE_NOT_AVAILABLE_RETRY_REASONS,
                              parent=parent, showGroups=groupsSpecified, pageSize=GC.Values[GC.CHAT_MAX_RESULTS], **kwargs, **kwargsUAA)
      for member in members:
        if 'member' in member:
          if member['member']['type'] == mtype and member['role'] == role:
            currentUsersSet.add(member['name'])
        elif 'groupMember' in member:
          currentGroupsSet.add(member['name'])
    except (GAPI.notFound, GAPI.invalidArgument, GAPI.permissionDenied) as e:
      exitIfChatNotConfigured(chat, kvList, str(e), i, count)
      continue
    except GAPI.failedPrecondition:
      userChatServiceNotEnabledWarning(user, i, count)
      continue
    if syncOperation != 'addonly':
      Act.Set([Act.REMOVE, Act.REMOVE_PREVIEW][preview])
      if usersSpecified:
        deleteMembers(currentUsersSet-syncUsersSet, userEntityType, i, count)
      if groupsSpecified:
        deleteMembers(currentGroupsSet-syncGroupsSet, Ent.CHAT_MEMBER_GROUP, i, count)
    if syncOperation != 'removeonly':
      Act.Set([Act.ADD, Act.ADD_PREVIEW][preview])
      if usersSpecified:
        addMembers(syncUsersSet-currentUsersSet, userMembers, userEntityType, i, count)
      if groupsSpecified:
        addMembers(syncGroupsSet-currentGroupsSet, groupMembers, Ent.CHAT_MEMBER_GROUP, i, count)
  if csvPF:
    csvPF.writeCSVfile('Chat Member Updates')

CHAT_MEMBERS_FIELDS_CHOICE_MAP = {
  "createtime": "createTime",
  "deletetime": "deleteTime",
  "groupmember": "groupMember",
  "member": "member",
  "name": "name",
  "role": "role",
  "state": "state",
  }

# gam [<UserTypeEntity>] info chatmember members <ChatMemberList>
#	[fields <ChatMemberFieldNameList>]
#	[formatjson]
# gam <UserItem> info chatmember asadmin members <ChatMemberList>
#	[fields <ChatMemberFieldNameList>]
#	[formatjson]
def infoChatMember(users):
  cd = buildGAPIObject(API.DIRECTORY)
  FJQC = FormatJSONQuoteChar()
  useAdminAccess, api, kwargsUAA = _getChatAdminAccess(API.CHAT_MEMBERSHIPS_ADMIN, API.CHAT_MEMBERSHIPS)
  fieldsList = []
  memberNames = []
  while Cmd.ArgumentsRemaining():
    myarg = getArgument()
    if myarg in {'member', 'members'}:
      memberNames.extend(getString(Cmd.OB_CHAT_MEMBER).replace(',', ' ').split())
    elif getFieldsList(myarg, CHAT_MEMBERS_FIELDS_CHOICE_MAP, fieldsList, initialField='name', onlyFieldsArg=True):
      pass
    else:
      FJQC.GetFormatJSON(myarg)
  if not memberNames:
    missingArgumentExit('members')
  fields = getFieldsFromFieldsList(fieldsList)
  i, count, users = getEntityArgument(users)
  if useAdminAccess:
    _chkChatAdminAccess(count)
  for user in users:
    i += 1
    user, chat, kvList = buildChatServiceObject(api, user, i, count, None, useAdminAccess)
    if not chat:
      continue
    jcount = len(memberNames)
    if not FJQC.formatJSON:
      entityPerformActionNumItems(kvList, jcount, Ent.CHAT_MEMBER, i, count)
    kvList.extend([Ent.CHAT_MEMBER, ''])
    j = 0
    for name in memberNames:
      j += 1
      kvList[-1] = name
      try:
        member = callGAPI(chat.spaces().members(), 'get',
                          bailOnInternalError=True,
                          throwReasons=[GAPI.NOT_FOUND, GAPI.INVALID_ARGUMENT, GAPI.INTERNAL_ERROR,
                                        GAPI.PERMISSION_DENIED, GAPI.FAILED_PRECONDITION],
                          name=name, fields=fields, **kwargsUAA)
        _getChatMemberEmail(cd, member)
        Ind.Increment()
        _showChatItem(member, Ent.CHAT_MEMBER, FJQC, j, jcount)
        Ind.Decrement()
      except (GAPI.notFound, GAPI.invalidArgument, GAPI.permissionDenied, GAPI.internalError) as e:
        exitIfChatNotConfigured(chat, kvList, str(e), i, count)
      except GAPI.failedPrecondition:
        userChatServiceNotEnabledWarning(user, i, count)
        continue

def doInfoChatMember():
  infoChatMember([None])

# gam [<UserTypeEntity>] show chatmembers
#	<ChatSpace>* [types <ChatSpaceTypeList>]
#	[showinvited [<Boolean>]] [showgroups [<Boolean>]] [filter <String>]
#	[fields <ChatMemberFieldNameList>]
#	[formatjson]
# gam [<UserTypeEntity>] print chatmembers [todrive <ToDriveAttribute>*]
#	<ChatSpace>* [types <ChatSpaceTypeList>]
#	[showinvited [<Boolean>]] [showgroups [<Boolean>]] [filter <String>]
#	[fields <ChatMemberFieldNameList>]
#	(addcsvdata <FieldName> <String>)*
#	[formatjson [quotechar <Character>]]
# gam <UserItem> show chatmembers asadmin
#	<ChatSpace>* [query <String>] [querytime<String> <Time>]
#	[orderby <ChatSpaceAdminOrderByFieldName> [ascending|descending]]
#	[showinvited [<Boolean>]] [showgroups [<Boolean>]] [filter <String>]
#	[fields <ChatMemberFieldNameList>]
#	[formatjson]
# gam <UserItem> print chatmembers asadmin [todrive <ToDriveAttribute>*]
#	<ChatSpace>* [query <String>] [querytime<String> <Time>]
#	[orderby <ChatSpaceAdminOrderByFieldName> [ascending|descending]]
#	[showinvited [<Boolean>]] [showgroups [<Boolean>]] [filter <String>]
#	[fields <ChatMemberFieldNameList>]
#	(addcsvdata <FieldName> <String>)*
#	[formatjson [quotechar <Character>]]
def printShowChatMembers(users):
  cd = buildGAPIObject(API.DIRECTORY)
  csvPF = CSVPrintFile(['User', 'space.name', 'space.displayName', 'name'] if not isinstance(users, list) else ['space.name', 'space.displayName', 'name']) if Act.csvFormat() else None
  FJQC = FormatJSONQuoteChar(csvPF)
  OBY = OrderBy(CHAT_SPACES_ADMIN_ORDERBY_CHOICE_MAP)
  useAdminAccess, api, kwargsUAA = _getChatAdminAccess(API.CHAT_MEMBERSHIPS_ADMIN, API.CHAT_MEMBERSHIPS)
  if useAdminAccess:
    queries = ['customer = "customers/my_customer" AND spaceType = "SPACE"']
    queryTimes = {}
  fieldsList = []
  pfilter = ''
  kwargs = {}
  kwargsCS = {}
  parentList = []
  addCSVData = {}
  while Cmd.ArgumentsRemaining():
    myarg = getArgument()
    if csvPF and myarg == 'todrive':
      csvPF.GetTodriveParameters()
    elif myarg == 'space' or myarg.startswith('spaces/') or myarg.startswith('space/'):
      parentList.append({'name': getSpaceName(myarg), 'displayName': ''})
    elif getFieldsList(myarg, CHAT_MEMBERS_FIELDS_CHOICE_MAP, fieldsList, initialField='name', onlyFieldsArg=True):
      pass
    elif myarg == 'showinvited':
      kwargs['showInvited'] = getBoolean()
    elif myarg == 'showgroups':
      kwargs['showGroups'] = getBoolean()
    elif myarg =='filter':
      pfilter = getString(Cmd.OB_STRING)
    elif not useAdminAccess and _getChatSpaceListParms(myarg, kwargsCS):
      pass
    elif useAdminAccess and _getChatSpaceSearchParms(myarg, queries, queryTimes, OBY):
      pass
    elif csvPF and myarg == 'addcsvdata':
      getAddCSVData(addCSVData)
    else:
      FJQC.GetFormatJSONQuoteChar(myarg, True)
  if useAdminAccess:
    if not parentList:
      kwargsCS['orderBy'] = OBY.orderBy
      substituteQueryTimes(queries, queryTimes)
      kwargsCS['query'] = queries[0]
      kwargsCS['useAdminAccess'] = True
  else:
    if not parentList and not kwargsCS:
      kwargsCS['filter'] = 'spaceType = "SPACE" OR spaceType = "GROUP_CHAT" OR spaceType = "DIRECT_MESSAGE"'
  if pfilter:
    if 'member.type' not in pfilter:
      kwargs['filter'] = 'member.type != "BOT" AND '+pfilter
    else:
      kwargs['filter'] = pfilter
  else:
    kwargs['filter'] = 'member.type != "BOT"'
  fields = getItemFieldsFromFieldsList('memberships', fieldsList)
  i, count, users = getEntityArgument(users)
  if useAdminAccess:
    _chkChatAdminAccess(count)
    sortName = 'displayName'
  else:
    sortName = 'name'
  for user in users:
    i += 1
    user, chat, kvList = buildChatServiceObject(api, user, i, count, [Ent.CHAT_SPACE, None], useAdminAccess)
    if not chat:
      continue
    if useAdminAccess:
      _, chatsp, _ = buildChatServiceObject(API.CHAT_SPACES_ADMIN, user, i, count, None, useAdminAccess)
    else:
      _, chatsp, _ = buildChatServiceObject(API.CHAT_SPACES, user, i, count, None, useAdminAccess)
    if not chatsp:
      continue
    if kwargsCS:
      if useAdminAccess:
        try:
          spaces = callGAPIpages(chatsp.spaces(), 'search', 'spaces',
                                 pageMessage=_getChatPageMessage(Ent.CHAT_SPACE, user, i, count, queries[0], True),
                                 bailOnInternalError=True,
                                 throwReasons=[GAPI.NOT_FOUND, GAPI.INVALID_ARGUMENT, GAPI.INTERNAL_ERROR,
                                               GAPI.PERMISSION_DENIED, GAPI.FAILED_PRECONDITION],
                                 retryReasons=GAPI.SERVICE_NOT_AVAILABLE_RETRY_REASONS,
                                 fields="nextPageToken,spaces(name,displayName,spaceType,membershipCount)", pageSize=GC.Values[GC.CHAT_MAX_RESULTS],
                                 **kwargsCS)
          for space in sorted(spaces, key=lambda k: k[sortName]):
            if space['spaceType'] == 'SPACE' and 'membershipCount' in space:
              parentList.append({'name': space['name'], 'displayName': space.get('displayName', 'None')})
        except (GAPI.notFound, GAPI.invalidArgument, GAPI.internalError,
                GAPI.permissionDenied, GAPI.failedPrecondition) as e:
          exitIfChatNotConfigured(chat, kvList, str(e), i, count)
          continue
      else:
        try:
          spaces = callGAPIpages(chatsp.spaces(), 'list', 'spaces',
                                 pageMessage=_getChatPageMessage(Ent.CHAT_SPACE, user, i, count, kwargsCS['filter']),
                                 bailOnInternalError=True,
                                 throwReasons=[GAPI.NOT_FOUND, GAPI.INVALID_ARGUMENT, GAPI.INTERNAL_ERROR,
                                               GAPI.PERMISSION_DENIED, GAPI.FAILED_PRECONDITION],
                                 retryReasons=GAPI.SERVICE_NOT_AVAILABLE_RETRY_REASONS,
                                 fields="nextPageToken,spaces(name,displayName,spaceType,membershipCount)", pageSize=GC.Values[GC.CHAT_MAX_RESULTS],
                                 **kwargsCS)
          for space in sorted(spaces, key=lambda k: k[sortName]):
#            if 'membershipCount' in space:
#              parentList.append({'name': space['name'], 'displayName': space.get('displayName', 'None')})
            parentList.append({'name': space['name'], 'displayName': space.get('displayName', 'None')})
        except (GAPI.notFound, GAPI.invalidArgument, GAPI.internalError, GAPI.permissionDenied) as e:
          exitIfChatNotConfigured(chat, kvList, str(e), i, count)
          continue
        except GAPI.failedPrecondition:
          userChatServiceNotEnabledWarning(user, i, count)
          continue
    jcount = len(parentList)
    j = 0
    for parent in parentList:
      j += 1
      parentName = parent['name']
      kvList[-1] = parentName
      qfilter = f'{Ent.Singular(Ent.CHAT_SPACE)}: {parentName}'
      if 'filter' in kwargs:
        qfilter += f', {kwargs["filter"]}'
      try:
        if not parent['displayName']:
          space = callGAPI(chatsp.spaces(), 'get',
                           throwReasons=[GAPI.NOT_FOUND, GAPI.INVALID_ARGUMENT, GAPI.PERMISSION_DENIED],
                           name=parentName, fields='displayName', **kwargsUAA)
          parent['displayName'] = space.get('displayName', 'None')
        members = callGAPIpages(chat.spaces().members(), 'list', 'memberships',
                                pageMessage=_getChatPageMessage(Ent.CHAT_MEMBER, user, j, jcount, qfilter),
                                throwReasons=[GAPI.NOT_FOUND, GAPI.INVALID_ARGUMENT, GAPI.PERMISSION_DENIED],
                                retryReasons=GAPI.SERVICE_NOT_AVAILABLE_RETRY_REASONS,
                                parent=parentName, fields=fields, pageSize=GC.Values[GC.CHAT_MAX_RESULTS], **kwargs, **kwargsUAA)
        for member in members:
          _getChatMemberEmail(cd, member)
      except (GAPI.notFound, GAPI.invalidArgument, GAPI.permissionDenied) as e:
        exitIfChatNotConfigured(chat, kvList, str(e), j, jcount)
        continue
      if not csvPF:
        kcount = len(members)
        if not FJQC.formatJSON:
          entityPerformActionNumItems(kvList, kcount, Ent.CHAT_MEMBER, j, jcount)
        Ind.Increment()
        k = 0
        for member in members:
          k += 1
          member['space'] = {'name': parentName, 'displayName': parent['displayName']}
          _showChatItem(member, Ent.CHAT_MEMBER, FJQC, k, kcount)
        Ind.Decrement()
      else:
        for member in members:
          _printChatItem(user, member, parent, Ent.CHAT_MEMBER, csvPF, FJQC, addCSVData)
  if csvPF:
    csvPF.writeCSVfile('Chat Members')

def doPrintShowChatMembers():
  printShowChatMembers([None])

def _getChatSenderEmail(cd, sender, chatSenders):
  if sender['type'] == 'HUMAN':
    _, senderUid = sender['name'].split('/')
    if senderUid in chatSenders:
      sender['email'] = chatSenders[senderUid]
    else:
      sender['email'], _ = convertUIDtoEmailAddressWithType(f'uid:{senderUid}', cd, None, emailTypes=['user'])
      chatSenders[senderUid] = sender['email']

def trimChatMessageIfRequired(body):
  if 'text' in body:
    msgLen = len(body['text'])
    if msgLen > 4096:
      stderrWarningMsg(Msg.TRIMMED_MESSAGE_FROM_LENGTH_TO_MAXIMUM.format(msgLen, 4096))
      body['text'] = body['text'][:4095]

CHAT_MESSAGE_REPLY_OPTION_MAP = {
  'fail': 'REPLY_MESSAGE_OR_FAIL',
  'fallbacktonew': 'REPLY_MESSAGE_FALLBACK_TO_NEW_THREAD',
  }

# gam [<UserTypeEntityu>] create chatmessage <ChatSpace>
#	<ChatContent>
#	[messageId <ChatMessageID>]
#	[(thread <ChatThread>)|(threadkey <String>) [replyoption fail|fallbacktonew]]
#	[returnidonly]
def createChatMessage(users):
  messageId = messageReplyOption = parent = None
  body = {}
  returnIdOnly = False
  while Cmd.ArgumentsRemaining():
    myarg = getArgument()
    if myarg == 'space' or myarg.startswith('spaces/') or myarg.startswith('space/'):
      parent = getSpaceName(myarg)
    elif myarg == 'thread':
      body.setdefault('thread', {})
      body['thread']['name'] = getString(Cmd.OB_CHAT_THREAD)
      Act.Set(Act.RESPOND)
    elif myarg == 'threadkey':
      body.setdefault('thread', {})
      body['thread']['threadKey'] = getString(Cmd.OB_STRING)
      Act.Set(Act.RESPOND)
    elif myarg == 'replyoption':
      messageReplyOption = getChoice(CHAT_MESSAGE_REPLY_OPTION_MAP, mapChoice=True)
    elif myarg in SORF_TEXT_ARGUMENTS:
      body['text'] = getStringOrFile(myarg, minLen=0, unescapeCRLF=True)[0]
    elif myarg == 'messageid':
      messageId = getString(Cmd.OB_CHAT_MESSAGE_ID, minLen=1, maxLen=63)
    elif myarg == 'returnidonly':
      returnIdOnly = True
    else:
      unknownArgumentExit()
  if not parent:
    missingArgumentExit('space')
  if 'text' not in body:
    missingArgumentExit('text or textfile')
  if 'thread' in body and messageReplyOption is None:
    messageReplyOption = CHAT_MESSAGE_REPLY_OPTION_MAP['fail']
  trimChatMessageIfRequired(body)
  action = Act.Get()
  i, count, users = getEntityArgument(users)
  for user in users:
    i += 1
    user, chat, kvList = buildChatServiceObject(API.CHAT_MESSAGES, user, i, count, [Ent.CHAT_SPACE, parent])
    if not chat:
      continue
    try:
      resp = callGAPI(chat.spaces().messages(), 'create',
                      throwReasons=[GAPI.NOT_FOUND, GAPI.INVALID_ARGUMENT, GAPI.PERMISSION_DENIED, GAPI.FAILED_PRECONDITION],
                      parent=parent, requestId=str(uuid.uuid4()),
                      messageReplyOption=messageReplyOption, messageId=messageId, body=body)
      if not returnIdOnly:
        kvList.extend([Ent.CHAT_MESSAGE, resp['name']])
        if 'clientAssignedMessageId' in resp:
          kvList.extend([Ent.CHAT_MESSAGE_ID, resp['clientAssignedMessageId']])
        kvList.extend([Ent.CHAT_THREAD, resp['thread']['name']])
        if (action == Act.RESPOND) and not resp.get('threadReply', False):
          Act.Set(Act.CREATE)
        entityActionPerformed(kvList, i, count)
        Act.Set(action)
      else:
        writeStdout(f'{resp["name"]}\n')
    except (GAPI.notFound, GAPI.invalidArgument, GAPI.permissionDenied) as e:
      exitIfChatNotConfigured(chat, kvList, str(e), i, count)
    except GAPI.failedPrecondition:
      userChatServiceNotEnabledWarning(user, i, count)

def doCreateChatMessage():
  createChatMessage([None])

# gam [<UserTypeMessage>] update chatmessage name <ChatMessage>
#	[<ChatContent>] [clearattachments <String>]
def updateChatMessage(users):
  name = None
  body = {}
  updateMask = []
  clearMsg = ''
  while Cmd.ArgumentsRemaining():
    myarg = getArgument()
    if myarg == 'name':
      name = getString(Cmd.OB_CHAT_MESSAGE)
    elif myarg in SORF_TEXT_ARGUMENTS:
      body['text'] = getStringOrFile(myarg, minLen=0, unescapeCRLF=True)[0]
      updateMask.append('text')
    elif myarg == 'clearattachments':
      clearMsg = getString(Cmd.OB_STRING, minLen=0)
      body['attachment'] = []
      updateMask.append('attachment')
    else:
      unknownArgumentExit()
  if not name:
    missingArgumentExit('name')
  if not updateMask:
    missingArgumentExit('text|textfile|clearattachments')
  trimChatMessageIfRequired(body)
  i, count, users = getEntityArgument(users)
  for user in users:
    i += 1
    user, chat, kvList = buildChatServiceObject(API.CHAT_MESSAGES, user, i, count, [Ent.CHAT_MESSAGE, name])
    if not chat:
      continue
    try:
      if 'attachment' in updateMask and 'text' not in updateMask:
        resp = callGAPI(chat.spaces().messages(), 'get',
                        throwReasons=[GAPI.NOT_FOUND, GAPI.INVALID_ARGUMENT, GAPI.PERMISSION_DENIED, GAPI.FAILED_PRECONDITION],
                        name=name, fields='text')
        body['text'] = resp.get('text', '')
        if clearMsg:
          body['text'] += clearMsg
        elif not body['text']:
          body['text'] = 'Attachments cleared'
        updateMask.append('text')
      resp = callGAPI(chat.spaces().messages(), 'patch',
                      throwReasons=[GAPI.NOT_FOUND, GAPI.INVALID_ARGUMENT, GAPI.PERMISSION_DENIED, GAPI.FAILED_PRECONDITION],
                      name=name, updateMask=','.join(updateMask), body=body)
      kvList.extend([Ent.CHAT_THREAD, resp['thread']['name']])
      entityActionPerformed(kvList, i, count)
    except (GAPI.notFound, GAPI.invalidArgument, GAPI.permissionDenied) as e:
      exitIfChatNotConfigured(chat, kvList, str(e), i, count)
    except GAPI.failedPrecondition:
      userChatServiceNotEnabledWarning(user, i, count)

def doUpdateChatMessage():
  updateChatMessage([None])

# gam [<UserTypeEntity>] delete chatmessage name <ChatMessage>
def deleteChatMessage(users):
  name = None
  while Cmd.ArgumentsRemaining():
    myarg = getArgument()
    if myarg == 'name':
      name = getString(Cmd.OB_CHAT_MESSAGE)
    else:
      unknownArgumentExit()
  if not name:
    missingArgumentExit('name')
  i, count, users = getEntityArgument(users)
  for user in users:
    i += 1
    user, chat, kvList = buildChatServiceObject(API.CHAT_MESSAGES, user, i, count, [Ent.CHAT_MESSAGE, name])
    if not chat:
      continue
    try:
      callGAPI(chat.spaces().messages(), 'delete',
               throwReasons=[GAPI.NOT_FOUND, GAPI.INVALID_ARGUMENT, GAPI.PERMISSION_DENIED, GAPI.FAILED_PRECONDITION],
               name=name)
      entityActionPerformed(kvList, i, count)
    except (GAPI.notFound, GAPI.invalidArgument, GAPI.permissionDenied) as e:
      exitIfChatNotConfigured(chat, kvList, str(e), i, count)
    except GAPI.failedPrecondition:
      userChatServiceNotEnabledWarning(user, i, count)

def doDeleteChatMessage():
  deleteChatMessage([None])

CHAT_MESSAGES_FIELDS_CHOICE_MAP = {
  "accessorywidgets": "accessoryWidgets",
  "actionresponse": "actionResponse",
  "annotations": "annotations",
  "argumenttext": "argumentText",
  "attachedgifs": "attachedGifs",
  "attachment": "attachment",
  "cards": "cards",
  "cardsv2": "cardsV2",
  "clientassignedmessageid": "clientAssignedMessageId",
  "createtime": "createTime",
  "deletetime": "deleteTime",
  "deletionmetadata": "deletionMetadata",
  "emojireactionsummaries": "emojiReactionSummaries",
  "fallbacktext": "fallbackText",
  "formattedtext": "formattedText",
  "lastupdatetime": "lastUpdateTime",
  "matchedurl": "matchedUrl",
  "name": "name",
  "privatemessageviewer": "privateMessageViewer",
  "quotedmessagemetadata": "quotedMessageMetadata",
  "sender": "sender",
  "slashcommand": "slashCommand",
  "space": "space",
  "text": "text",
  "thread": "thread",
  "threadreply": "threadReply",
  }

# gam [<UserTypeEntity>] info chatmessage name <ChatMessage>
#	[fields <ChatMessageFieldNameList>]
#	[formatjson]
def infoChatMessage(users):
  cd = buildGAPIObject(API.DIRECTORY)
  FJQC = FormatJSONQuoteChar()
  fieldsList = []
  name = None
  while Cmd.ArgumentsRemaining():
    myarg = getArgument()
    if myarg == 'name':
      name = getString(Cmd.OB_CHAT_MESSAGE)
    elif getFieldsList(myarg, CHAT_MESSAGES_FIELDS_CHOICE_MAP, fieldsList, initialField='name', onlyFieldsArg=True):
      pass
    else:
      FJQC.GetFormatJSON(myarg)
  if not name:
    missingArgumentExit('name')
  chatSenders = {}
  fields = getFieldsFromFieldsList(fieldsList)
  i, count, users = getEntityArgument(users)
  for user in users:
    i += 1
    user, chat, kvList = buildChatServiceObject(API.CHAT_MESSAGES, user, i, count, [Ent.CHAT_MESSAGE, name])
    if not chat:
      continue
    try:
      message = callGAPI(chat.spaces().messages(), 'get',
                         throwReasons=[GAPI.NOT_FOUND, GAPI.INVALID_ARGUMENT, GAPI.PERMISSION_DENIED, GAPI.FAILED_PRECONDITION],
                         name=name, fields=fields)
      _getChatSenderEmail(cd, message['sender'], chatSenders)
      if not FJQC.formatJSON:
        entityPerformAction(kvList, i, count)
      Ind.Increment()
      _showChatItem(message, Ent.CHAT_MESSAGE, FJQC)
      Ind.Decrement()
    except (GAPI.notFound, GAPI.invalidArgument, GAPI.permissionDenied) as e:
      exitIfChatNotConfigured(chat, kvList, str(e), i, count)
    except GAPI.failedPrecondition:
      userChatServiceNotEnabledWarning(user, i, count)

def doInfoChatMessage():
  infoChatMessage([None])

CHAT_MESSAGES_ORDERBY_CHOICE_MAP = {
  'createtime': 'createTime'
  }

# gam <UserTypeEntity> show chatmessages
#	<ChatSpace>+
#	[showdeleted [<Boolean>]]
#	[([start|starttime <Date>|<Time>] [end|endtime <Date>|<Time>])|(range <Date>|<Time> <Date>|<Time>)]
#	[thread <ChatThread>])
#	[fields <ChatMessageFieldNameList>]
#	[orderby createtime [ascending|descending]]
#	[formatjson]
# gam <UserTypeEntity> print chatmessages [todrive <ToDriveAttribute>*]
#	<ChatSpace>+
#	[showdeleted [<Boolean>]] [filter <String>]
#	[([start|starttime <Date>|<Time>] [end|endtime <Date>|<Time>])|(range <Date>|<Time> <Date>|<Time>)]
#	[thread <ChatThread>])
#	[fields <ChatMessageFieldNameList>]
#	[orderby createtime [ascending|descending]]
#	[formatjson [quotechar <Character>]]
def printShowChatMessages(users):
  cd = buildGAPIObject(API.DIRECTORY)
  csvPF = CSVPrintFile(['User', 'space.name', 'space.displayName', 'name']) if Act.csvFormat() else None
  FJQC = FormatJSONQuoteChar(csvPF)
  OBY = OrderBy(CHAT_MESSAGES_ORDERBY_CHOICE_MAP, ascendingKeyword='ASC', descendingKeyword='DESC')
  fieldsList = []
  pfilter = None
  parentList = []
  showDeleted = False
  startEndTime = StartEndTime()
  threadName = ''
  while Cmd.ArgumentsRemaining():
    myarg = getArgument()
    if csvPF and myarg == 'todrive':
      csvPF.GetTodriveParameters()
    elif myarg == 'space' or myarg.startswith('spaces/') or myarg.startswith('space/'):
      parentList.append({'name': getSpaceName(myarg), 'displayName': ''})
    elif getFieldsList(myarg, CHAT_MESSAGES_FIELDS_CHOICE_MAP, fieldsList, initialField='name', onlyFieldsArg=True):
      pass
    elif myarg == 'showdeleted':
      showDeleted = getBoolean()
    elif myarg =='filter':
      pfilter = getString(Cmd.OB_STRING)
    elif myarg in {'start', 'starttime', 'end', 'endtime', 'range'}:
      startEndTime.Get(myarg)
    elif myarg == 'thread':
      threadName = getString(Cmd.OB_CHAT_THREAD)
    elif myarg == 'orderby':
      OBY.GetChoice()
    else:
      FJQC.GetFormatJSONQuoteChar(myarg, True)
  if not parentList:
    missingArgumentExit('space')
  if startEndTime.startDateTime is not None or startEndTime.endDateTime is not None:
    if pfilter:
      pfilter += ' AND '
    else:
      pfilter = ''
    pfilter += '('
    if startEndTime.startDateTime is not None:
      pfilter += f'createTime > "{startEndTime.startDateTime}"'
      if startEndTime.endDateTime is not None:
        pfilter += ' AND '
    if startEndTime.endDateTime is not None:
      pfilter += f'createTime < "{startEndTime.endDateTime}"'
    pfilter += ')'
  if threadName:
    if pfilter:
      pfilter += ' AND '
    else:
      pfilter = ''
    pfilter += f'thread.name = {threadName}'
  chatSenders = {}
  fields = getItemFieldsFromFieldsList('messages', fieldsList)
  i, count, users = getEntityArgument(users)
  for user in users:
    i += 1
    user, chat, kvList = buildChatServiceObject(API.CHAT_MESSAGES, user, i, count, [Ent.CHAT_SPACE, None])
    if not chat:
      continue
    _, chatspg, _ = buildChatServiceObject(API.CHAT_SPACES, user, i, count, None)
    if not chatspg:
      continue
    jcount = len(parentList)
    j = 0
    for parent in parentList:
      j += 1
      parentName = parent['name']
      kvList[-1] = parentName
      qfilter = f'{Ent.Singular(Ent.CHAT_SPACE)}: {parentName}'
      if pfilter:
        qfilter += f', {pfilter}'
      try:
        if not parent['displayName']:
          space = callGAPI(chatspg.spaces(), 'get',
                           throwReasons=[GAPI.NOT_FOUND, GAPI.INVALID_ARGUMENT, GAPI.PERMISSION_DENIED, GAPI.FAILED_PRECONDITION],
                           name=parentName, fields='displayName')
          parent['displayName'] = space.get('displayName', 'None')
        messages = callGAPIpages(chat.spaces().messages(), 'list', 'messages',
                                 pageMessage=_getChatPageMessage(Ent.CHAT_MESSAGE, user, i, count, qfilter),
                                 throwReasons=[GAPI.NOT_FOUND, GAPI.INVALID_ARGUMENT, GAPI.PERMISSION_DENIED],
                                 retryReasons=GAPI.SERVICE_NOT_AVAILABLE_RETRY_REASONS,
                                 pageSize=GC.Values[GC.CHAT_MAX_RESULTS], parent=parentName,
                                 filter=pfilter, showDeleted=showDeleted, orderBy=OBY.orderBy,
                                 fields=fields)
        for message in messages:
          if 'sender' in message:
            _getChatSenderEmail(cd, message['sender'], chatSenders)
      except (GAPI.notFound, GAPI.invalidArgument, GAPI.permissionDenied) as e:
        exitIfChatNotConfigured(chat, kvList, str(e), i, count)
        continue
      except GAPI.failedPrecondition:
        userChatServiceNotEnabledWarning(user, i, count)
        break
      if not csvPF:
        kcount = len(messages)
        if not FJQC.formatJSON:
          entityPerformActionNumItems(kvList, kcount, Ent.CHAT_MESSAGE, j, jcount)
        Ind.Increment()
        k = 0
        for message in messages:
          k += 1
          if 'space' in message:
            message['space']['displayName'] = parent['displayName']
          _showChatItem(message, Ent.CHAT_MESSAGE, FJQC, k, kcount)
        Ind.Decrement()
      elif messages:
        for message in messages:
          _printChatItem(user, message, parent, Ent.CHAT_MESSAGE, csvPF, FJQC)
      elif GC.Values[GC.CSV_OUTPUT_USERS_AUDIT]:
        csvPF.WriteRowNoFilter({'User': user})
  if csvPF:
    csvPF.writeCSVfile('Chat Messages')

def _getChatSpaceDisplayName(chat, space, chatSpaces):
  spaceName = space['name']
  if spaceName not in chatSpaces:
    try:
      result = callGAPI(chat.spaces(), 'get',
                        throwReasons=[GAPI.NOT_FOUND, GAPI.INVALID_ARGUMENT, GAPI.INTERNAL_ERROR,
                                      GAPI.PERMISSION_DENIED, GAPI.FAILED_PRECONDITION],
                        name=spaceName, fields='displayName')
      spaceDisplayName = result.get('displayName', 'None')
    except (GAPI.notFound, GAPI.invalidArgument, GAPI.internalError, GAPI.permissionDenied, GAPI.failedPrecondition):
      spaceDisplayName = 'None'
    chatSpaces[spaceName] = spaceDisplayName
  space['displayName'] = chatSpaces[spaceName]

CHAT_SEARCHMESSAGES_ORDERBY_CHOICE_MAP = {
  'createtime': 'createTime',
  'relevance': 'relevance',
  }
CHAT_SEARCHMESSAGES_VIEW_CHOICE_MAP = {'basic': 'SEARCH_MESSAGES_VIEW_BASIC', 'full': 'SEARCH_MESSAGES_VIEW_FULL'}

# gam <UserTypeEntity> show chatsearchmessages
#	keywords <StringList>
#	<ChatSpace>*
#	[displaynames [all|any] <StringList>]
#	[senders <EmailAddressEntity>]*
#	[usermentions [all|any] <EmailAddressEntity>]*
#	[([start|starttime <Date>|<Time>] [end|endtime <Date>|<Time>])|(range <Date>|<Time> <Date>|<Time>)]
#	[hasattachment [<Boolean>]]
#	[fields <ChatMessageFieldNameList>]
#	[orderby createtime|relevance]
#	[basic|full]
#	[formatjson]
# gam <UserTypeEntity> print chatsearchmessages [todrive <ToDriveAttribute>*]
#	keywords <StringList>
#	<ChatSpace>*
#	[displaynames [all|any] <StringList>]
#	[senders <EmailAddressEntity>]*
#	[usermentions [all|any] <EmailAddressEntity>]*
#	[([start|starttime <Date>|<Time>] [end|endtime <Date>|<Time>])|(range <Date>|<Time> <Date>|<Time>)]
#	[hasattachment [<Boolean>]]
#	[fields <ChatMessageFieldNameList>]
#	[orderby createtime|relevance]
#	[basic|full]
#	[formatjson [quotechar <Character>]]
def printShowChatSearchMessages(users):
  if API.CHAT not in GM.Globals[GM.DEVELOPER_PREVIEW_APIS]:
    Cmd.Backup()
    usageErrorExit(Msg.DEVELOPER_PREVIEW_REQUIRED)
  cd = buildGAPIObject(API.DIRECTORY)
  csvPF = CSVPrintFile(['User', 'space.name', 'space.displayName', 'name']) if Act.csvFormat() else None
  FJQC = FormatJSONQuoteChar(csvPF)
  orderBy = None
  fieldsList = []
  keywordList = []
  spaceList = []
  displayNameConjunction = ''
  displayNameList = []
  senderList = []
  userMentionList = []
  startEndTime = StartEndTime()
  hasAttachment = False
  body = {'view': CHAT_SEARCHMESSAGES_VIEW_CHOICE_MAP['basic'],
          'pageSize': GC.Values[GC.CHAT_MAX_RESULTS], 'pageToken': None}
  parent = 'spaces/-'
  while Cmd.ArgumentsRemaining():
    myarg = getArgument()
    if csvPF and myarg == 'todrive':
      csvPF.GetTodriveParameters()
    elif myarg =='keywords':
      keywordList = getString(Cmd.OB_STRING_LIST, minLen=0).replace(',', ' ').split()
    elif myarg == 'space' or myarg.startswith('spaces/') or myarg.startswith('space/'):
      spaceList.append(getSpaceName(myarg))
    elif myarg == 'displaynames':
      displayNameConjunction = getChoice(AND_OR_CONJUNCTION_MAP, mapChoice=True, defaultChoice='OR')
      displayNameList = getString(Cmd.OB_STRING_LIST, minLen=0).replace(',', ' ').split()
    elif myarg == 'senders':
      senderList.extend(getNormalizedEmailAddressEntity(noUid=False))
    elif myarg == 'usermentions':
      userMentionConjunction = getChoice(AND_OR_CONJUNCTION_MAP, mapChoice=True, defaultChoice='OR')
      userMentionList.extend(getNormalizedEmailAddressEntity(noUid=False))
    elif myarg in {'start', 'starttime', 'end', 'endtime`', 'range'}:
      startEndTime.Get(myarg)
    elif myarg == 'hasattachment':
      hasAttachment = True
    elif myarg == 'orderby':
      orderBy = getChoice(CHAT_SEARCHMESSAGES_ORDERBY_CHOICE_MAP, mapChoice=True)
    elif myarg in CHAT_SEARCHMESSAGES_VIEW_CHOICE_MAP:
      body['view'] = CHAT_SEARCHMESSAGES_VIEW_CHOICE_MAP[myarg]
    elif getFieldsList(myarg, CHAT_MESSAGES_FIELDS_CHOICE_MAP, fieldsList, initialField='name', onlyFieldsArg=True):
      pass
    else:
      FJQC.GetFormatJSONQuoteChar(myarg, True)
  if not keywordList:
    missingArgumentExit('keywords')
  if orderBy is not None:
    body['orderBy'] = f'{orderBy} desc'
  body['filter'] = f'({" ".join(keywordList)})'
  if spaceList:
    body['filter'] += ' AND ('
    for space in spaceList:
      body['filter'] += f'space.name = "{space}" OR '
    body['filter'] = body['filter'][:-4] + ')'
  if displayNameList:
    body['filter'] += ' AND ('
    for displayName in displayNameList:
      body['filter'] += f'space.display_name:{displayName}" {displayNameConjunction} '
    body['filter'] = body['filter'][:-(len(displayNameConjunction)+2)] + ')'
  if senderList:
    body['filter'] += ' AND ('
    for sender in senderList:
      body['filter'] += f'sender.name = "users/{sender}" OR '
    body['filter'] = body['filter'][:-4] + ')'
  if userMentionList:
    body['filter'] += ' AND ('
    for userMention in userMentionList:
      body['filter'] += f'annotations.user_mentions.user.name:"users/{userMention}" {userMentionConjunction} '
    body['filter'] = body['filter'][:-(len(userMentionConjunction)+2)] + ')'
  if startEndTime.startDateTime is not None or startEndTime.endDateTime is not None:
    body['filter'] += ' AND ('
    if startEndTime.startDateTime is not None:
      body['filter'] += f'createTime >= "{startEndTime.startDateTime}"'
      if startEndTime.endDateTime is not None:
        body['filter'] += ' AND '
    if startEndTime.endDateTime is not None:
      body['filter'] += f'createTime < "{startEndTime.endDateTime}"'
    body['filter'] += ')'
  if hasAttachment:
    body['filter'] += ' AND attachment:*'
  chatSenders = {}
  chatSpaces = {}
  fields = getItemFieldsFromFieldsList('results(message', fieldsList)
  if fields:
    fields += ')'
  i, count, users = getEntityArgument(users)
  for user in users:
    i += 1
    user, chat, kvList = buildChatServiceObject(API.CHAT_MESSAGES, user, i, count, [Ent.CHAT_SPACE, None])
    if not chat:
      continue
    _, chatsp, _ = buildChatServiceObject(API.CHAT_SPACES, user, i, count, [Ent.CHAT_SPACE, None])
    if not chat:
      continue
    try:
      results = callGAPIpages(chat.spaces().messages(), 'search', 'results',
                              pageMessage=_getChatPageMessage(Ent.CHAT_MESSAGE, user, i, count, body['filter']),
                              throwReasons=[GAPI.NOT_FOUND, GAPI.INVALID_ARGUMENT, GAPI.PERMISSION_DENIED],
                              retryReasons=GAPI.SERVICE_NOT_AVAILABLE_RETRY_REASONS,
                              parent='spaces/-', body=body, fields=fields, pageArgsInBody=True)
      for result in results:
        if 'sender' in result['message']:
          _getChatSenderEmail(cd, result['message']['sender'], chatSenders)
        if 'space' in result['message']:
          _getChatSpaceDisplayName(chatsp, result['message']['space'], chatSpaces)
    except (GAPI.notFound, GAPI.invalidArgument, GAPI.permissionDenied) as e:
      exitIfChatNotConfigured(chat, kvList, str(e), i, count)
      continue
    except GAPI.failedPrecondition:
      userChatServiceNotEnabledWarning(user, i, count)
      break
    if not csvPF:
      jcount = len(results)
      if not FJQC.formatJSON:
        entityPerformActionNumItems(kvList, jcount, Ent.CHAT_MESSAGE, i, count)
      Ind.Increment()
      j = 0
      for result in results:
        j += 1
        _showChatItem(result['message'], Ent.CHAT_MESSAGE, FJQC, j, jcount)
      Ind.Decrement()
    elif results:
      for result in results:
        _printChatItem(user, result['message'], parent, Ent.CHAT_MESSAGE, csvPF, FJQC)
    elif GC.Values[GC.CSV_OUTPUT_USERS_AUDIT]:
      csvPF.WriteRowNoFilter({'User': user})
  if csvPF:
    csvPF.writeCSVfile('Chat Messages')

# gam <UserTypeEntity> info chatevent name <ChatEvent>
#	[formatjson]
def infoChatEvent(users):
  FJQC = FormatJSONQuoteChar()
  name = None
  while Cmd.ArgumentsRemaining():
    myarg = getArgument()
    if myarg == 'name':
      name = getString(Cmd.OB_CHAT_EVENT)
    else:
      FJQC.GetFormatJSON(myarg)
  if not name:
    missingArgumentExit('name')
  i, count, users = getEntityArgument(users)
  for user in users:
    i += 1
    user, chat, kvList = buildChatServiceObject(API.CHAT_EVENTS, user, i, count, [Ent.CHAT_EVENT, name])
    if not chat:
      continue
    try:
      event = callGAPI(chat.spaces().spaceEvents(), 'get',
                       throwReasons=[GAPI.NOT_FOUND, GAPI.INVALID_ARGUMENT, GAPI.PERMISSION_DENIED, GAPI.FAILED_PRECONDITION],
                       name=name)
      if not FJQC.formatJSON:
        entityPerformAction(kvList, i, count)
      Ind.Increment()
      _showChatItem(event, Ent.CHAT_EVENT, FJQC)
      Ind.Decrement()
    except (GAPI.notFound, GAPI.invalidArgument, GAPI.permissionDenied) as e:
      exitIfChatNotConfigured(chat, kvList, str(e), i, count)
    except GAPI.failedPrecondition:
      userChatServiceNotEnabledWarning(user, i, count)

def doInfoChatEvent():
  infoChatEvent([None])

# gam <UserTypeEntity> show chatevents
#       <ChatSpace>+
#	filter <String>
#	[formatjson]
# gam <UserTypeEntity> print chatevents [todrive <ToDriveAttribute>*]
#       <ChatSpace>+
#	filter <String>
#	[formatjson [quotechar <Character>]]
def printShowChatEvents(users):
  csvPF = CSVPrintFile(['User', 'space.name', 'space.displayName', 'name']) if Act.csvFormat() else None
  FJQC = FormatJSONQuoteChar(csvPF)
  pfilter = None
  parentList = []
  while Cmd.ArgumentsRemaining():
    myarg = getArgument()
    if csvPF and myarg == 'todrive':
      csvPF.GetTodriveParameters()
    elif myarg == 'space' or myarg.startswith('spaces/') or myarg.startswith('space/'):
      parentList.append({'name': getSpaceName(myarg), 'displayName': ''})
    elif myarg =='filter':
      pfilter = getString(Cmd.OB_STRING)
    else:
      FJQC.GetFormatJSONQuoteChar(myarg, True)
  if not parentList:
    missingArgumentExit('space')
  if not pfilter:
    missingArgumentExit('filter')
  i, count, users = getEntityArgument(users)
  for user in users:
    i += 1
    user, chat, kvList = buildChatServiceObject(API.CHAT_EVENTS, user, i, count, [Ent.CHAT_SPACE, None])
    if not chat:
      continue
    _, chatspg, _ = buildChatServiceObject(API.CHAT_SPACES, user, i, count, None)
    if not chatspg:
      continue
    jcount = len(parentList)
    j = 0
    for parent in parentList:
      j += 1
      parentName = parent['name']
      kvList[-1] = parentName
      qfilter = f'{Ent.Singular(Ent.CHAT_SPACE)}: {parentName}, {pfilter}'
      try:
        if not parent['displayName']:
          space = callGAPI(chatspg.spaces(), 'get',
                           throwReasons=[GAPI.NOT_FOUND, GAPI.INVALID_ARGUMENT, GAPI.PERMISSION_DENIED, GAPI.FAILED_PRECONDITION],
                           name=parentName, fields='displayName')
          parent['displayName'] = space.get('displayName', 'None')
        events = callGAPIpages(chat.spaces().spaceEvents(), 'list', 'spaceEvents',
                               pageMessage=_getChatPageMessage(Ent.CHAT_EVENT, user, i, count, qfilter),
                               throwReasons=[GAPI.NOT_FOUND, GAPI.INVALID_ARGUMENT, GAPI.PERMISSION_DENIED],
                               retryReasons=GAPI.SERVICE_NOT_AVAILABLE_RETRY_REASONS,
                               pageSize=GC.Values[GC.CHAT_MAX_RESULTS], parent=parentName, filter=pfilter)
      except (GAPI.notFound, GAPI.invalidArgument, GAPI.permissionDenied) as e:
        exitIfChatNotConfigured(chat, kvList, str(e), i, count)
        continue
      except GAPI.failedPrecondition:
        userChatServiceNotEnabledWarning(user, i, count)
        break
      if not csvPF:
        kcount = len(events)
        if not FJQC.formatJSON:
          entityPerformActionNumItems(kvList, kcount, Ent.CHAT_EVENT, j, jcount)
        Ind.Increment()
        k = 0
        for event in events:
          k += 1
          event['space'] = {'name': parentName, 'displayName': parent['displayName']}
          _showChatItem(event, Ent.CHAT_EVENT, FJQC, k, kcount)
        Ind.Decrement()
      elif events:
        for event in events:
          _printChatItem(user, event, parent, Ent.CHAT_EVENT, csvPF, FJQC)
      elif GC.Values[GC.CSV_OUTPUT_USERS_AUDIT]:
        csvPF.WriteRowNoFilter({'User': user})
  if csvPF:
    csvPF.writeCSVfile('Chat Events')

