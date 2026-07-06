"""GAM cloud storage management."""

import re

import googleapiclient.http
import hashlib
import base64
import os
import time

from gamlib import api as API
from gamlib import settings as GC
from gamlib import gapi as GAPI
from gamlib import msgs as Msg
from gam.var import Act, Cmd, Ent, Ind
from gam.util.api import buildGAPIObject
from gam.util.api_call import callGAPIpages, checkGAPIError
from gam.util.args import getArgument, getBoolean, getString
from gam.util.display import (
    ACTION_NOT_PERFORMED_RC,
    entityActionFailedWarning,
    entityActionPerformed,
    entityActionPerformedMessage,
    entityModifierNewValueActionFailedWarning,
    entityModifierNewValueActionPerformed,
    entityPerformAction,
    getPageMessage,
    printEntityMessage,
    printGettingAllAccountEntities,
    printGettingEntityItem,
)
from gam.util.errors import entityActionFailedExit, entityDoesNotExistExit, missingArgumentExit, unknownArgumentExit
from gam.util.fileio import (
    FILE_ERROR_RC,
    cleanFilepath,
    closeFile,
    fileErrorMessage,
    openFile,
    setFilePath,
    uniqueFilename,
)
from gam.util.gdoc import getBucketObjectName
from gam.util.output import (
    flushStderr,
    formatKeyValueList,
    systemErrorExit,
    writeStderr,
    writeStdout,
)
from gam.constants import GOOGLE_API_ERROR_RC
from gam.cmd.drive.transfer.fileops import HTTP_ERROR_PATTERN
from gam.util.api import ClientAPIAccessDeniedExit


def _copyStorageObjects(objects, target_bucket, target_prefix):
  """Copies objects to target_bucket.

  Args:
    objects: list of object dicts
      [
        {
          bucket: source bucket,
          name: source object name,
          (optional) md5Hash: source file hash value
        },
        ...
      ]
    target_bucket: target bucket id
    target_prefix: prefix name to prepend to target object

  """

  def process_rewrite(request_id, response, exception):
    fileIndex = int(request_id)
    if exception:
      http_status, reason, message = checkGAPIError(exception)
      # Poor man's backoff/retry
      if http_status == 429 or http_status > 499:
        writeStderr(f'Temporary error: {http_status} - {message}, Backing off: 10 seconds\n')
        flushStderr()
        time.sleep(10)
        next_batch.add(s.objects().rewrite(**files_to_copy[fileIndex]['method']), request_id=request_id)
        return
      if reason in GAPI.REASON_EXCEPTION_MAP:
        raise GAPI.REASON_EXCEPTION_MAP[reason](message)
      raise exception(message)
    source_displayname = files_to_copy[fileIndex]['source_displayname']
    target_displayname = files_to_copy[fileIndex]['target_displayname']
    if response.get('done'):
      source_md5 = files_to_copy[fileIndex]['md5Hash']
      target_md5 = response['resource']['md5Hash']
      if source_md5 != target_md5:
        systemErrorExit(GOOGLE_API_ERROR_RC, f'Target file {target_displayname} checksum {target_md5} does not match source {source_md5}. This should not happen')
      entityActionPerformedMessage([Ent.CLOUD_STORAGE_FILE, None], f'{1:>7.2%} Complete', fileIndex+1, totalFiles)
      Ind.Increment()
      writeStdout(formatKeyValueList(Ind.Spaces(), ['Source', source_displayname], '\n'))
      writeStdout(formatKeyValueList(Ind.Spaces(), ['Target', target_displayname], '\n'))
      Ind.Decrement()
    else:
      total_bytes = float(response.get('objectSize'))
      done_bytes = float(response.get('totalBytesRewritten'))
      entityActionPerformedMessage([Ent.CLOUD_STORAGE_FILE, None], f'{(done_bytes / total_bytes):>7.2%} Complete', fileIndex+1, totalFiles)
      Ind.Increment()
      writeStdout(formatKeyValueList(Ind.Spaces(), ['Source', source_displayname], '\n'))
      writeStdout(formatKeyValueList(Ind.Spaces(), ['Target', target_displayname], '\n'))
      Ind.Decrement()
      files_to_copy[fileIndex]['method']['rewriteToken'] = response.get('rewriteToken')
      next_batch.add(s.objects().rewrite(**files_to_copy[fileIndex]['method']), request_id=request_id)

  action = Act.Get()
  Act.Set(Act.COPY)
  s = buildGAPIObject(API.STORAGEWRITE)
  sbatch = s.new_batch_http_request(callback=process_rewrite)
  files_to_copy = []
  for object_ in objects:
    files_to_copy.append(
      {
        'md5Hash': object_['md5Hash'],
        'source_displayname': f'{object_["bucket"]}:{object_["name"]}',
        'target_displayname': f'{target_bucket}:{target_prefix}{object_["name"]}',
        'method': {
          'destinationBucket': target_bucket,
          'destinationObject': f'{target_prefix}{object_["name"]}',
          'sourceBucket': object_['bucket'],
          'sourceObject': object_['name'],
          'maxBytesRewrittenPerCall': 1048576, # uncomment to easily test multiple rewrite API calls per object
        },
      })
  totalFiles = len(files_to_copy)
  i = 0
  try:
    for file in files_to_copy:
      while len(sbatch._order) == 100:
        next_batch = s.new_batch_http_request(callback=process_rewrite)
        sbatch.execute()
        sbatch = next_batch
      sbatch.add(s.objects().rewrite(**file['method']), request_id=str(i))
      i += 1
    while len(sbatch._order) > 0:
      next_batch = s.new_batch_http_request(callback=process_rewrite)
      sbatch.execute()
      sbatch = next_batch
  except GAPI.notFound:
    Act.Set(action)
    entityDoesNotExistExit(Ent.CLOUD_STORAGE_BUCKET, target_bucket)
  except Exception:
    ClientAPIAccessDeniedExit()
  Act.Set(action)

def md5MatchesFile(filename, expected_md5, j=0, jcount=0):
  action = Act.Get()
  Act.Set(Act.VERIFY)
  try:
    f = openFile(filename, 'rb')
    hash_md5 = hashlib.md5()
    for chunk in iter(lambda: f.read(4096), b""):
      hash_md5.update(chunk)
    closeFile(f)
    actual_hash = hash_md5.hexdigest()
    if actual_hash == expected_md5:
      entityActionPerformed([Ent.FILE, filename, Ent.MD5HASH, expected_md5], j, jcount)
      Act.Set(action)
      return True
    entityActionFailedWarning([Ent.FILE, filename, Ent.MD5HASH, expected_md5], Msg.DOES_NOT_MATCH.format(actual_hash), j, jcount)
    Act.Set(action)
    return False
  except OSError as e:
    systemErrorExit(FILE_ERROR_RC, fileErrorMessage(filename, e))

def _getCloudStorageObject(s, bucket, s_object, localFilename, expectedMd5=None, zipToStdout=False, j=0, jcount=0):
  if not zipToStdout:
    localFilename = cleanFilepath(localFilename)
    entityValueList = [Ent.DRIVE_FILE, localFilename]
    if os.path.exists(localFilename):
      printEntityMessage(entityValueList, Msg.EXISTS)
      if not expectedMd5:
        return # nothing to verify, just assume we're good.
      if md5MatchesFile(localFilename, expectedMd5):
        return
      printEntityMessage(entityValueList, Msg.DOWNLOADING_AGAIN_AND_OVER_WRITING)
    entityPerformAction(entityValueList)
    file_path = os.path.dirname(localFilename)
    if not os.path.exists(file_path):
      os.makedirs(file_path)
    f = openFile(localFilename, 'wb')
  else:
    f = openFile('-', 'wb')
  try:
    request = s.objects().get_media(bucket=bucket, object=s_object)
    downloader = googleapiclient.http.MediaIoBaseDownload(f, request)
    done = False
    while not done:
      status, done = downloader.next_chunk()
      if not zipToStdout and status.progress() < 1.0:
        entityActionPerformedMessage([Ent.CLOUD_STORAGE_FILE, s_object], f'{status.progress():>7.2%}', j, jcount)
    if not zipToStdout:
      entityModifierNewValueActionPerformed([Ent.CLOUD_STORAGE_FILE, s_object], Act.MODIFIER_TO, localFilename, j, jcount)
      closeFile(f, True)
    if expectedMd5 and not md5MatchesFile(localFilename, expectedMd5):
      systemErrorExit(FILE_ERROR_RC, fileErrorMessage(localFilename, Msg.CORRUPT_FILE))
  except googleapiclient.http.HttpError as e:
    mg = HTTP_ERROR_PATTERN.match(str(e))
    entityModifierNewValueActionFailedWarning([Ent.CLOUD_STORAGE_FILE, s_object], Act.MODIFIER_TO, localFilename, mg.group(1) if mg else str(e), j, jcount)

TAKEOUT_EXPORT_PATTERN = re.compile(r'(takeout-export-[a-f,0-9,-]*)')

# gam copy storagebucket sourcebucket <StorageBucketName> targetbucket <StorageBucketName>
#	[sourceprefix <String>] [targetprefix <String>]
def doCopyCloudStorageBucket():
  s = buildGAPIObject(API.STORAGEREAD)
  source_bucket = None
  target_bucket = None
  source_prefix = None
  target_prefix = ''
  while Cmd.ArgumentsRemaining():
    myarg = getArgument()
    if myarg == 'sourcebucket':
      source_bucket = getString(Cmd.OB_URL)
    elif myarg == 'targetbucket':
      target_bucket = getString(Cmd.OB_URL)
    elif myarg == 'sourceprefix':
      source_prefix = getString(Cmd.OB_STRING, minLen=0)
    elif myarg == 'targetprefix':
      target_prefix = getString(Cmd.OB_STRING, minLen=0)
    else:
      unknownArgumentExit()
  if not target_bucket:
    missingArgumentExit('targetbucket')
  if not source_bucket:
    missingArgumentExit('sourcebucket')
  printGettingAllAccountEntities(Ent.FILE)
  pageMessage = getPageMessage()
  try:
    objects = callGAPIpages(s.objects(), 'list', 'items',
                            pageMessage=pageMessage,
                            throwReasons=[GAPI.NOT_FOUND, GAPI.FORBIDDEN],
                            bucket=source_bucket, prefix=source_prefix,
                            fields='nextPageToken,items(name,bucket,md5Hash)')
  except GAPI.notFound:
    entityDoesNotExistExit(Ent.CLOUD_STORAGE_BUCKET, source_bucket)
  except GAPI.forbidden as e:
    entityActionFailedExit([Ent.CLOUD_STORAGE_BUCKET, source_bucket], str(e))
  _copyStorageObjects(objects, target_bucket, target_prefix)

# gam download storagebucket <TakeoutBucketName>
#	[targetfolder <FilePath>]
def doDownloadCloudStorageBucket():
  bucket_url = getString(Cmd.OB_STRING)
  targetFolder = GC.Values[GC.DRIVE_DIR]
  while Cmd.ArgumentsRemaining():
    myarg = getArgument()
    if myarg == 'targetfolder':
      targetFolder = setFilePath(getString(Cmd.OB_FILE_PATH), GC.DRIVE_DIR)
      if not os.path.isdir(targetFolder):
        os.makedirs(targetFolder)
    else:
      unknownArgumentExit()
  bucket_match = re.search(TAKEOUT_EXPORT_PATTERN, bucket_url)
  if not bucket_match:
    systemErrorExit(ACTION_NOT_PERFORMED_RC, f'Could not find a takeout-export-* bucket in {bucket_url}')
  bucket = bucket_match.group(1)
  s = buildGAPIObject(API.STORAGEREAD)
  printGettingAllAccountEntities(Ent.FILE)
  pageMessage = getPageMessage()
  try:
    objects = callGAPIpages(s.objects(), 'list', 'items',
                            pageMessage=pageMessage,
                            throwReasons=[GAPI.NOT_FOUND, GAPI.FORBIDDEN],
                            bucket=bucket, projection='noAcl', fields='nextPageToken,items(name,md5Hash)')
  except GAPI.notFound:
    entityDoesNotExistExit(Ent.CLOUD_STORAGE_BUCKET, bucket)
  except GAPI.forbidden as e:
    entityActionFailedExit([Ent.CLOUD_STORAGE_BUCKET, bucket], str(e))
  count = len(objects)
  i = 0
  for s_object in objects:
    i += 1
    printGettingEntityItem(Ent.FILE, s_object['name'], i, count)
    expectedMd5 = base64.b64decode(s_object['md5Hash']).hex()
    _getCloudStorageObject(s, bucket, s_object['name'], os.path.join(targetFolder, s_object['name']),
                           expectedMd5=expectedMd5)

# gam download storagefile <StorageBucketObjectName>
#	[targetfolder <FilePath>] [overwrite [<Boolean>]] [nogcspath [Boolean>]]
def doDownloadCloudStorageFile():
  bucket, s_object, bucketObject = getBucketObjectName()
  targetFolder = GC.Values[GC.DRIVE_DIR]
  overwrite = nogcspath = False
  while Cmd.ArgumentsRemaining():
    myarg = getArgument()
    if myarg == 'targetfolder':
      targetFolder = setFilePath(getString(Cmd.OB_FILE_PATH), GC.DRIVE_DIR)
      if not os.path.isdir(targetFolder):
        os.makedirs(targetFolder)
    elif myarg == 'overwrite':
      overwrite = getBoolean()
    elif myarg == 'nogcspath':
      nogcspath = getBoolean()
    else:
      unknownArgumentExit()
  s_obpaths = s_object.rsplit('/', 1)
  s_obfile = s_obpaths[-1]
  if len(s_obpaths) > 1 and not nogcspath:
    targetFolder = os.path.join(targetFolder, s_obpaths[0])
  filename, _ = uniqueFilename(targetFolder, s_obfile, overwrite)
  filepath = os.path.dirname(filename)
  if not os.path.exists(filepath):
    os.makedirs(filepath)
  s = buildGAPIObject(API.STORAGEREAD)
  printGettingEntityItem(Ent.FILE, s_object)
  f = openFile(filename, 'wb')
  try:
    request = s.objects().get_media(bucket=bucket, object=s_object)
    downloader = googleapiclient.http.MediaIoBaseDownload(f, request)
    done = False
    while not done:
      _, done = downloader.next_chunk()
    entityModifierNewValueActionPerformed([Ent.CLOUD_STORAGE_FILE, s_object], Act.MODIFIER_TO, filename)
    closeFile(f, True)
  except googleapiclient.http.HttpError as e:
    mg = HTTP_ERROR_PATTERN.match(str(e))
    entityActionFailedWarning([Ent.CLOUD_STORAGE_FILE, bucketObject], mg.group(1) if mg else str(e))

