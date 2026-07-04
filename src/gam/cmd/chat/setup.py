"""Chat setup, emoji, and section management.

Part of the _chat_tmp sub-package."""

"""GAM Google Chat management."""

import re
import json
import sys
import base64
import os

from gamlib import api as API
from gamlib import settings as GC
from gamlib import gapi as GAPI
from gamlib import state as GM
from gamlib import msgs as Msg
from gam.util.api import buildGAPIObject
from gam.util.svcacct import buildGAPIServiceObject
from gam.util.api_call import callGAPI, callGAPIitems, callGAPIpages
from gam.util.args import (
    UTF8,
    checkArgumentPresent,
    checkForExtraneousArguments,
    getArgument,
    getChoice,
    getInteger,
    getString,
)
from gam.util.csv_pf import (
    CSVPrintFile,
    FormatJSONQuoteChar,
    cleanJSON,
    flattenJSON,
    showJSON,
)
from gam.util.display import (
    entityActionFailedWarning,
    entityActionNotPerformedWarning,
    entityActionPerformed,
    entityModifierItemValueListActionPerformed,
    entityPerformAction,
    entityPerformActionNumItems,
    getPageMessage,
    getPageMessageForWhom,
    printEntity,
    printGettingAllAccountEntities,
    printGettingAllEntityItemsForWhom,
    printLine,
    userChatServiceNotEnabledWarning,
)
from gam.util.entity import getEntityArgument, splitEmailAddressOrUID
from gam.util.errors import entityDoesNotExistExit, missingArgumentExit, unknownArgumentExit, usageErrorExit
from gam.util.fileio import setFilePath
from gam.util.output import setSysExitRC, systemErrorExit, writeStdout
from gam.constants import ADMIN_ACCESS_OPTIONS, API_ACCESS_DENIED_RC, GOOGLE_API_ERROR_RC, NO_ENTITIES_FOUND_RC
from gam.util.tags import _substituteForUser

from gam.var import Act, Cmd, Ent, Ind

def buildChatServiceObject(api=API.CHAT, user=None, i=0, count=0, entityTypeList=None, useAdminAccess=False):
  if user is None:
    _, chat = buildGAPIServiceObject(API.CHAT, user)
    kvList = [Ent.CHAT_BOT, None]
  else:
    user, chat = buildGAPIServiceObject(api, user, i, count)
    if not useAdminAccess:
      kvList = [Ent.USER, user]
    else:
      kvList = [Ent.CHAT_ADMIN, f'{user}(asadmin)']
  if entityTypeList is not None:
    kvList.extend(entityTypeList)
  return user, chat, kvList

def _getChatPageMessage(entityType, user, i, count, pfilter, useAdminAccess=False):
  if user is not None:
    printGettingAllEntityItemsForWhom(entityType, user if not useAdminAccess else f'{user}(asadmin)', i, count, pfilter)
    return getPageMessageForWhom()
  printGettingAllAccountEntities(entityType, pfilter)
  return getPageMessage()

def setupChatURL(chat):
  return f'https://console.cloud.google.com/apis/api/chat.googleapis.com/hangouts-chat?project={chat._http.credentials.project_id}'

def exitIfChatNotConfigured(chat, kvList, errMsg, i, count):
  if (('No bot associated with this project.' in errMsg) or
      ('Invalid project number.' in errMsg) or
      ('Google Chat app not found.' in errMsg)):
    systemErrorExit(API_ACCESS_DENIED_RC, Msg.TO_SET_UP_GOOGLE_CHAT.format(setupChatURL(chat), GM.Globals[GM.OAUTH2SERVICE_JSON_DATA]['project_id']))
  entityActionFailedWarning(kvList, errMsg, i, count)

def _getChatAdminAccess(adminAPI, userAPI):
  if checkArgumentPresent(ADMIN_ACCESS_OPTIONS) or GC.Values[GC.USE_CHAT_ADMIN_ACCESS]:
    return (True, adminAPI, {'useAdminAccess': True})
  return (False, userAPI, {})

def _chkChatAdminAccess(count):
  if count != 1:
    usageErrorExit(Msg.CHAT_ADMIN_ACCESS_LIMITED_TO_ONE_USER.format(count))

def _cleanChatSpace(space):
  space.pop('type', None)
  space.pop('threaded', None)

def _cleanChatMessage(message):
  message.pop('cards', None)

CHAT_TIME_OBJECTS = {'createTime', 'deleteTime', 'eventTime', 'lastActiveTime', 'lastUpdateTime'}

def _showChatItem(citem, entityType, FJQC, i=0, count=0):
  if entityType == Ent.CHAT_SPACE:
    _cleanChatSpace(citem)
    dictObjectsKey = {None: 'displayName'}
  elif entityType == Ent.CHAT_MESSAGE:
    _cleanChatMessage(citem)
    dictObjectsKey = {None: 'text'}
  else:
    dictObjectsKey={}
  if FJQC.formatJSON:
    printLine(json.dumps(cleanJSON(citem, timeObjects=CHAT_TIME_OBJECTS), ensure_ascii=False, sort_keys=True))
    return
  printEntity([entityType, citem['name']], i, count)
  Ind.Increment()
  showJSON(None, citem, timeObjects=CHAT_TIME_OBJECTS, dictObjectsKey=dictObjectsKey)
  Ind.Decrement()

def _printChatItem(user, citem, parent, entityType, csvPF, FJQC, addCSVData=None):
  if entityType == Ent.CHAT_SPACE:
    _cleanChatSpace(citem)
    baserow = {'User': user} if user is not None else {}
  elif entityType in {Ent.CHAT_SECTION, Ent.CHAT_SECTION_ITEM}:
    baserow = {'User': user}
  elif entityType == Ent.CHAT_EMOJI:
    baserow = {'User': user, 'name': citem['name'], 'emojiName': citem['emojiName']}
  else:
    if user is not None:
      baserow = {'User': user, 'space.name': parent['name'], 'space.displayName': parent['displayName']}
    else:
      baserow = {'space.name': parent['name'], 'space.displayName': parent['displayName']}
    if entityType == Ent.CHAT_MEMBER:
      if addCSVData:
        baserow.update(addCSVData)
    elif entityType == Ent.CHAT_MESSAGE:
      _cleanChatMessage(citem)
  row = flattenJSON(citem, flattened=baserow.copy(), timeObjects=CHAT_TIME_OBJECTS)
  if not FJQC.formatJSON:
    csvPF.WriteRowTitles(row)
  elif csvPF.CheckRowTitles(row):
    row = baserow.copy()
    row.update({'name': citem['name'],
                'JSON': json.dumps(cleanJSON(citem, timeObjects=CHAT_TIME_OBJECTS), ensure_ascii=False, sort_keys=True)})
    csvPF.WriteRowNoFilter(row)

def _getValidateEmojiName():
  name = getString(Cmd.OB_CHAT_EMOJI_NAME)
  if re.match(r'^:[0-9a-z_-]+:$', name):
    return name
  Cmd.Backup()
  usageErrorExit(Msg.INVALID_EMOJI_NAME.format(name))

# gam <UserTypeEntity> create chatemoji <ChatEmojiName>
#	 ([drivedir|(sourcefolder <FilePath>)] [filename <FileNamePattern>])
#	[formatjson]
def createChatEmoji(users):
  FJQC = FormatJSONQuoteChar()
  name = _getValidateEmojiName()
  body = {'emojiName': name, 'payload': {'filename': '', 'fileContent': ''}}
  sourceFolder = os.getcwd()
  filenamePattern = '#email#.jpg'
  while Cmd.ArgumentsRemaining():
    myarg = getArgument()
    if myarg == 'drivedir':
      sourceFolder = GC.Values[GC.DRIVE_DIR]
    elif myarg == 'sourcefolder':
      sourceFolder = setFilePath(getString(Cmd.OB_FILE_PATH), GC.INPUT_DIR)
      if not os.path.isdir(sourceFolder):
        entityDoesNotExistExit(Ent.DIRECTORY, sourceFolder)
    elif myarg == 'filename':
      filenamePattern = getString(Cmd.OB_FILE_NAME_PATTERN)
    else:
      FJQC.GetFormatJSON(myarg)
  i, count, users = getEntityArgument(users)
  for user in users:
    i += 1
    user, chat, kvList = buildChatServiceObject(API.CHAT_CUSTOM_EMOJIS, user, i, count, [Ent.CHAT_EMOJI, name])
    if not chat:
      continue
    user, userName, _ = splitEmailAddressOrUID(user)
    filename = os.path.join(sourceFolder, _substituteForUser(filenamePattern, user, userName))
    try:
      with open(filename, 'rb') as f:
        image_data = f.read()
    except (OSError, IOError) as e:
      entityActionFailedWarning([Ent.USER, user, Ent.CHAT_EMOJI, filename], str(e), i, count)
      continue
    body['payload'] = {'filename': os.path.basename(filename),
                       'fileContent':base64.urlsafe_b64encode(image_data).decode(UTF8)}
    try:
      emoji = callGAPI(chat.customEmojis(), 'create',
                       throwReasons=[GAPI.ALREADY_EXISTS, GAPI.INVALID_ARGUMENT, GAPI.PERMISSION_DENIED, GAPI.FAILED_PRECONDITION],
                       body=body)
      _showChatItem(emoji, Ent.CHAT_EMOJI, FJQC, i, count)
    except (GAPI.alreadyExists, GAPI.invalidArgument, GAPI.permissionDenied) as e:
      exitIfChatNotConfigured(chat, kvList, str(e), i, count)
    except GAPI.failedPrecondition:
      userChatServiceNotEnabledWarning(user, i, count)

def getEmojiName(myarg):
  if myarg == 'emojiname':
    name = _getValidateEmojiName()
    return 'customEmojis/'+name
  _, chatEmoji = Cmd.Previous().split('/', 1)
  return 'customEmojis/'+chatEmoji

# gam <UserTypeEntity> delete chatemoji <ChatEmoji>
def deleteChatEmoji(users):
  name = None
  while Cmd.ArgumentsRemaining():
    myarg = getArgument()
    if myarg == 'emojiname':
      name = getEmojiName(myarg)
    elif myarg.startswith('customemojis/'):
      name = getEmojiName(myarg)
    else:
      unknownArgumentExit()
  if not name:
    missingArgumentExit('ChatEmoji')
  i, count, users = getEntityArgument(users)
  for user in users:
    i += 1
    user, chat, kvList = buildChatServiceObject(API.CHAT_CUSTOM_EMOJIS, user, i, count, [Ent.CHAT_EMOJI, name])
    if not chat:
      continue
    try:
      callGAPI(chat.customEmojis(), 'delete',
               throwReasons=[GAPI.NOT_FOUND, GAPI.INVALID_ARGUMENT, GAPI.PERMISSION_DENIED, GAPI.FAILED_PRECONDITION],
               name=name)
      entityActionPerformed(kvList, i, count)
    except (GAPI.notFound, GAPI.invalidArgument, GAPI.permissionDenied) as e:
      exitIfChatNotConfigured(chat, kvList, str(e), i, count)
    except GAPI.failedPrecondition:
      userChatServiceNotEnabledWarning(user, i, count)

# gam <UserTypeEntity> info chatemoji <ChatEmoji>
#	[formatjson]
def infoChatEmoji(users):
  FJQC = FormatJSONQuoteChar()
  name = None
  while Cmd.ArgumentsRemaining():
    myarg = getArgument()
    if myarg == 'emojiname':
      name = getEmojiName(myarg)
    elif myarg.startswith('customemojis/'):
      name = getEmojiName(myarg)
    else:
      FJQC.GetFormatJSON(myarg)
  if not name:
    missingArgumentExit('ChatEmoji')
  i, count, users = getEntityArgument(users)
  for user in users:
    i += 1
    user, chat, kvList = buildChatServiceObject(API.CHAT_CUSTOM_EMOJIS, user, i, count, [Ent.CHAT_EMOJI, name])
    if not chat:
      continue
    try:
      emoji = callGAPI(chat.customEmojis(), 'get',
                       throwReasons=[GAPI.NOT_FOUND, GAPI.INVALID_ARGUMENT, GAPI.PERMISSION_DENIED, GAPI.FAILED_PRECONDITION],
                       name=name)
      if not FJQC.formatJSON:
        entityPerformAction(kvList, i, count)
      _showChatItem(emoji, Ent.CHAT_EMOJI, FJQC, i, count)
    except (GAPI.notFound, GAPI.invalidArgument, GAPI.permissionDenied) as e:
      exitIfChatNotConfigured(chat, kvList, str(e), i, count)
    except GAPI.failedPrecondition:
      userChatServiceNotEnabledWarning(user, i, count)

CHAT_EMOJI_SHOW_CREATED_BY_CHOICE_MAP = {
  'any': None,
  'me': 'creator("users/me")',
  'others': 'NOT creator("users/me")'
  }

# gam <UserTypeEntity> show chatemojis
#	[showcreatedby any|me|others]
#	[formatjson]
# gam <UserTypeEntity> print chatemojis [todrive <ToDriveAttribute>*]
#	[showcreatedby any|me|others]
#	[formatjson [quotechar <Character>]]
def printShowChatEmojis(users):
  csvPF = CSVPrintFile(['User', 'name', 'emojiName'])  if Act.csvFormat() else None
  FJQC = FormatJSONQuoteChar(csvPF)
  pfilter = CHAT_EMOJI_SHOW_CREATED_BY_CHOICE_MAP['me']
  while Cmd.ArgumentsRemaining():
    myarg = getArgument()
    if csvPF and myarg == 'todrive':
      csvPF.GetTodriveParameters()
    elif myarg =='showcreatedby':
      pfilter = getChoice(CHAT_EMOJI_SHOW_CREATED_BY_CHOICE_MAP, mapChoice=True)
    else:
      FJQC.GetFormatJSONQuoteChar(myarg, True)
  i, count, users = getEntityArgument(users)
  for user in users:
    i += 1
    user, chat, kvList = buildChatServiceObject(API.CHAT_CUSTOM_EMOJIS, user, i, count, [Ent.CHAT_EMOJI, None])
    if not chat:
      continue
    try:
      emojis = callGAPIpages(chat.customEmojis(), 'list', 'customEmojis',
                             pageMessage=_getChatPageMessage(Ent.CHAT_EMOJI, user, i, count, pfilter),
                             throwReasons=[GAPI.NOT_FOUND, GAPI.INVALID_ARGUMENT,
                                           GAPI.PERMISSION_DENIED, GAPI.FAILED_PRECONDITION],
                             retryReasons=GAPI.SERVICE_NOT_AVAILABLE_RETRY_REASONS,
                             pageSize=GC.Values[GC.CHAT_MAX_RESULTS], filter=pfilter)
    except (GAPI.notFound, GAPI.invalidArgument, GAPI.permissionDenied) as e:
      exitIfChatNotConfigured(chat, kvList, str(e), i, count)
      continue
    except GAPI.failedPrecondition:
      userChatServiceNotEnabledWarning(user, i, count)
      break
    if not csvPF:
      jcount = len(emojis)
      if not FJQC.formatJSON:
        entityPerformActionNumItems(kvList, jcount, Ent.CHAT_EMOJI, i, count)
      Ind.Increment()
      j = 0
      for emoji in sorted(emojis, key=lambda k: k['emojiName']):
        j += 1
        _showChatItem(emoji, Ent.CHAT_EMOJI, FJQC, j, jcount)
      Ind.Decrement()
    elif emojis:
      for emoji in sorted(emojis, key=lambda k: k['emojiName']):
        _printChatItem(user, emoji, '', Ent.CHAT_EMOJI, csvPF, FJQC)
    elif GC.Values[GC.CSV_OUTPUT_USERS_AUDIT]:
      csvPF.WriteRowNoFilter({'User': user})
  if csvPF:
    csvPF.writeCSVfile('Chat Custom Emojis')

# gam setup chat
def doSetupChat():
  checkForExtraneousArguments()
  _, chat , _ = buildChatServiceObject()
  writeStdout(Msg.TO_SET_UP_GOOGLE_CHAT.format(setupChatURL(chat), GM.Globals[GM.OAUTH2SERVICE_JSON_DATA]['project_id']))

def getChatSectionName():
  if not Cmd.ArgumentsRemaining():
    missingArgumentExit('<ChatSection>')
  myarg = Cmd.Current().lower()
  Cmd.Advance()
  if myarg == 'section':
    chatSection = getString(Cmd.OB_CHAT_SECTION)
    if chatSection.startswith('sections/') or chatSection.startswith('users/'):
      return chatSection
    return 'sections/'+chatSection
  if myarg.startswith('sections/') or myarg.startswith('users/'):
    return Cmd.Previous()
  return 'sections/'+Cmd.Previous()

CHAT_SECTION_POSITION = {
  'start': 'START',
  'end': 'END'
  }

# gam <UserTypeEntity> create chatsection
#	displayname <String>
#	[formatjson|returnidonly]
# gam <UserTypeEntity> update chatsection <ChatSection>
#	[displayname <String>]
#	[(sortorder <Integer>)|(position start|end)]
#	[formatjson]
def createUpdateChatSection(users):
  updateCmd = Act.Get() == Act.UPDATE
  FJQC = FormatJSONQuoteChar()
  name = None
  body = {}
  posbody = {}
  posloc = None
  returnIdOnly = False
  updateMask = set()
  if updateCmd:
    name = getChatSectionName()
  while Cmd.ArgumentsRemaining():
    myarg = getArgument()
    if myarg == 'displayname':
      body['displayName'] = getString(Cmd.OB_STRING, minLen=1, maxLen=80)
      updateMask.add('displayName')
    elif updateCmd and myarg == 'sortorder':
      posloc = Cmd.Location()
      posbody['sortOrder'] = getInteger(minVal=1)
    elif updateCmd and myarg == 'relativeposition':
      posloc = Cmd.Location()
      posbody['relativePosition'] = getChoice(CHAT_SECTION_POSITION, mapChoice=True)
    elif not updateCmd and myarg == 'returnidonly':
      returnIdOnly = True
    else:
      FJQC.GetFormatJSON(myarg)
    if updateCmd:
      if not name:
        missingArgumentExit('<ChatSection>')
      if 'sortOrder' in posbody and 'relativePosition' in posbody:
        Cmd.SetLocation(posloc-1)
        usageErrorExit(Msg.ARE_MUTUALLY_EXCLUSIVE.format('sortorder', 'relativeposition'))
    else:
      if 'displayName' not in body:
        missingArgumentExit('displayname')
      body['type'] = 'CUSTOM_SECTION'
  i, count, users = getEntityArgument(users)
  for user in users:
    i += 1
    user, chat, kvList = buildChatServiceObject(API.CHAT_SECTIONS, user, i, count,
                                                [Ent.CHAT_SECTION, body.get('displayName', '')])
    if not chat:
      continue
    try:
      if not updateCmd:
        section = callGAPI(chat.users().sections(), 'create',
                           bailOnInternalError=True,
                           throwReasons=[GAPI.NOT_FOUND, GAPI.INVALID_ARGUMENT, GAPI.INTERNAL_ERROR,
                                         GAPI.PERMISSION_DENIED, GAPI.FAILED_PRECONDITION],
                           retryReasons=GAPI.SERVICE_NOT_AVAILABLE_RETRY_REASONS,
                           parent=f'users/{user}', body=body)
        if not returnIdOnly:
          kvList[-1] = section['name']
          if not FJQC.formatJSON:
            entityActionPerformed(kvList, i, count)
          Ind.Increment()
          _showChatItem(section, Ent.CHAT_SECTION, FJQC)
          Ind.Decrement()
        else:
          writeStdout(f'{section["name"]}\n')
      else:
        pname = name
        if not pname.startswith('users/'):
          pname = f'users/{user}/{name}'
        kvList[-1] = pname
        if not body and not posbody:
          entityActionNotPerformedWarning(kvList, Msg.NO_CHANGES, i, count)
          continue
        if body:
          section = callGAPI(chat.users().sections(), 'patch',
                             bailOnInternalError=True,
                             throwReasons=[GAPI.NOT_FOUND, GAPI.INVALID_ARGUMENT, GAPI.INTERNAL_ERROR,
                                           GAPI.PERMISSION_DENIED, GAPI.FAILED_PRECONDITION],
                             retryReasons=GAPI.SERVICE_NOT_AVAILABLE_RETRY_REASONS,
                             name=pname, updateMask=','.join(updateMask), body=body)
        if posbody:
          section = callGAPI(chat.users().sections(), 'position',
                             bailOnInternalError=True,
                             throwReasons=[GAPI.NOT_FOUND, GAPI.INVALID_ARGUMENT, GAPI.INTERNAL_ERROR,
                                           GAPI.PERMISSION_DENIED, GAPI.FAILED_PRECONDITION],
                             retryReasons=GAPI.SERVICE_NOT_AVAILABLE_RETRY_REASONS,
                             name=pname, body=posbody)
          section = section['section']
        kvList[-1] = section['name']
        if not FJQC.formatJSON:
          entityActionPerformed(kvList, i, count)
        Ind.Increment()
        _showChatItem(section, Ent.CHAT_SECTION, FJQC)
        Ind.Decrement()
    except (GAPI.notFound, GAPI.invalidArgument, GAPI.internalError, GAPI.permissionDenied) as e:
      exitIfChatNotConfigured(chat, kvList, str(e), i, count)
      continue
    except GAPI.failedPrecondition:
      userChatServiceNotEnabledWarning(user, i, count)
      continue
    except AttributeError:
      systemErrorExit(GOOGLE_API_ERROR_RC, Msg.DEVELOPER_PREVIEW_REQUIRED)

# gam <UserTypeEntity> delete chatsection <ChatSection>
def deleteChatSection(users):
  name = getChatSectionName()
  checkForExtraneousArguments()
  i, count, users = getEntityArgument(users)
  for user in users:
    i += 1
    user, chat, kvList = buildChatServiceObject(API.CHAT_SECTIONS, user, i, count,
                                                [Ent.CHAT_SECTION, name])
    if not chat:
      continue
    try:
      pname = name
      if not pname.startswith('users/'):
        pname = f'users/{user}/{name}'
      kvList[-1] = pname
      callGAPI(chat.users().sections(), 'delete',
                         bailOnInternalError=True,
                         throwReasons=[GAPI.NOT_FOUND, GAPI.INVALID_ARGUMENT, GAPI.INTERNAL_ERROR,
                                       GAPI.PERMISSION_DENIED, GAPI.FAILED_PRECONDITION],
                         retryReasons=GAPI.SERVICE_NOT_AVAILABLE_RETRY_REASONS,
                         name=pname)
      entityActionPerformed(kvList, i, count)
    except (GAPI.notFound, GAPI.invalidArgument, GAPI.internalError, GAPI.permissionDenied) as e:
      exitIfChatNotConfigured(chat, kvList, str(e), i, count)
      continue
    except GAPI.failedPrecondition:
      userChatServiceNotEnabledWarning(user, i, count)
      continue
    except AttributeError:
      systemErrorExit(GOOGLE_API_ERROR_RC, Msg.DEVELOPER_PREVIEW_REQUIRED)

# gam <UserTypeEntity> show chatsections
#	[formatjson]
# gam <UserTypeEntity> print chatsections [todrive <ToDriveAttribute>*]
#	[formatjson [quotechar <Character>]]
def printShowChatSections(users):
  csvPF = CSVPrintFile(['User', 'name'])  if Act.csvFormat() else None
  FJQC = FormatJSONQuoteChar(csvPF)
  while Cmd.ArgumentsRemaining():
    myarg = getArgument()
    if csvPF and myarg == 'todrive':
      csvPF.GetTodriveParameters()
    else:
      FJQC.GetFormatJSONQuoteChar(myarg, True)
  i, count, users = getEntityArgument(users)
  for user in users:
    i += 1
    user, chat, kvList = buildChatServiceObject(API.CHAT_SECTIONS, user, i, count)
    if not chat:
      continue
    try:
      sections = callGAPIpages(chat.users().sections(), 'list', 'sections',
                               pageMessage=_getChatPageMessage(Ent.CHAT_SECTION, user, i, count, None),
                               bailOnInternalError=True,
                               throwReasons=[GAPI.NOT_FOUND, GAPI.INVALID_ARGUMENT, GAPI.INTERNAL_ERROR,
                                             GAPI.PERMISSION_DENIED, GAPI.FAILED_PRECONDITION],
                               retryReasons=GAPI.SERVICE_NOT_AVAILABLE_RETRY_REASONS,
                               parent=f'users/{user}', pageSize=GC.Values[GC.CHAT_MAX_RESULTS])
    except (GAPI.notFound, GAPI.invalidArgument, GAPI.internalError, GAPI.permissionDenied) as e:
      exitIfChatNotConfigured(chat, kvList, str(e), i, count)
      continue
    except GAPI.failedPrecondition:
      userChatServiceNotEnabledWarning(user, i, count)
      continue
    except AttributeError:
      systemErrorExit(GOOGLE_API_ERROR_RC, Msg.DEVELOPER_PREVIEW_REQUIRED)
    jcount = len(sections)
    if jcount == 0:
      setSysExitRC(NO_ENTITIES_FOUND_RC)
    if not csvPF:
      if not FJQC.formatJSON:
        entityPerformActionNumItems(kvList, jcount, Ent.CHAT_SECTION, i, count)
      Ind.Increment()
      j = 0
      for section in sections:
        j += 1
        _showChatItem(section, Ent.CHAT_SECTION, FJQC, j, jcount)
      Ind.Decrement()
    else:
      for section in sections:
        _printChatItem(user, section, None, Ent.CHAT_SECTION, csvPF, FJQC)
  if csvPF:
    csvPF.writeCSVfile('Chat Sections')

# gam <UserTypeEntity> move chatsectionitem <ChatSectionItem> to <ChatSection>
def moveShowChatSectionItem(users):
  name = getChatSectionName()
  if Cmd.PeekArgumentPresent(['to']):
    Cmd.Advance()
  target = getChatSectionName()
  checkForExtraneousArguments()
  i, count, users = getEntityArgument(users)
  for user in users:
    i += 1
    user, chat, kvList = buildChatServiceObject(API.CHAT_SECTIONS, user, i, count,
                                                [Ent.CHAT_SECTION_ITEM, name])
    if not chat:
      continue
    try:
      pname = name
      if not pname.startswith('users/'):
        pname = f'users/{user}/{name}'
      kvList[-1] = pname
      ptarget = target
      if not ptarget.startswith('users/'):
        ptarget = f'users/{user}/{target}'
      kvList[-1] = ptarget
      callGAPI(chat.users().sections().items(), 'move',
                         bailOnInternalError=True,
                         throwReasons=[GAPI.NOT_FOUND, GAPI.INVALID_ARGUMENT, GAPI.INTERNAL_ERROR,
                                       GAPI.PERMISSION_DENIED, GAPI.FAILED_PRECONDITION],
                         retryReasons=GAPI.SERVICE_NOT_AVAILABLE_RETRY_REASONS,
                         name=pname, body={'targetSection': ptarget})
      entityModifierItemValueListActionPerformed(kvList, Act.MODIFIER_TO, [Ent.CHAT_SECTION, ptarget], i, count)
    except (GAPI.notFound, GAPI.invalidArgument, GAPI.internalError, GAPI.permissionDenied) as e:
      exitIfChatNotConfigured(chat, kvList, str(e), i, count)
      continue
    except GAPI.failedPrecondition:
      userChatServiceNotEnabledWarning(user, i, count)
      continue
    except AttributeError:
      systemErrorExit(GOOGLE_API_ERROR_RC, Msg.DEVELOPER_PREVIEW_REQUIRED)

# gam <UserTypeEntity> show chatsectionitems <ChatSection>
#	[space <ChatSpace>]
#	[formatjson]
# gam <UserTypeEntity> print chatsectionitems  <ChatSection> [todrive <ToDriveAttribute>*]
#	[space <ChatSpace>]
#	[formatjson [quotechar <Character>]]
def printShowChatSectionItems(users):
  cd = buildGAPIObject(API.DIRECTORY)
  csvPF = CSVPrintFile(['User', 'name', 'space'])  if Act.csvFormat() else None
  FJQC = FormatJSONQuoteChar(csvPF)
  name = getChatSectionName()
  kwargs = {}
  while Cmd.ArgumentsRemaining():
    myarg = getArgument()
    if csvPF and myarg == 'todrive':
      csvPF.GetTodriveParameters()
    elif myarg == 'space' or myarg.startswith('spaces/') or myarg.startswith('space/'):
      kwargs['filter'] = f'space = {getSpaceName(myarg)}'
    else:
      FJQC.GetFormatJSONQuoteChar(myarg, True)
  i, count, users = getEntityArgument(users)
  for user in users:
    i += 1
    user, chat, kvList = buildChatServiceObject(API.CHAT_SECTIONS, user, i, count)
    if not chat:
      continue
    _, chatsp, _ = buildChatServiceObject(API.CHAT_SPACES, user, i, count)
    if not chatsp:
      continue
    _, chatme, _ = buildChatServiceObject(API.CHAT_MEMBERSHIPS, user, i, count)
    if not chatme:
      continue
    pname = name
    if not pname.startswith('users/'):
      pname = f'users/{user}/{name}'
    kvList[-1] = pname
    try:
      sectionItems = callGAPIpages(chat.users().sections().items(), 'list', 'sectionItems',
                                   pageMessage=_getChatPageMessage(Ent.CHAT_SECTION_ITEM, user, i, count, None),
                                   bailOnInternalError=True,
                                   throwReasons=[GAPI.NOT_FOUND, GAPI.INVALID_ARGUMENT, GAPI.INTERNAL_ERROR,
                                                 GAPI.PERMISSION_DENIED, GAPI.FAILED_PRECONDITION],
                                   retryReasons=GAPI.SERVICE_NOT_AVAILABLE_RETRY_REASONS,
                                   parent=pname, pageSize=GC.Values[GC.CHAT_MAX_RESULTS], **kwargs)
      for sectionItem in sectionItems:
        space = callGAPI(chatsp.spaces(), 'get',
                         bailOnInternalError=True,
                         throwReasons=[GAPI.NOT_FOUND, GAPI.INVALID_ARGUMENT, GAPI.INTERNAL_ERROR,
                                       GAPI.PERMISSION_DENIED, GAPI.FAILED_PRECONDITION],
                         retryReasons=GAPI.SERVICE_NOT_AVAILABLE_RETRY_REASONS,
                         name=sectionItem['space'], fields='displayName,spaceType')
        sectionItem['spaceDetails'] = {'spaceType': space['spaceType']}
        if space['spaceType'] == 'DIRECT_MESSAGE':
          members = callGAPIitems(chatme.spaces().members(), 'list', 'memberships',
                                  bailOnInternalError=True,
                                  throwReasons=[GAPI.NOT_FOUND, GAPI.INVALID_ARGUMENT, GAPI.INTERNAL_ERROR,
                                                GAPI.PERMISSION_DENIED, GAPI.FAILED_PRECONDITION],
                                  retryReasons=GAPI.SERVICE_NOT_AVAILABLE_RETRY_REASONS,
                                  parent=sectionItem['space'], fields='memberships(member)')
          for member in members:
            _getChatMemberEmail(cd, member)
          sectionItem['spaceDetails']['members'] = ' '.join([member['member']['email'] for member in members])
        elif 'displayName' in space:
          sectionItem['spaceDetails']['displayName'] = space['displayName']
    except (GAPI.notFound, GAPI.invalidArgument, GAPI.internalError, GAPI.permissionDenied) as e:
      exitIfChatNotConfigured(chat, kvList, str(e), i, count)
      continue
    except GAPI.failedPrecondition:
      userChatServiceNotEnabledWarning(user, i, count)
      continue
    except AttributeError:
      systemErrorExit(GOOGLE_API_ERROR_RC, Msg.DEVELOPER_PREVIEW_REQUIRED)
    jcount = len(sectionItems)
    if jcount == 0:
      setSysExitRC(NO_ENTITIES_FOUND_RC)
    if not csvPF:
      if not FJQC.formatJSON:
        entityPerformActionNumItems(kvList, jcount, Ent.CHAT_SECTION_ITEM, i, count)
      Ind.Increment()
      j = 0
      for sectionItem in sectionItems:
        j += 1
        _showChatItem(sectionItem, Ent.CHAT_SECTION_ITEM, FJQC, j, jcount)
      Ind.Decrement()
    else:
      for sectionItem in sectionItems:
        _printChatItem(user, sectionItem, None, Ent.CHAT_SECTION_ITEM, csvPF, FJQC)
  if csvPF:
    csvPF.writeCSVfile('Chat Sections')

