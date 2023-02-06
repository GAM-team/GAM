import base64
import os
import re
import sys
import time

import googleapiclient
from pathvalidate import sanitize_filepath

import gam
from gam.gapi import errors as gapi_errors
from gam.var import *
from gam import controlflow
from gam import fileutils
from gam import gapi
from gam import utils


def build():
    return gam.buildGAPIObject('storage')


def copy_bucket():
    s = build()
    source_bucket = None
    target_bucket = None
    prefix = None
    target_prefix = ''
    i = 3
    while i < len(sys.argv):
        myarg = sys.argv[i].lower().replace('_', '')
        if myarg == 'sourcebucket':
            source_bucket = sys.argv[i+1]
            i += 2
        elif myarg == 'targetbucket':
            target_bucket = sys.argv[i+1]
            i += 2
        elif myarg == 'sourceprefix':
            prefix = sys.argv[i+1]
            i += 2
        elif myarg == 'targetprefix':
            target_prefix = sys.argv[i+1]
            i += 2
        else:
            controlflow.invalid_argument_exit(sys.argv[i],
                                              'gam copy storagebucket')
    if not target_bucket:
        controlflow.missing_argument_exit('target_bucket', 'gam copy storagebucket')
    if not source_bucket:
        controlflow.missing_argument_exit('source_bucket', 'gam copy storagebucket')
    page_message = gapi.got_total_items_msg('Storage Objects', '...\n')
    objects = gapi.get_all_pages(s.objects(),
                                 'list',
                                 items='items',
                                 page_message=page_message,
                                 prefix=prefix,
                                 bucket=source_bucket,
                                 fields='items(name,bucket,md5Hash),nextPageToken')
    copy_objects(objects,
                 target_bucket,
                 target_prefix)


def copy_objects(objects,
                 target_bucket,
                 target_prefix):
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
        file_ptr = int(request_id)
        if exception:
            # Poor man's backoff/retry
            if exception.status_code == 429 or exception.status_code > 499:
                print(f'Temporary error {exception.status_code}. Sleeping 10 seconds...')
                time.sleep(10)
                next_batch.add(s.objects().rewrite(**files_to_copy[file_ptr]['method']),
                                                   request_id=request_id)
                return
            else:
                raise exception
        file_count = file_ptr + 1
        source_displayname = files_to_copy[file_ptr]['source_displayname']
        target_displayname = files_to_copy[file_ptr]['target_displayname']
        if response.get('done'):
            source_md5 = files_to_copy[file_ptr]['md5Hash']
            target_md5 = response['resource']['md5Hash']
            if source_md5 != target_md5:
                controlflow.system_error_exit(99, f'Target file {target_displayname} checksum {target_md5} does not match source {source_md5}. This should not happen')
            else:
                print(f'[ {file_count} / {total_files} ] 100% VERIFIED - finished copying:\n  source: {source_displayname}\n  dest: {target_displayname}')
        else:
            total_bytes = float(response.get('objectSize'))
            done_bytes = float(response.get('totalBytesRewritten'))
            pct = (done_bytes / total_bytes) * 100
            print(f'[ {file_count} / {total_files} ] {pct:.2f}%\n  source: {source_displayname}\n  dest:{target_displayname}')
            files_to_copy[file_ptr]['method']['rewriteToken'] = response.get('rewriteToken')
            next_batch.add(s.objects().rewrite(**files_to_copy[file_ptr]['method']),
                                               request_id=request_id)

    s = build()
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
                        #        'maxBytesRewrittenPerCall': 1048576, # uncomment to easily test multiple rewrite API calls per object
                               },
                })
    i = 0
    total_files = len(files_to_copy)
    for file in files_to_copy:
        while len(sbatch._order) == 100:
            next_batch = s.new_batch_http_request(callback=process_rewrite)
            sbatch.execute()
            sbatch = next_batch
        sbatch.add(s.objects().rewrite(**file['method']),
                   request_id=str(i))
        i += 1
    while len(sbatch._order) > 0:
        next_batch = s.new_batch_http_request(callback=process_rewrite)
        sbatch.execute()
        sbatch = next_batch
    print('All done!')


def get_cloud_storage_object(s,
                             bucket,
                             object_,
                             local_file=None,
                             expectedMd5=None):
    if not local_file:
        local_file = object_
    local_file = sanitize_filepath(local_file, platform='auto')
    if os.path.exists(local_file):
        sys.stdout.write(f'File {local_file} already exists.')
        sys.stdout.flush()
        if expectedMd5:
            sys.stdout.write(f' verifying {expectedMd5} hash...')
            sys.stdout.flush()
            if utils.md5_matches_file(local_file, expectedMd5, False):
                print('VERIFIED')
                return
            print('not verified. Downloading again and over-writing...')
        else:
            return  # nothing to verify, just assume we're good.
    print(f'Saving to {local_file}')
    request = s.objects().get_media(bucket=bucket, object=object_)
    file_path = os.path.dirname(local_file)
    if not os.path.exists(file_path):
        os.makedirs(file_path)
    f = fileutils.open_file(local_file, 'wb')
    downloader = googleapiclient.http.MediaIoBaseDownload(f, request)
    done = False
    while not done:
        status, done = downloader.next_chunk()
        sys.stdout.write(f' Downloaded: {status.progress():>7.2%}\r')
        sys.stdout.flush()
    sys.stdout.write('\n Download complete. Flushing to disk...\n')
    fileutils.close_file(f, True)
    if expectedMd5:
        f = fileutils.open_file(local_file, 'rb')
        sys.stdout.write(f' Verifying file hash is {expectedMd5}...')
        sys.stdout.flush()
        utils.md5_matches_file(local_file, expectedMd5, True)
        print('VERIFIED')
        fileutils.close_file(f)


def download_bucket():
    bucket = sys.argv[3]
    s = build()
    page_message = gapi.got_total_items_msg('Files', '...')
    fields = 'nextPageToken,items(name,id,md5Hash)'
    objects = gapi.get_all_pages(s.objects(),
                                 'list',
                                 'items',
                                 page_message=page_message,
                                 bucket=bucket,
                                 projection='noAcl',
                                 fields=fields)
    i = 1
    for object_ in objects:
        print(f'{i}/{len(objects)}')
        expectedMd5 = base64.b64decode(object_['md5Hash']).hex()
        get_cloud_storage_object(s,
                                 bucket,
                                 object_['name'],
                                 expectedMd5=expectedMd5)
        i += 1
