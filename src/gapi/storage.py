import base64
import os
import re
import sys

import googleapiclient

import __main__
from var import *
import controlflow
import fileutils
import gapi
import utils


def build_gapi():
    return __main__.buildGAPIObject('storage')


def get_cloud_storage_object(s, bucket, object_, local_file=None,
                             expectedMd5=None):
    if not local_file:
        local_file = object_
    if os.path.exists(local_file):
        sys.stdout.write(' File already exists. ')
        sys.stdout.flush()
        if expectedMd5:
            sys.stdout.write(f'Verifying {expectedMd5} hash...')
            sys.stdout.flush()
            if utils.md5_matches_file(local_file, expectedMd5, False):
                print('VERIFIED')
                return
            print('not verified. Downloading again and over-writing...')
        else:
            return  # nothing to verify, just assume we're good.
    print(f'saving to {local_file}')
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
    s = build_gapi()
    page_message = gapi.got_total_items_msg('Files', '...')
    fields = 'nextPageToken,items(name,id,md5Hash)'
    objects = gapi.get_all_pages(s.objects(), 'list', 'items',
                                 page_message=page_message, bucket=bucket,
                                 projection='noAcl', fields=fields)
    i = 1
    for object_ in objects:
        print(f'{i}/{len(objects)}')
        expectedMd5 = base64.b64decode(object_['md5Hash']).hex()
        get_cloud_storage_object(
            s, bucket, object_['name'], expectedMd5=expectedMd5)
        i += 1
