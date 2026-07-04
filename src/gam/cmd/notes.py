"""GAM Google Keep notes management."""

import re
import json

import googleapiclient.http
import os

from gamlib import api as API
from gamlib import settings as GC
from gamlib import gapi as GAPI
from gamlib import msgs as Msg
from gam.var import Act, Cmd, Ent, Ind
from gam.util.svcacct import buildGAPIServiceObject
from gam.util.api_call import callGAPI, callGAPIpages
from gam.util.args import (
    SORF_TEXT_ARGUMENTS,
    checkForExtraneousArguments,
    escapeCRsNLs,
    formatLocalTime,
    getArgument,
    getBoolean,
    getChoice,
    getEmailAddress,
    getJSON,
    getString,
    getStringOrFile,
)
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
    entityActionFailedWarning,
    entityActionNotPerformedWarning,
    entityActionPerformed,
    entityActionPerformedMessage,
    entityModifierNewValueActionFailedWarning,
    entityModifierNewValueActionPerformed,
    entityNumItemsActionPerformed,
    entityPerformActionNumItems,
    getPageMessageForWhom,
    printEntity,
    printEntityKVList,
    printGettingEntityItemForWhom,
    printKeyValueList,
    printKeyValueListWithCount,
    printLine,
    userDriveServiceNotEnabledWarning,
    userKeepServiceNotEnabledWarning,
)
from gam.util.entity import _validateUserGetObjectList, getEntityArgument, getUserObjectEntity, splitEmailAddressOrUID
from gam.util.errors import missingArgumentExit, unknownArgumentExit
from gam.util.fileio import closeFile, openFile, setFilePath, uniqueFilename
from gam.util.tags import _substituteForUser
from gam.cmd.drive.core import _driveFileParentSpecified, _getDriveFileParentInfo, getDriveFileParentAttribute, initDriveFileAttributes


def normalizeNoteName(noteName):
  if noteName.startswith('notes/'):
    return noteName
  return f'notes/{noteName}'

def _assignNoteOwner(note, user):
  for permission in note.get('permissions', []):
    if permission['role'] == 'OWNER':
      noteOwner = permission.get('user', {}).get('email', '').lower()
      note['owner'] = noteOwner
      note['ownedByMe'] = noteOwner == user
      break

def _checkNoteUserRole(note, user, role):
  for permission in note['permissions']:
    if permission['role'] == role and permission.get('user', {}).get('email', '').lower() == user:
      return True
  return False

def _showNoteListItems(listItems):
  printKeyValueList(['list', ''])
  Ind.Increment()
  kcount = len(listItems)
  k = 0
  for listItem in listItems:
    k += 1
    printKeyValueListWithCount(['item', ''], k, kcount)
    Ind.Increment()
    if 'text' in listItem and 'text' in listItem['text']:
      printKeyValueList(['text', listItem['text']['text']])
    if 'checked' in listItem:
      printKeyValueList(['checked', listItem['checked']])
    if 'childListItems' in listItem:
      _showNoteListItems(listItem['childListItems'])
    Ind.Decrement()
  Ind.Decrement()

def _showNotePermissions(permissions):
  printKeyValueList(['permissions', ''])
  Ind.Increment()
  kcount = len(permissions)
  k = 0
  for permission in permissions:
    k += 1
    printKeyValueListWithCount(['name', permission['name']], k, kcount)
    Ind.Increment()
    for field in ['role', 'deleted']:
      if field in permission:
        printKeyValueList([field, permission[field]])
    for field in ['user', 'group']:
      if field in permission:
        printKeyValueList([field, permission[field]['email']])
        break
    else:
      if 'email' in permission:
        printKeyValueList(['email', permission['email']])
    if 'family' in permission:
      family = permission['family']
      if 'text' in family:
        printKeyValueList(['family', family['text']['text']])
      elif 'list' in family:
        _showNoteListItems(family['list']['listItems'])
    Ind.Decrement()
  Ind.Decrement()

def _showNoteAttachments(attachments):
  printKeyValueList(['attachments', ''])
  Ind.Increment()
  kcount = len(attachments)
  k = 0
  for attachment in attachments:
    k += 1
    printKeyValueListWithCount(['name', attachment['name']], k, kcount)
    if 'mimeType' in attachment:
      Ind.Increment()
      printKeyValueList(['mimeType', ','.join(attachment['mimeType'])])
      Ind.Decrement()
  Ind.Decrement()

NOTES_TIME_OBJECTS = {'createTime', 'updateTime', 'trashTime'}

def _showNote(note, j=0, jcount=0, FJQC=None, compact=False):
  if FJQC is not None and FJQC.formatJSON:
    printLine(json.dumps(cleanJSON(note, timeObjects=NOTES_TIME_OBJECTS), ensure_ascii=False, sort_keys=True))
    return
  printEntity([Ent.NOTE, note['name']], j, jcount)
  Ind.Increment()
  printKeyValueList(['title', note.get('title', None)])
  for field in NOTES_TIME_OBJECTS:
    if field in note:
      printKeyValueList([field, formatLocalTime(note[field])])
  if 'trashed' in note:
    printKeyValueList(['trashed', note['trashed']])
  for field in ['owner', 'ownedByMe']:
    if field in note:
      printKeyValueList([field, note[field]])
  if 'permissions' in note:
    _showNotePermissions(note['permissions'])
  if 'attachments' in note:
    _showNoteAttachments(note['attachments'])
  body = note.get('body', {})
  if 'text' in body and 'text' in body['text']:
    if not compact:
      printKeyValueList(['text', None])
      Ind.Increment()
      printKeyValueList([Ind.MultiLineText(body['text']['text'])])
      Ind.Decrement()
    else:
      printKeyValueList(['text', escapeCRsNLs(body['text']['text'])])
  elif 'list' in body and 'listItems' in body['list']:
    _showNoteListItems(body['list']['listItems'])
  Ind.Decrement()

# gam <UserTypeEntity> create note [title <String>]
#	<NoteContent>
#       [missingtextvalue <String>]
#	[copyacls [copyowneraswriter]
#	[compact|formatjson|nodetails]
def createNote(users):
  def fixTextItem(item):
    if 'text' in item:
      if item['text']:
        item['text'] = unescapeCRsNLs(item['text'])
        return
    if missingTextValue:
      item['text'] = missingTextValue

  def fixListItem(item):
    if 'listItems' in item:
      if item['listItems']:
        for listItem in item['listItems']:
          fixTextItem(listItem['text'])
        return
    if missingTextValue:
      item['listItems'] = [{'checked': False, 'text': {'text': missingTextValue}}]

  FJQC = FormatJSONQuoteChar()
  compact = False
  showDetails = True
  missingTextValue = ''
  copyACLs = copyOwnerAsWriter = False
  body = {'title': '', 'body': {}}
  copyUsers = []
  copyGroups = []
  noteOwner = None
  while Cmd.ArgumentsRemaining():
    myarg = getArgument()
    if myarg == 'title':
      body['title'] = getString(Cmd.OB_STRING, minLen=1, maxLen=1000)
    elif myarg in SORF_TEXT_ARGUMENTS:
      msgText, _, _ = getStringOrFile(myarg, minLen=1, unescapeCRLF=True)
      body['body']['text'] = {'text': msgText}
    elif myarg == 'missingtextvalue':
      missingTextValue = getString(Cmd.OB_STRING, minLen=1)
    elif myarg == 'json':
      jsonData = getJSON([])
      if not body['title']:
        body['title'] = jsonData.get('title', missingTextValue)
      body['body'] = jsonData.get('body', {})
      if 'text' in body['body']:
        fixTextItem(body['body']['text'])
      elif 'list' in body['body']:
        fixListItem(body['body']['list'])
      for permission in jsonData.get('permissions', []):
        if permission['role'] == 'WRITER':
          if 'user' in permission:
            copyUsers.append(permission['user']['email'].lower())
          elif 'group' in permission:
            copyGroups.append(permission['group']['email'].lower())
        elif permission['role'] == 'OWNER':
          if 'user' in permission:
            noteOwner = permission['user']['email'].lower()
    elif myarg == 'copyacls':
      copyACLs = True
    elif myarg == 'copyowneraswriter':
      copyOwnerAsWriter = True
    elif myarg == 'compact':
      compact = True
    elif myarg == 'nodetails':
      showDetails = False
    else:
      FJQC.GetFormatJSON(myarg)
  if not body['body']:
    choices = list(SORF_TEXT_ARGUMENTS)
    choices.append('json')
    missingArgumentExit('|'.join(choices))
  i, count, users = getEntityArgument(users)
  for user in users:
    i += 1
    user, keep = buildGAPIServiceObject(API.KEEP, user, i, count)
    if not keep:
      continue
    if copyACLs:
      rbody = {'requests': []}
      for addr in copyUsers:
        if addr != user:
          rbody['requests'].append({'parent': None,
                                    'permission': {'role': 'WRITER', 'user': {'email': addr}}})
      for addr in copyGroups:
        rbody['requests'].append({'parent': None,
                                  'permission': {'role': 'WRITER', 'group': {'email': addr}}})
      if copyOwnerAsWriter and noteOwner and noteOwner != user:
        rbody['requests'].append({'parent': None,
                                  'permission': {'role': 'WRITER', 'user': {'email': noteOwner}}})
      kcount = len(rbody['requests'])
    try:
      note = callGAPI(keep.notes(), 'create',
                      throwReasons=GAPI.KEEP_THROW_REASONS,
                      body=body)
      name = note['name']
      entityKVList = [Ent.USER, user, Ent.NOTE, name]
      _assignNoteOwner(note, user)
      if copyACLs and kcount > 0:
        for request in rbody['requests']:
          request['parent'] = name
        try:
          callGAPI(keep.notes().permissions(), 'batchCreate',
                   throwReasons=GAPI.KEEP_THROW_REASONS,
                   parent=name, body=rbody)
          note = callGAPI(keep.notes(), 'get',
                          throwReasons=GAPI.KEEP_THROW_REASONS,
                          name=name)
        except (GAPI.badRequest, GAPI.permissionDenied, GAPI.invalidArgument, GAPI.notFound):
          pass
        except GAPI.serviceNotAvailable:
          pass
      if showDetails:
        _showNote(note, FJQC=FJQC, compact=compact)
      else:
        entityActionPerformed(entityKVList, i, count)
    except (GAPI.badRequest, GAPI.invalidArgument, GAPI.notFound) as e:
      entityActionFailedWarning([Ent.USER, user, Ent.NOTE, body['title']], str(e), i, count)
    except GAPI.authError:
      userKeepServiceNotEnabledWarning(user, i, count)

NOTES_FIELDS_CHOICE_MAP = {
  'attachments': 'attachments',
  'body': 'body',
  'createtime': 'createTime',
  'name': 'name',
  'permissions': 'permissions',
  'title': 'title',
  'trashed': 'trashed',
  'trashtime': 'trashTime',
  'updatetime': 'updateTime',
  }

# gam <UserTypeEntity> info note <NotesNameEntity>
#	[fields <NotesFieldList>]
#	[compact|formatjson]
# gam <UserTypeEntity> delete note <NotesNameEntity>
def deleteInfoNotes(users):
  function = 'delete' if Act.Get() == Act.DELETE else 'get'
  fieldsList = []
  noteNameEntity = getUserObjectEntity(Cmd.OB_NAME, Ent.NOTE)
  showPermissions = True
  if function == 'get':
    FJQC = FormatJSONQuoteChar()
    compact = False
    while Cmd.ArgumentsRemaining():
      myarg = getArgument()
      if getFieldsList(myarg, NOTES_FIELDS_CHOICE_MAP, fieldsList, initialField='name'):
        pass
      elif myarg == 'compact':
        compact = True
      else:
        FJQC.GetFormatJSON(myarg)
    fields = getFieldsFromFieldsList(fieldsList)
  else:
    FJQC = None
    checkForExtraneousArguments()
  if fieldsList and 'permissions' not in fieldsList:
    showPermissions = False
  i, count, users = getEntityArgument(users)
  for user in users:
    i += 1
    user, keep, noteNames, jcount = _validateUserGetObjectList(user, i, count, noteNameEntity,
                                                               api=API.KEEP, showAction=FJQC is None or not FJQC.formatJSON)
    if jcount == 0:
      continue
    Ind.Increment()
    j = 0
    for name in noteNames:
      j += 1
      name = normalizeNoteName(name)
      try:
        if function == 'get':
          note = callGAPI(keep.notes(), function,
                          throwReasons=GAPI.KEEP_THROW_REASONS,
                          name=name, fields=fields)
          if showPermissions:
            _assignNoteOwner(note, user)
          _showNote(note, j, jcount, FJQC, compact)
        else:
          callGAPI(keep.notes(), function,
                   throwReasons=GAPI.KEEP_THROW_REASONS,
                   name=name)
          entityActionPerformed([Ent.USER, user, Ent.NOTE, name], j, jcount)
      except (GAPI.badRequest, GAPI.invalidArgument, GAPI.notFound) as e:
        entityActionFailedWarning([Ent.USER, user, Ent.NOTE, name], str(e), j, jcount)
      except GAPI.authError:
        userKeepServiceNotEnabledWarning(user, i, count)
        break
    Ind.Decrement()

NOTES_ROLE_CHOICE_MAP = {
  'owner': 'OWNER',
  'writer': 'WRITER',
  }

NOTES_COUNTS_MAP = {
  'OWNER': 'noteOwner',
  'WRITER': 'noteWriter',
  }

# gam <UserTypeEntity> show notes
#	[fields <NotesFieldList>] [filter <String>]
#	[role owner|writer]
#	[countsonly]
#	[compact] [formatjson]
# gam <UserTypeEntity> print notes [todrive <ToDriveAttribute>*]
#	[fields <NotesFieldList>] [filter <String>]
#	[role owner|writer]
#	[countsonly]
#	[formatjson [quotechar <Character>]]
def printShowNotes(users):
  csvPF = CSVPrintFile(['User', 'name', 'title', 'owner', 'ownedByMe']) if Act.csvFormat() else None
  if csvPF:
    csvPF.SetNoEscapeChar(True)
  FJQC = FormatJSONQuoteChar(csvPF)
  compact = countsOnly = False
  fieldsList = []
  noteFilter = None
  role = None
  showPermissions = True
  while Cmd.ArgumentsRemaining():
    myarg = getArgument()
    if csvPF and myarg == 'todrive':
      csvPF.GetTodriveParameters()
    elif getFieldsList(myarg, NOTES_FIELDS_CHOICE_MAP, fieldsList, initialField=['name', 'title']):
      pass
    elif myarg == 'filter':
      noteFilter = getString(Cmd.OB_STRING)
    elif myarg == 'role':
      role = getChoice(NOTES_ROLE_CHOICE_MAP, mapChoice=True)
    elif not csvPF and myarg == 'compact':
      compact = True
    elif myarg == 'countsonly':
      countsOnly = True
    else:
      FJQC.GetFormatJSONQuoteChar(myarg, True)
  if FJQC.formatJSON:
    GC.Values[GC.CSV_OUTPUT_CONVERT_CR_NL] = False
  if fieldsList and 'permissions' not in fieldsList:
    showPermissions = False
    fieldsList.append('permissions')
    if csvPF:
      if not countsOnly:
        if not FJQC.formatJSON:
          csvPF.RemoveTitles(['owner', 'ownedByMe'])
        else:
          csvPF.RemoveJSONTitles(['owner', 'ownedByMe'])
  if countsOnly and csvPF:
    if not FJQC.formatJSON:
      csvPF.SetTitles(['User', 'noteOwner', 'noteWriter', 'totalNotes'])
    else:
      csvPF.SetJSONTitles(['User', 'JSON'])
  fields = getItemFieldsFromFieldsList('notes', fieldsList, returnItemIfNoneList=False)
  i, count, users = getEntityArgument(users)
  for user in users:
    i += 1
    user, keep = buildGAPIServiceObject(API.KEEP, user, i, count)
    if not keep:
      continue
    if csvPF:
      printGettingEntityItemForWhom(Ent.NOTE, user, i, count)
      pageMessage = getPageMessageForWhom()
    else:
      pageMessage = None
    try:
      notes = callGAPIpages(keep.notes(), 'list', 'notes',
                            pageMessage=pageMessage,
                            throwReasons=GAPI.KEEP_THROW_REASONS,
                            filter=noteFilter, fields=fields)
      if countsOnly:
        noteCounts = {'User': user, 'noteOwner': 0, 'noteWriter': 0, 'totalNotes': 0}
        for note in notes:
          noteCounts['totalNotes'] += 1
          for permission in note['permissions']:
            if permission.get('user', {}).get('email', '').lower() == user:
              noteCounts[NOTES_COUNTS_MAP[permission['role']]] += 1
              break
        if not csvPF:
          if not FJQC.formatJSON:
            printEntityKVList([Ent.USER, user], ['noteOwner', noteCounts['noteOwner'],
                                                 'noteWriter', noteCounts['noteWriter'],
                                                 'totalNotes', noteCounts['totalNotes']], i, count)
          else:
            printLine(json.dumps(cleanJSON(noteCounts), ensure_ascii=False, sort_keys=True))
        else:
          row = {'User': user, 'noteOwner': noteCounts['noteOwner'], 'noteWriter': noteCounts['noteWriter'],
                 'totalNotes': noteCounts['totalNotes']}
          if not FJQC.formatJSON:
            csvPF.WriteRowTitles(row)
          elif csvPF.CheckRowTitles(row):
            row = {'User': noteCounts.pop('User')}
            row['JSON'] = json.dumps(cleanJSON(noteCounts), ensure_ascii=False, sort_keys=True)
            csvPF.WriteRowNoFilter(row)
      elif not csvPF:
        jcount = len(notes)
        if not FJQC.formatJSON:
          entityPerformActionNumItems([Ent.USER, user], jcount, Ent.NOTE, i, count)
        Ind.Increment()
        j = 0
        for note in notes:
          j += 1
          if showPermissions:
            _assignNoteOwner(note, user)
          if role is None or _checkNoteUserRole(note, user, role):
            if not showPermissions:
              note.pop('permissions', None)
            _showNote(note, j, jcount, FJQC, compact)
        Ind.Decrement()
      elif notes:
        for note in notes:
          if showPermissions:
            _assignNoteOwner(note, user)
          if role is None or _checkNoteUserRole(note, user, role):
            if not showPermissions:
              note.pop('permissions', None)
            row = flattenJSON(note, flattened={'User': user}, timeObjects=NOTES_TIME_OBJECTS)
            if not FJQC.formatJSON:
              csvPF.WriteRowTitles(row)
            elif csvPF.CheckRowTitles(row):
              row = {'User': user, 'name': note['name'], 'title': note.get('title', '')}
              if showPermissions:
                row.update({'owner': note['owner'], 'ownedByMe': note['ownedByMe']})
              row['JSON'] = json.dumps(cleanJSON(note, timeObjects=NOTES_TIME_OBJECTS),
                                       ensure_ascii=False, sort_keys=True)
              csvPF.WriteRowNoFilter(row)
      elif GC.Values[GC.CSV_OUTPUT_USERS_AUDIT]:
        csvPF.WriteRowNoFilter({'User': user})
    except (GAPI.badRequest, GAPI.invalidArgument, GAPI.notFound) as e:
      entityActionFailedWarning([Ent.USER, user, Ent.NOTE, None], str(e), i, count)
    except GAPI.authError:
      userKeepServiceNotEnabledWarning(user, i, count)
  if csvPF:
    csvPF.writeCSVfile('Notes')

GET_NOTE_HTTP_ERROR_PATTERN = re.compile(r'^.*\'description\': \'(.*)\'')

# gam <UserTypeEntity> get noteattachments <NotesNameEntity>
#	[targetfolder <FilePath>] [targetname <FileName>] [overwrite [<Boolean>]]
#	[<DriveFileParentAttribute>]
def getNoteAttachments(users):
  noteNameEntity = getUserObjectEntity(Cmd.OB_NAME, Ent.NOTE)
  targetFolderPattern = GC.Values[GC.DRIVE_DIR]
  targetNamePattern = None
  overwrite = False
  body = {}
  parentParms = initDriveFileAttributes()
  while Cmd.ArgumentsRemaining():
    myarg = getArgument()
    if myarg == 'targetfolder':
      targetFolderPattern = setFilePath(getString(Cmd.OB_FILE_PATH), GC.DRIVE_DIR)
    elif myarg == 'targetname':
      targetNamePattern = getString(Cmd.OB_FILE_NAME)
    elif myarg == 'overwrite':
      overwrite = getBoolean()
    elif getDriveFileParentAttribute(myarg, parentParms):
      pass
    else:
      unknownArgumentExit()
  parentSpecified = _driveFileParentSpecified(parentParms)
  i, count, users = getEntityArgument(users)
  for user in users:
    i += 1
    user, keep, noteNames, jcount = _validateUserGetObjectList(user, i, count, noteNameEntity,
                                                               api=API.KEEP, showAction=True)
    if jcount == 0:
      continue
    if parentSpecified:
      _ , drive = buildGAPIServiceObject(API.DRIVE3, user, i, count)
      if not drive:
        continue
      if not _getDriveFileParentInfo(drive, user, i, count, body, parentParms):
        continue
    _, userName, _ = splitEmailAddressOrUID(user)
    targetFolder = _substituteForUser(targetFolderPattern, user, userName)
    if not os.path.isdir(targetFolder):
      os.makedirs(targetFolder)
    targetName = _substituteForUser(targetNamePattern, user, userName) if targetNamePattern else None
    Ind.Increment()
    j = 0
    for name in noteNames:
      j += 1
      name = normalizeNoteName(name)
      try:
        result = callGAPI(keep.notes(), 'get',
                          throwReasons=GAPI.KEEP_THROW_REASONS,
                          name=name, fields='title,attachments')
        title = result.get('title', 'attachment')
        kcount = len(result['attachments'])
        entityPerformActionNumItems([Ent.NOTE, name], kcount, Ent.ATTACHMENT, j, jcount)
        Ind.Increment()
        k = 0
        for attachment in result['attachments']:
          k += 1
          attachmentName = attachment['name'][attachment['name'].find('attachments'):]
          entityValueList = [Ent.ATTACHMENT, attachmentName]
          mimeTypes = attachment.get('mimeType', [])
          if not mimeTypes:
            entityActionNotPerformedWarning(entityValueList, Msg.MIMETYPE_NOT_PRESENT_IN_ATTACHMENT, k, kcount)
            continue
          mimeType = mimeTypes[0]
          localFilename, filename = uniqueFilename(targetFolder, f"{targetName or cleanFilename(title)}-{k}{MIMETYPE_EXTENSION_MAP.get(mimeType, '')}", overwrite)
          request = keep.media().download(name=attachment['name'], mimeType=mimeType)
          f = openFile(localFilename, 'wb', continueOnError=True)
          if f is None:
            continue
          downloader = googleapiclient.http.MediaIoBaseDownload(f, request)
          done = False
          downloadOK = False
          try:
            while not done:
              status, done = downloader.next_chunk()
              if status.progress() < 1.0:
                entityActionPerformedMessage(entityValueList, f'{status.progress():>7.2%}', k, kcount)
            entityModifierNewValueActionPerformed(entityValueList, Act.MODIFIER_TO, localFilename, k, kcount)
            downloadOK = True
          except (IOError, httplib2.HttpLib2Error) as e:
            entityModifierNewValueActionFailedWarning(entityValueList, Act.MODIFIER_TO, localFilename, str(e), k, kcount)
          except googleapiclient.http.HttpError as e:
            mg = GET_NOTE_HTTP_ERROR_PATTERN.match(str(e))
            if mg:
              entityModifierNewValueActionFailedWarning(entityValueList, Act.MODIFIER_TO, localFilename, mg.group(1), k, kcount)
            else:
              entityModifierNewValueActionFailedWarning(entityValueList, Act.MODIFIER_TO, localFilename, str(e), k, kcount)
          closeFile(f, True)
          if downloadOK and parentSpecified:
            body['name'] = filename
            body['mimeType'] = mimeType
            media_body = googleapiclient.http.MediaFileUpload(filename, mimetype=mimeType, resumable=True)
            Act.Set(Act.CREATE)
            try:
              result = callGAPI(drive.files(), 'create',
                                throwReasons=GAPI.DRIVE_USER_THROW_REASONS+[GAPI.FORBIDDEN, GAPI.INSUFFICIENT_PERMISSIONS,
                                                                            GAPI.INSUFFICIENT_PARENT_PERMISSIONS,
                                                                            GAPI.INVALID, GAPI.BAD_REQUEST, GAPI.CANNOT_ADD_PARENT,
                                                                            GAPI.FILE_NOT_FOUND, GAPI.UNKNOWN_ERROR, GAPI.STORAGE_QUOTA_EXCEEDED,
                                                                            GAPI.TEAMDRIVES_SHARING_RESTRICTION_NOT_ALLOWED,
                                                                            GAPI.TEAMDRIVE_FILE_LIMIT_EXCEEDED, GAPI.TEAMDRIVE_HIERARCHY_TOO_DEEP],
                                media_body=media_body, body=body, fields='id,name', supportsAllDrives=True)
              entityModifierNewValueActionPerformed([Ent.USER, user, Ent.DRIVE_FILE, f'{result["name"]}({result["id"]})'],
                                                    Act.MODIFIER_WITH_CONTENT_FROM, localFilename, k, kcount)
            except (GAPI.forbidden, GAPI.insufficientFilePermissions, GAPI.insufficientParentPermissions,
                    GAPI.invalid, GAPI.badRequest, GAPI.cannotAddParent,
                    GAPI.fileNotFound, GAPI.unknownError, GAPI.storageQuotaExceeded, GAPI.teamDrivesSharingRestrictionNotAllowed,
                    GAPI.teamDriveFileLimitExceeded, GAPI.teamDriveHierarchyTooDeep) as e:
              entityActionFailedWarning([Ent.USER, user, Ent.DRIVE_FILE, body['name']], str(e), k, kcount)
            except (GAPI.serviceNotAvailable, GAPI.authError, GAPI.domainPolicy) as e:
              userDriveServiceNotEnabledWarning(user, str(e), i, count)
            Act.Set(Act.DOWNLOAD)
        Ind.Decrement()
      except (GAPI.badRequest, GAPI.invalidArgument, GAPI.notFound) as e:
        entityActionFailedWarning([Ent.NOTE, name], str(e), j, jcount)
      except GAPI.authError:
        userKeepServiceNotEnabledWarning(user, i, count)
        break
    Ind.Decrement()

# gam <UserTypeEntity> create noteacl <NotesNameEntity>
#	(user|group <EmailAddress>)+
#	(json [charset <Charset>] <JSONData>)|(json file <FileName> [charset <Charset>])
#	[nodetails]
def createNotesACLs(users):
  noteNameEntity = getUserObjectEntity(Cmd.OB_NAME, Ent.NOTES_ACLS)
  body = {'requests': []}
  showDetails = True
  while Cmd.ArgumentsRemaining():
    myarg = getArgument()
    if myarg in {'user', 'group'}:
      body['requests'].append({'parent': None,
                               'permission': {'role': 'WRITER', myarg: {'email': getEmailAddress(noUid=True)}}})
    elif myarg == 'json':
      jsonData = getJSON([])
      for permission in jsonData.get('permissions', []):
        if permission['role'] == 'WRITER':
          if 'user' in permission:
            body['requests'].append({'parent': None,
                                     'permission': {'role': 'WRITER', 'user': {'email': permission['user']['email']}}})
          elif 'group' in permission:
            body['requests'].append({'parent': None,
                                     'permission': {'role': 'WRITER', 'group': {'email': permission['group']['email']}}})
    elif myarg == 'nodetails':
      showDetails = False
    else:
      unknownArgumentExit()
  kcount = len(body['requests'])
  i, count, users = getEntityArgument(users)
  for user in users:
    i += 1
    user, keep, noteNames, jcount = _validateUserGetObjectList(user, i, count, noteNameEntity, api=API.KEEP)
    if jcount == 0:
      continue
    Ind.Increment()
    j = 0
    for name in noteNames:
      j += 1
      name = normalizeNoteName(name)
      entityKVList = [Ent.USER, user, Ent.NOTE, name]
      rbody = body.copy()
      for request in rbody['requests']:
        request['parent'] = name
      try:
        permissions = callGAPI(keep.notes().permissions(), 'batchCreate',
                               throwReasons=GAPI.KEEP_THROW_REASONS+[GAPI.FAILED_PRECONDITION],
                               parent=name, body=rbody)
        entityNumItemsActionPerformed(entityKVList, kcount, Ent.NOTE_ACL, j, jcount)
        if showDetails:
          Ind.Increment()
          _showNotePermissions(permissions['permissions'])
          Ind.Decrement()
      except (GAPI.badRequest, GAPI.invalidArgument, GAPI.notFound, GAPI.failedPrecondition) as e:
        entityActionFailedWarning(entityKVList, str(e), i, count)
      except GAPI.authError:
        userKeepServiceNotEnabledWarning(user, i, count)
        break

# gam <UserTypeEntity> delete noteacl <NotesNameEntity>
#	(user|group <EmailAddress>)+
#	(json [charset <Charset>] <JSONData>)|(json file <FileName> [charset <Charset>])
def deleteNotesACLs(users):
  noteNameEntity = getUserObjectEntity(Cmd.OB_NAME, Ent.NOTES_ACLS)
  emails = {'user': set(), 'group': set()}
  body = {'names': []}
  while Cmd.ArgumentsRemaining():
    myarg = getArgument()
    if myarg in {'user', 'group'}:
      emails[myarg].add(getEmailAddress(noUid=True).lower())
    elif myarg == 'json':
      jsonData = getJSON([])
      for permission in jsonData.get('permissions', []):
        if permission['role'] == 'WRITER':
          loc = permission['name'].find('/permissions')
          body['names'].append(permission['name'][loc+1:])
    else:
      unknownArgumentExit()
  i, count, users = getEntityArgument(users)
  for user in users:
    i += 1
    user, keep, noteNames, jcount = _validateUserGetObjectList(user, i, count, noteNameEntity, api=API.KEEP)
    if jcount == 0:
      continue
    Ind.Increment()
    j = 0
    for name in noteNames:
      j += 1
      name = normalizeNoteName(name)
      rbody = body.copy()
      if emails['user'] or emails['group']:
        try:
          note = callGAPI(keep.notes(), 'get',
                          throwReasons=GAPI.KEEP_THROW_REASONS,
                          name=name, fields='permissions')
          for permission in note['permissions']:
            if permission['role'] == 'WRITER':
              if (('user' in permission and permission['user']['email'].lower() in emails['user']) or
                  ('group' in permission and permission['group']['email'].lower() in emails['group'])):
                rbody['names'].append(permission['name'])
        except (GAPI.badRequest, GAPI.permissionDenied, GAPI.invalidArgument, GAPI.notFound) as e:
          entityActionFailedWarning([Ent.USER, user, Ent.NOTE, name], str(e), i, count)
          break
        except GAPI.authError:
          userKeepServiceNotEnabledWarning(user, i, count)
          break
      for k, perm in enumerate(rbody['names']):
        if perm.startswith('notes/'):
          pass
        elif perm.startswith('permissions'):
          rbody['names'][k] = f'{name}/{perm}'
        else:
          rbody['names'][k] = f'{name}/permissions/{perm}'
      kcount = len(rbody['names'])
      entityKVList = [Ent.USER, user, Ent.NOTE, name]
      try:
        callGAPI(keep.notes().permissions(), 'batchDelete',
                 throwReasons=GAPI.KEEP_THROW_REASONS,
                 parent=name, body=rbody)
        entityNumItemsActionPerformed(entityKVList, kcount, Ent.NOTE_ACL, j, jcount)
      except (GAPI.badRequest, GAPI.invalidArgument, GAPI.notFound) as e:
        entityActionFailedWarning(entityKVList, str(e), i, count)
      except GAPI.authError:
        userKeepServiceNotEnabledWarning(user, i, count)
        break

