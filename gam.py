#!/usr/bin/env python
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

u"""GAM is a command line tool which allows Administrators to control their Google Apps domain and accounts.

With GAM you can programatically create users, turn on/off services for users like POP and Forwarding and much more.
For more information, see http://git.io/gam

"""

__author__ = u'Jay Lee <jay0lee@gmail.com>'
__version__ = u'3.51'
__license__ = u'Apache License 2.0 (http://www.apache.org/licenses/LICENSE-2.0)'

import sys, os, time, datetime, random, socket, csv, platform, re, calendar, base64, string
import subprocess

import json
import httplib2
import googleapiclient
import googleapiclient.discovery
import googleapiclient.errors
import googleapiclient.http
import oauth2client.client
import oauth2client.file
import oauth2client.tools
import mimetypes
import ntpath

is_frozen = getattr(sys, 'frozen', '')

GAM = u'GAM'
TRUE = u'true'
FALSE = u'false'
TRUE_FALSE = [TRUE, FALSE]
true_values = [TRUE, u'on', u'yes', u'enabled', u'1']
false_values = [FALSE, u'off', u'no', u'disabled', u'0']
usergroup_types = [u'user', u'users', u'group', u'ou', u'org',
                   u'ou_and_children', u'ou_and_child', u'query',
                   u'license', u'licenses', u'licence', u'licences', u'file', u'all',
                   u'cros']
ERROR = u'ERROR'
ERROR_PREFIX = ERROR+u': '
WARNING = u'WARNING'
WARNING_PREFIX = WARNING+u': '
FN_CACERT_PEM = u'cacert.pem'
FN_CLIENT_SECRETS_JSON = u'client_secrets.json'
FN_OAUTH2_TXT = u'oauth2.txt'
FN_OAUTH2SERVICE_JSON = u'oauth2service.json'
FN_EXTRA_ARGS_TXT = u'extra-args.txt'
GAMCACHE = u'gamcache'
MY_CUSTOMER = u'my_customer'
UNKNOWN_DOMAIN = u'Unknown'
#
# Global variables
#
# Shared by batch_worker and run_batch
q = None
#
# Location of gam.cfg, if not set, appdirs user_config_dir will be used
EV_GAM_CFG_HOME = u'GAM_CFG_HOME'
# Name of config file
GAM_CFG = u'gam.cfg'
GAM_BAK = u'gam.bak'
# Path to gam, assigned in SetGlobalVariables after the command line is cleaned up for Windows
GC_GAM_PATH = u'gam_path'
# Where will CSV files be written
GC_CSVFILE = u'csvfile'
#
# Global variables derived from values in gam.cfg
#
# Full path to cacert.pem
GC_CACERT_PEM = u'cacert_pem'
# Extra arguments to pass to GAPI functions
GC_EXTRA_ARGS = u'extra_args'
#
# Global variables defined in  gam.cfg
#
# Automatically generate gam batch command if number of users specified in gam users xxx command exceeds this number
# Default: 0, don't automatically generate gam batch commands
GC_AUTO_BATCH_MIN = u'auto_batch_min'
# GAM cache directory. If no_cache is specified, this variable will be set to None
GC_CACHE_DIR = u'cache_dir'
# Path to client_secrets.json
GC_CLIENT_SECRETS_JSON = u'client_secrets_json'
# GAM config directory containing client_secrets.json, oauth2.txt, oauth2service.json, extra_args.txt
GC_CONFIG_DIR = u'config_dir'
# custmerId from gam.cfg or retrieved from Google
GC_CUSTOMER_ID = u'customer_id'
# If debug_level > 0: extra_args[u'prettyPrint'] = True, httplib2.debuglevel = gam_debug_level, appsObj.debug = True
GC_DEBUG_LEVEL = u'debug_level'
# Domain from gam.cfg or oauth2.txt
GC_DOMAIN = u'domain'
# Google Drive download directory
GC_DRIVE_DIR = u'drive_dir'
# Time of last GAM update check
GC_LAST_UPDATE_CHECK = u'last_update_check'
# Maximum number of items to process without confirmation
GC_MAX_MESSAGES_TO_PROCESS = u'max_messages_to_process'
# If no_browser is False, writeCSVfile won't open a browser when todrive is set
# and doRequestOAuth prints a link and waits for the verification code when oauth2.txt is being created
GC_NO_BROWSER = u'no_browser'
# Disable GAM API caching
GC_NO_CACHE = u'no_cache'
# Disable GAM update check
GC_NO_UPDATE_CHECK = u'no_update_check'
# Disable SSL certificate validation
GC_NO_VERIFY_SSL = u'no_verify_ssl'
# Number of threads for gam batch
GC_NUM_THREADS = u'num_threads'
# Path to oauth2.txt
GC_OAUTH2_TXT = u'oauth2_txt'
# Path to oauth2service.json
GC_OAUTH2SERVICE_JSON = u'oauth2service_json'
# Default section to use for processing
GC_SECTION = u'section'
# Enable/disable "Getting ... " messages
GC_SHOW_GETTINGS = u'show_gettings'
# Default value for gam info user foo@bar.com
GC_SHOW_LICENSES = u'show_licenses'

GC_DEFAULTS = {
  GC_AUTO_BATCH_MIN: 0,
  GC_CACHE_DIR: u'',
  GC_CLIENT_SECRETS_JSON: FN_CLIENT_SECRETS_JSON,
  GC_CONFIG_DIR: u'',
  GC_CUSTOMER_ID: u'',
  GC_DEBUG_LEVEL: 0,
  GC_DOMAIN: u'',
  GC_DRIVE_DIR: u'',
  GC_LAST_UPDATE_CHECK: 0,
  GC_MAX_MESSAGES_TO_PROCESS: 1,
  GC_NO_BROWSER: FALSE,
  GC_NO_CACHE: FALSE,
  GC_NO_UPDATE_CHECK: FALSE,
  GC_NO_VERIFY_SSL: FALSE,
  GC_NUM_THREADS: 5,
  GC_OAUTH2_TXT: FN_OAUTH2_TXT,
  GC_OAUTH2SERVICE_JSON: FN_OAUTH2SERVICE_JSON,
  GC_SECTION: u'',
  GC_SHOW_GETTINGS: TRUE,
  GC_SHOW_LICENSES: TRUE,
  }

GC_Values = {}

GC_TYPE_BOOLEAN = u'bool'
GC_TYPE_DIRECTORY = u'dire'
GC_TYPE_FILE = u'file'
GC_TYPE_INTEGER = u'inte'
GC_TYPE_STRING = u'stri'

GC_VAR_TYPE_KEY = u'type'
GC_VAR_LIMITS_KEY = u'limits'

GC_VAR_INFO = {
  GC_AUTO_BATCH_MIN: {GC_VAR_TYPE_KEY: GC_TYPE_INTEGER, GC_VAR_LIMITS_KEY: (0, None)},
  GC_CACHE_DIR: {GC_VAR_TYPE_KEY: GC_TYPE_DIRECTORY},
  GC_CLIENT_SECRETS_JSON: {GC_VAR_TYPE_KEY: GC_TYPE_FILE},
  GC_CONFIG_DIR: {GC_VAR_TYPE_KEY: GC_TYPE_DIRECTORY},
  GC_CUSTOMER_ID: {GC_VAR_TYPE_KEY: GC_TYPE_STRING},
  GC_DEBUG_LEVEL: {GC_VAR_TYPE_KEY: GC_TYPE_INTEGER, GC_VAR_LIMITS_KEY: (0, None)},
  GC_DOMAIN: {GC_VAR_TYPE_KEY: GC_TYPE_STRING},
  GC_DRIVE_DIR: {GC_VAR_TYPE_KEY: GC_TYPE_DIRECTORY},
  GC_LAST_UPDATE_CHECK: {GC_VAR_TYPE_KEY: GC_TYPE_INTEGER, GC_VAR_LIMITS_KEY: (0, None)},
  GC_MAX_MESSAGES_TO_PROCESS: {GC_VAR_TYPE_KEY: GC_TYPE_INTEGER, GC_VAR_LIMITS_KEY: (0, None)},
  GC_NO_BROWSER: {GC_VAR_TYPE_KEY: GC_TYPE_BOOLEAN},
  GC_NO_CACHE: {GC_VAR_TYPE_KEY: GC_TYPE_BOOLEAN},
  GC_NO_UPDATE_CHECK: {GC_VAR_TYPE_KEY: GC_TYPE_BOOLEAN},
  GC_NO_VERIFY_SSL: {GC_VAR_TYPE_KEY: GC_TYPE_BOOLEAN},
  GC_NUM_THREADS: {GC_VAR_TYPE_KEY: GC_TYPE_INTEGER, GC_VAR_LIMITS_KEY: (1, None)},
  GC_OAUTH2_TXT: {GC_VAR_TYPE_KEY: GC_TYPE_FILE},
  GC_OAUTH2SERVICE_JSON: {GC_VAR_TYPE_KEY: GC_TYPE_FILE},
  GC_SECTION: {GC_VAR_TYPE_KEY: GC_TYPE_STRING},
  GC_SHOW_GETTINGS: {GC_VAR_TYPE_KEY: GC_TYPE_BOOLEAN},
  GC_SHOW_LICENSES: {GC_VAR_TYPE_KEY: GC_TYPE_BOOLEAN},
  }

GC_VAR_ALIASES = {
  u'autobatchmin':  u'auto_batch_min',
  u'cachedir':  u'cache_dir',
  u'clientsecretsjson':  u'client_secrets_json',
  u'configdir':  u'config_dir',
  u'customerid':  u'customer_id',
  u'debuglevel':  u'debug_level',
  u'domain':  u'domain',
  u'drivedir':  u'drive_dir',
  u'lastupdatecheck':  u'last_update_check',
  u'maxmessagestoprocess':  u'max_messages_to_process',
  u'nobrowser':  u'no_browser',
  u'nocache':  u'no_cache',
  u'noupdatecheck':  u'no_update_check',
  u'noverifyssl':  u'no_verify_ssl',
  u'numthreads':  u'num_threads',
  u'oauth2txt':  u'oauth2_txt',
  u'oauth2servicejson':  u'oauth2service_json',
  u'section':  u'section',
  u'showgettings':  u'show_gettings',
  u'showlicenses':  u'show_licenses',
  }

# Command line batch/csv keywords
GAM_CMD = u'gam'
COMMIT_BATCH_CMD = u'commit-batch'
#
# Command line redirect/select/config arguments
# Command line select/options arguments
REDIRECT_CMD = 'redirect'
REDIRECT_CSV_CMD = 'csv'
REDIRECT_STDOUT_CMD = 'stdout'
REDIRECT_STDERR_CMD = 'stderr'
REDIRECT_SUB_CMDS = [REDIRECT_CSV_CMD, REDIRECT_STDOUT_CMD, REDIRECT_STDERR_CMD]
REDIRECT_MODE_MAP = {u'append': 'a', u'write': 'w'}
SELECT_CMD = u'select'
SELECT_SAVE_CMD = u'save'
SELECT_VERIFY_CMD = u'verify'
SELECT_CSVFILE_CMD = u'csvfile'
CONFIG_CMD = u'config'
CONFIG_CREATE_CMD = u'create'
CONFIG_CREATE_OVERWRITE_CMD = u'overwrite'
CONFIG_DELETE_CMD = u'delete'
CONFIG_SELECT_CMD = u'select'
CONFIG_MAKE_CMD = u'make'
CONFIG_COPY_CMD = u'copy'
CONFIG_RESET_CMD = u'reset'
CONFIG_SET_CMD = u'set'
CONFIG_SAVE_CMD = u'save'
CONFIG_BACKUP_CMD = u'backup'
CONFIG_RESTORE_CMD = u'restore'
CONFIG_VERIFY_CMD = u'verify'
CONFIG_PRINT_CMD = u'print'
CONFIG_SUB_CMDS = [CONFIG_CREATE_CMD, CONFIG_DELETE_CMD, CONFIG_SELECT_CMD,
                   CONFIG_MAKE_CMD, CONFIG_COPY_CMD,
                   CONFIG_RESET_CMD, CONFIG_SET_CMD,
                   CONFIG_SAVE_CMD, CONFIG_BACKUP_CMD, CONFIG_RESTORE_CMD,
                   CONFIG_VERIFY_CMD, CONFIG_PRINT_CMD,
                   CONFIG_CMD,
                  ]
#
def convertUTF8(data):
  import collections
  if isinstance(data, str):
    return data
  elif isinstance(data, unicode):
    return data.encode('utf-8')
  elif isinstance(data, collections.Mapping):
    return dict(map(convertUTF8, data.iteritems()))
  elif isinstance(data, collections.Iterable):
    return type(data)(map(convertUTF8, data))
  else:
    return data

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
    start = argc.value - len(sys.argv)
    return [argv[i] for i in xrange(start, argc.value)]

from HTMLParser import HTMLParser
from re import sub
from sys import stderr
from traceback import print_exc

class _DeHTMLParser(HTMLParser):
  def __init__(self):
    HTMLParser.__init__(self)
    self.__text = []

  def handle_data(self, data):
    text = data.strip()
    if len(text) > 0:
      text = sub('[ \t\r\n]+', ' ', text)
      self.__text.append(text + ' ')

  def handle_starttag(self, tag, attrs):
    if tag == 'p':
      self.__text.append('\n\n')
    elif tag == 'br':
      self.__text.append('\n')

  def handle_startendtag(self, tag, attrs):
    if tag == 'br':
      self.__text.append('\n\n')

  def text(self):
    return ''.join(self.__text).strip()


def dehtml(text):
  try:
    parser = _DeHTMLParser()
    parser.feed(text.encode('utf-8'))
    parser.close()
    return parser.text()
  except:
    print_exc(file=stderr)
    return text

def showUsage():
  doGAMVersion()
  print u'''
Usage: gam [OPTIONS]...

GAM. Retrieve or set Google Apps domain,
user, group and alias settings. Exhaustive list of commands
can be found at: https://github.com/jay0lee/GAM/wiki

Examples:
gam info domain
gam create user jsmith firstname John lastname Smith password secretpass
gam update user jsmith suspended on
gam.exe update group announcements add member jsmith
...

'''
def integerLimits(minVal, maxVal):
  if (minVal != None) and (maxVal != None):
    return u'integer {0}<=x<={1}'.format(minVal, maxVal)
  if minVal != None:
    return u'integer x>={0}'.format(minVal)
  if maxVal != None:
    return u'integer x<={0}'.format(maxVal)
  return u'integer x'
#
# Open a file
#
def openFile(filename, mode='rb'):
  try:
    if filename != u'-':
      f = open(filename, mode)
    else:
      import StringIO
      f = StringIO.StringIO(unicode(sys.stdin.read()))
    return f
  except IOError as e:
    sys.stderr.write(u'{0}{1}\n'.format(ERROR_PREFIX, e))
    sys.exit(6)
#
# Read a file
#
def readFile(filename, mode='rb', continueOnError=False, displayError=True):
  try:
    if filename != u'-':
      with open(filename, mode) as f:
        return f.read()
    else:
      return unicode(sys.stdin.read())
  except IOError as e:
    if displayError:
      sys.stderr.write(u'{0}{1}\n'.format(WARNING_PREFIX, e))
    if continueOnError:
      return None
    sys.exit(6)
#
# Write a file
#
def writeFile(filename, data, mode='wb', continueOnError=False):
  try:
    with open(filename, mode) as f:
      f.write(data)
    return True
  except IOError as e:
    sys.stderr.write(u'{0}{1}\n'.format(ERROR_PREFIX, e))
    if continueOnError:
      return False
    sys.exit(6)
#
# Set global variables from config file
# Check for GAM updates based on status of no_update_check in config file
#
def SetGlobalVariables():
  global GC_Values
  import ConfigParser, collections
  from appdirs import user_config_dir, user_cache_dir

  def _getOldEnvVar(itemName, envVar):
    try:
      value = os.environ[envVar]
      if GC_VAR_INFO[itemName][GC_VAR_TYPE_KEY] == GC_TYPE_INTEGER:
        try:
          number = int(value)
          minVal, maxVal = GC_VAR_INFO[itemName][GC_VAR_LIMITS_KEY]
          if number < minVal:
            number = minVal
          elif maxVal and (number > maxVal):
            number = maxVal
        except ValueError:
          value = GC_DEFAULTS[itemName]
        value = str(number)
    except KeyError:
      value = GC_DEFAULTS[itemName]
    gamcfg.set(ConfigParser.DEFAULTSECT, itemName, unicode(value))

  def _getOldSignalFile(itemName, fileName, trueValue=TRUE, falseValue=FALSE):
    gamcfg.set(ConfigParser.DEFAULTSECT, itemName, trueValue if os.path.isfile(os.path.join(GC_Values[GC_GAM_PATH], fileName)) else falseValue)

  def _getOldEnvVarsSignalFiles():
    _getOldEnvVar(GC_CONFIG_DIR, u'GAMCONFIGDIR')
    _getOldEnvVar(GC_CACHE_DIR, u'GAMCACHEDIR')
    _getOldEnvVar(GC_DRIVE_DIR, u'GAMDRIVEDIR')
    _getOldEnvVar(GC_OAUTH2_TXT, u'OAUTHFILE')
    _getOldEnvVar(GC_OAUTH2SERVICE_JSON, u'OAUTHSERVICEFILE')
    value = gamcfg.get(ConfigParser.DEFAULTSECT, GC_OAUTH2SERVICE_JSON, raw=True)
    if value.find(u'.') == -1:
      gamcfg.set(ConfigParser.DEFAULTSECT, GC_OAUTH2SERVICE_JSON, value+u'.json')
    _getOldEnvVar(GC_CLIENT_SECRETS_JSON, u'CLIENTSECRETS')
    _getOldEnvVar(GC_DOMAIN, u'GA_DOMAIN')
    _getOldEnvVar(GC_CUSTOMER_ID, u'CUSTOMER_ID')
    _getOldEnvVar(GC_NUM_THREADS, u'GAM_THREADS')
    _getOldEnvVar(GC_AUTO_BATCH_MIN, u'GAM_AUTOBATCH')
    _getOldSignalFile(GC_DEBUG_LEVEL, u'debug.gam', trueValue=u'4', falseValue=u'0')
    _getOldSignalFile(GC_NO_VERIFY_SSL, u'noverifyssl.txt')
    _getOldSignalFile(GC_NO_BROWSER, u'nobrowser.txt')
    _getOldSignalFile(GC_NO_CACHE, u'nocache.txt')
    _getOldSignalFile(GC_NO_UPDATE_CHECK, u'noupdatecheck.txt')
    try:
      with open(os.path.join(GC_Values[GC_GAM_PATH], u'lastupdatecheck.txt'), 'rU') as f:
        latestUpdateCheck = int(f.readline())
    except:
      latestUpdateCheck = 0
    gamcfg.set(ConfigParser.DEFAULTSECT, GC_LAST_UPDATE_CHECK, str(latestUpdateCheck))

  def _checkMakeDir(itemName):
    if not os.path.isdir(GC_DEFAULTS[itemName]):
      try:
        os.makedirs(GC_DEFAULTS[itemName])
      except OSError as e:
        if not os.path.isdir(GC_DEFAULTS[itemName]):
          sys.stderr.write(u'{0}{1}\n'.format(ERROR_PREFIX, e))
          sys.exit(13)

  def _copyConfigFile(itemName):
    srcFile = os.path.expanduser(gamcfg.get(ConfigParser.DEFAULTSECT, itemName, raw=True))
    if not os.path.isabs(srcFile):
      srcFile = os.path.join(GC_Values[GC_GAM_PATH], srcFile)
    dstFile = os.path.join(GC_DEFAULTS[GC_CONFIG_DIR], os.path.basename(srcFile))
    if srcFile != dstFile:
      data = readFile(srcFile, mode=u'rU', continueOnError=True, displayError=False)
      if (data != None) and writeFile(dstFile, data, continueOnError=True):
        writeFile(dstFile, data)
        gamcfg.set(ConfigParser.DEFAULTSECT, itemName, os.path.basename(srcFile))

  def _getCfgBoolean(sectionName, itemName):
    value = gamcfg.get(sectionName, itemName, raw=True)
    if value in true_values:
      return True
    if value in false_values:
      return False
    sys.stderr.write(u'{0}Config File: {1}, Section: {2}, Item: {3}, Value: {4}, expected {5}\n'.format(ERROR_PREFIX, configFileName, sectionName, itemName, value, u','.join(TRUE_FALSE)))
    status[u'errors'] = True
    return False

  def _getCfgInteger(sectionName, itemName):
    value = gamcfg.get(sectionName, itemName, raw=True)
    minVal, maxVal = GC_VAR_INFO[itemName][GC_VAR_LIMITS_KEY]
    try:
      number = int(value)
      if (number >= minVal) and (not maxVal or (number <= maxVal)):
        return number
    except ValueError:
      pass
    sys.stderr.write(u'{0}Config File: {1}, Section: {2}, Item: {3}, Value: {4}, expected {5}\n'.format(ERROR_PREFIX, configFileName, sectionName, itemName, value, integerLimits(minVal, maxVal)))
    status[u'errors'] = True
    return 0

  def _getCfgSection(sectionName, itemName):
    value = gamcfg.get(sectionName, itemName, raw=True)
    if not value:
      return ConfigParser.DEFAULTSECT
    if gamcfg.has_section(value):
      return value
    sys.stderr.write(u'{0}Config File: {1}, Section: {2}, Item: {3}, Value: {4}, Not Found\n'.format(ERROR_PREFIX, configFileName, sectionName, itemName, value))
    status[u'errors'] = True
    return ConfigParser.DEFAULTSECT

  def _getCfgString(sectionName, itemName):
    return gamcfg.get(sectionName, itemName, raw=True)

  def _getCfgDirectory(sectionName, itemName):
    dirPath = os.path.expanduser(gamcfg.get(sectionName, itemName, raw=True))
    if (not dirPath) or (not os.path.isabs(dirPath)):
      if (sectionName != ConfigParser.DEFAULTSECT) and (gamcfg.has_option(sectionName, itemName)):
        dirPath = os.path.join(os.path.expanduser(gamcfg.get(ConfigParser.DEFAULTSECT, itemName, raw=True)), dirPath)
      if not os.path.isabs(dirPath):
        dirPath = os.path.join(gamCfgHome, dirPath)
    return dirPath

  def _getCfgFile(sectionName, itemName):
    value = os.path.expanduser(gamcfg.get(sectionName, itemName, raw=True))
    if not os.path.isabs(value):
      value = os.path.expanduser(os.path.join(_getCfgDirectory(sectionName, GC_CONFIG_DIR), value))
    return value

  def _readConfigFile(config, fileName, action=None):
    try:
      with open(fileName, 'rU') as f:
        config.readfp(f)
      if action:
        print u'Config File: {0}, {1}'.format(fileName, action)
    except (ConfigParser.MissingSectionHeaderError, ConfigParser.ParsingError) as e:
      sys.stderr.write(u'{0}Config File: {1}, Invalid: {2}\n'.format(ERROR_PREFIX, fileName, e.message))
      sys.exit(13)
    except IOError as e:
      sys.stderr.write(u'{0}{1}\n'.format(ERROR_PREFIX, e))
      sys.exit(13)

  def _writeConfigFile(config, fileName, action=None):
    try:
      with open(fileName, 'wb') as f:
        config.write(f)
      if action:
        print u'Config File: {0}, {1}'.format(fileName, action)
    except IOError as e:
      sys.stderr.write(u'{0}{1}\n'.format(ERROR_PREFIX, e))

  def _verifyValues():
    print u'Section: {0}'.format(sectionName)
    for itemName in sorted(GC_VAR_INFO):
      cfgValue = gamcfg.get(sectionName, itemName, raw=True)
      if GC_VAR_INFO[itemName][GC_VAR_TYPE_KEY] == GC_TYPE_FILE:
        expdValue = _getCfgFile(sectionName, itemName)
        if cfgValue != expdValue:
          cfgValue = u'{0} ; {1}'.format(cfgValue, expdValue)
      elif GC_VAR_INFO[itemName][GC_VAR_TYPE_KEY] == GC_TYPE_DIRECTORY:
        expdValue = _getCfgDirectory(sectionName, itemName)
        if cfgValue != expdValue:
          cfgValue = u'{0} ; {1}'.format(cfgValue, expdValue)
      elif (itemName == GC_SECTION) and (sectionName != ConfigParser.DEFAULTSECT):
        continue
      print u'  {0} = {1}'.format(itemName, cfgValue)

  def _chkCfgDirectories(sectionName):
    result = True
    for itemName in GC_VAR_INFO:
      if GC_VAR_INFO[itemName][GC_VAR_TYPE_KEY] == GC_TYPE_DIRECTORY:
        dirPath = GC_Values[itemName]
        if not os.path.isdir(dirPath):
          sys.stderr.write(u'{0}Config File: {1}, Section: {2}, Item: {3}, Value: {4}, Invalid Path\n'.format(ERROR_PREFIX, configFileName, sectionName, itemName, dirPath))
          result = False
    return result

  def _chkCfgFiles(sectionName):
    result = True
    for itemName in GC_VAR_INFO:
      if GC_VAR_INFO[itemName][GC_VAR_TYPE_KEY] == GC_TYPE_FILE:
        fileName = GC_Values[itemName]
        if not os.path.isfile(fileName):
          sys.stderr.write(u'{0}Config File: {1}, Section: {2}, Item: {3}, Value: {4}, Not Found\n'.format(WARNING_PREFIX, configFileName, sectionName, itemName, fileName))
          result = False
    return result

  def _setCSVFile(csvFile):
    if csvFile.replace(u'_', u'') == u'sectionname':
      csvFile = sectionName+u'.csv'
    csvFile = os.path.expanduser(csvFile)
    if not os.path.isabs(csvFile):
      csvFile = os.path.join(gamcfg.get(sectionName, GC_DRIVE_DIR, raw=True), csvFile)
    GC_Values[GC_CSVFILE] = openFile(csvFile, mode='w')

  def _setSTDFile(stdfile, ext, mode):
    if stdfile.replace(u'_', u'') == u'sectionname':
      stdfile = sectionName+'.'+ext
    stdfile = os.path.expanduser(stdfile)
    if not os.path.isabs(stdfile):
      stdfile = os.path.join(gamcfg.get(sectionName, GC_DRIVE_DIR, raw=True), stdfile)
    if ext == u'out':
      sys.stdout = openFile(stdfile, mode=mode)
    else:
      sys.stderr = openFile(stdfile, mode=mode)

  GC_Values = {GC_GAM_PATH: os.path.dirname(os.path.realpath(sys.argv[0]))}
  status = {u'errors': False}
  try:
# If GAM_CFG_HOME environment is set, use it for config path, use gamPath/gamcache for cache and gamPath for drive
    gamCfgHome = os.environ[EV_GAM_CFG_HOME]
    GC_DEFAULTS[GC_CACHE_DIR] = os.path.join(GC_Values[GC_GAM_PATH], GAMCACHE)
    GC_DEFAULTS[GC_DRIVE_DIR] = GC_Values[GC_GAM_PATH]
  except KeyError:
# If GAM_CFG_HOME environment is not set, use appdirs for config/cache paths, use ~/Downloads for drive
    gamCfgHome = user_config_dir(appname=GAM, appauthor=False)
    GC_DEFAULTS[GC_CACHE_DIR] = user_cache_dir(appname=GAM, appauthor=False)
    GC_DEFAULTS[GC_DRIVE_DIR] = os.path.expanduser(u'~/Downloads')
  GC_DEFAULTS[GC_CONFIG_DIR] = gamCfgHome

  gamcfg = ConfigParser.SafeConfigParser(defaults=collections.OrderedDict(sorted(GC_DEFAULTS.items(), key=lambda t: t[0])))
  configFileName = os.path.join(gamCfgHome, GAM_CFG)
  if not os.path.isfile(configFileName):
    _getOldEnvVarsSignalFiles()
    _checkMakeDir(GC_CONFIG_DIR)
    _checkMakeDir(GC_CACHE_DIR)
    for itemName in GC_VAR_INFO:
      if GC_VAR_INFO[itemName][GC_VAR_TYPE_KEY] == GC_TYPE_FILE:
        _copyConfigFile(itemName)
    _writeConfigFile(gamcfg, configFileName, action=u'Initialized')
  else:
    _readConfigFile(gamcfg, configFileName)
  i = 1
# select <SectionName> [save] [verify]
  if (i < len(sys.argv)) and (sys.argv[i] == SELECT_CMD):
    i += 1
    if i == len(sys.argv):
      sys.stderr.write(u'{0}{1} "", should be <SectionName>\n'.format(ERROR_PREFIX, SELECT_CMD))
      sys.exit(3)
    sectionName = sys.argv[i]
    i += 1
    if (not sectionName) or (sectionName.upper() == ConfigParser.DEFAULTSECT):
      sectionName = ConfigParser.DEFAULTSECT
    elif not gamcfg.has_section(sectionName):
      sys.stderr.write(u'{0}{1} "{2}", Not Found\n'.format(ERROR_PREFIX, SELECT_CMD, sectionName))
      sys.exit(3)
    while i < len(sys.argv):
      my_arg = sys.argv[i].lower()
      if my_arg == SELECT_SAVE_CMD:
        i += 1
        gamcfg.set(ConfigParser.DEFAULTSECT, GC_SECTION, sectionName)
        _writeConfigFile(gamcfg, configFileName, action=u'Saved')
      elif my_arg == SELECT_VERIFY_CMD:
        i += 1
        _verifyValues()
      else:
        break
# config ((create <SectionName> [overwrite])|(delete <SectionName>)|(select <SectionName>)|
#         (make <Directory>)|(copy <FromFile> <ToFile)|
#         (reset <VariableName>)|(set <VariableName> <Value>)|
#         save|(backup <FileName>)|(restore <FileName>)|
#         verify|print|
#        )* [config]
  elif (i < len(sys.argv)) and (sys.argv[i] == CONFIG_CMD):
    i += 1
    sectionName = _getCfgSection(ConfigParser.DEFAULTSECT, GC_SECTION)
    while i < len(sys.argv):
      my_arg = sys.argv[i].lower()
      if my_arg not in CONFIG_SUB_CMDS:
        sys.stderr.write(u'{0}{1} "{2}", should be {3}\n'.format(ERROR_PREFIX, CONFIG_CMD, my_arg, u','.join(CONFIG_SUB_CMDS)))
        sys.exit(3)
      i += 1
# create <SectionName> [overwrite]
      if my_arg == CONFIG_CREATE_CMD:
        if i == len(sys.argv):
          sys.stderr.write(u'{0}{1} "", should be <SectionName>\n'.format(ERROR_PREFIX, my_arg))
          sys.exit(3)
        value = sys.argv[i]
        i += 1
        if value.upper() == ConfigParser.DEFAULTSECT:
          sys.stderr.write(u'{0}{1} "{2}", Invalid\n'.format(ERROR_PREFIX, my_arg, value))
          sys.exit(3)
        if (i < len(sys.argv)) and (sys.argv[i].lower() == CONFIG_CREATE_OVERWRITE_CMD):
          overwrite = True
          i += 1
        else:
          overwrite = False
        if gamcfg.has_section(value):
          if not overwrite:
            sys.stderr.write(u'{0}{1} "{2}", Duplicate\n'.format(ERROR_PREFIX, my_arg, value))
            sys.exit(3)
        else:
          gamcfg.add_section(value)
        sectionName = value
# delete <SectionName>
      elif my_arg == CONFIG_DELETE_CMD:
        if i == len(sys.argv):
          sys.stderr.write(u'{0}{1} "", should be <SectionName>\n'.format(ERROR_PREFIX, my_arg))
          sys.exit(3)
        value = sys.argv[i]
        i += 1
        if value.upper() == ConfigParser.DEFAULTSECT:
          sys.stderr.write(u'{0}{1} "{2}", Invalid\n'.format(ERROR_PREFIX, my_arg, value))
          sys.exit(3)
        if not gamcfg.has_section(value):
          sys.stderr.write(u'{0}{1} "{2}", Not Found\n'.format(ERROR_PREFIX, my_arg, value))
          sys.exit(3)
        gamcfg.remove_section(value)
        sectionName = ConfigParser.DEFAULTSECT
        if gamcfg.get(ConfigParser.DEFAULTSECT, GC_SECTION, raw=True) == value:
          gamcfg.set(ConfigParser.DEFAULTSECT, GC_SECTION, u'')
# select <SectionName>
      elif my_arg == CONFIG_SELECT_CMD:
        if i == len(sys.argv):
          sys.stderr.write(u'{0}{1} "", should be <SectionName>\n'.format(ERROR_PREFIX, my_arg))
          sys.exit(3)
        value = sys.argv[i]
        i += 1
        if (not value) or (value.upper() == ConfigParser.DEFAULTSECT):
          value = u''
          sectionName = ConfigParser.DEFAULTSECT
        elif not gamcfg.has_section(value):
          sys.stderr.write(u'{0}{1} "{2}", Not Found\n'.format(ERROR_PREFIX, my_arg, value))
          sys.exit(3)
        else:
          sectionName = value
# make <Directory>
      elif my_arg == CONFIG_MAKE_CMD:
        if i == len(sys.argv):
          sys.stderr.write(u'{0}{1} "", should be <Directory>\n'.format(ERROR_PREFIX, my_arg))
          sys.exit(3)
        dstPath = os.path.expanduser(sys.argv[i])
        i += 1
        if not os.path.isabs(dstPath):
          dstPath = os.path.join(gamcfg.get(ConfigParser.DEFAULTSECT, GC_CONFIG_DIR, raw=True), dstPath)
        if not os.path.isdir(dstPath):
          try:
            os.makedirs(dstPath)
          except OSError as e:
            if not os.path.isdir(dstPath):
              sys.stderr.write(u'{0}{1}\n'.format(ERROR_PREFIX, e))
              sys.exit(6)
# copy <FromFile> <ToFile>
      elif my_arg == CONFIG_COPY_CMD:
        if i == len(sys.argv):
          sys.stderr.write(u'{0}{1} "", should be <FromFile>\n'.format(ERROR_PREFIX, my_arg))
          sys.exit(3)
        value = sys.argv[i]
        i += 1
        srcFile = os.path.expanduser(value)
        if not os.path.isabs(srcFile):
          srcFile = os.path.join(GC_Values[GC_GAM_PATH], srcFile)
        if i == len(sys.argv):
          sys.stderr.write(u'{0}{1} {2} "", should be <ToFile>\n'.format(ERROR_PREFIX, my_arg, value))
          sys.exit(3)
        dstFile = os.path.expanduser(sys.argv[i])
        i += 1
        if not os.path.isabs(dstFile):
          dstFile = os.path.join(gamcfg.get(sectionName, GC_CONFIG_DIR, raw=True), dstFile)
        data = readFile(srcFile, mode=u'rU')
        writeFile(dstFile, data)
# reset <VariableName>
      elif my_arg == CONFIG_RESET_CMD:
        if i < len(sys.argv):
          itemName = sys.argv[i].lower().replace(u'_', u'')
          i += 1
        else:
          itemName = u''
        if itemName not in GC_VAR_ALIASES:
          sys.stderr.write(u'{0}{1} "{2}", should be {3}\n'.format(ERROR_PREFIX, my_arg, itemName, u'|'.join(sorted(GC_DEFAULTS.keys()))))
          sys.exit(3)
        itemName = GC_VAR_ALIASES[itemName]
        if itemName in [GC_NO_UPDATE_CHECK, GC_LAST_UPDATE_CHECK]:
          gamcfg.set(ConfigParser.DEFAULTSECT, itemName, unicode(GC_DEFAULTS[itemName]))
        elif itemName != GC_SECTION:
          if sectionName != ConfigParser.DEFAULTSECT:
            gamcfg.remove_option(sectionName, itemName)
          else:
            gamcfg.set(ConfigParser.DEFAULTSECT, itemName, unicode(GC_DEFAULTS[itemName]))
        else:
          gamcfg.set(ConfigParser.DEFAULTSECT, itemName, u'')
# set <VariableName> <Value>
      elif my_arg == CONFIG_SET_CMD:
        if i < len(sys.argv):
          itemName = sys.argv[i].lower().replace(u'_', u'')
          i += 1
        else:
          itemName = u''
        if itemName not in GC_VAR_ALIASES:
          sys.stderr.write(u'{0}{1} "{2}", should be {3}\n'.format(ERROR_PREFIX, my_arg, itemName, u'|'.join(sorted(GC_DEFAULTS.keys()))))
          sys.exit(3)
        itemName = GC_VAR_ALIASES[itemName]
        if i == len(sys.argv):
          sys.stderr.write(u'{0}{1} {2} "", should be <Value>\n'.format(ERROR_PREFIX, my_arg, itemName))
          sys.exit(3)
        value = sys.argv[i]
        i += 1
        if itemName == GC_SECTION:
          if (not value) or (value.upper() == ConfigParser.DEFAULTSECT):
            value = u''
          elif not gamcfg.has_section(value):
            sys.stderr.write(u'{0}{1} {2} "{3}", Not Found \n'.format(ERROR_PREFIX, CONFIG_SET_CMD, itemName, value))
            sys.exit(3)
          gamcfg.set(ConfigParser.DEFAULTSECT, GC_SECTION, value)
          continue
        elif GC_VAR_INFO[itemName][GC_VAR_TYPE_KEY] == GC_TYPE_BOOLEAN:
          value = value.lower()
          if (value not in true_values) and (value not in false_values):
            sys.stderr.write(u'{0}{1} {2} "{3}", should be {4}\n'.format(ERROR_PREFIX, CONFIG_SET_CMD, itemName, value, u'|'.join(TRUE_FALSE)))
            sys.exit(3)
          if itemName == GC_NO_UPDATE_CHECK:
            gamcfg.set(ConfigParser.DEFAULTSECT, itemName, value)
            continue
        elif GC_VAR_INFO[itemName][GC_VAR_TYPE_KEY] == GC_TYPE_INTEGER:
          minVal, maxVal = GC_VAR_INFO[itemName][GC_VAR_LIMITS_KEY]
          try:
            value = int(value)
            if (value < minVal) or (maxVal and (value > maxVal)):
              sys.stderr.write(u'{0}{1} {2} "{3}", should be {4}\n'.format(ERROR_PREFIX, CONFIG_SET_CMD, itemName, value, integerLimits(minVal, maxVal)))
              sys.exit(3)
            value = str(value)
          except ValueError:
            sys.stderr.write(u'{0}{1} {2} "{3}", should be {4}\n'.format(ERROR_PREFIX, CONFIG_SET_CMD, itemName, value, integerLimits(minVal, maxVal)))
            sys.exit(3)
          if itemName == GC_LAST_UPDATE_CHECK:
            gamcfg.set(ConfigParser.DEFAULTSECT, itemName, value)
            continue
        elif GC_VAR_INFO[itemName][GC_VAR_TYPE_KEY] == GC_TYPE_DIRECTORY:
          fullPath = os.path.expanduser(value)
          if (sectionName != ConfigParser.DEFAULTSECT) and (not os.path.isabs(fullPath)):
            fullPath = os.path.join(gamcfg.get(ConfigParser.DEFAULTSECT, itemName, raw=True), fullPath)
          if not os.path.isdir(fullPath):
            sys.stderr.write(u'{0}{1} {2} "{3}", invalid path\n'.format(ERROR_PREFIX, CONFIG_SET_CMD, itemName, value))
            sys.exit(3)
        elif GC_VAR_INFO[itemName][GC_VAR_TYPE_KEY] == GC_TYPE_FILE:
          pass
        gamcfg.set(sectionName, itemName, value)
# save
      elif my_arg == CONFIG_SAVE_CMD:
        _writeConfigFile(gamcfg, configFileName, action=u'Saved')
# backup <FileName>
      elif my_arg == CONFIG_BACKUP_CMD:
        if i == len(sys.argv):
          sys.stderr.write(u'{0}{1} "", should be <FileName>\n'.format(ERROR_PREFIX, my_arg))
          sys.exit(3)
        fileName = os.path.expanduser(sys.argv[i])
        i += 1
        if not os.path.isabs(fileName):
          fileName = os.path.join(gamCfgHome, fileName)
        _writeConfigFile(gamcfg, fileName, action=u'Backed up')
# restore <FileName>
      elif my_arg == CONFIG_RESTORE_CMD:
        if i == len(sys.argv):
          sys.stderr.write(u'{0}{1} "", should be <FileName>\n'.format(ERROR_PREFIX, my_arg))
          sys.exit(3)
        fileName = os.path.expanduser(sys.argv[i])
        i += 1
        if not os.path.isabs(fileName):
          fileName = os.path.join(gamCfgHome, fileName)
        _readConfigFile(gamcfg, fileName, action=u'Restored')
# verify
      elif my_arg == CONFIG_VERIFY_CMD:
        _verifyValues()
# print
      elif my_arg == CONFIG_PRINT_CMD:
        value = readFile(configFileName, mode=u'rU')
        for line in value:
          sys.stdout.write(line)
# config
      else:
        break
# Use default section
  else:
    sectionName = _getCfgSection(ConfigParser.DEFAULTSECT, GC_SECTION)
# Assign directories first
  for itemName in [GC_CONFIG_DIR, GC_CACHE_DIR, GC_DRIVE_DIR]:
    if GC_VAR_INFO[itemName][GC_VAR_TYPE_KEY] == GC_TYPE_DIRECTORY:
      GC_Values[itemName] = _getCfgDirectory(sectionName, itemName)
# Everything else
  for itemName in GC_VAR_INFO:
    varType = GC_VAR_INFO[itemName][GC_VAR_TYPE_KEY]
    if varType == GC_TYPE_BOOLEAN:
      GC_Values[itemName] = _getCfgBoolean(sectionName, itemName)
    elif varType == GC_TYPE_INTEGER:
      GC_Values[itemName] = _getCfgInteger(sectionName, itemName)
    elif varType == GC_TYPE_STRING:
      GC_Values[itemName] = _getCfgString(sectionName, itemName)
    elif varType == GC_TYPE_FILE:
      GC_Values[itemName] = _getCfgFile(sectionName, itemName)
  if status[u'errors']:
    sys.exit(13)
  if not GC_Values[GC_NO_UPDATE_CHECK]:
    previousUpdateCheck = GC_Values[GC_LAST_UPDATE_CHECK]
    GC_Values[GC_LAST_UPDATE_CHECK] = doGAMCheckForUpdates(previousUpdateCheck)
    if GC_Values[GC_LAST_UPDATE_CHECK] != previousUpdateCheck:
      luc_config = ConfigParser.SafeConfigParser(defaults=collections.OrderedDict(sorted(GC_DEFAULTS.items(), key=lambda t: t[0])))
      _readConfigFile(luc_config, configFileName)
      luc_config.set(ConfigParser.DEFAULTSECT, GC_LAST_UPDATE_CHECK, str(GC_Values[GC_LAST_UPDATE_CHECK]))
      _writeConfigFile(luc_config, configFileName, action=u'{0} Updated'.format(GC_LAST_UPDATE_CHECK))
# redirect (csv sectionname|<FileName>)|(stdout write|append sectionname|<FileName>)|(stderr write|append sectionname|<FileName>)
  while (i < len(sys.argv)) and (sys.argv[i] == REDIRECT_CMD):
    i += 1
    if i < len(sys.argv):
      my_arg = sys.argv[i].lower()
      i += 1
    else:
      my_arg = u''
    if my_arg not in REDIRECT_SUB_CMDS:
      sys.stderr.write(u'{0}{1} "{2}", should be {3}\n'.format(ERROR_PREFIX, REDIRECT_CMD, my_arg, u'|'.join(REDIRECT_SUB_CMDS)))
      sys.exit(3)
# csv sectionname|<FileName>
    if my_arg == REDIRECT_CSV_CMD:
      if i == len(sys.argv):
        sys.stderr.write(u'{0}{1} {2} "", should be <FileName>\n'.format(ERROR_PREFIX, REDIRECT_CMD, my_arg))
        sys.exit(3)
      _setCSVFile(sys.argv[i])
      i += 1
# stdout write|append sectionname|<FileName>
# stderr write|append sectionname|<FileName>
    else:
      ext = u'out' if my_arg == REDIRECT_STDOUT_CMD else u'err'
      if i < len(sys.argv):
        mode = sys.argv[i].lower()
        i += 1
      else:
        mode = u''
      if mode not in REDIRECT_MODE_MAP:
        sys.stderr.write(u'{0}{1} {2} "{3}", should be {4}\n'.format(ERROR_PREFIX, REDIRECT_CMD, my_arg, mode, u'|'.join(REDIRECT_MODE_MAP)))
        sys.exit(3)
      if i == len(sys.argv):
        sys.stderr.write(u'{0}{1} {2} {3} "", should be <FileName>\n'.format(ERROR_PREFIX, REDIRECT_CMD, my_arg, mode))
        sys.exit(3)
      _setSTDFile(sys.argv[i], ext, REDIRECT_MODE_MAP[mode])
      i += 1
  if GC_CSVFILE not in GC_Values:
    GC_Values[GC_CSVFILE] = sys.stdout
# Globals derived from config file values
  GC_Values[GC_CACERT_PEM] = os.path.join(GC_Values[GC_GAM_PATH], FN_CACERT_PEM)
  GC_Values[GC_EXTRA_ARGS] = {u'prettyPrint': GC_Values[GC_DEBUG_LEVEL] > 0}
  httplib2.debuglevel = GC_Values[GC_DEBUG_LEVEL]
  if os.path.isfile(os.path.join(GC_Values[GC_CONFIG_DIR], FN_EXTRA_ARGS_TXT)):
    ea_config = ConfigParser.ConfigParser()
    ea_config.optionxform = str
    ea_config.read(os.path.join(GC_Values[GC_CONFIG_DIR], FN_EXTRA_ARGS_TXT))
    GC_Values[GC_EXTRA_ARGS].update(dict(ea_config.items(u'extra-args')))
# If no select/options commands were executed or some were and there are more arguments on the command line,
# warn if the json files are missing and return True
  if (i == 1) or (i < len(sys.argv)):
    if i > 1:
# Move remaining args down to 1
      j = 1
      while i < len(sys.argv):
        sys.argv[j] = sys.argv[i]
        j += 1
        i += 1
      del sys.argv[j:]
    _chkCfgDirectories(sectionName)
    _chkCfgFiles(sectionName)
    if GC_Values[GC_NO_CACHE]:
      GC_Values[GC_CACHE_DIR] = None
    return True
# We're done, nothing else to do
  return False

def doGAMVersion():
  import struct
  print u'GAM %s - http://git.io/gam\n%s\nPython %s.%s.%s %s-bit %s\ngoogle-api-python-client %s\n%s %s\nPath: %s' % (__version__, __author__,
                   sys.version_info[0], sys.version_info[1], sys.version_info[2], struct.calcsize('P')*8, sys.version_info[3], googleapiclient.__version__,
                   platform.platform(), platform.machine(), GC_Values[GC_GAM_PATH])

def doGAMCheckForUpdates(lastUpdateCheck):
  import urllib2
  try:
    current_version = float(__version__)
  except ValueError:
    return
  now_time = calendar.timegm(time.gmtime())
  if lastUpdateCheck > now_time - 604800:
    return lastUpdateCheck
  try:
    c = urllib2.urlopen(u'https://gam-update.appspot.com/latest-version.txt?v=%s' % __version__)
    try:
      latest_version = float(c.read())
    except ValueError:
      return
    if latest_version <= current_version:
      return now_time
    a = urllib2.urlopen(u'https://gam-update.appspot.com/latest-version-announcement.txt?v=%s' % __version__)
    announcement = a.read()
    sys.stderr.write(announcement)
    try:
      print u'\n\nHit CTRL+C to visit the GAM website and download the latest release or wait 15 seconds continue with this boring old version. GAM won\'t bother you with this announcement for 1 week or you can turn off update checks with the command: "gam config select default set no_update_check true save"'
      time.sleep(15)
    except KeyboardInterrupt:
      import webbrowser
      webbrowser.open(u'https://github.com/jay0lee/GAM/releases')
      print u'GAM is now exiting so that you can overwrite this old version with the latest release'
      sys.exit(0)
    return now_time
  except (urllib2.HTTPError, urllib2.URLError):
    return lastUpdateCheck

def commonAppsObjInit(appsObj):
  #Identify GAM to Google's Servers
  appsObj.source = u'GAM %s - http://git.io/gam / %s / Python %s.%s.%s %s / %s %s /' % (__version__, __author__,
                   sys.version_info[0], sys.version_info[1], sys.version_info[2], sys.version_info[3],
                   platform.platform(), platform.machine())
  #Show debugging output if debug.gam exists
  if GC_Values[GC_DEBUG_LEVEL] > 0:
    appsObj.debug = True
  return appsObj

def checkErrorCode(e, service):
  try:
    if e[0]['reason'] in [u'Token invalid - Invalid token: Stateless token expired', u'Token invalid - Invalid token: Token not found']:
      keep_domain = service.domain
      tryOAuth(service)
      service.domain = keep_domain
      return False
  except KeyError:
    pass
  if e[0]['body'][:34] in [u'Required field must not be blank: ', u'These characters are not allowed: ']:
    return e[0]['body']
  if e.error_code == 600 and e[0][u'body'] == u'Quota exceeded for the current request' or e[0][u'reason'] == u'Bad Gateway':
    return False
  if e.error_code == 600 and e[0][u'reason'] == u'Token invalid - Invalid token: Token disabled, revoked, or expired.':
    return u'403 - Token disabled, revoked, or expired. Please delete and re-create oauth.txt'
  if e.error_code == 1000: # UnknownError
    return False
  elif e.error_code == 1001: # ServerBusy
    return False
  elif e.error_code == 1002:
    return u'1002 - Unauthorized and forbidden'
  elif e.error_code == 1100:
    return u'1100 - User deleted recently'
  elif e.error_code == 1200:
    return u'1200 - Domain user limit exceeded'
  elif e.error_code == 1201:
    return u'1201 - Domain alias limit exceeded'
  elif e.error_code == 1202:
    return u'1202 - Domain suspended'
  elif e.error_code == 1203:
    return u'1203 - Domain feature unavailable'
  elif e.error_code == 1300:
    if e.invalidInput != '':
      return u'1300 - Entity %s exists' % e.invalidInput
    else:
      return u'1300 - Entity exists'
  elif e.error_code == 1301:
    if e.invalidInput != '':
      return u'1301 - Entity %s Does Not Exist' % e.invalidInput
    else:
      return u'1301 - Entity Does Not Exist'
  elif e.error_code == 1302:
    return u'1302 - Entity Name Is Reserved'
  elif e.error_code == 1303:
    if e.invalidInput != '':
      return u'1303 - Entity %s name not valid' % e.invalidInput
    else:
      return u'1303 - Entity name not valid'
  elif e.error_code == 1306:
    if e.invalidInput != '':
      return u'1306 - %s has members. Cannot delete.' % e.invalidInput
    else:
      return u'1306 - Entity has members. Cannot delete.'
  elif e.error_code == 1400:
    return u'1400 - Invalid Given Name'
  elif e.error_code == 1401:
    return u'1401 - Invalid Family Name'
  elif e.error_code == 1402:
    return u'1402 - Invalid Password'
  elif e.error_code == 1403:
    return u'1403 - Invalid Username'
  elif e.error_code == 1404:
    return u'1404 - Invalid Hash Function Name'
  elif e.error_code == 1405:
    return u'1405 - Invalid Hash Digest Length'
  elif e.error_code == 1406:
    return u'1406 - Invalid Email Address'
  elif e.error_code == 1407:
    return u'1407 - Invalid Query Parameter Value'
  elif e.error_code == 1408:
    return u'1408 - Invalid SSO Signing Key'
  elif e.error_code == 1409:
    return u'1409 - Invalid Encryption Public Key'
  elif e.error_code == 1410:
    return u'1410 - Feature Unavailable For User'
  elif e.error_code == 1500:
    return u'1500 - Too Many Recipients On Email List'
  elif e.error_code == 1501:
    return u'1501 - Too Many Aliases For User'
  elif e.error_code == 1502:
    return u'1502 - Too Many Delegates For User'
  elif e.error_code == 1601:
    return u'1601 - Duplicate Destinations'
  elif e.error_code == 1602:
    return u'1602 - Too Many Destinations'
  elif e.error_code == 1603:
    return u'1603 - Invalid Route Address'
  elif e.error_code == 1700:
    return u'1700 - Group Cannot Contain Cycle'
  elif e.error_code == 1800:
    return u'1800 - Invalid Domain Edition'
  elif e.error_code == 1801:
    if e.invalidInput != '':
      return u'1801 - Invalid value %s' % e.invalidInput
    else:
      return u'1801 - Invalid Value'
  else:
    return u'%s: Unknown Error: %s' % (e.error_code, str(e))

def tryOAuth(gdataObject):
  storage = oauth2client.file.Storage(GC_Values[GC_OAUTH2_TXT])
  credentials = storage.get()
  if credentials is None or credentials.invalid:
    doRequestOAuth()
    credentials = storage.get()
  if credentials.access_token_expired:
    credentials.refresh(httplib2.Http(ca_certs=GC_Values[GC_CACERT_PEM],
                                      disable_ssl_certificate_validation=GC_Values[GC_NO_VERIFY_SSL]))
  gdataObject.additional_headers = {u'Authorization': u'Bearer %s' % credentials.access_token}
  if not GC_Values[GC_DOMAIN]:
    GC_Values[GC_DOMAIN] = credentials.id_token[u'hd'].lower()
  if not GC_Values[GC_CUSTOMER_ID]:
    GC_Values[GC_CUSTOMER_ID] = MY_CUSTOMER
  gdataObject.domain = GC_Values[GC_DOMAIN]
  return True

def callGData(service, function, soft_errors=False, throw_errors=[], **kwargs):
  import gdata.apps.service
  method = getattr(service, function)
  retries = 10
  for n in range(1, retries+1):
    try:
      return method(**kwargs)
    except gdata.apps.service.AppsForYourDomainException, e:
      terminating_error = checkErrorCode(e, service)
      if e.error_code in throw_errors:
        raise
      if not terminating_error and n != retries:
        wait_on_fail = (2 ** n) if (2 ** n) < 60 else 60
        randomness = float(random.randint(1, 1000)) / 1000
        wait_on_fail = wait_on_fail + randomness
        if n > 3:
          sys.stderr.write(u'Temp error. Backing off %s seconds...' % (int(wait_on_fail)))
        time.sleep(wait_on_fail)
        if n > 3:
          sys.stderr.write(u'attempt %s/%s\n' % (n+1, retries))
        continue
      sys.stderr.write(u'Error: %s' % terminating_error)
      if soft_errors:
        if n != 1:
          sys.stderr.write(u' - Giving up.\n')
        return
      else:
        sys.exit(int(e.error_code))

def callGAPI(service, function, silent_errors=False, soft_errors=False, throw_reasons=[], retry_reasons=[], **kwargs):
  method = getattr(service, function)
  retries = 10
  parameters = dict(kwargs.items() + GC_Values[GC_EXTRA_ARGS].items())
  for n in range(1, retries+1):
    try:
      return method(**parameters).execute()
    except googleapiclient.errors.HttpError, e:
      try:
        error = json.loads(e.content)
      except ValueError:
        if n < 3:
          service._http.request.credentials.refresh(httplib2.Http(ca_certs=GC_Values[GC_CACERT_PEM],
                                                                  disable_ssl_certificate_validation=GC_Values[GC_NO_VERIFY_SSL]))
          continue
        if (e.resp[u'status'] == u'503') and (e.content == u'Quota exceeded for the current request'):
          time.sleep(1)
          continue
        if not silent_errors:
          print u'ERROR: %s' % e.content
        if soft_errors:
          return
        else:
          sys.exit(5)
      http_status = error[u'error'][u'code']
      message = error[u'error'][u'errors'][0][u'message']
      try:
        reason = error[u'error'][u'errors'][0][u'reason']
      except KeyError:
        reason = http_status
      if reason in throw_reasons:
        raise e
      if n != retries and (reason in [u'rateLimitExceeded', u'userRateLimitExceeded', u'backendError', u'internalError'] or reason in retry_reasons):
        wait_on_fail = (2 ** n) if (2 ** n) < 60 else 60
        randomness = float(random.randint(1, 1000)) / 1000
        wait_on_fail = wait_on_fail + randomness
        if n > 3:
          sys.stderr.write(u'Temp error %s. Backing off %s seconds...' % (reason, int(wait_on_fail)))
        time.sleep(wait_on_fail)
        if n > 3:
          sys.stderr.write(u'attempt %s/%s\n' % (n+1, retries))
        continue
      sys.stderr.write(u'Error %s: %s - %s\n\n' % (http_status, message, reason))
      if soft_errors:
        if n != 1:
          sys.stderr.write(u' - Giving up.\n')
        return
      else:
        sys.exit(int(http_status))
    except oauth2client.client.AccessTokenRefreshError, e:
      sys.stderr.write(u'Error: Authentication Token Error - %s' % e)
      sys.exit(403)
    except httplib2.CertificateValidationUnsupported:
      print u'\nError: You don\'t have the Python ssl module installed so we can\'t verify SSL Certificates.\n\nYou can fix this by installing the Python SSL module or you can live on dangerously and turn SSL validation off by creating a file called noverifyssl.txt in the same location as gam.exe / gam.py'
      sys.exit(8)
    except TypeError, e:
      print u'Error: %s' % e
      sys.exit(4)

def printGettingMessage(message):
  if GC_Values[GC_SHOW_GETTINGS]:
    sys.stderr.write(message)

FIRST_ITEM_MARKER = u'%%first_item%%'
LAST_ITEM_MARKER = u'%%last_item%%'
NUM_ITEMS_MARKER = u'%%num_items%%'
TOTAL_ITEMS_MARKER = u'%%total_items%%'

def getPageMessage(entityItem, forWhom=None, showTotal=True, showFirstLastItems=False, noNL=False):
  if GC_Values[GC_SHOW_GETTINGS]:
    pageMessage = u'Got {0} {1}'.format(TOTAL_ITEMS_MARKER if showTotal else NUM_ITEMS_MARKER, entityItem)
    if forWhom:
      pageMessage += u' for {0}'.format(forWhom)
    if showFirstLastItems:
      pageMessage += u': {0} - {1}'.format(FIRST_ITEM_MARKER, LAST_ITEM_MARKER)
    else:
      pageMessage += u'...'
    if not noNL:
      pageMessage += u'\n'
    return pageMessage
  else:
    return None

def callGAPIpages(service, function, items=u'items', nextPageToken=u'nextPageToken', page_message=None, message_attribute=None, **kwargs):
  pageToken = None
  all_pages = list()
  total_items = 0
  while True:
    this_page = callGAPI(service=service, function=function, pageToken=pageToken, **kwargs)
    if this_page:
      pageToken = this_page.get(nextPageToken)
      if items in this_page:
        page_items = len(this_page[items])
        total_items += page_items
        all_pages.extend(this_page[items])
      else:
        this_page = {items: []}
        page_items = 0
    else:
      pageToken = None
      this_page = {items: []}
      page_items = 0
    if page_message:
      show_message = page_message.replace(NUM_ITEMS_MARKER, str(page_items))
      show_message = show_message.replace(TOTAL_ITEMS_MARKER, str(total_items))
      if message_attribute:
        try:
          show_message = show_message.replace(FIRST_ITEM_MARKER, str(this_page[items][0][message_attribute]))
          show_message = show_message.replace(LAST_ITEM_MARKER, str(this_page[items][-1][message_attribute]))
        except (IndexError, KeyError):
          show_message = show_message.replace(FIRST_ITEM_MARKER, u'')
          show_message = show_message.replace(LAST_ITEM_MARKER, u'')
      sys.stderr.write('\r')
      sys.stderr.flush()
      sys.stderr.write(show_message)
    if not pageToken:
      if page_message and (page_message[-1] != u'\n'):
        sys.stderr.write(u'\r\n')
        sys.stderr.flush()
      return all_pages

API_VER_MAPPING = {
  u'admin-settings': u'v1',
  u'appsactivity': u'v1',
  u'calendar': u'v3',
  u'classroom': u'v1',
  u'cloudprint': u'v2',
  u'directory': u'directory_v1',
  u'drive': u'v2',
  u'gmail': u'v1',
  u'groupssettings': u'v1',
  u'licensing': u'v1',
  u'oauth2': u'v2',
  u'plus': u'v1',
  u'plusDomains': u'v1',
  u'reports': u'reports_v1',
  u'siteVerification': u'v1',
  }

def getAPIVer(api):
  return API_VER_MAPPING.get(api, u'v1')

API_SCOPE_MAPPING = {
  u'appsactivity': [u'https://www.googleapis.com/auth/activity',
                    u'https://www.googleapis.com/auth/drive'],
  u'calendar': [u'https://www.googleapis.com/auth/calendar',],
  u'drive': [u'https://www.googleapis.com/auth/drive',],
  u'gmail': [u'https://mail.google.com/',],
  u'plus': [u'https://www.googleapis.com/auth/plus.me',],
  u'plusDomains': [u'https://www.googleapis.com/auth/plus.me',
                   u'https://www.googleapis.com/auth/plus.circles.read',
                   u'https://www.googleapis.com/auth/plus.circles.write'],
}

def getAPIScope(api):
  return API_SCOPE_MAPPING.get(api, [])

def buildGAPIObject(api):
  storage = oauth2client.file.Storage(GC_Values[GC_OAUTH2_TXT])
  credentials = storage.get()
  if credentials is None or credentials.invalid:
    doRequestOAuth()
    credentials = storage.get()
  credentials.user_agent = u'GAM %s - http://git.io/gam / %s / Python %s.%s.%s %s / %s %s /' % (__version__, __author__,
                   sys.version_info[0], sys.version_info[1], sys.version_info[2], sys.version_info[3],
                   platform.platform(), platform.machine())
  http = httplib2.Http(ca_certs=GC_Values[GC_CACERT_PEM],
                       disable_ssl_certificate_validation=GC_Values[GC_NO_VERIFY_SSL],
                       cache=GC_Values[GC_CACHE_DIR])
  http = credentials.authorize(http)
  version = getAPIVer(api)
  if api in [u'directory', u'reports']:
    api = u'admin'
  try:
    service = googleapiclient.discovery.build(api, version, http=http)
  except googleapiclient.errors.UnknownApiNameOrVersion:
    disc_file = os.path.join(GC_Values[GC_GAM_PATH], u'%s-%s.json' % (api, version))
    if os.path.isfile(disc_file):
      f = open(disc_file, 'rb')
      discovery = f.read()
      f.close()
      service = googleapiclient.discovery.build_from_document(discovery, base=u'https://www.googleapis.com', http=http)
    else:
      print 'No online discovery doc and %s does not exist locally' % disc_file
      raise
  except httplib2.CertificateValidationUnsupported:
    print u'Error: You don\'t have the Python ssl module installed so we can\'t verify SSL Certificates. You can fix this by installing the Python SSL module or you can live on the edge and turn SSL validation off by creating a file called noverifyssl.txt in the same location as gam.exe / gam.py'
    sys.exit(8)
  except httplib2.ServerNotFoundError as e:
    print u'ERROR: %s' % (e)
    sys.exit(8)
  if GC_Values[GC_DOMAIN] and not GC_Values[GC_CUSTOMER_ID]:
    resp, result = service._http.request(u'https://www.googleapis.com/admin/directory/v1/users?domain=%s&maxResults=1&fields=users(customerId)' % GC_Values[GC_DOMAIN])
    try:
      resultObj = json.loads(result)
    except ValueError:
      print u'ERROR: unexpected response: %s' % result
      sys.exit(8)
    if resp[u'status'] == u'403':
      try:
        message = resultObj[u'error'][u'errors'][0][u'message']
      except KeyError:
        message = resultObj[u'error'][u'message']
      print u'ERROR: %s' % (message)
      sys.exit(8)
    try:
      GC_Values[GC_CUSTOMER_ID] = resultObj[u'users'][0][u'customerId']
    except KeyError:
      GC_Values[GC_DOMAIN] = None
  if (not GC_Values[GC_DOMAIN]) or (not GC_Values[GC_CUSTOMER_ID]):
    try:
      GC_Values[GC_DOMAIN] = credentials.id_token[u'hd']
    except (TypeError, KeyError):
      GC_Values[GC_DOMAIN] = u'Unknown'
    GC_Values[GC_CUSTOMER_ID] = MY_CUSTOMER
  return service

def buildGAPIServiceObject(api, act_as=None, soft_errors=False):
  try:
    json_string = open(GC_Values[GC_OAUTH2SERVICE_JSON]).read()
  except IOError, e:
    print u'Error: %s' % e
    print u''
    print u'Please follow the instructions at:\n\nhttps://github.com/jay0lee/GAM/wiki/CreatingClientSecretsFile#creating-your-own-oauth2servicejson\n\nto setup a Service Account'
    sys.exit(6)
  json_data = json.loads(json_string)
  try:
    SERVICE_ACCOUNT_EMAIL = json_data[u'web'][u'client_email']
    SERVICE_ACCOUNT_CLIENT_ID = json_data[u'web'][u'client_id']
    f = open(GC_Values[GC_OAUTH2SERVICE_JSON].replace(u'.json', u'.p12'), 'rb')
    key = f.read()
    f.close()
  except KeyError:
    # new format with config and data in the .json file...
    SERVICE_ACCOUNT_EMAIL = json_data[u'client_email']
    SERVICE_ACCOUNT_CLIENT_ID = json_data[u'client_id']
    key = json_data[u'private_key']
  scope = getAPIScope(api)
  if act_as == None:
    credentials = oauth2client.client.SignedJwtAssertionCredentials(SERVICE_ACCOUNT_EMAIL, key, scope=scope)
  else:
    credentials = oauth2client.client.SignedJwtAssertionCredentials(SERVICE_ACCOUNT_EMAIL, key, scope=scope, sub=act_as)
  credentials.user_agent = u'GAM %s - http://git.io/gam / %s / Python %s.%s.%s %s / %s %s /' % (__version__, __author__,
                   sys.version_info[0], sys.version_info[1], sys.version_info[2], sys.version_info[3],
                   platform.platform(), platform.machine())
  http = httplib2.Http(ca_certs=GC_Values[GC_CACERT_PEM],
                       disable_ssl_certificate_validation=GC_Values[GC_NO_VERIFY_SSL],
                       cache=GC_Values[GC_CACHE_DIR])
  http = credentials.authorize(http)
  version = getAPIVer(api)
  try:
    return googleapiclient.discovery.build(api, version, http=http)
  except oauth2client.client.AccessTokenRefreshError, e:
    if e.message in [u'access_denied', u'unauthorized_client: Unauthorized client or scope in request.']:
      print u'Error: Access Denied. Please make sure the Client Name:\n\n%s\n\nis authorized for the API Scope(s):\n\n%s\n\nThis can be configured in your Control Panel under:\n\nSecurity -->\nAdvanced Settings -->\nManage third party OAuth Client access' % (SERVICE_ACCOUNT_CLIENT_ID, ','.join(scope))
      sys.exit(5)
    else:
      print u'Error: %s' % e
      if soft_errors:
        return False
      sys.exit(4)

def buildDiscoveryObject(api):
  import uritemplate
  version = getAPIVer(api)
  if api in [u'directory', u'reports']:
    api = u'admin'
  params = {'api': api, 'apiVersion': version}
  http = httplib2.Http(ca_certs=GC_Values[GC_CACERT_PEM],
                       disable_ssl_certificate_validation=GC_Values[GC_NO_VERIFY_SSL],
                       cache=GC_Values[GC_CACHE_DIR])
  requested_url = uritemplate.expand(googleapiclient.discovery.DISCOVERY_URI, params)
  resp, content = http.request(requested_url)
  if resp.status == 404:
    raise googleapiclient.errors.UnknownApiNameOrVersion("name: %s  version: %s" % (api, version))
  if resp.status >= 400:
    raise googleapiclient.errors.HttpError(resp, content, uri=requested_url)
  try:
    return json.loads(content)
  except ValueError:
    sys.stderr.write(u'Failed to parse as JSON: ' + content+u'\n')
    raise googleapiclient.errors.InvalidJsonError()

def getEmailSettingsObject():
  import gdata.apps.emailsettings.service
  emailsettings = gdata.apps.emailsettings.service.EmailSettingsService()
  if not tryOAuth(emailsettings):
    doRequestOAuth()
    tryOAuth(emailsettings)
  emailsettings = commonAppsObjInit(emailsettings)
  return emailsettings

def getAdminSettingsObject():
  import gdata.apps.adminsettings.service
  adminsettings = gdata.apps.adminsettings.service.AdminSettingsService()
  if not tryOAuth(adminsettings):
    doRequestOAuth()
    tryOAuth(adminsettings)
  adminsettings = commonAppsObjInit(adminsettings)
  return adminsettings

def getAuditObject():
  import gdata.apps.audit.service
  auditObj = gdata.apps.audit.service.AuditService()
  if not tryOAuth(auditObj):
    doRequestOAuth()
    tryOAuth(auditObj)
  auditObj = commonAppsObjInit(auditObj)
  return auditObj

def getResCalObject():
  import gdata.apps.res_cal.service
  resCalObj = gdata.apps.res_cal.service.ResCalService()
  if not tryOAuth(resCalObj):
    doRequestOAuth()
    tryOAuth(resCalObj)
  resCalObj = commonAppsObjInit(resCalObj)
  return resCalObj

def geturl(url, dst):
  import urllib2
  u = urllib2.urlopen(url)
  f = open(dst, 'wb')
  meta = u.info()
  try:
    file_size = int(meta.getheaders(u'Content-Length')[0])
  except IndexError:
    file_size = -1
  file_size_dl = 0
  block_sz = 8192
  while True:
    filebuff = u.read(block_sz)
    if not filebuff:
      break
    file_size_dl += len(filebuff)
    f.write(filebuff)
    if file_size != -1:
      status = r"%10d  [%3.2f%%]" % (file_size_dl, file_size_dl * 100. / file_size)
    else:
      status = r"%10d [unknown size]" % (file_size_dl)
    status = status + chr(8)*(len(status)+1)
    print status,
  f.close()

def showReport():
  report = sys.argv[2].lower()
  rep = buildGAPIObject(u'reports')
  if GC_Values[GC_CUSTOMER_ID] == MY_CUSTOMER:
    GC_Values[GC_CUSTOMER_ID] = None
  date = filters = parameters = actorIpAddress = startTime = endTime = eventName = None
  to_drive = False
  userKey = 'all'
  i = 3
  while i < len(sys.argv):
    if sys.argv[i].lower() == u'date':
      date = sys.argv[i+1]
      i += 2
    elif sys.argv[i].lower() == u'start':
      startTime = sys.argv[i+1]
      i += 2
    elif sys.argv[i].lower() == u'end':
      endTime = sys.argv[i+1]
      i += 2
    elif sys.argv[i].lower() == u'event':
      eventName = sys.argv[i+1]
      i += 2
    elif sys.argv[i].lower() == u'user':
      userKey = sys.argv[i+1]
      i += 2
    elif sys.argv[i].lower() in [u'filter', u'filters']:
      filters = sys.argv[i+1]
      i += 2
    elif sys.argv[i].lower() in [u'fields', u'parameters']:
      parameters = sys.argv[i+1]
      i += 2
    elif sys.argv[i].lower() == u'ip':
      actorIpAddress = sys.argv[i+1]
      i += 2
    elif sys.argv[i].lower() == u'todrive':
      to_drive = True
      i += 1
    else:
      print u'Error: did not expect %s as an argument to "gam report"' % sys.argv[i]
      sys.exit(3)
  try_date = date
  if try_date == None:
    try_date = datetime.date.today()
  if report in [u'users', u'user']:
    while True:
      try:
        page_message = getPageMessage(u'users', showTotal=False)
        usage = callGAPIpages(service=rep.userUsageReport(), function=u'get', items=u'usageReports', page_message=page_message,
                              throw_reasons=[u'invalid'], date=str(try_date), userKey=userKey, customerId=GC_Values[GC_CUSTOMER_ID], filters=filters, parameters=parameters)
        break
      except googleapiclient.errors.HttpError, e:
        error = json.loads(e.content)
      try:
        message = error[u'error'][u'errors'][0][u'message']
      except KeyError:
        raise
      match_date = re.match(u'Data for dates later than (.*) is not yet available. Please check back later', message)
      if not match_date:
        print u'Error: %s' % message
        sys.exit(4)
      else:
        try_date = match_date.group(1)
    user_attributes = []
    titles = [u'email', u'date']
    for user_report in usage:
      row = {u'email': user_report[u'entity'][u'userEmail'], u'date': str(try_date)}
      try:
        for report_item in user_report[u'parameters']:
          items = report_item.values()
          name = items[1]
          value = items[0]
          if not name in titles:
            titles.append(name)
          row[name] = value
      except KeyError:
        pass
      user_attributes.append(row)
    header = {}
    for title in titles:
      header[title] = title
    user_attributes.insert(0, header)
    output_csv(user_attributes, titles, u'User Reports - %s' % try_date, to_drive)
  elif report in [u'customer', u'customers', u'domain']:
    while True:
      try:
        usage = callGAPIpages(service=rep.customerUsageReports(), function=u'get', items=u'usageReports', throw_reasons=[u'invalid'], customerId=GC_Values[GC_CUSTOMER_ID], date=str(try_date), parameters=parameters)
        break
      except googleapiclient.errors.HttpError, e:
        error = json.loads(e.content)
      try:
        message = error[u'error'][u'errors'][0][u'message']
      except KeyError:
        raise
      match_date = re.match(u'Data for dates later than (.*) is not yet available. Please check back later', message)
      if not match_date:
        print u'Error: %s' % message
        sys.exit(4)
      else:
        try_date = match_date.group(1)
    cust_attributes = [{u'name': u'name', u'value': u'value', u'client_id': u'client_id'}]
    titles = [u'name', u'value', u'client_id']
    auth_apps = list()
    for item in usage[0][u'parameters']:
      name = item[u'name']
      try:
        value = item[u'intValue']
      except KeyError:
        if name == u'accounts:authorized_apps':
          for subitem in item[u'msgValue']:
            app = dict()
            for an_item in subitem:
              if an_item == u'client_name':
                app['name'] = u'App: %s' % subitem[an_item]
              elif an_item == u'num_users':
                app['value'] = u'%s users' % subitem[an_item]
              elif an_item == u'client_id':
                app[u'client_id'] = subitem[an_item]
            auth_apps.append(app)
        continue
      cust_attributes.append({u'name': name, u'value': value})
    for app in auth_apps: # put apps at bottom
      cust_attributes.append(app)
    output_csv(csv_list=cust_attributes, titles=titles, list_type=u'Customer Report - %s' % try_date, todrive=to_drive)
  elif report in [u'doc', u'docs', u'calendar', u'calendars', u'login', u'logins', u'admin', u'drive', u'token', u'tokens']:
    if report in [u'doc', u'docs']:
      report = u'drive'
    elif report in [u'calendars']:
      report = u'calendar'
    elif report == u'logins':
      report = u'login'
    elif report == u'tokens':
      report = u'token'
    page_message = getPageMessage(u'items', showTotal=False)
    activities = callGAPIpages(service=rep.activities(), function=u'list', page_message=page_message,
                               applicationName=report, userKey=userKey, customerId=GC_Values[GC_CUSTOMER_ID], actorIpAddress=actorIpAddress,
                               startTime=startTime, endTime=endTime, eventName=eventName, filters=filters)
    if len(activities) > 0:
      attrs = []
      titles = []
      for activity in activities:
        events = activity[u'events']
        del activity[u'events']
        activity_row = flatten_json(activity)
        for event in events:
          row = flatten_json(event)
          row.update(activity_row)
          for item in row.keys():
            if item not in titles:
              titles.append(item)
          attrs.append(row)
      header = {}
      titles.remove(u'name')
      titles = sorted(titles)
      titles.insert(0, u'name')
      for title in titles:
        header[title] = title
      attrs.insert(0, header)
      cap_report = u'%s%s' % (report[0].upper(), report[1:])
      output_csv(attrs, titles, u'%s Activity Report' % cap_report, to_drive)

def doDelegates(users):
  import gdata.apps.service
  emailsettings = getEmailSettingsObject()
  if sys.argv[4].lower() == u'to':
    delegate = sys.argv[5].lower()
    if not delegate.find(u'@') > 0:
      delegate_domain = GC_Values[GC_DOMAIN].lower()
      delegate_email = u'%s@%s' % (delegate, delegate_domain)
    else:
      delegate_domain = delegate[delegate.find(u'@')+1:].lower()
      delegate_email = delegate
  else:
    showUsage()
    exit(6)
  count = len(users)
  i = 1
  for delegator in users:
    if delegator.find(u'@') > 0:
      delegator_domain = delegator[delegator.find('@')+1:].lower()
      delegator_email = delegator
      delegator = delegator[:delegator.find('@')]
    else:
      delegator_domain = GC_Values[GC_DOMAIN].lower()
      delegator_email = u'%s@%s' % (delegator, delegator_domain)
    emailsettings.domain = delegator_domain
    print u"Giving %s delegate access to %s (%s of %s)" % (delegate_email, delegator_email, i, count)
    i += 1
    delete_alias = False
    if delegate_domain == delegator_domain:
      use_delegate_address = delegate_email
    else:
      # Need to use an alias in delegator domain, first check to see if delegate already has one...
      cd = buildGAPIObject(u'directory')
      aliases = callGAPI(service=cd.users().aliases(), function=u'list', userKey=delegate_email)
      found_alias_in_delegator_domain = False
      try:
        for alias in aliases[u'aliases']:
          alias_domain = alias[u'alias'][alias[u'alias'].find(u'@')+1:].lower()
          if alias_domain == delegator_domain:
            use_delegate_address = alias[u'alias']
            print u'  Using existing alias %s for delegation' % use_delegate_address
            found_alias_in_delegator_domain = True
            break
      except KeyError:
        pass
      if not found_alias_in_delegator_domain:
        delete_alias = True
        use_delegate_address = u'%s@%s' % (''.join(random.sample(u'abcdefghijklmnopqrstuvwxyz0123456789', 25)), delegator_domain)
        print u'  Giving %s temporary alias %s for delegation' % (delegate_email, use_delegate_address)
        callGAPI(service=cd.users().aliases(), function=u'insert', userKey=delegate_email, body={u'alias': use_delegate_address})
        time.sleep(5)
    retries = 10
    for n in range(1, retries+1):
      try:
        callGData(service=emailsettings, function=u'CreateDelegate', throw_errors=[600, 1000, 1001], delegate=use_delegate_address, delegator=delegator)
        break
      except gdata.apps.service.AppsForYourDomainException, e:
        # 1st check to see if delegation already exists (causes 1000 error on create when using alias)
        get_delegates = callGData(service=emailsettings, function=u'GetDelegates', delegator=delegator)
        for get_delegate in get_delegates:
          if get_delegate[u'address'].lower() == delegate_email: # Delegation is already in place
            print u'That delegation is already in place...'
            if delete_alias:
              print u'  Deleting temporary alias...'
              doDeleteAlias(alias_email=use_delegate_address)
            sys.exit(0) # Emulate functionality of duplicate delegation between users in same domain, returning clean
        # Now check if either user account is suspended or requires password change
        cd = buildGAPIObject(u'directory')
        delegate_user_details = callGAPI(service=cd.users(), function=u'get', userKey=delegate_email)
        delegator_user_details = callGAPI(service=cd.users(), function=u'get', userKey=delegator_email)
        if delegate_user_details[u'suspended'] == True:
          sys.stderr.write(u'ERROR: User %s is suspended. You must unsuspend for delegation.\n' % delegate_email)
          if delete_alias:
            doDeleteAlias(alias_email=use_delegate_address)
          sys.exit(5)
        if delegator_user_details[u'suspended'] == True:
          sys.stderr.write(u'ERROR: User %s is suspended. You must unsuspend for delegation.\n' % delegator_email)
          if delete_alias:
            doDeleteAlias(alias_email=use_delegate_address)
          sys.exit(5)
        if delegate_user_details[u'changePasswordAtNextLogin'] == True:
          sys.stderr.write(u'ERROR: User %s is required to change password at next login. You must change password or clear changepassword flag for delegation.\n' % delegate_email)
          if delete_alias:
            doDeleteAlias(alias_email=use_delegate_address)
          sys.exit(5)
        if delegator_user_details[u'changePasswordAtNextLogin'] == True:
          sys.stderr.write(u'ERROR: User %s is required to change password at next login. You must change password or clear changepassword flag for delegation.\n' % delegator_email)
          if delete_alias:
            doDeleteAlias(alias_email=use_delegate_address)
          sys.exit(5)

        # Guess it was just a normal backoff error then?
        if n == retries:
          sys.stderr.write(u' - giving up.')
          sys.exit(e.error_code)
        wait_on_fail = (2 ** n) if (2 ** n) < 60 else 60
        randomness = float(random.randint(1, 1000)) / 1000
        wait_on_fail = wait_on_fail + randomness
        if n > 3:
          sys.stderr.write(u'Temp error. Backing off %s seconds...' % (int(wait_on_fail)))
        time.sleep(wait_on_fail)
        if n > 3:
          sys.stderr.write(u'attempt %s/%s\n' % (n+1, retries))
    time.sleep(10) # on success, sleep 10 seconds before exiting or moving on to next user to prevent ghost delegates
    if delete_alias:
      doDeleteAlias(alias_email=use_delegate_address)

def gen_sha512_hash(password):
  from passlib.handlers.sha2_crypt import sha512_crypt
  return sha512_crypt.encrypt(password, rounds=5000)

def getDelegates(users):
  emailsettings = getEmailSettingsObject()
  csv_format = False
  try:
    if sys.argv[5].lower() == u'csv':
      csv_format = True
  except IndexError:
    pass
  for user in users:
    if user.find(u'@') > 0:
      emailsettings.domain = user[user.find('@')+1:]
      user = user[:user.find('@')]
    else:
      emailsettings.domain = GC_Values[GC_DOMAIN]
    printGettingMessage(u"Getting delegates for %s...\n" % (user + '@' + emailsettings.domain))
    delegates = callGData(service=emailsettings, function=u'GetDelegates', soft_errors=True, delegator=user)
    try:
      for delegate in delegates:
        if csv_format:
          print u'%s,%s,%s' % (user + u'@' + emailsettings.domain, delegate[u'address'], delegate[u'status'])
        else:
          print u"Delegator: %s\n Delegate: %s\n Status: %s\n Delegate Email: %s\n Delegate ID: %s\n" % (user, delegate[u'delegate'],
                                                                                                         delegate[u'status'], delegate[u'address'],
                                                                                                         delegate[u'delegationId'])
    except TypeError:
      pass

def deleteDelegate(users):
  emailsettings = getEmailSettingsObject()
  delegate = sys.argv[5]
  if not delegate.find(u'@') > 0:
    if users[0].find(u'@') > 0:
      delegatedomain = users[0][users[0].find(u'@')+1:]
    else:
      delegatedomain = GC_Values[GC_DOMAIN]
    delegate = delegate+u'@'+delegatedomain
  count = len(users)
  i = 1
  for user in users:
    if user.find(u'@') > 0:
      emailsettings.domain = user[user.find(u'@')+1:]
      user = user[:user.find(u'@')]
    else:
      emailsettings.domain = GC_Values[GC_DOMAIN] #make sure it's back at default domain
    print u"Deleting %s delegate access to %s (%s of %s)" % (delegate, user+u'@'+emailsettings.domain, i, count)
    i += 1
    callGData(service=emailsettings, function=u'DeleteDelegate', delegate=delegate, delegator=user)

def doAddCourseParticipant():
  croom = buildGAPIObject(u'classroom')
  courseId = sys.argv[2]
  body_attribute = u'userId'
  if len(courseId) < 3 or (not courseId.isdigit() and courseId[:2] != u'd:'):
    courseId = u'd:%s' % courseId
  participant_type = sys.argv[4].lower()
  new_id = sys.argv[5]
  if participant_type in [u'teacher', u'teachers']:
    service = croom.courses().teachers()
  elif participant_type in [u'students', u'student']:
    service = croom.courses().students()
  elif participant_type in [u'alias']:
    service = croom.courses().aliases()
    body_attribute = u'alias'
    if new_id[1] != u':':
      new_id = u'd:%s' % new_id
  else:
    print 'ERROR: expected course participant type of teacher or student, got %s' % participant_type
    sys.exit(4)
  body = {body_attribute: new_id}
  callGAPI(service=service, function=u'create', courseId=courseId, body=body)
  if courseId[:2] == u'd:':
    courseId = courseId[2:]
  if new_id[:2] == u'd:':
    new_id = new_id[2:]
  print u'Added %s as a %s of course %s' % (new_id, participant_type, courseId)

def doSyncCourseParticipants():
  courseId = sys.argv[2]
  if not courseId.isdigit() and courseId[:2] != u'd:':
    courseId = u'd:%s' % courseId
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
    gam_commands.append([u'course', courseId, u'add', participant_type, add_email])
  for remove_email in to_remove:
    gam_commands.append([u'course', courseId, u'remove', participant_type, remove_email])
  run_batch(gam_commands, len(gam_commands))

def doDelCourseParticipant():
  croom = buildGAPIObject(u'classroom')
  courseId = sys.argv[2]
  if not courseId.isdigit() and courseId[:2] != u'd:':
    courseId = u'd:%s' % courseId
  participant_type = sys.argv[4].lower()
  remove_id = sys.argv[5]
  kwargs = {}
  if participant_type in [u'teacher', u'teachers']:
    service = croom.courses().teachers()
    kwargs[u'userId'] = remove_id
  elif participant_type in [u'student', u'students']:
    service = croom.courses().students()
    kwargs[u'userId'] = remove_id
  elif participant_type in [u'alias']:
    service = croom.courses().aliases()
    if remove_id[1] != u':':
      remove_id = u'd:%s' % remove_id
    kwargs[u'alias'] = remove_id
  else:
    print 'ERROR: expected course participant type of teacher or students, got %s' % participant_type
    sys.exit(4)
  callGAPI(service=service, function=u'delete', courseId=courseId, **kwargs)
  if courseId[:2] == u'd:':
    courseId = courseId[2:]
  if remove_id[:2] == u'd:':
    remove_id = remove_id[2:]
  print u'Removed %s as a %s of course %s' % (remove_id, participant_type, courseId)

def doDelCourse():
  croom = buildGAPIObject(u'classroom')
  courseId = sys.argv[3]
  if not courseId.isdigit():
    courseId = u'd:%s' % courseId
  callGAPI(service=croom.courses(), function=u'delete', id=courseId)
  print u'Deleted Course %s' % courseId

def doUpdateCourse():
  croom = buildGAPIObject(u'classroom')
  courseId = sys.argv[3]
  if not courseId.isdigit():
    courseId = u'd:%s' % courseId
  body = {}
  i = 4
  while i < len(sys.argv):
    if sys.argv[i].lower() == u'name':
      body[u'name'] = sys.argv[i+1]
      i += 2
    elif sys.argv[i].lower() == u'section':
      body[u'section'] = sys.argv[i+1]
      i += 2
    elif sys.argv[i].lower() == u'heading':
      body[u'descriptionHeading'] = sys.argv[i+1]
      i += 2
    elif sys.argv[i].lower() == u'description':
      body[u'description'] = sys.argv[i+1]
      i += 2
    elif sys.argv[i].lower() == u'room':
      body[u'room'] = sys.argv[i+1]
      i += 2
    elif sys.argv[i].lower() in [u'state', u'status']:
      body[u'courseState'] = sys.argv[i+1].upper()
      if body[u'courseState'] not in [u'ACTIVE', u'ARCHIVED', u'PROVISIONED', u'DECLINED']:
        print 'ERROR: course state can be active or archived. Got %s' % body[u'courseState']
        sys.exit(3)
      i += 2
    else:
      print u'ERROR: %s is not a valid argument to "gam update course"' % sys.argv[i]
      sys.exit(3)
  updateMask = u','.join(body.keys())
  body[u'id'] = courseId
  result = callGAPI(service=croom.courses(), function=u'patch', id=courseId, body=body, updateMask=updateMask)
  print u'Updated Course %s' % result[u'id']

def doCreateCourse():
  croom = buildGAPIObject(u'classroom')
  body = dict()
  i = 3
  while i < len(sys.argv):
    if sys.argv[i].lower() == u'name':
      body[u'name'] = sys.argv[i+1]
      i += 2
    elif sys.argv[i].lower() in [u'alias', u'id']:
      body[u'id'] = u'd:%s' % sys.argv[i+1]
      i += 2
    elif sys.argv[i].lower() == u'section':
      body[u'section'] = sys.argv[i+1]
      i += 2
    elif sys.argv[i].lower() == u'heading':
      body[u'descriptionHeading'] = sys.argv[i+1]
      i += 2
    elif sys.argv[i].lower() == u'description':
      body[u'description'] = sys.argv[i+1]
      i += 2
    elif sys.argv[i].lower() == u'room':
      body[u'room'] = sys.argv[i+1]
      i += 2
    elif sys.argv[i].lower() == u'teacher':
      body[u'ownerId'] = sys.argv[i+1]
      i += 2
    elif sys.argv[i].lower() in [u'state', u'status']:
      body[u'courseState'] = sys.argv[i+1].upper()
      if body[u'courseState'] not in [u'ACTIVE', u'ARCHIVED', u'PROVISIONED', u'DECLINED']:
        print 'ERROR: course state can be active or archived. Got %s' % body[u'courseState']
        sys.exit(3)
      i += 2
    else:
      print u'ERROR: %s is not a valid argument to "gam create course".' % sys.argv[i]
      sys.exit(3)
  if not u'ownerId' in body.keys():
    body['ownerId'] = u'me'
  if not u'name' in body.keys():
    body['name'] = u'Unknown Course'
  result = callGAPI(service=croom.courses(), function=u'create', body=body)
  print u'Created course %s' % result[u'id']

def doGetCourseInfo():
  courseId = sys.argv[3]
  if not courseId.isdigit():
    courseId = u'd:%s' % courseId
  croom = buildGAPIObject(u'classroom')
  info = callGAPI(service=croom.courses(), function=u'get', id=courseId)
  print_json(None, info)
  teachers = callGAPIpages(service=croom.courses().teachers(), function=u'list', items=u'teachers', courseId=courseId)
  students = callGAPIpages(service=croom.courses().students(), function=u'list', items=u'students', courseId=courseId)
  try:
    aliases = callGAPIpages(service=croom.courses().aliases(), function=u'list', items=u'aliases', throw_reasons=[u'notImplemented'], courseId=courseId)
  except googleapiclient.errors.HttpError:
    aliases = []
  if aliases:
    print u'Aliases:'
    for alias in aliases:
      print u'  %s' % alias[u'alias'][2:]
  print u'Participants:'
  print u' Teachers:'
  for teacher in teachers:
    try:
      print u'  %s - %s' % (teacher[u'profile'][u'name'][u'fullName'], teacher[u'profile'][u'emailAddress'])
    except KeyError:
      print u'  %s' % teacher[u'profile'][u'name'][u'fullName']
  print u' Students:'
  for student in students:
    try:
      print u'  %s - %s' % (student[u'profile'][u'name'][u'fullName'], student[u'profile'][u'emailAddress'])
    except KeyError:
      print u'  %s' % student[u'profile'][u'name'][u'fullName']

def doPrintCourses():
  croom = buildGAPIObject(u'classroom')
  croom_attributes = [{}]
  titles = []
  todrive = False
  teacherId = None
  studentId = None
  get_aliases = False
  i = 3
  while i < len(sys.argv):
    if sys.argv[i].lower() == u'teacher':
      teacherId = sys.argv[i+1]
      i += 2
    elif sys.argv[i].lower() == u'student':
      studentId = sys.argv[i+1]
      i += 2
    elif sys.argv[i].lower() == u'todrive':
      todrive = True
      i += 1
    elif sys.argv[i].lower() in [u'alias', u'aliases']:
      get_aliases = True
      i += 1
    else:
      print u'ERROR: %s is not a valid argument to "gam print courses".'
      sys.exit(3)
  printGettingMessage(u'Retrieving courses for organization (may take some time for large accounts)...\n')
  page_message = getPageMessage(u'courses')
  all_courses = callGAPIpages(service=croom.courses(), function=u'list', items=u'courses', page_message=page_message, teacherId=teacherId, studentId=studentId)
  for course in all_courses:
    croom_attributes.append(flatten_json(course))
    for item in croom_attributes[-1].keys():
      if item not in titles:
        titles.append(item)
        croom_attributes[0][item] = item
  if get_aliases:
    titles.append(u'Aliases')
    croom_attributes[0].update(Aliases=u'Aliases')
    num_courses = len(croom_attributes[1:])
    i = 1
    for course in croom_attributes[1:]:
      printGettingMessage('Getting aliases for course %s (%s/%s)\n' % (course[u'id'], i, num_courses))
      course_aliases = callGAPIpages(service=croom.courses().aliases(), function=u'list', items=u'aliases', courseId=course[u'id'])
      my_aliases = []
      for alias in course_aliases:
        my_aliases.append(alias[u'alias'][2:])
      course.update(Aliases=u' '.join(my_aliases))
      i += 1
  output_csv(croom_attributes, titles, u'Courses', todrive)

def doPrintCourseParticipants():
  croom = buildGAPIObject(u'classroom')
  participants_attributes = [{}]
  titles = []
  todrive = False
  courses = []
  teacherId = None
  studentId = None
  i = 3
  while i < len(sys.argv):
    if sys.argv[i].lower() in [u'course', u'class']:
      course = sys.argv[i+1]
      if not course.isdigit():
        course = u'd:%s' % course
      courses.append(course)
      i += 2
    elif sys.argv[i].lower() == u'teacher':
      teacherId = sys.argv[i+1]
      i += 2
    elif sys.argv[i].lower() == u'student':
      studentId = sys.argv[i+1]
      i += 2
    elif sys.argv[i].lower() == u'todrive':
      todrive = True
      i += 1
    else:
      print u'ERROR: %s is not a valid argument to "gam print course-participants".'
      sys.exit(3)
  printGettingMessage(u'Retrieving courses for organization (may take some time for large accounts)...\n')
  if len(courses) == 0:
    page_message = getPageMessage(u'courses')
    all_courses = callGAPIpages(service=croom.courses(), function=u'list', items=u'courses', page_message=page_message, teacherId=teacherId, studentId=studentId)
    for course in all_courses:
      courses.append(course[u'id'])
  else:
    all_courses = []
    for course in courses:
      all_courses.append(callGAPI(service=croom.courses(), function=u'get', id=course))
  y = 1
  num_courses = len(all_courses)
  for course in all_courses:
    course_id = course[u'id']
    page_message = getPageMessage(u'teachers', forWhom=u'course %s (%s/%s)' % (course_id, y, num_courses), noNL=True)
    teachers = callGAPIpages(service=croom.courses().teachers(), function=u'list', items=u'teachers', page_message=page_message, courseId=course_id)
    page_message = getPageMessage(u'students', forWhom=u'course %s (%s/%s)' % (course_id, y, num_courses), noNL=True)
    students = callGAPIpages(service=croom.courses().students(), function=u'list', items=u'students', page_message=page_message, courseId=course_id)
    for teacher in teachers:
      participant = flatten_json(teacher)
      participant[u'courseId'] = course_id
      participant[u'courseName'] = course[u'name']
      participant[u'userRole'] = u'TEACHER'
      participants_attributes.append(participant)
      for item in participant.keys():
        if item not in titles:
          titles.append(item)
          participants_attributes[0][item] = item
    for student in students:
      participant = flatten_json(student)
      participant[u'courseId'] = course_id
      participant[u'courseName'] = course[u'name']
      participant[u'userRole'] = u'STUDENT'
      participants_attributes.append(participant)
      for item in participant.keys():
        if item not in titles:
          titles.append(item)
          participants_attributes[0][item] = item
    y += 1
  output_csv(participants_attributes, titles, u'Course Participants', todrive)

PRINTJOB_ASCENDINGORDER_MAP = {
  u'createtime': u'CREATE_TIME',
  u'status': u'STATUS',
  u'title': u'TITLE',
  }
PRINTJOB_DESCENDINGORDER_MAP = {
  u'CREATE_TIME': u'CREATE_TIME_DESC',
  u'STATUS':  u'STATUS_DESC',
  u'TITLE': u'TITLE_DESC',
  }

def doPrintPrintJobs():
  cp = buildGAPIObject(u'cloudprint')
  job_attributes = [{}]
  titles = []
  todrive = False
  printerid = None
  owner = None
  status = None
  sortorder = None
  descending = False
  query = None
  i = 3
  age = None
  older_or_newer = None
  while i < len(sys.argv):
    if sys.argv[i].lower() == u'todrive':
      todrive = True
      i += 1
    elif sys.argv[i].lower().replace(u'_', u'') in [u'olderthan', u'newerthan']:
      if sys.argv[i].lower().replace(u'_', u'') == u'olderthan':
        older_or_newer = u'older'
      else:
        older_or_newer = u'newer'
      age_number = sys.argv[i+1][:-1]
      if not age_number.isdigit():
        print u'ERROR: expected a number, got %s' % age_number
        sys.exit(3)
      age_unit = sys.argv[i+1][-1].lower()
      if age_unit == u'm':
        age = int(time.time()) - (int(age_number) * 60)
      elif age_unit == u'h':
        age = int(time.time()) - (int(age_number) * 60 * 60)
      elif age_unit == u'd':
        age = int(time.time()) - (int(age_number) * 60 * 60 * 24)
      else:
        print u'ERROR: expected m (minutes), h (hours) or d (days), got %s' % age_unit
        sys.exit(3)
      i += 2
    elif sys.argv[i].lower() == u'query':
      query = sys.argv[i+1]
      i += 2
    elif sys.argv[i].lower() == u'status':
      status = sys.argv[i+1]
      i += 2
    elif sys.argv[i].lower() == u'ascending':
      descending = False
      i += 1
    elif sys.argv[i].lower() == u'descending':
      descending = True
      i += 1
    elif sys.argv[i].lower() == u'orderby':
      sortorder = sys.argv[i+1].lower().replace(u'_', u'')
      if sortorder not in PRINTJOB_ASCENDINGORDER_MAP:
        print 'Error: orderby must be one of %s. Got %s' % (','.join(PRINTJOB_ASCENDINGORDER_MAP), sortorder)
        sys.exit(4)
      sortorder = PRINTJOB_ASCENDINGORDER_MAP[sortorder]
      i += 2
    elif sys.argv[i].lower() in [u'printer', u'printerid']:
      printerid = sys.argv[i+1]
      i += 2
    elif sys.argv[i].lower() in [u'owner', u'user']:
      owner = sys.argv[i+1]
      i += 2
    else:
      print u'ERROR: %s is not a valid argument to "gam print printjobs"' % sys.argv[i]
      sys.exit(3)
  if sortorder and descending:
    sortorder = PRINTJOB_DESCENDINGORDER_MAP[sortorder]
  jobs = callGAPI(service=cp.jobs(), function=u'list', q=query, status=status, sortorder=sortorder, printerid=printerid, owner=owner)
  checkCloudPrintResult(jobs)
  for job in jobs[u'jobs']:
    createTime = int(job[u'createTime'])/1000
    if older_or_newer:
      if older_or_newer == u'older' and createTime > age:
        continue
      elif older_or_newer == u'newer' and createTime < age:
        continue
    updateTime = int(job[u'updateTime'])/1000
    job[u'createTime'] = datetime.datetime.fromtimestamp(createTime).strftime(u'%Y-%m-%d %H:%M:%S')
    job[u'updateTime'] = datetime.datetime.fromtimestamp(updateTime).strftime(u'%Y-%m-%d %H:%M:%S')
    job[u'tags'] = u' '.join(job[u'tags'])
    job_attributes.append(flatten_json(job))
    for item in job_attributes[-1].keys():
      if item not in titles:
        titles.append(item)
        job_attributes[0][item] = item
  output_csv(job_attributes, titles, u'Print Jobs', todrive)

def doPrintPrinters():
  cp = buildGAPIObject(u'cloudprint')
  printer_attributes = [{}]
  titles = []
  todrive = False
  query = None
  printer_type = None
  connection_status = None
  extra_fields = None
  i = 3
  while i < len(sys.argv):
    if sys.argv[i].lower() == u'query':
      query = sys.argv[i+1]
      i += 2
    elif sys.argv[i].lower() == u'type':
      printer_type = sys.argv[i+1]
      i += 2
    elif sys.argv[i].lower() == u'status':
      connection_status = sys.argv[i+1]
      i += 2
    elif sys.argv[i].lower().replace(u'_', u'') == u'extrafields':
      extra_fields = sys.argv[i+1]
      i += 2
    elif sys.argv[i].lower() == u'todrive':
      todrive = True
      i += 1
    else:
      print u'ERROR: %s is not a valid argument to "gam print printers".'
      sys.exit(3)
  printers = callGAPI(service=cp.printers(), function=u'list', q=query, type=printer_type, connection_status=connection_status, extra_fields=extra_fields)
  checkCloudPrintResult(printers)
  for printer in printers[u'printers']:
    createTime = int(printer[u'createTime'])/1000
    accessTime = int(printer[u'accessTime'])/1000
    updateTime = int(printer[u'updateTime'])/1000
    printer[u'createTime'] = datetime.datetime.fromtimestamp(createTime).strftime(u'%Y-%m-%d %H:%M:%S')
    printer[u'accessTime'] = datetime.datetime.fromtimestamp(accessTime).strftime(u'%Y-%m-%d %H:%M:%S')
    printer[u'updateTime'] = datetime.datetime.fromtimestamp(updateTime).strftime(u'%Y-%m-%d %H:%M:%S')
    printer[u'tags'] = u' '.join(printer[u'tags'])
    printer_attributes.append(flatten_json(printer))
    for item in printer_attributes[-1].keys():
      if item not in titles:
        titles.append(item)
        printer_attributes[0][item] = item
  output_csv(printer_attributes, titles, u'Printers', todrive)

def changeCalendarAttendees(users):
  cal = buildGAPIServiceObject(u'calendar', users[0])
  do_it = True
  i = 5
  allevents = False
  start_date = end_date = None
  while len(sys.argv) > i:
    if sys.argv[i].lower() == u'csv':
      csv_file = sys.argv[i+1]
      i += 2
    elif sys.argv[i].lower() == u'dryrun':
      do_it = False
      i += 1
    elif sys.argv[i].lower() == u'start':
      start_date = sys.argv[i+1]
      i += 2
    elif sys.argv[i].lower() == u'end':
      end_date = sys.argv[i+1]
      i += 2
    elif sys.argv[i].lower() == u'allevents':
      allevents = True
      i += 1
    else:
      showUsage()
      print u'%s is not a valid argument.'
      sys.exit(3)
  attendee_map = dict()
  csvfile = csv.reader(open(csv_file, 'rU'))
  for row in csvfile:
    attendee_map[row[0].lower()] = row[1].lower()
  for user in users:
    sys.stdout.write(u'Checking user %s\n' % user)
    if user.find(u'@') == -1:
      user = u'%s@%s' % (user, GC_Values[GC_DOMAIN])
    cal = buildGAPIServiceObject(u'calendar', user)
    page_token = None
    while True:
      events_page = callGAPI(service=cal.events(), function=u'list', calendarId=user, pageToken=page_token, timeMin=start_date, timeMax=end_date, showDeleted=False, showHiddenInvitations=False)
      print u'Got %s items' % len(events_page.get(u'items', []))
      for event in events_page.get(u'items', []):
        if event[u'status'] == u'cancelled':
          #print ' skipping cancelled event'
          continue
        try:
          event_summary = convertUTF8(event[u'summary'])
        except (KeyError, UnicodeEncodeError, UnicodeDecodeError):
          event_summary = event[u'id']
        try:
          if not allevents and event[u'organizer'][u'email'].lower() != user:
            #print ' skipping not-my-event %s' % event_summary
            continue
        except KeyError:
          pass # no email for organizer
        needs_update = False
        try:
          for attendee in event[u'attendees']:
            try:
              if attendee[u'email'].lower() in attendee_map.keys():
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
          body = dict()
          body[u'attendees'] = event[u'attendees']
          print u'UPDATING %s' % event_summary
          if do_it:
            callGAPI(service=cal.events(), function=u'patch', calendarId=user, eventId=event[u'id'], sendNotifications=False, body=body)
          else:
            print u' not pulling the trigger.'
        #else:
        #  print ' no update needed for %s' % event_summary
      try:
        page_token = events_page[u'nextPageToken']
      except KeyError:
        break

def deleteCalendar(users):
  cal = buildGAPIServiceObject(u'calendar', users[0])
  calendarId = sys.argv[5]
  if calendarId.find(u'@') == -1:
    calendarId = u'%s@%s' % (calendarId, GC_Values[GC_DOMAIN])
  for user in users:
    if user.find(u'@') == -1:
      user = u'%s@%s' % (user, GC_Values[GC_DOMAIN])
    cal = buildGAPIServiceObject(u'calendar', user)
    callGAPI(service=cal.calendarList(), function=u'delete', calendarId=calendarId)

def addCalendar(users):
  cal = buildGAPIServiceObject(u'calendar', users[0])
  body = dict()
  body[u'defaultReminders'] = list()
  body[u'id'] = sys.argv[5]
  if body[u'id'].find(u'@') == -1:
    body[u'id'] = u'%s@%s' % (body[u'id'], GC_Values[GC_DOMAIN])
  body[u'selected'] = True
  body[u'hidden'] = False
  colorRgbFormat = False
  i = 6
  while i < len(sys.argv):
    if sys.argv[i].lower() == u'selected':
      if sys.argv[i+1].lower() in true_values:
        body[u'selected'] = True
      elif sys.argv[i+1].lower() in false_values:
        body[u'selected'] = False
      else:
        showUsage()
        print u'Value for selected must be true or false, not %s' % sys.argv[i+1]
        exit(4)
      i += 2
    elif sys.argv[i].lower() == u'hidden':
      if sys.argv[i+1].lower() in true_values:
        body[u'hidden'] = True
      elif sys.argv[i+1].lower() in false_values:
        body[u'hidden'] = False
      else:
        showUsage()
        print u'Value for hidden must be true or false, not %s' % sys.argv[i+1]
        exit(4)
      i += 2
    elif sys.argv[i].lower() == u'reminder':
      method = sys.argv[i+1].lower()
      try:
        minutes = int(sys.argv[i+2])
      except ValueError:
        print u'Error: Reminder time must be specified in minutes, got %s' % sys.argv[i+2]
        sys.exit(22)
      if method != u'email' and method != u'sms' and method != u'popup':
        print u'Error: Method must be email, sms or popup. Got %s' % method
        sys.exit(23)
      body[u'defaultReminders'].append({u'method': method, u'minutes': minutes})
      i = i + 3
    elif sys.argv[i].lower() == u'summary':
      body[u'summaryOverride'] = sys.argv[i+1]
      i += 2
    elif sys.argv[i].lower() == u'colorindex':
      body[u'colorId'] = str(sys.argv[i+1])
      i += 2
    elif sys.argv[i].lower() == u'backgroundcolor':
      body[u'backgroundColor'] = sys.argv[i+1]
      colorRgbFormat = True
      i += 2
    elif sys.argv[i].lower() == u'foregroundcolor':
      body[u'foregroundColor'] = sys.argv[i+1]
      colorRgbFormat = True
      i += 2
    else:
      showUsage()
      print u'%s is not a valid argument for "gam add calendar"' % sys.argv[i]
  i = 1
  count = len(users)
  for user in users:
    if user.find(u'@') == -1:
      user = u'%s@%s' % (user, GC_Values[GC_DOMAIN])
    print u"Subscribing %s to %s calendar (%s of %s)" % (user, body['id'], i, count)
    cal = buildGAPIServiceObject(u'calendar', user)
    callGAPI(service=cal.calendarList(), function=u'insert', body=body, colorRgbFormat=colorRgbFormat)
    i += 1

def updateCalendar(users):
  calendarId = sys.argv[5]
  i = 6
  body = dict()
  body[u'id'] = calendarId
  colorRgbFormat = False
  while i < len(sys.argv):
    if sys.argv[i].lower() == u'selected':
      if sys.argv[i+1].lower() in true_values:
        body[u'selected'] = True
      elif sys.argv[i+1].lower() in false_values:
        body[u'selected'] = False
      else:
        showUsage()
        print u'Value for selected must be true or false, not %s' % sys.argv[i+1]
        exit(4)
      i += 2
    elif sys.argv[i].lower() == u'hidden':
      if sys.argv[i+1].lower() in true_values:
        body[u'hidden'] = True
      elif sys.argv[i+1].lower() in false_values:
        body[u'hidden'] = False
      else:
        showUsage()
        print u'Value for hidden must be true or false, not %s' % sys.argv[i+1]
        exit(4)
      i += 2
    elif sys.argv[i].lower() == u'summary':
      body[u'summaryOverride'] = sys.argv[i+1]
      i += 2
    elif sys.argv[i].lower() == u'colorindex':
      body[u'colorId'] = str(sys.argv[i+1])
      i += 2
    elif sys.argv[i].lower() == u'backgroundcolor':
      body[u'backgroundColor'] = sys.argv[i+1]
      colorRgbFormat = True
      i += 2
    elif sys.argv[i].lower() == u'foregroundcolor':
      body[u'foregroundColor'] = sys.argv[i+1]
      colorRgbFormat = True
      i += 2
    elif sys.argv[i].lower() == u'reminder':
      method = sys.argv[i+1].lower()
      try:
        minutes = int(sys.argv[i+2])
      except ValueError:
        print u'Error: Reminder time must be specified in minutes, got %s' % sys.argv[i+2]
        sys.exit(22)
      if method != u'email' and method != u'sms' and method != u'popup':
        print u'Error: Method must be email, sms or popup. Got %s' % method
        sys.exit(23)
      try:
        body[u'defaultReminders'].append({u'method': method, u'minutes': minutes})
      except KeyError:
        body[u'defaultReminders'] = [{u'method': method, u'minutes': minutes}]
      i = i + 3
    else:
      showUsage()
      print u'%s is not a valid argument for "gam update calendar"' % sys.argv[i]
  i = 1
  count = len(users)
  for user in users:
    print u"Updating %s's subscription to calendar %s (%s of %s)" % (user, calendarId, i, count)
    cal = buildGAPIServiceObject(u'calendar', user)
    callGAPI(service=cal.calendarList(), function=u'update', calendarId=calendarId, body=body, colorRgbFormat=colorRgbFormat)

def doPrinterShowACL():
  show_printer = sys.argv[2]
  cp = buildGAPIObject(u'cloudprint')
  printer_info = callGAPI(service=cp.printers(), function=u'get', printerid=show_printer)
  checkCloudPrintResult(printer_info)
  for acl in printer_info[u'printers'][0][u'access']:
    if u'key' in acl.keys():
      acl[u'accessURL'] = u'https://www.google.com/cloudprint/addpublicprinter.html?printerid=%s&key=%s' % (show_printer, acl[u'key'])
    print_json(None, acl)
    print

def doPrinterAddACL():
  printer = sys.argv[2]
  role = sys.argv[4].upper()
  scope = sys.argv[5]
  public = None
  skip_notification = True
  if scope.lower() == u'public':
    public = True
    scope = None
    role = None
    skip_notification = None
  elif scope.find(u'@') == -1:
    scope = u'/hd/domain/%s' % scope
  cp = buildGAPIObject(u'cloudprint')
  result = callGAPI(service=cp.printers(), function=u'share', printerid=printer, role=role, scope=scope, public=public, skip_notification=skip_notification)
  checkCloudPrintResult(result)
  who = scope
  if who == None:
    who = 'public'
    role = 'user'
  print u'Added %s %s' % (role, who)

def doPrinterDelACL():
  printer = sys.argv[2]
  scope = sys.argv[4]
  public = None
  if scope.lower() == u'public':
    public = True
    scope = None
  elif scope.find(u'@') == -1:
    scope = u'/hd/domain/%s' % scope
  cp = buildGAPIObject(u'cloudprint')
  result = callGAPI(service=cp.printers(), function=u'unshare', printerid=printer, scope=scope, public=public)
  checkCloudPrintResult(result)
  who = scope
  if who == None:
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
    filename = value['filename']
    mimetype = value['mimetype']
    lines.extend((
      '--{0}'.format(boundary),
      'Content-Disposition: form-data; name="{0}"; filename="{1}"'.format(
        escape_quote(name), escape_quote(filename)),
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
  i = 4
  while i < len(sys.argv):
    if sys.argv[i].lower().replace(u'_', u'') in [u'olderthan', u'newerthan']:
      if sys.argv[i].lower().replace(u'_', u'') == u'olderthan':
        older_or_newer = u'older'
      else:
        older_or_newer = u'newer'
      age_number = sys.argv[i+1][:-1]
      if not age_number.isdigit():
        print u'ERROR: expected a number, got %s' % age_number
        sys.exit(3)
      age_unit = sys.argv[i+1][-1].lower()
      if age_unit == u'm':
        age = int(time.time()) - (int(age_number) * 60)
      elif age_unit == u'h':
        age = int(time.time()) - (int(age_number) * 60 * 60)
      elif age_unit == u'd':
        age = int(time.time()) - (int(age_number) * 60 * 60 * 24)
      else:
        print u'ERROR: expected m (minutes), h (hours) or d (days), got %s' % age_unit
        sys.exit(3)
      i += 2
    elif sys.argv[i].lower() == u'query':
      query = sys.argv[i+1]
      i += 2
    elif sys.argv[i].lower() == u'status':
      status = sys.argv[i+1]
      i += 2
    elif sys.argv[i].lower() == u'ascending':
      descending = False
      i += 1
    elif sys.argv[i].lower() == u'descending':
      descending = True
      i += 1
    elif sys.argv[i].lower() == u'orderby':
      sortorder = sys.argv[i+1].lower().replace(u'_', u'')
      if sortorder not in PRINTJOB_ASCENDINGORDER_MAP:
        print 'Error: orderby must be one of %s. Got %s' % (','.join(PRINTJOB_ASCENDINGORDER_MAP), sortorder)
        sys.exit(4)
      sortorder = PRINTJOB_ASCENDINGORDER_MAP[sortorder]
      i += 2
    elif sys.argv[i].lower() in [u'owner', u'user']:
      owner = sys.argv[i+1]
      i += 2
    else:
      print u'ERROR: %s is not a valid argument to "gam printjobs fetch"' % sys.argv[i]
      sys.exit(3)
  if sortorder and descending:
    sortorder = PRINTJOB_DESCENDINGORDER_MAP[sortorder]
  result = callGAPI(service=cp.jobs(), function=u'list', q=query, status=status, sortorder=sortorder, printerid=printerid, owner=owner)
  if u'errorCode' in result.keys() and result[u'errorCode'] == 413:
    print u'No print jobs.'
    sys.exit(0)
  checkCloudPrintResult(result)
  valid_chars = u'-_.() abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789'
  ssd = '''{
  "state": {"type": "DONE"}
}'''
  for job in result[u'jobs']:
    createTime = int(job[u'createTime'])/1000
    if older_or_newer:
      if older_or_newer == u'older' and createTime > age:
        continue
      elif older_or_newer == u'newer' and createTime < age:
        continue
    fileUrl = job[u'fileUrl']
    jobid = job[u'id']
    fileName = job[u'title']
    fileName = u''.join(c if c in valid_chars else u'_' for c in fileName)
    fileName = u'%s-%s' % (fileName, jobid)
    _, content = cp._http.request(uri=fileUrl, method='GET')
    f = open(fileName, 'wb')
    f.write(content)
    f.close()
    #ticket = callGAPI(service=cp.jobs(), function=u'getticket', jobid=jobid, use_cjt=True)
    result = callGAPI(service=cp.jobs(), function=u'update', jobid=jobid, semantic_state_diff=ssd)
    checkCloudPrintResult(result)
    print u'Printed job %s to %s' % (jobid, fileName)

def doDelPrinter():
  cp = buildGAPIObject(u'cloudprint')
  printerid = sys.argv[3]
  result = callGAPI(service=cp.printers(), function=u'delete', printerid=printerid)
  checkCloudPrintResult(result)

def doGetPrinterInfo():
  cp = buildGAPIObject(u'cloudprint')
  printerid = sys.argv[3]
  everything = False
  i = 4
  while i < len(sys.argv):
    if sys.argv[i] == u'everything':
      everything = True
      i += 1
    else:
      print u'ERROR: %s is not a valid argument to "gam info printer..."'
      sys.exit(3)
  result = callGAPI(service=cp.printers(), function=u'get', printerid=printerid)
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
      print u'ERROR: %s is not a valid argument to "gam update printer"' % sys.argv[i]
      sys.exit(3)
  result = callGAPI(service=cp.printers(), function=u'update', printerid=printerid, **kwargs)
  checkCloudPrintResult(result)
  print u'Updated printer %s' % printerid

def doPrinterRegister():
  cp = buildGAPIObject(u'cloudprint')
  form_fields = {u'name': u'GAM',
                 u'proxy': u'GAM',
                 u'uuid': cp._http.request.credentials.id_token[u'sub'],
                 u'manufacturer': __author__,
                 u'model': u'cp1',
                 u'gcp_version': u'2.0',
                 u'setup_url': u'http://git.io/gam',
                 u'support_url': u'https://groups.google.com/forum/#!forum/google-apps-manager',
                 u'update_url': u'http://git.io/gamreleases',
                 u'firmware': __version__,
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
                 u'tags': [u'GAM', u'http://git.io/gam'],
                }
  form_files = {}
  body, headers = encode_multipart(form_fields, form_files)
  #Get the printer first to make sure our OAuth access token is fresh
  callGAPI(service=cp.printers(), function=u'list')
  _, result = cp._http.request(uri='https://www.google.com/cloudprint/register', method='POST', body=body, headers=headers)
  result = json.loads(result)
  checkCloudPrintResult(result)
  print u'Created printer %s' % result[u'printers'][0][u'id']

def doPrintJobResubmit():
  jobid = sys.argv[2]
  printerid = sys.argv[4]
  cp = buildGAPIObject(u'cloudprint')
  ssd = '''{
  "state": {"type": "HELD"}
}'''
  result = callGAPI(service=cp.jobs(), function=u'update', jobid=jobid, semantic_state_diff=ssd)
  checkCloudPrintResult(result)
  ticket = callGAPI(service=cp.jobs(), function=u'getticket', jobid=jobid, use_cjt=True)
  result = callGAPI(service=cp.jobs(), function=u'resubmit', printerid=printerid, jobid=jobid, ticket=ticket)
  checkCloudPrintResult(result)
  print u'Success resubmitting %s as job %s to printer %s' % (jobid, result[u'job'][u'id'], printerid)

def doPrintJobSubmit():
  printer = sys.argv[2]
  cp = buildGAPIObject(u'cloudprint')
  content = sys.argv[4]
  form_fields = {u'printerid': printer,
                 u'title': content,
                 u'ticket': u'{"version": "1.0"}',
                 u'tags': [u'GAM', u'http://git.io/gam']}
  i = 5
  while i < len(sys.argv):
    if sys.argv[i].lower() == u'tag':
      form_fields[u'tags'].append(sys.argv[i+1])
      i += 2
    elif sys.argv[i].lower() in [u'name', u'title']:
      form_fields[u'title'] = sys.argv[i+1]
      i += 2
    else:
      print u'ERROR: %s is not a valid argument for "gam printer ... print"'
      sys.exit(3)
  form_files = {}
  if content[:4] == u'http':
    form_fields[u'content'] = content
    form_fields[u'contentType'] = u'url'
  else:
    filepath = content
    content = ntpath.basename(content)
    mimetype = mimetypes.guess_type(filepath)[0]
    if mimetype == None:
      mimetype = u'application/octet-stream'
    f = open(filepath, 'rb')
    filecontent = f.read()
    f.close()
    form_files[u'content'] = {u'filename': content, u'content': filecontent, u'mimetype': mimetype}
  #result = callGAPI(service=cp.printers(), function=u'submit', body=body)
  body, headers = encode_multipart(form_fields, form_files)
  #Get the printer first to make sure our OAuth access token is fresh
  callGAPI(service=cp.printers(), function=u'get', printerid=printer)
  _, result = cp._http.request(uri='https://www.google.com/cloudprint/submit', method='POST', body=body, headers=headers)
  checkCloudPrintResult(result)
  if type(result) is str:
    result = json.loads(result)
  print u'Submitted print job %s' % result[u'job'][u'id']

def doDeletePrintJob():
  job = sys.argv[2]
  cp = buildGAPIObject(u'cloudprint')
  result = callGAPI(service=cp.jobs(), function=u'delete', jobid=job)
  checkCloudPrintResult(result)
  print u'Print Job %s deleted' % job

def doCancelPrintJob():
  job = sys.argv[2]
  cp = buildGAPIObject(u'cloudprint')
  ssd = '{"state": {"type": "ABORTED", "user_action_cause": {"action_code": "CANCELLED"}}}'
  result = callGAPI(service=cp.jobs(), function=u'update', jobid=job, semantic_state_diff=ssd)
  checkCloudPrintResult(result)
  print u'Print Job %s cancelled' % job

def checkCloudPrintResult(result):
  if type(result) is str:
    try:
      result = json.loads(result)
    except ValueError:
      print u'ERROR: unexpected response: %s' % result
      sys.exit(3)
  if not result[u'success']:
    print u'ERROR %s: %s' % (result[u'errorCode'], result[u'message'])
    sys.exit(result[u'errorCode'])

def doCalendarShowACL():
  show_cal = sys.argv[2]
  cal = buildGAPIObject(u'calendar')
  if show_cal.find(u'@') == -1:
    show_cal = u'%s@%s' % (show_cal, GC_Values[GC_DOMAIN])
  acls = callGAPI(service=cal.acl(), function=u'list', calendarId=show_cal)
  try:
    for rule in acls[u'items']:
      print u'  Scope %s - %s' % (rule[u'scope'][u'type'], rule[u'scope'][u'value'])
      print u'  Role: %s' % (rule[u'role'])
      print u''
  except IndexError:
    pass

def doCalendarAddACL(calendarId=None, act_as=None, role=None, scope=None, entity=None):
  if act_as != None:
    cal = buildGAPIServiceObject(u'calendar', act_as)
  else:
    cal = buildGAPIObject(u'calendar')
  body = dict()
  body[u'scope'] = dict()
  if calendarId == None:
    calendarId = sys.argv[2]
  if calendarId.find(u'@') == -1:
    calendarId = u'%s@%s' % (calendarId, GC_Values[GC_DOMAIN])
  if role != None:
    body[u'role'] = role
  else:
    body[u'role'] = sys.argv[4].lower()
  if body[u'role'] not in [u'freebusy', u'read', u'editor', u'owner', u'none']:
    print u'Error: Role must be freebusy, read, editor or owner. Not %s' % body['role']
    sys.exit(33)
  if body[u'role'] == u'freebusy':
    body[u'role'] = u'freeBusyReader'
  elif body[u'role'] == u'read':
    body[u'role'] = u'reader'
  elif body[u'role'] == u'editor':
    body[u'role'] = u'writer'
  if scope != None:
    body[u'scope'][u'type'] = scope
  else:
    body[u'scope'][u'type'] = sys.argv[5].lower()
  i = 6
  if body[u'scope'][u'type'] not in [u'default', u'user', u'group', u'domain']:
    body[u'scope'][u'type'] = u'user'
    i = 5
  try:
    if entity != None and body[u'scope'][u'type'] != u'default':
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
  callGAPI(service=cal.acl(), function=u'insert', calendarId=calendarId, body=body)

def doCalendarUpdateACL():
  calendarId = sys.argv[2]
  role = sys.argv[4].lower()
  scope = sys.argv[5].lower()
  try:
    entity = sys.argv[6].lower()
  except IndexError:
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
    entity = ''
  doCalendarAddACL(calendarId=calendarId, role=u'none', scope=scope, entity=entity)

def doCalendarWipeData():
  calendarId = sys.argv[2]
  cal = buildGAPIServiceObject(u'calendar', calendarId)
  if calendarId.find(u'@') == -1:
    calendarId = u'%s@%s' % (calendarId, GC_Values[GC_DOMAIN])
  callGAPI(service=cal.calendars(), function=u'clear', calendarId=calendarId)

def doCalendarAddEvent():
  calendarId = sys.argv[2]
  cal = buildGAPIServiceObject(u'calendar', calendarId)
  sendNotifications = timeZone = None
  i = 4
  body = {}
  while i < len(sys.argv):
    if sys.argv[i].lower() == u'notifyattendees':
      sendNotifications = True
      i += 1
    elif sys.argv[i].lower() == u'attendee':
      try:
        body[u'attendees'].append({u'email': sys.argv[i+1]})
      except KeyError:
        body[u'attendees'] = [{u'email': sys.argv[i+1]},]
      i += 2
    elif sys.argv[i].lower() == u'optionalattendee':
      try:
        body[u'attendees'].append({u'email': sys.argv[i+1], u'optional': True})
      except TypeError:
        body[u'attendees'] = [{u'email': sys.argv[i+1], u'optional': True},]
      i += 2
    elif sys.argv[i].lower() == u'anyonecanaddself':
      body[u'anyoneCanAddSelf'] = True
      i += 1
    elif sys.argv[i].lower() == u'description':
      body[u'description'] = sys.argv[i+1]
      i += 2
    elif sys.argv[i].lower() == u'start':
      if sys.argv[i+1].lower() == u'allday':
        body[u'start'] = {u'date': sys.argv[i+2]}
        i += 3
      else:
        body[u'start'] = {u'dateTime': sys.argv[i+1]}
        i += 2
    elif sys.argv[i].lower() == u'end':
      if sys.argv[i+1].lower() == u'allday':
        body[u'end'] = {u'date': sys.argv[i+2]}
        i += 3
      else:
        body[u'end'] = {u'dateTime': sys.argv[i+1]}
        i += 2
    elif sys.argv[i].lower() == u'guestscantinviteothers':
      body[u'guestsCanInviteOthers'] = False
      i += 1
    elif sys.argv[i].lower() == u'guestscantseeothers':
      body[u'guestsCanSeeOtherGuests'] = False
      i += 1
    elif sys.argv[i].lower() == u'id':
      body[u'id'] = sys.argv[i+1]
      i += 2
    elif sys.argv[i].lower() == u'summary':
      body[u'summary'] = sys.argv[i+1]
      i += 2
    elif sys.argv[i].lower() == u'location':
      body[u'location'] = sys.argv[i+1]
      i += 2
    elif sys.argv[i].lower() == u'available':
      body[u'transparency'] = u'transparent'
      i += 1
    elif sys.argv[i].lower() == u'visibility':
      if sys.argv[i+1].lower() in [u'default', u'public', u'private']:
        body[u'visibility'] = sys.argv[i+1].lower()
      else:
        print 'Error: visibility must be one of default, public or private, got %s' % sys.argv[i+1]
        sys.exit(3)
      i += 2
    elif sys.argv[i].lower() == u'tentative':
      body[u'status'] = u'tentative'
      i += 1
    elif sys.argv[i].lower() == u'source':
      body[u'source'] = {u'title': sys.argv[i+1], u'url': sys.argv[i+2]}
      i += 3
    elif sys.argv[i].lower() == u'noreminders':
      body[u'reminders'] = {u'useDefault': False}
      i += 1
    elif sys.argv[i].lower() == u'reminder':
      try:
        body[u'reminders'][u'overrides'].append({u'minutes': sys.argv[i+1], u'method': sys.argv[i+2]})
        body[u'reminders'][u'useDefault'] = False
      except KeyError:
        body[u'reminders'] = {u'useDefault': False, u'overrides': [{u'minutes': sys.argv[i+1], u'method': sys.argv[i+2]},]}
      i += 3
    elif sys.argv[i].lower() == u'recurrence':
      try:
        body[u'recurrence'].append(sys.argv[i+1])
      except KeyError:
        body[u'recurrence'] = [sys.argv[i+1],]
      i += 2
    elif sys.argv[i].lower() == u'timezone':
      timeZone = sys.argv[i+1]
      i += 2
    elif sys.argv[i].lower() == u'privateproperty':
      if u'extendedProperties' not in body:
        body[u'extendedProperties'] = {u'private': {}, u'shared': {}}
      body[u'extendedProperties']['private'][sys.argv[i+1]] = sys.argv[i+2]
      i += 3
    elif sys.argv[i].lower() == u'sharedproperty':
      if u'extendedProperties' not in body:
        body[u'extendedProperties'] = {u'private': {}, u'shared': {}}
      body[u'extendedProperties']['shared'][sys.argv[i+1]] = sys.argv[i+2]
      i += 3
    elif sys.argv[i].lower() == u'colorindex':
      body[u'colorId'] = str(sys.argv[i+1])
      i += 2
    else:
      print 'Error: %s is not a valid argument to "gam calendar..."' % sys.argv[i]
      sys.exit(4)
  if not timeZone and u'recurrence' in body:
    timeZone = callGAPI(service=cal.calendars(), function=u'get', calendarId=calendarId, fields=u'timeZone')[u'timeZone']
  if u'recurrence' in body:
    for a_time in [u'start', u'end']:
      try:
        body[a_time][u'timeZone'] = timeZone
      except KeyError:
        pass

  callGAPI(service=cal.events(), function=u'insert', calendarId=calendarId, sendNotifications=sendNotifications, body=body)


def doProfile(users):
  if sys.argv[4].lower() == u'share' or sys.argv[4].lower() == u'shared':
    body = {u'includeInGlobalAddressList': True}
  elif sys.argv[4].lower() == u'unshare' or sys.argv[4].lower() == u'unshared':
    body = {u'includeInGlobalAddressList': False}
  cd = buildGAPIObject(u'directory')
  count = len(users)
  i = 1
  for user in users:
    if user[:4].lower() == u'uid:':
      user = user[4:]
    elif user.find(u'@') == -1:
      user = u'%s@%s' % (user, GC_Values[GC_DOMAIN])
    print u'Setting Profile Sharing to %s for %s (%s of %s)' % (body[u'includeInGlobalAddressList'], user, i, count)
    callGAPI(service=cd.users(), function=u'patch', soft_errors=True, userKey=user, body=body)
    i += 1

def showProfile(users):
  i = 1
  count = len(users)
  cd = buildGAPIObject(u'directory')
  for user in users:
    if user[:4].lower() == u'uid:':
      user = user[4:]
    elif user.find(u'@') == -1:
      user = u'%s@%s' % (user, GC_Values[GC_DOMAIN])
    result = callGAPI(service=cd.users(), function=u'get', userKey=user, fields=u'includeInGlobalAddressList')
    try:
      print u'User: %s  Profile Shared: %s (%s/%s)' % (user, result[u'includeInGlobalAddressList'], i, count)
    except IndexError:
      pass
    i += 1

def doPhoto(users):
  cd = buildGAPIObject(u'directory')
  i = 1
  count = len(users)
  for user in users:
    if user[:4].lower() == u'uid:':
      user = user[4:]
    elif user.find('@') == -1:
      user = u'%s@%s' % (user, GC_Values[GC_DOMAIN])
    filename = sys.argv[5].replace(u'#user#', user)
    filename = filename.replace(u'#email#', user)
    filename = filename.replace(u'#username#', user[:user.find(u'@')])
    print u"Updating photo for %s with %s (%s of %s)" % (user, filename, i, count)
    i += 1
    if re.match(u'^(ht|f)tps?://.*$', filename):
      import urllib2
      try:
        f = urllib2.urlopen(filename)
        image_data = str(f.read())
      except urllib2.HTTPError, e:
        print e
        continue
    else:
      try:
        f = open(filename, 'rb')
        image_data = f.read()
        f.close()
      except IOError, e:
        print u' couldn\'t open %s: %s' % (filename, e.strerror)
        continue
    image_data = base64.urlsafe_b64encode(image_data)
    body = {u'photoData': image_data}
    callGAPI(service=cd.users().photos(), function=u'update', soft_errors=True, userKey=user, body=body)

def getPhoto(users):
  cd = buildGAPIObject(u'directory')
  i = 1
  count = len(users)
  for user in users:
    if user[:4].lower() == u'uid:':
      user = user[4:]
    elif user.find(u'@') == -1:
      user = u'%s@%s' % (user, GC_Values[GC_DOMAIN])
    filename = u'%s.jpg' % user
    print u"Saving photo to %s (%s/%s)" % (filename, i, count)
    i += 1
    try:
      photo = callGAPI(service=cd.users().photos(), function=u'get', throw_reasons=[u'notFound'], userKey=user)
    except googleapiclient.errors.HttpError:
      print u' no photo for %s' % user
      continue
    try:
      photo_data = str(photo[u'photoData'])
      print photo_data
      photo_data = base64.urlsafe_b64decode(photo_data)
    except KeyError:
      print u' no photo for %s' % user
      continue
    photo_file = open(filename, 'wb')
    photo_file.write(photo_data)
    photo_file.close()

def deletePhoto(users):
  cd = buildGAPIObject(u'directory')
  i = 1
  count = len(users)
  for user in users:
    if user[:4].lower() == u'uid:':
      user = user[4:]
    elif user.find('@') == -1:
      user = u'%s@%s' % (user, GC_Values[GC_DOMAIN])
    print u"Deleting photo for %s (%s of %s)" % (user, i, count)
    callGAPI(service=cd.users().photos(), function='delete', userKey=user)
    i += 1

def showCalendars(users):
  for user in users:
    cal = buildGAPIServiceObject(u'calendar', user)
    feed = callGAPI(service=cal.calendarList(), function=u'list')
    for usercal in feed[u'items']:
      print u'  Name: %s' % usercal['id']
      print convertUTF8(u'  Summary: %s' % usercal['summary'])
      try:
        print convertUTF8(u'    Description: %s' % usercal['description'])
      except KeyError:
        print u'    Description: '
      print u'    Access Level: %s' % usercal['accessRole']
      print u'    Timezone: %s' % usercal['timeZone']
      try:
        print convertUTF8(u'    Location: %s' % usercal['location'])
      except KeyError:
        pass
      try:
        print u'    Hidden: %s' % usercal['hidden']
      except KeyError:
        print u'    Hidden: False'
      try:
        print u'    Selected: %s' % usercal['selected']
      except KeyError:
        print u'    Selected: False'
      print u'    Default Reminders:'
      try:
        for reminder in usercal[u'defaultReminders']:
          print u'      Type: %s  Minutes: %s' % (reminder['method'], reminder['minutes'])
      except KeyError:
        pass
      print u''

def showCalSettings(users):
  for user in users:
    for user in users:
      cal = buildGAPIServiceObject(u'calendar', user)
      feed = callGAPI(service=cal.settings(), function='list')
      for setting in feed[u'items']:
        print u'%s: %s' % (setting[u'id'], setting[u'value'])

def showDriveSettings(users):
  todrive = False
  try:
    if sys.argv[5].lower() == u'todrive':
      todrive = True
  except IndexError:
    pass
  dont_show = [u'kind', u'selfLink', u'exportFormats', u'importFormats', u'maxUploadSizes', u'additionalRoleInfo', u'etag', u'features', u'user', u'isCurrentAppInstalled']
  count = 1
  drive_attr = []
  titles = [u'email',]
  for user in users:
    printGettingMessage(u'Getting Drive settings for %s (%s of %s)\n' % (user, count, len(users)))
    count += 1
    drive = buildGAPIServiceObject(u'drive', user)
    feed = callGAPI(service=drive.about(), function=u'get', soft_errors=True)
    if feed == None:
      continue
    row = {u'email': user}
    for setting in feed:
      if setting in dont_show:
        continue
      if setting == u'quotaBytesByService':
        for subsetting in feed[setting]:
          my_name = subsetting[u'serviceName']
          my_bytes = int(subsetting[u'bytesUsed'])
          row[my_name] = u'%smb' % (my_bytes / 1024 / 1024)
          if my_name not in titles:
            titles.append(my_name)
        continue
      row[setting] = feed[setting]
      if setting not in titles:
        titles.append(setting)
    drive_attr.append(row)
  headers = {}
  for title in titles:
    headers[title] = title
  drive_attr.insert(0, headers)
  output_csv(drive_attr, titles, u'User Drive Settings', todrive)

def doDriveActivity(users):
  drive_ancestorId = u'root'
  drive_fileId = None
  todrive = False
  i = 5
  while i < len(sys.argv):
    activity_object = sys.argv[i].lower().replace(u'_', '')
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
      print u'Error: %s is not a valid argument to gam <users> show driveactivity'
      sys.exit(3)
  activity_attributes = [{},]
  for user in users:
    activity = buildGAPIServiceObject(u'appsactivity', user)
    page_message = getPageMessage(u'activities', forWhom=user, noNL=True)
    feed = callGAPIpages(service=activity.activities(), function=u'list', items=u'activities',
                         page_message=page_message, source=u'drive.google.com', userId=u'me',
                         drive_ancestorId=drive_ancestorId, groupingStrategy=u'none',
                         drive_fileId=drive_fileId, pageSize=500)
    for item in feed:
      activity_attributes.append(flatten_json(item[u'combinedEvent']))
      for an_item in activity_attributes[-1].keys():
        if an_item not in activity_attributes[0]:
          activity_attributes[0][an_item] = an_item
  output_csv(activity_attributes, activity_attributes[0], u'Drive Activity', todrive)

def showDriveFileACL(users):
  fileId = sys.argv[5]
  for user in users:
    drive = buildGAPIServiceObject(u'drive', user)
    feed = callGAPI(service=drive.permissions(), function=u'list', fileId=fileId)
    for permission in feed[u'items']:
      try:
        print permission[u'name']
      except KeyError:
        pass
      for key in permission.keys():
        if key in [u'name', u'kind', u'etag', u'selfLink',]:
          continue
        print u' %s: %s' % (key, permission[key])
      print u''

def delDriveFileACL(users):
  fileId = sys.argv[5]
  permissionId = unicode(sys.argv[6])
  for user in users:
    drive = buildGAPIServiceObject(u'drive', user)
    if permissionId[:3].lower() == u'id:':
      permissionId = permissionId[3:]
    elif permissionId.lower() in [u'anyone']:
      pass
    else:
      permissionId = callGAPI(service=drive.permissions(), function=u'getIdForEmail', email=permissionId, fields=u'id')[u'id']
    print u'Removing permission for %s from %s' % (permissionId, fileId)
    callGAPI(service=drive.permissions(), function=u'delete', fileId=fileId, permissionId=permissionId)

def addDriveFileACL(users):
  fileId = sys.argv[5]
  body = {u'type': sys.argv[6].lower()}
  sendNotificationEmails = False
  emailMessage = None
  if body[u'type'] not in [u'user', u'group', u'domain', u'anyone']:
    print u'ERROR: permission type must be user, group domain or anyone. Got %s' % body[u'type']
  if body[u'type'] == u'anyone':
    i = 7
  else:
    body[u'value'] = sys.argv[7]
    i = 8
  while i < len(sys.argv):
    if sys.argv[i].lower().replace(u'_', u'') == u'withlink':
      body[u'withLink'] = True
      i += 1
    elif sys.argv[i].lower() == u'role':
      body[u'role'] = sys.argv[i+1]
      if body[u'role'] not in [u'reader', u'commenter', u'writer', u'owner', u'editor']:
        print u'ERROR: role must be reader, commenter, writer or owner, got %s' % body[u'role']
        sys.exit(9)
      if body[u'role'] == u'commenter':
        body[u'role'] = u'reader'
        body[u'additionalRoles'] = [u'commenter']
      elif body[u'role'] == u'editor':
        body[u'role'] = u'writer'
      i += 2
    elif sys.argv[i].lower().replace(u'_', u'') == u'sendemail':
      sendNotificationEmails = True
      i += 1
    elif sys.argv[i].lower().replace(u'_', u'') == u'emailmessage':
      sendNotificationEmails = True
      emailMessage = sys.argv[i+1]
      i += 2
    else:
      print u'ERROR: %s is not a valid argument for "gam ... add drivefileacl ..."' % sys.argv[i]
      sys.exit(9)
  for user in users:
    drive = buildGAPIServiceObject(u'drive', user)
    result = callGAPI(service=drive.permissions(), function=u'insert', fileId=fileId, sendNotificationEmails=sendNotificationEmails, emailMessage=emailMessage, body=body)
    print result

def updateDriveFileACL(users):
  fileId = sys.argv[5]
  permissionId = unicode(sys.argv[6])
  transferOwnership = None
  body = {}
  i = 7
  while i < len(sys.argv):
    if sys.argv[i].lower().replace(u'_', u'') == u'withlink':
      body[u'withLink'] = True
      i += 1
    elif sys.argv[i].lower() == u'role':
      body[u'role'] = sys.argv[i+1]
      if body[u'role'] not in [u'reader', u'commenter', u'writer', u'owner']:
        print u'ERROR: role must be reader, commenter, writer or owner, got %s' % body[u'role']
        sys.exit(9)
      if body[u'role'] == u'commenter':
        body[u'role'] = u'reader'
        body[u'additionalRoles'] = [u'commenter']
      i += 2
    elif sys.argv[i].lower().replace(u'_', u'') == u'transferownership':
      if sys.argv[i+1].lower() in true_values:
        transferOwnership = True
      elif sys.argv[i+1].lower() in false_values:
        transferOwnership = False
      else:
        print u'ERROR: transferownership should be true or false, got %s' % sys.argv[i+1].lower()
      i += 2
    else:
      print u'ERROR: %s is not a valid argument for "gam ... update drivefileacl ..."' % sys.argv[i]
      sys.exit(9)
  for user in users:
    drive = buildGAPIServiceObject(u'drive', user)
    if permissionId[:3].lower() == u'id:':
      permissionId = permissionId[3:]
    else:
      permissionId = callGAPI(service=drive.permissions(), function=u'getIdForEmail', email=permissionId, fields=u'id')[u'id']
    print u'updating permissions for %s to file %s' % (permissionId, fileId)
    result = callGAPI(service=drive.permissions(), function=u'patch', fileId=fileId, permissionId=permissionId, transferOwnership=transferOwnership, body=body)
    print result

def showDriveFiles(users):
  files_attr = [{u'Owner': u'Owner',}]
  titles = [u'Owner',]
  fields = u'nextPageToken,items(title,alternateLink'
  todrive = False
  query = u'"me" in owners'
  i = 5
  labels = list()
  while i < len(sys.argv):
    my_arg = sys.argv[i].lower().replace('_', '')
    if my_arg == u'todrive':
      todrive = True
      i += 1
    elif my_arg == u'query':
      query += u' and %s' % sys.argv[i+1]
      i += 2
    elif my_arg == u'allfields':
      fields = u'*'
      i += 1
    elif my_arg == u'createddate':
      fields += u',createdDate'
      i += 1
    elif my_arg == u'description':
      fields += u',description'
      i += 1
    elif my_arg == u'fileextension':
      fields += u',fileExtension'
      i += 1
    elif my_arg == u'filesize':
      fields += u',fileSize'
      i += 1
    elif my_arg == u'id':
      fields += u',id'
      i += 1
    elif my_arg in [u'restricted', u'restrict']:
      labels.append(u'restricted')
      i += 1
    elif my_arg in [u'starred', u'star']:
      labels.append(u'starred')
      i += 1
    elif my_arg in [u'trashed', u'trash']:
      labels.append(u'trashed')
      i += 1
    elif my_arg in [u'viewed', u'view']:
      labels.append(u'viewed')
      i += 1
    elif my_arg in [u'lastmodifyinguser', u'lastmodifyingusername']:
      fields += u',lastModifyingUserName'
      i += 1
    elif my_arg in [u'lastviewedbyuser', u'lastviewedbymedate']:
      fields += u',lastViewedByMeDate'
      i += 1
    elif my_arg in [u'md5', u'md5sum', u'md5checksum']:
      fields += u',md5Checksum'
      i += 1
    elif my_arg in [u'mimetype', u'mime']:
      fields += u',mimeType'
      i += 1
    elif my_arg in [u'modifiedbyuser', u'modifiedbymedate']:
      fields += u',modifiedByMeDate'
      i += 1
    elif my_arg in [u'modifieddate']:
      fields += u',modifiedDate'
      i += 1
    elif my_arg in [u'originalfilename']:
      fields += u',originalFilename'
      i += 1
    elif my_arg in [u'quotaused', 'quotabytesused']:
      fields += u',quotaBytesUsed'
      i += 1
    elif my_arg in [u'shared']:
      fields += u',shared'
      i += 1
    elif my_arg in [u'writerscanshare']:
      fields += u',writersCanShare'
      i += 1
    else:
      print u'Error: %s is not a valid argument for "gam ... show filelist"' % my_arg
      sys.exit(3)
  if len(labels) > 0:
    fields += ',labels(%s)' % ','.join(labels)
  if fields != u'*':
    fields += ')'
  for user in users:
    drive = buildGAPIServiceObject(u'drive', user)
    if user.find(u'@') == -1:
      print u'Error: got %s, expected a full email address' % user
      sys.exit(3)
    printGettingMessage(u'Getting files for %s...\n' % user)
    page_message = getPageMessage(u'files', forWhom=user)
    feed = callGAPIpages(service=drive.files(), function=u'list', page_message=page_message, soft_errors=True, q=query, maxResults=1000, fields=fields)
    for f_file in feed:
      a_file = {u'Owner': user}
      for attrib in f_file:
        if attrib in [u'kind', u'etags', u'etag', u'owners', u'parents', u'permissions']:
          continue
        attrib_type = type(f_file[attrib])
        if attrib not in titles and not attrib_type is dict:
          titles.append(attrib)
          files_attr[0][attrib] = attrib
        if attrib_type is list:
          a_file[attrib] = u' '.join(f_file[attrib])
        elif attrib_type is unicode or attrib_type is bool:
          a_file[attrib] = f_file[attrib]
        elif attrib_type is dict:
          for dict_attrib in f_file[attrib].keys():
            if dict_attrib in [u'kind', u'etags', u'etag']:
              continue
            if dict_attrib not in titles:
              titles.append(dict_attrib)
              files_attr[0][dict_attrib] = dict_attrib
            a_file[dict_attrib] = f_file[attrib][dict_attrib]
        else:
          print attrib_type
      files_attr.append(a_file)
  output_csv(files_attr, titles, u'%s %s %s Drive Files' % (GC_Values[GC_DOMAIN], sys.argv[1], sys.argv[2]), todrive)

def doDriveSearch(drive, query=None):
  printGettingMessage(u'Searching for files with query: "%s"...\n' % query)
  page_message = getPageMessage(u'files')
  files = callGAPIpages(service=drive.files(), function=u'list', page_message=page_message, q=query, fields=u'nextPageToken,items(id)', maxResults=1000)
  ids = list()
  for f_file in files:
    ids.append(f_file[u'id'])
  return ids

def deleteDriveFile(users):
  fileIds = sys.argv[5]
  function = u'trash'
  try:
    if sys.argv[6].lower() == u'purge':
      function = u'delete'
  except IndexError:
    pass
  for user in users:
    drive = buildGAPIServiceObject(u'drive', user)
    if fileIds[:6].lower() == u'query:':
      file_ids = doDriveSearch(drive, query=fileIds[6:])
    else:
      if fileIds[:8].lower() == u'https://' or fileIds[:7].lower == u'http://':
        fileIds = fileIds[fileIds.find(u'/d/')+3:]
        if fileIds.find(u'/') != -1:
          fileIds = fileIds[:fileIds.find(u'/')]
      file_ids = [fileIds,]
    if not file_ids:
      print u'No files to delete for %s' % user
    i = 0
    for fileId in file_ids:
      i += 1
      if function == u'trash':
        print u'trashing %s for %s (%s of %s)' % (fileId, user, i, len(file_ids))
      else:
        print u'purging %s for %s (%s of %s)' % (fileId, user, i, len(file_ids))
      callGAPI(service=drive.files(), function=function, fileId=fileId)

def printDriveFolderContents(feed, folderId, indent):
  for f_file in feed:
    for parent in f_file[u'parents']:
      if folderId == parent[u'id']:
        print ' ' * indent, convertUTF8(f_file[u'title'])
        if f_file[u'mimeType'] == u'application/vnd.google-apps.folder':
          printDriveFolderContents(feed, f_file[u'id'], indent+1)

def showDriveFileTree(users):
  for user in users:
    drive = buildGAPIServiceObject(u'drive', user)
    if user.find(u'@') == -1:
      print u'Error: got %s, expected a full email address' % user
      sys.exit(3)
    root_folder = callGAPI(service=drive.about(), function=u'get', fields=u'rootFolderId')[u'rootFolderId']
    printGettingMessage(u'Getting all files for %s...\n' % user)
    page_message = getPageMessage(u'files', forWhom=user)
    feed = callGAPIpages(service=drive.files(), function=u'list', page_message=page_message, maxResults=1000, fields=u'items(id,title,parents(id),mimeType),nextPageToken')
    printDriveFolderContents(feed, root_folder, 0)

def deleteEmptyDriveFolders(users):
  query = u'"me" in owners and mimeType = "application/vnd.google-apps.folder"'
  for user in users:
    drive = buildGAPIServiceObject(u'drive', user)
    if user.find(u'@') == -1:
      print u'Error: got %s, expected a full email address' % user
      sys.exit(3)
    deleted_empty = True
    while deleted_empty:
      printGettingMessage(u'Getting folders for %s...\n' % user)
      page_message = getPageMessage(u'folders', forWhom=user)
      feed = callGAPIpages(service=drive.files(), function=u'list', page_message=page_message, q=query, maxResults=1000, fields=u'items(title,id),nextPageToken')
      deleted_empty = False
      for folder in feed:
        children = callGAPI(service=drive.children(), function=u'list', folderId=folder[u'id'], maxResults=1, fields=u'items(id)')
        if not u'items' in children or len(children[u'items']) == 0:
          print convertUTF8(u' deleting empty folder %s...' % folder[u'title'])
          callGAPI(service=drive.files(), function=u'delete', fileId=folder[u'id'])
          deleted_empty = True
        else:
          print convertUTF8(u' not deleting folder %s because it contains at least 1 item (%s)' % (folder[u'title'], children[u'items'][0][u'id']))

def doUpdateDriveFile(users):
  convert = ocr = ocrLanguage = parent_query = local_filepath = media_body = fileIds = drivefilename = None
  operation = u'update'
  i = 5
  body = {}
  while i < len(sys.argv):
    if sys.argv[i].lower().replace(u'_', u'') == u'localfile':
      local_filepath = sys.argv[i+1]
      local_filename = ntpath.basename(local_filepath)
      mimetype = mimetypes.guess_type(local_filepath)[0]
      if mimetype == None:
        mimetype = u'application/octet-stream'
      body[u'title'] = local_filename
      body[u'mimeType'] = mimetype
      i += 2
    elif sys.argv[i].lower() == u'copy':
      operation = u'copy'
      i += 1
    elif sys.argv[i].lower() == u'id':
      fileIds = [sys.argv[i+1],]
      i += 2
    elif sys.argv[i].lower() == u'drivefilename':
      drivefilename = sys.argv[i+1]
      i += 2
    elif sys.argv[i].lower().replace(u'_', u'') == u'newfilename':
      body[u'title'] = sys.argv[i+1]
      i += 2
    elif sys.argv[i].lower() in [u'convert']:
      convert = True
      i += 1
    elif sys.argv[i].lower() in [u'ocr',]:
      ocr = True
      i += 1
    elif sys.argv[i].lower() in [u'ocrlanguage',]:
      ocrLanguage = sys.argv[i+1]
      i += 2
    elif sys.argv[i].lower() in [u'restrict', 'restricted']:
      if 'labels' not in body.keys():
        body[u'labels'] = dict()
      if sys.argv[i+1] in true_values:
        body[u'labels'][u'restricted'] = True
      elif sys.argv[i+1] in false_values:
        body[u'labels'][u'restricted'] = False
      else:
        print u'ERROR: value for restricted must be true or false, got %s' % sys.argv[i+1]
        sys.exit(9)
      i += 2
    elif sys.argv[i].lower() in [u'star', u'starred']:
      if u'labels' not in body.keys():
        body[u'labels'] = dict()
      if sys.argv[i+1] in true_values:
        body[u'labels'][u'starred'] = True
      elif sys.argv[i+1] in false_values:
        body[u'labels'][u'starred'] = False
      else:
        print u'ERROR: value for starred must be true or false, got %s' % sys.argv[i+1]
        sys.exit(9)
      i += 2
    elif sys.argv[i].lower() in [u'trash', u'trashed']:
      if u'labels' not in body.keys():
        body[u'labels'] = dict()
      if sys.argv[i+1] in true_values:
        body[u'labels'][u'trashed'] = True
      elif sys.argv[i+1] in false_values:
        body[u'labels'][u'trashed'] = False
      else:
        print u'ERROR: value for trashed must be true or false, got %s' % sys.argv[i+1]
        sys.exit(9)
      i += 2
    elif sys.argv[i].lower() in [u'view', u'viewed']:
      if u'labels' not in body.keys():
        body[u'labels'] = dict()
      if sys.argv[i+1] in true_values:
        body[u'labels'][u'viewed'] = True
      elif sys.argv[i+1] in false_values:
        body[u'labels'][u'viewed'] = False
      else:
        print u'ERROR: value for viewed must be true or false, got %s' % sys.argv[i+1]
        sys.exit(9)
      i += 2
    elif sys.argv[i].lower() == u'lastviewedbyme':
      body[u'lastViewedByMe'] = sys.argv[i+1]
      i += 2
    elif sys.argv[i].lower() == u'modifieddate':
      body[u'modifiedDate'] = sys.argv[i+1]
      i += 2
    elif sys.argv[i].lower() in [u'description',]:
      body[u'description'] = sys.argv[i+1]
      i += 2
    elif sys.argv[i].lower() in [u'mimetype',]:
      body[u'mimeType'] = sys.argv[i+1]
      if body[u'mimeType'].lower() in [u'gdoc', u'gdocument']:
        body[u'mimeType'] = u'application/vnd.google-apps.document'
      elif body[u'mimeType'].lower() == u'gdrawing':
        body[u'mimeType'] = u'application/vnd.google-apps.drawing'
      elif body[u'mimeType'].lower() in [u'gfolder', u'gdirectory']:
        body[u'mimeType'] = u'application/vnd.google-apps.folder'
      elif body[u'mimeType'].lower() == u'gform':
        body[u'mimeType'] = u'application/vnd.google-apps.form'
      elif body[u'mimeType'].lower() == u'gfusion':
        body[u'mimeType'] = u'application/vnd.google-apps.fusiontable'
      elif body[u'mimeType'].lower() == u'gpresentation':
        body[u'mimeType'] = u'application/vnd.google-apps.presentation'
      elif body[u'mimeType'].lower() == u'gscript':
        body[u'mimeType'] = u'application/vnd.google-apps.script'
      elif body[u'mimeType'].lower() == u'gsite':
        body[u'mimeType'] = u'application/vnd.google-apps.sites'
      elif body[u'mimeType'].lower() in [u'gsheet', u'gspreadsheet']:
        body[u'mimeType'] = u'application/vnd.google-apps.spreadsheet'
      i += 2
    elif sys.argv[i].lower() in [u'parentid']:
      if u'parents' not in body.keys():
        body[u'parents'] = list()
      body[u'parents'].append({u'id': sys.argv[i+1]})
      i += 2
    elif sys.argv[i].lower().replace(u'_', u'') in [u'parentname']:
      parent_query = u'mimeType = "application/vnd.google-apps.folder" and "me" in owners and title = "%s"' % sys.argv[i+1]
      i += 2
    elif sys.argv[i].lower() in [u'writerscantshare']:
      body[u'writersCanShare'] = False
      i += 1
    else:
      print u'Error: %s is not a valid argument for "gam ... create file"' % sys.argv[i]
      sys.exit(3)
  if not fileIds and not drivefilename:
    print u'ERROR: you need to specify either id or query in order to determine the file(s) to update'
    sys.exit(9)
  elif fileIds and drivefilename:
    print u'ERROR: you cannot specify both an id and a query.'
    sys.exit(9)
  for user in users:
    drive = buildGAPIServiceObject(u'drive', user)
    if parent_query:
      more_parents = doDriveSearch(drive, query=parent_query)
      if u'parents' not in body.keys():
        body[u'parents'] = list()
      for a_parent in more_parents:
        body[u'parents'].append({u'id': a_parent})
    if drivefilename:
      fileIds = doDriveSearch(drive, query=u'"me" in owners and title = "%s"' % drivefilename)
    if local_filepath:
      media_body = googleapiclient.http.MediaFileUpload(local_filepath, mimetype=mimetype, resumable=True)
    for fileId in fileIds:
      if operation == u'update':
        if media_body:
          result = callGAPI(service=drive.files(), function=u'update', fileId=fileId, convert=convert, ocr=ocr, ocrLanguage=ocrLanguage, media_body=media_body, body=body, fields='id')
        else:
          result = callGAPI(service=drive.files(), function=u'patch', fileId=fileId, convert=convert, ocr=ocr, ocrLanguage=ocrLanguage, body=body, fields='id,labels')
        try:
          print u'Successfully updated %s drive file with content from %s' % (result[u'id'], local_filename)
        except UnboundLocalError:
          print u'Successfully updated drive file/folder ID %s' % (result[u'id'])
      else:
        result = callGAPI(service=drive.files(), function=u'copy', fileId=fileId, convert=convert, ocr=ocr, ocrLanguage=ocrLanguage, body=body, fields=u'id,labels')
        print u'Successfully copied %s to %s' % (fileId, result[u'id'])

def createDriveFile(users):
  convert = ocr = ocrLanguage = parent_query = local_filepath = media_body = None
  i = 5
  body = {}
  while i < len(sys.argv):
    if sys.argv[i].lower().replace(u'_', u'') == u'localfile':
      local_filepath = sys.argv[i+1]
      local_filename = ntpath.basename(local_filepath)
      mimetype = mimetypes.guess_type(local_filepath)[0]
      if mimetype == None:
        mimetype = u'application/octet-stream'
      body[u'title'] = local_filename
      body[u'mimeType'] = mimetype
      i += 2
    elif sys.argv[i].lower().replace(u'_', u'') == u'drivefilename':
      body[u'title'] = sys.argv[i+1]
      i += 2
    elif sys.argv[i].lower() in [u'convert']:
      convert = True
      i += 1
    elif sys.argv[i].lower() in [u'ocr',]:
      ocr = True
      i += 1
    elif sys.argv[i].lower() in [u'ocrlanguage',]:
      ocrLanguage = sys.argv[i+1]
      i += 2
    elif sys.argv[i].lower() in [u'restrict', 'restricted']:
      if u'labels' not in body.keys():
        body[u'labels'] = dict()
      body[u'labels'][u'restricted'] = True
      i += 1
    elif sys.argv[i].lower() in [u'star', u'starred']:
      if u'labels' not in body.keys():
        body[u'labels'] = dict()
      body[u'labels'][u'starred'] = True
      i += 1
    elif sys.argv[i].lower() in [u'trash', u'trashed']:
      if u'labels' not in body.keys():
        body[u'labels'] = dict()
      body[u'labels'][u'trashed'] = True
      i += 1
    elif sys.argv[i].lower() in [u'view', u'viewed']:
      if u'labels' not in body.keys():
        body[u'labels'] = dict()
      body[u'labels'][u'viewed'] = True
      i += 1
    elif sys.argv[i].lower() == u'lastviewedbyme':
      body[u'lastViewedByMe'] = sys.argv[i+1]
      i += 2
    elif sys.argv[i].lower() == u'modifieddate':
      body[u'modifiedDate'] = sys.argv[i+1]
      i += 2
    elif sys.argv[i].lower() in [u'description',]:
      body[u'description'] = sys.argv[i+1]
      i += 2
    elif sys.argv[i].lower() in [u'mimetype',]:
      body[u'mimeType'] = sys.argv[i+1]
      if body[u'mimeType'].lower() in [u'gdoc', u'gdocument']:
        body[u'mimeType'] = u'application/vnd.google-apps.document'
      elif body[u'mimeType'].lower() == u'gdrawing':
        body[u'mimeType'] = u'application/vnd.google-apps.drawing'
      elif body[u'mimeType'].lower() in [u'gfolder', u'gdirectory']:
        body[u'mimeType'] = u'application/vnd.google-apps.folder'
      elif body[u'mimeType'].lower() == u'gform':
        body[u'mimeType'] = u'application/vnd.google-apps.form'
      elif body[u'mimeType'].lower() == u'gfusion':
        body[u'mimeType'] = u'application/vnd.google-apps.fusiontable'
      elif body[u'mimeType'].lower() == u'gpresentation':
        body[u'mimeType'] = u'application/vnd.google-apps.presentation'
      elif body[u'mimeType'].lower() == u'gscript':
        body[u'mimeType'] = u'application/vnd.google-apps.script'
      elif body[u'mimeType'].lower() == u'gsite':
        body[u'mimeType'] = u'application/vnd.google-apps.sites'
      elif body[u'mimeType'].lower() in [u'gsheet', u'gspreadsheet']:
        body[u'mimeType'] = u'application/vnd.google-apps.spreadsheet'
      i += 2
    elif sys.argv[i].lower() in [u'parentid']:
      if u'parents' not in body.keys():
        body[u'parents'] = list()
      body[u'parents'].append({u'id': sys.argv[i+1]})
      i += 2
    elif sys.argv[i].lower().replace(u'_', u'') in [u'parentname']:
      parent_query = u'mimeType = "application/vnd.google-apps.folder" and "me" in owners and title = "%s"' % sys.argv[i+1]
      i += 2
    elif sys.argv[i].lower() in [u'writerscantshare']:
      body[u'writersCanShare'] = False
      i += 1
    else:
      print u'Error: %s is not a valid argument for "gam ... create file"' % sys.argv[i]
      sys.exit(3)
  for user in users:
    drive = buildGAPIServiceObject(u'drive', user)
    if parent_query:
      more_parents = doDriveSearch(drive, query=parent_query)
      if u'parents' not in body.keys():
        body[u'parents'] = list()
      for a_parent in more_parents:
        body[u'parents'].append({u'id': a_parent})
    if local_filepath:
      media_body = googleapiclient.http.MediaFileUpload(local_filepath, mimetype=mimetype, resumable=True)
    result = callGAPI(service=drive.files(), function=u'insert', convert=convert, ocr=ocr, ocrLanguage=ocrLanguage, media_body=media_body, body=body, fields='id')
    try:
      print u'Successfully uploaded %s to Drive file ID %s' % (local_filename, result[u'id'])
    except UnboundLocalError:
      print u'Successfully created drive file/folder ID %s' % (result[u'id'])

def downloadDriveFile(users):
  i = 5
  query = fileIds = None
  gdownload_format = u'openoffice'
  target_folder = GC_Values[GC_DRIVE_DIR]
  safe_filename_chars = "-_.() %s%s" % (string.ascii_letters, string.digits)
  while i < len(sys.argv):
    if sys.argv[i].lower() == u'id':
      fileIds = [sys.argv[i+1],]
      i += 2
    elif sys.argv[i].lower() == 'query':
      query = sys.argv[i+1]
      i += 2
    elif sys.argv[i].lower() == u'format':
      gdownload_format = sys.argv[i+1].lower()
      if gdownload_format not in [u'openoffice', u'ms', u'microsoft', u'micro$oft', u'pdf']:
        print 'Error: format must be one of openoffice, microsoft or pdf. Got %s' % gdownload_format
        sys.exit(4)
      i += 2
    elif sys.argv[i].lower().replace('_', '') == u'targetfolder':
      target_folder = sys.argv[i+1]
      if not os.path.isdir(target_folder):
        os.makedirs(target_folder)
      i += 2
  export_extensions = {u'application/pdf': '.pdf',
                       u'application/vnd.openxmlformats-officedocument.wordprocessingml.document': u'.docx',
                       u'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet': u'.xlsx',
                       u'application/vnd.openxmlformats-officedocument.presentationml.presentation': u'.pptx',
                       u'application/vnd.oasis.opendocument.text': u'.odt',
                       u'application/x-vnd.oasis.opendocument.spreadsheet': u'.ods'}
  if gdownload_format == u'openoffice':
    export_formats = [u'application/vnd.oasis.opendocument.text',
                      u'application/x-vnd.oasis.opendocument.spreadsheet']
  elif gdownload_format in [u'ms', u'microsoft', u'micro$oft']:
    export_formats = [u'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
                      u'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
                      u'application/vnd.openxmlformats-officedocument.presentationml.presentation']
  elif gdownload_format == u'pdf':
    export_formats = [u'application/pdf',]
  if not query and not fileIds:
    print u'ERROR: need to specify a file ID with id parameter or a search query with the query parameter.'
    sys.exit(9)
  elif query and fileIds:
    print u'ERROR: you cannot specify both the id and query parameters at the same time.'
    sys.exit(9)
  for user in users:
    drive = buildGAPIServiceObject(u'drive', user)
    if query:
      fileIds = doDriveSearch(drive, query=query)
    else:
      if fileIds[0][:8].lower() == 'https://' or fileIds[0][:7].lower == 'http://':
        fileIds[0] = fileIds[0][fileIds[0].find('/d/')+3:]
        if fileIds[0].find('/') != -1:
          fileIds[0] = fileIds[0][:fileIds[0].find('/')]
    if not fileIds:
      print u'No files to download for %s' % user
    i = 0
    for fileId in fileIds:
      extension = None
      result = callGAPI(service=drive.files(), function=u'get', fileId=fileId, fields=u'fileSize,title,mimeType,downloadUrl,exportLinks')
      if result[u'mimeType'] == u'application/vnd.google-apps.folder':
        print u'Skipping download of folder %s' % result[u'title']
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
        for avail_export_format in result[u'exportLinks'].keys():
          if avail_export_format in export_formats:
            download_url = result[u'exportLinks'][avail_export_format]
            try:
              extension = export_extensions[avail_export_format]
            except KeyError:
              pass
            break
      file_title = result[u'title']
      safe_file_title = ''.join(c for c in file_title if c in safe_filename_chars)
      filename = os.path.join(target_folder, safe_file_title)
      if extension and filename.lower()[:len(extension)] != extension:
        filename = u'%s%s' % (filename, extension)
      y = 0
      if os.path.isfile(filename):
        while True:
          y += 1
          new_filename = os.path.join(target_folder, u'(%s)-%s' % (y, safe_file_title))
          if extension and new_filename.lower()[:len(extension)] != extension:
            new_filename = u'%s%s' % (new_filename, extension)
          if not os.path.isfile(new_filename):
            break
        filename = new_filename
      print my_line % filename
      _, content = drive._http.request(download_url)
      f = open(filename, 'wb')
      f.write(content)
      f.close()

def showDriveFileInfo(users):
  for user in users:
    fileId = sys.argv[5]
    drive = buildGAPIServiceObject(u'drive', user)
    feed = callGAPI(service=drive.files(), function=u'get', fileId=fileId)
    for setting in feed.keys():
      if setting == u'kind':
        continue
      setting_type = str(type(feed[setting]))
      if setting_type == u"<type 'list'>":
        print u'%s:' % setting
        for settin in feed[setting]:
          if settin == u'kind':
            continue
          settin_type = str(type(settin))
          if settin_type == u"<type 'dict'>":
            for setti in settin.keys():
              if setti == u'kind':
                continue
              print u' %s: %s' % (setti, settin[setti])
            print ''
      elif setting_type == u"<type 'dict'>":
        print u'%s:' % setting
        for settin in feed[setting].keys():
          if settin == u'kind':
            continue
          print u' %s: %s' % (settin, feed[setting][settin])
      else:
        print u'%s: %s' % (setting, feed[setting])

def transferSecCals(users):
  target_user = sys.argv[5]
  try:
    if sys.argv[6].lower() == u'keepuser':
      remove_source_user = False
  except IndexError:
    remove_source_user = True
  for user in users:
    source_cal = buildGAPIServiceObject(u'calendar', user)
    source_calendars = callGAPIpages(service=source_cal.calendarList(), function=u'list', minAccessRole=u'owner', showHidden=True, fields=u'items(id),nextPageToken')
    for source_cal in source_calendars:
      if source_cal[u'id'].find(u'@group.calendar.google.com') != -1:
        doCalendarAddACL(calendarId=source_cal[u'id'], act_as=user, role=u'owner', scope=u'user', entity=target_user)
        if remove_source_user:
          doCalendarAddACL(calendarId=source_cal[u'id'], act_as=target_user, role=u'none', scope=u'user', entity=user)

def transferDriveFiles(users):
  target_user = sys.argv[5]
  remove_source_user = True
  try:
    if sys.argv[6].lower() == u'keepuser':
      remove_source_user = False
  except IndexError:
    pass
  target_drive = buildGAPIServiceObject(u'drive', target_user)
  target_about = callGAPI(service=target_drive.about(), function=u'get', fields=u'quotaBytesTotal,quotaBytesUsed,rootFolderId')
  target_drive_free = int(target_about[u'quotaBytesTotal']) - int(target_about[u'quotaBytesUsed'])
  for user in users:
    counter = 0
    source_drive = buildGAPIServiceObject(u'drive', user)
    source_about = callGAPI(service=source_drive.about(), function=u'get', fields=u'quotaBytesTotal,quotaBytesUsed,rootFolderId, permissionId')
    source_drive_size = int(source_about[u'quotaBytesUsed'])
    if target_drive_free < source_drive_size:
      print u'Error: Cowardly refusing to perform migration due to lack of target drive space. Source size: %smb Target Free: %smb' % (source_drive_size / 1024 / 1024, target_drive_free / 1024 / 1024)
      sys.exit(4)
    print u'Source drive size: %smb  Target drive free: %smb' % (source_drive_size / 1024 / 1024, target_drive_free / 1024 / 1024)
    target_drive_free = target_drive_free - source_drive_size # prep target_drive_free for next user
    source_root = source_about[u'rootFolderId']
    source_permissionid = source_about[u'permissionId']
    printGettingMessage(u'Getting file list for source user: %s...\n' % user)
    page_message = getPageMessage(u'files')
    source_drive_files = callGAPIpages(service=source_drive.files(), function=u'list', page_message=page_message,
                                       q=u"'me' in owners and trashed = false", fields=u'items(id,parents,mimeType),nextPageToken')
    all_source_file_ids = []
    for source_drive_file in source_drive_files:
      all_source_file_ids.append(source_drive_file[u'id'])
    total_count = len(source_drive_files)
    printGettingMessage(u'Getting folder list for target user: %s...\n' % target_user)
    page_message = getPageMessage(u'folders')
    target_folders = callGAPIpages(service=target_drive.files(), function=u'list', page_message=page_message,
                                   q=u"'me' in owners and mimeType = 'application/vnd.google-apps.folder'", fields=u'items(id,title),nextPageToken')
    got_top_folder = False
    all_target_folder_ids = []
    for target_folder in target_folders:
      all_target_folder_ids.append(target_folder[u'id'])
      if (not got_top_folder) and target_folder[u'title'] == u'%s old files' % user:
        target_top_folder = target_folder[u'id']
        got_top_folder = True
    if not got_top_folder:
      create_folder = callGAPI(service=target_drive.files(), function=u'insert',
                               body={u'title': u'%s old files' % user, u'mimeType': u'application/vnd.google-apps.folder'}, fields=u'id')
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
            #print 'skipping %s' % file_id
            skipped_files = skip_file_for_now = True
            break
        if skip_file_for_now:
          continue
        else:
          transferred_files.append(drive_file[u'id'])
        counter += 1
        print u'Changing owner for file %s (%s/%s)' % (drive_file[u'id'], counter, total_count)
        body = {u'role': u'owner', u'type': u'user', u'value': target_user}
        callGAPI(service=source_drive.permissions(), function=u'insert', soft_errors=True, fileId=file_id, sendNotificationEmails=False, body=body)
        target_parents = []
        for parent in source_parents:
          try:
            if parent[u'isRoot']:
              target_parents.append({u'id': target_top_folder})
            else:
              target_parents.append({u'id': parent[u'id']})
          except TypeError:
            pass
        callGAPI(service=target_drive.files(), function=u'patch', soft_errors=True, retry_reasons=[u'notFound'], fileId=file_id, body={u'parents': target_parents})
        if remove_source_user:
          callGAPI(service=target_drive.permissions(), function=u'delete', soft_errors=True, fileId=file_id, permissionId=source_permissionid)
      if not skipped_files:
        break

def doImap(users):
  if sys.argv[4].lower() in true_values:
    enable = True
  elif sys.argv[4].lower() in false_values:
    enable = False
  emailsettings = getEmailSettingsObject()
  count = len(users)
  i = 1
  for user in users:
    if user.find(u'@') > 0:
      emailsettings.domain = user[user.find(u'@')+1:]
      user = user[:user.find(u'@')]
    else:
      emailsettings.domain = GC_Values[GC_DOMAIN] #make sure it's back at default domain
    print u"Setting IMAP Access to %s for %s (%s of %s)" % (str(enable), user+u'@'+emailsettings.domain, i, count)
    i += 1
    callGData(service=emailsettings, function=u'UpdateImap', soft_errors=True, username=user, enable=enable)

def getImap(users):
  emailsettings = getEmailSettingsObject()
  i = 1
  count = len(users)
  for user in users:
    if user.find(u'@') > 0:
      emailsettings.domain = user[user.find(u'@')+1:]
      user = user[:user.find(u'@')]
    else:
      emailsettings.domain = GC_Values[GC_DOMAIN]
    imapsettings = callGData(service=emailsettings, function=u'GetImap', soft_errors=True, username=user)
    try:
      print u'User %s  IMAP Enabled:%s (%s of %s)' % (user+u'@'+emailsettings.domain, imapsettings[u'enable'], i, count)
    except TypeError:
      pass
    i += 1

def getProductAndSKU(sku):
  if sku.lower() in [u'apps', u'gafb', u'gafw']:
    sku = u'Google-Apps-For-Business'
  elif sku.lower() in [u'gams',]:
    sku = u'Google-Apps-For-Postini'
  elif sku.lower() in [u'gau', u'unlimited', u'd4w', u'dfw']:
    sku = u'Google-Apps-Unlimited'
  elif sku.lower() == u'coordinate':
    sku = u'Google-Coordinate'
  elif sku.lower() == u'vault':
    sku = u'Google-Vault'
  elif sku.lower() in [u'vfe',]:
    sku = u'Google-Vault-Former-Employee'
  elif sku.lower() in [u'drive-20gb', u'drive20gb', u'20gb']:
    sku = u'Google-Drive-storage-20GB'
  elif sku.lower() in [u'drive-50gb', u'drive50gb', u'50gb']:
    sku = u'Google-Drive-storage-50GB'
  elif sku.lower() in [u'drive-200gb', u'drive200gb', u'200gb']:
    sku = u'Google-Drive-storage-200GB'
  elif sku.lower() in [u'drive-400gb', u'drive400gb', u'400gb']:
    sku = u'Google-Drive-storage-400GB'
  elif sku.lower() in [u'drive-1tb', u'drive1tb', u'1tb']:
    sku = u'Google-Drive-storage-1TB'
  elif sku.lower() in [u'drive-2tb', u'drive2tb', u'2tb']:
    sku = u'Google-Drive-storage-2TB'
  elif sku.lower() in [u'drive-4tb', u'drive4tb', u'4tb']:
    sku = u'Google-Drive-storage-4TB'
  elif sku.lower() in [u'drive-4tb', u'drive8tb', u'8tb']:
    sku = u'Google-Drive-storage-8TB'
  elif sku.lower() in [u'drive-16tb', u'drive16tb', u'16tb']:
    sku = u'Google-Drive-storage-16TB'
  if sku[:20] == u'Google-Drive-storage':
    product = u'Google-Drive-storage'
  else:
    try:
      product = re.search(u'^([A-Z,a-z]*-[A-Z,a-z]*)', sku).group(1)
    except AttributeError:
      product = sku
  return (product, sku)

def doLicense(users, operation):
  lic = buildGAPIObject(u'licensing')
  sku = sys.argv[5]
  productId, skuId = getProductAndSKU(sku)
  for user in users:
    if user.find(u'@') == -1:
      user = u'%s@%s' % (user, GC_Values[GC_DOMAIN])
    if operation == u'delete':
      callGAPI(service=lic.licenseAssignments(), function=operation, soft_errors=True, productId=productId, skuId=skuId, userId=user)
    elif operation == u'insert':
      callGAPI(service=lic.licenseAssignments(), function=operation, soft_errors=True, productId=productId, skuId=skuId, body={u'userId': user})
    elif operation == u'patch':
      try:
        old_sku = sys.argv[6]
        if old_sku.lower() == u'from':
          old_sku = sys.argv[7]
      except KeyError:
        print u'You need to specify the user\'s old SKU as the last argument'
        sys.exit(5)
      _, old_sku = getProductAndSKU(old_sku)
      callGAPI(service=lic.licenseAssignments(), function=operation, soft_errors=True, productId=productId, skuId=old_sku, userId=user, body={u'skuId': skuId})

def doPop(users):
  if sys.argv[4].lower() in true_values:
    enable = True
  elif sys.argv[4].lower() in false_values:
    enable = False
  enable_for = u'ALL_MAIL'
  action = u'KEEP'
  i = 5
  while i < len(sys.argv):
    if sys.argv[i].lower() == u'for':
      if sys.argv[i+1].lower() == u'allmail':
        enable_for = u'ALL_MAIL'
        i += 2
      elif sys.argv[i+1].lower() == u'newmail':
        enable_for = u'MAIL_FROM_NOW_ON'
        i += 2
    elif sys.argv[i].lower() == u'action':
      if sys.argv[i+1].lower() == u'keep':
        action = u'KEEP'
        i += 2
      elif sys.argv[i+1].lower() == u'archive':
        action = u'ARCHIVE'
        i += 2
      elif sys.argv[i+1].lower() == u'delete':
        action = u'DELETE'
        i += 2
    elif sys.argv[i].lower() == u'confirm':
      i += 1
    else:
      showUsage()
      sys.exit(2)
  emailsettings = getEmailSettingsObject()
  count = len(users)
  i = 1
  for user in users:
    if user.find(u'@') > 0:
      emailsettings.domain = user[user.find(u'@')+1:]
      user = user[:user.find(u'@')]
    else:
      emailsettings.domain = GC_Values[GC_DOMAIN] #make sure it's back at default domain
    print u"Setting POP Access to %s for %s (%s of %s)" % (str(enable), user+u'@'+emailsettings.domain, i, count)
    i += 1
    callGData(service=emailsettings, function=u'UpdatePop', soft_errors=True, username=user, enable=enable, enable_for=enable_for, action=action)

def getPop(users):
  emailsettings = getEmailSettingsObject()
  for user in users:
    if user.find(u'@') > 0:
      emailsettings.domain = user[user.find(u'@')+1:]
      user = user[:user.find(u'@')]
    else:
      emailsettings.domain = GC_Values[GC_DOMAIN]
    popsettings = callGData(service=emailsettings, function=u'GetPop', soft_errors=True, username=user)
    try:
      print u'User %s  POP Enabled:%s  Action:%s' % (user+u'@'+emailsettings.domain, popsettings[u'enable'], popsettings[u'action'])
    except TypeError:
      pass

def doSendAs(users):
  sendas = sys.argv[4]
  sendasName = sys.argv[5]
  make_default = reply_to = None
  i = 6
  while i < len(sys.argv):
    if sys.argv[i].lower() == u'default':
      make_default = True
      i += 1
    elif sys.argv[i].lower() == u'replyto':
      reply_to = sys.argv[i+1]
      i += 2
    else:
      showUsage()
      sys.exit(2)
  emailsettings = getEmailSettingsObject()
  if sendas.find(u'@') < 0:
    sendas = sendas+u'@'+GC_Values[GC_DOMAIN]
  count = len(users)
  i = 1
  for user in users:
    if user.find(u'@') > 0:
      emailsettings.domain = user[user.find(u'@')+1:]
      user = user[:user.find(u'@')]
    else:
      emailsettings.domain = GC_Values[GC_DOMAIN] #make sure it's back at default domain
    print u"Allowing %s to send as %s (%s of %s)" % (user+u'@'+emailsettings.domain, sendas, i, count)
    i += 1
    callGData(service=emailsettings, function=u'CreateSendAsAlias', soft_errors=True, username=user, name=sendasName, address=sendas, make_default=make_default, reply_to=reply_to)

def showSendAs(users):
  emailsettings = getEmailSettingsObject()
  for user in users:
    if user.find(u'@') > 0:
      emailsettings.domain = user[user.find(u'@')+1:]
      user = user[:user.find(u'@')]
    else:
      emailsettings.domain = GC_Values[GC_DOMAIN]
    print u'%s has the following send as aliases:' %  (user+u'@'+emailsettings.domain)
    sendases = callGData(service=emailsettings, function=u'GetSendAsAlias', soft_errors=True, username=user)
    try:
      for sendas in sendases:
        if sendas[u'isDefault'] == u'true':
          default = u'yes'
        else:
          default = u'no'
        if sendas[u'replyTo']:
          replyto = u' Reply To:<'+sendas[u'replyTo']+'>'
        else:
          replyto = u''
        if sendas[u'verified'] == u'true':
          verified = u'yes'
        else:
          verified = u'no'
        print u' "%s" <%s>%s Default:%s Verified:%s' % (sendas[u'name'], sendas[u'address'], replyto, default, verified)
    except TypeError:
      pass
    print u''

def doLanguage(users):
  language = sys.argv[4]
  emailsettings = getEmailSettingsObject()
  count = len(users)
  i = 1
  for user in users:
    if user.find(u'@') > 0:
      emailsettings.domain = user[user.find('@')+1:]
      user = user[:user.find('@')]
    else:
      emailsettings.domain = GC_Values[GC_DOMAIN] #make sure it's back at default domain
    print u"Setting the language for %s to %s (%s of %s)" % (user+u'@'+emailsettings.domain, language, i, count)
    i += 1
    callGData(service=emailsettings, function=u'UpdateLanguage', soft_errors=True, username=user, language=language)

def doUTF(users):
  if sys.argv[4].lower() in true_values:
    SetUTF = True
  elif sys.argv[4].lower() in false_values:
    SetUTF = False
  emailsettings = getEmailSettingsObject()
  count = len(users)
  i = 1
  for user in users:
    if user.find(u'@') > 0:
      emailsettings.domain = user[user.find(u'@')+1:]
      user = user[:user.find(u'@')]
    else:
      emailsettings.domain = GC_Values[GC_DOMAIN] #make sure it's back at default domain
    print u"Setting UTF-8 to %s for %s (%s of %s)" % (str(SetUTF), user+u'@'+emailsettings.domain, i, count)
    i += 1
    callGData(service=emailsettings, function=u'UpdateGeneral', soft_errors=True, username=user, unicode=SetUTF)

def doPageSize(users):
  if sys.argv[4] == u'25' or sys.argv[4] == u'50' or sys.argv[4] == u'100':
    PageSize = sys.argv[4]
  else:
    showUsage()
    sys.exit(2)
  emailsettings = getEmailSettingsObject()
  count = len(users)
  i = 1
  for user in users:
    if user.find(u'@') > 0:
      emailsettings.domain = user[user.find(u'@')+1:]
      user = user[:user.find(u'@')]
    else:
      emailsettings.domain = GC_Values[GC_DOMAIN] #make sure it's back at default domain
    print u"Setting Page Size to %s for %s (%s of %s)" % (PageSize, user+u'@'+emailsettings.domain, i, count)
    i += 1
    callGData(service=emailsettings, function=u'UpdateGeneral', soft_errors=True, username=user, page_size=PageSize)

def doShortCuts(users):
  if sys.argv[4].lower() in true_values:
    SetShortCuts = True
  elif sys.argv[4].lower() in false_values:
    SetShortCuts = False
  emailsettings = getEmailSettingsObject()
  count = len(users)
  i = 1
  for user in users:
    if user.find(u'@') > 0:
      emailsettings.domain = user[user.find(u'@')+1:]
      user = user[:user.find(u'@')]
    else:
      emailsettings.domain = GC_Values[GC_DOMAIN] #make sure it's back at default domain
    print u"Setting Keyboard Short Cuts to %s for %s (%s of %s)" % (str(SetShortCuts), user+u'@'+emailsettings.domain, i, count)
    i += 1
    callGData(service=emailsettings, function=u'UpdateGeneral', soft_errors=True, username=user, shortcuts=SetShortCuts)

def doArrows(users):
  if sys.argv[4].lower() in true_values:
    SetArrows = True
  elif sys.argv[4].lower() in false_values:
    SetArrows = False
  emailsettings = getEmailSettingsObject()
  count = len(users)
  i = 1
  for user in users:
    if user.find(u'@') > 0:
      emailsettings.domain = user[user.find(u'@')+1:]
      user = user[:user.find(u'@')]
    else:
      emailsettings.domain = GC_Values[GC_DOMAIN] #make sure it's back at default domain
    print u"Setting Personal Indicator Arrows to %s for %s (%s of %s)" % (str(SetArrows), user+u'@'+emailsettings.domain, i, count)
    i += 1
    callGData(service=emailsettings, function=u'UpdateGeneral', soft_errors=True, username=user, arrows=SetArrows)

def doSnippets(users):
  if sys.argv[4].lower() in true_values:
    SetSnippets = True
  elif sys.argv[4].lower() in false_values:
    SetSnippets = False
  emailsettings = getEmailSettingsObject()
  count = len(users)
  i = 1
  for user in users:
    if user.find(u'@') > 0:
      emailsettings.domain = user[user.find(u'@')+1:]
      user = user[:user.find(u'@')]
    else:
      emailsettings.domain = GC_Values[GC_DOMAIN] #make sure it's back at default domain
    print u"Setting Preview Snippets to %s for %s (%s of %s)" % (str(SetSnippets), user+u'@'+emailsettings.domain, i, count)
    i += 1
    callGData(service=emailsettings, function=u'UpdateGeneral', soft_errors=True, username=user, snippets=SetSnippets)

def doLabel(users):
  label = sys.argv[4]
  count = len(users)
  i = 1
  n = 5
  if sys.argv[3].lower() == u'add':
    n = 6
    label = sys.argv[5]
  body = {u'name': label}
  while n < len(sys.argv):
    if sys.argv[n].lower().replace(u'_', u'') == u'labellistvisibility':
      if sys.argv[n+1].lower().replace(u'_', u'') == u'hide':
        body[u'labelListVisibility'] = u'labelHide'
      elif sys.argv[n+1].lower().replace(u'_', u'') == u'show':
        body[u'labelListVisibility'] = u'labelShow'
      elif sys.argv[n+1].lower().replace(u'_', u'') == u'showifunread':
        body[u'labelListVisibility'] = u'labelShowIfUnread'
      else:
        print u'Error: label_list_visibility must be one of hide, show or show_if_unread, got %s' % sys.argv[n+1]
        sys.exit(3)
      n += 2
    elif sys.argv[n].lower().replace(u'_', u'') == u'messagelistvisibility':
      if sys.argv[n+1].lower().replace(u'_', u'') == u'hide':
        body[u'messageListVisibility'] = u'hide'
      elif sys.argv[n+1].lower().replace(u'_', u'') == u'show':
        body[u'messageListVisibility'] = u'show'
      else:
        print u'Error: message_list_visibility must be one of hide or show, got %s' % sys.argv[n+1]
        sys.exit(3)
      n += 2
    else:
      print u'Error: %s is not a valid argument for this command.' % sys.argv[n]
      sys.exit(3)
  for user in users:
    gmail = buildGAPIServiceObject(u'gmail', act_as=user)
    print u"Creating label %s for %s (%s of %s)" % (label, user, i, count)
    i += 1
    callGAPI(service=gmail.users().labels(), function=u'create', soft_errors=True, userId=user, body=body)

def doDeleteMessages(users, trashOrDelete):
  query = None
  doIt = False
  maxToProcess = GC_Values[GC_MAX_MESSAGES_TO_PROCESS]
  i = 5
  while i < len(sys.argv):
    if sys.argv[i].lower() == u'query':
      query = sys.argv[i+1]
      i += 2
    elif sys.argv[i].lower() == u'doit':
      doIt = True
      i += 1
    elif sys.argv[i].lower().replace(u'_', u'') == u'maxtodelete':
      maxToProcess = int(sys.argv[i+1])
      i += 2
    else:
      print u'ERROR: %s is not a valid argument for gam <users> delete messages.' % sys.argv[i]
      sys.exit(3)
  if not query:
    print u'ERROR: No query specified. You must specify some query!'
    sys.exit(4)
  for user in users:
    gmail = buildGAPIServiceObject(u'gmail', act_as=user)
    page_message = getPageMessage(u'messages', forWhom=user)
    listResult = callGAPIpages(service=gmail.users().messages(),
                               function=u'list', items=u'messages', page_message=page_message,
                               userId=u'me', q=query, includeSpamTrash=True)
    del_count = len(listResult)
    if not doIt:
      print u'would try to delete %s messages for user %s (max %s)\n' % (del_count, user, maxToProcess)
      continue
    elif del_count > maxToProcess:
      print u'WARNING: refusing to delete ANY messages for %s since max_to_delete is %s and messages to be deleted is %s\n' % (user, maxToProcess, del_count)
      continue
    i = 1
    # Batch seemed like a good idea but it kills
    # Gmail UI for users :-(
    '''dbatch = googleapiclient.http.BatchHttpRequest()
    for del_me in listResult:
      print u' deleting message %s for user %s (%s/%s)' % (del_me[u'id'], user, i, del_count)
      i += 1
      if trashOrDelete == u'trash':
        dbatch.add(gmail.users().messages().trash(userId=u'me',
         id=del_me[u'id']), callback=gmail_del_result)
      elif trashOrDelete == u'delete':
        dbatch.add(gmail.users().messages().delete(userId=u'me',
         id=del_me[u'id']), callback=gmail_del_result)
      if len(dbatch._order) == 5:
        dbatch.execute()
        dbatch = googleapiclient.http.BatchHttpRequest()
    if len(dbatch._order) > 0:
      dbatch.execute()'''
    for del_me in listResult:
      print u' %s message %s for user %s (%s/%s)' % (trashOrDelete, del_me[u'id'], user, i, del_count)
      i += 1
      callGAPI(service=gmail.users().messages(), function=trashOrDelete,
               id=del_me[u'id'], userId=u'me')

def doSpamMessages(users):
  query = None
  doIt = False
  maxToProcess = GC_Values[GC_MAX_MESSAGES_TO_PROCESS]
  i = 5
  while i < len(sys.argv):
    if sys.argv[i].lower() == u'query':
      query = sys.argv[i+1]
      i += 2
    elif sys.argv[i].lower() == u'doit':
      doIt = True
      i += 1
    elif sys.argv[i].lower().replace(u'_', u'') == u'maxtomove':
      maxToProcess = int(sys.argv[i+1])
      i += 2
    else:
      print u'ERROR: %s is not a valid argument for gam <users> spam messages.' % sys.argv[i]
      sys.exit(3)
  if not query:
    print u'ERROR: No query specified. You must specify some query!'
    sys.exit(4)
  for user in users:
    gmail = buildGAPIServiceObject(u'gmail', act_as=user)
    page_message = getPageMessage(u'messages', forWhom=user)
    listResult = callGAPIpages(service=gmail.users().messages(), function=u'list', items=u'messages', page_message=page_message,
                               userId=u'me', q=query, includeSpamTrash=False)
    move_count = len(listResult)
    if not doIt:
      print u'would try to mark as spam %s messages for user %s (max %s)\n' % (move_count, user, maxToProcess)
      continue
    elif move_count > maxToProcess:
      print u'WARNING: refusing to move ANY messages for %s since max_to_move is %s and messages to be moved is %s\n' % (user, maxToProcess, move_count)
      continue
    i = 1
    for move_me in listResult:
      print u' moving message %s for user %s (%s/%s)' % (move_me[u'id'], user, i, move_count)
      i += 1
      callGAPI(service=gmail.users().messages(), function=u'modify',
               id=move_me[u'id'], userId=u'me', body={u'addLabelIds': ['SPAM'], u'removeLabelIds': ['INBOX']})

def doDeleteLabel(users):
  label = sys.argv[5]
  for user in users:
    gmail = buildGAPIServiceObject(u'gmail', act_as=user)
    printGettingMessage(u'Getting all labels for %s...\n' % user)
    labels = callGAPI(service=gmail.users().labels(), function=u'list', userId=user, fields=u'labels(name,id,type)')
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
      got_label = False
      for del_label in labels[u'labels']:
        if label.lower() == del_label[u'name'].lower():
          del_labels.append(del_label)
          got_label = True
          break
      if not got_label:
        print u' Error: no such label for %s' % user
        continue
    del_me_count = len(del_labels)
    i = 1
    dbatch = googleapiclient.http.BatchHttpRequest()
    for del_me in del_labels:
      print u' deleting label %s (%s/%s)' % (del_me[u'name'], i, del_me_count)
      i += 1
      dbatch.add(gmail.users().labels().delete(userId=user, id=del_me[u'id']), callback=gmail_del_result)
      if len(dbatch._order) == 10:
        dbatch.execute()
        dbatch = googleapiclient.http.BatchHttpRequest()
    if len(dbatch._order) > 0:
      dbatch.execute()

def gmail_del_result(request_id, response, exception):
  if exception is not None:
    print exception

def showLabels(users):
  i = 5
  show_system = True
  while i < len(sys.argv):
    if sys.argv[i].lower().replace(u'_', u'') == u'onlyuser':
      show_system = False
      i += 1
    else:
      print u'Error: %s is not a valid argument' % sys.argv[i]
      sys.exit(3)
  for user in users:
    gmail = buildGAPIServiceObject(u'gmail', act_as=user)
    labels = callGAPI(service=gmail.users().labels(), function=u'list', userId=user)
    for label in labels[u'labels']:
      if label[u'type'] == u'system' and not show_system:
        continue
      print convertUTF8(label[u'name'])
      for a_key in label.keys():
        if a_key == u'name':
          continue
        print u' %s: %s' % (a_key, label[a_key])
      print u''

def showGmailProfile(users):
  todrive = False
  i = 6
  while i < len(sys.argv):
    if sys.argv[i].lower() == u'todrive':
      todrive = True
      i += 1
    else:
      print u'Error %s is not a valid argument for gam ... show gmailprofiles.'
      sys.exit(1)
  profiles = [{}]
  for user in users:
    printGettingMessage('Getting Gmail profile for %s\n' % user)
    gmail = buildGAPIServiceObject(u'gmail', act_as=user, soft_errors=True)
    if not gmail:
      continue
    results = callGAPI(service=gmail.users(), function=u'getProfile', userId=u'me', soft_errors=True)
    for item in results.keys():
      if item not in profiles[0]:
        profiles[0][item] = item
    profiles.append(results)
  output_csv(csv_list=profiles, titles=profiles[0], list_type=u'Gmail Profiles', todrive=todrive)

def updateLabels(users):
  label_name = sys.argv[5]
  body = {}
  i = 6
  while i < len(sys.argv):
    if sys.argv[i].lower() == u'name':
      body[u'name'] = sys.argv[i+1]
      i += 2
    elif sys.argv[i].lower().replace(u'_', '') == u'messagelistvisibility':
      body[u'messageListVisibility'] = sys.argv[i+1].lower()
      if body[u'messageListVisibility'] not in [u'hide', u'show']:
        print 'Error: message_list_visibility should be show or hide, got %s' % sys.argv[i+1]
        sys.exit(3)
      i += 2
    elif sys.argv[i].lower().replace(u' ', '') == u'labellistvisibility':
      if sys.argv[i+1].lower().replace(u'_', u'') == u'showifunread':
        body[u'labelListVisibility'] = u'labelShowIfUnread'
      elif sys.argv[i+1].lower().replace(u'_', u'') == u'show':
        body[u'labelListVisibility'] = u'labelShow'
      elif sys.argv[i+1].lower().replace(u'_', u'') == u'hide':
        body[u'labelListVisibility'] = u'labelHide'
      else:
        print 'Error: label_list_visibility should be hide, show or show_if_unread, got %s' % sys.argv[i+1]
        sys.exit(3)
      i += 2
    else:
      print 'Error: %s is not a valid argument' % sys.argv[i]
      sys.exit(3)
  for user in users:
    gmail = buildGAPIServiceObject(u'gmail', act_as=user)
    labels = callGAPI(service=gmail.users().labels(), function=u'list', userId=user, fields=u'labels(id,name)')
    label_id = None
    for label in labels[u'labels']:
      if label[u'name'].lower() == label_name.lower():
        label_id = label[u'id']
        break
    if not label_id:
      print 'Error: user does not have a label named %s' % label_name
    callGAPI(service=gmail.users().labels(), function=u'patch', soft_errors=True, userId=user, id=label_id, body=body)

def renameLabels(users):
  search = u'^Inbox/(.*)$'
  replace = u'%s'
  merge = False
  i = 5
  while i < len(sys.argv):
    if sys.argv[i].lower() == u'search':
      search = sys.argv[i+1]
    elif sys.argv[i].lower() == u'replace':
      replace = sys.argv[i+1]
    elif sys.argv[i].lower() == u'merge':
      merge = True
    else:
      print u'Error: %s is not a valid argument to rename label'
      sys.exit(3)
    i += 2
  pattern = re.compile(search, re.IGNORECASE)
  for user in users:
    gmail = buildGAPIServiceObject(u'gmail', act_as=user)
    labels = callGAPI(service=gmail.users().labels(), function=u'list', userId=user)
    for label in labels[u'labels']:
      if label[u'type'] == u'system':
        continue
      match_result = re.search(pattern, label[u'name'])
      if match_result != None:
        new_label_name = replace % match_result.groups()
        print u' Renaming "%s" to "%s"' % (label[u'name'], new_label_name)
        try:
          callGAPI(service=gmail.users().labels(), function=u'patch', soft_errors=True, throw_reasons=[u'aborted'],
                   id=label[u'id'], userId=user, body={u'name': new_label_name})
        except googleapiclient.errors.HttpError:
          if merge:
            print u'  Merging %s label to existing %s label' % (label[u'name'], new_label_name)
            messages_to_relabel = callGAPIpages(service=gmail.users().messages(), function=u'list', items=u'messages',
                                                userId=user, q=u'label:"%s"' % (label[u'name']))
            if len(messages_to_relabel) > 0:
              for new_label in labels[u'labels']:
                if new_label[u'name'].lower() == new_label_name.lower():
                  new_label_id = new_label[u'id']
                  body = {u'addLabelIds': [new_label_id]}
                  break
              i = 1
              for message_to_relabel in messages_to_relabel:
                print u'    relabeling message %s (%s/%s)' % (message_to_relabel[u'id'], i, len(messages_to_relabel))
                callGAPI(service=gmail.users().messages(), function=u'modify', userId=user, id=message_to_relabel[u'id'], body=body)
                i += 1
            else:
              print u'   no messages with %s label' % label[u'name']
            print u'   Deleting label %s' % label[u'name']
            callGAPI(service=gmail.users().labels(), function=u'delete', id=label[u'id'], userId=user)
          else:
            print u'  Error: looks like %s already exists, not renaming. Use the "merge" argument to merge the labels' % new_label_name

def doFilter(users):
  i = 4 # filter arguments start here
  from_ = to = subject = has_the_word = does_not_have_the_word = has_attachment = label = should_mark_as_read = should_archive = should_star = forward_to = should_trash = should_not_spam = None
  haveCondition = False
  while sys.argv[i].lower() in [u'from', u'to', u'subject', u'haswords', u'nowords', u'musthaveattachment']:
    if sys.argv[i].lower() == u'from':
      from_ = sys.argv[i+1]
      i += 2
      haveCondition = True
    elif sys.argv[i].lower() == u'to':
      to = sys.argv[i+1]
      i += 2
      haveCondition = True
    elif sys.argv[i].lower() == u'subject':
      subject = sys.argv[i+1]
      i += 2
      haveCondition = True
    elif sys.argv[i].lower() == u'haswords':
      has_the_word = sys.argv[i+1]
      i += 2
      haveCondition = True
    elif sys.argv[i].lower() == u'nowords':
      does_not_have_the_word = sys.argv[i+1]
      i += 2
      haveCondition = True
    elif sys.argv[i].lower() == u'musthaveattachment':
      has_attachment = True
      i += 1
      haveCondition = True
  if not haveCondition:
    showUsage()
    sys.exit(2)
  haveAction = False
  while i < len(sys.argv):
    if sys.argv[i].lower() == u'label':
      label = sys.argv[i+1]
      i += 2
      haveAction = True
    elif sys.argv[i].lower() == u'markread':
      should_mark_as_read = True
      i += 1
      haveAction = True
    elif sys.argv[i].lower() == u'archive':
      should_archive = True
      i += 1
      haveAction = True
    elif sys.argv[i].lower() == u'star':
      should_star = True
      i += 1
      haveAction = True
    elif sys.argv[i].lower() == u'forward':
      forward_to = sys.argv[i+1]
      i += 2
      haveAction = True
    elif sys.argv[i].lower() == u'trash':
      should_trash = True
      i += 1
      haveAction = True
    elif sys.argv[i].lower() == u'neverspam':
      should_not_spam = True
      i += 1
      haveAction = True
    else:
      showUsage()
      sys.exit(2)
  if not haveAction:
    showUsage()
    sys.exit(2)
  emailsettings = getEmailSettingsObject()
  count = len(users)
  i = 1
  for user in users:
    if user.find(u'@') > 0:
      emailsettings.domain = user[user.find(u'@')+1:]
      user = user[:user.find(u'@')]
    else:
      emailsettings.domain = GC_Values[GC_DOMAIN] #make sure it's back at default domain
    print u"Creating filter for %s (%s of %s)" % (user+'@'+emailsettings.domain, i, count)
    i += 1
    callGData(service=emailsettings, function=u'CreateFilter', soft_errors=True,
              username=user, from_=from_, to=to, subject=subject, has_the_word=has_the_word, does_not_have_the_word=does_not_have_the_word,
              has_attachment=has_attachment, label=label, should_mark_as_read=should_mark_as_read, should_archive=should_archive,
              should_star=should_star, forward_to=forward_to, should_trash=should_trash, should_not_spam=should_not_spam)

def doForward(users):
  action = forward_to = None
  gotAction = gotForward = False
  if sys.argv[4] in true_values:
    enable = True
  elif sys.argv[4] in false_values:
    enable = False
  else:
    showUsage()
    sys.exit(2)
  i = 5
  while i < len(sys.argv):
    if sys.argv[i].lower() in [u'keep', u'archive', u'delete']:
      action = sys.argv[i].upper()
      i += 1
      gotAction = True
    elif sys.argv[i].lower() == u'confirm':
      i += 1
    elif sys.argv[i].find(u'@') != -1:
      forward_to = sys.argv[i]
      gotForward = True
      i += 1
    else:
      showUsage()
      sys.exit(2)
  if enable and (not gotAction or not gotForward):
    showUsage()
    sys.exit()
  emailsettings = getEmailSettingsObject()
  count = len(users)
  i = 1
  for user in users:
    if user.find(u'@') > 0:
      emailsettings.domain = user[user.find(u'@')+1:]
      user = user[:user.find(u'@')]
    else:
      emailsettings.domain = GC_Values[GC_DOMAIN] #make sure it's back at default domain
    print u"Turning forward %s for %s, emails will be %s (%s of %s)" % (sys.argv[4], user+'@'+emailsettings.domain, action, i, count)
    i += 1
    callGData(service=emailsettings, function=u'UpdateForwarding', soft_errors=True, username=user, enable=enable, action=action, forward_to=forward_to)

def getForward(users):
  emailsettings = getEmailSettingsObject()
  for user in users:
    if user.find(u'@') > 0:
      emailsettings.domain = user[user.find('@')+1:]
      user = user[:user.find(u'@')]
    else:
      emailsettings.domain = GC_Values[GC_DOMAIN]
    forward = callGData(service=emailsettings, function=u'GetForward', soft_errors=True, username=user)
    try:
      print u"User %s:  Forward To:%s  Enabled:%s  Action:%s" % (user+u'@'+emailsettings.domain, forward[u'forwardTo'], forward[u'enable'], forward[u'action'])
    except TypeError:
      pass

def doSignature(users):
  import cgi
  if sys.argv[4].lower() == u'file':
    fp = open(sys.argv[5], 'rb')
    signature = cgi.escape(fp.read().replace(u'\\n', u'&#xA;').replace(u'"', u"'"))
    fp.close()
  else:
    signature = cgi.escape(sys.argv[4]).replace(u'\\n', u'&#xA;').replace(u'"', u"'")
  xmlsig = u'''<?xml version="1.0" encoding="utf-8"?>
<atom:entry xmlns:atom="http://www.w3.org/2005/Atom" xmlns:apps="http://schemas.google.com/apps/2006">
    <apps:property name="signature" value="%s" />
</atom:entry>''' % signature
  emailsettings = getEmailSettingsObject()
  count = len(users)
  i = 1
  for user in users:
    if user.find(u'@') > 0:
      emailsettings.domain = user[user.find(u'@')+1:]
      user = user[:user.find(u'@')]
    else:
      emailsettings.domain = GC_Values[GC_DOMAIN] #make sure it's back at default domain
    print u"Setting Signature for %s (%s of %s)" % (user+u'@'+emailsettings.domain, i, count)
    uri = u'https://apps-apis.google.com/a/feeds/emailsettings/2.0/%s/%s/signature' % (emailsettings.domain, user)
    i += 1
    callGData(service=emailsettings, function=u'Put', soft_errors=True, data=xmlsig, uri=uri)

def getSignature(users):
  emailsettings = getEmailSettingsObject()
  for user in users:
    if user.find(u'@') > 0:
      emailsettings.domain = user[user.find(u'@')+1:]
      user = user[:user.find(u'@')]
    else:
      emailsettings.domain = GC_Values[GC_DOMAIN]
    signature = callGData(service=emailsettings, function=u'GetSignature', soft_errors=True, username=user)
    try:
      sys.stdout.write(u"User %s signature:\n  " % (user+u'@'+emailsettings.domain))
      print u" %s" % signature[u'signature']
    except TypeError:
      pass

def doWebClips(users):
  if sys.argv[4].lower() in true_values:
    enable = True
  elif sys.argv[4].lower() in false_values:
    enable = False
  else:
    showUsage()
    sys.exit(2)
  emailsettings = getEmailSettingsObject()
  count = len(users)
  i = 1
  for user in users:
    if user.find(u'@') > 0:
      emailsettings.domain = user[user.find('@')+1:]
      user = user[:user.find(u'@')]
    else:
      emailsettings.domain = GC_Values[GC_DOMAIN] #make sure it's back at default domain
    print u"Turning Web Clips %s for %s (%s of %s)" % (sys.argv[4], user+u'@'+emailsettings.domain, i, count)
    i += 1
    callGData(service=emailsettings, function=u'UpdateWebClipSettings', soft_errors=True, username=user, enable=enable)

def doVacation(users):
  import cgi
  subject = message = u''
  if sys.argv[4] in true_values:
    enable = u'true'
  elif sys.argv[4] in false_values:
    enable = u'false'
  else:
    showUsage()
    sys.exit(2)
  contacts_only = domain_only = u'false'
  start_date = end_date = None
  i = 5
  while i < len(sys.argv):
    if sys.argv[i].lower() == u'subject':
      subject = sys.argv[i+1]
      i += 2
    elif sys.argv[i].lower() == u'message':
      message = sys.argv[i+1]
      i += 2
    elif sys.argv[i].lower() == u'contactsonly':
      contacts_only = u'true'
      i += 1
    elif sys.argv[i].lower() == u'domainonly':
      domain_only = u'true'
      i += 1
    elif sys.argv[i].lower() == u'startdate':
      start_date = sys.argv[i+1]
      i += 2
    elif sys.argv[i].lower() == u'enddate':
      end_date = sys.argv[i+1]
      i += 2
    elif sys.argv[i].lower() == u'file':
      fp = open(sys.argv[i+1], 'rb')
      message = fp.read()
      fp.close()
      i += 2
    else:
      showUsage()
      sys.exit(2)
  i = 1
  count = len(users)
  emailsettings = getEmailSettingsObject()
  message = cgi.escape(message).replace(u'\\n', u'&#xA;').replace(u'"', u"'")
  vacxml = u'''<?xml version="1.0" encoding="utf-8"?>
<atom:entry xmlns:atom="http://www.w3.org/2005/Atom" xmlns:apps="http://schemas.google.com/apps/2006">
    <apps:property name="enable" value="%s" />''' % enable
  vacxml += u'''<apps:property name="subject" value="%s" />
    <apps:property name="message" value="%s" />
    <apps:property name="contactsOnly" value="%s" />
    <apps:property name="domainOnly" value="%s" />''' % (subject, message, contacts_only, domain_only)
  if start_date != None:
    vacxml += u'''<apps:property name="startDate" value="%s" />''' % start_date
  if end_date != None:
    vacxml += u'''<apps:property name="endDate" value="%s" />''' % end_date
  vacxml += u'</atom:entry>'
  for user in users:
    if user.find(u'@') > 0:
      emailsettings.domain = user[user.find(u'@')+1:]
      user = user[:user.find(u'@')]
    else:
      emailsettings.domain = GC_Values[GC_DOMAIN] #make sure it's back at default domain
    print u"Setting Vacation for %s (%s of %s)" % (user+'@'+emailsettings.domain, i, count)
    uri = u'https://apps-apis.google.com/a/feeds/emailsettings/2.0/%s/%s/vacation' % (emailsettings.domain, user)
    i += 1
    callGData(service=emailsettings, function=u'Put', soft_errors=True, data=vacxml, uri=uri)

def getVacation(users):
  emailsettings = getEmailSettingsObject()
  for user in users:
    if user.find(u'@') > 0:
      emailsettings.domain = user[user.find(u'@')+1:]
      user = user[:user.find(u'@')]
    else:
      emailsettings.domain = GC_Values[GC_DOMAIN]
    vacationsettings = callGData(service=emailsettings, function=u'GetVacation', soft_errors=True, username=user)
    try:
      print u'''User %s
 Enabled: %s
 Contacts Only: %s
 Domain Only: %s
 Subject: %s
 Message: %s
 Start Date: %s
 End Date: %s
''' % (user+u'@'+emailsettings.domain, vacationsettings[u'enable'], vacationsettings[u'contactsOnly'], vacationsettings[u'domainOnly'], vacationsettings[u'subject'],
       vacationsettings[u'message'], vacationsettings[u'startDate'], vacationsettings[u'endDate'])
    except TypeError:
      pass

def doCreateDomain():
  cd = buildGAPIObject(u'directory')
  domain_name = sys.argv[3]
  domain_type = sys.argv[4].upper()
  if domain_type.replace(u'_', '') in [u'ALIAS', u'MIRROR', u'DOMAINALIAS', u'ALIAS_DOMAIN']:
    domain_type = u'DOMAIN_ALIAS'
  elif domain_type.replace(u'_', '') in [u'SECONDARY', u'SEPARATE', u'MULTIDOMAIN', u'MULTI']:
    domain_type = u'MULTI_DOMAIN'
  elif domain_type.replace(u'_', '') in [u'PRIMARY', u'PRIMARYDOMAIN', u'HOME']:
    domain_type = u'PRIMARY'
  elif domain_type != u'UNKNOWN':
    print u'Error: domain type should be alias, secondary, primary or unknown. Got %s' % domain_type
    sys.exit(4)
  body = {u'domain_name': domain_name, u'domain_type': domain_type}
  callGAPI(service=cd.domains(), function=u'insert', customerId=GC_Values[GC_CUSTOMER_ID], body=body)
  print u'Added domain %s' % domain_name

def doDelSchema():
  cd = buildGAPIObject(u'directory')
  schemaKey = sys.argv[3]
  callGAPI(service=cd.schemas(), function=u'delete', customerId=GC_Values[GC_CUSTOMER_ID], schemaKey=schemaKey)
  print u'Deleted schema %s' % schemaKey

def doCreateOrUpdateUserSchema():
  cd = buildGAPIObject(u'directory')
  schemaName = sys.argv[3]
  body = {u'schemaName': schemaName, u'fields': []}
  i = 4
  while i < len(sys.argv):
    if sys.argv[i] in [u'field']:
      a_field = {u'fieldName': sys.argv[i+1]}
      i += 2
      while True:
        if sys.argv[i].lower() in [u'type']:
          a_field[u'fieldType'] = sys.argv[i+1].upper()
          if a_field[u'fieldType'] not in [u'BOOL', u'DOUBLE', u'EMAIL', u'INT64', u'PHONE', u'STRING']:
            print 'Error: type must be bool, double, email, int64, phone or string. Got %s' % a_field[u'fieldType']
            sys.exit(3)
          i += 2
        elif sys.argv[i].lower() in [u'multivalued']:
          a_field[u'multiValued'] = True
          i += 1
        elif sys.argv[i].lower() in [u'indexed']:
          a_field[u'indexed'] = True
          i += 1
        elif sys.argv[i].lower() in [u'restricted']:
          a_field[u'readAccessType'] = u'ADMINS_AND_SELF'
          i += 1
        elif sys.argv[i].lower() in [u'range']:
          a_field[u'numericIndexingSpec'] = {u'minValue': sys.argv[i+1], u'maxValue': sys.argv[i+2]}
          i += 3
        elif sys.argv[i].lower() in [u'endfield']:
          body[u'fields'].append(a_field)
          i += 1
          break
        else:
          print 'Error: %s is not a valid argument to gam create schema' % sys.argv[i]
          sys.exit(4)
  if sys.argv[1].lower() == u'create':
    result = callGAPI(service=cd.schemas(), function=u'insert', customerId=GC_Values[GC_CUSTOMER_ID], body=body)
    print 'Created user schema %s' % result[u'schemaName']
  elif sys.argv[1].lower() == u'update':
    result = callGAPI(service=cd.schemas(), function=u'update', customerId=GC_Values[GC_CUSTOMER_ID], body=body, schemaKey=schemaName)
    print 'Updated user schema %s' % result[u'schemaName']

def doPrintUserSchemas():
  cd = buildGAPIObject(u'directory')
  schemas = callGAPI(service=cd.schemas(), function=u'list', customerId=GC_Values[GC_CUSTOMER_ID])
  if not schemas or u'schemas' not in schemas:
    return
  for schema in schemas[u'schemas']:
    print u'Schema: %s' % schema[u'schemaName']
    for a_key in schema.keys():
      if a_key not in [u'schemaName', u'fields', u'etag', u'kind']:
        print '%s: %s' % (a_key, schema[a_key])
    print
    for field in schema[u'fields']:
      print u' Field: %s' % field[u'fieldName']
      for a_key in field.keys():
        if a_key not in [u'fieldName', u'kind', u'etag']:
          print '  %s: %s' % (a_key, field[a_key])
      print
    print

def doGetUserSchema():
  cd = buildGAPIObject(u'directory')
  schemaKey = sys.argv[3]
  schema = callGAPI(service=cd.schemas(), function=u'get', customerId=GC_Values[GC_CUSTOMER_ID], schemaKey=schemaKey)
  print u'Schema: %s' % schema[u'schemaName']
  for a_key in schema.keys():
    if a_key not in [u'schemaName', u'fields', u'etag', u'kind']:
      print '%s: %s' % (a_key, schema[a_key])
  print
  for field in schema[u'fields']:
    print u' Field: %s' % field[u'fieldName']
    for a_key in field.keys():
      if a_key not in [u'fieldName', u'kind', u'etag']:
        print '  %s: %s' % (a_key, field[a_key])
    print

def clearBodyList(body, itemName):
  if itemName in body:
    del body[itemName]
  body.setdefault(itemName, None)

def appendItemToBodyList(body, itemName, itemValue):
  if (itemName in body) and (body[itemName] == None):
    del body[itemName]
  body.setdefault(itemName, [])
  body[itemName].append(itemValue)

def doCreateUser():
  cd = buildGAPIObject(u'directory')
  body = dict()
  body[u'name'] = dict()
  body[u'primaryEmail'] = sys.argv[3]
  if body[u'primaryEmail'].find(u'@') == -1:
    body[u'primaryEmail'] = u'%s@%s' % (body[u'primaryEmail'], GC_Values[GC_DOMAIN])
  gotFirstName = gotLastName = do_admin = False
  need_to_hash_password = need_password = True
  i = 4
  while i < len(sys.argv):
    if sys.argv[i].lower() == u'firstname':
      body[u'name'][u'givenName'] = sys.argv[i+1]
      gotFirstName = True
      i += 2
    elif sys.argv[i].lower() == u'lastname':
      body[u'name'][u'familyName'] = sys.argv[i+1]
      gotLastName = True
      i += 2
    elif sys.argv[i].lower() == u'password':
      body[u'password'] = sys.argv[i+1]
      need_password = False
      i += 2
    elif sys.argv[i].lower() == u'suspended':
      if sys.argv[i+1].lower() in true_values:
        body[u'suspended'] = True
      elif sys.argv[i+1].lower() in false_values:
        body[u'suspended'] = False
      else:
        print u'Error: suspended should be on or off, not %s' % sys.argv[i+1]
        sys.exit(5)
      i += 2
    elif sys.argv[i].lower() == u'gal':
      if sys.argv[i+1].lower() in true_values:
        body[u'includeInGlobalAddressList'] = True
      elif sys.argv[i+1].lower() in false_values:
        body[u'includeInGlobalAddressList'] = False
      else:
        print u'Error: gal should be on or off, not %s' % sys.argv[i+1]
        sys.exit(5)
      i += 2
    elif sys.argv[i].lower() in [u'sha', u'sha1', u'sha-1']:
      body[u'hashFunction'] = u'SHA-1'
      need_to_hash_password = False
      i += 1
    elif sys.argv[i].lower() == u'md5':
      body[u'hashFunction'] = u'MD5'
      need_to_hash_password = False
      i += 1
    elif sys.argv[i].lower() == u'crypt':
      body[u'hashFunction'] = u'crypt'
      need_to_hash_password = False
      i += 1
    elif sys.argv[i].lower() == u'nohash':
      need_to_hash_password = False
      i += 1
    elif sys.argv[i].lower() == u'changepassword':
      if sys.argv[i+1] in true_values:
        body[u'changePasswordAtNextLogin'] = True
      elif sys.argv[i+1] in false_values:
        body[u'changePasswordAtNextLogin'] = False
      else:
        print u'Error: changepassword should be on or off, not %s' % sys.argv[i+1]
        sys.exit(5)
      i += 2
    elif sys.argv[i].lower() == u'ipwhitelisted':
      if sys.argv[i+1] in true_values:
        body[u'ipWhitelisted'] = True
      elif sys.argv[i+1] in false_values:
        body[u'ipWhitelisted'] = False
      else:
        print u'Error: ipwhitelisted should be on or off, not %s' % sys.argv[i+1]
      i += 2
    elif sys.argv[i].lower() == u'admin':
      do_admin = True
      if sys.argv[i+1].lower() in true_values:
        admin_body = {u'status': True}
      elif sys.argv[i+1].lower() in false_values:
        admin_body = {u'status': False}
      else:
        print u'Error: admin should be on or off, not %s' % sys.argv[i+1]
        sys.exit(5)
      i += 2
    elif sys.argv[i].lower() == u'agreedtoterms':
      if sys.argv[i+1] in true_values:
        body[u'agreedToTerms'] = True
      elif sys.argv[i+1] in false_values:
        body[u'agreedToTerms'] = False
      else:
        print u'Error: agreedtoterms should be on or off, not %s' % sys.argv[i+1]
        sys.exit(5)
      i += 2
    elif sys.argv[i].lower() in [u'org', u'ou']:
      org = sys.argv[i+1]
      if org[0] != u'/':
        org = u'/%s' % org
      body[u'orgUnitPath'] = org
      i += 2
    elif sys.argv[i].lower() == u'im':
      i += 1
      if sys.argv[i].lower() == u'clear':
        i += 1
        clearBodyList(body, u'ims')
        continue
      im = dict()
      if sys.argv[i].lower() != u'type':
        print u'Error: wrong format for account im details. Expected type got %s' % sys.argv[i]
        sys.exit(6)
      i += 1
      im[u'type'] = sys.argv[i].lower()
      if im[u'type'] not in [u'custom', u'home', u'other', u'work']:
        print u'Error: type should be custom, home, other or work. Got %s' % im[u'type']
        sys.exit(7)
      if im[u'type'] == u'custom':
        i += 1
        im[u'customType'] = sys.argv[i]
      i += 1
      if sys.argv[i].lower() != u'protocol':
        print u'Error: wrong format for account details. Expected protocol got %s' % sys.argv[i]
        sys.exit(8)
      i += 1
      im[u'protocol'] = sys.argv[i].lower()
      if im[u'protocol'] not in [u'custom_protocol', u'aim', u'gtalk', u'icq', u'jabber', u'msn', u'net_meeting', u'qq', u'skype', u'yahoo']:
        print u'Error: protocol should be custom_protocol, aim, gtalk, icq, jabber, msn, net_meeting, qq, skype or yahoo. Got %s' % im[u'protocol']
      if im[u'protocol'] == u'custom_protocol':
        i += 1
        im[u'customProtocol'] = sys.argv[i]
      i += 1
      if sys.argv[i].lower() == u'primary':
        im[u'primary'] = True
        i += 1
      im[u'im'] = sys.argv[i]
      i += 1
      appendItemToBodyList(body, u'ims', im)
    elif sys.argv[i].lower() == u'address':
      i += 1
      if sys.argv[i].lower() == u'clear':
        i += 1
        clearBodyList(body, u'addresses')
        continue
      address = dict()
      if sys.argv[i].lower() != u'type':
        print u'Error: wrong format for account address details. Expected type got %s' % sys.argv[i]
        sys.exit(9)
      i += 1
      address[u'type'] = sys.argv[i].lower()
      if address[u'type'] not in [u'custom', u'home', u'other', u'work']:
        print u'Error: wrong type should be custom, home, other or work. Got %s' % address[u'type']
        sys.exit(10)
      if address[u'type'] == u'custom':
        i += 1
        address[u'customType'] = sys.argv[i]
      i += 1
      if sys.argv[i].lower() == u'unstructured':
        i += 1
        address[u'sourceIsStructured'] = False
        address[u'formatted'] = sys.argv[i]
        i += 1
      while True:
        argument = sys.argv[i].lower()
        if argument == u'pobox':
          address[u'poBox'] = sys.argv[i+1]
          i += 2
        elif argument == u'extendedaddress':
          address[u'extendedAddress'] = sys.argv[i+1]
          i += 2
        elif argument == u'streetaddress':
          address[u'streetAddress'] = sys.argv[i+1]
          i += 2
        elif argument == u'locality':
          address[u'locality'] = sys.argv[i+1]
          i += 2
        elif argument == u'region':
          address[u'region'] = sys.argv[i+1]
          i += 2
        elif argument == u'postalcode':
          address[u'postalCode'] = sys.argv[i+1]
          i += 2
        elif argument == u'country':
          address[u'country'] = sys.argv[i+1]
          i += 2
        elif argument == u'countrycode':
          address[u'countryCode'] = sys.argv[i+1]
          i += 2
        elif argument == u'notprimary':
          i += 1
          break
        elif argument == u'primary':
          address[u'primary'] = True
          i += 1
          break
      appendItemToBodyList(body, u'addresses', address)
    elif sys.argv[i].lower() == u'organization':
      i += 1
      if sys.argv[i].lower() == u'clear':
        i += 1
        clearBodyList(body, u'organizations')
        continue
      organization = dict()
      while True:
        argument = sys.argv[i].lower()
        if argument == u'name':
          organization[u'name'] = sys.argv[i+1]
          i += 2
        elif argument == u'title':
          organization[u'title'] = sys.argv[i+1]
          i += 2
        elif argument == u'customtype':
          organization[u'customType'] = sys.argv[i+1]
          i += 2
        elif argument == u'type':
          organization[u'type'] = sys.argv[i+1].lower()
          if organization[u'type'] not in [u'domain_only', u'school', u'unknown', u'work']:
            print u'Error: organization type must be domain_only, school, unknown or work. Got %s' % organization[u'type']
            sys.exit(11)
          i += 2
        elif argument == u'department':
          organization[u'department'] = sys.argv[i+1]
          i += 2
        elif argument == u'symbol':
          organization[u'symbol'] = sys.argv[i+1]
          i += 2
        elif argument == u'costcenter':
          organization[u'costCenter'] = sys.argv[i+1]
          i += 2
        elif argument == u'location':
          organization[u'location'] = sys.argv[i+1]
          i += 2
        elif argument == u'description':
          organization[u'description'] = sys.argv[i+1]
          i += 2
        elif argument == u'domain':
          organization[u'domain'] = sys.argv[i+1]
          i += 2
        elif argument == u'notprimary':
          i += 1
          break
        elif argument == u'primary':
          organization[u'primary'] = True
          i += 1
          break
      appendItemToBodyList(body, u'organizations', organization)
    elif sys.argv[i].lower() == u'phone':
      i += 1
      if sys.argv[i].lower() == u'clear':
        i += 1
        clearBodyList(body, u'phones')
        continue
      phone = dict()
      while True:
        argument = sys.argv[i].lower()
        if argument == u'value':
          phone[u'value'] = sys.argv[i+1]
          i += 2
        elif argument == u'type':
          phone[u'type'] = sys.argv[i+1].lower()
          if phone[u'type'] not in [u'assistant', u'callback', u'car', u'company_main', u'custom', u'grand_central', u'home', u'home_fax', u'isdn', u'main', u'mobile', u'other', u'other_fax', u'pager', u'radio', u'telex', u'tty_tdd', u'work', u'work_fax', u'work_mobile', u'work_pager']:
            print u'Error: phone type must be assistant, callback, car, company_main, custom, grand_central, home, home_fax, isdn, main, mobile, other, other_fax, pager, radio, telex, tty_tdd, work, work_fax, work_mobile, work_pager. Got %s' % phone[u'type']
            sys.exit(12)
          i += 2
          if phone[u'type'] == u'custom':
            phone[u'customType'] = sys.argv[i]
            i += 1
        elif argument == u'notprimary':
          i += 1
          break
        elif argument == u'primary':
          phone[u'primary'] = True
          i += 1
          break
      appendItemToBodyList(body, u'phones', phone)
    elif sys.argv[i].lower() == u'relation':
      i += 1
      if sys.argv[i].lower() == u'clear':
        i += 1
        clearBodyList(body, u'relations')
        continue
      relation = dict()
      relation[u'type'] = sys.argv[i]
      if relation[u'type'].lower() not in [u'mother', u'father', u'sister', u'brother', u'manager', u'assistant', u'partner']:
        relation[u'type'] = u'custom'
        relation[u'customType'] = sys.argv[i]
      i += 1
      relation[u'value'] = sys.argv[i]
      i += 1
      appendItemToBodyList(body, u'relations', relation)
    elif sys.argv[i].lower() == u'externalid':
      i += 1
      if sys.argv[i].lower() == u'clear':
        i += 1
        clearBodyList(body, u'externalIds')
        continue
      externalid = dict()
      externalid[u'type'] = sys.argv[i]
      if externalid[u'type'].lower() not in [u'account', u'customer', u'network', u'organization']:
        externalid[u'type'] = u'custom'
        externalid[u'customType'] = sys.argv[i]
      i += 1
      externalid[u'value'] = sys.argv[i]
      i += 1
      appendItemToBodyList(body, u'externalIds', externalid)
    elif sys.argv[i].lower() == u'website':
      i += 1
      if sys.argv[i].lower() == u'clear':
        i += 1
        clearBodyList(body, u'websites')
        continue
      website = dict()
      website[u'type'] = sys.argv[i]
      if website[u'type'].lower() not in [u'home_page', u'blog', u'profile', u'work', u'home', u'other', u'ftp', u'reservations', u'app_install_page']:
        website[u'type'] = u'custom'
        website[u'customType'] = sys.argv[i]
      i += 1
      website[u'value'] = sys.argv[i]
      i += 1
      appendItemToBodyList(body, u'websites', website)
#    else:
#      showUsage()
#      sys.exit(2)
    else:
      if u'customSchemas' not in body:
        body[u'customSchemas'] = {}
      try:
        (schemaName, fieldName) = sys.argv[i].split(u'.')
      except ValueError:
        print 'Error: %s is not a valid create user argument or custom schema name.' % sys.argv[i]
        sys.exit(3)
      field_value = sys.argv[i+1]
      is_multivalue = False
      if field_value.lower() in [u'multivalue', u'multivalued', u'value']:
        is_multivalue = True
        field_value = sys.argv[i+2]
      if schemaName not in body[u'customSchemas']:
        body[u'customSchemas'][schemaName] = {}
      if is_multivalue:
        if fieldName not in body[u'customSchemas'][schemaName]:
          body[u'customSchemas'][schemaName][fieldName] = []
        body[u'customSchemas'][schemaName][fieldName].append({u'value': field_value})
      else:
        body[u'customSchemas'][schemaName][fieldName] = field_value
      i += 2
      if is_multivalue:
        i += 1
  if not gotFirstName:
    body[u'name'][u'givenName'] = u'Unknown'
  if not gotLastName:
    body[u'name'][u'familyName'] = u'Unknown'
  if need_password:
    body[u'password'] = u''.join(random.sample(u'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789~`!@#$%^&*()-=_+:;"\'{}[]\\|', 25))
  if need_to_hash_password:
    body[u'password'] = gen_sha512_hash(body[u'password'])
    body[u'hashFunction'] = u'crypt'
  print u"Creating account for %s" % body[u'primaryEmail']
  callGAPI(service=cd.users(), function='insert', body=body, fields=u'primaryEmail')
  if do_admin:
    print u' Changing admin status for %s to %s' % (body[u'primaryEmail'], admin_body[u'status'])
    callGAPI(service=cd.users(), function=u'makeAdmin', userKey=body[u'primaryEmail'], body=admin_body)

def doCreateGroup():
  use_gs_api = False
  cd = buildGAPIObject(u'directory')
  body = dict()
  body[u'email'] = sys.argv[3]
  if body[u'email'].find(u'@') == -1:
    body[u'email'] = u'%s@%s' % (body[u'email'], GC_Values[GC_DOMAIN])
  got_name = False
  i = 4
  gs_body = dict()
  while i < len(sys.argv):
    if sys.argv[i].lower() == u'name':
      body[u'name'] = sys.argv[i+1]
      got_name = True
      i += 2
    elif sys.argv[i].lower() == u'description':
      body[u'description'] = sys.argv[i+1]
      i += 2
    else:
      value = sys.argv[i+1]
      gs_object = buildDiscoveryObject(u'groupssettings')
      matches_gs_setting = False
      for (attrib, params) in gs_object[u'schemas'][u'Groups'][u'properties'].items():
        if attrib in [u'kind', u'etag', u'email', u'name', u'description']:
          continue
        if sys.argv[i].lower().replace(u'_', u'') == attrib.lower():
          matches_gs_setting = True
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
              print u'Error: %s must be a number ending with M (megabytes), K (kilobytes) or nothing (bytes). Got %s' % value
              sys.exit(9)
          elif params[u'type'] == u'string':
            if params[u'description'].find(value.upper()) != -1: # ugly hack because API wants some values uppercased.
              value = value.upper()
            elif value.lower() in true_values:
              value = u'true'
            elif value.lower() in false_values:
              value = u'false'
          break
      if not matches_gs_setting:
        print u'ERROR: %s is not a valid argument for "gam create group..."' % sys.argv[i]
        sys.exit(9)
      gs_body[attrib] = value
      use_gs_api = True
      i += 2
  if not got_name:
    body[u'name'] = body[u'email']
  print u"Creating group %s" % body[u'email']
  callGAPI(service=cd.groups(), function=u'insert', body=body, fields=u'email')
  if use_gs_api:
    gs = buildGAPIObject(u'groupssettings')
    callGAPI(service=gs.groups(), function=u'patch', retry_reasons=[u'serviceLimit'], groupUniqueId=body[u'email'], body=gs_body)

def doCreateAlias():
  cd = buildGAPIObject(u'directory')
  body = dict()
  body[u'alias'] = sys.argv[3]
  if body[u'alias'].find(u'@') == -1:
    body[u'alias'] = u'%s@%s' % (body[u'alias'], GC_Values[GC_DOMAIN])
  target_type = sys.argv[4].lower()
  if target_type not in [u'user', u'group', u'target']:
    print u'Error: type of target should be user or group. Got %s' % target_type
    sys.exit(3)
  targetKey = sys.argv[5]
  if targetKey.find(u'@') == -1:
    targetKey = u'%s@%s' % (targetKey, GC_Values[GC_DOMAIN])
  print u'Creating alias %s for %s %s' % (body[u'alias'], target_type, targetKey)
  if target_type == u'user':
    callGAPI(service=cd.users().aliases(), function=u'insert', userKey=targetKey, body=body)
  elif target_type == u'group':
    callGAPI(service=cd.groups().aliases(), function=u'insert', groupKey=targetKey, body=body)
  elif target_type == u'target':
    try:
      callGAPI(service=cd.users().aliases(), function=u'insert', throw_reasons=[u'invalid'], userKey=targetKey, body=body)
    except googleapiclient.errors.HttpError:
      callGAPI(service=cd.groups().aliases(), function=u'insert', groupKey=targetKey, body=body)

def doCreateOrg():
  cd = buildGAPIObject(u'directory')
  body = dict()
  body[u'name'] = sys.argv[3]
  if body[u'name'][0] == u'/':
    body[u'name'] = body[u'name'][1:]
  i = 4
  body[u'parentOrgUnitPath'] = u'/'
  while i < len(sys.argv):
    if sys.argv[i].lower() == u'description':
      body[u'description'] = sys.argv[i+1]
      i += 2
    elif sys.argv[i].lower() == u'parent':
      body[u'parentOrgUnitPath'] = sys.argv[i+1]
      i += 2
    elif sys.argv[i].lower() == u'noinherit':
      body[u'blockInheritance'] = True
      i += 1
  callGAPI(service=cd.orgunits(), function=u'insert', customerId=GC_Values[GC_CUSTOMER_ID], body=body)

def doCreateResource():
  resId = sys.argv[3]
  common_name = sys.argv[4]
  description = None
  resType = None
  i = 5
  while i < len(sys.argv):
    if sys.argv[i].lower() == u'description':
      description = sys.argv[i+1]
      i += 2
    elif sys.argv[i].lower() == u'resType':
      resType = sys.argv[i+1]
      i += 2
  rescal = getResCalObject()
  callGData(service=rescal, function=u'CreateResourceCalendar', id=resId, common_name=common_name, description=description, type=resType)

def doUpdateUser(users):
  cd = buildGAPIObject(u'directory')
  body = dict()
  gotPassword = isMD5 = isSHA1 = isCrypt = False
  is_admin = nohash = None
  if sys.argv[1].lower() == u'update':
    i = 4
  else:
    i = 5
  do_update_user = False
  do_admin_user = False
  while i < len(sys.argv):
    if sys.argv[i].lower() == u'firstname':
      do_update_user = True
      if u'name' not in body:
        body[u'name'] = dict()
      body[u'name'][u'givenName'] = sys.argv[i+1]
      i += 2
    elif sys.argv[i].lower() == u'lastname':
      do_update_user = True
      if u'name' not in body:
        body[u'name'] = dict()
      body[u'name'][u'familyName'] = sys.argv[i+1]
      i += 2
    elif sys.argv[i].lower() in [u'username', u'email']:
      do_update_user = True
      body[u'primaryEmail'] = sys.argv[i+1]
      if body[u'primaryEmail'].find(u'@') == -1:
        body[u'primaryEmail'] = u'%s@%s' % (body[u'primaryEmail'], GC_Values[GC_DOMAIN])
      i += 2
    elif sys.argv[i].lower() == u'password':
      do_update_user = True
      body[u'password'] = sys.argv[i+1]
      if body[u'password'].lower() == u'random':
        body[u'password'] = ''.join(random.sample(u'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789~`!@#$%^&*()-=_+:;"\'{}[]\\|', 50))
      i += 2
      gotPassword = True
    elif sys.argv[i].lower() == u'admin':
      do_admin_user = True
      if sys.argv[i+1].lower() in true_values:
        is_admin = True
      elif sys.argv[i+1].lower() in false_values:
        is_admin = False
      i += 2
    elif sys.argv[i].lower() == u'suspended':
      do_update_user = True
      if sys.argv[i+1].lower() in true_values:
        body[u'suspended'] = True
      elif sys.argv[i+1].lower() in false_values:
        body[u'suspended'] = False
      i += 2
    elif sys.argv[i].lower() == u'gal':
      do_update_user = True
      if sys.argv[i+1].lower() in true_values:
        body[u'includeInGlobalAddressList'] = True
      elif sys.argv[i+1].lower() in false_values:
        body[u'includeInGlobalAddressList'] = False
      else:
        print u'Error: gal should be on or off, not %s' % sys.argv[i+1]
        sys.exit(5)
      i += 2
    elif sys.argv[i].lower() == u'ipwhitelisted':
      do_update_user = True
      if sys.argv[i+1].lower() in true_values:
        body[u'ipWhitelisted'] = True
      elif sys.argv[i+1].lower() in false_values:
        body[u'ipWhitelisted'] = False
      i += 2
    elif sys.argv[i].lower() in [u'sha', u'sha1', u'sha-1']:
      do_update_user = True
      body[u'hashFunction'] = u'SHA-1'
      i += 1
      isSHA1 = True
    elif sys.argv[i].lower() == u'md5':
      do_update_user = True
      body[u'hashFunction'] = u'MD5'
      i += 1
      isMD5 = True
    elif sys.argv[i].lower() == u'crypt':
      do_update_user = True
      body[u'hashFunction'] = u'crypt'
      i += 1
      isCrypt = True
    elif sys.argv[i].lower() == u'nohash':
      nohash = True
      i += 1
    elif sys.argv[i].lower() == u'changepassword':
      do_update_user = True
      if sys.argv[i+1].lower() in true_values:
        body[u'changePasswordAtNextLogin'] = True
      elif sys.argv[i+1].lower() in false_values:
        body[u'changePasswordAtNextLogin'] = False
      i += 2
    elif sys.argv[i].lower() in ['org', u'ou']:
      do_update_user = True
      body[u'orgUnitPath'] = sys.argv[i+1]
      if body[u'orgUnitPath'][0] != u'/':
        body[u'orgUnitPath'] = u'/'+body[u'orgUnitPath']
      i += 2
    elif sys.argv[i].lower() == u'agreedtoterms':
      do_update_user = True
      if sys.argv[i+1].lower() in true_values:
        body[u'agreedToTerms'] = True
      elif sys.argv[i+1].lower() in false_values:
        body[u'agreedToTerms'] = False
      i += 2
    elif sys.argv[i].lower() == u'customerid':
      do_update_user = True
      body[u'customerId'] = sys.argv[i+1]
      i += 2
    elif sys.argv[i].lower() == u'im':
      i += 1
      do_update_user = True
      if sys.argv[i].lower() == u'clear':
        i += 1
        clearBodyList(body, u'ims')
        continue
      im = dict()
      if sys.argv[i].lower() != u'type':
        print u'Error: wrong format for account im details. Expected type got %s' % sys.argv[i]
        sys.exit(6)
      i += 1
      im[u'type'] = sys.argv[i].lower()
      if im[u'type'] not in [u'custom', u'home', u'other', u'work']:
        print u'Error: type should be custom, home, other or work. Got %s' % im[u'type']
        sys.exit(7)
      if im[u'type'] == u'custom':
        i += 1
        im[u'customType'] = sys.argv[i]
      i += 1
      if sys.argv[i].lower() != u'protocol':
        print u'Error: wrong format for account details. Expected protocol got %s' % sys.argv[i]
        sys.exit(8)
      i += 1
      im[u'protocol'] = sys.argv[i].lower()
      if im[u'protocol'] not in [u'custom_protocol', u'aim', u'gtalk', u'icq', u'jabber', u'msn', u'net_meeting', u'qq', u'skype', u'yahoo']:
        print u'Error: protocol should be custom_protocol, aim, gtalk, icq, jabber, msn, net_meeting, qq, skype or yahoo. Got %s' % im[u'protocol']
      if im[u'protocol'] == u'custom_protocol':
        i += 1
        im[u'customProtocol'] = sys.argv[i]
      i += 1
      if sys.argv[i].lower() == u'primary':
        im[u'primary'] = True
        i += 1
      im[u'im'] = sys.argv[i]
      i += 1
      appendItemToBodyList(body, u'ims', im)
    elif sys.argv[i].lower() == u'address':
      i += 1
      do_update_user = True
      if sys.argv[i].lower() == u'clear':
        i += 1
        clearBodyList(body, u'addresses')
        continue
      address = dict()
      if sys.argv[i].lower() != u'type':
        print u'Error: wrong format for account address details. Expected type got %s' % sys.argv[i]
        sys.exit(9)
      i += 1
      address[u'type'] = sys.argv[i].lower()
      if address[u'type'] not in [u'custom', u'home', u'other', u'work']:
        print u'Error: wrong type should be custom, home, other or work. Got %s' % address[u'type']
        sys.exit(10)
      if address[u'type'] == u'custom':
        i += 1
        address[u'customType'] = sys.argv[i]
      i += 1
      if sys.argv[i].lower() == u'unstructured':
        i += 1
        address[u'sourceIsStructured'] = False
        address[u'formatted'] = sys.argv[i]
        i += 1
      while True:
        argument = sys.argv[i].lower()
        if argument == u'pobox':
          address[u'poBox'] = sys.argv[i+1]
          i += 2
        elif argument == u'extendedaddress':
          address[u'extendedAddress'] = sys.argv[i+1]
          i += 2
        elif argument == u'streetaddress':
          address[u'streetAddress'] = sys.argv[i+1]
          i += 2
        elif argument == u'locality':
          address[u'locality'] = sys.argv[i+1]
          i += 2
        elif argument == u'region':
          address[u'region'] = sys.argv[i+1]
          i += 2
        elif argument == u'postalcode':
          address[u'postalCode'] = sys.argv[i+1]
          i += 2
        elif argument == u'country':
          address[u'country'] = sys.argv[i+1]
          i += 2
        elif argument == u'countrycode':
          address[u'countryCode'] = sys.argv[i+1]
          i += 2
        elif argument == u'notprimary':
          i += 1
          break
        elif argument == u'primary':
          address[u'primary'] = True
          i += 1
          break
      appendItemToBodyList(body, u'addresses', address)
    elif sys.argv[i].lower() == u'organization':
      i += 1
      do_update_user = True
      if sys.argv[i].lower() == u'clear':
        i += 1
        clearBodyList(body, u'organizations')
        continue
      organization = dict()
      while True:
        argument = sys.argv[i].lower()
        if argument == u'name':
          organization[u'name'] = sys.argv[i+1]
          i += 2
        elif argument == u'title':
          organization[u'title'] = sys.argv[i+1]
          i += 2
        elif argument == u'customtype':
          organization[u'customType'] = sys.argv[i+1]
          i += 2
        elif argument == u'type':
          organization[u'type'] = sys.argv[i+1].lower()
          if organization[u'type'] not in [u'domain_only', u'school', u'unknown', u'work']:
            print u'Error: organization type must be domain_only, school, unknown or work. Got %s' % organization[u'type']
            sys.exit(11)
          i += 2
        elif argument == u'department':
          organization[u'department'] = sys.argv[i+1]
          i += 2
        elif argument == u'symbol':
          organization[u'symbol'] = sys.argv[i+1]
          i += 2
        elif argument == u'costcenter':
          organization[u'costCenter'] = sys.argv[i+1]
          i += 2
        elif argument == u'location':
          organization[u'location'] = sys.argv[i+1]
          i += 2
        elif argument == u'description':
          organization[u'description'] = sys.argv[i+1]
          i += 2
        elif argument == u'domain':
          organization[u'domain'] = sys.argv[i+1]
          i += 2
        elif argument == u'notprimary':
          i += 1
          break
        elif argument == u'primary':
          organization[u'primary'] = True
          i += 1
          break
      appendItemToBodyList(body, u'organizations', organization)
    elif sys.argv[i].lower() == u'phone':
      i += 1
      do_update_user = True
      if sys.argv[i].lower() == u'clear':
        i += 1
        clearBodyList(body, u'phones')
        continue
      phone = dict()
      while True:
        argument = sys.argv[i].lower()
        if argument == u'value':
          phone[u'value'] = sys.argv[i+1]
          i += 2
        elif argument == u'type':
          phone[u'type'] = sys.argv[i+1].lower()
          if phone[u'type'] not in [u'assistant', u'callback', u'car', u'company_main', u'custom', u'grand_central', u'home', u'home_fax', u'isdn', u'main', u'mobile', u'other', u'other_fax', u'pager', u'radio', u'telex', u'tty_tdd', u'work', u'work_fax', u'work_mobile', u'work_pager']:
            print u'Error: phone type must be assistant, callback, car, company_main, custom, grand_central, home, home_fax, isdn, main, mobile, other, other_fax, pager, radio, telex, tty_tdd, work, work_fax, work_mobile, work_pager. Got %s' % phone[u'type']
            sys.exit(12)
          i += 2
          if phone[u'type'] == u'custom':
            phone[u'customType'] = sys.argv[i]
            i += 1
        elif argument == u'notprimary':
          i += 1
          break
        elif argument == u'primary':
          phone[u'primary'] = True
          i += 1
          break
      appendItemToBodyList(body, u'phones', phone)
    elif sys.argv[i].lower() == u'relation':
      i += 1
      do_update_user = True
      if sys.argv[i].lower() == u'clear':
        i += 1
        clearBodyList(body, u'relations')
        continue
      relation = dict()
      relation[u'type'] = sys.argv[i]
      if relation[u'type'].lower() not in [u'mother', u'father', u'sister', u'brother', u'manager', u'assistant', u'partner']:
        relation[u'type'] = u'custom'
        relation[u'customType'] = sys.argv[i]
      i += 1
      relation[u'value'] = sys.argv[i]
      i += 1
      appendItemToBodyList(body, u'relations', relation)
    elif sys.argv[i].lower() == u'otheremail':
      i += 1
      do_update_user = True
      if sys.argv[i].lower() == u'clear':
        i += 1
        clearBodyList(body, u'emails')
        continue
      an_email = dict()
      an_email[u'type'] = sys.argv[i]
      if an_email[u'type'].lower() not in [u'custom', u'home', u'other', u'work']:
        an_email[u'type'] = u'custom'
        an_email[u'customType'] = sys.argv[i]
      i += 1
      an_email[u'address'] = sys.argv[i]
      i += 1
      appendItemToBodyList(body, u'emails', an_email)
    elif sys.argv[i].lower() == u'externalid':
      i += 1
      do_update_user = True
      if sys.argv[i].lower() == u'clear':
        i += 1
        clearBodyList(body, u'externalIds')
        continue
      externalid = dict()
      externalid[u'type'] = sys.argv[i]
      if externalid[u'type'].lower() not in [u'account', u'customer', u'network', u'organization']:
        externalid[u'type'] = u'custom'
        externalid[u'customType'] = sys.argv[i]
      i += 1
      externalid[u'value'] = sys.argv[i]
      i += 1
      appendItemToBodyList(body, u'externalIds', externalid)
    elif sys.argv[i].lower() == u'website':
      i += 1
      do_update_user = True
      if sys.argv[i].lower() == u'clear':
        i += 1
        clearBodyList(body, u'websites')
        continue
      website = dict()
      website[u'type'] = sys.argv[i]
      if website[u'type'].lower() not in [u'home_page', u'blog', u'profile', u'work', u'home', u'other', u'ftp', u'reservations', u'app_install_page']:
        website[u'type'] = u'custom'
        website[u'customType'] = sys.argv[i]
      i += 1
      website[u'value'] = sys.argv[i]
      i += 1
      appendItemToBodyList(body, u'websites', website)
#    else:
#      showUsage()
#      print u''
#      print u'Error: didn\'t expect %s command at position %s' % (sys.argv[i], i)
#      sys.exit(2)
    else:
      do_update_user = True
      if u'customSchemas' not in body:
        body[u'customSchemas'] = {}
      try:
        (schemaName, fieldName) = sys.argv[i].split(u'.')
      except ValueError:
        print u'Error: %s is not a valid user update argument or custom schema name' % sys.argv[i]
        sys.exit(3)
      field_value = sys.argv[i+1]
      is_multivalue = False
      if field_value.lower() == u'multivalue':
        is_multivalue = True
        field_value = sys.argv[i+2]
      if schemaName not in body[u'customSchemas']:
        body[u'customSchemas'][schemaName] = {}
      if is_multivalue:
        if fieldName not in body[u'customSchemas'][schemaName]:
          body[u'customSchemas'][schemaName][fieldName] = []
        body[u'customSchemas'][schemaName][fieldName].append({u'value': field_value})
      else:
        body[u'customSchemas'][schemaName][fieldName] = field_value
      i += 2
      if is_multivalue:
        i += 1
  if gotPassword and not (isSHA1 or isMD5 or isCrypt or nohash):
    body[u'password'] = gen_sha512_hash(body[u'password'])
    body[u'hashFunction'] = u'crypt'
  for user in users:
    if user[:4].lower() == u'uid:':
      user = user[4:]
    elif user.find(u'@') == -1:
      user = u'%s@%s' % (user, GC_Values[GC_DOMAIN])
    if u'primaryEmail' in body and body[u'primaryEmail'][:4].lower() == u'vfe@':
      user_primary = callGAPI(service=cd.users(), function=u'get', userKey=user, fields=u'primaryEmail,id')
      user = user_primary[u'id']
      user_primary = user_primary[u'primaryEmail']
      user_name = user_primary[:user_primary.find(u'@')]
      user_domain = user_primary[user_primary.find(u'@')+1:]
      body[u'primaryEmail'] = u'vfe.%s.%05d@%s' % (user_name, random.randint(1, 99999), user_domain)
      body[u'emails'] = [{u'type': u'custom', u'customType': u'former_employee', u'primary': False, u'address': user_primary}]
    sys.stdout.write(u'updating user %s...\n' % user)
    if do_update_user:
      callGAPI(service=cd.users(), function=u'update', userKey=user, body=body)
    if do_admin_user:
      callGAPI(service=cd.users(), function=u'makeAdmin', userKey=user, body={u'status': is_admin})

def doRemoveUsersAliases(users):
  cd = buildGAPIObject(u'directory')
  for user in users:
    user_aliases = callGAPI(service=cd.users(), function=u'get', userKey=user, fields=u'aliases,id,primaryEmail')
    user_id = user_aliases[u'id']
    user_primary = user_aliases[u'primaryEmail']
    if u'aliases' in user_aliases:
      print u'%s has %s aliases' % (user_primary, len(user_aliases[u'aliases']))
      for an_alias in user_aliases[u'aliases']:
        print u' removing alias %s for %s...' % (an_alias, user_primary)
        callGAPI(service=cd.users().aliases(), function=u'delete', userKey=user_id, alias=an_alias)
    else:
      print u'%s has no aliases' % user_primary

def doRemoveUsersGroups(users):
  cd = buildGAPIObject(u'directory')
  for user in users:
    user_groups = callGAPIpages(service=cd.groups(), items=u'groups', function=u'list', userKey=user, fields=u'groups(id,email)')
    num_groups = len(user_groups)
    print u'%s is in %s groups' % (user, num_groups)
    i = 1
    for user_group in user_groups:
      print u' removing %s from %s (%s/%s)' % (user, user_group[u'email'], i, num_groups)
      callGAPI(service=cd.members(), function=u'delete', soft_errors=True, groupKey=user_group[u'id'], memberKey=user)
      i += 1
    print u''

def doUpdateGroup():
  group = sys.argv[3]
  if sys.argv[4].lower() in [u'add', u'update', u'sync', u'remove']:
    cd = buildGAPIObject(u'directory')
    if group[0:3].lower() == u'uid:':
      group = group[4:]
    elif group.find(u'@') == -1:
      group = u'%s@%s' % (group, GC_Values[GC_DOMAIN])
    if sys.argv[4].lower() in [u'add', u'update']:
      role = sys.argv[5].upper()
      i = 6
      if role not in [u'OWNER', u'MANAGER', u'MEMBER']:
        role = u'MEMBER'
        i = 5
      if sys.argv[i].lower() in usergroup_types:
        users_email = getUsersToModify(entity_type=sys.argv[i], entity=sys.argv[i+1])
      else:
        users_email = [sys.argv[i],]
      for user_email in users_email:
        if user_email != u'*' and user_email.find(u'@') == -1:
          user_email = u'%s@%s' % (user_email, GC_Values[GC_DOMAIN])
        sys.stderr.write(u' %sing %s %s...' % (sys.argv[4].lower(), role.lower(), user_email))
        try:
          if sys.argv[4].lower() == u'add':
            body = {u'role': role}
            body[u'email'] = user_email
            result = callGAPI(service=cd.members(), function=u'insert', soft_errors=True, groupKey=group, body=body)
          elif sys.argv[4].lower() == u'update':
            result = callGAPI(service=cd.members(), function=u'update', soft_errors=True, groupKey=group, memberKey=user_email, body={u'email': user_email, u'role': role})
          try:
            if str(result[u'email']).lower() != user_email.lower():
              print u'added %s (primary address) to group' % result[u'email']
            else:
              print u'added %s to group' % result[u'email']
          except TypeError:
            pass
        except googleapiclient.errors.HttpError:
          pass
    elif sys.argv[4].lower() == u'sync':
      role = sys.argv[5].upper()
      i = 6
      if role not in [u'OWNER', u'MANAGER', u'MEMBER']:
        role = u'MEMBER'
        i = 5
      users_email = getUsersToModify(entity_type=sys.argv[i], entity=sys.argv[i+1])
      users_email = [x.lower() for x in users_email]
      current_emails = getUsersToModify(entity_type=u'group', entity=group, member_type=role)
      current_emails = [x.lower() for x in current_emails]
      to_add = list(set(users_email) - set(current_emails))
      to_remove = list(set(current_emails) - set(users_email))
      for user_email in to_add:
        sys.stderr.write(u' adding %s %s\n' % (role, user_email))
        try:
          result = callGAPI(service=cd.members(), function=u'insert', soft_errors=True, throw_reasons=[u'duplicate'], groupKey=group, body={u'email': user_email, u'role': role})
        except googleapiclient.errors.HttpError:
          result = callGAPI(service=cd.members(), function=u'update', soft_errors=True, groupKey=group, memberKey=user_email, body={u'email': user_email, u'role': role})
      for user_email in to_remove:
        sys.stderr.write(u' removing %s\n' % user_email)
        result = callGAPI(service=cd.members(), function=u'delete', soft_errors=True, groupKey=group, memberKey=user_email)
    elif sys.argv[4].lower() == u'remove':
      i = 5
      if sys.argv[i].lower() in [u'member', u'manager', u'owner']:
        i += 1
      if sys.argv[i].lower() in usergroup_types:
        user_emails = getUsersToModify(entity_type=sys.argv[i], entity=sys.argv[i+1])
      else:
        user_emails = [sys.argv[i],]
      for user_email in user_emails:
        if user_email != u'*' and user_email.find(u'@') == -1:
          user_email = u'%s@%s' % (user_email, GC_Values[GC_DOMAIN])
        sys.stderr.write(u' removing %s\n' % user_email)
        result = callGAPI(service=cd.members(), function=u'delete', soft_errors=True, groupKey=group, memberKey=user_email)
  else:
    i = 4
    use_cd_api = False
    use_gs_api = False
    gs_body = dict()
    cd_body = dict()
    while i < len(sys.argv):
      if sys.argv[i].lower() == u'email':
        use_cd_api = True
        cd_body[u'email'] = sys.argv[i+1]
        i += 2
      elif sys.argv[i].lower() == u'admincreated':
        use_cd_api = True
        cd_body[u'adminCreated'] = sys.argv[i+1].lower()
        if cd_body[u'adminCreated'] not in [u'true', u'false']:
          print u'Error: Value for admincreated must be true or false. Got %s' % cd_body[u'adminCreated']
          sys.exit(9)
        i += 2
      else:
        value = sys.argv[i+1]
        gs_object = buildDiscoveryObject(u'groupssettings')
        matches_gs_setting = False
        for (attrib, params) in gs_object[u'schemas'][u'Groups'][u'properties'].items():
          if attrib in [u'kind', u'etag', u'email']:
            continue
          if sys.argv[i].lower().replace(u'_', u'') == attrib.lower():
            matches_gs_setting = True
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
                print u'Error: %s must be a number ending with M (megabytes), K (kilobytes) or nothing (bytes). Got %s' % value
                sys.exit(9)
            elif params[u'type'] == u'string':
              if params[u'description'].find(value.upper()) != -1: # ugly hack because API wants some values uppercased.
                value = value.upper()
              elif value.lower() in true_values:
                value = u'true'
              elif value.lower() in false_values:
                value = u'false'
            break
        if not matches_gs_setting:
          print u'ERROR: %s is not a valid argument for "gam update group..."' % sys.argv[i]
          sys.exit(9)
        gs_body[attrib] = value
        use_gs_api = True
        i += 2
    if group[:4].lower() == u'uid:': # group settings API won't take uid so we make sure cd API is used so that we can grab real email.
      use_cd_api = True
      group = group[4:]
    elif group.find(u'@') == -1:
      cd = buildGAPIObject(u'directory')
      group = u'%s@%s' % (group, GC_Values[GC_DOMAIN])
    if use_cd_api:
      cd = buildGAPIObject(u'directory')
      try:
        if cd_body[u'email'].find('@') == -1:
          cd_body[u'email'] = u'%s@%s' % (cd_body[u'email'], GC_Values[GC_DOMAIN])
      except KeyError:
        pass
      cd_result = callGAPI(service=cd.groups(), function=u'update', groupKey=group, body=cd_body)
    if use_gs_api:
      gs = buildGAPIObject(u'groupssettings')
      if use_cd_api:
        group = cd_result[u'email']
      callGAPI(service=gs.groups(), function=u'patch', retry_reasons=[u'serviceLimit'], groupUniqueId=group, body=gs_body)
    print u'updated group %s' % group

def doUpdateAlias():
  alias = sys.argv[3]
  target_type = sys.argv[4].lower()
  if target_type not in [u'user', u'group', u'target']:
    print u'Error: target type should be "user", "group" or "target", got %s' % target_type
    sys.exit(2)
  target_email = sys.argv[5]
  cd = buildGAPIObject(u'directory')
  if alias.find(u'@') == -1:
    alias = u'%s@%s' % (alias, GC_Values[GC_DOMAIN])
  if target_email.find(u'@') == -1:
    target_email = u'%s@%s' % (target_email, GC_Values[GC_DOMAIN])
  try:
    callGAPI(service=cd.users().aliases(), function=u'delete', throw_reasons=[u'invalid'], userKey=alias, alias=alias)
  except googleapiclient.errors.HttpError:
    callGAPI(service=cd.groups().aliases(), function=u'delete', groupKey=alias, alias=alias)
  if target_type == u'user':
    callGAPI(service=cd.users().aliases(), function=u'insert', userKey=target_email, body={u'alias': alias})
  elif target_type == u'group':
    callGAPI(service=cd.groups().aliases(), function=u'insert', groupKey=target_email, body={u'alias': alias})
  elif target_type == u'target':
    try:
      callGAPI(service=cd.users().aliases(), function=u'insert', throw_reasons=[u'invalid'], userKey=target_email, body={u'alias': alias})
    except googleapiclient.errors.HttpError:
      callGAPI(service=cd.groups().aliases(), function=u'insert', groupKey=target_email, body={u'alias': alias})
  print u'updated alias %s' % alias

def doUpdateResourceCalendar():
  resId = sys.argv[3]
  common_name = None
  description = None
  resType = None
  i = 4
  while i < len(sys.argv):
    if sys.argv[i].lower() == u'name':
      common_name = sys.argv[i+1]
      i += 2
    elif sys.argv[i].lower() == u'description':
      description = sys.argv[i+1]
      i += 2
    elif sys.argv[i].lower() == u'type':
      resType = sys.argv[i+1]
      i += 2
  rescal = getResCalObject()
  callGData(service=rescal, function=u'UpdateResourceCalendar', id=resId, common_name=common_name, description=description, type=resType)
  print u'updated resource %s' % resId

def doUpdateCros():
  deviceId = sys.argv[3]
  cd = buildGAPIObject(u'directory')
  if deviceId[:6].lower() == u'query:':
    query = deviceId[6:]
    devices_result = callGAPIpages(service=cd.chromeosdevices(), function=u'list', items=u'chromeosdevices', query=query, customerId=GC_Values[GC_CUSTOMER_ID], fields=u'chromeosdevices/deviceId,nextPageToken')
    devices = list()
    for a_device in devices_result:
      devices.append(a_device[u'deviceId'])
  else:
    devices = [deviceId,]
  i = 4
  body = dict()
  while i < len(sys.argv):
    if sys.argv[i].lower() == u'user':
      body[u'annotatedUser'] = sys.argv[i + 1]
      i += 2
    elif sys.argv[i].lower() == u'location':
      body[u'annotatedLocation'] = sys.argv[i + 1]
      i += 2
    elif sys.argv[i].lower() == u'notes':
      body[u'notes'] = sys.argv[i + 1]
      i += 2
    elif sys.argv[i].lower() == u'status':
      body[u'status'] = sys.argv[i + 1].upper()
      #if body['status'] not in ['ACTIVE', 'DEPROVISIONED']:
      #  print 'Error: status must be active or deprovisioned, got %s' % body['status']
      #  sys.exit(3)
      i += 2
    elif sys.argv[i].lower() in [u'tag', u'asset', u'assetid']:
      body[u'annotatedAssetId'] = sys.argv[i + 1]
      #annotatedAssetId - Handle Asset Tag Field 2015-04-13
      i += 2
    elif sys.argv[i].lower() in [u'ou', u'org']:
      body[u'orgUnitPath'] = sys.argv[i + 1]
      if body[u'orgUnitPath'][0] != u'/':
        body[u'orgUnitPath'] = u'/%s' % body[u'orgUnitPath']
      i += 2
    else:
      print u'Error: %s is not a valid argument for gam update cros' % sys.argv[i]
      sys.exit(5)
  device_count = len(devices)
  i = 1
  for this_device in devices:
    print u' updating %s (%s of %s)' % (this_device, i, device_count)
    callGAPI(service=cd.chromeosdevices(), function=u'patch', deviceId=this_device, body=body, customerId=GC_Values[GC_CUSTOMER_ID])
    i += 1

def doUpdateMobile():
  resourceId = sys.argv[3]
  cd = buildGAPIObject(u'directory')
  i = 4
  action_body = patch_body = dict()
  doPatch = doAction = False
  while i < len(sys.argv):
    if sys.argv[i].lower() == u'action':
      action_body[u'action'] = sys.argv[i+1].lower()
      if action_body[u'action'] == u'wipe':
        action_body[u'action'] = u'admin_remote_wipe'
      elif action_body[u'action'].replace(u'_', '') in [u'accountwipe', u'wipeaccount']:
        action_body[u'action'] = u'admin_account_wipe'
      if action_body[u'action'] not in [u'admin_remote_wipe', u'admin_account_wipe', u'approve', u'block', u'cancel_remote_wipe_then_activate', u'cancel_remote_wipe_then_block']:
        print u'Error: action must be wipe, wipeaccount, approve, block, cancel_remote_wipe_then_activate or cancel_remote_wipe_then_block. Got %s' % action_body[u'action']
        sys.exit(5)
      doAction = True
      i += 2
    elif sys.argv[i].lower() == u'model':
      patch_body[u'model'] = sys.argv[i+1]
      i += 2
      doPatch = True
    elif sys.argv[i].lower() == u'os':
      patch_body[u'os'] = sys.argv[i+1]
      i += 2
      doPatch = True
    elif sys.argv[i].lower() == u'useragent':
      patch_body[u'userAgent'] = sys.argv[i+1]
      i += 2
      doPatch = True
    else:
      print u'Error: %s is not a valid argument for gam update cros' % sys.argv[i]
      sys.exit(5)
  if doPatch:
    callGAPI(service=cd.mobiledevices(), function=u'patch', resourceId=resourceId, body=patch_body, customerId=GC_Values[GC_CUSTOMER_ID])
  if doAction:
    callGAPI(service=cd.mobiledevices(), function=u'action', resourceId=resourceId, body=action_body, customerId=GC_Values[GC_CUSTOMER_ID])

def doDeleteMobile():
  cd = buildGAPIObject(u'directory')
  resourceId = sys.argv[3]
  callGAPI(service=cd.mobiledevices(), function='delete', resourceId=resourceId, customerId=GC_Values[GC_CUSTOMER_ID])

def doUpdateOrg():
  orgUnitPath = sys.argv[3]
  cd = buildGAPIObject(u'directory')
  if sys.argv[4].lower() in [u'move', u'add']:
    if sys.argv[5].lower() in usergroup_types:
      users = getUsersToModify(entity_type=sys.argv[5], entity=sys.argv[6])
    else:
      users = getUsersToModify(entity_type=u'user', entity=sys.argv[5])
    if sys.argv[5].lower() == u'cros':
      cros_count = len(users)
      current_cros = 1
      for cros in users:
        sys.stderr.write(u' moving %s to %s (%s/%s)\n' % (cros, orgUnitPath, current_cros, cros_count))
        callGAPI(service=cd.chromeosdevices(), function=u'update', soft_errors=True, customerId=GC_Values[GC_CUSTOMER_ID], deviceId=cros, body={u'orgUnitPath': '//%s' % orgUnitPath})
        current_cros += 1
    else:
      user_count = len(users)
      current_user = 1
      if orgUnitPath != u'/' and orgUnitPath[0] != '/': # we do want a / at the beginning for user updates
        orgUnitPath = u'/%s' % orgUnitPath
      for user in users:
        sys.stderr.write(u' moving %s to %s (%s/%s)\n' % (user, orgUnitPath, current_user, user_count))
        try:
          callGAPI(service=cd.users(), function=u'update', throw_reasons=[u'conditionNotMet'], userKey=user, body={u'orgUnitPath': orgUnitPath})
        except googleapiclient.errors.HttpError:
          pass
        current_user += 1
  else:
    body = dict()
    i = 4
    while i < len(sys.argv):
      if sys.argv[i].lower() == u'name':
        body[u'name'] = sys.argv[i+1]
        i += 2
      elif sys.argv[i].lower() == u'description':
        body[u'description'] = sys.argv[i+1]
        i += 2
      elif sys.argv[i].lower() == u'parent':
        body[u'parentOrgUnitPath'] = sys.argv[i+1]
        if body[u'parentOrgUnitPath'][0] != u'/':
          body[u'parentOrgUnitPath'] = '/'+body[u'parentOrgUnitPath']
        i += 2
      elif sys.argv[i].lower() == u'noinherit':
        body[u'blockInheritance'] = True
        i += 1
      elif sys.argv[i].lower() == u'inherit':
        body[u'blockInheritance'] = False
        i += 1
    if orgUnitPath[0] == u'/': # we don't want a / at the beginning for OU updates
      orgUnitPath = orgUnitPath[1:]
    callGAPI(service=cd.orgunits(), function=u'update', customerId=GC_Values[GC_CUSTOMER_ID], orgUnitPath=orgUnitPath, body=body)

def doWhatIs():
  email = sys.argv[2]
  cd = buildGAPIObject(u'directory')
  if email.find(u'@') == -1:
    email = u'%s@%s' % (email, GC_Values[GC_DOMAIN])
  try:
    user_or_alias = callGAPI(service=cd.users(), function=u'get', throw_reasons=[u'notFound', u'badRequest', u'invalid'], userKey=email, fields=u'primaryEmail')
    if user_or_alias[u'primaryEmail'].lower() == email.lower():
      sys.stderr.write(u'%s is a user\n\n' % email)
      doGetUserInfo(user_email=email)
      return
    else:
      sys.stderr.write(u'%s is a user alias\n\n' % email)
      doGetAliasInfo(alias_email=email)
      return
  except googleapiclient.errors.HttpError:
    sys.stderr.write(u'%s is not a user...\n' % email)
    sys.stderr.write(u'%s is not a user alias...\n' % email)
  try:
    group = callGAPI(service=cd.groups(), function=u'get', throw_reasons=[u'notFound', u'badRequest'], groupKey=email, fields=u'email')
  except googleapiclient.errors.HttpError:
    sys.stderr.write(u'%s is not a group either!\n\nDoesn\'t seem to exist!\n\n' % email)
    sys.exit(1)
  if group[u'email'].lower() == email.lower():
    sys.stderr.write(u'%s is a group\n\n' % email)
    doGetGroupInfo(group_name=email)
  else:
    sys.stderr.write(u'%s is a group alias\n\n' % email)
    doGetAliasInfo(alias_email=email)

def doGetUserInfo(user_email=None):
  cd = buildGAPIObject(u'directory')
  if user_email == None:
    try:
      user_email = sys.argv[3]
    except IndexError:
      storage = oauth2client.file.Storage(GC_Values[GC_OAUTH2_TXT])
      credentials = storage.get()
      if credentials is None or credentials.invalid:
        doRequestOAuth()
        credentials = storage.get()
      user_email = credentials.id_token[u'email']
  if user_email[:4].lower() == u'uid:':
    user_email = user_email[4:]
  elif user_email.find(u'@') == -1:
    user_email = u'%s@%s' % (user_email, GC_Values[GC_DOMAIN])
  getSchemas = getAliases = getGroups = True
  getLicenses = GC_Values[GC_SHOW_LICENSES]
  projection = u'full'
  customFieldMask = viewType = None
  i = 4
  while i < len(sys.argv):
    if sys.argv[i].lower() == u'noaliases':
      getAliases = False
      i += 1
    elif sys.argv[i].lower() == u'nogroups':
      getGroups = False
      i += 1
    elif sys.argv[i].lower() in [u'nolicenses', u'nolicences']:
      getLicenses = False
      i += 1
    elif sys.argv[i].lower() == u'noschemas':
      getSchemas = False
      projection = u'basic'
      i += 1
    elif sys.argv[i].lower() == u'schemas':
      getSchemas = True
      projection = u'custom'
      customFieldMask = sys.argv[i+1]
      i += 2
    elif sys.argv[i].lower() == u'userview':
      viewType = u'domain_public'
      getGroups = getLicenses = False
      i += 1
    else:
      print u'%s is not a valid argument for gam info user' % sys.argv[i]
      sys.exit(3)
  user = callGAPI(service=cd.users(), function=u'get', userKey=user_email, projection=projection, customFieldMask=customFieldMask, viewType=viewType)
  print u'User: %s' % user[u'primaryEmail']
  if u'name' in user and u'givenName' in user[u'name']:
    print u'First Name: %s' % user[u'name'][u'givenName']
  if u'name' in user and u'familyName' in user[u'name']:
    print u'Last Name: %s' % user[u'name'][u'familyName']
  if u'isAdmin' in user:
    print u'Is a Super Admin: %s' % user[u'isAdmin']
  if u'isDelegatedAdmin' in user:
    print u'Is Delegated Admin: %s' % user[u'isDelegatedAdmin']
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
    if user[u'lastLoginTime'] == u'1970-01-01T00:00:00.000Z':
      print u'Last login time: Never'
    else:
      print u'Last login time: %s' % user[u'lastLoginTime']
  if u'orgUnitPath' in user:
    print u'Google Org Unit Path: %s\n' % user[u'orgUnitPath']
  if u'thumbnailPhotoUrl' in user:
    print u'Photo URL: %s\n' % user[u'thumbnailPhotoUrl']
  if u'ims' in user:
    print u'IMs:'
    for im in user[u'ims']:
      for key in im.keys():
        print u' %s: %s' % (key, im[key])
      print u''
  if u'addresses' in user:
    print u'Addresses:'
    for address in user[u'addresses']:
      for key in address.keys():
        print u' %s: %s' % (key, address[key])
      print ''
  if u'organizations' in user:
    print u'Organizations:'
    for org in user[u'organizations']:
      for key in org.keys():
        print u' %s: %s' % (key, org[key])
      print u''
  if u'phones' in user:
    print u'Phones:'
    for phone in user[u'phones']:
      for key in phone.keys():
        print u' %s: %s' % (key, phone[key])
      print u''
  if u'emails' in user:
    if len(user[u'emails']) > 1:
      print u'Other Emails:'
      for an_email in user[u'emails']:
        if an_email[u'address'].lower() == user[u'primaryEmail'].lower():
          continue
        for key in an_email.keys():
          if key == u'type' and an_email[key] == u'custom':
            continue
          if key == u'customType':
            print u' type: %s' % an_email[key]
          else:
            print u' %s: %s' % (key, an_email[key])
      print u''
  if u'relations' in user:
    print u'Relations:'
    for relation in user[u'relations']:
      for key in relation.keys():
        if key == u'type' and relation[key] == u'custom':
          continue
        elif key == u'customType':
          print u' %s: %s' % (u'type', relation[key])
        else:
          print u' %s: %s' % (key, relation[key])
      print u''
  if u'externalIds' in user:
    print u'External IDs:'
    for externalId in user[u'externalIds']:
      for key in externalId:
        if key == u'type' and externalId[key] == u'custom':
          continue
        elif key == u'customType':
          print u' %s: %s' % (u'type', externalId[key])
        else:
          print u' %s: %s' % (key, externalId[key])
      print u''
  if getSchemas:
    print u'Custom Schemas:'
    if u'customSchemas' in user:
      for schema in user[u'customSchemas']:
        print u' Schema: %s' % schema
        for field in user[u'customSchemas'][schema]:
          if type(user[u'customSchemas'][schema][field]) is list:
            print '  %s:' % field
            for an_item in user[u'customSchemas'][schema][field]:
              print '   %s' % an_item[u'value']
          else:
            print u'  %s: %s' % (field, user[u'customSchemas'][schema][field])
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
    groups = callGAPIpages(service=cd.groups(), function=u'list', items=u'groups', userKey=user_email, fields=u'groups(name,email),nextPageToken')
    if len(groups) > 0:
      print u'Groups: (%s)' % len(groups)
      for group in groups:
        print u'   %s <%s>' % (group[u'name'], group[u'email'])
  if getLicenses:
    print u'Licenses:'
    lic = buildGAPIObject(api='licensing')
    for sku in [u'Google-Apps', u'Google-Apps-For-Business', u'Google-Apps-Unlimited', u'Google-Apps-For-Postini',
                u'Google-Coordinate', u'Google-Drive-storage-20GB', u'Google-Drive-storage-50GB', u'Google-Drive-storage-200GB',
                u'Google-Drive-storage-400GB', u'Google-Drive-storage-1TB', u'Google-Drive-storage-2TB',
                u'Google-Drive-storage-4TB', u'Google-Drive-storage-8TB', u'Google-Drive-storage-16TB', u'Google-Vault',
                u'Google-Vault-Former-Employee']:
      productId, skuId = getProductAndSKU(sku)
      try:
        result = callGAPI(service=lic.licenseAssignments(), function=u'get', throw_reasons=['notFound'], userId=user_email, productId=productId, skuId=skuId)
      except googleapiclient.errors.HttpError:
        continue
      print u' %s' % result[u'skuId']

def doGetGroupInfo(group_name=None):
  if group_name == None:
    group_name = sys.argv[3]
  get_users = True
  try:
    if sys.argv[4].lower() == u'nousers':
      get_users = False
  except IndexError:
    pass
  cd = buildGAPIObject(u'directory')
  gs = buildGAPIObject(u'groupssettings')
  if group_name[:4].lower() == u'uid:':
    group_name = group_name[4:]
  elif group_name.find(u'@') == -1:
    group_name = group_name+u'@'+GC_Values[GC_DOMAIN]
  basic_info = callGAPI(service=cd.groups(), function=u'get', groupKey=group_name)
  try:
    settings = callGAPI(service=gs.groups(), function=u'get', retry_reasons=[u'serviceLimit'], throw_reasons=u'authError',
                        groupUniqueId=basic_info[u'email']) # Use email address retrieved from cd since GS API doesn't support uid
  except googleapiclient.errors.HttpError:
    pass
  print u''
  print u'Group Settings:'
  for key, value in basic_info.items():
    if key in [u'kind', u'etag']:
      continue
    elif type(value) == type(list()):
      print u' %s:' % key
      for val in value:
        print u'  %s' % val
    else:
      print u' %s: %s' % (key, value)
  try:
    for key, value in settings.items():
      if key in [u'kind', u'etag', u'description', u'email', u'name']:
        continue
      elif key == u'maxMessageBytes':
        if value > 1024*1024:
          value = u'%sM' % (value / 1024 / 1024)
        elif value > 1024:
          value = u'%sK' % (value / 1024)
      print u' %s: %s' % (key, value)
  except UnboundLocalError:
    pass
  if get_users:
    members = callGAPIpages(service=cd.members(), function=u'list', items=u'members', groupKey=group_name)
    print u'Members:'
    for member in members:
      try:
        print u' %s: %s (%s)' % (member[u'role'].lower(), member[u'email'], member[u'type'].lower())
      except KeyError:
        try:
          print u' member: %s (%s)' % (member[u'email'], member[u'type'].lower())
        except KeyError:
          print u' member: %s (%s)' % (member[u'id'], member[u'type'].lower())
    print u'Total %s users in group' % len(members)

def doGetAliasInfo(alias_email=None):
  if alias_email == None:
    alias_email = sys.argv[3]
  cd = buildGAPIObject(u'directory')
  if alias_email.find(u'@') == -1:
    alias_email = u'%s@%s' % (alias_email, GC_Values[GC_DOMAIN])
  try:
    result = callGAPI(service=cd.users(), function=u'get', throw_reasons=[u'invalid', u'badRequest'], userKey=alias_email)
  except googleapiclient.errors.HttpError:
    result = callGAPI(service=cd.groups(), function=u'get', groupKey=alias_email)
  print u' Alias Email: %s' % alias_email
  try:
    if result[u'primaryEmail'].lower() == alias_email.lower():
      print u'Error: %s is a primary user email address, not an alias.' % alias_email
      sys.exit(3)
    print u' User Email: %s' % result[u'primaryEmail']
  except KeyError:
    print u' Group Email: %s' % result[u'email']
  print u' Unique ID: %s' % result[u'id']

def doGetResourceCalendarInfo():
  resId = sys.argv[3]
  rescal = getResCalObject()
  result = callGData(service=rescal, function=u'RetrieveResourceCalendar', id=resId)
  print u' Resource ID: '+result[u'resourceId']
  print u' Common Name: '+result[u'resourceCommonName']
  print u' Email: '+result[u'resourceEmail']
  try:
    print u' Type: '+result[u'resourceType']
  except KeyError:
    print u' Type: '
  try:
    print u' Description: '+result[u'resourceDescription']
  except KeyError:
    print u' Description: '

def doGetCrosInfo():
  deviceId = sys.argv[3]
  cd = buildGAPIObject(u'directory')
  info = callGAPI(service=cd.chromeosdevices(), function=u'get', customerId=GC_Values[GC_CUSTOMER_ID], deviceId=deviceId)
  print_json(None, info)

def doGetMobileInfo():
  deviceId = sys.argv[3]
  cd = buildGAPIObject(u'directory')
  try:
    info = callGAPI(service=cd.mobiledevices(), function=u'get', throw_reasons=[u'internalError'], customerId=GC_Values[GC_CUSTOMER_ID], resourceId=deviceId)
    print_json(None, info)
  except:
    sys.stderr.write(u'Error: Resource Not Found: {0} - notFound\n'.format(deviceId))

def print_json(object_name, object_value, spacing=u''):
  if object_name in [u'kind', u'etag', u'etags']:
    return
  if object_name != None:
    sys.stdout.write(u'%s%s: ' % (spacing, object_name))
  if type(object_value) is list:
    if len(object_value) == 1 and type(object_value[0]) in (str, unicode, int):
      sys.stdout.write(u'%s\n' % object_value[0])
      return
    sys.stdout.write(u'\n')
    for a_value in object_value:
      if type(a_value) in (str, unicode):
        print u' %s%s' % (spacing, a_value)
      else:
        print_json(object_name=None, object_value=a_value, spacing=u' %s' % spacing)
  elif type(object_value) is dict:
    for another_object in object_value.keys():
      print_json(object_name=another_object, object_value=object_value[another_object], spacing=spacing)
  else:
    sys.stdout.write(u'%s\n' % (object_value))

def doUpdateNotification():
  cd = buildGAPIObject(u'directory')
  ids = list()
  get_all = False
  i = 3
  isUnread = None
  while i < len(sys.argv):
    if sys.argv[i].lower() == u'unread':
      isUnread = True
      mark_as = u'unread'
      i += 1
    elif sys.argv[i].lower() == u'read':
      isUnread = False
      mark_as = u'read'
      i += 1
    elif sys.argv[i].lower() == u'id':
      if sys.argv[i+1].lower() == u'all':
        get_all = True
      else:
        ids.append(sys.argv[i+1])
      i += 2
    else:
      print u'Error: expected read or unread, got %s' % sys.argv[i]
      sys.exit(3)
  if isUnread == None:
    print u'Error: notifications need to be marked as read or unread.'
    sys.exit(3)
  if get_all:
    notifications = callGAPIpages(service=cd.notifications(), function=u'list', customer=GC_Values[GC_CUSTOMER_ID], fields=u'items(notificationId,isUnread),nextPageToken')
    for noti in notifications:
      if noti[u'isUnread'] != isUnread:
        ids.append(noti[u'notificationId'])
  print u'Marking %s notification(s) as %s...' % (len(ids), mark_as)
  for notificationId in ids:
    result = callGAPI(service=cd.notifications(), function=u'patch', customer=GC_Values[GC_CUSTOMER_ID], notificationId=notificationId, body={u'isUnread': isUnread}, fields=u'notificationId,isUnread')
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
    if sys.argv[i].lower() == u'id':
      if sys.argv[i+1].lower() == u'all':
        get_all = True
      else:
        ids.append(sys.argv[i+1])
      i += 2
    else:
      print u'Error: expected id, got %s' % sys.argv[i]
      sys.exit(3)
  if get_all:
    notifications = callGAPIpages(service=cd.notifications(), function=u'list', customer=GC_Values[GC_CUSTOMER_ID], fields=u'items(notificationId),nextPageToken')
    for noti in notifications:
      ids.append(noti[u'notificationId'])
  print u'Deleting %s notification(s)...' % len(ids)
  for notificationId in ids:
    callGAPI(service=cd.notifications(), function=u'delete', customer=GC_Values[GC_CUSTOMER_ID], notificationId=notificationId)
    print u'deleted %s' % id

def doSiteVerifyShow():
  verif = buildGAPIObject(u'siteVerification')
  a_domain = sys.argv[3]
  txt_record = callGAPI(service=verif.webResource(), function=u'getToken', body={u'site':{u'type':u'INET_DOMAIN', u'identifier':a_domain}, u'verificationMethod':u'DNS_TXT'})
  print u'TXT Record Name:   %s' % a_domain
  print u'TXT Record Value:  %s' % txt_record[u'token']
  print
  cname_record = callGAPI(service=verif.webResource(), function=u'getToken', body={u'site':{u'type':u'INET_DOMAIN', u'identifier':a_domain}, u'verificationMethod':u'DNS_CNAME'})
  cname_token = cname_record[u'token']
  cname_list = cname_token.split(u' ')
  cname_subdomain = cname_list[0]
  cname_value = cname_list[1]
  print u'CNAME Record Name:   %s.%s' % (cname_subdomain, a_domain)
  print u'CNAME Record Value:  %s' % cname_value
  print u''
  webserver_file_record = callGAPI(service=verif.webResource(), function=u'getToken', body={u'site':{u'type':u'SITE', u'identifier':u'http://%s/' % a_domain}, u'verificationMethod':u'FILE'})
  webserver_file_token = webserver_file_record[u'token']
  print u'Saving web server verification file to: %s' % webserver_file_token
  f = open(webserver_file_token, 'wb')
  f.write(u'google-site-verification: %s' % webserver_file_token)
  f.close()
  print u'Verification File URL: http://%s/%s' % (a_domain, webserver_file_token)
  print
  webserver_meta_record = callGAPI(service=verif.webResource(), function=u'getToken', body={u'site':{u'type':u'SITE', u'identifier':u'http://%s/' % a_domain}, u'verificationMethod':u'META'})
  print u'Meta URL:               http://%s/' % a_domain
  print u'Meta HTML Header Data:  %s' % webserver_meta_record[u'token']
  print

def doGetSiteVerifications():
  verif = buildGAPIObject(u'siteVerification')
  sites = callGAPI(service=verif.webResource(), function=u'list')
  try:
    for site in sites[u'items']:
      print u'Site: %s' % site[u'site'][u'identifier']
      print u'Type: %s' % site[u'site'][u'type']
      print u'Owners:'
      for owner in site[u'owners']:
        print u' %s' % owner
      print
  except KeyError:
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
    verify_result = callGAPI(service=verif.webResource(), function=u'insert', throw_reasons=[u'badRequest'], verificationMethod=verificationMethod, body=body)
  except googleapiclient.errors.HttpError, e:
    error = json.loads(e.content)
    message = error[u'error'][u'errors'][0][u'message']
    print u'ERROR: %s' % message
    verify_data = callGAPI(service=verif.webResource(), function=u'getToken', body=body)
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
  print u'You can now add %s or it\'s subdomains as secondary or domain aliases of the %s Google Apps Account.' % (a_domain, GC_Values[GC_DOMAIN])

def doGetNotifications():
  cd = buildGAPIObject(u'directory')
  i = 3
  unread_only = False
  while i < len(sys.argv):
    if sys.argv[i].lower() == u'unreadonly':
      unread_only = True
    else:
      print u'Error: expected unreadonly argument, got %s' % sys.argv[i]
      sys.exit(3)
    i += 1
  notifications = callGAPIpages(service=cd.notifications(), function=u'list', customer=GC_Values[GC_CUSTOMER_ID])
  for notification in notifications:
    if unread_only and not notification[u'isUnread']:
      continue
    print u'From: %s' % notification[u'fromAddress']
    print u'Subject: %s' % notification[u'subject']
    print u'Date: %s' % notification[u'sendTime']
    print u'ID: %s' % notification[u'notificationId']
    if notification[u'isUnread']:
      print u'Read Status: UNREAD'
    else:
      print u'Read Status: READ'
    print u''
    print dehtml(notification[u'body'])
    print u''
    print u'--------------'
    print u''

def doGetOrgInfo():
  cd = buildGAPIObject(u'directory')
  name = sys.argv[3]
  get_users = True
  show_children = False
  try:
    if sys.argv[4].lower() == u'nousers':
      get_users = False
    elif sys.argv[4].lower() in [u'children', u'child']:
      show_children = True
  except IndexError:
    pass
  if name == u'/':
    orgs = callGAPI(service=cd.orgunits(), function=u'list',
                    customerId=GC_Values[GC_CUSTOMER_ID], type=u'children',
                    fields=u'organizationUnits/parentOrgUnitId')
    name = orgs[u'organizationUnits'][0][u'parentOrgUnitId']
  if len(name) > 1 and name[0] == u'/':
    name = name[1:]
  result = callGAPI(service=cd.orgunits(), function=u'get', customerId=GC_Values[GC_CUSTOMER_ID], orgUnitPath=name)
  print_json(None, result)
  if get_users:
    name = result[u'orgUnitPath']
    print u'Users: '
    page_message = getPageMessage(u'users', showFirstLastItems=True)
    users = callGAPIpages(service=cd.users(), function=u'list', items=u'users', page_message=page_message,
                          message_attribute=u'primaryEmail', customer=GC_Values[GC_CUSTOMER_ID], query=u"orgUnitPath='%s'" % name,
                          maxResults=500, fields=u'users(primaryEmail,orgUnitPath),nextPageToken')
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
    asps = callGAPI(service=cd.asps(), function=u'list', userKey=user)
    print u'Application-Specific Passwords for %s' % user
    try:
      for asp in asps[u'items']:
        if asp[u'creationTime'] == u'0':
          created_date = u'Unknown'
        else:
          created_date = datetime.datetime.fromtimestamp(int(asp[u'creationTime'])/1000).strftime(u'%Y-%m-%d %H:%M:%S')
        if asp[u'lastTimeUsed'] == u'0':
          used_date = u'Never'
        else:
          used_date = datetime.datetime.fromtimestamp(int(asp[u'lastTimeUsed'])/1000).strftime(u'%Y-%m-%d %H:%M:%S')
        print u' ID: %s\n  Name: %s\n  Created: %s\n  Last Used: %s\n' % (asp[u'codeId'], asp[u'name'], created_date, used_date)
    except KeyError:
      print u' no ASPs for %s\n' % user

def doDelASP(users):
  codeId = sys.argv[5]
  cd = buildGAPIObject(u'directory')
  for user in users:
    callGAPI(service=cd.asps(), function=u'delete', userKey=user, codeId=codeId)
    print u'deleted ASP %s for %s' % (codeId, user)

def doGetBackupCodes(users):
  cd = buildGAPIObject(u'directory')
  for user in users:
    try:
      codes = callGAPI(service=cd.verificationCodes(), function=u'list', throw_reasons=[u'invalidArgument', u'invalid'], userKey=user)
    except googleapiclient.errors.HttpError:
      codes = dict()
      codes[u'items'] = list()
    print u'Backup verification codes for %s' % user
    print u''
    try:
      i = 0
      while True:
        sys.stdout.write(u'%s. %s\n' % (i+1, codes[u'items'][i][u'verificationCode']))
        i += 1
    except IndexError:
      print u''
    except KeyError:
      print u''
    print u''

def doGenBackupCodes(users):
  cd = buildGAPIObject(u'directory')
  for user in users:
    callGAPI(service=cd.verificationCodes(), function=u'generate', userKey=user)
    codes = callGAPI(service=cd.verificationCodes(), function=u'list', userKey=user)
    print u'Backup verification codes for %s' % user
    print ''
    try:
      i = 0
      while True:
        sys.stdout.write(u'%s. %s\n' % (i+1, codes[u'items'][i][u'verificationCode']))
        i += 1
    except IndexError:
      print u''
    except KeyError:
      print u''
    print u''

def doDelBackupCodes(users):
  cd = buildGAPIObject(u'directory')
  for user in users:
    try:
      callGAPI(service=cd.verificationCodes(), function=u'invalidate', soft_errors=True, throw_reasons=[u'invalid',], userKey=user)
    except googleapiclient.errors.HttpError:
      print u'No 2SV backup codes for %s' % user
      continue
    print u'2SV backup codes for %s invalidated' % user

def commonClientIds(clientId):
  if clientId == u'gasmo':
    return u'1095133494869.apps.googleusercontent.com'
  return clientId

def doGetTokens(users):
  cd = buildGAPIObject(u'directory')
  clientId = None
  i = 5
  while i < len(sys.argv):
    if sys.argv[i].lower() == u'clientid':
      clientId = sys.argv[i+1]
      i += 2
    else:
      print u'%s is not a valid argument for gam <users> show tokens' % sys.argv[i]
      sys.exit(3)
  if clientId:
    clientId = commonClientIds(clientId)
    for user in users:
      try:
        token = callGAPI(service=cd.tokens(), function=u'get', throw_reasons=[u'notFound',], userKey=user, clientId=clientId, fields=u'clientId')
      except googleapiclient.errors.HttpError:
        continue
      print u'%s has allowed this token' % user
    return
  for user in users:
    tokens = callGAPI(service=cd.tokens(), function=u'list', userKey=user)
    print u'Tokens for %s:' % user
    try:
      for token in tokens[u'items']:
        print u' Client ID: %s' % token[u'clientId']
        for item in token.keys():
          if item in [u'etag', u'kind', u'clientId']:
            continue
          if type(token[item]) is list:
            print u' %s:' % item
            for it in token[item]:
              print u'  %s' % it
          if type(token[item]) in (unicode, bool):
            try:
              print u' %s: %s' % (item, token[item])
            except UnicodeEncodeError:
              print u' %s: %s' % (item, token[item][:-1])
        print ''
    except KeyError:
      print u' no tokens for %s' % user
    print u''

def doDelTokens(users):
  cd = buildGAPIObject(u'directory')
  clientId = sys.argv[6]
  clientId = commonClientIds(clientId)
  for user in users:
    callGAPI(service=cd.tokens(), function=u'delete', userKey=user, clientId=clientId)
    print u'Deleted token for %s' % user

def doDeprovUser(users):
  cd = buildGAPIObject(u'directory')
  for user in users:
    printGettingMessage(u'Getting Application Specific Passwords for %s\n' % user)
    asps = callGAPI(service=cd.asps(), function=u'list', userKey=user, fields=u'items/codeId')
    i = 1
    try:
      for asp in asps[u'items']:
        print u' deleting ASP %s of %s' % (i, len(asps['items']))
        callGAPI(service=cd.asps(), function=u'delete', userKey=user, codeId=asp[u'codeId'])
        i += 1
    except KeyError:
      print u'No ASPs'
    print u'Invalidating 2SV Backup Codes for %s' % user
    try:
      callGAPI(service=cd.verificationCodes(), function=u'invalidate', soft_errors=True, throw_reasons=[u'invalid'], userKey=user)
    except googleapiclient.errors.HttpError:
      print u'No 2SV Backup Codes'
    printGettingMessage(u'Getting tokens for %s...\n' % user)
    tokens = callGAPI(service=cd.tokens(), function=u'list', userKey=user, fields=u'items/clientId')
    i = 1
    try:
      for token in tokens[u'items']:
        print u' deleting token %s of %s' % (i, len(tokens['items']))
        callGAPI(service=cd.tokens(), function=u'delete', userKey=user, clientId=token[u'clientId'])
        i += 1
    except KeyError:
      print u'No Tokens'
    print u'Done deprovisioning %s' % user

def doUpdateDomain():
  adminObj = getAdminSettingsObject()
  command = sys.argv[3].lower()
  if command == u'language':
    language = sys.argv[4]
    callGData(service=adminObj, function=u'UpdateDefaultLanguage', defaultLanguage=language)
  elif command == u'name':
    name = sys.argv[4]
    callGData(service=adminObj, function=u'UpdateOrganizationName', organizationName=name)
  elif command == u'admin_secondary_email':
    admin_secondary_email = sys.argv[4]
    callGData(service=adminObj, function=u'UpdateAdminSecondaryEmail', adminSecondaryEmail=admin_secondary_email)
  elif command == u'logo':
    logo_file = sys.argv[4]
    try:
      fp = open(logo_file, 'rb')
      logo_image = fp.read()
      fp.close()
    except IOError:
      print u'Error: can\'t open file %s' % logo_file
      sys.exit(11)
    callGData(service=adminObj, function=u'UpdateDomainLogo', logoImage=logo_image)
  elif command == u'mx_verify':
    result = callGData(service=adminObj, function=u'UpdateMXVerificationStatus')
    print u'Verification Method: %s' % result[u'verificationMethod']
    print u'Verified: %s' % result[u'verified']
  elif command == u'sso_settings':
    enableSSO = samlSignonUri = samlLogoutUri = changePasswordUri = ssoWhitelist = useDomainSpecificIssuer = None
    i = 4
    while i < len(sys.argv):
      if sys.argv[i].lower() == u'enabled':
        if sys.argv[i+1].lower() == u'true':
          enableSSO = True
        elif sys.argv[i+1].lower() == u'false':
          enableSSO = False
        else:
          print u'Error: value for enabled must be true or false, got %s' % sys.argv[i+1]
          exit(9)
        i += 2
      elif sys.argv[i].lower() == u'sign_on_uri':
        samlSignonUri = sys.argv[i+1]
        i += 2
      elif sys.argv[i].lower() == u'sign_out_uri':
        samlLogoutUri = sys.argv[i+1]
        i += 2
      elif sys.argv[i].lower() == u'password_uri':
        changePasswordUri = sys.argv[i+1]
        i += 2
      elif sys.argv[i].lower() == u'whitelist':
        ssoWhitelist = sys.argv[i+1]
        i += 2
      elif sys.argv[i].lower() == u'use_domain_specific_issuer':
        if sys.argv[i+1].lower() == u'true':
          useDomainSpecificIssuer = True
        elif sys.argv[i+1].lower() == u'false':
          useDomainSpecificIssuer = False
        else:
          print u'Error: value for use_domain_specific_issuer must be true or false, got %s' % sys.argv[i+1]
          sys.exit(9)
        i += 2
      else:
        print u'Error: unknown option for "gam update domain sso_settings...": %s' % sys.argv[i]
        sys.exit(9)
    callGData(service=adminObj, function=u'UpdateSSOSettings', enableSSO=enableSSO,
              samlSignonUri=samlSignonUri, samlLogoutUri=samlLogoutUri,
              changePasswordUri=changePasswordUri, ssoWhitelist=ssoWhitelist,
              useDomainSpecificIssuer=useDomainSpecificIssuer)
  elif command == u'sso_key':
    key_file = sys.argv[4]
    try:
      fp = open(key_file, 'rb')
      key_data = fp.read()
      fp.close()
    except IOError:
      print u'Error: can\'t open file %s' % logo_file
      sys.exit(11)
    callGData(service=adminObj, function=u'UpdateSSOKey', signingKey=key_data)
  elif command == u'user_migrations':
    value = sys.argv[4].lower()
    if value not in [u'true', u'false']:
      print u'Error: value for user_migrations must be true or false, got %s' % sys.argv[4]
      sys.exit(9)
    result = callGData(service=adminObj, function=u'UpdateUserMigrationStatus', enableUserMigration=value)
  elif command == u'outbound_gateway':
    gateway = sys.argv[4]
    mode = sys.argv[6].upper()
    try:
      result = callGData(service=adminObj, function=u'UpdateOutboundGatewaySettings', smartHost=gateway, smtpMode=mode)
    except TypeError:
      pass
  elif command == u'email_route':
    i = 4
    while i < len(sys.argv):
      if sys.argv[i].lower() == u'destination':
        destination = sys.argv[i+1]
        i += 2
      elif sys.argv[i].lower() == u'rewrite_to':
        rewrite_to = sys.argv[i+1].lower()
        if rewrite_to == u'true':
          rewrite_to = True
        elif rewrite_to == u'false':
          rewrite_to = False
        else:
          print u'Error: value for rewrite_to must be true or false, got %s' % sys.argv[i+1]
          sys.exit(9)
        i += 2
      elif sys.argv[i].lower() == u'enabled':
        enabled = sys.argv[i+1].lower()
        if enabled == u'true':
          enabled = True
        elif enabled == u'false':
          enabled = False
        else:
          print u'Error: value for enabled must be true or false, got %s' % sys.argv[i+1]
          sys.exit(9)
        i += 2
      elif sys.argv[i].lower() == u'bounce_notifications':
        bounce_notifications = sys.argv[i+1].lower()
        if bounce_notifications == u'true':
          bounce_notifications = True
        elif bounce_notifications == u'false':
          bounce_notifications = False
        else:
          print u'Error: value for bounce_notifications must be true or false, got %s' % sys.argv[i+1]
          sys.exit(9)
        i += 2
      elif sys.argv[i].lower() == u'account_handling':
        account_handling = sys.argv[i+1].lower()
        if account_handling == u'all_accounts':
          account_handling = u'allAccounts'
        elif account_handling == u'provisioned_accounts':
          account_handling = u'provisionedAccounts'
        elif account_handling == u'unknown_accounts':
          account_handling = u'unknownAccounts'
        else:
          print u'Error: value for account_handling must be all_accounts, provisioned_account or unknown_accounts. Got %s' % sys.argv[i+1]
          sys.exit(9)
        i += 2
      else:
        print u'Error: invalid setting for "gam update domain email_route..."'
        sys.exit(10)
    callGData(service=adminObj, function=u'AddEmailRoute', routeDestination=destination, routeRewriteTo=rewrite_to, routeEnabled=enabled,
              bounceNotifications=bounce_notifications, accountHandling=account_handling)
  else:
    print u'Error: that is not a valid "gam update domain" command'

def doGetDomainInfo():
  adm = buildGAPIObject(u'admin-settings')
  if len(sys.argv) > 4 and sys.argv[3].lower() == u'logo':
    target_file = sys.argv[4]
    adminObj = getAdminSettingsObject()
    logo_image = adminObj.GetDomainLogo()
    try:
      fp = open(target_file, 'wb')
      fp.write(logo_image)
      fp.close()
    except IOError:
      print u'Error: can\'t open file %s for writing' % target_file
      sys.exit(11)
    sys.exit(0)
  print u'Google Apps Domain: %s' % GC_Values[GC_DOMAIN]
  cd = buildGAPIObject(u'directory')
  if GC_Values[GC_CUSTOMER_ID] != MY_CUSTOMER:
    customer_id = GC_Values[GC_CUSTOMER_ID]
  else:
    result = callGAPI(service=cd.users(), function=u'list', fields=u'users(customerId)', customer=GC_Values[GC_CUSTOMER_ID], sortOrder=u'DESCENDING')
    customer_id = result[u'users'][0][u'customerId']
  print u'Customer ID: %s' % customer_id
  default_language = callGAPI(service=adm.defaultLanguage(), function=u'get', domainName=GC_Values[GC_DOMAIN])
  print u'Default Language: %s' % default_language[u'entry'][u'apps$property'][0][u'value']
  org_name = callGAPI(service=adm.organizationName(), function='get', domainName=GC_Values[GC_DOMAIN])
  print u'Organization Name: %s' % org_name[u'entry'][u'apps$property'][0][u'value']
  admin_email = callGAPI(service=adm.adminSecondaryEmail(), function='get', domainName=GC_Values[GC_DOMAIN])
  print u'Admin Secondary Email: %s' % admin_email[u'entry'][u'apps$property'][0][u'value']
  max_users = callGAPI(service=adm.maximumNumberOfUsers(), function=u'get', domainName=GC_Values[GC_DOMAIN])
  print u'Maximum Users: %s' % max_users[u'entry'][u'apps$property'][0][u'value']
  current_users = callGAPI(service=adm.currentNumberOfUsers(), function=u'get', domainName=GC_Values[GC_DOMAIN])
  print u'Current Users: %s' % current_users[u'entry'][u'apps$property'][0][u'value']
  is_dom_verified = callGAPI(service=adm.isVerified(), function=u'get', domainName=GC_Values[GC_DOMAIN])
  print u'Domain is Verified: %s' % is_dom_verified[u'entry'][u'apps$property'][0][u'value']
  domain_edition = callGAPI(service=adm.edition(), function=u'get', domainName=GC_Values[GC_DOMAIN])
  print u'Domain Edition: %s' % domain_edition[u'entry'][u'apps$property'][0][u'value']
  customer_pin = callGAPI(service=adm.customerPIN(), function=u'get', domainName=GC_Values[GC_DOMAIN])
  print u'Customer PIN: %s' % customer_pin[u'entry'][u'apps$property'][0][u'value']
  creation_time = callGAPI(service=adm.creationTime(), function=u'get', domainName=GC_Values[GC_DOMAIN])
  my_date = creation_time[u'entry'][u'apps$property'][0][u'value']
  my_date = my_date[:15]
  my_offset = creation_time[u'entry'][u'apps$property'][0][u'value'][19:]
  nice_time = datetime.datetime.strptime(my_date, u"%Y%m%dT%H%M%S")
  print u'Domain Creation Time: %s %s' % (nice_time, my_offset)
  country_code = callGAPI(service=adm.countryCode(), function=u'get', domainName=GC_Values[GC_DOMAIN])
  print u'Domain Country Code: %s' % country_code[u'entry'][u'apps$property'][0][u'value']
  mxverificationstatus = callGAPI(service=adm.mxVerification(), function=u'get', domainName=GC_Values[GC_DOMAIN])
  for entry in mxverificationstatus[u'entry'][u'apps$property']:
    if entry[u'name'] == u'verified':
      print u'MX Verification Verified: %s' % entry[u'value']
    elif entry[u'name'] == u'verificationMethod':
      print u'MX Verification Method: %s' % entry[u'value']
  ssosettings = callGAPI(service=adm.ssoGeneral(), function=u'get', domainName=GC_Values[GC_DOMAIN])
  for entry in ssosettings[u'entry'][u'apps$property']:
    if entry[u'name'] == u'enableSSO':
      print u'SSO Enabled: %s' % entry[u'value']
    elif entry[u'name'] == u'samlSignonUri':
      print u'SSO Signon Page: %s' % entry[u'value']
    elif entry[u'name'] == u'samlLogoutUri':
      print u'SSO Logout Page: %s' % entry[u'value']
    elif entry[u'name'] == u'changePasswordUri':
      print u'SSO Password Page: %s' % entry[u'value']
    elif entry[u'name'] == u'ssoWhitelist':
      print u'SSO Whitelist IPs: %s' % entry[u'value']
    elif entry[u'name'] == u'useDomainSpecificIssuer':
      print u'SSO Use Domain Specific Issuer: %s' % entry[u'value']
  ssokey = callGAPI(service=adm.ssoSigningKey(), function=u'get', silent_errors=True, soft_errors=True, domainName=GC_Values[GC_DOMAIN])
  try:
    for entry in ssokey[u'entry'][u'apps$property']:
      if entry[u'name'] == u'algorithm':
        print u'SSO Key Algorithm: %s' % entry[u'value']
      elif entry[u'name'] == u'format':
        print u'SSO Key Format: %s' % entry[u'value']
      elif entry[u'name'] == u'modulus':
        print u'SSO Key Modulus: %s' % entry[u'value']
      elif entry[u'name'] == u'exponent':
        print u'SSO Key Exponent: %s' % entry[u'value']
      elif entry[u'name'] == u'yValue':
        print u'SSO Key yValue: %s' % entry[u'value']
      elif entry[u'name'] == u'signingKey':
        print u'Full SSO Key: %s' % entry[u'value']
  except TypeError:
    pass
  migration_status = callGAPI(service=adm.userEmailMigrationEnabled(), function=u'get', domainName=GC_Values[GC_DOMAIN])
  print u'User Migration Enabled: %s' %  migration_status[u'entry'][u'apps$property'][0][u'value']
  outbound_gateway_settings = {u'smartHost': u'', u'smtpMode': u''} # Initialize blank in case we get an 1801 Error
  outbound_gateway_settings = callGAPI(service=adm.outboundGateway(), function=u'get', domainName=GC_Values[GC_DOMAIN])
  try:
    for entry in outbound_gateway_settings[u'entry'][u'apps$property']:
      if entry[u'name'] == u'smartHost':
        print u'Outbound Gateway Smart Host: %s' % entry[u'value']
      elif entry[u'name'] == u'smtpMode':
        print u'Outbound Gateway SMTP Mode: %s' % entry[u'value']
  except KeyError:
    print u'Outbound Gateway Smart Host: None'
    print u'Outbound Gateway SMTP Mode: None'

def doDeleteUser():
  user_email = sys.argv[3]
  cd = buildGAPIObject(u'directory')
  if user_email[:4].lower() == u'uid:':
    user_email = user_email[4:]
  elif user_email.find(u'@') == -1:
    user_email = u'%s@%s' % (user_email, GC_Values[GC_DOMAIN])
  print u"Deleting account for %s" % (user_email)
  callGAPI(service=cd.users(), function=u'delete', userKey=user_email)

def doUndeleteUser():
  user = sys.argv[3].lower()
  user_uid = False
  orgUnit = u'/'
  try:
    if sys.argv[4].lower() in [u'ou', u'org']:
      orgUnit = sys.argv[5]
  except IndexError:
    pass
  cd = buildGAPIObject(u'directory')
  if user[:4].lower() == u'uid:':
    user_uid = user[4:]
  elif user.find(u'@') == -1:
    user = u'%s@%s' % (user, GC_Values[GC_DOMAIN])
  if not user_uid:
    print u'Looking up UID for %s...' % user
    deleted_users = callGAPIpages(service=cd.users(), function=u'list', items=u'users', customer=GC_Values[GC_CUSTOMER_ID], showDeleted=True, maxResults=500)
    matching_users = list()
    for deleted_user in deleted_users:
      if str(deleted_user[u'primaryEmail']).lower() == user:
        matching_users.append(deleted_user)
    if len(matching_users) < 1:
      print u'ERROR: could not find deleted user with that address.'
      sys.exit(3)
    elif len(matching_users) > 1:
      print u'ERROR: more than one matching deleted %s user. Please select the correct one to undelete and specify with "gam undelete user uid:<uid>"' % user
      print u''
      for matching_user in matching_users:
        print u' uid:%s ' % matching_user[u'id']
        for attr_name in [u'creationTime', u'lastLoginTime', u'deletionTime']:
          try:
            if matching_user[attr_name] == u'1970-01-01T00:00:00.000Z':
              matching_user[attr_name] = u'Never'
            print u'   %s: %s ' % (attr_name, matching_user[attr_name])
          except KeyError:
            pass
        print
      sys.exit(3)
    else:
      user_uid = matching_users[0][u'id']
  print u"Undeleting account for %s" % user
  callGAPI(service=cd.users(), function=u'undelete', userKey=user_uid, body={u'orgUnitPath': orgUnit})

def doDeleteGroup():
  group = sys.argv[3]
  cd = buildGAPIObject(u'directory')
  if group[:4].lower() == u'uid:':
    group = group[4:]
  elif group.find(u'@') == -1:
    group = u'%s@%s' % (group, GC_Values[GC_DOMAIN])
  print u"Deleting group %s" % group
  callGAPI(service=cd.groups(), function=u'delete', groupKey=group)

def doDeleteAlias(alias_email=None):
  is_user = is_group = False
  if alias_email == None:
    alias_email = sys.argv[3]
  if alias_email.lower() == u'user':
    is_user = True
    alias_email = sys.argv[4]
  elif alias_email.lower() == u'group':
    is_group = True
    alias_email = sys.argv[4]
  cd = buildGAPIObject(u'directory')
  if alias_email.find(u'@') == -1:
    alias_email = u'%s@%s' % (alias_email, GC_Values[GC_DOMAIN])
  print u"Deleting alias %s" % alias_email
  if is_user or (not is_user and not is_group):
    try:
      callGAPI(service=cd.users().aliases(), function=u'delete', throw_reasons=[u'invalid', u'badRequest', u'notFound'], userKey=alias_email, alias=alias_email)
      return
    except googleapiclient.errors.HttpError, e:
      error = json.loads(e.content)
      reason = error[u'error'][u'errors'][0][u'reason']
      if reason == u'notFound':
        print u'Error: The alias %s does not exist' % alias_email
        sys.exit(4)
  if not is_user or (not is_user and not is_group):
    callGAPI(service=cd.groups().aliases(), function=u'delete', groupKey=alias_email, alias=alias_email)

def doDeleteResourceCalendar():
  res_id = sys.argv[3]
  rescal = getResCalObject()
  print u"Deleting resource calendar %s" % res_id
  callGData(service=rescal, function=u'DeleteResourceCalendar', id=res_id)

def doDeleteOrg():
  name = sys.argv[3]
  cd = buildGAPIObject(u'directory')
  if name[0] == u'/':
    name = name[1:]
  print u"Deleting organization %s" % name
  callGAPI(service=cd.orgunits(), function=u'delete', customerId=GC_Values[GC_CUSTOMER_ID], orgUnitPath=name)

def output_csv(csv_list, titles, list_type, todrive):
  csv.register_dialect(u'nixstdout', lineterminator=u'\n')
  if todrive:
    import StringIO
    string_file = StringIO.StringIO()
    writer = csv.DictWriter(string_file, fieldnames=titles, dialect=u'nixstdout', quoting=csv.QUOTE_MINIMAL)
  else:
    writer = csv.DictWriter(GC_Values[GC_CSVFILE], fieldnames=titles, dialect=u'nixstdout', quoting=csv.QUOTE_MINIMAL)
  writer.writerows(csv_list)
  if todrive:
    columns = len(csv_list[0])
    rows = len(csv_list)
    cell_count = rows * columns
    convert = True
    if cell_count > 500000 or columns > 256:
      print u'Warning: results are to large for Google Spreadsheets. Uploading as a regular CSV file.'
      convert = False
    drive = buildGAPIObject(u'drive')
    string_data = string_file.getvalue()
    media = googleapiclient.http.MediaInMemoryUpload(string_data, mimetype=u'text/csv')
    result = callGAPI(service=drive.files(), function=u'insert', convert=convert,
                      body={u'description': u' '.join(sys.argv), u'title': u'%s - %s' % (GC_Values[GC_DOMAIN], list_type), u'mimeType': u'text/csv'},
                      media_body=media)
    file_url = result[u'alternateLink']
    if GC_Values[GC_NO_BROWSER]:
      msg_txt = u'Drive file uploaded to:\n %s' % file_url
      msg_subj = u'%s - %s' % (GC_Values[GC_DOMAIN], list_type)
      send_email(msg_subj, msg_txt)
      print msg_txt
    else:
      import webbrowser
      webbrowser.open(file_url)

def flatten_json(structure, key="", path="", flattened=None):
  if flattened == None:
    flattened = {}
  if type(structure) not in(dict, list):
    flattened[((path + ".") if path else "") + key] = structure
  elif isinstance(structure, list):
    for i, item in enumerate(structure):
      flatten_json(item, "%d" % i, ".".join(filter(None, [path, key])), flattened)
  else:
    for new_key, value in structure.items():
      if new_key in [u'kind', u'etag']:
        continue
      if value == u'1970-01-01T00:00:00.000Z':
        value = u'Never'
      flatten_json(value, new_key, ".".join(filter(None, [path, key])), flattened)
  return flattened

def doPrintUsers():
  cd = buildGAPIObject(u'directory')
  user_fields = [u'primaryEmail',]
  fields = u''
  customer = GC_Values[GC_CUSTOMER_ID]
  printDomain = None
  query = None
  projection = u'basic'
  customFieldMask = None
  getGroupFeed = getLicenseFeed = email_parts = False
  todrive = False
  viewType = deleted_only = orderBy = sortOrder = None
  groupsDelimiter = u' '
  i = 3
  while i < len(sys.argv):
    if sys.argv[i].lower() == u'allfields':
      fields = None
      i += 1
    elif sys.argv[i].lower() == u'custom':
      user_fields.append(u'customSchemas')
      if sys.argv[i+1].lower() == u'all':
        projection = u'full'
      else:
        projection = u'custom'
        customFieldMask = sys.argv[i+1]
      i += 2
    elif sys.argv[i].lower() == u'todrive':
      todrive = True
      i += 1
    elif sys.argv[i].lower() in [u'deleted_only', u'only_deleted']:
      deleted_only = True
      i += 1
    elif sys.argv[i].lower() == u'delimiter':
      groupsDelimiter = sys.argv[i+1]
      i += 2
    elif sys.argv[i].lower() == u'orderby':
      orderBy = sys.argv[i+1]
      if orderBy.lower() not in [u'email', u'familyname', u'givenname', u'firstname', u'lastname']:
        print u'Error: orderby should be email, familyName or givenName. Got %s' % orderBy
        sys.exit(3)
      elif orderBy.lower() in [u'familyname', u'lastname']:
        orderBy = u'familyName'
      elif orderBy.lower() in [u'givenname', u'firstname']:
        orderBy = u'givenName'
      i += 2
    elif sys.argv[i].lower() == u'userview':
      viewType = u'domain_public'
      i += 1
    elif sys.argv[i].lower() in [u'ascending', u'descending']:
      sortOrder = sys.argv[i].upper()
      i += 1
    elif sys.argv[i].lower() == u'domain':
      printDomain = sys.argv[i+1]
      customer = None
      i += 2
    elif sys.argv[i].lower() == u'query':
      query = sys.argv[i+1]
      i += 2
    elif sys.argv[i].lower() in [u'firstname', u'givenname', u'lastname', u'familyName', u'fullname']:
      user_fields.append(u'name')
      i += 1
    elif sys.argv[i].lower() == u'ou':
      user_fields.append(u'orgUnitPath')
      i += 1
    elif sys.argv[i].lower() == u'suspended':
      user_fields.append(u'suspended')
      user_fields.append(u'suspensionReason')
      i += 1
    elif sys.argv[i].lower() == u'ismailboxsetup':
      user_fields.append(u'isMailboxSetup')
      i += 1
    elif sys.argv[i].lower() == u'changepassword':
      user_fields.append(u'changePasswordAtNextLogin')
      i += 1
    elif sys.argv[i].lower() == u'agreed2terms':
      user_fields.append(u'agreedToTerms')
      i += 1
    elif sys.argv[i].lower() == u'admin':
      user_fields.append(u'isAdmin')
      user_fields.append(u'isDelegatedAdmin')
      i += 1
    elif sys.argv[i].lower() == u'gal':
      user_fields.append(u'includeInGlobalAddressList')
      i += 1
    elif sys.argv[i].lower() in ['photo', 'photourl']:
      user_fields.append(u'thumbnailPhotoUrl')
      i += 1
    elif sys.argv[i].lower() == u'id':
      user_fields.append(u'id')
      i += 1
    elif sys.argv[i].lower() == u'creationtime':
      user_fields.append(u'creationTime')
      i += 1
    elif sys.argv[i].lower() == u'lastlogintime':
      user_fields.append(u'lastLoginTime')
      i += 1
    elif sys.argv[i].lower() in [u'nicknames', u'aliases']:
      user_fields.append(u'aliases')
      user_fields.append(u'nonEditableAliases')
      i += 1
    elif sys.argv[i].lower() in [u'im', u'ims']:
      user_fields.append(u'ims')
      i += 1
    elif sys.argv[i].lower() in [u'emails', u'email']:
      user_fields.append(u'emails')
      i += 1
    elif sys.argv[i].lower().replace(u'_', u'') in [u'externalids', u'externalid']:
      user_fields.append(u'externalIds')
      i += 1
    elif sys.argv[i].lower() in [u'relation', u'relations']:
      user_fields.append(u'relations')
      i += 1
    elif sys.argv[i].lower() in [u'address', u'addresses']:
      user_fields.append(u'addresses')
      i += 1
    elif sys.argv[i].lower() in [u'organization', u'organizations']:
      user_fields.append(u'organizations')
      i += 1
    elif sys.argv[i].lower() in [u'phone', u'phones']:
      user_fields.append(u'phones')
      i += 1
    elif sys.argv[i].lower() == u'groups':
      getGroupFeed = True
      i += 1
    elif sys.argv[i].lower() in [u'license', u'licenses', u'licence', u'licences']:
      getLicenseFeed = True
      i += 1
    elif sys.argv[i].lower() in [u'emailpart', u'emailparts', u'username']:
      email_parts = True
      i += 1
    else:
      showUsage()
      sys.exit(5)
  if fields != None:
    user_fields = set(user_fields)
    fields = u'nextPageToken,users(%s)' % u','.join(user_fields)
  printGettingMessage(u"Getting all users in Google Apps account (may take some time on a large account)...\n")
  page_message = getPageMessage(u'users', showFirstLastItems=True)
  all_users = callGAPIpages(service=cd.users(), function=u'list', items=u'users', page_message=page_message,
                            message_attribute=u'primaryEmail', customer=customer, domain=printDomain, fields=fields,
                            showDeleted=deleted_only, maxResults=500, orderBy=orderBy, sortOrder=sortOrder, viewType=viewType,
                            query=query, projection=projection, customFieldMask=customFieldMask)
  titles = [u'primaryEmail',]
  attributes = []
  for user in all_users:
    if email_parts:
      try:
        user_email = user[u'primaryEmail']
        if user_email.find(u'@') != -1:
          user[u'primaryEmailLocal'] = user_email[:user_email.find(u'@')]
          user[u'primaryEmailDomain'] = user_email[user_email.find(u'@')+1:]
      except KeyError:
        pass
    attributes.append(flatten_json(user))
    for item in attributes[-1].keys():
      if item not in titles:
        titles.append(item)
  titles.remove(u'primaryEmail')
  titles = sorted(titles)
  titles = [u'primaryEmail'] + titles
  header = {}
  for title in titles:
    header[title] = title
  attributes.insert(0, header)
  if getGroupFeed:
    total_users = len(attributes) - 1
    user_count = 1
    titles.append(u'Groups')
    attributes[0].update(Groups=u'Groups')
    for user in attributes[1:]:
      user_email = user[u'primaryEmail']
      printGettingMessage(u"Getting Group Membership for %s (%s/%s)\r\n" % (user_email, user_count, total_users))
      groups = callGAPIpages(service=cd.groups(), function=u'list', items=u'groups', userKey=user_email)
      grouplist = u''
      for groupname in groups:
        grouplist += groupname[u'email']+groupsDelimiter
      if grouplist[-1:] == groupsDelimiter:
        grouplist = grouplist[:-1]
      user.update(Groups=grouplist)
      user_count += 1
  if getLicenseFeed:
    titles.append(u'Licenses')
    attributes[0].update(Licenses=u'Licenses')
    licenses = doPrintLicenses(return_list=True)
    if len(licenses) > 1:
      for user in attributes[1:]:
        user_licenses = []
        for u_license in licenses:
          if u_license[u'userId'].lower() == user[u'primaryEmail'].lower():
            user_licenses.append(u_license[u'skuId'])
        user.update(Licenses=u' '.join(user_licenses))
  output_csv(attributes, titles, u'Users', todrive)

def doPrintGroups():
  i = 3
  printname = printdesc = printid = members = owners = managers = settings = admin_created = aliases = todrive = False
  customer = GC_Values[GC_CUSTOMER_ID]
  usedomain = usemember = None
  listDelimiter = u'\n'
  group_attributes = [{u'Email': u'Email'}]
  titles = [u'Email']
  fields = u'nextPageToken,groups(email)'
  while i < len(sys.argv):
    if sys.argv[i].lower() == u'domain':
      usedomain = sys.argv[i+1].lower()
      customer = None
      i += 2
    elif sys.argv[i].lower() == u'todrive':
      todrive = True
      i += 1
    elif sys.argv[i].lower() == u'delimiter':
      listDelimiter = sys.argv[i+1]
      i += 2
    elif sys.argv[i].lower() == u'member':
      usemember = sys.argv[i+1].lower()
      customer = None
      i += 2
    elif sys.argv[i].lower() == u'name':
      fields += u',groups(name)'
      printname = True
      group_attributes[0].update(Name=u'Name')
      titles.append(u'Name')
      i += 1
    elif sys.argv[i].lower() == u'admincreated':
      fields += u',groups(adminCreated)'
      admin_created = True
      group_attributes[0].update(Admin_Created=u'Admin_Created')
      titles.append(u'Admin_Created')
      i += 1
    elif sys.argv[i].lower() == u'description':
      fields += u',groups(description)'
      group_attributes[0].update(Description=u'Description')
      titles.append(u'Description')
      printdesc = True
      i += 1
    elif sys.argv[i].lower() == u'id':
      fields += u',groups(id)'
      group_attributes[0].update(ID=u'ID')
      titles.append(u'ID')
      printid = True
      i += 1
    elif sys.argv[i].lower() == u'aliases':
      fields += u',groups(aliases,nonEditableAliases)'
      group_attributes[0].update(Aliases=u'Aliases')
      group_attributes[0].update(NonEditableAliases=u'NonEditableAliases')
      titles.append(u'Aliases')
      titles.append(u'NonEditableAliases')
      aliases = True
      i += 1
    elif sys.argv[i].lower() == u'members':
      group_attributes[0].update(Members=u'Members')
      titles.append(u'Members')
      members = True
      i += 1
    elif sys.argv[i].lower() == u'owners':
      group_attributes[0].update(Owners=u'Owners')
      titles.append(u'Owners')
      owners = True
      i += 1
    elif sys.argv[i].lower() == u'managers':
      group_attributes[0].update(Managers=u'Managers')
      titles.append(u'Managers')
      managers = True
      i += 1
    elif sys.argv[i].lower() == u'settings':
      settings = True
      i += 1
    else:
      showUsage()
      sys.exit(7)
  cd = buildGAPIObject(u'directory')
  printGettingMessage(u"Retrieving All Groups for Google Apps account (may take some time on a large account)...\n")
  page_message = getPageMessage(u'groups', showTotal=False, showFirstLastItems=True)
  all_groups = callGAPIpages(service=cd.groups(), function=u'list', items=u'groups', page_message=page_message,
                             message_attribute=u'email', customer=customer, domain=usedomain, userKey=usemember, fields=fields)
  total_groups = len(all_groups)
  count = 0
  for group_vals in all_groups:
    count += 1
    group = {}
    group.update({u'Email': group_vals[u'email']})
    if printname:
      try:
        group.update({u'Name': group_vals[u'name']})
      except KeyError:
        pass
    if printdesc:
      try:
        group.update({u'Description': group_vals[u'description']})
      except KeyError:
        pass
    if printid:
      try:
        group.update({u'ID': group_vals[u'id']})
      except KeyError:
        pass
    if admin_created:
      try:
        group.update({u'Admin_Created': group_vals[u'adminCreated']})
      except KeyError:
        pass
    if aliases:
      try:
        group.update({u'Aliases': ' '.join(group_vals[u'aliases'])})
      except KeyError:
        pass
      try:
        group.update({u'NonEditableAliases': ' '.join(group_vals[u'nonEditableAliases'])})
      except KeyError:
        pass
    if members or owners or managers:
      roles = list()
      if members:
        roles.append(u'members')
      if owners:
        roles.append(u'owners')
      if managers:
        roles.append(u'managers')
      roles = u','.join(roles)
      printGettingMessage(u' Getting %s for %s (%s of %s)\n' % (roles, group_vals[u'email'], count, total_groups))
      page_message = getPageMessage(u'members', showTotal=False, showFirstLastItems=True)
      all_group_members = callGAPIpages(service=cd.members(), function=u'list', items=u'members', page_message=page_message,
                                        message_attribute=u'email', groupKey=group_vals[u'email'], roles=roles, fields=u'nextPageToken,members(email,role)')
      if members:
        all_true_members = list()
      if managers:
        all_managers = list()
      if owners:
        all_owners = list()
      for member in all_group_members:
        try:
          member_email = member[u'email']
        except KeyError:
          sys.stderr.write(u' Not sure to do with: %s' % member)
          continue
        try:
          if members and member[u'role'] == u'MEMBER':
            all_true_members.append(member_email)
          elif managers and member[u'role'] == u'MANAGER':
            all_managers.append(member_email)
          elif owners and member[u'role'] == u'OWNER':
            all_owners.append(member_email)
        except KeyError:
          all_true_members.append(member_email)
      if members:
        group.update({u'Members': listDelimiter.join(all_true_members)})
      if managers:
        group.update({u'Managers': listDelimiter.join(all_managers)})
      if owners:
        group.update({u'Owners': listDelimiter.join(all_owners)})
    if settings:
      printGettingMessage(u" Retrieving Settings for group %s (%s of %s)...\r\n" % (group_vals[u'email'], count, total_groups))
      gs = buildGAPIObject(u'groupssettings')
      settings = callGAPI(service=gs.groups(), function=u'get', retry_reasons=[u'serviceLimit'], groupUniqueId=group_vals[u'email'])
      for key in settings.keys():
        if key in [u'email', u'name', u'description', u'kind', u'etag']:
          continue
        setting_value = settings[key]
        if setting_value == None:
          setting_value = u''
        if key not in titles:
          group_attributes[0][key] = key
          titles.append(key)
        group.update({key: setting_value})
    group_attributes.append(group)
  output_csv(group_attributes, titles, u'Groups', todrive)

def doPrintOrgs():
  i = 3
  printname = printdesc = printparent = printinherit = todrive = False
  listType = u'all'
  orgUnitPath = u"/"
  org_attributes = [{}]
  fields = u'organizationUnits(orgUnitPath)'
  titles = []
  while i < len(sys.argv):
    if sys.argv[i].lower() == u'allfields':
      fields = None
      i += 1
    elif sys.argv[i].lower() == u'name':
      printname = True
      org_attributes[0].update(Name=u'Name')
      fields += u',organizationUnits(name)'
      titles.append(u'Name')
      i += 1
    elif sys.argv[i].lower() == u'toplevelonly':
      listType = u'children'
      i += 1
    elif sys.argv[i].lower() == u'from_parent':
      orgUnitPath = sys.argv[i+1]
      i += 2
    elif sys.argv[i].lower() == u'todrive':
      todrive = True
      i += 1
    elif sys.argv[i].lower() == u'description':
      printdesc = True
      fields += u',organizationUnits(description)'
      org_attributes[0].update(Description=u'Description')
      titles.append(u'Description')
      i += 1
    elif sys.argv[i].lower() == u'parent':
      printparent = True
      fields += u',organizationUnits(parentOrgUnitPath)'
      org_attributes[0].update(Parent=u'Parent')
      titles.append(u'Parent')
      i += 1
    elif sys.argv[i].lower() == u'inherit':
      printinherit = True
      fields += u',organizationUnits(blockInheritance)'
      org_attributes[0].update(InheritanceBlocked=u'InheritanceBlocked')
      titles.append(u'InheritanceBlocked')
      i += 1
    else:
      showUsage()
      exit(8)
  if fields:
    org_attributes[0][u'Path'] = u'Path'
    titles.append(u'Path')
  cd = buildGAPIObject(u'directory')
  printGettingMessage(u"Retrieving All Organizational Units for your account (may take some time on large domain)...")
  orgs = callGAPI(service=cd.orgunits(), function=u'list', customerId=GC_Values[GC_CUSTOMER_ID], fields=fields, type=listType, orgUnitPath=orgUnitPath)
  printGettingMessage(u"done\n")
  if not u'organizationUnits' in orgs:
    print u'0 org units in this Google Apps instance...'
    return
  for org_vals in orgs[u'organizationUnits']:
    orgUnit = {}
    if not fields:
      orgUnit = flatten_json(org_vals)
      for row in orgUnit:
        if row not in titles:
          titles.append(row)
          org_attributes[0][row] = row
    else:
      orgUnit.update({u'Path': org_vals[u'orgUnitPath']})
      if printname:
        name = org_vals[u'name']
        if name == None:
          name = u''
        orgUnit.update({u'Name': name})
      if printdesc:
        try:
          desc = org_vals[u'description']
          if desc == None:
            desc = u''
        except KeyError:
          pass
        orgUnit.update({u'Description': desc})
      if printparent:
        parent = org_vals[u'parentOrgUnitPath']
        if parent == None:
          parent = ''
        orgUnit.update({u'Parent': parent})
      if printinherit:
        try:
          orgUnit.update({u'InheritanceBlocked': org_vals[u'blockInheritance']})
        except KeyError:
          pass
    org_attributes.append(orgUnit)
  output_csv(org_attributes, titles, u'Orgs', todrive)

def doPrintAliases():
  todrive = False
  i = 3
  while i < len(sys.argv):
    if sys.argv[i].lower() == u'todrive':
      todrive = True
    i += 1
  cd = buildGAPIObject(u'directory')
  alias_attributes = []
  alias_attributes.append({u'Alias': u'Alias'})
  alias_attributes[0].update(Target=u'Target')
  alias_attributes[0].update(TargetType=u'TargetType')
  titles = [u'Alias', u'Target', u'TargetType']
  printGettingMessage(u"Retrieving All User Aliases for %s organization (may take some time on large domain)...\n" % GC_Values[GC_DOMAIN])
  page_message = getPageMessage(u'users', showTotal=False, showFirstLastItems=True)
  all_users = callGAPIpages(service=cd.users(), function=u'list', items=u'users', page_message=page_message,
                            message_attribute=u'primaryEmail', customer=GC_Values[GC_CUSTOMER_ID], fields=u'users(primaryEmail,aliases),nextPageToken', maxResults=500)
  for user in all_users:
    try:
      for alias in user[u'aliases']:
        alias_attributes.append({u'Alias': alias, u'Target': user[u'primaryEmail'], u'TargetType': u'User'})
    except KeyError:
      continue
  printGettingMessage(u"Retrieving All User Aliases for %s organization (may take some time on large domain)...\n" % GC_Values[GC_DOMAIN])
  page_message = getPageMessage(u'groups', showTotal=False, showFirstLastItems=True)
  all_groups = callGAPIpages(service=cd.groups(), function=u'list', items=u'groups', page_message=page_message,
                             message_attribute=u'email', customer=GC_Values[GC_CUSTOMER_ID], fields=u'groups(email,aliases),nextPageToken')
  for group in all_groups:
    try:
      for alias in group[u'aliases']:
        alias_attributes.append({u'Alias': alias, u'Target': group[u'email'], u'TargetType': u'Group'})
    except KeyError:
      continue
  output_csv(alias_attributes, titles, u'Aliases', todrive)

def doPrintGroupMembers():
  todrive = all_groups = False
  i = 3
  while i < len(sys.argv):
    if sys.argv[i].lower() == u'todrive':
      todrive = True
      i += 1
    elif sys.argv[i].lower() == u'group':
      all_groups = [{u'email': sys.argv[i+1].lower()}]
      i += 2
    else:
      print 'Error: %s is not a valid argument to "gam print groups"' % sys.argv[i]
      sys.exit(3)
  cd = buildGAPIObject(u'directory')
  member_attributes = [{u'group': u'group'},]
  if not all_groups:
    all_groups = callGAPIpages(service=cd.groups(), function=u'list', items=u'groups', message_attribute=u'email', customer=GC_Values[GC_CUSTOMER_ID], fields=u'nextPageToken,groups(email)')
  total_groups = len(all_groups)
  i = 1
  for group in all_groups:
    group_email = group[u'email']
    printGettingMessage(u'Getting members for %s (%s/%s)\n' % (group_email, i, total_groups))
    group_members = callGAPIpages(service=cd.members(), function=u'list', items=u'members', message_attribute=u'email', groupKey=group_email)
    for member in group_members:
      member_attr = {u'group': group_email}
      for title in member.keys():
        if title in [u'kind', u'etag']:
          continue
        try:
          member_attributes[0][title]
        except KeyError:
          member_attributes[0][title] = title
        member_attr[title] = member[title]
      member_attributes.append(member_attr)
    i += 1
  titles = member_attributes[0].keys()
  output_csv(member_attributes, titles, u'Group Members', todrive)

def doPrintMobileDevices():
  cd = buildGAPIObject(u'directory')
  mobile_attributes = [{}]
  titles = []
  todrive = False
  query = orderBy = sortOrder = None
  i = 3
  while i < len(sys.argv):
    if sys.argv[i].lower() == u'query':
      query = sys.argv[i+1]
      i += 2
    elif sys.argv[i].lower() == u'todrive':
      todrive = True
      i += 1
    elif sys.argv[i].lower() == u'orderby':
      orderBy = sys.argv[i+1].lower()
      allowed_values = [u'deviceid', u'email', u'lastsync', u'model', u'name', u'os', u'status', u'type']
      if orderBy.lower() not in allowed_values:
        print u'Error: orderBy must be one of %s. Got %s' % (u', '.join(allowed_values), orderBy)
        sys.exit(3)
      elif orderBy == u'lastsync':
        orderBy = u'lastSync'
      elif orderBy == u'deviceid':
        orderBy = u'deviceId'
      i += 2
    elif sys.argv[i].lower() in [u'ascending', u'descending']:
      sortOrder = sys.argv[i].upper()
      i += 1
    else:
      print 'Error: %s is not a valid argument to "gam print mobile"' % sys.argv[i]
      sys.exit(3)
  printGettingMessage(u'Retrieving All Mobile Devices for organization (may take some time for large accounts)...\n')
  page_message = getPageMessage(u'mobile devices')
  all_mobile = callGAPIpages(service=cd.mobiledevices(), function=u'list', items=u'mobiledevices', page_message=page_message,
                             customerId=GC_Values[GC_CUSTOMER_ID], query=query, orderBy=orderBy, sortOrder=sortOrder)
  for mobile in all_mobile:
    mobiledevice = dict()
    for title in mobile.keys():
      try:
        if title in [u'kind', u'etag', u'applications']:
          continue
        try:
          mobile_attributes[0][title]
        except KeyError:
          mobile_attributes[0][title] = title
          titles.append(title)
        if title in [u'name', u'email']:
          mobiledevice[title] = mobile[title][0]
        else:
          mobiledevice[title] = mobile[title]
      except KeyError:
        pass
    mobile_attributes.append(mobiledevice)
  output_csv(mobile_attributes, titles, u'Mobile', todrive)

def doPrintCrosDevices():
  cd = buildGAPIObject(u'directory')
  cros_attributes = [{u'deviceId': u'deviceId'}]
  titles = [u'deviceId',]
  todrive = False
  query = projection = orderBy = sortOrder = None
  noLists = False
  selectAttrib = None
  i = 3
  while i < len(sys.argv):
    my_arg = sys.argv[i].lower().replace(u'_', u'')
    if my_arg == u'query':
      query = sys.argv[i+1]
      i += 2
    elif my_arg == u'todrive':
      todrive = True
      i += 1
    elif my_arg == u'nolists':
      noLists = True
      selectAttrib = None
      i += 1
    elif my_arg == u'recentusers':
      selectAttrib = u'recentUsers'
      noLists = False
      i += 1
    elif my_arg in [u'timeranges', u'activetimeranges']:
      selectAttrib = u'activeTimeRanges'
      noLists = False
      i += 1
    elif my_arg == u'orderby':
      orderBy = sys.argv[i+1].lower().replace(u'_', u'')
      allowed_values = [u'location', u'user', u'lastsync', u'notes', u'serialnumber', u'status', u'supportenddate']
      if orderBy not in allowed_values:
        print u'Error: orderBy must be one of %s. Got %s' % (u', '.join(allowed_values), orderBy)
        sys.exit(3)
      elif orderBy == u'location':
        orderBy = u'annotatedLocation'
      elif orderBy == u'user':
        orderBy = u'annotatedUser'
      elif orderBy == u'lastsync':
        orderBy = u'lastSync'
      elif orderBy == u'serialnumber':
        orderBy = u'serialNumber'
      elif orderBy == u'supportEndDate':
        orderBy = u'supportEndDate'
      i += 2
    elif my_arg in [u'ascending', u'descending']:
      sortOrder = my_arg.upper()
      i += 1
    elif my_arg in [u'basic', u'full']:
      projection = my_arg.upper()
      i += 1
    else:
      print 'Error: %s is not a valid argument to "gam print cros"' % sys.argv[i]
      sys.exit(3)
  if selectAttrib:
    projection = u'FULL'
  printGettingMessage(u'Retrieving All Chrome OS Devices for organization (may take some time for large accounts)...\n')
  page_message = getPageMessage(u'Chrome devices')
  all_cros = callGAPIpages(service=cd.chromeosdevices(), function=u'list', items=u'chromeosdevices', page_message=page_message,
                           query=query, customerId=GC_Values[GC_CUSTOMER_ID], projection=projection, orderBy=orderBy, sortOrder=sortOrder)
  if all_cros:
    if (not noLists) and (not selectAttrib):
      for cros in all_cros:
        cros_attributes.append(flatten_json(cros))
        for item in cros_attributes[-1]:
          if item not in cros_attributes[0]:
            cros_attributes[0][item] = item
            titles.append(item)
    else:
      attribMap = dict()
      for cros in all_cros:
        row = dict()
        for attrib in cros:
          if attrib in [u'kind', u'etag', u'recentUsers', u'activeTimeRanges']:
            continue
          if attrib not in cros_attributes[0]:
            cros_attributes[0][attrib] = attrib
            titles.append(attrib)
          row[attrib] = cros[attrib]
        if noLists or (selectAttrib not in cros) or (not cros[selectAttrib]):
          cros_attributes.append(row)
        else:
          if not attribMap:
            for attrib in cros[selectAttrib][0]:
              xattrib = u'%s.%s' % (selectAttrib, attrib)
              if xattrib not in cros_attributes[0]:
                cros_attributes[0][xattrib] = xattrib
                titles.append(xattrib)
              attribMap[attrib] = xattrib
          for item in cros[selectAttrib]:
            new_row = row.copy()
            for attrib in item:
              if isinstance(item[attrib], (bool, int)):
                new_row[attribMap[attrib]] = str(item[attrib])
              else:
                new_row[attribMap[attrib]] = item[attrib]
            cros_attributes.append(new_row)
  output_csv(cros_attributes, titles, 'CrOS', todrive)

def doPrintLicenses(return_list=False, skus=None):
  lic = buildGAPIObject(u'licensing')
  products = [u'Google-Apps', u'Google-Drive-storage', u'Google-Coordinate', u'Google-Vault']
  licenses = []
  lic_attributes = [{}]
  todrive = False
  i = 3
  while i < len(sys.argv) and not return_list:
    if sys.argv[i].lower() == u'todrive':
      todrive = True
      i += 1
    elif sys.argv[i].lower() in [u'products', u'product']:
      products = sys.argv[i+1].split(',')
      i += 2
    elif sys.argv[i].lower() in [u'sku', u'skus']:
      skus = sys.argv[i+1].split(',')
      i += 2
    else:
      print u'Error: %s is not a valid argument to gam print licenses' % sys.argv[i]
      sys.exit(3)
  if skus:
    for sku in skus:
      product, sku = getProductAndSKU(sku)
      page_message = getPageMessage(u'Licenses', forWhom=sku)
      try:
        licenses += callGAPIpages(service=lic.licenseAssignments(), function=u'listForProductAndSku', throw_reasons=[u'invalid', u'forbidden'],
                                  page_message=page_message, customerId=GC_Values[GC_DOMAIN], productId=product, skuId=sku, fields=u'items(productId,skuId,userId),nextPageToken')
      except googleapiclient.errors.HttpError:
        licenses += []
  else:
    for productId in products:
      page_message = getPageMessage(u'Licenses', forWhom=productId)
      try:
        licenses += callGAPIpages(service=lic.licenseAssignments(), function=u'listForProduct', throw_reasons=[u'invalid', u'forbidden'],
                                  page_message=page_message, customerId=GC_Values[GC_DOMAIN], productId=productId, fields=u'items(productId,skuId,userId),nextPageToken')
      except googleapiclient.errors.HttpError:
        licenses = +[]
  for u_license in licenses:
    a_license = dict()
    for title in u_license:
      if title in [u'kind', u'etags', u'selfLink']:
        continue
      if title not in lic_attributes[0]:
        lic_attributes[0][title] = title
      a_license[title] = u_license[title]
    lic_attributes.append(a_license)
  if return_list:
    return lic_attributes
  output_csv(lic_attributes, lic_attributes[0], u'Licenses', todrive)

def doPrintTokens():
  todrive = False
  i = 3
  entity_type = u'all'
  entity = u'users'
  while i < len(sys.argv):
    if sys.argv[i].lower() == u'todrive':
      todrive = True
      i += 1
    elif sys.argv[i].lower() in usergroup_types:
      entity_type = sys.argv[i].lower()
      entity = sys.argv[i+1].lower()
      i += 2
  cd = buildGAPIObject(u'directory')
  all_users = getUsersToModify(entity_type=entity_type, entity=entity, silent=False)
  titles = [u'user', u'displayText', u'clientId', u'nativeApp', u'anonymous', u'scopes']
  token_attributes = [{}]
  for title in titles:
    token_attributes[0][title] = title
  for user in all_users:
    printGettingMessage(u' getting tokens for %s\n' % user)
    user_tokens = callGAPI(service=cd.tokens(), function='list', userKey=user)
    try:
      for user_token in user_tokens[u'items']:
        this_token = dict()
        this_token[u'user'] = user
        this_token[u'scopes'] = ' '.join(user_token[u'scopes'])
        for token_item in user_token.keys():
          if token_item in [u'kind', u'etag', u'scopes']:
            continue
          this_token[token_item] = user_token[token_item]
          if token_item not in titles:
            titles.append(token_item)
            token_attributes[0][token_item] = token_item
        token_attributes.append(this_token)
    except KeyError:
      pass
  output_csv(token_attributes, titles, u'OAuth Tokens', todrive)

def doPrintResources():
  i = 3
  res_attributes = []
  res_attributes.append({u'Name': u'Name'})
  titles = ['Name']
  printid = printdesc = printemail = todrive = False
  while i < len(sys.argv):
    if sys.argv[i].lower() == u'allfields':
      printid = printdesc = printemail = True
      res_attributes[0].update(ID=u'ID', Description=u'Description', Email=u'Email')
      titles.append(u'ID')
      titles.append(u'Description')
      titles.append(u'Email')
      i += 1
    elif sys.argv[i].lower() == u'todrive':
      todrive = True
      i += 1
    elif sys.argv[i].lower() == u'id':
      printid = True
      res_attributes[0].update(ID=u'ID')
      titles.append(u'ID')
      i += 1
    elif sys.argv[i].lower() == u'description':
      printdesc = True
      res_attributes[0].update(Description=u'Description')
      titles.append(u'Description')
      i += 1
    elif sys.argv[i].lower() == u'email':
      printemail = True
      res_attributes[0].update(Email=u'Email')
      titles.append(u'Email')
      i += 1
    else:
      showUsage()
      sys.exit(2)
  resObj = getResCalObject()
  printGettingMessage(u"Retrieving All Resource Calendars for your account (may take some time on a large domain)")
  resources = callGData(service=resObj, function=u'RetrieveAllResourceCalendars')
  for resource in resources:
    resUnit = {}
    resUnit.update({u'Name': resource[u'resourceCommonName']})
    if printid:
      resUnit.update({u'ID': resource[u'resourceId']})
    if printdesc:
      try:
        desc = resource[u'resourceDescription']
      except KeyError:
        desc = ''
      resUnit.update({u'Description': desc})
    if printemail:
      resUnit.update({u'Email': resource[u'resourceEmail']})
    res_attributes.append(resUnit)
  output_csv(res_attributes, titles, u'Resources', todrive)

def doCreateMonitor():
  source_user = sys.argv[4].lower()
  destination_user = sys.argv[5].lower()
  #end_date defaults to 30 days in the future...
  end_date = (datetime.datetime.now() + datetime.timedelta(days=30)).strftime(u"%Y-%m-%d %H:%M")
  begin_date = None
  incoming_headers_only = outgoing_headers_only = drafts_headers_only = chats_headers_only = False
  drafts = chats = True
  i = 6
  while i < len(sys.argv):
    if sys.argv[i].lower() == u'end':
      end_date = sys.argv[i+1]
      i += 2
    elif sys.argv[i].lower() == u'begin':
      begin_date = sys.argv[i+1]
      i += 2
    elif sys.argv[i].lower() == u'incoming_headers':
      incoming_headers_only = True
      i += 1
    elif sys.argv[i].lower() == u'outgoing_headers':
      outgoing_headers_only = True
      i += 1
    elif sys.argv[i].lower() == u'nochats':
      chats = False
      i += 1
    elif sys.argv[i].lower() == u'nodrafts':
      drafts = False
      i += 1
    elif sys.argv[i].lower() == u'chat_headers':
      chats_headers_only = True
      i += 1
    elif sys.argv[i].lower() == u'draft_headers':
      drafts_headers_only = True
      i += 1
    else:
      showUsage()
      sys.exit(2)
  audit = getAuditObject()
  if source_user.find('@') > 0:
    audit.domain = source_user[source_user.find(u'@')+1:]
    source_user = source_user[:source_user.find(u'@')]
  callGData(service=audit, function=u'createEmailMonitor', source_user=source_user, destination_user=destination_user, end_date=end_date, begin_date=begin_date,
            incoming_headers_only=incoming_headers_only, outgoing_headers_only=outgoing_headers_only,
            drafts=drafts, drafts_headers_only=drafts_headers_only, chats=chats, chats_headers_only=chats_headers_only)

def doShowMonitors():
  user = sys.argv[4].lower()
  audit = getAuditObject()
  if user.find('@') > 0:
    audit.domain = user[user.find(u'@')+1:]
    user = user[:user.find(u'@')]
  results = callGData(service=audit, function=u'getEmailMonitors', user=user)
  print sys.argv[4].lower()+u' has the following monitors:'
  print u''
  for monitor in results:
    print u' Destination: '+monitor['destUserName']
    try:
      print u'  Begin: '+monitor['beginDate']
    except KeyError:
      print u'  Begin: immediately'
    print u'  End: '+monitor['endDate']
    print u'  Monitor Incoming: '+monitor['outgoingEmailMonitorLevel']
    print u'  Monitor Outgoing: '+monitor['incomingEmailMonitorLevel']
    print u'  Monitor Chats: '+monitor['chatMonitorLevel']
    print u'  Monitor Drafts: '+monitor['draftMonitorLevel']
    print u''

def doDeleteMonitor():
  source_user = sys.argv[4].lower()
  destination_user = sys.argv[5].lower()
  audit = getAuditObject()
  if source_user.find(u'@') > 0:
    audit.domain = source_user[source_user.find(u'@')+1:]
    source_user = source_user[:source_user.find(u'@')]
  callGData(service=audit, function=u'deleteEmailMonitor', source_user=source_user, destination_user=destination_user)

def doRequestActivity():
  user = sys.argv[4].lower()
  audit = getAuditObject()
  if user.find('@') > 0:
    audit.domain = user[user.find(u'@')+1:]
    user = user[:user.find('@')]
  results = callGData(service=audit, function=u'createAccountInformationRequest', user=user)
  print u'Request successfully submitted:'
  print u' Request ID: '+results[u'requestId']
  print u' User: '+results[u'userEmailAddress']
  print u' Status: '+results[u'status']
  print u' Request Date: '+results[u'requestDate']
  print u' Requested By: '+results[u'adminEmailAddress']

def doStatusActivityRequests():
  audit = getAuditObject()
  try:
    user = sys.argv[4].lower()
    if user.find(u'@') > 0:
      audit.domain = user[user.find('@')+1:]
      user = user[:user.find(u'@')]
    request_id = sys.argv[5].lower()
    results = callGData(service=audit, function=u'getAccountInformationRequestStatus', user=user, request_id=request_id)
    print u''
    print u'  Request ID: '+results[u'requestId']
    print u'  User: '+results[u'userEmailAddress']
    print u'  Status: '+results[u'status']
    print u'  Request Date: '+results[u'requestDate']
    print u'  Requested By: '+results[u'adminEmailAddress']
    try:
      print u'  Number Of Files: '+results[u'numberOfFiles']
      for i in range(int(results[u'numberOfFiles'])):
        print u'  Url%s: %s' % (i, results[u'fileUrl%s' % i])
    except KeyError:
      pass
    print ''
  except IndexError:
    results = callGData(service=audit, function=u'getAllAccountInformationRequestsStatus')
    print u'Current Activity Requests:'
    print u''
    for request in results:
      print u' Request ID: '+request[u'requestId']
      print u'  User: '+request[u'userEmailAddress']
      print u'  Status: '+request[u'status']
      print u'  Request Date: '+request[u'requestDate']
      print u'  Requested By: '+request[u'adminEmailAddress']
      try:
        print u'  Number Of Files: '+request[u'numberOfFiles']
        for i in range(int(request[u'numberOfFiles'])):
          print u'  Url%s: %s' % (i, request[u'fileUrl%s' % i])
      except KeyError:
        pass
      print u''

def doDownloadActivityRequest():
  user = sys.argv[4].lower()
  request_id = sys.argv[5].lower()
  audit = getAuditObject()
  if user.find(u'@') > 0:
    audit.domain = user[user.find(u'@')+1:]
    user = user[:user.find(u'@')]
  results = callGData(service=audit, function=u'getAccountInformationRequestStatus', user=user, request_id=request_id)
  if results[u'status'] != u'COMPLETED':
    print u'Request needs to be completed before downloading, current status is: '+results[u'status']
    sys.exit(4)
  try:
    if int(results[u'numberOfFiles']) < 1:
      print u'ERROR: Request completed but no results were returned, try requesting again'
      sys.exit(4)
  except KeyError:
    print u'ERROR: Request completed but no files were returned, try requesting again'
    sys.exit(4)
  for i in range(0, int(results[u'numberOfFiles'])):
    url = results[u'fileUrl'+str(i)]
    filename = u'activity-'+user+'-'+request_id+'-'+unicode(i)+u'.txt.gpg'
    print u'Downloading '+filename+u' ('+unicode(i+1)+u' of '+results[u'numberOfFiles']+')'
    geturl(url, filename)

def doRequestExport():
  begin_date = end_date = search_query = None
  headers_only = include_deleted = False
  user = sys.argv[4].lower()
  i = 5
  while i < len(sys.argv):
    if sys.argv[i].lower() == u'begin':
      begin_date = sys.argv[i+1]
      i += 2
    elif sys.argv[i].lower() == u'end':
      end_date = sys.argv[i+1]
      i += 2
    elif sys.argv[i].lower() == u'search':
      search_query = sys.argv[i+1]
      i += 2
    elif sys.argv[i].lower() == u'headersonly':
      headers_only = True
      i += 1
    elif sys.argv[i].lower() == u'includedeleted':
      include_deleted = True
      i += 1
    else:
      showUsage()
      sys.exit(2)
  audit = getAuditObject()
  if user.find('@') > 0:
    audit.domain = user[user.find(u'@')+1:]
    user = user[:user.find(u'@')]
  results = callGData(service=audit, function=u'createMailboxExportRequest', user=user, begin_date=begin_date, end_date=end_date, include_deleted=include_deleted,
                      search_query=search_query, headers_only=headers_only)
  print u'Export request successfully submitted:'
  print u' Request ID: '+results['requestId']
  print u' User: '+results['userEmailAddress']
  print u' Status: '+results['status']
  print u' Request Date: '+results['requestDate']
  print u' Requested By: '+results['adminEmailAddress']
  print u' Include Deleted: '+results['includeDeleted']
  print u' Requested Parts: '+results['packageContent']
  try:
    print u' Begin: '+results['beginDate']
  except KeyError:
    print u' Begin: account creation date'
  try:
    print u' End: '+results['endDate']
  except KeyError:
    print u' End: export request date'

def doDeleteExport():
  audit = getAuditObject()
  user = sys.argv[4].lower()
  if user.find(u'@') > 0:
    audit.domain = user[user.find(u'@')+1:]
    user = user[:user.find(u'@')]
  request_id = sys.argv[5].lower()
  callGData(service=audit, function=u'deleteMailboxExportRequest', user=user, request_id=request_id)

def doDeleteActivityRequest():
  audit = getAuditObject()
  user = sys.argv[4].lower()
  if user.find(u'@') > 0:
    audit.domain = user[user.find(u'@')+1:]
    user = user[:user.find(u'@')]
  request_id = sys.argv[5].lower()
  callGData(service=audit, function=u'deleteAccountInformationRequest', user=user, request_id=request_id)

def doStatusExportRequests():
  audit = getAuditObject()
  try:
    user = sys.argv[4].lower()
    if user.find(u'@') > 0:
      audit.domain = user[user.find(u'@')+1:]
      user = user[:user.find(u'@')]
    request_id = sys.argv[5].lower()
    results = callGData(service=audit, function=u'getMailboxExportRequestStatus', user=user, request_id=request_id)
    print u''
    print u'  Request ID: '+results[u'requestId']
    print u'  User: '+results[u'userEmailAddress']
    print u'  Status: '+results[u'status']
    print u'  Request Date: '+results[u'requestDate']
    print u'  Requested By: '+results[u'adminEmailAddress']
    print u'  Requested Parts: '+results[u'packageContent']
    try:
      print u'  Request Filter: '+results[u'searchQuery']
    except KeyError:
      print u'  Request Filter: None'
    print u'  Include Deleted: '+results[u'includeDeleted']
    try:
      print u'  Number Of Files: '+results[u'numberOfFiles']
      for i in range(int(results[u'numberOfFiles'])):
        print u'  Url%s: %s' % (i, results[u'fileUrl%s' % i])
    except KeyError:
      pass
  except IndexError:
    results = callGData(service=audit, function=u'getAllMailboxExportRequestsStatus')
    print u'Current Export Requests:'
    print u''
    for request in results:
      print u' Request ID: '+request[u'requestId']
      print u'  User: '+request[u'userEmailAddress']
      print u'  Status: '+request[u'status']
      print u'  Request Date: '+request[u'requestDate']
      print u'  Requested By: '+request[u'adminEmailAddress']
      print u'  Requested Parts: '+request[u'packageContent']
      try:
        print u'  Request Filter: '+request[u'searchQuery']
      except KeyError:
        print u'  Request Filter: None'
      print u'  Include Deleted: '+request[u'includeDeleted']
      try:
        print u'  Number Of Files: '+request[u'numberOfFiles']
      except KeyError:
        pass
      print u''

def doWatchExportRequest():
  audit = getAuditObject()
  user = sys.argv[4].lower()
  if user.find(u'@') > 0:
    audit.domain = user[user.find(u'@')+1:]
    user = user[:user.find(u'@')]
  request_id = sys.argv[5].lower()
  while True:
    results = callGData(service=audit, function=u'getMailboxExportRequestStatus', user=user, request_id=request_id)
    if results[u'status'] != u'PENDING':
      print u'status is %s. Sending email.' % results[u'status']
      msg_txt = u"\n"
      msg_txt += u"  Request ID: %s\n" % results[u'requestId']
      msg_txt += u"  User: %s\n" % results[u'userEmailAddress']
      msg_txt += u"  Status: %s\n" % results[u'status']
      msg_txt += u"  Request Date: %s\n" % results[u'requestDate']
      msg_txt += u"  Requested By: %s\n" % results[u'adminEmailAddress']
      msg_txt += u"  Requested Parts: %s\n" % results[u'packageContent']
      try:
        msg_txt += u"  Request Filter: %s\n" % results[u'searchQuery']
      except KeyError:
        msg_txt += u"  Request Filter: None\n"
      msg_txt += u"  Include Deleted: %s\n" % results[u'includeDeleted']
      try:
        msg_txt += u"  Number Of Files: %s\n" % results[u'numberOfFiles']
        for i in range(int(results['numberOfFiles'])):
          msg_txt += u"  Url%s: %s\n" % (i, results[u'fileUrl%s' % i])
      except KeyError:
        pass
      msg_subj = u'Export #%s for %s status is %s' % (results[u'requestId'], results[u'userEmailAddress'], results[u'status'])
      send_email(msg_subj, msg_txt)
      break
    else:
      print u'status still PENDING, will check again in 5 minutes...'
      time.sleep(300)

def send_email(msg_subj, msg_txt, msg_rcpt=None):
  from email.mime.text import MIMEText
  gmail = buildGAPIObject(u'gmail')
  sender_email = gmail._http.request.credentials.id_token[u'email']
  if not msg_rcpt:
    msg_rcpt = sender_email
  msg = MIMEText(msg_txt)
  msg[u'Subject'] = msg_subj
  msg[u'From'] = sender_email
  msg[u'To'] = msg_rcpt
  msg_string = msg.as_string()
  msg_raw = base64.urlsafe_b64encode(msg_string)
  callGAPI(service=gmail.users().messages(), function=u'send', userId=sender_email, body={u'raw': msg_raw})

def doDownloadExportRequest():
  user = sys.argv[4].lower()
  request_id = sys.argv[5].lower()
  audit = getAuditObject()
  if user.find(u'@') > 0:
    audit.domain = user[user.find(u'@')+1:]
    user = user[:user.find(u'@')]
  results = callGData(service=audit, function=u'getMailboxExportRequestStatus', user=user, request_id=request_id)
  if results[u'status'] != u'COMPLETED':
    print u'Request needs to be completed before downloading, current status is: '+results[u'status']
    sys.exit(4)
  try:
    if int(results[u'numberOfFiles']) < 1:
      print u'ERROR: Request completed but no results were returned, try requesting again'
      sys.exit(4)
  except KeyError:
    print u'ERROR: Request completed but no files were returned, try requesting again'
    sys.exit(4)
  for i in range(0, int(results['numberOfFiles'])):
    url = results[u'fileUrl'+str(i)]
    filename = u'export-'+user+'-'+request_id+'-'+str(i)+u'.mbox.gpg'
    #don't download existing files. This does not check validity of existing local
    #file so partial/corrupt downloads will need to be deleted manually.
    if os.path.isfile(filename):
      continue
    print u'Downloading '+filename+u' ('+unicode(i+1)+u' of '+results[u'numberOfFiles']+')'
    geturl(url, filename)

def doUploadAuditKey():
  auditkey = sys.stdin.read()
  audit = getAuditObject()
  callGData(service=audit, function=u'updatePGPKey', pgpkey=auditkey)

def getUsersToModify(entity_type=None, entity=None, silent=False, return_uids=False, member_type=None):
  got_uids = False
  if entity_type == None:
    entity_type = sys.argv[1].lower()
  if entity == None:
    entity = sys.argv[2]
  cd = buildGAPIObject(u'directory')
  if entity_type == u'user':
    users = [entity,]
  elif entity_type == u'users':
    users = entity.replace(u',', u' ').split()
  elif entity_type == u'group':
    got_uids = True
    group = entity
    if member_type == None:
      member_type_message = u'all members'
    else:
      member_type_message = u'%ss' % member_type.lower()
    if group.find(u'@') == -1:
      group = u'%s@%s' % (group, GC_Values[GC_DOMAIN])
    if not silent:
      printGettingMessage(u"Getting %s of %s (may take some time for large groups)..." % (member_type_message, group))
    page_message = getPageMessage(member_type_message, noNL=True)
    members = callGAPIpages(service=cd.members(), function=u'list', items=u'members', page_message=page_message, groupKey=group, roles=member_type, fields=u'nextPageToken,members(email,id)')
    users = []
    for member in members:
      if return_uids:
        users.append(member[u'id'])
      else:
        users.append(member[u'email'])
  elif entity_type in [u'ou', u'org']:
    got_uids = True
    ou = entity
    if ou[0] != u'/':
      ou = u'/%s' % ou
    users = []
    if not silent:
      printGettingMessage(u"Getting all users in the Google Apps organization (may take some time on a large domain)...\n")
    page_message = getPageMessage(u'users', noNL=True)
    members = callGAPIpages(service=cd.users(), function=u'list', items=u'users', page_message=page_message,
                            customer=GC_Values[GC_CUSTOMER_ID], fields=u'nextPageToken,users(primaryEmail,id,orgUnitPath)',
                            query=u"orgUnitPath='%s'" % ou, maxResults=500)
    for member in members:
      if ou.lower() != member[u'orgUnitPath'].lower():
        continue
      if return_uids:
        users.append(member[u'id'])
      else:
        users.append(member[u'primaryEmail'])
    if not silent:
      printGettingMessage(u"%s users are directly in the OU.\n" % len(users))
  elif entity_type in [u'ou_and_children', u'ou_and_child']:
    got_uids = True
    ou = entity
    if ou[0] != u'/':
      ou = u'/%s' % ou
    users = []
    if not silent:
      printGettingMessage(u"Getting all users in the Google Apps organization (may take some time on a large domain)...\n")
    page_message = getPageMessage(u'users', noNL=True)
    members = callGAPIpages(service=cd.users(), function=u'list', items=u'users', page_message=page_message,
                            customer=GC_Values[GC_CUSTOMER_ID], fields=u'nextPageToken,users(primaryEmail,id)', query=u"orgUnitPath='%s'" % ou, maxResults=500)
    for member in members:
      if return_uids:
        users.append(member[u'id'])
      else:
        users.append(member[u'primaryEmail'])
    if not silent:
      printGettingMessage(u"done.\r\n")
  elif entity_type in [u'query',]:
    got_uids = True
    users = []
    if not silent:
      printGettingMessage(u"Getting all users that match query %s (may take some time on a large domain)...\n" % entity)
    page_message = getPageMessage(u'users', noNL=True)
    members = callGAPIpages(service=cd.users(), function=u'list', items=u'users', page_message=page_message,
                            customer=GC_Values[GC_CUSTOMER_ID], fields=u'nextPageToken,users(primaryEmail,id)', query=entity, maxResults=500)
    for member in members:
      if return_uids:
        users.append(member[u'id'])
      else:
        users.append(member[u'primaryEmail'])
    if not silent:
      printGettingMessage(u"done.\r\n")
  elif entity_type in [u'license', u'licenses', u'licence', u'licences']:
    users = []
    licenses = doPrintLicenses(return_list=True, skus=entity.split(u','))
    for row in licenses[1:]: # skip header
      try:
        users.append(row[u'userId'])
      except KeyError:
        pass
  elif entity_type == u'file':
    users = []
    filename = entity
    usernames = csv.reader(open(filename, 'rU'))
    for row in usernames:
      try:
        users.append(row.pop())
      except IndexError:
        pass
  elif entity_type in [u'courseparticipants', u'teachers', u'students']:
    croom = buildGAPIObject(u'classroom')
    users = []
    if not entity.isdigit() and entity[:2] != u'd:':
      entity = u'd:%s' % entity
    if entity_type in [u'courseparticipants', u'teachers']:
      page_message = getPageMessage(u'teachers', noNL=True)
      teachers = callGAPIpages(service=croom.courses().teachers(), function=u'list', items=u'teachers', page_message=page_message, courseId=entity)
      for teacher in teachers:
        users.append(teacher[u'profile'][u'emailAddress'])
    if entity_type in [u'courseparticipants', u'students']:
      page_message = getPageMessage(u'students', noNL=True)
      students = callGAPIpages(service=croom.courses().students(), function=u'list',
                               page_message=page_message, items=u'students', courseId=entity)
      for student in students:
        users.append(student[u'profile'][u'emailAddress'])
  elif entity_type == u'all':
    got_uids = True
    users = []
    if entity == u'users':
      if not silent:
        printGettingMessage(u"Getting all users in Google Apps account (may take some time on a large account)...\n")
      page_message = getPageMessage(u'users', noNL=True)
      all_users = callGAPIpages(service=cd.users(), function=u'list', items=u'users', page_message=page_message,
                                customer=GC_Values[GC_CUSTOMER_ID], fields=u'nextPageToken,users(primaryEmail,suspended,id)', maxResults=500)
      for member in all_users:
        if member[u'suspended'] == False:
          if return_uids:
            users.append(member[u'id'])
          else:
            users.append(member[u'primaryEmail'])
      if not silent:
        printGettingMessage(u"done getting %s users.\r\n" % len(users))
    elif entity == u'cros':
      if not silent:
        printGettingMessage(u"Getting all CrOS devices in Google Apps account (may take some time on a large account)...\n")
      all_cros = callGAPIpages(service=cd.chromeosdevices(), function=u'list', items=u'chromeosdevices',
                               customerId=GC_Values[GC_CUSTOMER_ID], fields=u'nextPageToken,chromeosdevices(deviceId)')
      for member in all_cros:
        users.append(member[u'deviceId'])
      if not silent:
        printGettingMessage(u"done getting %s CrOS devices.\r\n" % len(users))
  else:
    showUsage()
    sys.exit(2)
  full_users = list()
  if entity != u'cros' and not got_uids:
    for user in users:
      if user[:4] == u'uid:':
        full_users.append(user[4:])
      elif user.find(u'@') == -1:
        full_users.append(u'%s@%s' % (user, GC_Values[GC_DOMAIN]))
      else:
        full_users.append(user)
  else:
    full_users = users
  if return_uids and not got_uids:
    new_full_users = list()
    for user in full_users:
      user_result = callGAPI(service=cd.users(), function=u'get', userKey=user, fields=u'id')
      new_full_users.append(user_result[u'id'])
    full_users = new_full_users
  return full_users

def OAuthInfo():
  try:
    access_token = sys.argv[3]
  except IndexError:
    storage = oauth2client.file.Storage(GC_Values[GC_OAUTH2_TXT])
    credentials = storage.get()
    if credentials is None or credentials.invalid:
      doRequestOAuth()
      credentials = storage.get()
    credentials.user_agent = u'GAM %s - http://git.io/gam / %s / Python %s.%s.%s %s / %s %s /' % (__version__, __author__,
                                                                                                  sys.version_info[0], sys.version_info[1], sys.version_info[2],
                                                                                                  sys.version_info[3], platform.platform(), platform.machine())
    http = httplib2.Http(ca_certs=GC_Values[GC_CACERT_PEM],
                         disable_ssl_certificate_validation=GC_Values[GC_NO_VERIFY_SSL])
    if credentials.access_token_expired:
      credentials.refresh(http)
    access_token = credentials.access_token
    print u"\nOAuth File: %s" % GC_Values[GC_OAUTH2_TXT]
  oa2 = buildGAPIObject(u'oauth2')
  token_info = callGAPI(service=oa2, function=u'tokeninfo', access_token=access_token)
  print u"Client ID: %s" % token_info[u'issued_to']
  try:
    print u"Secret: %s" % credentials.client_secret
  except UnboundLocalError:
    pass
  print u'Scopes:'
  for scope in token_info[u'scope'].split(u' '):
    print u'  %s' % scope
  try:
    print u'Google Apps Admin: %s' % token_info[u'email']
  except KeyError:
    print u'Google Apps Admin: Unknown'

def doDeleteOAuth():
  storage = oauth2client.file.Storage(GC_Values[GC_OAUTH2_TXT])
  credentials = storage.get()
  try:
    credentials.revoke_uri = oauth2client.GOOGLE_REVOKE_URI
  except AttributeError:
    print u'Error: Authorization doesn\'t exist'
    sys.exit(1)
  http = httplib2.Http(ca_certs=GC_Values[GC_CACERT_PEM],
                       disable_ssl_certificate_validation=GC_Values[GC_NO_VERIFY_SSL])
  sys.stderr.write(u'This OAuth token will self-destruct in 3...')
  time.sleep(1)
  sys.stderr.write(u'2...')
  time.sleep(1)
  sys.stderr.write(u'1...')
  time.sleep(1)
  sys.stderr.write(u'boom!\n')
  try:
    credentials.revoke(http)
  except oauth2client.client.TokenRevokeError, e:
    print u'Error: %s' % e.message
    os.remove(GC_Values[GC_OAUTH2_TXT])

class cmd_flags(object):
  def __init__(self):
    self.short_url = True
    self.noauth_local_webserver = False
    self.logging_level = u'ERROR'
    self.auth_host_name = u'localhost'
    self.auth_host_port = [8080, 9090]

possible_scopes = [u'https://www.googleapis.com/auth/admin.directory.group',            # Groups Directory Scope
                   u'https://www.googleapis.com/auth/admin.directory.orgunit',          # Organization Directory Scope
                   u'https://www.googleapis.com/auth/admin.directory.user',             # Users Directory Scope
                   u'https://www.googleapis.com/auth/admin.directory.device.chromeos',  # Chrome OS Devices Directory Scope
                   u'https://www.googleapis.com/auth/admin.directory.device.mobile',    # Mobile Device Directory Scope
                   u'https://apps-apis.google.com/a/feeds/emailsettings/2.0/',          # Email Settings API
                   u'https://apps-apis.google.com/a/feeds/calendar/resource/',          # Calendar Resource API
                   u'https://apps-apis.google.com/a/feeds/compliance/audit/',           # Email Audit API
                   u'https://apps-apis.google.com/a/feeds/domain/',                     # Admin Settings API
                   u'https://www.googleapis.com/auth/apps.groups.settings',             # Group Settings API
                   u'https://www.googleapis.com/auth/calendar',                         # Calendar Data API
                   u'https://www.googleapis.com/auth/admin.reports.audit.readonly',     # Audit Reports
                   u'https://www.googleapis.com/auth/admin.reports.usage.readonly',     # Usage Reports
                   u'https://www.googleapis.com/auth/drive.file',                       # Drive API - Admin user access to files created or opened by the app
                   u'https://www.googleapis.com/auth/apps.licensing',                   # License Manager API
                   u'https://www.googleapis.com/auth/admin.directory.user.security',    # User Security Directory API
                   u'https://www.googleapis.com/auth/admin.directory.notifications',    # Notifications Directory API
                   u'https://www.googleapis.com/auth/siteverification',                 # Site Verification API
                   u'https://mail.google.com/',                                         # IMAP/SMTP authentication for admin notifications
                   u'https://www.googleapis.com/auth/admin.directory.userschema',       # Customer User Schema
                   u'https://www.googleapis.com/auth/classroom.rosters https://www.googleapis.com/auth/classroom.courses https://www.googleapis.com/auth/classroom.profile.emails https://www.googleapis.com/auth/classroom.profile.photos',          # Classroom API
                   u'https://www.googleapis.com/auth/cloudprint']			  # Cloudprint API

def doRequestOAuth(incremental_auth=False):
  MISSING_CLIENT_SECRETS_MESSAGE = u"""
WARNING: Please configure OAuth 2.0

To make GAM run you will need to populate the {0} file
found at:

   {1}

with information from the APIs Console <https://cloud.google.com/console>.

See:

https://github.com/jay0lee/GAM/wiki/CreatingClientSecretsFile

for instructions.

""".format(FN_CLIENT_SECRETS_JSON, GC_Values[GC_CLIENT_SECRETS_JSON])

  menu = u'''Select the authorized scopes for this token. Include a 'r' to grant read-only
access or an 'a' to grant action-only access.

[%s]  0)  Group Directory API (supports read-only)
[%s]  1)  Organizational Unit Directory API (supports read-only)
[%s]  2)  User Directory API (supports read-only)
[%s]  3)  Chrome OS Device Directory API (supports read-only)
[%s]  4)  Mobile Device Directory API (supports read-only and action)
[%s]  5)  User Email Settings API
[%s]  6)  Calendar Resources API
[%s]  7)  Audit Monitors, Activity and Mailbox Exports API
[%s]  8)  Admin Settings API
[%s]  9)  Groups Settings API
[%s] 10)  Calendar Data API (supports read-only)
[%s] 11)  Audit Reports API
[%s] 12)  Usage Reports API
[%s] 13)  Drive API (create report documents for admin user only)
[%s] 14)  License Manager API
[%s] 15)  User Security Directory API
[%s] 16)  Notifications Directory API
[%s] 17)  Site Verification API
[%s] 18)  IMAP/SMTP Access (send notifications to admin)
[%s] 19)  User Schemas (supports read-only)
[%s] 20)  Classroom API
[%s] 21)  Cloud Print API

     %s)  Select all scopes
     %s)  Unselect all scopes
     %s)  Continue
'''
  num_scopes = len(possible_scopes)
  selected_scopes = [u'*'] * num_scopes
  select_all_scopes = unicode(str(num_scopes))
  unselect_all_scopes = unicode(str(num_scopes+1))
  authorize_scopes = unicode(str(num_scopes+2))
  scope_choices = (select_all_scopes, unselect_all_scopes, authorize_scopes)

  os.system([u'clear', u'cls'][os.name == u'nt'])
  while True:
    menu_fill = tuple(selected_scopes)+scope_choices
    selection = raw_input(menu % menu_fill)
    try:
      if selection.lower().find(u'r') != -1:
        selection = int(selection.lower().replace(u'r', u''))
        if selection not in [0, 1, 2, 3, 4, 10, 19]:
          os.system([u'clear', u'cls'][os.name == u'nt'])
          print u'THAT SCOPE DOES NOT SUPPORT READ-ONLY MODE!\n'
          continue
        selected_scopes[selection] = u'R'
      elif selection.lower().find(u'a') != -1:
        selection = int(selection.lower().replace(u'a', u''))
        if selection not in [4,]:
          os.system([u'clear', u'cls'][os.name == u'nt'])
          print u'THAT SCOPE DOES NOT SUPPORT ACTION-ONLY MODE!\n'
          continue
        selected_scopes[selection] = u'A'
      elif int(selection) > -1 and int(selection) < num_scopes:
        if selected_scopes[int(selection)] == u' ':
          selected_scopes[int(selection)] = u'*'
        else:
          selected_scopes[int(selection)] = u' '
      elif selection == select_all_scopes:
        for i in xrange(0, num_scopes):
          selected_scopes[i] = u'*'
      elif selection == unselect_all_scopes:
        for i in xrange(0, num_scopes):
          selected_scopes[i] = u' '
      elif selection == authorize_scopes:
        at_least_one = False
        for i in range(0, len(selected_scopes)):
          if selected_scopes[i] in [u'*', u'R', u'A']:
            at_least_one = True
        if at_least_one:
          break
        else:
          os.system([u'clear', u'cls'][os.name == u'nt'])
          print u"YOU MUST SELECT AT LEAST ONE SCOPE!\n"
          continue
      else:
        os.system([u'clear', u'cls'][os.name == u'nt'])
        print u'NOT A VALID SELECTION!'
        continue
      os.system([u'clear', u'cls'][os.name == u'nt'])
    except ValueError:
      os.system([u'clear', u'cls'][os.name == u'nt'])
      print u'Not a valid selection.'
      continue

  if incremental_auth:
    scopes = []
  else:
    scopes = [u'email',] # Email Display Scope, always included
  for i in range(0, len(selected_scopes)):
    if selected_scopes[i] == u'*':
      scopes.append(possible_scopes[i])
    elif selected_scopes[i] == u'R':
      scopes.append(u'%s.readonly' % possible_scopes[i])
    elif selected_scopes[i] == u'A':
      scopes.append(u'%s.action' % possible_scopes[i])
  FLOW = oauth2client.client.flow_from_clientsecrets(GC_Values[GC_CLIENT_SECRETS_JSON],
                                                     scope=scopes,
                                                     message=MISSING_CLIENT_SECRETS_MESSAGE)
  storage = oauth2client.file.Storage(GC_Values[GC_OAUTH2_TXT])
  credentials = storage.get()
  flags = cmd_flags()
  if GC_Values[GC_NO_BROWSER]:
    flags.noauth_local_webserver = True
  if credentials is None or credentials.invalid or incremental_auth:
    http = httplib2.Http(ca_certs=GC_Values[GC_CACERT_PEM],
                         disable_ssl_certificate_validation=GC_Values[GC_NO_VERIFY_SSL])
    GC_Values[GC_EXTRA_ARGS][u'prettyPrint'] = True
    try:
      credentials = oauth2client.tools.run_flow(flow=FLOW, storage=storage, flags=flags, http=http)
    except httplib2.CertificateValidationUnsupported:
      print u'\nError: You don\'t have the Python ssl module installed so we can\'t verify SSL Certificates.\n\nYou can fix this by installing the Python SSL module or you can live on dangerously and turn SSL validation off with the command: "gam config select default set no_verify_ssl true save"'
      sys.exit(8)

def batch_worker():
  while True:
    item = q.get()
    subprocess.call(item, stderr=subprocess.STDOUT)
    q.task_done()

def run_batch(items, total_items):
  import Queue, threading
  global q
  current_item = 0
  python_cmd = [sys.executable.lower(),]
  if not getattr(sys, 'frozen', False): # we're not frozen
    python_cmd.append(os.path.realpath(sys.argv[0]))
  num_threads = min(total_items, GC_Values[GC_NUM_THREADS])
  q = Queue.Queue(maxsize=num_threads) # q.put() gets blocked when trying to create more items than there are workers
  print u'starting %s worker threads...' % num_threads
  for i in range(num_threads):
    t = threading.Thread(target=batch_worker)
    t.daemon = True
    t.start()
  for item in items:
    current_item += 1
    if not current_item % 100:
      print u'starting job %s / %s' % (current_item, total_items)
    if item[0] == COMMIT_BATCH_CMD:
      sys.stderr.write(u'{0} - waiting for running processes to finish before proceeding...\n'.format(COMMIT_BATCH_CMD))
      q.join()
      sys.stderr.write(u'{0} - complete\n'.format(COMMIT_BATCH_CMD))
      continue
    q.put(python_cmd+item)
  q.join()
#
# Process GAM command
#
def ProcessGAMCommand(args, processGamCfg=True):
  if args != sys.argv:
    sys.argv = args[:]
  savedStdout = sys.stdout
  savedStderr = sys.stderr
  try:
    if processGamCfg and (not SetGlobalVariables()):
      sys.exit(0)
    if sys.argv[1].lower() == u'batch':
      import shlex
      bat_filename = sys.argv[2]
      if bat_filename == u'-':
        import StringIO
        input_string = unicode(sys.stdin.read())
        f = StringIO.StringIO(input_string)
      else:
        f = open(bat_filename, 'rU')
      items = []
      cmdCount = 0
      for line in f:
        argv = shlex.split(line)
        if len(argv) > 0:
          cmd = argv[0].strip()
          if (not cmd) or cmd.startswith(u'#') or ((len(argv) == 1) and (cmd != COMMIT_BATCH_CMD)):
            continue
          if cmd == GAM_CMD:
            items.append(argv[1:])
            cmdCount += 1
          elif cmd == COMMIT_BATCH_CMD:
            items.append(argv)
          else:
            sys.stderr.write(u'{0}"{1}" is not a valid gam command\n'.format(ERROR_PREFIX, line.strip()))
      f.close()
      run_batch(items, cmdCount)
      sys.exit(0)
    elif sys.argv[1].lower() == 'csv':
      csv_filename = sys.argv[2]
      if csv_filename == u'-':
        import StringIO
        input_string = unicode(sys.stdin.read())
        f = StringIO.StringIO(input_string)
      else:
        f = open(csv_filename, 'rU')
      csvFile = csv.DictReader(f)
      if (len(sys.argv) < 4) or (sys.argv[3].lower() != GAM_CMD):
        sys.stderr.write('{0}"gam csv {1}" should be followed by a full GAM command...\n'.format(ERROR_PREFIX, csv_filename))
        sys.exit(3)
      optionalSubs = {}
      GAM_argv = []
      GAM_argvI = 0
      for arg in sys.argv[4:]:
        if arg[0] != '~':
          GAM_argv.append(arg)
        else:
          fieldName = arg[1:]
          if fieldName in csvFile.fieldnames:
            optionalSubs[GAM_argvI] = fieldName
            GAM_argv.append(fieldName)
          else:
            sys.stderr.write('{0}header "{1}" not found in CSV headers of "{2}", giving up.\n'.format(ERROR_PREFIX, fieldName, ','.join(csvFile.fieldnames)))
            sys.exit(3)
        GAM_argvI += 1
      items = []
      for row in csvFile:
        argv = GAM_argv[:]
        for GAM_argvI, fieldName in optionalSubs.iteritems():
          if row[fieldName]:
            argv[GAM_argvI] = row[fieldName]
          else:
            argv[GAM_argvI] = u''
        items.append(argv)
      f.close()
      run_batch(items, len(items))
      sys.exit(0)
    elif sys.argv[1].lower() == u'version':
      doGAMVersion()
      sys.exit(0)
    elif sys.argv[1].lower() == u'create':
      if sys.argv[2].lower() == u'user':
        doCreateUser()
      elif sys.argv[2].lower() == u'group':
        doCreateGroup()
      elif sys.argv[2].lower() in [u'nickname', u'alias']:
        doCreateAlias()
      elif sys.argv[2].lower() in [u'org', 'ou']:
        doCreateOrg()
      elif sys.argv[2].lower() == u'resource':
        doCreateResource()
      elif sys.argv[2].lower() in [u'verify', u'verification']:
        doSiteVerifyShow()
      elif sys.argv[2].lower() in [u'schema']:
        doCreateOrUpdateUserSchema()
      elif sys.argv[2].lower() in [u'course', u'class']:
        doCreateCourse()
      else:
        print u'Error: invalid argument to "gam create..."'
        sys.exit(2)
      sys.exit(0)
    elif sys.argv[1].lower() == u'update':
      if sys.argv[2].lower() == u'user':
        doUpdateUser([sys.argv[3],])
      elif sys.argv[2].lower() == u'group':
        doUpdateGroup()
      elif sys.argv[2].lower() in [u'nickname', u'alias']:
        doUpdateAlias()
      elif sys.argv[2].lower() in [u'ou', u'org']:
        doUpdateOrg()
      elif sys.argv[2].lower() == u'resource':
        doUpdateResourceCalendar()
      elif sys.argv[2].lower() == u'domain':
        doUpdateDomain()
      elif sys.argv[2].lower() == u'cros':
        doUpdateCros()
      elif sys.argv[2].lower() == u'mobile':
        doUpdateMobile()
      elif sys.argv[2].lower() in [u'notification', u'notifications']:
        doUpdateNotification()
      elif sys.argv[2].lower() in [u'verify', u'verification']:
        doSiteVerifyAttempt()
      elif sys.argv[2].lower() in [u'schema', u'schemas']:
        doCreateOrUpdateUserSchema()
      elif sys.argv[2].lower() in [u'course', u'class']:
        doUpdateCourse()
      elif sys.argv[2].lower() in [u'printer', u'print']:
        doUpdatePrinter()
      else:
        showUsage()
        print u'Error: invalid argument to "gam update..."'
        sys.exit(2)
      sys.exit(0)
    elif sys.argv[1].lower() == u'info':
      if sys.argv[2].lower() == u'user':
        doGetUserInfo()
      elif sys.argv[2].lower() == u'group':
        doGetGroupInfo()
      elif sys.argv[2].lower() in [u'nickname', u'alias']:
        doGetAliasInfo()
      elif sys.argv[2].lower() == u'domain':
        doGetDomainInfo()
      elif sys.argv[2].lower() in [u'org', u'ou']:
        doGetOrgInfo()
      elif sys.argv[2].lower() == u'resource':
        doGetResourceCalendarInfo()
      elif sys.argv[2].lower() == u'cros':
        doGetCrosInfo()
      elif sys.argv[2].lower() == u'mobile':
        doGetMobileInfo()
      elif sys.argv[2].lower() in [u'notifications', u'notification']:
        doGetNotifications()
      elif sys.argv[2].lower() in [u'verify', u'verification']:
        doGetSiteVerifications()
      elif sys.argv[2].lower() in [u'schema', u'schemas']:
        doGetUserSchema()
      elif sys.argv[2].lower() in [u'course', u'class']:
        doGetCourseInfo()
      elif sys.argv[2].lower() in [u'printer', u'print']:
        doGetPrinterInfo()
      else:
        print u'Error: invalid argument to "gam info..."'
        sys.exit(2)
      sys.exit(0)
    elif sys.argv[1].lower() == u'delete':
      if sys.argv[2].lower() == u'user':
        doDeleteUser()
      elif sys.argv[2].lower() == u'group':
        doDeleteGroup()
      elif sys.argv[2].lower() in [u'nickname', u'alias']:
        doDeleteAlias()
      elif sys.argv[2].lower() == u'org':
        doDeleteOrg()
      elif sys.argv[2].lower() == u'resource':
        doDeleteResourceCalendar()
      elif sys.argv[2].lower() == u'mobile':
        doDeleteMobile()
      elif sys.argv[2].lower() in [u'notification', u'notifications']:
        doDeleteNotification()
      elif sys.argv[2].lower() in [u'schema', u'schemas']:
        doDelSchema()
      elif sys.argv[2].lower() in [u'course', u'class']:
        doDelCourse()
      elif sys.argv[2].lower() in [u'printer', u'printers']:
        doDelPrinter()
      else:
        print u'Error: invalid argument to "gam delete"'
        sys.exit(2)
      sys.exit(0)
    elif sys.argv[1].lower() == u'undelete':
      if sys.argv[2].lower() == u'user':
        doUndeleteUser()
      else:
        print u'Error: invalid argument to "gam undelete..."'
        sys.exit(2)
      sys.exit(0)
    elif sys.argv[1].lower() == u'audit':
      if sys.argv[2].lower() == u'monitor':
        if sys.argv[3].lower() == u'create':
          doCreateMonitor()
        elif sys.argv[3].lower() == u'list':
          doShowMonitors()
        elif sys.argv[3].lower() == u'delete':
          doDeleteMonitor()
        else:
          print u'Error: invalid argument to "gam audit monitor..."'
          sys.exit(2)
      elif sys.argv[2].lower() == u'activity':
        if sys.argv[3].lower() == u'request':
          doRequestActivity()
        elif sys.argv[3].lower() == u'status':
          doStatusActivityRequests()
        elif sys.argv[3].lower() == u'download':
          doDownloadActivityRequest()
        elif sys.argv[3].lower() == u'delete':
          doDeleteActivityRequest()
        else:
          print u'Error: invalid argument to "gam audit activity..."'
          sys.exit(2)
      elif sys.argv[2].lower() == u'export':
        if sys.argv[3].lower() == u'status':
          doStatusExportRequests()
        elif sys.argv[3].lower() == u'watch':
          doWatchExportRequest()
        elif sys.argv[3].lower() == u'download':
          doDownloadExportRequest()
        elif sys.argv[3].lower() == u'request':
          doRequestExport()
        elif sys.argv[3].lower() == u'delete':
          doDeleteExport()
        else:
          print u'Error: invalid argument to "gam audit export..."'
          sys.exit(2)
      elif sys.argv[2].lower() == u'uploadkey':
        doUploadAuditKey()
      else:
        print u'Error: invalid argument to "gam audit..."'
        sys.exit(2)
      sys.exit(0)
    elif sys.argv[1].lower() == u'print':
      if sys.argv[2].lower() == u'users':
        doPrintUsers()
      elif sys.argv[2].lower() == u'nicknames' or sys.argv[2].lower() == u'aliases':
        doPrintAliases()
      elif sys.argv[2].lower() == u'groups':
        doPrintGroups()
      elif sys.argv[2].lower() in [u'group-members', u'groups-members']:
        doPrintGroupMembers()
      elif sys.argv[2].lower() in [u'orgs', u'ous']:
        doPrintOrgs()
      elif sys.argv[2].lower() == u'resources':
        doPrintResources()
      elif sys.argv[2].lower() == u'cros':
        doPrintCrosDevices()
      elif sys.argv[2].lower() == u'mobile':
        doPrintMobileDevices()
      elif sys.argv[2].lower() in [u'license', u'licenses', u'licence', u'licences']:
        doPrintLicenses()
      elif sys.argv[2].lower() in [u'token', u'tokens']:
        doPrintTokens()
      elif sys.argv[2].lower() in [u'schema', u'schemas']:
        doPrintUserSchemas()
      elif sys.argv[2].lower() in [u'courses', u'classes']:
        doPrintCourses()
      elif sys.argv[2].lower() in [u'course-participants', u'class-participants']:
        doPrintCourseParticipants()
      elif sys.argv[2].lower() in [u'printers']:
        doPrintPrinters()
      elif sys.argv[2].lower() in [u'printjobs']:
        doPrintPrintJobs()
      else:
        print u'Error: invalid argument to "gam print..."'
        sys.exit(2)
      sys.exit(0)
    elif sys.argv[1].lower() in [u'oauth', u'oauth2']:
      if sys.argv[2].lower() in [u'request', u'create']:
        doRequestOAuth()
      elif sys.argv[2].lower() == u'info':
        OAuthInfo()
      elif sys.argv[2].lower() in [u'delete', u'revoke']:
        doDeleteOAuth()
      else:
        print u'Error: invalid argument to "gam oauth..."'
        sys.exit(2)
      sys.exit(0)
    elif sys.argv[1].lower() == u'calendar':
      if sys.argv[3].lower() == u'showacl':
        doCalendarShowACL()
      elif sys.argv[3].lower() == u'add':
        doCalendarAddACL()
      elif sys.argv[3].lower() in [u'del', u'delete']:
        doCalendarDelACL()
      elif sys.argv[3].lower() == u'update':
        doCalendarUpdateACL()
      elif sys.argv[3].lower() == u'wipe':
        doCalendarWipeData()
      elif sys.argv[3].lower() == u'addevent':
        doCalendarAddEvent()
      else:
        print u'Error: invalid argument to "gam calendar..."'
        sys.exit(2)
      sys.exit(0)
    elif sys.argv[1].lower() == u'printer':
      if sys.argv[3].lower() == u'showacl':
        doPrinterShowACL()
      elif sys.argv[3].lower() == u'add':
        doPrinterAddACL()
      elif sys.argv[3].lower() in [u'del', u'delete', u'remove']:
        doPrinterDelACL()
      elif sys.argv[3].lower() == u'register':
        doPrinterRegister()
      else:
        print u'Error: invalid argument to "gam printer..."'
        sys.exit(2)
      sys.exit(0)
    elif sys.argv[1].lower() == u'printjob':
      if sys.argv[3].lower() == u'delete':
        doDeletePrintJob()
      elif sys.argv[3].lower() == u'cancel':
        doCancelPrintJob()
      elif sys.argv[3].lower() == u'submit':
        doPrintJobSubmit()
      elif sys.argv[3].lower() == u'fetch':
        doPrintJobFetch()
      elif sys.argv[3].lower() == u'resubmit':
        doPrintJobResubmit()
      else:
        print u'ERROR: invalid argument to "gam printjob..."'
        sys.exit(2)
      sys.exit(0)
    elif sys.argv[1].lower() == u'report':
      showReport()
      sys.exit(0)
    elif sys.argv[1].lower() == u'whatis':
      doWhatIs()
      sys.exit(0)
    elif sys.argv[1].lower() in [u'course', u'class']:
      if sys.argv[3].lower() in [u'add', u'create']:
        doAddCourseParticipant()
        sys.exit(0)
      elif sys.argv[3].lower() in [u'del', u'delete', u'remove']:
        doDelCourseParticipant()
        sys.exit(0)
      elif sys.argv[3].lower() == u'sync':
        doSyncCourseParticipants()
        sys.exit(0)
      else:
        print u'Error: invalid argument to "gam course..."'
        sys.exit(2)
    users = getUsersToModify()
    command = sys.argv[3].lower()
    if command == u'print':
      for user in users:
        print user
        sys.exit(0)
    if (GC_Values[GC_AUTO_BATCH_MIN] > 0) and (len(users) > GC_Values[GC_AUTO_BATCH_MIN]):
      items = []
      for user in users:
        items.append([u'user', user] + sys.argv[3:])
      run_batch(items, len(items))
      sys.exit(0)
    if command == u'transfer':
      transferWhat = sys.argv[4].lower()
      if transferWhat == u'drive':
        transferDriveFiles(users)
      elif transferWhat == u'seccals':
        transferSecCals(users)
    elif command == u'show':
      readWhat = sys.argv[4].lower()
      if readWhat in [u'labels', u'label']:
        showLabels(users)
      elif readWhat == u'profile':
        showProfile(users)
      elif readWhat == u'calendars':
        showCalendars(users)
      elif readWhat == u'calsettings':
        showCalSettings(users)
      elif readWhat == u'drivesettings':
        showDriveSettings(users)
      elif readWhat == u'drivefileacl':
        showDriveFileACL(users)
      elif readWhat == u'filelist':
        showDriveFiles(users)
      elif readWhat == u'filetree':
        showDriveFileTree(users)
      elif readWhat == u'fileinfo':
        showDriveFileInfo(users)
      elif readWhat == u'sendas':
        showSendAs(users)
      elif readWhat == u'gmailprofile':
        showGmailProfile(users)
      elif readWhat in [u'sig', u'signature']:
        getSignature(users)
      elif readWhat == u'forward':
        getForward(users)
      elif readWhat in [u'pop', u'pop3']:
        getPop(users)
      elif readWhat in [u'imap', u'imap4']:
        getImap(users)
      elif readWhat == u'vacation':
        getVacation(users)
      elif readWhat in [u'delegate', u'delegates']:
        getDelegates(users)
      elif readWhat in [u'backupcode', u'backupcodes', u'verificationcodes']:
        doGetBackupCodes(users)
      elif readWhat in [u'asp', u'asps', u'applicationspecificpasswords']:
        doGetASPs(users)
      elif readWhat in [u'token', u'tokens', u'oauth', u'3lo']:
        doGetTokens(users)
      elif readWhat in [u'driveactivity']:
        doDriveActivity(users)
      else:
        print u'Error: invalid argument to "gam <users> show..."'
        sys.exit(2)
    elif command == u'trash':
      if sys.argv[4].lower() in [u'message', u'messages']:
        doDeleteMessages(users, u'trash')
      else:
        print u'ERROR: invalid argument to "gam <users> trash..."'
        sys.exit(2)
    elif command == u'spam':
      if sys.argv[4].lower() in [u'message', u'messages']:
        doSpamMessages(users)
      else:
        print u'ERROR: invalid argument to "gam <users> spam..."'
        sys.exit(2)
    elif command == u'delete' or command == u'del':
      delWhat = sys.argv[4].lower()
      if delWhat == u'delegate':
        deleteDelegate(users)
      elif delWhat == u'calendar':
        deleteCalendar(users)
      elif delWhat == u'label':
        doDeleteLabel(users)
      elif delWhat in [u'message', u'messages']:
        doDeleteMessages(users, u'delete')
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
        doRemoveUsersGroups(users)
      elif delWhat in [u'alias', u'aliases']:
        doRemoveUsersAliases(users)
      elif delWhat in [u'emptydrivefolders']:
        deleteEmptyDriveFolders(users)
      elif delWhat in [u'drivefile']:
        deleteDriveFile(users)
      elif delWhat in [u'drivefileacl', u'drivefileacls']:
        delDriveFileACL(users)
      else:
        print u'Error: invalid argument to "gam <users> delete..."'
        sys.exit(2)
    elif command == u'add':
      addWhat = sys.argv[4].lower()
      if addWhat == u'calendar':
        addCalendar(users)
      elif addWhat == u'drivefile':
        createDriveFile(users)
      elif addWhat in [u'license', u'licence']:
        doLicense(users, u'insert')
      elif addWhat in [u'drivefileacl', u'drivefileacls']:
        addDriveFileACL(users)
      elif addWhat in [u'label', u'labels']:
        doLabel(users)
      else:
        print u'Error: invalid argument to "gam <users> add..."'
        sys.exit(2)
    elif command == u'update':
      if sys.argv[4].lower() == u'calendar':
        updateCalendar(users)
      elif sys.argv[4].lower() == u'calattendees':
        changeCalendarAttendees(users)
      elif sys.argv[4].lower() == u'photo':
        doPhoto(users)
      elif sys.argv[4].lower() in [u'license', u'licence']:
        doLicense(users, u'patch')
      elif sys.argv[4].lower() == u'user':
        doUpdateUser(users)
      elif sys.argv[4].lower() in [u'backupcode', u'backupcodes', u'verificationcodes']:
        doGenBackupCodes(users)
      elif sys.argv[4].lower() in [u'drivefile']:
        doUpdateDriveFile(users)
      elif sys.argv[4].lower() in [u'drivefileacls', u'drivefileacl']:
        updateDriveFileACL(users)
      elif sys.argv[4].lower() in [u'label', u'labels']:
        renameLabels(users)
      elif sys.argv[4].lower() in [u'labelsettings']:
        updateLabels(users)
      else:
        print u'Error: invalid argument to "gam <users> update..."'
        sys.exit(2)
    elif command in [u'deprov', u'deprovision']:
      doDeprovUser(users)
    elif command == u'get':
      if sys.argv[4].lower() == u'photo':
        getPhoto(users)
      elif sys.argv[4].lower() == u'drivefile':
        downloadDriveFile(users)
    elif command == u'profile':
      doProfile(users)
    elif command == u'imap':
      doImap(users)
    elif command in [u'pop', u'pop3']:
      doPop(users)
    elif command == u'sendas':
      doSendAs(users)
    elif command == u'language':
      doLanguage(users)
    elif command in [u'utf', u'utf8', u'utf-8', u'unicode']:
      doUTF(users)
    elif command == u'pagesize':
      doPageSize(users)
    elif command == u'shortcuts':
      doShortCuts(users)
    elif command == u'arrows':
      doArrows(users)
    elif command == u'snippets':
      doSnippets(users)
    elif command == u'label':
      doLabel(users)
    elif command == u'filter':
      doFilter(users)
    elif command == u'forward':
      doForward(users)
    elif command in [u'sig', u'signature']:
      doSignature(users)
    elif command == u'vacation':
      doVacation(users)
    elif command == u'webclips':
      doWebClips(users)
    elif command in [u'delegate', u'delegates']:
      doDelegates(users)
    else:
      print u'Error: %s is not a valid gam command' % command
      sys.exit(2)
    sys.exit(0)
  except IndexError:
    showUsage()
    sysExitRC = 2
  except KeyboardInterrupt:
    sysExitRC = 50
  except socket.error, e:
    sys.stderr.write(u'{0}{1}\n'.format(ERROR_PREFIX, e))
    sysExitRC = 3
  except MemoryError:
    sys.stderr.write(u'{0}{1}\n'.format(ERROR_PREFIX, u'GAM has run out of memory. If this is a large Google Apps instance, you should use a 64-bit version of GAM on Windows or a 64-bit version of Python on other systems.'))
    sysExitRC = 99
  except IOError as e:
    sys.stderr.write(u'{0}{1}\n'.format(ERROR_PREFIX, e))
    sysExitRC = 3
  except Exception as e:
    import traceback
    traceback.print_exc(file=savedStderr)
    sysExitRC = 1
  except SystemExit as sysExitRC:
    pass
  if sys.stdout != savedStdout:
    sys.stdout.close()
    sys.stdout = savedStdout
  if sys.stderr != savedStderr:
    sys.stderr.close()
    sys.stderr = savedStderr
  return sysExitRC
#
# Run from command line
#
if __name__ == "__main__":
  reload(sys)
  sys.setdefaultencoding(u'UTF-8')
  if os.name == u'nt':
    sys.argv = win32_unicode_argv() # cleanup sys.argv on Windows
  rc = ProcessGAMCommand(sys.argv)
  sys.exit(rc)
