"""Chat space CRUD and listing.

Part of the _chat_tmp sub-package."""

"""GAM Google Chat management."""

import json
import sys
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

def getSpaceName(myarg):
  if myarg == 'space':
    chatSpace = _getMain().getString(Cmd.OB_CHAT_SPACE)
    if chatSpace.startswith('spaces/'):
      return chatSpace
    if not chatSpace.startswith('space/'):
      return 'spaces/'+chatSpace
    _, chatSpace = chatSpace.split('/', 1)
  else: # myarg.startswith('spaces/') or myarg.startswith('space/')
    _, chatSpace = Cmd.Previous().split('/', 1)
  return 'spaces/'+chatSpace

def  getChatSpaceParameters(myarg, body, typeChoicesMap, updateMask):
  if myarg == 'displayname':
    body['displayName'] = _getMain().getString(Cmd.OB_STRING, minLen=0, maxLen=128)
    updateMask.add('displayName')
  elif myarg == 'type':
    body['spaceType'] = _getMain().getChoice(typeChoicesMap, mapChoice=True)
    updateMask.add('spaceType')
  elif myarg == 'description':
    body.setdefault('spaceDetails', {})
    body['spaceDetails']['description'] = _getMain().getString(Cmd.OB_STRING, minLen=0, maxLen=150)
    updateMask.add('spaceDetails')
  elif myarg in {'guidelines', 'rules'}:
    body.setdefault('spaceDetails', {})
    body['spaceDetails']['guidelines'] = _getMain().getString(Cmd.OB_STRING, minLen=0, maxLen=5000)
    updateMask.add('spaceDetails')
  elif myarg == 'history':
    body['spaceHistoryState'] = 'HISTORY_ON' if _getMain().getBoolean() else 'HISTORY_OFF'
    updateMask.add('spaceHistoryState')
  elif myarg in {'audience', 'restricted'}:
    body['accessSettings']= {'audience': None}
    if myarg == 'audience':
      body['accessSettings']['audience'] = _getMain().getString(Cmd.OB_STRING, minLen=1, maxLen=100)
    updateMask.add('accessSettings.audience')
  else:
    return False
  return True

CHAT_MEMBER_ROLE_MAP = {
  'member': 'ROLE_MEMBER',
  'manager': 'ROLE_ASSISTANT_MANAGER',
  'owner': 'ROLE_MANAGER',
  }

CHAT_ROLE_ENTITY_TYPE_MAP = {
  'ROLE_MEMBER': Ent.CHAT_MEMBER_USER,
  'ROLE_ASSISTANT_MANAGER': Ent.CHAT_MANAGER_USER,
  'ROLE_MANAGER':  Ent.CHAT_OWNER_USER,
  }

CHAT_MEMBER_TYPE_MAP = {
  'bot': 'BOT',
  'human': 'HUMAN'
  }

CHAT_SPACE_TYPE_MAP = {
  'space': 'SPACE',
  'groupchat': 'GROUP_CHAT',
  'directmessage': 'DIRECT_MESSAGE',
  }

CHAT_SPACE_PREDEFINED_PERMS_MAP = {
  'announcement': 'ANNOUNCEMENT_SPACE',
  'collaboration': 'COLLABORATION_SPACE',
  }

CHAT_SPACE_MIN_MAX_MEMBERS = {
  'SPACE': {'min': 0, 'max': 20},
  'GROUP_CHAT': {'min': 2, 'max': 20},
  'DIRECT_MESSAGE': {'min': 1, 'max': 1},
  }
# gam <UserTypeEntity> create chatspace
#       [type <ChatSpaceType>] [announcement|collaboration]
#	[restricted|(audience <String>)]
#	[externalusersallowed <Boolean>]
#	[members <UserTypeEntity>]
#	[displayname <String>]
#	[description <String>] [guidelines|rules <String>]
#	[<ChatContent>]
#	[(csv [todrive <ToDriveAttribute>*] [formatjson [quotechar <Character>]] (addcsvdata <FieldName> <String>)*) | formatjson | returnidonly]
def createChatSpace(users):
  def _writeSpaceDetails(space, resp=None):
    baserow = {'User': user, 'name': space['name']}
    if resp:
      baserow['message.name'] = resp['name']
    if addCSVData:
      baserow.update(addCSVData)
    row = _getMain().flattenJSON(space, flattened=baserow.copy(), timeObjects=CHAT_TIME_OBJECTS)
    if not FJQC.formatJSON:
      csvPF.WriteRowTitles(row)
    else:
      row = baserow.copy()
      row['JSON'] = json.dumps(_getMain().cleanJSON(space, timeObjects=CHAT_TIME_OBJECTS), ensure_ascii=False, sort_keys=True)
      csvPF.WriteRowNoFilter(row)

  csvPF = None
  FJQC = _getMain().FormatJSONQuoteChar(csvPF)
  addCSVData = {}
  body = {'space': {'spaceType': CHAT_SPACE_TYPE_MAP['space'], 'displayName': ''}, 'requestId': str(uuid.uuid4())}
  members = []
  tbody = {}
  returnIdOnly = False
  updateMask = set()
  while Cmd.ArgumentsRemaining():
    myarg = _getMain().getArgument()
    if getChatSpaceParameters(myarg, body['space'], CHAT_SPACE_TYPE_MAP, updateMask):
      pass
    elif myarg in CHAT_SPACE_PREDEFINED_PERMS_MAP:
      body['space']['predefinedPermissionSettings'] = CHAT_SPACE_PREDEFINED_PERMS_MAP[myarg]
    elif myarg == 'externalusersallowed':
      body['space']['externalUserAllowed'] = _getMain().getBoolean()
    elif myarg == 'members':
      _, members = _getMain().getEntityToModify(defaultEntityType=Cmd.ENTITY_USERS)
    elif myarg == 'returnidonly':
      returnIdOnly = True
    elif myarg == 'csv':
      csvPF = _getMain().CSVPrintFile(['User', 'name'])
      FJQC = _getMain().FormatJSONQuoteChar(csvPF)
    elif csvPF and myarg == 'todrive':
      csvPF.GetTodriveParameters()
    elif csvPF and myarg == 'addcsvdata':
      _getMain().getAddCSVData(addCSVData)
    elif myarg in _getMain().SORF_TEXT_ARGUMENTS:
      tbody['text'] = _getMain().getStringOrFile(myarg, minLen=0, unescapeCRLF=True)[0]
    else:
      FJQC.GetFormatJSONQuoteChar(myarg)
  spaceType = body['space']['spaceType']
  jcount = len(members)
  if (jcount < CHAT_SPACE_MIN_MAX_MEMBERS[spaceType]['min'] or
      jcount > CHAT_SPACE_MIN_MAX_MEMBERS[spaceType]['max']):
    _getMain().systemErrorExit(_getMain().USAGE_ERROR_RC,
                    Msg.INVALID_NUMBER_OF_CHAT_SPACE_MEMBERS.format(Ent.Singular(Ent.CHAT_SPACE),
                                                                    spaceType, jcount,
                                                                    CHAT_SPACE_MIN_MAX_MEMBERS[spaceType]['min'],
                                                                    CHAT_SPACE_MIN_MAX_MEMBERS[spaceType]['max']))
  mtype = CHAT_MEMBER_TYPE_MAP['human']
  if members:
    body['memberships'] = []
    for member in members:
      name = _getMain().normalizeEmailAddressOrUID(member)
      body['memberships'].append({'member': {'name': f'users/{name}', 'type': mtype}})
  if spaceType == 'SPACE':
    if not body['space']['displayName']:
      _getMain().missingArgumentExit('displayname')
  elif spaceType == 'GROUP_CHAT':
    body['space'].pop('displayName', None)
    body['space'].pop('predefinedPermissionSettings', None)
  else: # DIRECT_MESSAGE
    body['space'].pop('displayName', None)
    body['space'].pop('spaceDetails', None)
    body['space'].pop('predefinedPermissionSettings', None)
    body['space']['singleUserBotDm'] = False
  if tbody:
    trimChatMessageIfRequired(tbody)
  if csvPF:
    if tbody:
      csvPF.AddTitle('message.name')
    if addCSVData:
      csvPF.AddTitles(sorted(addCSVData.keys()))
    if FJQC.formatJSON:
      csvPF.SetJSONTitles(csvPF.titlesList)
      csvPF.AddJSONTitle('JSON')
    csvPF.SetSortAllTitles()
  i, count, users = _getMain().getEntityArgument(users)
  for user in users:
    i += 1
    user, chat, kvList = buildChatServiceObject(API.CHAT_SPACES, user, i, count,
                                                [Ent.CHAT_SPACE, body['space'].get('displayName', spaceType)])
    if not chat:
      continue
    try:
      space = _getMain().callGAPI(chat.spaces(), 'setup',
                       throwReasons=[GAPI.NOT_FOUND, GAPI.INVALID_ARGUMENT, GAPI.PERMISSION_DENIED, GAPI.FAILED_PRECONDITION],
                       body=body)
      if returnIdOnly:
        _getMain().writeStdout(f'{space["name"]}\n')
      elif not csvPF:
        kvList[-1] = space['name']
        if not FJQC.formatJSON:
          _getMain().entityActionPerformed(kvList, i, count)
        Ind.Increment()
        _showChatItem(space, Ent.CHAT_SPACE, FJQC)
        Ind.Decrement()
      elif not tbody:
        _writeSpaceDetails(space, None)
    except (GAPI.notFound, GAPI.invalidArgument, GAPI.permissionDenied) as e:
      exitIfChatNotConfigured(chat, kvList, str(e), i, count)
      continue
    except GAPI.failedPrecondition:
      _getMain().userChatServiceNotEnabledWarning(user, i, count)
      continue
    if tbody:
      parent = space['name']
      _, chat, kvList = buildChatServiceObject(API.CHAT_MESSAGES, user, i, count,
                                               [Ent.CHAT_SPACE, body['space'].get('displayName', parent)])
      if not chat:
        if csvPF:
          _writeSpaceDetails(space, None)
        continue
      try:
        resp = _getMain().callGAPI(chat.spaces().messages(), 'create',
                        throwReasons=[GAPI.NOT_FOUND, GAPI.INVALID_ARGUMENT, GAPI.PERMISSION_DENIED],
                        parent=parent, requestId=str(uuid.uuid4()), body=tbody, fields='name')
        if returnIdOnly:
          _getMain().writeStdout(f'{resp["name"]}\n')
        elif not csvPF:
          if not FJQC.formatJSON:
            kvList.extend([Ent.CHAT_MESSAGE, resp['name']])
            _getMain().entityActionPerformed(kvList, i, count)
          else:
            _getMain().printLine(json.dumps(_getMain().cleanJSON(resp), ensure_ascii=False, sort_keys=True))
        else:
          _writeSpaceDetails(space, resp)
      except (GAPI.notFound, GAPI.invalidArgument, GAPI.permissionDenied) as e:
        exitIfChatNotConfigured(chat, kvList, str(e), i, count)
        if csvPF:
          _writeSpaceDetails(space, None)
  if csvPF:
    csvPF.writeCSVfile('Chat Spaces')

CHAT_UPDATE_SPACE_TYPE_MAP = {
  'space': 'SPACE',
  }

CHAT_SPACE_ROLE_PERMISSIONS_MAP = {
  'owners': 'managersAllowed',
  'managers': 'assistantManagersAllowed',
  'members': 'membersAllowed',
  }

CHAT_UPDATE_SPACE_PERMISSIONS_MAP = {
  'managemembersandgroups': 'manageMembersAndGroups',
  'modifyspacedetails': 'modifySpaceDetails',
  'togglehistory': 'toggleHistory',
  'useatmentionall': 'useAtMentionAll',
  'manageapps': 'manageApps',
  'managewebhooks': 'manageWebhooks',
  'replymessages': 'replyMessages',
  }

# gam <UserTypeEntity> update chatspace <ChatSpace>
#	[restricted|(audience <String>)]|
#	([displayname <String>]
#	 [type space]
#	 [description <String>] [guidelines|rules <String>]
#	 [history <Boolean>])
#	[managemembersandgroups owners|managers|members]
#	[modifyspacedetails owners|managers|members]
#	[togglehistory owners|managers|members]
#	[useatmentionall owners|managers|members]
#	[manageapps owners|managers|members]
#	[managewebhooks owners|managers|members]
#	[replymessages owners|managers|members]
#	[formatjson]
def updateChatSpace(users):
  FJQC = _getMain().FormatJSONQuoteChar()
  useAdminAccess, api, kwargsUAA = _getChatAdminAccess(API.CHAT_SPACES_ADMIN, API.CHAT_SPACES)
  name = None
  body = {}
  updateMask = set()
  while Cmd.ArgumentsRemaining():
    myarg = _getMain().getArgument()
    if myarg == 'space' or myarg.startswith('spaces/') or myarg.startswith('space/'):
      name = getSpaceName(myarg)
    elif getChatSpaceParameters(myarg, body, CHAT_UPDATE_SPACE_TYPE_MAP, updateMask):
      pass
    elif myarg in CHAT_UPDATE_SPACE_PERMISSIONS_MAP:
      body.setdefault('permissionSettings', {})
      permissionSetting = CHAT_UPDATE_SPACE_PERMISSIONS_MAP[myarg]
      role = _getMain().getChoice(CHAT_SPACE_ROLE_PERMISSIONS_MAP, mapChoice=True)
      body['permissionSettings'][permissionSetting] = {}
      body['permissionSettings'][permissionSetting][role] = True
      if role == 'membersAllowed':
        body['permissionSettings'][permissionSetting]['assistantManagersAllowed'] = True
        body['permissionSettings'][permissionSetting]['managersAllowed'] = True
      elif role == 'assistantManagersAllowed':
        body['permissionSettings'][permissionSetting]['managersAllowed'] = True
      updateMask.add(f'permissionSettings.{permissionSetting}')
    else:
      FJQC.GetFormatJSON(myarg)
  if not name:
    _getMain().missingArgumentExit('space')
  if 'accessSettings.audience' in updateMask:
    tempMask = updateMask-{'accessSettings.audience'}
    if tempMask:
      _getMain().usageErrorExit(Msg.ARE_MUTUALLY_EXCLUSIVE.format('restricted/audience', 'displayname,type,description,guidelines,history'))
  i, count, users = _getMain().getEntityArgument(users)
  if useAdminAccess:
    _chkChatAdminAccess(count)
  for user in users:
    i += 1
    user, chat, kvList = buildChatServiceObject(api, user, i, count, [Ent.CHAT_SPACE, name], useAdminAccess)
    if not chat:
      continue
    try:
      space = _getMain().callGAPI(chat.spaces(), 'patch',
                       throwReasons=[GAPI.NOT_FOUND, GAPI.INVALID_ARGUMENT, GAPI.PERMISSION_DENIED, GAPI.FAILED_PRECONDITION],
                       name=name, updateMask=','.join(updateMask), body=body, **kwargsUAA)
      if not FJQC.formatJSON:
        _getMain().entityActionPerformed(kvList, i, count)
      Ind.Increment()
      _showChatItem(space, Ent.CHAT_SPACE, FJQC)
      Ind.Decrement()
    except (GAPI.notFound, GAPI.invalidArgument, GAPI.permissionDenied) as e:
      exitIfChatNotConfigured(chat, kvList, str(e), i, count)
    except GAPI.failedPrecondition:
      _getMain().userChatServiceNotEnabledWarning(user, i, count)

# gam <UserTypeEntity> delete chatspace <ChatSpace>
# gam <UserItem> delete chatspace asadmin <ChatSpace>
def deleteChatSpace(users):
  name = None
  useAdminAccess, api, kwargsUAA = _getChatAdminAccess(API.CHAT_SPACES_DELETE_ADMIN, API.CHAT_SPACES_DELETE)
  while Cmd.ArgumentsRemaining():
    myarg = _getMain().getArgument()
    if myarg == 'space' or myarg.startswith('spaces/') or myarg.startswith('space/'):
      name = getSpaceName(myarg)
    else:
      _getMain().unknownArgumentExit()
  if not name:
    _getMain().missingArgumentExit('space')
  i, count, users = _getMain().getEntityArgument(users)
  if useAdminAccess:
    _chkChatAdminAccess(count)
  for user in users:
    i += 1
    user, chat, kvList = buildChatServiceObject(api, user, i, count, [Ent.CHAT_SPACE, name], useAdminAccess)
    if not chat:
      continue
    try:
      _getMain().callGAPI(chat.spaces(), 'delete',
               throwReasons=[GAPI.NOT_FOUND, GAPI.INVALID_ARGUMENT, GAPI.PERMISSION_DENIED, GAPI.FAILED_PRECONDITION],
               name=name, **kwargsUAA)
      _getMain().entityActionPerformed(kvList, i, count)
    except (GAPI.notFound, GAPI.invalidArgument, GAPI.permissionDenied) as e:
      exitIfChatNotConfigured(chat, kvList, str(e), i, count)
    except GAPI.failedPrecondition:
      _getMain().userChatServiceNotEnabledWarning(user, i, count)

CHAT_SPACES_FIELDS_CHOICE_MAP = {
  "accesssettings": "accessSettings",
  "admininstalled": "adminInstalled",
  "createtime": "createTime",
  "displayname": "displayName",
  "externaluserallowed": "externalUserAllowed",
  "importmode": "importMode",
  "lastactivetime": "lastActiveTime",
  "membershipcount": "membershipCount",
  "name": "name",
  "permissionsettings": "permissionSettings",
  "singleuserbotdm": "singleUserBotDm",
  "spacedetails": "spaceDetails",
  "spacehistorystate": "spaceHistoryState",
  "spacethreadingstate": "spaceThreadingState",
  "spacetype": "spaceType",
  "spaceuri": "spaceUri",
  "threaded": "spaceThreadingState",
  "type": "spaceType",
  }

# gam [<UserTypeEntity>] info chatspace <ChatSpace>
#	[fields <ChatSpaceFieldNameList>]
#	[formatjson]
# gam <UserItem> info chatspace asadmin <ChatSpace>
#	[fields <ChatSpaceFieldNameList>]
#	[formatjson]
def infoChatSpace(users, name=None):
  FJQC = _getMain().FormatJSONQuoteChar()
  if name is None:
    function = 'get'
    useAdminAccess, api, kwargsUAA = _getChatAdminAccess(API.CHAT_SPACES_ADMIN, API.CHAT_SPACES)
  else:
    function = 'findDirectMessage'
    useAdminAccess = None
    kwargsUAA = {}
    api = API.CHAT_SPACES
  fieldsList = []
  while Cmd.ArgumentsRemaining():
    myarg = _getMain().getArgument()
    if function == 'get' and (myarg == 'space' or myarg.startswith('spaces/') or myarg.startswith('space/')):
      name = getSpaceName(myarg)
    elif _getMain().getFieldsList(myarg, CHAT_SPACES_FIELDS_CHOICE_MAP, fieldsList, initialField='name', onlyFieldsArg=True):
      pass
    else:
      FJQC.GetFormatJSON(myarg)
  if function == 'get' and not name:
    _getMain().missingArgumentExit('space')
  fields = _getMain().getFieldsFromFieldsList(fieldsList)
  i, count, users = _getMain().getEntityArgument(users)
  if useAdminAccess:
    _chkChatAdminAccess(count)
  for user in users:
    i += 1
    user, chat, kvList = buildChatServiceObject(api, user, i, count, [Ent.CHAT_SPACE, name], useAdminAccess)
    if not chat:
      continue
    try:
      space = _getMain().callGAPI(chat.spaces(), function,
                       throwReasons=[GAPI.NOT_FOUND, GAPI.INVALID_ARGUMENT, GAPI.PERMISSION_DENIED, GAPI.FAILED_PRECONDITION],
                       name=name, fields=fields, **kwargsUAA)
      if not FJQC.formatJSON:
        _getMain().entityPerformAction(kvList, i, count)
      Ind.Increment()
      _showChatItem(space, Ent.CHAT_SPACE, FJQC)
      Ind.Decrement()
    except (GAPI.notFound, GAPI.invalidArgument, GAPI.permissionDenied) as e:
      exitIfChatNotConfigured(chat, kvList, str(e), i, count)
    except GAPI.failedPrecondition:
      _getMain().userChatServiceNotEnabledWarning(user, i, count)

def doInfoChatSpace():
  infoChatSpace([None])

# gam [<UserTypeEntity>] info chatspacedm <UserItem>
#	[fields <ChatSpaceFieldNameList>]
#	[formatjson]
def infoChatSpaceDM(users):
  cd = _getMain().buildGAPIObject(API.DIRECTORY)
  name = _getMain().convertEmailAddressToUID(_getMain().getEmailAddress(returnUIDprefix='uid:'), cd, 'user')
  infoChatSpace(users, f'users/{name}')

def _getChatSpaceListParms(myarg, kwargs):
  if myarg in {'type', 'types'}:
    for ctype in _getMain().getString(Cmd.OB_GROUP_ROLE_LIST).lower().replace(',', ' ').split():
      if ctype in CHAT_SPACE_TYPE_MAP:
        kwargs.setdefault('filter', '')
        if kwargs['filter']:
          kwargs['filter'] += ' OR '
        kwargs['filter'] += f'spaceType = "{CHAT_SPACE_TYPE_MAP[ctype]}"'
      else:
        _getMain().invalidChoiceExit(ctype, CHAT_SPACE_TYPE_MAP, True)
  else:
    return False
  return True

def _getChatSpaceSearchParms(myarg, queries, queryTimes, OBY):
  if myarg == 'orderby':
    OBY.GetChoice()
  elif  myarg == 'query':
    queries[0] += ' AND '+_getMain().getString(Cmd.OB_QUERY)
  elif myarg.startswith('querytime'):
    queryTimes[myarg] = _getMain().getTimeOrDeltaFromNow()
  else:
    return False
  return True

CHAT_SPACES_ADMIN_ORDERBY_CHOICE_MAP = {
  'createtime': 'createTime',
  'lastactivetime': 'lastActiveTime',
  'membershipcount': 'membershipCount.joined_direct_human_user_count'
  }

# gam [<UserTypeEntity>] show chatspaces
#	[types <ChatSpaceTypeList>]
#	[fields <ChatSpaceFieldNameList>] [showaccesssettings]
#	[formatjson]
# gam [<UserTypeEntity>] print chatspaces [todrive <ToDriveAttribute>*]
#	[types <ChatSpaceTypeList>]
#	[fields <ChatSpaceFieldNameList>] [showaccesssettings]
#	[formatjson [quotechar <Character>]]
# gam <UserItem> show chatspaces asadmin
#	[query <String>] [querytime<String> <Time>]
#	[orderby <ChatSpaceAdminOrderByFieldName> [ascending|descending]]
#	[fields <ChatSpaceFieldNameList>] [showaccesssettings]
#	[formatjson]
# gam <UserItem> print chatspaces asadmin [todrive <ToDriveAttribute>*]
#	[query <String>] [querytime<String> <Time>]
#	[orderby <ChatSpaceAdminOrderByFieldName> [ascending|descending]]
#	[fields <ChatSpaceFieldNameList>] [showaccesssettings]
#	[formatjson [quotechar <Character>]]
def printShowChatSpaces(users):
  csvPF = _getMain().CSVPrintFile(['User', 'name'] if not isinstance(users, list) else ['name']) if Act.csvFormat() else None
  FJQC = _getMain().FormatJSONQuoteChar(csvPF)
  OBY = _getMain().OrderBy(CHAT_SPACES_ADMIN_ORDERBY_CHOICE_MAP)
  useAdminAccess, api, kwargsCS = _getChatAdminAccess(API.CHAT_SPACES_ADMIN, API.CHAT_SPACES)
  kwargsSAS = {'useAdminAccess': useAdminAccess}
  fieldsList = []
  queries = []
  queryTimes = {}
  pfilter = ''
  showAccessSettings = False
  if useAdminAccess:
    function = 'search'
    queries = ['customer = "customers/my_customer" AND spaceType = "SPACE"']
  else:
    function = 'list'
  while Cmd.ArgumentsRemaining():
    myarg = _getMain().getArgument()
    if csvPF and myarg == 'todrive':
      csvPF.GetTodriveParameters()
    elif _getMain().getFieldsList(myarg, CHAT_SPACES_FIELDS_CHOICE_MAP, fieldsList, initialField='name', onlyFieldsArg=True):
      pass
    elif not useAdminAccess and _getChatSpaceListParms(myarg, kwargsCS):
      pass
    elif useAdminAccess and _getChatSpaceSearchParms(myarg, queries, queryTimes, OBY):
      pass
    elif myarg == 'showaccesssettings':
      showAccessSettings = True
    else:
      FJQC.GetFormatJSONQuoteChar(myarg, True)
  if showAccessSettings and fieldsList:
    fieldsList.extend(['name', 'spaceType'])
  fields = _getMain().getItemFieldsFromFieldsList('spaces', fieldsList)
  i, count, users = _getMain().getEntityArgument(users)
  if useAdminAccess:
    _chkChatAdminAccess(count)
    kwargsCS['orderBy'] = OBY.orderBy
    _getMain().substituteQueryTimes(queries, queryTimes)
    pfilter = kwargsCS['query'] = queries[0]
    kwargsCS['useAdminAccess'] = True
    sortName = 'displayName' if 'displayName' in fieldsList else 'name'
  else:
    sortName = 'name'
  for user in users:
    i += 1
    user, chat, kvList = buildChatServiceObject(api, user, i, count, None, useAdminAccess)
    if not chat:
      continue
    try:
      spaces = _getMain().callGAPIpages(chat.spaces(), function, 'spaces',
                             pageMessage=_getChatPageMessage(Ent.CHAT_SPACE, user, i, count, pfilter, useAdminAccess),
                             bailOnInternalError=True,
                             throwReasons=[GAPI.NOT_FOUND, GAPI.INVALID_ARGUMENT, GAPI.INTERNAL_ERROR,
                                           GAPI.PERMISSION_DENIED, GAPI.FAILED_PRECONDITION],
                             retryReasons=GAPI.SERVICE_NOT_AVAILABLE_RETRY_REASONS,
                             fields=fields, pageSize=GC.Values[GC.CHAT_MAX_RESULTS], **kwargsCS)
      if showAccessSettings:
        for space in spaces:
          if space['spaceType'] == 'SPACE':
            try:
              result = _getMain().callGAPI(chat.spaces(), 'get',
                                throwReasons=[GAPI.NOT_FOUND, GAPI.INVALID_ARGUMENT, GAPI.INTERNAL_ERROR,
                                              GAPI.PERMISSION_DENIED, GAPI.FAILED_PRECONDITION],
                                name=space['name'], fields='accessSettings', **kwargsSAS)
              space.update(result)
            except (GAPI.notFound, GAPI.invalidArgument, GAPI.internalError, GAPI.permissionDenied, GAPI.failedPrecondition):
              pass
    except (GAPI.notFound, GAPI.invalidArgument, GAPI.internalError, GAPI.permissionDenied) as e:
      exitIfChatNotConfigured(chat, kvList, str(e), i, count)
      continue
    except GAPI.failedPrecondition:
      _getMain().userChatServiceNotEnabledWarning(user, i, count)
      continue
    jcount = len(spaces)
    if jcount == 0:
      _getMain().setSysExitRC(_getMain().NO_ENTITIES_FOUND_RC)
    if not csvPF:
      if not FJQC.formatJSON:
        _getMain().entityPerformActionNumItems(kvList, jcount, Ent.CHAT_SPACE, i, count)
      Ind.Increment()
      j = 0
      for space in sorted(spaces, key=lambda k: k[sortName]):
        j += 1
        _showChatItem(space, Ent.CHAT_SPACE, FJQC, j, jcount)
      Ind.Decrement()
    else:
      for space in sorted(spaces, key=lambda k: k[sortName]):
        _printChatItem(user, space, None, Ent.CHAT_SPACE, csvPF, FJQC)
  if csvPF:
    csvPF.writeCSVfile('Chat Spaces')

def doPrintShowChatSpaces():
  printShowChatSpaces([None])

