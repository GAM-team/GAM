"""Google Doc/Sheet/Cloud Storage constants and pure utility functions.

This module contains format constants, regex patterns, and the Cloud Storage
bucket name parser.  The composite data-fetching functions
(:func:`getGDocData`, :func:`getGSheetData`, :func:`getStorageFileData`,
:func:`openCSVFileReader`, :func:`getStringOrFile`, etc.) have been moved
to :mod:`gam.cmd.drive.gdoc_fetch` where they belong in the ``cmd`` layer.
"""

import re
from urllib.parse import unquote

from gam.var import Cmd
from gam.util.args import getString
from gam.util.display import ACTION_NOT_PERFORMED_RC
from gam.util.output import systemErrorExit

HTTP_ERROR_PATTERN = re.compile(r'^.*returned \"(.*)\"\>$')

GDOC_FORMAT_MIME_TYPES = {
  'gcsv': 'text/csv',
  'gdoc': 'text/plain',
  'ghtml': 'text/html',
  }

GCS_FORMAT_MIME_TYPES = {
  'gcscsv': 'text/csv',
  'gcsdoc': 'text/plain',
  'gcshtml': 'text/html',
  }

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

# String-or-file argument constants.
SORF_SIG_ARGUMENTS = {'signature', 'sig', 'textsig', 'htmlsig'}
SORF_MSG_ARGUMENTS = {'message', 'textmessage', 'htmlmessage'}
SORF_FILE_ARGUMENTS = {'file', 'textfile', 'htmlfile', 'gdoc', 'ghtml', 'gcsdoc', 'gcshtml'}
SORF_HTML_ARGUMENTS = {'htmlsig', 'htmlmessage', 'htmlfile', 'ghtml', 'gcshtml'}
SORF_TEXT_ARGUMENTS = {'text', 'textfile', 'gdoc', 'gcsdoc'}
SORF_SIG_FILE_ARGUMENTS = SORF_SIG_ARGUMENTS.union(SORF_FILE_ARGUMENTS)
SORF_MSG_FILE_ARGUMENTS = SORF_MSG_ARGUMENTS.union(SORF_FILE_ARGUMENTS)
