#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# GAM
#
# Copyright 2019, LLC All Rights Reserved.
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
"""GAM is a command line tool which allows Administrators to control their G Suite domain and accounts.

With GAM you can programatically create users, turn on/off services for users like POP and Forwarding and much more.
For more information, see https://git.io/gam
"""

import base64
import codecs
import configparser
import csv
import datetime
import hashlib
import importlib
import io
import json
import mimetypes
import os
import platform
import random
import re
import shlex
import signal
import socket
import ssl
import string
import struct
import sys
import time
import uuid
import webbrowser
import zipfile
import http.client as http_client
from email.mime.text import MIMEText
from multiprocessing import Pool
from multiprocessing import freeze_support
from urllib.parse import urlencode
from passlib.hash import sha512_crypt
import dns.resolver
import dateutil.parser

import googleapiclient
import googleapiclient.discovery
import googleapiclient.errors
import googleapiclient.http
import google.oauth2.service_account
import google_auth_httplib2
import httplib2
import oauth2client.client
import oauth2client.file
import oauth2client.tools
from oauth2client.contrib.dictionary_storage import DictionaryStorage

import utils
from var import *

# Finding path method varies between Python source, PyInstaller and StaticX
if os.environ.get('STATICX_PROG_PATH', False):
  # StaticX static executable
  GM_Globals[GM_GAM_PATH] = os.path.dirname(os.environ['STATICX_PROG_PATH'])
  # Pyinstaller executable
elif getattr(sys, 'frozen', False):
  GM_Globals[GM_GAM_PATH] = os.path.dirname(sys.executable)
else:
  # Source code
  GM_Globals[GM_GAM_PATH] = os.path.dirname(os.path.realpath(__file__))

# override httplib2._build_ssl_context so we can force min/max TLS values
# actual function replacement happens in SetGlobalVariables so we have config options set
def _build_ssl_context(disable_ssl_certificate_validation, ca_certs, cert_file=None, key_file=None):
  context = ssl.SSLContext(httplib2.DEFAULT_TLS_VERSION)
  context.verify_mode = ssl.CERT_REQUIRED
  context.check_hostname = True
  context.load_verify_locations(ca_certs)
  if cert_file:
    context.load_cert_chain(cert_file, key_file)
  if GC_Values[GC_TLS_MIN_VERSION]:
    context.minimum_version = getattr(ssl.TLSVersion, GC_Values[GC_TLS_MIN_VERSION])
  if GC_Values[GC_TLS_MAX_VERSION]:
    context.maximum_version = getattr(ssl.TLSVersion, GC_Values[GC_TLS_MAX_VERSION])
  return context

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
          kwargs['headers']['user-agent'] = '%s %s' % (GAM_USER_AGENT, kwargs['headers']['user-agent'])
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
  print('''
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

''')
#
# Error handling
#
def stderrErrorMsg(message):
  sys.stderr.write(utils.convertUTF8('\n{0}{1}\n'.format(ERROR_PREFIX, message)))

def stderrWarningMsg(message):
  sys.stderr.write(utils.convertUTF8('\n{0}{1}\n'.format(WARNING_PREFIX, message)))

def systemErrorExit(sysRC, message):
  if message:
    stderrErrorMsg(message)
  sys.exit(sysRC)

def invalidJSONExit(fileName):
  systemErrorExit(17, MESSAGE_INVALID_JSON.format(fileName))

def currentCount(i, count):
  return ' ({0}/{1})'.format(i, count) if (count > GC_Values[GC_SHOW_COUNTS_MIN]) else ''

def currentCountNL(i, count):
  return ' ({0}/{1})\n'.format(i, count) if (count > GC_Values[GC_SHOW_COUNTS_MIN]) else '\n'

def formatHTTPError(http_status, reason, message):
  return '{0}: {1} - {2}'.format(http_status, reason, message)

def getHTTPError(responses, http_status, reason, message):
  if reason in responses:
    return responses[reason]
  return formatHTTPError(http_status, reason, message)

def printGettingAllItems(items, query):
  if query:
    sys.stderr.write("Getting all {0} in G Suite account that match query ({1}) (may take some time on a large account)...\n".format(items, query))
  else:
    sys.stderr.write("Getting all {0} in G Suite account (may take some time on a large account)...\n".format(items))

def entityServiceNotApplicableWarning(entityType, entityName, i, count):
  sys.stderr.write('{0}: {1}, Service not applicable/Does not exist{2}'.format(entityType, entityName, currentCountNL(i, count)))

def entityDoesNotExistWarning(entityType, entityName, i, count):
  sys.stderr.write('{0}: {1}, Does not exist{2}'.format(entityType, entityName, currentCountNL(i, count)))

def entityUnknownWarning(entityType, entityName, i, count):
  domain = getEmailAddressDomain(entityName)
  if (domain == GC_Values[GC_DOMAIN]) or (domain.endswith('google.com')):
    entityDoesNotExistWarning(entityType, entityName, i, count)
  else:
    entityServiceNotApplicableWarning(entityType, entityName, i, count)

# Invalid CSV ~Header or ~~Header~~
def csvFieldErrorExit(fieldName, fieldNames):
  systemErrorExit(2, MESSAGE_HEADER_NOT_FOUND_IN_CSV_HEADERS.format(fieldName, ','.join(fieldNames)))

def printLine(message):
  sys.stdout.write(message+'\n')
#
def getBoolean(value, item):
  value = value.lower()
  if value in true_values:
    return True
  if value in false_values:
    return False
  systemErrorExit(2, 'Value for {0} must be {1} or {2}; got {3}'.format(item, '|'.join(true_values), '|'.join(false_values), value))

def getCharSet(i):
  if (i == len(sys.argv)) or (sys.argv[i].lower() != 'charset'):
    return (i, GC_Values.get(GC_CHARSET, GM_Globals[GM_SYS_ENCODING]))
  return (i+2, sys.argv[i+1])

def supportsColoredText():
  """Determines if the current terminal environment supports colored text.

  Returns:
    Bool, True if the current terminal environment supports colored text via
    ANSI escape characters.
  """
  # Make a rudimentary check for Windows. Though Windows does seem to support
  # colorization with VT100 emulation, it is disabled by default. Therefore,
  # we'll simply disable it in GAM on Windows for now.
  return not GM_Globals[GM_WINDOWS]

def createColoredText(text, color):
  """Uses ANSI escape characters to create colored text in supported terminals.

  See more at https://en.wikipedia.org/wiki/ANSI_escape_code#Colors

  Args:
    text: String, The text to colorize using ANSI escape characters.
    color: String, An ANSI escape sequence denoting the color of the text to be
      created. See more at https://en.wikipedia.org/wiki/ANSI_escape_code#Colors

  Returns:
    The input text with appropriate ANSI escape characters to create
    colorization in a supported terminal environment.
  """
  END_COLOR_SEQUENCE = '\033[0m'  # Ends the applied color formatting
  if supportsColoredText():
    return color + text + END_COLOR_SEQUENCE
  return text # Hand back the plain text, uncolorized.

def createRedText(text):
  """Uses ANSI encoding to create red colored text, if supported."""
  return createColoredText(text, '\033[91m')

COLORHEX_PATTERN = re.compile(r'^#[0-9a-fA-F]{6}$')

def getColor(color):
  color = color.lower().strip()
  if color in WEBCOLOR_MAP:
    return WEBCOLOR_MAP[color]
  tg = COLORHEX_PATTERN.match(color)
  if tg:
    return tg.group(0)
  systemErrorExit(2, 'A color must be a valid name or # and six hex characters (#012345); got {0}'.format(color))

def getLabelColor(color):
  color = color.lower().strip()
  tg = COLORHEX_PATTERN.match(color)
  if tg:
    color = tg.group(0)
    if color in LABEL_COLORS:
      return color
    systemErrorExit(2, 'A label color must be in the list: {0}; got {1}'.format('|'.join(LABEL_COLORS), color))
  systemErrorExit(2, 'A label color must be # and six hex characters (#012345); got {0}'.format(color))

def integerLimits(minVal, maxVal, item='integer'):
  if (minVal is not None) and (maxVal is not None):
    return '{0} {1}<=x<={2}'.format(item, minVal, maxVal)
  if minVal is not None:
    return '{0} x>={1}'.format(item, minVal)
  if maxVal is not None:
    return '{0} x<={1}'.format(item, maxVal)
  return '{0} x'.format(item)

def getInteger(value, item, minVal=None, maxVal=None):
  try:
    number = int(value.strip())
    if ((minVal is None) or (number >= minVal)) and ((maxVal is None) or (number <= maxVal)):
      return number
  except ValueError:
    pass
  systemErrorExit(2, 'expected {0} in range <{1}>, got {2}'.format(item, integerLimits(minVal, maxVal), value))

def removeCourseIdScope(courseId):
  if courseId.startswith('d:'):
    return courseId[2:]
  return courseId

def addCourseIdScope(courseId):
  if not courseId.isdigit() and courseId[:2] != 'd:':
    return 'd:{0}'.format(courseId)
  return courseId

def getString(i, item, optional=False, minLen=1, maxLen=None):
  if i < len(sys.argv):
    argstr = sys.argv[i]
    if argstr:
      if (len(argstr) >= minLen) and ((maxLen is None) or (len(argstr) <= maxLen)):
        return argstr
      systemErrorExit(2, 'expected <{0} for {1}>'.format(integerLimits(minLen, maxLen, 'string length'), item))
    if optional or (minLen == 0):
      return ''
    systemErrorExit(2, 'expected a Non-empty <{0}>'.format(item))
  elif optional:
    return ''
  systemErrorExit(2, 'expected a <{0}>'.format(item))

def getDelta(argstr, pattern):
  tg = pattern.match(argstr.lower())
  if tg is None:
    return None
  sign = tg.group(1)
  delta = int(tg.group(2))
  unit = tg.group(3)
  if unit == 'y':
    deltaTime = datetime.timedelta(days=delta*365)
  elif unit == 'w':
    deltaTime = datetime.timedelta(weeks=delta)
  elif unit == 'd':
    deltaTime = datetime.timedelta(days=delta)
  elif unit == 'h':
    deltaTime = datetime.timedelta(hours=delta)
  elif unit == 'm':
    deltaTime = datetime.timedelta(minutes=delta)
  if sign == '-':
    return -deltaTime
  return deltaTime

DELTA_DATE_PATTERN = re.compile(r'^([+-])(\d+)([dwy])$')
DELTA_DATE_FORMAT_REQUIRED = '(+|-)<Number>(d|w|y)'

def getDeltaDate(argstr):
  deltaDate = getDelta(argstr, DELTA_DATE_PATTERN)
  if deltaDate is None:
    systemErrorExit(2, 'expected a <{0}>; got {1}'.format(DELTA_DATE_FORMAT_REQUIRED, argstr))
  return deltaDate

DELTA_TIME_PATTERN = re.compile(r'^([+-])(\d+)([mhdw])$')
DELTA_TIME_FORMAT_REQUIRED = '(+|-)<Number>(m|h|d|w)'

def getDeltaTime(argstr):
  deltaTime = getDelta(argstr, DELTA_TIME_PATTERN)
  if deltaTime is None:
    systemErrorExit(2, 'expected a <{0}>; got {1}'.format(DELTA_TIME_FORMAT_REQUIRED, argstr))
  return deltaTime

YYYYMMDD_FORMAT = '%Y-%m-%d'
YYYYMMDD_FORMAT_REQUIRED = 'yyyy-mm-dd'

def getYYYYMMDD(argstr, minLen=1, returnTimeStamp=False, returnDateTime=False):
  argstr = argstr.strip()
  if argstr:
    if argstr[0] in ['+', '-']:
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
      systemErrorExit(2, 'expected a <{0}>; got {1}'.format(YYYYMMDD_FORMAT_REQUIRED, argstr))
  elif minLen == 0:
    return ''
  systemErrorExit(2, 'expected a <{0}>'.format(YYYYMMDD_FORMAT_REQUIRED))

YYYYMMDDTHHMMSS_FORMAT_REQUIRED = 'yyyy-mm-ddThh:mm:ss[.fff](Z|(+|-(hh:mm)))'

def getTimeOrDeltaFromNow(time_string):
  """Get an ISO 8601 time or a positive/negative delta applied to now.
  Args:
    time_string (string): The time or delta (e.g. '2017-09-01T12:34:56Z' or '-4h')
  Returns:
    string: iso8601 formatted datetime in UTC.
  """
  time_string = time_string.strip().upper()
  if time_string:
    if time_string[0] not in ['+', '-']:
      return time_string
    return (datetime.datetime.utcnow() + getDeltaTime(time_string)).isoformat() + 'Z'
  systemErrorExit(2, 'expected a <{0}>'.format(YYYYMMDDTHHMMSS_FORMAT_REQUIRED))

def getRowFilterDateOrDeltaFromNow(date_string):
  """Get an ISO 8601 date or a positive/negative delta applied to now.
  Args:
    date_string (string): The time or delta (e.g. '2017-09-01' or '-4y')
  Returns:
    string: iso8601 formatted datetime in UTC.
  """
  date_string = date_string.strip().upper()
  if date_string:
    if date_string[0] in ['+', '-']:
      deltaDate = getDelta(date_string, DELTA_DATE_PATTERN)
      if deltaDate is None:
        return (False, DELTA_DATE_FORMAT_REQUIRED)
      today = datetime.date.today()
      return (True, (datetime.datetime(today.year, today.month, today.day)+deltaDate).isoformat()+'Z')
    try:
      deltaDate = dateutil.parser.parse(date_string, ignoretz=True)
      return (True, datetime.datetime(deltaDate.year, deltaDate.month, deltaDate.day).isoformat()+'Z')
    except ValueError:
      pass
  return (False, YYYYMMDD_FORMAT_REQUIRED)

def getRowFilterTimeOrDeltaFromNow(time_string):
  """Get an ISO 8601 time or a positive/negative delta applied to now.
  Args:
    time_string (string): The time or delta (e.g. '2017-09-01T12:34:56Z' or '-4h')
  Returns:
    string: iso8601 formatted datetime in UTC.
  Exits:
    2: Not a valid delta.
  """
  time_string = time_string.strip().upper()
  if time_string:
    if time_string[0] in ['+', '-']:
      deltaTime = getDelta(time_string, DELTA_TIME_PATTERN)
      if deltaTime is None:
        return (False, DELTA_TIME_FORMAT_REQUIRED)
      return (True, (datetime.datetime.utcnow()+deltaTime).isoformat()+'Z')
    try:
      deltaTime = dateutil.parser.parse(time_string, ignoretz=True)
      return (True, deltaTime.isoformat()+'Z')
    except ValueError:
      pass
  return (False, YYYYMMDDTHHMMSS_FORMAT_REQUIRED)

YYYYMMDD_PATTERN = re.compile(r'^[0-9]{4}-[0-9]{2}-[0-9]{2}$')

def getDateZeroTimeOrFullTime(time_string):
  time_string = time_string.strip()
  if time_string:
    if YYYYMMDD_PATTERN.match(time_string):
      return getYYYYMMDD(time_string)+'T00:00:00.000Z'
    return getTimeOrDeltaFromNow(time_string)
  systemErrorExit(2, 'expected a <{0}>'.format(YYYYMMDDTHHMMSS_FORMAT_REQUIRED))

# Get domain from email address
def getEmailAddressDomain(emailAddress):
  atLoc = emailAddress.find('@')
  if atLoc == -1:
    return GC_Values[GC_DOMAIN].lower()
  return emailAddress[atLoc+1:].lower()

# Split email address unto user and domain
def splitEmailAddress(emailAddress):
  atLoc = emailAddress.find('@')
  if atLoc == -1:
    return (emailAddress.lower(), GC_Values[GC_DOMAIN].lower())
  return (emailAddress[:atLoc].lower(), emailAddress[atLoc+1:].lower())

UID_PATTERN = re.compile(r'u?id: ?(.+)', re.IGNORECASE)

# Normalize user/group email address/uid
# uid:12345abc -> 12345abc
# foo -> foo@domain
# foo@ -> foo@domain
# foo@bar.com -> foo@bar.com
# @domain -> domain
def normalizeEmailAddressOrUID(emailAddressOrUID, noUid=False, checkForCustomerId=False, noLower=False):
  if checkForCustomerId and (emailAddressOrUID == GC_Values[GC_CUSTOMER_ID]):
    return emailAddressOrUID
  if not noUid:
    cg = UID_PATTERN.match(emailAddressOrUID)
    if cg:
      return cg.group(1)
  atLoc = emailAddressOrUID.find('@')
  if atLoc == 0:
    return emailAddressOrUID[1:].lower() if not noLower else emailAddressOrUID[1:]
  if (atLoc == -1) or (atLoc == len(emailAddressOrUID)-1) and GC_Values[GC_DOMAIN]:
    if atLoc == -1:
      emailAddressOrUID = '{0}@{1}'.format(emailAddressOrUID, GC_Values[GC_DOMAIN])
    else:
      emailAddressOrUID = '{0}{1}'.format(emailAddressOrUID, GC_Values[GC_DOMAIN])
  return emailAddressOrUID.lower() if not noLower else emailAddressOrUID

# Normalize student/guardian email address/uid
# 12345678 -> 12345678
# - -> -
# Otherwise, same results as normalizeEmailAddressOrUID
def normalizeStudentGuardianEmailAddressOrUID(emailAddressOrUID):
  if emailAddressOrUID.isdigit() or emailAddressOrUID == '-':
    return emailAddressOrUID
  return normalizeEmailAddressOrUID(emailAddressOrUID)
#
# Open a file
#
def openFile(filename, mode='r', encoding=GM_Globals[GM_SYS_ENCODING], newline=None):
  try:
    if filename != '-':
      if 'b' in mode:
        return open(os.path.expanduser(filename), mode)
      return open(os.path.expanduser(filename), mode, encoding=encoding, newline=newline)
    if mode.startswith('r'):
      return io.StringIO(str(sys.stdin.read()))
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
def readFile(filename, mode='r', continueOnError=False, displayError=True, encoding=None):
  try:
    if filename != '-':
      if not encoding or 'b' in mode:
        with open(os.path.expanduser(filename), mode) as f:
          return f.read()
      with codecs.open(os.path.expanduser(filename), mode, encoding) as f:
        content = f.read()
# codecs does not strip UTF-8 BOM (ef:bb:bf) so we must
        if not content.startswith(str(codecs.BOM_UTF8)):
          return content
        return content[3:]
    return str(sys.stdin.read())
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
def writeFile(filename, data, mode='w', continueOnError=False, displayError=True):
  try:
    kwargs = {'encoding': GM_Globals[GM_SYS_ENCODING]} if 'b' not in mode else {}
    with open(os.path.expanduser(filename), mode, **kwargs) as f:
      f.write(data)
    return True
  except IOError as e:
    if continueOnError:
      if displayError:
        stderrErrorMsg(e)
      return False
    systemErrorExit(6, e)
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

  ROW_FILTER_COMP_PATTERN = re.compile(r'^(date|time|count)\s*([<>]=?|=|!=)\s*(.+)$', re.IGNORECASE)
  ROW_FILTER_BOOL_PATTERN = re.compile(r'^(boolean):(.+)$', re.IGNORECASE)
  ROW_FILTER_RE_PATTERN = re.compile(r'^(regex):(.+)$', re.IGNORECASE)

  def _getCfgRowFilter(itemName):
    value = GC_Defaults[itemName]
    rowFilters = {}
    if not value:
      return rowFilters
    try:
      for column, filterStr in iter(json.loads(value).items()):
        mg = ROW_FILTER_COMP_PATTERN.match(filterStr)
        if mg:
          if mg.group(1) in ['date', 'time']:
            if mg.group(1) == 'date':
              valid, filterValue = getRowFilterDateOrDeltaFromNow(mg.group(3))
            else:
              valid, filterValue = getRowFilterTimeOrDeltaFromNow(mg.group(3))
            if valid:
              rowFilters[column] = (mg.group(1), mg.group(2), filterValue)
              continue
            systemErrorExit(3, 'Item: {0}, Value: "{1}": "{2}", Expected: {3}'.format(itemName, column, filterStr, filterValue))
          else: #count
            if mg.group(3).isdigit():
              rowFilters[column] = (mg.group(1), mg.group(2), int(mg.group(3)))
              continue
            systemErrorExit(3, 'Item: {0}, Value: "{1}": "{2}", Expected: {3}'.format(itemName, column, filterStr, '<Number>'))
        mg = ROW_FILTER_BOOL_PATTERN.match(filterStr)
        if mg:
          value = mg.group(2).lower()
          if value in true_values:
            filterValue = True
          elif value in false_values:
            filterValue = False
          else:
            systemErrorExit(3, 'Item: {0}, Value: "{1}": "{2}", Expected true|false'.format(itemName, column, filterStr))
          rowFilters[column] = (mg.group(1), filterValue)
          continue
        mg = ROW_FILTER_RE_PATTERN.match(filterStr)
        if mg:
          try:
            rowFilters[column] = (mg.group(1), re.compile(mg.group(2)))
            continue
          except re.error as e:
            systemErrorExit(3, 'Item: {0}, Value: "{1}": {2}, Invalid RE: {3}'.format(itemName, column, filterStr, e))
        systemErrorExit(3, 'Item: {0}, Value: "{1}": {2}, Expected: (date|time|count<Operator><Value>) or (boolean:true|false) or (regex:<RegularExpression>)'.format(itemName, column, filterStr))
      return rowFilters
    except (TypeError, ValueError) as e:
      systemErrorExit(3, 'Item: {0}, Value: "{1}", Failed to parse as JSON: {2}'.format(itemName, value, str(e)))

  GC_Defaults[GC_CONFIG_DIR] = GM_Globals[GM_GAM_PATH]
  GC_Defaults[GC_CACHE_DIR] = os.path.join(GM_Globals[GM_GAM_PATH], 'gamcache')
  GC_Defaults[GC_DRIVE_DIR] = GM_Globals[GM_GAM_PATH]
  GC_Defaults[GC_SITE_DIR] = GM_Globals[GM_GAM_PATH]

  _getOldEnvVar(GC_CONFIG_DIR, 'GAMUSERCONFIGDIR')
  _getOldEnvVar(GC_SITE_DIR, 'GAMSITECONFIGDIR')
  _getOldEnvVar(GC_CACHE_DIR, 'GAMCACHEDIR')
  _getOldEnvVar(GC_DRIVE_DIR, 'GAMDRIVEDIR')
  _getOldEnvVar(GC_OAUTH2_TXT, 'OAUTHFILE')
  _getOldEnvVar(GC_OAUTH2SERVICE_JSON, 'OAUTHSERVICEFILE')
  if GC_Defaults[GC_OAUTH2SERVICE_JSON].find('.') == -1:
    GC_Defaults[GC_OAUTH2SERVICE_JSON] += '.json'
  _getOldEnvVar(GC_CLIENT_SECRETS_JSON, 'CLIENTSECRETS')
  _getOldEnvVar(GC_DOMAIN, 'GA_DOMAIN')
  _getOldEnvVar(GC_CUSTOMER_ID, 'CUSTOMER_ID')
  _getOldEnvVar(GC_CHARSET, 'GAM_CHARSET')
  _getOldEnvVar(GC_NUM_THREADS, 'GAM_THREADS')
  _getOldEnvVar(GC_ACTIVITY_MAX_RESULTS, 'GAM_ACTIVITY_MAX_RESULTS')
  _getOldEnvVar(GC_AUTO_BATCH_MIN, 'GAM_AUTOBATCH')
  _getOldEnvVar(GC_BATCH_SIZE, 'GAM_BATCH_SIZE')
  _getOldEnvVar(GC_DEVICE_MAX_RESULTS, 'GAM_DEVICE_MAX_RESULTS')
  _getOldEnvVar(GC_DRIVE_MAX_RESULTS, 'GAM_DRIVE_MAX_RESULTS')
  _getOldEnvVar(GC_MEMBER_MAX_RESULTS, 'GAM_MEMBER_MAX_RESULTS')
  _getOldEnvVar(GC_USER_MAX_RESULTS, 'GAM_USER_MAX_RESULTS')
  _getOldEnvVar(GC_CSV_HEADER_FILTER, 'GAM_CSV_HEADER_FILTER')
  _getOldEnvVar(GC_CSV_ROW_FILTER, 'GAM_CSV_ROW_FILTER')
  _getOldEnvVar(GC_TLS_MIN_VERSION, 'GAM_TLS_MIN_VERSION')
  _getOldEnvVar(GC_TLS_MAX_VERSION, 'GAM_TLS_MAX_VERSION')
  _getOldSignalFile(GC_DEBUG_LEVEL, 'debug.gam', filePresentValue=4, fileAbsentValue=0)
  _getOldSignalFile(GC_NO_VERIFY_SSL, 'noverifyssl.txt')
  _getOldSignalFile(GC_NO_BROWSER, 'nobrowser.txt')
#  _getOldSignalFile(GC_NO_CACHE, u'nocache.txt')
#  _getOldSignalFile(GC_CACHE_DISCOVERY_ONLY, u'allcache.txt', filePresentValue=False, fileAbsentValue=True)
  _getOldSignalFile(GC_NO_CACHE, 'allcache.txt', filePresentValue=False, fileAbsentValue=True)
  _getOldSignalFile(GC_NO_UPDATE_CHECK, 'noupdatecheck.txt')
# Assign directories first
  for itemName in GC_VAR_INFO:
    if GC_VAR_INFO[itemName][GC_VAR_TYPE] == GC_TYPE_DIRECTORY:
      GC_Values[itemName] = _getCfgDirectory(itemName)
  for itemName in GC_VAR_INFO:
    varType = GC_VAR_INFO[itemName][GC_VAR_TYPE]
    if varType == GC_TYPE_FILE:
      GC_Values[itemName] = _getCfgFile(itemName)
    elif varType == GC_TYPE_ROWFILTER:
      GC_Values[itemName] = _getCfgRowFilter(itemName)
    else:
      GC_Values[itemName] = GC_Defaults[itemName]
  GM_Globals[GM_LAST_UPDATE_CHECK_TXT] = os.path.join(GC_Values[GC_CONFIG_DIR], FN_LAST_UPDATE_CHECK_TXT)
  if not GC_Values[GC_NO_UPDATE_CHECK]:
    doGAMCheckForUpdates()
# Globals derived from config file values
  GM_Globals[GM_OAUTH2SERVICE_JSON_DATA] = None
  GM_Globals[GM_OAUTH2SERVICE_ACCOUNT_CLIENT_ID] = None
  GM_Globals[GM_EXTRA_ARGS_DICT] = {'prettyPrint': GC_Values[GC_DEBUG_LEVEL] > 0}
# override httplib2 settings
  httplib2.debuglevel = GC_Values[GC_DEBUG_LEVEL]
  httplib2._build_ssl_context = _build_ssl_context
  if os.path.isfile(os.path.join(GC_Values[GC_CONFIG_DIR], FN_EXTRA_ARGS_TXT)):
    ea_config = configparser.ConfigParser()
    ea_config.optionxform = str
    ea_config.read(os.path.join(GC_Values[GC_CONFIG_DIR], FN_EXTRA_ARGS_TXT))
    GM_Globals[GM_EXTRA_ARGS_DICT].update(dict(ea_config.items('extra-args')))
  if GC_Values[GC_NO_CACHE]:
    GM_Globals[GM_CACHE_DIR] = None
    GM_Globals[GM_CACHE_DISCOVERY_ONLY] = False
  else:
    GM_Globals[GM_CACHE_DIR] = GC_Values[GC_CACHE_DIR]
#    GM_Globals[GM_CACHE_DISCOVERY_ONLY] = GC_Values[GC_CACHE_DISCOVERY_ONLY]
    GM_Globals[GM_CACHE_DISCOVERY_ONLY] = False
  return True

def doGAMCheckForUpdates(forceCheck=False):

  def _gamLatestVersionNotAvailable():
    if forceCheck:
      systemErrorExit(4, 'GAM Latest Version information not available')

  current_version = gam_version
  now_time = int(time.time())
  if forceCheck:
    check_url = GAM_ALL_RELEASES # includes pre-releases
  else:
    last_check_time_str = readFile(GM_Globals[GM_LAST_UPDATE_CHECK_TXT], continueOnError=True, displayError=False)
    last_check_time = int(last_check_time_str) if last_check_time_str and last_check_time_str.isdigit() else 0
    if last_check_time > now_time-604800:
      return
    check_url = GAM_LATEST_RELEASE # latest full release
  headers = {'Accept': 'application/vnd.github.v3.text+json'}
  simplehttp = httplib2.Http(disable_ssl_certificate_validation=GC_Values[GC_NO_VERIFY_SSL])
  try:
    (_, c) = simplehttp.request(check_url, 'GET', headers=headers)
    try:
      release_data = json.loads(c.decode('utf-8'))
    except ValueError:
      _gamLatestVersionNotAvailable()
      return
    if isinstance(release_data, list):
      release_data = release_data[0] # only care about latest release
    if not isinstance(release_data, dict) or 'tag_name' not in release_data:
      _gamLatestVersionNotAvailable()
      return
    latest_version = release_data['tag_name']
    if latest_version[0].lower() == 'v':
      latest_version = latest_version[1:]
    if forceCheck or (latest_version > current_version):
      print('Version Check:\n Current: {0}\n Latest: {1}'.format(current_version, latest_version))
    if latest_version <= current_version:
      writeFile(GM_Globals[GM_LAST_UPDATE_CHECK_TXT], str(now_time), continueOnError=True, displayError=forceCheck)
      return
    announcement = release_data.get('body_text', 'No details about this release')
    sys.stderr.write('\nGAM %s release notes:\n\n' % latest_version)
    sys.stderr.write(announcement)
    try:
      printLine(MESSAGE_HIT_CONTROL_C_TO_UPDATE)
      time.sleep(15)
    except KeyboardInterrupt:
      webbrowser.open(release_data['html_url'])
      printLine(MESSAGE_GAM_EXITING_FOR_UPDATE)
      sys.exit(0)
    writeFile(GM_Globals[GM_LAST_UPDATE_CHECK_TXT], str(now_time), continueOnError=True, displayError=forceCheck)
    return
  except (httplib2.HttpLib2Error, httplib2.ServerNotFoundError):
    return

def doGAMVersion(checkForArgs=True):
  force_check = False
  simple = False
  extended = False
  if checkForArgs:
    i = 2
    while i < len(sys.argv):
      myarg = sys.argv[i].lower().replace('_', '')
      if myarg == 'check':
        force_check = True
        i += 1
      elif myarg == 'simple':
        simple = True
        i += 1
      elif myarg == 'extended':
        extended = True
        i += 1
      else:
        systemErrorExit(2, '%s is not a valid argument for "gam version"' % sys.argv[i])
  if simple:
    sys.stdout.write(gam_version)
    return
  version_data = 'GAM {0} - {1}\n{2}\nPython {3}.{4}.{5} {6}-bit {7}\ngoogle-api-python-client {8}\noauth2client {9}\n{10} {11}\nPath: {12}'
  print(version_data.format(gam_version, GAM_URL, gam_author, sys.version_info[0],
                            sys.version_info[1], sys.version_info[2], struct.calcsize('P')*8,
                            sys.version_info[3], googleapiclient.__version__, oauth2client.__version__, platform.platform(),
                            platform.machine(), GM_Globals[GM_GAM_PATH]))
  if force_check:
    doGAMCheckForUpdates(forceCheck=True)
  if extended:
    print(ssl.OPENSSL_VERSION)
    httpc = httplib2.Http()
    httpc.request('https://www.googleapis.com')
    cipher_name, tls_ver, _ = httpc.connections['https:www.googleapis.com'].sock.cipher()
    print('www.googleapis.com connects using %s %s' % (tls_ver, cipher_name))

def handleOAuthTokenError(e, soft_errors):
  if e.replace('.', '') in OAUTH2_TOKEN_ERRORS or e.startswith('Invalid response'):
    if soft_errors:
      return None
    if not GM_Globals[GM_CURRENT_API_USER]:
      stderrErrorMsg(MESSAGE_API_ACCESS_DENIED.format(GM_Globals[GM_OAUTH2SERVICE_ACCOUNT_CLIENT_ID],
                                                      ','.join(GM_Globals[GM_CURRENT_API_SCOPES])))
      systemErrorExit(12, MESSAGE_API_ACCESS_CONFIG)
    else:
      systemErrorExit(19, MESSAGE_SERVICE_NOT_APPLICABLE.format(GM_Globals[GM_CURRENT_API_USER]))
  systemErrorExit(18, 'Authentication Token Error - {0}'.format(e))

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
    sys.stderr.write('Temporary error: {0}, Backing off: {1} seconds, Retry: {2}/{3}\n'.format(errMsg, int(wait_on_fail), n, retries))
    sys.stderr.flush()
  time.sleep(wait_on_fail)

def checkGAPIError(e, soft_errors=False, silent_errors=False, retryOnHttpError=False, service=None):
  try:
    error = json.loads(e.content.decode('utf-8'))
  except ValueError:
    if (e.resp['status'] == '503') and (e.content == 'Quota exceeded for the current request'):
      return (e.resp['status'], GAPI_QUOTA_EXCEEDED, e.content)
    if (e.resp['status'] == '403') and (e.content.startswith('Request rate higher than configured')):
      return (e.resp['status'], GAPI_QUOTA_EXCEEDED, e.content)
    if (e.resp['status'] == '403') and ('Invalid domain.' in e.content):
      error = {'error': {'code': 403, 'errors': [{'reason': GAPI_NOT_FOUND, 'message': 'Domain not found'}]}}
    elif (e.resp['status'] == '400') and ('InvalidSsoSigningKey' in e.content):
      error = {'error': {'code': 400, 'errors': [{'reason': GAPI_INVALID, 'message': 'InvalidSsoSigningKey'}]}}
    elif (e.resp['status'] == '400') and ('UnknownError' in e.content):
      error = {'error': {'code': 400, 'errors': [{'reason': GAPI_INVALID, 'message': 'UnknownError'}]}}
    elif retryOnHttpError:
      service._http.request.credentials.refresh(httplib2.Http(disable_ssl_certificate_validation=GC_Values[GC_NO_VERIFY_SSL]))
      return (-1, None, None)
    elif soft_errors:
      if not silent_errors:
        stderrErrorMsg(e.content)
      return (0, None, None)
    else:
      systemErrorExit(5, e.content)
  if 'error' in error:
    http_status = error['error']['code']
    try:
      message = error['error']['errors'][0]['message']
    except KeyError:
      message = error['error']['message']
  else:
    if 'error_description' in error:
      if error['error_description'] == 'Invalid Value':
        message = error['error_description']
        http_status = 400
        error = {'error': {'errors': [{'reason': GAPI_INVALID, 'message': message}]}}
      else:
        systemErrorExit(4, str(error))
    else:
      systemErrorExit(4, str(error))
  try:
    reason = error['error']['errors'][0]['reason']
    if reason == 'notFound':
      if 'userKey' in message:
        reason = GAPI_USER_NOT_FOUND
      elif 'groupKey' in message:
        reason = GAPI_GROUP_NOT_FOUND
      elif 'memberKey' in message:
        reason = GAPI_MEMBER_NOT_FOUND
      elif 'Domain not found' in message:
        reason = GAPI_DOMAIN_NOT_FOUND
      elif 'Resource Not Found' in message:
        reason = GAPI_RESOURCE_NOT_FOUND
    elif reason == 'invalid':
      if 'userId' in message:
        reason = GAPI_USER_NOT_FOUND
      elif 'memberKey' in message:
        reason = GAPI_INVALID_MEMBER
    elif reason == 'failedPrecondition':
      if 'Bad Request' in message:
        reason = GAPI_BAD_REQUEST
      elif 'Mail service not enabled' in message:
        reason = GAPI_SERVICE_NOT_AVAILABLE
    elif reason == 'required':
      if 'memberKey' in message:
        reason = GAPI_MEMBER_NOT_FOUND
    elif reason == 'conditionNotMet':
      if 'Cyclic memberships not allowed' in message:
        reason = GAPI_CYCLIC_MEMBERSHIPS_NOT_ALLOWED
  except KeyError:
    reason = '{0}'.format(http_status)
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
class GAPI_permissionDenied(Exception):
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
  GAPI_PERMISSION_DENIED: GAPI_permissionDenied,
  GAPI_RESOURCE_NOT_FOUND: GAPI_resourceNotFound,
  GAPI_SERVICE_NOT_AVAILABLE: GAPI_serviceNotAvailable,
  GAPI_USER_NOT_FOUND: GAPI_userNotFound,
  }

def callGAPI(service, function,
             silent_errors=False, soft_errors=False,
             throw_reasons=None, retry_reasons=None,
             **kwargs):
  """Executes a single request on a Google service function.

  Args:
    service: A Google service object for the desired API.
    function: String, The name of a service request method to execute.
    silent_errors: Bool, If True, error messages are suppressed when
        encountered.
    soft_errors: Bool, If True, writes non-fatal errors to stderr.
    throw_reasons: A list of Google HTTP error reason strings indicating the
        errors generated by this request should be re-thrown. All other HTTP
        errors are consumed.
    retry_reasons: A list of Google HTTP error reason strings indicating which
        error should be retried, using exponential backoff techniques, when the
        error reason is encountered.

  Returns:
    The given Google service function's response object.
  """
  if throw_reasons is None:
    throw_reasons = []
  if retry_reasons is None:
    retry_reasons = []

  method = getattr(service, function)
  retries = 10
  parameters = dict(list(kwargs.items()) + list(GM_Globals[GM_EXTRA_ARGS_DICT].items()))
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
        stderrErrorMsg('{0}: {1} - {2}{3}'.format(http_status, message, reason, ['', ': Giving up.'][n > 1]))
        return None
      systemErrorExit(int(http_status), '{0}: {1} - {2}'.format(http_status, message, reason))
    except oauth2client.client.AccessTokenRefreshError as e:
      handleOAuthTokenError(str(e), soft_errors or GAPI_SERVICE_NOT_AVAILABLE in throw_reasons)
      if GAPI_SERVICE_NOT_AVAILABLE in throw_reasons:
        raise GAPI_serviceNotAvailable(str(e))
      stderrErrorMsg('User {0}: {1}'.format(GM_Globals[GM_CURRENT_API_USER], str(e)))
      return None
    except ValueError as e:
      if service._http.cache is not None:
        service._http.cache = None
        continue
      systemErrorExit(4, str(e))
    except (TypeError, httplib2.ServerNotFoundError) as e:
      systemErrorExit(4, str(e))

def callGAPIpages(service, function, items='items',
                  page_message=None, message_attribute=None,
                  soft_errors=False, throw_reasons=None, retry_reasons=None,
                  **kwargs):
  """Aggregates and returns all pages of a Google service function response.

  All pages of items are aggregated and returned as a single list.

  Args:
    service: A Google service object for the desired API.
    function: String, The name of a service request method to execute.
    items: String, the name of the resulting "items" field within the method's
        response object. The items in this field will be aggregated across all
        pages and returned.
    page_message: String, a message to be displayed to the user during paging.
        Template strings allow for dynamic content to be inserted during paging.

        Supported template strings:
          %%num_items%%   : The number of items in the current page.
          %%total_items%% : The current number of items discovered across all
                            pages.
          %%first_item%%  : In conjunction with `message_attribute` arg, will
                            display a unique property of the first item in the
                            current page.
          %%last_item%%   : In conjunction with `message_attribute` arg, will
                            display a unique property of the last item in the
                            current page.

    message_attribute: String, the name of a signature field within a single
        returned item which identifies that unique item. This field is used with
        `page_message` to templatize a paging status message.
    soft_errors: Bool, If True, writes non-fatal errors to stderr.
    throw_reasons: A list of Google HTTP error reason strings indicating the
        errors generated by this request should be re-thrown. All other HTTP
        errors are consumed.
    retry_reasons: A list of Google HTTP error reason strings indicating which
        error should be retried, using exponential backoff techniques, when the
        error reason is encountered.

  Returns:
    A list of all items received from all paged responses.
  """
  all_items = []
  page_token = None
  total_items = 0
  while True:
    page = callGAPI(service,
                    function,
                    soft_errors=soft_errors,
                    throw_reasons=throw_reasons,
                    retry_reasons=retry_reasons,
                    pageToken=page_token,
                    **kwargs)
    if page:
      page_token = page.get('nextPageToken')
      page_items = page.get(items, [])
      num_page_items = len(page_items)
      total_items += num_page_items
      all_items.extend(page_items)
    else:
      page_token = None
      num_page_items = 0

    # Show a paging message to the user that indicates paging progress
    if page_message:
      show_message = page_message.replace('%%num_items%%', str(num_page_items))
      show_message = show_message.replace('%%total_items%%', str(total_items))
      if message_attribute:
        first_item = page_items[0] if num_page_items > 0 else {}
        last_item = page_items[-1] if num_page_items > 1 else first_item
        show_message = show_message.replace('%%first_item%%', str(first_item.get(message_attribute, '')))
        show_message = show_message.replace('%%last_item%%', str(last_item.get(message_attribute, '')))
      sys.stderr.write('\r')
      sys.stderr.flush()
      sys.stderr.write(show_message)

    if not page_token:
      # End the paging status message and return all items.
      if page_message and (page_message[-1] != '\n'):
        sys.stderr.write('\r\n')
        sys.stderr.flush()
      return all_items

def callGAPIitems(service, function, items='items',
                  throw_reasons=None, retry_reasons=None,
                  **kwargs):
  """Gets a single page of items from a Google service function that is paged.

  Args:
    service: A Google service object for the desired API.
    function: String, The name of a service request method to execute.
    items: String, the name of the resulting "items" field within the service
        method's response object.
    soft_errors: Bool, If True, writes non-fatal errors to stderr.
    throw_reasons: A list of Google HTTP error reason strings indicating the
        errors generated by this request should be re-thrown. All other HTTP
        errors are consumed.
    retry_reasons: A list of Google HTTP error reason strings indicating which
        error should be retried, using exponential backoff techniques, when the
        error reason is encountered.

  Returns:
    The list of items in the first page of a response.
  """
  results = callGAPI(service,
                     function,
                     throw_reasons=throw_reasons,
                     retry_reasons=retry_reasons,
                     **kwargs)
  if results:
    return results.get(items, [])
  return []

def getAPIVersion(api):
  version = API_VER_MAPPING.get(api, 'v1')
  if api in ['directory', 'reports', 'datatransfer']:
    api = 'admin'
  elif api == 'drive3':
    api = 'drive'
  return (api, version, '{0}-{1}'.format(api, version))

def readDiscoveryFile(api_version):
  disc_filename = '%s.json' % (api_version)
  disc_file = os.path.join(GM_Globals[GM_GAM_PATH], disc_filename)
  if hasattr(sys, '_MEIPASS'):
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
    try:
      credentials.refresh(http)
    except oauth2client.client.HttpAccessTokenRefreshError as e:
      systemErrorExit(18, str(e))
  return credentials

def getService(api, http):
  api, version, api_version = getAPIVersion(api)
  if api in GM_Globals[GM_CURRENT_API_SERVICES] and version in GM_Globals[GM_CURRENT_API_SERVICES][api]:
    service = googleapiclient.discovery.build_from_document(GM_Globals[GM_CURRENT_API_SERVICES][api][version], http=http)
    if GM_Globals[GM_CACHE_DISCOVERY_ONLY]:
      http.cache = None
    return service
  if api in V1_DISCOVERY_APIS:
    discoveryServiceUrl = googleapiclient.discovery.DISCOVERY_URI
  else:
    discoveryServiceUrl = googleapiclient.discovery.V2_DISCOVERY_URI
  retries = 3
  for n in range(1, retries+1):
    try:
      service = googleapiclient.discovery.build(api, version, http=http, cache_discovery=False, discoveryServiceUrl=discoveryServiceUrl)
      GM_Globals[GM_CURRENT_API_SERVICES].setdefault(api, {})
      GM_Globals[GM_CURRENT_API_SERVICES][api][version] = service._rootDesc.copy()
      if GM_Globals[GM_CACHE_DISCOVERY_ONLY]:
        http.cache = None
      return service
    except httplib2.ServerNotFoundError as e:
      systemErrorExit(4, str(e))
    except (googleapiclient.errors.InvalidJsonError, KeyError, ValueError) as e:
      http.cache = None
      if n != retries:
        waitOnFailure(n, retries, str(e))
        continue
      systemErrorExit(17, str(e))
    except (http_client.ResponseNotReady, socket.error) as e:
      if n != retries:
        waitOnFailure(n, retries, str(e))
        continue
      systemErrorExit(3, str(e))
    except googleapiclient.errors.UnknownApiNameOrVersion:
      break
  disc_file, discovery = readDiscoveryFile(api_version)
  try:
    service = googleapiclient.discovery.build_from_document(discovery, http=http)
    GM_Globals[GM_CURRENT_API_SERVICES].setdefault(api, {})
    GM_Globals[GM_CURRENT_API_SERVICES][api][version] = service._rootDesc.copy()
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
      resp, result = service._http.request('https://www.googleapis.com/admin/directory/v1/users?domain={0}&maxResults=1&fields=users(customerId)'.format(GC_Values[GC_DOMAIN]))
      try:
        resultObj = json.loads(result)
      except ValueError:
        systemErrorExit(8, 'Unexpected response: {0}'.format(result))
      if resp['status'] in ['403', '404']:
        try:
          message = resultObj['error']['errors'][0]['message']
        except KeyError:
          message = resultObj['error']['message']
        systemErrorExit(8, '{0} - {1}'.format(message, GC_Values[GC_DOMAIN]))
      try:
        GC_Values[GC_CUSTOMER_ID] = resultObj['users'][0]['customerId']
      except KeyError:
        GC_Values[GC_CUSTOMER_ID] = MY_CUSTOMER
  else:
    GC_Values[GC_DOMAIN] = _getValueFromOAuth('hd', credentials=credentials)
    if not GC_Values[GC_CUSTOMER_ID]:
      GC_Values[GC_CUSTOMER_ID] = MY_CUSTOMER
  return service

# Convert UID to email address
def convertUIDtoEmailAddress(emailAddressOrUID, cd=None, email_type='user'):
  normalizedEmailAddressOrUID = normalizeEmailAddressOrUID(emailAddressOrUID)
  if normalizedEmailAddressOrUID.find('@') > 0:
    return normalizedEmailAddressOrUID
  if not cd:
    cd = buildGAPIObject('directory')
  if email_type == 'user':
    try:
      result = callGAPI(cd.users(), 'get',
                        throw_reasons=[GAPI_USER_NOT_FOUND],
                        userKey=normalizedEmailAddressOrUID, fields='primaryEmail')
      if 'primaryEmail' in result:
        return result['primaryEmail'].lower()
    except GAPI_userNotFound:
      pass
  else:
    try:
      result = callGAPI(cd.groups(), 'get',
                        throw_reasons=[GAPI_GROUP_NOT_FOUND],
                        groupKey=normalizedEmailAddressOrUID, fields='email')
      if 'email' in result:
        return result['email'].lower()
    except GAPI_groupNotFound:
      pass
  return normalizedEmailAddressOrUID

# Convert email address to UID
def convertEmailAddressToUID(emailAddressOrUID, cd=None, email_type='user'):
  normalizedEmailAddressOrUID = normalizeEmailAddressOrUID(emailAddressOrUID)
  if normalizedEmailAddressOrUID.find('@') > 0:
    if not cd:
      cd = buildGAPIObject('directory')
    if email_type != 'group':
      try:
        result = callGAPI(cd.users(), 'get',
                          throw_reasons=[GAPI_USER_NOT_FOUND],
                          userKey=normalizedEmailAddressOrUID, fields='id')
        if 'id' in result:
          return result['id']
      except GAPI_userNotFound:
        pass
    try:
      result = callGAPI(cd.groups(), 'get',
                        throw_reasons=[GAPI_NOT_FOUND],
                        groupKey=normalizedEmailAddressOrUID, fields='id')
      if 'id' in result:
        return result['id']
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
      stderrErrorMsg('User {0}: {1}'.format(GM_Globals[GM_CURRENT_API_USER], str(e)))
    return handleOAuthTokenError(str(e), True)
  return service

def buildAlertCenterGAPIObject(user):
  userEmail = convertUIDtoEmailAddress(user)
  return (userEmail, buildGAPIServiceObject('alertcenter', userEmail))

def buildActivityGAPIObject(user):
  userEmail = convertUIDtoEmailAddress(user)
  return (userEmail, buildGAPIServiceObject('appsactivity', userEmail))

def normalizeCalendarId(calname, checkPrimary=False):
  calname = calname.lower()
  if checkPrimary and calname == 'primary':
    return calname
  if not GC_Values[GC_DOMAIN]:
    GC_Values[GC_DOMAIN] = _getValueFromOAuth('hd')
  return convertUIDtoEmailAddress(calname)

def buildCalendarGAPIObject(calname):
  calendarId = normalizeCalendarId(calname)
  return (calendarId, buildGAPIServiceObject('calendar', calendarId))

def buildCalendarDataGAPIObject(calname):
  calendarId = normalizeCalendarId(calname)
  # Force service account token request. If we fail fall back to using admin for authentication
  cal = buildGAPIServiceObject('calendar', calendarId, False)
  if cal is None:
    _, cal = buildCalendarGAPIObject(_getValueFromOAuth('email'))
  return (calendarId, cal)

def buildDriveGAPIObject(user):
  userEmail = convertUIDtoEmailAddress(user)
  return (userEmail, buildGAPIServiceObject('drive', userEmail))

def buildDrive3GAPIObject(user):
  userEmail = convertUIDtoEmailAddress(user)
  return (userEmail, buildGAPIServiceObject('drive3', userEmail))

def buildGmailGAPIObject(user):
  userEmail = convertUIDtoEmailAddress(user)
  return (userEmail, buildGAPIServiceObject('gmail', userEmail))

def doCheckServiceAccount(users):
  all_scopes = []
  for _, scopes in list(API_SCOPE_MAPPING.items()):
    for scope in scopes:
      if scope not in all_scopes:
        all_scopes.append(scope)
  all_scopes.sort()
  for user in users:
    all_scopes_pass = True
    print('User: %s' % (user))
    for scope in all_scopes:
      try:
        credentials = getSvcAcctCredentials([scope], user)
        request = google_auth_httplib2.Request(httplib2.Http(disable_ssl_certificate_validation=GC_Values[GC_NO_VERIFY_SSL]))
        credentials.refresh(request)
        result = 'PASS'
      except httplib2.ServerNotFoundError as e:
        systemErrorExit(4, e)
      except google.auth.exceptions.RefreshError:
        result = 'FAIL'
        all_scopes_pass = False
      print(' Scope: {0:60} {1}'.format(scope, result))
    service_account = GM_Globals[GM_OAUTH2SERVICE_ACCOUNT_CLIENT_ID]
    if all_scopes_pass:
      print('\nAll scopes passed!\nService account %s is fully authorized.' % service_account)
      return
    user_domain = user[user.find('@')+1:]
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

def batchRequestID(entityName, j, jcount, item, role=''):
  return '{0}\n{1}\n{2}\n{3}\n{4}'.format(entityName, j, jcount, item, role)

def _adjustDate(errMsg):
  match_date = re.match('Data for dates later than (.*) is not yet available. Please check back later', errMsg)
  if not match_date:
    match_date = re.match('Start date can not be later than (.*)', errMsg)
  if not match_date:
    systemErrorExit(4, errMsg)
  return str(match_date.group(1))

def _checkFullDataAvailable(warnings, tryDate, fullDataRequired):
  for warning in warnings:
    if warning['code'] == 'PARTIAL_DATA_AVAILABLE':
      for app in warning['data']:
        if app['key'] == 'application' and app['value'] != 'docs' and (not fullDataRequired or app['value'] in fullDataRequired):
          tryDateTime = datetime.datetime.strptime(tryDate, YYYYMMDD_FORMAT)-datetime.timedelta(days=1)
          return (0, tryDateTime.strftime(YYYYMMDD_FORMAT))
    elif warning['code'] == 'DATA_NOT_AVAILABLE':
      for app in warning['data']:
        if app['key'] == 'application' and app['value'] != 'docs' and (not fullDataRequired or app['value'] in fullDataRequired):
          return (-1, tryDate)
  return (1, tryDate)

def showReport():
  rep = buildGAPIObject('reports')
  report = sys.argv[2].lower()
  customerId = GC_Values[GC_CUSTOMER_ID]
  if customerId == MY_CUSTOMER:
    customerId = None
  filters = parameters = actorIpAddress = startTime = endTime = eventName = orgUnitId = None
  tryDate = datetime.date.today().strftime(YYYYMMDD_FORMAT)
  to_drive = False
  userKey = 'all'
  fullDataRequired = None
  i = 3
  while i < len(sys.argv):
    myarg = sys.argv[i].lower()
    if myarg == 'date':
      tryDate = getYYYYMMDD(sys.argv[i+1])
      i += 2
    elif myarg in ['orgunit', 'org', 'ou']:
      _, orgUnitId = getOrgUnitId(sys.argv[i+1])
      i += 2
    elif myarg == 'fulldatarequired':
      fullDataRequired = []
      fdr = sys.argv[i+1].lower()
      if fdr and fdr != 'all':
        fullDataRequired = fdr.replace(',', ' ').split()
      i += 2
    elif myarg == 'start':
      startTime = getTimeOrDeltaFromNow(sys.argv[i+1])
      i += 2
    elif myarg == 'end':
      endTime = getTimeOrDeltaFromNow(sys.argv[i+1])
      i += 2
    elif myarg == 'event':
      eventName = sys.argv[i+1]
      i += 2
    elif myarg == 'user':
      userKey = normalizeEmailAddressOrUID(sys.argv[i+1])
      i += 2
    elif myarg in ['filter', 'filters']:
      filters = sys.argv[i+1]
      i += 2
    elif myarg in ['fields', 'parameters']:
      parameters = sys.argv[i+1]
      i += 2
    elif myarg == 'ip':
      actorIpAddress = sys.argv[i+1]
      i += 2
    elif myarg == 'todrive':
      to_drive = True
      i += 1
    else:
      systemErrorExit(2, '%s is not a valid argument to "gam report"' % sys.argv[i])
  if report in ['users', 'user']:
    while True:
      try:
        if fullDataRequired is not None:
          warnings = callGAPIitems(rep.userUsageReport(), 'get', 'warnings',
                                   throw_reasons=[GAPI_INVALID],
                                   date=tryDate, userKey=userKey, customerId=customerId, orgUnitID=orgUnitId, fields='warnings')
          fullData, tryDate = _checkFullDataAvailable(warnings, tryDate, fullDataRequired)
          if fullData < 0:
            print('No user report available.')
            sys.exit(1)
          if fullData == 0:
            continue
        page_message = 'Got %%num_items%% Users\n'
        usage = callGAPIpages(rep.userUsageReport(), 'get', 'usageReports', page_message=page_message, throw_reasons=[GAPI_INVALID],
                              date=tryDate, userKey=userKey, customerId=customerId, orgUnitID=orgUnitId, filters=filters, parameters=parameters)
        break
      except GAPI_invalid as e:
        tryDate = _adjustDate(str(e))
    if not usage:
      print('No user report available.')
      sys.exit(1)
    titles = ['email', 'date']
    csvRows = []
    for user_report in usage:
      if 'entity' not in user_report:
        continue
      row = {'email': user_report['entity']['userEmail'], 'date': tryDate}
      try:
        for report_item in user_report['parameters']:
          items = list(report_item.values())
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
    writeCSVfile(csvRows, titles, 'User Reports - %s' % tryDate, to_drive)
  elif report in ['customer', 'customers', 'domain']:
    while True:
      try:
        if fullDataRequired is not None:
          warnings = callGAPIitems(rep.customerUsageReports(), 'get', 'warnings',
                                   throw_reasons=[GAPI_INVALID],
                                   customerId=customerId, date=tryDate, fields='warnings')
          fullData, tryDate = _checkFullDataAvailable(warnings, tryDate, fullDataRequired)
          if fullData < 0:
            print('No customer report available.')
            sys.exit(1)
          if fullData == 0:
            continue
        usage = callGAPIpages(rep.customerUsageReports(), 'get', 'usageReports', throw_reasons=[GAPI_INVALID],
                              customerId=customerId, date=tryDate, parameters=parameters)
        break
      except GAPI_invalid as e:
        tryDate = _adjustDate(str(e))
    if not usage:
      print('No customer report available.')
      sys.exit(1)
    titles = ['name', 'value', 'client_id']
    csvRows = []
    auth_apps = list()
    for item in usage[0]['parameters']:
      if 'name' not in item:
        continue
      name = item['name']
      if 'intValue' in item:
        value = item['intValue']
      elif 'msgValue' in item:
        if name == 'accounts:authorized_apps':
          for subitem in item['msgValue']:
            app = {}
            for an_item in subitem:
              if an_item == 'client_name':
                app['name'] = 'App: %s' % subitem[an_item].replace('\n', '\\n')
              elif an_item == 'num_users':
                app['value'] = '%s users' % subitem[an_item]
              elif an_item == 'client_id':
                app['client_id'] = subitem[an_item]
            auth_apps.append(app)
          continue
        else:
          values = []
          for subitem in item['msgValue']:
            if 'count' in subitem:
              mycount = myvalue = None
              for key, value in list(subitem.items()):
                if key == 'count':
                  mycount = value
                else:
                  myvalue = value
                if mycount and myvalue:
                  values.append('%s:%s' % (myvalue, mycount))
              value = ' '.join(values)
            elif 'version_number' in subitem and 'num_devices' in subitem:
              values.append('%s:%s' % (subitem['version_number'], subitem['num_devices']))
            else:
              continue
            value = ' '.join(sorted(values, reverse=True))
      csvRows.append({'name': name, 'value': value})
    for app in auth_apps: # put apps at bottom
      csvRows.append(app)
    writeCSVfile(csvRows, titles, 'Customer Report - %s' % tryDate, todrive=to_drive)
  else:
    if report in ['doc', 'docs']:
      report = 'drive'
    elif report in ['calendars']:
      report = 'calendar'
    elif report == 'logins':
      report = 'login'
    elif report == 'tokens':
      report = 'token'
    elif report == 'group':
      report = 'groups'
    page_message = 'Got %%num_items%% items\n'
    activities = callGAPIpages(rep.activities(), 'list', 'items', page_message=page_message, applicationName=report,
                               userKey=userKey, customerId=customerId, actorIpAddress=actorIpAddress,
                               startTime=startTime, endTime=endTime, eventName=eventName, filters=filters)
    if activities:
      titles = ['name']
      csvRows = []
      for activity in activities:
        events = activity['events']
        del activity['events']
        activity_row = flatten_json(activity)
        for event in events:
          for item in event.get('parameters', []):
            if item['name'] in ['start_time', 'end_time']:
              val = item.get('intValue')
              if val is not None:
                val = int(val)
                if val >= 62135683200:
                  item['dateTimeValue'] = datetime.datetime.fromtimestamp(val-62135683200).isoformat()
                  item.pop('intValue')
          row = flatten_json(event)
          row.update(activity_row)
          for item in row:
            if item not in titles:
              titles.append(item)
          csvRows.append(row)
      sortCSVTitles(['name',], titles)
      writeCSVfile(csvRows, titles, '%s Activity Report' % report.capitalize(), to_drive)

def watchGmail(users):
  cs_data = readFile(GC_Values[GC_CLIENT_SECRETS_JSON], continueOnError=True, displayError=True, encoding=None)
  cs_json = json.loads(cs_data)
  project = 'projects/{0}'.format(cs_json['installed']['project_id'])
  gamTopics = project+'/topics/gam-pubsub-gmail-'
  gamSubscriptions = project+'/subscriptions/gam-pubsub-gmail-'
  pubsub = buildGAPIObject('pubsub')
  topics = callGAPIpages(pubsub.projects().topics(), 'list', items='topics', project=project)
  for atopic in topics:
    if atopic['name'].startswith(gamTopics):
      topic = atopic['name']
      break
  else:
    topic = gamTopics+uuid.uuid4()
    callGAPI(pubsub.projects().topics(), 'create', name=topic, body={})
    body = {'policy': {'bindings': [{'members': ['serviceAccount:gmail-api-push@system.gserviceaccount.com'], 'role': 'roles/pubsub.editor'}]}}
    callGAPI(pubsub.projects().topics(), 'setIamPolicy', resource=topic, body=body)
  subscriptions = callGAPIpages(pubsub.projects().topics().subscriptions(), 'list', items='subscriptions', topic=topic)
  for asubscription in subscriptions:
    if asubscription.startswith(gamSubscriptions):
      subscription = asubscription
      break
  else:
    subscription = gamSubscriptions+uuid.uuid4()
    callGAPI(pubsub.projects().subscriptions(), 'create', name=subscription, body={'topic': topic})
  gmails = {}
  for user in users:
    gmails[user] = {'g': buildGmailGAPIObject(user)[1]}
    callGAPI(gmails[user]['g'].users(), 'watch', userId='me', body={'topicName': topic})
    gmails[user]['seen_historyId'] = callGAPI(gmails[user]['g'].users(), 'getProfile', userId='me', fields='historyId')['historyId']
  print('Watching for events...')
  while True:
    results = callGAPI(pubsub.projects().subscriptions(), 'pull', subscription=subscription, body={'maxMessages': 100})
    if 'receivedMessages' in results:
      ackIds = []
      update_history = []
      for message in results['receivedMessages']:
        if 'data' in message['message']:
          decoded_message = json.loads(base64.b64decode(message['message']['data']))
          if 'historyId' in decoded_message:
            update_history.append(decoded_message['emailAddress'])
        if 'ackId' in message:
          ackIds.append(message['ackId'])
      if ackIds:
        callGAPI(pubsub.projects().subscriptions(), 'acknowledge', subscription=subscription, body={'ackIds': ackIds})
      if update_history:
        for a_user in update_history:
          results = callGAPI(gmails[a_user]['g'].users().history(), 'list', userId='me', startHistoryId=gmails[a_user]['seen_historyId'])
          if 'history' in results:
            for history in results['history']:
              if list(history.keys()) == ['messages', 'id']:
                continue
              if 'labelsAdded' in history:
                for labelling in history['labelsAdded']:
                  print('%s labels %s added to %s' % (a_user, ', '.join(labelling['labelIds']), labelling['message']['id']))
              if 'labelsRemoved' in history:
                for labelling in history['labelsRemoved']:
                  print('%s labels %s removed from %s' % (a_user, ', '.join(labelling['labelIds']), labelling['message']['id']))
              if 'messagesDeleted' in history:
                for deleting in history['messagesDeleted']:
                  print('%s permanently deleted message %s' % (a_user, deleting['message']['id']))
              if 'messagesAdded' in history:
                for adding in history['messagesAdded']:
                  print('%s created message %s with labels %s' % (a_user, adding['message']['id'], ', '.join(adding['message']['labelIds'])))
          gmails[a_user]['seen_historyId'] = results['historyId']

def addDelegates(users, i):
  if i == 4:
    if sys.argv[i].lower() != 'to':
      systemErrorExit(2, '%s is not a valid argument for "gam <users> delegate", expected to' % sys.argv[i])
    i += 1
  delegate = normalizeEmailAddressOrUID(sys.argv[i], noUid=True)
  i = 0
  count = len(users)
  for delegator in users:
    i += 1
    delegator, gmail = buildGmailGAPIObject(delegator)
    if not gmail:
      continue
    print("Giving %s delegate access to %s (%s/%s)" % (delegate, delegator, i, count))
    callGAPI(gmail.users().settings().delegates(), 'create', soft_errors=True, userId='me', body={'delegateEmail': delegate})

def gen_sha512_hash(password):
  return sha512_crypt.hash(password, rounds=5000)

def printShowDelegates(users, csvFormat):
  if csvFormat:
    todrive = False
    csvRows = []
    titles = ['User', 'delegateAddress', 'delegationStatus']
  else:
    csvStyle = False
  i = 5
  while i < len(sys.argv):
    myarg = sys.argv[i].lower()
    if not csvFormat and myarg == 'csv':
      csvStyle = True
      i += 1
    elif csvFormat and myarg == 'todrive':
      todrive = True
      i += 1
    else:
      systemErrorExit(2, '%s is not a valid argument for "gam <users> show delegates"' % sys.argv[i])
  count = len(users)
  i = 1
  for user in users:
    user, gmail = buildGmailGAPIObject(user)
    if not gmail:
      continue
    sys.stderr.write("Getting delegates for %s (%s/%s)...\n" % (user, i, count))
    i += 1
    delegates = callGAPI(gmail.users().settings().delegates(), 'list', soft_errors=True, userId='me')
    if delegates and 'delegates' in delegates:
      for delegate in delegates['delegates']:
        delegateAddress = delegate['delegateEmail']
        status = delegate['verificationStatus']
        if csvFormat:
          row = {'User': user, 'delegateAddress': delegateAddress, 'delegationStatus': status}
          csvRows.append(row)
        else:
          if csvStyle:
            print('%s,%s,%s' % (user, delegateAddress, status))
          else:
            print(utils.convertUTF8("Delegator: %s\n Status: %s\n Delegate Email: %s\n" % (user, status, delegateAddress)))
  if csvFormat:
    writeCSVfile(csvRows, titles, 'Delegates', todrive)

def deleteDelegate(users):
  delegate = normalizeEmailAddressOrUID(sys.argv[5], noUid=True)
  i = 0
  count = len(users)
  for user in users:
    i += 1
    user, gmail = buildGmailGAPIObject(user)
    if not gmail:
      continue
    print("Deleting %s delegate access to %s (%s/%s)" % (delegate, user, i, count))
    callGAPI(gmail.users().settings().delegates(), 'delete', soft_errors=True, userId='me', delegateEmail=delegate)

def doAddCourseParticipant():
  croom = buildGAPIObject('classroom')
  courseId = addCourseIdScope(sys.argv[2])
  noScopeCourseId = removeCourseIdScope(courseId)
  participant_type = sys.argv[4].lower()
  new_id = sys.argv[5]
  if participant_type in ['student', 'students']:
    new_id = normalizeEmailAddressOrUID(new_id)
    callGAPI(croom.courses().students(), 'create', courseId=courseId, body={'userId': new_id})
    print('Added %s as a student of course %s' % (new_id, noScopeCourseId))
  elif participant_type in ['teacher', 'teachers']:
    new_id = normalizeEmailAddressOrUID(new_id)
    callGAPI(croom.courses().teachers(), 'create', courseId=courseId, body={'userId': new_id})
    print('Added %s as a teacher of course %s' % (new_id, noScopeCourseId))
  elif participant_type in ['alias']:
    new_id = addCourseIdScope(new_id)
    callGAPI(croom.courses().aliases(), 'create', courseId=courseId, body={'alias': new_id})
    print('Added %s as an alias of course %s' % (removeCourseIdScope(new_id), noScopeCourseId))
  else:
    systemErrorExit(2, '%s is not a valid argument to "gam course ID add"' % participant_type)

def doSyncCourseParticipants():
  courseId = addCourseIdScope(sys.argv[2])
  participant_type = sys.argv[4].lower()
  diff_entity_type = sys.argv[5].lower()
  diff_entity = sys.argv[6]
  current_course_users = getUsersToModify(entity_type=participant_type, entity=courseId)
  print()
  current_course_users = [x.lower() for x in current_course_users]
  if diff_entity_type == 'courseparticipants':
    diff_entity_type = participant_type
  diff_against_users = getUsersToModify(entity_type=diff_entity_type, entity=diff_entity)
  print()
  diff_against_users = [x.lower() for x in diff_against_users]
  to_add = list(set(diff_against_users) - set(current_course_users))
  to_remove = list(set(current_course_users) - set(diff_against_users))
  gam_commands = []
  for add_email in to_add:
    gam_commands.append(['gam', 'course', courseId, 'add', participant_type, add_email])
  for remove_email in to_remove:
    gam_commands.append(['gam', 'course', courseId, 'remove', participant_type, remove_email])
  run_batch(gam_commands)

def doDelCourseParticipant():
  croom = buildGAPIObject('classroom')
  courseId = addCourseIdScope(sys.argv[2])
  noScopeCourseId = removeCourseIdScope(courseId)
  participant_type = sys.argv[4].lower()
  remove_id = sys.argv[5]
  if participant_type in ['student', 'students']:
    remove_id = normalizeEmailAddressOrUID(remove_id)
    callGAPI(croom.courses().students(), 'delete', courseId=courseId, userId=remove_id)
    print('Removed %s as a student of course %s' % (remove_id, noScopeCourseId))
  elif participant_type in ['teacher', 'teachers']:
    remove_id = normalizeEmailAddressOrUID(remove_id)
    callGAPI(croom.courses().teachers(), 'delete', courseId=courseId, userId=remove_id)
    print('Removed %s as a teacher of course %s' % (remove_id, noScopeCourseId))
  elif participant_type in ['alias']:
    remove_id = addCourseIdScope(remove_id)
    callGAPI(croom.courses().aliases(), 'delete', courseId=courseId, alias=remove_id)
    print('Removed %s as an alias of course %s' % (removeCourseIdScope(remove_id), noScopeCourseId))
  else:
    systemErrorExit(2, '%s is not a valid argument to "gam course ID delete"' % participant_type)

def doDelCourse():
  croom = buildGAPIObject('classroom')
  courseId = addCourseIdScope(sys.argv[3])
  callGAPI(croom.courses(), 'delete', id=courseId)
  print('Deleted Course %s' % courseId)

def _getValidCourseStates(croom):
  return [state for state in croom._rootDesc['schemas']['Course']['properties']['courseState']['enum'] if state != 'COURSE_STATE_UNSPECIFIED']

def _getValidatedState(state, validStates):
  state = state.upper()
  if state not in validStates:
    systemErrorExit(2, 'course state must be one of: %s. Got %s' % (', '.join(validStates).lower(), state.lower()))
  return state

def getCourseAttribute(myarg, value, body, croom, function):
  if myarg == 'name':
    body['name'] = value
  elif myarg == 'section':
    body['section'] = value
  elif myarg == 'heading':
    body['descriptionHeading'] = value
  elif myarg == 'description':
    body['description'] = value.replace('\\n', '\n')
  elif myarg == 'room':
    body['room'] = value
  elif myarg in ['owner', 'ownerid', 'teacher']:
    body['ownerId'] = normalizeEmailAddressOrUID(value)
  elif myarg in ['state', 'status']:
    validStates = _getValidCourseStates(croom)
    body['courseState'] = _getValidatedState(value, validStates)
  else:
    systemErrorExit(2, '%s is not a valid argument to "gam %s course"' % (myarg, function))

def _getCourseStates(croom, value, courseStates):
  validStates = _getValidCourseStates(croom)
  for state in value.replace(',', ' ').split():
    courseStates.append(_getValidatedState(state, validStates))

def doUpdateCourse():
  croom = buildGAPIObject('classroom')
  courseId = addCourseIdScope(sys.argv[3])
  body = {}
  i = 4
  while i < len(sys.argv):
    myarg = sys.argv[i].lower()
    getCourseAttribute(myarg, sys.argv[i+1], body, croom, 'update')
    i += 2
  updateMask = ','.join(list(body.keys()))
  body['id'] = courseId
  result = callGAPI(croom.courses(), 'patch', id=courseId, body=body, updateMask=updateMask)
  print('Updated Course %s' % result['id'])

def doCreateDomain():
  cd = buildGAPIObject('directory')
  domain_name = sys.argv[3]
  body = {'domainName': domain_name}
  callGAPI(cd.domains(), 'insert', customer=GC_Values[GC_CUSTOMER_ID], body=body)
  print('Added domain %s' % domain_name)

def doCreateDomainAlias():
  cd = buildGAPIObject('directory')
  body = {}
  body['domainAliasName'] = sys.argv[3]
  body['parentDomainName'] = sys.argv[4]
  callGAPI(cd.domainAliases(), 'insert', customer=GC_Values[GC_CUSTOMER_ID], body=body)

def doUpdateDomain():
  cd = buildGAPIObject('directory')
  domain_name = sys.argv[3]
  i = 4
  body = {}
  while i < len(sys.argv):
    myarg = sys.argv[i].lower()
    if myarg == 'primary':
      body['customerDomain'] = domain_name
      i += 1
    else:
      systemErrorExit(2, '%s is not a valid argument for "gam update domain"' % sys.argv[i])
  callGAPI(cd.customers(), 'update', customerKey=GC_Values[GC_CUSTOMER_ID], body=body)
  print('%s is now the primary domain.' % domain_name)

def doGetDomainInfo():
  if (len(sys.argv) < 4) or (sys.argv[3] == 'logo'):
    doGetCustomerInfo()
    return
  cd = buildGAPIObject('directory')
  domainName = sys.argv[3]
  result = callGAPI(cd.domains(), 'get', customer=GC_Values[GC_CUSTOMER_ID], domainName=domainName)
  if 'creationTime' in result:
    result['creationTime'] = str(datetime.datetime.fromtimestamp(int(result['creationTime'])/1000))
  if 'domainAliases' in result:
    for i in range(0, len(result['domainAliases'])):
      if 'creationTime' in result['domainAliases'][i]:
        result['domainAliases'][i]['creationTime'] = str(datetime.datetime.fromtimestamp(int(result['domainAliases'][i]['creationTime'])/1000))
  print_json(None, result)

def doGetDomainAliasInfo():
  cd = buildGAPIObject('directory')
  alias = sys.argv[3]
  result = callGAPI(cd.domainAliases(), 'get', customer=GC_Values[GC_CUSTOMER_ID], domainAliasName=alias)
  if 'creationTime' in result:
    result['creationTime'] = str(datetime.datetime.fromtimestamp(int(result['creationTime'])/1000))
  print_json(None, result)

def doGetCustomerInfo():
  cd = buildGAPIObject('directory')
  customer_info = callGAPI(cd.customers(), 'get', customerKey=GC_Values[GC_CUSTOMER_ID])
  print('Customer ID: %s' % customer_info['id'])
  print('Primary Domain: %s' % customer_info['customerDomain'])
  result = callGAPI(cd.domains(), 'get',
                    customer=customer_info['id'], domainName=customer_info['customerDomain'], fields='verified')
  print('Primary Domain Verified: %s' % result['verified'])
  print('Customer Creation Time: %s' % customer_info['customerCreationTime'])
  print('Default Language: %s' % customer_info.get('language', 'Unset (defaults to en)'))
  if 'postalAddress' in customer_info:
    print('Address:')
    for field in ADDRESS_FIELDS_PRINT_ORDER:
      if field in customer_info['postalAddress']:
        print(' %s: %s' % (field, customer_info['postalAddress'][field]))
  if 'phoneNumber' in customer_info:
    print('Phone: %s' % customer_info['phoneNumber'])
  print('Admin Secondary Email: %s' % customer_info['alternateEmail'])
  user_counts_map = {
    'accounts:num_users': 'Total Users',
    'accounts:gsuite_basic_total_licenses': 'G Suite Basic Licenses',
    'accounts:gsuite_basic_used_licenses': 'G Suite Basic Users',
    'accounts:gsuite_enterprise_total_licenses': 'G Suite Enterprise Licenses',
    'accounts:gsuite_enterprise_used_licenses': 'G Suite Enterprise Users',
    'accounts:gsuite_unlimited_total_licenses': 'G Suite Business Licenses',
    'accounts:gsuite_unlimited_used_licenses': 'G Suite Business Users'
    }
  parameters = ','.join(list(user_counts_map.keys()))
  tryDate = datetime.date.today().strftime(YYYYMMDD_FORMAT)
  customerId = GC_Values[GC_CUSTOMER_ID]
  if customerId == MY_CUSTOMER:
    customerId = None
  rep = buildGAPIObject('reports')
  usage = None
  while True:
    try:
      usage = callGAPIpages(rep.customerUsageReports(), 'get', 'usageReports', throw_reasons=[GAPI_INVALID],
                            customerId=customerId, date=tryDate, parameters=parameters)
      break
    except GAPI_invalid as e:
      tryDate = _adjustDate(str(e))
  if not usage:
    print('No user count data available.')
    return
  print('User counts as of %s:' % tryDate)
  for item in usage[0]['parameters']:
    api_name = user_counts_map.get(item['name'])
    api_value = int(item.get('intValue', 0))
    if api_name and api_value:
      print('  {}: {:,}'.format(api_name, api_value))

def doUpdateCustomer():
  cd = buildGAPIObject('directory')
  body = {}
  i = 3
  while i < len(sys.argv):
    myarg = sys.argv[i].lower().replace('_', '')
    if myarg in ADDRESS_FIELDS_ARGUMENT_MAP:
      body.setdefault('postalAddress', {})
      body['postalAddress'][ADDRESS_FIELDS_ARGUMENT_MAP[myarg]] = sys.argv[i+1]
      i += 2
    elif myarg in ['adminsecondaryemail', 'alternateemail']:
      body['alternateEmail'] = sys.argv[i+1]
      i += 2
    elif myarg in ['phone', 'phonenumber']:
      body['phoneNumber'] = sys.argv[i+1]
      i += 2
    elif myarg == 'language':
      body['language'] = sys.argv[i+1]
      i += 2
    else:
      systemErrorExit(2, '%s is not a valid argument for "gam update customer"' % myarg)
  if not body:
    systemErrorExit(2, 'no arguments specified for "gam update customer"')
  callGAPI(cd.customers(), 'patch', customerKey=GC_Values[GC_CUSTOMER_ID], body=body)
  print('Updated customer')

def doDelDomain():
  cd = buildGAPIObject('directory')
  domainName = sys.argv[3]
  callGAPI(cd.domains(), 'delete', customer=GC_Values[GC_CUSTOMER_ID], domainName=domainName)

def doDelDomainAlias():
  cd = buildGAPIObject('directory')
  domainAliasName = sys.argv[3]
  callGAPI(cd.domainAliases(), 'delete', customer=GC_Values[GC_CUSTOMER_ID], domainAliasName=domainAliasName)

def doPrintDomains():
  cd = buildGAPIObject('directory')
  todrive = False
  titles = ['domainName',]
  csvRows = []
  i = 3
  while i < len(sys.argv):
    myarg = sys.argv[i].lower()
    if myarg == 'todrive':
      todrive = True
      i += 1
    else:
      systemErrorExit(2, '%s is not a valid argument for "gam print domains".' % sys.argv[i])
  results = callGAPI(cd.domains(), 'list', customer=GC_Values[GC_CUSTOMER_ID])
  for domain in results['domains']:
    domain_attributes = {}
    domain['type'] = ['secondary', 'primary'][domain['isPrimary']]
    for attr in domain:
      if attr in ['kind', 'etag', 'domainAliases', 'isPrimary']:
        continue
      if attr in ['creationTime',]:
        domain[attr] = str(datetime.datetime.fromtimestamp(int(domain[attr])/1000))
      if attr not in titles:
        titles.append(attr)
      domain_attributes[attr] = domain[attr]
    csvRows.append(domain_attributes)
    if 'domainAliases' in domain:
      for aliasdomain in domain['domainAliases']:
        aliasdomain['domainName'] = aliasdomain['domainAliasName']
        del aliasdomain['domainAliasName']
        aliasdomain['type'] = 'alias'
        aliasdomain_attributes = {}
        for attr in aliasdomain:
          if attr in ['kind', 'etag']:
            continue
          if attr in ['creationTime',]:
            aliasdomain[attr] = str(datetime.datetime.fromtimestamp(int(aliasdomain[attr])/1000))
          if attr not in titles:
            titles.append(attr)
          aliasdomain_attributes[attr] = aliasdomain[attr]
        csvRows.append(aliasdomain_attributes)
  writeCSVfile(csvRows, titles, 'Domains', todrive)

def doPrintDomainAliases():
  cd = buildGAPIObject('directory')
  todrive = False
  titles = ['domainAliasName',]
  csvRows = []
  i = 3
  while i < len(sys.argv):
    myarg = sys.argv[i].lower()
    if myarg == 'todrive':
      todrive = True
      i += 1
    else:
      systemErrorExit(2, '%s is not a valid argument for "gam print domainaliases".' % sys.argv[i])
  results = callGAPI(cd.domainAliases(), 'list', customer=GC_Values[GC_CUSTOMER_ID])
  for domainAlias in results['domainAliases']:
    domainAlias_attributes = {}
    for attr in domainAlias:
      if attr in ['kind', 'etag']:
        continue
      if attr == 'creationTime':
        domainAlias[attr] = str(datetime.datetime.fromtimestamp(int(domainAlias[attr])/1000))
      if attr not in titles:
        titles.append(attr)
      domainAlias_attributes[attr] = domainAlias[attr]
    csvRows.append(domainAlias_attributes)
  writeCSVfile(csvRows, titles, 'Domains', todrive)

def doDelAdmin():
  cd = buildGAPIObject('directory')
  roleAssignmentId = sys.argv[3]
  print('Deleting Admin Role Assignment %s' % roleAssignmentId)
  callGAPI(cd.roleAssignments(), 'delete',
           customer=GC_Values[GC_CUSTOMER_ID], roleAssignmentId=roleAssignmentId)

def doCreateAdmin():
  cd = buildGAPIObject('directory')
  user = normalizeEmailAddressOrUID(sys.argv[3])
  body = {'assignedTo': convertEmailAddressToUID(user, cd)}
  role = sys.argv[4]
  body['roleId'] = getRoleId(role)
  body['scopeType'] = sys.argv[5].upper()
  if body['scopeType'] not in ['CUSTOMER', 'ORG_UNIT']:
    systemErrorExit(3, 'scope type must be customer or org_unit; got %s' % body['scopeType'])
  if body['scopeType'] == 'ORG_UNIT':
    orgUnit, orgUnitId = getOrgUnitId(sys.argv[6], cd)
    body['orgUnitId'] = orgUnitId[3:]
    scope = 'ORG_UNIT {0}'.format(orgUnit)
  else:
    scope = 'CUSTOMER'
  print('Giving %s admin role %s for %s' % (user, role, scope))
  callGAPI(cd.roleAssignments(), 'insert',
           customer=GC_Values[GC_CUSTOMER_ID], body=body)

def doPrintAdminRoles():
  cd = buildGAPIObject('directory')
  todrive = False
  titles = ['roleId', 'roleName', 'roleDescription', 'isSuperAdminRole', 'isSystemRole']
  fields = 'nextPageToken,items({0})'.format(','.join(titles))
  csvRows = []
  i = 3
  while i < len(sys.argv):
    myarg = sys.argv[i].lower()
    if myarg == 'todrive':
      todrive = True
      i += 1
    else:
      systemErrorExit(2, '%s is not a valid argument for "gam print adminroles".' % sys.argv[i])
  roles = callGAPIpages(cd.roles(), 'list', 'items',
                        customer=GC_Values[GC_CUSTOMER_ID], fields=fields)
  for role in roles:
    role_attrib = {}
    for key, value in list(role.items()):
      role_attrib[key] = value
    csvRows.append(role_attrib)
  writeCSVfile(csvRows, titles, 'Admin Roles', todrive)

def doPrintAdmins():
  cd = buildGAPIObject('directory')
  roleId = None
  userKey = None
  todrive = False
  fields = 'nextPageToken,items({0})'.format(','.join(['roleAssignmentId', 'roleId', 'assignedTo', 'scopeType', 'orgUnitId']))
  titles = ['roleAssignmentId', 'roleId', 'role', 'assignedTo', 'assignedToUser', 'scopeType', 'orgUnitId', 'orgUnit']
  csvRows = []
  i = 3
  while i < len(sys.argv):
    myarg = sys.argv[i].lower()
    if myarg == 'user':
      userKey = normalizeEmailAddressOrUID(sys.argv[i+1])
      i += 2
    elif myarg == 'role':
      roleId = getRoleId(sys.argv[i+1])
      i += 2
    elif myarg == 'todrive':
      todrive = True
      i += 1
    else:
      systemErrorExit(2, '%s is not a valid argument for "gam print admins".' % sys.argv[i])
  admins = callGAPIpages(cd.roleAssignments(), 'list', 'items',
                         customer=GC_Values[GC_CUSTOMER_ID], userKey=userKey, roleId=roleId, fields=fields)
  for admin in admins:
    admin_attrib = {}
    for key, value in list(admin.items()):
      if key == 'assignedTo':
        admin_attrib['assignedToUser'] = user_from_userid(value)
      elif key == 'roleId':
        admin_attrib['role'] = role_from_roleid(value)
      elif key == 'orgUnitId':
        value = 'id:{0}'.format(value)
        admin_attrib['orgUnit'] = orgunit_from_orgunitid(value)
      admin_attrib[key] = value
    csvRows.append(admin_attrib)
  writeCSVfile(csvRows, titles, 'Admins', todrive)

def buildOrgUnitIdToNameMap():
  cd = buildGAPIObject('directory')
  result = callGAPI(cd.orgunits(), 'list',
                    customerId=GC_Values[GC_CUSTOMER_ID],
                    fields='organizationUnits(orgUnitPath,orgUnitId)', type='all')
  GM_Globals[GM_MAP_ORGUNIT_ID_TO_NAME] = {}
  for orgUnit in result['organizationUnits']:
    GM_Globals[GM_MAP_ORGUNIT_ID_TO_NAME][orgUnit['orgUnitId']] = orgUnit['orgUnitPath']

def orgunit_from_orgunitid(orgunitid):
  if not GM_Globals[GM_MAP_ORGUNIT_ID_TO_NAME]:
    buildOrgUnitIdToNameMap()
  return GM_Globals[GM_MAP_ORGUNIT_ID_TO_NAME].get(orgunitid, orgunitid)

def buildRoleIdToNameToIdMap():
  cd = buildGAPIObject('directory')
  result = callGAPIpages(cd.roles(), 'list', 'items',
                         customer=GC_Values[GC_CUSTOMER_ID],
                         fields='nextPageToken,items(roleId,roleName)',
                         maxResults=100)
  GM_Globals[GM_MAP_ROLE_ID_TO_NAME] = {}
  GM_Globals[GM_MAP_ROLE_NAME_TO_ID] = {}
  for role in result:
    GM_Globals[GM_MAP_ROLE_ID_TO_NAME][role['roleId']] = role['roleName']
    GM_Globals[GM_MAP_ROLE_NAME_TO_ID][role['roleName']] = role['roleId']

def role_from_roleid(roleid):
  if not GM_Globals[GM_MAP_ROLE_ID_TO_NAME]:
    buildRoleIdToNameToIdMap()
  return GM_Globals[GM_MAP_ROLE_ID_TO_NAME].get(roleid, roleid)

def roleid_from_role(role):
  if not GM_Globals[GM_MAP_ROLE_NAME_TO_ID]:
    buildRoleIdToNameToIdMap()
  return GM_Globals[GM_MAP_ROLE_NAME_TO_ID].get(role, None)

def getRoleId(role):
  cg = UID_PATTERN.match(role)
  if cg:
    roleId = cg.group(1)
  else:
    roleId = roleid_from_role(role)
    if not roleId:
      systemErrorExit(4, '%s is not a valid role. Please ensure role name is exactly as shown in admin console.' % role)
  return roleId

def buildUserIdToNameMap():
  cd = buildGAPIObject('directory')
  result = callGAPIpages(cd.users(), 'list', 'users',
                         customer=GC_Values[GC_CUSTOMER_ID],
                         fields='nextPageToken,users(id,primaryEmail)',
                         maxResults=GC_Values[GC_USER_MAX_RESULTS])
  GM_Globals[GM_MAP_USER_ID_TO_NAME] = {}
  for user in result:
    GM_Globals[GM_MAP_USER_ID_TO_NAME][user['id']] = user['primaryEmail']

def user_from_userid(userid):
  if not GM_Globals[GM_MAP_USER_ID_TO_NAME]:
    buildUserIdToNameMap()
  return GM_Globals[GM_MAP_USER_ID_TO_NAME].get(userid, '')

def appID2app(dt, appID):
  for serviceName, serviceID in list(SERVICE_NAME_TO_ID_MAP.items()):
    if appID == serviceID:
      return serviceName
  online_services = callGAPIpages(dt.applications(), 'list', 'applications', customerId=GC_Values[GC_CUSTOMER_ID])
  for online_service in online_services:
    if appID == online_service['id']:
      return online_service['name']
  return 'applicationId: {0}'.format(appID)

def app2appID(dt, app):
  serviceName = app.lower()
  if serviceName in SERVICE_NAME_CHOICES_MAP:
    return (SERVICE_NAME_CHOICES_MAP[serviceName], SERVICE_NAME_TO_ID_MAP[SERVICE_NAME_CHOICES_MAP[serviceName]])
  online_services = callGAPIpages(dt.applications(), 'list', 'applications', customerId=GC_Values[GC_CUSTOMER_ID])
  for online_service in online_services:
    if serviceName == online_service['name'].lower():
      return (online_service['name'], online_service['id'])
  systemErrorExit(2, '%s is not a valid service for data transfer.' % app)

def convertToUserID(user):
  cg = UID_PATTERN.match(user)
  if cg:
    return cg.group(1)
  cd = buildGAPIObject('directory')
  if user.find('@') == -1:
    user = '%s@%s' % (user, GC_Values[GC_DOMAIN])
  try:
    return callGAPI(cd.users(), 'get', throw_reasons=[GAPI_USER_NOT_FOUND, GAPI_BAD_REQUEST, GAPI_FORBIDDEN], userKey=user, fields='id')['id']
  except (GAPI_userNotFound, GAPI_badRequest, GAPI_forbidden):
    systemErrorExit(3, 'no such user %s' % user)

def convertUserIDtoEmail(uid):
  cd = buildGAPIObject('directory')
  try:
    return callGAPI(cd.users(), 'get', throw_reasons=[GAPI_USER_NOT_FOUND, GAPI_BAD_REQUEST, GAPI_FORBIDDEN], userKey=uid, fields='primaryEmail')['primaryEmail']
  except (GAPI_userNotFound, GAPI_badRequest, GAPI_forbidden):
    return 'uid:{0}'.format(uid)

def doCreateDataTransfer():
  dt = buildGAPIObject('datatransfer')
  body = {}
  old_owner = sys.argv[3]
  body['oldOwnerUserId'] = convertToUserID(old_owner)
  apps = sys.argv[4].split(",")
  appNameList = []
  appIDList = []
  i = 0
  while i < len(apps):
    serviceName, serviceID = app2appID(dt, apps[i])
    appNameList.append(serviceName)
    appIDList.append({'applicationId': serviceID})
    i += 1
  body['applicationDataTransfers'] = (appIDList)
  new_owner = sys.argv[5]
  body['newOwnerUserId'] = convertToUserID(new_owner)
  parameters = {}
  i = 6
  while i < len(sys.argv):
    parameters[sys.argv[i].upper()] = sys.argv[i+1].upper().split(',')
    i += 2
  i = 0
  for key, value in list(parameters.items()):
    body['applicationDataTransfers'][i].setdefault('applicationTransferParams', [])
    body['applicationDataTransfers'][i]['applicationTransferParams'].append({'key': key, 'value': value})
    i += 1
  result = callGAPI(dt.transfers(), 'insert', body=body, fields='id')['id']
  print('Submitted request id %s to transfer %s from %s to %s' % (result, ','.join(map(str, appNameList)), old_owner, new_owner))

def doPrintTransferApps():
  dt = buildGAPIObject('datatransfer')
  apps = callGAPIpages(dt.applications(), 'list', 'applications', customerId=GC_Values[GC_CUSTOMER_ID])
  for app in apps:
    print_json(None, app)
    print()

def doPrintDataTransfers():
  dt = buildGAPIObject('datatransfer')
  i = 3
  newOwnerUserId = None
  oldOwnerUserId = None
  status = None
  todrive = False
  titles = ['id',]
  csvRows = []
  while i < len(sys.argv):
    myarg = sys.argv[i].lower().replace('_', '')
    if myarg in ['olduser', 'oldowner']:
      oldOwnerUserId = convertToUserID(sys.argv[i+1])
      i += 2
    elif myarg in ['newuser', 'newowner']:
      newOwnerUserId = convertToUserID(sys.argv[i+1])
      i += 2
    elif myarg == 'status':
      status = sys.argv[i+1]
      i += 2
    elif myarg == 'todrive':
      todrive = True
      i += 1
    else:
      systemErrorExit(2, '%s is not a valid argument for "gam print transfers"' % sys.argv[i])
  transfers = callGAPIpages(dt.transfers(), 'list', 'dataTransfers',
                            customerId=GC_Values[GC_CUSTOMER_ID], status=status,
                            newOwnerUserId=newOwnerUserId, oldOwnerUserId=oldOwnerUserId)
  for transfer in transfers:
    for i in range(0, len(transfer['applicationDataTransfers'])):
      a_transfer = {}
      a_transfer['oldOwnerUserEmail'] = convertUserIDtoEmail(transfer['oldOwnerUserId'])
      a_transfer['newOwnerUserEmail'] = convertUserIDtoEmail(transfer['newOwnerUserId'])
      a_transfer['requestTime'] = transfer['requestTime']
      a_transfer['applicationId'] = transfer['applicationDataTransfers'][i]['applicationId']
      a_transfer['application'] = appID2app(dt, a_transfer['applicationId'])
      a_transfer['status'] = transfer['applicationDataTransfers'][i]['applicationTransferStatus']
      a_transfer['id'] = transfer['id']
      if 'applicationTransferParams' in transfer['applicationDataTransfers'][i]:
        for param in transfer['applicationDataTransfers'][i]['applicationTransferParams']:
          a_transfer[param['key']] = ','.join(param.get('value', []))
    for title in a_transfer:
      if title not in titles:
        titles.append(title)
    csvRows.append(a_transfer)
  writeCSVfile(csvRows, titles, 'Data Transfers', todrive)

def doGetDataTransferInfo():
  dt = buildGAPIObject('datatransfer')
  dtId = sys.argv[3]
  transfer = callGAPI(dt.transfers(), 'get', dataTransferId=dtId)
  print('Old Owner: %s' % convertUserIDtoEmail(transfer['oldOwnerUserId']))
  print('New Owner: %s' % convertUserIDtoEmail(transfer['newOwnerUserId']))
  print('Request Time: %s' % transfer['requestTime'])
  for app in transfer['applicationDataTransfers']:
    print('Application: %s' % appID2app(dt, app['applicationId']))
    print('Status: %s' % app['applicationTransferStatus'])
    print('Parameters:')
    if 'applicationTransferParams' in app:
      for param in app['applicationTransferParams']:
        print(' %s: %s' % (param['key'], ','.join(param.get('value', []))))
    else:
      print(' None')
    print()

def doPrintShowGuardians(csvFormat):
  croom = buildGAPIObject('classroom')
  invitedEmailAddress = None
  studentIds = ['-',]
  states = None
  service = croom.userProfiles().guardians()
  items = 'guardians'
  itemName = 'Guardians'
  if csvFormat:
    csvRows = []
    todrive = False
    titles = ['studentEmail', 'studentId', 'invitedEmailAddress', 'guardianId']
  i = 3
  while i < len(sys.argv):
    myarg = sys.argv[i].lower()
    if csvFormat and myarg == 'todrive':
      todrive = True
      i += 1
    elif myarg == 'invitedguardian':
      invitedEmailAddress = normalizeEmailAddressOrUID(sys.argv[i+1])
      i += 2
    elif myarg == 'student':
      studentIds = [normalizeStudentGuardianEmailAddressOrUID(sys.argv[i+1])]
      i += 2
    elif myarg == 'invitations':
      service = croom.userProfiles().guardianInvitations()
      items = 'guardianInvitations'
      itemName = 'Guardian Invitations'
      titles = ['studentEmail', 'studentId', 'invitedEmailAddress', 'invitationId']
      if states is None:
        states = ['COMPLETE', 'PENDING', 'GUARDIAN_INVITATION_STATE_UNSPECIFIED']
      i += 1
    elif myarg == 'states':
      states = sys.argv[i+1].upper().replace(',', ' ').split()
      i += 2
    elif myarg in usergroup_types:
      studentIds = getUsersToModify(entity_type=myarg, entity=sys.argv[i+1])
      i += 2
    else:
      systemErrorExit(2, '%s is not a valid argument for "gam %s guardians"' % (sys.argv[i], ['show', 'print'][csvFormat]))
  i = 0
  count = len(studentIds)
  for studentId in studentIds:
    i += 1
    studentId = normalizeStudentGuardianEmailAddressOrUID(studentId)
    kwargs = {'invitedEmailAddress': invitedEmailAddress, 'studentId': studentId}
    if items == 'guardianInvitations':
      kwargs['states'] = states
    if studentId != '-':
      if csvFormat:
        sys.stderr.write('\r')
        sys.stderr.flush()
        sys.stderr.write('Getting %s for %s%s%s' % (itemName, studentId, currentCount(i, count), ' ' * 40))
    guardians = callGAPIpages(service, 'list', items, soft_errors=True, **kwargs)
    if not csvFormat:
      print('Student: {0}, {1}:{2}'.format(studentId, itemName, currentCount(i, count)))
      for guardian in guardians:
        print_json(None, guardian, spacing='  ')
    else:
      for guardian in guardians:
        guardian['studentEmail'] = studentId
        addRowTitlesToCSVfile(flatten_json(guardian), csvRows, titles)
  if csvFormat:
    sys.stderr.write('\n')
    writeCSVfile(csvRows, titles, itemName, todrive)

def doInviteGuardian():
  croom = buildGAPIObject('classroom')
  body = {'invitedEmailAddress': normalizeEmailAddressOrUID(sys.argv[3])}
  studentId = normalizeStudentGuardianEmailAddressOrUID(sys.argv[4])
  result = callGAPI(croom.userProfiles().guardianInvitations(), 'create', studentId=studentId, body=body)
  print('Invited email %s as guardian of %s. Invite ID %s' % (result['invitedEmailAddress'], studentId, result['invitationId']))

def _cancelGuardianInvitation(croom, studentId, invitationId):
  try:
    result = callGAPI(croom.userProfiles().guardianInvitations(), 'patch',
                      throw_reasons=[GAPI_FAILED_PRECONDITION, GAPI_FORBIDDEN, GAPI_NOT_FOUND],
                      studentId=studentId, invitationId=invitationId, updateMask='state', body={'state': 'COMPLETE'})
    print('Cancelled PENDING guardian invitation for %s as guardian of %s' % (result['invitedEmailAddress'], studentId))
    return True
  except GAPI_failedPrecondition:
    stderrErrorMsg('Guardian invitation %s for %s status is not PENDING' % (invitationId, studentId))
    GM_Globals[GM_SYSEXITRC] = 3
    return True
  except GAPI_forbidden:
    entityUnknownWarning('Student', studentId, 0, 0)
    sys.exit(3)
  except GAPI_notFound:
    return False

def doCancelGuardianInvitation():
  croom = buildGAPIObject('classroom')
  invitationId = sys.argv[3]
  studentId = normalizeStudentGuardianEmailAddressOrUID(sys.argv[4])
  if not _cancelGuardianInvitation(croom, studentId, invitationId):
    systemErrorExit(3, 'Guardian invitation %s for %s does not exist' % (invitationId, studentId))

def _deleteGuardian(croom, studentId, guardianId, guardianEmail):
  try:
    callGAPI(croom.userProfiles().guardians(), 'delete',
             throw_reasons=[GAPI_FORBIDDEN, GAPI_NOT_FOUND],
             studentId=studentId, guardianId=guardianId)
    print('Deleted %s as a guardian of %s' % (guardianEmail, studentId))
    return True
  except GAPI_forbidden:
    entityUnknownWarning('Student', studentId, 0, 0)
    sys.exit(3)
  except GAPI_notFound:
    return False

def doDeleteGuardian():
  croom = buildGAPIObject('classroom')
  invitationsOnly = False
  guardianId = normalizeStudentGuardianEmailAddressOrUID(sys.argv[3])
  guardianIdIsEmail = guardianId.find('@') != -1
  studentId = normalizeStudentGuardianEmailAddressOrUID(sys.argv[4])
  i = 5
  while i < len(sys.argv):
    myarg = sys.argv[i].lower()
    if myarg in ['invitation', 'invitations']:
      invitationsOnly = True
      i += 1
    else:
      systemErrorExit(2, '%s is not a valid argument for "gam delete guardian"' % (sys.argv[i]))
  if not invitationsOnly:
    if guardianIdIsEmail:
      try:
        results = callGAPIpages(croom.userProfiles().guardians(), 'list', 'guardians',
                                throw_reasons=[GAPI_FORBIDDEN],
                                studentId=studentId, invitedEmailAddress=guardianId,
                                fields='nextPageToken,guardians(studentId,guardianId)')
        if results:
          for result in results:
            _deleteGuardian(croom, result['studentId'], result['guardianId'], guardianId)
          return
      except GAPI_forbidden:
        entityUnknownWarning('Student', studentId, 0, 0)
        sys.exit(3)
    else:
      if _deleteGuardian(croom, studentId, guardianId, guardianId):
        return
  # See if there's a pending invitation
  if guardianIdIsEmail:
    try:
      results = callGAPIpages(croom.userProfiles().guardianInvitations(), 'list', 'guardianInvitations',
                              throw_reasons=[GAPI_FORBIDDEN],
                              studentId=studentId, invitedEmailAddress=guardianId, states=['PENDING',],
                              fields='nextPageToken,guardianInvitations(studentId,invitationId)')
      if results:
        for result in results:
          status = _cancelGuardianInvitation(croom, result['studentId'], result['invitationId'])
        sys.exit(status)
    except GAPI_forbidden:
      entityUnknownWarning('Student', studentId, 0, 0)
      sys.exit(3)
  else:
    if _cancelGuardianInvitation(croom, studentId, guardianId):
      return
  systemErrorExit(3, '%s is not a guardian of %s and no invitation exists.' % (guardianId, studentId))

def doCreateCourse():
  croom = buildGAPIObject('classroom')
  body = {}
  i = 3
  while i < len(sys.argv):
    myarg = sys.argv[i].lower()
    if myarg in ['alias', 'id']:
      body['id'] = 'd:%s' % sys.argv[i+1]
      i += 2
    else:
      getCourseAttribute(myarg, sys.argv[i+1], body, croom, 'create')
      i += 2
  if 'ownerId' not in body:
    systemErrorExit(2, 'expected teacher <UserItem>)')
  if 'name' not in body:
    systemErrorExit(2, 'expected name <String>)')
  result = callGAPI(croom.courses(), 'create', body=body)
  print('Created course %s' % result['id'])

def doGetCourseInfo():
  croom = buildGAPIObject('classroom')
  courseId = addCourseIdScope(sys.argv[3])
  info = callGAPI(croom.courses(), 'get', id=courseId)
  info['ownerEmail'] = convertUIDtoEmailAddress('uid:%s' % info['ownerId'])
  print_json(None, info)
  teachers = callGAPIpages(croom.courses().teachers(), 'list', 'teachers', courseId=courseId)
  students = callGAPIpages(croom.courses().students(), 'list', 'students', courseId=courseId)
  try:
    aliases = callGAPIpages(croom.courses().aliases(), 'list', 'aliases', throw_reasons=[GAPI_NOT_IMPLEMENTED], courseId=courseId)
  except GAPI_notImplemented:
    aliases = []
  if aliases:
    print('Aliases:')
    for alias in aliases:
      print('  %s' % alias['alias'][2:])
  print('Participants:')
  print(' Teachers:')
  for teacher in teachers:
    try:
      print(utils.convertUTF8('  %s - %s' % (teacher['profile']['name']['fullName'], teacher['profile']['emailAddress'])))
    except KeyError:
      print(utils.convertUTF8('  %s' % teacher['profile']['name']['fullName']))
  print(' Students:')
  for student in students:
    try:
      print(utils.convertUTF8('  %s - %s' % (student['profile']['name']['fullName'], student['profile']['emailAddress'])))
    except KeyError:
      print(utils.convertUTF8('  %s' % student['profile']['name']['fullName']))

COURSE_ARGUMENT_TO_PROPERTY_MAP = {
  'alternatelink': 'alternateLink',
  'coursegroupemail': 'courseGroupEmail',
  'coursematerialsets': 'courseMaterialSets',
  'coursestate': 'courseState',
  'creationtime': 'creationTime',
  'description': 'description',
  'descriptionheading': 'descriptionHeading',
  'enrollmentcode': 'enrollmentCode',
  'guardiansenabled': 'guardiansEnabled',
  'id': 'id',
  'name': 'name',
  'ownerid': 'ownerId',
  'room': 'room',
  'section': 'section',
  'teacherfolder': 'teacherFolder',
  'teachergroupemail': 'teacherGroupEmail',
  'updatetime': 'updateTime',
  }

def doPrintCourses():

  def _processFieldsList(myarg, i, fList):
    fieldNameList = sys.argv[i+1]
    for field in fieldNameList.lower().replace(',', ' ').split():
      if field in COURSE_ARGUMENT_TO_PROPERTY_MAP:
        if field != 'id':
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
      prefix = '{0}.{1}.'.format(role, j)
      profile = member['profile']
      emailAddress = profile.get('emailAddress')
      if emailAddress:
        memberTitle = prefix+'emailAddress'
        course[memberTitle] = emailAddress
        memberTitles.append(memberTitle)
      memberId = profile.get('id')
      if memberId:
        memberTitle = prefix+'id'
        course[memberTitle] = memberId
        memberTitles.append(memberTitle)
      fullName = profile.get('name', {}).get('fullName')
      if fullName:
        memberTitle = prefix+'name.fullName'
        course[memberTitle] = fullName
        memberTitles.append(memberTitle)
      addTitlesToCSVfile(memberTitles, titles)
      j += 1

  croom = buildGAPIObject('classroom')
  todrive = False
  fieldsList = []
  skipFieldsList = []
  titles = ['id',]
  csvRows = []
  ownerEmails = studentId = teacherId = None
  courseStates = []
  countsOnly = showAliases = False
  delimiter = ' '
  showMembers = ''
  i = 3
  while i < len(sys.argv):
    myarg = sys.argv[i].lower()
    if myarg == 'teacher':
      teacherId = normalizeEmailAddressOrUID(sys.argv[i+1])
      i += 2
    elif myarg == 'student':
      studentId = normalizeEmailAddressOrUID(sys.argv[i+1])
      i += 2
    elif myarg in ['state', 'states', 'status']:
      _getCourseStates(croom, sys.argv[i+1], courseStates)
      i += 2
    elif myarg == 'todrive':
      todrive = True
      i += 1
    elif myarg in ['alias', 'aliases']:
      showAliases = True
      i += 1
    elif myarg == 'countsonly':
      countsOnly = True
      i += 1
    elif myarg == 'delimiter':
      delimiter = sys.argv[i+1]
      i += 2
    elif myarg == 'show':
      showMembers = sys.argv[i+1].lower()
      if showMembers not in ['all', 'students', 'teachers']:
        systemErrorExit(2, 'show must be all, students or teachers; got %s' % showMembers)
      i += 2
    elif myarg == 'fields':
      if not fieldsList:
        fieldsList = ['id',]
      _processFieldsList(myarg, i, fieldsList)
      i += 2
    elif myarg == 'skipfields':
      _processFieldsList(myarg, i, skipFieldsList)
      i += 2
    elif myarg == 'owneremail':
      ownerEmails = {}
      cd = buildGAPIObject('directory')
      i += 1
    else:
      systemErrorExit(2, '%s is not a valid argument for "gam print courses"' % sys.argv[i])
  if ownerEmails is not None and fieldsList:
    fieldsList.append('ownerId')
  fields = 'nextPageToken,courses({0})'.format(','.join(set(fieldsList))) if fieldsList else None
  printGettingAllItems('Courses', None)
  page_message = 'Got %%num_items%% Courses...\n'
  all_courses = callGAPIpages(croom.courses(), 'list', 'courses', page_message=page_message, teacherId=teacherId, studentId=studentId, courseStates=courseStates, fields=fields)
  for course in all_courses:
    if ownerEmails is not None:
      ownerId = course['ownerId']
      if ownerId not in ownerEmails:
        ownerEmails[ownerId] = convertUIDtoEmailAddress('uid:%s' % ownerId, cd=cd)
      course['ownerEmail'] = ownerEmails[ownerId]
    for field in skipFieldsList:
      course.pop(field, None)
    addRowTitlesToCSVfile(flatten_json(course), csvRows, titles)
  if showAliases or showMembers:
    if showAliases:
      titles.append('Aliases')
    if showMembers:
      if countsOnly:
        teachersFields = 'nextPageToken,teachers(profile(id))'
        studentsFields = 'nextPageToken,students(profile(id))'
      else:
        teachersFields = 'nextPageToken,teachers(profile)'
        studentsFields = 'nextPageToken,students(profile)'
    i = 0
    count = len(csvRows)
    for course in csvRows:
      i += 1
      courseId = course['id']
      if showAliases:
        alias_message = ' Got %%%%num_items%%%% Aliases for course %s%s' % (courseId, currentCount(i, count))
        course_aliases = callGAPIpages(croom.courses().aliases(), 'list', 'aliases',
                                       page_message=alias_message,
                                       courseId=courseId)
        course['Aliases'] = delimiter.join([alias['alias'][2:] for alias in course_aliases])
      if showMembers:
        if showMembers != 'students':
          teacher_message = ' Got %%%%num_items%%%% Teachers for course %s%s' % (courseId, currentCount(i, count))
          results = callGAPIpages(croom.courses().teachers(), 'list', 'teachers',
                                  page_message=teacher_message,
                                  courseId=courseId, fields=teachersFields)
          _saveParticipants(course, results, 'teachers')
        if showMembers != 'teachers':
          student_message = ' Got %%%%num_items%%%% Students for course %s%s' % (courseId, currentCount(i, count))
          results = callGAPIpages(croom.courses().students(), 'list', 'students',
                                  page_message=student_message,
                                  courseId=courseId, fields=studentsFields)
          _saveParticipants(course, results, 'students')
  sortCSVTitles(['id', 'name'], titles)
  writeCSVfile(csvRows, titles, 'Courses', todrive)

def doPrintCourseParticipants():
  croom = buildGAPIObject('classroom')
  todrive = False
  titles = ['courseId',]
  csvRows = []
  courses = []
  teacherId = None
  studentId = None
  courseStates = []
  showMembers = 'all'
  i = 3
  while i < len(sys.argv):
    myarg = sys.argv[i].lower()
    if myarg in ['course', 'class']:
      courses.append(addCourseIdScope(sys.argv[i+1]))
      i += 2
    elif myarg == 'teacher':
      teacherId = normalizeEmailAddressOrUID(sys.argv[i+1])
      i += 2
    elif myarg == 'student':
      studentId = normalizeEmailAddressOrUID(sys.argv[i+1])
      i += 2
    elif myarg in ['state', 'states', 'status']:
      _getCourseStates(croom, sys.argv[i+1], courseStates)
      i += 2
    elif myarg == 'todrive':
      todrive = True
      i += 1
    elif myarg == 'show':
      showMembers = sys.argv[i+1].lower()
      if showMembers not in ['all', 'students', 'teachers']:
        systemErrorExit(2, 'show must be all, students or teachers; got %s' % showMembers)
      i += 2
    else:
      systemErrorExit(2, '%s is not a valid argument for "gam print course-participants"' % sys.argv[i])
  if not courses:
    printGettingAllItems('Courses', None)
    page_message = 'Got %%num_items%% Courses...\n'
    all_courses = callGAPIpages(croom.courses(), 'list', 'courses', page_message=page_message,
                                teacherId=teacherId, studentId=studentId, courseStates=courseStates, fields='nextPageToken,courses(id,name)')
  else:
    all_courses = []
    for course in courses:
      all_courses.append(callGAPI(croom.courses(), 'get', id=course, fields='id,name'))
  i = 0
  count = len(all_courses)
  for course in all_courses:
    i += 1
    courseId = course['id']
    if showMembers != 'students':
      page_message = ' Got %%%%num_items%%%% Teachers for course %s (%s/%s)' % (courseId, i, count)
      teachers = callGAPIpages(croom.courses().teachers(), 'list', 'teachers', page_message=page_message, courseId=courseId)
      for teacher in teachers:
        addRowTitlesToCSVfile(flatten_json(teacher, flattened={'courseId': courseId, 'courseName': course['name'], 'userRole': 'TEACHER'}), csvRows, titles)
    if showMembers != 'teachers':
      page_message = ' Got %%%%num_items%%%% Students for course %s (%s/%s)' % (courseId, i, count)
      students = callGAPIpages(croom.courses().students(), 'list', 'students', page_message=page_message, courseId=courseId)
      for student in students:
        addRowTitlesToCSVfile(flatten_json(student, flattened={'courseId': courseId, 'courseName': course['name'], 'userRole': 'STUDENT'}), csvRows, titles)
  sortCSVTitles(['courseId', 'courseName', 'userRole', 'userId'], titles)
  writeCSVfile(csvRows, titles, 'Course Participants', todrive)

def doPrintPrintJobs():
  cp = buildGAPIObject('cloudprint')
  todrive = False
  titles = ['printerid', 'id']
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
    myarg = sys.argv[i].lower().replace('_', '')
    if myarg == 'todrive':
      todrive = True
      i += 1
    elif myarg in ['olderthan', 'newerthan']:
      if myarg == 'olderthan':
        older_or_newer = 'older'
      else:
        older_or_newer = 'newer'
      age_number = sys.argv[i+1][:-1]
      if not age_number.isdigit():
        systemErrorExit(2, 'expected a number; got %s' % age_number)
      age_unit = sys.argv[i+1][-1].lower()
      if age_unit == 'm':
        age = int(time.time()) - (int(age_number) * 60)
      elif age_unit == 'h':
        age = int(time.time()) - (int(age_number) * 60 * 60)
      elif age_unit == 'd':
        age = int(time.time()) - (int(age_number) * 60 * 60 * 24)
      else:
        systemErrorExit(2, 'expected m (minutes), h (hours) or d (days); got %s' % age_unit)
      i += 2
    elif myarg == 'query':
      query = sys.argv[i+1]
      i += 2
    elif myarg == 'status':
      status = sys.argv[i+1]
      i += 2
    elif myarg == 'ascending':
      descending = False
      i += 1
    elif myarg == 'descending':
      descending = True
      i += 1
    elif myarg == 'orderby':
      sortorder = sys.argv[i+1].lower().replace('_', '')
      if sortorder not in PRINTJOB_ASCENDINGORDER_MAP:
        systemErrorExit(2, 'orderby must be one of %s; got %s' % (', '.join(PRINTJOB_ASCENDINGORDER_MAP), sortorder))
      sortorder = PRINTJOB_ASCENDINGORDER_MAP[sortorder]
      i += 2
    elif myarg in ['printer', 'printerid']:
      printerid = sys.argv[i+1]
      i += 2
    elif myarg in ['owner', 'user']:
      owner = sys.argv[i+1]
      i += 2
    elif myarg == 'limit':
      jobLimit = getInteger(sys.argv[i+1], myarg, minVal=0)
      i += 2
    else:
      systemErrorExit(2, '%s is not a valid argument for "gam print printjobs"' % sys.argv[i])
  if sortorder and descending:
    sortorder = PRINTJOB_DESCENDINGORDER_MAP[sortorder]
  if printerid:
    result = callGAPI(cp.printers(), 'get',
                      printerid=printerid)
    checkCloudPrintResult(result)
  if ((not sortorder) or (sortorder == 'CREATE_TIME_DESC')) and (older_or_newer == 'newer'):
    timeExit = True
  elif (sortorder == 'CREATE_TIME') and (older_or_newer == 'older'):
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
    result = callGAPI(cp.jobs(), 'list',
                      printerid=printerid, q=query, status=status, sortorder=sortorder,
                      owner=owner, offset=offset, limit=limit)
    checkCloudPrintResult(result)
    newJobs = result['range']['jobsCount']
    totalJobs = int(result['range']['jobsTotal'])
    if GC_Values[GC_DEBUG_LEVEL] > 0:
      sys.stderr.write('Debug: jobCount: {0}, jobLimit: {1}, jobsCount: {2}, jobsTotal: {3}\n'.format(jobCount, jobLimit, newJobs, totalJobs))
    if newJobs == 0:
      break
    jobCount += newJobs
    offset += newJobs
    for job in result['jobs']:
      createTime = int(job['createTime'])/1000
      if older_or_newer:
        if older_or_newer == 'older' and createTime > age:
          if timeExit:
            jobCount = totalJobs
            break
          continue
        elif older_or_newer == 'newer' and createTime < age:
          if timeExit:
            jobCount = totalJobs
            break
          continue
      updateTime = int(job['updateTime'])/1000
      job['createTime'] = datetime.datetime.fromtimestamp(createTime).strftime('%Y-%m-%d %H:%M:%S')
      job['updateTime'] = datetime.datetime.fromtimestamp(updateTime).strftime('%Y-%m-%d %H:%M:%S')
      job['tags'] = ' '.join(job['tags'])
      addRowTitlesToCSVfile(flatten_json(job), csvRows, titles)
    if jobCount >= totalJobs:
      break
  writeCSVfile(csvRows, titles, 'Print Jobs', todrive)

def doPrintPrinters():
  cp = buildGAPIObject('cloudprint')
  todrive = False
  titles = ['id',]
  csvRows = []
  queries = [None]
  printer_type = None
  connection_status = None
  extra_fields = None
  i = 3
  while i < len(sys.argv):
    myarg = sys.argv[i].lower().replace('_', '')
    if myarg in ['query', 'queries']:
      queries = getQueries(myarg, sys.argv[i+1])
      i += 2
    elif myarg == 'type':
      printer_type = sys.argv[i+1]
      i += 2
    elif myarg == 'status':
      connection_status = sys.argv[i+1]
      i += 2
    elif myarg == 'extrafields':
      extra_fields = sys.argv[i+1]
      i += 2
    elif myarg == 'todrive':
      todrive = True
      i += 1
    else:
      systemErrorExit(2, '%s is not a valid argument for "gam print printers"' % sys.argv[i])
  for query in queries:
    printers = callGAPI(cp.printers(), 'list', q=query, type=printer_type, connection_status=connection_status, extra_fields=extra_fields)
    checkCloudPrintResult(printers)
    for printer in printers['printers']:
      createTime = int(printer['createTime'])/1000
      accessTime = int(printer['accessTime'])/1000
      updateTime = int(printer['updateTime'])/1000
      printer['createTime'] = datetime.datetime.fromtimestamp(createTime).strftime('%Y-%m-%d %H:%M:%S')
      printer['accessTime'] = datetime.datetime.fromtimestamp(accessTime).strftime('%Y-%m-%d %H:%M:%S')
      printer['updateTime'] = datetime.datetime.fromtimestamp(updateTime).strftime('%Y-%m-%d %H:%M:%S')
      printer['tags'] = ' '.join(printer['tags'])
      addRowTitlesToCSVfile(flatten_json(printer), csvRows, titles)
  writeCSVfile(csvRows, titles, 'Printers', todrive)

def changeCalendarAttendees(users):
  do_it = True
  i = 5
  allevents = False
  start_date = end_date = None
  while len(sys.argv) > i:
    myarg = sys.argv[i].lower()
    if myarg == 'csv':
      csv_file = sys.argv[i+1]
      i += 2
    elif myarg == 'dryrun':
      do_it = False
      i += 1
    elif myarg == 'start':
      start_date = getTimeOrDeltaFromNow(sys.argv[i+1])
      i += 2
    elif myarg == 'end':
      end_date = getTimeOrDeltaFromNow(sys.argv[i+1])
      i += 2
    elif myarg == 'allevents':
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
    sys.stdout.write('Checking user %s\n' % user)
    user, cal = buildCalendarGAPIObject(user)
    if not cal:
      continue
    page_token = None
    while True:
      events_page = callGAPI(cal.events(), 'list', calendarId=user, pageToken=page_token, timeMin=start_date, timeMax=end_date, showDeleted=False, showHiddenInvitations=False)
      print('Got %s items' % len(events_page.get('items', [])))
      for event in events_page.get('items', []):
        if event['status'] == 'cancelled':
          #print u' skipping cancelled event'
          continue
        try:
          event_summary = utils.convertUTF8(event['summary'])
        except (KeyError, UnicodeEncodeError, UnicodeDecodeError):
          event_summary = event['id']
        try:
          if not allevents and event['organizer']['email'].lower() != user:
            #print u' skipping not-my-event %s' % event_summary
            continue
        except KeyError:
          pass # no email for organizer
        needs_update = False
        try:
          for attendee in event['attendees']:
            try:
              if attendee['email'].lower() in attendee_map:
                old_email = attendee['email'].lower()
                new_email = attendee_map[attendee['email'].lower()]
                print(' SWITCHING attendee %s to %s for %s' % (old_email, new_email, event_summary))
                event['attendees'].remove(attendee)
                event['attendees'].append({'email': new_email})
                needs_update = True
            except KeyError: # no email for that attendee
              pass
        except KeyError:
          continue # no attendees
        if needs_update:
          body = {}
          body['attendees'] = event['attendees']
          print('UPDATING %s' % event_summary)
          if do_it:
            callGAPI(cal.events(), 'patch', calendarId=user, eventId=event['id'], sendNotifications=False, body=body)
          else:
            print(' not pulling the trigger.')
        #else:
        #  print u' no update needed for %s' % event_summary
      try:
        page_token = events_page['nextPageToken']
      except KeyError:
        break

def deleteCalendar(users):
  calendarId = normalizeCalendarId(sys.argv[5])
  for user in users:
    user, cal = buildCalendarGAPIObject(user)
    if not cal:
      continue
    callGAPI(cal.calendarList(), 'delete', soft_errors=True, calendarId=calendarId)

CALENDAR_REMINDER_MAX_MINUTES = 40320

CALENDAR_MIN_COLOR_INDEX = 1
CALENDAR_MAX_COLOR_INDEX = 24

CALENDAR_EVENT_MIN_COLOR_INDEX = 1
CALENDAR_EVENT_MAX_COLOR_INDEX = 11

def getCalendarAttributes(i, body, function):
  colorRgbFormat = False
  while i < len(sys.argv):
    myarg = sys.argv[i].lower().replace('_', '')
    if myarg == 'selected':
      body['selected'] = getBoolean(sys.argv[i+1], myarg)
      i += 2
    elif myarg == 'hidden':
      body['hidden'] = getBoolean(sys.argv[i+1], myarg)
      i += 2
    elif myarg == 'summary':
      body['summaryOverride'] = sys.argv[i+1]
      i += 2
    elif myarg == 'colorindex':
      body['colorId'] = getInteger(sys.argv[i+1], myarg, minVal=CALENDAR_MIN_COLOR_INDEX, maxVal=CALENDAR_MAX_COLOR_INDEX)
      i += 2
    elif myarg == 'backgroundcolor':
      body['backgroundColor'] = getColor(sys.argv[i+1])
      colorRgbFormat = True
      i += 2
    elif myarg == 'foregroundcolor':
      body['foregroundColor'] = getColor(sys.argv[i+1])
      colorRgbFormat = True
      i += 2
    elif myarg == 'reminder':
      body.setdefault('defaultReminders', [])
      method = sys.argv[i+1].lower()
      if method not in CLEAR_NONE_ARGUMENT:
        if method not in CALENDAR_REMINDER_METHODS:
          systemErrorExit(2, 'Method must be one of %s; got %s' % (', '.join(CALENDAR_REMINDER_METHODS+CLEAR_NONE_ARGUMENT), method))
        minutes = getInteger(sys.argv[i+2], myarg, minVal=0, maxVal=CALENDAR_REMINDER_MAX_MINUTES)
        body['defaultReminders'].append({'method': method, 'minutes': minutes})
        i += 3
      else:
        i += 2
    elif myarg == 'notification':
      body.setdefault('notificationSettings', {'notifications': []})
      method = sys.argv[i+1].lower()
      if method not in CLEAR_NONE_ARGUMENT:
        if method not in CALENDAR_NOTIFICATION_METHODS:
          systemErrorExit(2, 'Method must be one of %s; got %s' % (', '.join(CALENDAR_NOTIFICATION_METHODS+CLEAR_NONE_ARGUMENT), method))
        eventType = sys.argv[i+2].lower()
        if eventType not in CALENDAR_NOTIFICATION_TYPES_MAP:
          systemErrorExit(2, 'Event must be one of %s; got %s' % (', '.join(CALENDAR_NOTIFICATION_TYPES_MAP), eventType))
        body['notificationSettings']['notifications'].append({'method': method, 'type': CALENDAR_NOTIFICATION_TYPES_MAP[eventType]})
        i += 3
      else:
        i += 2
    else:
      systemErrorExit(2, '%s is not a valid argument for "gam %s calendar"' % (sys.argv[i], function))
  return colorRgbFormat

def addCalendar(users):
  calendarId = normalizeCalendarId(sys.argv[5])
  body = {'id': calendarId, 'selected': True, 'hidden': False}
  colorRgbFormat = getCalendarAttributes(6, body, 'add')
  i = 0
  count = len(users)
  for user in users:
    i += 1
    user, cal = buildCalendarGAPIObject(user)
    if not cal:
      continue
    print("Subscribing %s to %s calendar (%s/%s)" % (user, calendarId, i, count))
    callGAPI(cal.calendarList(), 'insert', soft_errors=True, body=body, colorRgbFormat=colorRgbFormat)

def updateCalendar(users):
  calendarId = normalizeCalendarId(sys.argv[5], checkPrimary=True)
  body = {}
  colorRgbFormat = getCalendarAttributes(6, body, 'update')
  i = 0
  count = len(users)
  for user in users:
    i += 1
    user, cal = buildCalendarGAPIObject(user)
    if not cal:
      continue
    print("Updating %s's subscription to calendar %s (%s/%s)" % (user, calendarId, i, count))
    calId = calendarId if calendarId != 'primary' else user
    callGAPI(cal.calendarList(), 'patch', soft_errors=True, calendarId=calId, body=body, colorRgbFormat=colorRgbFormat)

def doPrinterShowACL():
  cp = buildGAPIObject('cloudprint')
  show_printer = sys.argv[2]
  printer_info = callGAPI(cp.printers(), 'get', printerid=show_printer)
  checkCloudPrintResult(printer_info)
  for acl in printer_info['printers'][0]['access']:
    if 'key' in acl:
      acl['accessURL'] = 'https://www.google.com/cloudprint/addpublicprinter.html?printerid=%s&key=%s' % (show_printer, acl['key'])
    print_json(None, acl)
    print()

def doPrinterAddACL():
  cp = buildGAPIObject('cloudprint')
  printer = sys.argv[2]
  role = sys.argv[4].upper()
  scope = sys.argv[5]
  notify = bool(len(sys.argv) > 6 and sys.argv[6].lower() == 'notify')
  public = None
  skip_notification = True
  if scope.lower() == 'public':
    public = True
    scope = None
    role = None
    skip_notification = None
  elif scope.find('@') == -1:
    scope = '/hd/domain/%s' % scope
  else:
    skip_notification = not notify
  result = callGAPI(cp.printers(), 'share', printerid=printer, role=role, scope=scope, public=public, skip_notification=skip_notification)
  checkCloudPrintResult(result)
  who = scope
  if who is None:
    who = 'public'
    role = 'user'
  print('Added %s %s' % (role, who))

def doPrinterDelACL():
  cp = buildGAPIObject('cloudprint')
  printer = sys.argv[2]
  scope = sys.argv[4]
  public = None
  if scope.lower() == 'public':
    public = True
    scope = None
  elif scope.find('@') == -1:
    scope = '/hd/domain/%s' % scope
  result = callGAPI(cp.printers(), 'unshare', printerid=printer, scope=scope, public=public)
  checkCloudPrintResult(result)
  who = scope
  if who is None:
    who = 'public'
  print('Removed %s' % who)

def encode_multipart(fields, files, boundary=None):
  def escape_quote(s):
    return s.replace('"', '\\"')

  def getFormDataLine(name, value, boundary):
    return '--{0}'.format(boundary), 'Content-Disposition: form-data; name="{0}"'.format(escape_quote(name)), '', str(value)

  if boundary is None:
    boundary = ''.join(random.choice(string.digits + string.ascii_letters) for i in range(30))
  lines = []
  for name, value in list(fields.items()):
    if name == 'tags':
      for tag in value:
        lines.extend(getFormDataLine('tag', tag, boundary))
    else:
      lines.extend(getFormDataLine(name, value, boundary))
  for name, value in list(files.items()):
    filename = value['filename']
    mimetype = value['mimetype']
    lines.extend((
      '--{0}'.format(boundary),
      'Content-Disposition: form-data; name="{0}"; filename="{1}"'.format(escape_quote(name), escape_quote(filename)),
      'Content-Type: {0}'.format(mimetype),
      '',
      value['content'],
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
  cp = buildGAPIObject('cloudprint')
  printerid = sys.argv[2]
  if printerid == 'any':
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
    myarg = sys.argv[i].lower().replace('_', '')
    if myarg in ['olderthan', 'newerthan']:
      if myarg == 'olderthan':
        older_or_newer = 'older'
      else:
        older_or_newer = 'newer'
      age_number = sys.argv[i+1][:-1]
      if not age_number.isdigit():
        systemErrorExit(2, 'expected a number; got %s' % age_number)
      age_unit = sys.argv[i+1][-1].lower()
      if age_unit == 'm':
        age = int(time.time()) - (int(age_number) * 60)
      elif age_unit == 'h':
        age = int(time.time()) - (int(age_number) * 60 * 60)
      elif age_unit == 'd':
        age = int(time.time()) - (int(age_number) * 60 * 60 * 24)
      else:
        systemErrorExit(2, 'expected m (minutes), h (hours) or d (days); got %s' % age_unit)
      i += 2
    elif myarg == 'query':
      query = sys.argv[i+1]
      i += 2
    elif myarg == 'status':
      status = sys.argv[i+1]
      i += 2
    elif myarg == 'ascending':
      descending = False
      i += 1
    elif myarg == 'descending':
      descending = True
      i += 1
    elif myarg == 'orderby':
      sortorder = sys.argv[i+1].lower().replace('_', '')
      if sortorder not in PRINTJOB_ASCENDINGORDER_MAP:
        systemErrorExit(2, 'orderby must be one of %s; got %s' % (', '.join(PRINTJOB_ASCENDINGORDER_MAP), sortorder))
      sortorder = PRINTJOB_ASCENDINGORDER_MAP[sortorder]
      i += 2
    elif myarg in ['owner', 'user']:
      owner = sys.argv[i+1]
      i += 2
    elif myarg == 'limit':
      jobLimit = getInteger(sys.argv[i+1], myarg, minVal=0)
      i += 2
    elif myarg == 'drivedir':
      targetFolder = GC_Values[GC_DRIVE_DIR]
      i += 1
    elif myarg == 'targetfolder':
      targetFolder = os.path.expanduser(sys.argv[i+1])
      if not os.path.isdir(targetFolder):
        os.makedirs(targetFolder)
      i += 2
    else:
      systemErrorExit(2, '%s is not a valid argument for "gam printjobs fetch"' % sys.argv[i])
  if sortorder and descending:
    sortorder = PRINTJOB_DESCENDINGORDER_MAP[sortorder]
  if printerid:
    result = callGAPI(cp.printers(), 'get',
                      printerid=printerid)
    checkCloudPrintResult(result)
  valid_chars = '-_.() abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789'
  ssd = '{"state": {"type": "DONE"}}'
  if ((not sortorder) or (sortorder == 'CREATE_TIME_DESC')) and (older_or_newer == 'newer'):
    timeExit = True
  elif (sortorder == 'CREATE_TIME') and (older_or_newer == 'older'):
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
    result = callGAPI(cp.jobs(), 'list',
                      printerid=printerid, q=query, status=status, sortorder=sortorder,
                      owner=owner, offset=offset, limit=limit)
    checkCloudPrintResult(result)
    newJobs = result['range']['jobsCount']
    totalJobs = int(result['range']['jobsTotal'])
    if newJobs == 0:
      break
    jobCount += newJobs
    offset += newJobs
    for job in result['jobs']:
      createTime = int(job['createTime'])/1000
      if older_or_newer:
        if older_or_newer == 'older' and createTime > age:
          if timeExit:
            jobCount = totalJobs
            break
          continue
        elif older_or_newer == 'newer' and createTime < age:
          if timeExit:
            jobCount = totalJobs
            break
          continue
      fileUrl = job['fileUrl']
      jobid = job['id']
      fileName = os.path.join(targetFolder, '{0}-{1}'.format(''.join(c if c in valid_chars else '_' for c in job['title']), jobid))
      _, content = cp._http.request(uri=fileUrl, method='GET')
      if writeFile(fileName, content, continueOnError=True):
#        ticket = callGAPI(cp.jobs(), u'getticket', jobid=jobid, use_cjt=True)
        result = callGAPI(cp.jobs(), 'update', jobid=jobid, semantic_state_diff=ssd)
        checkCloudPrintResult(result)
        print('Printed job %s to %s' % (jobid, fileName))
    if jobCount >= totalJobs:
      break
  if jobCount == 0:
    print('No print jobs.')

def doDelPrinter():
  cp = buildGAPIObject('cloudprint')
  printerid = sys.argv[3]
  result = callGAPI(cp.printers(), 'delete', printerid=printerid)
  checkCloudPrintResult(result)

def doGetPrinterInfo():
  cp = buildGAPIObject('cloudprint')
  printerid = sys.argv[3]
  everything = False
  i = 4
  while i < len(sys.argv):
    myarg = sys.argv[i].lower()
    if myarg == 'everything':
      everything = True
      i += 1
    else:
      systemErrorExit(2, '%s is not a valid argument for "gam info printer"' % sys.argv[i])
  result = callGAPI(cp.printers(), 'get', printerid=printerid)
  checkCloudPrintResult(result)
  printer_info = result['printers'][0]
  createTime = int(printer_info['createTime'])/1000
  accessTime = int(printer_info['accessTime'])/1000
  updateTime = int(printer_info['updateTime'])/1000
  printer_info['createTime'] = datetime.datetime.fromtimestamp(createTime).strftime('%Y-%m-%d %H:%M:%S')
  printer_info['accessTime'] = datetime.datetime.fromtimestamp(accessTime).strftime('%Y-%m-%d %H:%M:%S')
  printer_info['updateTime'] = datetime.datetime.fromtimestamp(updateTime).strftime('%Y-%m-%d %H:%M:%S')
  printer_info['tags'] = ' '.join(printer_info['tags'])
  if not everything:
    del printer_info['capabilities']
    del printer_info['access']
  print_json(None, printer_info)

def doUpdatePrinter():
  cp = buildGAPIObject('cloudprint')
  printerid = sys.argv[3]
  kwargs = {}
  i = 4
  update_items = ['isTosAccepted', 'gcpVersion', 'setupUrl',
                  'quotaEnabled', 'id', 'supportUrl', 'firmware',
                  'currentQuota', 'type', 'public', 'status', 'description',
                  'defaultDisplayName', 'proxy', 'dailyQuota', 'manufacturer',
                  'displayName', 'name', 'uuid', 'updateUrl', 'ownerId', 'model']
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
  result = callGAPI(cp.printers(), 'update', printerid=printerid, **kwargs)
  checkCloudPrintResult(result)
  print('Updated printer %s' % printerid)

def doPrinterRegister():
  cp = buildGAPIObject('cloudprint')
  form_fields = {'name': 'GAM',
                 'proxy': 'GAM',
                 'uuid': _getValueFromOAuth('sub'),
                 'manufacturer': gam_author,
                 'model': 'cp1',
                 'gcp_version': '2.0',
                 'setup_url': GAM_URL,
                 'support_url': 'https://groups.google.com/forum/#!forum/google-apps-manager',
                 'update_url': GAM_RELEASES,
                 'firmware': gam_version,
                 'semantic_state': {"version": "1.0", "printer": {"state": "IDLE",}},
                 'use_cdd': True,
                 'capabilities': {"version": "1.0",
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
                 'tags': ['GAM', GAM_URL],
                }
  body, headers = encode_multipart(form_fields, {})
  #Get the printer first to make sure our OAuth access token is fresh
  callGAPI(cp.printers(), 'list')
  _, result = cp._http.request(uri='https://www.google.com/cloudprint/register', method='POST', body=body, headers=headers)
  result = json.loads(result)
  checkCloudPrintResult(result)
  print('Created printer %s' % result['printers'][0]['id'])

def doPrintJobResubmit():
  cp = buildGAPIObject('cloudprint')
  jobid = sys.argv[2]
  printerid = sys.argv[4]
  ssd = '{"state": {"type": "HELD"}}'
  result = callGAPI(cp.jobs(), 'update', jobid=jobid, semantic_state_diff=ssd)
  checkCloudPrintResult(result)
  ticket = callGAPI(cp.jobs(), 'getticket', jobid=jobid, use_cjt=True)
  result = callGAPI(cp.jobs(), 'resubmit', printerid=printerid, jobid=jobid, ticket=ticket)
  checkCloudPrintResult(result)
  print('Success resubmitting %s as job %s to printer %s' % (jobid, result['job']['id'], printerid))

def doPrintJobSubmit():
  cp = buildGAPIObject('cloudprint')
  printer = sys.argv[2]
  content = sys.argv[4]
  form_fields = {'printerid': printer,
                 'title': content,
                 'ticket': '{"version": "1.0"}',
                 'tags': ['GAM', GAM_URL]}
  i = 5
  while i < len(sys.argv):
    myarg = sys.argv[i].lower()
    if myarg == 'tag':
      form_fields['tags'].append(sys.argv[i+1])
      i += 2
    elif myarg in ['name', 'title']:
      form_fields['title'] = sys.argv[i+1]
      i += 2
    else:
      systemErrorExit(2, '%s is not a valid argument for "gam printer ... print"' % sys.argv[i])
  form_files = {}
  if content[:4] == 'http':
    form_fields['content'] = content
    form_fields['contentType'] = 'url'
  else:
    filepath = content
    content = os.path.basename(content)
    mimetype = mimetypes.guess_type(filepath)[0]
    if mimetype is None:
      mimetype = 'application/octet-stream'
    filecontent = readFile(filepath, mode='rb')
    form_files['content'] = {'filename': content, 'content': filecontent, 'mimetype': mimetype}
  #result = callGAPI(cp.printers(), u'submit', body=body)
  body, headers = encode_multipart(form_fields, form_files)
  #Get the printer first to make sure our OAuth access token is fresh
  callGAPI(cp.printers(), 'get', printerid=printer)
  _, result = cp._http.request(uri='https://www.google.com/cloudprint/submit', method='POST', body=body, headers=headers)
  checkCloudPrintResult(result)
  if isinstance(result, str):
    result = json.loads(result)
  print('Submitted print job %s' % result['job']['id'])

def doDeletePrintJob():
  cp = buildGAPIObject('cloudprint')
  job = sys.argv[2]
  result = callGAPI(cp.jobs(), 'delete', jobid=job)
  checkCloudPrintResult(result)
  print('Print Job %s deleted' % job)

def doCancelPrintJob():
  cp = buildGAPIObject('cloudprint')
  job = sys.argv[2]
  ssd = '{"state": {"type": "ABORTED", "user_action_cause": {"action_code": "CANCELLED"}}}'
  result = callGAPI(cp.jobs(), 'update', jobid=job, semantic_state_diff=ssd)
  checkCloudPrintResult(result)
  print('Print Job %s cancelled' % job)

def checkCloudPrintResult(result):
  if isinstance(result, str):
    try:
      result = json.loads(result)
    except ValueError:
      systemErrorExit(3, 'unexpected response: %s' % result)
  if not result['success']:
    systemErrorExit(result['errorCode'], '%s: %s' % (result['errorCode'], result['message']))

def formatACLScope(rule):
  if rule['scope']['type'] != 'default':
    return '(Scope: {0}:{1})'.format(rule['scope']['type'], rule['scope']['value'])
  return '(Scope: {0})'.format(rule['scope']['type'])

def formatACLRule(rule):
  if rule['scope']['type'] != 'default':
    return '(Scope: {0}:{1}, Role: {2})'.format(rule['scope']['type'], rule['scope']['value'], rule['role'])
  return '(Scope: {0}, Role: {1})'.format(rule['scope']['type'], rule['role'])

def doCalendarShowACL():
  calendarId, cal = buildCalendarDataGAPIObject(sys.argv[2])
  if not cal:
    return
  acls = callGAPIpages(cal.acl(), 'list', 'items', calendarId=calendarId, fields='nextPageToken,items(role,scope)')
  i = 0
  count = len(acls)
  for rule in acls:
    i += 1
    print('Calendar: {0}, ACL: {1}{2}'.format(calendarId, formatACLRule(rule), currentCount(i, count)))

def _getCalendarACLScope(i, body):
  body['scope'] = {}
  myarg = sys.argv[i].lower()
  body['scope']['type'] = myarg
  i += 1
  if myarg in ['user', 'group']:
    body['scope']['value'] = normalizeEmailAddressOrUID(sys.argv[i], noUid=True)
    i += 1
  elif myarg == 'domain':
    if i < len(sys.argv) and sys.argv[i].lower().replace('_', '') != 'sendnotifications':
      body['scope']['value'] = sys.argv[i].lower()
      i += 1
    else:
      body['scope']['value'] = GC_Values[GC_DOMAIN]
  elif myarg != 'default':
    body['scope']['type'] = 'user'
    body['scope']['value'] = normalizeEmailAddressOrUID(myarg, noUid=True)
  return i

CALENDAR_ACL_ROLES_MAP = {
  'editor': 'writer',
  'freebusy': 'freeBusyReader',
  'freebusyreader': 'freeBusyReader',
  'owner': 'owner',
  'read': 'reader',
  'reader': 'reader',
  'writer': 'writer',
  'none': 'none',
  }

def doCalendarAddACL(function):
  calendarId, cal = buildCalendarDataGAPIObject(sys.argv[2])
  if not cal:
    return
  myarg = sys.argv[4].lower().replace('_', '')
  if myarg not in CALENDAR_ACL_ROLES_MAP:
    systemErrorExit(2, 'Role must be one of %s; got %s' % (', '.join(sorted(CALENDAR_ACL_ROLES_MAP.keys())), myarg))
  body = {'role': CALENDAR_ACL_ROLES_MAP[myarg]}
  i = _getCalendarACLScope(5, body)
  sendNotifications = True
  while i < len(sys.argv):
    myarg = sys.argv[i].lower().replace('_', '')
    if myarg == 'sendnotifications':
      sendNotifications = getBoolean(sys.argv[i+1], myarg)
      i += 2
    else:
      systemErrorExit(2, '%s is not a valid argument for "gam calendar <email> %s"' % (sys.argv[i], function.lower()))
  print('Calendar: {0}, {1} ACL: {2}'.format(calendarId, function, formatACLRule(body)))
  callGAPI(cal.acl(), 'insert', calendarId=calendarId, body=body, sendNotifications=sendNotifications)

def doCalendarDelACL():
  calendarId, cal = buildCalendarDataGAPIObject(sys.argv[2])
  if not cal:
    return
  body = {'role': 'none'}
  _getCalendarACLScope(5, body)
  print('Calendar: {0}, {1} ACL: {2}'.format(calendarId, 'Delete', formatACLScope(body)))
  callGAPI(cal.acl(), 'insert', calendarId=calendarId, body=body, sendNotifications=False)

def doCalendarWipeData():
  calendarId, cal = buildCalendarDataGAPIObject(sys.argv[2])
  if not cal:
    return
  callGAPI(cal.calendars(), 'clear', calendarId=calendarId)

def doCalendarDeleteEvent():
  calendarId, cal = buildCalendarDataGAPIObject(sys.argv[2])
  if not cal:
    return
  events = []
  sendNotifications = None
  doit = False
  i = 4
  while i < len(sys.argv):
    myarg = sys.argv[i].lower().replace('_', '')
    if myarg == 'notifyattendees':
      sendNotifications = True
      i += 1
    elif myarg in ['id', 'eventid']:
      events.append(sys.argv[i+1])
      i += 2
    elif myarg in ['query', 'eventquery']:
      query = sys.argv[i+1]
      result = callGAPIpages(cal.events(), 'list', 'items', calendarId=calendarId, q=query)
      for event in result:
        if 'id' in event and event['id'] not in events:
          events.append(event['id'])
      i += 2
    elif myarg == 'doit':
      doit = True
      i += 1
    else:
      systemErrorExit(2, '%s is not a valid argument for "gam calendar <email> deleteevent"' % sys.argv[i])
  if doit:
    for eventId in events:
      print(' deleting eventId %s' % eventId)
      callGAPI(cal.events(), 'delete', calendarId=calendarId, eventId=eventId, sendNotifications=sendNotifications)
  else:
    for eventId in events:
      print(' would delete eventId %s. Add doit to command to actually delete event' % eventId)

def doCalendarAddEvent():
  calendarId, cal = buildCalendarDataGAPIObject(sys.argv[2])
  if not cal:
    return
  sendNotifications = timeZone = None
  i = 4
  body = {}
  while i < len(sys.argv):
    myarg = sys.argv[i].lower().replace('_', '')
    if myarg == 'notifyattendees':
      sendNotifications = True
      i += 1
    elif myarg == 'attendee':
      body.setdefault('attendees', [])
      body['attendees'].append({'email': sys.argv[i+1]})
      i += 2
    elif myarg == 'optionalattendee':
      body.setdefault('attendees', [])
      body['attendees'].append({'email': sys.argv[i+1], 'optional': True})
      i += 2
    elif myarg == 'anyonecanaddself':
      body['anyoneCanAddSelf'] = True
      i += 1
    elif myarg == 'description':
      body['description'] = sys.argv[i+1].replace('\\n', '\n')
      i += 2
    elif myarg == 'start':
      if sys.argv[i+1].lower() == 'allday':
        body['start'] = {'date': getYYYYMMDD(sys.argv[i+2])}
        i += 3
      else:
        body['start'] = {'dateTime': getTimeOrDeltaFromNow(sys.argv[i+1])}
        i += 2
    elif myarg == 'end':
      if sys.argv[i+1].lower() == 'allday':
        body['end'] = {'date': getYYYYMMDD(sys.argv[i+2])}
        i += 3
      else:
        body['end'] = {'dateTime': getTimeOrDeltaFromNow(sys.argv[i+1])}
        i += 2
    elif myarg == 'guestscantinviteothers':
      body['guestsCanInviteOthers'] = False
      i += 1
    elif myarg == 'guestscantseeothers':
      body['guestsCanSeeOtherGuests'] = False
      i += 1
    elif myarg == 'id':
      body['id'] = sys.argv[i+1]
      i += 2
    elif myarg == 'summary':
      body['summary'] = sys.argv[i+1]
      i += 2
    elif myarg == 'location':
      body['location'] = sys.argv[i+1]
      i += 2
    elif myarg == 'available':
      body['transparency'] = 'transparent'
      i += 1
    elif myarg == 'visibility':
      if sys.argv[i+1].lower() in ['default', 'public', 'private']:
        body['visibility'] = sys.argv[i+1].lower()
      else:
        systemErrorExit(2, 'visibility must be one of default, public, private; got %s' % sys.argv[i+1])
      i += 2
    elif myarg == 'tentative':
      body['status'] = 'tentative'
      i += 1
    elif myarg == 'source':
      body['source'] = {'title': sys.argv[i+1], 'url': sys.argv[i+2]}
      i += 3
    elif myarg == 'noreminders':
      body['reminders'] = {'useDefault': False}
      i += 1
    elif myarg == 'reminder':
      body.setdefault('reminders', {'overrides': [], 'useDefault': False})
      body['reminders']['overrides'].append({'minutes': getInteger(sys.argv[i+1], myarg, minVal=0, maxVal=CALENDAR_REMINDER_MAX_MINUTES),
                                             'method': sys.argv[i+2]})
      i += 3
    elif myarg == 'recurrence':
      body.setdefault('recurrence', [])
      body['recurrence'].append(sys.argv[i+1])
      i += 2
    elif myarg == 'timezone':
      timeZone = sys.argv[i+1]
      i += 2
    elif myarg == 'privateproperty':
      if 'extendedProperties' not in body:
        body['extendedProperties'] = {'private': {}, 'shared': {}}
      body['extendedProperties']['private'][sys.argv[i+1]] = sys.argv[i+2]
      i += 3
    elif myarg == 'sharedproperty':
      if 'extendedProperties' not in body:
        body['extendedProperties'] = {'private': {}, 'shared': {}}
      body['extendedProperties']['shared'][sys.argv[i+1]] = sys.argv[i+2]
      i += 3
    elif myarg == 'colorindex':
      body['colorId'] = getInteger(sys.argv[i+1], myarg, CALENDAR_EVENT_MIN_COLOR_INDEX, CALENDAR_EVENT_MAX_COLOR_INDEX)
      i += 2
    else:
      systemErrorExit(2, '%s is not a valid argument for "gam calendar <email> addevent"' % sys.argv[i])
  if ('recurrence' in body) and (('start' in body) or ('end' in body)):
    if not timeZone:
      timeZone = callGAPI(cal.calendars(), 'get', calendarId=calendarId, fields='timeZone')['timeZone']
    if 'start' in body:
      body['start']['timeZone'] = timeZone
    if 'end' in body:
      body['end']['timeZone'] = timeZone
  callGAPI(cal.events(), 'insert', calendarId=calendarId, sendNotifications=sendNotifications, body=body)

def doCalendarModifySettings():
  calendarId, cal = buildCalendarDataGAPIObject(sys.argv[2])
  if not cal:
    return
  body = {}
  i = 4
  while i < len(sys.argv):
    myarg = sys.argv[i].lower().replace('_', '')
    if myarg == 'description':
      body['description'] = sys.argv[i+1]
      i += 2
    elif myarg == 'location':
      body['location'] = sys.argv[i+1]
      i += 2
    elif myarg == 'summary':
      body['summary'] = sys.argv[i+1]
      i += 2
    elif myarg == 'timezone':
      body['timeZone'] = sys.argv[i+1]
      i += 2
    else:
      systemErrorExit(2, '%s is not a valid argument for "gam calendar <email> modify"' % sys.argv[i])
  callGAPI(cal.calendars(), 'patch', calendarId=calendarId, body=body)

def doProfile(users):
  cd = buildGAPIObject('directory')
  myarg = sys.argv[4].lower()
  if myarg in ['share', 'shared']:
    body = {'includeInGlobalAddressList': True}
  elif myarg in ['unshare', 'unshared']:
    body = {'includeInGlobalAddressList': False}
  else:
    systemErrorExit(2, 'value for "gam <users> profile" must be true or false; got %s' % sys.argv[4])
  i = 0
  count = len(users)
  for user in users:
    i += 1
    print('Setting Profile Sharing to %s for %s (%s/%s)' % (body['includeInGlobalAddressList'], user, i, count))
    callGAPI(cd.users(), 'update', soft_errors=True, userKey=user, body=body)

def showProfile(users):
  cd = buildGAPIObject('directory')
  i = 0
  count = len(users)
  for user in users:
    i += 1
    result = callGAPI(cd.users(), 'get', userKey=user, fields='includeInGlobalAddressList')
    try:
      print('User: %s  Profile Shared: %s (%s/%s)' % (user, result['includeInGlobalAddressList'], i, count))
    except IndexError:
      pass

def doPhoto(users):
  cd = buildGAPIObject('directory')
  i = 0
  count = len(users)
  for user in users:
    i += 1
    filename = sys.argv[5].replace('#user#', user)
    filename = filename.replace('#email#', user)
    filename = filename.replace('#username#', user[:user.find('@')])
    print("Updating photo for %s with %s (%s/%s)" % (user, filename, i, count))
    if re.match('^(ht|f)tps?://.*$', filename):
      simplehttp = httplib2.Http(disable_ssl_certificate_validation=GC_Values[GC_NO_VERIFY_SSL])
      try:
        (_, image_data) = simplehttp.request(filename, 'GET')
      except (httplib2.HttpLib2Error, httplib2.ServerNotFoundError) as e:
        print(e)
        continue
    else:
      image_data = readFile(filename, mode='rb', continueOnError=True, displayError=True)
      if image_data is None:
        continue
    body = {'photoData': base64.urlsafe_b64encode(image_data).decode('utf-8')}
    callGAPI(cd.users().photos(), 'update', soft_errors=True, userKey=user, body=body)

def getPhoto(users):
  cd = buildGAPIObject('directory')
  targetFolder = os.getcwd()
  showPhotoData = True
  i = 5
  while i < len(sys.argv):
    myarg = sys.argv[i].lower().replace('_', '')
    if myarg == 'drivedir':
      targetFolder = GC_Values[GC_DRIVE_DIR]
      i += 1
    elif myarg == 'targetfolder':
      targetFolder = os.path.expanduser(sys.argv[i+1])
      if not os.path.isdir(targetFolder):
        os.makedirs(targetFolder)
      i += 2
    elif myarg == 'noshow':
      showPhotoData = False
      i += 1
    else:
      systemErrorExit(2, '%s is not a valid argument for "gam <users> get photo"' % sys.argv[i])
  i = 0
  count = len(users)
  for user in users:
    i += 1
    filename = os.path.join(targetFolder, '{0}.jpg'.format(user))
    print("Saving photo to %s (%s/%s)" % (filename, i, count))
    try:
      photo = callGAPI(cd.users().photos(), 'get', throw_reasons=[GAPI_USER_NOT_FOUND, GAPI_RESOURCE_NOT_FOUND], userKey=user)
    except GAPI_userNotFound:
      print(' unknown user %s' % user)
      continue
    except GAPI_resourceNotFound:
      print(' no photo for %s' % user)
      continue
    try:
      photo_data = photo['photoData']
      if showPhotoData:
        print(photo_data)
    except KeyError:
      print(' no photo for %s' % user)
      continue
    decoded_photo_data = base64.urlsafe_b64decode(photo_data)
    writeFile(filename, decoded_photo_data, mode='wb', continueOnError=True)

def deletePhoto(users):
  cd = buildGAPIObject('directory')
  i = 0
  count = len(users)
  for user in users:
    i += 1
    print("Deleting photo for %s (%s/%s)" % (user, i, count))
    callGAPI(cd.users().photos(), 'delete', userKey=user)

def _showCalendar(userCalendar, j, jcount):
  print('  Calendar: {0} ({1}/{2})'.format(userCalendar['id'], j, jcount))
  print(utils.convertUTF8('    Summary: {0}'.format(userCalendar.get('summaryOverride', userCalendar['summary']))))
  print(utils.convertUTF8('    Description: {0}'.format(userCalendar.get('description', ''))))
  print('    Access Level: {0}'.format(userCalendar['accessRole']))
  print('    Timezone: {0}'.format(userCalendar['timeZone']))
  print(utils.convertUTF8('    Location: {0}'.format(userCalendar.get('location', ''))))
  print('    Hidden: {0}'.format(userCalendar.get('hidden', 'False')))
  print('    Selected: {0}'.format(userCalendar.get('selected', 'False')))
  print('    Color ID: {0}, Background Color: {1}, Foreground Color: {2}'.format(userCalendar['colorId'], userCalendar['backgroundColor'], userCalendar['foregroundColor']))
  print('    Default Reminders:')
  for reminder in userCalendar.get('defaultReminders', []):
    print('      Method: {0}, Minutes: {1}'.format(reminder['method'], reminder['minutes']))
  print('    Notifications:')
  if 'notificationSettings' in userCalendar:
    for notification in userCalendar['notificationSettings'].get('notifications', []):
      print('      Method: {0}, Type: {1}'.format(notification['method'], notification['type']))

def infoCalendar(users):
  calendarId = normalizeCalendarId(sys.argv[5], checkPrimary=True)
  i = 0
  count = len(users)
  for user in users:
    i += 1
    user, cal = buildCalendarGAPIObject(user)
    if not cal:
      continue
    result = callGAPI(cal.calendarList(), 'get',
                      soft_errors=True,
                      calendarId=calendarId)
    if result:
      print('User: {0}, Calendar: ({1}/{2})'.format(user, i, count))
      _showCalendar(result, 1, 1)

def printShowCalendars(users, csvFormat):
  if csvFormat:
    todrive = False
    titles = []
    csvRows = []
  i = 5
  while i < len(sys.argv):
    myarg = sys.argv[i].lower()
    if csvFormat and myarg == 'todrive':
      todrive = True
      i += 1
    else:
      systemErrorExit(2, '%s is not a valid argument for "gam <users> %s calendars"' %  (myarg, ['show', 'print'][csvFormat]))
  i = 0
  count = len(users)
  for user in users:
    i += 1
    user, cal = buildCalendarGAPIObject(user)
    if not cal:
      continue
    result = callGAPIpages(cal.calendarList(), 'list', 'items', soft_errors=True)
    jcount = len(result)
    if not csvFormat:
      print('User: {0}, Calendars: ({1}/{2})'.format(user, i, count))
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
        row = {'primaryEmail': user}
        addRowTitlesToCSVfile(flatten_json(userCalendar, flattened=row), csvRows, titles)
  if csvFormat:
    sortCSVTitles(['primaryEmail', 'id'], titles)
    writeCSVfile(csvRows, titles, 'Calendars', todrive)

def showCalSettings(users):
  i = 0
  count = len(users)
  for user in users:
    i += 1
    user, cal = buildCalendarGAPIObject(user)
    if not cal:
      continue
    feed = callGAPIpages(cal.settings(), 'list', 'items', soft_errors=True)
    if feed:
      print('User: {0}, Calendar Settings: ({1}/{2})'.format(user, i, count))
      settings = {}
      for setting in feed:
        settings[setting['id']] = setting['value']
      for attr, value in sorted(settings.items()):
        print('  {0}: {1}'.format(attr, value))

def printDriveSettings(users):
  todrive = False
  i = 5
  while i < len(sys.argv):
    myarg = sys.argv[i].lower()
    if myarg == 'todrive':
      todrive = True
      i += 1
    else:
      systemErrorExit(2, '%s is not a valid argument for "gam <users> show drivesettings"' % sys.argv[i])
  dont_show = ['kind', 'exportFormats', 'importFormats', 'maxUploadSize', 'maxImportSizes', 'user', 'appInstalled']
  csvRows = []
  titles = ['email',]
  i = 0
  count = len(users)
  for user in users:
    i += 1
    user, drive = buildDrive3GAPIObject(user)
    if not drive:
      continue
    sys.stderr.write('Getting Drive settings for %s (%s/%s)\n' % (user, i, count))
    feed = callGAPI(drive.about(), 'get', fields='*', soft_errors=True)
    if feed is None:
      continue
    row = {'email': user}
    for setting in feed:
      if setting in dont_show:
        continue
      if setting == 'storageQuota':
        for subsetting, value in feed[setting].items():
          row[subsetting] = '%smb' % (int(value) / 1024 / 1024)
          if subsetting not in titles:
            titles.append(subsetting)
        continue
      row[setting] = feed[setting]
      if setting not in titles:
        titles.append(setting)
    csvRows.append(row)
  writeCSVfile(csvRows, titles, 'User Drive Settings', todrive)

def getTeamDriveThemes(users):
  for user in users:
    user, drive = buildDrive3GAPIObject(user)
    if not drive:
      continue
    themes = callGAPI(drive.about(), 'get', fields='teamDriveThemes', soft_errors=True)
    if themes is None or 'teamDriveThemes' not in themes:
      continue
    print('theme')
    for theme in themes['teamDriveThemes']:
      print(theme['id'])

def printDriveActivity(users):
  drive_ancestorId = 'root'
  drive_fileId = None
  todrive = False
  titles = ['user.name', 'user.permissionId', 'target.id', 'target.name', 'target.mimeType']
  csvRows = []
  i = 5
  while i < len(sys.argv):
    activity_object = sys.argv[i].lower().replace('_', '')
    if activity_object == 'fileid':
      drive_fileId = sys.argv[i+1]
      drive_ancestorId = None
      i += 2
    elif activity_object == 'folderid':
      drive_ancestorId = sys.argv[i+1]
      i += 2
    elif activity_object == 'todrive':
      todrive = True
      i += 1
    else:
      systemErrorExit(2, '%s is not a valid argument for "gam <users> show driveactivity"' % sys.argv[i])
  for user in users:
    user, activity = buildActivityGAPIObject(user)
    if not activity:
      continue
    page_message = 'Got %%%%total_items%%%% activities for %s' % user
    feed = callGAPIpages(activity.activities(), 'list', 'activities',
                         page_message=page_message, source='drive.google.com', userId='me',
                         drive_ancestorId=drive_ancestorId, groupingStrategy='none',
                         drive_fileId=drive_fileId, pageSize=GC_Values[GC_ACTIVITY_MAX_RESULTS])
    for item in feed:
      addRowTitlesToCSVfile(flatten_json(item['combinedEvent']), csvRows, titles)
  writeCSVfile(csvRows, titles, 'Drive Activity', todrive)

def printPermission(permission):
  if 'name' in permission:
    print(utils.convertUTF8(permission['name']))
  elif 'id' in permission:
    if permission['id'] == 'anyone':
      print('Anyone')
    elif permission['id'] == 'anyoneWithLink':
      print('Anyone with Link')
    else:
      print(permission['id'])
  for key in permission:
    if key in ['name', 'kind', 'etag', 'selfLink',]:
      continue
    print(utils.convertUTF8(' %s: %s' % (key, permission[key])))

def showDriveFileACL(users):
  fileId = sys.argv[5]
  useDomainAdminAccess = False
  i = 6
  while i < len(sys.argv):
    myarg = sys.argv[i].lower().replace('_', '')
    if myarg == 'asadmin':
      useDomainAdminAccess = True
      i += 1
    else:
      systemErrorExit(3, '%s is not a valid argument to "gam <users> show drivefileacl".' % sys.argv[i])
  for user in users:
    user, drive = buildDrive3GAPIObject(user)
    if not drive:
      continue
    feed = callGAPIpages(drive.permissions(), 'list', 'permissions',
                         fileId=fileId, fields='*', supportsTeamDrives=True,
                         useDomainAdminAccess=useDomainAdminAccess)
    for permission in feed:
      printPermission(permission)
      print('')

def getPermissionId(argstr):
  permissionId = argstr.strip()
  cg = UID_PATTERN.match(permissionId)
  if cg:
    return cg.group(1)
  permissionId = argstr.lower()
  if permissionId == 'anyone':
    return 'anyone'
  if permissionId == 'anyonewithlink':
    return 'anyoneWithLink'
  if permissionId.find('@') == -1:
    permissionId = '%s@%s' % (permissionId, GC_Values[GC_DOMAIN].lower())
  # We have to use v2 here since v3 has no permissions.getIdForEmail equivalent
  # https://code.google.com/a/google.com/p/apps-api-issues/issues/detail?id=4313
  _, drive2 = buildDriveGAPIObject(_getValueFromOAuth('email'))
  return callGAPI(drive2.permissions(), 'getIdForEmail', email=permissionId, fields='id')['id']

def delDriveFileACL(users):
  fileId = sys.argv[5]
  permissionId = getPermissionId(sys.argv[6])
  useDomainAdminAccess = False
  i = 7
  while i < len(sys.argv):
    myarg = sys.argv[i].lower().replace('_', '')
    if myarg == 'asadmin':
      useDomainAdminAccess = True
      i += 1
    else:
      systemErrorExit(3, '%s is not a valid argument to "gam <users> delete drivefileacl".' % sys.argv[i])
  for user in users:
    user, drive = buildDrive3GAPIObject(user)
    if not drive:
      continue
    print('Removing permission for %s from %s' % (permissionId, fileId))
    callGAPI(drive.permissions(), 'delete', fileId=fileId,
             permissionId=permissionId, supportsTeamDrives=True,
             useDomainAdminAccess=useDomainAdminAccess)

DRIVEFILE_ACL_ROLES_MAP = {
  'commenter': 'commenter',
  'contentmanager': 'fileOrganizer',
  'editor': 'writer',
  'fileorganizer': 'fileOrganizer',
  'organizer': 'organizer',
  'owner': 'owner',
  'read': 'reader',
  'reader': 'reader',
  'writer': 'writer',
  }

def addDriveFileACL(users):
  fileId = sys.argv[5]
  body = {'type': sys.argv[6].lower()}
  sendNotificationEmail = False
  emailMessage = None
  transferOwnership = None
  useDomainAdminAccess = False
  if body['type'] == 'anyone':
    i = 7
  elif body['type'] in ['user', 'group']:
    body['emailAddress'] = normalizeEmailAddressOrUID(sys.argv[7])
    i = 8
  elif body['type'] == 'domain':
    body['domain'] = sys.argv[7]
    i = 8
  else:
    systemErrorExit(5, 'permission type must be user, group domain or anyone; got %s' % body['type'])
  while i < len(sys.argv):
    myarg = sys.argv[i].lower().replace('_', '')
    if myarg == 'withlink':
      body['allowFileDiscovery'] = False
      i += 1
    elif myarg == 'discoverable':
      body['allowFileDiscovery'] = True
      i += 1
    elif myarg == 'role':
      role = sys.argv[i+1].lower()
      if role not in DRIVEFILE_ACL_ROLES_MAP:
        systemErrorExit(2, 'role must be {0}; got {1}'.format(', '.join(DRIVEFILE_ACL_ROLES_MAP), role))
      body['role'] = DRIVEFILE_ACL_ROLES_MAP[role]
      if body['role'] == 'owner':
        sendNotificationEmail = True
        transferOwnership = True
      i += 2
    elif myarg == 'sendemail':
      sendNotificationEmail = True
      i += 1
    elif myarg == 'emailmessage':
      sendNotificationEmail = True
      emailMessage = sys.argv[i+1]
      i += 2
    elif myarg == 'expires':
      body['expirationTime'] = getTimeOrDeltaFromNow(sys.argv[i+1])
      i += 2
    elif myarg == 'asadmin':
      useDomainAdminAccess = True
      i += 1
    else:
      systemErrorExit(2, '%s is not a valid argument for "gam <users> add drivefileacl"' % sys.argv[i])
  for user in users:
    user, drive = buildDrive3GAPIObject(user)
    if not drive:
      continue
    result = callGAPI(drive.permissions(), 'create', fields='*',
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
    myarg = sys.argv[i].lower().replace('_', '')
    if myarg == 'removeexpiration':
      removeExpiration = True
      i += 1
    elif myarg == 'role':
      role = sys.argv[i+1].lower()
      if role not in DRIVEFILE_ACL_ROLES_MAP:
        systemErrorExit(2, 'role must be {0}; got {1}'.format(', '.join(DRIVEFILE_ACL_ROLES_MAP), role))
      body['role'] = DRIVEFILE_ACL_ROLES_MAP[role]
      if body['role'] == 'owner':
        transferOwnership = True
      i += 2
    elif myarg == 'asadmin':
      useDomainAdminAccess = True
      i += 1
    else:
      systemErrorExit(2, '%s is not a valid argument for "gam <users> update drivefileacl"' % sys.argv[i])
  for user in users:
    user, drive = buildDrive3GAPIObject(user)
    if not drive:
      continue
    print('updating permissions for %s to file %s' % (permissionId, fileId))
    result = callGAPI(drive.permissions(), 'update', fields='*',
                      fileId=fileId, permissionId=permissionId, removeExpiration=removeExpiration,
                      transferOwnership=transferOwnership, body=body,
                      supportsTeamDrives=True, useDomainAdminAccess=useDomainAdminAccess)
    printPermission(result)

def _stripMeInOwners(query):
  if not query:
    return query
  if query == "'me' in owners":
    return None
  if query.startswith("'me' in owners and "):
    return query[len("'me' in owners and "):]
  return query

def printDriveFileList(users):
  allfields = anyowner = todrive = False
  fieldsList = []
  fieldsTitles = {}
  labelsList = []
  orderByList = []
  titles = ['Owner',]
  csvRows = []
  query = "'me' in owners"
  i = 5
  while i < len(sys.argv):
    myarg = sys.argv[i].lower().replace('_', '')
    if myarg == 'todrive':
      todrive = True
      i += 1
    elif myarg == 'orderby':
      fieldName = sys.argv[i+1].lower()
      i += 2
      if fieldName in DRIVEFILE_ORDERBY_CHOICES_MAP:
        fieldName = DRIVEFILE_ORDERBY_CHOICES_MAP[fieldName]
        orderBy = ''
        if i < len(sys.argv):
          orderBy = sys.argv[i].lower()
          if orderBy in SORTORDER_CHOICES_MAP:
            orderBy = SORTORDER_CHOICES_MAP[orderBy]
            i += 1
        if orderBy != 'DESCENDING':
          orderByList.append(fieldName)
        else:
          orderByList.append('{0} desc'.format(fieldName))
      else:
        systemErrorExit(2, 'orderby must be one of {0}; got {1}'.format(', '.join(sorted(DRIVEFILE_ORDERBY_CHOICES_MAP.keys())), fieldName))
    elif myarg == 'query':
      query += ' and %s' % sys.argv[i+1]
      i += 2
    elif myarg == 'fullquery':
      query = sys.argv[i+1]
      i += 2
    elif myarg == 'anyowner':
      anyowner = True
      i += 1
    elif myarg == 'allfields':
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
    fields = 'nextPageToken,items('
    if fieldsList:
      fields += ','.join(set(fieldsList))
      if labelsList:
        fields += ','
    if labelsList:
      fields += 'labels({0})'.format(','.join(set(labelsList)))
    fields += ')'
  elif not allfields:
    for field in ['name', 'alternatelink']:
      addFieldToCSVfile(field, {field: [DRIVEFILE_FIELDS_CHOICES_MAP[field]]}, fieldsList, fieldsTitles, titles)
    fields = 'nextPageToken,items({0})'.format(','.join(set(fieldsList)))
  else:
    fields = '*'
  if orderByList:
    orderBy = ','.join(orderByList)
  else:
    orderBy = None
  if anyowner:
    query = _stripMeInOwners(query)
  for user in users:
    user, drive = buildDriveGAPIObject(user)
    if not drive:
      continue
    sys.stderr.write('Getting files for %s...\n' % user)
    page_message = ' Got %%%%total_items%%%% files for %s...\n' % user
    feed = callGAPIpages(drive.files(), 'list', 'items',
                         page_message=page_message, soft_errors=True,
                         q=query, orderBy=orderBy, fields=fields, maxResults=GC_Values[GC_DRIVE_MAX_RESULTS])
    for f_file in feed:
      a_file = {'Owner': user}
      for attrib in f_file:
        if attrib in ['kind', 'etag']:
          continue
        if not isinstance(f_file[attrib], dict):
          if isinstance(f_file[attrib], list):
            if f_file[attrib]:
              if isinstance(f_file[attrib][0], (str, int, bool)):
                if attrib not in titles:
                  titles.append(attrib)
                a_file[attrib] = ' '.join(f_file[attrib])
              else:
                for j, l_attrib in enumerate(f_file[attrib]):
                  for list_attrib in l_attrib:
                    if list_attrib in ['kind', 'etag', 'selfLink']:
                      continue
                    x_attrib = '{0}.{1}.{2}'.format(attrib, j, list_attrib)
                    if x_attrib not in titles:
                      titles.append(x_attrib)
                    a_file[x_attrib] = l_attrib[list_attrib]
          elif isinstance(f_file[attrib], (str, int, bool)):
            if attrib not in titles:
              titles.append(attrib)
            a_file[attrib] = f_file[attrib]
          else:
            sys.stderr.write('File ID: {0}, Attribute: {1}, Unknown type: {2}\n'.format(f_file['id'], attrib, type(f_file[attrib])))
        elif attrib == 'labels':
          for dict_attrib in f_file[attrib]:
            if dict_attrib not in titles:
              titles.append(dict_attrib)
            a_file[dict_attrib] = f_file[attrib][dict_attrib]
        else:
          for dict_attrib in f_file[attrib]:
            if dict_attrib in ['kind', 'etag']:
              continue
            x_attrib = '{0}.{1}'.format(attrib, dict_attrib)
            if x_attrib not in titles:
              titles.append(x_attrib)
            a_file[x_attrib] = f_file[attrib][dict_attrib]
      csvRows.append(a_file)
  if allfields:
    sortCSVTitles(['Owner', 'id', 'title'], titles)
  writeCSVfile(csvRows, titles, '%s %s Drive Files' % (sys.argv[1], sys.argv[2]), todrive)

def doDriveSearch(drive, query=None, quiet=False):
  if not quiet:
    print('Searching for files with query: "%s"...' % query)
    page_message = ' Got %%total_items%% files...\n'
  else:
    page_message = None
  files = callGAPIpages(drive.files(), 'list', 'items',
                        page_message=page_message,
                        q=query, fields='nextPageToken,items(id)', maxResults=GC_Values[GC_DRIVE_MAX_RESULTS])
  ids = list()
  for f_file in files:
    ids.append(f_file['id'])
  return ids

def getFileIdFromAlternateLink(altLink):
  loc = altLink.find('/d/')
  if loc > 0:
    fileId = altLink[loc+3:]
    loc = fileId.find('/')
    if loc != -1:
      return fileId[:loc]
  else:
    loc = altLink.find('/folderview?id=')
    if loc > 0:
      fileId = altLink[loc+15:]
      loc = fileId.find('&')
      if loc != -1:
        return fileId[:loc]
  systemErrorExit(2, '%s is not a valid Drive File alternateLink' % altLink)

def deleteDriveFile(users):
  fileIds = sys.argv[5]
  function = 'trash'
  i = 6
  while i < len(sys.argv):
    myarg = sys.argv[i].lower()
    if myarg == 'purge':
      function = 'delete'
      i += 1
    elif myarg == 'untrash':
      function = 'untrash'
      i += 1
    else:
      systemErrorExit(2, '%s is not a valid argument for "gam <users> delete drivefile"' % sys.argv[i])
  action = DELETE_DRIVEFILE_FUNCTION_TO_ACTION_MAP[function]
  for user in users:
    user, drive = buildDriveGAPIObject(user)
    if not drive:
      continue
    if fileIds[:6].lower() == 'query:':
      file_ids = doDriveSearch(drive, query=fileIds[6:])
    else:
      if fileIds[:8].lower() == 'https://' or fileIds[:7].lower() == 'http://':
        fileIds = getFileIdFromAlternateLink(fileIds)
      file_ids = [fileIds,]
    if not file_ids:
      print('No files to %s for %s' % (function, user))
    i = 0
    for fileId in file_ids:
      i += 1
      print('%s %s for %s (%s/%s)' % (action, fileId, user, i, len(file_ids)))
      callGAPI(drive.files(), function, fileId=fileId, supportsTeamDrives=True)

def printDriveFolderContents(feed, folderId, indent):
  for f_file in feed:
    for parent in f_file['parents']:
      if folderId == parent['id']:
        print(' ' * indent, utils.convertUTF8(f_file['title']))
        if f_file['mimeType'] == 'application/vnd.google-apps.folder':
          printDriveFolderContents(feed, f_file['id'], indent+1)
        break

def showDriveFileTree(users):
  anyowner = False
  orderByList = []
  query = "'me' in owners"
  i = 5
  while i < len(sys.argv):
    myarg = sys.argv[i].lower().replace('_', '')
    if myarg == 'anyowner':
      anyowner = True
      i += 1
    elif myarg == 'orderby':
      fieldName = sys.argv[i+1].lower()
      i += 2
      if fieldName in DRIVEFILE_ORDERBY_CHOICES_MAP:
        fieldName = DRIVEFILE_ORDERBY_CHOICES_MAP[fieldName]
        orderBy = ''
        if i < len(sys.argv):
          orderBy = sys.argv[i].lower()
          if orderBy in SORTORDER_CHOICES_MAP:
            orderBy = SORTORDER_CHOICES_MAP[orderBy]
            i += 1
        if orderBy != 'DESCENDING':
          orderByList.append(fieldName)
        else:
          orderByList.append('{0} desc'.format(fieldName))
      else:
        systemErrorExit(2, 'orderby must be one of {0}; got {1}'.format(', '.join(sorted(DRIVEFILE_ORDERBY_CHOICES_MAP.keys())), fieldName))
    else:
      systemErrorExit(2, '%s is not a valid argument for "gam <users> show filetree"' % myarg)
  if orderByList:
    orderBy = ','.join(orderByList)
  else:
    orderBy = None
  if anyowner:
    query = _stripMeInOwners(query)
  for user in users:
    user, drive = buildDriveGAPIObject(user)
    if not drive:
      continue
    root_folder = callGAPI(drive.about(), 'get', fields='rootFolderId')['rootFolderId']
    sys.stderr.write('Getting all files for %s...\n' % user)
    page_message = ' Got %%%%total_items%%%% files for %s...\n' % user
    feed = callGAPIpages(drive.files(), 'list', 'items', page_message=page_message,
                         q=query, orderBy=orderBy, fields='items(id,title,parents(id),mimeType),nextPageToken', maxResults=GC_Values[GC_DRIVE_MAX_RESULTS])
    printDriveFolderContents(feed, root_folder, 0)

def deleteEmptyDriveFolders(users):
  query = '"me" in owners and mimeType = "application/vnd.google-apps.folder"'
  for user in users:
    user, drive = buildDriveGAPIObject(user)
    if not drive:
      continue
    deleted_empty = True
    while deleted_empty:
      sys.stderr.write('Getting folders for %s...\n' % user)
      page_message = ' Got %%%%total_items%%%% folders for %s...\n' % user
      feed = callGAPIpages(drive.files(), 'list', 'items', page_message=page_message,
                           q=query, fields='items(title,id),nextPageToken', maxResults=GC_Values[GC_DRIVE_MAX_RESULTS])
      deleted_empty = False
      for folder in feed:
        children = callGAPI(drive.children(), 'list',
                            folderId=folder['id'], fields='items(id)', maxResults=1)
        if 'items' not in children or not children['items']:
          print(utils.convertUTF8(' deleting empty folder %s...' % folder['title']))
          callGAPI(drive.files(), 'delete', fileId=folder['id'])
          deleted_empty = True
        else:
          print(utils.convertUTF8(' not deleting folder %s because it contains at least 1 item (%s)' % (folder['title'], children['items'][0]['id'])))

def doEmptyDriveTrash(users):
  for user in users:
    user, drive = buildDrive3GAPIObject(user)
    if not drive:
      continue
    print('Emptying Drive trash for %s' % user)
    callGAPI(drive.files(), 'emptyTrash')

def escapeDriveFileName(filename):
  if filename.find("'") == -1 and filename.find('\\') == -1:
    return filename
  encfilename = ''
  for c in filename:
    if c == "'":
      encfilename += "\\'"
    elif c == '\\':
      encfilename += '\\\\'
    else:
      encfilename += c
  return encfilename

def initializeDriveFileAttributes():
  return ({}, {DFA_LOCALFILEPATH: None, DFA_LOCALFILENAME: None, DFA_LOCALMIMETYPE: None, DFA_CONVERT: None, DFA_OCR: None, DFA_OCRLANGUAGE: None, DFA_PARENTQUERY: None})

def getDriveFileAttribute(i, body, parameters, myarg, update=False):
  if myarg == 'localfile':
    parameters[DFA_LOCALFILEPATH] = sys.argv[i+1]
    parameters[DFA_LOCALFILENAME] = os.path.basename(parameters[DFA_LOCALFILEPATH])
    body.setdefault('title', parameters[DFA_LOCALFILENAME])
    body['mimeType'] = mimetypes.guess_type(parameters[DFA_LOCALFILEPATH])[0]
    if body['mimeType'] is None:
      body['mimeType'] = 'application/octet-stream'
    parameters[DFA_LOCALMIMETYPE] = body['mimeType']
    i += 2
  elif myarg == 'convert':
    parameters[DFA_CONVERT] = True
    i += 1
  elif myarg == 'ocr':
    parameters[DFA_OCR] = True
    i += 1
  elif myarg == 'ocrlanguage':
    parameters[DFA_OCRLANGUAGE] = LANGUAGE_CODES_MAP.get(sys.argv[i+1].lower(), sys.argv[i+1])
    i += 2
  elif myarg in DRIVEFILE_LABEL_CHOICES_MAP:
    body.setdefault('labels', {})
    if update:
      body['labels'][DRIVEFILE_LABEL_CHOICES_MAP[myarg]] = getBoolean(sys.argv[i+1], myarg)
      i += 2
    else:
      body['labels'][DRIVEFILE_LABEL_CHOICES_MAP[myarg]] = True
      i += 1
  elif myarg in ['lastviewedbyme', 'lastviewedbyuser', 'lastviewedbymedate', 'lastviewedbymetime']:
    body['lastViewedByMeDate'] = getTimeOrDeltaFromNow(sys.argv[i+1])
    i += 2
  elif myarg in ['modifieddate', 'modifiedtime']:
    body['modifiedDate'] = getTimeOrDeltaFromNow(sys.argv[i+1])
    i += 2
  elif myarg == 'description':
    body['description'] = sys.argv[i+1]
    i += 2
  elif myarg == 'mimetype':
    mimeType = sys.argv[i+1]
    if mimeType in MIMETYPE_CHOICES_MAP:
      body['mimeType'] = MIMETYPE_CHOICES_MAP[mimeType]
    else:
      systemErrorExit(2, 'mimetype must be one of %s; got %s"' % (', '.join(MIMETYPE_CHOICES_MAP), mimeType))
    i += 2
  elif myarg == 'parentid':
    body.setdefault('parents', [])
    body['parents'].append({'id': sys.argv[i+1]})
    i += 2
  elif myarg == 'parentname':
    parameters[DFA_PARENTQUERY] = "'me' in owners and mimeType = '%s' and title = '%s'" % (MIMETYPE_GA_FOLDER, escapeDriveFileName(sys.argv[i+1]))
    i += 2
  elif myarg in ['anyownerparentname']:
    parameters[DFA_PARENTQUERY] = "mimeType = '%s' and title = '%s'" % (MIMETYPE_GA_FOLDER, escapeDriveFileName(sys.argv[i+1]))
    i += 2
  elif myarg == 'writerscantshare':
    body['writersCanShare'] = False
    i += 1
  else:
    systemErrorExit(2, '%s is not a valid argument for "gam <users> %s drivefile"' % (myarg, ['add', 'update'][update]))
  return i

def doUpdateDriveFile(users):
  fileIdSelection = {'fileIds': [], 'query': None}
  media_body = None
  operation = 'update'
  body, parameters = initializeDriveFileAttributes()
  i = 5
  while i < len(sys.argv):
    myarg = sys.argv[i].lower().replace('_', '')
    if myarg == 'copy':
      operation = 'copy'
      i += 1
    elif myarg == 'newfilename':
      body['title'] = sys.argv[i+1]
      i += 2
    elif myarg == 'id':
      fileIdSelection['fileIds'] = [sys.argv[i+1],]
      i += 2
    elif myarg == 'query':
      fileIdSelection['query'] = sys.argv[i+1]
      i += 2
    elif myarg == 'drivefilename':
      fileIdSelection['query'] = "'me' in owners and title = '{0}'".format(sys.argv[i+1])
      i += 2
    else:
      i = getDriveFileAttribute(i, body, parameters, myarg, True)
  if not fileIdSelection['query'] and not fileIdSelection['fileIds']:
    systemErrorExit(2, 'you need to specify either id, query or drivefilename in order to determine the file(s) to update')
  if fileIdSelection['query'] and fileIdSelection['fileIds']:
    systemErrorExit(2, 'you cannot specify multiple file identifiers. Choose one of id, drivefilename, query.')
  for user in users:
    user, drive = buildDriveGAPIObject(user)
    if not drive:
      continue
    if parameters[DFA_PARENTQUERY]:
      more_parents = doDriveSearch(drive, query=parameters[DFA_PARENTQUERY])
      body.setdefault('parents', [])
      for a_parent in more_parents:
        body['parents'].append({'id': a_parent})
    if fileIdSelection['query']:
      fileIdSelection['fileIds'] = doDriveSearch(drive, query=fileIdSelection['query'])
    if not fileIdSelection['fileIds']:
      print('No files to %s for %s' % (operation, user))
      continue
    if operation == 'update':
      if parameters[DFA_LOCALFILEPATH]:
        media_body = googleapiclient.http.MediaFileUpload(parameters[DFA_LOCALFILEPATH], mimetype=parameters[DFA_LOCALMIMETYPE], resumable=True)
      for fileId in fileIdSelection['fileIds']:
        if media_body:
          result = callGAPI(drive.files(), 'update',
                            fileId=fileId, convert=parameters[DFA_CONVERT],
                            ocr=parameters[DFA_OCR],
                            ocrLanguage=parameters[DFA_OCRLANGUAGE],
                            media_body=media_body, body=body, fields='id',
                            supportsTeamDrives=True)
          print('Successfully updated %s drive file with content from %s' % (result['id'], parameters[DFA_LOCALFILENAME]))
        else:
          result = callGAPI(drive.files(), 'patch',
                            fileId=fileId, convert=parameters[DFA_CONVERT],
                            ocr=parameters[DFA_OCR],
                            ocrLanguage=parameters[DFA_OCRLANGUAGE], body=body,
                            fields='id', supportsTeamDrives=True)
          print('Successfully updated drive file/folder ID %s' % (result['id']))
    else:
      for fileId in fileIdSelection['fileIds']:
        result = callGAPI(drive.files(), 'copy',
                          fileId=fileId, convert=parameters[DFA_CONVERT],
                          ocr=parameters[DFA_OCR],
                          ocrLanguage=parameters[DFA_OCRLANGUAGE],
                          body=body, fields='id', supportsTeamDrives=True)
        print('Successfully copied %s to %s' % (fileId, result['id']))

def createDriveFile(users):
  csv_output = to_drive = False
  csv_rows = []
  csv_titles = ['User', 'title', 'id']
  media_body = None
  body, parameters = initializeDriveFileAttributes()
  i = 5
  while i < len(sys.argv):
    myarg = sys.argv[i].lower().replace('_', '')
    if myarg == 'drivefilename':
      body['title'] = sys.argv[i+1]
      i += 2
    elif myarg == 'csv':
      csv_output = True
      i += 1
    elif myarg == 'todrive':
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
      body.setdefault('parents', [])
      for a_parent in more_parents:
        body['parents'].append({'id': a_parent})
    if parameters[DFA_LOCALFILEPATH]:
      media_body = googleapiclient.http.MediaFileUpload(parameters[DFA_LOCALFILEPATH], mimetype=parameters[DFA_LOCALMIMETYPE], resumable=True)
    result = callGAPI(drive.files(), 'insert',
                      convert=parameters[DFA_CONVERT], ocr=parameters[DFA_OCR],
                      ocrLanguage=parameters[DFA_OCRLANGUAGE],
                      media_body=media_body, body=body, fields='id,title,mimeType',
                      supportsTeamDrives=True)
    titleInfo = '{0}({1})'.format(result['title'], result['id'])
    if csv_output:
      csv_rows.append({'User': user, 'title': result['title'], 'id': result['id']})
    else:
      if parameters[DFA_LOCALFILENAME]:
        print('Successfully uploaded %s to Drive File %s' % (parameters[DFA_LOCALFILENAME], titleInfo))
      else:
        print('Successfully created Drive %s %s' % (['Folder', 'File'][result['mimeType'] != MIMETYPE_GA_FOLDER], titleInfo))
  if csv_output:
    writeCSVfile(csv_rows, csv_titles, 'Files', to_drive)

HTTP_ERROR_PATTERN = re.compile(r'^.*returned "(.*)">$')

def downloadDriveFile(users):
  i = 5
  fileIdSelection = {'fileIds': [], 'query': None}
  csvSheetTitle = revisionId = None
  exportFormatName = 'openoffice'
  exportFormatChoices = [exportFormatName]
  exportFormats = DOCUMENT_FORMATS_MAP[exportFormatName]
  targetFolder = GC_Values[GC_DRIVE_DIR]
  targetName = None
  overwrite = showProgress = targetStdout = False
  safe_filename_chars = "-_.() %s%s" % (string.ascii_letters, string.digits)
  while i < len(sys.argv):
    myarg = sys.argv[i].lower().replace('_', '')
    if myarg == 'id':
      fileIdSelection['fileIds'] = [sys.argv[i+1],]
      i += 2
    elif myarg == 'query':
      fileIdSelection['query'] = sys.argv[i+1]
      i += 2
    elif myarg == 'drivefilename':
      fileIdSelection['query'] = "'me' in owners and title = '{0}'".format(sys.argv[i+1])
      i += 2
    elif myarg == 'revision':
      revisionId = getInteger(sys.argv[i+1], myarg, minVal=1)
      i += 2
    elif myarg == 'csvsheet':
      csvSheetTitle = sys.argv[i+1]
      csvSheetTitleLower = csvSheetTitle.lower()
      i += 2
    elif myarg == 'format':
      exportFormatChoices = sys.argv[i+1].replace(',', ' ').lower().split()
      exportFormats = []
      for exportFormat in exportFormatChoices:
        if exportFormat in DOCUMENT_FORMATS_MAP:
          exportFormats.extend(DOCUMENT_FORMATS_MAP[exportFormat])
        else:
          systemErrorExit(2, 'format must be one of {0}; got {1}'.format(', '.join(DOCUMENT_FORMATS_MAP), exportFormat))
      i += 2
    elif myarg == 'targetfolder':
      targetFolder = os.path.expanduser(sys.argv[i+1])
      if not os.path.isdir(targetFolder):
        os.makedirs(targetFolder)
      i += 2
    elif myarg == 'targetname':
      targetName = sys.argv[i+1]
      targetStdout = targetName == '-'
      i += 2
    elif myarg == 'overwrite':
      overwrite = True
      i += 1
    elif myarg == 'showprogress':
      showProgress = True
      i += 1
    else:
      systemErrorExit(2, '%s is not a valid argument for "gam <users> get drivefile"' % sys.argv[i])
  if not fileIdSelection['query'] and not fileIdSelection['fileIds']:
    systemErrorExit(2, 'you need to specify either id, query or drivefilename in order to determine the file(s) to download')
  if fileIdSelection['query'] and fileIdSelection['fileIds']:
    systemErrorExit(2, 'you cannot specify multiple file identifiers. Choose one of id, drivefilename, query.')
  if csvSheetTitle:
    exportFormatName = 'csv'
    exportFormatChoices = [exportFormatName]
    exportFormats = DOCUMENT_FORMATS_MAP[exportFormatName]
  for user in users:
    user, drive = buildDriveGAPIObject(user)
    if not drive:
      continue
    if csvSheetTitle:
      sheet = buildGAPIServiceObject('sheets', user)
      if not sheet:
        continue
    if fileIdSelection['query']:
      fileIdSelection['fileIds'] = doDriveSearch(drive, query=fileIdSelection['query'], quiet=targetStdout)
    else:
      fileId = fileIdSelection['fileIds'][0]
      if fileId[:8].lower() == 'https://' or fileId[:7].lower() == 'http://':
        fileIdSelection['fileIds'][0] = getFileIdFromAlternateLink(fileId)
    if not fileIdSelection['fileIds']:
      print('No files to download for %s' % user)
    i = 0
    for fileId in fileIdSelection['fileIds']:
      fileExtension = None
      result = callGAPI(drive.files(), 'get',
                        fileId=fileId, fields='fileExtension,fileSize,mimeType,title', supportsTeamDrives=True)
      fileExtension = result.get('fileExtension')
      mimeType = result['mimeType']
      if mimeType == MIMETYPE_GA_FOLDER:
        print(utils.convertUTF8('Skipping download of folder %s' % result['title']))
        continue
      if mimeType in NON_DOWNLOADABLE_MIMETYPES:
        print(utils.convertUTF8('Format of file %s not downloadable' % result['title']))
        continue
      validExtensions = GOOGLEDOC_VALID_EXTENSIONS_MAP.get(mimeType)
      if validExtensions:
        my_line = 'Downloading Google Doc: %s'
        if csvSheetTitle:
          my_line += ', Sheet: %s' % csvSheetTitle
        googleDoc = True
      else:
        if 'fileSize' in result:
          my_line = 'Downloading: %%s of %s bytes' % utils.formatFileSize(int(result['fileSize']))
        else:
          my_line = 'Downloading: %s of unknown size'
        googleDoc = False
      my_line += ' to %s'
      csvSheetNotFound = fileDownloaded = fileDownloadFailed = False
      for exportFormat in exportFormats:
        extension = fileExtension or exportFormat['ext']
        if googleDoc and (extension not in validExtensions):
          continue
        if targetStdout:
          filename = 'stdout'
        else:
          if targetName:
            safe_file_title = targetName
          else:
            safe_file_title = ''.join(c for c in result['title'] if c in safe_filename_chars)
            if not safe_file_title:
              safe_file_title = fileId
          filename = os.path.join(targetFolder, safe_file_title)
          y = 0
          while True:
            if filename.lower()[-len(extension):] != extension.lower():
              filename += extension
            if overwrite or not os.path.isfile(filename):
              break
            y += 1
            filename = os.path.join(targetFolder, '({0})-{1}'.format(y, safe_file_title))
          print(utils.convertUTF8(my_line % (result['title'], filename)))
        spreadsheetUrl = None
        if googleDoc:
          if csvSheetTitle is None or mimeType != MIMETYPE_GA_SPREADSHEET:
            request = drive.files().export_media(fileId=fileId, mimeType=exportFormat['mime'])
            if revisionId:
              request.uri = '{0}&revision={1}'.format(request.uri, revisionId)
          else:
            spreadsheet = callGAPI(sheet.spreadsheets(), 'get',
                                   spreadsheetId=fileId, fields='spreadsheetUrl,sheets(properties(sheetId,title))')
            for sheet in spreadsheet['sheets']:
              if sheet['properties']['title'].lower() == csvSheetTitleLower:
                spreadsheetUrl = '{0}?format=csv&id={1}&gid={2}'.format(re.sub('/edit$', '/export', spreadsheet['spreadsheetUrl']),
                                                                        fileId, sheet['properties']['sheetId'])
                break
            else:
              stderrErrorMsg('Google Doc: %s, Sheet: %s, does not exist' % (result['title'], csvSheetTitle))
              csvSheetNotFound = True
              continue
        else:
          request = drive.files().get_media(fileId=fileId, revisionId=revisionId)
        fh = None
        try:
          fh = open(filename, 'wb') if not targetStdout else sys.stdout
          if not spreadsheetUrl:
            downloader = googleapiclient.http.MediaIoBaseDownload(fh, request)
            done = False
            while not done:
              status, done = downloader.next_chunk()
              if showProgress:
                print('Downloaded: {0:>7.2%}'.format(status.progress()))
          else:
            _, content = drive._http.request(uri=spreadsheetUrl, method='GET')
            fh.write(content)
            if targetStdout and content[-1] != '\n':
              fh.write('\n')
          if not targetStdout:
            closeFile(fh)
          fileDownloaded = True
          break
        except (IOError, httplib2.HttpLib2Error) as e:
          stderrErrorMsg(str(e))
          GM_Globals[GM_SYSEXITRC] = 6
          fileDownloadFailed = True
          break
        except googleapiclient.http.HttpError as e:
          mg = HTTP_ERROR_PATTERN.match(str(e))
          if mg:
            stderrErrorMsg(mg.group(1))
          else:
            stderrErrorMsg(str(e))
          fileDownloadFailed = True
          break
        if fh and not targetStdout:
          closeFile(fh)
          os.remove(filename)
      if not fileDownloaded and not fileDownloadFailed and not csvSheetNotFound:
        stderrErrorMsg('Format ({0}) not available'.format(','.join(exportFormatChoices)))
        GM_Globals[GM_SYSEXITRC] = 51

def showDriveFileInfo(users):
  fieldsList = []
  labelsList = []
  fileId = sys.argv[5]
  i = 6
  while i < len(sys.argv):
    myarg = sys.argv[i].lower().replace('_', '')
    if myarg == 'allfields':
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
    fieldsList.append('title')
    fields = ','.join(set(fieldsList))
    if labelsList:
      fields += ',labels({0})'.format(','.join(set(labelsList)))
  else:
    fields = '*'
  for user in users:
    user, drive = buildDriveGAPIObject(user)
    if not drive:
      continue
    feed = callGAPI(drive.files(), 'get', fileId=fileId, fields=fields, supportsTeamDrives=True)
    if feed:
      print_json(None, feed)

def showDriveFileRevisions(users):
  fileId = sys.argv[5]
  for user in users:
    user, drive = buildDriveGAPIObject(user)
    if not drive:
      continue
    feed = callGAPI(drive.revisions(), 'list', fileId=fileId)
    if feed:
      print_json(None, feed)

def transferSecCals(users):
  target_user = sys.argv[5]
  remove_source_user = sendNotifications = True
  i = 6
  while i < len(sys.argv):
    myarg = sys.argv[i].lower().replace('_', '')
    if myarg == 'keepuser':
      remove_source_user = False
      i += 1
    elif myarg == 'sendnotifications':
      sendNotifications = getBoolean(sys.argv[i+1], myarg)
      i += 2
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
    calendars = callGAPIpages(source_cal.calendarList(), 'list', 'items', soft_errors=True,
                              minAccessRole='owner', showHidden=True, fields='items(id),nextPageToken')
    for calendar in calendars:
      calendarId = calendar['id']
      if calendarId.find('@group.calendar.google.com') != -1:
        callGAPI(source_cal.acl(), 'insert', calendarId=calendarId,
                 body={'role': 'owner', 'scope': {'type': 'user', 'value': target_user}}, sendNotifications=sendNotifications)
        if remove_source_user:
          callGAPI(target_cal.acl(), 'insert', calendarId=calendarId,
                   body={'role': 'none', 'scope': {'type': 'user', 'value': user}}, sendNotifications=sendNotifications)

def transferDriveFiles(users):
  target_user = sys.argv[5]
  remove_source_user = True
  i = 6
  while i < len(sys.argv):
    myarg = sys.argv[i].lower()
    if myarg == 'keepuser':
      remove_source_user = False
      i += 1
    else:
      systemErrorExit(2, '%s is not a valid argument for "gam <users> transfer drive"' % sys.argv[i])
  target_user, target_drive = buildDriveGAPIObject(target_user)
  if not target_drive:
    return
  target_about = callGAPI(target_drive.about(), 'get', fields='quotaType,quotaBytesTotal,quotaBytesUsed')
  if target_about['quotaType'] != 'UNLIMITED':
    target_drive_free = int(target_about['quotaBytesTotal']) - int(target_about['quotaBytesUsed'])
  else:
    target_drive_free = None
  for user in users:
    user, source_drive = buildDriveGAPIObject(user)
    if not source_drive:
      continue
    counter = 0
    source_about = callGAPI(source_drive.about(), 'get', fields='quotaBytesTotal,quotaBytesUsed,rootFolderId,permissionId')
    source_drive_size = int(source_about['quotaBytesUsed'])
    if target_drive_free is not None:
      if target_drive_free < source_drive_size:
        systemErrorExit(4, MESSAGE_NO_TRANSFER_LACK_OF_DISK_SPACE.format(source_drive_size / 1024 / 1024, target_drive_free / 1024 / 1024))
      print('Source drive size: %smb  Target drive free: %smb' % (source_drive_size / 1024 / 1024, target_drive_free / 1024 / 1024))
      target_drive_free = target_drive_free - source_drive_size # prep target_drive_free for next user
    else:
      print('Source drive size: %smb  Target drive free: UNLIMITED' % (source_drive_size / 1024 / 1024))
    source_root = source_about['rootFolderId']
    source_permissionid = source_about['permissionId']
    print("Getting file list for source user: %s..." % user)
    page_message = ' Got %%total_items%% files\n'
    source_drive_files = callGAPIpages(source_drive.files(), 'list', 'items', page_message=page_message,
                                       q="'me' in owners and trashed = false", fields='items(id,parents,mimeType),nextPageToken')
    all_source_file_ids = []
    for source_drive_file in source_drive_files:
      all_source_file_ids.append(source_drive_file['id'])
    total_count = len(source_drive_files)
    print("Getting folder list for target user: %s..." % target_user)
    page_message = ' Got %%total_items%% folders\n'
    target_folders = callGAPIpages(target_drive.files(), 'list', 'items', page_message=page_message,
                                   q="'me' in owners and mimeType = 'application/vnd.google-apps.folder'", fields='items(id,title),nextPageToken')
    got_top_folder = False
    all_target_folder_ids = []
    for target_folder in target_folders:
      all_target_folder_ids.append(target_folder['id'])
      if (not got_top_folder) and target_folder['title'] == '%s old files' % user:
        target_top_folder = target_folder['id']
        got_top_folder = True
    if not got_top_folder:
      create_folder = callGAPI(target_drive.files(), 'insert', body={'title': '%s old files' % user, 'mimeType': 'application/vnd.google-apps.folder'}, fields='id')
      target_top_folder = create_folder['id']
    transferred_files = []
    while True: # we loop thru, skipping files until all of their parents are done
      skipped_files = False
      for drive_file in source_drive_files:
        file_id = drive_file['id']
        if file_id in transferred_files:
          continue
        source_parents = drive_file['parents']
        skip_file_for_now = False
        for source_parent in source_parents:
          if source_parent['id'] not in all_source_file_ids and source_parent['id'] not in all_target_folder_ids:
            continue  # means this parent isn't owned by source or target, shouldn't matter
          if source_parent['id'] not in transferred_files and source_parent['id'] != source_root:
            #print u'skipping %s' % file_id
            skipped_files = skip_file_for_now = True
            break
        if skip_file_for_now:
          continue
        else:
          transferred_files.append(drive_file['id'])
        counter += 1
        print('Changing owner for file %s (%s/%s)' % (drive_file['id'], counter, total_count))
        body = {'role': 'owner', 'type': 'user', 'value': target_user}
        callGAPI(source_drive.permissions(), 'insert', soft_errors=True, fileId=file_id, sendNotificationEmails=False, body=body)
        target_parents = []
        for parent in source_parents:
          try:
            if parent['isRoot']:
              target_parents.append({'id': target_top_folder})
            else:
              target_parents.append({'id': parent['id']})
          except TypeError:
            pass
        if not target_parents:
          target_parents.append({'id': target_top_folder})
        callGAPI(target_drive.files(), 'patch', soft_errors=True, retry_reasons=['notFound'], fileId=file_id, body={'parents': target_parents})
        if remove_source_user:
          callGAPI(target_drive.permissions(), 'delete', soft_errors=True, fileId=file_id, permissionId=source_permissionid)
      if not skipped_files:
        break

def doImap(users):
  enable = getBoolean(sys.argv[4], 'gam <users> imap')
  body = {'enabled': enable, 'autoExpunge': True, 'expungeBehavior': 'archive', 'maxFolderSize': 0}
  i = 5
  while i < len(sys.argv):
    myarg = sys.argv[i].lower()
    if myarg == 'noautoexpunge':
      body['autoExpunge'] = False
      i += 1
    elif myarg == 'expungebehavior':
      opt = sys.argv[i+1].lower()
      if opt in EMAILSETTINGS_IMAP_EXPUNGE_BEHAVIOR_CHOICES_MAP:
        body['expungeBehavior'] = EMAILSETTINGS_IMAP_EXPUNGE_BEHAVIOR_CHOICES_MAP[opt]
        i += 2
      else:
        systemErrorExit(2, 'value for "gam <users> imap expungebehavior" must be one of %s; got %s' % (', '.join(EMAILSETTINGS_IMAP_EXPUNGE_BEHAVIOR_CHOICES_MAP), opt))
    elif myarg == 'maxfoldersize':
      opt = sys.argv[i+1].lower()
      if opt in EMAILSETTINGS_IMAP_MAX_FOLDER_SIZE_CHOICES:
        body['maxFolderSize'] = int(opt)
        i += 2
      else:
        systemErrorExit(2, 'value for "gam <users> imap maxfoldersize" must be one of %s; got %s' % ('|'.join(EMAILSETTINGS_IMAP_MAX_FOLDER_SIZE_CHOICES), opt))
    else:
      systemErrorExit(2, '%s is not a valid argument for "gam <users> imap"' % myarg)
  i = 0
  count = len(users)
  for user in users:
    i += 1
    user, gmail = buildGmailGAPIObject(user)
    if not gmail:
      continue
    print("Setting IMAP Access to %s for %s (%s/%s)" % (str(enable), user, i, count))
    callGAPI(gmail.users().settings(), 'updateImap',
             soft_errors=True,
             userId='me', body=body)

def getImap(users):
  i = 0
  count = len(users)
  for user in users:
    i += 1
    user, gmail = buildGmailGAPIObject(user)
    if not gmail:
      continue
    result = callGAPI(gmail.users().settings(), 'getImap',
                      soft_errors=True,
                      userId='me')
    if result:
      enabled = result['enabled']
      if enabled:
        print('User: {0}, IMAP Enabled: {1}, autoExpunge: {2}, expungeBehavior: {3}, maxFolderSize:{4} ({5}/{6})'.format(user, enabled, result['autoExpunge'], result['expungeBehavior'], result['maxFolderSize'], i, count))
      else:
        print('User: {0}, IMAP Enabled: {1} ({2}/{3})'.format(user, enabled, i, count))

def getProductAndSKU(sku):
  l_sku = sku.lower().replace('-', '').replace(' ', '')
  for a_sku, sku_values in list(SKUS.items()):
    if l_sku == a_sku.lower().replace('-', '') or l_sku in sku_values['aliases'] or l_sku == sku_values['displayName'].lower().replace(' ', ''):
      return (sku_values['product'], a_sku)
  try:
    product = re.search('^([A-Z,a-z]*-[A-Z,a-z]*)', sku).group(1)
  except AttributeError:
    product = sku
  return (product, sku)

def doLicense(users, operation):
  lic = buildGAPIObject('licensing')
  sku = sys.argv[5]
  productId, skuId = getProductAndSKU(sku)
  i = 6
  if len(sys.argv) > 6 and sys.argv[i].lower() in ['product', 'productid']:
    productId = sys.argv[i+1]
    i += 2
  for user in users:
    if operation == 'delete':
      print('Removing license %s from user %s' % (_formatSKUIdDisplayName(skuId), user))
      callGAPI(lic.licenseAssignments(), operation, soft_errors=True, productId=productId, skuId=skuId, userId=user)
    elif operation == 'insert':
      print('Adding license %s to user %s' % (_formatSKUIdDisplayName(skuId), user))
      callGAPI(lic.licenseAssignments(), operation, soft_errors=True, productId=productId, skuId=skuId, body={'userId': user})
    elif operation == 'patch':
      try:
        old_sku = sys.argv[i]
        if old_sku.lower() == 'from':
          old_sku = sys.argv[i+1]
      except KeyError:
        systemErrorExit(2, 'You need to specify the user\'s old SKU as the last argument')
      _, old_sku = getProductAndSKU(old_sku)
      print('Changing user %s from license %s to %s' % (user, _formatSKUIdDisplayName(old_sku), _formatSKUIdDisplayName(skuId)))
      callGAPI(lic.licenseAssignments(), operation, soft_errors=True, productId=productId, skuId=old_sku, userId=user, body={'skuId': skuId})

def doPop(users):
  enable = getBoolean(sys.argv[4], 'gam <users> pop')
  body = {'accessWindow': ['disabled', 'allMail'][enable], 'disposition': 'leaveInInbox'}
  i = 5
  while i < len(sys.argv):
    myarg = sys.argv[i].lower()
    if myarg == 'for':
      opt = sys.argv[i+1].lower()
      if opt in EMAILSETTINGS_POP_ENABLE_FOR_CHOICES_MAP:
        body['accessWindow'] = EMAILSETTINGS_POP_ENABLE_FOR_CHOICES_MAP[opt]
        i += 2
      else:
        systemErrorExit(2, 'value for "gam <users> pop for" must be one of %s; got %s' % (', '.join(EMAILSETTINGS_POP_ENABLE_FOR_CHOICES_MAP), opt))
    elif myarg == 'action':
      opt = sys.argv[i+1].lower()
      if opt in EMAILSETTINGS_FORWARD_POP_ACTION_CHOICES_MAP:
        body['disposition'] = EMAILSETTINGS_FORWARD_POP_ACTION_CHOICES_MAP[opt]
        i += 2
      else:
        systemErrorExit(2, 'value for "gam <users> pop action" must be one of %s; got %s' % (', '.join(EMAILSETTINGS_FORWARD_POP_ACTION_CHOICES_MAP), opt))
    elif myarg == 'confirm':
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
    print("Setting POP Access to %s for %s (%s/%s)" % (str(enable), user, i, count))
    callGAPI(gmail.users().settings(), 'updatePop',
             soft_errors=True,
             userId='me', body=body)

def getPop(users):
  i = 0
  count = len(users)
  for user in users:
    i += 1
    user, gmail = buildGmailGAPIObject(user)
    if not gmail:
      continue
    result = callGAPI(gmail.users().settings(), 'getPop',
                      soft_errors=True,
                      userId='me')
    if result:
      enabled = result['accessWindow'] != 'disabled'
      if enabled:
        print('User: {0}, POP Enabled: {1}, For: {2}, Action: {3} ({4}/{5})'.format(user, enabled, result['accessWindow'], result['disposition'], i, count))
      else:
        print('User: {0}, POP Enabled: {1} ({2}/{3})'.format(user, enabled, i, count))

SMTPMSA_DISPLAY_FIELDS = ['host', 'port', 'securityMode']

def _showSendAs(result, j, jcount, formatSig):
  if result['displayName']:
    print(utils.convertUTF8('SendAs Address: {0} <{1}>{2}'.format(result['displayName'], result['sendAsEmail'], currentCount(j, jcount))))
  else:
    print(utils.convertUTF8('SendAs Address: <{0}>{1}'.format(result['sendAsEmail'], currentCount(j, jcount))))
  if result.get('replyToAddress'):
    print('  ReplyTo: {0}'.format(result['replyToAddress']))
  print('  IsPrimary: {0}'.format(result.get('isPrimary', False)))
  print('  Default: {0}'.format(result.get('isDefault', False)))
  if not result.get('isPrimary', False):
    print('  TreatAsAlias: {0}'.format(result.get('treatAsAlias', False)))
  if 'smtpMsa' in result:
    for field in SMTPMSA_DISPLAY_FIELDS:
      if field in result['smtpMsa']:
        print('  smtpMsa.{0}: {1}'.format(field, result['smtpMsa'][field]))
  if 'verificationStatus' in result:
    print('  Verification Status: {0}'.format(result['verificationStatus']))
  sys.stdout.write('  Signature:\n    ')
  signature = result.get('signature')
  if not signature:
    signature = 'None'
  if formatSig:
    print(utils.convertUTF8(utils.indentMultiLineText(utils.dehtml(signature), n=4)))
  else:
    print(utils.convertUTF8(utils.indentMultiLineText(signature, n=4)))

def _processTags(tagReplacements, message):
  while True:
    match = RT_PATTERN.search(message)
    if not match:
      break
    if tagReplacements.get(match.group(1)):
      message = RT_OPEN_PATTERN.sub('', message, count=1)
      message = RT_CLOSE_PATTERN.sub('', message, count=1)
    else:
      message = RT_STRIP_PATTERN.sub('', message, count=1)
  while True:
    match = RT_TAG_REPLACE_PATTERN.search(message)
    if not match:
      break
    message = re.sub(match.group(0), tagReplacements.get(match.group(1), ''), message)
  return message

def _processSignature(tagReplacements, signature, html):
  if signature:
    signature = signature.replace('\r', '').replace('\\n', '<br/>')
    if tagReplacements:
      signature = _processTags(tagReplacements, signature)
    if not html:
      signature = signature.replace('\n', '<br/>')
  return signature

def getSendAsAttributes(i, myarg, body, tagReplacements, command):
  if myarg == 'replace':
    matchTag = getString(i+1, 'Tag')
    matchReplacement = getString(i+2, 'String', minLen=0)
    tagReplacements[matchTag] = matchReplacement
    i += 3
  elif myarg == 'name':
    body['displayName'] = sys.argv[i+1]
    i += 2
  elif myarg == 'replyto':
    body['replyToAddress'] = sys.argv[i+1]
    i += 2
  elif myarg == 'default':
    body['isDefault'] = True
    i += 1
  elif myarg == 'treatasalias':
    body['treatAsAlias'] = getBoolean(sys.argv[i+1], myarg)
    i += 2
  else:
    systemErrorExit(2, '%s is not a valid argument for "gam <users> %s"' % (sys.argv[i], command))
  return i

SMTPMSA_PORTS = ['25', '465', '587']
SMTPMSA_SECURITY_MODES = ['none', 'ssl', 'starttls']
SMTPMSA_REQUIRED_FIELDS = ['host', 'port', 'username', 'password']

def addUpdateSendAs(users, i, addCmd):
  emailAddress = normalizeEmailAddressOrUID(sys.argv[i], noUid=True)
  i += 1
  if addCmd:
    command = ['sendas', 'add sendas'][i == 6]
    body = {'sendAsEmail': emailAddress, 'displayName': sys.argv[i]}
    i += 1
  else:
    command = 'update sendas'
    body = {}
  signature = None
  smtpMsa = {}
  tagReplacements = {}
  html = False
  while i < len(sys.argv):
    myarg = sys.argv[i].lower()
    if myarg in ['signature', 'sig']:
      signature = sys.argv[i+1]
      i += 2
      if signature.lower() == 'file':
        filename = sys.argv[i]
        i, encoding = getCharSet(i+1)
        signature = readFile(filename, encoding=encoding)
    elif myarg == 'html':
      html = True
      i += 1
    elif addCmd and myarg.startswith('smtpmsa.'):
      if myarg == 'smtpmsa.host':
        smtpMsa['host'] = sys.argv[i+1]
        i += 2
      elif myarg == 'smtpmsa.port':
        value = sys.argv[i+1].lower()
        if value not in SMTPMSA_PORTS:
          systemErrorExit(2, '{0} must be {1}; got {2}'.format(myarg, ', '.join(SMTPMSA_PORTS), value))
        smtpMsa['port'] = int(value)
        i += 2
      elif myarg == 'smtpmsa.username':
        smtpMsa['username'] = sys.argv[i+1]
        i += 2
      elif myarg == 'smtpmsa.password':
        smtpMsa['password'] = sys.argv[i+1]
        i += 2
      elif myarg == 'smtpmsa.securitymode':
        value = sys.argv[i+1].lower()
        if value not in SMTPMSA_SECURITY_MODES:
          systemErrorExit(2, '{0} must be {1}; got {2}'.format(myarg, ', '.join(SMTPMSA_SECURITY_MODES), value))
        smtpMsa['securityMode'] = value
        i += 2
      else:
        systemErrorExit(2, '%s is not a valid argument for "gam <users> %s"' % (sys.argv[i], command))
    else:
      i = getSendAsAttributes(i, myarg, body, tagReplacements, command)
  if signature is not None:
    body['signature'] = _processSignature(tagReplacements, signature, html)
  if smtpMsa:
    for field in SMTPMSA_REQUIRED_FIELDS:
      if field not in smtpMsa:
        systemErrorExit(2, 'smtpmsa.{0} is required.'.format(field))
    body['smtpMsa'] = smtpMsa
  kwargs = {'body': body}
  if not addCmd:
    kwargs['sendAsEmail'] = emailAddress
  i = 0
  count = len(users)
  for user in users:
    i += 1
    user, gmail = buildGmailGAPIObject(user)
    if not gmail:
      continue
    print("Allowing %s to send as %s (%s/%s)" % (user, emailAddress, i, count))
    callGAPI(gmail.users().settings().sendAs(), ['patch', 'create'][addCmd],
             soft_errors=True,
             userId='me', **kwargs)

def deleteSendAs(users):
  emailAddress = normalizeEmailAddressOrUID(sys.argv[5], noUid=True)
  i = 0
  count = len(users)
  for user in users:
    i += 1
    user, gmail = buildGmailGAPIObject(user)
    if not gmail:
      continue
    print("Disallowing %s to send as %s (%s/%s)" % (user, emailAddress, i, count))
    callGAPI(gmail.users().settings().sendAs(), 'delete',
             soft_errors=True,
             userId='me', sendAsEmail=emailAddress)

def updateSmime(users):
  smimeIdBase = None
  sendAsEmailBase = None
  make_default = False
  i = 5
  while i < len(sys.argv):
    myarg = sys.argv[i].lower()
    if myarg == 'id':
      smimeIdBase = sys.argv[i+1]
      i += 2
    elif myarg in ['sendas', 'sendasemail']:
      sendAsEmailBase = sys.argv[i+1]
      i += 2
    elif myarg in ['default']:
      make_default = True
      i += 1
    else:
      systemErrorExit(3, '%s is not a valid argument to "gam <users> update smime"' % myarg)
  if not make_default:
    print('Nothing to update for smime.')
    sys.exit(0)
  for user in users:
    user, gmail = buildGmailGAPIObject(user)
    if not gmail:
      continue
    sendAsEmail = sendAsEmailBase if sendAsEmailBase else user
    if not smimeIdBase:
      result = callGAPI(gmail.users().settings().sendAs().smimeInfo(), 'list', userId='me', sendAsEmail=sendAsEmail, fields='smimeInfo(id)')
      smimes = result.get('smimeInfo', [])
      if not smimes:
        systemErrorExit(3, '%s has no S/MIME certificates for sendas address %s' % (user, sendAsEmail))
      if len(smimes) > 1:
        systemErrorExit(3, '%s has more than one S/MIME certificate. Please specify a cert to update:\n %s' % (user, '\n '.join([smime['id'] for smime in smimes])))
      smimeId = smimes[0]['id']
    else:
      smimeId = smimeIdBase
    print('Setting smime id %s as default for user %s and sendas %s' % (smimeId, user, sendAsEmail))
    callGAPI(gmail.users().settings().sendAs().smimeInfo(), 'setDefault', userId='me', sendAsEmail=sendAsEmail, id=smimeId)

def deleteSmime(users):
  smimeIdBase = None
  sendAsEmailBase = None
  i = 5
  while i < len(sys.argv):
    myarg = sys.argv[i].lower()
    if myarg == 'id':
      smimeIdBase = sys.argv[i+1]
      i += 2
    elif myarg in ['sendas', 'sendasemail']:
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
      result = callGAPI(gmail.users().settings().sendAs().smimeInfo(), 'list', userId='me', sendAsEmail=sendAsEmail, fields='smimeInfo(id)')
      smimes = result.get('smimeInfo', [])
      if not smimes:
        systemErrorExit(3, '%s has no S/MIME certificates for sendas address %s' % (user, sendAsEmail))
      if len(smimes) > 1:
        systemErrorExit(3, '%s has more than one S/MIME certificate. Please specify a cert to delete:\n %s' % (user, '\n '.join([smime['id'] for smime in smimes])))
      smimeId = smimes[0]['id']
    else:
      smimeId = smimeIdBase
    print('Deleting smime id %s for user %s and sendas %s' % (smimeId, user, sendAsEmail))
    callGAPI(gmail.users().settings().sendAs().smimeInfo(), 'delete', userId='me', sendAsEmail=sendAsEmail, id=smimeId)

def printShowSmime(users, csvFormat):
  if csvFormat:
    todrive = False
    titles = ['User']
    csvRows = []
  primaryonly = False
  i = 5
  while i < len(sys.argv):
    myarg = sys.argv[i].lower()
    if csvFormat and myarg == 'todrive':
      todrive = True
      i += 1
    elif myarg == 'primaryonly':
      primaryonly = True
      i += 1
    else:
      systemErrorExit(3, '%s is not a valid argument for "gam <users> %s smime"' % (myarg, ['show', 'print'][csvFormat]))
  i = 0
  for user in users:
    i += 1
    user, gmail = buildGmailGAPIObject(user)
    if not gmail:
      continue
    if primaryonly:
      sendAsEmails = [user]
    else:
      result = callGAPI(gmail.users().settings().sendAs(), 'list', userId='me', fields='sendAs(sendAsEmail)')
      sendAsEmails = []
      for sendAs in result['sendAs']:
        sendAsEmails.append(sendAs['sendAsEmail'])
    for sendAsEmail in sendAsEmails:
      result = callGAPI(gmail.users().settings().sendAs().smimeInfo(), 'list', sendAsEmail=sendAsEmail, userId='me')
      smimes = result.get('smimeInfo', [])
      for j, _ in enumerate(smimes):
        smimes[j]['expiration'] = datetime.datetime.fromtimestamp(int(smimes[j]['expiration'])/1000).strftime('%Y-%m-%d %H:%M:%S')
      if csvFormat:
        for smime in smimes:
          addRowTitlesToCSVfile(flatten_json(smime, flattened={'User': user}), csvRows, titles)
      else:
        print_json(None, smimes)
  if csvFormat:
    writeCSVfile(csvRows, titles, 'S/MIME', todrive)

def printShowSendAs(users, csvFormat):
  if csvFormat:
    todrive = False
    titles = ['User', 'displayName', 'sendAsEmail', 'replyToAddress', 'isPrimary', 'isDefault', 'treatAsAlias', 'verificationStatus']
    csvRows = []
  formatSig = False
  i = 5
  while i < len(sys.argv):
    myarg = sys.argv[i].lower()
    if csvFormat and myarg == 'todrive':
      todrive = True
      i += 1
    elif not csvFormat and myarg == 'format':
      formatSig = True
      i += 1
    else:
      systemErrorExit(2, '%s is not a valid argument for "gam <users> %s sendas"' %  (myarg, ['show', 'print'][csvFormat]))
  i = 0
  count = len(users)
  for user in users:
    i += 1
    user, gmail = buildGmailGAPIObject(user)
    if not gmail:
      continue
    result = callGAPI(gmail.users().settings().sendAs(), 'list',
                      soft_errors=True,
                      userId='me')
    jcount = len(result.get('sendAs', [])) if (result) else 0
    if not csvFormat:
      print('User: {0}, SendAs Addresses: ({1}/{2})'.format(user, i, count))
      if jcount == 0:
        continue
      j = 0
      for sendas in result['sendAs']:
        j += 1
        _showSendAs(sendas, j, jcount, formatSig)
    else:
      if jcount == 0:
        continue
      for sendas in result['sendAs']:
        row = {'User': user, 'isPrimary': False}
        for item in sendas:
          if item != 'smtpMsa':
            if item not in titles:
              titles.append(item)
            row[item] = sendas[item]
          else:
            for field in SMTPMSA_DISPLAY_FIELDS:
              if field in sendas[item]:
                title = 'smtpMsa.{0}'.format(field)
                if title not in titles:
                  titles.append(title)
                row[title] = sendas[item][field]
        csvRows.append(row)
  if csvFormat:
    writeCSVfile(csvRows, titles, 'SendAs', todrive)

def infoSendAs(users):
  emailAddress = normalizeEmailAddressOrUID(sys.argv[5], noUid=True)
  formatSig = False
  i = 6
  while i < len(sys.argv):
    myarg = sys.argv[i].lower()
    if myarg == 'format':
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
    print('User: {0}, Show SendAs Address:{1}'.format(user, currentCount(i, count)))
    result = callGAPI(gmail.users().settings().sendAs(), 'get',
                      soft_errors=True,
                      userId='me', sendAsEmail=emailAddress)
    if result:
      _showSendAs(result, i, count, formatSig)

def addSmime(users):
  sendAsEmailBase = None
  setDefault = False
  body = {}
  i = 5
  while i < len(sys.argv):
    myarg = sys.argv[i].lower()
    if myarg == 'file':
      smimefile = sys.argv[i+1]
      body['pkcs12'] = base64.urlsafe_b64encode(readFile(smimefile, mode='rb'))
      i += 2
    elif myarg == 'password':
      body['encryptedKeyPassword'] = sys.argv[i+1]
      i += 2
    elif myarg == 'default':
      setDefault = True
      i += 1
    elif myarg in ['sendas', 'sendasemail']:
      sendAsEmailBase = sys.argv[i+1]
      i += 2
    else:
      systemErrorExit(3, '%s is not a valid argument for "gam <users> add smime"' % myarg)
  if 'pkcs12' not in body:
    systemErrorExit(3, 'you must specify a file to upload')
  i = 0
  for user in users:
    i += 1
    user, gmail = buildGmailGAPIObject(user)
    if not gmail:
      continue
    sendAsEmail = sendAsEmailBase if sendAsEmailBase else user
    result = callGAPI(gmail.users().settings().sendAs().smimeInfo(), 'insert', userId='me', sendAsEmail=sendAsEmail, body=body)
    if setDefault:
      callGAPI(gmail.users().settings().sendAs().smimeInfo(), 'setDefault', userId='me', sendAsEmail=sendAsEmail, id=result['id'])
    print('Added S/MIME certificate for user %s sendas %s issued by %s' % (user, sendAsEmail, result['issuerCn']))

def getLabelAttributes(i, myarg, body):
  if myarg == 'labellistvisibility':
    value = sys.argv[i+1].lower().replace('_', '')
    if value == 'hide':
      body['labelListVisibility'] = 'labelHide'
    elif value == 'show':
      body['labelListVisibility'] = 'labelShow'
    elif value == 'showifunread':
      body['labelListVisibility'] = 'labelShowIfUnread'
    else:
      systemErrorExit(2, 'label_list_visibility must be one of hide, show, show_if_unread; got %s' % value)
    i += 2
  elif myarg == 'messagelistvisibility':
    value = sys.argv[i+1].lower().replace('_', '')
    if value not in ['hide', 'show']:
      systemErrorExit(2, 'message_list_visibility must be show or hide; got %s' % value)
    body['messageListVisibility'] = value
    i += 2
  elif myarg == 'backgroundcolor':
    body.setdefault('color', {})
    body['color']['backgroundColor'] = getLabelColor(sys.argv[i+1])
    i += 2
  elif myarg == 'textcolor':
    body.setdefault('color', {})
    body['color']['textColor'] = getLabelColor(sys.argv[i+1])
    i += 2
  else:
    systemErrorExit(2, '%s is not a valid argument for this command.' % myarg)
  return i

def checkLabelColor(body):
  if 'color' not in body:
    return
  if 'backgroundColor' in body['color']:
    if 'textColor' in body['color']:
      return
    systemErrorExit(2, 'textcolor <LabelColorHex> is required.')
  systemErrorExit(2, 'backgroundcolor <LabelColorHex> is required.')

def doLabel(users, i):
  label = sys.argv[i]
  i += 1
  body = {'name': label}
  while i < len(sys.argv):
    myarg = sys.argv[i].lower().replace('_', '')
    i = getLabelAttributes(i, myarg, body)
  checkLabelColor(body)
  i = 0
  count = len(users)
  for user in users:
    i += 1
    user, gmail = buildGmailGAPIObject(user)
    if not gmail:
      continue
    print("Creating label %s for %s (%s/%s)" % (label, user, i, count))
    callGAPI(gmail.users().labels(), 'create', soft_errors=True, userId=user, body=body)

PROCESS_MESSAGE_FUNCTION_TO_ACTION_MAP = {'delete': 'deleted', 'trash': 'trashed', 'untrash': 'untrashed', 'modify': 'modified'}

def labelsToLabelIds(gmail, labels):
  allLabels = {
    'INBOX': 'INBOX', 'SPAM': 'SPAM', 'TRASH': 'TRASH',
    'UNREAD': 'UNREAD', 'STARRED': 'STARRED', 'IMPORTANT': 'IMPORTANT',
    'SENT': 'SENT', 'DRAFT': 'DRAFT',
    'CATEGORY_PERSONAL': 'CATEGORY_PERSONAL',
    'CATEGORY_SOCIAL': 'CATEGORY_SOCIAL',
    'CATEGORY_PROMOTIONS': 'CATEGORY_PROMOTIONS',
    'CATEGORY_UPDATES': 'CATEGORY_UPDATES',
    'CATEGORY_FORUMS': 'CATEGORY_FORUMS',
    }
  labelIds = list()
  for label in labels:
    if label not in allLabels:
      # first refresh labels in user mailbox
      label_results = callGAPI(gmail.users().labels(), 'list',
                               userId='me', fields='labels(id,name,type)')
      for a_label in label_results['labels']:
        if a_label['type'] == 'system':
          allLabels[a_label['id']] = a_label['id']
        else:
          allLabels[a_label['name']] = a_label['id']
    if label not in allLabels:
      # if still not there, create it
      label_results = callGAPI(gmail.users().labels(), 'create',
                               body={'labelListVisibility': 'labelShow',
                                     'messageListVisibility': 'show', 'name': label},
                               userId='me', fields='id')
      allLabels[label] = label_results['id']
    try:
      labelIds.append(allLabels[label])
    except KeyError:
      pass
    if label.find('/') != -1:
      # make sure to create parent labels for proper nesting
      parent_label = label[:label.rfind('/')]
      while True:
        if not parent_label in allLabels:
          label_result = callGAPI(gmail.users().labels(), 'create',
                                  userId='me', body={'name': parent_label})
          allLabels[parent_label] = label_result['id']
        if parent_label.find('/') == -1:
          break
        parent_label = parent_label[:parent_label.rfind('/')]
  return labelIds

def doProcessMessagesOrThreads(users, function, unit='messages'):
  query = None
  doIt = False
  maxToProcess = 1
  body = {}
  i = 5
  while i < len(sys.argv):
    myarg = sys.argv[i].lower().replace('_', '')
    if myarg == 'query':
      query = sys.argv[i+1]
      i += 2
    elif myarg == 'doit':
      doIt = True
      i += 1
    elif myarg in ['maxtodelete', 'maxtotrash', 'maxtomodify', 'maxtountrash']:
      maxToProcess = getInteger(sys.argv[i+1], myarg, minVal=0)
      i += 2
    elif (function == 'modify') and (myarg == 'addlabel'):
      body.setdefault('addLabelIds', [])
      body['addLabelIds'].append(sys.argv[i+1])
      i += 2
    elif (function == 'modify') and (myarg == 'removelabel'):
      body.setdefault('removeLabelIds', [])
      body['removeLabelIds'].append(sys.argv[i+1])
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
    print('Searching %s for %s' % (unit, user))
    unitmethod = getattr(gmail.users(), unit)
    page_message = 'Got %%%%total_items%%%% %s for user %s' % (unit, user)
    listResult = callGAPIpages(unitmethod(), 'list', unit, page_message=page_message,
                               userId='me', q=query, includeSpamTrash=True, soft_errors=True, fields='nextPageToken,{0}(id)'.format(unit))
    result_count = len(listResult)
    if not doIt or result_count == 0:
      print('would try to %s %s messages for user %s (max %s)\n' % (function, result_count, user, maxToProcess))
      continue
    elif result_count > maxToProcess:
      print('WARNING: refusing to %s ANY messages for %s since max messages to process is %s and messages to be %s is %s\n' % (function, user, maxToProcess, action, result_count))
      continue
    kwargs = {'body': {}}
    for my_key in body:
      kwargs['body'][my_key] = labelsToLabelIds(gmail, body[my_key])
    i = 0
    if unit == 'messages' and function in ['delete', 'modify']:
      batchFunction = 'batch%s' % function.title()
      id_batches = [[]]
      for a_unit in listResult:
        id_batches[i].append(a_unit['id'])
        if len(id_batches[i]) == 1000:
          i += 1
          id_batches.append([])
      processed_messages = 0
      for id_batch in id_batches:
        kwargs['body']['ids'] = id_batch
        print('%s %s messages' % (function, len(id_batch)))
        callGAPI(unitmethod(), batchFunction,
                 userId='me', **kwargs)
        processed_messages += len(id_batch)
        print('%s %s of %s messages' % (function, processed_messages, result_count))
      continue
    if not kwargs['body']:
      del kwargs['body']
    for a_unit in listResult:
      i += 1
      print(' %s %s %s for user %s (%s/%s)' % (function, unit, a_unit['id'], user, i, result_count))
      callGAPI(unitmethod(), function,
               id=a_unit['id'], userId='me', **kwargs)

def doDeleteLabel(users):
  label = sys.argv[5]
  label_name_lower = label.lower()
  for user in users:
    user, gmail = buildGmailGAPIObject(user)
    if not gmail:
      continue
    print('Getting all labels for %s...' % user)
    labels = callGAPI(gmail.users().labels(), 'list', userId=user, fields='labels(id,name,type)')
    del_labels = []
    if label == '--ALL_LABELS--':
      for del_label in labels['labels']:
        if del_label['type'] == 'system':
          continue
        del_labels.append(del_label)
    elif label[:6].lower() == 'regex:':
      regex = label[6:]
      p = re.compile(regex)
      for del_label in labels['labels']:
        if del_label['type'] == 'system':
          continue
        elif p.match(del_label['name']):
          del_labels.append(del_label)
    else:
      for del_label in labels['labels']:
        if label_name_lower == del_label['name'].lower():
          del_labels.append(del_label)
          break
      else:
        print(' Error: no such label for %s' % user)
        continue
    bcount = 0
    j = 0
    del_me_count = len(del_labels)
    dbatch = gmail.new_batch_http_request(callback=gmail_del_result)
    for del_me in del_labels:
      j += 1
      print(' deleting label %s (%s/%s)' % (del_me['name'], j, del_me_count))
      dbatch.add(gmail.users().labels().delete(userId=user, id=del_me['id']))
      bcount += 1
      if bcount == 10:
        dbatch.execute()
        dbatch = gmail.new_batch_http_request(callback=gmail_del_result)
        bcount = 0
    if bcount > 0:
      dbatch.execute()

def gmail_del_result(request_id, response, exception):
  if exception:
    print(exception)

def showLabels(users):
  i = 5
  onlyUser = showCounts = False
  while i < len(sys.argv):
    myarg = sys.argv[i].lower().replace('_', '')
    if myarg == 'onlyuser':
      onlyUser = True
      i += 1
    elif myarg == 'showcounts':
      showCounts = True
      i += 1
    else:
      systemErrorExit(2, '%s is not a valid argument for "gam <users> show labels"' % sys.argv[i])
  for user in users:
    user, gmail = buildGmailGAPIObject(user)
    if not gmail:
      continue
    labels = callGAPI(gmail.users().labels(), 'list', userId=user, soft_errors=True)
    if labels:
      for label in labels['labels']:
        if onlyUser and (label['type'] == 'system'):
          continue
        print(utils.convertUTF8(label['name']))
        for a_key in label:
          if a_key == 'name':
            continue
          print(' %s: %s' % (a_key, label[a_key]))
        if showCounts:
          counts = callGAPI(gmail.users().labels(), 'get',
                            userId=user, id=label['id'],
                            fields='messagesTotal,messagesUnread,threadsTotal,threadsUnread')
          for a_key in counts:
            print(' %s: %s' % (a_key, counts[a_key]))
        print('')

def showGmailProfile(users):
  todrive = False
  i = 6
  while i < len(sys.argv):
    myarg = sys.argv[i].lower()
    if myarg == 'todrive':
      todrive = True
      i += 1
    else:
      systemErrorExit(2, '%s is not a valid argument for gam <users> show gmailprofile' % sys.argv[i])
  csvRows = []
  titles = ['emailAddress']
  i = 0
  count = len(users)
  for user in users:
    i += 1
    user, gmail = buildGmailGAPIObject(user)
    if not gmail:
      continue
    sys.stderr.write('Getting Gmail profile for %s\n' % user)
    try:
      results = callGAPI(gmail.users(), 'getProfile',
                         throw_reasons=GAPI_GMAIL_THROW_REASONS,
                         userId='me')
      if results:
        for item in results:
          if item not in titles:
            titles.append(item)
        csvRows.append(results)
    except GAPI_serviceNotAvailable:
      entityServiceNotApplicableWarning('User', user, i, count)
  sortCSVTitles(['emailAddress',], titles)
  writeCSVfile(csvRows, titles, list_type='Gmail Profiles', todrive=todrive)

def updateLabels(users):
  label_name = sys.argv[5]
  label_name_lower = label_name.lower()
  body = {}
  i = 6
  while i < len(sys.argv):
    myarg = sys.argv[i].lower().replace('_', '')
    if myarg == 'name':
      body['name'] = sys.argv[i+1]
      i += 2
    else:
      i = getLabelAttributes(i, myarg, body)
  checkLabelColor(body)
  for user in users:
    user, gmail = buildGmailGAPIObject(user)
    if not gmail:
      continue
    labels = callGAPI(gmail.users().labels(), 'list', userId=user, fields='labels(id,name)')
    for label in labels['labels']:
      if label['name'].lower() == label_name_lower:
        callGAPI(gmail.users().labels(), 'patch', soft_errors=True,
                 userId=user, id=label['id'], body=body)
        break
    else:
      print('Error: user does not have a label named %s' % label_name)

def renameLabels(users):
  search = '^Inbox/(.*)$'
  replace = '%s'
  merge = False
  i = 5
  while i < len(sys.argv):
    myarg = sys.argv[i].lower()
    if myarg == 'search':
      search = sys.argv[i+1]
      i += 2
    elif myarg == 'replace':
      replace = sys.argv[i+1]
      i += 2
    elif myarg == 'merge':
      merge = True
      i += 1
    else:
      systemErrorExit(2, '%s is not a valid argument for "gam <users> rename label"' % sys.argv[i])
  pattern = re.compile(search, re.IGNORECASE)
  for user in users:
    user, gmail = buildGmailGAPIObject(user)
    if not gmail:
      continue
    labels = callGAPI(gmail.users().labels(), 'list', userId=user)
    for label in labels['labels']:
      if label['type'] == 'system':
        continue
      match_result = re.search(pattern, label['name'])
      if match_result is not None:
        try:
          new_label_name = replace % match_result.groups()
        except TypeError:
          systemErrorExit(2, 'The number of subfields ({0}) in search "{1}" does not match the number of subfields ({2}) in replace "{3}"'.format(len(match_result.groups()), search, replace.count('%s'), replace))
        print(' Renaming "%s" to "%s"' % (label['name'], new_label_name))
        try:
          callGAPI(gmail.users().labels(), 'patch', soft_errors=True, throw_reasons=[GAPI_ABORTED], id=label['id'], userId=user, body={'name': new_label_name})
        except GAPI_aborted:
          if merge:
            print('  Merging %s label to existing %s label' % (label['name'], new_label_name))
            messages_to_relabel = callGAPIpages(gmail.users().messages(), 'list', 'messages',
                                                userId=user, q='label:%s' % label['name'].lower().replace('/', '-').replace(' ', '-'))
            if messages_to_relabel:
              for new_label in labels['labels']:
                if new_label['name'].lower() == new_label_name.lower():
                  new_label_id = new_label['id']
                  body = {'addLabelIds': [new_label_id]}
                  break
              j = 1
              for message_to_relabel in messages_to_relabel:
                print('    relabeling message %s (%s/%s)' % (message_to_relabel['id'], j, len(messages_to_relabel)))
                callGAPI(gmail.users().messages(), 'modify', userId=user, id=message_to_relabel['id'], body=body)
                j += 1
            else:
              print('   no messages with %s label' % label['name'])
            print('   Deleting label %s' % label['name'])
            callGAPI(gmail.users().labels(), 'delete', id=label['id'], userId=user)
          else:
            print('  Error: looks like %s already exists, not renaming. Use the "merge" argument to merge the labels' % new_label_name)

def _getUserGmailLabels(gmail, user, i, count, **kwargs):
  try:
    labels = callGAPI(gmail.users().labels(), 'list',
                      throw_reasons=GAPI_GMAIL_THROW_REASONS,
                      userId='me', **kwargs)
    if not labels:
      labels = {'labels': []}
    return labels
  except GAPI_serviceNotAvailable:
    entityServiceNotApplicableWarning('User', user, i, count)
    return None

def _getLabelId(labels, labelName):
  for label in labels['labels']:
    if labelName in (label['id'], label['name']):
      return label['id']
  return None

def _getLabelName(labels, labelId):
  for label in labels['labels']:
    if label['id'] == labelId:
      return label['name']
  return labelId

def _printFilter(user, userFilter, labels):
  row = {'User': user, 'id': userFilter['id']}
  if 'criteria' in userFilter:
    for item in userFilter['criteria']:
      if item in ['hasAttachment', 'excludeChats']:
        row[item] = item
      elif item == 'size':
        row[item] = 'size {0} {1}'.format(userFilter['criteria']['sizeComparison'], userFilter['criteria'][item])
      elif item == 'sizeComparison':
        pass
      else:
        row[item] = '{0} {1}'.format(item, userFilter['criteria'][item])
  else:
    row['error'] = 'NoCriteria'
  if 'action' in userFilter:
    for labelId in userFilter['action'].get('addLabelIds', []):
      if labelId in FILTER_ADD_LABEL_TO_ARGUMENT_MAP:
        row[FILTER_ADD_LABEL_TO_ARGUMENT_MAP[labelId]] = FILTER_ADD_LABEL_TO_ARGUMENT_MAP[labelId]
      else:
        row['label'] = 'label {0}'.format(_getLabelName(labels, labelId))
    for labelId in userFilter['action'].get('removeLabelIds', []):
      if labelId in FILTER_REMOVE_LABEL_TO_ARGUMENT_MAP:
        row[FILTER_REMOVE_LABEL_TO_ARGUMENT_MAP[labelId]] = FILTER_REMOVE_LABEL_TO_ARGUMENT_MAP[labelId]
    if userFilter['action'].get('forward'):
      row['forward'] = 'forward {0}'.format(userFilter['action']['forward'])
  else:
    row['error'] = 'NoActions'
  return row

def _showFilter(userFilter, j, jcount, labels):
  print('  Filter: {0}{1}'.format(userFilter['id'], currentCount(j, jcount)))
  print('    Criteria:')
  if 'criteria' in userFilter:
    for item in userFilter['criteria']:
      if item in ['hasAttachment', 'excludeChats']:
        print('      {0}'.format(item))
      elif item == 'size':
        print('      {0} {1} {2}'.format(item, userFilter['criteria']['sizeComparison'], userFilter['criteria'][item]))
      elif item == 'sizeComparison':
        pass
      else:
        print(utils.convertUTF8('      {0} "{1}"'.format(item, userFilter['criteria'][item])))
  else:
    print('      ERROR: No Filter criteria')
  print('    Actions:')
  if 'action' in userFilter:
    for labelId in userFilter['action'].get('addLabelIds', []):
      if labelId in FILTER_ADD_LABEL_TO_ARGUMENT_MAP:
        print('      {0}'.format(FILTER_ADD_LABEL_TO_ARGUMENT_MAP[labelId]))
      else:
        print(utils.convertUTF8('      label "{0}"'.format(_getLabelName(labels, labelId))))
    for labelId in userFilter['action'].get('removeLabelIds', []):
      if labelId in FILTER_REMOVE_LABEL_TO_ARGUMENT_MAP:
        print('      {0}'.format(FILTER_REMOVE_LABEL_TO_ARGUMENT_MAP[labelId]))
    if userFilter['action'].get('forward'):
      print('    Forwarding Address: {0}'.format(userFilter['action']['forward']))
  else:
    print('      ERROR: No Filter actions')

def addFilter(users, i):
  body = {}
  addLabelName = None
  addLabelIds = []
  removeLabelIds = []
  while i < len(sys.argv):
    myarg = sys.argv[i].lower()
    if myarg in FILTER_CRITERIA_CHOICES_MAP:
      myarg = FILTER_CRITERIA_CHOICES_MAP[myarg]
      body.setdefault('criteria', {})
      if myarg == 'from':
        body['criteria'][myarg] = sys.argv[i+1]
        i += 2
      elif myarg == 'to':
        body['criteria'][myarg] = sys.argv[i+1]
        i += 2
      elif myarg in ['subject', 'query', 'negatedQuery']:
        body['criteria'][myarg] = sys.argv[i+1]
        i += 2
      elif myarg in ['hasAttachment', 'excludeChats']:
        body['criteria'][myarg] = True
        i += 1
      elif myarg == 'size':
        body['criteria']['sizeComparison'] = sys.argv[i+1].lower()
        if body['criteria']['sizeComparison'] not in ['larger', 'smaller']:
          systemErrorExit(2, 'size must be followed by larger or smaller; got %s' % sys.argv[i+1].lower())
        body['criteria'][myarg] = sys.argv[i+2]
        i += 3
    elif myarg in FILTER_ACTION_CHOICES:
      body.setdefault('action', {})
      if myarg == 'label':
        addLabelName = sys.argv[i+1]
        i += 2
      elif myarg == 'important':
        addLabelIds.append('IMPORTANT')
        if 'IMPORTANT' in removeLabelIds:
          removeLabelIds.remove('IMPORTANT')
        i += 1
      elif myarg == 'star':
        addLabelIds.append('STARRED')
        i += 1
      elif myarg == 'trash':
        addLabelIds.append('TRASH')
        i += 1
      elif myarg == 'notimportant':
        removeLabelIds.append('IMPORTANT')
        if 'IMPORTANT' in addLabelIds:
          addLabelIds.remove('IMPORTANT')
        i += 1
      elif myarg == 'markread':
        removeLabelIds.append('UNREAD')
        i += 1
      elif myarg == 'archive':
        removeLabelIds.append('INBOX')
        i += 1
      elif myarg == 'neverspam':
        removeLabelIds.append('SPAM')
        i += 1
      elif myarg == 'forward':
        body['action']['forward'] = sys.argv[i+1]
        i += 2
    else:
      systemErrorExit(2, '%s is not a valid argument for "gam <users> filter"' % sys.argv[i])
  if 'criteria' not in body:
    systemErrorExit(2, 'you must specify a crtieria <{0}> for "gam <users> filter"'.format('|'.join(FILTER_CRITERIA_CHOICES_MAP)))
  if 'action' not in body:
    systemErrorExit(2, 'you must specify an action <{0}> for "gam <users> filter"'.format('|'.join(FILTER_ACTION_CHOICES)))
  if removeLabelIds:
    body['action']['removeLabelIds'] = removeLabelIds
  i = 0
  count = len(users)
  for user in users:
    i += 1
    user, gmail = buildGmailGAPIObject(user)
    if not gmail:
      continue
    labels = _getUserGmailLabels(gmail, user, i, count, fields='labels(id,name)')
    if not labels:
      continue
    if addLabelIds:
      body['action']['addLabelIds'] = addLabelIds[:]
    if addLabelName:
      if not addLabelIds:
        body['action']['addLabelIds'] = []
      addLabelId = _getLabelId(labels, addLabelName)
      if not addLabelId:
        result = callGAPI(gmail.users().labels(), 'create',
                          soft_errors=True,
                          userId='me', body={'name': addLabelName}, fields='id')
        if not result:
          continue
        addLabelId = result['id']
      body['action']['addLabelIds'].append(addLabelId)
    print("Adding filter for %s (%s/%s)" % (user, i, count))
    result = callGAPI(gmail.users().settings().filters(), 'create',
                      soft_errors=True,
                      userId='me', body=body)
    if result:
      print("User: %s, Filter: %s, Added (%s/%s)" % (user, result['id'], i, count))

def deleteFilters(users):
  filterId = sys.argv[5]
  i = 0
  count = len(users)
  for user in users:
    i += 1
    user, gmail = buildGmailGAPIObject(user)
    if not gmail:
      continue
    print("Deleting filter %s for %s (%s/%s)" % (filterId, user, i, count))
    callGAPI(gmail.users().settings().filters(), 'delete',
             soft_errors=True,
             userId='me', id=filterId)

def printShowFilters(users, csvFormat):
  if csvFormat:
    todrive = False
    csvRows = []
    titles = ['User', 'id']
  i = 5
  while i < len(sys.argv):
    myarg = sys.argv[i].lower()
    if csvFormat and myarg == 'todrive':
      todrive = True
      i += 1
    else:
      systemErrorExit(2, '%s is not a valid argument for "gam <users> %s filter"' % (myarg, ['show', 'print'][csvFormat]))
  i = 0
  count = len(users)
  for user in users:
    i += 1
    user, gmail = buildGmailGAPIObject(user)
    if not gmail:
      continue
    labels = callGAPI(gmail.users().labels(), 'list',
                      soft_errors=True,
                      userId='me', fields='labels(id,name)')
    if not labels:
      labels = {'labels': []}
    result = callGAPI(gmail.users().settings().filters(), 'list',
                      soft_errors=True,
                      userId='me')
    jcount = len(result.get('filter', [])) if (result) else 0
    if not csvFormat:
      print('User: {0}, Filters: ({1}/{2})'.format(user, i, count))
      if jcount == 0:
        continue
      j = 0
      for userFilter in result['filter']:
        j += 1
        _showFilter(userFilter, j, jcount, labels)
    else:
      if jcount == 0:
        continue
      for userFilter in result['filter']:
        row = _printFilter(user, userFilter, labels)
        for item in row:
          if item not in titles:
            titles.append(item)
        csvRows.append(row)
  if csvFormat:
    sortCSVTitles(['User', 'id'], titles)
    writeCSVfile(csvRows, titles, 'Filters', todrive)

def infoFilters(users):
  filterId = sys.argv[5]
  i = 0
  count = len(users)
  for user in users:
    i += 1
    user, gmail = buildGmailGAPIObject(user)
    if not gmail:
      continue
    labels = callGAPI(gmail.users().labels(), 'list',
                      soft_errors=True,
                      userId='me', fields='labels(id,name)')
    if not labels:
      labels = {'labels': []}
    result = callGAPI(gmail.users().settings().filters(), 'get',
                      soft_errors=True,
                      userId='me', id=filterId)
    if result:
      print('User: {0}, Filter: ({1}/{2})'.format(user, i, count))
      _showFilter(result, 1, 1, labels)

def doForward(users):
  enable = getBoolean(sys.argv[4], 'gam <users> forward')
  body = {'enabled': enable}
  i = 5
  while i < len(sys.argv):
    myarg = sys.argv[i].lower()
    if myarg in EMAILSETTINGS_FORWARD_POP_ACTION_CHOICES_MAP:
      body['disposition'] = EMAILSETTINGS_FORWARD_POP_ACTION_CHOICES_MAP[myarg]
      i += 1
    elif myarg == 'confirm':
      i += 1
    elif myarg.find('@') != -1:
      body['emailAddress'] = sys.argv[i]
      i += 1
    else:
      systemErrorExit(2, '%s is not a valid argument for "gam <users> forward"' % myarg)
  if enable and (not body.get('disposition') or not body.get('emailAddress')):
    systemErrorExit(2, 'you must specify an action and a forwarding address for "gam <users> forward')
  i = 0
  count = len(users)
  for user in users:
    i += 1
    user, gmail = buildGmailGAPIObject(user)
    if not gmail:
      continue
    if enable:
      print("User: %s, Forward Enabled: %s, Forwarding Address: %s, Action: %s (%s/%s)" % (user, enable, body['emailAddress'], body['disposition'], i, count))
    else:
      print("User: %s, Forward Enabled: %s (%s/%s)" % (user, enable, i, count))
    callGAPI(gmail.users().settings(), 'updateAutoForwarding',
             soft_errors=True,
             userId='me', body=body)

def printShowForward(users, csvFormat):
  def _showForward(user, i, count, result):
    if 'enabled' in result:
      enabled = result['enabled']
      if enabled:
        print("User: %s, Forward Enabled: %s, Forwarding Address: %s, Action: %s (%s/%s)" % (user, enabled, result['emailAddress'], result['disposition'], i, count))
      else:
        print("User: %s, Forward Enabled: %s (%s/%s)" % (user, enabled, i, count))
    else:
      enabled = result['enable'] == 'true'
      if enabled:
        print("User: %s, Forward Enabled: %s, Forwarding Address: %s, Action: %s (%s/%s)" % (user, enabled, result['forwardTo'], EMAILSETTINGS_OLD_NEW_OLD_FORWARD_ACTION_MAP[result['action']], i, count))
      else:
        print("User: %s, Forward Enabled: %s (%s/%s)" % (user, enabled, i, count))

  def _printForward(user, result):
    if 'enabled' in result:
      row = {'User': user, 'forwardEnabled': result['enabled']}
      if result['enabled']:
        row['forwardTo'] = result['emailAddress']
        row['disposition'] = result['disposition']
    else:
      row = {'User': user, 'forwardEnabled': result['enable']}
      if result['enable'] == 'true':
        row['forwardTo'] = result['forwardTo']
        row['disposition'] = EMAILSETTINGS_OLD_NEW_OLD_FORWARD_ACTION_MAP[result['action']]
    csvRows.append(row)

  if csvFormat:
    todrive = False
    csvRows = []
    titles = ['User', 'forwardEnabled', 'forwardTo', 'disposition']
  i = 5
  while i < len(sys.argv):
    myarg = sys.argv[i].lower()
    if csvFormat and myarg == 'todrive':
      todrive = True
      i += 1
    else:
      systemErrorExit(2, '%s is not a valid argument for "gam <users> %s forward"' % (myarg, ['show', 'print'][csvFormat]))
  i = 0
  count = len(users)
  for user in users:
    i += 1
    user, gmail = buildGmailGAPIObject(user)
    if not gmail:
      continue
    result = callGAPI(gmail.users().settings(), 'getAutoForwarding',
                      soft_errors=True,
                      userId='me')
    if result:
      if not csvFormat:
        _showForward(user, i, count, result)
      else:
        _printForward(user, result)
  if csvFormat:
    writeCSVfile(csvRows, titles, 'Forward', todrive)

def addForwardingAddresses(users):
  emailAddress = normalizeEmailAddressOrUID(sys.argv[5], noUid=True)
  body = {'forwardingEmail':  emailAddress}
  i = 0
  count = len(users)
  for user in users:
    i += 1
    user, gmail = buildGmailGAPIObject(user)
    if not gmail:
      continue
    print("Adding Forwarding Address %s for %s (%s/%s)" % (emailAddress, user, i, count))
    callGAPI(gmail.users().settings().forwardingAddresses(), 'create',
             soft_errors=True,
             userId='me', body=body)

def deleteForwardingAddresses(users):
  emailAddress = normalizeEmailAddressOrUID(sys.argv[5], noUid=True)
  i = 0
  count = len(users)
  for user in users:
    i += 1
    user, gmail = buildGmailGAPIObject(user)
    if not gmail:
      continue
    print("Deleting Forwarding Address %s for %s (%s/%s)" % (emailAddress, user, i, count))
    callGAPI(gmail.users().settings().forwardingAddresses(), 'delete',
             soft_errors=True,
             userId='me', forwardingEmail=emailAddress)

def printShowForwardingAddresses(users, csvFormat):
  if csvFormat:
    todrive = False
    csvRows = []
    titles = ['User', 'forwardingEmail', 'verificationStatus']
  i = 5
  while i < len(sys.argv):
    myarg = sys.argv[i].lower()
    if csvFormat and myarg == 'todrive':
      todrive = True
      i += 1
    else:
      systemErrorExit(2, '%s is not a valid argument for "gam <users> %s forwardingaddresses"' % (myarg, ['show', 'print'][csvFormat]))
  i = 0
  count = len(users)
  for user in users:
    i += 1
    user, gmail = buildGmailGAPIObject(user)
    if not gmail:
      continue
    result = callGAPI(gmail.users().settings().forwardingAddresses(), 'list',
                      soft_errors=True,
                      userId='me')
    jcount = len(result.get('forwardingAddresses', [])) if (result) else 0
    if not csvFormat:
      print('User: {0}, Forwarding Addresses: ({1}/{2})'.format(user, i, count))
      if jcount == 0:
        continue
      j = 0
      for forward in result['forwardingAddresses']:
        j += 1
        print('  Forwarding Address: {0}, Verification Status: {1} ({2}/{3})'.format(forward['forwardingEmail'], forward['verificationStatus'], j, jcount))
    else:
      if jcount == 0:
        continue
      for forward in result['forwardingAddresses']:
        row = {'User': user, 'forwardingEmail': forward['forwardingEmail'], 'verificationStatus': forward['verificationStatus']}
        csvRows.append(row)
  if csvFormat:
    writeCSVfile(csvRows, titles, 'Forwarding Addresses', todrive)

def infoForwardingAddresses(users):
  emailAddress = normalizeEmailAddressOrUID(sys.argv[5], noUid=True)
  i = 0
  count = len(users)
  for user in users:
    i += 1
    user, gmail = buildGmailGAPIObject(user)
    if not gmail:
      continue
    forward = callGAPI(gmail.users().settings().forwardingAddresses(), 'get',
                       soft_errors=True,
                       userId='me', forwardingEmail=emailAddress)
    if forward:
      print('User: {0}, Forwarding Address: {1}, Verification Status: {2} ({3}/{4})'.format(user, forward['forwardingEmail'], forward['verificationStatus'], i, count))

def doSignature(users):
  tagReplacements = {}
  i = 4
  if sys.argv[i].lower() == 'file':
    filename = sys.argv[i+1]
    i, encoding = getCharSet(i+2)
    signature = readFile(filename, encoding=encoding)
  else:
    signature = getString(i, 'String', minLen=0)
    i += 1
  body = {}
  html = False
  while i < len(sys.argv):
    myarg = sys.argv[i].lower()
    if myarg == 'html':
      html = True
      i += 1
    else:
      i = getSendAsAttributes(i, myarg, body, tagReplacements, 'signature')
  body['signature'] = _processSignature(tagReplacements, signature, html)
  i = 0
  count = len(users)
  for user in users:
    i += 1
    user, gmail = buildGmailGAPIObject(user)
    if not gmail:
      continue
    print('Setting Signature for {0} ({1}/{2})'.format(user, i, count))
    callGAPI(gmail.users().settings().sendAs(), 'patch',
             soft_errors=True,
             userId='me', body=body, sendAsEmail=user)

def getSignature(users):
  formatSig = False
  i = 5
  while i < len(sys.argv):
    myarg = sys.argv[i].lower()
    if myarg == 'format':
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
    result = callGAPI(gmail.users().settings().sendAs(), 'get',
                      soft_errors=True,
                      userId='me', sendAsEmail=user)
    if result:
      _showSendAs(result, i, count, formatSig)

def doVacation(users):
  enable = getBoolean(sys.argv[4], 'gam <users> vacation')
  body = {'enableAutoReply': enable}
  if enable:
    responseBodyType = 'responseBodyPlainText'
    message = None
    tagReplacements = {}
    i = 5
    while i < len(sys.argv):
      myarg = sys.argv[i].lower()
      if myarg == 'subject':
        body['responseSubject'] = sys.argv[i+1]
        i += 2
      elif myarg == 'message':
        message = sys.argv[i+1]
        i += 2
      elif myarg == 'file':
        filename = sys.argv[i+1]
        i, encoding = getCharSet(i+2)
        message = readFile(filename, encoding=encoding)
      elif myarg == 'replace':
        matchTag = getString(i+1, 'Tag')
        matchReplacement = getString(i+2, 'String', minLen=0)
        tagReplacements[matchTag] = matchReplacement
        i += 3
      elif myarg == 'html':
        responseBodyType = 'responseBodyHtml'
        i += 1
      elif myarg == 'contactsonly':
        body['restrictToContacts'] = True
        i += 1
      elif myarg == 'domainonly':
        body['restrictToDomain'] = True
        i += 1
      elif myarg == 'startdate':
        body['startTime'] = getYYYYMMDD(sys.argv[i+1], returnTimeStamp=True)
        i += 2
      elif myarg == 'enddate':
        body['endTime'] = getYYYYMMDD(sys.argv[i+1], returnTimeStamp=True)
        i += 2
      else:
        systemErrorExit(2, '%s is not a valid argument for "gam <users> vacation"' % sys.argv[i])
    if message:
      if responseBodyType == 'responseBodyHtml':
        message = message.replace('\r', '').replace('\\n', '<br/>')
      else:
        message = message.replace('\r', '').replace('\\n', '\n')
      if tagReplacements:
        message = _processTags(tagReplacements, message)
      body[responseBodyType] = message
    if not message and not body.get('responseSubject'):
      systemErrorExit(2, 'You must specify a non-blank subject or message!')
  i = 0
  count = len(users)
  for user in users:
    i += 1
    user, gmail = buildGmailGAPIObject(user)
    if not gmail:
      continue
    print("Setting Vacation for %s (%s/%s)" % (user, i, count))
    callGAPI(gmail.users().settings(), 'updateVacation',
             soft_errors=True,
             userId='me', body=body)

def getVacation(users):
  formatReply = False
  i = 5
  while i < len(sys.argv):
    myarg = sys.argv[i].lower()
    if myarg == 'format':
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
    result = callGAPI(gmail.users().settings(), 'getVacation',
                      soft_errors=True,
                      userId='me')
    if result:
      enabled = result['enableAutoReply']
      print('User: {0}, Vacation: ({1}/{2})'.format(user, i, count))
      print('  Enabled: {0}'.format(enabled))
      if enabled:
        print('  Contacts Only: {0}'.format(result['restrictToContacts']))
        print('  Domain Only: {0}'.format(result['restrictToDomain']))
        if 'startTime' in result:
          print('  Start Date: {0}'.format(datetime.datetime.fromtimestamp(int(result['startTime'])/1000).strftime('%Y-%m-%d')))
        else:
          print('  Start Date: Started')
        if 'endTime' in result:
          print('  End Date: {0}'.format(datetime.datetime.fromtimestamp(int(result['endTime'])/1000).strftime('%Y-%m-%d')))
        else:
          print('  End Date: Not specified')
        print(utils.convertUTF8('  Subject: {0}'.format(result.get('responseSubject', 'None'))))
        sys.stdout.write('  Message:\n   ')
        if result.get('responseBodyPlainText'):
          print(utils.convertUTF8(utils.indentMultiLineText(result['responseBodyPlainText'], n=4)))
        elif result.get('responseBodyHtml'):
          if formatReply:
            print(utils.convertUTF8(utils.indentMultiLineText(utils.dehtml(result['responseBodyHtml']), n=4)))
          else:
            print(utils.convertUTF8(utils.indentMultiLineText(result['responseBodyHtml'], n=4)))
        else:
          print('None')

def doDelSchema():
  cd = buildGAPIObject('directory')
  schemaKey = sys.argv[3]
  callGAPI(cd.schemas(), 'delete', customerId=GC_Values[GC_CUSTOMER_ID], schemaKey=schemaKey)
  print('Deleted schema %s' % schemaKey)

def doCreateOrUpdateUserSchema(updateCmd):
  cd = buildGAPIObject('directory')
  schemaKey = sys.argv[3]
  if updateCmd:
    cmd = 'update'
    try:
      body = callGAPI(cd.schemas(), 'get', throw_reasons=[GAPI_NOT_FOUND], customerId=GC_Values[GC_CUSTOMER_ID], schemaKey=schemaKey)
    except GAPI_notFound:
      systemErrorExit(3, 'Schema %s does not exist.' % schemaKey)
  else: # create
    cmd = 'create'
    body = {'schemaName': schemaKey, 'fields': []}
  i = 4
  while i < len(sys.argv):
    myarg = sys.argv[i].lower()
    if myarg == 'field':
      if updateCmd: # clear field if it exists on update
        for n, field in enumerate(body['fields']):
          if field['fieldName'].lower() == sys.argv[i+1].lower():
            del body['fields'][n]
            break
      a_field = {'fieldName': sys.argv[i+1]}
      i += 2
      while True:
        myarg = sys.argv[i].lower()
        if myarg == 'type':
          a_field['fieldType'] = sys.argv[i+1].upper()
          if a_field['fieldType'] not in ['BOOL', 'DOUBLE', 'EMAIL', 'INT64', 'PHONE', 'STRING']:
            systemErrorExit(2, 'type must be one of bool, double, email, int64, phone, string; got %s' % a_field['fieldType'])
          i += 2
        elif myarg == 'multivalued':
          a_field['multiValued'] = True
          i += 1
        elif myarg == 'indexed':
          a_field['indexed'] = True
          i += 1
        elif myarg == 'restricted':
          a_field['readAccessType'] = 'ADMINS_AND_SELF'
          i += 1
        elif myarg == 'range':
          a_field['numericIndexingSpec'] = {'minValue': getInteger(sys.argv[i+1], myarg),
                                            'maxValue': getInteger(sys.argv[i+2], myarg)}
          i += 3
        elif myarg == 'endfield':
          body['fields'].append(a_field)
          i += 1
          break
        else:
          systemErrorExit(2, '%s is not a valid argument for "gam %s schema"' % (sys.argv[i], cmd))
    elif updateCmd and myarg == 'deletefield':
      for n, field in enumerate(body['fields']):
        if field['fieldName'].lower() == sys.argv[i+1].lower():
          del body['fields'][n]
          break
      else:
        systemErrorExit(3, 'field %s not found in schema %s' % (sys.argv[i+1], schemaKey))
      i += 2
    else:
      systemErrorExit(2, '%s is not a valid argument for "gam %s schema"' % (sys.argv[i], cmd))
  if updateCmd:
    result = callGAPI(cd.schemas(), 'update', customerId=GC_Values[GC_CUSTOMER_ID], body=body, schemaKey=schemaKey)
    print('Updated user schema %s' % result['schemaName'])
  else:
    result = callGAPI(cd.schemas(), 'insert', customerId=GC_Values[GC_CUSTOMER_ID], body=body)
    print('Created user schema %s' % result['schemaName'])

def _showSchema(schema):
  print('Schema: %s' % schema['schemaName'])
  for a_key in schema:
    if a_key not in ['schemaName', 'fields', 'etag', 'kind']:
      print(' %s: %s' % (a_key, schema[a_key]))
  for field in schema['fields']:
    print(' Field: %s' % field['fieldName'])
    for a_key in field:
      if a_key not in ['fieldName', 'kind', 'etag']:
        print('  %s: %s' % (a_key, field[a_key]))

def doPrintShowUserSchemas(csvFormat):
  cd = buildGAPIObject('directory')
  if csvFormat:
    todrive = False
    csvRows = []
    titles = []
  i = 3
  while i < len(sys.argv):
    myarg = sys.argv[i].lower()
    if csvFormat and myarg == 'todrive':
      todrive = True
      i += 1
    else:
      systemErrorExit(2, '%s is not a valid argument for "gam %s schemas"' % (myarg, ['show', 'print'][csvFormat]))
  schemas = callGAPI(cd.schemas(), 'list', customerId=GC_Values[GC_CUSTOMER_ID])
  if not schemas or 'schemas' not in schemas:
    return
  for schema in schemas['schemas']:
    if not csvFormat:
      _showSchema(schema)
    else:
      row = {'fields.Count': len(schema['fields'])}
      addRowTitlesToCSVfile(flatten_json(schema, flattened=row), csvRows, titles)
  if csvFormat:
    sortCSVTitles(['schemaId', 'schemaName', 'fields.Count'], titles)
    writeCSVfile(csvRows, titles, 'User Schemas', todrive)

def doGetUserSchema():
  cd = buildGAPIObject('directory')
  schemaKey = sys.argv[3]
  schema = callGAPI(cd.schemas(), 'get', customerId=GC_Values[GC_CUSTOMER_ID], schemaKey=schemaKey)
  _showSchema(schema)

def getUserAttributes(i, cd, updateCmd):
  def getEntryType(i, entry, entryTypes, setTypeCustom=True, customKeyword='custom', customTypeKeyword='customType'):
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
      entry['type'] = ltype
      entry.pop(customTypeKeyword, None)
    else:
      entry[customTypeKeyword] = utype
      if setTypeCustom:
        entry['type'] = customKeyword
      else:
        entry.pop('type', None)
    return i+1

  def checkClearBodyList(i, body, itemName):
    if sys.argv[i].lower() == 'clear':
      body.pop(itemName, None)
      body[itemName] = None
      return True
    return False

  def appendItemToBodyList(body, itemName, itemValue, checkSystemId=False):
    if (itemName in body) and (body[itemName] is None):
      del body[itemName]
    body.setdefault(itemName, [])
# Throw an error if multiple items are marked primary
    if itemValue.get('primary', False):
      for citem in body[itemName]:
        if citem.get('primary', False):
          if not checkSystemId or itemValue.get('systemId') == citem.get('systemId'):
            systemErrorExit(2, 'Multiple {0} are marked primary, only one can be primary'.format(itemName))
    body[itemName].append(itemValue)

  def _splitSchemaNameDotFieldName(sn_fn, fnRequired=True):
    if sn_fn.find('.') != -1:
      schemaName, fieldName = sn_fn.split('.', 1)
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
    body = {'name': {'givenName': 'Unknown', 'familyName': 'Unknown'}}
    body['primaryEmail'] = normalizeEmailAddressOrUID(sys.argv[i], noUid=True)
    i += 1
    need_password = True
  need_to_hash_password = True
  while i < len(sys.argv):
    myarg = sys.argv[i].lower()
    if myarg in ['firstname', 'givenname']:
      body.setdefault('name', {})
      body['name']['givenName'] = sys.argv[i+1]
      i += 2
    elif myarg in ['lastname', 'familyname']:
      body.setdefault('name', {})
      body['name']['familyName'] = sys.argv[i+1]
      i += 2
    elif myarg in ['username', 'email', 'primaryemail'] and updateCmd:
      body['primaryEmail'] = normalizeEmailAddressOrUID(sys.argv[i+1], noUid=True)
      i += 2
    elif myarg == 'customerid' and updateCmd:
      body['customerId'] = sys.argv[i+1]
      i += 2
    elif myarg == 'password':
      need_password = False
      body['password'] = sys.argv[i+1]
      if body['password'].lower() == 'random':
        need_password = True
      i += 2
    elif myarg == 'admin':
      value = getBoolean(sys.argv[i+1], myarg)
      if updateCmd or value:
        systemErrorExit(2, '%s %s is not a valid argument for "gam %s user"' % (sys.argv[i], value, ['create', 'update'][updateCmd]))
      i += 2
    elif myarg == 'suspended':
      body['suspended'] = getBoolean(sys.argv[i+1], myarg)
      i += 2
    elif myarg == 'archived':
      body['archived'] = getBoolean(sys.argv[i+1], myarg)
      i += 2
    elif myarg == 'gal':
      body['includeInGlobalAddressList'] = getBoolean(sys.argv[i+1], myarg)
      i += 2
    elif myarg in ['sha', 'sha1', 'sha-1']:
      body['hashFunction'] = 'SHA-1'
      need_to_hash_password = False
      i += 1
    elif myarg == 'md5':
      body['hashFunction'] = 'MD5'
      need_to_hash_password = False
      i += 1
    elif myarg == 'crypt':
      body['hashFunction'] = 'crypt'
      need_to_hash_password = False
      i += 1
    elif myarg == 'nohash':
      need_to_hash_password = False
      i += 1
    elif myarg == 'changepassword':
      body['changePasswordAtNextLogin'] = getBoolean(sys.argv[i+1], myarg)
      i += 2
    elif myarg == 'ipwhitelisted':
      body['ipWhitelisted'] = getBoolean(sys.argv[i+1], myarg)
      i += 2
    elif myarg == 'agreedtoterms':
      body['agreedToTerms'] = getBoolean(sys.argv[i+1], myarg)
      i += 2
    elif myarg in ['org', 'ou']:
      body['orgUnitPath'] = getOrgUnitItem(sys.argv[i+1], pathOnly=True)
      i += 2
    elif myarg in ['language', 'languages']:
      i += 1
      if checkClearBodyList(i, body, 'languages'):
        i += 1
        continue
      for language in sys.argv[i].replace(',', ' ').split():
        if language.lower() in LANGUAGE_CODES_MAP:
          appendItemToBodyList(body, 'languages', {'languageCode': LANGUAGE_CODES_MAP[language.lower()]})
        else:
          appendItemToBodyList(body, 'languages', {'customLanguage': language})
      i += 1
    elif myarg == 'gender':
      i += 1
      if checkClearBodyList(i, body, 'gender'):
        i += 1
        continue
      gender = {}
      i = getEntryType(i, gender, USER_GENDER_TYPES, customKeyword='other', customTypeKeyword='customGender')
      if (i < len(sys.argv)) and (sys.argv[i].lower() == 'addressmeas'):
        gender['addressMeAs'] = getString(i+1, 'String')
        i += 2
      body['gender'] = gender
    elif myarg in ['address', 'addresses']:
      i += 1
      if checkClearBodyList(i, body, 'addresses'):
        i += 1
        continue
      address = {}
      if sys.argv[i].lower() != 'type':
        systemErrorExit(2, 'wrong format for account address details. Expected type got %s' % sys.argv[i])
      i = getEntryType(i+1, address, USER_ADDRESS_TYPES)
      if sys.argv[i].lower() in ['unstructured', 'formatted']:
        i += 1
        address['sourceIsStructured'] = False
        address['formatted'] = sys.argv[i].replace('\\n', '\n')
        i += 1
      while True:
        myopt = sys.argv[i].lower()
        if myopt == 'pobox':
          address['poBox'] = sys.argv[i+1]
          i += 2
        elif myopt == 'extendedaddress':
          address['extendedAddress'] = sys.argv[i+1]
          i += 2
        elif myopt == 'streetaddress':
          address['streetAddress'] = sys.argv[i+1]
          i += 2
        elif myopt == 'locality':
          address['locality'] = sys.argv[i+1]
          i += 2
        elif myopt == 'region':
          address['region'] = sys.argv[i+1]
          i += 2
        elif myopt == 'postalcode':
          address['postalCode'] = sys.argv[i+1]
          i += 2
        elif myopt == 'country':
          address['country'] = sys.argv[i+1]
          i += 2
        elif myopt == 'countrycode':
          address['countryCode'] = sys.argv[i+1]
          i += 2
        elif myopt in ['notprimary', 'primary']:
          address['primary'] = myopt == 'primary'
          i += 1
          break
        else:
          systemErrorExit(2, 'invalid argument (%s) for account address details' % sys.argv[i])
      appendItemToBodyList(body, 'addresses', address)
    elif myarg in ['emails', 'otheremail', 'otheremails']:
      i += 1
      if checkClearBodyList(i, body, 'emails'):
        i += 1
        continue
      an_email = {}
      i = getEntryType(i, an_email, USER_EMAIL_TYPES)
      an_email['address'] = sys.argv[i]
      i += 1
      appendItemToBodyList(body, 'emails', an_email)
    elif myarg in ['im', 'ims']:
      i += 1
      if checkClearBodyList(i, body, 'ims'):
        i += 1
        continue
      im = {}
      if sys.argv[i].lower() != 'type':
        systemErrorExit(2, 'wrong format for account im details. Expected type got %s' % sys.argv[i])
      i = getEntryType(i+1, im, USER_IM_TYPES)
      if sys.argv[i].lower() != 'protocol':
        systemErrorExit(2, 'wrong format for account details. Expected protocol got %s' % sys.argv[i])
      i += 1
      im['protocol'] = sys.argv[i].lower()
      if im['protocol'] not in ['custom_protocol', 'aim', 'gtalk', 'icq', 'jabber', 'msn', 'net_meeting', 'qq', 'skype', 'yahoo']:
        systemErrorExit(2, 'protocol must be one of custom_protocol, aim, gtalk, icq, jabber, msn, net_meeting, qq, skype, yahoo; got %s' % im['protocol'])
      if im['protocol'] == 'custom_protocol':
        i += 1
        im['customProtocol'] = sys.argv[i]
      i += 1
      # Backwards compatability: notprimary|primary on either side of IM address
      myopt = sys.argv[i].lower()
      if myopt in ['notprimary', 'primary']:
        im['primary'] = myopt == 'primary'
        i += 1
      im['im'] = sys.argv[i]
      i += 1
      myopt = sys.argv[i].lower()
      if myopt in ['notprimary', 'primary']:
        im['primary'] = myopt == 'primary'
        i += 1
      appendItemToBodyList(body, 'ims', im)
    elif myarg in ['organization', 'organizations']:
      i += 1
      if checkClearBodyList(i, body, 'organizations'):
        i += 1
        continue
      organization = {}
      while True:
        myopt = sys.argv[i].lower()
        if myopt == 'name':
          organization['name'] = sys.argv[i+1]
          i += 2
        elif myopt == 'title':
          organization['title'] = sys.argv[i+1]
          i += 2
        elif myopt == 'customtype':
          organization['customType'] = sys.argv[i+1]
          organization.pop('type', None)
          i += 2
        elif myopt == 'type':
          i = getEntryType(i+1, organization, USER_ORGANIZATION_TYPES, setTypeCustom=False)
        elif myopt == 'department':
          organization['department'] = sys.argv[i+1]
          i += 2
        elif myopt == 'symbol':
          organization['symbol'] = sys.argv[i+1]
          i += 2
        elif myopt == 'costcenter':
          organization['costCenter'] = sys.argv[i+1]
          i += 2
        elif myopt == 'location':
          organization['location'] = sys.argv[i+1]
          i += 2
        elif myopt == 'description':
          organization['description'] = sys.argv[i+1]
          i += 2
        elif myopt == 'domain':
          organization['domain'] = sys.argv[i+1]
          i += 2
        elif myopt in ['notprimary', 'primary']:
          organization['primary'] = myopt == 'primary'
          i += 1
          break
        else:
          systemErrorExit(2, 'invalid argument (%s) for account organization details' % sys.argv[i])
      appendItemToBodyList(body, 'organizations', organization)
    elif myarg in ['phone', 'phones']:
      i += 1
      if checkClearBodyList(i, body, 'phones'):
        i += 1
        continue
      phone = {}
      while True:
        myopt = sys.argv[i].lower()
        if myopt == 'value':
          phone['value'] = sys.argv[i+1]
          i += 2
        elif myopt == 'type':
          i = getEntryType(i+1, phone, USER_PHONE_TYPES)
        elif myopt in ['notprimary', 'primary']:
          phone['primary'] = myopt == 'primary'
          i += 1
          break
        else:
          systemErrorExit(2, 'invalid argument (%s) for account phone details' % sys.argv[i])
      appendItemToBodyList(body, 'phones', phone)
    elif myarg in ['relation', 'relations']:
      i += 1
      if checkClearBodyList(i, body, 'relations'):
        i += 1
        continue
      relation = {}
      i = getEntryType(i, relation, USER_RELATION_TYPES)
      relation['value'] = sys.argv[i]
      i += 1
      appendItemToBodyList(body, 'relations', relation)
    elif myarg in ['externalid', 'externalids']:
      i += 1
      if checkClearBodyList(i, body, 'externalIds'):
        i += 1
        continue
      externalid = {}
      i = getEntryType(i, externalid, USER_EXTERNALID_TYPES)
      externalid['value'] = sys.argv[i]
      i += 1
      appendItemToBodyList(body, 'externalIds', externalid)
    elif myarg in ['website', 'websites']:
      i += 1
      if checkClearBodyList(i, body, 'websites'):
        i += 1
        continue
      website = {}
      i = getEntryType(i, website, USER_WEBSITE_TYPES)
      website['value'] = sys.argv[i]
      i += 1
      myopt = sys.argv[i].lower()
      if myopt in ['notprimary', 'primary']:
        website['primary'] = myopt == 'primary'
        i += 1
      appendItemToBodyList(body, 'websites', website)
    elif myarg in ['note', 'notes']:
      i += 1
      if checkClearBodyList(i, body, 'notes'):
        i += 1
        continue
      note = {}
      if sys.argv[i].lower() in ['text_plain', 'text_html']:
        note['contentType'] = sys.argv[i].lower()
        i += 1
      if sys.argv[i].lower() == 'file':
        filename = sys.argv[i+1]
        i, encoding = getCharSet(i+2)
        note['value'] = readFile(filename, encoding=encoding)
      else:
        note['value'] = sys.argv[i].replace('\\n', '\n')
        i += 1
      body['notes'] = note
    elif myarg in ['location', 'locations']:
      i += 1
      if checkClearBodyList(i, body, 'locations'):
        i += 1
        continue
      location = {'type': 'desk', 'area': ''}
      while True:
        myopt = sys.argv[i].lower()
        if myopt == 'type':
          i = getEntryType(i+1, location, USER_LOCATION_TYPES)
        elif myopt == 'area':
          location['area'] = sys.argv[i+1]
          i += 2
        elif myopt in ['building', 'buildingid']:
          location['buildingId'] = _getBuildingByNameOrId(cd, sys.argv[i+1])
          i += 2
        elif myopt in ['desk', 'deskcode']:
          location['deskCode'] = sys.argv[i+1]
          i += 2
        elif myopt in ['floor', 'floorname']:
          location['floorName'] = sys.argv[i+1]
          i += 2
        elif myopt in ['section', 'floorsection']:
          location['floorSection'] = sys.argv[i+1]
          i += 2
        elif myopt in ['endlocation']:
          i += 1
          break
        else:
          systemErrorExit(3, '%s is not a valid argument for user location details. Make sure user location details end with an endlocation argument')
      appendItemToBodyList(body, 'locations', location)
    elif myarg in ['ssh', 'sshkeys', 'sshpublickeys']:
      i += 1
      if checkClearBodyList(i, body, 'sshPublicKeys'):
        i += 1
        continue
      ssh = {}
      while True:
        myopt = sys.argv[i].lower()
        if myopt == 'expires':
          ssh['expirationTimeUsec'] = getInteger(sys.argv[i+1], myopt, minVal=0)
          i += 2
        elif myopt == 'key':
          ssh['key'] = sys.argv[i+1]
          i += 2
        elif myopt in ['endssh']:
          i += 1
          break
        else:
          systemErrorExit(3, '%s is not a valid argument for user ssh details. Make sure user ssh details end with an endssh argument')
      appendItemToBodyList(body, 'sshPublicKeys', ssh)
    elif myarg in ['posix', 'posixaccounts']:
      i += 1
      if checkClearBodyList(i, body, 'posixAccounts'):
        i += 1
        continue
      posix = {}
      while True:
        myopt = sys.argv[i].lower()
        if myopt == 'gecos':
          posix['gecos'] = sys.argv[i+1]
          i += 2
        elif myopt == 'gid':
          posix['gid'] = getInteger(sys.argv[i+1], myopt, minVal=0)
          i += 2
        elif myopt == 'uid':
          posix['uid'] = getInteger(sys.argv[i+1], myopt, minVal=1000)
          i += 2
        elif myopt in ['home', 'homedirectory']:
          posix['homeDirectory'] = sys.argv[i+1]
          i += 2
        elif myopt in ['primary']:
          posix['primary'] = getBoolean(sys.argv[i+1], myopt)
          i += 2
        elif myopt in ['shell']:
          posix['shell'] = sys.argv[i+1]
          i += 2
        elif myopt in ['system', 'systemid']:
          posix['systemId'] = sys.argv[i+1]
          i += 2
        elif myopt in ['username', 'name']:
          posix['username'] = sys.argv[i+1]
          i += 2
        elif myopt in ['os', 'operatingsystemtype']:
          posix['operatingSystemType'] = sys.argv[i+1]
          i += 2
        elif myopt in ['endposix']:
          i += 1
          break
        else:
          systemErrorExit(3, '%s is not a valid argument for user posix details. Make sure user posix details end with an endposix argument')
      appendItemToBodyList(body, 'posixAccounts', posix, checkSystemId=True)
    elif myarg in ['keyword', 'keywords']:
      i += 1
      if checkClearBodyList(i, body, 'keywords'):
        i += 1
        continue
      keyword = {}
      i = getEntryType(i, keyword, USER_KEYWORD_TYPES)
      keyword['value'] = sys.argv[i]
      i += 1
      appendItemToBodyList(body, 'keywords', keyword)
    elif myarg == 'clearschema':
      if not updateCmd:
        systemErrorExit(2, '%s is not a valid create user argument.' % sys.argv[i])
      schemaName, fieldName = _splitSchemaNameDotFieldName(sys.argv[i+1], False)
      up = 'customSchemas'
      body.setdefault(up, {})
      body[up].setdefault(schemaName, {})
      if fieldName is None:
        schema = callGAPI(cd.schemas(), 'get',
                          soft_errors=True,
                          customerId=GC_Values[GC_CUSTOMER_ID], schemaKey=schemaName, fields='fields(fieldName)')
        if not schema:
          sys.exit(2)
        for field in schema['fields']:
          body[up][schemaName][field['fieldName']] = None
      else:
        body[up][schemaName][fieldName] = None
      i += 2
    elif myarg.find('.') >= 0:
      schemaName, fieldName = _splitSchemaNameDotFieldName(sys.argv[i])
      up = 'customSchemas'
      body.setdefault(up, {})
      body[up].setdefault(schemaName, {})
      i += 1
      multivalue = sys.argv[i].lower()
      if multivalue in ['multivalue', 'multivalued', 'value', 'multinonempty']:
        i += 1
        body[up][schemaName].setdefault(fieldName, [])
        schemaValue = {}
        if sys.argv[i].lower() == 'type':
          i += 1
          schemaValue['type'] = sys.argv[i].lower()
          if schemaValue['type'] not in ['custom', 'home', 'other', 'work']:
            systemErrorExit(2, 'wrong type must be one of custom, home, other, work; got %s' % schemaValue['type'])
          i += 1
          if schemaValue['type'] == 'custom':
            schemaValue['customType'] = sys.argv[i]
            i += 1
        schemaValue['value'] = sys.argv[i]
        if schemaValue['value'] or multivalue != 'multinonempty':
          body[up][schemaName][fieldName].append(schemaValue)
      else:
        body[up][schemaName][fieldName] = sys.argv[i]
      i += 1
    else:
      systemErrorExit(2, '%s is not a valid argument for "gam %s user"' % (sys.argv[i], ['create', 'update'][updateCmd]))
  if need_password:
    body['password'] = ''.join(random.sample('abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789~`!@#$%^&*()-=_+:;"\'{}[]\\|', 25))
  if 'password' in body and need_to_hash_password:
    body['password'] = gen_sha512_hash(body['password'])
    body['hashFunction'] = 'crypt'
  return body

def getCRMService(login_hint):
  scope = 'https://www.googleapis.com/auth/cloud-platform'
  client_id = '297408095146-fug707qsjv4ikron0hugpevbrjhkmsk7.apps.googleusercontent.com'
  client_secret = 'qM3dP8f_4qedwzWQE1VR4zzU'
  flow = oauth2client.client.OAuth2WebServerFlow(client_id=client_id,
                                                 client_secret=client_secret, scope=scope, redirect_uri=oauth2client.client.OOB_CALLBACK_URN,
                                                 user_agent=GAM_INFO, access_type='online', response_type='code', login_hint=login_hint)
  storage_dict = {}
  storage = DictionaryStorage(storage_dict, 'credentials')
  flags = cmd_flags(noLocalWebserver=GC_Values[GC_NO_BROWSER])
  http = httplib2.Http(disable_ssl_certificate_validation=GC_Values[GC_NO_VERIFY_SSL])
  credentials = oauth2client.tools.run_flow(flow=flow, storage=storage, flags=flags, http=http)
  credentials.user_agent = GAM_INFO
  http = credentials.authorize(httplib2.Http(disable_ssl_certificate_validation=GC_Values[GC_NO_VERIFY_SSL], cache=None))
  return (googleapiclient.discovery.build('cloudresourcemanager', 'v1',
                                          http=http, cache_discovery=False,
                                          discoveryServiceUrl=googleapiclient.discovery.V2_DISCOVERY_URI),
          http)

def getGAMProjectAPIs():
  httpObj = httplib2.Http(disable_ssl_certificate_validation=GC_Values[GC_NO_VERIFY_SSL])
  _, c = httpObj.request(GAM_PROJECT_APIS, 'GET')
  return httpObj, c.decode('utf-8').splitlines()

def enableGAMProjectAPIs(GAMProjectAPIs, httpObj, projectId, checkEnabled, i=0, count=0):
  apis = GAMProjectAPIs[:]
  project_name = 'project:{0}'.format(projectId)
  serveman = googleapiclient.discovery.build('servicemanagement', 'v1',
                                             http=httpObj, cache_discovery=False,
                                             discoveryServiceUrl=googleapiclient.discovery.V2_DISCOVERY_URI)
  status = True
  if checkEnabled:
    try:
      services = callGAPIpages(serveman.services(), 'list', 'services',
                               throw_reasons=[GAPI_NOT_FOUND],
                               consumerId=project_name, fields='nextPageToken,services(serviceName)')
      jcount = len(services)
      print('  Project: {0}, Check {1} APIs{2}'.format(projectId, jcount, currentCount(i, count)))
      j = 0
      for service in sorted(services, key=lambda k: k['serviceName']):
        j += 1
        if 'serviceName' in service:
          if service['serviceName'] in apis:
            print('    API: {0}, Already enabled{1}'.format(service['serviceName'], currentCount(j, jcount)))
            apis.remove(service['serviceName'])
          else:
            print('    API: {0}, Already enabled (non-GAM which is fine){1}'.format(service['serviceName'], currentCount(j, jcount)))
    except GAPI_notFound as e:
      print('  Project: {0}, Update Failed: {1}{2}'.format(projectId, str(e), currentCount(i, count)))
      status = False
  jcount = len(apis)
  if status and jcount > 0:
    print('  Project: {0}, Enable {1} APIs{2}'.format(projectId, jcount, currentCount(i, count)))
    j = 0
    for api in apis:
      j += 1
      while True:
        try:
          callGAPI(serveman.services(), 'enable',
                   throw_reasons=[GAPI_FAILED_PRECONDITION, GAPI_FORBIDDEN, GAPI_PERMISSION_DENIED],
                   serviceName=api, body={'consumerId': project_name})
          print('    API: {0}, Enabled{1}'.format(api, currentCount(j, jcount)))
          break
        except GAPI_failedPrecondition as e:
          print('\nThere was an error enabling %s. Please resolve error as described below:' % api)
          print()
          print('\n%s\n' % e)
          print()
          input('Press enter once resolved and we will try enabling the API again.')
        except (GAPI_forbidden, GAPI_permissionDenied) as e:
          print('    API: {0}, Enable Failed: {1}{2}'.format(api, str(e), currentCount(j, jcount)))
          status = False
  return status

def _createClientSecretsOauth2service(httpObj, projectId):

  def _checkClientAndSecret(simplehttp, client_id, client_secret):
    url = 'https://www.googleapis.com/oauth2/v4/token'
    post_data = {'client_id': client_id, 'client_secret': client_secret,
                 'code': 'ThisIsAnInvalidCodeOnlyBeingUsedToTestIfClientAndSecretAreValid',
                 'redirect_uri': 'urn:ietf:wg:oauth:2.0:oob', 'grant_type': 'authorization_code'}
    headers = {'Content-type': 'application/x-www-form-urlencoded'}
    _, content = simplehttp.request(url, 'POST', urlencode(post_data), headers=headers)
    try:
      content = json.loads(content)
    except ValueError:
      print('Unknown error: %s' % content)
      return False
    if not 'error' in content or not 'error_description' in content:
      print('Unknown error: %s' % content)
      return False
    if content['error'] == 'invalid_grant':
      return True
    if content['error_description'] == 'The OAuth client was not found.':
      print('Ooops!!\n\n%s\n\nIs not a valid client ID. Please make sure you are following the directions exactly and that there are no extra spaces in your client ID.' % client_id)
      return False
    if content['error_description'] == 'Unauthorized':
      print('Ooops!!\n\n%s\n\nIs not a valid client secret. Please make sure you are following the directions exactly and that there are no extra spaces in your client secret.' % client_secret)
      return False
    print('Unknown error: %s' % content)
    return False

  simplehttp, GAMProjectAPIs = getGAMProjectAPIs()
  enableGAMProjectAPIs(GAMProjectAPIs, httpObj, projectId, False)
  iam = googleapiclient.discovery.build('iam', 'v1',
                                        http=httpObj, cache_discovery=False,
                                        discoveryServiceUrl=googleapiclient.discovery.V2_DISCOVERY_URI)
  sa_list = callGAPI(iam.projects().serviceAccounts(), 'list',
                     name='projects/%s' % projectId)
  service_account = None
  if 'accounts' in sa_list:
    for account in sa_list['accounts']:
      sa_email = '%s@%s.iam.gserviceaccount.com' % (projectId, projectId)
      if sa_email in account['name']:
        service_account = account
        break
  if not service_account:
    print('Creating Service Account')
    service_account = callGAPI(iam.projects().serviceAccounts(), 'create',
                               name='projects/%s' % projectId,
                               body={'accountId': projectId, 'serviceAccount': {'displayName': 'GAM Project'}})
  key = callGAPI(iam.projects().serviceAccounts().keys(), 'create',
                 name=service_account['name'], body={'privateKeyType': 'TYPE_GOOGLE_CREDENTIALS_FILE', 'keyAlgorithm': 'KEY_ALG_RSA_2048'})
  oauth2service_data = base64.b64decode(key['privateKeyData']).decode('utf-8')
  writeFile(GC_Values[GC_OAUTH2SERVICE_JSON], oauth2service_data, continueOnError=False)
  console_credentials_url = 'https://console.developers.google.com/apis/credentials/consent?createClient&project=%s' % projectId
  while True:
    print('''Please go to:

%s

1. Enter "GAM" for "Application name".
2. Leave other fields blank. Click "Save" button.
3. Choose "Other". Enter a desired value for "Name". Click the blue "Create" button.
4. Copy your "client ID" value.

''' % console_credentials_url)
# If you use Firefox to copy the Client ID and Secret, the data has leading and trailing newlines
# The first raw_input will get the leading newline, thus we have to issue another raw_input to get the data
# If the newlines are not present, the data is correctly read with the first raw_input
    client_id = input('Enter your Client ID: ').strip()
    if not client_id:
      client_id = input().strip()
    print('\nNow go back to your browser and copy your client secret.')
    client_secret = input('Enter your Client Secret: ').strip()
    if not client_secret:
      client_secret = input().strip()
    client_valid = _checkClientAndSecret(simplehttp, client_id, client_secret)
    if client_valid:
      break
    print()
  cs_data = '''{
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
}''' % (client_id, client_secret, projectId)
  writeFile(GC_Values[GC_CLIENT_SECRETS_JSON], cs_data, continueOnError=False)
  print('''Almost there! Now please switch back to your browser and:

1. Click OK to close "OAuth client" popup if it's still open.
2. Click "Manage service accounts" on the right of the screen.
3. Click the 3 dots to the right of your service account.
4. Choose Edit.
5. Click "Show Domain-Wide Delegation". Check "Enable G Suite Domain-wide Delegation", Click Save.
''')
  input('Press Enter when done...')
  print('That\'s it! Your GAM Project is created and ready to use.')

VALIDEMAIL_PATTERN = re.compile(r'^[^@]+@[^@]+\.[^@]+$')

def _getValidateLoginHint(login_hint):
  while True:
    if not login_hint:
      login_hint = input('\nWhat is your G Suite admin email address? ').strip()
    if login_hint.find('@') == -1 and GC_Values[GC_DOMAIN]:
      login_hint = '{0}@{1}'.format(login_hint, GC_Values[GC_DOMAIN].lower())
    if VALIDEMAIL_PATTERN.match(login_hint):
      return login_hint
    print('{0}Invalid email address: {1}'.format(ERROR_PREFIX, login_hint))
    login_hint = None

def _getProjects(crm, pfilter):
  try:
    return callGAPIpages(crm.projects(), 'list', 'projects', throw_reasons=[GAPI_BAD_REQUEST], filter=pfilter)
  except GAPI_badRequest as e:
    systemErrorExit(2, 'Project: {0}, {1}'.format(pfilter, str(e)))

PROJECTID_PATTERN = re.compile(r'^[a-z][a-z0-9-]{4,28}[a-z0-9]$')
PROJECTID_FORMAT_REQUIRED = '[a-z][a-z0-9-]{4,28}[a-z0-9]'

def _getLoginHintProjectId(createCmd):
  login_hint = None
  projectId = None
  try:
    login_hint = sys.argv[3]
    projectId = sys.argv[4]
  except IndexError:
    pass
  login_hint = _getValidateLoginHint(login_hint)
  if projectId:
    if not PROJECTID_PATTERN.match(projectId):
      systemErrorExit(2, 'Invalid Project ID: {0}, expected <{1}>'.format(projectId, PROJECTID_FORMAT_REQUIRED))
  elif createCmd:
    projectId = 'gam-project'
    for _ in range(3):
      projectId += '-{0}'.format(''.join(random.choice(string.digits + string.ascii_lowercase) for _ in range(3)))
  else:
    projectId = input('\nWhat is your API project ID? ').strip()
    if not PROJECTID_PATTERN.match(projectId):
      systemErrorExit(2, 'Invalid Project ID: {0}, expected <{1}>'.format(projectId, PROJECTID_FORMAT_REQUIRED))
  crm, httpObj = getCRMService(login_hint)
  projects = _getProjects(crm, 'id:{0}'.format(projectId))
  if not createCmd:
    if not projects:
      systemErrorExit(2, 'User: {0}, Project ID: {1}, Does not exist'.format(login_hint, projectId))
    if projects[0]['lifecycleState'] != 'ACTIVE':
      systemErrorExit(2, 'User: {0}, Project ID: {1}, Not active'.format(login_hint, projectId))
  else:
    if projects:
      systemErrorExit(2, 'User: {0}, Project ID: {1}, Duplicate'.format(login_hint, projectId))
  return (crm, httpObj, login_hint, projectId)

PROJECTID_FILTER_REQUIRED = 'gam|<ProjectID>|(filter <String>)'

def _getLoginHintProjects(printShowCmd):
  login_hint = None
  pfilter = None
  i = 3
  try:
    login_hint = sys.argv[i]
    i += 1
    pfilter = sys.argv[i]
    i += 1
  except IndexError:
    pass
  if not pfilter:
    pfilter = 'current' if not printShowCmd else 'id:gam-project-*'
  elif printShowCmd and pfilter.lower() == 'all':
    pfilter = None
  elif pfilter.lower() == 'gam':
    pfilter = 'id:gam-project-*'
  elif pfilter.lower() == 'filter':
    pfilter = sys.argv[i]
    i += 1
  elif PROJECTID_PATTERN.match(pfilter):
    pfilter = 'id:{0}'.format(pfilter)
  else:
    systemErrorExit(2, 'Invalid Project ID: {0}, expected <{1}{2}>'.format(pfilter, ['', 'all|'][printShowCmd], PROJECTID_FILTER_REQUIRED))
  login_hint = _getValidateLoginHint(login_hint)
  crm, httpObj = getCRMService(login_hint)
  if pfilter == 'current':
    cs_data = readFile(GC_Values[GC_CLIENT_SECRETS_JSON], continueOnError=True, displayError=True, encoding=None)
    if not cs_data:
      systemErrorExit(14, 'Your client secrets file:\n\n%s\n\nis missing. Please recreate the file.' % GC_Values[GC_CLIENT_SECRETS_JSON])
    try:
      cs_json = json.loads(cs_data)
      projects = [{'projectId': cs_json['installed']['project_id']}]
    except (ValueError, IndexError, KeyError):
      systemErrorExit(3, 'The format of your client secrets file:\n\n%s\n\nis incorrect. Please recreate the file.' % GC_Values[GC_CLIENT_SECRETS_JSON])
  else:
    projects = _getProjects(crm, pfilter)
  return (crm, httpObj, login_hint, projects, i)

def _checkForExistingProjectFiles():
  for a_file in [GC_Values[GC_OAUTH2SERVICE_JSON], GC_Values[GC_CLIENT_SECRETS_JSON]]:
    if os.path.exists(a_file):
      systemErrorExit(5, '%s already exists. Please delete or rename it before attempting to use another project.' % a_file)

def doCreateProject():
  _checkForExistingProjectFiles()
  crm, httpObj, login_hint, projectId = _getLoginHintProjectId(True)
  login_domain = login_hint[login_hint.find('@')+1:]
  body = {'projectId': projectId, 'name': 'GAM Project'}
  while True:
    create_again = False
    print('Creating project "%s"...' % body['name'])
    create_operation = callGAPI(crm.projects(), 'create', body=body)
    operation_name = create_operation['name']
    time.sleep(8) # Google recommends always waiting at least 5 seconds
    for i in range(1, 5):
      print('Checking project status...')
      status = callGAPI(crm.operations(), 'get',
                        name=operation_name)
      if 'error' in status:
        if status['error'].get('message', '') == 'No permission to create project in organization':
          print('Hmm... Looks like you have no rights to your Google Cloud Organization.')
          print('Attempting to fix that...')
          getorg = callGAPI(crm.organizations(), 'search',
                            body={'filter': 'domain:%s' % login_domain})
          try:
            organization = getorg['organizations'][0]['name']
            print('Your organization name is %s' % organization)
          except (KeyError, IndexError):
            systemErrorExit(3, 'you have no rights to create projects for your organization and you don\'t seem to be a super admin! Sorry, there\'s nothing more I can do.')
          org_policy = callGAPI(crm.organizations(), 'getIamPolicy',
                                resource=organization, body={})
          if 'bindings' not in org_policy:
            org_policy['bindings'] = []
            print('Looks like no one has rights to your Google Cloud Organization. Attempting to give you create rights...')
          else:
            print('The following rights seem to exist:')
            for a_policy in org_policy['bindings']:
              if 'role' in a_policy:
                print(' Role: %s' % a_policy['role'])
              if 'members' in a_policy:
                print(' Members:')
                for member in a_policy['members']:
                  print('  %s' % member)
              print()
          my_role = 'roles/resourcemanager.projectCreator'
          print('Giving %s the role of %s...' % (login_hint, my_role))
          org_policy['bindings'].append({'role': my_role, 'members': ['user:%s' % login_hint]})
          callGAPI(crm.organizations(), 'setIamPolicy',
                   resource=organization, body={'policy': org_policy})
          create_again = True
          break
        try:
          if status['error']['details'][0]['violations'][0]['description'] == 'Callers must accept Terms of Service':
            print('''Please go to:

https://console.cloud.google.com/start

and accept the Terms of Service (ToS). As soon as you've accepted the ToS popup, you can return here and press enter.''')
            input()
            create_again = True
            break
        except (IndexError, KeyError):
          pass
        systemErrorExit(1, status)
      if status.get('done', False):
        break
      sleep_time = i ** 2
      print('Project still being created. Sleeping %s seconds' % sleep_time)
      time.sleep(sleep_time)
    if create_again:
      continue
    if not status.get('done', False):
      systemErrorExit(1, 'Failed to create project: %s' % status)
    elif 'error' in status:
      systemErrorExit(2, status['error'])
    break
  _createClientSecretsOauth2service(httpObj, projectId)

def doUseProject():
  _checkForExistingProjectFiles()
  _, httpObj, _, projectId = _getLoginHintProjectId(False)
  _createClientSecretsOauth2service(httpObj, projectId)

def doUpdateProjects():
  _, httpObj, login_hint, projects, _ = _getLoginHintProjects(False)
  _, GAMProjectAPIs = getGAMProjectAPIs()
  count = len(projects)
  print('User: {0}, Update {1} Projects'.format(login_hint, count))
  i = 0
  for project in projects:
    i += 1
    projectId = project['projectId']
    enableGAMProjectAPIs(GAMProjectAPIs, httpObj, projectId, True, i, count)

def doDelProjects():
  crm, _, login_hint, projects, _ = _getLoginHintProjects(False)
  count = len(projects)
  print('User: {0}, Delete {1} Projects'.format(login_hint, count))
  i = 0
  for project in projects:
    i += 1
    projectId = project['projectId']
    try:
      callGAPI(crm.projects(), 'delete', throw_reasons=[GAPI_FORBIDDEN], projectId=projectId)
      print('  Project: {0} Deleted{1}'.format(projectId, currentCount(i, count)))
    except GAPI_forbidden as e:
      print('  Project: {0} Delete Failed: {1}{2}'.format(projectId, str(e), currentCount(i, count)))


def doPrintShowProjects(csvFormat):
  _, _, login_hint, projects, i = _getLoginHintProjects(True)
  if csvFormat:
    csvRows = []
    todrive = False
    titles = ['User', 'projectId', 'projectNumber', 'name', 'createTime', 'lifecycleState']
  while i < len(sys.argv):
    myarg = sys.argv[i].lower()
    if csvFormat and myarg == 'todrive':
      todrive = True
      i += 1
    else:
      systemErrorExit(2, '%s is not a valid argument for "gam %s projects"' % (myarg, ['show', 'print'][csvFormat]))
  if not csvFormat:
    count = len(projects)
    print('User: {0}, Show {1} Projects'.format(login_hint, count))
    i = 0
    for project in projects:
      i += 1
      print('  Project: {0}{1}'.format(project['projectId'], currentCount(i, count)))
      print('    projectNumber: {0}'.format(project['projectNumber']))
      print('    name: {0}'.format(project['name']))
      print('    createTime: {0}'.format(project['createTime']))
      print('    lifecycleState: {0}'.format(project['lifecycleState']))
      jcount = len(project.get('labels', []))
      if jcount > 0:
        print('    labels:')
        for k, v in list(project['labels'].items()):
          print('      {0}: {1}'.format(k, v))
      if 'parent' in project:
        print('    parent:')
        print('      type: {0}'.format(project['parent']['type']))
        print('      id: {0}'.format(project['parent']['id']))
  else:
    for project in projects:
      addRowTitlesToCSVfile(flatten_json(project, flattened={'User': login_hint}), csvRows, titles)
    writeCSVfile(csvRows, titles, 'Projects', todrive)

def doGetTeamDriveInfo(users):
  teamDriveId = sys.argv[5]
  useDomainAdminAccess = False
  i = 6
  while i < len(sys.argv):
    myarg = sys.argv[i].lower().replace('_', '')
    if myarg == 'asadmin':
      useDomainAdminAccess = True
      i += 1
    else:
      systemErrorExit(3, '%s is not a valid command for "gam <users> show teamdrive"' % sys.argv[i])
  for user in users:
    drive = buildGAPIServiceObject('drive3', user)
    if not drive:
      print('Failed to access Drive as %s' % user)
      continue
    result = callGAPI(drive.teamdrives(), 'get', teamDriveId=teamDriveId,
                      useDomainAdminAccess=useDomainAdminAccess, fields='*')
    print_json(None, result)

def doCreateTeamDrive(users):
  body = {'name': sys.argv[5]}
  i = 6
  while i < len(sys.argv):
    myarg = sys.argv[i].lower()
    if myarg == 'theme':
      body['themeId'] = sys.argv[i+1]
      i += 2
    else:
      systemErrorExit(3, '%s is not a valid argument to "gam <users> create teamdrive"' % sys.argv[i])
  for user in users:
    drive = buildGAPIServiceObject('drive3', user)
    if not drive:
      print('Failed to access Drive as %s' % user)
      continue
    requestId = str(uuid.uuid4())
    result = callGAPI(drive.teamdrives(), 'create', requestId=requestId, body=body, fields='id')
    print('Created Team Drive %s with id %s' % (body['name'], result['id']))

TEAMDRIVE_RESTRICTIONS_MAP = {
  'adminmanagedrestrictions': 'adminManagedRestrictions',
  'copyrequireswriterpermission': 'copyRequiresWriterPermission',
  'domainusersonly': 'domainUsersOnly',
  'teammembersonly': 'teamMembersOnly',
  }

def doUpdateTeamDrive(users):
  teamDriveId = sys.argv[5]
  body = {}
  useDomainAdminAccess = False
  i = 6
  while i < len(sys.argv):
    myarg = sys.argv[i].lower().replace('_', '')
    if myarg == 'name':
      body['name'] = sys.argv[i+1]
      i += 2
    elif myarg == 'theme':
      body['themeId'] = sys.argv[i+1]
      i += 2
    elif myarg == 'customtheme':
      body['backgroundImageFile'] = {
        'id': sys.argv[i+1],
        'xCoordinate': float(sys.argv[i+2]),
        'yCoordinate': float(sys.argv[i+3]),
        'width': float(sys.argv[i+4])
        }
      i += 5
    elif myarg == 'color':
      body['colorRgb'] = getColor(sys.argv[i+1])
      i += 2
    elif myarg == 'asadmin':
      useDomainAdminAccess = True
      i += 1
    elif myarg in TEAMDRIVE_RESTRICTIONS_MAP:
      body.setdefault('restrictions', {})
      body['restrictions'][TEAMDRIVE_RESTRICTIONS_MAP[myarg]] = getBoolean(sys.argv[i+1], myarg)
      i += 2
    else:
      systemErrorExit(3, '%s is not a valid argument for "gam <users> update teamdrive"' % sys.argv[i])
  if not body:
    systemErrorExit(4, 'nothing to update. Need at least a name argument.')
  for user in users:
    user, drive = buildDrive3GAPIObject(user)
    if not drive:
      continue
    result = callGAPI(drive.teamdrives(), 'update',
                      useDomainAdminAccess=useDomainAdminAccess, body=body, teamDriveId=teamDriveId, fields='id', soft_errors=True)
    if not result:
      continue
    print('Updated Team Drive %s' % (teamDriveId))

def printShowTeamDrives(users, csvFormat):
  todrive = False
  useDomainAdminAccess = False
  q = None
  i = 5
  while i < len(sys.argv):
    myarg = sys.argv[i].lower().replace('_', '')
    if myarg == 'todrive':
      todrive = True
      i += 1
    elif myarg == 'asadmin':
      useDomainAdminAccess = True
      i += 1
    elif myarg == 'query':
      q = sys.argv[i+1]
      i += 2
    else:
      systemErrorExit(3, '%s is not a valid argument for "gam <users> print|show teamdrives"')
  tds = []
  for user in users:
    sys.stderr.write('Getting Team Drives for %s\n' % user)
    user, drive = buildDrive3GAPIObject(user)
    if not drive:
      continue
    results = callGAPIpages(drive.teamdrives(), 'list', 'teamDrives',
                            useDomainAdminAccess=useDomainAdminAccess, fields='*',
                            q=q, soft_errors=True)
    if not results:
      continue
    for td in results:
      if 'id' not in td:
        continue
      if 'name' not in td:
        td['name'] = '<Unknown Team Drive>'
      this_td = {'id': td['id'], 'name': td['name']}
      if this_td in tds:
        continue
      tds.append({'id': td['id'], 'name': td['name']})
  if csvFormat:
    titles = ['name', 'id']
    writeCSVfile(tds, titles, 'Team Drives', todrive)
  else:
    for td in tds:
      print('Name: %s  ID: %s' % (td['name'], td['id']))

def doDeleteTeamDrive(users):
  teamDriveId = sys.argv[5]
  for user in users:
    user, drive = buildDrive3GAPIObject(user)
    if not drive:
      continue
    print('Deleting Team Drive %s' % (teamDriveId))
    callGAPI(drive.teamdrives(), 'delete', teamDriveId=teamDriveId, soft_errors=True)

def validateCollaborators(collaboratorList, cd):
  collaborators = []
  for collaborator in collaboratorList.split(','):
    collaborator_id = convertEmailAddressToUID(collaborator, cd)
    if not collaborator_id:
      systemErrorExit(4, 'failed to get a UID for %s. Please make sure this is a real user.' % collaborator)
    collaborators.append({'email': collaborator, 'id': collaborator_id})
  return collaborators

def doCreateVaultMatter():
  v = buildGAPIObject('vault')
  body = {'name': 'New Matter - %s' % datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
  collaborators = []
  cd = None
  i = 3
  while i < len(sys.argv):
    myarg = sys.argv[i].lower().replace('_', '')
    if myarg == 'name':
      body['name'] = sys.argv[i+1]
      i += 2
    elif myarg == 'description':
      body['description'] = sys.argv[i+1]
      i += 2
    elif myarg in ['collaborator', 'collaborators']:
      if not cd:
        cd = buildGAPIObject('directory')
      collaborators.extend(validateCollaborators(sys.argv[i+1], cd))
      i += 2
    else:
      systemErrorExit(3, '%s is not a valid argument to "gam create matter"' % sys.argv[i])
  matterId = callGAPI(v.matters(), 'create', body=body, fields='matterId')['matterId']
  print('Created matter %s' % matterId)
  for collaborator in collaborators:
    print(' adding collaborator %s' % collaborator['email'])
    callGAPI(v.matters(), 'addPermissions', matterId=matterId, body={'matterPermission': {'role': 'COLLABORATOR', 'accountId': collaborator['id']}})

VAULT_SEARCH_METHODS_MAP = {
  'account': 'ACCOUNT',
  'accounts': 'ACCOUNT',
  'entireorg': 'ENTIRE_ORG',
  'everyone': 'ENTIRE_ORG',
  'orgunit': 'ORG_UNIT',
  'ou': 'ORG_UNIT',
  'room': 'ROOM',
  'rooms': 'ROOM',
  'teamdrive': 'TEAM_DRIVE',
  'teamdrives': 'TEAM_DRIVE',
  }
VAULT_SEARCH_METHODS_LIST = ['accounts', 'orgunit', 'teamdrives', 'rooms', 'everyone']

def doCreateVaultExport():
  v = buildGAPIObject('vault')
  allowed_corpuses = v._rootDesc['schemas']['Query']['properties']['corpus']['enum']
  try:
    allowed_corpuses.remove('CORPUS_TYPE_UNSPECIFIED')
  except ValueError:
    pass
  allowed_scopes = v._rootDesc['schemas']['Query']['properties']['dataScope']['enum']
  try:
    allowed_scopes.remove('DATA_SCOPE_UNSPECIFIED')
  except ValueError:
    pass
  allowed_formats = ['MBOX', 'PST']
  export_format = 'MBOX'
  matterId = None
  body = {'query': {'dataScope': 'ALL_DATA'}, 'exportOptions': {}}
  i = 3
  while i < len(sys.argv):
    myarg = sys.argv[i].lower().replace('_', '')
    if myarg == 'matter':
      matterId = getMatterItem(v, sys.argv[i+1])
      body['matterId'] = matterId
      i += 2
    elif myarg == 'name':
      body['name'] = sys.argv[i+1]
      i += 2
    elif myarg == 'corpus':
      body['query']['corpus'] = sys.argv[i+1].upper()
      if body['query']['corpus'] not in allowed_corpuses:
        systemErrorExit(3, 'corpus must be one of %s. Got %s' % (', '.join(allowed_corpuses), sys.argv[i+1]))
      i += 2
    elif myarg in VAULT_SEARCH_METHODS_MAP:
      if body['query'].get('searchMethod'):
        systemErrorExit(3, 'Multiple search methods ({0}) specified, only one is allowed'.format(', '.join(VAULT_SEARCH_METHODS_LIST)))
      searchMethod = VAULT_SEARCH_METHODS_MAP[myarg]
      body['query']['searchMethod'] = searchMethod
      if searchMethod == 'ACCOUNT':
        body['query']['accountInfo'] = {'emails': sys.argv[i+1].split(',')}
        i += 2
      elif searchMethod == 'ORG_UNIT':
        body['query']['orgUnitInfo'] = {'orgUnitId': getOrgUnitId(sys.argv[i+1])[1]}
        i += 2
      elif searchMethod == 'TEAM_DRIVE':
        body['query']['teamDriveInfo'] = {'teamDriveIds': sys.argv[i+1].split(',')}
        i += 2
      elif searchMethod == 'ROOM':
        body['query']['hangoutsChatInfo'] = {'roomId': sys.argv[i+1].split(',')}
        i += 2
      else:
        i += 1
    elif myarg == 'scope':
      body['query']['dataScope'] = sys.argv[i+1].upper()
      if body['query']['dataScope'] not in allowed_scopes:
        systemErrorExit(3, 'scope must be one of %s. Got %s' % (', '.join(allowed_scopes), sys.argv[i+1]))
      i += 2
    elif myarg in ['terms']:
      body['query']['terms'] = sys.argv[i+1]
      i += 2
    elif myarg in ['start', 'starttime']:
      body['query']['startTime'] = getDateZeroTimeOrFullTime(sys.argv[i+1])
      i += 2
    elif myarg in ['end', 'endtime']:
      body['query']['endTime'] = getDateZeroTimeOrFullTime(sys.argv[i+1])
      i += 2
    elif myarg in ['timezone']:
      body['query']['timeZone'] = sys.argv[i+1]
      i += 2
    elif myarg in ['excludedrafts']:
      body['query']['mailOptions'] = {'excludeDrafts': getBoolean(sys.argv[i+1], myarg)}
      i += 2
    elif myarg in ['driveversiondate']:
      body['query'].setdefault('driveOptions', {})['versionDate'] = getDateZeroTimeOrFullTime(sys.argv[i+1])
      i += 2
    elif myarg in ['includeteamdrives']:
      body['query'].setdefault('driveOptions', {})['includeTeamDrives'] = getBoolean(sys.argv[i+1], myarg)
      i += 2
    elif myarg in ['includerooms']:
      body['query']['hangoutsChatOptions'] = {'includeRooms': getBoolean(sys.argv[i+1], myarg)}
      i += 2
    elif myarg in ['format']:
      export_format = sys.argv[i+1].upper()
      if export_format not in allowed_formats:
        print('ERROR: export format can be one of %s, got %s' % (', '.join(allowed_formats), export_format))
        sys.exit(3)
      i += 2
    elif myarg in ['includeaccessinfo']:
      body['exportOptions'].setdefault('driveOptions', {})['includeAccessInfo'] = getBoolean(sys.argv[i+1], myarg)
      i += 2
    else:
      systemErrorExit(3, '%s is not a valid argument to "gam create export"' % sys.argv[i])
  if not matterId:
    systemErrorExit(3, 'you must specify a matter for the new export.')
  if 'corpus' not in body['query']:
    systemErrorExit(3, 'you must specify a corpus for the new export. Choose one of %s' % ', '.join(allowed_corpuses))
  if 'searchMethod' not in body['query']:
    systemErrorExit(3, 'you must specify a search method for the new export. Choose one of %s' % ', '.join(VAULT_SEARCH_METHODS_LIST))
  if 'name' not in body:
    body['name'] = 'GAM %s export - %s' % (body['query']['corpus'], datetime.datetime.now())
  options_field = None
  if body['query']['corpus'] == 'MAIL':
    options_field = 'mailOptions'
  elif body['query']['corpus'] == 'GROUPS':
    options_field = 'groupsOptions'
  elif body['query']['corpus'] == 'HANGOUTS_CHAT':
    options_field = 'hangoutsChatOptions'
  if options_field:
    body['exportOptions'].pop('driveOptions', None)
    body['exportOptions'][options_field] = {'exportFormat': export_format}
  results = callGAPI(v.matters().exports(), 'create', matterId=matterId, body=body)
  print('Created export %s' % results['id'])
  print_json(None, results)

def doDeleteVaultExport():
  v = buildGAPIObject('vault')
  matterId = getMatterItem(v, sys.argv[3])
  exportId = convertExportNameToID(v, sys.argv[4], matterId)
  print('Deleting export %s / %s' % (sys.argv[4], exportId))
  callGAPI(v.matters().exports(), 'delete', matterId=matterId, exportId=exportId)

def doGetVaultExportInfo():
  v = buildGAPIObject('vault')
  matterId = getMatterItem(v, sys.argv[3])
  exportId = convertExportNameToID(v, sys.argv[4], matterId)
  export = callGAPI(v.matters().exports(), 'get', matterId=matterId, exportId=exportId)
  print_json(None, export)

def doDownloadVaultExport():
  verifyFiles = True
  extractFiles = True
  v = buildGAPIObject('vault')
  s = buildGAPIObject('storage')
  matterId = getMatterItem(v, sys.argv[3])
  exportId = convertExportNameToID(v, sys.argv[4], matterId)
  targetFolder = GC_Values[GC_DRIVE_DIR]
  i = 5
  while i < len(sys.argv):
    myarg = sys.argv[i].lower().replace('_', '')
    if myarg == 'targetfolder':
      targetFolder = os.path.expanduser(sys.argv[i+1])
      if not os.path.isdir(targetFolder):
        os.makedirs(targetFolder)
      i += 2
    elif myarg == 'noverify':
      verifyFiles = False
      i += 1
    elif myarg == 'noextract':
      extractFiles = False
      i += 1
    else:
      systemErrorExit(3, '%s is not a valid argument to "gam download export"' % sys.argv[i])
  export = callGAPI(v.matters().exports(), 'get', matterId=matterId, exportId=exportId)
  for s_file in export['cloudStorageSink']['files']:
    bucket = s_file['bucketName']
    s_object = s_file['objectName']
    filename = os.path.join(targetFolder, s_object.replace('/', '-'))
    print('saving to %s' % filename)
    request = s.objects().get_media(bucket=bucket, object=s_object)
    f = openFile(filename, 'wb')
    downloader = googleapiclient.http.MediaIoBaseDownload(f, request)
    done = False
    while not done:
      status, done = downloader.next_chunk()
      sys.stdout.write(' Downloaded: {0:>7.2%}\r'.format(status.progress()))
      sys.stdout.flush()
    sys.stdout.write('\n Download complete. Flushing to disk...\n')
    # Necessary to make sure file is flushed by both Python and OS
    # https://stackoverflow.com/a/13762137/1503886
    f.flush()
    os.fsync(f.fileno())
    closeFile(f)
    f = openFile(filename, 'rb')
    if verifyFiles:
      expected_hash = s_file['md5Hash']
      sys.stdout.write(' Verifying file hash is %s...' % expected_hash)
      sys.stdout.flush()
      hash_md5 = hashlib.md5()
      for chunk in iter(lambda: f.read(4096), b""):
        hash_md5.update(chunk)
      actual_hash = hash_md5.hexdigest()
      if actual_hash == expected_hash:
        print('VERIFIED')
      else:
        print('ERROR: actual hash was %s. Exiting on corrupt file.' % actual_hash)
        sys.exit(6)
    closeFile(f)
    if extractFiles and re.search(r'\.zip$', filename):
      extract_nested_zip(filename, targetFolder)

def extract_nested_zip(zippedFile, toFolder, spacing=' '):
  """ Extract a zip file including any nested zip files
      Delete the zip file(s) after extraction
  """
  print('%sextracting %s' % (spacing, zippedFile))
  with zipfile.ZipFile(zippedFile, 'r') as zfile:
    inner_files = zfile.infolist()
    for inner_file in inner_files:
      print('%s %s' % (spacing, inner_file.filename))
      inner_file_path = zfile.extract(inner_file, toFolder)
      if re.search(r'\.zip$', inner_file.filename):
        extract_nested_zip(inner_file_path, toFolder, spacing=spacing+' ')
  os.remove(zippedFile)

def doCreateVaultHold():
  v = buildGAPIObject('vault')
  allowed_corpuses = v._rootDesc['schemas']['Hold']['properties']['corpus']['enum']
  body = {'query': {}}
  i = 3
  query = None
  start_time = None
  end_time = None
  matterId = None
  accounts = []
  while i < len(sys.argv):
    myarg = sys.argv[i].lower().replace('_', '')
    if myarg == 'name':
      body['name'] = sys.argv[i+1]
      i += 2
    elif myarg == 'query':
      query = sys.argv[i+1]
      i += 2
    elif myarg == 'corpus':
      body['corpus'] = sys.argv[i+1].upper()
      if body['corpus'] not in allowed_corpuses:
        systemErrorExit(3, 'corpus must be one of %s. Got %s' % (', '.join(allowed_corpuses), sys.argv[i+1]))
      i += 2
    elif myarg in ['accounts', 'users', 'groups']:
      accounts = sys.argv[i+1].split(',')
      i += 2
    elif myarg in ['orgunit', 'ou']:
      body['orgUnit'] = {'orgUnitId': getOrgUnitId(sys.argv[i+1])[1]}
      i += 2
    elif myarg in ['start', 'starttime']:
      start_time = getDateZeroTimeOrFullTime(sys.argv[i+1])
      i += 2
    elif myarg in ['end', 'endtime']:
      end_time = getDateZeroTimeOrFullTime(sys.argv[i+1])
      i += 2
    elif myarg == 'matter':
      matterId = getMatterItem(v, sys.argv[i+1])
      i += 2
    else:
      systemErrorExit(3, '%s is not a valid argument to "gam create hold"' % sys.argv[i])
  if not matterId:
    systemErrorExit(3, 'you must specify a matter for the new hold.')
  if not body.get('name'):
    systemErrorExit(3, 'you must specify a name for the new hold.')
  if not body.get('corpus'):
    systemErrorExit(3, 'you must specify a corpus for the new hold. Choose one of %s' % (', '.join(allowed_corpuses)))
  if body['corpus'] == 'HANGOUTS_CHAT':
    query_type = 'hangoutsChatQuery'
  else:
    query_type = '%sQuery' % body['corpus'].lower()
  body['query'][query_type] = {}
  if body['corpus'] == 'DRIVE':
    if query:
      try:
        body['query'][query_type] = json.loads(query)
      except ValueError as e:
        systemErrorExit(3, '{0}, query: {1}'.format(str(e), query))
  elif body['corpus'] in ['GROUPS', 'MAIL']:
    if query:
      body['query'][query_type] = {'terms': query}
    if start_time:
      body['query'][query_type]['startTime'] = start_time
    if end_time:
      body['query'][query_type]['endTime'] = end_time
  if accounts:
    body['accounts'] = []
    cd = buildGAPIObject('directory')
    account_type = 'group' if body['corpus'] == 'GROUPS' else 'user'
    for account in accounts:
      body['accounts'].append({'accountId': convertEmailAddressToUID(account, cd, account_type)})
  holdId = callGAPI(v.matters().holds(), 'create', matterId=matterId, body=body, fields='holdId')['holdId']
  print('Created hold %s' % holdId)

def doDeleteVaultHold():
  v = buildGAPIObject('vault')
  hold = sys.argv[3]
  matterId = None
  i = 4
  while i < len(sys.argv):
    myarg = sys.argv[i].lower().replace('_', '')
    if myarg == 'matter':
      matterId = getMatterItem(v, sys.argv[i+1])
      holdId = convertHoldNameToID(v, hold, matterId)
      i += 2
    else:
      systemErrorExit(3, '%s is not a valid argument to "gam delete hold"' % myarg)
  if not matterId:
    systemErrorExit(3, 'you must specify a matter for the hold.')
  print('Deleting hold %s / %s' % (hold, holdId))
  callGAPI(v.matters().holds(), 'delete', matterId=matterId, holdId=holdId)

def doGetVaultHoldInfo():
  v = buildGAPIObject('vault')
  hold = sys.argv[3]
  matterId = None
  i = 4
  while i < len(sys.argv):
    myarg = sys.argv[i].lower().replace('_', '')
    if myarg == 'matter':
      matterId = getMatterItem(v, sys.argv[i+1])
      holdId = convertHoldNameToID(v, hold, matterId)
      i += 2
    else:
      systemErrorExit(3, '%s is not a valid argument for "gam info hold"' % myarg)
  if not matterId:
    systemErrorExit(3, 'you must specify a matter for the hold.')
  results = callGAPI(v.matters().holds(), 'get', matterId=matterId, holdId=holdId)
  cd = buildGAPIObject('directory')
  if 'accounts' in results:
    account_type = 'group' if results['corpus'] == 'GROUPS' else 'user'
    for i in range(0, len(results['accounts'])):
      uid = 'uid:%s' % results['accounts'][i]['accountId']
      acct_email = convertUIDtoEmailAddress(uid, cd, account_type)
      results['accounts'][i]['email'] = acct_email
  if 'orgUnit' in results:
    results['orgUnit']['orgUnitPath'] = doGetOrgInfo(results['orgUnit']['orgUnitId'], return_attrib='orgUnitPath')
  print_json(None, results)

def convertExportNameToID(v, nameOrID, matterId):
  nameOrID = nameOrID.lower()
  cg = UID_PATTERN.match(nameOrID)
  if cg:
    return cg.group(1)
  exports = callGAPIpages(v.matters().exports(), 'list', 'exports', matterId=matterId, fields='exports(id,name),nextPageToken')
  for export in exports:
    if export['name'].lower() == nameOrID:
      return export['id']
  systemErrorExit(4, 'could not find export name %s in matter %s' % (nameOrID, matterId))

def convertHoldNameToID(v, nameOrID, matterId):
  nameOrID = nameOrID.lower()
  cg = UID_PATTERN.match(nameOrID)
  if cg:
    return cg.group(1)
  holds = callGAPIpages(v.matters().holds(), 'list', 'holds', matterId=matterId, fields='holds(holdId,name),nextPageToken')
  for hold in holds:
    if hold['name'].lower() == nameOrID:
      return hold['holdId']
  systemErrorExit(4, 'could not find hold name %s in matter %s' % (nameOrID, matterId))

def convertMatterNameToID(v, nameOrID):
  nameOrID = nameOrID.lower()
  cg = UID_PATTERN.match(nameOrID)
  if cg:
    return cg.group(1)
  matters = callGAPIpages(v.matters(), 'list', 'matters', view='BASIC', fields='matters(matterId,name),nextPageToken')
  for matter in matters:
    if matter['name'].lower() == nameOrID:
      return matter['matterId']
  return None

def getMatterItem(v, nameOrID):
  matterId = convertMatterNameToID(v, nameOrID)
  if not matterId:
    systemErrorExit(4, 'could not find matter %s' % nameOrID)
  return matterId

def doUpdateVaultHold():
  v = buildGAPIObject('vault')
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
    myarg = sys.argv[i].lower().replace('_', '')
    if myarg == 'matter':
      matterId = getMatterItem(v, sys.argv[i+1])
      holdId = convertHoldNameToID(v, hold, matterId)
      i += 2
    elif myarg == 'query':
      query = sys.argv[i+1]
      i += 2
    elif myarg in ['orgunit', 'ou']:
      body['orgUnit'] = {'orgUnitId': getOrgUnitId(sys.argv[i+1])[1]}
      i += 2
    elif myarg in ['start', 'starttime']:
      start_time = getDateZeroTimeOrFullTime(sys.argv[i+1])
      i += 2
    elif myarg in ['end', 'endtime']:
      end_time = getDateZeroTimeOrFullTime(sys.argv[i+1])
      i += 2
    elif myarg in ['addusers', 'addaccounts', 'addgroups']:
      add_accounts = sys.argv[i+1].split(',')
      i += 2
    elif myarg in ['removeusers', 'removeaccounts', 'removegroups']:
      del_accounts = sys.argv[i+1].split(',')
      i += 2
    else:
      systemErrorExit(3, '%s is not a valid argument to "gam update hold"' % myarg)
  if not matterId:
    systemErrorExit(3, 'you must specify a matter for the hold.')
  if query or start_time or end_time or body.get('orgUnit'):
    old_body = callGAPI(v.matters().holds(), 'get', matterId=matterId, holdId=holdId, fields='corpus,query,orgUnit')
    body['query'] = old_body['query']
    body['corpus'] = old_body['corpus']
    if 'orgUnit' in old_body and 'orgUnit' not in body:
      # bah, API requires this to be sent on update even when it's not changing
      body['orgUnit'] = old_body['orgUnit']
    query_type = '%sQuery' % body['corpus'].lower()
    if body['corpus'] == 'DRIVE':
      if query:
        try:
          body['query'][query_type] = json.loads(query)
        except ValueError as e:
          systemErrorExit(3, '{0}, query: {1}'.format(str(e), query))
    elif body['corpus'] in ['GROUPS', 'MAIL']:
      if query:
        body['query'][query_type]['terms'] = query
      if start_time:
        body['query'][query_type]['startTime'] = start_time
      if end_time:
        body['query'][query_type]['endTime'] = end_time
  if body:
    print('Updating hold %s / %s' % (hold, holdId))
    callGAPI(v.matters().holds(), 'update', matterId=matterId, holdId=holdId, body=body)
  if add_accounts or del_accounts:
    cd = buildGAPIObject('directory')
    for account in add_accounts:
      print('adding %s to hold.' % account)
      add_body = {'accountId': convertEmailAddressToUID(account, cd)}
      callGAPI(v.matters().holds().accounts(), 'create', matterId=matterId, holdId=holdId, body=add_body)
    for account in del_accounts:
      print('removing %s from hold.' % account)
      accountId = convertEmailAddressToUID(account, cd)
      callGAPI(v.matters().holds().accounts(), 'delete', matterId=matterId, holdId=holdId, accountId=accountId)

def doUpdateVaultMatter(action=None):
  v = buildGAPIObject('vault')
  matterId = getMatterItem(v, sys.argv[3])
  body = {}
  action_kwargs = {'body': {}}
  add_collaborators = []
  remove_collaborators = []
  cd = None
  i = 4
  while i < len(sys.argv):
    myarg = sys.argv[i].lower().replace('_', '')
    if myarg == 'action':
      action = sys.argv[i+1].lower()
      if action not in VAULT_MATTER_ACTIONS:
        systemErrorExit(3, 'allowed actions are %s, got %s' % (', '.join(VAULT_MATTER_ACTIONS), action))
      i += 2
    elif myarg == 'name':
      body['name'] = sys.argv[i+1]
      i += 2
    elif myarg == 'description':
      body['description'] = sys.argv[i+1]
      i += 2
    elif myarg in ['addcollaborator', 'addcollaborators']:
      if not cd:
        cd = buildGAPIObject('directory')
      add_collaborators.extend(validateCollaborators(sys.argv[i+1], cd))
      i += 2
    elif myarg in ['removecollaborator', 'removecollaborators']:
      if not cd:
        cd = buildGAPIObject('directory')
      remove_collaborators.extend(validateCollaborators(sys.argv[i+1], cd))
      i += 2
    else:
      systemErrorExit(3, '%s is not a valid argument for "gam update matter"' % sys.argv[i])
  if action == 'delete':
    action_kwargs = {}
  if body:
    print('Updating matter %s...' % sys.argv[3])
    if 'name' not in body or 'description' not in body:
      # bah, API requires name/description to be sent on update even when it's not changing
      result = callGAPI(v.matters(), 'get', matterId=matterId, view='BASIC')
      body.setdefault('name', result['name'])
      body.setdefault('description', result.get('description'))
    callGAPI(v.matters(), 'update', body=body, matterId=matterId)
  if action:
    print('Performing %s on matter %s' % (action, sys.argv[3]))
    callGAPI(v.matters(), action, matterId=matterId, **action_kwargs)
  for collaborator in add_collaborators:
    print(' adding collaborator %s' % collaborator['email'])
    callGAPI(v.matters(), 'addPermissions', matterId=matterId, body={'matterPermission': {'role': 'COLLABORATOR', 'accountId': collaborator['id']}})
  for collaborator in remove_collaborators:
    print(' removing collaborator %s' % collaborator['email'])
    callGAPI(v.matters(), 'removePermissions', matterId=matterId, body={'accountId': collaborator['id']})

def doGetVaultMatterInfo():
  v = buildGAPIObject('vault')
  matterId = getMatterItem(v, sys.argv[3])
  result = callGAPI(v.matters(), 'get', matterId=matterId, view='FULL')
  if 'matterPermissions' in result:
    cd = buildGAPIObject('directory')
    for i in range(0, len(result['matterPermissions'])):
      uid = 'uid:%s' % result['matterPermissions'][i]['accountId']
      user_email = convertUIDtoEmailAddress(uid, cd)
      result['matterPermissions'][i]['email'] = user_email
  print_json(None, result)

def doCreateUser():
  cd = buildGAPIObject('directory')
  body = getUserAttributes(3, cd, False)
  print("Creating account for %s" % body['primaryEmail'])
  callGAPI(cd.users(), 'insert', body=body, fields='primaryEmail')

def GroupIsAbuseOrPostmaster(emailAddr):
  return emailAddr.startswith('abuse@') or emailAddr.startswith('postmaster@')

def mapCollaborativeACL(myarg, value):
  value = value.lower().replace('_', '')
  if value in COLLABORATIVE_ACL_CHOICES:
    return COLLABORATIVE_ACL_CHOICES[value]
  systemErrorExit(3, 'allowed choices for %s are %s, got %s' % (myarg, ', '.join(sorted(COLLABORATIVE_ACL_CHOICES)), value))

def getGroupAttrValue(myarg, value, gs_object, gs_body, function):
  if myarg == 'collaborative':
    value = mapCollaborativeACL(myarg, value)
    for attrName, attrValue in list(COLLABORATIVE_INBOX_ATTRIBUTES.items()):
      if attrValue == 'acl':
        gs_body[attrName] = value
      else:
        gs_body[attrName] = attrValue
    return
  for (attrib, params) in list(gs_object['schemas']['Groups']['properties'].items()):
    if attrib in ['kind', 'etag', 'email']:
      continue
    if myarg == attrib.lower():
      if params['type'] == 'integer':
        try:
          if value[-1:].upper() == 'M':
            value = int(value[:-1]) * 1024 * 1024
          elif value[-1:].upper() == 'K':
            value = int(value[:-1]) * 1024
          elif value[-1].upper() == 'B':
            value = int(value[:-1])
          else:
            value = int(value)
        except ValueError:
          systemErrorExit(2, '%s must be a number ending with M (megabytes), K (kilobytes) or nothing (bytes); got %s' % value)
      elif params['type'] == 'string':
        if attrib == 'description':
          value = value.replace('\\n', '\n')
        elif attrib == 'primaryLanguage':
          value = LANGUAGE_CODES_MAP.get(value.lower(), value)
        elif COLLABORATIVE_INBOX_ATTRIBUTES.get(attrib) == 'acl':
          value = mapCollaborativeACL(myarg, value)
        elif params['description'].find(value.upper()) != -1: # ugly hack because API wants some values uppercased.
          value = value.upper()
        elif value.lower() in true_values:
          value = 'true'
        elif value.lower() in false_values:
          value = 'false'
      # Another ugly hack because Groups Settings API doesn't have proper enumerator values set in discovery file.
      if 'description' in params and params['description'].find('Possible values are: ') != -1:
        possible_values = params['description'][params['description'].find('Possible values are: ')+21:].split(' ')
        if value not in possible_values:
          systemErrorExit(2, 'value for %s must be one of %s. Got %s.' % (attrib, ', '.join(possible_values), value))
      gs_body[attrib] = value
      return
  systemErrorExit(2, '%s is not a valid argument for "gam %s group"' % (myarg, function))

def doCreateGroup():
  cd = buildGAPIObject('directory')
  body = {'email': normalizeEmailAddressOrUID(sys.argv[3], noUid=True)}
  gs_get_before_update = got_name = False
  i = 4
  gs_body = {}
  gs = None
  while i < len(sys.argv):
    myarg = sys.argv[i].lower().replace('_', '')
    if myarg == 'name':
      body['name'] = sys.argv[i+1]
      got_name = True
      i += 2
    elif myarg == 'description':
      description = sys.argv[i+1].replace('\\n', '\n')
# The Directory API Groups insert method can not handle any of these characters ('\n<>=') in the description field
# If any of these characters are present, use the Group Settings API to set the description
      for c in '\n<>=':
        if description.find(c) != -1:
          gs_body['description'] = description
          if not gs:
            gs = buildGAPIObject('groupssettings')
            gs_object = gs._rootDesc
          break
      else:
        body['description'] = description
      i += 2
    elif myarg == 'getbeforeupdate':
      gs_get_before_update = True
      i += 1
    else:
      if not gs:
        gs = buildGAPIObject('groupssettings')
        gs_object = gs._rootDesc
      getGroupAttrValue(myarg, sys.argv[i+1], gs_object, gs_body, 'create')
      i += 2
  if not got_name:
    body['name'] = body['email']
  print("Creating group %s" % body['email'])
  callGAPI(cd.groups(), 'insert', body=body, fields='email')
  if gs and not GroupIsAbuseOrPostmaster(body['email']):
    if gs_get_before_update:
      current_settings = callGAPI(gs.groups(), 'get',
                                  retry_reasons=['serviceLimit'],
                                  groupUniqueId=body['email'], fields='*')
      if current_settings is not None:
        gs_body = dict(list(current_settings.items()) + list(gs_body.items()))
    if gs_body:
      callGAPI(gs.groups(), 'update', retry_reasons=['serviceLimit'], groupUniqueId=body['email'], body=gs_body)

def doCreateAlias():
  cd = buildGAPIObject('directory')
  body = {'alias': normalizeEmailAddressOrUID(sys.argv[3], noUid=True, noLower=True)}
  target_type = sys.argv[4].lower()
  if target_type not in ['user', 'group', 'target']:
    systemErrorExit(2, 'type of target must be user or group; got %s' % target_type)
  targetKey = normalizeEmailAddressOrUID(sys.argv[5])
  print('Creating alias %s for %s %s' % (body['alias'], target_type, targetKey))
  if target_type == 'user':
    callGAPI(cd.users().aliases(), 'insert', userKey=targetKey, body=body)
  elif target_type == 'group':
    callGAPI(cd.groups().aliases(), 'insert', groupKey=targetKey, body=body)
  elif target_type == 'target':
    try:
      callGAPI(cd.users().aliases(), 'insert', throw_reasons=[GAPI_INVALID, GAPI_BAD_REQUEST], userKey=targetKey, body=body)
    except (GAPI_invalid, GAPI_badRequest):
      callGAPI(cd.groups().aliases(), 'insert', groupKey=targetKey, body=body)

def doCreateOrg():
  cd = buildGAPIObject('directory')
  name = getOrgUnitItem(sys.argv[3], pathOnly=True, absolutePath=False)
  parent = ''
  body = {}
  i = 4
  while i < len(sys.argv):
    myarg = sys.argv[i].lower()
    if myarg == 'description':
      body['description'] = sys.argv[i+1].replace('\\n', '\n')
      i += 2
    elif myarg == 'parent':
      parent = getOrgUnitItem(sys.argv[i+1])
      i += 2
    elif myarg == 'noinherit':
      body['blockInheritance'] = True
      i += 1
    elif myarg == 'inherit':
      body['blockInheritance'] = False
      i += 1
    else:
      systemErrorExit(2, '%s is not a valid argument for "gam create org"' % sys.argv[i])
  if parent.startswith('id:'):
    parent = callGAPI(cd.orgunits(), 'get',
                      customerId=GC_Values[GC_CUSTOMER_ID], orgUnitPath=parent, fields='orgUnitPath')['orgUnitPath']
  if parent == '/':
    orgUnitPath = parent+name
  else:
    orgUnitPath = parent+'/'+name
  if orgUnitPath.count('/') > 1:
    body['parentOrgUnitPath'], body['name'] = orgUnitPath.rsplit('/', 1)
  else:
    body['parentOrgUnitPath'] = '/'
    body['name'] = orgUnitPath[1:]
  parent = body['parentOrgUnitPath']
  callGAPI(cd.orgunits(), 'insert', customerId=GC_Values[GC_CUSTOMER_ID], body=body)

def _getBuildingAttributes(args, body={}):
  i = 0
  while i < len(args):
    myarg = args[i].lower().replace('_', '')
    if myarg == 'id':
      body['buildingId'] = args[i+1]
      i += 2
    elif myarg == 'name':
      body['buildingName'] = args[i+1]
      i += 2
    elif myarg in ['lat', 'latitude']:
      if 'coordinates' not in body:
        body['coordinates'] = {}
      body['coordinates']['latitude'] = args[i+1]
      i += 2
    elif myarg in ['long', 'lng', 'longitude']:
      if 'coordinates' not in body:
        body['coordinates'] = {}
      body['coordinates']['longitude'] = args[i+1]
      i += 2
    elif myarg == 'description':
      body['description'] = args[i+1]
      i += 2
    elif myarg == 'floors':
      body['floorNames'] = args[i+1].split(',')
      i += 2
    else:
      systemErrorExit(3, '%s is not a valid argument for "gam create|update building"' % myarg)
  return body

def doCreateBuilding():
  cd = buildGAPIObject('directory')
  body = {'floorNames': ['1'],
          'buildingId': str(uuid.uuid4()),
          'buildingName': sys.argv[3]}
  body = _getBuildingAttributes(sys.argv[4:], body)
  print('Creating building %s...' % body['buildingId'])
  callGAPI(cd.resources().buildings(), 'insert',
           customer=GC_Values[GC_CUSTOMER_ID], body=body)

def _makeBuildingIdNameMap(cd):
  buildings = callGAPIpages(cd.resources().buildings(), 'list', 'buildings',
                            customer=GC_Values[GC_CUSTOMER_ID],
                            fields='nextPageToken,buildings(buildingId,buildingName)')
  GM_Globals[GM_MAP_BUILDING_ID_TO_NAME] = {}
  GM_Globals[GM_MAP_BUILDING_NAME_TO_ID] = {}
  for building in buildings:
    GM_Globals[GM_MAP_BUILDING_ID_TO_NAME][building['buildingId']] = building['buildingName']
    GM_Globals[GM_MAP_BUILDING_NAME_TO_ID][building['buildingName']] = building['buildingId']

def _getBuildingByNameOrId(cd, which_building, minLen=1):
  if not which_building or (minLen == 0 and which_building in ['id:', 'uid:']):
    if minLen == 0:
      return ''
    systemErrorExit(3, 'Building id/name is empty')
  cg = UID_PATTERN.match(which_building)
  if cg:
    return cg.group(1)
  if GM_Globals[GM_MAP_BUILDING_NAME_TO_ID] is None:
    _makeBuildingIdNameMap(cd)
# Exact name match, return ID
  if which_building in GM_Globals[GM_MAP_BUILDING_NAME_TO_ID]:
    return GM_Globals[GM_MAP_BUILDING_NAME_TO_ID][which_building]
# No exact name match, check for case insensitive name matches
  which_building_lower = which_building.lower()
  ci_matches = []
  for buildingName, buildingId in GM_Globals[GM_MAP_BUILDING_NAME_TO_ID].items():
    if buildingName.lower() == which_building_lower:
      ci_matches.append({'buildingName': buildingName, 'buildingId': buildingId})
# One match, return ID
  if len(ci_matches) == 1:
    return ci_matches[0]['buildingId']
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
    message = 'Multiple buildings with same name:\n'
    for building in ci_matches:
      message += '  Name:%s  id:%s\n' % (building['buildingName'], building['buildingId'])
    message += '\nPlease specify building name by exact case or by id.'
    systemErrorExit(3, message)
# No matches
  else:
    systemErrorExit(3, 'No such building %s' % which_building)

def _getBuildingNameById(cd, buildingId):
  if GM_Globals[GM_MAP_BUILDING_ID_TO_NAME] is None:
    _makeBuildingIdNameMap(cd)
  return GM_Globals[GM_MAP_BUILDING_ID_TO_NAME].get(buildingId, 'UNKNOWN')

def doUpdateBuilding():
  cd = buildGAPIObject('directory')
  buildingId = _getBuildingByNameOrId(cd, sys.argv[3])
  body = _getBuildingAttributes(sys.argv[4:])
  print('Updating building %s...' % buildingId)
  callGAPI(cd.resources().buildings(), 'patch',
           customer=GC_Values[GC_CUSTOMER_ID], buildingId=buildingId, body=body)

def doGetBuildingInfo():
  cd = buildGAPIObject('directory')
  buildingId = _getBuildingByNameOrId(cd, sys.argv[3])
  building = callGAPI(cd.resources().buildings(), 'get',
                      customer=GC_Values[GC_CUSTOMER_ID], buildingId=buildingId)
  if 'buildingId' in building:
    building['buildingId'] = 'id:{0}'.format(building['buildingId'])
  if 'floorNames' in building:
    building['floorNames'] = ','.join(building['floorNames'])
  if 'buildingName' in building:
    sys.stdout.write(building.pop('buildingName'))
  print_json(None, building)

def doDeleteBuilding():
  cd = buildGAPIObject('directory')
  buildingId = _getBuildingByNameOrId(cd, sys.argv[3])
  print('Deleting building %s...' % buildingId)
  callGAPI(cd.resources().buildings(), 'delete',
           customer=GC_Values[GC_CUSTOMER_ID], buildingId=buildingId)

def _getFeatureAttributes(args, body={}):
  i = 0
  while i < len(args):
    myarg = args[i].lower().replace('_', '')
    if myarg == 'name':
      body['name'] = args[i+1]
      i += 2
    else:
      systemErrorExit(3, '%s is not a valid argument for "gam create|update feature"')
  return body

def doCreateFeature():
  cd = buildGAPIObject('directory')
  body = _getFeatureAttributes(sys.argv[3:])
  print('Creating feature %s...' % body['name'])
  callGAPI(cd.resources().features(), 'insert',
           customer=GC_Values[GC_CUSTOMER_ID], body=body)

def doUpdateFeature():
  # update does not work for name and name is only field to be updated
  # if additional writable fields are added to feature in the future
  # we'll add support for update as well as rename
  cd = buildGAPIObject('directory')
  oldName = sys.argv[3]
  body = {'newName': sys.argv[5:]}
  print('Updating feature %s...' % oldName)
  callGAPI(cd.resources().features(), 'rename',
           customer=GC_Values[GC_CUSTOMER_ID], oldName=oldName,
           body=body)

def doDeleteFeature():
  cd = buildGAPIObject('directory')
  featureKey = sys.argv[3]
  print('Deleting feature %s...' % featureKey)
  callGAPI(cd.resources().features(), 'delete',
           customer=GC_Values[GC_CUSTOMER_ID], featureKey=featureKey)

def _getResourceCalendarAttributes(cd, args, body={}):
  i = 0
  while i < len(args):
    myarg = args[i].lower().replace('_', '')
    if myarg == 'name':
      body['resourceName'] = args[i+1]
      i += 2
    elif myarg == 'description':
      body['resourceDescription'] = args[i+1].replace('\\n', '\n')
      i += 2
    elif myarg == 'type':
      body['resourceType'] = args[i+1]
      i += 2
    elif myarg in ['building', 'buildingid']:
      body['buildingId'] = _getBuildingByNameOrId(cd, args[i+1], minLen=0)
      i += 2
    elif myarg in ['capacity']:
      body['capacity'] = getInteger(args[i+1], myarg, minVal=0)
      i += 2
    elif myarg in ['feature', 'features']:
      features = args[i+1].split(',')
      body['featureInstances'] = []
      for feature in features:
        body['featureInstances'].append({'feature': {'name': feature}})
      i += 2
    elif myarg in ['floor', 'floorname']:
      body['floorName'] = args[i+1]
      i += 2
    elif myarg in ['floorsection']:
      body['floorSection'] = args[i+1]
      i += 2
    elif myarg in ['category']:
      body['resourceCategory'] = args[i+1].upper()
      if body['resourceCategory'] == 'ROOM':
        body['resourceCategory'] = 'CONFERENCE_ROOM'
      i += 2
    elif myarg in ['uservisibledescription', 'userdescription']:
      body['userVisibleDescription'] = args[i+1]
      i += 2
    else:
      systemErrorExit(2, '%s is not a valid argument for "gam create|update resource"' % args[i])
  return body

def doCreateResourceCalendar():
  cd = buildGAPIObject('directory')
  body = {'resourceId': sys.argv[3],
          'resourceName': sys.argv[4]}
  body = _getResourceCalendarAttributes(cd, sys.argv[5:], body)
  print('Creating resource %s...' % body['resourceId'])
  callGAPI(cd.resources().calendars(), 'insert',
           customer=GC_Values[GC_CUSTOMER_ID], body=body)

def doUpdateResourceCalendar():
  cd = buildGAPIObject('directory')
  resId = sys.argv[3]
  body = _getResourceCalendarAttributes(cd, sys.argv[4:])
  # Use patch since it seems to work better.
  # update requires name to be set.
  callGAPI(cd.resources().calendars(), 'patch',
           customer=GC_Values[GC_CUSTOMER_ID], calendarResourceId=resId, body=body,
           fields='')
  print('updated resource %s' % resId)

def doUpdateUser(users, i):
  cd = buildGAPIObject('directory')
  if users is None:
    users = [normalizeEmailAddressOrUID(sys.argv[3])]
  body = getUserAttributes(i, cd, True)
  vfe = 'primaryEmail' in body and body['primaryEmail'][:4].lower() == 'vfe@'
  for user in users:
    userKey = user
    if vfe:
      user_primary = callGAPI(cd.users(), 'get', userKey=userKey, fields='primaryEmail,id')
      userKey = user_primary['id']
      user_primary = user_primary['primaryEmail']
      user_name, user_domain = splitEmailAddress(user_primary)
      body['primaryEmail'] = 'vfe.%s.%05d@%s' % (user_name, random.randint(1, 99999), user_domain)
      body['emails'] = [{'type': 'custom', 'customType': 'former_employee', 'primary': False, 'address': user_primary}]
    sys.stdout.write('updating user %s...\n' % user)
    if body:
      callGAPI(cd.users(), 'update', userKey=userKey, body=body)

def doRemoveUsersAliases(users):
  cd = buildGAPIObject('directory')
  for user in users:
    user_aliases = callGAPI(cd.users(), 'get', userKey=user, fields='aliases,id,primaryEmail')
    user_id = user_aliases['id']
    user_primary = user_aliases['primaryEmail']
    if 'aliases' in user_aliases:
      print('%s has %s aliases' % (user_primary, len(user_aliases['aliases'])))
      for an_alias in user_aliases['aliases']:
        print(' removing alias %s for %s...' % (an_alias, user_primary))
        callGAPI(cd.users().aliases(), 'delete', userKey=user_id, alias=an_alias)
    else:
      print('%s has no aliases' % user_primary)

def deleteUserFromGroups(users):
  cd = buildGAPIObject('directory')
  for user in users:
    user_groups = callGAPIpages(cd.groups(), 'list', 'groups', userKey=user, fields='groups(id,email)')
    num_groups = len(user_groups)
    print('%s is in %s groups' % (user, num_groups))
    j = 0
    for user_group in user_groups:
      j += 1
      print(' removing %s from %s (%s/%s)' % (user, user_group['email'], j, num_groups))
      callGAPI(cd.members(), 'delete', soft_errors=True, groupKey=user_group['id'], memberKey=user)
    print('')

def checkGroupExists(cd, group, i=0, count=0):
  group = normalizeEmailAddressOrUID(group)
  try:
    return callGAPI(cd.groups(), 'get',
                    throw_reasons=GAPI_GROUP_GET_THROW_REASONS, retry_reasons=GAPI_GROUP_GET_RETRY_REASONS,
                    groupKey=group, fields='email')['email']
  except (GAPI_groupNotFound, GAPI_domainNotFound, GAPI_domainCannotUseApis, GAPI_forbidden, GAPI_badRequest):
    entityUnknownWarning('Group', group, i, count)
    return None

UPDATE_GROUP_SUBCMDS = ['add', 'clear', 'delete', 'remove', 'sync', 'update']
GROUP_ROLES_MAP = {
  'owner': ROLE_OWNER, 'owners': ROLE_OWNER,
  'manager': ROLE_MANAGER, 'managers': ROLE_MANAGER,
  'member': ROLE_MEMBER, 'members': ROLE_MEMBER,
  }
MEMBER_DELIVERY_MAP = {
  'allmail': 'ALL_MAIL', 'digest': 'DIGEST', 'daily': 'DAILY',
  'abridged': 'DAILY', 'nomail': 'NONE', 'none': 'NONE'
  }
def doUpdateGroup():

# Convert foo@googlemail.com to foo@gmail.com; eliminate periods in name for foo.bar@gmail.com
  def _cleanConsumerAddress(emailAddress, mapCleanToOriginal):
    atLoc = emailAddress.find('@')
    if atLoc > 0:
      if emailAddress[atLoc+1:] in ['gmail.com', 'googlemail.com']:
        cleanEmailAddress = emailAddress[:atLoc].replace('.', '')+'@gmail.com'
        if cleanEmailAddress != emailAddress:
          mapCleanToOriginal[cleanEmailAddress] = emailAddress
          return cleanEmailAddress
    return emailAddress

  def _getRoleAndUsers():
    checkSuspended = None
    role = None
    delivery = None
    i = 5
    if sys.argv[i].lower() in GROUP_ROLES_MAP:
      role = GROUP_ROLES_MAP[sys.argv[i].lower()]
      i += 1
    if sys.argv[i].lower() in ['suspended', 'notsuspended']:
      checkSuspended = sys.argv[i].lower() == 'suspended'
      i += 1
    if sys.argv[i].lower().replace('_', '') in MEMBER_DELIVERY_MAP:
      delivery = MEMBER_DELIVERY_MAP[sys.argv[i].lower()]
      i += 1
    if sys.argv[i].lower() in usergroup_types:
      users_email = getUsersToModify(entity_type=sys.argv[i].lower(), entity=sys.argv[i+1], checkSuspended=checkSuspended, groupUserMembersOnly=False)
    else:
      users_email = [normalizeEmailAddressOrUID(sys.argv[i], checkForCustomerId=True)]
    return (role, users_email, delivery)

  gs_get_before_update = False
  cd = buildGAPIObject('directory')
  group = sys.argv[3]
  myarg = sys.argv[4].lower()
  items = []
  if myarg in UPDATE_GROUP_SUBCMDS:
    group = normalizeEmailAddressOrUID(group)
    if myarg == 'add':
      role, users_email, delivery = _getRoleAndUsers()
      if not role:
        role = ROLE_MEMBER
      if not checkGroupExists(cd, group):
        return
      if len(users_email) > 1:
        sys.stderr.write('Group: {0}, Will add {1} {2}s.\n'.format(group, len(users_email), role))
        for user_email in users_email:
          item = ['gam', 'update', 'group', group, 'add', role]
          if delivery:
            item.append(delivery)
          item.append(user_email)
          items.append(item)
      else:
        body = {'role': role, 'email' if users_email[0].find('@') != -1 else 'id': users_email[0]}
        add_text = ['as %s' % role]
        if delivery:
          body['delivery_settings'] = delivery
          add_text.append('delivery %s' % delivery)
        for i in range(2):
          try:
            callGAPI(cd.members(), 'insert',
                     throw_reasons=[GAPI_DUPLICATE, GAPI_MEMBER_NOT_FOUND, GAPI_RESOURCE_NOT_FOUND, GAPI_INVALID_MEMBER, GAPI_CYCLIC_MEMBERSHIPS_NOT_ALLOWED],
                     groupKey=group, body=body)
            print(' Group: {0}, {1} Added {2}'.format(group, users_email[0], ' '.join(add_text)))
            break
          except GAPI_duplicate as e:
            # check if user is a full member, not pending
            try:
              result = callGAPI(cd.members(), 'get', throw_reasons=[GAPI_MEMBER_NOT_FOUND], memberKey=users_email[0], groupKey=group, fields='role')
              print(' Group: {0}, {1} Add {2} Failed: Duplicate, already a {3}'.format(group, users_email[0], ' '.join(add_text), result['role']))
              break # if get succeeds, user is a full member and we throw duplicate error
            except GAPI_memberNotFound:
              # insert fails on duplicate and get fails on not found, user is pending
              print(' Group: {0}, {1} member is pending, deleting and re-adding to solve...'.format(group, users_email[0]))
              callGAPI(cd.members(), 'delete', memberKey=users_email[0], groupKey=group)
              continue # 2nd insert should succeed now that pending is clear
          except (GAPI_memberNotFound, GAPI_resourceNotFound, GAPI_invalidMember, GAPI_cyclicMembershipsNotAllowed) as e:
            print(' Group: {0}, {1} Add {2} Failed: {3}'.format(group, users_email[0], ' '.join(add_text), str(e)))
            break
    elif myarg == 'sync':
      syncMembersSet = set()
      syncMembersMap = {}
      role, users_email, delivery = _getRoleAndUsers()
      for user_email in users_email:
        if user_email in ('*', GC_Values[GC_CUSTOMER_ID]):
          syncMembersSet.add(GC_Values[GC_CUSTOMER_ID])
        else:
          syncMembersSet.add(_cleanConsumerAddress(user_email.lower(), syncMembersMap))
      group = checkGroupExists(cd, group)
      if group:
        currentMembersSet = set()
        currentMembersMap = {}
        for current_email in getUsersToModify(entity_type='group', entity=group, member_type=role, groupUserMembersOnly=False):
          if current_email == GC_Values[GC_CUSTOMER_ID]:
            currentMembersSet.add(current_email)
          else:
            currentMembersSet.add(_cleanConsumerAddress(current_email.lower(), currentMembersMap))
# Compare incoming members and current memebers using the cleaned addresses; we actually add/remove with the original addresses
        to_add = [syncMembersMap.get(emailAddress, emailAddress) for emailAddress in syncMembersSet-currentMembersSet]
        to_remove = [currentMembersMap.get(emailAddress, emailAddress) for emailAddress in currentMembersSet-syncMembersSet]
        sys.stderr.write('Group: {0}, Will add {1} and remove {2} {3}s.\n'.format(group, len(to_add), len(to_remove), role))
        for user in to_add:
          item = ['gam', 'update', 'group', group, 'add']
          if role:
            item.append(role)
          if delivery:
            item.append(delivery)
          item.append(user)
          items.append(item)
        for user in to_remove:
          items.append(['gam', 'update', 'group', group, 'remove', user])
    elif myarg in ['delete', 'remove']:
      _, users_email, _ = _getRoleAndUsers()
      if not checkGroupExists(cd, group):
        return
      if len(users_email) > 1:
        sys.stderr.write('Group: {0}, Will remove {1} emails.\n'.format(group, len(users_email)))
        for user_email in users_email:
          items.append(['gam', 'update', 'group', group, 'remove', user_email])
      else:
        try:
          callGAPI(cd.members(), 'delete',
                   throw_reasons=[GAPI_MEMBER_NOT_FOUND, GAPI_INVALID_MEMBER],
                   groupKey=group, memberKey=users_email[0])
          print(' Group: {0}, {1} Removed'.format(group, users_email[0]))
        except (GAPI_memberNotFound, GAPI_invalidMember) as e:
          print(' Group: {0}, {1} Remove Failed: {2}'.format(group, users_email[0], str(e)))
    elif myarg == 'update':
      role, users_email, delivery = _getRoleAndUsers()
      group = checkGroupExists(cd, group)
      if group:
        if not role and not delivery:
          role = ROLE_MEMBER
        if len(users_email) > 1:
          sys.stderr.write('Group: {0}, Will update {1} {2}s.\n'.format(group, len(users_email), role))
          for user_email in users_email:
            item = ['gam', 'update', 'group', group, 'update']
            if role:
              item.append(role)
            if delivery:
              item.append(delivery)
            item.append(user_email)
            items.append(item)
        else:
          body = {}
          update_text = []
          if role:
            body['role'] = role
            update_text.append('to %s' % role)
          if delivery:
            body['delivery_settings'] = delivery
            update_text.append('delivery %s' % delivery)
          try:
            callGAPI(cd.members(), 'update',
                     throw_reasons=[GAPI_MEMBER_NOT_FOUND, GAPI_INVALID_MEMBER],
                     groupKey=group, memberKey=users_email[0], body=body)
            print(' Group: {0}, {1} Updated {2}'.format(group, users_email[0], ' '.join(update_text)))
          except (GAPI_memberNotFound, GAPI_invalidMember) as e:
            print(' Group: {0}, {1} Update to {2} Failed: {3}'.format(group, users_email[0], role, str(e)))
    else: # clear
      checkSuspended = None
      fields = ['email', 'id']
      roles = []
      i = 5
      while i < len(sys.argv):
        myarg = sys.argv[i].lower()
        if myarg.upper() in [ROLE_OWNER, ROLE_MANAGER, ROLE_MEMBER]:
          roles.append(myarg.upper())
          i += 1
        elif myarg in ['suspended', 'notsuspended']:
          checkSuspended = myarg == 'suspended'
          fields.append('status')
          i += 1
        else:
          systemErrorExit(2, '%s is not a valid argument for "gam update group clear"' % sys.argv[i])
      if roles:
        roles = ','.join(sorted(set(roles)))
      else:
        roles = ROLE_MEMBER
      group = normalizeEmailAddressOrUID(group)
      member_type_message = '%ss' % roles.lower()
      sys.stderr.write("Getting %s of %s (may take some time for large groups)...\n" % (member_type_message, group))
      page_message = 'Got %%%%total_items%%%% %s...' % member_type_message
      validRoles, listRoles, listFields = _getRoleVerification(roles, 'nextPageToken,members({0})'.format(','.join(fields)))
      try:
        result = callGAPIpages(cd.members(), 'list', 'members',
                               page_message=page_message,
                               throw_reasons=GAPI_MEMBERS_THROW_REASONS,
                               groupKey=group, roles=listRoles, fields=listFields, maxResults=GC_Values[GC_MEMBER_MAX_RESULTS])
        if not result:
          print('Group already has 0 members')
          return
        if checkSuspended is None:
          users_email = [member.get('email', member['id']) for member in result if not validRoles or member.get('role', ROLE_MEMBER) in validRoles]
        elif checkSuspended:
          users_email = [member.get('email', member['id']) for member in result if (not validRoles or member.get('role', ROLE_MEMBER) in validRoles) and member['status'] == 'SUSPENDED']
        else: # elif not checkSuspended
          users_email = [member.get('email', member['id']) for member in result if (not validRoles or member.get('role', ROLE_MEMBER) in validRoles) and member['status'] != 'SUSPENDED']
        if len(users_email) > 1:
          sys.stderr.write('Group: {0}, Will remove {1} {2}{3}s.\n'.format(group, len(users_email), '' if checkSuspended is None else ['Non-suspended ', 'Suspended '][checkSuspended], roles))
          for user_email in users_email:
            items.append(['gam', 'update', 'group', group, 'remove', user_email])
        else:
          try:
            callGAPI(cd.members(), 'delete',
                     throw_reasons=[GAPI_MEMBER_NOT_FOUND, GAPI_INVALID_MEMBER],
                     groupKey=group, memberKey=users_email[0])
            print(' Group: {0}, {1} Removed'.format(group, users_email[0]))
          except (GAPI_memberNotFound, GAPI_invalidMember) as e:
            print(' Group: {0}, {1} Remove Failed: {2}'.format(group, users_email[0], str(e)))
      except (GAPI_groupNotFound, GAPI_domainNotFound, GAPI_invalid, GAPI_forbidden):
        entityUnknownWarning('Group', group, 0, 0)
    if items:
      run_batch(items)
  else:
    i = 4
    use_cd_api = False
    gs = None
    gs_body = {}
    cd_body = {}
    while i < len(sys.argv):
      myarg = sys.argv[i].lower().replace('_', '')
      if myarg == 'email':
        use_cd_api = True
        cd_body['email'] = normalizeEmailAddressOrUID(sys.argv[i+1])
        i += 2
      elif myarg == 'admincreated':
        use_cd_api = True
        cd_body['adminCreated'] = getBoolean(sys.argv[i+1], myarg)
        i += 2
      elif myarg == 'getbeforeupdate':
        gs_get_before_update = True
        i += 1
      else:
        if not gs:
          gs = buildGAPIObject('groupssettings')
          gs_object = gs._rootDesc
        getGroupAttrValue(myarg, sys.argv[i+1], gs_object, gs_body, 'update')
        i += 2
    group = normalizeEmailAddressOrUID(group)
    if use_cd_api or (group.find('@') == -1): # group settings API won't take uid so we make sure cd API is used so that we can grab real email.
      group = callGAPI(cd.groups(), 'update', groupKey=group, body=cd_body, fields='email')['email']
    if gs:
      if not GroupIsAbuseOrPostmaster(group):
        if gs_get_before_update:
          current_settings = callGAPI(gs.groups(), 'get',
                                      retry_reasons=['serviceLimit'],
                                      groupUniqueId=group, fields='*')
          if current_settings is not None:
            gs_body = dict(list(current_settings.items()) + list(gs_body.items()))
        if gs_body:
          callGAPI(gs.groups(), 'update', retry_reasons=['serviceLimit'], groupUniqueId=group, body=gs_body)
    print('updated group %s' % group)

def doUpdateAlias():
  cd = buildGAPIObject('directory')
  alias = normalizeEmailAddressOrUID(sys.argv[3], noUid=True, noLower=True)
  target_type = sys.argv[4].lower()
  if target_type not in ['user', 'group', 'target']:
    systemErrorExit(2, 'target type must be one of user, group, target; got %s' % target_type)
  target_email = normalizeEmailAddressOrUID(sys.argv[5])
  try:
    callGAPI(cd.users().aliases(), 'delete', throw_reasons=[GAPI_INVALID], userKey=alias, alias=alias)
  except GAPI_invalid:
    callGAPI(cd.groups().aliases(), 'delete', groupKey=alias, alias=alias)
  if target_type == 'user':
    callGAPI(cd.users().aliases(), 'insert', userKey=target_email, body={'alias': alias})
  elif target_type == 'group':
    callGAPI(cd.groups().aliases(), 'insert', groupKey=target_email, body={'alias': alias})
  elif target_type == 'target':
    try:
      callGAPI(cd.users().aliases(), 'insert', throw_reasons=[GAPI_INVALID], userKey=target_email, body={'alias': alias})
    except GAPI_invalid:
      callGAPI(cd.groups().aliases(), 'insert', groupKey=target_email, body={'alias': alias})
  print('updated alias %s' % alias)

def getCrOSDeviceEntity(i, cd):
  myarg = sys.argv[i].lower()
  if myarg == 'cros_sn':
    return i+2, getUsersToModify('cros_sn', sys.argv[i+1])
  if myarg == 'query':
    return i+2, getUsersToModify('crosquery', sys.argv[i+1])
  if myarg[:6] == 'query:':
    query = sys.argv[i][6:]
    if query[:12].lower() == 'orgunitpath:':
      kwargs = {'orgUnitPath': query[12:]}
    else:
      kwargs = {'query': query}
    devices = callGAPIpages(cd.chromeosdevices(), 'list', 'chromeosdevices',
                            customerId=GC_Values[GC_CUSTOMER_ID],
                            fields='nextPageToken,chromeosdevices(deviceId)', **kwargs)
    return i+1, [device['deviceId'] for device in devices]
  return i+1, sys.argv[i].replace(',', ' ').split()

def doUpdateCros():
  cd = buildGAPIObject('directory')
  i, devices = getCrOSDeviceEntity(3, cd)
  update_body = {}
  action_body = {}
  orgUnitPath = None
  ack_wipe = False
  while i < len(sys.argv):
    myarg = sys.argv[i].lower().replace('_', '')
    if myarg == 'user':
      update_body['annotatedUser'] = sys.argv[i+1]
      i += 2
    elif myarg == 'location':
      update_body['annotatedLocation'] = sys.argv[i+1]
      i += 2
    elif myarg == 'notes':
      update_body['notes'] = sys.argv[i+1].replace('\\n', '\n')
      i += 2
    elif myarg in ['tag', 'asset', 'assetid']:
      update_body['annotatedAssetId'] = sys.argv[i+1]
      i += 2
    elif myarg in ['ou', 'org']:
      orgUnitPath = getOrgUnitItem(sys.argv[i+1])
      i += 2
    elif myarg == 'action':
      action = sys.argv[i+1].lower().replace('_', '').replace('-', '')
      deprovisionReason = None
      if action in ['deprovisionsamemodelreplace', 'deprovisionsamemodelreplacement']:
        action = 'deprovision'
        deprovisionReason = 'same_model_replacement'
      elif action in ['deprovisiondifferentmodelreplace', 'deprovisiondifferentmodelreplacement']:
        action = 'deprovision'
        deprovisionReason = 'different_model_replacement'
      elif action in ['deprovisionretiringdevice']:
        action = 'deprovision'
        deprovisionReason = 'retiring_device'
      elif action not in ['disable', 'reenable']:
        systemErrorExit(2, 'expected action of deprovision_same_model_replace, deprovision_different_model_replace, deprovision_retiring_device, disable or reenable, got %s' % action)
      action_body = {'action': action}
      if deprovisionReason:
        action_body['deprovisionReason'] = deprovisionReason
      i += 2
    elif myarg == 'acknowledgedevicetouchrequirement':
      ack_wipe = True
      i += 1
    else:
      systemErrorExit(2, '%s is not a valid argument for "gam update cros"' % sys.argv[i])
  i = 0
  count = len(devices)
  if action_body:
    if action_body['action'] == 'deprovision' and not ack_wipe:
      print('WARNING: Refusing to deprovision %s devices because acknowledge_device_touch_requirement not specified. Deprovisioning a device means the device will have to be physically wiped and re-enrolled to be managed by your domain again. This requires physical access to the device and is very time consuming to perform for each device. Please add "acknowledge_device_touch_requirement" to the GAM command if you understand this and wish to proceed with the deprovision. Please also be aware that deprovisioning can have an effect on your device license count. See https://support.google.com/chrome/a/answer/3523633 for full details.' % (count))
      sys.exit(3)
    for deviceId in devices:
      i += 1
      print(' performing action %s for %s (%s of %s)' % (action, deviceId, i, count))
      callGAPI(cd.chromeosdevices(), function='action', customerId=GC_Values[GC_CUSTOMER_ID], resourceId=deviceId, body=action_body)
  else:
    if update_body:
      for deviceId in devices:
        i += 1
        print(' updating %s (%s of %s)' % (deviceId, i, count))
        callGAPI(service=cd.chromeosdevices(), function='update', customerId=GC_Values[GC_CUSTOMER_ID], deviceId=deviceId, body=update_body)
    if orgUnitPath:
      #move_body[u'deviceIds'] = devices
      # split moves into max 50 devices per batch
      for l in range(0, len(devices), 50):
        move_body = {'deviceIds': devices[l:l+50]}
        print(' moving %s devices to %s' % (len(move_body['deviceIds']), orgUnitPath))
        callGAPI(cd.chromeosdevices(), 'moveDevicesToOu', customerId=GC_Values[GC_CUSTOMER_ID], orgUnitPath=orgUnitPath, body=move_body)

def doUpdateMobile():
  cd = buildGAPIObject('directory')
  resourceId = sys.argv[3]
  i = 4
  body = {}
  while i < len(sys.argv):
    myarg = sys.argv[i].lower()
    if myarg == 'action':
      body['action'] = sys.argv[i+1].lower()
      if body['action'] == 'wipe':
        body['action'] = 'admin_remote_wipe'
      elif body['action'].replace('_', '') in ['accountwipe', 'wipeaccount']:
        body['action'] = 'admin_account_wipe'
      if body['action'] not in ['admin_remote_wipe', 'admin_account_wipe', 'approve', 'block', 'cancel_remote_wipe_then_activate', 'cancel_remote_wipe_then_block']:
        systemErrorExit(2, 'action must be one of wipe, wipeaccount, approve, block, cancel_remote_wipe_then_activate, cancel_remote_wipe_then_block; got %s' % body['action'])
      i += 2
    else:
      systemErrorExit(2, '%s is not a valid argument for "gam update mobile"' % sys.argv[i])
  if body:
    callGAPI(cd.mobiledevices(), 'action', resourceId=resourceId, body=body, customerId=GC_Values[GC_CUSTOMER_ID])

def doDeleteMobile():
  cd = buildGAPIObject('directory')
  resourceId = sys.argv[3]
  callGAPI(cd.mobiledevices(), 'delete', resourceId=resourceId, customerId=GC_Values[GC_CUSTOMER_ID])

def doUpdateOrg():
  cd = buildGAPIObject('directory')
  orgUnitPath = getOrgUnitItem(sys.argv[3])
  if sys.argv[4].lower() in ['move', 'add']:
    entity_type = sys.argv[5].lower()
    if entity_type in usergroup_types:
      users = getUsersToModify(entity_type=entity_type, entity=sys.argv[6])
    else:
      entity_type = 'users'
      users = getUsersToModify(entity_type=entity_type, entity=sys.argv[5])
    if (entity_type.startswith('cros')) or ((entity_type == 'all') and (sys.argv[6].lower() == 'cros')):
      for l in range(0, len(users), 50):
        move_body = {'deviceIds': users[l:l+50]}
        print(' moving %s devices to %s' % (len(move_body['deviceIds']), orgUnitPath))
        callGAPI(cd.chromeosdevices(), 'moveDevicesToOu', customerId=GC_Values[GC_CUSTOMER_ID], orgUnitPath=orgUnitPath, body=move_body)
    else:
      current_user = 0
      user_count = len(users)
      for user in users:
        current_user += 1
        sys.stderr.write(' moving %s to %s (%s/%s)\n' % (user, orgUnitPath, current_user, user_count))
        try:
          callGAPI(cd.users(), 'update', throw_reasons=[GAPI_CONDITION_NOT_MET], userKey=user, body={'orgUnitPath': orgUnitPath})
        except GAPI_conditionNotMet:
          pass
  else:
    body = {}
    i = 4
    while i < len(sys.argv):
      myarg = sys.argv[i].lower()
      if myarg == 'name':
        body['name'] = sys.argv[i+1]
        i += 2
      elif myarg == 'description':
        body['description'] = sys.argv[i+1].replace('\\n', '\n')
        i += 2
      elif myarg == 'parent':
        parent = getOrgUnitItem(sys.argv[i+1])
        if parent.startswith('id:'):
          body['parentOrgUnitId'] = parent
        else:
          body['parentOrgUnitPath'] = parent
        i += 2
      elif myarg == 'noinherit':
        body['blockInheritance'] = True
        i += 1
      elif myarg == 'inherit':
        body['blockInheritance'] = False
        i += 1
      else:
        systemErrorExit(2, '%s is not a valid argument for "gam update org"' % sys.argv[i])
    callGAPI(cd.orgunits(), 'update', customerId=GC_Values[GC_CUSTOMER_ID], orgUnitPath=encodeOrgUnitPath(makeOrgUnitPathRelative(orgUnitPath)), body=body)

def doWhatIs():
  cd = buildGAPIObject('directory')
  email = normalizeEmailAddressOrUID(sys.argv[2])
  try:
    user_or_alias = callGAPI(cd.users(), 'get', throw_reasons=[GAPI_NOT_FOUND, GAPI_BAD_REQUEST, GAPI_INVALID], userKey=email, fields='id,primaryEmail')
    if (user_or_alias['primaryEmail'].lower() == email) or (user_or_alias['id'] == email):
      sys.stderr.write('%s is a user\n\n' % email)
      doGetUserInfo(user_email=email)
      return
    sys.stderr.write('%s is a user alias\n\n' % email)
    doGetAliasInfo(alias_email=email)
    return
  except (GAPI_notFound, GAPI_badRequest, GAPI_invalid):
    sys.stderr.write('%s is not a user...\n' % email)
    sys.stderr.write('%s is not a user alias...\n' % email)
  try:
    group = callGAPI(cd.groups(), 'get', throw_reasons=[GAPI_NOT_FOUND, GAPI_BAD_REQUEST], groupKey=email, fields='id,email')
  except (GAPI_notFound, GAPI_badRequest):
    systemErrorExit(1, '%s is not a group either!\n\nDoesn\'t seem to exist!\n\n' % email)
  if (group['email'].lower() == email) or (group['id'] == email):
    sys.stderr.write('%s is a group\n\n' % email)
    doGetGroupInfo(group_name=email)
  else:
    sys.stderr.write('%s is a group alias\n\n' % email)
    doGetAliasInfo(alias_email=email)

def convertSKU2ProductId(res, sku, customerId):
  results = callGAPI(res.subscriptions(), 'list', customerId=customerId)
  for subscription in results['subscriptions']:
    if sku == subscription['skuId']:
      return subscription['subscriptionId']
  systemErrorExit(3, 'could not find subscription for customer %s and SKU %s' % (customerId, sku))

def doDeleteResoldSubscription():
  res = buildGAPIObject('reseller')
  customerId = sys.argv[3]
  sku = sys.argv[4]
  deletionType = sys.argv[5]
  subscriptionId = convertSKU2ProductId(res, sku, customerId)
  callGAPI(res.subscriptions(), 'delete', customerId=customerId, subscriptionId=subscriptionId, deletionType=deletionType)
  print('Cancelled %s for %s' % (sku, customerId))

def doCreateResoldSubscription():
  res = buildGAPIObject('reseller')
  customerId = sys.argv[3]
  customerAuthToken, body = _getResoldSubscriptionAttr(sys.argv[4:], customerId)
  result = callGAPI(res.subscriptions(), 'insert', customerId=customerId, customerAuthToken=customerAuthToken, body=body, fields='customerId')
  print('Created subscription:')
  print_json(None, result)

def doUpdateResoldSubscription():
  res = buildGAPIObject('reseller')
  function = None
  customerId = sys.argv[3]
  sku = sys.argv[4]
  subscriptionId = convertSKU2ProductId(res, sku, customerId)
  kwargs = {}
  i = 5
  while i < len(sys.argv):
    myarg = sys.argv[i].lower()
    if myarg == 'activate':
      function = 'activate'
      i += 1
    elif myarg == 'suspend':
      function = 'suspend'
      i += 1
    elif myarg == 'startpaidservice':
      function = 'startPaidService'
      i += 1
    elif myarg in ['renewal', 'renewaltype']:
      function = 'changeRenewalSettings'
      kwargs['body'] = {'renewalType': sys.argv[i+1].upper()}
      i += 2
    elif myarg in ['seats']:
      function = 'changeSeats'
      kwargs['body'] = {'numberOfSeats': getInteger(sys.argv[i+1], 'numberOfSeats', minVal=0)}
      if len(sys.argv) > i + 2 and sys.argv[i+2].isdigit():
        kwargs['body']['maximumNumberOfSeats'] = getInteger(sys.argv[i+2], 'maximumNumberOfSeats', minVal=0)
        i += 3
      else:
        i += 2
    elif myarg in ['plan']:
      function = 'changePlan'
      kwargs['body'] = {'planName': sys.argv[i+1].upper()}
      i += 2
      while i < len(sys.argv):
        planarg = sys.argv[i].lower()
        if planarg == 'seats':
          kwargs['body']['seats'] = {'numberOfSeats': getInteger(sys.argv[i+1], 'numberOfSeats', minVal=0)}
          if len(sys.argv) > i + 2 and sys.argv[i+2].isdigit():
            kwargs['body']['seats']['maximumNumberOfSeats'] = getInteger(sys.argv[i+2], 'maximumNumberOfSeats', minVal=0)
            i += 3
          else:
            i += 2
        elif planarg in ['purchaseorderid', 'po']:
          kwargs['body']['purchaseOrderId'] = sys.argv[i+1]
          i += 2
        elif planarg in ['dealcode', 'deal']:
          kwargs['body']['dealCode'] = sys.argv[i+1]
          i += 2
        else:
          systemErrorExit(3, '%s is not a valid argument to "gam update resoldsubscription plan"' % planarg)
    else:
      systemErrorExit(3, '%s is not a valid argument to "gam update resoldsubscription"' % myarg)
  result = callGAPI(res.subscriptions(), function, customerId=customerId, subscriptionId=subscriptionId, **kwargs)
  print('Updated %s SKU %s subscription:' % (customerId, sku))
  if result:
    print_json(None, result)

def doGetResoldSubscriptions():
  res = buildGAPIObject('reseller')
  customerId = sys.argv[3]
  customerAuthToken = None
  i = 4
  while i < len(sys.argv):
    myarg = sys.argv[i].lower().replace('_', '')
    if myarg in ['customerauthtoken', 'transfertoken']:
      customerAuthToken = sys.argv[i+1]
      i += 2
    else:
      systemErrorExit(3, '%s is not a valid argument for "gam info resoldsubscriptions"' % myarg)
  result = callGAPI(res.subscriptions(), 'list', customerId=customerId, customerAuthToken=customerAuthToken)
  print_json(None, result)

def _getResoldSubscriptionAttr(arg, customerId):
  body = {'plan': {},
          'seats': {},
          'customerId': customerId}
  customerAuthToken = None
  i = 0
  while i < len(arg):
    myarg = arg[i].lower().replace('_', '')
    if myarg in ['deal', 'dealcode']:
      body['dealCode'] = arg[i+1]
    elif myarg in ['plan', 'planname']:
      body['plan']['planName'] = arg[i+1].upper()
    elif myarg in ['purchaseorderid', 'po']:
      body['purchaseOrderId'] = arg[i+1]
    elif myarg in ['seats']:
      body['seats']['numberOfSeats'] = getInteger(sys.argv[i+1], 'numberOfSeats', minVal=0)
      if len(arg) > i + 2 and arg[i+2].isdigit():
        body['seats']['maximumNumberOfSeats'] = getInteger(sys.argv[i+2], 'maximumNumberOfSeats', minVal=0)
        i += 1
    elif myarg in ['sku', 'skuid']:
      _, body['skuId'] = getProductAndSKU(arg[i+1])
    elif myarg in ['customerauthtoken', 'transfertoken']:
      customerAuthToken = arg[i+1]
    else:
      systemErrorExit(3, '%s is not a valid argument for "gam create resoldsubscription"' % myarg)
    i += 2
  return customerAuthToken, body

def doGetResoldCustomer():
  res = buildGAPIObject('reseller')
  customerId = sys.argv[3]
  result = callGAPI(res.customers(), 'get', customerId=customerId)
  print_json(None, result)

def _getResoldCustomerAttr(arg):
  body = {}
  customerAuthToken = None
  i = 0
  while i < len(arg):
    myarg = arg[i].lower().replace('_', '')
    if myarg in ADDRESS_FIELDS_ARGUMENT_MAP:
      body.setdefault('postalAddress', {})
      body['postalAddress'][ADDRESS_FIELDS_ARGUMENT_MAP[myarg]] = arg[i+1]
    elif myarg in ['email', 'alternateemail']:
      body['alternateEmail'] = arg[i+1]
    elif myarg in ['phone', 'phonenumber']:
      body['phoneNumber'] = arg[i+1]
    elif myarg in ['customerauthtoken', 'transfertoken']:
      customerAuthToken = arg[i+1]
    else:
      systemErrorExit(3, '%s is not a valid argument for "gam %s resoldcustomer"' % (myarg, sys.argv[1]))
    i += 2
  return customerAuthToken, body

def doUpdateResoldCustomer():
  res = buildGAPIObject('reseller')
  customerId = sys.argv[3]
  customerAuthToken, body = _getResoldCustomerAttr(sys.argv[4:])
  callGAPI(res.customers(), 'patch', customerId=customerId, body=body, customerAuthToken=customerAuthToken, fields='customerId')
  print('updated customer %s' % customerId)

def doCreateResoldCustomer():
  res = buildGAPIObject('reseller')
  customerAuthToken, body = _getResoldCustomerAttr(sys.argv[4:])
  body['customerDomain'] = sys.argv[3]
  result = callGAPI(res.customers(), 'insert', body=body, customerAuthToken=customerAuthToken, fields='customerId,customerDomain')
  print('Created customer %s with id %s' % (result['customerDomain'], result['customerId']))

def _getValueFromOAuth(field, credentials=None):
  credentials = credentials if credentials is not None else getValidOauth2TxtCredentials()
  return credentials.id_token.get(field, 'Unknown')

def doGetMemberInfo():
  cd = buildGAPIObject('directory')
  memberKey = normalizeEmailAddressOrUID(sys.argv[3])
  groupKey = normalizeEmailAddressOrUID(sys.argv[4])
  info = callGAPI(cd.members(), 'get', memberKey=memberKey, groupKey=groupKey)
  print_json(None, info)

def doGetUserInfo(user_email=None):

  def user_lic_result(request_id, response, exception):
    if response and 'skuId' in response:
      user_licenses.append(response['skuId'])

  cd = buildGAPIObject('directory')
  i = 3
  if user_email is None:
    if len(sys.argv) > 3:
      user_email = normalizeEmailAddressOrUID(sys.argv[3])
      i = 4
    else:
      user_email = _getValueFromOAuth('email')
  getSchemas = getAliases = getGroups = getLicenses = True
  projection = 'full'
  customFieldMask = viewType = None
  skus = sorted(SKUS.keys())
  while i < len(sys.argv):
    myarg = sys.argv[i].lower()
    if myarg == 'noaliases':
      getAliases = False
      i += 1
    elif myarg == 'nogroups':
      getGroups = False
      i += 1
    elif myarg in ['nolicenses', 'nolicences']:
      getLicenses = False
      i += 1
    elif myarg in ['sku', 'skus']:
      skus = sys.argv[i+1].split(',')
      i += 2
    elif myarg == 'noschemas':
      getSchemas = False
      projection = 'basic'
      i += 1
    elif myarg in ['custom', 'schemas']:
      getSchemas = True
      projection = 'custom'
      customFieldMask = sys.argv[i+1]
      i += 2
    elif myarg == 'userview':
      viewType = 'domain_public'
      getGroups = getLicenses = False
      i += 1
    elif myarg in ['nousers', 'groups']:
      i += 1
    else:
      systemErrorExit(2, '%s is not a valid argument for "gam info user"' % myarg)
  user = callGAPI(cd.users(), 'get', userKey=user_email, projection=projection, customFieldMask=customFieldMask, viewType=viewType)
  print('User: %s' % user['primaryEmail'])
  if 'name' in user and 'givenName' in user['name']:
    print(utils.convertUTF8('First Name: %s' % user['name']['givenName']))
  if 'name' in user and 'familyName' in user['name']:
    print(utils.convertUTF8('Last Name: %s' % user['name']['familyName']))
  if 'languages' in user:
    up = 'languageCode'
    languages = [row[up] for row in user['languages'] if up in row]
    if languages:
      print('Languages: %s' % ','.join(languages))
    up = 'customLanguage'
    languages = [row[up] for row in user['languages'] if up in row]
    if languages:
      print('Custom Languages: %s' % ','.join(languages))
  if 'isAdmin' in user:
    print('Is a Super Admin: %s' % user['isAdmin'])
  if 'isDelegatedAdmin' in user:
    print('Is Delegated Admin: %s' % user['isDelegatedAdmin'])
  if 'isEnrolledIn2Sv' in user:
    print('2-step enrolled: %s' % user['isEnrolledIn2Sv'])
  if 'isEnforcedIn2Sv' in user:
    print('2-step enforced: %s' % user['isEnforcedIn2Sv'])
  if 'agreedToTerms' in user:
    print('Has Agreed to Terms: %s' % user['agreedToTerms'])
  if 'ipWhitelisted' in user:
    print('IP Whitelisted: %s' % user['ipWhitelisted'])
  if 'suspended' in user:
    print('Account Suspended: %s' % user['suspended'])
  if 'suspensionReason' in user:
    print('Suspension Reason: %s' % user['suspensionReason'])
  if 'changePasswordAtNextLogin' in user:
    print('Must Change Password: %s' % user['changePasswordAtNextLogin'])
  if 'id' in user:
    print('Google Unique ID: %s' % user['id'])
  if 'customerId' in user:
    print('Customer ID: %s' % user['customerId'])
  if 'isMailboxSetup' in user:
    print('Mailbox is setup: %s' % user['isMailboxSetup'])
  if 'includeInGlobalAddressList' in user:
    print('Included in GAL: %s' % user['includeInGlobalAddressList'])
  if 'creationTime' in user:
    print('Creation Time: %s' % user['creationTime'])
  if 'lastLoginTime' in user:
    if user['lastLoginTime'] == NEVER_TIME:
      print('Last login time: Never')
    else:
      print('Last login time: %s' % user['lastLoginTime'])
  if 'orgUnitPath' in user:
    print('Google Org Unit Path: %s\n' % user['orgUnitPath'])
  if 'thumbnailPhotoUrl' in user:
    print('Photo URL: %s\n' % user['thumbnailPhotoUrl'])
  if 'notes' in user:
    print('Notes:')
    notes = user['notes']
    if isinstance(notes, dict):
      contentType = notes.get('contentType', 'text_plain')
      print(' %s: %s' % ('contentType', contentType))
      if contentType == 'text_html':
        print(utils.convertUTF8(utils.indentMultiLineText(' value: {0}'.format(utils.dehtml(notes['value'])), n=2)))
      else:
        print(utils.convertUTF8(utils.indentMultiLineText(' value: {0}'.format(notes['value']), n=2)))
    else:
      print(utils.convertUTF8(utils.indentMultiLineText(' value: {0}'.format(notes), n=2)))
    print('')
  if 'gender' in user:
    print('Gender')
    gender = user['gender']
    for key in gender:
      if key == 'customGender' and not gender[key]:
        continue
      print(utils.convertUTF8(' %s: %s' % (key, gender[key])))
    print('')
  if 'keywords' in user:
    print('Keywords:')
    for keyword in user['keywords']:
      for key in keyword:
        if key == 'customType' and not keyword[key]:
          continue
        print(utils.convertUTF8(' %s: %s' % (key, keyword[key])))
      print('')
  if 'ims' in user:
    print('IMs:')
    for im in user['ims']:
      for key in im:
        print(utils.convertUTF8(' %s: %s' % (key, im[key])))
      print('')
  if 'addresses' in user:
    print('Addresses:')
    for address in user['addresses']:
      for key in address:
        if key != 'formatted':
          print(utils.convertUTF8(' %s: %s' % (key, address[key])))
        else:
          print(utils.convertUTF8(' %s: %s' % (key, address[key].replace('\n', '\\n'))))
      print('')
  if 'organizations' in user:
    print('Organizations:')
    for org in user['organizations']:
      for key in org:
        if key == 'customType' and not org[key]:
          continue
        print(utils.convertUTF8(' %s: %s' % (key, org[key])))
      print('')
  if 'locations' in user:
    print('Locations:')
    for location in user['locations']:
      for key in location:
        if key == 'customType' and not location[key]:
          continue
        print(utils.convertUTF8(' %s: %s' % (key, location[key])))
      print('')
  if 'sshPublicKeys' in user:
    print('SSH Public Keys:')
    for sshkey in user['sshPublicKeys']:
      for key in sshkey:
        print(utils.convertUTF8(' %s: %s' % (key, sshkey[key])))
      print('')
  if 'posixAccounts' in user:
    print('Posix Accounts:')
    for posix in user['posixAccounts']:
      for key in posix:
        print(utils.convertUTF8(' %s: %s' % (key, posix[key])))
      print('')
  if 'phones' in user:
    print('Phones:')
    for phone in user['phones']:
      for key in phone:
        print(utils.convertUTF8(' %s: %s' % (key, phone[key])))
      print('')
  if 'emails' in user:
    if len(user['emails']) > 1:
      print('Other Emails:')
      for an_email in user['emails']:
        if an_email['address'].lower() == user['primaryEmail'].lower():
          continue
        for key in an_email:
          if key == 'type' and an_email[key] == 'custom':
            continue
          if key == 'customType':
            print(utils.convertUTF8(' type: %s' % an_email[key]))
          else:
            print(utils.convertUTF8(' %s: %s' % (key, an_email[key])))
      print('')
  if 'relations' in user:
    print('Relations:')
    for relation in user['relations']:
      for key in relation:
        if key == 'type' and relation[key] == 'custom':
          continue
        elif key == 'customType':
          print(utils.convertUTF8(' %s: %s' % ('type', relation[key])))
        else:
          print(utils.convertUTF8(' %s: %s' % (key, relation[key])))
      print('')
  if 'externalIds' in user:
    print('External IDs:')
    for externalId in user['externalIds']:
      for key in externalId:
        if key == 'type' and externalId[key] == 'custom':
          continue
        elif key == 'customType':
          print(utils.convertUTF8(' %s: %s' % ('type', externalId[key])))
        else:
          print(utils.convertUTF8(' %s: %s' % (key, externalId[key])))
      print('')
  if 'websites' in user:
    print('Websites:')
    for website in user['websites']:
      for key in website:
        if key == 'type' and website[key] == 'custom':
          continue
        elif key == 'customType':
          print(utils.convertUTF8(' %s: %s' % ('type', website[key])))
        else:
          print(utils.convertUTF8(' %s: %s' % (key, website[key])))
      print('')
  if getSchemas:
    if 'customSchemas' in user:
      print('Custom Schemas:')
      for schema in user['customSchemas']:
        print(' Schema: %s' % schema)
        for field in user['customSchemas'][schema]:
          if isinstance(user['customSchemas'][schema][field], list):
            print('  %s:' % field)
            for an_item in user['customSchemas'][schema][field]:
              print(utils.convertUTF8('   type: %s' % (an_item['type'])))
              if an_item['type'] == 'custom':
                print(utils.convertUTF8('    customType: %s' % (an_item['customType'])))
              print(utils.convertUTF8('    value: %s' % (an_item['value'])))
          else:
            print(utils.convertUTF8('  %s: %s' % (field, user['customSchemas'][schema][field])))
        print()
  if getAliases:
    if 'aliases' in user:
      print('Email Aliases:')
      for alias in user['aliases']:
        print('  %s' % alias)
    if 'nonEditableAliases' in user:
      print('Non-Editable Aliases:')
      for alias in user['nonEditableAliases']:
        print('  %s' % alias)
  if getGroups:
    groups = callGAPIpages(cd.groups(), 'list', 'groups', userKey=user_email, fields='groups(name,email),nextPageToken')
    if groups:
      print('Groups: (%s)' % len(groups))
      for group in groups:
        print('   %s <%s>' % (group['name'], group['email']))
  if getLicenses:
    print('Licenses:')
    lic = buildGAPIObject('licensing')
    lbatch = lic.new_batch_http_request(callback=user_lic_result)
    user_licenses = []
    for sku in skus:
      productId, skuId = getProductAndSKU(sku)
      lbatch.add(lic.licenseAssignments().get(userId=user_email, productId=productId, skuId=skuId, fields='skuId'))
    lbatch.execute()
    for user_license in user_licenses:
      print('  %s' % (_formatSKUIdDisplayName(user_license)))

def _skuIdToDisplayName(skuId):
  return SKUS[skuId]['displayName'] if skuId in SKUS else skuId

def _formatSKUIdDisplayName(skuId):
  skuIdDisplay = _skuIdToDisplayName(skuId)
  if skuId == skuIdDisplay:
    return skuId
  return '{0} ({1})'.format(skuId, skuIdDisplay)

def doGetGroupInfo(group_name=None):
  cd = buildGAPIObject('directory')
  gs = buildGAPIObject('groupssettings')
  getAliases = getUsers = True
  getGroups = False
  if group_name is None:
    group_name = normalizeEmailAddressOrUID(sys.argv[3])
    i = 4
  else:
    i = 3
  while i < len(sys.argv):
    myarg = sys.argv[i].lower()
    if myarg == 'nousers':
      getUsers = False
      i += 1
    elif myarg == 'noaliases':
      getAliases = False
      i += 1
    elif myarg == 'groups':
      getGroups = True
      i += 1
    elif myarg in ['nogroups', 'nolicenses', 'nolicences', 'noschemas', 'schemas', 'userview']:
      i += 1
      if myarg == 'schemas':
        i += 1
    else:
      systemErrorExit(2, '%s is not a valid argument for "gam info group"' % myarg)
  basic_info = callGAPI(cd.groups(), 'get', groupKey=group_name)
  settings = {}
  if not GroupIsAbuseOrPostmaster(basic_info['email']):
    try:
      settings = callGAPI(gs.groups(), 'get', throw_reasons=[GAPI_AUTH_ERROR], retry_reasons=['serviceLimit'],
                          groupUniqueId=basic_info['email']) # Use email address retrieved from cd since GS API doesn't support uid
      if settings is None:
        settings = {}
    except GAPI_authError:
      pass
  print('')
  print('Group Settings:')
  for key, value in list(basic_info.items()):
    if (key in ['kind', 'etag']) or ((key == 'aliases') and (not getAliases)):
      continue
    if isinstance(value, list):
      print(' %s:' % key)
      for val in value:
        print('  %s' % val)
    else:
      print(utils.convertUTF8(' %s: %s' % (key, value)))
  for key, value in list(settings.items()):
    if key in ['kind', 'etag', 'description', 'email', 'name']:
      continue
    print(' %s: %s' % (key, value))
  if getGroups:
    groups = callGAPIpages(cd.groups(), 'list', 'groups',
                           userKey=basic_info['email'], fields='nextPageToken,groups(name,email)')
    if groups:
      print('Groups: ({0})'.format(len(groups)))
      for groupm in groups:
        print('  %s: %s' % (groupm['name'], groupm['email']))
  if getUsers:
    members = callGAPIpages(cd.members(), 'list', 'members', groupKey=group_name, fields='nextPageToken,members(email,id,role,type)', maxResults=GC_Values[GC_MEMBER_MAX_RESULTS])
    print('Members:')
    for member in members:
      print(' %s: %s (%s)' % (member.get('role', ROLE_MEMBER).lower(), member.get('email', member['id']), member['type'].lower()))
    print('Total %s users in group' % len(members))

def doGetAliasInfo(alias_email=None):
  cd = buildGAPIObject('directory')
  if alias_email is None:
    alias_email = normalizeEmailAddressOrUID(sys.argv[3])
  try:
    result = callGAPI(cd.users(), 'get', throw_reasons=[GAPI_INVALID, GAPI_BAD_REQUEST], userKey=alias_email)
  except (GAPI_invalid, GAPI_badRequest):
    result = callGAPI(cd.groups(), 'get', groupKey=alias_email)
  print(' Alias Email: %s' % alias_email)
  try:
    if result['primaryEmail'].lower() == alias_email.lower():
      systemErrorExit(3, '%s is a primary user email address, not an alias.' % alias_email)
    print(' User Email: %s' % result['primaryEmail'])
  except KeyError:
    print(' Group Email: %s' % result['email'])
  print(' Unique ID: %s' % result['id'])

def doGetResourceCalendarInfo():
  cd = buildGAPIObject('directory')
  resId = sys.argv[3]
  resource = callGAPI(cd.resources().calendars(), 'get',
                      customer=GC_Values[GC_CUSTOMER_ID], calendarResourceId=resId)
  if 'featureInstances' in resource:
    resource['features'] = ', '.join([a_feature['feature']['name'] for a_feature in resource.pop('featureInstances')])
  if 'buildingId' in resource:
    resource['buildingName'] = _getBuildingNameById(cd, resource['buildingId'])
    resource['buildingId'] = 'id:{0}'.format(resource['buildingId'])
  print_json(None, resource)

def _filterTimeRanges(activeTimeRanges, startDate, endDate):
  if startDate is None and endDate is None:
    return activeTimeRanges
  filteredTimeRanges = []
  for timeRange in activeTimeRanges:
    activityDate = datetime.datetime.strptime(timeRange['date'], YYYYMMDD_FORMAT)
    if ((startDate is None) or (activityDate >= startDate)) and ((endDate is None) or (activityDate <= endDate)):
      filteredTimeRanges.append(timeRange)
  return filteredTimeRanges

def _filterCreateReportTime(items, timeField, startTime, endTime):
  if startTime is None and endTime is None:
    return items
  filteredItems = []
  for item in items:
    timeValue = datetime.datetime.strptime(item[timeField], '%Y-%m-%dT%H:%M:%S.%fZ')
    if ((startTime is None) or (timeValue >= startTime)) and ((endTime is None) or (timeValue <= endTime)):
      filteredItems.append(item)
  return filteredItems

def _getFilterDate(dateStr):
  return datetime.datetime.strptime(dateStr, YYYYMMDD_FORMAT)

def doGetCrosInfo():
  cd = buildGAPIObject('directory')
  i, devices = getCrOSDeviceEntity(3, cd)
  downloadfile = None
  targetFolder = GC_Values[GC_DRIVE_DIR]
  projection = None
  fieldsList = []
  noLists = False
  startDate = endDate = None
  listLimit = 0
  while i < len(sys.argv):
    myarg = sys.argv[i].lower().replace('_', '')
    if myarg == 'nolists':
      noLists = True
      i += 1
    elif myarg in CROS_START_ARGUMENTS:
      startDate = _getFilterDate(sys.argv[i+1])
      i += 2
    elif myarg in CROS_END_ARGUMENTS:
      endDate = _getFilterDate(sys.argv[i+1])
      i += 2
    elif myarg == 'listlimit':
      listLimit = getInteger(sys.argv[i+1], myarg, minVal=-1)
      i += 2
    elif myarg == 'allfields':
      projection = 'FULL'
      fieldsList = []
      i += 1
    elif myarg in PROJECTION_CHOICES_MAP:
      projection = PROJECTION_CHOICES_MAP[myarg]
      if projection == 'FULL':
        fieldsList = []
      else:
        fieldsList = CROS_BASIC_FIELDS_LIST[:]
      i += 1
    elif myarg in CROS_ARGUMENT_TO_PROPERTY_MAP:
      if not fieldsList:
        fieldsList = ['deviceId',]
      fieldsList.extend(CROS_ARGUMENT_TO_PROPERTY_MAP[myarg])
      i += 1
    elif myarg == 'fields':
      if not fieldsList:
        fieldsList = ['deviceId',]
      fieldNameList = sys.argv[i+1]
      for field in fieldNameList.lower().replace(',', ' ').split():
        if field in CROS_ARGUMENT_TO_PROPERTY_MAP:
          fieldsList.extend(CROS_ARGUMENT_TO_PROPERTY_MAP[field])
          if field in CROS_ACTIVE_TIME_RANGES_ARGUMENTS+CROS_DEVICE_FILES_ARGUMENTS+CROS_RECENT_USERS_ARGUMENTS:
            projection = 'FULL'
            noLists = False
        else:
          systemErrorExit(2, '%s is not a valid argument for "gam info cros fields"' % field)
      i += 2
    elif myarg == 'downloadfile':
      downloadfile = sys.argv[i+1]
      if downloadfile.lower() == 'latest':
        downloadfile = downloadfile.lower()
      i += 2
    elif myarg == 'targetfolder':
      targetFolder = os.path.expanduser(sys.argv[i+1])
      if not os.path.isdir(targetFolder):
        os.makedirs(targetFolder)
      i += 2
    else:
      systemErrorExit(2, '%s is not a valid argument for "gam info cros"' % sys.argv[i])
  if fieldsList:
    fields = ','.join(set(fieldsList)).replace('.', '/')
  else:
    fields = None
  i = 0
  device_count = len(devices)
  for deviceId in devices:
    i += 1
    cros = callGAPI(cd.chromeosdevices(), 'get', customerId=GC_Values[GC_CUSTOMER_ID],
                    deviceId=deviceId, projection=projection, fields=fields)
    print('CrOS Device: {0} ({1} of {2})'.format(deviceId, i, device_count))
    if 'notes' in cros:
      cros['notes'] = cros['notes'].replace('\n', '\\n')
    cros = _checkTPMVulnerability(cros)
    for up in CROS_SCALAR_PROPERTY_PRINT_ORDER:
      if up in cros:
        if isinstance(cros[up], str):
          print('  {0}: {1}'.format(up, cros[up]))
        else:
          sys.stdout.write('  %s:' % up)
          print_json(None, cros[up], '  ')
    if not noLists:
      activeTimeRanges = _filterTimeRanges(cros.get('activeTimeRanges', []), startDate, endDate)
      lenATR = len(activeTimeRanges)
      if lenATR:
        print('  activeTimeRanges')
        for activeTimeRange in activeTimeRanges[:min(lenATR, listLimit or lenATR)]:
          print('    date: {0}'.format(activeTimeRange['date']))
          print('      activeTime: {0}'.format(str(activeTimeRange['activeTime'])))
          print('      duration: {0}'.format(utils.formatMilliSeconds(activeTimeRange['activeTime'])))
          print('      minutes: {0}'.format(activeTimeRange['activeTime']/60000))
      recentUsers = cros.get('recentUsers', [])
      lenRU = len(recentUsers)
      if lenRU:
        print('  recentUsers')
        for recentUser in recentUsers[:min(lenRU, listLimit or lenRU)]:
          print('    type: {0}'.format(recentUser['type']))
          print('      email: {0}'.format(recentUser.get('email', ['Unknown', 'UnmanagedUser'][recentUser['type'] == 'USER_TYPE_UNMANAGED'])))
      deviceFiles = _filterCreateReportTime(cros.get('deviceFiles', []), 'createTime', startDate, endDate)
      lenDF = len(deviceFiles)
      if lenDF:
        print('  deviceFiles')
        for deviceFile in deviceFiles[:min(lenDF, listLimit or lenDF)]:
          print('    {0}: {1}'.format(deviceFile['type'], deviceFile['createTime']))
      if downloadfile:
        deviceFiles = cros.get('deviceFiles', [])
        lenDF = len(deviceFiles)
        if lenDF:
          if downloadfile == 'latest':
            deviceFile = deviceFiles[-1]
          else:
            for deviceFile in deviceFiles:
              if deviceFile['createTime'] == downloadfile:
                break
            else:
              print('ERROR: file {0} not available to download.'.format(downloadfile))
              deviceFile = None
          if deviceFile:
            downloadfilename = os.path.join(targetFolder, 'cros-logs-{0}-{1}.zip'.format(deviceId, deviceFile['createTime']))
            _, content = cd._http.request(deviceFile['downloadUrl'])
            writeFile(downloadfilename, content, continueOnError=True)
            print('Downloaded: {0}'.format(downloadfilename))
        elif downloadfile:
          print('ERROR: no files to download.')
      cpuStatusReports = _filterCreateReportTime(cros.get('cpuStatusReports', []), 'reportTime', startDate, endDate)
      lenCSR = len(cpuStatusReports)
      if lenCSR:
        print('  cpuStatusReports')
        for cpuStatusReport in cpuStatusReports[:min(lenCSR, listLimit or lenCSR)]:
          print('    reportTime: {0}'.format(cpuStatusReport['reportTime']))
          print('      cpuTemperatureInfo')
          for tempInfo in cpuStatusReport.get('cpuTemperatureInfo', []):
            print('        {0}: {1}'.format(tempInfo['label'].strip(), tempInfo['temperature']))
          print('      cpuUtilizationPercentageInfo: {0}'.format(','.join([str(x) for x in cpuStatusReport['cpuUtilizationPercentageInfo']])))
      diskVolumeReports = cros.get('diskVolumeReports', [])
      lenDVR = len(diskVolumeReports)
      if lenDVR:
        print('  diskVolumeReports')
        print('    volumeInfo')
        for diskVolumeReport in diskVolumeReports[:min(lenDVR, listLimit or lenDVR)]:
          volumeInfo = diskVolumeReport['volumeInfo']
          for volume in volumeInfo:
            print('      volumeId: {0}'.format(volume['volumeId']))
            print('        storageFree: {0}'.format(volume['storageFree']))
            print('        storageTotal: {0}'.format(volume['storageTotal']))
      systemRamFreeReports = _filterCreateReportTime(cros.get('systemRamFreeReports', []), 'reportTime', startDate, endDate)
      lenSRFR = len(systemRamFreeReports)
      if lenSRFR:
        print('  systemRamFreeReports')
        for systemRamFreeReport in systemRamFreeReports[:min(lenSRFR, listLimit or lenSRFR)]:
          print('    reportTime: {0}'.format(systemRamFreeReport['reportTime']))
          print('      systemRamFreeInfo: {0}'.format(','.join(systemRamFreeReport['systemRamFreeInfo'])))

def doGetMobileInfo():
  cd = buildGAPIObject('directory')
  resourceId = sys.argv[3]
  info = callGAPI(cd.mobiledevices(), 'get', customerId=GC_Values[GC_CUSTOMER_ID], resourceId=resourceId)
  print_json(None, info)

def print_json(object_name, object_value, spacing=''):
  if object_name in ['kind', 'etag', 'etags']:
    return
  if object_name is not None:
    sys.stdout.write('%s%s: ' % (spacing, object_name))
  if isinstance(object_value, list):
    if len(object_value) == 1 and isinstance(object_value[0], (str, int, bool)):
      sys.stdout.write(utils.convertUTF8('%s\n' % object_value[0]))
      return
    if object_name is not None:
      sys.stdout.write('\n')
    for a_value in object_value:
      if isinstance(a_value, (str, int, bool)):
        sys.stdout.write(utils.convertUTF8(' %s%s\n' % (spacing, a_value)))
      else:
        print_json(None, a_value, ' %s' % spacing)
  elif isinstance(object_value, dict):
    print()
    if object_name is not None:
      sys.stdout.write('\n')
    for another_object in object_value:
      print_json(another_object, object_value[another_object], ' %s' % spacing)
  else:
    sys.stdout.write(utils.convertUTF8('%s\n' % (object_value)))

def doSiteVerifyShow():
  verif = buildGAPIObject('siteVerification')
  a_domain = sys.argv[3]
  txt_record = callGAPI(verif.webResource(), 'getToken', body={'site':{'type':'INET_DOMAIN', 'identifier':a_domain}, 'verificationMethod':'DNS_TXT'})
  print('TXT Record Name:   %s' % a_domain)
  print('TXT Record Value:  %s' % txt_record['token'])
  print()
  cname_record = callGAPI(verif.webResource(), 'getToken', body={'site':{'type':'INET_DOMAIN', 'identifier':a_domain}, 'verificationMethod':'DNS_CNAME'})
  cname_token = cname_record['token']
  cname_list = cname_token.split(' ')
  cname_subdomain = cname_list[0]
  cname_value = cname_list[1]
  print('CNAME Record Name:   %s.%s' % (cname_subdomain, a_domain))
  print('CNAME Record Value:  %s' % cname_value)
  print('')
  webserver_file_record = callGAPI(verif.webResource(), 'getToken', body={'site':{'type':'SITE', 'identifier':'http://%s/' % a_domain}, 'verificationMethod':'FILE'})
  webserver_file_token = webserver_file_record['token']
  print('Saving web server verification file to: %s' % webserver_file_token)
  writeFile(webserver_file_token, 'google-site-verification: {0}'.format(webserver_file_token), continueOnError=True)
  print('Verification File URL: http://%s/%s' % (a_domain, webserver_file_token))
  print()
  webserver_meta_record = callGAPI(verif.webResource(), 'getToken', body={'site':{'type':'SITE', 'identifier':'http://%s/' % a_domain}, 'verificationMethod':'META'})
  print('Meta URL:               http://%s/' % a_domain)
  print('Meta HTML Header Data:  %s' % webserver_meta_record['token'])
  print()

def doGetSiteVerifications():
  verif = buildGAPIObject('siteVerification')
  sites = callGAPIitems(verif.webResource(), 'list', 'items')
  if sites:
    for site in sites:
      print('Site: %s' % site['site']['identifier'])
      print('Type: %s' % site['site']['type'])
      print('Owners:')
      for owner in site['owners']:
        print(' %s' % owner)
      print()
  else:
    print('No Sites Verified.')

def doSiteVerifyAttempt():
  verif = buildGAPIObject('siteVerification')
  a_domain = sys.argv[3]
  verificationMethod = sys.argv[4].upper()
  if verificationMethod == 'CNAME':
    verificationMethod = 'DNS_CNAME'
  elif verificationMethod in ['TXT', 'TEXT']:
    verificationMethod = 'DNS_TXT'
  if verificationMethod in ['DNS_TXT', 'DNS_CNAME']:
    verify_type = 'INET_DOMAIN'
    identifier = a_domain
  else:
    verify_type = 'SITE'
    identifier = 'http://%s/' % a_domain
  body = {'site':{'type':verify_type, 'identifier':identifier}, 'verificationMethod':verificationMethod}
  try:
    verify_result = callGAPI(verif.webResource(), 'insert', throw_reasons=[GAPI_BAD_REQUEST], verificationMethod=verificationMethod, body=body)
  except GAPI_badRequest as e:
    print('ERROR: %s' % str(e))
    verify_data = callGAPI(verif.webResource(), 'getToken', body=body)
    print('Method:  %s' % verify_data['method'])
    print('Token:      %s' % verify_data['token'])
    if verify_data['method'] in ['DNS_CNAME', 'DNS_TXT']:
      resolver = dns.resolver.Resolver()
      resolver.nameservers = ['8.8.8.8', '8.8.4.4']
      if verify_data['method'] == 'DNS_CNAME':
        cname_token = verify_data['token']
        cname_list = cname_token.split(' ')
        cname_subdomain = cname_list[0]
        try:
          answers = resolver.query('%s.%s' % (cname_subdomain, a_domain), 'A')
          for answer in answers:
            print('DNS Record: %s' % answer)
        except (dns.resolver.NXDOMAIN, dns.resolver.NoAnswer):
          print('ERROR: No such domain found in DNS!')
      else:
        try:
          answers = resolver.query(a_domain, 'TXT')
          for answer in answers:
            print('DNS Record: %s' % str(answer).replace('"', ''))
        except dns.resolver.NXDOMAIN:
          print('ERROR: no such domain found in DNS!')
    return
  print('SUCCESS!')
  print('Verified:  %s' % verify_result['site']['identifier'])
  print('ID:  %s' % verify_result['id'])
  print('Type: %s' % verify_result['site']['type'])
  print('All Owners:')
  try:
    for owner in verify_result['owners']:
      print(' %s' % owner)
  except KeyError:
    pass
  print()
  print('You can now add %s or it\'s subdomains as secondary or domain aliases of the %s G Suite Account.' % (a_domain, GC_Values[GC_DOMAIN]))

def orgUnitPathQuery(path, checkSuspended):
  query = "orgUnitPath='{0}'".format(path.replace("'", "\\'")) if path != '/' else ''
  if checkSuspended is not None:
    query += ' isSuspended={0}'.format(checkSuspended)
  return query

def makeOrgUnitPathAbsolute(path):
  if path == '/':
    return path
  if path.startswith('/'):
    return path.rstrip('/')
  if path.startswith('id:'):
    return path
  if path.startswith('uid:'):
    return path[1:]
  return '/'+path.rstrip('/')

def makeOrgUnitPathRelative(path):
  if path == '/':
    return path
  if path.startswith('/'):
    return path[1:].rstrip('/')
  if path.startswith('id:'):
    return path
  if path.startswith('uid:'):
    return path[1:]
  return path.rstrip('/')

def encodeOrgUnitPath(path):
  if path.find('+') == -1 and path.find('%') == -1:
    return path
  encpath = ''
  for c in path:
    if c == '+':
      encpath += '%2B'
    elif c == '%':
      encpath += '%25'
    else:
      encpath += c
  return encpath

def getOrgUnitItem(orgUnit, pathOnly=False, absolutePath=True):
  if pathOnly and (orgUnit.startswith('id:') or orgUnit.startswith('uid:')):
    systemErrorExit(2, '%s is not valid in this context' % orgUnit)
  if absolutePath:
    return makeOrgUnitPathAbsolute(orgUnit)
  return makeOrgUnitPathRelative(orgUnit)

def getOrgUnitId(orgUnit, cd=None):
  if cd is None:
    cd = buildGAPIObject('directory')
  orgUnit = getOrgUnitItem(orgUnit)
  if orgUnit[:3] == 'id:':
    return (orgUnit, orgUnit)
  result = callGAPI(cd.orgunits(), 'get',
                    customerId=GC_Values[GC_CUSTOMER_ID], orgUnitPath=encodeOrgUnitPath(makeOrgUnitPathRelative(orgUnit)), fields='orgUnitId')
  return (orgUnit, result['orgUnitId'])

def getTopLevelOrgId(cd, orgUnitPath):
  try:
    # create a temp org so we can learn what the top level org ID is (sigh)
    temp_org = callGAPI(cd.orgunits(), 'insert', customerId=GC_Values[GC_CUSTOMER_ID],
                        body={'name': 'temp-delete-me', 'parentOrgUnitPath': orgUnitPath},
                        fields='parentOrgUnitId,orgUnitId')
    callGAPI(cd.orgunits(), 'delete', customerId=GC_Values[GC_CUSTOMER_ID], orgUnitPath=temp_org['orgUnitId'])
    return temp_org['parentOrgUnitId']
  except:
    pass
  return None

def doGetOrgInfo(name=None, return_attrib=None):
  cd = buildGAPIObject('directory')
  checkSuspended = None
  if not name:
    name = getOrgUnitItem(sys.argv[3])
    get_users = True
    show_children = False
    i = 4
    while i < len(sys.argv):
      myarg = sys.argv[i].lower()
      if myarg == 'nousers':
        get_users = False
        i += 1
      elif myarg in ['children', 'child']:
        show_children = True
        i += 1
      elif myarg in ['suspended', 'notsuspended']:
        checkSuspended = myarg == 'suspended'
        i += 1
      else:
        systemErrorExit(2, '%s is not a valid argument for "gam info org"' % sys.argv[i])
  if name == '/':
    orgs = callGAPI(cd.orgunits(), 'list',
                    customerId=GC_Values[GC_CUSTOMER_ID], type='children',
                    fields='organizationUnits/parentOrgUnitId')
    if 'organizationUnits' in orgs and orgs['organizationUnits']:
      name = orgs['organizationUnits'][0]['parentOrgUnitId']
    else:
      topLevelOrgId = getTopLevelOrgId(cd, '/')
      if topLevelOrgId:
        name = topLevelOrgId
  else:
    name = makeOrgUnitPathRelative(name)
  result = callGAPI(cd.orgunits(), 'get', customerId=GC_Values[GC_CUSTOMER_ID], orgUnitPath=encodeOrgUnitPath(name))
  if return_attrib:
    return result[return_attrib]
  print_json(None, result)
  if get_users:
    name = result['orgUnitPath']
    page_message = 'Got %%total_items%% Users: %%first_item%% - %%last_item%%\n'
    users = callGAPIpages(cd.users(), 'list', 'users', page_message=page_message,
                          message_attribute='primaryEmail', customer=GC_Values[GC_CUSTOMER_ID], query=orgUnitPathQuery(name, checkSuspended),
                          fields='users(primaryEmail,orgUnitPath),nextPageToken', maxResults=GC_Values[GC_USER_MAX_RESULTS])
    if checkSuspended is None:
      print('Users:')
    elif not checkSuspended:
      print('Users (Not suspended):')
    else:
      print('Users (Suspended):')
    for user in users:
      if show_children or (name.lower() == user['orgUnitPath'].lower()):
        sys.stdout.write(' %s' % user['primaryEmail'])
        if name.lower() != user['orgUnitPath'].lower():
          print(' (child)')
        else:
          print('')

def doGetASPs(users):
  cd = buildGAPIObject('directory')
  for user in users:
    asps = callGAPIitems(cd.asps(), 'list', 'items', userKey=user)
    if asps:
      print('Application-Specific Passwords for %s' % user)
      for asp in asps:
        if asp['creationTime'] == '0':
          created_date = 'Unknown'
        else:
          created_date = datetime.datetime.fromtimestamp(int(asp['creationTime'])/1000).strftime('%Y-%m-%d %H:%M:%S')
        if asp['lastTimeUsed'] == '0':
          used_date = 'Never'
        else:
          used_date = datetime.datetime.fromtimestamp(int(asp['lastTimeUsed'])/1000).strftime('%Y-%m-%d %H:%M:%S')
        print(' ID: %s\n  Name: %s\n  Created: %s\n  Last Used: %s\n' % (asp['codeId'], asp['name'], created_date, used_date))
    else:
      print(' no ASPs for %s\n' % user)

def doDelASP(users):
  cd = buildGAPIObject('directory')
  codeIdList = sys.argv[5].lower()
  if codeIdList == 'all':
    allCodeIds = True
  else:
    allCodeIds = False
    codeIds = codeIdList.replace(',', ' ').split()
  for user in users:
    if allCodeIds:
      asps = callGAPIitems(cd.asps(), 'list', 'items', userKey=user, fields='items/codeId')
      codeIds = [asp['codeId'] for asp in asps]
    for codeId in codeIds:
      callGAPI(cd.asps(), 'delete', userKey=user, codeId=codeId)
      print('deleted ASP %s for %s' % (codeId, user))

def printBackupCodes(user, codes):
  jcount = len(codes)
  realcount = 0
  for code in codes:
    if 'verificationCode' in code and code['verificationCode']:
      realcount += 1
  print('Backup verification codes for {0} ({1})'.format(user, realcount))
  print('')
  if jcount > 0:
    j = 0
    for code in codes:
      j += 1
      print('{0}. {1}'.format(j, code['verificationCode']))
    print('')

def doGetBackupCodes(users):
  cd = buildGAPIObject('directory')
  for user in users:
    try:
      codes = callGAPIitems(cd.verificationCodes(), 'list', 'items', throw_reasons=[GAPI_INVALID_ARGUMENT, GAPI_INVALID], userKey=user)
    except (GAPI_invalidArgument, GAPI_invalid):
      codes = []
    printBackupCodes(user, codes)

def doGenBackupCodes(users):
  cd = buildGAPIObject('directory')
  for user in users:
    callGAPI(cd.verificationCodes(), 'generate', userKey=user)
    codes = callGAPIitems(cd.verificationCodes(), 'list', 'items', userKey=user)
    printBackupCodes(user, codes)

def doDelBackupCodes(users):
  cd = buildGAPIObject('directory')
  for user in users:
    try:
      callGAPI(cd.verificationCodes(), 'invalidate', soft_errors=True, throw_reasons=[GAPI_INVALID], userKey=user)
    except GAPI_invalid:
      print('No 2SV backup codes for %s' % user)
      continue
    print('2SV backup codes for %s invalidated' % user)

def commonClientIds(clientId):
  if clientId == 'gasmo':
    return '1095133494869.apps.googleusercontent.com'
  return clientId

def doDelTokens(users):
  cd = buildGAPIObject('directory')
  clientId = None
  i = 5
  while i < len(sys.argv):
    myarg = sys.argv[i].lower().replace('_', '')
    if myarg == 'clientid':
      clientId = commonClientIds(sys.argv[i+1])
      i += 2
    else:
      systemErrorExit(3, '%s is not a valid argument to "gam <users> delete token"' % sys.argv[i])
  if not clientId:
    systemErrorExit(3, 'you must specify a clientid for "gam <users> delete token"')
  for user in users:
    try:
      callGAPI(cd.tokens(), 'get', throw_reasons=[GAPI_NOT_FOUND, GAPI_RESOURCE_NOT_FOUND], userKey=user, clientId=clientId)
    except (GAPI_notFound, GAPI_resourceNotFound):
      print('User %s did not authorize %s' % (user, clientId))
      continue
    callGAPI(cd.tokens(), 'delete', userKey=user, clientId=clientId)
    print('Deleted token for %s' % user)

def printShowTokens(i, entityType, users, csvFormat):
  def _showToken(token):
    print('  Client ID: %s' % token['clientId'])
    for item in token:
      if item not in ['clientId', 'scopes']:
        print(utils.convertUTF8('    %s: %s' % (item, token.get(item, ''))))
    item = 'scopes'
    print('    %s:' % item)
    for it in token.get(item, []):
      print('      %s' % it)

  cd = buildGAPIObject('directory')
  if csvFormat:
    todrive = False
    titles = ['user', 'clientId', 'displayText', 'anonymous', 'nativeApp', 'userKey', 'scopes']
    csvRows = []
  clientId = None
  while i < len(sys.argv):
    myarg = sys.argv[i].lower()
    if csvFormat and myarg == 'todrive':
      todrive = True
      i += 1
    elif myarg == 'clientid':
      clientId = commonClientIds(sys.argv[i+1])
      i += 2
    elif not entityType:
      entityType = myarg
      users = getUsersToModify(entity_type=entityType, entity=sys.argv[i+1], silent=False)
      i += 2
    else:
      systemErrorExit(2, '%s is not a valid argument for "gam <users> %s tokens"' % (myarg, ['show', 'print'][csvFormat]))
  if not entityType:
    users = getUsersToModify(entity_type='all', entity='users', silent=False)
  fields = ','.join(['clientId', 'displayText', 'anonymous', 'nativeApp', 'userKey', 'scopes'])
  i = 0
  count = len(users)
  for user in users:
    i += 1
    try:
      if csvFormat:
        sys.stderr.write('Getting Access Tokens for %s\n' % (user))
      if clientId:
        results = [callGAPI(cd.tokens(), 'get',
                            throw_reasons=[GAPI_NOT_FOUND, GAPI_USER_NOT_FOUND, GAPI_RESOURCE_NOT_FOUND],
                            userKey=user, clientId=clientId, fields=fields)]
      else:
        results = callGAPIitems(cd.tokens(), 'list', 'items',
                                throw_reasons=[GAPI_USER_NOT_FOUND],
                                userKey=user, fields='items({0})'.format(fields))
      jcount = len(results)
      if not csvFormat:
        print('User: {0}, Access Tokens ({1}/{2})'.format(user, i, count))
        if jcount == 0:
          continue
        for token in results:
          _showToken(token)
      else:
        if jcount == 0:
          continue
        for token in results:
          row = {'user': user, 'scopes': ' '.join(token.get('scopes', []))}
          for item in token:
            if item not in ['scopes']:
              row[item] = token.get(item, '')
          csvRows.append(row)
    except (GAPI_notFound, GAPI_userNotFound, GAPI_resourceNotFound):
      pass
  if csvFormat:
    writeCSVfile(csvRows, titles, 'OAuth Tokens', todrive)

def doDeprovUser(users):
  cd = buildGAPIObject('directory')
  for user in users:
    print('Getting Application Specific Passwords for %s' % user)
    asps = callGAPIitems(cd.asps(), 'list', 'items', userKey=user, fields='items/codeId')
    jcount = len(asps)
    if jcount > 0:
      j = 0
      for asp in asps:
        j += 1
        print(' deleting ASP %s of %s' % (j, jcount))
        callGAPI(cd.asps(), 'delete', userKey=user, codeId=asp['codeId'])
    else:
      print('No ASPs')
    print('Invalidating 2SV Backup Codes for %s' % user)
    try:
      callGAPI(cd.verificationCodes(), 'invalidate', soft_errors=True, throw_reasons=[GAPI_INVALID], userKey=user)
    except GAPI_invalid:
      print('No 2SV Backup Codes')
    print('Getting tokens for %s...' % user)
    tokens = callGAPIitems(cd.tokens(), 'list', 'items', userKey=user, fields='items/clientId')
    jcount = len(tokens)
    if jcount > 0:
      j = 0
      for token in tokens:
        j += 1
        print(' deleting token %s of %s' % (j, jcount))
        callGAPI(cd.tokens(), 'delete', userKey=user, clientId=token['clientId'])
    else:
      print('No Tokens')
    print('Done deprovisioning %s' % user)

def doDeleteUser():
  cd = buildGAPIObject('directory')
  user_email = normalizeEmailAddressOrUID(sys.argv[3])
  print("Deleting account for %s" % (user_email))
  callGAPI(cd.users(), 'delete', userKey=user_email)

def doUndeleteUser():
  cd = buildGAPIObject('directory')
  user = normalizeEmailAddressOrUID(sys.argv[3])
  orgUnit = '/'
  i = 4
  while i < len(sys.argv):
    myarg = sys.argv[i].lower()
    if myarg in ['ou', 'org']:
      orgUnit = makeOrgUnitPathAbsolute(sys.argv[i+1])
      i += 2
    else:
      systemErrorExit(2, '%s is not a valid argument for "gam undelete user"' % sys.argv[i])
  if user.find('@') == -1:
    user_uid = user
  else:
    print('Looking up UID for %s...' % user)
    deleted_users = callGAPIpages(cd.users(), 'list', 'users',
                                  customer=GC_Values[GC_CUSTOMER_ID], showDeleted=True, maxResults=GC_Values[GC_USER_MAX_RESULTS])
    matching_users = list()
    for deleted_user in deleted_users:
      if str(deleted_user['primaryEmail']).lower() == user:
        matching_users.append(deleted_user)
    if not matching_users:
      systemErrorExit(3, 'could not find deleted user with that address.')
    elif len(matching_users) > 1:
      print('ERROR: more than one matching deleted %s user. Please select the correct one to undelete and specify with "gam undelete user uid:<uid>"' % user)
      print('')
      for matching_user in matching_users:
        print(' uid:%s ' % matching_user['id'])
        for attr_name in ['creationTime', 'lastLoginTime', 'deletionTime']:
          try:
            if matching_user[attr_name] == NEVER_TIME:
              matching_user[attr_name] = 'Never'
            print('   %s: %s ' % (attr_name, matching_user[attr_name]))
          except KeyError:
            pass
        print()
      sys.exit(3)
    else:
      user_uid = matching_users[0]['id']
  print("Undeleting account for %s" % user)
  callGAPI(cd.users(), 'undelete', userKey=user_uid, body={'orgUnitPath': orgUnit})

def doDeleteGroup():
  cd = buildGAPIObject('directory')
  group = normalizeEmailAddressOrUID(sys.argv[3])
  print("Deleting group %s" % group)
  callGAPI(cd.groups(), 'delete', groupKey=group)

def doDeleteAlias(alias_email=None):
  cd = buildGAPIObject('directory')
  is_user = is_group = False
  if alias_email is None:
    alias_email = sys.argv[3]
  if alias_email.lower() == 'user':
    is_user = True
    alias_email = sys.argv[4]
  elif alias_email.lower() == 'group':
    is_group = True
    alias_email = sys.argv[4]
  alias_email = normalizeEmailAddressOrUID(alias_email, noUid=True, noLower=True)
  print("Deleting alias %s" % alias_email)
  if is_user or (not is_user and not is_group):
    try:
      callGAPI(cd.users().aliases(), 'delete', throw_reasons=[GAPI_INVALID, GAPI_BAD_REQUEST, GAPI_NOT_FOUND], userKey=alias_email, alias=alias_email)
      return
    except (GAPI_invalid, GAPI_badRequest):
      pass
    except GAPI_notFound:
      systemErrorExit(4, 'The alias %s does not exist' % alias_email)
  if not is_user or (not is_user and not is_group):
    callGAPI(cd.groups().aliases(), 'delete', groupKey=alias_email, alias=alias_email)

def doDeleteResourceCalendar():
  resId = sys.argv[3]
  cd = buildGAPIObject('directory')
  print("Deleting resource calendar %s" % resId)
  callGAPI(cd.resources().calendars(), 'delete',
           customer=GC_Values[GC_CUSTOMER_ID], calendarResourceId=resId)

def doDeleteOrg():
  cd = buildGAPIObject('directory')
  name = getOrgUnitItem(sys.argv[3])
  print("Deleting organization %s" % name)
  callGAPI(cd.orgunits(), 'delete', customerId=GC_Values[GC_CUSTOMER_ID], orgUnitPath=encodeOrgUnitPath(makeOrgUnitPathRelative(name)))

# Send an email
def send_email(msg_subj, msg_txt, msg_rcpt=None):
  userId, gmail = buildGmailGAPIObject(_getValueFromOAuth('email'))
  if not msg_rcpt:
    msg_rcpt = userId
  msg = MIMEText(msg_txt)
  msg['Subject'] = msg_subj
  msg['From'] = userId
  msg['To'] = msg_rcpt
  callGAPI(gmail.users().messages(), 'send',
           userId=userId, body={'raw': base64.urlsafe_b64encode(msg.as_bytes()).decode()})

def addFieldToFieldsList(fieldName, fieldsChoiceMap, fieldsList):
  fields = fieldsChoiceMap[fieldName.lower()]
  if isinstance(fields, list):
    fieldsList.extend(fields)
  else:
    fieldsList.append(fields)

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
  def rowDateTimeFilterMatch(dateMode, rowDate, op, filterDate):
    if not rowDate:
      return False
    try:
      rowTime = dateutil.parser.parse(rowDate, ignoretz=True)
      if dateMode:
        rowDate = datetime.datetime(rowTime.year, rowTime.month, rowTime.day).isoformat()+'Z'
    except ValueError:
      rowDate = NEVER_TIME
    if op == '<':
      return rowDate < filterDate
    if op == '<=':
      return rowDate <= filterDate
    if op == '>':
      return rowDate > filterDate
    if op == '>=':
      return rowDate >= filterDate
    if op == '!=':
      return rowDate != filterDate
    return rowDate == filterDate

  def rowCountFilterMatch(rowCount, op, filterCount):
    if not isinstance(rowCount, int):
      return False
    if op == '<':
      return rowCount < filterCount
    if op == '<=':
      return rowCount <= filterCount
    if op == '>':
      return rowCount > filterCount
    if op == '>=':
      return rowCount >= filterCount
    if op == '!=':
      return rowCount != filterCount
    return rowCount == filterCount

  def rowBooleanFilterMatch(rowBoolean, filterBoolean):
    if not isinstance(rowBoolean, bool):
      return False
    return rowBoolean == filterBoolean

  if GC_Values[GC_CSV_ROW_FILTER]:
    for column, filterVal in iter(GC_Values[GC_CSV_ROW_FILTER].items()):
      if column not in titles:
        sys.stderr.write('WARNING: Row filter column "{0}" is not in output columns\n'.format(column))
        continue
      if filterVal[0] == 'regex':
        csvRows = [row for row in csvRows if filterVal[1].search(row.get(column, ''))]
      elif filterVal[0] in ['date', 'time']:
        csvRows = [row for row in csvRows if rowDateTimeFilterMatch(filterVal[0] == 'date', row.get(column, ''), filterVal[1], filterVal[2])]
      elif filterVal[0] == 'count':
        csvRows = [row for row in csvRows if rowCountFilterMatch(row.get(column, ''), filterVal[1], filterVal[2])]
      else: #boolean
        csvRows = [row for row in csvRows if rowBooleanFilterMatch(row.get(column, False), filterVal[1])]
  if GC_Values[GC_CSV_HEADER_FILTER]:
    titles_filter = GC_Values[GC_CSV_HEADER_FILTER].lower().split(',')
    titles = [t for t in titles if t.lower() in titles_filter]
  csv.register_dialect('nixstdout', lineterminator='\n')
  if todrive:
    write_to = io.StringIO()
  else:
    write_to = sys.stdout
  writer = csv.DictWriter(write_to, fieldnames=titles, dialect='nixstdout', extrasaction='ignore', quoting=csv.QUOTE_MINIMAL)
  try:
    writer.writerow(dict((item, item) for item in writer.fieldnames))
    writer.writerows(csvRows)
  except IOError as e:
    systemErrorExit(6, e)
  if todrive:
    admin_email = _getValueFromOAuth('email')
    _, drive = buildDrive3GAPIObject(admin_email)
    if not drive:
      print('''\nGAM is not authorized to create Drive files. Please run:

gam user %s check serviceaccount

and follow recommend steps to authorize GAM for Drive access.''' % (admin_email))
      sys.exit(5)
    result = callGAPI(drive.about(), 'get', fields='maxImportSizes')
    columns = len(titles)
    rows = len(csvRows)
    cell_count = rows * columns
    data_size = len(write_to.getvalue())
    max_sheet_bytes = int(result['maxImportSizes'][MIMETYPE_GA_SPREADSHEET])
    if cell_count > MAX_GOOGLE_SHEET_CELLS or data_size > max_sheet_bytes:
      print('{0}{1}'.format(WARNING_PREFIX, MESSAGE_RESULTS_TOO_LARGE_FOR_GOOGLE_SPREADSHEET))
      mimeType = 'text/csv'
    else:
      mimeType = MIMETYPE_GA_SPREADSHEET
    body = {'description': ' '.join(sys.argv),
            'name': '%s - %s' % (GC_Values[GC_DOMAIN], list_type),
            'mimeType': mimeType}
    result = callGAPI(drive.files(), 'create', fields='webViewLink',
                      body=body,
                      media_body=googleapiclient.http.MediaInMemoryUpload(write_to.getvalue().encode(),
                                                                          mimetype='text/csv'))
    file_url = result['webViewLink']
    if GC_Values[GC_NO_BROWSER]:
      msg_txt = 'Drive file uploaded to:\n %s' % file_url
      msg_subj = '%s - %s' % (GC_Values[GC_DOMAIN], list_type)
      send_email(msg_subj, msg_txt)
      print(msg_txt)
    else:
      webbrowser.open(file_url)

def flatten_json(structure, key='', path='', flattened=None, listLimit=None):
  if flattened is None:
    flattened = {}
  if not isinstance(structure, (dict, list)):
    flattened[((path + '.') if path else '') + key] = structure
  elif isinstance(structure, list):
    for i, item in enumerate(structure):
      if listLimit and (i >= listLimit):
        break
      flatten_json(item, '{0}'.format(i), '.'.join([item for item in [path, key] if item]), flattened=flattened, listLimit=listLimit)
  else:
    for new_key, value in list(structure.items()):
      if new_key in ['kind', 'etag', '@type']:
        continue
      if value == NEVER_TIME:
        value = 'Never'
      flatten_json(value, new_key, '.'.join([item for item in [path, key] if item]), flattened=flattened, listLimit=listLimit)
  return flattened

USER_ARGUMENT_TO_PROPERTY_MAP = {
  'address': ['addresses',],
  'addresses': ['addresses',],
  'admin': ['isAdmin', 'isDelegatedAdmin',],
  'agreed2terms': ['agreedToTerms',],
  'agreedtoterms': ['agreedToTerms',],
  'aliases': ['aliases', 'nonEditableAliases',],
  'changepassword': ['changePasswordAtNextLogin',],
  'changepasswordatnextlogin': ['changePasswordAtNextLogin',],
  'creationtime': ['creationTime',],
  'deletiontime': ['deletionTime',],
  'email': ['emails',],
  'emails': ['emails',],
  'externalid': ['externalIds',],
  'externalids': ['externalIds',],
  'familyname': ['name.familyName',],
  'firstname': ['name.givenName',],
  'fullname': ['name.fullName',],
  'gal': ['includeInGlobalAddressList',],
  'gender': ['gender.type', 'gender.customGender', 'gender.addressMeAs',],
  'givenname': ['name.givenName',],
  'id': ['id',],
  'im': ['ims',],
  'ims': ['ims',],
  'includeinglobaladdresslist': ['includeInGlobalAddressList',],
  'ipwhitelisted': ['ipWhitelisted',],
  'isadmin': ['isAdmin', 'isDelegatedAdmin',],
  'isdelegatedadmin': ['isAdmin', 'isDelegatedAdmin',],
  'isenforcedin2sv': ['isEnforcedIn2Sv',],
  'isenrolledin2sv': ['isEnrolledIn2Sv',],
  'is2svenforced': ['isEnforcedIn2Sv',],
  'is2svenrolled': ['isEnrolledIn2Sv',],
  'ismailboxsetup': ['isMailboxSetup',],
  'keyword': ['keywords',],
  'keywords': ['keywords',],
  'language': ['languages',],
  'languages': ['languages',],
  'lastlogintime': ['lastLoginTime',],
  'lastname': ['name.familyName',],
  'location': ['locations',],
  'locations': ['locations',],
  'name': ['name.givenName', 'name.familyName', 'name.fullName',],
  'nicknames': ['aliases', 'nonEditableAliases',],
  'noneditablealiases': ['aliases', 'nonEditableAliases',],
  'note': ['notes',],
  'notes': ['notes',],
  'org': ['orgUnitPath',],
  'organization': ['organizations',],
  'organizations': ['organizations',],
  'orgunitpath': ['orgUnitPath',],
  'otheremail': ['emails',],
  'otheremails': ['emails',],
  'ou': ['orgUnitPath',],
  'phone': ['phones',],
  'phones': ['phones',],
  'photo': ['thumbnailPhotoUrl',],
  'photourl': ['thumbnailPhotoUrl',],
  'posix': ['posixAccounts',],
  'posixaccounts': ['posixAccounts',],
  'primaryemail': ['primaryEmail',],
  'relation': ['relations',],
  'relations': ['relations',],
  'ssh': ['sshPublicKeys',],
  'sshkeys': ['sshPublicKeys',],
  'sshpublickeys': ['sshPublicKeys',],
  'suspended': ['suspended', 'suspensionReason',],
  'thumbnailphotourl': ['thumbnailPhotoUrl',],
  'username': ['primaryEmail',],
  'website': ['websites',],
  'websites': ['websites',],
  }

def doPrintUsers():
  cd = buildGAPIObject('directory')
  todrive = False
  fieldsList = []
  fieldsTitles = {}
  titles = []
  csvRows = []
  addFieldToCSVfile('primaryemail', USER_ARGUMENT_TO_PROPERTY_MAP, fieldsList, fieldsTitles, titles)
  customer = GC_Values[GC_CUSTOMER_ID]
  domain = None
  queries = [None]
  projection = 'basic'
  customFieldMask = None
  sortHeaders = getGroupFeed = getLicenseFeed = email_parts = False
  viewType = deleted_only = orderBy = sortOrder = None
  groupDelimiter = ' '
  licenseDelimiter = ','
  i = 3
  while i < len(sys.argv):
    myarg = sys.argv[i].lower().replace('_', '')
    if myarg in PROJECTION_CHOICES_MAP:
      projection = myarg
      sortHeaders = True
      fieldsList = []
      i += 1
    elif myarg == 'allfields':
      projection = 'basic'
      sortHeaders = True
      fieldsList = []
      i += 1
    elif myarg == 'delimiter':
      groupDelimiter = licenseDelimiter = sys.argv[i+1]
      i += 2
    elif myarg == 'sortheaders':
      sortHeaders = True
      i += 1
    elif myarg in ['custom', 'schemas']:
      fieldsList.append('customSchemas')
      if sys.argv[i+1].lower() == 'all':
        projection = 'full'
      else:
        projection = 'custom'
        customFieldMask = sys.argv[i+1]
      i += 2
    elif myarg == 'todrive':
      todrive = True
      i += 1
    elif myarg in ['deletedonly', 'onlydeleted']:
      deleted_only = True
      i += 1
    elif myarg == 'orderby':
      orderBy = sys.argv[i+1]
      if orderBy.lower() not in ['email', 'familyname', 'givenname', 'firstname', 'lastname']:
        systemErrorExit(2, 'orderby must be one of email, familyName, givenName; got %s' % orderBy)
      elif orderBy.lower() in ['familyname', 'lastname']:
        orderBy = 'familyName'
      elif orderBy.lower() in ['givenname', 'firstname']:
        orderBy = 'givenName'
      i += 2
    elif myarg == 'userview':
      viewType = 'domain_public'
      i += 1
    elif myarg in SORTORDER_CHOICES_MAP:
      sortOrder = SORTORDER_CHOICES_MAP[myarg]
      i += 1
    elif myarg == 'domain':
      domain = sys.argv[i+1]
      customer = None
      i += 2
    elif myarg in ['query', 'queries']:
      queries = getQueries(myarg, sys.argv[i+1])
      i += 2
    elif myarg in USER_ARGUMENT_TO_PROPERTY_MAP:
      if not fieldsList:
        fieldsList = ['primaryEmail',]
      addFieldToCSVfile(myarg, USER_ARGUMENT_TO_PROPERTY_MAP, fieldsList, fieldsTitles, titles)
      i += 1
    elif myarg == 'fields':
      if not fieldsList:
        fieldsList = ['primaryEmail',]
      fieldNameList = sys.argv[i+1]
      for field in fieldNameList.lower().replace(',', ' ').split():
        if field in USER_ARGUMENT_TO_PROPERTY_MAP:
          addFieldToCSVfile(field, USER_ARGUMENT_TO_PROPERTY_MAP, fieldsList, fieldsTitles, titles)
        else:
          systemErrorExit(2, '%s is not a valid argument for "gam print users fields"' % field)
      i += 2
    elif myarg == 'groups':
      getGroupFeed = True
      i += 1
    elif myarg in ['license', 'licenses', 'licence', 'licences']:
      getLicenseFeed = True
      i += 1
    elif myarg in ['emailpart', 'emailparts', 'username']:
      email_parts = True
      i += 1
    else:
      systemErrorExit(2, '%s is not a valid argument for "gam print users"' % sys.argv[i])
  if fieldsList:
    fields = 'nextPageToken,users(%s)' % ','.join(set(fieldsList)).replace('.', '/')
  else:
    fields = None
  for query in queries:
    printGettingAllItems('Users', query)
    page_message = 'Got %%total_items%% Users: %%first_item%% - %%last_item%%\n'
    all_users = callGAPIpages(cd.users(), 'list', 'users', page_message=page_message,
                              message_attribute='primaryEmail', customer=customer, domain=domain, fields=fields,
                              showDeleted=deleted_only, orderBy=orderBy, sortOrder=sortOrder, viewType=viewType,
                              query=query, projection=projection, customFieldMask=customFieldMask, maxResults=GC_Values[GC_USER_MAX_RESULTS])
    for user in all_users:
      if email_parts and ('primaryEmail' in user):
        user_email = user['primaryEmail']
        if user_email.find('@') != -1:
          user['primaryEmailLocal'], user['primaryEmailDomain'] = splitEmailAddress(user_email)
      addRowTitlesToCSVfile(flatten_json(user), csvRows, titles)
  if sortHeaders:
    sortCSVTitles(['primaryEmail',], titles)
  if getGroupFeed:
    total_users = len(csvRows)
    user_count = 1
    titles.append('Groups')
    for user in csvRows:
      user_email = user['primaryEmail']
      sys.stderr.write("Getting Group Membership for %s (%s/%s)\r\n" % (user_email, user_count, total_users))
      groups = callGAPIpages(cd.groups(), 'list', 'groups', userKey=user_email)
      user['Groups'] = groupDelimiter.join([groupname['email'] for groupname in groups])
      user_count += 1
  if getLicenseFeed:
    titles.append('Licenses')
    licenses = doPrintLicenses(returnFields='userId,skuId')
    if licenses:
      for user in csvRows:
        u_licenses = licenses.get(user['primaryEmail'].lower())
        if u_licenses:
          user['Licenses'] = licenseDelimiter.join([_skuIdToDisplayName(skuId) for skuId in u_licenses])
  writeCSVfile(csvRows, titles, 'Users', todrive)

def doPrintShowAlerts():
  _, ac = buildAlertCenterGAPIObject(_getValueFromOAuth('email'))
  alerts = callGAPIpages(ac.alerts(), 'list', 'alerts')
  titles = []
  csv_rows = []
  for alert in alerts:
    aj = flatten_json(alert)
    for field in aj:
      if field not in titles:
        titles.append(field)
    csv_rows.append(aj)
  writeCSVfile(csv_rows, titles, 'Alerts', False)

def doPrintShowAlertFeedback():
  _, ac = buildAlertCenterGAPIObject(_getValueFromOAuth('email'))
  feedback = callGAPIpages(ac.alerts().feedback(), 'list', 'feedback', alertId='-')
  for feedbac in feedback:
    print(feedbac)

def _getValidAlertFeedbackTypes(ac):
  return [aftype for aftype in ac._rootDesc['schemas']['AlertFeedback']['properties']['type']['enum'] if aftype != 'ALERT_FEEDBACK_TYPE_UNSPECIFIED']

def doCreateAlertFeedback():
  _, ac = buildAlertCenterGAPIObject(_getValueFromOAuth('email'))
  valid_types = _getValidAlertFeedbackTypes(ac)
  alertId = sys.argv[3]
  body = {'type': sys.argv[4].upper()}
  if body['type'] not in valid_types:
    systemErrorExit(2, '%s is not a valid feedback value, expected one of: %s' % (body['type'], ', '.join(valid_types)))
  callGAPI(ac.alerts().feedback(), 'create', alertId=alertId, body=body)

def doDeleteOrUndeleteAlert(action):
  _, ac = buildAlertCenterGAPIObject(_getValueFromOAuth('email'))
  alertId = sys.argv[3]
  kwargs = {}
  if action == 'undelete':
    kwargs['body'] = {}
  callGAPI(ac.alerts(), action, alertId=alertId, **kwargs)

GROUP_ARGUMENT_TO_PROPERTY_TITLE_MAP = {
  'admincreated': ['adminCreated', 'Admin_Created'],
  'aliases': ['aliases', 'Aliases', 'nonEditableAliases', 'NonEditableAliases'],
  'description': ['description', 'Description'],
  'directmemberscount': ['directMembersCount', 'DirectMembersCount'],
  'email': ['email', 'Email'],
  'id': ['id', 'ID'],
  'name': ['name', 'Name'],
  }

GROUP_ATTRIBUTES_ARGUMENT_TO_PROPERTY_MAP = {
  'allowexternalmembers': 'allowExternalMembers',
  'allowwebposting': 'allowWebPosting',
  'archiveonly': 'archiveOnly',
  'customfootertext': 'customFooterText',
  'customreplyto': 'customReplyTo',
  'defaultmessagedenynotificationtext': 'defaultMessageDenyNotificationText',
  'gal': 'includeInGlobalAddressList',
  'includecustomfooter': 'includeCustomFooter',
  'includeinglobaladdresslist': 'includeInGlobalAddressList',
  'isarchived': 'isArchived',
  'memberscanpostasthegroup': 'membersCanPostAsTheGroup',
  'messagemoderationlevel': 'messageModerationLevel',
  'primarylanguage': 'primaryLanguage',
  'replyto': 'replyTo',
  'sendmessagedenynotification': 'sendMessageDenyNotification',
  'showingroupdirectory': 'showInGroupDirectory',
  'spammoderationlevel': 'spamModerationLevel',
  'whocanadd': 'whoCanAdd',
  'whocanassigntopics': 'whoCanAssignTopics',
  'whocancontactowner': 'whoCanContactOwner',
  'whocanenterfreeformtags': 'whoCanEnterFreeFormTags',
  'whocaninvite': 'whoCanInvite',
  'whocanjoin': 'whoCanJoin',
  'whocanleavegroup': 'whoCanLeaveGroup',
  'whocanmarkduplicate': 'whoCanMarkDuplicate',
  'whocanmarkfavoritereplyonanytopic': 'whoCanMarkFavoriteReplyOnAnyTopic',
  'whocanmarknoresponseneeded': 'whoCanMarkNoResponseNeeded',
  'whocanmodifytagsandcategories': 'whoCanModifyTagsAndCategories',
  'whocanpostmessage': 'whoCanPostMessage',
  'whocantaketopics': 'whoCanTakeTopics',
  'whocanunassigntopic': 'whoCanUnassignTopic',
  'whocanunmarkfavoritereplyonanytopic': 'whoCanUnmarkFavoriteReplyOnAnyTopic',
  'whocanviewgroup': 'whoCanViewGroup',
  'whocanviewmembership': 'whoCanViewMembership',
  }

def doPrintGroups():
  cd = buildGAPIObject('directory')
  i = 3
  members = membersCountOnly = managers = managersCountOnly = owners = ownersCountOnly = False
  customer = GC_Values[GC_CUSTOMER_ID]
  usedomain = usemember = usequery = None
  aliasDelimiter = ' '
  memberDelimiter = '\n'
  todrive = False
  cdfieldsList = []
  gsfieldsList = []
  fieldsTitles = {}
  titles = []
  csvRows = []
  addFieldTitleToCSVfile('email', GROUP_ARGUMENT_TO_PROPERTY_TITLE_MAP, cdfieldsList, fieldsTitles, titles)
  maxResults = None
  roles = []
  getSettings = sortHeaders = False
  while i < len(sys.argv):
    myarg = sys.argv[i].lower()
    if myarg == 'todrive':
      todrive = True
      i += 1
    elif myarg == 'domain':
      usedomain = sys.argv[i+1].lower()
      customer = None
      i += 2
    elif myarg == 'member':
      usemember = normalizeEmailAddressOrUID(sys.argv[i+1])
      customer = usequery = None
      i += 2
    elif myarg == 'query':
      usequery = sys.argv[i+1]
      usemember = None
      i += 2
    elif myarg == 'maxresults':
      maxResults = getInteger(sys.argv[i+1], myarg, minVal=0)
      i += 2
    elif myarg == 'delimiter':
      aliasDelimiter = memberDelimiter = sys.argv[i+1]
      i += 2
    elif myarg in GROUP_ARGUMENT_TO_PROPERTY_TITLE_MAP:
      addFieldTitleToCSVfile(myarg, GROUP_ARGUMENT_TO_PROPERTY_TITLE_MAP, cdfieldsList, fieldsTitles, titles)
      i += 1
    elif myarg == 'settings':
      getSettings = True
      i += 1
    elif myarg == 'allfields':
      getSettings = sortHeaders = True
      cdfieldsList = []
      gsfieldsList = []
      fieldsTitles = {}
      for field in GROUP_ARGUMENT_TO_PROPERTY_TITLE_MAP:
        addFieldTitleToCSVfile(field, GROUP_ARGUMENT_TO_PROPERTY_TITLE_MAP, cdfieldsList, fieldsTitles, titles)
      i += 1
    elif myarg == 'sortheaders':
      sortHeaders = True
      i += 1
    elif myarg == 'fields':
      fieldNameList = sys.argv[i+1]
      for field in fieldNameList.lower().replace(',', ' ').split():
        if field in GROUP_ARGUMENT_TO_PROPERTY_TITLE_MAP:
          addFieldTitleToCSVfile(field, GROUP_ARGUMENT_TO_PROPERTY_TITLE_MAP, cdfieldsList, fieldsTitles, titles)
        elif field in GROUP_ATTRIBUTES_ARGUMENT_TO_PROPERTY_MAP:
          addFieldToCSVfile(field, {field: [GROUP_ATTRIBUTES_ARGUMENT_TO_PROPERTY_MAP[field]]}, gsfieldsList, fieldsTitles, titles)
        elif field == 'collaborative':
          for attrName in COLLABORATIVE_INBOX_ATTRIBUTES:
            addFieldToCSVfile(attrName, {attrName: [attrName]}, gsfieldsList, fieldsTitles, titles)
        else:
          systemErrorExit(2, '%s is not a valid argument for "gam print groups fields"' % field)
      i += 2
    elif myarg in ['members', 'memberscount']:
      roles.append(ROLE_MEMBER)
      members = True
      if myarg == 'memberscount':
        membersCountOnly = True
      i += 1
    elif myarg in ['owners', 'ownerscount']:
      roles.append(ROLE_OWNER)
      owners = True
      if myarg == 'ownerscount':
        ownersCountOnly = True
      i += 1
    elif myarg in ['managers', 'managerscount']:
      roles.append(ROLE_MANAGER)
      managers = True
      if myarg == 'managerscount':
        managersCountOnly = True
      i += 1
    else:
      systemErrorExit(2, '%s is not a valid argument for "gam print groups"' % sys.argv[i])
  cdfields = ','.join(set(cdfieldsList))
  if gsfieldsList:
    getSettings = True
    gsfields = ','.join(set(gsfieldsList))
  elif getSettings:
    gsfields = None
  if getSettings:
    gs = buildGAPIObject('groupssettings')
  roles = ','.join(sorted(set(roles)))
  if roles:
    if members:
      addTitlesToCSVfile(['MembersCount',], titles)
      if not membersCountOnly:
        addTitlesToCSVfile(['Members',], titles)
    if managers:
      addTitlesToCSVfile(['ManagersCount',], titles)
      if not managersCountOnly:
        addTitlesToCSVfile(['Managers',], titles)
    if owners:
      addTitlesToCSVfile(['OwnersCount',], titles)
      if not ownersCountOnly:
        addTitlesToCSVfile(['Owners',], titles)
  printGettingAllItems('Groups', None)
  page_message = 'Got %%num_items%% Groups: %%first_item%% - %%last_item%%\n'
  entityList = callGAPIpages(cd.groups(), 'list', 'groups',
                             page_message=page_message, message_attribute='email',
                             customer=customer, domain=usedomain, userKey=usemember, query=usequery,
                             fields='nextPageToken,groups({0})'.format(cdfields),
                             maxResults=maxResults)
  i = 0
  count = len(entityList)
  for groupEntity in entityList:
    i += 1
    groupEmail = groupEntity['email']
    group = {}
    for field in cdfieldsList:
      if field in groupEntity:
        if isinstance(groupEntity[field], list):
          group[fieldsTitles[field]] = aliasDelimiter.join(groupEntity[field])
        else:
          group[fieldsTitles[field]] = groupEntity[field]
    if roles:
      sys.stderr.write(' Getting %s for %s (%s/%s)\n' % (roles, groupEmail, i, count))
      page_message = '  Got %%num_items%% members: %%first_item%% - %%last_item%%\n'
      validRoles, listRoles, listFields = _getRoleVerification(roles, 'nextPageToken,members(email,id,role)')
      groupMembers = callGAPIpages(cd.members(), 'list', 'members',
                                   page_message=page_message, message_attribute='email',
                                   soft_errors=True,
                                   groupKey=groupEmail, roles=listRoles, fields=listFields, maxResults=GC_Values[GC_MEMBER_MAX_RESULTS])
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
        member_email = member.get('email', member.get('id', None))
        if not member_email:
          sys.stderr.write(' Not sure what to do with: %s' % member)
          continue
        role = member.get('role', ROLE_MEMBER)
        if not validRoles or role in validRoles:
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
      if members:
        group['MembersCount'] = membersCount
        if not membersCountOnly:
          group['Members'] = memberDelimiter.join(membersList)
      if managers:
        group['ManagersCount'] = managersCount
        if not managersCountOnly:
          group['Managers'] = memberDelimiter.join(managersList)
      if owners:
        group['OwnersCount'] = ownersCount
        if not ownersCountOnly:
          group['Owners'] = memberDelimiter.join(ownersList)
    if getSettings and not GroupIsAbuseOrPostmaster(groupEmail):
      sys.stderr.write(" Retrieving Settings for group %s (%s/%s)...\r\n" % (groupEmail, i, count))
      settings = callGAPI(gs.groups(), 'get',
                          soft_errors=True,
                          retry_reasons=['serviceLimit', 'invalid'],
                          groupUniqueId=groupEmail, fields=gsfields)
      if settings:
        for key in settings:
          if key in ['email', 'name', 'description', 'kind', 'etag']:
            continue
          setting_value = settings[key]
          if setting_value is None:
            setting_value = ''
          if key not in titles:
            addTitleToCSVfile(key, titles)
          group[key] = setting_value
      else:
        sys.stderr.write(" Settings unavailable for group %s (%s/%s)...\r\n" % (groupEmail, i, count))
    csvRows.append(group)
  if sortHeaders:
    sortCSVTitles(['Email',], titles)
  writeCSVfile(csvRows, titles, 'Groups', todrive)

def doPrintOrgs():
  print_order = ['orgUnitPath', 'orgUnitId', 'name', 'description',
                 'parentOrgUnitPath', 'parentOrgUnitId', 'blockInheritance']
  cd = buildGAPIObject('directory')
  listType = 'all'
  orgUnitPath = "/"
  todrive = False
  fields = ['orgUnitPath', 'name', 'orgUnitId', 'parentOrgUnitId']
  titles = []
  csvRows = []
  parentOrgIds = []
  retrievedOrgIds = []
  i = 3
  while i < len(sys.argv):
    myarg = sys.argv[i].lower().replace('_', '')
    if myarg == 'todrive':
      todrive = True
      i += 1
    elif myarg == 'toplevelonly':
      listType = 'children'
      i += 1
    elif myarg == 'fromparent':
      orgUnitPath = getOrgUnitItem(sys.argv[i+1])
      i += 2
    elif myarg == 'allfields':
      fields = None
      i += 1
    elif myarg == 'fields':
      fields += sys.argv[i+1].split(',')
      i += 2
    else:
      systemErrorExit(2, '%s is not a valid argument for "gam print orgs"' % sys.argv[i])
  printGettingAllItems('Organizational Units', None)
  if fields:
    get_fields = ','.join(fields)
    list_fields = 'organizationUnits(%s)' % get_fields
  else:
    list_fields = None
    get_fields = None
  orgs = callGAPI(cd.orgunits(), 'list',
                  customerId=GC_Values[GC_CUSTOMER_ID], type=listType, orgUnitPath=orgUnitPath, fields=list_fields)
  if not 'organizationUnits' in orgs:
    topLevelOrgId = getTopLevelOrgId(cd, orgUnitPath)
    if topLevelOrgId:
      parentOrgIds.append(topLevelOrgId)
    orgunits = []
  else:
    orgunits = orgs['organizationUnits']
  for row in orgunits:
    retrievedOrgIds.append(row['orgUnitId'])
    if row['parentOrgUnitId'] not in parentOrgIds:
      parentOrgIds.append(row['parentOrgUnitId'])
  missing_parents = set(parentOrgIds) - set(retrievedOrgIds)
  for missing_parent in missing_parents:
    try:
      result = callGAPI(cd.orgunits(), 'get', throw_reasons=['required'],
                        customerId=GC_Values[GC_CUSTOMER_ID], orgUnitPath=missing_parent, fields=get_fields)
      orgunits.append(result)
    except:
      pass
  for row in orgunits:
    orgEntity = {}
    for key, value in list(row.items()):
      if key in ['kind', 'etag', 'etags']:
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
  csvRows.sort(key=lambda x: x['orgUnitPath'].lower(), reverse=False)
  writeCSVfile(csvRows, titles, 'Orgs', todrive)

def doPrintAliases():
  cd = buildGAPIObject('directory')
  todrive = False
  titles = ['Alias', 'Target', 'TargetType']
  csvRows = []
  userFields = ['primaryEmail', 'aliases']
  groupFields = ['email', 'aliases']
  doGroups = doUsers = True
  queries = [None]
  i = 3
  while i < len(sys.argv):
    myarg = sys.argv[i].lower().replace('_', '')
    if myarg == 'todrive':
      todrive = True
      i += 1
    elif myarg == 'shownoneditable':
      titles.insert(1, 'NonEditableAlias')
      userFields.append('nonEditableAliases')
      groupFields.append('nonEditableAliases')
      i += 1
    elif myarg == 'nogroups':
      doGroups = False
      i += 1
    elif myarg == 'nousers':
      doUsers = False
      i += 1
    elif myarg in ['query', 'queries']:
      queries = getQueries(myarg, sys.argv[i+1])
      doGroups = False
      doUsers = True
      i += 2
    else:
      systemErrorExit(2, '%s is not a valid argument for "gam print aliases"' % sys.argv[i])
  if doUsers:
    for query in queries:
      printGettingAllItems('User Aliases', query)
      page_message = 'Got %%num_items%% Users %%first_item%% - %%last_item%%\n'
      all_users = callGAPIpages(cd.users(), 'list', 'users', page_message=page_message,
                                message_attribute='primaryEmail', customer=GC_Values[GC_CUSTOMER_ID], query=query,
                                fields='nextPageToken,users({0})'.format(','.join(userFields)), maxResults=GC_Values[GC_USER_MAX_RESULTS])
      for user in all_users:
        for alias in user.get('aliases', []):
          csvRows.append({'Alias': alias, 'Target': user['primaryEmail'], 'TargetType': 'User'})
        for alias in user.get('nonEditableAliases', []):
          csvRows.append({'NonEditableAlias': alias, 'Target': user['primaryEmail'], 'TargetType': 'User'})
  if doGroups:
    printGettingAllItems('Group Aliases', None)
    page_message = 'Got %%num_items%% Groups %%first_item%% - %%last_item%%\n'
    all_groups = callGAPIpages(cd.groups(), 'list', 'groups', page_message=page_message,
                               message_attribute='email', customer=GC_Values[GC_CUSTOMER_ID],
                               fields='nextPageToken,groups({0})'.format(','.join(groupFields)))
    for group in all_groups:
      for alias in group.get('aliases', []):
        csvRows.append({'Alias': alias, 'Target': group['email'], 'TargetType': 'Group'})
      for alias in group.get('nonEditableAliases', []):
        csvRows.append({'NonEditableAlias': alias, 'Target': group['email'], 'TargetType': 'Group'})
  writeCSVfile(csvRows, titles, 'Aliases', todrive)

def doPrintGroupMembers():
  cd = buildGAPIObject('directory')
  todrive = False
  membernames = False
  customer = GC_Values[GC_CUSTOMER_ID]
  checkSuspended = usedomain = usemember = usequery = None
  roles = []
  fields = 'nextPageToken,members(email,id,role,status,type)'
  titles = ['group']
  csvRows = []
  groups_to_get = []
  i = 3
  while i < len(sys.argv):
    myarg = sys.argv[i].lower().replace('_', '')
    if myarg == 'todrive':
      todrive = True
      i += 1
    elif myarg == 'domain':
      usedomain = sys.argv[i+1].lower()
      customer = None
      i += 2
    elif myarg == 'member':
      usemember = normalizeEmailAddressOrUID(sys.argv[i+1])
      customer = usequery = None
      i += 2
    elif myarg == 'query':
      usequery = sys.argv[i+1]
      usemember = None
      i += 2
    elif myarg == 'fields':
      memberFieldsList = sys.argv[i+1].replace(',', ' ').lower().split()
      fields = 'nextPageToken,members(%s)' % (','.join(memberFieldsList))
      i += 2
    elif myarg == 'membernames':
      membernames = True
      titles.append('name')
      i += 1
    elif myarg in ['role', 'roles']:
      for role in sys.argv[i+1].lower().replace(',', ' ').split():
        if role in GROUP_ROLES_MAP:
          roles.append(GROUP_ROLES_MAP[role])
        else:
          systemErrorExit(2, '%s is not a valid role for "gam print group-members %s"' % (role, myarg))
      i += 2
    elif myarg in ['group', 'groupns', 'groupsusp']:
      group_email = normalizeEmailAddressOrUID(sys.argv[i+1])
      groups_to_get = [{'email': group_email}]
      if myarg == 'groupns':
        checkSuspended = False
      elif myarg == 'groupsusp':
        checkSuspended = True
      i += 2
    elif myarg in ['suspended', 'notsuspended']:
      checkSuspended = myarg == 'suspended'
      i += 1
    else:
      systemErrorExit(2, '%s is not a valid argument for "gam print group-members"' % sys.argv[i])
  if not groups_to_get:
    groups_to_get = callGAPIpages(cd.groups(), 'list', 'groups', message_attribute='email',
                                  customer=customer, domain=usedomain, userKey=usemember, query=usequery,
                                  fields='nextPageToken,groups(email)')
  i = 0
  count = len(groups_to_get)
  for group in groups_to_get:
    i += 1
    group_email = group['email']
    sys.stderr.write('Getting members for %s (%s/%s)\n' % (group_email, i, count))
    validRoles, listRoles, listFields = _getRoleVerification(','.join(roles), fields)
    group_members = callGAPIpages(cd.members(), 'list', 'members',
                                  soft_errors=True,
                                  groupKey=group_email, roles=listRoles, fields=listFields, maxResults=GC_Values[GC_MEMBER_MAX_RESULTS])
    for member in group_members:
      if ((validRoles and member.get('role', ROLE_MEMBER) not in validRoles) or
          (checkSuspended is not None and ((not checkSuspended and member['status'] == 'SUSPENDED') or (checkSuspended and member['status'] != 'SUSPENDED')))):
        continue
      for title in member:
        if title not in titles:
          titles.append(title)
      member['group'] = group_email
      if membernames and 'type' in member and 'id' in member:
        if member['type'] == 'USER':
          try:
            mbinfo = callGAPI(cd.users(), 'get',
                              throw_reasons=[GAPI_USER_NOT_FOUND, GAPI_NOT_FOUND, GAPI_FORBIDDEN],
                              userKey=member['id'], fields='name')
            memberName = mbinfo['name']['fullName']
          except (GAPI_userNotFound, GAPI_notFound, GAPI_forbidden):
            memberName = 'Unknown'
        elif member['type'] == 'GROUP':
          try:
            mbinfo = callGAPI(cd.groups(), 'get',
                              throw_reasons=[GAPI_NOT_FOUND, GAPI_FORBIDDEN],
                              groupKey=member['id'], fields='name')
            memberName = mbinfo['name']
          except (GAPI_notFound, GAPI_forbidden):
            memberName = 'Unknown'
        elif member['type'] == 'CUSTOMER':
          try:
            mbinfo = callGAPI(cd.customers(), 'get',
                              throw_reasons=[GAPI_BAD_REQUEST, GAPI_RESOURCE_NOT_FOUND, GAPI_FORBIDDEN],
                              customerKey=member['id'], fields='customerDomain')
            memberName = mbinfo['customerDomain']
          except (GAPI_badRequest, GAPI_resourceNotFound, GAPI_forbidden):
            memberName = 'Unknown'
        else:
          memberName = 'Unknown'
        member['name'] = memberName
      csvRows.append(member)
  writeCSVfile(csvRows, titles, 'Group Members', todrive)

def doPrintVaultMatters():
  v = buildGAPIObject('vault')
  todrive = False
  csvRows = []
  initialTitles = ['matterId', 'name', 'description', 'state']
  titles = initialTitles[:]
  view = 'FULL'
  i = 3
  while i < len(sys.argv):
    myarg = sys.argv[i].lower().replace('_', '')
    if myarg == 'todrive':
      todrive = True
      i += 1
    elif myarg in PROJECTION_CHOICES_MAP:
      view = PROJECTION_CHOICES_MAP[myarg]
      i += 1
    else:
      systemErrorExit(3, '%s is not a valid argument to "gam print matters"' % myarg)
  printGettingAllItems('Vault Matters', None)
  page_message = 'Got %%num_items%% Vault Matters...\n'
  matters = callGAPIpages(v.matters(), 'list', 'matters', page_message=page_message, view=view)
  for matter in matters:
    addRowTitlesToCSVfile(flatten_json(matter), csvRows, titles)
  sortCSVTitles(initialTitles, titles)
  writeCSVfile(csvRows, titles, 'Vault Matters', todrive)

def doPrintVaultExports():
  v = buildGAPIObject('vault')
  todrive = False
  csvRows = []
  initialTitles = ['matterId', 'id', 'name', 'createTime', 'status']
  titles = initialTitles[:]
  matters = []
  matterIds = []
  i = 3
  while i < len(sys.argv):
    myarg = sys.argv[i].lower().replace('_', '')
    if myarg == 'todrive':
      todrive = True
      i += 1
    elif myarg in ['matter', 'matters']:
      matters = sys.argv[i+1].split(',')
      i += 2
    else:
      systemErrorExit(3, '%s is not a valid a valid argument to "gam print exports"' % myarg)
  if not matters:
    matters_results = callGAPIpages(v.matters(), 'list', 'matters', view='BASIC', fields='matters(matterId,state),nextPageToken')
    for matter in matters_results:
      if matter['state'] != 'OPEN':
        print('ignoring matter %s in state %s' % (matter['matterId'], matter['state']))
        continue
      matterIds.append(matter['matterId'])
  else:
    for matter in matters:
      matterIds.append(getMatterItem(v, matter))
  for matterId in matterIds:
    sys.stderr.write('Retrieving exports for matter %s\n' % matterId)
    exports = callGAPIpages(v.matters().exports(), 'list', 'exports', matterId=matterId)
    for export in exports:
      addRowTitlesToCSVfile(flatten_json(export, flattened={'matterId': matterId}), csvRows, titles)
  sortCSVTitles(initialTitles, titles)
  writeCSVfile(csvRows, titles, 'Vault Exports', todrive)

def doPrintVaultHolds():
  v = buildGAPIObject('vault')
  todrive = False
  csvRows = []
  initialTitles = ['matterId', 'holdId', 'name', 'corpus', 'updateTime']
  titles = initialTitles[:]
  matters = []
  matterIds = []
  i = 3
  while i < len(sys.argv):
    myarg = sys.argv[i].lower().replace('_', '')
    if myarg == 'todrive':
      todrive = True
      i += 1
    elif myarg in ['matter', 'matters']:
      matters = sys.argv[i+1].split(',')
      i += 2
    else:
      systemErrorExit(3, '%s is not a valid a valid argument to "gam print holds"' % myarg)
  if not matters:
    matters_results = callGAPIpages(v.matters(), 'list', 'matters', view='BASIC', fields='matters(matterId,state),nextPageToken')
    for matter in matters_results:
      if matter['state'] != 'OPEN':
        print('ignoring matter %s in state %s' % (matter['matterId'], matter['state']))
        continue
      matterIds.append(matter['matterId'])
  else:
    for matter in matters:
      matterIds.append(getMatterItem(v, matter))
  for matterId in matterIds:
    sys.stderr.write('Retrieving holds for matter %s\n' % matterId)
    holds = callGAPIpages(v.matters().holds(), 'list', 'holds', matterId=matterId)
    for hold in holds:
      addRowTitlesToCSVfile(flatten_json(hold, flattened={'matterId': matterId}), csvRows, titles)
  sortCSVTitles(initialTitles, titles)
  writeCSVfile(csvRows, titles, 'Vault Holds', todrive)

def doPrintMobileDevices():
  cd = buildGAPIObject('directory')
  todrive = False
  titles = []
  csvRows = []
  fields = None
  projection = orderBy = sortOrder = None
  queries = [None]
  delimiter = ' '
  listLimit = 1
  appsLimit = -1
  i = 3
  while i < len(sys.argv):
    myarg = sys.argv[i].lower().replace('_', '')
    if myarg == 'todrive':
      todrive = True
      i += 1
    elif myarg in ['query', 'queries']:
      queries = getQueries(myarg, sys.argv[i+1])
      i += 2
    elif myarg == 'delimiter':
      delimiter = sys.argv[i+1]
      i += 2
    elif myarg == 'listlimit':
      listLimit = getInteger(sys.argv[i+1], myarg, minVal=-1)
      i += 2
    elif myarg == 'appslimit':
      appsLimit = getInteger(sys.argv[i+1], myarg, minVal=-1)
      i += 2
    elif myarg == 'fields':
      fields = 'nextPageToken,mobiledevices(%s)' % sys.argv[i+1]
      i += 2
    elif myarg == 'orderby':
      orderBy = sys.argv[i+1].lower()
      allowed_values = ['deviceid', 'email', 'lastsync', 'model', 'name', 'os', 'status', 'type']
      if orderBy.lower() not in allowed_values:
        systemErrorExit(2, 'orderBy must be one of %s; got %s' % (', '.join(allowed_values), orderBy))
      elif orderBy == 'lastsync':
        orderBy = 'lastSync'
      elif orderBy == 'deviceid':
        orderBy = 'deviceId'
      i += 2
    elif myarg in SORTORDER_CHOICES_MAP:
      sortOrder = SORTORDER_CHOICES_MAP[myarg]
      i += 1
    elif myarg in PROJECTION_CHOICES_MAP:
      projection = PROJECTION_CHOICES_MAP[myarg]
      i += 1
    else:
      systemErrorExit(2, '%s is not a valid argument for "gam print mobile"' % sys.argv[i])
  for query in queries:
    printGettingAllItems('Mobile Devices', query)
    page_message = 'Got %%num_items%% Mobile Devices...\n'
    all_mobile = callGAPIpages(cd.mobiledevices(), 'list', 'mobiledevices', page_message=page_message,
                               customerId=GC_Values[GC_CUSTOMER_ID], query=query, projection=projection, fields=fields,
                               orderBy=orderBy, sortOrder=sortOrder, maxResults=GC_Values[GC_DEVICE_MAX_RESULTS])
    for mobile in all_mobile:
      row = {}
      for attrib in mobile:
        if attrib in ['kind', 'etag']:
          continue
        if attrib in ['name', 'email', 'otherAccountsInfo']:
          if attrib not in titles:
            titles.append(attrib)
          if listLimit > 0:
            row[attrib] = delimiter.join(mobile[attrib][0:listLimit])
          elif listLimit == 0:
            row[attrib] = delimiter.join(mobile[attrib])
        elif attrib == 'applications':
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
              for field in ['displayName', 'packageName', 'versionName']:
                appDetails.append(app.get(field, '<None>'))
              appDetails.append(str(app.get('versionCode', '<None>')))
              permissions = app.get('permission', [])
              if permissions:
                appDetails.append('/'.join(permissions))
              else:
                appDetails.append('<None>')
              applications.append('-'.join(appDetails))
            row[attrib] = delimiter.join(applications)
        else:
          if attrib not in titles:
            titles.append(attrib)
          row[attrib] = mobile[attrib]
      csvRows.append(row)
  sortCSVTitles(['resourceId', 'deviceId', 'serialNumber', 'name', 'email', 'status'], titles)
  writeCSVfile(csvRows, titles, 'Mobile', todrive)

def doPrintCrosActivity():
  cd = buildGAPIObject('directory')
  todrive = False
  titles = ['deviceId', 'annotatedAssetId', 'annotatedLocation', 'serialNumber', 'orgUnitPath']
  csvRows = []
  fieldsList = ['deviceId', 'annotatedAssetId', 'annotatedLocation', 'serialNumber', 'orgUnitPath']
  startDate = endDate = None
  selectActiveTimeRanges = selectDeviceFiles = selectRecentUsers = False
  listLimit = 0
  delimiter = ','
  orgUnitPath = None
  queries = [None]
  i = 3
  while i < len(sys.argv):
    myarg = sys.argv[i].lower().replace('_', '')
    if myarg in ['query', 'queries']:
      queries = getQueries(myarg, sys.argv[i+1])
      i += 2
    elif myarg == 'limittoou':
      orgUnitPath = getOrgUnitItem(sys.argv[i+1])
      i += 2
    elif myarg == 'todrive':
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
    elif myarg == 'both':
      selectActiveTimeRanges = selectRecentUsers = True
      i += 1
    elif myarg == 'all':
      selectActiveTimeRanges = selectDeviceFiles = selectRecentUsers = True
      i += 1
    elif myarg in CROS_START_ARGUMENTS:
      startDate = _getFilterDate(sys.argv[i+1])
      i += 2
    elif myarg in CROS_END_ARGUMENTS:
      endDate = _getFilterDate(sys.argv[i+1])
      i += 2
    elif myarg == 'listlimit':
      listLimit = getInteger(sys.argv[i+1], myarg, minVal=0)
      i += 2
    elif myarg == 'delimiter':
      delimiter = sys.argv[i+1]
      i += 2
    else:
      systemErrorExit(2, '%s is not a valid argument for "gam print crosactivity"' % sys.argv[i])
  if not selectActiveTimeRanges and not selectDeviceFiles and not selectRecentUsers:
    selectActiveTimeRanges = selectRecentUsers = True
  if selectRecentUsers:
    fieldsList.append('recentUsers')
    addTitlesToCSVfile(['recentUsers.email',], titles)
  if selectActiveTimeRanges:
    fieldsList.append('activeTimeRanges')
    addTitlesToCSVfile(['activeTimeRanges.date', 'activeTimeRanges.duration', 'activeTimeRanges.minutes'], titles)
  if selectDeviceFiles:
    fieldsList.append('deviceFiles')
    addTitlesToCSVfile(['deviceFiles.type', 'deviceFiles.createTime'], titles)
  fields = 'chromeosdevices(%s),nextPageToken' % ','.join(fieldsList)
  for query in queries:
    printGettingAllItems('CrOS Devices', query)
    page_message = 'Got %%num_items%% CrOS Devices...\n'
    all_cros = callGAPIpages(cd.chromeosdevices(), 'list', 'chromeosdevices', page_message=page_message,
                             query=query, customerId=GC_Values[GC_CUSTOMER_ID], projection='FULL',
                             fields=fields, maxResults=GC_Values[GC_DEVICE_MAX_RESULTS], orgUnitPath=orgUnitPath)
    for cros in all_cros:
      row = {}
      for attrib in cros:
        if attrib not in ['recentUsers', 'activeTimeRanges', 'deviceFiles']:
          row[attrib] = cros[attrib]
      if selectActiveTimeRanges:
        activeTimeRanges = _filterTimeRanges(cros.get('activeTimeRanges', []), startDate, endDate)
        lenATR = len(activeTimeRanges)
        for activeTimeRange in activeTimeRanges[:min(lenATR, listLimit or lenATR)]:
          new_row = row.copy()
          new_row['activeTimeRanges.date'] = activeTimeRange['date']
          new_row['activeTimeRanges.duration'] = utils.formatMilliSeconds(activeTimeRange['activeTime'])
          new_row['activeTimeRanges.minutes'] = activeTimeRange['activeTime']/60000
          csvRows.append(new_row)
      if selectRecentUsers:
        recentUsers = cros.get('recentUsers', [])
        lenRU = len(recentUsers)
        row['recentUsers.email'] = delimiter.join([recent_user.get('email', ['Unknown', 'UnmanagedUser'][recent_user['type'] == 'USER_TYPE_UNMANAGED']) for recent_user in recentUsers[:min(lenRU, listLimit or lenRU)]])
        csvRows.append(row)
      if selectDeviceFiles:
        deviceFiles = _filterCreateReportTime(cros.get('deviceFiles', []), 'createTime', startDate, endDate)
        lenDF = len(deviceFiles)
        for deviceFile in deviceFiles[:min(lenDF, listLimit or lenDF)]:
          new_row = row.copy()
          new_row['deviceFiles.type'] = deviceFile['type']
          new_row['deviceFiles.createTime'] = deviceFile['createTime']
          csvRows.append(new_row)
  writeCSVfile(csvRows, titles, 'CrOS Activity', todrive)

def _checkTPMVulnerability(cros):
  if 'tpmVersionInfo' in cros and 'firmwareVersion' in cros['tpmVersionInfo']:
    if cros['tpmVersionInfo']['firmwareVersion'] in CROS_TPM_VULN_VERSIONS:
      cros['tpmVersionInfo']['tpmVulnerability'] = 'VULNERABLE'
    elif cros['tpmVersionInfo']['firmwareVersion'] in CROS_TPM_FIXED_VERSIONS:
      cros['tpmVersionInfo']['tpmVulnerability'] = 'UPDATED'
    else:
      cros['tpmVersionInfo']['tpmVulnerability'] = 'NOT IMPACTED'
  return cros

def doPrintCrosDevices():
  def _getSelectedLists(myarg):
    if myarg in CROS_ACTIVE_TIME_RANGES_ARGUMENTS:
      selectedLists['activeTimeRanges'] = True
    elif myarg in CROS_RECENT_USERS_ARGUMENTS:
      selectedLists['recentUsers'] = True
    elif myarg in CROS_DEVICE_FILES_ARGUMENTS:
      selectedLists['deviceFiles'] = True
    elif myarg in CROS_CPU_STATUS_REPORTS_ARGUMENTS:
      selectedLists['cpuStatusReports'] = True
    elif myarg in CROS_DISK_VOLUME_REPORTS_ARGUMENTS:
      selectedLists['diskVolumeReports'] = True
    elif myarg in CROS_SYSTEM_RAM_FREE_REPORTS_ARGUMENTS:
      selectedLists['systemRamFreeReports'] = True

  cd = buildGAPIObject('directory')
  todrive = False
  fieldsList = []
  fieldsTitles = {}
  titles = []
  csvRows = []
  addFieldToCSVfile('deviceid', CROS_ARGUMENT_TO_PROPERTY_MAP, fieldsList, fieldsTitles, titles)
  projection = orderBy = sortOrder = orgUnitPath = None
  queries = [None]
  noLists = sortHeaders = False
  selectedLists = {}
  startDate = endDate = None
  listLimit = 0
  i = 3
  while i < len(sys.argv):
    myarg = sys.argv[i].lower().replace('_', '')
    if myarg in ['query', 'queries']:
      queries = getQueries(myarg, sys.argv[i+1])
      i += 2
    elif myarg == 'limittoou':
      orgUnitPath = getOrgUnitItem(sys.argv[i+1])
      i += 2
    elif myarg == 'todrive':
      todrive = True
      i += 1
    elif myarg == 'nolists':
      noLists = True
      selectedLists = {}
      i += 1
    elif myarg in CROS_START_ARGUMENTS:
      startDate = _getFilterDate(sys.argv[i+1])
      i += 2
    elif myarg in CROS_END_ARGUMENTS:
      endDate = _getFilterDate(sys.argv[i+1])
      i += 2
    elif myarg == 'listlimit':
      listLimit = getInteger(sys.argv[i+1], myarg, minVal=0)
      i += 2
    elif myarg == 'orderby':
      orderBy = sys.argv[i+1].lower().replace('_', '')
      allowed_values = ['location', 'user', 'lastsync', 'notes', 'serialnumber', 'status', 'supportenddate']
      if orderBy not in allowed_values:
        systemErrorExit(2, 'orderBy must be one of %s; got %s' % (', '.join(allowed_values), orderBy))
      elif orderBy == 'location':
        orderBy = 'annotatedLocation'
      elif orderBy == 'user':
        orderBy = 'annotatedUser'
      elif orderBy == 'lastsync':
        orderBy = 'lastSync'
      elif orderBy == 'serialnumber':
        orderBy = 'serialNumber'
      elif orderBy == 'supportenddate':
        orderBy = 'supportEndDate'
      i += 2
    elif myarg in SORTORDER_CHOICES_MAP:
      sortOrder = SORTORDER_CHOICES_MAP[myarg]
      i += 1
    elif myarg in PROJECTION_CHOICES_MAP:
      projection = PROJECTION_CHOICES_MAP[myarg]
      sortHeaders = True
      if projection == 'FULL':
        fieldsList = []
      else:
        fieldsList = CROS_BASIC_FIELDS_LIST[:]
      i += 1
    elif myarg == 'allfields':
      projection = 'FULL'
      sortHeaders = True
      fieldsList = []
      i += 1
    elif myarg == 'sortheaders':
      sortHeaders = True
      i += 1
    elif myarg in CROS_LISTS_ARGUMENTS:
      _getSelectedLists(myarg)
      i += 1
    elif myarg in CROS_ARGUMENT_TO_PROPERTY_MAP:
      addFieldToFieldsList(myarg, CROS_ARGUMENT_TO_PROPERTY_MAP, fieldsList)
      i += 1
    elif myarg == 'fields':
      fieldNameList = sys.argv[i+1]
      for field in fieldNameList.lower().replace(',', ' ').split():
        if field in CROS_LISTS_ARGUMENTS:
          _getSelectedLists(field)
        elif field in CROS_ARGUMENT_TO_PROPERTY_MAP:
          addFieldToFieldsList(field, CROS_ARGUMENT_TO_PROPERTY_MAP, fieldsList)
        else:
          systemErrorExit(2, '%s is not a valid argument for "gam print cros fields"' % field)
      i += 2
    else:
      systemErrorExit(2, '%s is not a valid argument for "gam print cros"' % sys.argv[i])
  if selectedLists:
    noLists = False
    projection = 'FULL'
    for selectList in selectedLists:
      addFieldToFieldsList(selectList, CROS_ARGUMENT_TO_PROPERTY_MAP, fieldsList)
  if fieldsList:
    fieldsList.append('deviceId')
    fields = 'nextPageToken,chromeosdevices({0})'.format(','.join(set(fieldsList))).replace('.', '/')
  else:
    fields = None
  for query in queries:
    printGettingAllItems('CrOS Devices', query)
    page_message = 'Got %%num_items%% CrOS Devices...\n'
    all_cros = callGAPIpages(cd.chromeosdevices(), 'list', 'chromeosdevices', page_message=page_message,
                             query=query, customerId=GC_Values[GC_CUSTOMER_ID], projection=projection, orgUnitPath=orgUnitPath,
                             orderBy=orderBy, sortOrder=sortOrder, fields=fields, maxResults=GC_Values[GC_DEVICE_MAX_RESULTS])
    for cros in all_cros:
      cros = _checkTPMVulnerability(cros)
    if not noLists and not selectedLists:
      for cros in all_cros:
        if 'notes' in cros:
          cros['notes'] = cros['notes'].replace('\n', '\\n')
        for cpuStatusReport in cros.get('cpuStatusReports', []):
          for tempInfo in cpuStatusReport.get('cpuTemperatureInfo', []):
            tempInfo['label'] = tempInfo['label'].strip()
        addRowTitlesToCSVfile(flatten_json(cros, listLimit=listLimit), csvRows, titles)
      continue
    for cros in all_cros:
      if 'notes' in cros:
        cros['notes'] = cros['notes'].replace('\n', '\\n')
      row = {}
      for attrib in cros:
        if attrib not in set(['kind', 'etag', 'tpmVersionInfo', 'recentUsers', 'activeTimeRanges',
                              'deviceFiles', 'cpuStatusReports', 'diskVolumeReports', 'systemRamFreeReports']):
          row[attrib] = cros[attrib]
      activeTimeRanges = _filterTimeRanges(cros.get('activeTimeRanges', []) if selectedLists.get('activeTimeRanges') else [], startDate, endDate)
      recentUsers = cros.get('recentUsers', []) if selectedLists.get('recentUsers') else []
      deviceFiles = _filterCreateReportTime(cros.get('deviceFiles', []) if selectedLists.get('deviceFiles') else [], 'createTime', startDate, endDate)
      cpuStatusReports = _filterCreateReportTime(cros.get('cpuStatusReports', []) if selectedLists.get('cpuStatusReports') else [], 'reportTime', startDate, endDate)
      diskVolumeReports = cros.get('diskVolumeReports', []) if selectedLists.get('diskVolumeReports') else []
      systemRamFreeReports = _filterCreateReportTime(cros.get('systemRamFreeReports', []) if selectedLists.get('systemRamFreeReports') else [], 'reportTime', startDate, endDate)
      if noLists or (not activeTimeRanges and not recentUsers and not deviceFiles and
                     not cpuStatusReports and not diskVolumeReports and not systemRamFreeReports):
        addRowTitlesToCSVfile(row, csvRows, titles)
        continue
      lenATR = len(activeTimeRanges)
      lenRU = len(recentUsers)
      lenDF = len(deviceFiles)
      lenCSR = len(cpuStatusReports)
      lenDVR = len(diskVolumeReports)
      lenSRFR = len(systemRamFreeReports)
      for i in range(min(max(lenATR, lenRU, lenDF, lenCSR, lenDVR, lenSRFR), listLimit or max(lenATR, lenRU, lenDF, lenCSR, lenDVR, lenSRFR))):
        new_row = row.copy()
        if i < lenATR:
          new_row['activeTimeRanges.date'] = activeTimeRanges[i]['date']
          new_row['activeTimeRanges.activeTime'] = str(activeTimeRanges[i]['activeTime'])
          new_row['activeTimeRanges.duration'] = utils.formatMilliSeconds(activeTimeRanges[i]['activeTime'])
          new_row['activeTimeRanges.minutes'] = activeTimeRanges[i]['activeTime']/60000
        if i < lenRU:
          new_row['recentUsers.email'] = recentUsers[i].get('email', ['Unknown', 'UnmanagedUser'][recentUsers[i]['type'] == 'USER_TYPE_UNMANAGED'])
          new_row['recentUsers.type'] = recentUsers[i]['type']
        if i < lenDF:
          new_row['deviceFiles.type'] = deviceFiles[i]['type']
          new_row['deviceFiles.createTime'] = deviceFiles[i]['createTime']
        if i < lenCSR:
          new_row['cpuStatusReports.reportTime'] = cpuStatusReports[i]['reportTime']
          for tempInfo in cpuStatusReports[i].get('cpuTemperatureInfo', []):
            new_row['cpuStatusReports.cpuTemperatureInfo.{0}'.format(tempInfo['label'].strip())] = tempInfo['temperature']
          new_row['cpuStatusReports.cpuUtilizationPercentageInfo'] = ','.join([str(x) for x in cpuStatusReports[i]['cpuUtilizationPercentageInfo']])
        if i < lenDVR:
          volumeInfo = diskVolumeReports[i]['volumeInfo']
          j = 0
          for volume in volumeInfo:
            new_row['diskVolumeReports.volumeInfo.{0}.volumeId'.format(j)] = volume['volumeId']
            new_row['diskVolumeReports.volumeInfo.{0}.storageFree'.format(j)] = volume['storageFree']
            new_row['diskVolumeReports.volumeInfo.{0}.storageTotal'.format(j)] = volume['storageTotal']
            j += 1
        if i < lenSRFR:
          new_row['systemRamFreeReports.reportTime'] = systemRamFreeReports[i]['reportTime']
          new_row['systenRamFreeReports.systemRamFreeInfo'] = ','.join([str(x) for x in systemRamFreeReports[i]['systemRamFreeInfo']])
        addRowTitlesToCSVfile(new_row, csvRows, titles)
  if sortHeaders:
    sortCSVTitles(['deviceId',], titles)
  writeCSVfile(csvRows, titles, 'CrOS', todrive)

def doPrintLicenses(returnFields=None, skus=None, countsOnly=False, returnCounts=False):
  lic = buildGAPIObject('licensing')
  products = []
  licenses = []
  licenseCounts = []
  if not returnFields:
    csvRows = []
    todrive = False
    i = 3
    while i < len(sys.argv):
      myarg = sys.argv[i].lower()
      if not returnCounts and myarg == 'todrive':
        todrive = True
        i += 1
      elif myarg in ['products', 'product']:
        products = sys.argv[i+1].split(',')
        i += 2
      elif myarg in ['sku', 'skus']:
        skus = sys.argv[i+1].split(',')
        i += 2
      elif myarg == 'allskus':
        skus = sorted(SKUS.keys())
        products = []
        i += 1
      elif myarg == 'gsuite':
        skus = [skuId for skuId in SKUS if SKUS[skuId]['product'] in ['Google-Apps', '101031']]
        products = []
        i += 1
      elif myarg == 'countsonly':
        countsOnly = True
        i += 1
      else:
        systemErrorExit(2, '%s is not a valid argument for "gam print licenses"' % sys.argv[i])
    if not countsOnly:
      fields = 'nextPageToken,items(productId,skuId,userId)'
      titles = ['userId', 'productId', 'skuId']
    else:
      fields = 'nextPageToken,items(userId)'
      if not returnCounts:
        if skus:
          titles = ['productId', 'skuId', 'licenses']
        else:
          titles = ['productId', 'licenses']
  else:
    fields = 'nextPageToken,items({0})'.format(returnFields)
  if skus:
    for sku in skus:
      product, sku = getProductAndSKU(sku)
      page_message = 'Got %%%%total_items%%%% Licenses for %s...\n' % sku
      try:
        licenses += callGAPIpages(lic.licenseAssignments(), 'listForProductAndSku', 'items', throw_reasons=[GAPI_INVALID, GAPI_FORBIDDEN], page_message=page_message,
                                  customerId=GC_Values[GC_DOMAIN], productId=product, skuId=sku, fields=fields)
        if countsOnly:
          licenseCounts.append(['Product', product, 'SKU', sku, 'Licenses', len(licenses)])
          licenses = []
      except (GAPI_invalid, GAPI_forbidden):
        pass
  else:
    if not products:
      for sku in list(SKUS.values()):
        if sku['product'] not in products:
          products.append(sku['product'])
      products.sort()
    for productId in products:
      page_message = 'Got %%%%total_items%%%% Licenses for %s...\n' % productId
      try:
        licenses += callGAPIpages(lic.licenseAssignments(), 'listForProduct', 'items', throw_reasons=[GAPI_INVALID, GAPI_FORBIDDEN], page_message=page_message,
                                  customerId=GC_Values[GC_DOMAIN], productId=productId, fields=fields)
        if countsOnly:
          licenseCounts.append(['Product', productId, 'Licenses', len(licenses)])
          licenses = []
      except (GAPI_invalid, GAPI_forbidden):
        pass
  if countsOnly:
    if returnCounts:
      return licenseCounts
    if skus:
      for u_license in licenseCounts:
        csvRows.append({'productId': u_license[1], 'skuId': u_license[3], 'licenses': u_license[5]})
    else:
      for u_license in licenseCounts:
        csvRows.append({'productId': u_license[1], 'licenses': u_license[3]})
    writeCSVfile(csvRows, titles, 'Licenses', todrive)
    return
  if returnFields:
    if returnFields == 'userId':
      userIds = []
      for u_license in licenses:
        userId = u_license.get('userId', '').lower()
        if userId:
          userIds.append(userId)
      return userIds
    userSkuIds = {}
    for u_license in licenses:
      userId = u_license.get('userId', '').lower()
      skuId = u_license.get('skuId')
      if userId and skuId:
        userSkuIds.setdefault(userId, [])
        userSkuIds[userId].append(skuId)
    return userSkuIds
  for u_license in licenses:
    userId = u_license.get('userId', '').lower()
    skuId = u_license.get('skuId', '')
    csvRows.append({'userId': userId, 'productId': u_license.get('productId', ''),
                    'skuId': _skuIdToDisplayName(skuId)})
  writeCSVfile(csvRows, titles, 'Licenses', todrive)

def doShowLicenses():
  licenseCounts = doPrintLicenses(countsOnly=True, returnCounts=True)
  for u_license in licenseCounts:
    line = ''
    for i in range(0, len(u_license), 2):
      line += '{0}: {1}, '.format(u_license[i], u_license[i+1])
    print(line[:-2])

RESCAL_DFLTFIELDS = ['id', 'name', 'email',]
RESCAL_ALLFIELDS = ['id', 'name', 'email', 'description', 'type', 'buildingid', 'category', 'capacity',
                    'features', 'floor', 'floorsection', 'generatedresourcename', 'uservisibledescription',]

RESCAL_ARGUMENT_TO_PROPERTY_MAP = {
  'description': ['resourceDescription'],
  'building': ['buildingId',],
  'buildingid': ['buildingId',],
  'capacity': ['capacity',],
  'category': ['resourceCategory',],
  'email': ['resourceEmail'],
  'feature': ['featureInstances',],
  'features': ['featureInstances',],
  'floor': ['floorName',],
  'floorname': ['floorName',],
  'floorsection': ['floorSection',],
  'generatedresourcename': ['generatedResourceName',],
  'id': ['resourceId'],
  'name': ['resourceName'],
  'type': ['resourceType'],
  'userdescription': ['userVisibleDescription',],
  'uservisibledescription': ['userVisibleDescription',],
  }

def doPrintFeatures():
  to_drive = False
  cd = buildGAPIObject('directory')
  titles = []
  csvRows = []
  fieldsList = ['name']
  fields = 'nextPageToken,features(%s)'
  possible_fields = {}
  for pfield in cd._rootDesc['schemas']['Feature']['properties']:
    possible_fields[pfield.lower()] = pfield
  i = 3
  while i < len(sys.argv):
    myarg = sys.argv[i].lower()
    if myarg == 'todrive':
      to_drive = True
      i += 1
    elif myarg == 'allfields':
      fields = None
      i += 1
    elif myarg in possible_fields:
      fieldsList.append(possible_fields[myarg])
      i += 1
    elif 'feature'+myarg in possible_fields:
      fieldsList.append(possible_fields['feature'+myarg])
      i += 1
    else:
      systemErrorExit(3, '%s is not a valid argument to "gam print features"' % sys.argv[i])
  if fields:
    fields = fields % ','.join(fieldsList)
  features = callGAPIpages(cd.resources().features(), 'list', 'features',
                           customer=GC_Values[GC_CUSTOMER_ID], fields=fields)
  for feature in features:
    feature.pop('etags', None)
    feature.pop('etag', None)
    feature.pop('kind', None)
    feature = flatten_json(feature)
    for item in feature:
      if item not in titles:
        titles.append(item)
    csvRows.append(feature)
  sortCSVTitles('name', titles)
  writeCSVfile(csvRows, titles, 'Features', to_drive)

def doPrintBuildings():
  to_drive = False
  cd = buildGAPIObject('directory')
  titles = []
  csvRows = []
  fieldsList = ['buildingId']
  # buildings.list() currently doesn't support paging
  # but should soon, attempt to use it now so we
  # won't break when it's turned on.
  fields = 'nextPageToken,buildings(%s)'
  possible_fields = {}
  for pfield in cd._rootDesc['schemas']['Building']['properties']:
    possible_fields[pfield.lower()] = pfield
  i = 3
  while i < len(sys.argv):
    myarg = sys.argv[i].lower()
    if myarg == 'todrive':
      to_drive = True
      i += 1
    elif myarg == 'allfields':
      fields = None
      i += 1
    elif myarg in possible_fields:
      fieldsList.append(possible_fields[myarg])
      i += 1
    # Allows shorter arguments like "name" instead of "buildingname"
    elif 'building'+myarg in possible_fields:
      fieldsList.append(possible_fields['building'+myarg])
      i += 1
    else:
      systemErrorExit(3, '%s is not a valid argument to "gam print buildings"' % sys.argv[i])
  if fields:
    fields = fields % ','.join(fieldsList)
  buildings = callGAPIpages(cd.resources().buildings(), 'list', 'buildings',
                            customer=GC_Values[GC_CUSTOMER_ID], fields=fields)
  for building in buildings:
    building.pop('etags', None)
    building.pop('etag', None)
    building.pop('kind', None)
    if 'buildingId' in building:
      building['buildingId'] = 'id:{0}'.format(building['buildingId'])
    if 'floorNames' in building:
      building['floorNames'] = ','.join(building['floorNames'])
    building = flatten_json(building)
    for item in building:
      if item not in titles:
        titles.append(item)
    csvRows.append(building)
  sortCSVTitles('buildingId', titles)
  writeCSVfile(csvRows, titles, 'Buildings', to_drive)

def doPrintResourceCalendars():
  cd = buildGAPIObject('directory')
  todrive = False
  fieldsList = []
  fieldsTitles = {}
  titles = []
  csvRows = []
  i = 3
  while i < len(sys.argv):
    myarg = sys.argv[i].lower()
    if myarg == 'todrive':
      todrive = True
      i += 1
    elif myarg == 'allfields':
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
  fields = 'nextPageToken,items({0})'.format(','.join(set(fieldsList)))
  if 'buildingId' in fieldsList:
    addFieldToCSVfile('buildingName', {'buildingName': ['buildingName',]}, fieldsList, fieldsTitles, titles)
  printGettingAllItems('Resource Calendars', None)
  page_message = 'Got %%total_items%% Resource Calendars: %%first_item%% - %%last_item%%\n'
  resources = callGAPIpages(cd.resources().calendars(), 'list', 'items',
                            page_message=page_message, message_attribute='resourceId',
                            customer=GC_Values[GC_CUSTOMER_ID], fields=fields)
  for resource in resources:
    if 'featureInstances' in resource:
      resource['featureInstances'] = ','.join([a_feature['feature']['name'] for a_feature in resource.pop('featureInstances')])
    if 'buildingId' in resource:
      resource['buildingName'] = _getBuildingNameById(cd, resource['buildingId'])
      resource['buildingId'] = 'id:{0}'.format(resource['buildingId'])
    resUnit = {}
    for field in fieldsList:
      resUnit[fieldsTitles[field]] = resource.get(field, '')
    csvRows.append(resUnit)
  sortCSVTitles(['resourceId', 'resourceName', 'resourceEmail'], titles)
  writeCSVfile(csvRows, titles, 'Resources', todrive)

def shlexSplitList(entity, dataDelimiter=' ,'):
  lexer = shlex.shlex(entity, posix=True)
  lexer.whitespace = dataDelimiter
  lexer.whitespace_split = True
  return list(lexer)

def getQueries(myarg, argstr):
  if myarg == 'query':
    return [argstr]
  return shlexSplitList(argstr)

def _getRoleVerification(memberRoles, fields):
  if memberRoles and memberRoles.find(ROLE_MEMBER) != -1:
    return (set(memberRoles.split(',')), None, fields if fields.find('role') != -1 else fields[:-1]+',role)')
  return (set(), memberRoles, fields)

def getUsersToModify(entity_type=None, entity=None, silent=False, member_type=None, checkSuspended=None, groupUserMembersOnly=True):
  got_uids = False
  if entity_type is None:
    entity_type = sys.argv[1].lower()
  if entity is None:
    entity = sys.argv[2]
  cd = buildGAPIObject('directory')
  if entity_type == 'user':
    users = [entity,]
  elif entity_type == 'users':
    users = entity.replace(',', ' ').split()
  elif entity_type in ['group', 'group_ns', 'group_susp']:
    if entity_type == 'group_ns':
      checkSuspended = False
    elif entity_type == 'group_susp':
      checkSuspended = True
    got_uids = True
    group = entity
    if member_type is None:
      member_type_message = 'all members'
    else:
      member_type_message = '%ss' % member_type.lower()
    group = normalizeEmailAddressOrUID(group)
    page_message = None
    if not silent:
      sys.stderr.write("Getting %s of %s (may take some time for large groups)...\n" % (member_type_message, group))
      page_message = 'Got %%%%total_items%%%% %s...' % member_type_message
    validRoles, listRoles, listFields = _getRoleVerification(member_type, 'nextPageToken,members(email,id,type,status)')
    members = callGAPIpages(cd.members(), 'list', 'members', page_message=page_message,
                            groupKey=group, roles=listRoles, fields=listFields, maxResults=GC_Values[GC_MEMBER_MAX_RESULTS])
    users = []
    for member in members:
      if (((not groupUserMembersOnly) or (member['type'] == 'USER')) and
          (not validRoles or member.get('role', ROLE_MEMBER) in validRoles) and
          (checkSuspended is None or (not checkSuspended and member['status'] != 'SUSPENDED') or (checkSuspended and member['status'] == 'SUSPENDED'))):
        users.append(member.get('email', member['id']))
  elif entity_type in ['ou', 'org', 'ou_ns', 'org_ns', 'ou_susp', 'org_susp',]:
    if entity_type in ['ou_ns', 'org_ns']:
      checkSuspended = False
    elif entity_type in ['ou_susp', 'org_susp']:
      checkSuspended = True
    got_uids = True
    ou = makeOrgUnitPathAbsolute(entity)
    users = []
    if ou.startswith('id:'):
      ou = callGAPI(cd.orgunits(), 'get',
                    customerId=GC_Values[GC_CUSTOMER_ID], orgUnitPath=ou, fields='orgUnitPath')['orgUnitPath']
    query = orgUnitPathQuery(ou, checkSuspended)
    page_message = None
    if not silent:
      printGettingAllItems('Users', query)
      page_message = 'Got %%total_items%% Users...'
    members = callGAPIpages(cd.users(), 'list', 'users', page_message=page_message,
                            customer=GC_Values[GC_CUSTOMER_ID], fields='nextPageToken,users(primaryEmail,orgUnitPath)',
                            query=query, maxResults=GC_Values[GC_USER_MAX_RESULTS])
    ou = ou.lower()
    for member in members:
      if ou == member.get('orgUnitPath', '').lower():
        users.append(member['primaryEmail'])
    if not silent:
      sys.stderr.write("%s Users are directly in the OU.\n" % len(users))
  elif entity_type in ['ou_and_children', 'ou_and_child', 'ou_and_children_ns', 'ou_and_child_ns', 'ou_and_children_susp', 'ou_and_child_susp']:
    if entity_type in ['ou_and_children_ns', 'ou_and_child_ns']:
      checkSuspended = False
    elif entity_type in ['ou_and_children_susp', 'ou_and_child_susp']:
      checkSuspended = True
    got_uids = True
    ou = makeOrgUnitPathAbsolute(entity)
    users = []
    query = orgUnitPathQuery(ou, checkSuspended)
    page_message = None
    if not silent:
      printGettingAllItems('Users', query)
      page_message = 'Got %%total_items%% Users...'
    members = callGAPIpages(cd.users(), 'list', 'users', page_message=page_message,
                            customer=GC_Values[GC_CUSTOMER_ID], fields='nextPageToken,users(primaryEmail)',
                            query=query, maxResults=GC_Values[GC_USER_MAX_RESULTS])
    for member in members:
      users.append(member['primaryEmail'])
    if not silent:
      sys.stderr.write("done.\r\n")
  elif entity_type in ['query', 'queries']:
    if entity_type == 'query':
      queries = [entity]
    else:
      queries = shlexSplitList(entity)
    got_uids = True
    users = []
    usersSet = set()
    for query in queries:
      if not silent:
        printGettingAllItems('Users', query)
      page_message = 'Got %%total_items%% Users...'
      members = callGAPIpages(cd.users(), 'list', 'users', page_message=page_message,
                              customer=GC_Values[GC_CUSTOMER_ID], fields='nextPageToken,users(primaryEmail,suspended)',
                              query=query, maxResults=GC_Values[GC_USER_MAX_RESULTS])
      for member in members:
        email = member['primaryEmail']
        if (checkSuspended is None or checkSuspended == member['suspended']) and email not in usersSet:
          usersSet.add(email)
          users.append(email)
      if not silent:
        sys.stderr.write("done.\r\n")
  elif entity_type in ['license', 'licenses', 'licence', 'licences']:
    users = doPrintLicenses(returnFields='userId', skus=entity.split(','))
  elif entity_type in ['file', 'crosfile']:
    users = []
    f = openFile(entity)
    for row in f:
      user = row.strip()
      if user:
        users.append(user)
    closeFile(f)
    if entity_type == 'crosfile':
      entity = 'cros'
  elif entity_type in ['csv', 'csvfile', 'croscsv', 'croscsvfile']:
    drive, filenameColumn = os.path.splitdrive(entity)
    if filenameColumn.find(':') == -1:
      systemErrorExit(2, 'Expected {0} FileName:FieldName'.format(entity_type))
    (filename, column) = filenameColumn.split(':')
    f = openFile(drive+filename)
    input_file = csv.DictReader(f, restval='')
    if column not in input_file.fieldnames:
      csvFieldErrorExit(column, input_file.fieldnames)
    users = []
    for row in input_file:
      user = row[column].strip()
      if user:
        users.append(user)
    closeFile(f)
    if entity_type in ['croscsv', 'croscsvfile']:
      entity = 'cros'
  elif entity_type in ['courseparticipants', 'teachers', 'students']:
    croom = buildGAPIObject('classroom')
    users = []
    entity = addCourseIdScope(entity)
    if entity_type in ['courseparticipants', 'teachers']:
      page_message = 'Got %%total_items%% Teachers...'
      teachers = callGAPIpages(croom.courses().teachers(), 'list', 'teachers', page_message=page_message, courseId=entity)
      for teacher in teachers:
        email = teacher['profile'].get('emailAddress', None)
        if email:
          users.append(email)
    if entity_type in ['courseparticipants', 'students']:
      page_message = 'Got %%total_items%% Students...'
      students = callGAPIpages(croom.courses().students(), 'list', 'students', page_message=page_message, courseId=entity)
      for student in students:
        email = student['profile'].get('emailAddress', None)
        if email:
          users.append(email)
  elif entity_type == 'all':
    got_uids = True
    users = []
    entity = entity.lower()
    if entity == 'users':
      query = 'isSuspended=False'
      if not silent:
        printGettingAllItems('Users', None)
      page_message = 'Got %%total_items%% Users...'
      all_users = callGAPIpages(cd.users(), 'list', 'users', page_message=page_message,
                                customer=GC_Values[GC_CUSTOMER_ID], query=query,
                                fields='nextPageToken,users(primaryEmail)', maxResults=GC_Values[GC_USER_MAX_RESULTS])
      for member in all_users:
        users.append(member['primaryEmail'])
      if not silent:
        sys.stderr.write("done getting %s Users.\r\n" % len(users))
    elif entity == 'cros':
      if not silent:
        printGettingAllItems('CrOS Devices', None)
      page_message = 'Got %%total_items%% CrOS Devices...'
      all_cros = callGAPIpages(cd.chromeosdevices(), 'list', 'chromeosdevices', page_message=page_message,
                               customerId=GC_Values[GC_CUSTOMER_ID], fields='nextPageToken,chromeosdevices(deviceId)',
                               maxResults=GC_Values[GC_DEVICE_MAX_RESULTS])
      for member in all_cros:
        users.append(member['deviceId'])
      if not silent:
        sys.stderr.write("done getting %s CrOS Devices.\r\n" % len(users))
    else:
      systemErrorExit(3, '%s is not a valid argument for "gam all"' % entity)
  elif entity_type == 'cros':
    users = entity.replace(',', ' ').split()
    entity = 'cros'
  elif entity_type in ['crosquery', 'crosqueries', 'cros_sn']:
    if entity_type == 'cros_sn':
      queries = ['id:{0}'.format(sn) for sn in shlexSplitList(entity)]
    elif entity_type == 'crosqueries':
      queries = shlexSplitList(entity)
    else:
      queries = [entity]
    users = []
    usersSet = set()
    for query in queries:
      if not silent:
        printGettingAllItems('CrOS Devices', query)
      page_message = 'Got %%total_items%% CrOS Devices...'
      members = callGAPIpages(cd.chromeosdevices(), 'list', 'chromeosdevices', page_message=page_message,
                              customerId=GC_Values[GC_CUSTOMER_ID], fields='nextPageToken,chromeosdevices(deviceId)',
                              query=query, maxResults=GC_Values[GC_DEVICE_MAX_RESULTS])
      for member in members:
        deviceId = member['deviceId']
        if deviceId not in usersSet:
          usersSet.add(deviceId)
          users.append(deviceId)
      if not silent:
        sys.stderr.write("done.\r\n")
    entity = 'cros'
  else:
    systemErrorExit(2, '%s is not a valid argument for "gam"' % entity_type)
  full_users = list()
  if entity != 'cros' and not got_uids:
    for user in users:
      cg = UID_PATTERN.match(user)
      if cg:
        full_users.append(cg.group(1))
      elif user != '*' and user != GC_Values[GC_CUSTOMER_ID] and user.find('@') == -1:
        full_users.append('%s@%s' % (user, GC_Values[GC_DOMAIN]))
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
    print("\nOAuth File: %s" % GC_Values[GC_OAUTH2_TXT])
  oa2 = buildGAPIObject('oauth2')
  token_info = callGAPI(oa2, 'tokeninfo', access_token=access_token)
  print("Client ID: %s" % token_info['issued_to'])
  if credentials is not None:
    print("Secret: %s" % credentials.client_secret)
  scopes = token_info['scope'].split(' ')
  print('Scopes (%s):' % len(scopes))
  for scope in sorted(scopes):
    print('  %s' % scope)
  if credentials is not None:
    print('G Suite Admin: %s' % _getValueFromOAuth('email', credentials=credentials))

def doDeleteOAuth():
  storage, credentials = getOauth2TxtStorageCredentials()
  if credentials is None or credentials.invalid:
    storage.delete()
    return
  try:
    credentials.revoke_uri = oauth2client.GOOGLE_REVOKE_URI
  except AttributeError:
    systemErrorExit(1, 'Authorization doesn\'t exist')
  sys.stderr.write('This OAuth token will self-destruct in 3...')
  time.sleep(1)
  sys.stderr.write('2...')
  time.sleep(1)
  sys.stderr.write('1...')
  time.sleep(1)
  sys.stderr.write('boom!\n')
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
      systemErrorExit(0, '')
    client_id, client_secret = getOAuthClientIDAndSecret()
    login_hint = _getValidateLoginHint(login_hint)
    flow = oauth2client.client.OAuth2WebServerFlow(client_id=client_id,
                                                   client_secret=client_secret, scope=scopes, redirect_uri=oauth2client.client.OOB_CALLBACK_URN,
                                                   user_agent=GAM_INFO, response_type='code', login_hint=login_hint)
    credentials = oauth2client.tools.run_flow(flow=flow, storage=storage, flags=flags, http=http)
  else:
    print('It looks like you\'ve already authorized GAM. Refusing to overwrite existing file:\n\n%s' % GC_Values[GC_OAUTH2_TXT])

def getOAuthClientIDAndSecret():
  """Retrieves the OAuth client ID and client secret from JSON."""
  MISSING_CLIENT_SECRETS_MESSAGE = '''To use GAM you need to create an API project. Please run:

gam create project
'''
  filename = GC_Values[GC_CLIENT_SECRETS_JSON]
  cs_data = readFile(filename, continueOnError=True, displayError=True, encoding=None)
  if not cs_data:
    systemErrorExit(14, MISSING_CLIENT_SECRETS_MESSAGE)
  try:
    cs_json = json.loads(cs_data)
    client_id = cs_json['installed']['client_id']
    # chop off .apps.googleusercontent.com suffix as it's not needed
    # and we need to keep things short for the Auth URL.
    client_id = re.sub(r'\.apps\.googleusercontent\.com$', '', client_id)
    client_secret = cs_json['installed']['client_secret']
  except (ValueError, IndexError, KeyError):
    systemErrorExit(3, 'the format of your client secrets file:\n\n%s\n\n'
                    'is incorrect. Please recreate the file.' % filename)
  return (client_id, client_secret)

class cmd_flags():
  def __init__(self, noLocalWebserver):
    self.short_url = True
    self.noauth_local_webserver = noLocalWebserver
    self.logging_level = 'ERROR'
    self.auth_host_name = 'localhost'
    self.auth_host_port = [8080, 9090]

OAUTH2_SCOPES = [
  {'name': 'Classroom API - counts as 5 scopes',
   'subscopes': [],
   'scopes': ['https://www.googleapis.com/auth/classroom.rosters',
              'https://www.googleapis.com/auth/classroom.courses',
              'https://www.googleapis.com/auth/classroom.profile.emails',
              'https://www.googleapis.com/auth/classroom.profile.photos',
              'https://www.googleapis.com/auth/classroom.guardianlinks.students']},
  {'name': 'Cloud Print API',
   'subscopes': [],
   'scopes': 'https://www.googleapis.com/auth/cloudprint'},
  {'name': 'Data Transfer API',
   'subscopes': ['readonly'],
   'scopes': 'https://www.googleapis.com/auth/admin.datatransfer'},
  {'name': 'Directory API - Chrome OS Devices',
   'subscopes': ['readonly'],
   'scopes': 'https://www.googleapis.com/auth/admin.directory.device.chromeos'},
  {'name': 'Directory API - Customers',
   'subscopes': ['readonly'],
   'scopes': 'https://www.googleapis.com/auth/admin.directory.customer'},
  {'name': 'Directory API - Domains',
   'subscopes': ['readonly'],
   'scopes': 'https://www.googleapis.com/auth/admin.directory.domain'},
  {'name': 'Directory API - Groups',
   'subscopes': ['readonly'],
   'scopes': 'https://www.googleapis.com/auth/admin.directory.group'},
  {'name': 'Directory API - Mobile Devices',
   'subscopes': ['readonly', 'action'],
   'scopes': 'https://www.googleapis.com/auth/admin.directory.device.mobile'},
  {'name': 'Directory API - Organizational Units',
   'subscopes': ['readonly'],
   'scopes': 'https://www.googleapis.com/auth/admin.directory.orgunit'},
  {'name': 'Directory API - Resource Calendars',
   'subscopes': ['readonly'],
   'scopes': 'https://www.googleapis.com/auth/admin.directory.resource.calendar'},
  {'name': 'Directory API - Roles',
   'subscopes': ['readonly'],
   'scopes': 'https://www.googleapis.com/auth/admin.directory.rolemanagement'},
  {'name': 'Directory API - User Schemas',
   'subscopes': ['readonly'],
   'scopes': 'https://www.googleapis.com/auth/admin.directory.userschema'},
  {'name': 'Directory API - User Security',
   'subscopes': [],
   'scopes': 'https://www.googleapis.com/auth/admin.directory.user.security'},
  {'name': 'Directory API - Users',
   'subscopes': ['readonly'],
   'scopes': 'https://www.googleapis.com/auth/admin.directory.user'},
  {'name': 'Group Settings API',
   'subscopes': [],
   'scopes': 'https://www.googleapis.com/auth/apps.groups.settings'},
  {'name': 'License Manager API',
   'subscopes': [],
   'scopes': 'https://www.googleapis.com/auth/apps.licensing'},
  {'name': 'Pub / Sub API',
   'subscopes': [],
   'offByDefault': True,
   'scopes': 'https://www.googleapis.com/auth/pubsub'},
  {'name': 'Reports API - Audit Reports',
   'subscopes': [],
   'scopes': 'https://www.googleapis.com/auth/admin.reports.audit.readonly'},
  {'name': 'Reports API - Usage Reports',
   'subscopes': [],
   'scopes': 'https://www.googleapis.com/auth/admin.reports.usage.readonly'},
  {'name': 'Reseller API',
   'subscopes': [],
   'offByDefault': True,
   'scopes': 'https://www.googleapis.com/auth/apps.order'},
  {'name': 'Site Verification API',
   'subscopes': [],
   'scopes': 'https://www.googleapis.com/auth/siteverification'},
  {'name': 'Vault Matters and Holds API',
   'subscopes': ['readonly'],
   'scopes': 'https://www.googleapis.com/auth/ediscovery'},
  {'name': 'Cloud Storage (Vault Export - read only)',
   'subscopes': [],
   'scopes': 'https://www.googleapis.com/auth/devstorage.read_only'},
  {'name': 'User Profile (Email address - read only)',
   'subscopes': [],
   'scopes': 'email',
   'required': True},
  ]

def getScopesFromUser(menu_options=None):
  """Prompts the user to choose from a list of scopes to authorize.

  Args:
    menu_options: An optional list of ScopeMenuOptions to be presented in the
        menu. If no menu_options are provided, menu options will be generated
        from static OAUTH2_SCOPES definitions.

  Returns:
    A list of user-selected scopes to authorize.
  """

  if not menu_options:
    menu_options = [ScopeMenuOption.from_gam_oauth2scope(definition)
                    for definition in OAUTH2_SCOPES]
  menu = ScopeSelectionMenu(menu_options)
  try:
    menu.run()
  except ScopeSelectionMenu.UserRequestedExitException:
    systemErrorExit(0, '')

  return menu.get_selected_scopes()

class ScopeMenuOption():
  """A single GAM API/feature with scopes that can be turned on/off."""

  def __init__(self, oauth_scopes, description,
               is_required=False,
               is_selected=False,
               supported_restrictions=None,
               restriction=None):
    """A data structure for storing and toggling feature/API scope attributes.

    Args:
      oauth_scopes: A list of Google OAuth scope strings required for the
          feature or API. If the applicable scopes can vary in permission level,
          the scopes provided in this list should contain the highest level of
          permissions. More restrictive scopes are implemented by utilizing the
          `supported_restrictions` argument.
      description: String, a name or brief description of this API/feature.
      is_required: Bool, whether this API/feature is required for GAM. If True,
          the ScopeMenuOption cannot be unselected/disabled.
      is_selected: Bool, whether the ScopeMenuOption is currently
          selected/enabled.
      supported_restrictions: A list of strings that can be appended to the
          oauth_scopes, separated by '.', to restrict their permissions.
          For example, the directory API supports a 'readonly' mode on most
          scopes such that
          https://www.googleapis.com/auth/admin.directory.domain
          becomes
          https://www.googleapis.com/auth/admin.directory.domain.readonly
      restriction: String, the currently enabled restriction on all scopes in
          this ScopeMenuOption. Default is no restrictions (highest permission).
    """
    # Initialize private members
    self._is_selected = False
    self._restriction = None

    self.scopes = oauth_scopes
    self.description = description
    self.is_required = is_required
    # Required scopes must be selected
    self.is_selected = is_required or is_selected
    self.supported_restrictions = (
      supported_restrictions if supported_restrictions is not None else [])
    if restriction:
      self.restrict_to(restriction)

  def select(self, restriction=None):
    """Selects/enables the ScopeMenuOption with an optional restriction."""
    if restriction is not None:
      self.restrict_to(restriction)
    self.is_selected = True

  def unselect(self):
    """Unselects/disables the ScopeMenuOption."""
    self.is_selected = False

  @property
  def is_selected(self):
    return self._is_selected

  @is_selected.setter
  def is_selected(self, is_selected):
    if self.is_required and not is_selected:
      raise ValueError('Required scope cannot be unselected')
    if not is_selected:
      # Disable all applied restrictions
      self.unrestrict()
    self._is_selected = is_selected

  @property
  def is_restricted(self):
    return self._restriction is not None

  def supports_restriction(self, restriction):
    """Determines if a scope restriction is supported by this ScopeMenuOption.

    Args:
      restriction: String, the text appended to a full permission scope which
          will restrict its permissiveness. e.g. 'readonly' or 'action'.

    Returns:
      Bool, True if the scope restriction can be applied to this option.
    """
    return restriction in self.supported_restrictions

  @property
  def restriction(self):
    return self._restriction

  @restriction.setter
  def restriction(self, restriction):
    self.restrict_to(restriction)

  def restrict_to(self, restriction):
    """Applies a scope restriction to all scopes associated with this option.

    Args:
      restriction: String, a scope restriction which is appended to the
          full-permission scope with a leading '.'. e.g. if the full scope is
          https://www.googleapis.com/auth/admin.directory.domain
          providing 'readonly' here will make the effective scope
          https://www.googleapis.com/auth/admin.directory.domain.readonly
    """
    if self.supports_restriction(restriction):
      self._restriction = restriction
    else:
      error = 'Scope does not support a %s restriction.' % restriction
      if self.supported_restrictions is not None:
        restriction_list = ', '.join(self.supported_restrictions)
        error = error + (' Supported restrictions are: %s' % restriction_list)
      raise ValueError(error)

  def unrestrict(self):
    """Removes all scope restrictions currently applied."""
    self._restriction = None

  def get_effective_scopes(self):
    """Gets all scopes for this option, including their restrictions.

    Restrictions are applied in the form of trailing text which limit the
    scope's capabilities.
    """
    effective_scopes = []
    for scope in self.scopes:
      if self.is_restricted:
        scope = '%s.%s' % (scope, self._restriction)
      effective_scopes.append(scope)
    return effective_scopes

  @classmethod
  def from_gam_oauth2scope(cls, scope_definition):
    """Generates a ScopeMenuOption from a dict-style OAUTH2_SCOPES definition.

    Dict fields:
        name: Some description of the API/feature.
        subscopes: A list of compatible scope restrictions such as 'action' or
            'readonly'. Each scope in the scopes list must support this
            restriction text appended to the end of its normal scope text.
        scopes: A list of scopes that are required for the API/feature.
        offByDefault: A bool indicating whether this feature/scope should be off
            by default (when no prior selection has been made). Default is False
            (the item will be on/selected by default).
        required: A bool indicating the API/feature is required. This scope
            cannot be unselected. Default is False.

    Example:
    {
        'name': 'Made up API',
        'subscopes': ['action'],
        'scopes': ['https://www.googleapis.com/auth/some.scope'],
    }

    Args:
      scope_definition: A dict following the syntax of scopes defined in
          OAUTH2_SCOPES.

    Returns:
      A ScopeMenuOption object.
    """
    scopes = scope_definition.get('scopes', [])
    # If the scope is a single string, make it into a list.
    scope_list = scopes if isinstance(scopes, list) else [scopes]
    return cls(
      oauth_scopes=scope_list,
      description=scope_definition.get('name'),
      is_selected=not scope_definition.get('offByDefault'),
      supported_restrictions=scope_definition.get('subscopes', []),
      is_required=scope_definition.get('required', False))

class ScopeSelectionMenu():
  """A text menu which prompts the user to select the scopes to authorize."""

  class MenuChoiceError(Exception):
    """Error when an invalid or incompatible user choice is made."""
    pass

  class UserRequestedExitException(Exception):
    """Exception when the user requests immediate exit."""
    pass

  def __init__(self, options):
    """A menu of scope options to choose from.

    Args:
      options: A list of ScopeMenuOption objects from which to generate the menu
          Options will be presented on screen in the same order as the provided
          list.
    """
    self._options = options

  def get_options(self):
    """Returns all options that are available on this menu."""
    return self._options

  def get_selected_options(self):
    """Returns all currently selected ScopeMenuOptions."""
    return [option for option in self._options if option.is_selected]

  def get_selected_scopes(self):
    """Returns the aggregate set of oauth scopes currently selected."""
    selected_scopes = [scope for option in self.get_selected_options()
                       for scope in option.get_effective_scopes()]
    return set(selected_scopes)

  MENU_CHOICE = {
    'SELECT_ALL_SCOPES': 's',
    'UNSELECT_ALL_SCOPES': 'u',
    'EXIT': 'e',
    'CONTINUE': 'c'
  }

  _MENU_DISPLAY_TEXT = '''
Select the authorized scopes by entering a number.
Append an 'r' to grant read-only access or an 'a' to grant action-only access.

%s

     s)  Select all scopes
     u)  Unselect all scopes
     e)  Exit without changes
     c)  Continue to authorization

'''

  def get_menu_text(self):
    """Returns a text menu with numbered options."""
    scope_menu_items = [
      self._build_scope_menu_item(option, counter)
      for counter, option in enumerate(self._options)
    ]
    return ScopeSelectionMenu._MENU_DISPLAY_TEXT % '\n'.join(scope_menu_items)

  def _build_scope_menu_item(self, scope_option, option_number):
    """Builds a text line representing a single scope selection in the menu.

    The returned line is in the format:

    [<*>] <##>) <Feature description> (<supported scope modifiers>) [required]

    * = A single character indicating the option's selection status.
        '*' - All scopes are selected with full permissions.
        ' ' - No scopes are selected.
        'X' - Where 'X' is the first letter of the selected scope restriction,
              such as 'R' for readonly or 'A' for action, indicates scopes are
              selected with the corresponding restriction.
    ## = The line item number associated to this option.
    Feature description = The ScopeMenuOption description.
    scope modifiers = The supported scope restrictions for the ScopeMenuOption.
        When appended to the unrestricted, full oauth scope, these strings
        modify or restrict the access level of the given scope.
    [required] = Will only appear if the ScopeMenuOption is required and cannot
        be unselected.

    e.g. [*] 2) Directory API - Domains (supports 'readonly')

    Args:
      scope_option: The ScopeMenuOption associated with this line item.
      option_number: The selectable option number that is associated with
          modifying this line item.

    Returns:
      A string containing the line item text without a trailing newline.
    """
    SELECTION_INDICATOR = {
      'ALL_SELECTED': '*',
      'UNSELECTED': ' ',
      }
    indicator = SELECTION_INDICATOR['UNSELECTED']
    if scope_option.is_selected:
      if scope_option.is_restricted:
        # Use the first letter of the restriction as the indicator.
        indicator = scope_option.restriction[0].upper()
      else:
        indicator = SELECTION_INDICATOR['ALL_SELECTED']

    item_description = [
      '[%s]' % indicator,
      '%2d)' % option_number,
      scope_option.description,
      ]

    if scope_option.supported_restrictions:
      item_description.append(
        '(supports %s)' % ' and '.join(scope_option.supported_restrictions))

    if scope_option.is_required:
      item_description.append('[required]')

    return ' '.join(item_description)

  def get_prompt_text(self):
    """Builds and returns a prompt requesting user input."""
    # Get all the available restrictions and create the list of available
    # commands that the user can input.
    restrictions = {
      restriction for option in self._options
      for restriction in option.supported_restrictions
      }
    restriction_choices = [
      restriction[0].lower() for restriction in restrictions
      ]
    return ('Please enter 0-%d[%s] or %s: ' %
            (len(self._options)-1, # Keep the menu options 0-based
             '|'.join(restriction_choices),
             '|'.join(list(ScopeSelectionMenu.MENU_CHOICE.values()))))

  def run(self):
    """Displays the ScopeSelectionMenu to the user and prompts for input.

    The menu will continue to display until the user finishes adjusting all
    desired items and requests to return.

    After the menu is run, callers may use `get_selected_scopes()` or
    `get_selected_options()` methods to understand what the user's final choice
    was.

    Raises: ScopeSelectionMenu.UserRequestedExitException if the user chooses
        to exit the application entirely, rather than continue execution. This
        allows callers to decide how to handle the exit.
    """
    error_message = None
    while True:
      os.system(['clear', 'cls'][GM_Globals[GM_WINDOWS]])
      sys.stdout.write(self.get_menu_text())
      if error_message is not None:
        colored_error = createRedText(ERROR_PREFIX + error_message + '\n')
        sys.stdout.write(colored_error)
        error_message = None # Clear the pending error message

      user_input = input(self.get_prompt_text())
      try:
        prompt_again = self._process_menu_input(user_input)
        if not prompt_again:
          return
      except ScopeSelectionMenu.MenuChoiceError as e:
        error_message = str(e)

  _SINGLE_SCOPE_CHANGE_REGEX = re.compile(
    r'\s*(?P<scope_number>\d{1,2})\s*(?P<restriction>[a-z]?)', re.IGNORECASE)

  # Google-defined maximum number of scopes that can be authorized on a single
  # access token.
  MAXIMUM_NUM_SCOPES = 50

  def _process_menu_input(self, raw_menu_input):
    """Processes the raw user input provided to the menu prompt.

    Args:
      raw_menu_input: The raw, unaltered string provided by the user in response
          to the menu prompt.

    Returns:
      True, if the user should be prompted for further input. False, if the
      user has finished input and requested to continue execution of the
      program.

    Raises:
      ScopeSelectionMenu.UserRequestedExitException if the user requests to exit
          the application immediately.
      ScopeSelectionMenu.MenuChoiceError upon invalid user input.
    """
    user_input = raw_menu_input.lower().strip()
    single_scope_change = (
      ScopeSelectionMenu._SINGLE_SCOPE_CHANGE_REGEX.match(user_input))

    if single_scope_change:
      scope_number, restriction_command = single_scope_change.group(
        'scope_number', 'restriction')
      # Make sure we get an actual number to deal with.
      scope_number = int(scope_number)
      # Scope option numbers displayed in the menu are 0-based and map directly
      # to the indices in the list of scopes.
      if scope_number < 0 or scope_number > len(self._options) - 1:
        raise ScopeSelectionMenu.MenuChoiceError(
          'Invalid scope number "%d"' % scope_number)
      selected_option = self._options[scope_number]

      # Find the restriction that the user intended to apply.
      if restriction_command != '':
        matching_restrictions = [r for r in selected_option.supported_restrictions if r.startswith(restriction_command)]
        if not matching_restrictions:
          raise ScopeSelectionMenu.MenuChoiceError(
            'Scope "%s" does not support "%s" mode!' % (
              selected_option.description, restriction_command))
        restriction = matching_restrictions[0]
      else:
        restriction = None
      self._update_option(selected_option, restriction=restriction)

    elif user_input == ScopeSelectionMenu.MENU_CHOICE['SELECT_ALL_SCOPES']:
      for option in self._options:
        self._update_option(option, selected=True)
    elif user_input == ScopeSelectionMenu.MENU_CHOICE['UNSELECT_ALL_SCOPES']:
      for option in self._options:
        # Force-select required options
        self._update_option(option, selected=option.is_required)
    elif user_input == ScopeSelectionMenu.MENU_CHOICE['CONTINUE']:
      return False
    elif user_input == ScopeSelectionMenu.MENU_CHOICE['EXIT']:
      raise ScopeSelectionMenu.UserRequestedExitException()
    else:
      raise ScopeSelectionMenu.MenuChoiceError(
        'Invalid input "%s"' % user_input)

    return True

  def _update_option(self, option, selected=None, restriction=None):
    """Validates changes and updates the internal state of options on the menu.

    Args:
      option: The ScopeMenuOption to update
      selected: If provided, updates the "selected" status of the option. If
          not provided, the "selected" status will be toggled to its opposite
          state.
      restriction: If provided, applies a restriction to the provided option.

    Raises:
      ScopeSelectionMenu.MenuChoiceError on change validation errors.
    """
    if option.is_required and (not selected or selected is None):
      raise ScopeSelectionMenu.MenuChoiceError(
        'Scope "%s" is required and cannot be unselected!' %
        option.description)
    if selected and not option.is_selected:
      # Make sure we're not about to exceed the maximum number of scopes
      # authorized on a single token.
      num_scopes_to_add = len(option.get_effective_scopes())
      num_selected_scopes = len(self.get_selected_scopes())
      expected_num_scopes = num_scopes_to_add + num_selected_scopes
      if expected_num_scopes > ScopeSelectionMenu.MAXIMUM_NUM_SCOPES:
        raise ScopeSelectionMenu.MenuChoiceError(
          'Too many scopes selected (%d). Maximum is %d. Please remove some '
          'scopes and try again.' % (
            expected_num_scopes, ScopeSelectionMenu.MAXIMUM_NUM_SCOPES))

    if restriction is None:
      if selected is None:
        # Toggle the option on/off
        option.is_selected = not option.is_selected
      else:
        option.is_selected = selected
    else:
      if option.supports_restriction(restriction):
        option.select(restriction)
      else:
        raise ScopeSelectionMenu.MenuChoiceError(
          'Scope "%s" does not support %s mode!' % (
            option.description, restriction))

def init_gam_worker():
  signal.signal(signal.SIGINT, signal.SIG_IGN)

def run_batch(items):
  if not items:
    return
  num_worker_threads = min(len(items), GC_Values[GC_NUM_THREADS])
  pool = Pool(num_worker_threads, init_gam_worker)
  sys.stderr.write('Using %s processes...\n' % num_worker_threads)
  try:
    results = []
    for item in items:
      if item[0] == 'commit-batch':
        sys.stderr.write('commit-batch - waiting for running processes to finish before proceeding\n')
        pool.close()
        pool.join()
        pool = Pool(num_worker_threads, init_gam_worker)
        sys.stderr.write('commit-batch - running processes finished, proceeding\n')
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
        print('Finished %s of %s processes.' % (num_done, num_total))
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
    elif myarg[0] == '~':
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
  for GAM_argvI, fields in subFields.items():
    oargv = argv[GAM_argvI][:]
    argv[GAM_argvI] = ''
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
      items.append(['gam', 'user', user] + sys.argv[3:])
    run_batch(items)
    sys.exit(0)
  else:
    cmd(users, **kwargs)

def ProcessGAMCommandMulti(args):
  ProcessGAMCommand(args)

# Process GAM command
def ProcessGAMCommand(args):
  if args != sys.argv:
    sys.argv = args[:]
  GM_Globals[GM_SYSEXITRC] = 0
  try:
    SetGlobalVariables()
    command = sys.argv[1].lower()
    if command == 'batch':
      i = 2
      filename = sys.argv[i]
      i, encoding = getCharSet(i+1)
      f = openFile(filename, encoding=encoding)
      items = []
      errors = 0
      for line in f:
        try:
          argv = shlex.split(line)
        except ValueError as e:
          sys.stderr.write(utils.convertUTF8('Command: >>>{0}<<<\n'.format(line.strip())))
          sys.stderr.write('{0}{1}\n'.format(ERROR_PREFIX, str(e)))
          errors += 1
          continue
        if argv:
          cmd = argv[0].strip().lower()
          if (not cmd) or cmd.startswith('#') or ((len(argv) == 1) and (cmd != 'commit-batch')):
            continue
          if cmd == 'gam':
            items.append(argv)
          elif cmd == 'commit-batch':
            items.append([cmd])
          else:
            sys.stderr.write(utils.convertUTF8('Command: >>>{0}<<<\n'.format(line.strip())))
            sys.stderr.write('{0}Invalid: Expected <gam|commit-batch>\n'.format(ERROR_PREFIX))
            errors += 1
      closeFile(f)
      if errors == 0:
        run_batch(items)
        sys.exit(0)
      else:
        systemErrorExit(2, 'batch file: {0}, not processed, {1} error{2}'.format(filename, errors, ['', 's'][errors != 1]))
    elif command == 'csv':
      if httplib2.debuglevel > 0:
        systemErrorExit(1, 'CSV commands are not compatible with debug. Delete debug.gam and try again.')
      i = 2
      filename = sys.argv[i]
      i, encoding = getCharSet(i+1)
      f = openFile(filename, encoding=encoding)
      csvFile = csv.DictReader(f)
      if (i == len(sys.argv)) or (sys.argv[i].lower() != 'gam') or (i+1 == len(sys.argv)):
        systemErrorExit(3, '"gam csv <filename>" must be followed by a full GAM command...')
      i += 1
      GAM_argv, subFields = getSubFields(i, csvFile.fieldnames)
      items = []
      for row in csvFile:
        items.append(['gam']+processSubFields(GAM_argv, row, subFields))
      closeFile(f)
      run_batch(items)
      sys.exit(0)
    elif command == 'version':
      doGAMVersion()
      sys.exit(0)
    elif command == 'create':
      argument = sys.argv[2].lower()
      if argument == 'user':
        doCreateUser()
      elif argument == 'group':
        doCreateGroup()
      elif argument in ['nickname', 'alias']:
        doCreateAlias()
      elif argument in ['org', 'ou']:
        doCreateOrg()
      elif argument == 'resource':
        doCreateResourceCalendar()
      elif argument in ['verify', 'verification']:
        doSiteVerifyShow()
      elif argument == 'schema':
        doCreateOrUpdateUserSchema(False)
      elif argument in ['course', 'class']:
        doCreateCourse()
      elif argument in ['transfer', 'datatransfer']:
        doCreateDataTransfer()
      elif argument == 'domain':
        doCreateDomain()
      elif argument in ['domainalias', 'aliasdomain']:
        doCreateDomainAlias()
      elif argument == 'admin':
        doCreateAdmin()
      elif argument in ['guardianinvite', 'inviteguardian', 'guardian']:
        doInviteGuardian()
      elif argument in ['project', 'apiproject']:
        doCreateProject()
      elif argument in ['resoldcustomer', 'resellercustomer']:
        doCreateResoldCustomer()
      elif argument in ['resoldsubscription', 'resellersubscription']:
        doCreateResoldSubscription()
      elif argument in ['matter', 'vaultmatter']:
        doCreateVaultMatter()
      elif argument in ['hold', 'vaulthold']:
        doCreateVaultHold()
      elif argument in ['export', 'vaultexport']:
        doCreateVaultExport()
      elif argument in ['building']:
        doCreateBuilding()
      elif argument in ['feature']:
        doCreateFeature()
      elif argument in ['alertfeedback']:
        doCreateAlertFeedback()
      else:
        systemErrorExit(2, '%s is not a valid argument for "gam create"' % argument)
      sys.exit(0)
    elif command == 'use':
      argument = sys.argv[2].lower()
      if argument in ['project', 'apiproject']:
        doUseProject()
      else:
        systemErrorExit(2, '%s is not a valid argument for "gam use"' % argument)
      sys.exit(0)
    elif command == 'update':
      argument = sys.argv[2].lower()
      if argument == 'user':
        doUpdateUser(None, 4)
      elif argument == 'group':
        doUpdateGroup()
      elif argument in ['nickname', 'alias']:
        doUpdateAlias()
      elif argument in ['ou', 'org']:
        doUpdateOrg()
      elif argument == 'resource':
        doUpdateResourceCalendar()
      elif argument == 'cros':
        doUpdateCros()
      elif argument == 'mobile':
        doUpdateMobile()
      elif argument in ['verify', 'verification']:
        doSiteVerifyAttempt()
      elif argument in ['schema', 'schemas']:
        doCreateOrUpdateUserSchema(True)
      elif argument in ['course', 'class']:
        doUpdateCourse()
      elif argument in ['printer', 'print']:
        doUpdatePrinter()
      elif argument == 'domain':
        doUpdateDomain()
      elif argument == 'customer':
        doUpdateCustomer()
      elif argument in ['resoldcustomer', 'resellercustomer']:
        doUpdateResoldCustomer()
      elif argument in ['resoldsubscription', 'resellersubscription']:
        doUpdateResoldSubscription()
      elif argument in ['matter', 'vaultmatter']:
        doUpdateVaultMatter()
      elif argument in ['hold', 'vaulthold']:
        doUpdateVaultHold()
      elif argument in ['project', 'projects', 'apiproject']:
        doUpdateProjects()
      elif argument in ['building']:
        doUpdateBuilding()
      elif argument in ['feature']:
        doUpdateFeature()
      else:
        systemErrorExit(2, '%s is not a valid argument for "gam update"' % argument)
      sys.exit(0)
    elif command == 'info':
      argument = sys.argv[2].lower()
      if argument == 'user':
        doGetUserInfo()
      elif argument == 'group':
        doGetGroupInfo()
      elif argument == 'member':
        doGetMemberInfo()
      elif argument in ['nickname', 'alias']:
        doGetAliasInfo()
      elif argument == 'instance':
        doGetCustomerInfo()
      elif argument in ['org', 'ou']:
        doGetOrgInfo()
      elif argument == 'resource':
        doGetResourceCalendarInfo()
      elif argument == 'cros':
        doGetCrosInfo()
      elif argument == 'mobile':
        doGetMobileInfo()
      elif argument in ['verify', 'verification']:
        doGetSiteVerifications()
      elif argument in ['schema', 'schemas']:
        doGetUserSchema()
      elif argument in ['course', 'class']:
        doGetCourseInfo()
      elif argument in ['printer', 'print']:
        doGetPrinterInfo()
      elif argument in ['transfer', 'datatransfer']:
        doGetDataTransferInfo()
      elif argument == 'customer':
        doGetCustomerInfo()
      elif argument == 'domain':
        doGetDomainInfo()
      elif argument in ['domainalias', 'aliasdomain']:
        doGetDomainAliasInfo()
      elif argument in ['resoldcustomer', 'resellercustomer']:
        doGetResoldCustomer()
      elif argument in ['resoldsubscription', 'resoldsubscriptions', 'resellersubscription', 'resellersubscriptions']:
        doGetResoldSubscriptions()
      elif argument in ['matter', 'vaultmatter']:
        doGetVaultMatterInfo()
      elif argument in ['hold', 'vaulthold']:
        doGetVaultHoldInfo()
      elif argument in ['export', 'vaultexport']:
        doGetVaultExportInfo()
      elif argument in ['building']:
        doGetBuildingInfo()
      else:
        systemErrorExit(2, '%s is not a valid argument for "gam info"' % argument)
      sys.exit(0)
    elif command == 'cancel':
      argument = sys.argv[2].lower()
      if argument in ['guardianinvitation', 'guardianinvitations']:
        doCancelGuardianInvitation()
      else:
        systemErrorExit(2, '%s is not a valid argument for "gam cancel"' % argument)
      sys.exit(0)
    elif command == 'delete':
      argument = sys.argv[2].lower()
      if argument == 'user':
        doDeleteUser()
      elif argument == 'group':
        doDeleteGroup()
      elif argument in ['nickname', 'alias']:
        doDeleteAlias()
      elif argument == 'org':
        doDeleteOrg()
      elif argument == 'resource':
        doDeleteResourceCalendar()
      elif argument == 'mobile':
        doDeleteMobile()
      elif argument in ['schema', 'schemas']:
        doDelSchema()
      elif argument in ['course', 'class']:
        doDelCourse()
      elif argument in ['printer', 'printers']:
        doDelPrinter()
      elif argument == 'domain':
        doDelDomain()
      elif argument in ['domainalias', 'aliasdomain']:
        doDelDomainAlias()
      elif argument == 'admin':
        doDelAdmin()
      elif argument in ['guardian', 'guardians']:
        doDeleteGuardian()
      elif argument in ['project', 'projects']:
        doDelProjects()
      elif argument in ['resoldsubscription', 'resellersubscription']:
        doDeleteResoldSubscription()
      elif argument in ['matter', 'vaultmatter']:
        doUpdateVaultMatter(action=command)
      elif argument in ['hold', 'vaulthold']:
        doDeleteVaultHold()
      elif argument in ['export', 'vaultexport']:
        doDeleteVaultExport()
      elif argument in ['building']:
        doDeleteBuilding()
      elif argument in ['feature']:
        doDeleteFeature()
      elif argument in ['alert']:
        doDeleteOrUndeleteAlert('delete')
      else:
        systemErrorExit(2, '%s is not a valid argument for "gam delete"' % argument)
      sys.exit(0)
    elif command == 'undelete':
      argument = sys.argv[2].lower()
      if argument == 'user':
        doUndeleteUser()
      elif argument in ['matter', 'vaultmatter']:
        doUpdateVaultMatter(action=command)
      elif argument == 'alert':
        doDeleteOrUndeleteAlert('undelete')
      else:
        systemErrorExit(2, '%s is not a valid argument for "gam undelete"' % argument)
      sys.exit(0)
    elif command in ['close', 'reopen']:
      # close and reopen will have to be split apart if either takes a new argument
      argument = sys.argv[2].lower()
      if argument in ['matter', 'vaultmatter']:
        doUpdateVaultMatter(action=command)
      else:
        systemErrorExit(2, '%s is not a valid argument for "gam %s"' % (argument, command))
      sys.exit(0)
    elif command == 'print':
      argument = sys.argv[2].lower().replace('-', '')
      if argument == 'users':
        doPrintUsers()
      elif argument in ['nicknames', 'aliases']:
        doPrintAliases()
      elif argument == 'groups':
        doPrintGroups()
      elif argument in ['groupmembers', 'groupsmembers']:
        doPrintGroupMembers()
      elif argument in ['orgs', 'ous']:
        doPrintOrgs()
      elif argument == 'resources':
        doPrintResourceCalendars()
      elif argument == 'cros':
        doPrintCrosDevices()
      elif argument == 'crosactivity':
        doPrintCrosActivity()
      elif argument == 'mobile':
        doPrintMobileDevices()
      elif argument in ['license', 'licenses', 'licence', 'licences']:
        doPrintLicenses()
      elif argument in ['token', 'tokens', 'oauth', '3lo']:
        printShowTokens(3, None, None, True)
      elif argument in ['schema', 'schemas']:
        doPrintShowUserSchemas(True)
      elif argument in ['courses', 'classes']:
        doPrintCourses()
      elif argument in ['courseparticipants', 'classparticipants']:
        doPrintCourseParticipants()
      elif argument == 'printers':
        doPrintPrinters()
      elif argument == 'printjobs':
        doPrintPrintJobs()
      elif argument in ['transfers', 'datatransfers']:
        doPrintDataTransfers()
      elif argument == 'transferapps':
        doPrintTransferApps()
      elif argument == 'domains':
        doPrintDomains()
      elif argument in ['domainaliases', 'aliasdomains']:
        doPrintDomainAliases()
      elif argument == 'admins':
        doPrintAdmins()
      elif argument in ['roles', 'adminroles']:
        doPrintAdminRoles()
      elif argument in ['guardian', 'guardians']:
        doPrintShowGuardians(True)
      elif argument in ['matters', 'vaultmatters']:
        doPrintVaultMatters()
      elif argument in ['holds', 'vaultholds']:
        doPrintVaultHolds()
      elif argument in ['exports', 'vaultexports']:
        doPrintVaultExports()
      elif argument in ['building', 'buildings']:
        doPrintBuildings()
      elif argument in ['feature', 'features']:
        doPrintFeatures()
      elif argument in ['project', 'projects']:
        doPrintShowProjects(True)
      elif argument in ['alert', 'alerts']:
        doPrintShowAlerts()
      elif argument in ['alertfeedback', 'alertsfeedback']:
        doPrintShowAlertFeedback()
      else:
        systemErrorExit(2, '%s is not a valid argument for "gam print"' % argument)
      sys.exit(0)
    elif command == 'show':
      argument = sys.argv[2].lower()
      if argument in ['schema', 'schemas']:
        doPrintShowUserSchemas(False)
      elif argument in ['guardian', 'guardians']:
        doPrintShowGuardians(False)
      elif argument in ['license', 'licenses', 'licence', 'licences']:
        doShowLicenses()
      elif argument in ['project', 'projects']:
        doPrintShowProjects(False)
      else:
        systemErrorExit(2, '%s is not a valid argument for "gam show"' % argument)
      sys.exit(0)
    elif command in ['oauth', 'oauth2']:
      argument = sys.argv[2].lower()
      if argument in ['request', 'create']:
        try:
          login_hint = sys.argv[3].strip()
        except IndexError:
          login_hint = None
        doRequestOAuth(login_hint)
      elif argument in ['info', 'verify']:
        OAuthInfo()
      elif argument in ['delete', 'revoke']:
        doDeleteOAuth()
      else:
        systemErrorExit(2, '%s is not a valid argument for "gam oauth"' % argument)
      sys.exit(0)
    elif command == 'calendar':
      argument = sys.argv[3].lower()
      if argument == 'showacl':
        doCalendarShowACL()
      elif argument == 'add':
        doCalendarAddACL('Add')
      elif argument in ['del', 'delete']:
        doCalendarDelACL()
      elif argument == 'update':
        doCalendarAddACL('Update')
      elif argument == 'wipe':
        doCalendarWipeData()
      elif argument == 'addevent':
        doCalendarAddEvent()
      elif argument == 'deleteevent':
        doCalendarDeleteEvent()
      elif argument == 'modify':
        doCalendarModifySettings()
      else:
        systemErrorExit(2, '%s is not a valid argument for "gam calendar"' % argument)
      sys.exit(0)
    elif command == 'printer':
      if sys.argv[2].lower() == 'register':
        doPrinterRegister()
        sys.exit(0)
      argument = sys.argv[3].lower()
      if argument == 'showacl':
        doPrinterShowACL()
      elif argument == 'add':
        doPrinterAddACL()
      elif argument in ['del', 'delete', 'remove']:
        doPrinterDelACL()
      else:
        systemErrorExit(2, '%s is not a valid argument for "gam printer..."' % argument)
      sys.exit(0)
    elif command == 'printjob':
      argument = sys.argv[3].lower()
      if argument == 'delete':
        doDeletePrintJob()
      elif argument == 'cancel':
        doCancelPrintJob()
      elif argument == 'submit':
        doPrintJobSubmit()
      elif argument == 'fetch':
        doPrintJobFetch()
      elif argument == 'resubmit':
        doPrintJobResubmit()
      else:
        systemErrorExit(2, '%s is not a valid argument for "gam printjob"' % argument)
      sys.exit(0)
    elif command == 'report':
      showReport()
      sys.exit(0)
    elif command == 'whatis':
      doWhatIs()
      sys.exit(0)
    elif command in ['course', 'class']:
      argument = sys.argv[3].lower()
      if argument in ['add', 'create']:
        doAddCourseParticipant()
      elif argument in ['del', 'delete', 'remove']:
        doDelCourseParticipant()
      elif argument == 'sync':
        doSyncCourseParticipants()
      else:
        systemErrorExit(2, '%s is not a valid argument for "gam course"' % argument)
      sys.exit(0)
    elif command == 'download':
      argument = sys.argv[2].lower()
      if argument in ['export', 'vaultexport']:
        doDownloadVaultExport()
      else:
        systemErrorExit(2, '%s is not a valid argument for "gam download"' % argument)
      sys.exit(0)
    users = getUsersToModify()
    command = sys.argv[3].lower()
    if command == 'print' and len(sys.argv) == 4:
      for user in users:
        print(user)
      sys.exit(0)
    if (GC_Values[GC_AUTO_BATCH_MIN] > 0) and (len(users) > GC_Values[GC_AUTO_BATCH_MIN]):
      runCmdForUsers(None, users, True)
    if command == 'transfer':
      transferWhat = sys.argv[4].lower()
      if transferWhat == 'drive':
        transferDriveFiles(users)
      elif transferWhat == 'seccals':
        transferSecCals(users)
      else:
        systemErrorExit(2, '%s is not a valid argument for "gam <users> transfer"' % transferWhat)
    elif command == 'show':
      showWhat = sys.argv[4].lower()
      if showWhat in ['labels', 'label']:
        showLabels(users)
      elif showWhat == 'profile':
        showProfile(users)
      elif showWhat == 'calendars':
        printShowCalendars(users, False)
      elif showWhat == 'calsettings':
        showCalSettings(users)
      elif showWhat == 'drivesettings':
        printDriveSettings(users)
      elif showWhat == 'teamdrivethemes':
        getTeamDriveThemes(users)
      elif showWhat == 'drivefileacl':
        showDriveFileACL(users)
      elif showWhat == 'filelist':
        printDriveFileList(users)
      elif showWhat == 'filetree':
        showDriveFileTree(users)
      elif showWhat == 'fileinfo':
        showDriveFileInfo(users)
      elif showWhat == 'filerevisions':
        showDriveFileRevisions(users)
      elif showWhat == 'sendas':
        printShowSendAs(users, False)
      elif showWhat == 'smime':
        printShowSmime(users, False)
      elif showWhat == 'gmailprofile':
        showGmailProfile(users)
      elif showWhat in ['sig', 'signature']:
        getSignature(users)
      elif showWhat == 'forward':
        printShowForward(users, False)
      elif showWhat in ['pop', 'pop3']:
        getPop(users)
      elif showWhat in ['imap', 'imap4']:
        getImap(users)
      elif showWhat == 'vacation':
        getVacation(users)
      elif showWhat in ['delegate', 'delegates']:
        printShowDelegates(users, False)
      elif showWhat in ['backupcode', 'backupcodes', 'verificationcodes']:
        doGetBackupCodes(users)
      elif showWhat in ['asp', 'asps', 'applicationspecificpasswords']:
        doGetASPs(users)
      elif showWhat in ['token', 'tokens', 'oauth', '3lo']:
        printShowTokens(5, 'users', users, False)
      elif showWhat == 'driveactivity':
        printDriveActivity(users)
      elif showWhat in ['filter', 'filters']:
        printShowFilters(users, False)
      elif showWhat in ['forwardingaddress', 'forwardingaddresses']:
        printShowForwardingAddresses(users, False)
      elif showWhat in ['teamdrive', 'teamdrives']:
        printShowTeamDrives(users, False)
      elif showWhat in ['teamdriveinfo']:
        doGetTeamDriveInfo(users)
      else:
        systemErrorExit(2, '%s is not a valid argument for "gam <users> show"' % showWhat)
    elif command == 'print':
      printWhat = sys.argv[4].lower()
      if printWhat == 'calendars':
        printShowCalendars(users, True)
      elif printWhat in ['delegate', 'delegates']:
        printShowDelegates(users, True)
      elif printWhat == 'driveactivity':
        printDriveActivity(users)
      elif printWhat == 'drivesettings':
        printDriveSettings(users)
      elif printWhat == 'filelist':
        printDriveFileList(users)
      elif printWhat in ['filter', 'filters']:
        printShowFilters(users, True)
      elif printWhat == 'forward':
        printShowForward(users, True)
      elif printWhat in ['forwardingaddress', 'forwardingaddresses']:
        printShowForwardingAddresses(users, True)
      elif printWhat == 'sendas':
        printShowSendAs(users, True)
      elif printWhat == 'smime':
        printShowSmime(users, True)
      elif printWhat in ['token', 'tokens', 'oauth', '3lo']:
        printShowTokens(5, 'users', users, True)
      elif printWhat in ['teamdrive', 'teamdrives']:
        printShowTeamDrives(users, True)
      else:
        systemErrorExit(2, '%s is not a valid argument for "gam <users> print"' % printWhat)
    elif command == 'modify':
      modifyWhat = sys.argv[4].lower()
      if modifyWhat in ['message', 'messages']:
        doProcessMessagesOrThreads(users, 'modify', 'messages')
      elif modifyWhat in ['thread', 'threads']:
        doProcessMessagesOrThreads(users, 'modify', 'threads')
      else:
        systemErrorExit(2, '%s is not a valid argument for "gam <users> modify"' % modifyWhat)
    elif command == 'trash':
      trashWhat = sys.argv[4].lower()
      if trashWhat in ['message', 'messages']:
        doProcessMessagesOrThreads(users, 'trash', 'messages')
      elif trashWhat in ['thread', 'threads']:
        doProcessMessagesOrThreads(users, 'trash', 'threads')
      else:
        systemErrorExit(2, '%s is not a valid argument for "gam <users> trash"' % trashWhat)
    elif command == 'untrash':
      untrashWhat = sys.argv[4].lower()
      if untrashWhat in ['message', 'messages']:
        doProcessMessagesOrThreads(users, 'untrash', 'messages')
      elif untrashWhat in ['thread', 'threads']:
        doProcessMessagesOrThreads(users, 'untrash', 'threads')
      else:
        systemErrorExit(2, '%s is not a valid argument for "gam <users> untrash"' % untrashWhat)
    elif command in ['delete', 'del']:
      delWhat = sys.argv[4].lower()
      if delWhat == 'delegate':
        deleteDelegate(users)
      elif delWhat == 'calendar':
        deleteCalendar(users)
      elif delWhat  in ['labels', 'label']:
        doDeleteLabel(users)
      elif delWhat in ['message', 'messages']:
        runCmdForUsers(doProcessMessagesOrThreads, users, default_to_batch=True, function='delete', unit='messages')
      elif delWhat in ['thread', 'threads']:
        runCmdForUsers(doProcessMessagesOrThreads, users, default_to_batch=True, function='delete', unit='threads')
      elif delWhat == 'photo':
        deletePhoto(users)
      elif delWhat in ['license', 'licence']:
        doLicense(users, 'delete')
      elif delWhat in ['backupcode', 'backupcodes', 'verificationcodes']:
        doDelBackupCodes(users)
      elif delWhat in ['asp', 'asps', 'applicationspecificpasswords']:
        doDelASP(users)
      elif delWhat in ['token', 'tokens', 'oauth', '3lo']:
        doDelTokens(users)
      elif delWhat in ['group', 'groups']:
        deleteUserFromGroups(users)
      elif delWhat in ['alias', 'aliases']:
        doRemoveUsersAliases(users)
      elif delWhat == 'emptydrivefolders':
        deleteEmptyDriveFolders(users)
      elif delWhat == 'drivefile':
        deleteDriveFile(users)
      elif delWhat in ['drivefileacl', 'drivefileacls']:
        delDriveFileACL(users)
      elif delWhat in ['filter', 'filters']:
        deleteFilters(users)
      elif delWhat in ['forwardingaddress', 'forwardingaddresses']:
        deleteForwardingAddresses(users)
      elif delWhat == 'sendas':
        deleteSendAs(users)
      elif delWhat == 'smime':
        deleteSmime(users)
      elif delWhat == 'teamdrive':
        doDeleteTeamDrive(users)
      else:
        systemErrorExit(2, '%s is not a valid argument for "gam <users> delete"' % delWhat)
    elif command in ['add', 'create']:
      addWhat = sys.argv[4].lower()
      if addWhat == 'calendar':
        if command == 'add':
          addCalendar(users)
        else:
          systemErrorExit(2, '%s is not implemented for "gam <users> %s"' % (addWhat, command))
      elif addWhat == 'drivefile':
        createDriveFile(users)
      elif addWhat in ['license', 'licence']:
        doLicense(users, 'insert')
      elif addWhat in ['drivefileacl', 'drivefileacls']:
        addDriveFileACL(users)
      elif addWhat in ['label', 'labels']:
        doLabel(users, 5)
      elif addWhat in ['delegate', 'delegates']:
        addDelegates(users, 5)
      elif addWhat in ['filter', 'filters']:
        addFilter(users, 5)
      elif addWhat in ['forwardingaddress', 'forwardingaddresses']:
        addForwardingAddresses(users)
      elif addWhat == 'sendas':
        addUpdateSendAs(users, 5, True)
      elif addWhat == 'smime':
        addSmime(users)
      elif addWhat == 'teamdrive':
        doCreateTeamDrive(users)
      else:
        systemErrorExit(2, '%s is not a valid argument for "gam <users> %s"' % (addWhat, command))
    elif command == 'update':
      updateWhat = sys.argv[4].lower()
      if updateWhat == 'calendar':
        updateCalendar(users)
      elif updateWhat == 'calattendees':
        changeCalendarAttendees(users)
      elif updateWhat == 'photo':
        doPhoto(users)
      elif updateWhat in ['license', 'licence']:
        doLicense(users, 'patch')
      elif updateWhat == 'user':
        doUpdateUser(users, 5)
      elif updateWhat in ['backupcode', 'backupcodes', 'verificationcodes']:
        doGenBackupCodes(users)
      elif updateWhat == 'drivefile':
        doUpdateDriveFile(users)
      elif updateWhat in ['drivefileacls', 'drivefileacl']:
        updateDriveFileACL(users)
      elif updateWhat in ['label', 'labels']:
        renameLabels(users)
      elif updateWhat == 'labelsettings':
        updateLabels(users)
      elif updateWhat == 'sendas':
        addUpdateSendAs(users, 5, False)
      elif updateWhat == 'smime':
        updateSmime(users)
      elif updateWhat == 'teamdrive':
        doUpdateTeamDrive(users)
      else:
        systemErrorExit(2, '%s is not a valid argument for "gam <users> update"' % updateWhat)
    elif command in ['deprov', 'deprovision']:
      doDeprovUser(users)
    elif command == 'get':
      getWhat = sys.argv[4].lower()
      if getWhat == 'photo':
        getPhoto(users)
      elif getWhat == 'drivefile':
        downloadDriveFile(users)
      else:
        systemErrorExit(2, '%s is not a valid argument for "gam <users> get"' % getWhat)
    elif command == 'empty':
      emptyWhat = sys.argv[4].lower()
      if emptyWhat == 'drivetrash':
        doEmptyDriveTrash(users)
      else:
        systemErrorExit(2, '%s is not a valid argument for "gam <users> empty"' % emptyWhat)
    elif command == 'info':
      infoWhat = sys.argv[4].lower()
      if infoWhat == 'calendar':
        infoCalendar(users)
      elif infoWhat in ['filter', 'filters']:
        infoFilters(users)
      elif infoWhat in ['forwardingaddress', 'forwardingaddresses']:
        infoForwardingAddresses(users)
      elif infoWhat == 'sendas':
        infoSendAs(users)
      else:
        systemErrorExit(2, '%s is not a valid argument for "gam <users> info"' % infoWhat)
    elif command == 'check':
      checkWhat = sys.argv[4].replace('_', '').lower()
      if checkWhat == 'serviceaccount':
        doCheckServiceAccount(users)
      else:
        systemErrorExit(2, '%s is not a valid argument for "gam <users> check"' % checkWhat)
    elif command == 'profile':
      doProfile(users)
    elif command == 'imap':
      #doImap(users)
      runCmdForUsers(doImap, users, default_to_batch=True)
    elif command in ['pop', 'pop3']:
      doPop(users)
    elif command == 'sendas':
      addUpdateSendAs(users, 4, True)
    elif command == 'label':
      doLabel(users, 4)
    elif command == 'filter':
      addFilter(users, 4)
    elif command == 'forward':
      doForward(users)
    elif command in ['sig', 'signature']:
      doSignature(users)
    elif command == 'vacation':
      doVacation(users)
    elif command in ['delegate', 'delegates']:
      addDelegates(users, 4)
    elif command == 'watch':
      if len(sys.argv) > 4:
        watchWhat = sys.argv[4].lower()
      else:
        watchWhat = 'gmail'
      if watchWhat == 'gmail':
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

# Run from command line
if __name__ == "__main__":
  if sys.platform.startswith('win'):
    freeze_support()
  if sys.version_info[0] < 3 or sys.version_info[1] < 7:
    systemErrorExit(5, 'GAM requires Python 3.7 or newer. You are running %s.%s.%s. Please upgrade your Python version or use one of the binary GAM downloads.' % sys.version_info[:3])
  sys.exit(ProcessGAMCommand(sys.argv))
