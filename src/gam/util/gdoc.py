"""GAM GDoc/GSheet/Cloud Storage data retrieval utilities.

Reading data from Google Docs, Google Sheets, Cloud Storage
buckets, and CSV files.
"""

import csv
import re
import sys
import time
from tempfile import TemporaryFile
from urllib.parse import unquote

import googleapiclient.http
import httplib2
import google.auth.exceptions

from gamlib import glapi as API
from gamlib import glcfg as GC
from gamlib import glentity
Ent = glentity.GamEntity()
from gamlib import glgapi as GAPI
from gamlib import glglobals as GM
from gamlib import glmsgs as Msg
from gam.var import Cmd
from gam.constants import DEFAULT_CSV_READ_MODE, NO_ENTITIES_FOUND_RC
from util.args import UTF8, checkArgumentPresent, getBoolean, getCharSet, getCharacter, getEmailAddress, getSheetEntity, getSheetIdFromSheetEntity, getString, shlexSplitList
from util.display import ACTION_NOT_PERFORMED_RC, userDriveServiceNotEnabledWarning
from util.errors import entityActionFailedExit, entityDoesNotExistExit
from util.fileio import FILE_ERROR_RC, UTF8_SIG, fileErrorMessage, getGDocSheetDataFailedExit, getGDocSheetDataRetryWarning, openFile, setFilePath
from util.output import stderrWarningMsg, systemErrorExit




GDOC_FORMAT_MIME_TYPES = {
  'gcsv': 'text/csv',
  'gdoc': 'text/plain',
  'ghtml': 'text/html',
  }

# gdoc <EmailAddress> <DriveFileIDEntity>|<DriveFileNameEntity>
def getGDocData(gformat):
  from util.api import buildGAPIObject, buildGAPIServiceObject, callGAPI
  mimeType = GDOC_FORMAT_MIME_TYPES[gformat]
  user = getEmailAddress()
  fileIdEntity = getDriveFileEntity(queryShortcutsOK=False)
  if not GC.Values[GC.COMMANDDATA_CLIENTACCESS]:
    _, drive = buildGAPIServiceObject(API.DRIVE3, user)
  else:
    drive = buildGAPIObject(API.DRIVE3)
  if not drive:
    sys.exit(GM.Globals[GM.SYSEXITRC])
  _, _, jcount = _validateUserGetFileIDs(user, 0, 0, fileIdEntity, drive=drive)
  if jcount == 0:
    getGDocSheetDataFailedExit([Ent.USER, user], Msg.NO_ENTITIES_FOUND.format(Ent.Singular(Ent.DRIVE_FILE)))
  if jcount > 1:
    getGDocSheetDataFailedExit([Ent.USER, user], Msg.MULTIPLE_ENTITIES_FOUND.format(Ent.Plural(Ent.DRIVE_FILE), jcount, ','.join(fileIdEntity['list'])))
  fileId = fileIdEntity['list'][0]
  f = None
  try:
    result = callGAPI(drive.files(), 'get',
                      throwReasons=GAPI.DRIVE_GET_THROW_REASONS,
                      fileId=fileId, fields='name,mimeType,exportLinks',
                      supportsAllDrives=True)
# Google Doc
    if 'exportLinks' in result:
      if mimeType not in result['exportLinks']:
        getGDocSheetDataFailedExit([Ent.USER, user, Ent.DRIVE_FILE, result['name']],
                                   Msg.INVALID_MIMETYPE.format(result['mimeType'], mimeType))
      f = TemporaryFile(mode='w+', encoding=UTF8)
      _, content = drive._http.request(uri=result['exportLinks'][mimeType], method='GET')
      f.write(content.decode(UTF8_SIG))
      f.seek(0)
      return f
# Drive File
    if result['mimeType'] != mimeType:
      getGDocSheetDataFailedExit([Ent.USER, user, Ent.DRIVE_FILE, result['name']],
                                 Msg.INVALID_MIMETYPE.format(result['mimeType'], mimeType))
    fb = TemporaryFile(mode='wb+')
    request = drive.files().get_media(fileId=fileId)
    downloader = googleapiclient.http.MediaIoBaseDownload(fb, request)
    done = False
    while not done:
      _, done = downloader.next_chunk()
    f = TemporaryFile(mode='w+', encoding=UTF8)
    fb.seek(0)
    f.write(fb.read().decode(UTF8_SIG))
    fb.close()
    f.seek(0)
    return f
  except GAPI.fileNotFound:
    getGDocSheetDataFailedExit([Ent.USER, user, Ent.DOCUMENT, fileId], Msg.DOES_NOT_EXIST)
  except (IOError, httplib2.HttpLib2Error, google.auth.exceptions.TransportError, RuntimeError) as e:
    if f:
      f.close()
    getGDocSheetDataFailedExit([Ent.USER, user, Ent.DOCUMENT, fileId], str(e))
  except (GAPI.serviceNotAvailable, GAPI.authError, GAPI.domainPolicy) as e:
    userDriveServiceNotEnabledWarning(user, str(e))
    sys.exit(GM.Globals[GM.SYSEXITRC])

HTML_TITLE_PATTERN = re.compile(r'.*<title>(.+)</title>')

# gsheet <EmailAddress> <DriveFileIDEntity>|<DriveFileNameEntity> <SheetEntity>
def getGSheetData():
  from util.api import buildGAPIObject, buildGAPIServiceObject, callGAPI
  user = getEmailAddress()
  fileIdEntity = getDriveFileEntity(queryShortcutsOK=False)
  sheetEntity = getSheetEntity(False)
  if not GC.Values[GC.COMMANDDATA_CLIENTACCESS]:
    user, drive = buildGAPIServiceObject(API.DRIVE3, user)
  else:
    drive = buildGAPIObject(API.DRIVE3)
  if not drive:
    sys.exit(GM.Globals[GM.SYSEXITRC])
  _, _, jcount = _validateUserGetFileIDs(user, 0, 0, fileIdEntity, drive=drive)
  if jcount == 0:
    getGDocSheetDataFailedExit([Ent.USER, user], Msg.NO_ENTITIES_FOUND.format(Ent.Singular(Ent.DRIVE_FILE)))
  if jcount > 1:
    getGDocSheetDataFailedExit([Ent.USER, user], Msg.MULTIPLE_ENTITIES_FOUND.format(Ent.Plural(Ent.DRIVE_FILE), jcount, ','.join(fileIdEntity['list'])))
  if not GC.Values[GC.COMMANDDATA_CLIENTACCESS]:
    _, sheet = buildGAPIServiceObject(API.SHEETS, user)
  else:
    sheet = buildGAPIObject(API.SHEETS)
  if not sheet:
    sys.exit(GM.Globals[GM.SYSEXITRC])
  fileId = fileIdEntity['list'][0]
  f = None
  try:
    result = callGAPI(drive.files(), 'get',
                      throwReasons=GAPI.DRIVE_GET_THROW_REASONS,
                      fileId=fileId, fields='name,mimeType', supportsAllDrives=True)
    if result['mimeType'] != MIMETYPE_GA_SPREADSHEET:
      getGDocSheetDataFailedExit([Ent.USER, user, Ent.DRIVE_FILE, result['name']],
                                 Msg.INVALID_MIMETYPE.format(result['mimeType'], MIMETYPE_GA_SPREADSHEET))
    spreadsheet = callGAPI(sheet.spreadsheets(), 'get',
                           throwReasons=GAPI.SHEETS_ACCESS_THROW_REASONS,
                           spreadsheetId=fileId, fields='spreadsheetUrl,sheets(properties(sheetId,title))')
    sheetId = getSheetIdFromSheetEntity(spreadsheet, sheetEntity)
    if sheetId is None:
      getGDocSheetDataFailedExit([Ent.USER, user, Ent.SPREADSHEET, result['name'], sheetEntity['sheetType'], sheetEntity['sheetValue']], Msg.NOT_FOUND)
    spreadsheetUrl = f'{re.sub("/edit.*$", "/export", spreadsheet["spreadsheetUrl"])}?format=csv&id={fileId}&gid={sheetId}'
    f = TemporaryFile(mode='w+', encoding=UTF8)
    if GC.Values[GC.DEBUG_LEVEL] > 0:
      sys.stderr.write(f'Debug: spreadsheetUrl: {spreadsheetUrl}\n')
    triesLimit = 3
    for n in range(1, triesLimit+1):
      _, content = drive._http.request(uri=spreadsheetUrl, method='GET')
# Check for HTML error message instead of data
      if content[0:15] != b'<!DOCTYPE html>':
        break
      tg = HTML_TITLE_PATTERN.match(content[0:600].decode('utf-8'))
      errMsg = tg.group(1) if tg else 'Unknown error'
      getGDocSheetDataRetryWarning([Ent.USER, user, Ent.SPREADSHEET, result['name'], sheetEntity['sheetType'], sheetEntity['sheetValue']], errMsg, n, triesLimit)
      time.sleep(20)
    else:
      getGDocSheetDataFailedExit([Ent.USER, user, Ent.SPREADSHEET, result['name'], sheetEntity['sheetType'], sheetEntity['sheetValue']], errMsg)
    f.write(content.decode(UTF8_SIG))
    f.seek(0)
    return f
  except GAPI.fileNotFound:
    getGDocSheetDataFailedExit([Ent.USER, user, Ent.SPREADSHEET, fileId], Msg.DOES_NOT_EXIST)
  except (GAPI.notFound, GAPI.forbidden, GAPI.permissionDenied,
          GAPI.internalError, GAPI.insufficientFilePermissions, GAPI.badRequest,
          GAPI.invalid, GAPI.invalidArgument, GAPI.failedPrecondition) as e:
    getGDocSheetDataFailedExit([Ent.USER, user, Ent.SPREADSHEET, fileId, sheetEntity['sheetType'], sheetEntity['sheetValue']], str(e))
  except (IOError, httplib2.HttpLib2Error) as e:
    if f:
      f.close()
    getGDocSheetDataFailedExit([Ent.USER, user, Ent.SPREADSHEET, fileId, sheetEntity['sheetType'], sheetEntity['sheetValue']], str(e))
  except (GAPI.serviceNotAvailable, GAPI.authError, GAPI.domainPolicy) as e:
    userDriveServiceNotEnabledWarning(user, str(e))
    sys.exit(GM.Globals[GM.SYSEXITRC])


BUCKET_OBJECT_PATTERNS = [
  {'pattern': re.compile(r'https://storage.(?:googleapis|cloud.google).com/(.+?)/(.+)'), 'unquote': True},
  {'pattern': re.compile(r'gs://(.+?)/(.+)'), 'unquote': False},
  {'pattern': re.compile(r'(.+?)/(.+)'), 'unquote': False},
  ]

def getBucketObjectName():
  uri = getString(Cmd.OB_STRING)
  for pattern in BUCKET_OBJECT_PATTERNS:
    mg = re.search(pattern['pattern'], uri)
    if mg:
      bucket = mg.group(1)
      s_object = mg.group(2) if not pattern['unquote'] else unquote(mg.group(2))
      return (bucket, s_object, f'{bucket}/{s_object}')
  systemErrorExit(ACTION_NOT_PERFORMED_RC, f'Invalid <StorageBucketObjectName>: {uri}')

GCS_FORMAT_MIME_TYPES = {
  'gcscsv': 'text/csv',
  'gcsdoc': 'text/plain',
  'gcshtml': 'text/html',
  }

# gcscsv|gcshtml|gcsdoc <StorageBucketObjectName>
def getStorageFileData(gcsformat, returnData=True):
  from util.api import buildGAPIObject, callGAPI
  mimeType = GCS_FORMAT_MIME_TYPES[gcsformat]
  bucket, s_object, bucketObject = getBucketObjectName()
  s = buildGAPIObject(API.STORAGEREAD)
  try:
    result = callGAPI(s.objects(), 'get',
                      throwReasons=[GAPI.NOT_FOUND, GAPI.FORBIDDEN],
                      bucket=bucket, object=s_object, projection='noAcl', fields='contentType')
  except GAPI.notFound:
    entityDoesNotExistExit(Ent.CLOUD_STORAGE_FILE, bucketObject)
  except GAPI.forbidden as e:
    entityActionFailedExit([Ent.CLOUD_STORAGE_FILE, bucketObject], str(e))
  if result['contentType'] != mimeType:
    getGDocSheetDataFailedExit([Ent.CLOUD_STORAGE_FILE, bucketObject],
                               Msg.INVALID_MIMETYPE.format(result['contentType'], mimeType))
  fb = TemporaryFile(mode='wb+')
  try:
    request = s.objects().get_media(bucket=bucket, object=s_object)
    downloader = googleapiclient.http.MediaIoBaseDownload(fb, request)
    done = False
    while not done:
      _, done = downloader.next_chunk()
    fb.seek(0)
    if returnData:
      data = fb.read().decode(UTF8)
      fb.close()
      return data
    f = TemporaryFile(mode='w+', encoding=UTF8)
    f.write(fb.read().decode(UTF8_SIG))
    fb.close()
    f.seek(0)
    return f
  except googleapiclient.http.HttpError as e:
    mg = HTTP_ERROR_PATTERN.match(str(e))
    getGDocSheetDataFailedExit([Ent.CLOUD_STORAGE_FILE, bucketObject], mg.group(1) if mg else str(e))

# <CSVFileInput>
def openCSVFileReader(filename, fieldnames=None):
  from gam.cmd.drive.transfer.fileops import HTTP_ERROR_PATTERN
  filenameLower = filename.lower()
  if filenameLower == 'gsheet':
    f = getGSheetData()
    getCharSet()
  elif filenameLower in {'gcsv', 'gdoc'}:
    f = getGDocData(filenameLower)
    getCharSet()
  elif filenameLower in {'gcscsv', 'gcsdoc'}:
    f = getStorageFileData(filenameLower, False)
    getCharSet()
  else:
    encoding = getCharSet()
    filename = setFilePath(filename, GC.INPUT_DIR)
    f = openFile(filename, mode=DEFAULT_CSV_READ_MODE, encoding=encoding)
  if checkArgumentPresent('warnifnodata'):
    loc = f.tell()
    try:
      if not f.readline() or not f.readline():
        stderrWarningMsg(fileErrorMessage(filename, Msg.NO_CSV_FILE_DATA_FOUND))
        sys.exit(NO_ENTITIES_FOUND_RC)
      f.seek(loc)
    except (IOError, UnicodeDecodeError, UnicodeError) as e:
      systemErrorExit(FILE_ERROR_RC, fileErrorMessage(filename, e))
  if checkArgumentPresent('columndelimiter'):
    columnDelimiter = getCharacter()
  else:
    columnDelimiter = GC.Values[GC.CSV_INPUT_COLUMN_DELIMITER]
  if checkArgumentPresent('noescapechar'):
    noEscapeChar = getBoolean()
  else:
    noEscapeChar = GC.Values[GC.CSV_INPUT_NO_ESCAPE_CHAR]
  if checkArgumentPresent('quotechar'):
    quotechar = getCharacter()
  else:
    quotechar = GC.Values[GC.CSV_INPUT_QUOTE_CHAR]
  if not checkArgumentPresent('endcsv') and checkArgumentPresent('fields'):
    fieldnames = shlexSplitList(getString(Cmd.OB_FIELD_NAME_LIST))
  try:
    csvFile = csv.DictReader(f, fieldnames=fieldnames,
                             delimiter=columnDelimiter,
                             escapechar='\\' if not noEscapeChar else None,
                             quotechar=quotechar)
    return (f, csvFile, csvFile.fieldnames if csvFile.fieldnames is not None else [])
  except (csv.Error, UnicodeDecodeError, UnicodeError) as e:
    systemErrorExit(FILE_ERROR_RC, e)
