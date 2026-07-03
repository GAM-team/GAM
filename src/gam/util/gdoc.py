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


_gam = lambda: sys.modules['gam']


GDOC_FORMAT_MIME_TYPES = {
  'gcsv': 'text/csv',
  'gdoc': 'text/plain',
  'ghtml': 'text/html',
  }

# gdoc <EmailAddress> <DriveFileIDEntity>|<DriveFileNameEntity>
def getGDocData(gformat):
  mimeType = GDOC_FORMAT_MIME_TYPES[gformat]
  user = _gam().getEmailAddress()
  fileIdEntity = _gam().getDriveFileEntity(queryShortcutsOK=False)
  if not GC.Values[GC.COMMANDDATA_CLIENTACCESS]:
    _, drive = _gam().buildGAPIServiceObject(API.DRIVE3, user)
  else:
    drive = _gam().buildGAPIObject(API.DRIVE3)
  if not drive:
    sys.exit(GM.Globals[GM.SYSEXITRC])
  _, _, jcount = _gam()._validateUserGetFileIDs(user, 0, 0, fileIdEntity, drive=drive)
  if jcount == 0:
    _gam().getGDocSheetDataFailedExit([Ent.USER, user], Msg.NO_ENTITIES_FOUND.format(Ent.Singular(Ent.DRIVE_FILE)))
  if jcount > 1:
    _gam().getGDocSheetDataFailedExit([Ent.USER, user], Msg.MULTIPLE_ENTITIES_FOUND.format(Ent.Plural(Ent.DRIVE_FILE), jcount, ','.join(fileIdEntity['list'])))
  fileId = fileIdEntity['list'][0]
  f = None
  try:
    result = _gam().callGAPI(drive.files(), 'get',
                      throwReasons=GAPI.DRIVE_GET_THROW_REASONS,
                      fileId=fileId, fields='name,mimeType,exportLinks',
                      supportsAllDrives=True)
# Google Doc
    if 'exportLinks' in result:
      if mimeType not in result['exportLinks']:
        _gam().getGDocSheetDataFailedExit([Ent.USER, user, Ent.DRIVE_FILE, result['name']],
                                   Msg.INVALID_MIMETYPE.format(result['mimeType'], mimeType))
      f = TemporaryFile(mode='w+', encoding=_gam().UTF8)
      _, content = drive._http.request(uri=result['exportLinks'][mimeType], method='GET')
      f.write(content.decode(_gam().UTF8_SIG))
      f.seek(0)
      return f
# Drive File
    if result['mimeType'] != mimeType:
      _gam().getGDocSheetDataFailedExit([Ent.USER, user, Ent.DRIVE_FILE, result['name']],
                                 Msg.INVALID_MIMETYPE.format(result['mimeType'], mimeType))
    fb = TemporaryFile(mode='wb+')
    request = drive.files().get_media(fileId=fileId)
    downloader = googleapiclient.http.MediaIoBaseDownload(fb, request)
    done = False
    while not done:
      _, done = downloader.next_chunk()
    f = TemporaryFile(mode='w+', encoding=_gam().UTF8)
    fb.seek(0)
    f.write(fb.read().decode(_gam().UTF8_SIG))
    fb.close()
    f.seek(0)
    return f
  except GAPI.fileNotFound:
    _gam().getGDocSheetDataFailedExit([Ent.USER, user, Ent.DOCUMENT, fileId], Msg.DOES_NOT_EXIST)
  except (IOError, httplib2.HttpLib2Error, google.auth.exceptions.TransportError, RuntimeError) as e:
    if f:
      f.close()
    _gam().getGDocSheetDataFailedExit([Ent.USER, user, Ent.DOCUMENT, fileId], str(e))
  except (GAPI.serviceNotAvailable, GAPI.authError, GAPI.domainPolicy) as e:
    _gam().userDriveServiceNotEnabledWarning(user, str(e))
    sys.exit(GM.Globals[GM.SYSEXITRC])

HTML_TITLE_PATTERN = re.compile(r'.*<title>(.+)</title>')

# gsheet <EmailAddress> <DriveFileIDEntity>|<DriveFileNameEntity> <SheetEntity>
def getGSheetData():
  user = _gam().getEmailAddress()
  fileIdEntity = _gam().getDriveFileEntity(queryShortcutsOK=False)
  sheetEntity = _gam().getSheetEntity(False)
  if not GC.Values[GC.COMMANDDATA_CLIENTACCESS]:
    user, drive = _gam().buildGAPIServiceObject(API.DRIVE3, user)
  else:
    drive = _gam().buildGAPIObject(API.DRIVE3)
  if not drive:
    sys.exit(GM.Globals[GM.SYSEXITRC])
  _, _, jcount = _gam()._validateUserGetFileIDs(user, 0, 0, fileIdEntity, drive=drive)
  if jcount == 0:
    _gam().getGDocSheetDataFailedExit([Ent.USER, user], Msg.NO_ENTITIES_FOUND.format(Ent.Singular(Ent.DRIVE_FILE)))
  if jcount > 1:
    _gam().getGDocSheetDataFailedExit([Ent.USER, user], Msg.MULTIPLE_ENTITIES_FOUND.format(Ent.Plural(Ent.DRIVE_FILE), jcount, ','.join(fileIdEntity['list'])))
  if not GC.Values[GC.COMMANDDATA_CLIENTACCESS]:
    _, sheet = _gam().buildGAPIServiceObject(API.SHEETS, user)
  else:
    sheet = _gam().buildGAPIObject(API.SHEETS)
  if not sheet:
    sys.exit(GM.Globals[GM.SYSEXITRC])
  fileId = fileIdEntity['list'][0]
  f = None
  try:
    result = _gam().callGAPI(drive.files(), 'get',
                      throwReasons=GAPI.DRIVE_GET_THROW_REASONS,
                      fileId=fileId, fields='name,mimeType', supportsAllDrives=True)
    if result['mimeType'] != _gam().MIMETYPE_GA_SPREADSHEET:
      _gam().getGDocSheetDataFailedExit([Ent.USER, user, Ent.DRIVE_FILE, result['name']],
                                 Msg.INVALID_MIMETYPE.format(result['mimeType'], _gam().MIMETYPE_GA_SPREADSHEET))
    spreadsheet = _gam().callGAPI(sheet.spreadsheets(), 'get',
                           throwReasons=GAPI.SHEETS_ACCESS_THROW_REASONS,
                           spreadsheetId=fileId, fields='spreadsheetUrl,sheets(properties(sheetId,title))')
    sheetId = _gam().getSheetIdFromSheetEntity(spreadsheet, sheetEntity)
    if sheetId is None:
      _gam().getGDocSheetDataFailedExit([Ent.USER, user, Ent.SPREADSHEET, result['name'], sheetEntity['sheetType'], sheetEntity['sheetValue']], Msg.NOT_FOUND)
    spreadsheetUrl = f'{re.sub("/edit.*$", "/export", spreadsheet["spreadsheetUrl"])}?format=csv&id={fileId}&gid={sheetId}'
    f = TemporaryFile(mode='w+', encoding=_gam().UTF8)
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
      _gam().getGDocSheetDataRetryWarning([Ent.USER, user, Ent.SPREADSHEET, result['name'], sheetEntity['sheetType'], sheetEntity['sheetValue']], errMsg, n, triesLimit)
      time.sleep(20)
    else:
      _gam().getGDocSheetDataFailedExit([Ent.USER, user, Ent.SPREADSHEET, result['name'], sheetEntity['sheetType'], sheetEntity['sheetValue']], errMsg)
    f.write(content.decode(_gam().UTF8_SIG))
    f.seek(0)
    return f
  except GAPI.fileNotFound:
    _gam().getGDocSheetDataFailedExit([Ent.USER, user, Ent.SPREADSHEET, fileId], Msg.DOES_NOT_EXIST)
  except (GAPI.notFound, GAPI.forbidden, GAPI.permissionDenied,
          GAPI.internalError, GAPI.insufficientFilePermissions, GAPI.badRequest,
          GAPI.invalid, GAPI.invalidArgument, GAPI.failedPrecondition) as e:
    _gam().getGDocSheetDataFailedExit([Ent.USER, user, Ent.SPREADSHEET, fileId, sheetEntity['sheetType'], sheetEntity['sheetValue']], str(e))
  except (IOError, httplib2.HttpLib2Error) as e:
    if f:
      f.close()
    _gam().getGDocSheetDataFailedExit([Ent.USER, user, Ent.SPREADSHEET, fileId, sheetEntity['sheetType'], sheetEntity['sheetValue']], str(e))
  except (GAPI.serviceNotAvailable, GAPI.authError, GAPI.domainPolicy) as e:
    _gam().userDriveServiceNotEnabledWarning(user, str(e))
    sys.exit(GM.Globals[GM.SYSEXITRC])


BUCKET_OBJECT_PATTERNS = [
  {'pattern': re.compile(r'https://storage.(?:googleapis|cloud.google).com/(.+?)/(.+)'), 'unquote': True},
  {'pattern': re.compile(r'gs://(.+?)/(.+)'), 'unquote': False},
  {'pattern': re.compile(r'(.+?)/(.+)'), 'unquote': False},
  ]

def getBucketObjectName():
  Cmd = _gam().Cmd
  uri = _gam().getString(Cmd.OB_STRING)
  for pattern in BUCKET_OBJECT_PATTERNS:
    mg = re.search(pattern['pattern'], uri)
    if mg:
      bucket = mg.group(1)
      s_object = mg.group(2) if not pattern['unquote'] else unquote(mg.group(2))
      return (bucket, s_object, f'{bucket}/{s_object}')
  _gam().systemErrorExit(_gam().ACTION_NOT_PERFORMED_RC, f'Invalid <StorageBucketObjectName>: {uri}')

GCS_FORMAT_MIME_TYPES = {
  'gcscsv': 'text/csv',
  'gcsdoc': 'text/plain',
  'gcshtml': 'text/html',
  }

# gcscsv|gcshtml|gcsdoc <StorageBucketObjectName>
def getStorageFileData(gcsformat, returnData=True):
  mimeType = GCS_FORMAT_MIME_TYPES[gcsformat]
  bucket, s_object, bucketObject = getBucketObjectName()
  s = _gam().buildGAPIObject(API.STORAGEREAD)
  try:
    result = _gam().callGAPI(s.objects(), 'get',
                      throwReasons=[GAPI.NOT_FOUND, GAPI.FORBIDDEN],
                      bucket=bucket, object=s_object, projection='noAcl', fields='contentType')
  except GAPI.notFound:
    _gam().entityDoesNotExistExit(Ent.CLOUD_STORAGE_FILE, bucketObject)
  except GAPI.forbidden as e:
    _gam().entityActionFailedExit([Ent.CLOUD_STORAGE_FILE, bucketObject], str(e))
  if result['contentType'] != mimeType:
    _gam().getGDocSheetDataFailedExit([Ent.CLOUD_STORAGE_FILE, bucketObject],
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
      data = fb.read().decode(_gam().UTF8)
      fb.close()
      return data
    f = TemporaryFile(mode='w+', encoding=_gam().UTF8)
    f.write(fb.read().decode(_gam().UTF8_SIG))
    fb.close()
    f.seek(0)
    return f
  except googleapiclient.http.HttpError as e:
    mg = _gam().HTTP_ERROR_PATTERN.match(str(e))
    _gam().getGDocSheetDataFailedExit([Ent.CLOUD_STORAGE_FILE, bucketObject], mg.group(1) if mg else str(e))

# <CSVFileInput>
def openCSVFileReader(filename, fieldnames=None):
  Cmd = _gam().Cmd
  filenameLower = filename.lower()
  if filenameLower == 'gsheet':
    f = getGSheetData()
    _gam().getCharSet()
  elif filenameLower in {'gcsv', 'gdoc'}:
    f = getGDocData(filenameLower)
    _gam().getCharSet()
  elif filenameLower in {'gcscsv', 'gcsdoc'}:
    f = getStorageFileData(filenameLower, False)
    _gam().getCharSet()
  else:
    encoding = _gam().getCharSet()
    filename = _gam().setFilePath(filename, GC.INPUT_DIR)
    f = _gam().openFile(filename, mode=_gam().DEFAULT_CSV_READ_MODE, encoding=encoding)
  if _gam().checkArgumentPresent('warnifnodata'):
    loc = f.tell()
    try:
      if not f.readline() or not f.readline():
        _gam().stderrWarningMsg(_gam().fileErrorMessage(filename, Msg.NO_CSV_FILE_DATA_FOUND))
        sys.exit(_gam().NO_ENTITIES_FOUND_RC)
      f.seek(loc)
    except (IOError, UnicodeDecodeError, UnicodeError) as e:
      _gam().systemErrorExit(_gam().FILE_ERROR_RC, _gam().fileErrorMessage(filename, e))
  if _gam().checkArgumentPresent('columndelimiter'):
    columnDelimiter = _gam().getCharacter()
  else:
    columnDelimiter = GC.Values[GC.CSV_INPUT_COLUMN_DELIMITER]
  if _gam().checkArgumentPresent('noescapechar'):
    noEscapeChar = _gam().getBoolean()
  else:
    noEscapeChar = GC.Values[GC.CSV_INPUT_NO_ESCAPE_CHAR]
  if _gam().checkArgumentPresent('quotechar'):
    quotechar = _gam().getCharacter()
  else:
    quotechar = GC.Values[GC.CSV_INPUT_QUOTE_CHAR]
  if not _gam().checkArgumentPresent('endcsv') and _gam().checkArgumentPresent('fields'):
    fieldnames = _gam().shlexSplitList(_gam().getString(Cmd.OB_FIELD_NAME_LIST))
  try:
    csvFile = csv.DictReader(f, fieldnames=fieldnames,
                             delimiter=columnDelimiter,
                             escapechar='\\' if not noEscapeChar else None,
                             quotechar=quotechar)
    return (f, csvFile, csvFile.fieldnames if csvFile.fieldnames is not None else [])
  except (csv.Error, UnicodeDecodeError, UnicodeError) as e:
    _gam().systemErrorExit(_gam().FILE_ERROR_RC, e)
