#!/usr/bin/env python2
# -*- coding: utf-8 -*-
#
# GAM
#
# Copyright 2015, LLC All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
u"""GAM is a command line tool which allows Administrators to control their G Suite domain and accounts.

With GAM you can programatically create users, turn on/off services for users like POP and Forwarding and much more.
For more information, see https://git.io/gam
"""

import sys
import os
import string
import time
import base64
import codecs
import csv
import datetime
import httplib
import json
import mimetypes
import platform
import random
import re
import signal
import socket
import StringIO
import uuid

import googleapiclient
import googleapiclient.discovery
import googleapiclient.errors
import googleapiclient.http
import httplib2
import google.oauth2.service_account
import google_auth_httplib2
import oauth2client.client
import oauth2client.file
import oauth2client.tools

import utils
from var import *

# Override some oauth2client.tools strings saving us a few GAM-specific mods to oauth2client
oauth2client.tools._FAILED_START_MESSAGE = """
Failed to start a local webserver listening on either port 8080
or port 8090. Please check your firewall settings and locally
running programs that may be blocking or using those ports.

Falling back to nobrowser.txt  and continuing with
authorization.
"""

oauth2client.tools._BROWSER_OPENED_MESSAGE = """
Your browser has been opened to visit:

    {address}

If your browser is on a different machine then press CTRL+C and
create a file called nobrowser.txt in the same folder as GAM.
"""

oauth2client.tools._GO_TO_LINK_MESSAGE = """
Go to the following link in your browser:

    {address}
"""

# Override and wrap google_auth_httplib2 request methods so that the GAM
# user-agent string is inserted into HTTP request headers.
def _request_with_user_agent(request_method):
  """Inserts the GAM user-agent header kwargs sent to a method."""
  GAM_USER_AGENT = GAM_INFO

  def wrapped_request_method(self, *args, **kwargs):
    if kwargs.get('headers') is not None:
      if kwargs['headers'].get('user-agent'):
        if GAM_USER_AGENT not in kwargs['headers']['user-agent']:
          # Save the existing user-agent header and tack on the GAM user-agent.
          kwargs['headers']['user-agent'] = '%s %s' % (
              GAM_USER_AGENT, kwargs['headers']['user-agent'])
      else:
        kwargs['headers']['user-agent'] = GAM_USER_AGENT
    else:
      kwargs['headers'] = {'user-agent': GAM_USER_AGENT}

    return request_method(self, *args, **kwargs)

  return wrapped_request_method

google_auth_httplib2.Request.__call__ = _request_with_user_agent(
    google_auth_httplib2.Request.__call__)
google_auth_httplib2.AuthorizedHttp.request = _request_with_user_agent(
    google_auth_httplib2.AuthorizedHttp.request)

def showUsage():
  doGAMVersion(checkForArgs=False)
  print u'''
Usage: gam [OPTIONS]...

GAM. Retrieve or set G Suite domain,
user, group and alias settings. Exhaustive list of commands
can be found at: https://github.com/jay0lee/GAM/wiki

Examples:
gam info domain
gam create user jsmith firstname John lastname Smith password secretpass
gam update user jsmith suspended on
gam.exe update group announcements add member jsmith
...

'''
#
# Error handling
#
def stderrErrorMsg(message):
  sys.stderr.write(utils.convertUTF8(u'\n{0}{1}\n'.format(ERROR_PREFIX, message)))

def stderrWarningMsg(message):
  sys.stderr.write(utils.convertUTF8(u'\n{0}{1}\n'.format(WARNING_PREFIX, message)))

def systemErrorExit(sysRC, message):
  if message:
    stderrErrorMsg(message)
  sys.exit(sysRC)

def invalidJSONExit(fileName):
  systemErrorExit(17, MESSAGE_INVALID_JSON.format(fileName))

def noPythonSSLExit():
  systemErrorExit(8, MESSAGE_NO_PYTHON_SSL)

def currentCount(i, count):
  return u' ({0}/{1})'.format(i, count) if (count > GC_Values[GC_SHOW_COUNTS_MIN]) else u''

def currentCountNL(i, count):
  return u' ({0}/{1})\n'.format(i, count) if (count > GC_Values[GC_SHOW_COUNTS_MIN]) else u'\n'

def formatHTTPError(http_status, reason, message):
  return u'{0}: {1} - {2}'.format(http_status, reason, message)

def getHTTPError(responses, http_status, reason, message):
  if reason in responses:
    return responses[reason]
  return formatHTTPError(http_status, reason, message)

def entityServiceNotApplicableWarning(entityType, entityName, i, count):
  sys.stderr.write(u'{0}: {1}, Service not applicable/Does not exist{2}'.format(entityType, entityName, currentCountNL(i, count)))

def entityDoesNotExistWarning(entityType, entityName, i, count):
  sys.stderr.write(u'{0}: {1}, Does not exist{2}'.format(entityType, entityName, currentCountNL(i, count)))

def entityUnknownWarning(entityType, entityName, i, count):
  domain = getEmailAddressDomain(entityName)
  if (domain == GC_Values[GC_DOMAIN]) or (domain.endswith(u'google.com')):
    entityDoesNotExistWarning(entityType, entityName, i, count)
  else:
    entityServiceNotApplicableWarning(entityType, entityName, i, count)

# Invalid CSV ~Header or ~~Header~~
def csvFieldErrorExit(fieldName, fieldNames):
  systemErrorExit(2, MESSAGE_HEADER_NOT_FOUND_IN_CSV_HEADERS.format(fieldName, u','.join(fieldNames)))

def printLine(message):
  sys.stdout.write(message+u'\n')
#
def getBoolean(value, item):
  value = value.lower()
  if value in true_values:
    return True
  if value in false_values:
    return False
  systemErrorExit(2, u'Value for {0} must be {1} or {2}; got {3}'.format(item, u'|'.join(true_values), u'|'.join(false_values), value))

def getCharSet(i):
  if (i == len(sys.argv)) or (sys.argv[i].lower() != u'charset'):
    return (i, GC_Values.get(GC_CHARSET, GM_Globals[GM_SYS_ENCODING]))
  return (i+2, sys.argv[i+1])

COLORHEX_PATTERN = re.compile(r'^#[0-9a-fA-F]{6}$')

def getColor(color):
  color = color.lower().strip()
  if color in WEBCOLOR_MAP:
    return WEBCOLOR_MAP[color]
  tg = COLORHEX_PATTERN.match(color)
  if tg:
    return tg.group(0)
  systemErrorExit(2, u'A color must be a valid name or # and six hex characters (#012345); got {0}'.format(color))

def integerLimits(minVal, maxVal, item=u'integer'):
  if (minVal is not None) and (maxVal is not None):
    return u'{0} {1}<=x<={2}'.format(item, minVal, maxVal)
  if minVal is not None:
    return u'{0} x>={1}'.format(item, minVal)
  if maxVal is not None:
    return u'{0} x<={1}'.format(item, maxVal)
  return u'{0} x'.format(item)

def removeCourseIdScope(courseId):
  if courseId.startswith(u'd:'):
    return courseId[2:]
  return courseId

def addCourseIdScope(courseId):
  if not courseId.isdigit() and courseId[:2] != u'd:':
    return u'd:{0}'.format(courseId)
  return courseId

def getString(i, item, optional=False, minLen=1, maxLen=None):
  if i < len(sys.argv):
    argstr = sys.argv[i]
    if argstr:
      if (len(argstr) >= minLen) and ((maxLen is None) or (len(argstr) <= maxLen)):
        return argstr
      systemErrorExit(2, u'expected <{0} for {1}>'.format(integerLimits(minLen, maxLen, u'string length'), item))
    if optional or (minLen == 0):
      return u''
    systemErrorExit(2, u'expected a Non-empty <{0}>'.format(item))
  elif optional:
    return u''
  systemErrorExit(2, u'expected a <{0}>'.format(item))

def getDelta(argstr, pattern, formatRequired):
  tg = pattern.match(argstr.lower())
  if tg is None:
    systemErrorExit(2, u'expected a <{0}>; got {1}'.format(formatRequired, argstr))
  sign = tg.group(1)
  delta = int(tg.group(2))
  unit = tg.group(3)
  if unit == u'w':
    deltaTime = datetime.timedelta(weeks=delta)
  elif unit == u'd':
    deltaTime = datetime.timedelta(days=delta)
  elif unit == u'h':
    deltaTime = datetime.timedelta(hours=delta)
  elif unit == u'm':
    deltaTime = datetime.timedelta(minutes=delta)
  if sign == u'-':
    return -deltaTime
  return deltaTime

DELTA_DATE_PATTERN = re.compile(r'^([+-])(\d+)([dw])$')
DELTA_DATE_FORMAT_REQUIRED = u'(+|-)<Number>(d|w)'

def getDeltaDate(argstr):
  return getDelta(argstr, DELTA_DATE_PATTERN, DELTA_DATE_FORMAT_REQUIRED)

DELTA_TIME_PATTERN = re.compile(r'^([+-])(\d+)([mhdw])$')
DELTA_TIME_FORMAT_REQUIRED = u'(+|-)<Number>(m|h|d|w)'

def getDeltaTime(argstr):
  return getDelta(argstr, DELTA_TIME_PATTERN, DELTA_TIME_FORMAT_REQUIRED)

YYYYMMDD_FORMAT = u'%Y-%m-%d'
YYYYMMDD_FORMAT_REQUIRED = u'yyyy-mm-dd'

def getYYYYMMDD(argstr, minLen=1, returnTimeStamp=False, returnDateTime=False):
  argstr = argstr.strip()
  if argstr:
    if argstr[0] in [u'+', u'-']:
      today = datetime.date.today()
      argstr = (datetime.datetime(today.year, today.month, today.day)+getDeltaDate(argstr)).strftime(YYYYMMDD_FORMAT)
    try:
      dateTime = datetime.datetime.strptime(argstr, YYYYMMDD_FORMAT)
      if returnTimeStamp:
        return time.mktime(dateTime.timetuple())*1000
      if returnDateTime:
        return dateTime
      return argstr
    except ValueError:
      systemErrorExit(2, u'expected a <{0}>; got {1}'.format(YYYYMMDD_FORMAT_REQUIRED, argstr))
  elif minLen == 0:
    return u''
  systemErrorExit(2, u'expected a <{0}>'.format(YYYYMMDD_FORMAT_REQUIRED))

YYYYMMDDTHHMMSS_FORMAT_REQUIRED = u'yyyy-mm-ddThh:mm:ss[.fff](Z|(+|-(hh:mm)))'

def getTimeOrDeltaFromNow(time_string):
  """Get an ISO 8601 date/time or a positive/negative delta applied to now.
  Args:
    time_string (string): The time or delta (e.g. '2017-09-01T12:34:56Z' or '-4h')
  Returns:
    string: iso8601 formatted datetime in UTC.
  Exits:
    2: Not a valid delta.
  """
  time_string = time_string.strip().upper()
  if time_string:
    if time_string[0] not in [u'+', u'-']:
      return time_string
    return (datetime.datetime.utcnow() + getDeltaTime(time_string)).isoformat() + u'Z'
  systemErrorExit(2, u'expected a <{0}>'.format(YYYYMMDDTHHMMSS_FORMAT_REQUIRED))

YYYYMMDD_PATTERN = re.compile(r'^[0-9]{4}-[0-9]{2}-[0-9]{2}$')

def getDateZeroTimeOrFullTime(time_string):
  time_string = time_string.strip()
  if time_string:
    if YYYYMMDD_PATTERN.match(time_string):
      return getYYYYMMDD(time_string)+u'T00:00:00.000Z'
    return getTimeOrDeltaFromNow(time_string)
  systemErrorExit(2, u'expected a <{0}>'.format(YYYYMMDDTHHMMSS_FORMAT_REQUIRED))

# Get domain from email address
def getEmailAddressDomain(emailAddress):
  atLoc = emailAddress.find(u'@')
  if atLoc == -1:
    return GC_Values[GC_DOMAIN].lower()
  return emailAddress[atLoc+1:].lower()

# Split email address unto user and domain
def splitEmailAddress(emailAddress):
  atLoc = emailAddress.find(u'@')
  if atLoc == -1:
    return (emailAddress.lower(), GC_Values[GC_DOMAIN].lower())
  return (emailAddress[:atLoc].lower(), emailAddress[atLoc+1:].lower())

# Normalize user/group email address/uid
# uid:12345abc -> 12345abc
# foo -> foo@domain
# foo@ -> foo@domain
# foo@bar.com -> foo@bar.com
# @domain -> domain
def normalizeEmailAddressOrUID(emailAddressOrUID, noUid=False, checkForCustomerId=False):
  if checkForCustomerId and (emailAddressOrUID == GC_Values[GC_CUSTOMER_ID]):
    return emailAddressOrUID
  if (not noUid) and (emailAddressOrUID.find(u':') != -1):
    if emailAddressOrUID[:4].lower() == u'uid:':
      return emailAddressOrUID[4:]
    if emailAddressOrUID[:3].lower() == u'id:':
      return emailAddressOrUID[3:]
  atLoc = emailAddressOrUID.find(u'@')
  if atLoc == 0:
    return emailAddressOrUID[1:].lower()
  if (atLoc == -1) or (atLoc == len(emailAddressOrUID)-1) and GC_Values[GC_DOMAIN]:
    if atLoc == -1:
      emailAddressOrUID = u'{0}@{1}'.format(emailAddressOrUID, GC_Values[GC_DOMAIN])
    else:
      emailAddressOrUID = u'{0}{1}'.format(emailAddressOrUID, GC_Values[GC_DOMAIN])
  return emailAddressOrUID.lower()

# Normalize student/guardian email address/uid
# 12345678 -> 12345678
# - -> -
# Otherwise, same results as normalizeEmailAddressOrUID
def normalizeStudentGuardianEmailAddressOrUID(emailAddressOrUID):
  if emailAddressOrUID.isdigit() or emailAddressOrUID == u'-':
    return emailAddressOrUID
  return normalizeEmailAddressOrUID(emailAddressOrUID)
#
# Open a file
#
def openFile(filename, mode=u'rU'):
  try:
    if filename != u'-':
      return open(os.path.expanduser(filename), mode)
    if mode.startswith(u'r'):
      return StringIO.StringIO(unicode(sys.stdin.read()))
    return sys.stdout
  except IOError as e:
    systemErrorExit(6, e)
#
# Close a file
#
def closeFile(f):
  try:
    f.close()
    return True
  except IOError as e:
    stderrErrorMsg(e)
    return False
#
# Read a file
#
def readFile(filename, mode=u'rb', continueOnError=False, displayError=True, encoding=None):
  try:
    if filename != u'-':
      if not encoding:
        with open(os.path.expanduser(filename), mode) as f:
          return f.read()
      with codecs.open(os.path.expanduser(filename), mode, encoding) as f:
        content = f.read()
# codecs does not strip UTF-8 BOM (ef:bb:bf) so we must
        if not content.startswith(codecs.BOM_UTF8):
          return content
        return content[3:]
    return unicode(sys.stdin.read())
  except IOError as e:
    if continueOnError:
      if displayError:
        stderrWarningMsg(e)
      return None
    systemErrorExit(6, e)
  except (LookupError, UnicodeDecodeError, UnicodeError) as e:
    systemErrorExit(2, str(e))
#
# Write a file
#
def writeFile(filename, data, mode=u'wb', continueOnError=False, displayError=True):
  try:
    with open(os.path.expanduser(filename), mode) as f:
      f.write(data)
    return True
  except IOError as e:
    if continueOnError:
      if displayError:
        stderrErrorMsg(e)
      return False
    systemErrorExit(6, e)
#
class UTF8Recoder(object):
  """
  Iterator that reads an encoded stream and reencodes the input to UTF-8
  """
  def __init__(self, f, encoding):
    self.reader = codecs.getreader(encoding)(f)

  def __iter__(self):
    return self

  def next(self):
    return self.reader.next().encode(u'utf-8')

class UnicodeDictReader(object):
  """
  A CSV reader which will iterate over lines in the CSV file "f",
  which is encoded in the given encoding.
  """

  def __init__(self, f, dialect=csv.excel, encoding=u'utf-8', **kwds):
    self.encoding = encoding
    try:
      self.reader = csv.reader(UTF8Recoder(f, encoding) if self.encoding != u'utf-8' else f, dialect=dialect, **kwds)
      self.fieldnames = self.reader.next()
      if len(self.fieldnames) > 0 and self.fieldnames[0].startswith(codecs.BOM_UTF8):
        self.fieldnames[0] = self.fieldnames[0].replace(codecs.BOM_UTF8, '', 1)
    except (csv.Error, StopIteration):
      self.fieldnames = []
    except LookupError as e:
      systemErrorExit(2, str(e))
    self.numfields = len(self.fieldnames)

  def __iter__(self):
    return self

  def next(self):
    row = self.reader.next()
    l = len(row)
    if l < self.numfields:
      row += ['']*(self.numfields-l) # Must be '', not u''
    return dict((self.fieldnames[x], unicode(row[x], u'utf-8')) for x in range(self.numfields))
#
# Set global variables
# Check for GAM updates based on status of noupdatecheck.txt
#
def SetGlobalVariables():

  def _getOldEnvVar(itemName, envVar):
    value = os.environ.get(envVar, GC_Defaults[itemName])
    if GC_VAR_INFO[itemName][GC_VAR_TYPE] == GC_TYPE_INTEGER:
      try:
        number = int(value)
        minVal, maxVal = GC_VAR_INFO[itemName][GC_VAR_LIMITS]
        if number < minVal:
          number = minVal
        elif maxVal and (number > maxVal):
          number = maxVal
      except ValueError:
        number = GC_Defaults[itemName]
      value = number
    GC_Defaults[itemName] = value

  def _getOldSignalFile(itemName, fileName, filePresentValue=True, fileAbsentValue=False):
    GC_Defaults[itemName] = filePresentValue if os.path.isfile(os.path.join(GC_Defaults[GC_CONFIG_DIR], fileName)) else fileAbsentValue

  def _getCfgDirectory(itemName):
    return GC_Defaults[itemName]

  def _getCfgFile(itemName):
    value = os.path.expanduser(GC_Defaults[itemName])
    if not os.path.isabs(value):
      value = os.path.expanduser(os.path.join(GC_Values[GC_CONFIG_DIR], value))
    return value

  GC_Defaults[GC_CONFIG_DIR] = GM_Globals[GM_GAM_PATH]
  GC_Defaults[GC_CACHE_DIR] = os.path.join(GM_Globals[GM_GAM_PATH], u'gamcache')
  GC_Defaults[GC_DRIVE_DIR] = GM_Globals[GM_GAM_PATH]
  GC_Defaults[GC_SITE_DIR] = GM_Globals[GM_GAM_PATH]

  _getOldEnvVar(GC_CONFIG_DIR, u'GAMUSERCONFIGDIR')
  _getOldEnvVar(GC_SITE_DIR, u'GAMSITECONFIGDIR')
  _getOldEnvVar(GC_CACHE_DIR, u'GAMCACHEDIR')
  _getOldEnvVar(GC_DRIVE_DIR, u'GAMDRIVEDIR')
  _getOldEnvVar(GC_OAUTH2_TXT, u'OAUTHFILE')
  _getOldEnvVar(GC_OAUTH2SERVICE_JSON, u'OAUTHSERVICEFILE')
  if GC_Defaults[GC_OAUTH2SERVICE_JSON].find(u'.') == -1:
    GC_Defaults[GC_OAUTH2SERVICE_JSON] += u'.json'
  _getOldEnvVar(GC_CLIENT_SECRETS_JSON, u'CLIENTSECRETS')
  _getOldEnvVar(GC_DOMAIN, u'GA_DOMAIN')
  _getOldEnvVar(GC_CUSTOMER_ID, u'CUSTOMER_ID')
  _getOldEnvVar(GC_CHARSET, u'GAM_CHARSET')
  _getOldEnvVar(GC_NUM_THREADS, u'GAM_THREADS')
  _getOldEnvVar(GC_ACTIVITY_MAX_RESULTS, u'GAM_ACTIVITY_MAX_RESULTS')
  _getOldEnvVar(GC_AUTO_BATCH_MIN, u'GAM_AUTOBATCH')
  _getOldEnvVar(GC_BATCH_SIZE, u'GAM_BATCH_SIZE')
  _getOldEnvVar(GC_DEVICE_MAX_RESULTS, u'GAM_DEVICE_MAX_RESULTS')
  _getOldEnvVar(GC_DRIVE_MAX_RESULTS, u'GAM_DRIVE_MAX_RESULTS')
  _getOldEnvVar(GC_MEMBER_MAX_RESULTS, u'GAM_MEMBER_MAX_RESULTS')
  _getOldEnvVar(GC_USER_MAX_RESULTS, u'GAM_USER_MAX_RESULTS')
  _getOldSignalFile(GC_DEBUG_LEVEL, u'debug.gam', filePresentValue=4, fileAbsentValue=0)
  _getOldSignalFile(GC_NO_VERIFY_SSL, u'noverifyssl.txt')
  _getOldSignalFile(GC_NO_BROWSER, u'nobrowser.txt')
#  _getOldSignalFile(GC_NO_CACHE, u'nocache.txt')
#  _getOldSignalFile(GC_CACHE_DISCOVERY_ONLY, u'allcache.txt', filePresentValue=False, fileAbsentValue=True)
  _getOldSignalFile(GC_NO_CACHE, u'allcache.txt', filePresentValue=False, fileAbsentValue=True)
  _getOldSignalFile(GC_NO_UPDATE_CHECK, u'noupdatecheck.txt')
# Assign directories first
  for itemName in GC_VAR_INFO:
    if GC_VAR_INFO[itemName][GC_VAR_TYPE] == GC_TYPE_DIRECTORY:
      GC_Values[itemName] = _getCfgDirectory(itemName)
  for itemName in GC_VAR_INFO:
    varType = GC_VAR_INFO[itemName][GC_VAR_TYPE]
    if varType == GC_TYPE_FILE:
      GC_Values[itemName] = _getCfgFile(itemName)
    else:
      GC_Values[itemName] = GC_Defaults[itemName]
  GM_Globals[GM_LAST_UPDATE_CHECK_TXT] = os.path.join(GC_Values[GC_CONFIG_DIR], FN_LAST_UPDATE_CHECK_TXT)
  if not GC_Values[GC_NO_UPDATE_CHECK]:
    doGAMCheckForUpdates()
# Globals derived from config file values
  GM_Globals[GM_OAUTH2SERVICE_JSON_DATA] = None
  GM_Globals[GM_OAUTH2SERVICE_ACCOUNT_CLIENT_ID] = None
  GM_Globals[GM_EXTRA_ARGS_DICT] = {u'prettyPrint': GC_Values[GC_DEBUG_LEVEL] > 0}
  httplib2.debuglevel = GC_Values[GC_DEBUG_LEVEL]
  if os.path.isfile(os.path.join(GC_Values[GC_CONFIG_DIR], FN_EXTRA_ARGS_TXT)):
    import ConfigParser
    ea_config = ConfigParser.ConfigParser()
    ea_config.optionxform = str
    ea_config.read(os.path.join(GC_Values[GC_CONFIG_DIR], FN_EXTRA_ARGS_TXT))
    GM_Globals[GM_EXTRA_ARGS_DICT].update(dict(ea_config.items(u'extra-args')))
  if GC_Values[GC_NO_CACHE]:
    GM_Globals[GM_CACHE_DIR] = None
    GM_Globals[GM_CACHE_DISCOVERY_ONLY] = False
  else:
    GM_Globals[GM_CACHE_DIR] = GC_Values[GC_CACHE_DIR]
#    GM_Globals[GM_CACHE_DISCOVERY_ONLY] = GC_Values[GC_CACHE_DISCOVERY_ONLY]
    GM_Globals[GM_CACHE_DISCOVERY_ONLY] = False
  return True

def doGAMCheckForUpdates(forceCheck=False):
  import calendar

  def _gamLatestVersionNotAvailable():
    if forceCheck:
      systemErrorExit(4, u'GAM Latest Version information not available')

  current_version = gam_version
  now_time = calendar.timegm(time.gmtime())
  if forceCheck:
    check_url = GAM_ALL_RELEASES # includes pre-releases
  else:
    last_check_time_str = readFile(GM_Globals[GM_LAST_UPDATE_CHECK_TXT], continueOnError=True, displayError=False)
    last_check_time = int(last_check_time_str) if last_check_time_str and last_check_time_str.isdigit() else 0
    if last_check_time > now_time-604800:
      return
    check_url = GAM_LATEST_RELEASE # latest full release
  headers = {u'Accept': u'application/vnd.github.v3.text+json'}
  simplehttp = httplib2.Http(disable_ssl_certificate_validation=GC_Values[GC_NO_VERIFY_SSL])
  try:
    (_, c) = simplehttp.request(check_url, u'GET', headers=headers)
    try:
      release_data = json.loads(c)
    except ValueError:
      _gamLatestVersionNotAvailable()
      return
    if isinstance(release_data, list):
      release_data = release_data[0] # only care about latest release
    if not isinstance(release_data, dict) or u'tag_name' not in release_data:
      _gamLatestVersionNotAvailable()
      return
    latest_version = release_data[u'tag_name']
    if latest_version[0].lower() == u'v':
      latest_version = latest_version[1:]
    if forceCheck or (latest_version > current_version):
      print u'Version Check:\n Current: {0}\n Latest: {1}'.format(current_version, latest_version)
    if latest_version <= current_version:
      writeFile(GM_Globals[GM_LAST_UPDATE_CHECK_TXT], str(now_time), continueOnError=True, displayError=forceCheck)
      return
    announcement = release_data.get(u'body_text', u'No details about this release')
    sys.stderr.write(u'\nGAM %s release notes:\n\n' % latest_version)
    sys.stderr.write(announcement)
    try:
      printLine(MESSAGE_HIT_CONTROL_C_TO_UPDATE)
      time.sleep(15)
    except KeyboardInterrupt:
      import webbrowser
      webbrowser.open(release_data[u'html_url'])
      printLine(MESSAGE_GAM_EXITING_FOR_UPDATE)
      sys.exit(0)
    writeFile(GM_Globals[GM_LAST_UPDATE_CHECK_TXT], str(now_time), continueOnError=True, displayError=forceCheck)
    return
  except (httplib2.HttpLib2Error, httplib2.ServerNotFoundError, httplib2.CertificateValidationUnsupported):
    return

def doGAMVersion(checkForArgs=True):
  force_check = False
  simple = False
  if checkForArgs:
    i = 2
    while i < len(sys.argv):
      myarg = sys.argv[i].lower().replace(u'_', u'')
      if myarg == u'check':
        force_check = True
        i += 1
      elif myarg == u'simple':
        simple = True
        i += 1
      else:
        systemErrorExit(2, u'%s is not a valid argument for "gam version"' % sys.argv[i])
  if simple:
    sys.stdout.write(gam_version)
    return
  import struct
  version_data = u'GAM {0} - {1}\n{2}\nPython {3}.{4}.{5} {6}-bit {7}\ngoogle-api-python-client {8}\noauth2client {9}\n{10} {11}\nPath: {12}'
  print version_data.format(gam_version, GAM_URL, gam_author, sys.version_info[0],
                            sys.version_info[1], sys.version_info[2], struct.calcsize(u'P')*8,
                            sys.version_info[3], googleapiclient.__version__, oauth2client.__version__, platform.platform(),
                            platform.machine(), GM_Globals[GM_GAM_PATH])
  if force_check:
    doGAMCheckForUpdates(forceCheck=True)

def handleOAuthTokenError(e, soft_errors):
  if e.replace(u'.', u'') in OAUTH2_TOKEN_ERRORS or e.startswith(u'Invalid response'):
    if soft_errors:
      return None
    if not GM_Globals[GM_CURRENT_API_USER]:
      stderrErrorMsg(MESSAGE_API_ACCESS_DENIED.format(GM_Globals[GM_OAUTH2SERVICE_ACCOUNT_CLIENT_ID],
                                                      u','.join(GM_Globals[GM_CURRENT_API_SCOPES])))
      systemErrorExit(12, MESSAGE_API_ACCESS_CONFIG)
    else:
      systemErrorExit(19, MESSAGE_SERVICE_NOT_APPLICABLE.format(GM_Globals[GM_CURRENT_API_USER]))
  systemErrorExit(18, u'Authentication Token Error - {0}'.format(e))

def getSvcAcctCredentials(scopes, act_as):
  try:
    if not GM_Globals[GM_OAUTH2SERVICE_JSON_DATA]:
      json_string = readFile(GC_Values[GC_OAUTH2SERVICE_JSON], continueOnError=True, displayError=True)
      if not json_string:
        printLine(MESSAGE_INSTRUCTIONS_OAUTH2SERVICE_JSON)
        systemErrorExit(6, None)
      GM_Globals[GM_OAUTH2SERVICE_JSON_DATA] = json.loads(json_string)
    credentials = google.oauth2.service_account.Credentials.from_service_account_info(GM_Globals[GM_OAUTH2SERVICE_JSON_DATA])
    credentials = credentials.with_scopes(scopes)
    credentials = credentials.with_subject(act_as)
    GM_Globals[GM_OAUTH2SERVICE_ACCOUNT_CLIENT_ID] = GM_Globals[GM_OAUTH2SERVICE_JSON_DATA]['client_id']
    return credentials
  except (ValueError, KeyError):
    printLine(MESSAGE_INSTRUCTIONS_OAUTH2SERVICE_JSON)
    invalidJSONExit(GC_Values[GC_OAUTH2SERVICE_JSON])

def waitOnFailure(n, retries, errMsg):
  wait_on_fail = min(2 ** n, 60) + float(random.randint(1, 1000)) / 1000
  if n > 3:
    sys.stderr.write(u'Temporary error: {0}, Backing off: {1} seconds, Retry: {2}/{3}\n'.format(errMsg, int(wait_on_fail), n, retries))
    sys.stderr.flush()
  time.sleep(wait_on_fail)

def checkGAPIError(e, soft_errors=False, silent_errors=False, retryOnHttpError=False, service=None):
  try:
    error = json.loads(e.content)
  except ValueError:
    if (e.resp[u'status'] == u'503') and (e.content == u'Quota exceeded for the current request'):
      return (e.resp[u'status'], GAPI_QUOTA_EXCEEDED, e.content)
    if (e.resp[u'status'] == u'403') and (e.content.startswith(u'Request rate higher than configured')):
      return (e.resp[u'status'], GAPI_QUOTA_EXCEEDED, e.content)
    if (e.resp[u'status'] == u'403') and (u'Invalid domain.' in e.content):
      error = {u'error': {u'code': 403, u'errors': [{u'reason': GAPI_NOT_FOUND, u'message': u'Domain not found'}]}}
    elif (e.resp[u'status'] == u'400') and (u'InvalidSsoSigningKey' in e.content):
      error = {u'error': {u'code': 400, u'errors': [{u'reason': GAPI_INVALID, u'message': u'InvalidSsoSigningKey'}]}}
    elif (e.resp[u'status'] == u'400') and (u'UnknownError' in e.content):
      error = {u'error': {u'code': 400, u'errors': [{u'reason': GAPI_INVALID, u'message': u'UnknownError'}]}}
    elif retryOnHttpError:
      service._http.request.credentials.refresh(httplib2.Http(disable_ssl_certificate_validation=GC_Values[GC_NO_VERIFY_SSL]))
      return (-1, None, None)
    elif soft_errors:
      if not silent_errors:
        stderrErrorMsg(e.content)
      return (0, None, None)
    else:
      systemErrorExit(5, e.content)
  if u'error' in error:
    http_status = error[u'error'][u'code']
    try:
      message = error[u'error'][u'errors'][0][u'message']
    except KeyError:
      message = error[u'error'][u'message']
  else:
    if u'error_description' in error:
      if error[u'error_description'] == u'Invalid Value':
        message = error[u'error_description']
        http_status = 400
        error = {u'error': {u'errors': [{u'reason': GAPI_INVALID, u'message': message}]}}
      else:
        systemErrorExit(4, str(error))
    else:
      systemErrorExit(4, str(error))
  try:
    reason = error[u'error'][u'errors'][0][u'reason']
    if reason == u'notFound':
      if u'userKey' in message:
        reason = GAPI_USER_NOT_FOUND
      elif u'groupKey' in message:
        reason = GAPI_GROUP_NOT_FOUND
      elif u'memberKey' in message:
        reason = GAPI_MEMBER_NOT_FOUND
      elif u'Domain not found' in message:
        reason = GAPI_DOMAIN_NOT_FOUND
      elif u'Resource Not Found' in message:
        reason = GAPI_RESOURCE_NOT_FOUND
    elif reason == u'invalid':
      if u'userId' in message:
        reason = GAPI_USER_NOT_FOUND
      elif u'memberKey' in message:
        reason = GAPI_INVALID_MEMBER
    elif reason == u'failedPrecondition':
      if u'Bad Request' in message:
        reason = GAPI_BAD_REQUEST
      elif u'Mail service not enabled' in message:
        reason = GAPI_SERVICE_NOT_AVAILABLE
    elif reason == u'required':
      if u'memberKey' in message:
        reason = GAPI_MEMBER_NOT_FOUND
    elif reason == u'conditionNotMet':
      if u'Cyclic memberships not allowed' in message:
        reason = GAPI_CYCLIC_MEMBERSHIPS_NOT_ALLOWED
  except KeyError:
    reason = u'{0}'.format(http_status)
  return (http_status, reason, message)

class GAPI_aborted(Exception):
  pass
class GAPI_authError(Exception):
  pass
class GAPI_badRequest(Exception):
  pass
class GAPI_conditionNotMet(Exception):
  pass
class GAPI_cyclicMembershipsNotAllowed(Exception):
  pass
class GAPI_domainCannotUseApis(Exception):
  pass
class GAPI_domainNotFound(Exception):
  pass
class GAPI_duplicate(Exception):
  pass
class GAPI_failedPrecondition(Exception):
  pass
class GAPI_forbidden(Exception):
  pass
class GAPI_groupNotFound(Exception):
  pass
class GAPI_invalid(Exception):
  pass
class GAPI_invalidArgument(Exception):
  pass
class GAPI_invalidMember(Exception):
  pass
class GAPI_memberNotFound(Exception):
  pass
class GAPI_notFound(Exception):
  pass
class GAPI_notImplemented(Exception):
  pass
class GAPI_resourceNotFound(Exception):
  pass
class GAPI_serviceNotAvailable(Exception):
  pass
class GAPI_userNotFound(Exception):
  pass

GAPI_REASON_EXCEPTION_MAP = {
  GAPI_ABORTED: GAPI_aborted,
  GAPI_AUTH_ERROR: GAPI_authError,
  GAPI_BAD_REQUEST: GAPI_badRequest,
  GAPI_CONDITION_NOT_MET: GAPI_conditionNotMet,
  GAPI_CYCLIC_MEMBERSHIPS_NOT_ALLOWED: GAPI_cyclicMembershipsNotAllowed,
  GAPI_DOMAIN_CANNOT_USE_APIS: GAPI_domainCannotUseApis,
  GAPI_DOMAIN_NOT_FOUND: GAPI_domainNotFound,
  GAPI_DUPLICATE: GAPI_duplicate,
  GAPI_FAILED_PRECONDITION: GAPI_failedPrecondition,
  GAPI_FORBIDDEN: GAPI_forbidden,
  GAPI_GROUP_NOT_FOUND: GAPI_groupNotFound,
  GAPI_INVALID: GAPI_invalid,
  GAPI_INVALID_ARGUMENT: GAPI_invalidArgument,
  GAPI_INVALID_MEMBER: GAPI_invalidMember,
  GAPI_MEMBER_NOT_FOUND: GAPI_memberNotFound,
  GAPI_NOT_FOUND: GAPI_notFound,
  GAPI_NOT_IMPLEMENTED: GAPI_notImplemented,
  GAPI_RESOURCE_NOT_FOUND: GAPI_resourceNotFound,
  GAPI_SERVICE_NOT_AVAILABLE: GAPI_serviceNotAvailable,
  GAPI_USER_NOT_FOUND: GAPI_userNotFound,
  }

def callGAPI(service, function,
             silent_errors=False, soft_errors=False, throw_reasons=None, retry_reasons=None,
             **kwargs):
  if throw_reasons is None:
    throw_reasons = []
  if retry_reasons is None:
    retry_reasons = []
  method = getattr(service, function)
  retries = 10
  parameters = dict(kwargs.items() + GM_Globals[GM_EXTRA_ARGS_DICT].items())
  for n in range(1, retries+1):
    try:
      return method(**parameters).execute()
    except googleapiclient.errors.HttpError as e:
      http_status, reason, message = checkGAPIError(e, soft_errors=soft_errors, silent_errors=silent_errors, retryOnHttpError=n < 3, service=service)
      if http_status == -1:
        continue
      if http_status == 0:
        return None
      if reason in throw_reasons:
        if reason in GAPI_REASON_EXCEPTION_MAP:
          raise GAPI_REASON_EXCEPTION_MAP[reason](message)
        raise e
      if (n != retries) and (reason in GAPI_DEFAULT_RETRY_REASONS+retry_reasons):
        waitOnFailure(n, retries, reason)
        continue
      if soft_errors:
        stderrErrorMsg(u'{0}: {1} - {2}{3}'.format(http_status, message, reason, [u'', u': Giving up.'][n > 1]))
        return None
      systemErrorExit(int(http_status), u'{0}: {1} - {2}'.format(http_status, message, reason))
    except oauth2client.client.AccessTokenRefreshError as e:
      handleOAuthTokenError(str(e), soft_errors or GAPI_SERVICE_NOT_AVAILABLE in throw_reasons)
      if GAPI_SERVICE_NOT_AVAILABLE in throw_reasons:
        raise GAPI_serviceNotAvailable(str(e))
      stderrErrorMsg(u'User {0}: {1}'.format(GM_Globals[GM_CURRENT_API_USER], str(e)))
      return None
    except httplib2.CertificateValidationUnsupported:
      noPythonSSLExit()
    except ValueError as e:
      if service._http.cache is not None:
        service._http.cache = None
        continue
      systemErrorExit(4, str(e))
    except TypeError as e:
      systemErrorExit(4, str(e))
    except httplib2.ServerNotFoundError as e:
      systemErrorExit(4, str(e))

def callGAPIpages(service, function, items,
                  page_message=None, message_attribute=None,
                  soft_errors=False, throw_reasons=None, retry_reasons=None,
                  **kwargs):
  if throw_reasons is None:
    throw_reasons = []
  all_pages = list()
  total_items = 0
  while True:
    this_page = callGAPI(service, function, soft_errors=soft_errors,
                         throw_reasons=throw_reasons, retry_reasons=retry_reasons, **kwargs)
    if this_page:
      if items in this_page:
        page_items = len(this_page[items])
        total_items += page_items
        all_pages.extend(this_page[items])
      else:
        this_page = {items: []}
        page_items = 0
    else:
      this_page = {items: []}
      page_items = 0
    if page_message:
      show_message = page_message.replace(u'%%num_items%%', str(page_items))
      show_message = show_message.replace(u'%%total_items%%', str(total_items))
      if message_attribute:
        try:
          show_message = show_message.replace(u'%%first_item%%', str(this_page[items][0][message_attribute]))
          show_message = show_message.replace(u'%%last_item%%', str(this_page[items][-1][message_attribute]))
        except (IndexError, KeyError):
          show_message = show_message.replace(u'%%first_item%%', u'')
          show_message = show_message.replace(u'%%last_item%%', u'')
      sys.stderr.write(u'\r')
      sys.stderr.flush()
      sys.stderr.write(show_message)
    if this_page and this_page.get(u'nextPageToken'):
      kwargs[u'pageToken'] = this_page[u'nextPageToken']
    else:
      if page_message and (page_message[-1] != u'\n'):
        sys.stderr.write(u'\r\n')
        sys.stderr.flush()
      return all_pages

def callGAPIitems(service, function, items,
                  throw_reasons=None, retry_reasons=None,
                  **kwargs):
  if throw_reasons is None:
    throw_reasons = []
  if retry_reasons is None:
    retry_reasons = []
  results = callGAPI(service, function,
                     throw_reasons=throw_reasons, retry_reasons=retry_reasons,
                     **kwargs)
  if results:
    return results.get(items, [])
  return []

def getAPIVersion(api):
  version = API_VER_MAPPING.get(api, u'v1')
  if api in [u'directory', u'reports', u'datatransfer']:
    api = u'admin'
  elif api == u'drive3':
    api = u'drive'
  return (api, version, u'{0}-{1}'.format(api, version))

def readDiscoveryFile(api_version):
  disc_filename = u'%s.json' % (api_version)
  disc_file = os.path.join(GM_Globals[GM_GAM_PATH], disc_filename)
  if hasattr(sys, u'_MEIPASS'):
    pyinstaller_disc_file = os.path.join(sys._MEIPASS, disc_filename)
  else:
    pyinstaller_disc_file = None
  if os.path.isfile(disc_file):
    json_string = readFile(disc_file)
  elif pyinstaller_disc_file:
    json_string = readFile(pyinstaller_disc_file)
  else:
    systemErrorExit(11, MESSAGE_NO_DISCOVERY_INFORMATION.format(disc_file))
  try:
    discovery = json.loads(json_string)
    return (disc_file, discovery)
  except ValueError:
    invalidJSONExit(disc_file)

def getOauth2TxtStorageCredentials():
  storage = oauth2client.file.Storage(GC_Values[GC_OAUTH2_TXT])
  try:
    return (storage, storage.get())
  except (KeyError, ValueError):
    return (storage, None)

def getValidOauth2TxtCredentials():
  """Gets OAuth2 credentials which are guaranteed to be fresh and valid."""
  storage, credentials = getOauth2TxtStorageCredentials()
  if credentials is None or credentials.invalid:
    doRequestOAuth()
    credentials = storage.get()
  elif credentials.access_token_expired:
    http = httplib2.Http(disable_ssl_certificate_validation=GC_Values[GC_NO_VERIFY_SSL])
    credentials.refresh(http)
  return credentials

def getService(api, http):
  api, version, api_version = getAPIVersion(api)
  retries = 3
  for n in range(1, retries+1):
    try:
      service = googleapiclient.discovery.build(api, version, http=http, cache_discovery=False)
      if GM_Globals[GM_CACHE_DISCOVERY_ONLY]:
        http.cache = None
      return service
    except httplib2.ServerNotFoundError as e:
      systemErrorExit(4, str(e))
    except httplib2.CertificateValidationUnsupported:
      noPythonSSLExit()
    except (googleapiclient.errors.InvalidJsonError, KeyError, ValueError) as e:
      http.cache = None
      if n != retries:
        waitOnFailure(n, retries, str(e))
        continue
      systemErrorExit(17, str(e))
    except (httplib.ResponseNotReady, httplib2.SSLHandshakeError, socket.error) as e:
      if n != retries:
        waitOnFailure(n, retries, str(e))
        continue
      systemErrorExit(3, str(e))
    except googleapiclient.errors.UnknownApiNameOrVersion:
      break
  disc_file, discovery = readDiscoveryFile(api_version)
  try:
    service = googleapiclient.discovery.build_from_document(discovery, http=http)
    if GM_Globals[GM_CACHE_DISCOVERY_ONLY]:
      http.cache = None
    return service
  except (KeyError, ValueError):
    invalidJSONExit(disc_file)

def buildGAPIObject(api):
  GM_Globals[GM_CURRENT_API_USER] = None
  credentials = getValidOauth2TxtCredentials()
  credentials.user_agent = GAM_INFO
  http = credentials.authorize(httplib2.Http(disable_ssl_certificate_validation=GC_Values[GC_NO_VERIFY_SSL],
                                             cache=GM_Globals[GM_CACHE_DIR]))
  service = getService(api, http)
  if GC_Values[GC_DOMAIN]:
    if not GC_Values[GC_CUSTOMER_ID]:
      resp, result = service._http.request(u'https://www.googleapis.com/admin/directory/v1/users?domain={0}&maxResults=1&fields=users(customerId)'.format(GC_Values[GC_DOMAIN]))
      try:
        resultObj = json.loads(result)
      except ValueError:
        systemErrorExit(8, u'Unexpected response: {0}'.format(result))
      if resp[u'status'] in [u'403', u'404']:
        try:
          message = resultObj[u'error'][u'errors'][0][u'message']
        except KeyError:
          message = resultObj[u'error'][u'message']
        systemErrorExit(8, u'{0} - {1}'.format(message, GC_Values[GC_DOMAIN]))
      try:
        GC_Values[GC_CUSTOMER_ID] = resultObj[u'users'][0][u'customerId']
      except KeyError:
        GC_Values[GC_CUSTOMER_ID] = MY_CUSTOMER
  else:
    GC_Values[GC_DOMAIN] = _getValueFromOAuth(u'hd', credentials=credentials)
    if not GC_Values[GC_CUSTOMER_ID]:
      GC_Values[GC_CUSTOMER_ID] = MY_CUSTOMER
  return service

# Convert UID to email address
def convertUIDtoEmailAddress(emailAddressOrUID, cd=None, email_type=u'user'):
  normalizedEmailAddressOrUID = normalizeEmailAddressOrUID(emailAddressOrUID)
  if normalizedEmailAddressOrUID.find(u'@') > 0:
    return normalizedEmailAddressOrUID
  if not cd:
    cd = buildGAPIObject(u'directory')
  if email_type == u'user':
    try:
      result = callGAPI(cd.users(), u'get',
                        throw_reasons=[GAPI_USER_NOT_FOUND],
                        userKey=normalizedEmailAddressOrUID, fields=u'primaryEmail')
      if u'primaryEmail' in result:
        return result[u'primaryEmail'].lower()
    except GAPI_userNotFound:
      pass
  else:
    try:
      result = callGAPI(cd.groups(), u'get',
                        throw_reasons=[GAPI_GROUP_NOT_FOUND],
                        groupKey=normalizedEmailAddressOrUID, fields=u'email')
      if u'email' in result:
        return result[u'email'].lower()
    except GAPI_groupNotFound:
      pass
  return normalizedEmailAddressOrUID

# Convert email address to UID
def convertEmailAddressToUID(emailAddressOrUID, cd=None, email_type=u'user'):
  normalizedEmailAddressOrUID = normalizeEmailAddressOrUID(emailAddressOrUID)
  if normalizedEmailAddressOrUID.find(u'@') > 0:
    if not cd:
      cd = buildGAPIObject(u'directory')
    if email_type != u'group':
      try:
        result = callGAPI(cd.users(), u'get',
                          throw_reasons=[GAPI_USER_NOT_FOUND],
                          userKey=normalizedEmailAddressOrUID, fields=u'id')
        if u'id' in result:
          return result[u'id']
      except GAPI_userNotFound:
        pass
    try:
      result = callGAPI(cd.groups(), u'get',
                        throw_reasons=[GAPI_NOT_FOUND],
                        groupKey=normalizedEmailAddressOrUID, fields=u'id')
      if u'id' in result:
        return result[u'id']
    except GAPI_notFound:
      pass
    return None
  return normalizedEmailAddressOrUID

def buildGAPIServiceObject(api, act_as, showAuthError=True):
  http = httplib2.Http(disable_ssl_certificate_validation=GC_Values[GC_NO_VERIFY_SSL],
                       cache=GM_Globals[GM_CACHE_DIR])
  service = getService(api, http)
  GM_Globals[GM_CURRENT_API_USER] = act_as
  GM_Globals[GM_CURRENT_API_SCOPES] = API_SCOPE_MAPPING[api]
  credentials = getSvcAcctCredentials(GM_Globals[GM_CURRENT_API_SCOPES], act_as)
  request = google_auth_httplib2.Request(http)
  try:
    credentials.refresh(request)
    service._http = google_auth_httplib2.AuthorizedHttp(credentials, http=http)
  except httplib2.ServerNotFoundError as e:
    systemErrorExit(4, e)
  except google.auth.exceptions.RefreshError as e:
    if showAuthError:
      stderrErrorMsg(u'User {0}: {1}'.format(GM_Globals[GM_CURRENT_API_USER], str(e[0])))
    return handleOAuthTokenError(str(e[0]), True)
  return service

def buildActivityGAPIObject(user):
  userEmail = convertUIDtoEmailAddress(user)
  return (userEmail, buildGAPIServiceObject(u'appsactivity', userEmail))

def normalizeCalendarId(calname, checkPrimary=False):
  calname = calname.lower()
  if checkPrimary and calname == u'primary':
    return calname
  if not GC_Values[GC_DOMAIN]:
    GC_Values[GC_DOMAIN] = _getValueFromOAuth(u'hd')
  return convertUIDtoEmailAddress(calname)

def buildCalendarGAPIObject(calname):
  calendarId = normalizeCalendarId(calname)
  return (calendarId, buildGAPIServiceObject(u'calendar', calendarId))

def buildCalendarDataGAPIObject(calname):
  calendarId = normalizeCalendarId(calname)
  # Force service account token request. If we fail fall back to using admin for authentication
  cal = buildGAPIServiceObject(u'calendar', calendarId, False)
  if cal is None:
    _, cal = buildCalendarGAPIObject(_getValueFromOAuth(u'email'))
  return (calendarId, cal)

def buildDriveGAPIObject(user):
  userEmail = convertUIDtoEmailAddress(user)
  return (userEmail, buildGAPIServiceObject(u'drive', userEmail))

def buildDrive3GAPIObject(user):
  userEmail = convertUIDtoEmailAddress(user)
  return (userEmail, buildGAPIServiceObject(u'drive3', userEmail))

def buildGmailGAPIObject(user):
  userEmail = convertUIDtoEmailAddress(user)
  return (userEmail, buildGAPIServiceObject(u'gmail', userEmail))

def buildGplusGAPIObject(user):
  userEmail = convertUIDtoEmailAddress(user)
  return (userEmail, buildGAPIServiceObject(u'plus', userEmail))

def doCheckServiceAccount(users):
  all_scopes = []
  for _, scopes in API_SCOPE_MAPPING.items():
    for scope in scopes:
      if scope not in all_scopes:
        all_scopes.append(scope)
  all_scopes.sort()
  for user in users:
    all_scopes_pass = True
    print u'User: %s' % (user)
    for scope in all_scopes:
      try:
        credentials = getSvcAcctCredentials([scope], user)
        request = google_auth_httplib2.Request(httplib2.Http(disable_ssl_certificate_validation=GC_Values[GC_NO_VERIFY_SSL]))
        credentials.refresh(request)
        result = u'PASS'
      except httplib2.ServerNotFoundError as e:
        systemErrorExit(4, e)
      except google.auth.exceptions.RefreshError:
        result = u'FAIL'
        all_scopes_pass = False
      print u' Scope: {0:60} {1}'.format(scope, result)
    service_account = GM_Globals[GM_OAUTH2SERVICE_ACCOUNT_CLIENT_ID]
    if all_scopes_pass:
      print u'\nAll scopes passed!\nService account %s is fully authorized.' % service_account
      return
    user_domain = user[user.find(u'@')+1:]
    scopes_failed = '''Some scopes failed! Please go to:

https://admin.google.com/%s/AdminHome?#OGX:ManageOauthClients

and grant Client name:

%s

Access to scopes:

%s\n''' % (user_domain, service_account, ',\n'.join(all_scopes))
    systemErrorExit(1, scopes_failed)

# Batch processing request_id fields
RI_ENTITY = 0
RI_J = 1
RI_JCOUNT = 2
RI_ITEM = 3
RI_ROLE = 4

def batchRequestID(entityName, j, jcount, item, role=u''):
  return u'{0}\n{1}\n{2}\n{3}\n{4}'.format(entityName, j, jcount, item, role)

def _adjustDate(errMsg):
  match_date = re.match(u'Data for dates later than (.*) is not yet available. Please check back later', errMsg)
  if not match_date:
    match_date = re.match(u'Start date can not be later than (.*)', errMsg)
  if not match_date:
    systemErrorExit(4, errMsg)
  return unicode(match_date.group(1))

def _checkFullDataAvailable(warnings, tryDate, fullDataRequired):
  for warning in warnings:
    if warning[u'code'] == u'PARTIAL_DATA_AVAILABLE':
      for app in warning[u'data']:
        if app[u'key'] == u'application' and app[u'value'] != u'docs' and (not fullDataRequired or app[u'value'] in fullDataRequired):
          tryDateTime = datetime.datetime.strptime(tryDate, YYYYMMDD_FORMAT)-datetime.timedelta(days=1)
          return (0, tryDateTime.strftime(YYYYMMDD_FORMAT))
    elif warning[u'code'] == u'DATA_NOT_AVAILABLE':
      for app in warning[u'data']:
        if app[u'key'] == u'application' and app[u'value'] != u'docs' and (not fullDataRequired or app[u'value'] in fullDataRequired):
          return (-1, tryDate)
  return (1, tryDate)

def showReport():
  rep = buildGAPIObject(u'reports')
  report = sys.argv[2].lower()
  customerId = GC_Values[GC_CUSTOMER_ID]
  if customerId == MY_CUSTOMER:
    customerId = None
  filters = parameters = actorIpAddress = startTime = endTime = eventName = None
  tryDate = datetime.date.today().strftime(YYYYMMDD_FORMAT)
  to_drive = False
  userKey = u'all'
  fullDataRequired = None
  i = 3
  while i < len(sys.argv):
    myarg = sys.argv[i].lower()
    if myarg == u'date':
      tryDate = getYYYYMMDD(sys.argv[i+1])
      i += 2
    elif myarg == u'fulldatarequired':
      fullDataRequired = []
      fdr = sys.argv[i+1].lower()
      if len(fdr) > 0 and fdr != u'all':
        fullDataRequired = fdr.replace(u',', u' ').split()
      i += 2
    elif myarg == u'start':
      startTime = getTimeOrDeltaFromNow(sys.argv[i+1])
      i += 2
    elif myarg == u'end':
      endTime = getTimeOrDeltaFromNow(sys.argv[i+1])
      i += 2
    elif myarg == u'event':
      eventName = sys.argv[i+1]
      i += 2
    elif myarg == u'user':
      userKey = normalizeEmailAddressOrUID(sys.argv[i+1])
      i += 2
    elif myarg in [u'filter', u'filters']:
      filters = sys.argv[i+1]
      i += 2
    elif myarg in [u'fields', u'parameters']:
      parameters = sys.argv[i+1]
      i += 2
    elif myarg == u'ip':
      actorIpAddress = sys.argv[i+1]
      i += 2
    elif myarg == u'todrive':
      to_drive = True
      i += 1
    else:
      systemErrorExit(2, u'%s is not a valid argument to "gam report"' % sys.argv[i])
  if report in [u'users', u'user']:
    while True:
      try:
        if fullDataRequired is not None:
          warnings = callGAPIitems(rep.userUsageReport(), u'get', u'warnings',
                                   throw_reasons=[GAPI_INVALID],
                                   date=tryDate, userKey=userKey, customerId=customerId, fields=u'warnings')
          fullData, tryDate = _checkFullDataAvailable(warnings, tryDate, fullDataRequired)
          if fullData < 0:
            print u'No user report available.'
            sys.exit(1)
          if fullData == 0:
            continue
        page_message = u'Got %%num_items%% users\n'
        usage = callGAPIpages(rep.userUsageReport(), u'get', u'usageReports', page_message=page_message, throw_reasons=[GAPI_INVALID],
                              date=tryDate, userKey=userKey, customerId=customerId, filters=filters, parameters=parameters)
        break
      except GAPI_invalid as e:
        tryDate = _adjustDate(str(e))
    if not usage:
      print u'No user report available.'
      sys.exit(1)
    titles = [u'email', u'date']
    csvRows = []
    for user_report in usage:
      if u'entity' not in user_report:
        continue
      row = {u'email': user_report[u'entity'][u'userEmail'], u'date': tryDate}
      try:
        for report_item in user_report[u'parameters']:
          items = report_item.values()
          if len(items) < 2:
            continue
          name = items[1]
          value = items[0]
          if not name in titles:
            titles.append(name)
          row[name] = value
      except KeyError:
        pass
      csvRows.append(row)
    writeCSVfile(csvRows, titles, u'User Reports - %s' % tryDate, to_drive)
  elif report in [u'customer', u'customers', u'domain']:
    while True:
      try:
        if fullDataRequired is not None:
          warnings = callGAPIitems(rep.customerUsageReports(), u'get', u'warnings',
                                   throw_reasons=[GAPI_INVALID],
                                   customerId=customerId, date=tryDate, fields=u'warnings')
          fullData, tryDate = _checkFullDataAvailable(warnings, tryDate, fullDataRequired)
          if fullData < 0:
            print u'No customer report available.'
            sys.exit(1)
          if fullData == 0:
            continue
        usage = callGAPIpages(rep.customerUsageReports(), u'get', u'usageReports', throw_reasons=[GAPI_INVALID],
                              customerId=customerId, date=tryDate, parameters=parameters)
        break
      except GAPI_invalid as e:
        tryDate = _adjustDate(str(e))
    if not usage:
      print u'No customer report available.'
      sys.exit(1)
    titles = [u'name', u'value', u'client_id']
    csvRows = []
    auth_apps = list()
    for item in usage[0][u'parameters']:
      if u'name' not in item:
        continue
      name = item[u'name']
      if u'intValue' in item:
        value = item[u'intValue']
      elif u'msgValue' in item:
        if name == u'accounts:authorized_apps':
          for subitem in item[u'msgValue']:
            app = {}
            for an_item in subitem:
              if an_item == u'client_name':
                app[u'name'] = u'App: %s' % subitem[an_item].replace(u'\n', u'\\n')
              elif an_item == u'num_users':
                app[u'value'] = u'%s users' % subitem[an_item]
              elif an_item == u'client_id':
                app[u'client_id'] = subitem[an_item]
            auth_apps.append(app)
          continue
        else:
          values = []
          for subitem in item[u'msgValue']:
            if u'count' in subitem:
              mycount = myvalue = None
              for key, value in subitem.items():
                if key == u'count':
                  mycount = value
                else:
                  myvalue = value
                if mycount and myvalue:
                  values.append(u'%s:%s' % (myvalue, mycount))
              value = u' '.join(values)
            elif u'version_number' in subitem and u'num_devices' in subitem:
              values.append(u'%s:%s' % (subitem[u'version_number'], subitem[u'num_devices']))
            else:
              continue
            value = u' '.join(sorted(values, reverse=True))
      csvRows.append({u'name': name, u'value': value})
    for app in auth_apps: # put apps at bottom
      csvRows.append(app)
    writeCSVfile(csvRows, titles, u'Customer Report - %s' % tryDate, todrive=to_drive)
  else:
    if report in [u'doc', u'docs']:
      report = u'drive'
    elif report in [u'calendars']:
      report = u'calendar'
    elif report == u'logins':
      report = u'login'
    elif report == u'tokens':
      report = u'token'
    elif report == u'group':
      report = u'groups'
    page_message = u'Got %%num_items%% items\n'
    activities = callGAPIpages(rep.activities(), u'list', u'items', page_message=page_message, applicationName=report,
                               userKey=userKey, customerId=customerId, actorIpAddress=actorIpAddress,
                               startTime=startTime, endTime=endTime, eventName=eventName, filters=filters)
    if len(activities) > 0:
      titles = [u'name']
      csvRows = []
      for activity in activities:
        events = activity[u'events']
        del activity[u'events']
        activity_row = flatten_json(activity)
        for event in events:
          for item in event.get(u'parameters', []):
            if item[u'name'] in [u'start_time', u'end_time']:
              val = item.get(u'intValue')
              if val is not None:
                item[u'dateTimeValue'] = datetime.datetime.fromtimestamp(int(val)-62135683200).isoformat()
                item.pop(u'intValue')
          row = flatten_json(event)
          row.update(activity_row)
          for item in row:
            if item not in titles:
              titles.append(item)
          csvRows.append(row)
      sortCSVTitles([u'name',], titles)
      writeCSVfile(csvRows, titles, u'%s Activity Report' % report.capitalize(), to_drive)

def watchGmail(users):
  cs_data = readFile(GC_Values[GC_CLIENT_SECRETS_JSON], mode=u'rb', continueOnError=True, displayError=True, encoding=None)
  cs_json = json.loads(cs_data)
  project = u'projects/{0}'.format(cs_json[u'installed'][u'project_id'])
  gamTopics = project+u'/topics/gam-pubsub-gmail-'
  gamSubscriptions = project+u'/subscriptions/gam-pubsub-gmail-'
  pubsub = buildGAPIObject(u'pubsub')
  topics = callGAPIpages(pubsub.projects().topics(), u'list', items=u'topics', project=project)
  for atopic in topics:
    if atopic[u'name'].startswith(gamTopics):
      topic = atopic[u'name']
      break
  else:
    topic = gamTopics+uuid.uuid4()
    callGAPI(pubsub.projects().topics(), u'create', name=topic, body={})
    body = {u'policy': {u'bindings': [{u'members': [u'serviceAccount:gmail-api-push@system.gserviceaccount.com'], u'role': u'roles/pubsub.editor'}]}}
    callGAPI(pubsub.projects().topics(), u'setIamPolicy', resource=topic, body=body)
  subscriptions = callGAPIpages(pubsub.projects().topics().subscriptions(), u'list', items=u'subscriptions', topic=topic)
  for asubscription in subscriptions:
    if asubscription.startswith(gamSubscriptions):
      subscription = asubscription
      break
  else:
    subscription = gamSubscriptions+uuid.uuid4()
    callGAPI(pubsub.projects().subscriptions(), u'create', name=subscription, body={u'topic': topic})
  gmails = {}
  for user in users:
    gmails[user] = {u'g': buildGmailGAPIObject(user)[1]}
    callGAPI(gmails[user][u'g'].users(), u'watch', userId=u'me', body={u'topicName': topic})
    gmails[user]['seen_historyId'] = callGAPI(gmails[user][u'g'].users(), u'getProfile', userId=u'me', fields=u'historyId')[u'historyId']
  print 'Watching for events...'
  while True:
    results = callGAPI(pubsub.projects().subscriptions(), u'pull', subscription=subscription, body={u'maxMessages': 100})
    if u'receivedMessages' in results:
      ackIds = []
      update_history = []
      for message in results[u'receivedMessages']:
        if u'data' in message[u'message']:
          decoded_message = json.loads(base64.b64decode(message[u'message'][u'data']))
          if u'historyId' in decoded_message:
            update_history.append(decoded_message[u'emailAddress'])
        if u'ackId' in message:
          ackIds.append(message[u'ackId'])
      if ackIds:
        callGAPI(pubsub.projects().subscriptions(), u'acknowledge', subscription=subscription, body={u'ackIds': ackIds})
      if update_history:
        for a_user in update_history:
          results = callGAPI(gmails[a_user][u'g'].users().history(), u'list', userId=u'me', startHistoryId=gmails[a_user][u'seen_historyId'])
          if u'history' in results:
            for history in results[u'history']:
              if history.keys() == [u'messages', u'id']:
                continue
              if u'labelsAdded' in history:
                for labelling in history[u'labelsAdded']:
                  print u'%s labels %s added to %s' % (a_user, u', '.join(labelling[u'labelIds']), labelling[u'message'][u'id'])
              if u'labelsRemoved' in history:
                for labelling in history[u'labelsRemoved']:
                  print u'%s labels %s removed from %s' % (a_user, u', '.join(labelling[u'labelIds']), labelling[u'message'][u'id'])
              if u'messagesDeleted' in history:
                for deleting in history[u'messagesDeleted']:
                  print u'%s permanently deleted message %s' % (a_user, deleting[u'message'][u'id'])
              if u'messagesAdded' in history:
                for adding in history[u'messagesAdded']:
                  print u'%s created message %s with labels %s' % (a_user, adding[u'message'][u'id'], u', '.join(adding[u'message'][u'labelIds']))
          gmails[a_user][u'seen_historyId'] = results[u'historyId']

def addDelegates(users, i):
  if i == 4:
    if sys.argv[i].lower() != u'to':
      systemErrorExit(2, u'%s is not a valid argument for "gam <users> delegate", expected to' % sys.argv[i])
    i += 1
  delegate = sys.argv[i].lower()
  atLoc = delegate.find(u'@')
  if atLoc == -1:
    delegate_domain = GC_Values[GC_DOMAIN].lower()
    delegate_email = u'%s@%s' % (delegate, delegate_domain)
  else:
    delegate_domain = delegate[atLoc+1:].lower()
    delegate_email = delegate
  i = 0
  count = len(users)
  emailsettings = buildGAPIObject(u'email-settings')
  for delegator in users:
    i += 1
    atLocd = delegator.find(u'@')
    if atLocd == -1:
      delegator_domain = GC_Values[GC_DOMAIN].lower()
      delegator_email = u'%s@%s' % (delegator, delegator_domain)
    else:
      delegator_domain = delegator[atLocd+1:].lower()
      delegator_email = delegator
      delegator = delegator[:atLocd]
    uri = u'https://apps-apis.google.com/a/feeds/emailsettings/2.0/%s/%s/delegation' % (delegator_domain, delegator)
    body = u'''<?xml version="1.0" encoding="utf-8"?>
<atom:entry xmlns:atom="http://www.w3.org/2005/Atom" xmlns:apps="http://schemas.google.com/apps/2006">
<apps:property name="address" value="%s" />
</atom:entry>''' % delegate_email
    headers = {u'GData-Version': u'2.0', u'Content-Type': u'application/atom+xml; charset=UTF-8'}
    print u"Giving %s delegate access to %s (%s/%s)" % (delegate_email, delegator_email, i, count)
    retries = 10
    for n in range(1, retries+1):
      status, result = emailsettings._http.request(uri=uri, method=u'POST', body=body, headers=headers)
      httpStatus = int(status[u'status'])
      if httpStatus == 201: # Success
        time.sleep(10) # on success, sleep 10 seconds before exiting or moving on to next user to prevent ghost delegates
        break
      elif httpStatus > 499:
        waitOnFailure(n, retries, str(httpStatus))
      else:
        systemErrorExit(3, u'Could not create delegation - %s - %s' % (httpStatus, result))

def gen_sha512_hash(password):
  from passlib.handlers.sha2_crypt import sha512_crypt
  return sha512_crypt.encrypt(password, rounds=5000)

def printShowDelegates(users, csvFormat):
  emailsettings = buildGAPIObject(u'email-settings')
  if csvFormat:
    todrive = False
    csvRows = []
    titles = [u'User', u'delegateName', u'delegateAddress', u'delegationStatus']
  else:
    csvStyle = False
  i = 5
  while i < len(sys.argv):
    myarg = sys.argv[i].lower()
    if not csvFormat and myarg == u'csv':
      csvStyle = True
      i += 1
    elif csvFormat and myarg == u'todrive':
      todrive = True
      i += 1
    else:
      systemErrorExit(2, u'%s is not a valid argument for "gam <users> show delegates"' % sys.argv[i])
  for user in users:
    atLoc = user.find(u'@')
    if atLoc == -1:
      userName = user
      domainName = GC_Values[GC_DOMAIN]
      user = u'%s@%s' % (user, domainName)
    else:
      userName = user[:atLoc]
      domainName = user[atLoc+1:]
    sys.stderr.write(u"Getting delegates for %s...\n" % (user))
    delegates = callGAPI(emailsettings.delegates(), u'get', soft_errors=True, v=u'2.0', domainName=domainName, delegator=userName)
    if delegates and u'feed' in delegates and u'entry' in delegates[u'feed']:
      for delegate in delegates[u'feed']['entry']:
        status = u''
        delegateAddress = u''
        delegateName = u''
        delegationId = u''
        for item in delegate[u'apps$property']:
          if item[u'name'] == u'status':
            status = item[u'value']
          elif item[u'name'] == u'address':
            delegateAddress = item[u'value']
          elif item[u'name'] == u'delegate':
            delegateName = item[u'value']
          elif item[u'name'] == u'delegationId':
            delegationId = item[u'value']
        if csvFormat:
          row = {u'User': user, u'delegateName': delegateName, u'delegateAddress': delegateAddress, u'delegationStatus': status}
          csvRows.append(row)
        else:
          if csvStyle:
            print u'%s,%s,%s' % (user, delegateAddress, status)
          else:
            print utils.convertUTF8(u"Delegator: %s\n Delegate: %s\n Status: %s\n Delegate Email: %s\n Delegate ID: %s\n" % (user, delegateName, status, delegateAddress, delegationId))
  if csvFormat:
    writeCSVfile(csvRows, titles, u'Delegates', todrive)

def deleteDelegate(users):
  emailsettings = buildGAPIObject(u'email-settings')
  delegate = sys.argv[5]
  if not delegate.find(u'@') > 0:
    if users[0].find(u'@') > 0:
      delegatedomain = users[0][users[0].find(u'@')+1:]
    else:
      delegatedomain = GC_Values[GC_DOMAIN]
    delegate = u'%s@%s' % (delegate, delegatedomain)
  i = 0
  count = len(users)
  for user in users:
    i += 1
    atLoc = user.find(u'@')
    if atLoc == -1:
      domainName = GC_Values[GC_DOMAIN] #make sure it's back at default domain
    else:
      domainName = user[atLoc+1:]
      user = user[:atLoc]
    print u"Deleting %s delegate access to %s (%s/%s)" % (delegate, user+u'@'+domainName, i, count)
    callGAPI(emailsettings.delegates(), u'delete', v=u'2.0', delegate=delegate, delegator=user, domainName=domainName)

def doAddCourseParticipant():
  croom = buildGAPIObject(u'classroom')
  courseId = addCourseIdScope(sys.argv[2])
  noScopeCourseId = removeCourseIdScope(courseId)
  participant_type = sys.argv[4].lower()
  new_id = sys.argv[5]
  if participant_type in [u'student', u'students']:
    new_id = normalizeEmailAddressOrUID(new_id)
    callGAPI(croom.courses().students(), u'create', courseId=courseId, body={u'userId': new_id})
    print u'Added %s as a student of course %s' % (new_id, noScopeCourseId)
  elif participant_type in [u'teacher', u'teachers']:
    new_id = normalizeEmailAddressOrUID(new_id)
    callGAPI(croom.courses().teachers(), u'create', courseId=courseId, body={u'userId': new_id})
    print u'Added %s as a teacher of course %s' % (new_id, noScopeCourseId)
  elif participant_type in [u'alias']:
    new_id = addCourseIdScope(new_id)
    callGAPI(croom.courses().aliases(), u'create', courseId=courseId, body={u'alias': new_id})
    print u'Added %s as an alias of course %s' % (removeCourseIdScope(new_id), noScopeCourseId)
  else:
    systemErrorExit(2, u'%s is not a valid argument to "gam course ID add"' % participant_type)

def doSyncCourseParticipants():
  courseId = addCourseIdScope(sys.argv[2])
  participant_type = sys.argv[4].lower()
  diff_entity_type = sys.argv[5]
  diff_entity = sys.argv[6]
  current_course_users = getUsersToModify(entity_type=participant_type, entity=courseId)
  print
  current_course_users = [x.lower() for x in current_course_users]
  if diff_entity_type == u'courseparticipants':
    diff_entity_type = participant_type
  diff_against_users = getUsersToModify(entity_type=diff_entity_type, entity=diff_entity)
  print
  diff_against_users = [x.lower() for x in diff_against_users]
  to_add = list(set(diff_against_users) - set(current_course_users))
  to_remove = list(set(current_course_users) - set(diff_against_users))
  gam_commands = []
  for add_email in to_add:
    gam_commands.append([u'gam', u'course', courseId, u'add', participant_type, add_email])
  for remove_email in to_remove:
    gam_commands.append([u'gam', u'course', courseId, u'remove', participant_type, remove_email])
  run_batch(gam_commands)

def doDelCourseParticipant():
  croom = buildGAPIObject(u'classroom')
  courseId = addCourseIdScope(sys.argv[2])
  noScopeCourseId = removeCourseIdScope(courseId)
  participant_type = sys.argv[4].lower()
  remove_id = sys.argv[5]
  if participant_type in [u'student', u'students']:
    remove_id = normalizeEmailAddressOrUID(remove_id)
    callGAPI(croom.courses().students(), u'delete', courseId=courseId, userId=remove_id)
    print u'Removed %s as a student of course %s' % (remove_id, noScopeCourseId)
  elif participant_type in [u'teacher', u'teachers']:
    remove_id = normalizeEmailAddressOrUID(remove_id)
    callGAPI(croom.courses().teachers(), u'delete', courseId=courseId, userId=remove_id)
    print u'Removed %s as a teacher of course %s' % (remove_id, noScopeCourseId)
  elif participant_type in [u'alias']:
    remove_id = addCourseIdScope(remove_id)
    callGAPI(croom.courses().aliases(), u'delete', courseId=courseId, alias=remove_id)
    print u'Removed %s as an alias of course %s' % (removeCourseIdScope(remove_id), noScopeCourseId)
  else:
    systemErrorExit(2, u'%s is not a valid argument to "gam course ID delete"' % participant_type)

def doDelCourse():
  croom = buildGAPIObject(u'classroom')
  courseId = addCourseIdScope(sys.argv[3])
  callGAPI(croom.courses(), u'delete', id=courseId)
  print u'Deleted Course %s' % courseId

def _getValidCourseStates(croom):
  return [state for state in croom._rootDesc[u'schemas'][u'Course'][u'properties'][u'courseState'][u'enum'] if state != u'COURSE_STATE_UNSPECIFIED']

def _getValidatedState(state, validStates):
  state = state.upper()
  if state not in validStates:
    systemErrorExit(2, u'course state must be one of: %s. Got %s' % (u', '.join(validStates).lower(), state.lower()))
  return state

def getCourseAttribute(myarg, value, body, croom, function):
  if myarg == u'name':
    body[u'name'] = value
  elif myarg == u'section':
    body[u'section'] = value
  elif myarg == u'heading':
    body[u'descriptionHeading'] = value
  elif myarg == u'description':
    body[u'description'] = value.replace(u'\\n', u'\n')
  elif myarg == u'room':
    body[u'room'] = value
  elif myarg in [u'owner', u'ownerid', u'teacher']:
    body[u'ownerId'] = normalizeEmailAddressOrUID(value)
  elif myarg in [u'state', u'status']:
    validStates = _getValidCourseStates(croom)
    body[u'courseState'] = _getValidatedState(value, validStates)
  else:
    systemErrorExit(2, '%s is not a valid argument to "gam %s course"' % (myarg, function))

def _getCourseStates(croom, value, courseStates):
  validStates = _getValidCourseStates(croom)
  for state in value.replace(u',', u' ').split():
    courseStates.append(_getValidatedState(state, validStates))

def doUpdateCourse():
  croom = buildGAPIObject(u'classroom')
  courseId = addCourseIdScope(sys.argv[3])
  body = {}
  i = 4
  while i < len(sys.argv):
    myarg = sys.argv[i].lower()
    getCourseAttribute(myarg, sys.argv[i+1], body, croom, u'update')
    i += 2
  updateMask = u','.join(body.keys())
  body[u'id'] = courseId
  result = callGAPI(croom.courses(), u'patch', id=courseId, body=body, updateMask=updateMask)
  print u'Updated Course %s' % result[u'id']

def doCreateDomain():
  cd = buildGAPIObject(u'directory')
  domain_name = sys.argv[3]
  body = {u'domainName': domain_name}
  callGAPI(cd.domains(), u'insert', customer=GC_Values[GC_CUSTOMER_ID], body=body)
  print u'Added domain %s' % domain_name

def doCreateDomainAlias():
  cd = buildGAPIObject(u'directory')
  body = {}
  body[u'domainAliasName'] = sys.argv[3]
  body[u'parentDomainName'] = sys.argv[4]
  callGAPI(cd.domainAliases(), u'insert', customer=GC_Values[GC_CUSTOMER_ID], body=body)

def doUpdateDomain():
  cd = buildGAPIObject(u'directory')
  domain_name = sys.argv[3]
  i = 4
  body = {}
  while i < len(sys.argv):
    myarg = sys.argv[i].lower()
    if myarg == u'primary':
      body[u'customerDomain'] = domain_name
      i += 1
    else:
      systemErrorExit(2, '%s is not a valid argument for "gam update domain"' % sys.argv[i])
  callGAPI(cd.customers(), u'update', customerKey=GC_Values[GC_CUSTOMER_ID], body=body)
  print u'%s is now the primary domain.' % domain_name

def doGetDomainInfo():
  if (len(sys.argv) < 4) or (sys.argv[3] == u'logo'):
    doGetCustomerInfo()
    return
  cd = buildGAPIObject(u'directory')
  domainName = sys.argv[3]
  result = callGAPI(cd.domains(), u'get', customer=GC_Values[GC_CUSTOMER_ID], domainName=domainName)
  if u'creationTime' in result:
    result[u'creationTime'] = unicode(datetime.datetime.fromtimestamp(int(result[u'creationTime'])/1000))
  if u'domainAliases' in result:
    for i in range(0, len(result[u'domainAliases'])):
      if u'creationTime' in result[u'domainAliases'][i]:
        result[u'domainAliases'][i][u'creationTime'] = unicode(datetime.datetime.fromtimestamp(int(result[u'domainAliases'][i][u'creationTime'])/1000))
  print_json(None, result)

def doGetDomainAliasInfo():
  cd = buildGAPIObject(u'directory')
  alias = sys.argv[3]
  result = callGAPI(cd.domainAliases(), u'get', customer=GC_Values[GC_CUSTOMER_ID], domainAliasName=alias)
  if u'creationTime' in result:
    result[u'creationTime'] = unicode(datetime.datetime.fromtimestamp(int(result[u'creationTime'])/1000))
  print_json(None, result)

def doGetCustomerInfo():
  cd = buildGAPIObject(u'directory')
  customer_info = callGAPI(cd.customers(), u'get', customerKey=GC_Values[GC_CUSTOMER_ID])
  print u'Customer ID: %s' % customer_info[u'id']
  print u'Primary Domain: %s' % customer_info[u'customerDomain']
  result = callGAPI(cd.domains(), u'get',
                    customer=customer_info[u'id'], domainName=customer_info[u'customerDomain'], fields=u'verified')
  print u'Primary Domain Verified: %s' % result[u'verified']
  print u'Customer Creation Time: %s' % customer_info[u'customerCreationTime']
  print u'Default Language: %s' % customer_info[u'language']
  if u'postalAddress' in customer_info:
    print u'Address:'
    for field in ADDRESS_FIELDS_PRINT_ORDER:
      if field in customer_info[u'postalAddress']:
        print u' %s: %s' % (field, customer_info[u'postalAddress'][field])
  if u'phoneNumber' in customer_info:
    print u'Phone: %s' % customer_info[u'phoneNumber']
  print u'Admin Secondary Email: %s' % customer_info[u'alternateEmail']
  user_counts_map = {
    u'accounts:num_users': u'Total Users',
    u'accounts:gsuite_basic_total_licenses': u'G Suite Basic Licenses',
    u'accounts:gsuite_basic_used_licenses': u'G Suite Basic Users',
    u'accounts:gsuite_enterprise_total_licenses': u'G Suite Enterprise Licenses',
    u'accounts:gsuite_enterprise_used_licenses': u'G Suite Enterprise Users',
    u'accounts:gsuite_unlimited_total_licenses': u'G Suite Business Licenses',
    u'accounts:gsuite_unlimited_used_licenses': u'G Suite Business Users'
    }
  parameters = u','.join(user_counts_map.keys())
  tryDate = datetime.date.today().strftime(YYYYMMDD_FORMAT)
  customerId = GC_Values[GC_CUSTOMER_ID]
  if customerId == MY_CUSTOMER:
    customerId = None
  rep = buildGAPIObject(u'reports')
  while True:
    try:
      usage = callGAPIpages(rep.customerUsageReports(), u'get', u'usageReports', throw_reasons=[GAPI_INVALID],
                            customerId=customerId, date=tryDate, parameters=parameters)
      break
    except GAPI_invalid as e:
      tryDate = _adjustDate(str(e))
  if not usage:
    print u'No user count data available.'
    return
  print u'User counts as of %s:' % tryDate
  for item in usage[0][u'parameters']:
    api_name = user_counts_map.get(item[u'name'])
    api_value = int(item.get(u'intValue', 0))
    if api_name and api_value:
      print u'  {}: {:,}'.format(api_name, api_value)

def doUpdateCustomer():
  cd = buildGAPIObject(u'directory')
  body = {}
  i = 3
  while i < len(sys.argv):
    myarg = sys.argv[i].lower().replace(u'_', u'')
    if myarg in ADDRESS_FIELDS_ARGUMENT_MAP:
      body.setdefault(u'postalAddress', {})
      body[u'postalAddress'][ADDRESS_FIELDS_ARGUMENT_MAP[myarg]] = sys.argv[i+1]
      i += 2
    elif myarg in [u'adminsecondaryemail', u'alternateemail']:
      body[u'alternateEmail'] = sys.argv[i+1]
      i += 2
    elif myarg in [u'phone', u'phonenumber']:
      body[u'phoneNumber'] = sys.argv[i+1]
      i += 2
    elif myarg == u'language':
      body[u'language'] = sys.argv[i+1]
      i += 2
    else:
      systemErrorExit(2, '%s is not a valid argument for "gam update customer"' % myarg)
  if not body:
    systemErrorExit(2, 'no arguments specified for "gam update customer"')
  callGAPI(cd.customers(), u'update', customerKey=GC_Values[GC_CUSTOMER_ID], body=body)
  print u'Updated customer'

def doDelDomain():
  cd = buildGAPIObject(u'directory')
  domainName = sys.argv[3]
  callGAPI(cd.domains(), u'delete', customer=GC_Values[GC_CUSTOMER_ID], domainName=domainName)

def doDelDomainAlias():
  cd = buildGAPIObject(u'directory')
  domainAliasName = sys.argv[3]
  callGAPI(cd.domainAliases(), u'delete', customer=GC_Values[GC_CUSTOMER_ID], domainAliasName=domainAliasName)

def doPrintDomains():
  cd = buildGAPIObject(u'directory')
  todrive = False
  titles = [u'domainName',]
  csvRows = []
  i = 3
  while i < len(sys.argv):
    myarg = sys.argv[i].lower()
    if myarg == u'todrive':
      todrive = True
      i += 1
    else:
      systemErrorExit(2, '%s is not a valid argument for "gam print domains".' % sys.argv[i])
  results = callGAPI(cd.domains(), u'list', customer=GC_Values[GC_CUSTOMER_ID])
  for domain in results[u'domains']:
    domain_attributes = {}
    domain[u'type'] = [u'secondary', u'primary'][domain[u'isPrimary']]
    for attr in domain:
      if attr in [u'kind', u'etag', u'domainAliases', u'isPrimary']:
        continue
      if attr in [u'creationTime',]:
        domain[attr] = unicode(datetime.datetime.fromtimestamp(int(domain[attr])/1000))
      if attr not in titles:
        titles.append(attr)
      domain_attributes[attr] = domain[attr]
    csvRows.append(domain_attributes)
    if u'domainAliases' in domain:
      for aliasdomain in domain[u'domainAliases']:
        aliasdomain[u'domainName'] = aliasdomain[u'domainAliasName']
        del aliasdomain[u'domainAliasName']
        aliasdomain[u'type'] = u'alias'
        aliasdomain_attributes = {}
        for attr in aliasdomain:
          if attr in [u'kind', u'etag']:
            continue
          if attr in [u'creationTime',]:
            aliasdomain[attr] = unicode(datetime.datetime.fromtimestamp(int(aliasdomain[attr])/1000))
          if attr not in titles:
            titles.append(attr)
          aliasdomain_attributes[attr] = aliasdomain[attr]
        csvRows.append(aliasdomain_attributes)
  writeCSVfile(csvRows, titles, u'Domains', todrive)

def doPrintDomainAliases():
  cd = buildGAPIObject(u'directory')
  todrive = False
  titles = [u'domainAliasName',]
  csvRows = []
  i = 3
  while i < len(sys.argv):
    myarg = sys.argv[i].lower()
    if myarg == u'todrive':
      todrive = True
      i += 1
    else:
      systemErrorExit(2, '%s is not a valid argument for "gam print domainaliases".' % sys.argv[i])
  results = callGAPI(cd.domainAliases(), u'list', customer=GC_Values[GC_CUSTOMER_ID])
  for domainAlias in results[u'domainAliases']:
    domainAlias_attributes = {}
    for attr in domainAlias:
      if attr in [u'kind', u'etag']:
        continue
      if attr == u'creationTime':
        domainAlias[attr] = unicode(datetime.datetime.fromtimestamp(int(domainAlias[attr])/1000))
      if attr not in titles:
        titles.append(attr)
      domainAlias_attributes[attr] = domainAlias[attr]
    csvRows.append(domainAlias_attributes)
  writeCSVfile(csvRows, titles, u'Domains', todrive)

def doDelAdmin():
  cd = buildGAPIObject(u'directory')
  roleAssignmentId = sys.argv[3]
  print u'Deleting Admin Role Assignment %s' % roleAssignmentId
  callGAPI(cd.roleAssignments(), u'delete',
           customer=GC_Values[GC_CUSTOMER_ID], roleAssignmentId=roleAssignmentId)

def doCreateAdmin():
  cd = buildGAPIObject(u'directory')
  user = normalizeEmailAddressOrUID(sys.argv[3])
  body = {u'assignedTo': convertEmailAddressToUID(user, cd)}
  role = sys.argv[4]
  if role[:4].lower() == u'uid:':
    body[u'roleId'] = role[4:]
  else:
    body[u'roleId'] = roleid_from_role(role)
  if not body[u'roleId']:
    systemErrorExit(4, '%s is not a valid role. Please ensure role name is exactly as shown in admin console.' % role)
  body[u'scopeType'] = sys.argv[5].upper()
  if body[u'scopeType'] not in [u'CUSTOMER', u'ORG_UNIT']:
    systemErrorExit(3, 'scope type must be customer or org_unit; got %s' % body[u'scopeType'])
  if body[u'scopeType'] == u'ORG_UNIT':
    orgUnit = sys.argv[6]
    if orgUnit[:3] == u'id:':
      body[u'orgUnitId'] = orgUnit[3:]
    elif orgUnit[:4] == u'uid:':
      body[u'orgUnitId'] = orgUnit[4:]
    else:
      if orgUnit[0] == u'/':
        orgUnit = orgUnit[1:]
      body[u'orgUnitId'] = callGAPI(cd.orgunits(), u'get',
                                    customerId=GC_Values[GC_CUSTOMER_ID], orgUnitPath=orgUnit,
                                    fields=u'orgUnitId')[u'orgUnitId'][3:]
  if body[u'scopeType'] == u'CUSTOMER':
    scope = u'customer'
  else:
    scope = orgUnit
  print u'Giving %s admin role %s for %s' % (user, role, scope)
  callGAPI(cd.roleAssignments(), u'insert',
           customer=GC_Values[GC_CUSTOMER_ID], body=body)

def doPrintAdminRoles():
  cd = buildGAPIObject(u'directory')
  todrive = False
  titles = [u'roleId', u'roleName', u'roleDescription', u'isSuperAdminRole', u'isSystemRole']
  fields = u'nextPageToken,items({0})'.format(u','.join(titles))
  csvRows = []
  i = 3
  while i < len(sys.argv):
    myarg = sys.argv[i].lower()
    if myarg == u'todrive':
      todrive = True
      i += 1
    else:
      systemErrorExit(2, '%s is not a valid argument for "gam print adminroles".' % sys.argv[i])
  roles = callGAPIpages(cd.roles(), u'list', u'items',
                        customer=GC_Values[GC_CUSTOMER_ID], fields=fields)
  for role in roles:
    role_attrib = {}
    for key, value in role.items():
      role_attrib[key] = value
    csvRows.append(role_attrib)
  writeCSVfile(csvRows, titles, u'Admin Roles', todrive)

def doPrintAdmins():
  cd = buildGAPIObject(u'directory')
  roleId = None
  userKey = None
  todrive = False
  fields = u'nextPageToken,items({0})'.format(u','.join([u'roleAssignmentId', u'roleId', u'assignedTo', u'scopeType', u'orgUnitId']))
  titles = [u'roleAssignmentId', u'roleId', u'role', u'assignedTo', u'assignedToUser', u'scopeType', u'orgUnitId', u'orgUnit']
  csvRows = []
  i = 3
  while i < len(sys.argv):
    myarg = sys.argv[i].lower()
    if myarg == u'user':
      userKey = normalizeEmailAddressOrUID(sys.argv[i+1])
      i += 2
    elif myarg == u'role':
      role = sys.argv[i+1]
      if role[:4].lower() == u'uid:':
        roleId = role[4:]
      else:
        roleId = roleid_from_role(role)
        if not roleId:
          systemErrorExit(5, '%s is not a valid role' % role)
      i += 2
    elif myarg == u'todrive':
      todrive = True
      i += 1
    else:
      systemErrorExit(2, '%s is not a valid argument for "gam print admins".' % sys.argv[i])
  admins = callGAPIpages(cd.roleAssignments(), u'list', u'items',
                         customer=GC_Values[GC_CUSTOMER_ID], userKey=userKey, roleId=roleId, fields=fields)
  for admin in admins:
    admin_attrib = {}
    for key, value in admin.items():
      if key == u'assignedTo':
        admin_attrib[u'assignedToUser'] = user_from_userid(value)
      elif key == u'roleId':
        admin_attrib[u'role'] = role_from_roleid(value)
      elif key == u'orgUnitId':
        value = u'id:{0}'.format(value)
        admin_attrib[u'orgUnit'] = orgunit_from_orgunitid(value)
      admin_attrib[key] = value
    csvRows.append(admin_attrib)
  writeCSVfile(csvRows, titles, u'Admins', todrive)

def buildOrgUnitIdToNameMap():
  cd = buildGAPIObject(u'directory')
  result = callGAPI(cd.orgunits(), u'list',
                    customerId=GC_Values[GC_CUSTOMER_ID],
                    fields=u'organizationUnits(orgUnitPath,orgUnitId)', type=u'all')
  GM_Globals[GM_MAP_ORGUNIT_ID_TO_NAME] = {}
  for orgUnit in result[u'organizationUnits']:
    GM_Globals[GM_MAP_ORGUNIT_ID_TO_NAME][orgUnit[u'orgUnitId']] = orgUnit[u'orgUnitPath']

def orgunit_from_orgunitid(orgunitid):
  if not GM_Globals[GM_MAP_ORGUNIT_ID_TO_NAME]:
    buildOrgUnitIdToNameMap()
  return GM_Globals[GM_MAP_ORGUNIT_ID_TO_NAME].get(orgunitid, orgunitid)

def buildRoleIdToNameToIdMap():
  cd = buildGAPIObject(u'directory')
  result = callGAPIpages(cd.roles(), u'list', u'items',
                         customer=GC_Values[GC_CUSTOMER_ID],
                         fields=u'nextPageToken,items(roleId,roleName)',
                         maxResults=100)
  GM_Globals[GM_MAP_ROLE_ID_TO_NAME] = {}
  GM_Globals[GM_MAP_ROLE_NAME_TO_ID] = {}
  for role in result:
    GM_Globals[GM_MAP_ROLE_ID_TO_NAME][role[u'roleId']] = role[u'roleName']
    GM_Globals[GM_MAP_ROLE_NAME_TO_ID][role[u'roleName']] = role[u'roleId']

def role_from_roleid(roleid):
  if not GM_Globals[GM_MAP_ROLE_ID_TO_NAME]:
    buildRoleIdToNameToIdMap()
  return GM_Globals[GM_MAP_ROLE_ID_TO_NAME].get(roleid, roleid)

def roleid_from_role(role):
  if not GM_Globals[GM_MAP_ROLE_NAME_TO_ID]:
    buildRoleIdToNameToIdMap()
  return GM_Globals[GM_MAP_ROLE_NAME_TO_ID].get(role, None)

def buildUserIdToNameMap():
  cd = buildGAPIObject(u'directory')
  result = callGAPIpages(cd.users(), u'list', u'users',
                         customer=GC_Values[GC_CUSTOMER_ID],
                         fields=u'nextPageToken,users(id,primaryEmail)',
                         maxResults=GC_Values[GC_USER_MAX_RESULTS])
  GM_Globals[GM_MAP_USER_ID_TO_NAME] = {}
  for user in result:
    GM_Globals[GM_MAP_USER_ID_TO_NAME][user[u'id']] = user[u'primaryEmail']

def user_from_userid(userid):
  if not GM_Globals[GM_MAP_USER_ID_TO_NAME]:
    buildUserIdToNameMap()
  return GM_Globals[GM_MAP_USER_ID_TO_NAME].get(userid, u'')

def appID2app(dt, appID):
  for serviceName, serviceID in SERVICE_NAME_TO_ID_MAP.items():
    if appID == serviceID:
      return serviceName
  online_services = callGAPIpages(dt.applications(), u'list', u'applications', customerId=GC_Values[GC_CUSTOMER_ID])
  for online_service in online_services:
    if appID == online_service[u'id']:
      return online_service[u'name']
  return u'applicationId: {0}'.format(appID)

def app2appID(dt, app):
  serviceName = app.lower()
  if serviceName in SERVICE_NAME_CHOICES_MAP:
    return (SERVICE_NAME_CHOICES_MAP[serviceName], SERVICE_NAME_TO_ID_MAP[SERVICE_NAME_CHOICES_MAP[serviceName]])
  online_services = callGAPIpages(dt.applications(), u'list', u'applications', customerId=GC_Values[GC_CUSTOMER_ID])
  for online_service in online_services:
    if serviceName == online_service[u'name'].lower():
      return (online_service[u'name'], online_service[u'id'])
  systemErrorExit(2, '%s is not a valid service for data transfer.' % app)

def convertToUserID(user):
  if user[:4].lower() == u'uid:':
    return user[4:]
  if user[:3].lower() == u'id:':
    return user[3:]
  cd = buildGAPIObject(u'directory')
  if user.find(u'@') == -1:
    user = u'%s@%s' % (user, GC_Values[GC_DOMAIN])
  try:
    return callGAPI(cd.users(), u'get', throw_reasons=[GAPI_USER_NOT_FOUND, GAPI_BAD_REQUEST, GAPI_FORBIDDEN], userKey=user, fields=u'id')[u'id']
  except (GAPI_userNotFound, GAPI_badRequest, GAPI_forbidden):
    systemErrorExit(3, 'no such user %s' % user)

def convertUserIDtoEmail(uid):
  cd = buildGAPIObject(u'directory')
  try:
    return callGAPI(cd.users(), u'get', throw_reasons=[GAPI_USER_NOT_FOUND, GAPI_BAD_REQUEST, GAPI_FORBIDDEN], userKey=uid, fields=u'primaryEmail')[u'primaryEmail']
  except (GAPI_userNotFound, GAPI_badRequest, GAPI_forbidden):
    return u'uid:{0}'.format(uid)

def doCreateDataTransfer():
  dt = buildGAPIObject(u'datatransfer')
  body = {}
  old_owner = sys.argv[3]
  body[u'oldOwnerUserId'] = convertToUserID(old_owner)
  serviceName, serviceID = app2appID(dt, sys.argv[4])
  new_owner = sys.argv[5]
  body[u'newOwnerUserId'] = convertToUserID(new_owner)
  parameters = {}
  i = 6
  while i < len(sys.argv):
    parameters[sys.argv[i].upper()] = sys.argv[i+1].upper().split(u',')
    i += 2
  body[u'applicationDataTransfers'] = [{u'applicationId': serviceID}]
  for key, value in parameters.items():
    if u'applicationTransferParams' not in body[u'applicationDataTransfers'][0]:
      body[u'applicationDataTransfers'][0][u'applicationTransferParams'] = []
    body[u'applicationDataTransfers'][0][u'applicationTransferParams'].append({u'key': key, u'value': value})
  result = callGAPI(dt.transfers(), u'insert', body=body, fields=u'id')[u'id']
  print u'Submitted request id %s to transfer %s from %s to %s' % (result, serviceName, old_owner, new_owner)

def doPrintTransferApps():
  dt = buildGAPIObject(u'datatransfer')
  apps = callGAPIpages(dt.applications(), u'list', u'applications', customerId=GC_Values[GC_CUSTOMER_ID])
  for app in apps:
    print_json(None, app)
    print

def doPrintDataTransfers():
  dt = buildGAPIObject(u'datatransfer')
  i = 3
  newOwnerUserId = None
  oldOwnerUserId = None
  status = None
  todrive = False
  titles = [u'id',]
  csvRows = []
  while i < len(sys.argv):
    myarg = sys.argv[i].lower().replace(u'_', u'')
    if myarg in [u'olduser', u'oldowner']:
      oldOwnerUserId = convertToUserID(sys.argv[i+1])
      i += 2
    elif myarg in [u'newuser', u'newowner']:
      newOwnerUserId = convertToUserID(sys.argv[i+1])
      i += 2
    elif myarg == u'status':
      status = sys.argv[i+1]
      i += 2
    elif myarg == u'todrive':
      todrive = True
      i += 1
    else:
      systemErrorExit(2, '%s is not a valid argument for "gam print transfers"' % sys.argv[i])
  transfers = callGAPIpages(dt.transfers(), u'list', u'dataTransfers',
                            customerId=GC_Values[GC_CUSTOMER_ID], status=status,
                            newOwnerUserId=newOwnerUserId, oldOwnerUserId=oldOwnerUserId)
  for transfer in transfers:
    for i in range(0, len(transfer[u'applicationDataTransfers'])):
      a_transfer = {}
      a_transfer[u'oldOwnerUserEmail'] = convertUserIDtoEmail(transfer[u'oldOwnerUserId'])
      a_transfer[u'newOwnerUserEmail'] = convertUserIDtoEmail(transfer[u'newOwnerUserId'])
      a_transfer[u'requestTime'] = transfer[u'requestTime']
      a_transfer[u'applicationId'] = transfer[u'applicationDataTransfers'][i][u'applicationId']
      a_transfer[u'application'] = appID2app(dt, a_transfer[u'applicationId'])
      a_transfer[u'status'] = transfer[u'applicationDataTransfers'][i][u'applicationTransferStatus']
      a_transfer[u'id'] = transfer[u'id']
      if u'applicationTransferParams' in transfer[u'applicationDataTransfers'][i]:
        for param in transfer[u'applicationDataTransfers'][i][u'applicationTransferParams']:
          a_transfer[param[u'key']] = u','.join(param[u'value'])
    for title in a_transfer:
      if title not in titles:
        titles.append(title)
    csvRows.append(a_transfer)
  writeCSVfile(csvRows, titles, u'Data Transfers', todrive)

def doGetDataTransferInfo():
  dt = buildGAPIObject(u'datatransfer')
  dtId = sys.argv[3]
  transfer = callGAPI(dt.transfers(), u'get', dataTransferId=dtId)
  print u'Old Owner: %s' % convertUserIDtoEmail(transfer[u'oldOwnerUserId'])
  print u'New Owner: %s' % convertUserIDtoEmail(transfer[u'newOwnerUserId'])
  print u'Request Time: %s' % transfer[u'requestTime']
  for app in transfer[u'applicationDataTransfers']:
    print u'Application: %s' % appID2app(dt, app[u'applicationId'])
    print u'Status: %s' % app[u'applicationTransferStatus']
    print u'Parameters:'
    if u'applicationTransferParams' in app:
      for param in app[u'applicationTransferParams']:
        print   u' %s: %s' % (param[u'key'], u','.join(param[u'value']))
    else:
      print u' None'
    print

def doPrintShowGuardians(csvFormat):
  croom = buildGAPIObject(u'classroom')
  invitedEmailAddress = None
  studentIds = [u'-',]
  states = None
  service = croom.userProfiles().guardians()
  items = u'guardians'
  itemName = 'Guardians'
  if csvFormat:
    csvRows = []
    todrive = False
    titles = [u'studentEmail', u'studentId', u'invitedEmailAddress', u'guardianId']
  i = 3
  while i < len(sys.argv):
    myarg = sys.argv[i].lower()
    if csvFormat and myarg == u'todrive':
      todrive = True
      i += 1
    elif myarg == u'invitedguardian':
      invitedEmailAddress = normalizeEmailAddressOrUID(sys.argv[i+1])
      i += 2
    elif myarg == u'student':
      studentIds = [normalizeStudentGuardianEmailAddressOrUID(sys.argv[i+1])]
      i += 2
    elif myarg == u'invitations':
      service = croom.userProfiles().guardianInvitations()
      items = u'guardianInvitations'
      itemName = 'Guardian Invitations'
      titles = [u'studentEmail', u'studentId', u'invitedEmailAddress', u'invitationId']
      if states is None:
        states = [u'COMPLETE', u'PENDING', u'GUARDIAN_INVITATION_STATE_UNSPECIFIED']
      i += 1
    elif myarg == u'states':
      states = sys.argv[i+1].upper().replace(u',', u' ').split()
      i += 2
    elif myarg in usergroup_types:
      studentIds = getUsersToModify(entity_type=myarg, entity=sys.argv[i+1])
      i += 2
    else:
      systemErrorExit(2, '%s is not a valid argument for "gam %s guardians"' % (sys.argv[i], [u'show', u'print'][csvFormat]))
  i = 0
  count = len(studentIds)
  for studentId in studentIds:
    i += 1
    studentId = normalizeStudentGuardianEmailAddressOrUID(studentId)
    kwargs = {u'invitedEmailAddress': invitedEmailAddress, u'studentId': studentId}
    if items == u'guardianInvitations':
      kwargs[u'states'] = states
    if studentId != u'-':
      if csvFormat:
        sys.stderr.write('\r')
        sys.stderr.flush()
        sys.stderr.write(u'Getting %s for %s%s%s' % (itemName, studentId, currentCount(i, count), u' ' * 40))
    guardians = callGAPIpages(service, u'list', items, soft_errors=True, **kwargs)
    if not csvFormat:
      print u'Student: {0}, {1}:{2}'.format(studentId, itemName, currentCount(i, count))
      for guardian in guardians:
        print_json(None, guardian, spacing=u'  ')
    else:
      for guardian in guardians:
        guardian[u'studentEmail'] = studentId
        addRowTitlesToCSVfile(flatten_json(guardian), csvRows, titles)
  if csvFormat:
    sys.stderr.write(u'\n')
    writeCSVfile(csvRows, titles, itemName, todrive)

def doInviteGuardian():
  croom = buildGAPIObject(u'classroom')
  body = {u'invitedEmailAddress': normalizeEmailAddressOrUID(sys.argv[3])}
  studentId = normalizeStudentGuardianEmailAddressOrUID(sys.argv[4])
  result = callGAPI(croom.userProfiles().guardianInvitations(), u'create', studentId=studentId, body=body)
  print u'Invited email %s as guardian of %s. Invite ID %s' % (result[u'invitedEmailAddress'], studentId, result[u'invitationId'])

def _cancelGuardianInvitation(croom, studentId, invitationId):
  try:
    result = callGAPI(croom.userProfiles().guardianInvitations(), u'patch',
                      throw_reasons=[GAPI_FAILED_PRECONDITION, GAPI_FORBIDDEN, GAPI_NOT_FOUND],
                      studentId=studentId, invitationId=invitationId, updateMask=u'state', body={u'state': u'COMPLETE'})
    print u'Cancelled PENDING guardian invitation for %s as guardian of %s' % (result[u'invitedEmailAddress'], studentId)
    return True
  except GAPI_failedPrecondition:
    stderrErrorMsg(u'Guardian invitation %s for %s status is not PENDING' % (invitationId, studentId))
    GM_Globals[GM_SYSEXITRC] = 3
    return True
  except GAPI_forbidden:
    entityUnknownWarning(u'Student', studentId, 0, 0)
    sys.exit(3)
  except GAPI_notFound:
    return False

def doCancelGuardianInvitation():
  croom = buildGAPIObject(u'classroom')
  invitationId = sys.argv[3]
  studentId = normalizeStudentGuardianEmailAddressOrUID(sys.argv[4])
  if not _cancelGuardianInvitation(croom, studentId, invitationId):
    systemErrorExit(3, u'Guardian invitation %s for %s does not exist' % (invitationId, studentId))

def _deleteGuardian(croom, studentId, guardianId, guardianEmail):
  try:
    callGAPI(croom.userProfiles().guardians(), u'delete',
             throw_reasons=[GAPI_FORBIDDEN, GAPI_NOT_FOUND],
             studentId=studentId, guardianId=guardianId)
    print u'Deleted %s as a guardian of %s' % (guardianEmail, studentId)
    return True
  except GAPI_forbidden:
    entityUnknownWarning(u'Student', studentId, 0, 0)
    sys.exit(3)
  except GAPI_notFound:
    return False

def doDeleteGuardian():
  croom = buildGAPIObject(u'classroom')
  invitationsOnly = False
  guardianId = normalizeStudentGuardianEmailAddressOrUID(sys.argv[3])
  guardianIdIsEmail = guardianId.find(u'@') != -1
  studentId = normalizeStudentGuardianEmailAddressOrUID(sys.argv[4])
  i = 5
  while i < len(sys.argv):
    myarg = sys.argv[i].lower()
    if myarg in [u'invitation', u'invitations']:
      invitationsOnly = True
      i += 1
    else:
      systemErrorExit(2, '%s is not a valid argument for "gam delete guardian"' % (sys.argv[i]))
  if not invitationsOnly:
    if guardianIdIsEmail:
      try:
        results = callGAPIpages(croom.userProfiles().guardians(), u'list', u'guardians',
                                throw_reasons=[GAPI_FORBIDDEN],
                                studentId=studentId, invitedEmailAddress=guardianId)
        if len(results) > 0:
          for result in results:
            _deleteGuardian(croom, studentId, result[u'guardianId'], guardianId)
          return
      except GAPI_forbidden:
        entityUnknownWarning(u'Student', studentId, 0, 0)
        sys.exit(3)
    else:
      if _deleteGuardian(croom, studentId, guardianId, guardianId):
        return
  # See if there's a pending invitation
  if guardianIdIsEmail:
    try:
      results = callGAPIpages(croom.userProfiles().guardianInvitations(), u'list', u'guardianInvitations',
                              throw_reasons=[GAPI_FORBIDDEN],
                              studentId=studentId, invitedEmailAddress=guardianId, states=[u'PENDING',])
      if len(results) > 0:
        for result in results:
          status = _cancelGuardianInvitation(croom, studentId, result[u'invitationId'])
        sys.exit(status)
    except GAPI_forbidden:
      entityUnknownWarning(u'Student', studentId, 0, 0)
      sys.exit(3)
  else:
    if _cancelGuardianInvitation(croom, studentId, guardianId):
      return
  systemErrorExit(3, '%s is not a guardian of %s and no invitation exists.' % (guardianId, studentId))

def doCreateCourse():
  croom = buildGAPIObject(u'classroom')
  body = {u'ownerId': u'me',
          u'name': u'Unknown Course'}
  i = 3
  while i < len(sys.argv):
    myarg = sys.argv[i].lower()
    if myarg in [u'alias', u'id']:
      body[u'id'] = u'd:%s' % sys.argv[i+1]
      i += 2
    else:
      getCourseAttribute(myarg, sys.argv[i+1], body, croom, u'create')
      i += 2
  result = callGAPI(croom.courses(), u'create', body=body)
  print u'Created course %s' % result[u'id']

def doGetCourseInfo():
  croom = buildGAPIObject(u'classroom')
  courseId = addCourseIdScope(sys.argv[3])
  info = callGAPI(croom.courses(), u'get', id=courseId)
  info['ownerEmail'] = convertUIDtoEmailAddress(u'uid:%s' % info['ownerId'])
  print_json(None, info)
  teachers = callGAPIpages(croom.courses().teachers(), u'list', u'teachers', courseId=courseId)
  students = callGAPIpages(croom.courses().students(), u'list', u'students', courseId=courseId)
  try:
    aliases = callGAPIpages(croom.courses().aliases(), u'list', u'aliases', throw_reasons=[GAPI_NOT_IMPLEMENTED], courseId=courseId)
  except GAPI_notImplemented:
    aliases = []
  if aliases:
    print u'Aliases:'
    for alias in aliases:
      print u'  %s' % alias[u'alias'][2:]
  print u'Participants:'
  print u' Teachers:'
  for teacher in teachers:
    try:
      print utils.convertUTF8(u'  %s - %s' % (teacher[u'profile'][u'name'][u'fullName'], teacher[u'profile'][u'emailAddress']))
    except KeyError:
      print utils.convertUTF8(u'  %s' % teacher[u'profile'][u'name'][u'fullName'])
  print u' Students:'
  for student in students:
    try:
      print utils.convertUTF8(u'  %s - %s' % (student[u'profile'][u'name'][u'fullName'], student[u'profile'][u'emailAddress']))
    except KeyError:
      print utils.convertUTF8(u'  %s' % student[u'profile'][u'name'][u'fullName'])

COURSE_ARGUMENT_TO_PROPERTY_MAP = {
  u'alternatelink': u'alternateLink',
  u'coursegroupemail': u'courseGroupEmail',
  u'coursematerialsets': u'courseMaterialSets',
  u'coursestate': u'courseState',
  u'creationtime': u'creationTime',
  u'description': u'description',
  u'descriptionheading': u'descriptionHeading',
  u'enrollmentcode': u'enrollmentCode',
  u'guardiansenabled': u'guardiansEnabled',
  u'id': u'id',
  u'name': u'name',
  u'ownerid': u'ownerId',
  u'room': u'room',
  u'section': u'section',
  u'teacherfolder': u'teacherFolder',
  u'teachergroupemail': u'teacherGroupEmail',
  u'updatetime': u'updateTime',
  }

def doPrintCourses():

  def _processFieldsList(myarg, i, fList):
    fieldNameList = sys.argv[i+1]
    for field in fieldNameList.lower().replace(u',', u' ').split():
      if field in COURSE_ARGUMENT_TO_PROPERTY_MAP:
        if field != u'id':
          fList.append(COURSE_ARGUMENT_TO_PROPERTY_MAP[field])
      else:
        systemErrorExit(2, '%s is not a valid argument for "gam print courses %s"' % (field, myarg))

  def _saveParticipants(course, participants, role):
    jcount = len(participants)
    course[role] = jcount
    addTitlesToCSVfile([role], titles)
    if countsOnly:
      return
    j = 0
    for member in participants:
      memberTitles = []
      prefix = u'{0}.{1}.'.format(role, j)
      profile = member[u'profile']
      emailAddress = profile.get(u'emailAddress')
      if emailAddress:
        memberTitle = prefix+u'emailAddress'
        course[memberTitle] = emailAddress
        memberTitles.append(memberTitle)
      memberId = profile.get(u'id')
      if memberId:
        memberTitle = prefix+u'id'
        course[memberTitle] = memberId
        memberTitles.append(memberTitle)
      fullName = profile.get(u'name', {}).get(u'fullName')
      if fullName:
        memberTitle = prefix+u'name.fullName'
        course[memberTitle] = fullName
        memberTitles.append(memberTitle)
      addTitlesToCSVfile(memberTitles, titles)
      j += 1

  croom = buildGAPIObject(u'classroom')
  todrive = False
  fieldsList = []
  skipFieldsList = []
  titles = [u'id',]
  csvRows = []
  teacherId = None
  studentId = None
  courseStates = []
  showAliases = False
  countsOnly = False
  delimiter = u' '
  showMembers = u''
  i = 3
  while i < len(sys.argv):
    myarg = sys.argv[i].lower()
    if myarg == u'teacher':
      teacherId = normalizeEmailAddressOrUID(sys.argv[i+1])
      i += 2
    elif myarg == u'student':
      studentId = normalizeEmailAddressOrUID(sys.argv[i+1])
      i += 2
    elif myarg in [u'state', u'states', u'status']:
      _getCourseStates(croom, sys.argv[i+1], courseStates)
      i += 2
    elif myarg == u'todrive':
      todrive = True
      i += 1
    elif myarg in [u'alias', u'aliases']:
      showAliases = True
      i += 1
    elif myarg == u'countsonly':
      countsOnly = True
      i += 1
    elif myarg == u'delimiter':
      delimiter = sys.argv[i+1]
      i += 2
    elif myarg == u'show':
      showMembers = sys.argv[i+1].lower()
      if showMembers not in [u'all', u'students', u'teachers']:
        systemErrorExit(2, 'show must be all, students or teachers; got %s' % showMembers)
      i += 2
    elif myarg == u'fields':
      if not fieldsList:
        fieldsList = [u'id',]
      _processFieldsList(myarg, i, fieldsList)
      i += 2
    elif myarg == u'skipfields':
      _processFieldsList(myarg, i, skipFieldsList)
      i += 2
    else:
      systemErrorExit(2, '%s is not a valid argument for "gam print courses"' % sys.argv[i])
  fields = u'nextPageToken,courses({0})'.format(u','.join(set(fieldsList))) if fieldsList else None
  sys.stderr.write(u'Retrieving courses for organization (may take some time for large accounts)...\n')
  page_message = u'Got %%num_items%% courses...\n'
  all_courses = callGAPIpages(croom.courses(), u'list', u'courses', page_message=page_message, teacherId=teacherId, studentId=studentId, courseStates=courseStates, fields=fields)
  for course in all_courses:
    for field in skipFieldsList:
      course.pop(field, None)
    addRowTitlesToCSVfile(flatten_json(course), csvRows, titles)
  if showAliases or showMembers:
    if showAliases:
      titles.append(u'Aliases')
    if showMembers:
      if countsOnly:
        teachersFields = u'nextPageToken,teachers(profile(id))'
        studentsFields = u'nextPageToken,students(profile(id))'
      else:
        teachersFields = u'nextPageToken,teachers(profile)'
        studentsFields = u'nextPageToken,students(profile)'
    i = 0
    count = len(csvRows)
    for course in csvRows:
      i += 1
      courseId = course[u'id']
      if showAliases:
        alias_message = u' got %%%%num_items%%%% aliases for course %s%s' % (courseId, currentCount(i, count))
        course_aliases = callGAPIpages(croom.courses().aliases(), u'list', u'aliases',
                                       page_message=alias_message,
                                       courseId=courseId)
        course[u'Aliases'] = delimiter.join([alias[u'alias'][2:] for alias in course_aliases])
      if showMembers:
        if showMembers != u'students':
          teacher_message = u' got %%%%num_items%%%% teachers for course %s%s' % (courseId, currentCount(i, count))
          results = callGAPIpages(croom.courses().teachers(), u'list', u'teachers',
                                  page_message=teacher_message,
                                  courseId=courseId, fields=teachersFields)
          _saveParticipants(course, results, u'teachers')
        if showMembers != u'teachers':
          student_message = u' got %%%%num_items%%%% students for course %s%s' % (courseId, currentCount(i, count))
          results = callGAPIpages(croom.courses().students(), u'list', u'students',
                                  page_message=student_message,
                                  courseId=courseId, fields=studentsFields)
          _saveParticipants(course, results, u'students')
  sortCSVTitles([u'id', u'name'], titles)
  writeCSVfile(csvRows, titles, u'Courses', todrive)

def doPrintCourseParticipants():
  croom = buildGAPIObject(u'classroom')
  todrive = False
  titles = [u'courseId',]
  csvRows = []
  courses = []
  teacherId = None
  studentId = None
  courseStates = []
  showMembers = u'all'
  i = 3
  while i < len(sys.argv):
    myarg = sys.argv[i].lower()
    if myarg in [u'course', u'class']:
      courses.append(addCourseIdScope(sys.argv[i+1]))
      i += 2
    elif myarg == u'teacher':
      teacherId = normalizeEmailAddressOrUID(sys.argv[i+1])
      i += 2
    elif myarg == u'student':
      studentId = normalizeEmailAddressOrUID(sys.argv[i+1])
      i += 2
    elif myarg in [u'state', u'states', u'status']:
      _getCourseStates(croom, sys.argv[i+1], courseStates)
      i += 2
    elif myarg == u'todrive':
      todrive = True
      i += 1
    elif myarg == u'show':
      showMembers = sys.argv[i+1].lower()
      if showMembers not in [u'all', u'students', u'teachers']:
        systemErrorExit(2, 'show must be all, students or teachers; got %s' % showMembers)
      i += 2
    else:
      systemErrorExit(2, '%s is not a valid argument for "gam print course-participants"' % sys.argv[i])
  if len(courses) == 0:
    sys.stderr.write(u'Retrieving courses for organization (may take some time for large accounts)...\n')
    page_message = u'Got %%num_items%% courses...\n'
    all_courses = callGAPIpages(croom.courses(), u'list', u'courses', page_message=page_message,
                                teacherId=teacherId, studentId=studentId, courseStates=courseStates, fields=u'nextPageToken,courses(id,name)')
  else:
    all_courses = []
    for course in courses:
      all_courses.append(callGAPI(croom.courses(), u'get', id=course, fields=u'id,name'))
  i = 0
  count = len(all_courses)
  for course in all_courses:
    i += 1
    courseId = course[u'id']
    if showMembers != u'students':
      page_message = u' got %%%%num_items%%%% teachers for course %s (%s/%s)' % (courseId, i, count)
      teachers = callGAPIpages(croom.courses().teachers(), u'list', u'teachers', page_message=page_message, courseId=courseId)
      for teacher in teachers:
        addRowTitlesToCSVfile(flatten_json(teacher, flattened={u'courseId': courseId, u'courseName': course[u'name'], u'userRole': u'TEACHER'}), csvRows, titles)
    if showMembers != u'teachers':
      page_message = u' got %%%%num_items%%%% students for course %s (%s/%s)' % (courseId, i, count)
      students = callGAPIpages(croom.courses().students(), u'list', u'students', page_message=page_message, courseId=courseId)
      for student in students:
        addRowTitlesToCSVfile(flatten_json(student, flattened={u'courseId': courseId, u'courseName': course[u'name'], u'userRole': u'STUDENT'}), csvRows, titles)
  sortCSVTitles([u'courseId', u'courseName', u'userRole', u'userId'], titles)
  writeCSVfile(csvRows, titles, u'Course Participants', todrive)

def doPrintPrintJobs():
  cp = buildGAPIObject(u'cloudprint')
  todrive = False
  titles = [u'printerid', u'id']
  csvRows = []
  printerid = None
  owner = None
  status = None
  sortorder = None
  descending = False
  query = None
  age = None
  older_or_newer = None
  jobLimit = PRINTJOBS_DEFAULT_JOB_LIMIT
  i = 3
  while i < len(sys.argv):
    myarg = sys.argv[i].lower().replace(u'_', u'')
    if myarg == u'todrive':
      todrive = True
      i += 1
    elif myarg in [u'olderthan', u'newerthan']:
      if myarg == u'olderthan':
        older_or_newer = u'older'
      else:
        older_or_newer = u'newer'
      age_number = sys.argv[i+1][:-1]
      if not age_number.isdigit():
        systemErrorExit(2, 'expected a number; got %s' % age_number)
      age_unit = sys.argv[i+1][-1].lower()
      if age_unit == u'm':
        age = int(time.time()) - (int(age_number) * 60)
      elif age_unit == u'h':
        age = int(time.time()) - (int(age_number) * 60 * 60)
      elif age_unit == u'd':
        age = int(time.time()) - (int(age_number) * 60 * 60 * 24)
      else:
        systemErrorExit(2, 'expected m (minutes), h (hours) or d (days); got %s' % age_unit)
      i += 2
    elif myarg == u'query':
      query = sys.argv[i+1]
      i += 2
    elif myarg == u'status':
      status = sys.argv[i+1]
      i += 2
    elif myarg == u'ascending':
      descending = False
      i += 1
    elif myarg == u'descending':
      descending = True
      i += 1
    elif myarg == u'orderby':
      sortorder = sys.argv[i+1].lower().replace(u'_', u'')
      if sortorder not in PRINTJOB_ASCENDINGORDER_MAP:
        systemErrorExit(2, 'orderby must be one of %s; got %s' % (u', '.join(PRINTJOB_ASCENDINGORDER_MAP), sortorder))
      sortorder = PRINTJOB_ASCENDINGORDER_MAP[sortorder]
      i += 2
    elif myarg in [u'printer', u'printerid']:
      printerid = sys.argv[i+1]
      i += 2
    elif myarg in [u'owner', u'user']:
      owner = sys.argv[i+1]
      i += 2
    elif myarg == u'limit':
      jobLimit = max(0, int(sys.argv[i+1]))
      i += 2
    else:
      systemErrorExit(2, '%s is not a valid argument for "gam print printjobs"' % sys.argv[i])
  if sortorder and descending:
    sortorder = PRINTJOB_DESCENDINGORDER_MAP[sortorder]
  if printerid:
    result = callGAPI(cp.printers(), u'get',
                      printerid=printerid)
    checkCloudPrintResult(result)
  if ((not sortorder) or (sortorder == u'CREATE_TIME_DESC')) and (older_or_newer == u'newer'):
    timeExit = True
  elif (sortorder == u'CREATE_TIME') and (older_or_newer == u'older'):
    timeExit = True
  else:
    timeExit = False
  jobCount = offset = 0
  while True:
    if jobLimit == 0:
      limit = PRINTJOBS_DEFAULT_MAX_RESULTS
    else:
      limit = min(PRINTJOBS_DEFAULT_MAX_RESULTS, jobLimit-jobCount)
      if limit == 0:
        break
    result = callGAPI(cp.jobs(), u'list',
                      printerid=printerid, q=query, status=status, sortorder=sortorder,
                      owner=owner, offset=offset, limit=limit)
    checkCloudPrintResult(result)
    newJobs = result[u'range'][u'jobsCount']
    totalJobs = int(result[u'range'][u'jobsTotal'])
    if GC_Values[GC_DEBUG_LEVEL] > 0:
      sys.stderr.write(u'Debug: jobCount: {0}, jobLimit: {1}, jobsCount: {2}, jobsTotal: {3}\n'.format(jobCount, jobLimit, newJobs, totalJobs))
    if newJobs == 0:
      break
    jobCount += newJobs
    offset += newJobs
    for job in result[u'jobs']:
      createTime = int(job[u'createTime'])/1000
      if older_or_newer:
        if older_or_newer == u'older' and createTime > age:
          if timeExit:
            jobCount = totalJobs
            break
          continue
        elif older_or_newer == u'newer' and createTime < age:
          if timeExit:
            jobCount = totalJobs
            break
          continue
      updateTime = int(job[u'updateTime'])/1000
      job[u'createTime'] = datetime.datetime.fromtimestamp(createTime).strftime(u'%Y-%m-%d %H:%M:%S')
      job[u'updateTime'] = datetime.datetime.fromtimestamp(updateTime).strftime(u'%Y-%m-%d %H:%M:%S')
      job[u'tags'] = u' '.join(job[u'tags'])
      addRowTitlesToCSVfile(flatten_json(job), csvRows, titles)
    if jobCount >= totalJobs:
      break
  writeCSVfile(csvRows, titles, u'Print Jobs', todrive)

def doPrintPrinters():
  cp = buildGAPIObject(u'cloudprint')
  todrive = False
  titles = [u'id',]
  csvRows = []
  query = None
  printer_type = None
  connection_status = None
  extra_fields = None
  i = 3
  while i < len(sys.argv):
    myarg = sys.argv[i].lower().replace(u'_', u'')
    if myarg == u'query':
      query = sys.argv[i+1]
      i += 2
    elif myarg == u'type':
      printer_type = sys.argv[i+1]
      i += 2
    elif myarg == u'status':
      connection_status = sys.argv[i+1]
      i += 2
    elif myarg == u'extrafields':
      extra_fields = sys.argv[i+1]
      i += 2
    elif myarg == u'todrive':
      todrive = True
      i += 1
    else:
      systemErrorExit(2, '%s is not a valid argument for "gam print printers"' % sys.argv[i])
  printers = callGAPI(cp.printers(), u'list', q=query, type=printer_type, connection_status=connection_status, extra_fields=extra_fields)
  checkCloudPrintResult(printers)
  for printer in printers[u'printers']:
    createTime = int(printer[u'createTime'])/1000
    accessTime = int(printer[u'accessTime'])/1000
    updateTime = int(printer[u'updateTime'])/1000
    printer[u'createTime'] = datetime.datetime.fromtimestamp(createTime).strftime(u'%Y-%m-%d %H:%M:%S')
    printer[u'accessTime'] = datetime.datetime.fromtimestamp(accessTime).strftime(u'%Y-%m-%d %H:%M:%S')
    printer[u'updateTime'] = datetime.datetime.fromtimestamp(updateTime).strftime(u'%Y-%m-%d %H:%M:%S')
    printer[u'tags'] = u' '.join(printer[u'tags'])
    addRowTitlesToCSVfile(flatten_json(printer), csvRows, titles)
  writeCSVfile(csvRows, titles, u'Printers', todrive)

def changeCalendarAttendees(users):
  do_it = True
  i = 5
  allevents = False
  start_date = end_date = None
  while len(sys.argv) > i:
    myarg = sys.argv[i].lower()
    if myarg == u'csv':
      csv_file = sys.argv[i+1]
      i += 2
    elif myarg == u'dryrun':
      do_it = False
      i += 1
    elif myarg == u'start':
      start_date = getTimeOrDeltaFromNow(sys.argv[i+1])
      i += 2
    elif myarg == u'end':
      end_date = getTimeOrDeltaFromNow(sys.argv[i+1])
      i += 2
    elif myarg == u'allevents':
      allevents = True
      i += 1
    else:
      systemErrorExit(2, '%s is not a valid argument for "gam <users> update calattendees"' % sys.argv[i])
  attendee_map = {}
  f = openFile(csv_file)
  csvFile = csv.reader(f)
  for row in csvFile:
    attendee_map[row[0].lower()] = row[1].lower()
  closeFile(f)
  for user in users:
    sys.stdout.write(u'Checking user %s\n' % user)
    user, cal = buildCalendarGAPIObject(user)
    if not cal:
      continue
    page_token = None
    while True:
      events_page = callGAPI(cal.events(), u'list', calendarId=user, pageToken=page_token, timeMin=start_date, timeMax=end_date, showDeleted=False, showHiddenInvitations=False)
      print u'Got %s items' % len(events_page.get(u'items', []))
      for event in events_page.get(u'items', []):
        if event[u'status'] == u'cancelled':
          #print u' skipping cancelled event'
          continue
        try:
          event_summary = utils.convertUTF8(event[u'summary'])
        except (KeyError, UnicodeEncodeError, UnicodeDecodeError):
          event_summary = event[u'id']
        try:
          if not allevents and event[u'organizer'][u'email'].lower() != user:
            #print u' skipping not-my-event %s' % event_summary
            continue
        except KeyError:
          pass # no email for organizer
        needs_update = False
        try:
          for attendee in event[u'attendees']:
            try:
              if attendee[u'email'].lower() in attendee_map:
                old_email = attendee[u'email'].lower()
                new_email = attendee_map[attendee[u'email'].lower()]
                print u' SWITCHING attendee %s to %s for %s' % (old_email, new_email, event_summary)
                event[u'attendees'].remove(attendee)
                event[u'attendees'].append({u'email': new_email})
                needs_update = True
            except KeyError: # no email for that attendee
              pass
        except KeyError:
          continue # no attendees
        if needs_update:
          body = {}
          body[u'attendees'] = event[u'attendees']
          print u'UPDATING %s' % event_summary
          if do_it:
            callGAPI(cal.events(), u'patch', calendarId=user, eventId=event[u'id'], sendNotifications=False, body=body)
          else:
            print u' not pulling the trigger.'
        #else:
        #  print u' no update needed for %s' % event_summary
      try:
        page_token = events_page[u'nextPageToken']
      except KeyError:
        break

def deleteCalendar(users):
  calendarId = normalizeCalendarId(sys.argv[5])
  for user in users:
    user, cal = buildCalendarGAPIObject(user)
    if not cal:
      continue
    callGAPI(cal.calendarList(), u'delete', soft_errors=True, calendarId=calendarId)

def getCalendarAttributes(i, body, function):
  colorRgbFormat = False
  while i < len(sys.argv):
    myarg = sys.argv[i].lower().replace(u'_', u'')
    if myarg == u'selected':
      body[u'selected'] = getBoolean(sys.argv[i+1], myarg)
      i += 2
    elif myarg == u'hidden':
      body[u'hidden'] = getBoolean(sys.argv[i+1], myarg)
      i += 2
    elif myarg == u'summary':
      body[u'summaryOverride'] = sys.argv[i+1]
      i += 2
    elif myarg == u'colorindex':
      body[u'colorId'] = str(sys.argv[i+1])
      i += 2
    elif myarg == u'backgroundcolor':
      body[u'backgroundColor'] = getColor(sys.argv[i+1])
      colorRgbFormat = True
      i += 2
    elif myarg == u'foregroundcolor':
      body[u'foregroundColor'] = getColor(sys.argv[i+1])
      colorRgbFormat = True
      i += 2
    elif myarg == u'reminder':
      body.setdefault(u'defaultReminders', [])
      method = sys.argv[i+1].lower()
      if method not in CLEAR_NONE_ARGUMENT:
        if method not in CALENDAR_REMINDER_METHODS:
          systemErrorExit(2, 'Method must be one of %s; got %s' % (u', '.join(CALENDAR_REMINDER_METHODS+CLEAR_NONE_ARGUMENT), method))
        try:
          minutes = int(sys.argv[i+2])
        except ValueError:
          systemErrorExit(2, 'Reminder time must be specified in minutes; got %s' % sys.argv[i+2])
        body[u'defaultReminders'].append({u'method': method, u'minutes': minutes})
        i += 3
      else:
        i += 2
    elif myarg == u'notification':
      body.setdefault(u'notificationSettings', {u'notifications': []})
      method = sys.argv[i+1].lower()
      if method not in CLEAR_NONE_ARGUMENT:
        if method not in CALENDAR_NOTIFICATION_METHODS:
          systemErrorExit(2, 'Method must be one of %s; got %s' % (u', '.join(CALENDAR_NOTIFICATION_METHODS+CLEAR_NONE_ARGUMENT), method))
        eventType = sys.argv[i+2].lower()
        if eventType not in CALENDAR_NOTIFICATION_TYPES_MAP:
          systemErrorExit(2, 'Event must be one of %s; got %s' % (u', '.join(CALENDAR_NOTIFICATION_TYPES_MAP), eventType))
        body[u'notificationSettings'][u'notifications'].append({u'method': method, u'type': CALENDAR_NOTIFICATION_TYPES_MAP[eventType]})
        i += 3
      else:
        i += 2
    else:
      systemErrorExit(2, '%s is not a valid argument for "gam %s calendar"' % (sys.argv[i], function))
  return colorRgbFormat

def addCalendar(users):
  calendarId = normalizeCalendarId(sys.argv[5])
  body = {u'id': calendarId, u'selected': True, u'hidden': False}
  colorRgbFormat = getCalendarAttributes(6, body, u'add')
  i = 0
  count = len(users)
  for user in users:
    i += 1
    user, cal = buildCalendarGAPIObject(user)
    if not cal:
      continue
    print u"Subscribing %s to %s calendar (%s/%s)" % (user, calendarId, i, count)
    callGAPI(cal.calendarList(), u'insert', soft_errors=True, body=body, colorRgbFormat=colorRgbFormat)

def updateCalendar(users):
  calendarId = normalizeCalendarId(sys.argv[5], checkPrimary=True)
  body = {}
  colorRgbFormat = getCalendarAttributes(6, body, u'update')
  i = 0
  count = len(users)
  for user in users:
    i += 1
    user, cal = buildCalendarGAPIObject(user)
    if not cal:
      continue
    print u"Updating %s's subscription to calendar %s (%s/%s)" % (user, calendarId, i, count)
    callGAPI(cal.calendarList(), u'update', soft_errors=True, calendarId=calendarId, body=body, colorRgbFormat=colorRgbFormat)

def doPrinterShowACL():
  cp = buildGAPIObject(u'cloudprint')
  show_printer = sys.argv[2]
  printer_info = callGAPI(cp.printers(), u'get', printerid=show_printer)
  checkCloudPrintResult(printer_info)
  for acl in printer_info[u'printers'][0][u'access']:
    if u'key' in acl:
      acl[u'accessURL'] = u'https://www.google.com/cloudprint/addpublicprinter.html?printerid=%s&key=%s' % (show_printer, acl[u'key'])
    print_json(None, acl)
    print

def doPrinterAddACL():
  cp = buildGAPIObject(u'cloudprint')
  printer = sys.argv[2]
  role = sys.argv[4].upper()
  scope = sys.argv[5]
  notify = True if len(sys.argv) > 6 and sys.argv[6].lower() == u'notify' else False
  public = None
  skip_notification = True
  if scope.lower() == u'public':
    public = True
    scope = None
    role = None
    skip_notification = None
  elif scope.find(u'@') == -1:
    scope = u'/hd/domain/%s' % scope
  else:
    skip_notification = not notify
  result = callGAPI(cp.printers(), u'share', printerid=printer, role=role, scope=scope, public=public, skip_notification=skip_notification)
  checkCloudPrintResult(result)
  who = scope
  if who is None:
    who = u'public'
    role = u'user'
  print u'Added %s %s' % (role, who)

def doPrinterDelACL():
  cp = buildGAPIObject(u'cloudprint')
  printer = sys.argv[2]
  scope = sys.argv[4]
  public = None
  if scope.lower() == u'public':
    public = True
    scope = None
  elif scope.find(u'@') == -1:
    scope = u'/hd/domain/%s' % scope
  result = callGAPI(cp.printers(), u'unshare', printerid=printer, scope=scope, public=public)
  checkCloudPrintResult(result)
  who = scope
  if who is None:
    who = u'public'
  print u'Removed %s' % who

def encode_multipart(fields, files, boundary=None):
  def escape_quote(s):
    return s.replace('"', '\\"')

  def getFormDataLine(name, value, boundary):
    return '--{0}'.format(boundary), 'Content-Disposition: form-data; name="{0}"'.format(escape_quote(name)), '', str(value)

  if boundary is None:
    boundary = ''.join(random.choice(string.digits + string.ascii_letters) for i in range(30))
  lines = []
  for name, value in fields.items():
    if name == u'tags':
      for tag in value:
        lines.extend(getFormDataLine('tag', tag, boundary))
    else:
      lines.extend(getFormDataLine(name, value, boundary))
  for name, value in files.items():
    filename = value[u'filename']
    mimetype = value[u'mimetype']
    lines.extend((
      '--{0}'.format(boundary),
      'Content-Disposition: form-data; name="{0}"; filename="{1}"'.format(escape_quote(name), escape_quote(filename)),
      'Content-Type: {0}'.format(mimetype),
      '',
      value[u'content'],
    ))
  lines.extend((
    '--{0}--'.format(boundary),
    '',
  ))
  body = '\r\n'.join(lines)
  headers = {
    'Content-Type': 'multipart/form-data; boundary={0}'.format(boundary),
    'Content-Length': str(len(body)),
  }
  return (body, headers)

def doPrintJobFetch():
  cp = buildGAPIObject(u'cloudprint')
  printerid = sys.argv[2]
  if printerid == u'any':
    printerid = None
  owner = None
  status = None
  sortorder = None
  descending = False
  query = None
  age = None
  older_or_newer = None
  jobLimit = PRINTJOBS_DEFAULT_JOB_LIMIT
  targetFolder = os.getcwd()
  i = 4
  while i < len(sys.argv):
    myarg = sys.argv[i].lower().replace(u'_', u'')
    if myarg in [u'olderthan', u'newerthan']:
      if myarg == u'olderthan':
        older_or_newer = u'older'
      else:
        older_or_newer = u'newer'
      age_number = sys.argv[i+1][:-1]
      if not age_number.isdigit():
        systemErrorExit(2, 'expected a number; got %s' % age_number)
      age_unit = sys.argv[i+1][-1].lower()
      if age_unit == u'm':
        age = int(time.time()) - (int(age_number) * 60)
      elif age_unit == u'h':
        age = int(time.time()) - (int(age_number) * 60 * 60)
      elif age_unit == u'd':
        age = int(time.time()) - (int(age_number) * 60 * 60 * 24)
      else:
        systemErrorExit(2, 'expected m (minutes), h (hours) or d (days); got %s' % age_unit)
      i += 2
    elif myarg == u'query':
      query = sys.argv[i+1]
      i += 2
    elif myarg == u'status':
      status = sys.argv[i+1]
      i += 2
    elif myarg == u'ascending':
      descending = False
      i += 1
    elif myarg == u'descending':
      descending = True
      i += 1
    elif myarg == u'orderby':
      sortorder = sys.argv[i+1].lower().replace(u'_', u'')
      if sortorder not in PRINTJOB_ASCENDINGORDER_MAP:
        systemErrorExit(2, 'orderby must be one of %s; got %s' % (u', '.join(PRINTJOB_ASCENDINGORDER_MAP), sortorder))
      sortorder = PRINTJOB_ASCENDINGORDER_MAP[sortorder]
      i += 2
    elif myarg in [u'owner', u'user']:
      owner = sys.argv[i+1]
      i += 2
    elif myarg == u'limit':
      jobLimit = max(0, int(sys.argv[i+1]))
      i += 2
    elif myarg == u'drivedir':
      targetFolder = GC_Values[GC_DRIVE_DIR]
      i += 1
    elif myarg == u'targetfolder':
      targetFolder = os.path.expanduser(sys.argv[i+1])
      if not os.path.isdir(targetFolder):
        os.makedirs(targetFolder)
      i += 2
    else:
      systemErrorExit(2, '%s is not a valid argument for "gam printjobs fetch"' % sys.argv[i])
  if sortorder and descending:
    sortorder = PRINTJOB_DESCENDINGORDER_MAP[sortorder]
  if printerid:
    result = callGAPI(cp.printers(), u'get',
                      printerid=printerid)
    checkCloudPrintResult(result)
  valid_chars = u'-_.() abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789'
  ssd = u'{"state": {"type": "DONE"}}'
  if ((not sortorder) or (sortorder == u'CREATE_TIME_DESC')) and (older_or_newer == u'newer'):
    timeExit = True
  elif (sortorder == u'CREATE_TIME') and (older_or_newer == u'older'):
    timeExit = True
  else:
    timeExit = False
  jobCount = offset = 0
  while True:
    if jobLimit == 0:
      limit = PRINTJOBS_DEFAULT_MAX_RESULTS
    else:
      limit = min(PRINTJOBS_DEFAULT_MAX_RESULTS, jobLimit-jobCount)
      if limit == 0:
        break
    result = callGAPI(cp.jobs(), u'list',
                      printerid=printerid, q=query, status=status, sortorder=sortorder,
                      owner=owner, offset=offset, limit=limit)
    checkCloudPrintResult(result)
    newJobs = result[u'range'][u'jobsCount']
    totalJobs = int(result[u'range'][u'jobsTotal'])
    if newJobs == 0:
      break
    jobCount += newJobs
    offset += newJobs
    for job in result[u'jobs']:
      createTime = int(job[u'createTime'])/1000
      if older_or_newer:
        if older_or_newer == u'older' and createTime > age:
          if timeExit:
            jobCount = totalJobs
            break
          continue
        elif older_or_newer == u'newer' and createTime < age:
          if timeExit:
            jobCount = totalJobs
            break
          continue
      fileUrl = job[u'fileUrl']
      jobid = job[u'id']
      fileName = os.path.join(targetFolder, u'{0}-{1}'.format(u''.join(c if c in valid_chars else u'_' for c in job[u'title']), jobid))
      _, content = cp._http.request(uri=fileUrl, method='GET')
      if writeFile(fileName, content, continueOnError=True):
#        ticket = callGAPI(cp.jobs(), u'getticket', jobid=jobid, use_cjt=True)
        result = callGAPI(cp.jobs(), u'update', jobid=jobid, semantic_state_diff=ssd)
        checkCloudPrintResult(result)
        print u'Printed job %s to %s' % (jobid, fileName)
    if jobCount >= totalJobs:
      break
  if jobCount == 0:
    print u'No print jobs.'

def doDelPrinter():
  cp = buildGAPIObject(u'cloudprint')
  printerid = sys.argv[3]
  result = callGAPI(cp.printers(), u'delete', printerid=printerid)
  checkCloudPrintResult(result)

def doGetPrinterInfo():
  cp = buildGAPIObject(u'cloudprint')
  printerid = sys.argv[3]
  everything = False
  i = 4
  while i < len(sys.argv):
    myarg = sys.argv[i].lower()
    if myarg == u'everything':
      everything = True
      i += 1
    else:
      systemErrorExit(2, '%s is not a valid argument for "gam info printer"' % sys.argv[i])
  result = callGAPI(cp.printers(), u'get', printerid=printerid)
  checkCloudPrintResult(result)
  printer_info = result[u'printers'][0]
  createTime = int(printer_info[u'createTime'])/1000
  accessTime = int(printer_info[u'accessTime'])/1000
  updateTime = int(printer_info[u'updateTime'])/1000
  printer_info[u'createTime'] = datetime.datetime.fromtimestamp(createTime).strftime(u'%Y-%m-%d %H:%M:%S')
  printer_info[u'accessTime'] = datetime.datetime.fromtimestamp(accessTime).strftime(u'%Y-%m-%d %H:%M:%S')
  printer_info[u'updateTime'] = datetime.datetime.fromtimestamp(updateTime).strftime(u'%Y-%m-%d %H:%M:%S')
  printer_info[u'tags'] = u' '.join(printer_info[u'tags'])
  if not everything:
    del printer_info[u'capabilities']
    del printer_info[u'access']
  print_json(None, printer_info)

def doUpdatePrinter():
  cp = buildGAPIObject(u'cloudprint')
  printerid = sys.argv[3]
  kwargs = {}
  i = 4
  update_items = [u'isTosAccepted', u'gcpVersion', u'setupUrl',
                  u'quotaEnabled', u'id', u'supportUrl', u'firmware',
                  u'currentQuota', u'type', u'public', u'status', u'description',
                  u'defaultDisplayName', u'proxy', u'dailyQuota', u'manufacturer',
                  u'displayName', u'name', u'uuid', u'updateUrl', u'ownerId', u'model']
  while i < len(sys.argv):
    arg_in_item = False
    for item in update_items:
      if item.lower() == sys.argv[i].lower():
        kwargs[item] = sys.argv[i+1]
        i += 2
        arg_in_item = True
        break
    if not arg_in_item:
      systemErrorExit(2, '%s is not a valid argument for "gam update printer"' % sys.argv[i])
  result = callGAPI(cp.printers(), u'update', printerid=printerid, **kwargs)
  checkCloudPrintResult(result)
  print u'Updated printer %s' % printerid

def doPrinterRegister():
  cp = buildGAPIObject(u'cloudprint')
  form_fields = {u'name': u'GAM',
                 u'proxy': u'GAM',
                 u'uuid': _getValueFromOAuth(u'sub'),
                 u'manufacturer': gam_author,
                 u'model': u'cp1',
                 u'gcp_version': u'2.0',
                 u'setup_url': GAM_URL,
                 u'support_url': u'https://groups.google.com/forum/#!forum/google-apps-manager',
                 u'update_url': GAM_RELEASES,
                 u'firmware': gam_version,
                 u'semantic_state': {"version": "1.0", "printer": {"state": "IDLE",}},
                 u'use_cdd': True,
                 u'capabilities': {"version": "1.0",
                                   "printer": {"supported_content_type": [{"content_type": "application/pdf", "min_version": "1.5"},
                                                                          {"content_type": "image/jpeg"},
                                                                          {"content_type": "text/plain"}
                                                                         ],
                                               "copies": {"default": 1, "max": 100},
                                               "media_size": {"option": [{"name": "ISO_A4", "width_microns": 210000, "height_microns": 297000},
                                                                         {"name": "NA_LEGAL", "width_microns": 215900, "height_microns": 355600},
                                                                         {"name": "NA_LETTER", "width_microns": 215900, "height_microns": 279400, "is_default": True}
                                                                        ],
                                                             },
                                              },
                                  },
                 u'tags': [u'GAM', GAM_URL],
                }
  body, headers = encode_multipart(form_fields, {})
  #Get the printer first to make sure our OAuth access token is fresh
  callGAPI(cp.printers(), u'list')
  _, result = cp._http.request(uri='https://www.google.com/cloudprint/register', method='POST', body=body, headers=headers)
  result = json.loads(result)
  checkCloudPrintResult(result)
  print u'Created printer %s' % result[u'printers'][0][u'id']

def doPrintJobResubmit():
  cp = buildGAPIObject(u'cloudprint')
  jobid = sys.argv[2]
  printerid = sys.argv[4]
  ssd = u'{"state": {"type": "HELD"}}'
  result = callGAPI(cp.jobs(), u'update', jobid=jobid, semantic_state_diff=ssd)
  checkCloudPrintResult(result)
  ticket = callGAPI(cp.jobs(), u'getticket', jobid=jobid, use_cjt=True)
  result = callGAPI(cp.jobs(), u'resubmit', printerid=printerid, jobid=jobid, ticket=ticket)
  checkCloudPrintResult(result)
  print u'Success resubmitting %s as job %s to printer %s' % (jobid, result[u'job'][u'id'], printerid)

def doPrintJobSubmit():
  cp = buildGAPIObject(u'cloudprint')
  printer = sys.argv[2]
  content = sys.argv[4]
  form_fields = {u'printerid': printer,
                 u'title': content,
                 u'ticket': u'{"version": "1.0"}',
                 u'tags': [u'GAM', GAM_URL]}
  i = 5
  while i < len(sys.argv):
    myarg = sys.argv[i].lower()
    if myarg == u'tag':
      form_fields[u'tags'].append(sys.argv[i+1])
      i += 2
    elif myarg in [u'name', u'title']:
      form_fields[u'title'] = sys.argv[i+1]
      i += 2
    else:
      systemErrorExit(2, '%s is not a valid argument for "gam printer ... print"' % sys.argv[i])
  form_files = {}
  if content[:4] == u'http':
    form_fields[u'content'] = content
    form_fields[u'contentType'] = u'url'
  else:
    filepath = content
    content = os.path.basename(content)
    mimetype = mimetypes.guess_type(filepath)[0]
    if mimetype is None:
      mimetype = u'application/octet-stream'
    filecontent = readFile(filepath)
    form_files[u'content'] = {u'filename': content, u'content': filecontent, u'mimetype': mimetype}
  #result = callGAPI(cp.printers(), u'submit', body=body)
  body, headers = encode_multipart(form_fields, form_files)
  #Get the printer first to make sure our OAuth access token is fresh
  callGAPI(cp.printers(), u'get', printerid=printer)
  _, result = cp._http.request(uri='https://www.google.com/cloudprint/submit', method='POST', body=body, headers=headers)
  checkCloudPrintResult(result)
  if isinstance(result, str):
    result = json.loads(result)
  print u'Submitted print job %s' % result[u'job'][u'id']

def doDeletePrintJob():
  cp = buildGAPIObject(u'cloudprint')
  job = sys.argv[2]
  result = callGAPI(cp.jobs(), u'delete', jobid=job)
  checkCloudPrintResult(result)
  print u'Print Job %s deleted' % job

def doCancelPrintJob():
  cp = buildGAPIObject(u'cloudprint')
  job = sys.argv[2]
  ssd = u'{"state": {"type": "ABORTED", "user_action_cause": {"action_code": "CANCELLED"}}}'
  result = callGAPI(cp.jobs(), u'update', jobid=job, semantic_state_diff=ssd)
  checkCloudPrintResult(result)
  print u'Print Job %s cancelled' % job

def checkCloudPrintResult(result):
  if isinstance(result, str):
    try:
      result = json.loads(result)
    except ValueError:
      systemErrorExit(3, 'unexpected response: %s' % result)
  if not result[u'success']:
    systemErrorExit(result[u'errorCode'], '%s: %s' % (result[u'errorCode'], result[u'message']))

def formatACLRule(rule):
  if rule[u'scope'][u'type'] != u'default':
    return u'(Scope: {0}:{1}, Role: {2})'.format(rule[u'scope'][u'type'], rule[u'scope'][u'value'], rule[u'role'])
  return u'(Scope: {0}, Role: {1})'.format(rule[u'scope'][u'type'], rule[u'role'])

def doCalendarShowACL():
  calendarId, cal = buildCalendarDataGAPIObject(sys.argv[2])
  if not cal:
    return
  acls = callGAPIpages(cal.acl(), u'list', u'items', calendarId=calendarId, fields=u'nextPageToken,items(role,scope)')
  i = 0
  count = len(acls)
  for rule in acls:
    i += 1
    print u'Calendar: {0}, ACL: {1}{2}'.format(calendarId, formatACLRule(rule), currentCount(i, count))

def doCalendarAddACL(calendarId=None, act_as=None, role=None, scope=None, entity=None):
  if calendarId is None:
    calendarId = sys.argv[2]
  if not act_as:
    calendarId = normalizeCalendarId(calendarId)
    act_as = calendarId
  _, cal = buildCalendarDataGAPIObject(act_as)
  body = {u'scope': {}}
  if role is not None:
    body[u'role'] = role
  else:
    body[u'role'] = sys.argv[4].lower()
  if body[u'role'] not in [u'freebusy', u'read', u'reader', u'editor', u'writer', u'owner', u'none']:
    systemErrorExit(2, 'Role must be one of freebusy, reader, editor, writer, owner, none; got %s' % body[u'role'])
  if body[u'role'] == u'freebusy':
    body[u'role'] = u'freeBusyReader'
  elif body[u'role'] in [u'read', u'reader']:
    body[u'role'] = u'reader'
  elif body[u'role'] == u'editor':
    body[u'role'] = u'writer'
  if scope is not None:
    body[u'scope'][u'type'] = scope
  else:
    body[u'scope'][u'type'] = sys.argv[5].lower()
  i = 6
  if body[u'scope'][u'type'] not in [u'default', u'user', u'group', u'domain']:
    body[u'scope'][u'type'] = u'user'
    i = 5
  try:
    if entity is not None and body[u'scope'][u'type'] != u'default':
      body[u'scope'][u'value'] = entity
    else:
      body[u'scope'][u'value'] = sys.argv[i].lower()
    if (body[u'scope'][u'type'] in [u'user', u'group']) and body[u'scope'][u'value'].find(u'@') == -1:
      body[u'scope'][u'value'] = u'%s@%s' % (body[u'scope'][u'value'], GC_Values[GC_DOMAIN])
  except IndexError:
    pass
  if body[u'scope'][u'type'] == u'domain':
    try:
      body[u'scope'][u'value'] = sys.argv[6].lower()
    except IndexError:
      body[u'scope'][u'value'] = GC_Values[GC_DOMAIN]
  callGAPI(cal.acl(), u'insert', calendarId=calendarId, body=body)

def doCalendarUpdateACL():
  calendarId = sys.argv[2]
  role = sys.argv[4].lower()
  scope = sys.argv[5].lower()
  if len(sys.argv) > 6:
    entity = sys.argv[6].lower()
  else:
    entity = None
  doCalendarAddACL(calendarId=calendarId, role=role, scope=scope, entity=entity)

def doCalendarDelACL():
  calendarId = sys.argv[2]
  entity = sys.argv[5].lower()
  scope = u'user'
  if entity == u'domain':
    scope = u'domain'
  elif entity == u'default':
    scope = u'default'
    entity = u''
  doCalendarAddACL(calendarId=calendarId, role=u'none', scope=scope, entity=entity)

def doCalendarWipeData():
  calendarId, cal = buildCalendarDataGAPIObject(sys.argv[2])
  if not cal:
    return
  callGAPI(cal.calendars(), u'clear', calendarId=calendarId)

def doCalendarDeleteEvent():
  calendarId, cal = buildCalendarDataGAPIObject(sys.argv[2])
  if not cal:
    return
  events = []
  sendNotifications = None
  doit = False
  i = 4
  while i < len(sys.argv):
    myarg = sys.argv[i].lower().replace(u'_', u'')
    if myarg == u'notifyattendees':
      sendNotifications = True
      i += 1
    elif myarg in [u'id', u'eventid']:
      events.append(sys.argv[i+1])
      i += 2
    elif myarg in [u'query', u'eventquery']:
      query = sys.argv[i+1]
      result = callGAPIpages(cal.events(), u'list', u'items', calendarId=calendarId, q=query)
      for event in result:
        if u'id' in event and event[u'id'] not in events:
          events.append(event[u'id'])
      i += 2
    elif myarg == u'doit':
      doit = True
      i += 1
    else:
      systemErrorExit(2, '%s is not a valid argument for "gam calendar <email> deleteevent"' % sys.argv[i])
  if doit:
    for eventId in events:
      print u' deleting eventId %s' % eventId
      callGAPI(cal.events(), u'delete', calendarId=calendarId, eventId=eventId, sendNotifications=sendNotifications)
  else:
    for eventId in events:
      print u' would delete eventId %s. Add doit to command to actually delete event' % eventId

def doCalendarAddEvent():
  calendarId, cal = buildCalendarDataGAPIObject(sys.argv[2])
  if not cal:
    return
  sendNotifications = timeZone = None
  i = 4
  body = {}
  while i < len(sys.argv):
    myarg = sys.argv[i].lower().replace(u'_', u'')
    if myarg == u'notifyattendees':
      sendNotifications = True
      i += 1
    elif myarg == u'attendee':
      try:
        body[u'attendees'].append({u'email': sys.argv[i+1]})
      except KeyError:
        body[u'attendees'] = [{u'email': sys.argv[i+1]},]
      i += 2
    elif myarg == u'optionalattendee':
      try:
        body[u'attendees'].append({u'email': sys.argv[i+1], u'optional': True})
      except TypeError:
        body[u'attendees'] = [{u'email': sys.argv[i+1], u'optional': True},]
      i += 2
    elif myarg == u'anyonecanaddself':
      body[u'anyoneCanAddSelf'] = True
      i += 1
    elif myarg == u'description':
      body[u'description'] = sys.argv[i+1].replace(u'\\n', u'\n')
      i += 2
    elif myarg == u'start':
      if sys.argv[i+1].lower() == u'allday':
        body[u'start'] = {u'date': getYYYYMMDD(sys.argv[i+2])}
        i += 3
      else:
        body[u'start'] = {u'dateTime': getTimeOrDeltaFromNow(sys.argv[i+1])}
        i += 2
    elif myarg == u'end':
      if sys.argv[i+1].lower() == u'allday':
        body[u'end'] = {u'date': getYYYYMMDD(sys.argv[i+2])}
        i += 3
      else:
        body[u'end'] = {u'dateTime': getTimeOrDeltaFromNow(sys.argv[i+1])}
        i += 2
    elif myarg == u'guestscantinviteothers':
      body[u'guestsCanInviteOthers'] = False
      i += 1
    elif myarg == u'guestscantseeothers':
      body[u'guestsCanSeeOtherGuests'] = False
      i += 1
    elif myarg == u'id':
      body[u'id'] = sys.argv[i+1]
      i += 2
    elif myarg == u'summary':
      body[u'summary'] = sys.argv[i+1]
      i += 2
    elif myarg == u'location':
      body[u'location'] = sys.argv[i+1]
      i += 2
    elif myarg == u'available':
      body[u'transparency'] = u'transparent'
      i += 1
    elif myarg == u'visibility':
      if sys.argv[i+1].lower() in [u'default', u'public', u'private']:
        body[u'visibility'] = sys.argv[i+1].lower()
      else:
        systemErrorExit(2, 'visibility must be one of default, public, private; got %s' % sys.argv[i+1])
      i += 2
    elif myarg == u'tentative':
      body[u'status'] = u'tentative'
      i += 1
    elif myarg == u'source':
      body[u'source'] = {u'title': sys.argv[i+1], u'url': sys.argv[i+2]}
      i += 3
    elif myarg == u'noreminders':
      body[u'reminders'] = {u'useDefault': False}
      i += 1
    elif myarg == u'reminder':
      try:
        body[u'reminders'][u'overrides'].append({u'minutes': sys.argv[i+1], u'method': sys.argv[i+2]})
        body[u'reminders'][u'useDefault'] = False
      except KeyError:
        body[u'reminders'] = {u'useDefault': False, u'overrides': [{u'minutes': sys.argv[i+1], u'method': sys.argv[i+2]},]}
      i += 3
    elif myarg == u'recurrence':
      try:
        body[u'recurrence'].append(sys.argv[i+1])
      except KeyError:
        body[u'recurrence'] = [sys.argv[i+1],]
      i += 2
    elif myarg == u'timezone':
      timeZone = sys.argv[i+1]
      i += 2
    elif myarg == u'privateproperty':
      if u'extendedProperties' not in body:
        body[u'extendedProperties'] = {u'private': {}, u'shared': {}}
      body[u'extendedProperties'][u'private'][sys.argv[i+1]] = sys.argv[i+2]
      i += 3
    elif myarg == u'sharedproperty':
      if u'extendedProperties' not in body:
        body[u'extendedProperties'] = {u'private': {}, u'shared': {}}
      body[u'extendedProperties'][u'shared'][sys.argv[i+1]] = sys.argv[i+2]
      i += 3
    elif myarg == u'colorindex':
      body[u'colorId'] = str(sys.argv[i+1])
      i += 2
    else:
      systemErrorExit(2, '%s is not a valid argument for "gam calendar <email> addevent"' % sys.argv[i])
  if not timeZone and u'recurrence' in body:
    timeZone = callGAPI(cal.calendars(), u'get', calendarId=calendarId, fields=u'timeZone')[u'timeZone']
  if u'recurrence' in body:
    for a_time in [u'start', u'end']:
      try:
        body[a_time][u'timeZone'] = timeZone
      except KeyError:
        pass
  callGAPI(cal.events(), u'insert', calendarId=calendarId, sendNotifications=sendNotifications, body=body)

def doProfile(users):
  cd = buildGAPIObject(u'directory')
  myarg = sys.argv[4].lower()
  if myarg in [u'share', u'shared']:
    body = {u'includeInGlobalAddressList': True}
  elif myarg in [u'unshare', u'unshared']:
    body = {u'includeInGlobalAddressList': False}
  else:
    systemErrorExit(2, 'value for "gam <users> profile" must be true or false; got %s' % sys.argv[4])
  i = 0
  count = len(users)
  for user in users:
    i += 1
    print u'Setting Profile Sharing to %s for %s (%s/%s)' % (body[u'includeInGlobalAddressList'], user, i, count)
    callGAPI(cd.users(), u'update', soft_errors=True, userKey=user, body=body)

def showProfile(users):
  cd = buildGAPIObject(u'directory')
  i = 0
  count = len(users)
  for user in users:
    i += 1
    result = callGAPI(cd.users(), u'get', userKey=user, fields=u'includeInGlobalAddressList')
    try:
      print u'User: %s  Profile Shared: %s (%s/%s)' % (user, result[u'includeInGlobalAddressList'], i, count)
    except IndexError:
      pass

def doPhoto(users):
  cd = buildGAPIObject(u'directory')
  i = 0
  count = len(users)
  for user in users:
    i += 1
    filename = sys.argv[5].replace(u'#user#', user)
    filename = filename.replace(u'#email#', user)
    filename = filename.replace(u'#username#', user[:user.find(u'@')])
    print u"Updating photo for %s with %s (%s/%s)" % (user, filename, i, count)
    if re.match(u'^(ht|f)tps?://.*$', filename):
      simplehttp = httplib2.Http(disable_ssl_certificate_validation=GC_Values[GC_NO_VERIFY_SSL])
      try:
        (_, f) = simplehttp.request(filename, u'GET')
        image_data = str(f)
      except (httplib2.HttpLib2Error, httplib2.ServerNotFoundError, httplib2.CertificateValidationUnsupported) as e:
        print e
        continue
    else:
      image_data = readFile(filename, continueOnError=True, displayError=True)
      if image_data is None:
        continue
    image_data = base64.urlsafe_b64encode(image_data)
    body = {u'photoData': image_data}
    callGAPI(cd.users().photos(), u'update', soft_errors=True, userKey=user, body=body)

def getPhoto(users):
  cd = buildGAPIObject(u'directory')
  targetFolder = os.getcwd()
  showPhotoData = True
  i = 5
  while i < len(sys.argv):
    myarg = sys.argv[i].lower().replace(u'_', u'')
    if myarg == u'drivedir':
      targetFolder = GC_Values[GC_DRIVE_DIR]
      i += 1
    elif myarg == u'targetfolder':
      targetFolder = os.path.expanduser(sys.argv[i+1])
      if not os.path.isdir(targetFolder):
        os.makedirs(targetFolder)
      i += 2
    elif myarg == u'noshow':
      showPhotoData = False
      i += 1
    else:
      systemErrorExit(2, '%s is not a valid argument for "gam <users> get photo"' % sys.argv[i])
  i = 0
  count = len(users)
  for user in users:
    i += 1
    filename = os.path.join(targetFolder, u'{0}.jpg'.format(user))
    print u"Saving photo to %s (%s/%s)" % (filename, i, count)
    try:
      photo = callGAPI(cd.users().photos(), u'get', throw_reasons=[GAPI_USER_NOT_FOUND, GAPI_RESOURCE_NOT_FOUND], userKey=user)
    except GAPI_userNotFound:
      print u' unknown user %s' % user
      continue
    except GAPI_resourceNotFound:
      print u' no photo for %s' % user
      continue
    try:
      photo_data = str(photo[u'photoData'])
      if showPhotoData:
        print photo_data
      photo_data = base64.urlsafe_b64decode(photo_data)
    except KeyError:
      print u' no photo for %s' % user
      continue
    writeFile(filename, photo_data, continueOnError=True)

def deletePhoto(users):
  cd = buildGAPIObject(u'directory')
  i = 0
  count = len(users)
  for user in users:
    i += 1
    print u"Deleting photo for %s (%s/%s)" % (user, i, count)
    callGAPI(cd.users().photos(), u'delete', userKey=user)

def _showCalendar(userCalendar, j, jcount):
  print u'  Calendar: {0} ({1}/{2})'.format(userCalendar[u'id'], j, jcount)
  print utils.convertUTF8(u'    Summary: {0}'.format(userCalendar.get(u'summaryOverride', userCalendar[u'summary'])))
  print utils.convertUTF8(u'    Description: {0}'.format(userCalendar.get(u'description', u'')))
  print u'    Access Level: {0}'.format(userCalendar[u'accessRole'])
  print u'    Timezone: {0}'.format(userCalendar[u'timeZone'])
  print utils.convertUTF8(u'    Location: {0}'.format(userCalendar.get(u'location', u'')))
  print u'    Hidden: {0}'.format(userCalendar.get(u'hidden', u'False'))
  print u'    Selected: {0}'.format(userCalendar.get(u'selected', u'False'))
  print u'    Color ID: {0}, Background Color: {1}, Foreground Color: {2}'.format(userCalendar[u'colorId'], userCalendar[u'backgroundColor'], userCalendar[u'foregroundColor'])
  print u'    Default Reminders:'
  for reminder in userCalendar.get(u'defaultReminders', []):
    print u'      Method: {0}, Minutes: {1}'.format(reminder[u'method'], reminder[u'minutes'])
  print u'    Notifications:'
  if u'notificationSettings' in userCalendar:
    for notification in userCalendar[u'notificationSettings'].get(u'notifications', []):
      print u'      Method: {0}, Type: {1}'.format(notification[u'method'], notification[u'type'])

def infoCalendar(users):
  calendarId = normalizeCalendarId(sys.argv[5], checkPrimary=True)
  i = 0
  count = len(users)
  for user in users:
    i += 1
    user, cal = buildCalendarGAPIObject(user)
    if not cal:
      continue
    result = callGAPI(cal.calendarList(), u'get',
                      soft_errors=True,
                      calendarId=calendarId)
    if result:
      print u'User: {0}, Calendar: ({1}/{2})'.format(user, i, count)
      _showCalendar(result, 1, 1)

def printShowCalendars(users, csvFormat):
  if csvFormat:
    todrive = False
    titles = []
    csvRows = []
  i = 5
  while i < len(sys.argv):
    myarg = sys.argv[i].lower()
    if csvFormat and myarg == u'todrive':
      todrive = True
      i += 1
    else:
      systemErrorExit(2, '%s is not a valid argument for "gam <users> %s calendars"' %  (myarg, [u'show', u'print'][csvFormat]))
  i = 0
  count = len(users)
  for user in users:
    i += 1
    user, cal = buildCalendarGAPIObject(user)
    if not cal:
      continue
    result = callGAPIpages(cal.calendarList(), u'list', u'items', soft_errors=True)
    jcount = len(result)
    if not csvFormat:
      print u'User: {0}, Calendars: ({1}/{2})'.format(user, i, count)
      if jcount == 0:
        continue
      j = 0
      for userCalendar in result:
        j += 1
        _showCalendar(userCalendar, j, jcount)
    else:
      if jcount == 0:
        continue
      for userCalendar in result:
        row = {u'primaryEmail': user}
        addRowTitlesToCSVfile(flatten_json(userCalendar, flattened=row), csvRows, titles)
  if csvFormat:
    sortCSVTitles([u'primaryEmail', u'id'], titles)
    writeCSVfile(csvRows, titles, u'Calendars', todrive)

def showCalSettings(users):
  i = 0
  count = len(users)
  for user in users:
    i += 1
    user, cal = buildCalendarGAPIObject(user)
    if not cal:
      continue
    feed = callGAPIpages(cal.settings(), u'list', u'items', soft_errors=True)
    if feed:
      print u'User: {0}, Calendar Settings: ({1}/{2})'.format(user, i, count)
      settings = {}
      for setting in feed:
        settings[setting[u'id']] = setting[u'value']
      for attr, value in sorted(settings.items()):
        print u'  {0}: {1}'.format(attr, value)

def printDriveSettings(users):
  todrive = False
  i = 5
  while i < len(sys.argv):
    myarg = sys.argv[i].lower()
    if myarg == u'todrive':
      todrive = True
      i += 1
    else:
      systemErrorExit(2, '%s is not a valid argument for "gam <users> show drivesettings"' % sys.argv[i])
  dont_show = [u'kind', u'exportFormats', u'importFormats', u'maxUploadSize', u'maxImportSizes', u'user', u'appInstalled']
  csvRows = []
  titles = [u'email',]
  i = 0
  count = len(users)
  for user in users:
    i += 1
    user, drive = buildDrive3GAPIObject(user)
    if not drive:
      continue
    sys.stderr.write(u'Getting Drive settings for %s (%s/%s)\n' % (user, i, count))
    feed = callGAPI(drive.about(), u'get', fields=u'*', soft_errors=True)
    if feed is None:
      continue
    row = {u'email': user}
    for setting in feed:
      if setting in dont_show:
        continue
      if setting == u'storageQuota':
        for subsetting, value in feed[setting].iteritems():
          row[subsetting] = u'%smb' % (int(value) / 1024 / 1024)
          if subsetting not in titles:
            titles.append(subsetting)
        continue
      row[setting] = feed[setting]
      if setting not in titles:
        titles.append(setting)
    csvRows.append(row)
  writeCSVfile(csvRows, titles, u'User Drive Settings', todrive)

def getTeamDriveThemes(users):
  for user in users:
    user, drive = buildDrive3GAPIObject(user)
    if not drive:
      continue
    themes = callGAPI(drive.about(), u'get', fields=u'teamDriveThemes', soft_errors=True)
    if themes is None or u'teamDriveThemes' not in themes:
      continue
    print u'theme'
    for theme in themes[u'teamDriveThemes']:
      print theme[u'id']

def printDriveActivity(users):
  drive_ancestorId = u'root'
  drive_fileId = None
  todrive = False
  titles = [u'user.name', u'user.permissionId', u'target.id', u'target.name', u'target.mimeType']
  csvRows = []
  i = 5
  while i < len(sys.argv):
    activity_object = sys.argv[i].lower().replace(u'_', u'')
    if activity_object == u'fileid':
      drive_fileId = sys.argv[i+1]
      drive_ancestorId = None
      i += 2
    elif activity_object == u'folderid':
      drive_ancestorId = sys.argv[i+1]
      i += 2
    elif activity_object == u'todrive':
      todrive = True
      i += 1
    else:
      systemErrorExit(2, '%s is not a valid argument for "gam <users> show driveactivity"' % sys.argv[i])
  for user in users:
    user, activity = buildActivityGAPIObject(user)
    if not activity:
      continue
    page_message = u'Retrieved %%%%total_items%%%% activities for %s' % user
    feed = callGAPIpages(activity.activities(), u'list', u'activities',
                         page_message=page_message, source=u'drive.google.com', userId=u'me',
                         drive_ancestorId=drive_ancestorId, groupingStrategy=u'none',
                         drive_fileId=drive_fileId, pageSize=GC_Values[GC_ACTIVITY_MAX_RESULTS])
    for item in feed:
      addRowTitlesToCSVfile(flatten_json(item[u'combinedEvent']), csvRows, titles)
  writeCSVfile(csvRows, titles, u'Drive Activity', todrive)

def printPermission(permission):
  if u'name' in permission:
    print utils.convertUTF8(permission[u'name'])
  elif u'id' in permission:
    if permission[u'id'] == u'anyone':
      print u'Anyone'
    elif permission[u'id'] == u'anyoneWithLink':
      print u'Anyone with Link'
    else:
      print permission[u'id']
  for key in permission:
    if key in [u'name', u'kind', u'etag', u'selfLink',]:
      continue
    print utils.convertUTF8(u' %s: %s' % (key, permission[key]))

def showDriveFileACL(users):
  fileId = sys.argv[5]
  useDomainAdminAccess = False
  i = 6
  while i < len(sys.argv):
    myarg = sys.argv[i].lower().replace(u'_', u'')
    if myarg == u'asadmin':
      useDomainAdminAccess = True
      i += 1
    else:
      systemErrorExit(3, '%s is not a valid argument to "gam <users> show drivefileacl".' % sys.argv[i])
  for user in users:
    user, drive = buildDrive3GAPIObject(user)
    if not drive:
      continue
    feed = callGAPIpages(drive.permissions(), u'list', u'permissions',
                         fileId=fileId, fields=u'*', supportsTeamDrives=True,
                         useDomainAdminAccess=useDomainAdminAccess)
    for permission in feed:
      printPermission(permission)
      print u''

def getPermissionId(argstr):
  permissionId = argstr.strip().lower()
  if permissionId[:3] == u'id:':
    return argstr.strip()[3:]
  if permissionId == u'anyone':
    return u'anyone'
  if permissionId == u'anyonewithlink':
    return u'anyoneWithLink'
  if permissionId.find(u'@') == -1:
    permissionId = u'%s@%s' % (permissionId, GC_Values[GC_DOMAIN])
  # We have to use v2 here since v3 has no permissions.getIdForEmail equivalent
  # https://code.google.com/a/google.com/p/apps-api-issues/issues/detail?id=4313
  _, drive2 = buildDriveGAPIObject(_getValueFromOAuth(u'email'))
  return callGAPI(drive2.permissions(), u'getIdForEmail', email=permissionId, fields=u'id')[u'id']

def delDriveFileACL(users):
  fileId = sys.argv[5]
  permissionId = getPermissionId(sys.argv[6])
  useDomainAdminAccess = False
  i = 7
  while i < len(sys.argv):
    myarg = sys.argv[i].lower().replace(u'_', u'')
    if myarg == u'asadmin':
      useDomainAdminAccess = True
      i += 1
    else:
      systemErrorExit(3, '%s is not a valid argument to "gam <users> delete drivefileacl".' % sys.argv[i])
  for user in users:
    user, drive = buildDrive3GAPIObject(user)
    if not drive:
      continue
    print u'Removing permission for %s from %s' % (permissionId, fileId)
    callGAPI(drive.permissions(), u'delete', fileId=fileId,
             permissionId=permissionId, supportsTeamDrives=True,
             useDomainAdminAccess=useDomainAdminAccess)

def addDriveFileACL(users):
  fileId = sys.argv[5]
  body = {u'type': sys.argv[6].lower()}
  sendNotificationEmail = False
  emailMessage = None
  transferOwnership = None
  useDomainAdminAccess = False
  if body[u'type'] == u'anyone':
    i = 7
  elif body[u'type'] in [u'user', u'group']:
    body[u'emailAddress'] = normalizeEmailAddressOrUID(sys.argv[7])
    i = 8
  elif body[u'type'] == u'domain':
    body[u'domain'] = sys.argv[7]
    i = 8
  else:
    systemErrorExit(5, 'permission type must be user, group domain or anyone; got %s' % body[u'type'])
  while i < len(sys.argv):
    myarg = sys.argv[i].lower().replace(u'_', u'')
    if myarg == u'withlink':
      body[u'allowFileDiscovery'] = False
      i += 1
    elif myarg == u'discoverable':
      body[u'allowFileDiscovery'] = True
      i += 1
    elif myarg == u'role':
      body[u'role'] = sys.argv[i+1]
      if body[u'role'] not in [u'reader', u'commenter', u'writer', u'owner', u'organizer', u'editor']:
        systemErrorExit(2, 'role must be reader, commenter, writer, organizer, or owner; got %s' % body[u'role'])
      if body[u'role'] == u'editor':
        body[u'role'] = u'writer'
      elif body[u'role'] == u'owner':
        sendNotificationEmail = True
        transferOwnership = True
      i += 2
    elif myarg == u'sendemail':
      sendNotificationEmail = True
      i += 1
    elif myarg == u'emailmessage':
      sendNotificationEmail = True
      emailMessage = sys.argv[i+1]
      i += 2
    elif myarg == u'expires':
      body[u'expirationTime'] = getTimeOrDeltaFromNow(sys.argv[i+1])
      i += 2
    elif myarg == u'asadmin':
      useDomainAdminAccess = True
      i += 1
    else:
      systemErrorExit(2, '%s is not a valid argument for "gam <users> add drivefileacl"' % sys.argv[i])
  for user in users:
    user, drive = buildDrive3GAPIObject(user)
    if not drive:
      continue
    result = callGAPI(drive.permissions(), u'create', fields=u'*',
                      fileId=fileId, sendNotificationEmail=sendNotificationEmail,
                      emailMessage=emailMessage, body=body, supportsTeamDrives=True,
                      transferOwnership=transferOwnership,
                      useDomainAdminAccess=useDomainAdminAccess)
    printPermission(result)

def updateDriveFileACL(users):
  fileId = sys.argv[5]
  permissionId = getPermissionId(sys.argv[6])
  transferOwnership = None
  removeExpiration = None
  useDomainAdminAccess = False
  body = {}
  i = 7
  while i < len(sys.argv):
    myarg = sys.argv[i].lower().replace(u'_', u'')
    if myarg == u'withlink':
      body[u'allowFileDiscovery'] = False
      i += 1
    elif myarg == u'discoverable':
      body[u'allowFileDiscovery'] = True
      i += 1
    elif myarg == u'removeexpiration':
      removeExpiration = True
      i += 1
    elif myarg == u'role':
      body[u'role'] = sys.argv[i+1]
      if body[u'role'] not in [u'reader', u'commenter', u'writer', u'owner', u'organizer', u'editor']:
        systemErrorExit(2, 'role must be reader, commenter, writer, organizer, or owner; got %s' % body[u'role'])
      if body[u'role'] == u'editor':
        body[u'role'] = u'writer'
      elif body[u'role'] == u'owner':
        transferOwnership = True
      i += 2
    elif myarg == u'asadmin':
      useDomainAdminAccess = True
      i += 1
    else:
      systemErrorExit(2, '%s is not a valid argument for "gam <users> update drivefileacl"' % sys.argv[i])
  for user in users:
    user, drive = buildDrive3GAPIObject(user)
    if not drive:
      continue
    print u'updating permissions for %s to file %s' % (permissionId, fileId)
    result = callGAPI(drive.permissions(), u'update', fields=u'*',
                      fileId=fileId, permissionId=permissionId, removeExpiration=removeExpiration,
                      transferOwnership=transferOwnership, body=body,
                      supportsTeamDrives=True, useDomainAdminAccess=useDomainAdminAccess)
    printPermission(result)

def _stripMeInOwners(query):
  if not query:
    return query
  if query == u"'me' in owners":
    return None
  if query.startswith(u"'me' in owners and "):
    return query[len(u"'me' in owners and "):]
  return query

def printDriveFileList(users):
  allfields = anyowner = todrive = False
  fieldsList = []
  fieldsTitles = {}
  labelsList = []
  orderByList = []
  titles = [u'Owner',]
  csvRows = []
  query = u"'me' in owners"
  i = 5
  while i < len(sys.argv):
    myarg = sys.argv[i].lower().replace(u'_', u'')
    if myarg == u'todrive':
      todrive = True
      i += 1
    elif myarg == u'orderby':
      fieldName = sys.argv[i+1].lower()
      i += 2
      if fieldName in DRIVEFILE_ORDERBY_CHOICES_MAP:
        fieldName = DRIVEFILE_ORDERBY_CHOICES_MAP[fieldName]
        orderBy = u''
        if i < len(sys.argv):
          orderBy = sys.argv[i].lower()
          if orderBy in SORTORDER_CHOICES_MAP:
            orderBy = SORTORDER_CHOICES_MAP[orderBy]
            i += 1
        if orderBy != u'DESCENDING':
          orderByList.append(fieldName)
        else:
          orderByList.append(u'{0} desc'.format(fieldName))
      else:
        systemErrorExit(2, 'orderby must be one of {0}; got {1}'.format(u', '.join(sorted(DRIVEFILE_ORDERBY_CHOICES_MAP.keys())), fieldName))
    elif myarg == u'query':
      query += u' and %s' % sys.argv[i+1]
      i += 2
    elif myarg == u'fullquery':
      query = sys.argv[i+1]
      i += 2
    elif myarg == u'anyowner':
      anyowner = True
      i += 1
    elif myarg == u'allfields':
      fieldsList = []
      allfields = True
      i += 1
    elif myarg in DRIVEFILE_FIELDS_CHOICES_MAP:
      addFieldToCSVfile(myarg, {myarg: [DRIVEFILE_FIELDS_CHOICES_MAP[myarg]]}, fieldsList, fieldsTitles, titles)
      i += 1
    elif myarg in DRIVEFILE_LABEL_CHOICES_MAP:
      addFieldToCSVfile(myarg, {myarg: [DRIVEFILE_LABEL_CHOICES_MAP[myarg]]}, labelsList, fieldsTitles, titles)
      i += 1
    else:
      systemErrorExit(2, '%s is not a valid argument for "gam <users> show filelist"' % myarg)
  if fieldsList or labelsList:
    fields = u'nextPageToken,items('
    if fieldsList:
      fields += u','.join(set(fieldsList))
      if labelsList:
        fields += u','
    if labelsList:
      fields += u'labels({0})'.format(u','.join(set(labelsList)))
    fields += u')'
  elif not allfields:
    for field in [u'name', u'alternatelink']:
      addFieldToCSVfile(field, {field: [DRIVEFILE_FIELDS_CHOICES_MAP[field]]}, fieldsList, fieldsTitles, titles)
    fields = u'nextPageToken,items({0})'.format(u','.join(set(fieldsList)))
  else:
    fields = u'*'
  if orderByList:
    orderBy = u','.join(orderByList)
  else:
    orderBy = None
  if anyowner:
    query = _stripMeInOwners(query)
  for user in users:
    user, drive = buildDriveGAPIObject(user)
    if not drive:
      continue
    sys.stderr.write(u'Getting files for %s...\n' % user)
    page_message = u' got %%%%total_items%%%% files for %s...\n' % user
    feed = callGAPIpages(drive.files(), u'list', u'items',
                         page_message=page_message, soft_errors=True,
                         q=query, orderBy=orderBy, fields=fields, maxResults=GC_Values[GC_DRIVE_MAX_RESULTS])
    for f_file in feed:
      a_file = {u'Owner': user}
      for attrib in f_file:
        if attrib in [u'kind', u'etag']:
          continue
        if not isinstance(f_file[attrib], dict):
          if isinstance(f_file[attrib], list):
            if f_file[attrib]:
              if isinstance(f_file[attrib][0], (str, unicode, int, bool)):
                if attrib not in titles:
                  titles.append(attrib)
                a_file[attrib] = u' '.join(f_file[attrib])
              else:
                for j, l_attrib in enumerate(f_file[attrib]):
                  for list_attrib in l_attrib:
                    if list_attrib in [u'kind', u'etag', u'selfLink']:
                      continue
                    x_attrib = u'{0}.{1}.{2}'.format(attrib, j, list_attrib)
                    if x_attrib not in titles:
                      titles.append(x_attrib)
                    a_file[x_attrib] = l_attrib[list_attrib]
          elif isinstance(f_file[attrib], (str, unicode, int, bool)):
            if attrib not in titles:
              titles.append(attrib)
            a_file[attrib] = f_file[attrib]
          else:
            sys.stderr.write(u'File ID: {0}, Attribute: {1}, Unknown type: {2}\n'.format(f_file[u'id'], attrib, type(f_file[attrib])))
        elif attrib == u'labels':
          for dict_attrib in f_file[attrib]:
            if dict_attrib not in titles:
              titles.append(dict_attrib)
            a_file[dict_attrib] = f_file[attrib][dict_attrib]
        else:
          for dict_attrib in f_file[attrib]:
            if dict_attrib in [u'kind', u'etag']:
              continue
            x_attrib = u'{0}.{1}'.format(attrib, dict_attrib)
            if x_attrib not in titles:
              titles.append(x_attrib)
            a_file[x_attrib] = f_file[attrib][dict_attrib]
      csvRows.append(a_file)
  if allfields:
    sortCSVTitles([u'Owner', u'id', u'title'], titles)
  writeCSVfile(csvRows, titles, u'%s %s Drive Files' % (sys.argv[1], sys.argv[2]), todrive)

def doDriveSearch(drive, query=None):
  print u'Searching for files with query: "%s"...' % query
  page_message = u' got %%total_items%% files...\n'
  files = callGAPIpages(drive.files(), u'list', u'items',
                        page_message=page_message,
                        q=query, fields=u'nextPageToken,items(id)', maxResults=GC_Values[GC_DRIVE_MAX_RESULTS])
  ids = list()
  for f_file in files:
    ids.append(f_file[u'id'])
  return ids

def getFileIdFromAlternateLink(altLink):
  loc = altLink.find(u'/d/')
  if loc > 0:
    fileId = altLink[loc+3:]
    loc = fileId.find(u'/')
    if loc != -1:
      return fileId[:loc]
  else:
    loc = altLink.find(u'/folderview?id=')
    if loc > 0:
      fileId = altLink[loc+15:]
      loc = fileId.find(u'&')
      if loc != -1:
        return fileId[:loc]
  systemErrorExit(2, '%s is not a valid Drive File alternateLink' % altLink)

def deleteDriveFile(users):
  fileIds = sys.argv[5]
  function = u'trash'
  i = 6
  while i < len(sys.argv):
    myarg = sys.argv[i].lower()
    if myarg == u'purge':
      function = u'delete'
      i += 1
    elif myarg == u'untrash':
      function = u'untrash'
      i += 1
    else:
      systemErrorExit(2, '%s is not a valid argument for "gam <users> delete drivefile"' % sys.argv[i])
  action = DELETE_DRIVEFILE_FUNCTION_TO_ACTION_MAP[function]
  for user in users:
    user, drive = buildDriveGAPIObject(user)
    if not drive:
      continue
    if fileIds[:6].lower() == u'query:':
      file_ids = doDriveSearch(drive, query=fileIds[6:])
    else:
      if fileIds[:8].lower() == u'https://' or fileIds[:7].lower() == u'http://':
        fileIds = getFileIdFromAlternateLink(fileIds)
      file_ids = [fileIds,]
    if not file_ids:
      print u'No files to %s for %s' % (function, user)
    i = 0
    for fileId in file_ids:
      i += 1
      print u'%s %s for %s (%s/%s)' % (action, fileId, user, i, len(file_ids))
      callGAPI(drive.files(), function, fileId=fileId, supportsTeamDrives=True)

def printDriveFolderContents(feed, folderId, indent):
  for f_file in feed:
    for parent in f_file[u'parents']:
      if folderId == parent[u'id']:
        print u' ' * indent, utils.convertUTF8(f_file[u'title'])
        if f_file[u'mimeType'] == u'application/vnd.google-apps.folder':
          printDriveFolderContents(feed, f_file[u'id'], indent+1)
        break

def showDriveFileTree(users):
  anyowner = False
  orderByList = []
  query = u"'me' in owners"
  i = 5
  while i < len(sys.argv):
    myarg = sys.argv[i].lower().replace(u'_', u'')
    if myarg == u'anyowner':
      anyowner = True
      i += 1
    elif myarg == u'orderby':
      fieldName = sys.argv[i+1].lower()
      i += 2
      if fieldName in DRIVEFILE_ORDERBY_CHOICES_MAP:
        fieldName = DRIVEFILE_ORDERBY_CHOICES_MAP[fieldName]
        orderBy = u''
        if i < len(sys.argv):
          orderBy = sys.argv[i].lower()
          if orderBy in SORTORDER_CHOICES_MAP:
            orderBy = SORTORDER_CHOICES_MAP[orderBy]
            i += 1
        if orderBy != u'DESCENDING':
          orderByList.append(fieldName)
        else:
          orderByList.append(u'{0} desc'.format(fieldName))
      else:
        systemErrorExit(2, 'orderby must be one of {0}; got {1}'.format(u', '.join(sorted(DRIVEFILE_ORDERBY_CHOICES_MAP.keys())), fieldName))
    else:
      systemErrorExit(2, '%s is not a valid argument for "gam <users> show filetree"' % myarg)
  if orderByList:
    orderBy = u','.join(orderByList)
  else:
    orderBy = None
  if anyowner:
    query = _stripMeInOwners(query)
  for user in users:
    user, drive = buildDriveGAPIObject(user)
    if not drive:
      continue
    root_folder = callGAPI(drive.about(), u'get', fields=u'rootFolderId')[u'rootFolderId']
    sys.stderr.write(u'Getting all files for %s...\n' % user)
    page_message = u' got %%%%total_items%%%% files for %s...\n' % user
    feed = callGAPIpages(drive.files(), u'list', u'items', page_message=page_message,
                         q=query, orderBy=orderBy, fields=u'items(id,title,parents(id),mimeType),nextPageToken', maxResults=GC_Values[GC_DRIVE_MAX_RESULTS])
    printDriveFolderContents(feed, root_folder, 0)

def deleteEmptyDriveFolders(users):
  query = u'"me" in owners and mimeType = "application/vnd.google-apps.folder"'
  for user in users:
    user, drive = buildDriveGAPIObject(user)
    if not drive:
      continue
    deleted_empty = True
    while deleted_empty:
      sys.stderr.write(u'Getting folders for %s...\n' % user)
      page_message = u' got %%%%total_items%%%% folders for %s...\n' % user
      feed = callGAPIpages(drive.files(), u'list', u'items', page_message=page_message,
                           q=query, fields=u'items(title,id),nextPageToken', maxResults=GC_Values[GC_DRIVE_MAX_RESULTS])
      deleted_empty = False
      for folder in feed:
        children = callGAPI(drive.children(), u'list',
                            folderId=folder[u'id'], fields=u'items(id)', maxResults=1)
        if not u'items' in children or len(children[u'items']) == 0:
          print utils.convertUTF8(u' deleting empty folder %s...' % folder[u'title'])
          callGAPI(drive.files(), u'delete', fileId=folder[u'id'])
          deleted_empty = True
        else:
          print utils.convertUTF8(u' not deleting folder %s because it contains at least 1 item (%s)' % (folder[u'title'], children[u'items'][0][u'id']))

def doEmptyDriveTrash(users):
  for user in users:
    user, drive = buildDrive3GAPIObject(user)
    if not drive:
      continue
    print u'Emptying Drive trash for %s' % user
    callGAPI(drive.files(), u'emptyTrash')

def initializeDriveFileAttributes():
  return ({}, {DFA_LOCALFILEPATH: None, DFA_LOCALFILENAME: None, DFA_LOCALMIMETYPE: None, DFA_CONVERT: None, DFA_OCR: None, DFA_OCRLANGUAGE: None, DFA_PARENTQUERY: None})

def getDriveFileAttribute(i, body, parameters, myarg, update=False):
  if myarg == u'localfile':
    parameters[DFA_LOCALFILEPATH] = sys.argv[i+1]
    parameters[DFA_LOCALFILENAME] = os.path.basename(parameters[DFA_LOCALFILEPATH])
    body.setdefault(u'title', parameters[DFA_LOCALFILENAME])
    body[u'mimeType'] = mimetypes.guess_type(parameters[DFA_LOCALFILEPATH])[0]
    if body[u'mimeType'] is None:
      body[u'mimeType'] = u'application/octet-stream'
    parameters[DFA_LOCALMIMETYPE] = body[u'mimeType']
    i += 2
  elif myarg == u'convert':
    parameters[DFA_CONVERT] = True
    i += 1
  elif myarg == u'ocr':
    parameters[DFA_OCR] = True
    i += 1
  elif myarg == u'ocrlanguage':
    parameters[DFA_OCRLANGUAGE] = LANGUAGE_CODES_MAP.get(sys.argv[i+1].lower(), sys.argv[i+1])
    i += 2
  elif myarg in DRIVEFILE_LABEL_CHOICES_MAP:
    body.setdefault(u'labels', {})
    if update:
      body[u'labels'][DRIVEFILE_LABEL_CHOICES_MAP[myarg]] = getBoolean(sys.argv[i+1], myarg)
      i += 2
    else:
      body[u'labels'][DRIVEFILE_LABEL_CHOICES_MAP[myarg]] = True
      i += 1
  elif myarg in [u'lastviewedbyme', u'lastviewedbyuser', u'lastviewedbymedate', u'lastviewedbymetime']:
    body[u'lastViewedByMeDate'] = getTimeOrDeltaFromNow(sys.argv[i+1])
    i += 2
  elif myarg in [u'modifieddate', u'modifiedtime']:
    body[u'modifiedDate'] = getTimeOrDeltaFromNow(sys.argv[i+1])
    i += 2
  elif myarg == u'description':
    body[u'description'] = sys.argv[i+1]
    i += 2
  elif myarg == u'mimetype':
    mimeType = sys.argv[i+1]
    if mimeType in MIMETYPE_CHOICES_MAP:
      body[u'mimeType'] = MIMETYPE_CHOICES_MAP[mimeType]
    else:
      systemErrorExit(2, 'mimetype must be one of %s; got %s"' % (u', '.join(MIMETYPE_CHOICES_MAP), mimeType))
    i += 2
  elif myarg == u'parentid':
    body.setdefault(u'parents', [])
    body[u'parents'].append({u'id': sys.argv[i+1]})
    i += 2
  elif myarg == u'parentname':
    parameters[DFA_PARENTQUERY] = u"'me' in owners and mimeType = '%s' and title = '%s'" % (MIMETYPE_GA_FOLDER, sys.argv[i+1])
    i += 2
  elif myarg in [u'anyownerparentname']:
    parameters[DFA_PARENTQUERY] = u"mimeType = '%s' and title = '%s'" % (MIMETYPE_GA_FOLDER, sys.argv[i+1])
    i += 2
  elif myarg == u'writerscantshare':
    body[u'writersCanShare'] = False
    i += 1
  else:
    systemErrorExit(2, '%s is not a valid argument for "gam <users> %s drivefile"' % (myarg, [u'add', u'update'][update]))
  return i

def doUpdateDriveFile(users):
  fileIdSelection = {u'fileIds': [], u'query': None}
  media_body = None
  operation = u'update'
  body, parameters = initializeDriveFileAttributes()
  i = 5
  while i < len(sys.argv):
    myarg = sys.argv[i].lower().replace(u'_', u'')
    if myarg == u'copy':
      operation = u'copy'
      i += 1
    elif myarg == u'newfilename':
      body[u'title'] = sys.argv[i+1]
      i += 2
    elif myarg == u'id':
      fileIdSelection[u'fileIds'] = [sys.argv[i+1],]
      i += 2
    elif myarg == u'query':
      fileIdSelection[u'query'] = sys.argv[i+1]
      i += 2
    elif myarg == u'drivefilename':
      fileIdSelection[u'query'] = u"'me' in owners and title = '{0}'".format(sys.argv[i+1])
      i += 2
    else:
      i = getDriveFileAttribute(i, body, parameters, myarg, True)
  if not fileIdSelection[u'query'] and not fileIdSelection[u'fileIds']:
    systemErrorExit(2, 'you need to specify either id, query or drivefilename in order to determine the file(s) to update')
  if fileIdSelection[u'query'] and fileIdSelection[u'fileIds']:
    systemErrorExit(2, 'you cannot specify multiple file identifiers. Choose one of id, drivefilename, query.')
  for user in users:
    user, drive = buildDriveGAPIObject(user)
    if not drive:
      continue
    if parameters[DFA_PARENTQUERY]:
      more_parents = doDriveSearch(drive, query=parameters[DFA_PARENTQUERY])
      body.setdefault(u'parents', [])
      for a_parent in more_parents:
        body[u'parents'].append({u'id': a_parent})
    if fileIdSelection[u'query']:
      fileIdSelection[u'fileIds'] = doDriveSearch(drive, query=fileIdSelection[u'query'])
    if not fileIdSelection[u'fileIds']:
      print u'No files to %s for %s' % (operation, user)
      continue
    if operation == u'update':
      if parameters[DFA_LOCALFILEPATH]:
        media_body = googleapiclient.http.MediaFileUpload(parameters[DFA_LOCALFILEPATH], mimetype=parameters[DFA_LOCALMIMETYPE], resumable=True)
      for fileId in fileIdSelection[u'fileIds']:
        if media_body:
          result = callGAPI(drive.files(), u'update',
                            fileId=fileId, convert=parameters[DFA_CONVERT],
                            ocr=parameters[DFA_OCR],
                            ocrLanguage=parameters[DFA_OCRLANGUAGE],
                            media_body=media_body, body=body, fields=u'id',
                            supportsTeamDrives=True)
          print u'Successfully updated %s drive file with content from %s' % (result[u'id'], parameters[DFA_LOCALFILENAME])
        else:
          result = callGAPI(drive.files(), u'patch',
                            fileId=fileId, convert=parameters[DFA_CONVERT],
                            ocr=parameters[DFA_OCR],
                            ocrLanguage=parameters[DFA_OCRLANGUAGE], body=body,
                            fields=u'id', supportsTeamDrives=True)
          print u'Successfully updated drive file/folder ID %s' % (result[u'id'])
    else:
      for fileId in fileIdSelection[u'fileIds']:
        result = callGAPI(drive.files(), u'copy',
                          fileId=fileId, convert=parameters[DFA_CONVERT],
                          ocr=parameters[DFA_OCR],
                          ocrLanguage=parameters[DFA_OCRLANGUAGE],
                          body=body, fields=u'id', supportsTeamDrives=True)
        print u'Successfully copied %s to %s' % (fileId, result[u'id'])

def createDriveFile(users):
  csv_output = to_drive = False
  csv_rows = []
  csv_titles = [u'User', u'title', u'id']
  media_body = None
  body, parameters = initializeDriveFileAttributes()
  i = 5
  while i < len(sys.argv):
    myarg = sys.argv[i].lower().replace(u'_', u'')
    if myarg == u'drivefilename':
      body[u'title'] = sys.argv[i+1]
      i += 2
    elif myarg == u'csv':
      csv_output = True
      i += 1
    elif myarg == u'todrive':
      to_drive = True
      i += 1
    else:
      i = getDriveFileAttribute(i, body, parameters, myarg, False)
  for user in users:
    user, drive = buildDriveGAPIObject(user)
    if not drive:
      continue
    if parameters[DFA_PARENTQUERY]:
      more_parents = doDriveSearch(drive, query=parameters[DFA_PARENTQUERY])
      body.setdefault(u'parents', [])
      for a_parent in more_parents:
        body[u'parents'].append({u'id': a_parent})
    if parameters[DFA_LOCALFILEPATH]:
      media_body = googleapiclient.http.MediaFileUpload(parameters[DFA_LOCALFILEPATH], mimetype=parameters[DFA_LOCALMIMETYPE], resumable=True)
    result = callGAPI(drive.files(), u'insert',
                      convert=parameters[DFA_CONVERT], ocr=parameters[DFA_OCR],
                      ocrLanguage=parameters[DFA_OCRLANGUAGE],
                      media_body=media_body, body=body, fields=u'id,title,mimeType',
                      supportsTeamDrives=True)
    titleInfo = u'{0}({1})'.format(result[u'title'], result[u'id'])
    if csv_output:
      csv_rows.append({u'User': user, u'title': result[u'title'], u'id': result[u'id']})
    else:
      if parameters[DFA_LOCALFILENAME]:
        print u'Successfully uploaded %s to Drive File %s' % (parameters[DFA_LOCALFILENAME], titleInfo)
      else:
        print u'Successfully created Drive %s %s' % ([u'Folder', u'File'][result[u'mimeType'] != MIMETYPE_GA_FOLDER], titleInfo)
  if csv_output:
    writeCSVfile(csv_rows, csv_titles, u'Files', to_drive)

def downloadDriveFile(users):
  i = 5
  fileIdSelection = {u'fileIds': [], u'query': None}
  revisionId = None
  exportFormatName = u'openoffice'
  exportFormatChoices = [exportFormatName]
  exportFormats = DOCUMENT_FORMATS_MAP[exportFormatName]
  targetFolder = GC_Values[GC_DRIVE_DIR]
  safe_filename_chars = "-_.() %s%s" % (string.ascii_letters, string.digits)
  while i < len(sys.argv):
    myarg = sys.argv[i].lower().replace(u'_', u'')
    if myarg == u'id':
      fileIdSelection[u'fileIds'] = [sys.argv[i+1],]
      i += 2
    elif myarg == u'query':
      fileIdSelection[u'query'] = sys.argv[i+1]
      i += 2
    elif myarg == u'drivefilename':
      fileIdSelection[u'query'] = u"'me' in owners and title = '{0}'".format(sys.argv[i+1])
      i += 2
    elif myarg == u'revision':
      revisionId = sys.argv[i+1]
      i += 2
    elif myarg == u'format':
      exportFormatChoices = sys.argv[i+1].replace(u',', u' ').lower().split()
      exportFormats = []
      for exportFormat in exportFormatChoices:
        if exportFormat in DOCUMENT_FORMATS_MAP:
          exportFormats.extend(DOCUMENT_FORMATS_MAP[exportFormat])
        else:
          systemErrorExit(2, 'format must be one of {0}; got {1}'.format(u', '.join(DOCUMENT_FORMATS_MAP), exportFormat))
      i += 2
    elif myarg == u'targetfolder':
      targetFolder = os.path.expanduser(sys.argv[i+1])
      if not os.path.isdir(targetFolder):
        os.makedirs(targetFolder)
      i += 2
    else:
      systemErrorExit(2, '%s is not a valid argument for "gam <users> get drivefile"' % sys.argv[i])
  if not fileIdSelection[u'query'] and not fileIdSelection[u'fileIds']:
    systemErrorExit(2, 'you need to specify either id, query or drivefilename in order to determine the file(s) to download')
  if fileIdSelection[u'query'] and fileIdSelection[u'fileIds']:
    systemErrorExit(2, 'you cannot specify multiple file identifiers. Choose one of id, drivefilename, query.')
  for user in users:
    user, drive = buildDriveGAPIObject(user)
    if not drive:
      continue
    if fileIdSelection[u'query']:
      fileIdSelection[u'fileIds'] = doDriveSearch(drive, query=fileIdSelection[u'query'])
    else:
      fileId = fileIdSelection[u'fileIds'][0]
      if fileId[:8].lower() == u'https://' or fileId[:7].lower() == u'http://':
        fileIdSelection[u'fileIds'][0] = getFileIdFromAlternateLink(fileId)
    if not fileIdSelection[u'fileIds']:
      print u'No files to download for %s' % user
    i = 0
    for fileId in fileIdSelection[u'fileIds']:
      extension = None
      result = callGAPI(drive.files(), u'get', fileId=fileId,
                        fields=u'fileSize,title,mimeType,downloadUrl,exportLinks',
                        supportsTeamDrives=True)
      if result[u'mimeType'] == MIMETYPE_GA_FOLDER:
        print utils.convertUTF8(u'Skipping download of folder %s' % result[u'title'])
        continue
      try:
        result[u'fileSize'] = int(result[u'fileSize'])
        if result[u'fileSize'] < 1024:
          filesize = u'1kb'
        elif result[u'fileSize'] < (1024 * 1024):
          filesize = u'%skb' % (result[u'fileSize'] / 1024)
        elif result[u'fileSize'] < (1024 * 1024 * 1024):
          filesize = u'%smb' % (result[u'fileSize'] / 1024 / 1024)
        else:
          filesize = u'%sgb' % (result[u'fileSize'] / 1024 / 1024 / 1024)
        my_line = u'Downloading: %%s of %s bytes' % filesize
      except KeyError:
        my_line = u'Downloading Google Doc: %s'
      if u'downloadUrl' in result:
        download_url = result[u'downloadUrl']
      elif u'exportLinks' in result:
        for exportFormat in exportFormats:
          if exportFormat[u'mime'] in result[u'exportLinks']:
            download_url = result[u'exportLinks'][exportFormat[u'mime']]
            extension = exportFormat[u'ext']
            break
        else:
          print utils.convertUTF8(u'Skipping download of file {0}, Format {1} not available'.format(result[u'title'], u','.join(exportFormatChoices)))
          continue
      else:
        print utils.convertUTF8(u'Skipping download of file {0}, Format not downloadable')
        continue
      file_title = result[u'title']
      safe_file_title = u''.join(c for c in file_title if c in safe_filename_chars)
      if len(safe_file_title) < 1:
        safe_file_title = fileId
      filename = os.path.join(targetFolder, safe_file_title)
      y = 0
      while True:
        if extension and filename.lower()[-len(extension):] != extension:
          filename += extension
        if not os.path.isfile(filename):
          break
        y += 1
        filename = os.path.join(targetFolder, u'({0})-{1}'.format(y, safe_file_title))
      print utils.convertUTF8(my_line % filename)
      if revisionId:
        download_url = u'{0}&revision={1}'.format(download_url, revisionId)
      _, content = drive._http.request(download_url)
      writeFile(filename, content, continueOnError=True)

def showDriveFileInfo(users):
  fieldsList = []
  labelsList = []
  fileId = sys.argv[5]
  i = 6
  while i < len(sys.argv):
    myarg = sys.argv[i].lower().replace(u'_', u'')
    if myarg == u'allfields':
      fieldsList = []
      i += 1
    elif myarg in DRIVEFILE_FIELDS_CHOICES_MAP:
      fieldsList.append(DRIVEFILE_FIELDS_CHOICES_MAP[myarg])
      i += 1
    elif myarg in DRIVEFILE_LABEL_CHOICES_MAP:
      labelsList.append(DRIVEFILE_LABEL_CHOICES_MAP[myarg])
      i += 1
    else:
      systemErrorExit(2, '%s is not a valid argument for "gam <users> show fileinfo"' % myarg)
  if fieldsList or labelsList:
    fieldsList.append(u'title')
    fields = u','.join(set(fieldsList))
    if labelsList:
      fields += u',labels({0})'.format(u','.join(set(labelsList)))
  else:
    fields = u'*'
  for user in users:
    user, drive = buildDriveGAPIObject(user)
    if not drive:
      continue
    feed = callGAPI(drive.files(), u'get', fileId=fileId, fields=fields, supportsTeamDrives=True)
    if feed:
      print_json(None, feed)

def showDriveFileRevisions(users):
  fileId = sys.argv[5]
  for user in users:
    user, drive = buildDriveGAPIObject(user)
    if not drive:
      continue
    feed = callGAPI(drive.revisions(), u'list', fileId=fileId)
    if feed:
      print_json(None, feed)

def transferSecCals(users):
  target_user = sys.argv[5]
  remove_source_user = True
  i = 6
  while i < len(sys.argv):
    myarg = sys.argv[i].lower()
    if myarg == u'keepuser':
      remove_source_user = False
      i += 1
    else:
      systemErrorExit(2, '%s is not a valid argument for "gam <users> transfer seccals"' % sys.argv[i])
  if remove_source_user:
    target_user, target_cal = buildCalendarGAPIObject(target_user)
    if not target_cal:
      return
  for user in users:
    user, source_cal = buildCalendarGAPIObject(user)
    if not source_cal:
      continue
    source_calendars = callGAPIpages(source_cal.calendarList(), u'list', u'items', soft_errors=True,
                                     minAccessRole=u'owner', showHidden=True, fields=u'items(id),nextPageToken')
    for source_cal in source_calendars:
      if source_cal[u'id'].find(u'@group.calendar.google.com') != -1:
        doCalendarAddACL(calendarId=source_cal[u'id'], act_as=user, role=u'owner', scope=u'user', entity=target_user)
        if remove_source_user:
          doCalendarAddACL(calendarId=source_cal[u'id'], act_as=target_user, role=u'none', scope=u'user', entity=user)

def transferDriveFiles(users):
  target_user = sys.argv[5]
  remove_source_user = True
  i = 6
  while i < len(sys.argv):
    myarg = sys.argv[i].lower()
    if myarg == u'keepuser':
      remove_source_user = False
      i += 1
    else:
      systemErrorExit(2, '%s is not a valid argument for "gam <users> transfer drive"' % sys.argv[i])
  target_user, target_drive = buildDriveGAPIObject(target_user)
  if not target_drive:
    return
  target_about = callGAPI(target_drive.about(), u'get', fields=u'quotaType,quotaBytesTotal,quotaBytesUsed')
  if target_about[u'quotaType'] != u'UNLIMITED':
    target_drive_free = int(target_about[u'quotaBytesTotal']) - int(target_about[u'quotaBytesUsed'])
  else:
    target_drive_free = None
  for user in users:
    user, source_drive = buildDriveGAPIObject(user)
    if not source_drive:
      continue
    counter = 0
    source_about = callGAPI(source_drive.about(), u'get', fields=u'quotaBytesTotal,quotaBytesUsed,rootFolderId,permissionId')
    source_drive_size = int(source_about[u'quotaBytesUsed'])
    if target_drive_free is not None:
      if target_drive_free < source_drive_size:
        systemErrorExit(4, MESSAGE_NO_TRANSFER_LACK_OF_DISK_SPACE.format(source_drive_size / 1024 / 1024, target_drive_free / 1024 / 1024))
      print u'Source drive size: %smb  Target drive free: %smb' % (source_drive_size / 1024 / 1024, target_drive_free / 1024 / 1024)
      target_drive_free = target_drive_free - source_drive_size # prep target_drive_free for next user
    else:
      print u'Source drive size: %smb  Target drive free: UNLIMITED' % (source_drive_size / 1024 / 1024)
    source_root = source_about[u'rootFolderId']
    source_permissionid = source_about[u'permissionId']
    print u"Getting file list for source user: %s..." % user
    page_message = u'  got %%total_items%% files\n'
    source_drive_files = callGAPIpages(source_drive.files(), u'list', u'items', page_message=page_message,
                                       q=u"'me' in owners and trashed = false", fields=u'items(id,parents,mimeType),nextPageToken')
    all_source_file_ids = []
    for source_drive_file in source_drive_files:
      all_source_file_ids.append(source_drive_file[u'id'])
    total_count = len(source_drive_files)
    print u"Getting folder list for target user: %s..." % target_user
    page_message = u'  got %%total_items%% folders\n'
    target_folders = callGAPIpages(target_drive.files(), u'list', u'items', page_message=page_message,
                                   q=u"'me' in owners and mimeType = 'application/vnd.google-apps.folder'", fields=u'items(id,title),nextPageToken')
    got_top_folder = False
    all_target_folder_ids = []
    for target_folder in target_folders:
      all_target_folder_ids.append(target_folder[u'id'])
      if (not got_top_folder) and target_folder[u'title'] == u'%s old files' % user:
        target_top_folder = target_folder[u'id']
        got_top_folder = True
    if not got_top_folder:
      create_folder = callGAPI(target_drive.files(), u'insert', body={u'title': u'%s old files' % user, u'mimeType': u'application/vnd.google-apps.folder'}, fields=u'id')
      target_top_folder = create_folder[u'id']
    transferred_files = []
    while True: # we loop thru, skipping files until all of their parents are done
      skipped_files = False
      for drive_file in source_drive_files:
        file_id = drive_file[u'id']
        if file_id in transferred_files:
          continue
        source_parents = drive_file[u'parents']
        skip_file_for_now = False
        for source_parent in source_parents:
          if source_parent[u'id'] not in all_source_file_ids and source_parent[u'id'] not in all_target_folder_ids:
            continue  # means this parent isn't owned by source or target, shouldn't matter
          if source_parent[u'id'] not in transferred_files and source_parent[u'id'] != source_root:
            #print u'skipping %s' % file_id
            skipped_files = skip_file_for_now = True
            break
        if skip_file_for_now:
          continue
        else:
          transferred_files.append(drive_file[u'id'])
        counter += 1
        print u'Changing owner for file %s (%s/%s)' % (drive_file[u'id'], counter, total_count)
        body = {u'role': u'owner', u'type': u'user', u'value': target_user}
        callGAPI(source_drive.permissions(), u'insert', soft_errors=True, fileId=file_id, sendNotificationEmails=False, body=body)
        target_parents = []
        for parent in source_parents:
          try:
            if parent[u'isRoot']:
              target_parents.append({u'id': target_top_folder})
            else:
              target_parents.append({u'id': parent[u'id']})
          except TypeError:
            pass
        if not target_parents:
          target_parents.append({u'id': target_top_folder})
        callGAPI(target_drive.files(), u'patch', soft_errors=True, retry_reasons=[u'notFound'], fileId=file_id, body={u'parents': target_parents})
        if remove_source_user:
          callGAPI(target_drive.permissions(), u'delete', soft_errors=True, fileId=file_id, permissionId=source_permissionid)
      if not skipped_files:
        break

def doImap(users):
  enable = getBoolean(sys.argv[4], u'gam <users> imap')
  body = {u'enabled': enable, u'autoExpunge': True, u'expungeBehavior': u'archive', u'maxFolderSize': 0}
  i = 5
  while i < len(sys.argv):
    myarg = sys.argv[i].lower()
    if myarg == u'noautoexpunge':
      body[u'autoExpunge'] = False
      i += 1
    elif myarg == u'expungebehavior':
      opt = sys.argv[i+1].lower()
      if opt in EMAILSETTINGS_IMAP_EXPUNGE_BEHAVIOR_CHOICES_MAP:
        body[u'expungeBehavior'] = EMAILSETTINGS_IMAP_EXPUNGE_BEHAVIOR_CHOICES_MAP[opt]
        i += 2
      else:
        systemErrorExit(2, 'value for "gam <users> imap expungebehavior" must be one of %s; got %s' % (u', '.join(EMAILSETTINGS_IMAP_EXPUNGE_BEHAVIOR_CHOICES_MAP), opt))
    elif myarg == u'maxfoldersize':
      opt = sys.argv[i+1].lower()
      if opt in EMAILSETTINGS_IMAP_MAX_FOLDER_SIZE_CHOICES:
        body[u'maxFolderSize'] = int(opt)
        i += 2
      else:
        systemErrorExit(2, 'value for "gam <users> imap maxfoldersize" must be one of %s; got %s' % (u'|'.join(EMAILSETTINGS_IMAP_MAX_FOLDER_SIZE_CHOICES), opt))
    else:
      systemErrorExit(2, '%s is not a valid argument for "gam <users> imap"' % myarg)
  i = 0
  count = len(users)
  for user in users:
    i += 1
    user, gmail = buildGmailGAPIObject(user)
    if not gmail:
      continue
    print u"Setting IMAP Access to %s for %s (%s/%s)" % (str(enable), user, i, count)
    callGAPI(gmail.users().settings(), u'updateImap',
             soft_errors=True,
             userId=u'me', body=body)

def getImap(users):
  i = 0
  count = len(users)
  for user in users:
    i += 1
    user, gmail = buildGmailGAPIObject(user)
    if not gmail:
      continue
    result = callGAPI(gmail.users().settings(), u'getImap',
                      soft_errors=True,
                      userId=u'me')
    if result:
      enabled = result[u'enabled']
      if enabled:
        print u'User: {0}, IMAP Enabled: {1}, autoExpunge: {2}, expungeBehavior: {3}, maxFolderSize:{4} ({5}/{6})'.format(user, enabled, result[u'autoExpunge'], result[u'expungeBehavior'], result[u'maxFolderSize'], i, count)
      else:
        print u'User: {0}, IMAP Enabled: {1} ({2}/{3})'.format(user, enabled, i, count)

def getProductAndSKU(sku):
  l_sku = sku.lower().replace(u'-', u'').replace(u' ', u'')
  for a_sku, sku_values in SKUS.items():
    if l_sku == a_sku.lower().replace(u'-', u'') or l_sku in sku_values[u'aliases'] or l_sku == sku_values[u'displayName'].lower().replace(u' ', u''):
      return (sku_values[u'product'], a_sku)
  try:
    product = re.search(u'^([A-Z,a-z]*-[A-Z,a-z]*)', sku).group(1)
  except AttributeError:
    product = sku
  return (product, sku)

def doLicense(users, operation):
  lic = buildGAPIObject(u'licensing')
  sku = sys.argv[5]
  productId, skuId = getProductAndSKU(sku)
  i = 6
  if len(sys.argv) > 6 and sys.argv[i].lower() in [u'product', u'productid']:
    productId = sys.argv[i+1]
    i += 2
  for user in users:
    if operation == u'delete':
      print u'Removing license %s from user %s' % (_formatSKUIdDisplayName(skuId), user)
      callGAPI(lic.licenseAssignments(), operation, soft_errors=True, productId=productId, skuId=skuId, userId=user)
    elif operation == u'insert':
      print u'Adding license %s to user %s' % (_formatSKUIdDisplayName(skuId), user)
      callGAPI(lic.licenseAssignments(), operation, soft_errors=True, productId=productId, skuId=skuId, body={u'userId': user})
    elif operation == u'patch':
      try:
        old_sku = sys.argv[i]
        if old_sku.lower() == u'from':
          old_sku = sys.argv[i+1]
      except KeyError:
        systemErrorExit(2, 'You need to specify the user\'s old SKU as the last argument')
      _, old_sku = getProductAndSKU(old_sku)
      print u'Changing user %s from license %s to %s' % (user, _formatSKUIdDisplayName(old_sku), _formatSKUIdDisplayName(skuId))
      callGAPI(lic.licenseAssignments(), operation, soft_errors=True, productId=productId, skuId=old_sku, userId=user, body={u'skuId': skuId})

def doPop(users):
  enable = getBoolean(sys.argv[4], u'gam <users> pop')
  body = {u'accessWindow': [u'disabled', u'allMail'][enable], u'disposition': u'leaveInInbox'}
  i = 5
  while i < len(sys.argv):
    myarg = sys.argv[i].lower()
    if myarg == u'for':
      opt = sys.argv[i+1].lower()
      if opt in EMAILSETTINGS_POP_ENABLE_FOR_CHOICES_MAP:
        body[u'accessWindow'] = EMAILSETTINGS_POP_ENABLE_FOR_CHOICES_MAP[opt]
        i += 2
      else:
        systemErrorExit(2, 'value for "gam <users> pop for" must be one of %s; got %s' % (u', '.join(EMAILSETTINGS_POP_ENABLE_FOR_CHOICES_MAP), opt))
    elif myarg == u'action':
      opt = sys.argv[i+1].lower()
      if opt in EMAILSETTINGS_FORWARD_POP_ACTION_CHOICES_MAP:
        body[u'disposition'] = EMAILSETTINGS_FORWARD_POP_ACTION_CHOICES_MAP[opt]
        i += 2
      else:
        systemErrorExit(2, 'value for "gam <users> pop action" must be one of %s; got %s' % (u', '.join(EMAILSETTINGS_FORWARD_POP_ACTION_CHOICES_MAP), opt))
    elif myarg == u'confirm':
      i += 1
    else:
      systemErrorExit(2, '%s is not a valid argument for "gam <users> pop"' % myarg)
  i = 0
  count = len(users)
  for user in users:
    i += 1
    user, gmail = buildGmailGAPIObject(user)
    if not gmail:
      continue
    print u"Setting POP Access to %s for %s (%s/%s)" % (str(enable), user, i, count)
    callGAPI(gmail.users().settings(), u'updatePop',
             soft_errors=True,
             userId=u'me', body=body)

def getPop(users):
  i = 0
  count = len(users)
  for user in users:
    i += 1
    user, gmail = buildGmailGAPIObject(user)
    if not gmail:
      continue
    result = callGAPI(gmail.users().settings(), u'getPop',
                      soft_errors=True,
                      userId=u'me')
    if result:
      enabled = result[u'accessWindow'] != u'disabled'
      if enabled:
        print u'User: {0}, POP Enabled: {1}, For: {2}, Action: {3} ({4}/{5})'.format(user, enabled, result[u'accessWindow'], result[u'disposition'], i, count)
      else:
        print u'User: {0}, POP Enabled: {1} ({2}/{3})'.format(user, enabled, i, count)

def _showSendAs(result, j, jcount, formatSig):
  if result[u'displayName']:
    print utils.convertUTF8(u'SendAs Address: {0} <{1}>{2}'.format(result[u'displayName'], result[u'sendAsEmail'], currentCount(j, jcount)))
  else:
    print utils.convertUTF8(u'SendAs Address: <{0}>{1}'.format(result[u'sendAsEmail'], currentCount(j, jcount)))
  if result.get(u'replyToAddress'):
    print u'  ReplyTo: {0}'.format(result[u'replyToAddress'])
  print u'  IsPrimary: {0}'.format(result.get(u'isPrimary', False))
  print u'  Default: {0}'.format(result.get(u'isDefault', False))
  if not result.get(u'isPrimary', False):
    print u'  TreatAsAlias: {0}'.format(result.get(u'treatAsAlias', False))
    print u'  Verification Status: {0}'.format(result.get(u'verificationStatus', u'unspecified'))
  sys.stdout.write(u'  Signature:\n    ')
  signature = result.get(u'signature')
  if not signature:
    signature = u'None'
  if formatSig:
    print utils.convertUTF8(utils.indentMultiLineText(utils.dehtml(signature), n=4))
  else:
    print utils.convertUTF8(utils.indentMultiLineText(signature, n=4))

def _processTags(tagReplacements, message):
  while True:
    match = RT_PATTERN.search(message)
    if not match:
      break
    if tagReplacements.get(match.group(1)):
      message = RT_OPEN_PATTERN.sub(u'', message, count=1)
      message = RT_CLOSE_PATTERN.sub(u'', message, count=1)
    else:
      message = RT_STRIP_PATTERN.sub(u'', message, count=1)
  while True:
    match = RT_TAG_REPLACE_PATTERN.search(message)
    if not match:
      break
    message = re.sub(match.group(0), tagReplacements.get(match.group(1), u''), message)
  return message

def _processSignature(tagReplacements, signature, html):
  if signature:
    signature = signature.replace(u'\r', u'').replace(u'\\n', u'<br/>')
    if tagReplacements:
      signature = _processTags(tagReplacements, signature)
    if not html:
      signature = signature.replace(u'\n', u'<br/>')
  return signature

def getSendAsAttributes(i, myarg, body, tagReplacements, command):
  if myarg == u'replace':
    matchTag = getString(i+1, u'Tag')
    matchReplacement = getString(i+2, u'String', minLen=0)
    tagReplacements[matchTag] = matchReplacement
    i += 3
  elif myarg == u'name':
    body[u'displayName'] = sys.argv[i+1]
    i += 2
  elif myarg == u'replyto':
    body[u'replyToAddress'] = sys.argv[i+1]
    i += 2
  elif myarg == u'default':
    body[u'isDefault'] = True
    i += 1
  elif myarg == u'treatasalias':
    body[u'treatAsAlias'] = getBoolean(sys.argv[i+1], myarg)
    i += 2
  else:
    systemErrorExit(2, '%s is not a valid argument for "gam <users> %s"' % (sys.argv[i], command))
  return i

def addUpdateSendAs(users, i, addCmd):
  emailAddress = normalizeEmailAddressOrUID(sys.argv[i], noUid=True)
  i += 1
  if addCmd:
    command = [u'sendas', u'add sendas'][i == 6]
    body = {u'sendAsEmail': emailAddress, u'displayName': sys.argv[i]}
    i += 1
  else:
    command = u'update sendas'
    body = {}
  signature = None
  tagReplacements = {}
  html = False
  while i < len(sys.argv):
    myarg = sys.argv[i].lower()
    if myarg in [u'signature', u'sig']:
      signature = sys.argv[i+1]
      i += 2
      if signature.lower() == u'file':
        filename = sys.argv[i]
        i, encoding = getCharSet(i+1)
        signature = readFile(filename, encoding=encoding)
    elif myarg == u'html':
      html = True
      i += 1
    else:
      i = getSendAsAttributes(i, myarg, body, tagReplacements, command)
  if signature is not None:
    body[u'signature'] = _processSignature(tagReplacements, signature, html)
  kwargs = {u'body': body}
  if not addCmd:
    kwargs[u'sendAsEmail'] = emailAddress
  i = 0
  count = len(users)
  for user in users:
    i += 1
    user, gmail = buildGmailGAPIObject(user)
    if not gmail:
      continue
    print u"Allowing %s to send as %s (%s/%s)" % (user, emailAddress, i, count)
    callGAPI(gmail.users().settings().sendAs(), [u'patch', u'create'][addCmd],
             soft_errors=True,
             userId=u'me', **kwargs)

def deleteSendAs(users):
  emailAddress = normalizeEmailAddressOrUID(sys.argv[5], noUid=True)
  i = 0
  count = len(users)
  for user in users:
    i += 1
    user, gmail = buildGmailGAPIObject(user)
    if not gmail:
      continue
    print u"Disallowing %s to send as %s (%s/%s)" % (user, emailAddress, i, count)
    callGAPI(gmail.users().settings().sendAs(), u'delete',
             soft_errors=True,
             userId=u'me', sendAsEmail=emailAddress)

def updateSmime(users):
  smimeIdBase = None
  sendAsEmailBase = None
  make_default = False
  i = 5
  while i < len(sys.argv):
    myarg = sys.argv[i].lower()
    if myarg == u'id':
      smimeIdBase = sys.argv[i+1]
      i += 2
    elif myarg in [u'sendas', u'sendasemail']:
      sendAsEmailBase = sys.argv[i+1]
      i += 2
    elif myarg in [u'default']:
      make_default = True
      i += 1
    else:
      systemErrorExit(3, '%s is not a valid argument to "gam <users> update smime"' % myarg)
  if not make_default:
    print u'Nothing to update for smime.'
    sys.exit(0)
  for user in users:
    user, gmail = buildGmailGAPIObject(user)
    if not gmail:
      continue
    sendAsEmail = sendAsEmailBase if sendAsEmailBase else user
    if not smimeIdBase:
      result = callGAPI(gmail.users().settings().sendAs().smimeInfo(), u'list', userId=u'me', sendAsEmail=sendAsEmail, fields=u'smimeInfo(id)')
      smimes = result.get(u'smimeInfo', [])
      if len(smimes) == 0:
        systemErrorExit(3, '%s has no S/MIME certificates for sendas address %s' % (user, sendAsEmail))
      elif len(smimes) > 1:
        systemErrorExit(3, u'%s has more than one S/MIME certificate. Please specify a cert to update:\n %s' % (user, u'\n '.join([smime[u'id'] for smime in smimes])))
      smimeId = smimes[0][u'id']
    else:
      smimeId = smimeIdBase
    print u'Setting smime id %s as default for user %s and sendas %s' % (smimeId, user, sendAsEmail)
    callGAPI(gmail.users().settings().sendAs().smimeInfo(), u'setDefault', userId=u'me', sendAsEmail=sendAsEmail, id=smimeId)

def deleteSmime(users):
  smimeIdBase = None
  sendAsEmailBase = None
  i = 5
  while i < len(sys.argv):
    myarg = sys.argv[i].lower()
    if myarg == u'id':
      smimeIdBase = sys.argv[i+1]
      i += 2
    elif myarg in [u'sendas', u'sendasemail']:
      sendAsEmailBase = sys.argv[i+1]
      i += 2
    else:
      systemErrorExit(3, '%s is not a valid argument to "gam <users> delete smime"' % myarg)
  for user in users:
    user, gmail = buildGmailGAPIObject(user)
    if not gmail:
      continue
    sendAsEmail = sendAsEmailBase if sendAsEmailBase else user
    if not smimeIdBase:
      result = callGAPI(gmail.users().settings().sendAs().smimeInfo(), u'list', userId=u'me', sendAsEmail=sendAsEmail, fields=u'smimeInfo(id)')
      smimes = result.get(u'smimeInfo', [])
      if len(smimes) == 0:
        systemErrorExit(3, '%s has no S/MIME certificates for sendas address %s' % (user, sendAsEmail))
      elif len(smimes) > 1:
        systemErrorExit(3, u'%s has more than one S/MIME certificate. Please specify a cert to delete:\n %s' % (user, u'\n '.join([smime[u'id'] for smime in smimes])))
      smimeId = smimes[0][u'id']
    else:
      smimeId = smimeIdBase
    print u'Deleting smime id %s for user %s and sendas %s' % (smimeId, user, sendAsEmail)
    callGAPI(gmail.users().settings().sendAs().smimeInfo(), u'delete', userId=u'me', sendAsEmail=sendAsEmail, id=smimeId)

def printShowSmime(users, csvFormat):
  if csvFormat:
    todrive = False
    titles = [u'User']
    csvRows = []
  primaryonly = False
  i = 5
  while i < len(sys.argv):
    myarg = sys.argv[i].lower()
    if csvFormat and myarg == u'todrive':
      todrive = True
      i += 1
    elif myarg == u'primaryonly':
      primaryonly = True
      i += 1
    else:
      systemErrorExit(3, '%s is not a valid argument for "gam <users> %s smime"' % (myarg, [u'show', u'print'][csvFormat]))
  i = 0
  count = len(users)
  for user in users:
    i += 1
    user, gmail = buildGmailGAPIObject(user)
    if not gmail:
      continue
    if primaryonly:
      sendAsEmails = [user]
    else:
      result = callGAPI(gmail.users().settings().sendAs(), u'list', userId=u'me', fields=u'sendAs(sendAsEmail)')
      sendAsEmails = []
      for sendAs in result[u'sendAs']:
        sendAsEmails.append(sendAs[u'sendAsEmail'])
    for sendAsEmail in sendAsEmails:
      result = callGAPI(gmail.users().settings().sendAs().smimeInfo(), u'list', sendAsEmail=sendAsEmail, userId=u'me')
      smimes = result.get(u'smimeInfo', [])
      for j, _ in enumerate(smimes):
        smimes[j][u'expiration'] = datetime.datetime.fromtimestamp(int(smimes[j][u'expiration'])/1000).strftime('%Y-%m-%d %H:%M:%S')
      if csvFormat:
        for smime in smimes:
          addRowTitlesToCSVfile(flatten_json(smime, flattened={u'User': user}), csvRows, titles)
      else:
        print_json(None, smimes)
  if csvFormat:
    writeCSVfile(csvRows, titles, u'S/MIME', todrive)

def printShowSendAs(users, csvFormat):
  if csvFormat:
    todrive = False
    titles = [u'User', u'displayName', u'sendAsEmail', u'replyToAddress', u'isPrimary', u'isDefault', u'treatAsAlias', u'verificationStatus']
    csvRows = []
  formatSig = False
  i = 5
  while i < len(sys.argv):
    myarg = sys.argv[i].lower()
    if csvFormat and myarg == u'todrive':
      todrive = True
      i += 1
    elif not csvFormat and myarg == u'format':
      formatSig = True
      i += 1
    else:
      systemErrorExit(2, '%s is not a valid argument for "gam <users> %s sendas"' %  (myarg, [u'show', u'print'][csvFormat]))
  i = 0
  count = len(users)
  for user in users:
    i += 1
    user, gmail = buildGmailGAPIObject(user)
    if not gmail:
      continue
    result = callGAPI(gmail.users().settings().sendAs(), u'list',
                      soft_errors=True,
                      userId=u'me')
    jcount = len(result.get(u'sendAs', [])) if (result) else 0
    if not csvFormat:
      print u'User: {0}, SendAs Addresses: ({1}/{2})'.format(user, i, count)
      if jcount == 0:
        continue
      j = 0
      for sendas in result[u'sendAs']:
        j += 1
        _showSendAs(sendas, j, jcount, formatSig)
    else:
      if jcount == 0:
        continue
      for sendas in result[u'sendAs']:
        row = {u'User': user, u'isPrimary': False}
        for item in sendas:
          if item not in titles:
            titles.append(item)
          row[item] = sendas[item]
        csvRows.append(row)
  if csvFormat:
    writeCSVfile(csvRows, titles, u'SendAs', todrive)

def infoSendAs(users):
  emailAddress = normalizeEmailAddressOrUID(sys.argv[5], noUid=True)
  formatSig = False
  i = 6
  while i < len(sys.argv):
    myarg = sys.argv[i].lower()
    if myarg == u'format':
      formatSig = True
      i += 1
    else:
      systemErrorExit(2, '%s is not a valid argument for "gam <users> info sendas"' % sys.argv[i])
  i = 0
  count = len(users)
  for user in users:
    i += 1
    user, gmail = buildGmailGAPIObject(user)
    if not gmail:
      continue
    print u'User: {0}, Show SendAs Address:{1}'.format(user, currentCount(i, count))
    result = callGAPI(gmail.users().settings().sendAs(), u'get',
                      soft_errors=True,
                      userId=u'me', sendAsEmail=emailAddress)
    if result:
      _showSendAs(result, i, count, formatSig)

def addSmime(users):
  sendAsEmailBase = None
  setDefault = False
  body = {}
  i = 5
  while i < len(sys.argv):
    myarg = sys.argv[i].lower()
    if myarg == u'file':
      smimefile = sys.argv[i+1]
      body[u'pkcs12'] = base64.urlsafe_b64encode(readFile(smimefile, mode=u'rb'))
      i += 2
    elif myarg == u'password':
      body[u'encryptedKeyPassword'] = sys.argv[i+1]
      i += 2
    elif myarg == u'default':
      setDefault = True
      i += 1
    elif myarg in [u'sendas', u'sendasemail']:
      sendAsEmailBase = sys.argv[i+1]
      i += 2
    else:
      systemErrorExit(3, '%s is not a valid argument for "gam <users> add smime"' % myarg)
  if u'pkcs12' not in body:
    systemErrorExit(3, 'you must specify a file to upload')
  i = 0
  count = len(users)
  for user in users:
    i += 1
    user, gmail = buildGmailGAPIObject(user)
    if not gmail:
      continue
    sendAsEmail = sendAsEmailBase if sendAsEmailBase else user
    result = callGAPI(gmail.users().settings().sendAs().smimeInfo(), u'insert', userId=u'me', sendAsEmail=sendAsEmail, body=body)
    if setDefault:
      callGAPI(gmail.users().settings().sendAs().smimeInfo(), u'setDefault', userId=u'me', sendAsEmail=sendAsEmail, id=result[u'id'])
    print u'Added S/MIME certificate for user %s sendas %s issued by %s' % (user, sendAsEmail, result[u'issuerCn'])

def doLabel(users, i):
  label = sys.argv[i]
  i += 1
  body = {u'name': label}
  while i < len(sys.argv):
    myarg = sys.argv[i].lower().replace(u'_', u'')
    if myarg == u'labellistvisibility':
      value = sys.argv[i+1].lower().replace(u'_', u'')
      if value == u'hide':
        body[u'labelListVisibility'] = u'labelHide'
      elif value == u'show':
        body[u'labelListVisibility'] = u'labelShow'
      elif value == u'showifunread':
        body[u'labelListVisibility'] = u'labelShowIfUnread'
      else:
        systemErrorExit(2, 'label_list_visibility must be one of hide, show, show_if_unread; got %s' % sys.argv[i+1])
      i += 2
    elif myarg == u'messagelistvisibility':
      body[u'messageListVisibility'] = sys.argv[i+1].lower().replace(u'_', u'')
      if body[u'messageListVisibility'] not in [u'hide', u'show']:
        systemErrorExit(2, 'message_list_visibility must be show or hide; got %s' % sys.argv[i+1])
      i += 2
    else:
      systemErrorExit(2, '%s is not a valid argument for this command.' % sys.argv[i])
  i = 0
  count = len(users)
  for user in users:
    i += 1
    user, gmail = buildGmailGAPIObject(user)
    if not gmail:
      continue
    print u"Creating label %s for %s (%s/%s)" % (label, user, i, count)
    callGAPI(gmail.users().labels(), u'create', soft_errors=True, userId=user, body=body)

PROCESS_MESSAGE_FUNCTION_TO_ACTION_MAP = {u'delete': u'deleted', u'trash': u'trashed', u'untrash': u'untrashed', u'modify': u'modified'}

def labelsToLabelIds(gmail, labels):
  allLabels = {
    u'INBOX': u'INBOX', u'SPAM': u'SPAM', u'TRASH': u'TRASH',
    u'UNREAD': u'UNREAD', u'STARRED': u'STARRED', u'IMPORTANT': u'IMPORTANT',
    u'SENT': u'SENT', u'DRAFT': u'DRAFT',
    u'CATEGORY_PERSONAL': u'CATEGORY_PERSONAL',
    u'CATEGORY_SOCIAL': u'CATEGORY_SOCIAL',
    u'CATEGORY_PROMOTIONS': u'CATEGORY_PROMOTIONS',
    u'CATEGORY_UPDATES': u'CATEGORY_UPDATES',
    u'CATEGORY_FORUMS': u'CATEGORY_FORUMS',
    }
  labelIds = list()
  for label in labels:
    if label not in allLabels:
      # first refresh labels in user mailbox
      label_results = callGAPI(gmail.users().labels(), u'list',
                               userId=u'me', fields=u'labels(id,name,type)')
      for a_label in label_results[u'labels']:
        if a_label[u'type'] == u'system':
          allLabels[a_label[u'id']] = a_label[u'id']
        else:
          allLabels[a_label[u'name']] = a_label[u'id']
    if label not in allLabels:
      # if still not there, create it
      label_results = callGAPI(gmail.users().labels(), u'create',
                               body={u'labelListVisibility': u'labelShow',
                                     u'messageListVisibility': u'show', u'name': label},
                               userId=u'me', fields=u'id')
      allLabels[label] = label_results[u'id']
    try:
      labelIds.append(allLabels[label])
    except KeyError:
      pass
    if label.find(u'/') != -1:
      # make sure to create parent labels for proper nesting
      parent_label = label[:label.rfind(u'/')]
      while True:
        if not parent_label in allLabels:
          label_result = callGAPI(gmail.users().labels(), u'create',
                                  userId=u'me', body={u'name': parent_label})
          allLabels[parent_label] = label_result[u'id']
        if parent_label.find(u'/') == -1:
          break
        parent_label = parent_label[:parent_label.rfind(u'/')]
  return labelIds

def doProcessMessagesOrThreads(users, function, unit=u'messages'):
  query = None
  doIt = False
  maxToProcess = 1
  body = {}
  i = 5
  while i < len(sys.argv):
    myarg = sys.argv[i].lower().replace(u'_', u'')
    if myarg == u'query':
      query = sys.argv[i+1]
      i += 2
    elif myarg == u'doit':
      doIt = True
      i += 1
    elif myarg in [u'maxtodelete', u'maxtotrash', u'maxtomodify', u'maxtountrash']:
      maxToProcess = int(sys.argv[i+1])
      i += 2
    elif (function == u'modify') and (myarg == u'addlabel'):
      body.setdefault(u'addLabelIds', [])
      body[u'addLabelIds'].append(sys.argv[i+1])
      i += 2
    elif (function == u'modify') and (myarg == u'removelabel'):
      body.setdefault(u'removeLabelIds', [])
      body[u'removeLabelIds'].append(sys.argv[i+1])
      i += 2
    else:
      systemErrorExit(2, '%s is not a valid argument for "gam <users> %s %s"' % (sys.argv[i], function, unit))
  if not query:
    systemErrorExit(2, 'No query specified. You must specify some query!')
  action = PROCESS_MESSAGE_FUNCTION_TO_ACTION_MAP[function]
  for user in users:
    user, gmail = buildGmailGAPIObject(user)
    if not gmail:
      continue
    print u'Searching %s for %s' % (unit, user)
    unitmethod = getattr(gmail.users(), unit)
    page_message = u'Got %%%%total_items%%%% %s for user %s' % (unit, user)
    listResult = callGAPIpages(unitmethod(), u'list', unit, page_message=page_message,
                               userId=u'me', q=query, includeSpamTrash=True, soft_errors=True, fields=u'nextPageToken,{0}(id)'.format(unit))
    result_count = len(listResult)
    if not doIt or result_count == 0:
      print u'would try to %s %s messages for user %s (max %s)\n' % (function, result_count, user, maxToProcess)
      continue
    elif result_count > maxToProcess:
      print u'WARNING: refusing to %s ANY messages for %s since max messages to process is %s and messages to be %s is %s\n' % (function, user, maxToProcess, action, result_count)
      continue
    kwargs = {u'body': {}}
    for my_key in body:
      kwargs[u'body'][my_key] = labelsToLabelIds(gmail, body[my_key])
    i = 0
    if unit == u'messages' and function in [u'delete', u'modify']:
      batchFunction = u'batch%s' % function.title()
      id_batches = [[]]
      for a_unit in listResult:
        id_batches[i].append(a_unit[u'id'])
        if len(id_batches[i]) == 1000:
          i += 1
          id_batches.append([])
      processed_messages = 0
      for id_batch in id_batches:
        kwargs[u'body'][u'ids'] = id_batch
        print u'%s %s messages' % (function, len(id_batch))
        callGAPI(unitmethod(), batchFunction,
                 userId=u'me', **kwargs)
        processed_messages += len(id_batch)
        print u'%s %s of %s messages' % (function, processed_messages, result_count)
      continue
    if not kwargs[u'body']:
      del kwargs[u'body']
    for a_unit in listResult:
      i += 1
      print u' %s %s %s for user %s (%s/%s)' % (function, unit, a_unit[u'id'], user, i, result_count)
      callGAPI(unitmethod(), function,
               id=a_unit[u'id'], userId=u'me', **kwargs)

def doDeleteLabel(users):
  label = sys.argv[5]
  label_name_lower = label.lower()
  for user in users:
    user, gmail = buildGmailGAPIObject(user)
    if not gmail:
      continue
    print u'Getting all labels for %s...' % user
    labels = callGAPI(gmail.users().labels(), u'list', userId=user, fields=u'labels(id,name,type)')
    del_labels = []
    if label == u'--ALL_LABELS--':
      for del_label in labels[u'labels']:
        if del_label[u'type'] == u'system':
          continue
        del_labels.append(del_label)
    elif label[:6].lower() == u'regex:':
      regex = label[6:]
      p = re.compile(regex)
      for del_label in labels[u'labels']:
        if del_label[u'type'] == u'system':
          continue
        elif p.match(del_label[u'name']):
          del_labels.append(del_label)
    else:
      for del_label in labels[u'labels']:
        if label_name_lower == del_label[u'name'].lower():
          del_labels.append(del_label)
          break
      else:
        print u' Error: no such label for %s' % user
        continue
    bcount = 0
    j = 0
    del_me_count = len(del_labels)
    dbatch = gmail.new_batch_http_request()
    for del_me in del_labels:
      j += 1
      print u' deleting label %s (%s/%s)' % (del_me[u'name'], j, del_me_count)
      dbatch.add(gmail.users().labels().delete(userId=user, id=del_me[u'id']), callback=gmail_del_result)
      bcount += 1
      if bcount == 10:
        dbatch.execute()
        dbatch = gmail.new_batch_http_request()
        bcount = 0
    if bcount > 0:
      dbatch.execute()

def gmail_del_result(request_id, response, exception):
  if exception:
    print exception

def showLabels(users):
  i = 5
  onlyUser = showCounts = False
  while i < len(sys.argv):
    myarg = sys.argv[i].lower().replace(u'_', u'')
    if myarg == u'onlyuser':
      onlyUser = True
      i += 1
    elif myarg == u'showcounts':
      showCounts = True
      i += 1
    else:
      systemErrorExit(2, '%s is not a valid argument for "gam <users> show labels"' % sys.argv[i])
  for user in users:
    user, gmail = buildGmailGAPIObject(user)
    if not gmail:
      continue
    labels = callGAPI(gmail.users().labels(), u'list', userId=user, soft_errors=True)
    if labels:
      for label in labels[u'labels']:
        if onlyUser and (label[u'type'] == u'system'):
          continue
        print utils.convertUTF8(label[u'name'])
        for a_key in label:
          if a_key == u'name':
            continue
          print u' %s: %s' % (a_key, label[a_key])
        if showCounts:
          counts = callGAPI(gmail.users().labels(), u'get',
                            userId=user, id=label[u'id'],
                            fields=u'messagesTotal,messagesUnread,threadsTotal,threadsUnread')
          for a_key in counts:
            print u' %s: %s' % (a_key, counts[a_key])
        print u''

def showGmailProfile(users):
  todrive = False
  i = 6
  while i < len(sys.argv):
    myarg = sys.argv[i].lower()
    if myarg == u'todrive':
      todrive = True
      i += 1
    else:
      systemErrorExit(2, '%s is not a valid argument for gam <users> show gmailprofile' % sys.argv[i])
  csvRows = []
  titles = [u'emailAddress']
  i = 0
  count = len(users)
  for user in users:
    i += 1
    user, gmail = buildGmailGAPIObject(user)
    if not gmail:
      continue
    sys.stderr.write(u'Getting Gmail profile for %s\n' % user)
    try:
      results = callGAPI(gmail.users(), u'getProfile',
                         throw_reasons=GAPI_GMAIL_THROW_REASONS,
                         userId=u'me')
      if results:
        for item in results:
          if item not in titles:
            titles.append(item)
        csvRows.append(results)
    except GAPI_serviceNotAvailable:
      entityServiceNotApplicableWarning(u'User', user, i, count)
  sortCSVTitles([u'emailAddress',], titles)
  writeCSVfile(csvRows, titles, list_type=u'Gmail Profiles', todrive=todrive)

def showGplusProfile(users):
  todrive = False
  i = 6
  while i < len(sys.argv):
    myarg = sys.argv[i].lower()
    if myarg == u'todrive':
      todrive = True
      i += 1
    else:
      systemErrorExit(2, '%s is not a valid argument for gam <users> show gplusprofile' % sys.argv[i])
  csvRows = []
  titles = [u'id']
  i = 0
  count = len(users)
  for user in users:
    i += 1
    user, gplus = buildGplusGAPIObject(user)
    if not gplus:
      continue
    sys.stderr.write(u'Getting Gplus profile for %s\n' % user)
    try:
      results = callGAPI(gplus.people(), u'get',
                         throw_reasons=GAPI_GPLUS_THROW_REASONS,
                         userId=u'me')
      if results:
        results = flatten_json(results)
        csvRows.append(results)
        for item in results:
          if item not in titles:
            titles.append(item)
    except GAPI_serviceNotAvailable:
      entityServiceNotApplicableWarning(u'User', user, i, count)
  sortCSVTitles([u'id',], titles)
  writeCSVfile(csvRows, titles, list_type=u'Gplus Profiles', todrive=todrive)

def updateLabels(users):
  label_name = sys.argv[5]
  label_name_lower = label_name.lower()
  body = {}
  i = 6
  while i < len(sys.argv):
    myarg = sys.argv[i].lower().replace(u'_', u'')
    if myarg == u'name':
      body[u'name'] = sys.argv[i+1]
      i += 2
    elif myarg == u'labellistvisibility':
      value = sys.argv[i+1].lower().replace(u'_', u'')
      if value == u'hide':
        body[u'labelListVisibility'] = u'labelHide'
      elif value == u'show':
        body[u'labelListVisibility'] = u'labelShow'
      elif value == u'showifunread':
        body[u'labelListVisibility'] = u'labelShowIfUnread'
      else:
        systemErrorExit(2, 'label_list_visibility must be hide, show, show_if_unread; got %s' % sys.argv[i+1])
      i += 2
    elif myarg == u'messagelistvisibility':
      body[u'messageListVisibility'] = sys.argv[i+1].lower().replace(u'_', u'')
      if body[u'messageListVisibility'] not in [u'hide', u'show']:
        systemErrorExit(2, 'message_list_visibility must be show or hide; got %s' % sys.argv[i+1])
      i += 2
    else:
      systemErrorExit(2, '%s is not a valid argument for "gam <users> update labels"' % sys.argv[i])
  for user in users:
    user, gmail = buildGmailGAPIObject(user)
    if not gmail:
      continue
    labels = callGAPI(gmail.users().labels(), u'list', userId=user, fields=u'labels(id,name)')
    for label in labels[u'labels']:
      if label[u'name'].lower() == label_name_lower:
        callGAPI(gmail.users().labels(), u'patch', soft_errors=True,
                 userId=user, id=label[u'id'], body=body)
        break
    else:
      print u'Error: user does not have a label named %s' % label_name

def renameLabels(users):
  search = u'^Inbox/(.*)$'
  replace = u'%s'
  merge = False
  i = 5
  while i < len(sys.argv):
    myarg = sys.argv[i].lower()
    if myarg == u'search':
      search = sys.argv[i+1]
      i += 2
    elif myarg == u'replace':
      replace = sys.argv[i+1]
      i += 2
    elif myarg == u'merge':
      merge = True
      i += 1
    else:
      systemErrorExit(2, '%s is not a valid argument for "gam <users> rename label"' % sys.argv[i])
  pattern = re.compile(search, re.IGNORECASE)
  for user in users:
    user, gmail = buildGmailGAPIObject(user)
    if not gmail:
      continue
    labels = callGAPI(gmail.users().labels(), u'list', userId=user)
    for label in labels[u'labels']:
      if label[u'type'] == u'system':
        continue
      match_result = re.search(pattern, label[u'name'])
      if match_result is not None:
        try:
          new_label_name = replace % match_result.groups()
        except TypeError:
          systemErrorExit(2, 'The number of subfields ({0}) in search "{1}" does not match the number of subfields ({2}) in replace "{3}"'.format(len(match_result.groups()), search, replace.count(u'%s'), replace))
        print u' Renaming "%s" to "%s"' % (label[u'name'], new_label_name)
        try:
          callGAPI(gmail.users().labels(), u'patch', soft_errors=True, throw_reasons=[GAPI_ABORTED], id=label[u'id'], userId=user, body={u'name': new_label_name})
        except GAPI_aborted:
          if merge:
            print u'  Merging %s label to existing %s label' % (label[u'name'], new_label_name)
            q = u'label:"%s"' % label[u'name']
            messages_to_relabel = callGAPIpages(gmail.users().messages(), u'list', u'messages', userId=user, q=q)
            if len(messages_to_relabel) > 0:
              for new_label in labels[u'labels']:
                if new_label[u'name'].lower() == new_label_name.lower():
                  new_label_id = new_label[u'id']
                  body = {u'addLabelIds': [new_label_id]}
                  break
              j = 1
              for message_to_relabel in messages_to_relabel:
                print u'    relabeling message %s (%s/%s)' % (message_to_relabel[u'id'], j, len(messages_to_relabel))
                callGAPI(gmail.users().messages(), u'modify', userId=user, id=message_to_relabel[u'id'], body=body)
                j += 1
            else:
              print u'   no messages with %s label' % label[u'name']
            print u'   Deleting label %s' % label[u'name']
            callGAPI(gmail.users().labels(), u'delete', id=label[u'id'], userId=user)
          else:
            print u'  Error: looks like %s already exists, not renaming. Use the "merge" argument to merge the labels' % new_label_name

def _getUserGmailLabels(gmail, user, i, count, **kwargs):
  try:
    labels = callGAPI(gmail.users().labels(), u'list',
                      throw_reasons=GAPI_GMAIL_THROW_REASONS,
                      userId=u'me', **kwargs)
    if not labels:
      labels = {u'labels': []}
    return labels
  except GAPI_serviceNotAvailable:
    entityServiceNotApplicableWarning(u'User', user, i, count)
    return None

def _getLabelId(labels, labelName):
  for label in labels[u'labels']:
    if label[u'id'] == labelName or label[u'name'] == labelName:
      return label[u'id']
  return None

def _getLabelName(labels, labelId):
  for label in labels[u'labels']:
    if label[u'id'] == labelId:
      return label[u'name']
  return labelId

def _printFilter(user, userFilter, labels):
  row = {u'User': user, u'id': userFilter[u'id']}
  if u'criteria' in userFilter:
    for item in userFilter[u'criteria']:
      if item in [u'hasAttachment', u'excludeChats']:
        row[item] = item
      elif item == u'size':
        row[item] = u'size {0} {1}'.format(userFilter[u'criteria'][u'sizeComparison'], userFilter[u'criteria'][item])
      elif item == u'sizeComparison':
        pass
      else:
        row[item] = u'{0} {1}'.format(item, userFilter[u'criteria'][item])
  else:
    row[u'error'] = u'NoCriteria'
  if u'action' in userFilter:
    for labelId in userFilter[u'action'].get(u'addLabelIds', []):
      if labelId in FILTER_ADD_LABEL_TO_ARGUMENT_MAP:
        row[FILTER_ADD_LABEL_TO_ARGUMENT_MAP[labelId]] = FILTER_ADD_LABEL_TO_ARGUMENT_MAP[labelId]
      else:
        row[u'label'] = u'label {0}'.format(_getLabelName(labels, labelId))
    for labelId in userFilter[u'action'].get(u'removeLabelIds', []):
      if labelId in FILTER_REMOVE_LABEL_TO_ARGUMENT_MAP:
        row[FILTER_REMOVE_LABEL_TO_ARGUMENT_MAP[labelId]] = FILTER_REMOVE_LABEL_TO_ARGUMENT_MAP[labelId]
    if userFilter[u'action'].get(u'forward'):
      row[u'forward'] = u'forward {0}'.format(userFilter[u'action'][u'forward'])
  else:
    row[u'error'] = u'NoActions'
  return row

def _showFilter(userFilter, j, jcount, labels):
  print u'  Filter: {0}{1}'.format(userFilter[u'id'], currentCount(j, jcount))
  print u'    Criteria:'
  if u'criteria' in userFilter:
    for item in userFilter[u'criteria']:
      if item in [u'hasAttachment', u'excludeChats']:
        print u'      {0}'.format(item)
      elif item == u'size':
        print u'      {0} {1} {2}'.format(item, userFilter[u'criteria'][u'sizeComparison'], userFilter[u'criteria'][item])
      elif item == u'sizeComparison':
        pass
      else:
        print utils.convertUTF8(u'      {0} "{1}"'.format(item, userFilter[u'criteria'][item]))
  else:
    print u'      ERROR: No Filter criteria'
  print u'    Actions:'
  if u'action' in userFilter:
    for labelId in userFilter[u'action'].get(u'addLabelIds', []):
      if labelId in FILTER_ADD_LABEL_TO_ARGUMENT_MAP:
        print u'      {0}'.format(FILTER_ADD_LABEL_TO_ARGUMENT_MAP[labelId])
      else:
        print utils.convertUTF8(u'      label "{0}"'.format(_getLabelName(labels, labelId)))
    for labelId in userFilter[u'action'].get(u'removeLabelIds', []):
      if labelId in FILTER_REMOVE_LABEL_TO_ARGUMENT_MAP:
        print u'      {0}'.format(FILTER_REMOVE_LABEL_TO_ARGUMENT_MAP[labelId])
    if userFilter[u'action'].get(u'forward'):
      print u'    Forwarding Address: {0}'.format(userFilter[u'action'][u'forward'])
  else:
    print u'      ERROR: No Filter actions'
#

def addFilter(users, i):
  body = {}
  addLabelName = None
  addLabelIds = []
  removeLabelIds = []
  while i < len(sys.argv):
    myarg = sys.argv[i].lower()
    if myarg in FILTER_CRITERIA_CHOICES_MAP:
      myarg = FILTER_CRITERIA_CHOICES_MAP[myarg]
      body.setdefault(u'criteria', {})
      if myarg == u'from':
        body[u'criteria'][myarg] = sys.argv[i+1]
        i += 2
      elif myarg == u'to':
        body[u'criteria'][myarg] = sys.argv[i+1]
        i += 2
      elif myarg in [u'subject', u'query', u'negatedQuery']:
        body[u'criteria'][myarg] = sys.argv[i+1]
        i += 2
      elif myarg in [u'hasAttachment', u'excludeChats']:
        body[u'criteria'][myarg] = True
        i += 1
      elif myarg == u'size':
        body[u'criteria'][u'sizeComparison'] = sys.argv[i+1].lower()
        if body[u'criteria'][u'sizeComparison'] not in [u'larger', u'smaller']:
          systemErrorExit(2, 'size must be followed by larger or smaller; got %s' % sys.argv[i+1].lower())
        body[u'criteria'][myarg] = sys.argv[i+2]
        i += 3
    elif myarg in FILTER_ACTION_CHOICES:
      body.setdefault(u'action', {})
      if myarg == u'label':
        addLabelName = sys.argv[i+1]
        i += 2
      elif myarg == u'important':
        addLabelIds.append(u'IMPORTANT')
        if u'IMPORTANT' in removeLabelIds:
          removeLabelIds.remove(u'IMPORTANT')
        i += 1
      elif myarg == u'star':
        addLabelIds.append(u'STARRED')
        i += 1
      elif myarg == u'trash':
        addLabelIds.append(u'TRASH')
        i += 1
      elif myarg == u'notimportant':
        removeLabelIds.append(u'IMPORTANT')
        if u'IMPORTANT' in addLabelIds:
          addLabelIds.remove(u'IMPORTANT')
        i += 1
      elif myarg == u'markread':
        removeLabelIds.append(u'UNREAD')
        i += 1
      elif myarg == u'archive':
        removeLabelIds.append(u'INBOX')
        i += 1
      elif myarg == u'neverspam':
        removeLabelIds.append(u'SPAM')
        i += 1
      elif myarg == u'forward':
        body[u'action'][u'forward'] = sys.argv[i+1]
        i += 2
    else:
      systemErrorExit(2, '%s is not a valid argument for "gam <users> filter"' % sys.argv[i])
  if u'criteria' not in body:
    systemErrorExit(2, 'you must specify a crtieria <{0}> for "gam <users> filter"'.format(u'|'.join(FILTER_CRITERIA_CHOICES_MAP)))
  if u'action' not in body:
    systemErrorExit(2, 'you must specify an action <{0}> for "gam <users> filter"'.format(u'|'.join(FILTER_ACTION_CHOICES)))
  if removeLabelIds:
    body[u'action'][u'removeLabelIds'] = removeLabelIds
  i = 0
  count = len(users)
  for user in users:
    i += 1
    user, gmail = buildGmailGAPIObject(user)
    if not gmail:
      continue
    labels = _getUserGmailLabels(gmail, user, i, count, fields=u'labels(id,name)')
    if not labels:
      continue
    if addLabelIds:
      body[u'action'][u'addLabelIds'] = addLabelIds[:]
    if addLabelName:
      if not addLabelIds:
        body[u'action'][u'addLabelIds'] = []
      addLabelId = _getLabelId(labels, addLabelName)
      if not addLabelId:
        result = callGAPI(gmail.users().labels(), u'create',
                          soft_errors=True,
                          userId=u'me', body={u'name': addLabelName}, fields=u'id')
        if not result:
          continue
        addLabelId = result[u'id']
      body[u'action'][u'addLabelIds'].append(addLabelId)
    print u"Adding filter for %s (%s/%s)" % (user, i, count)
    result = callGAPI(gmail.users().settings().filters(), u'create',
                      soft_errors=True,
                      userId=u'me', body=body)
    if result:
      print u"User: %s, Filter: %s, Added (%s/%s)" % (user, result[u'id'], i, count)

def deleteFilters(users):
  filterId = sys.argv[5]
  i = 0
  count = len(users)
  for user in users:
    i += 1
    user, gmail = buildGmailGAPIObject(user)
    if not gmail:
      continue
    print u"Deleting filter %s for %s (%s/%s)" % (filterId, user, i, count)
    callGAPI(gmail.users().settings().filters(), u'delete',
             soft_errors=True,
             userId=u'me', id=filterId)

def printShowFilters(users, csvFormat):
  if csvFormat:
    todrive = False
    csvRows = []
    titles = [u'User', u'id']
  i = 5
  while i < len(sys.argv):
    myarg = sys.argv[i].lower()
    if csvFormat and myarg == u'todrive':
      todrive = True
      i += 1
    else:
      systemErrorExit(2, '%s is not a valid argument for "gam <users> %s filter"' % (myarg, [u'show', u'print'][csvFormat]))
  i = 0
  count = len(users)
  for user in users:
    i += 1
    user, gmail = buildGmailGAPIObject(user)
    if not gmail:
      continue
    labels = callGAPI(gmail.users().labels(), u'list',
                      soft_errors=True,
                      userId=u'me', fields=u'labels(id,name)')
    if not labels:
      labels = {u'labels': []}
    result = callGAPI(gmail.users().settings().filters(), u'list',
                      soft_errors=True,
                      userId=u'me')
    jcount = len(result.get(u'filter', [])) if (result) else 0
    if not csvFormat:
      print u'User: {0}, Filters: ({1}/{2})'.format(user, i, count)
      if jcount == 0:
        continue
      j = 0
      for userFilter in result[u'filter']:
        j += 1
        _showFilter(userFilter, j, jcount, labels)
    else:
      if jcount == 0:
        continue
      for userFilter in result[u'filter']:
        row = _printFilter(user, userFilter, labels)
        for item in row:
          if item not in titles:
            titles.append(item)
        csvRows.append(row)
  if csvFormat:
    sortCSVTitles([u'User', u'id'], titles)
    writeCSVfile(csvRows, titles, u'Filters', todrive)

def infoFilters(users):
  filterId = sys.argv[5]
  i = 0
  count = len(users)
  for user in users:
    i += 1
    user, gmail = buildGmailGAPIObject(user)
    if not gmail:
      continue
    labels = callGAPI(gmail.users().labels(), u'list',
                      soft_errors=True,
                      userId=u'me', fields=u'labels(id,name)')
    if not labels:
      labels = {u'labels': []}
    result = callGAPI(gmail.users().settings().filters(), u'get',
                      soft_errors=True,
                      userId=u'me', id=filterId)
    if result:
      print u'User: {0}, Filter: ({1}/{2})'.format(user, i, count)
      _showFilter(result, 1, 1, labels)

def doForward(users):
  enable = getBoolean(sys.argv[4], u'gam <users> forward')
  body = {u'enabled': enable}
  i = 5
  while i < len(sys.argv):
    myarg = sys.argv[i].lower()
    if myarg in EMAILSETTINGS_FORWARD_POP_ACTION_CHOICES_MAP:
      body[u'disposition'] = EMAILSETTINGS_FORWARD_POP_ACTION_CHOICES_MAP[myarg]
      i += 1
    elif myarg == u'confirm':
      i += 1
    elif myarg.find(u'@') != -1:
      body[u'emailAddress'] = sys.argv[i]
      i += 1
    else:
      systemErrorExit(2, '%s is not a valid argument for "gam <users> forward"' % myarg)
  if enable and (not body.get(u'disposition') or not body.get(u'emailAddress')):
    systemErrorExit(2, 'you must specify an action and a forwarding address for "gam <users> forward')
  i = 0
  count = len(users)
  for user in users:
    i += 1
    user, gmail = buildGmailGAPIObject(user)
    if not gmail:
      continue
    if enable:
      print u"User: %s, Forward Enabled: %s, Forwarding Address: %s, Action: %s (%s/%s)" % (user, enable, body[u'emailAddress'], body[u'disposition'], i, count)
    else:
      print u"User: %s, Forward Enabled: %s (%s/%s)" % (user, enable, i, count)
    callGAPI(gmail.users().settings(), u'updateAutoForwarding',
             soft_errors=True,
             userId=u'me', body=body)

def printShowForward(users, csvFormat):
  def _showForward(user, i, count, result):
    if u'enabled' in result:
      enabled = result[u'enabled']
      if enabled:
        print u"User: %s, Forward Enabled: %s, Forwarding Address: %s, Action: %s (%s/%s)" % (user, enabled, result[u'emailAddress'], result[u'disposition'], i, count)
      else:
        print u"User: %s, Forward Enabled: %s (%s/%s)" % (user, enabled, i, count)
    else:
      enabled = result[u'enable'] == u'true'
      if enabled:
        print u"User: %s, Forward Enabled: %s, Forwarding Address: %s, Action: %s (%s/%s)" % (user, enabled, result[u'forwardTo'], EMAILSETTINGS_OLD_NEW_OLD_FORWARD_ACTION_MAP[result[u'action']], i, count)
      else:
        print u"User: %s, Forward Enabled: %s (%s/%s)" % (user, enabled, i, count)

  def _printForward(user, result):
    if u'enabled' in result:
      row = {u'User': user, u'forwardEnabled': result[u'enabled']}
      if result[u'enabled']:
        row[u'forwardTo'] = result[u'emailAddress']
        row[u'disposition'] = result[u'disposition']
    else:
      row = {u'User': user, u'forwardEnabled': result[u'enable']}
      if result[u'enable'] == u'true':
        row[u'forwardTo'] = result[u'forwardTo']
        row[u'disposition'] = EMAILSETTINGS_OLD_NEW_OLD_FORWARD_ACTION_MAP[result[u'action']]
    csvRows.append(row)

  if csvFormat:
    todrive = False
    csvRows = []
    titles = [u'User', u'forwardEnabled', u'forwardTo', u'disposition']
  i = 5
  while i < len(sys.argv):
    myarg = sys.argv[i].lower()
    if csvFormat and myarg == u'todrive':
      todrive = True
      i += 1
    else:
      systemErrorExit(2, '%s is not a valid argument for "gam <users> %s forward"' % (myarg, [u'show', u'print'][csvFormat]))
  i = 0
  count = len(users)
  for user in users:
    i += 1
    user, gmail = buildGmailGAPIObject(user)
    if not gmail:
      continue
    result = callGAPI(gmail.users().settings(), u'getAutoForwarding',
                      soft_errors=True,
                      userId=u'me')
    if result:
      if not csvFormat:
        _showForward(user, i, count, result)
      else:
        _printForward(user, result)
  if csvFormat:
    writeCSVfile(csvRows, titles, u'Forward', todrive)

def addForwardingAddresses(users):
  emailAddress = normalizeEmailAddressOrUID(sys.argv[5], noUid=True)
  body = {u'forwardingEmail':  emailAddress}
  i = 0
  count = len(users)
  for user in users:
    i += 1
    user, gmail = buildGmailGAPIObject(user)
    if not gmail:
      continue
    print u"Adding Forwarding Address %s for %s (%s/%s)" % (emailAddress, user, i, count)
    callGAPI(gmail.users().settings().forwardingAddresses(), u'create',
             soft_errors=True,
             userId=u'me', body=body)

def deleteForwardingAddresses(users):
  emailAddress = normalizeEmailAddressOrUID(sys.argv[5], noUid=True)
  i = 0
  count = len(users)
  for user in users:
    i += 1
    user, gmail = buildGmailGAPIObject(user)
    if not gmail:
      continue
    print u"Deleting Forwarding Address %s for %s (%s/%s)" % (emailAddress, user, i, count)
    callGAPI(gmail.users().settings().forwardingAddresses(), u'delete',
             soft_errors=True,
             userId=u'me', forwardingEmail=emailAddress)

def printShowForwardingAddresses(users, csvFormat):
  if csvFormat:
    todrive = False
    csvRows = []
    titles = [u'User', u'forwardingEmail', u'verificationStatus']
  i = 5
  while i < len(sys.argv):
    myarg = sys.argv[i].lower()
    if csvFormat and myarg == u'todrive':
      todrive = True
      i += 1
    else:
      systemErrorExit(2, '%s is not a valid argument for "gam <users> %s forwardingaddresses"' % (myarg, [u'show', u'print'][csvFormat]))
  i = 0
  count = len(users)
  for user in users:
    i += 1
    user, gmail = buildGmailGAPIObject(user)
    if not gmail:
      continue
    result = callGAPI(gmail.users().settings().forwardingAddresses(), u'list',
                      soft_errors=True,
                      userId=u'me')
    jcount = len(result.get(u'forwardingAddresses', [])) if (result) else 0
    if not csvFormat:
      print u'User: {0}, Forwarding Addresses: ({1}/{2})'.format(user, i, count)
      if jcount == 0:
        continue
      j = 0
      for forward in result[u'forwardingAddresses']:
        j += 1
        print u'  Forwarding Address: {0}, Verification Status: {1} ({2}/{3})'.format(forward[u'forwardingEmail'], forward[u'verificationStatus'], j, jcount)
    else:
      if jcount == 0:
        continue
      for forward in result[u'forwardingAddresses']:
        row = {u'User': user, u'forwardingEmail': forward[u'forwardingEmail'], u'verificationStatus': forward[u'verificationStatus']}
        csvRows.append(row)
  if csvFormat:
    writeCSVfile(csvRows, titles, u'Forwarding Addresses', todrive)

def infoForwardingAddresses(users):
  emailAddress = normalizeEmailAddressOrUID(sys.argv[5], noUid=True)
  i = 0
  count = len(users)
  for user in users:
    i += 1
    user, gmail = buildGmailGAPIObject(user)
    if not gmail:
      continue
    forward = callGAPI(gmail.users().settings().forwardingAddresses(), u'get',
                       soft_errors=True,
                       userId=u'me', forwardingEmail=emailAddress)
    if forward:
      print u'User: {0}, Forwarding Address: {1}, Verification Status: {2} ({3}/{4})'.format(user, forward[u'forwardingEmail'], forward[u'verificationStatus'], i, count)

def doSignature(users):
  tagReplacements = {}
  i = 4
  if sys.argv[i].lower() == u'file':
    filename = sys.argv[i+1]
    i, encoding = getCharSet(i+2)
    signature = readFile(filename, encoding=encoding)
  else:
    signature = getString(i, u'String', minLen=0)
    i += 1
  body = {}
  html = False
  while i < len(sys.argv):
    myarg = sys.argv[i].lower()
    if myarg == u'html':
      html = True
      i += 1
    else:
      i = getSendAsAttributes(i, myarg, body, tagReplacements, u'signature')
  body[u'signature'] = _processSignature(tagReplacements, signature, html)
  i = 0
  count = len(users)
  for user in users:
    i += 1
    user, gmail = buildGmailGAPIObject(user)
    if not gmail:
      continue
    print u'Setting Signature for {0} ({1}/{2})'.format(user, i, count)
    callGAPI(gmail.users().settings().sendAs(), u'patch',
             soft_errors=True,
             userId=u'me', body=body, sendAsEmail=user)

def getSignature(users):
  formatSig = False
  i = 5
  while i < len(sys.argv):
    myarg = sys.argv[i].lower()
    if myarg == u'format':
      formatSig = True
      i += 1
    else:
      systemErrorExit(2, '%s is not a valid argument for "gam <users> show signature"' % sys.argv[i])
  i = 0
  count = len(users)
  for user in users:
    i += 1
    user, gmail = buildGmailGAPIObject(user)
    if not gmail:
      continue
    result = callGAPI(gmail.users().settings().sendAs(), u'get',
                      soft_errors=True,
                      userId=u'me', sendAsEmail=user)
    if result:
      _showSendAs(result, i, count, formatSig)

def doVacation(users):
  enable = getBoolean(sys.argv[4], u'gam <users> vacation')
  body = {u'enableAutoReply': enable}
  if enable:
    responseBodyType = u'responseBodyPlainText'
    message = None
    tagReplacements = {}
    i = 5
    while i < len(sys.argv):
      myarg = sys.argv[i].lower()
      if myarg == u'subject':
        body[u'responseSubject'] = sys.argv[i+1]
        i += 2
      elif myarg == u'message':
        message = sys.argv[i+1]
        i += 2
      elif myarg == u'file':
        filename = sys.argv[i+1]
        i, encoding = getCharSet(i+2)
        message = readFile(filename, encoding=encoding)
      elif myarg == u'replace':
        matchTag = getString(i+1, u'Tag')
        matchReplacement = getString(i+2, u'String', minLen=0)
        tagReplacements[matchTag] = matchReplacement
        i += 3
      elif myarg == u'html':
        responseBodyType = u'responseBodyHtml'
        i += 1
      elif myarg == u'contactsonly':
        body[u'restrictToContacts'] = True
        i += 1
      elif myarg == u'domainonly':
        body[u'restrictToDomain'] = True
        i += 1
      elif myarg == u'startdate':
        body[u'startTime'] = getYYYYMMDD(sys.argv[i+1], returnTimeStamp=True)
        i += 2
      elif myarg == u'enddate':
        body[u'endTime'] = getYYYYMMDD(sys.argv[i+1], returnTimeStamp=True)
        i += 2
      else:
        systemErrorExit(2, '%s is not a valid argument for "gam <users> vacation"' % sys.argv[i])
    if message:
      if responseBodyType == u'responseBodyHtml':
        message = message.replace(u'\r', u'').replace(u'\\n', u'<br/>')
      else:
        message = message.replace(u'\r', u'').replace(u'\\n', u'\n')
      if tagReplacements:
        message = _processTags(tagReplacements, message)
      body[responseBodyType] = message
    if not message and not body.get(u'responseSubject'):
      systemErrorExit(2, 'You must specify a non-blank subject or message!')
  i = 0
  count = len(users)
  for user in users:
    i += 1
    user, gmail = buildGmailGAPIObject(user)
    if not gmail:
      continue
    print u"Setting Vacation for %s (%s/%s)" % (user, i, count)
    callGAPI(gmail.users().settings(), u'updateVacation',
             soft_errors=True,
             userId=u'me', body=body)

def getVacation(users):
  formatReply = False
  i = 5
  while i < len(sys.argv):
    myarg = sys.argv[i].lower()
    if myarg == u'format':
      formatReply = True
      i += 1
    else:
      systemErrorExit(2, '%s is not a valid argument for "gam <users> show vacation"' % sys.argv[i])
  i = 0
  count = len(users)
  for user in users:
    i += 1
    user, gmail = buildGmailGAPIObject(user)
    if not gmail:
      continue
    result = callGAPI(gmail.users().settings(), u'getVacation',
                      soft_errors=True,
                      userId=u'me')
    if result:
      enabled = result[u'enableAutoReply']
      print u'User: {0}, Vacation: ({1}/{2})'.format(user, i, count)
      print u'  Enabled: {0}'.format(enabled)
      if enabled:
        print u'  Contacts Only: {0}'.format(result[u'restrictToContacts'])
        print u'  Domain Only: {0}'.format(result[u'restrictToDomain'])
        if u'startTime' in result:
          print u'  Start Date: {0}'.format(datetime.datetime.fromtimestamp(int(result[u'startTime'])/1000).strftime('%Y-%m-%d'))
        else:
          print u'  Start Date: Started'
        if u'endTime' in result:
          print u'  End Date: {0}'.format(datetime.datetime.fromtimestamp(int(result[u'endTime'])/1000).strftime('%Y-%m-%d'))
        else:
          print u'  End Date: Not specified'
        print utils.convertUTF8(u'  Subject: {0}'.format(result.get(u'responseSubject', u'None')))
        sys.stdout.write(u'  Message:\n   ')
        if result.get(u'responseBodyPlainText'):
          print utils.convertUTF8(utils.indentMultiLineText(result[u'responseBodyPlainText'], n=4))
        elif result.get(u'responseBodyHtml'):
          if formatReply:
            print utils.convertUTF8(utils.indentMultiLineText(utils.dehtml(result[u'responseBodyHtml']), n=4))
          else:
            print utils.convertUTF8(utils.indentMultiLineText(result[u'responseBodyHtml'], n=4))
        else:
          print u'None'

def doDelSchema():
  cd = buildGAPIObject(u'directory')
  schemaKey = sys.argv[3]
  callGAPI(cd.schemas(), u'delete', customerId=GC_Values[GC_CUSTOMER_ID], schemaKey=schemaKey)
  print u'Deleted schema %s' % schemaKey

def doCreateOrUpdateUserSchema(updateCmd):
  cd = buildGAPIObject(u'directory')
  schemaKey = sys.argv[3]
  if updateCmd:
    cmd = u'update'
    try:
      body = callGAPI(cd.schemas(), u'get', throw_reasons=[GAPI_NOT_FOUND], customerId=GC_Values[GC_CUSTOMER_ID], schemaKey=schemaKey)
    except GAPI_notFound:
      systemErrorExit(3, 'Schema %s does not exist.' % schemaKey)
  else: # create
    cmd = u'create'
    body = {u'schemaName': schemaKey, u'fields': []}
  i = 4
  while i < len(sys.argv):
    myarg = sys.argv[i].lower()
    if myarg == u'field':
      if updateCmd: # clear field if it exists on update
        for n, field in enumerate(body[u'fields']):
          if field[u'fieldName'].lower() == sys.argv[i+1].lower():
            del body[u'fields'][n]
            break
      a_field = {u'fieldName': sys.argv[i+1]}
      i += 2
      while True:
        myarg = sys.argv[i].lower()
        if myarg == u'type':
          a_field[u'fieldType'] = sys.argv[i+1].upper()
          if a_field[u'fieldType'] not in [u'BOOL', u'DOUBLE', u'EMAIL', u'INT64', u'PHONE', u'STRING']:
            systemErrorExit(2, 'type must be one of bool, double, email, int64, phone, string; got %s' % a_field[u'fieldType'])
          i += 2
        elif myarg == u'multivalued':
          a_field[u'multiValued'] = True
          i += 1
        elif myarg == u'indexed':
          a_field[u'indexed'] = True
          i += 1
        elif myarg == u'restricted':
          a_field[u'readAccessType'] = u'ADMINS_AND_SELF'
          i += 1
        elif myarg == u'range':
          a_field[u'numericIndexingSpec'] = {u'minValue': sys.argv[i+1], u'maxValue': sys.argv[i+2]}
          i += 3
        elif myarg == u'endfield':
          body[u'fields'].append(a_field)
          i += 1
          break
        else:
          systemErrorExit(2, '%s is not a valid argument for "gam %s schema"' % (sys.argv[i], cmd))
    elif updateCmd and myarg == u'deletefield':
      for n, field in enumerate(body[u'fields']):
        if field[u'fieldName'].lower() == sys.argv[i+1].lower():
          del body[u'fields'][n]
          break
      else:
        systemErrorExit(3, 'field %s not found in schema %s' % (sys.argv[i+1], schemaKey))
      i += 2
    else:
      systemErrorExit(2, '%s is not a valid argument for "gam %s schema"' % (sys.argv[i], cmd))
  if updateCmd:
    result = callGAPI(cd.schemas(), u'update', customerId=GC_Values[GC_CUSTOMER_ID], body=body, schemaKey=schemaKey)
    print u'Updated user schema %s' % result[u'schemaName']
  else:
    result = callGAPI(cd.schemas(), u'insert', customerId=GC_Values[GC_CUSTOMER_ID], body=body)
    print u'Created user schema %s' % result[u'schemaName']

def _showSchema(schema):
  print u'Schema: %s' % schema[u'schemaName']
  for a_key in schema:
    if a_key not in [u'schemaName', u'fields', u'etag', u'kind']:
      print u' %s: %s' % (a_key, schema[a_key])
  for field in schema[u'fields']:
    print u' Field: %s' % field[u'fieldName']
    for a_key in field:
      if a_key not in [u'fieldName', u'kind', u'etag']:
        print u'  %s: %s' % (a_key, field[a_key])

def doPrintShowUserSchemas(csvFormat):
  cd = buildGAPIObject(u'directory')
  if csvFormat:
    todrive = False
    csvRows = []
    titles = []
  i = 3
  while i < len(sys.argv):
    myarg = sys.argv[i].lower()
    if csvFormat and myarg == u'todrive':
      todrive = True
      i += 1
    else:
      systemErrorExit(2, '%s is not a valid argument for "gam %s schemas"' % (myarg, [u'show', u'print'][csvFormat]))
  schemas = callGAPI(cd.schemas(), u'list', customerId=GC_Values[GC_CUSTOMER_ID])
  if not schemas or u'schemas' not in schemas:
    return
  for schema in schemas[u'schemas']:
    if not csvFormat:
      _showSchema(schema)
    else:
      row = {u'fields.Count': len(schema[u'fields'])}
      addRowTitlesToCSVfile(flatten_json(schema, flattened=row), csvRows, titles)
  if csvFormat:
    sortCSVTitles([u'schemaId', u'schemaName', u'fields.Count'], titles)
    writeCSVfile(csvRows, titles, u'User Schemas', todrive)

def doGetUserSchema():
  cd = buildGAPIObject(u'directory')
  schemaKey = sys.argv[3]
  schema = callGAPI(cd.schemas(), u'get', customerId=GC_Values[GC_CUSTOMER_ID], schemaKey=schemaKey)
  _showSchema(schema)

def getUserAttributes(i, cd, updateCmd=False):
  def getEntryType(i, entry, entryTypes, setTypeCustom=True, customKeyword=u'custom', customTypeKeyword=u'customType'):
    """ Get attribute entry type
    entryTypes is list of pre-defined types, a|b|c
    Allow a|b|c|<String>, a|b|c|custom <String>
    setTypeCustom=True, For all fields except organizations, when setting a custom type you do:
    entry[u'type'] = u'custom'
    entry[u'customType'] = <String>
    setTypeCustom=False, For organizations, you don't set entry[u'type'] = u'custom'
    Preserve case of custom types
    """
    utype = sys.argv[i]
    ltype = utype.lower()
    if ltype == customKeyword:
      i += 1
      utype = sys.argv[i]
      ltype = utype.lower()
    if ltype in entryTypes:
      entry[u'type'] = ltype
      entry.pop(customTypeKeyword, None)
    else:
      entry[customTypeKeyword] = utype
      if setTypeCustom:
        entry[u'type'] = customKeyword
      else:
        entry.pop(u'type', None)
    return i+1

  def checkClearBodyList(i, body, itemName):
    if sys.argv[i].lower() == u'clear':
      body.pop(itemName, None)
      body[itemName] = None
      return True
    return False

  def appendItemToBodyList(body, itemName, itemValue, checkSystemId=False):
    if (itemName in body) and (body[itemName] is None):
      del body[itemName]
    body.setdefault(itemName, [])
# Throw an error if multiple items are marked primary
    if itemValue.get(u'primary', False):
      for citem in body[itemName]:
        if citem.get(u'primary', False):
          if not checkSystemId or itemValue.get(u'systemId') == citem.get(u'systemId'):
            systemErrorExit(2, 'Multiple {0} are marked primary, only one can be primary'.format(itemName))
    body[itemName].append(itemValue)

  def _splitSchemaNameDotFieldName(sn_fn, fnRequired=True):
    if sn_fn.find(u'.') != -1:
      schemaName, fieldName = sn_fn.split(u'.', 1)
      schemaName = schemaName.strip()
      fieldName = fieldName.strip()
      if schemaName and fieldName:
        return (schemaName, fieldName)
    elif not fnRequired:
      schemaName = sn_fn.strip()
      if schemaName:
        return (schemaName, None)
    systemErrorExit(2, '%s is not a valid custom schema.field name.' % sn_fn)

  if updateCmd:
    body = {}
    need_password = False
  else:
    body = {u'name': {u'givenName': u'Unknown', u'familyName': u'Unknown'}}
    body[u'primaryEmail'] = normalizeEmailAddressOrUID(sys.argv[i], noUid=True)
    i += 1
    need_password = True
  need_to_hash_password = True
  admin_body = {}
  while i < len(sys.argv):
    myarg = sys.argv[i].lower()
    if myarg in [u'firstname', u'givenname']:
      body.setdefault(u'name', {})
      body[u'name'][u'givenName'] = sys.argv[i+1]
      i += 2
    elif myarg in [u'lastname', u'familyname']:
      body.setdefault(u'name', {})
      body[u'name'][u'familyName'] = sys.argv[i+1]
      i += 2
    elif myarg in [u'username', u'email', u'primaryemail'] and updateCmd:
      body[u'primaryEmail'] = normalizeEmailAddressOrUID(sys.argv[i+1], noUid=True)
      i += 2
    elif myarg == u'customerid' and updateCmd:
      body[u'customerId'] = sys.argv[i+1]
      i += 2
    elif myarg == u'password':
      need_password = False
      body[u'password'] = sys.argv[i+1]
      if body[u'password'].lower() == u'random':
        need_password = True
      i += 2
    elif myarg == u'admin':
      admin_body[u'status'] = getBoolean(sys.argv[i+1], myarg)
      i += 2
    elif myarg == u'suspended':
      body[u'suspended'] = getBoolean(sys.argv[i+1], myarg)
      i += 2
    elif myarg == u'gal':
      body[u'includeInGlobalAddressList'] = getBoolean(sys.argv[i+1], myarg)
      i += 2
    elif myarg in [u'sha', u'sha1', u'sha-1']:
      body[u'hashFunction'] = u'SHA-1'
      need_to_hash_password = False
      i += 1
    elif myarg == u'md5':
      body[u'hashFunction'] = u'MD5'
      need_to_hash_password = False
      i += 1
    elif myarg == u'crypt':
      body[u'hashFunction'] = u'crypt'
      need_to_hash_password = False
      i += 1
    elif myarg == u'nohash':
      need_to_hash_password = False
      i += 1
    elif myarg == u'changepassword':
      body[u'changePasswordAtNextLogin'] = getBoolean(sys.argv[i+1], myarg)
      i += 2
    elif myarg == u'ipwhitelisted':
      body[u'ipWhitelisted'] = getBoolean(sys.argv[i+1], myarg)
      i += 2
    elif myarg == u'agreedtoterms':
      body[u'agreedToTerms'] = getBoolean(sys.argv[i+1], myarg)
      i += 2
    elif myarg in [u'org', u'ou']:
      body[u'orgUnitPath'] = sys.argv[i+1]
      if body[u'orgUnitPath'][0] != u'/':
        body[u'orgUnitPath'] = u'/%s' % body[u'orgUnitPath']
      i += 2
    elif myarg in [u'language', u'languages']:
      i += 1
      if checkClearBodyList(i, body, u'languages'):
        i += 1
        continue
      for language in sys.argv[i].replace(u',', u' ').split():
        if language.lower() in LANGUAGE_CODES_MAP:
          appendItemToBodyList(body, u'languages', {u'languageCode': LANGUAGE_CODES_MAP[language.lower()]})
        else:
          appendItemToBodyList(body, u'languages', {u'customLanguage': language})
      i += 1
    elif myarg == u'gender':
      i += 1
      if checkClearBodyList(i, body, u'gender'):
        i += 1
        continue
      gender = {}
      i = getEntryType(i, gender, USER_GENDER_TYPES, customKeyword=u'other', customTypeKeyword=u'customGender')
      if (i < len(sys.argv)) and (sys.argv[i].lower() == u'addressmeas'):
        gender[u'addressMeAs'] = getString(i+1, u'String')
        i += 2
      body[u'gender'] = gender
    elif myarg in [u'address', u'addresses']:
      i += 1
      if checkClearBodyList(i, body, u'addresses'):
        i += 1
        continue
      address = {}
      if sys.argv[i].lower() != u'type':
        systemErrorExit(2, 'wrong format for account address details. Expected type got %s' % sys.argv[i])
      i = getEntryType(i+1, address, USER_ADDRESS_TYPES)
      if sys.argv[i].lower() in [u'unstructured', u'formatted']:
        i += 1
        address[u'sourceIsStructured'] = False
        address[u'formatted'] = sys.argv[i].replace(u'\\n', u'\n')
        i += 1
      while True:
        myopt = sys.argv[i].lower()
        if myopt == u'pobox':
          address[u'poBox'] = sys.argv[i+1]
          i += 2
        elif myopt == u'extendedaddress':
          address[u'extendedAddress'] = sys.argv[i+1]
          i += 2
        elif myopt == u'streetaddress':
          address[u'streetAddress'] = sys.argv[i+1]
          i += 2
        elif myopt == u'locality':
          address[u'locality'] = sys.argv[i+1]
          i += 2
        elif myopt == u'region':
          address[u'region'] = sys.argv[i+1]
          i += 2
        elif myopt == u'postalcode':
          address[u'postalCode'] = sys.argv[i+1]
          i += 2
        elif myopt == u'country':
          address[u'country'] = sys.argv[i+1]
          i += 2
        elif myopt == u'countrycode':
          address[u'countryCode'] = sys.argv[i+1]
          i += 2
        elif myopt in [u'notprimary', u'primary']:
          address[u'primary'] = myopt == u'primary'
          i += 1
          break
        else:
          systemErrorExit(2, 'invalid argument (%s) for account address details' % sys.argv[i])
      appendItemToBodyList(body, u'addresses', address)
    elif myarg in [u'emails', u'otheremail', u'otheremails']:
      i += 1
      if checkClearBodyList(i, body, u'emails'):
        i += 1
        continue
      an_email = {}
      i = getEntryType(i, an_email, USER_EMAIL_TYPES)
      an_email[u'address'] = sys.argv[i]
      i += 1
      appendItemToBodyList(body, u'emails', an_email)
    elif myarg in [u'im', u'ims']:
      i += 1
      if checkClearBodyList(i, body, u'ims'):
        i += 1
        continue
      im = {}
      if sys.argv[i].lower() != u'type':
        systemErrorExit(2, 'wrong format for account im details. Expected type got %s' % sys.argv[i])
      i = getEntryType(i+1, im, USER_IM_TYPES)
      if sys.argv[i].lower() != u'protocol':
        systemErrorExit(2, 'wrong format for account details. Expected protocol got %s' % sys.argv[i])
      i += 1
      im[u'protocol'] = sys.argv[i].lower()
      if im[u'protocol'] not in [u'custom_protocol', u'aim', u'gtalk', u'icq', u'jabber', u'msn', u'net_meeting', u'qq', u'skype', u'yahoo']:
        systemErrorExit(2, 'protocol must be one of custom_protocol, aim, gtalk, icq, jabber, msn, net_meeting, qq, skype, yahoo; got %s' % im[u'protocol'])
      if im[u'protocol'] == u'custom_protocol':
        i += 1
        im[u'customProtocol'] = sys.argv[i]
      i += 1
      # Backwards compatability: notprimary|primary on either side of IM address
      myopt = sys.argv[i].lower()
      if myopt in [u'notprimary', u'primary']:
        im[u'primary'] = myopt == u'primary'
        i += 1
      im[u'im'] = sys.argv[i]
      i += 1
      myopt = sys.argv[i].lower()
      if myopt in [u'notprimary', u'primary']:
        im[u'primary'] = myopt == u'primary'
        i += 1
      appendItemToBodyList(body, u'ims', im)
    elif myarg in [u'organization', u'organizations']:
      i += 1
      if checkClearBodyList(i, body, u'organizations'):
        i += 1
        continue
      organization = {}
      while True:
        myopt = sys.argv[i].lower()
        if myopt == u'name':
          organization[u'name'] = sys.argv[i+1]
          i += 2
        elif myopt == u'title':
          organization[u'title'] = sys.argv[i+1]
          i += 2
        elif myopt == u'customtype':
          organization[u'customType'] = sys.argv[i+1]
          organization.pop(u'type', None)
          i += 2
        elif myopt == u'type':
          i = getEntryType(i+1, organization, USER_ORGANIZATION_TYPES, setTypeCustom=False)
        elif myopt == u'department':
          organization[u'department'] = sys.argv[i+1]
          i += 2
        elif myopt == u'symbol':
          organization[u'symbol'] = sys.argv[i+1]
          i += 2
        elif myopt == u'costcenter':
          organization[u'costCenter'] = sys.argv[i+1]
          i += 2
        elif myopt == u'location':
          organization[u'location'] = sys.argv[i+1]
          i += 2
        elif myopt == u'description':
          organization[u'description'] = sys.argv[i+1]
          i += 2
        elif myopt == u'domain':
          organization[u'domain'] = sys.argv[i+1]
          i += 2
        elif myopt in [u'notprimary', u'primary']:
          organization[u'primary'] = myopt == u'primary'
          i += 1
          break
        else:
          systemErrorExit(2, 'invalid argument (%s) for account organization details' % sys.argv[i])
      appendItemToBodyList(body, u'organizations', organization)
    elif myarg in [u'phone', u'phones']:
      i += 1
      if checkClearBodyList(i, body, u'phones'):
        i += 1
        continue
      phone = {}
      while True:
        myopt = sys.argv[i].lower()
        if myopt == u'value':
          phone[u'value'] = sys.argv[i+1]
          i += 2
        elif myopt == u'type':
          i = getEntryType(i+1, phone, USER_PHONE_TYPES)
        elif myopt in [u'notprimary', u'primary']:
          phone[u'primary'] = myopt == u'primary'
          i += 1
          break
        else:
          systemErrorExit(2, 'invalid argument (%s) for account phone details' % sys.argv[i])
      appendItemToBodyList(body, u'phones', phone)
    elif myarg in [u'relation', u'relations']:
      i += 1
      if checkClearBodyList(i, body, u'relations'):
        i += 1
        continue
      relation = {}
      i = getEntryType(i, relation, USER_RELATION_TYPES)
      relation[u'value'] = sys.argv[i]
      i += 1
      appendItemToBodyList(body, u'relations', relation)
    elif myarg in [u'externalid', u'externalids']:
      i += 1
      if checkClearBodyList(i, body, u'externalIds'):
        i += 1
        continue
      externalid = {}
      i = getEntryType(i, externalid, USER_EXTERNALID_TYPES)
      externalid[u'value'] = sys.argv[i]
      i += 1
      appendItemToBodyList(body, u'externalIds', externalid)
    elif myarg in [u'website', u'websites']:
      i += 1
      if checkClearBodyList(i, body, u'websites'):
        i += 1
        continue
      website = {}
      i = getEntryType(i, website, USER_WEBSITE_TYPES)
      website[u'value'] = sys.argv[i]
      i += 1
      myopt = sys.argv[i].lower()
      if myopt in [u'notprimary', u'primary']:
        website[u'primary'] = myopt == u'primary'
        i += 1
      appendItemToBodyList(body, u'websites', website)
    elif myarg in [u'note', u'notes']:
      i += 1
      if checkClearBodyList(i, body, u'notes'):
        i += 1
        continue
      note = {}
      if sys.argv[i].lower() in [u'text_plain', u'text_html']:
        note[u'contentType'] = sys.argv[i].lower()
        i += 1
      if sys.argv[i].lower() == u'file':
        filename = sys.argv[i+1]
        i, encoding = getCharSet(i+2)
        note[u'value'] = readFile(filename, encoding=encoding)
      else:
        note[u'value'] = sys.argv[i].replace(u'\\n', u'\n')
        i += 1
      body[u'notes'] = note
    elif myarg in [u'location', u'locations']:
      i += 1
      if checkClearBodyList(i, body, u'locations'):
        i += 1
        continue
      location = {u'type': u'desk', u'area': u''}
      while True:
        myopt = sys.argv[i].lower()
        if myopt == u'type':
          i = getEntryType(i+1, location, USER_LOCATION_TYPES)
        elif myopt == u'area':
          location[u'area'] = sys.argv[i+1]
          i += 2
        elif myopt in [u'building', u'buildingid']:
          location[u'buildingId'] = _getBuildingByNameOrId(cd, sys.argv[i+1])
          i += 2
        elif myopt in [u'desk', u'deskcode']:
          location[u'deskCode'] = sys.argv[i+1]
          i += 2
        elif myopt in [u'floor', u'floorname']:
          location[u'floorName'] = sys.argv[i+1]
          i += 2
        elif myopt in [u'section', u'floorsection']:
          location[u'floorSection'] = sys.argv[i+1]
          i += 2
        elif myopt in [u'endlocation']:
          i += 1
          break
        else:
          systemErrorExit(3, '%s is not a valid argument for user location details. Make sure user location details end with an endlocation argument')
      appendItemToBodyList(body, u'locations', location)
    elif myarg in [u'ssh', u'sshkeys', u'sshpublickeys']:
      i += 1
      if checkClearBodyList(i, body, u'sshPublicKeys'):
        i += 1
        continue
      ssh = {}
      while True:
        myopt = sys.argv[i].lower()
        if myopt == u'expires':
          ssh[u'expirationTimeUsec'] = sys.argv[i+1]
          i += 2
        elif myopt == u'key':
          ssh[u'key'] = sys.argv[i+1]
          i += 2
        elif myopt in [u'endssh']:
          i += 1
          break
        else:
          systemErrorExit(3, '%s is not a valid argument for user ssh details. Make sure user ssh details end with an endssh argument')
      appendItemToBodyList(body, u'sshPublicKeys', ssh)
    elif myarg in [u'posix', u'posixaccounts']:
      i += 1
      if checkClearBodyList(i, body, u'posixAccounts'):
        i += 1
        continue
      posix = {}
      while True:
        myopt = sys.argv[i].lower()
        if myopt == u'gecos':
          posix[u'gecos'] = sys.argv[i+1]
          i += 2
        elif myopt == u'gid':
          posix[u'gid'] = int(sys.argv[i+1])
          i += 2
        elif myopt == u'uid':
          posix[u'uid'] = int(sys.argv[i+1])
          i += 2
        elif myopt in [u'home', u'homedirectory']:
          posix[u'homeDirectory'] = sys.argv[i+1]
          i += 2
        elif myopt in [u'primary']:
          posix[u'primary'] = getBoolean(sys.argv[i+1], myopt)
          i += 2
        elif myopt in [u'shell']:
          posix[u'shell'] = sys.argv[i+1]
          i += 2
        elif myopt in [u'system', u'systemid']:
          posix[u'systemId'] = sys.argv[i+1]
          i += 2
        elif myopt in [u'username', u'name']:
          posix[u'username'] = sys.argv[i+1]
          i += 2
        elif myopt in [u'endposix']:
          i += 1
          break
        else:
          systemErrorExit(3, '%s is not a valid argument for user posix details. Make sure user posix details end with an endposix argument')
      appendItemToBodyList(body, u'posixAccounts', posix, checkSystemId=True)
    elif myarg in [u'keyword', u'keywords']:
      i += 1
      if checkClearBodyList(i, body, u'keywords'):
        i += 1
        continue
      keyword = {}
      i = getEntryType(i, keyword, USER_KEYWORD_TYPES, customKeyword=u'custom', customTypeKeyword=u'customType')
      keyword[u'value'] = sys.argv[i]
      i += 1
      appendItemToBodyList(body, u'keywords', keyword)
    elif myarg == u'clearschema':
      if not updateCmd:
        systemErrorExit(2, '%s is not a valid create user argument.' % sys.argv[i])
      schemaName, fieldName = _splitSchemaNameDotFieldName(sys.argv[i+1], False)
      up = u'customSchemas'
      body.setdefault(up, {})
      body[up].setdefault(schemaName, {})
      if fieldName is None:
        schema = callGAPI(cd.schemas(), u'get',
                          soft_errors=True,
                          customerId=GC_Values[GC_CUSTOMER_ID], schemaKey=schemaName, fields=u'fields(fieldName)')
        if not schema:
          sys.exit(2)
        for field in schema[u'fields']:
          body[up][schemaName][field[u'fieldName']] = None
      else:
        body[up][schemaName][fieldName] = None
      i += 2
    elif myarg.find(u'.') >= 0:
      schemaName, fieldName = _splitSchemaNameDotFieldName(sys.argv[i])
      up = u'customSchemas'
      body.setdefault(up, {})
      body[up].setdefault(schemaName, {})
      i += 1
      multivalue = sys.argv[i].lower()
      if multivalue in [u'multivalue', u'multivalued', u'value', u'multinonempty']:
        i += 1
        body[up][schemaName].setdefault(fieldName, [])
        schemaValue = {}
        if sys.argv[i].lower() == u'type':
          i += 1
          schemaValue[u'type'] = sys.argv[i].lower()
          if schemaValue[u'type'] not in [u'custom', u'home', u'other', u'work']:
            systemErrorExit(2, 'wrong type must be one of custom, home, other, work; got %s' % schemaValue[u'type'])
          i += 1
          if schemaValue[u'type'] == u'custom':
            schemaValue[u'customType'] = sys.argv[i]
            i += 1
        schemaValue[u'value'] = sys.argv[i]
        if schemaValue[u'value'] or multivalue != u'multinonempty':
          body[up][schemaName][fieldName].append(schemaValue)
      else:
        body[up][schemaName][fieldName] = sys.argv[i]
      i += 1
    else:
      systemErrorExit(2, '%s is not a valid argument for "gam %s user"' % (sys.argv[i], [u'create', u'update'][updateCmd]))
  if need_password:
    body[u'password'] = u''.join(random.sample(u'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789~`!@#$%^&*()-=_+:;"\'{}[]\\|', 25))
  if u'password' in body and need_to_hash_password:
    body[u'password'] = gen_sha512_hash(body[u'password'])
    body[u'hashFunction'] = u'crypt'
  return (body, admin_body)

VALIDEMAIL_PATTERN = re.compile(r'^[^@]+@[^@]+\.[^@]+$')

def getValidateLoginHint(login_hint):
  if login_hint:
    login_hint = login_hint.strip()
    if VALIDEMAIL_PATTERN.match(login_hint):
      return login_hint
  while True:
    login_hint = raw_input(u'\nWhat is your G Suite admin email address? ').strip()
    if VALIDEMAIL_PATTERN.match(login_hint):
      return login_hint
    print u'Error: that is not a valid email address'

def getCRMService(login_hint):
  from oauth2client.contrib.dictionary_storage import DictionaryStorage
  scope = u'https://www.googleapis.com/auth/cloud-platform'
  client_id = u'297408095146-fug707qsjv4ikron0hugpevbrjhkmsk7.apps.googleusercontent.com'
  client_secret = u'qM3dP8f_4qedwzWQE1VR4zzU'
  flow = oauth2client.client.OAuth2WebServerFlow(client_id=client_id,
                                                 client_secret=client_secret, scope=scope, redirect_uri=oauth2client.client.OOB_CALLBACK_URN,
                                                 user_agent=GAM_INFO, access_type=u'online', response_type=u'code', login_hint=login_hint)
  storage_dict = {}
  storage = DictionaryStorage(storage_dict, u'credentials')
  flags = cmd_flags(noLocalWebserver=GC_Values[GC_NO_BROWSER])
  http = httplib2.Http(disable_ssl_certificate_validation=GC_Values[GC_NO_VERIFY_SSL])
  try:
    credentials = oauth2client.tools.run_flow(flow=flow, storage=storage, flags=flags, http=http)
  except httplib2.CertificateValidationUnsupported:
    noPythonSSLExit()
  credentials.user_agent = GAM_INFO
  http = credentials.authorize(httplib2.Http(disable_ssl_certificate_validation=GC_Values[GC_NO_VERIFY_SSL],
                                             cache=None))
  return (googleapiclient.discovery.build(u'cloudresourcemanager', u'v1', http=http, cache_discovery=False), http)

def doDelProjects(login_hint=None):
  # Leave undocumented. Most users should never need.
  # Deletes all projects with ID gam-project-*
  login_hint = getValidateLoginHint(login_hint)
  crm, _ = getCRMService(login_hint)
  projects = callGAPIpages(crm.projects(), u'list', u'projects')
  for project in projects:
    pid = project[u'projectId']
    if pid.startswith(u'gam-project-'):
      print u'Deleting %s...' % pid
      try:
        callGAPI(crm.projects(), u'delete', throw_reasons=[GAPI_FORBIDDEN], projectId=pid)
      except GAPI_forbidden:
        pass

def enableProjectAPIs(simplehttp, httpObj, project_name, checkEnabled):
  _, c = simplehttp.request(GAM_PROJECT_APIS, u'GET')
  apis = c.splitlines()
  serveman = googleapiclient.discovery.build(u'servicemanagement', u'v1', http=httpObj, cache_discovery=False)
  if checkEnabled:
    enabledServices = callGAPIpages(serveman.services(), u'list', u'services',
                                    consumerId=project_name, fields=u'nextPageToken,services(serviceName)')
    for enabled in enabledServices:
      if u'serviceName' in enabled:
        if enabled[u'serviceName'] in apis:
          print u' API %s already enabled...' % enabled[u'serviceName']
          apis.remove(enabled[u'serviceName'])
        else:
          print u' API %s (non-GAM) is enabled (which is fine)' % enabled[u'serviceName']
  for api in apis:
    while True:
      print u' enabling API %s...' % api
      try:
        callGAPI(serveman.services(), u'enable',
                 throw_reasons=[GAPI_FAILED_PRECONDITION],
                 serviceName=api, body={u'consumerId': project_name})
        break
      except GAPI_failedPrecondition as e:
        print u'\nThere was an error enabling %s. Please resolve error as described below:' % api
        print
        print u'\n%s\n' % e
        print
        raw_input(u'Press enter once resolved and we will try enabling the API again.')

def doUpdateProject(login_hint=None):
  login_hint = getValidateLoginHint(login_hint)
  _, httpObj = getCRMService(login_hint)
  cs_data = readFile(GC_Values[GC_CLIENT_SECRETS_JSON], mode=u'rb', continueOnError=True, displayError=True, encoding=None)
  if not cs_data:
    systemErrorExit(14, u'Your client secrets file:\n\n%s\n\nis missing. Please recreate the file.' % GC_Values[GC_CLIENT_SECRETS_JSON])
  try:
    cs_json = json.loads(cs_data)
    project_name = 'project:%s' % cs_json[u'installed'][u'project_id']
  except (ValueError, IndexError, KeyError):
    systemErrorExit(3, u'The format of your client secrets file:\n\n%s\n\nis incorrect. Please recreate the file.' % GC_Values[GC_CLIENT_SECRETS_JSON])
  simplehttp = httplib2.Http(disable_ssl_certificate_validation=GC_Values[GC_NO_VERIFY_SSL])
  enableProjectAPIs(simplehttp, httpObj, project_name, True)

def doCreateProject(login_hint=None):

  def _checkClientAndSecret(simplehttp, client_id, client_secret):
    url = u'https://www.googleapis.com/oauth2/v4/token'
    post_data = {u'client_id': client_id, u'client_secret': client_secret,
                 u'code': u'ThisIsAnInvalidCodeOnlyBeingUsedToTestIfClientAndSecretAreValid',
                 u'redirect_uri': u'urn:ietf:wg:oauth:2.0:oob', u'grant_type': u'authorization_code'}
    headers = {'Content-type': 'application/x-www-form-urlencoded'}
    from urllib import urlencode
    _, content = simplehttp.request(url, u'POST', urlencode(post_data), headers=headers)
    try:
      content = json.loads(content)
    except ValueError:
      print u'Unknown error: %s' % content
      return False
    if not u'error' in content or not u'error_description' in content:
      print u'Unknown error: %s' % content
      return False
    if content[u'error'] == u'invalid_grant':
      return True
    if content[u'error_description'] == u'The OAuth client was not found.':
      print u'Ooops!!\n\n%s\n\nIs not a valid client ID. Please make sure you are following the directions exactly and that there are no extra spaces in your client ID.' % client_id
      return False
    if content[u'error_description'] == u'Unauthorized':
      print u'Ooops!!\n\n%s\n\nIs not a valid client secret. Please make sure you are following the directions exactly and that there are no extra spaces in your client secret.' % client_secret
      return False
    print u'Unknown error: %s' % content
    return False

  service_account_file = GC_Values[GC_OAUTH2SERVICE_JSON]
  client_secrets_file = GC_Values[GC_CLIENT_SECRETS_JSON]
  for a_file in [service_account_file, client_secrets_file]:
    if os.path.exists(a_file):
      systemErrorExit(5, '%s already exists. Please delete or rename it before attempting to create another project.' % a_file)
  login_hint = getValidateLoginHint(login_hint)
  login_domain = login_hint[login_hint.find(u'@')+1:]
  crm, httpObj = getCRMService(login_hint)
  project_id = u'gam-project'
  for i in range(3):
    project_id += u'-%s' % ''.join(random.choice(string.digits + string.ascii_lowercase) for i in range(3))
  project_name = u'project:%s' % project_id
  body = {u'projectId': project_id, u'name': u'GAM Project'}
  while True:
    create_again = False
    print u'Creating project "%s"...' % body[u'name']
    create_operation = callGAPI(crm.projects(), u'create',
                                body=body)
    operation_name = create_operation[u'name']
    time.sleep(5) # Google recommends always waiting at least 5 seconds
    for i in range(1, 5):
      print u'Checking project status...'
      status = callGAPI(crm.operations(), u'get',
                        name=operation_name)
      if u'error' in status:
        if status[u'error'].get(u'message', u'') == u'No permission to create project in organization':
          print u'Hmm... Looks like you have no rights to your Google Cloud Organization.'
          print u'Attempting to fix that...'
          getorg = callGAPI(crm.organizations(), u'search',
                            body={u'filter': u'domain:%s' % login_domain})
          try:
            organization = getorg[u'organizations'][0][u'name']
            print u'Your organization name is %s' % organization
          except (KeyError, IndexError):
            systemErrorExit(3, 'you have no rights to create projects for your organization and you don\'t seem to be a super admin! Sorry, there\'s nothing more I can do.')
          org_policy = callGAPI(crm.organizations(), u'getIamPolicy',
                                resource=organization, body={})
          if u'bindings' not in org_policy:
            org_policy[u'bindings'] = []
            print u'Looks like no one has rights to your Google Cloud Organization. Attempting to give you create rights...'
          else:
            print u'The following rights seem to exist:'
            for a_policy in org_policy[u'bindings']:
              if u'role' in a_policy:
                print u' Role: %s' % a_policy[u'role']
              if u'members' in a_policy:
                print u' Members:'
                for member in a_policy[u'members']:
                  print u'  %s' % member
              print
          my_role = u'roles/resourcemanager.projectCreator'
          print u'Giving %s the role of %s...' % (login_hint, my_role)
          org_policy[u'bindings'].append({u'role': my_role, u'members': [u'user:%s' % login_hint]})
          callGAPI(crm.organizations(), u'setIamPolicy',
                   resource=organization, body={u'policy': org_policy})
          create_again = True
          break
        try:
          if status[u'error'][u'details'][0][u'violations'][0][u'description'] == u'Callers must accept Terms of Service':
            print u'''Please go to:

https://console.cloud.google.com/start

and accept the Terms of Service (ToS). As soon as you've accepted the ToS popup, you can return here and press enter.'''
            raw_input()
            create_again = True
            break
        except (IndexError, KeyError):
          pass
        print status
        sys.exit(1)
      if status.get(u'done', False):
        break
      sleep_time = i ** 2
      print u'Project still being created. Sleeping %s seconds' % sleep_time
      time.sleep(sleep_time)
    if create_again:
      continue
    if not status.get(u'done', False):
      print u'Failed to create project: %s' % status
      sys.exit(1)
    elif u'error' in status:
      print status[u'error']
      sys.exit(2)
    break
  simplehttp = httplib2.Http(disable_ssl_certificate_validation=GC_Values[GC_NO_VERIFY_SSL])
  enableProjectAPIs(simplehttp, httpObj, project_name, False)
  iam = googleapiclient.discovery.build(u'iam', u'v1', http=httpObj, cache_discovery=False)
  print u'Creating Service Account'
  service_account = callGAPI(iam.projects().serviceAccounts(), u'create',
                             name=u'projects/%s' % project_id,
                             body={u'accountId': project_id, u'serviceAccount': {u'displayName': u'GAM Project'}})
  key = callGAPI(iam.projects().serviceAccounts().keys(), u'create',
                 name=service_account[u'name'], body={u'privateKeyType': u'TYPE_GOOGLE_CREDENTIALS_FILE', u'keyAlgorithm': u'KEY_ALG_RSA_2048'})
  oauth2service_data = base64.b64decode(key[u'privateKeyData'])
  writeFile(service_account_file, oauth2service_data, continueOnError=False)
  console_credentials_url = u'https://console.developers.google.com/apis/credentials?project=%s' % project_id
  while True:
    print u'''Please go to:

%s

1. Click the blue "Create credentials" button. Choose "OAuth client ID".
2. Click the blue "Configure consent screen" button. Enter "GAM" for "Product name to show to users".
3. Leave other fields blank. Click "Save" button.
3. Choose "Other" and click the blue "Create" button.
4. Copy your "client ID" value.

''' % console_credentials_url
    client_id = raw_input(u'Enter your Client ID: ').strip()
    print u'\nNow go back to your browser and copy your client secret.'
    client_secret = raw_input(u'Enter your Client Secret: ').strip()
    client_valid = _checkClientAndSecret(simplehttp, client_id, client_secret)
    if client_valid:
      break
    print
  cs_data = u'''{
    "installed": {
        "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
        "auth_uri": "https://accounts.google.com/o/oauth2/auth",
        "client_id": "%s",
        "client_secret": "%s",
        "project_id": "%s",
        "redirect_uris": [
            "urn:ietf:wg:oauth:2.0:oob",
            "http://localhost"
        ],
        "token_uri": "https://accounts.google.com/o/oauth2/token"
    }
}''' % (client_id, client_secret, project_id)
  writeFile(client_secrets_file, cs_data, continueOnError=False)
  print u'''Almost there! Now please switch back to your browser and:

1. Click OK to close "OAuth client" popup if it's still open.
2. Click "Manage service accounts" on the right of the screen.
3. Click the 3 dots to the right of your service account.
4. Choose Edit.
5. Check the "Enable G Suite Domain-wide Delegation" box and click Save.
'''
  raw_input(u'Press Enter when done...')
  print u'That\'s it! Your GAM Project is created and ready to use.'

def doGetTeamDriveInfo(users):
  teamDriveId = sys.argv[5]
  useDomainAdminAccess = False
  i = 6
  while i < len(sys.argv):
    myarg = sys.argv[i].lower().replace(u'_', u'')
    if myarg == u'asadmin':
      useDomainAdminAccess = True
      i += 1
    else:
      systemErrorExit(3, '%s is not a valid command for "gam <users> show teamdrive"' % sys.argv[i])
  for user in users:
    drive = buildGAPIServiceObject(u'drive3', user)
    if not drive:
      print u'Failed to access Drive as %s' % user
      continue
    result = callGAPI(drive.teamdrives(), u'get', teamDriveId=teamDriveId,
                      useDomainAdminAccess=useDomainAdminAccess, fields=u'*')
    print_json(None, result)

def doCreateTeamDrive(users):
  body = {u'name': sys.argv[5]}
  i = 6
  while i < len(sys.argv):
    myarg = sys.argv[i].lower()
    if myarg == u'theme':
      body[u'themeId'] = sys.argv[i+1]
      i += 2
    else:
      systemErrorExit(3, '%s is not a valid argument to "gam <users> create teamdrive"' % sys.argv[i])
  for user in users:
    drive = buildGAPIServiceObject(u'drive3', user)
    if not drive:
      print u'Failed to access Drive as %s' % user
      continue
    requestId = unicode(uuid.uuid4())
    result = callGAPI(drive.teamdrives(), u'create', requestId=requestId, body=body, fields=u'id')
    print u'Created Team Drive %s with id %s' % (body[u'name'], result[u'id'])

def doUpdateTeamDrive(users):
  teamDriveId = sys.argv[5]
  body = {}
  i = 6
  while i < len(sys.argv):
    myarg = sys.argv[i].lower()
    if myarg == u'name':
      body[u'name'] = sys.argv[i+1]
      i += 2
    elif myarg == u'theme':
      body[u'themeId'] = sys.argv[i+1]
      i += 2
    elif myarg == u'customtheme':
      body[u'backgroundImageFile'] = {
        u'id': sys.argv[i+1],
        u'xCoordinate': float(sys.argv[i+2]),
        u'yCoordinate': float(sys.argv[i+3]),
        u'width': float(sys.argv[i+4])
        }
      i += 5
    elif myarg == u'color':
      body[u'colorRgb'] = getColor(sys.argv[i+1])
      i += 2
    else:
      systemErrorExit(3, '%s is not a valid argument for "gam <users> update teamdrive"' % sys.argv[i])
  if not body:
    systemErrorExit(4, 'nothing to update. Need at least a name argument.')
  for user in users:
    user, drive = buildDrive3GAPIObject(user)
    if not drive:
      continue
    result = callGAPI(drive.teamdrives(), u'update', body=body, teamDriveId=teamDriveId, fields=u'id', soft_errors=True)
    if not result:
      continue
    print u'Updated Team Drive %s' % (teamDriveId)

def printShowTeamDrives(users, csvFormat):
  todrive = False
  useDomainAdminAccess = False
  q = None
  i = 5
  while i < len(sys.argv):
    myarg = sys.argv[i].lower().replace(u'_', u'')
    if myarg == u'todrive':
      todrive = True
      i += 1
    elif myarg == u'asadmin':
      useDomainAdminAccess = True
      i += 1
    elif myarg == u'query':
      q = sys.argv[i+1]
      i += 2
    else:
      systemErrorExit(3, '%s is not a valid argument for "gam <users> print|show teamdrives"')
  tds = []
  for user in users:
    sys.stderr.write(u'Getting Team Drives for %s\n' % user)
    user, drive = buildDrive3GAPIObject(user)
    if not drive:
      continue
    results = callGAPIpages(drive.teamdrives(), u'list', u'teamDrives',
                            useDomainAdminAccess=useDomainAdminAccess, fields=u'*',
                            q=q, soft_errors=True)
    if not results:
      continue
    for td in results:
      if u'id' not in td:
        continue
      if u'name' not in td:
        td[u'name'] = u'<Unknown Team Drive>'
      this_td = {u'id': td[u'id'], u'name': td[u'name']}
      if this_td in tds:
        continue
      tds.append({u'id': td[u'id'], u'name': td[u'name']})
  if csvFormat:
    titles = [u'name', u'id']
    writeCSVfile(tds, titles, u'Team Drives', todrive)
  else:
    for td in tds:
      print u'Name: %s  ID: %s' % (td[u'name'], td[u'id'])

def doDeleteTeamDrive(users):
  teamDriveId = sys.argv[5]
  for user in users:
    user, drive = buildDrive3GAPIObject(user)
    if not drive:
      continue
    print u'Deleting Team Drive %s' % (teamDriveId)
    callGAPI(drive.teamdrives(), u'delete', teamDriveId=teamDriveId, soft_errors=True)

def validateCollaborators(collaboratorList, cd):
  collaborators = []
  for collaborator in collaboratorList.split(u','):
    collaborator_id = convertEmailAddressToUID(collaborator, cd)
    if not collaborator_id:
      systemErrorExit(4, 'failed to get a UID for %s. Please make sure this is a real user.' % collaborator)
    collaborators.append({u'email': collaborator, u'id': collaborator_id})
  return collaborators

def doCreateVaultMatter():
  v = buildGAPIObject(u'vault')
  body = {u'name': u'New Matter - %s' % datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
  collaborators = []
  cd = None
  i = 3
  while i < len(sys.argv):
    myarg = sys.argv[i].lower().replace(u'_', u'')
    if myarg == u'name':
      body[u'name'] = sys.argv[i+1]
      i += 2
    elif myarg == u'description':
      body[u'description'] = sys.argv[i+1]
      i += 2
    elif myarg in [u'collaborator', u'collaborators']:
      if not cd:
        cd = buildGAPIObject(u'directory')
      collaborators.extend(validateCollaborators(sys.argv[i+1], cd))
      i += 2
    else:
      systemErrorExit(3, '%s is not a valid argument to "gam create matter"' % sys.argv[i])
  result = callGAPI(v.matters(), u'create', body=body, fields=u'matterId')
  matterId = result[u'matterId']
  print u'Created matter %s' % matterId
  for collaborator in collaborators:
    print u' adding collaborator %s' % collaborator[u'email']
    callGAPI(v.matters(), u'addPermissions', matterId=matterId, body={u'matterPermission': {u'role': u'COLLABORATOR', u'accountId': collaborator[u'id']}})

def doCreateVaultHold():
  v = buildGAPIObject(u'vault')
  allowed_corpuses = v._rootDesc[u'schemas'][u'Hold'][u'properties'][u'corpus'][u'enum']
  body = {u'query': {}}
  i = 3
  query = None
  start_time = None
  end_time = None
  matterId = None
  accounts = []
  while i < len(sys.argv):
    myarg = sys.argv[i].lower().replace(u'_', u'')
    if myarg == u'name':
      body[u'name'] = sys.argv[i+1]
      i += 2
    elif myarg == u'query':
      query = sys.argv[i+1]
      i += 2
    elif myarg == u'corpus':
      body[u'corpus'] = sys.argv[i+1].upper()
      if body[u'corpus'] not in allowed_corpuses:
        systemErrorExit(3, 'corpus must be one of %s. Got %s' % (u', '.join(allowed_corpuses), sys.argv[i+1]))
      i += 2
    elif myarg in [u'accounts', u'users', u'groups']:
      accounts = sys.argv[i+1].split(u',')
      i += 2
    elif myarg in [u'orgunit', u'ou']:
      body[u'orgUnit'] = {u'orgUnitId': doGetOrgInfo(name=sys.argv[i+1], return_attrib=u'orgUnitId')}
      i += 2
    elif myarg == u'starttime':
      start_time = getDateZeroTimeOrFullTime(sys.argv[i+1])
      i += 2
    elif myarg == u'endtime':
      end_time = getDateZeroTimeOrFullTime(sys.argv[i+1])
      i += 2
    elif myarg == u'matter':
      matterId = convertMatterNameToID(v, sys.argv[i+1])
      if not matterId:
        systemErrorExit(4, 'could not find matter %s' % sys.argv[i+1])
      i += 2
    else:
      systemErrorExit(3, '%s is not a valid argument to "gam create hold"' % sys.argv[i])
  if not matterId:
    systemErrorExit(3, 'you must specify a matter for the new hold.')
  if not body.get(u'name'):
    systemErrorExit(3, 'you must specify a name for the new hold.')
  if not body.get(u'corpus'):
    systemErrorExit(3, 'you must specify corpus for the new hold. One of %s' % (u', '.join(allowed_corpuses)))
  query_type = u'%sQuery' % body[u'corpus'].lower()
  body[u'query'][query_type] = {}
  if body[u'corpus'] == u'DRIVE':
    if query:
      try:
        body[u'query'][query_type] = json.loads(query)
      except ValueError as e:
        systemErrorExit(3, '{0}, query: {1}'.format(str(e), query))
  elif body[u'corpus'] in [u'GROUPS', u'MAIL']:
    if query:
      body[u'query'][query_type] = {u'terms': query}
    if start_time:
      body[u'query'][query_type][u'startTime'] = start_time
    if end_time:
      body[u'query'][query_type][u'endTime'] = end_time
  if accounts:
    body[u'accounts'] = []
    cd = buildGAPIObject(u'directory')
    account_type = u'group' if body[u'corpus'] == u'GROUPS' else u'user'
    for account in accounts:
      body[u'accounts'].append({u'accountId': convertEmailAddressToUID(account, cd, account_type)})
  callGAPI(v.matters().holds(), u'create', matterId=matterId, body=body)

def doDeleteVaultHold():
  v = buildGAPIObject(u'vault')
  hold = sys.argv[3]
  matterId = None
  i = 4
  while i < len(sys.argv):
    myarg = sys.argv[i].lower().replace(u'_', u'')
    if myarg == u'matter':
      matterId = convertMatterNameToID(v, sys.argv[i+1])
      if not matterId:
        systemErrorExit(4, 'could not find matter %s' % sys.argv[i+1])
      holdId = convertHoldNameToID(v, hold, matterId)
      if not holdId:
        systemErrorExit(4, 'could not find hold %s in matter %s' % (sys.argv[3], matterId))
      i += 2
    else:
      systemErrorExit(3, '%s is not a valid argument to "gam delete hold"' % myarg)
  if not matterId:
    systemErrorExit(3, 'you must specify a matter for the hold.')
  print u'Deleting hold %s / %s' % (hold, holdId)
  callGAPI(v.matters().holds(), u'delete', matterId=matterId, holdId=holdId)

def doGetVaultHoldInfo():
  v = buildGAPIObject(u'vault')
  hold = sys.argv[3]
  matterId = None
  i = 4
  while i < len(sys.argv):
    myarg = sys.argv[i].lower().replace(u'_', u'')
    if myarg == u'matter':
      matterId = convertMatterNameToID(v, sys.argv[i+1])
      if not matterId:
        systemErrorExit(4, 'could not find matter %s' % sys.argv[i+1])
      holdId = convertHoldNameToID(v, hold, matterId)
      if not holdId:
        systemErrorExit(4, 'could not find hold %s in matter %s' % (hold, matterId))
      i += 2
    else:
      systemErrorExit(3, '%s is not a valid argument for "gam info hold"' % myarg)
  if not matterId:
    systemErrorExit(3, 'you must specify a matter for the hold.')
  results = callGAPI(v.matters().holds(), u'get', matterId=matterId, holdId=holdId)
  cd = buildGAPIObject(u'directory')
  if u'accounts' in results:
    account_type = u'group' if results[u'corpus'] == u'GROUPS' else u'user'
    for i in range(0, len(results[u'accounts'])):
      uid = u'uid:%s' % results[u'accounts'][i][u'accountId']
      acct_email = convertUIDtoEmailAddress(uid, cd, account_type)
      results[u'accounts'][i][u'email'] = acct_email
  if u'orgUnit' in results:
    results[u'orgUnit'][u'orgUnitPath'] = doGetOrgInfo(results[u'orgUnit'][u'orgUnitId'], return_attrib=u'orgUnitPath')
  print_json(None, results)

def convertHoldNameToID(v, nameOrID, matterId):
  nameOrID = nameOrID.lower()
  if nameOrID[:4] == u'uid:':
    return nameOrID[4:]
  holds = callGAPIpages(v.matters().holds(), u'list', u'holds', matterId=matterId, fields=u'holds(holdId,name),nextPageToken')
  for hold in holds:
    if hold[u'name'].lower() == nameOrID:
      return hold[u'holdId']
  return None

def convertMatterNameToID(v, nameOrID):
  nameOrID = nameOrID.lower()
  if nameOrID[:4] == u'uid:':
    return nameOrID[4:]
  matters = callGAPIpages(v.matters(), u'list', u'matters', view=u'BASIC', fields=u'matters(matterId,name),nextPageToken')
  for matter in matters:
    if matter[u'name'].lower() == nameOrID:
      return matter[u'matterId']
  return None

def doUpdateVaultHold():
  v = buildGAPIObject(u'vault')
  hold = sys.argv[3]
  matterId = None
  body = {}
  query = None
  add_accounts = []
  del_accounts = []
  start_time = None
  end_time = None
  i = 4
  while i < len(sys.argv):
    myarg = sys.argv[i].lower().replace(u'_', u'')
    if myarg == u'matter':
      matterId = convertMatterNameToID(v, sys.argv[i+1])
      if not matterId:
        systemErrorExit(4, 'could not find matter %s' % sys.argv[i+1])
      holdId = convertHoldNameToID(v, hold, matterId)
      if not holdId:
        systemErrorExit(4, 'could not find hold %s in matter %s' % (hold, matterId))
      i += 2
    elif myarg == u'query':
      query = sys.argv[i+1]
      i += 2
    elif myarg in [u'orgunit', u'ou']:
      body[u'orgUnit'] = {u'orgUnitId': doGetOrgInfo(name=sys.argv[i+1], return_attrib=u'orgUnitId')}
      i += 2
    elif myarg == u'starttime':
      start_time = getDateZeroTimeOrFullTime(sys.argv[i+1])
      i += 2
    elif myarg == u'endtime':
      end_time = getDateZeroTimeOrFullTime(sys.argv[i+1])
      i += 2
    elif myarg in [u'addusers', u'addaccounts', u'addgroups']:
      add_accounts = sys.argv[i+1].split(u',')
      i += 2
    elif myarg in [u'removeusers', u'removeaccounts', u'removegroups']:
      del_accounts = sys.argv[i+1].split(u',')
      i += 2
    else:
      systemErrorExit(3, '%s is not a valid argument to "gam update hold"' % myarg)
  if not matterId:
    systemErrorExit(3, 'you must specify a matter for the hold.')
  if query or start_time or end_time or body.get(u'orgUnit'):
    old_body = callGAPI(v.matters().holds(), u'get', matterId=matterId, holdId=holdId, fields=u'corpus,query,orgUnit')
    body[u'query'] = old_body[u'query']
    body[u'corpus'] = old_body[u'corpus']
    if u'orgUnit' in old_body and u'orgUnit' not in body:
      # bah, API requires this to be sent on update even when it's not changing
      body[u'orgUnit'] = old_body[u'orgUnit']
    query_type = '%sQuery' % body[u'corpus'].lower()
    if body[u'corpus'] == u'DRIVE':
      if query:
        try:
          body[u'query'][query_type] = json.loads(query)
        except ValueError as e:
          systemErrorExit(3, '{0}, query: {1}'.format(str(e), query))
    elif body[u'corpus'] in [u'GROUPS', u'MAIL']:
      if query:
        body[u'query'][query_type][u'terms'] = query
      if start_time:
        body[u'query'][query_type][u'startTime'] = start_time
      if end_time:
        body[u'query'][query_type][u'endTime'] = end_time
  if body:
    print u'Updating hold %s / %s' % (hold, holdId)
    callGAPI(v.matters().holds(), u'update', matterId=matterId, holdId=holdId, body=body)
  if add_accounts or del_accounts:
    cd = buildGAPIObject(u'directory')
    for account in add_accounts:
      print u'adding %s to hold.' % account
      add_body = {u'accountId': convertEmailAddressToUID(account, cd)}
      callGAPI(v.matters().holds().accounts(), u'create', matterId=matterId, holdId=holdId, body=add_body)
    for account in del_accounts:
      print u'removing %s from hold.' % account
      accountId = convertEmailAddressToUID(account, cd)
      callGAPI(v.matters().holds().accounts(), u'delete', matterId=matterId, holdId=holdId, accountId=accountId)

def doUpdateVaultMatter(action=None):
  v = buildGAPIObject(u'vault')
  matterId = convertMatterNameToID(v, sys.argv[3])
  if not matterId:
    systemErrorExit(4, 'failed to lookup matter named %s' % sys.argv[3])
  body = {}
  action_kwargs = {u'body': {}}
  add_collaborators = []
  remove_collaborators = []
  cd = None
  i = 4
  while i < len(sys.argv):
    myarg = sys.argv[i].lower().replace(u'_', u'')
    if myarg == u'action':
      action = sys.argv[i+1].lower()
      if action not in VAULT_MATTER_ACTIONS:
        systemErrorExit(3, 'allowed actions are %s, got %s' % (u', '.join(VAULT_MATTER_ACTIONS), action))
      i += 2
    elif myarg == u'name':
      body[u'name'] = sys.argv[i+1]
      i += 2
    elif myarg == u'description':
      body[u'description'] = sys.argv[i+1]
      i += 2
    elif myarg in [u'addcollaborator', u'addcollaborators']:
      if not cd:
        cd = buildGAPIObject(u'directory')
      add_collaborators.extend(validateCollaborators(sys.argv[i+1], cd))
      i += 2
    elif myarg in [u'removecollaborator', u'removecollaborators']:
      if not cd:
        cd = buildGAPIObject(u'directory')
      remove_collaborators.extend(validateCollaborators(sys.argv[i+1], cd))
      i += 2
    else:
      systemErrorExit(3, '%s is not a valid argument for "gam update matter"' % sys.argv[i])
  if action == u'delete':
    action_kwargs = {}
  if body:
    print u'Updating matter %s...' % sys.argv[3]
    if u'name' not in body or u'description' not in body:
      # bah, API requires name/description to be sent on update even when it's not changing
      result = callGAPI(v.matters(), u'get', matterId=matterId, view=u'BASIC')
      body.setdefault(u'name', result[u'name'])
      body.setdefault(u'description', result.get(u'description'))
    callGAPI(v.matters(), u'update', body=body, matterId=matterId)
  if action:
    print u'Performing %s on matter %s' % (action, sys.argv[3])
    callGAPI(v.matters(), action, matterId=matterId, **action_kwargs)
  for collaborator in add_collaborators:
    print u' adding collaborator %s' % collaborator[u'email']
    callGAPI(v.matters(), u'addPermissions', matterId=matterId, body={u'matterPermission': {u'role': u'COLLABORATOR', u'accountId': collaborator[u'id']}})
  for collaborator in remove_collaborators:
    print u' removing collaborator %s' % collaborator[u'email']
    callGAPI(v.matters(), u'removePermissions', matterId=matterId, body={u'accountId': collaborator[u'id']})

def doGetVaultMatterInfo():
  v = buildGAPIObject(u'vault')
  matterId = convertMatterNameToID(v, sys.argv[3])
  result = callGAPI(v.matters(), u'get', matterId=matterId, view=u'FULL')
  if u'matterPermissions' in result:
    cd = buildGAPIObject(u'directory')
    for i in range(0, len(result[u'matterPermissions'])):
      uid = u'uid:%s' % result[u'matterPermissions'][i][u'accountId']
      user_email = convertUIDtoEmailAddress(uid, cd)
      result[u'matterPermissions'][i][u'email'] = user_email
  print_json(None, result)

def doCreateUser():
  cd = buildGAPIObject(u'directory')
  body, admin_body = getUserAttributes(3, cd, updateCmd=False)
  print u"Creating account for %s" % body[u'primaryEmail']
  callGAPI(cd.users(), u'insert', body=body, fields=u'primaryEmail')
  if admin_body:
    print u' Changing admin status for %s to %s' % (body[u'primaryEmail'], admin_body[u'status'])
    callGAPI(cd.users(), u'makeAdmin', userKey=body[u'primaryEmail'], body=admin_body)

def GroupIsAbuseOrPostmaster(emailAddr):
  return emailAddr.startswith(u'abuse@') or emailAddr.startswith(u'postmaster@')

def getGroupAttrValue(myarg, value, gs_object, gs_body, function):
  for (attrib, params) in gs_object[u'schemas'][u'Groups'][u'properties'].items():
    if attrib in [u'kind', u'etag', u'email']:
      continue
    if myarg == attrib.lower():
      if params[u'type'] == u'integer':
        try:
          if value[-1:].upper() == u'M':
            value = int(value[:-1]) * 1024 * 1024
          elif value[-1:].upper() == u'K':
            value = int(value[:-1]) * 1024
          elif value[-1].upper() == u'B':
            value = int(value[:-1])
          else:
            value = int(value)
        except ValueError:
          systemErrorExit(2, '%s must be a number ending with M (megabytes), K (kilobytes) or nothing (bytes); got %s' % value)
      elif params[u'type'] == u'string':
        if attrib == u'description':
          value = value.replace(u'\\n', u'\n')
        elif attrib == u'primaryLanguage':
          value = LANGUAGE_CODES_MAP.get(value.lower(), value)
        elif params[u'description'].find(value.upper()) != -1: # ugly hack because API wants some values uppercased.
          value = value.upper()
        elif value.lower() in true_values:
          value = u'true'
        elif value.lower() in false_values:
          value = u'false'
      gs_body[attrib] = value
      return
  systemErrorExit(2, '%s is not a valid argument for "gam %s group"' % (myarg, function))

def doCreateGroup():
  cd = buildGAPIObject(u'directory')
  body = {u'email': normalizeEmailAddressOrUID(sys.argv[3], noUid=True)}
  got_name = False
  i = 4
  gs_body = {}
  gs = None
  while i < len(sys.argv):
    myarg = sys.argv[i].lower().replace(u'_', u'')
    if myarg == u'name':
      body[u'name'] = sys.argv[i+1]
      got_name = True
      i += 2
    elif myarg == u'description':
      description = sys.argv[i+1].replace(u'\\n', u'\n')
# The Directory API Groups insert method can not handle any of these characters ('\n<>=') in the description field
# If any of these characters are present, use the Group Settings API to set the description
      for c in u'\n<>=':
        if description.find(c) != -1:
          gs_body[u'description'] = description
          if not gs:
            gs = buildGAPIObject(u'groupssettings')
            gs_object = gs._rootDesc
          break
      else:
        body[u'description'] = description
      i += 2
    else:
      if not gs:
        gs = buildGAPIObject(u'groupssettings')
        gs_object = gs._rootDesc
      getGroupAttrValue(myarg, sys.argv[i+1], gs_object, gs_body, u'create')
      i += 2
  if not got_name:
    body[u'name'] = body[u'email']
  print u"Creating group %s" % body[u'email']
  callGAPI(cd.groups(), u'insert', body=body, fields=u'email')
  if gs and not GroupIsAbuseOrPostmaster(body[u'email']):
    settings = callGAPI(gs.groups(), u'get',
                        retry_reasons=[u'serviceLimit'],
                        groupUniqueId=body[u'email'], fields=u'*')
    if settings is not None:
      settings.update(gs_body)
      callGAPI(gs.groups(), u'update', retry_reasons=[u'serviceLimit'], groupUniqueId=body[u'email'], body=settings)

def doCreateAlias():
  cd = buildGAPIObject(u'directory')
  body = {u'alias': normalizeEmailAddressOrUID(sys.argv[3], noUid=True)}
  target_type = sys.argv[4].lower()
  if target_type not in [u'user', u'group', u'target']:
    systemErrorExit(2, 'type of target must be user or group; got %s' % target_type)
  targetKey = normalizeEmailAddressOrUID(sys.argv[5])
  print u'Creating alias %s for %s %s' % (body[u'alias'], target_type, targetKey)
  if target_type == u'user':
    callGAPI(cd.users().aliases(), u'insert', userKey=targetKey, body=body)
  elif target_type == u'group':
    callGAPI(cd.groups().aliases(), u'insert', groupKey=targetKey, body=body)
  elif target_type == u'target':
    try:
      callGAPI(cd.users().aliases(), u'insert', throw_reasons=[GAPI_INVALID, GAPI_BAD_REQUEST], userKey=targetKey, body=body)
    except (GAPI_invalid, GAPI_badRequest):
      callGAPI(cd.groups().aliases(), u'insert', groupKey=targetKey, body=body)

def doCreateOrg():
  cd = buildGAPIObject(u'directory')
  body = {u'name': sys.argv[3]}
  if body[u'name'][0] == u'/':
    body[u'name'] = body[u'name'][1:]
  i = 4
  body[u'parentOrgUnitPath'] = u'/'
  while i < len(sys.argv):
    myarg = sys.argv[i].lower()
    if myarg == u'description':
      body[u'description'] = sys.argv[i+1].replace(u'\\n', u'\n')
      i += 2
    elif myarg == u'parent':
      body[u'parentOrgUnitPath'] = sys.argv[i+1]
      i += 2
    elif myarg == u'noinherit':
      body[u'blockInheritance'] = True
      i += 1
    elif myarg == u'inherit':
      body[u'blockInheritance'] = False
      i += 1
    else:
      systemErrorExit(2, '%s is not a valid argument for "gam create org"' % sys.argv[i])
  callGAPI(cd.orgunits(), u'insert', customerId=GC_Values[GC_CUSTOMER_ID], body=body)

def _getBuildingAttributes(args, body={}):
  i = 0
  while i < len(args):
    myarg = args[i].lower().replace(u'_', u'')
    if myarg == u'id':
      body[u'buildingId'] = args[i+1]
      i += 2
    elif myarg == u'name':
      body[u'buildingName'] = args[i+1]
      i += 2
    elif myarg in [u'lat', u'latitude']:
      if u'coordinates' not in body:
        body[u'coordinates'] = {}
      body[u'coordinates'][u'latitude'] = args[i+1]
      i += 2
    elif myarg in [u'long', u'lng', u'longitude']:
      if u'coordinates' not in body:
        body[u'coordinates'] = {}
      body[u'coordinates'][u'longitude'] = args[i+1]
      i += 2
    elif myarg == u'description':
      body[u'description'] = args[i+1]
      i += 2
    elif myarg == u'floors':
      body[u'floorNames'] = args[i+1].split(u',')
      i += 2
    else:
      systemErrorExit(3, '%s is not a valid argument for "gam create|update building"' % myarg)
  return body

def doCreateBuilding():
  cd = buildGAPIObject(u'directory')
  body = {u'floorNames': [u'1'],
          u'buildingId': unicode(uuid.uuid4()),
          u'buildingName': sys.argv[3]}
  body = _getBuildingAttributes(sys.argv[4:], body)
  print u'Creating building %s...' % body[u'buildingId']
  callGAPI(cd.resources().buildings(), u'insert',
           customer=GC_Values[GC_CUSTOMER_ID], body=body)

def _makeBuildingIdNameMap(cd):
  buildings = callGAPIpages(cd.resources().buildings(), u'list', u'buildings',
                            customer=GC_Values[GC_CUSTOMER_ID],
                            fields=u'nextPageToken,buildings(buildingId,buildingName)')
  GM_Globals[GM_MAP_BUILDING_ID_TO_NAME] = {}
  GM_Globals[GM_MAP_BUILDING_NAME_TO_ID] = {}
  for building in buildings:
    GM_Globals[GM_MAP_BUILDING_ID_TO_NAME][building[u'buildingId']] = building[u'buildingName']
    GM_Globals[GM_MAP_BUILDING_NAME_TO_ID][building[u'buildingName']] = building[u'buildingId']

def _getBuildingByNameOrId(cd, which_building, minLen=1):
  if not which_building or which_building.lower() == u'id:':
    if minLen == 0:
      return u''
    systemErrorExit(3, u'Building id/name is empty')
  if which_building[:3].lower() == u'id:':
    return which_building[3:]
  if GM_Globals[GM_MAP_BUILDING_NAME_TO_ID] is None:
    _makeBuildingIdNameMap(cd)
# Exact name match, return ID
  if which_building in GM_Globals[GM_MAP_BUILDING_NAME_TO_ID]:
    return GM_Globals[GM_MAP_BUILDING_NAME_TO_ID][which_building]
# No exact name match, check for case insensitive name matches
  which_building_lower = which_building.lower()
  ci_matches = []
  for buildingName, buildingId in GM_Globals[GM_MAP_BUILDING_NAME_TO_ID].iteritems():
    if buildingName.lower() == which_building_lower:
      ci_matches.append({u'buildingName': buildingName, u'buildingId': buildingId})
# One match, return ID
  if len(ci_matches) == 1:
    return ci_matches[0][u'buildingId']
# No or multiple name matches, try ID
# Exact ID match, return ID
  if which_building in GM_Globals[GM_MAP_BUILDING_ID_TO_NAME]:
    return which_building
# No exact ID match, check for case insensitive id match
  for buildingId in GM_Globals[GM_MAP_BUILDING_ID_TO_NAME]:
# Match, return ID
    if buildingId.lower() == which_building_lower:
      return buildingId
# Multiple name  matches
  if len(ci_matches) > 1:
    message = u'Multiple buildings with same name:\n'
    for building in ci_matches:
      message += u'  Name:%s  id:%s\n' % (building[u'buildingName'], building[u'buildingId'])
    message += u'\nPlease specify building name by exact case or by id.'
    systemErrorExit(3, message)
# No matches
  else:
    systemErrorExit(3, 'No such building %s' % which_building)

def _getBuildingNameById(cd, buildingId):
  if GM_Globals[GM_MAP_BUILDING_ID_TO_NAME] is None:
    _makeBuildingIdNameMap(cd)
  return GM_Globals[GM_MAP_BUILDING_ID_TO_NAME].get(buildingId, u'UNKNOWN')

def doUpdateBuilding():
  cd = buildGAPIObject(u'directory')
  buildingId = _getBuildingByNameOrId(cd, sys.argv[3])
  body = _getBuildingAttributes(sys.argv[4:])
  print u'Updating building %s...' % buildingId
  callGAPI(cd.resources().buildings(), u'patch',
           customer=GC_Values[GC_CUSTOMER_ID], buildingId=buildingId, body=body)

def doGetBuildingInfo():
  cd = buildGAPIObject(u'directory')
  buildingId = _getBuildingByNameOrId(cd, sys.argv[3])
  building = callGAPI(cd.resources().buildings(), u'get',
                      customer=GC_Values[GC_CUSTOMER_ID], buildingId=buildingId)
  if u'buildingId' in building:
    building[u'buildingId'] = u'id:{0}'.format(building[u'buildingId'])
  if u'floorNames' in building:
    building[u'floorNames'] = u','.join(building[u'floorNames'])
  if u'buildingName' in building:
    sys.stdout.write(building.pop(u'buildingName'))
  print_json(None, building)

def doDeleteBuilding():
  cd = buildGAPIObject(u'directory')
  buildingId = _getBuildingByNameOrId(cd, sys.argv[3])
  print u'Deleting building %s...' % buildingId
  callGAPI(cd.resources().buildings(), u'delete',
           customer=GC_Values[GC_CUSTOMER_ID], buildingId=buildingId)

def _getFeatureAttributes(args, body={}):
  i = 0
  while i < len(args):
    myarg = args[i].lower().replace(u'_', u'')
    if myarg == u'name':
      body[u'name'] = args[i+1]
      i += 2
    else:
      systemErrorExit(3, '%s is not a valid argument for "gam create|update feature"')
  return body

def doCreateFeature():
  cd = buildGAPIObject(u'directory')
  body = _getFeatureAttributes(sys.argv[3:])
  print u'Creating feature %s...' % body[u'name']
  callGAPI(cd.resources().features(), u'insert',
           customer=GC_Values[GC_CUSTOMER_ID], body=body)

def doUpdateFeature():
  # update does not work for name and name is only field to be updated
  # if additional writable fields are added to feature in the future
  # we'll add support for update as well as rename
  cd = buildGAPIObject(u'directory')
  oldName = sys.argv[3]
  body = {u'newName': sys.argv[5:]}
  print u'Updating feature %s...' % oldName
  callGAPI(cd.resources().features(), u'rename',
           customer=GC_Values[GC_CUSTOMER_ID], oldName=oldName,
           body=body)

def doDeleteFeature():
  cd = buildGAPIObject(u'directory')
  featureKey = sys.argv[3]
  print u'Deleting feature %s...' % featureKey
  callGAPI(cd.resources().features(), u'delete',
           customer=GC_Values[GC_CUSTOMER_ID], featureKey=featureKey)

def _getResourceCalendarAttributes(cd, args, body={}):
  i = 0
  while i < len(args):
    myarg = args[i].lower().replace(u'_', u'')
    if myarg == u'name':
      body[u'resourceName'] = args[i+1]
      i += 2
    elif myarg == u'description':
      body[u'resourceDescription'] = args[i+1].replace(u'\\n', u'\n')
      i += 2
    elif myarg == u'type':
      body[u'resourceType'] = args[i+1]
      i += 2
    elif myarg in [u'building', u'buildingid']:
      body[u'buildingId'] = _getBuildingByNameOrId(cd, args[i+1], minLen=0)
      i += 2
    elif myarg in [u'capacity']:
      body[u'capacity'] = int(args[i+1])
      i += 2
    elif myarg in [u'feature', u'features']:
      features = args[i+1].split(u',')
      body[u'featureInstances'] = []
      for feature in features:
        body[u'featureInstances'].append({u'feature': {u'name': feature}})
      i += 2
    elif myarg in [u'floor', u'floorname']:
      body[u'floorName'] = args[i+1]
      i += 2
    elif myarg in [u'floorsection']:
      body[u'floorSection'] = args[i+1]
      i += 2
    elif myarg in [u'category']:
      body[u'resourceCategory'] = args[i+1].upper()
      if body[u'resourceCategory'] == u'ROOM':
        body[u'resourceCategory'] = u'CONFERENCE_ROOM'
      i += 2
    elif myarg in [u'uservisibledescription', u'userdescription']:
      body[u'userVisibleDescription'] = args[i+1]
      i += 2
    else:
      systemErrorExit(2, '%s is not a valid argument for "gam create|update resource"' % args[i])
  return body

def doCreateResourceCalendar():
  cd = buildGAPIObject(u'directory')
  body = {u'resourceId': sys.argv[3],
          u'resourceName': sys.argv[4]}
  body = _getResourceCalendarAttributes(cd, sys.argv[5:], body)
  print u'Creating resource %s...' % body[u'resourceId']
  callGAPI(cd.resources().calendars(), u'insert',
           customer=GC_Values[GC_CUSTOMER_ID], body=body)

def doUpdateResourceCalendar():
  cd = buildGAPIObject(u'directory')
  resId = sys.argv[3]
  body = _getResourceCalendarAttributes(cd, sys.argv[4:])
  # Use patch since it seems to work better.
  # update requires name to be set.
  callGAPI(cd.resources().calendars(), u'patch',
           customer=GC_Values[GC_CUSTOMER_ID], calendarResourceId=resId, body=body,
           fields=u'')
  print u'updated resource %s' % resId

def doUpdateUser(users, i):
  cd = buildGAPIObject(u'directory')
  if users is None:
    users = [normalizeEmailAddressOrUID(sys.argv[3])]
  body, admin_body = getUserAttributes(i, cd, updateCmd=True)
  for user in users:
    if u'primaryEmail' in body and body[u'primaryEmail'][:4].lower() == u'vfe@':
      user_primary = callGAPI(cd.users(), u'get', userKey=user, fields=u'primaryEmail,id')
      user = user_primary[u'id']
      user_primary = user_primary[u'primaryEmail']
      user_name, user_domain = splitEmailAddress(user_primary)
      body[u'primaryEmail'] = u'vfe.%s.%05d@%s' % (user_name, random.randint(1, 99999), user_domain)
      body[u'emails'] = [{u'type': u'custom', u'customType': u'former_employee', u'primary': False, u'address': user_primary}]
    sys.stdout.write(u'updating user %s...\n' % user)
    if body:
      callGAPI(cd.users(), u'update', userKey=user, body=body)
    if admin_body:
      callGAPI(cd.users(), u'makeAdmin', userKey=user, body=admin_body)

def doRemoveUsersAliases(users):
  cd = buildGAPIObject(u'directory')
  for user in users:
    user_aliases = callGAPI(cd.users(), u'get', userKey=user, fields=u'aliases,id,primaryEmail')
    user_id = user_aliases[u'id']
    user_primary = user_aliases[u'primaryEmail']
    if u'aliases' in user_aliases:
      print u'%s has %s aliases' % (user_primary, len(user_aliases[u'aliases']))
      for an_alias in user_aliases[u'aliases']:
        print u' removing alias %s for %s...' % (an_alias, user_primary)
        callGAPI(cd.users().aliases(), u'delete', userKey=user_id, alias=an_alias)
    else:
      print u'%s has no aliases' % user_primary

def deleteUserFromGroups(users):
  cd = buildGAPIObject(u'directory')
  for user in users:
    user_groups = callGAPIpages(cd.groups(), u'list', u'groups', userKey=user, fields=u'groups(id,email)')
    num_groups = len(user_groups)
    print u'%s is in %s groups' % (user, num_groups)
    j = 0
    for user_group in user_groups:
      j += 1
      print u' removing %s from %s (%s/%s)' % (user, user_group[u'email'], j, num_groups)
      callGAPI(cd.members(), u'delete', soft_errors=True, groupKey=user_group[u'id'], memberKey=user)
    print u''

def checkGroupExists(cd, group, i=0, count=0):
  group = normalizeEmailAddressOrUID(group)
  try:
    return callGAPI(cd.groups(), u'get',
                    throw_reasons=GAPI_GROUP_GET_THROW_REASONS, retry_reasons=GAPI_GROUP_GET_RETRY_REASONS,
                    groupKey=group, fields=u'email')[u'email']
  except (GAPI_groupNotFound, GAPI_domainNotFound, GAPI_domainCannotUseApis, GAPI_forbidden, GAPI_badRequest):
    entityUnknownWarning(u'Group', group, i, count)
    return None

UPDATE_GROUP_SUBCMDS = [u'add', u'clear', u'delete', u'remove', u'sync', u'update']
GROUP_ROLES_MAP = {
  u'owner': ROLE_OWNER, u'owners': ROLE_OWNER,
  u'manager': ROLE_MANAGER, u'managers': ROLE_MANAGER,
  u'member': ROLE_MEMBER, u'members': ROLE_MEMBER,
  }

def doUpdateGroup():

# Convert foo@googlemail.com to foo@gmail.com; eliminate periods in name for foo.bar@gmail.com
  def _cleanConsumerAddress(emailAddress, mapCleanToOriginal):
    atLoc = emailAddress.find(u'@')
    if atLoc > 0:
      if emailAddress[atLoc+1:] in [u'gmail.com', u'googlemail.com']:
        cleanEmailAddress = emailAddress[:atLoc].replace(u'.', u'')+u'@gmail.com'
        if cleanEmailAddress != emailAddress:
          mapCleanToOriginal[cleanEmailAddress] = emailAddress
          return cleanEmailAddress
    return emailAddress

  def _getRoleAndUsers():
    checkNotSuspended = False
    role = ROLE_MEMBER
    i = 5
    if sys.argv[i].lower() in GROUP_ROLES_MAP:
      role = GROUP_ROLES_MAP[sys.argv[i].lower()]
      i += 1
    if sys.argv[i].lower() == u'notsuspended':
      checkNotSuspended = True
      i += 1
    if sys.argv[i].lower() in usergroup_types:
      users_email = getUsersToModify(entity_type=sys.argv[i], entity=sys.argv[i+1], checkNotSuspended=checkNotSuspended, groupUserMembersOnly=False)
    else:
      users_email = [normalizeEmailAddressOrUID(sys.argv[i], checkForCustomerId=True)]
    return (role, users_email)

  cd = buildGAPIObject(u'directory')
  group = sys.argv[3]
  myarg = sys.argv[4].lower()
  items = []
  if myarg in UPDATE_GROUP_SUBCMDS:
    group = normalizeEmailAddressOrUID(group)
    if myarg == u'add':
      role, users_email = _getRoleAndUsers()
      if not checkGroupExists(cd, group):
        return
      if len(users_email) > 1:
        sys.stderr.write(u'Group: {0}, Will add {1} {2}s.\n'.format(group, len(users_email), role))
        for user_email in users_email:
          items.append(['gam', 'update', 'group', group, 'add', role, user_email])
      else:
        body = {u'role': role, u'email': users_email[0]}
        for i in range(2):
          try:
            callGAPI(cd.members(), u'insert',
                     throw_reasons=[GAPI_DUPLICATE, GAPI_MEMBER_NOT_FOUND, GAPI_RESOURCE_NOT_FOUND, GAPI_INVALID_MEMBER, GAPI_CYCLIC_MEMBERSHIPS_NOT_ALLOWED],
                     groupKey=group, body=body)
            print u' Group: {0}, {1} Added as {2}'.format(group, users_email[0], role)
            break
          except GAPI_duplicate as e:
            # check if user is a full member, not pending
            try:
              result = callGAPI(cd.members(), u'get', throw_reasons=[GAPI_MEMBER_NOT_FOUND], memberKey=users_email[0], groupKey=group, fields=u'role')
              print u' Group: {0}, {1} Add as {2} Failed: Duplicate, already a {3}'.format(group, users_email[0], role, result[u'role'])
              break # if get succeeds, user is a full member and we throw duplicate error
            except GAPI_memberNotFound:
              # insert fails on duplicate and get fails on not found, user is pending
              print u' Group: {0}, {1} member is pending, deleting and re-adding to solve...'.format(group, users_email[0])
              callGAPI(cd.members(), u'delete', memberKey=users_email[0], groupKey=group)
              continue # 2nd insert should succeed now that pending is clear
          except (GAPI_memberNotFound, GAPI_resourceNotFound, GAPI_invalidMember, GAPI_cyclicMembershipsNotAllowed) as e:
            print u' Group: {0}, {1} Add as {2} Failed: {3}'.format(group, users_email[0], role, str(e))
            break
    elif myarg == u'sync':
      syncMembersSet = set()
      syncMembersMap = {}
      role, users_email = _getRoleAndUsers()
      for user_email in users_email:
        if user_email == u'*' or user_email == GC_Values[GC_CUSTOMER_ID]:
          syncMembersSet.add(GC_Values[GC_CUSTOMER_ID])
        else:
          syncMembersSet.add(_cleanConsumerAddress(user_email.lower(), syncMembersMap))
      group = checkGroupExists(cd, group)
      if group:
        currentMembersSet = set()
        currentMembersMap = {}
        for current_email in getUsersToModify(entity_type=u'group', entity=group, member_type=role, groupUserMembersOnly=False):
          if current_email == GC_Values[GC_CUSTOMER_ID]:
            currentMembersSet.add(current_email)
          else:
            currentMembersSet.add(_cleanConsumerAddress(current_email.lower(), currentMembersMap))
# Compare incoming members and current memebers using the cleaned addresses; we actually add/remove with the original addresses
        to_add = [syncMembersMap.get(emailAddress, emailAddress) for emailAddress in syncMembersSet-currentMembersSet]
        to_remove = [currentMembersMap.get(emailAddress, emailAddress) for emailAddress in currentMembersSet-syncMembersSet]
        sys.stderr.write(u'Group: {0}, Will add {1} and remove {2} {3}s.\n'.format(group, len(to_add), len(to_remove), role))
        for user in to_add:
          items.append([u'gam', u'update', u'group', group, u'add', role, user])
        for user in to_remove:
          items.append([u'gam', u'update', u'group', group, u'remove', user])
    elif myarg in [u'delete', u'remove']:
      role, users_email = _getRoleAndUsers()
      if not checkGroupExists(cd, group):
        return
      if len(users_email) > 1:
        sys.stderr.write(u'Group: {0}, Will remove {1} {2}s.\n'.format(group, len(users_email), role))
        for user_email in users_email:
          items.append(['gam', 'update', 'group', group, 'remove', user_email])
      else:
        try:
          callGAPI(cd.members(), u'delete',
                   throw_reasons=[GAPI_MEMBER_NOT_FOUND, GAPI_INVALID_MEMBER],
                   groupKey=group, memberKey=users_email[0])
          print u' Group: {0}, {1} Removed'.format(group, users_email[0])
        except (GAPI_memberNotFound, GAPI_invalidMember) as e:
          print u' Group: {0}, {1} Remove Failed: {2}'.format(group, users_email[0], str(e))
    elif myarg == u'update':
      role, users_email = _getRoleAndUsers()
      group = checkGroupExists(cd, group)
      if group:
        if len(users_email) > 1:
          sys.stderr.write(u'Group: {0}, Will update {1} {2}s.\n'.format(group, len(users_email), role))
          for user_email in users_email:
            items.append(['gam', 'update', 'group', group, 'update', role, user_email])
        else:
          body = {u'role': role}
          try:
            callGAPI(cd.members(), u'update',
                     throw_reasons=[GAPI_MEMBER_NOT_FOUND, GAPI_INVALID_MEMBER],
                     groupKey=group, memberKey=users_email[0], body=body)
            print u' Group: {0}, {1} Updated to {2}'.format(group, users_email[0], role)
          except (GAPI_memberNotFound, GAPI_invalidMember) as e:
            print u' Group: {0}, {1} Update to {2} Failed: {3}'.format(group, users_email[0], role, str(e))
    else: # clear
      suspended = False
      fields = [u'email', u'id']
      roles = []
      i = 5
      while i < len(sys.argv):
        myarg = sys.argv[i].lower()
        if myarg.upper() in [ROLE_OWNER, ROLE_MANAGER, ROLE_MEMBER]:
          roles.append(myarg.upper())
          i += 1
        elif myarg == u'suspended':
          suspended = True
          fields.append(u'status')
          i += 1
        else:
          systemErrorExit(2, '%s is not a valid argument for "gam update group clear"' % sys.argv[i])
      if roles:
        roles = u','.join(sorted(set(roles)))
      else:
        roles = ROLE_MEMBER
      group = normalizeEmailAddressOrUID(group)
      member_type_message = u'%ss' % roles.lower()
      sys.stderr.write(u"Getting %s of %s (may take some time for large groups)...\n" % (member_type_message, group))
      page_message = u'Got %%%%total_items%%%% %s...' % member_type_message
      try:
        result = callGAPIpages(cd.members(), u'list', u'members',
                               page_message=page_message,
                               throw_reasons=GAPI_MEMBERS_THROW_REASONS,
                               groupKey=group, roles=roles, fields=u'nextPageToken,members({0})'.format(u','.join(fields)),
                               maxResults=GC_Values[GC_MEMBER_MAX_RESULTS])
        if not suspended:
          users_email = [member.get(u'email', member[u'id']) for member in result]
        else:
          users_email = [member.get(u'email', member[u'id']) for member in result if member[u'status'] == u'SUSPENDED']
        if len(users_email) > 1:
          sys.stderr.write(u'Group: {0}, Will remove {1} {2}{3}s.\n'.format(group, len(users_email), [u'', u'suspended '][suspended], roles))
          for user_email in users_email:
            items.append(['gam', 'update', 'group', group, 'remove', user_email])
        else:
          try:
            callGAPI(cd.members(), u'delete',
                     throw_reasons=[GAPI_MEMBER_NOT_FOUND, GAPI_INVALID_MEMBER],
                     groupKey=group, memberKey=users_email[0])
            print u' Group: {0}, {1} Removed'.format(group, users_email[0])
          except (GAPI_memberNotFound, GAPI_invalidMember) as e:
            print u' Group: {0}, {1} Remove Failed: {2}'.format(group, users_email[0], str(e))
      except (GAPI_groupNotFound, GAPI_domainNotFound, GAPI_invalid, GAPI_forbidden):
        entityUnknownWarning(u'Group', group, 0, 0)
    if items:
      run_batch(items)
  else:
    i = 4
    use_cd_api = False
    gs = None
    gs_body = {}
    cd_body = {}
    while i < len(sys.argv):
      myarg = sys.argv[i].lower().replace(u'_', u'')
      if myarg == u'email':
        use_cd_api = True
        cd_body[u'email'] = normalizeEmailAddressOrUID(sys.argv[i+1])
        i += 2
      elif myarg == u'admincreated':
        use_cd_api = True
        cd_body[u'adminCreated'] = getBoolean(sys.argv[i+1], myarg)
        i += 2
      else:
        if not gs:
          gs = buildGAPIObject(u'groupssettings')
          gs_object = gs._rootDesc
        getGroupAttrValue(myarg, sys.argv[i+1], gs_object, gs_body, u'update')
        i += 2
    group = normalizeEmailAddressOrUID(group)
    if use_cd_api or (group.find(u'@') == -1): # group settings API won't take uid so we make sure cd API is used so that we can grab real email.
      group = callGAPI(cd.groups(), u'update', groupKey=group, body=cd_body, fields=u'email')[u'email']
    if gs:
      if not GroupIsAbuseOrPostmaster(group):
        settings = callGAPI(gs.groups(), u'get',
                            retry_reasons=[u'serviceLimit'],
                            groupUniqueId=group, fields=u'*')
        if settings is not None:
          settings.update(gs_body)
          callGAPI(gs.groups(), u'update', retry_reasons=[u'serviceLimit'], groupUniqueId=group, body=settings)
    print u'updated group %s' % group

def doUpdateAlias():
  cd = buildGAPIObject(u'directory')
  alias = normalizeEmailAddressOrUID(sys.argv[3], noUid=True)
  target_type = sys.argv[4].lower()
  if target_type not in [u'user', u'group', u'target']:
    systemErrorExit(2, 'target type must be one of user, group, target; got %s' % target_type)
  target_email = normalizeEmailAddressOrUID(sys.argv[5])
  try:
    callGAPI(cd.users().aliases(), u'delete', throw_reasons=[GAPI_INVALID], userKey=alias, alias=alias)
  except GAPI_invalid:
    callGAPI(cd.groups().aliases(), u'delete', groupKey=alias, alias=alias)
  if target_type == u'user':
    callGAPI(cd.users().aliases(), u'insert', userKey=target_email, body={u'alias': alias})
  elif target_type == u'group':
    callGAPI(cd.groups().aliases(), u'insert', groupKey=target_email, body={u'alias': alias})
  elif target_type == u'target':
    try:
      callGAPI(cd.users().aliases(), u'insert', throw_reasons=[GAPI_INVALID], userKey=target_email, body={u'alias': alias})
    except GAPI_invalid:
      callGAPI(cd.groups().aliases(), u'insert', groupKey=target_email, body={u'alias': alias})
  print u'updated alias %s' % alias

def doUpdateCros():
  cd = buildGAPIObject(u'directory')
  deviceId = sys.argv[3]
  if deviceId[:6].lower() == u'query:':
    query = deviceId[6:]
    if query[:12].lower() == u'orgunitpath:':
      kwargs = {u'orgUnitPath': query[12:]}
    else:
      kwargs = {u'query': query}
    devices_result = callGAPIpages(cd.chromeosdevices(), u'list', u'chromeosdevices',
                                   customerId=GC_Values[GC_CUSTOMER_ID], fields=u'chromeosdevices/deviceId,nextPageToken', **kwargs)
    devices = list()
    for a_device in devices_result:
      devices.append(a_device[u'deviceId'])
  else:
    devices = [deviceId,]
  i = 4
  update_body = {}
  action_body = {}
  orgUnitPath = None
  ack_wipe = False
  while i < len(sys.argv):
    myarg = sys.argv[i].lower().replace(u'_', u'')
    if myarg == u'user':
      update_body[u'annotatedUser'] = sys.argv[i+1]
      i += 2
    elif myarg == u'location':
      update_body[u'annotatedLocation'] = sys.argv[i+1]
      i += 2
    elif myarg == u'notes':
      update_body[u'notes'] = sys.argv[i+1].replace(u'\\n', u'\n')
      i += 2
    elif myarg in [u'tag', u'asset', u'assetid']:
      update_body[u'annotatedAssetId'] = sys.argv[i+1]
      i += 2
    elif myarg in [u'ou', u'org']:
      orgUnitPath = sys.argv[i+1]
      i += 2
    elif myarg == u'action':
      action = sys.argv[i+1].lower().replace(u'_', u'').replace(u'-', u'')
      deprovisionReason = None
      if action in [u'deprovisionsamemodelreplace', u'deprovisionsamemodelreplacement']:
        action = u'deprovision'
        deprovisionReason = u'same_model_replacement'
      elif action in [u'deprovisiondifferentmodelreplace', u'deprovisiondifferentmodelreplacement']:
        action = u'deprovision'
        deprovisionReason = u'different_model_replacement'
      elif action in [u'deprovisionretiringdevice']:
        action = u'deprovision'
        deprovisionReason = u'retiring_device'
      elif action not in [u'disable', u'reenable']:
        systemErrorExit(2, 'expected action of deprovision_same_model_replace, deprovision_different_model_replace, deprovision_retiring_device, disable or reenable, got %s' % action)
      action_body = {u'action': action}
      if deprovisionReason:
        action_body[u'deprovisionReason'] = deprovisionReason
      i += 2
    elif myarg == u'acknowledgedevicetouchrequirement':
      ack_wipe = True
      i += 1
    else:
      systemErrorExit(2, '%s is not a valid argument for "gam update cros"' % sys.argv[i])
  i = 0
  count = len(devices)
  if action_body:
    if action_body[u'action'] == u'deprovision' and not ack_wipe:
      print u'WARNING: Refusing to deprovision %s devices because acknowledge_device_touch_requirement not specified. Deprovisioning a device means the device will have to be physically wiped and re-enrolled to be managed by your domain again. This requires physical access to the device and is very time consuming to perform for each device. Please add "acknowledge_device_touch_requirement" to the GAM command if you understand this and wish to proceed with the deprovision. Please also be aware that deprovisioning can have an effect on your device license count. See https://support.google.com/chrome/a/answer/3523633 for full details.' % (count)
      sys.exit(3)
    for deviceId in devices:
      i += 1
      print u' performing action %s for %s (%s of %s)' % (action, deviceId, i, count)
      callGAPI(cd.chromeosdevices(), function=u'action', customerId=GC_Values[GC_CUSTOMER_ID], resourceId=deviceId, body=action_body)
  else:
    if update_body:
      for deviceId in devices:
        i += 1
        print u' updating %s (%s of %s)' % (deviceId, i, count)
        callGAPI(service=cd.chromeosdevices(), function=u'update', customerId=GC_Values[GC_CUSTOMER_ID], deviceId=deviceId, body=update_body)
    if orgUnitPath:
      #move_body[u'deviceIds'] = devices
      # split moves into max 50 devices per batch
      for l in range(0, len(devices), 50):
        move_body = {u'deviceIds': devices[l:l+50]}
        print u' moving %s devices to %s' % (len(move_body[u'deviceIds']), orgUnitPath)
        callGAPI(cd.chromeosdevices(), u'moveDevicesToOu', customerId=GC_Values[GC_CUSTOMER_ID], orgUnitPath=orgUnitPath, body=move_body)

def doUpdateMobile():
  cd = buildGAPIObject(u'directory')
  resourceId = sys.argv[3]
  i = 4
  body = {}
  while i < len(sys.argv):
    myarg = sys.argv[i].lower()
    if myarg == u'action':
      body[u'action'] = sys.argv[i+1].lower()
      if body[u'action'] == u'wipe':
        body[u'action'] = u'admin_remote_wipe'
      elif body[u'action'].replace(u'_', u'') in [u'accountwipe', u'wipeaccount']:
        body[u'action'] = u'admin_account_wipe'
      if body[u'action'] not in [u'admin_remote_wipe', u'admin_account_wipe', u'approve', u'block', u'cancel_remote_wipe_then_activate', u'cancel_remote_wipe_then_block']:
        systemErrorExit(2, 'action must be one of wipe, wipeaccount, approve, block, cancel_remote_wipe_then_activate, cancel_remote_wipe_then_block; got %s' % body[u'action'])
      i += 2
    else:
      systemErrorExit(2, '%s is not a valid argument for "gam update mobile"' % sys.argv[i])
  if body:
    callGAPI(cd.mobiledevices(), u'action', resourceId=resourceId, body=body, customerId=GC_Values[GC_CUSTOMER_ID])

def doDeleteMobile():
  cd = buildGAPIObject(u'directory')
  resourceId = sys.argv[3]
  callGAPI(cd.mobiledevices(), u'delete', resourceId=resourceId, customerId=GC_Values[GC_CUSTOMER_ID])

def doUpdateOrg():
  cd = buildGAPIObject(u'directory')
  orgUnitPath = sys.argv[3]
  if sys.argv[4].lower() in [u'move', u'add']:
    if sys.argv[5].lower() in usergroup_types:
      users = getUsersToModify(entity_type=sys.argv[5].lower(), entity=sys.argv[6])
    else:
      users = getUsersToModify(entity_type=u'user', entity=sys.argv[5])
    if (sys.argv[5].lower() == u'cros') or ((sys.argv[5].lower() == u'all') and (sys.argv[6].lower() == u'cros')):
      for l in range(0, len(users), 50):
        move_body = {u'deviceIds': users[l:l+50]}
        print u' moving %s devices to %s' % (len(move_body[u'deviceIds']), orgUnitPath)
        callGAPI(cd.chromeosdevices(), u'moveDevicesToOu', customerId=GC_Values[GC_CUSTOMER_ID], orgUnitPath=orgUnitPath, body=move_body)
    else:
      if orgUnitPath != u'/' and orgUnitPath[0] != u'/': # we do want a / at the beginning for user updates
        orgUnitPath = u'/%s' % orgUnitPath
      current_user = 0
      user_count = len(users)
      for user in users:
        current_user += 1
        sys.stderr.write(u' moving %s to %s (%s/%s)\n' % (user, orgUnitPath, current_user, user_count))
        try:
          callGAPI(cd.users(), u'update', throw_reasons=[GAPI_CONDITION_NOT_MET], userKey=user, body={u'orgUnitPath': orgUnitPath})
        except GAPI_conditionNotMet:
          pass
  else:
    body = {}
    i = 4
    while i < len(sys.argv):
      myarg = sys.argv[i].lower()
      if myarg == u'name':
        body[u'name'] = sys.argv[i+1]
        i += 2
      elif myarg == u'description':
        body[u'description'] = sys.argv[i+1].replace(u'\\n', u'\n')
        i += 2
      elif myarg == u'parent':
        body[u'parentOrgUnitPath'] = sys.argv[i+1]
        if body[u'parentOrgUnitPath'][0] != u'/':
          body[u'parentOrgUnitPath'] = u'/'+body[u'parentOrgUnitPath']
        i += 2
      elif myarg == u'noinherit':
        body[u'blockInheritance'] = True
        i += 1
      elif myarg == u'inherit':
        body[u'blockInheritance'] = False
        i += 1
      else:
        systemErrorExit(2, '%s is not a valid argument for "gam update org"' % sys.argv[i])
    if orgUnitPath[0] == u'/': # we don't want a / at the beginning for OU updates
      orgUnitPath = orgUnitPath[1:]
    callGAPI(cd.orgunits(), u'update', customerId=GC_Values[GC_CUSTOMER_ID], orgUnitPath=orgUnitPath, body=body)

def doWhatIs():
  cd = buildGAPIObject(u'directory')
  email = normalizeEmailAddressOrUID(sys.argv[2])
  try:
    user_or_alias = callGAPI(cd.users(), u'get', throw_reasons=[GAPI_NOT_FOUND, GAPI_BAD_REQUEST, GAPI_INVALID], userKey=email, fields=u'id,primaryEmail')
    if (user_or_alias[u'primaryEmail'].lower() == email) or (user_or_alias[u'id'] == email):
      sys.stderr.write(u'%s is a user\n\n' % email)
      doGetUserInfo(user_email=email)
      return
    else:
      sys.stderr.write(u'%s is a user alias\n\n' % email)
      doGetAliasInfo(alias_email=email)
      return
  except (GAPI_notFound, GAPI_badRequest, GAPI_invalid):
    sys.stderr.write(u'%s is not a user...\n' % email)
    sys.stderr.write(u'%s is not a user alias...\n' % email)
  try:
    group = callGAPI(cd.groups(), u'get', throw_reasons=[GAPI_NOT_FOUND, GAPI_BAD_REQUEST], groupKey=email, fields=u'id,email')
  except (GAPI_notFound, GAPI_badRequest):
    systemErrorExit(1, u'%s is not a group either!\n\nDoesn\'t seem to exist!\n\n' % email)
  if (group[u'email'].lower() == email) or (group[u'id'] == email):
    sys.stderr.write(u'%s is a group\n\n' % email)
    doGetGroupInfo(group_name=email)
  else:
    sys.stderr.write(u'%s is a group alias\n\n' % email)
    doGetAliasInfo(alias_email=email)

def convertSKU2ProductId(res, sku, customerId):
  results = callGAPI(res.subscriptions(), u'list', customerId=customerId)
  for subscription in results[u'subscriptions']:
    if sku == subscription[u'skuId']:
      return subscription[u'subscriptionId']
  systemErrorExit(3, 'could not find subscription for customer %s and SKU %s' % (customerId, sku))

def doDeleteResoldSubscription():
  res = buildGAPIObject(u'reseller')
  customerId = sys.argv[3]
  sku = sys.argv[4]
  deletionType = sys.argv[5]
  subscriptionId = convertSKU2ProductId(res, sku, customerId)
  callGAPI(res.subscriptions(), u'delete', customerId=customerId, subscriptionId=subscriptionId, deletionType=deletionType)
  print u'Cancelled %s for %s' % (sku, customerId)

def doCreateResoldSubscription():
  res = buildGAPIObject(u'reseller')
  customerId = sys.argv[3]
  customerAuthToken, body = _getResoldSubscriptionAttr(sys.argv[4:], customerId)
  result = callGAPI(res.subscriptions(), u'insert', customerId=customerId, customerAuthToken=customerAuthToken, body=body, fields=u'customerId')
  print u'Created subscription:'
  print_json(None, result)

def doUpdateResoldSubscription():
  res = buildGAPIObject(u'reseller')
  function = None
  customerId = sys.argv[3]
  sku = sys.argv[4]
  subscriptionId = convertSKU2ProductId(res, sku, customerId)
  kwargs = {}
  i = 5
  while i < len(sys.argv):
    myarg = sys.argv[i].lower()
    if myarg == u'activate':
      function = u'activate'
      i += 1
    elif myarg == u'suspend':
      function = u'suspend'
      i += 1
    elif myarg == u'startpaidservice':
      function = u'startPaidService'
      i += 1
    elif myarg in [u'renewal', u'renewaltype']:
      function = u'changeRenewalSettings'
      kwargs[u'body'] = {u'renewalType': sys.argv[i+1].upper()}
      i += 2
    elif myarg in [u'seats']:
      function = u'changeSeats'
      kwargs[u'body'] = {u'numberOfSeats': sys.argv[i+1]}
      if len(sys.argv) > i + 2 and sys.argv[i+2].isdigit():
        kwargs[u'body'][u'maximumNumberOfSeats'] = sys.argv[i+2]
        i += 3
      else:
        i += 2
    elif myarg in [u'plan']:
      function = u'changePlan'
      kwargs[u'body'] = {u'planName': sys.argv[i+1].upper()}
      i += 2
      while i < len(sys.argv):
        planarg = sys.argv[i].lower()
        if planarg == u'seats':
          kwargs[u'body'][u'seats'] = {u'numberOfSeats': sys.argv[i+1]}
          if len(sys.argv) > i + 2 and sys.argv[i+2].isdigit():
            kwargs[u'body'][u'seats'][u'maximumNumberOfSeats'] = sys.argv[i+2]
            i += 3
          else:
            i += 2
        elif planarg in [u'purchaseorderid', u'po']:
          kwargs[u'body'][u'purchaseOrderId'] = sys.argv[i+1]
          i += 2
        elif planarg in [u'dealcode', u'deal']:
          kwargs[u'body'][u'dealCode'] = sys.argv[i+1]
          i += 2
        else:
          systemErrorExit(3, '%s is not a valid argument to "gam update resoldsubscription plan"' % planarg)
    else:
      systemErrorExit(3, '%s is not a valid argument to "gam update resoldsubscription"' % myarg)
  result = callGAPI(res.subscriptions(), function, customerId=customerId, subscriptionId=subscriptionId, **kwargs)
  print u'Updated %s SKU %s subscription:' % (customerId, sku)
  if result:
    print_json(None, result)

def doGetResoldSubscriptions():
  res = buildGAPIObject(u'reseller')
  customerId = sys.argv[3]
  customerAuthToken = None
  i = 4
  while i < len(sys.argv):
    myarg = sys.argv[i].lower().replace(u'_', u'')
    if myarg in [u'customerauthtoken', u'transfertoken']:
      customerAuthToken = sys.argv[i+1]
      i += 2
    else:
      systemErrorExit(3, '%s is not a valid argument for "gam info resoldsubscriptions"' % myarg)
  result = callGAPI(res.subscriptions(), u'list', customerId=customerId, customerAuthToken=customerAuthToken)
  print_json(None, result)

def _getResoldSubscriptionAttr(arg, customerId):
  body = {u'plan': {},
          u'seats': {},
          u'customerId': customerId}
  customerAuthToken = None
  i = 0
  while i < len(arg):
    myarg = arg[i].lower().replace(u'_', u'')
    if myarg in [u'deal', u'dealcode']:
      body[u'dealCode'] = arg[i+1]
    elif myarg in [u'plan', u'planname']:
      body[u'plan'][u'planName'] = arg[i+1].upper()
    elif myarg in [u'purchaseorderid', u'po']:
      body[u'purchaseOrderId'] = arg[i+1]
    elif myarg in [u'seats']:
      body[u'seats'][u'numberOfSeats'] = arg[i+1]
      if len(arg) > i + 2 and arg[i+2].isdigit():
        body[u'seats'][u'maximumNumberOfSeats'] = arg[i+2]
        i += 1
    elif myarg in [u'sku', u'skuid']:
      _, body[u'skuId'] = getProductAndSKU(arg[i+1])
    elif myarg in [u'customerauthtoken', u'transfertoken']:
      customerAuthToken = arg[i+1]
    else:
      systemErrorExit(3, '%s is not a valid argument for "gam create resoldsubscription"' % myarg)
    i += 2
  return customerAuthToken, body

def doGetResoldCustomer():
  res = buildGAPIObject(u'reseller')
  customerId = sys.argv[3]
  result = callGAPI(res.customers(), u'get', customerId=customerId)
  print_json(None, result)

def _getResoldCustomerAttr(arg):
  body = {}
  customerAuthToken = None
  i = 0
  while i < len(arg):
    myarg = arg[i].lower().replace(u'_', u'')
    if myarg in ADDRESS_FIELDS_ARGUMENT_MAP:
      body.setdefault(u'postalAddress', {})
      body[u'postalAddress'][ADDRESS_FIELDS_ARGUMENT_MAP[myarg]] = arg[i+1]
    elif myarg in [u'email', u'alternateemail']:
      body[u'alternateEmail'] = arg[i+1]
    elif myarg in [u'phone', u'phonenumber']:
      body[u'phoneNumber'] = arg[i+1]
    elif myarg in [u'customerauthtoken', u'transfertoken']:
      customerAuthToken = arg[i+1]
    else:
      systemErrorExit(3, '%s is not a valid argument for "gam %s resoldcustomer"' % (myarg, sys.argv[1]))
    i += 2
  return customerAuthToken, body

def doUpdateResoldCustomer():
  res = buildGAPIObject(u'reseller')
  customerId = sys.argv[3]
  customerAuthToken, body = _getResoldCustomerAttr(sys.argv[4:])
  callGAPI(res.customers(), u'patch', customerId=customerId, body=body, customerAuthToken=customerAuthToken, fields=u'customerId')
  print u'updated customer %s' % customerId

def doCreateResoldCustomer():
  res = buildGAPIObject(u'reseller')
  customerAuthToken, body = _getResoldCustomerAttr(sys.argv[4:])
  body[u'customerDomain'] = sys.argv[3]
  result = callGAPI(res.customers(), u'insert', body=body, customerAuthToken=customerAuthToken, fields=u'customerId,customerDomain')
  print u'Created customer %s with id %s' % (result[u'customerDomain'], result[u'customerId'])

def _getValueFromOAuth(field, credentials=None):
  credentials = credentials if credentials is not None else getValidOauth2TxtCredentials()
  return credentials.id_token.get(field, u'Unknown')

def doGetUserInfo(user_email=None):

  def user_lic_result(request_id, response, exception):
    if response and u'skuId' in response:
      user_licenses.append(response[u'skuId'])

  cd = buildGAPIObject(u'directory')
  i = 3
  if user_email is None:
    if len(sys.argv) > 3:
      user_email = normalizeEmailAddressOrUID(sys.argv[3])
      i = 4
    else:
      user_email = _getValueFromOAuth(u'email')
  getSchemas = getAliases = getGroups = getLicenses = True
  projection = u'full'
  customFieldMask = viewType = None
  skus = sorted(SKUS.keys())
  while i < len(sys.argv):
    myarg = sys.argv[i].lower()
    if myarg == u'noaliases':
      getAliases = False
      i += 1
    elif myarg == u'nogroups':
      getGroups = False
      i += 1
    elif myarg in [u'nolicenses', u'nolicences']:
      getLicenses = False
      i += 1
    elif myarg in [u'sku', u'skus']:
      skus = sys.argv[i+1].split(u',')
      i += 2
    elif myarg == u'noschemas':
      getSchemas = False
      projection = u'basic'
      i += 1
    elif myarg in [u'custom', u'schemas']:
      getSchemas = True
      projection = u'custom'
      customFieldMask = sys.argv[i+1]
      i += 2
    elif myarg == u'userview':
      viewType = u'domain_public'
      getGroups = getLicenses = False
      i += 1
    elif myarg in [u'nousers', u'groups']:
      i += 1
    else:
      systemErrorExit(2, '%s is not a valid argument for "gam info user"' % myarg)
  user = callGAPI(cd.users(), u'get', userKey=user_email, projection=projection, customFieldMask=customFieldMask, viewType=viewType)
  print u'User: %s' % user[u'primaryEmail']
  if u'name' in user and u'givenName' in user[u'name']:
    print utils.convertUTF8(u'First Name: %s' % user[u'name'][u'givenName'])
  if u'name' in user and u'familyName' in user[u'name']:
    print utils.convertUTF8(u'Last Name: %s' % user[u'name'][u'familyName'])
  if u'languages' in user:
    up = u'languageCode'
    languages = [row[up] for row in user[u'languages'] if up in row]
    if languages:
      print u'Languages: %s' % u','.join(languages)
    up = u'customLanguage'
    languages = [row[up] for row in user[u'languages'] if up in row]
    if languages:
      print u'Custom Languages: %s' % u','.join(languages)
  if u'isAdmin' in user:
    print u'Is a Super Admin: %s' % user[u'isAdmin']
  if u'isDelegatedAdmin' in user:
    print u'Is Delegated Admin: %s' % user[u'isDelegatedAdmin']
  if u'isEnrolledIn2Sv' in user:
    print u'2-step enrolled: %s' % user[u'isEnrolledIn2Sv']
  if u'isEnforcedIn2Sv' in user:
    print u'2-step enforced: %s' % user[u'isEnforcedIn2Sv']
  if u'agreedToTerms' in user:
    print u'Has Agreed to Terms: %s' % user[u'agreedToTerms']
  if u'ipWhitelisted' in user:
    print u'IP Whitelisted: %s' % user[u'ipWhitelisted']
  if u'suspended' in user:
    print u'Account Suspended: %s' % user[u'suspended']
  if u'suspensionReason' in user:
    print u'Suspension Reason: %s' % user[u'suspensionReason']
  if u'changePasswordAtNextLogin' in user:
    print u'Must Change Password: %s' % user[u'changePasswordAtNextLogin']
  if u'id' in user:
    print u'Google Unique ID: %s' % user[u'id']
  if u'customerId' in user:
    print u'Customer ID: %s' % user[u'customerId']
  if u'isMailboxSetup' in user:
    print u'Mailbox is setup: %s' % user[u'isMailboxSetup']
  if u'includeInGlobalAddressList' in user:
    print u'Included in GAL: %s' % user[u'includeInGlobalAddressList']
  if u'creationTime' in user:
    print u'Creation Time: %s' % user[u'creationTime']
  if u'lastLoginTime' in user:
    if user[u'lastLoginTime'] == NEVER_TIME:
      print u'Last login time: Never'
    else:
      print u'Last login time: %s' % user[u'lastLoginTime']
  if u'orgUnitPath' in user:
    print u'Google Org Unit Path: %s\n' % user[u'orgUnitPath']
  if u'thumbnailPhotoUrl' in user:
    print u'Photo URL: %s\n' % user[u'thumbnailPhotoUrl']
  if u'notes' in user:
    print u'Notes:'
    notes = user[u'notes']
    if isinstance(notes, dict):
      contentType = notes.get(u'contentType', u'text_plain')
      print u' %s: %s' % (u'contentType', contentType)
      if contentType == u'text_html':
        print utils.convertUTF8(utils.indentMultiLineText(u' value: {0}'.format(utils.dehtml(notes[u'value'])), n=2))
      else:
        print utils.convertUTF8(utils.indentMultiLineText(u' value: {0}'.format(notes[u'value']), n=2))
    else:
      print utils.convertUTF8(utils.indentMultiLineText(u' value: {0}'.format(notes), n=2))
    print u''
  if u'gender' in user:
    print u'Gender'
    gender = user[u'gender']
    for key in gender:
      if key == u'customGender' and not gender[key]:
        continue
      print utils.convertUTF8(u' %s: %s' % (key, gender[key]))
    print u''
  if u'keywords' in user:
    print u'Keywords:'
    for keyword in user[u'keywords']:
      for key in keyword:
        if key == u'customType' and not keyword[key]:
          continue
        print utils.convertUTF8(u' %s: %s' % (key, keyword[key]))
      print u''
  if u'ims' in user:
    print u'IMs:'
    for im in user[u'ims']:
      for key in im:
        print utils.convertUTF8(u' %s: %s' % (key, im[key]))
      print u''
  if u'addresses' in user:
    print u'Addresses:'
    for address in user[u'addresses']:
      for key in address:
        if key != u'formatted':
          print utils.convertUTF8(u' %s: %s' % (key, address[key]))
        else:
          print utils.convertUTF8(u' %s: %s' % (key, address[key].replace(u'\n', u'\\n')))
      print u''
  if u'organizations' in user:
    print u'Organizations:'
    for org in user[u'organizations']:
      for key in org:
        if key == u'customType' and not org[key]:
          continue
        print utils.convertUTF8(u' %s: %s' % (key, org[key]))
      print u''
  if u'locations' in user:
    print u'Locations:'
    for location in user[u'locations']:
      for key in location:
        if key == u'customType' and not location[key]:
          continue
        print utils.convertUTF8(u' %s: %s' % (key, location[key]))
      print u''
  if u'sshPublicKeys' in user:
    print u'SSH Public Keys:'
    for sshkey in user[u'sshPublicKeys']:
      for key in sshkey:
        print utils.convertUTF8(u' %s: %s' % (key, sshkey[key]))
      print u''
  if u'posixAccounts' in user:
    print u'Posix Accounts:'
    for posix in user[u'posixAccounts']:
      for key in posix:
        print utils.convertUTF8(u' %s: %s' % (key, posix[key]))
      print u''
  if u'phones' in user:
    print u'Phones:'
    for phone in user[u'phones']:
      for key in phone:
        print utils.convertUTF8(u' %s: %s' % (key, phone[key]))
      print u''
  if u'emails' in user:
    if len(user[u'emails']) > 1:
      print u'Other Emails:'
      for an_email in user[u'emails']:
        if an_email[u'address'].lower() == user[u'primaryEmail'].lower():
          continue
        for key in an_email:
          if key == u'type' and an_email[key] == u'custom':
            continue
          if key == u'customType':
            print utils.convertUTF8(u' type: %s' % an_email[key])
          else:
            print utils.convertUTF8(u' %s: %s' % (key, an_email[key]))
      print u''
  if u'relations' in user:
    print u'Relations:'
    for relation in user[u'relations']:
      for key in relation:
        if key == u'type' and relation[key] == u'custom':
          continue
        elif key == u'customType':
          print utils.convertUTF8(u' %s: %s' % (u'type', relation[key]))
        else:
          print utils.convertUTF8(u' %s: %s' % (key, relation[key]))
      print u''
  if u'externalIds' in user:
    print u'External IDs:'
    for externalId in user[u'externalIds']:
      for key in externalId:
        if key == u'type' and externalId[key] == u'custom':
          continue
        elif key == u'customType':
          print utils.convertUTF8(u' %s: %s' % (u'type', externalId[key]))
        else:
          print utils.convertUTF8(u' %s: %s' % (key, externalId[key]))
      print u''
  if u'websites' in user:
    print u'Websites:'
    for website in user[u'websites']:
      for key in website:
        if key == u'type' and website[key] == u'custom':
          continue
        elif key == u'customType':
          print utils.convertUTF8(u' %s: %s' % (u'type', website[key]))
        else:
          print utils.convertUTF8(u' %s: %s' % (key, website[key]))
      print u''
  if getSchemas:
    if u'customSchemas' in user:
      print u'Custom Schemas:'
      for schema in user[u'customSchemas']:
        print u' Schema: %s' % schema
        for field in user[u'customSchemas'][schema]:
          if isinstance(user[u'customSchemas'][schema][field], list):
            print u'  %s:' % field
            for an_item in user[u'customSchemas'][schema][field]:
              print utils.convertUTF8(u'   type: %s' % (an_item[u'type']))
              if an_item[u'type'] == u'custom':
                print utils.convertUTF8(u'    customType: %s' % (an_item[u'customType']))
              print utils.convertUTF8(u'    value: %s' % (an_item[u'value']))
          else:
            print utils.convertUTF8(u'  %s: %s' % (field, user[u'customSchemas'][schema][field]))
        print
  if getAliases:
    if u'aliases' in user:
      print u'Email Aliases:'
      for alias in user[u'aliases']:
        print u'  %s' % alias
    if u'nonEditableAliases' in user:
      print u'Non-Editable Aliases:'
      for alias in user[u'nonEditableAliases']:
        print u'  %s' % alias
  if getGroups:
    groups = callGAPIpages(cd.groups(), u'list', u'groups', userKey=user_email, fields=u'groups(name,email),nextPageToken')
    if len(groups) > 0:
      print u'Groups: (%s)' % len(groups)
      for group in groups:
        print u'   %s <%s>' % (group[u'name'], group[u'email'])
  if getLicenses:
    print u'Licenses:'
    lic = buildGAPIObject(u'licensing')
    lbatch = lic.new_batch_http_request(callback=user_lic_result)
    user_licenses = []
    for sku in skus:
      productId, skuId = getProductAndSKU(sku)
      lbatch.add(lic.licenseAssignments().get(userId=user_email, productId=productId, skuId=skuId, fields=u'skuId'))
    lbatch.execute()
    for user_license in user_licenses:
      print '  %s' % (_formatSKUIdDisplayName(user_license))

def _skuIdToDisplayName(skuId):
  return SKUS[skuId][u'displayName'] if skuId in SKUS else skuId

def _formatSKUIdDisplayName(skuId):
  skuIdDisplay = _skuIdToDisplayName(skuId)
  if skuId == skuIdDisplay:
    return skuId
  return u'{0} ({1})'.format(skuId, skuIdDisplay)

def doGetGroupInfo(group_name=None):
  cd = buildGAPIObject(u'directory')
  gs = buildGAPIObject(u'groupssettings')
  getAliases = getUsers = True
  getGroups = False
  if group_name is None:
    group_name = normalizeEmailAddressOrUID(sys.argv[3])
    i = 4
  else:
    i = 3
  while i < len(sys.argv):
    myarg = sys.argv[i].lower()
    if myarg == u'nousers':
      getUsers = False
      i += 1
    elif myarg == u'noaliases':
      getAliases = False
      i += 1
    elif myarg == u'groups':
      getGroups = True
      i += 1
    elif myarg in [u'nogroups', u'nolicenses', u'nolicences', u'noschemas', u'schemas', u'userview']:
      i += 1
      if myarg == u'schemas':
        i += 1
    else:
      systemErrorExit(2, '%s is not a valid argument for "gam info group"' % myarg)
  basic_info = callGAPI(cd.groups(), u'get', groupKey=group_name)
  settings = {}
  if not GroupIsAbuseOrPostmaster(basic_info[u'email']):
    try:
      settings = callGAPI(gs.groups(), u'get', throw_reasons=[GAPI_AUTH_ERROR], retry_reasons=[u'serviceLimit'],
                          groupUniqueId=basic_info[u'email']) # Use email address retrieved from cd since GS API doesn't support uid
      if settings is None:
        settings = {}
    except GAPI_authError:
      pass
  print u''
  print u'Group Settings:'
  for key, value in basic_info.items():
    if (key in [u'kind', u'etag']) or ((key == u'aliases') and (not getAliases)):
      continue
    if isinstance(value, list):
      print u' %s:' % key
      for val in value:
        print u'  %s' % val
    else:
      print utils.convertUTF8(u' %s: %s' % (key, value))
  for key, value in settings.items():
    if key in [u'kind', u'etag', u'description', u'email', u'name']:
      continue
    elif key == u'maxMessageBytes':
      if value > 1024*1024:
        value = u'%sM' % (value / 1024 / 1024)
      elif value > 1024:
        value = u'%sK' % (value / 1024)
    print u' %s: %s' % (key, value)
  if getGroups:
    groups = callGAPIpages(cd.groups(), u'list', u'groups',
                           userKey=basic_info[u'email'], fields=u'nextPageToken,groups(name,email)')
    if groups:
      print u'Groups: ({0})'.format(len(groups))
      for groupm in groups:
        print u'  %s: %s' % (groupm[u'name'], groupm[u'email'])
  if getUsers:
    members = callGAPIpages(cd.members(), u'list', u'members', groupKey=group_name, fields=u'nextPageToken,members(email,id,role,type)', maxResults=GC_Values[GC_MEMBER_MAX_RESULTS])
    print u'Members:'
    for member in members:
      print u' %s: %s (%s)' % (member.get(u'role', ROLE_MEMBER).lower(), member.get(u'email', member[u'id']), member[u'type'].lower())
    print u'Total %s users in group' % len(members)

def doGetAliasInfo(alias_email=None):
  cd = buildGAPIObject(u'directory')
  if alias_email is None:
    alias_email = normalizeEmailAddressOrUID(sys.argv[3])
  try:
    result = callGAPI(cd.users(), u'get', throw_reasons=[GAPI_INVALID, GAPI_BAD_REQUEST], userKey=alias_email)
  except (GAPI_invalid, GAPI_badRequest):
    result = callGAPI(cd.groups(), u'get', groupKey=alias_email)
  print u' Alias Email: %s' % alias_email
  try:
    if result[u'primaryEmail'].lower() == alias_email.lower():
      systemErrorExit(3, '%s is a primary user email address, not an alias.' % alias_email)
    print u' User Email: %s' % result[u'primaryEmail']
  except KeyError:
    print u' Group Email: %s' % result[u'email']
  print u' Unique ID: %s' % result[u'id']

def doGetResourceCalendarInfo():
  cd = buildGAPIObject(u'directory')
  resId = sys.argv[3]
  resource = callGAPI(cd.resources().calendars(), u'get',
                      customer=GC_Values[GC_CUSTOMER_ID], calendarResourceId=resId)
  if u'featureInstances' in resource:
    resource[u'features'] = u', '.join([a_feature[u'feature'][u'name'] for a_feature in resource.pop(u'featureInstances')])
  if u'buildingId' in resource:
    resource[u'buildingName'] = _getBuildingNameById(cd, resource[u'buildingId'])
    resource[u'buildingId'] = u'id:{0}'.format(resource[u'buildingId'])
  print_json(None, resource)

def _filterTimeRanges(activeTimeRanges, startDate, endDate):
  if startDate is None and endDate is None:
    return activeTimeRanges
  filteredTimeRanges = []
  for timeRange in activeTimeRanges:
    activityDate = datetime.datetime.strptime(timeRange[u'date'], YYYYMMDD_FORMAT)
    if ((startDate is None) or (activityDate >= startDate)) and ((endDate is None) or (activityDate <= endDate)):
      filteredTimeRanges.append(timeRange)
  return filteredTimeRanges

def _filterDeviceFiles(deviceFiles, startTime, endTime):
  if startTime is None and endTime is None:
    return deviceFiles
  filteredDeviceFiles = []
  for deviceFile in deviceFiles:
    createTime = datetime.datetime.strptime(deviceFile[u'createTime'], u'%Y-%m-%dT%H:%M:%S.%fZ')
    if ((startTime is None) or (createTime >= startTime)) and ((endTime is None) or (createTime <= endTime)):
      filteredDeviceFiles.append(deviceFile)
  return filteredDeviceFiles

def _getFilterDate(dateStr):
  return datetime.datetime.strptime(dateStr, YYYYMMDD_FORMAT)

def doGetCrosInfo():
  cd = buildGAPIObject(u'directory')
  deviceId = sys.argv[3]
  if deviceId[:6].lower() == u'query:':
    query = deviceId[6:]
    if query[:12].lower() == u'orgunitpath:':
      kwargs = {u'orgUnitPath': query[12:]}
    else:
      kwargs = {u'query': query}
    devices_result = callGAPIpages(cd.chromeosdevices(), u'list', u'chromeosdevices',
                                   customerId=GC_Values[GC_CUSTOMER_ID], fields=u'chromeosdevices/deviceId,nextPageToken', **kwargs)
    devices = list()
    for a_device in devices_result:
      devices.append(a_device[u'deviceId'])
  else:
    devices = [deviceId,]
  downloadfile = None
  targetFolder = GC_Values[GC_DRIVE_DIR]
  projection = None
  fieldsList = []
  noLists = False
  startDate = endDate = None
  listLimit = 0
  i = 4
  while i < len(sys.argv):
    myarg = sys.argv[i].lower().replace(u'_', u'')
    if myarg == u'nolists':
      noLists = True
      i += 1
    elif myarg in CROS_START_ARGUMENTS:
      startDate = _getFilterDate(sys.argv[i+1])
      i += 2
    elif myarg in CROS_END_ARGUMENTS:
      endDate = _getFilterDate(sys.argv[i+1])
      i += 2
    elif myarg == u'listlimit':
      listLimit = int(sys.argv[i+1])
      i += 2
    elif myarg == u'allfields':
      projection = u'FULL'
      fieldsList = []
      i += 1
    elif myarg in PROJECTION_CHOICES_MAP:
      projection = PROJECTION_CHOICES_MAP[myarg]
      if projection == u'FULL':
        fieldsList = []
      else:
        fieldsList = CROS_BASIC_FIELDS_LIST[:]
      i += 1
    elif myarg in CROS_ARGUMENT_TO_PROPERTY_MAP:
      if not fieldsList:
        fieldsList = [u'deviceId',]
      fieldsList.extend(CROS_ARGUMENT_TO_PROPERTY_MAP[myarg])
      i += 1
    elif myarg == u'fields':
      if not fieldsList:
        fieldsList = [u'deviceId',]
      fieldNameList = sys.argv[i+1]
      for field in fieldNameList.lower().replace(u',', u' ').split():
        if field in CROS_ARGUMENT_TO_PROPERTY_MAP:
          fieldsList.extend(CROS_ARGUMENT_TO_PROPERTY_MAP[field])
          if field in CROS_ACTIVE_TIME_RANGES_ARGUMENTS+CROS_DEVICE_FILES_ARGUMENTS+CROS_RECENT_USERS_ARGUMENTS:
            projection = u'FULL'
            noLists = False
        else:
          systemErrorExit(2, '%s is not a valid argument for "gam info cros fields"' % field)
      i += 2
    elif myarg == u'downloadfile':
      downloadfile = sys.argv[i+1]
      if downloadfile.lower() == u'latest':
        downloadfile = downloadfile.lower()
      i += 2
    elif myarg == u'targetfolder':
      targetFolder = os.path.expanduser(sys.argv[i+1])
      if not os.path.isdir(targetFolder):
        os.makedirs(targetFolder)
      i += 2
    else:
      systemErrorExit(2, '%s is not a valid argument for "gam info cros"' % sys.argv[i])
  if fieldsList:
    fields = u','.join(set(fieldsList)).replace(u'.', u'/')
  else:
    fields = None
  i = 0
  device_count = len(devices)
  for deviceId in devices:
    i += 1
    cros = callGAPI(cd.chromeosdevices(), u'get', customerId=GC_Values[GC_CUSTOMER_ID],
                    deviceId=deviceId, projection=projection, fields=fields)
    print u'CrOS Device: {0} ({1} of {2})'.format(deviceId, i, device_count)
    if u'notes' in cros:
      cros[u'notes'] = cros[u'notes'].replace(u'\n', u'\\n')
    cros = _checkTPMVulnerability(cros)
    for up in CROS_SCALAR_PROPERTY_PRINT_ORDER:
      if up in cros:
        if isinstance(cros[up], basestring):
          print u'  {0}: {1}'.format(up, cros[up])
        else:
          sys.stdout.write(u'  %s:' % up)
          print_json(None, cros[up], u'  ')
    if not noLists:
      activeTimeRanges = _filterTimeRanges(cros.get(u'activeTimeRanges', []), startDate, endDate)
      lenATR = len(activeTimeRanges)
      if lenATR:
        print u'  activeTimeRanges'
        for activeTimeRange in activeTimeRanges[:min(lenATR, listLimit or lenATR)]:
          print u'    date: {0}'.format(activeTimeRange[u'date'])
          print u'      activeTime: {0}'.format(str(activeTimeRange[u'activeTime']))
          print u'      duration: {0}'.format(utils.formatMilliSeconds(activeTimeRange[u'activeTime']))
          print u'      minutes: {0}'.format(activeTimeRange[u'activeTime']/60000)
      recentUsers = cros.get(u'recentUsers', [])
      lenRU = len(recentUsers)
      if lenRU:
        print u'  recentUsers'
        for recentUser in recentUsers[:min(lenRU, listLimit or lenRU)]:
          print u'    type: {0}'.format(recentUser[u'type'])
          print u'      email: {0}'.format(recentUser.get(u'email', [u'Unknown', u'UnmanagedUser'][recentUser[u'type'] == u'USER_TYPE_UNMANAGED']))
      deviceFiles = _filterDeviceFiles(cros.get(u'deviceFiles', []), startDate, endDate)
      lenDF = len(deviceFiles)
      if lenDF:
        print u'  deviceFiles'
        for deviceFile in deviceFiles[:min(lenDF, listLimit or lenDF)]:
          print u'    {0}: {1}'.format(deviceFile[u'type'], deviceFile[u'createTime'])
      if downloadfile:
        deviceFiles = cros.get(u'deviceFiles', [])
        lenDF = len(deviceFiles)
        if lenDF:
          if downloadfile == u'latest':
            deviceFile = deviceFiles[-1]
          else:
            for deviceFile in deviceFiles:
              if deviceFile[u'createTime'] == downloadfile:
                break
            else:
              print u'ERROR: file {0} not available to download.'.format(downloadfile)
              deviceFile = None
          if deviceFile:
            downloadfilename = os.path.join(targetFolder, u'cros-logs-{0}-{1}.zip'.format(deviceId, deviceFile[u'createTime']))
            _, content = cd._http.request(deviceFile[u'downloadUrl'])
            writeFile(downloadfilename, content, continueOnError=True)
            print u'Downloaded: {0}'.format(downloadfilename)
        elif downloadfile:
          print u'ERROR: no files to download.'

def doGetMobileInfo():
  cd = buildGAPIObject(u'directory')
  deviceId = sys.argv[3]
  info = callGAPI(cd.mobiledevices(), u'get', customerId=GC_Values[GC_CUSTOMER_ID], resourceId=deviceId)
  print_json(None, info)

def print_json(object_name, object_value, spacing=u''):
  if object_name in [u'kind', u'etag', u'etags']:
    return
  if object_name is not None:
    sys.stdout.write(u'%s%s: ' % (spacing, object_name))
  if isinstance(object_value, list):
    if len(object_value) == 1 and isinstance(object_value[0], (str, unicode, int, bool)):
      sys.stdout.write(utils.convertUTF8(u'%s\n' % object_value[0]))
      return
    if object_name is not None:
      sys.stdout.write(u'\n')
    for a_value in object_value:
      if isinstance(a_value, (str, unicode, int, bool)):
        sys.stdout.write(utils.convertUTF8(u' %s%s\n' % (spacing, a_value)))
      else:
        print_json(None, a_value, u' %s' % spacing)
  elif isinstance(object_value, dict):
    print
    if object_name is not None:
      sys.stdout.write(u'\n')
    for another_object in object_value:
      print_json(another_object, object_value[another_object], u' %s' % spacing)
  else:
    sys.stdout.write(utils.convertUTF8(u'%s\n' % (object_value)))

def doUpdateNotification():
  cd = buildGAPIObject(u'directory')
  ids = list()
  get_all = False
  i = 3
  isUnread = None
  while i < len(sys.argv):
    myarg = sys.argv[i].lower()
    if myarg == u'unread':
      isUnread = True
      mark_as = u'unread'
      i += 1
    elif myarg == u'read':
      isUnread = False
      mark_as = u'read'
      i += 1
    elif myarg == u'id':
      if sys.argv[i+1].lower() == u'all':
        get_all = True
      else:
        ids.append(sys.argv[i+1])
      i += 2
    else:
      systemErrorExit(2, '%s is not a valid argument for "gam update notification"' % sys.argv[i])
  if isUnread is None:
    systemErrorExit(2, 'notifications need to be marked as read or unread.')
  if get_all:
    notifications = callGAPIpages(cd.notifications(), u'list', u'items', customer=GC_Values[GC_CUSTOMER_ID], fields=u'items(notificationId,isUnread),nextPageToken')
    for noti in notifications:
      if noti[u'isUnread'] != isUnread:
        ids.append(noti[u'notificationId'])
  print u'Marking %s notification(s) as %s...' % (len(ids), mark_as)
  for notificationId in ids:
    result = callGAPI(cd.notifications(), u'update', customer=GC_Values[GC_CUSTOMER_ID], notificationId=notificationId, body={u'isUnread': isUnread}, fields=u'notificationId,isUnread')
    if result[u'isUnread']:
      read_result = u'unread'
    else:
      read_result = u'read'
    print u'marked %s as %s' % (result[u'notificationId'], read_result)

def doDeleteNotification():
  cd = buildGAPIObject(u'directory')
  ids = list()
  get_all = False
  i = 3
  while i < len(sys.argv):
    myarg = sys.argv[i].lower()
    if myarg == u'id':
      if sys.argv[i+1].lower() == u'all':
        get_all = True
      else:
        ids.append(sys.argv[i+1])
      i += 2
    else:
      systemErrorExit(2, '%s is not a valid argument for "gam delete notification", expected id' % sys.argv[i])
  if get_all:
    notifications = callGAPIpages(cd.notifications(), u'list', u'items', customer=GC_Values[GC_CUSTOMER_ID], fields=u'items(notificationId),nextPageToken')
    for noti in notifications:
      ids.append(noti[u'notificationId'])
  print u'Deleting %s notification(s)...' % len(ids)
  for notificationId in ids:
    callGAPI(cd.notifications(), u'delete', customer=GC_Values[GC_CUSTOMER_ID], notificationId=notificationId)
    print u'deleted %s' % id

def doSiteVerifyShow():
  verif = buildGAPIObject(u'siteVerification')
  a_domain = sys.argv[3]
  txt_record = callGAPI(verif.webResource(), u'getToken', body={u'site':{u'type':u'INET_DOMAIN', u'identifier':a_domain}, u'verificationMethod':u'DNS_TXT'})
  print u'TXT Record Name:   %s' % a_domain
  print u'TXT Record Value:  %s' % txt_record[u'token']
  print
  cname_record = callGAPI(verif.webResource(), u'getToken', body={u'site':{u'type':u'INET_DOMAIN', u'identifier':a_domain}, u'verificationMethod':u'DNS_CNAME'})
  cname_token = cname_record[u'token']
  cname_list = cname_token.split(u' ')
  cname_subdomain = cname_list[0]
  cname_value = cname_list[1]
  print u'CNAME Record Name:   %s.%s' % (cname_subdomain, a_domain)
  print u'CNAME Record Value:  %s' % cname_value
  print u''
  webserver_file_record = callGAPI(verif.webResource(), u'getToken', body={u'site':{u'type':u'SITE', u'identifier':u'http://%s/' % a_domain}, u'verificationMethod':u'FILE'})
  webserver_file_token = webserver_file_record[u'token']
  print u'Saving web server verification file to: %s' % webserver_file_token
  writeFile(webserver_file_token, u'google-site-verification: {0}'.format(webserver_file_token), continueOnError=True)
  print u'Verification File URL: http://%s/%s' % (a_domain, webserver_file_token)
  print
  webserver_meta_record = callGAPI(verif.webResource(), u'getToken', body={u'site':{u'type':u'SITE', u'identifier':u'http://%s/' % a_domain}, u'verificationMethod':u'META'})
  print u'Meta URL:               http://%s/' % a_domain
  print u'Meta HTML Header Data:  %s' % webserver_meta_record[u'token']
  print

def doGetSiteVerifications():
  verif = buildGAPIObject(u'siteVerification')
  sites = callGAPIitems(verif.webResource(), u'list', u'items')
  if len(sites) > 0:
    for site in sites:
      print u'Site: %s' % site[u'site'][u'identifier']
      print u'Type: %s' % site[u'site'][u'type']
      print u'Owners:'
      for owner in site[u'owners']:
        print u' %s' % owner
      print
  else:
    print u'No Sites Verified.'

def doSiteVerifyAttempt():
  verif = buildGAPIObject(u'siteVerification')
  a_domain = sys.argv[3]
  verificationMethod = sys.argv[4].upper()
  if verificationMethod == u'CNAME':
    verificationMethod = u'DNS_CNAME'
  elif verificationMethod in [u'TXT', u'TEXT']:
    verificationMethod = u'DNS_TXT'
  if verificationMethod in [u'DNS_TXT', u'DNS_CNAME']:
    verify_type = u'INET_DOMAIN'
    identifier = a_domain
  else:
    verify_type = u'SITE'
    identifier = u'http://%s/' % a_domain
  body = {u'site':{u'type':verify_type, u'identifier':identifier}, u'verificationMethod':verificationMethod}
  try:
    verify_result = callGAPI(verif.webResource(), u'insert', throw_reasons=[GAPI_BAD_REQUEST], verificationMethod=verificationMethod, body=body)
  except GAPI_badRequest as e:
    print u'ERROR: %s' % str(e)
    verify_data = callGAPI(verif.webResource(), u'getToken', body=body)
    print u'Method:  %s' % verify_data[u'method']
    print u'Token:      %s' % verify_data[u'token']
    if verify_data[u'method'] == u'DNS_CNAME':
      try:
        import dns.resolver
        resolver = dns.resolver.Resolver()
        resolver.nameservers = [u'8.8.8.8', u'8.8.4.4']
        cname_token = verify_data[u'token']
        cname_list = cname_token.split(u' ')
        cname_subdomain = cname_list[0]
        try:
          answers = resolver.query(u'%s.%s' % (cname_subdomain, a_domain), u'A')
          for answer in answers:
            print u'DNS Record: %s' % answer
        except (dns.resolver.NXDOMAIN, dns.resolver.NoAnswer):
          print u'ERROR: No such domain found in DNS!'
      except ImportError:
        pass
    elif verify_data[u'method'] == u'DNS_TXT':
      try:
        import dns.resolver
        resolver = dns.resolver.Resolver()
        resolver.nameservers = [u'8.8.8.8', u'8.8.4.4']
        try:
          answers = resolver.query(a_domain, u'TXT')
          for answer in answers:
            print u'DNS Record: %s' % str(answer).replace(u'"', u'')
        except dns.resolver.NXDOMAIN:
          print u'ERROR: no such domain found in DNS!'
      except ImportError:
        pass
    return
  print u'SUCCESS!'
  print u'Verified:  %s' % verify_result[u'site'][u'identifier']
  print u'ID:  %s' % verify_result[u'id']
  print u'Type: %s' % verify_result[u'site'][u'type']
  print u'All Owners:'
  try:
    for owner in verify_result[u'owners']:
      print u' %s' % owner
  except KeyError:
    pass
  print
  print u'You can now add %s or it\'s subdomains as secondary or domain aliases of the %s G Suite Account.' % (a_domain, GC_Values[GC_DOMAIN])

def doGetNotifications():
  cd = buildGAPIObject(u'directory')
  i = 3
  unread_only = False
  while i < len(sys.argv):
    myarg = sys.argv[i].lower()
    if myarg == u'unreadonly':
      unread_only = True
    else:
      systemErrorExit(2, '%s is not a valid argument for "gam info notification", expected unreadonly' % sys.argv[i])
    i += 1
  notifications = callGAPIpages(cd.notifications(), u'list', u'items', customer=GC_Values[GC_CUSTOMER_ID])
  for notification in notifications:
    if unread_only and not notification[u'isUnread']:
      continue
    print u'From: %s' % notification[u'fromAddress']
    print u'Subject: %s' % notification[u'subject']
    print u'Date: %s' % notification[u'sendTime']
    print u'ID: %s' % notification[u'notificationId']
    print u'Read Status: %s' % ([u'READ', u'UNREAD'][notification[u'isUnread']])
    print u''
    print utils.convertUTF8(utils.dehtml(notification[u'body']))
    print u''
    print u'--------------'
    print u''

def orgUnitPathQuery(path):
  if path != u'/':
    return u"orgUnitPath='{0}'".format(path.replace(u"'", u"\\'"))
  return None

def getTopLevelOrgId(cd, orgUnitPath):
  try:
    # create a temp org so we can learn what the top level org ID is (sigh)
    temp_org = callGAPI(cd.orgunits(), u'insert', customerId=GC_Values[GC_CUSTOMER_ID],
                        body={u'name': u'temp-delete-me', u'parentOrgUnitPath': orgUnitPath},
                        fields=u'parentOrgUnitId,orgUnitId')
    callGAPI(cd.orgunits(), u'delete', customerId=GC_Values[GC_CUSTOMER_ID], orgUnitPath=temp_org[u'orgUnitId'])
    return temp_org[u'parentOrgUnitId']
  except:
    pass
  return None

def doGetOrgInfo(name=None, return_attrib=None):
  cd = buildGAPIObject(u'directory')
  if not name:
    name = sys.argv[3]
    get_users = True
    show_children = False
    i = 4
    while i < len(sys.argv):
      myarg = sys.argv[i].lower()
      if myarg == u'nousers':
        get_users = False
        i += 1
      elif myarg in [u'children', u'child']:
        show_children = True
        i += 1
      else:
        systemErrorExit(2, '%s is not a valid argument for "gam info org"' % sys.argv[i])
  if name == u'/':
    orgs = callGAPI(cd.orgunits(), u'list',
                    customerId=GC_Values[GC_CUSTOMER_ID], type=u'children',
                    fields=u'organizationUnits/parentOrgUnitId')
    if u'organizationUnits' in orgs and orgs[u'organizationUnits']:
      name = orgs[u'organizationUnits'][0][u'parentOrgUnitId']
    else:
      topLevelOrgId = getTopLevelOrgId(cd, u'/')
      if topLevelOrgId:
        name = topLevelOrgId
  if len(name) > 1 and name[0] == u'/':
    name = name[1:]
  result = callGAPI(cd.orgunits(), u'get', customerId=GC_Values[GC_CUSTOMER_ID], orgUnitPath=name)
  if return_attrib:
    return result[return_attrib]
  print_json(None, result)
  if get_users:
    name = result[u'orgUnitPath']
    print u'Users: '
    page_message = u'Got %%total_items%% users: %%first_item%% - %%last_item%%\n'
    users = callGAPIpages(cd.users(), u'list', u'users', page_message=page_message,
                          message_attribute=u'primaryEmail', customer=GC_Values[GC_CUSTOMER_ID], query=orgUnitPathQuery(name),
                          fields=u'users(primaryEmail,orgUnitPath),nextPageToken', maxResults=GC_Values[GC_USER_MAX_RESULTS])
    for user in users:
      if show_children or (name.lower() == user[u'orgUnitPath'].lower()):
        sys.stdout.write(u' %s' % user[u'primaryEmail'])
        if name.lower() != user[u'orgUnitPath'].lower():
          print u' (child)'
        else:
          print u''

def doGetASPs(users):
  cd = buildGAPIObject(u'directory')
  for user in users:
    asps = callGAPIitems(cd.asps(), u'list', u'items', userKey=user)
    if len(asps) > 0:
      print u'Application-Specific Passwords for %s' % user
      for asp in asps:
        if asp[u'creationTime'] == u'0':
          created_date = u'Unknown'
        else:
          created_date = datetime.datetime.fromtimestamp(int(asp[u'creationTime'])/1000).strftime(u'%Y-%m-%d %H:%M:%S')
        if asp[u'lastTimeUsed'] == u'0':
          used_date = u'Never'
        else:
          used_date = datetime.datetime.fromtimestamp(int(asp[u'lastTimeUsed'])/1000).strftime(u'%Y-%m-%d %H:%M:%S')
        print u' ID: %s\n  Name: %s\n  Created: %s\n  Last Used: %s\n' % (asp[u'codeId'], asp[u'name'], created_date, used_date)
    else:
      print u' no ASPs for %s\n' % user

def doDelASP(users):
  cd = buildGAPIObject(u'directory')
  codeIdList = sys.argv[5].lower()
  if codeIdList == u'all':
    allCodeIds = True
  else:
    allCodeIds = False
    codeIds = codeIdList.replace(u',', u' ').split()
  for user in users:
    if allCodeIds:
      asps = callGAPIitems(cd.asps(), u'list', u'items', userKey=user, fields=u'items/codeId')
      codeIds = [asp[u'codeId'] for asp in asps]
    for codeId in codeIds:
      callGAPI(cd.asps(), u'delete', userKey=user, codeId=codeId)
      print u'deleted ASP %s for %s' % (codeId, user)

def printBackupCodes(user, codes):
  jcount = len(codes)
  realcount = 0
  for code in codes:
    if u'verificationCode' in code and code[u'verificationCode']:
      realcount += 1
  print u'Backup verification codes for {0} ({1})'.format(user, realcount)
  print u''
  if jcount > 0:
    j = 0
    for code in codes:
      j += 1
      print u'{0}. {1}'.format(j, code[u'verificationCode'])
    print u''

def doGetBackupCodes(users):
  cd = buildGAPIObject(u'directory')
  for user in users:
    try:
      codes = callGAPIitems(cd.verificationCodes(), u'list', u'items', throw_reasons=[GAPI_INVALID_ARGUMENT, GAPI_INVALID], userKey=user)
    except (GAPI_invalidArgument, GAPI_invalid):
      codes = []
    printBackupCodes(user, codes)

def doGenBackupCodes(users):
  cd = buildGAPIObject(u'directory')
  for user in users:
    callGAPI(cd.verificationCodes(), u'generate', userKey=user)
    codes = callGAPIitems(cd.verificationCodes(), u'list', u'items', userKey=user)
    printBackupCodes(user, codes)

def doDelBackupCodes(users):
  cd = buildGAPIObject(u'directory')
  for user in users:
    try:
      callGAPI(cd.verificationCodes(), u'invalidate', soft_errors=True, throw_reasons=[GAPI_INVALID], userKey=user)
    except GAPI_invalid:
      print u'No 2SV backup codes for %s' % user
      continue
    print u'2SV backup codes for %s invalidated' % user

def commonClientIds(clientId):
  if clientId == u'gasmo':
    return u'1095133494869.apps.googleusercontent.com'
  return clientId

def doDelTokens(users):
  cd = buildGAPIObject(u'directory')
  clientId = None
  i = 5
  while i < len(sys.argv):
    myarg = sys.argv[i].lower().replace(u'_', '')
    if myarg == u'clientid':
      clientId = commonClientIds(sys.argv[i+1])
      i += 2
    else:
      systemErrorExit(3, '%s is not a valid argument to "gam <users> delete token"' % sys.argv[i])
  if not clientId:
    systemErrorExit(3, 'you must specify a clientid for "gam <users> delete token"')
  for user in users:
    try:
      callGAPI(cd.tokens(), u'get', throw_reasons=[GAPI_NOT_FOUND, GAPI_RESOURCE_NOT_FOUND], userKey=user, clientId=clientId)
    except (GAPI_notFound, GAPI_resourceNotFound):
      print u'User %s did not authorize %s' % (user, clientId)
      continue
    callGAPI(cd.tokens(), u'delete', userKey=user, clientId=clientId)
    print u'Deleted token for %s' % user

def printShowTokens(i, entityType, users, csvFormat):
  def _showToken(token):
    print u'  Client ID: %s' % token[u'clientId']
    for item in token:
      if item not in [u'clientId', u'scopes']:
        print utils.convertUTF8(u'    %s: %s' % (item, token.get(item, u'')))
    item = u'scopes'
    print u'    %s:' % item
    for it in token.get(item, []):
      print u'      %s' % it

  cd = buildGAPIObject(u'directory')
  if csvFormat:
    todrive = False
    titles = [u'user', u'clientId', u'displayText', u'anonymous', u'nativeApp', u'userKey', u'scopes']
    csvRows = []
  clientId = None
  while i < len(sys.argv):
    myarg = sys.argv[i].lower()
    if csvFormat and myarg == u'todrive':
      todrive = True
      i += 1
    elif myarg == u'clientid':
      clientId = commonClientIds(sys.argv[i+1])
      i += 2
    elif not entityType:
      entityType = myarg
      users = getUsersToModify(entity_type=entityType, entity=sys.argv[i+1], silent=False)
      i += 2
    else:
      systemErrorExit(2, '%s is not a valid argument for "gam <users> %s tokens"' % (myarg, [u'show', u'print'][csvFormat]))
  if not entityType:
    users = getUsersToModify(entity_type=u'all', entity=u'users', silent=False)
  fields = u','.join([u'clientId', u'displayText', u'anonymous', u'nativeApp', u'userKey', u'scopes'])
  i = 0
  count = len(users)
  for user in users:
    i += 1
    try:
      if csvFormat:
        sys.stderr.write(u'Getting Access Tokens for %s\n' % (user))
      if clientId:
        results = [callGAPI(cd.tokens(), u'get',
                            throw_reasons=[GAPI_NOT_FOUND, GAPI_USER_NOT_FOUND, GAPI_RESOURCE_NOT_FOUND],
                            userKey=user, clientId=clientId, fields=fields)]
      else:
        results = callGAPIitems(cd.tokens(), u'list', u'items',
                                throw_reasons=[GAPI_USER_NOT_FOUND],
                                userKey=user, fields=u'items({0})'.format(fields))
      jcount = len(results)
      if not csvFormat:
        print u'User: {0}, Access Tokens ({1}/{2})'.format(user, i, count)
        if jcount == 0:
          continue
        for token in results:
          _showToken(token)
      else:
        if jcount == 0:
          continue
        for token in results:
          row = {u'user': user, u'scopes': u' '.join(token.get(u'scopes', []))}
          for item in token:
            if item not in [u'scopes']:
              row[item] = token.get(item, u'')
          csvRows.append(row)
    except (GAPI_notFound, GAPI_userNotFound, GAPI_resourceNotFound):
      pass
  if csvFormat:
    writeCSVfile(csvRows, titles, u'OAuth Tokens', todrive)

def doDeprovUser(users):
  cd = buildGAPIObject(u'directory')
  for user in users:
    print u'Getting Application Specific Passwords for %s' % user
    asps = callGAPIitems(cd.asps(), u'list', u'items', userKey=user, fields=u'items/codeId')
    jcount = len(asps)
    if jcount > 0:
      j = 0
      for asp in asps:
        j += 1
        print u' deleting ASP %s of %s' % (j, jcount)
        callGAPI(cd.asps(), u'delete', userKey=user, codeId=asp[u'codeId'])
    else:
      print u'No ASPs'
    print u'Invalidating 2SV Backup Codes for %s' % user
    try:
      callGAPI(cd.verificationCodes(), u'invalidate', soft_errors=True, throw_reasons=[GAPI_INVALID], userKey=user)
    except GAPI_invalid:
      print u'No 2SV Backup Codes'
    print u'Getting tokens for %s...' % user
    tokens = callGAPIitems(cd.tokens(), u'list', u'items', userKey=user, fields=u'items/clientId')
    jcount = len(tokens)
    if jcount > 0:
      j = 0
      for token in tokens:
        j += 1
        print u' deleting token %s of %s' % (j, jcount)
        callGAPI(cd.tokens(), u'delete', userKey=user, clientId=token[u'clientId'])
    else:
      print u'No Tokens'
    print u'Done deprovisioning %s' % user

def doDeleteUser():
  cd = buildGAPIObject(u'directory')
  user_email = normalizeEmailAddressOrUID(sys.argv[3])
  print u"Deleting account for %s" % (user_email)
  callGAPI(cd.users(), u'delete', userKey=user_email)

def doUndeleteUser():
  cd = buildGAPIObject(u'directory')
  user = normalizeEmailAddressOrUID(sys.argv[3])
  orgUnit = u'/'
  i = 4
  while i < len(sys.argv):
    myarg = sys.argv[i].lower()
    if myarg in [u'ou', u'org']:
      orgUnit = sys.argv[i+1]
      i += 2
    else:
      systemErrorExit(2, '%s is not a valid argument for "gam undelete user"' % sys.argv[i])
  if user.find(u'@') == -1:
    user_uid = user
  else:
    print u'Looking up UID for %s...' % user
    deleted_users = callGAPIpages(cd.users(), u'list', u'users',
                                  customer=GC_Values[GC_CUSTOMER_ID], showDeleted=True, maxResults=GC_Values[GC_USER_MAX_RESULTS])
    matching_users = list()
    for deleted_user in deleted_users:
      if str(deleted_user[u'primaryEmail']).lower() == user:
        matching_users.append(deleted_user)
    if len(matching_users) < 1:
      systemErrorExit(3, 'could not find deleted user with that address.')
    elif len(matching_users) > 1:
      print u'ERROR: more than one matching deleted %s user. Please select the correct one to undelete and specify with "gam undelete user uid:<uid>"' % user
      print u''
      for matching_user in matching_users:
        print u' uid:%s ' % matching_user[u'id']
        for attr_name in [u'creationTime', u'lastLoginTime', u'deletionTime']:
          try:
            if matching_user[attr_name] == NEVER_TIME:
              matching_user[attr_name] = u'Never'
            print u'   %s: %s ' % (attr_name, matching_user[attr_name])
          except KeyError:
            pass
        print
      sys.exit(3)
    else:
      user_uid = matching_users[0][u'id']
  print u"Undeleting account for %s" % user
  callGAPI(cd.users(), u'undelete', userKey=user_uid, body={u'orgUnitPath': orgUnit})

def doDeleteGroup():
  cd = buildGAPIObject(u'directory')
  group = normalizeEmailAddressOrUID(sys.argv[3])
  print u"Deleting group %s" % group
  callGAPI(cd.groups(), u'delete', groupKey=group)

def doDeleteAlias(alias_email=None):
  cd = buildGAPIObject(u'directory')
  is_user = is_group = False
  if alias_email is None:
    alias_email = sys.argv[3]
  if alias_email.lower() == u'user':
    is_user = True
    alias_email = sys.argv[4]
  elif alias_email.lower() == u'group':
    is_group = True
    alias_email = sys.argv[4]
  alias_email = normalizeEmailAddressOrUID(alias_email, noUid=True)
  print u"Deleting alias %s" % alias_email
  if is_user or (not is_user and not is_group):
    try:
      callGAPI(cd.users().aliases(), u'delete', throw_reasons=[GAPI_INVALID, GAPI_BAD_REQUEST, GAPI_NOT_FOUND], userKey=alias_email, alias=alias_email)
      return
    except (GAPI_invalid, GAPI_badRequest):
      pass
    except GAPI_notFound:
      systemErrorExit(4, 'The alias %s does not exist' % alias_email)
  if not is_user or (not is_user and not is_group):
    callGAPI(cd.groups().aliases(), u'delete', groupKey=alias_email, alias=alias_email)

def doDeleteResourceCalendar():
  resId = sys.argv[3]
  cd = buildGAPIObject(u'directory')
  print u"Deleting resource calendar %s" % resId
  callGAPI(cd.resources().calendars(), u'delete',
           customer=GC_Values[GC_CUSTOMER_ID], calendarResourceId=resId)

def doDeleteOrg():
  cd = buildGAPIObject(u'directory')
  name = sys.argv[3]
  if name[0] == u'/':
    name = name[1:]
  print u"Deleting organization %s" % name
  callGAPI(cd.orgunits(), u'delete', customerId=GC_Values[GC_CUSTOMER_ID], orgUnitPath=name)

# Send an email
def send_email(msg_subj, msg_txt, msg_rcpt=None):
  from email.mime.text import MIMEText
  userId, gmail = buildGmailGAPIObject(_getValueFromOAuth(u'email'))
  if not msg_rcpt:
    msg_rcpt = userId
  msg = MIMEText(msg_txt)
  msg[u'Subject'] = msg_subj
  msg[u'From'] = userId
  msg[u'To'] = msg_rcpt
  callGAPI(gmail.users().messages(), u'send',
           userId=userId, body={u'raw': base64.urlsafe_b64encode(msg.as_string())})

# Write a CSV file
def addTitleToCSVfile(title, titles):
  titles.append(title)

def addTitlesToCSVfile(addTitles, titles):
  for title in addTitles:
    if title not in titles:
      addTitleToCSVfile(title, titles)

def addRowTitlesToCSVfile(row, csvRows, titles):
  csvRows.append(row)
  for title in row:
    if title not in titles:
      addTitleToCSVfile(title, titles)

# fieldName is command line argument
# fieldNameMap maps fieldName to API field names; CSV file header will be API field name
#ARGUMENT_TO_PROPERTY_MAP = {
#  u'admincreated': [u'adminCreated'],
#  u'aliases': [u'aliases', u'nonEditableAliases'],
#  }
# fieldsList is the list of API fields
# fieldsTitles maps the API field name to the CSV file header
def addFieldToCSVfile(fieldName, fieldNameMap, fieldsList, fieldsTitles, titles):
  for ftList in fieldNameMap[fieldName]:
    if ftList not in fieldsTitles:
      fieldsList.append(ftList)
      fieldsTitles[ftList] = ftList
      addTitlesToCSVfile([ftList], titles)

# fieldName is command line argument
# fieldNameTitleMap maps fieldName to API field name and CSV file header
#ARGUMENT_TO_PROPERTY_TITLE_MAP = {
#  u'admincreated': [u'adminCreated', u'Admin_Created'],
#  u'aliases': [u'aliases', u'Aliases', u'nonEditableAliases', u'NonEditableAliases'],
#  }
# fieldsList is the list of API fields
# fieldsTitles maps the API field name to the CSV file header
def addFieldTitleToCSVfile(fieldName, fieldNameTitleMap, fieldsList, fieldsTitles, titles):
  ftList = fieldNameTitleMap[fieldName]
  for i in range(0, len(ftList), 2):
    if ftList[i] not in fieldsTitles:
      fieldsList.append(ftList[i])
      fieldsTitles[ftList[i]] = ftList[i+1]
      addTitlesToCSVfile([ftList[i+1]], titles)

def sortCSVTitles(firstTitle, titles):
  restoreTitles = []
  for title in firstTitle:
    if title in titles:
      titles.remove(title)
      restoreTitles.append(title)
  titles.sort()
  for title in restoreTitles[::-1]:
    titles.insert(0, title)

def writeCSVfile(csvRows, titles, list_type, todrive):
  csv.register_dialect(u'nixstdout', lineterminator=u'\n')
  if todrive:
    string_file = StringIO.StringIO()
    writer = csv.DictWriter(string_file, fieldnames=titles, dialect=u'nixstdout', quoting=csv.QUOTE_MINIMAL)
  else:
    writer = csv.DictWriter(sys.stdout, fieldnames=titles, dialect=u'nixstdout', quoting=csv.QUOTE_MINIMAL)
  try:
    writer.writerow(dict((item, item) for item in writer.fieldnames))
    writer.writerows(csvRows)
  except IOError as e:
    systemErrorExit(6, e)
  if todrive:
    columns = len(csvRows[0])
    rows = len(csvRows)
    cell_count = rows * columns
    mimeType = u'application/vnd.google-apps.spreadsheet'
    if cell_count > 2000000 or columns > 256:
      print u'{0}{1}'.format(WARNING_PREFIX, MESSAGE_RESULTS_TOO_LARGE_FOR_GOOGLE_SPREADSHEET)
      mimeType = u'text/csv'
    admin_email = _getValueFromOAuth(u'email')
    _, drive = buildDrive3GAPIObject(admin_email)
    if not drive:
      print u'''\nGAM is not authorized to create Drive files. Please run:

gam user %s check serviceaccount

and follow recommend steps to authorize GAM for Drive access.''' % (admin_email)
      sys.exit(5)
    body = {u'description': u' '.join(sys.argv),
            u'name': u'%s - %s' % (GC_Values[GC_DOMAIN], list_type),
            u'mimeType': mimeType}
    result = callGAPI(drive.files(), u'create', fields=u'webViewLink',
                      body=body,
                      media_body=googleapiclient.http.MediaInMemoryUpload(string_file.getvalue(),
                                                                          mimetype=u'text/csv'))
    file_url = result[u'webViewLink']
    if GC_Values[GC_NO_BROWSER]:
      msg_txt = u'Drive file uploaded to:\n %s' % file_url
      msg_subj = u'%s - %s' % (GC_Values[GC_DOMAIN], list_type)
      send_email(msg_subj, msg_txt)
      print msg_txt
    else:
      import webbrowser
      webbrowser.open(file_url)

def flatten_json(structure, key=u'', path=u'', flattened=None, listLimit=None):
  if flattened is None:
    flattened = {}
  if not isinstance(structure, (dict, list)):
    flattened[((path + u'.') if path else u'') + key] = structure
  elif isinstance(structure, list):
    for i, item in enumerate(structure):
      if listLimit and (i >= listLimit):
        break
      flatten_json(item, u'{0}'.format(i), u'.'.join([item for item in [path, key] if item]), flattened=flattened, listLimit=listLimit)
  else:
    for new_key, value in structure.items():
      if new_key in [u'kind', u'etag']:
        continue
      if value == NEVER_TIME:
        value = u'Never'
      flatten_json(value, new_key, u'.'.join([item for item in [path, key] if item]), flattened=flattened, listLimit=listLimit)
  return flattened

USER_ARGUMENT_TO_PROPERTY_MAP = {
  u'address': [u'addresses',],
  u'addresses': [u'addresses',],
  u'admin': [u'isAdmin', u'isDelegatedAdmin',],
  u'agreed2terms': [u'agreedToTerms',],
  u'agreedtoterms': [u'agreedToTerms',],
  u'aliases': [u'aliases', u'nonEditableAliases',],
  u'changepassword': [u'changePasswordAtNextLogin',],
  u'changepasswordatnextlogin': [u'changePasswordAtNextLogin',],
  u'creationtime': [u'creationTime',],
  u'deletiontime': [u'deletionTime',],
  u'email': [u'emails',],
  u'emails': [u'emails',],
  u'externalid': [u'externalIds',],
  u'externalids': [u'externalIds',],
  u'familyname': [u'name.familyName',],
  u'firstname': [u'name.givenName',],
  u'fullname': [u'name.fullName',],
  u'gal': [u'includeInGlobalAddressList',],
  u'gender': [u'gender.type', u'gender.customGender', u'gender.addressMeAs',],
  u'givenname': [u'name.givenName',],
  u'id': [u'id',],
  u'im': [u'ims',],
  u'ims': [u'ims',],
  u'includeinglobaladdresslist': [u'includeInGlobalAddressList',],
  u'ipwhitelisted': [u'ipWhitelisted',],
  u'isadmin': [u'isAdmin', u'isDelegatedAdmin',],
  u'isdelegatedadmin': [u'isAdmin', u'isDelegatedAdmin',],
  u'isenforcedin2sv': [u'isEnforcedIn2Sv',],
  u'isenrolledin2sv': [u'isEnrolledIn2Sv',],
  u'is2svenforced': [u'isEnforcedIn2Sv',],
  u'is2svenrolled': [u'isEnrolledIn2Sv',],
  u'ismailboxsetup': [u'isMailboxSetup',],
  u'keyword': [u'keywords',],
  u'keywords': [u'keywords',],
  u'language': [u'languages',],
  u'languages': [u'languages',],
  u'lastlogintime': [u'lastLoginTime',],
  u'lastname': [u'name.familyName',],
  u'location': [u'locations',],
  u'locations': [u'locations',],
  u'name': [u'name.givenName', u'name.familyName', u'name.fullName',],
  u'nicknames': [u'aliases', u'nonEditableAliases',],
  u'noneditablealiases': [u'aliases', u'nonEditableAliases',],
  u'note': [u'notes',],
  u'notes': [u'notes',],
  u'org': [u'orgUnitPath',],
  u'organization': [u'organizations',],
  u'organizations': [u'organizations',],
  u'orgunitpath': [u'orgUnitPath',],
  u'otheremail': [u'emails',],
  u'otheremails': [u'emails',],
  u'ou': [u'orgUnitPath',],
  u'phone': [u'phones',],
  u'phones': [u'phones',],
  u'photo': [u'thumbnailPhotoUrl',],
  u'photourl': [u'thumbnailPhotoUrl',],
  u'posix': [u'posixAccounts',],
  u'posixaccounts': [u'posixAccounts',],
  u'primaryemail': [u'primaryEmail',],
  u'relation': [u'relations',],
  u'relations': [u'relations',],
  u'ssh': [u'sshPublicKeys',],
  u'sshkeys': [u'sshPublicKeys',],
  u'sshpublickeys': [u'sshPublicKeys',],
  u'suspended': [u'suspended', u'suspensionReason',],
  u'thumbnailphotourl': [u'thumbnailPhotoUrl',],
  u'username': [u'primaryEmail',],
  u'website': [u'websites',],
  u'websites': [u'websites',],
  }

def doPrintUsers():
  cd = buildGAPIObject(u'directory')
  todrive = False
  fieldsList = []
  fieldsTitles = {}
  titles = []
  csvRows = []
  addFieldToCSVfile(u'primaryemail', USER_ARGUMENT_TO_PROPERTY_MAP, fieldsList, fieldsTitles, titles)
  customer = GC_Values[GC_CUSTOMER_ID]
  domain = None
  query = None
  projection = u'basic'
  customFieldMask = None
  sortHeaders = getGroupFeed = getLicenseFeed = email_parts = False
  viewType = deleted_only = orderBy = sortOrder = None
  groupDelimiter = u' '
  licenseDelimiter = u','
  i = 3
  while i < len(sys.argv):
    myarg = sys.argv[i].lower().replace(u'_', u'')
    if myarg in PROJECTION_CHOICES_MAP:
      projection = myarg
      sortHeaders = True
      fieldsList = []
      i += 1
    elif myarg == u'allfields':
      projection = u'basic'
      sortHeaders = True
      fieldsList = []
      i += 1
    elif myarg == u'delimiter':
      groupDelimiter = licenseDelimiter = sys.argv[i+1]
      i += 2
    elif myarg == u'sortheaders':
      sortHeaders = True
      i += 1
    elif myarg in [u'custom', u'schemas']:
      fieldsList.append(u'customSchemas')
      if sys.argv[i+1].lower() == u'all':
        projection = u'full'
      else:
        projection = u'custom'
        customFieldMask = sys.argv[i+1]
      i += 2
    elif myarg == u'todrive':
      todrive = True
      i += 1
    elif myarg in [u'deletedonly', u'onlydeleted']:
      deleted_only = True
      i += 1
    elif myarg == u'orderby':
      orderBy = sys.argv[i+1]
      if orderBy.lower() not in [u'email', u'familyname', u'givenname', u'firstname', u'lastname']:
        systemErrorExit(2, 'orderby must be one of email, familyName, givenName; got %s' % orderBy)
      elif orderBy.lower() in [u'familyname', u'lastname']:
        orderBy = u'familyName'
      elif orderBy.lower() in [u'givenname', u'firstname']:
        orderBy = u'givenName'
      i += 2
    elif myarg == u'userview':
      viewType = u'domain_public'
      i += 1
    elif myarg in SORTORDER_CHOICES_MAP:
      sortOrder = SORTORDER_CHOICES_MAP[myarg]
      i += 1
    elif myarg == u'domain':
      domain = sys.argv[i+1]
      customer = None
      i += 2
    elif myarg == u'query':
      query = sys.argv[i+1]
      i += 2
    elif myarg in USER_ARGUMENT_TO_PROPERTY_MAP:
      if not fieldsList:
        fieldsList = [u'primaryEmail',]
      addFieldToCSVfile(myarg, USER_ARGUMENT_TO_PROPERTY_MAP, fieldsList, fieldsTitles, titles)
      i += 1
    elif myarg == u'fields':
      if not fieldsList:
        fieldsList = [u'primaryEmail',]
      fieldNameList = sys.argv[i+1]
      for field in fieldNameList.lower().replace(u',', u' ').split():
        if field in USER_ARGUMENT_TO_PROPERTY_MAP:
          addFieldToCSVfile(field, USER_ARGUMENT_TO_PROPERTY_MAP, fieldsList, fieldsTitles, titles)
        else:
          systemErrorExit(2, '%s is not a valid argument for "gam print users fields"' % field)
      i += 2
    elif myarg == u'groups':
      getGroupFeed = True
      i += 1
    elif myarg in [u'license', u'licenses', u'licence', u'licences']:
      getLicenseFeed = True
      i += 1
    elif myarg in [u'emailpart', u'emailparts', u'username']:
      email_parts = True
      i += 1
    else:
      systemErrorExit(2, '%s is not a valid argument for "gam print users"' % sys.argv[i])
  if fieldsList:
    fields = u'nextPageToken,users(%s)' % u','.join(set(fieldsList)).replace(u'.', u'/')
  else:
    fields = None
  sys.stderr.write(u"Getting all users in G Suite account (may take some time on a large account)...\n")
  page_message = u'Got %%total_items%% users: %%first_item%% - %%last_item%%\n'
  all_users = callGAPIpages(cd.users(), u'list', u'users', page_message=page_message,
                            message_attribute=u'primaryEmail', customer=customer, domain=domain, fields=fields,
                            showDeleted=deleted_only, orderBy=orderBy, sortOrder=sortOrder, viewType=viewType,
                            query=query, projection=projection, customFieldMask=customFieldMask, maxResults=GC_Values[GC_USER_MAX_RESULTS])
  for user in all_users:
    if email_parts and (u'primaryEmail' in user):
      user_email = user[u'primaryEmail']
      if user_email.find(u'@') != -1:
        user[u'primaryEmailLocal'], user[u'primaryEmailDomain'] = splitEmailAddress(user_email)
    addRowTitlesToCSVfile(flatten_json(user), csvRows, titles)
  if sortHeaders:
    sortCSVTitles([u'primaryEmail',], titles)
  if getGroupFeed:
    total_users = len(csvRows)
    user_count = 1
    titles.append(u'Groups')
    for user in csvRows:
      user_email = user[u'primaryEmail']
      sys.stderr.write(u"Getting Group Membership for %s (%s/%s)\r\n" % (user_email, user_count, total_users))
      groups = callGAPIpages(cd.groups(), u'list', u'groups', userKey=user_email)
      user[u'Groups'] = groupDelimiter.join([groupname[u'email'] for groupname in groups])
      user_count += 1
  if getLicenseFeed:
    titles.append(u'Licenses')
    licenses = doPrintLicenses(returnFields=u'userId,skuId')
    if licenses:
      for user in csvRows:
        u_licenses = licenses.get(user[u'primaryEmail'].lower())
        if u_licenses:
          user[u'Licenses'] = licenseDelimiter.join([_skuIdToDisplayName(skuId) for skuId in u_licenses])
  writeCSVfile(csvRows, titles, u'Users', todrive)

GROUP_ARGUMENT_TO_PROPERTY_TITLE_MAP = {
  u'admincreated': [u'adminCreated', u'Admin_Created'],
  u'aliases': [u'aliases', u'Aliases', u'nonEditableAliases', u'NonEditableAliases'],
  u'description': [u'description', u'Description'],
  u'directmemberscount': [u'directMembersCount', u'DirectMembersCount'],
  u'email': [u'email', u'Email'],
  u'id': [u'id', u'ID'],
  u'name': [u'name', u'Name'],
  }

GROUP_ATTRIBUTES_ARGUMENT_TO_PROPERTY_MAP = {
  u'allowexternalmembers': u'allowExternalMembers',
  u'allowgooglecommunication': u'allowGoogleCommunication',
  u'allowwebposting': u'allowWebPosting',
  u'archiveonly': u'archiveOnly',
  u'customfootertext': u'customFooterText',
  u'customreplyto': u'customReplyTo',
  u'defaultmessagedenynotificationtext': u'defaultMessageDenyNotificationText',
  u'gal': u'includeInGlobalAddressList',
  u'includecustomfooter': u'includeCustomFooter',
  u'includeinglobaladdresslist': u'includeInGlobalAddressList',
  u'isarchived': u'isArchived',
  u'maxmessagebytes': u'maxMessageBytes',
  u'memberscanpostasthegroup': u'membersCanPostAsTheGroup',
  u'messagedisplayfont': u'messageDisplayFont',
  u'messagemoderationlevel': u'messageModerationLevel',
  u'primarylanguage': u'primaryLanguage',
  u'replyto': u'replyTo',
  u'sendmessagedenynotification': u'sendMessageDenyNotification',
  u'showingroupdirectory': u'showInGroupDirectory',
  u'spammoderationlevel': u'spamModerationLevel',
  u'whocanadd': u'whoCanAdd',
  u'whocancontactowner': u'whoCanContactOwner',
  u'whocaninvite': u'whoCanInvite',
  u'whocanjoin': u'whoCanJoin',
  u'whocanleavegroup': u'whoCanLeaveGroup',
  u'whocanpostmessage': u'whoCanPostMessage',
  u'whocanviewgroup': u'whoCanViewGroup',
  u'whocanviewmembership': u'whoCanViewMembership',
  }

def doPrintGroups():
  cd = buildGAPIObject(u'directory')
  i = 3
  members = membersCountOnly = managers = managersCountOnly = owners = ownersCountOnly = False
  customer = GC_Values[GC_CUSTOMER_ID]
  usedomain = usemember = None
  aliasDelimiter = u' '
  memberDelimiter = u'\n'
  todrive = False
  cdfieldsList = []
  gsfieldsList = []
  fieldsTitles = {}
  titles = []
  csvRows = []
  addFieldTitleToCSVfile(u'email', GROUP_ARGUMENT_TO_PROPERTY_TITLE_MAP, cdfieldsList, fieldsTitles, titles)
  maxResults = None
  roles = []
  getSettings = sortHeaders = False
  while i < len(sys.argv):
    myarg = sys.argv[i].lower()
    if myarg == u'todrive':
      todrive = True
      i += 1
    elif myarg == u'domain':
      usedomain = sys.argv[i+1].lower()
      customer = None
      i += 2
    elif myarg == u'member':
      usemember = normalizeEmailAddressOrUID(sys.argv[i+1])
      customer = None
      i += 2
    elif myarg == u'maxresults':
      maxResults = int(sys.argv[i+1])
      i += 2
    elif myarg == u'delimiter':
      aliasDelimiter = memberDelimiter = sys.argv[i+1]
      i += 2
    elif myarg in GROUP_ARGUMENT_TO_PROPERTY_TITLE_MAP:
      addFieldTitleToCSVfile(myarg, GROUP_ARGUMENT_TO_PROPERTY_TITLE_MAP, cdfieldsList, fieldsTitles, titles)
      i += 1
    elif myarg == u'settings':
      getSettings = True
      i += 1
    elif myarg == u'allfields':
      getSettings = sortHeaders = True
      cdfieldsList = []
      gsfieldsList = []
      fieldsTitles = {}
      for field in GROUP_ARGUMENT_TO_PROPERTY_TITLE_MAP:
        addFieldTitleToCSVfile(field, GROUP_ARGUMENT_TO_PROPERTY_TITLE_MAP, cdfieldsList, fieldsTitles, titles)
      i += 1
    elif myarg == u'sortheaders':
      sortHeaders = True
      i += 1
    elif myarg == u'fields':
      fieldNameList = sys.argv[i+1]
      for field in fieldNameList.lower().replace(u',', u' ').split():
        if field in GROUP_ARGUMENT_TO_PROPERTY_TITLE_MAP:
          addFieldTitleToCSVfile(field, GROUP_ARGUMENT_TO_PROPERTY_TITLE_MAP, cdfieldsList, fieldsTitles, titles)
        elif field in GROUP_ATTRIBUTES_ARGUMENT_TO_PROPERTY_MAP:
          addFieldToCSVfile(field, {field: [GROUP_ATTRIBUTES_ARGUMENT_TO_PROPERTY_MAP[field]]}, gsfieldsList, fieldsTitles, titles)
          gsfieldsList.extend([GROUP_ATTRIBUTES_ARGUMENT_TO_PROPERTY_MAP[field],])
        else:
          systemErrorExit(2, '%s is not a valid argument for "gam print groups fields"' % field)
      i += 2
    elif myarg in [u'members', u'memberscount']:
      roles.append(ROLE_MEMBER)
      members = True
      if myarg == u'memberscount':
        membersCountOnly = True
      i += 1
    elif myarg in [u'owners', u'ownerscount']:
      roles.append(ROLE_OWNER)
      owners = True
      if myarg == u'ownerscount':
        ownersCountOnly = True
      i += 1
    elif myarg in [u'managers', u'managerscount']:
      roles.append(ROLE_MANAGER)
      managers = True
      if myarg == u'managerscount':
        managersCountOnly = True
      i += 1
    else:
      systemErrorExit(2, '%s is not a valid argument for "gam print groups"' % sys.argv[i])
  cdfields = u','.join(set(cdfieldsList))
  if len(gsfieldsList) > 0:
    getSettings = True
    gsfields = u','.join(set(gsfieldsList))
  elif getSettings:
    gsfields = None
  if getSettings:
    gs = buildGAPIObject(u'groupssettings')
  roles = u','.join(sorted(set(roles)))
  if roles:
    if members:
      addTitlesToCSVfile([u'MembersCount',], titles)
      if not membersCountOnly:
        addTitlesToCSVfile([u'Members',], titles)
    if managers:
      addTitlesToCSVfile([u'ManagersCount',], titles)
      if not managersCountOnly:
        addTitlesToCSVfile([u'Managers',], titles)
    if owners:
      addTitlesToCSVfile([u'OwnersCount',], titles)
      if not ownersCountOnly:
        addTitlesToCSVfile([u'Owners',], titles)
  sys.stderr.write(u"Retrieving All Groups for G Suite account (may take some time on a large account)...\n")
  page_message = u'Got %%num_items%% groups: %%first_item%% - %%last_item%%\n'
  entityList = callGAPIpages(cd.groups(), u'list', u'groups',
                             page_message=page_message, message_attribute=u'email',
                             customer=customer, domain=usedomain, userKey=usemember,
                             fields=u'nextPageToken,groups({0})'.format(cdfields),
                             maxResults=maxResults)
  i = 0
  count = len(entityList)
  for groupEntity in entityList:
    i += 1
    groupEmail = groupEntity[u'email']
    group = {}
    for field in cdfieldsList:
      if field in groupEntity:
        if isinstance(groupEntity[field], list):
          group[fieldsTitles[field]] = aliasDelimiter.join(groupEntity[field])
        else:
          group[fieldsTitles[field]] = groupEntity[field]
    if roles:
      sys.stderr.write(u' Getting %s for %s (%s/%s)\n' % (roles, groupEmail, i, count))
      page_message = u'Got %%num_items%% members: %%first_item%% - %%last_item%%\n'
      groupMembers = callGAPIpages(cd.members(), u'list', u'members',
                                   page_message=page_message, message_attribute=u'email',
                                   soft_errors=True,
                                   groupKey=groupEmail, roles=roles, fields=u'nextPageToken,members(email,id,role)',
                                   maxResults=GC_Values[GC_MEMBER_MAX_RESULTS])
      if members:
        membersList = []
        membersCount = 0
      if managers:
        managersList = []
        managersCount = 0
      if owners:
        ownersList = []
        ownersCount = 0
      for member in groupMembers:
        member_email = member.get(u'email', member.get(u'id', None))
        if not member_email:
          sys.stderr.write(u' Not sure what to do with: %s' % member)
          continue
        role = member.get(u'role', None)
        if role:
          if role == ROLE_MEMBER:
            if members:
              membersCount += 1
              if not membersCountOnly:
                membersList.append(member_email)
          elif role == ROLE_MANAGER:
            if managers:
              managersCount += 1
              if not managersCountOnly:
                managersList.append(member_email)
          elif role == ROLE_OWNER:
            if owners:
              ownersCount += 1
              if not ownersCountOnly:
                ownersList.append(member_email)
          elif members:
            membersCount += 1
            if not membersCountOnly:
              membersList.append(member_email)
        elif members:
          membersCount += 1
          if not membersCountOnly:
            membersList.append(member_email)
      if members:
        group[u'MembersCount'] = membersCount
        if not membersCountOnly:
          group[u'Members'] = memberDelimiter.join(membersList)
      if managers:
        group[u'ManagersCount'] = managersCount
        if not managersCountOnly:
          group[u'Managers'] = memberDelimiter.join(managersList)
      if owners:
        group[u'OwnersCount'] = ownersCount
        if not ownersCountOnly:
          group[u'Owners'] = memberDelimiter.join(ownersList)
    if getSettings and not GroupIsAbuseOrPostmaster(groupEmail):
      sys.stderr.write(u" Retrieving Settings for group %s (%s/%s)...\r\n" % (groupEmail, i, count))
      settings = callGAPI(gs.groups(), u'get',
                          soft_errors=True,
                          retry_reasons=[u'serviceLimit', u'invalid'],
                          groupUniqueId=groupEmail, fields=gsfields)
      if settings:
        for key in settings:
          if key in [u'email', u'name', u'description', u'kind', u'etag']:
            continue
          setting_value = settings[key]
          if setting_value is None:
            setting_value = u''
          if key not in titles:
            addTitleToCSVfile(key, titles)
          group[key] = setting_value
      else:
        sys.stderr.write(u" Settings unavailable for group %s (%s/%s)...\r\n" % (groupEmail, i, count))
    csvRows.append(group)
  if sortHeaders:
    sortCSVTitles([u'Email',], titles)
  writeCSVfile(csvRows, titles, u'Groups', todrive)

def doPrintOrgs():
  print_order = [u'orgUnitPath', u'orgUnitId', u'name', u'description',
                 u'parentOrgUnitPath', u'parentOrgUnitId', u'blockInheritance']
  cd = buildGAPIObject(u'directory')
  listType = u'all'
  orgUnitPath = u"/"
  todrive = False
  fields = [u'orgUnitPath', u'name', u'orgUnitId', u'parentOrgUnitId']
  titles = []
  csvRows = []
  parentOrgIds = []
  retrievedOrgIds = []
  i = 3
  while i < len(sys.argv):
    myarg = sys.argv[i].lower().replace(u'_', u'')
    if myarg == u'todrive':
      todrive = True
      i += 1
    elif myarg == u'toplevelonly':
      listType = u'children'
      i += 1
    elif myarg == u'fromparent':
      orgUnitPath = sys.argv[i+1]
      i += 2
    elif myarg == u'allfields':
      fields = None
      i += 1
    elif myarg == u'fields':
      fields += sys.argv[i+1].split(u',')
      i += 2
    else:
      systemErrorExit(2, '%s is not a valid argument for "gam print orgs"' % sys.argv[i])
  sys.stderr.write(u"Retrieving All Organizational Units for your account (may take some time on large domain)...\n")
  if fields:
    get_fields = u','.join(fields)
    list_fields = u'organizationUnits(%s)' % get_fields
  else:
    list_fields = None
    get_fields = None
  orgs = callGAPI(cd.orgunits(), u'list',
                  customerId=GC_Values[GC_CUSTOMER_ID], type=listType, orgUnitPath=orgUnitPath, fields=list_fields)
  if not u'organizationUnits' in orgs:
    topLevelOrgId = getTopLevelOrgId(cd, orgUnitPath)
    if topLevelOrgId:
      parentOrgIds.append(topLevelOrgId)
    orgunits = []
  else:
    orgunits = orgs[u'organizationUnits']
  for row in orgunits:
    retrievedOrgIds.append(row[u'orgUnitId'])
    if row[u'parentOrgUnitId'] not in parentOrgIds:
      parentOrgIds.append(row[u'parentOrgUnitId'])
  missing_parents = set(parentOrgIds) - set(retrievedOrgIds)
  for missing_parent in missing_parents:
    try:
      result = callGAPI(cd.orgunits(), u'get',
                        customerId=GC_Values[GC_CUSTOMER_ID], orgUnitPath=missing_parent, fields=get_fields, throw_reasons=[u'required'])
      orgunits.append(result)
    except:
      pass
  for row in orgunits:
    orgEntity = {}
    for key, value in row.items():
      if key in [u'kind', u'etag', u'etags']:
        continue
      if key not in titles:
        titles.append(key)
      orgEntity[key] = value
    csvRows.append(orgEntity)
  for title in titles:
    if title not in print_order:
      print_order.append(title)
  titles = sorted(titles, key=print_order.index)
  # sort results similar to how they list in admin console
  csvRows.sort(key=lambda x: x[u'orgUnitPath'].lower(), reverse=False)
  writeCSVfile(csvRows, titles, u'Orgs', todrive)

def doPrintAliases():
  cd = buildGAPIObject(u'directory')
  todrive = False
  titles = [u'Alias', u'Target', u'TargetType']
  csvRows = []
  userFields = [u'primaryEmail', u'aliases']
  groupFields = [u'email', u'aliases']
  doGroups = doUsers = True
  query = None
  i = 3
  while i < len(sys.argv):
    myarg = sys.argv[i].lower().replace(u'_', u'')
    if myarg == u'todrive':
      todrive = True
      i += 1
    elif myarg == u'shownoneditable':
      titles.insert(1, u'NonEditableAlias')
      userFields.append(u'nonEditableAliases')
      groupFields.append(u'nonEditableAliases')
      i += 1
    elif myarg == u'nogroups':
      doGroups = False
      i += 1
    elif myarg == u'nousers':
      doUsers = False
      i += 1
    elif myarg == u'query':
      query = getString(i+1, u'Query')
      doGroups = False
      doUsers = True
      i += 2
    else:
      systemErrorExit(2, '%s is not a valid argument for "gam print aliases"' % sys.argv[i])
  if doUsers:
    sys.stderr.write(u"Retrieving All User Aliases for %s organization (may take some time on large domain)...\n" % GC_Values[GC_DOMAIN])
    page_message = u'Got %%num_items%% users %%first_item%% - %%last_item%%\n'
    all_users = callGAPIpages(cd.users(), u'list', u'users', page_message=page_message,
                              message_attribute=u'primaryEmail', customer=GC_Values[GC_CUSTOMER_ID], query=query,
                              fields=u'nextPageToken,users({0})'.format(u','.join(userFields)), maxResults=GC_Values[GC_USER_MAX_RESULTS])
    for user in all_users:
      for alias in user.get(u'aliases', []):
        csvRows.append({u'Alias': alias, u'Target': user[u'primaryEmail'], u'TargetType': u'User'})
      for alias in user.get(u'nonEditableAliases', []):
        csvRows.append({u'NonEditableAlias': alias, u'Target': user[u'primaryEmail'], u'TargetType': u'User'})
  if doGroups:
    sys.stderr.write(u"Retrieving All Group Aliases for %s organization (may take some time on large domain)...\n" % GC_Values[GC_DOMAIN])
    page_message = u'Got %%num_items%% groups %%first_item%% - %%last_item%%\n'
    all_groups = callGAPIpages(cd.groups(), u'list', u'groups', page_message=page_message,
                               message_attribute=u'email', customer=GC_Values[GC_CUSTOMER_ID],
                               fields=u'nextPageToken,groups({0})'.format(u','.join(groupFields)))
    for group in all_groups:
      for alias in group.get(u'aliases', []):
        csvRows.append({u'Alias': alias, u'Target': group[u'email'], u'TargetType': u'Group'})
      for alias in group.get(u'nonEditableAliases', []):
        csvRows.append({u'NonEditableAlias': alias, u'Target': group[u'email'], u'TargetType': u'Group'})
  writeCSVfile(csvRows, titles, u'Aliases', todrive)

def doPrintGroupMembers():
  cd = buildGAPIObject(u'directory')
  todrive = False
  membernames = False
  customer = GC_Values[GC_CUSTOMER_ID]
  usedomain = None
  usemember = None
  roles = []
  fields = None
  titles = [u'group']
  csvRows = []
  groups_to_get = []
  i = 3
  while i < len(sys.argv):
    myarg = sys.argv[i].lower()
    if myarg == u'domain':
      usedomain = sys.argv[i+1].lower()
      customer = None
      i += 2
    elif myarg == u'todrive':
      todrive = True
      i += 1
    elif myarg == u'member':
      usemember = normalizeEmailAddressOrUID(sys.argv[i+1])
      customer = None
      i += 2
    elif myarg == u'fields':
      memberFieldsList = sys.argv[i+1].replace(u',', u' ').lower().split()
      fields = u'nextPageToken,members(%s)' % (','.join(memberFieldsList))
      i += 2
    elif myarg == u'membernames':
      membernames = True
      titles.append(u'name')
      i += 1
    elif myarg in [u'role', u'roles']:
      for role in sys.argv[i+1].lower().replace(u',', u' ').split():
        if role in GROUP_ROLES_MAP:
          roles.append(GROUP_ROLES_MAP[role])
        else:
          systemErrorExit(2, '%s is not a valid role for "gam print group-members %s"' % (role, myarg))
      i += 2
    elif myarg == u'group':
      group_email = normalizeEmailAddressOrUID(sys.argv[i+1])
      groups_to_get = [{u'email': group_email}]
      i += 2
    else:
      systemErrorExit(2, '%s is not a valid argument for "gam print group-members"' % sys.argv[i])
  if not groups_to_get:
    groups_to_get = callGAPIpages(cd.groups(), u'list', u'groups', message_attribute=u'email',
                                  customer=customer, domain=usedomain, userKey=usemember, fields=u'nextPageToken,groups(email)')
  i = 0
  count = len(groups_to_get)
  for group in groups_to_get:
    i += 1
    group_email = group[u'email']
    sys.stderr.write(u'Getting members for %s (%s/%s)\n' % (group_email, i, count))
    group_members = callGAPIpages(cd.members(), u'list', u'members',
                                  soft_errors=True, roles=u','.join(roles),
                                  groupKey=group_email, fields=fields, maxResults=GC_Values[GC_MEMBER_MAX_RESULTS])
    for member in group_members:
      for unwanted_item in [u'kind', u'etag']:
        if unwanted_item in member:
          del member[unwanted_item]
      for title in member:
        if title not in titles:
          titles.append(title)
      member[u'group'] = group_email
      if membernames and u'type' in member and u'id' in member:
        if member[u'type'] == u'USER':
          try:
            mbinfo = callGAPI(cd.users(), u'get',
                              throw_reasons=[GAPI_USER_NOT_FOUND, GAPI_NOT_FOUND, GAPI_FORBIDDEN],
                              userKey=member[u'id'], fields=u'name')
            memberName = mbinfo[u'name'][u'fullName']
          except (GAPI_userNotFound, GAPI_notFound, GAPI_forbidden):
            memberName = u'Unknown'
        elif member[u'type'] == u'GROUP':
          try:
            mbinfo = callGAPI(cd.groups(), u'get',
                              throw_reasons=[GAPI_NOT_FOUND, GAPI_FORBIDDEN],
                              groupKey=member[u'id'], fields=u'name')
            memberName = mbinfo[u'name']
          except (GAPI_notFound, GAPI_forbidden):
            memberName = u'Unknown'
        elif member[u'type'] == u'CUSTOMER':
          try:
            mbinfo = callGAPI(cd.customers(), u'get',
                              throw_reasons=[GAPI_BAD_REQUEST, GAPI_RESOURCE_NOT_FOUND, GAPI_FORBIDDEN],
                              customerKey=member[u'id'], fields=u'customerDomain')
            memberName = mbinfo[u'customerDomain']
          except (GAPI_badRequest, GAPI_resourceNotFound, GAPI_forbidden):
            memberName = u'Unknown'
        else:
          memberName = u'Unknown'
        member[u'name'] = memberName
      csvRows.append(member)
  writeCSVfile(csvRows, titles, u'Group Members', todrive)

def doPrintVaultMatters():
  v = buildGAPIObject(u'vault')
  todrive = False
  csvRows = []
  initialTitles = [u'matterId', u'name', u'description', u'state']
  titles = initialTitles[:]
  view = u'FULL'
  i = 3
  while i < len(sys.argv):
    myarg = sys.argv[i].lower().replace(u'_', u'')
    if myarg == u'todrive':
      todrive = True
      i += 1
    elif myarg in PROJECTION_CHOICES_MAP:
      view = PROJECTION_CHOICES_MAP[myarg]
      i += 1
    else:
      systemErrorExit(3, '%s is not a valid argument to "gam print matters"' % myarg)
  sys.stderr.write(u'Retrieving all Vault Matters...\n')
  page_message = u' got %%num_items%% matters...\n'
  matters = callGAPIpages(v.matters(), u'list', u'matters', page_message=page_message, view=view)
  for matter in matters:
    addRowTitlesToCSVfile(flatten_json(matter), csvRows, titles)
  sortCSVTitles(initialTitles, titles)
  writeCSVfile(csvRows, titles, u'Vault Matters', todrive)

def doPrintVaultHolds():
  v = buildGAPIObject(u'vault')
  todrive = False
  csvRows = []
  initialTitles = [u'matterId', u'holdId', u'name', u'corpus', u'updateTime']
  titles = initialTitles[:]
  matters = []
  matterIds = []
  i = 3
  while i < len(sys.argv):
    myarg = sys.argv[i].lower().replace(u'_', u'')
    if myarg == u'todrive':
      todrive = True
      i += 1
    elif myarg in [u'matter', u'matters']:
      matters = sys.argv[i+1].split(u',')
      i += 2
    else:
      systemErrorExit(3, '%s is not a valid a valid argument to "gam print holds"' % myarg)
  if not matters:
    matters_results = callGAPIpages(v.matters(), u'list', u'matters', view=u'BASIC', fields=u'matters(matterId,state),nextPageToken')
    for matter in matters_results:
      if matter[u'state'] != u'OPEN':
        print u'ignoring matter %s in state %s' % (matter[u'matterId'], matter[u'state'])
        continue
      matterIds.append(matter[u'matterId'])
  for matter in matters:
    matterIds.append(convertMatterNameToID(v, matter))
  for matterId in matterIds:
    sys.stderr.write(u'Retrieving holds for matter %s\n' % matterId)
    holds = callGAPIpages(v.matters().holds(), u'list', u'holds', matterId=matterId)
    for hold in holds:
      addRowTitlesToCSVfile(flatten_json(hold, flattened={u'matterId': matterId}), csvRows, titles)
  sortCSVTitles(initialTitles, titles)
  writeCSVfile(csvRows, titles, u'Vault Holds', todrive)

def doPrintMobileDevices():
  cd = buildGAPIObject(u'directory')
  todrive = False
  titles = []
  csvRows = []
  fields = None
  query = projection = orderBy = sortOrder = None
  delimiter = u' '
  listLimit = 1
  appsLimit = -1
  i = 3
  while i < len(sys.argv):
    myarg = sys.argv[i].lower().replace(u'_', u'')
    if myarg == u'todrive':
      todrive = True
      i += 1
    elif myarg == u'query':
      query = sys.argv[i+1]
      i += 2
    elif myarg == u'delimiter':
      delimiter = sys.argv[i+1]
      i += 2
    elif myarg == u'listlimit':
      listLimit = int(sys.argv[i+1])
      i += 2
    elif myarg == u'appslimit':
      appsLimit = int(sys.argv[i+1])
      i += 2
    elif myarg == u'fields':
      fields = u'nextPageToken,mobiledevices(%s)' % sys.argv[i+1]
      i += 2
    elif myarg == u'orderby':
      orderBy = sys.argv[i+1].lower()
      allowed_values = [u'deviceid', u'email', u'lastsync', u'model', u'name', u'os', u'status', u'type']
      if orderBy.lower() not in allowed_values:
        systemErrorExit(2, 'orderBy must be one of %s; got %s' % (u', '.join(allowed_values), orderBy))
      elif orderBy == u'lastsync':
        orderBy = u'lastSync'
      elif orderBy == u'deviceid':
        orderBy = u'deviceId'
      i += 2
    elif myarg in SORTORDER_CHOICES_MAP:
      sortOrder = SORTORDER_CHOICES_MAP[myarg]
      i += 1
    elif myarg in PROJECTION_CHOICES_MAP:
      projection = PROJECTION_CHOICES_MAP[myarg]
      i += 1
    else:
      systemErrorExit(2, '%s is not a valid argument for "gam print mobile"' % sys.argv[i])
  sys.stderr.write(u'Retrieving All Mobile Devices for organization (may take some time for large accounts)...\n')
  page_message = u'Got %%num_items%% mobile devices...\n'
  all_mobile = callGAPIpages(cd.mobiledevices(), u'list', u'mobiledevices', page_message=page_message,
                             customerId=GC_Values[GC_CUSTOMER_ID], query=query, projection=projection, fields=fields,
                             orderBy=orderBy, sortOrder=sortOrder, maxResults=GC_Values[GC_DEVICE_MAX_RESULTS])
  for mobile in all_mobile:
    row = {}
    for attrib in mobile:
      if attrib in [u'kind', u'etag']:
        continue
      if attrib in [u'name', u'email', u'otherAccountsInfo']:
        if attrib not in titles:
          titles.append(attrib)
        if listLimit > 0:
          row[attrib] = delimiter.join(mobile[attrib][0:listLimit])
        elif listLimit == 0:
          row[attrib] = delimiter.join(mobile[attrib])
      elif attrib == u'applications':
        if appsLimit >= 0:
          if attrib not in titles:
            titles.append(attrib)
          applications = []
          j = 0
          for app in mobile[attrib]:
            j += 1
            if appsLimit and (j > appsLimit):
              break
            appDetails = []
            for field in [u'displayName', u'packageName', u'versionName']:
              appDetails.append(app.get(field, u'<None>'))
            appDetails.append(unicode(app.get(u'versionCode', u'<None>')))
            permissions = app.get(u'permission', [])
            if permissions:
              appDetails.append(u'/'.join(permissions))
            else:
              appDetails.append(u'<None>')
            applications.append(u'-'.join(appDetails))
          row[attrib] = delimiter.join(applications)
      else:
        if attrib not in titles:
          titles.append(attrib)
        row[attrib] = mobile[attrib]
    csvRows.append(row)
  sortCSVTitles([u'resourceId', u'deviceId', u'serialNumber', u'name', u'email', u'status'], titles)
  writeCSVfile(csvRows, titles, u'Mobile', todrive)

def doPrintCrosActivity():
  cd = buildGAPIObject(u'directory')
  todrive = False
  titles = [u'deviceId', u'annotatedAssetId', u'annotatedLocation', u'serialNumber', u'orgUnitPath']
  csvRows = []
  fieldsList = [u'deviceId', u'annotatedAssetId', u'annotatedLocation', u'serialNumber', u'orgUnitPath']
  startDate = endDate = None
  selectActiveTimeRanges = selectDeviceFiles = selectRecentUsers = False
  listLimit = 0
  delimiter = u','
  query = orgUnitPath = None
  i = 3
  while i < len(sys.argv):
    myarg = sys.argv[i].lower().replace(u'_', u'')
    if myarg == u'query':
      query = sys.argv[i+1]
      i += 2
    elif myarg == u'limittoou':
      orgUnitPath = sys.argv[i+1]
      i += 2
    elif myarg == u'todrive':
      todrive = True
      i += 1
    elif myarg in CROS_ACTIVE_TIME_RANGES_ARGUMENTS:
      selectActiveTimeRanges = True
      i += 1
    elif myarg in CROS_DEVICE_FILES_ARGUMENTS:
      selectDeviceFiles = True
      i += 1
    elif myarg in CROS_RECENT_USERS_ARGUMENTS:
      selectRecentUsers = True
      i += 1
    elif myarg == u'both':
      selectActiveTimeRanges = selectRecentUsers = True
      i += 1
    elif myarg == u'all':
      selectActiveTimeRanges = selectDeviceFiles = selectRecentUsers = True
      i += 1
    elif myarg in CROS_START_ARGUMENTS:
      startDate = _getFilterDate(sys.argv[i+1])
      i += 2
    elif myarg in CROS_END_ARGUMENTS:
      endDate = _getFilterDate(sys.argv[i+1])
      i += 2
    elif myarg == u'listlimit':
      listLimit = int(sys.argv[i+1])
      i += 2
    elif myarg == u'delimiter':
      delimiter = sys.argv[i+1]
      i += 2
    else:
      systemErrorExit(2, '%s is not a valid argument for "gam print crosactivity"' % sys.argv[i])
  if not selectActiveTimeRanges and not selectDeviceFiles and not selectRecentUsers:
    selectActiveTimeRanges = selectRecentUsers = True
  if selectRecentUsers:
    fieldsList.append(u'recentUsers')
    addTitlesToCSVfile([u'recentUsers.email',], titles)
  if selectActiveTimeRanges:
    fieldsList.append(u'activeTimeRanges')
    addTitlesToCSVfile([u'activeTimeRanges.date', u'activeTimeRanges.duration', u'activeTimeRanges.minutes'], titles)
  if selectDeviceFiles:
    fieldsList.append(u'deviceFiles')
    addTitlesToCSVfile([u'deviceFiles.type', u'deviceFiles.createTime'], titles)
  fields = u'chromeosdevices(%s),nextPageToken' % u','.join(fieldsList)
  sys.stderr.write(u'Retrieving All Chrome OS Devices for organization (may take some time for large accounts)...\n')
  page_message = u'Got %%num_items%% Chrome devices...\n'
  all_cros = callGAPIpages(cd.chromeosdevices(), u'list', u'chromeosdevices', page_message=page_message,
                           query=query, customerId=GC_Values[GC_CUSTOMER_ID], projection=u'FULL',
                           fields=fields, maxResults=GC_Values[GC_DEVICE_MAX_RESULTS], orgUnitPath=orgUnitPath)
  for cros in all_cros:
    row = {}
    for attrib in cros:
      if attrib not in [u'recentUsers', u'activeTimeRanges', u'deviceFiles']:
        row[attrib] = cros[attrib]
    if selectActiveTimeRanges:
      activeTimeRanges = _filterTimeRanges(cros.get(u'activeTimeRanges', []), startDate, endDate)
      lenATR = len(activeTimeRanges)
      for activeTimeRange in activeTimeRanges[:min(lenATR, listLimit or lenATR)]:
        new_row = row.copy()
        new_row[u'activeTimeRanges.date'] = activeTimeRange[u'date']
        new_row[u'activeTimeRanges.duration'] = utils.formatMilliSeconds(activeTimeRange[u'activeTime'])
        new_row[u'activeTimeRanges.minutes'] = activeTimeRange[u'activeTime']/60000
        csvRows.append(new_row)
    if selectRecentUsers:
      recentUsers = cros.get(u'recentUsers', [])
      lenRU = len(recentUsers)
      row[u'recentUsers.email'] = delimiter.join([recent_user.get(u'email', [u'Unknown', u'UnmanagedUser'][recent_user[u'type'] == u'USER_TYPE_UNMANAGED']) for recent_user in recentUsers[:min(lenRU, listLimit or lenRU)]])
      csvRows.append(row)
    if selectDeviceFiles:
      deviceFiles = _filterDeviceFiles(cros.get(u'deviceFiles', []), startDate, endDate)
      lenDF = len(deviceFiles)
      for deviceFile in deviceFiles[:min(lenDF, listLimit or lenDF)]:
        new_row = row.copy()
        new_row[u'deviceFiles.type'] = deviceFile[u'type']
        new_row[u'deviceFiles.createTime'] = deviceFile[u'createTime']
        csvRows.append(new_row)
  writeCSVfile(csvRows, titles, u'CrOS Activity', todrive)

def _checkTPMVulnerability(cros):
  if u'tpmVersionInfo' in cros and u'firmwareVersion' in cros[u'tpmVersionInfo']:
    if cros[u'tpmVersionInfo'][u'firmwareVersion'] in CROS_TPM_VULN_VERSIONS:
      cros[u'tpmVersionInfo'][u'tpmVulnerability'] = u'VULNERABLE'
    elif cros[u'tpmVersionInfo'][u'firmwareVersion'] in CROS_TPM_FIXED_VERSIONS:
      cros[u'tpmVersionInfo'][u'tpmVulnerability'] = u'UPDATED'
    else:
      cros[u'tpmVersionInfo'][u'tpmVulnerability'] = u'NOT IMPACTED'
  return cros

def doPrintCrosDevices():
  cd = buildGAPIObject(u'directory')
  todrive = False
  fieldsList = []
  fieldsTitles = {}
  titles = []
  csvRows = []
  addFieldToCSVfile(u'deviceid', CROS_ARGUMENT_TO_PROPERTY_MAP, fieldsList, fieldsTitles, titles)
  sortHeaders = False
  query = projection = orderBy = sortOrder = orgUnitPath = None
  noLists = False
  selectActiveTimeRanges = selectDeviceFiles = selectRecentUsers = False
  startDate = endDate = None
  listLimit = 0
  i = 3
  while i < len(sys.argv):
    myarg = sys.argv[i].lower().replace(u'_', u'')
    if myarg == u'query':
      query = sys.argv[i+1]
      i += 2
    elif myarg == u'limittoou':
      orgUnitPath = sys.argv[i+1]
      i += 2
    elif myarg == u'todrive':
      todrive = True
      i += 1
    elif myarg == u'nolists':
      noLists = True
      selectActiveTimeRanges = selectDeviceFiles = selectRecentUsers = False
      i += 1
    elif myarg in CROS_ACTIVE_TIME_RANGES_ARGUMENTS:
      projection = u'FULL'
      selectActiveTimeRanges = True
      noLists = False
      if fieldsList:
        fieldsList.append(u'activeTimeRanges')
      i += 1
    elif myarg in CROS_DEVICE_FILES_ARGUMENTS:
      projection = u'FULL'
      selectDeviceFiles = True
      noLists = False
      if fieldsList:
        fieldsList.append(u'deviceFiles')
      i += 1
    elif myarg in CROS_RECENT_USERS_ARGUMENTS:
      projection = u'FULL'
      selectRecentUsers = True
      noLists = False
      if fieldsList:
        fieldsList.append(u'recentUsers')
      i += 1
    elif myarg in CROS_START_ARGUMENTS:
      startDate = _getFilterDate(sys.argv[i+1])
      i += 2
    elif myarg in CROS_END_ARGUMENTS:
      endDate = _getFilterDate(sys.argv[i+1])
      i += 2
    elif myarg == u'listlimit':
      listLimit = int(sys.argv[i+1])
      i += 2
    elif myarg == u'orderby':
      orderBy = sys.argv[i+1].lower().replace(u'_', u'')
      allowed_values = [u'location', u'user', u'lastsync', u'notes', u'serialnumber', u'status', u'supportenddate']
      if orderBy not in allowed_values:
        systemErrorExit(2, 'orderBy must be one of %s; got %s' % (u', '.join(allowed_values), orderBy))
      elif orderBy == u'location':
        orderBy = u'annotatedLocation'
      elif orderBy == u'user':
        orderBy = u'annotatedUser'
      elif orderBy == u'lastsync':
        orderBy = u'lastSync'
      elif orderBy == u'serialnumber':
        orderBy = u'serialNumber'
      elif orderBy == u'supportenddate':
        orderBy = u'supportEndDate'
      i += 2
    elif myarg in SORTORDER_CHOICES_MAP:
      sortOrder = SORTORDER_CHOICES_MAP[myarg]
      i += 1
    elif myarg in PROJECTION_CHOICES_MAP:
      projection = PROJECTION_CHOICES_MAP[myarg]
      sortHeaders = True
      if projection == u'FULL':
        fieldsList = []
      else:
        fieldsList = CROS_BASIC_FIELDS_LIST[:]
      i += 1
    elif myarg == u'allfields':
      projection = u'FULL'
      sortHeaders = True
      fieldsList = []
      i += 1
    elif myarg in CROS_ARGUMENT_TO_PROPERTY_MAP:
      if not fieldsList:
        fieldsList = [u'deviceId',]
      addFieldToCSVfile(myarg, CROS_ARGUMENT_TO_PROPERTY_MAP, fieldsList, fieldsTitles, titles)
      i += 1
    elif myarg == u'fields':
      if not fieldsList:
        fieldsList = [u'deviceId',]
      fieldNameList = sys.argv[i+1]
      for field in fieldNameList.lower().replace(u',', u' ').split():
        if field in CROS_ARGUMENT_TO_PROPERTY_MAP:
          addFieldToCSVfile(field, CROS_ARGUMENT_TO_PROPERTY_MAP, fieldsList, fieldsTitles, titles)
          if field in CROS_ACTIVE_TIME_RANGES_ARGUMENTS:
            projection = u'FULL'
            selectActiveTimeRanges = True
            noLists = False
          elif field in CROS_DEVICE_FILES_ARGUMENTS:
            projection = u'FULL'
            selectDeviceFiles = True
            noLists = False
          elif field in CROS_RECENT_USERS_ARGUMENTS:
            projection = u'FULL'
            selectRecentUsers = True
            noLists = False
        else:
          systemErrorExit(2, '%s is not a valid argument for "gam print cros fields"' % field)
      i += 2
    else:
      systemErrorExit(2, '%s is not a valid argument for "gam print cros"' % sys.argv[i])
  if fieldsList:
    fields = u'nextPageToken,chromeosdevices({0})'.format(u','.join(set(fieldsList))).replace(u'.', u'/')
  else:
    fields = None
  sys.stderr.write(u'Retrieving All Chrome OS Devices for organization (may take some time for large accounts)...\n')
  page_message = u'Got %%num_items%% Chrome devices...\n'
  all_cros = callGAPIpages(cd.chromeosdevices(), u'list', u'chromeosdevices', page_message=page_message,
                           query=query, customerId=GC_Values[GC_CUSTOMER_ID], projection=projection, orgUnitPath=orgUnitPath,
                           orderBy=orderBy, sortOrder=sortOrder, fields=fields, maxResults=GC_Values[GC_DEVICE_MAX_RESULTS])
  for cros in all_cros:
    cros = _checkTPMVulnerability(cros)
  if (not noLists) and (not selectActiveTimeRanges) and (not selectRecentUsers) and (not selectDeviceFiles):
    for cros in all_cros:
      if u'notes' in cros:
        cros[u'notes'] = cros[u'notes'].replace(u'\n', u'\\n')
      addRowTitlesToCSVfile(flatten_json(cros, listLimit=listLimit), csvRows, titles)
  else:
    if not noLists:
      if selectActiveTimeRanges:
        titles.extend([u'activeTimeRanges.date', u'activeTimeRanges.activeTime', u'activeTimeRanges.duration', u'activeTimeRanges.minutes'])
      if selectRecentUsers:
        titles.extend([u'recentUsers.email', u'recentUsers.type'])
      if selectDeviceFiles:
        titles.extend([u'deviceFiles.type', u'deviceFiles.createTime'])
    for cros in all_cros:
      if u'notes' in cros:
        cros[u'notes'] = cros[u'notes'].replace(u'\n', u'\\n')
      row = {}
      for attrib in cros:
        if attrib not in [u'kind', u'etag', u'recentUsers', u'activeTimeRanges', u'deviceFiles']:
          if attrib not in titles:
            titles.append(attrib)
          row[attrib] = cros[attrib]
      activeTimeRanges = _filterTimeRanges(cros.get(u'activeTimeRanges', []), startDate, endDate) if selectActiveTimeRanges else []
      recentUsers = cros.get(u'recentUsers', []) if selectRecentUsers else []
      deviceFiles = _filterDeviceFiles(cros.get(u'deviceFiles', []), startDate, endDate) if selectDeviceFiles else []
      if noLists or (not activeTimeRanges and not recentUsers and not deviceFiles):
        csvRows.append(row)
      else:
        lenATR = len(activeTimeRanges)
        lenRU = len(recentUsers)
        lenDF = len(deviceFiles)
        for i in xrange(min(listLimit, max(lenATR, lenRU)) if listLimit else max(lenATR, lenRU, lenDF)):
          new_row = row.copy()
          if i < lenATR:
            new_row[u'activeTimeRanges.date'] = activeTimeRanges[i][u'date']
            new_row[u'activeTimeRanges.activeTime'] = str(activeTimeRanges[i][u'activeTime'])
            new_row[u'activeTimeRanges.duration'] = utils.formatMilliSeconds(activeTimeRanges[i][u'activeTime'])
            new_row[u'activeTimeRanges.minutes'] = activeTimeRanges[i][u'activeTime']/60000
          if i < lenRU:
            new_row[u'recentUsers.email'] = recentUsers[i].get(u'email', [u'Unknown', u'UnmanagedUser'][recentUsers[i][u'type'] == u'USER_TYPE_UNMANAGED'])
            new_row[u'recentUsers.type'] = recentUsers[i][u'type']
          if i < lenDF:
            new_row[u'deviceFiles.type'] = deviceFiles[i][u'type']
            new_row[u'deviceFiles.createTime'] = deviceFiles[i][u'createTime']
          csvRows.append(new_row)
  if sortHeaders:
    sortCSVTitles([u'deviceId',], titles)
  writeCSVfile(csvRows, titles, u'CrOS', todrive)

def doPrintLicenses(returnFields=None, skus=None):
  lic = buildGAPIObject(u'licensing')
  products = []
  licenses = []
  if not returnFields:
    titles = [u'userId', u'productId', u'skuId']
    csvRows = []
    todrive = False
    i = 3
    while i < len(sys.argv):
      myarg = sys.argv[i].lower()
      if myarg == u'todrive':
        todrive = True
        i += 1
      elif myarg in [u'products', u'product']:
        products = sys.argv[i+1].split(u',')
        i += 2
      elif myarg in [u'sku', u'skus']:
        skus = sys.argv[i+1].split(u',')
        i += 2
      else:
        systemErrorExit(2, '%s is not a valid argument for "gam print licenses"' % sys.argv[i])
    fields = u'nextPageToken,items(productId,skuId,userId)'
  else:
    fields = u'nextPageToken,items({0})'.format(returnFields)
  if skus:
    for sku in skus:
      product, sku = getProductAndSKU(sku)
      page_message = u'Got %%%%total_items%%%% Licenses for %s...\n' % sku
      try:
        licenses += callGAPIpages(lic.licenseAssignments(), u'listForProductAndSku', u'items', throw_reasons=[GAPI_INVALID, GAPI_FORBIDDEN], page_message=page_message,
                                  customerId=GC_Values[GC_DOMAIN], productId=product, skuId=sku, fields=fields)
      except (GAPI_invalid, GAPI_forbidden):
        pass
  else:
    if not products:
      for sku in SKUS.values():
        if sku[u'product'] not in products:
          products.append(sku[u'product'])
      products.sort()
    for productId in products:
      page_message = u'Got %%%%total_items%%%% Licenses for %s...\n' % productId
      try:
        licenses += callGAPIpages(lic.licenseAssignments(), u'listForProduct', u'items', throw_reasons=[GAPI_INVALID, GAPI_FORBIDDEN], page_message=page_message,
                                  customerId=GC_Values[GC_DOMAIN], productId=productId, fields=fields)
      except (GAPI_invalid, GAPI_forbidden):
        pass
  if returnFields:
    if returnFields == u'userId':
      userIds = []
      for u_license in licenses:
        userId = u_license.get(u'userId', u'').lower()
        if userId:
          userIds.append(userId)
      return userIds
    else:
      userSkuIds = {}
      for u_license in licenses:
        userId = u_license.get(u'userId', u'').lower()
        skuId = u_license.get(u'skuId')
        if userId and skuId:
          userSkuIds.setdefault(userId, [])
          userSkuIds[userId].append(skuId)
      return userSkuIds
  for u_license in licenses:
    userId = u_license.get(u'userId', u'').lower()
    skuId = u_license.get(u'skuId', u'')
    csvRows.append({u'userId': userId, u'productId': u_license.get(u'productId', u''),
                    u'skuId': _skuIdToDisplayName(skuId)})
  writeCSVfile(csvRows, titles, u'Licenses', todrive)

RESCAL_DFLTFIELDS = [u'id', u'name', u'email',]
RESCAL_ALLFIELDS = [u'id', u'name', u'email', u'description', u'type', u'buildingid', u'category', u'capacity',
                    u'features', u'floor', u'floorsection', u'generatedresourcename', u'uservisibledescription',]

RESCAL_ARGUMENT_TO_PROPERTY_MAP = {
  u'description': [u'resourceDescription'],
  u'building': [u'buildingId',],
  u'buildingid': [u'buildingId',],
  u'capacity': [u'capacity',],
  u'category': [u'resourceCategory',],
  u'email': [u'resourceEmail'],
  u'feature': [u'featureInstances',],
  u'features': [u'featureInstances',],
  u'floor': [u'floorName',],
  u'floorname': [u'floorName',],
  u'floorsection': [u'floorSection',],
  u'generatedresourcename': [u'generatedResourceName',],
  u'id': [u'resourceId'],
  u'name': [u'resourceName'],
  u'type': [u'resourceType'],
  u'userdescription': [u'userVisibleDescription',],
  u'uservisibledescription': [u'userVisibleDescription',],
  }

def doPrintFeatures():
  to_drive = False
  cd = buildGAPIObject(u'directory')
  titles = []
  csvRows = []
  fieldsList = [u'name']
  fields = u'nextPageToken,features(%s)'
  possible_fields = {}
  for pfield in cd._rootDesc[u'schemas'][u'Feature'][u'properties']:
    possible_fields[pfield.lower()] = pfield
  i = 3
  while i < len(sys.argv):
    myarg = sys.argv[i].lower()
    if myarg == u'todrive':
      to_drive = True
      i += 1
    elif myarg == u'allfields':
      fields = None
      i += 1
    elif myarg in possible_fields:
      fieldsList.append(possible_fields[myarg])
      i += 1
    elif u'feature'+myarg in possible_fields:
      fieldsList.append(possible_fields[u'feature'+myarg])
      i += 1
    else:
      systemErrorExit(3, '%s is not a valid argument to "gam print features"' % sys.argv[i])
  if fields:
    fields = fields % u','.join(fieldsList)
  features = callGAPIpages(cd.resources().features(), u'list', u'features',
                           customer=GC_Values[GC_CUSTOMER_ID], fields=fields)
  for feature in features:
    feature.pop(u'etags', None)
    feature.pop(u'etag', None)
    feature.pop(u'kind', None)
    feature = flatten_json(feature)
    for item in feature:
      if item not in titles:
        titles.append(item)
    csvRows.append(feature)
  sortCSVTitles(u'name', titles)
  writeCSVfile(csvRows, titles, u'Features', to_drive)

def doPrintBuildings():
  to_drive = False
  cd = buildGAPIObject(u'directory')
  titles = []
  csvRows = []
  fieldsList = [u'buildingId']
  # buildings.list() currently doesn't support paging
  # but should soon, attempt to use it now so we
  # won't break when it's turned on.
  fields = u'nextPageToken,buildings(%s)'
  possible_fields = {}
  for pfield in cd._rootDesc[u'schemas'][u'Building'][u'properties']:
    possible_fields[pfield.lower()] = pfield
  i = 3
  while i < len(sys.argv):
    myarg = sys.argv[i].lower()
    if myarg == u'todrive':
      to_drive = True
      i += 1
    elif myarg == u'allfields':
      fields = None
      i += 1
    elif myarg in possible_fields:
      fieldsList.append(possible_fields[myarg])
      i += 1
    # Allows shorter arguments like "name" instead of "buildingname"
    elif u'building'+myarg in possible_fields:
      fieldsList.append(possible_fields[u'building'+myarg])
      i += 1
    else:
      systemErrorExit(3, '%s is not a valid argument to "gam print buildings"' % sys.argv[i])
  if fields:
    fields = fields % u','.join(fieldsList)
  buildings = callGAPIpages(cd.resources().buildings(), u'list', u'buildings',
                            customer=GC_Values[GC_CUSTOMER_ID], fields=fields)
  for building in buildings:
    building.pop(u'etags', None)
    building.pop(u'etag', None)
    building.pop(u'kind', None)
    if u'buildingId' in building:
      building[u'buildingId'] = u'id:{0}'.format(building[u'buildingId'])
    if u'floorNames' in building:
      building[u'floorNames'] = u','.join(building[u'floorNames'])
    building = flatten_json(building)
    for item in building:
      if item not in titles:
        titles.append(item)
    csvRows.append(building)
  sortCSVTitles(u'buildingId', titles)
  writeCSVfile(csvRows, titles, u'Buildings', to_drive)

def doPrintResourceCalendars():
  cd = buildGAPIObject(u'directory')
  todrive = False
  fieldsList = []
  fieldsTitles = {}
  titles = []
  csvRows = []
  i = 3
  while i < len(sys.argv):
    myarg = sys.argv[i].lower()
    if myarg == u'todrive':
      todrive = True
      i += 1
    elif myarg == u'allfields':
      fieldsList = []
      fieldsTitles = {}
      titles = []
      for field in RESCAL_ALLFIELDS:
        addFieldToCSVfile(field, RESCAL_ARGUMENT_TO_PROPERTY_MAP, fieldsList, fieldsTitles, titles)
      i += 1
    elif myarg in RESCAL_ARGUMENT_TO_PROPERTY_MAP:
      addFieldToCSVfile(myarg, RESCAL_ARGUMENT_TO_PROPERTY_MAP, fieldsList, fieldsTitles, titles)
      i += 1
    else:
      systemErrorExit(2, '%s is not a valid argument for "gam print resources"' % sys.argv[i])
  if not fieldsList:
    for field in RESCAL_DFLTFIELDS:
      addFieldToCSVfile(field, RESCAL_ARGUMENT_TO_PROPERTY_MAP, fieldsList, fieldsTitles, titles)
  fields = u'nextPageToken,items({0})'.format(u','.join(set(fieldsList)))
  if u'buildingId' in fieldsList:
    addFieldToCSVfile(u'buildingName', {u'buildingName': [u'buildingName',]}, fieldsList, fieldsTitles, titles)
  sys.stderr.write(u"Retrieving All Resource Calendars for your account (may take some time on a large domain)\n")
  page_message = u'Got %%total_items%% resources: %%first_item%% - %%last_item%%\n'
  resources = callGAPIpages(cd.resources().calendars(), u'list', u'items',
                            page_message=page_message, message_attribute=u'resourceId',
                            customer=GC_Values[GC_CUSTOMER_ID], fields=fields)
  for resource in resources:
    if u'featureInstances' in resource:
      resource[u'featureInstances'] = u','.join([a_feature[u'feature'][u'name'] for a_feature in resource.pop(u'featureInstances')])
    if u'buildingId' in resource:
      resource[u'buildingName'] = _getBuildingNameById(cd, resource[u'buildingId'])
      resource[u'buildingId'] = u'id:{0}'.format(resource[u'buildingId'])
    resUnit = {}
    for field in fieldsList:
      resUnit[fieldsTitles[field]] = resource.get(field, u'')
    csvRows.append(resUnit)
  sortCSVTitles([u'resourceId', u'resourceName', u'resourceEmail'], titles)
  writeCSVfile(csvRows, titles, u'Resources', todrive)

def getUsersToModify(entity_type=None, entity=None, silent=False, member_type=None, checkNotSuspended=False, groupUserMembersOnly=True):
  got_uids = False
  if entity_type is None:
    entity_type = sys.argv[1].lower()
  if entity is None:
    entity = sys.argv[2]
  cd = buildGAPIObject(u'directory')
  if entity_type == u'user':
    users = [entity,]
  elif entity_type == u'users':
    users = entity.replace(u',', u' ').split()
  elif entity_type == u'group':
    got_uids = True
    group = entity
    if member_type is None:
      member_type_message = u'all members'
    else:
      member_type_message = u'%ss' % member_type.lower()
    group = normalizeEmailAddressOrUID(group)
    page_message = None
    if not silent:
      sys.stderr.write(u"Getting %s of %s (may take some time for large groups)...\n" % (member_type_message, group))
      page_message = u'Got %%%%total_items%%%% %s...' % member_type_message
    members = callGAPIpages(cd.members(), u'list', u'members', page_message=page_message,
                            groupKey=group, roles=member_type, fields=u'nextPageToken,members(email,id,type,status)',
                            maxResults=GC_Values[GC_MEMBER_MAX_RESULTS])
    users = []
    for member in members:
      if ((not groupUserMembersOnly) or (member[u'type'] == u'USER')) and not (checkNotSuspended and (member[u'status'] == u'SUSPENDED')):
        users.append(member.get(u'email', member[u'id']))
  elif entity_type in [u'ou', u'org']:
    got_uids = True
    ou = entity
    if ou[0] != u'/':
      ou = u'/%s' % ou
    users = []
    page_message = None
    if not silent:
      sys.stderr.write(u"Getting all users in the G Suite organization (may take some time on a large domain)...\n")
      page_message = u'Got %%total_items%% users...'
    members = callGAPIpages(cd.users(), u'list', u'users', page_message=page_message,
                            customer=GC_Values[GC_CUSTOMER_ID], fields=u'nextPageToken,users(primaryEmail,suspended,orgUnitPath)',
                            query=orgUnitPathQuery(ou), maxResults=GC_Values[GC_USER_MAX_RESULTS])
    for member in members:
      if ou.lower() != member[u'orgUnitPath'].lower():
        continue
      if not checkNotSuspended or not member[u'suspended']:
        users.append(member[u'primaryEmail'])
    if not silent:
      sys.stderr.write(u"%s users are directly in the OU.\n" % len(users))
  elif entity_type in [u'ou_and_children', u'ou_and_child']:
    got_uids = True
    ou = entity
    if ou[0] != u'/':
      ou = u'/%s' % ou
    users = []
    page_message = None
    if not silent:
      sys.stderr.write(u"Getting all users in the G Suite organization (may take some time on a large domain)...\n")
      page_message = u'Got %%total_items%% users..'
    members = callGAPIpages(cd.users(), u'list', u'users', page_message=page_message,
                            customer=GC_Values[GC_CUSTOMER_ID], fields=u'nextPageToken,users(primaryEmail,suspended)',
                            query=orgUnitPathQuery(ou), maxResults=GC_Values[GC_USER_MAX_RESULTS])
    for member in members:
      if not checkNotSuspended or not member[u'suspended']:
        users.append(member[u'primaryEmail'])
    if not silent:
      sys.stderr.write(u"done.\r\n")
  elif entity_type in [u'query',]:
    got_uids = True
    users = []
    if not silent:
      sys.stderr.write(u"Getting all users that match query %s (may take some time on a large domain)...\n" % entity)
    page_message = u'Got %%total_items%% users...'
    members = callGAPIpages(cd.users(), u'list', u'users', page_message=page_message,
                            customer=GC_Values[GC_CUSTOMER_ID], fields=u'nextPageToken,users(primaryEmail,suspended)',
                            query=entity, maxResults=GC_Values[GC_USER_MAX_RESULTS])
    for member in members:
      if not checkNotSuspended or not member[u'suspended']:
        users.append(member[u'primaryEmail'])
    if not silent:
      sys.stderr.write(u"done.\r\n")
  elif entity_type in [u'license', u'licenses', u'licence', u'licences']:
    users = doPrintLicenses(returnFields=u'userId', skus=entity.split(u','))
  elif entity_type == u'file':
    users = []
    f = openFile(entity)
    for row in f:
      user = row.strip()
      if user:
        users.append(user)
    closeFile(f)
  elif entity_type in [u'csv', u'csvfile']:
    drive, filenameColumn = os.path.splitdrive(entity)
    if filenameColumn.find(u':') == -1:
      systemErrorExit(2, u'Expected {0} FileName:FieldName'.format(entity_type))
    (filename, column) = filenameColumn.split(u':')
    f = openFile(drive+filename, mode='rbU')
    input_file = csv.DictReader(f, restval=u'')
    if column not in input_file.fieldnames:
      csvFieldErrorExit(column, input_file.fieldnames)
    users = []
    for row in input_file:
      user = row[column].strip()
      if user:
        users.append(user)
    closeFile(f)
  elif entity_type in [u'courseparticipants', u'teachers', u'students']:
    croom = buildGAPIObject(u'classroom')
    users = []
    entity = addCourseIdScope(entity)
    if entity_type in [u'courseparticipants', u'teachers']:
      page_message = u'Got %%total_items%% teachers...'
      teachers = callGAPIpages(croom.courses().teachers(), u'list', u'teachers', page_message=page_message, courseId=entity)
      for teacher in teachers:
        email = teacher[u'profile'].get(u'emailAddress', None)
        if email:
          users.append(email)
    if entity_type in [u'courseparticipants', u'students']:
      page_message = u'Got %%total_items%% students...'
      students = callGAPIpages(croom.courses().students(), u'list', u'students', page_message=page_message, courseId=entity)
      for student in students:
        email = student[u'profile'].get(u'emailAddress', None)
        if email:
          users.append(email)
  elif entity_type == u'all':
    got_uids = True
    users = []
    if entity.lower() == u'users':
      if not silent:
        sys.stderr.write(u"Getting all users in G Suite account (may take some time on a large account)...\n")
      page_message = u'Got %%total_items%% users...'
      all_users = callGAPIpages(cd.users(), u'list', u'users', page_message=page_message,
                                customer=GC_Values[GC_CUSTOMER_ID],
                                fields=u'nextPageToken,users(primaryEmail,suspended)', maxResults=GC_Values[GC_USER_MAX_RESULTS])
      for member in all_users:
        if not member[u'suspended']:
          users.append(member[u'primaryEmail'])
      if not silent:
        sys.stderr.write(u"done getting %s users.\r\n" % len(users))
    elif entity.lower() == u'cros':
      if not silent:
        sys.stderr.write(u"Getting all CrOS devices in G Suite account (may take some time on a large account)...\n")
      all_cros = callGAPIpages(cd.chromeosdevices(), u'list', u'chromeosdevices',
                               customerId=GC_Values[GC_CUSTOMER_ID], fields=u'nextPageToken,chromeosdevices(deviceId)',
                               maxResults=GC_Values[GC_DEVICE_MAX_RESULTS])
      for member in all_cros:
        users.append(member[u'deviceId'])
      if not silent:
        sys.stderr.write(u"done getting %s CrOS devices.\r\n" % len(users))
    else:
      systemErrorExit(3, '%s is not a valid argument for "gam all"' % entity)
  elif entity_type == u'cros':
    users = entity.replace(u',', u' ').split()
    entity = u'cros'
  else:
    systemErrorExit(2, '%s is not a valid argument for "gam"' % entity_type)
  full_users = list()
  if entity != u'cros' and not got_uids:
    for user in users:
      if user[:4] == u'uid:':
        full_users.append(user[4:])
      elif user[:3] == u'id:':
        full_users.append(user[3:])
      elif user != u'*' and user != GC_Values[GC_CUSTOMER_ID] and user.find(u'@') == -1:
        full_users.append(u'%s@%s' % (user, GC_Values[GC_DOMAIN]))
      else:
        full_users.append(user)
  else:
    full_users = users
  return full_users

def OAuthInfo():
  credentials = None
  if len(sys.argv) > 3:
    access_token = sys.argv[3]
  else:
    credentials = getValidOauth2TxtCredentials()
    credentials.user_agent = GAM_INFO
    access_token = credentials.access_token
    print u"\nOAuth File: %s" % GC_Values[GC_OAUTH2_TXT]
  oa2 = buildGAPIObject(u'oauth2')
  token_info = callGAPI(oa2, u'tokeninfo', access_token=access_token)
  print u"Client ID: %s" % token_info[u'issued_to']
  if credentials is not None:
    print u"Secret: %s" % credentials.client_secret
  scopes = token_info[u'scope'].split(u' ')
  print u'Scopes (%s):' % len(scopes)
  for scope in sorted(scopes):
    print u'  %s' % scope
  if credentials is not None:
    print u'G Suite Admin: %s' % _getValueFromOAuth(u'email', credentials=credentials)

def doDeleteOAuth():
  storage, credentials = getOauth2TxtStorageCredentials()
  if credentials is None or credentials.invalid:
    storage.delete()
    return
  try:
    credentials.revoke_uri = oauth2client.GOOGLE_REVOKE_URI
  except AttributeError:
    systemErrorExit(1, u'Authorization doesn\'t exist')
  sys.stderr.write(u'This OAuth token will self-destruct in 3...')
  time.sleep(1)
  sys.stderr.write(u'2...')
  time.sleep(1)
  sys.stderr.write(u'1...')
  time.sleep(1)
  sys.stderr.write(u'boom!\n')
  try:
    credentials.revoke(httplib2.Http(disable_ssl_certificate_validation=GC_Values[GC_NO_VERIFY_SSL]))
  except oauth2client.client.TokenRevokeError as e:
    stderrErrorMsg(str(e))
    storage.delete()

def doRequestOAuth(login_hint=None):
  storage, credentials = getOauth2TxtStorageCredentials()
  if credentials is None or credentials.invalid:
    http = httplib2.Http(disable_ssl_certificate_validation=GC_Values[GC_NO_VERIFY_SSL])
    flags = cmd_flags(noLocalWebserver=GC_Values[GC_NO_BROWSER])
    scopes = getScopesFromUser()
    if scopes is None:
      return
    client_id, client_secret = getOAuthClientIDAndSecret()
    login_hint = getValidateLoginHint(login_hint)
    flow = oauth2client.client.OAuth2WebServerFlow(client_id=client_id,
                                                   client_secret=client_secret, scope=scopes, redirect_uri=oauth2client.client.OOB_CALLBACK_URN,
                                                   user_agent=GAM_INFO, response_type=u'code', login_hint=login_hint)
    try:
      credentials = oauth2client.tools.run_flow(flow=flow, storage=storage, flags=flags, http=http)
    except httplib2.CertificateValidationUnsupported:
      noPythonSSLExit()
  else:
    print u'It looks like you\'ve already authorized GAM. Refusing to overwrite existing file:\n\n%s' % GC_Values[GC_OAUTH2_TXT]

def getOAuthClientIDAndSecret():
  """Retrieves the OAuth client ID and client secret from JSON."""
  MISSING_CLIENT_SECRETS_MESSAGE = u'''To use GAM you need to create an API project. Please run:

gam create project
'''

  cs_data = readFile(GC_Values[GC_CLIENT_SECRETS_JSON], mode=u'rb', continueOnError=True, displayError=True, encoding=None)
  if not cs_data:
    systemErrorExit(14, MISSING_CLIENT_SECRETS_MESSAGE)
  try:
    cs_json = json.loads(cs_data)
    client_id = cs_json[u'installed'][u'client_id']
    # chop off .apps.googleusercontent.com suffix as it's not needed
    # and we need to keep things short for the Auth URL.
    client_id = re.sub(r'\.apps\.googleusercontent\.com$', u'', client_id)
    client_secret = cs_json[u'installed'][u'client_secret']
  except (ValueError, IndexError, KeyError):
    systemErrorExit(3, u'the format of your client secrets file:\n\n%s\n\n is incorrect. Please recreate the file.')
  return (client_id, client_secret)

class cmd_flags(object):
  def __init__(self, noLocalWebserver):
    self.short_url = True
    self.noauth_local_webserver = noLocalWebserver
    self.logging_level = u'ERROR'
    self.auth_host_name = u'localhost'
    self.auth_host_port = [8080, 9090]

OAUTH2_SCOPES = [
  {u'name': u'Classroom API - counts as 5 scopes',
   u'subscopes': [],
   u'scopes': [u'https://www.googleapis.com/auth/classroom.rosters',
               u'https://www.googleapis.com/auth/classroom.courses',
               u'https://www.googleapis.com/auth/classroom.profile.emails',
               u'https://www.googleapis.com/auth/classroom.profile.photos',
               u'https://www.googleapis.com/auth/classroom.guardianlinks.students']},
  {u'name': u'Cloud Print API',
   u'subscopes': [],
   u'scopes': u'https://www.googleapis.com/auth/cloudprint'},
  {u'name': u'Data Transfer API',
   u'subscopes': [u'readonly'],
   u'scopes': u'https://www.googleapis.com/auth/admin.datatransfer'},
  {u'name': u'Directory API - Chrome OS Devices',
   u'subscopes': [u'readonly'],
   u'scopes': u'https://www.googleapis.com/auth/admin.directory.device.chromeos'},
  {u'name': u'Directory API - Customers',
   u'subscopes': [u'readonly'],
   u'scopes': u'https://www.googleapis.com/auth/admin.directory.customer'},
  {u'name': u'Directory API - Domains',
   u'subscopes': [u'readonly'],
   u'scopes': u'https://www.googleapis.com/auth/admin.directory.domain'},
  {u'name': u'Directory API - Groups',
   u'subscopes': [u'readonly'],
   u'scopes': u'https://www.googleapis.com/auth/admin.directory.group'},
  {u'name': u'Directory API - Mobile Devices',
   u'subscopes': [u'readonly', u'action'],
   u'scopes': u'https://www.googleapis.com/auth/admin.directory.device.mobile'},
  {u'name': u'Directory API - Notifications',
   u'subscopes': [],
   u'scopes': u'https://www.googleapis.com/auth/admin.directory.notifications'},
  {u'name': u'Directory API - Organizational Units',
   u'subscopes': [u'readonly'],
   u'scopes': u'https://www.googleapis.com/auth/admin.directory.orgunit'},
  {u'name': u'Directory API - Resource Calendars',
   u'subscopes': [u'readonly'],
   u'scopes': u'https://www.googleapis.com/auth/admin.directory.resource.calendar'},
  {u'name': u'Directory API - Roles',
   u'subscopes': [u'readonly'],
   u'scopes': u'https://www.googleapis.com/auth/admin.directory.rolemanagement'},
  {u'name': u'Directory API - User Schemas',
   u'subscopes': [u'readonly'],
   u'scopes': u'https://www.googleapis.com/auth/admin.directory.userschema'},
  {u'name': u'Directory API - User Security',
   u'subscopes': [],
   u'scopes': u'https://www.googleapis.com/auth/admin.directory.user.security'},
  {u'name': u'Directory API - Users',
   u'subscopes': [u'readonly'],
   u'scopes': u'https://www.googleapis.com/auth/admin.directory.user'},
  {u'name': u'Email Settings API - Delegation',
   u'subscopes': [],
   u'scopes': u'https://apps-apis.google.com/a/feeds/emailsettings/2.0/'},
  {u'name': u'Group Settings API',
   u'subscopes': [],
   u'scopes': u'https://www.googleapis.com/auth/apps.groups.settings'},
  {u'name': u'License Manager API',
   u'subscopes': [],
   u'scopes': u'https://www.googleapis.com/auth/apps.licensing'},
  {u'name': u'Pub / Sub API',
   u'subscopes': [],
   u'offByDefault': True,
   u'scopes': u'https://www.googleapis.com/auth/pubsub'},
  {u'name': u'Reports API - Audit Reports',
   u'subscopes': [],
   u'scopes': u'https://www.googleapis.com/auth/admin.reports.audit.readonly'},
  {u'name': u'Reports API - Usage Reports',
   u'subscopes': [],
   u'scopes': u'https://www.googleapis.com/auth/admin.reports.usage.readonly'},
  {u'name': u'Reseller API',
   u'subscopes': [],
   u'offByDefault': True,
   u'scopes': u'https://www.googleapis.com/auth/apps.order'},
  {u'name': u'Site Verification API',
   u'subscopes': [],
   u'scopes': u'https://www.googleapis.com/auth/siteverification'},
  {u'name': u'Vault Matters and Holds API',
   u'subscopes': [u'readonly'],
   u'scopes': u'https://www.googleapis.com/auth/ediscovery'},
  ]

OAUTH2_MENU = u'''
Select the authorized scopes by entering a number.
Append an 'r' to grant read-only access or an 'a' to grant action-only access.

'''
for a_scope in OAUTH2_SCOPES:
  OAUTH2_MENU += u'[%%%%s] %%2d)  %s' % (a_scope[u'name'])
  if a_scope[u'subscopes']:
    OAUTH2_MENU += u' (supports %s)' % (u' and '.join(a_scope[u'subscopes']))
  OAUTH2_MENU += '\n'
OAUTH2_MENU += '''

     s)  Select all scopes
     u)  Unselect all scopes
     e)  Exit without changes
     c)  Continue to authorization
'''
OAUTH2_CMDS = [u's', u'u', u'e', u'c']
MAXIMUM_SCOPES = 48 # max of 50 - 2 for email scope always included

def getScopesFromUser():
  """Prompts the user to choose from a list of scopes to authorize."""
  def _checkMakeScopesList(scopes):
    del scopes[:]
    for i in range(num_scopes):
      if selected_scopes[i] == u'*':
        if not isinstance(OAUTH2_SCOPES[i][u'scopes'], list):
          scopes.append(OAUTH2_SCOPES[i][u'scopes'])
        else:
          scopes += OAUTH2_SCOPES[i][u'scopes']
      elif selected_scopes[i] == u'R':
        scopes.append(u'%s.readonly' % OAUTH2_SCOPES[i][u'scopes'])
      elif selected_scopes[i] == u'A':
        scopes.append(u'%s.action' % OAUTH2_SCOPES[i][u'scopes'])
    if len(scopes) > MAXIMUM_SCOPES:
      return (False, u'ERROR: {0} scopes selected, maximum is {1}, please unselect some.\n'.format(len(scopes), MAXIMUM_SCOPES))
    if len(scopes) == 0:
      return (False, u'ERROR: No scopes selected, please select at least one.\n')
    scopes.insert(0, u'email') # Email Display Scope, always included
    return (True, u'')

  num_scopes = len(OAUTH2_SCOPES)
  menu = OAUTH2_MENU % tuple(range(num_scopes))
  selected_scopes = []
  for scope in OAUTH2_SCOPES:
    if scope.get(u'offByDefault', False):
      selected_scopes.append(u' ')
    else:
      selected_scopes.append(u'*')
  scopes = []
  prompt = u'Please enter 0-{0}[a|r] or {1}: '.format(num_scopes-1, u'|'.join(OAUTH2_CMDS))
  message = u''
  while True:
    os.system([u'clear', u'cls'][GM_Globals[GM_WINDOWS]])
    if message:
      sys.stdout.write(message)
      message = u''
    sys.stdout.write(menu % tuple(selected_scopes))
    while True:
      choice = raw_input(prompt)
      if choice:
        selection = choice.lower()
        if selection.find(u'r') >= 0:
          mode = u'R'
          selection = selection.replace(u'r', u'')
        elif selection.find(u'a') >= 0:
          mode = u'A'
          selection = selection.replace(u'a', u'')
        else:
          mode = u' '
        if selection and selection.isdigit():
          selection = int(selection)
        if isinstance(selection, int) and selection < num_scopes:
          if mode == u'R':
            if u'readonly' not in OAUTH2_SCOPES[selection][u'subscopes']:
              sys.stdout.write(u'{0}Scope {1} does not support read-only mode!\n'.format(ERROR_PREFIX, selection))
              continue
          elif mode == u'A':
            if u'action' not in OAUTH2_SCOPES[selection][u'subscopes']:
              sys.stdout.write(u'{0}Scope {1} does not support action-only mode!\n'.format(ERROR_PREFIX, selection))
              continue
          elif selected_scopes[selection] != u'*':
            mode = u'*'
          else:
            mode = u' '
          selected_scopes[selection] = mode
          break
        elif isinstance(selection, str) and selection in OAUTH2_CMDS:
          if selection == u's':
            for i in range(num_scopes):
              selected_scopes[i] = u'*'
          elif selection == u'u':
            for i in range(num_scopes):
              selected_scopes[i] = u' '
          elif selection == u'e':
            return None
          break
        sys.stdout.write(u'{0}Invalid input "{1}"\n'.format(ERROR_PREFIX, choice))
    if selection == u'c':
      status, message = _checkMakeScopesList(scopes)
      if status:
        break
  return scopes

def init_gam_worker():
  signal.signal(signal.SIGINT, signal.SIG_IGN)

def run_batch(items):
  from multiprocessing import Pool
  if not items:
    return
  num_worker_threads = min(len(items), GC_Values[GC_NUM_THREADS])
  pool = Pool(num_worker_threads, init_gam_worker)
  sys.stderr.write(u'Using %s processes...\n' % num_worker_threads)
  try:
    results = []
    for item in items:
      if item[0] == u'commit-batch':
        sys.stderr.write(u'commit-batch - waiting for running processes to finish before proceeding\n')
        pool.close()
        pool.join()
        pool = Pool(num_worker_threads, init_gam_worker)
        sys.stderr.write(u'commit-batch - running processes finished, proceeding\n')
        continue
      results.append(pool.apply_async(ProcessGAMCommandMulti, [item]))
    pool.close()
    num_total = len(results)
    i = 1
    while True:
      num_done = 0
      for r in results:
        if r.ready():
          num_done += 1
      if num_done == num_total:
        break
      i += 1
      if i == 20:
        print u'Finished %s of %s processes.' % (num_done, num_total)
        i = 1
      time.sleep(1)
  except KeyboardInterrupt:
    pool.terminate()
  pool.join()

#
# Process command line arguments, find substitutions
# An argument containing instances of ~~xxx~~ has xxx replaced by the value of field xxx from the CSV file
# An argument containing exactly ~xxx is replaced by the value of field xxx from the CSV file
# Otherwise, the argument is preserved as is
#
# SubFields is a dictionary; the key is the argument number, the value is a list of tuples that mark
# the substition (fieldname, start, end).
# Example: update user '~User' address type work unstructured '~~Street~~, ~~City~~, ~~State~~ ~~ZIP~~' primary
# {2: [('User', 0, 5)], 7: [('Street', 0, 10), ('City', 12, 20), ('State', 22, 31), ('ZIP', 32, 39)]}
#
def getSubFields(i, fieldNames):
  subFields = {}
  PATTERN = re.compile(r'~~(.+?)~~')
  GAM_argv = []
  GAM_argvI = 0
  while i < len(sys.argv):
    myarg = sys.argv[i]
    if not myarg:
      GAM_argv.append(myarg)
    elif PATTERN.search(myarg):
      pos = 0
      while True:
        match = PATTERN.search(myarg, pos)
        if not match:
          break
        fieldName = match.group(1)
        if fieldName in fieldNames:
          subFields.setdefault(GAM_argvI, [])
          subFields[GAM_argvI].append((fieldName, match.start(), match.end()))
        else:
          csvFieldErrorExit(fieldName, fieldNames)
        pos = match.end()
      GAM_argv.append(myarg)
    elif myarg[0] == u'~':
      fieldName = myarg[1:]
      if fieldName in fieldNames:
        subFields[GAM_argvI] = [(fieldName, 0, len(myarg))]
        GAM_argv.append(myarg)
      else:
        csvFieldErrorExit(fieldName, fieldNames)
    else:
      GAM_argv.append(myarg)
    GAM_argvI += 1
    i += 1
  return(GAM_argv, subFields)
#
def processSubFields(GAM_argv, row, subFields):
  argv = GAM_argv[:]
  for GAM_argvI, fields in subFields.iteritems():
    oargv = argv[GAM_argvI][:]
    argv[GAM_argvI] = u''
    pos = 0
    for field in fields:
      argv[GAM_argvI] += oargv[pos:field[1]]
      if row[field[0]]:
        argv[GAM_argvI] += row[field[0]]
      pos = field[2]
    argv[GAM_argvI] += oargv[pos:]
  return argv

def runCmdForUsers(cmd, users, default_to_batch=False, **kwargs):
  if default_to_batch and len(users) > 1:
    items = []
    for user in users:
      items.append([u'gam', u'user', user] + sys.argv[3:])
    run_batch(items)
    sys.exit(0)
  else:
    cmd(users, **kwargs)

def resetDefaultEncodingToUTF8():
  if sys.getdefaultencoding().upper() != u'UTF-8':
    reload(sys)
    if hasattr(sys, u'setdefaultencoding'):
      sys.setdefaultencoding(u'UTF-8')

def ProcessGAMCommandMulti(args):
  resetDefaultEncodingToUTF8()
  ProcessGAMCommand(args)

# Process GAM command
def ProcessGAMCommand(args):
  if args != sys.argv:
    sys.argv = args[:]
  GM_Globals[GM_SYSEXITRC] = 0
  try:
    SetGlobalVariables()
    command = sys.argv[1].lower()
    if command == u'batch':
      import shlex
      i = 2
      filename = sys.argv[i]
      i, encoding = getCharSet(i+1)
      f = openFile(filename)
      batchFile = UTF8Recoder(f, encoding) if encoding != u'utf-8' else f
      items = []
      errors = 0
      for line in batchFile:
        try:
          argv = shlex.split(line)
        except ValueError as e:
          sys.stderr.write(utils.convertUTF8(u'Command: >>>{0}<<<\n'.format(line.strip())))
          sys.stderr.write(u'{0}{1}\n'.format(ERROR_PREFIX, str(e)))
          errors += 1
          continue
        if len(argv) > 0:
          cmd = argv[0].strip().lower()
          if (not cmd) or cmd.startswith(u'#') or ((len(argv) == 1) and (cmd != u'commit-batch')):
            continue
          if cmd == u'gam':
            items.append(argv)
          elif cmd == u'commit-batch':
            items.append([cmd])
          else:
            sys.stderr.write(utils.convertUTF8(u'Command: >>>{0}<<<\n'.format(line.strip())))
            sys.stderr.write(u'{0}Invalid: Expected <gam|commit-batch>\n'.format(ERROR_PREFIX))
            errors += 1
      closeFile(f)
      if errors == 0:
        run_batch(items)
        sys.exit(0)
      else:
        sys.stderr.write(u'{0}batch file: {1}, not processed, {2} error{3}\n'.format(ERROR_PREFIX, filename, errors, [u'', u's'][errors != 1]))
        sys.exit(2)
    elif command == u'csv':
      if httplib2.debuglevel > 0:
        print u'Sorry, CSV commands are not compatible with debug. Delete debug.gam and try again.'
        sys.exit(1)
      i = 2
      filename = sys.argv[i]
      i, encoding = getCharSet(i+1)
      f = openFile(filename, mode=u'rbU')
      csvFile = UnicodeDictReader(f, encoding=encoding)
      if (i == len(sys.argv)) or (sys.argv[i].lower() != u'gam') or (i+1 == len(sys.argv)):
        systemErrorExit(3, '"gam csv <filename>" must be followed by a full GAM command...')
      i += 1
      GAM_argv, subFields = getSubFields(i, csvFile.fieldnames)
      items = []
      for row in csvFile:
        items.append([u'gam']+processSubFields(GAM_argv, row, subFields))
      closeFile(f)
      run_batch(items)
      sys.exit(0)
    elif command == u'version':
      doGAMVersion()
      sys.exit(0)
    elif command == u'create':
      argument = sys.argv[2].lower()
      if argument == u'user':
        doCreateUser()
      elif argument == u'group':
        doCreateGroup()
      elif argument in [u'nickname', u'alias']:
        doCreateAlias()
      elif argument in [u'org', u'ou']:
        doCreateOrg()
      elif argument == u'resource':
        doCreateResourceCalendar()
      elif argument in [u'verify', u'verification']:
        doSiteVerifyShow()
      elif argument == u'schema':
        doCreateOrUpdateUserSchema(False)
      elif argument in [u'course', u'class']:
        doCreateCourse()
      elif argument in [u'transfer', u'datatransfer']:
        doCreateDataTransfer()
      elif argument == u'domain':
        doCreateDomain()
      elif argument in [u'domainalias', u'aliasdomain']:
        doCreateDomainAlias()
      elif argument == u'admin':
        doCreateAdmin()
      elif argument in [u'guardianinvite', u'inviteguardian', u'guardian']:
        doInviteGuardian()
      elif argument in [u'project', u'apiproject']:
        try:
          login_hint = sys.argv[3]
        except IndexError:
          login_hint = None
        doCreateProject(login_hint)
      elif argument in [u'resoldcustomer', u'resellercustomer']:
        doCreateResoldCustomer()
      elif argument in [u'resoldsubscription', u'resellersubscription']:
        doCreateResoldSubscription()
      elif argument in [u'matter', u'vaultmatter']:
        doCreateVaultMatter()
      elif argument in [u'hold', u'vaulthold']:
        doCreateVaultHold()
      elif argument in [u'building']:
        doCreateBuilding()
      elif argument in [u'feature']:
        doCreateFeature()
      else:
        systemErrorExit(2, '%s is not a valid argument for "gam create"' % argument)
      sys.exit(0)
    elif command == u'update':
      argument = sys.argv[2].lower()
      if argument == u'user':
        doUpdateUser(None, 4)
      elif argument == u'group':
        doUpdateGroup()
      elif argument in [u'nickname', u'alias']:
        doUpdateAlias()
      elif argument in [u'ou', u'org']:
        doUpdateOrg()
      elif argument == u'resource':
        doUpdateResourceCalendar()
      elif argument == u'cros':
        doUpdateCros()
      elif argument == u'mobile':
        doUpdateMobile()
      elif argument in [u'notification', u'notifications']:
        doUpdateNotification()
      elif argument in [u'verify', u'verification']:
        doSiteVerifyAttempt()
      elif argument in [u'schema', u'schemas']:
        doCreateOrUpdateUserSchema(True)
      elif argument in [u'course', u'class']:
        doUpdateCourse()
      elif argument in [u'printer', u'print']:
        doUpdatePrinter()
      elif argument == u'domain':
        doUpdateDomain()
      elif argument == u'customer':
        doUpdateCustomer()
      elif argument in [u'resoldcustomer', u'resellercustomer']:
        doUpdateResoldCustomer()
      elif argument in [u'resoldsubscription', u'resellersubscription']:
        doUpdateResoldSubscription()
      elif argument in [u'matter', u'vaultmatter']:
        doUpdateVaultMatter()
      elif argument in [u'hold', u'vaulthold']:
        doUpdateVaultHold()
      elif argument in [u'project', u'apiproject']:
        try:
          login_hint = sys.argv[3]
        except IndexError:
          login_hint = None
        doUpdateProject(login_hint)
      elif argument in [u'building']:
        doUpdateBuilding()
      elif argument in [u'feature']:
        doUpdateFeature()
      else:
        systemErrorExit(2, '%s is not a valid argument for "gam update"' % argument)
      sys.exit(0)
    elif command == u'info':
      argument = sys.argv[2].lower()
      if argument == u'user':
        doGetUserInfo()
      elif argument == u'group':
        doGetGroupInfo()
      elif argument in [u'nickname', u'alias']:
        doGetAliasInfo()
      elif argument == u'instance':
        doGetCustomerInfo()
      elif argument in [u'org', u'ou']:
        doGetOrgInfo()
      elif argument == u'resource':
        doGetResourceCalendarInfo()
      elif argument == u'cros':
        doGetCrosInfo()
      elif argument == u'mobile':
        doGetMobileInfo()
      elif argument in [u'notifications', u'notification']:
        doGetNotifications()
      elif argument in [u'verify', u'verification']:
        doGetSiteVerifications()
      elif argument in [u'schema', u'schemas']:
        doGetUserSchema()
      elif argument in [u'course', u'class']:
        doGetCourseInfo()
      elif argument in [u'printer', u'print']:
        doGetPrinterInfo()
      elif argument in [u'transfer', u'datatransfer']:
        doGetDataTransferInfo()
      elif argument == u'customer':
        doGetCustomerInfo()
      elif argument == u'domain':
        doGetDomainInfo()
      elif argument in [u'domainalias', u'aliasdomain']:
        doGetDomainAliasInfo()
      elif argument in [u'resoldcustomer', u'resellercustomer']:
        doGetResoldCustomer()
      elif argument in [u'resoldsubscription', u'resoldsubscriptions', u'resellersubscription', u'resellersubscriptions']:
        doGetResoldSubscriptions()
      elif argument in [u'matter', u'vaultmatter']:
        doGetVaultMatterInfo()
      elif argument in [u'hold', u'vaulthold']:
        doGetVaultHoldInfo()
      elif argument in [u'building']:
        doGetBuildingInfo()
      else:
        systemErrorExit(2, '%s is not a valid argument for "gam info"' % argument)
      sys.exit(0)
    elif command == u'cancel':
      argument = sys.argv[2].lower()
      if argument in [u'guardianinvitation', u'guardianinvitations']:
        doCancelGuardianInvitation()
      else:
        systemErrorExit(2, '%s is not a valid argument for "gam cancel"' % argument)
      sys.exit(0)
    elif command == u'delete':
      argument = sys.argv[2].lower()
      if argument == u'user':
        doDeleteUser()
      elif argument == u'group':
        doDeleteGroup()
      elif argument in [u'nickname', u'alias']:
        doDeleteAlias()
      elif argument == u'org':
        doDeleteOrg()
      elif argument == u'resource':
        doDeleteResourceCalendar()
      elif argument == u'mobile':
        doDeleteMobile()
      elif argument in [u'notification', u'notifications']:
        doDeleteNotification()
      elif argument in [u'schema', u'schemas']:
        doDelSchema()
      elif argument in [u'course', u'class']:
        doDelCourse()
      elif argument in [u'printer', u'printers']:
        doDelPrinter()
      elif argument == u'domain':
        doDelDomain()
      elif argument in [u'domainalias', u'aliasdomain']:
        doDelDomainAlias()
      elif argument == u'admin':
        doDelAdmin()
      elif argument in [u'guardian', u'guardians']:
        doDeleteGuardian()
      elif argument in [u'project', u'projects']:
        try:
          login_hint = sys.argv[3]
        except IndexError:
          login_hint = None
        doDelProjects(login_hint)
      elif argument in [u'resoldsubscription', u'resellersubscription']:
        doDeleteResoldSubscription()
      elif argument in [u'matter', u'vaultmatter']:
        doUpdateVaultMatter(action=command)
      elif argument in [u'hold', u'vaulthold']:
        doDeleteVaultHold()
      elif argument in [u'building']:
        doDeleteBuilding()
      elif argument in [u'feature']:
        doDeleteFeature()
      else:
        systemErrorExit(2, '%s is not a valid argument for "gam delete"' % argument)
      sys.exit(0)
    elif command == u'undelete':
      argument = sys.argv[2].lower()
      if argument == u'user':
        doUndeleteUser()
      elif argument in [u'matter', u'vaultmatter']:
        doUpdateVaultMatter(action=command)
      else:
        systemErrorExit(2, '%s is not a valid argument for "gam undelete"' % argument)
      sys.exit(0)
    elif command in [u'close', u'reopen']:
      # close and reopen will have to be split apart if either takes a new argument
      argument = sys.argv[2].lower()
      if argument in [u'matter', u'vaultmatter']:
        doUpdateVaultMatter(action=command)
      else:
        systemErrorExit(2, '%s is not a valid argument for "gam %s"' % (argument, command))
      sys.exit(0)
    elif command == u'print':
      argument = sys.argv[2].lower().replace(u'-', u'')
      if argument == u'users':
        doPrintUsers()
      elif argument in [u'nicknames', u'aliases']:
        doPrintAliases()
      elif argument == u'groups':
        doPrintGroups()
      elif argument in [u'groupmembers', u'groupsmembers']:
        doPrintGroupMembers()
      elif argument in [u'orgs', u'ous']:
        doPrintOrgs()
      elif argument == u'resources':
        doPrintResourceCalendars()
      elif argument == u'cros':
        doPrintCrosDevices()
      elif argument == u'crosactivity':
        doPrintCrosActivity()
      elif argument == u'mobile':
        doPrintMobileDevices()
      elif argument in [u'license', u'licenses', u'licence', u'licences']:
        doPrintLicenses()
      elif argument in [u'token', u'tokens', u'oauth', u'3lo']:
        printShowTokens(3, None, None, True)
      elif argument in [u'schema', u'schemas']:
        doPrintShowUserSchemas(True)
      elif argument in [u'courses', u'classes']:
        doPrintCourses()
      elif argument in [u'courseparticipants', u'classparticipants']:
        doPrintCourseParticipants()
      elif argument == u'printers':
        doPrintPrinters()
      elif argument == u'printjobs':
        doPrintPrintJobs()
      elif argument in [u'transfers', u'datatransfers']:
        doPrintDataTransfers()
      elif argument == u'transferapps':
        doPrintTransferApps()
      elif argument == u'domains':
        doPrintDomains()
      elif argument in [u'domainaliases', u'aliasdomains']:
        doPrintDomainAliases()
      elif argument == u'admins':
        doPrintAdmins()
      elif argument in [u'roles', u'adminroles']:
        doPrintAdminRoles()
      elif argument in [u'guardian', u'guardians']:
        doPrintShowGuardians(True)
      elif argument in [u'matters', u'vaultmatters']:
        doPrintVaultMatters()
      elif argument in [u'holds', u'vaultholds']:
        doPrintVaultHolds()
      elif argument in [u'building', u'buildings']:
        doPrintBuildings()
      elif argument in [u'feature', u'features']:
        doPrintFeatures()
      else:
        systemErrorExit(2, '%s is not a valid argument for "gam print"' % argument)
      sys.exit(0)
    elif command == u'show':
      argument = sys.argv[2].lower()
      if argument in [u'schema', u'schemas']:
        doPrintShowUserSchemas(False)
      elif argument in [u'guardian', u'guardians']:
        doPrintShowGuardians(False)
      else:
        systemErrorExit(2, '%s is not a valid argument for "gam show"' % argument)
      sys.exit(0)
    elif command in [u'oauth', u'oauth2']:
      argument = sys.argv[2].lower()
      if argument in [u'request', u'create']:
        try:
          login_hint = sys.argv[3]
        except IndexError:
          login_hint = None
        doRequestOAuth(login_hint)
      elif argument in [u'info', u'verify']:
        OAuthInfo()
      elif argument in [u'delete', u'revoke']:
        doDeleteOAuth()
      else:
        systemErrorExit(2, '%s is not a valid argument for "gam oauth"' % argument)
      sys.exit(0)
    elif command == u'calendar':
      argument = sys.argv[3].lower()
      if argument == u'showacl':
        doCalendarShowACL()
      elif argument == u'add':
        doCalendarAddACL()
      elif argument in [u'del', u'delete']:
        doCalendarDelACL()
      elif argument == u'update':
        doCalendarUpdateACL()
      elif argument == u'wipe':
        doCalendarWipeData()
      elif argument == u'addevent':
        doCalendarAddEvent()
      elif argument == u'deleteevent':
        doCalendarDeleteEvent()
      else:
        systemErrorExit(2, '%s is not a valid argument for "gam calendar"' % argument)
      sys.exit(0)
    elif command == u'printer':
      if sys.argv[2].lower() == u'register':
        doPrinterRegister()
        sys.exit(0)
      argument = sys.argv[3].lower()
      if argument == u'showacl':
        doPrinterShowACL()
      elif argument == u'add':
        doPrinterAddACL()
      elif argument in [u'del', u'delete', u'remove']:
        doPrinterDelACL()
      else:
        systemErrorExit(2, '%s is not a valid argument for "gam printer..."' % argument)
      sys.exit(0)
    elif command == u'printjob':
      argument = sys.argv[3].lower()
      if argument == u'delete':
        doDeletePrintJob()
      elif argument == u'cancel':
        doCancelPrintJob()
      elif argument == u'submit':
        doPrintJobSubmit()
      elif argument == u'fetch':
        doPrintJobFetch()
      elif argument == u'resubmit':
        doPrintJobResubmit()
      else:
        systemErrorExit(2, '%s is not a valid argument for "gam printjob"' % argument)
      sys.exit(0)
    elif command == u'report':
      showReport()
      sys.exit(0)
    elif command == u'whatis':
      doWhatIs()
      sys.exit(0)
    elif command in [u'course', u'class']:
      argument = sys.argv[3].lower()
      if argument in [u'add', u'create']:
        doAddCourseParticipant()
      elif argument in [u'del', u'delete', u'remove']:
        doDelCourseParticipant()
      elif argument == u'sync':
        doSyncCourseParticipants()
      else:
        systemErrorExit(2, '%s is not a valid argument for "gam course"' % argument)
      sys.exit(0)
    users = getUsersToModify()
    command = sys.argv[3].lower()
    if command == u'print' and len(sys.argv) == 4:
      for user in users:
        print user
      sys.exit(0)
    if (GC_Values[GC_AUTO_BATCH_MIN] > 0) and (len(users) > GC_Values[GC_AUTO_BATCH_MIN]):
      runCmdForUsers(None, users, True)
    if command == u'transfer':
      transferWhat = sys.argv[4].lower()
      if transferWhat == u'drive':
        transferDriveFiles(users)
      elif transferWhat == u'seccals':
        transferSecCals(users)
      else:
        systemErrorExit(2, '%s is not a valid argument for "gam <users> transfer"' % transferWhat)
    elif command == u'show':
      showWhat = sys.argv[4].lower()
      if showWhat in [u'labels', u'label']:
        showLabels(users)
      elif showWhat == u'profile':
        showProfile(users)
      elif showWhat == u'calendars':
        printShowCalendars(users, False)
      elif showWhat == u'calsettings':
        showCalSettings(users)
      elif showWhat == u'drivesettings':
        printDriveSettings(users)
      elif showWhat == u'teamdrivethemes':
        getTeamDriveThemes(users)
      elif showWhat == u'drivefileacl':
        showDriveFileACL(users)
      elif showWhat == u'filelist':
        printDriveFileList(users)
      elif showWhat == u'filetree':
        showDriveFileTree(users)
      elif showWhat == u'fileinfo':
        showDriveFileInfo(users)
      elif showWhat == u'filerevisions':
        showDriveFileRevisions(users)
      elif showWhat == u'sendas':
        printShowSendAs(users, False)
      elif showWhat == u'smime':
        printShowSmime(users, False)
      elif showWhat == u'gmailprofile':
        showGmailProfile(users)
      elif showWhat == u'gplusprofile':
        showGplusProfile(users)
      elif showWhat in [u'sig', u'signature']:
        getSignature(users)
      elif showWhat == u'forward':
        printShowForward(users, False)
      elif showWhat in [u'pop', u'pop3']:
        getPop(users)
      elif showWhat in [u'imap', u'imap4']:
        getImap(users)
      elif showWhat == u'vacation':
        getVacation(users)
      elif showWhat in [u'delegate', u'delegates']:
        printShowDelegates(users, False)
      elif showWhat in [u'backupcode', u'backupcodes', u'verificationcodes']:
        doGetBackupCodes(users)
      elif showWhat in [u'asp', u'asps', u'applicationspecificpasswords']:
        doGetASPs(users)
      elif showWhat in [u'token', u'tokens', u'oauth', u'3lo']:
        printShowTokens(5, u'users', users, False)
      elif showWhat == u'driveactivity':
        printDriveActivity(users)
      elif showWhat in [u'filter', u'filters']:
        printShowFilters(users, False)
      elif showWhat in [u'forwardingaddress', u'forwardingaddresses']:
        printShowForwardingAddresses(users, False)
      elif showWhat in [u'teamdrive', u'teamdrives']:
        printShowTeamDrives(users, False)
      elif showWhat in [u'teamdriveinfo']:
        doGetTeamDriveInfo(users)
      else:
        systemErrorExit(2, '%s is not a valid argument for "gam <users> show"' % showWhat)
    elif command == u'print':
      printWhat = sys.argv[4].lower()
      if printWhat == u'calendars':
        printShowCalendars(users, True)
      elif printWhat in [u'delegate', u'delegates']:
        printShowDelegates(users, True)
      elif printWhat == u'driveactivity':
        printDriveActivity(users)
      elif printWhat == u'drivesettings':
        printDriveSettings(users)
      elif printWhat == u'filelist':
        printDriveFileList(users)
      elif printWhat in [u'filter', u'filters']:
        printShowFilters(users, True)
      elif printWhat == u'forward':
        printShowForward(users, True)
      elif printWhat in [u'forwardingaddress', u'forwardingaddresses']:
        printShowForwardingAddresses(users, True)
      elif printWhat == u'sendas':
        printShowSendAs(users, True)
      elif printWhat == u'smime':
        printShowSmime(users, True)
      elif printWhat in [u'token', u'tokens', u'oauth', u'3lo']:
        printShowTokens(5, u'users', users, True)
      elif printWhat in [u'teamdrive', u'teamdrives']:
        printShowTeamDrives(users, True)
      else:
        systemErrorExit(2, '%s is not a valid argument for "gam <users> print"' % printWhat)
    elif command == u'modify':
      modifyWhat = sys.argv[4].lower()
      if modifyWhat in [u'message', u'messages']:
        doProcessMessagesOrThreads(users, u'modify', u'messages')
      elif modifyWhat in [u'thread', u'threads']:
        doProcessMessagesOrThreads(users, u'modify', u'threads')
      else:
        systemErrorExit(2, '%s is not a valid argument for "gam <users> modify"' % modifyWhat)
    elif command == u'trash':
      trashWhat = sys.argv[4].lower()
      if trashWhat in [u'message', u'messages']:
        doProcessMessagesOrThreads(users, u'trash', u'messages')
      elif trashWhat in [u'thread', u'threads']:
        doProcessMessagesOrThreads(users, u'trash', u'threads')
      else:
        systemErrorExit(2, '%s is not a valid argument for "gam <users> trash"' % trashWhat)
    elif command == u'untrash':
      untrashWhat = sys.argv[4].lower()
      if untrashWhat in [u'message', u'messages']:
        doProcessMessagesOrThreads(users, u'untrash', u'messages')
      elif untrashWhat in [u'thread', u'threads']:
        doProcessMessagesOrThreads(users, u'untrash', u'threads')
      else:
        systemErrorExit(2, '%s is not a valid argument for "gam <users> untrash"' % untrashWhat)
    elif command in [u'delete', u'del']:
      delWhat = sys.argv[4].lower()
      if delWhat == u'delegate':
        deleteDelegate(users)
      elif delWhat == u'calendar':
        deleteCalendar(users)
      elif delWhat == u'label':
        doDeleteLabel(users)
      elif delWhat in [u'message', u'messages']:
        runCmdForUsers(doProcessMessagesOrThreads, users, default_to_batch=True, function=u'delete', unit=u'messages')
      elif delWhat in [u'thread', u'threads']:
        runCmdForUsers(doProcessMessagesOrThreads, users, default_to_batch=True, function=u'delete', unit=u'threads')
      elif delWhat == u'photo':
        deletePhoto(users)
      elif delWhat in [u'license', u'licence']:
        doLicense(users, u'delete')
      elif delWhat in [u'backupcode', u'backupcodes', u'verificationcodes']:
        doDelBackupCodes(users)
      elif delWhat in [u'asp', u'asps', u'applicationspecificpasswords']:
        doDelASP(users)
      elif delWhat in [u'token', u'tokens', u'oauth', u'3lo']:
        doDelTokens(users)
      elif delWhat in [u'group', u'groups']:
        deleteUserFromGroups(users)
      elif delWhat in [u'alias', u'aliases']:
        doRemoveUsersAliases(users)
      elif delWhat == u'emptydrivefolders':
        deleteEmptyDriveFolders(users)
      elif delWhat == u'drivefile':
        deleteDriveFile(users)
      elif delWhat in [u'drivefileacl', u'drivefileacls']:
        delDriveFileACL(users)
      elif delWhat in [u'filter', u'filters']:
        deleteFilters(users)
      elif delWhat in [u'forwardingaddress', u'forwardingaddresses']:
        deleteForwardingAddresses(users)
      elif delWhat == u'sendas':
        deleteSendAs(users)
      elif delWhat == u'smime':
        deleteSmime(users)
      elif delWhat == u'teamdrive':
        doDeleteTeamDrive(users)
      else:
        systemErrorExit(2, '%s is not a valid argument for "gam <users> delete"' % delWhat)
    elif command in [u'add', u'create']:
      addWhat = sys.argv[4].lower()
      if addWhat == u'calendar':
        if command == u'add':
          addCalendar(users)
        else:
          systemErrorExit(2, '%s is not implemented for "gam <users> %s"' % (addWhat, command))
      elif addWhat == u'drivefile':
        createDriveFile(users)
      elif addWhat in [u'license', u'licence']:
        doLicense(users, u'insert')
      elif addWhat in [u'drivefileacl', u'drivefileacls']:
        addDriveFileACL(users)
      elif addWhat in [u'label', u'labels']:
        doLabel(users, 5)
      elif addWhat in [u'delegate', u'delegates']:
        addDelegates(users, 5)
      elif addWhat in [u'filter', u'filters']:
        addFilter(users, 5)
      elif addWhat in [u'forwardingaddress', u'forwardingaddresses']:
        addForwardingAddresses(users)
      elif addWhat == u'sendas':
        addUpdateSendAs(users, 5, True)
      elif addWhat == u'smime':
        addSmime(users)
      elif addWhat == u'teamdrive':
        doCreateTeamDrive(users)
      else:
        systemErrorExit(2, '%s is not a valid argument for "gam <users> %s"' % (addWhat, command))
    elif command == u'update':
      updateWhat = sys.argv[4].lower()
      if updateWhat == u'calendar':
        updateCalendar(users)
      elif updateWhat == u'calattendees':
        changeCalendarAttendees(users)
      elif updateWhat == u'photo':
        doPhoto(users)
      elif updateWhat in [u'license', u'licence']:
        doLicense(users, u'patch')
      elif updateWhat == u'user':
        doUpdateUser(users, 5)
      elif updateWhat in [u'backupcode', u'backupcodes', u'verificationcodes']:
        doGenBackupCodes(users)
      elif updateWhat == u'drivefile':
        doUpdateDriveFile(users)
      elif updateWhat in [u'drivefileacls', u'drivefileacl']:
        updateDriveFileACL(users)
      elif updateWhat in [u'label', u'labels']:
        renameLabels(users)
      elif updateWhat == u'labelsettings':
        updateLabels(users)
      elif updateWhat == u'sendas':
        addUpdateSendAs(users, 5, False)
      elif updateWhat == u'smime':
        updateSmime(users)
      elif updateWhat == u'teamdrive':
        doUpdateTeamDrive(users)
      else:
        systemErrorExit(2, '%s is not a valid argument for "gam <users> update"' % updateWhat)
    elif command in [u'deprov', u'deprovision']:
      doDeprovUser(users)
    elif command == u'get':
      getWhat = sys.argv[4].lower()
      if getWhat == u'photo':
        getPhoto(users)
      elif getWhat == u'drivefile':
        downloadDriveFile(users)
      else:
        systemErrorExit(2, '%s is not a valid argument for "gam <users> get"' % getWhat)
    elif command == u'empty':
      emptyWhat = sys.argv[4].lower()
      if emptyWhat == u'drivetrash':
        doEmptyDriveTrash(users)
      else:
        systemErrorExit(2, '%s is not a valid argument for "gam <users> empty"' % emptyWhat)
    elif command == u'info':
      infoWhat = sys.argv[4].lower()
      if infoWhat == u'calendar':
        infoCalendar(users)
      elif infoWhat in [u'filter', u'filters']:
        infoFilters(users)
      elif infoWhat in [u'forwardingaddress', u'forwardingaddresses']:
        infoForwardingAddresses(users)
      elif infoWhat == u'sendas':
        infoSendAs(users)
      else:
        systemErrorExit(2, '%s is not a valid argument for "gam <users> info"' % infoWhat)
    elif command == u'check':
      checkWhat = sys.argv[4].replace(u'_', '').lower()
      if checkWhat == u'serviceaccount':
        doCheckServiceAccount(users)
      else:
        systemErrorExit(2, '%s is not a valid argument for "gam <users> check"' % checkWhat)
    elif command == u'profile':
      doProfile(users)
    elif command == u'imap':
      #doImap(users)
      runCmdForUsers(doImap, users, default_to_batch=True)
    elif command in [u'pop', u'pop3']:
      doPop(users)
    elif command == u'sendas':
      addUpdateSendAs(users, 4, True)
    elif command == u'label':
      doLabel(users, 4)
    elif command == u'filter':
      addFilter(users, 4)
    elif command == u'forward':
      doForward(users)
    elif command in [u'sig', u'signature']:
      doSignature(users)
    elif command == u'vacation':
      doVacation(users)
    elif command in [u'delegate', u'delegates']:
      addDelegates(users, 4)
    elif command == u'watch':
      if len(sys.argv) > 4:
        watchWhat = sys.argv[4].lower()
      else:
        watchWhat = u'gmail'
      if watchWhat == u'gmail':
        watchGmail(users)
      else:
        systemErrorExit(2, '%s is not a valid argument for "gam <users> watch"' % watchWhat)
    else:
      systemErrorExit(2, '%s is not a valid argument for "gam"' % command)
  except IndexError:
    showUsage()
    sys.exit(2)
  except KeyboardInterrupt:
    sys.exit(50)
  except socket.error as e:
    systemErrorExit(3, str(e))
  except MemoryError:
    systemErrorExit(99, MESSAGE_GAM_OUT_OF_MEMORY)
  except SystemExit as e:
    GM_Globals[GM_SYSEXITRC] = e.code
  return GM_Globals[GM_SYSEXITRC]

if sys.platform.startswith('win'):
  from multiprocessing import freeze_support

  def win32_unicode_argv():
    from ctypes import POINTER, byref, cdll, c_int, windll
    from ctypes.wintypes import LPCWSTR, LPWSTR

    GetCommandLineW = cdll.kernel32.GetCommandLineW
    GetCommandLineW.argtypes = []
    GetCommandLineW.restype = LPCWSTR

    CommandLineToArgvW = windll.shell32.CommandLineToArgvW
    CommandLineToArgvW.argtypes = [LPCWSTR, POINTER(c_int)]
    CommandLineToArgvW.restype = POINTER(LPWSTR)

    cmd = GetCommandLineW()
    argc = c_int(0)
    argv = CommandLineToArgvW(cmd, byref(argc))
    if argc.value > 0:
      # Remove Python executable and commands if present
      argc_value = int(argc.value)
      sys.argv = argv[argc_value-len(sys.argv):argc_value]

# Run from command line
if __name__ == "__main__":
  resetDefaultEncodingToUTF8()
  if sys.platform.startswith('win'):
    freeze_support()
    win32_unicode_argv() # cleanup sys.argv on Windows
  if sys.version_info[:2] != (2, 7):
    systemErrorExit(5, 'GAM requires Python 2.7. You are running %s.%s.%s. Please upgrade your Python version or use one of the binary GAM downloads.' % sys.version_info[:3])
  sys.exit(ProcessGAMCommand(sys.argv))
