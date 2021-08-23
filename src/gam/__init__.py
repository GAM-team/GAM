"""Main behavioral methods and argument routing for GAM."""


import base64
import configparser
import csv
import datetime
from email import message_from_string
try:
    from importlib.metadata import version as lib_version
except ImportError:
    from importlib_metadata import version as lib_version
import io
import json
import mimetypes
import os
import platform
from pathlib import Path
import random
from secrets import SystemRandom
import re
import shlex
import signal
import socket
import ssl
import struct
import sys
import time
import uuid
import webbrowser
import zipfile
import http.client as http_client
from multiprocessing import Pool as mp_pool
from multiprocessing import Lock as mp_lock
from urllib.parse import quote, urlencode, urlparse
from pathvalidate import sanitize_filename
import dateutil.parser

import googleapiclient
import googleapiclient.discovery
import googleapiclient.errors
import googleapiclient.http
import google.oauth2.service_account
import httplib2
from google.auth.jwt import Credentials as JWTCredentials

from cryptography import x509
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.x509.oid import NameOID

import gam.auth.oauth
from gam import auth
from gam import controlflow
from gam import display
from gam import fileutils
from gam.gapi import calendar as gapi_calendar
from gam.gapi import cloudidentity as gapi_cloudidentity
from gam.gapi import cbcm as gapi_cbcm
from gam.gapi import chat as gapi_chat
from gam.gapi import chromehistory as gapi_chromehistory
from gam.gapi import chromemanagement as gapi_chromemanagement
from gam.gapi import chromepolicy as gapi_chromepolicy
from gam.gapi.cloudidentity import devices as gapi_cloudidentity_devices
from gam.gapi.cloudidentity import groups as gapi_cloudidentity_groups
from gam.gapi.cloudidentity import userinvitations as gapi_cloudidentity_userinvitations
from gam.gapi import contactdelegation as gapi_contactdelegation
from gam.gapi.directory import asps as gapi_directory_asps
from gam.gapi.directory import cros as gapi_directory_cros
from gam.gapi.directory import customer as gapi_directory_customer
from gam.gapi.directory import domainaliases as gapi_directory_domainaliases
from gam.gapi.directory import domains as gapi_directory_domains
from gam.gapi.directory import groups as gapi_directory_groups
from gam.gapi.directory import mobiledevices as gapi_directory_mobiledevices
from gam.gapi.directory import orgunits as gapi_directory_orgunits
from gam.gapi.directory import printers as gapi_directory_printers
from gam.gapi.directory import privileges as gapi_directory_privileges
from gam.gapi.directory import resource as gapi_directory_resource
from gam.gapi.directory import roles as gapi_directory_roles
from gam.gapi.directory import users as gapi_directory_users
from gam.gapi import licensing as gapi_licensing
from gam.gapi import siteverification as gapi_siteverification
from gam.gapi import errors as gapi_errors
from gam.gapi import reports as gapi_reports
from gam.gapi import storage as gapi_storage
from gam.gapi import vault as gapi_vault
from gam import gapi
from gam import transport
from gam import utils
from gam.var import *

yubikey = utils.LazyLoader('yubikey', globals(), 'gam.auth.yubikey')
from passlib.hash import sha512_crypt

if platform.system() == 'Linux':
    import distro

# Finding path method varies between Python source, PyInstaller and StaticX
if os.environ.get('STATICX_PROG_PATH', False):
    # StaticX static executable
    GM_Globals[GM_GAM_PATH] = os.path.dirname(os.environ['STATICX_PROG_PATH'])
    GM_Globals[GM_GAM_TYPE] = 'staticx'
    # Pyinstaller executable
elif getattr(sys, 'frozen', False):
    GM_Globals[GM_GAM_PATH] = os.path.dirname(sys.executable)
    GM_Globals[GM_GAM_TYPE] = 'pyinstaller'
else:
    # Source code
    GM_Globals[GM_GAM_PATH] = os.path.dirname(
        Path(os.path.realpath(__file__)).parent)
    GM_Globals[GM_GAM_TYPE] = 'pythonsource'


def showUsage():
    doGAMVersion(checkForArgs=False)
    print('''
Usage: gam [OPTIONS]...

GAM. Retrieve or set Google Workspace domain,
user, group and alias settings. Exhaustive list of commands
can be found at: https://github.com/jay0lee/GAM/wiki

Examples:
gam info domain
gam create user jsmith firstname John lastname Smith password secretpass
gam update user jsmith suspended on
gam.exe update group announcements add member jsmith
...

''')


def currentCount(i, count):
    return f' ({i}/{count})' if (count > GC_Values[GC_SHOW_COUNTS_MIN]) else ''


def currentCountNL(i, count):
    return f' ({i}/{count})\n' if (
        count > GC_Values[GC_SHOW_COUNTS_MIN]) else '\n'


def printGettingAllItems(items, query):
    if query:
        sys.stderr.write(
            f'Getting all {items} in Google Workspace account that match query ({query}) (may take some time on a large account)...\n'
        )
    else:
        sys.stderr.write(
            f'Getting all {items} in Google Workspace account (may take some time on a large account)...\n'
        )


def entityServiceNotApplicableWarning(entityType, entityName, i, count):
    sys.stderr.write(
        f'{entityType}: {entityName}, Service not applicable/Does not exist{currentCountNL(i, count)}'
    )


def entityDoesNotExistWarning(entityType, entityName, i, count):
    sys.stderr.write(
        f'{entityType}: {entityName}, Does not exist{currentCountNL(i, count)}')


def entityUnknownWarning(entityType, entityName, i, count):
    domain = getEmailAddressDomain(entityName)
    if (domain == GC_Values[GC_DOMAIN]) or (domain.endswith('google.com')):
        entityDoesNotExistWarning(entityType, entityName, i, count)
    else:
        entityServiceNotApplicableWarning(entityType, entityName, i, count)


def printLine(message):
    sys.stdout.write(message + '\n')


def getBoolean(value, item):
    value = value.lower()
    if value in true_values:
        return True
    if value in false_values:
        return False
    controlflow.system_error_exit(
        2,
        f'Value for {item} must be {"|".join(true_values)} or {"|".join(false_values)}; got {value}'
    )


def getCharSet(i):
    if (i == len(sys.argv)) or (sys.argv[i].lower() != 'charset'):
        return (i, GC_Values.get(GC_CHARSET, GM_Globals[GM_SYS_ENCODING]))
    return (i + 2, sys.argv[i + 1])


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
    return text  # Hand back the plain text, uncolorized.


def createRedText(text):
    """Uses ANSI encoding to create red colored text if supported."""
    return createColoredText(text, '\033[91m')


def createGreenText(text):
    """Uses ANSI encoding to create green colored text if supported."""
    return createColoredText(text, '\u001b[32m')


def createYellowText(text):
    """Uses ANSI encoding to create yellow text if supported."""
    return createColoredText(text, '\u001b[33m')


COLORHEX_PATTERN = re.compile(r'^#[0-9a-fA-F]{6}$')


def getColor(color):
    color = color.lower().strip()
    if color in WEBCOLOR_MAP:
        return WEBCOLOR_MAP[color]
    tg = COLORHEX_PATTERN.match(color)
    if tg:
        return tg.group(0)
    controlflow.system_error_exit(
        2,
        f'A color must be a valid name or # and six hex characters (#012345); got {color}'
    )


def getLabelColor(color):
    color = color.lower().strip()
    tg = COLORHEX_PATTERN.match(color)
    if tg:
        color = tg.group(0)
        if color in LABEL_COLORS:
            return color
        controlflow.expected_argument_exit('label color',
                                           ', '.join(LABEL_COLORS), color)
    controlflow.system_error_exit(
        2,
        f'A label color must be # and six hex characters (#012345); got {color}'
    )


def getInteger(value, item, minVal=None, maxVal=None):
    try:
        number = int(value.strip())
        if ((minVal is None) or (number >= minVal)) and ((maxVal is None) or
                                                         (number <= maxVal)):
            return number
    except ValueError:
        pass
    controlflow.system_error_exit(
        2,
        f'expected {item} in range <{utils.integerLimits(minVal, maxVal)}>, got {value}'
    )


def removeCourseIdScope(courseId):
    if courseId.startswith('d:'):
        return courseId[2:]
    return courseId


def addCourseIdScope(courseId):
    if not courseId.isdigit() and courseId[:2] != 'd:':
        return f'd:{courseId}'
    return courseId


# Get domain from email address
def getEmailAddressDomain(emailAddress):
    atLoc = emailAddress.find('@')
    if atLoc == -1:
        return GC_Values[GC_DOMAIN].lower()
    return emailAddress[atLoc + 1:].lower()


# Split email address unto user and domain
def splitEmailAddress(emailAddress):
    atLoc = emailAddress.find('@')
    if atLoc == -1:
        return (emailAddress.lower(), GC_Values[GC_DOMAIN].lower())
    return (emailAddress[:atLoc].lower(), emailAddress[atLoc + 1:].lower())


# Normalize user/group email address/uid
# uid:12345abc -> 12345abc
# foo -> foo@domain
# foo@ -> foo@domain
# foo@bar.com -> foo@bar.com
# @domain -> domain
def normalizeEmailAddressOrUID(emailAddressOrUID,
                               noUid=False,
                               checkForCustomerId=False,
                               noLower=False):
    if checkForCustomerId and (emailAddressOrUID == GC_Values[GC_CUSTOMER_ID]):
        return emailAddressOrUID
    if not noUid:
        cg = UID_PATTERN.match(emailAddressOrUID)
        if cg:
            return cg.group(1)
    atLoc = emailAddressOrUID.find('@')
    if atLoc == 0:
        return emailAddressOrUID[1:].lower(
        ) if not noLower else emailAddressOrUID[1:]
    if (atLoc == -1) or (atLoc == len(emailAddressOrUID) -
                         1) and GC_Values[GC_DOMAIN]:
        if atLoc == -1:
            emailAddressOrUID = f'{emailAddressOrUID}@{GC_Values[GC_DOMAIN]}'
        else:
            emailAddressOrUID = f'{emailAddressOrUID}{GC_Values[GC_DOMAIN]}'
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

    def _getOldSignalFile(itemName,
                          fileName,
                          filePresentValue=True,
                          fileAbsentValue=False):
        GC_Defaults[itemName] = filePresentValue if os.path.isfile(
            os.path.join(GC_Defaults[GC_CONFIG_DIR],
                         fileName)) else fileAbsentValue

    def _getCfgDirectory(itemName):
        return GC_Defaults[itemName]

    def _getCfgFile(itemName):
        if not GC_Defaults[itemName]:
            return None
        value = os.path.expanduser(GC_Defaults[itemName])
        if not os.path.isabs(value):
            value = os.path.expanduser(
                os.path.join(GC_Values[GC_CONFIG_DIR], value))
        return value

    def _getCfgHeaderFilter(itemName):
        value = GC_Defaults[itemName]
        headerFilters = []
        if not value:
            return headerFilters
        filters = shlexSplitList(value)
        for filterStr in filters:
            try:
                headerFilters.append(re.compile(filterStr, re.IGNORECASE))
            except re.error as e:
                controlflow.system_error_exit(
                    3, f'Item: {itemName}: "{filterStr}", Invalid RE: {str(e)}')
        return headerFilters

    ROW_FILTER_COMP_PATTERN = re.compile(
        r'^(date|time|count)\s*([<>]=?|=|!=)\s*(.+)$', re.IGNORECASE)
    ROW_FILTER_BOOL_PATTERN = re.compile(r'^(boolean):(.+)$', re.IGNORECASE)
    ROW_FILTER_RE_PATTERN = re.compile(r'^(regex|notregex):(.+)$', re.IGNORECASE)
    REGEX_CHARS = '^$*+|$[{('

    def _getCfgRowFilter(itemName):
        value = GC_Defaults[itemName]
        rowFilters = {}
        if not value:
            return rowFilters
        if value.startswith('{'):
            try:
                filterDict = json.loads(
                    value.encode('unicode-escape').decode(UTF8))
            except (TypeError, ValueError) as e:
                controlflow.system_error_exit(
                    3,
                    f'Item: {itemName}, Value: "{value}", Failed to parse as JSON: {str(e)}'
                )
        else:
            filterDict = {}
            status, filterList = shlexSplitListStatus(value)
            if not status:
                controlflow.system_error_exit(
                    3,
                    f'Item: {itemName}, Value: "{value}", Failed to parse as list'
                )
            for filterVal in filterList:
                if not filterVal:
                    continue
                try:
                    filterTokens = shlexSplitList(filterVal, ':')
                    column = filterTokens[0]
                    filterStr = ':'.join(filterTokens[1:])
                except ValueError:
                    controlflow.system_error_exit(
                        3,
                        f'Item: {itemName}, Value: "{filterVal}", Expected column:filter'
                    )
                filterDict[column] = filterStr
        for column, filterStr in iter(filterDict.items()):
            for c in REGEX_CHARS:
                if c in column:
                    columnPat = column
                    break
            else:
                columnPat = f'^{column}$'
            try:
                columnPat = re.compile(columnPat, re.IGNORECASE)
            except re.error as e:
                controlflow.system_error_exit(
                    3, f'Item: {itemName}: "{column}", Invalid RE: {str(e)}')
            mg = ROW_FILTER_COMP_PATTERN.match(filterStr)
            if mg:
                if mg.group(1) in ['date', 'time']:
                    if mg.group(1) == 'date':
                        valid, filterValue = utils.get_row_filter_date_or_delta_from_now(
                            mg.group(3))
                    else:
                        valid, filterValue = utils.get_row_filter_time_or_delta_from_now(
                            mg.group(3))
                    if valid:
                        rowFilters[column] = (columnPat, mg.group(1), mg.group(2),
                                              filterValue)
                        continue
                    controlflow.system_error_exit(
                        3,
                        f'Item: {itemName}, Value: "{column}": "{filterStr}", Expected: {filterValue}'
                    )
                else:  #count
                    if mg.group(3).isdigit():
                        rowFilters[column] = (columnPat, mg.group(1), mg.group(2),
                                              int(mg.group(3)))
                        continue
                    controlflow.system_error_exit(
                        3,
                        f'Item: {itemName}, Value: "{column}": "{filterStr}", Expected: <Number>'
                    )
            mg = ROW_FILTER_BOOL_PATTERN.match(filterStr)
            if mg:
                value = mg.group(2).lower()
                if value in true_values:
                    filterValue = True
                elif value in false_values:
                    filterValue = False
                else:
                    controlflow.system_error_exit(
                        3,
                        f'Item: {itemName}, Value: "{column}": "{filterStr}", Expected true|false'
                    )
                rowFilters[column] = (columnPat, mg.group(1), filterValue)
                continue
            mg = ROW_FILTER_RE_PATTERN.match(filterStr)
            if mg:
                try:
                    rowFilters[column] = (columnPat, mg.group(1), re.compile(mg.group(2)))
                    continue
                except re.error as e:
                    controlflow.system_error_exit(
                        3,
                        f'Item: {itemName}, Value: "{column}": "{filterStr}", Invalid RE: {str(e)}'
                    )
            controlflow.system_error_exit(
                3,
                f'Item: {itemName}, Value: "{column}": {filterStr}, Expected: (date|time|count<Operator><Value>) or (boolean:true|false) or (regex|notregex:<RegularExpression>)'
            )
        return rowFilters

    GC_Defaults[GC_CONFIG_DIR] = GM_Globals[GM_GAM_PATH]
    GC_Defaults[GC_CACHE_DIR] = os.path.join(GM_Globals[GM_GAM_PATH],
                                             'gamcache')
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
    _getOldEnvVar(GC_ADMIN_EMAIL, 'GA_ADMIN_EMAIL')
    _getOldEnvVar(GC_DOMAIN, 'GA_DOMAIN')
    _getOldEnvVar(GC_CUSTOMER_ID, 'CUSTOMER_ID')
    _getOldEnvVar(GC_CHARSET, 'GAM_CHARSET')
    _getOldEnvVar(GC_NUM_THREADS, 'GAM_THREADS')
    _getOldEnvVar(GC_AUTO_BATCH_MIN, 'GAM_AUTOBATCH')
    _getOldEnvVar(GC_BATCH_SIZE, 'GAM_BATCH_SIZE')
    _getOldEnvVar(GC_CSV_HEADER_FILTER, 'GAM_CSV_HEADER_FILTER')
    _getOldEnvVar(GC_CSV_HEADER_DROP_FILTER, 'GAM_CSV_HEADER_DROP_FILTER')
    _getOldEnvVar(GC_CSV_ROW_FILTER, 'GAM_CSV_ROW_FILTER')
    _getOldEnvVar(GC_CSV_ROW_DROP_FILTER, 'GAM_CSV_ROW_DROP_FILTER')
    _getOldEnvVar(GC_TLS_MIN_VERSION, 'GAM_TLS_MIN_VERSION')
    _getOldEnvVar(GC_TLS_MAX_VERSION, 'GAM_TLS_MAX_VERSION')
    _getOldEnvVar(GC_CA_FILE, 'GAM_CA_FILE')
    _getOldSignalFile(GC_DEBUG_LEVEL,
                      'debug.gam',
                      filePresentValue=4,
                      fileAbsentValue=0)
    _getOldSignalFile(GC_NO_BROWSER, 'nobrowser.txt')
    _getOldSignalFile(GC_OAUTH_BROWSER, 'oauthbrowser.txt')
    #  _getOldSignalFile(GC_NO_CACHE, u'nocache.txt')
    #  _getOldSignalFile(GC_CACHE_DISCOVERY_ONLY, u'allcache.txt', filePresentValue=False, fileAbsentValue=True)
    _getOldSignalFile(GC_NO_CACHE,
                      'allcache.txt',
                      filePresentValue=False,
                      fileAbsentValue=True)
    _getOldSignalFile(GC_NO_SHORT_URLS, 'noshorturls.txt')
    _getOldSignalFile(GC_NO_UPDATE_CHECK, 'noupdatecheck.txt')
    _getOldSignalFile(GC_ENABLE_DASA, FN_ENABLEDASA_TXT)
    # Assign directories first
    for itemName in GC_VAR_INFO:
        if GC_VAR_INFO[itemName][GC_VAR_TYPE] == GC_TYPE_DIRECTORY:
            GC_Values[itemName] = _getCfgDirectory(itemName)
    for itemName in GC_VAR_INFO:
        varType = GC_VAR_INFO[itemName][GC_VAR_TYPE]
        if varType == GC_TYPE_FILE:
            GC_Values[itemName] = _getCfgFile(itemName)
        elif varType == GC_TYPE_HEADERFILTER:
            GC_Values[itemName] = _getCfgHeaderFilter(itemName)
        elif varType == GC_TYPE_ROWFILTER:
            GC_Values[itemName] = _getCfgRowFilter(itemName)
        else:
            GC_Values[itemName] = GC_Defaults[itemName]
    GM_Globals[GM_LAST_UPDATE_CHECK_TXT] = os.path.join(
        GC_Values[GC_CONFIG_DIR], FN_LAST_UPDATE_CHECK_TXT)
    GM_Globals[GM_ENABLEDASA_TXT] = os.path.join(
        GC_Values[GC_CONFIG_DIR], FN_ENABLEDASA_TXT)
    if not GC_Values[GC_NO_UPDATE_CHECK]:
        doGAMCheckForUpdates()

# domain must be set and customer_id must be set and != my_customer when enable_dasa = true
    if GC_Values[GC_ENABLE_DASA]:
        if not GC_Values[GC_DOMAIN]:
            controlflow.system_error_exit(
                3,
                f'Environment variable GA_DOMAIN must be set when {GM_Globals[GM_ENABLEDASA_TXT]} is present'
                )
        if not GC_Values[GC_CUSTOMER_ID] or GC_Values[GC_CUSTOMER_ID] == MY_CUSTOMER:
            controlflow.system_error_exit(
                3,
                f'Environment variable CUSTOMER_ID must be set and not equal to {MY_CUSTOMER} when {GM_Globals[GM_ENABLEDASA_TXT]} is present\n'
                'Your customer ID can be found at admin.google.com > Account settings > Profile.'
                )


# Globals derived from config file values
    GM_Globals[GM_OAUTH2SERVICE_JSON_DATA] = None
    GM_Globals[GM_OAUTH2SERVICE_ACCOUNT_CLIENT_ID] = None
    GM_Globals[GM_EXTRA_ARGS_DICT] = {
        'prettyPrint': GC_Values[GC_DEBUG_LEVEL] > 0
    }
    # override httplib2 settings
    httplib2.debuglevel = GC_Values[GC_DEBUG_LEVEL]
    if os.path.isfile(os.path.join(GC_Values[GC_CONFIG_DIR],
                                   FN_EXTRA_ARGS_TXT)):
        ea_config = configparser.ConfigParser()
        ea_config.optionxform = str
        ea_config.read(os.path.join(GC_Values[GC_CONFIG_DIR],
                                    FN_EXTRA_ARGS_TXT))
        GM_Globals[GM_EXTRA_ARGS_DICT].update(
            dict(ea_config.items('extra-args')))
    if GC_Values[GC_NO_CACHE]:
        GM_Globals[GM_CACHE_DIR] = None
        GM_Globals[GM_CACHE_DISCOVERY_ONLY] = False
    else:
        GM_Globals[GM_CACHE_DIR] = GC_Values[GC_CACHE_DIR]
        #    GM_Globals[GM_CACHE_DISCOVERY_ONLY] = GC_Values[GC_CACHE_DISCOVERY_ONLY]
        GM_Globals[GM_CACHE_DISCOVERY_ONLY] = False
    return True

TIME_OFFSET_UNITS = [('day', 86400), ('hour', 3600), ('minute', 60),
                     ('second', 1)]


def getLocalGoogleTimeOffset(testLocation='admin.googleapis.com'):
    localUTC = datetime.datetime.now(datetime.timezone.utc)
    try:
        # we disable SSL verify so we can still get time even if clock
        # is way off. This could be spoofed / MitM but we'll fail for those
        # situations everywhere else but here.
        badhttp = transport.create_http()
        badhttp.disable_ssl_certificate_validation = True
        googleUTC = dateutil.parser.parse(
            badhttp.request('https://' + testLocation, 'HEAD')[0]['date'])
    except (httplib2.ServerNotFoundError, RuntimeError, ValueError) as e:
        controlflow.system_error_exit(4, str(e))
    offset = remainder = int(abs((localUTC - googleUTC).total_seconds()))
    timeoff = []
    for tou in TIME_OFFSET_UNITS:
        uval, remainder = divmod(remainder, tou[1])
        if uval:
            timeoff.append(f'{uval} {tou[0]}{"s" if uval != 1 else ""}')
    if not timeoff:
        timeoff.append('less than 1 second')
    nicetime = ', '.join(timeoff)
    return (offset, nicetime)


def doGAMCheckForUpdates(forceCheck=False):

    def _gamLatestVersionNotAvailable():
        if forceCheck:
            controlflow.system_error_exit(
                4, 'GAM Latest Version information not available')

    current_version = GAM_VERSION
    now_time = int(time.time())
    if forceCheck:
        check_url = GAM_ALL_RELEASES  # includes pre-releases
    else:
        last_check_time_str = fileutils.read_file(
            GM_Globals[GM_LAST_UPDATE_CHECK_TXT],
            continue_on_error=True,
            display_errors=False)
        last_check_time = int(
            last_check_time_str
        ) if last_check_time_str and last_check_time_str.isdigit() else 0
        if last_check_time > now_time - 604800:
            return
        check_url = GAM_LATEST_RELEASE  # latest full release
    headers = {'Accept': 'application/vnd.github.v3.text+json'}
    simplehttp = transport.create_http(timeout=10)
    try:
        (_, c) = simplehttp.request(check_url, 'GET', headers=headers)
        try:
            release_data = json.loads(c.decode(UTF8))
        except ValueError:
            _gamLatestVersionNotAvailable()
            return
        if isinstance(release_data, list):
            release_data = release_data[0]  # only care about latest release
        if not isinstance(release_data, dict) or 'tag_name' not in release_data:
            _gamLatestVersionNotAvailable()
            return
        latest_version = release_data['tag_name']
        if latest_version[0].lower() == 'v':
            latest_version = latest_version[1:]
        if forceCheck or (latest_version > current_version):
            print(
                f'Version Check:\n Current: {current_version}\n Latest: {latest_version}'
            )
        if latest_version <= current_version:
            fileutils.write_file(GM_Globals[GM_LAST_UPDATE_CHECK_TXT],
                                 str(now_time),
                                 continue_on_error=True,
                                 display_errors=forceCheck)
            return
        announcement = release_data.get('body_text',
                                        'No details about this release')
        sys.stderr.write(f'\nGAM {latest_version} release notes:\n\n')
        sys.stderr.write(announcement)
        try:
            printLine(MESSAGE_HIT_CONTROL_C_TO_UPDATE)
            time.sleep(15)
        except KeyboardInterrupt:
            webbrowser.open(release_data['html_url'])
            printLine(MESSAGE_GAM_EXITING_FOR_UPDATE)
            sys.exit(0)
        fileutils.write_file(GM_Globals[GM_LAST_UPDATE_CHECK_TXT],
                             str(now_time),
                             continue_on_error=True,
                             display_errors=forceCheck)
        return
    except (httplib2.HttpLib2Error, httplib2.ServerNotFoundError, RuntimeError,
            socket.timeout):
        return


def getOSPlatform():
    myos = platform.system()
    if myos == 'Linux':
        pltfrm = ' '.join(
            distro.linux_distribution(full_distribution_name=False)).title()
    elif myos == 'Windows':
        pltfrm = ' '.join(platform.win32_ver())
    elif myos == 'Darwin':
        myos = 'MacOS'
        mac_ver = platform.mac_ver()[0]
        major_ver = int(mac_ver.split('.')[0])  # macver 10.14.6 == major_ver 10
        minor_ver = int(mac_ver.split('.')[1])  # macver 10.14.6 == minor_ver 14
        if major_ver == 10:
            codename = MACOS_CODENAMES[major_ver].get(minor_ver, '')
        else:
            codename = MACOS_CODENAMES.get(major_ver, '')
        pltfrm = ' '.join([codename, mac_ver])
    else:
        pltfrm = platform.platform()
    return f'{myos} {pltfrm}'


def doGAMVersion(checkForArgs=True):
    force_check = extended = simple = timeOffset = False
    testLocation = 'admin.googleapis.com'
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
                timeOffset = True
                i += 1
            elif myarg == 'timeoffset':
                timeOffset = True
                i += 1
            elif myarg == 'location':
                testLocation = sys.argv[i + 1]
                i += 2
            else:
                controlflow.invalid_argument_exit(sys.argv[i], 'gam version')
    if simple:
        sys.stdout.write(GAM_VERSION)
        return
    pyversion = platform.python_version()
    cpu_bits = struct.calcsize('P') * 8
    api_client_ver = lib_version('google-api-python-client')
    print(
        (f'GAM {GAM_VERSION} - {GAM_URL} - {GM_Globals[GM_GAM_TYPE]}\n'
         f'{GAM_AUTHOR}\n'
         f'Python {pyversion} {cpu_bits}-bit {sys.version_info.releaselevel}\n'
         f'google-api-python-client {api_client_ver}\n'
         f'{getOSPlatform()} {platform.machine()}\n'
         f'Path: {GM_Globals[GM_GAM_PATH]}'))
    if sys.platform.startswith('win') and \
       cpu_bits == 32 and \
       platform.machine().find('64') != -1:
        print(MESSAGE_UPDATE_GAM_TO_64BIT)
    if timeOffset:
        offset, nicetime = getLocalGoogleTimeOffset(testLocation)
        print(MESSAGE_YOUR_SYSTEM_TIME_DIFFERS_FROM_GOOGLE_BY %
              (testLocation, nicetime))
        if offset > MAX_LOCAL_GOOGLE_TIME_OFFSET:
            controlflow.system_error_exit(4, 'Please fix your system time.')
    if force_check:
        doGAMCheckForUpdates(forceCheck=True)
    if extended:
        print(ssl.OPENSSL_VERSION)
        libs = ['cryptography',
                'filelock',
                'google-auth-httplib2',
                'google-auth-oauthlib',
                'google-auth',
                'httplib2',
                'passlib',
                'python-dateutil',
                'yubikey-manager',
                ]
        for lib in libs:
            try:
                print(f'{lib} {lib_version(lib)}')
            except:
                pass
        tls_ver, cipher_name, used_ip = _getServerTLSUsed(testLocation)
        print(
            f'{testLocation} ({used_ip}) connects using {tls_ver} {cipher_name}'
        )


def _getServerTLSUsed(location):
    url = f'https://{location}'
    _, netloc, _, _, _, _ = urlparse(url)
    conn = f'https:{netloc}'
    httpc = transport.create_http()
    headers = {'user-agent': GAM_INFO}
    retries = 5
    for n in range(1, retries + 1):
        try:
            httpc.request(url, headers=headers)
            break
        except (httplib2.ServerNotFoundError, RuntimeError) as e:
            if n != retries:
                httpc.connections = {}
                controlflow.wait_on_failure(n, retries, str(e))
                continue
            controlflow.system_error_exit(4, str(e))
    cipher_name, tls_ver, _ = httpc.connections[conn].sock.cipher()
    used_ip = httpc.connections[conn].sock.getpeername()[0]
    return tls_ver, cipher_name, used_ip


def _getSvcAcctData():
    if not GM_Globals[GM_OAUTH2SERVICE_JSON_DATA]:
        json_string = fileutils.read_file(GC_Values[GC_OAUTH2SERVICE_JSON],
                                          continue_on_error=True,
                                          display_errors=True)
        if not json_string:
            printLine(MESSAGE_INSTRUCTIONS_OAUTH2SERVICE_JSON)
            controlflow.system_error_exit(6, None)
        GM_Globals[GM_OAUTH2SERVICE_JSON_DATA] = json.loads(json_string)

jwt_apis = ['chat'] # APIs which can handle OAuthless JWT tokens
def getSvcAcctCredentials(scopes, act_as, api=None):
    try:
        _getSvcAcctData()
        sign_method = GM_Globals[GM_OAUTH2SERVICE_JSON_DATA].get('key_type', 'default')
        if act_as or api not in jwt_apis:
            if sign_method == 'default':
                credentials = google.oauth2.service_account.Credentials.from_service_account_info(
                    GM_Globals[GM_OAUTH2SERVICE_JSON_DATA])
            elif sign_method == 'yubikey':
                yksigner = yubikey.YubiKey(GM_Globals[GM_OAUTH2SERVICE_JSON_DATA])
                credentials = google.oauth2.service_account.Credentials._from_signer_and_info(yksigner,
                    GM_Globals[GM_OAUTH2SERVICE_JSON_DATA])
            credentials = credentials.with_scopes(scopes)
            if act_as:
                credentials = credentials.with_subject(act_as)
        else:
            audience = f'https://{api}.googleapis.com/'
            if sign_method == 'default':
                credentials = JWTCredentials.from_service_account_info(GM_Globals[GM_OAUTH2SERVICE_JSON_DATA],
                                                            audience=audience)
            elif sign_method == 'yubikey':
                yksigner = yubikey.YubiKey(GM_Globals[GM_OAUTH2SERVICE_JSON_DATA])
                credentials = JWTCredentials._from_signer_and_info(yksigner,
                                                                   GM_Globals[GM_OAUTH2SERVICE_JSON_DATA],
                                                                   audience=audience)
            credentials.project_id = GM_Globals[GM_OAUTH2SERVICE_JSON_DATA]['project_id']
        GM_Globals[GM_OAUTH2SERVICE_ACCOUNT_CLIENT_ID] = GM_Globals[
            GM_OAUTH2SERVICE_JSON_DATA]['client_id']
        return credentials
    except (ValueError, KeyError) as err:
        printLine(MESSAGE_INSTRUCTIONS_OAUTH2SERVICE_JSON)
        controlflow.invalid_json_exit(GC_Values[GC_OAUTH2SERVICE_JSON], err)


def getAPIVersion(api):
    version = API_VER_MAPPING.get(api, 'v1')
    api = API_NAME_MAPPING.get(api, api)
    return (api, version, f'{api}-{version}')


def readDiscoveryFile(api_version):
    disc_filename = f'{api_version}.json'
    disc_file = os.path.join(GM_Globals[GM_GAM_PATH], disc_filename)
    if hasattr(sys, '_MEIPASS'):
        pyinstaller_disc_file = os.path.join(sys._MEIPASS, disc_filename)  #pylint: disable=no-member
    else:
        pyinstaller_disc_file = None
    if os.path.isfile(disc_file):
        json_string = fileutils.read_file(disc_file)
    elif pyinstaller_disc_file:
        json_string = fileutils.read_file(pyinstaller_disc_file)
    else:
        controlflow.system_error_exit(
            11, MESSAGE_NO_DISCOVERY_INFORMATION.format(disc_file))
    try:
        discovery = json.loads(json_string)
        return (disc_file, discovery)
    except ValueError as err:
        controlflow.invalid_json_exit(disc_file, err)


def getOauth2TxtStorageCredentials():
    try:
        return auth.get_admin_credentials()
    except gam.auth.oauth.InvalidCredentialsFileError:
        # Maintain legacy behavior of this method that returns None if no
        # credential file is present.
        return None


def getValidOauth2TxtCredentials(force_refresh=False, api=None):
    """Gets OAuth2 credentials which are guaranteed to be fresh and valid."""
    try:
        credentials = auth.get_admin_credentials(api)
    except gam.auth.oauth.InvalidCredentialsFileError:
        doRequestOAuth()  # Make a new request which should store new creds.
        return getValidOauth2TxtCredentials(force_refresh=force_refresh,
                                            api=api)
    if credentials.expired or force_refresh:
        request = transport.create_request()
        credentials.refresh(request)
    return credentials


def getService(api, httpObj):
    api, version, api_version = getAPIVersion(api)
    if api in GM_Globals[GM_CURRENT_API_SERVICES] and version in GM_Globals[
            GM_CURRENT_API_SERVICES][api]:
        service = googleapiclient.discovery.build_from_document(
            GM_Globals[GM_CURRENT_API_SERVICES][api][version], http=httpObj)
        if GM_Globals[GM_CACHE_DISCOVERY_ONLY]:
            httpObj.cache = None
        return service
    if api in V1_DISCOVERY_APIS:
        discoveryServiceUrl = googleapiclient.discovery.DISCOVERY_URI
    else:
        discoveryServiceUrl = googleapiclient.discovery.V2_DISCOVERY_URI
    retries = 3
    for n in range(1, retries + 1):
        try:
            service = googleapiclient.discovery.build(
                api,
                version,
                http=httpObj,
                cache_discovery=False,
                static_discovery=False,
                discoveryServiceUrl=discoveryServiceUrl)
            GM_Globals[GM_CURRENT_API_SERVICES].setdefault(api, {})
            GM_Globals[GM_CURRENT_API_SERVICES][api][
                version] = service._rootDesc.copy()
            if GM_Globals[GM_CACHE_DISCOVERY_ONLY]:
                httpObj.cache = None
            return service
        except (httplib2.ServerNotFoundError, RuntimeError) as e:
            if n != retries:
                httpObj.connections = {}
                controlflow.wait_on_failure(n, retries, str(e))
                continue
            controlflow.system_error_exit(4, str(e))
        except (googleapiclient.errors.InvalidJsonError, KeyError,
                ValueError) as e:
            httpObj.cache = None
            if n != retries:
                controlflow.wait_on_failure(n, retries, str(e))
                continue
            controlflow.system_error_exit(17, str(e))
        except (http_client.ResponseNotReady, OSError,
                googleapiclient.errors.HttpError) as e:
            if 'The request is missing a valid API key' in str(e):
                break
            if n != retries:
                controlflow.wait_on_failure(n, retries, str(e))
                continue
            controlflow.system_error_exit(3, str(e))
        except googleapiclient.errors.UnknownApiNameOrVersion:
            break
    disc_file, discovery = readDiscoveryFile(api_version)
    try:
        service = googleapiclient.discovery.build_from_document(discovery,
                                                                http=httpObj)
        GM_Globals[GM_CURRENT_API_SERVICES].setdefault(api, {})
        GM_Globals[GM_CURRENT_API_SERVICES][api][
            version] = service._rootDesc.copy()
        if GM_Globals[GM_CACHE_DISCOVERY_ONLY]:
            httpObj.cache = None
        return service
    except (KeyError, ValueError):
        controlflow.invalid_json_exit(disc_file)


def buildGAPIObject(api):
    GM_Globals[GM_CURRENT_API_USER] = None
    credentials = getValidOauth2TxtCredentials(api=getAPIVersion(api)[0])
    credentials.user_agent = GAM_INFO
    httpObj = transport.AuthorizedHttp(
        credentials, transport.create_http(cache=GM_Globals[GM_CACHE_DIR]))
    service = getService(api, httpObj)
    if GC_Values[GC_DOMAIN]:
        if not GC_Values[GC_CUSTOMER_ID]:
            resp, result = service._http.request(
                f'https://www.googleapis.com/admin/directory/v1/users?domain={GC_Values[GC_DOMAIN]}&maxResults=1&fields=users(customerId)'
            )
            try:
                resultObj = json.loads(result)
            except ValueError:
                controlflow.system_error_exit(8,
                                              f'Unexpected response: {result}')
            if resp['status'] in ['403', '404']:
                try:
                    message = resultObj['error']['errors'][0]['message']
                except KeyError:
                    message = resultObj['error']['message']
                controlflow.system_error_exit(
                    8, f'{message} - {GC_Values[GC_DOMAIN]}')
            try:
                GC_Values[GC_CUSTOMER_ID] = resultObj['users'][0]['customerId']
            except KeyError:
                GC_Values[GC_CUSTOMER_ID] = MY_CUSTOMER
    else:
        GC_Values[GC_DOMAIN] = _getValueFromOAuth('hd', credentials=credentials)
        if GC_Values[GC_DOMAIN] == 'Unknown':
            GC_Values[GC_DOMAIN] = getEmailAddressDomain(
                _get_admin_email())
        if not GC_Values[GC_CUSTOMER_ID]:
            GC_Values[GC_CUSTOMER_ID] = MY_CUSTOMER
    return service


def buildGAPIObjectNoAuthentication(api):
    GM_Globals[GM_CURRENT_API_USER] = None
    httpObj = transport.create_http(cache=GM_Globals[GM_CACHE_DIR])
    service = getService(api, httpObj)
    return service

# Convert UID to email address
def convertUIDtoEmailAddress(emailAddressOrUID, cd=None, email_types=['user']):
    if isinstance(email_types, str):
        email_types = email_types.split(',')
    normalizedEmailAddressOrUID = normalizeEmailAddressOrUID(emailAddressOrUID)
    if normalizedEmailAddressOrUID.find('@') > 0:
        return normalizedEmailAddressOrUID
    if not cd:
        cd = buildGAPIObject('directory')
    if 'user' in email_types:
        try:
            result = gapi.call(
                cd.users(),
                'get',
                throw_reasons=[gapi_errors.ErrorReason.USER_NOT_FOUND],
                userKey=normalizedEmailAddressOrUID,
                fields='primaryEmail')
            if 'primaryEmail' in result:
                return result['primaryEmail'].lower()
        except gapi_errors.GapiUserNotFoundError:
            pass
    if 'group' in email_types:
        try:
            result = gapi.call(
                cd.groups(),
                'get',
                throw_reasons=[gapi_errors.ErrorReason.GROUP_NOT_FOUND],
                groupKey=normalizedEmailAddressOrUID,
                fields='email')
            if 'email' in result:
                return result['email'].lower()
        except gapi_errors.GapiGroupNotFoundError:
            pass
    if 'resource' in email_types:
        try:
            result = gapi.call(
                cd.resources().calendars(),
                'get',
                throw_reasons=[gapi_errors.ErrorReason.RESOURCE_NOT_FOUND],
                calendarResourceId=normalizedEmailAddressOrUID,
                customer=GC_Values[GC_CUSTOMER_ID],
                fields='resourceEmail')
            if 'resourceEmail' in result:
                return result['resourceEmail'].lower()
        except gapi_errors.GapiResourceNotFoundError:
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
                result = gapi.call(
                    cd.users(),
                    'get',
                    throw_reasons=[gapi_errors.ErrorReason.USER_NOT_FOUND],
                    userKey=normalizedEmailAddressOrUID,
                    fields='id')
                if 'id' in result:
                    return result['id']
            except gapi_errors.GapiUserNotFoundError:
                pass
        try:
            result = gapi.call(
                cd.groups(),
                'get',
                throw_reasons=[gapi_errors.ErrorReason.NOT_FOUND],
                groupKey=normalizedEmailAddressOrUID,
                fields='id')
            if 'id' in result:
                return result['id']
        except gapi_errors.GapiNotFoundError:
            pass
        return None
    return normalizedEmailAddressOrUID


def buildGAPIServiceObject(api, act_as, showAuthError=True, scopes=None):
    httpObj = transport.create_http(cache=GM_Globals[GM_CACHE_DIR])
    service = getService(api, httpObj)
    GM_Globals[GM_CURRENT_API_USER] = act_as
    if scopes:
        GM_Globals[GM_CURRENT_API_SCOPES] = scopes
    else:
        GM_Globals[GM_CURRENT_API_SCOPES] = API_SCOPE_MAPPING.get(
              api, service._rootDesc['auth']['oauth2']['scopes'])
    credentials = getSvcAcctCredentials(GM_Globals[GM_CURRENT_API_SCOPES],
                                        act_as, api)
    request = transport.create_request(httpObj)
    retries = 3
    for n in range(1, retries + 1):
        try:
            credentials.refresh(request)
            service._http = transport.AuthorizedHttp(credentials, http=httpObj)
            break
        except (httplib2.ServerNotFoundError, RuntimeError) as e:
            if n != retries:
                httpObj.connections = {}
                controlflow.wait_on_failure(n, retries, str(e))
                continue
            controlflow.system_error_exit(4, e)
        except google.auth.exceptions.RefreshError as e:
            if isinstance(e.args, tuple):
                e = e.args[0]
            if showAuthError:
                display.print_error(
                    f'User {GM_Globals[GM_CURRENT_API_USER]}: {str(e)}')
            return gapi.handle_oauth_token_error(str(e), True)
    return service


def buildAlertCenterGAPIObject(user):
    userEmail = convertUIDtoEmailAddress(user)
    return (userEmail, buildGAPIServiceObject('alertcenter', userEmail))


def buildActivityGAPIObject(user):
    userEmail = convertUIDtoEmailAddress(user)
    return (userEmail, buildGAPIServiceObject('driveactivity', userEmail))


def buildDriveGAPIObject(user):
    userEmail = convertUIDtoEmailAddress(user)
    return (userEmail, buildGAPIServiceObject('drive', userEmail))


def buildDrive3GAPIObject(user):
    userEmail = convertUIDtoEmailAddress(user)
    return (userEmail, buildGAPIServiceObject('drive3', userEmail))


def buildGmailGAPIObject(user):
    userEmail = convertUIDtoEmailAddress(user)
    return (userEmail, buildGAPIServiceObject('gmail', userEmail))


def printPassFail(description, result):
    print(f' {description:74} {result}')


def doCheckServiceAccount(users):
    i = 5
    test_pass = createGreenText('PASS')
    test_fail = createRedText('FAIL')
    test_warn = createYellowText('WARN')
    check_scopes = []
    while i < len(sys.argv):
        myarg = sys.argv[i].lower()
        if myarg in ['scope', 'scopes']:
            check_scopes = sys.argv[i + 1].replace(',', ' ').split()
            i += 2
        else:
            controlflow.invalid_argument_exit(
                myarg, 'gam user <email> check serviceaccount')
    print('Computer clock status:')
    timeOffset, nicetime = getLocalGoogleTimeOffset()
    if timeOffset < MAX_LOCAL_GOOGLE_TIME_OFFSET:
        time_status = test_pass
    else:
        time_status = test_fail
    printPassFail(
        MESSAGE_YOUR_SYSTEM_TIME_DIFFERS_FROM_GOOGLE_BY %
        ('admin.googleapis.com', nicetime), time_status)
    oa2 = getService('oauth2', transport.create_http())
    print('Service Account Private Key Authentication:')
    # We are explicitly not doing DwD here, just confirming service account can auth
    auth_error = ''
    try:
        credentials = getSvcAcctCredentials([USERINFO_EMAIL_SCOPE], None)
        request = transport.create_request()
        credentials.refresh(request)
        sa_token_info = gapi.call(oa2,
                                  'tokeninfo',
                                  access_token=credentials.token)
        if sa_token_info:
            sa_token_result = test_pass
        else:
            sa_token_result = test_fail
    except google.auth.exceptions.RefreshError as e:
        sa_token_result = test_fail
        auth_error = str(e.args[0])
    printPassFail(f'Authenticating...{auth_error}', sa_token_result)
    if sa_token_result == test_fail:
        controlflow.system_error_exit(
            3,
            'Invalid private key in oauth2service.json. Please delete the file and then\nrecreate with "gam create project" or "gam use project"'
        )
    print(
        'Checking key age. Google recommends rotating keys on a routine basis...'
    )
    try:
        iam = buildGAPIServiceObject('iam', None)
        project = GM_Globals[GM_OAUTH2SERVICE_ACCOUNT_CLIENT_ID]
        key_id = GM_Globals[GM_OAUTH2SERVICE_JSON_DATA]['private_key_id']
        name = f'projects/-/serviceAccounts/{project}/keys/{key_id}'
        key = gapi.call(iam.projects().serviceAccounts().keys(),
                        'get',
                        name=name,
                        throw_reasons=[gapi_errors.ErrorReason.FOUR_O_THREE])
        key_created = dateutil.parser.parse(
            key['validAfterTime'], ignoretz=True)
        key_age = datetime.datetime.now() - key_created
        key_days = key_age.days
        if key_days > 30:
            print(
                'Your key is old. Recommend running "gam rotate sakey" to get a new key'
            )
            key_age_result = test_warn
        else:
            key_age_result = test_pass
    except googleapiclient.errors.HttpError:
        key_age_result = test_warn
        key_days = 'UNKNOWN'
        print('Unable to check key age, please run "gam update project"')
    printPassFail(f'Key is {key_days} days old', key_age_result)
    if not check_scopes:
        for _, scopes in list(API_SCOPE_MAPPING.items()):
            for scope in scopes:
                if scope not in check_scopes:
                    check_scopes.append(scope)
    check_scopes.sort()
    for user in users:
        user = user.lower()
        all_scopes_pass = True
        #oa2 = getService('oauth2', transport.create_http())
        print(f'Domain-Wide Delegation authentication as {user}:')
        for scope in check_scopes:
            # try with and without email scope
            for scopes in [[scope, USERINFO_EMAIL_SCOPE], [scope]]:
                try:
                    credentials = getSvcAcctCredentials(scopes, user)
                    credentials.refresh(request)
                    break
                except (httplib2.ServerNotFoundError, RuntimeError) as e:
                    controlflow.system_error_exit(4, e)
                except google.auth.exceptions.RefreshError:
                    continue
            if credentials.token:
                token_info = gapi.call(oa2,
                                       'tokeninfo',
                                       access_token=credentials.token)
                if scope in token_info.get('scope', '').split(' ') and \
                   user == token_info.get('email', user).lower():
                    result = test_pass
                else:
                    result = test_fail
                    all_scopes_pass = False
            else:
                result = test_fail
                all_scopes_pass = False
            printPassFail(scope, result)
        service_account = GM_Globals[GM_OAUTH2SERVICE_ACCOUNT_CLIENT_ID]
        if all_scopes_pass:
            print(
                f'\nAll scopes passed!\nService account {service_account} is fully authorized.'
            )
            continue
        # Tack on email scope for more accurate checking
        check_scopes.append(USERINFO_EMAIL_SCOPE)
        long_url = ('https://admin.google.com/ac/owl/domainwidedelegation'
                    f'?clientScopeToAdd={",".join(check_scopes)}'
                    f'&clientIdToAdd={service_account}&overwriteClientId=true')
        short_url = utils.shorten_url(long_url)
        scopes_failed = f'''Some scopes failed! To authorize them, please go to:

  {short_url}

You will be directed to the Google Workspace admin console Security/API Controls/Domain-wide Delegation page
The "Add a new Client ID" box will open
Make sure that "Overwrite existing client ID" is checked
Please click Authorize to allow these scopes access.
After authorizing it may take some time for this test to pass so
go grab a cup of coffee and then try this command again.
'''
        controlflow.system_error_exit(1, scopes_failed)


# Batch processing request_id fields
RI_ENTITY = 0
RI_J = 1
RI_JCOUNT = 2
RI_ITEM = 3
RI_ROLE = 4


def batchRequestID(entityName, j, jcount, item, role=''):
    return f'{entityName}\n{j}\n{jcount}\n{item}\n{role}'


def watchGmail(users):
    project = f'projects/{_getCurrentProjectID()}'
    gamTopics = project + '/topics/gam-pubsub-gmail-'
    gamSubscriptions = project + '/subscriptions/gam-pubsub-gmail-'
    pubsub = buildGAPIObject('pubsub')
    topics = gapi.get_all_pages(pubsub.projects().topics(),
                                'list',
                                items='topics',
                                project=project)
    for atopic in topics:
        if atopic['name'].startswith(gamTopics):
            topic = atopic['name']
            break
    else:
        topic = gamTopics + str(uuid.uuid4())
        gapi.call(pubsub.projects().topics(), 'create', name=topic)
        body = {
            'policy': {
                'bindings': [{
                    'members': [
                        'serviceAccount:gmail-api-push@system.gserviceaccount.com'
                    ],
                    'role': 'roles/pubsub.editor'
                }]
            }
        }
        gapi.call(pubsub.projects().topics(),
                  'setIamPolicy',
                  resource=topic,
                  body=body)
    subscriptions = gapi.get_all_pages(
        pubsub.projects().topics().subscriptions(),
        'list',
        items='subscriptions',
        topic=topic)
    for asubscription in subscriptions:
        if asubscription.startswith(gamSubscriptions):
            subscription = asubscription
            break
    else:
        subscription = gamSubscriptions + str(uuid.uuid4())
        gapi.call(pubsub.projects().subscriptions(),
                  'create',
                  name=subscription,
                  body={'topic': topic})
    gmails = {}
    for user in users:
        gmails[user] = {'g': buildGmailGAPIObject(user)[1]}
        gapi.call(gmails[user]['g'].users(),
                  'watch',
                  userId='me',
                  body={'topicName': topic})
        gmails[user]['seen_historyId'] = gapi.call(
            gmails[user]['g'].users(),
            'getProfile',
            userId='me',
            fields='historyId')['historyId']
    print('Watching for events...')
    while True:
        results = gapi.call(pubsub.projects().subscriptions(),
                            'pull',
                            subscription=subscription,
                            body={'maxMessages': 100})
        if 'receivedMessages' in results:
            ackIds = []
            update_history = []
            for message in results['receivedMessages']:
                if 'data' in message['message']:
                    decoded_message = json.loads(
                        base64.b64decode(message['message']['data']))
                    if 'historyId' in decoded_message:
                        update_history.append(decoded_message['emailAddress'])
                if 'ackId' in message:
                    ackIds.append(message['ackId'])
            if ackIds:
                gapi.call(pubsub.projects().subscriptions(),
                          'acknowledge',
                          subscription=subscription,
                          body={'ackIds': ackIds})
            if update_history:
                for a_user in update_history:
                    results = gapi.call(
                        gmails[a_user]['g'].users().history(),
                        'list',
                        userId='me',
                        startHistoryId=gmails[a_user]['seen_historyId'])
                    if 'history' in results:
                        for history in results['history']:
                            if list(history) == ['messages', 'id']:
                                continue
                            if 'labelsAdded' in history:
                                for labelling in history['labelsAdded']:
                                    print(
                                        f'{a_user} labels {", ".join(labelling["labelIds"])} added to {labelling["message"]["id"]}'
                                    )
                            if 'labelsRemoved' in history:
                                for labelling in history['labelsRemoved']:
                                    print(
                                        f'{a_user} labels {", ".join(labelling["labelIds"])} removed from {labelling["message"]["id"]}'
                                    )
                            if 'messagesDeleted' in history:
                                for deleting in history['messagesDeleted']:
                                    print(
                                        f'{a_user} permanently deleted message {deleting["message"]["id"]}'
                                    )
                            if 'messagesAdded' in history:
                                for adding in history['messagesAdded']:
                                    print(
                                        f'{a_user} created message {adding["message"]["id"]} with labels {", ".join(adding["message"]["labelIds"])}'
                                    )
                    gmails[a_user]['seen_historyId'] = results['historyId']


def addDelegates(users, i):
    if i == 4:
        if sys.argv[i].lower() != 'to':
            controlflow.missing_argument_exit('to', 'gam <users> delegate')
        i += 1
    convertAlias = False
    if sys.argv[i].lower().replace('_', '') == 'convertalias':
        convertAlias = True
        i += 1
    delegate = normalizeEmailAddressOrUID(sys.argv[i], noUid=True)
    if convertAlias:
        delegate = gapi_directory_users.get_primary(delegate)
    i = 0
    count = len(users)
    for delegator in users:
        i += 1
        delegator, gmail = buildGmailGAPIObject(delegator)
        if not gmail:
            continue
        print(
            f'Giving {delegate} delegate access to {delegator}{currentCount(i, count)}'
        )
        gapi.call(gmail.users().settings().delegates(),
                  'create',
                  soft_errors=True,
                  userId='me',
                  body={'delegateEmail': delegate})


def gen_sha512_hash(password, rounds=10000):
    return sha512_crypt.hash(password, rounds=rounds)


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
            controlflow.invalid_argument_exit(sys.argv[i],
                f"gam <users> {['show', 'print'][csvFormat]} delegates")
    count = len(users)
    i = 1
    for user in users:
        user, gmail = buildGmailGAPIObject(user)
        if not gmail:
            continue
        sys.stderr.write(
            f'Getting delegates for {user}{currentCountNL(i, count)}')
        i += 1
        delegates = gapi.call(gmail.users().settings().delegates(),
                              'list',
                              soft_errors=True,
                              userId='me')
        if delegates and 'delegates' in delegates:
            for delegate in delegates['delegates']:
                delegateAddress = delegate['delegateEmail']
                status = delegate['verificationStatus']
                if csvFormat:
                    row = {
                        'User': user,
                        'delegateAddress': delegateAddress,
                        'delegationStatus': status
                    }
                    csvRows.append(row)
                else:
                    if csvStyle:
                        print(f'{user},{delegateAddress},{status}')
                    else:
                        print(
                            f'Delegator: {user}\n Status: {status}\n Delegate Email: {delegateAddress}\n'
                        )
            if not csvFormat and not csvStyle and delegates['delegates']:
                print(f'Total {len(delegates["delegates"])}')
    if csvFormat:
        display.write_csv_file(csvRows, titles, 'Delegates', todrive)


def deleteDelegate(users):
    convertAlias = False
    i = 5
    if sys.argv[i].lower().replace('_', '') == 'convertalias':
        convertAlias = True
        i += 1
    delegate = normalizeEmailAddressOrUID(sys.argv[i], noUid=True)
    if convertAlias:
        delegate = gapi_directory_users.get_primary(delegate)
    i = 0
    count = len(users)
    for user in users:
        i += 1
        user, gmail = buildGmailGAPIObject(user)
        if not gmail:
            continue
        print(
            f'Deleting {delegate} delegate access to {user}{currentCount(i, count)}'
        )
        gapi.call(gmail.users().settings().delegates(),
                  'delete',
                  soft_errors=True,
                  userId='me',
                  delegateEmail=delegate)


def doAddCourseParticipant():
    croom = buildGAPIObject('classroom')
    courseId = addCourseIdScope(sys.argv[2])
    noScopeCourseId = removeCourseIdScope(courseId)
    participant_type = sys.argv[4].lower()
    new_id = sys.argv[5]
    if participant_type in ['student', 'students']:
        new_id = normalizeEmailAddressOrUID(new_id)
        gapi.call(croom.courses().students(),
                  'create',
                  courseId=courseId,
                  body={'userId': new_id})
        print(f'Added {new_id} as a student of course {noScopeCourseId}')
    elif participant_type in ['teacher', 'teachers']:
        new_id = normalizeEmailAddressOrUID(new_id)
        gapi.call(croom.courses().teachers(),
                  'create',
                  courseId=courseId,
                  body={'userId': new_id})
        print(f'Added {new_id} as a teacher of course {noScopeCourseId}')
    elif participant_type in ['alias']:
        new_id = addCourseIdScope(new_id)
        gapi.call(croom.courses().aliases(),
                  'create',
                  courseId=courseId,
                  body={'alias': new_id})
        print(
            f'Added {removeCourseIdScope(new_id)} as an alias of course {noScopeCourseId}'
        )
    else:
        controlflow.invalid_argument_exit(participant_type, 'gam course ID add')


def doSyncCourseParticipants():
    courseId = addCourseIdScope(sys.argv[2])
    participant_type = sys.argv[4].lower()
    diff_entity_type = sys.argv[5].lower()
    diff_entity = sys.argv[6]
    current_course_users = getUsersToModify(entity_type=participant_type,
                                            entity=courseId)
    print()
    current_course_users = [x.lower() for x in current_course_users]
    if diff_entity_type == 'courseparticipants':
        diff_entity_type = participant_type
    diff_against_users = getUsersToModify(entity_type=diff_entity_type,
                                          entity=diff_entity)
    print()
    diff_against_users = [x.lower() for x in diff_against_users]
    to_add = list(set(diff_against_users) - set(current_course_users))
    to_remove = list(set(current_course_users) - set(diff_against_users))
    gam_commands = []
    for add_email in to_add:
        gam_commands.append(
            ['gam', 'course', courseId, 'add', participant_type, add_email])
    for remove_email in to_remove:
        gam_commands.append([
            'gam', 'course', courseId, 'remove', participant_type, remove_email
        ])
    run_batch(gam_commands)


def doDelCourseParticipant():
    croom = buildGAPIObject('classroom')
    courseId = addCourseIdScope(sys.argv[2])
    noScopeCourseId = removeCourseIdScope(courseId)
    participant_type = sys.argv[4].lower()
    remove_id = sys.argv[5]
    if participant_type in ['student', 'students']:
        remove_id = normalizeEmailAddressOrUID(remove_id)
        gapi.call(croom.courses().students(),
                  'delete',
                  courseId=courseId,
                  userId=remove_id)
        print(f'Removed {remove_id} as a student of course {noScopeCourseId}')
    elif participant_type in ['teacher', 'teachers']:
        remove_id = normalizeEmailAddressOrUID(remove_id)
        gapi.call(croom.courses().teachers(),
                  'delete',
                  courseId=courseId,
                  userId=remove_id)
        print(f'Removed {remove_id} as a teacher of course {noScopeCourseId}')
    elif participant_type in ['alias']:
        remove_id = addCourseIdScope(remove_id)
        gapi.call(croom.courses().aliases(),
                  'delete',
                  courseId=courseId,
                  alias=remove_id)
        print(
            f'Removed {removeCourseIdScope(remove_id)} as an alias of course {noScopeCourseId}'
        )
    else:
        controlflow.invalid_argument_exit(participant_type,
                                          'gam course ID delete')


def doDelCourse():
    croom = buildGAPIObject('classroom')
    courseId = addCourseIdScope(sys.argv[3])
    gapi.call(croom.courses(), 'delete', id=courseId)
    print(f'Deleted Course {courseId}')


def _getValidatedState(state, validStates):
    state = state.upper()
    if state not in validStates:
        controlflow.expected_argument_exit('course state',
                                           ', '.join(validStates).lower(),
                                           state.lower())
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
        validStates = gapi.get_enum_values_minus_unspecified(
            croom._rootDesc['schemas']['Course']['properties']['courseState']
            ['enum'])
        body['courseState'] = _getValidatedState(value, validStates)
    else:
        controlflow.invalid_argument_exit(myarg, f'gam {function} course')


def _getCourseStates(croom, value, courseStates):
    validStates = gapi.get_enum_values_minus_unspecified(
        croom._rootDesc['schemas']['Course']['properties']['courseState']
        ['enum'])
    for state in value.replace(',', ' ').split():
        courseStates.append(_getValidatedState(state, validStates))


def doUpdateCourse():
    croom = buildGAPIObject('classroom')
    courseId = addCourseIdScope(sys.argv[3])
    body = {}
    i = 4
    while i < len(sys.argv):
        myarg = sys.argv[i].lower()
        getCourseAttribute(myarg, sys.argv[i + 1], body, croom, 'update')
        i += 2
    updateMask = ','.join(list(body))
    body['id'] = courseId
    result = gapi.call(croom.courses(),
                       'patch',
                       id=courseId,
                       body=body,
                       updateMask=updateMask)
    print(f'Updated Course {result["id"]}')


def doDelAdmin():
    cd = buildGAPIObject('directory')
    roleAssignmentId = sys.argv[3]
    print(f'Deleting Admin Role Assignment {roleAssignmentId}')
    gapi.call(cd.roleAssignments(),
              'delete',
              customer=GC_Values[GC_CUSTOMER_ID],
              roleAssignmentId=roleAssignmentId)


def doCreateAdmin():
    cd = buildGAPIObject('directory')
    user = normalizeEmailAddressOrUID(sys.argv[3])
    body = {'assignedTo': convertEmailAddressToUID(user, cd)}
    role = sys.argv[4]
    body['roleId'] = getRoleId(role)
    body['scopeType'] = sys.argv[5].upper()
    if body['scopeType'] not in ['CUSTOMER', 'ORG_UNIT']:
        controlflow.expected_argument_exit('scope type',
                                           ', '.join(['customer', 'org_unit']),
                                           body['scopeType'])
    if body['scopeType'] == 'ORG_UNIT':
        orgUnit, orgUnitId = gapi_directory_orgunits.getOrgUnitId(
            sys.argv[6], cd)
        body['orgUnitId'] = orgUnitId[3:]
        scope = f'ORG_UNIT {orgUnit}'
    else:
        scope = 'CUSTOMER'
    print(f'Giving {user} admin role {role} for {scope}')
    gapi.call(cd.roleAssignments(),
              'insert',
              customer=GC_Values[GC_CUSTOMER_ID],
              body=body)


def doPrintAdmins():
    cd = buildGAPIObject('directory')
    roleId = None
    todrive = False
    kwargs = {}
    fields = 'nextPageToken,items(roleAssignmentId,roleId,assignedTo,scopeType,orgUnitId)'
    titles = [
        'roleAssignmentId', 'roleId', 'role', 'assignedTo', 'assignedToUser',
        'scopeType', 'orgUnitId', 'orgUnit'
    ]
    csvRows = []
    i = 3
    while i < len(sys.argv):
        myarg = sys.argv[i].lower()
        if myarg == 'user':
            kwargs['userKey'] = normalizeEmailAddressOrUID(sys.argv[i + 1])
            i += 2
        elif myarg == 'role':
            roleId = getRoleId(sys.argv[i + 1])
            i += 2
        elif myarg == 'todrive':
            todrive = True
            i += 1
        else:
            controlflow.invalid_argument_exit(sys.argv[i], 'gam print admins')
    if roleId and not kwargs:
        kwargs['roleId'] = roleId
        roleId = None
    admins = gapi.get_all_pages(cd.roleAssignments(),
                                'list',
                                'items',
                                customer=GC_Values[GC_CUSTOMER_ID],
                                fields=fields,
                                **kwargs)
    for admin in admins:
        if roleId and roleId != admin['roleId']:
            continue
        admin_attrib = {}
        for key, value in list(admin.items()):
            if key == 'assignedTo':
                admin_attrib['assignedToUser'] = user_from_userid(value)
            elif key == 'roleId':
                admin_attrib['role'] = role_from_roleid(value)
            elif key == 'orgUnitId':
                value = f'id:{value}'
                admin_attrib[
                    'orgUnit'] = gapi_directory_orgunits.orgunit_from_orgunitid(
                        value, cd)
            admin_attrib[key] = value
        csvRows.append(admin_attrib)
    display.write_csv_file(csvRows, titles, 'Admins', todrive)


def buildRoleIdToNameToIdMap():
    cd = buildGAPIObject('directory')
    result = gapi.get_all_pages(cd.roles(),
                                'list',
                                'items',
                                customer=GC_Values[GC_CUSTOMER_ID],
                                fields='nextPageToken,items(roleId,roleName)')
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
            controlflow.system_error_exit(
                4,
                f'{role} is not a valid role. Please ensure role name is exactly as shown in admin console.'
            )
    return roleId


def buildUserIdToNameMap():
    cd = buildGAPIObject('directory')
    result = gapi.get_all_pages(cd.users(),
                                'list',
                                'users',
                                customer=GC_Values[GC_CUSTOMER_ID],
                                fields='nextPageToken,users(id,primaryEmail)')
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
    online_services = gapi.get_all_pages(dt.applications(),
                                         'list',
                                         'applications',
                                         customerId=GC_Values[GC_CUSTOMER_ID])
    for online_service in online_services:
        if appID == online_service['id']:
            return online_service['name']
    return f'applicationId: {appID}'


def app2appID(dt, app):
    serviceName = app.lower()
    if serviceName in SERVICE_NAME_CHOICES_MAP:
        return (SERVICE_NAME_CHOICES_MAP[serviceName],
                SERVICE_NAME_TO_ID_MAP[SERVICE_NAME_CHOICES_MAP[serviceName]])
    online_services = gapi.get_all_pages(dt.applications(),
                                         'list',
                                         'applications',
                                         customerId=GC_Values[GC_CUSTOMER_ID])
    for online_service in online_services:
        if serviceName == online_service['name'].lower():
            return (online_service['name'], online_service['id'])
    controlflow.system_error_exit(
        2, f'{app} is not a valid service for data transfer.')


def convertToUserID(user):
    cg = UID_PATTERN.match(user)
    if cg:
        return cg.group(1)
    cd = buildGAPIObject('directory')
    if user.find('@') == -1:
        user = f'{user}@{GC_Values[GC_DOMAIN]}'
    try:
        return gapi.call(cd.users(),
                         'get',
                         throw_reasons=[
                             gapi_errors.ErrorReason.USER_NOT_FOUND,
                             gapi_errors.ErrorReason.BAD_REQUEST,
                             gapi_errors.ErrorReason.FORBIDDEN
                         ],
                         userKey=user,
                         fields='id')['id']
    except (gapi_errors.GapiUserNotFoundError, gapi_errors.GapiBadRequestError,
            gapi_errors.GapiForbiddenError):
        controlflow.system_error_exit(3, f'no such user {user}')


def convertUserIDtoEmail(uid):
    cd = buildGAPIObject('directory')
    try:
        return gapi.call(cd.users(),
                         'get',
                         throw_reasons=[
                             gapi_errors.ErrorReason.USER_NOT_FOUND,
                             gapi_errors.ErrorReason.BAD_REQUEST,
                             gapi_errors.ErrorReason.FORBIDDEN
                         ],
                         userKey=uid,
                         fields='primaryEmail')['primaryEmail']
    except (gapi_errors.GapiUserNotFoundError, gapi_errors.GapiBadRequestError,
            gapi_errors.GapiForbiddenError):
        return f'uid:{uid}'


def doCreateDataTransfer():
    dt = buildGAPIObject('datatransfer')
    body = {}
    old_owner = sys.argv[3]
    body['oldOwnerUserId'] = convertToUserID(old_owner)
    apps = sys.argv[4].split(',')
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
        parameters[sys.argv[i].upper()] = sys.argv[i + 1].upper().split(',')
        i += 2
    i = 0
    for key, value in list(parameters.items()):
        body['applicationDataTransfers'][i].setdefault(
            'applicationTransferParams', [])
        body['applicationDataTransfers'][i]['applicationTransferParams'].append(
            {
                'key': key,
                'value': value
            })
        i += 1
    result = gapi.call(dt.transfers(), 'insert', body=body, fields='id')['id']
    print(
        f'Submitted request id {result} to transfer {",".join(map(str, appNameList))} from {old_owner} to {new_owner}'
    )


def doPrintTransferApps():
    dt = buildGAPIObject('datatransfer')
    apps = gapi.get_all_pages(dt.applications(),
                              'list',
                              'applications',
                              customerId=GC_Values[GC_CUSTOMER_ID])
    display.print_json(apps)


def doPrintDataTransfers():
    dt = buildGAPIObject('datatransfer')
    i = 3
    newOwnerUserId = None
    oldOwnerUserId = None
    status = None
    todrive = False
    titles = [
        'id',
    ]
    csvRows = []
    while i < len(sys.argv):
        myarg = sys.argv[i].lower().replace('_', '')
        if myarg in ['olduser', 'oldowner']:
            oldOwnerUserId = convertToUserID(sys.argv[i + 1])
            i += 2
        elif myarg in ['newuser', 'newowner']:
            newOwnerUserId = convertToUserID(sys.argv[i + 1])
            i += 2
        elif myarg == 'status':
            status = sys.argv[i + 1]
            i += 2
        elif myarg == 'todrive':
            todrive = True
            i += 1
        else:
            controlflow.invalid_argument_exit(sys.argv[i],
                                              'gam print transfers')
    transfers = gapi.get_all_pages(dt.transfers(),
                                   'list',
                                   'dataTransfers',
                                   customerId=GC_Values[GC_CUSTOMER_ID],
                                   status=status,
                                   newOwnerUserId=newOwnerUserId,
                                   oldOwnerUserId=oldOwnerUserId)
    for transfer in transfers:
        for i in range(0, len(transfer['applicationDataTransfers'])):
            a_transfer = {}
            a_transfer['oldOwnerUserEmail'] = convertUserIDtoEmail(
                transfer['oldOwnerUserId'])
            a_transfer['newOwnerUserEmail'] = convertUserIDtoEmail(
                transfer['newOwnerUserId'])
            a_transfer['requestTime'] = transfer['requestTime']
            a_transfer['applicationId'] = transfer['applicationDataTransfers'][
                i]['applicationId']
            a_transfer['application'] = appID2app(dt,
                                                  a_transfer['applicationId'])
            a_transfer['status'] = transfer['applicationDataTransfers'][i][
                'applicationTransferStatus']
            a_transfer['id'] = transfer['id']
            if 'applicationTransferParams' in transfer[
                    'applicationDataTransfers'][i]:
                for param in transfer['applicationDataTransfers'][i][
                        'applicationTransferParams']:
                    a_transfer[param['key']] = ','.join(param.get('value', []))
        for title in a_transfer:
            if title not in titles:
                titles.append(title)
        csvRows.append(a_transfer)
    display.write_csv_file(csvRows, titles, 'Data Transfers', todrive)


def doGetDataTransferInfo():
    dt = buildGAPIObject('datatransfer')
    dtId = sys.argv[3]
    transfer = gapi.call(dt.transfers(), 'get', dataTransferId=dtId)
    print(f'Old Owner: {convertUserIDtoEmail(transfer["oldOwnerUserId"])}')
    print(f'New Owner: {convertUserIDtoEmail(transfer["newOwnerUserId"])}')
    print(f'Request Time: {transfer["requestTime"]}')
    for app in transfer['applicationDataTransfers']:
        print(f'Application: {appID2app(dt, app["applicationId"])}')
        print(f'Status: {app["applicationTransferStatus"]}')
        print('Parameters:')
        if 'applicationTransferParams' in app:
            for param in app['applicationTransferParams']:
                print(f' {param["key"]}: {",".join(param.get("value", []))}')
        else:
            print(' None')
        print()


def doPrintShowGuardians(csvFormat):
    croom = buildGAPIObject('classroom')
    invitedEmailAddress = None
    studentIds = [
        '-',
    ]
    states = None
    service = croom.userProfiles().guardians()
    items = 'guardians'
    itemName = 'Guardians'
    if csvFormat:
        csvRows = []
        todrive = False
        titles = [
            'studentEmail', 'studentId', 'invitedEmailAddress', 'guardianId'
        ]
    i = 3
    while i < len(sys.argv):
        myarg = sys.argv[i].lower()
        if csvFormat and myarg == 'todrive':
            todrive = True
            i += 1
        elif myarg == 'invitedguardian':
            invitedEmailAddress = normalizeEmailAddressOrUID(sys.argv[i + 1])
            i += 2
        elif myarg == 'student':
            studentIds = [
                normalizeStudentGuardianEmailAddressOrUID(sys.argv[i + 1])
            ]
            i += 2
        elif myarg == 'invitations':
            service = croom.userProfiles().guardianInvitations()
            items = 'guardianInvitations'
            itemName = 'Guardian Invitations'
            titles = [
                'studentEmail', 'studentId', 'invitedEmailAddress',
                'invitationId'
            ]
            if states is None:
                states = [
                    'COMPLETE', 'PENDING',
                    'GUARDIAN_INVITATION_STATE_UNSPECIFIED'
                ]
            i += 1
        elif myarg == 'states':
            states = sys.argv[i + 1].upper().replace(',', ' ').split()
            i += 2
        elif myarg in usergroup_types:
            studentIds = getUsersToModify(entity_type=myarg,
                                          entity=sys.argv[i + 1])
            i += 2
        else:
            controlflow.invalid_argument_exit(
                sys.argv[i], f"gam {['show', 'print'][csvFormat]} guardians")
    i = 0
    count = len(studentIds)
    for studentId in studentIds:
        i += 1
        studentId = normalizeStudentGuardianEmailAddressOrUID(studentId)
        kwargs = {
            'invitedEmailAddress': invitedEmailAddress,
            'studentId': studentId
        }
        if items == 'guardianInvitations':
            kwargs['states'] = states
        if studentId != '-':
            if csvFormat:
                sys.stderr.write('\r')
                sys.stderr.flush()
                sys.stderr.write(
                    f'Getting {itemName} for {studentId}{currentCount(i, count)}{" " * 40}'
                )
        guardians = gapi.get_all_pages(service,
                                       'list',
                                       items,
                                       soft_errors=True,
                                       **kwargs)
        if not csvFormat:
            print(f'Student: {studentId}, {itemName}:{currentCount(i, count)}')
            for guardian in guardians:
                display.print_json(guardian, spacing='  ')
        else:
            for guardian in guardians:
                guardian['studentEmail'] = studentId
                display.add_row_titles_to_csv_file(utils.flatten_json(guardian),
                                                   csvRows, titles)
    if csvFormat:
        sys.stderr.write('\n')
        display.write_csv_file(csvRows, titles, itemName, todrive)


def doInviteGuardian():
    croom = buildGAPIObject('classroom')
    body = {'invitedEmailAddress': normalizeEmailAddressOrUID(sys.argv[3])}
    studentId = normalizeStudentGuardianEmailAddressOrUID(sys.argv[4])
    result = gapi.call(croom.userProfiles().guardianInvitations(),
                       'create',
                       studentId=studentId,
                       body=body)
    print(
        f'Invited email {result["invitedEmailAddress"]} as guardian of {studentId}. Invite ID {result["invitationId"]}'
    )


def _cancelGuardianInvitation(croom, studentId, invitationId):
    try:
        result = gapi.call(croom.userProfiles().guardianInvitations(),
                           'patch',
                           throw_reasons=[
                               gapi_errors.ErrorReason.FAILED_PRECONDITION,
                               gapi_errors.ErrorReason.FORBIDDEN,
                               gapi_errors.ErrorReason.NOT_FOUND
                           ],
                           studentId=studentId,
                           invitationId=invitationId,
                           updateMask='state',
                           body={'state': 'COMPLETE'})
        print(
            f'Cancelled PENDING guardian invitation for {result["invitedEmailAddress"]} as guardian of {studentId}'
        )
        return True
    except gapi_errors.GapiFailedPreconditionError:
        display.print_error(
            f'Guardian invitation {invitationId} for {studentId} status is not PENDING'
        )
        GM_Globals[GM_SYSEXITRC] = 3
        return True
    except gapi_errors.GapiForbiddenError:
        entityUnknownWarning('Student', studentId, 0, 0)
        sys.exit(3)
    except gapi_errors.GapiNotFoundError:
        return False


def doCancelGuardianInvitation():
    croom = buildGAPIObject('classroom')
    invitationId = sys.argv[3]
    studentId = normalizeStudentGuardianEmailAddressOrUID(sys.argv[4])
    if not _cancelGuardianInvitation(croom, studentId, invitationId):
        controlflow.system_error_exit(
            3,
            f'Guardian invitation {invitationId} for {studentId} does not exist'
        )


def _deleteGuardian(croom, studentId, guardianId, guardianEmail):
    try:
        gapi.call(croom.userProfiles().guardians(),
                  'delete',
                  throw_reasons=[
                      gapi_errors.ErrorReason.FORBIDDEN,
                      gapi_errors.ErrorReason.NOT_FOUND
                  ],
                  studentId=studentId,
                  guardianId=guardianId)
        print(f'Deleted {guardianEmail} as a guardian of {studentId}')
        return True
    except gapi_errors.GapiForbiddenError:
        entityUnknownWarning('Student', studentId, 0, 0)
        sys.exit(3)
    except gapi_errors.GapiNotFoundError:
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
            controlflow.invalid_argument_exit(sys.argv[i],
                                              'gam delete guardian')
    if not invitationsOnly:
        if guardianIdIsEmail:
            try:
                results = gapi.get_all_pages(
                    croom.userProfiles().guardians(),
                    'list',
                    'guardians',
                    throw_reasons=[gapi_errors.ErrorReason.FORBIDDEN],
                    studentId=studentId,
                    invitedEmailAddress=guardianId,
                    fields='nextPageToken,guardians(studentId,guardianId)')
                if results:
                    for result in results:
                        _deleteGuardian(croom, result['studentId'],
                                        result['guardianId'], guardianId)
                    return
            except gapi_errors.GapiForbiddenError:
                entityUnknownWarning('Student', studentId, 0, 0)
                sys.exit(3)
        else:
            if _deleteGuardian(croom, studentId, guardianId, guardianId):
                return
    # See if there's a pending invitation
    if guardianIdIsEmail:
        try:
            results = gapi.get_all_pages(
                croom.userProfiles().guardianInvitations(),
                'list',
                'guardianInvitations',
                throw_reasons=[gapi_errors.ErrorReason.FORBIDDEN],
                studentId=studentId,
                invitedEmailAddress=guardianId,
                states=[
                    'PENDING',
                ],
                fields=
                'nextPageToken,guardianInvitations(studentId,invitationId)')
            if results:
                for result in results:
                    status = _cancelGuardianInvitation(croom,
                                                       result['studentId'],
                                                       result['invitationId'])
                sys.exit(status)
        except gapi_errors.GapiForbiddenError:
            entityUnknownWarning('Student', studentId, 0, 0)
            sys.exit(3)
    else:
        if _cancelGuardianInvitation(croom, studentId, guardianId):
            return
    controlflow.system_error_exit(
        3,
        f'{guardianId} is not a guardian of {studentId} and no invitation exists.'
    )


def doCreateCourse():
    croom = buildGAPIObject('classroom')
    body = {}
    i = 3
    while i < len(sys.argv):
        myarg = sys.argv[i].lower()
        if myarg in ['alias', 'id']:
            body['id'] = f'd:{sys.argv[i+1]}'
            i += 2
        else:
            getCourseAttribute(myarg, sys.argv[i + 1], body, croom, 'create')
            i += 2
    if 'ownerId' not in body:
        controlflow.system_error_exit(2, 'expected teacher <UserItem>)')
    if 'name' not in body:
        controlflow.system_error_exit(2, 'expected name <String>)')
    result = gapi.call(croom.courses(), 'create', body=body)
    print(f'Created course {result["id"]}')


def doGetCourseInfo():
    croom = buildGAPIObject('classroom')
    courseId = addCourseIdScope(sys.argv[3])
    info = gapi.call(croom.courses(), 'get', id=courseId)
    info['ownerEmail'] = convertUIDtoEmailAddress(f'uid:{info["ownerId"]}')
    display.print_json(info)
    teachers = gapi.get_all_pages(croom.courses().teachers(),
                                  'list',
                                  'teachers',
                                  courseId=courseId)
    students = gapi.get_all_pages(croom.courses().students(),
                                  'list',
                                  'students',
                                  courseId=courseId)
    try:
        aliases = gapi.get_all_pages(
            croom.courses().aliases(),
            'list',
            'aliases',
            throw_reasons=[gapi_errors.ErrorReason.NOT_IMPLEMENTED],
            courseId=courseId)
    except gapi_errors.GapiNotImplementedError:
        aliases = []
    if aliases:
        print('Aliases:')
        for alias in aliases:
            print(f'  {alias["alias"][2:]}')
    print('Participants:')
    print(' Teachers:')
    for teacher in teachers:
        try:
            print(
                f'  {teacher["profile"]["name"]["fullName"]} - {teacher["profile"]["emailAddress"]}'
            )
        except KeyError:
            print(f'  {teacher["profile"]["name"]["fullName"]}')
    print(' Students:')
    for student in students:
        try:
            print(
                f'  {student["profile"]["name"]["fullName"]} - {student["profile"]["emailAddress"]}'
            )
        except KeyError:
            print(f'  {student["profile"]["name"]["fullName"]}')


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
        fieldNameList = sys.argv[i + 1]
        for field in fieldNameList.lower().replace(',', ' ').split():
            if field in COURSE_ARGUMENT_TO_PROPERTY_MAP:
                if field != 'id':
                    fList.append(COURSE_ARGUMENT_TO_PROPERTY_MAP[field])
            else:
                controlflow.invalid_argument_exit(field,
                                                  f'gam print courses {myarg}')

    def _saveParticipants(course, participants, role):
        jcount = len(participants)
        course[role] = jcount
        display.add_titles_to_csv_file([role], titles)
        if countsOnly:
            return
        j = 0
        for member in participants:
            memberTitles = []
            prefix = f'{role}.{j}.'
            profile = member['profile']
            emailAddress = profile.get('emailAddress')
            if emailAddress:
                memberTitle = prefix + 'emailAddress'
                course[memberTitle] = emailAddress
                memberTitles.append(memberTitle)
            memberId = profile.get('id')
            if memberId:
                memberTitle = prefix + 'id'
                course[memberTitle] = memberId
                memberTitles.append(memberTitle)
            fullName = profile.get('name', {}).get('fullName')
            if fullName:
                memberTitle = prefix + 'name.fullName'
                course[memberTitle] = fullName
                memberTitles.append(memberTitle)
            display.add_titles_to_csv_file(memberTitles, titles)
            j += 1

    croom = buildGAPIObject('classroom')
    todrive = False
    fieldsList = []
    skipFieldsList = []
    titles = [
        'id',
    ]
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
            teacherId = normalizeEmailAddressOrUID(sys.argv[i + 1])
            i += 2
        elif myarg == 'student':
            studentId = normalizeEmailAddressOrUID(sys.argv[i + 1])
            i += 2
        elif myarg in ['state', 'states', 'status']:
            _getCourseStates(croom, sys.argv[i + 1], courseStates)
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
            delimiter = sys.argv[i + 1]
            i += 2
        elif myarg == 'show':
            showMembers = sys.argv[i + 1].lower()
            validShows = ['all', 'students', 'teachers']
            if showMembers not in validShows:
                controlflow.expected_argument_exit('show',
                                                   ', '.join(validShows),
                                                   showMembers)
            i += 2
        elif myarg == 'fields':
            if not fieldsList:
                fieldsList = [
                    'id',
                ]
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
            controlflow.invalid_argument_exit(sys.argv[i], 'gam print courses')
    if ownerEmails is not None and fieldsList:
        fieldsList.append('ownerId')
    fields = f'nextPageToken,courses({",".join(set(fieldsList))})' if fieldsList else None
    printGettingAllItems('Courses', None)
    page_message = gapi.got_total_items_msg('Courses', '...\n')
    all_courses = gapi.get_all_pages(croom.courses(),
                                     'list',
                                     'courses',
                                     page_message=page_message,
                                     teacherId=teacherId,
                                     studentId=studentId,
                                     courseStates=courseStates,
                                     fields=fields)
    for course in all_courses:
        if ownerEmails is not None:
            ownerId = course['ownerId']
            if ownerId not in ownerEmails:
                ownerEmails[ownerId] = convertUIDtoEmailAddress(f'uid:{ownerId}',
                                                                cd=cd)
            course['ownerEmail'] = ownerEmails[ownerId]
        for field in skipFieldsList:
            course.pop(field, None)
        display.add_row_titles_to_csv_file(utils.flatten_json(course), csvRows,
                                           titles)
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
                alias_message = gapi.got_total_items_msg(
                    f'Aliases for course {courseId}{currentCount(i, count)}',
                    '')
                course_aliases = gapi.get_all_pages(croom.courses().aliases(),
                                                    'list',
                                                    'aliases',
                                                    page_message=alias_message,
                                                    courseId=courseId)
                course['Aliases'] = delimiter.join(
                    [alias['alias'][2:] for alias in course_aliases])
            if showMembers:
                if showMembers != 'students':
                    teacher_message = gapi.got_total_items_msg(
                        f'Teachers for course {courseId}{currentCount(i, count)}',
                        '')
                    results = gapi.get_all_pages(croom.courses().teachers(),
                                                 'list',
                                                 'teachers',
                                                 page_message=teacher_message,
                                                 courseId=courseId,
                                                 fields=teachersFields)
                    _saveParticipants(course, results, 'teachers')
                if showMembers != 'teachers':
                    student_message = gapi.got_total_items_msg(
                        f'Students for course {courseId}{currentCount(i, count)}',
                        '')
                    results = gapi.get_all_pages(croom.courses().students(),
                                                 'list',
                                                 'students',
                                                 page_message=student_message,
                                                 courseId=courseId,
                                                 fields=studentsFields)
                    _saveParticipants(course, results, 'students')
    display.sort_csv_titles(['id', 'name'], titles)
    display.write_csv_file(csvRows, titles, 'Courses', todrive)


def doPrintCourseParticipants():
    croom = buildGAPIObject('classroom')
    todrive = False
    titles = [
        'courseId',
    ]
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
            courses.append(addCourseIdScope(sys.argv[i + 1]))
            i += 2
        elif myarg == 'teacher':
            teacherId = normalizeEmailAddressOrUID(sys.argv[i + 1])
            i += 2
        elif myarg == 'student':
            studentId = normalizeEmailAddressOrUID(sys.argv[i + 1])
            i += 2
        elif myarg in ['state', 'states', 'status']:
            _getCourseStates(croom, sys.argv[i + 1], courseStates)
            i += 2
        elif myarg == 'todrive':
            todrive = True
            i += 1
        elif myarg == 'show':
            showMembers = sys.argv[i + 1].lower()
            validShows = ['all', 'students', 'teachers']
            if showMembers not in validShows:
                controlflow.expected_argument_exit('show',
                                                   ', '.join(validShows),
                                                   showMembers)
            i += 2
        else:
            controlflow.invalid_argument_exit(sys.argv[i],
                                              'gam print course-participants')
    if not courses:
        printGettingAllItems('Courses', None)
        page_message = gapi.got_total_items_msg('Courses', '...\n')
        all_courses = gapi.get_all_pages(
            croom.courses(),
            'list',
            'courses',
            page_message=page_message,
            teacherId=teacherId,
            studentId=studentId,
            courseStates=courseStates,
            fields='nextPageToken,courses(id,name)')
    else:
        all_courses = []
        for course in courses:
            all_courses.append(
                gapi.call(croom.courses(), 'get', id=course, fields='id,name'))
    i = 0
    count = len(all_courses)
    for course in all_courses:
        i += 1
        courseId = course['id']
        if showMembers != 'students':
            page_message = gapi.got_total_items_msg(
                f'Teachers for course {courseId}{currentCount(i, count)}', '')
            teachers = gapi.get_all_pages(croom.courses().teachers(),
                                          'list',
                                          'teachers',
                                          page_message=page_message,
                                          courseId=courseId)
            for teacher in teachers:
                display.add_row_titles_to_csv_file(
                    utils.flatten_json(teacher,
                                       flattened={
                                           'courseId': courseId,
                                           'courseName': course['name'],
                                           'userRole': 'TEACHER'
                                       }), csvRows, titles)
        if showMembers != 'teachers':
            page_message = gapi.got_total_items_msg(
                f'Students for course {courseId}{currentCount(i, count)}', '')
            students = gapi.get_all_pages(croom.courses().students(),
                                          'list',
                                          'students',
                                          page_message=page_message,
                                          courseId=courseId)
            for student in students:
                display.add_row_titles_to_csv_file(
                    utils.flatten_json(student,
                                       flattened={
                                           'courseId': courseId,
                                           'courseName': course['name'],
                                           'userRole': 'STUDENT'
                                       }), csvRows, titles)
    display.sort_csv_titles(['courseId', 'courseName', 'userRole', 'userId'],
                            titles)
    display.write_csv_file(csvRows, titles, 'Course Participants', todrive)


def doProfile(users):
    cd = buildGAPIObject('directory')
    myarg = sys.argv[4].lower()
    if myarg in ['share', 'shared']:
        body = {'includeInGlobalAddressList': True}
    elif myarg in ['unshare', 'unshared']:
        body = {'includeInGlobalAddressList': False}
    else:
        controlflow.expected_argument_exit(
            'value for "gam <users> profile"',
            ', '.join(['share', 'shared', 'unshare', 'unshared']), sys.argv[4])
    i = 0
    count = len(users)
    for user in users:
        i += 1
        print(
            f'Setting Profile Sharing to {body["includeInGlobalAddressList"]} for {user}{currentCount(i, count)}'
        )
        gapi.call(cd.users(),
                  'update',
                  soft_errors=True,
                  userKey=user,
                  body=body)


def showProfile(users):
    cd = buildGAPIObject('directory')
    i = 0
    count = len(users)
    for user in users:
        i += 1
        result = gapi.call(cd.users(),
                           'get',
                           userKey=user,
                           fields='includeInGlobalAddressList')
        try:
            print(
                f'User: {user}  Profile Shared: {result["includeInGlobalAddressList"]}{currentCount(i, count)}'
            )
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
        print(
            f'Updating photo for {user} with {filename}{currentCount(i, count)}'
        )
        if re.match('^(ht|f)tps?://.*$', filename):
            simplehttp = transport.create_http()
            try:
                (_, image_data) = simplehttp.request(filename, 'GET')
            except (httplib2.HttpLib2Error, httplib2.ServerNotFoundError) as e:
                print(e)
                continue
        else:
            image_data = fileutils.read_file(filename,
                                             mode='rb',
                                             continue_on_error=True,
                                             display_errors=True)
            if image_data is None:
                continue
        body = {'photoData': base64.urlsafe_b64encode(image_data).decode(UTF8)}
        gapi.call(cd.users().photos(),
                  'update',
                  soft_errors=True,
                  userKey=user,
                  body=body)


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
            targetFolder = os.path.expanduser(sys.argv[i + 1])
            if not os.path.isdir(targetFolder):
                os.makedirs(targetFolder)
            i += 2
        elif myarg == 'noshow':
            showPhotoData = False
            i += 1
        else:
            controlflow.invalid_argument_exit(sys.argv[i],
                                              'gam <users> get photo')
    i = 0
    count = len(users)
    for user in users:
        i += 1
        filename = os.path.join(targetFolder, f'{user}.jpg')
        print(f'Saving photo to {filename}{currentCount(i, count)}')
        try:
            photo = gapi.call(cd.users().photos(),
                              'get',
                              throw_reasons=[
                                  gapi_errors.ErrorReason.USER_NOT_FOUND,
                                  gapi_errors.ErrorReason.RESOURCE_NOT_FOUND
                              ],
                              userKey=user)
        except gapi_errors.GapiUserNotFoundError:
            print(f' unknown user {user}')
            continue
        except gapi_errors.GapiResourceNotFoundError:
            print(f' no photo for {user}')
            continue
        try:
            photo_data = photo['photoData']
            if showPhotoData:
                print(photo_data)
        except KeyError:
            print(f' no photo for {user}')
            continue
        decoded_photo_data = base64.urlsafe_b64decode(photo_data)
        fileutils.write_file(filename,
                             decoded_photo_data,
                             mode='wb',
                             continue_on_error=True)


def deletePhoto(users):
    cd = buildGAPIObject('directory')
    i = 0
    count = len(users)
    for user in users:
        i += 1
        print(f'Deleting photo for {user}{currentCount(i, count)}')
        gapi.call(cd.users().photos(), 'delete', userKey=user, soft_errors=True)


def printDriveSettings(users):
    todrive = False
    i = 5
    while i < len(sys.argv):
        myarg = sys.argv[i].lower()
        if myarg == 'todrive':
            todrive = True
            i += 1
        else:
            controlflow.invalid_argument_exit(sys.argv[i],
                                              'gam <users> show drivesettings')
    dont_show = [
        'kind', 'exportFormats', 'importFormats', 'maxUploadSize',
        'maxImportSizes', 'user', 'appInstalled'
    ]
    csvRows = []
    titles = [
        'email',
    ]
    i = 0
    count = len(users)
    for user in users:
        i += 1
        user, drive = buildDrive3GAPIObject(user)
        if not drive:
            continue
        sys.stderr.write(
            f'Getting Drive settings for {user}{currentCountNL(i, count)}')
        feed = gapi.call(drive.about(), 'get', fields='*', soft_errors=True)
        if feed is None:
            continue
        row = {'email': user}
        for setting in feed:
            if setting in dont_show:
                continue
            if setting == 'storageQuota':
                for subsetting, value in feed[setting].items():
                    row[subsetting] = f'{int(value) / 1024 / 1024}mb'
                    if subsetting not in titles:
                        titles.append(subsetting)
                continue
            row[setting] = feed[setting]
            if setting not in titles:
                titles.append(setting)
        csvRows.append(row)
    display.write_csv_file(csvRows, titles, 'User Drive Settings', todrive)


def getTeamDriveThemes(users):
    for user in users:
        user, drive = buildDrive3GAPIObject(user)
        if not drive:
            continue
        themes = gapi.call(drive.about(),
                           'get',
                           fields='teamDriveThemes',
                           soft_errors=True)
        if themes is None or 'teamDriveThemes' not in themes:
            continue
        print('theme')
        for theme in themes['teamDriveThemes']:
            print(theme['id'])


def printDriveActivity(users):
    def _get_user_info(user_id):
        if user_id.startswith('people/'):
            user_id = user_id[7:]
        entry = user_info.get(user_id)
        if entry is None:
            result = gapi.call(cd.users(), 'get',
                              soft_errors=True,
                              userKey=user_id, fields='primaryEmail,name.fullName')
            if result:
                entry = (result['primaryEmail'], result['name']['fullName'])
            else:
                entry = (f'uid:{user_id}', 'Unknown')
            user_info[user_id] = entry
        return entry

    def _update_known_users(structure):
        if isinstance(structure, list):
          for v in structure:
              if isinstance(v, (dict, list)):
                  _update_known_users(v)
        elif isinstance(structure, dict):
          for k, v in sorted(iter(structure.items())):
              if k != 'knownUser':
                  if isinstance(v, (dict, list)):
                      _update_known_users(v)
              else:
                  entry = _get_user_info(v['personName'])
                  v['emailAddress'] = entry[0]
                  v['personName'] = entry[1]
                  break

    cd = buildGAPIObject('directory')
    drive_key = 'ancestorName'
    drive_fileId = 'root'
    user_info = {}
    todrive = False
    titles = [
        'user.name', 'user.emailAddress', 'target.id', 'target.name',
        'target.mimeType', 'eventTime'
    ]
    sort_titles = titles[:]
    csvRows = []
    i = 5
    while i < len(sys.argv):
        activity_object = sys.argv[i].lower().replace('_', '')
        if activity_object == 'fileid':
            drive_fileId = sys.argv[i + 1]
            drive_key = 'itemName'
            i += 2
        elif activity_object == 'folderid':
            drive_fileId = sys.argv[i + 1]
            drive_key = 'ancestorName'
            i += 2
        elif activity_object == 'todrive':
            todrive = True
            i += 1
        else:
            controlflow.invalid_argument_exit(sys.argv[i],
                                              'gam <users> show driveactivity')

    for user in users:
        user, activity = buildActivityGAPIObject(user)
        if not activity:
            continue
        page_token = None
        total_items = 0
        kwargs = {drive_key: f'items/{drive_fileId}',
                  'pageToken': page_token}
        page_message = gapi.got_total_items_msg(f'Activities for {user}', '')
        while True:
          feed = gapi.call(activity.activity(), 'query', body=kwargs)
          page_token, total_items = gapi.process_page(feed, 'activities', None, total_items, page_message, None)
          kwargs['pageToken'] = page_token
          if feed:
              for activity_event in feed.get('activities', []):
                  event_row = {}
                  actors = activity_event.get('actors', [])
                  if actors:
                      userId = actors[0].get('user', {}).get('knownUser', {}).get('personName', '')
                      if not userId:
                          userId = actors[0].get('impersonation', {}).get('impersonatedUser', {}).get('knownUser', {}).get('personName', '')
                      if userId:
                          entry = _get_user_info(userId)
                          event_row['user.name'] = entry[1]
                          event_row['user.emailAddress'] = entry[0]
                  targets = activity_event.get('targets', [])
                  if targets:
                      driveItem = targets[0].get('driveItem')
                      if driveItem:
                          event_row['target.id'] = driveItem['name'][6:]
                          event_row['target.name'] = driveItem['title']
                          event_row['target.mimeType'] = driveItem['mimeType']
                      else:
                          teamDrive = targets[0].get('teamDrive')
                          if teamDrive:
                              event_row['target.id'] = teamDrive['name'][11:]
                              event_row['target.name'] = teamDrive['title']
                  if 'timestamp' in activity_event:
                      event_row['eventTime'] = activity_event.pop('timestamp')
                  elif 'timeRange' in activity_event:
                      timeRange = activity_event.pop('timeRange')
                      event_row['eventTime'] = f'{timeRange["startTime"]}-{timeRange["endTime"]}'
                  _update_known_users(activity_event)
                  display.add_row_titles_to_csv_file(
                      utils.flatten_json(activity_event, flattened=event_row), csvRows, titles)
              del feed
          if not page_token:
              gapi.finalize_page_message(page_message)
              break
    display.sort_csv_titles(sort_titles, titles)
    display.write_csv_file(csvRows, titles, 'Drive Activity', todrive)


def printPermission(permission):
    if 'name' in permission:
        print(permission['name'])
    elif 'id' in permission:
        if permission['id'] == 'anyone':
            print('Anyone')
        elif permission['id'] == 'anyoneWithLink':
            print('Anyone with Link')
        else:
            print(permission['id'])
    for key in permission:
        if key in [
                'name',
                'kind',
                'etag',
                'selfLink',
        ]:
            continue
        print(f' {key}: {permission[key]}')


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
            controlflow.invalid_argument_exit(sys.argv[i],
                                              'gam <users> show drivefileacl')
    for user in users:
        user, drive = buildDrive3GAPIObject(user)
        if not drive:
            continue
        feed = gapi.get_all_pages(drive.permissions(),
                                  'list',
                                  'permissions',
                                  fileId=fileId,
                                  fields='*',
                                  supportsAllDrives=True,
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
        permissionId = f'{permissionId}@{GC_Values[GC_DOMAIN].lower()}'
    # We have to use v2 here since v3 has no permissions.getIdForEmail equivalent
    # https://code.google.com/a/google.com/p/apps-api-issues/issues/detail?id=4313
    _, drive2 = buildDriveGAPIObject(_get_admin_email())
    return gapi.call(drive2.permissions(),
                     'getIdForEmail',
                     email=permissionId,
                     fields='id')['id']


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
            controlflow.invalid_argument_exit(
                sys.argv[i], 'gam <users> delete drivefileacl')
    for user in users:
        user, drive = buildDrive3GAPIObject(user)
        if not drive:
            continue
        print(f'Removing permission for {permissionId} from {fileId}')
        gapi.call(drive.permissions(),
                  'delete',
                  fileId=fileId,
                  permissionId=permissionId,
                  supportsAllDrives=True,
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
    ubody = {}
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
        controlflow.expected_argument_exit(
            'permission type', ', '.join(['user', 'group', 'domain', 'anyone']),
            body['type'])
    while i < len(sys.argv):
        myarg = sys.argv[i].lower().replace('_', '')
        if myarg == 'withlink':
            body['allowFileDiscovery'] = False
            i += 1
        elif myarg == 'discoverable':
            body['allowFileDiscovery'] = True
            i += 1
        elif myarg == 'role':
            role = sys.argv[i + 1].lower()
            if role not in DRIVEFILE_ACL_ROLES_MAP:
                controlflow.expected_argument_exit(
                    'role', ', '.join(DRIVEFILE_ACL_ROLES_MAP), role)
            body['role'] = DRIVEFILE_ACL_ROLES_MAP[role]
            if body['role'] == 'owner':
                sendNotificationEmail = True
                transferOwnership = True
            ubody['role'] = body['role']
            i += 2
        elif myarg == 'sendemail':
            sendNotificationEmail = True
            i += 1
        elif myarg == 'emailmessage':
            sendNotificationEmail = True
            emailMessage = sys.argv[i + 1]
            i += 2
        elif myarg == 'expires':
            ubody['expirationTime'] = utils.get_time_or_delta_from_now(
                sys.argv[i + 1])
            i += 2
        elif myarg == 'asadmin':
            useDomainAdminAccess = True
            i += 1
        else:
            controlflow.invalid_argument_exit(sys.argv[i],
                                              'gam <users> add drivefileacl')
    for user in users:
        user, drive = buildDrive3GAPIObject(user)
        if not drive:
            continue
        result = gapi.call(drive.permissions(),
                           'create',
                           fields='*',
                           fileId=fileId,
                           sendNotificationEmail=sendNotificationEmail,
                           emailMessage=emailMessage,
                           body=body,
                           supportsAllDrives=True,
                           transferOwnership=transferOwnership,
                           useDomainAdminAccess=useDomainAdminAccess)
        if 'expirationTime' in ubody:
            result = gapi.call(drive.permissions(),
                               'update',
                               fields='*',
                               fileId=fileId,
                               permissionId=result['id'],
                               removeExpiration=False,
                               transferOwnership=False,
                               body=ubody,
                               supportsAllDrives=True,
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
            role = sys.argv[i + 1].lower()
            if role not in DRIVEFILE_ACL_ROLES_MAP:
                controlflow.expected_argument_exit(
                    'role', ', '.join(DRIVEFILE_ACL_ROLES_MAP), role)
            body['role'] = DRIVEFILE_ACL_ROLES_MAP[role]
            if body['role'] == 'owner':
                transferOwnership = True
            i += 2
        elif myarg == 'asadmin':
            useDomainAdminAccess = True
            i += 1
        else:
            controlflow.invalid_argument_exit(
                sys.argv[i], 'gam <users> update drivefileacl')
    for user in users:
        user, drive = buildDrive3GAPIObject(user)
        if not drive:
            continue
        print(f'updating permissions for {permissionId} to file {fileId}')
        result = gapi.call(drive.permissions(),
                           'update',
                           fields='*',
                           fileId=fileId,
                           permissionId=permissionId,
                           removeExpiration=removeExpiration,
                           transferOwnership=transferOwnership,
                           body=body,
                           supportsAllDrives=True,
                           useDomainAdminAccess=useDomainAdminAccess)
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
    titles = [
        'Owner',
    ]
    csvRows = []
    query = "'me' in owners"
    i = 5
    while i < len(sys.argv):
        myarg = sys.argv[i].lower().replace('_', '')
        if myarg == 'todrive':
            todrive = True
            i += 1
        elif myarg == 'orderby':
            fieldName = sys.argv[i + 1].lower()
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
                    orderByList.append(f'{fieldName} desc')
            else:
                controlflow.expected_argument_exit(
                    'orderby', ', '.join(sorted(DRIVEFILE_ORDERBY_CHOICES_MAP)),
                    fieldName)
        elif myarg == 'query':
            query += f' and {sys.argv[i+1]}'
            i += 2
        elif myarg == 'fullquery':
            query = sys.argv[i + 1]
            i += 2
        elif myarg == 'anyowner':
            anyowner = True
            i += 1
        elif myarg == 'allfields':
            fieldsList = []
            allfields = True
            i += 1
        elif myarg in DRIVEFILE_FIELDS_CHOICES_MAP:
            display.add_field_to_csv_file(
                myarg, {myarg: [DRIVEFILE_FIELDS_CHOICES_MAP[myarg]]},
                fieldsList, fieldsTitles, titles)
            i += 1
        elif myarg in DRIVEFILE_LABEL_CHOICES_MAP:
            display.add_field_to_csv_file(
                myarg, {myarg: [DRIVEFILE_LABEL_CHOICES_MAP[myarg]]},
                labelsList, fieldsTitles, titles)
            i += 1
        else:
            controlflow.invalid_argument_exit(myarg,
                                              'gam <users> show filelist')
    if fieldsList or labelsList:
        fields = 'nextPageToken,items('
        if fieldsList:
            fields += ','.join(set(fieldsList))
            if labelsList:
                fields += ','
        if labelsList:
            fields += f'labels({",".join(set(labelsList))})'
        fields += ')'
    elif not allfields:
        for field in ['name', 'alternatelink']:
            display.add_field_to_csv_file(
                field, {field: [DRIVEFILE_FIELDS_CHOICES_MAP[field]]},
                fieldsList, fieldsTitles, titles)
        fields = f'nextPageToken,items({",".join(set(fieldsList))})'
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
        sys.stderr.write(f'Getting files for {user}...\n')
        page_message = gapi.got_total_items_msg(f'Files for {user}', '...\n')
        feed = gapi.get_all_pages(drive.files(),
                                  'list',
                                  'items',
                                  page_message=page_message,
                                  soft_errors=True,
                                  q=query,
                                  orderBy=orderBy,
                                  fields=fields)
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
                                a_file[attrib] = len(f_file[attrib])
                                for j, l_attrib in enumerate(f_file[attrib]):
                                    for list_attrib in l_attrib:
                                        if list_attrib in [
                                                'kind', 'etag', 'selfLink'
                                        ]:
                                            continue
                                        if not isinstance(l_attrib[list_attrib], dict):
                                            x_attrib = f'{attrib}.{j}.{list_attrib}'
                                            if x_attrib not in titles:
                                                titles.append(x_attrib)
                                            a_file[x_attrib] = l_attrib[list_attrib]
                                        else:
                                            for sl_attrib in l_attrib[list_attrib]:
                                                if sl_attrib in [
                                                        'kind', 'etag', 'selfLink'
                                                ]:
                                                    continue
                                                x_attrib = f'{attrib}.{j}.{list_attrib}.{sl_attrib}'
                                                if x_attrib not in titles:
                                                    titles.append(x_attrib)
                                                a_file[x_attrib] = l_attrib[list_attrib][sl_attrib]
                    elif isinstance(f_file[attrib], (str, int, bool)):
                        if attrib not in titles:
                            titles.append(attrib)
                        a_file[attrib] = f_file[attrib]
                    else:
                        sys.stderr.write(
                            f'File ID: {f_file["id"]}, Attribute: {attrib}, Unknown type: {type(f_file[attrib])}\n'
                        )
                elif attrib == 'labels':
                    for dict_attrib in f_file[attrib]:
                        if dict_attrib not in titles:
                            titles.append(dict_attrib)
                        a_file[dict_attrib] = f_file[attrib][dict_attrib]
                else:
                    for dict_attrib in f_file[attrib]:
                        if dict_attrib in ['kind', 'etag']:
                            continue
                        x_attrib = f'{attrib}.{dict_attrib}'
                        if x_attrib not in titles:
                            titles.append(x_attrib)
                        a_file[x_attrib] = f_file[attrib][dict_attrib]
            csvRows.append(a_file)
    if allfields:
        display.sort_csv_titles(['Owner', 'id', 'title'], titles)
    display.write_csv_file(csvRows, titles,
                           f'{sys.argv[1]} {sys.argv[2]} Drive Files', todrive)


def doDriveSearch(drive, query=None, quiet=False):
    if not quiet:
        print(f'Searching for files with query: "{query}"...')
        page_message = gapi.got_total_items_msg('Files', '...\n')
    else:
        page_message = None
    files = gapi.get_all_pages(drive.files(),
                               'list',
                               'items',
                               page_message=page_message,
                               q=query,
                               fields='nextPageToken,items(id)')
    ids = list()
    for f_file in files:
        ids.append(f_file['id'])
    return ids


def getFileIdFromAlternateLink(altLink):
    loc = altLink.find('/d/')
    if loc > 0:
        fileId = altLink[loc + 3:]
        loc = fileId.find('/')
        if loc != -1:
            return fileId[:loc]
    else:
        loc = altLink.find('/folderview?id=')
        if loc > 0:
            fileId = altLink[loc + 15:]
            loc = fileId.find('&')
            if loc != -1:
                return fileId[:loc]
    controlflow.system_error_exit(
        2, f'{altLink} is not a valid Drive File alternateLink')


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
            controlflow.invalid_argument_exit(sys.argv[i],
                                              'gam <users> delete drivefile')
    action = DELETE_DRIVEFILE_FUNCTION_TO_ACTION_MAP[function]
    for user in users:
        user, drive = buildDriveGAPIObject(user)
        if not drive:
            continue
        if fileIds[:6].lower() == 'query:':
            file_ids = doDriveSearch(drive, query=fileIds[6:])
        else:
            if fileIds[:8].lower() == 'https://' or fileIds[:7].lower(
            ) == 'http://':
                fileIds = getFileIdFromAlternateLink(fileIds)
            file_ids = [
                fileIds,
            ]
        if not file_ids:
            print(f'No files to {function} for {user}')
        j = 0
        batch_size = 10
        dbatch = drive.new_batch_http_request(callback=drive_del_result)
        method = getattr(drive.files(), function)
        for fileId in file_ids:
            j += 1
            dbatch.add(method(fileId=fileId, supportsAllDrives=True))
            if len(dbatch._order) == batch_size:
                print(f'{action} {len(dbatch._order)} files...')
                dbatch.execute()
                dbatch = drive.new_batch_http_request(callback=drive_del_result)
        if len(dbatch._order) > 0:
            print(f'{action} {len(dbatch._order)} files...')
            dbatch.execute()


def drive_del_result(request_id, response, exception):
    if exception:
        print(exception)


def printDriveFolderContents(feed, folderId, indent):
    for f_file in feed:
        for parent in f_file['parents']:
            if folderId == parent['id']:
                print(' ' * indent, f_file['title'])
                if f_file['mimeType'] == 'application/vnd.google-apps.folder':
                    printDriveFolderContents(feed, f_file['id'], indent + 1)
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
            fieldName = sys.argv[i + 1].lower()
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
                    orderByList.append(f'{fieldName} desc')
            else:
                controlflow.expected_argument_exit(
                    'orderby', ', '.join(sorted(DRIVEFILE_ORDERBY_CHOICES_MAP)),
                    fieldName)
        else:
            controlflow.invalid_argument_exit(myarg,
                                              'gam <users> show filetree')
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
        root_folder = gapi.call(drive.about(), 'get',
                                fields='rootFolderId')['rootFolderId']
        sys.stderr.write(f'Getting all files for {user}...\n')
        page_message = gapi.got_total_items_msg(f'Files for {user}', '...\n')
        feed = gapi.get_all_pages(
            drive.files(),
            'list',
            'items',
            page_message=page_message,
            q=query,
            orderBy=orderBy,
            fields='items(id,title,parents(id),mimeType),nextPageToken')
        printDriveFolderContents(feed, root_folder, 0)


def deleteEmptyDriveFolders(users):
    query = '"me" in owners and mimeType = "application/vnd.google-apps.folder"'
    for user in users:
        user, drive = buildDriveGAPIObject(user)
        if not drive:
            continue
        deleted_empty = True
        while deleted_empty:
            sys.stderr.write(f'Getting folders for {user}...\n')
            page_message = gapi.got_total_items_msg(f'Folders for {user}',
                                                    '...\n')
            feed = gapi.get_all_pages(drive.files(),
                                      'list',
                                      'items',
                                      page_message=page_message,
                                      q=query,
                                      fields='items(title,id),nextPageToken')
            deleted_empty = False
            for folder in feed:
                children = gapi.call(drive.children(),
                                     'list',
                                     folderId=folder['id'],
                                     fields='items(id)',
                                     maxResults=1)
                if 'items' not in children or not children['items']:
                    print(f' deleting empty folder {folder["title"]}...')
                    gapi.call(drive.files(), 'delete', fileId=folder['id'])
                    deleted_empty = True
                else:
                    print(
                        f' not deleting folder {folder["title"]} because it contains at least 1 item ({children["items"][0]["id"]})'
                    )


def doEmptyDriveTrash(users):
    for user in users:
        user, drive = buildDrive3GAPIObject(user)
        if not drive:
            continue
        print(f'Emptying Drive trash for {user}')
        gapi.call(drive.files(), 'emptyTrash')


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
    return ({}, {
        DFA_LOCALFILEPATH: None,
        DFA_LOCALFILENAME: None,
        DFA_LOCALMIMETYPE: None,
        DFA_CONVERT: None,
        DFA_OCR: None,
        DFA_OCRLANGUAGE: None,
        DFA_PARENTQUERY: None
    })


def getDriveFileAttribute(i, body, parameters, myarg, update=False):
    operation = 'update' if update else 'add'
    if myarg == 'localfile':
        parameters[DFA_LOCALFILEPATH] = sys.argv[i + 1]
        if parameters[DFA_LOCALFILEPATH] != '-':
            parameters[DFA_LOCALFILENAME] = os.path.basename(
                parameters[DFA_LOCALFILEPATH])
            body.setdefault('title', parameters[DFA_LOCALFILENAME])
            body['mimeType'] = mimetypes.guess_type(
                parameters[DFA_LOCALFILEPATH])[0]
            if body['mimeType'] is None:
                body['mimeType'] = 'application/octet-stream'
            parameters[DFA_LOCALMIMETYPE] = body['mimeType']
        else:
            parameters[DFA_LOCALFILENAME] = '-'
            if body.get('mimeType') is None:
                body['mimeType'] = 'application/octet-stream'
        i += 2
    elif myarg == 'convert':
        parameters[DFA_CONVERT] = True
        i += 1
    elif myarg == 'ocr':
        parameters[DFA_OCR] = True
        i += 1
    elif myarg == 'ocrlanguage':
        parameters[DFA_OCRLANGUAGE] = LANGUAGE_CODES_MAP.get(
            sys.argv[i + 1].lower(), sys.argv[i + 1])
        i += 2
    elif myarg in ['copyrequireswriterpermission', 'restrict', 'restricted']:
        if update:
            body['copyRequiresWriterPermission'] = getBoolean(
                sys.argv[i + 1], myarg)
            i += 2
        else:
            body['copyRequiresWriterPermission'] = True
            i += 1
    elif myarg in DRIVEFILE_LABEL_CHOICES_MAP:
        body.setdefault('labels', {})
        if update:
            body['labels'][DRIVEFILE_LABEL_CHOICES_MAP[myarg]] = getBoolean(
                sys.argv[i + 1], myarg)
            i += 2
        else:
            body['labels'][DRIVEFILE_LABEL_CHOICES_MAP[myarg]] = True
            i += 1
    elif myarg in [
            'lastviewedbyme', 'lastviewedbyuser', 'lastviewedbymedate',
            'lastviewedbymetime'
    ]:
        body['lastViewedByMeDate'] = utils.get_time_or_delta_from_now(
            sys.argv[i + 1])
        i += 2
    elif myarg in ['modifieddate', 'modifiedtime']:
        body['modifiedDate'] = utils.get_time_or_delta_from_now(sys.argv[i + 1])
        i += 2
    elif myarg == 'description':
        body['description'] = sys.argv[i + 1]
        i += 2
    elif myarg == 'mimetype':
        mimeType = sys.argv[i + 1]
        if mimeType in MIMETYPE_CHOICES_MAP:
            body['mimeType'] = MIMETYPE_CHOICES_MAP[mimeType]
        else:
            controlflow.expected_argument_exit('mimetype',
                                               ', '.join(MIMETYPE_CHOICES_MAP),
                                               mimeType)
        i += 2
    elif myarg == 'parentid':
        body.setdefault('parents', [])
        body['parents'].append({'id': sys.argv[i + 1]})
        i += 2
    elif myarg == 'parentname':
        parameters[
            DFA_PARENTQUERY] = f"'me' in owners and mimeType = '{MIMETYPE_GA_FOLDER}' and title = '{escapeDriveFileName(sys.argv[i+1])}'"
        i += 2
    elif myarg in ['anyownerparentname']:
        parameters[
            DFA_PARENTQUERY] = f"mimeType = '{MIMETYPE_GA_FOLDER}' and title = '{escapeDriveFileName(sys.argv[i+1])}'"
        i += 2
    elif myarg == 'writerscantshare':
        body['writersCanShare'] = False
        i += 1
    elif myarg == 'writerscanshare':
        body['writersCanShare'] = True
        i += 1
    elif myarg == 'contentrestrictions':
        body['contentRestrictions'] = [{}]
        restriction = sys.argv[i+1].lower().replace('_', '')
        if restriction == 'readonly':
            body['contentRestrictions'][0]['readOnly'] = getBoolean(
                sys.argv[i+2], f'gam <users> {operation} drivefile')
            i += 3
            if len(sys.argv) > i and sys.argv[i].lower() == 'reason':
                if body['contentRestrictions'][0]['readOnly']:
                    body['contentRestrictions'][0]['reason'] = sys.argv[i+1]
                else:
                    controlflow.invalid_argument_exit(
                        'reason', 'contentrestrictions readonly false')
                i += 2
        else:
            controlflow.invalid_argument_exit(
                restriction, f'gam <users> {operation} drivefile')
    elif myarg == 'shortcut':
        body['mimeType'] = MIMETYPE_GA_SHORTCUT
        body['shortcutDetails'] = {'targetId': sys.argv[i+1]}
        i += 2
    elif myarg == 'securityupdate':
        body['linkShareMetadata'] = {'securityUpdateEnabled': getBoolean(
            sys.argv[i+1], f'gam <users> {operation} drivefile'), 'securityUpdateEligible': True}
        i += 2
    else:
        controlflow.invalid_argument_exit(
            myarg, f"gam <users> {operation} drivefile")
    return i


def get_media_body(parameters, body):
    if parameters[DFA_LOCALFILEPATH] != '-':
        media_body = googleapiclient.http.MediaFileUpload(parameters[DFA_LOCALFILEPATH], mimetype=parameters[DFA_LOCALMIMETYPE], resumable=True)
    else:
        if body['mimeType'] == MIMETYPE_GA_SPREADSHEET:
            mimetype = 'text/csv'
        elif body['mimeType'] == MIMETYPE_GA_DOCUMENT:
            mimetype = 'text/plain'
        else:
            mimetype = 'application/octet-stream'
        media_body = googleapiclient.http.MediaIoBaseUpload(io.BytesIO(sys.stdin.buffer.read()), mimetype, resumable=True)
    if media_body.size() == 0:
        media_body = None
    return media_body


def has_multiple_parents(body):
    return len(body.get('parents', [])) > 1


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
            body['title'] = sys.argv[i + 1]
            i += 2
        elif myarg == 'id':
            fileIdSelection['fileIds'] = [
                sys.argv[i + 1],
            ]
            i += 2
        elif myarg == 'query':
            fileIdSelection['query'] = sys.argv[i + 1]
            i += 2
        elif myarg == 'drivefilename':
            fileIdSelection[
                'query'] = f"'me' in owners and title = '{sys.argv[i+1]}'"
            i += 2
        else:
            i = getDriveFileAttribute(i, body, parameters, myarg, True)
    if not fileIdSelection['query'] and not fileIdSelection['fileIds']:
        controlflow.system_error_exit(
            2,
            'you need to specify either id, query or drivefilename in order to determine the file(s) to update'
        )
    if fileIdSelection['query'] and fileIdSelection['fileIds']:
        controlflow.system_error_exit(
            2,
            'you cannot specify multiple file identifiers. Choose one of id, drivefilename, query.'
        )
    if operation == 'update' and parameters[DFA_LOCALFILEPATH]:
        media_body = get_media_body(parameters, body)
    for user in users:
        user, drive = buildDriveGAPIObject(user)
        if not drive:
            continue
        if parameters[DFA_PARENTQUERY]:
            more_parents = doDriveSearch(drive,
                                         query=parameters[DFA_PARENTQUERY])
            body.setdefault('parents', [])
            for a_parent in more_parents:
                body['parents'].append({'id': a_parent})
        if has_multiple_parents(body):
            sys.stderr.write(f"Multiple parents ({len(body['parents'])}) specified for {user}, only one is allowed.\n")
            continue
        if fileIdSelection['query']:
            fileIdSelection['fileIds'] = doDriveSearch(
                drive, query=fileIdSelection['query'])
        if not fileIdSelection['fileIds']:
            print(f'No files to {operation} for {user}')
            continue
        if operation == 'update':
            for fileId in fileIdSelection['fileIds']:
                if media_body:
                    result = gapi.call(drive.files(),
                                       'update',
                                       fileId=fileId,
                                       convert=parameters[DFA_CONVERT],
                                       ocr=parameters[DFA_OCR],
                                       ocrLanguage=parameters[DFA_OCRLANGUAGE],
                                       media_body=media_body,
                                       body=body,
                                       fields='id',
                                       supportsAllDrives=True)
                    print(
                        f'Successfully updated {result["id"]} drive file with content from {parameters[DFA_LOCALFILENAME]}'
                    )
                else:
                    result = gapi.call(drive.files(),
                                       'patch',
                                       fileId=fileId,
                                       convert=parameters[DFA_CONVERT],
                                       ocr=parameters[DFA_OCR],
                                       ocrLanguage=parameters[DFA_OCRLANGUAGE],
                                       body=body,
                                       fields='id',
                                       supportsAllDrives=True)
                    print(
                        f'Successfully updated drive file/folder ID {result["id"]}'
                    )
        else:
            for fileId in fileIdSelection['fileIds']:
                result = gapi.call(drive.files(),
                                   'copy',
                                   fileId=fileId,
                                   convert=parameters[DFA_CONVERT],
                                   ocr=parameters[DFA_OCR],
                                   ocrLanguage=parameters[DFA_OCRLANGUAGE],
                                   body=body,
                                   fields='id',
                                   supportsAllDrives=True)
                print(f'Successfully copied {fileId} to {result["id"]}')


def createDriveFile(users):
    csv_output = return_id_only = to_drive = False
    csv_rows = []
    csv_titles = ['User', 'title', 'id']
    media_body = None
    body, parameters = initializeDriveFileAttributes()
    i = 5
    while i < len(sys.argv):
        myarg = sys.argv[i].lower().replace('_', '')
        if myarg == 'drivefilename':
            body['title'] = sys.argv[i + 1]
            i += 2
        elif myarg == 'csv':
            csv_output = True
            i += 1
        elif myarg == 'todrive':
            to_drive = True
            i += 1
        elif myarg == 'returnidonly':
            return_id_only = True
            i += 1
        else:
            i = getDriveFileAttribute(i, body, parameters, myarg, False)
    if parameters[DFA_LOCALFILEPATH]:
        media_body = get_media_body(parameters, body)
    for user in users:
        user, drive = buildDriveGAPIObject(user)
        if not drive:
            continue
        if parameters[DFA_PARENTQUERY]:
            more_parents = doDriveSearch(drive,
                                         query=parameters[DFA_PARENTQUERY])
            body.setdefault('parents', [])
            for a_parent in more_parents:
                body['parents'].append({'id': a_parent})
        if has_multiple_parents(body):
            sys.stderr.write(f"Multiple parents ({len(body['parents'])}) specified for {user}, only one is allowed.\n")
            continue
        result = gapi.call(drive.files(),
                           'insert',
                           convert=parameters[DFA_CONVERT],
                           ocr=parameters[DFA_OCR],
                           ocrLanguage=parameters[DFA_OCRLANGUAGE],
                           media_body=media_body,
                           body=body,
                           fields='id,title,mimeType',
                           supportsAllDrives=True)
        if return_id_only:
            sys.stdout.write(f"{result['id']}\n")
        elif csv_output:
            csv_rows.append({
                'User': user,
                'title': result['title'],
                'id': result['id']
            })
        else:
            titleInfo = f'{result["title"]}({result["id"]})'
            if parameters[DFA_LOCALFILENAME]:
                print(
                    f'Successfully uploaded {parameters[DFA_LOCALFILENAME]} to Drive File {titleInfo}'
                )
            else:
                created_type = ['Folder', 'File'
                               ][result['mimeType'] != MIMETYPE_GA_FOLDER]
                print(f'Successfully created Drive {created_type} {titleInfo}')
    if csv_output:
        display.write_csv_file(csv_rows, csv_titles, 'Files', to_drive)


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
    while i < len(sys.argv):
        myarg = sys.argv[i].lower().replace('_', '')
        if myarg == 'id':
            fileIdSelection['fileIds'] = [
                sys.argv[i + 1],
            ]
            i += 2
        elif myarg == 'query':
            fileIdSelection['query'] = sys.argv[i + 1]
            i += 2
        elif myarg == 'drivefilename':
            fileIdSelection[
                'query'] = f"'me' in owners and title = '{sys.argv[i+1]}'"
            i += 2
        elif myarg == 'revision':
            revisionId = getInteger(sys.argv[i + 1], myarg, minVal=1)
            i += 2
        elif myarg == 'csvsheet':
            csvSheetTitle = sys.argv[i + 1]
            csvSheetTitleLower = csvSheetTitle.lower()
            i += 2
        elif myarg == 'format':
            exportFormatChoices = sys.argv[i + 1].replace(',',
                                                          ' ').lower().split()
            exportFormats = []
            for exportFormat in exportFormatChoices:
                if exportFormat in DOCUMENT_FORMATS_MAP:
                    exportFormats.extend(DOCUMENT_FORMATS_MAP[exportFormat])
                else:
                    controlflow.expected_argument_exit(
                        'format', ', '.join(DOCUMENT_FORMATS_MAP), exportFormat)
            i += 2
        elif myarg == 'targetfolder':
            targetFolder = os.path.expanduser(sys.argv[i + 1])
            if not os.path.isdir(targetFolder):
                os.makedirs(targetFolder)
            i += 2
        elif myarg == 'targetname':
            targetName = sys.argv[i + 1]
            targetStdout = targetName == '-'
            i += 2
        elif myarg == 'overwrite':
            overwrite = True
            i += 1
        elif myarg == 'showprogress':
            showProgress = True
            i += 1
        else:
            controlflow.invalid_argument_exit(sys.argv[i],
                                              'gam <users> get drivefile')
    if not fileIdSelection['query'] and not fileIdSelection['fileIds']:
        controlflow.system_error_exit(
            2,
            'you need to specify either id, query or drivefilename in order to determine the file(s) to download'
        )
    if fileIdSelection['query'] and fileIdSelection['fileIds']:
        controlflow.system_error_exit(
            2,
            'you cannot specify multiple file identifiers. Choose one of id, drivefilename, query.'
        )
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
            fileIdSelection['fileIds'] = doDriveSearch(
                drive, query=fileIdSelection['query'], quiet=targetStdout)
        else:
            fileId = fileIdSelection['fileIds'][0]
            if fileId[:8].lower() == 'https://' or fileId[:7].lower(
            ) == 'http://':
                fileIdSelection['fileIds'][0] = getFileIdFromAlternateLink(
                    fileId)
        if not fileIdSelection['fileIds']:
            print(f'No files to download for {user}')
        i = 0
        for fileId in fileIdSelection['fileIds']:
            fileExtension = None
            result = gapi.call(drive.files(),
                               'get',
                               fileId=fileId,
                               fields='fileExtension,fileSize,mimeType,title',
                               supportsAllDrives=True)
            fileExtension = result.get('fileExtension')
            mimeType = result['mimeType']
            if mimeType == MIMETYPE_GA_FOLDER:
                print(f'Skipping download of folder {result["title"]}')
                continue
            if mimeType in NON_DOWNLOADABLE_MIMETYPES:
                print(f'Format of file {result["title"]} not downloadable')
                continue
            validExtensions = GOOGLEDOC_VALID_EXTENSIONS_MAP.get(mimeType)
            if validExtensions:
                my_line = 'Downloading Google Doc: %s'
                if csvSheetTitle:
                    my_line += f', Sheet: {csvSheetTitle}'
                googleDoc = True
            else:
                if 'fileSize' in result:
                    my_line = 'Downloading: %%s of %s bytes' % utils.formatFileSize(
                        int(result['fileSize']))
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
                        safe_file_title = sanitize_filename(result['title'])
                        if not safe_file_title:
                            safe_file_title = fileId
                    filename = os.path.join(targetFolder, safe_file_title)
                    y = 0
                    while True:
                        if filename.lower(
                        )[-len(extension):] != extension.lower():
                            filename += extension
                        if overwrite or not os.path.isfile(filename):
                            break
                        y += 1
                        filename = os.path.join(targetFolder,
                                                f'({y})-{safe_file_title}')
                    print(my_line % (result['title'], filename))
                spreadsheetUrl = None
                if googleDoc:
                    if csvSheetTitle is None or mimeType != MIMETYPE_GA_SPREADSHEET:
                        request = drive.files().export_media(
                            fileId=fileId, mimeType=exportFormat['mime'])
                        if revisionId:
                            request.uri = f'{request.uri}&revision={revisionId}'
                    else:
                        spreadsheet = gapi.call(
                            sheet.spreadsheets(),
                            'get',
                            spreadsheetId=fileId,
                            fields=
                            'spreadsheetUrl,sheets(properties(sheetId,title))')
                        for sheet in spreadsheet['sheets']:
                            if sheet['properties']['title'].lower(
                            ) == csvSheetTitleLower:
                                spreadsheetUrl = '{0}?format=csv&id={1}&gid={2}'.format(
                                    re.sub('/edit.*$', '/export',
                                           spreadsheet['spreadsheetUrl']),
                                    fileId, sheet['properties']['sheetId'])
                                break
                        else:
                            display.print_error(
                                f'Google Doc: {result["title"]}, Sheet: {csvSheetTitle}, does not exist'
                            )
                            csvSheetNotFound = True
                            continue
                else:
                    request = drive.files().get_media(fileId=fileId,
                                                      revisionId=revisionId)
                fh = None
                try:
                    fh = open(filename,
                              'wb') if not targetStdout else sys.stdout
                    if not spreadsheetUrl:
                        downloader = googleapiclient.http.MediaIoBaseDownload(
                            fh, request)
                        done = False
                        while not done:
                            status, done = downloader.next_chunk()
                            if showProgress:
                                print('Downloaded: {0:>7.2%}'.format(
                                    status.progress()))
                    else:
                        _, content = drive._http.request(uri=spreadsheetUrl,
                                                         method='GET')
                        fh.write(content)
                        if targetStdout and content[-1] != '\n':
                            fh.write('\n')
                    if not targetStdout:
                        fileutils.close_file(fh)
                    fileDownloaded = True
                    break
                except (IOError, httplib2.HttpLib2Error) as e:
                    display.print_error(str(e))
                    GM_Globals[GM_SYSEXITRC] = 6
                    fileDownloadFailed = True
                    break
                except googleapiclient.http.HttpError as e:
                    mg = HTTP_ERROR_PATTERN.match(str(e))
                    if mg:
                        display.print_error(mg.group(1))
                    else:
                        display.print_error(str(e))
                    fileDownloadFailed = True
                    break
                if fh and not targetStdout:
                    fileutils.close_file(fh)
                    os.remove(filename)
            if not fileDownloaded and not fileDownloadFailed and not csvSheetNotFound:
                display.print_error(
                    f'Format ({",".join(exportFormatChoices)}) not available')
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
            controlflow.invalid_argument_exit(myarg,
                                              'gam <users> show fileinfo')
    if fieldsList or labelsList:
        fieldsList.append('title')
        fields = ','.join(set(fieldsList))
        if labelsList:
            fields += f',labels({",".join(set(labelsList))})'
    else:
        fields = '*'
    for user in users:
        user, drive = buildDriveGAPIObject(user)
        if not drive:
            continue
        feed = gapi.call(drive.files(),
                         'get',
                         fileId=fileId,
                         fields=fields,
                         supportsAllDrives=True)
        if feed:
            display.print_json(feed)


def showDriveFileRevisions(users):
    fileId = sys.argv[5]
    for user in users:
        user, drive = buildDriveGAPIObject(user)
        if not drive:
            continue
        feed = gapi.call(drive.revisions(), 'list', fileId=fileId)
        if feed:
            display.print_json(feed)


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
            controlflow.invalid_argument_exit(sys.argv[i],
                                              'gam <users> transfer drive')
    target_user, target_drive = buildDriveGAPIObject(target_user)
    if not target_drive:
        return
    target_about = gapi.call(target_drive.about(),
                             'get',
                             fields='quotaType,quotaBytesTotal,quotaBytesUsed')
    if target_about['quotaType'] != 'UNLIMITED':
        target_drive_free = int(target_about['quotaBytesTotal']) - int(
            target_about['quotaBytesUsed'])
    else:
        target_drive_free = None
    for user in users:
        user, source_drive = buildDriveGAPIObject(user)
        if not source_drive:
            continue
        counter = 0
        source_about = gapi.call(
            source_drive.about(),
            'get',
            fields='quotaBytesTotal,quotaBytesUsed,rootFolderId,permissionId')
        source_drive_size = int(source_about['quotaBytesUsed'])
        if target_drive_free is not None:
            if target_drive_free < source_drive_size:
                controlflow.system_error_exit(
                    4,
                    MESSAGE_NO_TRANSFER_LACK_OF_DISK_SPACE.format(
                        source_drive_size / 1024 / 1024,
                        target_drive_free / 1024 / 1024))
            print(
                f'Source drive size: {source_drive_size / 1024 / 1024}mb  Target drive free: {target_drive_free / 1024 / 1024}mb'
            )
            target_drive_free = target_drive_free - source_drive_size  # prep target_drive_free for next user
        else:
            print(
                f'Source drive size: {source_drive_size / 1024 / 1024}mb  Target drive free: UNLIMITED'
            )
        source_root = source_about['rootFolderId']
        source_permissionid = source_about['permissionId']
        print(f'Getting file list for source user: {user}...')
        page_message = gapi.got_total_items_msg('Files', '\n')
        source_drive_files = gapi.get_all_pages(
            source_drive.files(),
            'list',
            'items',
            page_message=page_message,
            q="'me' in owners and trashed = false",
            fields='items(id,parents,mimeType),nextPageToken')
        all_source_file_ids = []
        for source_drive_file in source_drive_files:
            all_source_file_ids.append(source_drive_file['id'])
        total_count = len(source_drive_files)
        print(f'Getting folder list for target user: {target_user}...')
        page_message = gapi.got_total_items_msg('Folders', '\n')
        target_folders = gapi.get_all_pages(
            target_drive.files(),
            'list',
            'items',
            page_message=page_message,
            q=
            "'me' in owners and mimeType = 'application/vnd.google-apps.folder'",
            fields='items(id,title),nextPageToken')
        got_top_folder = False
        all_target_folder_ids = []
        for target_folder in target_folders:
            all_target_folder_ids.append(target_folder['id'])
            if (not got_top_folder
               ) and target_folder['title'] == f'{user} old files':
                target_top_folder = target_folder['id']
                got_top_folder = True
        if not got_top_folder:
            create_folder = gapi.call(
                target_drive.files(),
                'insert',
                body={
                    'title': f'{user} old files',
                    'mimeType': 'application/vnd.google-apps.folder'
                },
                fields='id')
            target_top_folder = create_folder['id']
        transferred_files = []
        while True:  # we loop thru, skipping files until all of their parents are done
            skipped_files = False
            for drive_file in source_drive_files:
                file_id = drive_file['id']
                if file_id in transferred_files:
                    continue
                source_parents = drive_file['parents']
                skip_file_for_now = False
                for source_parent in source_parents:
                    if source_parent[
                            'id'] not in all_source_file_ids and source_parent[
                                'id'] not in all_target_folder_ids:
                        continue  # means this parent isn't owned by source or target, shouldn't matter
                    if source_parent[
                            'id'] not in transferred_files and source_parent[
                                'id'] != source_root:
                        #print(f'skipping {file_id}')
                        skipped_files = skip_file_for_now = True
                        break
                if skip_file_for_now:
                    continue
                transferred_files.append(drive_file['id'])
                counter += 1
                print(
                    f'Changing owner for file {drive_file["id"]}{currentCount(counter, total_count)}'
                )
                body = {'role': 'owner', 'type': 'user', 'value': target_user}
                gapi.call(source_drive.permissions(),
                          'insert',
                          soft_errors=True,
                          fileId=file_id,
                          sendNotificationEmails=False,
                          body=body)
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
                gapi.call(target_drive.files(),
                          'patch',
                          soft_errors=True,
                          retry_reasons=[gapi_errors.ErrorReason.NOT_FOUND],
                          fileId=file_id,
                          body={'parents': target_parents})
                if remove_source_user:
                    gapi.call(target_drive.permissions(),
                              'delete',
                              soft_errors=True,
                              fileId=file_id,
                              permissionId=source_permissionid)
            if not skipped_files:
                break


def sendOrDropEmail(users, method='send'):
    body = subject = ''
    recipient = labels = sender = None
    kwargs = {}
    if method in ['insert', 'import']:
        kwargs['internalDateSource'] = 'receivedTime'
        if method == 'import':
            kwargs['neverMarkSpam'] = True
    msgHeaders = {}
    i = 4
    while i < len(sys.argv):
        myarg = sys.argv[i].lower().replace('_', '')
        if myarg == 'message':
            body = sys.argv[i + 1]
            i += 2
        elif myarg == 'file':
            filename = sys.argv[i + 1]
            i, encoding = getCharSet(i + 2)
            body = fileutils.read_file(filename, encoding=encoding)
        elif myarg == 'subject':
            subject = sys.argv[i + 1]
            i += 2
        elif myarg in ['recipient', 'to']:
            recipient = sys.argv[i + 1]
            i += 2
        elif myarg == 'from':
            sender = sys.argv[i + 1]
            i += 2
        elif myarg == 'header':
            msgHeaders[sys.argv[i + 1]] = sys.argv[i + 2]
            i += 3
        elif method in ['insert', 'import'] and myarg == 'labels':
            labels = shlexSplitList(sys.argv[i + 1])
            i += 2
        elif method in ['insert', 'import'] and myarg == 'deleted':
            kwargs['deleted'] = True
            i += 1
        elif myarg == 'date':
            msgHeaders['Date'] = utils.get_time_or_delta_from_now(sys.argv[i +
                                                                           1])
            if method in ['insert', 'import']:
                kwargs['internalDateSource'] = 'dateHeader'
            i += 2
        elif method == 'import' and myarg == 'checkspam':
            kwargs['neverMarkSpam'] = False
            i += 1
        elif method == 'import' and myarg == 'processforcalendar':
            kwargs['processForCalendar'] = True
        else:
            controlflow.invalid_argument_exit(sys.argv[i],
                                              f'gam <users> {method}email')
    for user in users:
        send_email(subject, body, recipient, sender, user, method, labels,
                   msgHeaders, kwargs)


def doImap(users):
    enable = getBoolean(sys.argv[4], 'gam <users> imap')
    body = {
        'enabled': enable,
        'autoExpunge': True,
        'expungeBehavior': 'archive',
        'maxFolderSize': 0
    }
    i = 5
    while i < len(sys.argv):
        myarg = sys.argv[i].lower()
        if myarg == 'noautoexpunge':
            body['autoExpunge'] = False
            i += 1
        elif myarg == 'expungebehavior':
            opt = sys.argv[i + 1].lower()
            if opt in EMAILSETTINGS_IMAP_EXPUNGE_BEHAVIOR_CHOICES_MAP:
                body[
                    'expungeBehavior'] = EMAILSETTINGS_IMAP_EXPUNGE_BEHAVIOR_CHOICES_MAP[
                        opt]
                i += 2
            else:
                controlflow.expected_argument_exit(
                    'gam <users> imap expungebehavior',
                    ', '.join(EMAILSETTINGS_IMAP_EXPUNGE_BEHAVIOR_CHOICES_MAP),
                    opt)
        elif myarg == 'maxfoldersize':
            opt = sys.argv[i + 1].lower()
            if opt in EMAILSETTINGS_IMAP_MAX_FOLDER_SIZE_CHOICES:
                body['maxFolderSize'] = int(opt)
                i += 2
            else:
                controlflow.expected_argument_exit(
                    'gam <users> imap maxfoldersize',
                    '| '.join(EMAILSETTINGS_IMAP_MAX_FOLDER_SIZE_CHOICES), opt)
        else:
            controlflow.invalid_argument_exit(myarg, 'gam <users> imap')
    i = 0
    count = len(users)
    for user in users:
        i += 1
        user, gmail = buildGmailGAPIObject(user)
        if not gmail:
            continue
        print(
            f'Setting IMAP Access to {str(enable)} for {user}{currentCount(i, count)}'
        )
        gapi.call(gmail.users().settings(),
                  'updateImap',
                  soft_errors=True,
                  userId='me',
                  body=body)


def doLanguage(users):
    i = 0
    count = len(users)
    displayLanguage = sys.argv[4]
    for user in users:
        i += 1
        user, gmail = buildGmailGAPIObject(user)
        if not gmail:
            continue
        print(
            f'Setting languaged to {displayLanguage} for {user}{currentCount(i, count)}'
        )
        result = gapi.call(gmail.users().settings(),
                           'updateLanguage',
                           userId='me',
                           body={'displayLanguage': displayLanguage})
        print(f'Language is set to {result["displayLanguage"]} for {user}')


def getLanguage(users):
    i = 0
    count = len(users)
    for user in users:
        i += 1
        user, gmail = buildGmailGAPIObject(user)
        if not gmail:
            continue
        result = gapi.call(gmail.users().settings(),
                           'getLanguage',
                           soft_errors=True,
                           userId='me')
        if result:
            print(
                f'User: {user}, Language: {result["displayLanguage"]}{currentCount(i, count)}'
            )


def getImap(users):
    i = 0
    count = len(users)
    for user in users:
        i += 1
        user, gmail = buildGmailGAPIObject(user)
        if not gmail:
            continue
        result = gapi.call(gmail.users().settings(),
                           'getImap',
                           soft_errors=True,
                           userId='me')
        if result:
            enabled = result['enabled']
            if enabled:
                print(
                    f'User: {user}, IMAP Enabled: {enabled}, autoExpunge: {result["autoExpunge"]}, expungeBehavior: {result["expungeBehavior"]}, maxFolderSize: {result["maxFolderSize"]}{currentCount(i, count)}'
                )
            else:
                print(
                    f'User: {user}, IMAP Enabled: {enabled}{currentCount(i, count)}'
                )


def doPop(users):
    enable = getBoolean(sys.argv[4], 'gam <users> pop')
    body = {
        'accessWindow': ['disabled', 'allMail'][enable],
        'disposition': 'leaveInInbox'
    }
    i = 5
    while i < len(sys.argv):
        myarg = sys.argv[i].lower()
        if myarg == 'for':
            opt = sys.argv[i + 1].lower()
            if opt in EMAILSETTINGS_POP_ENABLE_FOR_CHOICES_MAP:
                body['accessWindow'] = EMAILSETTINGS_POP_ENABLE_FOR_CHOICES_MAP[
                    opt]
                i += 2
            else:
                controlflow.expected_argument_exit(
                    'gam <users> pop for',
                    ', '.join(EMAILSETTINGS_POP_ENABLE_FOR_CHOICES_MAP), opt)
        elif myarg == 'action':
            opt = sys.argv[i + 1].lower()
            if opt in EMAILSETTINGS_FORWARD_POP_ACTION_CHOICES_MAP:
                body[
                    'disposition'] = EMAILSETTINGS_FORWARD_POP_ACTION_CHOICES_MAP[
                        opt]
                i += 2
            else:
                controlflow.expected_argument_exit(
                    'gam <users> pop action',
                    ', '.join(EMAILSETTINGS_FORWARD_POP_ACTION_CHOICES_MAP),
                    opt)
        elif myarg == 'confirm':
            i += 1
        else:
            controlflow.invalid_argument_exit(myarg, 'gam <users> pop')
    i = 0
    count = len(users)
    for user in users:
        i += 1
        user, gmail = buildGmailGAPIObject(user)
        if not gmail:
            continue
        print(
            f'Setting POP Access to {str(enable)} for {user}{currentCount(i, count)}'
        )
        gapi.call(gmail.users().settings(),
                  'updatePop',
                  soft_errors=True,
                  userId='me',
                  body=body)


def getPop(users):
    i = 0
    count = len(users)
    for user in users:
        i += 1
        user, gmail = buildGmailGAPIObject(user)
        if not gmail:
            continue
        result = gapi.call(gmail.users().settings(),
                           'getPop',
                           soft_errors=True,
                           userId='me')
        if result:
            enabled = result['accessWindow'] != 'disabled'
            if enabled:
                print(
                    f'User: {user}, POP Enabled: {enabled}, For: {result["accessWindow"]}, Action: {result["disposition"]}{currentCount(i, count)}'
                )
            else:
                print(
                    f'User: {user}, POP Enabled: {enabled}{currentCount(i, count)}'
                )


SMTPMSA_DISPLAY_FIELDS = ['host', 'port', 'securityMode']


def _showSendAs(result, j, jcount, formatSig):
    if result['displayName']:
        print(
            f'SendAs Address: {result["displayName"]} <{result["sendAsEmail"]}>{currentCount(j, jcount)}'
        )
    else:
        print(
            f'SendAs Address: <{result["sendAsEmail"]}>{currentCount(j, jcount)}'
        )
    if result.get('replyToAddress'):
        print(f'  ReplyTo: {result["replyToAddress"]}')
    print(f'  IsPrimary: {result.get("isPrimary", False)}')
    print(f'  Default: {result.get("isDefault", False)}')
    if not result.get('isPrimary', False):
        print(f'  TreatAsAlias: {result.get("treatAsAlias", False)}')
    if 'smtpMsa' in result:
        for field in SMTPMSA_DISPLAY_FIELDS:
            if field in result['smtpMsa']:
                print(f'  smtpMsa.{field}: {result["smtpMsa"][field]}')
    if 'verificationStatus' in result:
        print(f'  Verification Status: {result["verificationStatus"]}')
    sys.stdout.write('  Signature:\n    ')
    signature = result.get('signature')
    if not signature:
        signature = 'None'
    if formatSig:
        print(utils.indentMultiLineText(utils.dehtml(signature), n=4))
    else:
        print(utils.indentMultiLineText(signature, n=4))


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
        message = re.sub(match.group(0),
                         tagReplacements.get(match.group(1), ''), message)
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
        matchTag = utils.get_string(i + 1, 'Tag')
        matchReplacement = utils.get_string(i + 2, 'String', minLen=0)
        tagReplacements[matchTag] = matchReplacement
        i += 3
    elif myarg == 'name':
        body['displayName'] = sys.argv[i + 1]
        i += 2
    elif myarg == 'replyto':
        body['replyToAddress'] = sys.argv[i + 1]
        i += 2
    elif myarg == 'default':
        body['isDefault'] = True
        i += 1
    elif myarg == 'treatasalias':
        body['treatAsAlias'] = getBoolean(sys.argv[i + 1], myarg)
        i += 2
    else:
        controlflow.invalid_argument_exit(myarg, f'gam <users> {command}')
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
            signature = sys.argv[i + 1]
            i += 2
            if signature.lower() == 'file':
                filename = sys.argv[i]
                i, encoding = getCharSet(i + 1)
                signature = fileutils.read_file(filename, encoding=encoding)
        elif myarg == 'html':
            html = True
            i += 1
        elif addCmd and myarg.startswith('smtpmsa.'):
            if myarg == 'smtpmsa.host':
                smtpMsa['host'] = sys.argv[i + 1]
                i += 2
            elif myarg == 'smtpmsa.port':
                value = sys.argv[i + 1].lower()
                if value not in SMTPMSA_PORTS:
                    controlflow.expected_argument_exit(myarg,
                                                       ', '.join(SMTPMSA_PORTS),
                                                       value)
                smtpMsa['port'] = int(value)
                i += 2
            elif myarg == 'smtpmsa.username':
                smtpMsa['username'] = sys.argv[i + 1]
                i += 2
            elif myarg == 'smtpmsa.password':
                smtpMsa['password'] = sys.argv[i + 1]
                i += 2
            elif myarg == 'smtpmsa.securitymode':
                value = sys.argv[i + 1].lower()
                if value not in SMTPMSA_SECURITY_MODES:
                    controlflow.expected_argument_exit(
                        myarg, ', '.join(SMTPMSA_SECURITY_MODES), value)
                smtpMsa['securityMode'] = value
                i += 2
            else:
                controlflow.invalid_argument_exit(sys.argv[i],
                                                  f'gam <users> {command}')
        else:
            i = getSendAsAttributes(i, myarg, body, tagReplacements, command)
    if signature is not None:
        body['signature'] = _processSignature(tagReplacements, signature, html)
    if smtpMsa:
        for field in SMTPMSA_REQUIRED_FIELDS:
            if field not in smtpMsa:
                controlflow.system_error_exit(2,
                                              f'smtpmsa.{field} is required.')
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
        print(
            f'Allowing {user} to send as {emailAddress}{currentCount(i, count)}'
        )
        gapi.call(gmail.users().settings().sendAs(), ['patch',
                                                      'create'][addCmd],
                  soft_errors=True,
                  userId='me',
                  **kwargs)


def deleteSendAs(users):
    emailAddress = normalizeEmailAddressOrUID(sys.argv[5], noUid=True)
    i = 0
    count = len(users)
    for user in users:
        i += 1
        user, gmail = buildGmailGAPIObject(user)
        if not gmail:
            continue
        print(
            f'Disallowing {user} to send as {emailAddress}{currentCount(i, count)}'
        )
        gapi.call(gmail.users().settings().sendAs(),
                  'delete',
                  soft_errors=True,
                  userId='me',
                  sendAsEmail=emailAddress)


def updateSmime(users):
    smimeIdBase = None
    sendAsEmailBase = None
    make_default = False
    i = 5
    while i < len(sys.argv):
        myarg = sys.argv[i].lower()
        if myarg == 'id':
            smimeIdBase = sys.argv[i + 1]
            i += 2
        elif myarg in ['sendas', 'sendasemail']:
            sendAsEmailBase = sys.argv[i + 1]
            i += 2
        elif myarg in ['default']:
            make_default = True
            i += 1
        else:
            controlflow.invalid_argument_exit(myarg, 'gam <users> update smime')
    if not make_default:
        print('Nothing to update for smime.')
        sys.exit(0)
    for user in users:
        user, gmail = buildGmailGAPIObject(user)
        if not gmail:
            continue
        sendAsEmail = sendAsEmailBase if sendAsEmailBase else user
        if not smimeIdBase:
            result = gapi.call(gmail.users().settings().sendAs().smimeInfo(),
                               'list',
                               userId='me',
                               sendAsEmail=sendAsEmail,
                               fields='smimeInfo(id)')
            smimes = result.get('smimeInfo', [])
            if not smimes:
                controlflow.system_error_exit(
                    3,
                    f'{user} has no S/MIME certificates for sendas address {sendAsEmail}'
                )
            if len(smimes) > 1:
                certList = '\n '.join([smime['id'] for smime in smimes])
                controlflow.system_error_exit(
                    3,
                    f'{user} has more than one S/MIME certificate. Please specify a cert to update:\n {certList}'
                )
            smimeId = smimes[0]['id']
        else:
            smimeId = smimeIdBase
        print(
            f'Setting smime id {smimeId} as default for user {user} and sendas {sendAsEmail}'
        )
        gapi.call(gmail.users().settings().sendAs().smimeInfo(),
                  'setDefault',
                  userId='me',
                  sendAsEmail=sendAsEmail,
                  id=smimeId)


def deleteSmime(users):
    smimeIdBase = None
    sendAsEmailBase = None
    i = 5
    while i < len(sys.argv):
        myarg = sys.argv[i].lower()
        if myarg == 'id':
            smimeIdBase = sys.argv[i + 1]
            i += 2
        elif myarg in ['sendas', 'sendasemail']:
            sendAsEmailBase = sys.argv[i + 1]
            i += 2
        else:
            controlflow.invalid_argument_exit(myarg, 'gam <users> delete smime')
    for user in users:
        user, gmail = buildGmailGAPIObject(user)
        if not gmail:
            continue
        sendAsEmail = sendAsEmailBase if sendAsEmailBase else user
        if not smimeIdBase:
            result = gapi.call(gmail.users().settings().sendAs().smimeInfo(),
                               'list',
                               userId='me',
                               sendAsEmail=sendAsEmail,
                               fields='smimeInfo(id)')
            smimes = result.get('smimeInfo', [])
            if not smimes:
                controlflow.system_error_exit(
                    3,
                    f'{user} has no S/MIME certificates for sendas address {sendAsEmail}'
                )
            if len(smimes) > 1:
                certList = '\n '.join([smime['id'] for smime in smimes])
                controlflow.system_error_exit(
                    3,
                    f'{user} has more than one S/MIME certificate. Please specify a cert to delete:\n {certList}'
                )
            smimeId = smimes[0]['id']
        else:
            smimeId = smimeIdBase
        print(
            f'Deleting smime id {smimeId} for user {user} and sendas {sendAsEmail}'
        )
        gapi.call(gmail.users().settings().sendAs().smimeInfo(),
                  'delete',
                  userId='me',
                  sendAsEmail=sendAsEmail,
                  id=smimeId)


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
            controlflow.invalid_argument_exit(
                myarg, f"gam <users> {['show', 'print'][csvFormat]} smime")
    i = 0
    for user in users:
        i += 1
        user, gmail = buildGmailGAPIObject(user)
        if not gmail:
            continue
        if primaryonly:
            sendAsEmails = [user]
        else:
            result = gapi.call(gmail.users().settings().sendAs(),
                               'list',
                               userId='me',
                               fields='sendAs(sendAsEmail)')
            sendAsEmails = []
            for sendAs in result['sendAs']:
                sendAsEmails.append(sendAs['sendAsEmail'])
        for sendAsEmail in sendAsEmails:
            result = gapi.call(gmail.users().settings().sendAs().smimeInfo(),
                               'list',
                               sendAsEmail=sendAsEmail,
                               userId='me')
            smimes = result.get('smimeInfo', [])
            for j, _ in enumerate(smimes):
                smimes[j]['expiration'] = utils.formatTimestampYMDHMS(
                    smimes[j]['expiration'])
            if csvFormat:
                for smime in smimes:
                    display.add_row_titles_to_csv_file(
                        utils.flatten_json(smime, flattened={'User': user}),
                        csvRows, titles)
            else:
                display.print_json(smimes)
    if csvFormat:
        display.write_csv_file(csvRows, titles, 'S/MIME', todrive)


def printShowSendAs(users, csvFormat):
    if csvFormat:
        todrive = False
        titles = [
            'User', 'displayName', 'sendAsEmail', 'replyToAddress', 'isPrimary',
            'isDefault', 'treatAsAlias', 'verificationStatus'
        ]
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
            controlflow.invalid_argument_exit(
                myarg, f"gam <users> {['show', 'print'][csvFormat]} sendas")
    i = 0
    count = len(users)
    for user in users:
        i += 1
        user, gmail = buildGmailGAPIObject(user)
        if not gmail:
            continue
        result = gapi.call(gmail.users().settings().sendAs(),
                           'list',
                           soft_errors=True,
                           userId='me')
        jcount = len(result.get('sendAs', [])) if (result) else 0
        if not csvFormat:
            print(f'User: {user}, SendAs Addresses:{currentCount(i, count)}')
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
                                title = f'smtpMsa.{field}'
                                if title not in titles:
                                    titles.append(title)
                                row[title] = sendas[item][field]
                csvRows.append(row)
    if csvFormat:
        display.write_csv_file(csvRows, titles, 'SendAs', todrive)


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
            controlflow.invalid_argument_exit(sys.argv[i],
                                              'gam <users> info sendas')
    i = 0
    count = len(users)
    for user in users:
        i += 1
        user, gmail = buildGmailGAPIObject(user)
        if not gmail:
            continue
        print(f'User: {user}, Show SendAs Address:{currentCount(i, count)}')
        result = gapi.call(gmail.users().settings().sendAs(),
                           'get',
                           soft_errors=True,
                           userId='me',
                           sendAsEmail=emailAddress)
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
            smimefile = sys.argv[i + 1]
            smimeData = fileutils.read_file(smimefile, mode='rb')
            body['pkcs12'] = base64.urlsafe_b64encode(smimeData).decode(UTF8)
            i += 2
        elif myarg == 'password':
            body['encryptedKeyPassword'] = sys.argv[i + 1]
            i += 2
        elif myarg == 'default':
            setDefault = True
            i += 1
        elif myarg in ['sendas', 'sendasemail']:
            sendAsEmailBase = sys.argv[i + 1]
            i += 2
        else:
            controlflow.invalid_argument_exit(myarg, 'gam <users> add smime')
    if 'pkcs12' not in body:
        controlflow.system_error_exit(3, 'you must specify a file to upload')
    i = 0
    for user in users:
        i += 1
        user, gmail = buildGmailGAPIObject(user)
        if not gmail:
            continue
        sendAsEmail = sendAsEmailBase if sendAsEmailBase else user
        result = gapi.call(gmail.users().settings().sendAs().smimeInfo(),
                           'insert',
                           userId='me',
                           sendAsEmail=sendAsEmail,
                           body=body)
        if setDefault:
            gapi.call(gmail.users().settings().sendAs().smimeInfo(),
                      'setDefault',
                      userId='me',
                      sendAsEmail=sendAsEmail,
                      id=result['id'])
        print(
            f'Added S/MIME certificate for user {user} sendas {sendAsEmail} issued by {result["issuerCn"]}'
        )


def getLabelAttributes(i, myarg, body, function):
    if myarg == 'labellistvisibility':
        value = sys.argv[i + 1].lower().replace('_', '')
        if value == 'hide':
            body['labelListVisibility'] = 'labelHide'
        elif value == 'show':
            body['labelListVisibility'] = 'labelShow'
        elif value == 'showifunread':
            body['labelListVisibility'] = 'labelShowIfUnread'
        else:
            controlflow.expected_argument_exit(
                'label_list_visibility',
                ', '.join(['hide', 'show', 'show_if_unread']), value)
        i += 2
    elif myarg == 'messagelistvisibility':
        value = sys.argv[i + 1].lower().replace('_', '')
        if value not in ['hide', 'show']:
            controlflow.expected_argument_exit('message_list_visibility',
                                               ', '.join(['hide',
                                                          'show']), value)
        body['messageListVisibility'] = value
        i += 2
    elif myarg == 'backgroundcolor':
        body.setdefault('color', {})
        body['color']['backgroundColor'] = getLabelColor(sys.argv[i + 1])
        i += 2
    elif myarg == 'textcolor':
        body.setdefault('color', {})
        body['color']['textColor'] = getLabelColor(sys.argv[i + 1])
        i += 2
    else:
        controlflow.invalid_argument_exit(myarg,
                                          f'gam <users> {function} labels')
    return i


def checkLabelColor(body):
    if 'color' not in body:
        return
    if 'backgroundColor' in body['color']:
        if 'textColor' in body['color']:
            return
        controlflow.system_error_exit(2,
                                      'textcolor <LabelColorHex> is required.')
    controlflow.system_error_exit(
        2, 'backgroundcolor <LabelColorHex> is required.')


def doLabel(users, i):
    label = sys.argv[i]
    i += 1
    body = {'name': label}
    while i < len(sys.argv):
        myarg = sys.argv[i].lower().replace('_', '')
        i = getLabelAttributes(i, myarg, body, 'create')
    checkLabelColor(body)
    i = 0
    count = len(users)
    for user in users:
        i += 1
        user, gmail = buildGmailGAPIObject(user)
        if not gmail:
            continue
        print(f'Creating label {label} for {user}{currentCount(i, count)}')
        gapi.call(gmail.users().labels(),
                  'create',
                  soft_errors=True,
                  userId=user,
                  body=body)


PROCESS_MESSAGE_FUNCTION_TO_ACTION_MAP = {
    'delete': 'deleted',
    'trash': 'trashed',
    'untrash': 'untrashed',
    'modify': 'modified'
}


def labelsToLabelIds(gmail, labels):
    allLabels = {
        'INBOX': 'INBOX',
        'SPAM': 'SPAM',
        'TRASH': 'TRASH',
        'UNREAD': 'UNREAD',
        'STARRED': 'STARRED',
        'IMPORTANT': 'IMPORTANT',
        'SENT': 'SENT',
        'DRAFT': 'DRAFT',
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
            label_results = gapi.call(gmail.users().labels(),
                                      'list',
                                      userId='me',
                                      fields='labels(id,name,type)')
            for a_label in label_results['labels']:
                if a_label['type'] == 'system':
                    allLabels[a_label['id']] = a_label['id']
                else:
                    allLabels[a_label['name']] = a_label['id']
        if label not in allLabels:
            # if still not there, create it
            label_results = gapi.call(gmail.users().labels(),
                                      'create',
                                      body={
                                          'labelListVisibility': 'labelShow',
                                          'messageListVisibility': 'show',
                                          'name': label
                                      },
                                      userId='me',
                                      fields='id')
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
                    label_result = gapi.call(gmail.users().labels(),
                                             'create',
                                             userId='me',
                                             body={'name': parent_label})
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
            query = sys.argv[i + 1]
            i += 2
        elif myarg == 'doit':
            doIt = True
            i += 1
        elif myarg in [
                'maxtodelete', 'maxtotrash', 'maxtomodify', 'maxtountrash'
        ]:
            maxToProcess = getInteger(sys.argv[i + 1], myarg, minVal=0)
            i += 2
        elif (function == 'modify') and (myarg == 'addlabel'):
            body.setdefault('addLabelIds', [])
            body['addLabelIds'].append(sys.argv[i + 1])
            i += 2
        elif (function == 'modify') and (myarg == 'removelabel'):
            body.setdefault('removeLabelIds', [])
            body['removeLabelIds'].append(sys.argv[i + 1])
            i += 2
        else:
            controlflow.invalid_argument_exit(sys.argv[i],
                                              f'gam <users> {function} {unit}')
    if not query:
        controlflow.system_error_exit(
            2, 'No query specified. You must specify some query!')
    action = PROCESS_MESSAGE_FUNCTION_TO_ACTION_MAP[function]
    for user in users:
        user, gmail = buildGmailGAPIObject(user)
        if not gmail:
            continue
        print(f'Searching {unit.capitalize()} for {user}')
        unitmethod = getattr(gmail.users(), unit)
        page_message = gapi.got_total_items_msg(
            f'{unit.capitalize()} for user {user}', '')
        listResult = gapi.get_all_pages(unitmethod(),
                                        'list',
                                        unit,
                                        page_message=page_message,
                                        userId='me',
                                        q=query,
                                        includeSpamTrash=True,
                                        soft_errors=True,
                                        fields=f'nextPageToken,{unit}(id)')
        result_count = len(listResult)
        if not doIt or result_count == 0:
            print(
                f'would try to {function} {result_count} messages for user {user} (max {maxToProcess})\n'
            )
            continue
        if result_count > maxToProcess:
            print(
                f'WARNING: refusing to {function} ANY messages for user {user} since max messages to process is {maxToProcess} and messages to be {action} is {result_count}\n'
            )
            continue
        kwargs = {'body': {}}
        for my_key in body:
            kwargs['body'][my_key] = labelsToLabelIds(gmail, body[my_key])
        i = 0
        if unit == 'messages' and function in ['delete', 'modify']:
            batchFunction = f'batch{function.title()}'
            id_batches = [[]]
            for a_unit in listResult:
                id_batches[i].append(a_unit['id'])
                if len(id_batches[i]) == 1000:
                    i += 1
                    id_batches.append([])
            processed_messages = 0
            for id_batch in id_batches:
                kwargs['body']['ids'] = id_batch
                print(f'{function} {len(id_batch)} messages')
                gapi.call(unitmethod(), batchFunction, userId='me', **kwargs)
                processed_messages += len(id_batch)
                print(
                    f'{function} {processed_messages} of {result_count} messages'
                )
            continue
        if not kwargs['body']:
            del kwargs['body']
        for a_unit in listResult:
            i += 1
            print(
                f' {function} {unit} {a_unit["id"]} for user {user}{currentCount(i, result_count)}'
            )
            gapi.call(unitmethod(),
                      function,
                      id=a_unit['id'],
                      userId='me',
                      **kwargs)


def doDeleteLabel(users):
    label = sys.argv[5]
    label_name_lower = label.lower()
    for user in users:
        user, gmail = buildGmailGAPIObject(user)
        if not gmail:
            continue
        print(f'Getting all labels for {user}...')
        labels = gapi.call(gmail.users().labels(),
                           'list',
                           userId=user,
                           fields='labels(id,name,type)')
        del_labels = []
        if label == '--ALL_LABELS--':
            for del_label in sorted(labels['labels'],
                                    key=lambda k: k['name'],
                                    reverse=True):
                if del_label['type'] != 'system':
                    del_labels.append(del_label)
        elif label[:6].lower() == 'regex:':
            regex = label[6:]
            p = re.compile(regex)
            for del_label in sorted(labels['labels'],
                                    key=lambda k: k['name'],
                                    reverse=True):
                if del_label['type'] != 'system' and p.match(del_label['name']):
                    del_labels.append(del_label)
        else:
            for del_label in sorted(labels['labels'],
                                    key=lambda k: k['name'],
                                    reverse=True):
                if label_name_lower == del_label['name'].lower():
                    del_labels.append(del_label)
                    break
            else:
                print(f' Error: no such label for {user}')
                continue
        bcount = 0
        i = 0
        count = len(del_labels)
        dbatch = gmail.new_batch_http_request(callback=gmail_del_result)
        for del_me in del_labels:
            i += 1
            print(f' deleting label {del_me["name"]}{currentCount(i, count)}')
            dbatch.add(gmail.users().labels().delete(userId=user,
                                                     id=del_me['id']))
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


def printShowLabels(users, show=True):
    i = 5
    onlyUser = False
    showCounts = False
    todrive = False
    while i < len(sys.argv):
        myarg = sys.argv[i].lower().replace('_', '')
        if myarg == 'onlyuser':
            onlyUser = True
            i += 1
        elif myarg == 'todrive':
            todrive = True
            i += 1
        elif myarg == 'showcounts':
            showCounts = True
            i += 1
        else:
            controlflow.invalid_argument_exit(sys.argv[i],
                                          'gam <users> show labels')
    if not show:
        titles = ['email']
    for user in users:
        user, gmail = buildGmailGAPIObject(user)
        if not gmail:
            continue
        labels = gapi.call(gmail.users().labels(),
                           'list',
                           userId=user,
                           soft_errors=True).get('labels', [])
        i = 0
        for label in labels:
            i += 1
            if onlyUser and (label['type'] == 'system'):
                continue
            if showCounts:
                if i >= 50 and not i % 50:
                    # show label get count for greater than 100 labels
                    # every 100 labels
                    sys.stderr.write('\r')
                    sys.stderr.flush()
                    sys.stderr.write(f'Getting counts for label {i} of {len(labels)}')
                counts = gapi.call(
                    gmail.users().labels(),
                    'get',
                    userId=user,
                    id=label['id'],
                    fields=
                   'messagesTotal,messagesUnread,threadsTotal,threadsUnread'
                )
                label.update(counts)
            if show:
                print(label['name'])
                for a_key in label:
                    if a_key == 'name':
                        continue
                    print(f' {a_key}: {label[a_key]}')
                print('')
            else:
                for key in label:
                    if key not in titles:
                        titles.append(key)
                label['email'] = user
        if not show:
            display.write_csv_file(labels,
                                   titles,
                                   'Gmail Labels',
                                   todrive)


def showGmailProfile(users):
    todrive = False
    i = 6
    while i < len(sys.argv):
        myarg = sys.argv[i].lower()
        if myarg == 'todrive':
            todrive = True
            i += 1
        else:
            controlflow.invalid_argument_exit(sys.argv[i],
                                              'gam <users> show gmailprofile')
    csvRows = []
    titles = ['emailAddress']
    i = 0
    count = len(users)
    for user in users:
        i += 1
        user, gmail = buildGmailGAPIObject(user)
        if not gmail:
            continue
        sys.stderr.write(f'Getting Gmail profile for {user}\n')
        try:
            results = gapi.call(gmail.users(),
                                'getProfile',
                                throw_reasons=gapi_errors.GMAIL_THROW_REASONS,
                                userId='me')
            if results:
                for item in results:
                    if item not in titles:
                        titles.append(item)
                csvRows.append(results)
        except gapi_errors.GapiServiceNotAvailableError:
            entityServiceNotApplicableWarning('User', user, i, count)
    display.sort_csv_titles([
        'emailAddress',
    ], titles)
    display.write_csv_file(csvRows,
                           titles,
                           list_type='Gmail Profiles',
                           todrive=todrive)


def updateLabels(users):
    label_name = sys.argv[5]
    label_name_lower = label_name.lower()
    body = {}
    i = 6
    while i < len(sys.argv):
        myarg = sys.argv[i].lower().replace('_', '')
        if myarg == 'name':
            body['name'] = sys.argv[i + 1]
            i += 2
        else:
            i = getLabelAttributes(i, myarg, body, 'update')
    checkLabelColor(body)
    for user in users:
        user, gmail = buildGmailGAPIObject(user)
        if not gmail:
            continue
        labels = gapi.call(gmail.users().labels(),
                           'list',
                           userId=user,
                           fields='labels(id,name)')
        for label in labels['labels']:
            if label['name'].lower() == label_name_lower:
                gapi.call(gmail.users().labels(),
                          'patch',
                          soft_errors=True,
                          userId=user,
                          id=label['id'],
                          body=body)
                break
        else:
            print(f'Error: user does not have a label named {label_name}')


def cleanLabelQuery(labelQuery):
    for ch in '/ (){}':
        labelQuery = labelQuery.replace(ch, '-')
    return labelQuery.lower()


def renameLabels(users):
    search = '^Inbox/(.*)$'
    replace = '%s'
    merge = False
    i = 5
    while i < len(sys.argv):
        myarg = sys.argv[i].lower()
        if myarg == 'search':
            search = sys.argv[i + 1]
            i += 2
        elif myarg == 'replace':
            replace = sys.argv[i + 1]
            i += 2
        elif myarg == 'merge':
            merge = True
            i += 1
        else:
            controlflow.invalid_argument_exit(sys.argv[i],
                                              'gam <users> rename label')
    pattern = re.compile(search, re.IGNORECASE)
    for user in users:
        user, gmail = buildGmailGAPIObject(user)
        if not gmail:
            continue
        labels = gapi.call(gmail.users().labels(), 'list', userId=user)
        print(f'got {len(labels["labels"])} labels')
        for label in labels['labels']:
            if label['type'] == 'system':
                continue
            match_result = re.search(pattern, label['name'])
            if match_result is not None:
                try:
                    new_label_name = replace % match_result.groups()
                except TypeError:
                    controlflow.system_error_exit(
                        2,
                        f'The number of subfields ({len(match_result.groups())}) in search "{search}" does not match the number of subfields ({replace.count("%s")}) in replace "{replace}"'
                    )
                print(f' Renaming "{label["name"]}" to "{new_label_name}"')
                try:
                    gapi.call(gmail.users().labels(),
                              'patch',
                              soft_errors=True,
                              throw_reasons=[gapi_errors.ErrorReason.ABORTED],
                              id=label['id'],
                              userId=user,
                              body={'name': new_label_name})
                except gapi_errors.GapiAbortedError:
                    if merge:
                        print(
                            f'  Merging {label["name"]} label to existing {new_label_name} label'
                        )
                        messages_to_relabel = gapi.get_all_pages(
                            gmail.users().messages(),
                            'list',
                            'messages',
                            userId=user,
                            q=f'label:{cleanLabelQuery(label["name"])}')
                        if messages_to_relabel:
                            for new_label in labels['labels']:
                                if new_label['name'].lower(
                                ) == new_label_name.lower():
                                    new_label_id = new_label['id']
                                    body = {'addLabelIds': [new_label_id]}
                                    break
                            j = 0
                            jcount = len(messages_to_relabel)
                            for message_to_relabel in messages_to_relabel:
                                j += 1
                                print(
                                    f'    relabeling message {message_to_relabel["id"]}{currentCount(j, jcount)}'
                                )
                                gapi.call(gmail.users().messages(),
                                          'modify',
                                          userId=user,
                                          id=message_to_relabel['id'],
                                          body=body)
                        else:
                            print(f'   no messages with {label["name"]} label')
                        print(f'   Deleting label {label["name"]}')
                        gapi.call(gmail.users().labels(),
                                  'delete',
                                  id=label['id'],
                                  userId=user)
                    else:
                        print(
                            f'  Error: looks like {new_label_name} already exists, not renaming. Use the "merge" argument to merge the labels'
                        )


def _getUserGmailLabels(gmail, user, i, count, **kwargs):
    try:
        labels = gapi.call(gmail.users().labels(),
                           'list',
                           throw_reasons=gapi_errors.GMAIL_THROW_REASONS,
                           userId='me',
                           **kwargs)
        if not labels:
            labels = {'labels': []}
        return labels
    except gapi_errors.GapiServiceNotAvailableError:
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
                row[item] = f'size {userFilter["criteria"]["sizeComparison"]} {userFilter["criteria"][item]}'
            elif item == 'sizeComparison':
                pass
            else:
                row[item] = f'{item} {userFilter["criteria"][item]}'
    else:
        row['error'] = 'NoCriteria'
    if 'action' in userFilter:
        for labelId in userFilter['action'].get('addLabelIds', []):
            if labelId in FILTER_ADD_LABEL_TO_ARGUMENT_MAP:
                row[FILTER_ADD_LABEL_TO_ARGUMENT_MAP[
                    labelId]] = FILTER_ADD_LABEL_TO_ARGUMENT_MAP[labelId]
            else:
                row['label'] = f'label {_getLabelName(labels, labelId)}'
        for labelId in userFilter['action'].get('removeLabelIds', []):
            if labelId in FILTER_REMOVE_LABEL_TO_ARGUMENT_MAP:
                row[FILTER_REMOVE_LABEL_TO_ARGUMENT_MAP[
                    labelId]] = FILTER_REMOVE_LABEL_TO_ARGUMENT_MAP[labelId]
        if userFilter['action'].get('forward'):
            row['forward'] = f'forward {userFilter["action"]["forward"]}'
    else:
        row['error'] = 'NoActions'
    return row


def _showFilter(userFilter, j, jcount, labels):
    print(f'  Filter: {userFilter["id"]}{currentCount(j, jcount)}')
    print('    Criteria:')
    if 'criteria' in userFilter:
        for item in userFilter['criteria']:
            if item in ['hasAttachment', 'excludeChats']:
                print(f'      {item}')
            elif item == 'size':
                print(
                    f'      {item} {userFilter["criteria"]["sizeComparison"]} {userFilter["criteria"][item]}'
                )
            elif item == 'sizeComparison':
                pass
            else:
                print(f'      {item} "{userFilter["criteria"][item]}"')
    else:
        print('      ERROR: No Filter criteria')
    print('    Actions:')
    if 'action' in userFilter:
        for labelId in userFilter['action'].get('addLabelIds', []):
            if labelId in FILTER_ADD_LABEL_TO_ARGUMENT_MAP:
                print(f'      {FILTER_ADD_LABEL_TO_ARGUMENT_MAP[labelId]}')
            else:
                print(f'      label "{_getLabelName(labels, labelId)}"')
        for labelId in userFilter['action'].get('removeLabelIds', []):
            if labelId in FILTER_REMOVE_LABEL_TO_ARGUMENT_MAP:
                print(f'      {FILTER_REMOVE_LABEL_TO_ARGUMENT_MAP[labelId]}')
        if userFilter['action'].get('forward'):
            print(f'    Forwarding Address: {userFilter["action"]["forward"]}')
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
                body['criteria'][myarg] = sys.argv[i + 1]
                i += 2
            elif myarg == 'to':
                body['criteria'][myarg] = sys.argv[i + 1]
                i += 2
            elif myarg in ['subject', 'query', 'negatedQuery']:
                body['criteria'][myarg] = sys.argv[i + 1]
                i += 2
            elif myarg in ['hasAttachment', 'excludeChats']:
                body['criteria'][myarg] = True
                i += 1
            elif myarg == 'size':
                body['criteria']['sizeComparison'] = sys.argv[i + 1].lower()
                if body['criteria']['sizeComparison'] not in [
                        'larger', 'smaller'
                ]:
                    controlflow.system_error_exit(
                        2,
                        f'size must be followed by larger or smaller; got {sys.argv[i+1].lower()}'
                    )
                body['criteria'][myarg] = sys.argv[i + 2]
                i += 3
        elif myarg in FILTER_ACTION_CHOICES:
            body.setdefault('action', {})
            if myarg == 'label':
                addLabelName = sys.argv[i + 1]
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
                body['action']['forward'] = sys.argv[i + 1]
                i += 2
        else:
            controlflow.invalid_argument_exit(sys.argv[i], 'gam <users> filter')
    if 'criteria' not in body:
        controlflow.system_error_exit(
            2,
            f'you must specify a crtieria <{"|".join(FILTER_CRITERIA_CHOICES_MAP)}> for "gam <users> filter"'
        )
    if 'action' not in body:
        controlflow.system_error_exit(
            2,
            f'you must specify an action <{"|".join(FILTER_ACTION_CHOICES)}> for "gam <users> filter"'
        )
    if removeLabelIds:
        body['action']['removeLabelIds'] = removeLabelIds
    i = 0
    count = len(users)
    for user in users:
        i += 1
        user, gmail = buildGmailGAPIObject(user)
        if not gmail:
            continue
        labels = _getUserGmailLabels(gmail,
                                     user,
                                     i,
                                     count,
                                     fields='labels(id,name)')
        if not labels:
            continue
        if addLabelIds:
            body['action']['addLabelIds'] = addLabelIds[:]
        if addLabelName:
            if not addLabelIds:
                body['action']['addLabelIds'] = []
            addLabelId = _getLabelId(labels, addLabelName)
            if not addLabelId:
                result = gapi.call(gmail.users().labels(),
                                   'create',
                                   soft_errors=True,
                                   userId='me',
                                   body={'name': addLabelName},
                                   fields='id')
                if not result:
                    continue
                addLabelId = result['id']
            body['action']['addLabelIds'].append(addLabelId)
        print(f'Adding filter for {user}{currentCount(i, count)}')
        result = gapi.call(gmail.users().settings().filters(),
                           'create',
                           soft_errors=True,
                           userId='me',
                           body=body)
        if result:
            print(
                f'User: {user}, Filter: {result["id"]}, Added{currentCount(i, count)}'
            )


def deleteFilters(users):
    filterId = sys.argv[5]
    i = 0
    count = len(users)
    for user in users:
        i += 1
        user, gmail = buildGmailGAPIObject(user)
        if not gmail:
            continue
        print(f'Deleting filter {filterId} for {user}{currentCount(i, count)}')
        gapi.call(gmail.users().settings().filters(),
                  'delete',
                  soft_errors=True,
                  userId='me',
                  id=filterId)


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
            controlflow.invalid_argument_exit(
                myarg, f"gam <users> {['show', 'print'][csvFormat]} filter")
    i = 0
    count = len(users)
    for user in users:
        i += 1
        user, gmail = buildGmailGAPIObject(user)
        if not gmail:
            continue
        labels = gapi.call(gmail.users().labels(),
                           'list',
                           soft_errors=True,
                           userId='me',
                           fields='labels(id,name)')
        if not labels:
            labels = {'labels': []}
        result = gapi.call(gmail.users().settings().filters(),
                           'list',
                           soft_errors=True,
                           userId='me')
        jcount = len(result.get('filter', [])) if (result) else 0
        if not csvFormat:
            print(f'User: {user}, Filters:{currentCount(i, count)}')
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
        display.sort_csv_titles(['User', 'id'], titles)
        display.write_csv_file(csvRows, titles, 'Filters', todrive)


def infoFilters(users):
    filterId = sys.argv[5]
    i = 0
    count = len(users)
    for user in users:
        i += 1
        user, gmail = buildGmailGAPIObject(user)
        if not gmail:
            continue
        labels = gapi.call(gmail.users().labels(),
                           'list',
                           soft_errors=True,
                           userId='me',
                           fields='labels(id,name)')
        if not labels:
            labels = {'labels': []}
        result = gapi.call(gmail.users().settings().filters(),
                           'get',
                           soft_errors=True,
                           userId='me',
                           id=filterId)
        if result:
            print(f'User: {user}, Filter:{currentCount(i, count)}')
            _showFilter(result, 1, 1, labels)


def doForward(users):
    enable = getBoolean(sys.argv[4], 'gam <users> forward')
    body = {'enabled': enable}
    i = 5
    while i < len(sys.argv):
        myarg = sys.argv[i].lower()
        if myarg in EMAILSETTINGS_FORWARD_POP_ACTION_CHOICES_MAP:
            body['disposition'] = EMAILSETTINGS_FORWARD_POP_ACTION_CHOICES_MAP[
                myarg]
            i += 1
        elif myarg == 'confirm':
            i += 1
        elif myarg.find('@') != -1:
            body['emailAddress'] = sys.argv[i]
            i += 1
        else:
            controlflow.invalid_argument_exit(myarg, 'gam <users> forward')
    if enable and (not body.get('disposition') or not body.get('emailAddress')):
        controlflow.system_error_exit(
            2,
            'you must specify an action and a forwarding address for "gam <users> forward'
        )
    i = 0
    count = len(users)
    for user in users:
        i += 1
        user, gmail = buildGmailGAPIObject(user)
        if not gmail:
            continue
        if enable:
            print(
                f'User: {user}, Forward Enabled: {enable}, Forwarding Address: {body["emailAddress"]}, Action: {body["disposition"]}{currentCount(i, count)}'
            )
        else:
            print(
                f'User: {user}, Forward Enabled: {enable}{currentCount(i, count)}'
            )
        gapi.call(gmail.users().settings(),
                  'updateAutoForwarding',
                  soft_errors=True,
                  userId='me',
                  body=body)


def printShowForward(users, csvFormat):

    def _showForward(user, i, count, result):
        if 'enabled' in result:
            enabled = result['enabled']
            if enabled:
                print(
                    f'User: {user}, Forward Enabled: {enabled}, Forwarding Address: {result["emailAddress"]}, Action: {result["disposition"]}{currentCount(i, count)}'
                )
            else:
                print(
                    f'User: {user}, Forward Enabled: {enabled}{currentCount(i, count)}'
                )
        else:
            enabled = result['enable'] == 'true'
            if enabled:
                print(
                    f'User: {user}, Forward Enabled: {enabled}, Forwarding Address: {result["forwardTo"]}, Action: {EMAILSETTINGS_OLD_NEW_OLD_FORWARD_ACTION_MAP[result["action"]]}{currentCount(i, count)}'
                )
            else:
                print(
                    f'User: {user}, Forward Enabled: {enabled}{currentCount(i, count)}'
                )

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
                row['disposition'] = EMAILSETTINGS_OLD_NEW_OLD_FORWARD_ACTION_MAP[
                    result['action']]
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
            controlflow.invalid_argument_exit(
                myarg, f"gam <users> {['show', 'print'][csvFormat]} forward")
    i = 0
    count = len(users)
    for user in users:
        i += 1
        user, gmail = buildGmailGAPIObject(user)
        if not gmail:
            continue
        result = gapi.call(gmail.users().settings(),
                           'getAutoForwarding',
                           soft_errors=True,
                           userId='me')
        if result:
            if not csvFormat:
                _showForward(user, i, count, result)
            else:
                _printForward(user, result)
    if csvFormat:
        display.write_csv_file(csvRows, titles, 'Forward', todrive)


def addForwardingAddresses(users):
    emailAddress = normalizeEmailAddressOrUID(sys.argv[5], noUid=True)
    body = {'forwardingEmail': emailAddress}
    i = 0
    count = len(users)
    for user in users:
        i += 1
        user, gmail = buildGmailGAPIObject(user)
        if not gmail:
            continue
        print(
            f'Adding Forwarding Address {emailAddress} for {user}{currentCount(i, count)}'
        )
        gapi.call(gmail.users().settings().forwardingAddresses(),
                  'create',
                  soft_errors=True,
                  userId='me',
                  body=body)


def deleteForwardingAddresses(users):
    emailAddress = normalizeEmailAddressOrUID(sys.argv[5], noUid=True)
    i = 0
    count = len(users)
    for user in users:
        i += 1
        user, gmail = buildGmailGAPIObject(user)
        if not gmail:
            continue
        print(
            f'deleting Forwarding Address {emailAddress} for {user}{currentCount(i, count)}'
        )
        gapi.call(gmail.users().settings().forwardingAddresses(),
                  'delete',
                  soft_errors=True,
                  userId='me',
                  forwardingEmail=emailAddress)


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
            controlflow.invalid_argument_exit(
                myarg,
                f"gam <users> {['show', 'print'][csvFormat]} forwardingaddresses"
            )
    i = 0
    count = len(users)
    for user in users:
        i += 1
        user, gmail = buildGmailGAPIObject(user)
        if not gmail:
            continue
        result = gapi.call(gmail.users().settings().forwardingAddresses(),
                           'list',
                           soft_errors=True,
                           userId='me')
        jcount = len(result.get('forwardingAddresses', [])) if (result) else 0
        if not csvFormat:
            print(
                f'User: {user}, Forwarding Addresses:{currentCount(i, count)}')
            if jcount == 0:
                continue
            j = 0
            for forward in result['forwardingAddresses']:
                j += 1
                print(
                    f'  Forwarding Address: {forward["forwardingEmail"]}, Verification Status: {forward["verificationStatus"]}{currentCount(j, jcount)}'
                )
        else:
            if jcount == 0:
                continue
            for forward in result['forwardingAddresses']:
                row = {
                    'User': user,
                    'forwardingEmail': forward['forwardingEmail'],
                    'verificationStatus': forward['verificationStatus']
                }
                csvRows.append(row)
    if csvFormat:
        display.write_csv_file(csvRows, titles, 'Forwarding Addresses', todrive)


def infoForwardingAddresses(users):
    emailAddress = normalizeEmailAddressOrUID(sys.argv[5], noUid=True)
    i = 0
    count = len(users)
    for user in users:
        i += 1
        user, gmail = buildGmailGAPIObject(user)
        if not gmail:
            continue
        forward = gapi.call(gmail.users().settings().forwardingAddresses(),
                            'get',
                            soft_errors=True,
                            userId='me',
                            forwardingEmail=emailAddress)
        if forward:
            print(
                f'User: {user}, Forwarding Address: {forward["forwardingEmail"]}, Verification Status: {forward["verificationStatus"]}{currentCount(i, count)}'
            )


def doSignature(users):
    tagReplacements = {}
    i = 4
    if sys.argv[i].lower() == 'file':
        filename = sys.argv[i + 1]
        i, encoding = getCharSet(i + 2)
        signature = fileutils.read_file(filename, encoding=encoding)
    else:
        signature = utils.get_string(i, 'String', minLen=0)
        i += 1
    body = {}
    html = False
    while i < len(sys.argv):
        myarg = sys.argv[i].lower()
        if myarg == 'html':
            html = True
            i += 1
        else:
            i = getSendAsAttributes(i, myarg, body, tagReplacements,
                                    'signature')
    body['signature'] = _processSignature(tagReplacements, signature, html)
    i = 0
    count = len(users)
    for user in users:
        i += 1
        user, gmail = buildGmailGAPIObject(user)
        if not gmail:
            continue
        print(f'Setting Signature for {user}{currentCount(i, count)}')
        gapi.call(gmail.users().settings().sendAs(),
                  'patch',
                  soft_errors=True,
                  userId='me',
                  body=body,
                  sendAsEmail=user)


def getSignature(users):
    formatSig = False
    i = 5
    while i < len(sys.argv):
        myarg = sys.argv[i].lower()
        if myarg == 'format':
            formatSig = True
            i += 1
        else:
            controlflow.invalid_argument_exit(sys.argv[i],
                                              'gam <users> show signature')
    i = 0
    count = len(users)
    for user in users:
        i += 1
        user, gmail = buildGmailGAPIObject(user)
        if not gmail:
            continue
        result = gapi.call(gmail.users().settings().sendAs(),
                           'get',
                           soft_errors=True,
                           userId='me',
                           sendAsEmail=user)
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
                body['responseSubject'] = sys.argv[i + 1]
                i += 2
            elif myarg == 'message':
                message = sys.argv[i + 1]
                i += 2
            elif myarg == 'file':
                filename = sys.argv[i + 1]
                i, encoding = getCharSet(i + 2)
                message = fileutils.read_file(filename, encoding=encoding)
            elif myarg == 'replace':
                matchTag = utils.get_string(i + 1, 'Tag')
                matchReplacement = utils.get_string(i + 2, 'String', minLen=0)
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
                body['startTime'] = utils.get_yyyymmdd(sys.argv[i + 1],
                                                       returnTimeStamp=True)
                i += 2
            elif myarg == 'enddate':
                body['endTime'] = utils.get_yyyymmdd(sys.argv[i + 1],
                                                     returnTimeStamp=True)
                i += 2
            else:
                controlflow.invalid_argument_exit(sys.argv[i],
                                                  'gam <users> vacation')
        if message:
            if responseBodyType == 'responseBodyHtml':
                message = message.replace('\r', '').replace('\\n', '<br/>')
            else:
                message = message.replace('\r', '').replace('\\n', '\n')
            if tagReplacements:
                message = _processTags(tagReplacements, message)
            body[responseBodyType] = message
        if not message and not body.get('responseSubject'):
            controlflow.system_error_exit(
                2, 'You must specify a non-blank subject or message!')
    i = 0
    count = len(users)
    for user in users:
        i += 1
        user, gmail = buildGmailGAPIObject(user)
        if not gmail:
            continue
        print(f'Setting Vacation for {user}{currentCount(i, count)}')
        gapi.call(gmail.users().settings(),
                  'updateVacation',
                  soft_errors=True,
                  userId='me',
                  body=body)


def getVacation(users):
    formatReply = False
    i = 5
    while i < len(sys.argv):
        myarg = sys.argv[i].lower()
        if myarg == 'format':
            formatReply = True
            i += 1
        else:
            controlflow.invalid_argument_exit(sys.argv[i],
                                              'gam <users> show vacation')
    i = 0
    count = len(users)
    for user in users:
        i += 1
        user, gmail = buildGmailGAPIObject(user)
        if not gmail:
            continue
        result = gapi.call(gmail.users().settings(),
                           'getVacation',
                           soft_errors=True,
                           userId='me')
        if result:
            enabled = result['enableAutoReply']
            print(f'User: {user}, Vacation:{currentCount(i, count)}')
            print(f'  Enabled: {enabled}')
            if enabled:
                print(f'  Contacts Only: {result["restrictToContacts"]}')
                print(f'  Domain Only: {result["restrictToDomain"]}')
                if 'startTime' in result:
                    print(
                        f'  Start Date: {utils.formatTimestampYMD(result["startTime"])}'
                    )
                else:
                    print('  Start Date: Started')
                if 'endTime' in result:
                    print(
                        f'  End Date: {utils.formatTimestampYMD(result["endTime"])}'
                    )
                else:
                    print('  End Date: Not specified')
                print(f'  Subject: {result.get("responseSubject", "None")}')
                sys.stdout.write('  Message:\n   ')
                if result.get('responseBodyPlainText'):
                    print(
                        utils.indentMultiLineText(
                            result['responseBodyPlainText'], n=4))
                elif result.get('responseBodyHtml'):
                    if formatReply:
                        print(
                            utils.indentMultiLineText(utils.dehtml(
                                result['responseBodyHtml']),
                                                      n=4))
                    else:
                        print(
                            utils.indentMultiLineText(
                                result['responseBodyHtml'], n=4))
                else:
                    print('None')


def doDelSchema():
    cd = buildGAPIObject('directory')
    schemaKey = sys.argv[3]
    gapi.call(cd.schemas(),
              'delete',
              customerId=GC_Values[GC_CUSTOMER_ID],
              schemaKey=schemaKey)
    print(f'Deleted schema {schemaKey}')


def doCreateOrUpdateUserSchema(updateCmd):
    cd = buildGAPIObject('directory')
    schemaKey = sys.argv[3]
    if updateCmd:
        cmd = 'update'
        try:
            body = gapi.call(cd.schemas(),
                             'get',
                             throw_reasons=[gapi_errors.ErrorReason.NOT_FOUND],
                             customerId=GC_Values[GC_CUSTOMER_ID],
                             schemaKey=schemaKey)
        except gapi_errors.GapiNotFoundError:
            controlflow.system_error_exit(
                3, f'Schema {schemaKey} does not exist.')
    else:  # create
        cmd = 'create'
        body = {'schemaName': schemaKey, 'fields': []}
    i = 4
    while i < len(sys.argv):
        myarg = sys.argv[i].lower()
        if myarg == 'field':
            if updateCmd:  # clear field if it exists on update
                for n, field in enumerate(body['fields']):
                    if field['fieldName'].lower() == sys.argv[i + 1].lower():
                        del body['fields'][n]
                        break
            a_field = {'fieldName': sys.argv[i + 1]}
            i += 2
            while True:
                myarg = sys.argv[i].lower()
                if myarg == 'type':
                    a_field['fieldType'] = sys.argv[i + 1].upper()
                    validTypes = [
                        'BOOL', 'DATE', 'DOUBLE', 'EMAIL', 'INT64', 'PHONE', 'STRING'
                    ]
                    if a_field['fieldType'] not in validTypes:
                        controlflow.expected_argument_exit(
                            'type', ', '.join(validTypes).lower(),
                            a_field['fieldType'])
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
                    a_field['numericIndexingSpec'] = {
                        'minValue': getInteger(sys.argv[i + 1], myarg),
                        'maxValue': getInteger(sys.argv[i + 2], myarg)
                    }
                    i += 3
                elif myarg == 'endfield':
                    body['fields'].append(a_field)
                    i += 1
                    break
                else:
                    controlflow.invalid_argument_exit(sys.argv[i],
                                                      f'gam {cmd} schema')
        elif updateCmd and myarg == 'deletefield':
            for n, field in enumerate(body['fields']):
                if field['fieldName'].lower() == sys.argv[i + 1].lower():
                    del body['fields'][n]
                    break
            else:
                controlflow.system_error_exit(
                    2, f'field {sys.argv[i+1]} not found in schema {schemaKey}')
            i += 2
        else:
            controlflow.invalid_argument_exit(sys.argv[i], f'gam {cmd} schema')
    if updateCmd:
        result = gapi.call(cd.schemas(),
                           'update',
                           customerId=GC_Values[GC_CUSTOMER_ID],
                           body=body,
                           schemaKey=schemaKey)
        print(f'Updated user schema {result["schemaName"]}')
    else:
        result = gapi.call(cd.schemas(),
                           'insert',
                           customerId=GC_Values[GC_CUSTOMER_ID],
                           body=body)
        print(f'Created user schema {result["schemaName"]}')


def _showSchema(schema):
    print(f'Schema: {schema["schemaName"]}')
    for a_key in schema:
        if a_key not in ['schemaName', 'fields', 'etag', 'kind']:
            print(f' {a_key}: {schema[a_key]}')
    for field in schema['fields']:
        print(f' Field: {field["fieldName"]}')
        for a_key in field:
            if a_key not in ['fieldName', 'kind', 'etag']:
                print(f'  {a_key}: {field[a_key]}')


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
            controlflow.invalid_argument_exit(
                myarg, f"gam <users> {['show', 'print'][csvFormat]} schemas")
    schemas = gapi.call(cd.schemas(),
                        'list',
                        customerId=GC_Values[GC_CUSTOMER_ID])
    if not schemas or 'schemas' not in schemas:
        return
    for schema in schemas['schemas']:
        if not csvFormat:
            _showSchema(schema)
        else:
            row = {'fields.Count': len(schema['fields'])}
            display.add_row_titles_to_csv_file(
                utils.flatten_json(schema, flattened=row), csvRows, titles)
    if csvFormat:
        display.sort_csv_titles(['schemaId', 'schemaName', 'fields.Count'],
                                titles)
        display.write_csv_file(csvRows, titles, 'User Schemas', todrive)


def doGetUserSchema():
    cd = buildGAPIObject('directory')
    schemaKey = sys.argv[3]
    schema = gapi.call(cd.schemas(),
                       'get',
                       customerId=GC_Values[GC_CUSTOMER_ID],
                       schemaKey=schemaKey)
    _showSchema(schema)


def getUserAttributes(i, cd, updateCmd):

    def getEntryType(i,
                     entry,
                     entryTypes,
                     setTypeCustom=True,
                     customKeyword='custom',
                     customTypeKeyword='customType'):
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
        return i + 1

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
                    if not checkSystemId or itemValue.get(
                            'systemId') == citem.get('systemId'):
                        controlflow.system_error_exit(
                            2,
                            f'Multiple {itemName} are marked primary, only one can be primary'
                        )
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
        controlflow.system_error_exit(
            2, f'{sn_fn} is not a valid custom schema.field name.')

    if updateCmd:
        body = {}
        need_password = False
    else:
        body = {'name': {'givenName': 'Unknown', 'familyName': 'Unknown'}}
        body['primaryEmail'] = normalizeEmailAddressOrUID(sys.argv[i],
                                                          noUid=True)
        i += 1
        need_password = True
    need_to_hash_password = True
    need_to_b64_decrypt_password = False
    verifyNotInvitable = False
    while i < len(sys.argv):
        myarg = sys.argv[i].lower()
        if myarg in ['firstname', 'givenname']:
            body.setdefault('name', {})
            body['name']['givenName'] = sys.argv[i + 1]
            i += 2
        elif myarg in ['lastname', 'familyname']:
            body.setdefault('name', {})
            body['name']['familyName'] = sys.argv[i + 1]
            i += 2
        elif myarg in ['username', 'email', 'primaryemail'] and updateCmd:
            body['primaryEmail'] = normalizeEmailAddressOrUID(sys.argv[i + 1],
                                                              noUid=True)
            i += 2
        elif myarg == 'customerid' and updateCmd:
            body['customerId'] = sys.argv[i + 1]
            i += 2
        elif myarg == 'password':
            need_password = False
            body['password'] = sys.argv[i + 1]
            if body['password'].lower() == 'random':
                need_password = True
            i += 2
        elif myarg == 'admin':
            value = getBoolean(sys.argv[i + 1], myarg)
            if updateCmd or value:
                controlflow.invalid_argument_exit(
                    f'{sys.argv[i]} {value}',
                    f"gam {['create', 'update'][updateCmd]} user")
            i += 2
        elif myarg == 'suspended':
            body['suspended'] = getBoolean(sys.argv[i + 1], myarg)
            i += 2
        elif myarg == 'archived':
            body['archived'] = getBoolean(sys.argv[i + 1], myarg)
            i += 2
        elif myarg == 'gal':
            body['includeInGlobalAddressList'] = getBoolean(
                sys.argv[i + 1], myarg)
            i += 2
        elif myarg in ['sha', 'sha1', 'sha-1', 'base64-sha1']:
            body['hashFunction'] = 'SHA-1'
            need_to_hash_password = False
            if myarg == 'base64-sha1':
                need_to_b64_decrypt_password = True
            i += 1
        elif myarg in ['md5', 'base64-md5']:
            body['hashFunction'] = 'MD5'
            need_to_hash_password = False
            if myarg == 'base64-md5':
                need_to_b64_decrypt_password = True
            i += 1
        elif myarg == 'crypt':
            body['hashFunction'] = 'crypt'
            need_to_hash_password = False
            i += 1
        elif myarg == 'nohash':
            need_to_hash_password = False
            i += 1
        elif myarg == 'changepassword':
            body['changePasswordAtNextLogin'] = getBoolean(
                sys.argv[i + 1], myarg)
            i += 2
        elif myarg == 'ipwhitelisted':
            body['ipWhitelisted'] = getBoolean(sys.argv[i + 1], myarg)
            i += 2
        elif myarg == 'agreedtoterms':
            body['agreedToTerms'] = getBoolean(sys.argv[i + 1], myarg)
            i += 2
        elif myarg in ['org', 'ou']:
            body['orgUnitPath'] = gapi_directory_orgunits.getOrgUnitItem(
                sys.argv[i + 1], pathOnly=True)
            i += 2
        elif myarg in ['language', 'languages']:
            i += 1
            if checkClearBodyList(i, body, 'languages'):
                i += 1
                continue
            for language in sys.argv[i].replace(',', ' ').split():
                if language.lower() in LANGUAGE_CODES_MAP:
                    appendItemToBodyList(
                        body, 'languages',
                        {'languageCode': LANGUAGE_CODES_MAP[language.lower()]})
                else:
                    appendItemToBodyList(body, 'languages',
                                         {'customLanguage': language})
            i += 1
        elif myarg == 'gender':
            i += 1
            if checkClearBodyList(i, body, 'gender'):
                i += 1
                continue
            gender = {}
            i = getEntryType(i,
                             gender,
                             USER_GENDER_TYPES,
                             customKeyword='other',
                             customTypeKeyword='customGender')
            if (i < len(sys.argv)) and (sys.argv[i].lower() == 'addressmeas'):
                gender['addressMeAs'] = utils.get_string(i + 1, 'String')
                i += 2
            body['gender'] = gender
        elif myarg in ['address', 'addresses']:
            i += 1
            if checkClearBodyList(i, body, 'addresses'):
                i += 1
                continue
            address = {}
            if sys.argv[i].lower() != 'type':
                controlflow.system_error_exit(
                    2,
                    f'wrong format for account address details. Expected type got {sys.argv[i]}'
                )
            i = getEntryType(i + 1, address, USER_ADDRESS_TYPES)
            if sys.argv[i].lower() in ['unstructured', 'formatted']:
                i += 1
                address['sourceIsStructured'] = False
                address['formatted'] = sys.argv[i].replace('\\n', '\n')
                i += 1
            while True:
                myopt = sys.argv[i].lower()
                if myopt == 'pobox':
                    address['poBox'] = sys.argv[i + 1]
                    i += 2
                elif myopt == 'extendedaddress':
                    address['extendedAddress'] = sys.argv[i + 1]
                    i += 2
                elif myopt == 'streetaddress':
                    address['streetAddress'] = sys.argv[i + 1]
                    i += 2
                elif myopt == 'locality':
                    address['locality'] = sys.argv[i + 1]
                    i += 2
                elif myopt == 'region':
                    address['region'] = sys.argv[i + 1]
                    i += 2
                elif myopt == 'postalcode':
                    address['postalCode'] = sys.argv[i + 1]
                    i += 2
                elif myopt == 'country':
                    address['country'] = sys.argv[i + 1]
                    i += 2
                elif myopt == 'countrycode':
                    address['countryCode'] = sys.argv[i + 1]
                    i += 2
                elif myopt in ['notprimary', 'primary']:
                    address['primary'] = myopt == 'primary'
                    i += 1
                    break
                else:
                    controlflow.system_error_exit(
                        2,
                        f'invalid argument ({sys.argv[i]}) for account address details'
                    )
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
                controlflow.system_error_exit(
                    2,
                    f'wrong format for account im details. Expected type got {sys.argv[i]}'
                )
            i = getEntryType(i + 1, im, USER_IM_TYPES)
            if sys.argv[i].lower() != 'protocol':
                controlflow.system_error_exit(
                    2,
                    f'wrong format for account details. Expected protocol got {sys.argv[i]}'
                )
            i += 1
            im['protocol'] = sys.argv[i].lower()
            validProtocols = [
                'custom_protocol', 'aim', 'gtalk', 'icq', 'jabber', 'msn',
                'net_meeting', 'qq', 'skype', 'yahoo'
            ]
            if im['protocol'] not in validProtocols:
                controlflow.expected_argument_exit('protocol',
                                                   ', '.join(validProtocols),
                                                   im['protocol'])
            if im['protocol'] == 'custom_protocol':
                i += 1
                im['customProtocol'] = sys.argv[i]
            i += 1
            # Backwards compatibility: notprimary|primary on either side of IM address
            myopt = sys.argv[i].lower()
            if myopt in ['notprimary', 'primary']:
                im['primary'] = myopt == 'primary'
                i += 1
            im['im'] = sys.argv[i]
            i += 1
            myopt = sys.argv[i].lower() if i < len(sys.argv) else ''
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
                    organization['name'] = sys.argv[i + 1]
                    i += 2
                elif myopt == 'title':
                    organization['title'] = sys.argv[i + 1]
                    i += 2
                elif myopt == 'customtype':
                    organization['customType'] = sys.argv[i + 1]
                    organization.pop('type', None)
                    i += 2
                elif myopt == 'type':
                    i = getEntryType(i + 1,
                                     organization,
                                     USER_ORGANIZATION_TYPES,
                                     setTypeCustom=False)
                elif myopt == 'department':
                    organization['department'] = sys.argv[i + 1]
                    i += 2
                elif myopt == 'symbol':
                    organization['symbol'] = sys.argv[i + 1]
                    i += 2
                elif myopt == 'costcenter':
                    organization['costCenter'] = sys.argv[i + 1]
                    i += 2
                elif myopt == 'location':
                    organization['location'] = sys.argv[i + 1]
                    i += 2
                elif myopt == 'description':
                    organization['description'] = sys.argv[i + 1]
                    i += 2
                elif myopt == 'domain':
                    organization['domain'] = sys.argv[i + 1]
                    i += 2
                elif myopt in ['notprimary', 'primary']:
                    organization['primary'] = myopt == 'primary'
                    i += 1
                    break
                else:
                    controlflow.system_error_exit(
                        2,
                        f'invalid argument ({sys.argv[i]}) for account organization details'
                    )
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
                    phone['value'] = sys.argv[i + 1]
                    i += 2
                elif myopt == 'type':
                    i = getEntryType(i + 1, phone, USER_PHONE_TYPES)
                elif myopt in ['notprimary', 'primary']:
                    phone['primary'] = myopt == 'primary'
                    i += 1
                    break
                else:
                    controlflow.system_error_exit(
                        2,
                        f'invalid argument ({sys.argv[i]}) for account phone details'
                    )
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
            myopt = sys.argv[i].lower() if i < len(sys.argv) else ''
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
                filename = sys.argv[i + 1]
                i, encoding = getCharSet(i + 2)
                note['value'] = fileutils.read_file(filename, encoding=encoding)
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
                    i = getEntryType(i + 1, location, USER_LOCATION_TYPES)
                elif myopt == 'area':
                    location['area'] = sys.argv[i + 1]
                    i += 2
                elif myopt in ['building', 'buildingid']:
                    location[
                        'buildingId'] = gapi_directory_resource.getBuildingByNameOrId(
                            cd, sys.argv[i + 1])
                    i += 2
                elif myopt in ['desk', 'deskcode']:
                    location['deskCode'] = sys.argv[i + 1]
                    i += 2
                elif myopt in ['floor', 'floorname']:
                    location['floorName'] = sys.argv[i + 1]
                    i += 2
                elif myopt in ['section', 'floorsection']:
                    location['floorSection'] = sys.argv[i + 1]
                    i += 2
                elif myopt in ['endlocation']:
                    i += 1
                    break
                else:
                    controlflow.system_error_exit(
                        3,
                        f'{myopt} is not a valid argument for user location details. Make sure user location details end with an endlocation argument'
                    )
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
                    ssh['expirationTimeUsec'] = getInteger(sys.argv[i + 1],
                                                           myopt,
                                                           minVal=0)
                    i += 2
                elif myopt == 'key':
                    ssh['key'] = sys.argv[i + 1]
                    i += 2
                elif myopt in ['endssh']:
                    i += 1
                    break
                else:
                    controlflow.system_error_exit(
                        3,
                        f'{myopt} is not a valid argument for user ssh details. Make sure user ssh details end with an endssh argument'
                    )
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
                    posix['gecos'] = sys.argv[i + 1]
                    i += 2
                elif myopt == 'gid':
                    posix['gid'] = getInteger(sys.argv[i + 1], myopt, minVal=0)
                    i += 2
                elif myopt == 'uid':
                    posix['uid'] = getInteger(sys.argv[i + 1],
                                              myopt,
                                              minVal=1000)
                    i += 2
                elif myopt in ['home', 'homedirectory']:
                    posix['homeDirectory'] = sys.argv[i + 1]
                    i += 2
                elif myopt in ['primary']:
                    posix['primary'] = getBoolean(sys.argv[i + 1], myopt)
                    i += 2
                elif myopt in ['shell']:
                    posix['shell'] = sys.argv[i + 1]
                    i += 2
                elif myopt in ['system', 'systemid']:
                    posix['systemId'] = sys.argv[i + 1]
                    i += 2
                elif myopt in ['username', 'name']:
                    posix['username'] = sys.argv[i + 1]
                    i += 2
                elif myopt in ['os', 'operatingsystemtype']:
                    posix['operatingSystemType'] = sys.argv[i + 1]
                    i += 2
                elif myopt in ['endposix']:
                    i += 1
                    break
                else:
                    controlflow.system_error_exit(
                        3,
                        f'{myopt} is not a valid argument for user posix details. Make sure user posix details end with an endposix argument'
                    )
            appendItemToBodyList(body,
                                 'posixAccounts',
                                 posix,
                                 checkSystemId=True)
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
        elif myarg in ['recoveryemail']:
            body['recoveryEmail'] = sys.argv[i + 1]
            i += 2
        elif myarg in ['recoveryphone']:
            body['recoveryPhone'] = sys.argv[i + 1]
            if body['recoveryPhone'] and body['recoveryPhone'][0] != '+':
                body['recoveryPhone'] = '+' + body['recoveryPhone']
            i += 2
        elif myarg == 'clearschema':
            if not updateCmd:
                controlflow.invalid_argument_exit(sys.argv[i],
                                                  'gam create user')
            schemaName, fieldName = _splitSchemaNameDotFieldName(
                sys.argv[i + 1], False)
            up = 'customSchemas'
            body.setdefault(up, {})
            body[up].setdefault(schemaName, {})
            if fieldName is None:
                schema = gapi.call(cd.schemas(),
                                   'get',
                                   soft_errors=True,
                                   customerId=GC_Values[GC_CUSTOMER_ID],
                                   schemaKey=schemaName,
                                   fields='fields(fieldName)')
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
            if multivalue in [
                    'multivalue', 'multivalued', 'value', 'multinonempty'
            ]:
                i += 1
                body[up][schemaName].setdefault(fieldName, [])
                schemaValue = {}
                if sys.argv[i].lower() == 'type':
                    i += 1
                    schemaValue['type'] = sys.argv[i].lower()
                    validSchemaTypes = ['custom', 'home', 'other', 'work']
                    if schemaValue['type'] not in validSchemaTypes:
                        controlflow.expected_argument_exit(
                            'schema type', ', '.join(validSchemaTypes),
                            schemaValue['type'])
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
        elif myarg == 'verifynotinvitable':
            verifyNotInvitable = True
            i += 1
        else:
            controlflow.invalid_argument_exit(
                sys.argv[i], f"gam {['create', 'update'][updateCmd]} user")
    if need_password:
        # generate a password with unicode chars that are not allowed in
        # passwords. We expect "password random nohash" to fail but no one
        # should be using that. Our goal here is to purposefully block login
        # with this password.
        pass_chars = [chr(i) for i in range(1, 55296)]
        rnd = SystemRandom()
        body['password'] = ''.join(
            rnd.choice(pass_chars) for _ in range(4096))
    if 'password' in body and need_to_hash_password:
        body['password'] = gen_sha512_hash(body['password'])
        body['hashFunction'] = 'crypt'
    elif 'password' in body and need_to_b64_decrypt_password:
        if body['password'].lower()[:5] in ['{md5}', '{sha}']:
            body['password'] = body['password'][5:]
        body['password'] = base64.b64decode(body['password']).hex()
    return (body, verifyNotInvitable)


def getCRMService(login_hint):
    scopes = ['https://www.googleapis.com/auth/cloud-platform']
    client_id = '297408095146-fug707qsjv4ikron0hugpevbrjhkmsk7.apps.googleusercontent.com'
    client_secret = 'qM3dP8f_4qedwzWQE1VR4zzU'
    creds = gam.auth.oauth.Credentials.from_client_secrets(
        client_id,
        client_secret,
        scopes,
        'online',
        login_hint=login_hint,
        use_console_flow=not GC_Values[GC_OAUTH_BROWSER])
    httpc = transport.AuthorizedHttp(creds, transport.create_http())
    return getService('cloudresourcemanager', httpc), httpc


def getGAMProjectFile(filepath):
    # if file exists locally in GAM path then use it.
    # allows for testing changes before updating project.
    local_file = os.path.join(GM_Globals[GM_GAM_PATH], filepath)
    if os.path.isfile(local_file):
        return fileutils.read_file(local_file,
                                   continue_on_error=False,
                                   display_errors=True)
    file_url = GAM_PROJECT_FILEPATH + filepath
    httpObj = transport.create_http()
    _, c = httpObj.request(file_url, 'GET')
    return c.decode(UTF8)


def enableGAMProjectAPIs(GAMProjectAPIs,
                         httpObj,
                         projectId,
                         checkEnabled,
                         i=0,
                         count=0):
    apis = GAMProjectAPIs[:]
    project_name = f'projects/{projectId}'
    serveu = getService('serviceusage', httpObj)
    status = True
    if checkEnabled:
        try:
            services = gapi.get_all_pages(
                serveu.services(),
                'list',
                'services',
                throw_reasons=[gapi_errors.ErrorReason.NOT_FOUND],
                parent=project_name,
                filter='state:ENABLED',
                fields='nextPageToken,services(name)')
            jcount = len(services)
            print(
                f'  Project: {projectId}, Check {jcount} APIs{currentCount(i, count)}'
            )
            j = 0
            for service in sorted(services, key=lambda k: k['name']):
                j += 1
                if 'name' in service:
                    service_name = service['name'].split('/')[-1]
                    if service_name in apis:
                        print(
                            f'    API: {service_name}, Already enabled{currentCount(j, jcount)}'
                        )
                        apis.remove(service_name)
                    else:
                        print(
                            f'    API: {service_name}, Already enabled (non-GAM which is fine){currentCount(j, jcount)}'
                        )
        except gapi_errors.GapiNotFoundError as e:
            print(
                f'  Project: {projectId}, Update Failed: {str(e)}{currentCount(i, count)}'
            )
            status = False
    jcount = len(apis)
    if status and jcount > 0:
        print(
            f'  Project: {projectId}, Enable {jcount} APIs{currentCount(i, count)}'
        )
        j = 0
        for api in apis:
            service_name = f'projects/{projectId}/services/{api}'
            j += 1
            while True:
                try:
                    gapi.call(serveu.services(),
                              'enable',
                              throw_reasons=[
                                  gapi_errors.ErrorReason.FAILED_PRECONDITION,
                                  gapi_errors.ErrorReason.FORBIDDEN,
                                  gapi_errors.ErrorReason.PERMISSION_DENIED
                              ],
                              name=service_name)
                    print(f'    API: {api}, Enabled{currentCount(j, jcount)}')
                    break
                except gapi_errors.GapiFailedPreconditionError as e:
                    print(
                        f'\nThere was an error enabling {api}. Please resolve error as described below:'
                    )
                    print()
                    print(f'\n{str(e)}\n')
                    print()
                    input(
                        'Press enter once resolved and we will try enabling the API again.'
                    )
                except (gapi_errors.GapiForbiddenError,
                        gapi_errors.GapiPermissionDeniedError) as e:
                    print(
                        f'    API: {api}, Enable Failed: {str(e)}{currentCount(j, jcount)}'
                    )
                    status = False
    return status


def _grantRotateRights(iam, service_account, email, account_type='serviceAccount'):
    print(f'Giving account {email} rights to rotate {service_account} private key')
    body = {
        'policy': {
            'bindings': [{
                'role': 'roles/iam.serviceAccountKeyAdmin',
                'members': [f'{account_type}:{email}']
            }]
        }
    }
    gapi.call(iam.projects().serviceAccounts(),
              'setIamPolicy',
              resource=f'projects/-/serviceAccounts/{service_account}',
              body=body)


def setGAMProjectConsentScreen(httpObj, projectId, login_hint):
    print('Setting GAM project consent screen...')
    iap = getService('iap', httpObj)
    body = {'applicationTitle': 'GAM', 'supportEmail': login_hint}
    throw_reasons = [
        gapi_errors.ErrorReason.FOUR_O_NINE, gapi_errors.ErrorReason.FOUR_O_O
    ]
    try:
        gapi.call(iap.projects().brands(),
                  'create',
                  parent=f'projects/{projectId}',
                  body=body,
                  throw_reasons=throw_reasons)
    except googleapiclient.errors.HttpError:
        pass


def _createClientSecretsOauth2service(httpObj, projectId, login_hint):

    def _checkClientAndSecret(simplehttp, client_id, client_secret):
        url = 'https://oauth2.googleapis.com/token'
        post_data = {
            'client_id':
                client_id,
            'client_secret':
                client_secret,
            'code':
                'ThisIsAnInvalidCodeOnlyBeingUsedToTestIfClientAndSecretAreValid',
            'redirect_uri':
                'urn:ietf:wg:oauth:2.0:oob',
            'grant_type':
                'authorization_code'
        }
        headers = {'Content-type': 'application/x-www-form-urlencoded'}
        _, content = simplehttp.request(url,
                                        'POST',
                                        urlencode(post_data),
                                        headers=headers)
        try:
            content = json.loads(content)
        except ValueError:
            print(f'Unknown error: {content}')
            return False
        if not 'error' in content or not 'error_description' in content:
            print(f'Unknown error: {content}')
            return False
        if content['error'] == 'invalid_grant':
            return True
        if content['error_description'] == 'The OAuth client was not found.':
            print(
                f'Ooops!!\n\n{client_id}\n\nIs not a valid client ID. Please make sure you are following the directions exactly and that there are no extra spaces in your client ID.'
            )
            return False
        if content['error_description'] == 'Unauthorized':
            print(
                f'Ooops!!\n\n{client_secret}\n\nIs not a valid client secret. Please make sure you are following the directions exactly and that there are no extra spaces in your client secret.'
            )
            return False
        print(f'Unknown error: {content}')
        return False

    GAMProjectAPIs = getGAMProjectFile('project-apis.txt').splitlines()
    enableGAMProjectAPIs(GAMProjectAPIs, httpObj, projectId, False)
    setGAMProjectConsentScreen(httpObj, projectId, login_hint)
    iam = getService('iam', httpObj)
    sa_list = gapi.call(iam.projects().serviceAccounts(),
                        'list',
                        name=f'projects/{projectId}')
    service_account = None
    if 'accounts' in sa_list:
        for account in sa_list['accounts']:
            sa_email = f'{projectId}@{projectId}.iam.gserviceaccount.com'
            if sa_email in account['name']:
                service_account = account
                break
    if not service_account:
        print('Creating Service Account')
        service_account = gapi.call(iam.projects().serviceAccounts(),
                                    'create',
                                    name=f'projects/{projectId}',
                                    body={
                                        'accountId': projectId,
                                        'serviceAccount': {
                                            'displayName': 'GAM Project'
                                        }
                                    })
        GM_Globals[GM_OAUTH2SERVICE_ACCOUNT_CLIENT_ID] = service_account[
            'uniqueId']
    sa_email = service_account['name'].rsplit('/', 1)[-1]
    doCreateOrRotateServiceAccountKeys(iam,
                                       project_id=service_account['projectId'],
                                       client_email=service_account['email'],
                                       client_id=service_account['uniqueId'])
    _grantRotateRights(iam, sa_email, sa_email)
    console_url = f'https://console.cloud.google.com/apis/credentials/oauthclient?project={projectId}'
    while True:
        print(f'''Please go to:

{console_url}

1. Choose "Desktop App" or "Other" for "Application type".
2. Enter a desired value for "Name" or leave as is.
3. Click the blue "Create" button.
4. Copy the "client ID" value that shows on the next page.

''')
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
        simplehttp = transport.create_http()
        client_valid = _checkClientAndSecret(simplehttp, client_id,
                                             client_secret)
        if client_valid:
            break
        print()
    cs_data = f'''{{
    "installed": {{
        "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
        "auth_uri": "https://accounts.google.com/o/oauth2/v2/auth",
        "client_id": "{client_id}",
        "client_secret": "{client_secret}",
        "created_by": "{login_hint}",
        "project_id": "{projectId}",
        "redirect_uris": ["http://localhost", "urn:ietf:wg:oauth:2.0:oob"],
        "token_uri": "https://oauth2.googleapis.com/token"
    }}
}}'''
    fileutils.write_file(GC_Values[GC_CLIENT_SECRETS_JSON],
                         cs_data,
                         continue_on_error=False)
    print('That\'s it! Your GAM Project is created and ready to use.')


VALIDEMAIL_PATTERN = re.compile(r'^[^@]+@[^@]+\.[^@]+$')


def _getValidateLoginHint(login_hint=None):
    while True:
        if not login_hint:
            login_hint = input(
                '\nWhat is your Google Workspace admin email address? ').strip()
        if login_hint.find('@') == -1 and GC_Values[GC_DOMAIN]:
            login_hint = f'{login_hint}@{GC_Values[GC_DOMAIN].lower()}'
        if VALIDEMAIL_PATTERN.match(login_hint):
            return login_hint
        print(f'{ERROR_PREFIX}Invalid email address: {login_hint}')
        login_hint = None


def _getCurrentProjectID():
    cs_data = fileutils.read_file(GC_Values[GC_CLIENT_SECRETS_JSON],
                                  continue_on_error=True,
                                  display_errors=True)
    if not cs_data:
        controlflow.system_error_exit(
            14,
            f'Your client secrets file:\n\n{GC_Values[GC_CLIENT_SECRETS_JSON]}\n\nis missing. Please recreate the file.'
        )
    try:
        return json.loads(cs_data)['installed']['project_id']
    except (ValueError, IndexError, KeyError):
        controlflow.system_error_exit(
            3,
            f'The format of your client secrets file:\n\n{GC_Values[GC_CLIENT_SECRETS_JSON]}\n\nis incorrect. Please recreate the file.'
        )


def _getProjects(crm, pfilter):
    try:
        return gapi.get_all_pages(
            crm.projects(),
            'search',
            'projects',
            throw_reasons=[gapi_errors.ErrorReason.BAD_REQUEST],
            query=pfilter)
    except gapi_errors.GapiBadRequestError as e:
        controlflow.system_error_exit(2, f'Project: {pfilter}, {str(e)}')


PROJECTID_PATTERN = re.compile(r'^[a-z][a-z0-9-]{4,28}[a-z0-9]$')
PROJECTID_FORMAT_REQUIRED = '[a-z][a-z0-9-]{4,28}[a-z0-9]'


def _getLoginHintProjectId(createCmd):
    login_hint = None
    projectId = None
    parent = None
    if len(sys.argv) >= 4 and sys.argv[3].lower() not in [
            'admin', 'project', 'parent'
    ]:
        # legacy "gam create/use project <email> <project-id>
        try:
            login_hint = sys.argv[3]
            projectId = sys.argv[4]
        except IndexError:
            pass
    else:
        i = 3
        while i < len(sys.argv):
            myarg = sys.argv[i].lower().replace('_', '')
            if myarg == 'admin':
                login_hint = sys.argv[i + 1]
                i += 2
            elif myarg == 'project':
                projectId = sys.argv[i + 1]
                i += 2
            elif createCmd and myarg == 'parent':
                parent = sys.argv[i + 1]
                i += 2
            else:
                expected = ['admin', 'project']
                if createCmd:
                    expected.append('parent')
                controlflow.system_error_exit(
                    3,
                    f'{myarg} is not a valid argument for "gam {["use", "create"][createCmd]} project", expected one of: {", ".join(expected)}'
                )
    login_hint = _getValidateLoginHint(login_hint)
    if projectId:
        if not PROJECTID_PATTERN.match(projectId):
            controlflow.system_error_exit(
                2,
                f'Invalid Project ID: {projectId}, expected <{PROJECTID_FORMAT_REQUIRED}>'
            )
    elif createCmd:
        projectId = 'gam-project'
        for _ in range(3):
            projectId += f'-{"".join(random.choice(LOWERNUMERIC_CHARS) for _ in range(3))}'
    else:
        projectId = input('\nWhat is your API project ID? ').strip()
        if not PROJECTID_PATTERN.match(projectId):
            controlflow.system_error_exit(
                2,
                f'Invalid Project ID: {projectId}, expected <{PROJECTID_FORMAT_REQUIRED}>'
            )
    crm, httpObj = getCRMService(login_hint)
    if parent and not parent.startswith('organizations/') and not parent.startswith('folders/'):
        parent = convertGCPFolderNameToID(parent, crm)
    projects = _getProjects(crm, f'id:{projectId}')
    if not createCmd:
        if not projects:
            controlflow.system_error_exit(
                2,
                f'User: {login_hint}, Project ID: {projectId}, Does not exist')
        if projects[0]['state'] != 'ACTIVE':
            controlflow.system_error_exit(
                2, f'User: {login_hint}, Project ID: {projectId}, Not active')
    else:
        if projects:
            controlflow.system_error_exit(
                2, f'User: {login_hint}, Project ID: {projectId}, Duplicate')
    return (crm, httpObj, login_hint, projectId, parent)


PROJECTID_FILTER_REQUIRED = 'gam|<ProjectID>|(filter <String>)'


def convertGCPFolderNameToID(parent, crm):
    folders = gapi.get_all_pages(crm.folders(),
                                 'search',
                                 'folders',
                                 query=f'displayName="{parent}"')
    if not folders:
        controlflow.system_error_exit(
            1, f'ERROR: No folder found matching displayName={parent}')
    if len(folders) > 1:
        print('Multiple matches:')
        for folder in folders:
            print(f'  Name: {folder["name"]}  ID: {folder["displayName"]}')
        controlflow.system_error_exit(
            2, 'ERROR: Multiple matching folders, please specify one.')
    return folders[0]['name']


def createGCPFolder():
    displayName = sys.argv[3]
    login_hint = _getValidateLoginHint()
    login_domain = login_hint.split('@')[-1]
    crm, _ = getCRMService(login_hint)
    organization = getGCPOrg(crm, login_domain)
    result = gapi.call(crm.folders(), 'create',
                       body={'parent': organization, 'displayName': displayName})
    print(f'User: {login_hint}, Folder: {displayName}, GCP Folder Name: {result["name"]}, Created')


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
        pfilter = f'id:{pfilter}'
    else:
        controlflow.system_error_exit(
            2,
            f'Invalid Project ID: {pfilter}, expected <{["", "all|"][printShowCmd]}{PROJECTID_FILTER_REQUIRED}>'
        )
    login_hint = _getValidateLoginHint(login_hint)
    crm, httpObj = getCRMService(login_hint)
    if pfilter in ['current', 'id:current']:
        projectID = _getCurrentProjectID()
        if not printShowCmd:
            projects = [{'projectId': projectID}]
        else:
            projects = _getProjects(crm, f'id:{projectID}')
    else:
        projects = _getProjects(crm, pfilter)
    return (crm, httpObj, login_hint, projects, i)


def _checkForExistingProjectFiles():
    for a_file in [
            GC_Values[GC_OAUTH2SERVICE_JSON], GC_Values[GC_CLIENT_SECRETS_JSON]
    ]:
        if os.path.exists(a_file):
            controlflow.system_error_exit(
                5,
                f'{a_file} already exists. Please delete or rename it before attempting to use another project.'
            )


def getGCPOrg(crm, domain):
    resp = gapi.call(crm.organizations(),
                     'search',
                     query=f'domain:{domain}')
    try:
        organization = resp['organizations'][0]['name']
        print(f'Your organization name is {organization}')
        return organization
    except (KeyError, IndexError):
        controlflow.system_error_exit(
             3,
            'you have no rights to create projects for your organization and you don\'t seem to be a super admin! Sorry, there\'s nothing more I can do.'
            )


def doCreateProject():
    _checkForExistingProjectFiles()
    crm, httpObj, login_hint, projectId, parent = _getLoginHintProjectId(True)
    login_domain = login_hint[login_hint.find('@') + 1:]
    body = {'projectId': projectId, 'displayName': 'GAM Project'}
    if parent:
        body['parent'] = parent
    while True:
        create_again = False
        print(f'Creating project "{body["displayName"]}"...')
        create_operation = gapi.call(crm.projects(), 'create', body=body)
        operation_name = create_operation['name']
        time.sleep(8)  # Google recommends always waiting at least 5 seconds
        for i in range(1, 5):
            print('Checking project status...')
            status = gapi.call(crm.operations(), 'get', name=operation_name)
            if 'error' in status:
                if status['error'].get(
                        'message', ''
                ) == 'No permission to create project in organization':
                    print(
                        'Hmm... Looks like you have no rights to your Google Cloud Organization.'
                    )
                    print('Attempting to fix that...')
                    organization = getGCPOrg(crm, login_domain)
                    org_policy = gapi.call(crm.organizations(),
                                           'getIamPolicy',
                                           resource=organization)
                    if 'bindings' not in org_policy:
                        org_policy['bindings'] = []
                        print(
                            'Looks like no one has rights to your Google Cloud Organization. Attempting to give you create rights...'
                        )
                    else:
                        print('The following rights seem to exist:')
                        for a_policy in org_policy['bindings']:
                            if 'role' in a_policy:
                                print(f' Role: {a_policy["role"]}')
                            if 'members' in a_policy:
                                print(' Members:')
                                for member in a_policy['members']:
                                    print(f'  {member}')
                            print()
                    my_role = 'roles/resourcemanager.projectCreator'
                    print(f'Giving {login_hint} the role of {my_role}...')
                    org_policy['bindings'].append({
                        'role': my_role,
                        'members': [f'user:{login_hint}']
                    })
                    gapi.call(crm.organizations(),
                              'setIamPolicy',
                              resource=organization,
                              body={'policy': org_policy})
                    create_again = True
                    break
                try:
                    if status['error']['details'][0]['violations'][0][
                            'description'] == 'Callers must accept Terms of Service':
                        print('''Please go to:

https://console.cloud.google.com/start

and accept the Terms of Service (ToS). As soon as you've accepted the ToS popup, you can return here and press enter.'''
                             )
                        input()
                        create_again = True
                        break
                except (IndexError, KeyError):
                    pass
                controlflow.system_error_exit(1, status)
            if status.get('done', False):
                break
            sleep_time = i**2
            print(f'Project still being created. Sleeping {sleep_time} seconds')
            time.sleep(sleep_time)
        if create_again:
            continue
        if not status.get('done', False):
            controlflow.system_error_exit(
                1, f'Failed to create project: {status}')
        elif 'error' in status:
            controlflow.system_error_exit(2, status['error'])
        break
    _createClientSecretsOauth2service(httpObj, projectId, login_hint)


def doUseProject():
    _checkForExistingProjectFiles()
    _, httpObj, login_hint, projectId, _ = _getLoginHintProjectId(False)
    _createClientSecretsOauth2service(httpObj, projectId, login_hint)


def doUpdateProjects():
    _, httpObj, login_hint, projects, _ = _getLoginHintProjects(False)
    GAMProjectAPIs = getGAMProjectFile('project-apis.txt').splitlines()
    count = len(projects)
    print(f'User: {login_hint}, Update {count} Projects')
    i = 0
    for project in projects:
        i += 1
        projectId = project['projectId']
        enableGAMProjectAPIs(GAMProjectAPIs, httpObj, projectId, True, i, count)
        iam = getService('iam', httpObj)
        _getSvcAcctData()  # needed to read in GM_OAUTH2SERVICE_JSON_DATA
        sa_email = GM_Globals[GM_OAUTH2SERVICE_JSON_DATA]['client_email']
        _grantRotateRights(iam, sa_email, sa_email)


def _generatePrivateKeyAndPublicCert(client_id, key_size):
    print(' Generating new private key...')
    private_key = rsa.generate_private_key(public_exponent=65537,
                                           key_size=key_size,
                                           backend=default_backend())
    private_pem = private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption()).decode()
    print(' Extracting public certificate...')
    public_key = private_key.public_key()
    builder = x509.CertificateBuilder()
    builder = builder.subject_name(
        x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, client_id)]))
    builder = builder.issuer_name(
        x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, client_id)]))
    builder = builder.not_valid_before(datetime.datetime.today())
    # Google uses 12/31/9999 date for end time
    builder = builder.not_valid_after(datetime.datetime(9999, 12, 31, 23, 59))
    builder = builder.serial_number(x509.random_serial_number())
    builder = builder.public_key(public_key)
    builder = builder.add_extension(x509.BasicConstraints(ca=False,
                                                          path_length=None),
                                    critical=True)
    builder = builder.add_extension(x509.KeyUsage(key_cert_sign=False,
                                                  crl_sign=False,
                                                  digital_signature=True,
                                                  content_commitment=False,
                                                  key_encipherment=False,
                                                  data_encipherment=False,
                                                  key_agreement=False,
                                                  encipher_only=False,
                                                  decipher_only=False),
                                    critical=True)
    builder = builder.add_extension(x509.ExtendedKeyUsage(
        [x509.oid.ExtendedKeyUsageOID.SERVER_AUTH]),
                                    critical=True)
    certificate = builder.sign(private_key=private_key,
                               algorithm=hashes.SHA256(),
                               backend=default_backend())
    public_cert_pem = certificate.public_bytes(
        serialization.Encoding.PEM).decode()
    publicKeyData = base64.b64encode(public_cert_pem.encode())
    if isinstance(publicKeyData, bytes):
        publicKeyData = publicKeyData.decode()
    print(' Done generating private key and public certificate.')
    return private_pem, publicKeyData


def _formatOAuth2ServiceData(service_data):
    quoted_email = quote(service_data.get('client_email', ''))
    service_data['auth_provider_x509_cert_url'] = 'https://www.googleapis.com/oauth2/v1/certs'
    service_data['auth_uri'] = 'https://accounts.google.com/o/oauth2/auth'
    service_data['client_x509_cert_url'] = f'https://www.googleapis.com/robot/v1/metadata/x509/{quoted_email}'
    service_data['token_uri'] = 'https://oauth2.googleapis.com/token'
    service_data['type'] = 'service_account'
    return json.dumps(service_data, indent=2, sort_keys=True)


def doShowServiceAccountKeys():
    iam = buildGAPIServiceObject('iam', None)
    keyTypes = None
    i = 3
    while i < len(sys.argv):
        myarg = sys.argv[i].lower().replace('_', '')
        if myarg == 'all':
            keyTypes = None
            i += 1
        elif myarg in ['system', 'systemmanaged']:
            keyTypes = 'SYSTEM_MANAGED'
            i += 1
        elif myarg in ['user', 'usermanaged']:
            keyTypes = 'USER_MANAGED'
            i += 1
        else:
            controlflow.invalid_argument_exit(myarg, 'gam show sakeys')
    name = f'projects/-/serviceAccounts/{GM_Globals[GM_OAUTH2SERVICE_ACCOUNT_CLIENT_ID]}'
    currentPrivateKeyId = GM_Globals[GM_OAUTH2SERVICE_JSON_DATA][
        'private_key_id']
    keys = gapi.get_items(iam.projects().serviceAccounts().keys(),
                          'list',
                          'keys',
                          name=name,
                          keyTypes=keyTypes)
    if not keys:
        print('No keys')
        return
    parts = keys[0]['name'].rsplit('/')
    for i in range(0, 4, 2):
        print(f'{parts[i][:-1]}: {parts[i+1]}')
    for key in keys:
        key['name'] = key['name'].rsplit('/', 1)[-1]
        if key['name'] == currentPrivateKeyId:
            key['usedToAuthenticateThisRequest'] = True
    display.print_json(keys)


def doCreateOrRotateServiceAccountKeys(iam=None,
                                       project_id=None,
                                       client_email=None,
                                       client_id=None):
    local_key_size = 2048
    mode = 'retainexisting'
    body = {}
    if iam:
        new_data = {
                'client_email': client_email,
                'project_id': project_id,
                'client_id': client_id,
                'key_type': 'default'
                }
    else:
        _getSvcAcctData()
        # dict() ensures we have a real copy, not pointer
        new_data = dict(GM_Globals[GM_OAUTH2SERVICE_JSON_DATA])
        oldPrivateKeyId = new_data.get('private_key_id')
        # assume default key type unless we are told otherwise
        new_data['key_type'] = 'default'
        mode = 'retainnone'
        i = 3
        iam = buildGAPIServiceObject('iam', None)
        while i < len(sys.argv):
            myarg = sys.argv[i].lower().replace('_', '')
            if myarg == 'algorithm':
                body['keyAlgorithm'] = sys.argv[i + 1].upper()
                allowed_algorithms = gapi.get_enum_values_minus_unspecified(
                    iam._rootDesc['schemas']['CreateServiceAccountKeyRequest']
                    ['properties']['keyAlgorithm']['enum'])
                if body['keyAlgorithm'] not in allowed_algorithms:
                    controlflow.expected_argument_exit(
                        'algorithm', ', '.join(allowed_algorithms),
                        body['keyAlgorithm'])
                local_key_size = 0
                i += 2
            elif myarg == 'localkeysize':
                local_key_size = int(sys.argv[i + 1])
                if local_key_size not in [1024, 2048, 4096]:
                    controlflow.system_error_exit(
                        3,
                        'localkeysize must be 1024, 2048 or 4096. 1024 is weak and dangerous. 2048 is recommended. 4096 is slow.'
                    )
                i += 2
            elif myarg == 'yubikey':
                new_data['key_type'] = 'yubikey'
                i += 1
            elif myarg == 'yubikeyslot':
                new_data['yubikey_slot'] = sys.argv[i+1].upper()
                i += 2
            elif myarg == 'yubikeypin':
                new_data['yubikey_pin'] = input('Enter your YubiKey PIN: ')
                i += 1
            elif myarg == 'yubikeyserialnumber':
                try:
                    new_data['yubikey_serial_number'] = int(sys.argv[i+1])
                except ValueError:
                    controlflow.system_error_exit(
                            3,
                            'yubikey_serial_number must be a number')
                i += 2
            elif myarg in ['retainnone', 'retainexisting', 'replacecurrent']:
                mode = myarg
                i += 1
            else:
                controlflow.invalid_argument_exit(myarg, 'gam rotate sakeys')
    sa_name = f'projects/-/serviceAccounts/{new_data["client_id"]}'
    if new_data.get('key_type') == 'yubikey':
        # Use yubikey private key
        new_data['yubikey_key_type'] = f'RSA{local_key_size}'
        new_data.pop('private_key', None)
        yk = yubikey.YubiKey(new_data)
        if 'yubikey_serial_number' not in new_data:
            new_data['yubikey_serial_number'] = yk.get_serial_number()
        if 'yubikey_slot' not in new_data:
            new_data['yubikey_slot'] = 'AUTHENTICATION'
        publicKeyData = yk.get_certificate()
    elif local_key_size:
        # Generate private key locally, store in file
        new_data['private_key'], publicKeyData = _generatePrivateKeyAndPublicCert(
            sa_name, local_key_size)
        new_data['key_type'] = 'default'
        for key in list(new_data):
            if key.startswith('yubikey_'):
                new_data.pop(key, None)
    if local_key_size:
        # Upload public cert for yubikey or local generated
        print(' Uploading new public certificate to Google...')
        throw_reasons = [
                gapi_errors.ErrorReason.FOUR_O_O,
                gapi_errors.ErrorReason.NOT_FOUND
                ]
        max_retries = 10
        for i in range(1, max_retries + 1):
            try:
                result = gapi.call(
                    iam.projects().serviceAccounts().keys(),
                    'upload',
                    throw_reasons=throw_reasons,
                    retry_reasons=[gapi_errors.ErrorReason.FOUR_O_THREE],
                    name=sa_name,
                    body={'publicKeyData': publicKeyData})
                break
            except googleapiclient.errors.HttpError as err:
                if hasattr(err, 'error_details') and \
                   err.error_details == 'The given public key already exists.':
                    print('WARNING: that key already exists.')
                    result = {'name': oldPrivateKeyId}
                    break
                elif hasattr(err, 'error_details'):
                    controlflow.system_error_exit(
                            4, err.error_details)
                else:
                    controlflow.system_error_exit(
                            4, err)
            except gapi_errors.GapiNotFoundError as e:
                if i == max_retries:
                    raise e
                sleep_time = i * 5
                if i > 3:
                    print(
                        f'Waiting for Service Account creation to complete. Sleeping {sleep_time} seconds\n'
                    )
                time.sleep(sleep_time)
        newPrivateKeyId = result['name'].rsplit('/', 1)[-1]
        new_data['private_key_id'] = newPrivateKeyId
        new_data_str = _formatOAuth2ServiceData(new_data)
    else:
        # Ask Google to generate private key, store locally
        result = gapi.call(iam.projects().serviceAccounts().keys(),
                           'create',
                           name=sa_name,
                           retry_reasons=[gapi_errors.ErrorReason.FOUR_O_THREE],
                           body=body)
        new_data_str = base64.b64decode(
            result['privateKeyData']).decode(UTF8)
        newPrivateKeyId = result['name'].rsplit('/', 1)[-1]
    fileutils.write_file(GC_Values[GC_OAUTH2SERVICE_JSON],
                         new_data_str,
                         continue_on_error=False)
    print(
        f' Wrote new service account data for {newPrivateKeyId} to {GC_Values[GC_OAUTH2SERVICE_JSON]}'
    )
    if mode != 'retainexisting':
        keys = gapi.get_items(iam.projects().serviceAccounts().keys(),
                              'list',
                              'keys',
                              name=sa_name,
                              keyTypes='USER_MANAGED')
        count = len(keys) if mode == 'retainnone' else 1
        print(
            f' Revoking {count} existing key(s) for Service Account {new_data["client_id"]}')
        for key in keys:
            keyName = key['name'].rsplit('/', 1)[-1]
            if (mode == 'retainnone' or keyName == oldPrivateKeyId) and keyName != newPrivateKeyId:
                print(f'  Revoking existing key {keyName} for service account')
                gapi.call(iam.projects().serviceAccounts().keys(),
                          'delete',
                          retry_reasons=[gapi_errors.ErrorReason.FOUR_O_THREE],
                          name=key['name'])
                if mode != 'retainnone':
                    break


def doDeleteServiceAccountKeys():
    iam = buildGAPIServiceObject('iam', None)
    doit = False
    keyList = []
    i = 3
    while i < len(sys.argv):
        myarg = sys.argv[i].lower()
        if myarg == 'doit':
            doit = True
            i += 1
        else:
            keyList.extend(sys.argv[i].replace(',', ' ').split())
            i += 1
    clientId = GM_Globals[GM_OAUTH2SERVICE_ACCOUNT_CLIENT_ID]
    currentPrivateKeyId = GM_Globals[GM_OAUTH2SERVICE_JSON_DATA][
        'private_key_id']
    name = f'projects/-/serviceAccounts/{clientId}'
    keys = gapi.get_items(iam.projects().serviceAccounts().keys(),
                          'list',
                          'keys',
                          name=name,
                          keyTypes='USER_MANAGED')
    print(f' Service Account {clientId} has {len(keys)} existing key(s)')
    for dkeyName in keyList:
        for key in keys:
            keyName = key['name'].rsplit('/', 1)[-1]
            if dkeyName == keyName:
                if keyName == currentPrivateKeyId and not doit:
                    print(
                        f' Current existing key {keyName} for service account not revoked because doit argument not specified '
                    )
                    break
                print(f' Revoking existing key {keyName} for service account')
                gapi.call(iam.projects().serviceAccounts().keys(),
                          'delete',
                          name=key['name'])
                break
        else:
            print(f' Existing key {dkeyName} for service account not found')


def doDelProjects():
    crm, _, login_hint, projects, _ = _getLoginHintProjects(False)
    count = len(projects)
    print(f'User: {login_hint}, Delete {count} Projects')
    i = 0
    for project in projects:
        i += 1
        projectId = project['projectId']
        try:
            gapi.call(crm.projects(),
                      'delete',
                      throw_reasons=[gapi_errors.ErrorReason.FORBIDDEN],
                      name=project['name'])
            print(f'  Project: {projectId} Deleted{currentCount(i, count)}')
        except gapi_errors.GapiForbiddenError as e:
            print(
                f'  Project: {projectId} Delete Failed: {str(e)}{currentCount(i, count)}'
            )


def doPrintShowProjects(csvFormat):
    _, _, login_hint, projects, i = _getLoginHintProjects(True)
    if csvFormat:
        csvRows = []
        todrive = False
        titles = [
            'User', 'projectId', 'name', 'displayName',
            'createTime', 'updateTime', 'deleteTime',
            'state'
        ]
    while i < len(sys.argv):
        myarg = sys.argv[i].lower()
        if csvFormat and myarg == 'todrive':
            todrive = True
            i += 1
        else:
            controlflow.invalid_argument_exit(
                myarg, f"gam {['show', 'print'][csvFormat]} projects")
    if not csvFormat:
        count = len(projects)
        print(f'User: {login_hint}, Show {count} Projects')
        i = 0
        for project in projects:
            i += 1
            print(f'  Project: {project["projectId"]}{currentCount(i, count)}')
            print(f'    name: {project["name"]}')
            print(f'    displayName: {project["displayName"]}')
            for field in ['createTime', 'updateTime', 'deleteTime']:
                if field in project:
                    print(f'    {field}: {project[field]}')
            print(f'    state: {project["state"]}')
            jcount = len(project.get('labels', []))
            if jcount > 0:
                print('    labels:')
                for k, v in list(project['labels'].items()):
                    print(f'      {k}: {v}')
            if 'parent' in project:
                print(f'    parent: {project["parent"]}')
    else:
        for project in projects:
            display.add_row_titles_to_csv_file(
                utils.flatten_json(project, flattened={'User': login_hint}),
                csvRows, titles)
        display.write_csv_file(csvRows, titles, 'Projects', todrive)


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
            controlflow.invalid_argument_exit(myarg,
                                              'gam <users> show teamdrive')
    for user in users:
        drive = buildGAPIServiceObject('drive3', user)
        if not drive:
            print(f'Failed to access Drive as {user}')
            continue
        result = gapi.call(drive.drives(),
                           'get',
                           driveId=teamDriveId,
                           useDomainAdminAccess=useDomainAdminAccess,
                           fields='*')
        display.print_json(result)


def doCreateTeamDrive(users):
    body = {'name': sys.argv[5]}
    i = 6
    while i < len(sys.argv):
        myarg = sys.argv[i].lower()
        if myarg == 'theme':
            body['themeId'] = sys.argv[i + 1]
            i += 2
        else:
            controlflow.invalid_argument_exit(sys.argv[i],
                                              'gam <users> create teamdrive')
    for user in users:
        drive = buildGAPIServiceObject('drive3', user)
        if not drive:
            print(f'Failed to access Drive as {user}')
            continue
        requestId = str(uuid.uuid4())
        result = gapi.call(drive.drives(),
                           'create',
                           requestId=requestId,
                           body=body,
                           fields='id')
        print(f'Created Team Drive {body["name"]} with id {result["id"]}')


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
            body['name'] = sys.argv[i + 1]
            i += 2
        elif myarg == 'theme':
            body['themeId'] = sys.argv[i + 1]
            i += 2
        elif myarg == 'customtheme':
            body['backgroundImageFile'] = {
                'id': sys.argv[i + 1],
                'xCoordinate': float(sys.argv[i + 2]),
                'yCoordinate': float(sys.argv[i + 3]),
                'width': float(sys.argv[i + 4])
            }
            i += 5
        elif myarg == 'color':
            body['colorRgb'] = getColor(sys.argv[i + 1])
            i += 2
        elif myarg == 'asadmin':
            useDomainAdminAccess = True
            i += 1
        elif myarg in TEAMDRIVE_RESTRICTIONS_MAP:
            body.setdefault('restrictions', {})
            body['restrictions'][
                TEAMDRIVE_RESTRICTIONS_MAP[myarg]] = getBoolean(
                    sys.argv[i + 1], myarg)
            i += 2
        else:
            controlflow.invalid_argument_exit(sys.argv[i],
                                              'gam <users> update teamdrive')
    if not body:
        controlflow.system_error_exit(
            4, 'nothing to update. Need at least a name argument.')
    for user in users:
        user, drive = buildDrive3GAPIObject(user)
        if not drive:
            continue
        result = gapi.call(drive.drives(),
                           'update',
                           useDomainAdminAccess=useDomainAdminAccess,
                           body=body,
                           driveId=teamDriveId,
                           fields='id',
                           soft_errors=True)
        if not result:
            continue
        print(f'Updated Team Drive {teamDriveId}')


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
            q = sys.argv[i + 1]
            i += 2
        else:
            controlflow.invalid_argument_exit(
                myarg, f"gam {['show', 'print'][csvFormat]} teamdrives")
    tds = []
    titles = []
    for user in users:
        sys.stderr.write(f'Getting Team Drives for {user}\n')
        user, drive = buildDrive3GAPIObject(user)
        if not drive:
            continue
        results = gapi.get_all_pages(drive.drives(),
                                     'list',
                                     'drives',
                                     useDomainAdminAccess=useDomainAdminAccess,
                                     fields='*',
                                     q=q,
                                     soft_errors=True)
        if not results:
            continue
        for td in results:
            td = utils.flatten_json(td)
            for key in td:
                if key not in titles:
                    titles.append(key)
            tds.append(td)
    if csvFormat:
        display.write_csv_file(tds, titles, 'Team Drives', todrive)
    else:
        for td in tds:
            name = td.pop('name')
            my_id = td.pop('id')
            print(f'Name: {name}  ID: {my_id}')
            display.print_json(td)
            print()



def doDeleteTeamDrive(users):
    teamDriveId = sys.argv[5]
    for user in users:
        user, drive = buildDrive3GAPIObject(user)
        if not drive:
            continue
        print(f'Deleting Team Drive {teamDriveId}')
        gapi.call(drive.drives(),
                  'delete',
                  driveId=teamDriveId,
                  soft_errors=True)


def extract_nested_zip(zippedFile, toFolder, spacing=' '):
    """ Extract a zip file including any nested zip files
      Delete the zip file(s) after extraction
  """
    print(f'{spacing}extracting {zippedFile}')
    with zipfile.ZipFile(zippedFile, 'r') as zfile:
        inner_files = zfile.infolist()
        for inner_file in inner_files:
            print(f'{spacing} {inner_file.filename}')
            inner_file_path = zfile.extract(inner_file, toFolder)
            if re.search(r'\.zip$', inner_file.filename):
                extract_nested_zip(inner_file_path,
                                   toFolder,
                                   spacing=spacing + ' ')
    os.remove(zippedFile)


def doCreateUser():
    cd = buildGAPIObject('directory')
    body, verifyNotInvitable = getUserAttributes(3, cd, False)
    if (verifyNotInvitable and
        gapi_cloudidentity_userinvitations.is_invitable_user(body['primaryEmail'])):
        controlflow.system_error_exit(51, f'User not created, {body["primaryEmail"]} is an unmanaged account')
    print(f'Creating account for {body["primaryEmail"]}')
    gapi.call(cd.users(), 'insert', body=body, fields='primaryEmail')


def doCreateAlias():
    cd = buildGAPIObject('directory')
    body = {
        'alias':
            normalizeEmailAddressOrUID(sys.argv[3], noUid=True, noLower=True)
    }
    target_type = sys.argv[4].lower()
    if target_type not in ['user', 'group', 'target']:
        controlflow.expected_argument_exit(
            'target type', ', '.join(['user', 'group', 'target']), target_type)
    targetKey = normalizeEmailAddressOrUID(sys.argv[5])
    if len(sys.argv) > 6:
        myarg = sys.argv[6].lower().replace('_', '')
        if myarg != 'verifynotinvitable':
            controlflow.system_error_exit(
                3,
                f'{myarg} is not a valid argument for "gam create alias"'
                )
        if gapi_cloudidentity_userinvitations.is_invitable_user(body['alias']):
            controlflow.system_error_exit(51, f'Alias not created, {body["alias"]} is an unmanaged account')
    print(f'Creating alias {body["alias"]} for {target_type} {targetKey}')
    if target_type == 'user':
        gapi.call(cd.users().aliases(), 'insert', userKey=targetKey, body=body)
    elif target_type == 'group':
        gapi.call(cd.groups().aliases(),
                  'insert',
                  groupKey=targetKey,
                  body=body)
    elif target_type == 'target':
        try:
            gapi.call(cd.users().aliases(),
                      'insert',
                      throw_reasons=[
                          gapi_errors.ErrorReason.INVALID,
                          gapi_errors.ErrorReason.BAD_REQUEST
                      ],
                      userKey=targetKey,
                      body=body)
        except (gapi_errors.GapiInvalidError, gapi_errors.GapiBadRequestError):
            gapi.call(cd.groups().aliases(),
                      'insert',
                      groupKey=targetKey,
                      body=body)


def doUpdateUser(users, i):
    cd = buildGAPIObject('directory')
    if users is None:
        users = [normalizeEmailAddressOrUID(sys.argv[3])]
    body, verifyNotInvitable = getUserAttributes(i, cd, True)
    vfe = 'primaryEmail' in body and body['primaryEmail'][:4].lower() == 'vfe@'
    for user in users:
        userKey = user
        if vfe:
            user_primary = gapi.call(cd.users(),
                                     'get',
                                     userKey=userKey,
                                     fields='primaryEmail,id')
            userKey = user_primary['id']
            user_primary = user_primary['primaryEmail']
            user_name, user_domain = splitEmailAddress(user_primary)
            body[
                'primaryEmail'] = f'vfe.{user_name}.{random.randint(1, 99999):05d}@{user_domain}'
            body['emails'] = [{
                'type': 'custom',
                'customType': 'former_employee',
                'primary': False,
                'address': user_primary
            }]
        if (verifyNotInvitable and'primaryEmail' in body and
            gapi_cloudidentity_userinvitations.is_invitable_user(body['primaryEmail'])):
            controlflow.system_error_exit(51, f'User {user} not updated, new primaryEmail {body["primaryEmail"]} is an unmanaged account')
        sys.stdout.write(f'updating user {user}...\n')
        if body:
            gapi.call(cd.users(), 'update', userKey=userKey, body=body)


def doRemoveUsersAliases(users):
    cd = buildGAPIObject('directory')
    for user in users:
        user_aliases = gapi.call(cd.users(),
                                 'get',
                                 userKey=user,
                                 fields='aliases,id,primaryEmail')
        user_id = user_aliases['id']
        user_primary = user_aliases['primaryEmail']
        if 'aliases' in user_aliases:
            print(f'{user_primary} has {len(user_aliases["aliases"])} aliases')
            for an_alias in user_aliases['aliases']:
                print(f' removing alias {an_alias} for {user_primary}...')
                gapi.call(cd.users().aliases(),
                          'delete',
                          userKey=user_id,
                          alias=an_alias)
        else:
            print(f'{user_primary} has no aliases')


def doUpdateAlias():
    cd = buildGAPIObject('directory')
    alias = normalizeEmailAddressOrUID(sys.argv[3], noUid=True, noLower=True)
    target_type = sys.argv[4].lower()
    if target_type not in ['user', 'group', 'target']:
        controlflow.expected_argument_exit(
            'target type', ', '.join(['user', 'group', 'target']), target_type)
    target_email = normalizeEmailAddressOrUID(sys.argv[5])
    if len(sys.argv) > 6:
        myarg = sys.argv[6].lower().replace('_', '')
        if myarg != 'verifynotinvitable':
            controlflow.system_error_exit(
                3,
                f'{myarg} is not a valid argument for "gam update alias"'
                )
        if gapi_cloudidentity_userinvitations.is_invitable_user(alias):
            controlflow.system_error_exit(51, f'Alias not updated, {alias} is an unmanaged account')
    try:
        gapi.call(cd.users().aliases(),
                  'delete',
                  throw_reasons=[gapi_errors.ErrorReason.INVALID],
                  userKey=alias,
                  alias=alias)
    except gapi_errors.GapiInvalidError:
        gapi.call(cd.groups().aliases(), 'delete', groupKey=alias, alias=alias)
    if target_type == 'user':
        gapi.call(cd.users().aliases(),
                  'insert',
                  userKey=target_email,
                  body={'alias': alias})
    elif target_type == 'group':
        gapi.call(cd.groups().aliases(),
                  'insert',
                  groupKey=target_email,
                  body={'alias': alias})
    elif target_type == 'target':
        try:
            gapi.call(cd.users().aliases(),
                      'insert',
                      throw_reasons=[gapi_errors.ErrorReason.INVALID],
                      userKey=target_email,
                      body={'alias': alias})
        except gapi_errors.GapiInvalidError:
            gapi.call(cd.groups().aliases(),
                      'insert',
                      groupKey=target_email,
                      body={'alias': alias})
    print(f'updated alias {alias}')


def doWhatIs():
    cd = buildGAPIObject('directory')
    email = normalizeEmailAddressOrUID(sys.argv[2])
    try:
        user_or_alias = gapi.call(cd.users(),
                                  'get',
                                  throw_reasons=[
                                      gapi_errors.ErrorReason.USER_NOT_FOUND,
                                      gapi_errors.ErrorReason.NOT_FOUND,
                                      gapi_errors.ErrorReason.BAD_REQUEST,
                                      gapi_errors.ErrorReason.INVALID
                                  ],
                                  userKey=email,
                                  fields='id,primaryEmail')
        if (user_or_alias['primaryEmail'].lower()
                == email) or (user_or_alias['id'] == email):
            sys.stderr.write(f'{email} is a user\n\n')
            doGetUserInfo(user_email=email)
            return
        sys.stderr.write(f'{email} is a user alias\n\n')
        doGetAliasInfo(alias_email=email)
        return
    except (gapi_errors.GapiUserNotFoundError, gapi_errors.GapiNotFoundError,
            gapi_errors.GapiBadRequestError, gapi_errors.GapiInvalidError):
        sys.stderr.write(f'{email} is not a user...\n')
        sys.stderr.write(f'{email} is not a user alias...\n')
    try:
        group = gapi.call(cd.groups(),
                          'get',
                          throw_reasons=[
                              gapi_errors.ErrorReason.GROUP_NOT_FOUND,
                              gapi_errors.ErrorReason.NOT_FOUND,
                              gapi_errors.ErrorReason.BAD_REQUEST,
                              gapi_errors.ErrorReason.FORBIDDEN
                          ],
                          groupKey=email,
                          fields='id,email')
        if (group['email'].lower() == email) or (group['id'] == email):
            sys.stderr.write(f'{email} is a group\n\n')
            gapi_directory_groups.info(group_name=email)
            return
        sys.stderr.write(f'{email} is a group alias\n\n')
        doGetAliasInfo(alias_email=email)
        return
    except (gapi_errors.GapiGroupNotFoundError, gapi_errors.GapiNotFoundError,
            gapi_errors.GapiBadRequestError, gapi_errors.GapiForbiddenError):
        sys.stderr.write(f'{email} is not a group...\n')
        sys.stderr.write(f'{email} is not a group alias...\n')
    if gapi_cloudidentity_userinvitations.is_invitable_user(email):
        sys.stderr.write(f'{email} is an unmanaged account\n\n')
    else:
        controlflow.system_error_exit(
            1, f'{email} doesn\'t seem to exist!\n\n')


def convertSKU2ProductId(res, sku, customerId):
    results = gapi.call(res.subscriptions(), 'list', customerId=customerId)
    for subscription in results['subscriptions']:
        if sku == subscription['skuId']:
            return subscription['subscriptionId']
    controlflow.system_error_exit(
        3,
        f'could not find subscription for customer {customerId} and SKU {sku}')


def doDeleteResoldSubscription():
    res = buildGAPIObject('reseller')
    customerId = sys.argv[3]
    sku = sys.argv[4]
    deletionType = sys.argv[5]
    subscriptionId = convertSKU2ProductId(res, sku, customerId)
    gapi.call(res.subscriptions(),
              'delete',
              customerId=customerId,
              subscriptionId=subscriptionId,
              deletionType=deletionType)
    print(f'Cancelled {sku} for {customerId}')


def doCreateResoldSubscription():
    res = buildGAPIObject('reseller')
    customerId = sys.argv[3]
    customerAuthToken, body = _getResoldSubscriptionAttr(
        sys.argv[4:], customerId)
    result = gapi.call(res.subscriptions(),
                       'insert',
                       customerId=customerId,
                       customerAuthToken=customerAuthToken,
                       body=body,
                       fields='customerId')
    print('Created subscription:')
    display.print_json(result)


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
            kwargs['body'] = {'renewalType': sys.argv[i + 1].upper()}
            i += 2
        elif myarg in ['seats']:
            function = 'changeSeats'
            kwargs['body'] = {
                'numberOfSeats':
                    getInteger(sys.argv[i + 1], 'numberOfSeats', minVal=0)
            }
            if len(sys.argv) > i + 2 and sys.argv[i + 2].isdigit():
                kwargs['body']['maximumNumberOfSeats'] = getInteger(
                    sys.argv[i + 2], 'maximumNumberOfSeats', minVal=0)
                i += 3
            else:
                i += 2
        elif myarg in ['plan']:
            function = 'changePlan'
            kwargs['body'] = {'planName': sys.argv[i + 1].upper()}
            i += 2
            while i < len(sys.argv):
                planarg = sys.argv[i].lower()
                if planarg == 'seats':
                    kwargs['body']['seats'] = {
                        'numberOfSeats':
                            getInteger(sys.argv[i + 1],
                                       'numberOfSeats',
                                       minVal=0)
                    }
                    if len(sys.argv) > i + 2 and sys.argv[i + 2].isdigit():
                        kwargs['body']['seats'][
                            'maximumNumberOfSeats'] = getInteger(
                                sys.argv[i + 2],
                                'maximumNumberOfSeats',
                                minVal=0)
                        i += 3
                    else:
                        i += 2
                elif planarg in ['purchaseorderid', 'po']:
                    kwargs['body']['purchaseOrderId'] = sys.argv[i + 1]
                    i += 2
                elif planarg in ['dealcode', 'deal']:
                    kwargs['body']['dealCode'] = sys.argv[i + 1]
                    i += 2
                else:
                    controlflow.invalid_argument_exit(
                        planarg, 'gam update resoldsubscription plan')
        else:
            controlflow.invalid_argument_exit(myarg,
                                              'gam update resoldsubscription')
    result = gapi.call(res.subscriptions(),
                       function,
                       customerId=customerId,
                       subscriptionId=subscriptionId,
                       **kwargs)
    print(f'Updated {customerId} SKU {sku} subscription:')
    if result:
        display.print_json(result)


def doGetResoldSubscriptions():
    res = buildGAPIObject('reseller')
    customerId = sys.argv[3]
    customerAuthToken = None
    i = 4
    while i < len(sys.argv):
        myarg = sys.argv[i].lower().replace('_', '')
        if myarg in ['customerauthtoken', 'transfertoken']:
            customerAuthToken = sys.argv[i + 1]
            i += 2
        else:
            controlflow.invalid_argument_exit(myarg,
                                              'gam info resoldsubscriptions')
    result = gapi.call(res.subscriptions(),
                       'list',
                       customerId=customerId,
                       customerAuthToken=customerAuthToken)
    display.print_json(result)


def _getResoldSubscriptionAttr(arg, customerId):
    body = {'plan': {}, 'seats': {}, 'customerId': customerId}
    customerAuthToken = None
    i = 0
    while i < len(arg):
        myarg = arg[i].lower().replace('_', '')
        if myarg in ['deal', 'dealcode']:
            body['dealCode'] = arg[i + 1]
        elif myarg in ['plan', 'planname']:
            body['plan']['planName'] = arg[i + 1].upper()
        elif myarg in ['purchaseorderid', 'po']:
            body['purchaseOrderId'] = arg[i + 1]
        elif myarg in ['seats']:
            body['seats']['numberOfSeats'] = getInteger(arg[i + 1],
                                                        'numberOfSeats',
                                                        minVal=0)
            if len(arg) > i + 2 and arg[i + 2].isdigit():
                body['seats']['maximumNumberOfSeats'] = getInteger(
                    arg[i + 2], 'maximumNumberOfSeats', minVal=0)
                i += 1
        elif myarg in ['sku', 'skuid']:
            _, body['skuId'] = gapi_licensing.getProductAndSKU(arg[i + 1])
        elif myarg in ['customerauthtoken', 'transfertoken']:
            customerAuthToken = arg[i + 1]
        else:
            controlflow.invalid_argument_exit(myarg,
                                              'gam create resoldsubscription')
        i += 2
    return customerAuthToken, body


def doGetResoldCustomer():
    res = buildGAPIObject('reseller')
    customerId = sys.argv[3]
    result = gapi.call(res.customers(), 'get', customerId=customerId)
    display.print_json(result)


def _getResoldCustomerAttr(arg):
    body = {}
    customerAuthToken = None
    i = 0
    while i < len(arg):
        myarg = arg[i].lower().replace('_', '')
        if myarg in ADDRESS_FIELDS_ARGUMENT_MAP:
            body.setdefault('postalAddress', {})
            body['postalAddress'][ADDRESS_FIELDS_ARGUMENT_MAP[myarg]] = arg[i +
                                                                            1]
        elif myarg in ['email', 'alternateemail']:
            body['alternateEmail'] = arg[i + 1]
        elif myarg in ['phone', 'phonenumber']:
            body['phoneNumber'] = arg[i + 1]
        elif myarg in ['customerauthtoken', 'transfertoken']:
            customerAuthToken = arg[i + 1]
        else:
            controlflow.invalid_argument_exit(
                myarg, f'gam {sys.argv[1]} resoldcustomer')
        i += 2
    return customerAuthToken, body


def doUpdateResoldCustomer():
    res = buildGAPIObject('reseller')
    customerId = sys.argv[3]
    customerAuthToken, body = _getResoldCustomerAttr(sys.argv[4:])
    gapi.call(res.customers(),
              'patch',
              customerId=customerId,
              body=body,
              customerAuthToken=customerAuthToken,
              fields='customerId')
    print(f'updated customer {customerId}')


def doCreateResoldCustomer():
    res = buildGAPIObject('reseller')
    customerAuthToken, body = _getResoldCustomerAttr(sys.argv[4:])
    body['customerDomain'] = sys.argv[3]
    result = gapi.call(res.customers(),
                       'insert',
                       body=body,
                       customerAuthToken=customerAuthToken,
                       fields='customerId,customerDomain')
    print(
        f'Created customer {result["customerDomain"]} with id {result["customerId"]}'
    )

def _getValueFromOAuth(field, credentials=None):
    if not credentials:
        credentials = auth.get_admin_credentials()
    return credentials.get_token_value(field)


def _get_admin_email():
    if GC_Values[GC_ADMIN_EMAIL]:
        return GC_Values[GC_ADMIN_EMAIL]
    if GC_Values[GC_ENABLE_DASA]:
        controlflow.system_error_exit(
            3,
            f'Environment variable GA_ADMIN_EMAIL must be set when {GM_Globals[GM_ENABLEDASA_TXT]} is present'
            )
    return _getValueFromOAuth('email')

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
            user_email = _get_admin_email()
    getSchemas = True
    getAliases = True
    getGroups = True
    getCIGroups = False
    getLicenses = True
    projection = 'full'
    customFieldMask = viewType = None
    skus = sorted(SKUS)
    while i < len(sys.argv):
        myarg = sys.argv[i].lower()
        if myarg == 'noaliases':
            getAliases = False
            i += 1
        elif myarg == 'nogroups':
            getGroups = False
            i += 1
        elif myarg == 'grouptree':
            getCIGroups = True
            getGroups = False
            i += 1
        elif myarg in ['nolicenses', 'nolicences']:
            getLicenses = False
            i += 1
        elif myarg in ['sku', 'skus']:
            skus = sys.argv[i + 1].split(',')
            i += 2
        elif myarg == 'noschemas':
            getSchemas = False
            projection = 'basic'
            i += 1
        elif myarg in ['custom', 'schemas']:
            getSchemas = True
            projection = 'custom'
            customFieldMask = sys.argv[i + 1]
            i += 2
        elif myarg == 'userview':
            viewType = 'domain_public'
            getGroups = getLicenses = False
            i += 1
        elif myarg in ['nousers', 'groups']:
            i += 1
        else:
            controlflow.invalid_argument_exit(myarg, 'gam info user')
    user = gapi.call(cd.users(),
                     'get',
                     userKey=user_email,
                     projection=projection,
                     customFieldMask=customFieldMask,
                     viewType=viewType)
    print(f'User: {user["primaryEmail"]}')
    if 'name' in user and 'givenName' in user['name']:
        print(f'First Name: {user["name"]["givenName"]}')
    if 'name' in user and 'familyName' in user['name']:
        print(f'Last Name: {user["name"]["familyName"]}')
    if 'languages' in user:
        up = 'languageCode'
        languages = [row[up] for row in user['languages'] if up in row]
        if languages:
            print(f'Languages: {",".join(languages)}')
        up = 'customLanguage'
        languages = [row[up] for row in user['languages'] if up in row]
        if languages:
            print(f'Custom Languages: {",".join(languages)}')
    if 'isAdmin' in user:
        print(f'Is a Super Admin: {user["isAdmin"]}')
    if 'isDelegatedAdmin' in user:
        print(f'Is Delegated Admin: {user["isDelegatedAdmin"]}')
    if 'isEnrolledIn2Sv' in user:
        print(f'2-step enrolled: {user["isEnrolledIn2Sv"]}')
    if 'isEnforcedIn2Sv' in user:
        print(f'2-step enforced: {user["isEnforcedIn2Sv"]}')
    if 'agreedToTerms' in user:
        print(f'Has Agreed to Terms: {user["agreedToTerms"]}')
    if 'ipWhitelisted' in user:
        print(f'IP Whitelisted: {user["ipWhitelisted"]}')
    if 'suspended' in user:
        print(f'Account Suspended: {user["suspended"]}')
    if 'suspensionReason' in user:
        print(f'Suspension Reason: {user["suspensionReason"]}')
    if 'archived' in user:
        print(f'Is Archived: {user["archived"]}')
    if 'changePasswordAtNextLogin' in user:
        print(f'Must Change Password: {user["changePasswordAtNextLogin"]}')
    if 'id' in user:
        print(f'Google Unique ID: {user["id"]}')
    if 'customerId' in user:
        print(f'Customer ID: {user["customerId"]}')
    if 'isMailboxSetup' in user:
        print(f'Mailbox is setup: {user["isMailboxSetup"]}')
    if 'includeInGlobalAddressList' in user:
        print(f'Included in GAL: {user["includeInGlobalAddressList"]}')
    if 'creationTime' in user:
        print(f'Creation Time: {user["creationTime"]}')
    if 'lastLoginTime' in user:
        if user['lastLoginTime'] == NEVER_TIME:
            print('Last login time: Never')
        else:
            print(f'Last login time: {user["lastLoginTime"]}')
    if 'orgUnitPath' in user:
        print(f'Google Org Unit Path: {user["orgUnitPath"]}')
    if 'thumbnailPhotoUrl' in user:
        print(f'Photo URL: {user["thumbnailPhotoUrl"]}')
    if 'recoveryPhone' in user:
        print(f'Recovery Phone: {user["recoveryPhone"]}')
    if 'recoveryEmail' in user:
        print(f'Recovery Email: {user["recoveryEmail"]}')
    if 'notes' in user:
        print('Notes:')
        notes = user['notes']
        if isinstance(notes, dict):
            contentType = notes.get('contentType', 'text_plain')
            print(f' contentType: {contentType}')
            if contentType == 'text_html':
                print(
                    utils.indentMultiLineText(
                        f' value: {utils.dehtml(notes["value"])}', n=2))
            else:
                print(
                    utils.indentMultiLineText(f' value: {notes["value"]}', n=2))
        else:
            print(utils.indentMultiLineText(f' value: {notes}', n=2))
        print('')
    if 'gender' in user:
        print('Gender')
        gender = user['gender']
        for key in gender:
            if key == 'customGender' and not gender[key]:
                continue
            print(f' {key}: {gender[key]}')
        print('')
    if 'keywords' in user:
        print('Keywords:')
        for keyword in user['keywords']:
            for key in keyword:
                if key == 'customType' and not keyword[key]:
                    continue
                print(f' {key}: {keyword[key]}')
            print('')
    if 'ims' in user:
        print('IMs:')
        for im in user['ims']:
            for key in im:
                print(f' {key}: {im[key]}')
            print('')
    if 'addresses' in user:
        print('Addresses:')
        for address in user['addresses']:
            for key in address:
                if key != 'formatted':
                    print(f' {key}: {address[key]}')
                else:
                    addr = address[key].replace('\n', '\\n')
                    print(f' {key}: {addr}')
            print('')
    if 'organizations' in user:
        print('Organizations:')
        for org in user['organizations']:
            for key in org:
                if key == 'customType' and not org[key]:
                    continue
                print(f' {key}: {org[key]}')
            print('')
    if 'locations' in user:
        print('Locations:')
        for location in user['locations']:
            for key in location:
                if key == 'customType' and not location[key]:
                    continue
                print(f' {key}: {location[key]}')
            print('')
    if 'sshPublicKeys' in user:
        print('SSH Public Keys:')
        for sshkey in user['sshPublicKeys']:
            for key in sshkey:
                print(f' {key}: {sshkey[key]}')
            print('')
    if 'posixAccounts' in user:
        print('Posix Accounts:')
        for posix in user['posixAccounts']:
            for key in posix:
                print(f' {key}: {posix[key]}')
            print('')
    if 'phones' in user:
        print('Phones:')
        for phone in user['phones']:
            for key in phone:
                print(f' {key}: {phone[key]}')
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
                        print(f' type: {an_email[key]}')
                    else:
                        print(f' {key}: {an_email[key]}')
            print('')
    if 'relations' in user:
        print('Relations:')
        for relation in user['relations']:
            for key in relation:
                if key == 'type' and relation[key] == 'custom':
                    continue
                if key == 'customType':
                    print(f' type: {relation[key]}')
                else:
                    print(f' {key}: {relation[key]}')
            print('')
    if 'externalIds' in user:
        print('External IDs:')
        for externalId in user['externalIds']:
            for key in externalId:
                if key == 'type' and externalId[key] == 'custom':
                    continue
                if key == 'customType':
                    print(f' typw: {externalId[key]}')
                else:
                    print(f' {key}: {externalId[key]}')
            print('')
    if 'websites' in user:
        print('Websites:')
        for website in user['websites']:
            for key in website:
                if key == 'type' and website[key] == 'custom':
                    continue
                if key == 'customType':
                    print(f' type: {website[key]}')
                else:
                    print(f' {key}: {website[key]}')
            print('')
    if getSchemas:
        if 'customSchemas' in user:
            print('Custom Schemas:')
            for schema in user['customSchemas']:
                print(f' Schema: {schema}')
                for field in user['customSchemas'][schema]:
                    if isinstance(user['customSchemas'][schema][field], list):
                        print(f'  {field}:')
                        for an_item in user['customSchemas'][schema][field]:
                            print(f'   type: {an_item["type"]}')
                            if an_item['type'] == 'custom':
                                print(
                                    f'    customType: {an_item["customType"]}')
                            print(f'    value: {an_item["value"]}')
                    else:
                        print(
                            f'  {field}: {user["customSchemas"][schema][field]}'
                        )
                print()
    if getAliases:
        if 'aliases' in user:
            print('Email Aliases:')
            for alias in user['aliases']:
                print(f'  {alias}')
        if 'nonEditableAliases' in user:
            print('Non-Editable Aliases:')
            for alias in user['nonEditableAliases']:
                print(f'  {alias}')
    if getGroups:
        throw_reasons = [gapi_errors.ErrorReason.FORBIDDEN]
        kwargs = {}
        if GC_Values[GC_ENABLE_DASA]:
            # Allows groups.list() to function but will limit
            # returned groups to those in same domain as user
            # so only do this for DASA admins
            kwargs['domain'] = GC_Values[GC_DOMAIN]
        try:
            groups = gapi.get_all_pages(
                cd.groups(),
                'list',
                'groups',
                userKey=user_email,
                fields='groups(name,email),nextPageToken',
                throw_reasons=throw_reasons, **kwargs)
            if groups:
                print(f'Groups: ({len(groups)})')
                for group in groups:
                    print(f'   {group["name"]} <{group["email"]}>')
        except gapi.errors.GapiForbiddenError:
            print('No access to show user groups.')
    elif getCIGroups:
        memberships = gapi_cloudidentity_groups.get_membership_graph(user_email)
        print('Group Membership Tree:')
        if memberships:
            group_name_mapping = {}
            group_displayname_mapping = {}
            groups = memberships.get('groups', [])
            for group in groups:
                group_name = group.get('name')
                group_key = group.get('groupKey', {})
                group_email = group_key.get('id', '')
                group_display_name = group.get('displayName', '')
                group_name_mapping[group_name] = group_email
                group_displayname_mapping[group_email] = group_display_name
            edges = []
            seen_group_count = {}
            for adj in memberships.get('adjacencyList', []):
                group_name = adj.get('group', '')
                group_email = group_name_mapping[group_name]
                for edge in adj.get('edges', []):
                    seen_group_count[group_email] = seen_group_count.get(group_email, 0) + 1
                    member_email = edge.get('memberKey', {}).get('id')
                    edges.append((member_email, group_email))
            print_group_map(user_email, group_displayname_mapping, seen_group_count, edges, 3, 'direct')
            if seen_group_count and max(seen_group_count.values()) > 1:
                print()
                print('   * user has multiple direct or inherited memberships in group')
        print()
    if getLicenses:
        print('Licenses:')
        lic = buildGAPIObject('licensing')
        lbatch = lic.new_batch_http_request(callback=user_lic_result)
        user_licenses = []
        for sku in skus:
            productId, skuId = gapi_licensing.getProductAndSKU(sku)
            lbatch.add(lic.licenseAssignments().get(userId=user_email,
                                                    productId=productId,
                                                    skuId=skuId,
                                                    fields='skuId'))
        lbatch.execute()
        for user_license in user_licenses:
            print(f'  {gapi_licensing._formatSKUIdDisplayName(user_license)}')

def print_group_map(parent, group_name_mappings, seen_group_count, edges, spaces, direction):
    for a_parent, a_child in edges:
        if a_parent == parent:
            group_display_name = group_name_mappings[a_child]
            output = f'{" " * spaces}{group_display_name} <{a_child}> ({direction})'
            if seen_group_count[a_child] > 1:
                output += ' *'
            print(output)
            print_group_map(a_child, group_name_mappings, seen_group_count, edges, spaces+2, 'inherited')

def doGetAliasInfo(alias_email=None):
    cd = buildGAPIObject('directory')
    if alias_email is None:
        alias_email = normalizeEmailAddressOrUID(sys.argv[3])
    try:
        result = gapi.call(cd.users(),
                           'get',
                           throw_reasons=[
                               gapi_errors.ErrorReason.INVALID,
                               gapi_errors.ErrorReason.BAD_REQUEST
                           ],
                           userKey=alias_email)
    except (gapi_errors.GapiInvalidError, gapi_errors.GapiBadRequestError):
        result = gapi.call(cd.groups(), 'get', groupKey=alias_email)
    print(f' Alias Email: {alias_email}')
    try:
        if result['primaryEmail'].lower() == alias_email.lower():
            controlflow.system_error_exit(
                3,
                f'{alias_email} is a primary user email address, not an alias.')
        print(f' User Email: {result["primaryEmail"]}')
    except KeyError:
        print(f' Group Email: {result["email"]}')
    print(f' Unique ID: {result["id"]}')


def printBackupCodes(user, codes):
    jcount = len(codes)
    realcount = 0
    for code in codes:
        if 'verificationCode' in code and code['verificationCode']:
            realcount += 1
    print(f'Backup verification codes for {user} ({realcount})')
    print('')
    if jcount > 0:
        j = 0
        for code in codes:
            j += 1
            print(f'{j}. {code["verificationCode"]}')
        print('')


def doGetBackupCodes(users):
    cd = buildGAPIObject('directory')
    for user in users:
        try:
            codes = gapi.get_items(cd.verificationCodes(),
                                   'list',
                                   'items',
                                   throw_reasons=[
                                       gapi_errors.ErrorReason.INVALID_ARGUMENT,
                                       gapi_errors.ErrorReason.INVALID
                                   ],
                                   userKey=user)
        except (gapi_errors.GapiInvalidArgumentError,
                gapi_errors.GapiInvalidError):
            codes = []
        printBackupCodes(user, codes)


def doGenBackupCodes(users):
    cd = buildGAPIObject('directory')
    for user in users:
        gapi.call(cd.verificationCodes(), 'generate', userKey=user)
        codes = gapi.get_items(cd.verificationCodes(),
                               'list',
                               'items',
                               userKey=user)
        printBackupCodes(user, codes)


def doDelBackupCodes(users):
    cd = buildGAPIObject('directory')
    for user in users:
        try:
            gapi.call(cd.verificationCodes(),
                      'invalidate',
                      soft_errors=True,
                      throw_reasons=[gapi_errors.ErrorReason.INVALID],
                      userKey=user)
        except gapi_errors.GapiInvalidError:
            print(f'No 2SV backup codes for {user}')
            continue
        print(f'2SV backup codes for {user} invalidated')


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
            clientId = commonClientIds(sys.argv[i + 1])
            i += 2
        else:
            controlflow.invalid_argument_exit(sys.argv[i],
                                              'gam <users> delete token')
    if not clientId:
        controlflow.system_error_exit(
            3, 'you must specify a clientid for "gam <users> delete token"')
    for user in users:
        try:
            gapi.call(cd.tokens(),
                      'get',
                      throw_reasons=[
                          gapi_errors.ErrorReason.NOT_FOUND,
                          gapi_errors.ErrorReason.RESOURCE_NOT_FOUND
                      ],
                      userKey=user,
                      clientId=clientId)
        except (gapi_errors.GapiNotFoundError,
                gapi_errors.GapiResourceNotFoundError):
            print(f'User {user} did not authorize {clientId}')
            continue
        gapi.call(cd.tokens(), 'delete', userKey=user, clientId=clientId)
        print(f'Deleted token for {user}')


def printShowTokens(i, entityType, users, csvFormat):

    def _showToken(token):
        print(f'  Client ID: {token["clientId"]}')
        for item in token:
            if item not in ['clientId', 'scopes']:
                print(f'    {item}: {token.get(item, "")}')
        item = 'scopes'
        print(f'    {item}:')
        for it in token.get(item, []):
            print(f'      {it}')

    cd = buildGAPIObject('directory')
    if csvFormat:
        todrive = False
        titles = [
            'user', 'clientId', 'displayText', 'anonymous', 'nativeApp',
            'userKey', 'scopes'
        ]
        csvRows = []
    clientId = None
    while i < len(sys.argv):
        myarg = sys.argv[i].lower()
        if csvFormat and myarg == 'todrive':
            todrive = True
            i += 1
        elif myarg == 'clientid':
            clientId = commonClientIds(sys.argv[i + 1])
            i += 2
        elif not entityType:
            entityType = myarg
            users = getUsersToModify(entity_type=entityType,
                                     entity=sys.argv[i + 1],
                                     silent=False)
            i += 2
        else:
            controlflow.invalid_argument_exit(
                myarg, f"gam <users> {['show', 'print'][csvFormat]} tokens")
    if not entityType:
        users = getUsersToModify(entity_type='all',
                                 entity='users',
                                 silent=False)
    fields = ','.join([
        'clientId', 'displayText', 'anonymous', 'nativeApp', 'userKey', 'scopes'
    ])
    i = 0
    count = len(users)
    for user in users:
        i += 1
        try:
            if csvFormat:
                sys.stderr.write(f'Getting Access Tokens for {user}\n')
            if clientId:
                results = [
                    gapi.call(cd.tokens(),
                              'get',
                              throw_reasons=[
                                  gapi_errors.ErrorReason.NOT_FOUND,
                                  gapi_errors.ErrorReason.USER_NOT_FOUND,
                                  gapi_errors.ErrorReason.RESOURCE_NOT_FOUND
                              ],
                              userKey=user,
                              clientId=clientId,
                              fields=fields)
                ]
            else:
                results = gapi.get_items(
                    cd.tokens(),
                    'list',
                    'items',
                    throw_reasons=[gapi_errors.ErrorReason.USER_NOT_FOUND],
                    userKey=user,
                    fields=f'items({fields})')
            jcount = len(results)
            if not csvFormat:
                print(f'User: {user}, Access Tokens{currentCount(i, count)}')
                if jcount == 0:
                    continue
                for token in results:
                    _showToken(token)
            else:
                if jcount == 0:
                    continue
                for token in results:
                    row = {
                        'user': user,
                        'scopes': ' '.join(token.get('scopes', []))
                    }
                    for item in token:
                        if item not in ['scopes']:
                            row[item] = token.get(item, '')
                    csvRows.append(row)
        except (gapi_errors.GapiNotFoundError,
                gapi_errors.GapiUserNotFoundError,
                gapi_errors.GapiResourceNotFoundError):
            pass
    if csvFormat:
        display.write_csv_file(csvRows, titles, 'OAuth Tokens', todrive)


def doDeprovUser(users):
    cd = buildGAPIObject('directory')
    for user in users:
        gapi_directory_asps.delete([user], cd=cd, codeIdList='all')
        print(f'Invalidating 2SV Backup Codes for {user}')
        try:
            gapi.call(cd.verificationCodes(),
                      'invalidate',
                      soft_errors=True,
                      throw_reasons=[gapi_errors.ErrorReason.INVALID],
                      userKey=user)
        except gapi_errors.GapiInvalidError:
            print('No 2SV Backup Codes')
        print(f'Getting tokens for {user}...')
        tokens = gapi.get_items(cd.tokens(),
                                'list',
                                'items',
                                userKey=user,
                                fields='items/clientId')
        jcount = len(tokens)
        if jcount > 0:
            j = 0
            for token in tokens:
                j += 1
                print(f' deleting token {j} of {jcount})')
                gapi.call(cd.tokens(),
                          'delete',
                          userKey=user,
                          clientId=token['clientId'])
        else:
            print('No Tokens')
        print(f'Done deprovisioning {user}')


def doDeleteUser():
    cd = buildGAPIObject('directory')
    user_email = normalizeEmailAddressOrUID(sys.argv[3])
    print(f'Deleting account for {user_email}')
    gapi.call(cd.users(), 'delete', userKey=user_email)


def doUndeleteUser():
    cd = buildGAPIObject('directory')
    user = normalizeEmailAddressOrUID(sys.argv[3])
    orgUnit = '/'
    i = 4
    while i < len(sys.argv):
        myarg = sys.argv[i].lower()
        if myarg in ['ou', 'org']:
            orgUnit = gapi_directory_orgunits.makeOrgUnitPathAbsolute(
                sys.argv[i + 1])
            i += 2
        else:
            controlflow.invalid_argument_exit(sys.argv[i], 'gam undelete user')
    if user.find('@') == -1:
        user_uid = user
    else:
        print(f'Looking up UID for {user}...')
        deleted_users = gapi.get_all_pages(cd.users(),
                                           'list',
                                           'users',
                                           customer=GC_Values[GC_CUSTOMER_ID],
                                           showDeleted=True)
        matching_users = list()
        for deleted_user in deleted_users:
            if str(deleted_user['primaryEmail']).lower() == user:
                matching_users.append(deleted_user)
        if not matching_users:
            controlflow.system_error_exit(
                3, 'could not find deleted user with that address.')
        elif len(matching_users) > 1:
            print(
                f'ERROR: more than one matching deleted {user} user. Please select the correct one to undelete and specify with "gam undelete user uid:<uid>"'
            )
            print('')
            for matching_user in matching_users:
                print(f' uid:{matching_user["id"]} ')
                for attr_name in [
                        'creationTime', 'lastLoginTime', 'deletionTime'
                ]:
                    try:
                        if matching_user[attr_name] == NEVER_TIME:
                            matching_user[attr_name] = 'Never'
                        print(f'   {attr_name}: {matching_user[attr_name]} ')
                    except KeyError:
                        pass
                print()
            sys.exit(3)
        else:
            user_uid = matching_users[0]['id']
    print(f'Undeleting account for {user}')
    gapi.call(cd.users(),
              'undelete',
              userKey=user_uid,
              body={'orgUnitPath': orgUnit})


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
    alias_email = normalizeEmailAddressOrUID(alias_email,
                                             noUid=True,
                                             noLower=True)
    print(f'Deleting alias {alias_email}')
    if is_user or (not is_user and not is_group):
        try:
            gapi.call(cd.users().aliases(),
                      'delete',
                      throw_reasons=[
                          gapi_errors.ErrorReason.INVALID,
                          gapi_errors.ErrorReason.BAD_REQUEST,
                          gapi_errors.ErrorReason.NOT_FOUND
                      ],
                      userKey=alias_email,
                      alias=alias_email)
            return
        except (gapi_errors.GapiInvalidError, gapi_errors.GapiBadRequestError):
            pass
        except gapi_errors.GapiNotFoundError:
            controlflow.system_error_exit(
                4, f'The alias {alias_email} does not exist')
    if not is_user or (not is_user and not is_group):
        gapi.call(cd.groups().aliases(),
                  'delete',
                  groupKey=alias_email,
                  alias=alias_email)


def send_email(subject,
               body,
               recipient=None,
               sender=None,
               user=None,
               method='send',
               labels=None,
               msgHeaders={},
               kwargs={}):
    api_body = {}
    default_sender = default_recipient = False
    if not user:
        user = _get_admin_email()
    userId, gmail = buildGmailGAPIObject(user)
    if not gmail:
        return
    resource = gmail.users().messages()
    if labels:
        api_body['labelIds'] = labelsToLabelIds(gmail, labels)
    if not sender:
        sender = userId
        default_sender = True
    if not recipient:
        recipient = userId
        default_recipient = True
    # Force ASCII for RFC compliance
    # xmlcharref seems to work to display at least
    # some unicode in HTML body and is ignored in
    # plain text body.
    body = body.encode('ascii', 'xmlcharrefreplace').decode()
    msg = message_from_string(body)
    for header, value in msgHeaders.items():
        msg.__delitem__(
            header)  # can remove multiple case-insensitive matching headers
        msg.add_header(header, value)
    if subject:
        msg.__delitem__('Subject')
        msg['Subject'] = subject
    if not default_sender:
        msg.__delitem__('From')
    if not msg['From']:
        msg['From'] = sender
    if not default_recipient:
        msg.__delitem__('to')
    if not msg['To']:
        msg['To'] = recipient
    api_body['raw'] = base64.urlsafe_b64encode(msg.as_bytes()).decode()
    if method == 'draft':
        resource = gmail.users().drafts()
        method = 'create'
        api_body = {'message': api_body}
    elif method in ['insert', 'import']:
        if method == 'import':
            method = 'import_'
    gapi.call(resource, method, userId=userId, body=api_body, **kwargs)


USER_ARGUMENT_TO_PROPERTY_MAP = {
    'address': ['addresses',],
    'addresses': ['addresses',],
    'admin': [
        'isAdmin',
        'isDelegatedAdmin',
    ],
    'agreed2terms': ['agreedToTerms',],
    'agreedtoterms': ['agreedToTerms',],
    'aliases': [
        'aliases',
        'nonEditableAliases',
    ],
    'archived': ['archived',],
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
    'gender': [
        'gender.type',
        'gender.customGender',
        'gender.addressMeAs',
    ],
    'givenname': ['name.givenName',],
    'id': ['id',],
    'im': ['ims',],
    'ims': ['ims',],
    'includeinglobaladdresslist': ['includeInGlobalAddressList',],
    'ipwhitelisted': ['ipWhitelisted',],
    'isadmin': [
        'isAdmin',
        'isDelegatedAdmin',
    ],
    'isdelegatedadmin': [
        'isAdmin',
        'isDelegatedAdmin',
    ],
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
    'name': [
        'name.givenName',
        'name.familyName',
        'name.fullName',
    ],
    'nicknames': [
        'aliases',
        'nonEditableAliases',
    ],
    'noneditablealiases': [
        'aliases',
        'nonEditableAliases',
    ],
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
    'recoveryemail': ['recoveryEmail',],
    'recoveryphone': ['recoveryPhone',],
    'relation': ['relations',],
    'relations': ['relations',],
    'ssh': ['sshPublicKeys',],
    'sshkeys': ['sshPublicKeys',],
    'sshpublickeys': ['sshPublicKeys',],
    'suspended': [
        'suspended',
        'suspensionReason',
    ],
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
    display.add_field_to_csv_file('primaryemail', USER_ARGUMENT_TO_PROPERTY_MAP,
                                  fieldsList, fieldsTitles, titles)
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
            groupDelimiter = licenseDelimiter = sys.argv[i + 1]
            i += 2
        elif myarg == 'sortheaders':
            sortHeaders = True
            i += 1
        elif myarg in ['custom', 'schemas']:
            fieldsList.append('customSchemas')
            if sys.argv[i + 1].lower() == 'all':
                projection = 'full'
            else:
                projection = 'custom'
                customFieldMask = sys.argv[i + 1]
            i += 2
        elif myarg == 'todrive':
            todrive = True
            i += 1
        elif myarg in ['deletedonly', 'onlydeleted']:
            deleted_only = True
            i += 1
        elif myarg == 'orderby':
            orderBy = sys.argv[i + 1]
            validOrderBy = [
                'email', 'familyname', 'givenname', 'firstname', 'lastname'
            ]
            if orderBy.lower() not in validOrderBy:
                controlflow.expected_argument_exit('orderby',
                                                   ', '.join(validOrderBy),
                                                   orderBy)
            if orderBy.lower() in ['familyname', 'lastname']:
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
            domain = sys.argv[i + 1]
            customer = None
            i += 2
        elif myarg in ['query', 'queries']:
            queries = getQueries(myarg, sys.argv[i + 1])
            i += 2
        elif myarg in USER_ARGUMENT_TO_PROPERTY_MAP:
            if not fieldsList:
                fieldsList = [
                    'primaryEmail',
                ]
            display.add_field_to_csv_file(myarg, USER_ARGUMENT_TO_PROPERTY_MAP,
                                          fieldsList, fieldsTitles, titles)
            i += 1
        elif myarg == 'fields':
            if not fieldsList:
                fieldsList = [
                    'primaryEmail',
                ]
            fieldNameList = sys.argv[i + 1]
            for field in fieldNameList.lower().replace(',', ' ').split():
                if field in USER_ARGUMENT_TO_PROPERTY_MAP:
                    display.add_field_to_csv_file(
                        field, USER_ARGUMENT_TO_PROPERTY_MAP, fieldsList,
                        fieldsTitles, titles)
                else:
                    controlflow.invalid_argument_exit(field,
                                                      'gam print users fields')
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
            controlflow.invalid_argument_exit(sys.argv[i], 'gam print users')
    if fieldsList:
        fields = f'nextPageToken,users({",".join(set(fieldsList)).replace(".", "/")})'
    else:
        fields = None
    for query in queries:
        printGettingAllItems('Users', query)
        page_message = gapi.got_total_items_first_last_msg('Users')
        all_users = gapi.get_all_pages(cd.users(),
                                       'list',
                                       'users',
                                       page_message=page_message,
                                       message_attribute='primaryEmail',
                                       customer=customer,
                                       domain=domain,
                                       fields=fields,
                                       showDeleted=deleted_only,
                                       orderBy=orderBy,
                                       sortOrder=sortOrder,
                                       viewType=viewType,
                                       query=query,
                                       projection=projection,
                                       customFieldMask=customFieldMask)
        for user in all_users:
            if email_parts and ('primaryEmail' in user):
                user_email = user['primaryEmail']
                if user_email.find('@') != -1:
                    user['primaryEmailLocal'], user[
                        'primaryEmailDomain'] = splitEmailAddress(user_email)
            display.add_row_titles_to_csv_file(utils.flatten_json(user),
                                               csvRows, titles)
    if sortHeaders:
        display.sort_csv_titles([
            'primaryEmail',
        ], titles)
    if getGroupFeed:
        i = 0
        count = len(csvRows)
        titles.append('Groups')
        for user in csvRows:
            i += 1
            user_email = user['primaryEmail']
            sys.stderr.write(
                f'Getting Group Membership for {user_email}{currentCountNL(i, count)}'
            )
            groups = gapi.get_all_pages(cd.groups(),
                                        'list',
                                        'groups',
                                        userKey=user_email)
            user['Groups'] = groupDelimiter.join(
                [groupname['email'] for groupname in groups])
    if getLicenseFeed:
        titles.append('Licenses')
        licenses = gapi_licensing.print_(returnFields='userId,skuId')
        if licenses:
            for user in csvRows:
                u_licenses = licenses.get(user['primaryEmail'].lower())
                if u_licenses:
                    user['Licenses'] = licenseDelimiter.join(
                        [gapi_licensing._skuIdToDisplayName(skuId) for skuId in u_licenses])
    display.write_csv_file(csvRows, titles, 'Users', todrive)


def doPrintShowAlerts():
    _, ac = buildAlertCenterGAPIObject(_get_admin_email())
    alerts = gapi.get_all_pages(ac.alerts(), 'list', 'alerts')
    titles = []
    csv_rows = []
    for alert in alerts:
        aj = utils.flatten_json(alert)
        for field in aj:
            if field not in titles:
                titles.append(field)
        csv_rows.append(aj)
    display.write_csv_file(csv_rows, titles, 'Alerts', False)


def doPrintShowAlertFeedback():
    _, ac = buildAlertCenterGAPIObject(_get_admin_email())
    feedback = gapi.get_all_pages(ac.alerts().feedback(),
                                  'list',
                                  'feedback',
                                  alertId='-')
    for feedbac in feedback:
        print(feedbac)


def doCreateAlertFeedback():
    _, ac = buildAlertCenterGAPIObject(_get_admin_email())
    valid_types = gapi.get_enum_values_minus_unspecified(
        ac._rootDesc['schemas']['AlertFeedback']['properties']['type']['enum'])
    alertId = sys.argv[3]
    body = {'type': sys.argv[4].upper()}
    if body['type'] not in valid_types:
        controlflow.system_error_exit(
            2,
            f'{body["type"]} is not a valid feedback value, expected one of: {", ".join(valid_types)}'
        )
    gapi.call(ac.alerts().feedback(), 'create', alertId=alertId, body=body)


def doDeleteOrUndeleteAlert(action):
    _, ac = buildAlertCenterGAPIObject(_get_admin_email())
    alertId = sys.argv[3]
    kwargs = {}
    if action == 'undelete':
        kwargs['body'] = {}
    gapi.call(ac.alerts(), action, alertId=alertId, **kwargs)


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
            queries = getQueries(myarg, sys.argv[i + 1])
            doGroups = False
            doUsers = True
            i += 2
        else:
            controlflow.invalid_argument_exit(sys.argv[i], 'gam print aliases')
    if doUsers:
        for query in queries:
            printGettingAllItems('User Aliases', query)
            page_message = gapi.got_total_items_first_last_msg('Users')
            all_users = gapi.get_all_pages(
                cd.users(),
                'list',
                'users',
                page_message=page_message,
                message_attribute='primaryEmail',
                customer=GC_Values[GC_CUSTOMER_ID],
                query=query,
                fields=f'nextPageToken,users({",".join(userFields)})')
            for user in all_users:
                for alias in user.get('aliases', []):
                    csvRows.append({
                        'Alias': alias,
                        'Target': user['primaryEmail'],
                        'TargetType': 'User'
                    })
                for alias in user.get('nonEditableAliases', []):
                    csvRows.append({
                        'NonEditableAlias': alias,
                        'Target': user['primaryEmail'],
                        'TargetType': 'User'
                    })
    if doGroups:
        printGettingAllItems('Group Aliases', None)
        page_message = gapi.got_total_items_first_last_msg('Groups')
        all_groups = gapi.get_all_pages(
            cd.groups(),
            'list',
            'groups',
            page_message=page_message,
            message_attribute='email',
            customer=GC_Values[GC_CUSTOMER_ID],
            fields=f'nextPageToken,groups({",".join(groupFields)})')
        for group in all_groups:
            for alias in group.get('aliases', []):
                csvRows.append({
                    'Alias': alias,
                    'Target': group['email'],
                    'TargetType': 'Group'
                })
            for alias in group.get('nonEditableAliases', []):
                csvRows.append({
                    'NonEditableAlias': alias,
                    'Target': group['email'],
                    'TargetType': 'Group'
                })
    display.write_csv_file(csvRows, titles, 'Aliases', todrive)


def shlexSplitList(entity, dataDelimiter=' ,'):
    lexer = shlex.shlex(entity, posix=True)
    lexer.whitespace = dataDelimiter
    lexer.whitespace_split = True
    return list(lexer)


def shlexSplitListStatus(entity, dataDelimiter=' ,'):
    lexer = shlex.shlex(entity, posix=True)
    lexer.whitespace = dataDelimiter
    lexer.whitespace_split = True
    try:
        return (True, list(lexer))
    except ValueError as e:
        return (False, str(e))


def getQueries(myarg, argstr):
    if myarg == 'query':
        return [argstr]
    return shlexSplitList(argstr)


def _getRoleVerification(memberRoles, fields):
    if memberRoles and memberRoles.find(ROLE_MEMBER) != -1:
        return (set(memberRoles.split(',')), None,
                fields if fields.find('role') != -1 else fields[:-1] + ',role)')
    return (set(), memberRoles, fields)


def getUsersToModify(entity_type=None,
                     entity=None,
                     silent=False,
                     member_type=None,
                     checkSuspended=None,
                     groupUserMembersOnly=True):
    got_uids = False
    if entity_type is None:
        entity_type = sys.argv[1].lower()
    if entity is None:
        entity = sys.argv[2]
    # avoid building cd for user/users since it
    # unnnecesarily pushes user through admin auth
    if entity_type not in ['user', 'users'] or \
       ('@' not in entity and not GC_Values[GC_DOMAIN]):
        cd = buildGAPIObject('directory')
    if entity_type == 'user':
        users = [entity]
    elif entity_type == 'users':
        users = entity.replace(',', ' ').split()
    elif entity_type in ['group', 'group_ns', 'group_susp', 'group_inde']:
        if entity_type == 'group_ns':
            checkSuspended = False
        elif entity_type == 'group_susp':
            checkSuspended = True
        includeDerivedMembership = entity_type == 'group_inde'
        got_uids = True
        group = entity
        if member_type is None:
            member_type_message = 'all members'
        else:
            member_type_message = f'{member_type.lower()}s'
        group = normalizeEmailAddressOrUID(group)
        page_message = None
        if not silent:
            sys.stderr.write(
                f'Getting {member_type_message} of {group} (may take some time for large groups)...\n'
            )
            page_message = gapi.got_total_items_msg(f'{member_type_message}',
                                                    '...')
        validRoles, listRoles, listFields = _getRoleVerification(
            member_type, 'nextPageToken,members(email,id,type,status)')
        members = gapi.get_all_pages(
            cd.members(),
            'list',
            'members',
            page_message=page_message,
            groupKey=group,
            roles=listRoles,
            includeDerivedMembership=includeDerivedMembership,
            fields=listFields)
        users = []
        for member in members:
            if ((not groupUserMembersOnly and not includeDerivedMembership) or
                (member['type'] == 'USER')
               ) and gapi_directory_groups._checkMemberRoleIsSuspended(
                   member, validRoles, checkSuspended):
                users.append(member.get('email', member['id']))
    elif entity_type in ['cigroup']:
        got_uids = False
        group = entity
        member_fields = ['memberKey']
        if member_type is None:
            member_type_message = 'all members'
        else:
            member_type_message = f'{member_type.lower()}s'
            member_fields.append('roles')
        fields = f'nextPageToken,memberships({",".join(member_fields)})'
        group = normalizeEmailAddressOrUID(group)
        ci = gapi_cloudidentity.build()
        parent = gapi_cloudidentity_groups.group_email_to_id(ci, group)
        page_message = None
        if not silent:
            sys.stderr.write(
                f'Getting {member_type_message} of {group} (may take some time for large groups)...\n'
            )
            page_message = gapi.got_total_items_msg(f'{member_type_message}',
                                                    '...')
        members = gapi.get_all_pages(ci.groups().memberships(),
                                     'list',
                                     'memberships',
                                     page_message=page_message,
                                     parent=parent,
                                     fields=fields)
        if member_type:
            members = gapi_cloudidentity_groups.filter_members_to_roles(
                members, [member_type])
        users = []
        for member in members:
            users.append(member['memberKey']['id'])
    elif entity_type in [
            'ou',
            'org',
            'ou_ns',
            'org_ns',
            'ou_susp',
            'org_susp',
    ]:
        if entity_type in ['ou_ns', 'org_ns']:
            checkSuspended = False
        elif entity_type in ['ou_susp', 'org_susp']:
            checkSuspended = True
        got_uids = True
        ou = gapi_directory_orgunits.makeOrgUnitPathAbsolute(entity)
        users = []
        if ou.startswith('id:'):
            ou = gapi.call(cd.orgunits(),
                           'get',
                           customerId=GC_Values[GC_CUSTOMER_ID],
                           orgUnitPath=ou,
                           fields='orgUnitPath')['orgUnitPath']
        query = gapi_directory_orgunits.orgUnitPathQuery(ou, checkSuspended)
        page_message = None
        if not silent:
            printGettingAllItems('Users', query)
            page_message = gapi.got_total_items_msg('Users', '...')
        members = gapi.get_all_pages(
            cd.users(),
            'list',
            'users',
            page_message=page_message,
            customer=GC_Values[GC_CUSTOMER_ID],
            fields='nextPageToken,users(primaryEmail,orgUnitPath)',
            query=query)
        ou = ou.lower()
        for member in members:
            if ou == member.get('orgUnitPath', '').lower():
                users.append(member['primaryEmail'])
        if not silent:
            sys.stderr.write(f'{len(users)} Users are directly in the OU.\n')
    elif entity_type in [
            'ou_and_children', 'ou_and_child', 'ou_and_children_ns',
            'ou_and_child_ns', 'ou_and_children_susp', 'ou_and_child_susp'
    ]:
        if entity_type in ['ou_and_children_ns', 'ou_and_child_ns']:
            checkSuspended = False
        elif entity_type in ['ou_and_children_susp', 'ou_and_child_susp']:
            checkSuspended = True
        got_uids = True
        ou = gapi_directory_orgunits.makeOrgUnitPathAbsolute(entity)
        users = []
        query = gapi_directory_orgunits.orgUnitPathQuery(ou, checkSuspended)
        page_message = None
        if not silent:
            printGettingAllItems('Users', query)
            page_message = gapi.got_total_items_msg('Users', '...')
        members = gapi.get_all_pages(cd.users(),
                                     'list',
                                     'users',
                                     page_message=page_message,
                                     customer=GC_Values[GC_CUSTOMER_ID],
                                     fields='nextPageToken,users(primaryEmail)',
                                     query=query)
        for member in members:
            users.append(member['primaryEmail'])
        if not silent:
            sys.stderr.write('done.\r\n')
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
            page_message = gapi.got_total_items_msg('Users', '...')
            members = gapi.get_all_pages(
                cd.users(),
                'list',
                'users',
                page_message=page_message,
                customer=GC_Values[GC_CUSTOMER_ID],
                fields='nextPageToken,users(primaryEmail,suspended)',
                query=query)
            for member in members:
                email = member['primaryEmail']
                if (checkSuspended is None or checkSuspended
                        == member['suspended']) and email not in usersSet:
                    usersSet.add(email)
                    users.append(email)
            if not silent:
                sys.stderr.write('done.\r\n')
    elif entity_type in ['license', 'licenses', 'licence', 'licences']:
        users = gapi_licensing.print_(returnFields='userId', skus=entity.split(','))
    elif entity_type in ['file', 'crosfile']:
        users = []
        f = fileutils.open_file(entity, strip_utf_bom=True)
        for row in f:
            user = row.strip()
            if user:
                users.append(user)
        fileutils.close_file(f)
        if entity_type == 'crosfile':
            entity = 'cros'
    elif entity_type in ['csv', 'csvfile', 'croscsv', 'croscsvfile']:
        drive, filenameColumn = os.path.splitdrive(entity)
        if filenameColumn.find(':') == -1:
            controlflow.system_error_exit(
                2, f'Expected {entity_type} FileName:FieldName')
        (filename, column) = filenameColumn.split(':')
        f = fileutils.open_file(drive + filename)
        input_file = csv.DictReader(f, restval='')
        if column not in input_file.fieldnames:
            controlflow.csv_field_error_exit(column, input_file.fieldnames)
        users = []
        for row in input_file:
            user = row[column].strip()
            if user:
                users.append(user)
        fileutils.close_file(f)
        if entity_type in ['croscsv', 'croscsvfile']:
            entity = 'cros'
    elif entity_type in ['courseparticipants', 'teachers', 'students']:
        croom = buildGAPIObject('classroom')
        users = []
        entity = addCourseIdScope(entity)
        if entity_type in ['courseparticipants', 'teachers']:
            page_message = gapi.got_total_items_msg('Teachers', '...')
            teachers = gapi.get_all_pages(croom.courses().teachers(),
                                          'list',
                                          'teachers',
                                          page_message=page_message,
                                          courseId=entity)
            for teacher in teachers:
                email = teacher['profile'].get('emailAddress', None)
                if email:
                    users.append(email)
        if entity_type in ['courseparticipants', 'students']:
            page_message = gapi.got_total_items_msg('Students', '...')
            students = gapi.get_all_pages(croom.courses().students(),
                                          'list',
                                          'students',
                                          page_message=page_message,
                                          courseId=entity)
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
            page_message = gapi.got_total_items_msg('Users', '...')
            all_users = gapi.get_all_pages(
                cd.users(),
                'list',
                'users',
                page_message=page_message,
                customer=GC_Values[GC_CUSTOMER_ID],
                query=query,
                fields='nextPageToken,users(primaryEmail)')
            for member in all_users:
                users.append(member['primaryEmail'])
            if not silent:
                sys.stderr.write(f'done getting {len(users)} Users.\r\n')
        elif entity == 'cros':
            if not silent:
                printGettingAllItems('CrOS Devices', None)
            page_message = gapi.got_total_items_msg('CrOS Devices', '...')
            all_cros = gapi.get_all_pages(
                cd.chromeosdevices(),
                'list',
                'chromeosdevices',
                page_message=page_message,
                customerId=GC_Values[GC_CUSTOMER_ID],
                fields='nextPageToken,chromeosdevices(deviceId)')
            for member in all_cros:
                users.append(member['deviceId'])
            if not silent:
                sys.stderr.write(f'done getting {len(users)} CrOS Devices.\r\n')
        else:
            controlflow.invalid_argument_exit(entity, 'gam all')
    elif entity_type == 'cros':
        users = entity.replace(',', ' ').split()
        entity = 'cros'
    elif entity_type in ['crosquery', 'crosqueries', 'cros_sn']:
        if entity_type == 'cros_sn':
            queries = [f'id:{sn}' for sn in shlexSplitList(entity)]
        elif entity_type == 'crosqueries':
            queries = shlexSplitList(entity)
        else:
            queries = [entity]
        users = []
        usersSet = set()
        for query in queries:
            if not silent:
                printGettingAllItems('CrOS Devices', query)
            page_message = gapi.got_total_items_msg('CrOS Devices', '...')
            members = gapi.get_all_pages(
                cd.chromeosdevices(),
                'list',
                'chromeosdevices',
                page_message=page_message,
                customerId=GC_Values[GC_CUSTOMER_ID],
                fields='nextPageToken,chromeosdevices(deviceId)',
                query=query)
            for member in members:
                deviceId = member['deviceId']
                if deviceId not in usersSet:
                    usersSet.add(deviceId)
                    users.append(deviceId)
            if not silent:
                sys.stderr.write('done.\r\n')
        entity = 'cros'
    else:
        controlflow.invalid_argument_exit(entity_type, 'gam')
    full_users = list()
    if entity != 'cros' and not got_uids:
        for user in users:
            cg = UID_PATTERN.match(user)
            if cg:
                full_users.append(cg.group(1))
            elif user != '*' and user != GC_Values[
                    GC_CUSTOMER_ID] and user.find('@') == -1:
                full_users.append(f'{user}@{GC_Values[GC_DOMAIN]}')
            else:
                full_users.append(user)
    else:
        full_users = users
    return full_users


def OAuthInfo():
    credentials = access_token = id_token = None
    show_secret = False
    i = 3
    while i < len(sys.argv):
        myarg = sys.argv[i].lower().replace('_', '')
        if myarg == 'accesstoken':
            access_token = sys.argv[i + 1]
            i += 2
        elif myarg == 'idtoken':
            id_token = sys.argv[i + 1]
            i += 2
        elif myarg == 'showsecret':
            show_secret = True
            i += 1
        else:
            controlflow.invalid_argument_exit(sys.argv[i], 'gam oauth info')
    if not access_token and not id_token:
        credentials = getValidOauth2TxtCredentials()
        access_token = credentials.token
        print(f'\nOAuth File: {GC_Values[GC_OAUTH2_TXT]}')
    oa2 = buildGAPIObject('oauth2')
    token_info = gapi.call(oa2,
                           'tokeninfo',
                           access_token=access_token,
                           id_token=id_token)
    if 'issued_to' in token_info:
        print(f'Client ID: {token_info["issued_to"]}')
    if credentials is not None and show_secret:
        print(f'Secret: {credentials.client_secret}')
    if 'scope' in token_info:
        scopes = token_info['scope'].split(' ')
        print(f'Scopes ({len(scopes)})')
        for scope in sorted(scopes):
            print(f'  {scope}')
    if 'email' in token_info:
        print(f'Google Workspace Admin: {token_info["email"]}')
    if 'expires_in' in token_info:
        expires = (
            datetime.datetime.now() +
            datetime.timedelta(seconds=token_info['expires_in'])).isoformat()
        print(f'Expires: {expires}')
    for key, value in token_info.items():
        if key not in ['issued_to', 'scope', 'email', 'expires_in']:
            print(f'{key}: {value}')


def doDeleteOAuth():
    credentials = getOauth2TxtStorageCredentials()
    if credentials is None:
        return
    sys.stderr.write('This OAuth token will self-destruct in 3...')
    sys.stderr.flush()
    time.sleep(1)
    sys.stderr.write('2...')
    sys.stderr.flush()
    time.sleep(1)
    sys.stderr.write('1...')
    sys.stderr.flush()
    time.sleep(1)
    sys.stderr.write('boom!\n')
    sys.stderr.flush()
    credentials.revoke()
    credentials.delete()


def createOAuth():
    '''Explicit command line to create OAuth credentials'''
    login_hint = None
    scopes = None
    if len(sys.argv) >= 4 and sys.argv[3].lower() not in [
            'admin', 'scope', 'scopes'
    ]:
        # legacy "gam oauth create/request <email>
        login_hint = sys.argv[3]
    else:
        i = 3
        while i < len(sys.argv):
            myarg = sys.argv[i].lower().replace('_', '')
            if myarg == 'admin':
                login_hint = sys.argv[i + 1]
                i += 2
            elif myarg in ['scope', 'scopes']:
                scopes = sys.argv[i + 1].split(',')
                i += 2
            else:
                controlflow.system_error_exit(
                    3,
                    f'{myarg} is not a valid argument for "gam oauth create"')
    login_hint = _getValidateLoginHint(login_hint)
    doRequestOAuth(login_hint, scopes)


def doRequestOAuth(login_hint=None, scopes=None):
    missing_client_secrets_message = (
        'To use GAM you need to create an API '
        'project. Please run:\n\ngam create project')
    client_secrets_file = GC_Values[GC_CLIENT_SECRETS_JSON]
    invalid_client_secrets_format_message = (
        'The format of your client secrets '
        'file:\n\n%s\n\nis incorrect. '
        'Please recreate the file.' % client_secrets_file)
    stored_creds = getOauth2TxtStorageCredentials()
    if stored_creds and stored_creds.valid:
        print(
            'It looks like you\'ve already authorized GAM. Refusing to overwrite existing file:\n\n%s'
            % stored_creds.filename)
        return

    if scopes is None:
        scopes = getScopesFromUser()
    if scopes is None:
        # There were no scopes selected. Exit cleanly.
        controlflow.system_error_exit(0, '')
    login_hint = _getValidateLoginHint(login_hint)
    # Needs to be set so oauthlib doesn't puke when Google changes our scopes
    os.environ['OAUTHLIB_RELAX_TOKEN_SCOPE'] = 'true'
    try:
        creds = gam.auth.oauth.Credentials.from_client_secrets_file(
            client_secrets_file=client_secrets_file,
            scopes=scopes,
            access_type='offline',
            login_hint=login_hint,
            credentials_file=GC_Values[GC_OAUTH2_TXT],
            use_console_flow=not GC_Values[GC_OAUTH_BROWSER])
        creds.write()
    except gam.auth.oauth.InvalidClientSecretsFileError:
        controlflow.system_error_exit(14, missing_client_secrets_message)
    except gam.auth.oauth.InvalidClientSecretsFileFormatError:
        controlflow.system_error_exit(3, invalid_client_secrets_format_message)


OAUTH2_SCOPES = [
    {
        'name': 'Chrome Browser Cloud Management',
        'subscopes': ['readonly'],
        'scopes': 'https://www.googleapis.com/auth/admin.directory.device.chromebrowsers',
    },
    {
        'name': 'Chrome Management API - read only',
        'subscope': [],
        'scopes': ['https://www.googleapis.com/auth/chrome.management.reports.readonly'],
    },
    {
        'name': 'Chrome Policy API',
        'subscope': ['readonly'],
        'scopes': ['https://www.googleapis.com/auth/chrome.management.policy'],
    },
    {
        'name':
            'Classroom API - counts as 5 scopes',
        'subscopes': [],
        'scopes': [
            'https://www.googleapis.com/auth/classroom.rosters',
            'https://www.googleapis.com/auth/classroom.courses',
            'https://www.googleapis.com/auth/classroom.profile.emails',
            'https://www.googleapis.com/auth/classroom.profile.photos',
            'https://www.googleapis.com/auth/classroom.guardianlinks.students'
        ]
    },
    {
        'name': 'Cloud Identity - Groups',
        'subscopes': ['readonly'],
        'scopes': 'https://www.googleapis.com/auth/cloud-identity.groups'
    },
    {
        'name': 'Cloud Identity - User Invitations',
        'subscopes': ['readonly'],
        'scopes': 'https://www.googleapis.com/auth/cloud-identity.userinvitations',
        'offByDefault': True,
    },
    {
        'name': 'Contact Delegation',
        'subscopes': ['readonly'],
        'scopes': 'https://www.googleapis.com/auth/admin.contact.delegation'
    },
    {
        'name': 'Data Transfer API',
        'subscopes': ['readonly'],
        'scopes': 'https://www.googleapis.com/auth/admin.datatransfer'
    },
    {
        'name': 'Directory API - Chrome OS Devices',
        'subscopes': ['readonly'],
        'scopes':
            'https://www.googleapis.com/auth/admin.directory.device.chromeos'
    },
    {
        'name': 'Directory API - Customers',
        'subscopes': ['readonly'],
        'scopes': 'https://www.googleapis.com/auth/admin.directory.customer'
    },
    {
        'name': 'Directory API - Domains',
        'subscopes': ['readonly'],
        'scopes': 'https://www.googleapis.com/auth/admin.directory.domain'
    },
    {
        'name': 'Directory API - Groups',
        'subscopes': ['readonly'],
        'scopes': 'https://www.googleapis.com/auth/admin.directory.group'
    },
    {
        'name': 'Directory API - Mobile Devices',
        'subscopes': ['readonly', 'action'],
        'scopes':
            'https://www.googleapis.com/auth/admin.directory.device.mobile'
    },
    {
        'name': 'Directory API - Printers',
        'subscopes': ['readonly'],
        # note - currently DASA only but admin credentials should work soon
        'scopes': 'https://www.googleapis.com/auth/admin.chrome.printers'
    },
    {
        'name': 'Directory API - Organizational Units',
        'subscopes': ['readonly'],
        'scopes': 'https://www.googleapis.com/auth/admin.directory.orgunit'
    },
    {
        'name':
            'Directory API - Resource Calendars',
        'subscopes': ['readonly'],
        'scopes':
            'https://www.googleapis.com/auth/admin.directory.resource.calendar'
    },
    {
        'name':
            'Directory API - Roles',
        'subscopes': ['readonly'],
        'scopes':
            'https://www.googleapis.com/auth/admin.directory.rolemanagement'
    },
    {
        'name': 'Directory API - User Schemas',
        'subscopes': ['readonly'],
        'scopes': 'https://www.googleapis.com/auth/admin.directory.userschema'
    },
    {
        'name':
            'Directory API - User Security',
        'subscopes': [],
        'scopes':
            'https://www.googleapis.com/auth/admin.directory.user.security'
    },
    {
        'name': 'Directory API - Users',
        'subscopes': ['readonly'],
        'scopes': 'https://www.googleapis.com/auth/admin.directory.user'
    },
    {
        'name': 'Group Settings API',
        'subscopes': [],
        'scopes': 'https://www.googleapis.com/auth/apps.groups.settings'
    },
    {
        'name': 'License Manager API',
        'subscopes': [],
        'scopes': 'https://www.googleapis.com/auth/apps.licensing'
    },
    {
        'name': 'Pub / Sub API',
        'subscopes': [],
        'offByDefault': True,
        'scopes': 'https://www.googleapis.com/auth/pubsub'
    },
    {
        'name': 'Reports API - Audit Reports',
        'subscopes': [],
        'scopes': 'https://www.googleapis.com/auth/admin.reports.audit.readonly'
    },
    {
        'name': 'Reports API - Usage Reports',
        'subscopes': [],
        'scopes': 'https://www.googleapis.com/auth/admin.reports.usage.readonly'
    },
    {
        'name': 'Reseller API',
        'subscopes': [],
        'offByDefault': True,
        'scopes': 'https://www.googleapis.com/auth/apps.order'
    },
    {
        'name': 'Site Verification API',
        'subscopes': [],
        'scopes': 'https://www.googleapis.com/auth/siteverification'
    },
    {
        'name': 'Vault Matters and Holds API',
        'subscopes': ['readonly'],
        'scopes': 'https://www.googleapis.com/auth/ediscovery'
    },
    {
        'name': 'Cloud Storage (Vault Export - read only)',
        'subscopes': [],
        'scopes': 'https://www.googleapis.com/auth/devstorage.read_only'
    },
    {
        'name': 'User Profile (Email address - read only)',
        'subscopes': [],
        'scopes': 'email',
        'required': True
    },
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
        menu_options = [
            ScopeMenuOption.from_gam_oauth2scope(definition)
            for definition in OAUTH2_SCOPES
        ]
    menu = ScopeSelectionMenu(menu_options)
    try:
        menu.run()
    except ScopeSelectionMenu.UserRequestedExitException:
        controlflow.system_error_exit(0, '')

    return menu.get_selected_scopes()


class ScopeMenuOption():
    """A single GAM API/feature with scopes that can be turned on/off."""

    def __init__(self,
                 oauth_scopes,
                 description,
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
        self.supported_restrictions = (supported_restrictions
                                       if supported_restrictions is not None
                                       else [])
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
            error = f'Scope does not support a {restriction} restriction.'
            if self.supported_restrictions is not None:
                restriction_list = ', '.join(self.supported_restrictions)
                error = error + (
                    f' Supported restrictions are: {restriction_list}')
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
                scope = f'{scope}.{self._restriction}'
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
        return cls(oauth_scopes=scope_list,
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
        selected_scopes = [
            scope for option in self.get_selected_options()
            for scope in option.get_effective_scopes()
        ]
        return list(set(selected_scopes))

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
        return ScopeSelectionMenu._MENU_DISPLAY_TEXT % '\n'.join(
            scope_menu_items)

    @staticmethod
    def _build_scope_menu_item(scope_option, option_number):
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
            f'[{indicator}]',
            f'{option_number:2d})',
            scope_option.description,
        ]

        if scope_option.supported_restrictions:
            restrictions = ' and '.join(scope_option.supported_restrictions)
            item_description.append(f'(supports {restrictions})')

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
        return ('Please enter 0-%d[%s] or %s: ' % (
            len(self._options) - 1,  # Keep the menu options 0-based
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
                colored_error = createRedText(ERROR_PREFIX + error_message +
                                              '\n')
                sys.stdout.write(colored_error)
                error_message = None  # Clear the pending error message

            user_input = input(self.get_prompt_text())
            try:
                prompt_again = self._process_menu_input(user_input)
                if not prompt_again:
                    return
            except ScopeSelectionMenu.MenuChoiceError as e:
                error_message = str(e)

    _SINGLE_SCOPE_CHANGE_REGEX = re.compile(
        r'\s*(?P<scope_number>\d{1,2})\s*(?P<restriction>[a-z]?)',
        re.IGNORECASE)

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
                    f'Invalid scope number "{scope_number}"')
            selected_option = self._options[scope_number]

            # Find the restriction that the user intended to apply.
            if restriction_command != '':
                matching_restrictions = [
                    r for r in selected_option.supported_restrictions
                    if r.startswith(restriction_command)
                ]
                if not matching_restrictions:
                    raise ScopeSelectionMenu.MenuChoiceError(
                        f'Scope "{selected_option.description}" does not support "{restriction_command}" mode!'
                    )
                restriction = matching_restrictions[0]
            else:
                restriction = None
            self._update_option(selected_option, restriction=restriction)

        elif user_input == ScopeSelectionMenu.MENU_CHOICE['SELECT_ALL_SCOPES']:
            for option in self._options:
                self._update_option(option, selected=True)
        elif user_input == ScopeSelectionMenu.MENU_CHOICE[
                'UNSELECT_ALL_SCOPES']:
            for option in self._options:
                # Force-select required options
                self._update_option(option, selected=option.is_required)
        elif user_input == ScopeSelectionMenu.MENU_CHOICE['CONTINUE']:
            return False
        elif user_input == ScopeSelectionMenu.MENU_CHOICE['EXIT']:
            raise ScopeSelectionMenu.UserRequestedExitException()
        else:
            raise ScopeSelectionMenu.MenuChoiceError(
                f'Invalid input "{user_input}"')

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
                f'Scope "{option.description}" is required and cannot be unselected!'
            )
        if selected and not option.is_selected:
            # Make sure we're not about to exceed the maximum number of scopes
            # authorized on a single token.
            num_scopes_to_add = len(option.get_effective_scopes())
            num_selected_scopes = len(self.get_selected_scopes())
            expected_num_scopes = num_scopes_to_add + num_selected_scopes
            if expected_num_scopes > ScopeSelectionMenu.MAXIMUM_NUM_SCOPES:
                raise ScopeSelectionMenu.MenuChoiceError(
                    f'Too many scopes selected ({expected_num_scopes}). Maximum is '
                    f'{ScopeSelectionMenu.MAXIMUM_NUM_SCOPES}.Please remove some scopes '
                    'and try again.')

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
                    f'Scope "{option.description}" does not support {restriction} mode!'
                )


def init_gam_worker(l):
    global mplock
    mplock = l
    signal.signal(signal.SIGINT, signal.SIG_IGN)


def run_batch(items):
    if not items:
        return
    num_worker_threads = min(len(items), GC_Values[GC_NUM_THREADS])
    l = mp_lock()
    pool = mp_pool(num_worker_threads, init_gam_worker, maxtasksperchild=200, initargs=(l,))
    sys.stderr.write(f'Using {num_worker_threads} processes...\n')
    try:
        results = []
        for item in items:
            if item[0] == 'commit-batch':
                sys.stderr.write(
                    'commit-batch - waiting for running processes to finish before proceeding\n'
                )
                pool.close()
                pool.join()
                pool = mp_pool(num_worker_threads, init_gam_worker, maxtasksperchild=200, initargs=(1,))
                sys.stderr.write(
                    'commit-batch - running processes finished, proceeding\n')
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
                print(f'Finished {num_done} of {num_total} processes.')
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
                    subFields[GAM_argvI].append(
                        (fieldName, match.start(), match.end()))
                else:
                    controlflow.csv_field_error_exit(fieldName, fieldNames)
                pos = match.end()
            GAM_argv.append(myarg)
        elif myarg[0] == '~':
            fieldName = myarg[1:]
            if fieldName in fieldNames:
                subFields[GAM_argvI] = [(fieldName, 0, len(myarg))]
                GAM_argv.append(myarg)
            else:
                controlflow.csv_field_error_exit(fieldName, fieldNames)
        else:
            GAM_argv.append(myarg)
        GAM_argvI += 1
        i += 1
    return (GAM_argv, subFields)


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
        if sys.version_info[1] >= 7:
            try:
                sys.stdout.reconfigure(encoding=GC_Values[GC_CHARSET],
                                       errors='backslashreplace')
                sys.stdin.reconfigure(encoding=GC_Values[GC_CHARSET],
                                      errors='backslashreplace')
            except AttributeError:
                pass
        command = sys.argv[1].lower()
        if command == 'batch':
            i = 2
            filename = sys.argv[i]
            i, encoding = getCharSet(i + 1)
            f = fileutils.open_file(filename,
                                    encoding=encoding,
                                    strip_utf_bom=True)
            items = []
            errors = 0
            for line in f:
                try:
                    argv = shlex.split(line)
                except ValueError as e:
                    sys.stderr.write(f'Command: >>>{line.strip()}<<<\n')
                    sys.stderr.write(f'{ERROR_PREFIX}{str(e)}\n')
                    errors += 1
                    continue
                if argv:
                    cmd = argv[0].strip().lower()
                    if (not cmd) or cmd.startswith('#') or (
                        (len(argv) == 1) and (cmd != 'commit-batch')):
                        continue
                    if cmd == 'gam':
                        items.append(argv)
                    elif cmd == 'commit-batch':
                        items.append([cmd])
                    else:
                        sys.stderr.write(f'Command: >>>{line.strip()}<<<\n')
                        sys.stderr.write(
                            f'{ERROR_PREFIX}Invalid: Expected <gam|commit-batch>\n'
                        )
                        errors += 1
            fileutils.close_file(f)
            if errors == 0:
                run_batch(items)
                sys.exit(0)
            else:
                controlflow.system_error_exit(
                    2,
                    f'batch file: {filename}, not processed, {errors} error{["", "s"][errors != 1]}'
                )
        elif command in ['csv', 'csvtest']:
            if httplib2.debuglevel > 0:
                controlflow.system_error_exit(
                    1,
                    'CSV commands are not compatible with debug. Delete debug.gam and try again.'
                )
            i = 2
            filename = sys.argv[i]
            i, encoding = getCharSet(i + 1)
            f = fileutils.open_file(filename, encoding=encoding)
            csvFile = csv.DictReader(f)
            if (i == len(sys.argv)) or (sys.argv[i].lower() !=
                                        'gam') or (i + 1 == len(sys.argv)):
                controlflow.system_error_exit(
                    3,
                    '"gam csv <filename>" must be followed by a full GAM command...'
                )
            i += 1
            GAM_argv, subFields = getSubFields(i, csvFile.fieldnames)
            items = []
            for row in csvFile:
                items.append(['gam'] +
                             processSubFields(GAM_argv, row, subFields))
            fileutils.close_file(f)
            if command == 'csv':
                run_batch(items)
            else:
                print('The CSV file has the following headers:')
                for field in csvFile.fieldnames:
                    print(f'  {field}')
                print()
                num_items = min(len(items), 10)
                print(
                    f'Here are the first {num_items} commands GAM will run (note that quoting may be lost/invalid in this output):\n'
                )
                for i in range(num_items):
                    c = ' '.join([
                        item if (item and (item.find(' ') == -1) and
                                 (item.find(',') == -1) and
                                 (item.find("'") == -1)) else '"' + item + '"'
                        for item in items[i]
                    ])
                    print(f'  {c}')
            sys.exit(0)
        elif command == 'version':
            doGAMVersion()
            sys.exit(0)
        elif command == 'create':
            argument = sys.argv[2].lower()
            if argument == 'user':
                doCreateUser()
            elif argument == 'group':
                gapi_directory_groups.create()
            elif argument == 'cigroup':
                gapi_cloudidentity_groups.create()
            elif argument in ['nickname', 'alias']:
                doCreateAlias()
            elif argument in ['org', 'ou']:
                gapi_directory_orgunits.create()
            elif argument == 'resource':
                gapi_directory_resource.createResourceCalendar()
            elif argument in ['verify', 'verification']:
                gapi_siteverification.create()
            elif argument == 'schema':
                doCreateOrUpdateUserSchema(False)
            elif argument in ['course', 'class']:
                doCreateCourse()
            elif argument in ['transfer', 'datatransfer']:
                doCreateDataTransfer()
            elif argument == 'domain':
                gapi_directory_domains.create()
            elif argument == 'device':
                gapi_cloudidentity_devices.create()
            elif argument in ['domainalias', 'aliasdomain']:
                gapi_directory_domainaliases.create()
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
                gapi_vault.createMatter()
            elif argument in ['hold', 'vaulthold']:
                gapi_vault.createHold()
            elif argument in ['export', 'vaultexport']:
                gapi_vault.createExport()
            elif argument in ['building']:
                gapi_directory_resource.createBuilding()
            elif argument in ['feature']:
                gapi_directory_resource.createFeature()
            elif argument in ['alertfeedback']:
                doCreateAlertFeedback()
            elif argument in ['gcpfolder']:
                createGCPFolder()
            elif argument in ['adminrole']:
                gapi_directory_roles.create()
            elif argument in ['browsertoken', 'browsertokens']:
                gapi_cbcm.createtoken()
            elif argument in ['printer']:
                gapi_directory_printers.create()
            elif argument in ['chatmessage']:
                gapi_chat.create_message()
            else:
                controlflow.invalid_argument_exit(argument, 'gam create')
            sys.exit(0)
        elif command == 'use':
            argument = sys.argv[2].lower()
            if argument in ['project', 'apiproject']:
                doUseProject()
            else:
                controlflow.invalid_argument_exit(argument, 'gam use')
            sys.exit(0)
        elif command == 'update':
            argument = sys.argv[2].lower()
            if argument == 'user':
                doUpdateUser(None, 4)
            elif argument == 'group':
                gapi_directory_groups.update()
            elif argument == 'cigroup':
                gapi_cloudidentity_groups.update()
            elif argument in ['nickname', 'alias']:
                doUpdateAlias()
            elif argument in ['ou', 'org']:
                gapi_directory_orgunits.update()
            elif argument == 'resource':
                gapi_directory_resource.updateResourceCalendar()
            elif argument == 'cros':
                gapi_directory_cros.doUpdateCros()
            elif argument == 'mobile':
                gapi_directory_mobiledevices.update()
            elif argument in ['verify', 'verification']:
                gapi.siteverification.update()
            elif argument in ['schema', 'schemas']:
                doCreateOrUpdateUserSchema(True)
            elif argument in ['course', 'class']:
                doUpdateCourse()
            elif argument == 'domain':
                gapi_directory_domains.update()
            elif argument == 'customer':
                gapi_directory_customer.doUpdateCustomer()
            elif argument in ['resoldcustomer', 'resellercustomer']:
                doUpdateResoldCustomer()
            elif argument in ['resoldsubscription', 'resellersubscription']:
                doUpdateResoldSubscription()
            elif argument in ['matter', 'vaultmatter']:
                gapi_vault.updateMatter()
            elif argument in ['hold', 'vaulthold']:
                gapi_vault.updateHold()
            elif argument in ['project', 'projects', 'apiproject']:
                doUpdateProjects()
            elif argument in ['building']:
                gapi_directory_resource.updateBuilding()
            elif argument in ['feature']:
                gapi_directory_resource.updateFeature()
            elif argument in ['adminrole']:
                gapi_directory_roles.update()
            elif argument == 'deviceuserstate':
                gapi_cloudidentity_devices.update_state()
            elif argument in ['browser', 'browsers']:
                gapi_cbcm.update()
            elif argument == 'chromepolicy':
                gapi_chromepolicy.update_policy()
            elif argument in ['printer']:
                gapi_directory_printers.update()
            elif argument in ['chatmessage']:
                gapi_chat.update_message()
            else:
                controlflow.invalid_argument_exit(argument, 'gam update')
            sys.exit(0)
        elif command == 'info':
            argument = sys.argv[2].lower()
            if argument == 'user':
                doGetUserInfo()
            elif argument == 'group':
                gapi_directory_groups.info()
            elif argument == 'cigroup':
                gapi_cloudidentity_groups.info()
            elif argument == 'member':
                gapi_directory_groups.info_member()
            elif argument == 'cimember':
                gapi_cloudidentity_groups.info_member()
            elif argument in ['nickname', 'alias']:
                doGetAliasInfo()
            elif argument == 'instance':
                gapi_directory_customer.doGetCustomerInfo()
            elif argument in ['org', 'ou']:
                gapi_directory_orgunits.info()
            elif argument == 'resource':
                gapi_directory_resource.getResourceCalendarInfo()
            elif argument == 'cros':
                gapi_directory_cros.doGetCrosInfo()
            elif argument == 'mobile':
                gapi_directory_mobiledevices.info()
            elif argument in ['verify', 'verification']:
                gapi.siteverification.info()
            elif argument in ['schema', 'schemas']:
                doGetUserSchema()
            elif argument in ['course', 'class']:
                doGetCourseInfo()
            elif argument in ['transfer', 'datatransfer']:
                doGetDataTransferInfo()
            elif argument == 'customer':
                gapi_directory_customer.doGetCustomerInfo()
            elif argument == 'domain':
                gapi_directory_domains.info()
            elif argument in ['domainalias', 'aliasdomain']:
                gapi_directory_domainaliases.info()
            elif argument in ['resoldcustomer', 'resellercustomer']:
                doGetResoldCustomer()
            elif argument in ['printer']:
                gapi_directory_printers.info()
            elif argument in [
                    'resoldsubscription', 'resoldsubscriptions',
                    'resellersubscription', 'resellersubscriptions'
            ]:
                doGetResoldSubscriptions()
            elif argument in ['matter', 'vaultmatter']:
                gapi_vault.getMatterInfo()
            elif argument in ['hold', 'vaulthold']:
                gapi_vault.getHoldInfo()
            elif argument in ['export', 'vaultexport']:
                gapi_vault.getExportInfo()
            elif argument in ['building']:
                gapi_directory_resource.getBuildingInfo()
            elif argument in ['device']:
                gapi_cloudidentity_devices.info()
            elif argument == 'deviceuserstate':
                gapi_cloudidentity_devices.info_state()
            elif argument in ['browser', 'browsers']:
                gapi_cbcm.info()
            elif argument in ['userinvitation', 'userinvitations']:
                gapi_cloudidentity_userinvitations.get()
            else:
                controlflow.invalid_argument_exit(argument, 'gam info')
            sys.exit(0)
        elif command == 'cancel':
            argument = sys.argv[2].lower()
            if argument in ['guardianinvitation', 'guardianinvitations']:
                doCancelGuardianInvitation()
            elif argument in ['userinvitation', 'userinvitations']:
                gapi_cloudidentity_userinvitations.cancel()
            else:
                controlflow.invalid_argument_exit(argument, 'gam cancel')
            sys.exit(0)
        elif command == 'delete':
            argument = sys.argv[2].lower()
            if argument == 'user':
                doDeleteUser()
            elif argument == 'group':
                gapi_directory_groups.delete()
            elif argument == 'device':
                gapi_cloudidentity_devices.delete()
            elif argument == 'deviceuser':
                gapi_cloudidentity_devices.delete_user()
            elif argument == 'cigroup':
                gapi_cloudidentity_groups.delete()
            elif argument in ['nickname', 'alias']:
                doDeleteAlias()
            elif argument == 'org':
                gapi_directory_orgunits.delete()
            elif argument == 'resource':
                gapi_directory_resource.deleteResourceCalendar()
            elif argument == 'mobile':
                gapi_directory_mobiledevices.delete()
            elif argument in ['schema', 'schemas']:
                doDelSchema()
            elif argument in ['course', 'class']:
                doDelCourse()
            elif argument == 'domain':
                gapi_directory_domains.delete()
            elif argument in ['domainalias', 'aliasdomain']:
                gapi_directory_domainaliases.delete()
            elif argument == 'admin':
                doDelAdmin()
            elif argument in ['guardian', 'guardians']:
                doDeleteGuardian()
            elif argument in ['project', 'projects']:
                doDelProjects()
            elif argument in ['resoldsubscription', 'resellersubscription']:
                doDeleteResoldSubscription()
            elif argument in ['matter', 'vaultmatter']:
                gapi_vault.updateMatter(action=command)
            elif argument in ['hold', 'vaulthold']:
                gapi_vault.deleteHold()
            elif argument in ['export', 'vaultexport']:
                gapi_vault.deleteExport()
            elif argument in ['building']:
                gapi_directory_resource.deleteBuilding()
            elif argument in ['feature']:
                gapi_directory_resource.deleteFeature()
            elif argument in ['alert']:
                doDeleteOrUndeleteAlert('delete')
            elif argument in ['sakey', 'sakeys']:
                doDeleteServiceAccountKeys()
            elif argument in ['adminrole']:
                gapi_directory_roles.delete()
            elif argument in ['browser', 'browsers']:
                gapi_cbcm.delete()
            elif argument in ['printer']:
                gapi_directory_printers.delete()
            elif argument == 'chromepolicy':
                gapi_chromepolicy.delete_policy()
            elif argument == 'chatmessage':
                gapi_chat.delete_message()
            else:
                controlflow.invalid_argument_exit(argument, 'gam delete')
            sys.exit(0)
        elif command == 'undelete':
            argument = sys.argv[2].lower()
            if argument == 'user':
                doUndeleteUser()
            elif argument in ['matter', 'vaultmatter']:
                gapi_vault.updateMatter(action=command)
            elif argument == 'alert':
                doDeleteOrUndeleteAlert('undelete')
            else:
                controlflow.invalid_argument_exit(argument, 'gam undelete')
            sys.exit(0)
        elif command == 'revoke':
            argument = sys.argv[2].lower()
            if argument in ['browsertoken', 'browserokens']:
                gapi_cbcm.revoketoken()
            sys.exit(0)
        elif command in ['close', 'reopen']:
            # close and reopen will have to be split apart if either takes a new argument
            argument = sys.argv[2].lower()
            if argument in ['matter', 'vaultmatter']:
                gapi_vault.updateMatter(action=command)
            else:
                controlflow.invalid_argument_exit(argument, f'gam {command}')
            sys.exit(0)
        elif command == 'print':
            argument = sys.argv[2].lower().replace('-', '')
            if argument == 'users':
                doPrintUsers()
            elif argument in ['nicknames', 'aliases']:
                doPrintAliases()
            elif argument == 'groups':
                gapi_directory_groups.print_()
            elif argument == 'cigroups':
                gapi_cloudidentity_groups.print_()
            elif argument == 'devices':
                gapi_cloudidentity_devices.print_()
            elif argument in ['groupmembers', 'groupsmembers']:
                gapi_directory_groups.print_members()
            elif argument in ['cigroupmembers', 'cigroupsmembers']:
                gapi_cloudidentity_groups.print_members()
            elif argument in ['orgs', 'ous']:
                gapi_directory_orgunits.print_()
            elif argument == 'privileges':
                gapi_directory_privileges.print_()
            elif argument == 'resources':
                gapi_directory_resource.printResourceCalendars()
            elif argument == 'cros':
                gapi_directory_cros.doPrintCrosDevices()
            elif argument == 'crosactivity':
                gapi_directory_cros.doPrintCrosActivity()
            elif argument == 'mobile':
                gapi_directory_mobiledevices.print_()
            elif argument in ['license', 'licenses', 'licence', 'licences']:
                gapi_licensing.print_()
            elif argument in ['token', 'tokens', 'oauth', '3lo']:
                printShowTokens(3, None, None, True)
            elif argument in ['schema', 'schemas']:
                doPrintShowUserSchemas(True)
            elif argument in ['courses', 'classes']:
                doPrintCourses()
            elif argument in ['courseparticipants', 'classparticipants']:
                doPrintCourseParticipants()
            elif argument in ['transfers', 'datatransfers']:
                doPrintDataTransfers()
            elif argument == 'transferapps':
                doPrintTransferApps()
            elif argument == 'domains':
                gapi_directory_domains.print_()
            elif argument in ['domainaliases', 'aliasdomains']:
                gapi_directory_domainaliases.print_()
            elif argument == 'admins':
                doPrintAdmins()
            elif argument in ['roles', 'adminroles']:
                gapi_directory_roles.print_()
            elif argument in ['guardian', 'guardians']:
                doPrintShowGuardians(True)
            elif argument in ['matters', 'vaultmatters']:
                gapi_vault.printMatters()
            elif argument in ['holds', 'vaultholds']:
                gapi_vault.printHolds()
            elif argument in ['exports', 'vaultexports']:
                gapi_vault.printExports()
            elif argument in ['building', 'buildings']:
                gapi_directory_resource.printBuildings()
            elif argument in ['feature', 'features']:
                gapi_directory_resource.printFeatures()
            elif argument in ['project', 'projects']:
                doPrintShowProjects(True)
            elif argument in ['alert', 'alerts']:
                doPrintShowAlerts()
            elif argument in ['alertfeedback', 'alertsfeedback']:
                doPrintShowAlertFeedback()
            elif argument in ['browser', 'browsers']:
                gapi_cbcm.print_()
            elif argument in ['browsertoken', 'browsertokens']:
                gapi_cbcm.printshowtokens(True)
            elif argument in ['vaultcount']:
                gapi_vault.print_count()
            elif argument in ['userinvitations']:
                gapi_cloudidentity_userinvitations.print_()
            elif argument in ['printermodels']:
                gapi_directory_printers.print_models()
            elif argument in ['printers']:
                gapi_directory_printers.print_()
            elif argument in ['chromeapps']:
                gapi_chromemanagement.printApps()
            elif argument in ['chromeappdevices']:
                gapi_chromemanagement.printAppDevices()
            elif argument in ['chromeversions']:
                gapi_chromemanagement.printVersions()
            elif argument in ['chromehistory']:
                gapi_chromehistory.printHistory()
            elif argument in ['chatspaces']:
                gapi_chat.print_spaces()
            elif argument in ['chatmembers']:
                gapi_chat.print_members()
            else:
                controlflow.invalid_argument_exit(argument, 'gam print')
            sys.exit(0)
        elif command == 'send':
            argument = sys.argv[2].lower()
            if argument in ['userinvitation', 'userinvitations']:
                gapi_cloudidentity_userinvitations.send()
            else:
                controlflow.invalid_argument_exit(argument, 'gam send')
            sys.exit(0)
        elif command == 'show':
            argument = sys.argv[2].lower()
            if argument in ['schema', 'schemas']:
                doPrintShowUserSchemas(False)
            elif argument in ['guardian', 'guardians']:
                doPrintShowGuardians(False)
            elif argument in ['license', 'licenses', 'licence', 'licences']:
                gapi_licensing.show()
            elif argument in ['project', 'projects']:
                doPrintShowProjects(False)
            elif argument in ['sakey', 'sakeys']:
                doShowServiceAccountKeys()
            elif argument in ['browsertoken', 'browsertokens']:
                gapi_cbcm.printshowtokens(False)
            elif argument in ['chromeschema', 'chromeschemas']:
                gapi_chromepolicy.printshow_schemas()
            elif argument in ['chromepolicy', 'chromepolicies']:
                gapi_chromepolicy.printshow_policies()
            else:
                controlflow.invalid_argument_exit(argument, 'gam show')
            sys.exit(0)
        elif command == 'move':
            argument = sys.argv[2].lower()
            if argument in ['browser', 'browsers']:
                gapi_cbcm.move()
            sys.exit(0)
        elif command in ['oauth', 'oauth2']:
            argument = sys.argv[2].lower()
            if argument in ['request', 'create']:
                createOAuth()
            elif argument in ['info', 'verify']:
                OAuthInfo()
            elif argument in ['delete', 'revoke']:
                doDeleteOAuth()
            elif argument in ['refresh']:
                creds = getValidOauth2TxtCredentials(force_refresh=True)
                if not creds:
                    controlflow.system_error_exit(5,
                                                  'Credential refresh failed')
                else:
                    print('Credentials refreshed')
            else:
                controlflow.invalid_argument_exit(argument, 'gam oauth')
            sys.exit(0)
        elif command == 'calendar':
            argument = sys.argv[3].lower()
            if argument == 'showacl':
                gapi_calendar.printShowACLs(False)
            elif argument == 'printacl':
                gapi_calendar.printShowACLs(True)
            elif argument == 'add':
                gapi_calendar.addACL('Add')
            elif argument in ['del', 'delete']:
                gapi_calendar.delACL()
            elif argument == 'update':
                gapi_calendar.addACL('Update')
            elif argument == 'wipe':
                gapi_calendar.wipeData()
            elif argument == 'addevent':
                gapi_calendar.addOrUpdateEvent('add')
            elif argument == 'updateevent':
                gapi_calendar.addOrUpdateEvent('update')
            elif argument == 'infoevent':
                gapi_calendar.infoEvent()
            elif argument == 'deleteevent':
                gapi_calendar.moveOrDeleteEvent('delete')
            elif argument == 'moveevent':
                gapi_calendar.moveOrDeleteEvent('move')
            elif argument == 'printevents':
                gapi_calendar.printEvents()
            elif argument == 'modify':
                gapi_calendar.modifySettings()
            else:
                controlflow.invalid_argument_exit(argument, 'gam calendar')
            sys.exit(0)
        elif command == 'report':
            gapi_reports.showReport()
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
                controlflow.invalid_argument_exit(argument, 'gam course')
            sys.exit(0)
        elif command == 'download':
            argument = sys.argv[2].lower()
            if argument in ['export', 'vaultexport']:
                gapi_vault.downloadExport()
            elif argument in ['storagebucket']:
                gapi_storage.download_bucket()
            else:
                controlflow.invalid_argument_exit(argument, 'gam download')
            sys.exit(0)
        elif command == 'rotate':
            argument = sys.argv[2].lower()
            if argument in ['sakey', 'sakeys']:
                doCreateOrRotateServiceAccountKeys()
            else:
                controlflow.invalid_argument_exit(argument, 'gam rotate')
            sys.exit(0)
        elif command == 'check':
            argument = sys.argv[2].lower()
            if argument in ['isinvitable', 'userinvitation', 'userinvitations']:
                gapi_cloudidentity_userinvitations.check()
            sys.exit(0)
        elif command in ['cancelwipe', 'wipe', 'approve', 'block', 'sync']:
            target = sys.argv[2].lower().replace('_', '')
            if target in ['device', 'devices']:
                if command == 'cancelwipe':
                    gapi_cloudidentity_devices.cancel_wipe()
                elif command == 'wipe':
                    gapi_cloudidentity_devices.wipe()
                elif command == 'sync':
                    gapi_cloudidentity_devices.sync()
            elif target == 'deviceuser':
                if command == 'cancelwipe':
                    gapi_cloudidentity_devices.cancel_wipe_user()
                elif command == 'wipe':
                    gapi_cloudidentity_devices.wipe_user()
                elif command == 'approve':
                    gapi_cloudidentity_devices.approve_user()
                elif command == 'block':
                    gapi_cloudidentity_devices.block_user()
            sys.exit(0)
        elif command in ['issuecommand', 'getcommand']:
            target = sys.argv[2].lower().replace('_', '')
            if target == 'cros':
                if command == 'issuecommand':
                    gapi_directory_cros.issue_command()
                elif command == 'getcommand':
                    gapi_directory_cros.get_command()
            sys.exit(0)
        elif command in ['yubikey']:
            action = sys.argv[2].lower().replace('_', '')
            if action == 'resetpiv':
                yk = yubikey.YubiKey()
                yk.reset_piv()
            sys.exit(0)
        users = getUsersToModify()
        command = sys.argv[3].lower()
        if command == 'print' and len(sys.argv) == 4:
            for user in users:
                print(user)
            sys.exit(0)
        if (GC_Values[GC_AUTO_BATCH_MIN] >
                0) and (len(users) > GC_Values[GC_AUTO_BATCH_MIN]):
            runCmdForUsers(None, users, True)
        if command == 'transfer':
            transferWhat = sys.argv[4].lower()
            if transferWhat == 'drive':
                transferDriveFiles(users)
            elif transferWhat == 'seccals':
                gapi_calendar.transferSecCals(users)
            else:
                controlflow.invalid_argument_exit(transferWhat,
                                                  'gam <users> transfer')
        elif command == 'show':
            showWhat = sys.argv[4].lower()
            if showWhat in ['labels', 'label']:
                printShowLabels(users)
            elif showWhat == 'profile':
                showProfile(users)
            elif showWhat == 'calendars':
                gapi_calendar.printShowCalendars(users, False)
            elif showWhat == 'calsettings':
                gapi_calendar.showCalSettings(users)
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
            elif showWhat in ['language']:
                getLanguage(users)
            elif showWhat == 'vacation':
                getVacation(users)
            elif showWhat in ['delegate', 'delegates']:
                printShowDelegates(users, False)
            elif showWhat in ['backupcode', 'backupcodes', 'verificationcodes']:
                doGetBackupCodes(users)
            elif showWhat in ['asp', 'asps', 'applicationspecificpasswords']:
                gapi_directory_asps.info(users)
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
            elif showWhat in ['contactdelegate', 'contactdelegates']:
                gapi_contactdelegation.print_(users, False)
            else:
                controlflow.invalid_argument_exit(showWhat, 'gam <users> show')
        elif command == 'print':
            printWhat = sys.argv[4].lower()
            if printWhat == 'calendars':
                gapi_calendar.printShowCalendars(users, True)
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
            elif printWhat in ['contactdelegate', 'contactdelegates']:
                gapi_contactdelegation.print_(users, True)
            elif printWhat in ['labels']:
                printShowLabels(users, show=False)
            else:
                controlflow.invalid_argument_exit(printWhat,
                                                  'gam <users> print')
        elif command == 'modify':
            modifyWhat = sys.argv[4].lower()
            if modifyWhat in ['message', 'messages']:
                doProcessMessagesOrThreads(users, 'modify', 'messages')
            elif modifyWhat in ['thread', 'threads']:
                doProcessMessagesOrThreads(users, 'modify', 'threads')
            else:
                controlflow.invalid_argument_exit(modifyWhat,
                                                  'gam <users> modify')
        elif command == 'trash':
            trashWhat = sys.argv[4].lower()
            if trashWhat in ['message', 'messages']:
                doProcessMessagesOrThreads(users, 'trash', 'messages')
            elif trashWhat in ['thread', 'threads']:
                doProcessMessagesOrThreads(users, 'trash', 'threads')
            else:
                controlflow.invalid_argument_exit(trashWhat,
                                                  'gam <users> trash')
        elif command == 'untrash':
            untrashWhat = sys.argv[4].lower()
            if untrashWhat in ['message', 'messages']:
                doProcessMessagesOrThreads(users, 'untrash', 'messages')
            elif untrashWhat in ['thread', 'threads']:
                doProcessMessagesOrThreads(users, 'untrash', 'threads')
            else:
                controlflow.invalid_argument_exit(untrashWhat,
                                                  'gam <users> untrash')
        elif command in ['delete', 'del']:
            delWhat = sys.argv[4].lower()
            if delWhat == 'delegate':
                deleteDelegate(users)
            elif delWhat == 'calendar':
                gapi_calendar.deleteCalendar(users)
            elif delWhat in ['labels', 'label']:
                doDeleteLabel(users)
            elif delWhat in ['message', 'messages']:
                runCmdForUsers(doProcessMessagesOrThreads,
                               users,
                               default_to_batch=True,
                               function='delete',
                               unit='messages')
            elif delWhat in ['thread', 'threads']:
                runCmdForUsers(doProcessMessagesOrThreads,
                               users,
                               default_to_batch=True,
                               function='delete',
                               unit='threads')
            elif delWhat == 'photo':
                deletePhoto(users)
            elif delWhat in ['license', 'licence']:
                gapi_licensing.delete(users)
            elif delWhat in ['backupcode', 'backupcodes', 'verificationcodes']:
                doDelBackupCodes(users)
            elif delWhat in ['asp', 'asps', 'applicationspecificpasswords']:
                gapi_directory_asps.delete(users)
            elif delWhat in ['token', 'tokens', 'oauth', '3lo']:
                doDelTokens(users)
            elif delWhat in ['group', 'groups']:
                gapi_directory_groups.deleteUserFromGroups(users)
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
            elif delWhat == 'contactdelegate':
                gapi_contactdelegation.delete(users)
            else:
                controlflow.invalid_argument_exit(delWhat, 'gam <users> delete')
        elif command in ['add', 'create']:
            addWhat = sys.argv[4].lower()
            if addWhat == 'calendar':
                if command == 'add':
                    gapi_calendar.addCalendar(users)
                else:
                    controlflow.system_error_exit(
                        2,
                        f'{addWhat} is not implemented for "gam <users> {command}"'
                    )
            elif addWhat == 'drivefile':
                createDriveFile(users)
            elif addWhat in ['license', 'licence']:
                gapi_licensing.create(users)
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
            elif addWhat == 'contactdelegate':
                gapi_contactdelegation.create(users)
            else:
                controlflow.invalid_argument_exit(addWhat,
                                                  f'gam <users> {command}')
        elif command == 'sync':
            syncWhat = sys.argv[4].lower()
            if syncWhat in ['license', 'licence']:
                gapi_licensing.sync(users)
            else:
                controlflow.invalid_argument_exit(syncWhat,
                                                  f'gam <users> {command}')
        elif command == 'update':
            updateWhat = sys.argv[4].lower()
            if updateWhat == 'calendar':
                gapi_calendar.updateCalendar(users)
            elif updateWhat == 'calattendees':
                gapi_calendar.changeAttendees(users)
            elif updateWhat == 'photo':
                doPhoto(users)
            elif updateWhat in ['license', 'licence']:
                gapi_licensing.update(users)
            elif updateWhat == 'user':
                doUpdateUser(users, 5)
            elif updateWhat in [
                    'backupcode', 'backupcodes', 'verificationcodes'
            ]:
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
                controlflow.invalid_argument_exit(updateWhat,
                                                  'gam <users> update')
        elif command in ['deprov', 'deprovision']:
            doDeprovUser(users)
        elif command == 'get':
            getWhat = sys.argv[4].lower()
            if getWhat == 'photo':
                getPhoto(users)
            elif getWhat == 'drivefile':
                downloadDriveFile(users)
            else:
                controlflow.invalid_argument_exit(getWhat, 'gam <users> get')
        elif command == 'empty':
            emptyWhat = sys.argv[4].lower()
            if emptyWhat == 'drivetrash':
                doEmptyDriveTrash(users)
            else:
                controlflow.invalid_argument_exit(emptyWhat,
                                                  'gam <users> empty')
        elif command == 'info':
            infoWhat = sys.argv[4].lower()
            if infoWhat == 'calendar':
                gapi_calendar.infoCalendar(users)
            elif infoWhat in ['filter', 'filters']:
                infoFilters(users)
            elif infoWhat in ['forwardingaddress', 'forwardingaddresses']:
                infoForwardingAddresses(users)
            elif infoWhat == 'sendas':
                infoSendAs(users)
            else:
                controlflow.invalid_argument_exit(infoWhat, 'gam <users> info')
        elif command == 'check':
            checkWhat = sys.argv[4].replace('_', '').lower()
            if checkWhat == 'serviceaccount':
                doCheckServiceAccount(users)
            elif checkWhat == 'isinvitable':
                gapi_cloudidentity_userinvitations.bulk_is_invitable(users)
            else:
                controlflow.invalid_argument_exit(checkWhat,
                                                  'gam <users> check')
        elif command == 'profile':
            doProfile(users)
        elif command == 'imap':
            #doImap(users)
            runCmdForUsers(doImap, users, default_to_batch=True)
        elif command == 'sendemail':
            sendOrDropEmail(users, 'send')
        elif command == 'importemail':
            sendOrDropEmail(users, 'import')
        elif command == 'insertemail':
            sendOrDropEmail(users, 'insert')
        elif command == 'draftemail':
            sendOrDropEmail(users, 'draft')
        elif command == 'language':
            doLanguage(users)
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
                controlflow.invalid_argument_exit(watchWhat,
                                                  'gam <users> watch')
        elif command == 'signout':
            gapi_directory_users.signout(users)
        elif command == 'turnoff2sv':
            gapi_directory_users.turn_off_2sv(users)
        elif command == 'waitformailbox':
            gapi_directory_users.wait_for_mailbox(users)
        else:
            controlflow.invalid_argument_exit(command, 'gam')
    except IndexError:
        showUsage()
        sys.exit(2)
    except KeyboardInterrupt:
        sys.exit(50)
    except OSError as e:
        controlflow.system_error_exit(3, str(e))
    except MemoryError:
        controlflow.system_error_exit(99, MESSAGE_GAM_OUT_OF_MEMORY)
    except SystemExit as e:
        GM_Globals[GM_SYSEXITRC] = e.code
    return GM_Globals[GM_SYSEXITRC]
