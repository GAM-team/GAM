"""Drive file delete, trash, download, and document operations.

Part of the transfer sub-package."""

"""File delete/trash/download/transfer/claim operations.

"""

"""GAM Google Drive file, permission, shared drive, and label management."""

import re
import json
import sys

import googleapiclient.http

from gam.cmd.drive.core import DFA_PARENTID, DFA_PARENTQUERY, _getEntityMimeType, _validateUserGetFileIDs, getDriveFileEntity
import os
import time

from gamlib import api as API
from gamlib import settings as GC
from gamlib import gapi as GAPI
from gamlib import state as GM
from gamlib import msgs as Msg
from gam.util.svcacct import buildGAPIServiceObject
from gam.util.api_call import callGAPI, callGAPIitems, callGAPIpages
from gam.util.args import (
    OrderBy,
    UTF8,
    checkArgumentPresent,
    checkForExtraneousArguments,
    getArgument,
    getBoolean,
    getChoice,
    getJSON,
    getSheetEntity,
    getSheetIdFromSheetEntity,
    getString,
    splitEmailAddress,
)
from gam.util.csv_pf import CSVPrintFile, FormatJSONQuoteChar, showJSON
from gam.util.display import (
    entityActionFailedWarning,
    entityActionNotPerformedWarning,
    entityActionPerformed,
    entityActionPerformedMessage,
    entityModifierNewValueActionFailedWarning,
    entityModifierNewValueActionPerformed,
    entityModifierNewValueItemValueListActionPerformed,
    entityModifierNewValueKeyValueActionPerformed,
    entityPerformActionNumItemsModifier,
    getPageMessageForWhom,
    invalidQuery,
    printGettingAllEntityItemsForWhom,
    printLine,
    userDriveServiceNotEnabledWarning,
)
from gam.util.entity import (
    getEntityArgument,
    splitEmailAddressOrUID,
)
from gam.util.errors import invalidChoiceExit, unknownArgumentExit
from gam.util.fileio import (
    cleanFilename,
    closeFile,
    setFilePath,
    uniqueFilename,
    writeFile,
)
from gam.util.output import setSysExitRC, writeStderr, formatFileSize
from gam.constants import MY_NON_TRASHED_FOLDER_NAME
from gam.util.tags import _substituteForUser

from gam.var import Act, Cmd, Ent, Ind

APPLICATION_VND_GOOGLE_APPS = 'application/vnd.google-apps.'
MIMETYPE_GA_DOCUMENT = f'{APPLICATION_VND_GOOGLE_APPS}document'
MIMETYPE_GA_DRAWING = f'{APPLICATION_VND_GOOGLE_APPS}drawing'
MIMETYPE_GA_FILE = f'{APPLICATION_VND_GOOGLE_APPS}file'
MIMETYPE_GA_FOLDER = f'{APPLICATION_VND_GOOGLE_APPS}folder'
MIMETYPE_GA_FORM = f'{APPLICATION_VND_GOOGLE_APPS}form'
MIMETYPE_GA_FUSIONTABLE = f'{APPLICATION_VND_GOOGLE_APPS}fusiontable'
MIMETYPE_GA_JAM = f'{APPLICATION_VND_GOOGLE_APPS}jam'
MIMETYPE_GA_MAP = f'{APPLICATION_VND_GOOGLE_APPS}map'
MIMETYPE_GA_PRESENTATION = f'{APPLICATION_VND_GOOGLE_APPS}presentation'
MIMETYPE_GA_SCRIPT = f'{APPLICATION_VND_GOOGLE_APPS}script'
MIMETYPE_GA_SCRIPT_JSON = f'{APPLICATION_VND_GOOGLE_APPS}script+json'
MIMETYPE_GA_SHORTCUT = f'{APPLICATION_VND_GOOGLE_APPS}shortcut'
MIMETYPE_GA_3P_SHORTCUT = f'{APPLICATION_VND_GOOGLE_APPS}drive-sdk'
MIMETYPE_GA_SITE = f'{APPLICATION_VND_GOOGLE_APPS}site'
MIMETYPE_GA_SPREADSHEET = f'{APPLICATION_VND_GOOGLE_APPS}spreadsheet'
ME_IN_OWNERS = "'me' in owners"
ME_IN_OWNERS_AND = ME_IN_OWNERS + " and "
NOT_ME_IN_OWNERS = "not " + ME_IN_OWNERS
NOT_ME_IN_OWNERS_AND = NOT_ME_IN_OWNERS + " and "
WITH_ANY_FILE_NAME = "name = '{0}'"
WITH_MY_FILE_NAME = ME_IN_OWNERS_AND + WITH_ANY_FILE_NAME
WITH_OTHER_FILE_NAME = NOT_ME_IN_OWNERS_AND + WITH_ANY_FILE_NAME
ROOT = 'root'
ORPHANS = 'Orphans'
SHARED_WITHME = 'SharedWithMe'
SHARED_DRIVES = 'SharedDrives'

UNKNOWN = 'Unknown'
ORPHANS_COLLECTED_RC = 30

def deleteDriveFile(users, function=None):
  fileIdEntity = getDriveFileEntity()
  if not function:
    function = getChoice(DELETE_DRIVEFILE_CHOICE_MAP, defaultChoice='trash', mapChoice=True)
  if checkArgumentPresent('shortcutandtarget'):
    shortcutAndTarget = getBoolean()
  else:
    shortcutAndTarget = False
  checkForExtraneousArguments()
  Act.Set(DELETE_DRIVEFILE_FUNCTION_TO_ACTION_MAP[function])
  if function != 'delete':
    trash_body = {'trashed': function == 'trash'}
  i, count, users = getEntityArgument(users)
  for user in users:
    i += 1
    user, drive, jcount = _validateUserGetFileIDs(user, i, count, fileIdEntity, entityType=Ent.DRIVE_FILE_OR_FOLDER)
    if jcount == 0:
      continue
    Ind.Increment()
    j = 0
    for fileId in fileIdEntity['list']:
      j += 1
      try:
        fileInfoList = []
        if shortcutAndTarget:
          capability = DELETE_DRIVEFILE_FUNCTION_TO_CAPABILITY_MAP[function]
          fileInfo = (fileId, Ent.DRIVE_FILE_OR_FOLDER, Ent.DRIVE_FILE_OR_FOLDER_ID)
          result = callGAPI(drive.files(), 'get',
                            throwReasons=GAPI.DRIVE_GET_THROW_REASONS,
                            fileId=fileId, fields=f'name,mimeType,shortcutDetails,capabilities({capability})', supportsAllDrives=True)
          if result['mimeType'] == MIMETYPE_GA_SHORTCUT:
            if not result['capabilities'][capability]:
              entityActionNotPerformedWarning([Ent.USER, user, Ent.DRIVE_SHORTCUT, result['name']],
                                              Msg.SHORTCUT_TARGET_CAPABILITY_IS_FALSE.format('Shortcut', capability), j, jcount)
              continue
            fileInfoList.append((fileId, Ent.DRIVE_SHORTCUT, Ent.DRIVE_SHORTCUT_ID))
            fileId = result['shortcutDetails']['targetId']
            fileInfo = (fileId, Ent.DRIVE_FILE_OR_FOLDER, Ent.DRIVE_FILE_OR_FOLDER_ID)
            tresult = callGAPI(drive.files(), 'get',
                               throwReasons=GAPI.DRIVE_GET_THROW_REASONS,
                               fileId=fileId, fields=f'name,capabilities({capability})', supportsAllDrives=True)
            if not tresult['capabilities'][capability]:
              entityActionNotPerformedWarning([Ent.USER, user, Ent.DRIVE_SHORTCUT, result['name'], Ent.DRIVE_FILE_OR_FOLDER, tresult['name']],
                                              Msg.SHORTCUT_TARGET_CAPABILITY_IS_FALSE.format('Target', capability), j, jcount)
              continue
        fileInfoList.append((fileId, Ent.DRIVE_FILE_OR_FOLDER, Ent.DRIVE_FILE_OR_FOLDER_ID))
        for fileInfo in fileInfoList:
          fileId = fileInfo[0]
          if function != 'delete':
            result = callGAPI(drive.files(), 'update',
                              throwReasons=GAPI.DRIVE_ACCESS_THROW_REASONS+[GAPI.FILE_NEVER_WRITABLE],
                              fileId=fileId, body=trash_body, fields='name', supportsAllDrives=True)
            if result and 'name' in result:
              fileName = result['name']
            else:
              fileName = fileId
          else:
            callGAPI(drive.files(), function,
                     throwReasons=GAPI.DRIVE_ACCESS_THROW_REASONS+[GAPI.FILE_NEVER_WRITABLE],
                     fileId=fileId, supportsAllDrives=True)
            fileName = fileId
          entityActionPerformed([Ent.USER, user, fileInfo[1], fileName], j, jcount)
      except (GAPI.fileNotFound, GAPI.forbidden, GAPI.internalError, GAPI.insufficientFilePermissions, GAPI.unknownError, GAPI.fileNeverWritable) as e:
        entityActionFailedWarning([Ent.USER, user, fileInfo[2], fileId], str(e), j, jcount)
      except (GAPI.serviceNotAvailable, GAPI.authError, GAPI.domainPolicy) as e:
        userDriveServiceNotEnabledWarning(user, str(e), i, count)
        break
    Ind.Decrement()

# gam <UserTypeEntity> purge drivefile <DriveFileEntity> [shortcutandtarget [<Boolean>]]
def purgeDriveFile(users):
  deleteDriveFile(users, 'delete')

# gam <UserTypeEntity> trash drivefile <DriveFileEntity> [shortcutandtarget [<Boolean>]]
def trashDriveFile(users):
  deleteDriveFile(users, 'trash')

# gam <UserTypeEntity> untrash drivefile <DriveFileEntity> [shortcutandtarget [<Boolean>]]
def untrashDriveFile(users):
  deleteDriveFile(users, 'untrash')

NON_DOWNLOADABLE_MIMETYPES = [MIMETYPE_GA_FORM, MIMETYPE_GA_FUSIONTABLE, MIMETYPE_GA_MAP, MIMETYPE_GA_FOLDER, MIMETYPE_GA_SHORTCUT]

GOOGLEDOC_VALID_EXTENSIONS_MAP = {
  MIMETYPE_GA_DRAWING: ['.jpeg', '.jpg', '.pdf', '.png', '.svg'],
  MIMETYPE_GA_DOCUMENT: ['.docx', '.epub', '.html', '.odt', '.pdf', '.rtf', '.txt', '.zip'],
  MIMETYPE_GA_JAM: ['.pdf'],
  MIMETYPE_GA_PRESENTATION: ['.pdf', '.pptx', '.odp', '.txt'],
  MIMETYPE_GA_SCRIPT: ['.json'],
  MIMETYPE_GA_SPREADSHEET: ['.csv', '.ods', '.pdf', '.tsv', '.xlsx', '.zip'],
  }

MICROSOFT_FORMATS_LIST = [
  {'mime': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document', 'ext': '.docx'},
  {'mime': 'application/vnd.openxmlformats-officedocument.wordprocessingml.template', 'ext': '.dotx'},
  {'mime': 'application/vnd.openxmlformats-officedocument.presentationml.presentation', 'ext': '.pptx'},
  {'mime': 'application/vnd.openxmlformats-officedocument.presentationml.template', 'ext': '.potx'},
  {'mime': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet', 'ext': '.xlsx'},
  {'mime': 'application/vnd.openxmlformats-officedocument.spreadsheetml.template', 'ext': '.xltx'},
  {'mime': 'application/msword', 'ext': '.doc'},
  {'mime': 'application/msword', 'ext': '.dot'},
  {'mime': 'application/vnd.ms-powerpoint', 'ext': '.ppt'},
  {'mime': 'application/vnd.ms-powerpoint', 'ext': '.pot'},
  {'mime': 'application/vnd.ms-excel', 'ext': '.xls'},
  {'mime': 'application/vnd.ms-excel', 'ext': '.xlt'},
  ]

OPENOFFICE_FORMATS_LIST = [
  {'mime': 'application/vnd.oasis.opendocument.presentation', 'ext': '.odp'},
  {'mime': 'application/x-vnd.oasis.opendocument.spreadsheet', 'ext': '.ods'},
  {'mime': 'application/vnd.oasis.opendocument.spreadsheet', 'ext': '.ods'},
  {'mime': 'application/vnd.oasis.opendocument.text', 'ext': '.odt'},
  ]

DOCUMENT_FORMATS_MAP = {
  'csv': [{'mime': 'text/csv', 'ext': '.csv'}],
  'doc': [{'mime': 'application/msword', 'ext': '.doc'}],
  'dot': [{'mime': 'application/msword', 'ext': '.dot'}],
  'docx': [{'mime': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document', 'ext': '.docx'}],
  'dotx': [{'mime': 'application/vnd.openxmlformats-officedocument.wordprocessingml.template', 'ext': '.dotx'}],
  'epub': [{'mime': 'application/epub+zip', 'ext': '.epub'}],
  'html': [{'mime': 'text/html', 'ext': '.html'}],
  'jpeg': [{'mime': 'image/jpeg', 'ext': '.jpeg'}],
  'jpg': [{'mime': 'image/jpeg', 'ext': '.jpg'}],
  'json': [{'mime': MIMETYPE_GA_SCRIPT_JSON, 'ext': '.json'}],
  'mht': [{'mime': 'message/rfc822', 'ext': 'mht'}],
  'odp': [{'mime': 'application/vnd.oasis.opendocument.presentation', 'ext': '.odp'}],
  'ods': [{'mime': 'application/x-vnd.oasis.opendocument.spreadsheet', 'ext': '.ods'},
          {'mime': 'application/vnd.oasis.opendocument.spreadsheet', 'ext': '.ods'}],
  'odt': [{'mime': 'application/vnd.oasis.opendocument.text', 'ext': '.odt'}],
  'pdf': [{'mime': 'application/pdf', 'ext': '.pdf'}],
  'png': [{'mime': 'image/png', 'ext': '.png'}],
  'ppt': [{'mime': 'application/vnd.ms-powerpoint', 'ext': '.ppt'}],
  'pot': [{'mime': 'application/vnd.ms-powerpoint', 'ext': '.pot'}],
  'potx': [{'mime': 'application/vnd.openxmlformats-officedocument.presentationml.template', 'ext': '.potx'}],
  'pptx': [{'mime': 'application/vnd.openxmlformats-officedocument.presentationml.presentation', 'ext': '.pptx'}],
  'rtf': [{'mime': 'application/rtf', 'ext': '.rtf'}],
  'svg': [{'mime': 'image/svg+xml', 'ext': '.svg'}],
  'tsv': [{'mime': 'text/tab-separated-values', 'ext': '.tsv'},
          {'mime': 'text/tsv', 'ext': '.tsv'}],
  'txt': [{'mime': 'text/plain', 'ext': '.txt'}],
  'xls': [{'mime': 'application/vnd.ms-excel', 'ext': '.xls'}],
  'xlt': [{'mime': 'application/vnd.ms-excel', 'ext': '.xlt'}],
  'xlsx': [{'mime': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet', 'ext': '.xlsx'}],
  'xltx': [{'mime': 'application/vnd.openxmlformats-officedocument.spreadsheetml.template', 'ext': '.xltx'}],
  'zip': [{'mime': 'application/zip', 'ext': '.zip'}],
  }

MIMETYPE_EXTENSION_MAP = {
  'application/epub+zip': '.epub',
  'application/msword': '.doc',
  'application/octet-stream': '',
  'application/pdf': '.pdf',
  'application/rtf': '.rtf',
  'application/vnd.ms-excel': '.xls',
  'application/vnd.ms-powerpoint': '.ppt',
  'application/vnd.oasis.opendocument.presentation': '.odp',
  'application/vnd.oasis.opendocument.spreadsheet': '.ods',
  'application/vnd.oasis.opendocument.text': '.odt',
  'application/vnd.openxmlformats-officedocument.presentationml.presentation': '.pptx',
  'application/vnd.openxmlformats-officedocument.presentationml.template': '.potx',
  'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet': '.xlsx',
  'application/vnd.openxmlformats-officedocument.spreadsheetml.template': '.xltx',
  'application/vnd.openxmlformats-officedocument.wordprocessingml.document': '.docx',
  'application/vnd.openxmlformats-officedocument.wordprocessingml.template': '.dotx',
  'application/x-vnd.oasis.opendocument.spreadsheet': '.ods',
  'application/zip': '.zip',
  'image/gif': '.gif',
  'image/jpeg': '.jpg',
  'image/jpg': '.jpg',
  'image/png': '.png',
  'image/svg+xml': '.svg',
  'image/webp': '.webp',
  'message/rfc822': 'mht',
  'text/csv': '.csv',
  'text/html': '.html',
  'text/plain': '.txt',
  'text/rtf': '.rtf',
  'text/tab-separated-values': '.tsv',
  'text/tsv': '.tsv',
  }

HTTP_ERROR_PATTERN = re.compile(r'^.*returned "(.*)">$')

# gam <UserTypeEntity> get drivefile <DriveFileEntity> [revision <DriveFileRevisionID>]
#	[(format <FileFormatList>)|(gsheet|csvsheet <SheetEntity>)] [exportsheetaspdf <String>]
#	[targetfolder <FilePath>] [targetname -|<FileName>]
#	[donotfollowshortcuts [<Boolean>]] [overwrite [<Boolean>]] [showprogress [<Boolean>]]
#	[acknowledgeabuse [<Boolean>]]
def getDriveFile(users):
  def closeRemoveTargetFile(f):
    if f and not targetStdout:
      closeFile(f)
      os.remove(filename)

  fileIdEntity = getDriveFileEntity()
  sheetEntity = None
  exportSheetAsPDF = revisionId = ''
  exportFormatName = 'openoffice'
  exportFormatChoices = [exportFormatName]
  exportFormats = OPENOFFICE_FORMATS_LIST
  defaultFormats = True
  targetFolderPattern = GC.Values[GC.DRIVE_DIR]
  targetNamePattern = None
  acknowledgeAbuse = donotFollowShortcuts = overwrite = showProgress = suppressStdoutMsgs = targetStdout = False
  while Cmd.ArgumentsRemaining():
    myarg = getArgument()
    if myarg == 'format':
      exportFormatChoices = getString(Cmd.OB_FORMAT_LIST).replace(',', ' ').lower().split()
      exportFormats = []
      for exportFormat in exportFormatChoices:
        if exportFormat in {'ms', 'microsoft', 'micro$oft'}:
          exportFormats.extend(MICROSOFT_FORMATS_LIST)
        elif exportFormat == 'openoffice':
          exportFormats.extend(OPENOFFICE_FORMATS_LIST)
        elif exportFormat in DOCUMENT_FORMATS_MAP:
          exportFormats.extend(DOCUMENT_FORMATS_MAP[exportFormat])
        else:
          invalidChoiceExit(exportFormat, DOCUMENT_FORMATS_MAP, True)
      defaultFormats = False
    elif myarg == 'targetfolder':
      targetFolderPattern = setFilePath(getString(Cmd.OB_FILE_PATH), GC.DRIVE_DIR)
    elif myarg == 'targetname':
      targetNamePattern = getString(Cmd.OB_FILE_NAME)
      targetStdout = targetNamePattern == '-'
      suppressStdoutMsgs = False if not targetStdout else GM.Globals[GM.STDOUT][GM.REDIRECT_STD]
    elif myarg == 'donotfollowshortcuts':
      donotFollowShortcuts = getBoolean()
    elif myarg == 'overwrite':
      overwrite = getBoolean()
    elif myarg == 'revision':
      revisionId = getString(Cmd.OB_DRIVE_FILE_REVISION_ID)
    elif myarg in {'gsheet', 'csvsheet'}:
      sheetEntity = getSheetEntity(False)
    elif myarg == 'exportsheetaspdf':
      exportSheetAsPDF = getString(Cmd.OB_STRING, minLen=0)
    elif myarg == 'nocache':
      pass
    elif myarg == 'showprogress':
      showProgress = getBoolean()
    elif myarg == 'acknowledgeabuse':
      acknowledgeAbuse = getBoolean()
    else:
      unknownArgumentExit()
  if exportSheetAsPDF:
    exportFormatName = 'pdf'
    exportFormatChoices = [exportFormatName]
    exportFormats = DOCUMENT_FORMATS_MAP[exportFormatName]
  elif sheetEntity:
    if defaultFormats:
      exportFormatName = 'csv'
    else:
      exportFormatName = exportFormats[0]['ext'][1:]
    exportFormatChoices = [exportFormatName]
    exportFormats = DOCUMENT_FORMATS_MAP[exportFormatName]
  i, count, users = getEntityArgument(users)
  for user in users:
    i += 1
    user, drive, jcount = _validateUserGetFileIDs(user, i, count, fileIdEntity, entityType=Ent.DRIVE_FILE if not suppressStdoutMsgs else None)
    if jcount == 0:
      continue
    _, userName, _ = splitEmailAddressOrUID(user)
    if exportSheetAsPDF or sheetEntity:
      _, sheet = buildGAPIServiceObject(API.SHEETS, user, i, count)
      if not sheet:
        continue
    targetFolder = _substituteForUser(targetFolderPattern, user, userName)
    if not os.path.isdir(targetFolder):
      os.makedirs(targetFolder)
    targetName = _substituteForUser(targetNamePattern, user, userName) if targetNamePattern else None
    Ind.Increment()
    j = 0
    for fileId in fileIdEntity['list']:
      j += 1
      fileExtension = None
      try:
        result = callGAPI(drive.files(), 'get',
                          throwReasons=GAPI.DRIVE_GET_THROW_REASONS,
                          fileId=fileId, fields='name,fullFileExtension,mimeType,quotaBytesUsed,shortcutDetails', supportsAllDrives=True)
        mimeType = result['mimeType']
        if (mimeType == MIMETYPE_GA_SHORTCUT) and not donotFollowShortcuts:
          fileId = result['shortcutDetails']['targetId']
          result = callGAPI(drive.files(), 'get',
                            throwReasons=GAPI.DRIVE_GET_THROW_REASONS,
                            fileId=fileId, fields='name,fullFileExtension,mimeType,size', supportsAllDrives=True)
          mimeType = result['mimeType']
        entityValueList = [Ent.USER, user, _getEntityMimeType(result), result['name']]
        if mimeType in NON_DOWNLOADABLE_MIMETYPES:
          entityActionNotPerformedWarning(entityValueList, Msg.FORMAT_NOT_DOWNLOADABLE, j, jcount)
          continue
        if revisionId:
          callGAPI(drive.revisions(), 'get',
                   throwReasons=GAPI.DRIVE_GET_THROW_REASONS+[GAPI.REVISION_NOT_FOUND],
                   fileId=fileId, revisionId=revisionId, fields='id')
        fileExtension = result.get('fullFileExtension')
        googleDocExtensions = GOOGLEDOC_VALID_EXTENSIONS_MAP.get(mimeType)
        if googleDocExtensions:
          my_line = ['Type', 'Google Doc']
          googleDoc = True
          for exportFormat in exportFormats:
            if exportFormat['ext'] in googleDocExtensions:
              exportMimeType = exportFormat['mime']
              if fileExtension:
                extension = '.'+fileExtension
              else:
                extension = exportFormat['ext']
              break
          else:
            entityActionNotPerformedWarning(entityValueList, Msg.FORMAT_NOT_AVAILABLE.format(','.join(exportFormatChoices)), j, jcount)
            continue
        else:
          if 'quotaBytesUsed' in result:
            my_line = ['Size', formatFileSize(int(result['quotaBytesUsed']))]
          else:
            my_line = ['Size', UNKNOWN]
          googleDoc = False
          if fileExtension:
            extension = '.'+fileExtension
          else:
            extension = MIMETYPE_EXTENSION_MAP.get(mimeType, '')
        while True:
          if targetStdout:
            filename = 'stdout'
          else:
            filename, _ = uniqueFilename(targetFolder, targetName or cleanFilename(result['name']), overwrite, extension)
          spreadsheetUrl = None
          f = None
          try:
            if googleDoc:
              if (not exportSheetAsPDF and not sheetEntity) or mimeType != MIMETYPE_GA_SPREADSHEET:
                request = drive.files().export_media(fileId=fileId, mimeType=exportMimeType)
                if revisionId:
                  request.uri = f'{request.uri}&revision={revisionId}'
              else:
                spreadsheet = callGAPI(sheet.spreadsheets(), 'get',
                                       throwReasons=GAPI.SHEETS_ACCESS_THROW_REASONS,
                                       spreadsheetId=fileId, fields='spreadsheetUrl,sheets(properties(sheetId,title))')
#                spreadsheetUrl = f'{re.sub("/edit.*$", "/export", spreadsheet["spreadsheetUrl"])}?exportFormat={exportFormatName}&format={exportFormatName}&id={fileId}'
                spreadsheetUrl = f'{re.sub("/edit.*$", "/export", spreadsheet["spreadsheetUrl"])}?format={exportFormatName}&id={fileId}'
                if sheetEntity:
                  entityValueList.extend([sheetEntity['sheetType'], sheetEntity['sheetValue']])
                  sheetId = getSheetIdFromSheetEntity(spreadsheet, sheetEntity)
                  if sheetId is None:
                    entityActionNotPerformedWarning(entityValueList, Msg.NOT_FOUND, j, jcount)
                    break
                  spreadsheetUrl += f'&gid={sheetId}'
                spreadsheetUrl += exportSheetAsPDF
            else:
              if revisionId:
                entityValueList.extend([Ent.DRIVE_FILE_REVISION, revisionId])
                request = drive.revisions().get_media(fileId=fileId, revisionId=revisionId)
              else:
                request = drive.files().get_media(fileId=fileId, acknowledgeAbuse=acknowledgeAbuse)
            if not targetStdout:
              f = open(filename, 'wb')
            else:
              f = os.fdopen(os.dup(sys.stdout.fileno()), 'wb')
            if not spreadsheetUrl:
              downloader = googleapiclient.http.MediaIoBaseDownload(f, request)
              done = False
              while not done:
                status, done = downloader.next_chunk()
                if showProgress and not suppressStdoutMsgs and status.progress() < 1.0:
                  entityActionPerformedMessage(entityValueList, f'{status.progress():>7.2%}', j, jcount)
            else:
              if GC.Values[GC.DEBUG_LEVEL] > 0:
                sys.stderr.write(f'Debug: spreadsheetUrl: {spreadsheetUrl}\n')
              maxRetries = 10
              sleepTime = 5
              for retry in range(1, maxRetries+1):
                status, content = drive._http.request(uri=spreadsheetUrl, method='GET')
                if status['status'] != '429':
                  break
                writeStderr(Msg.RETRYING_GOOGLE_SHEET_EXPORT_SLEEPING.format(retry, maxRetries, sleepTime))
                time.sleep(sleepTime)
              if status['status'] == '200':
                f.write(content)
                if targetStdout and content[-1] != '\n':
                  f.write(bytes('\n', UTF8))
              else:
                entityModifierNewValueActionFailedWarning(entityValueList, Act.MODIFIER_TO, filename, f'HTTP Error: {status["status"]}', j, jcount)
                closeRemoveTargetFile(f)
                break
            if not targetStdout:
              closeFile(f)
            if not suppressStdoutMsgs:
              entityModifierNewValueKeyValueActionPerformed(entityValueList, Act.MODIFIER_TO, filename, my_line[0], my_line[1], j, jcount)
            break
          except (IOError, httplib2.HttpLib2Error) as e:
            entityModifierNewValueActionFailedWarning(entityValueList, Act.MODIFIER_TO, filename, str(e), j, jcount)
          except googleapiclient.http.HttpError as e:
            mg = HTTP_ERROR_PATTERN.match(str(e))
            if mg:
              entityModifierNewValueActionFailedWarning(entityValueList, Act.MODIFIER_TO, filename, mg.group(1), j, jcount)
            else:
              entityModifierNewValueActionFailedWarning(entityValueList, Act.MODIFIER_TO, filename, str(e), j, jcount)
          closeRemoveTargetFile(f)
          break
      except GAPI.fileNotFound:
        entityActionFailedWarning([Ent.USER, user, Ent.DRIVE_FILE_OR_FOLDER_ID, fileId], Msg.DOES_NOT_EXIST, j, jcount)
      except GAPI.revisionNotFound:
        entityActionFailedWarning([Ent.USER, user, Ent.DRIVE_FILE_OR_FOLDER_ID, fileId, Ent.DRIVE_FILE_REVISION, revisionId], Msg.DOES_NOT_EXIST, j, jcount)
      except (GAPI.notFound, GAPI.forbidden, GAPI.permissionDenied,
              GAPI.internalError, GAPI.insufficientFilePermissions, GAPI.badRequest,
              GAPI.invalid, GAPI.invalidArgument, GAPI.failedPrecondition) as e:
        entityActionFailedWarning([Ent.USER, user, Ent.SPREADSHEET, fileId], str(e), j, jcount)
      except (GAPI.serviceNotAvailable, GAPI.authError, GAPI.domainPolicy) as e:
        userDriveServiceNotEnabledWarning(user, str(e), i, count)
        break
    Ind.Decrement()

SUGGESTIONS_VIEW_MODE_CHOICE_MAP = {
  'default': 'DEFAULT_FOR_CURRENT_ACCESS',
  'suggestionsinline': 'SUGGESTIONS_INLINE',
  'previewsuggestionsaccepted': 'PREVIEW_SUGGESTIONS_ACCEPTED',
  'previewwithoutsuggestions': 'PREVIEW_WITHOUT_SUGGESTIONS'
  }

# gam <UserTypeEntity> get document <DriveFileEntity>
#	[viewmode default|suggestions_inline|preview_suggestions_accepted|preview_without_suggestions]
#	[targetfolder <FilePath>] [targetname <FileName>]
#	[donotfollowshortcuts [<Boolean>]] [overwrite [<Boolean>]]
def getGoogleDocument(users):
  fileIdEntity = getDriveFileEntity()
  suggestionsViewMode = SUGGESTIONS_VIEW_MODE_CHOICE_MAP['default']
  targetFolderPattern = GC.Values[GC.DRIVE_DIR]
  targetNamePattern = None
  donotFollowShortcuts = overwrite = False
  while Cmd.ArgumentsRemaining():
    myarg = getArgument()
    if myarg == 'viewmode':
      suggestionsViewMode = getChoice(SUGGESTIONS_VIEW_MODE_CHOICE_MAP, mapChoice=True)
    elif myarg == 'targetfolder':
      targetFolderPattern = setFilePath(getString(Cmd.OB_FILE_PATH), GC.DRIVE_DIR)
    elif myarg == 'targetname':
      targetNamePattern = getString(Cmd.OB_FILE_NAME)
    elif myarg == 'donotfollowshortcuts':
      donotFollowShortcuts = getBoolean()
    elif myarg == 'overwrite':
      overwrite = getBoolean()
    else:
      unknownArgumentExit()
  i, count, users = getEntityArgument(users)
  for user in users:
    i += 1
    user, drive, jcount = _validateUserGetFileIDs(user, i, count, fileIdEntity, entityType=Ent.DOCUMENT)
    if jcount == 0:
      continue
    _, docs = buildGAPIServiceObject(API.DOCS, user, i, count)
    if not docs:
      continue
    _, userName, _ = splitEmailAddressOrUID(user)
    targetFolder = _substituteForUser(targetFolderPattern, user, userName)
    if not os.path.isdir(targetFolder):
      os.makedirs(targetFolder)
    targetName = _substituteForUser(targetNamePattern, user, userName) if targetNamePattern else None
    Ind.Increment()
    j = 0
    for fileId in fileIdEntity['list']:
      j += 1
      try:
        result = callGAPI(drive.files(), 'get',
                          throwReasons=GAPI.DRIVE_GET_THROW_REASONS,
                          fileId=fileId, fields='name,mimeType,shortcutDetails', supportsAllDrives=True)
        mimeType = result['mimeType']
        if (mimeType == MIMETYPE_GA_SHORTCUT) and not donotFollowShortcuts:
          fileId = result['shortcutDetails']['targetId']
          result = callGAPI(drive.files(), 'get',
                            throwReasons=GAPI.DRIVE_GET_THROW_REASONS,
                            fileId=fileId, fields='name,mimeType', supportsAllDrives=True)
          mimeType = result['mimeType']
        docName = result['name']
        if mimeType != MIMETYPE_GA_DOCUMENT:
          entityActionNotPerformedWarning([Ent.USER, user, Ent.DRIVE_FILE, docName],
                                          Msg.INVALID_MIMETYPE.format(mimeType, MIMETYPE_GA_DOCUMENT), j, jcount)
          continue
        filename, _ = uniqueFilename(targetFolder, targetName or cleanFilename(docName), overwrite)
        result = callGAPI(docs.documents(), 'get',
                          throwReasons=GAPI.DRIVE_GET_THROW_REASONS,
                          documentId=fileId, suggestionsViewMode=suggestionsViewMode)
        if writeFile(filename, json.dumps(result, indent=2, sort_keys=True)+'\n', continueOnError=True):
          entityModifierNewValueActionPerformed([Ent.USER, user, Ent.DOCUMENT, f'{docName}({fileId})'], Act.MODIFIER_TO, filename, j, jcount)
      except GAPI.fileNotFound:
        entityActionFailedWarning([Ent.USER, user, Ent.DOCUMENT, fileId], Msg.DOES_NOT_EXIST, j, jcount)
      except (GAPI.serviceNotAvailable, GAPI.authError, GAPI.domainPolicy) as e:
        userDriveServiceNotEnabledWarning(user, str(e), i, count)
        break
    Ind.Decrement()

# gam <UserTypeEntity> update docuument <DriveFileEntity>
#	((json [charset <Charset>] <SpreadsheetJSONUpdateRequest>) |
#	 (json file <FileName> [charset <Charset>]))
#	[formatjson]
def updateGoogleDocument(users):
  fileIdEntity = getDriveFileEntity()
  body = {}
  FJQC = FormatJSONQuoteChar()
  while Cmd.ArgumentsRemaining():
    myarg = getArgument()
    if myarg == 'json':
      body = getJSON([])
    else:
      FJQC.GetFormatJSON(myarg)
  i, count, users = getEntityArgument(users)
  for user in users:
    i += 1
    user, _, jcount = _validateUserGetFileIDs(user, i, count, fileIdEntity, entityType=Ent.DOCUMENT if not FJQC.formatJSON else None)
    if jcount == 0:
      continue
    _, docs = buildGAPIServiceObject(API.DOCS, user, i, count)
    if not docs:
      continue
    Ind.Increment()
    j = 0
    for documentId in fileIdEntity['list']:
      j += 1
      try:
        result = callGAPI(docs.documents(), 'batchUpdate',
                          throwReasons=GAPI.DOCS_ACCESS_THROW_REASONS,
                          documentId=documentId, body=body)
        if FJQC.formatJSON:
          printLine('{'+f'"User": "{user}", "documentId": "{documentId}", "JSON": {json.dumps(result, ensure_ascii=False, sort_keys=False)}'+'}')
          continue
        entityActionPerformed([Ent.USER, user, Ent.DOCUMENT, documentId], j, jcount)
        Ind.Increment()
        for field in ['replies', 'writeControl']:
          if field in result:
            showJSON(field, result[field])
        Ind.Decrement()
      except (GAPI.fileNotFound, GAPI.forbidden, GAPI.permissionDenied,
              GAPI.internalError, GAPI.insufficientFilePermissions, GAPI.badRequest,
              GAPI.invalid, GAPI.invalidArgument, GAPI.failedPrecondition) as e:
        entityActionFailedWarning([Ent.USER, user, Ent.DOCUMENT, documentId], str(e), j, jcount)
      except (GAPI.serviceNotAvailable, GAPI.authError, GAPI.domainPolicy) as e:
        userDriveServiceNotEnabledWarning(user, str(e), i, count)
        break
    Ind.Decrement()

# gam <UserTypeEntity> collect orphans
#	[(targetuserfoldername <DriveFolderName>)(targetuserfolderid <DriveFolderID>)]
#	[useshortcuts [<Boolean>]]
#	(orderby <DriveFileOrderByFieldName> [ascending|descending])*
#	[preview] [todrive <ToDriveAttribute>*]
def collectOrphans(users):
  OBY = OrderBy(DRIVEFILE_ORDERBY_CHOICE_MAP)
  csvPF = None
  targetParms = initDriveFileAttributes()
  targetUserFolderId = None
  targetUserFolderPattern = '#user# orphaned files'
  targetParentBody = {}
  query = ME_IN_OWNERS_AND+'trashed = false'
  useShortcuts = False
  while Cmd.ArgumentsRemaining():
    myarg = getArgument()
    if myarg == 'orderby':
      OBY.GetChoice()
    elif myarg == 'targetuserfoldername':
      targetUserFolderPattern = getString(Cmd.OB_DRIVE_FOLDER_NAME)
      targetUserFolderId = None
    elif myarg == 'targetuserfolderid':
      targetUserFolderId = getString(Cmd.OB_DRIVE_FOLDER_ID)
      targetUserFolderPattern = None
    elif myarg == 'useshortcuts':
      useShortcuts = getBoolean()
    elif myarg == 'preview':
      csvPF = CSVPrintFile(['Owner', 'type', 'id', 'name', 'action'])
    elif csvPF and myarg == 'todrive':
      csvPF.GetTodriveParameters()
    else:
      unknownArgumentExit()
  i, count, users = getEntityArgument(users)
  for user in users:
    i += 1
    user, drive = buildGAPIServiceObject(API.DRIVE3, user, i, count)
    if not drive:
      continue
    userName, _ = splitEmailAddress(user)
    try:
      printGettingAllEntityItemsForWhom(Ent.DRIVE_FILE_OR_FOLDER, Ent.TypeName(Ent.USER, user), i, count, query=query)
      feed = callGAPIpages(drive.files(), 'list', 'files',
                           pageMessage=getPageMessageForWhom(),
                           throwReasons=GAPI.DRIVE_USER_THROW_REASONS,
                           retryReasons=[GAPI.UNKNOWN_ERROR],
                           q=query, orderBy=OBY.orderBy,
                           fields='nextPageToken,files(id,name,parents,mimeType,sharedWithMeTime,capabilities(canMoveItemWithinDrive))',
                           pageSize=GC.Values[GC.DRIVE_MAX_RESULTS])
      if targetUserFolderPattern:
        trgtUserFolderName = _substituteForUser(targetUserFolderPattern, user, userName)
        targetParms[DFA_PARENTQUERY] = MY_NON_TRASHED_FOLDER_NAME.format(escapeDriveFileName(trgtUserFolderName))
      else:
        targetParms[DFA_PARENTID] = targetUserFolderId
        trgtUserFolderName = targetUserFolderId
      if not _getDriveFileParentInfo(drive, user, i, count, targetParentBody, targetParms, True, False):
        continue
      orphanDriveFiles = []
      for fileEntry in feed:
        if not fileEntry.get('parents') and 'sharedWithMeTime' not in fileEntry:
          orphanDriveFiles.append(fileEntry)
      jcount = len(orphanDriveFiles)
      entityPerformActionNumItemsModifier([Ent.USER, user], jcount, Ent.DRIVE_ORPHAN_FILE_OR_FOLDER,
                                          f'{Act.MODIFIER_INTO} {Ent.Singular(Ent.DRIVE_FOLDER)}: {trgtUserFolderName}', i, count)
      if jcount == 0:
        continue
      if not csvPF:
        if 'parents' not in targetParentBody or not targetParentBody['parents']:
          try:
            newParentId = callGAPI(drive.files(), 'create',
                                   throwReasons=GAPI.DRIVE_USER_THROW_REASONS+[GAPI.FORBIDDEN, GAPI.INSUFFICIENT_PERMISSIONS, GAPI.INSUFFICIENT_PARENT_PERMISSIONS,
                                                                               GAPI.UNKNOWN_ERROR, GAPI.STORAGE_QUOTA_EXCEEDED,
                                                                               GAPI. TEAMDRIVE_FILE_LIMIT_EXCEEDED, GAPI.TEAMDRIVE_HIERARCHY_TOO_DEEP],
                                   body={'name': trgtUserFolderName, 'mimeType': MIMETYPE_GA_FOLDER}, fields='id')['id']
          except (GAPI.forbidden, GAPI.insufficientPermissions, GAPI.insufficientParentPermissions,
                  GAPI.unknownError, GAPI.storageQuotaExceeded, GAPI.teamDriveFileLimitExceeded, GAPI.teamDriveHierarchyTooDeep) as e:
            entityActionFailedWarning([Ent.USER, user, Ent.DRIVE_FOLDER, trgtUserFolderName], str(e), i, count)
            continue
        else:
          newParentId = targetParentBody['parents'][0]
      setSysExitRC(ORPHANS_COLLECTED_RC)
      Ind.Increment()
      j = 0
      for fileEntry in orphanDriveFiles:
        j += 1
        fileId = fileEntry['id']
        fileName = fileEntry['name']
        fileType = _getEntityMimeType(fileEntry)
# Deleted 6.26.16
#        if fileType == Ent.DRIVE_FOLDER and not fileEntry['capabilities']['canAddMyDriveParent']:
#          # Typically Google Backup & Sync images of laptops
#          continue
        if not useShortcuts and fileEntry['capabilities']['canMoveItemWithinDrive']:
          if csvPF:
            csvPF.WriteRow({'Owner': user, 'type': Ent.Singular(fileType), 'id': fileId, 'name': fileName, 'action': 'changeParent'})
            continue
          try:
            callGAPI(drive.files(), 'update',
                     bailOnInternalError=True,
                     throwReasons=GAPI.DRIVE_USER_THROW_REASONS+[GAPI.BAD_REQUEST, GAPI.FILE_NOT_FOUND,
                                                                 GAPI.INTERNAL_ERROR, GAPI.INSUFFICIENT_PARENT_PERMISSIONS],
                     retryReasons=[GAPI.FILE_NOT_FOUND],
                     fileId=fileId, body={}, addParents=newParentId, fields='')
            entityModifierNewValueItemValueListActionPerformed([Ent.USER, user, fileType, fileName],
                                                               Act.MODIFIER_INTO, None, [Ent.DRIVE_FOLDER, trgtUserFolderName], j, jcount)
          except (GAPI.badRequest, GAPI.fileNotFound, GAPI.internalError, GAPI.insufficientParentPermissions,) as e:
            entityActionFailedWarning([Ent.USER, user, fileType, fileName], str(e), j, jcount)
          except (GAPI.serviceNotAvailable, GAPI.authError, GAPI.domainPolicy) as e:
            userDriveServiceNotEnabledWarning(user, str(e), i, count)
            break
        else:
          if csvPF:
            csvPF.WriteRow({'Owner': user, 'type': Ent.Singular(fileType), 'id': fileId, 'name': fileName, 'action': 'createShortcut'})
            continue
          try:
            # Check for existing shortcut, do not duplicate
            files = callGAPIitems(drive.files(), 'list', 'files',
                                  throwReasons=GAPI.DRIVE_USER_THROW_REASONS+[GAPI.INVALID_QUERY, GAPI.INVALID],
                                  q=f"'me' in owners and name = '{escapeDriveFileName(fileName)}' and mimeType = '{MIMETYPE_GA_SHORTCUT}' and '{newParentId}' in parents and trashed = false",
                                  fields='files(id,shortcutDetails(targetId))')
            existingShortcut = False
            for f_file in files:
              if f_file['shortcutDetails']['targetId'] == fileId:
                entityActionNotPerformedWarning([Ent.USER, user, fileType, fileName, Ent.DRIVE_FILE_SHORTCUT, f"{fileName}({f_file['id']})"],
                                                Msg.ALREADY_EXISTS_IN_TARGET_FOLDER.format(Ent.Singular(Ent.DRIVE_FOLDER), trgtUserFolderName), j, jcount)
                existingShortcut = True
                break
            if existingShortcut:
              continue
            body = {'name': fileName, 'mimeType': MIMETYPE_GA_SHORTCUT, 'parents': [newParentId], 'shortcutDetails': {'targetId': fileId}}
            result = callGAPI(drive.files(), 'create',
                              throwReasons=GAPI.DRIVE_USER_THROW_REASONS+[GAPI.INVALID_QUERY, GAPI.FORBIDDEN, GAPI.INSUFFICIENT_PERMISSIONS, GAPI.INSUFFICIENT_PARENT_PERMISSIONS,
                                                                          GAPI.INVALID, GAPI.BAD_REQUEST, GAPI.FILE_NOT_FOUND, GAPI.UNKNOWN_ERROR,
                                                                          GAPI.STORAGE_QUOTA_EXCEEDED, GAPI.TEAMDRIVE_FILE_LIMIT_EXCEEDED, GAPI.TEAMDRIVE_HIERARCHY_TOO_DEEP,
                                                                          GAPI.SHORTCUT_TARGET_INVALID],
                              body=body, fields='id,name', supportsAllDrives=True)
            entityModifierNewValueItemValueListActionPerformed([Ent.USER, user, fileType, fileName, Ent.DRIVE_FILE_SHORTCUT, f'{result["name"]}({result["id"]})'],
                                                               Act.MODIFIER_INTO, None, [Ent.DRIVE_FOLDER, trgtUserFolderName], j, jcount)

          except GAPI.invalidQuery:
            entityActionFailedWarning([Ent.USER, user, fileType, fileName], invalidQuery(query), j, jcount)
          except (GAPI.forbidden, GAPI.insufficientFilePermissions, GAPI.insufficientParentPermissions, GAPI.invalid, GAPI.badRequest,
                  GAPI.fileNotFound, GAPI.unknownError, GAPI.storageQuotaExceeded, GAPI.teamDriveFileLimitExceeded, GAPI.teamDriveHierarchyTooDeep,
                  GAPI.shortcutTargetInvalid) as e:
            entityActionFailedWarning([Ent.USER, user, fileType, fileName, Ent.DRIVE_FILE_SHORTCUT, body['name']], str(e), j, jcount)
          except (GAPI.serviceNotAvailable, GAPI.authError, GAPI.domainPolicy) as e:
            userDriveServiceNotEnabledWarning(user, str(e), i, count)
            break
      Ind.Decrement()
    except (GAPI.serviceNotAvailable, GAPI.authError, GAPI.domainPolicy) as e:
      userDriveServiceNotEnabledWarning(user, str(e), i, count)
  if csvPF:
    csvPF.writeCSVfile('Orphans to Collect')

TRANSFER_DRIVEFILE_ACL_ROLES_MAP = {
  'commenter': 'commenter',
  'contentmanager': 'fileOrganizer',
  'contributor': 'writer',
  'editor': 'writer',
  'fileorganizer': 'fileOrganizer',
  'fileorganiser': 'fileOrganizer',
  'manager': 'organizer',
  'organizer': 'organizer',
  'organiser': 'organizer',
  'owner': 'organizer',
  'read': 'reader',
  'reader': 'reader',
  'viewer': 'reader',
  'writer': 'writer',
  'current': 'current',
  'none': 'none',
  'source': 'source',
  }

# gam <UserTypeEntity> transfer drive <UserItem> [select <DriveFileEntity>]
#	[(targetfolderid <DriveFolderID>)|(targetfoldername <DriveFolderName>)]
#	[targetuserfoldername <DriveFolderName>] [targetuserorphansfoldername <DriveFolderName>]
#	[mergewithtarget [<Boolean>]]
#	[createshortcutsfornonmovablefiles [<Boolean>]]
#	[skipids <DriveFileEntity>]
#	[keepuser | (retainrole reader|commenter|writer|editor|fileorganizer|none)] [noretentionmessages]
#	[nonowner_retainrole reader|commenter|writer|editor|fileorganizer|current|none]
#	[nonowner_targetrole reader|commenter|writer|editor|fileorganizer|current|none|source]
#	(orderby <DriveFileOrderByFieldName> [ascending|descending])*
#	[preview] [todrive <ToDriveAttribute>*]
