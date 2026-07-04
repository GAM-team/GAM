"""User photo and profile management.

Part of the _userop_tmp sub-package."""

"""GAM user operations: Looker Studio, user groups, licenses, photos, profile, sheets, tokens, deprovision."""

import re

import googleapiclient.http
import base64
import os

import google.auth
import google.auth.exceptions

from gamlib import api as API
from gamlib import settings as GC
from gamlib import gapi as GAPI
from gamlib import state as GM
from gamlib import msgs as Msg
from gam.util.access import entityUnknownWarning
from gam.util.api import buildGAPIObject, buildGAPIServiceObject, callGAPI, getHttpObj
from gam.util.args import (
    UTF8,
    checkForExtraneousArguments,
    getArgument,
    getChoice,
    getEmailAddress,
    getInteger,
    getString,
    normalizeEmailAddressOrUID,
)
from gam.util.display import (
    entityActionFailedWarning,
    entityActionPerformed,
    entityItemValueListActionNotPerformedWarning,
    entityPerformActionNumItems,
    printEntity,
)
from gam.util.entity import getEntityArgument, splitEmailAddressOrUID
from gam.util.errors import entityDoesNotExistExit, unknownArgumentExit
from gam.util.fileio import UNKNOWN, setFilePath, writeFileReturnError
from gam.util.output import writeStdout
from gam.util.tags import _substituteForUser
from gam.cmd.drive.core import _validateUserGetFileIDs, getDriveFileEntity

from gam.var import Act, Cmd, Ent, Ind

from tempfile import TemporaryFile

def updatePhoto(users):
  cd = buildGAPIObject(API.DIRECTORY)
  baseFileIdEntity = drive = owner = None
  sourceFolder = os.getcwd()
  if Cmd.NumArgumentsRemaining() == 1:
    filenamePattern = getString(Cmd.OB_FILE_NAME_PATTERN)
  else:
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
      elif myarg == 'gphoto':
        owner, drive = buildGAPIServiceObject(API.DRIVE3, getEmailAddress())
        if not drive:
          return
        baseFileIdEntity = getDriveFileEntity(queryShortcutsOK=False)
      else:
        unknownArgumentExit()
  p = re.compile('^(ht|f)tps?://.*$')
  i, count, users = getEntityArgument(users)
  for user in users:
    i += 1
    user, userName, _ = splitEmailAddressOrUID(user)
    filename = _substituteForUser(filenamePattern, user, userName)
    if baseFileIdEntity is not None:
      fileIdEntity = baseFileIdEntity.copy()
      if fileIdEntity['query'] is not None:
        fileIdEntity['query'] = _substituteForUser(fileIdEntity['query'], user, userName)
      _, _, jcount = _validateUserGetFileIDs(owner, 0, 0, fileIdEntity, drive=drive, entityType=None)
      if jcount == 0:
        entityItemValueListActionNotPerformedWarning([Ent.USER, user], [Ent.OWNER, owner],
                                                     Msg.NO_ENTITIES_FOUND.format(Ent.Singular(Ent.DRIVE_FILE)), i, count)
        continue
      if jcount > 1:
        entityItemValueListActionNotPerformedWarning([Ent.USER, user], [Ent.OWNER, owner],
                                                     Msg.MULTIPLE_ENTITIES_FOUND.format(Ent.Plural(Ent.DRIVE_FILE), jcount, ','.join(fileIdEntity['list'])), i, count)
        continue
      fb = TemporaryFile(mode='wb+')
      filename = fileIdEntity['list'][0]
      request = drive.files().get_media(fileId=filename)
      downloader = googleapiclient.http.MediaIoBaseDownload(fb, request)
      done = False
      while not done:
        _, done = downloader.next_chunk()
      fb.seek(0)
      image_data = fb.read()
      fb.close()
    elif p.match(filename):
      try:
        status, image_data = getHttpObj().request(filename, 'GET')
        if status['status'] != '200':
          entityActionFailedWarning([Ent.USER, user, Ent.PHOTO, filename], Msg.NOT_ALLOWED, i, count)
          continue
      except (httplib2.HttpLib2Error, google.auth.exceptions.TransportError, RuntimeError) as e:
        entityActionFailedWarning([Ent.USER, user, Ent.PHOTO, filename], str(e), i, count)
        continue
    else:
      filename = os.path.join(sourceFolder, filename)
      try:
        with open(filename, 'rb') as f:
          image_data = f.read()
      except (OSError, IOError) as e:
        entityActionFailedWarning([Ent.USER, user, Ent.PHOTO, filename], str(e), i, count)
        continue
    body = {'photoData': base64.urlsafe_b64encode(image_data).decode(UTF8)}
    try:
      try:
        callGAPI(cd.users().photos(), 'delete',
                 bailOnInternalError=True,
                 throwReasons=[GAPI.USER_NOT_FOUND, GAPI.FORBIDDEN, GAPI.PHOTO_NOT_FOUND, GAPI.INTERNAL_ERROR],
                 userKey=user)
      except (GAPI.photoNotFound, GAPI.internalError):
        pass
      callGAPI(cd.users().photos(), 'update',
               throwReasons=[GAPI.USER_NOT_FOUND, GAPI.FORBIDDEN, GAPI.INVALID_INPUT, GAPI.CONDITION_NOT_MET],
               userKey=user, body=body, fields='')
      entityActionPerformed([Ent.USER, user, Ent.PHOTO, filename], i, count)
    except (GAPI.invalidInput, GAPI.conditionNotMet) as e:
      entityActionFailedWarning([Ent.USER, user, Ent.PHOTO, filename], str(e), i, count)
    except (GAPI.userNotFound, GAPI.forbidden):
      entityUnknownWarning(Ent.USER, user, i, count)

# gam <UserTypeEntity> delete photo
def deletePhoto(users):
  cd = buildGAPIObject(API.DIRECTORY)
  checkForExtraneousArguments()
  i, count, users = getEntityArgument(users)
  for user in users:
    i += 1
    user = normalizeEmailAddressOrUID(user)
    try:
      callGAPI(cd.users().photos(), 'delete',
               bailOnInternalError=True,
               throwReasons=[GAPI.USER_NOT_FOUND, GAPI.FORBIDDEN, GAPI.PHOTO_NOT_FOUND, GAPI.INTERNAL_ERROR],
               userKey=user)
      entityActionPerformed([Ent.USER, user, Ent.PHOTO, ''], i, count)
    except (GAPI.photoNotFound, GAPI.internalError) as e:
      entityActionFailedWarning([Ent.USER, user, Ent.PHOTO, ''], str(e), i, count)
    except (GAPI.userNotFound, GAPI.forbidden):
      entityUnknownWarning(Ent.USER, user, i, count)

def getPhoto(users, profileMode):
  cd = buildGAPIObject(API.DIRECTORY)
  targetFolder = os.getcwd()
  filenamePattern = '#email#.#ext#'
  noDefault = returnURLonly = False
  writeFileData = showPhotoData = True
  size = ''
  while Cmd.ArgumentsRemaining():
    myarg = getArgument()
    if myarg == 'drivedir':
      targetFolder = GC.Values[GC.DRIVE_DIR]
    elif myarg == 'targetfolder':
      targetFolder = setFilePath(getString(Cmd.OB_FILE_PATH), GC.DRIVE_DIR)
      if not os.path.isdir(targetFolder):
        os.makedirs(targetFolder)
    elif myarg == 'filename':
      filenamePattern = getString(Cmd.OB_FILE_NAME_PATTERN)
    elif myarg == 'nofile':
      writeFileData = False
    elif myarg == 'noshow':
      showPhotoData = False
    elif profileMode and myarg == 'returnurlonly':
      returnURLonly = True
    elif myarg == 'nodefault':
      noDefault = True
    elif profileMode and myarg == 'size':
      size = getInteger(minVal=50)
    else:
      unknownArgumentExit()
  i, count, users = getEntityArgument(users)
  for user in users:
    i += 1
    if profileMode:
      user, people = buildGAPIServiceObject(API.PEOPLE, user, i, count)
      if not people:
        continue
    else:
      user = normalizeEmailAddressOrUID(user)
    _, userName, _ = splitEmailAddressOrUID(user)
    filename = os.path.join(targetFolder, _substituteForUser(filenamePattern, user, userName))
    try:
      if not showPhotoData:
        entityPerformActionNumItems([Ent.USER, user], 1, Ent.PHOTO, i, count)
      if not profileMode:
        photo = callGAPI(cd.users().photos(), 'get',
                         throwReasons=[GAPI.USER_NOT_FOUND, GAPI.FORBIDDEN, GAPI.PHOTO_NOT_FOUND],
                         userKey=user)
        if showPhotoData:
          writeStdout(photo['photoData']+'\n')
        photo_data = base64.urlsafe_b64decode(photo['photoData'])
      else:
        result = callGAPI(people.people(), 'get',
                          throwReasons=[GAPI.NOT_FOUND],
                          retryReasons=GAPI.SERVICE_NOT_AVAILABLE_RETRY_REASONS,
                          resourceName='people/me', personFields='photos')
        default = False
        url = None
        for photo in result.get('photos', []):
          if photo['metadata']['source']['type'] == 'PROFILE':
            default = photo.get('default', False)
            url = photo['url']
            break
        if not url:
          entityActionFailedWarning([Ent.USER, user, Ent.PHOTO, None], Msg.PROFILE_PHOTO_NOT_FOUND, i, count)
          continue
        if noDefault and default:
          entityActionFailedWarning([Ent.USER, user, Ent.PHOTO, None], Msg.PROFILE_PHOTO_IS_DEFAULT, i, count)
          continue
        if returnURLonly:
          writeStdout(f'{url}\n')
          continue
        if size:
          url = re.sub(r"=s\d+$", f"=s{size}", url)
        try:
          status, photo_data = getHttpObj().request(url, 'GET')
          if status['status'] != '200':
            entityActionFailedWarning([Ent.USER, user, Ent.PHOTO, filename], Msg.NOT_ALLOWED, i, count)
            continue
          if showPhotoData:
            writeStdout(base64.encodebytes(photo_data).decode(UTF8))
        except (httplib2.HttpLib2Error, google.auth.exceptions.TransportError, RuntimeError) as e:
          entityActionFailedWarning([Ent.USER, user, Ent.PHOTO, filename], str(e), i, count)
          continue
      if writeFileData:
        if photo_data[:3] == b'\xff\xd8\xff':
          extension = 'jpg'
        elif photo_data[:8] == b'\x89\x50\x4e\x47\x0d\x0a\x1a\x0a':
          extension = 'png'
        elif photo_data[:6] == b'\x47\x49\x46\x38\x37\x61' or photo_data[:6] == b'\x47\x49\x46\x38\x39\x61':
          extension = 'gif'
        elif photo_data[:2] == b'\x42\x4d':
          extension= 'bmp'
        elif photo_data[:4] == b'\x49\x49\x2A\x00' or photo_data[:4] == b'\x4D\x4D\x00\x2A':
          extension= 'tif'
        else:
          extension = 'img'
        filenameExt = filename.replace('#ext#', extension)
        status, e = writeFileReturnError(filenameExt, photo_data, mode='wb')
        if status:
          if not showPhotoData:
            entityActionPerformed([Ent.USER, user, Ent.PHOTO, filenameExt], i, count)
        else:
          entityActionFailedWarning([Ent.USER, user, Ent.PHOTO, filenameExt], str(e), i, count)
    except (GAPI.notFound, GAPI.photoNotFound) as e:
      entityActionFailedWarning([Ent.USER, user, Ent.PHOTO, None], str(e), i, count)
    except (GAPI.userNotFound, GAPI.forbidden):
      entityUnknownWarning(Ent.USER, user, i, count)

# gam <UserTypeEntity> get photo [drivedir|(targetfolder <FilePath>)] [filename <FileNamePattern>]]
#	[noshow] [nofile]
def getUserPhoto(users):
  getPhoto(users, False)

# gam <UserTypeEntity> get profilephoto [drivedir|(targetfolder <FilePath>)] [filename <FileNamePattern>]
#	[noshow] [nofile] [returnurlonly] [nodefault] [size <Integer>]
def getProfilePhoto(users):
  getPhoto(users, True)

PROFILE_SHARING_CHOICE_MAP = {
  'share': True,
  'shared': True,
  'unshare': False,
  'unshared': False,
  }

def _setShowProfile(users, function, **kwargs):
  cd = buildGAPIObject(API.DIRECTORY)
  checkForExtraneousArguments()
  i, count, users = getEntityArgument(users)
  for user in users:
    i += 1
    user = normalizeEmailAddressOrUID(user)
    try:
      result = callGAPI(cd.users(), function,
                        throwReasons=[GAPI.USER_NOT_FOUND, GAPI.FORBIDDEN],
                        userKey=user, fields='includeInGlobalAddressList', **kwargs)
      printEntity([Ent.USER, user, Ent.PROFILE_SHARING_ENABLED, result.get('includeInGlobalAddressList', UNKNOWN)], i, count)
    except (GAPI.userNotFound, GAPI.forbidden):
      entityUnknownWarning(Ent.USER, user, i, count)

# gam <UserTypeEntity> profile share|shared|unshare|unshared
def setProfile(users):
  body = {'includeInGlobalAddressList': getChoice(PROFILE_SHARING_CHOICE_MAP, mapChoice=True)}
  _setShowProfile(users, 'update', body=body)

# gam <UserTypeEntity> show profile
def showProfile(users):
  _setShowProfile(users, 'get')

# gam <UserTypeEntity> create sheet
#	((json [charset <Charset>] <SpreadsheetJSONCreateRequest>) |
#	 (json file <FileName> [charset <Charset>]))
#	[<DriveFileParentAttribute>]
#	[formatjson] [returnidonly]
