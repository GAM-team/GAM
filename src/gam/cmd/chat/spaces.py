"""Chat space CRUD and listing.

Part of the _chat_tmp sub-package."""

"""GAM Google Chat management."""

import json
import uuid

from gamlib import api as API
from gamlib import settings as GC
from gamlib import gapi as GAPI
from gamlib import msgs as Msg
from gam.util.api import buildGAPIObject
from gam.util.api_call import callGAPI, callGAPIpages
from gam.util.args import (
    OrderBy,
    getAddCSVData,
    getArgument,
    getBoolean,
    getChoice,
    getEmailAddress,
    getString,
    getTimeOrDeltaFromNow,
    normalizeEmailAddressOrUID,
    substituteQueryTimes,
)
from gam.util.gdoc import SORF_TEXT_ARGUMENTS, getStringOrFile
from gam.util.csv_pf import (
    CSVPrintFile,
    FormatJSONQuoteChar,
    cleanJSON,
    flattenJSON,
    getFieldsFromFieldsList,
    getFieldsList,
    getItemFieldsFromFieldsList,
)
from gam.util.display import (
    entityActionPerformed,
    entityPerformAction,
    entityPerformActionNumItems,
    printLine,
    userChatServiceNotEnabledWarning,
)
from gam.util.entity import getEntityArgument, getEntityToModify
from gam.util.errors import (
    USAGE_ERROR_RC,
    invalidChoiceExit,
    missingArgumentExit,
    unknownArgumentExit,
    usageErrorExit,
)
from gam.util.output import setSysExitRC, systemErrorExit, writeStdout
from gam.constants import NO_ENTITIES_FOUND_RC

from gam.var import Act, Cmd, Ent, Ind
from gam.cmd.chat.setup import (
    CHAT_TIME_OBJECTS,
    _chkChatAdminAccess,
    _getChatAdminAccess,
    _getChatPageMessage,
    _printChatItem,
    _showChatItem,
    buildChatServiceObject,
    exitIfChatNotConfigured,
    getSpaceName,
    trimChatMessageIfRequired,
)
from gam.util.uid import convertEmailAddressToUID

def  getChatSpaceParameters(myarg, body, typeChoicesMap, updateMask):
  if myarg == 'displayname':
    body['displayName'] = getString(Cmd.OB_STRING, minLen=0, maxLen=128)
    updateMask.add('displayName')
  elif myarg == 'type':
    body['spaceType'] = getChoice(typeChoicesMap, mapChoice=True)
    updateMask.add('spaceType')
  elif myarg == 'description':
    body.setdefault('spaceDetails', {})
    body['spaceDetails']['description'] = getString(Cmd.OB_STRING, minLen=0, maxLen=150)
    updateMask.add('spaceDetails')
  elif myarg in {'guidelines', 'rules'}:
    body.setdefault('spaceDetails', {})
    body['spaceDetails']['guidelines'] = getString(Cmd.OB_STRING, minLen=0, maxLen=5000)
    updateMask.add('spaceDetails')
  elif myarg == 'history':
    body['spaceHistoryState'] = 'HISTORY_ON' if getBoolean() else 'HISTORY_OFF'
    updateMask.add('spaceHistoryState')
  elif myarg in {'audience', 'restricted'}:
    body['accessSettings']= {'audience': None}
    if myarg == 'audience':
      body['accessSettings']['audience'] = getString(Cmd.OB_STRING, minLen=1, maxLen=100)
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
    row = flattenJSON(space, flattened=baserow.copy(), timeObjects=CHAT_TIME_OBJECTS)
    if not FJQC.formatJSON:
      csvPF.WriteRowTitles(row)
    else:
      row = baserow.copy()
      row['JSON'] = json.dumps(cleanJSON(space, timeObjects=CHAT_TIME_OBJECTS), ensure_ascii=False, sort_keys=True)
      csvPF.WriteRowNoFilter(row)

  csvPF = None
  FJQC = FormatJSONQuoteChar(csvPF)
  addCSVData = {}
  body = {'space': {'spaceType': CHAT_SPACE_TYPE_MAP['space'], 'displayName': ''}, 'requestId': str(uuid.uuid4())}
  members = []
  tbody = {}
  returnIdOnly = False
  updateMask = set()
  while Cmd.ArgumentsRemaining():
    myarg = getArgument()
    if getChatSpaceParameters(myarg, body['space'], CHAT_SPACE_TYPE_MAP, updateMask):
      pass
    elif myarg in CHAT_SPACE_PREDEFINED_PERMS_MAP:
      body['space']['predefinedPermissionSettings'] = CHAT_SPACE_PREDEFINED_PERMS_MAP[myarg]
    elif myarg == 'externalusersallowed':
      body['space']['externalUserAllowed'] = getBoolean()
    elif myarg == 'members':
      _, members = getEntityToModify(defaultEntityType=Cmd.ENTITY_USERS)
    elif myarg == 'returnidonly':
      returnIdOnly = True
    elif myarg == 'csv':
      csvPF = CSVPrintFile(['User', 'name'])
      FJQC = FormatJSONQuoteChar(csvPF)
    elif csvPF and myarg == 'todrive':
      csvPF.GetTodriveParameters()
    elif csvPF and myarg == 'addcsvdata':
      getAddCSVData(addCSVData)
    elif myarg in SORF_TEXT_ARGUMENTS:
      tbody['text'] = getStringOrFile(myarg, minLen=0, unescapeCRLF=True)[0]
    else:
      FJQC.GetFormatJSONQuoteChar(myarg)
  spaceType = body['space']['spaceType']
  jcount = len(members)
  if (jcount < CHAT_SPACE_MIN_MAX_MEMBERS[spaceType]['min'] or
      jcount > CHAT_SPACE_MIN_MAX_MEMBERS[spaceType]['max']):
    systemErrorExit(USAGE_ERROR_RC,
                    Msg.INVALID_NUMBER_OF_CHAT_SPACE_MEMBERS.format(Ent.Singular(Ent.CHAT_SPACE),
                                                                    spaceType, jcount,
                                                                    CHAT_SPACE_MIN_MAX_MEMBERS[spaceType]['min'],
                                                                    CHAT_SPACE_MIN_MAX_MEMBERS[spaceType]['max']))
  mtype = CHAT_MEMBER_TYPE_MAP['human']
  if members:
    body['memberships'] = []
    for member in members:
      name = normalizeEmailAddressOrUID(member)
      body['memberships'].append({'member': {'name': f'users/{name}', 'type': mtype}})
  if spaceType == 'SPACE':
    if not body['space']['displayName']:
      missingArgumentExit('displayname')
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
  i, count, users = getEntityArgument(users)
  for user in users:
    i += 1
    user, chat, kvList = buildChatServiceObject(API.CHAT_SPACES, user, i, count,
                                                [Ent.CHAT_SPACE, body['space'].get('displayName', spaceType)])
    if not chat:
      continue
    try:
      space = callGAPI(chat.spaces(), 'setup',
                       throwReasons=[GAPI.NOT_FOUND, GAPI.INVALID_ARGUMENT, GAPI.PERMISSION_DENIED, GAPI.FAILED_PRECONDITION],
                       body=body)
      if returnIdOnly:
        writeStdout(f'{space["name"]}\n')
      elif not csvPF:
        kvList[-1] = space['name']
        if not FJQC.formatJSON:
          entityActionPerformed(kvList, i, count)
        Ind.Increment()
        _showChatItem(space, Ent.CHAT_SPACE, FJQC)
        Ind.Decrement()
      elif not tbody:
        _writeSpaceDetails(space, None)
    except (GAPI.notFound, GAPI.invalidArgument, GAPI.permissionDenied) as e:
      exitIfChatNotConfigured(chat, kvList, str(e), i, count)
      continue
    except GAPI.failedPrecondition:
      userChatServiceNotEnabledWarning(user, i, count)
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
        resp = callGAPI(chat.spaces().messages(), 'create',
                        throwReasons=[GAPI.NOT_FOUND, GAPI.INVALID_ARGUMENT, GAPI.PERMISSION_DENIED],
                        parent=parent, requestId=str(uuid.uuid4()), body=tbody, fields='name')
        if returnIdOnly:
          writeStdout(f'{resp["name"]}\n')
        elif not csvPF:
          if not FJQC.formatJSON:
            kvList.extend([Ent.CHAT_MESSAGE, resp['name']])
            entityActionPerformed(kvList, i, count)
          else:
            printLine(json.dumps(cleanJSON(resp), ensure_ascii=False, sort_keys=True))
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
  FJQC = FormatJSONQuoteChar()
  useAdminAccess, api, kwargsUAA = _getChatAdminAccess(API.CHAT_SPACES_ADMIN, API.CHAT_SPACES)
  name = None
  body = {}
  updateMask = set()
  while Cmd.ArgumentsRemaining():
    myarg = getArgument()
    if myarg == 'space' or myarg.startswith('spaces/') or myarg.startswith('space/'):
      name = getSpaceName(myarg)
    elif getChatSpaceParameters(myarg, body, CHAT_UPDATE_SPACE_TYPE_MAP, updateMask):
      pass
    elif myarg in CHAT_UPDATE_SPACE_PERMISSIONS_MAP:
      body.setdefault('permissionSettings', {})
      permissionSetting = CHAT_UPDATE_SPACE_PERMISSIONS_MAP[myarg]
      role = getChoice(CHAT_SPACE_ROLE_PERMISSIONS_MAP, mapChoice=True)
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
    missingArgumentExit('space')
  if 'accessSettings.audience' in updateMask:
    tempMask = updateMask-{'accessSettings.audience'}
    if tempMask:
      usageErrorExit(Msg.ARE_MUTUALLY_EXCLUSIVE.format('restricted/audience', 'displayname,type,description,guidelines,history'))
  i, count, users = getEntityArgument(users)
  if useAdminAccess:
    _chkChatAdminAccess(count)
  for user in users:
    i += 1
    user, chat, kvList = buildChatServiceObject(api, user, i, count, [Ent.CHAT_SPACE, name], useAdminAccess)
    if not chat:
      continue
    try:
      space = callGAPI(chat.spaces(), 'patch',
                       throwReasons=[GAPI.NOT_FOUND, GAPI.INVALID_ARGUMENT, GAPI.PERMISSION_DENIED, GAPI.FAILED_PRECONDITION],
                       name=name, updateMask=','.join(updateMask), body=body, **kwargsUAA)
      if not FJQC.formatJSON:
        entityActionPerformed(kvList, i, count)
      Ind.Increment()
      _showChatItem(space, Ent.CHAT_SPACE, FJQC)
      Ind.Decrement()
    except (GAPI.notFound, GAPI.invalidArgument, GAPI.permissionDenied) as e:
      exitIfChatNotConfigured(chat, kvList, str(e), i, count)
    except GAPI.failedPrecondition:
      userChatServiceNotEnabledWarning(user, i, count)

# gam <UserTypeEntity> delete chatspace <ChatSpace>
# gam <UserItem> delete chatspace asadmin <ChatSpace>
def deleteChatSpace(users):
  name = None
  useAdminAccess, api, kwargsUAA = _getChatAdminAccess(API.CHAT_SPACES_DELETE_ADMIN, API.CHAT_SPACES_DELETE)
  while Cmd.ArgumentsRemaining():
    myarg = getArgument()
    if myarg == 'space' or myarg.startswith('spaces/') or myarg.startswith('space/'):
      name = getSpaceName(myarg)
    else:
      unknownArgumentExit()
  if not name:
    missingArgumentExit('space')
  i, count, users = getEntityArgument(users)
  if useAdminAccess:
    _chkChatAdminAccess(count)
  for user in users:
    i += 1
    user, chat, kvList = buildChatServiceObject(api, user, i, count, [Ent.CHAT_SPACE, name], useAdminAccess)
    if not chat:
      continue
    try:
      callGAPI(chat.spaces(), 'delete',
               throwReasons=[GAPI.NOT_FOUND, GAPI.INVALID_ARGUMENT, GAPI.PERMISSION_DENIED, GAPI.FAILED_PRECONDITION],
               name=name, **kwargsUAA)
      entityActionPerformed(kvList, i, count)
    except (GAPI.notFound, GAPI.invalidArgument, GAPI.permissionDenied) as e:
      exitIfChatNotConfigured(chat, kvList, str(e), i, count)
    except GAPI.failedPrecondition:
      userChatServiceNotEnabledWarning(user, i, count)

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
  FJQC = FormatJSONQuoteChar()
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
    myarg = getArgument()
    if function == 'get' and (myarg == 'space' or myarg.startswith('spaces/') or myarg.startswith('space/')):
      name = getSpaceName(myarg)
    elif getFieldsList(myarg, CHAT_SPACES_FIELDS_CHOICE_MAP, fieldsList, initialField='name', onlyFieldsArg=True):
      pass
    else:
      FJQC.GetFormatJSON(myarg)
  if function == 'get' and not name:
    missingArgumentExit('space')
  fields = getFieldsFromFieldsList(fieldsList)
  i, count, users = getEntityArgument(users)
  if useAdminAccess:
    _chkChatAdminAccess(count)
  for user in users:
    i += 1
    user, chat, kvList = buildChatServiceObject(api, user, i, count, [Ent.CHAT_SPACE, name], useAdminAccess)
    if not chat:
      continue
    try:
      space = callGAPI(chat.spaces(), function,
                       throwReasons=[GAPI.NOT_FOUND, GAPI.INVALID_ARGUMENT, GAPI.PERMISSION_DENIED, GAPI.FAILED_PRECONDITION],
                       name=name, fields=fields, **kwargsUAA)
      if not FJQC.formatJSON:
        entityPerformAction(kvList, i, count)
      Ind.Increment()
      _showChatItem(space, Ent.CHAT_SPACE, FJQC)
      Ind.Decrement()
    except (GAPI.notFound, GAPI.invalidArgument, GAPI.permissionDenied) as e:
      exitIfChatNotConfigured(chat, kvList, str(e), i, count)
    except GAPI.failedPrecondition:
      userChatServiceNotEnabledWarning(user, i, count)

def doInfoChatSpace():
  infoChatSpace([None])

# gam [<UserTypeEntity>] info chatspacedm <UserItem>
#	[fields <ChatSpaceFieldNameList>]
#	[formatjson]
def infoChatSpaceDM(users):
  cd = buildGAPIObject(API.DIRECTORY)
  name = convertEmailAddressToUID(getEmailAddress(returnUIDprefix='uid:'), cd, 'user')
  infoChatSpace(users, f'users/{name}')

def _getChatSpaceListParms(myarg, kwargs):
  if myarg in {'type', 'types'}:
    for ctype in getString(Cmd.OB_GROUP_ROLE_LIST).lower().replace(',', ' ').split():
      if ctype in CHAT_SPACE_TYPE_MAP:
        kwargs.setdefault('filter', '')
        if kwargs['filter']:
          kwargs['filter'] += ' OR '
        kwargs['filter'] += f'spaceType = "{CHAT_SPACE_TYPE_MAP[ctype]}"'
      else:
        invalidChoiceExit(ctype, CHAT_SPACE_TYPE_MAP, True)
  else:
    return False
  return True

def _getChatSpaceSearchParms(myarg, queries, queryTimes, OBY):
  if myarg == 'orderby':
    OBY.GetChoice()
  elif  myarg == 'query':
    queries[0] += ' AND '+getString(Cmd.OB_QUERY)
  elif myarg.startswith('querytime'):
    queryTimes[myarg] = getTimeOrDeltaFromNow()
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
  csvPF = CSVPrintFile(['User', 'name'] if not isinstance(users, list) else ['name']) if Act.csvFormat() else None
  FJQC = FormatJSONQuoteChar(csvPF)
  OBY = OrderBy(CHAT_SPACES_ADMIN_ORDERBY_CHOICE_MAP)
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
    myarg = getArgument()
    if csvPF and myarg == 'todrive':
      csvPF.GetTodriveParameters()
    elif getFieldsList(myarg, CHAT_SPACES_FIELDS_CHOICE_MAP, fieldsList, initialField='name', onlyFieldsArg=True):
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
  fields = getItemFieldsFromFieldsList('spaces', fieldsList)
  i, count, users = getEntityArgument(users)
  if useAdminAccess:
    _chkChatAdminAccess(count)
    kwargsCS['orderBy'] = OBY.orderBy
    substituteQueryTimes(queries, queryTimes)
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
      spaces = callGAPIpages(chat.spaces(), function, 'spaces',
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
              result = callGAPI(chat.spaces(), 'get',
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
      userChatServiceNotEnabledWarning(user, i, count)
      continue
    jcount = len(spaces)
    if jcount == 0:
      setSysExitRC(NO_ENTITIES_FOUND_RC)
    if not csvPF:
      if not FJQC.formatJSON:
        entityPerformActionNumItems(kvList, jcount, Ent.CHAT_SPACE, i, count)
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

